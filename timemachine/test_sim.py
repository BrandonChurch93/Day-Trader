"""Checks for the time machine's pretend broker, sessions and server, on a small made-up tape. No network.
Run: python3 timemachine/test_sim.py"""
import copy, datetime as dt, json, math, os, shutil, sys, tempfile, threading, urllib.request
from pathlib import Path

TMP = tempfile.mkdtemp(prefix="tm_test_")
os.environ["TM_RUNS"] = TMP + "/runs"; os.environ["TM_SESSIONS_LOG"] = TMP + "/SESSIONS.jsonl"; os.environ.pop("TM_HANDLE", None)
ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT / "practice"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import books, broker as B, trader as T
from timemachine.tape import Tape
from timemachine import session as S, code_traders as C, server as SV
from timemachine.simbroker import SimBroker

UTC = dt.timezone.utc
N = [0]
def ok(cond, what):
    N[0] += 1
    if not cond:
        print("FAIL:", what); sys.exit(1)

def U(*a):
    return dt.datetime(*a, tzinfo=UTC)

T0 = U(2026, 10, 1)
CFG = S.full_config(); HS_C = CFG["tm_crypto_half_spread_bps"] / 1e4; HS_S = CFG["tm_stock_half_spread_bps"] / 1e4; FEE = CFG["practice_crypto_fee_bps_added"] / 1e4
ok(CFG["tm_tick_minutes"] == 5 and CFG["tm_crypto_wake_hours_utc"] == [0, 12] and CFG["tm_stock_wake_times_ny"] == [10.0, 12.5, 15.5] and CFG["practice_crypto_fee_in_coin"] == 0,
   "set-up: the hand-worked times below assume 5 minute ticks, crypto wakes at 00 and 12 UTC, stock wakes at 10:00, 12:30, 15:30 New York, and the crypto fee in dollars")
ok(CFG["practice_amount_per_trader_usd"] == CFG["tm_account_start_usd"], "the one trader's budget is the whole pretend account")


# ---- the made-up tape
def btc(i):  # flat at 100, then from minute 122 at 94 (below a stop at 95)
    return 100.0 if i < 122 else 94.0
def eth(i):  # flat at 50, then from minute 200 at 56 (above a target at 55)
    return 50.0 if i < 200 else 56.0
def sol(i):
    return 20.0 + (i % 7) * 0.01

def make_tape(path):
    tp = Tape(path); rows = []
    for i in range(3 * 1440):
        t = T0 + dt.timedelta(minutes=i)
        for sym, f in (("BTC/USD", btc), ("ETH/USD", eth), ("SOL/USD", sol)):
            if sym == "SOL/USD" and i % 3 == 1:
                continue  # a minute with no trades: no bar
            p = f(i); v = 1.0 if (sym == "SOL/USD" and i == 6) else 1000.0
            rows.append((sym, "1Min", t, p, p * 1.001, p * 0.999, p, v))
    for j in range(-40, 3):
        for sym, p in (("BTC/USD", 100.0), ("ETH/USD", 50.0), ("SOL/USD", 20.0)):
            rows.append((sym, "1Day", T0 + dt.timedelta(days=j), p, p, p, p, 5000.0))
    # stocks: two sessions, 13:30Z to 20:00Z (9:30 to 16:00 New York)
    sess = [("2026-10-01", U(2026, 10, 1, 13, 30), U(2026, 10, 1, 20)), ("2026-10-02", U(2026, 10, 2, 13, 30), U(2026, 10, 2, 20))]
    tp.add_sessions(sess)
    for date, op, cl in sess:
        tp.add_universe(date, ["AAA", "BBB", "CCC", "SPY"])
        m = 0; t = op - dt.timedelta(minutes=30)
        while t < cl + dt.timedelta(minutes=30):  # extended-hours minutes too, which must never fill
            p = 10.0 + m * 0.001
            for sym in ("AAA", "CCC", "SPY"):
                rows.append((sym, "1Min", t, p, p, p, p, 100000.0))
            m += 1; t += dt.timedelta(minutes=1)
        t = op
        while t < cl:
            for sym in ("AAA", "BBB", "CCC", "SPY"):
                rows.append((sym, "30Min", t, 10.0, 10.0, 10.0, 10.0, 1e6))
            t += dt.timedelta(minutes=30)
    for j in range(1, 40):
        d = (T0 - dt.timedelta(days=j)).strftime("%Y-%m-%d")
        for sym in ("AAA", "BBB", "CCC", "SPY"):
            rows.append((sym, "1Day", U(2026, 10, 1) - dt.timedelta(days=j) + dt.timedelta(hours=4), 10.0, 10.0, 10.0, 10.0, 1e6))
    tp.add_bars(rows)
    tp.add_news([dict(id=1, created=T0 + dt.timedelta(hours=1), updated=T0 + dt.timedelta(hours=30), headline="Early story, edited later", summary="s1",
                      source="x", url="https://example.com/1", symbols=["BTCUSD"]),
                 dict(id=2, created=T0 + dt.timedelta(hours=13), updated=T0 + dt.timedelta(hours=13), headline="Later story", summary="s2", source="x",
                      url="https://example.com/2", symbols=["BTCUSD"])])
    return tp

