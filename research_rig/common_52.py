"""Calendar, packet contract and post-lock mathematics for Plan 52."""
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
from itertools import groupby
from math import isfinite, sqrt
import random
import re
from statistics import fmean, stdev
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

BPS = 10_000


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P52_" + code)


def keys(value, expected, code):
    need(type(value) is dict and value.keys() == set(expected.split()), code)


def day(value):
    need(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), "DATE")
    return date.fromisoformat(value)


def utc(value):
    need(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value), "UTC")
    return datetime.fromisoformat(value)


def symbols(cfg):
    return sorted(set(cfg["funds"]) | set(cfg["proxies"].values()))


def calendar(blobs, cfg):
    start, end = map(day, (cfg["first_bar_date"], cfg["last_bar_date"]))
    sessions = []
    versions = set()
    for blob in blobs:
        keys(blob, "calendar sessions version", "CALENDAR")
        need(blob["calendar"] == "XNYS" and isinstance(blob["version"], str), "CALENDAR")
        versions.add(blob["version"])
        sessions.extend(d for d in map(day, blob["sessions"]) if start <= d <= end)
    need(len(versions) == 1 and len(sessions) == cfg["sessions_per_symbol"]
         and sessions == sorted(set(sessions)) and sessions[0] == start
         and sessions[-1] == end, "CALENDAR")
    return tuple(sessions)


def windows(days, cfg):
    out = {k: [] for k in ("quarters", "controls", "shown")}
    non_december = 0
    for (y, m), group in groupby(enumerate(days), key=lambda x: (x[1].year, x[1].month)):
        i, entry = list(group)[-1]
        if y < cfg["judged_first_year"] or entry.isoformat()[:7] > cfg["shown_last_month"]:
            continue
        quarter = m % 3 == 0
        if y > cfg["judged_last_year"] and not quarter:
            continue
        which = ("quarters" if quarter else "controls") if y <= cfg["judged_last_year"] else "shown"
        after = days[i+1:i+1+cfg["held_sessions"]]
        next_month = (y + (m == 12), m % 12 + 1)
        need(len(after) == cfg["held_sessions"] and all((d.year, d.month) == next_month for d in after), "WINDOW")
        out[which].append((entry, after))
        non_december += which == "quarters" and m != 12
    need(({k: len(v) for k, v in out.items()} | {"non_december": non_december}) == cfg["expected"], "COUNTS")
    return out


def positive(v, cfg):
    if type(v) not in (int, float, Decimal):
        return False
    d = v if type(v) is Decimal else Decimal(str(v))
    if not d.is_finite() or d <= 0:
        return False
    t = d.as_tuple()
    r = cfg["resources"]
    return len(t.digits) <= r["max_numeric_digits"] and abs(t.exponent) <= r["max_numeric_scale"]


def exact(v):
    return Fraction(str(v)) if type(v) is float else Fraction(v)


def bars(rows, days, cfg):
    need(type(rows) is list and len(rows) == len(days), "BAR_COVERAGE")
    ny = ZoneInfo("America/New_York")
    prev, run = None, 0
    closes = {}
    for expected, row in zip(days, rows, strict=True):
        keys(row, "t o h l c v", "BAR_FIELDS")
        stamp = utc(row["t"]).astimezone(ny)
        need(stamp.date() == expected and stamp.hour == stamp.minute == stamp.second == 0, "BAR_CLOCK")
        o, h, l, c = shape = tuple(row[k] for k in ("o", "h", "l", "c"))
        need(all(positive(v, cfg) for v in (*shape, row["v"])) and l <= min(o, c) <= max(o, c) <= h, "BAR_VALUES")
        run = run + 1 if shape == prev else 1
        need(run < cfg["max_identical_ohlc_run_exclusive"], "BAR_STALE")
        prev = shape
        closes[expected] = exact(c)
    return closes


