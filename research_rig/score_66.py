"""Plan 66 (DRAFT): synthetic power, a no-return input check, or one approved scored run."""
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
INPUTS, RUN = DATA / "plan66_inputs", DATA / "replay_66"
PLAN, PINS, APPROVAL = "PREREG_66_third_friday_settlement.md", "PINNED_66.json", "APPROVAL_66.md"
PIN_NAMES = {PLAN, "calendar_66.json", "common_66.py", "score_66.py", "test_66.py"}
LEDGER_ROW, QUEUE_ROW = b"210", b"108"
CAP = 12 * 1024 * 1024
APPROVAL_RE = (rb"Approved by the lead: plan 66, validation and one scored run, freeze commit ([0-9a-f]{40}), "
               rb"freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64})\.\n")
# Edges are gross bp per expiration (leg 1 overnight plus leg 2 intraday on SH). Noise SD from published figures.
SCENARIOS = (
    ("stated_edge_25bp", 25.0, 104.6, 8.0, None, None),
    ("half_stated_12_5bp", 12.5, 104.6, 8.0, None, None),
    ("etf_open_martone_21_9bp", 21.9, 104.6, 8.0, None, None),
    ("post_2023_es_3_3bp", 3.3, 104.6, 8.0, None, None),
    ("stated_then_3_3bp_from_oct_2023", 25.0, 104.6, 8.0, 3.3, None),
    ("stated_sd_103_9", 25.0, 103.9, 8.0, None, None),
    ("stated_sd_125_5", 25.0, 125.5, 8.0, None, None),
    ("stated_cost_12bp", 25.0, 104.6, 12.0, None, None),
    ("stated_t5_tails", 25.0, 104.6, 8.0, None, 5),
    ("zero_edge", 0.0, 104.6, 8.0, None, None),
)


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P66_" + code)


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
    raise Refused("P66_JSON_NUMBER")


def parse(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=reject_number)


def encode(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False, default=str) + "\n").encode()


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
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval) is not None, "APPROVAL")
    need(is_pin(freeze_pin) and is_pin(input_pin), "PIN")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode()
         and not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")

    def contents(commit, name):
        return git("show", f"{commit}:research_rig/{name}").stdout

    body = re.fullmatch(APPROVAL_RE, contents(approval, APPROVAL))
    need(body is not None, "APPROVAL")
    freeze, f_pin, i_pin = (x.decode("ascii") for x in body.groups())
    parent = git("rev-list", "--parents", "-n", "1", approval).stdout.split()[1:]
    need((f_pin, i_pin) == (freeze_pin, input_pin) and len(parent) == 1, "APPROVAL")
    need(git("merge-base", "--is-ancestor", freeze, parent[0].decode(), allow=True).returncode == 0, "APPROVAL")
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
        need(re.search(rb"(?m)^\| " + LEDGER_ROW + rb" \|[^\n]+research_rig/" + re.escape(PLAN.encode()) + rb"\x60",
                       contents(commit, "TRIAL_LEDGER.md")), "LEDGER")
        need(re.search(rb"(?m)^\| " + QUEUE_ROW + rb" \|[^\n]+research_rig/" + re.escape(PLAN.encode()) + rb"\x60",
                       git("show", f"{commit}:docs/QUEUE.md").stdout), "QUEUE")
    return freeze, blobs


def load_engine(blob):
    C = ModuleType("common_66_verified")
    exec(compile(blob, "common_66.py", "exec"), C.__dict__)
    return C


def load_inputs(input_dir, input_pin, C, calendar_blob):
    """Private packet: manifest.json pins marks.json and actions.json. Opens no network and no bars."""
    private_dir(input_dir)
    events = C.calendar(parse(calendar_blob))
    m = parse(pinned(input_dir / "manifest.json", input_pin, private=True))
    need(type(m) is dict and set(m) == {"schema", "mode", "feed", "adjustment", "open_rule", "collected_utc", "files"}
         and m["schema"] == 1 and m["mode"] == "plan66_marks" and m["feed"] == "sip" and m["adjustment"] == "raw"
         and m["open_rule"] == C.OPEN_RULE, "MANIFEST")
    ts = m["collected_utc"]
    need(type(ts) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", ts)
         and datetime.fromisoformat(ts[:-1] + "+00:00").date() > C.LAST, "MANIFEST_CLOCK")
    names = {"marks.json", "actions.json"}
    need(type(m["files"]) is dict and set(m["files"]) == names and all(map(is_pin, m["files"].values()))
         and {p.name for p in input_dir.iterdir()} == names | {"manifest.json"}, "MANIFEST_FILES")
    blobs = {n: parse(pinned(input_dir / n, m["files"][n], private=True)) for n in sorted(names)}
    return events, C.marks_packet(blobs["marks.json"], events), C.actions_packet(blobs["actions.json"])


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
        write_new(run / "score_66.lock", encode(job))
    except FileExistsError:
        raise Refused("P66_CONSUMED_OR_NOT_EMPTY") from None
    sync_dir(run)
    result = encode({"job": job} | evaluate(*inputs))
    # Publish complete bytes only. A post-claim error consumes the run, with no retry.
    temporary = run / ".results_66.tmp"
    write_new(temporary, result)
    os.link(temporary, run / "results_66.json", follow_symlinks=False)
    sync_dir(run)
    temporary.unlink()
    sync_dir(run)


