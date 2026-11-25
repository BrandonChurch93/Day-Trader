"""Score the AI-calls pilot (PREREG_02). Reports every run. No pass mark."""
import json, math, numpy as np, pandas as pd
from engine import simulate, metrics, shuffle_spells
from rules import RULES
FIRST=pd.Timestamp("2026-06-30"); LASTDEC=pd.Timestamp("2026-11-23"); END=pd.Timestamp("2026-11-24"); COST=30.0; N=147
D={}
for a,f in [("btc","bitstamp_BTCUSD"),("eth","bitstamp_ETHUSD")]:
    d=pd.read_csv(f"data/{f}.csv",parse_dates=["date"]).set_index("date"); D[a]=d[d.index<=END]
runs={}
for l in open("pilot/decisions.jsonl"):
    r=json.loads(l); runs.setdefault(r["run"],[]).append(r)
def sim(targets):
    """targets: dict coin -> array of N weights. Returns equity series (sum of halves), weights, traded."""
    tot=None; W={}; TR=0; trades=0
    for a in D:
        d=D[a]; seg=d[(d.index>=FIRST)&(d.index<=END)]; t=np.r_[targets[a],np.nan][:len(seg)]
        eq,wt,tr=simulate(seg.open.values,seg.close.values,t,COST,band=0.10,start_cash=0.5)
        e=pd.Series(eq,index=seg.index); tot=e if tot is None else tot+e; W[a]=wt; TR+=tr.sum(); trades+=int((tr>0).sum())
    return tot,W,TR,trades
def summarize(eq,W,TR,trades):
    e=eq.values; r=e[1:]/e[:-1]-1; peak=np.maximum.accumulate(np.r_[1.0,e])
    return dict(net_return=float(e[-1]-1),max_drop=float((np.r_[1.0,e]/peak-1).min()),exposure=float((W["btc"]+W["eth"]).mean()/2*1.0) if False else float(np.mean([W["btc"].mean(),W["eth"].mean()])),
                trades=trades,turnover=float(TR),cost_paid=float(TR*COST/1e4),sharpe=float(r.mean()/r.std(ddof=1)*math.sqrt(365)) if r.std()>0 else 0.0), r
def boot(diff,block=10,draws=2000,seed=7):
    rng=np.random.default_rng(seed); n=len(diff); nb=math.ceil(n/block); out=np.empty(draws)
    for i in range(draws):
        st=rng.integers(0,n-block+1,nb); idx=(st[:,None]+np.arange(block)[None,:]).ravel()[:n]; out[i]=diff[idx].mean()
    return [float(x) for x in np.percentile(out,[5,50,95])]
# comparators
p1={a:RULES["P1"](D[a].close)[(D[a].index>=FIRST)&(D[a].index<=LASTDEC)].values for a in D}
hold={a:np.ones(N) for a in D}
out={"n_decisions":{k:len(v) for k,v in runs.items()}}
res={}; R={}; T={"P1":p1,"hold":hold}
for k,v in runs.items():
    if len(v)!=N: continue
    assert [x["step"] for x in v]==list(range(1,N+1))
    T[k]={a:np.array([x[a] for x in v]) for a in D}
for k,t in T.items():
    eq,W,TR,tr=sim(t); s,r=summarize(eq,W,TR,tr); res[k]=s; R[k]=r; res[k]["final"]=float(eq.iloc[-1])
for k in T:
    if k in ("P1","hold"): continue
    d=R[k]-R["P1"]; res[k]["daily_diff_vs_P1_bps_mean"]=float(d.mean()*1e4); res[k]["daily_diff_vs_P1_bps_90"]=[x*1e4 for x in boot(d)]
    dh=R[k]-R["hold"]; res[k]["daily_diff_vs_hold_bps_90"]=[x*1e4 for x in boot(dh)]
    res[k]["match_P1_share"]=float(np.mean([np.mean(np.abs(T[k][a]-np.round(p1[a]*4)/4)<1e-9) for a in D]))
    res[k]["mean_abs_gap_to_P1"]=float(np.mean([np.mean(np.abs(T[k][a]-p1[a])) for a in D]))
    res[k]["corr_weight_with_P1"]=float(np.mean([np.corrcoef(T[k][a],p1[a])[0,1] for a in D]))
    rng=np.random.default_rng(7); cnt=0; fin=[]
    for i in range(1000):
        e=sim({a:shuffle_spells(T[k][a],rng) for a in D})[0]; fin.append(e.iloc[-1]-1)
    res[k]["shuffle_pct"]=float((np.array(fin)<res[k]["net_return"]).mean()); res[k]["shuffle_median_return"]=float(np.median(fin))
fab=[k for k in res if k.startswith("r_fable")]
if len(fab)>=2:
    out["fable_spread"]=dict(net_min=min(res[k]["net_return"] for k in fab),net_max=max(res[k]["net_return"] for k in fab),
        pair_agreement={f"{a}|{b}":float(np.mean([np.mean(T[a][c]==T[b][c]) for c in D])) for i,a in enumerate(fab) for b in fab[i+1:]})
out["runs"]=res
json.dump(out,open("results_02.json","w"),indent=1)
print(out["n_decisions"]); print(out.get("fable_spread"))
for k,s in res.items():
    print(f"{k:10s} net {s['net_return']*100:+6.2f}% drop {s['max_drop']*100:6.2f}% exp {s['exposure']:.2f} trades {s['trades']:3d} cost {s['cost_paid']*100:.2f}% SR {s['sharpe']:+.2f}"+(f" | vsP1 {s['daily_diff_vs_P1_bps_mean']:+.1f}bps/d 90% [{s['daily_diff_vs_P1_bps_90'][0]:+.1f},{s['daily_diff_vs_P1_bps_90'][2]:+.1f}] match {s['match_P1_share']:.2f} corr {s['corr_weight_with_P1']:.2f} shuf {s['shuffle_pct']:.3f}" if 'match_P1_share' in s else ""))