TAPE = make_tape(TMP + "/tape.sqlite")
NOW = [T0]
def sb_new(name):
    return SimBroker(TAPE, lambda: NOW[0], CFG, Path(TMP) / f"{name}.json")


# ---- fill price and time
b = sb_new("fill1"); NOW[0] = T0 + dt.timedelta(minutes=10, seconds=30)
o = b.submit("BTC/USD", "buy", "gtc", "c1", notional=500.0)
ok(o["status"] == "accepted", "an order is open when placed")
NOW[0] = T0 + dt.timedelta(minutes=11, seconds=59); ok(b.order_by_cid("c1")["status"] == "accepted", "it does not fill before the clock passes the end of the next minute's bar")
NOW[0] = T0 + dt.timedelta(minutes=12); o = b.order_by_cid("c1")
ok(o["status"] == "filled" and o["filled_at"] == "2026-10-01T00:11:00Z", "it fills at the first bar that starts at or after the order time (00:11), never the bar the order sits inside (00:10)")
ok(abs(float(o["filled_avg_price"]) - 100.0 * (1 + HS_C)) < 1e-9, "the fill price is that bar's open moved up by half the crypto spread")
q = math.floor(500.0 / (100 * (1 + HS_C)) * 1e9 + 1e-6) / 1e9
ok(abs(float(o["filled_qty"]) - q) < 1e-12 and abs(b.cash() - (1000 - q * 100 * (1 + HS_C) * (1 + FEE))) < 1e-9, "quantity, and cash less the dollars and the fee")
NOW[0] = T0 + dt.timedelta(minutes=20); o = b.submit("BTC/USD", "sell", "gtc", "c2", qty=q); NOW[0] = T0 + dt.timedelta(minutes=21, seconds=1)
o = b.order_by_cid("c2"); ok(o["status"] == "filled" and abs(float(o["filled_avg_price"]) - 100 * (1 - HS_C)) < 1e-9 and o["filled_at"] == "2026-10-01T00:20:00Z", "a sell fills at the open moved down by half the spread")
ok(b.positions() == {}, "nothing is held after selling all")
b = sb_new("fill2"); NOW[0] = T0 + dt.timedelta(minutes=1, seconds=5); b.submit("SOL/USD", "buy", "gtc", "s1", notional=100.0)
NOW[0] = T0 + dt.timedelta(minutes=2, seconds=59); ok(b.order_by_cid("s1")["status"] == "accepted", "SOL has no bar at minute 1 and the minute 2 bar is not finished: still open")
NOW[0] = T0 + dt.timedelta(minutes=3); o = b.order_by_cid("s1")
ok(o["filled_at"] == "2026-10-01T00:02:00Z", "a missing minute is skipped: it fills at the next bar that exists")

# ---- the volume cap: SOL's minute 6 has volume 1, so at most 0.1 coin fills and the rest is canceled
ok(CFG["tm_crypto_max_share_of_minute_volume"] == 0, "set-up: the crypto volume cap is off by default")
b = sb_new("vol0"); NOW[0] = T0 + dt.timedelta(minutes=6); b.submit("SOL/USD", "buy", "gtc", "v0", notional=100.0); NOW[0] = T0 + dt.timedelta(minutes=7)
ok(b.order_by_cid("v0")["status"] == "filled", "with the crypto cap at 0, a thin minute fills the whole order")
CAPPED = dict(CFG, tm_crypto_max_share_of_minute_volume=0.1)
b = SimBroker(TAPE, lambda: NOW[0], CAPPED, Path(TMP) / "vol.json"); NOW[0] = T0 + dt.timedelta(minutes=6); b.submit("SOL/USD", "buy", "gtc", "v1", notional=100.0); NOW[0] = T0 + dt.timedelta(minutes=7)
o = b.order_by_cid("v1"); cap = 0.1 * 1.0
ok(o["status"] == "canceled" and abs(float(o["filled_qty"]) - cap) < 1e-12, "an order larger than the volume cap is part filled, then canceled (the Alpaca shape)")
bk, _ = books.derive(b.orders(), ["X"], 1000, FEE, False)
oth = books.derive([dict(o, client_order_id=books.cid_for("X", "t1"))], ["X"], 1000, FEE, False)[0]["X"]
ok(oth["orders"][0]["status"] == "part filled" and abs(oth["pos"]["SOLUSD"] - cap) < 1e-12, "the desk's books count it as part filled, with only the filled part held")
ok(abs(b.cash() - oth["cash"]) < 1e-9, "the books' cash and the pretend account's cash agree on a part fill")

