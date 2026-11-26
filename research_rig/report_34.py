"""Format the pinned M34 aggregate result only; never import or run the scorer."""
import argparse
import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path

RESULT = Path("/home/user/workspace/rig/data/measure_34/results_34.json")
RESULT_SHA = "b0c574ae97c085a962523909ec8ff6a78013b447f69c5bf0336ab15936803a63"
REVIEW_SHA = "e04e0c61a7fe10c4348d6b3fc47012ff2eebd8059f73c41283791528dbf82dd2"
FREEZE_COMMIT = "90d8877d1cc37a20f10d19c790418787fc8924d5"
PAGE = "docs/research/82_measurement_34_tmf_ubt_month_end.md"
CAP_KB = 600000
MARKED = "fixed_2bps_plus_half_spread"
ARMS = {
    "fixed_2bps": "Fixed 2 bp",
    "measured_half_spread": "Half-spread only",
    MARKED: "Fixed 2 bp + half-spread",
    "fixed_5bps": "Fixed 5 bp",
    "fixed_10bps": "Fixed 10 bp",
}


def load(path=RESULT):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != RESULT_SHA:
        raise ValueError("M34 saved result SHA-256 mismatch")
    return json.loads(raw)


def pct(x, digits=4):
    return f"{x:+.{digits}%}"


def times(x):
    return "undefined" if x is None else f"{x:.4f}x"


def verdict(ok):
    return "Pass" if ok else "Fail"


def run_utc(r):
    return datetime.fromisoformat(r["job"]["claimed_utc"]).strftime("%Y-%m-%d %H:%M:%S UTC")


def band(f):
    lo, hi = f["reference_band"]
    return f"{lo:.1f}x to {hi:.1f}x"


def outcome(r):
    f = r["funds"]["TMF"]
    m = f["marks"]
    a = f["arms"][MARKED]
    return (f"TMF gross tracking {times(f['gross_tracking_ratio'])} vs {band(f)} "
            f"({verdict(m['gross_tracking_band']).lower()}); marked net mean {pct(a['mean_net'])} "
            f"({verdict(m['positive_net_at_fixed_2bps_plus_half_spread']).lower()}); "
            f"marked worst window {pct(a['worst_window']['net'], 1)}. UBT shown only.")


