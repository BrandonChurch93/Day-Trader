"""Plan 20 mechanics. No I/O; hours and minutes are UTC epoch units."""
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from math import ceil, isfinite, sqrt
from random import Random
from statistics import fmean, median, stdev

NAN = float("nan")


class Invalid(ValueError):
    pass


class NoFill(LookupError):
    pass


def policy(p):
    p = dict(p)
    p["start"] = (date.fromisoformat(p["first_date"]) - date(1970, 1, 1)).days * 24
    p["end"] = ((date.fromisoformat(p["last_date"]) - date(1970, 1, 1)).days + 1) * 24
    return p


def year(hour):
    return datetime.fromtimestamp(hour * 3600, timezone.utc).year


@dataclass(frozen=True)
class Notice:
    ticker: str
    symbol: str
    minute: int


@dataclass(frozen=True)
class Setup:
    entry: int
    high: float
    signals: tuple
    sample_hour: int


@dataclass(frozen=True)
class Trade:
    year: int
    price: float
    funding: float
    turnover: float
    exit_reason: str

    @property
    def stopped(self):
        return self.exit_reason == "stop"

    def net(self, bps):
        return self.price + self.funding - self.turnover * bps / 10000


class Tape:
    def __init__(self, start, end):
        self.start, self.end = start, end
        self.fields = {key: array("d", [NAN]) * (end - start)
                       for key in ("open", "high", "close", "volume", "mark")}
        self.funding = {}
        self.settlements = ()
        self.last_trade = start - 1

    def at(self, key, h):
        return self.fields[key][h - self.start] if self.start <= h < self.end else NAN

    def set(self, key, h, x):
        if not self.start <= h < self.end or isfinite(self.at(key, h)):
            raise Invalid("outside tape or duplicate")
        self.fields[key][h - self.start] = x
        if key == "open":
            self.last_trade = max(self.last_trade, h)

    def bar(self, h):
        return isfinite(self.at("open", h))

    def finish(self):
        self.settlements = tuple(sorted(self.funding))


