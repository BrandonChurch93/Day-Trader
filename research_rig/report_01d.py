"""Descriptive tables for replay 01. Same trials, no new rules: last-720-day hold comparison and calendar years."""
import numpy as np, pandas as pd, json
from engine import *; from rules import RULES; from common_01 import *
out={}
for a in ["BTCUSD","ETHUSD"]:
    d=load(a); dd=d[d.index>=START[a]]
    w=dd[dd.index>="2024-12-05"]; e=simulate(w.open.values,w.close.values,np.ones(len(w)),30)[0]; m=metrics(e)
    out[a]={"hold_last720":{k:m[k] for k in ["total","sharpe","maxdd"]},"years":{}}
    print(a,"hold 2024-12-05..2026-11-24",{k:round(m[k],3) for k in ["total","sharpe","maxdd"]})
    eqs={r:run(a,r,30)[0] for r in ["P1","P2"]}; eqs["hold"]=bh(a,30)
    for y in range(int(START[a][:4]),2027):
        row={}
        for k,e in eqs.items():
            s=e[str(y)]; prev=e[:str(y-1)]; base=prev.iloc[-1] if len(prev) else s.iloc[0]
            full=pd.concat([pd.Series([base]),s]); row[k]=float(s.iloc[-1]/base-1); row[k+"_dd"]=float((full/full.cummax()-1).min())
        out[a]["years"][y]=row
        print(f"  {y} hold {row['hold']*100:7.1f}% (dd {row['hold_dd']*100:6.1f}%)  P1 {row['P1']*100:7.1f}% (dd {row['P1_dd']*100:6.1f}%)  P2 {row['P2']*100:7.1f}% (dd {row['P2_dd']*100:6.1f}%)")
json.dump(out,open("results_01d.json","w"),indent=1)
