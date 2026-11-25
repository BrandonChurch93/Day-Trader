"""Writes docs/research/54_replay_13_year_or_method.md from results_13.json. Reads no price. Free to rerun."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "results_13.json")))
P = R["parameters"]; Y = R["years"]; J = R["judgment"]
OUT = os.path.join(HERE, "..", "docs", "research", "54_replay_13_year_or_method.md")

def pct(x): return f"{x*100:+,.1f}%"
def cell(d, k="gain"): return pct(d[k])
def cost_key(name, c): return name if c == P["cost_bps_per_side"] else f"{name}_cost_{c}"
FIND = {"supported": "supported: the method, not the year", "paid only when coins rose": "paid only when coins rose: the year",
        "not paid": "not paid"}

L = []
L.append("# 54. Replay 13: the owner's method as a fixed rule, year by year 2020 to 2026")
L.append("")
L.append(f"Status: research result, pretend trades on past prices, run once {R['job']['run_started_utc'][:16].replace('T', ' ')} UTC against commit {R['job']['git_head'][:7]}. Built by `research_rig/report_13.py` from `research_rig/results_13.json`. The plan is `research_rig/PREREG_13_year_or_method.md`; its numbers are in the config key `replay_13_plan`. Ledger rows 144 and 145.")
L.append("")
L.append("Labels: MEASURED means computed from the stored result file. Every figure below is MEASURED unless marked.")
L.append("")
L.append("## What was asked")
L.append("")
L.append("The owner made money in 2021 buying dips and selling peaks on the coins people were chasing. Was it the method or the year? Two fixed rules were run on every year from 2020, each year starting again from 1.00, on hourly Binance prices, with the coin list taken from each month's ranking at the time so that dead coins are in.")
L.append("")
L.append(f"- Each Monday the hot five are the {P['hot_n']} coins with the largest {P['rise_days']}-day gain among the first {P['universe_top_n']} by size (bitcoin, ether, dollar-tied, gold-backed, wrapped and exchange coins left out).")
L.append("- Rule A: buy the hot five in equal parts and hold them for the week.")
L.append(f"- Rule B: on the hot five, buy a coin when its hourly close is {P['dip_pct']}% or more below its highest close of the last {P['dip_lookback_hours']} hours and still above its close {P['rise_days']} days ago; sell at +{P['take_pct']}%, at -{P['stop_pct']}%, or after {P['max_hold_hours']} hours.")
L.append(f"- Cost {P['cost_bps_per_side']} bps a side, judged. No leverage, judged. Fills at the next hour's open.")
L.append("- Yardsticks: every rankable coin held in equal parts; the same rule on five coins drawn at random each Monday (" + str(P["random_draws"]) + f" paths, the {P['random_percentile']}th percentile); bitcoin held, for scale.")
L.append("")
L.append("## The finding")
L.append("")
for k, name in (("B", "Rule B, the dip-and-peak rule (the nearer of the two to what the owner did)"), ("A", "Rule A, holding the hot five for the week")):
    j = J[k]
    L.append(f"- {name}: {FIND.get(j['finding'], j['finding'])}. Above all coins in {len(j['above_all'])} of {len(j['eligible'])} years ({', '.join(j['above_all']) or 'none'}); also above the random mark in {len(j['above_both'])} ({', '.join(j['above_both']) or 'none'}); of those, years in which all coins fell: {', '.join(j['above_both_falling']) or 'none'}. The mark was at least {P['min_years_above']} years with at least one falling year.")
L.append("")
L.append("A support means worth a time machine test and then the practice desk. It does not mean it makes money.")
L.append("")
L.append(f"## Each year at the judged cost ({P['cost_bps_per_side']} bps a side, no leverage)")
L.append("")
L.append("| Year | Rule A | Rule B | All coins held | Random five, rule A mark | Random five, rule B mark | Bitcoin held | Rule B trades | Rule B share stopped out |")
L.append("|---|---|---|---|---|---|---|---|---|")
for y in sorted(Y):
    f = Y[y]["fixed"]; r = Y[y]["random"]
    L.append(f"| {y} | {cell(f['A'])} | {cell(f['B'])} | {cell(f['all'])} | {pct(r['A']['percentile'])} | {pct(r['B']['percentile'])} | {pct(Y[y]['BTC']['net'])} | {f['B']['trades']:,} | {f['B']['stop_share']*100:.0f}% |")
L.append("")
L.append("2026 runs to 2026-11-23. Each year starts at its first Monday.")
L.append("")
L.append("## Other cost levels, shown and not judged")
L.append("")
L.append("| Year | " + " | ".join(f"Rule A at {c} bps | Rule B at {c} bps | All coins at {c} bps" for c in P["other_costs_bps"]) + f" | Rule B at {P['shown_leverage']}x, {P['cost_bps_per_side']} bps |")
L.append("|---|" + "---|" * (3 * len(P["other_costs_bps"]) + 1))
for y in sorted(Y):
    f = Y[y]["fixed"]
    L.append(f"| {y} | " + " | ".join(f"{cell(f[cost_key('A', c)])} | {cell(f[cost_key('B', c)])} | {cell(f[cost_key('all', c)])}" for c in P["other_costs_bps"]) + f" | {cell(f['B_leveraged'])} |")
L.append("")
L.append("## How rule B's trades ended")
L.append("")
L.append("| Year | Take | Stop | Time limit | Week end | Flagged part-weeks, rule A | Flagged part-weeks, rule B |")
L.append("|---|---|---|---|---|---|---|")
for y in sorted(Y):
    f = Y[y]["fixed"]; q = f["B"]["reasons"]
    L.append(f"| {y} | {q.get('take', 0):,} | {q.get('stop', 0):,} | {q.get('timeout', 0):,} | {q.get('week_end', 0):,} | {f['A']['flagged_share_pct']:.1f}% | {f['B']['flagged_share_pct']:.1f}% |")
L.append("")
L.append(f"A year with more than {P['max_flagged_share_pct']}% flagged cannot count. Years that could count: rule A {', '.join(J['A']['eligible'])}; rule B {', '.join(J['B']['eligible'])}.")
L.append("")
lossA = [y for y in sorted(Y) if Y[y]["fixed"]["A"]["gain"] < 0]
btcA = [y for y in sorted(Y) if Y[y]["fixed"]["A"]["gain"] > Y[y]["BTC"]["net"]]
lossB = [y for y in sorted(Y) if Y[y]["fixed"]["B"]["gain"] < 0]
allB5 = [y for y in sorted(Y) if Y[y]["fixed"]["B_cost_5"]["gain"] > Y[y]["fixed"]["all_cost_5"]["gain"]]
L.append("## Reading the result")
L.append("")
L.append(f"- Rule B lost money in {len(lossB)} of {len(Y)} years ({', '.join(lossB)}), 2021 among them: in the year coins rose most, selling every 5% gain gave the rise away and the trading costs took the rest. At the lowest cost shown it still ended below all coins held in every year but {', '.join(allB5) or 'none'}. At 3x it was close to a total loss in most years. So the fixed dip-and-peak rule does not explain the owner's 2021. What is left are the things the rule does not have: the year itself, the choice of coins, leverage on a rising market, and judgment.")
L.append(f"- Rule A met the marks set before the run, and that needs care. The marks compare it with the average coin, and the average coin was a poor thing to hold after 2021. Rule A still ended {len(lossA)} of {len(Y)} years with a loss ({', '.join(lossA)}) and ended above bitcoin held only in {', '.join(btcA) or 'no year'}. In 2020 and 2021 it was only a little above the random-five mark. In the latest year, 2026, it was well below every yardstick.")
L.append("- What the result does show: last week's hottest coins did somewhat better than the average coin in five of seven years, two falling years among them. That is a lean, not a method. Held long by itself it rides the whole coin market up and down.")
L.append("- What follows, as new plans with their own ledger rows and not as a reading of this one: the hot five against the rest of the market with the market's own move taken out, which needs short positions on futures; and the hot five only while the market as a whole is rising.")
L.append("")
L.append("## What this does not cover")
L.append("")
L.append("- Rule B is a fixed rule with round numbers. It is not the owner's eye for a chart. It answers whether buying 5% dips on rising coins and selling 5% up was paid by itself.")
L.append("- Hot here means last week's price gain. It does not use what people were talking about.")
L.append("- One venue's prices (Binance), hourly. Coins it did not list are missing from the list and counted in the result file. The cost is a flat figure, not a measured spread for each coin in each year; small coins in 2020 and 2021 may have cost more.")
L.append("- Each year stands alone from 1.00; nothing is carried from year to year.")
L.append("- Rule A's support comes from one run of one set of round numbers on seven years. Seven years is a small sample. It has not been tried on prices it has not seen, because every year was used here.")
L.append("- The 3x column closes a position at a total loss of its part when the price falls " + str(P["liquidation_drop_pct"]) + "% below entry. It is a simulation and not any venue's margin rules.")
L.append("")
open(OUT, "w").write("\n".join(L))
print("wrote docs/research/54_replay_13_year_or_method.md")