def cash_actions(obj, days, spans, cfg):
    keys(obj, "schema coverage_start coverage_end funds", "ACTION_FIELDS")
    need(type(obj["schema"]) is int and obj["schema"] == 1
         and day(obj["coverage_start"]) <= days[0] <= days[-1] <= day(obj["coverage_end"])
         and type(obj["funds"]) is dict and set(obj["funds"]) == set(symbols(cfg)), "ACTION_COVERAGE")
    clock = set(days)
    years = {d.year for d in days}
    result, splits_checked = {}, 0
    for s, value in obj["funds"].items():
        keys(value, "source cash splits", "ACTION_FIELDS")
        src = urlsplit(value["source"])
        need(src.scheme == "https" and src.hostname and not src.username and not src.password, "ACTION_SOURCE")
        need(value["splits"] == cfg["expected_splits"].get(s, []), "ACTION_SPLIT_SET")
        for split in value["splits"]:
            need(type(split["old"]) is int and type(split["new"]) is int, "ACTION_SPLIT_SET")
            ex = day(split["ex_date"])
            need(ex in clock and all(not (entry < ex <= after[-1]) for group in spans.values()
                                     for entry, after in group), "ACTION_SPLIT_WINDOW")
            splits_checked += 1
        need(type(value["cash"]) is list, "ACTION_FIELDS")
        ids, cash = set(), {}
        for row in value["cash"]:
            keys(row, "id ex_date amount", "ACTION_FIELDS")
            ex, uid, amount = day(row["ex_date"]), row["id"], row["amount"]
            need(type(uid) is str and uid.strip() and uid == uid.strip() and uid not in ids
                 and ex in clock and positive(amount, cfg), "ACTION_CASH")
            ids.add(uid)
            cash[ex] = cash.get(ex, 0) + exact(amount)
        need({d.year for d in cash} == years, "ACTION_YEAR")
        result[s] = cash
    return result, splits_checked


def t_value(xs):
    sd = stdev(xs) if len(xs) > 1 else 0
    return fmean(xs) * sqrt(len(xs)) / sd if sd else None


def summary(xs):
    return {"count": len(xs), "mean": fmean(xs), "t": t_value(xs), "positive": sum(x > 0 for x in xs)}


def shown_gap(quarters, controls):
    quarters, controls = [list(map(exact, xs)) for xs in (quarters, controls)]
    qm, cm = exact_mean(quarters), exact_mean(controls)
    difference = qm - cm
    se_squared = exact_sample_variance(quarters, qm) / len(quarters) + exact_sample_variance(controls, cm) / len(controls)
    return {"net_mean_difference": float(difference), "welch_t": report_t(difference, se_squared)}


def panel(net, proxy_net, controls, is_non_december, cfg):
    m = cfg["marks"]
    floor, t = m["strict_floor"], m["minimum_t"]
    plain, credit, other = summary(net), summary(proxy_net), summary(controls)
    trim = fmean(sorted(net)[:-m["drop_best"]])
    non_dec = fmean(x for x, keep in zip(net, is_non_december, strict=True) if keep)
    breadth = m["positive_share"]
    marks = {
        "mean_net": plain["mean"] > floor,
        "t_net": plain["t"] is not None and plain["t"] >= t,
        "mean_proxy_net": credit["mean"] > floor,
        "t_proxy_net": credit["t"] is not None and credit["t"] >= t,
        "above_non_quarter_month_ends": plain["mean"] > other["mean"],
        "trimmed_net": trim > floor,
        "non_december_net": non_dec > floor,
    }
    breadth_marks = {
        "sixty_percent": plain["positive"] * breadth["denominator"] >= len(net) * breadth["numerator"],
        "strict_majority": plain["positive"] > len(net) - plain["positive"],
    }
    return {"net": plain, "proxy_net": credit, "controls_net": other,
            "trimmed_net_mean": trim, "non_december_net_mean": non_dec}, marks, breadth_marks


def apply_marks(marks, breadth_marks, raw_t_required, breadth):
    active = dict(marks)
    if not raw_t_required:
        del active["t_net"]
    if breadth != "none":
        active["positive_quarters"] = breadth_marks[breadth]
    return active


def exact_mean(values):
    return sum(values, Fraction(0)) / len(values)


