"""Count 118: pre-earnings reversal, price-blind count of SEC 8-K Item 2.02 report times and
whether the report day can be known before entry. Reads only off-repo EDGAR metadata saved under
RAW (default /home/user/workspace/rig/data/count_118). Reads no price of any kind.

Step 1: from 8k_2014_2021.jsonl (8-K rows with SEC acceptance times, filing date 2014-10-01 to 2021-12-31),
keep original 8-K filings that list Item 2.02. 2.02 filings by one company within 60 calendar days of the first in a group form one group; the kept report is
the first whose Item 2.02 text (saved snippet, clus_flags.json) names results or earnings and none of a fixed list of
non-report words (preliminary, transcript, guidance, charge and so on); if none passes, the first is kept. Timing in New York time: before 09:30 is before the
open, 09:30 to the close (16:00, 13:00 on early-close days) is in session, later is after the close.
Report day t is the acceptance day if it is a session and the filing is not after the close, else the
next session.
Step 2a (fixed before scoring): forecast for each report = the company's kept report 300 to 430 calendar
days earlier that is closest to 364 days earlier; same weekday and same nth weekday of the same month
one year later (last such weekday if no nth); moved to the next session if not a session; timing class of
the base report applied to get the forecast report day f. Score: sessions from f to t.
Usable under 2a: enter at the close of f-1 only if no 2.02 for that quarter was accepted before then;
usable if t is f or f+1 (the reversal window t-1..t+1 is then inside entry f-1 .. exit t+1).
"""
import json, os, sys, hashlib, datetime as dt, collections
from zoneinfo import ZoneInfo
RAW = os.environ.get("RAW", "/home/user/workspace/rig/data/count_118")
HERE = os.path.dirname(os.path.abspath(__file__))
NY = ZoneInfo("America/New_York")
D = dt.date

