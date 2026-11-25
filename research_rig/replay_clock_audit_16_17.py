"""Count coverage, zero-volume spells and absent marks without reading prices."""
import argparse
from bisect import bisect_left
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import score_16 as A
from . import score_17 as B

F,C,M = A.F,A.C,A.M


def audit(data,out):
    data,out = data.resolve(),out.resolve()
    F.DATA = data
    F.F.DATA = data.parent/"replay_13"
    p13,p = F.config()
    viewed,held = [F.json_read(data/n) for n in ("manifest_futures.json","manifest_futures_held.json")]
    policy = F.json_read(out/A.IDENTITY)
    for name,h in policy["archive_manifest_sha256"].items():
        if F.digest((data/name).read_bytes())!=h:
            raise ValueError("manifest is not pinned by the selected identity policy")
    merged = B.combine_futures(viewed,held,policy["snapshots_sha256"])
    stop = A.funding_cutoff(p,p13,A.source_ranges(viewed))
    runtime = p|{"end":F.F.utc(stop).date().isoformat()}
    years = list(C.year_windows(runtime))
    mondays = {t for _,lo,hi in years for t in range(lo,hi,C.WEEK)}
    timeline = A.I.Timeline(policy,stop)
    allowed = {sym for _,sym in timeline.admitted(runtime)["futures"]}
    ranges = A.source_ranges(merged)
    snapshots = F.json_read(data/"snapshots_16.json")
    spans = defaultdict(set)
    floors = A.I.DatedPairs(timeline.floors["futures"])
    for snaps in snapshots.values():
        for snap in snaps:
            for row in snap["kept"]:
                for raw in F.perp_segments(row):
                    a = M.hourly_asset(A.I.bound_asset(raw,floors))
                    spans[raw.pair].add(a)
    groups = defaultdict(list)
    for key,m in merged["archives"].items():
        symbol = key.split("/")[5]
        if symbol in allowed or symbol in {"AGIXUSDT","ICPUSDT"}:
            groups[symbol].append((key,m))

    yes,no = M.FBar(1,1,1,1,1),M.FBar(1,1,1,1,0)
    def one(item):
        symbol,files = item
        trade,mark,funds = {},set(),set()
        vtrade,vmark = set(),set()
        for key,m in files:
            raw = F.archive_root(key,m["where"]).read_bytes()
            if F.digest(raw)!=m["sha256"]:
                raise ValueError("archive differs from pinned manifest")
            category = "mark" if "/markPriceKlines/" in key else "funding" if "/fundingRate/" in key else "trade"
            if category=="trade":
                for row in F.F.zip_rows(raw):
                    t = F.F.open_epoch(row[0])
                    if t<=stop:
                        if t in trade:
                            raise ValueError("overlapping trade rows")
                        trade[t] = no if float(row[5])==0 else yes
                        if key in viewed["archives"]:
                            vtrade.add(t)
            elif category=="mark":
                ts = {t for t in F.csv_times(raw) if t<=stop}
                mark.update(ts)
                if key in viewed["archives"]:
                    vmark.update(ts)
            else:
                funds.update(t for u in F.csv_times(raw) if (t:=(u+30)//60*60)<=stop)
        source = M.Tape(C.Series(trade),C.Series({}),dict.fromkeys(funds,0.),ranges.get(symbol,()))
        thin = C.Series({t:trade[t] for t in mondays if t in trade})
        def project(full):
            result = M.Tape(thin,C.Series({}),{},full.covered)
            result.dead,result.dead_starts = full.dead,full.dead_starts
            pay = full.payments
            result.payments = sorted({pay[i] for t in mondays if (i:=bisect_left(pay,t)-1)>=0})
            return result
        clock = project(source)
        for asset in spans[symbol]:
            if (asset.begin,asset.end)!=(-M.UNBOUNDED,M.UNBOUNDED):
                clock.scoped[asset.begin,asset.end] = project(source.within(asset))
        n = len(vtrade-vmark),len(trade.keys()-mark)
        return symbol,clock,n

    tapes,marks = {},{}
    with ThreadPoolExecutor(2) as pool:
        for sym,tape,n in pool.map(one,groups.items()):
            tapes[sym],marks[sym] = tape,n
    result = {}
    for sample,snaps in snapshots.items():
        result[sample] = {}
        for year,start,end in years:
            new_n,back_n = 0,0
            for t in range(start,end,C.WEEK):
                at = min(t+C.WEEK,end)
                snap = M.snapshot_at(snaps,t)
                ids = timeline.at(t)["futures"]
                live,_ = M.market_pool(snap,tapes,t,at,p,ids)
                old,_ = M.market_pool(snap,tapes,t,at,p,ids,legacy_file_gate=True)
                live_ids = {a.coin for a in live}
                new_n += len(live_ids)
                back_n += len(live_ids-{a.coin for a in old})
            result[sample][str(year)] = {"live_coin_weeks":new_n,"old_file_gate_returned":back_n}
    view_admitted = {k.split("/")[5] for k in A.admitted_archives(
        viewed,timeline.admitted(runtime)["futures"],False)["archives"]}
    stamp = lambda t:F.F.utc(t).isoformat() if t<10**12 else None
    outputs = {"coverage":result,"cutoff_utc":F.F.utc(stop).isoformat(),
               "trade_hours_without_mark":{"16":sum(marks[s][0] for s in view_admitted),
                                           "17":sum(marks[s][1] for s in allowed if s in marks)},
               "zero_runs_examples":{s:[[stamp(a),stamp(b)] for a,b in tapes[s].dead]
                                     for s in ("AGIXUSDT","ICPUSDT")}}
    F.F.put_json(out/"replay_clock_audit_16_17.json",outputs)
    print(outputs,flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("data",type=Path)
    p.add_argument("out",type=Path)
    x=p.parse_args()
    audit(x.data,x.out)
