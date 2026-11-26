"""Calendar, packet contract and post-lock mathematics for Plan 52."""
from datetime import date, datetime
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


def positive(v):
    return type(v) in (int, float) and isfinite(v) and v > 0


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
        need(all(map(positive, (*shape, row["v"]))) and l <= min(o, c) <= max(o, c) <= h, "BAR_VALUES")
        run = run + 1 if shape == prev else 1
        need(run < cfg["max_identical_ohlc_run_exclusive"], "BAR_STALE")
        prev = shape
        closes[expected] = c
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
                 and ex in clock and positive(amount), "ACTION_CASH")
            ids.add(uid)
            cash[ex] = cash.get(ex, 0) + amount
            need(isfinite(cash[ex]), "ACTION_CASH")
        need({d.year for d in cash} == years, "ACTION_YEAR")
        result[s] = cash
    return result, splits_checked


def t_value(xs):
    sd = stdev(xs) if len(xs) > 1 else 0
    return fmean(xs) * sqrt(len(xs)) / sd if sd else None


def summary(xs):
    return {"count": len(xs), "mean": fmean(xs), "t": t_value(xs), "positive": sum(x > 0 for x in xs)}


def judge(net, proxy_net, controls, is_non_december, cfg):
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
        "positive_quarters": plain["positive"] * breadth["denominator"] >= len(net) * breadth["numerator"],
    }
    return {"marks": marks, "supported": all(marks.values()), "net": plain, "proxy_net": credit,
            "controls_net": other, "trimmed_net_mean": trim, "non_december_net_mean": non_dec}


def window_return(entry_close, exit_close, payouts, f):
    value = (exit_close * (1-f) + payouts) / (entry_close * (1+f)) - 1
    need(isfinite(value), "RETURN")
    return value


def evaluate(spans, prices, cash, cfg):
    f = cfg["cost_bps_per_side"] / BPS
    book = {}
    for group, rows in spans.items():
        events = []
        for entry, held in rows:
            def ret(symbol, fee):
                return window_return(prices[symbol][entry], prices[symbol][held[-1]],
                                     sum(cash[symbol].get(d, 0) for d in held), fee)

            net = {s: ret(s, f) for s in cfg["funds"]}
            proxies = {s: ret(s, 0) for s in set(cfg["proxies"].values())}
            raw, credit = fmean(net.values()), fmean(net[s] - proxies[p] for s, p in cfg["proxies"].items())
            events.append({"entry": entry.isoformat(), "exit": held[-1].isoformat(), "net": raw,
                           "proxy_net": credit, "net_usd": raw * cfg["budget_usd"]})
        book[group] = events
    q = book["quarters"]
    verdict = judge([e["net"] for e in q], [e["proxy_net"] for e in q],
                    [e["net"] for e in book["controls"]], [e["entry"][5:7] != "12" for e in q], cfg)
    return {"judged": verdict, "events": book}


def calibrate(cfg):
    """Synthetic basket-level daily noise; no vendor data or external access."""
    a = cfg["calibration"]
    rng = random.Random(a["seed"])
    widths = cfg["held_sessions"]
    f = cfg["cost_bps_per_side"] / BPS
    edges = a["edge_bps"]
    hits = dict.fromkeys(edges, 0)
    by_mark = {edge: {} for edge in edges}
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
            grid = judge(net, residual, control, non_dec, cfg)
            hits[edge] += grid["supported"]
            for k, v in grid["marks"].items():
                by_mark[edge][k] = by_mark[edge].get(k, 0) + v
    return {"synthetic_only": True, "assumptions": a, "observations": cfg["expected"],
            "scenarios": [{"planted_gross_edge_bps": edge, "all_marks_pass_count": hits[edge],
                           "all_marks_pass_rate": hits[edge] / a["worlds"], "mark_pass_counts": by_mark[edge]}
                          for edge in edges]}
