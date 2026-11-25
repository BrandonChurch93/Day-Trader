"""Plan TM06: works out, once, the four test weeks and the five coins for each swing session, from daily bars only.
The five coins of a week are the ones that rose most over the seven days before the week starts (known at the start).
Prints the values that go into tm06_plan in config/thresholds.yaml. Reads no minute bar and starts no session.
Weeks are whole UTC weeks, Monday to Monday. They are ranked by the gain of the plan's coins held in equal parts,
and the weeks at the 10th, 30th, 70th and 90th percentile are taken: two falling, two rising, not the extremes.
    python3 timemachine/tm06_fix_weeks.py"""
import sqlite3, datetime as dt, json, os
TAPE = os.environ.get("TM_FAST_TAPE", "/home/user/workspace/rig/tm_store/tape_fast.sqlite")
LEFT_OUT = ["BTC/USD", "ETH/USD", "PAXG/USD"]; FIRST_MONDAY = "2026-04-06"; LAST_MONDAY = "2026-11-23"; PCTS = [0.1, 0.3, 0.7, 0.9]; PER_SESSION = 5
def main():
    c = sqlite3.connect(f"file:{TAPE}?mode=ro", uri=True)
    coins = sorted(s for s in json.loads(c.execute("select value from meta where key='coins_json'").fetchone()[0]) if s not in LEFT_OUT)
    D = {s: {dt.datetime.fromtimestamp(t, dt.timezone.utc).date(): cl for t, cl in c.execute("select t,c from bars where symbol=? and tf='1Day'", (s,))} for s in coins}
    d = dt.date.fromisoformat(FIRST_MONDAY); end = dt.date.fromisoformat(LAST_MONDAY); weeks = []
    while d + dt.timedelta(days=7) <= end:
        a, b = d - dt.timedelta(days=1), d + dt.timedelta(days=6)   # close of the Sunday before, close of the Sunday that ends the week
        r = [D[s][b] / D[s][a] - 1 for s in coins if a in D[s] and b in D[s]]
        weeks.append((sum(r) / len(r), d.isoformat(), len(r))); d += dt.timedelta(days=7)
    ranked = sorted(weeks); n = len(ranked); picks = sorted(ranked[round(p * (n - 1))] for p in PCTS)
    out = {"coins": coins, "weeks_ranked": n, "swing_weeks": []}
    for ret, monday, k in sorted(picks, key=lambda x: x[1]):
        m = dt.date.fromisoformat(monday); a, b = m - dt.timedelta(days=8), m - dt.timedelta(days=1)   # the seven days that end at the Sunday close before the week
        rise = sorted(((D[s][b] / D[s][a] - 1, s) for s in coins if a in D[s] and b in D[s]), reverse=True)[:PER_SESSION]
        out["swing_weeks"].append({"start": monday, "end": (m + dt.timedelta(days=7)).isoformat(), "basket_gain": round(ret, 4), "coins_priced": k,
                                   "coins": sorted(s for _, s in rise), "rise_before": {s: round(r, 4) for r, s in rise}})
    print(json.dumps(out, indent=1))
if __name__ == "__main__": main()
