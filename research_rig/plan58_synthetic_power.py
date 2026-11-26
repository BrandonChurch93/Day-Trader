"""Synthetic plan 58 feasibility; this script has no market-data inputs."""
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
import json
from zoneinfo import ZoneInfo

import numpy as np

WORLD_COUNT = 10000
SEED = 582123
START = date(2024, 1, 11)
SPOT_START = date(2016, 1, 1)
LATER_START = date(2023, 7, 1)
END = date(2026, 11, 25)
ET = ZoneInfo("America/New_York")
FULL_CLOSURES = frozenset(map(date.fromisoformat, """
2024-01-15 2024-02-19 2024-03-29 2024-05-27 2024-06-19
2024-07-04 2024-09-02 2024-11-28 2024-12-25
2025-01-01 2025-01-09 2025-01-20 2025-02-17 2025-04-18 2025-05-26
2025-06-19 2025-07-04 2025-09-01 2025-11-27 2025-12-25
2026-01-01 2026-01-19 2026-02-16 2026-04-03 2026-05-25
2026-06-19 2026-07-03 2026-09-07
""".split()))
EARLY_CLOSES = frozenset(map(date.fromisoformat, """
2024-07-03 2024-11-29 2024-12-24
2025-07-03 2025-11-28 2025-12-24
""".split()))


def scheduled_days(start=START):
    return tuple(d for i in range((END - start).days + 1)
                 if (d := start + timedelta(days=i)).weekday() < 5
                 and d not in FULL_CLOSURES and d not in EARLY_CLOSES)


def regime(d):
    ts = datetime.combine(d, time(21), timezone.utc).astimezone(ET)
    return "daylight" if ts.dst() else "standard"


def simulate(days, sigma, rho, cluster):
    later = np.array([d >= LATER_START for d in days])
    groups = [(d - timedelta(days=d.weekday())).toordinal() if cluster == "week"
              else d.year * 12 + d.month for d in days]
    _, starts, idx = np.unique(groups, return_index=True, return_inverse=True)
    sizes = np.diff(np.append(starts, len(days)))
    n = len(days)
    k = len(starts)
    rng = np.random.default_rng(SEED)
    plants = [("net_null", 0.0)] + [
        (f"gross_{gross:g}_cost_{cost:g}", gross - cost)
        for gross in (7, 3.5) for cost in (2, 3.5, 5)
    ]
    out = {name: {"t_only": 0, "all_marks": 0} for name, _ in plants}
    for _ in range(0, WORLD_COUNT, 100):
        common = rng.normal(size=(100, k))[:, idx]
        # t5 divided by its standard deviation gives a finite-variance, heavy-tailed residual.
        student = rng.standard_t(df=5, size=(100, n)) / (5 / 3) ** 0.5
        noise = sigma * (rho**0.5 * common + (1 - rho)**0.5 * student)
        noise_by_group = np.add.reduceat(noise, starts, axis=1)
        later_noise_mean = noise[:, later].mean(axis=1)
        noise_mean = noise_by_group.sum(axis=1) / n
        se = (k / (k - 1) * ((noise_by_group - noise_mean[:, None] * sizes) ** 2)
              .sum(axis=1)) ** 0.5 / n
        for key, net in plants:
            mean = noise_mean + net
            clear = (se > 0) & (mean >= 2.0 * se)
            out[key]["t_only"] += int(clear.sum())
            out[key]["all_marks"] += int((clear & (later_noise_mean + net > 0)).sum())
    return {"two_hour_sigma_bp": sigma, "cluster_shock_share": rho, "cluster": cluster,
            "cluster_count": k, "counts": out}


def main():
    sessions = scheduled_days()
    all_days = tuple(SPOT_START + timedelta(days=i) for i in range((END - SPOT_START).days + 1))
    specs = ((80, 0.10, "week"), (80, 0.05, "month"), (60, 0.10, "week"),
             (100, 0.10, "week"), (80, 0.10, "month"))
    routes = {"all_days": all_days, "weekdays": tuple(d for d in all_days if d.weekday() < 5)}
    print(json.dumps({"start": str(SPOT_START), "end": str(END), "later_start": str(LATER_START),
                      "ibit_shown_only": {"dates": len(sessions),
                                          "regimes": dict(Counter(map(regime, sessions)))},
                      "worlds_per_case": WORLD_COUNT, "seed": SEED, "routes": {
                          key: {"dates": len(days), "later_dates": sum(d >= LATER_START for d in days),
                                "cases": [simulate(days, *spec) for spec in specs]}
                          for key, days in routes.items()
                      }}, indent=2))


if __name__ == "__main__":
    main()
