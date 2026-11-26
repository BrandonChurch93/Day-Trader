"""E10 public Coinbase USD observations and pretend fills only. No keys, login or orders."""
import argparse
import fcntl
import inspect
import json
import math
import os
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from urllib import error, parse as urlparse, request

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research_rig"))
import score_75 as core

CARD = "practice/traders/E10_coin_trend_ratchet.md"
PINNED = (CARD, "practice/forward_e10.py", "research_rig/score_75.py", "config/thresholds.yaml")
OFF = Path("/home/user/workspace/rig/data/forward_e10")
PUBLIC = ROOT / "practice/forward/E10_log.json"
HOST = "https://api.exchange.coinbase.com"
BINANCE_HOST = "https://api.binance.us"
SECOND = "binance_us"
SECOND_LABEL = "second book, cheaper venue, quotes only, no account"
QUOTE_LINES = {"quote", SECOND}
UTC = timezone.utc
NAMES = core.NAMES


class Refuse(Exception):
    pass


class Blocked(Refuse):
    pass


def need(ok, message):
    if not ok:
        raise Refuse(message)


def settings():
    raw = yaml.safe_load((ROOT / PINNED[-1]).read_text())
    base_f = raw["forward_e10"]["value"]
    f = base_f | {"second_fees": raw[base_f["second_fee_key"]]["value"]}
    rule = raw[f["rule_key"]]["value"]
    marks = raw[rule["inherited_marks_key"]]["value"]
    fees = {key: sum(raw[base]["value"][field] for field in fields) / 10000
            for key, (base, *fields) in rule["costs"].items()}
    base, field = f["spot_taker"]
    fees = {"quote": raw[base]["value"][field] / 10000,
            "flat": fees["main"], "harsh": fees["harsh"]}
    return f, rule, marks, fees


def second_fee(f, coin):
    cfg = f["second_fees"]
    return cfg["taker_overrides_bp"].get(coin, cfg["default_taker_bp"]) / 10000


def now_utc():
    return datetime.now(UTC)


def midnight(t):
    return t.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)


def iso(t):
    return t.astimezone(UTC).isoformat(timespec="seconds")


def parse(t):
    return datetime.fromisoformat(t)


def blob(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(blob(value).encode()).hexdigest()


def pins():
    return {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in PINNED}


@contextmanager
def private(folder, create=False):
    if create:
        folder.mkdir(mode=0o700, exist_ok=True)
    fd = os.open(folder, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY)
    try:
        st = os.fstat(fd)
        need(stat.S_IMODE(st.st_mode) == 0o700 and st.st_uid == os.geteuid(), "private folder required")
        yield fd
    finally:
        os.close(fd)


@contextmanager
def private_file(fd, name, flags):
    file = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=fd)
    try:
        st = os.fstat(file)
        need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_uid == os.geteuid()
             and stat.S_IMODE(st.st_mode) == 0o600, "private regular file required")
        yield file
    finally:
        os.close(file)


@contextmanager
def lock(fd, name, blocking=False):
    with private_file(fd, name, os.O_RDWR | os.O_CREAT) as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        except BlockingIOError:
            raise Refuse("another writer is running") from None
        yield


def read_log(fd):
    try:
        with private_file(fd, "log.jsonl", os.O_RDONLY) as file, os.fdopen(os.dup(file), "r") as inp:
            rows = []
            prior = None
            for line in inp:
                obj = json.loads(line)
                current = obj.pop("sha256")
                need(line.endswith("\n") and obj["prev"] == prior and digest(obj) == current,
                     "log chain broken")
                rows.append(obj | {"sha256": current})
                prior = current
            with private_file(fd, "tip", os.O_RDONLY) as tip:
                need(os.read(tip, 100).decode() == (prior or "") + "\n", "log tip mismatch")
            return rows
    except FileNotFoundError:
        for name in ("log.jsonl", "tip"):
            try:
                os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise Refuse("log tip mismatch") from None
        return []
    except (KeyError, ValueError, AttributeError, TypeError):
        raise Refuse("log chain broken") from None


