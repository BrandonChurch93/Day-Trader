"""Plan 12: how often bootstrap mark 2 passes on made-up data with no edge in it. Writes noedge_12.json, which
report_12.py quotes beside mark 2. Synthetic prices only; no real data is read.
1,000 data sets, seeds 0 to 999; each is 1,008 trading days from 2019-01-02 (48 months, like the design half), SPY plus
60 stocks that move with SPY plus noise, 400 random events over 8 members, cost 0, exit on day entry + hold - 1, the
member's book scored as in score_12 with blocks of block_months(hold) months."""
import sys, json, datetime as dt, numpy as np
import common_12 as C

SETS, OUT = 1000, "noedge_12.json"
days, d = [], dt.date(2019, 1, 2)
while len(days) < 1008:
    if d.weekday() < 5: days.append(d.isoformat())
    d += dt.timedelta(days=1)

def trial(seed, hold):
    r = np.random.default_rng(seed); n = len(days)
    sr = r.normal(0.0003, 0.01, n); sc = 100 * np.cumprod(1 + sr); data = {"SPY": (np.r_[100, sc[:-1]], sc)}
    for k in range(60):
        x = sr + r.normal(0, 0.015, n); c = 20 * np.cumprod(1 + x); data[f"K{k}"] = (np.r_[20, c[:-1]], c)
    q = C.Prices.from_arrays(days, data); m = 400
    a = r.integers(1, n - hold - 1, m); s = np.array([q.si[f"K{k}"] for k in r.integers(0, 60, m)]); mem = r.integers(0, 8, m)
    pf = C.portfolio(q, *C.merge(mem, s, a, a + hold - 1, "member"), by="member", cost=0)
    sm = C.summarize(q, pf)
    return [C.bootstrap_p5(sm["monthly_diff"], 1000, seed, b) > 0 for b in (1, C.block_months(hold))]

if __name__ == "__main__":
    res = dict(sets=SETS, months=48, draws_per_set=1000, written_utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M"), holds={})
    for hold in C.P["holds_days"]:
        R = np.array([trial(s, hold) for s in range(SETS)])
        res["holds"][str(hold)] = dict(block_months=C.block_months(hold), pass_rate_blocks=float(R[:, 1].mean()), pass_rate_single_months_not_used=float(R[:, 0].mean()))
        print(f"hold {hold}: blocks of {C.block_months(hold)} months pass {R[:, 1].mean():.1%}; single months {R[:, 0].mean():.1%}")
    json.dump(res, open(OUT, "w"), indent=1); print("wrote", OUT)
