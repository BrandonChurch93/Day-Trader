"""One approved, price-blind count of Plan 61's vendor-ex-missing-only events."""
import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import os
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
base = SimpleNamespace(**runpy.run_path(str(ROOT / "research_rig/score_61.py")))
p, s = base.p, base.s
VALIDATION = "2d8608728c82b5f422057c7ba7e03a7a77b855b1"
FREEZE = "90decb33ce679d018c5769ea37f9be891647511b"
DECISIONS = base.RUN / f"decisions.{VALIDATION}.json"
DECISIONS_SHA256 = "c132f0b50ee0731f94636c28930c341e6b365c0972c64403603b2acc29da73d9"
APPROVAL = "research_rig/COUNT_APPROVAL_62.md"
APPROVAL_RE = (rb"Approved by the lead: plan 62 ledger 205, one price-blind vendor-ex count, "
               rb"Plan 61 decisions SHA-256 " + p.SHA + rb"\.\n")
OUT = ROOT / "research_rig/COUNT_62.json"
CENT = Fraction(1, 100)
MISSING = "vendor_ex_missing"
BUCKETS = ("A", "B", "C", "D", "E", "F")
TARGET_FIELDS = {"id", "ex", "kind", "value", "payment", "available", "sources"}
DISCLOSURE_FIELDS = {"accession", "filing", "declared", "announced", "record"}


def need(ok):
    p.need(ok, "P62_COUNT_REFUSED")


def approve(commit):
    p.checkout(commit)
    _, (decisions_pin,) = p.approval_line(commit, APPROVAL, APPROVAL_RE)
    need(decisions_pin == DECISIONS_SHA256)
    p.follows(VALIDATION, commit)
    adoption, (named_adoption, pin) = p.approval_line(VALIDATION, base.VALID, base.VALID_RE)
    need(adoption == named_adoption and sha256(p.contents(adoption, base.ADOPT)).hexdigest() == pin)
    parent, (vendor, vendor_approval, freeze, frozen_pins) = p.approval_line(adoption, base.ADOPT, base.ADOPT_RE)
    need(parent == freeze == FREEZE and vendor == base.VENDOR_APPROVAL and
         sha256(p.contents(vendor, s.VALID)).hexdigest() == vendor_approval)
    manifest = p.contents(freeze, base.PINS)
    need(sha256(manifest).hexdigest() == frozen_pins)
    pins = p.parse(manifest)
    need(set(pins) == base.SOURCES)
    blobs = {n: p.file_bytes(ROOT / n, pin, 2**20) for n, pin in pins.items()}
    _, _, price, vendor_pin, vendor_index_pin = base.historical(vendor)
    return decisions_pin, blobs, price, vendor_pin, vendor_index_pin


def cohort(packet, docket):
    need(set(packet) == {"summary", "decisions"} and set(packet["decisions"]) == {e.a for e in docket})
    selected = set()
    for accession, row in packet["decisions"].items():
        need(set(row) == {"gates", "placed", "stress_placed", "liquid_placed", "earlier_placed"})
        gates = row["gates"]
        need(set(gates) == set(base.GATES + base.SHOWN_GATES) and all(type(v) is str for v in gates.values()))
        if gates["vendor_ex_agreement"] == MISSING and all(
                gates[k] == "pass" for k in base.GATES if k != "vendor_ex_agreement"):
            need(row["placed"] is False)
            selected.add(accession)
    need(len(selected) == 88)
    return selected


def classify(e, ex, cash, schedule):
    need(ex in schedule)
    same = [amount for day, amount in cash if day == ex]
    target = p.exact(e.declared)
    if any(amount >= target - CENT for amount in same):
        return "A"
    if same:
        return "B"
    near = [amount for day, amount in cash if day in schedule and abs(schedule[day] - schedule[ex]) <= 10]
    if any(amount >= target / 2 for amount in near):
        return "C"
    if near:
        return "F"
    return "D" if cash else "E"


