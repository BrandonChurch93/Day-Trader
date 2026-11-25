"""Build scratch point-in-time policy using dated results, not price fields."""
import argparse
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
import re

try:
    from . import fetch_16 as F, score_16 as S, identity_asof_16_17 as I, identity_chronology_16_17 as H
except ImportError:
    import fetch_16 as F
    import score_16 as S
    import identity_asof_16_17 as I
    import identity_chronology_16_17 as H


def urlkey(url):
    hit = re.search(r"(?:[a-f0-9]{32}|\d{9,})(?:$|/|\?)",url)
    return hit[0].rstrip("/?") if hit else url.rstrip("/")


def notice_date(text):
    pattern = r"(?:published on|last updated on|\bpublished)\s*:?\s*(\d{4}-\d{2}-\d{2})"
    hit = re.search(pattern,text,re.I)
    if not hit:
        hit = re.search(r"^# [^\n]+\n[ \t]*(\d{4}-\d{2}-\d{2})(?: \d\d:\d\d)?[ \t]*$",text,re.M)
    return date.fromisoformat(hit[1]).isoformat() if hit else None


def chronology(data,old):
    inv = F.json_read(data/"identity_inventory.json")
    retained = {}
    for name in old["archive_manifest_sha256"]:
        market = "spot" if name=="manifest_spot.json" else "futures"
        for key,meta in F.json_read(data/name)["archives"].items():
            if "/klines/" in key and meta["n"]:
                pair = key.split("/")[4 if market=="spot" else 5]
                clk = F.F.utc(meta["first"]).date().isoformat()
                k = (market,pair)
                retained[k] = min(retained.get(k,clk),clk)
    records,revived,floors,veto = [],{},{},set()
    for r in old["rows"]:
        if not r["checked"]:
            continue
        info = inv[str(r["id"])]
        x = info["markets"].get(r["market"]+"/"+r["pair"],{})
        segments = x.get("segments",())
        if r["market"]=="spot" and r["id"] in F.SPOT_SWAP_IDS:
            segments = [(F.F.utc(lo).isoformat() if lo>-10**12 else None,None)
                        for lo,hi,pair in F.spot_segments({"id":r["id"]}) if pair==r["pair"]]
        floor = (min(a[:10] for a,_ in segments) if segments and all(a for a,_ in segments) else None)
        k = (r["market"],r["pair"])
        bounds = H.gap_bounds(info["cmc_date_added"],retained.get(k),x.get("earliest_archive_month"),floor)
        direct = H.gap_bounds(info["cmc_date_added"],retained.get(k),segment_floor=floor)
        samples = set(info["samples"]) & {"held","viewed"}
        group = "both" if len(samples)==2 else next(iter(samples),"neither")
        row = {key:r[key] for key in ("id","name","market","pair","status","notice_status")}
        records.append(row|{"list":group,"gap_min_max_days":bounds,
                            "retained_min_max_days":direct,
                            "bucket":H.bucket(bounds),"retained_bucket":H.bucket(direct)})
        ident = (r["id"],r["market"],r["pair"])
        if bounds is not None and 0<bounds[1]<=H.TOLERANCE:
            floors[ident] = min(info["cmc_date_added"])
            if H.soft_removal(r,bounds):
                revived[ident] = floors[ident]
        elif bounds is None or bounds[1]>H.TOLERANCE:
            veto.add(ident)
    summary = {}
    for key in ("bucket","retained_bucket"):
        counts = defaultdict(Counter)
        for row in records:
            counts[row[key]][row["list"]] += 1
        summary[key] = {k:dict(v) for k,v in counts.items()}
    return records,summary,revived,floors,veto


