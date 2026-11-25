"""Write or check the Replay 06 page from stored summaries. Reads no bars and runs no rule."""

import argparse
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "docs/research/35_replay_06_fund_trend.md"
LABEL = {
    "G1": "Month-end trend, core funds",
    "G2": "Daily trend ensemble, core funds",
    "G3": "SPY momentum versus bills, else IEF",
    "G4": "Month-end trend on SPY",
    "G5": "Top ranked funds above trend",
    "G6": "Fixed SPY/IEF mix, no timing",
    "HOLD_CORE": "Core funds hold",
    "HOLD_ALL": "All eligible funds hold",
    "SPY": "SPY hold",
    "SPY_IEF": "Equal SPY/IEF hold",
}
SENS = ("at_zero_cost", "at_stress_cost", "next_close")


def pct(x):
    return "UNKNOWN" if x is None else f"{x:.2%}"


def num(x):
    return "UNKNOWN" if x is None else f"{x:.2f}"


def row(*cells):
    return "| " + " | ".join(map(str, cells)) + " |"


def dates(pane):
    return " through ".join(pane["dates"])


def metrics(stats):
    return " / ".join((pct(stats["cagr"]), num(stats["sharpe"]), pct(stats["maxdd"]),
                       f"{stats['sides']:,}"))


def flag(passed):
    return "pass" if passed else "fail"


def break_even(rule):
    be = rule["break_even"]
    if be["status"] == "below_at_zero":
        return "never ahead at zero"
    return (">" if be["status"] == "above_cap" else "") + num(be["bps"])


def paste_rows(j):
    all_rules = j["rules"]
    held = j["slices"]["held"]
    def at(key):
        return held["rules"][key]["base"]["cagr"]

    n, k = len(all_rules), sum(r["marks"]["passed"] for r in all_rules.values())
    cost = j["costs_bps_per_side"]["base"]
    page = "`docs/research/35_replay_06_fund_trend.md`"
    status = row("Replay 06", "Slow trend and allocation rules on Alpaca daily fund bars",
                 f"{k} of {n} passed at {cost} bps per side. G5 passed only the cost mark: "
                 f"held back {dates(held)}, {pct(at('G5'))} a year versus "
                 f"{pct(at('HOLD_ALL'))} for its yardstick and {pct(at('SPY'))} for SPY hold.",
                 page)
    done = row("14", "Replay 06: fund trend rules on daily prices",
               f"Done. Held-back slice run once. {k} of {n} passed at {cost} bps per side. "
               f"G5 beat its own yardstick on yearly gain, but not SPY hold or all the marks ({page}).")
    return status, done


