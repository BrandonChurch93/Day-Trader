"""Plan 74 offline custody guards and synthetic-only signal replay."""

import csv
import hashlib
import io
import json
import math
import mmap
import os
import re
import stat
import struct
import subprocess
import sys
from bisect import bisect_right
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, time
from fractions import Fraction
from pathlib import Path
from statistics import fmean
from tempfile import TemporaryFile
from zoneinfo import ZoneInfo

from count_74 import (ARMS, ROOT, Bar, CloseView, Prefix, Refusal, branches, close_signals,
                      config, count_lines, count_signals, in_fence, market, require, trailing_ema)


DESIGN_DIR = Path("/home/user/workspace/rig/data/plan_74_design")
LEDGER = "research_rig/TRIAL_LEDGER.md"
HASH = re.compile(r"[a-f0-9]{64}\Z")
ID = re.compile(r"[A-Za-z0-9._:-]+\Z")
BAR = struct.Struct("<ddddd")
NAMES = {"calendar.csv", "identity.json", "bars_index.csv", "bars.f64", "source_receipt.json"}
# Resource limits for the transport schema, not trading settings.
SMALL_FILE = 64 * 1024
META_FILE = 64 * 1024 * 1024
CHUNK = 1024 * 1024
BP_PER_UNIT = 10_000
EASTERN = ZoneInfo("America/New_York")


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def unique(pairs):
    result = dict(pairs)
    require(len(result) == len(pairs), "REFUSE_JSON")
    return result


def read_json(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=lambda _: _bad_json())


def _bad_json():
    raise Refusal("REFUSE_JSON")


def digest(s):
    return isinstance(s, str) and HASH.fullmatch(s) is not None


@contextmanager
def private_folder(folder):
    require(folder.is_absolute() and ".." not in folder.parts, "REFUSE_DIR")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in folder.parts[1:]:
            new = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        info = os.fstat(fd)
        require(info.st_uid == os.geteuid() and info.st_mode & 0o077 == 0, "REFUSE_PRIVATE_DIR")
        yield fd
    finally:
        os.close(fd)


@contextmanager
def open_private(fd, name, limit):
    child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    with os.fdopen(child, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                and info.st_uid == os.geteuid() and info.st_mode & 0o077 == 0
                and info.st_size <= limit, "REFUSE_FILE")
        yield stream, info.st_size


def small_bytes(fd, name, limit):
    with open_private(fd, name, limit) as (stream, size):
        blob = stream.read(limit + 1)
        require(len(blob) == size, "REFUSE_SIZE")
        return blob


def approved_id(ledger, stage="DESIGN"):
    rows = re.findall(r"^\|[ \t]*226[ \t]*\|[^\r\n]*$", ledger, flags=re.M)
    require(len(rows) == 1, "REFUSE_LEDGER_ROW")
    prefix = {"DESIGN": "p74d", "COUNT": "p74c"}[stage]
    key = f"P74_{stage}_GO"
    keys = re.findall(r"(?<![A-Za-z0-9_])" + key + r"\s*=", rows[0])
    ids = re.findall(r"(?<![A-Za-z0-9_])" + key + f"=({prefix}-[a-f0-9]{{64}})" + r"(?=[\s`|]|$)", rows[0])
    require(len(keys) == len(ids) == 1, "REFUSE_LEDGER_GO")
    return ids[0]


def committed_approval(root=ROOT, *, stage="DESIGN"):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull

    def git(*args):
        proc = subprocess.run(("git", "-c", "core.fsmonitor=false", *args),
                              cwd=root, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, check=False)
        require(proc.returncode == 0, "REFUSE_GIT")
        return proc.stdout.decode()

    commit = git("rev-parse", "--verify", "HEAD").strip()
    require(re.fullmatch(r"[a-f0-9]{40,64}", commit), "REFUSE_GIT")
    tracked = git("ls-files", "-v", "-z").split("\0")
    require(all(not x or x.startswith("H ") for x in tracked), "REFUSE_DIRTY")
    require(not git("status", "--porcelain", "--untracked-files=no"), "REFUSE_DIRTY")
    approval = approved_id(git("show", f"{commit}:{LEDGER}"), stage)
    require(git("rev-parse", "--verify", "HEAD").strip() == commit, "REFUSE_GIT")
    return commit, approval


def receipt_pin(fd, approval):
    data = read_json(small_bytes(fd, "design_receipt.json", SMALL_FILE))
    require(isinstance(data, dict) and set(data) == {"schema", "go_id", "manifest_sha256"}
            and type(data["schema"]) is int and data["schema"] == 1
            and digest(data["manifest_sha256"]), "REFUSE_RECEIPT")
    pin = data["manifest_sha256"]
    require(data["go_id"] == approval == "p74d-" + pin, "REFUSE_GO_MISMATCH")
    return pin


def table(data, fields):
    lines = csv.reader(io.StringIO(data.decode("ascii"), newline=""), strict=True)
    require(next(lines, None) == list(fields), "REFUSE_INDEX")
    for row in lines:
        require(len(row) == len(fields), "REFUSE_INDEX")
        yield row


def iso(s):
    day = date.fromisoformat(s)
    require(day.isoformat() == s, "REFUSE_CLOCK")
    return day


def acceptance(s):
    stamp = datetime.fromisoformat(s)
    require(stamp.tzinfo is not None and stamp.utcoffset() is not None, "REFUSE_CLOCK")
    local = stamp.astimezone(EASTERN)
    require(local.isoformat() == stamp.isoformat(), "REFUSE_CLOCK")
    return local


def exchange_close(s, day):
    require(re.fullmatch(r"[0-9]{2}:[0-9]{2}", s), "REFUSE_CLOCK")
    return datetime.combine(day, time.fromisoformat(s), EASTERN)


