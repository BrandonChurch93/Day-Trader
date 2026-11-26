"""Silent validation or one locked Plan 41 score from an approved, pinned packet."""
import argparse
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
INPUTS, RUN = DATA / "plan41_inputs", DATA / "replay_41"
PLAN = "research_rig/PREREG_41_pension_month_end.md"
PINS = "research_rig/PINNED_41.json"
APPROVAL = "research_rig/APPROVAL_41.md"
CALENDAR = "research_rig/calendar_25.json"
ENGINE = "research_rig/common_41.py"
CONFIG = "config/thresholds.yaml"
PIN_NAMES = {PLAN, CALENDAR, ENGINE, CONFIG, "research_rig/score_41.py", "research_rig/test_41.py"}
CAP = 12 * 1024 * 1024
APPROVAL_RE = (rb"Approved by the lead: plan 41, validation and one scored run, freeze commit ([0-9a-f]{40}), "
               rb"freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64}), "
               rb"cash actions SHA-256 ([0-9a-f]{64})\.\n")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P41_" + code)


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
    raise Refused("P41_JSON_NUMBER")


def parse(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=reject_number, parse_float=Decimal)


def encode(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def private_dir(path):
    st = path.lstat()
    need(path.resolve() == path and stat.S_ISDIR(st.st_mode) and st.st_uid == os.geteuid()
         and stat.S_IMODE(st.st_mode) == 0o700, "PRIVATE")


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


def authorize(approval, freeze_pin, input_pin, actions_pin):
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval), "APPROVAL")
    need(all(map(is_pin, (freeze_pin, input_pin, actions_pin))), "PIN")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode()
         and not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")

    def contents(commit, name):
        return git("show", f"{commit}:{name}").stdout

    body = re.fullmatch(APPROVAL_RE, contents(approval, APPROVAL))
    need(body is not None, "APPROVAL")
    freeze, f_pin, i_pin, a_pin = (x.decode("ascii") for x in body.groups())
    parent = git("rev-list", "--parents", "-n", "1", approval).stdout.split()[1:]
    need((f_pin, i_pin, a_pin) == (freeze_pin, input_pin, actions_pin) and len(parent) == 1, "APPROVAL")
    need(git("merge-base", "--is-ancestor", freeze, parent[0].decode(), allow=True).returncode == 0, "APPROVAL")
    need(git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", approval).stdout
         == f"A\t{APPROVAL}\n".encode(), "APPROVAL")
    need(git("cat-file", "-e", f"{freeze}:{APPROVAL}", allow=True).returncode != 0, "APPROVAL")
    manifest = pinned(REPO / PINS, freeze_pin)
    need(manifest == contents(freeze, PINS) == contents(approval, PINS), "FREEZE")
    pins = parse(manifest)
    need(type(pins) is dict and set(pins) == PIN_NAMES and all(map(is_pin, pins.values())), "FREEZE")
    blobs = {name: pinned(REPO / name, pins[name]) for name in pins}
    need(all(b == contents(freeze, name) == contents(approval, name) for name, b in blobs.items()), "FREEZE")
    need([line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")] == [b"Status FROZEN."], "FREEZE")
    link = b"`" + PLAN.encode() + b"`"
    for name, row, code in (("research_rig/TRIAL_LEDGER.md", 176, "LEDGER"), ("docs/QUEUE.md", 54, "QUEUE")):
        prefix = f"| {row} |".encode()
        a, b = ([line for line in contents(commit, name).splitlines() if line.startswith(prefix)]
                for commit in (freeze, approval))
        need(len(a) == 1 and a == b and link in a[0], code)
    return freeze, blobs


def load_engine(blob):
    reset_tzpath(("/usr/share/zoneinfo",))
    C = ModuleType("common_41_verified")
    exec(compile(blob, ENGINE, "exec"), C.__dict__)
    return C


def read_config(blob):
    # The single Plan 41 YAML value is written in JSON flow syntax to avoid loading
    # a third-party parser in the isolated scorer and to avoid duplicated constants.
    block = re.findall(rb"(?m)^replay_41_plan:\n  value: (\{[^\n]+\})\n", blob)
    need(len(block) == 1, "CONFIG")
    cfg = parse(block[0])
    need(type(cfg) is dict and set(cfg) == {"first", "last", "sessions", "months", "years", "capital",
                                          "signal_offset", "entry_offset", "costs", "fixed_spy_weight", "marks"},
         "CONFIG")
    need(type(cfg["costs"]) is dict and set(cfg["costs"]) == {"judged", "shown"}
         and type(cfg["costs"]["shown"]) is list
         and type(cfg["marks"]) is dict and set(cfg["marks"]) == {"minimum_months", "minimum_t", "drop_best",
                                                               "minimum_positive_years", "recent_from",
                                                               "positive_cutoff"}, "CONFIG")
    return cfg


def load_inputs(input_dir, input_pin, actions_pin, C, calendar_blob, cfg):
    private_dir(input_dir)
    days, windows = C.calendar(parse(calendar_blob), cfg)
    m = parse(pinned(input_dir / "manifest.json", input_pin, private=True))
    need(type(m) is dict and set(m) == {"schema", "mode", "feed", "adjustment", "start", "end",
                                       "collected_utc", "files"}
         and type(m["schema"]) is int and m["schema"] == 1 and m["mode"] == "raw_dated_distributions"
         and m["feed"] == "sip" and m["adjustment"] == "raw" and m["start"] == cfg["first"]
         and m["end"] == cfg["last"], "MANIFEST")
    ts = m["collected_utc"]
    need(type(ts) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts)
         and datetime.fromisoformat(ts).date() > days[-1], "MANIFEST_CLOCK")
    names = {s + ".json" for s in C.SYMBOLS} | {"cash_actions.json"}
    need(type(m["files"]) is dict and set(m["files"]) == names and all(map(is_pin, m["files"].values()))
         and {p.name for p in input_dir.iterdir()} == names | {"manifest.json"}
         and is_pin(actions_pin) and m["files"]["cash_actions.json"] == actions_pin, "MANIFEST_FILES")
    blobs = {name: pinned(input_dir / name, m["files"][name], private=True) for name in sorted(names)}
    actions = C.cash_actions(parse(blobs["cash_actions.json"]), days)
    tapes = {s: C.bar_tape(parse(blobs[s + ".json"]), days) for s in C.SYMBOLS}
    return days, windows, tapes, actions, cfg


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
    job = metadata | {"claimed_utc": datetime.now(timezone.utc).isoformat()}
    try:
        write_new(run / "score_41.lock", encode(job))
    except FileExistsError:
        raise Refused("P41_CONSUMED_OR_NOT_EMPTY") from None
    sync_dir(run)
    result = encode({"job": job} | evaluate(*inputs))
    tmp = run / ".results_41.tmp"
    write_new(tmp, result)
    os.link(tmp, run / "results_41.json", follow_symlinks=False)
    sync_dir(run)
    tmp.unlink()
    sync_dir(run)


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "P41_ARGUMENTS\n")


