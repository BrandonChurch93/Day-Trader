"""Pure clock, data-quality and post-claim statistics for Plan 31."""
from datetime import date
from math import fsum, isfinite, sqrt

import common_25 as prior

PROXY = {"LQD": "IEF", "HYG": "IEI", "MBB": "IEF", "TIP": "IEF"}
FUNDS = tuple(PROXY)
SYMBOLS = (*FUNDS, "IEF", "IEI", "SPY")
START, END = date(2016, 1, 4), date(2026, 10, 30)
JAN = (2016, 1)
WARMUP = 60
COLLINEARITY = 1e-12


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P31_" + code)


def calendar(obj):
    source_days = prior.check_calendar(obj)
    days = tuple(d for d in source_days if START <= d <= END)
    need(len(days) == 2723 and days[0] == START and days[-1] == END, "CALENDAR")
    return days


def design(days):
    """Calendar only. Fitting indices never end in a judged or shown window."""
    schedules = prior.months(days)
    end_days = {d for rows in schedules.values() for d in rows[-3:]}
    outside = tuple(d for d in days[1:] if d not in end_days)
    months = {}
    for key, rows in schedules.items():
        buy, sell, inside = rows[-4], rows[-1], rows[-3:]
        prior_count = sum(d < rows[0] for d in outside)
        cutoff = buy if key == JAN else rows[0]
        training = tuple(d for d in outside if d < cutoff)
        months[key] = (buy, sell, inside, training, prior_count >= WARMUP)
    need(len(months) == 130 and sum(item[-1] for item in months.values()) == 126, "CALENDAR")
    need(len(months[JAN][3]) == 14, "CALENDAR")
    return months


def iso_day(s):
    need(type(s) is str, "CLOCK")
    d = date.fromisoformat(s)
    need(s == d.isoformat(), "CLOCK")
    return d


def action_packet(obj, days):
    need(type(obj) is dict and set(obj) == {"schema", "coverage_start", "coverage_end", "funds"}
         and type(obj["schema"]) is int and obj["schema"] == 1
         and iso_day(obj["coverage_start"]) == START and iso_day(obj["coverage_end"]) == END
         and type(obj["funds"]) is dict and set(obj["funds"]) == set(SYMBOLS), "ACTIONS")
    day_set, out = set(days), {}
    for sym in SYMBOLS:
        fund = obj["funds"][sym]
        need(type(fund) is dict and set(fund) == {"source", "splits", "cash"}
             and type(fund["source"]) is str and fund["source"].startswith("https://")
             and fund["splits"] == [] and type(fund["cash"]) is list and fund["cash"], "ACTIONS")
        ids, covered = set(), set()
        for event in fund["cash"]:
            need(type(event) is dict and set(event) == {"id", "ex_date", "amount"}
                 and type(event["id"]) is str and bool(event["id"].strip())
                 and event["id"] not in ids, "ACTIONS")
            d = iso_day(event["ex_date"])
            need(d in day_set, "ACTION_CLOCK")
            covered.add(d.year)
            ids.add(event["id"])
        need(covered == set(prior.YEARS), "ACTION_COVERAGE")
        out[sym] = prior.distributions(fund["cash"])
    return out


def bar_tape(rows, days):
    need(type(rows) is list and len(rows) == len(days) and all(
        type(r) is dict and set(r) == {"t", "o", "h", "l", "c", "v"} for r in rows), "BARS")
    prior.check_bar_clocks(rows, days)
    return prior.price_tape(rows, days)


def daily_returns(days, bars, cash):
    result = {
        sym: {d: (bars[sym][d].c + cash[sym].get(d, 0)) / bars[sym][p].c - 1
              for p, d in zip(days, days[1:])}
        for sym in SYMBOLS
    }
    need(all(isfinite(r) for by_day in result.values() for r in by_day.values()), "NUMERIC")
    return result


def slopes(y, x1, x2):
    """OLS intercept is used for fitting, but only the slopes are returned."""
    n = len(y)
    need(n >= 3 and n == len(x1) == len(x2), "FIT_COUNT")
    # Compute means once, and standardize regressors before checking rank.
    yc, a, b = ([x - avg for x in xs] for xs, avg in ((v, prior.fmean(v)) for v in (y, x1, x2)))
    norm = lambda xs: sqrt(fsum(x*x for x in xs))
    dot = lambda xs, ys: fsum(x*y for x, y in zip(xs, ys, strict=True))
    an, bn = norm(a), norm(b)
    need(all(isfinite(v) and v > 0 for v in (an, bn)), "FIT_SINGULAR")
    u, v = [x/an for x in a], [x/bn for x in b]
    rho = dot(u, v)
    det = 1 - rho*rho
    need(isfinite(det) and det > COLLINEARITY, "FIT_SINGULAR")
    uy, vy = dot(u, yc), dot(v, yc)
    coeff = ((uy-rho*vy)/det/an, (vy-rho*uy)/det/bn)
    need(all(isfinite(c) for c in coeff), "FIT_NUMERIC")
    return coeff


