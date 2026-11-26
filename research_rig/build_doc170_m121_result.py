"""Rebuild doc 170 (Measurement 121 result) from two pinned aggregate files only.

Reads the runtime's summary and the auditor's independent aggregate, both kept outside
the repo. No order row, quote, trade or vendor page is opened here.
"""
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research/170_m121_result.md"
SUMMARY = Path("/home/user/workspace/rig/data/m121r/completed/summary.json")
CHECK = Path("/home/user/workspace/rig/data/m121r_check/independent_aggregate.json")
SUMMARY_SHA = "c7f408b6e2e14f1d7b12ff2e30f537d6dce28cc242418316aa1c33fe823ff14b"
CHECK_SHA = "2ca21071c92a192aed9bde8a80e1666595a6babf5d63a635eb21799950302021"
GROUPS = (("equity", "Stock funds"), ("taxable_bond", "Taxable bond funds"), ("muni", "Muni funds"), ("pooled", "All"))
MARKS = (("short", "60 seconds"), ("primary", "300 seconds (the main mark)"), ("long", "900 seconds"), ("close", "Just before the close"))


def pinned(path, digest):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != digest:
        raise ValueError(f"pinned input differs: {path.name}")
    return json.loads(raw)


def pct(x, d=1):
    return f"{100 * x:.{d}f}%"


def bp(x):
    return f"{x:+.1f} bp"


