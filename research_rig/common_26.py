"""Earlier Treasury replay schedule, input checks, and Replay 25 engine wiring."""
from datetime import date
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from itertools import groupby
import re

import common_25 as engine

SYMBOLS = engine.SYMBOLS
FIRST = date(2002, 7, 30)
LAST = date(2015, 12, 31)
POST = date(2009, 1, 1)
OVERLAP_LAST = date(2026, 10, 31)
EXPORT_LAST = date(2026, 10, 30)
PULL_A_LAST = date(2020, 12, 31)
PULL_B_FIRST = date(2020, 12, 1)
YEARS = range(FIRST.year, LAST.year + 1)
ACTIONS_SHA = "6f1a5cc1117cdd59e5f9a19d881fb4debe059b72eb8241720609e49525ac67b2"
SIP_MANIFEST_SHA = "43f92b5249c8a2aa8778139f928cf643814e47b778d5892a903227830777aa9a"
SIP_DRAFT_SHA = "c4c0108467c0acfcd95781b9a73379b4a1022a43ca8229f8654a2a445e777bd8"


class Refused(Exception):
    pass


def need(test, code):
    if not test:
        raise Refused("P26_" + code)


def date_string(value):
    need(type(value) is str, "SESSION")
    day = date.fromisoformat(value)
    need(day.isoformat() == value, "SESSION")
    return day


def calendar(payload):
    need(set(payload) == {"calendar", "version", "sessions"} and payload["calendar"] == "XNYS"
         and payload["version"] == "4.13.3", "CALENDAR")
    days = tuple(date_string(x) for x in payload["sessions"])
    need(len(days) == 3381 and days == tuple(sorted(set(days))) and days[0] == FIRST and days[-1] == LAST,
         "CALENDAR")
    by_month = month_groups(days)
    need(len(by_month) == 162 and len(by_month[0]) == 2 and all(len(m) >= 6 for m in by_month[1:]),
         "CALENDAR")
    return days


def month_groups(days):
    return tuple(tuple(g) for _, g in groupby(days, key=lambda d: (d.year, d.month)))


def windows(days, width):
    return [(m[-1-width], m[-1], m[-width:]) for m in month_groups(days)[1:]]


def next_three(days):
    groups = month_groups(days)[1:]
    return [(a[-1], b[2], b[:3]) for a, b in zip(groups, groups[1:])]


def checked_number(value):
    need(type(value) in (str, int, float, Decimal), "BAR_NUMBER")
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise Refused("P26_BAR_NUMBER") from None
    need(number.is_finite() and number > 0 and 0 < float(number) < float("inf")
         and len(number.as_tuple().digits) <= 128 and abs(number.as_tuple().exponent) <= 512, "BAR_NUMBER")
    return number


def vendor_bars(raw, days):
    """Exact normalized raw OHLCV schema. No alternate close accepted."""
    need(type(raw) is list and len(raw) == len(days), "BAR_CLOCK")
    closes = {}
    rows = []
    for expected, row in zip(days, raw, strict=True):
        need(type(row) is dict and set(row) == {"date", "open", "high", "low", "close", "volume"},
             "BAR_SCHEMA")
        need(type(row["close"]) is str and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", row["close"]),
             "CLOSE_TEXT")
        day = date_string(row["date"])
        need(day == expected, "BAR_CLOCK")
        o, h, low, c, v = [checked_number(row[k]) for k in ("open", "high", "low", "close", "volume")]
        rows.append(dict(o=float(o), h=float(h), l=float(low), c=float(c), v=float(v)))
        closes[day] = c
    try:
        tape = engine.price_tape(rows, days)
    except engine.Refused:
        raise Refused("P26_BAR_QUALITY") from None
    return tape, closes