def count(docket, days, selected, actions, vendor, cfg, meta, vendor_index_pin):
    need(actions["version"] == 1 and actions["reviewer"] == cfg["action_checker"])
    need(set(vendor) == {"version", "custodian", "endpoint", "adoption", "native_index_sha256", "records"} and
         vendor["version"] == 2 and vendor["custodian"] == cfg["custodian"] and vendor["endpoint"] == s.VENDOR_ENDPOINT
         and vendor["adoption"] == meta and vendor["native_index_sha256"] == vendor_index_pin)
    schedule = {day: i for i, day in enumerate(days)}
    buckets = Counter(dict.fromkeys(BUCKETS, 0))
    provenance = Counter({"no_structured_ex_date_provenance": 0, "unrecognized_extra_fields": 0})
    for e in docket:
        if e.a not in selected:
            continue
        stock = actions["records"][e.a]["stock"]
        disclosure = stock["target_disclosure"]
        need(stock["status"] == "complete" and stock["start"] == str(e.start) and stock["end"] == str(e.end)
             and disclosure["accession"] == e.a)
        targets = [row for row in stock["items"] if row["id"] == stock["target"]]
        need(len(targets) == 1)
        target = targets[0]
        ex = p.d(target["ex"])
        need(target["kind"] == "special" and p.money(target["value"]) == e.declared and p.cites(target["sources"])
             and e.start <= ex <= e.end)
        # The documented schema stores two URLs and an ex-date, not whether
        # either URL states it or the reviewer derived it from the record date.
        extra = set(target) - TARGET_FIELDS or set(disclosure) - DISCLOSURE_FIELDS
        provenance["unrecognized_extra_fields" if extra else "no_structured_ex_date_provenance"] += 1
        leg = vendor["records"][e.a]["stock"]
        need(leg["identity"] == stock["identity"] and leg["start"] == str(e.start) and leg["complete"] is True
             and set(leg["views"]) == {"all", "filing_all"} and all(v == stock["identity"] for v in leg["views"].values()))
        cash = []
        for row in leg["items"]:
            if row["type"] != "cash":
                continue
            date = p.d(row["ex"])
            if e.start <= date <= e.end:
                amount = p.exact(p.money(row["cash_usd"]))
                need(amount > 0 and date in schedule)
                cash.append((date, amount))
        # Recheck the original reason with Plan 61's pinned multiplicity rule.
        terms = [(p.d(row["ex"]), row["kind"], p.money(row["value"])) for row in stock["items"]
                 if row["kind"] in ("special", "ordinary")]
        need(base.crosscheck_ex(e, (terms, ex), (True, [(d, "cash", v, None) for d, v in cash])) == MISSING)
        buckets[classify(e, ex, cash, schedule)] += 1
    need(sum(buckets.values()) == sum(provenance.values()) == len(selected))
    return {"vendor_ex_missing_only": len(selected), "classes": dict(buckets),
            "verified_action_ex_date_provenance": dict(provenance)}


def measure(decisions_pin, blobs, price, vendor_pin, vendor_index_pin):
    cfg = s.config(blobs[p.CONFIG])
    days = p.calendar(blobs[n] for n in p.CALENDARS)
    need(price["docket_sha256"] == cfg["docket_sha256"])
    docket = p.events(p.file_bytes(p.DOCKET, price["docket_sha256"], 12*2**20, private=True), days, cfg)
    decisions = p.parse(p.file_bytes(DECISIONS, decisions_pin, 24*2**20, private=True))
    selected = cohort(decisions, docket)
    del decisions
    actions = p.parse(p.file_bytes(p.INPUT / "actions.json", price["actions.json"], 32*2**20, private=True))
    vendor = p.parse(p.file_bytes(s.VENDOR / s.VENDOR_NAME, vendor_pin, 64*2**20, private=True))
    meta = dict(docket_sha256=price["docket_sha256"], identities_sha256=price["identities.json"],
                bars_sha256=price["bars.json"])
    return count(docket, days, selected, actions, vendor, cfg, meta, vendor_index_pin)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-commit", required=True)
    args = parser.parse_args()
    authorization = approve(args.approval_commit)
    # Reserve the fixed output before any private data read; leave it in
    # place on failure so a repeat cannot silently start a second read.
    with os.fdopen(os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600), "wb") as dst:
        p.sync_dir(OUT.parent)
        out = p.render(measure(*authorization))
        dst.write(out)
        dst.flush()
        os.fsync(dst.fileno())
    sys.stdout.buffer.write(out)


if __name__ == "__main__":
    try:
        main()
    except (Exception, KeyboardInterrupt):
        sys.exit("P62_COUNT_REFUSED")
