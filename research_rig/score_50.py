"""Plan 50: synthetic calibration, silent validation, or one locked score from an approved, pinned packet."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import sys
from types import ModuleType
from zoneinfo import reset_tzpath

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = Path("/home/user/workspace/rig/data")
INPUTS, RUN = DATA / "plan50_inputs", DATA / "replay_50"
PLAN = "research_rig/PREREG_50_cef_liquidations.md"
PINS = "research_rig/PINNED_50.json"
APPROVAL = "research_rig/APPROVAL_50.md"
CALENDAR = "research_rig/calendar_50.json"
ENGINE = "research_rig/common_50.py"
CALIBRATION = "research_rig/CALIBRATION_50.json"
CONFIG = "config/thresholds.yaml"
PIN_NAMES = {PLAN, CALENDAR, ENGINE, CALIBRATION, CONFIG, "research_rig/score_50.py", "research_rig/test_50.py"}
PROVENANCE = ("events.json", "instruments.json", "actions.json")
PROVENANCE_PINS = {"packet:" + name for name in PROVENANCE}
LEDGER_ROW, QUEUE_ROW = 184, 88
CAP = 64 * 1024 * 1024
APPROVAL_RE = (rb"Approved by the lead: plan 50, validation and one scored run, freeze commit ([0-9a-f]{40}), "
               rb"freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64}), "
               rb"events SHA-256 ([0-9a-f]{64}), instruments SHA-256 ([0-9a-f]{64}), actions SHA-256 ([0-9a-f]{64})\.\n")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P50_" + code)


def is_pin(v):
    return type(v) is str and re.fullmatch(r"[0-9a-f]{64}", v) is not None


def pinned(path, pin, private=False):
    need(is_pin(pin), "PIN")
    need(path.resolve() == path, "FILE")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as f:
        st = os.fstat(f.fileno())
        need(stat.S_ISREG(st.st_mode) and st.st_size <= CAP, "FILE")
        if private:
            need(st.st_uid == os.geteuid() and stat.S_IMODE(st.st_mode) == 0o600, "PRIVATE")
        blob = f.read(CAP + 1)
    need(len(blob) <= CAP and sha256(blob).hexdigest() == pin, "PIN")
    return blob


def unique(pairs):
    obj = dict(pairs)
    need(len(obj) == len(pairs), "JSON_DUPLICATE")
    return obj


def reject_number(_):
    raise Refused("P50_JSON_NUMBER")


def parse(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=reject_number, parse_float=Decimal)


def encode(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def private_dir(path):
    st = path.lstat()
    need(path.resolve() == path and stat.S_ISDIR(st.st_mode) and st.st_uid == os.geteuid()
         and stat.S_IMODE(st.st_mode) == 0o700, "PRIVATE")


def resources():
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = min(x for x in (768 * 1024 * 1024, soft, hard) if x != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
    if os.nice(0) < 10:
        os.nice(10 - os.nice(0))


def git(*args, allow=False):
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0"}
    proc = subprocess.run(["/usr/bin/git", "--no-replace-objects", "-c", "core.fsmonitor=false",
                           "-c", "safe.directory=*", "-C", str(REPO), *args], capture_output=True, env=env,
                          timeout=15)
    need(allow or proc.returncode == 0, "APPROVAL")
    return proc


def authorize(approval, freeze_pin, input_pin, *provenance):
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval) is not None, "APPROVAL")
    need(all(map(is_pin, (freeze_pin, input_pin, *provenance))), "PIN")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode()
         and not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")

    def contents(commit, name):
        return git("show", f"{commit}:{name}").stdout

    body = re.fullmatch(APPROVAL_RE, contents(approval, APPROVAL))
    need(body is not None, "APPROVAL")
    freeze, *named = (x.decode("ascii") for x in body.groups())
    parent = git("rev-list", "--parents", "-n", "1", approval).stdout.split()[1:]
    need(tuple(named) == (freeze_pin, input_pin, *provenance) and len(parent) == 1, "APPROVAL")
    # The approval sits directly on the freeze, so every pinned file (including the whole config) is the frozen one.
    need(parent[0].decode() == freeze, "APPROVAL")
    need(git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", approval).stdout
         == f"A\t{APPROVAL}\n".encode(), "APPROVAL")
    need(git("cat-file", "-e", f"{freeze}:{APPROVAL}", allow=True).returncode != 0, "APPROVAL")
    manifest = pinned(REPO / PINS, freeze_pin)
    need(manifest == contents(freeze, PINS) == contents(approval, PINS), "FREEZE")
    pins = parse(manifest)
    need(type(pins) is dict and set(pins) == PIN_NAMES | PROVENANCE_PINS and all(map(is_pin, pins.values()))
         and tuple(pins["packet:" + name] for name in PROVENANCE) == provenance, "FREEZE")
    blobs = {name: pinned(REPO / name, pins[name]) for name in PIN_NAMES}
    need(all(b == contents(freeze, name) == contents(approval, name) for name, b in blobs.items()), "FREEZE")
    need([line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")] == [b"Status FROZEN."], "FREEZE")
    link = b"`" + PLAN.encode() + b"`"
    for name, row, code in (("research_rig/TRIAL_LEDGER.md", LEDGER_ROW, "LEDGER"),
                            ("docs/QUEUE.md", QUEUE_ROW, "QUEUE")):
        prefix = f"| {row} |".encode()
        a, b = ([line for line in contents(commit, name).splitlines() if line.startswith(prefix)]
                for commit in (freeze, approval))
        need(len(a) == 1 and a == b and link in a[0], code)
    return freeze, blobs


def load_engine(blob):
    reset_tzpath(("/usr/share/zoneinfo",))
    C = ModuleType("common_50_verified")
    exec(compile(blob, ENGINE, "exec"), C.__dict__)
    return C


def read_config(blob):
    # One JSON-flow YAML value, read without a third-party parser.
    block = re.findall(rb"(?m)^replay_50_plan:\n  value: (\{[^\n]+\})\n", blob)
    need(len(block) == 1, "CONFIG")
    return parse(block[0])


def check_calibration(C, cfg, blob):
    report = C.calibrate(cfg)
    need(blob == encode(report) and all(row["pass_rate"].get("all", 0) <= report["null_ceiling"]
         for row in report["cells"] if row["planted_net_excess_pp"] == 0), "CALIBRATION")


def quote_name(key):
    symbol, session, side = key
    return f"quotes_{symbol}_{session}_{side}.json"


def load_inputs(input_dir, input_pin, provenance, C, calendar_blob, cfg):
    private_dir(input_dir)
    cal = C.calendar(parse(calendar_blob))
    m = parse(pinned(input_dir / "manifest.json", input_pin, private=True))
    need(C.exact(m, "schema mode feed adjustment first_day last_data collected_utc files")
         and type(m["schema"]) is int and m["schema"] == 1 and m["mode"] == "plan50_raw_sip_v1"
         and m["feed"] == "sip" and m["adjustment"] == "raw" and m["first_day"] == cfg["first_day"]
         and m["last_data"] == cfg["last_data"]
         and C.ny(C.utc(m["collected_utc"])).date() > C.day(cfg["last_data"]), "MANIFEST")
    need(type(m["files"]) is dict and set(PROVENANCE) <= set(m["files"]) and all(map(is_pin, m["files"].values()))
         and tuple(m["files"][name] for name in PROVENANCE) == provenance, "MANIFEST_FILES")

    def load(name):
        return parse(pinned(input_dir / name, m["files"][name], private=True))

    event_blob = load("events.json")
    rows = C.events(event_blob, cal, cfg)
    need(len(rows) >= cfg["min_placed"], "PREPRICE_COUNT_FLOOR")
    qkeys = sorted(C.quote_keys(rows))
    names = set(PROVENANCE) | {"bars.json"} | {quote_name(key) for key in qkeys}
    need(set(m["files"]) == names and {p.name for p in input_dir.iterdir()} == names | {"manifest.json"},
         "MANIFEST_FILES")
    identity = C.instruments(load("instruments.json"), rows)
    a = C.actions(load("actions.json"), rows)
    b = C.bars(load("bars.json"), identity)
    q = {key: C.quote_window(load(quote_name(key)), key, identity, cal, cfg) for key in qkeys}
    prepared = C.prepare(rows, b, q, a, cfg)
    excluded = event_blob["excluded"]
    return (rows, b, a, cfg, prepared), excluded


def unused(run):
    private_dir(run)
    need(not any(run.iterdir()), "CONSUMED_OR_NOT_EMPTY")


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def write_new(path, payload):
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def once(run, metadata, inputs, evaluate):
    unused(run)
    job = metadata | {"claimed_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    try:
        write_new(run / "score_50.lock", encode(job))
    except FileExistsError:
        raise Refused("P50_CONSUMED_OR_NOT_EMPTY") from None
    sync_dir(run)
    result = encode({"job": job} | evaluate(*inputs))
    tmp = run / ".results_50.tmp"
    write_new(tmp, result)
    os.link(tmp, run / "results_50.json", follow_symlinks=False)
    sync_dir(run)
    tmp.unlink()
    sync_dir(run)


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "P50_ARGUMENTS\n")


def check_environment():
    need(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize == 0
         and not any(k.startswith(("P50_", "PLAN50_", "GIT_", "PYTHON", "LD_")) or k in {"TZ", "TZDIR"}
                     for k in os.environ), "ENVIRONMENT")


def main():
    p = Parser(description=__doc__, allow_abbrev=False)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--calibrate", action="store_true")
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--go", action="store_true")
    for flag in ("--approval-commit", "--freeze-sha256", "--input-sha256", "--events-sha256",
                 "--instruments-sha256", "--actions-sha256"):
        p.add_argument(flag)
    a = p.parse_args()
    os.umask(0o077)
    try:
        if a.calibrate:
            # Synthetic only: reads the working-tree engine and config, never the input or run directories.
            need(not any((a.approval_commit, a.freeze_sha256, a.input_sha256, a.events_sha256, a.instruments_sha256, a.actions_sha256)), "ARGUMENTS")
            C = load_engine((REPO / ENGINE).read_bytes())
            sys.stdout.buffer.write(encode(C.calibrate(C.config(read_config((REPO / CONFIG).read_bytes())))))
            return
        pins = (a.approval_commit, a.freeze_sha256, a.input_sha256, a.events_sha256, a.instruments_sha256, a.actions_sha256)
        need(all(v is not None for v in pins), "ARGUMENTS")
        check_environment()
        freeze, blobs = authorize(*pins)
        C = load_engine(blobs[ENGINE])
        resources()
        try:
            cfg = C.config(read_config(blobs[CONFIG]))
            check_calibration(C, cfg, blobs[CALIBRATION])
            inputs, excluded = load_inputs(INPUTS, a.input_sha256, pins[3:], C, blobs[CALENDAR], cfg)
        except C.Refused as exc:
            raise Refused(str(exc)) from None
        if a.validate_inputs:
            print(encode(inputs[-1][2] | {"status": "P50_INPUTS_OK",
                  "excluded_preprice": dict(Counter(x["reason"] for x in excluded))}).decode(), end="")
            return
        meta = {"schema": 1, "ledger": LEDGER_ROW, "queue": QUEUE_ROW, "freeze_commit": freeze,
                "approval_commit": a.approval_commit, "freeze_sha256": a.freeze_sha256,
                "input_sha256": a.input_sha256,
                "provenance": dict(zip(PROVENANCE, pins[3:]))}
        need((freeze, blobs) == authorize(*pins), "APPROVAL")
        try:
            once(RUN, meta, inputs, lambda *args: C.evaluate(*args) | {"excluded_preprice": excluded})
        except C.Refused as exc:
            raise Refused(str(exc)) from None
    except Refused as exc:
        p.exit(2, f"{exc}\n")
    except Exception:
        p.exit(2, "P50_REFUSED\n")
    print("P50_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
