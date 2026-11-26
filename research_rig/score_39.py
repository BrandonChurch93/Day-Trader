"""Validate a pinned private Plan 39 packet, or score it once after a durable claim."""
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
INPUTS, RUN = DATA / "plan39_inputs", DATA / "replay_39"
PLAN, PINS, APPROVAL = "PREREG_39_iwm_preholiday.md", "PINNED_39.json", "APPROVAL_39.md"
PIN_NAMES = {PLAN, "calendar_39.json", "common_39.py", "score_39.py", "test_39.py"}
CAP = 12 * 1024 * 1024
APPROVAL_RE = (rb"Approved by the lead: plan 39, validation and one scored run, freeze commit ([0-9a-f]{40}), "
               rb"freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64}), "
               rb"cash actions SHA-256 ([0-9a-f]{64})\.\n")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P39_" + code)


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
    raise Refused("P39_JSON_NUMBER")


def parse(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=reject_number)


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
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval) is not None, "APPROVAL")
    need(all(map(is_pin, (freeze_pin, input_pin, actions_pin))), "PIN")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode()
         and not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")

    def contents(commit, name):
        return git("show", f"{commit}:research_rig/{name}").stdout

    body = re.fullmatch(APPROVAL_RE, contents(approval, APPROVAL))
    need(body is not None, "APPROVAL")
    freeze, f_pin, i_pin, a_pin = (x.decode("ascii") for x in body.groups())
    parent = git("rev-list", "--parents", "-n", "1", approval).stdout.split()[1:]
    need((f_pin, i_pin, a_pin) == (freeze_pin, input_pin, actions_pin) and len(parent) == 1, "APPROVAL")
    need(git("merge-base", "--is-ancestor", freeze, parent[0].decode(), allow=True).returncode == 0,
         "APPROVAL")
    need(git("diff-tree", "--no-commit-id", "--name-status", "-r", approval).stdout
         == f"A\tresearch_rig/{APPROVAL}\n".encode(), "APPROVAL")
    need(git("cat-file", "-e", f"{freeze}:research_rig/{APPROVAL}", allow=True).returncode != 0, "APPROVAL")
    manifest = pinned(HERE / PINS, freeze_pin)
    need(manifest == contents(freeze, PINS) == contents(approval, PINS), "FREEZE")
    pins = parse(manifest)
    need(type(pins) is dict and set(pins) == PIN_NAMES and all(map(is_pin, pins.values())), "FREEZE")
    blobs = {name: pinned(HERE / name, pins[name]) for name in pins}
    need(all(b == contents(freeze, name) == contents(approval, name) for name, b in blobs.items()), "FREEZE")
    need([line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")] == [b"Status FROZEN."],
         "FREEZE")
    for commit in (freeze, approval):
        need(re.search(rb"(?m)^\| 174 \|[^\n]+research_rig/" + re.escape(PLAN.encode()) + rb"\x60 \|",
                       contents(commit, "TRIAL_LEDGER.md")), "LEDGER")
        queue = git("show", f"{commit}:docs/QUEUE.md").stdout
        need(re.search(rb"(?m)^\| 65 \|[^\n]+research_rig/" + re.escape(PLAN.encode()) + rb"\x60", queue),
             "QUEUE")
    return freeze, blobs


def load_engine(blobs):
    C = ModuleType("common_39_verified")
    exec(compile(blobs["common_39.py"], "common_39.py", "exec"), C.__dict__)
    return C


def load_inputs(input_dir, input_pin, actions_pin, C, calendar_blob):
    private_dir(input_dir)
    days, events = C.calendar(parse(calendar_blob))
    m = parse(pinned(input_dir / "manifest.json", input_pin, private=True))
    need(type(m) is dict and set(m) == {"schema", "mode", "feed", "adjustment", "start", "end",
                                       "collected_utc", "files"}
         and type(m["schema"]) is int and m["schema"] == 1 and m["mode"] == "raw_dated_distributions"
         and m["feed"] == "sip" and m["adjustment"] == "raw" and m["start"] == str(C.FIRST)
         and m["end"] == str(C.LAST), "MANIFEST")
    ts = m["collected_utc"]
    need(type(ts) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", ts)
         and datetime.fromisoformat(ts[:-1] + "+00:00").date() > C.LAST, "MANIFEST_CLOCK")
    names = {s + ".json" for s in C.SYMBOLS} | {"cash_actions.json"}
    need(type(m["files"]) is dict and set(m["files"]) == names and all(map(is_pin, m["files"].values()))
         and {p.name for p in input_dir.iterdir()} == names | {"manifest.json"}
         and m["files"]["cash_actions.json"] == actions_pin, "MANIFEST_FILES")
    blobs = {name: pinned(input_dir / name, m["files"][name], private=True) for name in sorted(names)}
    cash = C.payouts(parse(blobs["cash_actions.json"]), days)
    tapes = {s: C.bar_tape(parse(blobs[s + ".json"]), days) for s in C.SYMBOLS}
    return days, events, tapes, cash


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
        write_new(run / "score_39.lock", encode(job))
    except FileExistsError:
        raise Refused("P39_CONSUMED_OR_NOT_EMPTY") from None
    sync_dir(run)
    result = encode({"job": job} | evaluate(*inputs))
    # Publish complete bytes only. A post-claim error consumes the run, with no retry.
    temporary = run / ".results_39.tmp"
    write_new(temporary, result)
    os.link(temporary, run / "results_39.json", follow_symlinks=False)
    sync_dir(run)
    temporary.unlink()
    sync_dir(run)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "P39_ARGUMENTS\n")


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
        need(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize == 0
             and not any(k.startswith(("P39_", "PLAN39_", "GIT_", "PYTHON", "LD_")) for k in os.environ),
             "ENVIRONMENT")
        resources()
        freeze, blobs = authorize(a.approval_commit, a.freeze_sha256, a.input_sha256, a.actions_sha256)
        if a.go:
            unused(RUN)
        C = load_engine(blobs)
        inputs = load_inputs(INPUTS, a.input_sha256, a.actions_sha256, C, blobs["calendar_39.json"])
        if a.validate_inputs:
            days, events, _, _ = inputs
            print("P39_INPUTS_OK", "symbols", len(C.SYMBOLS), "sessions_per_symbol", len(days),
                  "planned_events", len(events), "planned_post_2019_events", sum(s >= C.POST for s in events),
                  "planned_early_close_exits", sum(v[3] for v in events.values()))
            return
        meta = {"schema": 1, "ledger": 174, "queue": 65, "freeze_commit": freeze,
                "approval_commit": a.approval_commit, "freeze_sha256": a.freeze_sha256,
                "input_sha256": a.input_sha256, "actions_sha256": a.actions_sha256}
        once(RUN, meta, inputs, C.evaluate)
    except Refused as exc:
        p.exit(2, f"{exc}\n")
    except Exception:
        p.exit(2, "P39_REFUSED\n")
    print("P39_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
