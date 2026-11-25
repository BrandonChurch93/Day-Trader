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

# ---- crypto sessions never see stock symbols, stock movers, or sec_edgar/finbold news even with stocks on the tape
ISO_T = Tape(TMP + "/tape_iso.sqlite")
ISO_T.add_sessions([("2026-10-01", U(2026, 10, 1, 13, 30), U(2026, 10, 1, 20, 0)),
                    ("2026-10-02", U(2026, 10, 2, 13, 30), U(2026, 10, 2, 20, 0))])
ISO_T.add_universe("2026-10-01", ["SPY", "AAPL"])
ISO_T.add_universe("2026-10-02", ["SPY", "AAPL"])
ISO_T.add_bars(
    [("BTC/USD", "1Min", U(2026, 10, 1, 0) + dt.timedelta(minutes=m), 100.0, 101.0, 99.0, 100.5, 5.0) for m in range(24 * 60)]
    + [("BTC/USD", "1Day", U(2026, 9, 30, 0), 99.0, 101.0, 98.0, 100.0, 500.0),
       ("SPY", "1Day", U(2026, 9, 30, 4), 500.0, 502.0, 499.0, 501.0, 1e6),
       ("AAPL", "1Day", U(2026, 9, 30, 4), 200.0, 205.0, 199.0, 204.0, 1e6)]
    + [("SPY", "1Min", U(2026, 10, 1, 13, 30) + dt.timedelta(minutes=m), 501.0, 502.0, 500.0, 501.5, 1000.0) for m in range(180)]
    + [("AAPL", "1Min", U(2026, 10, 1, 13, 30) + dt.timedelta(minutes=m), 205.0, 210.0, 204.0, 209.0, 2000.0) for m in range(180)]
)
ISO_T.add_news([
    dict(id=9001, created=U(2026, 10, 1, 11, 0), updated=U(2026, 10, 1, 11, 0),
         headline="8-K AAPL Item 2.02", summary="SEC filing", source="sec_edgar", url="https://sec.gov/1", symbols=["AAPL"]),
    dict(id=9002, created=U(2026, 10, 1, 11, 30), updated=U(2026, 10, 1, 11, 30),
         headline="Apple stock surges", summary="Finbold story", source="finbold", url="https://finbold.com/1", symbols=["AAPL", "SPY"]),
    dict(id=9003, created=U(2026, 10, 1, 11, 45), updated=U(2026, 10, 1, 11, 45),
         headline="Bitcoin holds steady", summary="Crypto story", source="cryptoslate", url="https://cryptoslate.com/1", symbols=["BTC/USD"]),
])
sc_iso = S.Session(S.create("iso_crypto", "C1", "m", "practice/traders/B01_crypto_swing_price_only.md",
                            "2026-10-01", "2026-10-01", market="crypto", watch=["BTC/USD"], news=True, tape=ISO_T).name, tape=ISO_T)
sc_iso.submit({"no_pick": True, "why": "advance to 12:00 UTC"})
pk_iso = sc_iso.packet()
ok(pk_iso["feed"]["movers"]["gainers"] == [] and pk_iso["feed"]["movers"]["losers"] == [] and pk_iso["feed"]["most_active"] == [],
   "crypto packet blanks stock movers and most_active even with stocks on the tape")
ok(all("/" in sym for sym in pk_iso["feed"]["prices"]), "crypto packet prices contain only crypto symbols")
ok(all(a.get("source") not in ("sec_edgar", "finbold") and all("/" in sym for sym in a.get("symbols", [])) for a in pk_iso["feed"]["news"]),
   "crypto packet news contains no sec_edgar/finbold items or stock symbols")
ok(len(pk_iso["feed"]["news"]) == 1 and pk_iso["feed"]["news"][0]["headline"] == "Bitcoin holds steady",
   "crypto packet still includes matching crypto news")
looks0 = sc_iso.looks_left()
ok(not sc_iso.look("bars", symbol="SPY", timeframe="1Min")["ok"] and not sc_iso.look("price", symbols="AAPL")["ok"] and not sc_iso.look("news", symbols="AAPL")["ok"],
   "crypto session refuses stock bars, price, and news lookups")
ok(sc_iso.looks_left() == looks0, "refused stock lookups in a crypto session do not spend a lookup")
ln_iso = sc_iso.look("news", days=2)
ok(ln_iso["ok"] and len(ln_iso["data"]) == 1 and ln_iso["data"][0]["source"] == "cryptoslate"
   and all(a["source"] not in ("sec_edgar", "finbold") and all("/" in sym for sym in a["symbols"]) for a in ln_iso["data"]),
   "crypto no-symbol news lookup returns only session-coin news and never sec_edgar or finbold")

