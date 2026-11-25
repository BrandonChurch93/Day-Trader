"""X1 second-source cross-check and S1 fill-delay sensitivity for PREREG_01. No new rules."""
import numpy as np, pandas as pd, json
from engine import *
from rules import RULES
from common_01 import *
out={"X1":{}, "S1":{}}
# ---- X1
for a in ["BTCUSD","ETHUSD"]:
    b=load(a); k=pd.read_csv(f"data/kraken_{a}.csv",parse_dates=["date"]).set_index("date"); k=k[k.index<="2026-11-24"]
    j=b.join(k,how="inner",rsuffix="_k"); diff=(j.close_k/j.close-1).abs()*1e4
    X={"days":int(len(j)),"first":str(j.index[0].date()),"last":str(j.index[-1].date()),"close_diff_bps_median":float(diff.median()),"close_diff_bps_p99":float(diff.quantile(0.99)),"close_diff_bps_max":float(diff.max()),"rules":{}}
    spl=b.copy(); spl.loc[k.index.intersection(spl.index),["open","high","low","close"]]=k.loc[k.index.intersection(spl.index),["open","high","low","close"]]
    for rule in ["P1","P2"]:
        res={}
        for name,src in [("bitstamp",b),("kraken",spl)]:
            tgt=RULES[rule](src.close); m=src.index>=k.index[0]; dd=src[m]
            eq,wt,tr=simulate(dd.open.values,dd.close.values,tgt[m].values,30)
            mm=metrics(eq); res[name]=dict(total=mm["total"],sharpe=mm["sharpe"],maxdd=mm["maxdd"],trades=int((tr>0).sum()))
        tb=RULES[rule](b.close)[b.index>=k.index[0]]; tk=RULES[rule](spl.close)[spl.index>=k.index[0]]
        res["days_target_differs"]=int((np.abs(tb.values-tk.values)>1e-9).sum())
        X["rules"][rule]=res
    out["X1"][a]=X
# ---- S1
def hour_open(a):
    h=pd.read_csv(f"data/bitstamp_{a}_1h.csv"); h["dt"]=pd.to_datetime(h.ts,unit="s"); h=h[h.volume>0] if False else h
    h["day"]=h.dt.dt.normalize(); h["hr"]=h.dt.dt.hour
    g=h[h.hr>=1].sort_values("dt").groupby("day").first()
    return g.open, g.hr
for a in ["BTCUSD","ETHUSD"]:
    d=load(a); m=d.index>=START[a]; dd=d[m]; ho,hh=hour_open(a)
    o1=ho.reindex(dd.index); miss=int(o1.isna().sum()); late=int((hh.reindex(dd.index)>1).sum()); o1=o1.fillna(dd.open)
    gap=((o1/dd.open-1).abs()*1e4)
    S={"days":int(len(dd)),"hour_missing_days":miss,"hour_later_than_0100_days":late,"abs_move_first_hour_bps_median":float(gap.median()),"abs_move_first_hour_bps_p90":float(gap.quantile(0.9)),"rules":{}}
    for rule in RULES:
        tgt=RULES[rule](d.close)[m].values; r={}
        for vname,c in [("Alpaca",30),("Binance.US",7)]:
            for variant,(op,tg) in {"base":(dd.open.values,tgt),"hour_late":(o1.values,tgt),"day_late":(dd.open.values,np.r_[np.nan,tgt[:-1]])}.items():
                eq,wt,tr=simulate(op,dd.close.values,tg,c); e=pd.Series(eq,index=dd.index)
                r[f"{vname}|{variant}"]={k:{x:metrics(e[lo:hi].values)[x] for x in ["sharpe","cagr","maxdd"]} for k,(lo,hi) in SL.items() if k in ("all","held")}
        S["rules"][rule]=r
    out["S1"][a]=S
json.dump(out,open("results_01c.json","w"),indent=1,default=float)
for a,X in out["X1"].items():
    print("X1",a,{k:v for k,v in X.items() if k!="rules"})
    for r,v in X["rules"].items(): print("   ",r,v)
for a,S in out["S1"].items():
    print("S1",a,{k:v for k,v in S.items() if k!="rules"})
    for r,v in S["rules"].items():
        print(f"   {r:5s} "+" | ".join(f"{vn[:3]} all SR {v[vn+'|base']['all']['sharpe']:.2f}/{v[vn+'|hour_late']['all']['sharpe']:.2f}/{v[vn+'|day_late']['all']['sharpe']:.2f} held {v[vn+'|base']['held']['sharpe']:.2f}/{v[vn+'|hour_late']['held']['sharpe']:.2f}/{v[vn+'|day_late']['held']['sharpe']:.2f}" for vn in ["Alpaca","Binance.US"]))
