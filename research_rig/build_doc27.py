"""Writes docs/research/27_replay_07_intraday_spy_qqq.md from results_07.json. Runs no rule and reads no price.
Usage, from research_rig/: python3 build_doc27.py   (R07_FILE and R07_OUT override the input and output, for checking on the development output)"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("R07_FILE", os.path.join(HERE, "results_07.json"))
DST = os.environ.get("R07_OUT", os.path.join(HERE, "..", "docs", "research", "27_replay_07_intraday_spy_qqq.md"))
r = json.load(open(SRC)); S = r["symbols"]; RULES = ["N1", "N2", "N3", "N4", "N5", "N6", "N7", "N8"]
J = r["judged"]; C = r["costs"]; held = "dev" if r["dev_only"] else "held"; cfg = r["config"]
pc = lambda x: "n/a" if x is None else f"{x * 100:+.1f}%"
f2 = lambda x: "n/a" if x is None or x != x else f"{x:.2f}"
f3 = lambda x: "n/a" if x is None or x != x else f"{x:.3f}"
yn = lambda b: "pass" if b else "fail"
bps = lambda c: f"{c:g} bps"
LAB = {"low": "replay_07_costs.low_bps_per_side", "lower": "cost_model_bps_per_side_liquid_etf, lower end", "upper": "cost_model_bps_per_side_liquid_etf, upper end"}
def be_txt(b, key):
    x = b[key]
    if x["status"] == "below_at_zero": return "never ahead, even at 0"
    if x["status"] == "above_cap": return f"above {2 * x['bps']:g}"
    return f"{2 * x['bps']:.2f}"
L = []; w = L.append
w("# Replay 07: day trading rules on SPY and QQQ one-minute bars")
w("")
w(f"Written by `research_rig/build_doc27.py` from `research_rig/results_07.json`. Do not edit by hand. Every figure here is MEASURED by `research_rig/run_07.py` (run {r['run_utc']} UTC, command `{r['command']}`, code at commit {r['git']['commit'][:7]}" + (", with changes not yet committed: `run_07.py` was new and uncommitted when it ran, so the code that ran is the first committed version of `run_07.py`" if r['git'].get('code_changed_since_commit') else "") + f") unless it is labelled otherwise.")
w("")
w("Plan: `research_rig/PREREG_07_intraday_spy_qqq.md`, frozen and pushed before the run. Ledger rows 56 to 71 in `research_rig/TRIAL_LEDGER.md`. The held-back years were run once.")
w("")
w("Price source: " + r["price_source"] + ". Known gaps are in `docs/research/10_historical_data_and_practice.md`; the days this test did not use are counted below. There is no second price source, so there is no cross-check.")
w("")
w("Costs per side: " + ", ".join(f"{bps(C[k])} (`{LAB[k].split(',')[0]}`{', ' + LAB[k].split(', ')[1] if ',' in LAB[k] else ''})" for k in C) + f". Pass marks are judged at {bps(C['lower'])} and {bps(C['upper'])} only. Commission 0. Cash earns nothing. Long only, no leverage.")
w("")
w("## Result")
w("")
for s in S:
    p = [x for x in RULES if S[s]["passed_both_judged_costs"][x]]
    w(f"- {s}: {len(p)} of {len(RULES)} rules pass all five marks at both judged costs" + (f": {', '.join(p)}." if p else "."))
    for k in J:
        pk = [x for x in RULES if S[s]["costs"][k]["rules"][x]["marks"]["passed"]]
        w(f"- {s} at {bps(C[k])}: passes {', '.join(pk) if pk else 'none'}.")
w(f"- A pass means \"worth running on the practice desk\". It does not mean \"makes money\".")
w("")
w("## Days used")
w("")
w("| Fund | Used days | First result day | Last day | Early closes used | Days not used | Why not used |")
w("|---|---|---|---|---|---|---|")
for s, x in S.items():
    why = "; ".join(f"{k}: {v}" for k, v in sorted(x["days_not_used_by_reason"].items()))
    w(f"| {s} | {x['result_days']} | {x['first_result_day']} | {x['last_day']} | {x['early_close_days_used']} | {x['days_not_used']} | {why} |")
w("")
w(f"The first `replay_07_data` warm-up days of each fund are left out of every result. Check on the prices: N5 and N6 together match holding before costs to within a log gap of " + ", ".join(f"{x['n5_plus_n6_vs_hold_max_log_gap']:.1e} ({s})" for s, x in S.items()) + ".")
w("")
w(f"## Pass marks, {'development slice (this is a development output)' if r['dev_only'] else 'held-back slice for mark 1'}")
w("")
w("Mark 1 compares the rule with holding the same fund on the held-back slice (`replay_max_drop_ratio_vs_hold`). Mark 2 is the break-even cost against holding (`backtest_min_breakeven_cost_multiple`). Mark 3 is the deflated Sharpe ratio (`replay_min_deflated_sharpe`), count " + str(r["n_trials"]) + ". Mark 4 is the largest overfitting estimate over the fixed start dates (`backtest_max_pbo`). Mark 5 is shuffled timing (`replay_min_shuffle_percentile`). N5 and N6 cannot pass mark 5 by construction, as the plan says.")
w("")
for s, x in S.items():
    for k in J:
        co = x["costs"][k]; h = co["hold"][held]
        w(f"### {s} at {bps(C[k])} per side")
        w("")
        w("| Rule | Growth a year | Sharpe | Largest drop | Drop vs holding | Deflated Sharpe | Shuffle share beaten | 1 | 2 | 3 | 4 | 5 | All five |")
        w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        w(f"| Holding {s} | {pc(h['cagr'])} | {f2(h['sharpe'])} | {pc(h['maxdd'])} | | | | | | | | | |")
        for n in RULES:
            q = co["rules"][n]; m = q["marks"]; hh = q[held]
            w(f"| {n} | {pc(hh['cagr'])} | {f2(hh['sharpe'])} | {pc(hh['maxdd'])} | {f2(q['dd_ratio_vs_hold'])} | {f3(q['dsr'])} | {f3(q['shuffle_pct'])} | {yn(m['m1'])} | {yn(m['m2'])} | {yn(m['m3'])} | {yn(m['m4'])} | {yn(m['m5'])} | {yn(m['passed'])} |")
        w("")
        w(f"Mark 4, overfitting estimate by start date: " + ", ".join(f"{d}: {f3(v['pbo'])}" for d, v in co["pbo_by_start"].items()) + f". Largest {f3(co['pbo_largest'])}. Mark 3 spread per day, all counted trials: {co['spread_per_day_all_counted']:.4f}; this plan's 16 alone: {co['spread_per_day_these_16']:.4f}.")
        w("")
w("## Break-even cost")
w("")
w(f"Round trip in bps (two sides), whole sample. Against holding: the first cost where the rule's Sharpe ratio stops being above holding's, holding paying the same cost. Against zero: the first cost where the average daily return stops being above zero. Set beside `intraday_trend_max_round_trip_bps` = {cfg['intraday_trend_max_round_trip_bps']} bps.")
w("")
w("| Fund | Rule | Against holding | Against zero |")
w("|---|---|---|---|")
for s, x in S.items():
    for n in RULES:
        b = x["breakeven"][n]; w(f"| {s} | {n} | {be_txt(b, 'vs_hold_per_side')} | {be_txt(b, 'vs_zero_per_side')} |")
w("")
sl = ["dev", "held", "post", "all"] if not r["dev_only"] else ["dev", "all"]
SLN = {"dev": "development", "held": "held back", "post": "after the cutoff", "all": "whole"}
w("## Growth a year by slice")
w("")
for k in C:
    w(f"### At {bps(C[k])} per side")
    w("")
    w("| Fund | Rule | " + " | ".join(f"{SLN[z]}: growth, Sharpe" for z in sl) + " |")
    w("|---|---|" + "---|" * len(sl))
    for s, x in S.items():
        co = x["costs"][k]
        w(f"| {s} | Holding | " + " | ".join(f"{pc(co['hold'][z]['cagr'])}, {f2(co['hold'][z]['sharpe'])}" for z in sl) + " |")
        for n in RULES:
            q = co["rules"][n]; w(f"| {s} | {n} | " + " | ".join(f"{pc(q[z]['cagr'])}, {f2(q[z]['sharpe'])}" for z in sl) + " |")
    w("")
w("The slice after the cutoff is a few months long, so its growth a year is a short sample stretched to a year.")
w("")
w("## Trades and the best days")
w("")
k0 = J[0]
w(f"Whole sample at {bps(C[k0])}. The share of the log growth from the best 10 days is shown only where the whole-sample growth is above zero.")
w("")
w("| Fund | Rule | Trades | Share of days with a trade | Share of log growth from the best 10 days |")
w("|---|---|---|---|---|")
for s, x in S.items():
    for n in RULES:
        q = x["costs"][k0]["rules"][n]; b10 = q["best10_share_of_log_growth"]
        w(f"| {s} | {n} | {q['trades_whole']} | {q['share_of_days_with_a_trade']:.2f} | {'n/a' if b10 is None else f'{b10:.2f}'} |")
w("")
w("## Sensitivities, reported and not judged")
w("")
w(f"At {bps(C[k0])}. One minute later: every fill at a minute's open moved one minute later. N1 extra stop cost: every stop pays one more cost.")
w("")
w(f"| Fund | Rule | {SLN[held]}: Sharpe as run | {SLN[held]}: Sharpe one minute later | whole: Sharpe as run | whole: Sharpe one minute later |")
w("|---|---|---|---|---|---|")
for s, x in S.items():
    for n in RULES:
        q = x["costs"][k0]["rules"][n]; w(f"| {s} | {n} | {f2(q[held]['sharpe'])} | {f2(q['lag1'][held]['sharpe'])} | {f2(q['all']['sharpe'])} | {f2(q['lag1']['all']['sharpe'])} |")
w("")
for s, x in S.items():
    q = x["costs"][k0]["rules"]["N1"]; w(f"- {s} N1 with one more cost per stop: whole-sample Sharpe {f2(q['stop_extra_cost']['all']['sharpe'])}, growth a year {pc(q['stop_extra_cost']['all']['cagr'])}.")
w("")
w("## Year by year")
w("")
w(f"Growth in each calendar year at {bps(C[k0])}. The first and last years are part years.")
w("")
for s, x in S.items():
    co = x["costs"][k0]; ys = sorted(co["hold_yearly"], key=int)
    w(f"### {s}")
    w("")
    w("| Year | Holding | " + " | ".join(RULES) + " |")
    w("|---|---|" + "---|" * len(RULES))
    for y in ys:
        w(f"| {y} | {pc(co['hold_yearly'][y])} | " + " | ".join(pc(co["rules"][n]["yearly"][y]) for n in RULES) + " |")
    w("")
w("## What this does and does not show")
w("")
w("- MEASURED: the figures above, on this price source, with the fills and costs of the plan.")
w("- UNKNOWN: whether the prices are adjusted for dividends. If they are not, holding the fund and N5 both miss the dividend, about the fund's yield a year, and the day-only rules miss nothing. That favours the day-only rules against holding in marks 1 and 2.")
w("- UNKNOWN: the stock calendar, written from memory. Days whose bars did not match it were not used.")
w("- UNKNOWN: whether the one-minute prices are right on the days used. Days whose one-minute range or last close disagreed with the daily file by more than `replay_07_data` allows were not used. A wrong price inside the range would not be found.")
w("- Not tested: real fills. The costs are assumed, not measured on SPY or QQQ. Market-on-close and opening fills are taken at the bar prices.")
w("- Not tested: shorting, leverage and volatility sizing, which the papers' headline numbers use.")
w("")
open(DST, "w").write("\n".join(L) + "\n"); print("wrote", DST)
