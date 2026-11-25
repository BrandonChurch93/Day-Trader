import numpy as np, pandas as pd, json, math, subprocess, sys
from engine import *
from rules import RULES
VENUES={"Binance.US":2,"Alpaca":25,"Kraken $10k tier":38,"Kraken entry":80,"Coinbase entry":90}; SLIP=5
def load(a):
    d=pd.read_csv(f"data/bitstamp_{a}.csv",parse_dates=["date"]).set_index("date"); return d[d.index<="2026-11-24"]
START={"BTCUSD":"2013-01-01","ETHUSD":"2018-03-05"}
SL={"dev":(None,"2022-12-31"),"held":("2023-01-01","2026-06-30"),"post":("2026-07-01","2026-11-24"),"all":(None,"2026-11-24")}
def run(a, rule, cost, tgt_override=None):
    d=load(a); tgt=RULES[rule](d.close) if tgt_override is None else tgt_override
    m=d.index>=START[a]; dd=d[m]; t=tgt[m].values if tgt_override is None else tgt_override
    # the last pre-start signal is not used: first trade can be at the second bar
    eq,wt,tr=simulate(dd.open.values,dd.close.values,t,cost)
    return pd.Series(eq,index=dd.index),pd.Series(wt,index=dd.index),pd.Series(tr,index=dd.index),t
def slice_metrics(eq,wt,tr,lo,hi):
    e=eq[lo:hi]; m=metrics(e.values); w=wt[lo:hi]; t=tr[lo:hi]
    m["exposure"]=float(w.mean()); m["trades"]=int((t>0).sum()); m["turnover_py"]=float((t/eq.shift(1).reindex(t.index)).sum()/(len(e)/365))
    return m
def bh(a,cost):
    d=load(a); dd=d[d.index>=START[a]]; eq,wt,tr=simulate(dd.open.values,dd.close.values,np.ones(len(dd)),cost); return pd.Series(eq,index=dd.index)
def bh_slice(a,cost,lo,hi):
    d=load(a); dd=d[d.index>=START[a]][lo:hi]; eq,wt,tr=simulate(dd.open.values,dd.close.values,np.ones(len(dd)),cost); return pd.Series(eq,index=dd.index)
def rets(e): return (e/e.shift(1)-1).dropna().values
def breakeven(a,rule,target_fn,lo=0,hi=600):
    f=lambda c: target_fn(run(a,rule,c)[0])
    if f(lo)<=0: return 0.0
    if f(hi)>0: return float(hi)
    for _ in range(30):
        mid=(lo+hi)/2
        if f(mid)>0: lo=mid
        else: hi=mid
    return (lo+hi)/2
