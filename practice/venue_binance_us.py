"""Binance.US public transport and private custody shared by the forward collectors."""
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
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
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

import yaml


ROOT = Path(__file__).resolve().parents[1]
COINS = "AAVE ADA AVAX BCH BNB BTC DOGE DOT ETH HBAR LINK LTC NEAR PEPE SHIB SOL SUI XLM XRP ZEC".split()
VENUE = "Binance.US"
HOST = "api.binance.us"
VENUES = {VENUE: HOST}
LEDGER = "research_rig/TRIAL_LEDGER.md"
APPROVAL_REF = "refs/heads/main"
HOUR = timedelta(hours=1)
PUBLIC_ENDPOINTS = frozenset({"/api/v3/depth", "/api/v3/klines", "/api/v3/exchangeInfo", "/api/v3/aggTrades"})
HOUR_MS = int(HOUR.total_seconds() * 1000)
BLOCKS = (418, 401, 403, 451)


class Refuse(Exception):
    pass


class Failure(Exception):
    def __init__(self, reason):
        self.reason = reason


class Blocked(Failure):
    def __init__(self, host, status):
        super().__init__(f"{host} refused with HTTP {status}")
        self.host, self.status = host, status


class Cooldown(Failure):
    def __init__(self, not_before):
        super().__init__("shared_cooldown")
        self.not_before = not_before


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


def precise_utc(t):
    return t.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


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


SIDES = ("buy", "sell")


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


def configured_gate_path():
    return Path(yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
                ["binance_us_gate"]["value"]["cooldown_path"])


def gate_time(value):
    need(type(value) is str and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z", value),
         "invalid shared Binance.US gate time")
    try:
        return parse(value)
    except ValueError:
        raise Refuse("invalid shared Binance.US gate time") from None


def retry_until(now, hint):
    if hint and re.fullmatch(r"[0-9]+", hint := hint.strip()):
        try:
            return now + timedelta(seconds=max(1, int(hint)))
        except (OverflowError, ValueError):
            # Never shorten a valid but unrepresentably long wait.
            return datetime.max.replace(tzinfo=timezone.utc)
    try:
        when = parsedate_to_datetime(hint) if hint else None
        if when and when.utcoffset() is not None:
            return max(when, now + timedelta(seconds=1))
    except (ValueError, TypeError, OverflowError):
        pass
    return now + timedelta(seconds=60)


