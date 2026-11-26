"""E06 forward watch: the TM06 hot-coin rules R1, R2 and R3 on public Coinbase prices, once a day, pretend money, no AI.

Card: practice/traders/E06_forward_hot_coin_rules.md (the card governs). Commands:
  plan              print the pinned settings (no prices)
  start             write the log header once: card and logger SHA-256, freeze commit and the first wake after it
  record            record the current wake if it is inside its recording window and not yet recorded; else do nothing
  loop              call record every 10 minutes for as long as the process lives
  alive             counts only: wakes due, recorded, void, last record clock. No prices, picks or returns
  score             the lead's one read at the end; refuses until all weeks are complete
Picks reuse the TM06 rule code (timemachine/tm06.py: listed, change_pct, volume_row and the top_7d_rise ranking) on a small
in-memory tape built from the fetched candles. Reads only https://api.exchange.coinbase.com public candles, at most 2.5
requests a second, and nothing else. Stdlib only."""
import argparse, fcntl, json, os, sqlite3, subprocess, sys, time, urllib.error, urllib.request
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from timemachine import tm06, perp as P  # noqa: E402

CARD = "practice/traders/E06_forward_hot_coin_rules.md"
OFF = Path("/home/user/workspace/rig/data/forward_e06")
UTC = timezone.utc
DAY = 86400
WEEKS = 20
START_USD = 1000.0
OPEN_AFTER_MIN = 20       # record no earlier than 20 minutes after the wake
WINDOW_MIN = 180          # and no later than 3 hours after it; a wake not recorded by then is void
FILL_WITHIN_MIN = 15      # the fill is the open of the first minute at or after the wake, within 15 minutes
VOL_RATIO = 1.5           # R2 drops a pick that is red over 24 hours with volume at least this times usual
CB = "https://api.exchange.coinbase.com/products/{}-USD/candles"
MIN_GAP = 0.4


class Refuse(Exception):
    pass


def need(ok, why):
    if not ok:
        raise Refuse(why)


def settings(cfg=None):
    cfg = cfg or tm06.full_config(); p = tm06.plan(cfg)
    ch = cfg["tm06_pick_change_hours"]; need(24 in ch, "tm06_pick_change_hours has no 24-hour change")
    return dict(coins=p["coins"], wake_hour=p["wake_hour"], max_names=p["max_names"], rise_hours=p["rise_hours"], fee_bps=p["main_fee_bps"],
                change_hours=24, usual_days=int(cfg["tm06_pick_volume_usual_days"]), listed_hours=float(cfg["tm06_pick_listed_hours"]),
                half_spread_bps={s: P.half_spread_bps(cfg, s) for s in p["coins"]}, vol_ratio=VOL_RATIO, weeks=WEEKS, start_usd=START_USD), cfg


# ---- clocks
def wake_at(day):
    return datetime(day.year, day.month, day.day, settings()[0]["wake_hour"], tzinfo=UTC)


def wakes_from(first, n):
    return [first + timedelta(days=i) for i in range(n)]


def iso(t):
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


# ---- the public candles
class Coinbase:
    def __init__(self):
        self.last = 0.0

    def __call__(self, coin, gran, start, end):
        out = []
        for attempt in range(5):
            time.sleep(max(0.0, self.last + MIN_GAP - time.monotonic())); self.last = time.monotonic()
            url = CB.format(coin) + f"?granularity={gran}&start={iso(start)}&end={iso(end)}"
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "e06-forward-watch/1.0", "Accept": "application/json"}), timeout=30) as r:
                    out = json.loads(r.read(4 * 1024 * 1024))
                break
            except urllib.error.HTTPError as e:
                need(e.code not in (401, 403, 451), f"venue refused with HTTP {e.code}")
                time.sleep(2 ** attempt * (5 if e.code == 429 else 1))
            except (urllib.error.URLError, TimeoutError, OSError):
                time.sleep(2 ** attempt)
        else:
            raise Refuse("venue did not answer")
        return [(int(c[0]), float(c[3]), float(c[2]), float(c[1]), float(c[4]), float(c[5])) for c in out]  # t, o, h, l, c, v


