"""Plan 70 offline QA. All prices, schedules and returns are invented."""
import json
import math
from collections import Counter

import numpy as np

from sweep_70 import (DAY, DAYS, HALF_INDEX, HOUR, HOURS, STOP, Tape, YEARS,
                      read_hour_rows, rows_bytes, score_signal, sweep, too_thin)


COINS = ["ADA", "BTC", "ETH", "SOL"]


def fake_panel(seed, plant=False, drift=0):
    rng = np.random.default_rng(seed)
    n = len(HOURS)
    shape = (len(COINS), n)
    common = rng.normal(0, .002, n)
    close_incr = rng.normal(0, .004, shape) + common
    gap = rng.normal(drift, .0005, shape)
    if plant:
        # ADA, Mondays through Fridays 09:00 UTC, two completed down hours
        # followed by a rebound after the entry open. Keep all other tapes real-free.
        from sweep_70 import UTC_HOUR, WEEKEND
        ix = np.flatnonzero((UTC_HOUR == 9) & ~WEEKEND & (DAY % 3 != 0))
        close_incr[0, ix - 1] = -.013
        close_incr[0, ix - 2] = -.010
        close_incr[0, ix] = .021
    close_log = np.cumsum(close_incr + gap, axis=1)
    open_log = np.c_[np.zeros(len(COINS)), close_log[:, :-1]] + gap
    o, c = np.exp(open_log) * 100, np.exp(close_log) * 100
    wick = np.exp(rng.uniform(.0001, .004, shape))
    return np.stack((o, np.maximum(o, c) * wick, np.minimum(o, c) / wick,
                     c, rng.lognormal(5, .5, shape)), axis=2)


def wire_rows(rows, suffix):
    for t, row in zip(HOURS, rows):
        yield (f"{int(t) * 1000}," + ",".join(map(repr, map(float, row)))
               + f",{(int(t) + HOUR) * 1000 - 1},0\n").encode()
    yield from suffix


def wire_panel(panel, suffix):
    out = np.empty_like(panel)
    for j, rows in enumerate(panel):
        for i, row in read_hour_rows(wire_rows(rows, suffix)):
            out[j, i] = row
    return out


