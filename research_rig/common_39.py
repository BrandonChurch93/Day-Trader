"""Calendar, raw input checks and pure numerical machinery for Plan 39."""
from bisect import bisect_left
from datetime import date, datetime, timedelta
from math import isfinite, sqrt
from statistics import fmean, stdev, variance
from zoneinfo import ZoneInfo

FIRST = date(2016, 1, 4)
LAST = date(2026, 10, 30)
POST = date(2020, 1, 1)
YEARS = tuple(range(2016, 2027))
SYMBOLS = ("IWM", "SPY")
COSTS = (2, 5, 10)
MIN_EVENTS, MIN_T, DROP_BEST, MIN_YEARS = 80, 2.0, 3, 7
NY = ZoneInfo("America/New_York")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P39_" + code)


def exact_day(x):
    d = date.fromisoformat(x)
    need(d.isoformat() == x, "DATE")
    return d


def calendar(raw):
    need(set(raw) == {"calendar", "version", "holiday_order", "closures_by_year",
                      "special_closures", "early_closes_by_year"}
         and raw["calendar"] == "XNYS" and raw["version"] == "official-nyse-2016-2026-v1",
         "CALENDAR")
    names = raw["holiday_order"]
    need(type(names) is list and len(set(names)) == len(names) == 10, "CALENDAR")
    closures, early = {}, set()
    for key in ("closures_by_year", "early_closes_by_year"):
        need(set(raw[key]) == {str(y) for y in YEARS}, "CALENDAR")
    for y in YEARS:
        dates = raw["closures_by_year"][str(y)]
        need(type(dates) is list and len(dates) == len(names), "CALENDAR")
        for md, label in zip(dates, names, strict=True):
            if md is not None:
                d = exact_day(f"{y}-{md}")
                need(d not in closures, "CALENDAR")
                closures[d] = label
        for md in raw["early_closes_by_year"][str(y)]:
            d = exact_day(f"{y}-{md}")
            need(d not in early, "CALENDAR")
            early.add(d)
    special = {exact_day(d): v for d, v in raw["special_closures"].items()}
    need(set(special) == {date(2018, 12, 5), date(2025, 1, 9)} and not (special.keys() & closures.keys()),
         "CALENDAR")
    closures.update(special)
    need(not (early & closures.keys()) and all(d.weekday() < 5 for d in early | closures.keys()), "CALENDAR")
    # Metadata-only 2015 carry-in for the documented unscorable 2016 New Year's event.
    d0 = date(2015, 12, 30)
    expected_sessions = tuple(d0 + timedelta(days=i) for i in range((LAST - d0).days + 1)
                              if (d0 + timedelta(days=i)).weekday() < 5
                              and d0 + timedelta(days=i) not in closures)
    days = tuple(d for d in expected_sessions if d >= FIRST)
    events = {}
    outside_scope = []
    for d, label in sorted(closures.items()):
        if d > LAST:
            continue
        ix = bisect_left(expected_sessions, d)
        need(ix >= 2, "CALENDAR")
        buy, sell = expected_sessions[ix - 2:ix]
        if sell < FIRST:
            outside_scope.append((d, buy, sell))
            continue
        need(buy >= FIRST and sell not in events, "CALENDAR")
        events[sell] = (buy, d, label, sell in early)
    need(outside_scope == [(date(2016, 1, 1), date(2015, 12, 30), date(2015, 12, 31))]
         and len(days) == 2723 and days[0] == FIRST and days[-1] == LAST
         and len(events) == 102 and sum(d >= POST for d in events) == 65
         and sum(v[3] for v in events.values()) == 11, "CALENDAR")
    return days, events


def bar_tape(rows, days):
    need(type(rows) is list and len(rows) == len(days), "BARS")
    closes, last, same = {}, None, 0
    for row, d in zip(rows, days, strict=True):
        need(type(row) is dict and set(row) == {"t", "o", "h", "l", "c", "v"}, "BAR_FIELDS")
        need(type(row["t"]) is str, "BAR_TIME")
        try:
            ts = datetime.fromisoformat(row["t"].replace("Z", "+00:00"))
        except ValueError:
            raise Refused("P39_BAR_TIME") from None
        need(ts.utcoffset() is not None, "BAR_TIME")
        local = ts.astimezone(NY)
        need(local.date() == d and (local.hour, local.minute, local.second, local.microsecond) == (0, 0, 0, 0),
             "BAR_TIME")
        px = tuple(row[k] for k in ("o", "h", "l", "c"))
        need(all(type(x) in (int, float) and isfinite(x) and x > 0 for x in px)
             and type(row["v"]) is int and row["v"] > 0, "BAR_VALUES")
        o, h, low, c = px
        need(low <= min(o, c) <= max(o, c) <= h, "BAR_VALUES")
        same = same + 1 if px == last else 1
        need(same < 5, "BAR_FLAT_RUN")
        last, closes[d] = px, c
    return closes


