"""Compare the fixed ±600 bp and plain t marks using aggregate placebo inputs."""
import argparse
import json
from math import ceil, erf, sqrt
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
TRIALS, SEED, SCHEDULE_DRAWS = 6000, 61002, 1024
PAIR_FLOOR, YEARS_FLOOR, T_FLOOR, CAP = 250, 7, 2, 600
TAIL_SHARE = 0.05
PLACEMENTS = (0.80, 0.70)
MULTIPLES = (1.0, 1.5, 2.0)
EDGES = (0, 15, 30, 50)
MAD_MULTIPLIER = 1.482602218505602


def fit_scales(sd, scaled_mad):
    # Centered two-normal scale mixture: calibrate the population absolute
    # median and second moment, rather than declaring the full SD to be a bell.
    target = scaled_mad / MAD_MULTIPLIER
    if not 0 < target or not 0 < scaled_mad < sd:
        raise ValueError("these aggregates cannot fit a centered scale mixture")
    def broad(calm):
        return sqrt((sd**2 - (1 - TAIL_SHARE) * calm**2) / TAIL_SHARE)

    lo, hi = 0.0, sd
    for _ in range(80):
        mid = (lo + hi) / 2
        cdf = ((1 - TAIL_SHARE) * erf(target / (sqrt(2) * mid)) +
               TAIL_SHARE * erf(target / (sqrt(2) * broad(mid))))
        if cdf > 0.5:
            lo = mid
        else:
            hi = mid
    calm = (lo + hi) / 2
    return calm, broad(calm)


def candidate_schedule(data):
    groups = [(j, int(size)) for j, (_, sizes) in enumerate(sorted(data["ex_date_cluster_size_counts_by_year"].items()))
              for size, n in sorted(sizes.items()) for _ in range(n)]
    sizes = np.array([n for _, n in groups])
    group = np.repeat(np.arange(len(groups)), sizes)
    year = np.repeat([j for j, _ in groups], sizes)
    if len(group) != data["terminal_counts"]["price_blind_upper_bound"] or len(groups) != data["distinct_ex_dates"]:
        raise ValueError("inconsistent aggregate schedule")
    return group, year


def fit_cluster_share(group, row, rng):
    # Observed measure is the between-group sum of squares divided by total
    # sum of squares. Even iid values allocate about (G-1)/(N-1) there.
    # Fit the ratio of expected sums of squares, using three placebo slots
    # per contributor and uniformly removing unused slots. The measured subset
    # supplies a count only, so calendar composition is itself simulated.
    m, n = row["events_contributing"], row["placebo_observations"]
    share = row["between_ex_date_variance_share"]
    if not 0 < m <= len(group) or not m <= n <= 3*m or not 0 <= share <= 1:
        raise ValueError("invalid cluster targets")
    group_counts, leverage, max_size = [], [], 0
    for _ in range(SCHEDULE_DRAWS):
        candidates = rng.choice(len(group), m, replace=False) if m < len(group) else np.arange(len(group))
        slots = np.repeat(group[candidates], 3)
        if n < len(slots):
            slots = rng.choice(slots, n, replace=False)
        ns = np.bincount(slots)
        group_counts.append(np.count_nonzero(ns))
        leverage.append((np.dot(ns, ns) - n) / n)
        max_size = max(max_size, int(ns.max()))
    g, a = float(np.mean(group_counts)), float(np.mean(leverage))
    effective = (share * (n - 1) - (g - 1)) / (n - g - a * (1 - share))
    # Draw the regime once per ex-date cluster. Because the same scale
    # multiplies every member, it does not attenuate the correlation.
    if not -1 / (max_size - 1) <= effective <= 1:
        raise ValueError("target between-date share is infeasible with this mixture")
    reconstructed = (g - 1 + effective * (n - g - a)) / (n - 1 - effective * a)
    return effective, (g - 1) / (n - 1), reconstructed


def sample_noise(group, calm, broad, rho, rng):
    z = rng.standard_normal(len(group))
    n = np.bincount(group)
    m = np.bincount(group, weights=z)[group] / n[group]
    z = sqrt(1 - rho) * (z - m) + np.sqrt(1 + (n[group] - 1) * rho) * m
    return z * np.where(rng.random(len(n)) < TAIL_SHARE, broad, calm)[group]


