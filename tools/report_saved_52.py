"""Print Replay 52 from one pinned saved result; never open market data or run the scorer."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from statistics import fmean
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RESULT_SHA = "a4e7e74f0cca19f2b1ae22130f5816a7b6a9ff062847ef0c710fc5c185c1beca"
LOCK_SHA = "8ec1943cb08c4d78c0cf2f8920a86813760e551ed379460aafe592058148d22f"
CASH_REVIEW_SHA = "f6bb59a4dea09140db22485479be25eae30e703c769fc43b7f1cee096d9aa54e"
RECOMPUTE_SHA = "f76b54e7cf35bea6f651ae960da92e71efd789d526cdbd9a3eb4dbfa0391850b"


def percent(value, places=4):
    return f"{value:+.{places}%}"


def signed_money(value):
    return f"{'-' if value < 0 else '+'}${abs(value):.2f}"


def settings():
    config = (ROOT / "config/thresholds.yaml").read_text().split("replay_52_plan:\n  value: ", 1)[1].splitlines()[0]
    calibration = json.loads((ROOT / "research_rig/CALIBRATION_52.json").read_bytes())
    selected = calibration["selected"]
    row = next(x for x in calibration["variants"] if all(x[k] == v for k, v in selected.items()))
    return json.loads(config), row["scenarios"]


def render(result):
    cfg, scenarios = settings()
    job, judged = result["job"], result["judged"]
    net, proxy, controls = (judged[k] for k in ("net", "proxy_net", "controls_net"))
    gap = result["shown_only"]["quarter_minus_control_net"]
    events = result["events"]
    shown = events["shown"]
    clock = datetime.fromisoformat(job["claimed_utc"])
    local = clock.astimezone(ZoneInfo("America/Boise")).strftime("%Y-%m-%d %H:%M:%S %Z")
    utc = clock.strftime("%Y-%m-%d %H:%M:%S UTC")
    expected = cfg["expected"]
    budget = cfg["budget_usd"]
    years = cfg["judged_last_year"] - cfg["judged_first_year"] + 1
    pace = net["count"] // years
    symbols = len(set(cfg["funds"]) | set(cfg["proxies"].values()))
    coverage = cfg["sessions_per_symbol"]
    fees = cfg["cost_bps_per_side"]
    marks = judged["marks"]
    trim = cfg["marks"]["drop_best"]
    cutoff = cfg["marks"]["minimum_t"]
    cases = [
        ("mean_net", "Net mean above zero", percent(net["mean"])),
        ("mean_proxy_net", "Net mean after the Treasury proxy above zero", percent(proxy["mean"])),
        ("t_proxy_net", f"Net-of-proxy t at least {cutoff:.1f}", f"{proxy['t']:.2f}"),
        ("above_non_quarter_month_ends", "Net mean above ordinary month-ends",
         f"{percent(net['mean'])} against {percent(controls['mean'])}"),
        ("trimmed_net", f"Net mean above zero without the best {trim} quarters", percent(judged["trimmed_net_mean"])),
        ("non_december_net", f"Net mean above zero on {expected['non_december']} non-December quarters",
         percent(judged["non_december_net_mean"])),
    ]
    if (set(marks) != {k for k, _, _ in cases} or all(marks.values()) != judged["supported"]
            or (job["ledger"], job["queue"]) != (cfg["ledger_row"], cfg["queue_row"])
            or len(events["quarters"]) != net["count"] or net["count"] != proxy["count"]
            or len(events["controls"]) != controls["count"] or len(shown) != expected["shown"]
            or net["count"] != expected["quarters"] or controls["count"] != expected["controls"]):
        raise ValueError("saved result and frozen settings disagree")
    outcome = "passed" if judged["supported"] else "did not pass"
    table = "\n".join(f"| {label} | {value} | {'met' if marks[key] else 'not met'} |" for key, label, value in cases)
    funds = ", ".join(cfg["funds"])
    shown_year = cfg["shown_last_month"][:4]
    edge = cfg["calibration"]["power_target_bps"]
    return f"""# Replay 52. Corporate bond funds after quarter-end

MEASURED. The rule {outcome}: **{sum(marks.values())} of {len(marks)} frozen marks**. The basket averaged {percent(net['mean'])} net per quarter-end (t {net['t']:.2f}) across {net['count']} quarters and rose in {net['positive']} of them. Net of the Treasury proxy it averaged {percent(proxy['mean'])} (t {proxy['t']:.2f}). The same basket averaged {percent(controls['mean'])} after ordinary month-ends (t {controls['t']:.2f}). The rule does not advance.

## The rule

STATED, from the [frozen plan](../../research_rig/PREREG_52_quarter_end_dealer_rebound.md). Split ${budget} equally across {funds} using fractional shares. Buy at the last scheduled quarter close and sell at the close after {cfg['held_sessions']} new-quarter sessions. Credit dated cash distributions during the hold without reinvesting. Use raw daily SIP closes and {fees} basis points of assumed cost per side; no quote spread was measured. Subtract the same-window gross IEF return for LQD and VCIT and the IEI return for HYG and JNK. The proxies are comparisons, not short trades or exact duration matches.