# ---- stock session: early-close wakes, finished minutes only, 1Day only after close, 30Min/1Hour from 1Min, half-spread fills, regular-hours only
STK_T = Tape(TMP + "/tape_stock_checks.sqlite")
STK_T.add_sessions([
    ("2026-07-02", U(2026, 7, 2, 13, 30), U(2026, 7, 2, 20, 0)),   # regular day (09:30-16:00 NY)
    ("2026-07-03", U(2026, 7, 3, 13, 30), U(2026, 7, 3, 17, 0)),   # early close (09:30-13:00 NY)
])
STK_T.add_universe("2026-07-02", ["SPY", "STK"])
STK_T.add_universe("2026-07-03", ["SPY", "STK"])
# 1Day bars for 2026-07-01 (prior), 2026-07-02 (regular, inflated high/close to detect any pre-close leak), 2026-07-03 (early close)
STK_T.add_bars([
    ("SPY", "1Day", U(2026, 7, 1, 4), 500.0, 501.0, 499.0, 500.0, 1e6),
    ("STK", "1Day", U(2026, 7, 1, 4), 100.0, 101.0, 99.0, 100.0, 1e6),
    ("SPY", "1Day", U(2026, 7, 2, 4), 500.0, 505.0, 498.0, 504.0, 1e6),
    ("STK", "1Day", U(2026, 7, 2, 4), 100.0, 999.0, 10.0, 888.0, 1e6),
    ("SPY", "1Day", U(2026, 7, 3, 4), 504.0, 506.0, 503.0, 505.0, 1e6),
    ("STK", "1Day", U(2026, 7, 3, 4), 110.0, 115.0, 109.0, 114.0, 1e6),
])
# 1Min bars on 2026-07-02 (09:30-15:59 NY = 390 mins): 100.0 through 12:29 NY, then 500.0 from 12:30 NY onward
stk_mins = []
for m in range(390):
    t = U(2026, 7, 2, 13, 30) + dt.timedelta(minutes=m)
    px = 100.0 if m < 180 else (200.0 if m == 180 else 250.0)
    stk_mins.append(("STK", "1Min", t, px, px + 1.0, px - 1.0, px, 10000.0))
    stk_mins.append(("SPY", "1Min", t, 500.0, 501.0, 499.0, 500.0, 10000.0))
for m in range(210):
    t = U(2026, 7, 3, 13, 30) + dt.timedelta(minutes=m)
    stk_mins.append(("STK", "1Min", t, 110.0, 111.0, 109.0, 110.0, 10000.0))
    stk_mins.append(("SPY", "1Min", t, 504.0, 505.0, 503.0, 504.0, 10000.0))
STK_T.add_bars(stk_mins)
ss_chk = S.Session(S.create("stk_chk", "S1", "m", "practice/traders/A01_stock_news_catalyst.md",
                            "2026-07-02", "2026-07-03", market="stocks", benchmark="SPY", watch=["STK", "SPY"], tape=STK_T).name, tape=STK_T)
ok(ss_chk.meta["wakes"] == ["2026-07-02T14:00:00Z", "2026-07-02T16:30:00Z", "2026-07-02T19:30:00Z",
                            "2026-07-03T14:00:00Z", "2026-07-03T16:30:00Z"],
   "stock wakes drop 15:30 NY on an early-close day (13:00 NY close)")
ss_chk.submit({"no_pick": True, "why": "advance to 12:30 NY"})
pk_mid = ss_chk.packet()
ok(pk_mid["utc"] == "2026-07-02T16:30:00Z" and pk_mid["feed"]["prices"]["STK"]["price"] == 100.0
   and pk_mid["feed"]["prices"]["STK"]["day_high"] == 101.0 and pk_mid["feed"]["prices"]["STK"]["day_low"] == 99.0,
   "stock packet at 12:30 NY uses only finished minutes (<= 12:29 NY) and never today's 1Day bar or the 12:30 minute")
l_1m = ss_chk.look("bars", symbol="STK", timeframe="1Min", days=1)
ok(l_1m["ok"] and l_1m["data"][-1]["t"] == "2026-07-02T16:29:00Z" and all(b["c"] == 100.0 for b in l_1m["data"]),
   "stock 1Min lookup at 12:30 NY ends at 12:29 NY")
l_1d = ss_chk.look("bars", symbol="STK", timeframe="1Day", days=5)
ok(l_1d["ok"] and [b["t"] for b in l_1d["data"]] == ["2026-07-01T04:00:00Z"],
   "stock 1Day lookup before the close hides today's daily bar")
l_30m = ss_chk.look("bars", symbol="STK", timeframe="30Min", days=1)
l_1h = ss_chk.look("bars", symbol="STK", timeframe="1Hour", days=1)
ok(l_30m["ok"] and l_30m["data"][-1]["t"] == "2026-07-02T16:00:00Z" and l_1h["ok"] and l_1h["data"][-1]["t"] == "2026-07-02T15:00:00Z",
   "stock 30Min and 1Hour lookups build finished buckets from 1Min bars when 30Min bars are absent")
ok(STK_T.bars("STK", "1Day", U(2026, 7, 1, 0), U(2026, 7, 2, 20, 5))[-1]["t"] == U(2026, 7, 2, 4),
   "stock 1Day bar becomes visible after the session close")
# Direct SimBroker check: fill at next minute's open +/- tm_stock_half_spread_bps (zero fee), and refusal outside regular hours
clk_stk = [U(2026, 7, 2, 16, 29, 30)]
sb_stk = SimBroker(STK_T, lambda: clk_stk[0], CFG, TMP + "/acct_stk_chk.json")
sb_stk.submit("STK", "buy", "day", "stk-b1", notional=500.0)
clk_stk[0] = U(2026, 7, 2, 16, 31, 0)
ob1 = sb_stk.order_by_cid("stk-b1")
ok(ob1["status"] == "filled" and ob1["filled_at"] == "2026-07-02T16:30:00Z"
   and abs(float(ob1["filled_avg_price"]) - 200.0 * (1 + HS_S)) < 1e-6 and ob1["sim"]["fee_usd"] == 0.0,
   "stock buy fills at the next minute's open plus tm_stock_half_spread_bps with zero fee")
