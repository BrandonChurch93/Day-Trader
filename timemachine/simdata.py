"""Simulated Alpaca Market Data + Clock/Calendar/Asset GET layer backed by Tape.

`SimData(tape, clock).get(base, path, params)` answers every read path in
`practice/market.py: READS` as of `clock()` (the simulated UTC now), in the
exact JSON shapes Alpaca documents. Nothing stamped after `clock()` is ever
returned. Standard library only.
"""
import datetime as dt, re, sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "practice") not in sys.path:
    sys.path.insert(0, str(ROOT / "practice"))
from broker import Refused
import market as M

try:
    from .tape import NY, UTC, from_epoch, to_epoch, to_utc_dt
except ImportError:
    from tape import NY, UTC, from_epoch, to_epoch, to_utc_dt

_TF_MAP = {"1Min": "1Min", "1T": "1Min", "30Min": "30Min", "30T": "30Min", "1Day": "1Day", "1D": "1Day"}


def _iso(val):
    if val is None:
        return None
    d = to_utc_dt(val)
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def _clamp_end(end_param, now_dt):
    if not end_param:
        return now_dt
    end_dt = to_utc_dt(end_param)
    return end_dt if end_dt < now_dt else now_dt


def _snap_to_alpaca(s):
    t_iso = _iso(s["t"])
    p = s["price"]
    out = {
        "latestQuote": {"bp": p, "ap": p, "bs": 1, "as": 1, "t": t_iso},
        "latestTrade": {"p": p, "s": 1, "t": t_iso},
    }
    if s.get("day_open") is not None:
        out["dailyBar"] = {
            "t": t_iso, "o": s["day_open"], "h": s["day_high"], "l": s["day_low"],
            "c": p, "v": s["day_volume"] if s.get("day_volume") is not None else 0,
        }
    if s.get("prev_close") is not None:
        out["prevDailyBar"] = {
            "t": t_iso, "o": s["prev_close"], "h": s["prev_close"], "l": s["prev_close"],
            "c": s["prev_close"], "v": 0,
        }
    return out


