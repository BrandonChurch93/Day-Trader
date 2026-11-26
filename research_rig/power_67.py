"""Synthetic-only Plan 67 power screen. Takes no input or file paths."""

import json
import math

import numpy as np


SEED = 67109
WORLDS = 50_000
YEARS = 10
ASSUMED_DAYS_PER_YEAR = 250
TRADING_SESSIONS_PER_YEAR = 252
SYNTHETIC_DAYS_PER_WEEK = 5
ASSUMED_HOLD_SESSIONS = 3.4
BASELINE_DRIFT_BP = 14.7
EDGES_BP = (0.0, 8.4, 16.8, 33.6)
MIN_COUNT = 150
MIN_POS_YEARS = 6
MIN_T = 2.0
MIN_POWER = 0.33


def groups(n):
    rng = np.random.default_rng(SEED)
    per_year = [n // YEARS + (i < n % YEARS) for i in range(YEARS)]
    day = np.concatenate([
        np.sort(rng.choice(ASSUMED_DAYS_PER_YEAR, size=k, replace=False)) + i * ASSUMED_DAYS_PER_YEAR
        for i, k in enumerate(per_year)
    ])
    year = day // ASSUMED_DAYS_PER_YEAR
    _, week = np.unique(day // SYNTHETIC_DAYS_PER_WEEK, return_inverse=True)
    return year, week


def mark_rates(dates, vol, rho):
    sigma_bp = vol * 10_000 * math.sqrt(ASSUMED_HOLD_SESSIONS / TRADING_SESSIONS_PER_YEAR)
    years, week = groups(dates)
    starts = np.flatnonzero(np.r_[True, week[1:] != week[:-1]])
    year_starts = np.flatnonzero(np.r_[True, years[1:] != years[:-1]])
    n_week = len(starts)
    trim = math.ceil(dates * 0.01)
    rng = np.random.default_rng(SEED + 1)
    pass_count = {edge: 0 for edge in EDGES_BP}
    t_count = dict(pass_count)
    for _ in range(WORLDS // 500):
        shocks_week = rng.normal(size=(500, n_week))
        shocks_date = rng.normal(size=(500, dates))
        noise = sigma_bp * (math.sqrt(rho) * shocks_week[:, week] + math.sqrt(1 - rho) * shocks_date)
        centered = noise - np.mean(noise, axis=1, keepdims=True)
        cluster_sums = np.add.reduceat(centered, starts, axis=1)
        se = np.sqrt((n_week / (n_week - 1)) * np.sum(cluster_sums ** 2, axis=1)) / dates
        for edge in EDGES_BP:
            x = noise + edge
            mean = np.mean(x, axis=1)
            t_pass = mean / se >= MIN_T
            t_count[edge] += int(np.sum(t_pass))
            yes = ((dates >= MIN_COUNT) & (mean > 0) & t_pass
                   & (np.mean(np.partition(x, dates - trim, axis=1)[:, :dates - trim], axis=1) > 0)
                   & (np.sum(np.add.reduceat(x, year_starts, axis=1) > 0, axis=1) >= MIN_POS_YEARS)
                   & (np.mean(x + BASELINE_DRIFT_BP, axis=1) > 0))
            pass_count[edge] += int(np.sum(yes))
    return {"assumed_dates": dates, "synthetic_weeks": n_week, "weekly_shock_correlation": rho,
            "published_annual_vol_percent": round(vol * 100, 2), "implied_hold_noise_bp": round(sigma_bp, 4),
            "trim_dates": trim, "scenarios": [
                {"assumed_excess_bp": edge, "passes": pass_count[edge],
                 "pass_rate": pass_count[edge] / WORLDS, "t_mark_rate": t_count[edge] / WORLDS}
                for edge in EDGES_BP
            ]}


def main():
    cases = [(180, 0.1672, 0.25), (180, 0.1554, 0.0), (180, 0.1748, 0.25),
             (164, 0.1672, 0.25), (150, 0.1672, 0.25)]
    print(json.dumps({"seed": SEED, "worlds_per_case": WORLDS, "assumed_hold_sessions": ASSUMED_HOLD_SESSIONS,
                      "assumed_plain_minus_excess_bp": BASELINE_DRIFT_BP, "required_power": MIN_POWER,
                      "central_case_index": 0, "cases": [mark_rates(*case) for case in cases]}, indent=2))


if __name__ == "__main__":
    main()
