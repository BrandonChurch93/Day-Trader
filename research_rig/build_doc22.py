"""Builds docs/research/22_replay_05_stock_trend.md from results_05.json (first run) and results_05b.json (corrected run,
AMENDMENT_05_I2_equal_thirds.md). Run after both runs of run_05.py. Tables show the corrected run unless they say otherwise."""
import json
r1 = json.load(open("results_05.json")); r = json.load(open("results_05b.json")); assert r["i2_pooled_on_reentry"] and not r1.get("i2_pooled_on_reentry", False)
TH = r["thresholds"]; C = r["costs"]; C1 = r1["costs"]; L = ["low", "base", "high"]; N = list(C["base"]["rules"])
NAME = {"T1": "Ten-month rule", "T2": "200-day rule", "T3": "Twelve-month momentum", "T4": "Four-average ensemble (P1)", "T5": "Trendpilot, first version", "V1": "Size by volatility, no trend",
        "I1": "Twelve industries, each on the ten-month rule", "I2": "Top three industries with a market filter"}
BEN = {n: ("HOLD12" if n == "I1" else "HOLD") for n in N}; BN = {"HOLD": "Hold the market", "HOLD12": "Hold the twelve industries"}
pc = lambda x, d=1: f"{x*100:+.{d}f}%"; yn = lambda b: "PASS" if b else "fail"; MK = ["m1", "m2", "m3", "m4", "m5"]
def be(x): return "never ahead" if x["status"] == "below_at_zero" else ("above 2,560 bps" if x["status"] == "above_cap" else f"{x['bps']:.0f} bps")
def slice_tab(lab, sl):
    o = C[lab]; t = "| Rule | Growth a year | Sharpe above bills | Largest drop | Average share in stocks | Days with a trade, a year |\n|---|---|---|---|---|---|\n"
    for b in ("HOLD", "HOLD12"):
        m = o["bench"][b][sl]; t += f"| {BN[b]} | {pc(m['cagr'])} | {m['sharpe']:.2f} | {pc(m['maxdd'])} | 100% | |\n"
    for n in N:
        m = o["rules"][n][sl]; yrs = m["n"] / 252
        t += f"| {n}. {NAME[n]} | {pc(m['cagr'])} | {m['sharpe']:.2f} | {pc(m['maxdd'])} | {m['avg_weight']*100:.0f}% | {m['sides']/yrs:.1f} |\n"
    return t
def marks_tab():
    t = "| Rule | Cost per side | 1 held-back | 2 break-even | 3 deflated Sharpe | 4 overfitting | 5 shuffle | All five, corrected run | All five, first run | Beat the fixed mix on the held-back slice |\n|---|---|---|---|---|---|---|---|---|---|\n"
    both = lambda c, f: c if c == f else f"{c} (first run: {f})"
    for n in N:
        for lab in L:
            x = C[lab]["rules"][n]; m = x["marks"]; x1 = C1[lab]["rules"][n]; m1 = x1["marks"]
            v = yn(m['passed']) if not (m['passed'] and not x['beats_fixed_mix_held']) else "passes the marks, but holding less stock did as well"
            fm = lambda z: 'yes' if z['beats_fixed_mix_held'] else 'no'
            t += f"| {n} | {C[lab]['cost_bps_per_side']} bps | " + " | ".join(both(yn(m[k]), yn(m1[k])) for k in MK) + f" | {v} | {yn(m1['passed'])} | {both(fm(x), fm(x1))} |\n"
    return t
