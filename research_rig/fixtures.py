"""Engine checks with known answers. Must pass before any result counts."""
import numpy as np, pandas as pd, hashlib, json
from engine import simulate, metrics
from rules import RULES
ok=True
def check(name,cond,detail=""):
    global ok; ok&=bool(cond); print(("PASS " if cond else "FAIL ")+name, detail)
# 1 hand-worked profit: opens 100,100,110,120 ; decide in at close0, fill open1=100; decide out at close2, fill open3=120 -> +20%
o=np.array([100.,100,110,120,120]); c=np.array([100.,105,115,120,120]); tgt=np.array([1.,1,0,0,0])
eq,wt,tr=simulate(o,c,tgt,0.0)
check("1 hand-worked profit", abs(eq[-1]-1.2)<1e-12, f"equity {eq[-1]:.6f} expected 1.200000")
# 2 hand-worked costs at 100 bps a side: buy x where x*1.01=1 -> x=0.990099, units=0.00990099; sell at 120 -> 1.188119*0.99=1.176238
eq,wt,tr=simulate(o,c,tgt,100.0)
exp=(1/1.01)/100*120*0.99
check("2 hand-worked costs", abs(eq[-1]-exp)<1e-12, f"equity {eq[-1]:.6f} expected {exp:.6f}")
# 3 buy and hold equals asset return less one side of cost
rng=np.random.default_rng(1); c2=100*np.cumprod(1+rng.normal(0,0.02,500)); o2=np.r_[c2[0],c2[:-1]]
eq,wt,tr=simulate(o2,c2,np.ones(500),25.0)
exp=(1/1.0025)/o2[1]*c2[-1]
check("3 buy and hold", abs(eq[-1]-exp)<1e-9, f"equity {eq[-1]:.6f} expected {exp:.6f}")
# 4 peeking: a rule that knows tomorrow's close must beat the honest one; honest signal shifted one bar must differ
s=pd.Series(c2); honest=RULES["S50"](s).values
peek=(s.shift(-1)>s).astype(float).values
e_h=simulate(o2,c2,honest,0)[0][-1]; e_p=simulate(o2,c2,peek,0)[0][-1]; e_s=simulate(o2,c2,np.r_[np.nan,honest[:-1]],0)[0][-1]
check("4 peeking is visible", e_p>3*e_h and abs(e_s-e_h)>1e-9, f"honest {e_h:.3f} peeking {e_p:.3f} shifted {e_s:.3f}")
# 5 random entries on a driftless series lose about their costs
res=[]; cost=25.0
for seed in range(300):
    r=np.random.default_rng(seed); cz=100*np.exp(np.cumsum(r.normal(-0.0002,0.02,1000))); oz=np.r_[cz[0],cz[:-1]]   # zero expected simple return
    tg=(r.random(1000)<0.5).astype(float); tg=np.repeat(tg[::10],10)
    eq,wt,tr=simulate(oz,cz,tg,cost); res.append((eq[-1]-1, tr.sum()*cost/1e4))
res=np.array(res); se=res[:,0].std()/np.sqrt(len(res))
check("5 random entries lose about costs", abs(res[:,0].mean()+res[:,1].mean())<3*se, f"mean result {res[:,0].mean():.4f}, mean cost paid {res[:,1].mean():.4f}, 3 standard errors {3*se:.4f}")
# 9 cash never below zero, weight never above 1
eq,wt,tr=simulate(o2,c2,np.ones(500),90.0)
check("9 no leverage", wt.max()<=1+1e-9 and eq.min()>0, f"max weight {wt.max():.6f}")
# 15 determinism
h=lambda: hashlib.sha256(simulate(o2,c2,honest,25.0)[0].tobytes()).hexdigest()
check("15 determinism", h()==h(), h()[:16])
print("ALL PASS" if ok else "SOME FAILED")
