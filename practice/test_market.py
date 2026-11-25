"""Checks for practice/market.py with a fake GET transport and no network.
Run: python3 practice/test_market.py
"""
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import broker as B
import market as M

N = [0]


def ok(cond, what):
    N[0] += 1
    if not cond:
        print("FAIL:", what)
        sys.exit(1)


def matches_reads(base, path):
    return any(base == b and re.fullmatch(pat, path) for b, pat in M.READS)


class FakeGet:
    """Fake get(base, path, params) that checks every request against market.READS."""

    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def __call__(self, base, path, params=None):
        self.calls.append((base, path, dict(params) if params else None))
        ok(matches_reads(base, path), f"request matches READS: {base}{path}")
        return self.handler(base, path, params or {})


# ---- static safety checks on market.py
src = (Path(__file__).parent / "market.py").read_text()
ok("import urllib" not in src and "from urllib" not in src, "market.py does not import urllib")
ok("api.alpaca.markets" not in src.replace("paper-api.alpaca.markets", ""), "real-money host is absent from market.py")
ok(all(w not in src for w in ("openai", "anthropic", "perplexity", "requests.")), "no model or third-party HTTP client")

# ---- timestamp parsing: nanoseconds, Z, numeric offsets
ok(M._iso_utc("2022-08-17T10:18:27.052763263Z") == "2022-08-17T10:18:27Z", "RFC-3339 9-digit nanoseconds with Z")
ok(M._iso_utc("2022-08-17T10:18:23.84717767Z") == "2022-08-17T10:18:23Z", "RFC-3339 8-digit fractional seconds with Z")
ok(M._iso_utc("2025-06-24T14:15:22-04:00") == "2025-06-24T18:15:22Z", "RFC-3339 negative numeric offset to UTC")
ok(M._iso_utc("2025-06-24T14:15:22.123456789+02:00") == "2025-06-24T12:15:22Z", "RFC-3339 nanos with positive offset")
ok(M._iso_utc("2025-06-24T14:15:22-0400") == "2025-06-24T18:15:22Z", "RFC-3339 offset without colon")
ok(M._iso_utc("not-a-timestamp") is None, "invalid timestamp returns None")

# ---- documented snapshot examples: quote mid vs trade fallback, wide spread, crypto vs stock routing, missing & bad prices
STOCK_SNAP_DOC = {
    "AAPL": {
        "dailyBar": {"c": 173.03, "h": 173.71, "l": 171.6618, "n": 515139, "o": 172.62, "t": "2022-08-16T04:00:00Z", "v": 56457696, "vw": 172.743391},
        "latestQuote": {"ap": 172.7, "as": 5, "ax": "Q", "bp": 172.6, "bs": 2, "bx": "Q", "c": ["R"], "t": "2022-08-17T10:18:27.052763263Z", "z": "C"},
        "latestTrade": {"c": ["@", "T"], "i": 1011, "p": 172.61, "s": 160, "t": "2022-08-17T10:18:24.114694956Z", "x": "Q", "z": "C"},
        "minuteBar": {"c": 172.69, "h": 172.69, "l": 172.69, "n": 3, "o": 172.69, "t": "2022-08-17T10:16:00Z", "v": 106, "vw": 172.688113},
        "prevDailyBar": {"c": 173.19, "h": 173.39, "l": 171.345, "n": 501626, "o": 171.5, "t": "2022-08-15T04:00:00Z", "v": 54091719, "vw": 172.625371},
    },
    "WIDE": {
        "dailyBar": {"c": 100.0, "h": 105.0, "l": 95.0, "n": 10, "o": 98.0, "t": "2022-08-16T04:00:00Z", "v": 500, "vw": 100.0},
        "latestQuote": {"ap": 105.0, "as": 1, "ax": "V", "bp": 95.0, "bs": 1, "bx": "V", "c": ["R"], "t": "2022-08-17T10:18:27Z", "z": "C"},
        "latestTrade": {"c": ["@"], "i": 2, "p": 101.25, "s": 10, "t": "2022-08-17T10:15:00.500000000Z", "x": "V", "z": "C"},
        "prevDailyBar": {"c": 99.0, "h": 100.0, "l": 98.0, "n": 5, "o": 99.0, "t": "2022-08-15T04:00:00Z", "v": 400, "vw": 99.0},
    },
    "NOASK": {
        "latestQuote": {"ap": 0, "as": 0, "ax": "V", "bp": 50.0, "bs": 1, "bx": "V", "c": ["R"], "t": "2022-08-17T10:18:27Z", "z": "C"},
        "latestTrade": {"c": ["@"], "i": 3, "p": 50.5, "s": 10, "t": "2022-08-17T10:12:00Z", "x": "V", "z": "C"},
    },
    "BADPX": {
        "latestQuote": {"ap": float("nan"), "as": 1, "bp": -5.0, "bs": 1, "t": "2022-08-17T10:18:27Z"},
        "latestTrade": {"p": 0, "s": 1, "t": "2022-08-17T10:18:27Z"},
    },
}

