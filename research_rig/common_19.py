"""Pure hourly Monday Asia calculations. No file access."""
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from statistics import mean, stdev
from zoneinfo import ZoneInfo

HOUR = 3600
DAY = 24
WEEK = 7 * DAY
NY = ZoneInfo("America/New_York")
UTC = timezone.utc
SYMBOLS = ("BTCUSDT", "ETHUSDT")
MARKS = ("sharpe", "full_years", "post_cme", "placebo", "breadth")


class Incomplete(ValueError):
    pass


class NonpositiveEquity(Exception):
    pass


@dataclass
class Tape:
    opens: dict
    closes: dict
    marks: dict
    rates: dict


def utc(hour):
    return datetime.fromtimestamp(hour * HOUR, UTC)


def hour(stamp):
    d = datetime.fromisoformat(stamp)
    if d.tzinfo is None:
        d = d.replace(tzinfo=UTC)
    n = d.timestamp()
    if n % HOUR:
        raise Incomplete("expected an hourly boundary")
    return int(n // HOUR)


def policy(raw):
    required = {"first_date", "last_date", "cme_cut", "sunday_hour_ny", "hold_hours",
                "funding_hours", "funding_jitter_seconds", "judged_bps", "shown_bps",
                "min_sharpe", "min_positive_years", "min_trade_pct", "placebo_percentile", "annual_days",
                "calibration_seed", "calibration_seeds", "calibration_edges_bps",
                "calibration_hourly_common_sigma", "calibration_hourly_idio_sigma",
                "calibration_funding_bps"}
    if set(raw) != required:
        raise Incomplete("unexpected policy keys")
    p = dict(raw)
    p.update(start=hour(p["first_date"]), end=hour(p["last_date"]) + DAY,
             cut=hour(p["cme_cut"]))
    if not (p["start"] < p["cut"] < p["end"] and
            all(type(p[k]) is int for k in ("sunday_hour_ny", "hold_hours", "funding_hours",
                                            "funding_jitter_seconds", "min_positive_years", "min_trade_pct",
                                            "annual_days", "calibration_seed", "calibration_seeds"))
            and 0 <= p["sunday_hour_ny"] < DAY and 0 < p["hold_hours"] < WEEK - 1
            and 0 < p["funding_hours"] <= DAY and DAY % p["funding_hours"] == 0
            and 0 <= p["funding_jitter_seconds"] < HOUR / 2 and p["min_positive_years"] > 0
            and p["annual_days"] > 0 and math.isfinite(p["min_sharpe"])
            and len(p["shown_bps"]) == 2 and
            0 <= p["shown_bps"][0] < p["judged_bps"] < p["shown_bps"][1] < 10000
            and 0 < p["min_trade_pct"] <= 100 and 0 < p["placebo_percentile"] < 100
            and p["calibration_seeds"] > 0 and p["calibration_seed"] >= 0
            and bool(p["calibration_edges_bps"]) and
            all(math.isfinite(x) and 0 <= x < 10000 for x in p["calibration_edges_bps"])
            and len(p["calibration_hourly_idio_sigma"]) == len(SYMBOLS)
            and all(math.isfinite(s) and s > 0 for s in
                    [p["calibration_hourly_common_sigma"], *p["calibration_hourly_idio_sigma"]])
            and math.isfinite(p["calibration_funding_bps"])):
        raise Incomplete("invalid replay policy")
    return p


def starts(p, shift):
    """Local hours modulo the New York civil week, Sunday indexed at zero."""
    weekday, start_hour = divmod((p["sunday_hour_ny"] + shift) % WEEK, DAY)
    first = utc(p["start"]).astimezone(NY).date()
    sunday = first - timedelta(days=(first.weekday() + 1) % 7)
    wall = datetime.combine(sunday + timedelta(days=weekday),
                            datetime.min.time()).replace(hour=start_hour)
    last = utc(p["end"]).astimezone(NY).date()
    out = []
    while wall.date() <= last:
        dt = wall.replace(tzinfo=NY, fold=0)
        as_utc = dt.astimezone(UTC)
        h = int(as_utc.timestamp() // HOUR)
        # Check round trip to reject a nonexistent local clock reading.
        if (as_utc.astimezone(NY).replace(tzinfo=None) == wall and
                p["start"] <= h - p["hold_hours"] - 1 and h + p["hold_hours"] < p["end"]):
            out.append(h)
        wall += timedelta(days=7)
    return out


def direction(tape, h, p, variant):
    if variant == "long":
        return 1
    value = tape.closes[h - 1]
    prior = tape.opens[h - 1] if variant == "one_candle" else tape.closes[h - p["hold_hours"] - 1]
    return int(value > prior) - int(value < prior)


def sharpe(returns, annual_days):
    if len(returns) < 2:
        return None
    std = stdev(returns)
    return mean(returns) / std * math.sqrt(annual_days) if std else None


def replay(tapes, p, entries, bps, variant="momentum", *, sharpe_only=False):
    fee = bps / 10000
    hold = p["hold_hours"]
    capital = 1.
    high = 1.
    fall = price_pnl = funding_pnl = fees = exposure = 0.
    ticks, values = [p["start"]], [capital]
    traded = post_traded = 0
    for entry in entries:
        exit_hour = entry + hold
        changes = defaultdict(float)
        active = False
        for tape in tapes:
            side = direction(tape, entry, p, variant)
            if not side:
                continue
            active = True
            prev = tape.opens[entry]
            stake = capital / (len(tapes) * (1 + fee))
            qty = side * stake / prev
            exposure = max(exposure, stake * len(tapes) / capital)
            charge = abs(qty) * prev * fee
            fees += charge
            changes[entry] -= charge
            for h in range(entry + 1, exit_hour + 1):
                px = tape.opens[h]
                move = qty * (px - prev)
                price_pnl += move
                changes[h] += move
                if h % p["funding_hours"] == 0:
                    flow = -qty * tape.marks[h] * tape.rates[h]
                    funding_pnl += flow
                    changes[h] += flow
                prev = px
            charge = abs(qty) * prev * fee
            fees += charge
            changes[exit_hour] -= charge
        if active:
            traded += 1
            post_traded += entry >= p["cut"]
        for h in sorted(changes):
            capital += changes[h]
            if not math.isfinite(capital):
                raise Incomplete("invalid marked account equity")
            if capital <= 0:
                raise NonpositiveEquity
            high = max(high, capital)
            fall = max(fall, 1 - capital / high)
            ticks.append(h)
            values.append(capital)

    def at(h):
        return values[bisect_right(ticks, h) - 1]

    def segment(left, right):
        boundaries = [left, *range((left // DAY + 1) * DAY, right, DAY), right]
        path = [at(h) for h in boundaries]
        returns = [b / a - 1 for a, b in zip(path, path[1:])]
        return dict(net=path[-1] / path[0] - 1, sharpe=sharpe(returns, p["annual_days"]),
                    return_bins=len(returns))

    start, end = p["start"], p["end"]
    if sharpe_only:
        return {"whole": segment(start, end)}
    years, full = {}, []
    for y in range(utc(start).year, utc(end - 1).year + 1):
        a, b = hour(f"{y}-01-01"), hour(f"{y + 1}-01-01")
        years[str(y)] = at(min(end, b)) / at(max(start, a)) - 1
        if start <= a and b <= end:
            full.append(str(y))
    return dict(whole=segment(start, end), before_cme=segment(start, p["cut"]),
                after_cme=segment(p["cut"], end), years=years, full_years=full,
                largest_fall=fall, scheduled_weeks=len(entries), traded_weeks=traded,
                post_cme_weeks=sum(h >= p["cut"] for h in entries), post_cme_traded_weeks=post_traded,
                price_pnl=price_pnl, funding_pnl=funding_pnl, fees=fees,
                max_initial_gross_bound=exposure)


def placebo_threshold(values, failed, percent):
    """Use minus infinity internally for failed accounts, never put it in JSON."""
    finite = sorted(values)
    n = len(finite) + failed
    if not n:
        return None, "undefined"
    frac = (n - 1) * percent / 100
    left, right = math.floor(frac), math.ceil(frac)
    if left < failed:
        return None, "below_all_finite"
    lo, hi = finite[left - failed], finite[right - failed]
    return lo + (hi - lo) * (frac - left), "finite"


def breadth(book, min_pct):
    return all(book[scheduled] > 0 and 100 * book[traded] >= min_pct * book[scheduled]
               for scheduled, traded in (("scheduled_weeks", "traded_weeks"),
                                          ("post_cme_weeks", "post_cme_traded_weeks")))


def measure(tapes, p, check=lambda: None):
    selected = starts(p, 0)
    bps = p["judged_bps"]
    books = {**{s: [tapes[s]] for s in SYMBOLS}, "pair": [tapes[s] for s in SYMBOLS]}

    def book(tapes, entries, cost, variant="momentum", *, sharpe_only=False):
        try:
            return replay(tapes, p, entries, cost, variant, sharpe_only=sharpe_only)
        except NonpositiveEquity:
            return {"refusal": "NONPOSITIVE_EQUITY"}

    def grid(cost, variant="momentum"):
        return {k: book(v, selected, cost, variant) for k, v in books.items()}

    base = grid(bps)
    placebo = {}
    failed = []
    for shift in range(1, WEEK):
        check()
        b = book(books["pair"], starts(p, shift), bps, sharpe_only=True)
        key = str(shift)
        if "refusal" in b:
            failed.append(key)
        placebo[key] = b.get("whole", {}).get("sharpe")
    defined = [v for v in placebo.values() if v is not None]
    undefined = len(placebo) - len(defined) - len(failed)
    threshold, rank = (None, "undefined") if undefined else placebo_threshold(
        defined, len(failed), p["placebo_percentile"])
    pair = base["pair"]
    marks = dict.fromkeys(MARKS, False)
    if "refusal" not in pair:
        s = pair["whole"]["sharpe"]
        marks.update(sharpe=s is not None and s >= p["min_sharpe"],
                     full_years=sum(pair["years"][y] > 0 for y in pair["full_years"]) >= p["min_positive_years"],
                     post_cme=pair["after_cme"]["net"] > 0,
                     placebo=s is not None and (rank == "below_all_finite" or
                                                 (threshold is not None and s > threshold)),
                     breadth=breadth(pair, p["min_trade_pct"]))
    return dict(main=base, marks=marks, passes=all(marks.values()),
                shown_costs={str(c): grid(c) for c in p["shown_bps"]},
                shown_signals={key: grid(bps, key) for key in ("one_candle", "long")},
                placebo=dict(sharpes=placebo, percentile=threshold, percentile_status=rank,
                             failed=failed, undefined=undefined, defined=len(defined)))
