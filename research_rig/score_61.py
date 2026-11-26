"""Replay 61. Offline adopted inputs, counts-only validation, separate once-only score."""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
from math import ceil
import os
from pathlib import Path
import re
import runpy
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent


def module(name):
    return SimpleNamespace(**runpy.run_path(str(ROOT / "research_rig" / name)))


s = module("score_60.py")
p = s.p
blind = module("count_61.py")
RUN = p.DATA / "replay_61"
LEDGER, QUEUE = 203, 105
PLAN = "research_rig/PREREG_61_special_dividend_ex_day.md"
COUNT = "research_rig/COUNT_61.json"
PROOF = "research_rig/POWER_61.json"
PLACEBO = "research_rig/PLACEBO_61.json"
LIQUID_PLACEBO = "research_rig/PLACEBO_LIQUID_61.json"
PINS = "research_rig/PINNED_61.json"
ADOPT, VALID, GO = ("research_rig/" + f for f in ("ADOPTION_61.md", "APPROVAL_61.md", "GO_61.md"))
VENDOR_APPROVAL = "8babbf959c0133549c8961733941ebab35875872"
INHERITED = {p.ENGINE, p.PROVENANCE, p.BASIS, *p.CALENDARS, s.ADAPTER,
             "research_rig/score_43.py", "research_rig/score_60.py",
             "research_rig/test_43.py", "research_rig/test_60.py"}
SOURCES = INHERITED | {PLAN, COUNT, PROOF, PLACEBO, LIQUID_PLACEBO, p.CONFIG, "research_rig/count_61.py",
                      "research_rig/power_61.py", "research_rig/placebo_61.py",
                      "research_rig/score_61.py", "research_rig/test_61.py"}
ADOPT_RE = (rb"Approved by the lead: plan 61 ledger 203, adopt Plan 60 validation commit " + p.UUID +
            rb", Plan 60 validation approval SHA-256 " + p.SHA + rb", freeze commit " + p.UUID +
            rb", freeze SHA-256 " + p.SHA + rb", no price acquisition\.\n")
VALID_RE = (rb"Approved by the lead: plan 61 ledger 203, validation only, adoption commit " + p.UUID +
            rb", adoption approval SHA-256 " + p.SHA + rb"\.\n")
GO_RE = (rb"Approved by the lead: plan 61 ledger 203, one scored run, validation approval commit " + p.UUID +
         rb", validation receipt SHA-256 " + p.SHA + rb"\.\n")
ARMS = ("stock", "IWM")
TAX = Fraction(24, 100)
WINSOR_CAP = Fraction(600, 10_000)
PAIR_FLOOR, YEAR_FLOOR, T_FLOOR, TRIM_PERCENT, LIQUIDITY_FLOOR = 250, 7, 2, 1, 1_000_000
GATES = ("verified_ex_clock", "vendor_ex_agreement", "stock_bars", "iwm_bars", "stock_padding_volume", "stock_padding_dollar_volume",
         "stock_clock_volume", "iwm_clock_volume", "stock_vendor_basis", "iwm_vendor_basis",
         "stock_whole_share", "iwm_whole_share", "stock_integral_split", "iwm_integral_split")
SHOWN_GATES = ("liquid_padding_dollar_volume", "earlier_clock",
         "earlier_stock_clock_volume", "earlier_iwm_clock_volume",
         "earlier_stock_whole_share", "earlier_iwm_whole_share", "earlier_stock_integral_split", "earlier_iwm_integral_split",
         "stress_stock_whole_share", "stress_iwm_whole_share", "stress_stock_integral_split",
         "stress_iwm_integral_split")


class Stop(Exception):
    pass


def need(value, code):
    if not value:
        raise Stop("P61_" + code)


