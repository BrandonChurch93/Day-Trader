"""Offline tests for timemachine/tape.py, timemachine/simdata.py, and timemachine/record.py.

No network calls. Proves the as-of rule on every read path (Tape, SimData, and
practice/market.py unchanged), future-mutation invariance, thread safety, and
fixture-tests every recorder command (sessions, daily, universe, halfhours,
minutes, news, crypto, 429 backoff, sip->iex fallback, resume).
"""
import concurrent.futures, datetime as dt, json, sys, tempfile, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "practice"))

from broker import Refused
import market as M
from timemachine.tape import NY, UTC, Tape, to_utc_dt
from timemachine.simdata import SimData
from timemachine import record as R

PASS = FAIL = 0


def ok(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"FAIL: {msg}")


def _iso(s):
    return to_utc_dt(s)


def build_synthetic_tape(db_path):
    """Build a small synthetic tape spanning 2026-07-02 (full), 2026-07-03 (half-day), 2026-07-06 (full)."""
    t = Tape(db_path)

    # Sessions (EDT = UTC-4 in July):
    # 2026-07-02: 09:30-16:00 NY = 13:30-20:00 UTC
    # 2026-07-03: 09:30-13:00 NY = 13:30-17:00 UTC (half-day)
    # 2026-07-06: 09:30-16:00 NY = 13:30-20:00 UTC
    t.add_sessions([
        ("2026-07-02", "2026-07-02T13:30:00Z", "2026-07-02T20:00:00Z"),
        ("2026-07-03", "2026-07-03T13:30:00Z", "2026-07-03T17:00:00Z"),
        ("2026-07-06", "2026-07-06T13:30:00Z", "2026-07-06T20:00:00Z"),
    ])

    t.add_universe("2026-07-02", ["AAPL", "MSFT", "SPY"])
    t.add_universe("2026-07-03", ["AAPL", "MSFT", "SPY"])
    t.add_universe("2026-07-06", ["AAPL", "MSFT", "SPY"])

    bars = [
        # 1Day stock bars (timestamped 04:00:00Z = midnight EDT, matching Alpaca convention)
        ("AAPL", "1Day", "2026-07-02T04:00:00Z", 100.0, 102.0, 99.0, 101.0, 500000),
        ("AAPL", "1Day", "2026-07-03T04:00:00Z", 101.0, 105.0, 100.5, 104.0, 400000),
        ("AAPL", "1Day", "2026-07-06T04:00:00Z", 104.0, 108.0, 103.0, 107.0, 600000),
        ("MSFT", "1Day", "2026-07-02T04:00:00Z", 200.0, 202.0, 198.0, 200.0, 300000),
        ("MSFT", "1Day", "2026-07-03T04:00:00Z", 199.0, 200.0, 194.0, 195.0, 250000),
        ("SPY", "1Day", "2026-07-02T04:00:00Z", 500.0, 502.0, 499.0, 501.0, 1000000),
        ("SPY", "1Day", "2026-07-03T04:00:00Z", 501.0, 503.0, 500.0, 502.0, 900000),

        # 30Min bars on 2026-07-03 for AAPL and MSFT (MSFT has NO 1Min bars -> tests 30Min fallback!)
        ("AAPL", "30Min", "2026-07-03T13:30:00Z", 101.0, 102.5, 100.5, 102.0, 50000),
        ("AAPL", "30Min", "2026-07-03T14:00:00Z", 102.0, 104.0, 101.5, 103.5, 60000),
        ("MSFT", "30Min", "2026-07-03T13:30:00Z", 199.0, 199.5, 197.0, 198.0, 40000),
        ("MSFT", "30Min", "2026-07-03T14:00:00Z", 198.0, 198.5, 195.0, 196.0, 45000),

        # 1Min bars on 2026-07-03 for AAPL
        ("AAPL", "1Min", "2026-07-03T13:30:00Z", 101.0, 101.5, 100.8, 101.2, 1000),
        ("AAPL", "1Min", "2026-07-03T13:31:00Z", 101.2, 101.8, 101.1, 101.7, 1500),
        ("AAPL", "1Min", "2026-07-03T13:32:00Z", 101.7, 102.0, 101.5, 101.9, 1200),
        ("AAPL", "1Min", "2026-07-03T14:00:00Z", 102.0, 103.0, 101.9, 102.8, 2000),

        # Future-only symbol (only appears on 2026-07-06)
        ("LATE", "1Day", "2026-07-06T04:00:00Z", 50.0, 55.0, 49.0, 54.0, 100000),

        # Crypto bars (BTC/USD, ETH/USD)
        ("BTC/USD", "1Day", "2026-07-02T00:00:00Z", 60000.0, 61000.0, 59500.0, 60500.0, 100.0),
        ("BTC/USD", "1Day", "2026-07-03T00:00:00Z", 60500.0, 62000.0, 60200.0, 61800.0, 120.0),
        ("BTC/USD", "1Min", "2026-07-03T13:30:00Z", 60500.0, 60600.0, 60450.0, 60550.0, 2.5),
        ("BTC/USD", "1Min", "2026-07-03T13:31:00Z", 60550.0, 60700.0, 60520.0, 60680.0, 3.0),
        ("ETH/USD", "1Day", "2026-07-02T00:00:00Z", 3000.0, 3050.0, 2980.0, 3020.0, 500.0),
        ("ETH/USD", "1Min", "2026-07-03T13:30:00Z", 3020.0, 3030.0, 3010.0, 3015.0, 10.0),
    ]
    t.add_bars(bars)

    t.add_news([
        {
            "id": 101,
            "created_at": "2026-07-03T13:00:00Z",
            "updated_at": "2026-07-03T13:00:00Z",
            "headline": "Apple morning note",
            "summary": "Summary 1",
            "source": "wire",
            "url": "https://example.com/1",
            "symbols": ["AAPL"],
        },
        {
            "id": 102,
            "created_at": "2026-07-03T13:31:00Z",
            "updated_at": "2026-07-03T18:00:00Z",  # edited AFTER simulated now!
            "headline": "AAPL & MSFT update",
            "summary": "Summary 2",
            "source": "wire",
            "url": "https://example.com/2",
            "symbols": ["AAPL", "MSFT"],
        },
        {
            "id": 103,
            "created_at": "2026-07-03T13:32:01Z",  # created AFTER 13:32:00Z, before 14:00:00Z
            "updated_at": "2026-07-03T13:32:01Z",
            "headline": "Later morning headline",
            "summary": "Must never appear at 13:32:00Z",
            "source": "wire",
            "url": "https://example.com/3",
            "symbols": ["AAPL"],
        },
        {
            "id": 104,
            "created_at": "2026-07-03T14:00:01Z",  # created AFTER 14:00:00Z
            "updated_at": "2026-07-03T14:00:01Z",
            "headline": "Afternoon headline",
            "summary": "Must never appear at 14:00:00Z",
            "source": "wire",
            "url": "https://example.com/4",
            "symbols": ["AAPL"],
        },
    ])
    return t


