"""Plan 62, with the pinned Plan 61 design and a same-date vendor-cash exception."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import runpy
import sys
from types import FunctionType, SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
b = SimpleNamespace(**runpy.run_path(str(ROOT / "research_rig/score_61.py")))
p = b.p
RUN = p.DATA / "replay_62"
QUEUE, LEDGER = 105, 205
PLAN, PINS = "research_rig/PREREG_62_special_dividend_ex_day_v2.md", "research_rig/PINNED_62.json"
ADOPT, VALID, GO = ("research_rig/" + n for n in ("ADOPTION_62.md", "APPROVAL_62.md", "GO_62.md"))
COUNT = "research_rig/COUNT_62.json"
COUNT_FILES = {"research_rig/count_62.py", "research_rig/test_count_62.py", "research_rig/COUNT_APPROVAL_62.md"}
INHERITED = b.SOURCES | {b.PINS}
SOURCES = INHERITED | COUNT_FILES | {COUNT, PLAN, "research_rig/score_62.py", "research_rig/test_62.py"}
PRIOR_FREEZE = "90decb33ce679d018c5769ea37f9be891647511b"
PRIOR_VALID = "2d8608728c82b5f422057c7ba7e03a7a77b855b1"
COUNT_APPROVAL = "183bf1d65fc7148d4da298672cb779d90f1905d1"
ADOPT_RE = (rb"Approved by the lead: plan 62 ledger 205, adopt Plan 61 validation commit " + p.UUID +
            rb", Plan 61 validation approval SHA-256 " + p.SHA + rb", freeze commit " + p.UUID +
            rb", freeze SHA-256 " + p.SHA + rb", no price acquisition\.\n")
VALID_RE = (rb"Approved by the lead: plan 62 ledger 205, validation only, adoption commit " + p.UUID +
            rb", adoption approval SHA-256 " + p.SHA + rb"\.\n")
GO_RE = (rb"Approved by the lead: plan 62 ledger 205, one scored run, validation approval commit " + p.UUID +
         rb", validation receipt SHA-256 " + p.SHA + rb"\.\n")
CLASS_A = "vendor_ex_class_a"
SHOWN = {"pass": "vendor_exact_match", CLASS_A: "vendor_class_a"}


class Stop(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Stop("P62_" + code)


def historical():
    adoption, (named_adoption, pin) = p.approval_line(PRIOR_VALID, b.VALID, b.VALID_RE)
    need(adoption == named_adoption and sha256(p.contents(adoption, b.ADOPT)).hexdigest() == pin, "HISTORY")
    parent, (vendor_validation, vendor_approval, freeze, frozen_pins) = p.approval_line(adoption, b.ADOPT, b.ADOPT_RE)
    need(parent == freeze == PRIOR_FREEZE and vendor_validation == b.VENDOR_APPROVAL and
         sha256(p.contents(vendor_validation, b.s.VALID)).hexdigest() == vendor_approval and
         sha256(p.contents(freeze, b.PINS)).hexdigest() == frozen_pins, "HISTORY")
    p.follows(vendor_validation, freeze)
    _, price_prior, price, vendor, index = b.historical(vendor_validation)
    return vendor_validation, price_prior, price, vendor, index


def authorize(commit, mode):
    p.checkout(commit)
    validation, receipt = commit, None
    if mode == "go":
        parent, (validation, receipt) = p.approval_line(commit, GO, GO_RE)
        need(parent == validation, "APPROVAL_PARENT")
    parent, (adoption, adoption_pin) = p.approval_line(validation, VALID, VALID_RE)
    need(parent == adoption, "APPROVAL_PARENT")
    parent, (prior, prior_pin, freeze, freeze_pin) = p.approval_line(adoption, ADOPT, ADOPT_RE)
    need(parent == freeze and prior == PRIOR_VALID, "ADOPTION_PARENT")
    p.follows(prior, COUNT_APPROVAL)
    p.follows(COUNT_APPROVAL, freeze)
    need(sha256(p.contents(prior, b.VALID)).hexdigest() == prior_pin, "HISTORY")
    vendor_validation, price_prior, price, vendor, index = historical()
    refs = (freeze, adoption, validation) + ((commit,) if mode == "go" else ())
    manifest = p.file_bytes(ROOT / PINS, freeze_pin, 16384)
    need(all(p.contents(r, PINS) == manifest for r in refs), "MANIFEST")
    pins = p.parse(manifest)
    need(set(pins) == SOURCES and all(map(p.is_pin, pins.values())), "MANIFEST")
    blobs = {n: p.file_bytes(ROOT / n, pin, 2**20) for n, pin in pins.items()}
    need(all(p.contents(r, n) == blob for n, blob in blobs.items() for r in refs), "MANIFEST")
    need([line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")] == [b"Status FROZEN."],
         "DRAFT_NOT_FROZEN")
    need(all(blobs[n] == p.contents(PRIOR_FREEZE, n) for n in INHERITED) and
         all(blobs[n] == p.contents(COUNT_APPROVAL, n) for n in COUNT_FILES), "INHERITED_TERMS")
    for i, name in enumerate((ADOPT, VALID, GO), 1):
        need(all(p.git("cat-file", "-e", f"{r}:{name}", allow=True).returncode != 0 for r in refs[:i]),
             "EARLY_APPROVAL")
    need(all(p.git("cat-file", "-e", f"{r}:{b.GO}", allow=True).returncode != 0 for r in (prior, *refs)),
         "PLAN61_GO_PRESENT")
    need(sha256(p.contents(adoption, ADOPT)).hexdigest() == adoption_pin and
         all(p.contents(r, ADOPT) == p.contents(adoption, ADOPT) for r in refs[1:]) and
         all(p.contents(r, VALID) == p.contents(validation, VALID) for r in refs[2:]), "APPROVAL_PIN")
    for num, path in ((LEDGER, "research_rig/TRIAL_LEDGER.md"), (QUEUE, "docs/QUEUE.md")):
        rows = [[x for x in p.contents(r, path).splitlines() if x.startswith(f"| {num} |".encode())] for r in refs]
        need(len(rows[0]) == 1 and PLAN.encode() in rows[0][0] and all(row == rows[0] for row in rows), "LEDGER_QUEUE")
    job = dict(plan=62, queue=QUEUE, ledger=LEDGER, freeze_commit=freeze, freeze_sha256=freeze_pin,
               adoption_commit=adoption, adoption_sha256=adoption_pin, validation_commit=validation,
               plan61_validation_commit=prior, plan61_validation_sha256=prior_pin, count_approval_commit=COUNT_APPROVAL,
               plan60_validation_commit=vendor_validation, price_adoption_source=price_prior,
               vendor_actions_sha256=vendor, vendor_index_sha256=index, adopted_price=price)
    if mode == "go":
        job.update(go_commit=commit, validation_receipt_sha256=receipt)
    return blobs, job


def bind(fn, **bindings):
    """Reuse the pinned function body with only the specified dependencies changed."""
    return FunctionType(fn.__code__, fn.__globals__ | bindings, fn.__name__, fn.__defaults__, fn.__closure__)


def vendor_status(e, act, vendor_leg):
    status = b.crosscheck_ex(e, act, vendor_leg)
    if status == "vendor_ex_missing":
        _, ex = act
        floor = p.exact(e.declared) - Fraction(1, 100)
        if e.start <= ex <= e.end and any(
                day == ex and kind == "cash" and amount >= floor for day, kind, amount, _ in vendor_leg[1]):
            return CLASS_A
    return status


def prepare(*args):
    admitted = set()

    def crosscheck(e, act, vendor_leg):
        status = vendor_status(e, act, vendor_leg)
        if status == CLASS_A:
            admitted.add(e.a)
            return "pass"
        return status

    decisions, placed = bind(b.prepare, crosscheck_ex=crosscheck)(*args)
    for accession in admitted:
        decisions[accession]["gates"]["vendor_ex_agreement"] = CLASS_A
    return decisions, placed


def summary(decisions):
    counts = b.summary(decisions)
    counts["placed_by_vendor_ex_status"] = {label: sum(
        d["placed"] and d["gates"]["vendor_ex_agreement"] == status for d in decisions.values())
        for status, label in SHOWN.items()}
    need(sum(counts["placed_by_vendor_ex_status"].values()) == counts["placed_pairs"], "VENDOR_SPLIT")
    return counts


def score(placed, decisions, counts, cfg, years):
    shown = {}

    def marks(rows, ex_years):
        subsets = {status: [] for status in SHOWN}
        for _, accession, value in rows:
            subsets[decisions[accession]["gates"]["vendor_ex_agreement"]].append(value)
        for status, values in subsets.items():
            label = SHOWN[status]
            need(len(values) == counts["placed_by_vendor_ex_status"][label], "VENDOR_SPLIT")
            shown[label] = dict(n=len(values), paired_mean=p.avg(values))
        return b.marks(rows, ex_years)

    result = bind(b.score, marks=marks)(placed, counts, cfg, years)
    result.update(plan=62, ledger=LEDGER, queue=QUEUE)
    result["shown_only"].update(shown)
    return result


def execute(commit, mode):
    blobs, job = authorize(commit, mode)
    b.run_dir(RUN)
    if mode == "validate":
        expected = {f"{key}.{commit}.json" for key in ("decisions", "validation")}
        need({f.name for f in RUN.iterdir()} <= expected, "RUN_FOLDER_NOT_EMPTY")
    p.unused(RUN)
    cfg = b.s.config(blobs[p.CONFIG])
    p.resources(cfg)
    years = b.check_proof(blobs)
    q, days, C, verified, vendor, records = b.load(blobs, job, cfg)
    decisions, placed = prepare(q, days, C, verified, vendor, records, cfg)
    del records, vendor
    counts = summary(decisions)
    validation = job["validation_commit"]
    wire = p.render(dict(summary=counts, decisions=decisions))
    dfile, vfile = (RUN / f"{key}.{validation}.json" for key in ("decisions", "validation"))
    expected = p.render(dict(status="validated_no_returns", decisions_sha256=sha256(wire).hexdigest(),
                             **{k: v for k, v in job.items() if k not in ("go_commit", "validation_receipt_sha256")}))
    if mode == "validate":
        p.put_or_check(dfile, wire, 24*2**20)
        p.put_or_check(vfile, expected, 32768)
        sys.stdout.buffer.write(p.render(counts) + b"P62_VALIDATED\n")
        return
    pin = sha256(expected).hexdigest()
    need(pin == job["validation_receipt_sha256"] and p.file_bytes(vfile, pin, 32768, private=True) == expected and
         p.file_bytes(dfile, sha256(wire).hexdigest(), 24*2**20, private=True) == wire, "VALIDATION_RECEIPT")
    need(authorize(commit, "go") == (blobs, job), "APPROVAL_CHANGED")
    job["started_utc"] = datetime.now(timezone.utc).isoformat()
    p.once(RUN, job, lambda: score(placed, decisions, counts, cfg, years))
    print("P62_SCORED_ONCE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-inputs", action="store_true")
    modes.add_argument("--go", action="store_true")
    parser.add_argument("--approval-commit", required=True)
    args = parser.parse_args()
    try:
        execute(args.approval_commit, "go" if args.go else "validate")
    except (Stop, b.Stop, p.Refused) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (Exception, KeyboardInterrupt):
        print("P62_REFUSED", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
