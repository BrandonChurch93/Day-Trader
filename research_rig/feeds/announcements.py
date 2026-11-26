"""Offline, point-in-time announcement context from exact Wayback index captures."""

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
import base64
import hashlib
import re
import shutil
import sqlite3
from urllib.parse import urljoin, urlsplit


STORE = Path('/home/user/workspace/rig/data/feeds_announcements')
DB_NAME = 'announcements.sqlite'
START, END = '20210101000000', '20261031235959'
DELAY_SECONDS = 300
MAX_BODY = 2 * 1024 * 1024
MAX_DB = 32 * 1024 * 1024
MIN_FREE = 1024 ** 3
MAX_EXCERPT = 240
MAX_HREF = 512
ASSETS = r'[a-zA-Z0-9._%+~-]+'
HEX_ID = r'[a-fA-F0-9]{32}'
INDEXES = {
    'binance': ('www.binance.com', ('/en/support/announcement',)),
    'coinbase': ('www.coinbase.com', ('/blog',)),
    'kraken': ('blog.kraken.com', ('/category/asset-listings', '/category/product/asset-listings')),
    'okx': ('www.okx.com', ('/help/category/announcements',)),
    'bybit': ('announcements.bybit.com', ('/en',)),
}
ARTICLE_PATHS = {
    'binance': re.compile(rf'/en/support/announcement/(?:detail/|{ASSETS}-)?({HEX_ID})'),
    'coinbase': re.compile(rf'/blog/({ASSETS})'),
    'kraken': re.compile(rf'/(?:product/asset-listings|product|news|post/[0-9]+)/({ASSETS})'),
    'okx': re.compile(rf'/help/({ASSETS})'),
    'bybit': re.compile(rf'/en/article/({ASSETS})'),
}
REGULAR_PATH = re.compile(r'/[a-zA-Z0-9._/+~-]+', re.ASCII)
DIGEST = re.compile(r'[A-Z2-7]{32}', re.ASCII)
STAMP = re.compile(r'[0-9]{14}', re.ASCII)
EVENTS = {
    'monitoring_tag': re.compile(r'\bmonitoring tags?\b', re.I),
    'delisting': re.compile(r'\b(?:de[ -]?list(?:s|ed|ing)?|(?:remov(?:e|es|ed|ing)|removal of) '
                            r'(?:the )?(?:selected |certain )?(?:(?:spot|margin) )?trading pairs?)\b', re.I),
    'trading_halt': re.compile(r'\b(?:halt(?:s|ed|ing)?|suspend(?:s|ed|ing)?|suspension|paus(?:e|es|ing|ed)'
                                r'|disabl(?:e|es|ed|ing))\b.{0,65}\btrading\b'
                                r'|\btrading\b.{0,42}\b(?:halt(?:s|ed|ing)?|suspend(?:s|ed|ing)?|paused)\b', re.I),
    'listing': re.compile(r'\b(?:new listings?(?=[:\s])|will list|to list|lists|now listed|available for trading'
                           r'|trading (?:begins|starts|is live))\b', re.I),
}
NON_NOTICE = re.compile(r'^(?:learn|how to|what is|guide to|why list|view all|see all)\b'
                        r'|\b(?:listings? process|listings? polic(?:y|ies))\b', re.I)
VOID = frozenset('area base br col embed hr img input link meta param source track wbr'.split())
SKIP = frozenset('aside footer header nav noscript script style svg template'.split())
SCHEMA = f"""
CREATE TABLE IF NOT EXISTS announcement (
    exchange TEXT NOT NULL CHECK (exchange IN ('binance','coinbase','kraken','okx','bybit')),
    notice_key TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('listing','delisting','monitoring_tag','trading_halt')),
    capture_ts INTEGER NOT NULL,
    known_at INTEGER NOT NULL CHECK (known_at = capture_ts + {DELAY_SECONDS}),
    digest TEXT NOT NULL CHECK (length(digest) = 32),
    capture_url TEXT NOT NULL,
    notice_url TEXT NOT NULL,
    excerpt TEXT NOT NULL CHECK (length(excerpt) BETWEEN 1 AND {MAX_EXCERPT}),
    PRIMARY KEY (exchange, notice_key)
) STRICT, WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS announcement_wake ON announcement(known_at, exchange, notice_key);
"""


