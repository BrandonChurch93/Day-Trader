"""Plan 51 strategy. No IO. Reuse Replay 13's point-in-time and execution rules."""
from bisect import bisect_left
from collections import deque
from dataclasses import dataclass
from datetime import date
from fractions import Fraction
import heapq
import math
import random
from statistics import mean

try:
    from . import common_13 as prior
except ImportError:
    import common_13 as prior


@dataclass
class Day:
    start: int
    month: str
    active: bool
    ranked: tuple
    listed: tuple


class Gate:
    def __init__(self, n):
        self.history = deque(maxlen=n)
        self.total = Fraction(0)
        self.missing = 0

    def add(self, observation):
        if len(self.history) == self.history.maxlen:
            expired = self.history[0]
            if expired is None:
                self.missing -= 1
            else:
                self.total -= expired
        if observation is None:
            self.missing += 1
        else:
            if not isinstance(observation, Fraction):
                observation = Fraction(str(observation))
            self.total += observation
        self.history.append(observation)
        return (len(self.history) == self.history.maxlen
                and self.missing == 0 and self.total > 0)


def exact_close(series, t):
    if hasattr(series, "exact_close"):
        return series.exact_close(t)
    return Fraction(str(series.bars[t].c))


def rank_at(snapshots, data, t, p):
    listed, ranked, _ = prior.weekly_universe(snapshots, data, t, p)
    latest = t - prior.HOUR
    earlier = latest - p["rise_days"] * prior.DAY
    # Membership and segmentation come from Replay 13; only exact tie handling
    # changes. Native-close ratios do not use a binary float for ranking.
    ranked.sort(key=lambda a: (-exact_close(data[a.pair], latest) /
                               exact_close(data[a.pair], earlier), a.coin))
    return listed, ranked


def signal_return(data, ranked, start, end, k):
    # Nothing observed after the latest completed hourly close enters this value.
    a, b = start - prior.HOUR, end - prior.HOUR
    if len(ranked) < k:
        return None
    changes = []
    for asset in ranked:
        series = data[asset.pair]
        bars = series.bars
        if not (asset.begin <= a < b < asset.end and a in bars and b in bars):
            return None
        changes.append(exact_close(series, b) / exact_close(series, a) - 1)
    return mean(changes[:k]) - mean(changes)


def year_days(snapshots, data, start, end, p):
    n, k = p["lookback_days"], p["hot_n"]
    gate = Gate(n)
    before = ()
    for t in range(start - n * prior.DAY, end, prior.DAY):
        listed, ranked = rank_at(snapshots, data, t, p)
        on = gate.add(signal_return(data, before, t - prior.DAY, t, k))
        before = tuple(ranked)
        if t >= start:
            yield Day(t, prior.utc(t).strftime("%Y-%m"), on, before, tuple(listed))


def schedule(mask):
    spells, gaps = [], [0]
    for i, active in enumerate(mask):
        if active:
            if not i or not mask[i - 1]:
                spells.append(0)
            spells[-1] += 1
        else:
            if i and mask[i - 1]:
                gaps.append(0)
            gaps[-1] += 1
    if mask and mask[-1]:
        gaps.append(0)
    return spells, gaps


def shuffled_mask(spells, gaps, rng):
    if not spells:
        return [False] * gaps[0]
    lengths = list(spells)
    places = [i for i, length in enumerate(gaps) if length]
    values = [gaps[i] for i in places]
    rng.shuffle(lengths)
    rng.shuffle(values)
    placed = [0] * len(gaps)
    for i, v in zip(places, values):
        placed[i] = v
    mask = [False] * placed[0]
    for i, length in enumerate(lengths):
        mask.extend([True] * length)
        mask.extend([False] * placed[i + 1])
    return mask


class Fills:
    def __init__(self, data, p):
        self.data = data
        self.look = p["max_missing_hours"] * prior.HOUR
        self.fee = p["cost_bps_per_side"] / 10_000
        self.buys, self.sells = {}, {}

    def buy(self, asset, t):
        key = asset, t
        if key not in self.buys:
            self.buys[key] = self.data[asset.pair].open_at_or_after(
                max(t, asset.begin), min(t + self.look + prior.HOUR, asset.end))
        return self.buys[key]

    def sell(self, asset, t, end):
        key = asset, t, end
        if key not in self.sells:
            series = self.data[asset.pair]
            limit = min(t, asset.end)
            hit = series.open_at_or_after(t, min(end + prior.HOUR, asset.end))
            if hit is None:
                j = bisect_left(series.times, limit) - 1
                hit = (None, series.bars[series.times[j]].c) if j >= 0 else (None, 0)
            self.sells[key] = hit
        return self.sells[key]


def portfolio(fills, steps, end):
    """Trade only changes. Pending exits are not spendable until their release."""
    fee, cash, terminal = fills.fee, 1.0, 0.0
    held, queue = {}, []
    for t, desired, slots in steps:
        for asset in sorted(held.keys() - set(desired)):
            quantity = held.pop(asset)
            when, px = fills.sell(asset, t, end)
            proceed = quantity * px * (1 - fee)
            if when is None:
                terminal += proceed
            else:
                heapq.heappush(queue, (when, proceed))
        while queue and queue[0][0] <= t:
            cash += heapq.heappop(queue)[1]
        parts = slots - len(held)
        if parts > 0 and cash > 0:
            budget = cash / parts
            for asset in desired:
                if asset in held:
                    continue
                fill = fills.buy(asset, t)
                if fill is not None:
                    held[asset] = budget / (fill[1] * (1 + fee))
                    cash -= budget
    for asset, quantity in held.items():
        _, px = fills.sell(asset, end, end)
        terminal += quantity * px * (1 - fee)
    return cash + terminal + math.fsum(v for _, v in queue)


