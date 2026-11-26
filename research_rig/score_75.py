"""Plan 75 repeat only: invented tests, no-decode validation, and a one-shot go."""

import csv
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[1]
REPEAT_DIR = Path("/home/user/workspace/rig/data/plan_75_repeat")
NAMES = tuple("AAVE ADA AVAX BCH BNB BTC DOGE DOT ETH HBAR LINK LTC NEAR PEPE SHIB SOL SUI XLM XRP ZEC".split())
START, STOP = date(2020, 1, 1), date(2024, 1, 1)
REPEAT_DAYS = tuple(START + timedelta(days=i) for i in range((STOP - START).days))
HASH = re.compile(r"[0-9a-f]{64}\Z")
INDEX_HEADER = b"date,coin,eligible,open_present,close_present,sell_allowed\n"
LEDGER = "research_rig/TRIAL_LEDGER.md"


class Refusal(Exception):
    """Only fixed codes; no input data in a diagnostic."""


def require(ok, code):
    if not ok:
        raise Refusal(code)


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


@contextmanager
def open_folder(folder):
    """Anchor reads, lock and output to one directory inode; reject symlinks."""
    require(folder.is_absolute() and not {"..", "."}.intersection(folder.parts), "REFUSE_DIR")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in folder.parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def read_at(fd, name, limit):
    child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    with os.fdopen(child, "rb") as f:
        meta = os.fstat(f.fileno())
        require(stat.S_ISREG(meta.st_mode) and meta.st_nlink == 1 and meta.st_size <= limit,
                "REFUSE_FILE")
        blob = f.read(limit + 1)
        require(len(blob) == meta.st_size, "REFUSE_SIZE")
        return blob


def snapshot(folder, name, limit):
    with open_folder(folder) as fd:
        return read_at(fd, name, limit)


def unique(pairs):
    obj = dict(pairs)
    require(len(pairs) == len(obj), "REFUSE_MANIFEST")
    return obj


def validate_bytes(manifest, index, payload, expected_manifest_sha):
    """Check pinned raw bytes and key geometry. Never interpret a price field."""
    require(HASH.fullmatch(expected_manifest_sha) and sha(manifest) == expected_manifest_sha,
            "REFUSE_PIN")
    try:
        m = json.loads(manifest, object_pairs_hook=unique)
    except (ValueError, RecursionError):
        raise Refusal("REFUSE_MANIFEST") from None
    require(isinstance(m, dict) and set(m) == {
        "schema", "start", "stop_exclusive", "names", "rows", "index_sha256",
        "payload_sha256", "source_receipt_sha256", "eligibility_receipt_sha256"
    }, "REFUSE_MANIFEST")
    n = len(NAMES) * len(REPEAT_DAYS)
    require(type(m["schema"]) is int and m["schema"] == 1 and m["start"] == START.isoformat()
            and m["stop_exclusive"] == STOP.isoformat() and m["names"] == list(NAMES)
            and type(m["rows"]) is int and m["rows"] == n, "REFUSE_SCHEMA")
    require(all(isinstance(m[k], str) and HASH.fullmatch(m[k]) for k in m if k.endswith("_sha256")),
            "REFUSE_HASH")
    require(sha(index) == m["index_sha256"] and sha(payload) == m["payload_sha256"], "REFUSE_HASH")
    require(len(payload) == 16 * n and index.startswith(INDEX_HEADER)
            and index.endswith(b"\n"), "REFUSE_SIZE")
    rows = index[len(INDEX_HEADER):].splitlines()
    require(len(rows) == n, "REFUSE_ROWS")
    flags = np.empty((len(REPEAT_DAYS), len(NAMES), 4), dtype=bool)
    for i, day in enumerate(REPEAT_DAYS):
        for j, coin in enumerate(NAMES):
            row = rows[i * len(NAMES) + j].split(b",")
            require(len(row) == 6 and row[:2] == [day.isoformat().encode(), coin.encode()]
                    and all(x in (b"0", b"1") for x in row[2:])
                    and not (row[2] == b"1" and row[-1] == b"0"), "REFUSE_INDEX")
            flags[i, j] = [x == b"1" for x in row[2:]]
    return flags


