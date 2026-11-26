"""Plan 47 synthetic calibration, approved no-return validation or one sealed score."""
import argparse
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIVATE = Path("/home/user/workspace/rig/data/replay_47")
INPUTS, RUN = PRIVATE / "inputs", PRIVATE / "score"
PLAN = "research_rig/PREREG_47_edgar_altcoin_treasuries.md"
DOCKET = "research_rig/DOCKET_47_preprice.md"
CONFIG = "config/thresholds.yaml"
ENGINE = "research_rig/common_47.py"
PINS = "research_rig/PINNED_47.json"
APPROVAL = "research_rig/APPROVAL_47.md"
NAMES = {PLAN, DOCKET, CONFIG, ENGINE, "research_rig/test_47.py", "research_rig/score_47.py"}
APPROVAL_RE = (
    rb"Approved by the lead: plan 47, one custodian collection, validation and one scored run, "
    rb"freeze commit ([0-9a-f]{40}), freeze SHA-256 ([0-9a-f]{64}), "
    rb"event manifest SHA-256 ([0-9a-f]{64})\.\n"
)
PIN = re.compile(r"[0-9a-f]{64}")
CAP = 8 * 1024 * 1024


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused(code)


def pin(v):
    return type(v) is str and PIN.fullmatch(v) is not None


def digest(b):
    return sha256(b).hexdigest()


def exact_json(pairs):
    result = dict(pairs)
    need(len(result) == len(pairs), "DUPLICATE_JSON_KEY")
    return result


def reject_constant(_):
    raise Refused("JSON_NUMBER")


def parse(b):
    return json.loads(b, parse_float=Decimal, object_pairs_hook=exact_json, parse_constant=reject_constant)


