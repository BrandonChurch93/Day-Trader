"""Plan 74 power screen on made-up returns only. No market data, no network. Reads only `replay_74_plan`
in config/thresholds.yaml.

Second version, overlapping holds. Five design years of 252 sessions, 21-session calendar months (60 months).
A world has n signals; signal i enters on session floor(i * 1260 / n) and holds a made-up number of sessions,
uniform from 1 to the card's limit (40 for Card A, 10 for Card B). Its excess return over the market fund is
    mean + common part + own part.
The common part is a weighted sum of calendar-month shocks over the months the hold spans, weight = share of
hold sessions in that month, scaled so it carries the stated share of variance. Signals whose holds share a month
share that month's shock. All shocks are Student t with 3 degrees of freedom (fat tails).
Every design-year mark is applied, with the t clustered by calendar month of entry: mean above zero and at least
the floor, month-clustered t at least the t mark, positive in at least 4 of 5 entry years, positive after removing
the top 1%, at least 150 signals on at least 100 entry days. Power = share of worlds passing every mark.
Run: python3 research_rig/power_74.py > /tmp/power_74.txt  (prints the main markdown table).
Run: python3 research_rig/power_74.py --sensitivity  (prints the shown-only table with the common month share varied)."""
import json, math, pathlib, numpy as np

def _plan():
    lines = (pathlib.Path(__file__).resolve().parents[1] / "config" / "thresholds.yaml").read_text().splitlines()
    i = lines.index("replay_74_plan:")
    return json.loads(lines[i + 1].split("value:", 1)[1])

_P = _plan(); _M = _P["marks"]; _W = _P["power"]
MARKS = dict(mean_floor=_M["mean_floor"], t=_M["min_t"], years_pos=_M["years_positive"], years=_M["years"],
             trim=_M["trim_top_share"], signals=_M["min_signals"], days=_M["min_entry_days"])
DRAWS = _W["draws"]; SEED = _W["seed"]; SHARE = _W["common_share"]
YEAR_SESSIONS = _W["sessions_per_year"]; MONTH_SESSIONS = _W["sessions_per_month"]
SESSIONS = YEAR_SESSIONS * MARKS["years"]; MONTHS = SESSIONS // MONTH_SESSIONS
COUNTS = _W["counts"]; MEANS = _W["means"]; HOLD = _W["hold_limit"]; TARGET = _W["target"]
CASES = [(c, sd) for c in ("A", "B") for sd in _W["noise_sd"][c]]
SHOW = _W["show_counts"]

def t3(rng, size):
    return rng.standard_t(3, size) / math.sqrt(3.0)   # unit variance

def layout(n, hold, rng):
    entry = (np.arange(n) * SESSIONS) // n
    length = rng.integers(1, hold + 1, n)
    W = np.zeros((n, MONTHS + 2))
    for i in range(n):
        s = np.arange(entry[i], entry[i] + length[i]) // MONTH_SESSIONS
        np.add.at(W[i], s, 1.0 / length[i])
    W /= np.sqrt((W ** 2).sum(axis=1, keepdims=True))   # unit variance of the common part
    month = entry // MONTH_SESSIONS; year = entry // YEAR_SESSIONS
    return W, entry, month, year

def passes(x, entry, month, year, floor=True):
    n = len(x); m = x.mean()
    if n < MARKS["signals"] or len(np.unique(entry)) < MARKS["days"]: return False
    if m <= 0 or (floor and m < MARKS["mean_floor"]): return False
    ud, inv = np.unique(month, return_inverse=True); G = len(ud)
    tot = np.bincount(inv, weights=x - m)
    se = math.sqrt(G / (G - 1) * (tot ** 2).sum()) / n
    if se <= 0 or m / se < MARKS["t"]: return False
    pos = sum(1 for y in range(MARKS["years"]) if (year == y).any() and x[year == y].mean() > 0)
    if pos < MARKS["years_pos"]: return False
    k = math.ceil(MARKS["trim"] * n)
    return np.sort(x)[:-k].mean() > 0

def power(n, mu, sd, hold, rng, share=None):
    share = SHARE if share is None else share
    W, entry, month, year = layout(n, hold, rng)
    a = b = 0
    for _ in range(DRAWS):
        x = mu + sd * (math.sqrt(share) * (W @ t3(rng, W.shape[1])) + math.sqrt(1 - share) * t3(rng, n))
        a += passes(x, entry, month, year, True); b += passes(x, entry, month, year, False)
    return a / DRAWS, b / DRAWS

def main():
    rng = np.random.default_rng(SEED)
    print("| Card | Hold limit, sessions | Noise SD per signal | True mean excess | Smallest count, 80% power, all marks | Smallest count, 80%, without the mean floor | Power at " + " / ".join(f"{n:,}" for n in SHOW) + " signals, all marks |")
    print("|---|---:|---:|---:|---:|---:|---|")
    for card, sd in CASES:
        for mu in MEANS:
            res = {n: power(n, mu, sd, HOLD[card], rng) for n in COUNTS}
            full = next((f"{n:,}" for n in COUNTS if res[n][0] >= TARGET), f"none up to {COUNTS[-1]:,} (best {max(r[0] for r in res.values()):.0%})")
            nofl = next((f"{n:,}" for n in COUNTS if res[n][1] >= TARGET), f"none up to {COUNTS[-1]:,}")
            print(f"| {card} | {HOLD[card]} | {sd:.0%} | +{mu:.1%} | {full} | {nofl} | " + " / ".join(f"{res[n][0]:.0%}" for n in SHOW) + " |", flush=True)
    print(f"\nMEASURED on made-up data: {DRAWS} worlds per cell, seed {SEED}, common month shock {SHARE:.0%} of variance, "
          f"holds uniform 1 to the limit, t clustered by calendar month of entry ({MONTHS} months), Student t with 3 degrees of freedom, mean floor {MARKS['mean_floor']:.1%}.")

def sensitivity():
    rng = np.random.default_rng(SEED + 1)
    print("\nShown only, the common month share varied, middle noise SD per card:\n")
    print("| Card | Noise SD | Common month share | True mean excess | Smallest count, 80% power, all marks | Power at " + " / ".join(f"{n:,}" for n in SHOW) + " signals |")
    print("|---|---:|---:|---:|---:|---|")
    for card in ("A", "B"):
        sd = _W["noise_sd"][card][1]
        for share in _W["common_share_shown"]:
            for mu in MEANS:
                res = {n: power(n, mu, sd, HOLD[card], rng, share)[0] for n in COUNTS}
                full = next((f"{n:,}" for n in COUNTS if res[n] >= TARGET), f"none up to {COUNTS[-1]:,} (best {max(res.values()):.0%})")
                print(f"| {card} | {sd:.0%} | {share:.0%} | +{mu:.1%} | {full} | " + " / ".join(f"{res[n]:.0%}" for n in SHOW) + " |", flush=True)

if __name__ == "__main__":
    import sys
    if "--sensitivity" in sys.argv:
        sensitivity(); raise SystemExit

    main()
