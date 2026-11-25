"""Replay 03: intraday rules on hourly bars. PREREG_03_intraday_crypto.md. Writes results_03.json."""
import numpy as np, pandas as pd, json, math, sys
from common_03 import *
import common_01 as c1
from rules import RULES as DAILY_RULES
MULT=2; PBO_MAX=0.25; DROP=0.6; DSR_MIN=0.95; SHUF=0.95   # keys in config/thresholds.yaml
SL={"dev":(None,"2022-12-31"),"held":("2023-01-01","2026-06-30"),"post":("2026-07-01","2026-11-24"),"all":(None,"2026-11-24")}
NAMES=["H1","H2","H3","H4","H5","H6","H7","H8"]; N_TRIALS=36
def drets(e): return (e/e.shift(1)-1).dropna().values
out={"start":{}, "quality":{}, "assets":{}, "n_trials":N_TRIALS}
D={}
for a in ["BTCUSD","ETHUSD"]:
    q,d=quality(a); s=start_date(a); out["start"][a]=str(s.date()); out["quality"][a]={int(k):float(v) for k,v in q.items()}
    T=rules_h(d,a); m=d.index>=s; dd=d[m]; D[a]=dict(d=dd,o=dd.open.values,c=dd.close.values,T={k:v[m] for k,v in T.items()},eod=(dd.index.hour==23))
    out["quality"][a+"_fills_on_zero_volume_bars_H1"]=int(((np.diff(np.r_[0,D[a]["T"]["H1"][:-1]])!=0)&(dd.volume.values[1:]==0)).sum())
def run(a,name,cost,target=None):
    x=D[a]; t=x["T"][name] if target is None else target
    eq,held=sim_fast(x["o"],x["c"],t,cost); return pd.Series(eq[x["eod"]],index=x["d"].index[x["eod"]].floor("D")),eq,held
def sm(e,lo,hi):
    return metrics(e[lo:hi].values)
def trips(eq,held,idx,lo,hi):
    prev=np.r_[0,held[:-1]]; ent=np.flatnonzero((held==1)&(prev==0)); ex=np.flatnonzero((held==0)&(prev==1))
    k=min(len(ent),len(ex)); ent=ent[:k]; ex=ex[:k]
    base=np.where(ent>0,eq[np.maximum(ent-1,0)],1.0); r=eq[ex]/base-1; t=idx[ent]
    lo_=pd.Timestamp(lo) if lo else idx[0]; hi_=pd.Timestamp(hi)+pd.Timedelta(days=1)
    mk=(t>=lo_)&(t<hi_); r=r[mk]; yrs=max(1e-9,(min(hi_,idx[-1])-max(lo_,idx[0])).days/365)
    return dict(n=int(len(r)),per_year=float(len(r)/yrs),avg_bps=float(r.mean()*1e4) if len(r) else 0.0,win=float((r>0).mean()) if len(r) else 0.0,hours=float((ex-ent)[mk].mean()) if len(r) else 0.0)
def breakeven(f,lo=0.0,hi=600.0):
    if f(lo)<=0: return 0.0
    if f(hi)>0: return float(hi)
    for _ in range(30):
        mid=(lo+hi)/2
        if f(mid)>0: lo=mid
        else: hi=mid
    return (lo+hi)/2
