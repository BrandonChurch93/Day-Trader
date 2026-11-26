"""Print Replay 53 from its pinned saved result, never from prices or the scorer.

Run: python3 research_rig/report_53.py PATH/TO/results_53.json
The report uses frozen plan settings, the stored synthetic calibration, and
lead-reported custody facts explicitly labelled STATED. It writes only stdout.
"""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean

import yaml

ROOT = Path(__file__).resolve().parent.parent
RESULT_SHA = "2f8e2160d53659c08634a6878e7ceb0f805bc04d922c6444c36cdf1af3d1365a"
STATED = {
    "ticker_changes": 6, "roster_typos": 1,
    "split_ratio": "1-for-2", "split_session": "2024-06-24", "split_accession": "0001398344-25-012578",
    "basis_turn": 2023, "basis_rows": 21, "basis_reviewers": 2, "primary_documented_all": 279,
    "benchmark_amount_window": "January 2026",
    "validation_stop_utc": "2026-11-26 09:02 UTC", "cash_freeze": "06b7bba1c979ed1a4a443711e9f397bd4667dfa8",
}


def pct(x):
    return f"{x:+.2%}"


def row(*cells):
    return "| " + " | ".join(map(str, cells)) + " |"


def table(headers, rows):
    return "\n".join([row(*headers), row(*["---"] * len(headers)), *(row(*r) for r in rows)])


def settings():
    config = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
    scope = config["replay_53_plan"]["value"]
    return config[scope["base"]]["value"], scope