CRYPTO_SNAP_DOC = {
    "snapshots": {
        "BTC/USD": {
            "dailyBar": {"c": 31744, "h": 31807, "l": 31416, "n": 438, "o": 31660, "t": "2022-05-31T05:00:00Z", "v": 67.3518, "vw": 31582.7034526175},
            "latestQuote": {"ap": 31742, "as": 0.395, "bp": 31741, "bs": 0.395, "t": "2022-05-31T11:55:58.507608832Z"},
            "latestTrade": {"i": 32396097, "p": 31744, "s": 0.0543, "t": "2022-05-31T11:53:45.027481Z", "tks": "B"},
            "minuteBar": {"c": 31744, "h": 31744, "l": 31744, "n": 2, "o": 31744, "t": "2022-05-31T11:53:00Z", "v": 0.0886, "vw": 31744},
            "prevDailyBar": {"c": 31649, "h": 32251, "l": 30251, "n": 8221, "o": 30310, "t": "2022-05-30T05:00:00Z", "v": 1856.4065, "vw": 30877.2751897281},
        }
    }
}


def snap_handler(base, path, params):
    if base == M.DATA and path == "/v2/stocks/snapshots":
        return STOCK_SNAP_DOC
    if base == M.DATA and path == "/v1beta3/crypto/us/snapshots":
        return CRYPTO_SNAP_DOC
    raise AssertionError(f"unexpected {base}{path}")


fg = FakeGet(snap_handler)
px = M.prices(fg, ["AAPL", "WIDE", "NOASK", "BADPX", "MISSING", "BTC/USD"])
ok(abs(px["AAPL"]["price"] - 172.65) < 1e-9, "tight quote uses mid price (172.6+172.7)/2")
ok(px["AAPL"]["utc"] == "2022-08-17T10:18:27Z" and px["AAPL"]["source"] == "iex", "AAPL uses quote utc and iex source")
ok(px["AAPL"]["prev_close"] == 173.19 and px["AAPL"]["day_open"] == 172.62 and px["AAPL"]["day_volume"] == 56457696, "AAPL daily fields populated")
ok(px["WIDE"]["price"] == 101.25 and px["WIDE"]["utc"] == "2022-08-17T10:15:00Z", "wide spread (10%) falls back to latestTrade")
ok(px["NOASK"]["price"] == 50.5 and px["NOASK"]["ask"] is None and px["NOASK"]["bid"] == 50.0, "zero ask rejected and falls back to trade")
ok("BADPX" not in px and "MISSING" not in px, "non-positive/NaN prices and missing symbols are omitted")
ok(abs(px["BTC/USD"]["price"] - 31741.5) < 1e-9 and px["BTC/USD"]["source"] == "crypto-us", "crypto routes to crypto snapshots with crypto-us source")
ok(px["BTC/USD"]["utc"] == "2022-05-31T11:55:58Z", "crypto quote nanosecond timestamp converted to UTC")