def exact_sample_variance(values, mean):
    return sum(((v - mean)**2 for v in values), Fraction(0)) / (len(values) - 1) if len(values) > 1 else None


def report_t(mean, se_squared):
    return (1 if mean >= 0 else -1) * sqrt(float(mean**2 / se_squared)) if se_squared else None


def exact_stats(values, threshold):
    mean = exact_mean(values)
    var = exact_sample_variance(values, mean)
    se_squared = var / len(values) if var is not None else None
    passes_t = bool(se_squared and mean >= 0 and mean**2 >= threshold**2 * se_squared)
    report = {"count": len(values), "mean": float(mean), "t": report_t(mean, se_squared),
              "positive": sum(v > 0 for v in values)}
    return mean, passes_t, report


def judge(net, proxy_net, controls, is_non_december, cfg):
    net, proxy_net, controls = [[exact(v) for v in series] for series in (net, proxy_net, controls)]
    m = cfg["marks"]
    floor, threshold = exact(m["strict_floor"]), exact(m["minimum_t"])
    a, ta, raw_report = exact_stats(net, threshold)
    b, tb, proxy_report = exact_stats(proxy_net, threshold)
    c, _, control_report = exact_stats(controls, threshold)
    trim = exact_mean(sorted(net)[:-m["drop_best"]])
    non_dec = exact_mean([x for x, keep in zip(net, is_non_december, strict=True) if keep])
    pos, n = raw_report["positive"], len(net)
    r = m["positive_share"]
    breadth = {"sixty_percent": pos * r["denominator"] >= n * r["numerator"], "strict_majority": pos > n - pos}
    base = {"mean_net": a > floor, "t_net": ta, "mean_proxy_net": b > floor, "t_proxy_net": tb,
            "above_non_quarter_month_ends": a > c, "trimmed_net": trim > floor, "non_december_net": non_dec > floor}
    marks = apply_marks(base, breadth, m["raw_t_required"], m["breadth"])
    metrics = {"net": raw_report, "proxy_net": proxy_report, "controls_net": control_report,
               "trimmed_net_mean": float(trim), "non_december_net_mean": float(non_dec)}
    return metrics | {"marks": marks, "supported": all(marks.values())}


def exact_window_return(entry_close, exit_close, payouts, f):
    return (exact(exit_close) * (1-f) + exact(payouts)) / (exact(entry_close) * (1+f)) - 1


def window_return(entry_close, exit_close, payouts, f):
    """Floating-point model for generated worlds only."""
    value = (exit_close * (1-f) + payouts) / (entry_close * (1+f)) - 1
    need(isfinite(value), "RETURN")
    return value


def evaluate(spans, prices, cash, cfg):
    f = Fraction(cfg["cost_bps_per_side"], BPS)
    book = {}
    for group, rows in spans.items():
        events = []
        for entry, held in rows:
            def ret(symbol, fee):
                return exact_window_return(prices[symbol][entry], prices[symbol][held[-1]],
                                           sum((exact(cash[symbol].get(d, 0)) for d in held), Fraction(0)), fee)

            net = {s: ret(s, f) for s in cfg["funds"]}
            proxies = {s: ret(s, 0) for s in set(cfg["proxies"].values())}
            raw, credit = exact_mean(net.values()), exact_mean([net[s] - proxies[p] for s, p in cfg["proxies"].items()])
            events.append({"entry": entry.isoformat(), "exit": held[-1].isoformat(), "net": raw,
                           "proxy_net": credit, "net_usd": raw * cfg["budget_usd"]})
        book[group] = events
    q = book["quarters"]
    raw, controls = [e["net"] for e in q], [e["net"] for e in book["controls"]]
    verdict = judge(raw, [e["proxy_net"] for e in q], controls, [e["entry"][5:7] != "12" for e in q], cfg)
    report = {group: [{k: float(v) if type(v) is Fraction else v for k, v in e.items()} for e in rows]
              for group, rows in book.items()}
    return {"judged": verdict, "events": report, "shown_only": {"quarter_minus_control_net": shown_gap(raw, controls)}}


