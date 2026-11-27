"""Forward-only public order-book cost observations for ledger 232."""

import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import fcntl
from functools import cache
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import stat
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "docs/research/195_measurement_133_binance_us_cost.md"
DEFAULT_OFF = Path("/home/user/workspace/rig/data/measure_133")
PUBLIC = ROOT / "practice/forward/M133_log.json"
COINS = "AAVE ADA AVAX BCH BNB BTC DOGE DOT ETH HBAR LINK LTC NEAR PEPE SHIB SOL SUI XLM XRP ZEC".split()
VENUE = "Binance.US"
HOST = "api.binance.us"
VENUES = {VENUE: HOST}
LEDGER = "research_rig/TRIAL_LEDGER.md"
APPROVAL_REF = "refs/heads/main"
SIDES = ("buy", "sell")
GROUPS = ("all", "midnight_utc", "btc_drop")
HOUR = timedelta(hours=1)
PUBLIC_ENDPOINTS = frozenset({"/api/v3/depth", "/api/v3/klines", "/api/v3/exchangeInfo", "/api/v3/aggTrades"})
HOUR_MS = int(HOUR.total_seconds() * 1000)
BLOCKS = (401, 403, 451)


class Refuse(Exception):
    pass


class Failure(Exception):
    def __init__(self, reason):
        self.reason = reason


class Blocked(Failure):
    def __init__(self, host, status):
        super().__init__(f"{host} refused with HTTP {status}")
        self.host, self.status = host, status


class RequestAlarm(TimeoutError):
    def __init__(self, window_limited):
        super().__init__("request wall-clock budget elapsed")
        self.window_limited = window_limited


def need(ok, reason):
    if not ok:
        raise Refuse(reason)


def now_utc():
    return datetime.now(timezone.utc)


def iso(t):
    return t.isoformat(timespec="seconds").replace("+00:00", "Z")


def parse(s):
    return datetime.fromisoformat(s)


def hour(t):
    return t.replace(minute=0, second=0, microsecond=0)


