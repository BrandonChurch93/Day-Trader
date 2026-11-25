"""Record historical Alpaca market data into the time-machine SQLite tape.

GET-only, plain `urllib` (honours `HTTPS_PROXY`), never sees or reads any API
key. Runs keyless for crypto, or under `pplx credentials run <handle> -- ...`
for stocks and news. Respects `tm_record_max_rpm`, backs off on 429, saves
progress in `meta` so interrupted runs resume cleanly, and logs to stdout.

Commands:
  sessions  --from D --to D
  daily     --from D --to D
  universe  --from D --to D
  halfhours --from D --to D
  minutes     --symbols A,B --from D --to D
  news        --from D --to D
  crypto      --symbols BTC/USD,ETH/USD --from D --to D [--tf both|1Day|1Min]
  crypto-news --from D --to D [--sources cryptoslate,cryptopotato,newsbtc]
  load-csv    --tf 1Min|1Day (--file PATH --symbol SYM | --dir PATH) [--from D] [--to D]
  sessions-from-tape [--symbol SPY] --from D --to D
  stock-news  --symbols A,B --from D --to D [--sources sec_edgar,finbold]
"""
import argparse, csv, datetime as dt, hashlib, html, json, math, re, statistics, sys, time
import urllib.error, urllib.parse, urllib.request
from pathlib import Path

try:
    from .tape import NY, UTC, Tape, from_epoch, to_epoch, to_utc_dt
except ImportError:
    from tape import NY, UTC, Tape, from_epoch, to_epoch, to_utc_dt

ROOT = Path(__file__).resolve().parent.parent
DATA = "https://data.alpaca.markets"
NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqtraded.txt"
USER_AGENT = "Day-Trader research modernsoftworks@gmail.com"

KEYLESS_CRYPTO_NEWS_SOURCES = {
    "cryptoslate": "https://cryptoslate.com/wp-json/wp/v2/posts",
    "cryptopotato": "https://cryptopotato.com/wp-json/wp/v2/posts",
    "newsbtc": "https://www.newsbtc.com/wp-json/wp/v2/posts",
}

TM_KEYS = [
    "tm_daily_lookback_days",
    "tm_universe_min_price",
    "tm_universe_min_dollar_volume",
    "tm_universe_lookback_days",
    "tm_record_max_rpm",
    "tm_record_batch_size",
    "tm_keyless_news_max_rpm",
    "tm_keyless_news_per_page",
    "tm_sec_edgar_max_rpm",
]

SEC_USER_AGENT = "Day-Trader research modernsoftworks@gmail.com"
SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
FINBOLD_WP_BASE = "https://finbold.com/wp-json/wp/v2/posts"


def config(path=ROOT / "config" / "thresholds.yaml"):
    out, key = {}, None
    with open(path) as f:
        for line in f:
            m = re.match(r"^([a-z0-9_]+):\s*$", line)
            if m:
                key = m.group(1)
                continue
            m = re.match(r"^  value:\s*(.*)$", line)
            if m and key in TM_KEYS:
                out[key] = json.loads(m.group(1).strip())
    missing = [k for k in TM_KEYS if k not in out]
    if missing:
        raise KeyError(f"missing tm_ config keys: {missing}")
    return out


class HttpError(Exception):
    def __init__(self, code, body="", headers=None):
        super().__init__(f"HTTP {code}: {body[:200]}")
        self.code = code
        self.body = body
        self.headers = headers or {}


def default_http_get(url, timeout=30, user_agent=None):
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": user_agent or USER_AGENT},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise HttpError(e.code, body, dict(e.headers) if e.headers else {})


class Client:
    """Rate-limited GET-only HTTP client with 429/5xx backoff."""

    def __init__(self, max_rpm=150, http_get=None, sleep_fn=None, now_fn=None, max_retries=5, user_agent=None):
        self.min_interval = 60.0 / max(1.0, float(max_rpm))
        if http_get is not None:
            self.http_get = http_get
        elif user_agent is not None:
            self.http_get = lambda url: default_http_get(url, user_agent=user_agent)
        else:
            self.http_get = default_http_get
        self.sleep_fn = sleep_fn or time.sleep
        self.now_fn = now_fn or time.monotonic
        self.max_retries = max_retries
        self._last_req = 0.0
        self.requests_made = 0

    def _pace(self):
        if self._last_req > 0:
            gap = self.min_interval - (self.now_fn() - self._last_req)
            if gap > 0:
                self.sleep_fn(gap)
        self._last_req = self.now_fn()

    def get_text_with_headers(self, url):
        for attempt in range(self.max_retries + 1):
            self._pace()
            self.requests_made += 1
            try:
                status, body, headers = self.http_get(url)
                return body, headers
            except HttpError as e:
                if e.code == 429 or 500 <= e.code < 600:
                    if attempt >= self.max_retries:
                        raise
                    ra = e.headers.get("Retry-After") or e.headers.get("retry-after")
                    wait = float(ra) if ra and str(ra).replace(".", "", 1).isdigit() else (2.0 ** (attempt + 1))
                    print(f"[record] HTTP {e.code} on {url[:80]}... backing off {wait:.1f}s (attempt {attempt + 1})", flush=True)
                    self.sleep_fn(wait)
                    continue
                raise
        raise RuntimeError("unreachable")

    def get_text(self, url):
        body, _ = self.get_text_with_headers(url)
        return body

    def get_json_with_headers(self, base, path, params=None):
        q = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None})
        url = f"{base}{path}" + (f"?{q}" if q else "")
        body, headers = self.get_text_with_headers(url)
        return json.loads(body), headers

    def get_json(self, base, path, params=None):
        data, _ = self.get_json_with_headers(base, path, params)
        return data


def _parse_date(s):
    return dt.date.fromisoformat(s[:10])


