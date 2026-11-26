"""Count 118 step 2b helper. Draws 60 reports (random.Random(118) over the events file sorted by accession) and,
for each, reads the company's own EDGAR 8-K filings accepted in the 45 calendar days before the report that list
Item 7.01 or 8.01, plus the company's previous kept Item 2.02 filing. It saves, per document, the first date named in its own Item 2.02 text (to check
whether the 8-K acceptance lags the press release), and per document only whether the actual release date appears within 200 characters of a call, webcast, results or earnings word, and any other
dates so placed. Saves notice_2b.json under RAW. Reads EDGAR archives with a declared user agent, at most 4
requests a second. No full-text search, no prices."""
import json, os, re, csv, time, random, html, urllib.request, datetime as dt
RAW=os.environ.get("RAW","/home/user/workspace/rig/data/count_118"); HERE=os.path.dirname(os.path.abspath(__file__))
UA="Brandon Church research modernsoftworks@gmail.com"
def get(u):
    time.sleep(0.25)
    try: return urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=40).read().decode("utf-8","ignore")
    except Exception as e: return ""
MON="January February March April May June July August September October November December".split()
def pats(d):
    m=MON[d.month-1]; a=m[:3]
    return [f"{m} {d.day}, {d.year}",f"{m} {d.day}",f"{a}. {d.day}",f"{a} {d.day},",f"{d.month}/{d.day}/{d.year}"]
DATE=re.compile(r"(January|February|March|April|May|June|July|August|September|October|November|December|Jan\.|Feb\.|Mar\.|Apr\.|Aug\.|Sept?\.|Oct\.|Nov\.|Dec\.) (\d{1,2})(, (20\d\d))?")
KEY=re.compile(r"conference call|webcast|earnings|results|report",re.I)
def scan(text,d):
    t=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",text)))
    hit=False; other=set()
    for m in DATE.finditer(t):
        w=t[max(0,m.start()-200):m.end()+200]
        if not KEY.search(w) or not re.search(r"(will|to be|scheduled|plans? to|host)",w,re.I): continue
        s=m.group(0)
        if any(s.startswith(p) or p.startswith(s) for p in pats(d)): hit=True
        else: other.add(s)
    return hit,sorted(other)[:5]
def main():
    ev=sorted(csv.DictReader(open(os.path.join(HERE,"count_118_events.csv"))),key=lambda e:e["acc"])
    sample=random.Random(118).sample(ev,60)
    rows=[json.loads(l) for l in open(os.path.join(RAW,"8k_2014_2021.jsonl"))]
    out=[]
    for e in sample:
        acc_ts=dt.datetime.strptime(e["accepted_et"],"%Y-%m-%d %H:%M:%S"); d=acc_ts.date()
        cand=[r for r in rows if r["tk"]==e["tk"] and r["form"]=="8-K" and r["acc"]!=e["acc"]]
        def et(r): return dt.datetime.fromisoformat(r["at"].replace("Z","+00:00")).astimezone(__import__("zoneinfo").ZoneInfo("America/New_York")).replace(tzinfo=None)
        pre=[r for r in cand if 0<(acc_ts-et(r)).total_seconds()<=45*86400 and ({"7.01","8.01"}&set(r["items"].split(",")))]
        prev202=[r for r in cand if "2.02" in r["items"].split(",") and 45*86400<(acc_ts-et(r)).total_seconds()<=130*86400]
        prev202=prev202[-1:] 
        docs=[]
        for r in pre+prev202:
            base=f"https://www.sec.gov/Archives/edgar/data/{r['cik']}/{r['acc'].replace('-','')}/"
            idx=get(base+"index.json")
            try: items=[i["name"] for i in json.loads(idx)["directory"]["item"]]
            except Exception: items=[r["doc"]]
            items=[n for n in items if re.search(r"\.(htm|html|txt)$",n,re.I) and not n.endswith("-index.htm") and not n.endswith("-index-headers.html") and not re.match(r"\d{10}-\d\d-\d{6}\.txt$",n)][:6]
            for n in items:
                hit,other=scan(get(base+n),d)
                docs.append(dict(acc=r["acc"],items=r["items"],kind="prior_2.02" if r in prev202 else "7.01/8.01",doc=n,date_named=hit,other_dates=other,accepted=r["at"]))
        me=next(r for r in rows if r["acc"]==e["acc"])
        t=re.sub(r"\s+"," ",html.unescape(re.sub(r"<[^>]+>"," ",get(f"https://www.sec.gov/Archives/edgar/data/{me['cik']}/{me['acc'].replace('-','')}/{me['doc']}"))))
        i=t.find("2.02"); m=re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December) (\d{1,2}) ?, (20\d\d)",t[i:i+600]) if i>=0 else None
        rel=dt.date(int(m.group(3)),MON.index(m.group(1))+1,int(m.group(2))).isoformat() if m else None
        out.append(dict(release_date_in_8k=rel,tk=e["tk"],acc=e["acc"],accepted_et=e["accepted_et"],t=e["t"],f=e["f"],err=e["err_sessions"],docs=docs))
        print(e["tk"],e["accepted_et"],rel,len(pre),len(prev202),sum(x["date_named"] for x in docs),flush=True)
    json.dump(out,open(os.path.join(RAW,"notice_2b.json"),"w"),indent=1)

# Notices confirmed by reading the sentence around the matched date (one per hit; each names the actual date
# of the results release). A matched date that the reading did not confirm would be listed here as False.
CONFIRMED={"IBM":"will report its second quarter 2019 earnings on July 17, 2019",
           "UNP":"will announce financial results for the quarter and year ended December 31, 2017, on January 25, 2018",
           "INTC":"plans to report its earnings for the third quarter of 2021 on October 21, 2021"}
def table():
    """Writes count_118_notice_sample.csv (no price fields) from notice_2b.json."""
    N=json.load(open(os.path.join(RAW,"notice_2b.json")))
    cols=["tk","acc","accepted_et","t","f_2a","err_2a","release_date_in_8k","docs_checked","docs_701_801","notice_found","notice_acc","notice_kind","notice_accepted","named_date","calendar_days_ahead","named_vs_actual"]
    out=os.path.join(HERE,"count_118_notice_sample.csv")
    with open(out,"w") as fh:
        fh.write(",".join(cols)+"\n")
        for n in sorted(N,key=lambda n:n["acc"]):
            hit=[d for d in n["docs"] if d["date_named"] and n["tk"] in CONFIRMED]
            rel=dt.date.fromisoformat(n["accepted_et"][:10])
            r=dict(tk=n["tk"],acc=n["acc"],accepted_et=n["accepted_et"],t=n["t"],f_2a=n["f"] or "",err_2a="" if n["err"] in (None,"") else n["err"],
                   release_date_in_8k=n["release_date_in_8k"] or "",docs_checked=len(n["docs"]),docs_701_801=sum(d["kind"]!="prior_2.02" for d in n["docs"]),
                   notice_found=bool(hit),notice_acc="",notice_kind="",notice_accepted="",named_date="",calendar_days_ahead="",named_vs_actual="")
            if hit:
                h=hit[0]; na=dt.datetime.fromisoformat(h["accepted"].replace("Z","+00:00")).date()
                r.update(notice_acc=h["acc"],notice_kind=h["kind"],notice_accepted=na.isoformat(),named_date=rel.isoformat(),calendar_days_ahead=(rel-na).days,named_vs_actual="exact")
            fh.write(",".join(str(r[c]) for c in cols)+"\n")
    print(out)
if __name__=="__main__":
    import sys
    table() if sys.argv[1:]==["--table"] else main()
