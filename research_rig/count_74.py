"""Gate (c): close-only signal rules and integer-only design counts."""

import csv
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from statistics import fmean


ROOT = Path(__file__).resolve().parents[1]
ARMS = {"A": ("earnings", "without_market", "without_earnings", "one_add", "52w"),
        "B": ("pooled", "Gold", "Revival")}
COUNT_ARMS = {"A": ("earnings", "without_earnings"), "B": ("pooled",)}


class Refusal(Exception):
    """Fixed diagnostic, always sent to stderr by a command-line entry point."""


def require(ok, code):
    if not ok:
        raise Refusal(code)


def config():
    lines = (ROOT / "config/thresholds.yaml").read_text().splitlines()
    return json.loads(lines[lines.index("replay_74_plan:") + 1].split("value:", 1)[1])


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    card: str
    arm: str
    id: str
    day: int
    line: float
    stop: float
    maximum: float
    tag: str = ""
    rank: float = 0.0
    relative_volume: float = 0.0


@dataclass(frozen=True)
class CloseView:
    """Every bar series passed to the signal engine stops at this close."""

    clock: tuple
    bars: dict
    eligible: frozenset
    shares: dict  # available share counts in previous-close share basis
    earnings: frozenset  # issuer's first quarterly Item 2.02 in the window
    split_factors: dict  # ID -> effective session index -> new shares / old
    next_split_known: frozenset

    def __post_init__(self):
        require(self.clock and all(len(v) == len(self.clock) for v in self.bars.values()),
                "REFUSE_PREFIX")
        require(all(0 <= i < len(self.clock) for d in self.split_factors.values() for i in d),
                "REFUSE_PREFIX")

    @property
    def t(self):
        return len(self.clock) - 1

    def series(self, id_, first, last, basis=None):
        require(last <= self.t and (basis is None or basis <= self.t), "REFUSE_PREFIX")
        if first < 0 or id_ not in self.bars:
            return None
        rows = self.bars[id_][first:last + 1]
        if not rows or any(b is None for b in rows):
            return None
        splits = self.split_factors.get(id_, {})
        if basis is None or not splits:
            return rows
        out = []
        for i, b in enumerate(rows, first):
            f = math.prod(f for j, f in splits.items() if i < j <= basis)
            out.append(Bar(b.open / f, b.high / f, b.low / f, b.close / f, b.volume * f))
        return out


class Prefix:
    """A lazy view that cannot index after the current signal close."""

    def __init__(self, series, length):
        self.series, self.length = series, length

    def __len__(self):
        return self.length

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self.series[i] for i in range(*index.indices(len(self))))
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError(index)
        return self.series[index]


def ema(values, n):
    if len(values) < n:
        return None
    avg = fmean(values[:n])
    alpha = 2 / (n + 1)
    for v in values[n:]:
        avg += alpha * (v - avg)
    return avg


def trailing_ema(view, name, n):
    start = view.t
    rows = view.bars.get(name, ())
    if not rows or rows[start] is None:
        return None
    while start and rows[start - 1] is not None:
        start -= 1
    return ema([b.close for b in view.series(name, start, view.t, view.t)], n)


def market(view, cfg, arm):
    if arm == "without_market":
        return True
    a = cfg["signal_rules"]["A"]
    fund, n = ((cfg["arm_52w"]["market_fund"], cfg["arm_52w"]["market_sma_sessions"])
               if arm == "52w" else (a["sma_fund"], a["market_sma_sessions"]))
    last = view.series(fund, view.t - n + 1, view.t, view.t)
    if not last or last[-1].close <= fmean(b.close for b in last):
        return False
    if arm == "52w":
        return True
    fund, n = a["ema_fund"], a["market_ema_sessions"]
    avg = trailing_ema(view, fund, n)
    return avg is not None and view.bars[fund][view.t].close > avg


