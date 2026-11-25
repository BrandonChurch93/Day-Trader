"""Replay 13. --selftest uses invented bars. --run is a frozen, one-shot read."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

try:
    from . import common_13 as C
    from . import fetch_13 as F
except ImportError:
    import common_13 as C
    import fetch_13 as F

HERE = Path(__file__).resolve().parent
DRAFT = HERE / "PREREG_13_year_or_method_DRAFT.md"
PLAN = HERE / "PREREG_13_year_or_method.md"
CONFIG = F.ROOT / "config/thresholds.yaml"
RESULT = HERE / "results_13.json"
LOCAL_LOCK = HERE / "score_13.lock"
DURABLE_LOCK = F.DATA / "score_13.lock"


class Refused(RuntimeError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def frozen(text):
    statuses = re.findall(r"^Status:[^\r\n]*", text, re.MULTILINE | re.IGNORECASE)
    return len(statuses) == 1 and re.match(r"^Status: frozen\b", statuses[0]) is not None


def read_frozen_plan():
    if DRAFT.exists() or DRAFT.is_symlink() or not PLAN.is_file():
        raise Refused("refused: remove the draft by renaming it to the final plan at freeze")
    plan = PLAN.read_bytes()
    if not frozen(plan.decode()):
        raise Refused("refused: plan 13 status is not frozen")
    return plan


def unused_paths(result, local, durable):
    for path in (result, local, durable):
        if path.exists() or path.is_symlink():
            raise Refused(f"refused: previous attempt exists: {path}")


def lock_file(path, job):
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as e:
        raise Refused(f"refused: lock already exists: {path}") from e
    with os.fdopen(fd, "w") as file:
        json.dump(job,file,sort_keys=True,indent=2)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())


def guard(plan, result, local, durable, job):
    if not frozen(plan):
        raise Refused("refused: plan 13 status is not frozen")
    unused_paths(result,local,durable)
    # Shared data lock survives a checkout reset. Never delete a failure lock.
    lock_file(durable,job)
    lock_file(local,job)


def verify_parameters(p):
    expected = {"start","end","universe_top_n","rise_days","dip_pct","dip_lookback_hours",
                "take_pct","stop_pct","max_hold_hours","cost_bps_per_side","other_costs_bps",
                "shown_leverage","liquidation_drop_pct","financing_bps_per_8h","random_draws",
                "seed","min_years_above","hot_n","random_percentile","judged_leverage",
                "financing_interval_hours","max_flagged_share_pct","min_trades_per_year","new_trials",
                "max_missing_hours"}
    if p.keys() != expected:
        raise Refused(f"unexpected plan keys: {sorted(p.keys() ^ expected)}")
    if (p["new_trials"] != 2 or p["judged_leverage"] != 1 or p["shown_leverage"] <= 1
        or min(p[k] for k in ("rise_days","dip_lookback_hours","max_hold_hours","random_draws",
                              "hot_n","universe_top_n","min_years_above","financing_interval_hours")) < 1
        or p["hot_n"] > p["universe_top_n"]
        or not 0 <= p["random_percentile"] <= 100
        or not 0 <= p["max_flagged_share_pct"] <= 100
        or type(p["max_missing_hours"]) is not int or p["max_missing_hours"] < 0
        or not 0 < p["liquidation_drop_pct"] < 100
        or not 0 < p["dip_pct"] < 100 or not 0 < p["stop_pct"] < 100
        or p["take_pct"] <= 0 or p["min_trades_per_year"] < 0 or p["financing_bps_per_8h"] < 0
        or len(set(p["other_costs_bps"]+[p["cost_bps_per_side"]])) != 1+len(p["other_costs_bps"])
        or not all(0 <= b < 10_000 for b in p["other_costs_bps"]+[p["cost_bps_per_side"]])):
        raise Refused("invalid plan definitions")


def load_verified_data(p, expected):
    mf = (F.DATA/"manifest.json").read_bytes()
    raw = (F.DATA/"snapshots.json").read_bytes()
    hashes = {"manifest_sha256":digest(mf),"snapshots_sha256":digest(raw)}
    if hashes != expected:
        raise Refused("input metadata changed after fingerprinting")
    manifest = json.loads(mf)
    snapshots = json.loads(raw)
    if (manifest["errors"] or manifest["collection_parameters"] != F.collection_parameters(p)
        or manifest["snapshot_sha256"] != digest(raw)
        or manifest.get("excluded_ids") != json.loads(json.dumps(F.EXCLUDE))
        or manifest["pair_mappings"] != json.loads(json.dumps(F.MANUAL))
        or any(len(s["kept"]) != p["universe_top_n"] or
               s["kept"] != [r for r in s["top_raw"] if r["id"] not in F.EXCLUDE][:p["universe_top_n"]]
               for s in snapshots if not s.get("hole"))):
        raise Refused("archive is not complete and aligned with the plan manifest")
    for s in snapshots:
        if not s.get("hole"):
            path = F.DATA/"cmc"/(s["date"].replace("-","")+".html.gz")
            if digest(path.read_bytes()) != s["sha256"]:
                raise Refused(f"snapshot fingerprint mismatch: {s['date']}")
    grouped = {}
    for key,meta in manifest["archives"].items():
        pair = key.split("/")[4]
        grouped.setdefault(pair,[]).append((key,meta))
    if not grouped or "BTCUSDT" not in grouped:
        raise Refused("archive is empty or lacks BTC scale data")

    def load_group(item):
        pair, files = item
        bars = {}
        for key,meta in files:
            blob = (F.DATA/"archives"/key).read_bytes()
            if digest(blob) != meta["sha256"]:
                raise Refused(f"archive fingerprint mismatch: {key}")
            count = 0
            for row in F.zip_rows(blob):
                t = F.open_epoch(row[0])
                o,l,c = map(float,(row[1],row[3],row[4]))
                if (not all(math.isfinite(v) and v > 0 for v in (o,l,c)) or l > min(o,c)
                    or t in bars or t % F.HOUR):
                    raise Refused(f"archive bad or duplicate bar: {key} {t}")
                bars[t] = C.Bar(o,l,c)
                count += 1
            if count != meta["n"]:
                raise Refused(f"archive count differs from manifest: {key}")
        return pair,C.Series(bars)

    with ThreadPoolExecutor(6) as pool:
        data = dict(pool.map(load_group, grouped.items()))
    return snapshots,data,{**hashes,"archives":len(manifest["archives"]),"pairs":len(data)}


def now():
    return datetime.now(timezone.utc).isoformat()


def git_head():
    return subprocess.run(["git","rev-parse","HEAD"], cwd=F.ROOT, text=True, capture_output=True,
                          check=True).stdout.strip()


def run():
    plan = read_frozen_plan()
    unused_paths(RESULT,LOCAL_LOCK,DURABLE_LOCK)
    cfg = CONFIG.read_bytes()
    p = F.yaml.safe_load(cfg)["replay_13_plan"]["value"]
    verify_parameters(p)
    locked_inputs = {f"{file}_sha256":digest((F.DATA/f"{file}.json").read_bytes())
                     for file in ("manifest","snapshots")}
    job = {"mode":"run","run_started_utc":now(),"command":[sys.executable, *sys.argv],
           "git_head":git_head(),"plan_sha256":digest(plan),"config_sha256":digest(cfg), "inputs":locked_inputs,
           "code_sha256":{x.name:digest(x.read_bytes()) for x in
                          (HERE/"fetch_13.py",HERE/"common_13.py",HERE/"score_13.py",HERE/"test_13.py")}}
    if read_frozen_plan() != plan:
        raise Refused("refused: frozen plan changed while staging")
    guard(plan.decode(),RESULT,LOCAL_LOCK,DURABLE_LOCK,job)
    try:
        snapshots, data, data_fingerprints = load_verified_data(p,locked_inputs)
        answer = C.replay(snapshots,data,p)
        answer.update(job=job,inputs=data_fingerprints,parameters=p,admitted_coins=F.roster(snapshots),
                      run_finished_utc=now())
        if RESULT.exists() or RESULT.is_symlink():
            raise Refused("result appeared after lock")
        F.put_json(RESULT,answer)
        print(RESULT)
    except Exception as e:
        # Locks remain. A failed invocation is never silently rerunnable.
        sys.stderr.write(f"run failed after taking lock: {type(e).__name__}: {e}\n")
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest",action="store_true")
    g.add_argument("--run",action="store_true")
    args = p.parse_args()
    if args.selftest:
        import unittest
        try:
            from . import test_13
        except ImportError:
            import test_13
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_13)
        if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
            raise SystemExit(1)
    else:
        try:
            run()
        except Refused as e:
            raise SystemExit(str(e))


if __name__ == "__main__":
    main()