class Tape:
    """The few tm06 reads need a tape whose _conn() has a bars table; this is one, in memory."""
    def __init__(self):
        self.c = sqlite3.connect(":memory:")
        self.c.execute("CREATE TABLE bars(symbol TEXT, tf TEXT, t INTEGER, o REAL, h REAL, l REAL, c REAL, v REAL, PRIMARY KEY(symbol, tf, t))")

    def _conn(self):
        return self.c

    def add(self, s, tf, rows):
        self.c.executemany("INSERT OR REPLACE INTO bars VALUES (?,?,?,?,?,?,?,?)", [(s, tf, *r) for r in rows])


def fetch(st, wake, get):
    """Candles known by the record time that the rules and the fill need: minutes from 25 hours before the wake to 15 minutes after,
    an hour of minutes before the 7-day point, and the daily bars of the usual-volume days."""
    tape, n = Tape(), int(wake.timestamp())
    for s in st["coins"]:
        coin = s.split("/")[0]; mins = []
        a = n - 25 * 3600
        while a < n + FILL_WITHIN_MIN * 60:
            b = min(a + 299 * 60, n + FILL_WITHIN_MIN * 60)
            mins += get(coin, 60, datetime.fromtimestamp(a, UTC), datetime.fromtimestamp(b, UTC)); a = b + 60
        r = n - int(st["rise_hours"] * 3600)
        mins += get(coin, 60, datetime.fromtimestamp(r - 3600, UTC), datetime.fromtimestamp(r, UTC))
        days = get(coin, 86400, datetime.fromtimestamp(n - (st["usual_days"] + 3) * DAY, UTC), datetime.fromtimestamp(n - DAY, UTC))
        tape.add(s, "1Min", [m for m in mins if m[0] <= n + FILL_WITHIN_MIN * 60])
        tape.add(s, "1Day", [d for d in days if d[0] + DAY <= n])
    return tape


# ---- the rules (TM06 code)
def picks(st, tape, wake, cfg):
    lst = tm06.listed(tape, st["coins"], wake, cfg)
    r7 = {s: tm06.change_pct(tape, s, wake, st["rise_hours"]) for s in lst}
    r1 = sorted((s for s in r7 if r7[s] is not None), key=lambda s: (-r7[s], s))[:st["max_names"]]
    why = {}
    for s in r1:
        c24 = tm06.change_pct(tape, s, wake, st["change_hours"]); vr = tm06.volume_row(tape, s, wake, cfg)["ratio"]
        why[s] = dict(change_24h_pct=c24, volume_ratio=vr, dropped=bool(c24 is not None and c24 < 0 and vr is not None and vr >= st["vol_ratio"]))
    r2 = [s for s in r1 if not why[s]["dropped"]]
    return dict(listed=lst, rise_7d_pct=r7, R1=r1, R2=r2, R3=list(st["coins"]), r2_checks=why)


def fill_prices(tape, coins, wake):
    n = int(wake.timestamp()); out = {}
    for s in coins:
        r = tape.c.execute("SELECT o FROM bars WHERE symbol=? AND tf='1Min' AND t>=? AND t<? ORDER BY t LIMIT 1", (s, n, n + FILL_WITHIN_MIN * 60)).fetchone()
        out[s] = r[0] if r else None
    return out


