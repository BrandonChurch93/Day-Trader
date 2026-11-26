"""Custodian-only, once-only Plan 63 placebo runner. No target packet path."""
from base64 import b64decode
from datetime import date
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

from count_63 import CUTOFF, EVENTS, EVENTS_SHA, HOLDS, candidates, intersects_target, schedule, select
from placebo_63 import Leg, admissible, measure, placebo_embargo, touches_deny
from preflight_63 import PLACEBO_EXCLUSIONS_NAME, PLACEBO_EXCLUSIONS_SHA, parse_placebo_exclusions
from score_63 import Stop


RIG = Path(__file__).resolve().parent
PACKET = Path("/home/user/workspace/rig/data/plan63_inputs/placebo")
APPROVAL = "research_rig/PLACEBO_APPROVE_63.json"
PROJECT_APPROVAL = "research_rig/PLACEBO_PROJECT_APPROVE_63.json"
FREEZE = "research_rig/PLACEBO_FREEZE_63.json"
REVIEW = "research_rig/PLACEBO_AUDIT_63.md"
ACQUISITION_APPROVAL = "research_rig/ACQUISITION_APPROVE_63.md"
WINDOWS = "scope.json"
EVIDENCE = "evidence.json"
FIELD_INDEX = "field_index.json"
PREFLIGHT = "scope_preflight.json"
TRANSPORT = "bar_transport.json"
LEGS = "legs.json"
REMEDIATION = "stage_a_custody_manifest_v2.json"
PROJECTION_RECEIPT = "projection_receipt.json"
CLAIM = "attempt.once"
PENDING = "report.pending"
REPORT = "report.json"
PINS = {"count_63.py", "placebo_63.py", "placebo_run_63.py", "placebo_project_63.py",
        "placebo_native_63.py", "preflight_63.py", "score_63.py",
        "calendar_25.json", "calendar_26.json", "calendar_50.json"}
SHA = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
NUMBER = re.compile(r"(?:0|[1-9][0-9]{0,11})(?:(?:\.[0-9]{1,12})?(?:[Ee][+-]?[0-9]{1,2})?|/[1-9][0-9]{0,11})\Z")
MAX = 12_000_000
OUTPUT_PINS = ("scope_sha256", "evidence_sha256", "preflight_sha256", "transport_sha256",
               "field_index_sha256", "legs_sha256")


def need(ok, code):
    if not ok:
        raise Stop(code)


def hashed(raw, pin):
    need(type(pin) is str and SHA.fullmatch(pin) and sha256(raw).hexdigest() == pin, "PIN")
    return raw