def _date_chunks(start_d, end_d, days_per_chunk):
    cur = start_d
    while cur <= end_d:
        nxt = min(end_d, cur + dt.timedelta(days=days_per_chunk - 1))
        yield cur, nxt
        cur = nxt + dt.timedelta(days=1)


def _fetch_stock_bars_paged(client, symbols, tf, start_iso, end_iso, tape, preferred_feed="sip"):
    """Fetch stock bars with feed=sip fallback to feed=iex on 403; record feed in meta."""
    feed = tape.get_meta("stock_feed") or preferred_feed
    bars_by_sym = {}
    token = None
    while True:
        params = {
            "symbols": ",".join(symbols),
            "timeframe": tf,
            "start": start_iso,
            "end": end_iso,
            "adjustment": "raw",
            "feed": feed,
            "limit": 10000,
            "sort": "asc",
        }
        if token:
            params["page_token"] = token
        try:
            data = client.get_json(DATA, "/v2/stocks/bars", params)
        except HttpError as e:
            if e.code == 403 and feed == "sip":
                print("[record] feed=sip returned 403; falling back to feed=iex", flush=True)
                feed = "iex"
                tape.set_meta("stock_feed", "iex")
                token = None
                bars_by_sym = {}
                continue
            raise
        if tape.get_meta("stock_feed") != feed:
            tape.set_meta("stock_feed", feed)
        for sym, blist in (data.get("bars") or {}).items():
            bars_by_sym.setdefault(sym, []).extend(blist)
        token = data.get("next_page_token")
        if not token:
            break
    return bars_by_sym, feed


def _fetch_crypto_bars_paged(client, symbols, tf, start_iso, end_iso):
    bars_by_sym = {}
    token = None
    while True:
        params = {
            "symbols": ",".join(symbols),
            "timeframe": tf,
            "start": start_iso,
            "end": end_iso,
            "limit": 10000,
            "sort": "asc",
        }
        if token:
            params["page_token"] = token
        data = client.get_json(DATA, "/v1beta3/crypto/us/bars", params)
        for sym, blist in (data.get("bars") or {}).items():
            bars_by_sym.setdefault(sym, []).extend(blist)
        token = data.get("next_page_token")
        if not token:
            break
    return bars_by_sym


