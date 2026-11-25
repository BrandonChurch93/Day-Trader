"""Lightweight single-process audit probes for Replay 05.
Does not modify any rig file or start a full run."""
import sys, os, math, json
sys.path.insert(0, "/home/user/workspace/dt-work/research_rig")
import numpy as np
import pandas as pd
import run_05 as r5
import rig2 as R

print("=== PROBE 1: DATA CHECKS ===")
rm, rf, ind = r5.load()
print(f"Rows: {len(rm)}, first={rm.index[0].date()}, last={rm.index[-1].date()}")
print(f"Any NaN: rm={rm.isna().sum()}, rf={rf.isna().sum()}, ind={ind.isna().sum().sum()}")
print(f"rm range: [{rm.min():.5f}, {rm.max():.5f}], rf range: [{rf.min():.6f}, {rf.max():.6f}]")
print(f"ind columns ({len(ind.columns)}): {list(ind.columns)}")
# Check if any negative RF days exist
print(f"Negative RF days: {(rf < 0).sum()}, zero RF days: {(rf == 0).sum()}")
# Check date gaps (weekends/holidays expected; check max gap in calendar days)
gaps = rm.index.to_series().diff().dt.days.dropna()
print(f"Max calendar day gap: {int(gaps.max())} days on {gaps.idxmax().date()}")
# Check how many trading days in 1927-08-01..2026-09-30 and in each slice
D = r5.setup()
r5.D = D
print(f"Test sample days (>= {r5.START}): {len(D['idx'])}, first={D['idx'][0].date()}, last={D['idx'][-1].date()}")
for k, (lo, hi) in r5.SL.items():
    ep = R.with_base(np.ones(len(D["idx"])), D["idx"])
    s = R.cut(ep, lo, hi)
    print(f"  Slice {k:5s}: {len(s)-1:5d} return days, base={s.index[0].date()}, first_ret={s.index[1].date()}, last_ret={s.index[-1].date()}")

print("\n=== PROBE 2: LOOK-AHEAD PERTURBATION TEST (ALL 8 RULES) ===")
# Perturb returns STRICTLY AFTER cutoff date t_cut and verify earlier signals/targets do not change.
I_base = (1 + rm).cumprod()
B_base = (1 + rf).cumprod()
IND_base = (1 + ind).cumprod()

def compute_all_targets(rm_, rf_, ind_):
    I_ = (1 + rm_).cumprod(); B_ = (1 + rf_).cumprod(); IND_ = (1 + ind_).cumprod()
    out = {
        "T1": r5.t1(I_),
        "T2": r5.t2(I_),
        "T3": r5.t3(I_, B_),
        "T4": r5.t4(I_),
        "T5": r5.t5(I_),
        "V1": r5.v1(rm_),
        "I1": np.column_stack([r5.t1(IND_[c]) for c in IND_.columns]),
        "I2": r5.i2_assign(I_, IND_),
    }
    return out

base_T = compute_all_targets(rm, rf, ind)
# Test cutoffs: mid-month day, month-end day, day after month-end, and inside held-back slice
cutoffs = ["2006-05-15", "2006-05-31", "2006-06-01", "2020-03-16", "2022-06-30"]
for cstr in cutoffs:
    t_cut = pd.Timestamp(cstr)
    rm_p = rm.copy(); rf_p = rf.copy(); ind_p = ind.copy()
    future = rm.index > t_cut
    rm_p.loc[future] = -0.15
    rf_p.loc[future] = 0.05
    ind_p.loc[future] = -0.15
    pert_T = compute_all_targets(rm_p, rf_p, ind_p)
    past = rm.index <= t_cut
    leaks = []
    for k in base_T:
        a = np.nan_to_num(base_T[k][past], nan=-999.0)
        b = np.nan_to_num(pert_T[k][past], nan=-999.0)
        if not np.array_equal(a, b):
            leaks.append(k)
    print(f"  Cutoff {cstr}: signal leaks = {leaks}")

