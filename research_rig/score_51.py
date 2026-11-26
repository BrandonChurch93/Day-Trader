"""Plan 51: approval-bound counts or a single lead-only historical score."""
import argparse
from array import array
from bisect import bisect_left
from collections import defaultdict
from datetime import date, timedelta
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

import yaml

try:
    from . import calibrate_51 as K, common_51 as C, fetch_13 as F
except ImportError:
    import calibrate_51 as K
    import common_51 as C
    import fetch_13 as F

ROOT = Path(__file__).resolve().parents[1]
PLAN = "research_rig/PREREG_51_momentum_when_it_pays.md"
APPROVAL = "research_rig/APPROVAL_51.md"
CALIBRATION = "research_rig/CALIBRATION_51.json"
CONFIG = "config/thresholds.yaml"
BOUND = (PLAN, CONFIG, CALIBRATION, "research_rig/common_13.py", "research_rig/fetch_13.py",
         "research_rig/common_51.py", "research_rig/score_51.py", "research_rig/calibrate_51.py",
         "research_rig/test_51.py", "practice/traders/E05_momentum_regime_watch.md")
APPROVAL_LINE = (rb"Approved by the lead agent for Plan 51 historical counts and one lead-only score "
                 rb"from freeze ([0-9a-f]{40}) with Replay 13 manifest ([0-9a-f]{64})\.\n")
ARCHIVE = re.compile(r"data/spot/(monthly|daily)/klines/([A-Z0-9]+)/1h/\2-1h-"
                     r"(\d{4}-\d{2}(?:-\d{2})?)\.zip")


class Refused(Exception):
    pass


def require(valid, code):
    if not valid:
        raise Refused("P51_" + code)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], stderr=subprocess.DEVNULL)


def sha(raw):
    return sha256(raw).hexdigest()


def private_read(root, rel, cap=16 << 20):
    path = root / rel
    require(path.resolve() == path and path.is_relative_to(root), "INPUT_PATH")
    with path.open("rb") as handle:
        raw = handle.read(cap + 1)
    require(len(raw) <= cap, "INPUT_SIZE")
    return raw


def resolve(fixture):
    if fixture:
        scratch = ROOT.parent
        require(scratch.parent == Path("/tmp") and scratch.name.startswith("plan51-fixture-")
                and ROOT.name == "repo" and (ROOT / ".synthetic-only").read_bytes() == b"SYNTHETIC ONLY\n",
                "FIXTURE_ROOT")
        return scratch / "input", scratch / "run"
    require(not (ROOT / ".synthetic-only").exists(), "FIXTURE_MODE")
    return F.DATA, ROOT.parent / "rig/data/replay_51"


def authorize(fixture):
    require(not git("status", "--porcelain", "--untracked-files=all"), "DIRTY")
    parents = git("rev-list", "--parents", "-1", "HEAD").decode().split()
    require(len(parents) == 2, "APPROVAL_PARENT")
    head, freeze = parents
    require(git("diff-tree", "--no-commit-id", "--name-status", "-r", head).decode().splitlines()
            == [f"A\t{APPROVAL}"], "APPROVAL_DIFF")
    match = re.fullmatch(APPROVAL_LINE, git("show", f"{head}:{APPROVAL}"))
    require(match and match[1].decode() == freeze, "APPROVAL_TEXT")
    files = {path: git("show", f"{freeze}:{path}") for path in BOUND}
    require(all((ROOT / path).read_bytes() == raw for path, raw in files.items()), "PIN")
    require(b"\nStatus: FROZEN\n" in files[PLAN], "NOT_FROZEN")
    cfg = yaml.safe_load(files[CONFIG])
    p = cfg["replay_51_plan"]["value"]
    replay13 = cfg["replay_13_plan"]["value"]
    calibration = json.loads(files[CALIBRATION])
    require(bool(calibration.get("cli_fixture")) == fixture, "CALIBRATION_MODE")
    release = K.release(calibration["rows"], p)
    require(release["unlocked"] and all(calibration[k] == v for k, v in release.items()), "CALIBRATION")
    require(all(p[key] == replay13[key] for key in
                ("universe_top_n", "rise_days", "hot_n", "cost_bps_per_side", "max_missing_hours",
                 "judged_leverage")), "REPLAY13_RULES")
    return head, freeze, match[2].decode(), p, replay13