def check_environment():
    need(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize == 0
         and not any(k.startswith(("P41_", "PLAN41_", "GIT_", "PYTHON", "LD_")) or k in {"TZ", "TZDIR"}
                     for k in os.environ),
         "ENVIRONMENT")


def main():
    p = Parser(description=__doc__, allow_abbrev=False)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--go", action="store_true")
    p.add_argument("--approval-commit", required=True)
    p.add_argument("--freeze-sha256", required=True)
    p.add_argument("--input-sha256", required=True)
    p.add_argument("--actions-sha256", required=True)
    a = p.parse_args()
    os.umask(0o077)
    try:
        check_environment()
        resources()
        freeze, blobs = authorize(a.approval_commit, a.freeze_sha256, a.input_sha256, a.actions_sha256)
        C = load_engine(blobs[ENGINE])
        cfg = read_config(blobs[CONFIG])
        try:
            inputs = load_inputs(INPUTS, a.input_sha256, a.actions_sha256, C, blobs[CALENDAR], cfg)
        except C.Refused as exc:
            raise Refused(str(exc)) from None
        if a.validate_inputs:
            days, windows = inputs[:2]
            print("P41_INPUTS_OK", "symbols", len(C.SYMBOLS), "sessions_per_symbol", len(days),
                  "planned_months", len(windows), "planned_reversals", sum(w[-1] is not None for w in windows))
            return
        meta = {"schema": 1, "ledger": 176, "queue": 54, "freeze_commit": freeze,
                "approval_commit": a.approval_commit, "freeze_sha256": a.freeze_sha256,
                "input_sha256": a.input_sha256, "actions_sha256": a.actions_sha256}
        need((freeze, blobs) == authorize(a.approval_commit, a.freeze_sha256, a.input_sha256,
                                         a.actions_sha256), "APPROVAL")
        once(RUN, meta, inputs, C.evaluate)
    except Refused as exc:
        p.exit(2, f"{exc}\n")
    except Exception:
        p.exit(2, "P41_REFUSED\n")
    print("P41_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