# Also test engine execution causality: perturbing day t+1 returns must NOT affect eq[t] or wt[t],
# and perturbing day t's signal must NOT affect day t's return (for lag=1, must not affect day t+1's return either!)
print("\n=== PROBE 2b: SIGNAL-TO-FILL LAG VERIFICATION ===")
# Find first switch of T1 after START
t1_arr = D["T"]["T1"]
idx = D["idx"]
sw = np.flatnonzero(np.diff(t1_arr) != 0) + 1
s0 = sw[0]
eq_t1, wt_t1, tr_t1 = r5.run_rule("T1", 5.0, lag=1)
print(f"First T1 target change at i={s0} ({idx[s0].date()}): target[{s0-1}]={t1_arr[s0-1]} -> target[{s0}]={t1_arr[s0]}")
for j in range(s0 - 1, s0 + 4):
    is_me = bool(r5.month_end_flag(idx)[j])
    print(f"  i={j} {idx[j].date()} (ME={str(is_me):5s}): target={t1_arr[j]:.1f}, wt={wt_t1[j]:.4f}, tr={tr_t1[j]:.4f}, eq={eq_t1[j]:.6f}")

# Check month-end vs next-day fill on 2008 T1 switch
m08 = (idx >= "2007-11-25") & (idx <= "2008-01-10")
print("T1 around Dec 2007 / Jan 2008:")
for j in np.flatnonzero(m08):
    if tr_t1[j] > 0 or (j > 0 and t1_arr[j] != t1_arr[j-1]):
        print(f"  i={j} {idx[j].date()}: target={t1_arr[j]:.1f}, wt={wt_t1[j]:.4f}, tr={tr_t1[j]:.4f}")

print("\n=== PROBE 3: T5 INITIAL STATE & EDGE-CASE CHECK ===")
# Check T5 state on START if initialized to 0.0 vs 1.0
def t5_init(I, init_state):
    m = I.rolling(200).mean(); above = (I > m).values; mv = m.values; n = len(I); out = np.full(n, np.nan); state = init_state; ua = 0; ub = 0
    for i in range(n):
        if np.isnan(mv[i]): continue
        ua = ua + 1 if above[i] else 0; ub = ub + 1 if not above[i] else 0
        if ua >= 5: state = 1.0
        elif state == 1.0 and ub >= 5: state = 0.5
        if state < 1.0 and ua < 5 and i >= 5 and not np.isnan(mv[i - 5]) and mv[i] < mv[i - 5]: state = 0.0
        out[i] = state
    return out
m_start = I_base.index >= r5.START
diff_init = (t5_init(I_base, 1.0)[m_start] != t5_init(I_base, 0.0)[m_start]).sum()
print(f"T5 init_state=1.0 vs 0.0 differences after {r5.START}: {diff_init} days")
# Check T5 transitions: how many days spent in 1.0, 0.5, 0.0
t5s = D["T"]["T5"]
print(f"T5 target share: 1.0={(t5s==1.0).mean():.3f}, 0.5={(t5s==0.5).mean():.3f}, 0.0={(t5s==0.0).mean():.3f}")

print("\n=== PROBE 4: SLOT WEIGHT DRIFT IN I2 AND SLEEVE WEIGHT DRIFT IN I1 / HOLD12 ===")
# Re-run sim_slots tracking individual slot values for I2
RA = D["ind"]; rc = D["rf"]; assign = D["A2"]; n, ns = assign.shape
val = np.full(ns, 1.0 / ns); cur = np.full(ns, -1); c = 5.0 / 1e4 * 2
slot_shares = np.empty((n, ns))
for t in range(n):
    for s in range(ns): val[s] *= 1 + (rc[t] if cur[s] < 0 else RA[t, cur[s]])
    if t - 1 >= 0:
        want = assign[t - 1]
        for s in range(ns):
            if want[s] != cur[s]:
                val[s] *= (1 - c) if want[s] < 0 else 1 / (1 + c); cur[s] = want[s]
    slot_shares[t] = val / val.sum()