# ---- stock snapshots 4xx on iex falls back to delayed_sip, and batching splits >100 symbols
def snap_fallback_handler(base, path, params):
    if params.get("feed") == "iex":
        raise B.Refused(403, "forbidden iex")
    if params.get("feed") == "delayed_sip":
        return {s: STOCK_SNAP_DOC["AAPL"] for s in params["symbols"].split(",")}
    raise AssertionError("unexpected feed")


fg_fb = FakeGet(snap_fallback_handler)
many = [f"SYM{i}" for i in range(105)]
px_fb = M.prices(fg_fb, many)
ok(len(px_fb) == 105 and px_fb["SYM0"]["source"] == "delayed_sip", "iex 403 falls back to delayed_sip across batches")
ok(len([c for c in fg_fb.calls if c[2]["feed"] == "delayed_sip"]) == 2, "105 stock symbols batched into 2 calls")

# ---- bars: sip 403 -> iex fallback, adjustment=all on daily, paging on minute & daily, crypto routing
def bars_handler(base, path, params):
    if path == "/v2/stocks/bars":
        if params.get("feed") == "sip":
            raise B.Refused(403, "subscription does not permit querying recent SIP data")
        if params.get("timeframe") == "1Day":
            ok(params.get("adjustment") == "all", "daily stock bars request adjustment=all")
            if not params.get("page_token"):
                return {
                    "bars": {"AAPL": [{"c": 178.21, "h": 178.26, "l": 178.21, "n": 65, "o": 178.26, "t": "2022-01-03T09:00:00Z", "v": 1118, "vw": 178.23}]},
                    "next_page_token": "tok2",
                }
            return {
                "bars": {"AAPL": [{"c": 179.0, "h": 180.0, "l": 177.5, "n": 70, "o": 178.5, "t": "2022-01-04T09:00:00Z", "v": 2000, "vw": 179.1}]},
                "next_page_token": None,
            }
        # 1Min bars with paging and limit cap
        if not params.get("page_token"):
            return {
                "bars": {"AAPL": [
                    {"c": 170.0, "h": 171.0, "l": 169.0, "o": 170.0, "t": "2022-01-03T14:30:00Z", "v": 100},
                    {"c": 170.5, "h": 171.0, "l": 170.0, "o": 170.0, "t": "2022-01-03T14:31:00Z", "v": 120},
                ]},
                "next_page_token": "m2",
            }
        return {
            "bars": {"AAPL": [
                {"c": 171.0, "h": 171.5, "l": 170.5, "o": 170.5, "t": "2022-01-03T14:32:00Z", "v": 150},
                {"c": 171.5, "h": 172.0, "l": 171.0, "o": 171.0, "t": "2022-01-03T14:33:00Z", "v": 160},
            ]},
            "next_page_token": None,
        }
    if path == "/v1beta3/crypto/us/bars":
        return {
            "bars": {"BTC/USD": [{"c": 29003, "h": 29003, "l": 28999, "n": 4, "o": 28999, "t": "2022-05-27T10:18:00Z", "v": 0.0, "vw": 29001}]},
            "next_page_token": None,
        }
    raise AssertionError(f"unexpected {path}")


fg_b = FakeGet(bars_handler)
db = M.daily_bars(fg_b, "AAPL", "2022-01-03T00:00:00Z")
ok(len(db) == 2 and db[0]["t"] < db[1]["t"] and db[1]["c"] == 179.0, "daily_bars falls back sip->iex and follows next_page_token")
mb = M.minute_bars(fg_b, "AAPL", "2022-01-03T14:30:00Z", limit=3)
ok(len(mb) == 3 and mb[0]["t"] == "2022-01-03T14:30:00Z" and mb[2]["t"] == "2022-01-03T14:32:00Z", "minute_bars pages and respects limit")
cb = M.daily_bars(fg_b, "BTC/USD", "2022-05-27T00:00:00Z")
ok(len(cb) == 1 and cb[0]["c"] == 29003.0 and cb[0]["v"] == 0.0, "crypto bars routed to v1beta3 and allow zero volume")