def historical(prior):
    historic_adopt, (named_adoption, adopt_pin, vp, vi) = p.approval_line(prior, s.VALID, s.VALID_RE)
    need(historic_adopt == named_adoption and sha256(p.contents(historic_adopt, s.ADOPT)).hexdigest() == adopt_pin,
         "HISTORICAL_APPROVAL")
    old_freeze, (price_prior, pp, plan60_freeze, fp) = p.approval_line(historic_adopt, s.ADOPT, s.ADOPT_RE)
    need(old_freeze == plan60_freeze, "HISTORICAL_APPROVAL")
    need(sha256(p.contents(plan60_freeze, s.PINS)).hexdigest() == fp, "HISTORICAL_APPROVAL")
    need(price_prior == p.PREVIOUS_VALIDATION and sha256(p.contents(price_prior, p.APPROVAL)).hexdigest() == pp,
         "HISTORICAL_APPROVAL")
    price_parent, (acq, ap, ids, bars, acts, fetch, native, transport, rebuild) = p.approval_line(
        price_prior, p.APPROVAL, p.APPROVAL_RE)
    p.follows(acq, price_parent)
    acq_parent, (freeze43, fp43, docket, collector) = p.approval_line(acq, p.ACQUISITION, p.ACQUISITION_RE)
    p.follows(freeze43, acq_parent)
    need(collector == p.COLLECTOR_SHA256 and (ids, acts, bars) == (blind.IDS, blind.ACTIONS, blind.BARS),
         "HISTORICAL_PACKET")
    price = dict(acquisition_commit=acq, freeze_commit=freeze43, freeze_sha256=fp43, docket_sha256=docket,
                 collector_sha256=collector, acquisition_receipt_sha256=ap, fetch_start_sha256=fetch,
                 native_index_sha256=native, transport_index_sha256=transport, offline_rebuild_sha256=rebuild,
                 **dict(zip(p.PACKETS, (ids, bars, acts))))
    return plan60_freeze, price_prior, price, vp, vi


def authorize(commit, mode):
    p.checkout(commit)
    validation, receipt = commit, None
    if mode == "go":
        parent, (validation, receipt) = p.approval_line(commit, GO, GO_RE)
        need(parent == validation, "APPROVAL_PARENT")
    parent, (adoption, adoption_pin) = p.approval_line(validation, VALID, VALID_RE)
    need(parent == adoption, "APPROVAL_PARENT")
    parent, (prior, prior_pin, freeze, freeze_pin) = p.approval_line(adoption, ADOPT, ADOPT_RE)
    need(parent == freeze and prior == VENDOR_APPROVAL, "ADOPTION_PARENT")
    p.follows(prior, freeze)
    need(sha256(p.contents(prior, s.VALID)).hexdigest() == prior_pin, "HISTORICAL_APPROVAL")
    plan60_freeze, price_prior, price, vendor, index = historical(prior)
    refs = (freeze, adoption, validation) + ((commit,) if mode == "go" else ())
    manifest = p.file_bytes(ROOT / PINS, freeze_pin, 16384)
    need(all(p.contents(r, PINS) == manifest for r in refs), "MANIFEST")
    pins = p.parse(manifest)
    need(set(pins) == SOURCES and all(map(p.is_pin, pins.values())), "MANIFEST")
    blobs = {n: p.file_bytes(ROOT / n, pin, 2**20) for n, pin in pins.items()}
    need(all(p.contents(r, n) == blob for n, blob in blobs.items() for r in refs), "MANIFEST")
    need([line for line in blobs[PLAN].splitlines() if line.startswith(b"Status ")] == [b"Status FROZEN."],
         "DRAFT_NOT_FROZEN")
    need(all(blobs[n] == p.contents(plan60_freeze, n) for n in INHERITED) and
         s.config(blobs[p.CONFIG]) == s.config(p.contents(plan60_freeze, p.CONFIG)), "INHERITED_TERMS")
    for i, name in enumerate((ADOPT, VALID, GO), 1):
        need(all(p.git("cat-file", "-e", f"{r}:{name}", allow=True).returncode != 0 for r in refs[:i]),
             "EARLY_APPROVAL")
    need(sha256(p.contents(adoption, ADOPT)).hexdigest() == adoption_pin and
         all(p.contents(r, ADOPT) == p.contents(adoption, ADOPT) for r in refs[1:]) and
         all(p.contents(r, VALID) == p.contents(validation, VALID) for r in refs[2:]), "APPROVAL_PIN")
    for num, name in ((LEDGER, "research_rig/TRIAL_LEDGER.md"), (QUEUE, "docs/QUEUE.md")):
        rows = [[x for x in p.contents(r, name).splitlines() if x.startswith(f"| {num} |".encode())] for r in refs]
        need(len(rows[0]) == 1 and PLAN.encode() in rows[0][0] and all(row == rows[0] for row in rows), "LEDGER_QUEUE")
    job = dict(plan=61, queue=QUEUE, ledger=LEDGER, freeze_commit=freeze, freeze_sha256=freeze_pin,
               adoption_commit=adoption, adoption_sha256=adoption_pin, validation_commit=validation,
               plan60_validation_commit=prior, plan60_validation_sha256=prior_pin, price_adoption_source=price_prior,
               vendor_actions_sha256=vendor, vendor_index_sha256=index, adopted_price=price)
    if mode == "go":
        job.update(go_commit=commit, validation_receipt_sha256=receipt)
    return blobs, job


