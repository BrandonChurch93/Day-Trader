"""Write Replay 60 from the sealed aggregate result and saved validation output.

Run: python3 research_rig/report_60.py
The optional tracked RECOMPUTE_60.json is a separate aggregate review note.
Never opens price or action inputs, or imports or invokes the scorer.
"""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path("/home/user/workspace/rig/data")
TARGET = ROOT / "docs/research/126_replay_60_special_dividends.md"
RECOMPUTE = ROOT / "research_rig/RECOMPUTE_60.json"
RESULT_SHA = "c28680d0b3515b8bd0b3827048b3ad10ae28db4c2cae6262411e53500121e3d1"
VALIDATION_SHA = "40fc7e591f7eff9b8131112ccc11f534d19d8dc6ac82c9eb342448c041033a0c"
FIRST_STOP_SHA = "b26e485145c304040b1349819593324c191a64b0c35e19d757c269b79794f144"
# Frozen terms and separately stated freeze-test record, not newly estimated values.
CAPITAL, SLEEVES, SLEEVE_USD = 500, 5, 100
ENTRY, SHOWN_ENTRY, EXIT, WAIT, PRE = 2, 1, 20, 5, 5
MIN_VOLUME, FLOOR_PAIRS, T_FLOOR, YEAR_FLOOR = 100_000, 300, 2, 7
TRIM, RECENT, BPS, STRESS_BPS, SHARE_FLOOR = 0.01, 2020, 5, 10, 0.01
YIELD_LOW, YIELD_HIGH = 0.01, 0.03
FREEZE_TESTS_PASSED, FREEZE_TESTS_TOTAL = 16, 17
PRIOR_PLAN, PRIOR_STOPS = 43, 3

DECISIONS = {
    "eligible_pair": "Placed stock and matched IWM pair",
    "noncash_skip": "Frozen noncash exclusion",
    "outside_padding_volume": "Outside universe: missing or zero-volume padding session",
    "outside_dollar_volume": "Outside universe: low median dollar volume",
    "unfilled_entry": "Unfilled stock entry: missing or zero-volume bar",
    "refused_no_exit": "Refused: no permitted exit",
    "refused_vendor_basis": "Refused: stock or IWM vendor basis",
    "refused_fractional_split": "Refused: judged lot would become fractional",
    "unfilled_capital": "Unfilled stock entry: whole share not affordable",
    "unfilled_iwm_clock": "Unfilled IWM control: matched clock unavailable",
    "unfilled_iwm_capital": "Unfilled IWM control: whole share not affordable",
}
BASIS_REASONS = {
    "vendor_mapping_or_coverage": "Vendor mapping or coverage incomplete",
    "unsupported_vendor_action": "Unsupported vendor action",
    "vendor_action_not_session": "Vendor action date not a regular session",
    "vendor_basis_mismatch": "Adjusted bars did not match the reconstructed basis",
    "unsupported_vendor_action_combination": "Unsupported same-session actions",
    "vendor_cash_reference_missing_or_invalid": "Cash action lacked a usable reference close",
    "vendor_basis_insufficient": "Too few usable raw and adjusted pairs",
}
SPLIT_ARMS = {
    "entry_plus_one": f"Session +{SHOWN_ENTRY} entry",
    "stress_cost": "Higher friction",
    "paired_spy": "Paired SPY",
    "sleeves": "Settled sleeves",
}
SLEEVE_SKIPS = {
    "cannot_buy_share_or_unsettled": "Whole share not affordable or cash unsettled",
    "issuer_open": "Issuer already open or reserved",
    "no_free_sleeve": "No free sleeve",
}
SHOWN = {
    "entry_plus_one": f"Session +{SHOWN_ENTRY} entry",
    "stress_cost": f"Higher friction ({STRESS_BPS} bp per side, same cent floor)",
    "paired_spy": "Stock minus SPY",
    "deployed": "Stock mean on deployed cash",
    "declared_ex_inside": "Declared ex-date inside actual hold",
    "declared_ex_outside_or_canceled": "Declared ex-date outside hold or canceled",
    "first_time_YES": "First-time declaration: yes",
    "first_time_NO": "First-time declaration: no",
    "first_time_UNKNOWN": "First-time declaration: unknown",
    "size_bucket_0": f"Declared yield below {YIELD_LOW:.0%}",
    "size_bucket_1": f"Declared yield at least {YIELD_LOW:.0%} and below {YIELD_HIGH:.0%}",
    "size_bucket_2": f"Declared yield at least {YIELD_HIGH:.0%}",
    "including_vendor_basis_refusals": "Stock including otherwise feasible vendor-basis refusals",
    "paired_iwm_including_vendor_basis_refusals": "Stock minus IWM including otherwise feasible vendor-basis refusals",
}