def easter(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3;h=(19*a+b-d-g+15)%30
    i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451;mo=(h+l-7*m+114)//31;da=(h+l-7*m+114)%31+1
    return D(y,mo,da)
def nth(y,m,wd,n):
    x=D(y,m,1); x+=dt.timedelta((wd-x.weekday())%7); return x+dt.timedelta(7*(n-1))
def last(y,m,wd):
    x=D(y,m+1,1)-dt.timedelta(1) if m<12 else D(y,12,31); return x-dt.timedelta((x.weekday()-wd)%7)
def obs(x):
    return x-dt.timedelta(1) if x.weekday()==5 else (x+dt.timedelta(1) if x.weekday()==6 else x)
HOL=set(); EARLY=set()
for y in range(2014,2023):
    ny=D(y,1,1)
    if ny.weekday()!=5: HOL.add(obs(ny))
    HOL|={nth(y,1,0,3),nth(y,2,0,3),easter(y)-dt.timedelta(2),last(y,5,0),obs(D(y,7,4)),nth(y,9,0,1),nth(y,11,3,4),obs(D(y,12,25))}
    EARLY.add(nth(y,11,3,4)+dt.timedelta(1))
    for x in (D(y,12,24),D(y,7,3)):
        if x.weekday()<5 and x not in HOL and obs(D(y,7,4))!=D(y,7,3): EARLY.add(x)
HOL.add(D(2018,12,5))
EARLY-=HOL
def sess(x): return x.weekday()<5 and x not in HOL
SESS=[D(2014,1,1)+dt.timedelta(i) for i in range(365*9)]; SESS=[x for x in SESS if sess(x)]
IDX={x:i for i,x in enumerate(SESS)}
def nxt(x):
    x+=dt.timedelta(1)
    while not sess(x): x+=dt.timedelta(1)
    return x
def onorafter(x): return x if sess(x) else nxt(x)

def timing(ts):
    d=ts.date(); hm=ts.hour*60+ts.minute; close=13*60 if d in EARLY else 16*60
    if not sess(d): return "closed_day", nxt(d)
    if hm<9*60+30: return "before_open", d
    if hm<close: return "in_session", d
    return "after_close", nxt(d)

def load():
    rows=[json.loads(l) for l in open(os.path.join(RAW,"8k_2014_2021.jsonl"))]
    rep=[r for r in rows if r["form"]=="8-K" and "2.02" in r["items"].split(",")]
    for r in rep:
        r["ts"]=dt.datetime.fromisoformat(r["at"].replace("Z","+00:00")).astimezone(NY)
    flags=json.load(open(os.path.join(RAW,"clus_flags.json")))
    by=collections.defaultdict(list)
    for r in rep: by[r["tk"]].append(r)
    kept=[];extra=0;CL=collections.Counter()
    for tk,L in by.items():
        L.sort(key=lambda r:r["ts"]); i=0
        while i<len(L):
            c=[L[i]]; j=i+1
            while j<len(L) and (L[j]["ts"]-L[i]["ts"]).days<60: c.append(L[j]); j+=1
            if len(c)==1: c[0]["dd"]="single"; kept.append(c[0])
            else:
                pick=next((r for r in c if flags.get(r["acc"])),None)
                CL["clusters"]+=1; CL["picked_by_text" if pick else "fallback_first"]+=1
                k=pick or c[0]; k["dd"]="text" if pick else "fallback"; kept.append(k); extra+=len(c)-1
            i=j
    global CLUSTERS; CLUSTERS=dict(CL)
    for r in kept:
        r["cls"],r["t"]=timing(r["ts"])
    return kept,extra

def forecast(r,L):
    t0=r["ts"].date(); best=None
    for b in L:
        gap=(t0-b["ts"].date()).days
        if 300<=gap<=430 and (best is None or abs(gap-364)<abs((t0-best["ts"].date()).days-364)): best=b
    if not best: return None
    bd=best["ts"].date(); n=(bd.day-1)//7+1; y=bd.year+1
    try: fd=nth(y,bd.month,bd.weekday(),n)
    except ValueError: fd=None
    if fd is None or fd.month!=bd.month: fd=last(y,bd.month,bd.weekday())
    fd=onorafter(fd)
    f=fd if best["cls"] in ("before_open","in_session") else nxt(fd)
    return dict(base=best["acc"],fdate=fd,f=f,bcls=best["cls"])

def main():
    kept,extra=load()
    by=collections.defaultdict(list)
    for r in kept: by[r["tk"]].append(r)
    ev=[]
    for r in kept:
        if not (D(2016,1,1)<=r["t"]<=D(2021,12,31)): continue
        fc=forecast(r,by[r["tk"]])
        e=dict(tk=r["tk"],cik=r["cik"],acc=r["acc"],accepted_et=r["ts"].strftime("%Y-%m-%d %H:%M:%S"),timing=r["cls"],t=r["t"].isoformat(),dedupe=r["dd"])
        if fc:
            err=IDX[r["t"]]-IDX[fc["f"]]
            entry=SESS[IDX[fc["f"]]-1]
            known_before=r["t"]<=entry if r["cls"]!="after_close" else r["ts"].date()<entry  # report out before entry close
            # report accepted before the entry close means it is known: skip
            out_before = r["ts"] < dt.datetime.combine(entry,dt.time(13 if entry in EARLY else 16,0),NY)
            e.update(f=fc["f"].isoformat(),entry_2a=entry.isoformat(),err_sessions=err,base_acc=fc["base"],skip_known=out_before,usable_2a=(err in (0,1)) and not out_before and r["dd"]!="fallback")
        else:
            e.update(f=None,entry_2a=None,err_sessions=None,base_acc=None,skip_known=None,usable_2a=False)
        ev.append(e)
    ev.sort(key=lambda e:(e["t"],e["tk"]))
    out=os.path.join(HERE,"count_118_events.csv")
    cols=["tk","cik","acc","accepted_et","timing","t","dedupe","f","entry_2a","err_sessions","skip_known","usable_2a","base_acc"]
    with open(out,"w") as fh:
        fh.write(",".join(cols)+"\n")
        for e in ev: fh.write(",".join("" if e[c] is None else str(e[c]) for c in cols)+"\n")
    S=dict(extra_202_dropped=extra,clusters=CLUSTERS,reports=len(ev),companies=len({e["tk"] for e in ev}),days=len({e["t"] for e in ev}))
    yr=collections.OrderedDict()
    for y in range(2016,2022):
        E=[e for e in ev if e["t"].startswith(str(y))]
        c=collections.Counter(e["timing"] for e in E)
        yr[y]=dict(reports=len(E),days=len({e["t"] for e in E}),**{k:c.get(k,0) for k in ("before_open","in_session","after_close","closed_day")})
    S["by_year"]=yr
    F=[e for e in ev if e["f"]]
    c=collections.Counter()
    for e in F:
        x=e["err_sessions"]
        c["exact" if x==0 else "late_1" if x==1 else "early_1" if x==-1 else "late_more" if x>1 else "early_more"]+=1
    S["forecast_2a"]=dict(with_base=len(F),no_base=len(ev)-len(F),**c,skip_known=sum(bool(e["skip_known"]) for e in F))
    U=[e for e in ev if e["usable_2a"]]
    S["usable_2a"]=dict(events=len(U),entry_days=len({e["entry_2a"] for e in U}),by_year={y:sum(e["t"].startswith(str(y)) for e in U) for y in range(2016,2022)},
                       wasted_entries=sum(1 for e in F if not e["usable_2a"] and not e["skip_known"]))
    S["usable_2a"]["fallback_dedupe_excluded"]=sum(e["dedupe"]=="fallback" and e["err_sessions"] in (0,1) and e["skip_known"] is False for e in ev)
    S["clus_flags_sha256"]=hashlib.sha256(open(os.path.join(RAW,"clus_flags.json"),"rb").read()).hexdigest()
    S["events_csv_sha256"]=hashlib.sha256(open(out,"rb").read()).hexdigest()
    json.dump(S,open(os.path.join(HERE,"count_118_summary.json"),"w"),indent=1,default=str)
    print(json.dumps(S,indent=1,default=str))
if __name__=="__main__": main()
