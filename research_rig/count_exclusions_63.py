"""Price-blind, aggregate Plan 63 attrition from approved identity metadata only."""
from collections import Counter
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from count_63 import CUTOFF, EVENTS, EVENTS_SHA, HOLDS, candidates, counts, schedule, select
from placebo_63 import admissible
from score_63 import YEARS


PREFLIGHT = Path("/home/user/workspace/rig/data/plan63_provenance/plan63_allowlist_preflight.json")
STAGE_A = Path("/home/user/workspace/rig/data/plan63_provenance/plan63_stage_a_preflight.json")
STAGE_SHA = "39e62436a4a5162bb212a9f2bea212a06a7f3b58bf4d98f28434f48aff9a0a56"


def summarize(rows, sessions, preflight, dropped_segments=(), successor_marks=()):
    subjects = {r["cef_cik"] for r in rows}
    resolved = set(preflight["allowlist"])
    unresolved = set(preflight["unresolved_details"])
    immature = subjects - resolved - unresolved
    if (len(subjects), len(resolved), len(unresolved), len(immature)) != (229, 216, 12, 1):
        raise ValueError("preflight identity counts")
    if (resolved & unresolved or not resolved | unresolved <= subjects or
            preflight["last_complete_session"] != str(CUTOFF) or preflight["events_102_sha256"] != EVENTS_SHA):
        raise ValueError("preflight identity scope")
    r0, d0, days, closes = candidates(rows, sessions)
    mature = {n: [r for r in select(d0, closes, n) if days[r["exit"]] <= CUTOFF] for n in HOLDS}
    if any(r["fund"] in immature for pool in mature.values() for r in pool):
        raise ValueError("unclassified mature identity")
    kept = [r for r in rows if r["cef_cik"] in resolved]
    r1, d1, _, _ = candidates(kept, sessions)
    result = {"raw_census_rows_excluded_by_reason": dict(Counter(
                  "unresolved_identity" if r["fund"] in unresolved else "no_mature_window"
                  for r in r0 if r["fund"] not in resolved)), "holds": {}}
    blocked = {}
    for key, first, last in dropped_segments:
        if key not in resolved or first > last:
            raise ValueError("invalid deny segment")
        blocked.setdefault(key, []).append((date.fromisoformat(first), date.fromisoformat(last)))
    allowed = admissible(kept, sessions, successor_marks, blocked)

    def deny(f, a, b):
        return any(x <= b and a <= y for x, y in blocked.get(f, ()))

    for n in HOLDS:
        eligible = [r for r in select(d1, closes, n) if days[r["exit"]] <= CUTOFF]
        target = [r for r in eligible if not deny(r["fund"], days[r["entry"]], days[r["exit"]])]
        placebo = [r for r, reason, _ in allowed[n] if reason == "eligible"]
        result["holds"][str(n)] = {
            "target": counts(target),
            "target_by_year": {str(y): counts([r for r in target if r["day"].year == y]) for y in YEARS},
            "placebo": counts(placebo),
            "target_windows_excluded_unresolved_cik": sum(r["fund"] in unresolved for r in mature[n]),
            "target_windows_excluded_deny_collision": len(eligible) - len(target),
        }
    return result


def segment_check(original, stage, original_sha):
    pins = stage["parent_artifacts"]
    if pins["plan63_allowlist_preflight_sha256"] != original_sha or pins["events_102_sha256"] != EVENTS_SHA:
        raise ValueError("parent preflight mismatch")
    bindings = stage["resolved_segment_cusip_bindings"]
    if set(bindings) != set(original["allowlist"]):
        raise ValueError("resolved binding mismatch")
    horizon = date(2016, 1, 1), CUTOFF
    denied = [(r["kind"], r["value"].upper(), date.fromisoformat(r["from"]), date.fromisoformat(r["through"]))
              for r in stage["deny_manifest"]["records"]]
    if any(a > b for _, _, a, b in denied):
        raise ValueError("bad deny date")
    collisions, conservative, unknown = [], [], []
    for key, info in (*bindings.items(), ("PCEF", {"segments": [
        {**stage["benchmark_binding"], "bound_cusips_13d": [stage["benchmark_binding"]["cusip"]]}]})):
        for s in info["segments"]:
            a, b = date.fromisoformat(s["from"]), date.fromisoformat(s["through"])
            segment = key, s["from"], s["through"]
            cusips = [x.upper() for x in s["bound_cusips_13d"]]
            if not cusips:
                unknown.append(segment)
            for kind, value, x, y in denied:
                hit = (value == s["ticker"].upper()) if kind == "ticker" else any(
                    value == c or len(value) >= 8 and len(c) >= 8 and value[:8] == c[:8] for c in cusips)
                if hit and x <= b and a <= y:
                    collisions.append(segment)
                if hit and a <= horizon[1] and horizon[0] <= b and x <= horizon[1] and horizon[0] <= y:
                    conservative.append(segment)
    return tuple(sorted(set(collisions))), tuple(sorted(set(conservative))), tuple(sorted(set(unknown)))


if __name__ == "__main__":
    c = EVENTS.read_bytes()
    if sha256(c).hexdigest() != EVENTS_SHA:
        raise SystemExit("census hash mismatch")
    base, stage = PREFLIGHT.read_bytes(), STAGE_A.read_bytes()
    if sha256(stage).hexdigest() != STAGE_SHA:
        raise SystemExit("stage preflight hash mismatch")
    rows, sessions, original = json.loads(c), schedule(), json.loads(base)
    hits, strict, missing = segment_check(original, json.loads(stage), sha256(base).hexdigest())
    if any(x[0] == "PCEF" for x in (*hits, *strict, *missing)):
        raise SystemExit("benchmark collision or identity gap")
    print(json.dumps({"known_field_collision_segments": len(hits), "conservative_collision_segments": len(strict),
                     "unknown_cusip_segments": len(missing),
                     "known_fields": summarize(rows, sessions, original, strict),
                     "sensitivity_if_unverified_segments_dropped":
                     summarize(rows, sessions, original, set(strict) | set(missing))},
                     sort_keys=True, indent=2))