class SimData:
    """Answers `practice/market.py` GET calls from a recorded Tape as of `clock()`."""

    def __init__(self, tape, clock):
        self.tape = tape
        self.clock = clock

    def __call__(self, base, path, params=None):
        return self.get(base, path, params)

    def _now(self):
        return to_utc_dt(self.clock())

    def get(self, base, path, params=None):
        if not any(base == b and re.fullmatch(pat, path) for b, pat in M.READS):
            raise Refused(404, "unknown read path")
        params = params or {}
        now = self._now()

        if base == M.DATA and path == "/v2/stocks/snapshots":
            syms = [s.strip() for s in str(params.get("symbols", "")).split(",") if s.strip()]
            snaps = self.tape.snapshot(syms, now)
            return {sym: _snap_to_alpaca(s) for sym, s in snaps.items()}

        if base == M.DATA and path == "/v1beta3/crypto/us/snapshots":
            syms = [s.strip() for s in str(params.get("symbols", "")).split(",") if s.strip()]
            snaps = self.tape.snapshot(syms, now)
            return {"snapshots": {sym: _snap_to_alpaca(s) for sym, s in snaps.items()}}

        if base == M.DATA and path in ("/v2/stocks/bars", "/v1beta3/crypto/us/bars"):
            return self._bars(params, now)

        if base == M.DATA and path in ("/v1beta1/screener/stocks/movers", "/v1beta1/screener/crypto/movers"):
            mkt = "crypto" if "/crypto/" in path else "stocks"
            top = int(params.get("top", 10))
            mv = self.tape.movers(now, top=top, market=mkt)
            return {"gainers": mv["gainers"], "losers": mv["losers"], "last_updated": _iso(now), "market_type": mkt}

        if base == M.DATA and path == "/v1beta1/screener/stocks/most-actives":
            top = int(params.get("top", 10))
            by = str(params.get("by", "volume"))
            return {"most_actives": self.tape.most_active(now, top=top, by=by), "last_updated": _iso(now)}

        if base == M.DATA and path == "/v1beta1/news":
            return self._news(params, now)

        if base == M.PAPER and path.startswith("/v2/assets/"):
            return self._asset(path[len("/v2/assets/"):], now)

        if base == M.PAPER and path == "/v2/clock":
            return {
                "is_open": self.tape.is_open(now),
                "next_open": _iso(self.tape.next_open(now)),
                "next_close": _iso(self.tape.next_close(now)),
                "timestamp": _iso(now),
            }

        if base == M.PAPER and path == "/v3/clock":
            is_open = self.tape.is_open(now)
            ny_date = now.astimezone(NY).strftime("%Y-%m-%d")
            nxt_open = self.tape.next_open(now)
            nxt_close = self.tape.next_close(now)
            return {
                "clocks": [{
                    "market": {"acronym": "NYSE", "mic": "XNYS", "name": "New York Stock Exchange", "timezone": "America/New_York"},
                    "timestamp": _iso(now),
                    "is_market_day": self.tape.session(ny_date) is not None,
                    "next_market_open": _iso(nxt_open),
                    "next_market_close": _iso(nxt_close),
                    "phase": "core" if is_open else "closed",
                    "phase_until": _iso(nxt_close if is_open else nxt_open),
                }]
            }

        if base == M.PAPER and path == "/v2/calendar":
            start = str(params.get("start") or "1970-01-01")[:10]
            end = str(params.get("end") or "2099-12-31")[:10]
            rows = self.tape.sessions(start, end)
            return [
                {
                    "date": d,
                    "open": o.astimezone(NY).strftime("%H:%M"),
                    "close": c.astimezone(NY).strftime("%H:%M"),
                    "session_open": "0400",
                    "session_close": "2000",
                    "settlement_date": d,
                }
                for d, o, c in rows
            ]

        if base == M.PAPER and path == "/v3/calendar/NYSE":
            start = str(params.get("start") or "1970-01-01")[:10]
            end = str(params.get("end") or "2099-12-31")[:10]
            rows = self.tape.sessions(start, end)
            return {
                "market": {"acronym": "NYSE", "mic": "XNYS", "name": "New York Stock Exchange", "timezone": "America/New_York"},
                "calendar": [{"date": d, "core_start": _iso(o), "core_end": _iso(c)} for d, o, c in rows],
            }

        raise Refused(404, "unknown read path")

    def _bars(self, params, now):
        syms = [s.strip() for s in str(params.get("symbols", "")).split(",") if s.strip()]
        tf = _TF_MAP.get(str(params.get("timeframe", "1Day")))
        if not tf:
            raise Refused(400, "unsupported timeframe")
        eff_now = _clamp_end(params.get("end"), now)
        start_dt = to_utc_dt(params["start"]) if params.get("start") else from_epoch(0)
        if start_dt > eff_now:
            return {"bars": {}, "next_page_token": None}

        limit = max(1, min(int(params.get("limit", 1000)), 10000))
        offset = int(params["page_token"]) if params.get("page_token") else 0
        desc = str(params.get("sort", "asc")).lower() == "desc"

        flat = []
        for sym in syms:
            rows = self.tape.bars(sym, tf, start_dt, eff_now, limit=None)
            if desc:
                rows = list(reversed(rows))
            for b in rows:
                flat.append((sym, {"t": _iso(b["t"]), "o": b["o"], "h": b["h"], "l": b["l"], "c": b["c"], "v": b["v"]}))

        page = flat[offset : offset + limit]
        next_tok = str(offset + limit) if offset + limit < len(flat) else None
        out_bars = {}
        for sym, b in page:
            out_bars.setdefault(sym, []).append(b)
        return {"bars": out_bars, "next_page_token": next_tok}

    def _news(self, params, now):
        eff_now = _clamp_end(params.get("end"), now)
        start_dt = to_utc_dt(params["start"]) if params.get("start") else None
        if start_dt is not None and start_dt > eff_now:
            return {"news": [], "next_page_token": None}
        syms = [s.strip() for s in str(params.get("symbols", "")).split(",") if s.strip()] or None
        limit = max(1, min(int(params.get("limit", 10)), 50))
        offset = int(params["page_token"]) if params.get("page_token") else 0
        asc = str(params.get("sort", "desc")).lower() == "asc"

        # Fetch enough items to serve offset + limit + 1 (to know if another page exists)
        items = self.tape.news(eff_now, symbols=syms, since_utc=start_dt, limit=offset + limit + 1)
        if asc:
            items = list(reversed(items))
        page = items[offset : offset + limit]
        next_tok = str(offset + limit) if len(items) > offset + limit else None

        eff_ep = to_epoch(eff_now)
        formatted = []
        for a in page:
            upd = a["updated"] if to_epoch(a["updated"]) <= eff_ep else a["created"]
            rec = {
                "id": a["id"],
                "headline": a["headline"],
                "summary": a["summary"],
                "symbols": a["symbols"],
                "source": a["source"],
                "url": a["url"],
                "created_at": _iso(a["created"]),
                "updated_at": _iso(upd),
            }
            if a.get("edited_later"):
                rec["edited_later"] = True
            formatted.append(rec)
        return {"news": formatted, "next_page_token": next_tok}

    def _asset(self, raw_sym, now):
        sym = raw_sym.replace("%2F", "/").replace("%2f", "/")
        resolved = None
        if self.tape.has_symbol_as_of(sym, now):
            resolved = sym
        elif "/" not in sym and len(sym) > 3 and sym.endswith("USD"):
            alt = sym[:-3] + "/USD"
            if self.tape.has_symbol_as_of(alt, now):
                resolved = alt
        if not resolved:
            raise Refused(404, "asset not found")
        is_crypto = "/" in resolved
        out = {
            "symbol": resolved,
            "tradable": True,
            "fractionable": True,
            "class": "crypto" if is_crypto else "us_equity",
            "exchange": "CRYPTO" if is_crypto else "NYSE",
            "status": "active",
        }
        if is_crypto:
            out.update({"min_order_size": "0.0001", "min_trade_increment": "0.0001", "price_increment": "0.01"})
        return out
