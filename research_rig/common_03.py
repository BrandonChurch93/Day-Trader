"""Replay 03 helpers: hourly bars, binary rules. See PREREG_03_intraday_crypto.md. Not the product."""
import numpy as np, pandas as pd, math
from engine import *
from rules import p1 as daily_p1
VENUES={"Binance.US":2,"Alpaca":25,"Kraken $10k tier":38,"Kraken entry":80,"Coinbase entry":90}; SLIP=5
END="2026-11-24 23:00"
def load_h(a):
    d=pd.read_csv(f"data/bitstamp_{a}_1h.csv"); d.index=pd.to_datetime(d.ts,unit="s"); d=d.drop(columns="ts")
    d=d[~d.index.duplicated()].sort_index(); d=d[d.index<=END]
    full=pd.date_range(d.index[0].floor("D"),END,freq="h"); miss=~full.isin(d.index)
    d=d.reindex(full); d["missing"]=miss; d["close"]=d.close.ffill()
    for c in ["open","high","low"]: d[c]=d[c].fillna(d.close)
    d["volume"]=d.volume.fillna(0.0); return d.dropna(subset=["close"])
def quality(a):
    d=load_h(a); bad=(d.missing|(d.volume==0)); return bad.groupby(d.index.year).mean(), d
def start_date(a):
    q,d=quality(a); first=d.index[0]; years=sorted(q.index)
    for y in years:
        s=pd.Timestamp(f"{y}-01-01")
        if s<first+pd.Timedelta(hours=4800): continue
        if all(q[z]<0.01 for z in years if z>=y): return s
    return None
def sim_fast(o,c,target,cost_bps):
    """Vectorised simulate for 0/1 targets. Returns equity at each close. Must equal engine.simulate."""
    k=cost_bps/1e4; held=np.zeros(len(c)); held[1:]=np.nan_to_num(target[:-1],nan=0.0)
    prev=np.zeros(len(c)); prev[1:]=held[:-1]; pc=np.empty(len(c)); pc[0]=c[0]; pc[1:]=c[:-1]
    f=np.ones(len(c))
    stay=(held==1)&(prev==1); f[stay]=c[stay]/pc[stay]
    ent=(held==1)&(prev==0); f[ent]=c[ent]/o[ent]/(1+k)
    ex=(held==0)&(prev==1); f[ex]=o[ex]/pc[ex]*(1-k)
    return np.cumprod(f), held
def shuffle_fast(t, rng):
    t=np.nan_to_num(t,nan=0.0); cut=np.flatnonzero(np.diff(t)!=0)+1; parts=np.split(t,cut)
    return np.concatenate([parts[i] for i in rng.permutation(len(parts))])
def rules_h(d, a):
    """Returns dict of target arrays (decided at close of bar t)."""
    c=d.close; o=d.open; h=d.index.hour.values; day=d.index.floor("D"); n=len(d); out={}
    dopen=o.groupby(day).transform("first")
    # H1
    sig=((c>dopen)&(h==11)).groupby(day).transform("max")
    out["H1"]=np.where(sig&(h>=11)&(h<=22),1.0,0.0)
    out["C1"]=np.where((h>=11)&(h<=22),1.0,0.0)
    # H2
    rng_hi=d.high.where(h<=3).groupby(day).transform("max")
    brk=(c>rng_hi)&(h>=4)&(h<=22); on=brk.groupby(day).cummax()
    out["H2"]=np.where(on&(h<=22),1.0,0.0)
    # H3
    r=c/c.shift(1)-1
    s0=((r>0)&(h==0)).groupby(day).transform("max")
    out["H3"]=np.where(s0&(h==22)&(r>0),1.0,0.0)
    # H4, H5
    sd=r.rolling(168).std(ddof=1).shift(1); trig=(r<-2*sd)
    def hold4(tr):
        x=tr.astype(float); return (x.rolling(4,min_periods=1).max()>0).astype(float).values
    out["H4"]=hold4(trig)
    out["H5"]=hold4(trig&(c>c.rolling(4800).mean()))
    # H6
    m24=c.rolling(24).mean(); m168=c.rolling(168).mean()
    out["H6"]=np.where((c>m24)&(m24>m168),1.0,0.0)
    # H7
    dd=pd.read_csv(f"data/bitstamp_{a}.csv",parse_dates=["date"]).set_index("date")
    w=daily_p1(dd.close).shift(1)            # weight as of the prior day's close
    filt=pd.Series(day).map(w).values>=0.5
    out["H7"]=np.where(filt,out["H1"],0.0)
    # H8
    mv=(c/dopen-1).abs(); df=pd.DataFrame({"mv":mv.values,"h":h,"day":day})
    band=df.groupby("h").mv.transform(lambda s: s.rolling(14).mean().shift(1)).values
    cv=c.values; dv=dopen.values; t8=np.zeros(n); state=0; done=False
    for i in range(n):
        if h[i]==0: state=0; done=False
        if h[i]==23: t8[i]=0.0; state=0; continue
        if state==0 and not done and h[i]>=1 and not np.isnan(band[i]) and cv[i]>dv[i]*(1+band[i]): state=1; done=True
        elif state==1 and cv[i]<dv[i]: state=0
        t8[i]=state
    out["H8"]=t8
    return out
def daily(eq_h, idx):
    s=pd.Series(eq_h,index=idx); return s[s.index.hour==23]