def git(*args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(["git", "--no-replace-objects", *args], cwd=RIG.parent, env=env,
                          capture_output=True, check=True).stdout


def unique(pairs):
    out = {}
    for k, v in pairs:
        need(k not in out, "JSON_DUPLICATE")
        out[k] = v
    return out


def decode(blob):
    return json.loads(blob, object_pairs_hook=unique)


def require_checkout(commit):
    need(COMMIT.fullmatch(commit), "APPROVAL")
    need(git("rev-parse", "HEAD").strip().decode("ascii") == commit, "APPROVAL_CHECKOUT")


def sole_add(commit, path):
    head, *parents = git("rev-list", "--parents", "-n1", commit).decode("ascii").split()
    need(head == commit and len(parents) == 1, "APPROVAL_PARENT")
    parent = parents[0]
    diff = git("diff-tree", "--no-commit-id", "--name-status", "-r", parent, commit)
    need(diff == f"A\t{path}\n".encode("ascii"), "APPROVAL_SOLE_ADD")
    return parent


def projection_lineage(commit):
    freeze = sole_add(commit, PROJECT_APPROVAL)
    raw = git("show", f"{commit}:{PROJECT_APPROVAL}")
    a = decode(raw)
    input_keys = ("remediated_capture_sha256", "placebo_exclusions_sha256")
    exact(a, "purpose approved_by freeze_commit freeze_sha256 " + " ".join(input_keys))
    need(a["purpose"] == "plan63_placebo_projection_only" and a["approved_by"] == "lead"
         and a["freeze_commit"] == freeze, "PROJECT_APPROVAL")
    frozen = decode(hashed(git("show", f"{freeze}:{FREEZE}"), a["freeze_sha256"]))
    exact(frozen, "status custodian_uid source_pins auditor_review_sha256 acquisition_approval_sha256 "
          + " ".join(input_keys))
    need(frozen["status"] == "placebo_source_frozen_before_hold_ruling" and type(frozen["custodian_uid"]) is int
         and frozen["custodian_uid"] == os.geteuid() and set(frozen["source_pins"]) == PINS, "APPROVAL")
    need(all(valid_pin(a[k]) and a[k] == frozen[k] for k in input_keys),
         "APPROVAL_PINS")
    need(a["placebo_exclusions_sha256"] == PLACEBO_EXCLUSIONS_SHA, "PLACEBO_EXCLUSIONS_PIN")
    for name, pin in frozen["source_pins"].items():
        hashed((RIG / name).read_bytes(), pin)
        hashed(git("show", f"{freeze}:research_rig/{name}"), pin)
    hashed(git("show", f"{freeze}:{REVIEW}"), frozen["auditor_review_sha256"])
    hashed(git("show", f"{freeze}:{ACQUISITION_APPROVAL}"), frozen["acquisition_approval_sha256"])
    return frozen, raw


def approved_project(commit):
    require_checkout(commit)
    return projection_lineage(commit)[0]


def approved(commit):
    require_checkout(commit)
    project_commit = sole_add(commit, APPROVAL)
    frozen, projection_auth = projection_lineage(project_commit)
    a = decode(git("show", f"{commit}:{APPROVAL}"))
    exact(a, "purpose approved_by project_commit project_approval_sha256 projection_receipt_sha256 "
          + " ".join(OUTPUT_PINS))
    need(a["purpose"] == "plan63_single_placebo_dispersion" and a["approved_by"] == "lead" and
         a["project_commit"] == project_commit and valid_pin(a["projection_receipt_sha256"]) and
         all(valid_pin(a[k]) for k in OUTPUT_PINS), "MEASUREMENT_APPROVAL")
    hashed(projection_auth, a["project_approval_sha256"])
    return {**frozen, **a}


def check_projection_receipt(blob, auth):
    receipt = decode(hashed(blob, auth["projection_receipt_sha256"]))
    exact(receipt, "schema project_commit remediated_capture_sha256 placebo_exclusions_sha256 "
          + " ".join(OUTPUT_PINS))
    need(receipt["schema"] == "plan63-audited-projection-receipt-v1" and all(receipt[k] == auth[k] for k in
         ("project_commit", "remediated_capture_sha256", "placebo_exclusions_sha256", *OUTPUT_PINS)),
         "PROJECTION_RECEIPT")


def file_in(folder, name):
    fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=folder)
    with os.fdopen(fd, "rb") as f:
        s = os.fstat(fd)
        need(stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode) == 0o600 and s.st_uid == os.geteuid()
             and s.st_nlink == 1 and 0 < s.st_size <= MAX, "FILE_POLICY")
        blob = f.read(MAX + 1)
        need(len(blob) == s.st_size, "FILE_POLICY")
        return blob


def check_remediated_capture(auth):
    folder = os.open(PACKET.parent, os.O_DIRECTORY | os.O_RDONLY | os.O_NOFOLLOW)
    try:
        s = os.fstat(folder)
        need(stat.S_IMODE(s.st_mode) == 0o700 and s.st_uid == auth["custodian_uid"], "FILE_POLICY")
        hashed(file_in(folder, REMEDIATION), auth["remediated_capture_sha256"])
    finally:
        os.close(folder)