held_m = (idx >= "2006-06-01") & (idx <= "2026-06-30")
print(f"I2 slot shares at 1927-08-01: {np.round(slot_shares[0], 4)}")
print(f"I2 slot shares at 2006-06-01: {np.round(slot_shares[np.flatnonzero(held_m)[0]], 4)}")
print(f"I2 slot shares at 2026-06-30: {np.round(slot_shares[np.flatnonzero(held_m)[-1]], 4)}")
print(f"I2 slot shares mean over held: {np.round(slot_shares[held_m].mean(axis=0), 4)}")
print(f"I2 max single-slot share over held: {slot_shares[held_m].max():.4f}, min: {slot_shares[held_m].min():.4f}")

# Check I1 and HOLD12 sleeve drift
k12 = D["TI"].shape[1]
parts_i1 = [r5.sim_ret(D["ind"][:, j], D["rf"], D["TI"][:, j], 5.0, lag=1, start=1.0 / k12)[0] for j in range(k12)]
eq_i1_mat = np.column_stack(parts_i1)
sh_i1 = eq_i1_mat / eq_i1_mat.sum(axis=1, keepdims=True)
parts_h12 = [r5.sim_ret(D["ind"][:, j], D["rf"], np.ones(len(idx)), 5.0, lag=1, start=1.0 / k12)[0] for j in range(k12)]
eq_h12_mat = np.column_stack(parts_h12)
sh_h12 = eq_h12_mat / eq_h12_mat.sum(axis=1, keepdims=True)
i_h0 = np.flatnonzero(held_m)[0]; i_h1 = np.flatnonzero(held_m)[-1]
print(f"I1 12-sleeve share range at 2006-06-01: [{sh_i1[i_h0].min():.4f}, {sh_i1[i_h0].max():.4f}] (ideal 0.0833)")
print(f"I1 12-sleeve share range at 2026-06-30: [{sh_i1[i_h1].min():.4f}, {sh_i1[i_h1].max():.4f}]")
print(f"HOLD12 12-sleeve share range at 2006-06-01: [{sh_h12[i_h0].min():.4f}, {sh_h12[i_h0].max():.4f}]")
print(f"HOLD12 12-sleeve share range at 2026-06-30: [{sh_h12[i_h1].min():.4f}, {sh_h12[i_h1].max():.4f}]")

# Compare I2 (drifted slots) vs I2_rebal (rebalanced to 1/3 each whenever a switch happens or at month-end)
# Specifically: what if I2 rebalanced to 1/3 each when entering from cash (all 3 slots) or when switching?
# Let's check I2 starting fresh at 2006-06-01 vs carried from 1927!
eq_i2_full, _, _ = r5.run_rule("I2", 5.0, lag=1)
m_i2_held = r5.met(eq_i2_full, "2006-06-01", "2026-06-30")
# Also simulate I2 with equal-weight reset at 2006-05-31 (i.e. if slots were 1/3 each entering held-back)
val2 = np.full(ns, 1.0 / ns); cur2 = np.full(ns, -1); eq_i2_eq = np.empty(n)
for t in range(n):
    if idx[t] == pd.Timestamp("2006-06-01"):
        val2[:] = val2.sum() / ns  # hypothetical 1/3 reset at start of held-back
    for s in range(ns): val2[s] *= 1 + (rc[t] if cur2[s] < 0 else RA[t, cur2[s]])
    if t - 1 >= 0:
        want = assign[t - 1]
        for s in range(ns):
            if want[s] != cur2[s]:
                val2[s] *= (1 - c) if want[s] < 0 else 1 / (1 + c); cur2[s] = want[s]
    eq_i2_eq[t] = val2.sum()
m_i2_eq_held = r5.met(eq_i2_eq, "2006-06-01", "2026-06-30")
print(f"I2 held (actual drifted slots): CAGR={m_i2_held['cagr']*100:.2f}%, SR={m_i2_held['sharpe']:.3f}, MDD={m_i2_held['maxdd']*100:.2f}%")
print(f"I2 held (1/3 reset at 2006-06-01): CAGR={m_i2_eq_held['cagr']*100:.2f}%, SR={m_i2_eq_held['sharpe']:.3f}, MDD={m_i2_eq_held['maxdd']*100:.2f}%")

