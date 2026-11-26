"""Plan 41 calendar, validation, and post-lock numerical engine."""
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
from math import sqrt
import re
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")
SYMBOLS = ("SPY", "TLT")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P41_" + code)


def day(value):
    need(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "DATE")
    return date.fromisoformat(value)


def calendar(raw, cfg):
    need(type(raw) is dict and set(raw) == {"calendar", "version", "sessions"}
         and raw["calendar"] == "XNYS" and raw["version"] == "4.13.3"
         and type(raw["sessions"]) is list, "CALENDAR")
    all_sessions = tuple(map(day, raw["sessions"]))
    first, last = day(cfg["first"]), day(cfg["last"])
    need(all_sessions == tuple(sorted(set(all_sessions))) and all_sessions[0] == first
         and last in all_sessions and all(d.weekday() < 5 for d in all_sessions), "CALENDAR")
    days = tuple(d for d in all_sessions if first <= d <= last)
    need(len(days) == cfg["sessions"] and days[-1] == last, "CALENDAR")
    by_month = defaultdict(list)
    for d in days:
        by_month[(d.year, d.month)].append(d)
    need(len(by_month) == cfg["months"] and len({d.year for d in days}) == cfg["years"], "CALENDAR")
    windows, anchor = [], first
    signal_offset, entry_offset = cfg["signal_offset"], cfg["entry_offset"]
    month_rows = list(by_month.values())
    for i, dates in enumerate(month_rows):
        need(len(dates) >= signal_offset > entry_offset > 1, "CALENDAR")
        signal, entry, exit_ = dates[-signal_offset], dates[-entry_offset], dates[-1]
        next_first = month_rows[i + 1][0] if i + 1 < len(month_rows) else None
        need(anchor < signal < entry < exit_, "CALENDAR")
        windows.append((anchor, signal, entry, exit_, next_first))
        anchor = exit_
    return days, tuple(windows)


def positive_number(value):
    # Bound representations before Fraction conversion, not as a data filter.
    if type(value) is int:
        return 0 < value <= 10**30
    return (type(value) is Decimal and value.is_finite() and value > 0 and
            len(value.as_tuple().digits) <= 32 and -30 <= value.adjusted() <= 30)