def load_repeat_snapshot(fd, pin):
    require(HASH.fullmatch(pin), "REFUSE_PIN")
    manifest = read_at(fd, "manifest.json", 8192)
    require(sha(manifest) == pin, "REFUSE_PIN")
    index = read_at(fd, "index.csv", 1024 * 1024)
    opaque = read_at(fd, "prices.f64", 16 * len(REPEAT_DAYS) * len(NAMES))
    return validate_bytes(manifest, index, opaque, pin), opaque


def validate_inputs(pin):
    require(HASH.fullmatch(pin), "REFUSE_PIN")
    with open_folder(REPEAT_DIR) as fd:
        load_repeat_snapshot(fd, pin)


def decode_repeat(flags, opaque):
    """Pure decoder for same-byte audit of a future authorized repeat runner."""
    values = np.frombuffer(opaque, dtype="<f8").reshape(*flags.shape[:2], 2)
    present = flags[..., 1:3]
    require(np.all(np.where(present, np.isfinite(values) & (values > 0), np.isnan(values))),
            "REFUSE_PRICES")
    require(np.all(~flags[..., 0] | flags[..., 3]), "REFUSE_FLAGS")
    tape = Tape(REPEAT_DAYS, NAMES, values[..., 0], values[..., 1], flags[..., 0], flags[..., 3])
    tape.check()
    return tape


@dataclass(frozen=True)
class Tape:
    days: tuple
    names: tuple
    opens: np.ndarray
    closes: np.ndarray
    eligible: np.ndarray
    sell: np.ndarray

    def check(self):
        require(len(self.days) > 1 and len(self.names) > 0 and self.days[0] >= START
                and self.days[-1] < STOP and len(set(self.names)) == len(self.names)
                and all(b == a + timedelta(days=1) for a, b in zip(self.days, self.days[1:])),
                "REFUSE_FENCE")
        shape = (len(self.days), len(self.names))
        for a in (self.opens, self.closes):
            require(a.shape == shape and np.all(np.isnan(a) | (np.isfinite(a) & (a > 0))),
                    "REFUSE_PRICES")
        require(self.eligible.shape == self.sell.shape == shape, "REFUSE_FLAGS")


def load_config():
    raw = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
    cfg = raw["replay_75_plan"]["value"]
    require(cfg["repeat"] == [START.isoformat(), STOP.isoformat()], "REFUSE_FENCE")
    costs = {line: sum(raw[key]["value"][fld] for fld in fields) / 10000
             for line, (key, *fields) in cfg["costs"].items()}
    return cfg, raw[cfg["inherited_marks_key"]]["value"], costs


def indicators(tape, lookbacks, cfg, annual):
    days, names = tape.closes.shape
    k = len(lookbacks)
    risk = np.full((days, names), np.nan)
    long = np.zeros((days, names, k), dtype=bool)
    warm = np.zeros((days, names, k), dtype=bool)
    vdays = cfg["vol_days"]
    for j in range(names):
        run = 0
        stop = [None] * k
        for d, price in enumerate(tape.closes[:, j]):
            if not np.isfinite(price):
                run = 0
                # Do not erase the live stop during a data gap.
                if d:
                    long[d, j] = long[d - 1, j]
                continue
            run += 1
            if run > vdays:
                q = tape.closes[d-vdays:d+1, j]
                vol = np.std(q[1:] / q[:-1] - 1, ddof=1) * annual**0.5
                if np.isfinite(vol) and vol > 0:
                    risk[d, j] = vol
            for f, lookback in enumerate(lookbacks):
                before = stop[f]
                warm[d, j, f] = run >= max(lookback, vdays + 1)
                if run >= lookback:
                    q = tape.closes[d-lookback+1:d+1, j]
                    upper, lower = max(q), min(q)
                    mid = lower + (upper - lower) / 2
                    # The printed equation gives the upper channel priority at equality.
                    if price == upper or (before is not None and price > before):
                        stop[f] = mid if before is None else max(before, mid)
                    else:
                        stop[f] = None
                elif before is not None and price <= before:
                    stop[f] = None
                long[d, j, f] = stop[f] is not None
    return long, risk, warm