# ---- screener: movers (stocks & crypto) and most_active
MOVERS_DOC = {
    "gainers": [{"change": 2.46, "percent_change": 145.56, "price": 4.15, "symbol": "AGRI"}],
    "losers": [{"change": -0.26, "percent_change": -63.07, "price": 0.1502, "symbol": "MTACW"}],
    "last_updated": "2022-03-10T17:53:30.088309839Z",
    "market_type": "stocks",
}
MOST_ACTIVE_DOC = {
    "last_updated": "2022-03-10T17:53:30.088309839Z",
    "most_actives": [{"symbol": "AAPL", "trade_count": 639626, "volume": 122709184}],
}


def screener_handler(base, path, params):
    if path == "/v1beta1/screener/stocks/movers":
        return MOVERS_DOC
    if path == "/v1beta1/screener/crypto/movers":
        return {**MOVERS_DOC, "market_type": "crypto", "gainers": [{"change": 500, "percent_change": 8.5, "price": 64000, "symbol": "BTC/USD"}]}
    if path == "/v1beta1/screener/stocks/most-actives":
        return MOST_ACTIVE_DOC
    raise AssertionError(f"unexpected {path}")


fg_s = FakeGet(screener_handler)
mv = M.movers(fg_s, top=20)
ok(mv["gainers"][0] == {"symbol": "AGRI", "price": 4.15, "change_pct": 145.56} and mv["utc"] == "2022-03-10T17:53:30Z", "stock movers parsed")
cmv = M.movers(fg_s, top=10, market="crypto")
ok(cmv["gainers"][0]["symbol"] == "BTC/USD", "crypto movers parsed")
ma = M.most_active(fg_s, top=20, by="volume")
ok(ma == [{"symbol": "AAPL", "volume": 122709184, "trade_count": 639626}], "most_active parsed")

# ---- news: pagination up to limit, newest first, slash stripped on symbols param
NEWS_P1 = {
    "news": [
        {"id": 100536145, "headline": "Headline 1", "summary": "Sum 1", "symbols": ["SPCX"], "source": "fiscal.ai", "url": "https://example.com/1", "created_at": "2026-10-21T15:02:10Z", "updated_at": "2026-10-21T15:02:10Z"},
        {"id": 62429279, "headline": "Headline 2", "summary": "Sum 2", "symbols": ["TSLA"], "source": "benzinga", "url": "https://example.com/2", "created_at": "2026-10-18T12:51:02Z", "updated_at": "2026-10-18T12:51:02Z"},
    ],
    "next_page_token": "np2",
}
NEWS_P2 = {
    "news": [
        {"id": 111, "headline": "Headline 3", "summary": "Sum 3", "symbols": ["AAPL"], "source": "benzinga", "url": None, "created_at": "2026-10-17T10:00:00Z", "updated_at": "2026-10-17T10:00:00Z"},
        {"id": 112, "headline": "Headline 4", "summary": "Sum 4", "symbols": ["AAPL"], "source": "benzinga", "url": None, "created_at": "2026-10-16T10:00:00Z", "updated_at": "2026-10-16T10:00:00Z"},
    ],
    "next_page_token": None,
}


def news_handler(base, path, params):
    ok(params.get("symbols") == "AAPL,BTCUSD", "news strips slash from crypto symbol")
    return NEWS_P2 if params.get("page_token") == "np2" else NEWS_P1


fg_n = FakeGet(news_handler)
nw = M.news(fg_n, symbols=["AAPL", "BTC/USD"], since_utc_iso="2026-10-01T00:00:00Z", limit=3)
ok(len(nw) == 3 and [a["id"] for a in nw] == [100536145, 62429279, 111], "news follows next_page_token up to limit")