def exclusive(folder, name, blob):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=folder)
    with os.fdopen(fd, "wb") as f:
        f.write(blob)
        f.flush()
        os.fsync(f.fileno())
    os.fsync(folder)


def exact(obj, fields):
    need(type(obj) is dict and set(obj) == set(fields.split()), "ROW_SHAPE")


def stamp(d):
    need(type(d) is str, "DATE_SHAPE")
    result = date.fromisoformat(d)
    need(str(result) == d, "DATE_SHAPE")
    return result


def money(s):
    need(type(s) is str and NUMBER.fullmatch(s), "NUMERIC_SHAPE")
    return Fraction(s)


def valid_pin(s):
    return type(s) is str and SHA.fullmatch(s) is not None


class Proofs:
    def __init__(self, rows):
        need(type(rows) is list, "ASSURANCE")
        self.rows = {}
        self.used = set()
        for row in rows:
            exact(row, "sha256 role binding bytes_b64")
            need(type(row["bytes_b64"]) is str and type(row["binding"]) is list and
                 all(type(k) is str for k in row["binding"]), "ASSURANCE")
            raw = b64decode(row["bytes_b64"], validate=True)
            pin = row["sha256"]
            need(bool(raw) and valid_pin(pin) and sha256(raw).hexdigest() == pin, "ASSURANCE_BYTES")
            role, binding = row["role"], tuple(row["binding"])
            need(role in ("identity", "alias", "successor", "basis", "action_coverage", "action", "missing_endpoint",
                          "excluded", "deny", "cusip_unverified"),
                 "ASSURANCE")
            # Bind role and asserted identifiers/dates to the authenticated
            # receipt content, not only the caller-supplied index wrapper.
            receipt = decode(raw)
            exact(receipt, "schema role binding support details")
            need(receipt["schema"] == "plan63-reviewed-proof-v1" and receipt["role"] == role and
                 receipt["binding"] == list(binding) and type(receipt["support"]) is list and receipt["support"],
                 "ASSURANCE_RECEIPT")
            sources, source_claims = set(), []
            for support in receipt["support"]:
                exact(support, "source_kind sha256 bytes_b64")
                kind = support["source_kind"]
                need(kind in ("issuer_primary", "sec_primary", "exchange_primary", "vendor_native",
                              "custodian_transport", "independent_reconciliation"), "ASSURANCE_SOURCE")
                sources.add(kind)
                content = decode(hashed(b64decode(support["bytes_b64"], validate=True), support["sha256"]))
                exact(content, "schema source_kind role binding excerpt_sha256 excerpt_b64 claim")
                need(content["schema"] == "plan63-bound-source-excerpt-v1" and content["source_kind"] == kind
                     and content["role"] == role and content["binding"] == list(binding), "ASSURANCE_SOURCE_BINDING")
                need(bool(hashed(b64decode(content["excerpt_b64"], validate=True), content["excerpt_sha256"])),
                     "ASSURANCE_SOURCE_CONTENT")
                source_claims.append((kind, content["claim"]))
            if role in ("basis", "action_coverage", "action"):
                need("vendor_native" in sources and "independent_reconciliation" in sources, "ASSURANCE_SOURCE")
            if role in ("identity", "alias", "successor", "action", "deny", "cusip_unverified"):
                need(sources.intersection({"issuer_primary", "sec_primary", "exchange_primary"}), "ASSURANCE_SOURCE")
            details = receipt["details"]
            if role == "action_coverage":
                exact(details, "action_sha256s")
                pins = details["action_sha256s"]
                need(type(pins) is list and pins == sorted(set(pins)) and all(map(valid_pin, pins)), "ASSURANCE_CONTENT")
            elif role == "action":
                exact(details, "canonical_amount")
                need(type(details["canonical_amount"]) is str and NUMBER.fullmatch(details["canonical_amount"]),
                     "ASSURANCE_CONTENT")
                need(all(c == {"canonical_amount": details["canonical_amount"]} for _, c in source_claims),
                     "ACTION_SOURCE_DISAGREEMENT")
            else:
                exact(details, "")
            if role != "action":
                need(all(c == details for _, c in source_claims), "ASSURANCE_SOURCE_DISAGREEMENT")
            key = pin, role, binding
            need(key not in self.rows, "ASSURANCE")
            self.rows[key] = details

    def require(self, pin, role, *binding):
        k = pin, role, tuple(str(x) for x in binding)
        need(k in self.rows, "ASSURANCE")
        self.used.add(k)
        return self.rows[k]

    def complete(self):
        need(self.used == self.rows.keys(), "ASSURANCE_EXTRA")