TAPE.add_bars([("CCC", "1Min", U(2026, 10, 1, 15), 10.0, 10.0, 10.0, 10.0, 5.0)])  # a thin stock minute
b = sb_new("volstock"); NOW[0] = U(2026, 10, 1, 15); b.submit("CCC", "buy", "day", "vs", notional=500.0); NOW[0] = U(2026, 10, 1, 15, 1)
o = b.order_by_cid("vs"); ok(o["status"] == "canceled" and abs(float(o["filled_qty"]) - CFG["tm_max_share_of_minute_volume"] * 5) < 1e-9, "the stock volume cap: only that share of the minute's volume fills, the rest is canceled")

# ---- refusals where the real broker refuses
b = sb_new("ref"); NOW[0] = T0 + dt.timedelta(minutes=30)
def refused(fn):
    try:
        fn(); return False
    except B.Refused:
        return True
b.submit("BTC/USD", "buy", "gtc", "r1", notional=10.0)
ok(refused(lambda: b.submit("BTC/USD", "buy", "gtc", "r1", notional=10.0)), "the same client id twice is refused")
ok(refused(lambda: b.submit("BTC/USD", "buy", "gtc", "r2", notional=5000.0)), "a buy over the cash is refused")
ok(refused(lambda: b.submit("ETH/USD", "sell", "gtc", "r3", qty=1.0)), "a sale of something not held is refused (no shorting)")
ok(refused(lambda: b.submit("ZZZ/USD", "buy", "gtc", "r4", notional=10.0)), "an unknown symbol is refused")
ok(refused(lambda: b.submit("AAA", "buy", "day", "r5", notional=10.0)), "a stock order while the market is closed is refused")
NOW[0] = U(2026, 10, 1, 14)
ok(refused(lambda: b.submit("BBB", "buy", "day", "r6", notional=10.0)), "a stock with no minute bars that day is refused (no fill could be worked out)")
o = b.submit("AAA", "buy", "day", "r7", notional=10.0); NOW[0] = U(2026, 10, 1, 14, 1)
o = b.order_by_cid("r7"); ok(o["status"] == "filled" and abs(float(o["filled_avg_price"]) - (10.0 + 60 * 0.001) * (1 + HS_S)) < 1e-9, "a stock fills at the next minute's open plus half the stock spread, with no fee")
NOW[0] = U(2026, 10, 1, 19, 59, 30); b.submit("AAA", "buy", "day", "r8", notional=10.0); NOW[0] = U(2026, 10, 1, 20, 5)
ok(b.order_by_cid("r8")["status"] == "expired" and b.order_by_cid("r8")["filled_qty"] == "0", "a day order with no regular-hours bar before the close expires; the after-hours bars are not used")
b2 = SimBroker(TAPE, lambda: NOW[0], CFG, Path(TMP) / "ref.json")
ok(b2.orders() == b.orders() and b2.cash() == b.cash(), "the pretend account read back from its file is the same: a restart loses nothing")


# ---- sessions
def scripted(acts_by_step):
    def fn(packet, look):
        a = acts_by_step.get(packet["step"])
        return a(packet) if a else {"no_pick": True, "why": "nothing"}
    return fn

def two_coins(packet):
    return dict(thesis="Buy two coins with exits.", actions=[dict(symbol="BTC/USD", side="buy", usd=400, reason="r"), dict(symbol="ETH/USD", side="buy", usd=400, reason="r")],
                exits=[dict(symbol="BTC/USD", stop=95.0), dict(symbol="ETH/USD", target=55.0)])

def mk(sid, trader="A07", market="crypto", start="2026-10-01", end="2026-10-01", **kw):
    kw.setdefault("news", True)
    S.create(sid, trader, "test", "practice/traders/A07_crypto_trend.md", start, end, market=market, tape=TAPE, **kw)
    return sid

log0 = len(Path(os.environ["TM_SESSIONS_LOG"]).read_text().splitlines()) if Path(os.environ["TM_SESSIONS_LOG"]).exists() else 0
sid = mk("exits1", watch=["BTC/USD", "ETH/USD"], benchmark="BTC/USD")
meta = json.loads((Path(TMP) / "runs" / sid / "session.json").read_text())
ok(meta["wakes"] == ["2026-10-01T00:00:00Z", "2026-10-01T12:00:00Z"] and meta["end_utc"] == "2026-10-02T00:00:00Z", "crypto wakes at the configured UTC hours, and the window ends at the next midnight")
line = json.loads(Path(os.environ["TM_SESSIONS_LOG"]).read_text().splitlines()[-1])
ok(all(k in line for k in ("session", "trader", "model", "method", "method_sha256", "window", "wakes", "config_hash", "created_utc", "git_commit")) and line["method_sha256"],
   "the session is counted in SESSIONS.jsonl with every field the spec names")