print("\n=== PROBE 5: CHECK ALL 8 RULES + BENCHMARKS AT 5 bps (NO SHUFFLES) ===")
eq_h, wt_h, tr_h = r5.run_rule("HOLD", 5.0)
eq_h12, wt_h12, tr_h12 = r5.run_rule("HOLD12", 5.0)
mh = r5.met(eq_h, "2006-06-01", "2026-06-30")
mh12 = r5.met(eq_h12, "2006-06-01", "2026-06-30")
print(f"HOLD   held: CAGR={mh['cagr']*100:+.2f}%, SR={mh['sharpe']:.3f}, MDD={mh['maxdd']*100:.2f}%")
print(f"HOLD12 held: CAGR={mh12['cagr']*100:+.2f}%, SR={mh12['sharpe']:.3f}, MDD={mh12['maxdd']*100:.2f}%")
X5 = {}
for name in r5.NAMES:
    eq, wt, tr = r5.run_rule(name, 5.0)
    X5[name] = r5.ex(eq)
    m_dev = r5.met(eq, None, "2006-05-31")
    m_held = r5.met(eq, "2006-06-01", "2026-06-30")
    act_dev = R.activity(eq, wt, tr, idx, None, "2006-05-31", r5.PPY)
    act_held = R.activity(eq, wt, tr, idx, "2006-06-01", "2026-06-30", r5.PPY)
    b_held = mh12 if name == "I1" else mh
    dd_ratio = abs(m_held["maxdd"]) / abs(b_held["maxdd"])
    m1 = (m_held["sharpe"] > b_held["sharpe"]) and (dd_ratio <= 0.6)
    print(f"  {name}: dev_wt={act_dev['avg_weight']:.3f}, held_wt={act_held['avg_weight']:.3f} | "
          f"held CAGR={m_held['cagr']*100:+.2f}%, SR={m_held['sharpe']:.3f}, MDD={m_held['maxdd']*100:.2f}%, dd_rat={dd_ratio:.3f}, m1={m1}")

# Check PBO and DSR at 5 bps
M5 = np.column_stack([X5[n] for n in r5.NAMES])
pbo5 = R.pbo_cscv(M5, 16, "earliest")
pbo5_lat = R.pbo_cscv(M5, 16, "latest")
sd5 = float(np.std([R.sharpe_pp(X5[n]) for n in r5.NAMES], ddof=1))
print(f"\n5 bps PBO (drop earliest): {pbo5}")
print(f"5 bps PBO (drop latest)  : {pbo5_lat}")
print(f"5 bps DSR (N=44, sd={sd5:.6f}):")
for name in r5.NAMES:
    dsr, sr0 = R.deflated_sharpe(X5[name], 44, sd5)
    print(f"  {name}: SR_ann={R.sharpe_pp(X5[name])*math.sqrt(252):.3f}, DSR={dsr:.4f} (sr0_ann={sr0*math.sqrt(252):.3f})")

print("\n=== PROBE 6: CHECK SHUFFLE TRADE COUNT & EXPOSURE (20 DRAWS, 5 bps) ===")
for name in r5.NAMES:
    eq, wt, tr = r5.run_rule(name, 5.0)
    real_sides = int((tr > R.DUST * np.r_[1.0, eq[:-1]]).sum())
    real_wt = float(wt.mean())
    rng = np.random.default_rng(7)
    s_sides, s_wt = [], []
    for _ in range(20):
        e, w, t_ = r5.run_rule(name, 5.0, target=r5.null_target(name, rng))
        s_sides.append(int((t_ > R.DUST * np.r_[1.0, e[:-1]]).sum()))
        s_wt.append(float(w.mean()))
    print(f"  {name}: real sides={real_sides:4d}, wt={real_wt:.4f} | shuf(20) mean sides={np.mean(s_sides):6.1f}, wt={np.mean(s_wt):.4f}")

