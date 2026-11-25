"""Cross-check X2 and S2: replay 01 rules on Kraken's full daily history. PREREG_01_X2_kraken_full_history.md. Writes results_01x2.json."""
import numpy as np, pandas as pd, json, sys
import common_01 as c1
from engine import *
from rules import RULES
from common_03 import sim_fast, shuffle_fast
MULT=2; PBO_MAX=0.25; DROP=0.6; DSR_MIN=0.95; SHUF=0.95   # keys in config/thresholds.yaml
def kload(a):
    d=pd.read_csv(f"data/krakenfull_{a}.csv",parse_dates=["date"]).set_index("date"); return d[d.index<="2026-11-24"]
c1.load=kload
BIN=[r for r in RULES if r not in ("P1","P2")]
def do(start_eth):
    c1.START={"BTCUSD":"2014-05-01","ETHUSD":start_eth}; res={}
    for a in ["BTCUSD","ETHUSD"]:
        b0=c1.bh(a,c1.SLIP); sb=metrics(b0.values)["sharpe"]; res[a]={"rules":{r:{"venues":{}} for r in RULES},"bh":{},"pbo":{}}
        for r in RULES:
            res[a]["rules"][r]["be_vs_bh_bps"]=c1.breakeven(a,r,lambda e: metrics(e.values)["sharpe"]-sb)
            res[a]["rules"][r]["be_zero_bps"]=c1.breakeven(a,r,lambda e: metrics(e.values)["cagr"])
    for v,fee in c1.VENUES.items():
        c=fee+c1.SLIP; R={}; T={}
        for a in ["BTCUSD","ETHUSD"]:
            b=c1.bh(a,c); res[a]["bh"][v]={k:metrics(b[lo:hi].values) for k,(lo,hi) in c1.SL.items()}; res[a].setdefault("_bh",{})[v]=c1.rets(b)
            for r in RULES:
                eq,wt,tr,t=c1.run(a,r,c); R[(a,r)]=c1.rets(eq); T[(a,r)]=t
                res[a]["rules"][r]["venues"][v]={k:c1.slice_metrics(eq,wt,tr,lo,hi) for k,(lo,hi) in c1.SL.items()}
        port=[]
        for r in ["P1","P2"]:
            es=[]
            for a in ["BTCUSD","ETHUSD"]:
                d=kload(a); tgt=RULES[r](d.close); m=d.index>="2018-03-05"; dd=d[m]
                es.append(pd.Series(simulate(dd.open.values,dd.close.values,tgt[m].values,c,start_cash=0.5)[0],index=dd.index))
            port.append(c1.rets(es[0]+es[1]))
        sd=float(np.std([sharpe_per_period(x) for x in list(R.values())+port],ddof=1))
        for a in ["BTCUSD","ETHUSD"]:
            pbo=pbo_cscv(np.column_stack([R[(a,r)] for r in RULES]),16); res[a]["pbo"][v]=pbo
            d=kload(a); dd=d[d.index>=c1.START[a]]; o=dd.open.values; cl=dd.close.values
            for r in RULES:
                rng=np.random.default_rng(7); s_real=sharpe_per_period(R[(a,r)]); cnt=0
                for i in range(1000):
                    if r in BIN: e=sim_fast(o,cl,shuffle_fast(T[(a,r)],rng),c)[0]
                    else: e=simulate(o,cl,shuffle_spells(T[(a,r)],rng),c)[0]
                    cnt+= sharpe_per_period(e[1:]/e[:-1]-1)<s_real
                dsr=deflated_sharpe(R[(a,r)],20,sd)[0]; rv=res[a]["rules"][r]["venues"][v]; h=rv["held"]; b=res[a]["bh"][v]["held"]
                m1=(h["sharpe"]>b["sharpe"]) and (abs(h["maxdd"])<=DROP*abs(b["maxdd"])); m2=res[a]["rules"][r]["be_vs_bh_bps"]>=MULT*c; m3=dsr>DSR_MIN; m4=pbo<PBO_MAX; m5=cnt/1000>SHUF
                rv["marks"]=dict(dsr=dsr,shuffle=cnt/1000,dd_ratio=abs(h["maxdd"])/abs(b["maxdd"]),boot=[float(z) for z in block_bootstrap_sharpe_diff(R[(a,r)],res[a]["_bh"][v])],
                                 m1=bool(m1),m2=bool(m2),m3=bool(m3),m4=bool(m4),m5=bool(m5),passed=bool(m1 and m2 and m3 and m4 and m5))
        print(start_eth,v,"done",flush=True)
    for a in res: res[a].pop("_bh",None)
    return res
A=do("2018-03-05"); json.dump({"X2":A,"build":json.load(open("kraken_daily_build.json"))},open("results_01x2.json","w"),indent=1,default=float)
B=do("2016-03-01"); json.dump({"X2":A,"S2_ETH":B["ETHUSD"],"build":json.load(open("kraken_daily_build.json"))},open("results_01x2.json","w"),indent=1,default=float)
print("done")