def metrics(total, twin_factors, without, wins, p):
    twin_net = [x - 1 for x in twin_factors]
    twin_net = [x - 1 for x in twin_factors]
    p_rank = (1 + sum(v >= total for v in twin_net)) / (1 + len(twin_net))
    q = prior.percentile(twin_net, 90)
    marks = {"positive_net": total > 0, "positive_full_years": wins >= p["min_positive_years"],
             "above_twin_p90": total > q, "family_tail_guard": p_rank <= p["twin_p_max"],
             "without_best_month": without > 0}
    return {"net": total, "positive_full_years": wins, "without_best_month": without,
            "twin_p90": q, "twin_p_rank": p_rank, "marks": marks, "pass": all(marks.values())}


def day_factor(fills, days, mask, end, k):
    return portfolio(fills, ((d.start, d.ranked[:k] if on else (), k)
                             for d, on in zip(days, mask)), end)


def yardsticks(fills, days, end, p):
    k = p["hot_n"]
    weeks = [d for d in days if prior.utc(d.start).weekday() == 0]
    first = days[0].start
    bar = fills.data["BTCUSDT"].bars
    btc = (bar[end].o / bar[first].o * (1 - fills.fee) / (1 + fills.fee) - 1
           if first in bar and end in bar else None)
    return {"weekly_rule_a": portfolio(fills, ((d.start, d.ranked[:k], k) for d in weeks), end) - 1,
            "weekly_universe": portfolio(fills, ((d.start, d.ranked, len(d.ranked)) for d in weeks), end) - 1,
            "daily_always_on": day_factor(fills, days, [True] * len(days), end, k) - 1,
            "btc": btc}


def counts(panels):
    return {"days": sum(len(days) for days, _ in panels.values()),
            "in_market_days": sum(d.active for days, _ in panels.values() for d in days),
            "spells_per_year": {y: len(schedule([d.active for d in days])[0])
                                for y, (days, _) in panels.items()},
            "coins_on_list_per_year": {y: len({a.coin for d in days for a in d.listed})
                                       for y, (days, _) in panels.items()}}


def prepare(snapshots, data, p):
    panels = {}
    for yr in p["years"]:
        start, stop = boundaries(yr)
        end = stamp(p["judged_stop"]) if yr == p["years"][-1] else stop
        panels[str(yr)] = (list(year_days(snapshots, data, start, end, p)), end)
    return panels


def run(data, panels, snapshots, p):
    k = p["hot_n"]
    fills = Fills(data, p)
    rng = random.Random(p["twin_seed"])
    twins = [1.0] * p["twin_draws"]
    annual, months = {}, {}
    for yr, (days, end) in panels.items():
        mask = [d.active for d in days]
        spells, gaps = schedule(mask)
        annual[yr] = {"net": day_factor(fills, days, mask, end, k) - 1,
                      "days": len(days), "active_days": sum(mask), "spells": len(spells),
                      **yardsticks(fills, days, end, p)}
        for j in range(len(twins)):
            twins[j] *= day_factor(fills, days, shuffled_mask(spells, gaps, rng), end, k)
        groups = {}
        for d in days:
            groups.setdefault(d.month, []).append(d)
        for month, group in groups.items():
            months[month] = day_factor(fills, group, [d.active for d in group],
                                       group[-1].start + prior.DAY, k) - 1
    best = min(months, key=lambda m: (-months[m], m))
    without = math.prod(day_factor(fills, days, [d.active and d.month != best for d in days], end, k)
                        for days, end in panels.values()) - 1
    total = math.prod(1 + row["net"] for row in annual.values()) - 1
    wins = sum(annual[str(yr)]["net"] > 0 for yr in p["years"][:-1])
    start, end = stamp(p["judged_stop"]), stamp(p["shown_stop"])
    days = list(year_days(snapshots, data, start, end, p))
    shown = {"net": day_factor(fills, days, [d.active for d in days], end, k) - 1,
             "days": len(days), "active_days": sum(d.active for d in days), **yardsticks(fills, days, end, p)}
    verdict = metrics(total, twins, without, wins, p)
    yardstick_total = {k: (math.prod(1 + row[k] for row in annual.values()) - 1
                           if all(row[k] is not None for row in annual.values()) else None)
                      for k in ("weekly_rule_a", "weekly_universe", "daily_always_on", "btc")}
    return {"annual": annual, "judged_yardsticks": yardstick_total,
            "monthly_standalone_net": months, "best_month": best, "shown_only": shown,
            "label": "passed on reused years" if verdict["pass"] else "did not pass on reused years",
            **verdict}


def stamp(text):
    return prior.stamp(date.fromisoformat(text))


def boundaries(y):
    january = date(y, 1, 1)
    first_monday = january.toordinal() + (-january.weekday()) % 7
    return prior.stamp(date.fromordinal(first_monday)), prior.stamp(date(y + 1, 1, 1))
