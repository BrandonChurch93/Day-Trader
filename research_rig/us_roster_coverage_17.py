"""Report dated manifest coverage only. Never open an archive."""
import argparse
from collections import defaultdict
from pathlib import Path

from . import score_16 as A, us_roster_17 as U


def report(data,source):
    F = A.F
    p13,p = F.config()
    viewed,held,spot = [F.json_read(data/name) for name in
        ("manifest_futures.json","manifest_futures_held.json","manifest_spot.json")]
    cut = A.funding_cutoff(p,p13,A.source_ranges(viewed))
    policy = F.json_read(data/"next"/A.IDENTITY)
    start = next(A.C.year_windows(p))[1]
    futures = defaultdict(list)
    for key,m in (viewed["archives"]|held["archives"]).items():
        if "/klines/" in key and m["n"]:
            futures[key.split("/")[5]].append((m["first"],m["last"]))
    spot_pairs = {key.split("/")[4] for key,m in spot["archives"].items()
                  if m["n"] and m["first"]<cut and m["last"]>=start}
    dated = A.I.Timeline(policy,cut).admitted(p|{"end":F.F.utc(cut).date().isoformat()})
    def monday(t):
        d=F.F.utc(t)
        return (d.date()-A.timedelta(days=d.weekday())).isoformat()
    lines = ["# Replay 17 US roster mapping and stored coverage","",
             "MEASURED from pinned manifest clock metadata only. Weeks are Monday UTC labels, within the "
             "scoring window; a bar anywhere in the week counts, regardless of Monday liveness. "
             "Spot input means at least one dated-admitted mapping has stored spot bars in the window. "
             "This is not a count of eligible trades, and no bar values were read.","",
             f"Roster SHA-256 `{U.SHA256}`. MEASURED list only, excluding BTC, ETH, PAXG and USDC.","",
             "| Roster coin | CMC ID | Stored perpetual symbols | First week with bars | Last week with bars | Spot ranking input |",
             "|---|---:|---|---|---|---|"]
    for row in U.rows(source.read_bytes()):
        i = row["id"]
        mapped = {r["pair"] for r in policy["rows"] if r["id"]==i and
                  r["market"]=="futures" and r["checked"] and r["notice_status"]!="REMOVED"}
        ranges = [(a.pair,max(lo,a.begin,start),min(hi,a.end-3600,cut-3600))
                  for a in F.perp_segments(row) if a.pair in mapped
                  for lo,hi in futures[a.pair]]
        ranges = [(s,lo,hi) for s,lo,hi in ranges if lo<=hi]
        names = ", ".join(sorted({s for s,_,_ in ranges})) or "None stored"
        first = monday(min(lo for _,lo,_ in ranges)) if ranges else "n/a"
        last = monday(max(hi for _,_,hi in ranges)) if ranges else "n/a"
        ok = any((i,s) in dated["spot"] and s in spot_pairs for _,_,s in F.spot_segments(row))
        lines.append(f"| {row['symbol']} | {i} | {names} | {first} | {last} | {'Available' if ok else 'No admitted spot input'} |")
    return "\n".join(lines)+"\n"


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("data",type=Path)
    p.add_argument("source",type=Path)
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    text=report(args.data,args.source)
    if args.output is None:
        print(text,end="")
    else:
        with args.output.open("x") as out:
            out.write(text)
