"""Do the one-minute files and the daily files from the workspace's own price lookup agree with each other?
For SPY and QQQ, for every day that is in both: the day's open, high, low and close are rebuilt from the one-minute bars
and compared with the daily row. The gap is in basis points of the daily figure (1 bps = 0.01%).
Reads data/platform_bars/ (or PLATFORM_BARS_DIR). Writes platform_bars_crosscheck.json next to this script: counts,
dates and gaps in basis points only, no price.
Runs no trading rule and works out no return over time. It compares two figures for the same day.
What it can show: on which days the two sets of files disagree, and whether the yearly gap between them stays small, which is
what one would see if they are adjusted the same way. It cannot prove that they are. (This line said "whether the two sets of
files are adjusted the same way" when the script was run. An outside check found that too strong, and it was reworded after the run.
No code line was changed.) It does not leave out days where the one-minute files have minutes missing.
What it cannot show: whether either is right. Both come from the same lookup. A second source is still needed.
The bands below were committed and pushed before the script was first run, and so was this text apart from the line above.
  python3 platform_bars_crosscheck.py"""
import csv, glob, json, os, datetime as dt, statistics
from collections import defaultdict
H = os.path.dirname(os.path.abspath(__file__))
D = os.environ.get("PLATFORM_BARS_DIR", os.path.join(H, "data", "platform_bars"))
BANDS = [1, 5, 10, 25]          # basis points. A day is counted in the first band its gap fits in; over the last band it is listed by date
LIST_OVER = BANDS[-1]
FIELDS = ["open", "high", "low", "close"]

def bps(minute, daily): return (minute / daily - 1.0) * 1e4

def day_bars(sym):
    days = defaultdict(list)
    for p in sorted(glob.glob(os.path.join(D, "1min", f"{sym}_1min_*.csv"))):
        with open(p, newline="") as fh:
            r = csv.reader(fh); next(r)
            for x in r:
                if x: days[x[0][:10]].append(x)
    return days

def check(sym):
    daily = {}
    with open(os.path.join(D, "1day", f"{sym}_1day.csv"), newline="") as fh:
        r = csv.reader(fh); next(r)
        for x in r:
            if x: daily[x[0][:10]] = [float(v) for v in x[1:5]]
    mins = day_bars(sym)
    both = sorted(set(daily) & set(mins))
    out = {"days_in_both": len(both), "days_in_one_minute_only": sorted(set(mins) - set(daily)),
           "days_in_daily_only_inside_one_minute_range": len([d for d in daily if d not in mins and min(mins) <= d <= max(mins)]),
           "fields": {}, "median_close_gap_bps_by_year": {}}
    gaps = {f: {} for f in FIELDS}
    for d in both:
        rows = sorted(mins[d], key=lambda x: x[0])
        built = [float(rows[0][1]), max(float(x[2]) for x in rows), min(float(x[3]) for x in rows), float(rows[-1][4])]
        for f, m, dy in zip(FIELDS, built, daily[d]): gaps[f][d] = bps(m, dy)
    for f in FIELDS:
        g = gaps[f]; counts = {}; prev = 0
        for b in BANDS:
            counts[f"over_{prev}_up_to_{b}_bps" if prev else f"up_to_{b}_bps"] = sum(1 for v in g.values() if prev < abs(v) <= b) if prev else sum(1 for v in g.values() if abs(v) <= b)
            prev = b
        over = sorted(((d, round(v, 1)) for d, v in g.items() if abs(v) > LIST_OVER))
        out["fields"][f] = {"days_by_size_of_gap": counts, f"days_over_{LIST_OVER}_bps": len(over), f"dates_over_{LIST_OVER}_bps": [[d, v] for d, v in over],
                            "median_gap_bps": round(statistics.median(g.values()), 2), "median_size_of_gap_bps": round(statistics.median(abs(v) for v in g.values()), 2)}
    # a high built from one-minute bars can never be above the day's true high, nor a low below the day's true low
    out["days_one_minute_high_above_daily_high_by_over_1_bps"] = sum(1 for v in gaps["high"].values() if v > 1)
    out["days_one_minute_low_below_daily_low_by_over_1_bps"] = sum(1 for v in gaps["low"].values() if v < -1)
    by_year = defaultdict(list)
    for d, v in gaps["close"].items(): by_year[d[:4]].append(v)
    out["median_close_gap_bps_by_year"] = {y: round(statistics.median(v), 2) for y, v in sorted(by_year.items())}
    return out

def main():
    rep = {"what_this_is": "Gap between the day's figures rebuilt from one-minute bars and the daily row, same lookup, in basis points of the daily figure. No price is stored here.",
           "bands_bps": BANDS, "funds": {s: check(s) for s in ("SPY", "QQQ")}}
    json.dump(rep, open(os.path.join(H, "platform_bars_crosscheck.json"), "w"), indent=1)
    print("platform_bars_crosscheck.json written")

if __name__ == "__main__": main()