def detail_tab(lab):
    o = C[lab]; t = "| Rule | Held-back Sharpe, rule | Comparison | Drop as a share of the comparison's | Break-even cost per side | Deflated Sharpe | Share of shuffles beaten | Sharpe gap to the comparison, whole sample: low end, middle, high end of the resampled range | Fixed mix: share in stocks | Fixed mix: held-back Sharpe | Fixed mix: largest drop |\n|---|---|---|---|---|---|---|---|---|---|---|\n"
    for n in N:
        x = o["rules"][n]; b = o["bench"][BEN[n]]["held"]; f = x["fixed_mix"]; bt = x["boot_sharpe_diff_vs_bench"]
        t += f"| {n} | {x['held']['sharpe']:.2f} | {b['sharpe']:.2f} | {x['dd_ratio']*100:.0f}% | {be(r['breakeven'][n]['vs_bench'])} | {x['dsr']:.3f} | {x['shuffle_pct']*100:.1f}% | {bt[0]:+.2f}, {bt[1]:+.2f}, {bt[2]:+.2f} | {f['weight']*100:.0f}% | {f['held']['sharpe']:.2f} | {pc(f['held']['maxdd'])} |\n"
    return t
def years_tab(lab):
    o = C[lab]; t = "| Rule | 2008 | 2020 | 2022 | Largest drop in 2008 | Largest drop in 2020 | Largest drop in 2022 |\n|---|---|---|---|---|---|---|\n"
    for bb in ("HOLD", "HOLD12"):
        m = o["bench"][bb]; t += f"| {BN[bb]} | {pc(m['y2008']['total'])} | {pc(m['y2020']['total'])} | {pc(m['y2022']['total'])} | {pc(m['y2008']['maxdd'])} | {pc(m['y2020']['maxdd'])} | {pc(m['y2022']['maxdd'])} |\n"
    for n in N:
        m = o["rules"][n]; t += f"| {n} | {pc(m['y2008']['total'])} | {pc(m['y2020']['total'])} | {pc(m['y2022']['total'])} | {pc(m['y2008']['maxdd'])} | {pc(m['y2020']['maxdd'])} | {pc(m['y2022']['maxdd'])} |\n"
    return t
def sens_tab(lab):
    o = C[lab]; t = "| Rule | Held-back Sharpe as tested | Traded the same close | Cash earns nothing |\n|---|---|---|---|\n"
    for n in N:
        x = o["rules"][n]; t += f"| {n} | {x['held']['sharpe']:.2f} | {x['same_close']['held']['sharpe']:.2f} | {x['cash_earns_nothing']['held']['sharpe']:.2f} |\n"
    return t
P = {lab: [n for n in N if C[lab]["rules"][n]["marks"]["passed"]] for lab in L}
P1 = {lab: [n for n in N if C1[lab]["rules"][n]["marks"]["passed"]] for lab in L}
G = json.load(open("i2_2020_note.json")); R = C["base"]["rules"]
b = C["base"]; b1 = C1["base"]; hb = b["bench"]["HOLD"]["held"]; ha = b["bench"]["HOLD"]["all"]
ls = lambda L_: ", ".join(L_) if L_ else "none"
SAME = ["cagr", "sharpe", "maxdd", "avg_weight"]
for lab in L:   # the correction touches rule I2 only: the other seven rules and both comparisons must be identical between the runs
    for n in N:
        if n != "I2": assert all(C[lab]["rules"][n][sl][k] == C1[lab]["rules"][n][sl][k] for sl in ("held", "all", "dev") for k in SAME), (lab, n)
        if n != "I2": assert C[lab]["rules"][n]["shuffle_pct"] == C1[lab]["rules"][n]["shuffle_pct"]
    for bb in ("HOLD", "HOLD12"): assert C[lab]["bench"][bb]["held"] == C1[lab]["bench"][bb]["held"]