# ---- the pretend book
def rebalance(book, target, px, st):
    """Trade to equal parts of the target names at the fill prices, paying half the spread and the fee on traded notional,
    scaled once so the book stays fully paid. Names and weights unchanged means no trade."""
    if book.get("names") == sorted(target):
        return 0.0
    V = book["cash"] + sum(q * px[s] for s, q in book["qty"].items())
    w = {s: 1.0 / len(target) for s in target}
    rate = {s: (st["half_spread_bps"][s] + st["fee_bps"]) / 1e4 for s in st["coins"]}
    c = 1.0
    for _ in range(20):
        T = {s: c * w.get(s, 0.0) * V for s in set(w) | set(book["qty"])}
        cost = sum(abs(T[s] - book["qty"].get(s, 0.0) * px[s]) * rate[s] for s in T)
        c = (V - cost) / V if V > 0 else 0.0
    book["qty"] = {s: T[s] / px[s] for s in T if T[s] > 0}
    book["cash"] = V - sum(T.values()) - cost
    book["names"] = sorted(target)
    return cost


def value(book, px):
    return book["cash"] + sum(q * px[s] for s, q in book["qty"].items())


# ---- the off-repo log
def enc(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False)


def read_log(off=OFF):
    f = off / "log.jsonl"
    if not f.exists():
        return []
    out, prev = [], None
    for line in f.read_text().splitlines():
        x = json.loads(line)
        need(x["prev"] == prev, "log chain broken")
        prev = sha256(line.encode()).hexdigest(); out.append(x)
    return out