def cash_actions(raw, days):
    need(set(raw) == {"schema", "coverage_start", "coverage_end", "funds"} and type(raw["schema"]) is int
         and raw["schema"] == 1 and date_string(raw["coverage_start"]) == FIRST
         and date_string(raw["coverage_end"]) == LAST and set(raw["funds"]) == set(SYMBOLS),
         "ACTIONS_COVERAGE")
    try:
        sessions, out = set(days), {}
        for symbol in SYMBOLS:
            fund = raw["funds"][symbol]
            need(set(fund) == {"source", "splits", "cash"} and type(fund["source"]) is str
                 and fund["source"].startswith("https://www.ishares.com/") and fund["splits"] == []
                 and type(fund["cash"]) is list and len(fund["cash"]) == 161, "ACTIONS_COVERAGE")
            used_dates, used_ids = set(), set()
            for row in fund["cash"]:
                need(type(row) is dict and set(row) == {"id", "ex_date", "amount"} and type(row["id"]) is str
                     and row["id"] and row["id"] not in used_ids, "ACTIONS_SCHEMA")
                day = date_string(row["ex_date"])
                need(day in sessions and day not in used_dates, "ACTIONS_CLOCK")
                used_ids.add(row["id"])
                used_dates.add(day)
            out[symbol] = engine.distributions(fund["cash"])
        return out
    except engine.Refused:
        raise Refused("P26_ACTIONS_AMOUNT") from None


def compare_closes(vendor, sip):
    need(tuple(vendor) == tuple(sip), "OVERLAP_CLOCK")
    n = len(sip)
    need(n > 0, "OVERLAP_CLOCK")
    # Decimal subtraction uses a rounding context; rational subtraction cannot round to a cent.
    count = sum(abs(Fraction(vendor[d]) - Fraction(p)) <= Fraction(1, 100) for d, p in sip.items())
    need(1000 * count >= 995 * n, "OVERLAP_AGREEMENT")
    return count, n


def scored(days, bars, cash, include_shown):
    """Call only after lock. Use the Replay 25 fee, payout, and statistic functions."""
    spans = windows(days, 3)
    samples = engine.window_values(bars, cash, spans, engine.COSTS[0])
    values = [r for _, r in samples]
    annual = {str(y): engine.pack([r for d, r in samples if d.year == y]) for y in YEARS}
    leave = {str(y): engine.pack([r for d, r in samples if d.year != y]) for y in YEARS}
    later = engine.mean([r for d, r in samples if d >= POST])
    trimmed = engine.mean(sorted(values)[:-engine.TRIM])
    inside = {d for _, _, ds in spans for d in ds}
    daily = {y: ([], []) for y in YEARS}
    for prev, day in zip(days, days[1:]):
        # Replay 25 gross daily total return; date coverage is set by this plan.
        daily[day.year][0 if day in inside else 1].append((bars[day].c + cash.get(day, 0)) / bars[prev].c - 1)
    by_year = {str(y): engine.compare(*g) for y, g in daily.items()}
    gap = engine.compare(*([r for g in daily.values() for r in g[i]] for i in (0, 1)))
    stats = engine.pack(values)

    def positive(v):
        return v is not None and v > 0

    def passes_t(v):
        return v is not None and v >= engine.MIN_T

    share = sum(positive(x["mean_net"]) for x in annual.values()) / len(YEARS)
    daily_share = sum(positive(x["difference"]) for x in by_year.values()) / len(YEARS)
    stats.update(trimmed_mean=trimmed, later_half_mean=later, positive_year_share=share, leave_one_year_out=leave,
                 daily_comparison=gap, daily_comparison_by_year=by_year, positive_daily_year_share=daily_share)
    if not include_shown:
        return stats, {}
    gates = {
        "windows": stats["n"] >= engine.MIN_WINDOWS,
        "positive_mean": positive(stats["mean_net"]),
        "window_t": passes_t(stats["t"]),
        "trimmed_positive": positive(trimmed),
        "daily_difference_and_t": positive(gap["difference"]) and passes_t(gap["welch_t"]),
        "positive_year_share": share >= engine.YEAR_SHARE,
        "later_half_positive": positive(later),
        "every_leave_one_year_out_positive": all(positive(x["mean_net"]) for x in leave.values()),
        "positive_daily_year_share": daily_share >= engine.YEAR_SHARE,
    }
    stats.update(gates=gates, passes=all(gates.values()))

    def summary(span, bps=engine.COSTS[0]):
        return engine.pack([r for _, r in engine.window_values(bars, cash, span, bps)])

    shown = {
        "other_costs_same_window": {str(b): summary(spans, b) for b in engine.COSTS[1:]},
        "other_widths_at_2bps": {str(w): summary(windows(days, w)) for w in engine.WIDTHS if w != 3},
        "next_month_first_three_at_2bps": summary(next_three(days)),
        "by_year_at_2bps": annual,
        "cash_return": 0.0,
    }
    return stats, shown
