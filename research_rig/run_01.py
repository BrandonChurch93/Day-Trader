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
out={"assets":{}}
for a in ["BTCUSD","ETHUSD"]:
    A={"rules":{}}; R={}
    for v,fee in VENUES.items():
        c=fee+SLIP; b=bh(a,c)
        A.setdefault("bh",{})[v]={k:metrics(bh_slice(a,c,lo,hi).values) for k,(lo,hi) in SL.items()}
    for rule in RULES:
        rr={"venues":{}}
        for v,fee in VENUES.items():
            c=fee+SLIP; eq,wt,tr,t=run(a,rule,c)
            rr["venues"][v]={k:slice_metrics(eq,wt,tr,lo,hi) for k,(lo,hi) in SL.items()}
            if v=="Alpaca": R[rule]=rets(eq); eqA=eq; tA=t
            if v=="Binance.US": R.setdefault("_bin",{})[rule]=rets(eq)
        b0=bh(a,SLIP); sb=metrics(b0.values)["sharpe"]
        rr["be_vs_bh_bps"]=breakeven(a,rule,lambda e: metrics(e.values)["sharpe"]-sb)
        rr["be_zero_bps"]=breakeven(a,rule,lambda e: metrics(e.values)["cagr"])
        # shuffled timing at Alpaca cost
        rng=np.random.default_rng(7); d=load(a); dd=d[d.index>=START[a]]; sh=[]
        for i in range(1000):
            ts=shuffle_spells(tA,rng); e=simulate(dd.open.values,dd.close.values,ts,25+SLIP)[0]; sh.append(metrics(e)["sharpe"])
        sh=np.array(sh); s_real=metrics(eqA.values)["sharpe"]
        rr["shuffle_pct"]=float((sh<s_real).mean()); rr["shuffle_median_sharpe"]=float(np.median(sh))
        bA=bh(a,25+SLIP); rr["boot_sharpe_diff_vs_bh"]=[float(x) for x in block_bootstrap_sharpe_diff(rets(eqA),rets(bA))]
        A["rules"][rule]=rr
    names=list(RULES); M=np.column_stack([R[n] for n in names]); A["pbo"]=pbo_cscv(M,16)
    A["_R"]={n:R[n] for n in names}
    out["assets"][a]=A
# portfolios from 2018-03-05, per venue
port={}
for rule in ["P1","P2"]:
    port[rule]={}
    for v,fee in VENUES.items():
        c=fee+SLIP; es=[]
        for a in ["BTCUSD","ETHUSD"]:
            d=load(a); tgt=RULES[rule](d.close); m=d.index>="2018-03-05"; dd=d[m]
            e=simulate(dd.open.values,dd.close.values,tgt[m].values,c,start_cash=0.5)[0]; es.append(pd.Series(e,index=dd.index))
        pe=es[0]+es[1]; bhp=sum(pd.Series(simulate(load(a)[load(a).index>="2018-03-05"].open.values,load(a)[load(a).index>="2018-03-05"].close.values,np.ones(len(es[0])),c,start_cash=0.5)[0],index=es[0].index) for a in ["BTCUSD","ETHUSD"])
        port[rule][v]={k:{"rule":metrics(pe[lo:hi].values),"bh":metrics(bhp[lo:hi].values)} for k,(lo,hi) in SL.items()}
        if v=="Alpaca": out.setdefault("_portR",{})[rule]=rets(pe)
out["port"]=port
# deflated Sharpe across all 20 trials (Alpaca cost), per-period Sharpe std across trials
allr=[out["assets"][a]["_R"][n] for a in out["assets"] for n in RULES]+[out["_portR"][r] for r in ["P1","P2"]]
sd=float(np.std([sharpe_per_period(r) for r in allr],ddof=1)); out["trial_sharpe_std_per_period"]=sd
for a in out["assets"]:
    for n in RULES:
        dsr,sr0=deflated_sharpe(out["assets"][a]["_R"][n],20,sd); out["assets"][a]["rules"][n]["dsr"]=dsr
    del out["assets"][a]["_R"]
for r in ["P1","P2"]: out["port"][r]["dsr"]=deflated_sharpe(out["_portR"][r],20,sd)[0]
del out["_portR"]
out["commit_note"]="run_01.py, seed 7, data bitstamp daily through 2026-11-24"
json.dump(out,open("results_01.json","w"),indent=1,default=float)
print("done")
