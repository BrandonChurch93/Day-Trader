"""Plan 74 power screen on made-up returns only. No market data, no file input, no network.

Each made-up world has n signals spread evenly over the five design years (2017 to 2021, 252 sessions a year),
on n / signals_per_day distinct entry days. A signal's excess return over the market fund is
    mean + day shock (shared by the signals of one entry day) + own shock,
both shocks Student t with 3 degrees of freedom (fat tails), scaled so the total SD is the stated noise and the
day shock carries the stated share of variance. Every design-year mark of `replay_74_plan` is applied:
mean above zero and at least the mean floor, day-clustered t at least the t mark, positive in at least 4 of 5
years, positive mean after removing the top 1% of signals, at least 150 signals on at least 100 entry days.
Power is the share of worlds that pass every mark. A second column drops only the mean floor, to show its effect.
Settings are read from `replay_74_plan` in config/thresholds.yaml.
Run: python3 research_rig/power_74.py > /tmp/power_74.txt  (prints a markdown table)."""
import json, math, pathlib, numpy as np

def _plan():
    lines = (pathlib.Path(__file__).resolve().parents[1] / "config" / "thresholds.yaml").read_text().splitlines()
    i = lines.index("replay_74_plan:")
    return json.loads(lines[i + 1].split("value:", 1)[1])

_P = _plan(); _M = _P["marks"]; _W = _P["power"]
MARKS = dict(mean_floor=_M["mean_floor"], t=_M["min_t"], years_pos=_M["years_positive"], years=_M["years"],
             trim=_M["trim_top_share"], signals=_M["min_signals"], days=_M["min_entry_days"])
DRAWS = _W["draws"]
SEED = _W["seed"]
SIGNALS_PER_DAY = _W["signals_per_day"]
DAY_SHARE = _W["day_share"]
COUNTS = [150, 200, 300, 400, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000, 12000, 16000]
CASES = [(c, sd) for c in ("A", "B") for sd in _W["noise_sd"][c]]
MEANS = _W["means"]

def t3(rng, size):
    return rng.standard_t(3, size) / math.sqrt(3.0)   # unit variance

def passes(x, day, year, floor=True):
    n = len(x); m = x.mean()
    if n < MARKS["signals"]: return False
    ud, inv = np.unique(day, return_inverse=True); G = len(ud)
    if G < MARKS["days"] or m <= 0 or (floor and m < MARKS["mean_floor"]): return False
    tot = np.bincount(inv, weights=x - m)
    se = math.sqrt(G / (G - 1) * (tot ** 2).sum()) / n
    if se <= 0 or m / se < MARKS["t"]: return False
    pos = sum(1 for y in range(MARKS["years"]) if (year == y).any() and x[year == y].mean() > 0)
    if pos < MARKS["years_pos"]: return False
    k = math.ceil(MARKS["trim"] * n)
    return np.sort(x)[:-k].mean() > 0

def power(n, mu, sd, rng):
    day = (np.arange(n) / SIGNALS_PER_DAY).astype(int); days = day[-1] + 1
    year = (day * MARKS["years"]) // days
    a = b = 0
    for _ in range(DRAWS):
        ds = t3(rng, days) * sd * math.sqrt(DAY_SHARE)
        x = mu + ds[day] + t3(rng, n) * sd * math.sqrt(1 - DAY_SHARE)
        a += passes(x, day, year, True); b += passes(x, day, year, False)
    return a / DRAWS, b / DRAWS

def main():
    rng = np.random.default_rng(SEED)
    print("| Card | Noise SD per signal | True mean excess | Doc 117 count, 80% at t 2 | Smallest count, 80% power, all marks | Smallest count, 80%, without the 1.0% floor | Power at 150 / 500 / 1,000 / 2,000 / 4,000 signals, all marks |")
    print("|---|---:|---:|---:|---:|---:|---|")
    for card, sd in CASES:
        for mu in MEANS:
            res = {n: power(n, mu, sd, rng) for n in COUNTS}
            full = next((f"{n:,}" for n in COUNTS if res[n][0] >= _W["target"]), f"none up to {COUNTS[-1]:,} (best {max(r[0] for r in res.values()):.0%})")
            nofl = next((f"{n:,}" for n in COUNTS if res[n][1] >= _W["target"]), f"none up to {COUNTS[-1]:,}")
            d117 = math.ceil(8 * (sd / mu) ** 2)
            print(f"| {card} | {sd:.0%} | +{mu:.1%} | {d117:,} | {full} | {nofl} | " + " / ".join(f"{res[n][0]:.0%}" for n in (150, 500, 1000, 2000, 4000)) + " |", flush=True)
    print(f"\nMEASURED on made-up data: {DRAWS} worlds per cell, seed {SEED}, {SIGNALS_PER_DAY} signals per entry day, day shock {DAY_SHARE:.0%} of variance, Student t with 3 degrees of freedom.")

if __name__ == "__main__": main()
