"""Plan 48: synthetic calibration, silent validation, or one locked score from an approved, pinned packet."""
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
INPUTS, RUN = DATA / "plan48_inputs", DATA / "replay_48"
PLAN = "research_rig/PREREG_48_muni_cef_tax_loss.md"
PINS = "research_rig/PINNED_48.json"
APPROVAL = "research_rig/APPROVAL_48.md"
CALENDAR = "research_rig/calendar_25.json"
ENGINE = "research_rig/common_48.py"
CALIBRATION = "research_rig/CALIBRATION_48.json"
CONFIG = "config/thresholds.yaml"
PIN_NAMES = {PLAN, CALENDAR, ENGINE, CALIBRATION, CONFIG, "research_rig/score_48.py", "research_rig/test_48.py"}
ROSTER_PIN = "packet:roster.csv"  # off-repo point-in-time roster, pinned at freeze
LEDGER_ROW, QUEUE_ROW = 182, 86
CAP = 64 * 1024 * 1024
CONFIG_KEYS = {"first_turn", "last_turn", "turns", "capital", "sleeve_usd", "picks", "formation_from_end",
               "entry_from_end", "shown_exit_session", "benchmark", "split_check_ratio", "cost", "marks", "calibration", "resources"}
APPROVAL_RE = (rb"Approved by the lead: plan 48, validation and one scored run, freeze commit ([0-9a-f]{40}), "
               rb"freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64}), "
               rb"roster SHA-256 ([0-9a-f]{64}), distributions SHA-256 ([0-9a-f]{64})\.\n")


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P48_" + code)


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
    raise Refused("P48_JSON_NUMBER")


def parse(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=reject_number, parse_float=Decimal)


def encode(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def private_dir(path):
    st = path.lstat()
    need(path.resolve() == path and stat.S_ISDIR(st.st_mode) and st.st_uid == os.geteuid()
         and stat.S_IMODE(st.st_mode) == 0o700, "PRIVATE")


def resources(cfg):
    r = cfg["resources"]
    with open("/proc/meminfo") as stream:
        available = next(int(s.split()[1]) for s in stream if s.startswith("MemAvailable:"))
    need(available >= r["minimum_free_mib"] * 1024, "LOW_MEMORY")
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = min(x for x in (r["process_cap_mib"] * 1024 * 1024, soft, hard) if x != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
    priority = os.nice(0)
    if priority < r["nice"]:
        os.nice(r["nice"] - priority)


def git(*args, allow=False):
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0"}
    proc = subprocess.run(["/usr/bin/git", "--no-replace-objects", "-c", "core.fsmonitor=false",
                           "-c", "safe.directory=*", "-C", str(REPO), *args], capture_output=True, env=env,
                          timeout=15)
    need(allow or proc.returncode == 0, "APPROVAL")
    return proc


def authorize(approval, freeze_pin, input_pin, roster_pin, dist_pin):
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval) is not None, "APPROVAL")
    need(all(map(is_pin, (freeze_pin, input_pin, roster_pin, dist_pin))), "PIN")
    need(git("rev-parse", "HEAD").stdout.strip() == approval.encode()
         and not git("status", "--porcelain", "--untracked-files=all").stdout, "APPROVAL")

    def contents(commit, name):
        return git("show", f"{commit}:{name}").stdout

    body = re.fullmatch(APPROVAL_RE, contents(approval, APPROVAL))
    need(body is not None, "APPROVAL")
    freeze, *named = (x.decode("ascii") for x in body.groups())
    parent = git("rev-list", "--parents", "-n", "1", approval).stdout.split()[1:]
    need(tuple(named) == (freeze_pin, input_pin, roster_pin, dist_pin) and len(parent) == 1, "APPROVAL")
    # The approval sits directly on the freeze, so every pinned file (including the whole config) is the frozen one.
    need(parent[0].decode() == freeze, "APPROVAL")
    need(git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", approval).stdout
         == f"A\t{APPROVAL}\n".encode(), "APPROVAL")
    need(git("cat-file", "-e", f"{freeze}:{APPROVAL}", allow=True).returncode != 0, "APPROVAL")
    manifest = pinned(REPO / PINS, freeze_pin)
    need(manifest == contents(freeze, PINS) == contents(approval, PINS), "FREEZE")
    pins = parse(manifest)
    need(type(pins) is dict and set(pins) == PIN_NAMES | {ROSTER_PIN} and all(map(is_pin, pins.values()))
         and pins[ROSTER_PIN] == roster_pin, "FREEZE")
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
    C = ModuleType("common_48_verified")
    exec(compile(blob, ENGINE, "exec"), C.__dict__)
    return C