def calendar(tape, warm):
    """One roster clock, based on the completed prior close, then remove promptly."""
    first = False
    roster = np.zeros_like(tape.eligible)
    resets = np.zeros(len(tape.days), dtype=bool)
    for d in range(1, len(tape.days)):
        prior = roster[d - 1]
        candidate = tape.eligible[d-1] & tape.eligible[d] & warm[d-1].any(axis=1)
        first_open = not first and (candidate & np.isfinite(tape.opens[d])).any()
        if first_open or (first and tape.days[d].day == 1):
            roster[d] = candidate
            resets[d] = True
            first = first or candidate.any()
        else:
            roster[d] = prior & tape.eligible[d]
    return roster, resets


@dataclass
class Book:
    nav: np.ndarray
    weights: np.ndarray
    targets: np.ndarray
    fills: list
    stale_marks: int
    max_target_weight: float


def play(tape, cost, cfg, cap, inputs, roster_clock, *, mode="trend", override=None, shift=0):
    """Book open fills net by coin, then mark the close. Shift is synthetic test only."""
    long, risk, warm = inputs
    roster, resets = roster_clock
    nd, nc, k = long.shape
    shares = np.zeros((nc, k))
    virtual_cash = np.zeros_like(shares)
    queued = np.zeros_like(shares, dtype=bool)
    last = np.zeros(nc)
    reserve = 1.0
    nav, fills, stale, peak_target = np.ones(nd), [], 0, 0.0
    weights = np.zeros((nd, nc, k))
    targets = np.full((nd, nc, k), np.nan)
    for d in range(1, nd):
        p = tape.opens[d]
        can_open = np.isfinite(p)
        tradable = can_open & tape.sell[d]
        px = np.where(can_open, p, last)
        old_value = shares * px[:, None]
        prior_value = shares * last[:, None]
        old_budget = prior_value + virtual_cash
        drift = np.divide(prior_value, old_budget, out=np.zeros_like(shares), where=old_budget > 0)
        balance = virtual_cash.sum() + reserve
        book = balance + old_value.sum()
        active = roster[d]
        monthly = resets[d]
        envelope = old_value + virtual_cash
        if monthly and active.any():
            stranded = old_value[~active & ~tradable].sum()
            envelope = np.broadcast_to(
                (active * max(0, book - stranded) / (active.sum() * k))[:, None], shares.shape
            ).copy()
        signal_day = d - 1 + shift
        wanted = drift.copy()
        queued |= (~active)[:, None] & (shares > 0)
        source = None
        risk_ok = True
        if mode == "hold":
            wanted[:] = 1
        elif override is not None:
            source = override[d]
            wanted[:] = source
            queued |= (source == 0) & (shares > 0)
        elif 0 <= signal_day < nd:
            intent = long[signal_day]
            v = risk[signal_day, :, None]
            target = np.divide(cfg["target_vol"], v, out=np.zeros_like(v), where=np.isfinite(v))
            target = np.minimum(target, cap)
            peak_target = max(peak_target, float(np.max(target)))
            good = warm[signal_day] & np.isfinite(v)
            risk_ok = good
            reweight = monthly | (shares == 0) | (np.abs(target - drift) > cfg["resize_weight_delta"])
            wanted = np.where(good & intent & reweight, target, drift)
            wanted[~intent] = 0
            queued |= ~intent & (shares > 0)
        # No buys without an eligible scheduled open and a completed valid prior close.
        buy_ok = (active & can_open & np.isfinite(tape.closes[d - 1]))[:, None]
        goal = shares.copy()
        if mode == "hold":
            move = np.broadcast_to(monthly | (shares == 0), shares.shape)
        elif source is not None:
            move = np.isfinite(source) | monthly
            wanted = np.where(np.isfinite(source), source, drift)
        else:
            move = monthly | (wanted != drift)
        proposed = np.divide(wanted * envelope, px[:, None], out=shares.copy(), where=px[:, None] > 0)
        proposed = np.where(risk_ok | (proposed <= shares), proposed, shares)
        goal = np.where(move & buy_ok, proposed, goal)
        goal = np.where(queued | ~active[:, None], 0, goal)
        # An exit waiting for an executable sale does not become a new buy.
        goal = np.where(tradable[:, None] | (buy_ok & (goal >= shares)), goal, shares)
        delta = (goal - shares) * px[:, None]
        sells, buys = np.minimum(delta, 0), np.maximum(delta, 0)

        def debit(net):
            return float(cost * np.abs(net).sum())

        def net_at(scale):
            return (sells + scale * buys).sum(axis=1)

        net = net_at(1)
        if cap <= 1 and net.sum() + debit(net) > balance + 1e-12:
            lo, hi = 0.0, 1.0
            for _ in range(48):
                mid = (lo + hi) / 2
                n = net_at(mid)
                if n.sum() + debit(n) <= balance:
                    lo = mid
                else:
                    hi = mid
            delta = sells + lo * buys
            net = net_at(lo)
        shares += np.divide(delta, px[:, None], out=np.zeros_like(shares), where=px[:, None] > 0)
        shares[np.abs(shares) < 1e-14] = 0
        queued &= shares > 0
        for j in np.flatnonzero(np.abs(net) > 1e-14):
            fills.append((d, j, float(net[j]), float(abs(net[j]) * cost)))
        balance -= net.sum() + debit(net)
        post = shares * px[:, None]
        # Reconcile sleeve cash after coin-level netting. On a resize/rebalance,
        # cash follows the sleeve budgets; otherwise it stays where it was.
        cash_goal = envelope - post
        if cap <= 1:
            cash_goal = np.maximum(cash_goal, 0)
        cash_goal[~active] = 0
        if abs(cash_goal.sum()) > 1e-14 and balance * cash_goal.sum() > 0:
            virtual_cash = cash_goal * (balance / cash_goal.sum())
        else:
            virtual_cash = np.zeros_like(shares)
        reserve = balance - virtual_cash.sum()
        denom = post + virtual_cash
        weights[d] = np.divide(post, denom, out=np.zeros_like(shares), where=denom > 0)
        if mode == "trend" and override is None:
            targets[d] = np.where(move & (goal != 0) & (shares > 0), wanted, np.nan)
        close = tape.closes[d]
        good_close = np.isfinite(close)
        stale += int(np.count_nonzero((shares.sum(axis=1) > 0) & ~good_close))
        last = np.where(good_close, close, last)
        value = shares.sum(axis=1) * last
        if d == nd - 1:
            # Only a valid, permitted final print is cashable. No stale terminal sale.
            require(not np.any((value > 0) & (~good_close | ~tape.sell[d])), "REFUSE_TERMINAL")
            for j in np.flatnonzero(value > 1e-14):
                fills.append((d, j, -float(value[j]), float(value[j] * cost)))
            value *= 1 - cost
        nav[d] = balance + value.sum()
        require(np.isfinite(nav[d]) and nav[d] > 0, "REFUSE_NAV")
    return Book(nav, weights, targets, fills, stale, peak_target)