def enc(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(b):
    return sha256(b).hexdigest()


def git(*args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    try:
        return subprocess.check_output(("git", "-c", "core.fsmonitor=false", *args), cwd=ROOT, env=env,
                                       text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        raise Refuse("cannot read committed approval or frozen build") from None


def require_go(row, key, commit, *, ledger=None):
    need(re.fullmatch(r"[a-f0-9]{40}", commit), "invalid frozen build")
    body = git("show", f"{APPROVAL_REF}:{LEDGER}") if ledger is None else ledger
    rows = re.findall(rf"^\|[ \t]*{row}[ \t]*\|[^\r\n]*$", body, re.M)
    marker = rf"(?<![A-Za-z0-9_]){key}"
    approvals = re.findall(marker + r"=([a-f0-9]{40})(?=[\s`|]|$)", rows[0]) if len(rows) == 1 else []
    need(approvals == [commit],
         f"{key} missing or mismatched on committed ledger row {row}")


def checked_build(pins):
    paths = list(pins)
    tracks = git("ls-files", "-v", "-z", "--", *paths).split("\0")
    need({r[2:] for r in tracks if r.startswith("H ")} == set(paths)
         and not git("status", "--porcelain", "--untracked-files=no", "--", *paths),
         "frozen inputs not tracked and clean")
    return git("rev-parse", "--verify", "HEAD").strip()


PINNED = ("practice/measure_133.py", "config/thresholds.yaml",
          "docs/research/195_measurement_133_binance_us_cost.md", "research_rig/GRID_70.json")


def settings():
    cfg = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
    block = cfg["measure_133"]
    plan = block["value"]
    inherited = cfg[plan["protocol_ref"]]["value"]
    fees = cfg[plan["fee_ref"]]["value"]
    path, rule_id, field, key = inherited["btc_drop_reference"].split(":")
    rules = json.loads((ROOT / path).read_text())
    signal = next(r for r in rules if r["id"] == rule_id)[field][key]
    return block, dict(days=inherited["days"], sizes_usd=inherited["sizes_usd"], decision=inherited["decision"],
                       binance_fee=fees["default_taker_bp"], binance_bnb_fee=fees["taker_overrides_bp"]["BNB"],
                       btc_drop=signal, coins=COINS, offset_s=plan["wake_offset_s"], window_s=plan["window_s"])


def frozen():
    block, st = settings()
    return dict(settings=st, sha256={"plan": digest(PLAN.read_bytes()),
                                   "logger": digest(Path(__file__).read_bytes()),
                                   "config_block": digest(enc(block).encode())})


@cache
def private_roots():
    block = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())["measure_132"]
    return tuple(Path(root).resolve() for root in block["value"]["private_roots"])


def checked_dir(off, create=False):
    need(not off.is_symlink(), "log directory must not be a symlink")
    off = off.resolve()
    need(any(off != root and off.is_relative_to(root) for root in private_roots()),
         "private log directory must be below an allowed storage root")
    # An ordinary checkout, linked worktree, or submodule has a .git directory
    # or gitfile at its root. Refuse even when the marker is broken, ignored by
    # Git discovery settings, or supplied through a symlinked parent.
    for parent in (off, *off.parents):
        try:
            (parent / ".git").lstat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        raise Refuse("private log directory must be outside every Git working tree")
    if create:
        missing = [p for p in (off, *off.parents) if not p.exists()]
        off.mkdir(parents=True, exist_ok=True, mode=0o700)
        for p in reversed(missing):
            fsync_dir(p.parent)
    need(off.is_dir() and off.stat().st_uid == os.geteuid() and stat.S_IMODE(off.stat().st_mode) == 0o700,
         "log directory must be a directory with mode 0700")
    return off


def private_open(path, flags):
    fd = os.open(path, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    st = os.fstat(fd)
    if not (stat.S_ISREG(st.st_mode) and stat.S_IMODE(st.st_mode) == 0o600 and st.st_nlink == 1 and st.st_uid == os.geteuid()):
        os.close(fd)
        raise Refuse("private files must be regular, single-link files with mode 0600")
    return fd


@contextmanager
def locked(off, *, write=True, create=False):
    off = checked_dir(off, create)
    flags = os.O_RDWR | os.O_CREAT if write else os.O_RDONLY
    with os.fdopen(private_open(off / ".lock", flags), "rb") as lock:
        try:
            fcntl.flock(lock, (fcntl.LOCK_EX if write else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refuse("logger is busy") from None
        yield off


def anchor_state(rows):
    return {
        "record_count": len(rows),
        "wake_count": sum(r["kind"] in ("wake", "void") for r in rows),
        "last_wake": next((r["wake"] for r in reversed(rows) if r.get("wake") is not None), None),
        "tip_sha256": rows[-1]["sha256_row"] if rows else None,
    }


def fsync_dir(off):
    fd = os.open(off, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_anchor(off, state):
    with tempfile.NamedTemporaryFile(mode="wb", dir=off, prefix=".anchor-", delete=False) as temp:
        try:
            os.fchmod(temp.fileno(), 0o600)
            temp.write(enc(state).encode() + b"\n")
            temp.flush()
            os.fsync(temp.fileno())
            os.replace(temp.name, off / "anchor.json")
            fsync_dir(off)
        finally:
            Path(temp.name).unlink(missing_ok=True)


def read_anchor(off):
    try:
        fd = private_open(off / "anchor.json", os.O_RDONLY)
    except FileNotFoundError:
        return None
    with os.fdopen(fd, "rb") as stream:
        try:
            value = json.load(stream)
            need(isinstance(value, dict) and type(value.get("record_count")) is int
                 and value["record_count"] >= 0, "invalid log anchor")
            return value
        except (ValueError, TypeError):
            raise Refuse("invalid log anchor") from None


def read_log(off, *, recover=False, clock=now_utc):
    path = off / "log.jsonl"
    anchor = read_anchor(off)
    rows, prev, complete_bytes, torn = [], None, 0, b""
    try:
        fd = private_open(path, os.O_RDONLY)
    except FileNotFoundError:
        fd = None
    if fd is not None:
        with os.fdopen(fd, "rb") as stream:
            for line in stream:
                if not line.endswith(b"\n"):
                    torn = line
                    break
                try:
                    row = json.loads(line)
                    own = row.pop("sha256_row")
                    need(row["prev"] == prev and own == digest(enc(row).encode()), "log chain broken")
                except (ValueError, KeyError, TypeError, AttributeError):
                    raise Refuse("log chain broken") from None
                row["sha256_row"] = prev = own
                rows.append(row)
                complete_bytes += len(line)
    if anchor is None:
        need(fd is None, "log exists without a durable tail anchor")
        return rows
    need(len(rows) >= anchor["record_count"], "log is shorter than its durable tail anchor")
    need(len(rows) <= anchor["record_count"], "durable tail anchor is behind the log")
    need(anchor == anchor_state(rows), "log tip does not match the durable tail anchor")
    if torn:
        need(rows and recover, "torn log tail; recovery requires an anchored record and writable command")
        recover_tail(off, rows, complete_bytes, torn, clock)
    return rows


def next_row(rows, event):
    row = dict(event, prev=rows[-1]["sha256_row"] if rows else None)
    row["sha256_row"] = digest(enc(row).encode())
    return row, enc(row).encode() + b"\n"


def recover_tail(off, rows, complete_bytes, torn, clock):
    off = checked_dir(off)
    row, encoded = next_row(rows, dict(kind="recovery", made_utc=iso(clock()), reason="torn_final_line",
                                      discarded_bytes=len(torn), discarded_sha256=digest(torn)))
    # The replacement contains both the truncated prefix and its recovery row;
    # a crash cannot leave a successfully truncated log with no recovery row.
    path = off / "log.jsonl"
    with tempfile.NamedTemporaryFile(mode="wb", dir=off, prefix=".recover-", delete=False) as temp:
        try:
            os.fchmod(temp.fileno(), 0o600)
            with os.fdopen(private_open(path, os.O_RDONLY), "rb") as source:
                remaining = complete_bytes
                while remaining:
                    data = source.read(min(remaining, 1024 * 1024))
                    need(data, "log changed during tail recovery")
                    temp.write(data)
                    remaining -= len(data)
            temp.write(encoded)
            temp.flush()
            os.fsync(temp.fileno())
            os.replace(temp.name, path)
            fsync_dir(off)
        finally:
            Path(temp.name).unlink(missing_ok=True)
    rows.append(row)
    write_anchor(off, anchor_state(rows))


def append(off, rows, **event):
    off = checked_dir(off)
    row, encoded = next_row(rows, event)
    with os.fdopen(private_open(off / "log.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT), "ab") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    rows.append(row)
    write_anchor(off, anchor_state(rows))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


@contextmanager
def wall_budget(seconds, window_limited):
    # The Linux runner is single-threaded. A per-socket timeout alone does not
    # bound a response that keeps sending data slowly.
    def expired(signum, frame):
        raise RequestAlarm(window_limited)

    prior = signal.signal(signal.SIGALRM, expired)
    try:
        signal.setitimer(signal.ITIMER_REAL, seconds)
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, prior)


class PublicPages:
    def __init__(self, opener=None, sleep=time.sleep, monotonic=time.monotonic):
        self.opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self.sleep, self.monotonic = sleep, monotonic
        self.last = {}
        self.deadline = None

    def get(self, venue, path):
        route = urllib.parse.urlsplit(path)
        need(venue == VENUE and route.path in PUBLIC_ENDPOINTS and path.startswith(route.path)
             and not (route.scheme or route.netloc or route.fragment), "unapproved endpoint")
        host = HOST
        req = urllib.request.Request(f"https://{host}{path}", headers={
            "User-Agent": "usd-public-forward/1.0", "Accept": "application/json"})
        for attempt in range(3):
            self.sleep(max(0.0, self.last.get(host, float("-inf")) + 0.4 - self.monotonic()))
            remaining = (self.deadline - now_utc()).total_seconds() if self.deadline else 5
            if remaining <= 0:
                raise Failure("wake_window_elapsed")
            self.last[host] = self.monotonic()
            try:
                budget = min(5, remaining)
                with wall_budget(budget, self.deadline is not None and remaining <= 5):
                    with self.opener.open(req, timeout=5) as response:
                        raw = response.read(8 * 1024 * 1024 + 1)
                    if len(raw) > 8 * 1024 * 1024:
                        raise Failure("response_too_large")
                    if self.deadline and now_utc() >= self.deadline:
                        raise Failure("wake_window_elapsed")
                    return json.loads(raw, parse_float=Decimal)
            except urllib.error.HTTPError as exc:
                status = exc.code
                hint = exc.headers.get("Retry-After") if exc.headers else None
                exc.close()
                if status in BLOCKS:
                    raise Blocked(host, status) from None
                if status != 429 or attempt == 2:
                    raise Failure(f"http_{status}") from None
                delay = 2 ** attempt
                if hint:
                    try:
                        from email.utils import parsedate_to_datetime
                        delay = max(delay, int(hint) if hint.isdigit()
                                    else (parsedate_to_datetime(hint) - now_utc()).total_seconds())
                    except (TypeError, ValueError, OverflowError):
                        raise Failure("http_429_bad_retry_after") from None
                if delay > 8:
                    raise Failure("http_429_retry_after_over_limit") from None
                if self.deadline and now_utc() + timedelta(seconds=delay) >= self.deadline:
                    raise Failure("wake_window_elapsed") from None
                self.sleep(delay)
            except urllib.error.URLError as exc:
                reason = self.timeout_status(exc.reason) if isinstance(exc.reason, TimeoutError) else "network_failure"
                raise Failure(reason) from None
            except TimeoutError as exc:
                raise Failure(self.timeout_status(exc)) from None
            except OSError:
                raise Failure("network_failure") from None
            except (ValueError, RecursionError):
                raise Failure("invalid_json") from None

    def timeout_status(self, exc):
        if ((isinstance(exc, RequestAlarm) and exc.window_limited)
                or (self.deadline is not None and now_utc() >= self.deadline)):
            return "wake_window_elapsed"
        return "timeout"

    def book(self, venue, coin):
        need(coin in COINS, "unapproved USD coin")
        return self.get(venue, f"/api/v3/depth?symbol={coin}USD&limit=100")

    def klines(self, coin, wake, hours):
        need(coin in COINS, "unapproved USD coin")
        end = epoch_ms(hour(wake))
        params = urllib.parse.urlencode({"symbol": coin + "USD", "interval": "1h",
                                         "startTime": end - hours * HOUR_MS, "endTime": end - 1,
                                         "limit": hours})
        return self.get(VENUE, "/api/v3/klines?" + params)

    def candles(self, wake):
        return self.klines("BTC", wake, 2)

    def pairs(self):
        obj = self.get(VENUE, "/api/v3/exchangeInfo")
        if not isinstance(obj["symbols"], list) or not obj["symbols"]:
            raise Failure("invalid_pair_metadata")
        found = {}
        for p in obj["symbols"]:
            coin = p["baseAsset"]
            if coin in COINS and p["quoteAsset"] == "USD" and p["symbol"] == coin + "USD":
                status = p["status"]
                if not isinstance(status, str) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", status) or coin in found:
                    raise Failure("invalid_pair_metadata")
                found[coin] = status
        return {coin: found.get(coin, "NO_USD_PAIR") for coin in COINS}


def price(x):
    if type(x) not in (str, int, float, Decimal):
        raise ValueError("invalid price/size scalar")
    val = Decimal(str(x))
    if not val.is_finite() or val <= 0:
        raise ValueError("nonpositive or nonfinite price/size")
    return val


def walk(levels, usd):
    remaining = Decimal(usd)
    base = Decimal(0)
    for px, qty in levels:
        level_usd = px * qty
        if level_usd >= remaining:
            if base == 0:
                return px
            return Decimal(usd) / (base + remaining / px)
        base += qty
        remaining -= level_usd
    return None


def ticket(book, venue, sizes, fee):
    need(venue == VENUE, "unapproved venue")

    def levels(raw, descending):
        if not isinstance(raw, list) or not raw:
            raise ValueError("empty or malformed side")
        out = []
        for level in raw:
            if (not isinstance(level, list) or len(level) != 2
                    or type(level[0]) is not str or type(level[1]) is not str):
                raise ValueError("malformed level")
            px, qty = price(level[0]), price(level[1])
            if out and not (out[-1][0] > px if descending else out[-1][0] < px):
                raise ValueError("unsorted or duplicate price level")
            out.append((px, qty))
        return out

    try:
        if not isinstance(book, dict):
            raise ValueError("expected depth object")
        bids, asks = levels(book["bids"], True), levels(book["asks"], False)
    except (KeyError, ValueError, ArithmeticError):
        return {"status": "bad book"}
    bid, ask = bids[0][0], asks[0][0]
    if bid >= ask:
        return {"status": "bad book"}
    if book.get("auction_mode"):
        return {"status": "auction_book"}
    mid = (bid + ask) / 2
    out = {"status": "ok", "bid": str(bid), "ask": str(ask), "midpoint": str(mid), "sizes": {}}
    for size in sizes:
        for side, levels, sign in (("buy", asks, 1), ("sell", bids, -1)):
            fill = walk(levels, size)
            side_out = ({"status": "too thin"} if fill is None else
                        {"status": "ok", "fill_price": str(fill),
                         "cost_bp": str(sign * (fill - mid) * 10_000 / mid + Decimal(str(fee)))})
            out["sizes"].setdefault(str(size), {})[side] = side_out
    return out


def epoch_ms(t):
    delta = t - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000


def closed_klines(rows, wake, hours):
    end = epoch_ms(hour(wake))
    want = range(end - hours * HOUR_MS, end, HOUR_MS)
    if not isinstance(rows, list):
        raise Failure("invalid_candle")
    out = {}
    for row in rows:
        if (not isinstance(row, list) or len(row) != 12 or type(row[0]) is not int
                or type(row[6]) is not int):
            raise Failure("invalid_candle")
        stamp = row[0]
        if stamp >= end:
            continue  # the current open hour never contributes a price
        if stamp not in want or row[6] != stamp + HOUR_MS - 1 or stamp in out:
            raise Failure("invalid_or_duplicate_candle_clock")
        fields = row[1:6]
        if any(type(x) is not str for x in fields):
            raise Failure("invalid_candle")
        o, hi, lo, cl = (price(x) for x in fields[:4])
        volume = Decimal(fields[4])
        if not (lo <= min(o, cl) <= max(o, cl) <= hi and volume.is_finite() and volume >= 0):
            raise Failure("invalid_candle")
        out[stamp] = (o, hi, lo, cl, volume)
    if set(out) != set(want):
        raise Failure("missing_adjacent_candle")
    return out


def candle_signal(rows, wake, threshold):
    closes = [v[3] for _, v in sorted(closed_klines(rows, wake, 2).items())]
    value = (closes[1] / closes[0]).ln()
    return {"status": "ok", "log_return": str(value), "drop": value <= -Decimal(str(threshold))}


def terminal(off, rows, exc, *, phase, now, wake=None):
    append(off, rows, kind="stop", phase=phase, at=iso(now), wake=iso(wake) if wake else None,
           host=exc.host, http_status=exc.status)
    raise Refuse(exc.reason)


def start(off, pages=None, clock=now_utc):
    # Start creates a private frozen header; all observation starts at first_wake.
    commit = checked_build(PINNED)
    require_go(232, "M133_START", commit)
    with locked(off, create=True) as off:
        rows = read_log(off, recover=True, clock=clock)
        need(not rows, "log already started")
        fixed = frozen()
        now = clock()
        first = hour(now) + timedelta(seconds=fixed["settings"]["offset_s"])
        if first <= now:
            first += HOUR
        last = first + (fixed["settings"]["days"] * 24 - 1) * HOUR
        write_anchor(off, anchor_state(rows))
        append(off, rows, kind="header", **fixed, freeze=commit, made_utc=iso(now),
               first_wake=iso(first), last_wake=iso(last))
        return {"freeze": commit, "first_wake": iso(first), "last_wake": iso(last)}


def header(rows):
    need(rows and rows[0]["kind"] == "header", "log not started")
    return rows[0]


def record(off, pages, clock=now_utc):
    with locked(off) as off:
        return record_locked(off, pages, clock)


def record_locked(off, pages, clock, rows=None):
    rows = read_log(off, recover=True, clock=clock) if rows is None else rows
    h = header(rows)
    need(not any(r["kind"] == "stop" for r in rows), "logger already stopped; see alive for host/status")
    need(all(h[k] == v for k, v in frozen().items()), "plan, logger or resolved settings changed")
    require_go(232, "M133_START", h["freeze"])
    window = timedelta(seconds=h["settings"]["window_s"])
    pairs = next((r["pairs"] for r in rows if r["kind"] == "pairs"), None)
    first, last = parse(h["first_wake"]), parse(h["last_wake"])
    finished = {r["wake"] for r in rows if r["kind"] in ("wake", "void")}
    begun = {r["wake"] for r in rows if r["kind"] == "begin"}
    wake = first
    while wake <= min(last, clock()):
        stamp = iso(wake)
        now = clock()
        if stamp not in finished:
            if stamp in begun or now >= wake + window:
                reason = "incomplete_attempt_not_retried" if stamp in begun else "missed_wake"
                if wake == first and pairs is None:
                    pairs = {}
                    append(off, rows, kind="pairs", status="first_inventory_not_collected", pairs=pairs)
                append(off, rows, kind="void", wake=stamp, made_utc=iso(now), reason=reason)
            elif now >= wake:
                append(off, rows, kind="begin", wake=stamp, made_utc=iso(now))
                if pairs is None:
                    try:
                        if isinstance(pages, PublicPages):
                            pages.deadline = wake + window
                        pairs = pages.pairs()
                        if (not isinstance(pairs, dict) or set(pairs) != set(COINS)
                                or any(not isinstance(x, str) for x in pairs.values())
                                or clock() >= wake + window):
                            raise Failure("invalid_or_late_pair_metadata")
                    except Blocked as exc:
                        terminal(off, rows, exc, phase="exchangeInfo", now=clock(), wake=wake)
                    except (Failure, OSError, KeyError, TypeError, ValueError) as exc:
                        append(off, rows, kind="pairs", status=getattr(exc, "reason", "invalid_pair_metadata"), pairs={})
                        append(off, rows, kind="void", wake=stamp, made_utc=iso(clock()), reason="pair_inventory_unavailable")
                        return stamp
                    append(off, rows, kind="pairs", status="ok", pairs=pairs)
                collect(off, rows, h["settings"], pairs, pages, wake, clock)
                return stamp
        wake += HOUR
    return None


def collect(off, rows, st, pairs, pages, wake, clock):
    window = timedelta(seconds=st["window_s"])
    if isinstance(pages, PublicPages):
        pages.deadline = wake + window
    books = {venue: {} for venue in VENUES}
    try:
        try:
            signal = candle_signal(pages.candles(wake), wake, st["btc_drop"])
            if clock() >= wake + window:
                signal = {"status": "wake_window_elapsed"}
        except Blocked:
            raise
        except Failure as exc:
            signal = {"status": exc.reason}
        except (KeyError, TypeError, ValueError, InvalidOperation, IndexError):
            signal = {"status": "invalid_candle"}
        for coin in COINS:
            for venue in VENUES:
                status = pairs.get(coin)
                if status != "TRADING":
                    out = {"status": "pair_inventory_unavailable" if status is None else
                           "no_usd_pair" if status == "NO_USD_PAIR" else "pair_not_trading"}
                elif clock() >= wake + window:
                    out = {"status": "wake_window_elapsed"}
                else:
                    fee = st["binance_bnb_fee"] if coin == "BNB" else st["binance_fee"]
                    try:
                        raw = pages.book(venue, coin)
                        out = ({"status": "wake_window_elapsed"} if clock() >= wake + window
                               else ticket(raw, venue, st["sizes_usd"], fee))
                    except Blocked:
                        raise
                    except Failure as exc:
                        out = {"status": ("no_usd_book" if exc.reason == "http_404"
                                          else exc.reason)}
                    except (KeyError, TypeError, ValueError, ArithmeticError, IndexError):
                        out = {"status": "bad book"}
                received = clock()
                if status == "TRADING" and received >= wake + window:
                    out = {"status": "wake_window_elapsed"}
                books[venue][coin] = dict(out, observed_utc=iso(received))
    except Blocked as exc:
        terminal(off, rows, exc, phase="wake", now=clock(), wake=wake)
    finally:
        if isinstance(pages, PublicPages):
            pages.deadline = None
    append(off, rows, kind="wake", wake=iso(wake), made_utc=iso(clock()), bitcoin=signal, books=books)


def stats(values):
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return {"n": 0, "median_bp": None, "p90_bp": None}
    median = (ordered[(n - 1) // 2] + ordered[n // 2]) / 2
    return {"n": n, "median_bp": float(median), "p90_bp": float(ordered[(9*n + 9)//10 - 1])}


def summarize(rows, *, full=False):
    st = header(rows)["settings"]
    samples, detailed, paired = defaultdict(list), defaultdict(list), Counter()
    book_counts = {v: Counter() for v in VENUES}
    side_counts = {v: Counter() for v in VENUES}
    wake_counts, btc_counts, pair_counts = Counter(), Counter(), Counter()
    stop = None
    for row in rows[1:]:
        kind = row["kind"]
        wake_counts[kind] += 1
        if kind == "stop":
            stop = {k: row[k] for k in ("host", "http_status")}
        if kind == "pairs":
            pair_counts.update(row["pairs"].values())
            if row["status"] != "ok":
                pair_counts[row["status"]] += 1
        if kind != "wake":
            continue
        signal = row["bitcoin"]
        btc_counts[signal["status"]] += 1
        if (signal["status"] == "wake_window_elapsed"
                or any(b["status"] == "wake_window_elapsed" for books in row["books"].values() for b in books.values())):
            wake_counts["partial"] += 1
        groups = ["all"]
        if parse(row["wake"]).hour == 0:
            groups.append("midnight_utc")
            wake_counts["midnight"] += 1
        if signal.get("drop"):
            groups.append("btc_drop")
        for venue, books in row["books"].items():
            for coin, book in books.items():
                book_counts[venue][book["status"]] += 1
                for size, sides in book.get("sizes", {}).items():
                    if ("midnight_utc" in groups and venue == "Binance.US"
                            and size == str(max(st["sizes_usd"]))
                            and all(sides[s]["status"] == "ok" for s in SIDES)):
                        paired[coin] += 1
                    for side, item in sides.items():
                        side_counts[venue][item["status"]] += 1
                        if item["status"] != "ok":
                            continue
                        value = Decimal(item["cost_bp"])
                        samples[venue, size, side].append(value)
                        if full:
                            for group in groups:
                                detailed[coin, venue, size, group, side].append(value)
    out = {"status": "BLOCKED" if stop else "STARTED",
           "wake_counts": dict(wake_counts), "scheduled_wakes": st["days"] * 24,
           "book_counts": book_counts, "side_counts": side_counts,
           "bitcoin_candle_counts": dict(btc_counts), "binance_pair_status_counts": dict(pair_counts),
           "stop": stop,
           "costs": {v: {str(n): {s: stats(samples[v, str(n), s]) for s in SIDES}
                         for n in st["sizes_usd"]} for v in VENUES}}
    if not full:
        return out
    out["table"] = [
        {"coin": c, "venue": v, "size_usd": n, "group": g,
         **{s: stats(detailed[c, v, str(n), g, s]) for s in SIDES}}
        for c in COINS for v in VENUES for n in st["sizes_usd"] for g in GROUPS]
    decision = st["decision"]
    qualifying = []
    for coin in COINS:
        side_values = [sorted(detailed[coin, "Binance.US", str(max(st["sizes_usd"])), "midnight_utc", s])
                       for s in SIDES]
        if paired[coin] >= decision["min_midnights"] and all(
                (v[(len(v)-1)//2] + v[len(v)//2])/2 <= Decimal(str(decision["max_cost_bp"])) for v in side_values):
            qualifying.append(coin)
    met = len(qualifying) >= decision["min_coins"]
    out["decision"] = {"met": met, "qualifying_coins": qualifying,
                       "paired_midnights_by_coin": {c: paired[c] for c in COINS},
                       "main_cost_line_bp": decision["max_cost_bp"] if met else decision["fallback_cost_bp"]}
    return out


def atomic_json(path, value):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".m133-", delete=False) as temp:
        try:
            temp.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
            temp.flush()
            if path == PUBLIC:
                os.fchmod(temp.fileno(), 0o644)
            os.replace(temp.name, path)
        finally:
            Path(temp.name).unlink(missing_ok=True)


def read_gate(rows, h, now):
    need(now >= parse(h["last_wake"]) + timedelta(seconds=h["settings"]["window_s"]), "last wake has not passed")
    require_go(232, "M133_READ", h["freeze"])
    need(not any(r["kind"] == "read" for r in rows), "read already used")


def report(off, command, clock=now_utc):
    official = off == DEFAULT_OFF
    with locked(off, write=command == "read") as off:
        rows = read_log(off, recover=command == "read", clock=clock)
        h = header(rows)
        need(all(h[k] == v for k, v in frozen().items()), "plan, logger or resolved settings changed")
        if command == "read":
            now = clock()
            read_gate(rows, h, now)
            if not any(r["kind"] == "stop" for r in rows):
                finish_schedule(off, rows, h, now)
            append(off, rows, kind="read", made_utc=iso(now))
        out = summarize(rows, full=command == "read")
        if command == "publish":
            atomic_json(PUBLIC if official else off / "M133_log.json", out)
        return out


def finish_schedule(off, rows, h, now):
    """After the final window, project missed wakes locally without transport."""
    finished = {r["wake"] for r in rows if r["kind"] in ("wake", "void")}
    begun = {r["wake"] for r in rows if r["kind"] == "begin"}
    wake, last = parse(h["first_wake"]), parse(h["last_wake"])
    while wake <= last:
        stamp = iso(wake)
        if stamp not in finished:
            reason = "incomplete_attempt_not_retried" if stamp in begun else "missed_wake"
            append(off, rows, kind="void", wake=stamp, made_utc=iso(now), reason=reason)
        wake += HOUR


def loop(off, pages, clock=now_utc):
    # A distinct lifetime lock keeps observers available between wakes. A one-shot
    # record shares the operation lock and is idempotent under the same schedule.
    off = checked_dir(off)
    with os.fdopen(private_open(off / ".loop.lock", os.O_RDWR | os.O_CREAT), "rb") as loop_lock:
        try:
            fcntl.flock(loop_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refuse("a loop is already running") from None
        while True:
            with locked(off) as off:
                rows = read_log(off, recover=True, clock=clock)
                h = header(rows)
                record_locked(off, pages, clock, rows)
            now = clock()
            last = parse(h["last_wake"])
            window = timedelta(seconds=h["settings"]["window_s"])
            if now >= last + window:
                return
            nxt = max(parse(h["first_wake"]), hour(now) + timedelta(seconds=h["settings"]["offset_s"]))
            if nxt <= now:
                nxt += HOUR
            time.sleep(max(0, (min(nxt, last + window) - now).total_seconds()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "start", "record", "loop", "alive", "publish", "read"))
    command = parser.parse_args().command
    os.umask(0o077)
    off = DEFAULT_OFF
    try:
        if command == "plan":
            print(PLAN.read_text(), end="")
            return 0
        if command in ("start", "record", "loop"):
            out = {"start": start, "record": record, "loop": loop}[command](off, PublicPages())
        else:
            out = report(off, command)
        if out is not None:
            print(json.dumps(out, indent=2, sort_keys=True))
    except (Refuse, OSError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
