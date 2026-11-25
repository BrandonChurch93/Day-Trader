"""Plan 14 adjustment check. For five dividend payers (KO, PG, JNJ, XOM, PEP) and three companies with spin-offs (GE, MMM,
HON), compares adjustment=all against adjustment=raw closes: does the factor adjusted / raw stay constant between the
feed's listed ex-dates (cash dividends, spin-offs, splits) and step only on them? Prints counts and the largest wobble
inside a segment only; no price, no return. Run from research_rig/: python3 check_adjust_14.py"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_14 as F, csv, os, json, numpy as np, common_14 as C
days=C.calendar(); me=set(days[i] for i in C.month_end_index(days))
def bars(sym, adj):
    out=[]; tok=None
    while True:
        u=f"https://data.alpaca.markets/v2/stocks/bars?symbols={sym}&timeframe=1Day&start=2016-01-04&end=2026-11-24&feed=sip&adjustment={adj}&limit=10000"+(f"&page_token={tok}" if tok else "")
        d=F.get(u); out+=(d.get("bars") or {}).get(sym,[]); tok=d.get("next_page_token")
        if not tok: return {b["t"][:10]:b for b in out}
def actions(sym, types):
    out=[]
    for y in range(2016,2027):
        u=f"https://data.alpaca.markets/v1/corporate-actions?symbols={sym}&types={types}&start={y}-01-01&end={y}-12-31&limit=1000"
        r=F.subprocess.run(["pplx","credentials","run",F.CRED,"--","curl","-s","--max-time","60",u],capture_output=True,text=True)
        try: d=json.loads(r.stdout)
        except Exception: continue
        for k,v in (d.get("corporate_actions") or {}).items(): out+=[(k,x.get("ex_date")) for x in v]
    return out
res={}
for sym in ("KO","PG","JNJ","XOM","PEP","GE","MMM","HON"):
    A=bars(sym,"all"); R=bars(sym,"raw"); ds=sorted(set(A)&set(R))
    q=np.array([A[d]["c"]/R[d]["c"] for d in ds])
    ch=[ds[i] for i in range(1,len(ds)) if abs(q[i]/q[i-1]-1)>2e-3]          # a step in the factor
    acts=actions(sym,"cash_dividend,spin_off,forward_split,reverse_split")
    ex={e for _,e in acts if e}
    steps_on_ex=sum(1 for d in ch if d in ex); 
    # between steps constant? spread of q inside each segment, excluding rounding
    seg_ok=True; last=0
    idx=[0]+[ds.index(d) for d in ch]+[len(ds)]
    worst=0.0
    for a,b in zip(idx[:-1],idx[1:]):
        s=q[a:b]; 
        if len(s)>1: worst=max(worst,float(np.max(np.abs(s/np.median(s)-1))))
    spin=[(k,e) for k,e in acts if k=="spin_offs" or k=="spin_off"]
    res[sym]=dict(steps=len(ch), steps_on_listed_ex_dates=steps_on_ex, listed_actions=len(ex), max_wobble_inside_segments=round(worst,4),
                  spin_offs=[e for k,e in acts if "spin" in k], step_on_spin=[e for k,e in acts if "spin" in k and e in ch],
                  ranking_closes=len([d for d in ds if d in me]))
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(F.DATA, "adjust_check.json"), "w"), indent=1)