def run_dir(run):
    if not os.path.lexists(run):
        raise Stop("P61_RUN_FOLDER_MISSING: create the private run directory empty with mode 0700")
    try:
        p.private_dir(run)
    except (p.Refused, OSError):
        raise Stop("P61_RUN_FOLDER_NOT_PRIVATE") from None


def load(blobs, job, cfg):
    for path in (p.INPUT, s.VENDOR):
        p.private_dir(path)
    price = job["adopted_price"]
    p.file_bytes(p.COLLECTOR, p.COLLECTOR_SHA256, 2**20)
    q, days, _ = p.local_schedule(blobs)
    need(len(q) == cfg["eligible"] and price["docket_sha256"] == cfg["docket_sha256"], "DOCKET")
    acq = price["acquisition_commit"]
    expected = p.render(p.acquired(price, cfg, price["identities.json"], price["actions.json"]))
    need(p.file_bytes(p.INPUT / f"acquisition.{acq}.lock", price["acquisition_receipt_sha256"],
                      16384, private=True) == expected, "PRICE_RECEIPT")
    ids = p.parse(p.file_bytes(p.INPUT / "identities.json", price["identities.json"], 8*2**20, private=True))
    actions = p.parse(p.file_bytes(p.INPUT / "actions.json", price["actions.json"], 32*2**20, private=True))
    verified = p.identity_actions(q, days, cfg, ids, actions)
    del actions
    adoption = dict(docket_sha256=price["docket_sha256"], identities_sha256=price["identities.json"],
                    bars_sha256=price["bars.json"])
    vendor = s.load_vendor(blobs, job, adoption, cfg, q, verified[0])
    wire = p.file_bytes(p.INPUT / "bars.json", price["bars.json"], 96*2**20, private=True)
    native = SimpleNamespace(decisions={e.a: dict(noncash=e.a not in verified[2]) for e in q})
    p.check_native(blobs[p.PROVENANCE], price, cfg, q, days, ids, native, wire)
    bars = p.parse(wire)
    del wire
    need(bars["version"] == 1 and bars["custodian"] == cfg["custodian"] and bars["endpoint"] == p.ENDPOINT
         and bars["feed"] == "sip" and bars["timeframe"] == "1Day" and bars["adjustments"] == ["raw", "all"]
         and set(bars["records"]) == verified[2], "PACKET_SCHEMA")
    return q, days, p.engine(blobs[p.ENGINE]), verified, vendor, bars["records"]


def bar_leg(e, scope, bar, ident, C):
    if (bar["ticker"], bar["identity"], bar["entry_asof"], bar["filing_asof"], bar["start"], bar["end"]) != (
            ident["ticker"], ident["identity"], str(e.entry), str(e.at.date()), str(e.start), str(e.end)):
        raise Stop("bar_scope")
    return tuple(p.tape(bar[v], set(scope), C) for v in p.VIEWS)


def choose_lot(gates, prefix, leg, start, end, raw, seq, bps, cfg, clock_prefix=""):
    if gates[f"{clock_prefix}{leg}_clock_volume"] != "pass":
        return
    qty = p.quantity(raw[start].c, cfg["capital"], bps, cfg)
    gates[f"{prefix}{leg}_whole_share"] = "pass" if qty else "unaffordable"
    if qty:
        gates[f"{prefix}{leg}_integral_split"] = "fractional" if s.fractional(qty, seq, start, end) else "pass"


def crosscheck_ex(e, act, vendor_leg):
    seq, target = act
    if target is None:
        return "not_evaluable"
    complete, items = vendor_leg
    if not complete:
        return "vendor_mapping_or_coverage"
    # The filing target is the unique verified special on its date.
    # Remove vendor records already assigned exactly to a different verified
    # cash action before comparing the remaining same-amount candidates.
    verified_other = Counter((ex, amount) for ex, kind, amount, *_ in seq
                             if kind in ("ordinary", "special") and not (kind == "special" and ex == target))
    amount = p.exact(e.declared)
    vendor_cash = Counter((ex, value) for ex, kind, value, _ in items
                          if kind == "cash" and value == amount and e.start <= ex <= e.end)
    matching = [ex for ex, _ in (vendor_cash - verified_other).elements()]
    if not matching:
        return "vendor_ex_missing"
    if len(matching) != 1:
        return "vendor_ex_ambiguous"
    return "pass" if matching[0] == target else "vendor_ex_disagrees"