def episodes(book):
    """Extract open-to-open realized sleeve spells and their resize instructions."""
    active = book.weights > 0
    out = []
    for j in range(active.shape[1]):
        for k in range(active.shape[2]):
            a = active[:, j, k]
            starts = np.flatnonzero(a & ~np.r_[False, a[:-1]])
            ends = np.flatnonzero(~a & np.r_[False, a[:-1]]).tolist()
            if a[-1]:
                ends += [len(a)]
            for lo, hi in zip(starts, ends, strict=True):
                target_path = book.targets[lo:hi, j, k].copy()
                if not np.isfinite(target_path[0]):
                    target_path[0] = book.weights[lo, j, k]
                out.append((int(lo), int(hi), j, k, target_path))
    return sorted(out, key=lambda x: x[:4])


def twins(tape, cost, cfg, marks, inputs, clock, book):
    roster, _ = clock
    active = book.weights > 0
    shape = active.shape
    spells = episodes(book)
    ceiling = int(active.sum(axis=(1, 2)).max())
    months = {}
    for d, day in enumerate(tape.days):
        months.setdefault((day.year, day.month), []).append(d)
    rng = np.random.default_rng(marks["twin_seed"])
    ends, missed = [], 0
    opens = np.isfinite(tape.opens)
    prior_closes = np.r_[np.zeros_like(opens[:1]), np.isfinite(tape.closes[:-1])]
    for _ in range(marks["twins"]):
        busy = np.zeros(shape, dtype=bool)
        count = np.zeros(shape[0], dtype=int)
        intents = np.full(shape, np.nan)
        for enter, leave, j, k, path in spells:
            day = tape.days[enter]
            options = months[day.year, day.month]
            duration = leave - enter
            for _ in range(marks["twin_max_draws"]):
                start = options[int(rng.integers(len(options)))]
                stop = start + duration
                if (not start or stop > shape[0] or (stop == shape[0]) != (leave == shape[0])
                        or not opens[start, j] or not prior_closes[start, j]
                        or not roster[start:stop, j].all() or busy[start:stop, j, k].any()
                        or (count[start:stop] >= ceiling).any()):
                    continue
                if stop < shape[0]:
                    if not (opens[stop, j] and tape.sell[stop, j]):
                        continue
                    if not busy[stop, j, k]:
                        intents[stop, j, k] = 0
                elif not (np.isfinite(tape.closes[-1, j]) and tape.sell[-1, j]):
                    continue
                busy[start:stop, j, k] = True
                count[start:stop] += 1
                intents[start:stop, j, k] = path
                break
            else:
                missed += 1
        if spells:
            ends.append(play(tape, cost, cfg, cfg["cap"], inputs, clock, override=intents).nav[-1])
        else:
            ends.append(1.0)
    return float(np.percentile(ends, marks["twin_percentile"], method="linear")), missed, len(spells) * len(ends)