def canonical_identities(source, census, proofs, cusip_unverified):
    """Enforce a full one-issue-per-CIK mapping, injective across the universe.

    A transfer/reused canonical ID or unresolved class requires a new reviewed
    mapping design, not silent splitting, matching or skipping.
    """
    need(type(source) is list, "IDENTITY")
    expected = {"PCEF", *(r["cef_cik"] for r in census)}
    by_subject, by_issue, seen_unverified = {}, {}, set()
    for row in source:
        exact(row, "subject_key stable_security_id identity_sha256 dated_aliases")
        subject, issue = row["subject_key"], row["stable_security_id"]
        need(subject in expected and subject not in by_subject and type(issue) is str and
             0 < len(issue) <= 120 and issue not in by_issue and valid_pin(row["identity_sha256"])
             and type(row["dated_aliases"]) is list and row["dated_aliases"], "IDENTITY")
        proofs.require(row["identity_sha256"], "identity", subject, issue)
        last_end = date.min
        spans = []
        for a in row["dated_aliases"]:
            exact(a, "alias from_session through_session cusips evidence_sha256")
            start, end = stamp(a["from_session"]), stamp(a["through_session"])
            symbol = a["alias"]
            need(last_end < start <= end and type(symbol) is str and
                 0 < len(symbol) <= 120 and valid_pin(a["evidence_sha256"]), "IDENTITY")
            cusips = a["cusips"]
            need(type(cusips) is list and cusips == sorted(set(cusips)) and
                 all(type(c) is str and re.fullmatch(r"[A-Z0-9*@#]{9}", c) for c in cusips), "CUSIP")
            if not cusips:
                k = subject, symbol, start, end
                need(subject != "PCEF" and k in cusip_unverified, "CUSIP_UNVERIFIED")
                proofs.require(cusip_unverified[k], "cusip_unverified", *k)
                seen_unverified.add(k)
            proofs.require(a["evidence_sha256"], "alias", subject, issue, symbol, start, end, *cusips)
            spans.append((symbol, start, end, cusips))
            last_end = end
        by_subject[subject] = issue, row["identity_sha256"], spans
        by_issue[issue] = subject
    need(set(by_subject) == expected, "IDENTITY")
    need(seen_unverified == cusip_unverified.keys(), "CUSIP_UNVERIFIED")
    globally = {}
    for _, _, spans in by_subject.values():
        for symbol, start, end, cusips in spans:
            for identifier in (("ticker", symbol.upper()), *(("cusip", c) for c in cusips)):
                overlaps = globally.setdefault(identifier, [])
                need(all(e < start or end < s for s, e in overlaps), "ALIAS_COLLISION")
                overlaps.append((start, end))
    return by_subject, by_issue