def payouts(raw, days):
    need(set(raw) == {"schema", "coverage_start", "coverage_end", "funds"} and type(raw["schema"]) is int
         and raw["schema"] == 1 and raw["coverage_start"] == FIRST.isoformat()
         and raw["coverage_end"] == LAST.isoformat() and set(raw["funds"]) == set(SYMBOLS), "ACTIONS")
    sessions, cash = set(days), {}
    for symbol in SYMBOLS:
        fund = raw["funds"][symbol]
        need(set(fund) == {"source", "splits", "cash"} and type(fund["source"]) is str
             and fund["source"].startswith("https://") and fund["splits"] == []
             and type(fund["cash"]) is list and fund["cash"], "ACTION_COVERAGE")
        rates, ids = {}, set()
        for row in fund["cash"]:
            need(type(row) is dict and set(row) == {"id", "ex_date", "amount"}
                 and type(row["id"]) is str and row["id"].strip() and row["id"] not in ids, "ACTION_ROW")
            ids.add(row["id"])
            d, amount = exact_day(row["ex_date"]), row["amount"]
            need(d in sessions and type(amount) in (int, float) and isfinite(amount) and amount > 0, "ACTION_ROW")
            rates[d] = rates.get(d, 0) + amount
            need(isfinite(rates[d]), "ACTION_ROW")
        cash[symbol] = rates
    return cash


def one_return(buy, sell, cash, bps):
    f = bps / 10_000
    return (sell * (1 - f) + cash) / (buy * (1 + f)) - 1


def sample_t(values):
    se = stdev(values) / sqrt(len(values)) if len(values) >= 2 else 0
    return fmean(values) / se if se else None


def summary(values):
    return {"n": len(values), "mean": fmean(values) if values else None, "t": sample_t(values)}


def comparison(inside, outside):
    gap = fmean(inside) - fmean(outside)
    se = sqrt(variance(inside) / len(inside) + variance(outside) / len(outside))
    return {"inside": summary(inside), "outside": summary(outside), "difference": gap,
            "welch_t": gap / se if se else None}


def evaluate(days, events, tapes, actions):
    def event_returns(symbol, cost):
        tape, cash = tapes[symbol], actions[symbol]
        return {sell: one_return(tape[buy], tape[sell], cash.get(sell, 0), cost)
                for sell, (buy, _, _, _) in events.items()}
    net = event_returns("IWM", COSTS[0])
    values = list(net.values())
    primary = summary(values)
    trimmed = fmean(sorted(values)[:-DROP_BEST])
    post = summary([v for d, v in net.items() if d >= POST])
    years = {y: summary([v for d, v in net.items() if d.year == y]) for y in YEARS}
    positive_years = sum(s["mean"] is not None and s["mean"] > 0 for s in years.values())
    gross = {s: one_return(tapes["IWM"][b], tapes["IWM"][s], actions["IWM"].get(s, 0), 0)
             for b, s in zip(days[:-1], days[1:], strict=True)}
    cmp = comparison([v for d, v in gross.items() if d in events],
                     [v for d, v in gross.items() if d not in events])
    gates = {
        "count": len(values) >= MIN_EVENTS,
        "net_mean": primary["mean"] > 0,
        "net_t": primary["t"] is not None and primary["t"] >= MIN_T,
        "drop_best_three": trimmed > 0,
        "post_2019_net_mean": post["mean"] is not None and post["mean"] > 0,
        "gross_difference_and_welch_t": cmp["difference"] > 0 and cmp["welch_t"] is not None
        and cmp["welch_t"] >= MIN_T,
        "positive_year_breadth": positive_years >= MIN_YEARS,
    }
    return {
        "calendar_counts": {"events": len(events), "early_close_exits": sum(v[3] for v in events.values()),
                            "other_sessions": cmp["outside"]["n"]},
        "IWM_judged_2_bps_per_side": primary | {"trimmed_mean": trimmed, "post_2019": post,
                                              "2016_through_2019": summary([v for d, v in net.items() if d < POST]),
                                              "years": years, "positive_years": positive_years,
                                              "daily_comparison_gross": cmp, "gates": gates, "passes": all(gates.values())},
        "IWM_cost_sensitivity_shown_only": {bps: summary(list(event_returns("IWM", bps).values()))
                                            for bps in COSTS[1:]},
        "SPY_same_events_shown_only_2_bps_per_side": summary(list(event_returns("SPY", COSTS[0]).values())),
        "limits": ["SIP daily close is a proxy for an executable close; per-side costs are fixed assumptions.",
                   "The study's equal-weight CRSP index is not cap-weighted IWM.",
                   "Conventional t statistics are descriptive; no serial-dependence correction. No cash yield or tax."],
    }
