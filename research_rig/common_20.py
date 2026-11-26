"""Plan 20 mechanics. No I/O; hours and minutes are UTC epoch units."""
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from heapq import merge
from math import ceil, isfinite, sqrt
from random import Random
from statistics import fmean, median, stdev

NAN = float("nan")


class Invalid(ValueError):
    pass


class NoFill(LookupError):
    pass


class Canceled(LookupError):
    pass


class InputFault(LookupError):
    def __init__(self, kind, hour):
        self.kind, self.hour = kind, hour
        super().__init__(kind, hour)


def policy(p):
    p = dict(p)
    p["start"] = (date.fromisoformat(p["first_date"]) - date(1970, 1, 1)).days * 24
    p["end"] = ((date.fromisoformat(p["last_date"]) - date(1970, 1, 1)).days + 1) * 24
    p["last_event_minute"] = int(datetime.fromisoformat(p["last_event_utc"]).timestamp() // 60)
    return p


def year(hour):
    return datetime.fromtimestamp(hour * 3600, timezone.utc).year


@dataclass(frozen=True)
class Notice:
    ticker: str
    symbol: str
    minute: int
    legacy_path_flag: bool = False


@dataclass(frozen=True)
class Contract:
    symbol: str
    asset: str
    launch_minute: int
    end_minute: int | None
    archive_tail_minute: int | None = None

    def active(self, minute):
        return self.launch_minute <= minute and (self.end_minute is None or minute < self.end_minute)


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
    favorable_terminal_price: float | None = None
    exit_minute: int | None = None

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


def setup(tape, minute, p, contract, *, trigger=None, earlier=None, screen=True,
          post_notice_only=False, counts=None, cancel_at=None):
    """Notice or ordinary trigger; None means no qualifying signal.

    LookupError is an unavailable window; it is never counted as a flat trade.
    """
    signal_start = minute // 60 + int(post_notice_only) if trigger is None else trigger - 2
    if trigger is None and not tape.bar(minute // 60):
        raise InputFault("klines", minute // 60)
    if earlier is not None:
        entry = (minute + p["notice_delay_minutes"] + 59) // 60 - int(earlier)
        reference = tape.at("close", minute // 60 - 1)
        if not isfinite(reference):
            raise InputFault("klines", minute // 60 - 1)
        signals = (minute // 60 - 1,)
    else:
        day = (minute // 1440) * 24
        signals = ()
        for d in range(p["red_days"]):
            start = day + 24 * d
            prior, last = start - 1, start + 23
            next_entry = start + 24 + p["entry_hour_utc"]
            if cancel_at is not None and cancel_at <= next_entry * 60:
                raise Canceled
            if contract.end_minute is not None and (last + 1) * 60 > contract.end_minute:
                return None
            if contract.archive_tail_minute is not None and (last + 1) * 60 > contract.archive_tail_minute:
                raise InputFault("unverified_end", contract.archive_tail_minute // 60)
            a, b = tape.at("close", prior), tape.at("close", last)
            if contract.launch_minute >= start * 60:
                if counts is not None:
                    counts["days_with_no_prelaunch_prior_close"] += 1
                continue
            if not isfinite(a) or not isfinite(b):
                raise InputFault("klines", prior if not isfinite(a) else last)
            signals += (prior, last)
            if b < a:
                entry = next_entry
                break
        else:
            return None
    if entry >= p["end"]:
        raise InputFault("klines", entry)
    if contract.end_minute is not None and entry * 60 >= contract.end_minute:
        raise NoFill
    if contract.archive_tail_minute is not None and entry * 60 >= contract.archive_tail_minute:
        raise InputFault("unverified_end", contract.archive_tail_minute // 60)
    high = [tape.at("high", h) for h in range(signal_start, entry)]
    if not high:
        if earlier is not None or post_notice_only:
            return None
        raise InputFault("klines", signal_start)
    if not all(map(isfinite, high)):
        raise InputFault("klines", next(h for h in range(signal_start, entry) if not isfinite(tape.at("high", h))))
    top = max(high)
    if earlier is not None and screen and top < reference * (1 + p["pump_min_pct"] / 100):
        return None
    return Setup(entry, top, tuple(sorted(set(signals + tuple(range(signal_start, entry))))), minute // 60)


def execution(tape, signal, p, contract):
    """Return exit minute, adverse fill, reason and shown terminal price."""
    h = signal.entry
    limit = h + p["hold_hours"]
    tail = contract.archive_tail_minute
    if tail is not None and h * 60 >= tail:
        raise InputFault("unverified_end", tail // 60)
    if not tape.bar(h):
        raise InputFault("klines", h)
    end = contract.end_minute
    if not contract.active(h * 60):
        raise InputFault("klines", h)
    if tape.at("volume", h) == 0:
        raise NoFill
    initial = tape.at("open", h)
    stop = min(signal.high, initial * (1 + p["stop_cap_pct"] / 100))
    last_positive = None
    stop_at = p["end"] * 60 if end is None else min(end, p["end"] * 60)
    if tail is not None:
        stop_at = min(stop_at, tail)
    for i in range(h, min((stop_at + 59) // 60, tape.last_trade + 1)):
        if not tape.bar(i) or tape.at("volume", i) == 0:
            continue
        if i >= limit:
            return (i * 60, tape.at("open", i), "time" if i == limit else "deferred_time", None)
        if tape.at("high", i) >= stop:
            return (i * 60, max(stop, tape.at("open", i)), "stop", None)
        last_positive = i
    if end is not None and end < p["end"] * 60 and last_positive is not None:
        shown = tape.at("close", last_positive)
        return end, max(stop, shown), "terminal_close", shown
    if tail is not None and stop_at == tail:
        raise InputFault("unverified_end", tail // 60)
    raise InputFault("klines", limit)


def settled(tape, start, exit_minute, *, terminal=False, validate_only=False):
    if start * 60 == exit_minute:
        return
    exit_hour = exit_minute // 60
    s = tape.settlements
    left, right = bisect_right(s, start), bisect_right(s, exit_hour)
    # Published settlement intervals can vary by coin and over time. Envelope
    # the hold with adjacent observations, rather than imputing zero funding.
    if not left:
        raise InputFault("fundingRate", start)
    if right == len(s) and (not terminal or exit_hour - s[-1] >= tape.funding[s[-1]][0]):
        raise InputFault("fundingRate", min(exit_hour, s[-1] + tape.funding[s[-1]][0]))
    for j in range(left, min(right + 1, len(s))):
        if s[j] - s[j - 1] != tape.funding[s[j]][0]:
            raise InputFault("fundingRate", min(s[j], s[j - 1] + tape.funding[s[j]][0]))
    for h in s[left:right]:
        mark = tape.at("mark", h)
        if not isfinite(mark):
            raise InputFault("markPriceKlines", h)
        if not validate_only:
            yield mark * tape.funding[h][1]


def evaluate(tape, signal, p, contract, *, validate_only=False):
    h = signal.entry
    e, price, reason, shown = execution(tape, signal, p, contract)
    funding = tuple(settled(tape, h, e, terminal=reason == "terminal_close", validate_only=validate_only))
    if validate_only:
        return None
    start = tape.at("open", h)
    return Trade(year(signal.sample_hour), 1 - price / start, sum(funding) / start, 1 + price / start,
                 reason, shown / start if shown is not None else None, e)


def last_close_version(trade):
    ratio = trade.favorable_terminal_price
    if ratio is None:
        return trade
    return Trade(trade.year, 1 - ratio, trade.funding, 1 + ratio, trade.exit_reason, ratio, trade.exit_minute)


def pump_triggers(tape, symbol, p):
    for h in range(max(tape.start + 3, p["start"]), min(tape.end, p["last_event_minute"] // 60 + 1)):
        ref = tape.at("close", h - 3)
        if not isfinite(ref):
            continue
        a, b = tape.at("high", h - 2), tape.at("high", h - 1)
        if isfinite(a) and isfinite(b) and max(a, b) >= ref * (1 + p["pump_min_pct"] / 100):
            yield h, symbol


def ordinary(tapes, contracts, notice_index, p, counts=None, *, validate_only=False, absent=None, domains=None,
             source_counts=None):
    """Ordinary pumps, with one trigger per rolling asset week across aliases."""
    window = p["exclusion_days"] * 24
    blocks = {}
    if counts is None:
        counts = Counter()
    triggers = merge(*(pump_triggers(tape, symbol, p) for symbol, tape in tapes.items()))
    for h, symbol in triggers:
        if domains is not None and symbol in domains and not any(
                lo <= min(h - 3, h // 24 * 24 - 1) and h // 24 * 24 + p["red_days"] * 24
                + p["entry_hour_utc"] + p["hold_hours"] + 8 < hi for lo, hi in domains[symbol]):
            counts["out_of_predeclared_supplement_domain"] += 1
            continue
        tape = tapes[symbol]
        active = [c for c in contracts[symbol] if c.active(h * 60)]
        if len(active) != 1 or not tape.bar(h):
            counts["not_trading_at_trigger"] += 1
            if absent is not None:
                absent[symbol] += 1
            continue
        contract = active[0]
        if (h - 3) * 60 < contract.launch_minute:
            counts["trigger_lookback_before_dated_launch"] += 1
            continue
        if h < blocks.get(contract.asset, p["start"]):
            continue
        notice_minutes = notice_index.get(contract.asset, ())
        k = bisect_left(notice_minutes, (h - window) * 60)
        if k < len(notice_minutes) and notice_minutes[k] <= h * 60:
            continue
        blocks[contract.asset] = h + window
        try:
            next_notice = notice_minutes[k] if k < len(notice_minutes) else None
            signal = setup(tape, h * 60, p, contract, trigger=h, counts=counts, cancel_at=next_notice)
            if not signal:
                counts["no_red_day"] += 1
                continue
            trade = evaluate(tape, signal, p, contract, validate_only=validate_only)
            counts["traded"] += 1
            if source_counts is not None:
                source = "supplement_only_symbols" if domains is not None and symbol in domains else "store_symbols"
                source_counts[source] += 1
            if not validate_only:
                counts[trade.exit_reason] += 1
                yield trade, k == len(notice_minutes) or notice_minutes[k] > trade.exit_minute
        except NoFill:
            counts["no_fill"] += 1
        except Canceled:
            counts["canceled_before_entry"] += 1
        except InputFault as error:
            error.symbol = symbol
            raise


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
                placebo_distinct_set_means=len(set(draws)),
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
