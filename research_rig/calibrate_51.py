"""Pure synthetic calibration for Plan 51; never opens a market-data path."""
from datetime import datetime, timezone
import math
import random

try:
    from . import common_51 as C
except ImportError:
    import common_51 as C


def growth(prefix, spells, gaps, edge_cost, rebalance_cost):
    t, result = gaps[0], 0.0
    for i, n in enumerate(spells):
        result += prefix[t + n] - prefix[t] + edge_cost + (n - 1) * rebalance_cost
        t += n + gaps[i + 1]
    return math.exp(result)


def draw(rng, p, edge, kind, block=0):
    fee = p["cost_bps_per_side"] / 10_000
    edge_cost = math.log((1 - fee) / (1 + fee))
    rebalance = math.log1p(math.expm1(edge_cost) / p["hot_n"])
    twins = [1.0] * p["twin_draws"]
    wins, total, best = 0, 1.0, (-math.inf, None)
    panels = []
    active_days = calendar_days = permutable_years = 0
    for i, yr in enumerate(p["years"]):
        start, stop = C.boundaries(yr)
        if i == len(p["years"]) - 1:
            stop = C.stamp(p["judged_stop"])
        gate = C.Gate(p["lookback_days"])
        on, prefix, mask = False, [0.0], []
        phase = rng.randrange(2 * block) if block else 0
        for d in range(-p["lookback_days"], (stop - start) // 86400):
            sigma = 2 if kind == "volatility_blocks" and (d // 21) % 2 else 1
            if kind == "persistent":
                # State does not depend on the rule; expected premium over phases
                # is zero at every date and exactly zero over each complete cycle.
                drift = edge if (d + phase) % (2 * block) < block else -edge
            else:
                drift = edge if kind == "feedback" and on else 0
            gross_edge = rng.gauss(0, p["calibration_relative_sigma"] * sigma) + drift
            gross_market = rng.gauss(0, p["calibration_market_sigma"] * sigma)
            if d >= 0:
                prefix.append(prefix[-1] + math.log1p(gross_market + gross_edge))
                mask.append(on)
            on = gate.add(gross_edge)
        spells, gaps = C.schedule(mask)
        gain = growth(prefix, spells, gaps, edge_cost, rebalance)
        total *= gain
        wins += i < len(p["years"]) - 1 and gain > 1
        ps, pg = list(spells), [g for g in gaps if g]
        active_days += sum(mask)
        calendar_days += len(mask)
        permutable_years += len(set(ps)) > 1 or len(set(pg)) > 1
        positions = [i for i, g in enumerate(gaps) if g]
        if ps:
            for j in range(len(twins)):
                rng.shuffle(ps)
                rng.shuffle(pg)
                placed = [0] * len(gaps)
                for pos, length in zip(positions, pg):
                    placed[pos] = length
                twins[j] *= growth(prefix, ps, placed, edge_cost, rebalance)
        first = 0
        for j in range(1, len(mask) + 1):
            if j == len(mask) or datetime.fromtimestamp(start + j * 86400, timezone.utc).day == 1:
                local = [v - prefix[first] for v in prefix[first:j + 1]]
                own = growth(local, *C.schedule(mask[first:j]), edge_cost, rebalance)
                if own > best[0]:
                    best = own, (i, first, j)
                first = j
        panels.append((prefix, mask))
    panel, first, end = best[1]
    panels[panel][1][first:end] = [False] * (end - first)
    without = math.prod(growth(prefix, *C.schedule(mask), edge_cost, rebalance)
                        for prefix, mask in panels)
    return C.metrics(total - 1, twins, without - 1, wins, p)["pass"], active_days / calendar_days, permutable_years


def upper95(passes, n):
    # One-sided exact binomial upper limit by inversion.
    lo, hi = passes / n, 1.0
    for _ in range(45):
        mid = (lo + hi) / 2
        cdf = math.fsum(math.comb(n, k) * mid ** k * (1 - mid) ** (n - k)
                        for k in range(passes + 1))
        if cdf > .05:
            lo = mid
        else:
            hi = mid
    return hi


def calibrate(p):
    n = p["calibration_trials"]
    rows = {}
    scenarios = [("iid", 0, 0), ("volatility_blocks", 0, 0)]
    scenarios += [("feedback", bp, 0) for bp in p["calibration_edges_bps"]]
    scenarios += [("persistent", bp, days) for days in p["calibration_block_days"]
                  for bp in p["calibration_edges_bps"]]
    for kind, bp, block in scenarios:
        simulations = [draw(random.Random(p["calibration_seed"] + i), p, bp / 10_000, kind, block)
                       for i in range(n)]
        passes = sum(v[0] for v in simulations)
        key = f"{kind}_{bp}bp" + (f"_{block}d" if block else "")
        rows[key] = {"passes": passes, "trials": n, "rate": passes / n,
                     "upper95": upper95(passes, n),
                     "mean_active_share": math.fsum(v[1] for v in simulations) / n,
                     "mean_permutable_panels": math.fsum(v[2] for v in simulations) / n}
    return {"rows": rows, **release(rows, p)}


def release(rows, p):
    target = f"persistent_{p['calibration_target_bps']}bp_{p['calibration_target_days']}d"
    null_ok = all(rows[k]["upper95"] <= .10 for k in ("iid_0bp", "volatility_blocks_0bp"))
    power_ok = rows[target]["rate"] >= p["calibration_power_floor"]
    return {"unlocked": null_ok and power_ok, "null_ok": null_ok, "power_ok": power_ok, "power_target": target}
