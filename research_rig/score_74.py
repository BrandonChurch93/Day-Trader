"""Plan 74 offline custody guards and synthetic-only signal replay."""

import csv
import hashlib
import io
import json
import math
import os
import re
import stat
import struct
import subprocess
import sys
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import fmean
from tempfile import TemporaryFile

from count_74 import (ARMS, ROOT, Bar, CloseView, Refusal, activation_rules, branches,
                      close_signals, config, count_signals, market, require, trailing_ema)


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


def approved_id(ledger):
    rows = re.findall(r"^\|[ \t]*226[ \t]*\|[^\r\n]*$", ledger, flags=re.M)
    require(len(rows) == 1, "REFUSE_LEDGER_ROW")
    keys = re.findall(r"(?<![A-Za-z0-9_])P74_DESIGN_GO\s*=", rows[0])
    ids = re.findall(r"(?<![A-Za-z0-9_])P74_DESIGN_GO=(p74d-[a-f0-9]{64})(?=[\s`|]|$)", rows[0])
    require(len(keys) == len(ids) == 1, "REFUSE_LEDGER_GO")
    return ids[0]


def committed_approval(root=ROOT):
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
    approval = approved_id(git("show", f"{commit}:{LEDGER}"))
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
        nested(row["share_counts"], {"filed_date", "basis_date", "shares", "accession"},
               ("filed_date", "basis_date"))
        for share in row["share_counts"]:
            require(type(share["shares"]) is int and share["shares"] > 0, "REFUSE_IDENTITY")
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
    days = tuple(iso(row[0]) for row in table(checked("calendar.csv"), ("session",)))
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
    return days, names, segments


def create_lock(fd, approval):
    try:
        child = os.open("RUN.lock", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600, dir_fd=fd)
    except FileExistsError:
        raise Refusal("REFUSE_LOCK") from None
    with os.fdopen(child, "wb") as stream:
        stream.write((approval + "\n").encode("ascii"))
        stream.flush()
        os.fsync(stream.fileno())
    os.fsync(fd)