def bar_tape(raw, days):
    need(type(raw) is list and len(raw) == len(days), "BARS")
    tape, last, repeated = {}, None, 0
    for row, d in zip(raw, days, strict=True):
        need(type(row) is dict and set(row) == {"t", "o", "h", "l", "c", "v"}, "BAR_FIELDS")
        t = row["t"]
        need(type(t) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", t), "BAR_TIME")
        local = datetime.fromisoformat(t).astimezone(NY)
        need(local.date() == d and (local.hour, local.minute, local.second) == (0, 0, 0), "BAR_TIME")
        px = tuple(row[k] for k in ("o", "h", "l", "c"))
        need(all(map(positive_number, px))
             and type(row["v"]) is int and row["v"] > 0, "BAR_VALUES")
        o, h, low, c = px
        need(low <= min(o, c) <= max(o, c) <= h, "BAR_VALUES")
        repeated = repeated + 1 if px == last else 1
        need(repeated < 5, "BAR_FLAT_RUN")
        tape[d], last = c, px
    return tape


def cash_actions(raw, days):
    need(type(raw) is dict and set(raw) == {"schema", "coverage_start", "coverage_end", "funds"}
         and type(raw["schema"]) is int and raw["schema"] == 1
         and day(raw["coverage_start"]) == days[0] and day(raw["coverage_end"]) == days[-1]
         and type(raw["funds"]) is dict and set(raw["funds"]) == set(SYMBOLS), "ACTIONS")
    sessions, parsed = set(days), {}
    for symbol in SYMBOLS:
        fund = raw["funds"][symbol]
        need(type(fund) is dict and set(fund) == {"source", "splits", "cash"}
             and type(fund["source"]) is str and re.fullmatch(r"https://[^\s]+", fund["source"])
             and fund["splits"] == [] and type(fund["cash"]) is list and fund["cash"], "ACTION_COVERAGE")
        seen, rows, previous = set(), [], None
        for row in fund["cash"]:
            need(type(row) is dict and set(row) == {"id", "ex_date", "amount"}, "ACTION_FIELDS")
            identifier, d, amount = row["id"], day(row["ex_date"]), row["amount"]
            need(type(identifier) is str and identifier == identifier.strip() and identifier
                 and identifier not in seen and d in sessions
                 and positive_number(amount), "ACTION_ROW")
            key = (d, identifier)
            need(previous is None or key > previous, "ACTION_ORDER")
            seen.add(identifier)
            rows.append((d, amount))
            previous = key
        parsed[symbol] = rows
    return parsed


def exact(v):
    return Fraction(v)


def signal_side(days, tapes, cash, anchor, decision):
    """Compute the sign only from sessions (anchor, decision]."""
    wealth = {symbol: Fraction(1) for symbol in SYMBOLS}
    a, b = days.index(anchor), days.index(decision)
    for prior, now in zip(days[a:b], days[a + 1:b + 1], strict=True):
        for s in SYMBOLS:
            wealth[s] *= (tapes[s][now] + cash[s].get(now, 0)) / tapes[s][prior]
    if wealth["SPY"] == wealth["TLT"]:
        return "CASH", "CASH"
    return ("TLT", "SPY") if wealth["SPY"] > wealth["TLT"] else ("SPY", "TLT")


def side_return(tape, cash, entry, exit_, bps, capital):
    fee = Fraction(bps, 10_000)
    cost = tape[entry] * (1 + fee)
    shares = capital // cost
    payouts = sum(amount for d, amount in cash.items() if entry < d <= exit_)
    net = shares * (tape[exit_] * (1 - fee) + payouts - cost) / capital
    return net, shares


def summary(vals):
    vals = list(vals)
    n, total = len(vals), sum(vals, Fraction(0))
    square = n * sum(v * v for v in vals) - total * total
    t = None
    if n >= 2 and square > 0:
        t = sqrt(float((n - 1) * total * total / square))
        if total < 0:
            t = -t
    return {"n": n, "mean": float(total / n) if n else None, "t": t}


def assess(rows, cfg):
    m = cfg["marks"]
    values = [r["difference"] for r in rows]
    primary = summary(values)
    year_values = {str(y): [r["difference"] for r in rows if r["exit"].year == y]
                   for y in range(day(cfg["first"]).year, day(cfg["last"]).year + 1)}
    trim = sorted(values, reverse=True)[m["drop_best"]:]
    recent = [r["difference"] for r in rows if r["exit"] >= day(m["recent_from"])]
    plain = [r["conditional"] for r in rows]
    laggard = [r["laggard_minus_winner"] for r in rows]

    def positive(v):
        return bool(v) and sum(v) > exact(m["positive_cutoff"]) * len(v)

    positive_years = sum(map(positive, year_values.values()))
    n, total = len(values), sum(values)
    # Compare the squared one-sample t exactly; the sign and variance tests
    # prevent accepting a negative or undefined t.
    square = n * sum(v * v for v in values) - total * total
    t_pass = n >= 2 and total > 0 and square > 0 and (n - 1) * total * total >= exact(m["minimum_t"])**2 * square

    marks = {
        "minimum_months": primary["n"] >= m["minimum_months"],
        "positive_mean": positive(values),
        "minimum_t": t_pass,
        "positive_after_best_removed": positive(trim),
        "positive_years": positive_years >= m["minimum_positive_years"],
        "positive_recent": positive(recent),
        "positive_plain": positive(plain),
        "positive_laggard_minus_winner": positive(laggard),
    }
    return {"difference": primary, "trimmed_difference": summary(trim), "recent_difference": summary(recent),
            "years": {y: summary(v) for y, v in year_values.items()}, "positive_years": positive_years,
            "conditional": summary(plain), "laggard_minus_winner": summary(laggard), "marks": marks,
            "passed": all(marks.values())}


def evaluate(days, windows, tapes, actions, cfg):
    tapes = {s: {d: exact(x) for d, x in tapes[s].items()} for s in SYMBOLS}
    cash = {s: defaultdict(Fraction) for s in SYMBOLS}
    for s in SYMBOLS:
        for d, amount in actions[s]:
            cash[s][d] += exact(amount)
    capital = exact(cfg["capital"])
    judged = cfg["costs"]["judged"]
    signals = [(w, signal_side(days, tapes, cash, *w[:2])) for w in windows]

    def settled(bps):
        rows = []
        mix = exact(cfg["fixed_spy_weight"])
        for (anchor, decision, entry, exit_, next_first), (laggard, winner) in signals:
            by_fund = {s: side_return(tapes[s], cash[s], entry, exit_, bps, capital) for s in SYMBOLS}
            by_fund["CASH"] = (Fraction(0), 0)
            c, shares = by_fund[laggard]
            mirror = by_fund[winner][0]
            bond, spy = (by_fund[s][0] for s in ("TLT", "SPY"))
            rows.append({"anchor": anchor, "decision": decision, "entry": entry, "exit": exit_,
                         "selected": laggard, "shares": shares, "conditional": c, "always_tlt": bond,
                         "always_spy": spy, "difference": c - bond, "mirror": mirror,
                         "laggard_minus_winner": c - mirror, "fixed_mix": mix * spy + (1 - mix) * bond})
        return rows

    rows = settled(judged)
    result = assess(rows, cfg)
    summarize = lambda field, group=rows: summary(r[field] for r in group)
    reversal = []
    for (_, _, _, exit_, next_first), (laggard, winner) in signals:
        if next_first is not None:
            returns = {s: side_return(tapes[s], cash[s], exit_, next_first, judged, capital)[0] for s in SYMBOLS}
            returns["CASH"] = Fraction(0)
            reversal.append(returns[winner] - returns[laggard])
    shown = {
        "always_spy": summarize("always_spy"),
        "always_tlt": summarize("always_tlt"),
        "spy_on_spy_signal": summarize("always_spy", [r for r in rows if r["selected"] == "SPY"]),
        "spy_on_other_signals": summarize("always_spy", [r for r in rows if r["selected"] != "SPY"]),
        "mirror": summarize("mirror"),
        "fixed_mix": summarize("fixed_mix"),
        "conditional_minus_fixed_mix": summary(r["conditional"] - r["fixed_mix"] for r in rows),
        "first_next_session_winner_minus_laggard": summary(reversal),
        "without_january_2016": summarize("difference", rows[1:]),
        "cost_sensitivity": {},
    }
    for bps in cfg["costs"]["shown"]:
        alt = settled(bps)
        shown["cost_sensitivity"][str(bps)] = {f: summarize(f, alt)
                                              for f in ("conditional", "difference", "laggard_minus_winner")}
    monthly = [{k: v.isoformat() if isinstance(v, date) else float(v) if isinstance(v, Fraction) else v
                for k, v in r.items()} for r in rows]
    return {"judged": result, "shown_only": shown, "monthly": monthly,
            "selected_counts": {s: sum(r["selected"] == s for r in rows) for s in (*SYMBOLS, "CASH")},
            "selected_but_unaffordable": {
                s: sum(r["selected"] == s and r["shares"] == 0 for r in rows) for s in SYMBOLS}}
