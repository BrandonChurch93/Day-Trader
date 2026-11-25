"""One-shot Replay 16. --selftest never touches the real archive."""
import argparse
from bisect import bisect_left
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date,timedelta
import json
import math
import sys

import numpy as np

try:
    from . import common_13 as C, score_13 as S
    from . import common_16 as M, fetch_16 as F
except ImportError:
    import common_13 as C
    import score_13 as S
    import common_16 as M
    import fetch_16 as F

HERE = S.HERE
DRAFT = HERE/"PREREG_16_hot_five_hedged_DRAFT.md"
PLAN = HERE/"PREREG_16_hot_five_hedged.md"
PEER_DRAFT = HERE/"PREREG_17_short_the_peak_DRAFT.md"
PEER_PLAN = HERE/"PREREG_17_short_the_peak.md"
RESULT = HERE/"results_16.json"
LOCAL_LOCK = HERE/"score_16.lock"
DURABLE_LOCK = F.DATA/"score_16.lock"
META = ("snapshots_16.json","snapshot_fingerprints.json","manifest_spot.json","manifest_futures.json")
CODE = ("common_13.py","fetch_13.py","score_13.py","common_16.py","fetch_16.py",
        "score_16.py","test_16.py","report_16.py")


def plan_bytes():
    if DRAFT.exists() or DRAFT.is_symlink() or not PLAN.is_file():
        raise S.Refused("refused: draft exists or final Replay 16 plan is absent")
    raw = PLAN.read_bytes()
    if not S.frozen(raw.decode()):
        raise S.Refused("refused: Replay 16 is not frozen")
    return raw


def peer_plan_bytes():
    if PEER_DRAFT.exists() or PEER_DRAFT.is_symlink() or not PEER_PLAN.is_file():
        raise S.Refused("refused: both plans must be frozen before either shared-list run")
    raw = PEER_PLAN.read_bytes()
    if not S.frozen(raw.decode()):
        raise S.Refused("refused: Replay 17 is not frozen")
    return raw


def validate(p,p13):
    keys = {"start","end","held_rank_from","held_rank_to","long_share","cost_low","cost_judged",
            "cost_high","min_basket_names","live_funding_lookback_hours","short_stop_pct","random_draws",
            "seed","random_percentile","min_years_above","min_falling_years","max_year_loss_pct",
            "max_missing_hours","max_flagged_week_share_pct"}
    if p.keys() != keys:
        raise S.Refused(f"unexpected Replay 16 plan keys: {sorted(p.keys() ^ keys)}")
    if (p["long_share"] != .5 or p["held_rank_from"] != p13["universe_top_n"]+1
        or p["held_rank_to"]-p["held_rank_from"]+1 != p13["universe_top_n"]
        or (p["start"],p["end"]) != (p13["start"],p13["end"])
        or not 0<p["short_stop_pct"]<100
        or min(p[k] for k in ("min_basket_names","live_funding_lookback_hours","random_draws",
                              "min_years_above","min_falling_years"))<1
        or not 0<=p["random_percentile"]<=100 or p["max_missing_hours"]<0
        or not 0<=p["max_flagged_week_share_pct"]<=100 or not 0<p["max_year_loss_pct"]<=100
        or any(len(p[f"cost_{s}"])!=3 or not all(0<=x<10_000 for x in p[f"cost_{s}"])
               for s in M.LEVELS)):
        raise S.Refused("invalid Replay 16 plan")


def funding_range(key):
    lo = date.fromisoformat(key[-11:-4]+"-01")
    hi = (lo.replace(day=28)+timedelta(days=4)).replace(day=1)
    return F.F.stamp(lo),F.F.stamp(hi)


def merge_ranges(ranges):
    out = []
    for lo,hi in sorted(set(ranges)):
        if not out or out[-1][1]<lo:
            out.append((lo,hi))
        else:
            out[-1] = out[-1][0],max(out[-1][1],hi)
    return tuple(out)