def markdown(r):
    funds = r["funds"]
    tmf = funds["TMF"]
    marked = tmf["arms"][MARKED]
    n = marked["n"]
    job = r["job"]
    lines = [
        "# Measurement 34. TMF and UBT at Treasury month-end", "",
        f"MEASURED. {outcome(r)} The unlevered TLT gross mean was {pct(r['tlt_gross_mean'])} per window.", "",
        f"Reading: This uses the same {n} windows as [Replay 25](69_replay_25_treasury_month_end.md). "
        "It measures the cost and tracking of the same effect through leveraged funds, not a second piece of evidence. "
        f"TMF's worst window was about {pct(tmf['arms']['fixed_2bps']['worst_window']['net'], 1)} "
        f"at fixed cost of 2 bp per side and {pct(marked['worst_window']['net'], 2)} at the marked cost. "
        "The quoted spread is an estimate, not an observed fill.", "",
        "## Gross tracking and frozen marks", "",
        "| Fund | Gross mean per window | Gross mean / TLT gross mean | Frozen band | Tracking mark |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for sym, f in funds.items():
        mark = verdict(f["marks"]["gross_tracking_band"]) if sym == "TMF" else "Informational only"
        lines.append(f"| {sym} | {pct(f['gross_mean'])} | {times(f['gross_tracking_ratio'])} | {band(f)} | {mark} |")
    lines += ["",
              f"MEASURED. TMF's other mark, strictly positive mean at {ARMS[MARKED].lower()} per side: "
              f"{verdict(tmf['marks']['positive_net_at_fixed_2bps_plus_half_spread'])} "
              f"({pct(marked['mean_net'])}). UBT has no pass/fail marks.", "",
              "## Closing-minute SIP half-spread", "",
              "| Fund | Side | Endpoints | Mean, bp | Median, bp | P95, bp | Max, bp |",
              "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for sym, f in funds.items():
        for side in ("entry", "exit"):
            x = f[f"{side}_half_spread_bps"]
            stats = " | ".join(f"{x[k]:.3f}" for k in ("mean", "median", "p95", "max"))
            lines.append(f"| {sym} | {side.title()} | {x['n']} | {stats} |")
    lines += ["", "MEASURED. Multiple raw rows at the final timestamp: " +
              "; ".join(f"{sym} {f['tied_quote_endpoints']} of "
                        f"{f['entry_half_spread_bps']['n'] + f['exit_half_spread_bps']['n']}"
                        for sym, f in funds.items()) + ". The frozen policy is a " +
              tmf["tied_quote_policy"] +
              ". It validates every row in the final-timestamp group and ignores vendor row order.", "",
              "## Net cost comparisons", "",
              "Costs are per side; trimmed means drop the three best windows. Fixed-cost ratios use TLT at "
              "the same fixed cost; quote-cost ratios use TLT at fixed 2 bp per side, so the costs differ. "
              "Drawdown is from the rule's own equity on daily closes, including inside held windows. "
              "The last calendar year is partial.", ""]
    for sym, f in funds.items():
        lines += [f"### {sym}", "",
                  "| Cost per side | Mean net | t | Trimmed mean | Worst window (entry to exit) | "
                  "Worst compounded year | Worst mean year | Positive mean years | Net ratio vs TLT | Max drawdown (peak to trough) |",
                  "| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |"]
        for arm, label in ARMS.items():
            a = f["arms"][arm]
            w, d, years = a["worst_window"], a["max_drawdown"], a["by_year"]
            wy, my = a["worst_year_compounded"], a["worst_year_mean"]
            t = "undefined" if a["t"] is None else f"{a['t']:.3f}"
            positive = sum(y["mean_net"] > 0 for y in years.values())
            lines.append(f"| {label} | {pct(a['mean_net'])} | {t} | {pct(a['trimmed_mean'])} | "
                         f"{pct(w['net'], 2)} ({w['entry']} to {w['exit']}) | "
                         f"{wy} ({pct(years[wy]['compounded_net'], 2)}) | {my} ({pct(years[my]['mean_net'], 2)}) | "
                         f"{positive} of {len(years)} | {times(a['net_tracking_ratio'])} | "
                         f"{d['fraction']:.2%} ({d['peak']} to {d['trough']}) |")
        lines += ["", "Annual net mean / compounded return by cost:", "",
                  "| Exit year | Windows | " + " | ".join(ARMS.values()) + " |",
                  "| --- | ---: | " + " | ".join(["---:"] * len(ARMS)) + " |"]
        for year, y in f["arms"][MARKED]["by_year"].items():
            year_costs = [f["arms"][arm]["by_year"][year] for arm in ARMS]
            cells = " | ".join(f"{pct(z['mean_net'], 2)} / {pct(z['compounded_net'], 2)}" for z in year_costs)
            lines.append(f"| {year} | {y['n']} | {cells} |")
        lines.append("")
    lines += ["## Run and custody", "",
              f"MEASURED. The lead ran the [refrozen measurement](../../research_rig/MEASURE_34_tmf_month_end.md) "
              f"once at {run_utc(r)} from commit `{FREEZE_COMMIT}` under a {CAP_KB // 1000} MB "
              f"address-space cap (`ulimit -v {CAP_KB}`). The run is locked; do not rerun it.", "",
              "MEASURED. The second-source payout and split review passed before the run. "
              f"The off-repo payout review (PAYOUT_REVIEW.md) is pinned at SHA-256 `{REVIEW_SHA}`. "
              "This page was generated only from the saved aggregate result; no market payload was opened.", "",
              f"- Result SHA-256: `{RESULT_SHA}`",
              f"- Freeze SHA-256: `{job['freeze_sha256']}`",
              f"- Input manifest SHA-256: `{job['input_sha256']}`",
              f"- Replay 25 TLT manifest SHA-256: `{job['tlt_manifest_sha256']}`", ""]
    return "\n".join(lines)


def dashboard_card(r, github_base):
    f = r["funds"]["TMF"]
    a = f["arms"][MARKED]
    return dict(
        id="measure34", title="Treasury month-end: TMF and UBT", date=r["job"]["claimed_utc"][:10],
        tone="mixed", verdict="TMF: positive net mean, tracking mark missed",
        basis="MEASURED from the pinned aggregate result. UBT is informational only.",
        summary=f"Same {a['n']} windows as Replay 25. This measures costs and tracking, not new evidence. {outcome(r)}",
        numbers=[
            ["TLT gross mean per window", pct(r["tlt_gross_mean"])],
            *[[f"{sym} gross mean / TLT gross mean", times(z["gross_tracking_ratio"])] for sym, z in r["funds"].items()],
            *[[f"{sym} mean net at 2 bp + half-spread per side", pct(z["arms"][MARKED]["mean_net"])]
              for sym, z in r["funds"].items()],
        ],
        links=[["Measurement 34", github_base + PAGE]],
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--summary", action="store_true")
    args = p.parse_args()
    result = load()
    print(f"{run_utc(result)}. {outcome(result)}" if args.summary else markdown(result), end="\n" if args.summary else "")