for a in ["BTCUSD","ETHUSD"]:
    x=D[a]; idx=x["d"].index; A={"rules":{}, "bh":{}, "C1":{}, "pbo":{}}
    ones=np.ones(len(idx))
    sb=metrics(run(a,None,SLIP,ones)[0].values)["sharpe"]
    for name in NAMES:
        rr={"venues":{}}
        rr["exposure"]=float(np.r_[0,x["T"][name][:-1]].mean())
        rr["be_vs_bh_bps"]=breakeven(lambda c: metrics(run(a,name,c)[0].values)["sharpe"]-sb)
        rr["be_zero_bps"]=breakeven(lambda c: metrics(run(a,name,c)[0].values)["cagr"])
        e0,eqh,held=run(a,name,0.0); rr["gross"]={k:sm(e0,lo,hi) for k,(lo,hi) in SL.items()}; rr["gross_trips"]=trips(eqh,held,idx,None,"2026-11-24")
        A["rules"][name]=rr
    for v,fee in VENUES.items():
        c=fee+SLIP
        b,_,_=run(a,None,c,ones); A["bh"][v]={k:sm(b,lo,hi) for k,(lo,hi) in SL.items()}
        e,_,_=run(a,"C1",c); A["C1"][v]={k:sm(e,lo,hi) for k,(lo,hi) in SL.items()}
        R={}
        for name in NAMES:
            e,eqh,held=run(a,name,c); R[name]=drets(e)
            A["rules"][name]["venues"][v]={k:dict(sm(e,lo,hi),trips=trips(eqh,held,idx,lo,hi)) for k,(lo,hi) in SL.items()}
        # all 36 trials at this venue's cost: 20 from replay 01 plus these 16 (both assets) -> done after loop over assets
        A.setdefault("_R",{})[v]=R
        A["pbo"][v]=pbo_cscv(np.column_stack([R[n] for n in NAMES]),16)
        A.setdefault("_bh",{})[v]=drets(b)
    out["assets"][a]=A
    print(a,"metrics done",flush=True)
# deflated Sharpe, shuffles, bootstrap, pass marks
for v,fee in VENUES.items():
    c=fee+SLIP; old=[]
    for a in ["BTCUSD","ETHUSD"]:
        for rule in DAILY_RULES: old.append(c1.rets(c1.run(a,rule,c)[0]))
    for rule in ["P1","P2"]:
        es=[]
        for a in ["BTCUSD","ETHUSD"]:
            d=c1.load(a); tgt=DAILY_RULES[rule](d.close); m=d.index>="2018-03-05"; dd=d[m]
            es.append(pd.Series(simulate(dd.open.values,dd.close.values,tgt[m].values,c,start_cash=0.5)[0],index=dd.index))
        old.append(c1.rets(es[0]+es[1]))
    new=[out["assets"][a]["_R"][v][n] for a in out["assets"] for n in NAMES]
    assert len(old)+len(new)==N_TRIALS
    sd=float(np.std([sharpe_per_period(r) for r in old+new],ddof=1))
    for a in ["BTCUSD","ETHUSD"]:
        A=out["assets"][a]; x=D[a]
        for name in NAMES:
            r=A["_R"][v][name]; dsr=deflated_sharpe(r,N_TRIALS,sd)[0]
            rng=np.random.default_rng(7); s_real=sharpe_per_period(r); cnt=0
            for i in range(1000):
                eq,_=sim_fast(x["o"],x["c"],shuffle_fast(x["T"][name],rng),c); ed=eq[x["eod"]]
                cnt+= sharpe_per_period(ed[1:]/ed[:-1]-1)<s_real
            boot=[float(z) for z in block_bootstrap_sharpe_diff(r,A["_bh"][v])]
            rv=A["rules"][name]["venues"][v]; h=rv["held"]; b=A["bh"][v]["held"]
            m1=(h["sharpe"]>b["sharpe"]) and (abs(h["maxdd"])<=DROP*abs(b["maxdd"]))
            m2=A["rules"][name]["be_vs_bh_bps"]>=MULT*c; m3=dsr>DSR_MIN; m4=A["pbo"][v]<PBO_MAX; m5=cnt/1000>SHUF
            rv["marks"]=dict(dsr=dsr,shuffle=cnt/1000,boot=boot,dd_ratio=abs(h["maxdd"])/abs(b["maxdd"]),m1=bool(m1),m2=bool(m2),m3=bool(m3),m4=bool(m4),m5=bool(m5),passed=bool(m1 and m2 and m3 and m4 and m5),
                             made_money_all=bool(rv["all"]["total"]>0),made_money_held=bool(h["total"]>0))
    print(v,"marks done",flush=True)
    o2={k:v for k,v in out.items() if k!="assets"}; o2["assets"]={a:{k:v for k,v in out["assets"][a].items() if not k.startswith("_")} for a in out["assets"]}
    json.dump(o2,open("results_03.json","w"),indent=1,default=float)
print("done")
