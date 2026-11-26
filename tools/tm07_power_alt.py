"""TM07 power of the registered weekly mark and the lead's alternative mark, by simulation (ledger 198).

Noise: the TM06 swing week-to-week spread of weekly net differences between two arms on the same week.
TM06 has no paired scout/no-scout arms, so the proxy is every pair of the seven TM06 swing models
(a to f and g) on the same four weeks, at 1x and the 12 bp main fee. Each pair's differences are
centred on the pair mean; the pooled standard deviation sets the normal model, and the centred
values themselves are resampled for the second model. A true weekly edge (percentage points) is added.

Registered mark: 3 of 3 screen weeks won and at least 16 of 20 weeks won.
Alternative mark: one-sided paired t of at least 2 on the 20 weekly differences, at least 12 of 20
weeks won, and a positive mean after dropping the best week. Shown with and without the screen gate.
Weeks are independent draws; the chained-gain lines are not modelled, so all figures are upper bounds.
Writes the table to the given Markdown file; prints only the file name.
"""
import hashlib, itertools, json, math, random, sys
from pathlib import Path

NOTES = Path("/home/user/workspace/rig/tm_notes")
PINS = {"results_tm06_six_fast.json": "e50d82af23f731158bee11eaebbd0ed367fb56ebeeec41cdfdec87123cb35412",
        "results_tm06_g.json": "cd49fb4c86a74f02bd24866f18c3a07b5508a79e3edf32d04aa5a130aa2fdef5"}
EDGES = (0.0, 0.5, 1.0, 2.0, 3.0)
N, SCREEN, DRAWS, SEED = 20, 3, 100_000, 1


def weekly():
    out = {}
    for f, pin in PINS.items():
        b = (NOTES / f).read_bytes()
        if hashlib.sha256(b).hexdigest() != pin:
            sys.exit(f"refused: {f} differs from its pin")
        for sid, s in json.loads(b)["scores"].items():
            if sid.startswith("TM06-S-"):
                arm, week = sid.split("-")[2], sid.split("-")[3]
                out.setdefault(arm, {})[week] = s["by_multiple"]["1x"]["12"]["model"]["final_gain_pct"]
    return out


def residuals(g):
    res = []
    for a, b in itertools.combinations(sorted(g), 2):
        weeks = sorted(set(g[a]) & set(g[b]))
        d = [g[a][w] - g[b][w] for w in weeks]
        m = sum(d) / len(d)
        k = math.sqrt(len(d) / (len(d) - 1))
        res += [(x - m) * k for x in d]
    return res


def marks(d):
    wins = sum(x > 0 for x in d)
    screen = all(x > 0 for x in d[:SCREEN])
    m = sum(d) / N
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (N - 1))
    t = m / (sd / math.sqrt(N)) if sd > 0 else (math.inf if m > 0 else -math.inf)
    drop = (sum(d) - max(d)) / (N - 1)
    alt = t >= 2 and wins >= 12 and drop > 0
    return screen and wins >= 16, alt, screen and alt


def power(draw, edge, rng):
    c = [0, 0, 0]
    for _ in range(DRAWS):
        r = marks([edge + draw(rng) for _ in range(N)])
        for i in range(3):
            c[i] += r[i]
    return [100 * x / DRAWS for x in c]


def main():
    out = Path(sys.argv[1])
    res = residuals(weekly())
    sd = math.sqrt(sum(x * x for x in res) / len(res))
    models = (("normal", lambda r: r.gauss(0, sd)), ("resampled", lambda r: r.choice(res)))
    lines = [f"Noise: pooled standard deviation of the weekly net difference between two TM06 swing arms on the same week, {sd:.2f} percentage points, from {len(res)} centred pair-week values (7 arms, 21 pairs, 4 weeks, 1x, 12 bp). {DRAWS:,} simulated 20-week sets per cell, seed {SEED}.", "",
             "| Noise model | True weekly edge (pp) | Registered: 3 of 3 screen and 16 of 20 | Alternative: t at least 2, 12 of 20, mean without best week above 0 | Alternative with the 3 of 3 screen gate |",
             "|---|---:|---:|---:|---:|"]
    for name, draw in models:
        for e in EDGES:
            rng = random.Random(f"{SEED}:{name}:{e}")
            p = power(draw, e, rng)
            lines.append(f"| {name} | {e:.1f}{' (null)' if e == 0 else ''} | {p[0]:.2f}% | {p[1]:.2f}% | {p[2]:.2f}% |")
    out.write_text("\n".join(lines) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
