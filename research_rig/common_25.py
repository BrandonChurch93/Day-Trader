"""Replay 25 preregistered design and pure numerical machinery."""
from dataclasses import dataclass
from datetime import date, datetime
from itertools import groupby
from math import isfinite, sqrt
from statistics import fmean, stdev, variance
from zoneinfo import ZoneInfo

FIRST = date(2016, 1, 1)
LAST = date(2026, 10, 31)
BAR_FROM = date(2016, 1, 4)
ACTION_COVERAGE_FROM = date(2015, 12, 31)
DATA_END = date(2026, 11, 24)
POST = date(2020, 1, 1)
YEARS = tuple(range(FIRST.year, LAST.year + 1))
SYMBOLS = ("TLT", "IEF")
WIDTHS = (1, 2, 3, 4, 5)
COSTS = (2, 5, 10)
MIN_WINDOWS, MIN_T, TRIM, YEAR_SHARE = 100, 2.0, 3, 0.60
EXPECTED_MONTHS = 130
NY = ZoneInfo("America/New_York")


class Refused(Exception):
    pass


def need(condition, code):
    if not condition:
        raise Refused(code)


def session(value):
    # Alpaca daily bars use the New York session date, not a UTC resampling.
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    need(stamp.utcoffset() is not None, "P25_BAR_CLOCK")
    local = stamp.astimezone(NY)
    need((local.hour, local.minute, local.second, local.microsecond) == (0, 0, 0, 0), "P25_BAR_CLOCK")
    return local.date()


def check_calendar(raw):
    need(set(raw) == {"calendar", "version", "sessions"} and raw["calendar"] == "XNYS"
         and raw["version"] == "4.13.3", "P25_CALENDAR")
    days = tuple(date.fromisoformat(v) for v in raw["sessions"])
    need(len(days) == 2740 and days == tuple(sorted(set(days))) and days[0] == BAR_FROM and days[-1] == DATA_END,
         "P25_CALENDAR")
    m = months(days)
    need(len(m) == EXPECTED_MONTHS and all(len(rows) >= 6 for rows in m.values()), "P25_CALENDAR")
    need(len([d for d in days if d > LAST]) >= 3, "P25_CALENDAR")
    return days


def check_bar_clocks(rows, days):
    need(isinstance(rows, list), "P25_BAR_SCHEMA")
    actual = tuple(session(x["t"]) for x in rows)
    need(actual == days, "P25_BAR_CLOCK")
    vols = [x["v"] for x in rows]
    need(all(type(v) in (int, float) and isfinite(v) and v >= 0 for v in vols), "P25_BAR_VOLUME")
    return actual


def check_actions(raw, days):
    """Only metadata/date checks. Rates are validated silently in scorer, not fetcher."""
    need(set(raw) == {"schema", "coverage_start", "coverage_end", "funds"} and raw["schema"] == 1
         and date.fromisoformat(raw["coverage_start"]) <= ACTION_COVERAGE_FROM
         and date.fromisoformat(raw["coverage_end"]) >= DATA_END
         and set(raw["funds"]) == set(SYMBOLS), "P25_ACTION_COVERAGE")
    for fund in raw["funds"].values():
        need(set(fund) == {"source", "splits", "cash"} and isinstance(fund["source"], str)
             and fund["source"].startswith("https://") and fund["splits"] == []
             and isinstance(fund["cash"], list) and fund["cash"], "P25_ACTION_COVERAGE")
        keys = set()
        sessions = set(days)
        for row in fund["cash"]:
            need(set(row) == {"id", "ex_date", "amount"} and isinstance(row["id"], str)
                 and row["id"] and row["id"] not in keys
                 and date.fromisoformat(row["ex_date"]) in sessions, "P25_ACTION_CLOCK")
            keys.add(row["id"])


@dataclass(frozen=True)
class Bar:
    o: float
    h: float
    l: float
    c: float
    v: float


def price_tape(rows, days):
    bars = []
    prev = None
    run = 0
    previous_ohlc = None
    same_ohlc = 0
    for x in rows:
        px = [x[k] for k in ("o", "h", "l", "c")]
        need(all(type(v) in (int, float) and v > 0 and isfinite(v) for v in px), "P25_BAR_PRICE")
        o, h, l, c = px
        need(l <= min(o, c) <= max(o, c) <= h, "P25_BAR_PRICE")
        b = Bar(o, h, l, c, x["v"])
        flat = o == h == l == c and b.v == 0
        run = (run + 1 if run and c == prev else 1) if flat else 0
        need(run < 5, "P25_FLAT_RUN")
        same_ohlc = same_ohlc + 1 if px == previous_ohlc else 1
        need(same_ohlc < 5, "P25_FLAT_RUN")
        previous_ohlc = px
        prev = c
        bars.append(b)
    # No zero-volume proxy is admissible in either the window or comparator.
    need(all(b.v > 0 for b in bars), "P25_ZERO_VOLUME")
    return dict(zip(days, bars, strict=True))