def append(x, off=OFF):
    off.mkdir(parents=True, exist_ok=True, mode=0o700)
    need(off.stat().st_mode & 0o077 == 0, "log directory must be private")
    f = off / "log.jsonl"
    with open(off / ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        cur = read_log(off)
        x["prev"] = sha256(f.read_text().splitlines()[-1].encode()).hexdigest() if cur else None
        fd = os.open(f, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        with os.fdopen(fd, "a") as out:
            out.write(enc(x) + "\n")
    return x


def file_sha(p):
    return sha256((ROOT / p).read_bytes()).hexdigest()


def start(now, off=OFF, commit=None, commit_utc=None):
    need(not read_log(off), "log already started")
    if commit is None:
        need(subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", CARD, "practice/forward_e06.py"], capture_output=True, text=True).stdout == "",
             "card or logger differs from the freeze commit")
        commit, commit_utc = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%H %ct", "--", CARD], capture_output=True, text=True, check=True).stdout.split()
        commit_utc = datetime.fromtimestamp(int(commit_utc), UTC)
    w = wake_at(commit_utc)
    first = w if w > commit_utc else w + timedelta(days=1)
    need(now < first + timedelta(minutes=WINDOW_MIN), "the first wake after the freeze has passed")
    st, _ = settings()
    return append(dict(kind="header", card=CARD, card_sha256=file_sha(CARD), logger_sha256=file_sha("practice/forward_e06.py"),
                       freeze_commit=commit, freeze_utc=iso(commit_utc), first_wake=iso(first), wakes=7 * WEEKS + 1, settings=st, made_utc=iso(now)), off)


def schedule(log):
    h = log[0]; return wakes_from(parse(h["first_wake"]), h["wakes"])


def record(now, get=None, off=OFF):
    log = read_log(off); need(log and log[0]["kind"] == "header", "log not started")
    h = log[0]
    need(file_sha(CARD) == h["card_sha256"] and file_sha("practice/forward_e06.py") == h["logger_sha256"], "card or logger changed since the freeze")
    done = {x["wake"] for x in log[1:]}
    due = [w for w in schedule(log) if w + timedelta(minutes=OPEN_AFTER_MIN) <= now < w + timedelta(minutes=WINDOW_MIN)]
    if not due or iso(due[0]) in done:
        return None
    wake = due[0]; st, cfg = settings()
    books = {}
    for x in reversed(log[1:]):
        if x["kind"] == "wake":
            books = json.loads(json.dumps(x["books"])); break
    try:
        tape = fetch(st, wake, get or Coinbase())
        px = fill_prices(tape, st["coins"], wake)
        missing = sorted(s for s, p in px.items() if not p)
        if missing:
            return append(dict(kind="void", wake=iso(wake), reason=f"no fill minute for {len(missing)} coin(s)", coins=missing, made_utc=iso(now)), off)
        pk = picks(st, tape, wake, cfg)
    except Refuse as e:
        return append(dict(kind="void", wake=iso(wake), reason=str(e), made_utc=iso(now)), off)
    marks, costs = {}, {}
    for arm in ("R1", "R2", "R3"):
        b = books.get(arm) or dict(cash=st["start_usd"], qty={}, names=None)
        marks[arm] = value(b, px)
        if arm != "R3" or b["names"] is None:
            costs[arm] = rebalance(b, pk[arm], px, st)
        books[arm] = b
    return append(dict(kind="wake", wake=iso(wake), made_utc=iso(now), fill_open=px, picks=pk, value_before_trade=marks, costs_usd=costs, books=books), off)


def alive(now, off=OFF):
    log = read_log(off)
    if not log:
        return dict(started=False)
    sch = schedule(log); past = [w for w in sch if w + timedelta(minutes=WINDOW_MIN) <= now]
    rec = {x["wake"]: x["kind"] for x in log[1:]}
    return dict(started=True, first_wake=log[0]["first_wake"], wakes_total=len(sch), wakes_closed=len(past),
                recorded=sum(rec.get(iso(w)) == "wake" for w in past), void_logged=sum(rec.get(iso(w)) == "void" for w in past),
                void_missed=sum(iso(w) not in rec for w in past), last_made_utc=log[-1].get("made_utc"))


def score(now, off=OFF):
    log = read_log(off); sch = schedule(log)
    need(sch[-1] + timedelta(minutes=WINDOW_MIN) <= now, "the watch has not finished")
    v = {x["wake"]: x["value_before_trade"] for x in log[1:] if x["kind"] == "wake"}
    weeks = []
    for k in range(WEEKS):
        a, b = iso(sch[7 * k]), iso(sch[7 * k + 7])
        if a in v and b in v:
            g = {arm: v[b][arm] / v[a][arm] - 1 for arm in ("R1", "R2", "R3")}
            weeks.append(dict(week=k + 1, start=a, gain=g, R1_win=g["R1"] > g["R3"], R2_win=g["R2"] > g["R3"], R2_over_R1=g["R2"] > g["R1"]))
        else:
            weeks.append(dict(week=k + 1, start=a, void=True, R1_win=False, R2_win=False, R2_over_R1=False))
    need_wins = 16
    r1, r2 = sum(w["R1_win"] for w in weeks), sum(w["R2_win"] for w in weeks)
    return dict(weeks=weeks, void_weeks=sum(bool(w.get("void")) for w in weeks), R1_wins=r1, R2_wins=r2, need=need_wins,
                R1_beats_R3=r1 >= need_wins, R2_beats_R3=r2 >= need_wins, shown_R2_over_R1_weeks=sum(w["R2_over_R1"] for w in weeks))


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("command", choices=["plan", "start", "record", "loop", "alive", "score"])
    a = cli.parse_args(); now = lambda: datetime.now(UTC)
    try:
        if a.command == "plan":
            st, _ = settings(); print(json.dumps({k: v for k, v in st.items() if k != "half_spread_bps"}, indent=1)); print("half spreads pinned for", len(st["half_spread_bps"]), "coins")
        elif a.command == "start":
            h = start(now()); print("started; first wake", h["first_wake"], "freeze", h["freeze_commit"])
        elif a.command == "record":
            x = record(now()); print("nothing due" if x is None else f"{x['kind']} {x['wake']}")
        elif a.command == "loop":
            while True:
                try:
                    x = record(now())
                    if x is not None:
                        print(iso(now()), x["kind"], x["wake"], flush=True)
                except Refuse as e:
                    print(iso(now()), "refused:", e, flush=True)
                time.sleep(600)
        elif a.command == "alive":
            print(json.dumps(alive(now()), indent=1))
        else:
            print(json.dumps(score(now()), indent=1))
    except Refuse as e:
        cli.exit(2, f"Refused: {e}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