def synthetic(C, sims, seed):
    events = C.calendar(parse((HERE / "calendar_66.json").read_bytes()))
    out = {"sims": sims, "seed": seed, "expirations": len(events), "post_oct_2023": C.N_POST, "scenarios": {}}
    for name, edge, sd, cost, post_edge, tails in SCENARIOS:
        r = C.synthetic_power(edge, sd, cost, sims=sims, seed=seed, post_edge_gross_bp=post_edge,
                              dates=events, tails=tails)
        out["scenarios"][name] = {"edge_gross_bp": edge, "sd_bp": sd, "cost_bp": cost,
                                  "post_oct_2023_edge_gross_bp": post_edge, "t_df": tails} | r
    out["gate_33pct_at_stated_edge"] = out["scenarios"]["stated_edge_25bp"]["power"] >= 0.33
    return out


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "P66_ARGUMENTS\n")


def main():
    p = Parser(description=__doc__, allow_abbrev=False)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic", action="store_true")
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--go", action="store_true")
    p.add_argument("--sims", type=int, default=20_000)
    p.add_argument("--seed", type=int, default=66)
    p.add_argument("--approval-commit")
    p.add_argument("--freeze-sha256")
    p.add_argument("--input-sha256")
    a = p.parse_args()
    os.umask(0o077)
    try:
        resources()
        if a.synthetic:
            sys.path.insert(0, str(HERE))
            import common_66 as C
            need(1_000 <= a.sims <= 200_000, "ARGUMENTS")
            sys.stdout.write(encode(synthetic(C, a.sims, a.seed)).decode())
            return
        need(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize == 0
             and not any(k.startswith(("P66_", "PLAN66_", "GIT_", "PYTHON", "LD_")) for k in os.environ),
             "ENVIRONMENT")
        if a.validate_inputs:
            # No approval needed; no return, share count or price is printed. Engine read from the working tree.
            need(a.input_sha256 is not None and a.approval_commit is None and a.freeze_sha256 is None, "ARGUMENTS")
            C = load_engine((HERE / "common_66.py").read_bytes())
            events, marks, actions = load_inputs(INPUTS, a.input_sha256, C, (HERE / "calendar_66.json").read_bytes())
            placed = C.place(events, marks, actions)
            for e, v in placed.items():
                print(e.isoformat(), v[0] if v[0] == "PLACED" else "REFUSED_" + v[1])
            n = sum(v[0] == "PLACED" for v in placed.values())
            print("P66_INPUTS_OK", "expirations", len(events), "placed", n,
                  "placed_from_oct_2023", sum(v[0] == "PLACED" and e >= C.POST for e, v in placed.items()),
                  "placed_at_least_120", n >= C.MIN_PLACED)
            return
        need(None not in (a.approval_commit, a.freeze_sha256, a.input_sha256), "ARGUMENTS")
        freeze, blobs = authorize(a.approval_commit, a.freeze_sha256, a.input_sha256)
        unused(RUN)
        C = load_engine(blobs["common_66.py"])
        inputs = load_inputs(INPUTS, a.input_sha256, C, blobs["calendar_66.json"])
        meta = {"schema": 1, "ledger": 210, "queue": 108, "freeze_commit": freeze,
                "approval_commit": a.approval_commit, "freeze_sha256": a.freeze_sha256,
                "input_sha256": a.input_sha256}
        once(RUN, meta, inputs, C.evaluate)
    except Exception as exc:  # both this file's and the engine's Refused carry a P66_ code
        p.exit(2, f"{exc}\n" if type(exc).__name__ == "Refused" else "P66_REFUSED\n")
    print("P66_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