STATED. Judged dates are quarter-ends from {cfg['judged_first_year']} through {cfg['judged_last_year']}, with the same-window ordinary month-ends as the control. The licensed raw SIP source begins in {cfg['judged_first_year']}, so the earlier year in the original draft was removed before any price was read. No substitute or mixed-vendor data filled it. The {shown_year} quarters were set aside from every mark.

## Frozen marks

MEASURED. All marks had to pass. Zero does not meet a positive sign mark. The raw net t and positive-quarter count are context, not marks.

| Mark | Measured | Verdict |
|---|---:|---|
{table}

## Shown only

MEASURED. Quarter-end minus ordinary month-end was {gap['net_mean_difference']*100:+.4f} percentage points (Welch t {gap['welch_t']:.2f}). The t had no pass threshold and does not adjust for shared or serial shocks. Ordinary month-ends were positive in {controls['positive']} of {controls['count']} windows.

MEASURED. The {len(shown)} {shown_year} windows averaged {percent(fmean(x['net'] for x in shown))} net and {percent(fmean(x['proxy_net'] for x in shown))} after the Treasury proxy. They are not a second trial and do not change the result.

## In dollars

MEASURED. On a fresh ${budget} at each entry, the mean net result was {signed_money(budget*net['mean'])} per quarter-end basket, or {signed_money(budget*net['mean']*pace)} per year at {pace} round trips without compounding, before taxes. STATED. These are sample averages at assumed fills, not expected profits or losses.

## What the result can show

STATED. [Rapp and Waibel](https://www.aeaweb.org/conference/2026/program/paper/S2KkB95R) studied dealer balance sheets; this replay tested an ETF trade, not their mechanism. Replay 31 already used parts of the post-close clock in a pooled daily comparison, as disclosed in the frozen plan.

MEASURED, synthetic only. The pre-run model passed {scenarios['quarter_only'][str(edge)]['rate']:.2%} of worlds with a true quarter-only edge of +{edge} bp. With that same edge at every month-end, it passed {scenarios['all_month_ends'][str(edge)]['rate']:.2%}. STATED. This failure does not rule out a small effect, and even a pass would not establish that the rise is special to quarter-ends. UNKNOWN. Whether live fractional orders could have obtained these closes.

## Data checks and run record

- **Validation**: STATED, from the lead's counts-only check. It placed {sum(len(v) for v in events.values())} windows: {net['count']} judged, {controls['count']} controls and {len(shown)} shown. There were {expected['non_december']} non-December judged windows. Each of {symbols} symbols had {coverage:,} sessions ({symbols*coverage:,} bars in total). Validation checked one split and found no holding window that crossed it.
- **JNK history**: STATED, from the lead's custody report. The first vendor query omitted 839 JNK sessions before the reverse split in 2019. The custodian recovered those sessions using the documented literal-ticker setting, and the code auditor rebuilt the packet byte for byte. No adjusted data were substituted.
- **Cash history**: STATED, from the lead's custody report. The independent checker added five cash distributions for 2016-08-01 that were missing from the vendor, using issuer pages. The off-repo checker report is pinned below.
- **First command**: STATED, from the lead. The first `--go` refused with `P52_PRIVATE` before the lock was claimed and before any return was computed. The results directory had the wrong mode and contained the validation output. The lead moved those files out, set the directory to `0700`, and the one scored run completed.
- **Claim**: MEASURED. The saved result was claimed {local} ({utc}). This report reads the pinned saved result only. The lock stays in place.

## Independent recompute

MEASURED. Entry and exit dates matched for all {net['count']} quarters, {controls['count']} controls and {len(shown)} shown windows. The largest absolute per-window return difference was on the order of 1e-18; summaries matched to floating-point precision and all {len(marks)} marks failed in both. STATED. The independent reviewer wrote the recompute before opening the saved result and did not open the scorer. The recompute note is off repo, SHA-256 `{RECOMPUTE_SHA}`.

STATED. A future plan could put these details together more explicitly. The review used the {controls['count']} non-quarter month-ends in {cfg['judged_first_year']} through {cfg['judged_last_year']}; applied the same ex-date cash rule to Treasury proxies; used sample standard deviation with n minus one for t; treated positive as strictly above zero; trimmed the highest {trim} raw net results out of {net['count']}; and applied trading cost on fund legs only. All these readings matched the scorer.

## Pins

- Approval commit `{job['approval_commit']}`
- Freeze commit `{job['freeze_commit']}`
- Saved result SHA-256 `{RESULT_SHA}`
- Lock SHA-256 `{LOCK_SHA}`
- Freeze manifest SHA-256 `{job['freeze_sha256']}`
- Input manifest SHA-256 `{job['input_sha256']}`
- Cash-action packet SHA-256 `{job['actions_sha256']}`
- Independent cash review SHA-256 `{CASH_REVIEW_SHA}`
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saved_result", type=Path)
    args = parser.parse_args()
    blob = args.saved_result.read_bytes()
    if sha256(blob).hexdigest() != RESULT_SHA:
        parser.exit(2, "Saved result SHA-256 mismatch.\n")
    print(render(json.loads(blob)), end="")


if __name__ == "__main__":
    main()