def period_return(nav, days, first, stop):
    rows = [i for i, d in enumerate(days) if first <= d < stop]
    if not rows:
        return None
    return float(nav[rows[-1]] / (nav[rows[0] - 1] if rows[0] else 1) - 1)


def summarize(tape, book, marks):
    nav = book.nav
    perf = nav / np.r_[1.0, nav[:-1]] - 1
    sd = np.std(perf, ddof=1)
    days = tape.days
    years = {y: period_return(nav, days, date(y, 1, 1), date(y + 1, 1, 1))
             for y in sorted({d.year for d in days})}
    holds = [b - a - (b == len(days)) for a, b, *_ in episodes(book)]
    return {
        "net": float(nav[-1] - 1),
        "sharpe": float(perf.mean() / sd * marks["annual_days"]**0.5) if sd > 0 else None,
        "drawdown": float(np.max(1 - nav / np.maximum.accumulate(np.maximum(nav, 1)))),
        "years": years,
        "positive_years": sum(x > 0 for x in years.values()),
        "fill_count": len(book.fills),
        "cost_on_fills": sum(fee for *_, fee in book.fills),
        "stale_coin_days": book.stale_marks,
        "hold_days": {"n": len(holds), "median": float(np.median(holds)) if holds else None,
                      "p90": float(np.percentile(holds, 90)) if holds else None,
                      "max": max(holds, default=None), "over_60": sum(x > 60 for x in holds)},
    }