def test_tape_as_of(t):
    # 1Min bar finish boundary: bar at 13:31:00 finishes at 13:32:00
    b_before = t.bars("AAPL", "1Min", "2026-07-03T13:30:00Z", "2026-07-03T13:31:59Z")
    ok(len(b_before) == 1 and b_before[0]["t"] == _iso("2026-07-03T13:30:00Z"), "1Min excludes in-progress bar at 13:31:59Z")

    b_exact = t.bars("AAPL", "1Min", "2026-07-03T13:30:00Z", "2026-07-03T13:32:00Z")
    ok(len(b_exact) == 2 and b_exact[-1]["t"] == _iso("2026-07-03T13:31:00Z"), "1Min includes bar exactly at 13:32:00Z")

    # limit keeps newest N
    b_lim = t.bars("AAPL", "1Min", "2026-07-03T13:30:00Z", "2026-07-03T14:05:00Z", limit=2)
    ok(len(b_lim) == 2 and b_lim[0]["t"] == _iso("2026-07-03T13:32:00Z") and b_lim[1]["t"] == _iso("2026-07-03T14:00:00Z"), "bars limit keeps newest N oldest-first")

    # 30Min bar finish boundary: 13:30 bar finishes at 14:00:00
    b30_before = t.bars("MSFT", "30Min", "2026-07-03T13:00:00Z", "2026-07-03T13:59:59Z")
    ok(len(b30_before) == 0, "30Min excludes in-progress bar at 13:59:59Z")
    b30_exact = t.bars("MSFT", "30Min", "2026-07-03T13:00:00Z", "2026-07-03T14:00:00Z")
    ok(len(b30_exact) == 1 and b30_exact[0]["c"] == 198.0, "30Min includes bar at 14:00:00Z")

    # Stock 1Day bar finish boundary on half-day (closes 17:00:00Z = 13:00 NY)
    d_before = t.bars("AAPL", "1Day", "2026-07-01T00:00:00Z", "2026-07-03T16:59:59Z")
    ok(len(d_before) == 1 and d_before[0]["c"] == 101.0, "stock 1Day excludes half-day bar at 16:59:59Z")
    d_exact = t.bars("AAPL", "1Day", "2026-07-01T00:00:00Z", "2026-07-03T17:00:00Z")
    ok(len(d_exact) == 2 and d_exact[-1]["c"] == 104.0, "stock 1Day includes half-day bar at 17:00:00Z")

    # Crypto 1Day bar finish boundary (2026-07-03T00:00:00Z finishes at 2026-07-04T00:00:00Z)
    c_before = t.bars("BTC/USD", "1Day", "2026-07-01T00:00:00Z", "2026-07-03T23:59:59Z")
    ok(len(c_before) == 1 and c_before[0]["c"] == 60500.0, "crypto 1Day excludes in-progress UTC day")
    c_exact = t.bars("BTC/USD", "1Day", "2026-07-01T00:00:00Z", "2026-07-04T00:00:00Z")
    ok(len(c_exact) == 2 and c_exact[-1]["c"] == 61800.0, "crypto 1Day includes finished UTC day at 00:00Z")

    # fill_bar
    fb = t.fill_bar("AAPL", "2026-07-03T13:30:30Z", "2026-07-03T13:32:00Z")
    ok(fb is not None and fb["t"] == _iso("2026-07-03T13:31:00Z"), "fill_bar returns first 1Min bar after_utc <= t and t+60 <= before_utc")
    fb_none = t.fill_bar("AAPL", "2026-07-03T13:30:30Z", "2026-07-03T13:31:59Z")
    ok(fb_none is None, "fill_bar returns None when bar has not finished before before_utc")

    # snapshot: AAPL uses 1Min, MSFT falls back to 30Min at 14:00:00Z, timestamp = bar end
    sn = t.snapshot(["AAPL", "MSFT", "BTC/USD", "LATE"], "2026-07-03T14:00:00Z")
    ok("AAPL" in sn and sn["AAPL"]["price"] == 101.9 and sn["AAPL"]["t"] == _iso("2026-07-03T13:33:00Z"), "snapshot AAPL uses last finished 1Min bar end")
    ok(sn["AAPL"]["prev_close"] == 101.0 and sn["AAPL"]["day_open"] == 101.0 and sn["AAPL"]["day_volume"] == 3700, "snapshot AAPL aggregates only finished 1Min bars")
    ok("MSFT" in sn and sn["MSFT"]["price"] == 198.0 and sn["MSFT"]["t"] == _iso("2026-07-03T14:00:00Z"), "snapshot MSFT falls back to 30Min bar end")
    ok("BTC/USD" in sn and sn["BTC/USD"]["price"] == 60680.0 and sn["BTC/USD"]["t"] == _iso("2026-07-03T13:32:00Z"), "snapshot crypto uses 1Min bar end")
    ok("LATE" not in sn, "snapshot excludes future-only symbol LATE")

    # news: created <= now, edited_later flag
    nw = t.news("2026-07-03T13:32:00Z")
    ok([x["id"] for x in nw] == [102, 101], "news returns newest-first and excludes 103 created at 13:32:01Z")
    ok(nw[0].get("edited_later") is True and "edited_later" not in nw[1], "news sets edited_later only when updated > created")
    nw_sym = t.news("2026-07-03T13:32:00Z", symbols=["MSFT"])
    ok([x["id"] for x in nw_sym] == [102], "news filters by symbol")

    # sessions, is_open, next_open, next_close
    ok(t.is_open("2026-07-03T13:30:00Z") is True, "is_open True at open")
    ok(t.is_open("2026-07-03T17:00:00Z") is False, "is_open False at half-day close")
    ok(t.next_close("2026-07-03T14:00:00Z") == _iso("2026-07-03T17:00:00Z"), "next_close returns half-day close")
    ok(t.next_open("2026-07-03T17:00:00Z") == _iso("2026-07-06T13:30:00Z"), "next_open skips weekend to Monday")

    # movers & most_active as of 14:00:00Z
    mv = t.movers("2026-07-03T14:00:00Z", top=5, market="stocks")
    ok(len(mv["gainers"]) == 1 and mv["gainers"][0]["symbol"] == "AAPL", "movers gainers identifies AAPL")
    ok(len(mv["losers"]) == 1 and mv["losers"][0]["symbol"] == "MSFT", "movers losers identifies MSFT")
    ma = t.most_active("2026-07-03T14:00:00Z", top=5)
    ok(len(ma) >= 2 and ma[0]["symbol"] == "MSFT", "most_active ranks by finished intraday volume")

    # has_minutes / ensure_minutes / has_symbol_as_of
    ok(t.has_minutes("AAPL", "2026-07-03") is True and t.has_minutes("MSFT", "2026-07-03") is False, "has_minutes accurate")
    ok(t.has_symbol_as_of("LATE", "2026-07-03T17:00:00Z") is False, "has_symbol_as_of False before first finished bar")
    ok(t.has_symbol_as_of("LATE", "2026-07-06T20:00:00Z") is True, "has_symbol_as_of True after first finished bar")


