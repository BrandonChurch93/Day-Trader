"""The stepping server. Local only (127.0.0.1), port $TM_PORT (default 8765). Pretend money only.

  GET  /next?session=S       the packet for the current wake (does not move the clock; the same answer if asked twice)
  GET  /look?session=S&what=bars&symbol=X&timeframe=1Min|30Min|1Day&days=N
  GET  /look?session=S&what=news&symbols=A,B&days=N
  GET  /look?session=S&what=price&symbols=A,B
  POST /pick?session=S       body: a pick, or {"no_pick": true, "why": "..."}. Answers with a receipt, then the clock moves.
  GET  /status?session=S     step k of N, done or not
A weights session (timemachine/weights.py) uses the same addresses; its /pick body is {"weights": {...}, "why": "..."}
or {"no_change": true, "why": "..."}.
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
from timemachine import weights as W

_tape = None; _reg = threading.Lock(); _sessions = {}
_CACHE_MAX = None  # read from config at serve() or first use
_ro_tapes = {}  # one shared read-only tape per fast store path, for every session made on it (was one Tape per session)


def cache_max():
    """tm_server_day_bars_cache_max from config/thresholds.yaml: day-bar cache entries a tape may hold before its caches are dropped."""
    return int(W.lev_config(keys=["tm_server_day_bars_cache_max"])["tm_server_day_bars_cache_max"])


def ro_tape(path):
    with _reg:
        if path not in _ro_tapes:
            _ro_tapes[path] = Tape(path, readonly=True)
        return _ro_tapes[path]


def trim_caches():
    """The tape caches only save reads; past the cap they are dropped whole and filled again on use."""
    global _CACHE_MAX
    if _CACHE_MAX is None:
        _CACHE_MAX = cache_max()
    cap = _CACHE_MAX
    for t in [x for x in [_tape] if x is not None] + list(_ro_tapes.values()):
        if len(t._day_bars_cache) > cap:
            t._clear_cache()


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


def handle_desk(method, path, sid, body, authorization,registration=None):
    actions = {("GET", "/desk/next"): "next", ("GET", "/desk/status"): "status",
               ("POST", "/desk/look"): "look", ("POST", "/desk/notes"): "notes",
               ("POST", "/desk/pick"): "pick", ("POST", "/desk/usage"): "usage"}
    action = actions.get((method, path))
    if not action:
        return 404, dict(ok=False, error="unknown desk route")
    prefix = "Bearer "
    if not isinstance(authorization, str) or not authorization.startswith(prefix):
        return 403, dict(ok=False, error="desk access denied")
    try:
        token = authorization[len(prefix):]
        sess = W.open_session(sid, desk_token=token)
        if registration is not None:
            from timemachine.desk import digest
            if digest((sess.manifest.get("registration") or {}).get("body")) != registration:
                raise PermissionError
        role = sess.authenticate(token)
        if role is None:
            raise PermissionError
        obj = json.loads(body) if body else {}
        if not isinstance(obj, dict):
            raise ValueError("expected a JSON object")
        return 200, sess.handle(role, action, obj)
    except (PermissionError, FileNotFoundError):
        return 403, dict(ok=False, error="desk access denied")
    except (ValueError, TypeError) as exc:
        return 400, dict(ok=False, error=str(exc)[:300])


def handle_desk_only(method,path,q,body,authorization,registration=None):
    sid = (q.get("session") or [""])[0]
    if not path.startswith("/desk/") or not sid.startswith("TM07-"):
        return 404, dict(ok=False,error="unknown desk route")
    return handle_desk(method,path,sid,body,authorization,registration)


def handle(method, path, q, body, authorization=None):
    sid = (q.get("session") or [""])[0]
    if not sid:
        return 400, dict(ok=False, error="session=... is needed")
    if path.startswith("/desk/"):
        if not sid.startswith("TM07-"):
            return 404, dict(ok=False, error="unknown route")
        return handle_desk(method, path, sid, body, authorization)
    if sid.startswith("TM07-") and not (S.runs_dir() / sid / "session.json").is_file():
        return 404, dict(ok=False, error="unknown legacy session")
    slot = get_session(sid)
    with slot[0]:
        if slot[1] is None:
            try:
                meta = json.loads((S.runs_dir() / sid / "session.json").read_text()) if (S.runs_dir() / sid / "session.json").exists() else {}
                tp = ro_tape(meta["tape"]) if meta.get("tape_readonly") and meta.get("tape") else tape()
                slot[1] = W.open_session(sid, tape=tp)  # a weights or a pick session; carries on any desk runs a stopped server left half done
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
                if not (sess.dir / "packets" / f"{sess.prog['k']}.json").exists():
                    # a pick for a wake the trader has not been shown: most often a second send after a lost reply
                    return 409, dict(ok=False, error="You have not asked for /next at this wake. If you sent a pick and got no answer, it was taken and the clock moved. "
                                                    "Call /next to see where you are, then decide again. Nothing was traded just now and the clock did not move.")
                r = sess.submit(obj)
                return (200 if r.get("ok") else 400), r
        except S.Done:
            return done_answer(sess)
        except AssertionError as e:
            return 400, dict(ok=False, error=str(e))
        return 404, dict(ok=False, error="unknown address. Use /next, /look, /pick or /status.")


def compact(q):
    """Plan TM06 picker and swing sessions get compact JSON (their packets are large); every other session as before."""
    slot = _sessions.get((q.get("session") or [""])[0])
    meta = getattr(slot[1], "meta", None) if slot else None
    return bool(meta) and (meta.get("tm06") or {}).get("part") in ("P", "S")


class H(BaseHTTPRequestHandler):
    desk_only = False

    def _go(self, method):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        size = int(self.headers.get("Content-Length") or 0) if method == "POST" else 0
        if u.path.startswith("/desk/") and not 0 <= size <= 65536:
            self.send_error(413)
            return
        body = self.rfile.read(size) if method == "POST" else None
        try:
            if self.desk_only:
                code,obj = handle_desk_only(method,u.path,q,body,self.headers.get("Authorization"),self.server.desk_registration)
            elif u.path.startswith("/desk/"):
                code,obj = 404, dict(ok=False,error="use the isolated desk listener")
            else:
                code,obj = handle(method,u.path,q,body,self.headers.get("Authorization"))
                trim_caches()
        except Exception as e:
            traceback.print_exc(); code, obj = 500, dict(ok=False, error=f"{type(e).__name__}: {str(e)[:300]}")
        data = (json.dumps(obj, separators=(",", ":"), sort_keys=True) if self.desk_only or compact(q) else json.dumps(obj, indent=1, sort_keys=True)).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(data))); self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._go("GET")

    def do_POST(self):
        self._go("POST")

    def log_message(self, fmt, *a):
        sys.stderr.write("tm-server " + (fmt % a) + "\n")


def serve(port=None):
    global _CACHE_MAX
    _CACHE_MAX = cache_max()
    port = int(port if port is not None else os.environ.get("TM_PORT", "8765"))
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"time machine server on http://127.0.0.1:{srv.server_address[1]} (runs in {S.runs_dir()})", flush=True)
    return srv


class DeskH(H):
    desk_only = True


def serve_desk(port,*,approval_key,proof,signature,launcher_digest):
    from timemachine.desk import validate_worker_boundary
    root = os.environ.get("TM07_RUNS_DIR")
    if not root:
        raise ValueError("set a separate TM07_RUNS_DIR")
    validate_worker_boundary(approval_key,proof,signature,root,launcher_digest=launcher_digest)
    registration = proof.get("registration")
    if not isinstance(registration,str) or len(registration) != 64:
        raise ValueError("sealed worker proof must name the registered attempt")
    server = ThreadingHTTPServer(("127.0.0.1",int(port)),DeskH)
    server.desk_registration = registration
    return server


if __name__ == "__main__":
    serve().serve_forever()
