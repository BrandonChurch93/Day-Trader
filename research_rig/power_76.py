"""Plan 76 made-up returns only. No tape, approval or custody code is called."""

import json
from math import sqrt

import numpy as np

from score_76 import config, net


def simulate(cfg):
    settings = cfg["power"]
    rng = np.random.default_rng(settings["seed"])
    worlds, df = settings["worlds"], settings["residual_t_df"]
    rows = []
    for n in settings["trades"]:
        by_year = np.array_split(np.arange(n), settings["years"])
        year = np.concatenate([np.repeat(j, len(k)) for j, k in enumerate(by_year)])
        regime = rng.normal(0, settings["year_sd"], (worlds, settings["years"]))[:, year]
        shocks = rng.standard_t(df, size=(worlds, n)) * sqrt((df - 2) / df)
        random_mean_noise = rng.normal(size=(worlds, cfg["control"]["draws"])) / sqrt(n)
        for sd in settings["residual_sd"]:
            centered = np.clip(shocks * sd, -settings["residual_bound"], settings["residual_bound"]) + regime
            # Approximate matched control book means under the same year mix,
            # with a CLT residual. The real scorer draws full calendar books.
            control = regime.mean(axis=1)[:, None] + random_mean_noise * sd
            for arm, paper in settings["paper_gross"].items():
                for fraction in settings["edge_fractions"]:
                    gross = centered + fraction * paper
                    rank = (gross.mean(axis=1)[:, None] > control).mean(axis=1) > cfg["control"]["beat_share"]
                    for line, bp in cfg["costs_bp"].items():
                        returns = net(gross, bp)
                        avg = returns.mean(axis=1)
                        trim = cfg["trim_per_year"]
                        removed = sum(np.sort(returns[:, indices], axis=1)[:, -trim:].sum(axis=1) for indices in by_year)
                        trim_mean = (returns.sum(axis=1) - removed) / (n - cfg["trim_per_year"] * len(by_year))
                        enough = n >= cfg["min_heldback_trades"]
                        marks = {"positive": avg > cfg["mean_floor"], "beats_random": rank,
                                 "positive_trimmed": trim_mean > cfg["mean_floor"],
                                 "enough_trades": np.full(worlds, enough)}
                        rows.append({"arm": arm, "trades": n, "noise_sd": sd, "paper_fraction": fraction,
                                     "cost_line": line, "marks": {k: float(v.mean()) for k, v in marks.items()},
                                     "all_four": float(np.logical_and.reduce(list(marks.values())).mean())})
    return {"status": "MEASURED_SIMULATION_ONLY", "worlds": worlds, "scenarios": rows}


if __name__ == "__main__":
    print(json.dumps(simulate(config()), sort_keys=True, allow_nan=False))