def test_simdata_and_market(t):
    now = [_iso("2026-07-03T14:00:00Z")]
    sim = SimData(t, lambda: now[0])

    # practice/market.py functions unchanged!
    px = M.prices(sim, ["AAPL", "MSFT", "BTC/USD"])
    ok(px["AAPL"]["price"] == 101.9 and px["AAPL"]["bid"] == px["AAPL"]["ask"] == 101.9, "market.prices AAPL bid=ask=close")
    ok(_iso(px["AAPL"]["utc"]) <= now[0] and _iso(px["MSFT"]["utc"]) <= now[0] and _iso(px["BTC/USD"]["utc"]) <= now[0], "market.prices timestamps <= now")

    # daily_bars clamped to now (cannot see 2026-07-03 stock bar at 14:00Z)
    db_a = M.daily_bars(sim, "AAPL", "2026-07-01T00:00:00Z")
    db_c = M.daily_bars(sim, "BTC/USD", "2026-07-01T00:00:00Z")
    ok(len(db_a) == 1 and db_a[0]["c"] == 101.0, "market.daily_bars excludes unfinished stock day")
    ok(len(db_c) == 1 and db_c[0]["c"] == 60500.0, "market.daily_bars excludes unfinished crypto day")

    # Direct SimData.get with future end/start clamped!
    clamped = sim.get(M.DATA, "/v2/stocks/bars", {
        "symbols": "AAPL", "timeframe": "1Min",
        "start": "2026-07-03T13:30:00Z", "end": "2026-07-09T00:00:00Z",
    })
    ok(len(clamped["bars"]["AAPL"]) == 3 and clamped["bars"]["AAPL"][-1]["t"] == "2026-07-03T13:32:00Z", "SimData.get clamps future end to now")
    fut_start = sim.get(M.DATA, "/v2/stocks/bars", {
        "symbols": "AAPL", "timeframe": "1Min",
        "start": "2026-07-03T15:00:00Z", "end": "2026-07-09T00:00:00Z",
    })
    ok(fut_start["bars"] == {}, "SimData.get returns empty when start > now")

    # minute_bars
    mb = M.minute_bars(sim, "AAPL", "2026-07-03T13:00:00Z", limit=60)
    ok(len(mb) == 3 and all(_iso(b["t"]) < now[0] for b in mb), "market.minute_bars returns only finished bars")

    # movers & most_active
    mv = M.movers(sim, top=5, market="stocks")
    ok(mv["gainers"][0]["symbol"] == "AAPL" and mv["losers"][0]["symbol"] == "MSFT", "market.movers works on SimData")
    ma = M.most_active(sim, top=5)
    ok(len(ma) >= 2 and ma[0]["symbol"] == "MSFT", "market.most_active works on SimData")

    # news: updated_at clamped so NO timestamp > now!
    nw_raw = sim.get(M.DATA, "/v1beta1/news", {"start": "2026-07-03T00:00:00Z", "end": "2026-07-09T00:00:00Z"})
    ok(len(nw_raw["news"]) == 3 and all(a["id"] != 104 for a in nw_raw["news"]), "SimData news clamps future end and hides 104")
    ok(all(_iso(a["created_at"]) <= now[0] and _iso(a["updated_at"]) <= now[0] for a in nw_raw["news"]), "SimData news never returns any timestamp > now")
    nw_m = M.news(sim, symbols=["AAPL"], limit=10)
    ok(len(nw_m) == 3, "market.news works on SimData")

    # asset: present vs future-only
    a_ok = M.asset(sim, "AAPL")
    ok(a_ok["tradable"] is True and a_ok["fractionable"] is True, "market.asset AAPL tradable & fractionable")
    a_crypto = M.asset(sim, "BTC/USD")
    ok(a_crypto["tradable"] is True and a_crypto["class"] == "crypto", "market.asset BTC/USD works")
    ok(M.asset(sim, "LATE") is None, "market.asset LATE returns None before first finished bar")

    # clock & calendar
    clk = M.market_clock(sim)
    ok(clk["is_open"] is True and clk["next_close_utc"] == "2026-07-03T17:00:00Z", "market.market_clock works on SimData")
    cal = M.calendar(sim, "2026-07-02", "2026-07-06")
    ok(len(cal) == 3 and cal[1]["close_utc"] == "2026-07-03T17:00:00Z", "market.calendar returns half-day close 17:00Z")

    # build_feed end-to-end
    feed = M.build_feed(sim, ["AAPL", "MSFT"], ["BTC/USD"], now[0])
    ok("AAPL" in feed["prices"] and "BTC/USD" in feed["prices"] and len(feed["news"]) == 3, "market.build_feed works unchanged on SimData")


