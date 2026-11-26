"""Counts-only maximum participation and synthetic cluster power for Plan 46."""
from collections import Counter
from math import sqrt
from random import Random

import common_46 as C
import score_46 as S


def mde(groups, threshold, seed=460083, draws=20000):
    # For independent Normal date means, t=(Z+delta*sqrt(G))/sqrt(chi2/(G-1)).
    # The 80th percentile of the required delta solves for 80% crossing probability.
    rng = Random(seed)
    values = sorted((threshold * sqrt(rng.gammavariate((groups - 1) / 2, 2) / (groups - 1))
                     - rng.gauss(0, 1)) / sqrt(groups) for _ in range(draws))
    return values[int(0.80 * draws)]


def counts(holds, skips):
    for leg, picks in holds.items():
        cluster = Counter(r[1] for r in picks)
        eff = len(picks)**2 / sum(v * v for v in cluster.values()) if cluster else 0
        print(f"{leg}: {len(picks)} planned; {len(cluster)} posting dates; max cluster {max(cluster.values(), default=0)};"
              f" effective dates at perfect within-date correlation {eff:.2f}; skips {skips[leg]}")


def main():
    cfg = C.config(S.read_config((S.REPO / S.CONFIG).read_bytes()))
    rows = C.docket(S.parse((S.REPO / S.DOCKET).read_bytes()), cfg)
    holds, skips = C.planned(rows, cfg)
    print(f"docket {len(rows)}; posting dates {len({r[0] for r in rows})}; coins {len({r[2] for r in rows})}")
    counts(holds, skips)
    for n in sorted({min(cfg["min_dates"].values()), max(cfg["min_dates"].values()), 35}
                    | {len({r[1] for r in picks}) for picks in holds.values() if len({r[1] for r in picks}) > 1}):
        effect = mde(n, float(cfg["min_t"]))
        print(f"{n:2} equal independent posting dates: t>= {cfg['min_t']} needs {effect:.3f} date SD for 80% power;"
              f" {effect * 5:.2f} pp at illustrative 5 pp date SD")
    print("Synthetic calibration for the paired t mark only, not the probability of all marks passing.")


if __name__ == "__main__":
    main()
