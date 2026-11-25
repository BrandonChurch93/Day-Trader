"""Rebuild Replays 16/17 identity from saved pages and archive daily levels.

Only dated boolean matches, counts and provenance are written. No prices,
marks, returns or funding values are emitted. This does not run the replay.
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import build_identity_asof_16_17 as B, diagnose_identity_daily_16_17 as D, score_16 as A

F,L = D.F,D.L


def fence(market,cid,pair):
    return (F.NOTICE_SPOT_DELIST if market=="spot" else F.NOTICE_DELIST).get((cid,pair))


def status(n,m,notice):
    level = "NO_VERDICT" if n<3 else "CONFIRMED" if 5*m>=4*n else "REMOVED" if 2*m<n else "UNKNOWN"
    outcome = ("REMOVED" if "REMOVED" in (level,notice) else "CONFIRMED" if
               level=="CONFIRMED" or (level=="NO_VERDICT" and notice=="CONFIRMED") else "UNKNOWN")
    return level,outcome


def rebuild(data,out,baseline):
    data,out,baseline = data.resolve(),out.resolve(),baseline.resolve()
    F.DATA = data
    F.F.DATA = data.parent/"replay_13"
    old = F.json_read(baseline)
    if "as_of_rows" in old:
        raise ValueError("use the preserved original all-month identity baseline")
    snapshots = F.json_read(data/"snapshots_16.json")
    raw_hash = F.digest((data/"snapshots_16.json").read_bytes())
    if raw_hash!=old["snapshots_sha256"]:
        raise ValueError("snapshot source differs from preserved baseline")
    hashes = {n:F.digest((data/n).read_bytes()) for n in L.MANIFESTS}
    manifests = [F.json_read(data/n) for n in L.MANIFESTS]
    index = L.archive_index(manifests)
    p13,p = F.config()
    cutoff = A.funding_cutoff(p,p13,A.source_ranges(manifests[1]))
    cutoff_date = F.F.utc(cutoff).date().isoformat()
    inventory = F.json_read(data/"identity_inventory.json")
    page_dates = {s["date"][:7]:s["date"] for s in snapshots["viewed"] if not s.get("hole")}
    quotes,_ = L.quotes_by_coin(snapshots,{r["id"] for r in old["rows"] if r["checked"]})
    jobs = defaultdict(lambda:defaultdict(list))
    for r in old["rows"]:
        if not r["checked"]:
            continue
        cid,market,pair = L.mapping(r)
        inv = inventory[str(cid)]
        original = inv["markets"].get(market+"/"+pair,{}).get("segments",[(None,None)])
        bounds = [(F.F.boundary(lo,-10**12),F.F.boundary(hi,10**12)) for lo,hi in original]
        if market=="spot" and cid in F.SPOT_SWAP_IDS:
            bounds = [(lo,hi) for lo,hi,s in F.spot_segments({"id":cid}) if s==pair]
        elif notice:=fence(market,cid,pair):
            edge = F.F.boundary(notice[0],10**12)
            bounds = [(lo,min(hi,edge)) for lo,hi in bounds]
        units = r["quote_multiplier"]
        for ym,(stamp,price) in quotes[cid].items():
            day = D.utc_day(stamp)
            saved = page_dates[ym]
            if saved<=cutoff_date and day+D.DAY<=cutoff and any(lo<=day and day+D.DAY<=hi for lo,hi in bounds):
                jobs[market,pair][day].append(((cid,market,pair),saved,price,units))

    def get_months(key):
        todo = jobs[key]
        got = defaultdict(list)
        for day,(low,high) in D.by_day(index.get(key,{}),todo).items():
            for k,saved,price,units in todo[day]:
                got[k].append([saved,day+D.DAY,D.daily_matches(price,units,low,high)])
        return got

    evidence = {}
    with ThreadPoolExecutor(2) as pool:
        for got in pool.map(get_months,sorted(jobs)):
            evidence.update(got)
    rows,dated = [],[]
    for row in old["rows"]:
        r = row.copy()
        if r["checked"]:
            k = L.mapping(r)
            m = sorted(evidence.get(k,()))
            dated.append(dict(zip(("id","market","pair"),k))|{"months":m})
            if notice:=fence(r["market"],r["id"],r["pair"]):
                end,url = notice
                r.update(notice_status="UNKNOWN",notice_end_utc=end,
                         reason=r["reason"]+"; use prior level matches only, then end at official settlement",
                         official_urls=list(dict.fromkeys(r["official_urls"]+[url])))
            hits = sum(x[2] for x in m)
            level,outcome = status(len(m),hits,r["notice_status"])
            r.update(comparable_months=len(m),matched_months=hits,level_status=level,status=outcome)
        rows.append(r)
    revised = old|{
        "rows":rows,"counts":dict(Counter(r["status"] for r in rows)),
        "confirmed":{m:[[r["id"],r["pair"]] for r in rows
                        if r["market"]==m and r["status"]=="CONFIRMED"] for m in ("spot","futures")},
        "archive_manifest_sha256":hashes,"identity_review_sha256":F.digest(Path(__file__).read_bytes()),
        "legacy_policy_sha256":F.digest(baseline.read_bytes()),
    }
    rebuilt = out/"identity_baseline_rebuilt_16_17.json"
    F.F.put_json(rebuilt,revised)
    F.F.put_json(out/"identity_months_16_17.json",
                 {"snapshots_sha256":raw_hash,"archive_manifest_sha256":hashes,"rows":dated})
    B.build(data,out,rebuilt,allow_early=True)


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("data",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("baseline",type=Path)
    x = p.parse_args()
    rebuild(x.data,x.out,x.baseline)