def checked(path, digest):
    blob = path.read_bytes()
    if sha256(blob).hexdigest() != digest:
        raise ValueError(f"saved artifact does not match its pin: {path.name}")
    return blob


def pct(value):
    return "not available" if value is None else f"{value:+.2%}"


def money(value):
    return f"{'+' if value >= 0 else '-'}${abs(value):,.2f}"


def table(header, rows):
    def row(cells):
        return "| " + " | ".join(map(str, cells)) + " |"
    return "\n".join((row(header), row(["---"] * len(header)), *(row(r) for r in rows)))


def read_recompute(path):
    if not path.exists():
        return None
    note = json.loads(path.read_bytes())
    fields = {"by", "read_scorer", "verdict", "taken_as_given", "rederived", "compared_fields", "differences", "notes"}
    if type(note) is not dict or set(note) != fields or note["verdict"] not in {"AGREE", "DIFFERS", "PENDING"}:
        raise ValueError("bad aggregate recompute schema")
    if note["verdict"] == "PENDING":
        return None
    plain = lambda v: type(v) is str and bool(v.strip()) and v.isprintable() and "\u2014" not in v
    if (not plain(note["by"]) or type(note["read_scorer"]) is not bool
            or not all(type(note[k]) is list and all(map(plain, note[k])) for k in ("taken_as_given", "rederived", "notes"))
            or not all(type(note[k]) is int for k in ("compared_fields", "differences"))
            or not 0 <= note["differences"] <= note["compared_fields"]
            or (note["differences"] == 0) != (note["verdict"] == "AGREE")):
        raise ValueError("inconsistent aggregate recompute note")
    return note


def independent(note):
    if note is None:
        return "UNKNOWN. Independent recompute: pending."
    read = "read" if note["read_scorer"] else "did not read"
    return "\n".join([
        f"STATED by {note['by']}. Independent recompute: {note['verdict']}. The helper {read} the scorer.",
        "",
        f"- Compared fields: {note['compared_fields']}; differences: {note['differences']}.",
        f"- Taken as given: {'; '.join(note['taken_as_given']) or 'nothing listed'}.",
        f"- Rederived: {'; '.join(note['rederived']) or 'nothing listed'}.",
        *(f"- {item}" for item in note["notes"]),
    ])


