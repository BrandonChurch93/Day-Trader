"""Builds docs/research/22_replay_05_stock_trend.md from results_05.json. Run after run_05.py."""
import json
r = json.load(open("results_05.json")); TH = r["thresholds"]; C = r["costs"]; L = ["low", "base", "high"]; N = list(C["base"]["rules"])
NAME = {"T1": "Ten-month rule", "T2": "200-day rule", "T3": "Twelve-month momentum", "T4": "Four-average ensemble (P1)", "T5": "Trendpilot, first version", "V1": "Size by volatility, no trend",
        "I1": "Twelve industries, each on the ten-month rule", "I2": "Top three industries with a market filter"}
BEN = {n: ("HOLD12" if n == "I1" else "HOLD") for n in N}; BN = {"HOLD": "Hold the market", "HOLD12": "Hold the twelve industries"}
pc = lambda x, d=1: f"{x*100:+.{d}f}%"; yn = lambda b: "PASS" if b else "fail"; MK = ["m1", "m2", "m3", "m4", "m5"]
def be(x): return "never ahead" if x["status"] == "below_at_zero" else ("above 2,560 bps" if x["status"] == "above_cap" else f"{x['bps']:.0f} bps")
def slice_tab(lab, sl):
    o = C[lab]; t = "| Rule | Growth a year | Sharpe above bills | Largest drop | Average share in stocks | Trade sides a year |\n|---|---|---|---|---|---|\n"
    for b in ("HOLD", "HOLD12"):
        m = o["bench"][b][sl]; t += f"| {BN[b]} | {pc(m['cagr'])} | {m['sharpe']:.2f} | {pc(m['maxdd'])} | 100% | |\n"
    for n in N:
        m = o["rules"][n][sl]; yrs = m["n"] / 252
        t += f"| {n}. {NAME[n]} | {pc(m['cagr'])} | {m['sharpe']:.2f} | {pc(m['maxdd'])} | {m['avg_weight']*100:.0f}% | {m['sides']/yrs:.1f} |\n"
    return t
def marks_tab():
    t = "| Rule | Cost per side | 1 held-back | 2 break-even | 3 deflated Sharpe | 4 overfitting | 5 shuffle | Verdict | Beat the fixed mix on the held-back slice |\n|---|---|---|---|---|---|---|---|---|\n"
    for n in N:
        for lab in L:
            x = C[lab]["rules"][n]; m = x["marks"]
            t += f"| {n} | {C[lab]['cost_bps_per_side']} bps | " + " | ".join(yn(m[k]) for k in MK) + f" | {yn(m['passed'])} | {'yes' if x['beats_fixed_mix_held'] else 'no'} |\n"
    return t
def detail_tab(lab):
    o = C[lab]; t = "| Rule | Held-back Sharpe, rule | Comparison | Drop as a share of the comparison's | Break-even cost per side | Deflated Sharpe | Share of shuffles beaten | Fixed mix: share in stocks | Fixed mix: held-back Sharpe | Fixed mix: largest drop |\n|---|---|---|---|---|---|---|---|---|---|\n"
    for n in N:
        x = o["rules"][n]; b = o["bench"][BEN[n]]["held"]; f = x["fixed_mix"]
        t += f"| {n} | {x['held']['sharpe']:.2f} | {b['sharpe']:.2f} | {x['dd_ratio']*100:.0f}% | {be(r['breakeven'][n]['vs_bench'])} | {x['dsr']:.3f} | {x['shuffle_pct']*100:.1f}% | {f['weight']*100:.0f}% | {f['held']['sharpe']:.2f} | {pc(f['held']['maxdd'])} |\n"
    return t
def years_tab(lab):
    o = C[lab]; t = "| Rule | 2008 | 2020 | 2022 | Largest drop in 2008 | Largest drop in 2020 | Largest drop in 2022 |\n|---|---|---|---|---|---|---|\n"
    m = o["bench"]["HOLD"]; t += f"| Hold the market | {pc(m['y2008']['total'])} | {pc(m['y2020']['total'])} | {pc(m['y2022']['total'])} | {pc(m['y2008']['maxdd'])} | {pc(m['y2020']['maxdd'])} | {pc(m['y2022']['maxdd'])} |\n"
    for n in N:
        m = o["rules"][n]; t += f"| {n} | {pc(m['y2008']['total'])} | {pc(m['y2020']['total'])} | {pc(m['y2022']['total'])} | {pc(m['y2008']['maxdd'])} | {pc(m['y2020']['maxdd'])} | {pc(m['y2022']['maxdd'])} |\n"
    return t
def sens_tab(lab):
    o = C[lab]; t = "| Rule | Held-back Sharpe as tested | Traded the same close | Cash earns nothing |\n|---|---|---|---|\n"
    for n in N:
        x = o["rules"][n]; t += f"| {n} | {x['held']['sharpe']:.2f} | {x['same_close']['held']['sharpe']:.2f} | {x['cash_earns_nothing']['held']['sharpe']:.2f} |\n"
    return t