def factors(sym, training, daily):
    def use(s):
        return [daily[s][d] for d in training]
    return slopes(use(sym), use(PROXY[sym]), use("SPY"))


def residual(sym, betas, gross, fund_return):
    b_t, b_s = betas[sym]
    return fund_return - b_t * gross[PROXY[sym]] - b_s * gross["SPY"]


def evaluate(days, bars, cash, schedule):
    daily = daily_returns(days, bars, cash)
    judged, early = [], []
    daily_year = {y: ([], []) for y in prior.YEARS}
    month_days = prior.months(days)
    for key, (buy, sell, inside, training, counts) in schedule.items():
        beta = {sym: factors(sym, training, daily) for sym in FUNDS}
        span = [(buy, sell, inside)]
        gross = {s: prior.window_values(bars[s], cash[s], span, 0)[0][1]
                 for s in ("IEF", "IEI", "SPY")}
        by_cost = {}
        for c in prior.COSTS:
            plain = {s: prior.window_values(bars[s], cash[s], span, c)[0][1] for s in FUNDS}
            res = {s: residual(s, beta, gross, plain[s]) for s in FUNDS}
            by_cost[c] = (prior.fmean(plain.values()), prior.fmean(res.values()), plain, res)
        if not counts:
            early.append({"month": f"{key[0]}-{key[1]:02d}", "fit_intervals": len(training),
                          "plain_net": by_cost[2][0], "residual_net": by_cost[2][1]})
            continue
        judged.append((key[0], by_cost, beta))
        for d in month_days[key]:
            factor_returns = {s: daily[s][d] for s in ("IEF", "IEI", "SPY")}
            pooled = prior.fmean(residual(s, beta, factor_returns, daily[s][d]) for s in FUNDS)
            daily_year[key[0]][0 if d in inside else 1].append(pooled)
    all_a, all_b = ([r for values in daily_year.values() for r in values[i]] for i in (0, 1))
    need((len(all_a), len(all_b)) == (378, 2263), "COMPARATOR_CLOCK")
    return summarize(judged, early, daily_year, all_a, all_b)


def summarize(judged, early, daily_year, all_a, all_b):
    vals = [cost[2][1] for _, cost, _ in judged]
    plain = [cost[2][0] for _, cost, _ in judged]
    byyear = {str(y): prior.pack([c[2][1] for yr, c, _ in judged if yr == y]) for y in prior.YEARS}
    leave = {str(y): prior.pack([c[2][1] for yr, c, _ in judged if yr != y]) for y in prior.YEARS}
    daily = {str(y): prior.compare(*pair) for y, pair in daily_year.items()}
    gap = prior.compare(all_a, all_b)
    stats = prior.pack(vals)
    trimmed = prior.mean(sorted(vals)[:-prior.TRIM])
    post = prior.mean([c[2][1] for y, c, _ in judged if y >= 2020])
    positive = lambda x: x is not None and x > 0
    t_ok = lambda x: x is not None and x >= prior.MIN_T
    yr_count = sum(positive(x["mean_net"]) for x in byyear.values())
    daily_count = sum(positive(x["difference"]) for x in daily.values())
    plain_summary = prior.pack(plain)
    gates = {
        "windows": stats["n"] >= prior.MIN_WINDOWS,
        "residual_positive_mean": positive(stats["mean_net"]),
        "residual_window_t": t_ok(stats["t"]),
        "residual_trimmed_positive": positive(trimmed),
        "daily_difference_and_t": positive(gap["difference"]) and t_ok(gap["welch_t"]),
        "positive_year_share": yr_count >= 7,
        "post_2019_positive": positive(post),
        "every_leave_one_year_out_positive": all(positive(x["mean_net"]) for x in leave.values()),
        "positive_daily_year_share": daily_count >= 7,
        "plain_net_pooled_positive": positive(plain_summary["mean_net"]),
    }
    shown = {str(cost): {
        "plain": prior.pack([c[cost][0] for _, c, _ in judged]),
        "residual": prior.pack([c[cost][1] for _, c, _ in judged]),
        "by_fund": {s: {"plain": prior.pack([c[cost][2][s] for _, c, _ in judged]),
                       "residual": prior.pack([c[cost][3][s] for _, c, _ in judged])} for s in FUNDS},
    } for cost in prior.COSTS}
    beta = {s: {factor: {"min": min(legs[s][i] for _, _, legs in judged),
                          "max": max(legs[s][i] for _, _, legs in judged)}
                for i, factor in enumerate((PROXY[s], "SPY"))} for s in FUNDS}
    return {"judged": stats | {"gates": gates, "passes": all(gates.values()),
                             "trimmed_mean": trimmed, "post_2019_mean": post,
                             "positive_years": yr_count, "positive_daily_years": daily_count,
                             "by_year": byyear, "leave_one_year_out": leave, "daily": gap,
                             "daily_by_year": daily, "plain": plain_summary},
            "shown": {"by_cost": shown, "beta_ranges": beta, "warmup_months": early}}
