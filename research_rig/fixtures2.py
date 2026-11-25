"""Checks with known answers for rig2. Exits with an error if any check fails (A15)."""
import numpy as np, pandas as pd, hashlib, sys, math
import rig2 as R
from rules import RULES
ok = True
def check(name, cond, detail=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name, detail)
o = np.array([100., 100, 110, 120, 120]); c = np.array([100., 105, 115, 120, 120]); tgt = np.array([1., 1, 0, 0, 0])
eq, wt, tr = R.simulate(o, c, tgt, 0.0)
check("1 hand-worked profit", abs(eq[-1] - 1.2) < 1e-12, f"equity {eq[-1]:.6f} expected 1.200000")
eq, wt, tr = R.simulate(o, c, tgt, 100.0); exp = (1 / 1.01) / 100 * 120 * 0.99
check("2 hand-worked costs", abs(eq[-1] - exp) < 1e-12, f"equity {eq[-1]:.6f} expected {exp:.6f}")
rng = np.random.default_rng(1); c2 = 100 * np.cumprod(1 + rng.normal(0, 0.02, 500)); o2 = np.r_[c2[0], c2[:-1]]
eq, wt, tr = R.simulate(o2, c2, np.ones(500), 25.0); exp = (1 / 1.0025) / o2[1] * c2[-1]
check("3 buy and hold", abs(eq[-1] - exp) < 1e-9, f"equity {eq[-1]:.6f} expected {exp:.6f}")
s = pd.Series(c2); honest = np.nan_to_num(RULES["S50"](s).values, nan=0.0); peek = (s.shift(-1) > s).astype(float).values
e_h = R.simulate(o2, c2, honest, 0)[0][-1]; e_p = R.simulate(o2, c2, peek, 0)[0][-1]; e_s = R.simulate(o2, c2, np.r_[0.0, honest[:-1]], 0)[0][-1]
check("4 peeking is visible", e_p > 3 * e_h and abs(e_s - e_h) > 1e-9, f"honest {e_h:.3f} peeking {e_p:.3f} shifted {e_s:.3f}")
res = []; cost = 25.0
for seed in range(300):
    r = np.random.default_rng(seed); cz = 100 * np.exp(np.cumsum(r.normal(-0.0002, 0.02, 1000))); oz = np.r_[cz[0], cz[:-1]]
    tg = (r.random(1000) < 0.5).astype(float); tg = np.repeat(tg[::10], 10)
    eq, wt, tr = R.simulate(oz, cz, tg, cost); res.append((eq[-1] - 1, tr.sum() * cost / 1e4))
