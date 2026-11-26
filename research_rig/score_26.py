"""Validate or score one explicitly approved offline Replay 26 input set."""
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

import common_26 as C

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DATA = Path("/home/user/workspace/rig/data/replay_26")
EXPORTS = Path("/home/user/workspace/rig/data/plan26_inputs")
ACTIONS = Path("/home/user/workspace/rig/data/plan26_sources/cash_actions_2002_2015.json")
SIP = Path("/home/user/workspace/rig/data/replay_25/inputs")
PLAN = "PREREG_26_treasury_month_end_early.md"
PINS = "PINNED_26.json"
APPROVAL = "APPROVAL_26.md"
PINNED_FILES = (PLAN, "common_26.py", "score_26.py", "test_26.py", "calendar_26.json", "source_26.json",
                "common_25.py", "calendar_25.json")
PARTS = {"a": (C.FIRST, C.PULL_A_LAST, 4640), "b": (C.PULL_B_FIRST, C.EXPORT_LAST, 1486)}
NAMES = {f"{s}_{part}.json" for s in C.SYMBOLS for part in PARTS}
NORMALIZER = "normalize_plan26.py"
APPROVAL_LINE = (rb"Approved by the lead: plan 26, private workspace source confirmed, validation and one "
                 rb"scored run, freeze commit ([0-9a-f]{40})\.\n")


def pin(value):
    C.need(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value), "PIN")


def digest(blob):
    return sha256(blob).hexdigest()


def unique_pairs(pairs):
    out = {}
    for key, value in pairs:
        C.need(key not in out, "JSON_DUPLICATE_KEY")
        out[key] = value
    return out


def parse(blob, decimal=False):
    def bad_constant(_):
        raise C.Refused("P26_JSON_NUMBER")

    return json.loads(blob, object_pairs_hook=unique_pairs, parse_constant=bad_constant,
                      parse_float=Decimal if decimal else float)


def pinned(path, expected, private=False):
    pin(expected)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
        info = os.fstat(stream.fileno())
        C.need(stat.S_ISREG(info.st_mode), "INPUT_FILE")
        limit = 12 * 1024 * 1024
        C.need(info.st_size <= limit, "INPUT_FILE")
        if private:
            C.need(info.st_uid == os.geteuid() and info.st_mode & 0o077 == 0, "INPUT_PRIVATE")
        blob = stream.read(limit + 1)
    C.need(len(blob) <= limit and digest(blob) == expected, "PIN")
    return blob


def private_dir(path):
    s = path.lstat()
    C.need(path.resolve() == path and stat.S_ISDIR(s.st_mode) and s.st_uid == os.geteuid()
           and s.st_mode & 0o077 == 0, "INPUT_PRIVATE")


def resources():
    with open("/proc/meminfo") as stream:
        available = next(int(s.split()[1]) for s in stream if s.startswith("MemAvailable:"))
    C.need(available >= 1_572_864, "LOW_MEMORY")
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = min(x for x in (292_968 * 1024, soft, hard) if x != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
    if os.nice(0) < 10:
        os.nice(10 - os.nice(0))


def authorize(approval, freeze_pin):
    C.need(not any(k.startswith("P26_") for k in os.environ), "ENVIRONMENT")
    C.need(re.fullmatch(r"[0-9a-f]{40}", approval), "APPROVAL")
    pin(freeze_pin)

    def git(*args, allow=False):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        p = subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, env=env, timeout=15)
        C.need(allow or p.returncode == 0, "APPROVAL")
        return p

    def frozen_blob(commit, name):
        return git("show", f"{commit}:research_rig/{name}").stdout

    C.need(git("rev-parse", "HEAD").stdout.decode().strip() == approval, "APPROVAL")
    C.need(not git("status", "--porcelain", "--untracked-files=no").stdout.strip(), "APPROVAL")
    mark = re.fullmatch(APPROVAL_LINE, frozen_blob(approval, APPROVAL))
    C.need(mark is not None, "APPROVAL")
    freeze = mark[1].decode()
    C.need(freeze != approval and git("merge-base", "--is-ancestor", freeze, approval, allow=True).returncode == 0,
           "APPROVAL")
    C.need(git("cat-file", "-e", f"{freeze}:research_rig/{APPROVAL}", allow=True).returncode != 0,
           "APPROVAL")
    blob = pinned(HERE / PINS, freeze_pin)
    C.need(blob == frozen_blob(freeze, PINS) == frozen_blob(approval, PINS), "FREEZE")
    pins = parse(blob)
    C.need(set(pins) == set(PINNED_FILES), "FREEZE")
    for value in pins.values():
        pin(value)
    verified = {name: pinned(HERE / name, pins[name]) for name in PINNED_FILES}
    for name, raw in verified.items():
        C.need(raw == frozen_blob(freeze, name) == frozen_blob(approval, name), "FREEZE")
    C.need(verified[PLAN].splitlines().count(b"Status FROZEN.") == 1, "FREEZE")
    source_contract(parse(verified["source_26.json"]))
    ledger = frozen_blob(freeze, "TRIAL_LEDGER.md")
    C.need(re.search(rb"(?m)^\| 163 \|[^\n]+" + re.escape(PLAN.encode()) + rb"\x60 \|", ledger), "LEDGER")
    return freeze, verified