def approved_scope(manifest, census, sessions, proofs, preflight, placebo_exclusions=()):
    exact(manifest, "schema identity_map successor_marks scopes")
    need(manifest["schema"] == "plan63-placebo-projection-v1", "ROW_SHAPE")
    need(type(manifest["successor_marks"]) is list and type(manifest["scopes"]) is list, "ROW_SHAPE")
    exact(preflight, "schema excluded deny successor_marks cusip_unverified")
    need(preflight["schema"] == "plan63-approved-scope-preflight-v1" and
         all(type(preflight[k]) is list for k in ("excluded", "deny", "successor_marks", "cusip_unverified")), "PREFLIGHT")
    need(preflight["successor_marks"] == manifest["successor_marks"], "SUCCESSOR_COMPLETENESS")
    dropped = {}
    all_subjects = {r["cef_cik"] for r in census}
    for row in preflight["excluded"]:
        exact(row, "subject_key reason evidence_sha256")
        key, reason = row["subject_key"], row["reason"]
        need(key in all_subjects and key not in dropped and reason in ("unresolved_identity", "outside_maturity"),
             "EXCLUDED_IDENTITY")
        proofs.require(row["evidence_sha256"], "excluded", key, reason)
        dropped[key] = reason
    _, d0, days, closes = candidates(census, sessions)
    intended_mature = {r["fund"] for n in HOLDS for r in select(d0, closes, n) if days[r["exit"]] <= CUTOFF}
    need(all((key in intended_mature) == (reason == "unresolved_identity") for key, reason in dropped.items()),
         "EXCLUSION_MATURITY")
    retained = [r for r in census if r["cef_cik"] not in dropped]
    need(set(placebo_exclusions) <= all_subjects - dropped.keys(), "PLACEBO_EXCLUSION_COVERAGE")
    cusip_unverified = {}
    for row in preflight["cusip_unverified"]:
        exact(row, "subject_key alias from_session through_session evidence_sha256")
        a, b = stamp(row["from_session"]), stamp(row["through_session"])
        key = row["subject_key"], row["alias"], a, b
        need(a <= b and key not in cusip_unverified and valid_pin(row["evidence_sha256"]), "CUSIP_UNVERIFIED")
        cusip_unverified[key] = row["evidence_sha256"]
    by_subject, by_issue = canonical_identities(manifest["identity_map"], retained, proofs, cusip_unverified)
    excluded_tokens, deny = set(), {}
    for row in preflight["deny"]:
        exact(row, "subject_key kind identifier from_session through_session evidence_sha256")
        key, kind, ident = row["subject_key"], row["kind"], row["identifier"]
        a, b = stamp(row["from_session"]), stamp(row["through_session"])
        token = key, kind, ident, a, b
        need(key in dropped and kind in ("ticker", "cusip") and
             type(ident) is str and 0 < len(ident) <= 120 and ident == ident.upper() and
             a <= b and token not in excluded_tokens, "DENY")
        need(kind != "cusip" or re.fullmatch(r"[A-Z0-9*@#]{8,9}", ident), "DENY")
        proofs.require(row["evidence_sha256"], "deny", *token)
        excluded_tokens.add(token)
    for key, (_, _, alleles) in by_subject.items():
        for sym, a, b, cusips in alleles:
            if any(x <= b and a <= y and (ident == sym.upper() if kind == "ticker" else
                   any(ident == c or ident[:8] == c[:8] for c in cusips))
                   for _, kind, ident, x, y in excluded_tokens):
                need(key != "PCEF", "BENCHMARK_DENY_COLLISION")
                deny.setdefault(key, []).append((a, b))
    successors = []
    successor_keys = set()
    for s in manifest["successor_marks"]:
        exact(s, "stable_security_id valuation_day evidence_sha256")
        issue, day = s["stable_security_id"], stamp(s["valuation_day"])
        need(type(issue) is str and issue not in ("", by_subject["PCEF"][0]) and day in sessions
             and (issue, day) not in successor_keys and valid_pin(s["evidence_sha256"]), "SUCCESSOR_MARK")
        proofs.require(s["evidence_sha256"], "successor", issue, day)
        successor_keys.add((issue, day))
        if issue in by_issue:
            successors.append((by_issue[issue], day))
    expected = {(key, *span) for rows in admissible(retained, sessions, successors, deny, placebo_exclusions).values()
                for row, reason, span in rows if reason == "eligible" for key in (row["fund"], "PCEF")}
    got = {}
    for o in manifest["scopes"]:
        exact(o, "subject_key start end status stable_security_id entry_alias exit_alias identity_sha256 "
                 "split_basis_sha256 action_coverage_sha256 missing_endpoint_sha256")
        scope = o["subject_key"], stamp(o["start"]), stamp(o["end"])
        need(scope in expected and scope not in got, "SCOPE")
        need(o["status"] in ("present", "missing_endpoint"), "ROW_SHAPE")
        issue, identity_pin, aliases = by_subject[scope[0]]
        need((o["stable_security_id"], o["identity_sha256"]) == (issue, identity_pin), "IDENTITY")
        for k, day in (("entry_alias", scope[1]), ("exit_alias", scope[2])):
            alias = next((a for a, x, y, _ in aliases if x <= day <= y and not touches_deny(deny, scope[0], day, day)), None)
            need(o[k] == alias and (alias is not None or o["status"] == "missing_endpoint"), "IDENTITY")
        if o["status"] == "present":
            need(o["missing_endpoint_sha256"] is None, "ASSURANCE")
            proofs.require(o["split_basis_sha256"], "basis", issue, scope[1], scope[2])
            proofs.require(o["action_coverage_sha256"], "action_coverage", issue, scope[1], scope[2])
        else:
            need(o["split_basis_sha256"] is None and o["action_coverage_sha256"] is None, "ASSURANCE")
            proofs.require(o["missing_endpoint_sha256"], "missing_endpoint", issue, scope[1], scope[2])
        got[scope] = o
    need(set(got) == expected, "SCOPE")
    return got, tuple(successors), retained, deny


