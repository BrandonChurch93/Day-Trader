"""Pure scheduling and scoring for the fixed Coinbase reachability study."""
from collections import defaultdict
from datetime import datetime, timezone
import math

import numpy as np

import sweep_70 as sweep
from coinbase_72 import DIAG, FRESH, HOUR, MINUTE, MAX_BUCKETS, validate

DAY = 86400
YEARS = (2017, 2018, 2019)
PRIMARY = "71-013"
SHOWN = ("70-102", "71-035")


def stamp(iso):
    return int(datetime.fromisoformat(iso).replace(tzinfo=timezone.utc).timestamp())


def hourly_jobs(config):
    jobs = []
    for coin, first_day in sorted(config["sources"].items()):
        for start in range(stamp(first_day), FRESH[1], HOUR * MAX_BUCKETS):
            jobs.append(validate((coin, HOUR, start, min(start + HOUR * MAX_BUCKETS, FRESH[1])), "hourly"))
    return jobs


def activated(data, config):
    result, starts = {}, {}
    for coin in sorted(config["sources"]):
        hours = data.get((coin, HOUR), {})
        day_counts = defaultdict(int)
        for t in hours:
            day_counts[t // DAY * DAY] += 1
        first = min((d for d, n in day_counts.items() if n == 24), default=None)
        if first is None:
            raise ValueError("admitted Coinbase pair lacks any full UTC day: " + coin)
        starts[coin] = first
        result[coin] = {t: values for t, values in hours.items() if t >= first}
    if "BTC" not in result:
        raise ValueError("BTC signal candles are required")
    return result, starts


def schedule(hours, rules):
    """Job count: close-to-close signal only. No open price or realized payoff is used."""
    specs = (PRIMARY, *SHOWN)
    time = np.arange(FRESH[0], FRESH[1], HOUR)
    coins = sorted(hours)
    btc = coins.index("BTC")
    log_close = np.full((len(coins), len(time)), np.nan)
    for j, coin in enumerate(coins):
        for t, bar in hours[coin].items():
            if not FRESH[0] <= t < FRESH[1]:
                raise ValueError("non-fresh clock in signal source")
            log_close[j, (t - FRESH[0]) // HOUR] = math.log(bar[3])
    maint = np.array([sweep.maintenance(t) for t in time])
    result = {}
    for rid in specs:
        r = rules[rid]
        lag, mult, cut = (r["parameters"][k] for k in ("lag", "multiple", "threshold"))
        hold = r["hold_hours"]
        signed = np.full_like(log_close, np.nan)
        past = np.lib.stride_tricks.sliding_window_view(log_close, lag + 1, axis=1)[:, :-1]
        signed[:, lag+1:] = np.where(np.all(np.isfinite(past), axis=2), past[:, :, 0] - past[:, :, -1], np.nan)
        extra = signed - mult * signed[btc]
        extra[btc] = np.nan
        score = np.where(np.isfinite(extra) & (extra > 0) & (signed[btc] >= cut), extra, -np.inf)
        pick = np.argmax(score, axis=0)
        orders = []
        next_free = 0
        for i in np.flatnonzero(np.isfinite(score[pick, np.arange(len(time))])):
            if i < next_free or i + hold >= len(time) or np.any(maint[i:i+hold+1]):
                continue
            orders.append([coins[pick[i]], int(time[i]), int(time[i+hold])])
            next_free = i + hold
        result[rid] = orders
    return result


def count_fields(tickets):
    by_year = dict.fromkeys(map(str, YEARS), 0)
    for _, t, _ in tickets:
        by_year[str(datetime.fromtimestamp(t, timezone.utc).year)] += 1
    return {"tickets": len(tickets), "days": len({x[1] // DAY for x in tickets}),
            "coins": sorted({x[0] for x in tickets}), "tickets_per_year": by_year}


def window_jobs(fresh, diag, config):
    intervals = defaultdict(list)
    policy = config["minutes"]
    e = policy["judged"]
    span = policy["fallback_minutes"] + 1

    def add(coin, gran, lo, hi):
        job = validate((coin, gran, lo, hi), "windows")
        intervals[job[:2]].append(job[2:])

    def needed(coin, opening, offsets, fence):
        for offset in offsets:
            a = opening + offset * MINUTE
            if a < fence[1]:
                add(coin, MINUTE, a, min(a + span * MINUTE, fence[1]))

    for rid, tickets in fresh.items():
        for coin, opening, closing in tickets:
            needed(coin, opening, [e, *policy["shown_late"]] if rid == PRIMARY else [e], FRESH)
            needed(coin, closing, [e], FRESH)
            if rid == PRIMARY:
                needed("BTC", opening, [e], FRESH)
                needed("BTC", closing, [e], FRESH)
    for coin, opening, closing in diag:
        needed(coin, opening, [e, *policy["shown_late"]], DIAG)
        needed(coin, closing, [e], DIAG)
        add(coin, HOUR, opening, opening + HOUR)
        add(coin, HOUR, closing, closing + HOUR)
    requests = []
    for (coin, gran), spans in sorted(intervals.items()):
        merged = []
        for a, b in sorted(spans):
            # Do not join the fresh and diagnostic dates or fetch any unused gap.
            if merged and a <= merged[-1][1] and not (a >= DIAG[0] and merged[-1][0] < DIAG[0]):
                merged[-1][1] = max(b, merged[-1][1])
            else:
                merged.append([a, b])
        for a, b in merged:
            for t in range(a, b, gran * MAX_BUCKETS):
                requests.append(validate((coin, gran, t, min(t + gran * MAX_BUCKETS, b)), "windows"))
    return requests


def first_minute(data, coin, base, offset, config, fence):
    minutes = data.get((coin, MINUTE), {})
    for stagger in range(config["minutes"]["fallback_minutes"] + 1):
        t = base + (offset + stagger) * MINUTE
        if not fence[0] <= t < fence[1]:
            break
        if t in minutes:
            return t
    return None


def fallback(data, coin, base, offset, config, fence, *, field=None):
    t = first_minute(data, coin, base, offset, config, fence)
    if t is None:
        return None
    bar = data[coin, MINUTE][t]
    return (bar[1] + bar[2]) / 2 if field is None else bar[field]


def actual_overlaps(tickets, data, cfg, mode, offsets):
    """Clock-only gate. It does not inspect any price field, even on a dropped ticket."""
    if mode == "hourly":
        return set()
    last_exit = FRESH[0]
    rejected = set()
    for coin, opening, closing in tickets:
        coins = (coin, "BTC") if mode == "hedged" else (coin,)
        entries = [first_minute(data, c, opening, offsets[0], cfg, FRESH) for c in coins]
        exits = [first_minute(data, c, closing, offsets[1], cfg, FRESH) for c in coins]
        if None in entries or None in exits:
            continue
        if min(entries) < last_exit:
            rejected.add(opening)
        else:
            last_exit = max(exits)
    return rejected


def hourly_reference(hours, holds):
    out = {}
    for coin, bars in hours.items():
        for hold in holds:
            gross = defaultdict(list)
            for t in sorted(bars):
                if all(t+h*HOUR in bars and not sweep.maintenance(t+h*HOUR) for h in range(hold+1)):
                    gross[t // HOUR % 24].append(bars[t + hold*HOUR][0] / bars[t][0] - 1)
            for h, x in gross.items():
                out[coin, h, hold] = float(np.mean(x))
    return out


def ticket_value(ticket, mode, offsets, data, hourly, config, fees, fence=FRESH):
    coin, opening, closing = ticket

    def price(c, t, in_leg):
        if mode == "hourly":
            row = hourly.get(c, {}).get(t)
            return None if row is None else row[0]
        field = (1 if in_leg else 2) if mode == "worst" else None
        return fallback(data, c, t, offsets[0 if in_leg else 1], config, fence, field=field)

    a, b = price(coin, opening, True), price(coin, closing, False)
    if a is None:
        return None, "missing_entry_hour" if mode == "hourly" else "missing_entry_minute"
    if b is None:
        return None, "missing_exit_hour" if mode == "hourly" else "missing_exit_minute"
    gross, fee = b/a - 1, fees["futures_round_trip_bp"][coin]
    if mode == "hedged":
        x, y = price("BTC", opening, True), price("BTC", closing, False)
        if x is None or y is None:
            return None, "missing_hedge_minute"
        gross = .5 * (gross - (y/x - 1))
        fee = .5 * (fee + fees["futures_round_trip_bp"]["BTC"])
    hold = (closing-opening)//HOUR
    return gross - (fee + hold * fees["funding_adverse_bp_per_hour"]) / 10000, None


def aggregate(tickets, data, hourly, ref, cfg, fees, mode, offsets, mark, overlaps=None):
    net, paired, dates = [], [], []
    drops = defaultdict(int)
    if overlaps is None:
        overlaps = actual_overlaps(tickets, data, cfg, mode, offsets)
    for coin, opening, closing in tickets:
        if opening in overlaps:
            drops["actual_minute_overlap"] += 1
            continue
        ret, reason = ticket_value((coin, opening, closing), mode, offsets, data, hourly, cfg, fees)
        if reason is not None:
            drops[reason] += 1
            continue
        hold = (closing - opening) // HOUR
        key = (opening // HOUR % 24, hold)
        comparator = ref.get((coin, *key))
        if mode == "hedged" and comparator is not None:
            btc = ref.get(("BTC", *key))
            comparator = .5 * (comparator - btc) if btc is not None else None
        if comparator is None:
            drops["missing_hourly_reference"] += 1
            continue
        net.append(ret)
        paired.append(ret - comparator)
        dates.append(opening)
    p, m, times = np.array(net), np.array(paired), np.array(dates, dtype=np.int64)
    day = (times - FRESH[0]) // DAY
    active = len(np.unique(day))
    cutoff = len(p) - max(1, math.ceil(len(p) * mark["trim_share"]))
    trimmed = float(np.sort(p)[:cutoff].mean()) if cutoff > 0 else None
    year_sums = {}
    for y in YEARS:
        a = stamp(f"{y}-01-01")
        b = stamp(f"{y+1}-01-01")
        year_sums[str(y)] = float(p[(a <= times) & (times < b)].sum())
    t = sweep.t_cluster(m, day)
    passed = (len(p) >= mark["min_tickets"] and active >= mark["min_days"] and p.mean() > 0
              and t is not None and t >= mark["matched_t"] and trimmed is not None and trimmed > 0
              and sum(x > 0 for x in year_sums.values()) >= mark["positive_years"])
    return {"scheduled": len(tickets), "tickets": len(p), "active_days": active,
            "rows_dropped_by_reason": dict(sorted(drops.items())), "plain_mean": float(p.mean()) if len(p) else None,
            "matched_mean": float(m.mean()) if len(m) else None, "matched_day_t": t,
            "trimmed_plain_mean": trimmed, "plain_net_by_year": year_sums, "meets_marks": bool(passed)}


def power(tickets, half_edge, cfg, mark):
    """Invented day/individual noise, fixed exact count schedule, no real payoffs."""
    p = cfg["power"]
    day = np.array([(t - FRESH[0]) // DAY for _, t, _ in tickets], dtype=int)
    years = [np.array([stamp(f"{y}-01-01") <= t < stamp(f"{y+1}-01-01") for _, t, _ in tickets], dtype=bool)
             for y in YEARS]
    n, active = len(day), len(np.unique(day))
    cut = n - max(1, math.ceil(n * mark["trim_share"]))
    passes = 0
    if n >= mark["min_tickets"] and active >= mark["min_days"] and active >= 2 and cut > 0:
        rng = np.random.Generator(np.random.PCG64(p["seed"]))
        total_days = (FRESH[1] - FRESH[0]) // DAY
        for _ in range(p["draws"]):
            x = (half_edge + rng.normal(0, p["day_noise_bp"] / 10000, total_days)[day]
                 + rng.normal(0, p["ticket_noise_bp"] / 10000, n))
            t = sweep.t_cluster(x, day)
            passes += (x.mean() > 0 and t is not None and t >= mark["matched_t"]
                       and np.partition(x, cut - 1)[:cut].mean() > 0
                       and sum(x[mask].sum() > 0 for mask in years) >= mark["positive_years"])
    return {"draws": p["draws"], "passes": int(passes), "half_edge_bp": half_edge * 10000,
            "probability": float(passes / p["draws"]), "schedule_tickets": n, "schedule_days": active}


def outage_touch(opening, closing, outage):
    return any(t // DAY in outage for t in range(opening - 2 * HOUR, closing + HOUR, HOUR))


def diagnostic(tickets, data, cfg, fees, *, detailed=False):
    """One common sample for apples-to-apples venue and clock repricing."""
    policy = cfg["minutes"]
    clock = policy["judged"]
    modes = {"coinbase_hourly_open": ("hourly", (0, 0)),
             "coinbase_reachable_minute": ("midpoint", (clock, clock)),
             **{f"coinbase_entry_{n}m_late": ("midpoint", (n, clock)) for n in policy["shown_late"]}}
    if detailed:
        modes["coinbase_worst_minute"] = ("worst", (clock, clock))
    hourly = {c: v for (c, gran), v in data.items() if gran == HOUR}
    outage = {stamp(d) // DAY for d in cfg["outage_utc_dates"]}
    coverage = dict.fromkeys(modes, 0)
    filtered_coverage = dict.fromkeys(modes, 0)
    filtered_scheduled = 0
    common = []
    detail = []
    for coin, opening, closing, search_net in tickets:
        ex = outage_touch(opening, closing, outage)
        if detailed and ex:
            detail.append((coin, opening, closing, None, None))
            continue
        filtered_scheduled += not ex
        priced = {key: ticket_value((coin, opening, closing), mode, args, data, hourly, cfg, fees, DIAG)
                  for key, (mode, args) in modes.items()}
        if detailed:
            detail.append((coin, opening, closing, search_net, priced))
            continue
        result = {key: pair[0] for key, pair in priced.items()}
        for k, v in result.items():
            coverage[k] += v is not None
            if not ex:
                filtered_coverage[k] += v is not None
        if any(v is None for v in result.values()):
            continue
        common.append((search_net, result, ex))

    if detailed:
        return tuple(modes), detail

    def summarize(records):
        mean = float(np.mean([r[0] for r in records])) if records else None
        estimates = {key: float(np.mean([r[1][key] for r in records])) if records else None for key in modes}
        return {"tickets": len(records), "frozen_search_plain_mean": mean,
                "coinbase_plain_mean": estimates,
                "share_of_same_population_search_mean": {k: v / mean if mean else None
                                                         for k, v in estimates.items()}}
    return {"kind": "shown_search_dates_not_a_test", "scheduled": len(tickets), "observed_by_clock": coverage,
            "scheduled_after_named_outage_dates": filtered_scheduled,
            "observed_by_clock_after_named_outage_dates": filtered_coverage,
            "same_tickets_all_clocks": summarize(common),
            "same_tickets_after_named_outage_dates": summarize([r for r in common if not r[2]])}
