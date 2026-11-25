"""The stepping server. Local only (127.0.0.1), port $TM_PORT (default 8765). Pretend money only.

  GET  /next?session=S       the packet for the current wake (does not move the clock; the same answer if asked twice)
  GET  /look?session=S&what=bars&symbol=X&timeframe=1Min|30Min|1Day&days=N
  GET  /look?session=S&what=news&symbols=A,B&days=N
  GET  /look?session=S&what=price&symbols=A,B
  POST /pick?session=S       body: a pick, or {"no_pick": true, "why": "..."}. Answers with a receipt, then the clock moves.
  GET  /status?session=S     step k of N, done or not
When the last wake is done the session writes result.json and every later call answers DONE.
Each session has its own lock; many sessions can run at once. All state is in the session folder, so a restarted server
carries on where it stopped. Run: python3 timemachine/server.py. Standard library only."""
import json, os, sys, threading, traceback, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from timemachine import session as S
from timemachine.tape import Tape

_tape = None; _reg = threading.Lock(); _sessions = {}


def tape():
    global _tape
    if _tape is None:
        _tape = Tape()
    return _tape


def get_session(sid):
    with _reg:
        if sid not in _sessions:
            _sessions[sid] = [threading.Lock(), None]
        return _sessions[sid]


def done_answer(sess):
    return 200, dict(status="DONE", done=True, session=sess.meta["session"], result=str(sess.dir / "result.json"))


def handle(method, path, q, body):
    sid = (q.get("session") or [""])[0]
    if not sid:
        return 400, dict(ok=False, error="session=... is needed")
    slot = get_session(sid)
    with slot[0]:
        if slot[1] is None:
            try:
                slot[1] = S.Session(sid, tape=tape())  # carries on any desk runs a stopped server left half done
            except KeyError:
                return 404, dict(ok=False, error=f"no session {sid}")
        sess = slot[1]
        if path == "/status" and method == "GET":
            return 200, sess.status()
        if sess.done():
            return done_answer(sess)
        try:
            if path == "/next" and method == "GET":
                return 200, sess.packet()
            if path == "/look" and method == "GET":
                one = lambda k, d=None: (q.get(k) or [d])[0]
                r = sess.look(one("what"), symbol=one("symbol"), symbols=one("symbols"), timeframe=one("timeframe", "1Day"), days=one("days"))
                return (200 if r.get("ok") else 429 if "No lookups left" in r.get("error", "") else 400), r
            if path == "/pick" and method == "POST":
                try:
                    obj = json.loads(body or b"null")
                except ValueError:
                    return 400, sess.bad(["The body is not JSON."])
                r = sess.submit(obj)
                return (200 if r.get("ok") else 400), r
        except S.Done:
            return done_answer(sess)
        except AssertionError as e:
            return 400, dict(ok=False, error=str(e))
        return 404, dict(ok=False, error="unknown address. Use /next, /look, /pick or /status.")


class H(BaseHTTPRequestHandler):
    def _go(self, method):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0)) if method == "POST" else None
        try:
            code, obj = handle(method, u.path, q, body)
        except Exception as e:
            traceback.print_exc(); code, obj = 500, dict(ok=False, error=f"{type(e).__name__}: {str(e)[:300]}")
        data = json.dumps(obj, indent=1, sort_keys=True).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._go("GET")

    def do_POST(self):
        self._go("POST")

    def log_message(self, fmt, *a):
        sys.stderr.write("tm-server " + (fmt % a) + "\n")


def serve(port=None):
    port = int(port if port is not None else os.environ.get("TM_PORT", "8765"))
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"time machine server on http://127.0.0.1:{srv.server_address[1]} (runs in {S.runs_dir()})", flush=True)
    return srv


if __name__ == "__main__":
    serve().serve_forever()