# ---- asset: equity, crypto old symbology, coin pair %2F fallback, 404 -> None
def asset_handler(base, path, params):
    if path == "/v2/assets/AAPL":
        return {"id": "b0b6", "class": "us_equity", "exchange": "NASDAQ", "symbol": "AAPL", "status": "active", "tradable": True, "fractionable": True}
    if path == "/v2/assets/BTCUSD":
        return {"id": "c1", "class": "crypto", "exchange": "CRYPTO", "symbol": "BTC/USD", "status": "active", "tradable": True, "fractionable": True, "min_order_size": "0.0001", "min_trade_increment": "0.0001", "price_increment": "1"}
    if path == "/v2/assets/BTCUSDT":
        raise B.Refused(404, "not found")
    if path == "/v2/assets/BTC%2FUSDT":
        return {"id": "c2", "class": "crypto", "exchange": "CRYPTO", "symbol": "BTC/USDT", "status": "active", "tradable": True, "fractionable": True, "min_order_size": "0.001"}
    raise B.Refused(404, "not found")


fg_a = FakeGet(asset_handler)
a_eq = M.asset(fg_a, "AAPL")
ok(a_eq["tradable"] is True and a_eq["class"] == "us_equity" and a_eq["min_order_size"] is None, "equity asset parsed")
a_btc = M.asset(fg_a, "BTC/USD")
ok(a_btc["class"] == "crypto" and a_btc["min_order_size"] == 0.0001 and a_btc["price_increment"] == 1.0, "crypto asset old symbology parsed")
a_pair = M.asset(fg_a, "BTC/USDT")
ok(a_pair["symbol"] == "BTC/USDT" and a_pair["min_order_size"] == 0.001, "coin pair falls back to URL-encoded %2F path on 404")
ok(M.asset(fg_a, "NOPE") is None, "404 asset returns None")

# ---- market_clock: v2 normal, v2 Refused -> v3, v2 Unclear -> v3
V2_CLOCK = {"is_open": True, "next_close": "2025-06-24T16:00:00-04:00", "next_open": "2025-06-25T09:30:00-04:00", "timestamp": "2025-06-24T14:15:22-04:00"}
V3_CLOCK = {
    "clocks": [{
        "market": {"acronym": "NYSE", "mic": "XNYS", "name": "New York Stock Exchange", "timezone": "America/New_York"},
        "timestamp": "2025-06-24T14:15:22-04:00",
        "is_market_day": True,
        "next_market_open": "2025-06-25T09:30:00-04:00",
        "next_market_close": "2025-06-24T16:00:00-04:00",
        "phase": "core",
        "phase_until": "2025-06-24T16:00:00-04:00",
    }]
}

c_v2 = M.market_clock(FakeGet(lambda b, p, q: V2_CLOCK))
ok(c_v2 == {"is_open": True, "next_open_utc": "2025-06-25T13:30:00Z", "next_close_utc": "2025-06-24T20:00:00Z"}, "v2 clock parsed to UTC")


def clock_refused(b, p, q):
    if p == "/v2/clock":
        raise B.Refused(404, "gone")
    return V3_CLOCK


def clock_unclear(b, p, q):
    if p == "/v2/clock":
        raise B.Unclear("timeout")
    return V3_CLOCK


ok(M.market_clock(FakeGet(clock_refused)) == c_v2, "clock falls back to v3 on Refused")
ok(M.market_clock(FakeGet(clock_unclear)) == c_v2, "clock falls back to v3 on Unclear")

# ---- calendar: v2 (EST + EDT early close) and v3 fallback
V2_CAL = [
    {"date": "2025-01-02", "open": "09:30", "close": "16:00", "session_open": "0400", "session_close": "2000", "settlement_date": "2025-01-03"},
    {"date": "2025-07-03", "open": "09:30", "close": "13:00", "session_open": "0400", "session_close": "1700", "settlement_date": "2025-07-07"},
]
cal = M.calendar(FakeGet(lambda b, p, q: V2_CAL), "2025-01-02", "2025-07-03")
ok(cal[0] == {"date": "2025-01-02", "open_utc": "2025-01-02T14:30:00Z", "close_utc": "2025-01-02T21:00:00Z"}, "v2 calendar EST -> UTC")
ok(cal[1] == {"date": "2025-07-03", "open_utc": "2025-07-03T13:30:00Z", "close_utc": "2025-07-03T17:00:00Z"}, "v2 calendar EDT early close -> UTC")


