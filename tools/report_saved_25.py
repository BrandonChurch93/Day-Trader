"""Render the pinned Replay 25 aggregate result. Does not open inputs or score."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

RESULT_SHA = "902482a78439835871582986aeb40265acd1d6442c95f8ffc90955c788d029a8"
COMMIT = "a23980332e241ba2813d4433b5313aa81e925863"


def pct(x, digits=4):
    return f"{x:+.{digits}%}" if x is not None else "undefined"


def stat(x):
    return f"{x:.2f}" if x is not None else "undefined"


def points(x):
    return f"{100 * x:+.4f} pp" if x is not None else "undefined"


def row(*cells):
    return "| " + " | ".join(map(str, cells)) + " |"


def render(data):
    j, shown, job = data["judged_TLT"], data["shown_TLT"], data["job"]
    gates = j["gates"]
    passed = sum(gates.values())
    years = shown["by_year_at_2bps"]
    daily = j["daily_comparison_by_year"]
    leave = j["leave_one_year_out"]
    comparison = j["daily_comparison"]
    low_year = min(leave, key=lambda y: leave[y]["mean_net"])
    positive_years = sum(x["mean_net"] > 0 for x in years.values())
    positive_daily_years = sum(x["difference"] > 0 for x in daily.values())
    positive_omissions = sum(x["mean_net"] > 0 for x in leave.values())
    time = datetime.fromisoformat(job["claimed_utc"]).strftime("%Y-%m-%d %H:%M:%S UTC")
    verdict = "passed" if j["passes"] else "did not pass"
    marks = (
        ("windows", "At least 100 monthly windows", j["n"]),
        ("positive_mean", "Net mean above zero", pct(j["mean_net"])),
        ("window_t", "Net window t at least 2.0", stat(j["t"])),
        ("trimmed_positive", "Net mean above zero after dropping the best three", pct(j["trimmed_mean"])),
        ("daily_difference_and_t", "Gross inside-minus-outside mean above zero and Welch t at least 2.0",
         f"{points(comparison['difference'])} per day; Welch t {stat(comparison['welch_t'])}"),
        ("positive_year_share", "At least 60% of years have positive net means",
         f"{positive_years} of {len(years)} ({j['positive_year_share']:.1%})"),
        ("post_2019_positive", "Net mean above zero from January 2020", pct(j["post_2019_mean"])),
        ("every_leave_one_year_out_positive", "Net mean above zero omitting any single year",
         f"{positive_omissions} of {len(leave)}; lowest {pct(leave[low_year]['mean_net'])} omitting {low_year}"),
        ("positive_daily_year_share", "At least 60% of years have a positive gross daily difference",
         f"{positive_daily_years} of {len(daily)} ({j['positive_daily_year_share']:.1%})"),
    )
    if {key for key, _, _ in marks} != set(gates) or j["passes"] != all(gates.values()):
        raise ValueError("saved verdict does not reconcile")
    lines = [
        "# Replay 25. Treasury ETF month-end window", "",
        f"MEASURED. The unlevered TLT rule {verdict} **{passed} of {len(gates)} marks** at 2 basis points per side. "
        f"It averaged {pct(j['mean_net'])} net over {j['n']} monthly windows, with a t-statistic of {stat(j['t'])}. "
        "This is the first counted trading-replay pass in this project, not a result from live trading.", "",
        "STATED. The [frozen plan](../../research_rig/PREREG_25_treasury_month_end.md) buys at the fourth-last "
        "session's close, sells at the last session's close, and otherwise holds cash with no yield. "
        "January 2016 through October 2026 is judged; the November extension supplies a shown comparison only. "
        "The run used raw SIP daily bars and dated issuer cash distributions, not adjusted closes.", "",
        "## Nine judged marks", "",
        row("Mark", "Measured", "Verdict"), row("---", "---:", "---"),
    ]
    lines.extend(row(label, value, "met" if gates[key] else "not met") for key, label, value in marks)
    lines.extend([
        "",
        f"MEASURED. Gross daily means were {pct(comparison['inside_mean'])} across {comparison['inside_n']:,} "
        f"inside intervals and {pct(comparison['outside_mean'])} across {comparison['outside_n']:,} "
        "outside intervals. These daily comparisons do not subtract strategy fees.", "",
        "## Calendar years", "",
        "MEASURED. Net means and window t-statistics use the judged strategy and cost. The daily columns are gross. "
        "The final year covers only January through October.", "",
        row("Year", "Windows", "Net mean", "Window t", "Inside n", "Inside mean", "Outside n", "Outside mean",
            "Daily gap", "Welch t"),
        row("---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"),
    ])
    for year, w in sorted(years.items()):
        d = daily[year]
        lines.append(row(year, w["n"], pct(w["mean_net"]), stat(w["t"]), d["inside_n"], pct(d["inside_mean"]),
                         d["outside_n"], pct(d["outside_mean"]), points(d["difference"]), stat(d["welch_t"])))
    lines.extend(["", "## Leaving out one year at a time", "",
                  "MEASURED. This mark requires a positive mean in each reduced sample, not a t-statistic of 2.0.",
                  "The rows overlap, so they are not independent replications.", "",
                  row("Omitted year", "Remaining windows", "Net mean", "Window t"),
                  row("---", "---:", "---:", "---:")])
    for year, w in sorted(leave.items()):
        lines.append(row(year, w["n"], pct(w["mean_net"]), stat(w["t"])))
    costs = shown["other_costs_same_window"]
    widths = shown["other_widths_at_2bps"]
    comparisons = (
        [(f"TLT last three, {cost} bps per side", costs[cost]) for cost in ("5", "10")]
        + [(f"TLT last {width} session{'s' if width != '1' else ''}, 2 bps per side", widths[width])
           for width in ("1", "2", "4", "5")]
        + [("TLT next month's first three sessions, 2 bps per side", shown["next_month_first_three_at_2bps"]),
           ("IEF last three, 2 bps per side", data["shown_IEF_same_rule"]),
           ("TLT calendar 2022 only, 2 bps per side", shown["calendar_2022_at_2bps"])]
    )
    lines.extend(["", "## Shown only", "",
                  "MEASURED. No alternate cost, width, or instrument was used to select the judged result. "
                  f"The assumed return on uninvested cash was {shown['cash_return']:.0%}.", "",
                  row("Variant", "Windows", "Net mean", "Window t"), row("---", "---:", "---:", "---:")])
    lines.extend(row(label, w["n"], pct(w["mean_net"]), stat(w["t"])) for label, w in comparisons)
    lines.extend([
        "", "## Limits", "",
        "UNKNOWN. The consolidated SIP close is not a proven auction fill. A live order could fill at a different "
        "price, and the study has no measured slippage beyond the assumed costs "
        "([Alpaca Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)). "
        f"The same window's mean slips to {pct(costs['5']['mean_net'])} at 5 bps and "
        f"{pct(costs['10']['mean_net'])} at 10 bps per side, and both shown t-statistics are below 2.", "",
        "MEASURED. In the [Measurement 27](70_measure_27_tlt_closing_cross.md) after-run check, not a judged mark, "
        "the Nasdaq closing cross equalled Replay 25's TLT SIP close on 251 of 258 entry or exit sessions with "
        "a cross identified; in the [Replay 26 source check](73_replay_26_blocked_at_source_check.md), a second "
        "vendor differed from SIP by more than one cent on 55 of 1,508 TLT and IEF fund-sessions (3.6%) in "
        "2016–2018, usually by no more than five cents, with the cause UNKNOWN.", "",
        f"MEASURED. A t-statistic of {stat(j['t'])} is modest. It uses the usual sample standard error and does not "
        "adjust for testing many ideas or for dependence over time. One pass in about 25 tests is not strong "
        f"confirmation. The partial 2026 year lost money, averaging {pct(years['2026']['mean_net'])} a window. "
        f"Twelve times the judged monthly mean is about {12 * j['mean_net']:.1%} a year unlevered, before taxes. "
        "That is a way to put the size in context, not measured compound growth or a forecast.", "",
        "STATED. The 2016–2018 years overlap the source paper's 1990–2018 sample. Its roughly 0.25% monthly "
        "figure came from a modeled 10-year Treasury position net of repo, not an ETF purchase "
        "([Hartley and Schwarz](https://kristaschwarz.com/EOM.pdf)). This replay is not a fully independent "
        "test of the original idea. The planned fixed-rule check on older data from a different vendor "
        "was blocked before scoring, so it does not confirm or refute this result.", "",
        "## Run record", "",
        f"MEASURED. The saved result records ledger {job['ledger']}, queue 41, and a claim at {time}. "
        f"STATED. The run owner reports one score from clean commit `{COMMIT}`. "
        "The replay figures come from the saved aggregate result; the later checks are linked above.", "",
        f"- Saved result SHA-256 `{RESULT_SHA}`",
        f"- Freeze manifest SHA-256 `{job['draft_sha256']}`",
        f"- Input manifest SHA-256 `{job['inputs_sha256']}`",
        f"- Cash-action packet SHA-256 `{job['actions_sha256']}`", "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="Off-repo saved results_25.json")
    args = parser.parse_args()
    blob = args.result.read_bytes()
    if sha256(blob).hexdigest() != RESULT_SHA:
        parser.exit(1, "P25_REPORT_RESULT_PIN\n")
    print(render(json.loads(blob)), end="")


if __name__ == "__main__":
    main()