def distributions(raw):
    cash = {}
    for row in raw:
        payout = row["amount"]
        need(type(payout) in (float, int) and isfinite(payout) and payout > 0, "P25_ACTION_AMOUNT")
        d = date.fromisoformat(row["ex_date"])
        cash[d] = cash.get(d, 0) + payout
        need(isfinite(cash[d]), "P25_ACTION_AMOUNT")
    return cash


def months(days):
    return {k: tuple(group) for k, group in groupby(
        (d for d in days if FIRST <= d <= LAST), key=lambda d: (d.year, d.month))}


def windows(days, width):
    return [(rows[-1-width], rows[-1], rows[-width:]) for rows in months(days).values()]


def next_three(days):
    ix = {d: i for i, d in enumerate(days)}
    spans = []
    for _, end, _ in windows(days, 3):
        following = days[ix[end] + 1:ix[end] + 4]
        need(len(following) == 3 and all((d.year, d.month) != (end.year, end.month)
                                       for d in following), "P25_NEXT_WINDOW")
        spans.append((end, following[-1], following))
    return spans


def window_values(bars, dividends, spans, bps):
    f = bps / 10_000
    return [(sell, (bars[sell].c * (1 - f) + sum(dividends.get(d, 0) for d in earned_days))
             / (bars[buy].c * (1 + f)) - 1) for buy, sell, earned_days in spans]


def mean(values):
    return fmean(values) if values else None


def one_sample(values):
    sd = stdev(values) if len(values) > 1 else 0
    return fmean(values) * sqrt(len(values)) / sd if sd > 0 else None


def compare(inside, outside):
    a, b = mean(inside), mean(outside)
    gap = a-b if a is not None and b is not None else None
    se2 = (variance(inside) / len(inside) + variance(outside) / len(outside)
           if len(inside) >= 2 and len(outside) >= 2 else 0)
    return {"difference": gap, "welch_t": gap / sqrt(se2) if se2 > 0 else None,
            "inside_n": len(inside), "outside_n": len(outside), "inside_mean": a, "outside_mean": b}


def daily_split(days, bars, dividends, spans):
    inside_days = {d for _, _, ds in spans for d in ds}
    a, b = [], []
    by_year = {y: ([], []) for y in YEARS}
    for prev, day in zip(days, days[1:]):
        if FIRST <= day <= LAST:
            daily = (bars[day].c + dividends.get(day, 0)) / bars[prev].c - 1
            inside = day in inside_days
            (a if inside else b).append(daily)
            by_year[day.year][0 if inside else 1].append(daily)
    return compare(a, b), {str(y): compare(*ds) for y, ds in by_year.items()}


def pack(values):
    return {"n": len(values), "mean_net": mean(values), "t": one_sample(values)}


def evaluate(days, bars, dividends):
    spans = windows(days, 3)
    judged = window_values(bars, dividends, spans, COSTS[0])
    values = [v for _, v in judged]
    post = [v for d, v in judged if d >= POST]
    by_year = {str(y): pack([v for d, v in judged if d.year == y]) for y in YEARS}
    share = sum(row["mean_net"] is not None and row["mean_net"] > 0 for row in by_year.values()) / len(YEARS)
    leave_out = {str(y): pack([v for d, v in judged if d.year != y]) for y in YEARS}
    gap, daily_years = daily_split(days, bars, dividends, spans)
    def gt(x): return x is not None and x > 0
    daily_share = sum(gt(row["difference"]) for row in daily_years.values()) / len(YEARS)
    stats = pack(values) | {"trimmed_mean": mean(sorted(values)[:-TRIM]), "post_2019_mean": mean(post),
                            "positive_year_share": share,
                            "daily_comparison": gap, "leave_one_year_out": leave_out,
                            "daily_comparison_by_year": daily_years, "positive_daily_year_share": daily_share}
    def meets_t(x): return x is not None and x >= MIN_T
    gap = stats["daily_comparison"]
    gates = {
        "windows": stats["n"] >= MIN_WINDOWS, "positive_mean": gt(stats["mean_net"]),
        "window_t": meets_t(stats["t"]), "trimmed_positive": gt(stats["trimmed_mean"]),
        "daily_difference_and_t": gt(gap["difference"]) and meets_t(gap["welch_t"]),
        "positive_year_share": share >= YEAR_SHARE, "post_2019_positive": gt(stats["post_2019_mean"]),
        "every_leave_one_year_out_positive": all(gt(row["mean_net"]) for row in leave_out.values()),
        "positive_daily_year_share": daily_share >= YEAR_SHARE,
    }
    summary = lambda w, bps: pack([v for _, v in window_values(bars, dividends, w, bps)])
    return {
        "judged": stats | {"gates": gates, "passes": all(gates.values())},
        "shown": {"other_costs_same_window": {str(c): summary(spans, c) for c in COSTS[1:]},
                  "other_widths_at_2bps": {str(w): summary(windows(days, w), COSTS[0])
                                           for w in WIDTHS if w != 3},
                  "by_year_at_2bps": by_year,
                  "next_month_first_three_at_2bps": summary(next_three(days), COSTS[0]),
                  "calendar_2022_at_2bps": by_year["2022"], "cash_return": 0.0},
    }
