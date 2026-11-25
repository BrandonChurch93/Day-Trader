"""Count held live futures coin-weeks from stored timestamps only."""
import argparse
from collections import defaultdict
from pathlib import Path

from . import score_16 as A


def count(data,out):
    F,A16,C = A.F,A.M,A.C
    F.DATA = data
    F.F.DATA = data.parent/"replay_13"
    p13,p = F.config()
    viewed,held = [F.json_read(data/name) for name in
                   ("manifest_futures.json","manifest_futures_held.json")]
    a,b = viewed["archives"],held["archives"]
    if any(a[key]!=b[key] for key in a.keys() & b.keys()):
        raise ValueError("shared manifest entries differ")
    merged = {"archives":a|b}
    cutoff = A.funding_cutoff(p,p13,A.source_ranges(viewed))
    runtime = p|{"end":F.F.utc(cutoff).date().isoformat()}
    windows = list(C.year_windows(runtime))
    monday = {t for _,start,end in windows for t in range(start,end,C.WEEK)}
    before,after = [A.I.Timeline(F.json_read(out/name),cutoff) for name in
                    ("identity_policy_asof_before_chronology_16_17.json",A.IDENTITY)]
    old = F.json_read(data/A.IDENTITY)
    old_allow = {tuple(x) for x in old["confirmed"]["futures"]}
    held_rows = F.json_read(data/"snapshots_16.json")["held"]
    candidates = {asset.pair for snap in held_rows for r in snap["kept"] for asset in F.perp_segments(r)}
    trade,pays = defaultdict(set),defaultdict(set)
    for key,m in merged["archives"].items():
        symbol = key.split("/")[5]
        if symbol not in candidates or not m["n"] or m["first"]>=cutoff:
            continue
        clock = m["first"],m["last"],m["n"]
        funding = "/fundingRate/" in key
        if not funding:
            if "/klines/" not in key:
                continue
            might = {t for t in monday if clock[0]<=t<=clock[1]}
            if not might:
                continue
            # The original clock audit established unique hourly stamps.
            # A count equal to the full interval therefore proves continuity.
            if clock[0]%A16.H==clock[1]%A16.H==0 and clock[2]==1+(clock[1]-clock[0])//A16.H:
                trade[symbol].update(might)
                continue
        raw = F.archive_root(key,m["where"]).read_bytes()
        if F.digest(raw)!=m["sha256"]:
            raise ValueError("archive fingerprint changed")
        ts = list(F.csv_times(raw))
        if (ts[0],ts[-1],len(ts))!=clock:
            raise ValueError("archive clock fingerprint changed")
        if funding:
            pays[symbol].update(t for u in ts if (t:=(u+30)//60*60)<=cutoff)
        else:
            trade[symbol].update(might.intersection(ts))
    ranges = A.source_ranges(merged)
    tapes = {symbol:A16.Tape(C.Series(dict.fromkeys(trade[symbol])),C.Series({}),
                             dict.fromkeys(pays[symbol]),ranges.get(symbol,()))
             for symbol in candidates}
    counts = {}
    for year,start,end in windows:
        annual = [0,0,0]
        for t in range(start,end,C.WEEK):
            snap = A16.snapshot_at(held_rows,t)
            for i,allow in enumerate((old_allow,before.at(t)["futures"],after.at(t)["futures"])):
                pool,_ = A16.market_pool(snap,tapes,t,min(t+C.WEEK,end),p,allow)
                annual[i] += len(pool)
        counts[str(year)] = dict(zip(("all_month_original","asof_before","asof_after"),annual))
    expected = F.json_read(data/"coverage_16_17.json")["coverage"]["held"]
    if any(v["all_month_original"]!=expected[y]["confirmed_live_contract_coin_weeks"]
           for y,v in counts.items()):
        raise ValueError("original all-month coverage no longer reproduces")
    F.F.put_json(out/"held_live_coverage_chronology_16_17.json",counts)
    print(counts)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("data",type=Path)
    p.add_argument("out",type=Path)
    x=p.parse_args()
    count(x.data,x.out)
