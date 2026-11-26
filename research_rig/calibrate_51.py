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


def uniform_gaps(spells, cash_days, rng):
    """Uniform weak composition after reserving one day per interior gap."""
    k = len(spells)
    if not k:
        return [cash_days]
    slack = cash_days - (k - 1)
    if slack == 0:
        return [0] + [1] * (k - 1) + [0]
    bars = [-1, *sorted(rng.sample(range(slack + k), k)), slack + k]
    return [b - a - 1 + (0 < i < k) for i, (a, b) in enumerate(zip(bars, bars[1:]))]


def draw(rng, p, edge, kind, block=0, uniform=None):
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
        cash_days = len(mask) - sum(spells)
        active_days += sum(mask)
        calendar_days += len(mask)
        permutable_years += (bool(ps) and cash_days > len(ps) - 1 if uniform is not None
                             else len(set(ps)) > 1 or len(set(pg)) > 1)
        positions = [i for i, g in enumerate(gaps) if g]
        if ps:
            for j in range(len(twins)):
                rng.shuffle(ps)
                rng.shuffle(pg)
                if uniform is None:
                    placed = [0] * len(gaps)
                    for pos, length in zip(positions, pg):
                        placed[pos] = length
                    twins[j] *= growth(prefix, ps, placed, edge_cost, rebalance)
                else:
                    # Keep advancing the original shuffle RNG above so all
                    # simulated prices and gates match the original run exactly.
                    placed = uniform_gaps(spells, cash_days, uniform)
                    twins[j] *= growth(prefix, spells, placed, edge_cost, rebalance)
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
    result = C.metrics(total - 1, twins, without - 1, wins, p)
    return result["pass"], active_days / calendar_days, permutable_years, result["marks"]


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


def calibrate(p, *, uniform=False):
    n = p["calibration_trials"]
    rows = {}
    scenarios = [("iid", 0, 0), ("volatility_blocks", 0, 0)]
    if not uniform:
        scenarios += [("feedback", bp, 0) for bp in p["calibration_edges_bps"]]
    scenarios += [("persistent", bp, days) for days in p["calibration_block_days"]
                  for bp in p["calibration_edges_bps"]]
    for kind, bp, block in scenarios:
        simulations = []
        for i in range(n):
            seed = p["calibration_seed"] + i
            placement_rng = random.Random(f"plan51-uniform-{seed}") if uniform else None
            simulations.append(draw(random.Random(seed), p, bp / 10_000, kind, block, placement_rng))
        passes = sum(v[0] for v in simulations)
        key = f"{kind}_{bp}bp" + (f"_{block}d" if block else "")
        rows[key] = {"passes": passes, "trials": n, "rate": passes / n,
                     "upper95": upper95(passes, n),
                     "mean_active_share": math.fsum(v[1] for v in simulations) / n,
                     "mean_permutable_panels": math.fsum(v[2] for v in simulations) / n}
        if uniform:
            rows[key]["marks_passed"] = {mark: sum(v[3][mark] for v in simulations)
                                          for mark in simulations[0][3]}
            rows[key]["all_non_twin_passed"] = sum(
                all(v[3][mark] for mark in ("positive_net", "positive_full_years", "without_best_month"))
                for v in simulations)
    if uniform:
        target = f"persistent_{p['calibration_target_bps']}bp_{p['calibration_target_days']}d"
        null_ok = all(rate(rows[k]) <= p["calibration_redesign_null_ceiling"]
                      for k in ("iid_0bp", "volatility_blocks_0bp"))
        power_ok = rate(rows[target]) >= p["calibration_power_floor"]
        return {"rows": rows, "comparison": "uniform_placement", "power_target": target,
                "null_ok": null_ok, "power_ok": power_ok, "unlocked": null_ok and power_ok}
    return {"rows": rows, **release(rows, p)}


def rate(row):
    x, n = row["passes"], row["trials"]
    if type(x) is not int or type(n) is not int or not 0 <= x <= n or n <= 0:
        raise ValueError("invalid calibration counts")
    return x / n


def release(rows, p, *, verify_counts=False):
    target = f"persistent_{p['calibration_target_bps']}bp_{p['calibration_target_days']}d"
    if verify_counts:
        for row in rows.values():
            observed = rate(row)
            if (row["trials"] != p["calibration_trials"] or row["rate"] != observed
                    or row["upper95"] != upper95(row["passes"], row["trials"])):
                raise ValueError("inconsistent calibration record")
    null_ok = all(upper95(rows[k]["passes"], rows[k]["trials"]) <= .10
                  for k in ("iid_0bp", "volatility_blocks_0bp"))
    power_ok = rate(rows[target]) >= p["calibration_power_floor"]
    return {"unlocked": null_ok and power_ok, "null_ok": null_ok, "power_ok": power_ok, "power_target": target}