def read_config(blob):
    # One JSON-flow YAML value, read without a third-party parser.
    block = re.findall(rb"(?m)^replay_48_plan:\n  value: (\{[^\n]+\})\n", blob)
    need(len(block) == 1, "CONFIG")
    cfg = parse(block[0])
    need(type(cfg) is dict and set(cfg) == CONFIG_KEYS, "CONFIG")
    need(set(cfg["cost"]) == {"extra_bps", "proxy_half_bps", "window_start", "measure_start", "measure_end",
                              "expiry_seconds", "min_coverage_seconds"}
         and set(cfg["marks"]) == {"min_positive_years", "min_years_ahead_of_benchmark", "drop_best"}
         and set(cfg["calibration"]) == {"trials", "seed", "edges", "benchmark_sd", "group_beta",
                                         "group_residual_sd", "beta_only_premium", "loser_residual_sd",
                                         "null_ceiling"}
         and set(cfg["resources"]) == {"minimum_free_mib", "process_cap_mib", "nice"}, "CONFIG")
    return cfg


def check_calibration(C, cfg, blob):
    need(blob == encode(C.calibrate(cfg)), "CALIBRATION")


def input_names(cfg):
    years = range(cfg["first_turn"], cfg["last_turn"] + 1)
    return ({"roster.csv", "distributions.json"} | {f"bars_{y}.json" for y in years}
            | {f"quotes_{y}.json" for y in years})


def load_inputs(input_dir, input_pin, roster_pin, dist_pin, C, calendar_blob, cfg):
    private_dir(input_dir)
    windows = C.turns(parse(calendar_blob), cfg)
    m = parse(pinned(input_dir / "manifest.json", input_pin, private=True))
    need(type(m) is dict and set(m) == {"schema", "mode", "feed", "adjustment", "first_turn", "last_turn",
                                       "collected_utc", "files"}
         and type(m["schema"]) is int and m["schema"] == 1 and m["mode"] == "plan48_raw_sip_v1"
         and m["feed"] == "sip" and m["adjustment"] == "raw" and m["first_turn"] == cfg["first_turn"]
         and m["last_turn"] == cfg["last_turn"], "MANIFEST")
    ts = m["collected_utc"]
    need(type(ts) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", ts) is not None
         and datetime.fromisoformat(ts.replace("Z", "+00:00")).date() > windows[-1]["exit"], "MANIFEST_CLOCK")
    names = input_names(cfg)
    need(type(m["files"]) is dict and set(m["files"]) == names and all(map(is_pin, m["files"].values()))
         and {p.name for p in input_dir.iterdir()} == names | {"manifest.json"}
         and m["files"]["roster.csv"] == roster_pin and m["files"]["distributions.json"] == dist_pin,
         "MANIFEST_FILES")
    roster = C.roster(pinned(input_dir / "roster.csv", roster_pin, private=True), cfg)
    cash = C.distributions(parse(pinned(input_dir / "distributions.json", dist_pin, private=True)),
                           windows, roster, cfg)
    packet = {}
    for w in windows:
        y = w["turn"]
        funds, bench = C.bars_file(parse(pinned(input_dir / f"bars_{y}.json", m["files"][f"bars_{y}.json"],
                                                private=True)), w, roster[y], cfg)
        quotes = C.quotes_file(parse(pinned(input_dir / f"quotes_{y}.json", m["files"][f"quotes_{y}.json"],
                                            private=True)), w, roster[y], cfg)
        for s, closes in funds.items():
            C.check_jumps(closes, cash[y][0][s]["splits"], cfg)
        C.check_jumps(bench, [], cfg)
        packet[y] = (funds, bench, quotes, cash[y])
    return windows, packet, roster


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
        write_new(run / "score_48.lock", encode(job))
    except FileExistsError:
        raise Refused("P48_CONSUMED_OR_NOT_EMPTY") from None
    sync_dir(run)
    result = encode({"job": job} | evaluate(*inputs))
    tmp = run / ".results_48.tmp"
    write_new(tmp, result)
    os.link(tmp, run / "results_48.json", follow_symlinks=False)
    sync_dir(run)
    tmp.unlink()
    sync_dir(run)


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "P48_ARGUMENTS\n")