def upper_wilson(hits, n, z):
    p = hits / n
    return (p + z*z / (2*n) + z * sqrt(p*(1-p)/n + z*z/(4*n*n))) / (1 + z*z/n)


def calibration_variants():
    return [(raw, breadth) for raw in (True, False)
            for breadth in ("sixty_percent", "strict_majority", "none")]


def calibration_record(cfg, hits):
    a = cfg["calibration"]
    n, rows = a["worlds"], []
    edges = a["edge_bps"]
    for raw, breadth in calibration_variants():
        scenarios = {}
        for world in ("quarter_only", "all_month_ends"):
            scenarios[world] = {}
            for edge in edges:
                count = hits[raw, breadth, world, edge]
                need(type(count) is int and 0 <= count <= n, "CALIBRATION")
                scenarios[world][str(edge)] = {"count": count, "rate": count / n}
        null = scenarios["quarter_only"]["0"]
        need(null == scenarios["all_month_ends"]["0"]
             and all(scenarios["all_month_ends"][str(e)]["count"] <= scenarios["quarter_only"][str(e)]["count"]
                     for e in edges), "CALIBRATION")
        upper = upper_wilson(null["count"], n, a["one_sided_normal_z"])
        rows.append({"raw_t_required": raw, "breadth": breadth, "scenarios": scenarios,
                     "null_upper_wilson": upper,
                     "eligible": null["rate"] <= a["null_rate_cap"] and upper <= a["null_upper_cap"]})
    # Rows are strictest-first for ties; max returns the first maximizer.
    eligible = [row for row in rows if row["eligible"]]
    need(eligible, "NO_CALIBRATION_CANDIDATE")
    winner = max(eligible, key=lambda row: row["scenarios"]["quarter_only"][str(a["power_target_bps"])]["count"])
    return {"synthetic_only": True, "assumptions": a, "observations": cfg["expected"], "variants": rows,
            "selected": {k: winner[k] for k in ("raw_t_required", "breadth")}}


def calibrate(cfg):
    """Synthetic model grid on common draws; never a candidate search on real data."""
    a = cfg["calibration"]
    rng = random.Random(a["seed"])
    widths = cfg["held_sessions"]
    f = cfg["cost_bps_per_side"] / BPS
    edges = a["edge_bps"]
    variants = calibration_variants()
    worlds = ("quarter_only", "all_month_ends")
    hits = {(raw, breadth, world, edge): 0 for raw, breadth in variants for world in worlds for edge in edges}
    dates = [(y, m) for y in range(cfg["judged_first_year"], cfg["judged_last_year"] + 1) for m in range(1, 13)]
    non_dec = [m != 12 for _, m in dates if m % 3 == 0]
    for _ in range(a["worlds"]):
        year = {y: rng.gauss(0, a["year_sd_bps"]) / BPS for y, m in dates if m == 1}
        q, control = [], []
        for y, m in dates:
            proxy = sum(rng.gauss(0, a["proxy_daily_sd_bps"]) for _ in range(widths)) / BPS
            credit = year[y] + sum(rng.gauss(0, a["credit_daily_sd_bps"]) for _ in range(widths)) / BPS
            if m % 3 == 0:
                q.append((proxy, credit))
            else:
                control.append(window_return(1, 1 + proxy + credit, 0, f))
        for edge in edges:
            net = [window_return(1, 1 + proxy + credit + edge / BPS, 0, f) for proxy, credit in q]
            residual = [n - p for n, (p, _) in zip(net, q, strict=True)]
            metrics, base, breadth_marks = panel(net, residual, control, non_dec, cfg)
            shift = (edge / BPS) * ((1-f)/(1+f))
            shared_base = base | {"above_non_quarter_month_ends":
                                  metrics["net"]["mean"] > metrics["controls_net"]["mean"] + shift}
            for raw, breadth in variants:
                plain = apply_marks(base, breadth_marks, raw, breadth)
                shared = apply_marks(shared_base, breadth_marks, raw, breadth)
                hits[raw, breadth, "quarter_only", edge] += all(plain.values())
                hits[raw, breadth, "all_month_ends", edge] += all(shared.values())

    return calibration_record(cfg, hits)
