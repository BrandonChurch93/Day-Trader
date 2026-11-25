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
"""
import argparse, datetime as dt, hashlib, html, json, re, statistics, sys, time
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
]


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


def default_http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}, method="GET")
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

    def __init__(self, max_rpm=150, http_get=None, sleep_fn=None, now_fn=None, max_retries=5):
        self.min_interval = 60.0 / max(1.0, float(max_rpm))
        self.http_get = http_get or default_http_get
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
    finally:
        tape.close()


if __name__ == "__main__":
    main()