def check_environment():
    need(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize == 0
         and not any(k.startswith(("P48_", "PLAN48_", "GIT_", "PYTHON", "LD_")) or k in {"TZ", "TZDIR"}
                     for k in os.environ), "ENVIRONMENT")


def main():
    p = Parser(description=__doc__, allow_abbrev=False)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--calibrate", action="store_true")
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--go", action="store_true")
    for flag in ("--approval-commit", "--freeze-sha256", "--input-sha256", "--roster-sha256",
                 "--distributions-sha256"):
        p.add_argument(flag)
    a = p.parse_args()
    os.umask(0o077)
    try:
        if a.calibrate:
            # Synthetic only: reads the working-tree engine and config, never the input or run directories.
            need(not any((a.approval_commit, a.freeze_sha256, a.input_sha256, a.roster_sha256,
                          a.distributions_sha256)), "ARGUMENTS")
            C = load_engine((REPO / ENGINE).read_bytes())
            sys.stdout.buffer.write(encode(C.calibrate(read_config((REPO / CONFIG).read_bytes()))))
            return
        pins = (a.approval_commit, a.freeze_sha256, a.input_sha256, a.roster_sha256, a.distributions_sha256)
        need(all(v is not None for v in pins), "ARGUMENTS")
        check_environment()
        freeze, blobs = authorize(*pins)
        C = load_engine(blobs[ENGINE])
        cfg = read_config(blobs[CONFIG])
        resources(cfg)
        try:
            check_calibration(C, cfg, blobs[CALIBRATION])
            inputs = load_inputs(INPUTS, a.input_sha256, a.roster_sha256, a.distributions_sha256, C,
                                 blobs[CALENDAR], cfg)
        except C.Refused as exc:
            raise Refused(str(exc)) from None
        windows, packet, roster = inputs
        if a.validate_inputs:
            print("P48_INPUTS_OK", "turns", len(windows), "roster_rows", sum(len(v) for v in roster.values()),
                  "symbol_files", 2 * len(windows))
            return
        meta = {"schema": 1, "ledger": LEDGER_ROW, "queue": QUEUE_ROW, "freeze_commit": freeze,
                "approval_commit": a.approval_commit, "freeze_sha256": a.freeze_sha256,
                "input_sha256": a.input_sha256, "roster_sha256": a.roster_sha256,
                "distributions_sha256": a.distributions_sha256}
        need((freeze, blobs) == authorize(*pins), "APPROVAL")
        try:
            once(RUN, meta, (windows, packet, cfg), C.evaluate)
        except C.Refused as exc:
            raise Refused(str(exc)) from None
    except Refused as exc:
        p.exit(2, f"{exc}\n")
    except Exception:
        p.exit(2, "P48_REFUSED\n")
    print("P48_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