try:
    mk("exits1"); ok(False, "")
except FileExistsError:
    ok(True, "")
ok(len(Path(os.environ["TM_SESSIONS_LOG"]).read_text().splitlines()) == log0 + 1, "a session id cannot be made twice, and a refused make is not counted")

s = S.Session(sid, tape=TAPE); pk = s.packet()
ok(pk["step"] == 1 and pk["of"] == 2 and pk["utc"] == "2026-10-01T00:00:00Z" and pk["pick_id"] == "20261001T0000Z", "the first packet: step 1 of 2, at the first wake")
ok(s.packet() == pk, "asking for the packet twice gives the same answer")
ok(set(pk["feed"]) >= {"clock", "prices", "movers", "crypto_movers", "most_active", "news", "problems"} and "BTC/USD" in pk["feed"]["prices"], "the packet carries the desk's own market feed")
ok(pk["book"]["cash_usd"] == 1000 and pk["book"]["positions"] == [] and pk["last_pick"] is None, "the first book: all cash")
r = s.submit(dict(trader="B01", thesis="x", actions=[])); ok(not r["ok"] and r["bad_attempts"] == 1 and s.prog["k"] == 0, "a pick for another trader is refused and counted, and the clock does not move")
r = s.submit(dict(thesis="x", actions=[dict(symbol="BTC/USD", side="buy", usd=-1, reason="r")]))
ok(not r["ok"] and r["bad_attempts"] == 2 and any("usd must be" in e for e in r["errors"]) and s.now == T0, "a pick that does not fit picks.validate is refused with its error text, counted, and the clock does not move")
r = s.submit({"no_pick": True, "extra": 1}); ok(not r["ok"] and r["bad_attempts"] == 3, "a malformed no-pick is refused")
lk = s.look("price", symbols="BTC/USD,ETH/USD"); ok(lk["ok"] and lk["data"]["BTC/USD"]["t"] == "2026-10-01T00:00:00Z" and lk["looks_left"] == CFG["tm_max_looks_per_wake"] - 1,
                                               "a price lookup is as of the wake, from the last finished minute, and is counted")
lk = s.look("bars", symbol="BTC/USD", timeframe="1Day", days=10); ok(lk["ok"] and lk["data"][-1]["t"] == "2026-09-30T00:00:00Z", "daily bars: today's unfinished day is not shown")
lk = s.look("news", symbols="BTC/USD", days=2); ok(lk["ok"] and lk["data"] == [], "no news before it is created")
r = s.submit(two_coins(pk))
ok(r["ok"] and r["step"] == 1 and s.prog["k"] == 1 and s.now == U(2026, 10, 1, 12), "a good pick moves the clock to the next wake")
pf = Path(TMP) / "runs" / sid / "picks" / "A07" / "20261001T0000Z.json"; ok(pf.exists() and json.loads(pf.read_text())["made_utc"] == "2026-10-01T00:00:00Z", "the pick file is written where the live desk reads it, with the template's times filled in")
orders = s.sb.orders(); by = {(o["symbol"], o["side"]): o for o in orders}
ok(len(orders) == 4 and all(o["status"] == "filled" for o in orders), "two buys and two exit sells, all filled")
ok(by[("BTC/USD", "buy")]["filled_at"] == "2026-10-01T00:00:00Z" and by[("BTC/USD", "buy")]["submitted_at"] == "2026-10-01T00:00:00Z", "the buys are sent at the wake and fill on the minute that starts then")
# BTC is 94 from minute 122 (02:02). That bar is finished at 02:03. Ticks are every 5 minutes, so the first desk run that sees it is 02:05.
ok(by[("BTC/USD", "sell")]["submitted_at"] == "2026-10-01T02:05:00Z" and by[("BTC/USD", "sell")]["filled_at"] == "2026-10-01T02:05:00Z", "the stop fires at the first tick after the price crosses it (02:05), not before")
ok(abs(float(by[("BTC/USD", "sell")]["filled_avg_price"]) - 94 * (1 - HS_C)) < 1e-9, "the stop sale fills at the next minute's open less half the spread")
# ETH is 56 from minute 200 (03:20); finished at 03:21; the first tick after is 03:25.
ok(by[("ETH/USD", "sell")]["submitted_at"] == "2026-10-01T03:25:00Z", "the target fires at the first tick after the price crosses it (03:25)")
pk2 = s.packet(); ok(pk2["step"] == 2 and pk2["last_pick"]["pick_id"] == "20261001T0000Z" and len(pk2["last_pick"]["orders_since"]) == 4, "the next packet says what happened to the last pick")
ok(pk2["book"]["closed_trades"] == 2 and pk2["book"]["wins"] == 1 and pk2["book"]["losses"] == 1, "the book shows one win and one loss")
news = pk2["feed"]["news"]; ok(len(news) == 1 and news[0]["headline"] == "Early story, edited later" and news[0].get("edited_later"), "at 12:00 the 01:00 story shows, marked as edited later; the 13:00 story does not")
lk = s.look("news", symbols="BTC/USD", days=1); ok(lk["data"][0]["id"] == 1 and "updated" not in lk["data"][0], "a news lookup never shows the later edit time")
r = s.submit({"no_pick": True, "why": "done"}); ok(r["ok"] and r["done"] and s.done(), "the last pick finishes the session")
res = json.loads((Path(TMP) / "runs" / sid / "result.json").read_text())
ok(all(k in res for k in ("session", "summary", "steps", "benchmark_hold", "limits")) and len(res["steps"]) == 2 and res["steps"][0]["bad_attempts"] == 3 and res["steps"][0]["looks"] == 3,
   "result.json has the session, the desk's summary, the steps with lookups and bad attempts, the benchmark hold and the limits")