def score_repeat(tape, save_fills=None):
    """In-memory repeat engine. The runner can keep a private ledger of actual fills."""
    tape.check()
    require(tape.days == REPEAT_DAYS, "REFUSE_FENCE")
    cfg, marks, costs = load_config()
    annual = marks["annual_days"]
    indicator_lines = {
        lookbacks: indicators(tape, lookbacks, cfg, annual)
        for lookbacks in (tuple(cfg["lookbacks"]), tuple(cfg["printed_lookbacks"]),
                          *((n,) for n in cfg["lookbacks"]))
    }
    inp = indicator_lines[tuple(cfg["lookbacks"])]
    clock = calendar(tape, inp[2])
    cut = date.fromisoformat(cfg["repeat_cut"])
    lines = {}
    for line, fee in costs.items():
        book = play(tape, fee, cfg, cfg["cap"], inp, clock)
        hold = play(tape, fee, cfg, 1, inp, clock, mode="hold")
        if save_fills is not None:
            save_fills(line, "primary", book.fills)
            save_fills(line, "same_list_hold", hold.fills)
        twin_cut, missed, attempted = twins(tape, fee, cfg, marks, inp, clock, book)
        shown = summarize(tape, book, marks)
        a = period_return(book.nav, tape.days, START, cut)
        b = period_return(book.nav, tape.days, cut, STOP)
        lines[line] = {
            "primary": shown, "cost_per_side": fee, "same_list_hold_net": float(hold.nav[-1] - 1),
            "halves_net": [a, b], "both_halves_positive_shown_only": a > 0 and b > 0,
            "twins_cut_net": twin_cut - 1, "twins_failed_placements": missed,
            "twins_placement_attempts": attempted,
            "twins_placement_failure_rate": missed / attempted if attempted else None,
            "twins_n": marks["twins"],
            "marks_shown_only": {
                "above_same_list_hold": book.nav[-1] > hold.nav[-1],
                "sharpe_at_least_floor": shown["sharpe"] is not None and shown["sharpe"] >= marks["min_sharpe"],
                "drawdown_at_most_ceiling": shown["drawdown"] <= marks["max_drawdown"],
                "above_twin_cut": book.nav[-1] > twin_cut,
                "literal_five_of_seven": "NOT_APPLICABLE", "three_of_four":
                    shown["positive_years"] >= cfg["repeat_years_positive"],
            },
            "shown_only": {},
        }
        alt = [("three_legs_200_cap", tuple(cfg["lookbacks"]), cfg["printed_cap"]),
               ("the paper's rule as printed", tuple(cfg["printed_lookbacks"]), cfg["printed_cap"]),
               *((str(n), (n,), cfg["cap"]) for n in cfg["lookbacks"])]
        for label, lookbacks, cap in alt:
            a_inp = indicator_lines[lookbacks]
            # Keep the same coin admission clock. Unwarmed individual legs stay cash.
            alt_book = play(tape, fee, cfg, cap, a_inp, clock)
            lines[line]["shown_only"][label] = summarize(tape, alt_book, marks)
            if save_fills is not None:
                save_fills(line, label, alt_book.fills)
    main = lines["main"]
    return {"lines": lines, "implementation_check": main["primary"]["net"] > 0
            and any(x > 0 for x in main["halves_net"])}


def approval_id(ledger):
    rows = re.findall(r"^\|[ \t]*225[ \t]*\|[^\n]*$", ledger, flags=re.M)
    require(len(rows) == 1, "REFUSE_LEDGER_ROW")
    row = rows[0]
    keys = re.findall(r"(?<![A-Za-z0-9_])P75_REPEAT_GO\s*=", row)
    matches = re.findall(r"(?<![A-Za-z0-9_])P75_REPEAT_GO=(p75r-[0-9a-f]{64})(?=[\s`|]|$)", row)
    require(len(keys) == len(matches) == 1, "REFUSE_LEDGER_GO")
    return matches[0]


