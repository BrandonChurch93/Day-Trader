"""Sealed-envelope server for the AI-calls pilot. One step is released at a time, per run.
A run cannot see day t+1 until its decision for day t is recorded with a server timestamp."""
import json, sys, os, time, datetime, numpy as np, pandas as pd
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine import simulate
D={}
for a,f in [("BTC","bitstamp_BTCUSD"),("ETH","bitstamp_ETHUSD")]:
    d=pd.read_csv(os.path.join(os.path.dirname(__file__),"..","data",f+".csv"),parse_dates=["date"]).set_index("date"); D[a]=d[d.index<="2026-11-24"]
FIRST=pd.Timestamp("2026-06-30"); LAST=pd.Timestamp("2026-11-23")
DAYS=pd.date_range(FIRST,LAST); N=len(DAYS); COST=30.0; GRID={0.0,0.25,0.5,0.75,1.0}
LOG=os.path.join(os.path.dirname(__file__),"decisions.jsonl")
runs={}
if os.path.exists(LOG):
    for l in open(LOG):
        r=json.loads(l); runs.setdefault(r["run"],[]).append(r)
def account(run):
    """equity and weights after the last recorded decision's day close"""
    dec=runs.get(run,[]); k=len(dec); out={}
    tot=0; costs=0
    for a in D:
        d=D[a]; i0=d.index.get_loc(FIRST); seg=d.iloc[i0:i0+k+1]   # bars from FIRST through the current decision day
        tgt=np.array([x[a.lower()] for x in dec]+[np.nan])[:len(seg)]
        eq,wt,tr=simulate(seg.open.values,seg.close.values,tgt,COST,band=0.10,start_cash=0.5)
        out[a]=(eq[-1],wt[-1]); tot+=eq[-1]; costs+=tr.sum()*COST/1e4
    return tot,out,costs
def line(a,day):
    d=D[a]; i=d.index.get_loc(day); c=d.close; x=d.iloc[i]
    r=lambda n: (c.iloc[i]/c.iloc[i-n]-1)*100
    sma=lambda n: c.iloc[i-n+1:i+1].mean()
    vol=c.pct_change().iloc[i-29:i+1].std(ddof=1)*np.sqrt(365)*100
    hi=c.iloc[i-364:i+1].max()
    return (f"{a}: open {x.open:.2f} high {x.high:.2f} low {x.low:.2f} close {x.close:.2f} volume {x.volume:.0f}\n"
            f"   change 1d {r(1):+.2f}% 7d {r(7):+.2f}% 30d {r(30):+.2f}% 90d {r(90):+.2f}% | averages 20d {sma(20):.2f} 50d {sma(50):.2f} 100d {sma(100):.2f} 200d {sma(200):.2f} | 30d volatility {vol:.0f}% a year | {(x.close/hi-1)*100:+.1f}% from 365d high close")
def packet(run):
    k=len(runs.get(run,[]))
    if k>=N: return "DONE. All %d decisions are recorded. Stop now and report."%N
    day=DAYS[k]; tot,acc,costs=account(run); s=[f"STEP {k+1} of {N}. It is just after the UTC close of {day.date()}. Your decision fills at the next open."]
    if k==0:
        for a in D:
            d=D[a]; i=d.index.get_loc(day); h=d.close.iloc[i-119:i+1]
            s.append(f"{a} last 120 daily closes, oldest first: "+" ".join(f"{v:.0f}" if a=="BTC" else f"{v:.1f}" for v in h.values))
    for a in D: s.append(line(a,day))
    s.append(f"Account: value {tot:.4f} (started 1.0000; half assigned to each coin). Held now: BTC {acc['BTC'][1]:.2f} of its half, ETH {acc['ETH'][1]:.2f} of its half. Costs paid so far {costs:.4f}. Cost is 0.30% of each dollar traded.")
    s.append("Reply with btc and eth, each one of 0, 0.25, 0.5, 0.75, 1 (the share of that coin's half to hold), and a reason of at most 25 words.")
    return "\n".join(s)
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def do_GET(self):
        u=urlparse(self.path); q={k:v[0] for k,v in parse_qs(u.query).items()}; run=q.get("run","")
        if not run.startswith("r_"): return self.send("unknown run")
        if u.path=="/step": return self.send(packet(run))
        if u.path=="/decide":
            try: b=float(q["btc"]); e=float(q["eth"])
            except Exception: return self.send("ERROR: give btc and eth as numbers. Nothing recorded.\n"+packet(run))
            if b not in GRID or e not in GRID: return self.send("ERROR: weights must be one of 0, 0.25, 0.5, 0.75, 1. Nothing recorded.\n"+packet(run))
            k=len(runs.get(run,[]))
            if k>=N: return self.send(packet(run))
            rec={"run":run,"step":k+1,"day":str(DAYS[k].date()),"btc":b,"eth":e,"reason":q.get("reason","")[:300],"server_time":datetime.datetime.utcnow().isoformat()}
            runs.setdefault(run,[]).append(rec); open(LOG,"a").write(json.dumps(rec)+"\n")
            return self.send("RECORDED step %d.\n\n"%(k+1)+packet(run))
        self.send("use /step or /decide")
    def send(self,t):
        b=t.encode(); self.send_response(200); self.send_header("Content-Type","text/plain"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
HTTPServer(("127.0.0.1",8765),H).serve_forever()