def render(data, base, scope, calib):
    j, shown, job, counts = (data[k] for k in ("judged", "shown_only", "job", "input_counts"))
    m, costs = base["marks"], base["cost"]
    n, picks, capital, sleeve = (base[k] for k in ("turns", "picks", "capital", "sleeve_usd"))
    b = scope["benchmark"]
    years = j["years"]
    claim = datetime.fromisoformat(job["claimed_utc"]).strftime("%Y-%m-%d %H:%M:%S UTC")
    gates = j["marks"]
    status = "Passed" if j["passed"] else "Did not pass"
    total = lambda key: sum(y[key] for y in years)
    denom = lambda x: f"{x} of {n}"
    p = [y["portfolio"] for y in years]
    vs_b = [y["portfolio"] - y["benchmark"] for y in years]
    vs_roster = [y["portfolio"] - y["roster_ew"] for y in years]
    vs_price = [y["portfolio_price"] - y["roster_ew_price"] for y in years]
    trimmed = sorted(p, reverse=True)[m["drop_best"]:]
    actual = [len(years) == n, mean(p) > 0, sum(x > 0 for x in p) >= m["min_positive_years"],
              mean(vs_b) > 0, sum(x > 0 for x in vs_b) >= m["min_years_ahead_of_benchmark"],
              mean(trimmed) > 0, mean(vs_roster) > 0 and mean(vs_price) > 0]
    marks = [
        ("all_turns", "Turns", f"all {n} turns scored", denom(len(years))),
        ("positive_mean", "Net mean", "yearly portfolio mean above zero", pct(j["mean_portfolio"])),
        ("positive_years", "Positive turns", f"at least {denom(m['min_positive_years'])} above zero", denom(j["positive_years"])),
        ("beats_benchmark_mean", f"Against {b}, mean", "mean portfolio minus benchmark above zero",
         pct(j["mean_portfolio_minus_benchmark"])),
        ("beats_benchmark_years", f"Against {b}, turns", f"at least {denom(m['min_years_ahead_of_benchmark'])} ahead",
         denom(j["years_ahead_of_benchmark"])),
        ("positive_without_best", "Without best turn", f"mean above zero after removing the best {m['drop_best']}",
         pct(j["mean_without_best"])),
        ("beats_roster_mean", "Loser effect", "mean portfolio minus roster above zero with cash and with cash zeroed",
         f"{pct(j['mean_portfolio_minus_roster_ew'])} with cash; {pct(j['mean_portfolio_minus_roster_ew_price_only'])} cash zeroed"),
    ]
    if (set(gates) != {k for k, *_ in marks} or actual != [gates[k] for k, *_ in marks]
            or all(actual) != j["passed"] or [y["turn"] for y in years] != list(range(base["first_turn"], base["last_turn"] + 1))
            or any(len(y["held"]) != picks or y["picks"] != picks for y in years)
            or counts["eligible_rows"] != total("eligible") or job["roster_sha256"] != scope["roster_attestation"]["roster_sha256"]):
        raise ValueError("saved result and frozen settings do not reconcile")
    held_total = total("picks")
    zero, fifth = shown["zero_cost"], shown["fifth_january_session_exit"]
    best, worst = max(years, key=lambda y: y["portfolio"]), min(years, key=lambda y: y["portfolio"])
    dollars = lambda x: f"{'+' if x >= 0 else '-'}${abs(x) * capital:.2f}"
    cost_pp = lambda key: f"{(zero[key] - j[key]) * 100:.2f} percentage points"
    gate = shown["vendor_cash_gate"]
    overlap = gate["overlap"]
    summary = gate["by_turn_and_primary_status"].values()
    primary = {k: sum(y[k]["fund_years"] for y in summary) for k in ("documented", "none", "partial", "unresolved")}
    incomplete = sum(v["fund_years"] - v["vendor_complete"] for y in summary for v in y.values())
    g = scope["vendor_cash_gate"]
    corr = shown["replay48_correlation"]
    genuine = [x for x in shown["jump_clearances"] if x["flagged"] and x["outcome"] == "CLEARED_GENUINE_MOVE"]
    dates = sorted({x["later_date"] for x in genuine})
    u = STATED
    outcomes = (("Judged: last January close", j),
                ("Shown only: zero cost", zero), ("Shown only: cash zeroed", shown["cash_zeroed"]),
                ("Shown only: primary cash only", shown["primary_only"]), ("Shown only: fifth January session", fifth))
    pfields = ("mean_portfolio", "mean_benchmark", "mean_portfolio_minus_benchmark",
               "mean_portfolio_minus_roster_ew", "mean_portfolio_minus_roster_ew_price_only")
    rate = calib["pass_rate"]
    return "\n\n".join([
        "# Replay 53. Taxable closed-end fund January rebound",
        f"MEASURED. {status}, **{sum(gates.values())} of {len(gates)} frozen marks**, in the one scored run claimed "
        f"{claim}. The portfolio averaged {pct(j['mean_portfolio'])} net against {pct(j['mean_benchmark'])} for {b} "
        f"and {pct(j['mean_roster_ew'])} for the equal-weight roster. It was positive in {denom(j['positive_years'])} "
        f"turns and ahead of {b} in {denom(j['years_ahead_of_benchmark'])}; both counts missed.",
        "## The rule",
        "STATED, from the [frozen plan](../../research_rig/PREREG_53_taxable_cef_tax_loss.md), "
        "[cash amendment](../../research_rig/AMENDMENT_53_CASH.md) and [identity amendment](../../research_rig/AMENDMENT_53_JUMPS.md). "
        f"Use the latest eligible public {b} holdings before the December cutoff, excluding municipal fund-years. "
        f"At the second-to-last December close, rank complete, affordable, unsplit-through-entry funds by raw price return from the "
        f"first January close. Buy the worst {picks}, each in a ${sleeve} whole-share sleeve at the last December close, "
        f"and sell at the last January close. Cash is credited on eligible ex-dates, not reinvested; idle cash earns nothing. "
        f"{b} is one ${capital} whole-share sleeve. The equal-weight roster averages all eligible ${sleeve} sleeves.",
        "## Frozen marks",
        f"MEASURED. All {len(marks)} marks were required at the judged cost. Zero is not positive.",
        table(("Mark", "Frozen bar", "Measured", "Verdict"),
              ((*cells, "met" if gates[key] else "not met") for key, *cells in marks)),
        "## The ten turns",
        "MEASURED. Turn means the December entry year. Held cash gaps are primary unresolved or partial "
        "windows, even if vendor cash was later admitted. Proxy sides are held entry or exit sides flagged for short quote cover.",
        table(("Turn", "Held funds, in rank order", "Portfolio net", b, "Roster equal weight", "Eligible",
               "Held primary cash gaps", "Held proxy sides"),
              [*((y["turn"], ", ".join(y["held"]), pct(y["portfolio"]), pct(y["benchmark"]), pct(y["roster_ew"]),
                    y["eligible"], f"{y['held_cash_gaps']} of {y['picks']}", y["held_quote_coverage_proxy_sides"]) for y in years),
               ("Mean", "", pct(j["mean_portfolio"]), pct(j["mean_benchmark"]), pct(j["mean_roster_ew"]), "",
                f"{total('held_cash_gaps')} of {held_total}", total("held_quote_coverage_proxy_sides"))]),
        f"MEASURED. Best turn: {best['turn']} at {pct(best['portfolio'])}; without it the mean was "
        f"{pct(j['mean_without_best'])}. A usable exit close was missing for {total('held_missing_exit')} held "
        f"fund-turns and {total('eligible_missing_exit')} eligible fund-turns.",
        "## Costs as charged",
        f"STATED. Each side used the measured closing half-spread plus {costs['extra_bps']} bp, with SIP quotes "
        f"from {costs['measure_start']} through {costs['measure_end']} New York time, a {costs['expiry_seconds']}-second quote "
        f"life and a {costs['min_coverage_seconds']}-second minimum cover. Short cover uses a {costs['proxy_half_bps']} bp "
        f"half-spread proxy plus the same side fee. A missing exit carries the last usable close, charging the larger "
        "of the entry half-spread and the proxy, plus the side fee. There is no separate commission or tax charge.",
        f"MEASURED. {total('held_quote_coverage_proxy_sides')} held sides had short quote cover. Compared with zero cost "
        f"at the same whole-share sizes, the charged costs reduced mean portfolio return by {cost_pp('mean_portfolio')}, "
        f"{b} by {cost_pp('mean_benchmark')} and the roster by {cost_pp('mean_roster_ew')}.",
        "## Against the roster, cash zeroed",
        "MEASURED. The paired comparison uses the same dates, costs, and eligible funds. The loser mark "
        "requires a positive mean both with admitted cash and with all cash set to zero on both sides.",
        table(("Turn", "Minus roster, with cash", "Minus roster, cash zeroed"),
              [*((y["turn"], pct(a), pct(z)) for y, a, z in zip(years, vs_roster, vs_price)),
               ("Mean", pct(j["mean_portfolio_minus_roster_ew"]), pct(j["mean_portfolio_minus_roster_ew_price_only"])),
               ("Turns above zero", denom(sum(x > 0 for x in vs_roster)), denom(sum(x > 0 for x in vs_price)))]),
        "## Shown only",
        f"MEASURED, shown only. These lines do not rescue or replace a mark. Zero cost keeps judged share sizes; cash zeroed "
        f"removes cash for every fund and {b}; primary cash only omits the vendor tier.",
        table(("Line", "Portfolio mean", f"{b} mean", f"Minus {b}", "Minus roster, with line cash",
               "Minus roster, cash zeroed", "Positive turns", f"Turns ahead of {b}"),
              ((label, *(pct(v[k]) for k in pfields), denom(v["positive_years"]), denom(v["years_ahead_of_benchmark"]))
               for label, v in outcomes)),
        f"MEASURED, shown only. Pearson correlation with the [Replay 48 yearly portfolio results](103_replay_48_muni_cef_january.md) "
        f"was {corr['pearson_r']:+.3f} across {corr['observations']} paired turns. This uses the judged last-January-close lines.",
        f"STATED. The exit on January session {base['shown_exit_session']} was a displayed sensitivity. Its performance "
        f"was looked at after the fact on the same {n} years and cannot be counted as a pass. A fair test would freeze that "
        "exit, the roster, costs, cash, benchmarks and marks before looking at new turns, then use genuinely unseen or forward data.",
        f"MEASURED on synthetic data before the run. In {calib['trials']:,} trials (seed {calib['seed']}), the marks "
        f"passed {rate['zero_edge']:.2%} with no edge and {rate['beta_only']:.2%} with a broad rally but no loser effect. "
        "These are model assumptions, not measured odds in real trading.",
        "## In dollars",
        f"MEASURED. On ${capital} once a year the mean net result was {dollars(j['mean_portfolio'])}, versus "
        f"{dollars(j['mean_benchmark'])} for {b} and {dollars(j['mean_roster_ew'])} for the roster. The worst turn was "
        f"{dollars(worst['portfolio'])} and the best was {dollars(best['portfolio'])}, before taxes.",
        "## Gaps and disclosures",
        "\n".join([
            f"- MEASURED. {len(genuine)} raw-close pairs were cleared as genuine March market moves ({' and '.join(dates)}), not split events.",
            f"- STATED by the lead. {u['ticker_changes']} ticker changes were stitched and {u['roster_typos']} roster typo "
            "was corrected (PPF to PPT). Third-party symbol reuse was not checked against a vendor symbol history.",
            f"- MEASURED. {counts['ineligible_terminated_before_entry']} pre-entry delistings or mergers were ineligible, "
            f"{counts['ineligible_other_preentry_gap']} had another pre-entry gap, and {counts['ineligible_preentry_split']} "
            "pre-entry splits made their fund-turns ineligible for ranking and the eligible roster comparison. "
            "They were not treated as held splits. STATED by the lead: these were reverse splits.",
            f"- STATED by the lead. SABA had a {u['split_ratio']} reverse split effective on the first split-basis "
            f"session {u['split_session']} (SEC accession {u['split_accession']}). For turn {u['basis_turn']}, the later split "
            "left different vendor adjusted bases across GIM and SABA. The control copy was aligned to the judged exit basis "
            f"without changing raw bars, using counts only ({u['basis_rows']} of {u['basis_rows']} SABA rows); "
            f"{u['basis_reviewers']} auditors returned CLEAR.",
            f"- STATED by the lead. Primary cash including the benchmark: {u['primary_documented_all']} documented, "
            f"{primary['none']} none, {primary['partial']} partial and {primary['unresolved']} unresolved. MEASURED: the roster-only "
            f"proof had {primary['documented']} documented and {primary['none']} none. Some primary gaps remain even with vendor cash; "
            f"{total('held_empty_cash')} of {held_total} held fund-turns had an empty final cash list, which can also mean no payout.",
            f"- MEASURED. The vendor gate {'passed' if gate['passed'] else 'did not pass'}: {overlap['matched_events']} of "
            f"{overlap['primary_events']} primary events matched and {overlap['clean_windows']} of {overlap['fund_years']} "
            f"proof windows had no extras, versus fixed floors of {g['minimum_primary_match_percent']}% and "
            f"{g['minimum_clean_window_percent']}%. Match required exact ex-date and an absolute amount difference no more than "
            f"${g['amount_tolerance']}. {incomplete} vendor rows were incomplete. The reliable aggregate admitted "
            f"{gate['admitted_events']} events as `{gate['admitted_source_kind']}`. STATED: blank native currency was treated as USD, "
            "and blank-currency candidates were checked against matching blank-currency proof events. The overlap is not a random sample.",
            "- MEASURED from the frozen source. The shown-only by-turn/status counts of admitted vendor events and fund-turns "
            "overwrite rather than add when more than one fund qualifies in a bucket. Do not add those fields to infer coverage. "
            "The change from the cash amendment to the final freeze did not fix this bug. It does not affect the gate totals, "
            "overall admitted event count, cash credited, returns, or marks.",
            "- STATED by the lead. Two brief custody exposures: NAV text in one SEC exhibit, and a helper output that printed "
            "post-exit reinvestment prices for one fund. No such numbers are reproduced here.",
            f"- STATED by the lead. The {b} {u['benchmark_amount_window']} distribution amount did not have a distinct second "
            "source. The vendor tier did not supplement the benchmark.",
            "- STATED. The roster comes from public holdings snapshots, which can be stale; the index screen also limits coverage. "
            "The benchmark and roster are linked by construction and have different weights. Thin funds may not fill at the modeled close. "
            "The turns share calendar shocks and are not independent draws.",
        ]),
        "## Stops before scoring",
        "\n".join([
            f"- MEASURED from the saved validation output. At {u['validation_stop_utc']}, validation stopped with "
            f"`P53_UNRECORDED_SPLIT`. STATED by the lead, the {base['split_check_ratio']} factor guard flagged "
            f"{len(genuine) + 1} pairs: {len(genuine)} genuine moves and one BTX ticker reuse. The v4 amendment documented "
            "the moves and repaired the ticker reuse by using the documented historical identities; this stop took no lock.",
            "- STATED by the custodian. Two offline packet assembly stops, not scorer validation: "
            "`UNDOCUMENTED_NATIVE_SPLIT` for missing primary evidence on the SABA split, resolved by the SEC record; "
            "`REPAIRED_SPLIT_CONTROL` for the GIM to SABA basis step, resolved by the documented control-copy alignment. "
            "Both were resolved before sealing.",
            f"- UNKNOWN. The reported possible pre-cash scorer validation stop has no saved output located; its code and time "
            f"are not verified. The cash amendment came first, at commit `{u['cash_freeze']}`.",
            "- MEASURED. The sealed v4 validation printed `P53_INPUTS_OK`, and the sole scored run printed "
            "`P53_RESULT_WRITTEN`. The publication does not rerun either.",
        ]),
        "## Next to Replay 48",
        "- MEASURED. Replay 48 passed its frozen marks; Replay 53 did not. Both beat their eligible rosters on average with cash zeroed.\n"
        f"- MEASURED. The judged portfolios shared the same {n} turn years and had a positive turn-level correlation.\n"
        "- STATED, lead agent's reading. Treat this as related evidence for a January rebound, not a second independent pass.\n"
        "- STATED, lead agent's reading. The taxable last-January-close rule does not advance on this result.",
        "## Independent recompute",
        "UNKNOWN. Independent recompute in progress; outcome to be filled by the lead.",
        "## Run record",
        f"MEASURED. The saved result records a claim at {claim} for queue {job['queue']} and ledger {job['ledger']}. "
        "STATED. The lead reports one successful scored run; this page reads that saved result without reopening market data or the scorer.",
        "\n".join(f"- {label} `{value}`" for label, value in (
            ("Approval commit", job["approval_commit"]), ("Strategy freeze commit", job["freeze_commit"]),
            ("Saved result SHA-256", RESULT_SHA), ("Freeze manifest SHA-256", job["freeze_sha256"]),
            ("Input manifest SHA-256", job["input_sha256"]), ("Roster SHA-256", job["roster_sha256"]),
            ("Distributions SHA-256", job["distributions_sha256"]),
            ("Jump clearances SHA-256", job["jump_clearances_sha256"]),
            ("Identity segments SHA-256", job["identity_segments_sha256"]))),
    ]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    blob = args.result.read_bytes()
    if sha256(blob).hexdigest() != RESULT_SHA:
        parser.error("saved Replay 53 result does not match its pin")
    calib = json.loads((ROOT / "research_rig/CALIBRATION_53.json").read_bytes())
    print(render(json.loads(blob), *settings(), calib), end="")


if __name__ == "__main__":
    main()