def check_transport_embargo(transport, retained, sessions, successors, deny, placebo_exclusions):
    """Reject any forbidden stream from metadata before any archive/price opens."""
    exact(transport, "schema streams")
    need(transport["schema"] == "plan63-placebo-bar-transport-v1" and type(transport["streams"]) is list,
         "NATIVE_INDEX")
    raw, _, days, _ = candidates(retained, sessions)
    subjects = {r["fund"] for r in raw}
    blocked = placebo_embargo(raw, days, sessions, successors)
    for stream in transport["streams"]:
        exact(stream, "partition subject_key stable_security_id alias first last feed view pages")
        key = stream["subject_key"]
        a, b = stamp(stream["first"]), stamp(stream["last"])
        need(a <= b, "NATIVE_STREAM")
        if key == "PCEF":
            need(stream["partition"] == "benchmark", "NATIVE_PARTITION")
        else:
            need(stream["partition"] == "placebo" and key in subjects and key not in placebo_exclusions,
                 "NATIVE_PLACEBO_EXCLUDED")
            need(not intersects_target(blocked, key, (a, b)) and not touches_deny(deny, key, a, b),
                 "NATIVE_EMBARGO")


def read_projection(payload, allowed, proofs):
    exact(payload, "schema legs")
    need(payload["schema"] == "plan63-placebo-prices-v1" and type(payload["legs"]) is list, "ROW_SHAPE")
    legs = {scope: None for scope, m in allowed.items() if m["status"] != "present"}
    for o in payload["legs"]:
        exact(o, "subject_key start end stable_security_id entry exit actions")
        key, start, end = o["subject_key"], stamp(o["start"]), stamp(o["end"])
        scope = key, start, end
        need(scope in allowed and scope not in legs, "SCOPE")
        m = allowed[scope]
        need(m["status"] == "present" and o["stable_security_id"] == m["stable_security_id"], "IDENTITY")
        prices = []
        for k, need_day in (("entry", start), ("exit", end)):
            bar = o[k]
            exact(bar, "session alias feed view volume raw_close")
            need(stamp(bar["session"]) == need_day and bar["alias"] == m[f"{k}_alias"] and
                 bar["feed"] == "sip" and bar["view"] == "raw" and type(bar["volume"]) is int
                 and bar["volume"] > 0, "BAR")
            prices.append(money(bar["raw_close"]))
        seen = set()
        actions = []
        need(type(o["actions"]) is list, "ACTION")
        for event in o["actions"]:
            exact(event, "economic_action_sha256 ex_date kind amount")
            proof = event["economic_action_sha256"]
            need(valid_pin(proof) and proof not in seen, "ACTION")
            seen.add(proof)
            d, kind, qty = stamp(event["ex_date"]), event["kind"], money(event["amount"])
            action_receipt = proofs.require(proof, "action", m["stable_security_id"], d, kind)
            need(action_receipt["canonical_amount"] == event["amount"], "ACTION_AMOUNT")
            actions.append((d, kind, qty))
        receipt = proofs.require(m["action_coverage_sha256"], "action_coverage", m["stable_security_id"], start, end)
        need(seen == set(receipt["action_sha256s"]), "ACTION_COMPLETENESS")
        legs[scope] = Leg(key, start, end, *prices, True, True, tuple(actions))
    need(set(legs) == set(allowed), "SCOPE")
    return legs