def _rows_from_bars_dict(bars_by_sym, tf):
    rows = []
    for sym, blist in bars_by_sym.items():
        for b in blist:
            rows.append((sym, tf, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"]))
    return rows


def parse_nasdaq_symbols(text):
    """Parse Nasdaq Trader nasdaqtraded.txt into a sorted list of non-test symbols."""
    syms = []
    for i, line in enumerate(text.splitlines()):
        if i == 0 or not line.strip() or line.startswith("File Creation Time"):
            continue
        parts = line.split("|")
        if len(parts) < 8:
            continue
        sym = parts[1].strip()
        test_issue = parts[7].strip().upper()
        if not sym or test_issue == "Y":
            continue
        # Keep standard ticker characters (letters, digits, dot, hyphen)
        if not re.fullmatch(r"[A-Za-z0-9.\-]+", sym):
            continue
        syms.append(sym)
    return sorted(set(syms))


def record_sessions(tape, client, start_d, end_d):
    """Derive NYSE regular sessions from SPY 1Min bars (first & last regular-hours bar)."""
    sd, ed = _parse_date(start_d), _parse_date(end_d)
    total_sessions = 0
    for c_start, c_end in _date_chunks(sd, ed, 14):
        meta_key = f"sessions_done:{c_start.isoformat()}:{c_end.isoformat()}"
        if tape.get_meta(meta_key):
            print(f"[sessions] skip completed chunk {c_start}..{c_end}", flush=True)
            continue
        start_iso = f"{c_start.isoformat()}T00:00:00Z"
        end_iso = f"{c_end.isoformat()}T23:59:59Z"
        bars_by_sym, feed = _fetch_stock_bars_paged(client, ["SPY"], "1Min", start_iso, end_iso, tape)
        spy_bars = bars_by_sym.get("SPY", [])
        by_day = {}
        for b in spy_bars:
            t_utc = to_utc_dt(b["t"])
            t_ny = t_utc.astimezone(NY)
            hm = (t_ny.hour, t_ny.minute)
            if (9, 30) <= hm < (16, 0):
                d_str = t_ny.strftime("%Y-%m-%d")
                ep = to_epoch(t_utc)
                if d_str not in by_day:
                    by_day[d_str] = [ep, ep]
                else:
                    if ep < by_day[d_str][0]:
                        by_day[d_str][0] = ep
                    if ep > by_day[d_str][1]:
                        by_day[d_str][1] = ep
        sess_rows = [(d, o, c + 60) for d, (o, c) in sorted(by_day.items())]
        n = tape.add_sessions(sess_rows)
        total_sessions += n
        tape.set_meta(meta_key, str(n))
        print(f"[sessions] {c_start}..{c_end} ({feed}): {n} sessions", flush=True)
    return total_sessions


def record_daily(tape, client, start_d, end_d, cfg, symbols=None):
    """Record 1Day raw bars for Nasdaq Trader equities + tm_daily_lookback_days prior."""
    sd, ed = _parse_date(start_d), _parse_date(end_d)
    lookback = int(cfg["tm_daily_lookback_days"])
    fetch_start = sd - dt.timedelta(days=lookback)
    if symbols is None:
        print(f"[daily] fetching Nasdaq Trader symbol list from {NASDAQ_URL}", flush=True)
        symbols = parse_nasdaq_symbols(client.get_text(NASDAQ_URL))
        print(f"[daily] {len(symbols)} symbols loaded", flush=True)
    batch_size = int(cfg["tm_record_batch_size"])
    start_iso = f"{fetch_start.isoformat()}T00:00:00Z"
    end_iso = f"{ed.isoformat()}T23:59:59Z"
    total_bars = 0
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        meta_key = f"daily_done:{fetch_start.isoformat()}:{ed.isoformat()}:{i}:{batch[0]}:{batch[-1]}"
        if tape.get_meta(meta_key):
            continue
        bars_by_sym, feed = _fetch_stock_bars_paged(client, batch, "1Day", start_iso, end_iso, tape)
        rows = _rows_from_bars_dict(bars_by_sym, "1Day")
        n = tape.add_bars(rows)
        total_bars += n
        tape.set_meta(meta_key, str(n))
        print(f"[daily] batch {i // batch_size + 1}/{(len(symbols) + batch_size - 1) // batch_size} ({feed}): +{n} bars", flush=True)
    return total_bars


def record_universe(tape, start_d, end_d, cfg):
    """Compute liquid universe per session date using ONLY 1Day bars strictly before each date."""
    min_price = float(cfg["tm_universe_min_price"])
    min_dv = float(cfg["tm_universe_min_dollar_volume"])
    lookback = int(cfg["tm_universe_lookback_days"])
    sess_list = tape.sessions(start_d, end_d)
    if not sess_list:
        print(f"[universe] no sessions in tape for {start_d}..{end_d}", flush=True)
        return 0
    # Load all stock 1Day bars once into memory (sorted by t ascending) for fast, strictly-before slicing
    conn = tape._conn()
    all_rows = conn.execute(
        "SELECT symbol, t, c, v FROM bars WHERE tf='1Day' AND symbol NOT LIKE '%/%' ORDER BY symbol, t ASC"
    ).fetchall()
    by_sym = {}
    for sym, t_ep, c, v in all_rows:
        d_str = from_epoch(t_ep).astimezone(NY).strftime("%Y-%m-%d")
        by_sym.setdefault(sym, []).append((d_str, c, c * v))

    total_entries = 0
    for sess_date, _, _ in sess_list:
        chosen = []
        for sym, series in by_sym.items():
            # Strictly before sess_date (no look-ahead)
            prior = [x for x in series if x[0] < sess_date]
            if not prior:
                continue
            window = prior[-lookback:]
            prior_close = window[-1][1]
            med_dv = statistics.median(x[2] for x in window)
            if prior_close >= min_price and med_dv >= min_dv:
                chosen.append(sym)
        n = tape.add_universe(sess_date, chosen)
        total_entries += n
        print(f"[universe] {sess_date}: {n} symbols", flush=True)
    return total_entries


def record_halfhours(tape, client, start_d, end_d, cfg):
    """Record 30Min raw bars for the computed universe in [start_d, end_d]."""
    sd, ed = _parse_date(start_d), _parse_date(end_d)
    sess_list = tape.sessions(start_d, end_d)
    syms = sorted({s for d, _, _ in sess_list for s in tape.universe(d)})
    if not syms:
        print(f"[halfhours] empty universe for {start_d}..{end_d}", flush=True)
        return 0
    batch_size = int(cfg["tm_record_batch_size"])
    total_bars = 0
    for c_start, c_end in _date_chunks(sd, ed, 14):
        start_iso = f"{c_start.isoformat()}T00:00:00Z"
        end_iso = f"{c_end.isoformat()}T23:59:59Z"
        for i in range(0, len(syms), batch_size):
            batch = syms[i : i + batch_size]
            meta_key = f"halfhours_done:{c_start.isoformat()}:{c_end.isoformat()}:{i}:{batch[0]}:{batch[-1]}"
            if tape.get_meta(meta_key):
                continue
            bars_by_sym, feed = _fetch_stock_bars_paged(client, batch, "30Min", start_iso, end_iso, tape)
            rows = _rows_from_bars_dict(bars_by_sym, "30Min")
            n = tape.add_bars(rows)
            total_bars += n
            tape.set_meta(meta_key, str(n))
            print(f"[halfhours] {c_start}..{c_end} batch {i // batch_size + 1} ({feed}): +{n} bars", flush=True)
    return total_bars


def record_minutes(tape, client, symbols, start_d, end_d, cfg):
    """Record 1Min raw bars for specific stock symbols."""
    sd, ed = _parse_date(start_d), _parse_date(end_d)
    batch_size = min(20, int(cfg["tm_record_batch_size"]))
    total_bars = 0
    for c_start, c_end in _date_chunks(sd, ed, 7):
        start_iso = f"{c_start.isoformat()}T00:00:00Z"
        end_iso = f"{c_end.isoformat()}T23:59:59Z"
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            meta_key = f"minutes_done:{c_start.isoformat()}:{c_end.isoformat()}:{','.join(batch)}"
            if tape.get_meta(meta_key):
                continue
            bars_by_sym, feed = _fetch_stock_bars_paged(client, batch, "1Min", start_iso, end_iso, tape)
            rows = _rows_from_bars_dict(bars_by_sym, "1Min")
            n = tape.add_bars(rows)
            total_bars += n
            tape.set_meta(meta_key, str(n))
            print(f"[minutes] {c_start}..{c_end} {','.join(batch)} ({feed}): +{n} bars", flush=True)
    return total_bars


def record_news(tape, client, start_d, end_d):
    """Record Alpaca news headlines & summaries (include_content=false)."""
    sd, ed = _parse_date(start_d), _parse_date(end_d)
    total_articles = 0
    for c_start, c_end in _date_chunks(sd, ed, 7):
        meta_key = f"news_done:{c_start.isoformat()}:{c_end.isoformat()}"
        if tape.get_meta(meta_key):
            print(f"[news] skip completed chunk {c_start}..{c_end}", flush=True)
            continue
        start_iso = f"{c_start.isoformat()}T00:00:00Z"
        end_iso = f"{c_end.isoformat()}T23:59:59Z"
        token = None
        chunk_count = 0
        while True:
            params = {
                "start": start_iso,
                "end": end_iso,
                "limit": 50,
                "sort": "asc",
                "include_content": "false",
            }
            if token:
                params["page_token"] = token
            data = client.get_json(DATA, "/v1beta1/news", params)
            articles = data.get("news") or []
            if articles:
                chunk_count += tape.add_news(articles)
            token = data.get("next_page_token")
            if not token:
                break
        total_articles += chunk_count
        tape.set_meta(meta_key, str(chunk_count))
        print(f"[news] {c_start}..{c_end}: +{chunk_count} articles", flush=True)
    return total_articles


def record_crypto(tape, client, symbols, start_d, end_d, tf="both"):
    """Record 1Day and/or 1Min crypto bars (keyless)."""
    sd, ed = _parse_date(start_d), _parse_date(end_d)
    total_bars = 0

    if tf in ("both", "1Day"):
        # 1Day bars across full range (one request per symbol batch)
        day_key = f"crypto_1Day:{sd.isoformat()}:{ed.isoformat()}:{','.join(symbols)}"
        if not tape.get_meta(day_key):
            bars_by_sym = _fetch_crypto_bars_paged(
                client, symbols, "1Day", f"{sd.isoformat()}T00:00:00Z", f"{ed.isoformat()}T23:59:59Z"
            )
            n = tape.add_bars(_rows_from_bars_dict(bars_by_sym, "1Day"))
            total_bars += n
            tape.set_meta(day_key, str(n))
            print(f"[crypto 1Day] {sd}..{ed} ({len(symbols)} pairs): +{n} bars", flush=True)
        else:
            print(f"[crypto 1Day] skip completed {sd}..{ed}", flush=True)

    if tf in ("both", "1Min"):
        # 1Min bars in 7-day chunks per batch of up to 5 pairs (keeps pages small & resumable)
        for c_start, c_end in _date_chunks(sd, ed, 7):
            start_iso = f"{c_start.isoformat()}T00:00:00Z"
            end_iso = f"{c_end.isoformat()}T23:59:59Z"
            for i in range(0, len(symbols), 5):
                batch = symbols[i : i + 5]
                meta_key = f"crypto_1Min:{c_start.isoformat()}:{c_end.isoformat()}:{','.join(batch)}"
                if tape.get_meta(meta_key):
                    continue
                bars_by_sym = _fetch_crypto_bars_paged(client, batch, "1Min", start_iso, end_iso)
                n = tape.add_bars(_rows_from_bars_dict(bars_by_sym, "1Min"))
                total_bars += n
                tape.set_meta(meta_key, str(n))
                print(f"[crypto 1Min] {c_start}..{c_end} {','.join(batch)}: +{n} bars", flush=True)
    return total_bars


_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_CRYPTO_PATTERNS = [
    ("BTC/USD", re.compile(r"\b(bitcoin|btc)\b", re.I)),
    ("ETH/USD", re.compile(r"\b(ethereum|ether|eth)\b", re.I)),
    ("SOL/USD", re.compile(r"\b(solana|sol)\b", re.I)),
    ("XRP/USD", re.compile(r"\b(xrp|ripple)\b", re.I)),
    ("DOGE/USD", re.compile(r"\b(dogecoin|doge)\b", re.I)),
    ("AVAX/USD", re.compile(r"\b(avalanche|avax)\b", re.I)),
    ("LINK/USD", re.compile(r"\bchainlink\b", re.I)),
    ("LTC/USD", re.compile(r"\b(litecoin|ltc)\b", re.I)),
]
_LINK_TICKER_RE = re.compile(r"\bLINK\b")
_GENERAL_CRYPTO_RE = re.compile(
    r"\b(crypto|cryptocurrency|cryptocurrencies|altcoin|altcoins|defi|stablecoin|stablecoins|"
    r"blockchain|web3|memecoin|memecoins|binance|coinbase|kraken|sec|etf|etfs|fomc|fed|"
    r"digital asset|digital assets|crypto market)\b",
    re.I,
)


def _clean_html(text):
    if not text:
        return ""
    s = html.unescape(_TAG_RE.sub(" ", str(text)))
    return _SPACE_RE.sub(" ", s).strip()


def _match_crypto_symbols(headline, summary):
    blob = f"{headline} {summary}"
    syms = []
    for sym, pat in _CRYPTO_PATTERNS:
        if pat.search(blob):
            syms.append(sym)
    if "LINK/USD" not in syms and _LINK_TICKER_RE.search(blob):
        syms.append("LINK/USD")
    if syms:
        return syms
    if _GENERAL_CRYPTO_RE.search(blob):
        return ["CRYPTO"]
    return []


def _keyless_news_id(source, url):
    digest = hashlib.sha256(f"{source}:{url}".encode("utf-8")).digest()
    return (1 << 60) | (int.from_bytes(digest[:8], "big") & ((1 << 60) - 1))


def _ensure_utc_iso(s):
    if not s:
        return None
    s = str(s).strip()
    if s.endswith("Z") or re.search(r"[+-]\d{2}:\d{2}$", s):
        return s
    return s + "Z"


def record_crypto_news(tape, client, start_d, end_d, cfg, sources=None):
    """Record keyless dated crypto headlines from public WordPress REST endpoints."""
    sd, ed = _parse_date(start_d), _parse_date(end_d)
    per_page = int(cfg["tm_keyless_news_per_page"])
    chosen = list(sources) if sources else list(KEYLESS_CRYPTO_NEWS_SOURCES.keys())
    unknown = [s for s in chosen if s not in KEYLESS_CRYPTO_NEWS_SOURCES]
    if unknown:
        raise ValueError(f"unknown keyless crypto news sources: {unknown}")

    total_articles = 0
    for src in chosen:
        endpoint = KEYLESS_CRYPTO_NEWS_SOURCES[src]
        for c_start, c_end in _date_chunks(sd, ed, 14):
            meta_key = f"crypto_news_done:{src}:{c_start.isoformat()}:{c_end.isoformat()}"
            if tape.get_meta(meta_key):
                print(f"[crypto-news:{src}] skip completed chunk {c_start}..{c_end}", flush=True)
                continue
            after_iso = f"{c_start.isoformat()}T00:00:00Z"
            before_iso = f"{c_end.isoformat()}T23:59:59Z"
            page = 1
            chunk_articles = []
            while True:
                params = {
                    "after": after_iso,
                    "before": before_iso,
                    "per_page": per_page,
                    "page": page,
                    "orderby": "date",
                    "order": "asc",
                    "_fields": "id,date_gmt,modified_gmt,link,title,excerpt",
                }
                try:
                    posts, headers = client.get_json_with_headers(endpoint, "", params)
                except HttpError as e:
                    if e.code == 400 and "rest_post_invalid_page_number" in e.body:
                        break
                    raise
                if not isinstance(posts, list) or not posts:
                    break
                for p in posts:
                    created_iso = _ensure_utc_iso(p.get("date_gmt"))
                    if not created_iso:
                        continue
                    mod_iso = _ensure_utc_iso(p.get("modified_gmt")) or created_iso
                    c_ep, m_ep = to_epoch(created_iso), to_epoch(mod_iso)
                    # Scheduled posts often have modified_gmt <= date_gmt; only mark edited_later when modified > published
                    upd_iso = mod_iso if m_ep > c_ep else created_iso
                    headline = _clean_html((p.get("title") or {}).get("rendered"))
                    summary = _clean_html((p.get("excerpt") or {}).get("rendered"))
                    url = str(p.get("link") or "").strip()
                    if not headline or not url:
                        continue
                    syms = _match_crypto_symbols(headline, summary)
                    if not syms:
                        continue
                    chunk_articles.append({
                        "id": _keyless_news_id(src, url),
                        "created_at": created_iso,
                        "updated_at": upd_iso,
                        "headline": headline,
                        "summary": summary[:600],
                        "source": src,
                        "url": url,
                        "symbols": syms,
                    })
                total_pages_hdr = headers.get("X-WP-TotalPages") or headers.get("x-wp-totalpages")
                if total_pages_hdr and str(total_pages_hdr).isdigit():
                    if page >= int(total_pages_hdr):
                        break
                elif len(posts) < per_page:
                    break
                page += 1

            n = tape.add_news(chunk_articles) if chunk_articles else 0
            total_articles += n
            tape.set_meta(meta_key, str(n))
            print(f"[crypto-news:{src}] {c_start}..{c_end}: +{n} articles", flush=True)
    return total_articles


def _parse_csv_bar_ts(raw_date, tf, symbol):
    """Parse platform_bars CSV `date` column into UTC epoch seconds.

    - 1Day stock (`YYYY-MM-DD`): midnight America/New_York converted to UTC so
      `from_epoch(t).astimezone(NY).strftime('%Y-%m-%d') == YYYY-MM-DD`.
    - 1Min (`YYYY-MM-DDTHH:MM:SS` or with `Z`): UTC timestamp.
    """
    s = str(raw_date or "").strip()
    if not s:
        return None
    if tf == "1Day" and len(s) == 10 and "/" not in symbol:
        y, mo, d = (int(x) for x in s.split("-"))
        return int(dt.datetime(y, mo, d, 0, 0, 0, tzinfo=NY).astimezone(UTC).timestamp())
    return to_epoch(_ensure_utc_iso(s))


def load_csv_file(tape, path, symbol, tf, start_d=None, end_d=None):
    """Load stock bars from one platform_bars CSV file into the tape (WAL-safe)."""
    p = Path(path)
    sd = _parse_date(start_d) if start_d else None
    ed = _parse_date(end_d) if end_d else None
    rows = []
    with open(p, newline="") as f:
        rdr = csv.DictReader(f)
        required = {"date", "open", "high", "low", "close", "volume"}
        if not rdr.fieldnames or not required.issubset(set(rdr.fieldnames)):
            return 0
        for rec in rdr:
            raw_d = (rec.get("date") or "").strip()
            if not raw_d:
                continue
            try:
                day = dt.date.fromisoformat(raw_d[:10])
            except ValueError:
                continue
            if sd and day < sd:
                continue
            if ed and day > ed:
                continue
            try:
                o = float(rec["open"])
                h = float(rec["high"])
                l = float(rec["low"])
                c = float(rec["close"])
                v = float(rec["volume"])
            except (TypeError, ValueError):
                continue
            if not all(math.isfinite(x) for x in (o, h, l, c, v)):
                continue
            if o <= 0 or h <= 0 or l <= 0 or c <= 0 or v < 0 or h < l:
                continue
            ts = _parse_csv_bar_ts(raw_d, tf, symbol)
            if ts is None:
                continue
            rows.append((symbol, tf, ts, o, h, l, c, v))
    if not rows:
        return 0
    return tape.add_bars(rows)


def load_csv_dir(tape, directory, tf, start_d=None, end_d=None, symbols=None):
    """Load all matching platform_bars CSV files in `directory` into the tape."""
    dpath = Path(directory)
    want = set(symbols) if symbols else None
    total = 0
    for fpath in sorted(dpath.glob("*.csv")):
        sym = fpath.name.split("_", 1)[0].upper()
        if not sym or (want and sym not in want):
            continue
        n = load_csv_file(tape, fpath, sym, tf, start_d=start_d, end_d=end_d)
        if n:
            total += n
            print(f"[load-csv:{tf}] {fpath.name} ({sym}): +{n} bars", flush=True)
    return total


def derive_sessions_from_tape(tape, start_d, end_d, symbol="SPY"):
    """Derive NYSE regular sessions (open_utc, close_utc) from already-loaded 1Min bars."""
    sd, ed = _parse_date(start_d), _parse_date(end_d)
    start_ts = int(dt.datetime(sd.year, sd.month, sd.day, 0, 0, 0, tzinfo=NY).astimezone(UTC).timestamp())
    end_ts = int(dt.datetime(ed.year, ed.month, ed.day, 23, 59, 59, tzinfo=NY).astimezone(UTC).timestamp())
    rows = tape._conn().execute(
        "SELECT t FROM bars WHERE symbol = ? AND tf = '1Min' AND t >= ? AND t <= ? ORDER BY t ASC",
        (symbol, start_ts, end_ts),
    ).fetchall()
    by_day = {}
    for (ep,) in rows:
        t_ny = from_epoch(ep).astimezone(NY)
        hm = (t_ny.hour, t_ny.minute)
        if (9, 30) <= hm < (16, 0):
            d_str = t_ny.strftime("%Y-%m-%d")
            if d_str not in by_day:
                by_day[d_str] = [ep, ep]
            else:
                if ep < by_day[d_str][0]:
                    by_day[d_str][0] = ep
                if ep > by_day[d_str][1]:
                    by_day[d_str][1] = ep
    sess_rows = [(d, o, c + 60) for d, (o, c) in sorted(by_day.items())]
    n = tape.add_sessions(sess_rows)
    print(f"[sessions-from-tape:{symbol}] {sd}..{ed}: {n} sessions", flush=True)
    return n


SEC_8K_ITEM_NAMES = {
    "1.01": "Material Agreement",
    "1.02": "Termination of Material Agreement",
    "1.05": "Cybersecurity Incident",
    "2.01": "Acquisition/Disposition",
    "2.02": "Results of Operations",
    "2.03": "Direct Financial Obligation",
    "2.05": "Exit/Disposal Costs",
    "2.06": "Material Impairments",
    "3.02": "Unregistered Equity Sales",
    "4.01": "Auditor Change",
    "4.02": "Non-Reliance on Financials",
    "5.02": "Officer/Director Changes",
    "5.03": "Bylaws/Charter Amendments",
    "5.07": "Shareholder Vote",
    "7.01": "Reg FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Exhibits",
}

STOCK_NAME_KEYWORDS = {
    "AAPL": ("apple",),
    "AMD": ("advanced micro devices",),
    "AMGN": ("amgen",),
    "AMZN": ("amazon",),
    "AVGO": ("broadcom",),
    "AXP": ("american express",),
    "BA": ("boeing",),
    "CAT": ("caterpillar",),
    "COIN": ("coinbase",),
    "CRM": ("salesforce",),
    "CSCO": ("cisco",),
    "CVX": ("chevron",),
    "DIS": ("disney", "walt disney"),
    "GOOGL": ("alphabet", "google"),
    "GS": ("goldman sachs",),
    "HD": ("home depot",),
    "HON": ("honeywell",),
    "IBM": ("international business machines",),
    "JNJ": ("johnson & johnson", "johnson and johnson"),
    "JPM": ("jpmorgan", "jp morgan"),
    "KO": ("coca-cola", "coca cola"),
    "MCD": ("mcdonald's", "mcdonalds"),
    "META": ("meta platforms",),
    "MMM": ("3m company",),
    "MRK": ("merck",),
    "MSFT": ("microsoft",),
    "MSTR": ("microstrategy",),
    "NFLX": ("netflix",),
    "NKE": ("nike",),
    "NVDA": ("nvidia",),
    "PG": ("procter & gamble", "procter and gamble"),
    "PLTR": ("palantir",),
    "SHW": ("sherwin-williams", "sherwin williams"),
    "TRV": ("travelers companies",),
    "TSLA": ("tesla",),
    "UNH": ("unitedhealth",),
    "V": ("visa inc",),
    "WMT": ("walmart",),
}


def _format_8k_items(raw_items):
    if isinstance(raw_items, (list, tuple)):
        codes = [str(x).strip() for x in raw_items if str(x).strip()]
    else:
        codes = [x.strip() for x in str(raw_items or "").split(",") if x.strip()]
    if not codes:
        return "unspecified"
    parts = [f"{c} {SEC_8K_ITEM_NAMES[c]}" if c in SEC_8K_ITEM_NAMES else c for c in codes]
    return ", ".join(parts)


SEC_STOCK_FORMS = ("8-K", "8-K/A", "10-Q", "10-Q/A", "10-K", "10-K/A")


def _extract_sec_8k_rows(sym, cik, company_title, block, sd_str, ed_str):
    forms = block.get("form") or []
    accs = block.get("acceptanceDateTime") or []
    items_col = block.get("items") or []
    acc_nums = block.get("accessionNumber") or []
    prim_docs = block.get("primaryDocument") or []
    filing_dates = block.get("filingDate") or []
    report_dates = block.get("reportDate") or []
    out = []
    for i, form in enumerate(forms):
        if form not in SEC_STOCK_FORMS:
            continue
        acc_dt = (accs[i] if i < len(accs) else "") or ""
        if not acc_dt or len(acc_dt) < 10:
            continue
        day_str = acc_dt[:10]
        if day_str < sd_str or day_str > ed_str:
            continue
        ts = to_epoch(_ensure_utc_iso(acc_dt))
        acc_num = acc_nums[i] if i < len(acc_nums) else ""
        prim_doc = prim_docs[i] if i < len(prim_docs) else ""
        acc_nodash = acc_num.replace("-", "")
        rep_date = report_dates[i] if i < len(report_dates) else ""
        is_8k = form in ("8-K", "8-K/A")
        if is_8k:
            if acc_nodash and prim_doc:
                url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{prim_doc}"
            else:
                url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={int(cik):010d}&type=8-K&acc={acc_num}"
            raw_items = items_col[i] if i < len(items_col) else ""
            items_label = _format_8k_items(raw_items)
            headline = f"{sym} Form {form} (Items {items_label}): {company_title}"
            summary = f"SEC EDGAR {form} filed by {company_title} ({sym}), accepted {acc_dt}. Items: {items_label}."
        else:
            if acc_nodash and acc_num:
                url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{acc_num}-index.htm"
            else:
                url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={int(cik):010d}&type={form}&acc={acc_num}"
            raw_items = ""
            period_part = f" (period {rep_date})" if rep_date else ""
            headline = f"{sym} Form {form}{period_part}: {company_title}"
            summary = f"SEC EDGAR {form} accepted {_ensure_utc_iso(acc_dt)}. Filing index: {url}"
        item = {
            "id": _keyless_news_id("sec_edgar", url),
            "headline": headline,
            "summary": summary,
            "source": "sec_edgar",
            "url": url,
            "created_at": _ensure_utc_iso(acc_dt),
            "updated_at": _ensure_utc_iso(acc_dt),
            "symbols": [sym],
            "form": form,
            "items": raw_items,
            "accession_number": acc_num,
            "filing_date": filing_dates[i] if i < len(filing_dates) else "",
            "report_date": rep_date,
            "cik": f"{int(cik):010d}",
        }
        out.append(item)
    return out


def record_sec_news(tape, client, symbols, start_d, end_d, cfg=None):
    """Record dated SEC EDGAR 8-K, 10-Q, and 10-K filings (and amendments) using acceptanceDateTime (UTC to the second)."""
    sd_str, ed_str = _parse_date(start_d).isoformat(), _parse_date(end_d).isoformat()
    tickers_raw = json.loads(client.get_text(SEC_TICKERS_URL))
    by_sym = {}
    for rec in tickers_raw.values():
        t = str(rec.get("ticker") or "").upper()
        if t and t not in by_sym:
            by_sym[t] = (int(rec["cik_str"]), str(rec.get("title") or t))

    total = 0
    for sym in symbols:
        sym_u = sym.upper()
        if sym_u not in by_sym:
            continue
        cik, company_title = by_sym[sym_u]
        sub_url = f"{SEC_SUBMISSIONS_BASE}/CIK{cik:010d}.json"
        try:
            sub = json.loads(client.get_text(sub_url))
        except HttpError as e:
            print(f"[stock-news:sec_edgar] {sym_u} HTTP {e.code} skipped", flush=True)
            continue
        filings = sub.get("filings") or {}
        recent = filings.get("recent") or {}
        rows = _extract_sec_8k_rows(sym_u, cik, company_title, recent, sd_str, ed_str)
        # Follow archive files if recent does not reach back to sd_str
        rec_dates = recent.get("filingDate") or []
        oldest_recent = rec_dates[-1] if rec_dates else "9999-12-31"
        if oldest_recent > sd_str:
            for meta in filings.get("files") or []:
                f_from = str(meta.get("filingFrom") or "")
                f_to = str(meta.get("filingTo") or "")
                fname = meta.get("name") or ""
                if not fname or (f_to and f_to < sd_str) or (f_from and f_from > ed_str):
                    continue
                try:
                    arch = json.loads(client.get_text(f"{SEC_SUBMISSIONS_BASE}/{fname}"))
                except HttpError:
                    continue
                rows.extend(_extract_sec_8k_rows(sym_u, cik, company_title, arch, sd_str, ed_str))
        if rows:
            n = tape.add_news(rows)
            total += n
            print(f"[stock-news:sec_edgar] {sym_u} (CIK {cik:010d}): +{n} 8-K filings", flush=True)
    return total


def _tag_stock_symbols(headline, summary, allowed_symbols):
    """Tag stock/ETF symbols mentioned in headline or summary.

    Uses case-sensitive whole-word ticker matching (excluding ambiguous 1-2 char tickers
    unless prefixed with `$` or parenthesized) plus exact company-name keyword matching.
    """
    text_raw = f"{headline} {summary}"
    text_low = text_raw.lower()
    found = set()
    for sym in allowed_symbols:
        su = sym.upper()
        if len(su) <= 2:
            if re.search(rf"(?:\${re.escape(su)}\b|\({re.escape(su)}\)|\b(?:NYSE|NASDAQ):\s*{re.escape(su)}\b)", text_raw):
                found.add(su)
        else:
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(su)}(?![A-Za-z0-9])", text_raw):
                found.add(su)
        for kw in STOCK_NAME_KEYWORDS.get(su, ()):
            if re.search(rf"(?<![a-z0-9]){re.escape(kw)}(?![a-z0-9])", text_low):
                found.add(su)
                break
    return sorted(found)


def record_finbold_stock_news(tape, client, symbols, start_d, end_d, cfg):
    """Record dated stock headlines from Finbold's public WordPress REST API."""
    sd, ed = _parse_date(start_d), _parse_date(end_d)
    per_page = int(cfg["tm_keyless_news_per_page"])
    allowed = [s.upper() for s in symbols]
    total = 0
    for c_start, c_end in _date_chunks(sd, ed, 14):
        after = f"{c_start.isoformat()}T00:00:00Z"
        before = f"{c_end.isoformat()}T23:59:59Z"
        page = 1
        chunk_rows = []
        while True:
            params = {
                "after": after,
                "before": before,
                "per_page": per_page,
                "page": page,
                "orderby": "date",
                "order": "asc",
                "_fields": "id,date_gmt,modified_gmt,link,title,excerpt",
            }
            try:
                posts, headers = client.get_json_with_headers(FINBOLD_WP_BASE, "", params)
            except HttpError as e:
                if e.code == 400:
                    break
                raise
            if not posts:
                break
            for p in posts:
                link = p.get("link") or ""
                if not link:
                    continue
                headline = _clean_html((p.get("title") or {}).get("rendered", ""))
                summary = _clean_html((p.get("excerpt") or {}).get("rendered", ""))
                if not headline:
                    continue
                syms = _tag_stock_symbols(headline, summary, allowed)
                if not syms:
                    continue
                pub_iso = _ensure_utc_iso(p.get("date_gmt") or "")
                mod_iso = _ensure_utc_iso(p.get("modified_gmt") or pub_iso)
                created = to_epoch(pub_iso)
                updated = to_epoch(mod_iso)
                edited_later = (updated - created) > 3600
                item = {
                    "id": _keyless_news_id("finbold", link),
                    "headline": headline,
                    "summary": summary,
                    "source": "finbold",
                    "url": link,
                    "created_at": pub_iso,
                    "updated_at": mod_iso,
                    "symbols": syms,
                    "wp_id": p.get("id"),
                    "edited_later": edited_later,
                }
                chunk_rows.append(item)
            total_pages = int(headers.get("X-WP-TotalPages") or headers.get("x-wp-totalpages") or 1)
            if page >= total_pages:
                break
            page += 1
        n = tape.add_news(chunk_rows)
        total += n
        print(f"[stock-news:finbold] {c_start}..{c_end}: +{n} articles", flush=True)
    return total


def main(argv=None):
    ap = argparse.ArgumentParser(description="Record historical Alpaca market data into the time-machine tape.")
    ap.add_argument("--db", default=None, help="Path to tape.sqlite (default: $TM_STORE/tape.sqlite)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("sessions", "daily", "universe", "halfhours", "news"):
        p = sub.add_parser(name)
        p.add_argument("--from", dest="start", required=True)
        p.add_argument("--to", dest="end", required=True)

    p_cn = sub.add_parser("crypto-news")
    p_cn.add_argument("--from", dest="start", required=True)
    p_cn.add_argument("--to", dest="end", required=True)
    p_cn.add_argument("--sources", default=",".join(KEYLESS_CRYPTO_NEWS_SOURCES.keys()), help="Comma-separated keyless sources")

    p_lc = sub.add_parser("load-csv")
    p_lc.add_argument("--tf", choices=("1Min", "1Day"), required=True)
    p_lc.add_argument("--file", dest="file_path", default=None)
    p_lc.add_argument("--symbol", default=None)
    p_lc.add_argument("--dir", dest="dir_path", default=None)
    p_lc.add_argument("--symbols", default=None, help="Optional comma-separated filter when using --dir")
    p_lc.add_argument("--from", dest="start", default=None)
    p_lc.add_argument("--to", dest="end", default=None)

    p_st = sub.add_parser("sessions-from-tape")
    p_st.add_argument("--symbol", default="SPY")
    p_st.add_argument("--from", dest="start", required=True)
    p_st.add_argument("--to", dest="end", required=True)

    p_sn = sub.add_parser("stock-news")
    p_sn.add_argument("--symbols", required=True, help="Comma-separated stock/ETF symbols")
    p_sn.add_argument("--from", dest="start", required=True)
    p_sn.add_argument("--to", dest="end", required=True)
    p_sn.add_argument("--sources", default="sec_edgar,finbold", help="Comma-separated sources: sec_edgar,finbold")

    for name in ("minutes", "crypto"):
        p = sub.add_parser(name)
        p.add_argument("--symbols", required=True, help="Comma-separated symbols")
        p.add_argument("--from", dest="start", required=True)
        p.add_argument("--to", dest="end", required=True)
        if name == "crypto":
            p.add_argument("--tf", choices=("both", "1Day", "1Min"), default="both")

    args = ap.parse_args(argv)
    cfg = config()
    tape = Tape(args.db)
    rpm = cfg["tm_keyless_news_max_rpm"] if args.cmd == "crypto-news" else cfg["tm_record_max_rpm"]
    client = Client(max_rpm=rpm)

    try:
        if args.cmd == "sessions":
            record_sessions(tape, client, args.start, args.end)
        elif args.cmd == "daily":
            record_daily(tape, client, args.start, args.end, cfg)
        elif args.cmd == "universe":
            record_universe(tape, args.start, args.end, cfg)
        elif args.cmd == "halfhours":
            record_halfhours(tape, client, args.start, args.end, cfg)
        elif args.cmd == "minutes":
            syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
            record_minutes(tape, client, syms, args.start, args.end, cfg)
        elif args.cmd == "news":
            record_news(tape, client, args.start, args.end)
        elif args.cmd == "crypto":
            syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
            record_crypto(tape, client, syms, args.start, args.end, tf=args.tf)
        elif args.cmd == "crypto-news":
            srcs = [s.strip() for s in args.sources.split(",") if s.strip()]
            record_crypto_news(tape, client, args.start, args.end, cfg, sources=srcs)
        elif args.cmd == "load-csv":
            if args.file_path:
                sym = args.symbol or Path(args.file_path).name.split("_", 1)[0].upper()
                n = load_csv_file(tape, args.file_path, sym, args.tf, start_d=args.start, end_d=args.end)
                print(f"[load-csv:{args.tf}] {args.file_path} ({sym}): +{n} bars", flush=True)
            elif args.dir_path:
                syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()] if args.symbols else None
                load_csv_dir(tape, args.dir_path, args.tf, start_d=args.start, end_d=args.end, symbols=syms)
            else:
                ap.error("load-csv requires --file or --dir")
        elif args.cmd == "sessions-from-tape":
            derive_sessions_from_tape(tape, args.start, args.end, symbol=args.symbol)
        elif args.cmd == "stock-news":
            syms = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
            srcs = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
            if "sec_edgar" in srcs:
                sec_client = Client(max_rpm=cfg["tm_sec_edgar_max_rpm"], user_agent=SEC_USER_AGENT)
                record_sec_news(tape, sec_client, syms, args.start, args.end, cfg)
            if "finbold" in srcs:
                fb_client = Client(max_rpm=cfg["tm_keyless_news_max_rpm"])
                record_finbold_stock_news(tape, fb_client, syms, args.start, args.end, cfg)
    finally:
        tape.close()


if __name__ == "__main__":
    main()