def enc(x):
    return (json.dumps(x, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def checked(path, expected=None, private=False):
    need(path.resolve(strict=True) == path, "FILE_PATH")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as f:
        st = os.fstat(f.fileno())
        need(stat.S_ISREG(st.st_mode) and 0 < st.st_size <= CAP, "FILE")
        if private:
            need(st.st_uid == os.geteuid() and stat.S_IMODE(st.st_mode) == 0o600, "PRIVATE")
        b = f.read(CAP + 1)
    need(len(b) <= CAP and (expected is None or (pin(expected) and digest(b) == expected)), "DIGEST")
    return b


def checked_dir(path):
    info = path.lstat()
    need(path.resolve(strict=True) == path and stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid()
         and stat.S_IMODE(info.st_mode) == 0o700, "PRIVATE")


def native_hash(path, expected):
    need(path.resolve(strict=True) == path, "FILE_PATH")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as f:
        st = os.fstat(f.fileno())
        need(stat.S_ISREG(st.st_mode) and st.st_size > 0
             and st.st_uid == os.geteuid() and stat.S_IMODE(st.st_mode) == 0o600, "PRIVATE")
        h = sha256()
        while block := f.read(1024 * 1024):
            h.update(block)
        need(h.hexdigest() == expected, "NATIVE_HASH")


def custody(receipt, packet, approval, manifest, bundle, root):
    """Verify a lead-pinned independent custody review and byte-for-byte retained objects."""
    need(type(receipt) is dict and set(receipt) == {"schema", "status", "approval_commit",
         "manifest_sha256", "bundle_sha256", "objects", "keys"}
         and type(receipt["schema"]) is int and receipt["schema"] == 1
         and receipt["status"] == "INDEPENDENT_NATIVE_NO_RETURN_REVIEW_COMPLETE"
         and receipt["approval_commit"] == approval and receipt["manifest_sha256"] == manifest
         and receipt["bundle_sha256"] == bundle and type(receipt["objects"]) is dict
         and type(receipt["keys"]) is list, "CUSTODY")
    expected = sorted([r["venue"], r["product"], r["time"], r["state"], r["source_sha256"]] for r in packet["rows"])
    need(receipt["keys"] == expected and set(receipt["objects"]) == {row[-1] for row in expected}, "CUSTODY_COVERAGE")
    checked_dir(root)
    for sha, obj in receipt["objects"].items():
        need(pin(sha) and type(obj) is dict and set(obj) == {"urls", "receipt_sha256"}
             and type(obj["urls"]) is dict and pin(obj["receipt_sha256"]), "CUSTODY_OBJECT")
        # URL describes the retained native object. Request/status/coverage details are
        # reviewed independently and retained as a second sealed object.
        native_scope = {(v, p) for v, p, _, _, h in expected if h == sha}
        need(set(obj["urls"]) == {p for _, p in native_scope}
             and len({v for v, _ in native_scope}) == 1, "CUSTODY_URL")
        for venue, product in native_scope:
            url = obj["urls"][product]
            need(type(url) is str and (url == f"https://api.exchange.coinbase.com/products/{product}/candles"
                 if venue == "coinbase" else url.startswith(("https://support.kraken.com/",
                 "https://www.kraken.com/", "https://drive.google.com/"))), "CUSTODY_URL")
        checked(root / (obj["receipt_sha256"] + ".json"), obj["receipt_sha256"], private=True)
        native_hash(root / sha, sha)


def git(*args, allow=False):
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0"}
    proc = subprocess.run(["/usr/bin/git", "--no-replace-objects", "-c", "core.fsmonitor=false",
                           "-C", str(ROOT), *args], capture_output=True, env=env, timeout=15)
    need(allow or proc.returncode == 0, "APPROVAL")
    return proc


def authorize(approval, frozen_pin):
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval) and pin(frozen_pin), "APPROVAL")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode()
         and not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")

    def obj(rev, name):
        return git("show", f"{rev}:{name}").stdout

    clause = re.fullmatch(APPROVAL_RE, obj(approval, APPROVAL))
    need(clause is not None, "APPROVAL")
    frozen, approved_pin, docket_pin = (v.decode() for v in clause.groups())
    parents = git("rev-list", "--parents", "-n", "1", approval).stdout.decode().split()[1:]
    need(frozen_pin == approved_pin and len(parents) == 1 and
         git("merge-base", "--is-ancestor", frozen, parents[0], allow=True).returncode == 0, "APPROVAL")
    need(git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", approval).stdout
         == f"A\t{APPROVAL}\n".encode() and
         git("cat-file", "-e", f"{frozen}:{APPROVAL}", allow=True).returncode != 0, "APPROVAL")
    b = checked(ROOT / PINS, frozen_pin)
    need(b == obj(frozen, PINS) == obj(approval, PINS), "FROZEN_PACKAGE")
    manifest = parse(b)
    need(type(manifest) is dict and set(manifest) == NAMES and all(map(pin, manifest.values())), "FROZEN_PACKAGE")
    blobs = {name: checked(ROOT / name, sha) for name, sha in manifest.items()}
    need(all(blob == obj(frozen, name) == obj(approval, name) for name, blob in blobs.items()), "FROZEN_PACKAGE")
    plan = blobs[PLAN].splitlines()
    need([l for l in plan if l.startswith(b"Status ")] == [b"Status FROZEN."] and
         [l for l in plan if l.startswith(b"EVENT_MANIFEST_SHA256:")] ==
         [b"EVENT_MANIFEST_SHA256: " + docket_pin.encode()], "FROZEN_PLAN")
    for name, row in (("research_rig/TRIAL_LEDGER.md", 180), ("docs/QUEUE.md", 82)):
        prefix = f"| {row} |".encode()
        a, z = ([l for l in obj(commit, name).splitlines() if l.startswith(prefix)] for commit in (frozen, approval))
        need(len(a) == 1 and a == z and (b"`" + PLAN.encode() + b"`") in a[0], "FROZEN_LEDGER")
    return frozen, docket_pin, blobs


def load(cfg_b, engine_b):
    matches = re.findall(rb"(?m)^replay_47_plan:\n  value: (\{[^\n]+\})\n", cfg_b)
    need(len(matches) == 1, "CONFIG")
    engine = ModuleType("plan47_verified")
    exec(compile(engine_b, ENGINE, "exec"), engine.__dict__)
    return engine, engine.vals(parse(matches[0]))