assert r["breakeven"]["T1"] == r1["breakeven"]["T1"]
both = [n for n in N if all(n in P[lab] and n in P1[lab] for lab in L)]
both_any = {lab: [n for n in N if n in P[lab] and n in P1[lab]] for lab in L}
only4_first = {lab: [n for n in N if (not C1[lab]["rules"][n]["marks"]["m4"]) and all(C1[lab]["rules"][n]["marks"][k] for k in ("m1", "m2", "m3", "m5"))] for lab in L}
more = [n for n in N if b["rules"][n]["held"]["cagr"] > b["bench"][BEN[n]]["held"]["cagr"]]
m1 = [n for n in N if b["rules"][n]["marks"]["m1"]]; fm = [n for n in N if b["rules"][n]["beats_fixed_mix_held"]]
better_sh = [n for n in N if b["rules"][n]["held"]["sharpe"] > b["bench"][BEN[n]]["held"]["sharpe"]]
small_dd = [n for n in N if b["rules"][n]["dd_ratio"] <= TH["replay_max_drop_ratio_vs_hold"]]
boot_pos = [n for n in N if b["rules"][n]["boot_sharpe_diff_vs_bench"][0] > 0]
def lists(c):
    """The lists in the bottom line, for one run at 5 bps."""
    rr = c["rules"]
    return dict(more=[n for n in N if rr[n]["held"]["cagr"] > c["bench"][BEN[n]]["held"]["cagr"]],
                m1=[n for n in N if rr[n]["marks"]["m1"]], fm=[n for n in N if rr[n]["beats_fixed_mix_held"]],
                sh=[n for n in N if rr[n]["held"]["sharpe"] > c["bench"][BEN[n]]["held"]["sharpe"]],
                dd=[n for n in N if rr[n]["dd_ratio"] <= TH["replay_max_drop_ratio_vs_hold"]],
                boot=[n for n in N if rr[n]["boot_sharpe_diff_vs_bench"][0] > 0])
LF, LC = lists(b1), lists(b)
assert LC == dict(more=more, m1=m1, fm=fm, sh=better_sh, dd=small_dd, boot=boot_pos)
def by_run(k): return ls(LF[k]) + " (the same in both runs)" if LF[k] == LC[k] else f"first run {ls(LF[k])}; corrected run {ls(LC[k])}"
_keys = lambda d, pre="": [x for k, v in d.items() for x in (_keys(v, pre + k + "/") if isinstance(v, dict) else [pre + k])]
def _get(d, path):
    for k in path.split("/"): d = d[k]
    return d
moved = sorted({k for lab in L for n in N if n != "I2" for k in _keys(C[lab]["rules"][n]) if _get(C[lab]["rules"][n], k) != _get(C1[lab]["rules"][n], k)})
assert set(moved) <= {"dsr", "marks/m4", "marks/passed"}, moved   # for the seven other rules nothing else differs between the runs
SAME_NOTE = ("Which run this table shows: the seven rules other than I2 made the same trades in both runs, and this builder checks that their "
             "figures are the same in both, apart from mark 4, the all-five verdict and the deflated Sharpe, which are worked out across the "
             "whole set of eight. The comparisons are the same in both runs too. So the only row here that belongs to the corrected run alone "
             "is I2. Research recommends that no pass from either run is credited (question 18b in the morning list); I2's first-run figures are in the table \"Rule I2, first run against "
             "corrected run\" above.")
dsr_min = min(C[lab]["rules"][n]["dsr"] for lab in L for n in N)
def dsr_lo(R):
    v, n, lab = min((R[lab]["rules"][n]["dsr"], n, lab) for lab in L for n in N); return f"{v:.4f} ({n} at {R[lab]['cost_bps_per_side']} bps)"
t1 = b["rules"]["T1"]; i2 = b["rules"]["I2"]; i2f = b1["rules"]["I2"]
growth_lo = min(b["rules"][n]["held"]["cagr"] for n in N if n != "I2"); growth_hi = max(b["rules"][n]["held"]["cagr"] for n in N if n != "I2")
dd_lo = max(b["rules"][n]["held"]["maxdd"] for n in N if n != "I2"); dd_hi = min(b["rules"][n]["held"]["maxdd"] for n in N if n != "I2")
def pbo_tab():
    t = "| Cost per side | First run | First run, latest days dropped | Corrected run | Corrected run, latest days dropped | Bar | Ties |\n|---|---|---|---|---|---|---|\n"
    for lab in L:
        a1 = C1[lab]; a2 = C[lab]
        t += f"| {a2['cost_bps_per_side']} bps | {a1['pbo']['pbo']:.3f} | {a1['pbo_drop_latest']['pbo']:.3f} | {a2['pbo']['pbo']:.3f} | {a2['pbo_drop_latest']['pbo']:.3f} | under {TH['backtest_max_pbo']} | {a2['pbo']['tie_share']*100:.1f}% of cases |\n"
    return t
