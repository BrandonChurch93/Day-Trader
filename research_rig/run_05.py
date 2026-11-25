"""Replay 05: slow trend rules on the US stock market, free data. Plan: PREREG_05_stock_trend_free_data.md.
Writes results_05.json. Not the product."""
import numpy as np, pandas as pd, json, sys, os, subprocess, math
from multiprocessing import Pool
import rig2 as R
F = os.environ.get("FRENCH_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "french"))
PPY = 252; NSHUF = 1000; N_TRIALS = 44; COSTS = {"low": 2, "base": 5, "high": 10}
SL = {"dev": (None, "2006-05-31"), "held": ("2006-06-01", "2026-06-30"), "post": ("2026-07-01", "2026-09-30"), "all": (None, "2026-09-30"),
      "y2008": ("2008-01-01", "2008-12-31"), "y2020": ("2020-01-01", "2020-12-31"), "y2022": ("2022-01-01", "2022-12-31")}
POOL = os.environ.get("R05_POOL") == "1"   # AMENDMENT_05_I2_equal_thirds.md: split into equal thirds again on re-entry from all cash
OUT = "results_05b.json" if POOL else "results_05.json"
START = "1927-08-01"; NAMES = ["T1", "T2", "T3", "T4", "T5", "V1", "I1", "I2"]

# ------------------------------------------------------------------ data
def load():
    f = pd.read_csv(f"{F}/F-F_Research_Data_Factors_daily__main.csv"); f.index = pd.to_datetime(f.date.astype(str), format="%Y%m%d")
    ind = pd.read_csv(f"{F}/12_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv"); ind.index = pd.to_datetime(ind.date.astype(str), format="%Y%m%d"); ind = ind.drop(columns="date")
    assert f.index.equals(ind.index) and f.index.is_monotonic_increasing and f.index.is_unique
    assert (ind > -99).all().all() and (f[["Mkt-RF", "RF"]] > -99).all().all(), "missing codes present"
    return (f["Mkt-RF"] + f["RF"]) / 100, f["RF"] / 100, ind / 100

# ------------------------------------------------------------------ return-based engines
def sim_ret(ra, rc, target, cost_bps, band=0.10, lag=1, sides=2, start=1.0):
    """ra, rc: daily returns of the asset and of cash. target[t] is decided at the close of day t and traded at the
    close of day t+lag. Each trade pays cost_bps times sides (the cash fund is traded too)."""
    n = len(ra); eq = np.empty(n); wt = np.empty(n); tr = np.zeros(n); S = 0.0; C = start; c = cost_bps / 1e4 * sides
    for t in range(n):
        S *= 1 + ra[t]; C *= 1 + rc[t]
        if t - lag >= 0:
            tw = target[t - lag]; e = S + C; cur = S / e
            if abs(tw - cur) > band:
                want = tw * e
                if want > S:
                    x = (want - S) / (1 + tw * c)
                    if tw >= 1.0 or x >= C / (1 + c): x = C / (1 + c); C = 0.0
                    else: C -= x * (1 + c)
                    S += x
                else:
                    if tw <= 0.0: x = S; S = 0.0
                    else: x = min((S - want) / (1 - tw * c), S); S -= x
                    C += x * (1 - c)
                tr[t] = x
        eq[t] = S + C; wt[t] = S / eq[t]
    return eq, wt, tr

def sim_slots(RA, rc, assign, cost_bps, lag=1, sides=2, pool=None):
    """Slot engine. RA: days x assets returns. assign[t, s]: asset index held by slot s as decided at the close of
    day t (-1 is cash). Each slot starts with an equal share in cash. A slot trades only when its asset changes.
    pool: when every slot is in cash and at least one is about to buy, the cash is first split equally again."""
    if pool is None: pool = POOL
    n, ns = assign.shape; val = np.full(ns, 1.0 / ns); cur = np.full(ns, -1); eq = np.empty(n); wt = np.empty(n); tr = np.zeros(n); c = cost_bps / 1e4 * sides
    for t in range(n):
        for s in range(ns): val[s] *= 1 + (rc[t] if cur[s] < 0 else RA[t, cur[s]])
        if t - lag >= 0:
            want = assign[t - lag]
            if pool and (cur < 0).all() and (want >= 0).any(): val[:] = val.sum() / ns
            for s in range(ns):
                if want[s] != cur[s]:
                    tr[t] += val[s]; val[s] *= (1 - c) if want[s] < 0 else 1 / (1 + c); cur[s] = want[s]
        eq[t] = val.sum(); wt[t] = val[cur >= 0].sum() / eq[t]
    return eq, wt, tr

# ------------------------------------------------------------------ rules
def month_end_flag(idx):
    m = idx.to_period("M"); return np.r_[m[1:] != m[:-1], True]
def monthly_to_daily(idx, sig_at_me):
    """sig_at_me: Series on month-end days. Returns daily array holding the last month-end signal (nan before the first)."""
    return sig_at_me.reindex(idx).ffill().values
def t1(I):
    me = I[month_end_flag(I.index)]; s = (me > me.rolling(10).mean()).astype(float).where(me.rolling(10).mean().notna()); return monthly_to_daily(I.index, s)
def t2(I):
    m = I.rolling(200).mean(); return (I > m).astype(float).where(m.notna()).values
def t3(I, B):
    me = I[month_end_flag(I.index)]; be = B[month_end_flag(B.index)]
    s = ((me / me.shift(12)) > (be / be.shift(12))).astype(float).where(me.shift(12).notna()); return monthly_to_daily(I.index, s)
def t4(I):
    return (sum((I > I.rolling(L).mean()).astype(float).where(I.rolling(L).mean().notna()) for L in (20, 50, 100, 200)) / 4).values
def t5(I):
    m = I.rolling(200).mean(); above = (I > m).values; mv = m.values; n = len(I); out = np.full(n, np.nan); state = 1.0; ua = 0; ub = 0
    for i in range(n):
        if np.isnan(mv[i]): continue
        ua = ua + 1 if above[i] else 0; ub = ub + 1 if not above[i] else 0
        if ua >= 5: state = 1.0
        elif state == 1.0 and ub >= 5: state = 0.5
        if state < 1.0 and ua < 5 and i >= 5 and not np.isnan(mv[i - 5]) and mv[i] < mv[i - 5]: state = 0.0
        out[i] = state
    return out
def v1(r):
    vol = r.rolling(21).std(ddof=1) * math.sqrt(PPY); return np.minimum(1.0, 0.10 / vol).where(vol.notna()).values
def i2_assign(I, IND):
    me = month_end_flag(I.index); mom = (IND[me] / IND[me].shift(12) - 1); filt = pd.Series(t1(I), index=I.index)[me]
    cur = [-1, -1, -1]; rows = {}
    for d in mom.index:
        if mom.loc[d].isna().any() or np.isnan(filt.loc[d]): rows[d] = [np.nan] * 3; continue
        top = list(np.argsort(-mom.loc[d].values)[:3]) if filt.loc[d] > 0 else []
        new = [a if a in top else -1 for a in cur]
        if top:
            free = [a for a in top if a not in new]
            new = [free.pop(0) if a < 0 else a for a in new]
        cur = new; rows[d] = list(cur)
    A = pd.DataFrame.from_dict(rows, orient="index").reindex(I.index).ffill(); return A.values

# ------------------------------------------------------------------ run
def setup():
    rm, rf, ind = load(); I = (1 + rm).cumprod(); B = (1 + rf).cumprod(); IND = (1 + ind).cumprod()
    T = {"T1": t1(I), "T2": t2(I), "T3": t3(I, B), "T4": t4(I), "T5": t5(I), "V1": v1(rm)}
    TI = np.column_stack([t1(IND[c]) for c in IND.columns]); A2 = i2_assign(I, IND)
    m = I.index >= START; idx = I.index[m]
    assert not np.isnan(TI[m]).any() and not np.isnan(A2[m]).any() and all(not np.isnan(T[k][m]).any() for k in T)
    return dict(idx=idx, rm=rm.values[m], rf=rf.values[m], ind=ind.values[m], T={k: v[m] for k, v in T.items()}, TI=TI[m], A2=A2[m].astype(int))
D = None
def run_rule(name, c, lag=1, cash=True, target=None):
    rf = D["rf"] if cash else np.zeros(len(D["rf"]))
    if name in D["T"] or name in ("HOLD", "MIX"):
        t = target if target is not None else (np.ones(len(rf)) if name == "HOLD" else D["T"][name]); return sim_ret(D["rm"], rf, t, c, lag=lag)
    if name in ("I1", "HOLD12"):
        TI = target if target is not None else (np.ones_like(D["TI"]) if name == "HOLD12" else D["TI"]); k = TI.shape[1]; eq = 0; wt = 0; tr = 0
        parts = [sim_ret(D["ind"][:, j], rf, TI[:, j], c, lag=lag, start=1.0 / k) for j in range(k)]
        eq = sum(p[0] for p in parts); wt = sum(p[0] * p[1] for p in parts) / eq; tr = sum(p[2] for p in parts); return eq, wt, tr
    if name == "I2": return sim_slots(D["ind"], rf, target if target is not None else D["A2"], c, lag=lag)
BENCH = {n: "HOLD" for n in NAMES}; BENCH["I1"] = "HOLD12"
def ex(eq):
    """Excess returns over bills from an equity array (first day included)."""
    return R.rets(np.r_[1.0, eq]) - D["rf"]
def met(eq, lo, hi):
    ep = R.with_base(eq, D["idx"]); s = R.cut(ep, lo, hi); rfp = pd.Series(D["rf"], index=D["idx"]).reindex(s.index[1:]).values
    return R.metrics(s.values, PPY, rf=rfp)
def null_target(name, rng):
    if name in ("T1", "T2", "T3"): return R.null_binary(D["T"][name], rng)
    k = int(rng.integers(30, len(D["rf"]) - 30))
    if name == "I1": return np.roll(D["TI"], k, axis=0)
    if name == "I2": return np.roll(D["A2"], k, axis=0)
    return np.roll(D["T"][name], k)
def cost_job(args):
    lab, c = args; out = {"rules": {}, "bench": {}}; X = {}
    for b in ("HOLD", "HOLD12"):
        eq, wt, tr = run_rule(b, c); out["bench"][b] = {k: met(eq, lo, hi) for k, (lo, hi) in SL.items()}; X[b] = ex(eq)
    for n in NAMES:
        eq, wt, tr = run_rule(n, c); X[n] = ex(eq)
        rr = {k: dict(met(eq, lo, hi), **R.activity(eq, wt, tr, D["idx"], lo, hi, PPY)) for k, (lo, hi) in SL.items()}
        rr["same_close"] = {k: met(run_rule(n, c, lag=0)[0], *SL[k]) for k in ("held", "all")}
        rr["cash_earns_nothing"] = {k: met(run_rule(n, c, cash=False)[0], *SL[k]) for k in ("held", "all")}
        # fixed mix with the rule's own average weight in the development slice
        wbar = rr["dev"]["avg_weight"]; meq = run_rule("MIX", c, target=np.full(len(D["rf"]), wbar))[0] if n not in ("I1", "I2") else None
        if n == "I1": meq = run_rule("I1", c, target=np.full_like(D["TI"], wbar))[0]
        if n == "I2": meq = run_rule("MIX", c, target=np.full(len(D["rf"]), wbar))[0]
        rr["fixed_mix"] = {"weight": wbar, **{k: met(meq, *SL[k]) for k in ("held", "all")}}
        rr["beats_fixed_mix_held"] = bool(rr["held"]["sharpe"] > rr["fixed_mix"]["held"]["sharpe"] and abs(rr["held"]["maxdd"]) < abs(rr["fixed_mix"]["held"]["maxdd"]))
        out["rules"][n] = rr
    sd = float(np.std([R.sharpe_pp(X[n]) for n in NAMES], ddof=1)); out["trial_sharpe_std_per_period"] = sd
    M = np.column_stack([X[n] for n in NAMES]); out["pbo"] = R.pbo_cscv(M, 16, "earliest"); out["pbo_drop_latest"] = R.pbo_cscv(M, 16, "latest")
    for n in NAMES:
        rng = np.random.default_rng(7); s_real = R.sharpe_pp(X[n]); cnt = 0; sides = []; wts = []
        for i in range(NSHUF):
            eq, wt, tr = run_rule(n, c, target=null_target(n, rng)); cnt += R.sharpe_pp(ex(eq)) < s_real
            sides.append(int((tr > R.DUST * np.r_[1.0, eq[:-1]]).sum())); wts.append(float(wt.mean()))
        rr = out["rules"][n]; rr["dsr"] = R.deflated_sharpe(X[n], N_TRIALS, sd)[0]; rr["shuffle_pct"] = cnt / NSHUF
        rr["shuffle_mean_sides"] = float(np.mean(sides)); rr["shuffle_mean_avg_weight"] = float(np.mean(wts))
        rr["boot_sharpe_diff_vs_bench"] = R.block_bootstrap_sharpe_diff(X[n], X[BENCH[n]], block=21, ppy=PPY)
        rr["dd_ratio"] = abs(rr["held"]["maxdd"]) / abs(out["bench"][BENCH[n]]["held"]["maxdd"])
    print(lab, "done", flush=True); return lab, out
def be_job(n):
    sh = lambda name, c: R.metrics(np.r_[1.0, run_rule(name, c)[0]], PPY, rf=D["rf"])
    return n, dict(vs_bench=R.breakeven(lambda c: sh(n, c)["sharpe"] - sh(BENCH[n], c)["sharpe"]), zero_excess=R.breakeven(lambda c: sh(n, c)["sharpe"]))

def fixtures():
    ok = True
    def check(name, cond, detail=""):
        nonlocal ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name, detail)
    r = np.random.default_rng(2); ra = r.normal(0.0004, 0.01, 600); rc = np.full(600, 0.0001)
    eq = sim_ret(ra, rc, np.ones(600), 5.0)[0]; exp = (1.0001 ** 2) / (1 + 0.001) * np.prod(1 + ra[2:])
    check("R1 holding equals market return less entry cost", abs(eq[-1] / exp - 1) < 1e-12, f"{eq[-1]:.6f} expected {exp:.6f}")
    eq = sim_ret(ra, rc, np.zeros(600), 5.0)[0]; check("R2 zero weight equals bills", abs(eq[-1] - 1.0001 ** 600) < 1e-12)
    eq = sim_ret(np.array([0.0, 0.0, 0.10, 0.0, 0.0]), np.zeros(5), np.array([1., 0, 0, 0, 0]), 50.0)[0]; exp = 1 / 1.01 * 1.10 * 0.99
    check("R3 hand-worked switch with costs", abs(eq[-1] - exp) < 1e-12, f"{eq[-1]:.6f} expected {exp:.6f}")
    peek = (np.r_[ra[2:], 0, 0] > 0).astype(float); honest = (ra > 0).astype(float)
    check("R4 peeking is visible", sim_ret(ra, rc, peek, 0)[0][-1] > 3 * sim_ret(ra, rc, honest, 0)[0][-1])
    RA = r.normal(0.0004, 0.01, (600, 4)); asg = np.repeat(r.integers(-1, 4, (30, 2)), 20, axis=0)
    a = sim_slots(RA, rc, asg, 5.0)[0]; b = sim_slots(RA, rc, asg, 5.0)[0]
    one = sim_slots(RA, rc, np.zeros((600, 1), int), 5.0)[0]; ref = sim_ret(RA[:, 0], rc, np.ones(600), 5.0)[0]
    check("R5 slot engine matches the plain engine and repeats", np.array_equal(a, b) and abs(one[-1] / ref[-1] - 1) < 1e-12)
    # R6, hand-worked: three thirds in stocks for 3 days (+10%, 0, -10% a day), out, in again, then the first asset gains 50% in one day.
    # Thirds before re-entry: 1.331/3, 1/3, 0.729/3 (sum 1.02). Pooled: 0.34 each, so 0.34 * 1.5 + 0.68 = 1.19. Not pooled: 1.331/3 * 1.5 + 1/3 + 0.729/3.
    RA6 = np.zeros((9, 3)); RA6[2:5, 0] = 0.10; RA6[2:5, 2] = -0.10; RA6[7, 0] = 0.5; asg6 = np.array([[0, 1, 2]] * 3 + [[-1, -1, -1]] * 2 + [[0, 1, 2]] * 4)
    e_p = sim_slots(RA6, np.zeros(9), asg6, 0.0, pool=True)[0][-1]; e_u = sim_slots(RA6, np.zeros(9), asg6, 0.0, pool=False)[0][-1]
    check("R6 thirds are equal again on re-entry from cash when pooling is on, and drift when it is off",
          abs(e_p - 1.19) < 1e-12 and abs(e_u - (1.331 / 3 * 1.5 + 1 / 3 + 0.729 / 3)) < 1e-12, f"pooled {e_p:.6f} expected 1.190000, not pooled {e_u:.6f} expected {1.331 / 3 * 1.5 + 1 / 3 + 0.729 / 3:.6f}")
    return ok

if __name__ == "__main__":
    if subprocess.run([sys.executable, "fixtures2.py"], capture_output=True).returncode != 0 or not fixtures(): raise SystemExit("checks failed; nothing was run")
    D = setup()
    import multiprocessing as _mp
    with _mp.get_context("fork").Pool(4) as pool:   # fork so workers inherit the loaded data
        be = dict(pool.map(be_job, NAMES)); res = pool.map(cost_job, list(COSTS.items()))
    out = {"thresholds": R.thresholds_used(), "start": START, "days": int(len(D["idx"])), "n_trials": N_TRIALS, "shuffles": NSHUF, "breakeven": be, "costs": {}}
    for lab, o in res:
        c = COSTS[lab]
        for n in NAMES:
            x = o["rules"][n]; x["marks"] = R.five_marks(x["held"], o["bench"][BENCH[n]]["held"], be[n]["vs_bench"], c, x["dsr"], o["pbo"]["pbo"], x["shuffle_pct"])
        out["costs"][lab] = dict(o, cost_bps_per_side=c)
    out["i2_pooled_on_reentry"] = POOL
    json.dump(out, open(OUT, "w"), indent=1, default=float); print("done", OUT)
else:
    pass
