"""Plan 20 mechanics. No I/O; hours and minutes are UTC epoch units."""
from array import array
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
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
    if (p["funding_interval_rule"], p["missing_funding_rule"], p["missing_funding_floor_pct"]) != (
            "single_aligned_switch", "adverse_max_abs_contract_rate", 2.0):
        raise Invalid("unsupported funding policy")
    if p["missing_hold_bar_rule"] != "adverse_stop_next_executable":
        raise Invalid("unsupported missing hold bar policy")
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
    new_positions_halted_minute: int | None = None

    def active(self, minute):
        return self.launch_minute <= minute and (self.end_minute is None or minute < self.end_minute)

    def new_position_allowed(self, minute):
        return (self.active(minute) and
                (self.new_positions_halted_minute is None or minute < self.new_positions_halted_minute))


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
    missing_funding_settlements: int = 0
    missing_funding_debit: float = 0.0

    @property
    def stopped(self):
        return self.exit_reason in {"stop", "gap_stop", "gap_terminal_close"}

    @property
    def gap_close(self):
        return self.exit_reason in {"gap_stop", "gap_terminal_close"}

    @property
    def terminal_close(self):
        return self.exit_reason in {"terminal_close", "gap_terminal_close"}

    def net(self, bps):
        return self.price + self.funding - self.turnover * bps / 10000


class Tape:
    def __init__(self, start, end, funding_peak_contracts=()):
        self.start, self.end = start, end
        self.fields = {key: array("d", [NAN]) * (end - start)
                       for key in ("open", "high", "close", "volume", "mark")}
        self.funding = {}
        self.funding_peaks = dict.fromkeys(funding_peak_contracts, 0.0)
        self.settlements = ()

    def at(self, key, h):
        return self.fields[key][h - self.start] if self.start <= h < self.end else NAN

    def set(self, key, h, x):
        if not self.start <= h < self.end or isfinite(self.at(key, h)):
            raise Invalid("outside tape or duplicate")
        self.fields[key][h - self.start] = x

    def bar(self, h):
        return isfinite(self.at("open", h))

    def finish(self):
        self.settlements = tuple(sorted(self.funding))

    def funding_peak(self, contract):
        if contract in self.funding_peaks:
            return self.funding_peaks[contract]
        return max((abs(rate) for h, (_, rate) in self.funding.items()
                    if contract.launch_minute <= h * 60 and
                    (contract.end_minute is None or h * 60 <= contract.end_minute)), default=0.0)


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
    if not contract.new_position_allowed(entry * 60):
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