def main():
    s, c = pinned(SUMMARY, SUMMARY_SHA), pinned(CHECK, CHECK_SHA)
    g, cg = s["by_group"], c["by_group"]
    P, CP = g["pooled"], cg["pooled"]
    boot = {m: s["bootstrap"][m]["pooled"] for m in ("fund_day", "calendar_day")}
    est = boot["fund_day"]
    cm = CP["marks"]["primary"]["metrics"]["bps"]
    # The two counts must agree exactly; the means to a hundredth of a basis point.
    for name, _ in GROUPS:
        a, b = g[name], cg[name]
        assert (a["scheduled"], a["evaluable_placed"], a["states"]["filled"], a["states"]["unknown"]) == \
               (b["scheduled"], b["evaluable_placed"], b["fills"], b["unknown"]), name
        for mark, _ in MARKS:
            assert a["mark_available"][mark] == b["marks"][mark]["available"], (name, mark)
    assert abs(est["primary_gross_bps"]["estimate"] - cm["gross"]["mean"]) < .01
    assert abs(est["primary_adverse_bps"]["estimate"] - cm["adverse"]["mean"]) < .01
    assert abs(est["primary_entry_half_bps"]["estimate"] - cm["entry_half"]["mean"]) < .01
    assert s["coverage_floors_met"] is False and c["coverage_floors_met"] is False
    assert s["consider_later_strategy_test"] is False and c["consider_later_strategy_test"] is False
    stale = P["reasons"]["placement_quote_stale"]
    half, adverse, exitc = (cm[k]["mean"] for k in ("entry_half", "adverse", "exit_concession"))
    gross = cm["gross"]["mean"]
    assert abs(half - adverse - exitc - gross) < .01
    saved = est["entry_ask_saved_bps"]
    L = []
    w = L.append
    w("# Measurement 121 result: what a small resting bid in a closed-end fund keeps")
    w("")
    w("- Status: RECORD. Built by `research_rig/build_doc170_m121_result.py` from two aggregate files held outside the repo; no order row is in the repo.")
    w("- Plan, rule changes and the stop record of the first attempt: [doc 166](166_m121_cef_resting_bid.md). Ledger rows 223 (first attempt, stopped with nothing kept) and 224 (this run).")
    w("- This is a measurement of order handling on past quotes and trades. It is not a profit test and no order was sent anywhere.")
    w("")
    w("## Short answer")
    w("")
    w(f"- MEASURED: a pretend $500 buy order resting at the best bid for 30 minutes filled {pct(P['fill_rate_headline'], 2)} of the time ({P['states']['filled']} of {P['evaluable_placed']} placed orders).")
    w(f"- MEASURED: on the fills that could be marked, the best bid five minutes after the fill was {bp(gross)} from the fill price on average, median {bp(cm['gross']['median'])} ({cm['gross']['n']} of {P['states']['filled']} fills). 95% interval {boot['fund_day']['primary_gross_bps']['lower']:+.1f} to {boot['fund_day']['primary_gross_bps']['upper']:+.1f} bp by fund-day, {boot['calendar_day']['primary_gross_bps']['lower']:+.1f} to {boot['calendar_day']['primary_gross_bps']['upper']:+.1f} bp by calendar day. Both are wholly below zero.")
    w(f"- MEASURED: the order earned half the spread, {bp(half)}, and then the middle price moved against it by {adverse:.1f} bp within five minutes. Selling back at the bid would give up another {exitc:.1f} bp. The bid fills mostly when the price is about to fall.")
    w("- By the decision line fixed before the run: the coverage floors were not met and the interval is below zero, so no strategy test follows from this. The idea of earning the spread with a patient bid in these funds is closed.")
    w("")
    w("## Counts")
    w("")
    w("| Group | Scheduled | Could not be judged | No placement | Placed | Filled | Fill rate |")
    w("|---|---|---|---|---|---|---|")
    for name, label in GROUPS:
        a = g[name]
        w(f"| {label} | {a['scheduled']:,} | {a['states']['unknown']:,} | {a['states']['not_placed']} | {a['evaluable_placed']:,} | {a['states']['filled']} | {pct(a['fill_rate_headline'], 2)} |")
    w("")
    w(f"- MEASURED: {P['identity_excluded_slots']} more slots ({P['identity_excluded_fund_days']} fund-days, one fund) were left out before the run under Amendment 1.")
    w(f"- MEASURED: {P['states']['unknown']:,} of {P['scheduled']:,} slots could not be judged, {stale:,} of them because the quote at the placement time was older than the plan allows. So only {pct(P['known_slots'] / P['scheduled'])} of slots are known, against a floor of 90% in every group. These funds quote too seldom for the rule as written.")
    w(f"- MEASURED: {P['mark_available']['primary']} of {P['states']['filled']} fills ({pct(P['mark_available']['primary'] / P['states']['filled'])}) had a usable five-minute mark, against a floor of 90%. The floors on distinct funds, fund-days and dates were met ({P['primary_marked_funds']} funds, {P['primary_marked_fund_days']} fund-days, {P['primary_marked_dates']} dates).")
    w("- The figures below are therefore from the half of the sample that could be judged. UNKNOWN: whether the other half would look the same.")
    w("")
    w("## After a fill")
    w("")
    w("| Mark | Fills marked | Mean, bid against fill price | Median |")
    w("|---|---|---|---|")
    for mark, label in MARKS:
        m = CP["marks"][mark]["metrics"]["bps"]["gross"]
        w(f"| {label} | {m['n']} | {bp(m['mean'])} | {bp(m['median'])} |")
    w("")
    w("| Group | Fills marked at 300 s | Mean | 95% interval by fund-day |")
    w("|---|---|---|---|")
    for name, label in GROUPS:
        b = s["bootstrap"]["fund_day"][name]["primary_gross_bps"]
        w(f"| {label} | {g[name]['mark_available']['primary']} | {bp(b['estimate'])} | {b['lower']:+.1f} to {b['upper']:+.1f} bp |")
    w("")
    w(f"- MEASURED, description only: against the best ask at the moment the order was placed, a filled order paid {saved['estimate']:.1f} bp less ({saved['lower']:.1f} to {saved['upper']:.1f}). That saving is on the {pct(P['fill_rate_headline'], 1)} that filled; the other {pct(1 - P['fill_rate_headline'], 1)} bought nothing.")
    w(f"- INFERENCE: five minutes after a fill the bid sits {abs(gross):.1f} bp under the fill price and the ask about two half-spreads above that bid, so a buyer who simply waited and took the ask would have paid about the same. The patient bid is not cheaper in a way we can use; it is roughly a wash, with a {pct(1 - P['fill_rate_headline'], 0)} chance of not buying at all.")
    w("")
    w("## Check")
    w("")
    w("- MEASURED: an independent auditor recomputed every count and mean from the kept order rows with its own program, without reading the runtime's report code or its summary. This builder refuses to write the page unless the counts match exactly and the means match to a hundredth of a basis point.")
    w(f"- MEASURED: the auditor's own 95% intervals for the main mark, from a different random stream, are {c['primary_intervals']['fund_day']['bounds'][0]:+.1f} to {c['primary_intervals']['fund_day']['bounds'][1]:+.1f} bp by fund-day and {c['primary_intervals']['calendar_day']['bounds'][0]:+.1f} to {c['primary_intervals']['calendar_day']['bounds'][1]:+.1f} bp by calendar day.")
    w("")
    w("## Limits")
    w("")
    w(f"- STATED by the runtime: {s['identity']['limit']}")
    w("- One window of 24 sessions in September and October 2025, 23 funds drawn by a fixed hash from SEC filings. A fill is inferred from a later exchange trade at least one cent through the limit that covers the whole order; real queue position is not known, so the true fill rate could be lower or higher.")
    w("- Halt and pause data covered only part of each session. Gross figures: no commission, no regulatory fee.")
    w("- What it is good for: any later closed-end fund rule should assume it pays the spread to get in. A patient bid does not lower the cost.")
    OUT.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