class PackedSeries:
    def __init__(self, times, opens, closes):
        self.times, self.opens, self.closes = times, opens, closes
        self.bars = self

    def __contains__(self, t):
        i = bisect_left(self.times, t)
        return i < len(self.times) and self.times[i] == t

    def __getitem__(self, t):
        i = bisect_left(self.times, t)
        if i == len(self.times) or self.times[i] != t:
            raise KeyError(t)
        return C.prior.Bar(self.opens[i], 0, self.closes[i])

    def open_at_or_after(self, t, end):
        i = bisect_left(self.times, t)
        if i < len(self.times) and self.times[i] < end:
            return self.times[i], self.opens[i]
        return None

    def usable_lookback(self, a, b, limit):
        lo, hi = bisect_left(self.times, a), bisect_left(self.times, b)
        return (hi < len(self.times) and self.times[lo] == a and self.times[hi] == b
                and (b - a) // F.HOUR - (hi - lo) <= limit)


def load(root, manifest_hash, p13, fixture, space):
    raw = private_read(root, "manifest.json")
    require(sha(raw) == manifest_hash, "MANIFEST_HASH")
    mf = json.loads(raw)
    require(not mf["errors"] and mf["collection_parameters"] == F.collection_parameters(p13)
            and mf["excluded_ids"] == json.loads(json.dumps(F.EXCLUDE))
            and mf["pair_mappings"] == json.loads(json.dumps(F.MANUAL)), "MANIFEST_SHAPE")
    raw = private_read(root, "snapshots.json")
    require(sha(raw) == mf["snapshot_sha256"], "SNAPSHOT_HASH")
    snapshots = json.loads(raw)
    expected = []
    lo, hi = (date.fromisoformat(p13[x]) for x in ("start", "end"))
    for month in F.months(lo.replace(day=1) - timedelta(days=1), hi):
        expected.append(str(F.sunday(month)))
    require(bool(snapshots) and (fixture or [s["date"] for s in snapshots] == expected)
            and all(a["known_at"] < b["known_at"] for a, b in zip(snapshots, snapshots[1:])), "SNAPSHOT_DATES")
    for s in snapshots:
        day = date.fromisoformat(s["date"])
        require(s["known_at"] == F.stamp(day + timedelta(days=1)) and day.weekday() == 6, "SNAPSHOT_CLOCK")
        if s.get("hole"):
            require(s["kept"] == [], "SNAPSHOT_HOLE")
            continue
        ranks = s["top_raw"]
        require(ranks[0]["id"] == 1 and ranks[0]["cmcRank"] == 1
                and len({r["id"] for r in ranks}) == len(ranks)
                and all(a["cmcRank"] <= b["cmcRank"] for a, b in zip(ranks, ranks[1:]))
                and len(s["kept"]) == p13["universe_top_n"]
                and s["kept"] == [r for r in ranks if r["id"] not in F.EXCLUDE][:p13["universe_top_n"]],
                "SNAPSHOT_RANKS")
        require(sha(private_read(root, f"cmc/{day:%Y%m%d}.html.gz")) == s["sha256"], "SNAPSHOT_ARCHIVE")
    groups = defaultdict(list)
    for rel, meta in mf["archives"].items():
        match = ARCHIVE.fullmatch(rel)
        require(match and (match[1] == "daily") == (len(match[3]) == 10), "ARCHIVE_KEY")
        groups[match[2]].append((match[3], rel, meta))
    require("BTCUSDT" in groups, "NO_BTC")
    data = {}
    for pair, group in sorted(groups.items()):
        require(shutil.disk_usage(space).free >= (3 << 29), "LOW_DISK")
        times, opens, closes = array("q"), array("d"), array("d")
        for _, rel, meta in sorted(group):
            blob = private_read(root, "archives/" + rel)
            require(sha(blob) == meta["sha256"], "ARCHIVE_HASH")
            n = 0
            for row in F.zip_rows(blob):
                t = F.open_epoch(row[0])
                o, low, c = map(float, (row[1], row[3], row[4]))
                require(t % F.HOUR == 0 and (not times or t > times[-1])
                        and all(math.isfinite(v) and v > 0 for v in (o, low, c))
                        and low <= min(o, c), "BAR_SHAPE")
                times.append(t)
                opens.append(o)
                closes.append(c)
                n += 1
            require(n == meta["n"], "ARCHIVE_ROWS")
        data[pair] = PackedSeries(times, opens, closes)
    return snapshots, data


def exclusive(path, body):
    encoded = json.dumps(body, sort_keys=True, allow_nan=False) + "\n"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", action="store_true")
    mode.add_argument("--go", action="store_true")
    parser.add_argument("--synthetic-fixture", action="store_true")
    args = parser.parse_args()
    try:
        root, run = resolve(args.synthetic_fixture)
        head, freeze, manifest, p, p13 = authorize(args.synthetic_fixture)
        require(run.resolve() == run and not run.is_relative_to(ROOT), "RUN_PATH")
        require(run.is_dir(), "RUN_DIRECTORY")
        lock, result = run / "score_51.lock", run / "results_51.json"
        require(not os.path.lexists(lock) and not os.path.lexists(result), "SPENT")
        require(shutil.disk_usage(run).free >= (3 << 29), "LOW_DISK")
        snapshots, data = load(root, manifest, p13, args.synthetic_fixture, run)
        panels = C.prepare(snapshots, data, p)
        if args.validate:
            print(json.dumps(C.counts(panels), sort_keys=True))
            return 0
        require(shutil.disk_usage(run).free >= (3 << 29), "LOW_DISK")
        try:
            exclusive(lock, {"approval": head, "freeze": freeze, "manifest_sha256": manifest})
        except FileExistsError:
            raise Refused("P51_SPENT") from None
        scored = C.run(data, panels, snapshots, p)
        exclusive(result, scored)
        return 0
    except Refused as exc:
        print("REFUSED", exc)
    except Exception:
        print("REFUSED P51_CHECK_FAILED")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
