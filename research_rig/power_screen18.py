"""Queue 18 synthetic-only, filing-quarter-clustered all-marks power."""
import json
import math
import sys
from pathlib import Path

import numpy as np


SEED = 18214
WORLDS = 30_000
BATCH = 250
GATE = 0.33
GRID = (0, 50, 80.8, 90.8, 100, 125, 150, 150.1, 160.1, 175, 200, 225,
        250, 275, 300, 350, 400, 500, 600, 750, 1000)


def run(counts, years, sigma, rho, adjacent, tail_df):
    rng = np.random.default_rng(SEED)
    quarters = len(counts)
    q = np.repeat(np.arange(quarters), counts)
    active = counts > 0
    k, n = int(active.sum()), int(counts.sum())
    if k < 2 or n < 2:
        raise ValueError("insufficient dated nonempty clusters")
    ends = np.cumsum(counts)
    ycounts = np.bincount(years, weights=counts, minlength=11)
    yends = np.cumsum(ycounts).astype(int)
    fixed = np.array(GRID)[None, :]
    trim = math.ceil(n / 100)
    passes, passes_t = np.zeros(len(GRID), int), np.zeros(len(GRID), int)
    weight = (2 * adjacent / (1 + math.sqrt(1 - 4 * adjacent ** 2))) if adjacent else 0
    for _ in range(WORLDS // BATCH):
        levels = rng.normal(size=(BATCH, quarters + 1))
        shared = (levels[:, 1:] + weight * levels[:, :-1]) / math.hypot(1, weight)
        event = rng.normal(size=(BATCH, n))
        if tail_df:
            event *= np.sqrt((tail_df - 2) / rng.chisquare(tail_df, size=(BATCH, n)))
        paired = sigma * (math.sqrt(rho) * shared[:, q] + math.sqrt(1 - rho) * event)
        # Any common rally on both stock and SPY cancels in the paired score.
        # Check the equality directly too; synthetic means and marks use paired values.
        rally = np.full((1, n), 200.)
        np.testing.assert_allclose((paired + rally) - rally, paired, rtol=5e-16, atol=1e-12)
        csum = np.column_stack((np.zeros(BATCH), paired.cumsum(axis=1)))
        qsum = np.diff(csum[:, np.r_[0, ends]], axis=1)
        means = csum[:, [-1]] / n
        residual_sums = qsum - means * counts
        se = np.sqrt(k / (k - 1) * (residual_sums ** 2).sum(axis=1, keepdims=True)) / n
        t_ok = (means + fixed) >= 2 * se
        trimmed_means = np.partition(paired, n - trim, axis=1)[:, :n - trim].mean(axis=1, keepdims=True)
        ysums = np.diff(csum[:, np.r_[0, yends]], axis=1)
        breadth = (ysums[:, :, None] + ycounts[None, :, None] * fixed[:, None, :] > 0).sum(axis=1) >= 7
        passes_t += t_ok.sum(axis=0)
        passes += ((means + fixed > 0) & t_ok & (trimmed_means + fixed > 0) & breadth).sum(axis=0)
    covariance_units = (1 - rho) * n + rho * (
        (counts ** 2).sum() + 2 * adjacent * counts[:-1] @ counts[1:])
    return {"sigma_paired_bp_assumed": sigma, "within_quarter_rho_assumed": rho,
            "adjacent_quarter_shared_shock_rho_assumed": adjacent, "event_tail_df": tail_df,
            "events": n, "nonempty_quarters": k, "trim_dropped": trim,
            "effective_count_model": round(n * n / covariance_units, 2),
            "first_grid_net_bp_clearing_33pct": next((x for x, p in zip(GRID, passes) if p / WORLDS >= GATE), None),
            "grid": [{"net_bp": x, "all_marks_rate": int(p) / WORLDS, "t_only_rate": int(t) / WORLDS}
                     for x, p, t in zip(GRID, passes, passes_t)]}


def main(path):
    data = json.loads(Path(path).read_text())
    rows = data["quarterly"]
    counts = np.array([r["primary"].get("official_list_common_proxy", 0) for r in rows])
    liberal = np.array([r["primary"].get("liberal_new_share_cusips", 0) for r in rows])
    wider = np.array([r["wider_shown_only"].get("official_list_common_proxy", 0) for r in rows])
    years = np.array([int(r["filing_quarter"][:4]) - 2016 for r in rows])
    out = {"kind": "synthetic_only", "seed": SEED, "worlds_per_case": WORLDS,
           "gate_all_marks": GATE, "minimum_count": 300,
           "chosen_horizon": 63, "shown_only_horizon": 21,
           "exact_published_clock_spy_net_bp": None,
           "published_carhart_proxy_not_spy_bp_per_day": {"63": 2.7, "21": 4.8},
           "published_proxy_gross_linear_bp": {"63": 170.1, "21": 100.8},
           "cost_scenarios_round_trip_bp": [10, 20],
           "published_proxy_cost_adjusted_bp": {"63": [160.1, 150.1], "21": [90.8, 80.8]},
           "primary_quarter_counts": counts.tolist(), "liberal_quarter_counts": liberal.tolist(),
           "marks": {"mean_positive": True, "min_quarter_cr1_t": 2, "drop_top_fraction_ceiling": .01,
                     "trimmed_mean_positive": True, "positive_filing_years_required": 7},
           "identical_joint_rally_bp_checked": 200, "cases": {}}
    for h, s, low, high, adj in ((63, 1500, 1000, 2000, .20), (21, 866, 577, 1155, .05)):
        out["cases"][str(h)] = {
            "central": run(counts, years, s, .20, adj, 5),
            "low_dependence": run(counts, years, s, .05, adj, None),
            "quiet_independent_favorable": run(counts, years, low, 0, 0, None),
            "same_five_liberal_upper_count_central_noise": run(liberal, years, s, .20, adj, 5),
            "no_2026q4_central_noise": run(np.r_[counts[:-1], 0], years, s, .20, adj, 5),
            "noisy_dependent": run(counts, years, high, .35, adj, 5),
        }
    # Same design, but this is Table IA.XX's own broad-list delayed long-side
    # value. It happens to equal the five-name buy-and-hold number numerically.
    out["wider_table_i_shown_only"] = {
        "quarters": wider.tolist(),
        "horizon": 63,
        "delayed_daily_rebalanced_gross_carhart_bp_per_day": 2.7,
        "published_table": "IA.XX B, printed page 52",
        "delayed_buy_hold_gross_carhart_bp_per_day": None,
        "exact_published_clock_spy_net_bp": None,
        "linear_proxy_after_cost_bp": [160.1, 150.1],
        "cases": {
            "central": run(wider, years, 1500, .20, .20, 5),
            "low_dependence": run(wider, years, 1500, .05, .20, None),
            "quiet_independent_favorable": run(wider, years, 1000, 0, 0, None),
            "no_2026q4_central_noise": run(np.r_[wider[:-1], 0], years, 1500, .20, .20, 5),
            "noisy_dependent": run(wider, years, 2000, .35, .20, 5),
        },
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