try:
    s.packet(); ok(False, "")
except S.Done:
    ok(True, "after the last wake every call answers DONE")

# ---- the books from practice/books.py agree with the pretend account to the cent
tr = res["summary"]["traders"][0]
ok(abs(tr["cash_usd"] - s.sb.cash()) < 0.005 and tr["positions"] == [] and s.sb.holding() == {}, "the desk's books and the pretend account agree on cash to the cent and hold the same things")
q1 = math.floor(400 / (100 * (1 + HS_C)) * 1e9 + 1e-6) / 1e9; q2 = math.floor(400 / (50 * (1 + HS_C)) * 1e9 + 1e-6) / 1e9
hand = 1000 - 2 * 0 - (q1 * 100 * (1 + HS_C) + q2 * 50 * (1 + HS_C)) * (1 + FEE) + (q1 * 94 * (1 - HS_C) + q2 * 56 * (1 - HS_C)) * (1 - FEE)
ok(abs(tr["value_usd"] - hand) < 0.006, "the end value, worked by hand from the fill model")
ok(res["summary"]["status"] == "running" and not res["summary"]["symbols_stopped"], "the desk found nothing that did not add up")

# ---- no look-ahead: a packet at T never changes when later tape rows are edited
import sqlite3
src_db = sqlite3.connect(TMP + "/tape.sqlite"); dst_db = sqlite3.connect(TMP + "/tape_peek.sqlite"); src_db.backup(dst_db); src_db.close(); dst_db.close()
MAIN_TAPE, TAPE = TAPE, Tape(TMP + "/tape_peek.sqlite")  # a copy of the tape, so the later rows can be changed
sid = mk("peek", watch=["BTC/USD", "ETH/USD"], benchmark="BTC/USD", end="2026-10-02"); s = S.Session(sid, tape=TAPE)
s.submit(two_coins(s.packet())); s.submit({"no_pick": True, "why": "w"}); tT = s.now
ok(tT == U(2026, 10, 2), "set-up: at the third wake")
before = s.packet(fresh=True)
def later_iso(obj, path=""):
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += later_iso(v, path + "." + k)
    elif isinstance(obj, list):
        for v in obj:
            out += later_iso(v, path + "[]")
    elif isinstance(obj, str) and len(obj) >= 20 and obj[4:5] == "-" and obj[10:11] == "T":
        try:
            if S.parse(obj) > tT:
                out.append(path)
        except ValueError:
            pass
    return out
allowed = {".next_wake_utc", ".pick_template.expires_utc", ".feed.clock.next_open_utc", ".feed.clock.next_close_utc"}
ok(set(later_iso(before)) <= allowed, f"no time after the simulated now appears in the packet, except the schedule: {set(later_iso(before)) - allowed}")
edits = [(sym, "1Min", tT + dt.timedelta(minutes=i), 999.0, 999.0, 999.0, 999.0, 7.0) for sym in ("BTC/USD", "ETH/USD", "SOL/USD") for i in range(0, 600)]
edits += [(sym, "1Day", U(2026, 10, 2), 999.0, 999.0, 999.0, 999.0, 7.0) for sym in ("BTC/USD", "ETH/USD")]
TAPE.add_bars(edits); TAPE.add_news([dict(id=9, created=tT + dt.timedelta(seconds=1), updated=tT + dt.timedelta(seconds=1), headline="From the future", summary="f", source="x",
                                          url="https://example.com/9", symbols=["BTCUSD"])])
