"""Validate the pinned Plan 31 packet or score it once after an exclusive claim."""
import argparse
from datetime import datetime, timezone
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

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = Path("/home/user/workspace/rig/data")
INPUTS, RUN = DATA / "plan31_inputs", DATA / "replay_31"
PLAN, PINS, APPROVAL = ("PREREG_31_bond_etf_month_end.md", "PINNED_31.json", "APPROVAL_31.md")
PIN_NAMES = {PLAN, "calendar_25.json", "common_25.py", "common_31.py", "score_31.py", "test_31.py"}
CAP = 12 * 1024 * 1024
APPROVAL_RE = (rb"Approved by the lead: plan 31, validation and one scored run, freeze commit ([0-9a-f]{40}), "
               rb"freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64}), "
               rb"cash actions SHA-256 ([0-9a-f]{64})\.\n")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P31_" + code)


def is_pin(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def pinned(path, expected, private=False):
    need(is_pin(expected), "PIN")
    need(path.resolve() == path, "FILE")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as f:
        s = os.fstat(f.fileno())
        need(stat.S_ISREG(s.st_mode) and s.st_size <= CAP, "FILE")
        if private:
            need(s.st_uid == os.geteuid() and s.st_mode & 0o077 == 0, "PRIVATE")
        blob = f.read(CAP + 1)
    need(len(blob) <= CAP and sha256(blob).hexdigest() == expected, "PIN")
    return blob


def unique(pairs):
    obj = dict(pairs)
    need(len(obj) == len(pairs), "JSON")
    return obj


def reject_number(_):
    raise Refused("P31_JSON_NUMBER")


def parse(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=reject_number)


def encode(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def private_dir(path):
    s = path.lstat()
    need(path.resolve() == path and stat.S_ISDIR(s.st_mode) and s.st_uid == os.geteuid()
         and s.st_mode & 0o077 == 0, "PRIVATE")


def resources():
    with open("/proc/meminfo") as stream:
        available = next(int(s.split()[1]) for s in stream if s.startswith("MemAvailable:"))
    need(available >= 1_572_864, "LOW_MEMORY")
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = min(x for x in (292_968 * 1024, soft, hard) if x != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
    priority = os.nice(0)
    if priority < 10:
        os.nice(10 - priority)


def git(*args, allow=False):
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0"}
    proc = subprocess.run(["/usr/bin/git", "--no-replace-objects", "-c", "core.fsmonitor=false",
                           "-C", str(REPO), *args], capture_output=True, env=env, timeout=15)
    need(allow or proc.returncode == 0, "APPROVAL")
    return proc


def authorize(approval, freeze_pin, inputs_pin, actions_pin):
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval) is not None, "APPROVAL")
    need(all(map(is_pin, (freeze_pin, inputs_pin, actions_pin))), "PIN")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode(), "APPROVAL")
    need(not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")
    def contents(commit, name):
        return git("show", f"{commit}:research_rig/{name}").stdout
    body = re.fullmatch(APPROVAL_RE, contents(approval, APPROVAL))
    need(body is not None, "APPROVAL")
    freeze, f_pin, i_pin, a_pin = (x.decode("ascii") for x in body.groups())
    need((f_pin, i_pin, a_pin) == (freeze_pin, inputs_pin, actions_pin), "APPROVAL")
    need(freeze != approval and git("merge-base", "--is-ancestor", freeze, approval, allow=True).returncode == 0,
         "APPROVAL")
    need(git("cat-file", "-e", f"{freeze}:research_rig/{APPROVAL}", allow=True).returncode != 0, "APPROVAL")
    manifest = pinned(HERE / PINS, freeze_pin)
    need(manifest == contents(freeze, PINS) == contents(approval, PINS), "FREEZE")
    pins = parse(manifest)
    need(type(pins) is dict and set(pins) == PIN_NAMES and all(map(is_pin, pins.values())), "FREEZE")
    blobs = {name: pinned(HERE / name, pins[name]) for name in pins}
    need(all(data == contents(freeze, name) == contents(approval, name) for name, data in blobs.items()), "FREEZE")
    statuses = [line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")]
    need(statuses == [b"Status FROZEN."], "FREEZE")
    ledger = contents(freeze, "TRIAL_LEDGER.md")
    need(re.search(rb"(?m)^\| 166 \|[^\n]+research_rig/" + re.escape(PLAN.encode()) + rb"\x60 \|", ledger),
         "LEDGER")
    return freeze, blobs


def load_engine(blobs):
    # Exact already verified bytes, not any module found on PYTHONPATH or disk.
    for name in ("common_25", "common_31"):
        src = name + ".py"
        module = ModuleType(name)
        sys.modules[name] = module
        exec(compile(blobs[src], str(HERE / src), "exec"), module.__dict__)
    return module


def load_inputs(src, output, inputs_pin, actions_pin, C, calendar_bytes):
    private_dir(src)
    private_dir(output)
    unused(output)
    manifest = parse(pinned(src / "manifest.json", inputs_pin, private=True))
    fields = {"schema", "vendor", "feed", "adjustment", "frequency", "start", "end", "collected_utc", "files"}
    need(type(manifest) is dict and set(manifest) == fields and type(manifest["schema"]) is int
         and manifest["schema"] == 1 and type(manifest["vendor"]) is str
         and 0 < len(manifest["vendor"].strip()) <= 200
         and manifest["feed"] == "sip" and manifest["adjustment"] == "raw" and manifest["frequency"] == "1Day"
         and manifest["start"] == str(C.START) and manifest["end"] == str(C.END), "MANIFEST")
    when = manifest["collected_utc"]
    need(type(when) is str and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", when),
         "MANIFEST")
    datetime.fromisoformat(when.replace("Z", "+00:00"))
    action_file = "cash_actions.json"
    names = {s + ".json" for s in C.SYMBOLS} | {action_file}
    files = manifest["files"]
    need(type(files) is dict and set(files) == names and all(map(is_pin, files.values())), "MANIFEST")
    need(files[action_file] == actions_pin, "ACTION_PIN")
    need({p.name for p in src.iterdir()} == names | {"manifest.json"}, "MANIFEST")
    stored = {name: pinned(src / name, files[name], private=True) for name in sorted(names)}
    days = C.calendar(parse(calendar_bytes))
    schedule = C.design(days)
    payouts = C.action_packet(parse(stored[action_file]), days)
    bars = {s: C.bar_tape(parse(stored[s + ".json"]), days) for s in C.SYMBOLS}
    return days, bars, payouts, schedule


def unused(output):
    need(not any(os.path.lexists(output / name) for name in ("score_31.lock", "results_31.json")), "CONSUMED")


def write_exclusive(path, data):
    with path.open("xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def once(output, metadata, inputs, evaluate):
    unused(output)
    job = metadata | {"claimed_utc": datetime.now(timezone.utc).isoformat()}
    try:
        write_exclusive(output / "score_31.lock", encode(job))
    except FileExistsError:
        raise Refused("P31_CONSUMED") from None
    sync_dir(output)
    result = evaluate(*inputs)
    write_exclusive(output / "results_31.json", encode({"job": job} | result))
    sync_dir(output)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "P31_ARGUMENTS\n")


def main():
    p = Parser(description=__doc__, allow_abbrev=False)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--go", action="store_true")
    p.add_argument("--approval-commit", required=True)
    p.add_argument("--freeze-sha256", required=True)
    p.add_argument("--input-sha256", required=True)
    p.add_argument("--actions-sha256", required=True)
    args = p.parse_args()
    os.umask(0o077)
    try:
        need(sys.flags.isolated and sys.dont_write_bytecode
             and not any(k.startswith(("P31_", "GIT_", "PYTHON")) for k in os.environ), "ENVIRONMENT")
        resources()
        freeze, blobs = authorize(args.approval_commit, args.freeze_sha256, args.input_sha256, args.actions_sha256)
        C = load_engine(blobs)
        inputs = load_inputs(INPUTS, RUN, args.input_sha256, args.actions_sha256, C, blobs["calendar_25.json"])
        if args.validate_inputs:
            days, _, _, schedule = inputs
            print("P31_INPUTS_OK", "symbols", len(C.SYMBOLS), "sessions_per_symbol", len(days),
                  "planned_months", len(schedule), "expected_judged_months", sum(s[-1] for s in schedule.values()))
            return
        meta = {"schema": 1, "ledger": 166, "queue": 50, "freeze_commit": freeze,
                "approval_commit": args.approval_commit, "freeze_sha256": args.freeze_sha256,
                "input_sha256": args.input_sha256, "actions_sha256": args.actions_sha256}
        once(RUN, meta, inputs, C.evaluate)
    except Refused as exc:
        p.exit(2, f"{exc}\n")
    except Exception:
        p.exit(2, "P31_REFUSED\n")
    print("P31_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