def test_future_mutation_invariance(t):
    """Adding future bars/news/universe/symbols after T0 must never alter ANY read at T0."""
    t0 = _iso("2026-07-03T14:00:00Z")
    sim = SimData(t, lambda: t0)

    def capture():
        return json.dumps({
            "tape_bars_1m": [{**b, "t": b["t"].isoformat()} for b in t.bars("AAPL", "1Min", "2026-07-01T00:00:00Z", t0)],
            "tape_bars_30m": [{**b, "t": b["t"].isoformat()} for b in t.bars("MSFT", "30Min", "2026-07-01T00:00:00Z", t0)],
            "tape_bars_1d": [{**b, "t": b["t"].isoformat()} for b in t.bars("AAPL", "1Day", "2026-07-01T00:00:00Z", t0)],
            "tape_crypto_1d": [{**b, "t": b["t"].isoformat()} for b in t.bars("BTC/USD", "1Day", "2026-07-01T00:00:00Z", t0)],
            "snap": {k: {**v, "t": v["t"].isoformat()} for k, v in t.snapshot(["AAPL", "MSFT", "BTC/USD", "FUTX"], t0).items()},
            "news": [{**n, "created": n["created"].isoformat(), "updated": n["updated"].isoformat()} for n in t.news(t0)],
            "movers": t.movers(t0, top=10, market="stocks"),
            "most_active": t.most_active(t0, top=10),
            "feed": M.build_feed(sim, ["AAPL", "MSFT"], ["BTC/USD"], t0),
        }, sort_keys=True, default=str)

    before = capture()

    # Mutate tape with dramatic future events after t0
    t.add_bars([
        ("AAPL", "1Min", "2026-07-03T14:01:00Z", 999.0, 999.0, 999.0, 999.0, 9999999),
        ("MSFT", "30Min", "2026-07-03T14:30:00Z", 1.0, 1.0, 1.0, 1.0, 9999999),
        ("AAPL", "1Day", "2026-07-07T04:00:00Z", 500.0, 500.0, 500.0, 500.0, 9999999),
        ("BTC/USD", "1Min", "2026-07-03T14:00:00Z", 100000.0, 100000.0, 100000.0, 100000.0, 9999.0),
        ("FUTX", "1Min", "2026-07-03T14:00:00Z", 10.0, 10.0, 10.0, 10.0, 50000),
    ])
    t.add_news([{
        "id": 999,
        "created_at": "2026-07-03T14:00:01Z",
        "updated_at": "2026-07-03T14:00:01Z",
        "headline": "Breaking future news",
        "summary": "Leak test",
        "source": "wire",
        "url": "https://example.com/fut",
        "symbols": ["AAPL", "MSFT"],
    }])
    t.add_universe("2026-07-07", ["FUTX"])

    after = capture()
    ok(before == after, "future-mutation invariance: adding future rows never changes any read at T0")