after = s.packet(fresh=True)
ok(after == before, "the packet at T is the same after every bar from T on, today's daily bar and a later story are all changed")
lk = s.look("bars", symbol="BTC/USD", timeframe="1Min", days=1); ok(all(S.parse(x["t"]) + dt.timedelta(minutes=1) <= tT for x in lk["data"]) and 999.0 not in [x["c"] for x in lk["data"]],
                                                                    "a minute-bar lookup shows only finished bars")
NOW[0] = tT; bb = SimBroker(TAPE, lambda: NOW[0], CFG, Path(TMP) / "peek_b.json"); bb.submit("BTC/USD", "buy", "gtc", "p1", notional=10.0)
ok(bb.order_by_cid("p1")["status"] == "accepted", "an order placed at T cannot fill from a bar that is not finished at T")
TAPE = MAIN_TAPE

# ---- skipping idle ticks gives the same result as running every tick
def run_fn(sid, fn):
    return S.run_code_trader(sid, fn, tape=TAPE)
def same(a, b):
    strip = lambda r: dict(summary=r["summary"], steps=r["steps"], account=r["account"], benchmark_hold=r["benchmark_hold"])
    return json.dumps(strip(a), sort_keys=True) == json.dumps(strip(b), sort_keys=True)
plan = {1: two_coins, 3: lambda p: dict(thesis="t", actions=[dict(symbol="SOL/USD", side="buy", usd=100, reason="r")], exits=[dict(symbol="SOL/USD", by_utc="2026-10-02T03:00:00Z")])}
a = run_fn(mk("skip_on", end="2026-10-02", benchmark="BTC/USD"), scripted(plan))
cfg0 = copy.deepcopy(CFG)
p = Path(TMP) / "runs"
mk("skip_off", end="2026-10-02", benchmark="BTC/USD"); m = json.loads((p / "skip_off" / "session.json").read_text()); m["config"]["tm_skip_idle_ticks"] = 0.0
(p / "skip_off" / "session.json").write_text(json.dumps(m)); b_ = run_fn("skip_off", scripted(plan))
ok(a["run_facts"]["ticks_skipped"] > 0 and b_["run_facts"]["ticks_skipped"] == 0 and a["run_facts"]["ticks_run"] < b_["run_facts"]["ticks_run"], "set-up: one run skipped idle ticks, the other ran every tick")
ok(same(a, b_), "skipping idle ticks gives exactly the same summary, steps, account and benchmark")
ok(any(c["symbol"] == "SOL/USD" for c in a["summary"]["closed"]) and a["summary"]["totals"]["orders"] >= 5, "set-up: the compared runs did trade, including a timed exit")

# ---- a restart continues the same session with the same result
mk("restart", end="2026-10-02", benchmark="BTC/USD"); s = S.Session("restart", tape=TAPE); fn = scripted(plan)
s.submit(fn(s.packet(), s.look)); s.crash_after = 40
try:
    s.submit(fn(s.packet(), s.look)); ok(False, "")
except RuntimeError:
    ok(True, "")
prog = json.loads((p / "restart" / "progress.json").read_text()); ok(prog["phase"] == "ticking" and prog["tick_i"] == 40, "set-up: the pretend crash left the session part way through its desk runs")
del s
c = run_fn("restart", fn)
ok(same(a, c), "the restarted session carries on and ends with the same result as one that never stopped")

# ---- the server: a trader needs only HTTP; a stopped server loses nothing
SV._tape = TAPE; SV.H.log_message = lambda *a: None; srv = SV.serve(0); port = srv.server_address[1]; th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
def call(path, body=None):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=None if body is None else json.dumps(body).encode(), method="GET" if body is None else "POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
mk("http", end="2026-10-02", benchmark="BTC/USD")
code, pk = call("/next?session=http"); ok(code == 200 and pk["step"] == 1 and call("/next?session=http")[1] == pk, "GET /next gives the packet, the same twice")
mk("http_look"); code, r = call("/look?session=http_look&what=bars&symbol=BTC/USD&timeframe=1Day&days=5"); ok(code == 200 and r["ok"] and r["data"], "GET /look works")
code, r = call("/pick?session=http", {"thesis": "x", "actions": [{"symbol": "BTC/USD", "side": "buy", "usd": 0, "reason": "r"}]}); ok(code == 400 and not r["ok"], "a bad pick answers 400 with the error")
code, r = call("/pick?session=http", plan[1](pk)); ok(code == 200 and r["ok"] and call("/status?session=http")[1]["step"] == 2, "POST /pick moves the clock")
code, r = call("/pick?session=http", plan[1](pk)); ok(code == 409 and not r["ok"] and call("/status?session=http")[1]["step"] == 2, "a second send of a pick, before /next is asked again, is refused and moves nothing")
srv.shutdown(); srv.server_close(); SV._sessions.clear()
srv = SV.serve(0); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
ok(call("/status?session=http")[1]["step"] == 2, "a new server carries on at the same step")
for k in range(2, 5):
    code, pk = call("/next?session=http"); body = plan[k](pk) if k in plan else {"no_pick": True, "why": "nothing"}
    code, r = call("/pick?session=http", body)