sb_stk.submit("STK", "sell", "day", "stk-s1", qty=float(ob1["filled_qty"]))
clk_stk[0] = U(2026, 7, 2, 16, 32, 0)
os1 = sb_stk.order_by_cid("stk-s1")
ok(os1["status"] == "filled" and os1["filled_at"] == "2026-07-02T16:31:00Z"
   and abs(float(os1["filled_avg_price"]) - 250.0 * (1 - HS_S)) < 1e-6 and os1["sim"]["fee_usd"] == 0.0,
   "stock sell fills at the next minute's open minus tm_stock_half_spread_bps with zero fee")
for bad_t, label in [(U(2026, 7, 2, 13, 25), "pre-market"), (U(2026, 7, 2, 20, 0), "after regular close"), (U(2026, 7, 3, 17, 0), "after early close")]:
    clk_stk[0] = bad_t
    refused_closed = False
    try:
        sb_stk.submit("STK", "buy", "day", f"closed-{label}", notional=100.0)
    except B.Refused as e:
        refused_closed = "closed" in str(e)
    ok(refused_closed, f"stock order outside regular hours ({label}) is refused")

# ---- weights sessions (timemachine/weights.py): the trader answers with target weights; one book function for session, twins and scorer
import re
from timemachine import weights as W, score_weights as SW
WCFG = W.full_config(); MC = WCFG["tm_weights_min_change"]
ok(all(k in WCFG for k in W.W_KEYS) and 0 < MC < 1, "set-up: every tm_weights_ key is in config/thresholds.yaml")
WD0 = U(2026, 9, 1)
def wbtc(i):  # every minute has its own price, so the fill minute can be told from the bar before it
    return 100.0 + i * 0.0001
def weth(i):
    return 50.0 - i * 0.0001
def make_wtape(path):
    tp = Tape(path); rows = []
    for i in range(10 * 1440):
        t = WD0 + dt.timedelta(minutes=i)
        if t == U(2026, 9, 3, 12):
            continue  # a gap: no BTC trade in this minute
        rows.append(("BTC/USD", "1Min", t, wbtc(i), wbtc(i), wbtc(i), wbtc(i), 10.0))
        rows.append(("ETH/USD", "1Min", t, weth(i), weth(i), weth(i), weth(i), 10.0))
    for j in range(-120, 10):  # daily closes: BTC 1000 + j, ETH 500 - j
        rows.append(("BTC/USD", "1Day", WD0 + dt.timedelta(days=j), 1.0, 1.0, 1.0, 1000.0 + j, 1.0))
        rows.append(("ETH/USD", "1Day", WD0 + dt.timedelta(days=j), 1.0, 1.0, 1.0, 500.0 - j, 1.0))
    days = ["2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04", "2026-09-08", "2026-09-09", "2026-09-10"]  # no 09-07 (holiday), no 09-11
    sess = [(d, dt.datetime.fromisoformat(d + "T13:30:00+00:00"), dt.datetime.fromisoformat(d + "T20:00:00+00:00")) for d in days]
    tp.add_sessions(sess)
    for n, (d, op, cl) in enumerate(sess):
        tp.add_universe(d, ["AAA", "BBB", "SPY"]); t = op - dt.timedelta(minutes=30); m = 0
        while t < cl + dt.timedelta(minutes=30):  # extended-hours minutes too, which must never fill
            for k, sym in enumerate(("AAA", "BBB", "SPY")):
                px = 10.0 * (k + 1) + n + m * 0.001; rows.append((sym, "1Min", t, px, px, px, px, 1e6))
            m += 1; t += dt.timedelta(minutes=1)
    for j in range(-120, 12):
        for k, sym in enumerate(("AAA", "BBB", "SPY")):
            rows.append((sym, "1Day", WD0 + dt.timedelta(days=j, hours=4), 1.0, 1.0, 1.0, 10.0 * (k + 1) + j * 0.1, 1e6))
    tp.add_bars(rows)
    tp.add_news([dict(id=101, created=U(2026, 9, 1, 3), updated=U(2026, 9, 1, 3), headline="BTC story one", summary="a", source="x", url="https://example.com/101", symbols=["BTCUSD"]),
                 dict(id=102, created=U(2026, 9, 1, 4), updated=U(2026, 9, 1, 4), headline="Other coin story", summary="b", source="x", url="https://example.com/102", symbols=["ZZZUSD"]),
                 dict(id=103, created=U(2026, 9, 1, 13), updated=U(2026, 9, 5), headline="BTC story two", summary="c", source="x", url="https://example.com/103", symbols=["BTCUSD"])])
    return tp
WT = make_wtape(TMP + "/wtape.sqlite")
def wmk(sid, syms=("BTC/USD", "ETH/USD"), start="2026-09-01", end="2026-09-03", **kw):
    W.create(sid, "W01", "script", "timemachine/TRADER_BRIEF_WEIGHTS.md", start, end, list(syms), tape=WT, **kw); return W.WSession(sid, tape=WT)