def test_thread_safety(t):
    t0 = _iso("2026-07-03T14:00:00Z")
    errors = []

    def worker(i):
        try:
            for _ in range(15):
                t.bars("AAPL", "1Min", "2026-07-03T13:30:00Z", t0)
                t.snapshot(["AAPL", "BTC/USD"], t0)
                t.news(t0)
                t.add_bars([(f"THR{i}", "1Min", "2026-07-06T14:00:00Z", 10.0, 11.0, 9.0, 10.5, 100)])
        except Exception as e:
            errors.append(e)

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(worker, range(6)))
    ok(len(errors) == 0, f"thread safety across 6 concurrent workers (errors={errors})")


def test_recorder_fixtures():
    cfg = R.config()
    ok(all(k in cfg for k in R.TM_KEYS), "record.config() loads all 6 tm_ keys from config/thresholds.yaml")

    # Nasdaq symbol parser
    sample_nasdaq = (
        "Nasdaq Traded|Symbol|Security Name|Listing Exchange|Market Category|ETF|Round Lot Size|Test Issue|Financial Status|CQS Symbol|NASDAQ Symbol|NextShares\n"
        "Y|AAPL|Apple Inc.|Q|Q|N|100|N|N||AAPL|N\n"
        "Y|ZVZZT|Test Stock|Q|Q|N|100|Y|N||ZVZZT|N\n"
        "Y|BRK.B|Berkshire|N| |N|100|N||BRK.B|BRK.B|N\n"
        "File Creation Time: 1125202612:00|||||||\n"
    )
    syms = R.parse_nasdaq_symbols(sample_nasdaq)
    ok(syms == ["AAPL", "BRK.B"], f"parse_nasdaq_symbols filters test issues & footer (got {syms})")

    # 429 backoff + Retry-After + pacing
    sleeps = []
    calls = [0]

    def flaky_get(url):
        calls[0] += 1
        if calls[0] == 1:
            raise R.HttpError(429, "rate limit", {"Retry-After": "1.5"})
        if calls[0] == 2:
            raise R.HttpError(429, "rate limit", {})
        return 200, json.dumps({"ok": True}), {}

    cli = R.Client(max_rpm=120, http_get=flaky_get, sleep_fn=sleeps.append, now_fn=lambda: 100.0)
    res = cli.get_json("https://example.com", "/test")
    ok(res == {"ok": True} and calls[0] == 3, "Client retries on 429 and succeeds")
    ok(1.5 in sleeps and 4.0 in sleeps, f"Client honours Retry-After then exponential backoff (sleeps={sleeps})")

    # Full recorder command suite on fixture HTTP server
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "rec.sqlite"
        t = Tape(db)
        req_log = []

        def fake_http(url):
            req_log.append(url)
            u = urllib.parse.urlparse(url)
            q = urllib.parse.parse_qs(u.query)
            if u.path.endswith("nasdaqtraded.txt"):
                return 200, sample_nasdaq, {}
            if u.path == "/v2/stocks/bars":
                feed = q.get("feed", ["sip"])[0]
                if feed == "sip":
                    raise R.HttpError(403, "subscription does not permit querying recent SIP data")
                tf = q["timeframe"][0]
                req_syms = q["symbols"][0].split(",")
                if tf == "1Min" and req_syms == ["SPY"]:
                    # Full day 2026-07-02 (09:30-15:59 NY) + half-day 2026-07-03 (09:30-12:59 NY)
                    return 200, json.dumps({"bars": {"SPY": [
                        {"t": "2026-07-02T13:30:00Z", "o": 500, "h": 501, "l": 499, "c": 500.5, "v": 1000},
                        {"t": "2026-07-02T19:59:00Z", "o": 501, "h": 502, "l": 500, "c": 501.5, "v": 1000},
                        {"t": "2026-07-03T13:30:00Z", "o": 502, "h": 503, "l": 501, "c": 502.5, "v": 1000},
                        {"t": "2026-07-03T16:59:00Z", "o": 502.5, "h": 503, "l": 502, "c": 502.8, "v": 1000},
                    ]}, "next_page_token": None}), {}
                if tf == "1Day":
                    # AAPL qualifies on both days; BRK.B only crosses min_price on 2026-07-02 (so NOT in 2026-07-02 universe, YES in 2026-07-03!)
                    return 200, json.dumps({"bars": {
                        "AAPL": [
                            {"t": "2026-07-01T04:00:00Z", "o": 100, "h": 102, "l": 99, "c": 100, "v": 200000},
                            {"t": "2026-07-02T04:00:00Z", "o": 100, "h": 103, "l": 99, "c": 102, "v": 200000},
                        ],
                        "BRK.B": [
                            {"t": "2026-07-01T04:00:00Z", "o": 3, "h": 4, "l": 3, "c": 4, "v": 5000000},   # price < 5!
                            {"t": "2026-07-02T04:00:00Z", "o": 10, "h": 12, "l": 9, "c": 10, "v": 5000000},  # price >= 5 on 07-02!
                        ],
                    }, "next_page_token": None}), {}
                if tf == "30Min":
                    return 200, json.dumps({"bars": {
                        s: [{"t": "2026-07-02T13:30:00Z", "o": 100, "h": 101, "l": 99, "c": 100.5, "v": 10000}]
                        for s in req_syms
                    }, "next_page_token": None}), {}
                if tf == "1Min":
                    return 200, json.dumps({"bars": {
                        s: [{"t": "2026-07-02T13:30:00Z", "o": 100, "h": 101, "l": 99, "c": 100.2, "v": 500}]
                        for s in req_syms
                    }, "next_page_token": None}), {}
            if u.path == "/v1beta1/news":
                ok(q.get("include_content") == ["false"], "record_news passes include_content=false")
                tok = q.get("page_token", [None])[0]
                if not tok:
                    return 200, json.dumps({"news": [{
                        "id": 201, "created_at": "2026-07-02T14:00:00Z", "updated_at": "2026-07-02T14:00:00Z",
                        "headline": "H1", "summary": "S1", "source": "w", "url": "u1", "symbols": ["AAPL"],
                    }], "next_page_token": "p2"}), {}
                return 200, json.dumps({"news": [{
                    "id": 202, "created_at": "2026-07-02T15:00:00Z", "updated_at": "2026-07-02T15:00:00Z",
                    "headline": "H2", "summary": "S2", "source": "w", "url": "u2", "symbols": ["AAPL"],
                }], "next_page_token": None}), {}
            if u.path == "/v1beta3/crypto/us/bars":
                tf = q["timeframe"][0]
                return 200, json.dumps({"bars": {
                    "BTC/USD": [{"t": "2026-07-02T00:00:00Z", "o": 60000, "h": 61000, "l": 59000, "c": 60500, "v": 10}]
                }, "next_page_token": None}), {}
            raise R.HttpError(404, f"unexpected url {url}")

        cli2 = R.Client(max_rpm=150, http_get=fake_http, sleep_fn=lambda _: None, now_fn=lambda: 0.0)

        # 1. sessions (triggers sip->iex fallback & records meta)
        n_sess = R.record_sessions(t, cli2, "2026-07-02", "2026-07-03")
        ok(n_sess == 2 and t.get_meta("stock_feed") == "iex", "record_sessions falls back sip->iex and stores 2 sessions")
        s03 = t.session("2026-07-03")
        ok(s03 == (_iso("2026-07-03T13:30:00Z"), _iso("2026-07-03T17:00:00Z")), "record_sessions detects 13:00 NY half-day close")
        before_resume = cli2.requests_made
        R.record_sessions(t, cli2, "2026-07-02", "2026-07-03")
        ok(cli2.requests_made == before_resume, "record_sessions resumes cleanly without re-fetching completed chunks")

        # 2. daily
        n_daily = R.record_daily(t, cli2, "2026-07-02", "2026-07-03", cfg)
        ok(n_daily == 4, f"record_daily stores 4 bars (got {n_daily})")

        # 3. universe (NO LOOK-AHEAD!)
        R.record_universe(t, "2026-07-02", "2026-07-03", cfg)
        ok(t.universe("2026-07-02") == ["AAPL"], f"universe 07-02 excludes BRK.B (strictly prior close < 5): {t.universe('2026-07-02')}")
        ok(t.universe("2026-07-03") == ["AAPL", "BRK.B"], f"universe 07-03 includes BRK.B once prior day >= 5: {t.universe('2026-07-03')}")

        # 4. halfhours & minutes
        n_hh = R.record_halfhours(t, cli2, "2026-07-02", "2026-07-03", cfg)
        ok(n_hh == 2, f"record_halfhours stores 30Min bars for universe (got {n_hh})")
        n_min = R.record_minutes(t, cli2, ["AAPL"], "2026-07-02", "2026-07-03", cfg)
        ok(n_min == 1 and t.has_minutes("AAPL", "2026-07-02"), "record_minutes stores 1Min bars")

        # 5. news (paginated)
        n_nw = R.record_news(t, cli2, "2026-07-02", "2026-07-03")
        ok(n_nw == 2 and len(t.news("2026-07-02T16:00:00Z")) == 2, "record_news paginates and stores articles")

        # 6. crypto (keyless) + --tf filter
        n_cr = R.record_crypto(t, cli2, ["BTC/USD"], "2026-07-02", "2026-07-02", tf="1Day")
        ok(n_cr == 1, f"record_crypto tf=1Day stores only 1Day bar (got {n_cr})")
        n_cr2 = R.record_crypto(t, cli2, ["BTC/USD"], "2026-07-02", "2026-07-02", tf="1Min")
        ok(n_cr2 == 1, f"record_crypto tf=1Min stores only 1Min bar (got {n_cr2})")

        # 7. crypto-news (keyless WordPress REST)
        wp_pages = [
            [
                {
                    "id": 1,
                    "date_gmt": "2026-07-02T14:00:00",
                    "modified_gmt": "2026-07-02T12:00:00",  # scheduled before publish -> NOT edited_later
                    "link": "https://cryptoslate.com/btc-sol-rally/",
                    "title": {"rendered": "Bitcoin &amp; Solana Lead Market"},
                    "excerpt": {"rendered": "<p>BTC and SOL rose in early trading.</p>"},
                },
                {
                    "id": 2,
                    "date_gmt": "2026-07-02T14:30:00",
                    "modified_gmt": "2026-07-02T18:00:00",  # edited AFTER publish -> edited_later=True
                    "link": "https://cryptoslate.com/link-update/",
                    "title": {"rendered": "Chainlink Expands Oracle Network"},
                    "excerpt": {"rendered": "<p>LINK adoption grows across DeFi.</p>"},
                },
                {
                    "id": 3,
                    "date_gmt": "2026-07-02T14:45:00",
                    "modified_gmt": "2026-07-02T14:45:00",
                    "link": "https://cryptoslate.com/off-topic/",
                    "title": {"rendered": "Follow this link for weather"},
                    "excerpt": {"rendered": "<p>Sunny skies ahead.</p>"},  # lowercase 'link', no crypto terms -> skipped!
                },
            ],
            [
                {
                    "id": 4,
                    "date_gmt": "2026-07-02T15:00:00",
                    "modified_gmt": "2026-07-02T15:00:00",
                    "link": "https://cryptoslate.com/sec-etf-news/",
                    "title": {"rendered": "SEC Reviews New Crypto ETF"},
                    "excerpt": {"rendered": "<p>Regulators examine digital asset filings.</p>"},
                },
            ],
        ]

        def fake_wp(url):
            u = urllib.parse.urlparse(url)
            q = urllib.parse.parse_qs(u.query)
            pg = int(q.get("page", ["1"])[0])
            return 200, json.dumps(wp_pages[pg - 1]), {"X-WP-TotalPages": str(len(wp_pages))}

        cli_wp = R.Client(max_rpm=30, http_get=fake_wp, sleep_fn=lambda _: None, now_fn=lambda: 0.0)
        n_cn = R.record_crypto_news(t, cli_wp, "2026-07-02", "2026-07-02", cfg, sources=["cryptoslate"])
        ok(n_cn == 3, f"record_crypto_news stores 3 relevant articles and skips off-topic (got {n_cn})")
        # Resume skips completed chunk
        reqs_before = cli_wp.requests_made
        R.record_crypto_news(t, cli_wp, "2026-07-02", "2026-07-02", cfg, sources=["cryptoslate"])
        ok(cli_wp.requests_made == reqs_before, "record_crypto_news resumes without re-fetching completed chunk")

        # Strict as-of check at 14:40Z: sees #1 (BTC/USD, SOL/USD) and #2 (LINK/USD, edited_later=True), NOT #4 (15:00Z)!
        nw_asof = t.news("2026-07-02T14:40:00Z", symbols=["BTC/USD", "LINK/USD", "CRYPTO"])
        cs_items = [a for a in nw_asof if a["source"] == "cryptoslate"]
        ok(len(cs_items) == 2, f"keyless crypto-news as-of 14:40Z hides 15:00Z article (got {len(cs_items)})")
        by_url = {a["url"]: a for a in cs_items}
        ok("edited_later" not in by_url["https://cryptoslate.com/btc-sol-rally/"], "scheduled post (modified <= date) not marked edited_later")
        ok(by_url["https://cryptoslate.com/btc-sol-rally/"]["headline"] == "Bitcoin & Solana Lead Market", "HTML entities unescaped in headline")
        ok(by_url["https://cryptoslate.com/link-update/"].get("edited_later") is True, "post modified after publish marked edited_later")
        # SimData clamps updated_at <= now on edited keyless news; market.news strips '/' -> 'LINKUSD' and still matches!
        sim_cn = SimData(t, lambda: _iso("2026-07-02T14:40:00Z"))
        raw_cn = sim_cn.get(M.DATA, "/v1beta1/news", {"symbols": "LINK/USD"})
        ok(len(raw_cn["news"]) == 1 and raw_cn["news"][0]["updated_at"] == "2026-07-02T14:30:00Z", "SimData clamps future modified_gmt to created_at")
        m_cn = M.news(sim_cn, symbols=["LINK/USD"], limit=10)
        ok(len(m_cn) == 1 and m_cn[0]["source"] == "cryptoslate", "market.news slashless crypto ticker matches stored LINK/USD")
        t.close()


def main():
    with tempfile.TemporaryDirectory() as tmp:
        t = build_synthetic_tape(Path(tmp) / "test.sqlite")
        try:
            test_tape_as_of(t)
            test_simdata_and_market(t)
            test_future_mutation_invariance(t)
            test_thread_safety(t)
        finally:
            t.close()
    test_recorder_fixtures()
    print(f"test_tape: {PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