def source_ranges(manifest):
    ranges = defaultdict(list)
    for key in manifest["archives"]:
        if "/monthly/fundingRate/" in key:
            ranges[key.split("/")[5]].append(funding_range(key))
    return {s:merge_ranges(v) for s,v in ranges.items()}


def funding_cutoff(p,p13,ranges):
    windows = list(C.year_windows(p13|{k:p[k] for k in ("start","end")}))
    _,start,last = windows[-1]
    valid = [t+C.WEEK for t in range(start,last,C.WEEK) if t+C.WEEK<=last and
             all(any(lo<=t and t+C.WEEK<hi for lo,hi in ranges.get(a.pair,()))
                 for a in M.MAJORS)]
    if not valid:
        raise S.Refused("no complete final-year major funding week")
    return max(valid)


class Packed:
    """Hourly OHLC subsets without millions of Python dictionary/bar objects."""
    def __init__(self, timestamps, values, ctor):
        self.times = timestamps
        self.values = values
        self.ctor = ctor

    def __contains__(self,t):
        i = bisect_left(self.times,t)
        return i<len(self.times) and self.times[i]==t

    def __getitem__(self,t):
        i = bisect_left(self.times,t)
        if i>=len(self.times) or self.times[i]!=t:
            raise KeyError(t)
        return self.ctor(*self.values[i])

    def get(self,t,default=None):
        i = bisect_left(self.times,t)
        return self.ctor(*self.values[i]) if i<len(self.times) and self.times[i]==t else default


def series(rows,ctor):
    rows.sort(key=lambda x:x[0])
    ts = np.fromiter((r[0] for r in rows),dtype=np.int64,count=len(rows))
    if len(ts)>1 and np.any(ts[1:]<=ts[:-1]):
        raise S.Refused("overlapping hourly archive files")
    vals = np.array([r[1:] for r in rows],dtype=np.float64).reshape(-1,3)
    out = C.Series.__new__(C.Series)
    out.bars = Packed(ts,vals,ctor)
    out.times = ts
    return out


def load_groups(manifest,spot,cutoff):
    jobs = defaultdict(list)
    for key,meta in manifest["archives"].items():
        parts = key.split("/")
        symbol = parts[4] if spot else parts[5]
        jobs[symbol].append((key,meta))
    def group(job):
        symbol,files = job
        trade,mark,funding = [],[],{}
        for key,meta in files:
            if meta["where"] not in (("replay_13","replay_16") if spot else ("replay_16",)):
                raise S.Refused(f"unknown archive source: {key}")
            blob = F.archive_root(key,meta["where"]).read_bytes()
            if F.digest(blob)!=meta["sha256"]:
                raise S.Refused(f"changed archive: {key}")
            count = 0
            for row in F.F.zip_rows(blob):
                count += 1
                t = F.F.open_epoch(row[0])
                if t>cutoff:
                    continue
                if "/fundingRate/" in key:
                    rate = float(row[2])
                    t = (t+30)//60*60
                    if t%M.H or t in funding or not math.isfinite(rate):
                        raise S.Refused(f"ambiguous funding clock: {key}")
                    funding[t] = rate
                else:
                    o,x,c = (float(row[i]) for i in (1,3 if spot else 2,4))
                    if (t%M.H or not all(math.isfinite(v) and v>0 for v in (o,x,c)) or
                        (x>min(o,c) if spot else x<max(o,c))):
                        raise S.Refused(f"malformed hourly bar: {key}")
                    (mark if "/markPriceKlines/" in key else trade).append((t,o,x,c))
            if count!=meta["n"]:
                raise S.Refused(f"archive row count changed: {key}")
        if spot:
            return symbol,series(trade,C.Bar)
        return symbol,M.Tape(series(trade,M.FBar),series(mark,M.FBar),funding,())
    with ThreadPoolExecutor(8) as pool:
        return dict(pool.map(group,jobs.items()))