def ans(w=None, why="scripted"):
    return {"no_change": True, "why": why} if w is None else {"weights": w, "why": why}
def go(s, body):
    s.packet(); return s.submit(body)

# wakes
s = wmk("w_basic")
ok(s.meta["wakes"] == [S.iso(U(2026, 9, d, h)) for d in (1, 2, 3) for h in (0, 12)] and s.meta["end_utc"] == "2026-09-04T00:00:00Z",
   "a crypto weights session wakes at tm_crypto_wake_hours_utc each day and ends at midnight after the last day")
ws, we = W.make_wakes(WT, "stocks", "2026-09-01", "2026-09-11", W.default_rules("stocks", "weekly", WCFG))
ok(ws == [U(2026, 9, 4, 19, 30), U(2026, 9, 10, 19, 30)] and we == U(2026, 9, 10, 20),
   "weekly stock wakes: Friday 15:30 New York, or the last session day before it when Friday has no session; the session ends at the last close")
wl2, _ = W.make_wakes(WT, "crypto", "2026-04-01", "2026-11-23", W.default_rules("crypto", "daily", WCFG))
ok(len(wl2) == 2 * 237, "a session may span many months (April to November, two wakes a day)")
ok(W.make_wakes(WT, "crypto", "2026-09-01", "2026-09-03", [dict(every="day", utc_hours=[0]), dict(every="week", weekday=2, ny_time=12.0)])[0]
   == [U(2026, 9, 1), U(2026, 9, 2), U(2026, 9, 2, 16), U(2026, 9, 3)], "a list of wake rules is merged into one schedule")

# refused answers: nothing moves
pk0 = s.packet()
for bad, what in [(ans({"BTC/USD": 1.2}), "a weight over 1"), (ans({"BTC/USD": -0.1}), "a negative weight"), (ans({"BTC/USD": 0.6, "ETH/USD": 0.5}), "weights adding up to more than 1"),
                  (ans({"DOGE/USD": 0.1}), "a symbol not allowed"), (ans({"BTC/USD": True}), "a weight that is not a number"), ({"weights": {"BTC/USD": 0.5}}, "an answer with no why"),
                  ({"weights": {"BTC/USD": 0.5}, "why": "x", "stop": 90}, "an answer with a stop in it"), ([0.5], "a body that is not an object")]:
    r = s.submit(bad); ok(not r["ok"] and s.prog["k"] == 0 and s.prog["book"]["cash"] == WCFG["tm_account_start_usd"], f"refused, nothing traded, the clock did not move: {what}")
ok(s.prog["bad"]["0"] == 8 and s.packet() == pk0, "refused answers are counted and the packet is unchanged")

# fills at the next minute's open with costs
r = go(s, ans({"BTC/USD": 0.5}, "half in"))
t0 = r["trades"][0]; o0 = wbtc(0)
ok(r["ok"] and t0["fill_utc"] == "2026-09-01T00:00:00Z" and t0["open"] == o0 and abs(t0["price"] - o0 * (1 + HS_C)) < 1e-12,
   "a crypto answer at a wake fills at the open of the minute that starts at the wake, plus tm_crypto_half_spread_bps")
ok(abs(t0["qty"] - 500.0 / o0) < 1e-12 and abs(s.prog["book"]["cash"] - (1000.0 - 500.0 * (1 + HS_C) * (1 + FEE))) < 1e-9 and abs(t0["fee_usd"] - 500.0 * (1 + HS_C) * FEE) < 1e-9,
   "a weight is a share of the book at the fill minute's open; cash pays the spread and practice_crypto_fee_bps_added on top")
ok(t0["fill_utc"] >= s.meta["wakes"][0] and S.parse(t0["fill_utc"]) + dt.timedelta(minutes=1) <= s.wakes[1], "the fill minute starts at or after the wake and ends before the next wake")
r = go(s, ans({"BTC/USD": 0.5 + MC / 2}, "a small nudge"))
ok(r["ok"] and r["changed"] and not r["trades"] and r["skipped"] and "tm_weights_min_change" in r["skipped"][0]["why"] and s.prog["book"]["target"] == {"BTC/USD": 0.5 + MC / 2},
   "a change smaller than tm_weights_min_change is not traded (and the reason is recorded)")
