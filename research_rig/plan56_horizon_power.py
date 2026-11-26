"""Price-free horizon and mark calibration on the actual primary filing dates."""
import argparse
import csv
import json
from pathlib import Path
import sys

import numpy as np

WORLDS = 5000
GROSS = {10: 153 * 146 / 199, 20: 153.0}  # bp; 10 is a horizon transfer, not a paper result
SPECS = (
    ("iid", 0.0, 0.0),
    ("issuer_only", 0.15, 0.0),
    ("month_only", 0.0, 0.20),
    ("weak_both", 0.05, 0.05),
    ("central_both", 0.15, 0.20),
    ("stress_both", 0.25, 0.30),
)


def prepare(rows):
    rows = sorted((r for r in rows if r[-1]), key=lambda r: (r[0][:7], r[1], r[0], r[2]))
    ixs = np.unique([r[1] for r in rows], return_inverse=True)[1]
    _, starts, mxs = np.unique([r[0][:7] for r in rows], return_inverse=True, return_index=True)
    return ixs, mxs, starts


def model(ix, mx, starts, sigma, drop, issuer_share, month_share, edges):
    rng = np.random.default_rng(56576)
    # Size-only design information. Clustering shares are guesses, not fitted.
    N, I, M = len(ix), int(ix.max()) + 1, len(starts)
    wi = np.bincount(ix) / N
    wm = np.bincount(mx) / N
    residual = 1 - issuer_share - month_share
    variance = residual / N + issuer_share * (wi @ wi) + month_share * (wm @ wm) + drop / ((1 - drop) * N)
    out = np.zeros((len(edges), 4), dtype=int)
    for left in range(0, WORLDS, 100):
        batch = min(100, WORLDS - left)
        a = rng.standard_normal((batch, I))[:, ix]
        b = rng.standard_normal((batch, M))[:, mx]
        c = rng.standard_normal((batch, N))
        noise = sigma * (issuer_share**0.5 * a + month_share**0.5 * b + residual**0.5 * c)
        placed = rng.random((batch, N)) >= drop
        counts = np.add.reduceat(placed.astype(int), starts, axis=1)
        base = np.add.reduceat(noise * placed, starts, axis=1)
        k = (counts > 0).sum(axis=1)
        n = counts.sum(axis=1)
        centered = base - counts * (base.sum(axis=1) / n)[:, None]
        se = (k / (k - 1) * (centered * centered).sum(axis=1)) ** 0.5 / n
        for j, e in enumerate(edges):
            sums = base + counts * (e / 10000)
            aggregate = sums.sum(axis=1)
            t = aggregate / n >= 2.0 * se
            positive = aggregate > 0
            trimmed = aggregate > sums.max(axis=1)
            refusal = (N - n) * 10 <= N
            out[j] += [t.sum(), (t & positive).sum(), (t & positive & trimmed).sum(), (t & positive & trimmed & refusal).sum()]
    return variance**0.5 * sigma * 10000, out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("private_calendar", type=Path)
    args = p.parse_args()
    with args.private_calendar.open() as f:
        ix, mx, starts = prepare(json.load(f))
    w = csv.writer(sys.stdout)
    w.writerow(("sessions", "case", "issuer_share", "month_share", "paired_sigma", "attrition",
                "true_net_bp", "theoretical_se_bp", "worlds", "t_only", "with_positive",
                "with_best_month_removed", "with_refusal_cap"))
    for h, sigma, opt in ((10, .12, .08), (20, .173, .08 * 2**0.5)):
        edges = [0.0, GROSS[h] - 100, GROSS[h] - 50, GROSS[h] - 133]
        if h == 20:
            edges.append(320 - 100)  # shown only: dissimilar all-purchase microcap event sample
        for name, ri, rm in SPECS:
            scenarios = [(name, sigma, .05), (name + "_low_noise", opt, 0.0)]
            if name == "central_both":
                scenarios.append(("central_both_stress_noise", sigma * 4 / 3, .08))
            for label, s, a in scenarios:
                se, counts = model(ix, mx, starts, s, a, ri, rm, edges)
                for e, row in zip(edges, counts, strict=True):
                    w.writerow((h, label, ri, rm, round(s, 5), a, round(e, 4), round(se, 3), WORLDS, *row))


if __name__ == "__main__":
    main()