def guarded_run(fd, current, cfg, *, authorize=activation_rules, decoder=None):
    """The decoder, if supplied for an invented fixture, sees only pinned bytes."""
    try:
        os.stat("RUN.lock", dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise Refusal("REFUSE_LOCK")
    before = current()
    pin = receipt_pin(fd, before[1])
    authorize(cfg)
    require(decoder is not None, "REFUSE_PRODUCTION_DECODER_NOT_BUILT")
    with TemporaryFile(dir=fd_path(fd)) as opaque:
        layout = load_snapshot(fd, pin, cfg, opaque)
        require(current() == before, "REFUSE_GIT")
        create_lock(fd, before[1])
        return decoder(layout, opaque, cfg)


def fd_path(fd):
    return f"/proc/self/fd/{fd}"


def decode_bar(stream):
    """Interpret a private fixture's raw open/high/low/close/volume."""
    bar = Bar(*BAR.unpack(stream.read(BAR.size)))
    require(all(math.isfinite(v) and v > 0 for v in (bar.open, bar.high, bar.low, bar.close))
            and 0 <= bar.volume < math.inf
            and bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high,
            "REFUSE_BAR")
    return bar


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

    def view(self, day):
        return CloseView(self.days[:day + 1], {k: v[:day + 1] for k, v in self.bars.items()},
                         self.members.get(day, frozenset()), self.shares.get(day, {}),
                         self.earnings.get(day, frozenset()),
                         {k: {i: f for i, f in v.items() if i <= day} for k, v in self.splits.items()},
                         self.next_split_known.get(day, frozenset()))

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


@dataclass(frozen=True)
class Trade:
    day: date
    price: float
    legs: tuple


def simulate(tape, signal, cfg):
    """A single per-signal trade; callers suppress overlap per arm."""
    require(signal.arm != "one_add", "REFUSE_UNRESOLVED_ADD")
    name, card, enter = signal.id, signal.card, signal.day + 1
    rule = cfg["signal_rules"][card]
    stock, fund = tape.bars[name], cfg["benchmark"][card]
    if enter >= len(tape.days) or stock[enter] is None:
        return None
    cap = signal.maximum
    actual = stock[enter].open
    factor = tape.scale(name, signal.day, enter)
    line, stop = signal.line / factor, signal.stop / factor
    cap /= factor
    if not line < actual <= cap:
        return None
    if signal.arm == "52w":
        stop = actual * (1 - cfg["arm_52w"]["stop_share"])
    elif (cap - stop) / cap > rule["stop_refusal"]:
        return None
    market_bars = tape.bars[fund]
    require(market_bars[enter] is not None, "REFUSE_BENCHMARK")
    legs = []
    risk = actual - stop
    left, pending, partial = 1.0, None, False

    def sale(day, kind, reason, quantity, value):
        bench = market_bars[day]
        require(bench is not None, "REFUSE_BENCHMARK")
        reference = getattr(bench, "close" if kind == "intraday" else kind)
        reference *= tape.scale(fund, enter, day)
        legs.append(Leg(day, kind, reason, quantity, value, risk,
                        reference / market_bars[enter].open - 1))

    for day in range(enter, len(tape.days)):
        b = stock[day]
        require(b is not None, "REFUSE_UNEXPLAINED_BAR_GAP")
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
        if b.low * f <= stop:
            sale(day, "intraday", "stop_intraday", left, stop)
            break
        if tape.delisted.get(name) == day:
            sale(day, "close", "delisted", left, b.close * f)
            break
        view = tape.view(day)
        avg = trailing_ema(view, name, rule["exit_ema_sessions"])
        if ((avg is not None and b.close < avg)
                or day - enter + 1 >= cfg["power"]["hold_limit"][card]
                or (card == "A" and not market(view, cfg, signal.arm))
                or (card == "B" and b.close * f < line)):
            pending = "full"
        elif card == "B" and not partial:
            target = (rule["gold_target"] if signal.tag == "Gold"
                      else actual + rule["revival_risk_multiple"] * risk)
            if b.close * f >= target:
                pending = "partial"
    require(math.isclose(sum(leg.shares for leg in legs), 1.0), "REFUSE_TERMINAL_HOLD")
    return Trade(tape.days[enter], actual, tuple(legs))


def excess(trade, bp, overshoot, delist_share):
    cost = bp / BP_PER_UNIT
    value = 0.0
    bench = 0.0
    for leg in trade.legs:
        price = leg.value
        if leg.reason == "stop_intraday":
            price -= leg.risk * overshoot
        if leg.reason == "delisted":
            price *= delist_share
        value += leg.shares * price
        bench += leg.shares * leg.benchmark
    return value * (1 - cost) / (trade.price * (1 + cost)) - 1 - bench


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
    cases = sum(any(leg.reason == "delisted" for leg in t.legs) for t in trades)
    sides = {str(x): line(cost, slip, x) for x in d["shown"]}
    trigger = bool(trades) and cases / len(trades) > d["share_trigger"]
    passed = main["passed"] and (not trigger or sides[str(d["trigger_line"])]["passed"])
    return {"main": main, "delisted": cases, "delisted_trigger": trigger,
            "delisted_shown": sides, "passed": passed,
            "cost_shown": {str(x): line(x, slip, d["primary"]) for x in cfg["cost_shown_bp_per_side"][card]},
            "overshoot_shown": ({"odd_lots_in": line(cost, cfg["stop_overshoot_shown"]["A_odd_lots_in"],
                                                   d["primary"])} if card == "A" else {})}


def design_candidates(tape, cfg):
    first, last = (iso(cfg[k]) for k in ("design_first", "design_last"))
    require(tape.days[-1] <= last, "REFUSE_FENCE")
    out = []
    for i, d in enumerate(tape.days):
        if first <= d <= last:
            out.extend(close_signals(tape.view(i), cfg)[0])
    return out


def play_arm(tape, signals, cfg):
    trades, blocked, refused = [], 0, 0
    latest = {}
    for s in sorted(signals, key=lambda item: (item.day, item.id)):
        # The exact cooldown and boundary convention still need ruling.
        if s.id in latest and s.day <= latest[s.id]:
            blocked += 1
            continue
        t = simulate(tape, s, cfg)
        if t is None:
            refused += 1
        else:
            trades.append(t)
            cooldown = cfg["signal_rules"]["B"]["cooldown"] if s.card == "B" else 0
            latest[s.id] = t.legs[-1].day + cooldown
    return trades, blocked, refused


def synthetic_design(tape, cfg, *, months=None):
    signals = design_candidates(tape, cfg)
    picks = branches(count_signals(signals, tape.days, cfg), cfg)
    report = {}
    for card, arm in picks.items():
        if arm == "close_on_count":
            report[card] = {"judged_arm": arm, "passed": False}
            continue
        outcomes = {}
        for candidate in ARMS[card]:
            if candidate == "one_add":
                outcomes[candidate] = {"status": "unresolved"}
                continue
            trades, blocked, refused = play_arm(tape, (s for s in signals if (s.card, s.arm) ==
                                                       (card, candidate)), cfg)
            outcomes[candidate] = {"counts": {"blocked": blocked, "refused": refused},
                                   **aggregate(trades, card, cfg, months=months)}
        report[card] = {"judged_arm": arm, "arms": outcomes, "passed": outcomes[arm]["passed"]}
    return report


def summary(report, cfg):
    for card in ARMS:
        yield card + " " + json.dumps(report[card], sort_keys=True, allow_nan=False)
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
                load_snapshot(fd, value, cfg)
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
