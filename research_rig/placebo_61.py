"""One approved pre-freeze dispersion measurement; stdout is five aggregates only."""
from bisect import bisect_left
from collections import defaultdict
from fractions import Fraction
from math import isfinite
from pathlib import Path
import re
import runpy
from statistics import mean, median, stdev
import sys
from types import SimpleNamespace

blind = SimpleNamespace(**runpy.run_path(str(Path(__file__).resolve().with_name("count_61.py"))))
p = blind.p
CLOSE = re.compile(rb'\{"c":"([^"\\]+)"')
LIQUIDITY_FLOOR = 1_000_000
FIELDS = ("placebo_observations", "events_contributing", "sample_sd_bps", "mad_scaled_bps",
          "between_ex_date_variance_share")


def read_close(blob, row):
    matched = CLOSE.match(blob, row["offset"])
    p.need(matched is not None, "P61_PLACEBO_STRUCTURE")
    v = p.exact(p.money(matched[1].decode("ascii")))
    p.need(v > 0, "P61_PLACEBO_STRUCTURE")
    return v


def leg_return(blob, rows, actions, start, end):
    buy, sell = (read_close(blob, rows[day]) for day in (start, end))
    shares, cash = Fraction(1), Fraction(0)
    for ex, kind, value, *_ in actions:
        if not start < ex <= end:
            continue
        if kind == "split":
            shares *= p.exact(value)
        else:
            cash += shares * p.exact(value)
    return (shares * sell + cash - buy) / buy


def liquid(blob, days, e, entry, stock_rows):
    pad = days[bisect_left(days, e.start):bisect_left(days, e.early)]
    p.need(len(pad) == blind.PADDING and pad[-1] < entry, "P61_PLACEBO_PADDING")
    dollars = []
    for day in pad:
        row = stock_rows[day]
        matched = blind.ROW.match(blob, row["offset"])
        p.need(row["positive"] and matched is not None, "P61_PLACEBO_PADDING")
        dollars.append(read_close(blob, row) * int(matched[2]))
    return sorted(dollars)[len(pad)//2] >= LIQUIDITY_FLOOR


def measure(q, days, verified, blob, liquid_only=False):
    actions = verified[1]
    bars = blind.strip_bars(blob, indexed=True)
    groups = defaultdict(list)
    contributing = eligible = 0
    for e, status, entry, ex, raw in blind.screening(q, days, verified, bars, indexed=True):
        if status != "price_blind_upper_bound":
            continue
        if liquid_only and not liquid(blob, days, e, entry, raw["stock"]):
            continue
        eligible += 1
        first = bisect_left(days, e.start)
        last = bisect_left(days, entry) - 3
        observed = 0
        # Choose at most three nearest positive-volume matched pairs, using only
        # the redacted flags. The latest endpoint is entry-minus-three sessions.
        for i in range(last, first, -1):
            start, end = days[i-1], days[i]
            if not all(raw[leg].get(day, {}).get("positive") for leg in ("stock", "IWM") for day in (start, end)):
                continue
            p.need(e.start <= start < end < entry < ex and i <= last, "P61_PLACEBO_CLOCK")
            stock, iwm = (leg_return(blob, raw[leg], actions[e.a][leg][0], start, end) for leg in ("stock", "IWM"))
            groups[ex].append(float((stock - iwm) * 10_000))
            observed += 1
            if observed == 3:
                break
        contributing += bool(observed)
    values = [v for vs in groups.values() for v in vs]
    p.need(len(values) > 1 and len(groups) > 1, "P61_PLACEBO_COUNT")
    center = mean(values)
    center_md = median(values)
    total = sum((v - center)**2 for v in values)
    p.need(total > 0, "P61_PLACEBO_VARIANCE")
    between = sum(len(g) * (mean(g) - center)**2 for g in groups.values())
    out = (len(values), contributing, stdev(values), 1.482602218505602 * median(abs(v-center_md) for v in values),
           min(1.0, between / total))
    p.need(all(isfinite(v) and v >= 0 for v in out), "P61_PLACEBO_VARIANCE")
    published = dict(zip(FIELDS, out))
    if liquid_only:
        published["liquidity_subset_events"] = eligible
    return published


if __name__ == "__main__":
    # No file writes and no exception payload from private input.
    try:
        opts = sys.argv[1:]
        p.need(opts in ([], ["--liquid-subset"]), "P61_PLACEBO_ARGS")
        sys.stdout.buffer.write(p.render(measure(*blind.sealed(), liquid_only=bool(opts))))
    except (Exception, KeyboardInterrupt):
        sys.exit(2)