def committed_approval():
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}

    def git(*args):
        proc = subprocess.run(("git", *args), cwd=ROOT, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
        require(proc.returncode == 0, "REFUSE_GIT")
        return proc.stdout.decode("utf-8")

    commit = git("rev-parse", "--verify", "HEAD").strip()
    require(re.fullmatch(r"[0-9a-f]{40,64}", commit), "REFUSE_GIT")
    require(git("status", "--porcelain", "--untracked-files=no") == "", "REFUSE_DIRTY")
    go = approval_id(git("show", f"{commit}:{LEDGER}"))
    require(git("rev-parse", "--verify", "HEAD").strip() == commit, "REFUSE_GIT")
    return go


def receipt_pin(fd, approved):
    try:
        receipt = json.loads(read_at(fd, "repeat_receipt.json", 4096), object_pairs_hook=unique)
    except (ValueError, RecursionError, Refusal):
        raise Refusal("REFUSE_RECEIPT") from None
    require(isinstance(receipt, dict) and set(receipt) == {"schema", "go_id", "manifest_sha256"}
            and type(receipt["schema"]) is int and receipt["schema"] == 1
            and isinstance(receipt["manifest_sha256"], str)
            and HASH.fullmatch(receipt["manifest_sha256"]), "REFUSE_RECEIPT")
    pin = receipt["manifest_sha256"]
    require(receipt["go_id"] == approved == "p75r-" + pin, "REFUSE_GO_MISMATCH")
    return pin


def ensure_absent(fd, name, code):
    try:
        os.stat(name, dir_fd=fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise Refusal(code)


@contextmanager
def new_private(fd, name, code):
    try:
        f = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
    except FileExistsError:
        raise Refusal(code) from None
    with os.fdopen(f, "w", encoding="ascii", newline="") as output:
        yield output
        output.flush()
        os.fsync(output.fileno())
    os.fsync(fd)


def run_repeat(fd, approved):
    """Validate once on the same directory handle, claim permanently, then decode."""
    folder = os.fstat(fd)
    require(folder.st_uid == os.geteuid() and folder.st_mode & 0o077 == 0, "REFUSE_PRIVATE_DIR")
    ensure_absent(fd, "RUN.lock", "REFUSE_LOCK")
    ensure_absent(fd, "fills.csv", "REFUSE_OUTPUT")
    pin = receipt_pin(fd, approved)
    flags, opaque = load_repeat_snapshot(fd, pin)
    with new_private(fd, "RUN.lock", "REFUSE_LOCK") as lock:
        lock.write(approved + "\n")
    tape = decode_repeat(flags, opaque)
    with new_private(fd, "fills.csv", "REFUSE_OUTPUT") as fills:
        out = csv.writer(fills)
        out.writerow(("cost_line", "book", "date_utc", "coin", "signed_notional", "cost"))

        def save_fills(cost_line, book, rows):
            out.writerows((cost_line, book, tape.days[d].isoformat(), tape.names[j], notional, cost)
                          for d, j, notional, cost in rows)

        return score_repeat(tape, save_fills)


def registered_summary(report):
    """Three fixed lines; the report is aggregate, never keyed by coin or fill."""
    lines = [label.upper() + " " + json.dumps(report["lines"][label], sort_keys=True,
             default=lambda scalar: scalar.item(), allow_nan=False) for label in ("main", "harsh")]
    lines.append("IMPLEMENTATION_CHECK " + ("PASS" if report["implementation_check"] else "FAIL"))
    return "\n".join(lines)


def main(args):
    if args == ["--self-test"]:
        from test_score_75 import self_test
        self_test()
        return 0
    if len(args) == 2 and args[0] in {"--validate-inputs", "--go-repeat"}:
        try:
            if args[0] == "--validate-inputs":
                validate_inputs(args[1])
                summary = "VALIDATED_NO_PRICE_DECODE"
            else:
                require(args[1] == str(REPEAT_DIR), "REFUSE_DIR")
                approved = committed_approval()
                with open_folder(REPEAT_DIR) as fd:
                    summary = registered_summary(run_repeat(fd, approved))
        except Refusal as e:
            print(str(e))
            return 2
        except (OSError, ValueError):
            print("REFUSE_INPUT")
            return 2
        print(summary)
        return 0
    print("REFUSE_MODE")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