def cal_v3_handler(b, p, q):
    if p == "/v2/calendar":
        raise B.Refused(404, "gone")
    return {"market": {"acronym": "NYSE"}, "calendar": [{"date": "2025-01-02", "core_start": "2025-01-02T14:30:00Z", "core_end": "2025-01-02T21:00:00Z"}]}


ok(M.calendar(FakeGet(cal_v3_handler), "2025-01-02", "2025-01-02") == [cal[0]], "calendar falls back to v3/calendar/NYSE")

# ---- build_feed: partial failure lands in problems, no secret/raw body leaked, size capped < 200 KB
SECRET_BODY = "SECRET_KEY_LEAK_XYZ raw broker body"


def feed_handler(base, path, params):
    if path == "/v2/clock":
        return V2_CLOCK
    if path == "/v2/stocks/snapshots":
        return {"AAPL": STOCK_SNAP_DOC["AAPL"]}
    if path == "/v1beta3/crypto/us/snapshots":
        return CRYPTO_SNAP_DOC
    if path == "/v1beta1/screener/stocks/movers":
        raise B.Refused(403, SECRET_BODY)
    if path == "/v1beta1/screener/crypto/movers":
        raise B.Unclear("timeout")
    if path == "/v1beta1/screener/stocks/most-actives":
        return MOST_ACTIVE_DOC
    if path == "/v1beta1/news":
        return {
            "news": [
                {"id": i, "headline": f"H{i} " + ("x" * 200), "summary": "y" * 600, "symbols": ["AAPL"], "source": "s", "url": f"https://ex.com/{i}", "created_at": "2026-10-21T15:02:10Z"}
                for i in range(50)
            ],
            "next_page_token": None,
        }
    raise AssertionError(f"unexpected {path}")


fg_feed = FakeGet(feed_handler)
feed = M.build_feed(fg_feed, ["AAPL"], ["BTC/USD"], dt.datetime(2026, 11, 25, 15, 0, tzinfo=dt.timezone.utc))
blob = json.dumps(feed)
ok(feed["clock"]["is_open"] is True and "AAPL" in feed["prices"] and "BTC/USD" in feed["prices"], "build_feed keeps working parts when others fail")
ok(len(feed["most_active"]) == 1 and len(feed["news"]) > 0, "build_feed keeps most_active and news")
ok(len(feed["problems"]) == 2, "two failing parts recorded in problems")
ok(SECRET_BODY not in blob and "SECRET_KEY_LEAK_XYZ" not in blob, "raw refusal body never leaks into feed")
ok(len(blob.encode("utf-8")) < 200_000, "feed stays under 200 KB")

# ---- build_feed trims huge news payloads to stay under 200 KB
def huge_news_handler(base, path, params):
    if path == "/v1beta1/news":
        tok = params.get("page_token")
        page = int(tok) if tok else 0
        return {
            "news": [
                {"id": page * 50 + i, "headline": "A" * 240, "summary": "B" * 500, "symbols": ["AAPL"] * 12, "source": "s", "url": "https://example.com/" + ("u" * 200), "created_at": "2026-10-21T15:02:10Z"}
                for i in range(50)
            ],
            "next_page_token": str(page + 1) if page < 10 else None,
        }
    return feed_handler(base, path, params)


huge_feed = M.build_feed(FakeGet(huge_news_handler), ["AAPL"], ["BTC/USD"], "2026-11-25T15:00:00Z")
ok(len(json.dumps(huge_feed).encode("utf-8")) < 200_000, "huge news feed is capped under 200 KB")

print(f"{N[0]} checks passed")
