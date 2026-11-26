"""Plan 68. Made-up stock and matched-fund excess only. Reads no inputs."""

import math
from pathlib import Path
import json

import numpy as np


SEED = 681213
TRIALS = 30_000
BATCH = 200
QUARTERS = 43
YEARS = 11
HOLD_SESSIONS = 60
MIN_T = 2.0
MIN_POS_YEARS = 7
TRIM_FRACTION = 0.01
GATE = 0.33
SIGMA_BP = 1130.572
ANNOUNCEMENT_SPY_GROSS_BP = -4
MATCHED_STYLE_GROSS_BP = 16
ANNOUNCEMENT_CAPM_GROSS_BP = 88
MIN_STOCK_ROUND_TRIP_BP = 10
# SEC coverage counts, not returns. Row order: acceptance quarter, 2016 Q1 to 2026 Q3.
STRUCTURALLY_USABLE_RELEASES = (
    437, 441, 409, 409, 442, 457, 451, 474, 468, 479, 473, 469,
    450, 460, 456, 503, 496, 493, 494, 488, 379, 376, 355, 305,
    78, 80, 72, 71, 45, 47, 42, 43, 38, 40, 37, 38, 32, 32, 31, 33,
    22, 23, 23,
)
GRID_BP = sorted({ANNOUNCEMENT_SPY_GROSS_BP, ANNOUNCEMENT_SPY_GROSS_BP - MIN_STOCK_ROUND_TRIP_BP,
                  0, MATCHED_STYLE_GROSS_BP - MIN_STOCK_ROUND_TRIP_BP,
                  MATCHED_STYLE_GROSS_BP, 50, ANNOUNCEMENT_CAPM_GROSS_BP - MIN_STOCK_ROUND_TRIP_BP,
                  ANNOUNCEMENT_CAPM_GROSS_BP, 100, 150, 200, 250, 300, 400})


def case(entries, within_quarter_rho, adjacent_shared_rho):
    rng = np.random.default_rng(SEED)
    qcount = np.full(QUARTERS, entries, dtype=int) if isinstance(entries, int) else np.array(entries)
    qstarts = np.r_[0, qcount.cumsum()[:-1]]
    qid = np.repeat(np.arange(QUARTERS), qcount)
    n = int(qcount.sum())
    trim = math.ceil(n * TRIM_FRACTION)
    t_passes = np.zeros(len(GRID_BP), dtype=np.int64)
    all_passes = np.zeros_like(t_passes)
    known = np.array(GRID_BP, dtype=float)[None, :]
    year_start = np.arange(YEARS) * 4
    # Normal shocks are already stock-minus-fund. A common rally of identical
    # exposure on both sides cancels exactly and does not change these arrays.
    # Moving average quarter shocks make adjacent quarters depend on each other.
    adjacent_weight = (0.0 if not adjacent_shared_rho else
                       2 * adjacent_shared_rho / (1 + math.sqrt(1 - 4 * adjacent_shared_rho ** 2)))
    for _ in range(TRIALS // BATCH):
        raw_shared = rng.standard_normal((BATCH, QUARTERS + 1))
        shared = (raw_shared[:, 1:] + adjacent_weight * raw_shared[:, :-1]) / math.hypot(1, adjacent_weight)
        private = rng.standard_normal((BATCH, n))
        noise = SIGMA_BP * (math.sqrt(within_quarter_rho) * shared[:, qid]
                            + math.sqrt(1 - within_quarter_rho) * private)
        qsum = np.add.reduceat(noise, qstarts, axis=1)
        mean_noise = qsum.sum(axis=1) / n
        centered_qsum = qsum - qcount * mean_noise[:, None]
        se = np.sqrt(QUARTERS / (QUARTERS - 1) * (centered_qsum ** 2).sum(axis=1)) / n
        trimmed_noise = np.partition(noise, n - trim, axis=1)[:, :n - trim].mean(axis=1)
        ymean = np.add.reduceat(qsum, year_start, axis=1) / np.add.reduceat(qcount, year_start)
        mean = mean_noise[:, None] + known
        t = mean / se[:, None]
        trimmed = trimmed_noise[:, None] + known > 0
        breadth = (ymean[:, :, None] + known[:, None, :] > 0).sum(axis=1) >= MIN_POS_YEARS
        t_passes += (t >= MIN_T).sum(axis=0)
        all_passes += ((mean > 0) & (t >= MIN_T) & trimmed & breadth).sum(axis=0)
    count_beyond = next((e for e, p in zip(GRID_BP, all_passes) if p / TRIALS >= GATE), None)
    effective_n_if_independent_quarters = float(
        n * n / (within_quarter_rho * (qcount ** 2).sum() + (1 - within_quarter_rho) * n)
    )
    return {
        "entries_per_quarter_assumed": entries,
        "events": n,
        "trim": trim,
        "within_quarter_correlation": within_quarter_rho,
        "adjacent_quarter_shared_shock_correlation": adjacent_shared_rho,
        "effective_n_ignoring_adjacent_overlap": round(effective_n_if_independent_quarters, 4),
        "first_grid_point_reaching_gate_net_bp": count_beyond,
        "grid": [
            {
                "planted_net_bp": e,
                "all_passes": int(p),
                "all_pass_rate": int(p) / TRIALS,
                "t_only_pass_rate": int(tp) / TRIALS,
            } for e, p, tp in zip(GRID_BP, all_passes, t_passes)
        ],
    }


def main():
    released = tuple(max(1, (count + 5) // 10) for count in STRUCTURALLY_USABLE_RELEASES)
    out = {
        "kind": "synthetic_only",
        "seed": SEED,
        "worlds_per_case": TRIALS,
        "calendar_quarters": QUARTERS,
        "years": YEARS,
        "hold_sessions": HOLD_SESSIONS,
        "marks": {"mean_strictly_positive": True, "min_quarter_clustered_t": MIN_T,
                  "trim_top_fraction": TRIM_FRACTION, "trimmed_mean_strictly_positive": True,
                  "min_positive_years": MIN_POS_YEARS},
        "required_power": GATE,
        "published_marginal_excess_noise_proxy_bp": SIGMA_BP,
        "nearest_announcement_spy_proxy_gross_bp": ANNOUNCEMENT_SPY_GROSS_BP,
        "matched_style_benchmark_proxy_gross_bp": MATCHED_STYLE_GROSS_BP,
        "announcement_capm_upper_proxy_gross_bp": ANNOUNCEMENT_CAPM_GROSS_BP,
        "illustrative_min_stock_round_trip_bp": MIN_STOCK_ROUND_TRIP_BP,
        "known_exact_clock_after_cost_market_long_side_bp": None,
        "sec_quarterly_structurally_usable_release_counts": STRUCTURALLY_USABLE_RELEASES,
        "central_case_index": 0,
        "cases": [case(*args) for args in ((50, .50, 0.0), (90, .25, 0.0),
                                          (20, .50, 0.0), (50, .50, .25),
                                          (90, .10, 0.0), (90, .05, 0.0),
                                          (released, .50, 0.0), (released, .25, 0.0),
                                          (released, .05, 0.0))],
    }
    # Deterministic bytes: no stamps, dependencies on real data or machine paths.
    Path(__file__).with_name("POWER_68.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