def identity_register(data, cfg):
    obj = read_json(data)
    require(isinstance(obj, dict) and set(obj) == {"schema", "securities"}
            and type(obj["schema"]) is int and obj["schema"] == 1
            and isinstance(obj["securities"], list), "REFUSE_IDENTITY")
    fields = {"id", "kind", "ticker_intervals", "cusips", "registration_date", "delisted",
              "delist_effective", "eligibility_intervals", "splits", "quarter_first_202",
              "share_counts", "halts"}
    names = {}
    last = iso(cfg["design_last"])

    def dated(day):
        require(iso(day) <= last, "REFUSE_FENCE")

    def nested(rows, keys, dates):
        for item in rows:
            require(isinstance(item, dict) and set(item) == keys, "REFUSE_IDENTITY")
            for k in dates:
                dated(item[k])

    for row in obj["securities"]:
        require(isinstance(row, dict) and set(row) == fields and isinstance(row["id"], str)
                and ID.fullmatch(row["id"]) and row["id"] not in names
                and row["kind"] in {"stock", "fund"} and type(row["delisted"]) is bool
                and (row["delist_effective"] is not None) == row["delisted"], "REFUSE_IDENTITY")
        for key in fields - {"id", "kind", "registration_date", "delisted", "delist_effective"}:
            require(type(row[key]) is list, "REFUSE_IDENTITY")
        for key in ("delist_effective", "registration_date"):
            if row[key] is not None:
                dated(row[key])
        require(all(isinstance(c, str) and c for c in row["cusips"]), "REFUSE_IDENTITY")
        nested(row["ticker_intervals"], {"ticker", "venue", "first", "last", "asof"},
               ("first", "last", "asof"))
        for k in ("eligibility_intervals", "halts"):
            nested(row[k], {"first", "last", "evidence"}, ("first", "last"))
        nested(row["splits"], {"ex_date", "announcement_date", "new_shares", "old_shares"},
               ("ex_date", "announcement_date"))
        nested(row["quarter_first_202"], {"quarter", "accepted_et", "accession"}, ("quarter",))
        nested(row["share_counts"], {"filed_date", "basis_date", "accepted_et", "report_date",
                                     "shares", "accession"}, ("filed_date", "basis_date", "report_date"))
        for earning in row["quarter_first_202"]:
            if earning["accepted_et"] is not None:
                dated(acceptance(earning["accepted_et"]).date().isoformat())
        for share in row["share_counts"]:
            require(type(share["shares"]) is int and share["shares"] > 0, "REFUSE_IDENTITY")
            dated(acceptance(share["accepted_et"]).date().isoformat())
        for split in row["splits"]:
            require(all(type(split[k]) is int and split[k] > 0 for k in ("new_shares", "old_shares")),
                    "REFUSE_IDENTITY")
        names[row["id"]] = row
    a = cfg["signal_rules"]["A"]
    funds = set(cfg["benchmark"].values()) | {cfg["arm_52w"]["market_fund"], a["ema_fund"], a["sma_fund"]}
    require(all(name in names and names[name]["kind"] == "fund" for name in funds), "REFUSE_IDENTITY")
    return names


def load_snapshot(fd, pin, cfg, copy=None):
    """Read no numeric bar value. If requested, keep exactly the hashed bytes."""
    require(digest(pin), "REFUSE_PIN")
    raw = small_bytes(fd, "manifest.json", SMALL_FILE)
    require(sha(raw) == pin, "REFUSE_PIN")
    m = read_json(raw)
    require(isinstance(m, dict) and set(m) == {"schema", "warmup_first", "design_first",
                                             "design_last", "rows", "sha256"}
            and type(m["schema"]) is int and m["schema"] == 1
            and type(m["rows"]) is int and m["rows"] > 0, "REFUSE_MANIFEST")
    for k in ("warmup_first", "design_first", "design_last"):
        require(m[k] == cfg[k], "REFUSE_FENCE")
    hashes = m["sha256"]
    require(isinstance(hashes, dict) and set(hashes) == NAMES
            and all(digest(x) for x in hashes.values()), "REFUSE_HASH")

    def checked(name):
        data = small_bytes(fd, name, META_FILE)
        require(sha(data) == hashes[name], "REFUSE_HASH")
        return data

    receipt = read_json(checked("source_receipt.json"))
    require(isinstance(receipt, dict) and set(receipt) == {"schema", "source_pins", "review_id"}
            and type(receipt["schema"]) is int and receipt["schema"] == 1
            and isinstance(receipt["source_pins"], dict) and receipt["source_pins"]
            and all(digest(x) for x in receipt["source_pins"].values())
            and isinstance(receipt["review_id"], str) and receipt["review_id"], "REFUSE_SOURCE_RECEIPT")
    calendar = tuple((iso(day), clock) for day, clock in
                     table(checked("calendar.csv"), ("session", "close_et")))
    days = tuple(d for d, _ in calendar)
    closes = tuple(exchange_close(c, d) for d, c in calendar)
    require(days and days[0] == iso(cfg["warmup_first"]) and days[-1] == iso(cfg["design_last"])
            and iso(cfg["design_first"]) in days and all(a < b for a, b in zip(days, days[1:])),
            "REFUSE_FENCE")
    names = identity_register(checked("identity.json"), cfg)
    seen = set()
    offset, prior = 0, ("", -1)
    segments = []
    for name, first, rows in table(checked("bars_index.csv"), ("id", "first_session_index", "rows")):
        require(name in names and first.isascii() and first.isdecimal()
                and rows.isascii() and rows.isdecimal(), "REFUSE_INDEX")
        start, length = int(first), int(rows)
        require(length and start + length <= len(days) and (name, start) > prior, "REFUSE_INDEX")
        segments.append((name, start, length, offset))
        seen.add(name)
        prior = name, start + length - 1
        offset += length
    require(seen == set(names) and offset == m["rows"], "REFUSE_ROWS")
    expected = BAR.size * offset
    require(expected <= cfg["disk_cap_gib_compressed"] * 1024 ** 3, "REFUSE_SIZE")
    with open_private(fd, "bars.f64", expected) as (stream, size):
        require(size == expected, "REFUSE_SIZE")
        h = hashlib.sha256()
        copied = 0
        while (block := stream.read(CHUNK)):
            copied += len(block)
            require(copied <= expected, "REFUSE_SIZE")
            h.update(block)
            if copy is not None:
                copy.write(block)
        require(copied == expected and h.hexdigest() == hashes["bars.f64"], "REFUSE_HASH")
    if copy is not None:
        copy.seek(0)
    return days, closes, names, segments