def append(fd, rows, row):
    row = row | {"prev": rows[-1]["sha256"] if rows else None}
    row["sha256"] = digest(row)
    with private_file(fd, "log.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND) as file:
        with os.fdopen(os.dup(file), "a") as out:
            out.write(blob(row) + "\n")
            out.flush()
            os.fsync(out.fileno())
        with private_file(fd, "tip.tmp", os.O_WRONLY | os.O_CREAT | os.O_EXCL) as tip:
            os.write(tip, (row["sha256"] + "\n").encode())
            os.fsync(tip)
        os.replace("tip.tmp", "tip", src_dir_fd=fd, dst_dir_fd=fd)
        os.fsync(fd)
    rows.append(row)


def checked(rows, *, recording=False):
    need(rows and rows[0]["kind"] == "header", "log not started")
    need(rows[0]["pins"] == pins(), "frozen files changed")
    if recording:
        need(not any(r["kind"] == "blocked" for r in rows), "venue blocked; recording stopped")
    return rows[0]


def start(now, folder=OFF, commit=None):
    with private(folder, create=True) as fd, lock(fd, "writer.lock"):
        rows = read_log(fd)
        need(not rows, "log already started")
        if commit is None:
            git = lambda *a: subprocess.check_output(("git", *a), cwd=ROOT, text=True).strip()
            need(not git("status", "--porcelain", "--", *PINNED), "freeze files differ from HEAD")
            commit = git("rev-parse", "HEAD")
        append(fd, rows, {"kind": "header", "pins": pins(), "freeze": commit,
                          "first": iso(midnight(now) + timedelta(days=1)), "started": iso(now)})
        return rows[0]


def positive(value):
    try:
        x = float(value)
        return x if math.isfinite(x) and x > 0 else None
    except (TypeError, ValueError):
        return None


def product_state(product):
    keys = ("trading_disabled", "cancel_only", "post_only", "limit_only")
    raw = {k: (product or {}).get(k) for k in (*keys, "status")}
    blocked = raw["status"] != "online" or any(raw[k] is not False for k in keys[:-1])
    limited = raw["limit_only"]
    return {"eligible": not blocked and limited is False, "sell": not blocked and type(limited) is bool,
            "base_min": positive((product or {}).get("base_min_size")),
            "usd_min": positive((product or {}).get("min_market_funds")),
            "exists": product is not None, "flags": raw}


class SameHost(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise Refuse("public host returned a redirect")


class PublicREST:
    host = None

    def __init__(self, f):
        self.f, self.last = f, 0.
        self.opener = request.build_opener(SameHost())

    def get(self, path, missing_ok=False):
        need(path.startswith("/") and not path.startswith("//"), "invalid venue path")
        for attempt in range(self.f["request_attempts"]):
            time.sleep(max(0, self.last + self.f["request_gap_s"] - time.monotonic()))
            self.last = time.monotonic()
            try:
                req = request.Request(self.host + path, headers={"User-Agent": "e10-forward/1", "Accept": "application/json"})
                with self.opener.open(req, timeout=self.f["timeout_s"]) as inp:
                    return json.load(inp)
            except error.HTTPError as e:
                e.close()
                if e.code in (401, 403, 451):
                    raise Blocked(f"venue refused HTTP {e.code}") from None
                if e.code == 404 and missing_ok:
                    return None
                delay = 2 ** attempt
                if e.code == 429:
                    delay = max(delay * self.f["rate_backoff_s"], positive(e.headers.get("Retry-After")) or 0)
                    if delay > self.f["rate_backoff_cap_s"]:
                        raise Refuse("rate limit exceeds observation budget") from None
            except (error.URLError, OSError, ValueError):
                delay = 2 ** attempt
            if attempt + 1 < self.f["request_attempts"]:
                time.sleep(delay)
        raise Refuse("public venue unavailable")


class Coinbase(PublicREST):
    host = HOST

    def products(self):
        return {p["id"]: p for p in self.get("/products")}

    def candles(self, coin, first, stop):
        gran = self.f["day_s"]
        query = urlparse.urlencode({"granularity": gran, "start": iso(first), "end": iso(stop)})
        raw = self.get(f"/products/{coin}-USD/candles?{query}", True)
        out = {}
        for row in raw or ():
            dt = datetime.fromtimestamp(int(row[0]), UTC)
            if first <= dt < stop and dt == midnight(dt):
                need(dt.date().isoformat() not in out, "duplicate candle clock")
                out[dt.date().isoformat()] = [positive(row[3]), positive(row[4])]
        return out

    def book(self, coin):
        raw = self.get(f"/products/{coin}-USD/book?level=1", True)
        try:
            bid, ask = positive(raw["bids"][0][0]), positive(raw["asks"][0][0])
        except (KeyError, IndexError, TypeError):
            return None
        return [bid, ask] if bid and ask and bid <= ask else None


class BinanceUS(PublicREST):
    host = BINANCE_HOST

    def products(self):
        raw = self.get("/api/v3/exchangeInfo")
        need(isinstance(raw, dict) and isinstance(raw.get("symbols"), list), "invalid public pair list")
        return {p["symbol"]: p for p in raw["symbols"] if isinstance(p, dict)
                and p.get("baseAsset") in NAMES and p.get("quoteAsset") == "USD"
                and p.get("symbol") == p["baseAsset"] + "USD"}

    def book(self, coin):
        symbol = coin + "USD"
        raw = self.get("/api/v3/ticker/bookTicker?symbol=" + symbol, True)
        if not isinstance(raw, dict) or raw.get("symbol") != symbol:
            return None
        bid, ask = positive(raw.get("bidPrice")), positive(raw.get("askPrice"))
        if bid and ask and bid <= ask and positive(raw.get("bidQty")) and positive(raw.get("askQty")):
            return [bid, ask]
        return None


def binance_pair(product):
    p = product or {}
    status = p.get("status")
    market = isinstance(p.get("orderTypes"), list) and "MARKET" in p["orderTypes"]
    allowed = status == "TRADING" and p.get("isSpotTradingAllowed") is True and market
    minimums = {}
    for entry in p.get("filters") or ():
        if not isinstance(entry, dict):
            continue
        k = entry.get("filterType")
        if (k == "MIN_NOTIONAL" and entry.get("applyToMarket") is True) or (
                k == "NOTIONAL" and entry.get("applyMinToMarket") is True):
            n = positive(entry.get("minNotional"))
            if n:
                minimums[k] = n
    qty = [positive(entry.get("minQty")) for entry in p.get("filters") or ()
           if isinstance(entry, dict) and entry.get("filterType") == "MARKET_LOT_SIZE"]
    return {"eligible": allowed, "sell": allowed, "exists": product is not None,
            "base_min": max((v for v in qty if v), default=None),
            "usd_min": max(minimums.values(), default=None),
            "flags": {"status": status, "spot": p.get("isSpotTradingAllowed"), "market": market}}


def make_adapter():
    """Compile frozen play with checked execution, fees, and terminal marking seams."""
    source = inspect.getsource(core.play)
    signature = '*, mode="trend", override=None, shift=0):'
    old_start = "        sells, buys = np.minimum(delta, 0), np.maximum(delta, 0)"
    old_stop = "        shares += np.divide(delta, px[:, None], out=np.zeros_like(shares), where=px[:, None] > 0)"
    terminal = "        if d == nd - 1:"
    old_fee = "float(abs(net[j]) * cost)"
    old_cash = "balance -= net.sum() + debit(net)"
    need(all(source.count(s) == 1 for s in (signature, old_start, old_stop, terminal, old_fee, old_cash)),
         "frozen play seam changed")
    source = source.replace(signature, signature[:-2] + ", execution=None, terminal=True):")
    lo, hi = source.index(old_start), source.index(old_stop)
    block = source[lo:hi].rstrip().splitlines()
    dl, dh = block.index("        def debit(net):"), block.index("        def net_at(scale):")
    debit = block[dl:dh]
    block = block[:dl] + block[dh:]
    source = (source[:lo] + "\n".join(debit) + "\n        if execution is None:\n" +
              "\n".join("    " + line if line else "" for line in block) +
              "\n        else:\n            delta, net, charges = execution(d, delta, px, balance, cost, queued)\n" + source[hi:])
    source = source.replace(old_fee, "float(abs(net[j]) * cost if execution is None else charges[j])")
    source = source.replace(old_cash, "balance -= net.sum() + (debit(net) if execution is None else charges.sum())")
    source = source.replace(terminal, "        if terminal and d == nd - 1:")
    namespace = vars(core).copy()
    exec(compile(source, core.__file__ + ":E10", "exec"), namespace)
    return namespace["play"]


play_forward = make_adapter()


def decisions(tape, rule, marks):
    signals = core.indicators(tape, rule["lookbacks"], rule, marks["annual_days"])
    return signals, core.calendar(tape, signals[2])


def execution(rows, size, line, skip, attempted, void_buys, pending, f):
    """Plan at the reference open; settle the net coin quantity at its bid/ask."""
    def at(d, delta, px, cash, fee, queued):
        shared = rows[d]
        market = shared.get(SECOND, {}) if line == SECOND else shared
        sells, buys = np.minimum(delta, 0), np.maximum(delta, 0)
        base, usd = np.zeros(len(px)), np.zeros(len(px))
        ratio_buy, ratio_sell = np.ones(len(px)), np.ones(len(px))
        allowed = np.ones(len(px), dtype=bool)
        rates = np.array([second_fee(f, k) for k in NAMES]) if line == SECOND else fee
        reasons = {}
        for j in np.flatnonzero(np.any(delta != 0, axis=1)):
            state = market.get("states", {}).get(NAMES[j], {})
            q = market.get("quotes", {}).get(NAMES[j])
            base[j], usd[j] = state.get("base_min") or 0, state.get("usd_min") or 0
            allowed[j] = bool(usd[j] if line == SECOND else (base[j] or usd[j]))
            reasons[j] = "minimum_unknown"
            if line in QUOTE_LINES:
                if q and px[j] > 0:
                    ratio_buy[j], ratio_sell[j] = q["ask"] / px[j], q["bid"] / px[j]
                else:
                    allowed[j] = False
                    reasons[j] = "quote_missing"
            if line == SECOND and not state.get("eligible"):
                allowed[j] = False
                reasons[j] = ("venue_unavailable" if market.get("status") != "OBSERVED" else "pair_unavailable")
            missing_shared_data = NAMES[j] in shared.get("candle_failures", {})
            if missing_shared_data or not market.get("buy_window") or not (q and q["timely"]):
                if delta[j].sum() > 1e-14:
                    void_buys.add((d, int(j)))
                    # Keep any exit quantity even when the coincident purchase is void.
                    buys[j] = 0
        trial = (sells + buys).sum(axis=1)
        candidates = {int(j) for j in np.flatnonzero(np.abs(trial) > 1e-14)}
        attempted[d] = candidates | {j for day, j in void_buys if day == d}
        for j in attempted[d]:
            if not allowed[j]:
                skip[d, j] = reasons[j]
                buys[j] = sells[j] = 0

        def net_at(x):
            net = (sells + x * buys).sum(axis=1)
            return net * np.where(net > 0, ratio_buy, ratio_sell)

        def debit(net):
            magnitude = np.abs(net)
            return float(np.dot(magnitude, rates)) if line == SECOND else fee * magnitude.sum()

        while True:
            hi = 1.
            net = net_at(hi)
            if net.sum() + debit(net) > cash + 1e-12:
                lo = 0.
                for _ in range(48):
                    mid = (lo + hi) / 2
                    v = net_at(mid)
                    if v.sum() + debit(v) <= cash:
                        lo = mid
                    else:
                        hi = mid
                hi = lo
                net = net_at(hi)
            ref = (sells + hi * buys).sum(axis=1)
            qty = np.divide(np.abs(ref) * size, px, out=np.zeros_like(px), where=px > 0)
            too_small = (np.abs(net) > 1e-14) & ((qty < base) | (np.abs(net) * size < usd))
            if not too_small.any():
                settled = sells + hi * buys
                if shared.get("kind") in {"wake", "void"}:
                    pending[d] = set(np.flatnonzero(queued.any(axis=1) & ~(settled < -1e-14).any(axis=1)))
                return settled, net, rates * np.abs(net)
            for j in np.flatnonzero(too_small):
                skip[d, int(j)] = "under_minimum"
            buys[too_small] = sells[too_small] = 0
    return at


def market_rows(log):
    return [r for r in log if r["kind"] in {"wake", "void", "close"}]


def make_tape(log, f, rule, line):
    first = parse(log[0]["first"]).date()
    prefix = max(rule["vol_days"] + 1, max(rule["lookbacks"]))
    days0 = first - timedelta(days=prefix)
    visits = market_rows(log)
    end = parse(visits[-1]["wake"]).date() if visits else first
    days = tuple(days0 + timedelta(days=i) for i in range((end-days0).days + 1))
    rows = [{} for _ in days]
    s = len(days), len(NAMES)
    opens, closes = np.full(s, np.nan), np.full(s, np.nan)
    eligible, sale = np.zeros(s, bool), np.zeros(s, bool)
    earliest = next((w for w in visits if w["kind"] == "wake"), None)
    if earliest:
        for k, mapping in earliest.get("warmup", {}).items():
            j = NAMES.index(k)
            for stamp, px in mapping.items():
                d = (datetime.fromisoformat(stamp).date() - days0).days
                if 0 <= d < prefix:
                    closes[d, j] = px if px is not None else np.nan
    for w in visits:
        d = (parse(w["wake"]).date() - days0).days
        rows[d] = w
        if w["kind"] != "wake":
            eligible[d] = eligible[d-1]
        for stamp, bars in w.get("completed", {}).items():
            observed = (datetime.fromisoformat(stamp).date() - days0).days
            need(0 <= observed < d, "completed close outside fence")
            for k, rec in bars.items():
                j = NAMES.index(k)
                need(not np.isfinite(closes[observed, j]), "completed close already frozen")
                closes[observed, j] = rec
        outage = w.get("outage", False)
        if outage:
            eligible[d] = eligible[d-1]
        for j, k in enumerate(NAMES):
            if w["kind"] != "wake":
                continue
            state = w["states"][k]
            if w is earliest:
                # First point-in-time snapshot supplies initial admission only.
                eligible[d-1, j] = state["eligible"]
            if outage:
                continue
            eligible[d, j], sale[d, j] = state["eligible"], state["sell"]
            px = w["opens"].get(k)
            q = w["quotes"].get(k)
            if line == "quote" and q:
                px = (q["bid"] + q["ask"]) / 2
            if px is not None:
                opens[d, j] = px
    return core.Tape(days, NAMES, opens, closes, eligible, sale), rows, prefix


def run_book(log, f, rule, marks, fees, line, size):
    # The second book consumes the same inputs and roster clock as Coinbase.
    tape, rows, prefix = make_tape(log, f, rule, "quote" if line == SECOND else line)
    skipped, attempted, void_buys, pending = {}, {}, set(), {}
    signal, roster = decisions(tape, rule, marks)
    if line == SECOND:
        opens = tape.opens.copy()
        for d, row in enumerate(rows):
            for k, q in row.get(SECOND, {}).get("quotes", {}).items():
                opens[d, NAMES.index(k)] = (q["bid"] + q["ask"]) / 2
        # Venue-specific restrictions, including missing pairs, are execution
        # gates below; the shared roster and completed close signals do not change.
        tape = core.Tape(tape.days, tape.names, opens, tape.closes, tape.eligible, np.isfinite(opens))
    rate = second_fee(f, f["reference_coin"]) if line == SECOND else fees[line]
    book = play_forward(tape, rate, rule, rule["cap"], signal, roster, terminal=False,
                        execution=execution(rows, size, line, skipped, attempted, void_buys, pending, f))
    return tape, prefix, book, skipped, attempted, void_buys, pending


def coin_page(fetch, failures, coin, *args):
    try:
        return fetch(coin, *args)
    except Blocked:
        raise
    except (Refuse, OSError, ValueError, TypeError, IndexError, KeyError):
        failures[coin] = "PAGE_UNAVAILABLE"
        return None


def public_quotes(venue, coins, wake, clock, f):
    found = {}
    failures = {}
    for coin in coins:
        q = coin_page(venue.book, failures, coin)
        if not q:
            failures.setdefault(coin, "QUOTE_MISSING")
        sec = (clock() - wake).total_seconds()
        if q and 0 <= sec < f["day_s"]:
            found[coin] = {"bid": q[0], "ask": q[1], "seconds": sec,
                           "timely": sec <= f["quote_offsets_s"][-1]}
    return found, failures


def capture_second(venue, wake, clock, f, stopped):
    row = {"states": {}, "quotes": {}, "quote_failures": {},
           "buy_window": False, "late": True, "status": "NOT_OBSERVED"}
    if stopped or venue is None:
        row["status"] = "BLOCKED" if stopped else "NOT_OBSERVED"
        return row, None
    try:
        products = venue.products()
        row["states"] = {k: binance_pair(products.get(k + "USD")) for k in NAMES}
        row["quotes"], row["quote_failures"] = public_quotes(
            venue, [k for k in NAMES if row["states"][k]["eligible"]], wake, clock, f)
    except Blocked as e:
        row["status"] = "BLOCKED"
        return row, str(e)
    except (Refuse, OSError, ValueError, TypeError, KeyError):
        row["status"] = "UNAVAILABLE"
        return row, None
    row["status"] = "OBSERVED"
    row["buy_window"] = any(q["timely"] for q in row["quotes"].values())
    row["late"] = not row["buy_window"]
    return row, None


def capture(log, wake, venue, clock, f, rule, close_only=False):
    first = parse(log[0]["first"])
    warm = not any(r["kind"] == "wake" for r in log) and not close_only
    pre_days = max(rule["vol_days"] + 1, max(rule["lookbacks"]))
    begin = first - timedelta(days=pre_days)
    last = next((parse(r["wake"]) for r in reversed(log) if r["kind"] == "wake"), first)
    products = venue.products()
    states = {k: product_state(products.get(k + "-USD")) for k in NAMES}
    row = {"kind": "close" if close_only else "wake", "wake": iso(wake),
           "states": states, "completed": {}, "warmup": {}, "opens": {}, "quotes": {},
           "quote_failures": {}, "candle_failures": {},
           "outage": not any(s["eligible"] or s["sell"] for s in states.values())}
    if not close_only:
        row["quotes"], row["quote_failures"] = public_quotes(
            venue, [k for k in NAMES if states[k]["eligible"] or states[k]["sell"]
                    or k == f["reference_coin"]], wake, clock, f)
        row["buy_window"] = any(q["timely"] for q in row["quotes"].values())
        row["late"] = not row["buy_window"]
        row["observed"] = iso(clock())
    for k in NAMES:
        if k + "-USD" not in products:
            continue
        if warm:
            warmup = coin_page(venue.candles, row["candle_failures"], k, begin, first) or {}
            row["warmup"][k] = {d: bar[1] for d, bar in warmup.items()
                               if d < first.date().isoformat() and bar[1] is not None}
        stop = wake if close_only else wake + timedelta(days=1)
        cursor = last
        while cursor < stop:
            part = min(stop, cursor + timedelta(days=f["candle_page_days"]))
            daily = coin_page(venue.candles, row["candle_failures"], k, cursor, part) or {}
            for d, (op, cl) in daily.items():
                if d < wake.date().isoformat() and cl is not None:
                    row["completed"].setdefault(d, {})[k] = cl
                if not close_only and d == wake.date().isoformat() and op is not None:
                    row["opens"][k] = op  # never keep any close from the forming candle
            cursor = part
    return row


def attach_orders(log, row, f, rule, marks, fees):
    day = parse(row["wake"]).date()
    by_line, follow, second_follow = {}, set(), set()
    for line in (*fees, SECOND):
        for size_label, size in f["bankroll_usd"].items():
            tape, _, book, skipped, attempted, void_buys, pending = run_book(
                log + [row], f, rule, marks, fees, line, size)
            d = tape.days.index(day)
            ts = {NAMES[j] for j in attempted.get(d, set())}
            fills = [{"coin": NAMES[j], "side": "buy" if amount > 0 else "sell"}
                     for i, j, amount, _ in book.fills if i == d]
            ts.update(fill["coin"] for fill in fills)
            by_line[f"{line}:{size_label}"] = {
                "orders": sorted(ts), "fills": fills,
                "under": sum(v == "under_minimum" for (i, j), v in skipped.items() if i == d),
                "minimum_unknown": sum(v == "minimum_unknown" for (i, j), v in skipped.items() if i == d),
                "quote_missing": sum(v == "quote_missing" for (i, j), v in skipped.items() if i == d),
                "pair_unavailable": sum(v == "pair_unavailable" for (i, j), v in skipped.items() if i == d),
                "venue_unavailable": sum(v == "venue_unavailable" for (i, j), v in skipped.items() if i == d),
                "void_buys": sum(i == d for i, j in void_buys),
                "queued_sells": len(pending.get(d, ())),
                "delayed_sells": sum(i == d and amount < 0 and j in pending.get(d-1, ())
                                     for i, j, amount, _ in book.fills),
            }
            (second_follow if line == SECOND else follow).update(ts)
    row["orders"], row["follow"] = by_line, sorted(follow)
    market = row[SECOND]
    market["follow"] = sorted(k for k in second_follow if market["states"].get(k, {}).get("eligible"))


def record(now, venue=None, folder=OFF, clock=now_utc, sleep=time.sleep, *, second_venue=None):
    f, rule, marks, fees = settings()
    with private(folder) as fd, lock(fd, "observer.lock"):
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            with lock(fd, "writer.lock"):
                rows = read_log(fd)
                header = checked(rows, recording=True)
                first = parse(header["first"])
                visits = market_rows(rows)
                observed = next((parse(r["wake"]) for r in visits if r["kind"] == "wake"), None)
                end = observed + timedelta(days=f["score_days"]) if observed else None
                wake = min(midnight(now), end) if end else midnight(now)
                next_wake = parse(visits[-1]["wake"]) + timedelta(days=1) if visits else first
                while next_wake < wake:
                    append(fd, rows, {"kind": "void", "wake": iso(next_wake), "reason": "missed"})
                    next_wake += timedelta(days=1)
                if next_wake != wake or now < wake + timedelta(seconds=f["wake_delay_s"]):
                    return None
                if venue is None and second_venue is None:
                    second_venue = BinanceUS(f)
                venue = venue if venue is not None else Coinbase(f)
                second_stopped = any(r["kind"] == "second_blocked" for r in rows)
                job = (pool.submit(capture_second, second_venue, wake, clock, f, second_stopped)
                       if wake != end else None)
                try:
                    row = capture(rows, wake, venue, clock, f, rule, close_only=wake == end)
                finally:
                    if job is not None:
                        market, second_stop = job.result()
                        if second_stop:
                            append(fd, rows, {"kind": "second_blocked", "observed": iso(clock()), "reason": second_stop})
                            second_stopped = True
                if job is not None:
                    row[SECOND] = market
                    attach_orders(rows, row, f, rule, marks, fees)
                append(fd, rows, row)
            for offset in f["quote_offsets_s"]:
                second_coins = row.get(SECOND, {}).get("follow") if not second_stopped else None
                if not (row.get("follow") or second_coins):
                    break
                target = wake + timedelta(seconds=offset)
                wait = (target - clock()).total_seconds()
                if wait < 0:
                    continue  # a missed observation is never made up
                sleep(wait)
                job = pool.submit(public_quotes, second_venue, second_coins, wake, clock, f) if second_coins else None
                try:
                    quotes, failures = public_quotes(venue, row["follow"], wake, clock, f)
                    if row["follow"]:
                        with lock(fd, "writer.lock", blocking=True):
                            append(fd, rows, {"kind": "follow", "wake": iso(wake), "offset": offset,
                                              "quotes": quotes, "quote_failures": failures})
                finally:
                    if job is not None:
                        with lock(fd, "writer.lock", blocking=True):
                            try:
                                quotes, failures = job.result()
                                append(fd, rows, {"kind": "second_follow", "wake": iso(wake),
                                                  "offset": offset, "quotes": quotes, "quote_failures": failures})
                            except Blocked as e:
                                append(fd, rows, {"kind": "second_blocked", "observed": iso(clock()), "reason": str(e)})
                                second_stopped = True
            return row
        except Blocked as e:
            with lock(fd, "writer.lock", blocking=True):
                append(fd, rows, {"kind": "blocked", "observed": iso(clock()), "reason": str(e)})
            raise
        finally:
            pool.shutdown(wait=True)


def quantiles(items):
    return {"n": len(items), "median_bp": float(np.median(items)) if items else None,
            "p90_bp": float(np.percentile(items, 90)) if items else None}


def venue_counts(rows, f, fees, line):
    visits = market_rows(rows)
    done = [w for w in visits if w["kind"] == "wake"]
    second = line == SECOND
    market = (lambda w: w[SECOND]) if second else (lambda w: w)
    primary = f"{line}:main"
    reference = fees["flat"] * 10000
    places = {}
    for size in f["bankroll_usd"]:
        key = f"{line}:{size}"
        reports = [w["orders"][key] for w in done]
        places[size] = {name: sum(len(r[name]) if isinstance(r[name], list) else r[name] for r in reports)
                        for name in ("orders", "fills", "under", "minimum_unknown", "quote_missing",
                                     "void_buys", "queued_sells", "pair_unavailable", "venue_unavailable")}
        places[size]["delayed_sells"] = sum(r["delayed_sells"] for r in reports)
    spreads, side = {}, {"buy": [], "sell": []}
    for w in done:
        for k in w["orders"][primary]["orders"]:
            q = market(w)["quotes"].get(k)
            if q:
                spreads.setdefault(k, []).append(10000 * (q["ask"] - q["bid"]) / (q["ask"] + q["bid"]))
        for fill in w["orders"][primary]["fills"]:
            q = market(w)["quotes"][fill["coin"]]
            midpoint = (q["ask"] + q["bid"]) / 2
            direction = fill["side"]
            ratio = (q["ask"] if direction == "buy" else q["bid"]) / midpoint
            fee = second_fee(f, fill["coin"]) if second else fees["quote"]
            side[direction].append(10000 * (abs(ratio - 1) + ratio * fee))
    cost = {s: quantiles(v) for s, v in side.items()}
    for value in cost.values():
        value["median_minus_flat_bp"] = None if value["median_bp"] is None else value["median_bp"] - reference
        value["p90_minus_flat_bp"] = None if value["p90_bp"] is None else value["p90_bp"] - reference
    marker = "second_blocked" if second else "blocked"
    block = next((x["reason"] for x in rows if x["kind"] == marker), None)
    late = sum(market(w)["late"] for w in done)
    unavailable = sum(market(w).get("status") != "OBSERVED" for w in done) if second else 0
    return {"label": SECOND_LABEL if second else "main book, Coinbase quotes",
            "status": ("BLOCKED" if block else "NO_DECISION_FEED" if second and any(
                x["kind"] == "blocked" for x in rows) else "STARTED" if rows else "NOT_STARTED"),
            "block_reason": block, "unavailable_observations": unavailable,
            "coin_quote_page_failures": sum(
                list(market(w).get("quote_failures", {}).values()).count("PAGE_UNAVAILABLE") for w in done)
                + sum(list(r.get("quote_failures", {}).values()).count("PAGE_UNAVAILABLE") for r in rows
                      if r["kind"] == ("second_follow" if second else "follow")),
            "coin_candle_page_failures": 0 if second else sum(len(w.get("candle_failures", {})) for w in visits),
            "wakes": len(done), "void_wakes": sum(w["kind"] == "void" for w in visits) + late,
            "missed_wakes": sum(w["kind"] == "void" for w in visits), "late_wakes": late,
            "placeability": places, "half_spread_by_coin": {k: quantiles(v) for k, v in sorted(spreads.items())},
            "all_in_cost_by_side": cost, "flat_reference_bp": reference,
            "follow_observations": sum(len(r["quotes"]) for r in rows
                                       if r["kind"] == ("second_follow" if second else "follow"))}


def counts(rows, f, fees):
    return {"card": "E10", "coinbase_vs_second_feed": "NOT_MEASURED",
            "coinbase": venue_counts(rows, f, fees, "quote"), SECOND: venue_counts(rows, f, fees, SECOND)}


def alive(folder=OFF):
    f, _, _, fees = settings()
    if not folder.exists():
        return counts([], f, fees)
    with private(folder) as fd, lock(fd, "writer.lock", blocking=True):
        rows = read_log(fd)
        if rows:
            checked(rows)
        return counts(rows, f, fees)


def publish(folder=OFF, path=PUBLIC):
    result = alive(folder)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def periods(tape, idx, nav, gross_btc, fee):
    def metrics(lo, hi):
        prior = nav[lo - 1]
        sub = nav[lo:hi] / prior
        dd = float(np.max(1 - sub / np.maximum.accumulate(np.maximum(sub, 1))))
        stats = {"net": float(sub[-1] - 1), "largest_fall": dd,
                 "matched_btc": None, "btc_scale": None}
        if gross_btc is not None and len(sub) >= 2:
            underlying = gross_btc[lo-idx:hi-idx]
            before = gross_btc[lo-idx-1] if lo != idx else 1.
            stats["matched_btc"], stats["btc_scale"] = core.matched_btc(
                underlying / before, [(0, 0, 1., 0.)] if lo == idx else [], sub, fee)
        return stats

    stop = len(tape.days) - 1  # the final collector wake supplies the preceding close only
    groups = {}
    for i in range(idx, stop):
        day = tape.days[i]
        groups.setdefault(f"{day.year}-Q{(day.month-1)//3+1}", []).append(i)
    return {"whole": metrics(idx, stop), "calendar_quarters": {q: metrics(ix[0], ix[-1]+1) for q, ix in groups.items()}}


def score(now, folder=OFF):
    f, rule, marks, fees = settings()
    with private(folder) as fd, lock(fd, "writer.lock"):
        rows = read_log(fd)
        checked(rows)
        need(not any(r["kind"] == "score" for r in rows), "score already read")
        visits = market_rows(rows)
        initial = next((r for r in visits if r["kind"] == "wake"), None)
        need(initial is not None, "not yet: no first wake")
        first = parse(initial["wake"])
        need(now >= max(first + timedelta(days=f["score_days"]),
                        parse(initial["observed"]) + timedelta(days=f["score_days"])),
             "not yet: forward year incomplete")
        need(visits and visits[-1]["kind"] == "close", "final closing observation missing")
        reference = f["reference_coin"]
        result, second = {}, {"label": SECOND_LABEL}
        second["status"] = ("INCOMPLETE_VENUE_BLOCKED" if any(r["kind"] == "second_blocked" for r in rows)
                            else "RECORD_NOT_VERDICT")
        for line in (*fees, SECOND):
            if line == SECOND and not any(r.get(SECOND, {}).get("quotes") for r in visits):
                second["status"] = ("UNSCORABLE_VENUE_BLOCKED" if second["status"] == "INCOMPLETE_VENUE_BLOCKED"
                                    else "UNSCORABLE_NO_QUOTES")
                second["record"] = None
                continue
            market = initial[SECOND] if line == SECOND else initial
            q = market["quotes"].get(reference)
            benchmark_ask = q["ask"] if q and q["timely"] else None
            fee = second_fee(f, reference) if line == SECOND else fees[line]
            tape, _, book, _, _, _, _ = run_book(rows, f, rule, marks, fees, line, f["bankroll_usd"]["main"])
            idx = tape.days.index(first.date())
            close = tape.closes[idx:-1, tape.names.index(reference)]
            gross = close / benchmark_ask if benchmark_ask and np.isfinite(close).all() else None
            metrics = periods(tape, idx, book.nav, gross, fee)
            metrics["stale_coin_day_marks"] = int(np.count_nonzero(
                (book.weights[idx:-1] > 0).any(axis=2) & ~np.isfinite(tape.closes[idx:-1])))
            if line == SECOND:
                second["record"] = metrics
            else:
                result[line] = metrics
        out = {"label": "RECORD_NOT_VERDICT", "lines": result, SECOND: second}
        append(fd, rows, {"kind": "score", "read": iso(now), "result_sha256": digest(out)})
        return out


def loop(folder=OFF):
    f, _, _, _ = settings()
    with private(folder) as fd, lock(fd, "loop.lock"):
        with lock(fd, "writer.lock", blocking=True):
            checked(read_log(fd), recording=True)
        while True:
            try:
                row = record(now_utc(), folder=folder)
                if row and row["kind"] == "close":
                    return
            except Blocked:
                raise
            except (Refuse, OSError):
                print("observation unavailable", flush=True)
            with lock(fd, "writer.lock", blocking=True):
                if any(r["kind"] == "close" for r in read_log(fd)):
                    return
            t = now_utc()
            nxt = midnight(t) + timedelta(days=1, seconds=f["wake_delay_s"])
            time.sleep(max(0, (nxt-t).total_seconds()))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=("plan", "start", "record", "loop", "alive", "publish", "score"))
    command = cli.parse_args().command
    try:
        if command == "plan":
            f, rule, _, fees = settings()
            output = {"forward": f, "rule": rule, "fees": fees, "coins": NAMES}
        elif command == "start":
            row = start(now_utc())
            output = {"first": row["first"], "freeze": row["freeze"]}
        elif command == "record":
            row = record(now_utc())
            output = {"status": row["kind"], "wake": row["wake"]} if row else {"status": "nothing due"}
        elif command == "loop":
            loop()
            return 0
        elif command == "alive":
            output = alive()
        elif command == "publish":
            output = publish()
        else:
            output = score(now_utc())
        print(json.dumps(output, sort_keys=True, allow_nan=False))
        return 0
    except (Refuse, core.Refusal, OSError) as e:
        print(f"REFUSED {type(e).__name__}" if isinstance(e, OSError) else f"REFUSED {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