print("\n=== PROBE 7: INDEPENDENT RE-COMPUTATION OF HOLD AND T1 FROM RAW CSV (5 bps) ===")
# Read raw clean CSV directly without importing any run_05 or rig2 helper
raw = pd.read_csv("/home/user/workspace/rig/stocks_free/french/clean/F-F_Research_Data_Factors_daily__main.csv")
raw["dt"] = pd.to_datetime(raw["date"].astype(str), format="%Y%m%d")
raw = raw.set_index("dt").sort_index()
mkt_ret = (raw["Mkt-RF"] + raw["RF"]) / 100.0
bill_ret = raw["RF"] / 100.0
idx_tr = (1.0 + mkt_ret).cumprod()

# Month-end dates: last trading day of each calendar month
ym = idx_tr.index.to_period("M")
is_me = np.append(ym[1:] != ym[:-1], True)
me_vals = idx_tr[is_me]
me_sma10 = me_vals.rolling(10).mean()
me_sig = (me_vals > me_sma10).astype(float).where(me_sma10.notna())
daily_sig = me_sig.reindex(idx_tr.index).ffill()

# Slice test period >= 1927-08-01
test_mask = idx_tr.index >= pd.Timestamp("1927-08-01")
dt_test = idx_tr.index[test_mask]
ra_t = mkt_ret.values[test_mask]
rc_t = bill_ret.values[test_mask]
sig_t = daily_sig.values[test_mask]

def indep_sim(ra_arr, rc_arr, tgt_arr, bps_per_side=5.0, sides=2):
    """Independent 0/1 cash-or-stock simulator: signal on day t fills at close of day t+1."""
    cost = bps_per_side / 1e4 * sides
    n = len(ra_arr)
    eq = np.empty(n)
    in_mkt = False
    val = 1.0
    for t in range(n):
        val *= (1.0 + ra_arr[t]) if in_mkt else (1.0 + rc_arr[t])
        if t >= 1:
            want_in = bool(tgt_arr[t - 1] > 0.5)
            if want_in and not in_mkt:
                val /= (1.0 + cost)
                in_mkt = True
            elif (not want_in) and in_mkt:
                val *= (1.0 - cost)
                in_mkt = False
        eq[t] = val
    return pd.Series(eq, index=dt_test)

def indep_metrics(eq_ser, rf_ser, lo, hi):
    # Prepend base equity = 1.0 one day before first test date
    base_dt = eq_ser.index[0] - pd.Timedelta(days=1)
    eqp = pd.concat([pd.Series([1.0], index=[base_dt]), eq_ser])
    if lo is None:
        sub = eqp.loc[:hi]
    else:
        pos0 = eqp.index.searchsorted(pd.Timestamp(lo), side="left") - 1
        pos1 = eqp.index.searchsorted(pd.Timestamp(hi), side="right")
        sub = eqp.iloc[pos0:pos1]
    r = sub.values[1:] / sub.values[:-1] - 1.0
    rf_sub = rf_ser.reindex(sub.index[1:]).values
    ex_r = r - rf_sub
    years = len(r) / 252.0
    cagr = (sub.values[-1] / sub.values[0]) ** (1.0 / years) - 1.0
    sr = ex_r.mean() / ex_r.std(ddof=1) * math.sqrt(252.0)
    peak = np.maximum.accumulate(sub.values)
    mdd = float((sub.values / peak - 1.0).min())
    return cagr, sr, mdd

eq_hold_ind = indep_sim(ra_t, rc_t, np.ones(len(ra_t)), 5.0, 2)
eq_t1_ind = indep_sim(ra_t, rc_t, sig_t, 5.0, 2)
rf_ser_t = pd.Series(rc_t, index=dt_test)

eq_hold_r5 = r5.run_rule("HOLD", 5.0)[0]
eq_t1_r5 = r5.run_rule("T1", 5.0)[0]

print(f"Max abs equity diff over 99 years: HOLD={np.max(np.abs(eq_hold_ind.values - eq_hold_r5)):.3e}, T1={np.max(np.abs(eq_t1_ind.values - eq_t1_r5)):.3e}")

