"""Plan 19. No real input is opened by the synthetic self-test."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import isfinite
import os
from pathlib import Path
import re
import resource
import subprocess
import unittest

import yaml

from . import archive_18 as A, common_19 as C

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT.parent / "rig" / "data"
RUN = DATA / "replay_19"
PLAN = "research_rig/PREREG_19_monday_asia.md"
CONFIG = "config/thresholds.yaml"
LEDGER = "research_rig/TRIAL_LEDGER.md"
ARCHIVE_DEP = "research_rig/archive_18.py", "research_rig/common_18.py"
PINNED = (PLAN, CONFIG, LEDGER, *ARCHIVE_DEP,
          *(f"research_rig/{name}_19.py" for name in ("common", "score", "test")))
MANIFEST = RUN / "manifest_19.json"
LOCK = RUN / "score_19.lock"
RESULT = ROOT / "research_rig" / "results_19.json"
STORES = {"replay_16": DATA / "replay_16" / "archives", "replay_19": RUN / "archives"}
US_HOUR = C.HOUR * 10**6
FOLDERS = {"klines", "markPriceKlines", "fundingRate"}


class Refused(Exception):
    """Public refusal communicates only a fixed code and named path."""
    def __init__(self, code, path):
        super().__init__(code)
        self.code, self.path = code, path


def digest(b):
    return sha256(b).hexdigest()


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def memory():
    with open("/proc/meminfo", encoding="ascii") as f:
        kb = int(next(line for line in f if line.startswith("MemAvailable:")).split()[1])
    if kb < 1572864:
        raise C.Incomplete("available system memory below 1.5 GiB")


def authorize(commit, manifest_pin):
    if not re.fullmatch(r"[0-9a-f]{40}", commit or "") or not A.SHA.fullmatch(manifest_pin or ""):
        raise C.Incomplete("approved commit and trusted manifest digest are required")
    if git("rev-parse", "HEAD").decode().strip() != commit or git("status", "--porcelain"):
        raise C.Incomplete("check out the clean approved commit before running")
    approved = {}
    for name in PINNED:
        try:
            approved[name] = (ROOT / name).read_bytes()
            if approved[name] != git("show", f"{commit}:{name}"):
                raise C.Incomplete("approved scorer bytes differ")
        except (Exception, KeyboardInterrupt):
            raise Refused("P19_AUTH_REFUSED", ROOT / name) from None
    if not re.search(rb"(?m)^Status FROZEN\.$", approved[PLAN]):
        raise C.Incomplete("Plan 19 remains a draft")
    if not re.search(rb"(?m)^\| 155 \|[^\n]+PREREG_19_monday_asia", approved[LEDGER]):
        raise C.Incomplete("missing ledger row 155")
    if RUN.is_symlink() or RUN.stat().st_uid != os.geteuid() or RUN.stat().st_mode & 0o022:
        raise C.Incomplete("canonical run folder must not be group/world writable or linked")
    try:
        p = C.policy(yaml.safe_load(approved[CONFIG])["replay_19_plan"]["value"])
    except (Exception, KeyboardInterrupt):
        raise Refused("P19_AUTH_REFUSED", ROOT / CONFIG) from None
    try:
        m = json.loads(A.read_pinned(MANIFEST, manifest_pin))
        if m.get("version") != 1 or not isinstance(m.get("archives"), dict):
            raise C.Incomplete("invalid Plan 19 archive inventory")
    except (Exception, KeyboardInterrupt):
        raise Refused("P19_INVENTORY_REFUSED", MANIFEST) from None
    return p, m["archives"], {name: digest(raw) for name, raw in approved.items()}


def select(archives, p):
    seen = {}
    for name, spec in archives.items():
        match = A.BULK.fullmatch(name)
        if not match or match[3] not in C.SYMBOLS or match[2] not in FOLDERS:
            raise C.Incomplete("inventory has an unexpected archive path")
        a, b = A.archive_span(match)
        if not isinstance(spec, dict) or set(spec) != {"where", "sha256"} or spec["where"] not in STORES:
            raise C.Incomplete("inventory has an unexpected archive entry")
        if not isinstance(spec["sha256"], str) or not A.SHA.fullmatch(spec["sha256"]):
            raise C.Incomplete("inventory has an invalid archive hash")
        if b <= p["start"] or a >= p["end"]:
            raise C.Incomplete("inventory includes a file outside the replay period")
        key = match[3], match[2]
        spans = seen.setdefault(key, [])
        if any(a < end and b > start for start, end in spans):
            raise C.Incomplete("inventory has overlapping files")
        spans.append((a, b))
        yield name, spec, key, a, b


def add_row(tape, kind, a, b, row, p):
    stamp = A.clock_us(row[0])
    h = (stamp + US_HOUR // 2) // US_HOUR
    if kind == "fundingRate":
        if (abs(stamp - h * US_HOUR) > p["funding_jitter_seconds"] * 10**6 or
                h % p["funding_hours"] or int(row[1]) != p["funding_hours"]):
            raise C.Incomplete("unexpected settlement clock")
        if not (a <= h < b or a * US_HOUR <= stamp < b * US_HOUR):
            raise C.Incomplete("settlement outside archive span")
    elif stamp != h * US_HOUR or not a <= h < b:
        raise C.Incomplete("bar outside archive span or off-hour")
    elif len(row) < 7 or A.clock_us(row[6]) // 1000 != (stamp + US_HOUR) // 1000 - 1:
        raise C.Incomplete("bar has a missing or noncanonical closing clock")
    if not p["start"] <= h < p["end"]:
        return
    if kind == "fundingRate":
        dst, value = tape.rates, float(row[2])
        valid = isfinite(value)
    elif kind == "markPriceKlines":
        dst, value = tape.marks, float(row[1])
        valid = isfinite(value) and value > 0
    else:
        dst, value = tape.opens, float(row[1])
        close, volume = float(row[4]), float(row[5])
        valid = (all(isfinite(x) and x > 0 for x in (value, close)) and
                 isfinite(volume) and volume >= 0)
    if h in dst or not valid:
        raise C.Incomplete("duplicate or invalid archive row")
    dst[h] = value
    if kind == "klines":
        tape.closes[h] = close
        if volume == 0:
            tape.zero_trade.add(h)


def validate_tapes(tapes, p):
    for symbol, tape in tapes.items():
        for h in range(p["start"], p["end"]):
            if h not in tape.opens or h not in tape.closes:
                yield symbol, "klines", h
            if h % p["funding_hours"] == 0:
                if h not in tape.marks:
                    yield symbol, "markPriceKlines", h
                if h not in tape.rates:
                    yield symbol, "fundingRate", h
    zero_trade = {symbol: tape.zero_trade for symbol, tape in tapes.items() if tape.zero_trade}
    if zero_trade:
        for entry in C.starts(p, 0):
            for candles in C.trade_candle_roles(entry, p).values():
                for h in candles:
                    for symbol, hours in zero_trade.items():
                        if h in hours:
                            yield symbol, "klines", h


def verify_inventory(archives, p):
    """Before claiming the one-shot, check only paths, sizes and period metadata."""
    spans = {(s, k): [] for s in C.SYMBOLS for k in FOLDERS}
    selected = []
    for name, spec, (symbol, kind), a, b in select(archives, p):
        memory()
        store = STORES[spec["where"]].resolve()
        path = store / name
        try:
            if path.resolve() != path or not path.is_file() or not 0 < path.stat().st_size <= A.MAX_ZIP_BYTES:
                raise C.Incomplete("missing, linked or oversized ZIP")
        except (Exception, KeyboardInterrupt):
            raise Refused("P19_INVENTORY_REFUSED", path) from None
        spans[symbol, kind].append((max(a, p["start"]), min(b, p["end"])))
        selected.append((path, spec["sha256"], symbol, kind, a, b))
    for periods in spans.values():
        cursor = p["start"]
        for a, b in sorted(periods):
            if a != cursor:
                raise C.Incomplete("archive inventory has a period gap")
            cursor = b
        if cursor != p["end"]:
            raise C.Incomplete("archive inventory stops short of the required period")
    return selected


def load(selected, p):
    tapes = {s: C.Tape({}, {}, {}, {}) for s in C.SYMBOLS}
    for path, pin, symbol, kind, a, b in selected:
        memory()
        try:
            for row in A.zip_rows(A.read_pinned(path, pin)):
                add_row(tapes[symbol], kind, a, b, row, p)
        except (Exception, KeyboardInterrupt):
            raise Refused("P19_LOAD_REFUSED", path) from None
    fault = next(validate_tapes(tapes, p), None)
    if fault is not None:
        symbol, kind, h = fault
        path = next((f for f, _, s, k, a, b in selected if (s, k) == (symbol, kind) and a <= h < b), MANIFEST)
        raise Refused("P19_LOAD_REFUSED", path)
    return tapes


def write(stream, payload):
    stream.write(json.dumps(payload, sort_keys=True, allow_nan=False) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def sync(folder):
    fd = os.open(folder, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def claim(lock, result, job, prepare, calculate):
    if os.path.lexists(lock) or os.path.lexists(result):
        raise Refused("P19_CONSUMED", lock if os.path.lexists(lock) else result)
    prepared = prepare()
    if os.path.lexists(result):
        raise Refused("P19_CONSUMED", result)
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise Refused("P19_CONSUMED", lock) from None
    with os.fdopen(fd, "w") as stream:
        write(stream, dict(status="consumed", **job))
        sync(lock.parent)
        try:
            payload = calculate(prepared)
            with result.open("x") as output:
                write(output, payload)
            sync(result.parent)
        except BaseException:
            write(stream, {"status": "failed"})
            raise
        write(stream, {"status": "completed", "output": result.name})


def go(commit, pin):
    try:
        memory()
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        cap = min(v for v in (A.MEMORY_CAP, soft, hard) if v != resource.RLIM_INFINITY)
        resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
        os.nice(max(0, 10 - os.nice(0)))
    except (Exception, KeyboardInterrupt):
        raise Refused("P19_RESOURCE_REFUSED", "/proc/meminfo") from None
    try:
        p, archives, hashes = authorize(commit, pin)
    except Refused:
        raise
    except (Exception, KeyboardInterrupt):
        raise Refused("P19_AUTH_REFUSED", ROOT / PLAN) from None
    if os.path.lexists(ROOT / "research_rig" / LOCK.name):
        raise Refused("P19_CONSUMED", ROOT / "research_rig" / LOCK.name)
    job = dict(started_utc=datetime.now(timezone.utc).isoformat(), ledger=155,
               commit=commit, manifest_sha256=pin, repo_sha256=hashes)

    def prepare():
        try:
            selected = verify_inventory(archives, p)
        except Refused:
            raise
        except (Exception, KeyboardInterrupt):
            raise Refused("P19_INVENTORY_REFUSED", MANIFEST) from None
        try:
            tapes = load(selected, p)
            memory()
            return tapes
        except Refused:
            raise
        except (Exception, KeyboardInterrupt):
            raise Refused("P19_LOAD_REFUSED", MANIFEST) from None

    def calculate(tapes):
        return dict(job=job, policy=p, outcome=C.measure(tapes, p, check=memory))

    claim(LOCK, RESULT, job, prepare, calculate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--selftest", action="store_true")
    choice.add_argument("--calibration", action="store_true")
    choice.add_argument("--go", action="store_true")
    parser.add_argument("--approval-commit")
    parser.add_argument("--manifest-sha256")
    args = parser.parse_args()
    if args.selftest:
        from . import test_19
        tests = unittest.defaultTestLoader.loadTestsFromModule(test_19)
        return int(not unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful())
    if args.calibration:
        from . import test_19
        p = C.policy(yaml.safe_load((ROOT / CONFIG).read_bytes())["replay_19_plan"]["value"])
        test_19.calibrate(p)
        return 0
    try:
        go(args.approval_commit, args.manifest_sha256)
    except Refused as exc:
        safe_path = str(exc.path).encode("unicode_escape").decode("ascii")
        parser.exit(1, f"{exc.code} {safe_path}\n")
    except (Exception, KeyboardInterrupt):
        parser.exit(1, f"P19_RUN_REFUSED {LOCK}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