def exported_files(manifest, source):
    C.need(type(manifest) is dict and set(manifest) == {"schema", "route", "adjust_flag", "terms_note",
                                                        "pull_cap_note", "funds"}
           and type(manifest["schema"]) is int and manifest["schema"] == 1 and manifest["route"] == source["route"]
           and manifest["adjust_flag"] == source["export_adjust_flag"]
           and all(type(manifest[k]) is str and 0 < len(manifest[k].strip()) <= 1500
                   for k in ("terms_note", "pull_cap_note"))
           and type(manifest["funds"]) is dict and set(manifest["funds"]) == set(C.SYMBOLS), "MANIFEST")
    staged, native = {}, {}
    for symbol, pulls in manifest["funds"].items():
        C.need(type(pulls) is dict and set(pulls) == set(PARTS), "PROVENANCE")
        for part, (first, last, size) in PARTS.items():
            f = pulls[part]
            C.need(type(f) is dict and set(f) == {"file", "sha256", "source_file", "source_sha256", "pulled_utc",
                                                "row_count", "first", "last", "normalization"}
                   and f["file"] == f"{symbol}_{part}.json" and type(f["row_count"]) is int and f["row_count"] == size
                   and f["source_file"] == f"native/{symbol}_{part}_native.csv"
                   and f["first"] == str(first) and f["last"] == str(last)
                   and isinstance(f["pulled_utc"], str) and re.fullmatch(
                       r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?Z", f["pulled_utc"]), "PROVENANCE")
            n = f["normalization"]
            C.need(type(n) is dict and set(n) == {"script", "script_sha256", "recipe"}
                   and n["script"] == NORMALIZER and n["script_sha256"] == source["normalizer_sha256"]
                   and type(n["recipe"]) is str and 0 < len(n["recipe"].strip()) <= 1500, "PROVENANCE")
            datetime.fromisoformat(f["pulled_utc"].replace("Z", "+00:00"))
            pin(f["source_sha256"])
            pin(f["sha256"])
            staged[f["file"]] = f["sha256"]
            native[f["source_file"]] = f["source_sha256"]
    return staged, native


def joins(a, b, a_days, b_days, expected_days, sip_closes):
    full_a, prices_a = C.vendor_bars(a, a_days)
    _, prices_b = C.vendor_bars(b, b_days)
    duplicate = tuple(d for d in a_days if d >= C.PULL_B_FIRST)
    C.need(len(duplicate) == 22 and duplicate == b_days[:len(duplicate)], "JOIN_CLOCK")
    C.need(all((left["date"], left["close"]) == (right["date"], right["close"])
               for left, right in zip(a[-len(duplicate):], b[:len(duplicate)], strict=True)), "JOIN_CLOSE")
    overlap_a = {d: p for d, p in prices_a.items() if d > C.LAST}
    joined = overlap_a | {d: p for d, p in prices_b.items() if d > C.PULL_A_LAST}
    checks = {
        "a": C.compare_closes(overlap_a, {d: p for d, p in sip_closes.items() if d <= C.PULL_A_LAST}),
        "b": C.compare_closes(prices_b, {d: p for d, p in sip_closes.items() if d >= C.PULL_B_FIRST}),
        "all": C.compare_closes(joined, sip_closes),
    }
    return {d: full_a[d] for d in expected_days}, checks


def prepare(root, inputs_pin, verified, exports=EXPORTS, actions=ACTIONS, sip=SIP):
    # Returns no values outside the process. This function never calls the strategy.
    private_dir(root)
    private_dir(exports)
    private_dir(actions.parent)
    private_dir(sip)
    source = source_contract(parse(verified["source_26.json"]))
    C.need(inputs_pin == source["export_manifest_sha256"], "EXPORT_PIN")
    manifest = parse(pinned(exports / "manifest.json", inputs_pin, private=True))
    files, native = exported_files(manifest, source)
    C.need({p.name for p in exports.iterdir()} == NAMES | {"manifest.json", "native", NORMALIZER}, "MANIFEST")
    native_dir = exports / "native"
    private_dir(native_dir)
    C.need({p.name for p in native_dir.iterdir()} == {Path(n).name for n in native}, "MANIFEST")
    pinned(exports / NORMALIZER, source["normalizer_sha256"], private=True)
    for name, expected in native.items():
        pinned(exports / name, expected, private=True)
    sm = parse(pinned(sip / "manifest.json", C.SIP_MANIFEST_SHA, private=True))
    C.need(sm["feed"] == "sip" and sm["adjustment"] == "raw" and sm["draft_sha256"] == C.SIP_DRAFT_SHA,
           "SIP_MANIFEST")
    for sym in C.SYMBOLS:
        pin(sm["files"][sym + ".json"])
    raw = {name: pinned(exports / name, files[name], private=True) for name in sorted(NAMES)}
    cash = pinned(actions, C.ACTIONS_SHA, private=True)
    reference = {s: pinned(sip / (s + ".json"), sm["files"][s + ".json"], private=True) for s in C.SYMBOLS}

    expected_days = C.calendar(parse(verified["calendar_26.json"]))
    days25 = C.engine.check_calendar(parse(verified["calendar_25.json"]))
    overlap_days = tuple(d for d in days25 if d <= C.OVERLAP_LAST)
    C.need(len(overlap_days) == 2723 and overlap_days[-1] == C.EXPORT_LAST, "OVERLAP_CLOCK")
    a_days = expected_days + tuple(d for d in overlap_days if d <= C.PULL_A_LAST)
    b_days = tuple(d for d in overlap_days if d >= C.PULL_B_FIRST)
    C.need(len(a_days) == PARTS["a"][2] and len(b_days) == PARTS["b"][2], "JOIN_CLOCK")
    tape, counts = {}, {}
    for sym in C.SYMBOLS:
        sip_rows = parse(reference[sym], True)
        C.need(type(sip_rows) is list and len(sip_rows) == len(days25), "OVERLAP_CLOCK")
        closes = {}
        for row, d in zip(sip_rows, days25, strict=True):
            C.need(C.engine.session(row["t"]) == d, "OVERLAP_CLOCK")
            if d <= C.OVERLAP_LAST:
                closes[d] = C.checked_number(row["c"])
        a = parse(raw[sym + "_a.json"], True)
        b = parse(raw[sym + "_b.json"], True)
        tape[sym], counts[sym] = joins(a, b, a_days, b_days, expected_days, closes)
    days = tuple(tape["TLT"])  # Both tapes already match the independently pinned session list.
    return days, tape, C.cash_actions(parse(cash), days), counts


def source_contract(source):
    C.need(type(source) is dict and set(source) == {"name", "route", "terms_url", "terms_note", "upstream_adjustment",
                                                    "adjustment", "status", "export_manifest_sha256",
                                                    "export_adjust_flag", "normalizer_sha256"}
           and source["status"] == "lead_selected" and source["adjustment"] == "raw"
           and all(type(source[k]) is str and 0 < len(source[k].strip()) <= 500
                   for k in ("name", "route", "terms_url", "terms_note", "upstream_adjustment", "export_adjust_flag"))
           and source["terms_url"].startswith("https://"), "SOURCE")
    pin(source["export_manifest_sha256"])
    pin(source["normalizer_sha256"])
    return source


def encode(data):
    return (json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def scored(job, inside):
    days, tape, payouts, counts = inside
    measured, shown = C.scored(days, tape["TLT"], payouts["TLT"], True)
    ief, _ = C.scored(days, tape["IEF"], payouts["IEF"], False)
    return {"job": job, "overlap_agreements": counts, "judged_TLT": measured, "shown_TLT": shown,
            "shown_IEF_same_rule": ief}


def once(root, job, validate, calculate):
    lock, result = root / "score_26.lock", root / "results_26.json"
    C.need(not os.path.lexists(lock) and not os.path.lexists(result), "CONSUMED")
    inputs = validate()
    try:
        with lock.open("xb") as stream:
            stream.write(encode(job))
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        raise C.Refused("P26_CONSUMED") from None
    output = encode(calculate(inputs))
    with result.open("xb") as stream:
        stream.write(output)
        stream.flush()
        os.fsync(stream.fileno())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--go", action="store_true")
    p.add_argument("--approval-commit", required=True)
    p.add_argument("--freeze-sha256", required=True)
    p.add_argument("--input-sha256", required=True)
    args = p.parse_args()
    os.umask(0o077)
    try:
        C.need(not any(k.startswith("P26_") for k in os.environ), "ENVIRONMENT")
        resources()
        pin(args.input_sha256)
        freeze, verified = authorize(args.approval_commit, args.freeze_sha256)
        prepare_input = lambda: prepare(DATA, args.input_sha256, verified)
        if args.validate_inputs:
            _, _, _, counts = prepare_input()
            print("P26_OVERLAP_AGREEMENTS",
                  *(f"{s} {part} {counts[s][part][0]} {counts[s][part][1]}"
                    for s in C.SYMBOLS for part in ("a", "b", "all")))
            return
        job = {"schema": 1, "ledger": 163, "freeze_commit": freeze,
               "approval_commit": args.approval_commit, "freeze_sha256": args.freeze_sha256,
               "input_sha256": args.input_sha256, "cash_actions_sha256": C.ACTIONS_SHA,
               "sip_inputs_sha256": C.SIP_MANIFEST_SHA, "claimed_utc": datetime.now(timezone.utc).isoformat()}
        once(DATA, job, prepare_input, lambda inputs: scored(job, inputs))
    except C.Refused as exc:
        p.exit(2, f"{exc}\n")
    except (KeyError, ValueError, TypeError, IndexError, OSError, StopIteration, ArithmeticError,
            C.engine.Refused, subprocess.SubprocessError):
        p.exit(2, "P26_REFUSED\n")
    print("P26_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