for _ in range(3):
    code, pk = call("/next?session=http"); call("/pick?session=http", {"no_pick": True, "why": "nothing"})
code, r = call("/next?session=http"); ok(code == 200 and r["status"] == "DONE", "after the last wake the server answers DONE")
ok(call("/pick?session=http", {"no_pick": True, "why": "w"})[1]["status"] == "DONE" and call("/look?session=http&what=price&symbols=BTC/USD")[1]["status"] == "DONE", "every later call answers DONE")
hr = json.loads((p / "http" / "result.json").read_text())
ok(hr["steps"][0]["bad_attempts"] == 1, "the bad attempt over HTTP is counted in the steps"); hr["steps"][0]["bad_attempts"] = 0
ok(same(a, hr), "the session run over HTTP, across a server restart, has the same result as the one run in-process")
ok(call("/next?session=nope")[0] == 404, "an unknown session answers 404")
srv.shutdown(); srv.server_close()

# ---- look limit
mk("looks"); s = S.Session("looks", tape=TAPE)
for i in range(int(CFG["tm_max_looks_per_wake"])):
    s.look("price", symbols="BTC/USD")
ok(not s.look("price", symbols="BTC/USD")["ok"] and len((p / "looks" / "looks.jsonl").read_text().splitlines()) == CFG["tm_max_looks_per_wake"], "lookups stop at tm_max_looks_per_wake, and each one is logged")

# ---- code traders: hold, and the random twin is the same for the same seed
h = run_fn(mk("hold", trader="HOLD", end="2026-10-02", benchmark="BTC/USD", watch=["BTC/USD"]), C.hold("BTC/USD"))
ht = h["summary"]["traders"][0]
ok(h["summary"]["totals"]["orders"] == 1 and ht["positions"][0]["symbol"] == "BTC/USD" and abs(ht["cash_usd"] - h["account"]["cash_usd"]) < 0.005, "hold buys once and keeps it; books and account agree")
ok(abs(ht["gain_pct"] - ht["hold_gain_pct"]) < 0.003, "hold ends close to the benchmark hold (the gap is the half spread)")
src = json.loads((p / "skip_on" / "result.json").read_text())
t1 = run_fn(mk("twin1", trader="TWIN", end="2026-10-02", wakes=src["session"]["wakes"], benchmark="BTC/USD"), C.random_twin(src, 7, tape=TAPE))
t2 = run_fn(mk("twin2", trader="TWIN", end="2026-10-02", wakes=src["session"]["wakes"], benchmark="BTC/USD"), C.random_twin(src, 7, tape=TAPE))
t3 = run_fn(mk("twin3", trader="TWIN", end="2026-10-02", wakes=src["session"]["wakes"], benchmark="BTC/USD"), C.random_twin(src, 8, tape=TAPE))
pk1 = [st["pick"] for st in t1["steps"]]; pk2_ = [st["pick"] for st in t2["steps"]]
ok(pk1 == pk2_ and same(t1, t2), "the random twin is the same for the same seed: same picks, same result")
buys = [st for st in t1["steps"] if st["pick"]]
ok([st["utc"] for st in buys] == [st["utc"] for st in src["steps"] if st["pick"] and any(a["side"] == "buy" for a in st["pick"]["actions"])], "the twin buys at the same wakes the AI bought")
ok(sum(a["usd"] for st in buys for a in st["pick"]["actions"]) == 900, "the twin buys the same dollars (400 + 400 + 100)")
ok(all(x.get("by_utc") or x.get("stop") or x.get("target") for st in buys for x in st["pick"]["exits"]), "the twin carries the AI's exits over in percent and holding time")
ok(all(t["pick"] is None or all(a["symbol"] in ("BTC/USD", "ETH/USD", "SOL/USD") for a in t["pick"]["actions"]) for t in t3["steps"]), "a crypto twin draws from the crypto list")

# ---- a stock session: wakes on trading days in New York time, no ticks overnight, one after the close
mk("stock1", trader="A02", market="stocks", start="2026-10-01", end="2026-10-02", benchmark="SPY", watch=["AAA"])
s = S.Session("stock1", tape=TAPE)
ok(s.meta["wakes"] == ["2026-10-01T14:00:00Z", "2026-10-01T16:30:00Z", "2026-10-01T19:30:00Z", "2026-10-02T14:00:00Z", "2026-10-02T16:30:00Z", "2026-10-02T19:30:00Z"],
   "stock wakes at 10:00, 12:30 and 15:30 New York on each trading day")
