"""Doc 117 power only. Reads two date-only calendars, no market inputs."""

from datetime import date, timedelta
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
AS_OF = date(2026, 11, 26)
YEARS = tuple(range(2016, 2027))
WORLDS = 50_000
SEED = 142676869
GATE = 0.33
YEAR_RHO = 0.02
BREADTH = 7
MIN_T = 2.0


def calendars():
    # calendar_25 stops Nov 24. Nov 25 was the last session before Thanksgiving.
    sessions = [date.fromisoformat(d) for d in
                json.loads((ROOT / "calendar_25.json").read_text())["sessions"]]
    sessions.append(date(2026, 11, 25))
    assert sessions[0] == date(2016, 1, 4) and len(sessions) == len(set(sessions))
    sessions = [d for d in sorted(sessions) if d <= AS_OF]
    turns = {(d.year, d.month): d for d in sessions}
    ends = [d for d in turns.values() if (d.year, d.month) < (AS_OF.year, AS_OF.month)]
    expiry = [date.fromisoformat(x["expiration"]) for x in
              json.loads((ROOT / "calendar_66.json").read_text())["expirations"]]
    expiry = [d for d in expiry if d <= AS_OF]
    assert all(d in sessions for d in expiry + ends)
    assert len(ends) == 130 and len(expiry) == 131
    # Do not infer actual QQQ triggers. Evenly spaced proxy dates at 22/year,
    # with a prorated 2026 and at most one assumed trade per chosen week.
    model = []
    for y in YEARS:
        weeks = {}
        for d in sessions:
            if d.year == y and d < sessions[-1]:
                weeks.setdefault(d - timedelta(days=d.weekday()), d)
        weeks = list(weeks.values())
        count = round(22 * len(weeks) / 52) if y == AS_OF.year else 22
        model.extend(weeks[i * len(weeks) // count] for i in range(count))
    return sessions, model, expiry, ends


def simulate(dates, min_count, sigma, profiles, headline, seed_offset):
    n = len(dates)
    year = np.array([d.year - YEARS[0] for d in dates])
    starts = np.flatnonzero(np.r_[True, year[1:] != year[:-1]])
    k = len(starts)
    trim = math.ceil(0.01 * n)
    year_counts = np.bincount(year)
    n_eff = n * n / (n + YEAR_RHO * np.sum(year_counts * (year_counts - 1)))
    rng = np.random.default_rng(SEED + seed_offset)
    gross = {name: np.broadcast_to(amount, (n,)) for name, amount, _, _ in profiles}
    marks = {name: np.zeros(4, dtype=int) for name, _, _, _ in profiles}
    hurdle_rates = np.zeros(101, dtype=int)
    grid = np.arange(101) * (sigma / 100)

    for _ in range(WORLDS // 500):
        noise = sigma * (math.sqrt(YEAR_RHO) * rng.standard_normal((500, k))[:, year]
                         + math.sqrt(1 - YEAR_RHO) * rng.standard_normal((500, n)))
        for name, _, cost, shared_drift in profiles:
            # In the shared-rally case the same +50 bp goes into both legs.
            x = (noise + gross[name] + shared_drift) - (cost + shared_drift)
            avg = x.mean(axis=1)
            by_year = np.add.reduceat(x, starts, axis=1)
            centered = by_year - avg[:, None] * year_counts
            se = np.sqrt(k / (k - 1) * np.sum(centered ** 2, axis=1)) / n
            trimmed = np.partition(x, n - trim, axis=1)[:, :n - trim].mean(axis=1)
            breadth = (by_year > 0).sum(axis=1) >= BREADTH
            passed = (avg > 0, avg >= MIN_T * se, trimmed > 0, breadth)
            marks[name] += [np.count_nonzero(passed[1]), np.count_nonzero(passed[2]),
                            np.count_nonzero(passed[3]),
                            np.count_nonzero(np.logical_and.reduce(passed)) if n >= min_count else 0]
            if name == "no_edge":
                # A constant per-date lift leaves clustered SE unchanged.
                # The seventh-largest yearly mean must also rise strictly above zero.
                y_lift = -np.partition(by_year / year_counts, k - BREADTH, axis=1)[:, k - BREADTH]
                needed = np.maximum.reduce([-avg, MIN_T * se - avg, -trimmed, y_lift])
                if n >= min_count:
                    hurdle_rates += (grid[None, :] > needed[:, None]).sum(axis=0)

    scenarios = {}
    for name, _, cost, shared_drift in profiles:
        net = float(np.mean(gross[name])) - cost
        t, trimmed, breadth, all_five = (int(v) for v in marks[name])
        scenarios[name] = dict(
            gross_bp=round(net + cost, 4), cost_bp=cost, net_bp=round(net, 4),
            common_rally_bp=shared_drift,
            quick_signal_sq=round(float(n_eff * (max(net, 0) / sigma) ** 2), 4),
            t_mark=t / WORLDS, trim_mark=trimmed / WORLDS, breadth_mark=breadth / WORLDS,
            all_five=all_five / WORLDS)
    first = np.flatnonzero(hurdle_rates / WORLDS >= GATE)
    cost = next(cost for name, _, cost, _ in profiles if name == "no_edge")
    return dict(n=n, year_counts=year_counts.tolist(), min_count=min_count,
                count_mark=n >= min_count, n_eff=round(float(n_eff), 4),
                assumed_sd_bp=round(sigma, 4), trim_n=trim, headline=headline,
                first_33_pct_net_grid_bp=round(float(grid[first[0]] - cost), 4) if len(first) else None,
                scenarios=scenarios)


def main():
    sessions, model, expiry, ends = calendars()
    seasons = [d for d in ends if d.month in (6, 7, 12)]
    results = {
        "as_of_boise": AS_OF.isoformat(), "seed": SEED, "worlds": WORLDS,
        "gate": GATE, "min_t": MIN_T, "positive_years_required": BREADTH,
        "cluster": "calendar year", "within_year_shock_correlation": YEAR_RHO,
        "calendar_counts": {
            "overnight_windows_ceiling_to_cutoff": len(sessions) - 1,
            "qqq_three_down_closes_actual": None, "qqq_modeled": len(model),
            "opex_completed": len(expiry), "opex_full_2016_2026": 12 * len(YEARS),
            "opex_completed_from_dec_2022": sum(d >= date(2022, 12, 1) for d in expiry),
            "muni_month_ends_completed": len(ends), "muni_month_ends_full_2016_2026": 12 * len(YEARS),
            "muni_season_months_completed": len(seasons), "muni_season_months_full_2016_2026": 3 * len(YEARS),
            "muni_season_month_counts_jun_jul_dec": [sum(d.month == m for d in seasons) for m in (6, 7, 12)],
        },
        "row_67": simulate(model, 100, 47.0, [
            ("no_edge", 0, 10, 0), ("shared_rally", 0, 10, 50),
            ("qqq_three_down_net", 14, 10, 0),
        ], "qqq_three_down_net", 67),
        "row_67_wider_sd": simulate(model, 100, 94.0, [
            ("no_edge", 0, 10, 0), ("qqq_three_down_net", 14, 10, 0),
        ], "qqq_three_down_net", 67),
        "row_68": simulate(expiry, 100, 200.0, [
            ("no_edge", 0, 4, 0), ("shared_rally", 0, 4, 50),
            ("legacy_spy_20bp_no_benchmark", 20, 4, 0),
            ("legacy_spy_20bp_if_already_net", 20, 0, 0),
            ("legacy_index_30bp_no_benchmark", 30, 4, 0),
            ("legacy_index_30bp_low_cost", 30, 2, 0),
            ("modern_spy_minus_regular_week", -36, 4, 0),
            ("modern_index_minus_other", -65, 4, 0),
        ], "legacy_index_30bp_no_benchmark", 68),
        "row_69_month_end": simulate(ends, 100, 568 / math.sqrt(252), [
            ("no_edge", 0, 4, 0), ("shared_rally", 0, 4, 50),
        ], "no_edge", 69),
        "row_69_season": simulate(seasons, 24, 568 / math.sqrt(12), [
            ("no_edge", 0, 4, 0), ("shared_rally", 0, 4, 50),
            ("repeat_selected_index_months", [{6: 0, 7: 66, 12: 56}[d.month] for d in seasons], 4, 0),
        ], "repeat_selected_index_months", 70),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
