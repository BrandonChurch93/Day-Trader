"""One-shot scoring. All validation is silent; model evaluation follows exclusive claim."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import resource

import common_25 as C
import fetch_25 as F

LIMITS = [
    "The consolidated SIP daily close is a proxy, not the auction print or a verified executable exchange close.",
    "The published 0.25% a month is a modeled 10-year Treasury position net of GC repo over 1990–2018, not an ETF.",
    "The unlevered replay has fixed per-side costs, no interest on idle cash or payouts, and no taxes.",
    "Window and Welch t-statistics are descriptive IID-style measures, not serial-dependence corrections.",
    "The replay uses raw SIP bars and the approved dated cash-action packet only.",
]


def resources():
    with open("/proc/meminfo") as stream:
        available = next(int(s.split()[1]) for s in stream if s.startswith("MemAvailable:"))
    C.need(available >= 1_572_864, "P25_LOW_MEMORY")
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    cap = min(x for x in (292_968 * 1024, soft, hard) if x != resource.RLIM_INFINITY)
    resource.setrlimit(resource.RLIMIT_AS, (cap, hard))
    if os.nice(0) < 10:
        os.nice(10 - os.nice(0))


def prepare(draft_sha, manifest_sha, actions_sha, root):
    for pin in (draft_sha, manifest_sha, actions_sha):
        F.check_pin(pin)
    days = F.draft(draft_sha)
    path = root / "inputs"
    F.private_dir(path)
    m = json.loads(F.pinned(path / "manifest.json", manifest_sha, private=True))
    C.need(set(m) == {"schema", "mode", "feed", "adjustment", "start", "end", "collected_utc",
                       "draft_sha256", "files"} and m["schema"] == 1 and m["feed"] == "sip"
           and m["start"] == str(C.BAR_FROM) and m["end"] == str(C.DATA_END)
           and m["draft_sha256"] == draft_sha, "P25_MANIFEST")
    C.need(m["mode"] == F.RAW and m["adjustment"] == "raw", "P25_MANIFEST")
    names = {s + ".json" for s in C.SYMBOLS} | {"cash_actions.json"}
    C.need(set(m["files"]) == names and {p.name for p in path.iterdir()} == names | {"manifest.json"},
           "P25_MANIFEST")
    for name in sorted(names):
        F.check_pin(m["files"][name])
    C.need(m["files"]["cash_actions.json"] == actions_sha, "P25_ACTION_PIN")
    payloads = {name: F.pinned(path / name, m["files"][name], private=True) for name in sorted(names)}
    data = {name: json.loads(payload) for name, payload in payloads.items()}
    actions = data["cash_actions.json"]
    C.check_actions(actions, days)
    tape, cash = {}, {}
    for sym in C.SYMBOLS:
        rows = data[sym + ".json"]
        C.check_bar_clocks(rows, days)
        tape[sym] = C.price_tape(rows, days)
        cash[sym] = C.distributions(actions["funds"][sym]["cash"])
    return m, days, tape, cash


def claim(root, job, validate, calculate):
    lock, result = root / "score_25.lock", root / "results_25.json"
    C.need(not os.path.lexists(lock) and not os.path.lexists(result), "P25_CONSUMED")
    inputs = validate()
    try:
        with lock.open("xb") as stream:
            stream.write(F.encode(job))
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        raise C.Refused("P25_CONSUMED") from None
    output = F.encode(calculate(inputs))
    with result.open("xb") as stream:
        stream.write(output)
        stream.flush()
        os.fsync(stream.fileno())


def outcome(job, inputs):
    m, days, tape, cash = inputs
    tlt = C.evaluate(days, tape["TLT"], cash["TLT"])
    ief = C.evaluate(days, tape["IEF"], cash["IEF"])
    return {"job": job, "mode": m["mode"], "judged_TLT": tlt["judged"],
            "shown_TLT": tlt["shown"],
            "shown_IEF_same_rule": {k: v for k, v in ief["judged"].items() if k not in {"gates", "passes"}},
            "limits": LIMITS[:]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--go", action="store_true", required=True)
    p.add_argument("--approved-draft-sha256", required=True)
    p.add_argument("--approved-input-sha256", required=True)
    p.add_argument("--approved-actions-sha256", required=True)
    a = p.parse_args()
    os.umask(0o077)
    try:
        resources()
        root = F.DATA
        F.private_dir(root)
        job = {"schema": 1, "ledger": 162, "draft_sha256": a.approved_draft_sha256,
               "inputs_sha256": a.approved_input_sha256,
               "actions_sha256": a.approved_actions_sha256,
               "claimed_utc": datetime.now(timezone.utc).isoformat()}
        # No returns are computed by prepare; the exclusive lock is claimed between these callbacks.
        claim(root, job, lambda: prepare(a.approved_draft_sha256, a.approved_input_sha256,
                                        a.approved_actions_sha256, root),
              lambda data: outcome(job, data))
    except C.Refused as exc:
        p.exit(2, f"{exc}\n")
    except (KeyError, ValueError, TypeError, IndexError, StopIteration, OSError, ArithmeticError):
        p.exit(2, "P25_SCORE_REFUSED\n")
    print("P25_RESULT_WRITTEN")


if __name__ == "__main__":
    main()