P = {lab: [n for n in N if C[lab]["rules"][n]["marks"]["passed"]] for lab in L}; b = C["base"]; hb = b["bench"]["HOLD"]["held"]; ha = b["bench"]["HOLD"]["all"]
more = [n for n in N if b["rules"][n]["held"]["cagr"] > b["bench"][BEN[n]]["held"]["cagr"]]
m1 = [n for n in N if b["rules"][n]["marks"]["m1"]]; fm = [n for n in N if b["rules"][n]["beats_fixed_mix_held"]]
better_sh = [n for n in N if b["rules"][n]["held"]["sharpe"] > b["bench"][BEN[n]]["held"]["sharpe"]]
small_dd = [n for n in N if b["rules"][n]["dd_ratio"] <= TH["replay_max_drop_ratio_vs_hold"]]
pb = b["pbo"]; ls = lambda L_: ", ".join(L_) if L_ else "none"
t1 = b["rules"]["T1"]
doc = f"""# 22. Replay 05: slow trend rules on the US stock market, free data from 1927

Status: research result. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Plan written and pushed before the run: `research_rig/PREREG_05_stock_trend_free_data.md`. Every number below is MEASURED by `research_rig/run_05.py` and placed here by `research_rig/build_doc22.py`.

One thing to know about how this was run: before the full run, the script was tried once with 3 shuffles at the middle cost to see that it worked. I saw rough results from that try. No rule or setting was changed afterwards.

## Bottom line

- {r['days']:,} trading days, {r['start']} to 2026-09-30. Eight rules. Held-back slice: 2006-06-01 to 2026-06-30.
- Rules that pass all five marks: {ls(P['low'])} at 2 bps a side, {ls(P['base'])} at 5 bps, {ls(P['high'])} at 10 bps.
- Holding the market in the held-back slice grew {pc(hb['cagr'])} a year with a largest drop of {pc(hb['maxdd'])}. Rules that grew more than their comparison at 5 bps: {ls(more)}.
- Rules with a better Sharpe ratio than their comparison in the held-back slice: {ls(better_sh)}. Rules whose largest drop was small enough for mark 1: {ls(small_dd)}. Rules that pass mark 1: {ls(m1)}.
- Rules that beat a fixed mix of stocks and cash with the same average share in stocks, on both Sharpe ratio and largest drop: {ls(fm)}.
- The ten-month rule, the best known of these: {pc(t1['held']['cagr'])} a year against {pc(hb['cagr'])} for holding, largest drop {pc(t1['held']['maxdd'])} against {pc(hb['maxdd'])}, in stocks {t1['held']['avg_weight']*100:.0f}% of the time on average.
- Overfitting estimate across the eight rules at 5 bps: {pb['pbo']:.3f} against a bar of {TH['backtest_max_pbo']} (`backtest_max_pbo`). Document 16 shows this mark is jumpy, so read it with care in both directions.
- Taxes are not in these numbers. A rule that sells pays tax sooner than holding does.

## What the rules are

| Id | Rule |
|---|---|
| T1 | Hold the market when it is above its ten-month average, else Treasury bills. Checked at month end |
| T2 | Hold the market when it is above its 200-day average, else bills. Checked daily |
| T3 | Hold the market when its last 12 months beat bills, else bills. Checked at month end |
| T4 | Share in stocks equals how many of the 20, 50, 100 and 200 day averages the market is above |
| T5 | The first published version of the Pacer Trendpilot rule: all in, half in, or out, using the 200-day average |
| V1 | No trend. Hold less when the market has been jumpy |
| I1 | Twelve industry groups, each on its own ten-month rule |
| I2 | When the ten-month rule says hold, own the three industry groups that rose most over 12 months |

## Held-back slice, 2006-06-01 to 2026-06-30, at 5 bps a side

{slice_tab('base', 'held')}
## Whole sample, {r['start']} to 2026-09-30, at 5 bps a side

{slice_tab('base', 'all')}
## Pass marks

{marks_tab()}
The numbers behind the marks, at 5 bps a side:

{detail_tab('base')}
## The three bad years, at 5 bps a side

{years_tab('base')}
## Does the fill assumption matter

Held-back Sharpe ratio at 5 bps a side. The test trades one full day late. "Traded the same close" is the ideal case that cannot be done in practice.

{sens_tab('base')}
## What this does and does not show

- These are returns of an index that cannot be bought directly. A total market fund is the nearest thing. Fund fees and tracking gaps are left out for the rules and for holding alike.
- The held-back slice holds two fast falls with fast rebounds (2020 and 2022) and one slow fall (2008). Slow trend rules are built for slow falls.
- The three months after the designer's knowledge cutoff are far too short to mean anything and are in the output file only.
- This is the cheap first look. A fair test of funds that can be bought needs paid daily prices with opening prices (`docs/decisions/morning_list_2026-11-25.md`).

## Files

- Plan: `research_rig/PREREG_05_stock_trend_free_data.md`. Data notes: `research_rig/data_notes_french.md`
- Code: `research_rig/run_05.py`, `rig2.py`, `build_doc22.py`. Output: `research_rig/results_05.json`
- Trials counted so far: {r['n_trials']} (`research_rig/TRIAL_LEDGER.md`)

## Sources

- [Kenneth French data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
- [Pacer Trendpilot US Large Cap ETF prospectus, SEC](https://www.sec.gov/Archives/edgar/data/1616668/000089418925006695/pacertrendpilotuslargecape.htm)
"""
assert "—" not in doc
open("../docs/research/22_replay_05_stock_trend.md", "w").write(doc); print(len(doc.splitlines()), "lines; passes", P)
