"""One-shot Replay 17. The selftest only uses invented bars."""
import argparse
import json
import sys

try:
    from . import score_16 as A, common_17 as M
except ImportError:
    import score_16 as A
    import common_17 as M

F,S = A.F,A.S
HERE = A.HERE
RESULT = HERE/"results_17.json"
LOCAL_LOCK = HERE/"score_17.lock"
DURABLE_LOCK = F.DATA/"score_17.lock"
HELD = "manifest_futures_held.json"
CODE = A.CODE+("common_17.py","score_17.py","report_17.py","test_17.py")


def validate(p,p13,p16):
    expected = {"hot_n","rise_days","dip_pct","dip_lookback_hours","take_pct","stop_pct",
                "max_hold_hours","cost_bps_per_side","other_costs_bps","shown_leverage",
                "forced_close_rise_pct","random_draws","seed","min_years_above","min_rising_years",
                "min_trades_per_year","max_flagged_share_pct"}
    if p.keys()!=expected:
        raise S.Refused(f"unexpected Replay 17 keys: {sorted(p.keys() ^ expected)}")
    if (any(p[k]!=p13[k] for k in ("hot_n","rise_days","dip_pct","dip_lookback_hours",
                                   "take_pct","stop_pct","max_hold_hours","shown_leverage"))
        or p["forced_close_rise_pct"]<=0 or p["random_draws"]<1 or p["min_trades_per_year"]<1
        or not 0<=p["max_flagged_share_pct"]<=100 or
        not 1<=p["min_rising_years"]<=p["min_years_above"]<=7 or
        not (len(p["other_costs_bps"])==2 and
             0<=min(p["other_costs_bps"])<p["cost_bps_per_side"]<max(p["other_costs_bps"])<10000)):
        raise S.Refused("invalid Replay 17 parameters or changed Rule B trigger")
    A.validate(p16,p13)


def combine_futures(viewed,held,snapshot_sha):
    if held["errors"] or held["snapshots_sha256"]!=snapshot_sha:
        raise S.Refused("held futures manifest incomplete or assigned to different snapshot lists")
    a,b = viewed["archives"],held["archives"]
    if any(a[k]!=b[k] for k in a.keys() & b.keys()):
        raise S.Refused("same archive listed with different metadata")
    return {"archives":a|b}


def run():
    raw,peer = A.peer_plan_bytes(),A.plan_bytes()
    S.unused_paths(RESULT,LOCAL_LOCK,DURABLE_LOCK)
    config = (F.F.ROOT/"config/thresholds.yaml").read_bytes()
    cfg = F.F.yaml.safe_load(config)
    p13,p16,p = (cfg[f"replay_{i}_plan"]["value"] for i in (13,16,17))
    validate(p,p13,p16)
    expected = {n:F.digest((F.DATA/n).read_bytes()) for n in (*A.META,HELD)}
    job = {"command":[sys.executable,*sys.argv],"git_head":S.git_head(),"start_utc":S.now(),
           "plan_sha256":F.digest(raw),"peer_plan_sha256":F.digest(peer),
           "config_sha256":F.digest(config),"inputs":expected,
           "code_sha256":{name:F.digest((HERE/name).read_bytes()) for name in CODE}}
    if A.peer_plan_bytes()!=raw or A.plan_bytes()!=peer:
        raise S.Refused("one of the plans changed before lock")
    S.guard(raw.decode(),RESULT,LOCAL_LOCK,DURABLE_LOCK,job)
    try:
        snap,spot_meta,viewed = A.metadata({k:expected[k] for k in A.META},peer)
        held = (F.DATA/HELD).read_bytes()
        if F.digest(held)!=expected[HELD]:
            raise S.Refused("held archive manifest changed after lock")
        futures = combine_futures(viewed,json.loads(held),expected["snapshots_16.json"])
        ranges = A.source_ranges(futures)
        cutoff = A.funding_cutoff(p16,p13,A.source_ranges(viewed))
        spot = A.load_groups(spot_meta,True,cutoff)
        tapes = A.load_groups(futures,False,cutoff)
        for symbol,tape in tapes.items():
            tape.covered = ranges.get(symbol,())
        replay = M.replay(snap,spot,tapes,p,p16|{"end":F.F.utc(cutoff).date().isoformat()},p13)
        replay.update(job=job,finished_utc=S.now(),cutoff_utc=F.F.utc(cutoff).isoformat(),parameters=p,
                      perp_identity_mappings=F.PERP_MANUAL,perp_identity_evidence=F.PERP_EVIDENCE,
                      perp_identity_uncertainties=F.PERP_UNCERTAIN,bundled_aliases=F.BUNDLES)
        if RESULT.exists() or RESULT.is_symlink():
            raise S.Refused("result appeared after lock")
        F.F.put_json(RESULT,replay)
        print(RESULT)
    except Exception as exc:
        sys.stderr.write(f"Replay 17 failed after taking lock: {exc}\n")
        raise


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--selftest",action="store_true")
    mode.add_argument("--run",action="store_true")
    args = parser.parse_args()
    if args.selftest:
        import unittest
        import test_17
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_17)
        raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    try:
        run()
    except S.Refused as exc:
        raise SystemExit(str(exc))