for sl_name, (lo, hi) in [("dev", (None, "2006-05-31")), ("held", ("2006-06-01", "2026-06-30"))]:
    for label, ind_eq, r5_eq in [("HOLD", eq_hold_ind, eq_hold_r5), ("T1", eq_t1_ind, eq_t1_r5)]:
        c1_, s1_, d1_ = indep_metrics(ind_eq, rf_ser_t, lo, hi)
        m_r5 = r5.met(r5_eq, lo, hi)
        print(f"  {sl_name:4s} {label:4s} | indep: CAGR={c1_*100:+.4f}%, SR={s1_:.6f}, MDD={d1_*100:.4f}% | "
              f"run_05: CAGR={m_r5['cagr']*100:+.4f}%, SR={m_r5['sharpe']:.6f}, MDD={m_r5['maxdd']*100:.4f}% | "
              f"diff=({(c1_-m_r5['cagr']):.2e}, {(s1_-m_r5['sharpe']):.2e}, {(d1_-m_r5['maxdd']):.2e})")

print("\n=== PROBE 8: I2 REBALANCED ON CASH RE-ENTRY vs DRIFTED SLOTS (5 bps) ===")
# What if I2 resets its 3 cash slots to equal 1/3 when entering from all-cash (which is literally free in cash!)?
val_c = np.full(ns, 1.0 / ns); cur_c = np.full(ns, -1); eq_i2_cashrebal = np.empty(n); shares_c = np.empty((n, ns))
for t in range(n):
    for s in range(ns): val_c[s] *= 1 + (rc[t] if cur_c[s] < 0 else RA[t, cur_c[s]])
    if t - 1 >= 0:
        want = assign[t - 1]
        # When currently all in cash, pooling cash equally into 1/3 per slot costs nothing
        if (cur_c < 0).all() and (want >= 0).all():
            val_c[:] = val_c.sum() / ns
        for s in range(ns):
            if want[s] != cur_c[s]:
                val_c[s] *= (1 - c) if want[s] < 0 else 1 / (1 + c); cur_c[s] = want[s]
    eq_i2_cashrebal[t] = val_c.sum(); shares_c[t] = val_c / val_c.sum()

m_i2_cr_held = r5.met(eq_i2_cashrebal, "2006-06-01", "2026-06-30")
m_i2_cr_all = r5.met(eq_i2_cashrebal, None, "2026-09-30")
m_i2_dr_all = r5.met(eq_i2_full, None, "2026-09-30")
print(f"I2 drifted    all : CAGR={m_i2_dr_all['cagr']*100:.2f}%, SR={m_i2_dr_all['sharpe']:.3f}, MDD={m_i2_dr_all['maxdd']*100:.2f}%")
print(f"I2 cash-rebal all : CAGR={m_i2_cr_all['cagr']*100:.2f}%, SR={m_i2_cr_all['sharpe']:.3f}, MDD={m_i2_cr_all['maxdd']*100:.2f}%")
print(f"I2 drifted    held: CAGR={m_i2_held['cagr']*100:.2f}%, SR={m_i2_held['sharpe']:.3f}, MDD={m_i2_held['maxdd']*100:.2f}%, dd_rat={abs(m_i2_held['maxdd'])/abs(mh['maxdd']):.3f}")
print(f"I2 cash-rebal held: CAGR={m_i2_cr_held['cagr']*100:.2f}%, SR={m_i2_cr_held['sharpe']:.3f}, MDD={m_i2_cr_held['maxdd']*100:.2f}%, dd_rat={abs(m_i2_cr_held['maxdd'])/abs(mh['maxdd']):.3f}")
print(f"I2 cash-rebal max slot share in held: {shares_c[held_m].max():.4f}, min: {shares_c[held_m].min():.4f}")

# Check PBO with I2 cash-rebal replacing I2 drifted
X5_cr = dict(X5); X5_cr["I2"] = r5.ex(eq_i2_cashrebal)
M5_cr = np.column_stack([X5_cr[n] for n in r5.NAMES])
print("5 bps PBO with I2 cash-rebal:", R.pbo_cscv(M5_cr, 16, "earliest"))