res = np.array(res); se = res[:, 0].std() / np.sqrt(len(res))
check("5 random entries lose about costs", abs(res[:, 0].mean() + res[:, 1].mean()) < 3 * se, f"mean result {res[:,0].mean():.4f}, mean cost paid {res[:,1].mean():.4f}, 3 standard errors {3*se:.4f}")
eq, wt, tr = R.simulate(o2, c2, np.ones(500), 90.0)
check("9 no leverage", wt.max() <= 1 + 1e-9 and eq.min() > 0, f"max weight {wt.max():.6f}")
h = lambda: hashlib.sha256(R.simulate(o2, c2, honest, 25.0)[0].tobytes()).hexdigest()
check("15 determinism", h() == h(), h()[:16])
# --- added after the audit
# 16 dust: a full sale leaves exactly nothing, and trade sides are counted once
eq, wt, tr = R.simulate(o2, c2, honest, 30.0)
sides = int((tr > R.DUST * np.r_[1.0, eq[:-1]]).sum()); flips = int((np.diff(np.r_[0.0, honest[:-1]]) != 0).sum())
check("16 no dust trades", sides == flips and (wt[np.r_[0.0, honest[:-1]] == 0] == 0).all(), f"sides {sides}, changes of target {flips}")
# 17 fast engine equals general engine, with and without bars that cannot fill
worst = 0.0
for seed in range(1000):
    r = np.random.default_rng(seed); n = 400; cz = 100 * np.exp(np.cumsum(r.normal(0, 0.02, n))); oz = cz * np.exp(r.normal(0, 0.003, n))
    tg = np.repeat((r.random(n // 5) < 0.5).astype(float), 5); cf = (r.random(n) > 0.1) if seed % 2 else None
    cost = float(r.choice([0, 7, 30, 95]))
    a = R.simulate(oz, cz, tg, cost, can_fill=cf)[0]; b = R.sim_fast(oz, cz, tg, cost, can_fill=cf)[0]
    worst = max(worst, np.abs(a / b - 1).max())
check("17 fast engine equals general engine", worst < 1e-10, f"largest relative gap {worst:.2e} over 1,000 random inputs")
try:
    R.sim_fast(o2, c2, np.r_[np.nan, honest[1:]], 0); bad = True
except AssertionError: bad = False
check("18 fast engine refuses missing targets", not bad)
# 19 an order due on a bar that did not trade waits for the next bar that did
o3 = np.array([100., 100, 110, 120, 130, 130]); c3 = np.array([100., 105, 115, 125, 130, 130]); t3 = np.array([1., 1, 1, 0, 0, 0]); cf = np.array([True, False, True, True, True, True])
eq = R.simulate(o3, c3, t3, 0.0, can_fill=cf)[0]
check("19 waits for a bar that traded", abs(eq[-1] - 130 / 110) < 1e-12 and eq[1] == 1.0, f"equity {eq[-1]:.6f} expected {130/110:.6f}")
# 20 band: no trade inside 0.10, also to or from zero
eq, wt, tr = R.simulate(np.full(6, 100.), np.full(6, 100.), np.array([0.08, 0.5, 0.45, 0.58, 0.0, 0.0]), 0.0)
check("20 band has no exception", (tr > 0).tolist() == [False, False, True, False, False, True], str((tr > 0).tolist()))
# 21 shuffles keep trades, time held and both end states
r = np.random.default_rng(3); tg = np.repeat((r.random(200) < 0.5).astype(float), r.integers(1, 9, 200)); good = True
def nsp(x): return int((np.diff(x) != 0).sum())
for i in range(200):
    z = R.null_binary(tg, r); good &= (nsp(z) == nsp(tg)) and z.sum() == tg.sum() and z[0] == tg[0] and z[-1] == tg[-1] and len(z) == len(tg)
check("21 shuffle keeps trades and time held", good and not np.array_equal(R.null_binary(tg, r), tg))
z = R.null_circular(np.arange(100.), np.random.default_rng(0)); check("22 circular shift keeps every value", sorted(z) == list(np.arange(100.)) and z[0] != 0)
# 23 overfitting estimate: pure noise gives about one half on average over many samples, one truly better rule gives about zero
ps = []
for seed in range(40):
    r = np.random.default_rng(100 + seed); X = r.normal(0, 0.01, (1607, 10)); ps.append(R.pbo_cscv(X, 16)["pbo"])
p_noise = R.pbo_cscv(X, 16); X2 = X.copy(); X2[:, 3] += 0.004; p_good = R.pbo_cscv(X2, 16)
check("23 overfitting estimate on known cases", 0.42 < np.mean(ps) < 0.58 and p_good["pbo"] < 0.02 and p_noise["rows_dropped"] == 1607 % 16, f"noise, mean of 40 samples {np.mean(ps):.3f} (single samples range {min(ps):.3f} to {max(ps):.3f}), one real edge {p_good['pbo']:.3f}, rows dropped {p_noise['rows_dropped']}")
X3 = X.copy(); X3[:, 0] = 0.0; p0 = R.pbo_cscv(X3, 16)
check("24 a rule that never trades is counted, not ignored", p0["zero_variance_cases"] == 2 * 12870 and np.isfinite(p0["pbo"]), f"cases {p0['zero_variance_cases']}")
# 25 break-even search
b = R.breakeven(lambda c: 100 - c); b2 = R.breakeven(lambda c: -1.0); b3 = R.breakeven(lambda c: 1.0)
check("25 break-even search", abs(b["bps"] - 100) < 1e-4 and b["status"] == "bracketed" and b2["status"] == "below_at_zero" and b3["status"] == "above_cap")
# 26 first day is counted
ep = R.with_base(np.array([1.1, 1.21]), pd.DatetimeIndex(["2020-01-01", "2020-01-02"])); m = R.metrics(ep.values)
check("26 first day is counted", m["n"] == 2 and abs(m["total"] - 0.21) < 1e-12 and len(R.cut(ep, "2020-01-02", "2020-01-02")) == 2)
# 27 deflated Sharpe refuses a flat series
check("27 undefined values fail", not np.isfinite(R.deflated_sharpe(np.zeros(100), 20, 0.01)[0]) and not R.five_marks(dict(sharpe=float('nan'), maxdd=-0.1), dict(sharpe=1.0, maxdd=-0.5), dict(bps=100, status="bracketed"), 7, float("nan"), float("nan"), float("nan"))["passed"])
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