def required_benchmark_prints(layout, cfg):
    days, _, _, segments = layout
    funds = set(cfg["benchmark"].values())
    design_first = iso(cfg["design_first"])
    possible = range(bisect_right(days, design_first), len(days))
    for fund in sorted(funds):
        present = {i for name, start, length, _ in segments if name == fund
                   for i in range(start, start + length)}
        missing = [days[i].isoformat() for i in possible if i not in present]
        require(not missing, "REFUSE_BENCHMARK_MISSING " + " ".join(missing))


def new_file(fd, name, blob):
    try:
        child = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600, dir_fd=fd)
    except FileExistsError:
        raise Refusal("REFUSE_LOCK") from None
    with os.fdopen(child, "wb") as stream:
        stream.write(blob)
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(fd)


def require_unlocked(fd, name):
    try:
        os.stat(name, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise Refusal("REFUSE_LOCK")


def claimed_snapshot(fd, current, before, pin, cfg, lock_name, decoder):
    with TemporaryFile(dir=fd_path(fd)) as opaque:
        layout = load_snapshot(fd, pin, cfg, opaque)
        if lock_name == "RUN.lock":
            required_benchmark_prints(layout, cfg)
        require(current() == before, "REFUSE_GIT")
        new_file(fd, lock_name, (before[1] + "\n").encode("ascii"))
        return decoder(layout, opaque, cfg)


def guarded_run(fd, current, cfg, *, decoder=None):
    """The decoder sees only pinned bytes after the irreversible lock."""
    require_unlocked(fd, "RUN.lock")
    before = current()
    pin = receipt_pin(fd, before[1])
    expected = completed_count(fd, pin)
    if decoder is None:
        def decoder(layout, opaque, plan):
            return decode_design(layout, opaque, plan, expected)
    return claimed_snapshot(fd, current, before, pin, cfg, "RUN.lock", decoder)


def completed_count(fd, pin):
    try:
        locked = small_bytes(fd, "COUNT.lock", SMALL_FILE)
        result = read_json(small_bytes(fd, "COUNT.receipt.json", SMALL_FILE))
    except (FileNotFoundError, ValueError, TypeError, RecursionError):
        raise Refusal("REFUSE_COUNT_NOT_COMPLETE") from None
    go = "p74c-" + pin
    require(locked == (go + "\n").encode("ascii") and isinstance(result, dict)
            and set(result) == {"schema", "go_id", "count_lines"}
            and type(result["schema"]) is int and result["schema"] == 1
            and result["go_id"] == go and isinstance(result["count_lines"], list)
            and all(isinstance(x, str) and "\n" not in x for x in result["count_lines"]), "REFUSE_COUNT_NOT_COMPLETE")
    return result["count_lines"]


def guarded_count(fd, current, pin, cfg, *, decoder=None):
    require_unlocked(fd, "COUNT.lock")
    before = current()
    require(digest(pin) and before[1] == "p74c-" + pin, "REFUSE_GO_MISMATCH")
    require_unlocked(fd, "COUNT.receipt.json")
    lines = claimed_snapshot(fd, current, before, pin, cfg, "COUNT.lock", decoder or decode_count)
    body = json.dumps({"schema": 1, "go_id": before[1], "count_lines": lines}).encode("ascii")
    new_file(fd, "COUNT.receipt.json", body)
    return lines


def run_count(pin, cfg):
    def current():
        return committed_approval(stage="COUNT")

    current()
    with private_folder(DESIGN_DIR) as fd:
        return guarded_count(fd, current, pin, cfg)


def fd_path(fd):
    return f"/proc/self/fd/{fd}"


def decode_bar(stream):
    """Interpret a private fixture's raw open/high/low/close/volume."""
    return checked_bar(BAR.unpack(stream.read(BAR.size)))


def checked_bar(values):
    bar = Bar(*values)
    require(all(math.isfinite(v) and v > 0 for v in (bar.open, bar.high, bar.low, bar.close))
            and 0 <= bar.volume < math.inf
            and bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high,
            "REFUSE_BAR")
    return bar


class BarSeries:
    """Segment index plus opaque map; decode one record at a time on demand."""

    def __init__(self, source, length, segments):
        self.source, self.length, self.segments = source, length, segments
        self.starts = [start for start, _, _ in segments]
        self.last = segments[-1][0] + segments[-1][1] - 1

    def __len__(self):
        return self.length

    def present(self, i):
        j = bisect_right(self.starts, i) - 1
        return j >= 0 and i < self.starts[j] + self.segments[j][1]

    def __getitem__(self, i):
        if isinstance(i, slice):
            return tuple(self[j] for j in range(*i.indices(len(self))))
        if i < 0:
            i += len(self)
        if not 0 <= i < len(self):
            raise IndexError(i)
        j = bisect_right(self.starts, i) - 1
        if j < 0:
            return None
        start, size, offset = self.segments[j]
        if i >= start + size:
            return None
        return checked_bar(BAR.unpack_from(self.source, BAR.size * (offset + i - start)))


class AsOf:
    """Compiled filing metadata. No bar prices and no network."""

    def __init__(self, days, closes, data, cfg):
        self.days, self.closes, self.cfg = days, closes, cfg
        self.stocks, self.splits = {}, {}
        for name, row in data.items():
            factors = {}
            for item in row["splits"]:
                day = iso(item["ex_date"])
                i = bisect_right(days, day) - 1
                if i >= 0 and days[i] == day:
                    factors[i] = factors.get(i, 1) * Fraction(item["new_shares"], item["old_shares"])
            if factors:
                self.splits[name] = factors
            if row["kind"] != "stock":
                continue
            eligible = [(iso(x["first"]), iso(x["last"])) for x in row["eligibility_intervals"]]
            earnings = sorted(acceptance(x["accepted_et"]) for x in row["quarter_first_202"]
                              if x["accepted_et"] is not None)
            shares = sorted((iso(x["filed_date"]), acceptance(x["accepted_et"]),
                             iso(x["report_date"]), x["shares"], iso(x["basis_date"]))
                            for x in row["share_counts"])
            split_register = [(iso(x["ex_date"]), iso(x["announcement_date"]),
                               x["new_shares"] / x["old_shares"]) for x in row["splits"]]
            self.stocks[name] = eligible, earnings, shares, split_register

    def at(self, i):
        members, shares, earnings, next_split = set(), {}, set(), set()
        lookback = self.cfg["signal_rules"]["A"]["earnings_sessions"]
        today = self.days[i]
        prev = self.days[i - 1] if i else None
        for name, (eligibility, filings, counts, splits) in self.stocks.items():
            if not any(a <= today <= b for a, b in eligibility):
                continue
            members.add(name)
            if i >= lookback and any(self.closes[i - lookback] < f <= self.closes[i] for f in filings):
                earnings.add(name)
            if prev is not None:
                known = [x for x in counts if x[0] <= prev and x[1].date() <= prev]
                if known:
                    _, _, _, quantity, basis = max(known, key=lambda x: x[1:4])
                    shares[name] = quantity * math.prod(q for day, _, q in splits if basis < day <= prev)
            if i + 1 < len(self.days) and any(day == self.days[i + 1] and announced <= today
                                             for day, announced, _ in splits):
                next_split.add(name)
        return frozenset(members), shares, frozenset(earnings), frozenset(next_split)


@contextmanager
def tape_snapshot(layout, opaque, cfg):
    days, closes, data, segments = layout
    with mmap.mmap(opaque.fileno(), 0, access=mmap.ACCESS_READ) as source:
        by_name = defaultdict(list)
        for name, start, length, offset in segments:
            by_name[name].append((start, length, offset))
        bars = {n: BarSeries(source, len(days), rows) for n, rows in by_name.items()}
        clock = AsOf(days, closes, data, cfg)
        yield Tape(days, bars, {}, {}, {}, clock.splits, {},
                   {n: bars[n].last for n, row in data.items() if row["delisted"]}, clock)


@dataclass(frozen=True)
class Tape:
    days: tuple
    bars: dict
    members: dict
    shares: dict
    earnings: dict
    splits: dict
    next_split_known: dict
    delisted: dict  # independently documented final bar index
    asof: AsOf | None = None

    def view(self, day, *, only=None):
        ids = self.bars if only is None else set(only).intersection(self.bars)
        member, shares, earnings, next_split = (self.asof.at(day) if only is None and self.asof else
            (self.members.get(day, frozenset()), self.shares.get(day, {}), self.earnings.get(day, frozenset()),
             self.next_split_known.get(day, frozenset())))
        return CloseView(self.days[:day + 1], {k: Prefix(self.bars[k], day + 1) for k in ids},
                         member, shares, earnings,
                         {k: {i: f for i, f in v.items() if i <= day} for k, v in self.splits.items()},
                         next_split)

    def scale(self, name, first, last):
        return math.prod(f for i, f in self.splits.get(name, {}).items() if first < i <= last)


@dataclass(frozen=True)
class Leg:
    day: int
    print_kind: str
    reason: str
    shares: float
    value: float  # entry-share basis, before sale friction
    risk: float
    benchmark: float
    recognized: int | None = None
    add_benchmark: float = 0.0


@dataclass(frozen=True)
class Trade:
    day: date
    price: float
    legs: tuple
    added: float = 0.0
    add_price: float = 0.0
    add_day: int | None = None


def entry_terms(tape, signal, cfg):
    name, card, enter = signal.id, signal.card, signal.day + 1
    stock = tape.bars[name]
    if enter >= len(tape.days) or enter in tape.splits.get(name, {}) or stock[enter] is None:
        return None
    actual, line, cap, stop = stock[enter].open, signal.line, signal.maximum, signal.stop
    if not line < actual <= cap:
        return None
    if signal.arm == "52w":
        stop = actual * (1 - cfg["arm_52w"]["stop_share"])
    elif (cap - stop) / cap > cfg["signal_rules"][card]["stop_refusal"]:
        return None
    return actual, line, stop


def last_bar(stock):
    if isinstance(stock, BarSeries):
        return stock.last
    return next((i for i in range(len(stock) - 1, -1, -1) if stock[i] is not None), -1)


def simulate(tape, signal, cfg, *, with_benchmark=True):
    """A single per-signal trade; callers suppress overlap per arm."""
    name, card, enter = signal.id, signal.card, signal.day + 1
    rule = cfg["signal_rules"][card]
    stock, fund = tape.bars[name], cfg["benchmark"][card]
    terms = entry_terms(tape, signal, cfg)
    if terms is None:
        return None
    actual, line, stop = terms
    market_bars = tape.bars.get(fund)
    if with_benchmark:
        require(market_bars is not None and market_bars[enter] is not None, "REFUSE_BENCHMARK")
    legs = []
    raw_risk = actual - stop
    fee = cfg["costs_bp_per_side"][card] / BP_PER_UNIT
    overshoot = cfg["stop_overshoot_share_of_risk"][card]
    adverse_entry = actual * (1 + fee)
    adverse_risk = adverse_entry - (stop - overshoot * raw_risk) * (1 - fee)
    add = cfg["add_rules"]
    a = cfg["signal_rules"]["A"]
    add_on = signal.arm == "one_add"
    added, add_price, order, tried, add_day = 0.0, 0.0, None, False, None
    left, pending, partial = 1.0, None, False
    held, had_gap, last = 0, False, enter
    terminal_bar = last_bar(stock)

    def sale(day, kind, reason, quantity, value, recognized=None):
        market_return = 0.0
        added_return = 0.0
        if with_benchmark:
            bench = market_bars[day]
            require(bench is not None, "REFUSE_BENCHMARK")
            reference = getattr(bench, "close" if kind == "intraday" else kind)
            reference *= tape.scale(fund, enter, day)
            market_return = reference / market_bars[enter].open - 1
            if add_day is not None:
                add_reference = market_bars[add_day]
                require(add_reference is not None, "REFUSE_BENCHMARK")
                added_return = reference / (add_reference.open * tape.scale(fund, enter, add_day)) - 1
        risk = max(0, (actual + added * add_price) / (1 + added) - stop)
        legs.append(Leg(day, kind, reason, quantity, value, risk, market_return, recognized, added_return))

    for day in range(enter, len(tape.days)):
        b = stock[day]
        if b is None:
            had_gap = True
            order = None  # a pending add has no retry at a later open
            if day > terminal_bar:
                reason = "delisted" if name in tape.delisted else "bars_ended"
                sale(last, "close", reason, left, stock[last].close * tape.scale(name, enter, last), day)
                break
            # Card A must still process market switch exits on the exchange calendar.
            if card == "A" and pending != "full":
                if not market(tape.view(day, only=(a["ema_fund"], a["sma_fund"],
                                                   cfg["arm_52w"]["market_fund"])), cfg, signal.arm):
                    pending = "full"
            continue
        held += 1
        last = day
        f = tape.scale(name, enter, day)
        if b.open * f <= stop:
            sale(day, "open", "stop_gap", left, b.open * f)
            break
        if pending == "full":
            sale(day, "open", "close_trigger", left, b.open * f)
            break
        if pending == "partial":
            quantity = rule["partial_share"]
            sale(day, "open", "partial", quantity, b.open * f)
            left -= quantity
            partial = True
            pending = None
        if order is not None:
            revised, maximum, scheduled = order
            if day == scheduled and revised < b.open * f <= maximum:
                add_price = b.open * f
                added = add["max_initial_share"]
                add_day = day
                left += added
                stop = revised
            order = None
        if b.low * f <= stop:
            sale(day, "intraday", "stop_intraday", left, stop)
            break
        view = tape.view(day, only=(name, a["ema_fund"], a["sma_fund"], cfg["arm_52w"]["market_fund"]))
        avg = trailing_ema(view, name, rule["exit_ema_sessions"])
        if ((avg is not None and b.close < avg)
                or held >= cfg["power"]["hold_limit"][card]
                or (card == "A" and not market(view, cfg, signal.arm))
                or (card == "B" and b.close * f < line)):
            pending = "full"
        elif card == "B" and not partial:
            target = (rule["gold_target"] if signal.tag == "Gold"
                      else actual + rule["revival_risk_multiple"] * raw_risk)
            if b.close * f >= target:
                pending = "partial"
        elif (add_on and not tried and added == 0 and add["first_session"] <= day - enter <= add["last_session"]
              and b.close * f >= actual + add["risk_units"] * adverse_risk):
            revised = max(stop, adverse_entry, b.low * f)
            maximum = b.close * f * add["entry_cap"]
            tried = True
            if (maximum - revised) / maximum <= add["stop_refusal"]:
                order = revised, maximum, day + 1
    else:
        require(had_gap, "REFUSE_TERMINAL_HOLD")
        sale(last, "close", "design_fence", left, stock[last].close * tape.scale(name, enter, last),
             len(tape.days) - 1)
    require(math.isclose(sum(leg.shares for leg in legs), 1 + added), "REFUSE_TERMINAL_HOLD")
    return Trade(tape.days[enter], actual, tuple(legs), added, add_price, add_day)


def benchmark_return(trade):
    if trade.added:
        leg = trade.legs[0]
        add_cost = trade.added * trade.add_price
        return (trade.price * leg.benchmark + add_cost * leg.add_benchmark) / (trade.price + add_cost)
    return sum(leg.shares * leg.benchmark for leg in trade.legs)


def excess(trade, bp, overshoot, delist_share):
    cost = bp / BP_PER_UNIT
    value = 0.0
    for leg in trade.legs:
        price = leg.value
        if leg.reason == "stop_intraday":
            price -= leg.risk * overshoot
        if leg.reason in {"delisted", "bars_ended"}:
            price *= delist_share
        value += leg.shares * price
    return (value * (1 - cost) / ((trade.price + trade.added * trade.add_price) * (1 + cost))
            - 1 - benchmark_return(trade))


def cluster_key(day, style):
    if style == "entry_month":
        return day.year, day.month
    if style == "entry_day":
        return day
    require(style == "entry_week", "REFUSE_CLUSTER")
    week = day.isocalendar()
    return week.year, week.week


def cluster_t(rows, style, groups=None):
    if not rows:
        return None
    avg = fmean(x for _, x in rows)
    totals = defaultdict(float)
    for day, x in rows:
        totals[cluster_key(day, style)] += x - avg
    g = len(totals) if groups is None else groups
    require(g >= len(totals), "REFUSE_CLUSTER")
    if g < 2:
        return None
    se = math.sqrt(g / (g - 1) * sum(v * v for v in totals.values())) / len(rows)
    return avg / se if se > 0 else None


def marks(rows, cfg, *, months=None):
    m = cfg["marks"]
    vals = sorted(x for _, x in rows)
    avg = fmean(vals) if vals else None
    groups = defaultdict(list)
    for d, x in rows:
        groups[d.year].append(x)
    positive = sum(fmean(v) > m["mean_above"] for v in groups.values())
    trim = len(vals) - math.ceil(len(vals) * m["trim_top_share"])
    trimmed = fmean(vals[:trim]) if trim > 0 else None
    n, days = len(vals), len({d for d, _ in rows})
    t = cluster_t(rows, cfg["cluster"], months)
    thin = n < m["min_signals"] or days < m["min_entry_days"]
    passed = (not thin and avg is not None and avg > m["mean_above"] and avg >= m["mean_floor"]
              and t is not None and t >= m["min_t"] and enough_years(positive, m)
              and trimmed is not None and trimmed > m["mean_above"])
    return {"signals": n, "entry_days": days, "mean": avg, "t": t, "positive_years": positive,
            "trimmed_mean": trimmed, "trimmed_count": n - trim, "too_thin": thin, "passed": passed,
            **{k: cluster_t(rows, k) for k in cfg["cluster_shown"]}}


def enough_years(positive, m):
    return m["years_positive"] <= positive <= m["years"]


def aggregate(trades, card, cfg, *, months=None):
    cost = cfg["costs_bp_per_side"][card]
    slip = cfg["stop_overshoot_share_of_risk"][card]
    d = cfg["delisted_last_close_share"]

    def line(bp, overshoot, delist):
        return marks([(t.day, excess(t, bp, overshoot, delist)) for t in trades], cfg, months=months)

    main = line(cost, slip, d["primary"])
    docs = sum(any(leg.reason == "delisted" for leg in t.legs) for t in trades)
    undocumented = sum(any(leg.reason == "bars_ended" for leg in t.legs) for t in trades)
    fence = sum(any(leg.reason == "design_fence" for leg in t.legs) for t in trades)
    cases = docs + undocumented
    sides = {str(x): line(cost, slip, x) for x in d["shown"]}
    trigger = cfg["dead_name_coverage"]["forced_half_line"] or (
        bool(trades) and cases / len(trades) > d["share_trigger"])
    passed = main["passed"] and (not trigger or sides[str(d["trigger_line"])]["passed"])
    return {"main": main, "delisted_documented": docs, "bars_ended_undocumented": undocumented,
            "design_fence_exits": fence,
            "coverage_warning": bool(trades) and fence / len(trades) > cfg["design_fence_coverage_warning_share"],
            "delisted_trigger": trigger,
            "delisted_shown": sides, "passed": passed,
            "cost_shown": {str(x): line(x, slip, d["primary"]) for x in cfg["cost_shown_bp_per_side"][card]},
            "overshoot_shown": ({"odd_lots_in": line(cost, cfg["stop_overshoot_shown"]["A_odd_lots_in"],
                                                   d["primary"])} if card == "A" else {})}


def design_candidates(tape, cfg, *, branches_only=False, diagnostics=None):
    last = iso(cfg["design_last"])
    require(tape.days[-1] <= last, "REFUSE_FENCE")
    out, pools = [], {}
    open_cards = set(ARMS) - set(cfg["dead_name_coverage"]["closed_cards"])
    for i, d in enumerate(tape.days):
        allowed = {card for card in open_cards if in_fence(tape.days, i, card, cfg)}
        if not allowed:
            continue
        excluded = None if branches_only else {card: set() for card in ARMS}
        signals, screened = close_signals(tape.view(i), cfg, branches_only=branches_only,
                                         exclusions=excluded,
                                         diagnostics=diagnostics if "A" in allowed else None)
        signals = [s for s in signals if s.card in allowed]
        out.extend(signals)
        if signals and excluded is not None:
            for card in {s.card for s in signals}:
                pools[card, i] = tuple(n for n in screened[card] if n not in excluded[card])
    return out, pools


def play_arm(tape, signals, cfg, executed=None):
    trades, blocked, refused = [], 0, 0
    latest = {}
    for s in sorted(signals, key=lambda item: (item.day, item.id)):
        if s.id in latest and s.day < latest[s.id]:
            blocked += 1
            continue
        t = simulate(tape, s, cfg)
        if t is None:
            refused += 1
        else:
            trades.append(t)
            if executed is not None:
                executed.append((s, t))
            cooldown = cfg["signal_rules"]["B"]["cooldown"] if s.card == "B" else 0
            latest[s.id] = t.legs[-1].day + cooldown + (s.card == "B")
    return trades, blocked, refused


def pool_comparison(tape, trades, pools, card, cfg):
    comparison, edge, blank = [], [], 0
    for s, trade in trades:
        enter = s.day + 1
        values = []
        for name in pools.get((card, s.day), ()):
            if name == s.id:
                continue
            bars = tape.bars[name]
            start = bars[enter]
            if start is None:
                continue
            add_bar = bars[trade.add_day] if trade.add_day is not None else None
            if trade.add_day is not None and add_bar is None:
                continue
            controls = []
            for leg in trade.legs:
                b = bars[leg.day]
                if b is None:
                    break
                price = b.open if leg.print_kind == "open" else b.close
                first_return = price * tape.scale(name, enter, leg.day) / start.open - 1
                if add_bar is None:
                    controls.append(leg.shares * first_return)
                else:
                    other = price * tape.scale(name, trade.add_day, leg.day) / add_bar.open - 1
                    spent = trade.added * trade.add_price
                    controls.append((trade.price * first_return + spent * other) / (trade.price + spent))
            else:
                values.append(sum(controls))
        if len(values) < cfg["compare_shown"]["min_pool"]:
            blank += 1
        else:
            mean = fmean(values)
            comparison.append(mean)
            net = excess(trade, cfg["costs_bp_per_side"][card], cfg["stop_overshoot_share_of_risk"][card],
                         cfg["delisted_last_close_share"]["primary"])
            bench = benchmark_return(trade)
            edge.append(net + bench - mean)
    return {"compared": len(comparison), "blank": blank,
            "mean_pool": fmean(comparison) if comparison else None,
            "mean_excess_over_pool": fmean(edge) if edge else None}


def settlement_lag(day, rule):
    if day < iso(rule["settle_second_first"]):
        return rule["settle_initial_sessions"]
    if day <= iso(rule["settle_second_last"]):
        return rule["settle_second_sessions"]
    return rule["settle_third_sessions"]


def book_rank(s):
    return (-s.rank, -s.relative_volume, s.id) if s.card == "A" else (
        s.tag != "Gold", -s.relative_volume, s.id)


def cash_book(tape, signals, card, cfg):
    """One shown-only cash book, with settlement and integer order quantities."""
    b = cfg["book_rules"]
    rules = cfg["signal_rules"][card]
    fee = cfg["costs_bp_per_side"][card] / BP_PER_UNIT
    slip = cfg["stop_overshoot_share_of_risk"][card]
    last_share = cfg["delisted_last_close_share"]["primary"]
    cash = b["initial_equity"]
    queued, positions, sale_days, sales, settlements, by_day = {}, {}, {}, defaultdict(list), defaultdict(float), defaultdict(list)
    totals = dict(raw=len(signals), signal_days=len({s.day for s in signals}), funded=0, adds=0,
                  settlement_blocked=0, open_limits=0, zero_shares=0, capacity_blocked=0,
                  overlap_or_cooldown=0, gap_exits=0, stop_exits=0, partial_exits=0,
                  delisted_documented=0, bars_ended_undocumented=0, design_fence_exits=0,
                  split_fractions_rounded=0)
    for s in signals:
        by_day[s.day].append(s)

    def sell(name, entered, leg, final, recognized):
        nonlocal cash
        if name not in positions or positions[name][0] != entered:
            return
        enter, left = positions[name]
        n = left if final else math.floor(left * rules["partial_share"])
        if not n:
            return
        value = leg.value
        if leg.reason == "stop_intraday":
            value -= slip * leg.risk
            totals["stop_exits"] += 1
        elif leg.reason == "stop_gap":
            totals["gap_exits"] += 1
        elif leg.reason == "delisted":
            totals["delisted_documented"] += 1
            value *= last_share
        elif leg.reason == "bars_ended":
            totals["bars_ended_undocumented"] += 1
            value *= last_share
        elif leg.reason == "design_fence":
            totals["design_fence_exits"] += 1
        elif leg.reason == "partial":
            totals["partial_exits"] += 1
        clear = max(recognized, leg.day + settlement_lag(tape.days[leg.day], b))
        proceeds = n * value / tape.scale(name, enter, leg.day) * (1 - fee)
        if clear == recognized:
            cash += proceeds
        else:
            settlements[clear] += proceeds
        if n == left:
            sale_days[name] = leg.day
            del positions[name]
        else:
            positions[name] = enter, left - n

    for i, day in enumerate(tape.days):
        cash += settlements.pop(i, 0.0)
        previous = sales.pop(i, [])
        for name, entered, leg, final in previous:
            if leg.recognized is not None and leg.recognized > leg.day:
                sell(name, entered, leg, final, i)
        for name, (entered, quantity) in list(positions.items()):
            ratio = tape.splits.get(name, {}).get(i)
            if ratio is None:
                continue
            in_new_shares = quantity * ratio
            whole = math.floor(in_new_shares)
            if whole != in_new_shares:
                totals["split_fractions_rounded"] += 1
            if whole:
                positions[name] = entered, whole
            else:
                sale_days[name] = i
                del positions[name]
        for name, entered, leg, final in previous:
            if leg.print_kind == "open":
                sell(name, entered, leg, final, i)

        for s, n in queued.pop(i, []):
            if s.id in positions or len(positions) >= b["max_positions"]:
                totals["capacity_blocked"] += 1
                continue
            terms = entry_terms(tape, s, cfg)
            if terms is None:
                totals["open_limits"] += 1
                continue
            actual = terms[0] * (1 + fee)
            if n * actual > cash:
                totals["settlement_blocked"] += 1
                continue
            trade = simulate(tape, s, cfg, with_benchmark=False)
            cash -= n * actual
            totals["funded"] += 1
            positions[s.id] = i, n
            for j, leg in enumerate(trade.legs):
                final = j == len(trade.legs) - 1
                known = leg.day if leg.recognized is None else leg.recognized
                if known == i:
                    previous.append((s.id, i, leg, final))
                else:
                    sales[known].append((s.id, i, leg, final))

        for name, entered, leg, final in previous:
            if leg.print_kind != "open" and (leg.recognized is None or leg.recognized == leg.day):
                sell(name, entered, leg, final, i)

        clock = by_day.get(i)
        if not clock:
            continue
        cooldown = rules["cooldown"] if card == "B" else -1
        allowed = []
        for s in clock:
            if s.id in positions or i <= sale_days.get(s.id, -len(tape.days)) + cooldown:
                totals["overlap_or_cooldown"] += 1
            else:
                allowed.append(s)
        if not allowed or i + 1 >= len(tape.days):
            continue
        equity = cash + sum(settlements.values())
        for name, (_, left) in positions.items():
            bars = tape.bars[name]
            j = i
            while bars[j] is None:
                j -= 1
            mark = bars[j].close / tape.scale(name, j, i) * (1 - fee)
            equity += left * mark
        next_cash = cash + settlements.get(i + 1, 0.0)
        orders = []
        for s in sorted(allowed, key=book_rank)[:b["max_initial_orders_per_day"]]:
            if (s.maximum - s.stop) / s.maximum > rules["stop_refusal"]:
                totals["open_limits"] += 1
                continue
            worst = s.maximum * (1 + fee)
            adverse_stop = (s.stop - slip * (s.maximum - s.stop)) * (1 - fee)
            size = math.floor(min(b["risk_share"] * equity / (worst - adverse_stop),
                                  b["position_share"] * equity / worst))
            if size <= 0:
                totals["zero_shares"] += 1
                continue
            n = min(size, math.floor(next_cash / worst))
            if n <= 0:
                totals["settlement_blocked"] += 1
                continue
            orders.append((s, n))
            next_cash -= n * worst
        if orders:
            queued[i + 1] = orders
    require(not positions, "REFUSE_BOOK_TERMINAL_HOLD")
    finish = cash + sum(settlements.values())
    return {**totals, "ending_equity": finish, "net_return": finish / b["initial_equity"] - 1}


def design_replay(tape, cfg, expected_counts=None):
    diagnostics = {"missing_share_name_days": 0}
    signals, pools = design_candidates(tape, cfg, diagnostics=diagnostics)
    counts = count_signals(signals, tape.days, cfg)
    if expected_counts is not None:
        require(list(count_lines(counts, cfg, diagnostics)) == expected_counts, "REFUSE_COUNT_REPLAY_MISMATCH")
    picks = branches(counts, cfg)
    first = iso(cfg["design_first"])
    a = cfg["signal_rules"]["A"]
    switch_funds = a["ema_fund"], a["sma_fund"]

    def present(name, i):
        bars = tape.bars.get(name)
        return bars is not None and (bars.present(i) if isinstance(bars, BarSeries) else bars[i] is not None)

    absent = (sum(d >= first and any(not present(n, i) for n in switch_funds)
                  for i, d in enumerate(tape.days))
              if picks["A"] != "close_on_coverage" else 0)
    report = {}
    for card, arm in picks.items():
        if arm == "close_on_coverage":
            report[card] = {"judged_arm": arm, "passed": False}
            continue
        extra = {"missing_switch_days": absent} if card == "A" else {}
        if arm == "close_on_count":
            report[card] = {"judged_arm": arm, "passed": False, **extra}
            continue
        outcomes = {}
        for candidate in ARMS[card]:
            executed = []
            selection = [s for s in signals if (s.card, s.arm) == (card, candidate)]
            trades, blocked, refused = play_arm(tape, selection, cfg, executed)
            outcomes[candidate] = {"counts": {"blocked": blocked, "refused": refused},
                                   "comparison_shown": pool_comparison(tape, executed, pools, card, cfg),
                                   **aggregate(trades, card, cfg)}
        book = cash_book(tape, [s for s in signals if (s.card, s.arm) == (card, arm)], card, cfg)
        report[card] = {"judged_arm": arm, "arms": outcomes, "book_shown": book,
                        "passed": outcomes[arm]["passed"],
                        "coverage_warning": outcomes[arm]["coverage_warning"], **extra}
    return report


def decode_count(layout, opaque, cfg):
    with tape_snapshot(layout, opaque, cfg) as tape:
        diagnostics = {"missing_share_name_days": 0}
        signals, _ = design_candidates(tape, cfg, branches_only=True, diagnostics=diagnostics)
        return list(count_lines(count_signals(signals, tape.days, cfg), cfg, diagnostics))


def decode_design(layout, opaque, cfg, expected_counts=None):
    with tape_snapshot(layout, opaque, cfg) as tape:
        return design_replay(tape, cfg, expected_counts)


def summary(report, cfg):
    c = cfg["dead_name_coverage"]["C"]
    warning = "" if c is None else f" SURVIVORSHIP WARNING C={c}"
    for card in ARMS:
        yield card + " " + json.dumps(report[card], sort_keys=True, allow_nan=False) + warning
    yield cfg["result_line"][not any(x["passed"] for x in report.values())]


def main(args):
    if args == ["--self-test"]:
        from test_score_74 import self_test
        self_test()
        return 0
    try:
        if args and args[0].startswith(("--held-back", "--go-held", "--heldback")):
            raise Refusal("held-back mode is not built")
        require(len(args) == 2 and args[0] in {"--validate-inputs", "--go-design"}, "REFUSE_MODE")
        mode, value = args
        cfg = config()
        if mode == "--go-design":
            require(value == str(DESIGN_DIR), "REFUSE_DIR")
            committed_approval()  # refuse before touching the private folder
        with private_folder(DESIGN_DIR) as fd:
            if mode == "--validate-inputs":
                required_benchmark_prints(load_snapshot(fd, value, cfg), cfg)
                print("VALIDATED_NO_PRICE_DECODE")
            else:
                for line in summary(guarded_run(fd, committed_approval, cfg), cfg):
                    print(line)
    except Refusal as exc:
        print(exc, file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, csv.Error):
        print("REFUSE_INPUT", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