def build(data,out,baseline=None,allow_early=False):
    old_path = baseline if baseline is not None else data/S.IDENTITY
    old = F.json_read(old_path)
    if "as_of_rows" in old:
        raise ValueError("provide the original all-month policy with --baseline")
    dated = F.json_read(out/"identity_months_16_17.json")
    snap_raw = (data/"snapshots_16.json").read_bytes()
    if (old["snapshots_sha256"] != F.digest(snap_raw)
        or old["snapshots_sha256"] != dated["snapshots_sha256"]
        or old["archive_manifest_sha256"] != dated["archive_manifest_sha256"]):
        raise ValueError("as-of evidence uses different source metadata")
    for name,sha in old["archive_manifest_sha256"].items():
        if F.digest((data/name).read_bytes())!=sha:
            raise ValueError(f"changed manifest {name}")
    chron = {}
    if allow_early:
        records,chron,revived,floors,veto = chronology(data,old)
        chron = chron|{"tolerance_days":H.TOLERANCE,
                       "inventory_sha256":F.digest((data/"identity_inventory.json").read_bytes())}
        amended = []
        for r in old["rows"]:
            k = (r["id"],r["market"],r["pair"])
            if k in floors:
                r = r|{"start_from_utc":floors[k]}
            if k in revived:
                # Restore the opportunity for level evidence, not an automatic
                # historical notice confirmation. Other identity removals stand.
                status = r["level_status"] if r["level_status"]!="NO_VERDICT" else "UNKNOWN"
                r = r|{"notice_status":"UNKNOWN","status":status,
                       "reason":r["reason"]+"; date-only veto lifted under the 60-day tolerance"}
            if k in veto and r["status"]!="REMOVED":
                r = r|{"notice_status":"REMOVED","status":"REMOVED",
                       "reason":r["reason"]+"; chronology upper bound exceeds 60 days or is unavailable"}
            amended.append(r)
        old = old|{"rows":amended,"counts":dict(Counter(r["status"] for r in amended)),
                   "notice_counts":dict(Counter(r.get("notice_status","NO_ARCHIVE") for r in amended)),
                   "confirmed":{m:[[r["id"],r["pair"]] for r in amended
                                   if r["market"]==m and r["status"]=="CONFIRMED"]
                                for m in ("spot","futures")}}
        F.F.put_json(out/"identity_chronology_counts_16_17.json",
                     {"counts":chron,"records":records,
                      "restored":[list(k)+[d] for k,d in sorted(revived.items())],
                      "hard_vetoes":[list(k) for k in sorted(veto)]})
    date_sets = defaultdict(set)
    for p in sorted(data.glob("identity_notices_*.json")):
        for hits in F.json_read(p).values():
            for hit in hits:
                if d:=notice_date(hit["snippet"]):
                    date_sets[urlkey(hit["url"])].add(d)
    supplemental = out/"identity_notice_dates_16_17.json"
    if supplemental.is_file():
        for url,d in F.json_read(supplemental).items():
            date_sets[urlkey(url)].add(date.fromisoformat(d).isoformat())
    p13,p = F.config()
    cutoff = S.funding_cutoff(p,p13,S.source_ranges(F.json_read(data/"manifest_futures.json")))
    cutoff_day=F.F.utc(cutoff).date().isoformat()
    key = lambda r:(r["id"],r["market"],r["pair"])
    evidence = {key(r):r["months"] for r in dated["rows"]}
    checked = [r for r in old["rows"] if r["checked"]]
    if set(evidence)!={key(r) for r in checked} or len(evidence)!=len(dated["rows"]):
        raise ValueError("dated results do not cover exactly the original checked mappings")
    rows,unknown = [],{}
    for r in checked:
        when = None
        if r["notice_status"]=="CONFIRMED":
            ds = [date_sets.get(urlkey(u),set()) for u in r["official_urls"]]
            if ds and all(ds):
                # In a conflict use the later documented publication date.
                when = max(max(d) for d in ds)
            else:
                for url,dates in zip(r["official_urls"],ds):
                    if not dates:
                        unknown[url] = unknown.get(url,0)+1
        start = F.F.boundary(r.get("start_from_utc"),-10**12)
        months = [m for m in evidence[key(r)]
                  if m[0]<=cutoff_day and start+86400<=m[1]<=cutoff]
        rows.append(dict(id=r["id"],market=r["market"],pair=r["pair"],
                         notice_status=r["notice_status"],notice_at=when,months=months,
                         all_month_status=r["status"])|
                    {k:r[k] for k in ("start_from_utc","notice_end_utc") if k in r})
    policy = old|{"schema_version":2,"all_month_policy_sha256":F.digest(old_path.read_bytes()),
                  "evidence_sha256":F.digest((out/"identity_months_16_17.json").read_bytes()),
                  "as_of_rows":rows,"as_of_cutoff_utc":cutoff_day}
    if allow_early:
        policy["chronology"] = {"tolerance_days":H.TOLERANCE,
             "counts_sha256":F.digest((out/"identity_chronology_counts_16_17.json").read_bytes())}
    rt = p|{"end":cutoff_day}
    timeline = I.Timeline(policy,cutoff)
    comparison = I.compare_counts(timeline,F.json_read(data/"snapshots_16.json"),rt)
    F.F.put_json(out/S.IDENTITY,policy)
    F.F.put_json(out/"identity_asof_changes_16_17.json",comparison)
    F.F.put_json(out/"identity_missing_notice_dates_16_17.json",unknown)
    print("notice-confirmed mappings with dated evidence",sum(r["notice_at"] is not None for r in rows))
    print("notice URLs without dates",len(unknown))


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("data",type=Path)
    p.add_argument("out",type=Path)
    p.add_argument("--baseline",type=Path,help="preserved original all-month policy")
    p.add_argument("--allow-early",action="store_true",help="amend date-only exclusions within 60 days")
    opt=p.parse_args()
    build(opt.data,opt.out,opt.baseline,opt.allow_early)
