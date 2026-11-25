"""Recorded market tape backed by SQLite with strict as-of (no look-ahead) reads.

Every read takes `now_utc` and refuses to return any bar, quote, news item, or
screener stat stamped after `now_utc`. Thread-safe via one SQLite connection per
thread (WAL mode) and a write lock. Standard library only.
"""
import time
import datetime as dt, json, math, os, re, sqlite3, subprocess, sys, threading
from pathlib import Path
from zoneinfo import ZoneInfo

UTC = dt.timezone.utc
NY = ZoneInfo("America/New_York")
DEFAULT_STORE = Path(os.environ.get("TM_STORE", "/home/user/workspace/rig/tm_store"))
TF_SECS = {"1Min": 60, "30Min": 1800, "1Day": 86400}
_TS_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[Tt ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?([Zz]|[+-]\d{2}:?\d{2})$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS bars (
    symbol TEXT NOT NULL,
    tf TEXT NOT NULL,
    t INTEGER NOT NULL,
    o REAL NOT NULL,
    h REAL NOT NULL,
    l REAL NOT NULL,
    c REAL NOT NULL,
    v REAL NOT NULL,
    PRIMARY KEY (symbol, tf, t)
);
CREATE INDEX IF NOT EXISTS idx_bars_tf_t ON bars (tf, t);

CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY,
    created INTEGER NOT NULL,
    updated INTEGER NOT NULL,
    headline TEXT NOT NULL,
    summary TEXT NOT NULL,
    source TEXT NOT NULL,
    url TEXT,
    symbols_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_news_created ON news (created DESC, id DESC);

CREATE TABLE IF NOT EXISTS news_symbols (
    symbol TEXT NOT NULL,
    created INTEGER NOT NULL,
    id INTEGER NOT NULL,
    PRIMARY KEY (symbol, created, id)
);
CREATE INDEX IF NOT EXISTS idx_news_sym_created ON news_symbols (symbol, created DESC, id DESC);

CREATE TABLE IF NOT EXISTS sessions (
    date TEXT PRIMARY KEY,
    open_utc INTEGER NOT NULL,
    close_utc INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS universe (
    date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    PRIMARY KEY (date, symbol)
);

CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def to_utc_dt(value):
    """Convert datetime, RFC-3339 string, YYYY-MM-DD date string, or epoch seconds to UTC datetime."""
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return dt.datetime.fromtimestamp(float(value), tz=UTC)
    if isinstance(value, str):
        s = value.strip()
        if len(s) == 10 and s[4] == "-" and s[7] == "-":
            y, mo, d = (int(x) for x in s.split("-"))
            return dt.datetime(y, mo, d, tzinfo=UTC)
        m = _TS_RE.match(s)
        if m:
            y, mo, d, hh, mm, ss, frac, tz_s = m.groups()
            us = int((frac or "")[:6].ljust(6, "0"))
            if tz_s in ("Z", "z"):
                tz = UTC
            else:
                sign, dig = (1 if tz_s[0] == "+" else -1), tz_s[1:].replace(":", "")
                tz = dt.timezone(dt.timedelta(hours=sign * int(dig[:2]), minutes=sign * int(dig[2:])))
            return dt.datetime(int(y), int(mo), int(d), int(hh), int(mm), int(ss), us, tzinfo=tz).astimezone(UTC)
    raise ValueError(f"cannot parse timestamp: {value!r}")


def to_epoch(value):
    """Convert datetime/ISO/epoch to integer UTC epoch seconds (floored)."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    return int(to_utc_dt(value).timestamp())


def from_epoch(ts):
    return dt.datetime.fromtimestamp(int(ts), tz=UTC)


def _day_bounds(symbol, date_str):
    y, mo, d = (int(x) for x in date_str.split("-"))
    if "/" in symbol:
        start = dt.datetime(y, mo, d, tzinfo=UTC)
        return int(start.timestamp()), int((start + dt.timedelta(days=1)).timestamp())
    start = dt.datetime(y, mo, d, tzinfo=NY).astimezone(UTC)
    end = dt.datetime(y, mo, d, 23, 59, 59, tzinfo=NY).astimezone(UTC) + dt.timedelta(seconds=1)
    return int(start.timestamp()), int(end.timestamp())


def _default_stock_close_epoch(date_str):
    y, mo, d = (int(x) for x in date_str.split("-"))
    return int(dt.datetime(y, mo, d, 16, 0, tzinfo=NY).astimezone(UTC).timestamp())


class Tape:
    """Thread-safe SQLite market tape with strict as-of queries."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else (Path(os.environ.get("TM_STORE", str(DEFAULT_STORE))) / "tape.sqlite")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._write_lock = threading.Lock()
        with self._write_lock:
            conn = self._conn()
            conn.executescript(SCHEMA)
            conn.commit()

    def _conn(self):
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.path), timeout=30.0)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=30000")
            self._local.conn = conn
        return conn

    def close(self):
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None

    # ---- write methods (used by record.py and tests)
    def add_bars(self, rows):
        """Insert or replace bars. Each row: (symbol, tf, t, o, h, l, c, v) or dict."""
        cleaned = []
        for r in rows:
            if isinstance(r, dict):
                sym, tf, t, o, h, l, c, v = r["symbol"], r["tf"], to_epoch(r["t"]), float(r["o"]), float(r["h"]), float(r["l"]), float(r["c"]), float(r["v"])
            else:
                sym, tf, t, o, h, l, c, v = r[0], r[1], to_epoch(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[6]), float(r[7])
            if tf not in TF_SECS:
                raise ValueError(f"unsupported tf: {tf}")
            if all(math.isfinite(x) and x > 0 for x in (o, h, l, c)) and math.isfinite(v) and v >= 0:
                cleaned.append((sym, tf, t, o, h, l, c, v))
        if not cleaned:
            return 0
        with self._write_lock:
            conn = self._conn()
            conn.executemany(
                "INSERT OR REPLACE INTO bars (symbol, tf, t, o, h, l, c, v) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                cleaned,
            )
            conn.commit()
        return len(cleaned)

    def add_news(self, rows):
        """Insert news articles without overwriting earlier headline/summary if already stored."""
        news_rows, sym_rows = [], []
        for r in rows:
            nid = int(r["id"])
            created = to_epoch(r.get("created") if "created" in r else r.get("created_at"))
            updated = to_epoch(r.get("updated") if "updated" in r else (r.get("updated_at") or created))
            syms = [str(s) for s in (r.get("symbols") or ()) if isinstance(s, str) and s]
            news_rows.append((
                nid, created, updated, str(r.get("headline") or ""), str(r.get("summary") or ""),
                str(r.get("source") or ""), r.get("url"), json.dumps(syms),
            ))
            for s in dict.fromkeys(syms):
                sym_rows.append((s, created, nid))
        if not news_rows:
            return 0
        with self._write_lock:
            conn = self._conn()
            conn.executemany(
                "INSERT OR IGNORE INTO news (id, created, updated, headline, summary, source, url, symbols_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                news_rows,
            )
            if sym_rows:
                conn.executemany(
                    "INSERT OR IGNORE INTO news_symbols (symbol, created, id) VALUES (?, ?, ?)",
                    sym_rows,
                )
            conn.commit()
        return len(news_rows)

    def add_sessions(self, rows):
        """Insert or replace trading sessions: (date, open_utc, close_utc) or dict."""
        cleaned = []
        for r in rows:
            if isinstance(r, dict):
                cleaned.append((str(r["date"]), to_epoch(r["open_utc"]), to_epoch(r["close_utc"])))
            else:
                cleaned.append((str(r[0]), to_epoch(r[1]), to_epoch(r[2])))
        if not cleaned:
            return 0
        with self._write_lock:
            conn = self._conn()
            conn.executemany("INSERT OR REPLACE INTO sessions (date, open_utc, close_utc) VALUES (?, ?, ?)", cleaned)
            conn.commit()
        return len(cleaned)

    def add_universe(self, date_str, symbols):
        """Set the liquid stock universe for a given YYYY-MM-DD date."""
        syms = sorted(set(s for s in symbols if isinstance(s, str) and s))
        with self._write_lock:
            conn = self._conn()
            conn.execute("DELETE FROM universe WHERE date = ?", (date_str,))
            if syms:
                conn.executemany("INSERT INTO universe (date, symbol) VALUES (?, ?)", [(date_str, s) for s in syms])
            conn.commit()
        return len(syms)

    def set_meta(self, key, value):
        with self._write_lock:
            conn = self._conn()
            conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (str(key), str(value)))
            conn.commit()

    def get_meta(self, key, default=None):
        row = self._conn().execute("SELECT value FROM meta WHERE key = ?", (str(key),)).fetchone()
        return row[0] if row else default

    # ---- session / clock reads
    def session(self, date_str):
        row = self._conn().execute("SELECT open_utc, close_utc FROM sessions WHERE date = ?", (str(date_str),)).fetchone()
        return (from_epoch(row[0]), from_epoch(row[1])) if row else None

    def sessions(self, first_date, last_date):
        rows = self._conn().execute(
            "SELECT date, open_utc, close_utc FROM sessions WHERE date >= ? AND date <= ? ORDER BY date ASC",
            (str(first_date), str(last_date)),
        ).fetchall()
        return [(r[0], from_epoch(r[1]), from_epoch(r[2])) for r in rows]

    def is_open(self, now_utc):
        now_ts = to_epoch(now_utc)
        row = self._conn().execute(
            "SELECT 1 FROM sessions WHERE open_utc <= ? AND close_utc > ? LIMIT 1",
            (now_ts, now_ts),
        ).fetchone()
        return row is not None

    def next_open(self, now_utc):
        now_ts = to_epoch(now_utc)
        row = self._conn().execute(
            "SELECT open_utc FROM sessions WHERE open_utc > ? ORDER BY open_utc ASC LIMIT 1",
            (now_ts,),
        ).fetchone()
        return from_epoch(row[0]) if row else None

    def next_close(self, now_utc):
        now_ts = to_epoch(now_utc)
        row = self._conn().execute(
            "SELECT close_utc FROM sessions WHERE close_utc > ? ORDER BY close_utc ASC LIMIT 1",
            (now_ts,),
        ).fetchone()
        return from_epoch(row[0]) if row else None

    # ---- bar reads (strict as-of)
    def _stock_day_close_epoch(self, date_str):
        row = self._conn().execute("SELECT close_utc FROM sessions WHERE date = ?", (date_str,)).fetchone()
        return row[0] if row else _default_stock_close_epoch(date_str)

    def _bar_end_epoch(self, symbol, tf, t_epoch):
        if tf == "1Min":
            return t_epoch + 60
        if tf == "30Min":
            return t_epoch + 1800
        if "/" in symbol:
            return t_epoch + 86400
        d_str = from_epoch(t_epoch).astimezone(NY).strftime("%Y-%m-%d")
        return self._stock_day_close_epoch(d_str)

    def bars(self, symbol, tf, start_utc, now_utc, limit=None):
        """Return finished bars oldest first as of now_utc. limit keeps newest `limit` bars."""
        if tf not in TF_SECS:
            raise ValueError(f"unsupported tf: {tf}")
        now_ts = to_epoch(now_utc)
        start_ts = to_epoch(start_utc) if start_utc is not None else 0
        if start_ts > now_ts:
            return []

        conn = self._conn()
        if tf in ("1Min", "30Min") or "/" in symbol:
            max_t = now_ts - TF_SECS[tf]
            if start_ts > max_t:
                return []
            if limit is not None:
                lim = max(0, int(limit))
                if lim == 0:
                    return []
                rows = conn.execute(
                    "SELECT t, o, h, l, c, v FROM bars WHERE symbol = ? AND tf = ? AND t >= ? AND t <= ? ORDER BY t DESC LIMIT ?",
                    (symbol, tf, start_ts, max_t, lim),
                ).fetchall()
                rows.reverse()
            else:
                rows = conn.execute(
                    "SELECT t, o, h, l, c, v FROM bars WHERE symbol = ? AND tf = ? AND t >= ? AND t <= ? ORDER BY t ASC",
                    (symbol, tf, start_ts, max_t),
                ).fetchall()
        else:
            # 1Day stock bars: visible once now_ts >= session close_utc for that bar's trading date
            rows_all = conn.execute(
                "SELECT t, o, h, l, c, v FROM bars WHERE symbol = ? AND tf = '1Day' AND t >= ? AND t <= ? ORDER BY t ASC",
                (symbol, start_ts, now_ts),
            ).fetchall()
            rows = []
            for r in rows_all:
                d_str = from_epoch(r[0]).astimezone(NY).strftime("%Y-%m-%d")
                if now_ts >= self._stock_day_close_epoch(d_str):
                    rows.append(r)
            if limit is not None:
                lim = max(0, int(limit))
                rows = rows[-lim:] if lim > 0 else []

        return [{"t": from_epoch(r[0]), "o": r[1], "h": r[2], "l": r[3], "c": r[4], "v": r[5]} for r in rows]

    def fill_bar(self, symbol, after_utc, before_utc):
        """First 1Min bar with after_utc <= t and t + 60s <= before_utc, or None."""
        after_ts, before_ts = to_epoch(after_utc), to_epoch(before_utc)
        max_t = before_ts - 60
        if after_ts > max_t:
            return None
        row = self._conn().execute(
            "SELECT t, o, h, l, c, v FROM bars WHERE symbol = ? AND tf = '1Min' AND t >= ? AND t <= ? ORDER BY t ASC LIMIT 1",
            (symbol, after_ts, max_t),
        ).fetchone()
        return {"t": from_epoch(row[0]), "o": row[1], "h": row[2], "l": row[3], "c": row[4], "v": row[5]} if row else None

    def has_minutes(self, symbol, date_str):
        lo, hi = _day_bounds(symbol, str(date_str))
        row = self._conn().execute(
            "SELECT 1 FROM bars WHERE symbol = ? AND tf = '1Min' AND t >= ? AND t < ? LIMIT 1",
            (symbol, lo, hi),
        ).fetchone()
        return row is not None

    def has_symbol_as_of(self, symbol, now_utc):
        """True if the tape has any finished bar for `symbol` as of `now_utc`."""
        now_ts = to_epoch(now_utc)
        conn = self._conn()
        for tf, dur in (("1Min", 60), ("30Min", 1800)):
            if conn.execute("SELECT 1 FROM bars WHERE symbol = ? AND tf = ? AND t <= ? LIMIT 1", (symbol, tf, now_ts - dur)).fetchone():
                return True
        return bool(self.bars(symbol, "1Day", 0, now_ts, limit=1))

    def ensure_minutes(self, symbol, date_str):
        """Fetch missing 1Min bars via record.py if TM_HANDLE is set; else return False."""
        if self.has_minutes(symbol, date_str):
            return True
        handle = os.environ.get("TM_HANDLE", "").strip()
        if not handle:
            return False
        rec_script = str(Path(__file__).resolve().parent / "record.py")
        cmd = [
            "pplx", "credentials", "run", handle, "--",
            sys.executable, rec_script, "minutes",
            "--symbols", symbol, "--from", str(date_str), "--to", str(date_str),
        ]
        try:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
        except Exception:
            return False
        return self.has_minutes(symbol, date_str)

    # ---- snapshot / screener / universe / news
    def _latest_session_on_or_before(self, now_ts):
        row = self._conn().execute(
            "SELECT date, open_utc, close_utc FROM sessions WHERE open_utc <= ? ORDER BY open_utc DESC LIMIT 1",
            (now_ts,),
        ).fetchone()
        return row

    def snapshot(self, symbols, now_utc):
        """As-of snapshot from the finest finished bars. Missing symbols are omitted."""
        now_ts = to_epoch(now_utc)
        now_dt = from_epoch(now_ts)
        conn = self._conn()
        out = {}
        sess = self._latest_session_on_or_before(now_ts)

        for sym in dict.fromkeys(s for s in (symbols or ()) if isinstance(s, str) and s):
            is_crypto = "/" in sym
            if is_crypto:
                day_start = int(dt.datetime(now_dt.year, now_dt.month, now_dt.day, tzinfo=UTC).timestamp())
                day_date = now_dt.strftime("%Y-%m-%d")
            else:
                if sess:
                    day_date, day_start = sess[0], sess[1]
                else:
                    ny_d = now_dt.astimezone(NY)
                    day_date = ny_d.strftime("%Y-%m-%d")
                    day_start = int(dt.datetime(ny_d.year, ny_d.month, ny_d.day, tzinfo=NY).astimezone(UTC).timestamp())

            # Choose finest finished bar: 1Min if minutes exist for this symbol and day, else 30Min, else 1Day
            chosen_tf, last_row = None, None
            if self.has_minutes(sym, day_date):
                r1 = conn.execute(
                    "SELECT t, o, h, l, c, v FROM bars WHERE symbol = ? AND tf = '1Min' AND t <= ? ORDER BY t DESC LIMIT 1",
                    (sym, now_ts - 60),
                ).fetchone()
                if r1:
                    chosen_tf, last_row = "1Min", r1
            if last_row is None:
                r30 = conn.execute(
                    "SELECT t, o, h, l, c, v FROM bars WHERE symbol = ? AND tf = '30Min' AND t <= ? ORDER BY t DESC LIMIT 1",
                    (sym, now_ts - 1800),
                ).fetchone()
                if r30:
                    chosen_tf, last_row = "30Min", r30
            if last_row is None:
                # Fall back to any earlier finished 1Min bar if present (e.g. crypto with only 1Min recorded)
                r1_any = conn.execute(
                    "SELECT t, o, h, l, c, v FROM bars WHERE symbol = ? AND tf = '1Min' AND t <= ? ORDER BY t DESC LIMIT 1",
                    (sym, now_ts - 60),
                ).fetchone()
                if r1_any:
                    chosen_tf, last_row = "1Min", r1_any
            if last_row is None:
                daily = self.bars(sym, "1Day", 0, now_ts, limit=1)
                if not daily:
                    continue
                db = daily[-1]
                t_ep = to_epoch(db["t"])
                end_dt = from_epoch(self._bar_end_epoch(sym, "1Day", t_ep))
                bar_date = (from_epoch(t_ep) if is_crypto else from_epoch(t_ep).astimezone(NY)).strftime("%Y-%m-%d")
                if bar_date == day_date:
                    prev_daily = self.bars(sym, "1Day", 0, now_ts, limit=2)
                    prev_c = prev_daily[0]["c"] if len(prev_daily) == 2 else None
                    out[sym] = {
                        "price": db["c"], "t": end_dt, "prev_close": prev_c,
                        "day_open": db["o"], "day_high": db["h"], "day_low": db["l"], "day_volume": db["v"],
                    }
                else:
                    out[sym] = {
                        "price": db["c"], "t": end_dt, "prev_close": db["c"],
                        "day_open": None, "day_high": None, "day_low": None, "day_volume": None,
                    }
                continue

            bar_end = from_epoch(last_row[0] + TF_SECS[chosen_tf])
            # Aggregate current day OHLCV from finished bars of chosen_tf >= day_start
            day_rows = conn.execute(
                "SELECT o, h, l, c, v FROM bars WHERE symbol = ? AND tf = ? AND t >= ? AND t <= ? ORDER BY t ASC",
                (sym, chosen_tf, day_start, now_ts - TF_SECS[chosen_tf]),
            ).fetchall()
            if day_rows:
                day_open = day_rows[0][0]
                day_high = max(r[1] for r in day_rows)
                day_low = min(r[2] for r in day_rows)
                day_vol = sum(r[4] for r in day_rows)
            else:
                day_open = day_high = day_low = day_vol = None

            # prev_close: latest finished 1Day bar strictly before day_date
            day_lo, _ = _day_bounds(sym, day_date)
            prev_row = conn.execute(
                "SELECT t, c FROM bars WHERE symbol = ? AND tf = '1Day' AND t < ? ORDER BY t DESC LIMIT 1",
                (sym, day_lo),
            ).fetchone()
            prev_close = None
            if prev_row and self._bar_end_epoch(sym, "1Day", prev_row[0]) <= now_ts:
                prev_close = prev_row[1]

            out[sym] = {
                "price": last_row[4], "t": bar_end, "prev_close": prev_close,
                "day_open": day_open, "day_high": day_high, "day_low": day_low, "day_volume": day_vol,
            }
        return out

    def universe(self, date_str):
        rows = self._conn().execute(
            "SELECT symbol FROM universe WHERE date = ? ORDER BY symbol ASC",
            (str(date_str),),
        ).fetchall()
        return [r[0] for r in rows]

    def _active_universe_date(self, now_ts):
        ny_date = from_epoch(now_ts).astimezone(NY).strftime("%Y-%m-%d")
        row = self._conn().execute(
            "SELECT date FROM universe WHERE date <= ? ORDER BY date DESC LIMIT 1",
            (ny_date,),
        ).fetchone()
        return row[0] if row else ny_date

    def _crypto_symbols_as_of(self, now_ts):
        # the first bar of each pair, read once and kept for five minutes: the same answer as asking the table every time, far faster
        c = getattr(self, "_first_crypto", None)
        if c is None or time.time() - c[0] > 300:
            rows = self._conn().execute("SELECT symbol, MIN(t) FROM bars WHERE symbol LIKE '%/%' GROUP BY symbol ORDER BY symbol ASC").fetchall()
            c = self._first_crypto = (time.time(), [(r[0], r[1]) for r in rows])
        return [sym for sym, t0 in c[1] if t0 <= now_ts - 60]

    def movers(self, now_utc, top=20, market="stocks"):
        now_ts = to_epoch(now_utc)
        syms = self._crypto_symbols_as_of(now_ts) if market == "crypto" else self.universe(self._active_universe_date(now_ts))
        snaps = self.snapshot(syms, now_ts)
        scored = []
        for sym, s in snaps.items():
            pc = s.get("prev_close")
            if pc and pc > 0:
                chg = s["price"] - pc
                pct = (s["price"] / pc - 1.0) * 100.0
                scored.append({"symbol": sym, "price": s["price"], "change": chg, "percent_change": pct})
        gainers = sorted([x for x in scored if x["percent_change"] > 0], key=lambda x: (-x["percent_change"], x["symbol"]))[:top]
        losers = sorted([x for x in scored if x["percent_change"] < 0], key=lambda x: (x["percent_change"], x["symbol"]))[:top]
        return {"gainers": gainers, "losers": losers}

    def most_active(self, now_utc, top=20, by="volume"):
        now_ts = to_epoch(now_utc)
        syms = self.universe(self._active_universe_date(now_ts))
        snaps = self.snapshot(syms, now_ts)
        rows = [
            {"symbol": sym, "volume": int(s["day_volume"] or 0), "trade_count": 0}
            for sym, s in snaps.items()
            if s.get("day_volume") is not None
        ]
        rows.sort(key=lambda x: (-x["volume"], x["symbol"]))
        return rows[:top]

    def news(self, now_utc, symbols=None, since_utc=None, limit=50):
        """Newest first, created <= now_utc only. Marks edited_later=True when updated > created."""
        now_ts = to_epoch(now_utc)
        since_ts = to_epoch(since_utc) if since_utc is not None else None
        if since_ts is not None and since_ts > now_ts:
            return []
        cap = max(0, int(limit))
        if cap == 0:
            return []
        conn = self._conn()
        if symbols:
            expanded = []
            for s in symbols:
                if isinstance(s, str) and s.strip():
                    ss = s.strip()
                    expanded.append(ss)
                    if "/" in ss:
                        expanded.append(ss.replace("/", ""))
                    elif len(ss) > 3 and ss.endswith("USD"):
                        expanded.append(ss[:-3] + "/USD")
            sym_list = list(dict.fromkeys(expanded))
            if not sym_list:
                return []
            placeholders = ",".join("?" for _ in sym_list)
            sql = (
                f"SELECT DISTINCT n.id, n.created, n.updated, n.headline, n.summary, n.source, n.url, n.symbols_json "
                f"FROM news n JOIN news_symbols ns ON n.id = ns.id "
                f"WHERE ns.symbol IN ({placeholders}) AND n.created <= ?"
            )
            params = sym_list + [now_ts]
            if since_ts is not None:
                sql += " AND n.created >= ?"
                params.append(since_ts)
            sql += " ORDER BY n.created DESC, n.id DESC LIMIT ?"
            params.append(cap)
            rows = conn.execute(sql, params).fetchall()
        else:
            sql = "SELECT id, created, updated, headline, summary, source, url, symbols_json FROM news WHERE created <= ?"
            params = [now_ts]
            if since_ts is not None:
                sql += " AND created >= ?"
                params.append(since_ts)
            sql += " ORDER BY created DESC, id DESC LIMIT ?"
            params.append(cap)
            rows = conn.execute(sql, params).fetchall()

        out = []
        for nid, created, updated, headline, summary, source, url, syms_json in rows:
            item = {
                "id": nid,
                "created": from_epoch(created),
                "updated": from_epoch(updated),
                "headline": headline,
                "summary": summary,
                "source": source,
                "url": url,
                "symbols": json.loads(syms_json),
            }
            if updated > created:
                item["edited_later"] = True
            out.append(item)
        return out