@dataclass(frozen=True)
class IndexCapture:
    """CDX fields and an in-memory replay response from the same exact capture.

    Caller supplies observed response URL, headers, status and original payload
    bytes. This module makes no network requests and never stores the body.
    """

    exchange: str
    original: str
    timestamp: str
    digest: str
    response_url: str
    http_status: int
    memento_datetime: str
    content_type: str
    body: bytes


def _index_proof(c):
    if c.exchange not in INDEXES or not STAMP.fullmatch(c.timestamp) or not START <= c.timestamp <= END:
        raise ValueError('unexpected exchange or capture timestamp')
    ts = datetime.strptime(c.timestamp, '%Y%m%d%H%M%S').replace(tzinfo=timezone.utc)
    host, indexes = INDEXES[c.exchange]
    if not any(c.original in {f'{scheme}://{host}{p}{suffix}'
                             for scheme in ('http', 'https') for suffix in ('', '/')} for p in indexes):
        raise ValueError('capture is not an allowlisted index URL')
    replay = f'https://web.archive.org/web/{c.timestamp}id_/{c.original}'
    if (c.http_status != 200 or c.response_url != replay or
            c.content_type.split(';', 1)[0].strip().lower() != 'text/html'):
        raise ValueError('expected exact successful raw Wayback HTML, not a redirect or live page')
    try:
        moment = parsedate_to_datetime(c.memento_datetime)
    except (TypeError, ValueError) as exc:
        raise ValueError('missing or invalid Memento-Datetime') from exc
    if moment != ts:
        raise ValueError('Memento-Datetime does not match the CDX capture')
    if type(c.body) is not bytes or not 0 < len(c.body) <= MAX_BODY or not DIGEST.fullmatch(c.digest):
        raise ValueError('invalid body size or CDX digest')
    calculated = base64.b32encode(hashlib.sha1(c.body).digest()).decode('ascii')
    if c.digest != calculated:
        raise ValueError('raw HTML bytes do not match the CDX digest')
    return int(ts.timestamp()), replay, c.body.decode('utf-8', errors='strict')


def _notice(exchange, source_url, href):
    # Original same-host links only; no archive-rewritten, query-only or live
    # fetch. Strip query/fragment entirely instead of retaining tracking data.
    if not href or len(href) > MAX_HREF or not href.strip() or any(x.isspace() for x in href.strip()):
        return None
    href = href.strip()
    if href.startswith(('?', '#')) or '\\' in href:
        return None
    try:
        part = urlsplit(urljoin(source_url, href))
    except ValueError:
        return None
    host = INDEXES[exchange][0]
    path = part.path.rstrip('/')
    if (part.scheme not in ('http', 'https') or part.netloc != host or not REGULAR_PATH.fullmatch(path)
            or any(piece in ('.', '..') for piece in path.split('/'))):
        return None
    article = ARTICLE_PATHS[exchange].fullmatch(path)
    if not article:
        return None
    # Binance's direct and /detail aliases have the same 32-hex notice ID.
    # Other venues stay path-keyed: do not borrow later text via inferred aliases.
    key = article.group(1).lower() if exchange == 'binance' else path
    return key, f'https://{host}{path}'


