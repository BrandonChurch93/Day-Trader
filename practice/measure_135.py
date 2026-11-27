"""Ledger 236: once-only spot book costs, for two calm night hours only."""

import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import fcntl
import http.client
import json
import os
from pathlib import Path
import signal
import stat
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


# Copied from the public practice/venue_binance_us.py COINS used by M134.
COINS = tuple("AAVE ADA AVAX BCH BNB BTC DOGE DOT ETH HBAR LINK LTC NEAR PEPE SHIB SOL SUI XLM XRP ZEC".split())
SIZES = (25, 250, 1000)
SIDES = ("buy", "sell")
MINUTES = (20, 30, 40, 50)
WINDOW = (18, 56)
FEE_BP = 2
HEADLINE_BP = 25
DEPTH = 100
TIMEOUT_S = 5
MAX_BYTES = 1024 * 1024
ENDPOINT = "https://api.binance.us/api/v3/depth"
OFF = Path("/home/user/workspace/rig/data/measure_135")
RAW_NAME = "books.jsonl"
LIMITATION = "Reading of two calm night hours only, not a midnight UTC benchmark or a reading of fast markets."


class Refuse(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def now_utc():
    return datetime.now(timezone.utc)


def utc(t):
    if t.utcoffset() is None:
        raise Refuse("clock must supply an aware UTC time")
    return t.astimezone(timezone.utc)


def iso(t):
    return utc(t).isoformat().replace("+00:00", "Z")


def slots(started):
    """Choose the first intact two-hour block with at least 60 s notice."""
    now = utc(started)
    hour = now.replace(minute=0, second=0, microsecond=0)
    if hour + timedelta(minutes=MINUTES[0]) < now + timedelta(seconds=60):
        hour += timedelta(hours=1)
    return tuple(hour + timedelta(hours=h, minutes=m) for h in range(2) for m in MINUTES)


def in_window(when):
    return WINDOW[0] <= utc(when).minute <= WINDOW[1]


def check_window(when, slot):
    if not in_window(when):
        raise Refuse("outside the UTC minute 18 to 56 request window")
    if not slot <= utc(when) < slot + timedelta(minutes=1):
        raise Refuse("outside the scheduled snapshot minute; no catch-up")


def wait_for(slot, clock, sleep):
    while True:
        now = utc(clock())
        if now >= slot:
            check_window(now, slot)
            return
        sleep(min(1, (slot - now).total_seconds()))


def public_opener():
    return build_opener(ProxyHandler({}), NoRedirect())


@contextmanager
def response_budget():
    def timed_out(_number, _frame):
        raise TimeoutError("response budget expired")

    previous = signal.signal(signal.SIGALRM, timed_out)
    signal.setitimer(signal.ITIMER_REAL, TIMEOUT_S)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


class DepthClient:
    def __init__(self, opener, clock=now_utc, monotonic=time.monotonic, sleep=time.sleep):
        self.opener, self.clock, self.monotonic, self.sleep = opener, clock, monotonic, sleep
        self.last_finish = None

    def book(self, coin, slot):
        if coin not in COINS:
            raise Refuse("unknown USD symbol")
        check_window(self.clock(), slot)
        req = Request(ENDPOINT + "?" + urlencode({"symbol": coin + "USD", "limit": DEPTH}),
                      headers={"Accept": "application/json", "User-Agent": "usd-book-spot-check/1.0"},
                      method="GET")
        while True:
            left = 0 if self.last_finish is None else 1 - (self.monotonic() - self.last_finish)
            if left <= 0:
                break
            self.sleep(min(1, left))
        try:
            with response_budget():
                check_window(self.clock(), slot)
                with self.opener.open(req, timeout=TIMEOUT_S) as response:
                    if response.status != 200:
                        raise Refuse(f"{coin}USD: HTTP {response.status}")
                    body = response.read(MAX_BYTES + 1)
        except HTTPError as exc:
            exc.close()
            raise Refuse(f"{coin}USD: HTTP {exc.code}") from None
        except (URLError, OSError, http.client.HTTPException) as exc:
            cause = exc.reason if isinstance(exc, URLError) else exc
            reason = "timeout" if isinstance(cause, TimeoutError) else "transport failure"
            raise Refuse(f"{coin}USD: {reason}") from None
        finally:
            # A full second after the prior reply is conservative even if the
            # process stalled between its clock check and the actual send.
            self.last_finish = self.monotonic()
        received = utc(self.clock())
        check_window(received, slot)
        try:
            if len(body) > MAX_BYTES:
                raise ValueError("oversize reply")
            raw = json.loads(body, parse_constant=reject_constant)
            metrics = stored_metrics(*book_metrics(raw))
        except (ValueError, TypeError, ArithmeticError, RecursionError):
            raise Refuse(f"{coin}USD: malformed book") from None
        return received, raw, metrics


def reject_constant(value):
    raise ValueError(f"nonfinite JSON constant: {value}")


def number(value):
    if not isinstance(value, str):
        raise ValueError("prices and amounts must be strings")
    parsed = Decimal(value)
    if (not parsed.is_finite() or parsed <= 0 or not -50 <= parsed.adjusted() <= 50
            or len(parsed.as_tuple().digits) > 128):
        raise ValueError("invalid price or amount")
    return parsed


def levels(raw, *, descending):
    if not isinstance(raw, list) or not 1 <= len(raw) <= DEPTH:
        raise ValueError("empty or malformed book side")
    out = []
    for item in raw:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("malformed depth level")
        px, qty = map(number, item)
        if out and not (out[-1][0] > px if descending else out[-1][0] < px):
            raise ValueError("unsorted or duplicate depth levels")
        out.append((px, qty))
    return out


def walk(levels_, usd):
    """M134 convention: fix USD notional; return average price, or cannot fill."""
    remaining, base = Decimal(usd), Decimal(0)
    for px, qty in levels_:
        level_usd = px * qty
        if level_usd >= remaining:
            if base == 0:
                return px
            return Decimal(usd) / (base + remaining / px)
        base += qty
        remaining -= level_usd
    return None


def book_metrics(raw):
    if not isinstance(raw, dict) or "bids" not in raw or "asks" not in raw or raw.get("auction_mode"):
        raise ValueError("malformed or auction book")
    bids, asks = levels(raw["bids"], descending=True), levels(raw["asks"], descending=False)
    bid, ask = bids[0][0], asks[0][0]
    if bid >= ask:
        raise ValueError("crossed or locked book")
    mid = (bid + ask) / 2
    gap = (ask - bid) * 10_000 / mid
    costs = {}
    for size in SIZES:
        costs[size] = {}
        for side, depth, sign in (("buy", asks, 1), ("sell", bids, -1)):
            fill = walk(depth, size)
            costs[size][side] = None if fill is None else sign * (fill - mid) * 10_000 / mid
    return gap, costs


def stored_metrics(gap, costs):
    return {"quoted_gap_bp": str(gap), "sizes_usd": {
        str(size): {side: {"status": "cannot_fill"} if value is None
                    else {"status": "ok", "cost_bp": str(value)}
                    for side, value in sides.items()}
        for size, sides in costs.items()}}


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def journal(off, *, create=False):
    off = Path(off).absolute()
    if off.name != OFF.name or any(path.is_symlink() for path in (off, *off.parents)):
        raise Refuse("observation directory must be the private, non-symlink Measurement 135 directory")
    if any((path / ".git").exists() or (path / ".git").is_symlink() for path in (off, *off.parents)):
        raise Refuse("raw books cannot be stored in a Git working tree")
    if create:
        try:
            off.mkdir(mode=0o700)
        except FileExistsError:
            pass
        else:
            fsync_dir(off.parent)
    st = off.stat()
    if not stat.S_ISDIR(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o700 or st.st_uid != os.geteuid():
        raise Refuse("private observation directory must be owned and mode 0700")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL if create else os.O_RDONLY
    try:
        fd = os.open(off / RAW_NAME, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    except FileExistsError:
        raise Refuse("Measurement 135 already attempted; a second run needs a new ledger row") from None
    with os.fdopen(fd, "w" if create else "r", encoding="utf-8") as stream:
        st = os.fstat(stream.fileno())
        if (not stat.S_ISREG(st.st_mode) or stat.S_IMODE(st.st_mode) != 0o600
                or st.st_uid != os.geteuid() or st.st_nlink != 1):
            raise Refuse("private journal must be an owned, single-link 0600 file")
        try:
            fcntl.flock(stream.fileno(), (fcntl.LOCK_EX if create else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refuse("Measurement 135 is still running") from None
        if create:
            fsync_dir(off)
        yield stream


def append(stream, **row):
    stream.write(json.dumps(row, separators=(",", ":"), allow_nan=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def capture(off, client, clock, sleep):
    started = utc(clock())
    selected = slots(started)
    with journal(off, create=True) as stream:
        append(stream, kind="header", started=iso(started), slots=[iso(s) for s in selected], symbols=list(COINS))
        current = None
        try:
            for current in selected:
                wait_for(current, clock, sleep)
                for coin in COINS:
                    received, raw, metrics = client.book(coin, current)
                    append(stream, kind="book", slot=iso(current), symbol=coin, received=iso(received),
                           raw=raw, measured=metrics)
        except Refuse as exc:
            append(stream, kind="stop", slot=iso(current) if current else None, reason=str(exc))
            raise
        except KeyboardInterrupt:
            append(stream, kind="stop", slot=iso(current) if current else None, reason="interrupted")
            raise
        append(stream, kind="complete")


def median(values):
    ordered = sorted(values)
    if not ordered:
        return None
    n = len(ordered)
    return (ordered[(n - 1) // 2] + ordered[n // 2]) / 2


def numeric(value):
    return None if value is None else float(value)


def summarize(rows):
    if not rows or rows[0].get("kind") != "header" or rows[0].get("symbols") != list(COINS):
        raise Refuse("invalid private journal header")
    snapshots = rows[0]["slots"]
    if snapshots != [iso(s) for s in slots(datetime.fromisoformat(rows[0]["started"]))]:
        raise Refuse("invalid private journal schedule")
    books, counts, missing = set(), Counter(), Counter()
    gap = {coin: [] for coin in COINS}
    collected = {(coin, size, side): [] for coin in COINS for size in SIZES for side in SIDES}
    status = "incomplete"
    detail = None
    for row in rows[1:]:
        kind = row.get("kind")
        if status != "incomplete":
            raise Refuse("data encountered after the terminal journal row")
        if kind == "stop":
            status, detail = "stopped", row["reason"]
            continue
        if kind == "complete":
            if len(books) != len(snapshots) * len(COINS):
                raise Refuse("complete journal is missing books")
            status = "complete"
            continue
        coin, slot = row.get("symbol"), row.get("slot")
        if kind != "book" or coin not in gap or slot not in snapshots or (coin, slot) in books:
            raise Refuse("invalid or duplicate private observation")
        check_window(datetime.fromisoformat(row["received"]), datetime.fromisoformat(slot))
        books.add((coin, slot))
        counts[slot] += 1
        gap_bp, costs = book_metrics(row["raw"])
        if row["measured"] != stored_metrics(gap_bp, costs):
            raise Refuse("private book and recorded measurements disagree")
        gap[coin].append(gap_bp)
        for size in SIZES:
            for side, result in costs[size].items():
                if result is None:
                    missing[coin, size, side] += 1
                else:
                    collected[coin, size, side].append(result)
    mids = {key: median(values) for key, values in collected.items()}
    coin_costs, headlines = {}, {}
    for size in SIZES:
        worst = []
        for coin in COINS:
            values = {side: mids[coin, size, side] for side in SIDES}
            worse = max(values.values()) if all(v is not None for v in values.values()) else None
            if worse is not None:
                worst.append(worse)
            coin_costs.setdefault(coin + "USD", {})[size] = {
                "median_buy_bp": numeric(values["buy"]), "median_sell_bp": numeric(values["sell"]),
                "worse_side_median_bp": numeric(worse),
                "cannot_fill": {s: missing[coin, size, s] for s in SIDES}}
        headlines[size] = {
            "coins_at_or_below_25_bp": sum(v <= HEADLINE_BP for v in worst),
            "coins_with_both_side_medians": len(worst), "coins_total": len(COINS),
            "across_coins_median_worse_side_bp": numeric(median(worst)),
            "cannot_fill": {s: sum(missing[c, size, s] for c in COINS) for s in SIDES}}
    return {
        "status": status, "stop_reason": detail, "scope": LIMITATION,
        "stated_fee_bp_per_side_not_in_costs": FEE_BP, "snapshots_planned": len(snapshots),
        "snapshots_taken": len(counts), "snapshots_complete": sum(n == len(COINS) for n in counts.values()),
        "books_taken": len(books), "by_size_usd": headlines,
        "by_symbol": {c + "USD": {"median_gap_bp": numeric(median(gap[c])), "costs_by_size_usd": coin_costs[c + "USD"]}
                      for c in COINS}}


def report(off):
    with journal(off) as stream:
        try:
            return summarize([json.loads(line, parse_constant=reject_constant) for line in stream])
        except (ValueError, KeyError, TypeError, AttributeError, ArithmeticError, RecursionError):
            raise Refuse("invalid private journal; no figures printed") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "report"))
    command = parser.parse_args().command
    os.umask(0o077)
    try:
        if command == "run":
            capture(OFF, DepthClient(public_opener()), now_utc, time.sleep)
        print(json.dumps(report(OFF), indent=2, sort_keys=True, allow_nan=False))
    except Refuse as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"REFUSED: private journal I/O: {exc.strerror or type(exc).__name__}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