def render(j, coverage, calibration):
    rules, slices = j["rules"], j["slices"]
    design, held = slices["design"], slices["held"]
    cost = j["costs_bps_per_side"]
    prov = j["provenance"]
    th = prov["thresholds"]
    pwr = calibration["illustrative_power"]
    months = coverage["slices"]["held"]["complete_month_end_sessions"]
    if months != pwr["complete_holdout_months"]:
        raise ValueError("Power and coverage use different month counts.")
    base = {k: v["base"] for k, v in held["rules"].items()}
    stats = th["replay_06_statistics"]
    setup = th["replay_06_rules"]
    funds = ", ".join(prov["input_files"])
    n_pass = sum(r["marks"]["passed"] for r in rules.values())
    ahead = sum(base[k]["cagr"] > base["SPY"]["cagr"] for k in rules)
    status, done = paste_rows(j)
    t = [
        "# Replay 06: slow trend rules on funds", "",
        f"MEASURED. {n_pass} of {len(rules)} passed at the assumed {cost['base']} bps per side. "
        f"G5 passed only the cost mark. In the held-back slice, {ahead} beat SPY hold on yearly gain. "
        "These are simulated results, not a practice or live account record.", "",
        "## What was asked", "",
        "- STATED. Can slow trend rules on funds you can buy cut losses and still beat holding after costs? "
        "Each rule faced its own holding yardstick, and every rule was also shown against SPY hold. "
        "Where a pass mark uses a holding yardstick, it uses the rule's own. G6 was a fixed mix, not a timing rule.", "",
        "## How it ran", "",
        f"- MEASURED. Design: {dates(design)} ({coverage['slices']['design']['sessions']:,} sessions). "
        f"Held back: {dates(held)} ({coverage['slices']['held']['sessions']:,} sessions). The held period ran once "
        f"against [the frozen plan](../../research_rig/PREREG_06_fund_trend_paid_data.md) in `{prov['prereg_commit'][:7]}`. "
        f"Mark 3 counted {j['trial_count']} trials: {stats['prior_count_at_draft']} prior plus "
        f"{stats['new_trials']} new, including the G6 context row (`replay_06_statistics` and the ledger).",
        "- STATED. The runner used [Alpaca SIP daily bars](https://docs.alpaca.markets/reference/stockbars) "
        f"adjusted for distributions and splits: {funds}. Signals used data through the decision close, with fills at the next "
        "session's open. Inactive trend sleeves held BIL. Each slice started from cash; no sale was added at its end. "
        "The simulated opening price is not proof that an order would fill there.",
        f"- STATED. The judging cost was {cost['base']} bps on each buy or sell "
        "(`cost_model_bps_per_side_liquid_etf`), including the first buy for each yardstick and trades in BIL. "
        "It was an allowance for spread and slippage, not a measured charge.",
        f"- STATED. The basket yardsticks held equal parts and rebalanced yearly. G6 started at "
        f"{setup['g6_spy_weight']:.0%} SPY and {1 - setup['g6_spy_weight']:.0%} IEF, and reset yearly. "
        "The equal SPY/IEF yardstick is extra context for G3.", "",
        "## Rules against holding", "",
        "MEASURED. Each result cell shows yearly gain / annualized Sharpe above BIL / largest drop from a closing peak / trade sides. "
        f"All use {cost['base']} bps per side. A buy or sell in a fund is a side. "
        "SPY appears twice where it is both the main yardstick and the common comparison.", "",
    ]
    for phase, pane in slices.items():
        t += [f"### {phase.capitalize()}", "",
              row("Rule", "Rule result", "Own holding yardstick", "Yardstick result", "SPY hold"),
              "|---|---:|---|---:|---:|"]
        data = pane["rules"]
        for key, rule in rules.items():
            own = rule["primary"]
            t.append(row(f"{key}: {LABEL[key]}", metrics(data[key]["base"]), LABEL[own],
                         metrics(data[own]["base"]), metrics(data["SPY"]["base"])))
        t += ["", f"Extra yardstick for G3, equal SPY/IEF hold: {metrics(data['SPY_IEF']['base'])}. "
              "This yardstick was not used to judge G3.", ""]
    t += [
        "### Holding with exposure matched in hindsight", "",
        f"MEASURED. This check uses each rule's own yardstick and BIL, with {cost['base']} bps per side. "
        "The rule's average weight outside BIL sets the yardstick's target weight. "
        "That weight is known only after the slice, so this is not a trading rule or pass mark. "
        "The cells use the same units as the tables above.", "",
        row("Rule", "Design yardstick with BIL", "Held yardstick with BIL"),
        "|---|---:|---:|",
    ]
    for key in rules:
        t.append(row(key, metrics(design["exposure_matched"][key]), metrics(held["exposure_matched"][key])))
    t += [
        "", "## Pass marks", "",
        f"- STATED. In the held period, mark 1 requires higher Sharpe than the main yardstick and a largest drop at most "
        f"{pct(th['replay_max_drop_ratio_vs_hold'])} as large (`replay_max_drop_ratio_vs_hold`).",
        f"- STATED. Mark 2 uses compounded growth across both reset slices. The rule must beat its yardstick at no cost and stay ahead through "
        f"{cost['stress']} bps per side (`backtest_min_breakeven_cost_multiple`).",
        f"- STATED. Mark 3 requires whole-sample deflated Sharpe above {num(th['replay_min_deflated_sharpe'])} "
        "(`replay_min_deflated_sharpe`). This mark raises the bar because many rules were tried.",
        f"- MEASURED. Mark 4 used the worst overfitting estimate, {pct(j['max_pbo'])}, "
        f"against a cap of {pct(th['backtest_max_pbo'])} (`backtest_max_pbo`). Estimates by fixed start: "
        + "; ".join(f"{d}: {pct(v['pbo'])}" for d, v in j["pbo"].items()) + ".",
        f"- STATED. Mark 5 requires beating more than {pct(th['replay_min_shuffle_percentile'])} "
        "of the matched timing draws (`replay_min_shuffle_percentile`). G6 has no timing control, so it cannot pass mark 5.", "",
        f"MEASURED. These are the stored verdicts at a judging cost of {cost['base']} bps per side.", "",
        row("Rule", "Mark 1", "Mark 2", "Mark 3", "Mark 4", "Mark 5", "Overall",
            "Break-even bps/side", "Deflated Sharpe", "Timing draws beaten"),
        "|---|---|---|---|---|---|---|---:|---:|---:|",
    ]
    for key, rule in rules.items():
        marks = rule["marks"]
        s = rule["shuffle"]
        t.append(row(key, *(flag(marks[k]) for k in sorted(marks) if k != "passed"),
                     flag(marks["passed"]), break_even(rule), num(rule["deflated_sharpe"]),
                     "n/a" if s is None else pct(s["percentile"])))
    t += [
        "", "## Cost and fill checks", "",
        "MEASURED. The table shows yearly gain. The cost-free and doubled-cost checks fill at the next open. "
        f"The next-close check uses the same {cost['base']} bps per side as the main run. "
        "These are checks, not new pass verdicts.", "",
        row("Rule or yardstick", f"Design: {cost['zero']} bps", f"Design: {cost['stress']} bps",
            "Design: next close", f"Held: {cost['zero']} bps", f"Held: {cost['stress']} bps",
            "Held: next close"),
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key in design["rules"]:
        t.append(row(f"{key}: {LABEL[key]}", *(
            pct(pane["rules"][key][mode]["cagr"]) for pane in (design, held) for mode in SENS)))
    t += [
        "", "## Timing control", "",
        f"MEASURED. The control used {th['replay_09_statistics']['draws']:,} timing draws per rule "
        f"where available. It rotated each rule's target schedule within each slice, kept fund targets "
        f"together and charged the same {cost['base']} bps per side. It did not force the same turnover. "
        "Turnover is traded dollars divided by account value, per year. Each pair is rule / mean control. "
        "Non-BIL weight is the average share of the account outside BIL.", "",
        row("Rule", "Design turnover", "Held turnover", "Design non-BIL weight", "Held non-BIL weight"),
        "|---|---:|---:|---:|---:|",
    ]
    for key, rule in rules.items():
        shuffle = rule["shuffle"]
        first, second = shuffle["slices"] if shuffle else ({}, {})
        d = design["rules"][key]["base"]
        t.append(row(key, *(f"{pct(actual[m])} / {pct(ctrl['mean_' + m]) if shuffle else 'n/a'}"
                           for m in ("turnover_py", "risk_weight")
                           for actual, ctrl in ((d, first), (base[key], second)))))
    t += ["", "MEASURED. Each twin figure is total gain for the first timing draw in that slice, not yearly gain. "
          "The last column compares compounded growth across both slices; ties do not count as wins.", "",
          row("Rule", "Design twin total gain", "Held twin total gain", "Whole-sample draws beaten"),
          "|---|---:|---:|---:|"]
    for key, rule in rules.items():
        shuffle = rule["shuffle"]
        twins = [pct(s["random_twin_total"]) for s in shuffle["slices"]] if shuffle else ["n/a", "n/a"]
        t.append(row(key, *twins,
                     pct(shuffle["percentile"]) if shuffle else "n/a"))
    t += [
        "", "## What it shows", "",
        f"- MEASURED. G5 earned {pct(base['G5']['cagr'])} per year versus "
        f"{pct(base['HOLD_ALL']['cagr'])} for holding its funds and {pct(base['SPY']['cagr'])} for SPY. "
        f"It broke even against its own yardstick at {break_even(rules['G5'])} bps per side over the combined slices. "
        f"Its held-back Sharpe was lower than that yardstick's "
        f"({num(base['G5']['sharpe'])} versus {num(base['HOLD_ALL']['sharpe'])}).",
        f"- MEASURED. G4, the closest comparison to the practice trend rule, earned "
        f"{pct(base['G4']['cagr'])} a year with a {pct(base['G4']['maxdd'])} drawdown versus "
        f"{pct(base['SPY']['cagr'])} and {pct(base['SPY']['maxdd'])} for SPY hold. "
        "The smaller drop did not make it a pass.", "",
        "## What it does not show", "",
        f"- MEASURED. The held period contains {months} complete months "
        "(`fund_coverage_06.json`). "
        f"The bars begin {th['replay_06_data']['first_bar']} (`replay_06_data.first_bar`); "
        "they do not include the 2008 financial crisis.",
        "- STATED. Months and funds can move together. The fund list was chosen from funds that survived. Backward dividend adjustments can change "
        "with vendor revisions. The replay used a single price source and did not test capacity, tax, "
        "real dividend reinvestment or actual fill costs.",
        f"- STATED. With independent months, {pct(pwr['assumed_annual_active_sd'])} assumed annual active volatility "
        f"and {pct(pwr['goal'])} power, the sketch needs about {100 * pwr['detectable_annual_edge']:.1f} percentage points "
        f"of yearly edge at a one-sided {pct(1 - pwr['one_sided_percentile'])} cutoff (`replay_06_statistics`). "
        "This is for a simple mean-return check, not the five marks. "
        "The slice cannot confirm a small edge. Even a pass here would be weak evidence.",
        "- UNKNOWN. Whether the same rules hold up through other regimes or on future practice fills.", "",
        "## What it means for T1 on VTI", "",
        f"- STATED. The practice desk uses T1 on VTI; G4 used the same {setup['trend_months']}-month idea on SPY "
        "and did not test T1 on VTI. "
        "G4's result is a warning about the trade-off, not a reason to count T1 as profitable, declare it broken "
        "or promote it beyond pretend money. Keep T1 as a forward control and judge it against holding VTI "
        "with the practice records and actual costs.", "",
        "## Rows to paste", "",
        "Status results table:", "", "```markdown", status, "```", "",
        "Queue Done table:", "", "```markdown", done, "```", "",
        "Generated by `research_rig/report_06.py` from `results_06.json`, `fund_coverage_06.json` "
        "and `fund_adjustments_06.json`. The report reads no market bars and runs no rule.", "",
    ]
    return "\n".join(t)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 if the page is missing or stale.")
    args = parser.parse_args()
    expected = render(*(json.loads((HERE / f).read_text()) for f in (
        "results_06.json", "fund_coverage_06.json", "fund_adjustments_06.json")))
    if args.check:
        if not OUT.is_file() or OUT.read_bytes() != expected.encode("utf-8"):
            print(f"Stale replay report: {OUT}", file=sys.stderr)
            return 1
    else:
        OUT.write_text(expected, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