def sync(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_new(path, b):
    with os.fdopen(os.open(path, os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_WRONLY, 0o600), "wb") as f:
        f.write(b)
        f.flush()
        os.fsync(f.fileno())


def unused(run):
    checked_dir(run)
    need(not any(run.iterdir()), "CONSUMED_OR_NOT_EMPTY")


def score_once(run, pins, validated, evaluator):
    unused(run)
    job = pins | {"claimed_utc": datetime.now(timezone.utc).isoformat()}
    try:
        write_new(run / "score_47.lock", enc(job))
    except FileExistsError:
        raise Refused("CONSUMED_OR_NOT_EMPTY") from None
    sync(run)
    result = enc({"job": job, "outcome": evaluator(*validated)})
    tmp = run / ".results_47.tmp"
    write_new(tmp, result)
    os.link(tmp, run / "results_47.json", follow_symlinks=False)
    sync(run)
    tmp.unlink()
    sync(run)
    return digest(result)


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "P47_ARGUMENTS\n")


def main():
    cli = Parser(description=__doc__, allow_abbrev=False)
    mode = cli.add_mutually_exclusive_group(required=True)
    for name in ("--calibration", "--scope", "--validate-inputs", "--go"):
        mode.add_argument(name, action="store_true")
    cli.add_argument("--approval-commit")
    cli.add_argument("--freeze-sha256")
    cli.add_argument("--bundle-sha256")
    cli.add_argument("--custody-sha256")
    a = cli.parse_args()
    os.umask(0o077)
    try:
        if a.calibration:
            need(not any((a.approval_commit, a.freeze_sha256, a.bundle_sha256, a.custody_sha256)), "ARGUMENTS")
            C, p = load(checked(ROOT / CONFIG), checked(ROOT / ENGINE))
            print(enc(C.calibration(p)).decode(), end="")
            return 0
        need(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize == 0
             and not any(k.startswith(("PYTHON", "GIT_", "LD_")) or k in {"TZ", "TZDIR"} for k in os.environ),
             "ENVIRONMENT")
        if os.nice(0) < 10:
            os.nice(10 - os.nice(0))
        freeze, events_pin, sources = authorize(a.approval_commit, a.freeze_sha256)
        C, p = load(sources[CONFIG], sources[ENGINE])
        checked_dir(PRIVATE)
        checked_dir(INPUTS)
        manifest = parse(checked(INPUTS / "manifest.json", events_pin, private=True))
        rows = C.events(manifest, p)
        need(manifest["docket_sha256"] == digest(sources[DOCKET]), "DOCKET_BINDING")
        need(len(rows) >= p["min_events"], "COUNT_FLOOR")
        scope = C.bar_keys(rows, p)
        need(datetime.now(timezone.utc) >= max(C.stamp(t) for _, _, t in scope) + timedelta(minutes=1),
             "SOURCE_NOT_YET_MATURE")
        if a.scope:
            need(a.bundle_sha256 is None and a.custody_sha256 is None, "ARGUMENTS")
            print(enc({"manifest_sha256": events_pin, "granularity_seconds": 60, "want": sorted(scope)}).decode(), end="")
            return 0
        unused(RUN)
        need(pin(a.bundle_sha256) and pin(a.custody_sha256), "BUNDLE_PIN")
        packet = parse(checked(INPUTS / "bundle.json", a.bundle_sha256, private=True))
        bars = C.validate(packet, scope, events_pin)
        receipt = parse(checked(INPUTS / "custody.json", a.custody_sha256, private=True))
        custody(receipt, packet, a.approval_commit, events_pin, a.bundle_sha256, INPUTS / "native")
        if a.validate_inputs:
            print("P47_VALIDATED")
            return 0
        pins = {"approval_commit": a.approval_commit, "freeze_commit": freeze, "freeze_sha256": a.freeze_sha256,
                "manifest_sha256": events_pin, "bundle_sha256": a.bundle_sha256,
                "custody_sha256": a.custody_sha256}
        result = score_once(RUN, pins, (rows, bars, p), C.evaluate)
        print("P47_SCORED " + result)
        return 0
    except Refused as e:
        print("P47_" + str(e), file=sys.stderr)
    except (OSError, ValueError, ArithmeticError, TypeError, KeyError, subprocess.SubprocessError):
        print("P47_REFUSED", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
