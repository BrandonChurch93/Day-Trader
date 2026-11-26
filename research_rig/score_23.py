"""Plan 23 scorer. One shot.

  python3 score_23.py --selftest                       the tests in test_23.py, invented bars only
  python3 score_23.py --run --approval-commit <c> --freeze-sha256 <sha>   the one real run, after the lead's approval

The run refuses before its lock if anything pinned in freeze.json differs. It then claims an exclusive lock file
(O_CREAT|O_EXCL) in RUN, checks every pin again, and only then opens a bar's prices. A lock that exists means the run
has been used up, whatever happened after it was taken. Results go to RUN/results_23.json, off repo.
"""
import argparse, datetime as dt, json, os, sys

import common_23 as C
import fetch_23 as F

RESULT = "results_23.json"
LOCK = "score_23.lock"


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def verify(trusted, P=None):
    """Every pin, from bytes. Returns the freeze record, the frozen events and the paths."""
    P = P or F.paths()
    if not trusted:
        raise C.Refused("P23_NO_FREEZE_SHA")
    raw = open(P["freeze"], "rb").read()
    if C.sha256_bytes(raw) != trusted:
        raise C.Refused("P23_FREEZE_SHA " + P["freeze"])
    rec = json.loads(raw)
    for f, h in rec["code_sha256"].items():
        if C.sha256_file(os.path.join(C.HERE, f)) != h:
            raise C.Refused("P23_CODE_CHANGED " + f)
    for key, path in (("ipos_sha256", P["ipos"]), ("breakpoints_sha256", P["bps"]), ("snips_sha256", P["snips"]),
                      ("events_selected_sha256", P["selected"]), ("events_frozen_sha256", P["frozen"])):
        if C.sha256_file(path) != rec[key]:
            raise C.Refused("P23_INPUT_CHANGED " + path)
    events = C.parse_events(open(P["frozen"], "rb").read())
    ok = [e for e in events if e["status"] == "ok"]
    if any(e["status"] == "refused_no_exit_bar" for e in events):
        raise C.Refused("P23_REFUSED_NO_EXIT_BAR")
    if set(rec["bars_sha256"]) != {e["accession"] for e in ok} | {"SPY"}:
        raise C.Refused("P23_BAR_SET")
    for name, h in rec["bars_sha256"].items():
        path = os.path.join(P["bars"], name + ".json")
        if C.sha256_file(path) != h:
            raise C.Refused("P23_BARS_CHANGED " + path)
    return rec, events, P


def claim(run, job):
    for f in (RESULT, LOCK):
        if os.path.lexists(os.path.join(run, f)):
            raise C.Refused("P23_ALREADY_USED " + os.path.join(run, f))
    fd = os.open(os.path.join(run, LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o444)
    with os.fdopen(fd, "w") as fh:
        json.dump(job, fh, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    fsync_dir(run)


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def compute(events, P, p):
    spy = {b["d"]: b for b in C.bars_from_json(open(os.path.join(P["bars"], "SPY.json"), "rb").read())}
    sessions = sorted(spy)
    rows = []
    for e in events:
        if e["status"] != "ok":
            continue
        bars = C.bars_from_json(open(os.path.join(P["bars"], e["accession"] + ".json"), "rb").read())
        bars = [b for b in bars if b["d"] <= str(p["bar_end"])]
        rows.append(C.trade(e, bars, spy, sessions, p))
    traded = [r for r in rows if r["status"] == "traded"]
    if len(traded) != len(rows):                       # no trade may drop after the lock
        raise C.Refused("P23_DROPPED_AFTER_LOCK")
    judged = [r for r in traded if r["group"] == "judged"]
    status = {}
    for e in events:
        status[(e["group"], e["status"])] = status.get((e["group"], e["status"]), 0) + 1
    return dict(judgment=C.judge(judged, p), shown=C.shown(traded, p),
                pre_lock_status={f"{g}|{s}": n for (g, s), n in sorted(status.items())},
                trades=traded)


def run(trusted, P=None):
    p = C.load_config()
    rec, events, P = verify(trusted, P)
    job = dict(command=[sys.executable, *sys.argv], start_utc=now(), freeze_sha256=trusted,
               code_sha256=rec["code_sha256"])
    claim(P["run"], job)
    try:
        rec2, events, P = verify(trusted, P)
        if rec2 != rec:
            raise C.Refused("P23_CHANGED_AFTER_LOCK")
        out = compute(events, P, p)
        out.update(job=job, finished_utc=now(), parameters=p)
        path = os.path.join(P["run"], RESULT)
        if os.path.lexists(path):
            raise C.Refused("P23_RESULT_APPEARED")
        with open(path, "x") as fh:
            json.dump(out, fh, sort_keys=True, indent=1, default=str)
            fh.flush()
            os.fsync(fh.fileno())
        fsync_dir(P["run"])
        print(path)
    except Exception as exc:
        sys.stderr.write(f"Plan 23 failed after taking the lock; the run is used up: {exc}\n")
        raise


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    ap.add_argument("--freeze-sha256")
    ap.add_argument("--approval-commit", help="the lead's approval commit; needed for --run")
    a = ap.parse_args()
    if a.selftest:
        import unittest, test_23
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_23)
        raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    try:
        C.authorize(a.approval_commit)
        run(a.freeze_sha256)
    except C.Refused as exc:
        raise SystemExit(str(exc))
