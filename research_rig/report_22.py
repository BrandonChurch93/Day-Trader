"""Build Replay 22's report from the pinned saved aggregate; never score or read market inputs.

Run: python3 research_rig/report_22.py [--result PATH] [--output PATH]
Reads only the saved aggregate results_22.json (pinned by SHA-256), the replay_22_plan block of
config/thresholds.yaml, research_rig/APPROVAL_22.md for the freeze commit, and the two pre-run calibration
files on planted paths (pinned by SHA-256). It never runs score_22.py and never opens a price archive.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

import yaml

ROOT = Path(__file__).resolve().parent.parent
RESULT = Path("/home/user/workspace/rig/data/replay_22/results_22.json")
TARGET = ROOT / "docs/research/137_replay_22_fable_rule_a.md"
RESULT_SHA = "0529b20bf2c0430a149be0179ea0f2662f7e7050288cad589ec59f8fb6f4717f"
CALIBRATION = {
    "lasting": (ROOT / "research_rig/calibration_22.json", "97d060af4d8ff1a7330bb9609e55d35a0e1c1c014d264f075acb84cbd0387bf7"),
    "fading": (ROOT / "research_rig/calibration_timing_22.json", "1444af07ce9f48c168f6cbc46caf21805b44d3b1f3f9bc2fe1c759f02eed5269"),
}
APPROVAL = ROOT / "research_rig/APPROVAL_22.md"
# Independent recompute: a second helper's own code written from the plan text, saved off the repo and
# fixed on disk (11:29:50 UTC) before it opened the scored result. Aggregates only.
RECOMPUTE = Path("/home/user/workspace/rig/data/replay_22_notes/recompute_22.json")
RECOMPUTE_SHA = "eb53c35924329360027e134fde81371491a2e6962077eebbc362192da3a594d2"
RECOMPUTE_FIXED = "2026-11-26 11:29:50 UTC"
# STATED by the lead agent: the saved aggregate holds no run clock.
RUN_WINDOW = ("2026-11-26 11:21:18 UTC", "2026-11-26 11:22:26 UTC")
PLAN_PATH = "../../research_rig/PREREG_22_fable_rule_a.md"


def read_result(path):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != RESULT_SHA:
        raise ValueError("Replay 22 saved result does not match its SHA-256")
    return json.loads(raw)


def read_recompute():
    raw = RECOMPUTE.read_bytes()
    if sha256(raw).hexdigest() != RECOMPUTE_SHA:
        raise ValueError("Replay 22 recompute does not match its SHA-256")
    return json.loads(raw)


def recompute_lines(j, cfg, cost, rc):
    rule, hold, tw = j["rule_a"][cost], j["hold"][cost], j["twins"]
    pairs = [(rc["rule"]["end"], rule["final"]), (rc["hold"]["end"], hold["final"]),
             (rc["rule"]["sharpe"], rule["sharpe"]), (rc["hold"]["sharpe"], hold["sharpe"]),
             (rc["rule"]["max_drawdown"], rule["max_drawdown"]), (rc["hold"]["max_drawdown"], hold["max_drawdown"])]
    pairs += [(rc[k]["by_year"][y], v) for k, side in (("rule", rule), ("hold", hold)) for y, v in side["by_year"].items()]
    gap = max(abs(a - b) for a, b in pairs)
    if gap > 1e-9 or rc["trade_count"] != j["trades"] or rc["rule"]["positive_years"] != rule["positive_years"]:
        raise ValueError("recompute no longer agrees with the scored result; rewrite this section by hand")
    names = {"beats_hold": "beats_hold", "sharpe": "sharpe", "drawdown": "drawdown", "twins": "twins", "positive_years": "years"}
    if any(rc["marks"][a] != j["judge"]["tests"][b] for a, b in names.items()) or rc["passed"] != j["judge"]["pass"]:
        raise ValueError("recompute marks differ from the scored result; rewrite this section by hand")
    return "\n".join([
        f"- MEASURED. A second helper rebuilt the judged numbers with its own code, written from the plan text without reading the scorer. Its numbers were fixed on disk at {RECOMPUTE_FIXED}, before it opened the scored result (SHA-256 `{RECOMPUTE_SHA}`). It checked all {rc['archives_verified']:,} input archives against the manifest.",
        f"- MEASURED. All five marks agree, and the overall verdict agrees: did not pass.",
        f"- MEASURED. Rule and same-list hold end values, daily Sharpe, largest fall and all {len(rule['by_year'])} yearly figures on both sides agree to within {gap:.0e}. Trades: {rc['trade_count']} in both. Positive years: {rc['rule']['positive_years']} in both.",
        f"- MEASURED. The random twins differ a little, as expected: twin median {rc['twins']['median']:.2f} times the start against {tw['median']:.2f}, 95th percentile {rc['twins']['p95']:.2f} against {tw['cut']:.2f}, entries not placed {rc['twins']['dropped_entries']} against {tw['counts']['twin_entries_not_placed']}. The rule's {rule['final']:.2f} is under both cuts, so the mark is the same either way.",
        "- STATED by the helper. The plan names the twin seed but not the random generator, the draw order or the percentile method, so the twin stream could not be rebuilt exactly. UNKNOWN which of those causes the gap.",
        f"- UNKNOWN from the recompute. It did not work out the share of twins at or above the rule ({j['twins']['share_at_or_above_rule']:.0%} in the scored run), or any shown-only line.",
    ])


def read_calibration():
    out = {}
    for name, (path, pin) in CALIBRATION.items():
        raw = path.read_bytes()
        if sha256(raw).hexdigest() != pin:
            raise ValueError(f"Replay 22 calibration file {path.name} does not match its SHA-256")
        out[name] = json.loads(raw)
    return out


def plan():
    return yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())["replay_22_plan"]["value"]


def pct(x, d=2):
    return f"{x * 100:+,.{d}f}%"


def plain_pct(x, d=2):
    return f"{x * 100:,.{d}f}%"


def total(final):
    return pct(final - 1)


def share(x):
    return f"{x:.2f}"


def table(head, rows):
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in (head, ("---",) * len(head), *rows))


def render(data, cfg, calib, freeze):
    j, s = data["judged"], data["source_months_shown_only"]
    c = cfg["judged_cost_bps"]
    rule, hold, tw, judge = j["rule_a"][str(c)], j["hold"][str(c)], j["twins"], j["judge"]
    years = sorted(rule["by_year"])
    last = years[-1]
    n_years = len(years)
    marks = {
        "beats_hold": ("Beats holding", "End value above holding the same list in equal weights, same costs",
                       f"{total(rule['final'])} against {total(hold['final'])}", rule["final"] > hold["final"]),
        "sharpe": ("Daily Sharpe", f"At least {cfg['min_sharpe']:.1f}", f"{rule['sharpe']:.2f}", rule["sharpe"] >= cfg["min_sharpe"]),
        "drawdown": ("Largest fall", f"{plain_pct(cfg['max_drawdown'], 0)} or less", plain_pct(rule["max_drawdown"]),
                     rule["max_drawdown"] <= cfg["max_drawdown"]),
        "twins": ("Random twins", f"End value above the {cfg['twin_percentile']:.0f}th percentile of {cfg['twins']} random-entry twins",
                  f"{total(rule['final'])} against {total(tw['cut'])}; {plain_pct(tw['share_at_or_above_rule'], 0)} of twins at or above the rule",
                  rule["final"] > tw["cut"]),
        "years": ("Positive years", f"At least {cfg['min_positive_years']} of {n_years} calendar years ({last} to March)",
                  f"{rule['positive_years']} of {n_years}", rule["positive_years"] >= cfg["min_positive_years"]),
    }
    met = sum(v[-1] for v in marks.values())
    stated_pos = sum(rule["by_year"][y] > 0 for y in years)
    wb = j["without_best"]
    if (data["plan"] != 22 or set(judge["tests"]) != set(marks) or any(judge["tests"][k] != v[-1] for k, v in marks.items())
            or judge["pass"] is not all(judge["tests"].values()) or judge["pass"] or judge["twin_cut"] != tw["cut"]
            or tw["n"] != cfg["twins"] or rule["years"] != n_years or stated_pos != rule["positive_years"]
            or sorted(j["rule_a"]) != sorted(map(str, [c, *cfg["shown_cost_bps"]]))
            or sum(j["exit_reasons"].values()) != j["trades"] or not wb["final"] < 1):
        raise ValueError("Replay 22 saved aggregates and frozen marks do not reconcile")
    # The plain-words reading below must stay true of the numbers it describes.
    if not (abs(rule["final"] / hold["final"] - 1) < .05 and abs(rule["max_drawdown"] - hold["max_drawdown"]) < .10
            and tw["share_at_or_above_rule"] >= .5):
        raise ValueError("Replay 22 plain reading no longer fits the saved aggregates")
    gaps, hg = rule["gaps"], hold["gaps"]
    v = data["validation_counts"]["judged"]
    absent = data["absent_days"]
    entries = cfg["twins"] * j["trades"]
    shown_costs = [b for b in cfg["shown_cost_bps"]]
    lasting, fading = (calib[k]["edges_pct"] for k in ("lasting", "fading"))
    top = str(max(cfg["calibration_edges_pct"]))
    zero = "0"
    if lasting[zero]["pass_share"] != fading[zero]["pass_share"]:
        raise ValueError("Replay 22 calibration files disagree on the no-edge case")
    reasons = {"close_under_level": "daily close under the breakout level", "stall": "stall exit",
               "left_list": "left the list", "window_end": "still held at the end of the window"}
    sr = s["rule_a"][str(c)]
    cut = "Cannot count toward a mark."
    return "\n\n".join([
        f"# Replay {data['plan']}. Fable rule A, no AI",
        "## The rule",
        "\n".join([
            f"- STATED, from the [frozen plan]({PLAN_PATH}). Rule A was read off the Fable 5.2 picker's notes and run here as a fixed rule, with no AI, on the monthly top {cfg['top_rank']} coins.",
            f"- STATED. Wake once a day at {cfg['wake_hour_utc']}:00 UTC. A coin signals when its last hourly close is above the highest hourly high of the {cfg['range_days']} full days before and was not above it at the last wake, is at most {cfg['max_above_level_pct']:g}% above that level, on a volume ratio of {cfg['min_volume_ratio']:g} or more.",
            f"- STATED. Buy at the next hourly open. Hold at most {cfg['max_names']} names, each reset to 1 over the larger of {cfg['min_parts']} and the names held. The rest is cash at zero yield.",
            f"- STATED. Sell when a daily close falls under the breakout level, or after {cfg['stall_days']} days with no new high while the volume ratio is under {cfg['stall_volume_ratio']:g}.",
            f"- STATED. Judged from {cfg['judged_start']} to {cfg['judged_end']} (end not included) at {c} bp a side, against holding the same list in equal weights at the same cost.",
        ]),
        "## Did it pass?",
        f"MEASURED. Did not pass, **{met} of {len(marks)} frozen marks**, in the one scored run, started {RUN_WINDOW[0]}. "
        f"Only the mark against holding was met, and only just: the rule ended at {total(rule['final'])} and holding the same coins at {total(hold['final'])}. "
        f"Its daily Sharpe was {rule['sharpe']:.2f}, its largest fall {plain_pct(rule['max_drawdown'])}, it was positive in {rule['positive_years']} of {n_years} years, "
        f"and {plain_pct(tw['share_at_or_above_rule'], 0)} of the random-entry twins ended at or above it. The row closes.",
        "## Frozen marks",
        f"MEASURED at the judged cost of {c} bp a side. All five were required. End values are total returns over the judged window.",
        table(("Mark", "Frozen bar", "Measured", "Verdict"),
              [(label, bar, value, "met" if ok else "not met") for label, bar, value, ok in marks.values()]),
        "## By year",
        f"MEASURED at {c} bp a side. Each year runs from its 1 January mark to the next. {last} runs to 1 April only.",
        table(("Year", "Rule A", "Same-list hold"),
              [(y + (" (to March)" if y == last else ""), pct(rule["by_year"][y]), pct(hold["by_year"][y])) for y in years]),
        "## Shown only",
        "MEASURED. Each line below was named in the plan as shown only. None of them can count toward a mark.",
        "\n".join([
            f"- Bitcoin held over the judged window: {total(j['btc_held']['final'])}, largest fall {plain_pct(j['btc_held']['max_drawdown'])}, daily Sharpe {j['btc_held']['sharpe']:.2f}. {cut}",
            f"- Time in cash: {plain_pct(j['time_in_cash'])} of judged wakes with no name held. {cut}",
            f"- Trades: {j['trades']} in all, {j['trades_per_year']:.1f} a year. {cut}",
            "- Exit reasons: " + "; ".join(f"{reasons.get(k, k)} {n}" for k, n in sorted(j["exit_reasons"].items(), key=lambda x: -x[1])) + f". {cut}",
            f"- Without the best {cfg['drop_best']} trades: {total(wb['final'])}, largest fall {plain_pct(wb['max_drawdown'])}, positive in {wb['positive_years']} of {wb['years']} years. {cut}",
            f"- Rule A with the rule C cash switch: {total(j['rule_a_with_c']['final'])}, largest fall {plain_pct(j['rule_a_with_c']['max_drawdown'])}, daily Sharpe {j['rule_a_with_c']['sharpe']:.2f}, positive in {j['rule_a_with_c']['positive_years']} of {j['rule_a_with_c']['years']} years. The switch was off at {j['btc_switch_off_wakes']:,} of {v['wakes']:,} wakes; {j['counts']['btc_switch_unreadable']} wakes could not read it. {cut}",
            f"- Shorter exit (no new high in {cfg['stall_days']} days, without the volume condition): {total(j['rule_a_short_exit']['final'])}, largest fall {plain_pct(j['rule_a_short_exit']['max_drawdown'])}. {cut}",
            *[f"- Cost at {b} bp a side: rule {total(j['rule_a'][str(b)]['final'])}, same-list hold {total(j['hold'][str(b)]['final'])}. {cut}" for b in shown_costs],
            f"- The months the rule came from, {cfg['shown_start']} to {cfg['shown_end']}, a fresh account at {c} bp: rule {total(sr['final'])}, same-list hold {total(s['hold'][str(c)]['final'])}, "
            f"Bitcoin held {total(s['btc_held']['final'])}; {s['trades']} trades, {plain_pct(s['time_in_cash'])} of wakes in cash, "
            f"{total(s['without_best']['final'])} without the best {cfg['drop_best']} trades. {cut}",
        ]),
        "## Gaps",
        "\n".join([
            f"- MEASURED. Held hours without a bar: {gaps['held_hours_without_bar']} for the rule, {hg['held_hours_without_bar']} for the same-list hold.",
            f"- MEASURED. Stale marks (a daily mark on an old close): {gaps['stale_mark_values']} for the rule, {hg['stale_mark_values']} for the hold. Positions closed at their last bar: {gaps['closed_at_last_bar']} and {hg['closed_at_last_bar']}.",
            f"- MEASURED. Coin-wakes not tradable because the spot identity was not confirmed: {j['counts']['coin_wakes_not_confirmed']:,} of {j['counts']['coin_wakes_listed']:,} listed coin-wakes. Without a pair segment: {j['counts']['coin_wakes_no_pair_segment']}. With a missing hour, so no signal could be read: {j['counts']['signal_incomplete']:,}.",
            f"- MEASURED. Listed coins with no Binance pair: {len(data['no_binance_pair']) or 'none'}" + (f" ({', '.join(data['no_binance_pair'])})." if data["no_binance_pair"] else "."),
            f"- MEASURED. Pair-days absent from the archive: {sum(map(len, absent.values())):,} across {len(absent)} pairs ({', '.join(sorted(absent))}). Bitcoin had {data['validation_counts']['btc_missing_hours']} missing hours.",
            f"- MEASURED. Twin entries not placed after {cfg['twin_max_draws']:,} draws: {tw['counts']['twin_entries_not_placed']} of {entries:,} ({cfg['twins']} twins times {j['trades']} trades).",
            f"- MEASURED on planted paths before the run. Power was low. With a true {top}% edge the five marks passed in {share(lasting[top]['pass_share'])} of seeds when the gain lasted and {share(fading[top]['pass_share'])} when it faded; with no edge, in {share(lasting[zero]['pass_share'])}. So a fail says little about a small edge.",
            "- UNKNOWN. How many dead coins the saved list pages left out. The result covers the tradable subset that could be rebuilt.",
            "- STATED. The rule's shape came from eight months of one agent's notes. The judged window is outside those months.",
        ]),
        "## What it means",
        f"MEASURED. The rule ended about level with holding the same coins ({total(rule['final'])} against {total(hold['final'])}) "
        f"and fell about as far as they did ({plain_pct(rule['max_drawdown'])} against {plain_pct(hold['max_drawdown'])}). "
        f"{plain_pct(tw['share_at_or_above_rule'], 0)} of random-entry twins did as well or better, so on these marks it cannot be told apart from random entries. "
        f"Without its best {cfg['drop_best']} trades it lost money ({total(wb['final'])}). STATED. The row closes.",
        "## Independent recompute",
        recompute_lines(j, cfg, str(c), read_recompute()),
        "## Run record",
        "\n".join([
            f"- STATED by the lead agent. Scored exactly once, from {RUN_WINDOW[0]} to {RUN_WINDOW[1]}, exit 0. Ledger 159, queue 40.",
            f"- MEASURED. Freeze: `{freeze}`.",
            f"- MEASURED. Scoring approval: `{data['approval_commit']}`.",
            f"- MEASURED. Saved aggregate result SHA-256: `{RESULT_SHA}`.",
        ]),
    ]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, default=RESULT)
    parser.add_argument("--output", type=Path, default=TARGET)
    args = parser.parse_args()
    freeze = re.search(r"freeze commit ([0-9a-f]{40})\.", APPROVAL.read_text())[1]
    args.output.write_text(render(read_result(args.result), plan(), read_calibration(), freeze), encoding="utf-8")


if __name__ == "__main__":
    main()
