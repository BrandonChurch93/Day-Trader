"""Plan 76. Pure calculations plus three separately guarded one-shot modes."""

import os
import sys

# A custody invocation must not load checkout-local shadow modules.
if __name__ == "__main__":
    sys.dont_write_bytecode = True
    checkout = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path[:] = [p for p in sys.path if os.path.commonpath((checkout, os.path.realpath(p or "."))) != checkout]

from bisect import bisect_left
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import random
import re
import stat
import subprocess

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
LEDGER = "research_rig/TRIAL_LEDGER.md"
MODES = {"--count": "count", "--go-design": "design", "--go-heldback": "heldback"}
PREVIOUS = {"design": "count", "heldback": "design"}
HOUR = timedelta(hours=1)
HASH = re.compile(r"[a-f0-9]{64}\Z")


class Refusal(Exception):
    """Only fixed public codes."""


def need(ok, code):
    if not ok:
        raise Refusal(code)


def config():
    return yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())["plan_76"]["value"]


def utc(day):
    return datetime.combine(date.fromisoformat(day), datetime.min.time(), timezone.utc)


@dataclass(frozen=True, slots=True)
class Tape:
    start: datetime
    names: tuple
    close: np.ndarray
    full: np.ndarray
    open: np.ndarray | None = None

    def clock(self, index):
        return self.start + index * HOUR


@dataclass(frozen=True, slots=True)
class Trade:
    coin: int
    entry: int
    exit: int
    gross: float


