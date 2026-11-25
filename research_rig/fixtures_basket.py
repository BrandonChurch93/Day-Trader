"""Checks of the basket engine that must pass before replay 04 is run."""
import numpy as np
from basket import simulate_basket
from engine import simulate
ok=True
def chk(name,cond):
    global ok; ok&=bool(cond); print(("PASS " if cond else "FAIL ")+name)
rng=np.random.default_rng(1); T=400
c=100*np.cumprod(1+rng.normal(0,0.03,T)); o=np.r_[c[0],c[:-1]*(1+rng.normal(0,0.002,T-1))]
tgt=(rng.random(T)>0.5).astype(float); tgt=np.repeat(tgt[::7],7)[:T]
# 1 one coin, 0/1 targets, equals the single-asset engine
e1=simulate(o,c,tgt,30)[0]; e2=simulate_basket(o[:,None],c[:,None],tgt[:,None],[30],np.array([0.10]))[0]
chk("one coin equals single-asset engine", np.allclose(e1,e2,rtol=1e-9))
# 2 hand-worked: two coins, half each, bought at open of day 1, cost 100 bps
O=np.array([[10,20],[10,20],[11,20]],float); C=np.array([[10,20],[11,20],[12,18]],float); W=np.array([[.5,.5],[.5,.5],[.5,.5]])
e,w,tr,ev=simulate_basket(O,C,W,[100,100],np.array([.2,.2]))
x=0.5/1.01; cash=1-2*x*1.01; hand1=cash+x/10*11+x/20*20; hand2=cash+x/10*12+x/20*18
chk("hand-worked two coins", abs(e[1]-hand1)<1e-12 and abs(e[2]-hand2)<1e-12)
# 3 zero cost, always fully invested equal weight in two coins with no rebalance = average of the two price ratios
O=np.c_[o,o[::-1]]; C=np.c_[c,c[::-1]]; W=np.full((T,2),0.5)
e=simulate_basket(O,C,W,[0,0],np.array([9.,9.]))[0]
chk("no-rebalance hold equals average of price ratios", abs(e[-1]-0.5*(C[-1,0]/O[1,0]+C[-1,1]/O[1,1]))<1e-9)
# 4 peeking gives a different, better result
ret=np.r_[c[1:]/o[1:]-1,0]; peek=(ret>0).astype(float)   # at the close of t it knows day t+1's open-to-close move
honest=np.r_[0,peek[:-1]]                                    # the same signal one day late, which is what can be known
ep=simulate_basket(o[:,None],c[:,None],peek[:,None],[0],np.array([.1]))[0][-1]; eh=simulate_basket(o[:,None],c[:,None],honest[:,None],[0],np.array([.1]))[0][-1]
chk("peeking rule beats the same rule run honestly", ep>eh*2)
# 5 delisting: coin's data ends while held; sold at last close less cost and haircut
O=np.array([[10.],[10.],[np.nan],[np.nan]]); C=np.array([[10.],[8.],[np.nan],[np.nan]]); W=np.ones((4,1))
e,w,tr,ev=simulate_basket(O,C,W,[100],np.array([.1]),last_day=np.array([1]),delist_haircut=0.5)
u=(1/1.01)/10; chk("delisting exit with haircut", abs(e[-1]-u*8*0.5*0.99)<1e-12 and len(ev)==1)
# 6 costs: random daily flips lose about their costs
flip=(rng.random(T)>0.5).astype(float); a=simulate_basket(o[:,None],c[:,None],flip[:,None],[0],np.array([.1])); b=simulate_basket(o[:,None],c[:,None],flip[:,None],[50],np.array([.1]))
ntr=(a[2]>0).sum(); chk("cost drag about trades times cost", abs(np.log(b[0][-1]/a[0][-1])+ntr*0.005)<0.02*ntr*0.005+1e-3)
# 7 never spends more cash than there is, weights never above 1
W=np.full((T,2),0.9); e,w,tr,ev=simulate_basket(np.c_[o,o],np.c_[c,c],W,[30,30],np.array([.05,.05]))
chk("no leverage", w.sum(1).max()<=1+1e-9)
# ---------------------------------------------------------------- added for run_04.py (2026-11-25)
import sys, pandas as pd, rig2 as R
from basket import sim_batch, month_members, k5_weight, hold_on_weekday, circular_shift_in_span
# 8 the batched engine with the old to/from-zero exception equals simulate_basket on random inputs, also batched
worst = 0.0; worstb = 0.0
for seed in range(300):
    r = np.random.default_rng(1000 + seed); n = 250; N = int(r.integers(1, 7))
    C8 = 100 * np.exp(np.cumsum(r.normal(0, 0.03, (n, N)), 0)); O8 = C8 * np.exp(r.normal(0, 0.01, (n, N)))
    O8[r.random((n, N)) < 0.1] = np.nan
    ld = np.full(N, 10 ** 9)
    if seed % 3 == 0:
        i = int(r.integers(0, N)); ld[i] = int(r.integers(50, n - 2)); C8[ld[i] + 1:, i] = np.nan; O8[ld[i] + 1:, i] = np.nan
    W8 = np.repeat(r.choice([0, .25, .5, .75, 1.0], (n // 5 + 1, N)), 5, 0)[:n] / N
    cost = r.choice([0, 7, 30, 95], N).astype(float); band = np.full(N, float(r.choice([0.01, 0.05, 0.2])) / N); hc = float(r.choice([0, 0.5]))
    a = simulate_basket(O8, C8, W8, cost, band, last_day=ld, delist_haircut=hc)[0]
    b = sim_batch(O8, C8, W8, cost, band, last_day=ld, delist_haircut=hc, zero_exception=True)["eq"]
    worst = max(worst, np.abs(a / b - 1).max())
    if seed % 10 == 0:
        W2 = np.stack([W8, W8[::-1], W8]); bb = sim_batch(O8, C8, W2, cost, band, last_day=ld, delist_haircut=hc, zero_exception=True)["eq"]
        worstb = max(worstb, np.abs(bb[0] / b - 1).max(), np.abs(bb[2] / b - 1).max())
chk(f"batched engine (old exception on) equals simulate_basket, 300 random inputs, gap {worst:.1e}, batch gap {worstb:.1e}", worst < 1e-10 and worstb < 1e-12)
# 9 with the literal band (A12), one coin at zero cost, it equals rig2.simulate with bars that cannot fill
worst = 0.0
for seed in range(300):
    r = np.random.default_rng(2000 + seed); n = 300; cz = 100 * np.exp(np.cumsum(r.normal(0, 0.02, n))); oz = cz * np.exp(r.normal(0, 0.003, n))
    tg = np.repeat(r.choice([0, .25, .5, .75, 1.0], n // 5), 5); cf = r.random(n) > 0.1; o9 = np.where(cf, oz, np.nan)
    a = R.simulate(oz, cz, tg, 0.0, band=0.1, can_fill=cf)[0]; b = sim_batch(o9[:, None], cz[:, None], tg[:, None], [0.0], [0.1])["eq"]
    worst = max(worst, np.abs(a / b - 1).max())
chk(f"literal band equals rig2.simulate for one coin at zero cost (gap {worst:.1e})", worst < 1e-10)
# 10 literal band (A12): a position that has drifted below the band with target zero is kept while the pair is in
# its basket, and sold when the pair leaves the basket (the plan says such a pair "is sold")
O10 = np.full((6, 1), 100.); C10 = np.full((6, 1), 100.); C10[2:] = 10.; O10[3:] = 10.
W10 = np.array([[0.5], [0.5], [0.0], [0.0], [0.0], [0.0]]); mem = np.array([[1], [1], [1], [0], [0], [0]], bool)
r3 = sim_batch(O10, C10, W10, [0], [0.1], detail=True); r4 = sim_batch(O10, C10, W10, [0], [0.1], member=mem, detail=True)
r5 = sim_batch(O10, C10, W10, [0], [0.1], zero_exception=True, detail=True)
chk("literal band keeps a drifted position with target zero; sold on leaving the basket; old exception counted",
    r3["wt"][-1, 0] > 0.05 and r4["wt"][-1, 0] == 0.0 and r4["traded"][4, 0] > 0 and r5["wt"][-1, 0] == 0.0 and r3["old_exception_would_fire"] == 3)
# 11 an order due on a day the pair did not trade waits, then uses the newest target
O11 = np.array([[10.], [np.nan], [12.], [13.]]); C11 = np.array([[10.], [11.], [12.], [13.]]); W11 = np.array([[1.], [0.5], [0.5], [0.5]])
r11 = sim_batch(O11, C11, W11, [0], [0.1], detail=True)
chk("no trade on the fill day: order waits, fills next traded open with newest target", r11["traded"][1, 0] == 0 and abs(r11["traded"][2, 0] - 0.5) < 1e-12 and r11["eq"][1] == 1.0 and r11["waits"] == 1)
# 12 hold once: bought at the first fill day only, never traded again
o12 = np.c_[100 * np.exp(np.cumsum(rng.normal(0, 0.03, 50)))]; c12 = o12 * 1.01; rb = np.zeros(50, bool); rb[1] = True
r12 = sim_batch(o12, c12, np.ones((50, 1)), [40], [0.0], rebal=rb, detail=True)
chk("hold benchmark bought once", abs(r12["eq"][-1] - c12[-1, 0] / o12[1, 0] / 1.004) < 1e-12 and r12["sides"] == 1)
# 13 membership uses nothing from the month it selects for
r = np.random.default_rng(5); n = 700; N = 30; names = [f"P{i:02d}" for i in range(N)]
base = 100 * np.exp(np.cumsum(r.normal(0, 0.04, (n, N)), 0)); base[:, 5] = base[:, 4] * np.exp(r.normal(0, 0.002, n))   # a copy of P04
base[:, 7] = 1.0 * np.exp(r.normal(0, 0.0005, n))                                                                       # a pegged coin
TR = r.random((n, N)) > 0.02; TR[:, 9] = r.random(n) > 0.3                                                             # P09 rarely trades
first = np.zeros(N, int); first[11] = 450                                                                              # P11 too young
DV = np.where(TR, r.lognormal(10, 1, (n, N)) * np.linspace(1, 3, N)[None], 0.0)
Cm = base.copy(); Cm[:first[11], 11] = np.nan; DV[:first[11], 11] = 0; TR[:first[11], 11] = False
P = dict(names=names, C=Cm, CM=Cm, DV=DV, TR=TR, first=first)
d = 600; keep, info = month_members(P, d)
P2 = dict(P, CM=Cm.copy(), DV=DV.copy(), TR=TR.copy()); P2["CM"][d:] *= r.lognormal(0, 1, (n - d, N)); P2["DV"][d:] = r.lognormal(14, 3, (n - d, N)); P2["TR"][d:] = r.random((n - d, N)) > 0.5
keep2, _ = month_members(P2, d)
P3 = dict(P, DV=DV.copy()); P3["DV"][d - 1] *= r.lognormal(0, 3, N); P3["DV"][d - 60:d - 1] *= r.lognormal(0, 3, (59, N)); keep3, _ = month_members(P3, d)
chk("membership unchanged when data from the selected month on are changed", keep == keep2 and keep != keep3)
nk = [names[j] for j in keep]
chk("membership filters: copy, peg, inactive, young left out", "P05" not in nk and "P04" in nk and "P07" not in nk and "P09" not in nk and "P11" not in nk and len(nk) == N - 4 and info["copies_dropped"].get("P05") == "P04")
# 14 K5 weights on a hand-made series
c14 = np.r_[np.full(200, 100.0), np.linspace(100, 150, 40)]; w = k5_weight(c14)
x = c14[-180:][::-1]; i = np.arange(180); hand = 0
for hs, hl in ((1, 5), (2.5, 10), (5, 20), (10, 40)):
    a = 2.0 ** (-i / hs); b = 2.0 ** (-i / hl); hand += (x @ a / a.sum()) >= (x @ b / b.sum())
c14b = np.r_[np.full(200, 100.0), np.linspace(100, 60, 40)]; flat = k5_weight(np.full(200, 5.0))
# (an exactly flat series is not used: the two averages then differ only by rounding, so ties are not a stable test)
c14c = 100 * np.exp(np.cumsum(np.random.default_rng(9).normal(0, 0.03, 400))); w14c = k5_weight(c14c); handc = []
for t in range(179, 400):
    x = c14c[t - 179:t + 1][::-1]; hh = 0
    for hs, hl in ((1, 5), (2.5, 10), (5, 20), (10, 40)):
        a = 2.0 ** (-i / hs); b = 2.0 ** (-i / hl); hh += (x @ (a / a.sum())) >= (x @ (b / b.sum()))
    handc.append(hh / 4)
chk("K5 weights: rising 1, falling 0, hand loop on a random series, nan before 180 closes",
    w[-1] == 1.0 and k5_weight(c14b)[-1] == 0.0 and np.array_equal(w14c[179:], handc) and np.isnan(w[178]) and not np.isnan(w[179]) and w[-1] == hand / 4)
zz = np.r_[np.full(200, 100.0), 100 + 10 * np.sin(np.arange(200) / 6)]; wz = k5_weight(zz); mixed = sorted(set(np.round(wz[250:] * 4).astype(int)))
dts = pd.date_range("2026-01-01", periods=len(zz)); hw = hold_on_weekday(wz, dts)
chk(f"K5 takes in-between values {mixed} and changes only on Wednesdays", len(mixed) >= 3 and all(dts[j].weekday() == 2 for j in range(1, len(hw)) if hw[j] != hw[j - 1] and not np.isnan(hw[j - 1])))
# 15 circular shift inside each pair's own history keeps its time in market and leaves other rows alone
r = np.random.default_rng(7); good = True
for _ in range(200):
    x = r.choice([0, .25, .5, .75, 1.0], 500); a, b = int(r.integers(0, 200)), int(r.integers(300, 500)); y, did = circular_shift_in_span(x, a, b, r)
    good &= did and np.isclose(y[a:b + 1].sum(), x[a:b + 1].sum()) and sorted(y[a:b + 1]) == sorted(x[a:b + 1]) and np.array_equal(y[:a], x[:a]) and np.array_equal(y[b + 1:], x[b + 1:])
chk("circular shift keeps each coin's time in market and touches only its own history", good)
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