def i2_tab():
    t = "| Run | Cost per side | Growth a year | Sharpe above bills | Largest drop | Drop as a share of the market's | Mark 1 | All five |\n|---|---|---|---|---|---|---|---|\n"
    for nm, CC in (("First run, code as it was", C1), ("Corrected run, equal thirds on re-entry", C)):
        for lab in L:
            x = CC[lab]["rules"]["I2"]; m = x["held"]; t += f"| {nm} | {CC[lab]['cost_bps_per_side']} bps | {pc(m['cagr'])} | {m['sharpe']:.2f} | {pc(m['maxdd'])} | {x['dd_ratio']*100:.0f}% | {yn(x['marks']['m1'])} | {yn(x['marks']['passed'])} |\n"
    return t
flips = [f"{n} at {C[lab]['cost_bps_per_side']} bps: {yn(C1[lab]['rules'][n]['marks']['passed'])} to {yn(C[lab]['rules'][n]['marks']['passed'])}" for lab in L for n in N if C1[lab]["rules"][n]["marks"]["passed"] != C[lab]["rules"][n]["marks"]["passed"]]
flips_own = [f for f in flips if not f.startswith("I2")]
doc = f"""# 22. Replay 05: slow trend rules on the US stock market, free data from 1927

Status: research result. Proposed by research. No owner decision is recorded here.

Note, 2026-11-25. Which of the two runs below counts is not settled. The corrected run fixed a fault in the code of one rule, not in the engine. The owner's rule allows a second run of the held-back slice only when the engine itself was wrong, so it may not cover this one. That is questions 18a and 18b in `archive/decisions/morning_list_2026-11-25.md`. The first run has a slip of its own: its ledger row was added after it started, and a short try with 3 shuffles came before it. Research recommends that no pass from either run is credited, that the fails stand, and that every figure below is kept as a measurement. The owner has not answered.

Date: 2026-11-25. Plan written and pushed before the run: `research_rig/PREREG_05_stock_trend_free_data.md`. Correction written and pushed before the corrected run: `research_rig/AMENDMENT_05_I2_equal_thirds.md`. Every number below is MEASURED by `research_rig/run_05.py` and placed here by `research_rig/build_doc22.py`, unless it says it is the auditor's.

## How this was run, including what went wrong

- Before the full run, the script was tried once with 3 shuffles at the middle cost to see that it worked. I saw rough results from that try. No rule or setting was changed afterwards.
- Two full starts were lost to process problems on the test machine and were restarted unchanged. No result from them was read.
- The first full run finished and is kept as `research_rig/results_05.json`.
- An independent audit then found that the code for rule I2 did not do what the plan says (`archive/audit/2026-11-25_replay_05_audit.md`, finding 1). The plan says one third in each of three industry groups. The code split the account in three once, in 1927, and never again. MEASURED by the auditor: by 2026-06-30 one third had grown to 87.8% of the account.
- The correction was written down and pushed, then the run was repeated with only that change. It is kept as `research_rig/results_05b.json`.
- The auditor had already measured what the correction would do before it was written down. So a pass that appears only in the corrected run is a pass after a correction whose effect was known. This page reports it as that.
- The audit found no look-ahead in any of the eight rules, and its own separate rebuild of holding the market and of rule T1 from the raw file matched the rig exactly (MEASURED by the auditor).

## Bottom line

- {r['days']:,} trading days, {r['start']} to 2026-09-30. Eight rules. Held-back slice: 2006-06-01 to 2026-06-30.
- Rules that pass all five marks in the first run: {ls(P1['low'])} at 2 bps a side, {ls(P1['base'])} at 5 bps, {ls(P1['high'])} at 10 bps.
- Rules that pass all five marks in the corrected run: {ls(P['low'])} at 2 bps a side, {ls(P['base'])} at 5 bps, {ls(P['high'])} at 10 bps.
- Rules that pass in both runs at all three cost levels: {ls(both)}. That is the only reading with no asterisk. Rules that pass in both runs at 10 bps only: {ls([n for n in N if n in P1['high'] and n in P['high']])}.
- Verdicts that changed between the runs: {"; ".join(flips) if flips else "none"}.
- {"Verdicts changed for rules whose own trades did not change at all (" + "; ".join(flips_own) + "). The only thing that moved for them is mark 4, which is worked out across the whole set of eight rules." if flips_own else "No verdict changed for a rule whose own trades did not change."}
- In the first run, the rules that failed mark 4 and nothing else: {ls(only4_first['low'])} at 2 bps, {ls(only4_first['base'])} at 5 bps, {ls(only4_first['high'])} at 10 bps.
- What the rules did in the held-back slice, in plain terms: holding the market grew {pc(hb['cagr'])} a year with a largest drop of {pc(hb['maxdd'])}. The seven rules other than I2 grew between {pc(growth_lo)} and {pc(growth_hi)} a year, with largest drops between {pc(dd_lo)} and {pc(dd_hi)}. Rules that grew more than their comparison at 5 bps: {by_run('more')}. In the first run I2 grew {pc(i2f['held']['cagr'])} a year, but its largest drop was {i2f['dd_ratio']*100:.0f}% of the market's, too large for mark 1.
- Rules with a better Sharpe ratio than their comparison in the held-back slice: {by_run('sh')}. Rules whose largest drop was small enough for mark 1: {by_run('dd')}. Rules that pass mark 1: {by_run('m1')}.
- Rules that beat a fixed mix of stocks and cash on both Sharpe ratio and largest drop in the held-back slice: {by_run('fm')}. The fixed mix holds the rule's own average share in stocks from the development slice.

- Rules whose Sharpe ratio is above the comparison's over the whole sample even at the low end of the resampled range: {by_run('boot')}. For every other rule the range includes zero, so the gap could be chance.
- The ten-month rule, the best known of these: {pc(t1['held']['cagr'])} a year against {pc(hb['cagr'])} for holding, largest drop {pc(t1['held']['maxdd'])} against {pc(hb['maxdd'])}, in stocks {t1['held']['avg_weight']*100:.0f}% of the time on average. These figures are the same in both runs.
- Mark 3 screened nothing in this test. The lowest deflated Sharpe of any rule at any cost was {dsr_min:.4f} against a bar of {TH['replay_min_deflated_sharpe']} (`replay_min_deflated_sharpe`). The plan takes the spread of Sharpe ratios across these eight rules. They all trade the same market and sit close together, so the hurdle is near zero (auditor's finding 2). The code follows the plan. The plan was not changed after the run.
- Taxes are not in these numbers. A rule that sells pays tax sooner than holding does.

## What this means

- These rules gave up growth and cut the largest drop. That is the same shape the live funds built on these rules show (`docs/research/21_systematic_funds_and_published_rules.md`).
- None of this is fast money. The best case here is a smoother ride at a lower return than holding.
- Whether a rule "passes" here hangs on mark 4, and mark 4 moved from fail to pass when one of the eight rules was corrected. `docs/research/16_rig_audit.md` found the same weakness on bitcoin. The value in `backtest_max_pbo` is not changed. How to measure mark 4 in a steadier way is an open question for the owner.
- A pass means "worth running in the practice account". It does not mean "makes money".

## The overfitting estimate (mark 4), both runs

{pbo_tab()}
No tie occurred in either run, so the three tie readings are equal. (Corrected 2026-11-25: this line first said eight rules cannot tie. They can, when two rules have the same result.)

## Rule I2, first run against corrected run, held-back slice

{i2_tab()}
Three cautions about rule I2 in the corrected run:

- It passes only after the correction, and the effect of the correction was known before it was written down.
- Its 2020 year was {pc(R['I2']['y2020']['total'])}, against {pc(R['T1']['y2020']['total'])} for the ten-month rule. In 2020 one of the twelve industry groups, {G['top']}, rose {pc(G['return_by_group'][G['top']])}. The next highest, {G['second']}, rose {pc(G['return_by_group'][G['second']])} (MEASURED from the industry file by `research_rig/i2_2020_note.py`). Which groups I2 held in 2020 is not in the output file, and which companies drove that group is not checked (both UNKNOWN). The likely reading, not proven here, is that one group's one year is a large part of what I2 did in the held-back slice.
- The twelve groups are index groups. They cannot be bought as they are. Sector funds are the nearest thing and they are not the same groups. No sector fund has been tested here.

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
| I2 | When the ten-month rule says hold, own the three industry groups that rose most over 12 months, one third each |

The twelve industry sleeves in I1, and in its comparison, start equal in 1927 and are never set back to equal, as the plan says. MEASURED by the auditor: by 2006-06-01 the sleeves of I1 ranged from 2.8% to 18.5% of the account (finding 5).

## Held-back slice, 2006-06-01 to 2026-06-30, at 5 bps a side, corrected run

{SAME_NOTE}

{slice_tab('base', 'held')}
"Days with a trade" counts days, not sides. A switch between stocks and bills pays two sides, and the cost of every side is charged. An earlier draft of this table called the column trade sides (auditor's finding 3).

## Whole sample, {r['start']} to 2026-09-30, at 5 bps a side, corrected run

{SAME_NOTE}

{slice_tab('base', 'all')}
## Pass marks

Marks 1 to 5 and the fixed-mix column are from the corrected run. Where the first run gave a different answer, it follows in brackets. The two "All five" columns give the verdict of each run.

{marks_tab()}
The numbers behind the marks, at 5 bps a side, corrected run. {SAME_NOTE} In this table the deflated Sharpe column is from the corrected run for every rule. Across all three cost levels the lowest deflated Sharpe is {dsr_lo(C)} in the corrected run and {dsr_lo(C1)} in the first run.

{detail_tab('base')}
## The three bad years, at 5 bps a side, corrected run

{SAME_NOTE}

{years_tab('base')}
## Does the fill assumption matter

Held-back Sharpe ratio at 5 bps a side, corrected run. Only the I2 row differs from the first run. The test trades one full day late. "Traded the same close" is the ideal case that cannot be done in practice.

{sens_tab('base')}
## What this does and does not show

- These are returns of an index that cannot be bought directly. A total market fund is the nearest thing. Fund fees and tracking gaps are left out for the rules and for holding alike.
- The held-back slice holds 2008, 2020 and 2022. The table above shows each year one by one.
- The three months after the designer's knowledge cutoff are far too short to mean anything and are in the output files only.
- This is the cheap first look. A fair test of funds that can be bought needs daily fund prices with opening prices and dividend history. Dividend history is the part that still needs a purchase (`archive/decisions/morning_list_2026-11-25.md`, `research_rig/PREREG_06_fund_trend_paid_data.md`).

## Files

- Plan: `research_rig/PREREG_05_stock_trend_free_data.md`. Correction: `research_rig/AMENDMENT_05_I2_equal_thirds.md`. Data notes: `research_rig/data_notes_french.md`
- Audit: `archive/audit/2026-11-25_replay_05_audit.md`, `archive/audit/replay_05_probes.py`
- Code: `research_rig/run_05.py`, `rig2.py`, `build_doc22.py`, `i2_2020_note.py`. Output: `research_rig/results_05.json` (first run), `research_rig/results_05b.json` (corrected run, started with `R05_POOL=1`)
- Trials counted in the deflated Sharpe formula: {r['n_trials']} (`research_rig/TRIAL_LEDGER.md`)

## Sources

- [Kenneth French data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
- [Pacer Trendpilot US Large Cap ETF prospectus, SEC](https://www.sec.gov/Archives/edgar/data/1616668/000089418925006695/pacertrendpilotuslargecape.htm)
"""
assert "—" not in doc
open("../docs/research/22_replay_05_stock_trend.md", "w").write(doc); print(len(doc.splitlines()), "lines; first run passes", P1, "corrected", P, "both", both)