def close_signals(view, cfg, *, branches_only=False, exclusions=None, diagnostics=None):
    """Return close-only candidates plus the two pre-trigger comparison pools."""
    a, b = (cfg["signal_rules"][c] for c in ("A", "B"))
    t = view.t
    ranks, scan_b, hits = [], [], []
    for name in sorted(view.eligible):
        now = view.series(name, t, t)
        if not now:
            continue
        bar = now[0]
        if a["price_min"] <= bar.close <= a["price_max"]:
            raw = view.series(name, t - a["turn_sessions"], t - 1)
            ret = view.series(name, t - 1 - a["rank_sessions"], t - 1, t - 1)
            if raw and ret and fmean(x.close * x.volume for x in raw) >= a["turn_min"]:
                if name not in view.shares:
                    if diagnostics is not None:
                        diagnostics["missing_share_name_days"] += 1
                elif a["cap_min"] <= view.shares[name] * raw[-1].close <= a["cap_max"]:
                    ranks.append((ret[-1].close / ret[0].close - 1, name))
        if not b["price_min"] <= bar.close <= b["price_max"]:
            continue
        first = t - b["vol_sessions"]
        raw = view.series(name, first, t - 1)
        split = view.series(name, first, t - 1, t)
        if not raw or not split:
            continue
        avg = fmean(x.volume for x in split)
        if avg < b["vol_min"] or fmean(x.close * x.volume for x in raw) < b["turn_min"]:
            continue
        scan_b.append(name)
        if name in view.next_split_known or any(t - b["split_block"] < k <= t
                                               for k in view.split_factors.get(name, {})):
            continue
        half = b["base_half"]
        base = view.series(name, t - 2 * half, t - 1, t)
        if not base:
            continue
        before, after = base[:half], base[half:]
        pivot = max(x.high for x in base)
        if (min(x.low for x in after) < min(x.low for x in before) * (1 + b["rise"])
                or any(max(x.high for x in part) < pivot * b["base_high"] for part in (before, after))
                or bar.volume < b["rel_volume"] * avg):
            continue
        gold = view.series(name, t - b["gold_sessions"], t - 1)
        revival = view.series(name, t - b["revival_early"], t - b["revival_late"], t)
        line = max(pivot, b["gold_price"])
        if gold and all(x.close < b["gold_price"] for x in gold) and line < bar.close <= line * (1 + b["break_cap"]):
            tag = "Gold"
        elif (revival and revival[-1].close <= revival[0].close * (1 - b["revival_drop"])
              and pivot < bar.close <= pivot * (1 + b["break_cap"])):
            tag, line = "Revival", pivot
        else:
            continue
        if exclusions is not None:
            exclusions["B"].add(name)
        for arm in (("pooled",) if branches_only else ("pooled", tag)):
            hits.append(Signal("B", arm, name, t, line, line * b["stop_ratio"],
                               bar.close * b["entry_cap"], tag, relative_volume=bar.volume / avg))

    leaders = []
    arms = COUNT_ARMS["A"] if branches_only else ARMS["A"]
    primary_switch = market(view, cfg, "earnings")
    switch = {arm: market(view, cfg, arm) if arm in ("52w", "without_market") else primary_switch
              for arm in arms}
    ranks.sort(key=lambda x: (-x[0], x[1]))
    for rank, name in ranks[:math.ceil(len(ranks) * a["rank_share"])]:
        high = view.series(name, t - a["high_sessions"], t - 1, t - 1)
        n = a["tight_sessions"]
        tight = view.series(name, t - 2 * n, t - 1, t - 1)
        if not high or not tight or high[-1].close < a["near_high"] * max(x.high for x in high):
            continue

        def span(part):
            return (max(x.high for x in part) - min(x.low for x in part)) / fmean(x.close for x in part)

        if span(tight[n:]) > a["range_ratio"] * span(tight[:n]):
            continue
        leaders.append(name)
        bar = view.bars[name][t]
        pri = view.series(name, t - a["pivot_sessions"], t - 1, t)
        vol = view.series(name, t - a["vol_sessions"], t - 1, t)
        if not pri or not vol:
            continue
        pivot = max(x.high for x in pri)
        avg = fmean(x.volume for x in vol)
        if not (pivot < bar.close <= pivot * (1 + a["break_cap"])
                and bar.volume >= a["rel_volume"] * avg):
            continue
        if exclusions is not None:
            exclusions["A"].add(name)
        for arm, on in switch.items():
            if on and (name in view.earnings or arm in ("without_earnings", "52w")):
                hits.append(Signal("A", arm, name, t, max(pivot, bar.low), bar.low,
                                   bar.close * a["entry_cap"], rank=rank,
                                   relative_volume=bar.volume / avg if avg else 0))
    return hits, {"A": tuple(leaders), "B": tuple(scan_b)}