def t_pass(values, group, n_by_group, g):
    n = len(values)
    avg = float(np.mean(values))
    if avg <= 0 or g < 2:
        return False
    delta = np.bincount(group, weights=values, minlength=len(n_by_group)) - n_by_group * avg
    variance = (g / ((g - 1) * n * n)) * np.dot(delta, delta)
    return bool(variance > 0 and avg**2 >= T_FLOOR**2 * variance)


def passes(values, group, year, n_by_group, g):
    n = len(values)
    if float(np.mean(values)) <= 0 or np.count_nonzero(np.bincount(year, weights=values) > 0) < YEARS_FLOOR:
        return False, False
    kept = n - ceil(n / 100)
    if float(np.mean(np.partition(values, kept-1)[:kept])) <= 0:
        return False, False
    return (t_pass(values, group, n_by_group, g),
            t_pass(np.clip(values, -CAP, CAP), group, n_by_group, g))


def case(group, year, eligible, row, seed):
    calm, broad = fit_scales(row["sample_sd_bps"], row["mad_scaled_bps"])
    rho, iid_share, reconstructed = fit_cluster_share(group, row, np.random.default_rng(seed+1))
    by_place = {}
    for probability in PLACEMENTS:
        rng = np.random.default_rng(seed)
        acc = np.zeros((len(MULTIPLES), len(EDGES), 2), dtype=int)
        count_hits = placed_total = 0
        for _ in range(TRIALS):
            which = rng.choice(len(group), eligible, replace=False) if eligible < len(group) else np.arange(len(group))
            which = which[rng.random(eligible) < probability]
            n = len(which)
            placed_total += n
            if n < PAIR_FLOOR:
                continue
            count_hits += 1
            g_ids, y_ids = group[which], year[which]
            n_by_group = np.bincount(g_ids)
            g = np.count_nonzero(n_by_group)
            noise = sample_noise(g_ids, calm, broad, rho, rng)
            for i, multiple in enumerate(MULTIPLES):
                for j, edge in enumerate(EDGES):
                    raw, winsor = passes(multiple * noise + edge, g_ids, y_ids, n_by_group, g)
                    acc[i, j, 0] += raw
                    acc[i, j, 1] += winsor
        if np.any(acc[:, 0, :] > TRIALS // 10):
            raise ValueError("simulated zero-edge all-mark pass rate exceeds 10%")
        by_place[str(probability)] = dict(mean_placed=placed_total/TRIALS, count_mark_hits=count_hits, counts={
            str(m): dict(plain_t=acc[i, :, 0].tolist(), winsor_t=acc[i, :, 1].tolist()) for i, m in enumerate(MULTIPLES)})
    return dict(candidate_count=eligible, calm_sd_bps=calm, rare_sd_bps=broad,
                date_correlation=rho, iid_between_share=iid_share, fitted_between_share=reconstructed,
                noise_sd_bps={str(m): row["sample_sd_bps"]*m for m in MULTIPLES}, by_placement=by_place)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    load = lambda n: json.loads((ROOT / n).read_bytes())
    group, year = candidate_schedule(load("COUNT_61.json"))
    all_rows, liquid = load("PLACEBO_61.json"), load("PLACEBO_LIQUID_61.json")
    m = liquid["liquidity_subset_events"]
    if not liquid["events_contributing"] <= m <= len(group):
        raise ValueError("inconsistent subset count")
    data = dict(plan=61, ledger=203, queue=105, trials=TRIALS, seed=SEED, schedule_draws=SCHEDULE_DRAWS,
                tail_probability=TAIL_SHARE, edge_bps=EDGES, evidence_t=T_FLOOR, winsor_cap_bps=CAP,
                pair_floor=PAIR_FLOOR, positive_years_floor=YEARS_FLOOR, trim_top_percent=1,
                full=case(group, year, len(group), all_rows, SEED),
                liquid=case(group, year, m, liquid, SEED+2))
    blob = json.dumps(data, sort_keys=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(blob, encoding="utf-8")
    else:
        sys.stdout.write(blob)


if __name__ == "__main__":
    main()