def earlier_clock(e, ex, days):
    idx = bisect_left(days, ex)
    if idx < 2 or days[idx-2] < e.start:
        return "clock_outside_sealed_window", None
    d = days[idx-2]
    if days.closes.get(d) is None or e.at >= days.closes[d]:
        return "filing_not_public_before_entry_close", None
    if d < e.early:
        return "padding_not_complete_before_entry", None
    return "pass", d


def prepare(q, days, C, verified, vendor, records, cfg):
    keyed, actions, modeled = verified
    decision, placed = {}, []
    tolerance = p.exact(p.money(cfg["ohlc_tick"])) / 2 + p.exact(p.money(cfg["ohlc_slack"]))
    for e in q:
        gates = dict.fromkeys(GATES + SHOWN_GATES, "not_evaluable")
        decision[e.a] = {"gates": gates, "placed": False, "stress_placed": False,
                         "liquid_placed": False, "earlier_placed": False}
        if e.a not in modeled:
            gates["verified_ex_clock"] = "noncash_skip"
            continue
        act = actions[e.a]
        reason, start, end = blind.ex_clock(e, act["stock"][1], days)
        gates["verified_ex_clock"] = reason or "pass"
        gates["vendor_ex_agreement"] = crosscheck_ex(e, act["stock"], vendor[e.a]["stock"])
        earlier = None
        if end is not None:
            gates["earlier_clock"], earlier = earlier_clock(e, end, days)
        scope = days[bisect_left(days, e.start):bisect_right(days, e.end)]
        pad = [day for day in scope if day < e.early]
        need(len(pad) == cfg["pre_padding_sessions"], "PADDING_POLICY")
        legs = {}
        for leg, k in zip(ARMS, ("stock", "iwm")):
            try:
                raw, adj, filing = bar_leg(e, scope, records[e.a][leg], keyed[e.a][1][leg], C)
            except (p.Refused, C.Incomplete, Stop, KeyError, TypeError, ValueError, ArithmeticError):
                gates[k + "_bars"] = "bar_invalid"
                continue
            gates[k + "_bars"] = "pass"
            seq, target = act[leg]
            legs[leg] = raw, seq, target
            if leg == "stock":
                has_pad = all(s.yes(raw, day) for day in pad)
                gates["stock_padding_volume"] = "pass" if has_pad else "unavailable"
                if has_pad:
                    liquidity = sorted(p.exact(raw[day].c) * p.exact(raw[day].v) for day in pad)
                    gates["stock_padding_dollar_volume"] = (
                        "pass" if liquidity[len(pad)//2] >= cfg["min_median_dollar_volume"] else "below_floor")
                    gates["liquid_padding_dollar_volume"] = (
                        "pass" if liquidity[len(pad)//2] >= LIQUIDITY_FLOOR else "below_floor")
            complete, items = vendor[e.a][leg]
            why = s.vendor_compare(raw, adj, filing, scope, items, tolerance)[0] if complete else "vendor_mapping_or_coverage"
            gates[k + "_vendor_basis"] = why or "pass"
            if start is not None:
                gates[k + "_clock_volume"] = "pass" if all(s.yes(raw, d) for d in (start, end)) else "unavailable"
                choose_lot(gates, "", k, start, end, raw, seq, cfg["cost"]["bps"], cfg)
                choose_lot(gates, "stress_", k, start, end, raw, seq, cfg["cost"]["stress_bps"], cfg)
            if earlier is not None:
                gates[f"earlier_{k}_clock_volume"] = "pass" if all(s.yes(raw, d) for d in (earlier, end)) else "unavailable"
                choose_lot(gates, "earlier_", k, earlier, end, raw, seq, cfg["cost"]["bps"], cfg, clock_prefix="earlier_")
        main = all(gates[k] == "pass" for k in GATES)
        stress = main and all(gates[k] == "pass" for k in SHOWN_GATES if k.startswith("stress_"))
        liquid = main and gates["liquid_padding_dollar_volume"] == "pass"
        early = main and all(gates[k] == "pass" for k in SHOWN_GATES if k.startswith("earlier_"))
        decision[e.a].update(placed=main, stress_placed=stress, liquid_placed=liquid, earlier_placed=early)
        if main:
            placed.append((e, start, end, legs, stress, liquid, earlier if early else None))
    return decision, placed


def summary(decisions):
    return dict(events=len(decisions), placed_pairs=sum(d["placed"] for d in decisions.values()),
                shown_stress_pairs=sum(d["stress_placed"] for d in decisions.values()),
                shown_liquid_pairs=sum(d["liquid_placed"] for d in decisions.values()),
                shown_earlier_pairs=sum(d["earlier_placed"] for d in decisions.values()),
                gate_counts={k: dict(Counter(d["gates"][k] for d in decisions.values())) for k in GATES + SHOWN_GATES})


def economic(record, start, end, bps, cfg):
    raw, seq, target = record
    buy, sell = p.exact(raw[start].c), p.exact(raw[end].c)
    n = p.quantity(buy, cfg["capital"], bps, cfg)
    need(n > 0, "SCORE_LOT")
    debit = n * (buy + p.fee(buy, bps, cfg))
    dividend = special = Fraction(0)
    for ex, kind, value, *_ in seq:
        if not start < ex <= end:
            continue
        if kind == "split":
            n *= value
            need(n == int(n), "SCORE_LOT")
        else:
            amount = n * p.exact(value)
            dividend += amount
            if kind == "special" and ex == target:
                special += amount
    pnl = n * (sell - p.fee(sell, bps, cfg)) + dividend - debit
    return pnl / cfg["capital"], special / cfg["capital"]


def marks(rows, years):
    stat = p.cluster([(day, value) for day, _, value in rows])
    winsorized = p.cluster([(day, min(WINSOR_CAP, max(-WINSOR_CAP, value))) for day, _, value in rows])
    n = len(rows)
    drop = ceil(Fraction(n * TRIM_PERCENT, 100))
    trim = p.avg(sorted(v for _, _, v in rows)[:n-drop])
    yearly = {str(y): p.avg([v for day, _, v in rows if day.year == y]) for y in years}
    positive = lambda x: x is not None and x > 0
    t_met = lambda z, bar: positive(z["mean"]) and positive(z["variance"]) and z["mean"]**2 >= bar**2*z["variance"]
    flags = dict(pairs=n >= PAIR_FLOOR, paired_mean=positive(stat["mean"]),
                 winsorized_ex_date_clustered_t=t_met(winsorized, T_FLOOR),
                 positive_after_trim=positive(trim),
                 positive_ex_years=sum(map(positive, yearly.values())) >= YEAR_FLOOR)
    if all(flags.values()):
        disposition = "passed_evidence"
    elif (stat["mean"] is not None and stat["mean"] <= 0) or (winsorized["t"] is not None and not t_met(winsorized, 1)):
        disposition = "close_row"
    elif positive(stat["mean"]) and t_met(winsorized, 1) and not t_met(winsorized, T_FLOOR):
        disposition = "not_shown_not_refuted_forward_pretend_only"
    else:
        disposition = "not_shown_no_forward_disposition"
    return dict(passed=all(flags.values()), marks=flags, paired=stat, winsorized_paired=winsorized,
                disposition=disposition, trim_removed=drop, trimmed_mean=trim, by_ex_year=yearly)


def score(placed, counts, cfg, years):
    rows, stock, iwm = [], [], []
    shown = defaultdict(list)
    for e, first, ex, legs, stress, liquid, earlier in placed:
        a, special = economic(legs["stock"], first, ex, cfg["cost"]["bps"], cfg)
        b, _ = economic(legs["IWM"], first, ex, cfg["cost"]["bps"], cfg)
        paired = a - b
        rows.append((ex, e.a, paired))
        stock.append(a)
        iwm.append(b)
        shown["cash_special_haircut_24_percent"].append(paired - TAX * special)
        if liquid:
            shown["liquidity_at_least_1m"].append(paired)
        y = p.exact(e.declared) / p.exact(legs["stock"][0][first].c)
        shown[f"yield_bucket_{sum(y >= p.exact(cut) for cut in cfg['size_breaks'])}"].append(paired)
        if stress:
            x, y = (economic(legs[leg], first, ex, cfg["cost"]["stress_bps"], cfg)[0] for leg in ARMS)
            shown["stress_cost"].append(x - y)
        if earlier is not None:
            x, y = (economic(legs[leg], earlier, ex, cfg["cost"]["bps"], cfg)[0] for leg in ARMS)
            shown["earlier_entry"].append(x - y)
    for k in ("stress_cost", "cash_special_haircut_24_percent", "liquidity_at_least_1m", "earlier_entry",
              *(f"yield_bucket_{i}" for i in range(3))):
        shown[k]
    judged = marks(rows, years)
    shown_aggregate = {k: dict(n=len(v), paired_mean=p.avg(v)) for k, v in shown.items()}
    shown_aggregate.update(plain_clustered_t=judged["paired"]["t"],
                           stock_only=dict(n=len(stock), mean=p.avg(stock)),
                           matched_iwm=dict(n=len(iwm), mean=p.avg(iwm)))
    raw = judged["paired"]
    judged["paired"] = {k: raw[k] for k in ("n", "groups", "mean")}
    return dict(plan=61, queue=QUEUE, ledger=LEDGER, judged=judged, gate_counts=counts, shown_only=shown_aggregate)


def check_proof(blobs):
    count, proof = p.parse(blobs[COUNT]), p.parse(blobs[PROOF])
    placebo = p.parse(blobs[PLACEBO])
    liquid = p.parse(blobs[LIQUID_PLACEBO])
    pairs = count["terminal_counts"]["price_blind_upper_bound"]
    years = sorted(map(int, count["ex_year_candidates"]))
    need((proof["plan"], proof["ledger"], proof["queue"]) == (61, LEDGER, QUEUE)
         and pairs == sum(count["ex_year_candidates"].values())
         and proof["full"]["candidate_count"] == pairs >= placebo["events_contributing"]
         and proof["liquid"]["candidate_count"] == liquid["liquidity_subset_events"] >= liquid["events_contributing"]
         and (proof["pair_floor"], proof["positive_years_floor"], proof["evidence_t"], proof["trim_top_percent"],
              proof["winsor_cap_bps"]) == (PAIR_FLOOR, YEAR_FLOOR, T_FLOOR, TRIM_PERCENT, WINSOR_CAP * 10_000)
         and proof["trials"] == 6000 and proof["seed"] == 61002 and proof["edge_bps"] == [0, 15, 30, 50], "CALIBRATION")
    for key in ("full", "liquid"):
        case = proof[key]
        need(set(case["by_placement"]) == {"0.7", "0.8"}, "CALIBRATION")
        for place in case["by_placement"].values():
            need(set(place["counts"]) == {"1.0", "1.5", "2.0"}, "CALIBRATION")
            for modes in place["counts"].values():
                need(set(modes) == {"plain_t", "winsor_t"} and all(
                    len(h) == 4 and all(type(v) is int and 0 <= v <= proof["trials"] for v in h)
                    and h[0] <= proof["trials"] // 10 for h in modes.values()), "CALIBRATION")
    return years


def execute(commit, mode):
    blobs, job = authorize(commit, mode)
    run_dir(RUN)
    if mode == "validate":
        expected = {f"{key}.{commit}.json" for key in ("decisions", "validation")}
        need({f.name for f in RUN.iterdir()} <= expected, "RUN_FOLDER_NOT_EMPTY")
    p.unused(RUN)
    cfg = s.config(blobs[p.CONFIG])
    p.resources(cfg)
    years = check_proof(blobs)
    q, days, C, verified, vendor, records = load(blobs, job, cfg)
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
        sys.stdout.buffer.write(p.render(counts) + b"P61_VALIDATED\n")
        return
    pin = sha256(expected).hexdigest()
    need(pin == job["validation_receipt_sha256"] and p.file_bytes(vfile, pin, 32768, private=True) == expected and
         p.file_bytes(dfile, sha256(wire).hexdigest(), 24*2**20, private=True) == wire, "VALIDATION_RECEIPT")
    need(authorize(commit, "go") == (blobs, job), "APPROVAL_CHANGED")
    job["started_utc"] = datetime.now(timezone.utc).isoformat()
    p.once(RUN, job, lambda: score(placed, counts, cfg, years))
    print("P61_SCORED_ONCE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate-inputs", action="store_true")
    modes.add_argument("--go", action="store_true")
    parser.add_argument("--approval-commit", required=True)
    args = parser.parse_args()
    try:
        execute(args.approval_commit, "go" if args.go else "validate")
    except (Stop, p.Refused) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (Exception, KeyboardInterrupt):
        print("P61_REFUSED", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
