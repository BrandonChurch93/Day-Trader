"""Silent validation or one locked Plan 46 score from an approved, pinned packet."""
import argparse
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from hashlib import sha1, sha256
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
INPUTS, RUN = DATA / "plan46_inputs", DATA / "replay_46"
PLAN = "research_rig/PREREG_46_cftc_altcoin_futures.md"
PINS = "research_rig/PINNED_46.json"
APPROVAL = "research_rig/APPROVAL_46.md"
DOCKET = "research_rig/docket_46.json"
ENGINE = "research_rig/common_46.py"
CONFIG = "config/thresholds.yaml"
PIN_NAMES = {PLAN, DOCKET, ENGINE, CONFIG, "research_rig/score_46.py", "research_rig/test_46.py",
             "research_rig/calibrate_46.py", "research_rig/AUDIT_46_cftc_docket.md"}
CAP = 12 * 1024 * 1024
APPROVAL_RE = (rb"Approved by the lead agent for plan 46 legs A and B, validation and one scored run, "
               rb"freeze commit ([0-9a-f]{40}), freeze SHA-256 ([0-9a-f]{64}), "
               rb"input SHA-256 ([0-9a-f]{64})\.\n")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P46_" + code)


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
    raise Refused("P46_JSON_NUMBER")


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


def authorize(approval, freeze_pin, input_pin):
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval), "APPROVAL")
    need(all(map(is_pin, (freeze_pin, input_pin))), "PIN")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode()
         and not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")

    def contents(commit, name):
        return git("show", f"{commit}:{name}").stdout

    body = re.fullmatch(APPROVAL_RE, contents(approval, APPROVAL))
    need(body is not None, "APPROVAL")
    freeze, f_pin, i_pin = (x.decode("ascii") for x in body.groups())
    parent = git("rev-list", "--parents", "-n", "1", approval).stdout.split()[1:]
    need((f_pin, i_pin) == (freeze_pin, input_pin) and len(parent) == 1, "APPROVAL")
    need(git("merge-base", "--is-ancestor", freeze, parent[0].decode(), allow=True).returncode == 0, "APPROVAL")
    need(git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", approval).stdout
         == f"A\t{APPROVAL}\n".encode(), "APPROVAL")
    need(git("cat-file", "-e", f"{freeze}:{APPROVAL}", allow=True).returncode != 0, "APPROVAL")
    manifest = pinned(REPO / PINS, freeze_pin)
    pins = parse(manifest)
    need(type(pins) is dict and set(pins) == PIN_NAMES and all(map(is_pin, pins.values())), "FREEZE")
    blobs = {name: pinned(REPO / name, pins[name]) for name in pins}
    tree_blobs = blobs | {PINS: manifest}
    for commit in (freeze, approval):
        records = git("ls-tree", "-z", "--full-tree", commit, "--", *sorted(tree_blobs)).stdout.split(b"\0")
        need(records[-1] == b"" and len(records) == len(tree_blobs) + 1, "FREEZE")
        for record in records[:-1]:
            meta, raw_name = record.split(b"\t", 1)
            mode, kind, oid = meta.split()
            blob = tree_blobs[raw_name.decode("ascii")]
            git_oid = sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest().encode()
            need(mode in {b"100644", b"100755"} and kind == b"blob" and oid == git_oid, "FREEZE")
    need([line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")] == [b"Status FROZEN."], "FREEZE")
    link = b"`" + PLAN.encode() + b"`"
    for name, row, code in (("research_rig/TRIAL_LEDGER.md", 179, "LEDGER"),
                            ("research_rig/TRIAL_LEDGER.md", 181, "LEDGER"), ("docs/QUEUE.md", 83, "QUEUE")):
        prefix = f"| {row} |".encode()
        a, b = ([line for line in contents(commit, name).splitlines() if line.startswith(prefix)]
                for commit in (freeze, approval))
        need(len(a) == 1 and a == b and link in a[0], code)
    return freeze, blobs


def load_engine(blob):
    reset_tzpath(("/usr/share/zoneinfo",))
    C = ModuleType("common_46_verified")
    exec(compile(blob, ENGINE, "exec"), C.__dict__)
    return C


def read_config(blob):
    block = re.findall(rb"(?m)^replay_46_plan:\n  value: (\{[^\n]+\})\n", blob)
    need(len(block) == 1, "CONFIG")
    return parse(block[0])


def utc(token):
    need(type(token) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", token),
         "SOURCE_CLOCK")
    return datetime.fromisoformat(token)


def justify_native(raw, normal, expected, collected, product, C):
    need(type(raw) is dict and set(raw) == {"product", "requests", "not_listed"}
         and raw["product"] == product and type(raw["requests"]) is list
         and type(raw["not_listed"]) is dict, "SOURCE")
    hits, witnessed, attempts = {}, {}, set()
    for req in raw["requests"]:
        need(type(req) is dict and set(req) == {"start", "end", "retrieved_utc", "status", "body"}
             and type(req["status"]) is int and req["status"] == 200
             and type(req["body"]) is list and len(req["body"]) <= 300, "SOURCE_REQUEST")
        start, end = C.day(req["start"]), C.day(req["end"])
        at = utc(req["retrieved_utc"])
        need(1 <= (end - start).days <= 300 and datetime.combine(end, time(), timezone.utc) <= at <= collected,
             "SOURCE_CLOCK")
        need((start, end, at) not in attempts and any(start <= d < end for d in expected), "SOURCE_REQUEST")
        attempts.add((start, end, at))
        occurrences = {}
        for row in req["body"]:
            need(type(row) is list and len(row) == 6 and type(row[0]) is int
                 and 0 < row[0] < 4102444800 and row[0] % 86400 == 0, "SOURCE_CANDLE")
            d = datetime.fromtimestamp(row[0], timezone.utc).date()
            need(d not in occurrences, "SOURCE_CANDLE")
            payload = row[1:]
            C.candle_tape({d.isoformat(): payload}, {d})
            occurrences[d] = payload
            if start <= d < end and d in expected:
                need(d not in hits or hits[d] == payload, "SOURCE_CONFLICT")
                hits[d] = payload
        for d in expected:
            if start <= d < end:
                prev = witnessed.get(d, (0, 0))
                witnessed[d] = prev[0] + 1, prev[1] + int(d in occurrences)
    absent = {}
    for d in expected:
        token, value = d.isoformat(), normal[d.isoformat()]
        if value is not None:
            need(hits.get(d) == value and token not in raw["not_listed"]
                 and witnessed[d][0] == witnessed[d][1], "SOURCE_MISMATCH")
            continue
        need(d not in hits, "SOURCE_MISMATCH")
        if token in raw["not_listed"]:
            evidence = raw["not_listed"][token]
            need(type(evidence) is dict and set(evidence) == {"url", "excerpt"}
                 and type(evidence["url"]) is str
                 and re.fullmatch(r"https://(?:help\.|www\.)?coinbase\.com/[A-Za-z0-9_./%-]+", evidence["url"])
                 and type(evidence["excerpt"]) is str and 16 <= len(evidence["excerpt"]) <= 1000,
                 "SOURCE_NOT_LISTED")
            absent[token] = "official_not_listed"
        else:
            need(witnessed.get(d, (0, 0))[0] >= 2, "SOURCE_UNRESOLVED")
            absent[token] = "absent_from_confirmed_responses"
    need(set(raw["not_listed"]) <= set(absent), "SOURCE_NOT_LISTED")
    return absent


def load_inputs(input_dir, input_pin, C, docket_blob, cfg):
    private_dir(input_dir)
    cfg = C.config(cfg)
    rows = C.docket(parse(docket_blob), cfg)
    holds, skips = C.planned(rows, cfg)
    wanted = C.required(holds)
    m = parse(pinned(input_dir / "manifest.json", input_pin, private=True))
    need(type(m) is dict and set(m) == {"schema", "source", "collected_utc", "docket_sha256", "files",
                                        "native_files", "reconciliation_sha256"}
         and type(m["schema"]) is int and m["schema"] == 2
         and m["source"] == cfg["source"] and m["docket_sha256"] == sha256(docket_blob).hexdigest(),
         "MANIFEST")
    latest = max((day for bucket in wanted.values() for day in bucket), default=C.day(cfg["asof"]))
    ts = utc(m["collected_utc"])
    now = datetime.now(timezone.utc)
    need(datetime.combine(latest + timedelta(days=1), time(), timezone.utc) <= ts <= now, "MANIFEST_CLOCK")
    names = {s + "-USD.json" for s in wanted}
    n_names = {s + "-USD.native.json" for s in wanted}
    review_name = "source_reconciliation.json"
    need(type(m["files"]) is dict and set(m["files"]) == names and all(map(is_pin, m["files"].values()))
         and type(m["native_files"]) is dict and set(m["native_files"]) == n_names
         and all(map(is_pin, m["native_files"].values()))
         and {p.name for p in input_dir.iterdir()} == names | n_names | {"manifest.json", review_name},
         "MANIFEST_FILES")
    receipt = parse(pinned(input_dir / review_name, m["reconciliation_sha256"], private=True))
    need(type(receipt) is dict and set(receipt) == {"schema", "source", "docket_sha256", "review", "reviewed_utc", "files"}
         and type(receipt["schema"]) is int and receipt["schema"] == 1 and receipt["source"] == m["source"]
         and receipt["docket_sha256"] == m["docket_sha256"]
         and receipt["review"] == "independent_exact_native_grid_and_gap_check"
         and ts <= utc(receipt["reviewed_utc"]) <= now
         and type(receipt["files"]) is dict and set(receipt["files"]) == names, "SOURCE_RECONCILIATION")
    raw = {n: pinned(input_dir / n, m["files"][n], private=True) for n in sorted(names)}
    native = {n: pinned(input_dir / n, m["native_files"][n], private=True) for n in sorted(n_names)}
    tapes = {}
    for s, days in wanted.items():
        n, native_name = s + "-USD.json", s + "-USD.native.json"
        tape = parse(raw[n])
        tapes[s] = C.candle_tape(tape, days)
        gaps = justify_native(parse(native[native_name]), tape, days, ts, s + "-USD", C)
        need(receipt["files"][n] == {"normalized_sha256": m["files"][n], "native_sha256": m["native_files"][native_name],
                                     "missing": gaps}, "SOURCE_RECONCILIATION")
    # This checks calendar and candle presence only. No price ratios or return functions here.
    counts = {leg: C.execution(leg, holds[leg], tapes) for leg in C.LEGS}
    return (holds, skips, tapes, cfg), counts


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
        write_new(run / "score_46.lock", encode(job))
    except FileExistsError:
        raise Refused("P46_CONSUMED_OR_NOT_EMPTY") from None
    sync_dir(run)
    result = encode({"job": job} | evaluate(*inputs))
    tmp = run / ".results_46.tmp"
    write_new(tmp, result)
    os.link(tmp, run / "results_46.json", follow_symlinks=False)
    sync_dir(run)
    tmp.unlink()
    sync_dir(run)


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "P46_ARGUMENTS\n")


def check_environment():
    need(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize == 0
         and not any(k.startswith(("P46_", "PLAN46_", "GIT_", "PYTHON", "LD_")) or k in {"TZ", "TZDIR"}
                     for k in os.environ),
         "ENVIRONMENT")


def dispatch(a):
    freeze, blobs = authorize(a.approval_commit, a.freeze_sha256, a.input_sha256)
    C = load_engine(blobs[ENGINE])
    cfg = read_config(blobs[CONFIG])
    try:
        inputs, counts = load_inputs(INPUTS, a.input_sha256, C, blobs[DOCKET], cfg)
    except C.Refused as exc:
        raise Refused(str(exc)) from None
    if a.validate_inputs:
        print("P46_INPUTS_OK", "symbols", len(inputs[2]),
              *[f"{leg} planned {len(inputs[0][leg])} placed {len(counts[leg][0])} "
                f"posting_dates {len({r[1] for r in counts[leg][0]})}" for leg in C.LEGS])
        return
    meta = {"schema": 1, "ledger": cfg["ledger"], "queue": cfg["queue"], "freeze_commit": freeze,
            "approval_commit": a.approval_commit, "freeze_sha256": a.freeze_sha256,
            "input_sha256": a.input_sha256, "docket_sha256": sha256(blobs[DOCKET]).hexdigest()}
    need((freeze, blobs) == authorize(a.approval_commit, a.freeze_sha256, a.input_sha256), "APPROVAL")
    once(RUN, meta, inputs, C.evaluate)
    print("P46_RESULT_WRITTEN")


def main():
    p = Parser(description=__doc__, allow_abbrev=False)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--go", action="store_true")
    p.add_argument("--approval-commit", required=True)
    p.add_argument("--freeze-sha256", required=True)
    p.add_argument("--input-sha256", required=True)
    a = p.parse_args()
    os.umask(0o077)
    try:
        check_environment()
        resources()
        dispatch(a)
    except Refused as exc:
        p.exit(2, f"{exc}\n")
    except Exception:
        p.exit(2, "P46_REFUSED\n")


if __name__ == "__main__":
    main()