def render(data, validation, validated, first_error, first_exit, note):
    job, o = data["job"], data["outcome"]
    j, counts, shown, sleeves = (o[k] for k in ("judged", "decisions", "shown", "sleeves"))
    a, p, years, flags = (j[k] for k in ("absolute", "paired", "by_acceptance_year", "marks"))
    yearly, reasons = counts["by_year"], counts["reason_counts"]
    positive_years = sum(v is not None and v > 0 for v in years.values())
    labels = {
        "placed": ("Placed pairs", f"At least {FLOOR_PAIRS} pairs", a["n"], a["n"] >= FLOOR_PAIRS),
        "net": ("Net mean", "Stock mean above zero", pct(a["mean"]), a["mean"] > 0),
        "clustered_t": ("Stock clustered t", f"Positive stock mean and t at least {T_FLOOR}",
                        f"{a['t']:.2f}", a["mean"] > 0 and a["t"] >= T_FLOOR),
        "trimmed": ("Without best events", f"Mean above zero after dropping the best {TRIM:.0%}, rounded up",
                    f"{pct(j['trimmed_mean'])}; removed {j['trim_removed']}", j["trimmed_mean"] > 0),
        "positive_years": ("Positive years", f"At least {YEAR_FLOOR} positive acceptance years",
                           f"{positive_years} of {len(years)}", positive_years >= YEAR_FLOOR),
        "recent": ("Recent mean", f"Mean above zero from {RECENT} onward",
                   pct(j["recent_mean"]), j["recent_mean"] > 0),
        "paired": ("Paired IWM", f"Positive stock minus IWM mean and clustered t at least {T_FLOOR}",
                   f"{pct(p['mean'])}; t {p['t']:.2f}", p["mean"] > 0 and p["t"] >= T_FLOOR),
    }
    basis = counts["vendor_basis_refusal_reasons"]
    if (counts != validation or (o["plan"], o["ledger"], o["queue"]) != (job["plan"], job["ledger"], job["queue"])
            or set(flags) != set(labels) or any(flags[k] != spec[-1] for k, spec in labels.items())
            or j["passed"] != all(flags.values()) or a["n"] != p["n"] or a["n"] != reasons["eligible_pair"]
            or set(years) != set(yearly) or set(reasons) != set(DECISIONS)
            or sum(reasons.values()) != counts["events"] or not set(basis) <= set(BASIS_REASONS)
            or set(shown) - set(SHOWN) or set(sleeves["skips"]) - set(SLEEVE_SKIPS)
            or any(sum(row["reason_counts"].values()) != row["events"] for row in yearly.values())
            or any(sum(row["reason_counts"][k] for row in yearly.values()) != v for k, v in reasons.items())):
        raise ValueError("saved aggregate result, no-return summary or frozen marks do not reconcile")
    missed = [label for k, (label, *_) in labels.items() if not flags[k]]
    verdict = "Passed" if j["passed"] else "Did not pass"
    miss_text = ("Missed " + ", ".join(missed) + "." if len(missed) == 1 else
                 "Missed marks: " + ", ".join(missed) + "." if missed else "No marks were missed.")
    when = datetime.fromisoformat(job["started_utc"]).strftime("%Y-%m-%d %H:%M:%S UTC")
    control_mean = a["mean"] - p["mean"]
    return "\n\n".join([
        f"# Replay {o['plan']}. Special-dividend declarations",
        f"MEASURED. {verdict}, **{sum(flags.values())} of {len(flags)} frozen marks** in the single scored run at "
        f"{when}. {miss_text} The average stock return was {pct(a['mean'])} net and the paired lead over IWM was "
        f"{pct(p['mean'])}, but its clustered t was {p['t']:.2f}.",
        "## The rule",
        "STATED from the [frozen plan](../../research_rig/PREREG_60_special_dividends.md). "
        f"Require positive stock volume on every one of the {PRE} frozen padding sessions and at least "
        f"${MIN_VOLUME:,} in median daily dollar volume over those sessions. Buy whole shares on ${CAPITAL} "
        f"at the session +{ENTRY} open and plan to sell at the session +{EXIT} close. "
        f"If the planned exit bar is absent or has no volume, use the first positive-volume open in the next {WAIT} sessions. "
        f"No usable entry means no fill; gaps inside a hold are carried. IWM uses the same actual clocks. "
        f"Charge the larger of {BPS} bp of trade value or ${SHARE_FLOOR:.2f} per share per side. "
        "Use independently verified actions for cash and share changes.",
        "## Frozen marks",
        f"MEASURED. All {len(flags)} marks were required. The t statistics group observations by entry month.",
        table(("Mark", "Frozen bar", "Measured", "Verdict"),
              ((label, bar, value, "met" if flags[k] else "not met") for k, (label, bar, value, _) in labels.items())),
        "## Judged block",
        "MEASURED. A placed pair uses the same stock and IWM clocks, each on its own starting allocation. "
        "The IWM mean below is the stock mean less the saved mean of the paired differences. "
        "Stock minus IWM is a difference in percentage points.",
        table(("Line", "Pairs", "Mean net", "Clustered t", "Entry months"), [
            ("Stock", a["n"], pct(a["mean"]), f"{a['t']:.2f}", a["groups"]),
            ("Matched IWM", p["n"], pct(control_mean), "not stored", p["groups"]),
            ("Stock minus IWM", p["n"], pct(p["mean"]), f"{p['t']:.2f}", p["groups"]),
        ]),
        "## By acceptance year",
        "MEASURED. Stock means use only judged pairs. The result does not store annual IWM or paired means.",
        table(("Year", "Filing events", "Judged pairs", "Stock mean net", "Missing padding", "Low volume",
               "Vendor basis refusals", "Fractional lot refusals", "Stock capital misses"),
              ((y, r["events"], r["reason_counts"]["eligible_pair"], pct(years[y]),
                *(r["reason_counts"][k] for k in ("outside_padding_volume", "outside_dollar_volume",
                  "refused_vendor_basis", "refused_fractional_split", "unfilled_capital")))
               for y, r in sorted(yearly.items()))),
        "## Decisions and refusal reasons",
        f"MEASURED. The {counts['events']} filing events each have one terminal decision. "
        f"There were {counts['delayed_exits']} delayed exits and {counts['inside_unavailable_sessions']} "
        "unavailable sessions carried inside holds. The counts below do not replace any mark.",
        table(("Decision", "Events"), ((label, reasons[k]) for k, label in DECISIONS.items())),
        f"MEASURED. Vendor diagnostic tags below count stock or IWM legs across the docket, not distinct refused events. "
        f"There were {reasons['refused_vendor_basis']} terminal event refusals for this reason. "
        "A leg can carry a tag on an event already excluded for another reason.",
        table(("Vendor basis diagnostic", "Stock or IWM legs"), ((label, basis.get(k, 0)) for k, label in BASIS_REASONS.items())),
        "## Shown only",
        "MEASURED, shown only. None of these figures can count toward a mark. The inclusion checks add otherwise "
        "feasible vendor-basis refusals as a sensitivity; they do not establish those raw bars are correct.",
        table(("Line", "Observations", "Mean net"), ((label, shown[k]["n"], pct(shown[k]["mean"]))
                                                    for k, label in SHOWN.items() if k in shown)),
        f"MEASURED, shown only. There were {counts['shown_spy_basis_failures']} SPY basis failures, of which "
        f"{counts['shown_spy_basis_omissions']} alone removed a feasible SPY comparison. There were "
        f"{counts['vendor_only_in_window_actions']} vendor-only and {counts['filing_only_in_window_actions']} "
        f"verified-list-only in-window action instances across event legs. "
        f"Of {counts['post_window_action_legs']} legs with a post-window price action, "
        f"{counts['post_window_action_explains_legs']} had a known action product within the fitted interval. "
        f"UNKNOWN. Absolute tail scale: {o['vendor_tail_absolute_scale']}.",
        table(("Shown arm", "Fractional-lot flags"), ((label, counts["shown_fractional_split_arms"][k])
                                                      for k, label in SPLIT_ARMS.items())),
        "## Settled sleeves on starting cash",
        f"MEASURED, shown only. Starting with ${CAPITAL} in {SLEEVES} settled ${SLEEVE_USD} sleeves, "
        f"the replay placed {sleeves['placed']} orders and made {money(sleeves['pnl_usd'])} total net, "
        f"or {pct(sleeves['on_starting_cash'])} of starting cash. This is a full-period result before taxes, "
        "not an annual return and not a mark.",
        table(("Sleeve skip", "Events"), ((label, sleeves["skips"].get(k, 0)) for k, label in SLEEVE_SKIPS.items())),
        "## Gaps and disclosures",
        "\n".join([
            f"- STATED in the frozen plan. Replay {PRIOR_PLAN} stopped {PRIOR_STOPS} times during validation, "
            "without ever computing a return. The lead and auditor knew the earlier refusal counts. "
            "This replay carried forward the docket, not an earlier return.",
            f"- MEASURED. {reasons['refused_vendor_basis']} events were refused because stock or IWM vendor bases did "
            "not reproduce or were not established. The judged result does not establish an effect for them.",
            "- STATED. A split can be announced after entry. The fractional-lot refusal therefore depends on "
            f"hindsight, not on the entry screen. It excluded {reasons['refused_fractional_split']} judged events.",
            f"- MEASURED from saved stderr. The first validation stopped with `{first_error}` (exit {first_exit}). "
            "STATED by the lead. The private run directory did not exist; after it was created empty with private permissions, "
            f"validation printed `{validated}`. No return was computed by validation.",
            f"- STATED from the freeze test record. The direct frozen-head suite passed {FREEZE_TESTS_PASSED} of "
            f"{FREEZE_TESTS_TOTAL} tests. The draft-rejection fixture copied the frozen status from the checkout. "
            "The same test passed with the parent's draft text supplied only to its temporary fixture; the freeze was not changed.",
            "- UNKNOWN. The replay does not establish future fills, future returns, or an effect on the filings that did not place.",
        ]),
        "## Independent recompute",
        independent(note),
        "## Run record",
        f"MEASURED. The saved result records a scored run on queue {o['queue']} and ledger {o['ledger']}. "
        "The saved validation totals exactly match the scored result's decision totals. This report does not rerun validation or scoring.",
        "\n".join([
            f"- Freeze commit `{job['freeze_commit']}`",
            f"- Freeze manifest SHA-256 `{job['freeze_sha256']}`",
            f"- Adoption commit `{job['adoption_commit']}`",
            f"- Validation approval `{job['validation_commit']}`",
            f"- Scoring approval `{job['go_commit']}`",
            f"- Saved result SHA-256 `{RESULT_SHA}`",
            f"- Saved validation output SHA-256 `{VALIDATION_SHA}`",
        ]),
    ]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, default=DATA / "replay_60/result.json")
    parser.add_argument("--validation-dir", type=Path, default=DATA / "replay_60_notes")
    parser.add_argument("--output", type=Path, default=TARGET)
    args = parser.parse_args()
    data = json.loads(checked(args.result, RESULT_SHA))
    lines = checked(args.validation_dir / "validate_v2.out", VALIDATION_SHA).decode("ascii").splitlines()
    first_error, exit_line = checked(args.validation_dir / "validate_v1.err", FIRST_STOP_SHA).decode("ascii").splitlines()
    if lines[-1] != "P60_VALIDATED" or first_error != "P60_REFUSED" or not exit_line.startswith("exit="):
        raise ValueError("saved validation transcript is not the expected record")
    page = render(data, json.loads("\n".join(lines[:-1])), lines[-1], first_error, int(exit_line[5:]),
                  read_recompute(RECOMPUTE))
    args.output.write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