class Gate:
    """One private, persistent venue gate. Its lock spans the HTTP response."""
    def __init__(self, cooldown_path=None, clock=now_utc):
        self.cooldown_path = Path(cooldown_path) if cooldown_path is not None else configured_gate_path()
        self.clock = clock
        self.held = None

    @contextmanager
    def mutex(self, deadline=None):
        directory = checked_dir(self.cooldown_path.parent, create=True)
        with os.fdopen(private_open(directory / ".gate.lock", os.O_RDWR | os.O_CREAT), "rb") as fd:
            until = time.monotonic() + 0.5
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if deadline is not None and self.clock() >= deadline:
                        raise Failure("wake_window_elapsed") from None
                    if time.monotonic() >= until:
                        raise Failure("shared_gate_busy") from None
                    time.sleep(0.025)
            yield directory

    @staticmethod
    def read(path):
        try:
            with os.fdopen(private_open(path, os.O_RDONLY), "rb") as f:
                raw = f.read(4097)
        except FileNotFoundError:
            return None
        try:
            value = json.loads(raw)
            need(len(raw) <= 4096 and isinstance(value, dict), "invalid shared Binance.US gate file")
            return value
        except (ValueError, RecursionError):
            raise Refuse("invalid shared Binance.US gate file") from None

    @staticmethod
    def write(path, value):
        with tempfile.NamedTemporaryFile("wb", dir=path.parent, prefix=".gate-", delete=False) as f:
            try:
                f.write((enc(value) + "\n").encode())
                f.flush()
                os.fsync(f.fileno())
                os.replace(f.name, path)
                fsync_dir(path.parent)
            finally:
                Path(f.name).unlink(missing_ok=True)

    def check_stop(self, directory):
        stop = self.read(directory / "stop.json")
        if stop is not None:
            need(set(stop) == {"host", "http_status", "stopped_utc"} and stop["host"] == HOST
                 and type(stop["http_status"]) is int and stop["http_status"] in BLOCKS,
                 "invalid shared Binance.US stop")
            gate_time(stop["stopped_utc"])
            raise Blocked(HOST, stop["http_status"])

    def not_before(self, directory):
        state = self.read(directory / self.cooldown_path.name)
        if state is None:
            return None
        need(set(state) == {"not_before_utc"}, "invalid shared Binance.US cooldown")
        return gate_time(state["not_before_utc"])

    def check_start(self):
        with self.mutex() as directory:
            self.check_stop(directory)
            self.not_before(directory)  # Validate custody; cooling down does not cancel a future schedule.

    @contextmanager
    def attempt(self, deadline=None):
        with self.mutex(deadline) as directory:
            self.check_stop(directory)
            not_before = self.not_before(directory)
            now = self.clock()
            if deadline is not None and now >= deadline:
                raise Failure("wake_window_elapsed")
            if not_before is not None and now < not_before:
                raise Cooldown(not_before)
            self.held = directory
            try:
                yield
            finally:
                self.held = None

    def http_error(self, status, retry_after=None):
        need(self.held is not None, "venue gate update requires the request lock")
        if status in BLOCKS:
            self.write(self.held / "stop.json",
                       {"host": HOST, "http_status": status, "stopped_utc": precise_utc(self.clock())})
            raise Blocked(HOST, status)
        if status == 429:
            until = retry_until(self.clock(), retry_after)
            self.write(self.held / self.cooldown_path.name, {"not_before_utc": precise_utc(until)})
            raise Cooldown(until)


def check_start(gate=None):
    try:
        (gate if gate is not None else Gate()).check_start()
    except Failure as exc:
        raise Refuse(exc.reason) from None


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
    def __init__(self, opener=None, sleep=time.sleep, monotonic=time.monotonic, *, gate=None, clock=now_utc):
        self.opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self.sleep, self.monotonic = sleep, monotonic
        self.gate, self.clock = gate if gate is not None else Gate(clock=clock), clock
        self.last = {}
        self.deadline = None

    def get(self, venue, path):
        route = urllib.parse.urlsplit(path)
        need(venue == VENUE and route.path in PUBLIC_ENDPOINTS and path.startswith(route.path)
             and not (route.scheme or route.netloc or route.fragment), "unapproved endpoint")
        host = HOST
        req = urllib.request.Request(f"https://{host}{path}", headers={
            "User-Agent": "usd-public-forward/1.0", "Accept": "application/json"})
        self.sleep(max(0.0, self.last.get(host, float("-inf")) + 0.4 - self.monotonic()))
        with self.gate.attempt(self.deadline):
            remaining = (self.deadline - self.clock()).total_seconds() if self.deadline else 5
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
                    if self.deadline and self.clock() > self.deadline:
                        raise Failure("wake_window_elapsed")
                    return json.loads(raw, parse_float=Decimal)
            except urllib.error.HTTPError as exc:
                try:
                    self.gate.http_error(exc.code, exc.headers.get("Retry-After") if exc.headers else None)
                    raise Failure(f"http_{exc.code}") from None
                finally:
                    exc.close()
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
                or (self.deadline is not None and self.clock() >= self.deadline)):
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


def atomic_json(path, value, *, public=False):
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix=".public-", delete=False) as temp:
        try:
            temp.write(json.dumps(value, indent=2, sort_keys=True) + "\n")
            temp.flush()
            if public:
                os.fchmod(temp.fileno(), 0o644)
            os.replace(temp.name, path)
        finally:
            Path(temp.name).unlink(missing_ok=True)
