"""Pure price-free Plan 63 request planner shared by custody tooling."""
from collections import defaultdict
from hashlib import sha256
import json
import re

from count_63 import CUTOFF, HOLDS, candidates, select
from placebo_63 import admissible, touches_deny


PLACEBO_EXCLUSIONS_SHA = "7eceed81899f00a7002ded8fbf2577da73d46af02f5a8ea4ecce90448b81f405"
PLACEBO_EXCLUSIONS_NAME = "placebo_exclusions.json"
N_PURGED = 9


def parse_placebo_exclusions(data, pin=PLACEBO_EXCLUSIONS_SHA):
    if type(data) is not bytes or sha256(data).hexdigest() != pin:
        raise ValueError("placebo exclusion digest")
    rows = json.loads(data)
    if (type(rows) is not list or len(rows) != N_PURGED or
            any(type(k) is not str or not re.fullmatch(r"[0-9]{10}", k) for k in rows) or
            rows != sorted(set(rows)) or data != (json.dumps(rows, separators=(",", ":")) + "\n").encode("ascii")):
        raise ValueError("placebo exclusion shape")
    return frozenset(rows)


def merge_spans(spans):
    out = []
    for a, b in sorted(spans):
        if not out or a > out[-1][1] + 1:
            out.append([a, b])
        elif b > out[-1][1]:
            out[-1][1] = b
    return [tuple(s) for s in out]


def request_calendar(events, sessions, *, placebo_exclusions=(), successor_marks=(), deny=None, target_hold=None):
    """Plan intervals by subject; merge only complete surviving windows.

    Independent dated-alias splitting is done downstream for transport.
    Never subtract embargoed sessions from a candidate placebo. A placebo
    exclusion does not remove a target event or alter its position reservation.
    Optional target_hold narrows Stage B bars/quotes without narrowing embargo.
    """
    if target_hold is not None and target_hold not in HOLDS:
        raise ValueError("unsupported hold")
    _, deduped, days, closes = candidates(events, sessions)
    slots = {d: i for i, d in enumerate(sorted(sessions))}
    deny = {} if deny is None else deny
    targets, quotes, placebo = defaultdict(list), defaultdict(set), defaultdict(list)
    for n in ((target_hold,) if target_hold is not None else HOLDS):
        for row in select(deduped, closes, n):
            subject = row["fund"]
            a, b = days[row["entry"]], days[row["exit"]]
            if b <= CUTOFF and not touches_deny(deny, subject, a, b):
                targets[subject].append((slots[a], slots[b]))
                quotes[subject].update((a, b))
    gate_counts = {}
    for n, windows in admissible(events, sessions, successor_marks, deny, placebo_exclusions).items():
        gates = defaultdict(int)
        for row, gate, span in windows:
            gates[gate] += 1
            if gate == "eligible":
                a, b = span
                placebo[row["fund"]].append((slots[a], slots[b]))
        gate_counts[str(n)] = dict(sorted(gates.items()))
    return {
        "target": {k: merge_spans(v) for k, v in targets.items()},
        "placebo": {k: merge_spans(v) for k, v in placebo.items()},
        "quote_dates": quotes,
        "placebo_gate_counts": gate_counts,
    }
