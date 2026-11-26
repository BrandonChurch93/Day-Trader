"""Render Replay 31 from one pinned saved aggregate. Never score or open market inputs."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

RESULT_SHA = "42133558d711352ce132a496924b1b9b01d781d765d8ce9a38c11e19a89daca2"
REVIEW_SHA = "c8fea227114a2e22832333994a86c6db853eb7c87261dc47734407cae8c5b868"
PROXY = {"LQD": "IEF", "HYG": "IEI", "MBB": "IEF", "TIP": "IEF"}


def pct(x):
    return f"{x:+.4%}" if x is not None else "undefined"


def stat(x):
    return f"{x:.2f}" if x is not None else "undefined"


def beta(x):
    return f"{x['min']:.3f} to {x['max']:.3f}"


def row(*cells):
    return "| " + " | ".join(map(str, cells)) + " |"


def render(data):
    j, shown, job = data["judged"], data["shown"], data["job"]
    years, omissions = j["by_year"], j["leave_one_year_out"]
    daily_years, gap = j["daily_by_year"], j["daily"]
    costs, warm = shown["by_cost"], shown["warmup_months"]
    gates = j["gates"]
    passed, years_n = sum(gates.values()), len(years)
    leave_n = sum(v["mean_net"] > 0 for v in omissions.values())
    lqd = costs["2"]["by_fund"]["LQD"]["residual"]
    claimed = datetime.fromisoformat(job["claimed_utc"]).strftime("%Y-%m-%d %H:%M:%S UTC")
    marks = (
        ("windows", "At least 100 judged months", j["n"]),
        ("residual_positive_mean", "Mean net residual above zero", pct(j["mean_net"])),
        ("residual_window_t", "Monthly residual t at least 2.0", stat(j["t"])),
        ("residual_trimmed_positive", "Residual mean above zero without the best three months", pct(j["trimmed_mean"])),
        ("daily_difference_and_t", "Daily residual gap above zero and Welch t at least 2.0",
         f"{pct(gap['difference'])} per day; t {stat(gap['welch_t'])}"),
        ("positive_year_share", "At least 7 years with positive mean monthly residuals", f"{j['positive_years']} of {years_n}"),
        ("post_2019_positive", "Mean monthly residual above zero from January 2020", pct(j["post_2019_mean"])),
        ("every_leave_one_year_out_positive", "Mean residual above zero after each single-year omission",
         f"{leave_n} of {len(omissions)}"),
        ("positive_daily_year_share", "At least 7 years with a positive daily residual gap",
         f"{j['positive_daily_years']} of {years_n}"),
        ("plain_net_pooled_positive", "Plain long-only net mean above zero", pct(j["plain"]["mean_net"])),
    )
    if (set(gates) != {k for k, _, _ in marks} or all(gates.values()) != j["passes"]
            or set(years) != set(omissions) or set(years) != set(daily_years)
            or (job["ledger"], job["queue"]) != (166, 50)
            or costs["2"]["plain"] != j["plain"]
            or costs["2"]["residual"] != {k: j[k] for k in ("n", "mean_net", "t")}):
        raise ValueError("saved results do not reconcile")
    lines = [
        "# Replay 31. Bond funds at month-end", "",
        f"MEASURED. Replay 31 {'passed' if j['passes'] else 'did not pass'}: **{passed} of {len(gates)} marks**. "
        f"The four-fund basket rose {pct(j['plain']['mean_net'])} net per window at 2 basis points per side "
        f"(t {stat(j['plain']['t'])}), but after subtracting its modeled Treasury and stock exposures, "
        f"the average was {pct(j['mean_net'])} (t {stat(j['t'])}) across {j['n']} months.", "",
        "STATED. The [frozen rule](../../research_rig/PREREG_31_bond_etf_month_end.md) put equal dollars in "
        "LQD, HYG, MBB and TIP from the fourth-last New York trading session's close to the last close. "
        "It used raw SIP closes and issuer payouts. Earlier days outside the window set each month's "
        "two slopes: IEF for LQD, MBB and TIP, IEI for HYG, and SPY for all four. The residual subtracts "
        "the contemporaneous gross benchmark returns scaled by those slopes; the benchmark legs were not traded.", "",
        "## Ten frozen marks", "",
        row("Mark", "Measured", "Verdict"), row("---", "---:", "---"),
    ]
    lines.extend(row(label, value, "met" if gates[key] else "not met") for key, label, value in marks)
    lines.extend([
        "",
        f"MEASURED. The pooled gross daily residual averaged {pct(gap['inside_mean'])} inside the window "
        f"({gap['inside_n']:,} intervals) and {pct(gap['outside_mean'])} outside ({gap['outside_n']:,} intervals). "
        f"The difference was {pct(gap['difference'])} per day, with Welch t {stat(gap['welch_t'])}.", "",
        "## Cost and fund breakdown", "",
        "MEASURED. All rows use the same judged months. Costs apply to the actual long funds only. "
        "The 5 and 10 basis point cases and all individual fund rows are shown without verdicts.", "",
        row("Bps per side", "Fund", "Plain net mean", "Plain t", "Residual net mean", "Residual t"),
        row("---:", "---", "---:", "---:", "---:", "---:"),
    ])
    for c in ("2", "5", "10"):
        bucket = costs[c]
        for sym, cell in [("Equal-weight pool", bucket)] + [(s, bucket["by_fund"][s]) for s in PROXY]:
            p, r = cell["plain"], cell["residual"]
            lines.append(row(c, sym, pct(p["mean_net"]), stat(p["t"]), pct(r["mean_net"]), stat(r["t"])))
    lines.extend([
        "",
        f"MEASURED. LQD's residual was {pct(lqd['mean_net'])} at 2 basis points per side (t {stat(lqd['t'])}). "
        "That is an observation from a shown-only row, not a finding about LQD or a separately tested short trade.", "",
        "## By year", "",
        "MEASURED. Residuals use 2 basis points per side for the monthly columns; the daily comparison is gross. "
        "The 2016 and 2026 rows cover only May to December and January to October, respectively.", "",
        row("Year", "Months", "Monthly residual", "Monthly t", "Inside n", "Inside mean", "Outside n",
            "Outside mean", "Daily gap", "Welch t"),
        row("---", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:"),
    ])
    for yr, monthly in sorted(years.items()):
        d = daily_years[yr]
        lines.append(row(yr, monthly["n"], pct(monthly["mean_net"]), stat(monthly["t"]), d["inside_n"],
                         pct(d["inside_mean"]), d["outside_n"], pct(d["outside_mean"]), pct(d["difference"]),
                         stat(d["welch_t"])))
    lines.extend(["", "## Leaving out one year at a time", "",
                  "MEASURED. These subsets overlap; they are not independent tests. "
                  "This mark checks the mean, not the t-statistic.", "",
                  row("Omitted year", "Months left", "Mean residual", "t"), row("---", "---:", "---:", "---:")])
    for yr, subset in sorted(omissions.items()):
        lines.append(row(yr, subset["n"], pct(subset["mean_net"]), stat(subset["t"])))
    lines.extend(["", "## Beta ranges and warm-up", "",
                  "MEASURED. Ranges are from the judged months only. Each beta was fitted on earlier out-of-window days, "
                  "not selected to improve the month-end result.", "",
                  row("Fund", "Treasury ETF", "Treasury beta range", "SPY beta range"),
                  row("---", "---", "---:", "---:")])
    for sym, proxy in PROXY.items():
        legs = shown["beta_ranges"][sym]
        lines.append(row(sym, proxy, beta(legs[proxy]), beta(legs["SPY"])))
    lines.extend(["", "MEASURED. The four warm-up months were shown at 2 basis points per side, not judged. "
                  "They were also excluded from the daily comparison.", "",
                  row("Warm-up month", "Fit intervals", "Plain net", "Residual net"),
                  row("---", "---:", "---:", "---:")])
    for w in warm:
        lines.append(row(w["month"], w["fit_intervals"], pct(w["plain_net"]), pct(w["residual_net"])))
    lines.extend([
        "", "## Reading and limits", "",
        "MEASURED. The long-only bond funds rose into month-end in this sample. There was no positive average "
        "left after the Treasury and stock benchmarks, and the daily comparison did not meet its mark. "
        "STATED. This looks like the month-end rise seen in [Replay 25](69_replay_25_treasury_month_end.md) "
        "showing up in other bond funds, not evidence of a second effect. This test cannot say how much of "
        "the rise came from Treasuries versus stocks or prove that a smaller separate effect is absent.", "",
        f"STATED. The window was borrowed from Replay 25 and only {j['n']} months were judged. "
        "The adjustment uses one Treasury ETF and one stock ETF per fund; it does not remove every yield-curve, "
        "credit, inflation or mortgage risk. The t-statistics are descriptive and do not adjust for serial dependence. "
        "The SIP close and fixed fees are not a live-fill test. UNKNOWN. What a retail order would have earned.", "",
        "## Run record", "",
        f"MEASURED. The pinned result records a claim at {claimed} with ledger {job['ledger']} and queue {job['queue']}. "
        "STATED. The lead agent reports one scored run after counts-only validation and the independent issuer "
        "payout review. This page reads the saved result only.", "",
        f"- Approval commit `{job['approval_commit']}`",
        f"- Strategy freeze commit `{job['freeze_commit']}`",
        f"- Saved result SHA-256 `{RESULT_SHA}`",
        f"- Freeze manifest SHA-256 `{job['freeze_sha256']}`",
        f"- Input manifest SHA-256 `{job['input_sha256']}`",
        f"- Cash-action packet SHA-256 `{job['actions_sha256']}`",
        f"- Independent payout review SHA-256 `{REVIEW_SHA}`", "",
    ])
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("result", type=Path)
    args = p.parse_args()
    try:
        blob = args.result.read_bytes()
        if sha256(blob).hexdigest() != RESULT_SHA:
            p.exit(2, "P31_REPORT_RESULT_PIN\n")
        output = render(json.loads(blob))
    except (OSError, KeyError, TypeError, ValueError):
        p.exit(2, "P31_REPORT_REFUSED\n")
    print(output, end="")


if __name__ == "__main__":
    main()