r = go(s, ans(None, "keep")); ok(r["ok"] and not r["changed"] and not r["trades"], "no_change trades nothing")
r = go(s, ans({"BTC/USD": 0.5 + MC / 2}, "same again")); ok(r["ok"] and not r["changed"] and not r["trades"], "a repeated answer trades nothing")
cash_before = s.prog["book"]["cash"]; qb = s.prog["book"]["qty"]["BTC/USD"]
r = go(s, ans({"ETH/USD": 0.3}, "switch"))   # wake 2026-09-03 00:00
ts = {t["symbol"]: t for t in r["trades"]}; i = int((U(2026, 9, 3) - WD0).total_seconds() // 60)
ok(list(ts) == ["BTC/USD", "ETH/USD"] and ts["BTC/USD"]["side"] == "sell" and abs(ts["BTC/USD"]["qty"] - qb) < 1e-12 and ts["BTC/USD"]["open"] == wbtc(i)
   and abs(ts["BTC/USD"]["price"] - wbtc(i) * (1 - HS_C)) < 1e-12 and ts["ETH/USD"]["open"] == weth(i) and "BTC/USD" not in s.prog["book"]["qty"],
   "a switch sells first (the whole holding when the weight goes to zero), then buys, both at the next minute's open with the spread")
V = cash_before + qb * wbtc(i); proceeds = qb * wbtc(i) * (1 - HS_C) * (1 - FEE); qe = 0.3 * V / weth(i)
ok(abs(ts["ETH/USD"]["qty"] - qe) < 1e-9 and abs(s.prog["book"]["cash"] - (cash_before + proceeds - 0.3 * V * (1 + HS_C) * (1 + FEE))) < 1e-9,
   "the new weight is a share of the book valued at the fill minute's opens, and cash is what is left after spread and fee")
r = go(s, ans({"ETH/USD": 0.3, "BTC/USD": 0.2}, "gap"))  # wake 2026-09-03 12:00: BTC has no bar in that minute
tb = [t for t in r["trades"] if t["symbol"] == "BTC/USD"]
ok(tb and tb[0]["fill_utc"] == "2026-09-03T12:01:00Z" and tb[0]["open"] == wbtc(2 * 1440 + 721), "a gap in the minutes: the fill waits for the next recorded minute")
book_mid = json.loads(json.dumps(s.prog["book"]))
mc_cfg = dict(WCFG, tm_weights_min_change=0.5); b2 = W.new_book(1000.0); b2["qty"] = {"ETH/USD": 1.0}; b2["cash"] = 950.0; b2["target"] = {"ETH/USD": 0.05}
rr = W.step_book(b2, {}, dict(fills={"ETH/USD": ["2026-09-01T00:00:00Z", 50.0]}, marks={"ETH/USD": 50.0}), mc_cfg, False)
ok(rr["trades"] and rr["trades"][0]["side"] == "sell" and "ETH/USD" not in b2["qty"], "a move to zero weight is always traded, even when smaller than tm_weights_min_change")
ok(s.done() and (s.dir / "result.json").exists(), "the session finishes after the last wake")
res = json.loads((s.dir / "result.json").read_text()); em = res["end_marks"]
ok(abs(res["final"]["value_usd"] - (res["final"]["cash_usd"] + sum(q * em[k] for k, q in res["final"]["holdings"].items()))) < 1e-9,
   "the final value is cash plus each holding at the tape's last price at the end")
lines = [json.loads(x) for x in (s.dir / "records" / "wakes.jsonl").read_text().splitlines()]
ok(len(lines) == 6 and all(set(("asked", "weights_after", "value_before", "value_after_fill", "why")) <= set(x) for x in lines) and lines[0]["why"] == "half in"
   and lines[2]["asked"] is None, "every wake is recorded: weights asked, weights held after fills, book value, and the why text")
ok(sorted(f.name for f in (s.dir / "picks" / "W01").iterdir())[0] == "20260901T0000Z.json", "each answer is kept as sent, in picks/<TRADER>/<wake id>.json")
logw = [json.loads(x) for x in Path(os.environ["TM_SESSIONS_LOG"]).read_text().splitlines() if '"w_basic"' in x]
ok(len(logw) == 1 and logw[0]["kind"] == "weights" and logw[0]["wakes"]["count"] == 6 and logw[0]["symbols"] == ["BTC/USD", "ETH/USD"], "the session is one line in SESSIONS.jsonl with kind weights")

# no bar after the wake is ever visible
s = wmk("w_peek", news=True); script = [ans({"BTC/USD": 0.4}), ans(None), ans({"ETH/USD": 0.5}), ans(None), ans({"BTC/USD": 0.1, "ETH/USD": 0.1}), ans(None)]
src_db = sqlite3.connect(TMP + "/wtape.sqlite")
for k in range(6):
    pk = s.packet(); w = s.wakes[k]; we_ = int(w.timestamp())
    dst = TMP + f"/wtape_peek{k}.sqlite"; dst_db = sqlite3.connect(dst); src_db.backup(dst_db)
    dst_db.execute("UPDATE bars SET o=o*2, h=h*2, l=l*2, c=c*2 WHERE (tf='1Min' AND t > ?) OR (tf='1Day' AND symbol LIKE '%/%' AND t > ?)", (we_ - 60, we_ - 86400))
    dst_db.execute("UPDATE news SET headline = headline || ' CHANGED' WHERE created > ?", (we_,)); dst_db.commit(); dst_db.close()
    peek = W.WSession("w_peek", tape=Tape(dst)).packet(fresh=True)
    ok(peek == pk, f"wake {k}: the packet is the same when every bar and story after the wake is changed")
    stamps = re.findall(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", json.dumps({x: v for x, v in pk.items() if x != "next_wake_utc"}))
    ok(stamps and max(stamps) <= S.iso(w), f"wake {k}: no time in the packet is after the wake")
    if k == 1:
        lk = s.look("bars", symbol="BTC/USD", timeframe="1Min", days=1)
        ok(lk["ok"] and lk["data"] and max(S.parse(b["t"]) for b in lk["data"]) + dt.timedelta(minutes=1) <= w, "a lookup of minute bars ends at the last minute finished by the wake")
    s.submit(script[k])
src_db.close()
pk1 = json.loads((s.dir / "packets" / "1.json").read_text()); pk2 = json.loads((s.dir / "packets" / "2.json").read_text())
ok([n["headline"] for n in pk1["news"]] == ["BTC story one"] and [n["headline"] for n in pk2["news"]] == ["BTC story two"] and pk2["news"][0]["edited_later"],
   "news: only headlines since the last wake, only for the session's symbols, marked when edited later")
ok(W.WSession("w_basic", tape=WT).meta["news"] is False and json.loads((S.runs_dir() / "w_basic" / "packets" / "1.json").read_text())["news"] is None, "a session without news shows none")
WT.add_news([dict(id=200 + i, created=U(2026, 9, 6, 1 + i), updated=U(2026, 9, 6, 1 + i), headline=f"capped {i}", summary="s", source="sec_edgar" if i == 3 else "x",
                  url=f"https://example.com/c{i}", symbols=["BTCUSD"]) for i in range(4)])
sc_ = wmk("w_cap", start="2026-09-06", end="2026-09-06", news=True); go(sc_, ans(None)); sc_.cfg["tm_weights_max_headlines_per_symbol"] = 1
pkc = sc_.packet(fresh=True)
ok([n["headline"] for n in pkc["news"]] == ["capped 3", "capped 2"] and pkc["news_left_out"] == {"BTC/USD": 2},
   "news: at most the cap of headlines per symbol, newest first, every filing kept, and the count left out is shown")
r2 = pk2["symbols"]["BTC/USD"]  # wake 2026-09-02 00:00: the last closed daily bar is 2026-09-01 (close 1000)
ok(r2["last_daily_bar"] == "2026-09-01T00:00:00Z" and abs(r2["return_1d"] - (1000.0 / 999.0 - 1)) < 1e-12 and abs(r2["return_91d"] - (1000.0 / 909.0 - 1)) < 1e-12,
   "trailing returns come from closed 1Day bars only, over tm_weights_return_days")

# the same answers twice give the same result; a restart loses nothing
def wrun(sid, stop_at=None, **kw):
    s = wmk(sid, **kw)
    for k, b in enumerate(script):
        if stop_at is not None and k == stop_at:
            s = W.WSession(sid, tape=WT)  # as if the server stopped and a new one opened the folder
        go(s, b)
    return json.loads((s.dir / "result.json").read_text())
strip = lambda r: (r["steps"], r["final"])
ra, rb = wrun("w_twice_a"), wrun("w_twice_b")
ok(strip(ra) == strip(rb), "a second run with the same answers gives the same steps, fills and final value")
ok(strip(wrun("w_restart", stop_at=3)) == strip(ra), "a session reopened mid-way carries on with the same result")

# a session that starts long equals hold when the weights never change
s = wmk("w_long", opening={"BTC/USD": 1.0})
ok(s.packet()["book"]["target_now"] == {"BTC/USD": 1.0}, "the opening target is shown at the first wake")
for _ in range(6):
    go(s, ans(None))
rl = json.loads((s.dir / "result.json").read_text()); qh = 1000.0 / (1 + FEE) / (wbtc(0) * (1 + HS_C))
ok(abs(rl["final"]["holdings"]["BTC/USD"] - qh) < 1e-12 and abs(rl["final"]["value_usd"] - qh * rl["end_marks"]["BTC/USD"]) < 1e-9,
   "a session that starts long buys at the first minute with costs, and with no change it is just holding")
s = wmk("w_long_same", opening={"BTC/USD": 1.0})
for _ in range(6):
    go(s, ans({"BTC/USD": 1.0}))
ok(json.loads((s.dir / "result.json").read_text())["final"] == rl["final"], "answering the same weights every wake equals no change")
sc = SW.score("w_long", tape=WT, draws=20)
ok(abs(sc["twins"]["hold_BTC/USD"]["stats"]["final_value_usd"] - rl["final"]["value_usd"]) < 1e-9 and sc["twins"]["shuffle"]["model_percentile"] == 0.0
   and not sc["twins"]["shuffle"]["model_above_median"], "the scorer's bitcoin hold equals a long session that never changes; its shuffles tie with it, and a tie counts against the model")
tw1 = sc["twins"]["shuffle_runs"]
ok(tw1["runs"] == 1 and tw1["note"] == "no timing to judge" and tw1["model_percentile"] is None and tw1["final_gain_pct"]["low"] == tw1["final_gain_pct"]["high"] == sc["model_stats"]["final_gain_pct"],
   "shuffle_runs: a model with one run gets twins identical to itself, and the scorer says no timing to judge instead of a percentile")

# the scorer: numbers only from the records and the tape, seeded
sc1, sc2 = SW.score("w_twice_a", tape=WT, draws=30), SW.score("w_twice_a", tape=WT, draws=30)
ok(sc1 == sc2 and sc1["twins"]["shuffle"]["final_gain_pct"]["n"] == 30 and 0 <= sc1["twins"]["shuffle"]["model_percentile"] <= 100 and "hold_equal_weight" in sc1["twins"],
   "score_weights.py: the same twins every time with the same seed")
ok(abs(sc1["model_stats"]["final_value_usd"] - ra["final"]["value_usd"]) < 1e-9 and sc1["model_stats"]["trade_wakes"] == sum(1 for x in ra["steps"] if x["trades"]),
   "score_weights.py replays the model's answers through the same book function and gets the recorded value")
def wcount(series):
    c = {}
    for t in series:
        c[json.dumps(W.norm(t) if t else {}, sort_keys=True)] = c.get(json.dumps(W.norm(t) if t else {}, sort_keys=True), 0) + 1
    return c
def twin_held(sid, draws):
    """For each shuffle_runs draw, the targets the book held wake by wake (as recorded by the same book function)."""
    m = json.loads((S.runs_dir() / sid / "session.json").read_text()); rr = json.loads((S.runs_dir() / sid / "result.json").read_text())
    tb = W.price_table(WT, m); rs = SW.runs_of([x["target"] for x in rr["steps"]])
    return [x["target"] for x in rr["steps"]], rs, [[r["target"] for r in W.run_answers(m, tb, SW.shuffle_runs_series(rs, rr["config"]["tm_weights_twin_seed"], sid, i), rr["config"])[1]] for i in range(draws)]
for sid in ("w_twice_a", "w_long"):
    mt, rs_, held = twin_held(sid, 30)
    ok(all(wcount(h) == wcount(mt) for h in held) and all(len(h) == len(mt) for h in held),
       f"shuffle_runs ({sid}): every draw holds each target for the same total number of wakes as the model")
mt, rs_, held = twin_held("w_twice_a", 30)
ok(len(rs_) > 1 and sc1["twins"]["shuffle_runs"]["runs"] == len(rs_) and all(len(SW.runs_of(h)) <= len(rs_) for h in held) and any(h != mt for h in held),
   "shuffle_runs: the same number of changes or fewer, at different times")
ok(SW.distinct_orders([({"A": 1}, 2), ({"B": 1}, 1), ({"A": 1}, 2)]) == 3 and SW.distinct_orders([({"A": 1}, 2), ({"A": 1}, 1)]) == 2,
   "shuffle_runs: the count of distinct orders treats runs with the same target and length as one")
pubj = json.loads(json.dumps(SW.public(sc1)))
ok(set(pubj["twins"]) == {"shuffle", "shuffle_decisions", "shuffle_runs", "hold_BTC/USD", "hold_equal_weight"} and not any(k.startswith("_") for v in pubj["twins"].values() for k in v),
   "the json output names the sets shuffle, shuffle_decisions, shuffle_runs and hold_*, without the per-draw lists")
sm = SW.sum_sessions(["w_twice_a", "w_long"], tape=WT, draws=30); scl = SW.score("w_long", tape=WT, draws=30)
xs = [a_ + b_ for a_, b_ in zip(sc1["twins"]["shuffle_runs"]["_draw_gains_pct"], scl["twins"]["shuffle_runs"]["_draw_gains_pct"])]
ok(abs(sm["model_gain_pct_sum"] - (sc1["model_stats"]["final_gain_pct"] + scl["model_stats"]["final_gain_pct"])) < 1e-9 and sm["sets"]["shuffle_runs"]["n"] == 30
   and abs(sm["sets"]["shuffle_runs"]["low"] - min(xs)) < 1e-9 and sm["sets"]["shuffle_runs"]["model_percentile"] == SW.pct_below(sm["model_gain_pct_sum"], xs),
   "--sum: the model's gains added up, each twin set's gains added draw by draw, and the percentile of the summed model gain")
ok(sm["sets"]["shuffle_runs"].get("note") is None and abs(sm["sets"]["hold_BTC/USD"]["gain_pct_sum"] - sc1["twins"]["hold_BTC/USD"]["stats"]["final_gain_pct"] - scl["twins"]["hold_BTC/USD"]["stats"]["final_gain_pct"]) < 1e-9,
   "--sum: a month with no timing still adds to the sum, and the holds are summed too")
dst_db = sqlite3.connect(TMP + "/wtape_bad.sqlite"); src_db = sqlite3.connect(TMP + "/wtape.sqlite"); src_db.backup(dst_db); src_db.close()
dst_db.execute("UPDATE bars SET o=o*2 WHERE symbol='ETH/USD' AND tf='1Min'"); dst_db.commit(); dst_db.close()
try:
    SW.score("w_twice_a", tape=Tape(TMP + "/wtape_bad.sqlite"), draws=5); caught = False
except AssertionError:
    caught = True
ok(caught, "score_weights.py stops when the tape no longer gives the prices the session recorded")

# stocks: answers outside regular hours fill at the next regular open; weekly wakes
s = wmk("w_stk", syms=("AAA", "BBB", "SPY"), start="2026-09-01", end="2026-09-02", market="stocks", rules=[dict(every="session_day", ny_times=[9.0])])
ok(s.meta["wakes"] == ["2026-09-01T13:00:00Z", "2026-09-02T13:00:00Z"], "stock wake rules may name times outside regular hours")
r = go(s, ans({"AAA": 0.5}, "before the open"))
ok(r["trades"][0]["fill_utc"] == "2026-09-01T13:30:00Z" and abs(r["trades"][0]["open"] - 10.03) < 1e-9 and abs(r["trades"][0]["price"] - 10.03 * (1 + HS_S)) < 1e-9 and r["trades"][0]["fee_usd"] == 0.0,
   "a stock answer before the open fills at the regular open (not in extended hours), plus tm_stock_half_spread_bps, no fee")
r = go(s, ans({}, "all cash"))
ok(s.done() and [t["side"] for t in r["trades"]] == ["sell"] and not s.prog["book"]["qty"], "an empty weights answer sells everything to cash")
s = wmk("w_stk2", syms=("AAA", "BBB", "SPY"), start="2026-09-01", end="2026-09-03", market="stocks", rules=[dict(every="session_day", ny_times=[17.0])])
ok(s.meta["wakes"] == ["2026-09-01T21:00:00Z", "2026-09-02T21:00:00Z"], "no wake after the last close of the window")
r = go(s, ans({"BBB": 0.25}, "after the close"))
ok(r["trades"][0]["fill_utc"] == "2026-09-02T13:30:00Z" and abs(r["trades"][0]["open"] - 21.03) < 1e-9, "a stock answer after the close fills at the next day's regular open")
s = wmk("w_stk3", syms=("AAA", "BBB", "SPY"), start="2026-09-01", end="2026-09-02", market="stocks", rules=[dict(every="session_day", ny_times=[9.0, 17.0])])
go(s, ans(None)); r = go(s, ans({"BBB": 0.25}, "after the close, next wake before the open"))
ok(not r["trades"] and r["skipped"][0]["why"].startswith("no recorded minute") and s.prog["book"]["target"] == {"BBB": 0.25},
   "a stock answer whose next wake comes before the next open does not fill there")
r = go(s, ans(None, "keep"))
ok([t["symbol"] for t in r["trades"]] == ["BBB"] and r["trades"][0]["fill_utc"] == "2026-09-02T13:30:00Z", "the unfilled move is tried again at the next wake, even with no change")
s = wmk("w_stk_week", syms=("AAA", "BBB"), start="2026-09-01", end="2026-09-11", market="stocks", wake_kind="weekly", basket_size=1)
ok(s.meta["benchmark"] == "SPY" and not s.submit(ans({"AAA": 0.5, "BBB": 0.5}))["ok"] and not s.submit(ans({"AAA": 0.5}))["ok"] and s.prog["k"] == 0,
   "a session with a basket size refuses answers that do not name exactly that many symbols in equal shares")
r = go(s, dict(ans({"AAA": 1.0}, "weekly"), driver="price", reasons={"AAA": "added: steady"}))
ok(s.meta["wakes"][0] == "2026-09-04T19:30:00Z" and r["trades"][0]["fill_utc"] == "2026-09-04T19:30:00Z", "the weekly Friday 15:30 decision fills at that minute")
ok(not s.submit(dict(ans(None), driver="a hunch"))["ok"], "a driver outside the list is refused")
go(s, dict(ans({"BBB": 1.0}, "swap"), driver="news")); scs = SW.score("w_stk_week", tape=WT, draws=20)
ok(s.prog["steps"][0]["driver"] == "price" and s.prog["steps"][0]["reasons"] == {"AAA": "added: steady"}, "the driver and the reasons are recorded with the step")
ok("random_basket" in scs["twins"] and scs["twins"]["random_basket"]["final_gain_pct"]["n"] == 20 and "hold_SPY" in scs["twins"] and "hold_BTC/USD" not in scs["twins"],
   "stock sessions get a random basket twin set and a SPY hold, even when SPY is not on the allowed list")
mt, rs_, held = twin_held("w_stk_week", 30)
ok(len(rs_) == 2 and all(wcount(h) == wcount(mt) for h in held), "shuffle_runs on stocks: whole baskets, each held for the same number of weeks as the model")

# the server serves weights sessions on the same addresses
SV._tape = WT; SV._sessions.clear(); srv = SV.serve(0); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
wmk("w_http")
code, r = call("/pick?session=w_http", ans({"BTC/USD": 0.5})); ok(code == 409, "a weights answer before /next is refused, as in pick sessions")
code, pk = call("/next?session=w_http"); ok(code == 200 and pk["kind"] == "weights" and pk["step"] == 1 and pk["allowed"] == ["BTC/USD", "ETH/USD"], "GET /next gives the weights packet")
code, r = call("/pick?session=w_http", ans({"BTC/USD": 2})); ok(code == 400 and not r["ok"], "a bad weights answer answers 400")
code, r = call("/pick?session=w_http", ans({"BTC/USD": 0.5})); ok(code == 200 and r["ok"] and call("/status?session=w_http")[1]["step"] == 2, "POST /pick with weights moves the clock")
code, r = call("/look?session=w_http&what=bars&symbol=BTC/USD&timeframe=1Day&days=5"); ok(code == 200 and r["ok"], "lookups work in a weights session")
srv.shutdown(); srv.server_close(); SV._sessions.clear()
srv = SV.serve(0); port = srv.server_address[1]; threading.Thread(target=srv.serve_forever, daemon=True).start()
ok(call("/status?session=w_http")[1]["step"] == 2 and call("/status?session=w_http")[1]["kind"] == "weights", "a new server carries on the weights session at the same step")
for _ in range(5):
    call("/next?session=w_http"); call("/pick?session=w_http", ans(None))
ok(call("/next?session=w_http")[1]["status"] == "DONE", "after the last wake the server answers DONE")
srv.shutdown(); srv.server_close(); SV._sessions.clear()

n_log = len(Path(os.environ["TM_SESSIONS_LOG"]).read_text().splitlines())
ok(n_log == log0 + len([d for d in p.iterdir() if (d / "session.json").exists()]), "every session made is one line in the sessions log")

shutil.rmtree(TMP, ignore_errors=True)
print(f"{N[0]} checks passed")
