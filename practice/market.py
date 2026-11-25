"""Read-only market data layer for the practice trading desk (Alpaca APIs).

Does not open network connections or use HTTP libraries. Every function takes a
`get(base, path, params) -> parsed JSON` callable wired to the broker's
allow-listed GET transport. Standard library only.
"""
import datetime as dt, json, math, re
from zoneinfo import ZoneInfo

try:
    from .broker import Refused, Unclear
except ImportError:
    from broker import Refused, Unclear

DATA, PAPER = "https://data.alpaca.markets", "https://paper-api.alpaca.markets"
READS = [
    (DATA, r"/v2/stocks/snapshots"), (DATA, r"/v1beta3/crypto/us/snapshots"),
    (DATA, r"/v2/stocks/bars"), (DATA, r"/v1beta3/crypto/us/bars"),
    (DATA, r"/v1beta1/screener/(stocks|crypto)/movers"),
    (DATA, r"/v1beta1/screener/stocks/most-actives"), (DATA, r"/v1beta1/news"),
    (PAPER, r"/v2/assets/[A-Za-z0-9._%-]+"), (PAPER, r"/v2/clock"), (PAPER, r"/v3/clock"),
    (PAPER, r"/v2/calendar"), (PAPER, r"/v3/calendar/NYSE"),
]
UTC, NY = dt.timezone.utc, ZoneInfo("America/New_York")
BATCH_SIZE, MAX_PAGES, MAX_FEED_BYTES = 100, 50, 180_000
_TS_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[Tt ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?([Zz]|[+-]\d{2}:?\d{2})$")
_ASSET_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


def _parse_ts(value):
    if isinstance(value, dt.datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    m = _TS_RE.match(value.strip()) if isinstance(value, str) else None
    if not m:
        return None
    y, mo, d, hh, mm, ss, frac, tz_s = m.groups()
    us = int((frac or "")[:6].ljust(6, "0"))
    if tz_s in ("Z", "z"):
        tz = UTC
    else:
        sign, dig = (1 if tz_s[0] == "+" else -1), tz_s[1:].replace(":", "")
        tz = dt.timezone(dt.timedelta(hours=sign * int(dig[:2]), minutes=sign * int(dig[2:])))
    try:
        return dt.datetime(int(y), int(mo), int(d), int(hh), int(mm), int(ss), us, tzinfo=tz).astimezone(UTC)
    except ValueError:
        return None


def _iso_utc(value):
    t = _parse_ts(value)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ") if t else None

def _finite(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None

def _pos(v): return x if (x := _finite(v)) is not None and x > 0 else None
def _nonneg(v): return x if (x := _finite(v)) is not None and x >= 0 else None


def _parse_snapshot(snap, source, max_spread):
    if not isinstance(snap, dict):
        return None
    q, t = snap.get("latestQuote") or {}, snap.get("latestTrade") or {}
    db, pb = snap.get("dailyBar") or {}, snap.get("prevDailyBar") or {}
    bid, ask, trade_p = _pos(q.get("bp")), _pos(q.get("ap")), _pos(t.get("p"))
    price, utc = None, None
    if bid is not None and ask is not None and ask >= bid:
        mid = (bid + ask) / 2.0
        if mid > 0 and (ask - bid) / mid < max_spread:
            price, utc = mid, _iso_utc(q.get("t"))  # a quote is dated by its own time, never by the last trade's
    if (price is None or utc is None) and trade_p is not None:
        price, utc = trade_p, _iso_utc(t.get("t"))
    if price is None or utc is None:
        return None
    return {
        "price": price, "bid": bid, "ask": ask, "utc": utc,
        "prev_close": _pos(pb.get("c")), "day_open": _pos(db.get("o")),
        "day_high": _pos(db.get("h")), "day_low": _pos(db.get("l")),
        "day_volume": _nonneg(db.get("v")), "source": source,
    }


def prices(get, symbols, max_spread=0.02):
    """Latest prices from stock and crypto snapshots. Missing or invalid symbols are omitted."""
    uniq = list(dict.fromkeys(s for s in (symbols or []) if isinstance(s, str) and s.strip()))
    stocks, crypto, out = [s for s in uniq if "/" not in s], [s for s in uniq if "/" in s], {}
    for i in range(0, len(stocks), BATCH_SIZE):
        batch, raw, used, last_err = stocks[i : i + BATCH_SIZE], None, None, None
        for feed in ("iex", "delayed_sip"):
            try:
                raw, used = get(DATA, "/v2/stocks/snapshots", {"symbols": ",".join(batch), "feed": feed}), feed
                break
            except Refused as e:
                last_err = e
        if raw is None:
            raise last_err
        for sym, snap in (raw.items() if isinstance(raw, dict) else ()):
            if (parsed := _parse_snapshot(snap, used, max_spread)) is not None:
                out[sym] = parsed
    for i in range(0, len(crypto), BATCH_SIZE):
        raw = get(DATA, "/v1beta3/crypto/us/snapshots", {"symbols": ",".join(crypto[i : i + BATCH_SIZE])})
        snaps = (raw or {}).get("snapshots") if isinstance(raw, dict) else None
        for sym, snap in (snaps.items() if isinstance(snaps, dict) else ()):
            if (parsed := _parse_snapshot(snap, "crypto-us", max_spread)) is not None:
                out[sym] = parsed
    return out


def _paged_bars(get, path, base_params, symbol, max_items=None):
    out, token = [], None
    for _ in range(MAX_PAGES):
        p = dict(base_params)
        if max_items is not None:
            rem = max_items - len(out)
            if rem <= 0:
                return out[:max_items]
            p["limit"] = min(rem, 10000)
        if token:
            p["page_token"] = token
        resp = get(DATA, path, p)
        bmap = (resp or {}).get("bars") if isinstance(resp, dict) else None
        for b in (bmap.get(symbol, []) if isinstance(bmap, dict) else ()) or ():
            if isinstance(b, dict):
                ts = _iso_utc(b.get("t"))
                o, h, l, c, v = _pos(b.get("o")), _pos(b.get("h")), _pos(b.get("l")), _pos(b.get("c")), _nonneg(b.get("v"))
                if ts and None not in (o, h, l, c, v):
                    out.append({"t": ts, "o": o, "h": h, "l": l, "c": c, "v": v})
        token = resp.get("next_page_token") if isinstance(resp, dict) else None
        if not token or (max_items is not None and len(out) >= max_items):
            return out[:max_items] if max_items is not None else out
    raise Unclear("too many bar pages")


def _bars(get, symbol, timeframe, start_utc_iso, limit=None, adjustment=None):
    if "/" in symbol:
        return _paged_bars(get, "/v1beta3/crypto/us/bars", {"symbols": symbol, "timeframe": timeframe, "start": start_utc_iso, "limit": 1000, "sort": "asc"}, symbol, limit)
    last_err = None
    for feed in ("sip", "iex"):
        p = {"symbols": symbol, "timeframe": timeframe, "start": start_utc_iso, "limit": 1000, "feed": feed, "sort": "asc"}
        if adjustment:
            p["adjustment"] = adjustment
        try:
            return _paged_bars(get, "/v2/stocks/bars", p, symbol, limit)
        except Refused as e:
            last_err = e
    raise last_err


def minute_bars(get, symbol, start_utc_iso, limit=1000): return _bars(get, symbol, "1Min", start_utc_iso, limit=limit)
def daily_bars(get, symbol, start_utc_iso): return _bars(get, symbol, "1Day", start_utc_iso, adjustment="all")


def movers(get, top=20, market="stocks"):
    if market not in ("stocks", "crypto"):
        raise ValueError("market must be 'stocks' or 'crypto'")
    resp = get(DATA, f"/v1beta1/screener/{market}/movers", {"top": max(1, min(int(top), 50))})
    if not isinstance(resp, dict):
        raise Unclear("unexpected movers response")
    def clean(items):
        return [
            {"symbol": m["symbol"], "price": px, "change_pct": pct}
            for m in (items or ()) if isinstance(m, dict) and isinstance(m.get("symbol"), str) and m["symbol"]
            and (px := _pos(m.get("price"))) is not None and (pct := _finite(m.get("percent_change"))) is not None
        ]
    return {"gainers": clean(resp.get("gainers")), "losers": clean(resp.get("losers")), "utc": _iso_utc(resp.get("last_updated"))}


def most_active(get, top=20, by="volume"):
    if by not in ("volume", "trades"):
        raise ValueError("by must be 'volume' or 'trades'")
    resp = get(DATA, "/v1beta1/screener/stocks/most-actives", {"top": max(1, min(int(top), 100)), "by": by})
    items = (resp.get("most_actives") if isinstance(resp, dict) else ()) or ()
    return [
        {"symbol": r["symbol"], "volume": int(vol), "trade_count": int(cnt)}
        for r in items if isinstance(r, dict) and isinstance(r.get("symbol"), str) and r["symbol"]
        and (vol := _nonneg(r.get("volume"))) is not None and (cnt := _nonneg(r.get("trade_count"))) is not None
    ]


def news(get, symbols=None, since_utc_iso=None, limit=50):
    cap, base_p = max(1, int(limit)), {"sort": "desc", "include_content": "false"}
    if symbols:
        norm = [s.replace("/", "") for s in symbols if isinstance(s, str) and s.strip()]
        if norm:
            base_p["symbols"] = ",".join(dict.fromkeys(norm))
    if since_utc_iso:
        base_p["start"] = since_utc_iso
    out, token = [], None
    for _ in range(MAX_PAGES):
        if len(out) >= cap: break
        p = dict(base_p, limit=min(cap - len(out), 50), **({"page_token": token} if token else {}))
        resp = get(DATA, "/v1beta1/news", p)
        for a in (resp.get("news") if isinstance(resp, dict) else ()) or ():
            if isinstance(a, dict) and (utc := _iso_utc(a.get("created_at")) or _iso_utc(a.get("updated_at"))):
                out.append({
                    "utc": utc, "headline": str(a.get("headline") or "").strip(), "summary": str(a.get("summary") or "").strip(),
                    "symbols": [str(s) for s in (a.get("symbols") or ()) if isinstance(s, str)],
                    "source": str(a.get("source") or ""), "url": a.get("url") if isinstance(a.get("url"), str) else None, "id": a.get("id"),
                })
                if len(out) >= cap: break
        if not (token := resp.get("next_page_token") if isinstance(resp, dict) else None):
            break
    return out[:cap]


def asset(get, symbol):
    if not isinstance(symbol, str) or not symbol or ".." in symbol or not _ASSET_RE.fullmatch(symbol):
        raise ValueError("invalid asset symbol")
    candidates = [symbol.replace("/", ""), symbol.replace("/", "%2F")] if "/" in symbol else [symbol]
    resp = None
    for idx, sym_path in enumerate(candidates):
        try:
            resp = get(PAPER, f"/v2/assets/{sym_path}", None); break
        except Refused as e:
            if e.status != 404: raise
            if idx + 1 == len(candidates): return None
    if not isinstance(resp, dict): return None
    return {
        "symbol": resp.get("symbol"), "tradable": bool(resp.get("tradable")), "fractionable": bool(resp.get("fractionable")),
        "class": resp.get("class"), "exchange": resp.get("exchange"), "status": resp.get("status"),
        "min_order_size": _pos(resp.get("min_order_size")), "min_trade_increment": _pos(resp.get("min_trade_increment")),
        "price_increment": _pos(resp.get("price_increment")),
    }


def market_clock(get):
    try:
        c = get(PAPER, "/v2/clock", None)
        if isinstance(c, dict) and isinstance(c.get("is_open"), bool):
            return {"is_open": c["is_open"], "next_open_utc": _iso_utc(c.get("next_open")), "next_close_utc": _iso_utc(c.get("next_close"))}
    except (Refused, Unclear):
        pass
    c3 = get(PAPER, "/v3/clock", {"markets": "NYSE"})
    clocks = c3.get("clocks") if isinstance(c3, dict) else None
    if not isinstance(clocks, list) or not clocks:
        raise Unclear("missing clock data")
    k = next((x for x in clocks if isinstance(x, dict) and (x.get("market") or {}).get("acronym") in ("NYSE", "NASDAQ", "XNYS", "XNAS")), clocks[0])
    if not isinstance(k, dict) or not isinstance(k.get("phase"), str):
        raise Unclear("unexpected v3 clock shape")
    return {"is_open": k["phase"] == "core", "next_open_utc": _iso_utc(k.get("next_market_open")), "next_close_utc": _iso_utc(k.get("next_market_close"))}


def calendar(get, start_date, end_date):
    def ny_utc(ds, hm):
        y, mo, d = (int(x) for x in ds.split("-")); hh, mm = (int(x) for x in hm.split(":"))
        return dt.datetime(y, mo, d, hh, mm, tzinfo=NY).astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        rows = get(PAPER, "/v2/calendar", {"start": start_date, "end": end_date})
        if isinstance(rows, list):
            return [{"date": r["date"], "open_utc": ny_utc(r["date"], r["open"]), "close_utc": ny_utc(r["date"], r["close"])}
                    for r in rows if isinstance(r, dict) and r.get("date") and r.get("open") and r.get("close")]
    except (Refused, Unclear):
        pass
    resp = get(PAPER, "/v3/calendar/NYSE", {"start": start_date, "end": end_date, "timezone": "UTC"})
    days = resp.get("calendar") if isinstance(resp, dict) else None
    if not isinstance(days, list):
        raise Unclear("unexpected calendar response")
    return [{"date": r["date"], "open_utc": o, "close_utc": c}
            for r in days if isinstance(r, dict) and r.get("date") and (o := _iso_utc(r.get("core_start"))) and (c := _iso_utc(r.get("core_end")))]


def build_feed(get, watch_symbols, held_symbols, now_utc):
    problems = []
    all_syms = list(dict.fromkeys(list(watch_symbols or []) + list(held_symbols or [])))
    def safe(part, default, fn):
        try:
            return fn()
        except Refused as e:
            problems.append(f"Could not read {part}: broker refused request (HTTP {e.status}).")
        except Unclear:
            problems.append(f"Could not read {part}: broker response was unclear.")
        except (ValueError, KeyError, TypeError):
            problems.append(f"Could not read {part}: unexpected response format.")
        return default
    feed = {
        "utc": _iso_utc(now_utc) or str(now_utc),
        "clock": safe("market clock", None, lambda: market_clock(get)),
        "prices": safe("prices", {}, lambda: prices(get, all_syms) if all_syms else {}),
        "movers": safe("stock movers", {"gainers": [], "losers": [], "utc": None}, lambda: movers(get, top=20, market="stocks")),
        "crypto_movers": safe("crypto movers", {"gainers": [], "losers": [], "utc": None}, lambda: movers(get, top=20, market="crypto")),
        "most_active": safe("most active stocks", [], lambda: most_active(get, top=20, by="volume")),
        "news": [
            {"utc": a["utc"], "headline": a["headline"][:240], "summary": a["summary"][:500], "symbols": a["symbols"][:12], "url": a["url"]}
            for a in safe("news", [], lambda: news(get, symbols=all_syms or None, limit=50))
        ],
        "problems": problems,
    }
    while len(json.dumps(feed, separators=(",", ":")).encode("utf-8")) > MAX_FEED_BYTES and feed["news"]:
        feed["news"].pop()
    return feed