def power_fixture(config):
    # Fixed schedule, 5 synthetic UTC entry days/week, 1 or 2 trades/day.
    # Invented 45 bp day shock and 65 bp independent ticket shock (79.06 bp SD,
    # same-day correlation .324). Zero true clock drift, no estimated baseline
    # error in this approximation. True edge is after all costs.
    rng = np.random.default_rng(70080)
    days = np.flatnonzero(np.arange(DAYS) % 7 < 5)
    day_ix = np.repeat(days, 1 + (days % 3 == 0))
    day_ids, counts = np.unique(day_ix, return_counts=True)
    half = (day_ids < HALF_INDEX // 24, day_ids >= HALF_INDEX // 24)
    n = len(day_ix)
    marks = config["search_marks"]
    assert not too_thin(n, len(day_ids), [h.sum() for h in half], marks)
    sims, sd_day, sd_ticket = 2048, 45., 65.
    noise = (rng.normal(0, sd_day, (sims, DAYS))[:, day_ix]
             + rng.normal(0, sd_ticket, (sims, n)))
    partial = np.add.reduceat(noise, np.r_[0, np.cumsum(counts)[:-1]], axis=1)

    def needed(loc, t):
        k = counts[loc].sum()
        sums = partial[:, loc]
        m = sums.sum(axis=1) / k
        g = loc.sum()
        se = np.sqrt(g / (g - 1) * ((sums - m[:, None] * counts[loc]) ** 2).sum(axis=1)) / k
        return t * se - m

    trim = n - math.ceil(marks["trim_share"] * n)
    need = np.maximum.reduce([needed(np.ones(len(day_ids), bool), marks["full_t"]),
                              needed(half[0], marks["half_t"]), needed(half[1], marks["half_t"]),
                              -np.partition(noise, trim, axis=1)[:, :trim].mean(axis=1),
                              marks["annual_min"] * YEARS * 10000 / n - noise.mean(axis=1)])

    def grid_mark(q):
        x = math.ceil(float(np.quantile(need, q, method="higher")) * 4) / 4
        return {"true_net_bp": x, "all_mark_pass_fraction": float(np.mean(need <= x))}

    return {"synthetic_trials": sims, "trades": n, "entry_days": len(day_ids),
            "day_shock_sd_bp": sd_day, "ticket_shock_sd_bp": sd_ticket,
            "same_day_corr": sd_day**2 / (sd_day**2 + sd_ticket**2),
            "includes_top_three_selection": False, "half_power": grid_mark(.5),
            "eighty_percent_power": grid_mark(.8)}


def synthetic_main(rules, config):
    marks = config["search_marks"]
    assert not too_thin(200, 100, [40, 60], marks)
    assert too_thin(199, 100, [50, 50], marks)
    assert too_thin(200, 99, [49, 50], marks)
    assert too_thin(200, 100, [39, 61], marks)
    costs = np.array([config["futures_round_trip_bp"][c] for c in COINS])
    plant = fake_panel(70001, plant=True)
    before = wire_panel(plant, [])
    impossible = [f"{STOP * 1000},THIS,WOULD,FAIL,IF,PARSED\n".encode(),
                  f"{(STOP + HOUR) * 1000},1,10000000,1,9999999,9999999,{(STOP + 2 * HOUR) * 1000 - 1}\n".encode()]
    after = wire_panel(plant, impossible)
    base_rows = sweep(COINS, before, rules, costs, config)
    assert rows_bytes(base_rows) == rows_bytes(sweep(COINS, after, rules, costs, config))
    finalists = [r for r in base_rows if r["finalist_rank"]]
    target = next(r for r in rules if r["family"] == "clock_after_move"
                  and r["parameters"]["entry_hour"] == 9
                  and r["parameters"]["day_type"] == "weekday" and r["parameters"]["lag"] == 2
                  and r["side"] == 1 and r["hold_hours"] == 1)
    target_row = next(r for r in base_rows if r["rule"] == target["id"])
    assert target_row["meets_search_marks"] and any(r["family"] == "clock_after_move" for r in finalists)

    cut = HALF_INDEX + 9
    changed = before.copy()
    changed[:, cut:, :4] *= 23
    changed[:, cut:, 4] *= 60
    a, b = Tape(COINS, before), Tape(COINS, changed)
    for rule in rules:
        assert np.array_equal(score_signal(a, rule)[:, :cut + 1],
                              score_signal(b, rule)[:, :cut + 1], equal_nan=True)

    fixture = {**target, "family": "_always_long_fixture"}
    rising = sweep(["BTC"], fake_panel(70302, drift=.012)[1:2], [fixture], costs[1:2], config)[0]
    assert rising["plain_mean"] > 0 and rising["simple_net_annual"] > marks["annual_min"]
    assert rising["paired_day_t"] < marks["full_t"] and not rising["meets_search_marks"]

    # For luck, use the complete gate and registered costs. Also retain the
    # original cost-free raw-t stress, with the same noise paths and no floors.
    null_total = 100
    buyable_zero, ungated_zero, eligible_zero = 0, 0, 0
    thin_crossings, thick_crossings, false_finalists = [], [], []
    ungated = {**config, "funding_adverse_bp_per_hour": 0}
    for seed in range(70100, 70100 + null_total):
        panel = fake_panel(seed)
        judged = sweep(COINS, panel, rules, costs, config)
        false_rows = [r for r in judged if r["finalist_rank"]]
        buyable_zero += not false_rows
        if false_rows:
            false_finalists.append({"seed": seed, "rules": false_rows})
        raw = sweep(COINS, panel, rules, np.zeros(len(COINS)), ungated)
        crosses = [r for r in raw if r["paired_day_t"] is not None and r["paired_day_t"] >= marks["full_t"]]
        ungated_zero += not crosses
        eligible_zero += not any(not r["too_thin"] for r in crosses)
        thin_crossings.extend(r for r in crosses if r["too_thin"])
        thick_crossings.extend(r for r in crosses if not r["too_thin"])
    n_thin = [r["trades"] for r in thin_crossings]
    d_thin = [r["active_days"] for r in thin_crossings]
    print(json.dumps({"planted_target": target_row["rule"],
                      "planted_finalists": [r["rule"] for r in finalists],
                      "post_cutoff_output_bytes_identical": True,
                      "future_signal_prefix_identical_rules": len(rules),
                      "always_long_plain_mean_bp": 1e4 * rising["plain_mean"],
                      "always_long_matched_day_t": rising["paired_day_t"],
                      "null_seeds_with_no_finalist_at_judged_cost": buyable_zero,
                      "null_finalists_at_judged_cost": false_finalists,
                      "cost_free_stress_no_eligible_t_at_mark": eligible_zero,
                      "cost_free_stress_no_ungated_t_at_mark": ungated_zero,
                      "cost_free_stress_thin_crossing_families": dict(Counter(r["family"] for r in thin_crossings)),
                      "cost_free_stress_eligible_crossing_families": dict(Counter(r["family"] for r in thick_crossings)),
                      "cost_free_stress_thin_crossing_trades_range": [min(n_thin), max(n_thin)] if n_thin else [],
                      "cost_free_stress_thin_crossing_days_range": [min(d_thin), max(d_thin)] if d_thin else [],
                      "null_seeds": null_total,
                      "power": power_fixture(config)}, indent=2, sort_keys=True))
    assert buyable_zero >= 95, buyable_zero
