"""Plan 52: synthetic calibration, pinned validation, or one locked score."""
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
from zoneinfo import reset_tzpath

REPO = Path(__file__).resolve().parent.parent
DATA = Path("/home/user/workspace/rig/data")
INPUTS, RUN = DATA / "plan52_inputs", DATA / "replay_52"
PLAN = "research_rig/PREREG_52_quarter_end_dealer_rebound.md"
PINS = "research_rig/PINNED_52.json"
APPROVAL = "research_rig/APPROVAL_52.md"
CALENDARS = ["research_rig/calendar_25.json"]
ENGINE = "research_rig/common_52.py"
CONFIG = "config/thresholds.yaml"
CALIBRATION = "research_rig/CALIBRATION_52.json"
PIN_NAMES = {PLAN, *CALENDARS, ENGINE, CONFIG, CALIBRATION, "research_rig/score_52.py", "research_rig/test_52.py"}
CAP = 64 * 1024 * 1024
APPROVAL_RE = (
    rb"Approved by the lead: plan 52, validation and one scored run, freeze commit ([0-9a-f]{40}), "
    rb"freeze SHA-256 ([0-9a-f]{64}), input SHA-256 ([0-9a-f]{64}), actions SHA-256 ([0-9a-f]{64})\.\n"
)


class Refused(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Refused("P52_" + code)


def is_pin(v):
    return type(v) is str and re.fullmatch(r"[0-9a-f]{64}", v) is not None


def pinned(path, pin, private=False):
    need(is_pin(pin), "PIN")
    need(path.resolve() == path, "FILE")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        st = os.fstat(stream.fileno())
        need(stat.S_ISREG(st.st_mode) and st.st_size <= CAP, "FILE")
        if private:
            need(st.st_uid == os.geteuid() and stat.S_IMODE(st.st_mode) == 0o600, "PRIVATE")
        blob = stream.read(CAP + 1)
    need(len(blob) <= CAP and sha256(blob).hexdigest() == pin, "PIN")
    return blob


def unique(pairs):
    obj = dict(pairs)
    need(len(obj) == len(pairs), "JSON_DUPLICATE")
    return obj


def reject_number(_):
    raise Refused("P52_JSON_NUMBER")


def parse(blob):
    return json.loads(blob, object_pairs_hook=unique, parse_constant=reject_number)


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


def git(*args):
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_OPTIONAL_LOCKS": "0"}
    proc = subprocess.run(["/usr/bin/git", "--no-replace-objects", "-c", "core.fsmonitor=false",
                           "-c", "safe.directory=*", "-C", str(REPO), *args], capture_output=True, env=env, timeout=15)
    need(proc.returncode == 0, "APPROVAL")
    return proc.stdout


def read_config(blob):
    matches = re.findall(rb"(?m)^replay_52_plan:\n  value: (\{[^\n]+\})\n", blob)
    need(len(matches) == 1, "CONFIG")
    cfg = parse(matches[0])
    need(set(cfg) == set(("ledger_row queue_row judged_first_year judged_last_year shown_last_month first_bar_date "
                          "last_bar_date sessions_per_symbol funds proxies expected_splits budget_usd held_sessions "
                          "cost_bps_per_side max_identical_ohlc_run_exclusive expected marks calibration resources").split())
         and len(cfg["funds"]) == len(set(cfg["funds"])) and set(cfg["funds"]) == set(cfg["proxies"])
         and not (set(cfg["funds"]) & set(cfg["proxies"].values())), "CONFIG")
    m = cfg["marks"]
    need(type(m["raw_t_required"]) is bool and m["breadth"] in {"sixty_percent", "strict_majority", "none"}, "CONFIG")
    return cfg


def authorize(approval, freeze_pin, input_pin, actions_pin):
    need(type(approval) is str and re.fullmatch(r"[0-9a-f]{40}", approval) is not None, "APPROVAL")
    need(all(map(is_pin, (freeze_pin, input_pin, actions_pin))), "PIN")
    need(git("rev-parse", "HEAD").strip() == approval.encode()
         and not git("status", "--porcelain", "--untracked-files=all"), "APPROVAL")
    body = re.fullmatch(APPROVAL_RE, git("show", f"{approval}:{APPROVAL}"))
    need(body is not None, "APPROVAL")
    freeze, *pins = [x.decode("ascii") for x in body.groups()]
    need(pins == [freeze_pin, input_pin, actions_pin]
         and git("rev-list", "--parents", "-n", "1", approval).split()[1:] == [freeze.encode()]
         and git("diff-tree", "--no-commit-id", "--no-renames", "--name-status", "-r", approval)
         == f"A\t{APPROVAL}\n".encode(), "APPROVAL")
    manifest = pinned(REPO / PINS, freeze_pin)
    need(manifest == git("show", f"{freeze}:{PINS}"), "FREEZE")
    expected = parse(manifest)
    need(type(expected) is dict and set(expected) == PIN_NAMES and all(map(is_pin, expected.values())), "FREEZE")
    blobs = {name: pinned(REPO / name, expected[name]) for name in expected}
    need(all(b == git("show", f"{freeze}:{name}") for name, b in blobs.items()), "FREEZE")
    need([s for s in blobs[PLAN].splitlines() if s.startswith(b"Status ")] == [b"Status FROZEN."], "FREEZE")
    cfg = read_config(blobs[CONFIG])
    cal = parse(blobs[CALIBRATION])
    need(cal["synthetic_only"] is True and cal["assumptions"] == cfg["calibration"]
         and cal["observations"] == cfg["expected"]
         and cal["selected"] == {k: cfg["marks"][k] for k in ("raw_t_required", "breadth")}, "CALIBRATION")
    ref = b"`" + PLAN.encode() + b"`"
    for name, row, code in (("research_rig/TRIAL_LEDGER.md", cfg["ledger_row"], "LEDGER"),
                            ("docs/QUEUE.md", cfg["queue_row"], "QUEUE")):
        lines = [line for line in git("show", f"{freeze}:{name}").splitlines() if line.startswith(f"| {row} |".encode())]
        need(len(lines) == 1 and ref in lines[0], code)
    return freeze, blobs, cfg


def load_engine(blob):
    reset_tzpath(("/usr/share/zoneinfo",))
    mod = ModuleType("common_52_verified")
    exec(compile(blob, ENGINE, "exec"), mod.__dict__)
    return mod


def load_input(input_dir, cfg, C, calendar_blobs, pin, actions_pin):
    days = C.calendar(calendar_blobs, cfg)
    spans = C.windows(days, cfg)
    private_dir(input_dir)
    m = parse(pinned(input_dir / "manifest.json", pin, private=True))
    C.keys(m, "schema vendor feed adjustment frequency start end collected_utc files", "MANIFEST")
    need(type(m["schema"]) is int and m["schema"] == 1
         and type(m["vendor"]) is str and m["vendor"].strip() and
         (m["feed"], m["adjustment"], m["frequency"], m["start"], m["end"])
         == ("sip", "raw", "daily", days[0].isoformat(), days[-1].isoformat()), "MANIFEST")
    # With the pinned endpoint, 21:00 UTC is at or after the last regular NY close.
    # The whole next UTC day is safe regardless of early closes or daylight saving.
    need(C.utc(m["collected_utc"]).date() > days[-1], "COLLECTION_CLOCK")
    syms = C.symbols(cfg)
    actions = "cash_actions.json"
    filenames = {f"{s}.json" for s in syms} | {actions}
    need(type(m["files"]) is dict and set(m["files"]) == filenames and all(map(is_pin, m["files"].values()))
         and m["files"][actions] == actions_pin and {p.name for p in input_dir.iterdir()} == filenames | {"manifest.json"},
         "MANIFEST_FILES")
    cash, split_count = C.cash_actions(parse(pinned(input_dir / actions, actions_pin, private=True)), days, spans, cfg)
    prices = {s: C.bars(parse(pinned(input_dir / f"{s}.json", m["files"][f"{s}.json"], private=True)), days, cfg)
              for s in syms}
    return spans, prices, cash, split_count


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


def once(run, meta, inputs, evaluate):
    private_dir(run)
    need(not any(run.iterdir()), "CONSUMED_OR_NOT_EMPTY")
    job = meta | {"claimed_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    try:
        write_new(run / "score_52.lock", encode(job))
    except FileExistsError:
        raise Refused("P52_CONSUMED_OR_NOT_EMPTY") from None
    sync_dir(run)
    payload = encode({"job": job} | evaluate(*inputs))
    temp = run / ".results_52.tmp"
    write_new(temp, payload)
    os.link(temp, run / "results_52.json", follow_symlinks=False)
    sync_dir(run)
    temp.unlink()
    sync_dir(run)


class Parser(argparse.ArgumentParser):
    def error(self, _message):
        self.exit(2, "P52_ARGUMENTS\n")


def check_environment():
    need(sys.flags.isolated and sys.dont_write_bytecode and sys.flags.optimize == 0
         and not any(k.startswith(("P52_", "PLAN52_", "GIT_", "PYTHON", "LD_")) or k in {"TZ", "TZDIR"}
                     for k in os.environ), "ENVIRONMENT")


def main():
    p = Parser(description=__doc__, allow_abbrev=False)
    mode = p.add_mutually_exclusive_group(required=True)
    for name in ("--validate-inputs", "--calibrate", "--go"):
        mode.add_argument(name, action="store_true")
    for name in ("--approval-commit", "--freeze-sha256", "--input-sha256", "--actions-sha256"):
        p.add_argument(name)
    a = p.parse_args()
    args = (a.approval_commit, a.freeze_sha256, a.input_sha256, a.actions_sha256)
    os.umask(0o077)
    try:
        if a.calibrate:
            need(all(v is None for v in args), "ARGUMENTS")
            C = load_engine((REPO / ENGINE).read_bytes())
            sys.stdout.buffer.write(encode(C.calibrate(read_config((REPO / CONFIG).read_bytes()))))
            return
        need(all(v is not None for v in args), "ARGUMENTS")
        check_environment()
        freeze, blobs, cfg = authorize(*args)
        C = load_engine(blobs[ENGINE])
        resources(cfg)
        try:
            spans, prices, cash, splits = load_input(INPUTS, cfg, C, [parse(blobs[name]) for name in CALENDARS],
                                                     a.input_sha256, a.actions_sha256)
            if a.validate_inputs:
                print("P52_INPUTS_OK", "events_placed", sum(map(len, spans.values())),
                      "judged_clusters", len(spans["quarters"]), "control_clusters", len(spans["controls"]),
                      "shown_clusters", len(spans["shown"]), "non_december_clusters", cfg["expected"]["non_december"],
                      "symbols", len(prices), "sessions_per_symbol", cfg["sessions_per_symbol"],
                      "bar_rows", sum(map(len, prices.values())), "splits_checked", splits, "crossed_splits", 0)
                return
            meta = {"schema": 1, "ledger": cfg["ledger_row"], "queue": cfg["queue_row"],
                    "freeze_commit": freeze, "approval_commit": a.approval_commit, "freeze_sha256": a.freeze_sha256,
                    "input_sha256": a.input_sha256, "actions_sha256": a.actions_sha256}
            need((freeze, blobs, cfg) == authorize(*args), "APPROVAL")
            once(RUN, meta, (spans, prices, cash, cfg), C.evaluate)
        except C.Refused as exc:
            raise Refused(str(exc)) from None
    except Refused as exc:
        p.exit(2, f"{exc}\n")
    except Exception:
        p.exit(2, "P52_REFUSED\n")
    print("P52_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