def setup(tape, minute, p, *, trigger=None, earlier=None, screen=True):
    """Notice or ordinary trigger; None means no qualifying signal.

    LookupError is an unavailable window; it is never counted as a flat trade.
    """
    signal_start = minute // 60 if trigger is None else trigger - 2
    if not tape.bar(signal_start):
        raise LookupError
    if earlier is not None:
        entry = (minute + p["notice_delay_minutes"] + 59) // 60 - int(earlier)
        reference = tape.at("close", minute // 60 - 1)
        if not isfinite(reference):
            raise LookupError
        signals = (minute // 60 - 1,)
    else:
        day = (minute // 1440) * 24
        signals = ()
        for d in range(p["red_days"]):
            start = day + 24 * d
            prior, last = start - 1, start + 23
            a, b = tape.at("close", prior), tape.at("close", last)
            if not isfinite(a) or not isfinite(b):
                raise LookupError
            signals += (prior, last)
            if b < a:
                entry = start + 24 + p["entry_hour_utc"]
                break
        else:
            return None
    if entry >= p["end"]:
        raise LookupError
    high = [tape.at("high", h) for h in range(signal_start, entry)]
    if not high or not all(map(isfinite, high)):
        raise LookupError
    top = max(high)
    if earlier is not None and screen and top < reference * (1 + p["pump_min_pct"] / 100):
        return None
    return Setup(entry, top, tuple(sorted(set(signals + tuple(range(signal_start, entry))))), minute // 60)


def execution_hours(tape, signal, p):
    """Determine the exit clock and price, before applying costs or returns."""
    h = signal.entry
    limit = h + p["hold_hours"]
    if not tape.bar(h):
        raise LookupError
    if tape.at("volume", h) == 0:
        raise NoFill
    initial = tape.at("open", h)
    stop = min(signal.high, initial * (1 + p["stop_cap_pct"] / 100))
    last = min(tape.last_trade, p["end"] - 1)
    for i in range(h, last + 1):
        if not tape.bar(i):
            raise LookupError
        if tape.at("volume", i) == 0:
            continue
        if i >= limit:
            return i, tape.at("open", i), "time" if i == limit else "deferred_time"
        if tape.at("high", i) >= stop:
            return i, max(stop, tape.at("open", i)), "stop"
    if last < p["end"] - 1:
        # A terminal close is booked when the last candle completes, not at
        # that candle's open. An internal gap is never considered terminal.
        return last + 1, tape.at("close", last), "terminal_close"
    raise LookupError


def settled(tape, start, exit_hour, *, terminal=False, validate_only=False):
    if start == exit_hour:
        return
    s = tape.settlements
    left, right = bisect_right(s, start), bisect_right(s, exit_hour)
    # Published settlement intervals can vary by coin and over time. Envelope
    # the hold with adjacent observations, rather than imputing zero funding.
    if not left:
        raise LookupError
    if right == len(s) and (not terminal or exit_hour - s[-1] >= tape.funding[s[-1]][0]):
        raise LookupError
    for j in range(left, min(right + 1, len(s))):
        if s[j] - s[j - 1] != tape.funding[s[j]][0]:
            raise LookupError
    for h in s[left:right]:
        mark = tape.at("mark", h)
        if not isfinite(mark):
            raise LookupError
        if not validate_only:
            yield mark * tape.funding[h][1]


def evaluate(tape, signal, p, *, validate_only=False):
    h = signal.entry
    e, price, reason = execution_hours(tape, signal, p)
    funding = tuple(settled(tape, h, e, terminal=reason == "terminal_close", validate_only=validate_only))
    if validate_only:
        return None
    start = tape.at("open", h)
    return Trade(year(signal.sample_hour), 1 - price / start, sum(funding) / start, 1 + price / start, reason)


def ordinary(tape, notice_minutes, p, counts=None):
    """Greedy first trigger per rolling exclusion window, then the red-day rule."""
    window = p["exclusion_days"] * 24
    block = p["start"]
    if counts is None:
        counts = Counter()
    for h in range(max(tape.start + 3, p["start"]), min(tape.end, p["end"])):
        if h < block:
            continue
        ref = tape.at("close", h - 3)
        a, b = tape.at("high", h - 2), tape.at("high", h - 1)
        if not all(map(isfinite, (ref, a, b))) or max(a, b) < ref * (1 + p["pump_min_pct"] / 100):
            continue
        k = bisect_left(notice_minutes, (h - window) * 60)
        if k < len(notice_minutes) and notice_minutes[k] <= h * 60:
            continue
        if not tape.bar(h):
            counts["not_trading_at_trigger"] += 1
            continue
        block = h + window
        try:
            signal = setup(tape, h * 60, p, trigger=h)
            if signal:
                trade = evaluate(tape, signal, p)
                counts["traded"] += 1
                counts[trade.exit_reason] += 1
                yield trade
            else:
                counts["no_red_day"] += 1
        except NoFill:
            counts["no_fill"] += 1
        except LookupError:
            counts["other"] += 1


def percentile(values, percent):
    ordered = sorted(values)
    k = (len(ordered) - 1) * percent / 100
    lo, hi = int(k), ceil(k)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def judgment(p, judged, pools, check=lambda: None):
    n = len(judged)
    by_year = Counter(y for y, _ in judged)
    net = [r for _, r in judged]
    mean = fmean(net) if n else None
    deviation = stdev(net) if n > 1 else None
    t_stat = mean / (deviation / sqrt(n)) if deviation else None
    trimmed = fmean(sorted(net)[:-p["drop_best"]]) if n > p["drop_best"] else None
    draws = []
    if n and all(len(pools.get(y, ())) >= count for y, count in by_year.items()):
        rng = Random(p["placebo_seed"])
        for i in range(p["placebo_draws"]):
            if not i % 100:
                check()
            draws.append(fmean(v for y, k in sorted(by_year.items()) for v in rng.sample(pools[y], k)))
    cutoff = percentile(draws, p["placebo_percentile"]) if draws else None
    marks = dict(count=n >= p["min_trades"], mean=mean is not None and mean > 0,
                 placebo=cutoff is not None and mean > cutoff, trimmed=trimmed is not None and trimmed > 0,
                 t_stat=t_stat is not None and t_stat >= p["min_t_stat"])
    return dict(passes=all(marks.values()), marks=marks, mean=mean, trimmed_mean=trimmed,
                t_stat=t_stat, placebo_cut=cutoff, placebo_draws=len(draws), placebo_set_means=draws,
                placebo_pool_by_year={y: len(v) for y, v in sorted(pools.items())})


def summary(trades, bps, *, split=True):
    values = [t.net(bps) for t in trades]
    n = len(values)
    row = dict(count=n, mean=fmean(values) if n else None, median=median(values) if n else None,
               winners=sum(v > 0 for v in values) / n if n else None,
               stopped=sum(t.stopped for t in trades) / n if n else None,
               worst=min(values) if n else None, funding=fmean(t.funding for t in trades) if n else None,
               terminal_closes=sum(t.exit_reason == "terminal_close" for t in trades),
               deferred_timed_exits=sum(t.exit_reason == "deferred_time" for t in trades))
    if split:
        buckets = defaultdict(list)
        for t in trades:
            buckets[t.year].append(t)
        row["by_year"] = {y: summary(ts, bps, split=False) for y, ts in sorted(buckets.items())}
    return row