def metadata(expected,plan):
    fresh = {name:(F.DATA/name).read_bytes() for name in META}
    if {k:F.digest(v) for k,v in fresh.items()}!=expected:
        raise S.Refused("metadata changed after lock")
    snapshots,fp,spot,futures = [json.loads(fresh[k]) for k in META]
    frozen_prefix = {"viewed_sha256":"ccb0fe0d5485","held_sha256":"f5bea224faad",
                     "combined_sha256":"3cc9dcf9bed1"}
    for name in ("viewed","held"):
        hashed = F.digest(json.dumps(snapshots[name],sort_keys=True,separators=(",",":"),
                                     ensure_ascii=False).encode())
        if fp[f"{name}_sha256"]!=hashed:
            raise S.Refused("list fingerprint does not match snapshot")
    if (fp["combined_sha256"]!=expected["snapshots_16.json"] or
        any(not fp[key].startswith(v) or v not in plan.decode() for key,v in frozen_prefix.items()) or
        fp["source_sha256"]!=F.digest((F.F.DATA/"snapshots.json").read_bytes())):
        raise S.Refused("snapshot fingerprints differ from the preregistered lists")
    for m in (spot,futures):
        if m["errors"] or m["snapshots_sha256"]!=expected["snapshots_16.json"]:
            raise S.Refused("archive incomplete or bound to different snapshot lists")
    return snapshots,spot,futures


def run():
    raw = plan_bytes()
    peer = peer_plan_bytes()
    S.unused_paths(RESULT,LOCAL_LOCK,DURABLE_LOCK)
    config = (F.F.ROOT/"config/thresholds.yaml").read_bytes()
    cfg = F.F.yaml.safe_load(config)
    p13,p = (cfg[f"replay_{n}_plan"]["value"] for n in (13,16))
    validate(p,p13)
    expected = {name:F.digest((F.DATA/name).read_bytes()) for name in META}
    job = {"command":[sys.executable,*sys.argv],"git_head":S.git_head(),"start_utc":S.now(),
           "plan_sha256":F.digest(raw),"peer_plan_sha256":F.digest(peer),
           "config_sha256":F.digest(config),"inputs":expected,
           "code_sha256":{name:F.digest((HERE/name).read_bytes()) for name in CODE}}
    if plan_bytes()!=raw or peer_plan_bytes()!=peer:
        raise S.Refused("plan changed before lock")
    S.guard(raw.decode(),RESULT,LOCAL_LOCK,DURABLE_LOCK,job)
    try:
        snapshots,sp,fut = metadata(expected,raw)
        ranges = source_ranges(fut)
        cutoff = funding_cutoff(p,p13,ranges)
        spot = load_groups(sp,True,cutoff)
        tapes = load_groups(fut,False,cutoff)
        for s,tape in tapes.items():
            tape.covered = ranges.get(s,())
        runtime = p|{"end":F.F.utc(cutoff).date().isoformat()}
        result = M.replay(snapshots,spot,tapes,runtime,p13)
        result.update(job=job,finished_utc=S.now(),cutoff_utc=F.F.utc(cutoff).isoformat(),
                      parameters=p,spot_identity_mappings=F.F.MANUAL,perp_identity_mappings=F.PERP_MANUAL,
                      perp_identity_evidence=F.PERP_EVIDENCE,perp_identity_uncertainties=F.PERP_UNCERTAIN,
                      bundled_aliases=F.BUNDLES)
        if RESULT.exists() or RESULT.is_symlink():
            raise S.Refused("result appeared after lock")
        F.F.put_json(RESULT,result)
        print(RESULT)
    except Exception as exc:
        sys.stderr.write(f"Replay 16 failed after taking lock: {exc}\n")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--selftest",action="store_true")
    mode.add_argument("--run",action="store_true")
    args = parser.parse_args()
    if args.selftest:
        import unittest
        import test_16
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_16)
        raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    try:
        run()
    except S.Refused as exc:
        raise SystemExit(str(exc))