sch = s.schedule(2); ok(sch[0] == U(2026, 10, 1, 19, 30) and U(2026, 10, 1, 20) in sch and U(2026, 10, 1, 20, 5) not in sch and U(2026, 10, 2, 13, 30) in sch and len(sch) == 6 + 1 + 6,
                        "after the last wake of a day: ticks to the close, one tick at the close, none overnight, then from the open")
ok(s.schedule(5)[-1] == U(2026, 10, 2, 20), "the session ends with one tick after the last close")
fn = scripted({1: lambda pk: dict(thesis="t", actions=[dict(symbol="AAA", side="buy", usd=300, reason="r"), dict(symbol="BBB", side="buy", usd=100, reason="r")],
                                  exits=[dict(symbol="AAA", by_utc="2026-10-02T15:00:00Z")])})
r = S.run_code_trader("stock1", fn, tape=TAPE); o = {x["symbol"] + x["side"]: x for x in r["summary"]["orders"]}
ok(o["AAAbuy"]["filled_utc"] == "2026-10-01T14:00:00Z" and o["AAAsell"]["utc"] == "2026-10-02T15:00:00Z", "the stock buy fills at the wake's minute and the timed exit sells at its tick the next day")
ok(o["BBBbuy"]["status"] == "rejected" and r["summary"]["traders"][0]["closed_trades"] == 1, "a stock with no minute bars is refused by the pretend broker and shown as refused")
ok(abs(r["summary"]["traders"][0]["cash_usd"] - r["account"]["cash_usd"]) < 0.005, "stock session: books and account agree to the cent")

# ---- half-hour and hour bars for a coin are built from minutes, and never include a bucket that is still open
BT = Tape(TMP + "/tape_built.sqlite"); t0 = U(2026, 10, 1, 10)
BT.add_bars([("BTC/USD", "1Min", t0 + dt.timedelta(minutes=i), 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i, 1.0) for i in range(150)])
hb = S.built_bars(BT, "BTC/USD", 3600, U(2026, 10, 1, 9), U(2026, 10, 1, 12, 17), 2000)
ok([x["t"] for x in hb] == [U(2026, 10, 1, 10), U(2026, 10, 1, 11)], "hour bars: the hour still open at the look time is not returned")
ok(hb[0]["o"] == 100.0 and hb[0]["h"] == 160.0 and hb[0]["l"] == 99.0 and hb[0]["c"] == 159.5 and hb[0]["v"] == 60.0, "an hour bar is the first open, highest high, lowest low, last close and summed volume of its minutes")
hb2 = S.built_bars(BT, "BTC/USD", 1800, U(2026, 10, 1, 9), U(2026, 10, 1, 12, 30), 3)
ok([x["t"] for x in hb2] == [U(2026, 10, 1, 11), U(2026, 10, 1, 11, 30), U(2026, 10, 1, 12)] and hb2[-1]["c"] == 249.5, "half-hour bars: a bucket that ended exactly at the look time is returned, and the limit keeps the newest")
ok(json.loads((S.create("bm1", "BM", "m", "practice/traders/B01_crypto_swing_price_only.md", "2026-10-01", "2026-10-02", watch=["AVAX/USD", "BTC/USD"], tape=BT) / "session.json").read_text())["benchmark"] == "BTC/USD", "a coin session is measured against bitcoin when bitcoin is on its list")

# ---- a session made without news shows none, even when the tape holds headlines for that time
sn = S.Session(mk("nonews1", news=False, start="2026-10-01", end="2026-10-02"), tape=MAIN_TAPE); sw = S.Session(mk("withnews1", start="2026-10-01", end="2026-10-02"), tape=MAIN_TAPE)
while not sw.done() and not sw.packet()["feed"]["news"]:
    sn.submit({"no_pick": True, "why": "w"}); sw.submit({"no_pick": True, "why": "w"})
ok(not sw.done() and sw.packet()["feed"]["news"] and sn.now == sw.now and sn.packet()["feed"]["news"] == [], "price-only session: the packet has no headlines at a time when a news session has some")
lk = sn.look("news", symbols="BTC/USD", days=5); ok(not lk["ok"] and "no news" in lk["error"] and sn.looks_left() == CFG["tm_max_looks_per_wake"], "price-only session: a news lookup is refused and not counted")

n_log = len(Path(os.environ["TM_SESSIONS_LOG"]).read_text().splitlines())
ok(n_log == log0 + len([d for d in p.iterdir() if (d / "session.json").exists()]), "every session made is one line in the sessions log")

shutil.rmtree(TMP, ignore_errors=True)
print(f"{N[0]} checks passed")
