"""Pass-mark evaluation per venue for PREREG_01. Same 20 trials, no new rules.
Marks 3 to 5 (deflated Sharpe, overfitting probability, shuffled timing) worked out at each venue's own cost."""
import numpy as np, pandas as pd, json, sys
from engine import *
from rules import RULES
from common_01 import *
o=json.load(open("results_01.json")); MULT=2; PBO_MAX=0.25   # backtest_min_breakeven_cost_multiple, backtest_max_pbo in config/thresholds.yaml
res={}
for v,fee in VENUES.items():
    c=fee+SLIP; R={}; T={}
    for a in ["BTCUSD","ETHUSD"]:
        for rule in RULES:
            eq,wt,tr,t=run(a,rule,c); R[(a,rule)]=rets(eq); T[(a,rule)]=t
    port={}
    for rule in ["P1","P2"]:
        es=[]
        for a in ["BTCUSD","ETHUSD"]:
            d=load(a); tgt=RULES[rule](d.close); m=d.index>="2018-03-05"; dd=d[m]
            es.append(pd.Series(simulate(dd.open.values,dd.close.values,tgt[m].values,c,start_cash=0.5)[0],index=dd.index))
        port[rule]=rets(es[0]+es[1])
    allr=list(R.values())+list(port.values()); sd=float(np.std([sharpe_per_period(r) for r in allr],ddof=1))
    pbo={a:pbo_cscv(np.column_stack([R[(a,r)] for r in RULES]),16) for a in ["BTCUSD","ETHUSD"]}
    for a in ["BTCUSD","ETHUSD"]:
        d=load(a); dd=d[d.index>=START[a]]
        for rule in RULES:
            rr=o["assets"][a]["rules"][rule]; h=rr["venues"][v]["held"]; b=o["assets"][a]["bh"][v]["held"]
            rng=np.random.default_rng(7); s_real=sharpe_per_period(R[(a,rule)]); cnt=0
            for i in range(1000):
                e=simulate(dd.open.values,dd.close.values,shuffle_spells(T[(a,rule)],rng),c)[0]
                cnt+= sharpe_per_period(e[1:]/e[:-1]-1)<s_real
            dsr=deflated_sharpe(R[(a,rule)],20,sd)[0]
            m1=(h["sharpe"]>b["sharpe"]) and (abs(h["maxdd"])<=0.6*abs(b["maxdd"]))
            m2=rr["be_vs_bh_bps"]>=MULT*c; m3=dsr>0.95; m4=pbo[a]<PBO_MAX; m5=cnt/1000>0.95
            res[f"{v}|{a}|{rule}"]=dict(held_sharpe=h["sharpe"],bh_held_sharpe=b["sharpe"],held_maxdd=h["maxdd"],bh_held_maxdd=b["maxdd"],dd_ratio=abs(h["maxdd"])/abs(b["maxdd"]),
                be_vs_bh=rr["be_vs_bh_bps"],need_be=MULT*c,dsr=dsr,pbo=pbo[a],shuffle=cnt/1000,m1=bool(m1),m2=bool(m2),m3=bool(m3),m4=bool(m4),m5=bool(m5),passed=bool(m1 and m2 and m3 and m4 and m5))
    print(v,"done",flush=True)
    json.dump(res,open("passmarks_01.json","w"),indent=1,default=float)