class _Links(HTMLParser):
    """Only visible-ish anchor text from the HTML itself, without JS or child fetches."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.blocked = 0
        self.active = None
        self.links = []

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        blocked = (tag in SKIP or 'hidden' in attrs or attrs.get('aria-hidden') == 'true' or
                   bool(re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', attrs.get('style') or '', re.I)))
        if tag in VOID:
            if tag == 'br' and not blocked:
                self.handle_data(' ')
            return
        if len(self.stack) >= 256:
            raise ValueError('HTML nesting exceeds bound')
        self.stack.append((tag, blocked))
        self.blocked += blocked
        if tag == 'a':
            self.active = (attrs.get('href'), []) if not self.blocked else None

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                if any(t == 'a' for t, _ in self.stack[i:]) and self.active is not None:
                    href, pieces = self.active
                    self.links.append((href, ' '.join(''.join(pieces).split())))
                    self.active = None
                self.blocked -= sum(b for _, b in self.stack[i:])
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.active is not None and not self.blocked:
            self.active[1].append(data)


def _same_time_row(old, new):
    # Alias links and equivalent captures can carry identical notice evidence.
    # Break those ties without blending provenance from separate captures.
    if old[:3] != new[:3] or old[8] != new[8]:
        raise ValueError('conflicting evidence for notice at the same capture timestamp')
    return min(old, new, key=lambda row: (row[6], row[5], row[7]))


def _rows(capture):
    ts, replay, html = _index_proof(capture)
    parser = _Links()
    parser.feed(html)
    parser.close()
    observations = {}
    for href, text in parser.links:
        target = _notice(capture.exchange, capture.original, href)
        if not target or not 12 <= len(text) <= 1000 or NON_NOTICE.search(text) or not text.isprintable():
            continue
        excerpt = text[:MAX_EXCERPT]
        kinds = [kind for kind, pattern in EVENTS.items() if pattern.search(excerpt)]
        if len(kinds) != 1:
            continue
        key, url = target
        row = (capture.exchange, key, kinds[0], ts, ts + DELAY_SECONDS, capture.digest, replay, url, excerpt)
        observations[key] = _same_time_row(observations[key], row) if key in observations else row
    return tuple(observations.values())


def stage_index(capture):
    """Verify one capture and keep only the earliest observed notice excerpt.

    Returns the number of eligible notice observations in this capture, not the
    number inserted. A JS shell can correctly return zero; this is not evidence
    that no notices existed. Do not call this with unapproved publisher content.
    """
    rows = _rows(capture)
    if not rows:
        return 0
    if shutil.disk_usage(STORE.parent).free < MIN_FREE + MAX_DB * 3:
        raise OSError('insufficient disk headroom; the feed must leave 1 GiB free')
    STORE.mkdir(mode=0o700, exist_ok=True)
    path = STORE / DB_NAME
    if (STORE.resolve() != STORE or STORE.stat().st_mode & 0o077 or path.is_symlink() or
            (path.exists() and (not path.is_file() or path.stat().st_mode & 0o077))):
        raise OSError('announcement store must be a private directory and file, not a symlink')
    # Exclusive file creation keeps it private before SQLite opens it; mode=rw
    # prevents the database from being silently recreated if the file is absent.
    try:
        path.touch(mode=0o600, exist_ok=False)
    except FileExistsError:
        pass
    with closing(sqlite3.connect(path.as_uri() + '?mode=rw', uri=True)) as conn, conn:
        conn.execute('PRAGMA temp_store=MEMORY')
        conn.execute('PRAGMA journal_mode=DELETE')
        page_size = conn.execute('PRAGMA page_size').fetchone()[0]
        max_pages = MAX_DB // page_size
        if conn.execute(f'PRAGMA max_page_count={max_pages}').fetchone()[0] != max_pages:
            raise OSError('announcement store exceeds disk budget')
        conn.executescript(SCHEMA)
        conn.execute('BEGIN IMMEDIATE')
        for row in rows:
            stored = conn.execute('SELECT * FROM announcement WHERE exchange=? AND notice_key=?', row[:2]).fetchone()
            if stored and stored[3] == row[3]:
                row = _same_time_row(stored, row)
            if not stored or (row[3] <= stored[3] and row != stored):
                conn.execute('INSERT OR REPLACE INTO announcement VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', row)
    return len(rows)


def get_announcements(wake_utc, *, after_utc=None, exchange=None, db_path=None):
    """Scout query: return first captured index excerpts known by this wake.

    Times are UTC Unix seconds. Optional lower bound is exclusive on known_at.
    Missing data is not evidence of no event. Missing database raises an error.
    """
    if type(wake_utc) is not int or (after_utc is not None and
                                    (type(after_utc) is not int or after_utc > wake_utc)):
        raise ValueError('wake and optional lower bound must be ordered integer Unix seconds')
    if exchange is not None and exchange not in INDEXES:
        raise ValueError('unknown exchange')
    path = Path(db_path) if db_path is not None else STORE / DB_NAME
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT * FROM announcement WHERE capture_ts <= known_at '
            'AND known_at = capture_ts + ? AND known_at <= ? '
            'AND (? IS NULL OR known_at > ?) AND (? IS NULL OR exchange = ?) '
            'ORDER BY known_at, exchange, notice_key',
            (DELAY_SECONDS, wake_utc, after_utc, after_utc, exchange, exchange),
        ).fetchall()
    return [dict(row) for row in rows]