def eligibility(start, hours, names, cfg):
    """Metadata only. The half-open date intervals are in UTC."""
    full = np.zeros((hours, len(names)), dtype=bool)
    for j, coin in enumerate(names):
        for lo, hi in cfg["admissions"][coin]:
            first = max(0, (utc(lo) - start) // HOUR)
            stop = min(hours, (utc(hi) - start) // HOUR) if hi else hours
            if first < stop:
                full[first:stop, j] = True
    for day in cfg["all_closed_dates"]:
        first = (utc(day) - start) // HOUR
        if 0 <= first < hours:
            full[first:first + timedelta(days=1) // HOUR] = False
    return full


def signals(tape, drop):
    """At entry index e, inspect only closes e-2/e-1 and admission flags."""
    for e in range(2, len(tape.close) + 1):
        prior, now = tape.close[e - 2:e]
        admitted = tape.full[e - 2:e + 1].all(axis=0)
        # The comparison is algebraically close/prior - 1 <= -drop.
        # Multiplying by the fixed threshold also admits exact decimal examples.
        hit = admitted & (now <= prior * (1 - drop))
        if hit.any():
            candidates = np.flatnonzero(hit)
            best = candidates[np.argmin(now[candidates] / prior[candidates])]
            yield e, int(best)


def counts(tape, cfg):
    hold = cfg["hold_hours"]["primary"]
    years = sorted({str(y) for y in range(tape.start.year, tape.clock(len(tape.close) - 1).year + 1)}
                   | {str(y) for y in cfg["count_years"]})
    by_arm, refused = {}, {}
    for arm, drop in cfg["drops"].items():
        by_year, free = dict.fromkeys(years, 0), 0
        refused[arm] = 0
        for e, _ in signals(tape, drop):
            if e >= free:
                if e + hold >= len(tape.close):
                    refused[arm] += 1
                    continue
                by_year[str(tape.clock(e).year)] += 1
                free = e + hold
        by_arm[arm] = dict(sorted(by_year.items()))
    selected = next((arm for arm in ("primary", "alternate") if all(
        by_arm[arm][str(y)] >= cfg["count_each_year"] for y in cfg["count_years"])), None)
    return {"selected": selected, "outcome": "advance to design" if selected else "closed on count",
            "counts_by_utc_entry_year": by_arm, "refused_at_fence": refused, "unresolved_at_fence": None}


def executable(tape):
    need(tape.open is not None, "REFUSE_OPEN_VIEW")
    return tape.full & np.isfinite(tape.open)


def next_sale(opens):
    return [np.flatnonzero(opens[:, j]) for j in range(opens.shape[1])]


def fill(tape, sales, coin, entry, hold):
    avail = sales[coin]
    i = avail.searchsorted(entry + hold)
    if i < len(avail):
        exit_ = int(avail[i])
        return Trade(coin, entry, exit_, float(tape.open[exit_, coin] / tape.open[entry, coin] - 1))
    return None


def tickets(tape, drop, hold, opens, sales):
    traded, no_entry, refused, unresolved, free = [], 0, 0, 0, 0
    for e, j in signals(tape, drop):
        if e < free:
            continue
        if e + hold >= len(tape.close):
            refused += 1
            continue
        if not opens[e, j]:
            no_entry += 1
            continue
        t = fill(tape, sales, j, e, hold)
        if t is None:
            unresolved = 1
            break
        free = t.exit
        traded.append(t)
    return traded, {"missing_selected_open": no_entry, "refused_at_fence": refused, "unresolved_at_fence": unresolved,
                    "delayed_sales": sum(t.exit > t.entry + hold for t in traded)}


def net(gross, bp):
    fee = bp / 10_000
    return (1 + np.asarray(gross)) * ((1 - fee) / (1 + fee)) - 1


def hour_of_week(clock):
    return timedelta(days=clock.weekday(), hours=clock.hour) // HOUR


def random_books(tape, actual, hold, opens, sales, cfg):
    """Fixed exact strata, randomized order, uniform among currently free dates."""
    if not actual:
        return []
    keys = [(t.coin, hour_of_week(tape.clock(t.entry))) for t in actual]
    start_how = hour_of_week(tape.start)
    week = timedelta(weeks=1) // HOUR
    pools = {}
    for j, how in sorted(set(keys)):
        first = (how - start_how) % week
        pools[j, how] = [t for e in range(first, len(tape.close) - hold, week)
                         if opens[e, j] and (t := fill(tape, sales, j, e, hold)) is not None]
    # Keep only calendars here. The trade's realized return never determines a draw.
    settings = cfg["control"]
    rng = random.Random(settings["seed"])
    results = []
    for _ in range(settings["draws"]):
        for _ in range(settings["max_attempts_per_draw"]):
            order = list(keys)
            rng.shuffle(order)
            occupied, chosen = [], []
            for key in order:
                pool = pools[key]
                # A random permutation makes the first legal choice uniform.
                for t in rng.sample(pool, len(pool)):
                    k = bisect_left(occupied, (t.entry,))
                    if ((k and occupied[k - 1][1] > t.entry)
                            or (k < len(occupied) and occupied[k][0] < t.exit)):
                        continue
                    occupied.insert(k, (t.entry, t.exit))
                    chosen.append(t)
                    break
                else:
                    break
            if len(chosen) == len(keys):
                results.append(chosen)
                break
        else:
            return []
    return results


def mean_or_none(a):
    return float(np.mean(a)) if len(a) else None


def marks(values, years, controls, cfg):
    a, years = np.asarray(values), np.asarray(years)
    center = mean_or_none(a)
    floor = cfg["mean_floor"]
    complete = len(controls) == cfg["control"]["draws"]
    beat = float(np.mean(center > np.asarray(controls))) if center is not None and complete else None
    trim = cfg["trim_per_year"]
    kept = np.concatenate([np.sort(a[years == y])[:-trim] for y in sorted(set(years))]) if len(a) else []
    trimmed = mean_or_none(kept)
    return {"trades": len(a), "mean_net": center, "control_share_strictly_beaten": beat,
            "mean_without_each_year_best": trimmed,
            "marks": {"positive": center is not None and center > floor,
                      "beats_random": beat is not None and beat > cfg["control"]["beat_share"],
                      "positive_trimmed": trimmed is not None and trimmed > floor,
                      "enough_trades": len(a) >= cfg["min_heldback_trades"]}}


def means(gross, cfg):
    return {line: mean_or_none(net(gross, bp)) for line, bp in cfg["costs_bp"].items()}


def scored(tape, stage, selected, cfg):
    opens = executable(tape)
    sales = next_sale(opens)
    hold = cfg["hold_hours"]
    drops = cfg["drops"]
    shown = {}
    for arm, drop in drops.items():
        main, gaps = tickets(tape, drop, hold["primary"], opens, sales)
        short, short_gaps = tickets(tape, drop, hold["shown"], opens, sales)
        late = [float(tape.open[t.exit, t.coin] / tape.close[t.entry, t.coin] - 1)
                for t in main if tape.full[t.entry, t.coin] and np.isfinite(tape.close[t.entry, t.coin])]
        gross = [t.gross for t in main]
        if arm == selected:
            actual, actual_gaps = main, gaps
        else:
            shown[arm] = {"trades": len(main), "mean_net": means(gross, cfg), **gaps}
        shown[arm + "_short"] = {"trades": len(short), "mean_net": means([t.gross for t in short], cfg), **short_gaps}
        shown[arm + "_late"] = {"trades": len(late), "mean_net": means(late, cfg),
                               "missing_late_close": len(main) - len(late)}
    calendars = random_books(tape, actual, hold["primary"], opens, sales, cfg)
    comp = [float(np.mean([t.gross for t in book])) for book in calendars]
    years = [tape.clock(t.entry).year for t in actual]
    gross = [t.gross for t in actual]
    lines = {line: marks(net(gross, bp), years, net(comp, bp), cfg) for line, bp in cfg["costs_bp"].items()}
    if stage == "design":
        advance = any(result["marks"]["positive"] for result in lines.values())
        outcome = "advance to held-back" if advance else "closed on design"
        shown["selected_arm_marks"] = lines
        report = {"go_on_check_mean_net": {line: result["mean_net"] for line, result in lines.items()}}
    elif len(actual) < cfg["min_heldback_trades"]:
        outcome = "closed on count"
    elif all(lines["main"]["marks"].values()):
        outcome = "forward card only"
    elif all(lines["cheap"]["marks"].values()):
        outcome = "forward card on Binance.US books, not a counted pass"
    else:
        outcome = "did not pass"
    if stage != "design":
        report = {"lines": lines}
    return {"selected": selected, "outcome": outcome, **report, "shown_only": shown,
            "coverage": actual_gaps, "random_books": len(comp),
            "trades_by_utc_entry_year": {str(y): years.count(y) for y in sorted(set(years))}}


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def unique(pairs):
    out = dict(pairs)
    need(len(pairs) == len(out), "REFUSE_METADATA")
    return out


def object_from(blob):
    try:
        out = json.loads(blob, object_pairs_hook=unique)
    except (ValueError, RecursionError):
        raise Refusal("REFUSE_METADATA") from None
    need(type(out) is dict, "REFUSE_METADATA")
    return out


def is_hash(value):
    return isinstance(value, str) and HASH.fullmatch(value) is not None


def approval(ledger, stage, row):
    key = "P76_" + stage.upper() + "_GO"
    hits = re.findall(rf"^\|[ \t]*{row}[ \t]*\|[^\n]*$", ledger, re.M)
    need(len(hits) == 1, "REFUSE_LEDGER_ROW")
    pattern = rf"(?<![A-Za-z0-9_]){key}(?![A-Za-z0-9_])"
    pins = re.findall(pattern + r"=([a-f0-9]{64})(?=[\s`|]|$)", hits[0])
    need(len(pins) == 1 and len(re.findall(pattern, ledger)) == 1, "REFUSE_LEDGER_GO")
    return pins[0]


def committed_ledger():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

    def git(*args):
        result = subprocess.run(("git", *args), cwd=ROOT, env=env, check=False,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        need(result.returncode == 0, "REFUSE_GIT")
        return result.stdout

    commit = git("rev-parse", "--verify", "HEAD").strip().decode("ascii")
    need(re.fullmatch(r"[a-f0-9]{40,64}", commit), "REFUSE_GIT")
    tags = git("ls-files", "-v", "-z").split(b"\x00")
    need(not any(t[:1].islower() or t[:1] == b"S" for t in tags), "REFUSE_GIT_FLAGS")
    need(not git("ls-files", "--others", "-z"), "REFUSE_UNTRACKED")
    need(not git("status", "--porcelain", "--untracked-files=all"), "REFUSE_DIRTY")
    ledger = git("show", f"{commit}:{LEDGER}").decode("utf-8")
    need(git("rev-parse", "--verify", "HEAD").strip() == commit.encode(), "REFUSE_GIT")
    return ledger


@contextmanager
def open_folder(path):
    need(path.is_absolute() and ".." not in path.parts, "REFUSE_DIR")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        st = os.fstat(fd)
        need(st.st_uid == os.geteuid() and stat.S_IMODE(st.st_mode) == 0o700, "REFUSE_PRIVATE_DIR")
        yield fd
    finally:
        os.close(fd)


def read_file(fd, name, limit):
    child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    with os.fdopen(child, "rb") as f:
        st = os.fstat(f.fileno())
        need(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_uid == os.geteuid()
             and stat.S_IMODE(st.st_mode) == 0o600 and st.st_size <= limit, "REFUSE_FILE")
        blob = f.read(limit + 1)
        need(len(blob) == st.st_size, "REFUSE_SIZE")
        return blob


def new_file(fd, name, payload, code):
    try:
        child = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    except FileExistsError:
        raise Refusal(code) from None
    with os.fdopen(child, "wb") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    os.fsync(fd)


def snapshot(fd, stage, pin, cfg):
    """Opaque load and custody validation. No price values interpreted."""
    cap = cfg["custody"]["metadata_max_bytes"]
    manifest = read_file(fd, "manifest.json", cap)
    need(is_hash(pin) and digest(manifest) == pin, "REFUSE_PIN")
    m = object_from(manifest)
    need(set(m) == {"schema", "stage", "start", "stop_exclusive", "names", "hours", "bars_sha256",
                    "source_receipt_sha256", "prior_result_sha256"}, "REFUSE_MANIFEST")
    names = tuple(sorted(cfg["admissions"]))
    need(type(m["schema"]) is int and m["schema"] == cfg["schema"] and m["stage"] == stage
         and m["names"] == list(names), "REFUSE_MANIFEST")
    need(is_hash(m["bars_sha256"]) and is_hash(m["source_receipt_sha256"])
         and (is_hash(m["prior_result_sha256"]) if stage in PREVIOUS else m["prior_result_sha256"] is None),
         "REFUSE_MANIFEST")
    first, stop = m["start"], m["stop_exclusive"]
    need(all(isinstance(d, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) for d in (first, stop)), "REFUSE_FENCE")
    need(first == cfg["heldback_start"] if stage == "heldback" else [first, stop] == cfg["design"], "REFUSE_FENCE")
    start = utc(first)
    hours = (utc(stop) - start) // HOUR
    need(type(m["hours"]) is int and m["hours"] == hours and cfg["hold_hours"]["primary"] + 2 < hours
         <= cfg["custody"]["max_hours"], "REFUSE_FENCE")
    source = read_file(fd, "source_receipt.json", cap)
    need(digest(source) == m["source_receipt_sha256"], "REFUSE_SOURCE_RECEIPT")
    receipt = object_from(read_file(fd, "receipt.json", cap))
    need(receipt == {"schema": cfg["schema"], "stage": stage, "manifest_sha256": pin,
                     "separate_custodian": True, "permission_confirmed": True}
         and type(receipt["schema"]) is int and receipt["separate_custodian"] is True
         and receipt["permission_confirmed"] is True, "REFUSE_RECEIPT")
    size = hours * len(names) * (1 if stage == "count" else 2) * np.dtype("<f8").itemsize
    prices = read_file(fd, "bars.f64", size)
    need(len(prices) == size and digest(prices) == m["bars_sha256"], "REFUSE_TAPE_HASH")
    return m, prices


def read_bars(m, payload, cfg):
    """The only decoder for the venue-neutral custodian tape."""
    names = tuple(m["names"])
    start = utc(m["start"])
    hours = m["hours"]
    count = m["stage"] == "count"
    a = np.frombuffer(payload, dtype="<f8").reshape(hours, len(names), -1)
    need(bool(np.all(np.isnan(a) | ((a > 0) & np.isfinite(a)))), "REFUSE_PRICE_ENCODING")
    if not count:
        need(bool(np.array_equal(np.isnan(a[:, :, 0]), np.isnan(a[:, :, 1]))), "REFUSE_PRICE_ENCODING")
    return Tape(start, names, a[:, :, -1], eligibility(start, hours, names, cfg), None if count else a[:, :, 0])


def carry_in(path, stage, manifest, ledger, cfg):
    if stage not in PREVIOUS:
        return None
    prev = PREVIOUS[stage]
    prev_pin = approval(ledger, prev, cfg["ledger_row"])
    with open_folder(path / prev) as fd:
        cap = cfg["custody"]["metadata_max_bytes"]
        need(read_file(fd, "RUN.lock", cap) == (prev_pin + "\n").encode(), "REFUSE_PREVIOUS_LOCK")
        blob = read_file(fd, "result.json", cap)
    need(digest(blob) == manifest["prior_result_sha256"], "REFUSE_PREVIOUS_RESULT")
    previous = object_from(blob)
    expected = "advance to design" if stage == "design" else "advance to held-back"
    need(previous.get("stage") == prev and previous.get("manifest_sha256") == prev_pin
         and previous.get("outcome") == expected and previous.get("selected") in cfg["drops"], "REFUSE_PREVIOUS_RESULT")
    return previous["selected"]


def execute(fd, stage, pin, manifest, payload, selected, cfg):
    # All loads, authentication, and silent numeric validation finish before
    # the exclusive durable claim. No scoring routine receives tape before it.
    tape = read_bars(manifest, payload, cfg)
    try:
        os.stat("result.json", dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise Refusal("REFUSE_OUTPUT_EXISTS")
    new_file(fd, "RUN.lock", (pin + "\n").encode(), "REFUSE_LOCK")
    result = counts(tape, cfg) if stage == "count" else scored(tape, stage, selected, cfg)
    result.update(stage=stage, manifest_sha256=pin)
    body = json.dumps(result, sort_keys=True, allow_nan=False).encode() + b"\n"
    new_file(fd, "result.json", body, "REFUSE_OUTPUT_EXISTS")
    return body.decode().rstrip()


def main(args):
    try:
        cfg = config()
        path = Path(cfg["custody"]["root"])
        validate = len(args) == 3 and args[0] == "--validate-inputs" and args[1] in MODES
        if validate:
            stage, pin = MODES[args[1]], args[2]
            need(is_hash(pin), "REFUSE_PIN")
        else:
            need(len(args) == 1 and args[0] in MODES, "REFUSE_MODE")
            stage = MODES[args[0]]
            ledger = committed_ledger()
            pin = approval(ledger, stage, cfg["ledger_row"])
        with open_folder(path / stage) as fd:
            manifest, payload = snapshot(fd, stage, pin, cfg)
            if validate:
                result = "VALIDATED_NO_PRICE_DECODE"
            else:
                selected = carry_in(path, stage, manifest, ledger, cfg)
                result = execute(fd, stage, pin, manifest, payload, selected, cfg)
        print(result)
        return 0
    except Refusal as exc:
        print(str(exc))
    except (OSError, ValueError, ArithmeticError, KeyError, TypeError):
        print("REFUSE_INPUT")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