def count_signals(signals, clock, cfg):
    """No data past signal close, and no fill/return/benchmark logic."""
    raw, lower = defaultdict(set), defaultdict(set)
    prior = {}
    for s in sorted(signals, key=lambda s: (s.day, s.card, s.arm, s.id)):
        if s.arm not in COUNT_ARMS[s.card] or not in_fence(clock, s.day, s.card, cfg):
            continue
        key = s.card, s.arm
        raw[key].add((s.day, s.id))
        gap = cfg["count_branch"]["lower_bound_gap_sessions"][s.card]
        key_id = (*key, s.id)
        if key_id not in prior or s.day - prior[key_id] > gap:
            lower[key].add((s.day, s.id))
            prior[key_id] = s.day

    def numbers(pairs):
        return len(pairs), len({d for d, _ in pairs})

    return {(card, arm): (*numbers(raw[card, arm]), *numbers(lower[card, arm]))
            for card, arms in COUNT_ARMS.items() for arm in arms}


def in_fence(clock, day, card, cfg):
    first, last = (date.fromisoformat(cfg[k]) for k in ("design_first", "design_last"))
    return (0 <= day < len(clock) and first <= clock[day] <= last
            and day + cfg["design_last_signal_offset"][card] < len(clock) and clock[-1] <= last)


def branches(counts, cfg):
    branch = cfg["count_branch"]
    need = branch.get("need_signals")
    require(isinstance(need, dict) and set(need) == set(ARMS)
            and all(type(v) is int and v > 0 for v in need.values())
            and branch["bound"] == "lower", "REFUSE_COUNT_NEED")
    picked = {}
    for card in ARMS:
        *arms, closed = branch[f"card_{card}"]
        picked[card] = next((a for a in arms if counts[card, a][2] >= need[card]), closed)
    return picked


def count_lines(counts, cfg, diagnostics=None):
    picked = branches(counts, cfg)
    for (card, arm), numbers in counts.items():
        require(all(type(v) is int for v in numbers), "REFUSE_COUNT_OUTPUT")
        yield f"{card} {arm} raw={numbers[0]} raw_days={numbers[1]} lower={numbers[2]} lower_days={numbers[3]}"
    if diagnostics is not None:
        missing = diagnostics["missing_share_name_days"]
        require(type(missing) is int, "REFUSE_COUNT_OUTPUT")
        yield f"A missing_share_name_days={missing}"
    for card, arm in picked.items():
        yield f"BRANCH {card} {arm}"


def main(args):
    try:
        if args == ["--self-test"]:
            from test_score_74 import bars_fixture
            cfg = config()
            tape, signal = bars_fixture(cfg)
            diagnostics = {"missing_share_name_days": 0}
            signals, _ = close_signals(tape.view(signal.day), cfg, branches_only=True,
                                       diagnostics=diagnostics)
            print("\n".join(count_lines(count_signals(signals, tape.days, cfg), cfg, diagnostics)))
            return 0
        require(len(args) == 2 and args[0] == "--go-count", "REFUSE_MODE")
        from score_74 import run_count
        print("\n".join(run_count(args[1], config())))
    except Refusal as exc:
        print(exc, file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, OverflowError, RecursionError, csv.Error):
        print("REFUSE_INPUT", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