def execution(tape, signal, p, contract, *, continue_gaps=False):
    """Return exit minute, adverse fill, reason and shown terminal price."""
    h = signal.entry
    limit = h + p["hold_hours"]
    tail = contract.archive_tail_minute
    if tail is not None and h * 60 >= tail:
        raise InputFault("unverified_end", tail // 60)
    if not contract.new_position_allowed(h * 60):
        raise NoFill
    if not tape.bar(h):
        raise InputFault("klines", h)
    end = contract.end_minute
    if tape.at("volume", h) == 0:
        raise NoFill
    initial = tape.at("open", h)
    stop = min(signal.high, initial * (1 + p["stop_cap_pct"] / 100))
    last_positive = None
    missing_stop = False
    stop_at = p["end"] * 60 if end is None else min(end, p["end"] * 60)
    if tail is not None:
        stop_at = min(stop_at, tail)
    for i in range(h, (stop_at + 59) // 60):
        if not tape.bar(i):
            missing_stop |= not continue_gaps
            continue
        if tape.at("volume", i) == 0:
            continue
        if missing_stop:
            return i * 60, max(stop, tape.at("open", i)), "gap_stop", None
        if i >= limit:
            return (i * 60, tape.at("open", i), "time" if i == limit else "deferred_time", None)
        if tape.at("high", i) >= stop:
            return (i * 60, max(stop, tape.at("open", i)), "stop", None)
        last_positive = i
    if end is not None and end < p["end"] * 60 and last_positive is not None:
        shown = tape.at("close", last_positive)
        return end, max(stop, shown), "gap_terminal_close" if missing_stop else "terminal_close", shown
    if tail is not None and stop_at == tail:
        raise InputFault("unverified_end", tail // 60)
    raise InputFault("klines", limit)


def funding_clock_gap(left, old, right, new):
    """Classify adjacent labelled clocks on their UTC-multiple grids."""
    if old not in {1, 2, 4, 8} or new not in {1, 2, 4, 8} or left >= right or left % old or right % new:
        return "unlabelled_gap", ()
    if old == new:
        missing = range(left + old, right, old)
        return ("labelled_missing" if missing else "regular"), missing
    # The switch can take effect at any hour after left, through right. It
    # must occur before the next old-grid settlement would be due, and after
    # the last interior new-grid clock. Otherwise an omission is ambiguous.
    if max(left, right - new) + 1 <= min(right, left + old):
        return "consistent_interval_change", ()
    return "unlabelled_gap", ()


def settled(tape, start, exit_minute, p, contract, *, terminal=False, validate_only=False, input_fault=None):
    assert input_fault is None or validate_only
    if start * 60 == exit_minute:
        return
    exit_hour = exit_minute // 60
    s = tape.settlements
    first = bisect_left(s, (contract.launch_minute + 59) // 60)
    end = len(s) if contract.end_minute is None else bisect_right(s, contract.end_minute // 60)
    left, right = bisect_right(s, start, first, end), bisect_right(s, exit_hour, first, end)
    # No other lifetime of a reused ticker can anchor this contract's grid.
    if left == first:
        raise InputFault("fundingRate", start)
    missing = []
    if right == end:
        last = s[end - 1]
        interval = tape.funding[last][0]
        next_due = last + interval
        if not terminal or contract.end_minute != exit_minute or interval not in {1, 2, 4, 8} or last % interval:
            raise InputFault("fundingRate", min(exit_hour, next_due))
        missing.extend(range(max(next_due, (start // interval + 1) * interval), exit_hour + 1, interval))
    for j in range(left, min(right + 1, end)):
        a, b = s[j - 1], s[j]
        old, new = tape.funding[a][0], tape.funding[b][0]
        category, absent = funding_clock_gap(a, old, b, new)
        if category == "unlabelled_gap":
            if old not in {1, 2, 4, 8} or new not in {1, 2, 4, 8} or a % old or b % new:
                raise InputFault("fundingRate", max(start, a))
            first_open = max(start, a)
            possible = min((first_open // interval + 1) * interval for interval in (old, new))
            if possible < b and possible <= exit_hour:
                raise InputFault("fundingRate", possible)
        missing.extend(h for h in absent if start < h <= exit_hour)
    def mark_fault(h):
        error = InputFault("markPriceKlines", h)
        if input_fault is None:
            raise error
        input_fault(error)

    for h in s[left:right]:
        mark = tape.at("mark", h)
        if not isfinite(mark):
            mark_fault(h)
        if not validate_only:
            yield mark * tape.funding[h][1], False
    penalty = (max(p["missing_funding_floor_pct"] / 100, tape.funding_peak(contract))
               if missing and not validate_only else None)
    for h in missing:
        mark = tape.at("mark", h)
        if not isfinite(mark):
            mark_fault(h)
        if not validate_only:
            yield -mark * penalty, True


def evaluate(tape, signal, p, contract, *, validate_only=False, continue_gaps=False, input_fault=None):
    h = signal.entry
    e, price, reason, shown = execution(tape, signal, p, contract, continue_gaps=continue_gaps)
    funding = tuple(settled(tape, h, e, p, contract, terminal=reason in {"terminal_close", "gap_terminal_close"},
                            validate_only=validate_only, input_fault=input_fault))
    if validate_only:
        return None
    start = tape.at("open", h)
    return Trade(year(signal.sample_hour), 1 - price / start, sum(v for v, _ in funding) / start,
                 1 + price / start, reason, shown / start if shown is not None else None, e,
                 sum(missing for _, missing in funding), -sum(v for v, missing in funding if missing) / start)


def last_close_version(trade):
    ratio = trade.favorable_terminal_price
    if ratio is None:
        return trade
    return replace(trade, price=1 - ratio, turnover=1 + ratio)


def pump_triggers(tape, symbol, p):
    for h in range(max(tape.start + 3, p["start"]), min(tape.end, p["last_event_minute"] // 60 + 1)):
        ref = tape.at("close", h - 3)
        if not isfinite(ref):
            continue
        a, b = tape.at("high", h - 2), tape.at("high", h - 1)
        if isfinite(a) and isfinite(b) and max(a, b) >= ref * (1 + p["pump_min_pct"] / 100):
            yield h, symbol


def ordinary(tapes, contracts, notice_index, p, counts=None, *, validate_only=False, absent=None, domains=None,
             source_counts=None, gap_comparison=None, input_fault=None):
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
            trade = evaluate(tape, signal, p, contract, validate_only=validate_only,
                             input_fault=None if input_fault is None else lambda error: input_fault(symbol, error))
            counts["traded"] += 1
            if source_counts is not None:
                source = "supplement_only_symbols" if domains is not None and symbol in domains else "store_symbols"
                source_counts[source] += 1
            if not validate_only:
                counts[trade.exit_reason] += 1
                if trade.gap_close and gap_comparison is not None:
                    gap_comparison(trade, tape, signal, contract)
                yield trade, k == len(notice_minutes) or notice_minutes[k] > trade.exit_minute
        except NoFill:
            counts["no_fill"] += 1
        except Canceled:
            counts["canceled_before_entry"] += 1
        except InputFault as error:
            if input_fault is not None:
                input_fault(symbol, error)
                continue
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
               missing_funding_trades=sum(t.missing_funding_settlements > 0 for t in trades),
               missing_funding_settlements=sum(t.missing_funding_settlements for t in trades),
               missing_funding_debit_sum_entry_notional=sum(t.missing_funding_debit for t in trades),
               terminal_closes=sum(t.terminal_close for t in trades),
               missing_hold_bar_closes=sum(t.gap_close for t in trades),
               deferred_timed_exits=sum(t.exit_reason == "deferred_time" for t in trades))
    if split:
        buckets = defaultdict(list)
        for t in trades:
            buckets[t.year].append(t)
        row["by_year"] = {y: summary(ts, bps, split=False) for y, ts in sorted(buckets.items())}
    return row