def run(commit):
    auth = approved(commit)
    census = decode(hashed(EVENTS.read_bytes(), EVENTS_SHA))
    sessions = schedule()
    folder = os.open(PACKET, os.O_DIRECTORY | os.O_RDONLY | os.O_NOFOLLOW)
    try:
        s = os.fstat(folder)
        need(stat.S_IMODE(s.st_mode) == 0o700 and s.st_uid == auth["custodian_uid"], "FILE_POLICY")
        v = os.fstatvfs(folder)
        need(v.f_bavail * v.f_frsize >= 2_684_420_096, "DISK_GATE")  # 2.5 GiB plus 64 KiB output reserve
        for name in (PENDING, REPORT):
            try:
                os.stat(name, dir_fd=folder, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise Stop("ALREADY_PUBLISHED")
        check_remediated_capture(auth)
        check_projection_receipt(file_in(folder, PROJECTION_RECEIPT), auth)
        manifest = decode(hashed(file_in(folder, WINDOWS), auth["scope_sha256"]))
        preflight = decode(hashed(file_in(folder, PREFLIGHT), auth["preflight_sha256"]))
        evidence = Proofs(decode(hashed(file_in(folder, EVIDENCE), auth["evidence_sha256"])))
        hashed(file_in(folder, FIELD_INDEX), auth["field_index_sha256"])
        transport = decode(hashed(file_in(folder, TRANSPORT), auth["transport_sha256"]))
        purged = parse_placebo_exclusions(file_in(folder, PLACEBO_EXCLUSIONS_NAME), auth["placebo_exclusions_sha256"])
        allowed, successors, retained, deny = approved_scope(manifest, census, sessions, evidence, preflight, purged)
        check_transport_embargo(transport, retained, sessions, successors, deny, purged)
        # Persistently reserve the sole attempt before opening the price slice.
        # No retry after any failure past this point. Never publish a partial report.
        exclusive(folder, CLAIM, (commit + "\n").encode("ascii"))
        legs = read_projection(decode(hashed(file_in(folder, LEGS), auth["legs_sha256"])), allowed, evidence)
        evidence.complete()
        out = measure(retained, sessions, lambda k, a, b: legs[(k, a, b)], successors, deny, purged)
        exclusive(folder, PENDING, (json.dumps(out, sort_keys=True, allow_nan=False) + "\n").encode("ascii"))
        os.link(PENDING, REPORT, src_dir_fd=folder, dst_dir_fd=folder, follow_symlinks=False)
        os.unlink(PENDING, dir_fd=folder)
        os.fsync(folder)
    finally:
        os.close(folder)


if __name__ == "__main__":
    try:
        need(len(sys.argv) == 2, "ARGS")
        run(sys.argv[1])
    except (Exception, KeyboardInterrupt):
        # No underlying exception parameters, data rows, stdout or tracebacks.
        sys.exit(2)
