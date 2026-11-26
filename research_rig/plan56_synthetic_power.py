"""Synthetic paired net returns on the filing calendar; never loads market data."""
import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import random

WORLDS = 5000


def clustered_var(groups, mean, n):
    k = len(groups)
    if k <= 1:
        return float("inf")
    return k / (k - 1) * sum((s - mean * c) ** 2 for s, c in groups.values()) / (n * n)


def passes(recs, effects):
    issuer = defaultdict(lambda: [0.0, 0])
    month = defaultdict(lambda: [0.0, 0])
    joint = defaultdict(lambda: [0.0, 0])
    total = 0.0
    for (i, m), x in recs:
        total += x
        for group in (issuer[i], month[m], joint[i, m]):
            group[0] += x
            group[1] += 1
    n = len(recs)
    if n < 3 or len(issuer) < 2 or len(month) < 2:
        return []
    mu = total / n
    vi, vm, vj = (clustered_var(g, mu, n) for g in (issuer, month, joint))
    v = max(vi, vm, vi + vm - vj)
    hurdle = 2.0 * math.sqrt(v)
    return [bp for bp in effects if mu + bp / 10000 >= hurdle
            and total + n * (bp / 10000) > 0
            and total + n * (bp / 10000) > max(s + k * (bp / 10000) for s, k in month.values())]


def model(labels, sigma, attrition, seed):
    # Positive same-issuer and same-calendar dependence. Trading noise is not sampled.
    rng = random.Random(seed)
    individual = math.sqrt(1 - 0.15 - 0.20)
    issuers = sorted({i for i, _ in labels})
    months = sorted({m for _, m in labels})
    effects = [0, 25, 50, 100]
    outcome = Counter()
    for _ in range(WORLDS):
        issuer = {i: rng.gauss(0, 1) for i in issuers}
        by_month = {m: rng.gauss(0, 1) for m in months}
        paths = [
            ((i, m), sigma * (math.sqrt(0.15) * issuer[i] +
                              math.sqrt(0.20) * by_month[m] +
                              individual * rng.gauss(0, 1)))
            for i, m in labels
            if rng.random() >= attrition
        ]
        outcome.update(passes(paths, effects))
    return {bp: outcome[bp] for bp in effects}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("private_calendar", type=Path)
    args = parser.parse_args()
    with args.private_calendar.open() as handle:
        rows = json.load(handle)
    for name, selected in (
        ("all primary candidates, optimistic clock coverage", rows),
        ("primary candidates with exact trigger clock", [r for r in rows if r[-1]]),
    ):
        labels = [(r[1], r[0][:7]) for r in selected]
        print(name, len(labels), len(set(i for i, _ in labels)), len(set(m for _, m in labels)))
        if name.startswith("primary") and len(selected) == len(rows):
            print("Same docket as optimistic case; see preceding results.")
            continue
        for k, (sigma, drop) in enumerate([(0.08, 0.0), (0.12, 0.05), (0.16, 0.10)]):
            print(f"{sigma=:.2f} {drop=:.2f} out of {WORLDS}", model(labels, sigma, drop, 56730 + k))


if __name__ == "__main__":
    main()
