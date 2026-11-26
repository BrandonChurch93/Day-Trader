"""Render Replay 41 from its pinned saved result, without opening market data or scoring."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

RESULT_SHA = "509f68fdac4088d6c10e0a8674990804a561c8e0313c7a4610d0481f85487bea"


def pct(stat):
    return f"{stat['mean']:+.4%}"


def t(stat):
    return "undefined" if stat["t"] is None else f"{stat['t']:.2f}"


def row(*cells):
    return "| " + " | ".join(map(str, cells)) + " |"


def stat_row(name, stat):
    return row(name, stat["n"], pct(stat), t(stat))


def render(data):
    j, shown, job = data["judged"], data["shown_only"], data["job"]
    diff, plain, spread = (j[k] for k in ("difference", "conditional", "laggard_minus_winner"))
    trimmed, recent, years = (j[k] for k in ("trimmed_difference", "recent_difference", "years"))
    months, chosen, unaffordable = data["monthly"], data["selected_counts"], data["selected_but_unaffordable"]
    marks = (
        ("minimum_months", "At least 100 judged months", diff["n"], diff["n"] >= 100),
        ("positive_mean", "Paired mean above zero", pct(diff), diff["mean"] > 0),
        ("minimum_t", "Paired t at least 2.0", t(diff), diff["t"] is not None and diff["t"] >= 2.0),
        ("positive_after_best_removed", "Paired mean above zero after dropping the best three months",
         pct(trimmed), trimmed["mean"] > 0),
        ("positive_years", "Positive paired annual mean in at least 7 of 11 years",
         f"{j['positive_years']} of {len(years)}", j["positive_years"] >= 7),
        ("positive_recent", "Paired mean above zero from January 2020", pct(recent), recent["mean"] > 0),
        ("positive_plain", "Conditional rule's own net mean above zero", pct(plain), plain["mean"] > 0),
        ("positive_laggard_minus_winner", "Net laggard minus winner mean above zero", pct(spread), spread["mean"] > 0),
    )
    gates = j["marks"]
    if (
        gates != {key: met for key, _, _, met in marks} or all(gates.values()) != j["passed"]
        or (job["schema"], job["ledger"], job["queue"]) != (1, 176, 54)
        or len(months) != diff["n"] or sum(v["n"] for v in years.values()) != diff["n"]
        or sum(v["mean"] > 0 for v in years.values()) != j["positive_years"]
        or trimmed["n"] != diff["n"] - 3
        or any(sum(m["selected"] == sym for m in months) != chosen[sym] for sym in chosen)
        or any(sum(m["selected"] == sym and m["shares"] == 0 for m in months) != unaffordable[sym]
               for sym in unaffordable)
        or any(m["difference"] != 0 for m in months if m["selected"] == "TLT")
    ):
        raise ValueError("saved results do not reconcile")
    claim = datetime.fromisoformat(job["claimed_utc"]).strftime("%Y-%m-%d %H:%M:%S UTC")
    outcome = "passed" if j["passed"] else "did not pass"
    headers = (row("Comparison", "Months", "Mean net per window", "t"), row("---", "---:", "---:", "---:"))
    lines = [
        "# Replay 41. Switching to the month-end laggard", "",
        f"MEASURED. The laggard switch {outcome}: **{sum(gates.values())} of {len(gates)} frozen marks**. "
        f"The rule averaged {pct(plain)} net per window (t {t(plain)}) but added only {pct(diff)} "
        f"(t {t(diff)}) over always holding TLT in the same {diff['n']} windows. "
        f"The paired mean was {pct(recent)} from 2020 and {pct(trimmed)} without the best three months.", "",
        "STATED. The [frozen rule](../../research_rig/PREREG_41_pension_month_end.md) used raw SIP closes and "
        "issuer cash distributions. It chose the worse-performing ETF (SPY or TLT) by month-to-date total "
        "return at the fifth-last NYSE session's close, bought at the fourth-last close, and sold at the last close. "
        "Each month reset to $500, sized in whole shares. The judged cost was 2 basis points per side. "
        "The January 2016 signal starts at the first session's close; subsequent months start at the previous month-end.", "",
        "## Frozen marks", "",
        "MEASURED. Paired means the rule minus always-TLT with the same window, budget and fee convention. "
        "All marks were required, and zero is not positive.", "",
        row("Fixed bar", "Measured", "Verdict"), row("---", "---:", "---"),
    ]
    lines.extend(row(label, value, "met" if gates[key] else "not met") for key, label, value, _ in marks)
    lines.extend([
        "", "## Net returns at the judged cost", "",
        "MEASURED. The always-TLT return is shown for context and supplies the judged subtraction; "
        "its standalone return, like always-SPY, has no separate pass mark. Laggard minus winner compares "
        "two separately sized long-only arms; it is not a short trade.", "", *headers,
        stat_row("Conditional rule", plain),
        stat_row("Always TLT (benchmark level, shown only)", shown["always_tlt"]),
        stat_row("Always SPY (shown only)", shown["always_spy"]),
        stat_row("Conditional minus always TLT (judged)", diff),
        stat_row("Paired, without best three", trimmed),
        stat_row("Paired, January 2020 through October 2026", recent),
        stat_row("Laggard minus winner (judged sign)", spread), "",
        f"MEASURED. The signal selected TLT in {chosen['TLT']} months, SPY in {chosen['SPY']}, "
        f"and cash on {chosen['CASH']} signal ties. In {unaffordable['SPY']} SPY-selected months, "
        "even one share plus the buy fee did not fit. STATED. The frozen rule held idle cash with zero "
        "return, did not substitute TLT or use fractional shares, and kept these months in the paired comparison. "
        "Selecting TLT contributed a zero paired difference by construction.", "",
        "## Paired result by calendar year", "",
        "MEASURED. The year is assigned by the month-end exit. The 2026 row ends in October.", "",
        row("Year", "Months", "Mean net difference", "t"), row("---", "---:", "---:", "---:"),
    ])
    lines.extend(stat_row(year, stat) for year, stat in sorted(years.items()))
    lines.extend([
        "", "## Cost sensitivity", "",
        "MEASURED. Same windows, with whole shares recalculated for each entry cost. "
        "Only 2 basis points per side were judged; 5 and 10 are shown only.", "",
        row("Basis points per side", "Use", "Rule mean", "Rule t", "Paired mean", "Paired t",
            "Laggard minus winner mean", "Laggard minus winner t"),
        row("---:", "---", "---:", "---:", "---:", "---:", "---:", "---:"),
    ])
    for cost, r, d, s in [(2, plain, diff, spread)] + [
        (int(c), *(bucket[k] for k in ("conditional", "difference", "laggard_minus_winner")))
        for c, bucket in sorted(shown["cost_sensitivity"].items(), key=lambda item: int(item[0]))
    ]:
        lines.append(row(cost, "judged" if cost == 2 else "shown only", pct(r), t(r), pct(d), t(d), pct(s), t(s)))
    lines.extend([
        "", "## Shown only at 2 basis points per side", "",
        "MEASURED. SPY groups use the signal, not whether a share could be bought. The fixed mix averages "
        "two independently sized benchmark sleeves; the mirror picks the winner. The next-session spread "
        "uses the winner minus laggard from the prior signal; October 2026 has no next session in scope.", "", *headers,
    ])
    for key, label in (
        ("spy_on_spy_signal", "SPY in SPY-selected months"),
        ("spy_on_other_signals", "SPY in other months"),
        ("fixed_mix", "Fixed 50/50 mix"),
        ("conditional_minus_fixed_mix", "Conditional minus fixed mix"),
        ("mirror", "Mirror (choose winner)"),
        ("without_january_2016", "Paired without January 2016"),
        ("first_next_session_winner_minus_laggard", "Next-session winner minus laggard"),
    ):
        lines.append(stat_row(label, shown[key]))
    lines.extend([
        "", "## What this adds", "",
        f"MEASURED. Nearly all of the conditional rule's pooled net gain was present in always-TLT "
        f"({pct(shown['always_tlt'])} versus {pct(plain)}). STATED. The practical reading is that the rule "
        f"mostly held TLT at month-end, the same {diff['n']} windows as [Replay 25](69_replay_25_treasury_month_end.md), "
        "with a different whole-share budget denominator. It does not establish a second effect or a reason to switch.", "",
        "STATED. [Harvey, Mazzoleni and Melone, NBER Working Paper 33554, January 2026 revision]"
        "(https://www.nber.org/system/files/working_papers/w33554/w33554.pdf) simulate a monthly 60/40 "
        "reset and use the resulting stock/bond weight drift to predict next-day futures returns in the final "
        "five sessions, strongest in the last four. Their strategy uses long and short futures, including "
        "ten-year Treasury futures, and a separate reversal signal. This replay instead fixes a fifth-last "
        "close ETF signal and holds one long-only ETF at a time for three close-to-close intervals, with "
        "long-duration TLT rather than a ten-year futures leg. It tests the predicted direction in a retail-sized "
        "proxy, not their exact strategy and not who traded. T-statistics are descriptive and unadjusted for "
        "serial dependence or prior related tests. UNKNOWN. Whether a real close order could get these fills.", "",
        "## Run record", "",
        f"MEASURED. The saved result records the claim at {claim} for queue {job['queue']} and ledger {job['ledger']}. "
        "STATED. The lead agent reports one scored run after counts-only validation. This report reads the saved "
        "result only; there was no rerun and the lock stays.", "",
        f"- Approval commit `{job['approval_commit']}`",
        f"- Strategy freeze commit `{job['freeze_commit']}`",
        f"- Saved result SHA-256 `{RESULT_SHA}`",
        f"- Freeze manifest SHA-256 `{job['freeze_sha256']}`",
        f"- Input manifest SHA-256 `{job['input_sha256']}`",
        f"- Cash-action packet SHA-256 `{job['actions_sha256']}`", "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    try:
        blob = args.result.read_bytes()
        if sha256(blob).hexdigest() != RESULT_SHA:
            parser.exit(2, "P41_REPORT_RESULT_PIN\n")
        output = render(json.loads(blob))
    except (OSError, KeyError, TypeError, ValueError):
        parser.exit(2, "P41_REPORT_REFUSED\n")
    print(output, end="")


if __name__ == "__main__":
    main()
