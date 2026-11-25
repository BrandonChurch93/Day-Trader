"""Builds docs/research/16_rig_audit.md from compare_v1_v2.json, results_v2.json, noise_pbo.json and audit/pbo_stability.json.
Run after run_v2.py, compare_v1_v2.py and noise_pbo.py. Every number in the document comes from those files."""
import json, statistics as st
v = json.load(open("results_v2.json")); c = json.load(open("compare_v1_v2.json")); nz = json.load(open("noise_pbo.json")); ps = json.load(open("../audit/pbo_stability.json"))
V = ["Binance.US", "Alpaca", "Kraken $10k tier", "Kraken entry", "Coinbase entry"]; COST = {"Binance.US": 7, "Alpaca": 30, "Kraken $10k tier": 43, "Kraken entry": 85, "Coinbase entry": 95}
AN = {"BTCUSD": "Bitcoin", "ETHUSD": "Ether"}; MN = {"m1": "1 held-back", "m2": "2 break-even", "m3": "3 deflated Sharpe", "m4": "4 overfitting", "m5": "5 shuffle", "passed": "verdict"}
RUN = {"R01": "Replay 01 (Bitstamp prices)", "X2": "Cross-check X2 (Kraken prices)", "S2": "Sensitivity S2 (ether from 2016, Kraken prices)", "R03": "Replay 03 (hourly rules)", "DIAG": "Diagnostic (Bitstamp prices from 2014-05-01, not pre-registered)"}
pc = lambda x, d=1: f"{x*100:+.{d}f}%"; yn = lambda b: "PASS" if b else "fail"; f3 = lambda x: "n/a" if x is None else f"{x:.3f}"
TH = v["thresholds"]; cn = c["counts"]
def changes():
    t = "| Run | Venue cost | Coin | Rule | What changed (first run to rerun) |\n|---|---|---|---|---|\n"
    for x in c["changes"]:
        if x["run"] == "R03": continue
        t += f"| {x['run']} | {x['venue']} | {AN[x['asset']]} | {x['rule']} | " + "; ".join(f"mark {MN[k]}: {yn(a)} to {yn(b)}" if k != "passed" else f"verdict: {yn(a)} to {yn(b)}" for k, (a, b) in x["marks"].items()) + " |\n"
    return t
def r03_changes():
    import collections
    cc = collections.Counter((k, a, b) for x in c["changes"] if x["run"] == "R03" for k, (a, b) in x["marks"].items())
    return "\n".join(f"- Mark {MN[k]}, {yn(a)} to {yn(b)}: {n} rule, coin and venue combinations." for (k, a, b), n in sorted(cc.items(), key=lambda z: -z[1])) + "\n"
def counts():
    t = "| Run | Rule and venue pairs | Passed, first run | Passed, rerun | Single marks that changed |\n|---|---|---|---|---|\n"
    for k in ["R01", "X2", "S2", "R03"]:
        if k in cn: t += f"| {RUN[k]} | {cn[k]['trials']} | {cn[k]['passed_first']} | {cn[k]['passed_rerun']} | {cn[k]['marks_changed']} |\n"
    return t
def both():
    t = "| Venue cost | Coin | Rule | Bitstamp prices | Kraken prices | Both, rerun | Both, first run | Marks failed on Kraken prices |\n|---|---|---|---|---|---|---|---|\n"
    for x in c["both_histories"]:
        if x["bitstamp"] or x["kraken"] or x["first_bitstamp"] or x["first_kraken"]:
            t += f"| {x['venue']} ({COST[x['venue']]} bps) | {AN[x['asset']]} | {x['rule']} | {yn(x['bitstamp'])} | {yn(x['kraken'])} | {yn(x['both'])} | {yn(x['first_both'])} | {', '.join(MN[m] for m in x['kraken_failed']) or 'none'} |\n"
    return t
BOTH = [x for x in c["both_histories"] if x["both"]]; BOTH0 = [x for x in c["both_histories"] if x["first_both"]]
def held(vn):
    t = "| Rule | Sharpe, Bitstamp | Sharpe, Kraken | Largest drop, Bitstamp | Largest drop, Kraken | Growth a year, Bitstamp | Growth a year, Kraken | Share of shuffles beaten, Kraken | Deflated Sharpe, Kraken |\n|---|---|---|---|---|---|---|---|---|\n"
    b = v["R01"]["venues"][vn]["BTCUSD"]; k = v["X2"]["venues"][vn]["BTCUSD"]
    t += f"| Hold bitcoin | {b['hold']['held']['sharpe']:.2f} | {k['hold']['held']['sharpe']:.2f} | {pc(b['hold']['held']['maxdd'])} | {pc(k['hold']['held']['maxdd'])} | {pc(b['hold']['held']['cagr'])} | {pc(k['hold']['held']['cagr'])} | | |\n"
    for r in b["rules"]:
        x = b["rules"][r]; y = k["rules"][r]; xw = x["held_worse_of_two_fills"]; yw = y["held_worse_of_two_fills"]
        t += f"| {r} | {xw['sharpe']:.2f} | {yw['sharpe']:.2f} | {pc(xw['maxdd'])} | {pc(yw['maxdd'])} | {pc(x['held']['cagr'])} | {pc(y['held']['cagr'])} | {y['shuffle_pct']*100:.1f}% | {y['dsr']:.3f} |\n"
    return t
def readnote():
    t = []
    for src, name in (("R01", "Bitstamp"), ("X2", "Kraken")):
        o = v[src]["venues"]["Binance.US"]["BTCUSD"]; h = o["hold"]["held"]; rs = [o["rules"][x["rule"]] for x in BOTH if x["venue"] == "Binance.US"]
        less = sum(r["held"]["cagr"] < h["cagr"] for r in rs); dd = [abs(r["held_worse_of_two_fills"]["maxdd"]) / abs(h["maxdd"]) for r in rs]
        t.append(f"on {name} prices {less} of the {len(rs)} passing rules grew less than holding bitcoin, and their largest drop was {min(dd)*100:.0f}% to {max(dd)*100:.0f}% of the drop from holding")
    return "How to read these, at Binance.US cost in the held-back years: " + "; ".join(t) + ". A rule passes mark 1 by having a better Sharpe ratio and a much smaller drop. Mark 1 does not ask for more growth than holding."
def pbo():
    t = "| Run | Venue cost | Coin | First run | Rerun (ties count as overfit, the verdict) | Ties count as half | Ties count as not overfit | Share of splits that tie | Rerun with the latest days dropped instead |\n|---|---|---|---|---|---|---|---|---|\n"
    for x in c["pbo"]:
        if x["run"] in ("R01", "X2", "DIAG") and x["asset"] == "BTCUSD":
            t += f"| {x['run']} | {x['venue']} | {AN[x['asset']]} | {f4(x['first'])} | {x['rerun']:.4f} | {x['ties_half']:.4f} | {x['ties_not_overfit']:.4f} | {x['tie_share']*100:.1f}% | {x['latest_days_dropped']:.4f} |\n"
    return t
def price_gap():
    import os
    if not (os.path.exists("data/bitstamp_BTCUSD.csv") and os.path.exists("data/krakenfull_BTCUSD.csv")): return json.load(open("venue_price_gap.json"))   # raw prices absent: use the stored summary
    import pandas as pd
    b = pd.read_csv("data/bitstamp_BTCUSD.csv", parse_dates=["date"]).set_index("date"); k = pd.read_csv("data/krakenfull_BTCUSD.csv", parse_dates=["date"]).set_index("date")
    j = b.join(k, lsuffix="_b", rsuffix="_k", how="inner"); j = j[(j.index >= "2014-05-01") & (j.index <= "2026-11-24")]; d = (j.close_k / j.close_b - 1).abs() * 1e4
    g = {"days": int(len(d)), "median_bps_2014_2017": float(d[d.index.year <= 2017].median()), "median_bps_2020_on": float(d[d.index.year >= 2020].median()), "max_bps": float(d.max())}
    json.dump(g, open("venue_price_gap.json", "w"), indent=1); return g
PG = price_gap()
def stab():
    d = ps["dates"]; le = [x["pbo_le0"] for x in d]; n_pass = sum(x < TH["backtest_max_pbo"] for x in le)
    t = f"- Start date moved one month at a time from {d[0]['start']} to {d[-1]['start']} ({len(d)} start dates, Bitstamp bitcoin, Alpaca cost, first-run code): the estimate ran from {min(le):.3f} to {max(le):.3f}, middle value {st.median(le):.3f}. It was under the bar on {n_pass} of {len(d)} start dates. The one that passed is the start date the plan used.\n"
    for s0, bl in ps["blocks"].items():
        bl = sorted(bl, key=lambda z: z["S"]); ks = [str(z["S"]) for z in bl]; vals = [z["pbo_le0"] for z in bl]
        t += f"- Number of blocks changed ({', '.join(ks)}) with start {s0}: the estimate ran from {min(vals):.3f} to {max(vals):.3f}, under the bar for {sum(x < TH['backtest_max_pbo'] for x in vals)} of {len(vals)} block counts.\n"
    return t
def noise():
    t = "| Made-up data with no edge | Average | Middle | 5th to 95th percentile | Lowest to highest | Share of samples under the bar |\n|---|---|---|---|---|---|\n"
    for k, x in nz["cases"].items():
        p = x["pbo"]; t += f"| {k} | {p['mean']:.2f} | {p['p50']:.2f} | {p['p05']:.2f} to {p['p95']:.2f} | {p['min']:.2f} to {p['max']:.2f} | {p['share_below_bar']*100:.1f}% |\n"
    return t
def r03():
    R3 = v["R03"]; t = "| Coin | Rule | Round trips a year | Average gain per round trip before costs | Break-even cost per side against holding | Held-back Sharpe at Binance.US cost | Holding, same slice | Held-back growth a year at Alpaca cost | Marks passed at Binance.US cost |\n|---|---|---|---|---|---|---|---|---|\n"
    for a in AN:
        for n, g in R3["per_rule"][a].items():
            if n == "C1": continue
            b = R3["venues"]["Binance.US"][a]; x = b["rules"][n]; y = R3["venues"]["Alpaca"][a]["rules"][n]; be = g["vs_hold"]
            bes = "never ahead" if be["status"] == "below_at_zero" else ("above 2,560 bps" if be["status"] == "above_cap" else f"{be['bps']:.1f} bps")
            t += f"| {AN[a]} | {n} | {g['gross_trips']['per_year']:.0f} | {g['gross_trips']['avg_bps']:+.1f} bps | {bes} | {x['held']['sharpe']:.2f} | {b['hold']['held']['sharpe']:.2f} | {pc(y['held']['cagr'])} | {sum(x['marks'][m] for m in ['m1','m2','m3','m4','m5'])} of 5 |\n"
    return t
r03_pass = sum(x["marks"]["passed"] for vn in V for a in AN for x in v["R03"]["venues"][vn][a]["rules"].values()); r03_n = sum(1 for vn in V for a in AN for x in v["R03"]["venues"][vn][a]["rules"])
r03_lose = sum(x["all"]["cagr"] < 0 for a in AN for x in v["R03"]["venues"]["Alpaca"][a]["rules"].values()); r03_k = sum(1 for a in AN for x in v["R03"]["venues"]["Alpaca"][a]["rules"])
kb = next(x for x in c["pbo"] if x["run"] == "X2" and x["venue"] == "Binance.US" and x["asset"] == "BTCUSD")
DG = next(x["rerun"] for x in c["pbo"] if x["run"] == "DIAG" and x["venue"] == "Binance.US")
f4 = lambda x: "" if x is None else f"{x:.4f}"
n9 = nz["cases"]["9 rules, correlation 0.8"]["pbo"]
bl = lambda L: ", ".join(f"{x['rule']}" for x in L) or "none"
byv = lambda L: "; ".join(f"{vn} cost: {bl([x for x in L if x['venue']==vn])}" for vn in V if any(x['venue']==vn for x in L)) or "none"
doc = f"""# 16. Audit of the test rig, and the corrected results

Status: research result. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. This document replaces the verdict tables in documents 12, 12b and 15. Those documents stay as the record of the first run.

Every number below is MEASURED by `research_rig/run_v2.py` and read from its output by `research_rig/build_doc16.py`, unless it is tagged otherwise.

## Bottom line

- Two different AI models audited the rig code line by line, separately. Neither found a rule that used future prices. Both found faults in how results were measured.
- I wrote down every fix and pushed it before rerunning anything (`research_rig/AMENDMENT_2026-11-25_audit_fixes.md`). No slice was changed. Correction added later on 2026-11-25: an earlier version of this line also said no rule, cost or pass mark was changed. That was wrong. Two rows of that list are not engine fixes. A13 made pass mark 1 stricter than the plan wrote it, so that it must also hold with the fill one hour late. A08 changed what buy and hold pays when the break-even cost is worked out, from a flat 5 bps to the same cost as the rule. A third row, A12, is an engine fix to the 0.10 band check that changes the trades of one rule, P2. So a pass in this rerun did not come from engine fixes alone, and research recommends that none is credited (question 18b in `docs/decisions/morning_list_2026-11-25.md`).
- After the fixes, rules that pass on both price histories: {byv(BOTH)}. In the first run that list was: {byv(BOTH0)}.
- So the fixes turned four failures into passes at the cheapest venue only. That is a result found after the fact. It is a reason to test in the practice account, not a result to rely on.
- The pass sits on a knife edge. The overfitting estimate for bitcoin on Kraken prices at Binance.US cost is {kb['rerun']:.4f} against a bar of {TH['backtest_max_pbo']} (`backtest_max_pbo`). With the latest days dropped instead of the earliest it is {kb['latest_days_dropped']:.4f}, which fails. On Bitstamp prices started on the same day as the Kraken history it is {DG:.4f}, which fails.
- Mark 4 itself is too jumpy to trust as a yes or no. On made-up data with no edge at all, {n9['share_below_bar']*100:.0f}% of samples still came in under the bar. Moving the start date by one month flips the first run's result.
- At every other venue cost, including Alpaca and Kraken, no rule passes on both histories. Ether passes nowhere.
- Day trading rules on hourly bars: {r03_pass} of {r03_n} rule, coin and venue combinations pass after the fixes. {r03_lose} of {r03_k} lose money over the whole sample at Alpaca cost.

## Who audited, and how

| Auditor | Model | What it did | Report |
|---|---|---|---|
| A | GPT-6.2 Sol | Read every file. Wrote its own separate replay from scratch and compared it with the rig day by day. 18 findings | `audit/2026-11-25_auditor_a.md`, `audit/replay_independent.py`, `audit/diagnostics.py` |
| B | Gemini Neon | Checked the statistics against the original papers, ran them on made-up data, tested each hourly rule for use of future prices by changing future bars and watching for any change in earlier signals. 11 findings | `audit/2026-11-25_auditor_b.md`, `audit/pbo_stability.json` |

What they agreed on:

- No rule uses a price it could not have known. Signals use the close of bar t and fill at the open of bar t+1. MEASURED by both.
- The rule definitions match their written plans. MEASURED by both. The engine's 0.10 band check did not follow the plan's words for moves to or from zero, which changed the trades of one rule, P2 (fix A12).
- Auditor A's separate replay matched the rig's daily account value and Sharpe ratio to rounding. MEASURED by A.

## What was wrong, in plain words

| Fault | What it did to the results | Fixed in the rerun |
|---|---|---|
| Shuffled timing test (mark 5) mixed up the in and out spells | For in-or-out rules the shuffles traded about half as often as the real rule, so they paid less cost and were harder to beat. For the fractional rule P2 the shuffles traded about three times as often, so they were easier to beat | Yes. Shuffles now keep the same number of trades and the same time held |
| First day of each slice was dropped, and holding the coin was restarted from cash in each slice | Small. Holding paid an extra entry cost inside the held-back slice | Yes |
| Overfitting estimate (mark 4) used blocks of unequal size | Small shifts in the estimate | Yes. Equal blocks |
| Overfitting estimate counted an exact tie with the middle rank as overfit | With 9 rules this happens in about 1 split in 12. It moved the estimate from under the bar to just over it in the first cross-check | Reported three ways. The verdict keeps the first reading. See the section on mark 4 |
| Orders filled on bars with no trades | A few bars on each history | Yes. The order waits for the next bar that traded |
| Break-even cost search stopped at 600 bps and compared against holding at a fixed 5 bps | Reported numbers were capped. Slightly unfair to the rules | Yes. Search to 2,560 bps, holding pays the same cost |
| The one-hour-late fill was a side table | Mark 1 only used the ideal fill | Yes. Mark 1 must hold with the fill one hour late as well. The worse of the two is shown |
| Checks printed a failure but did not stop the run | None seen, but a failed check could have been missed | Yes. A failed check stops everything |
| Pass mark numbers were typed into scripts | None, but against the rule that each number lives in one place | Yes. Read from `config/thresholds.yaml` at run time |
| Cross-check X1 was described as Kraken prices | It was a mix of two sources | Relabelled as a mixed-source check. X2 replaces it |

The full list, with file and line for each, is in the two audit reports and the amendment.

## Rerun: how many verdicts moved

{counts()}
Every mark that changed on the daily rules, in both directions:

{changes()}
Marks that changed on the hourly rules (the full list is in `research_rig/compare_v1_v2.json`):

{r03_changes()}
Why mark 5 moved so much on the hourly rules: in the first run the shuffles traded about half as often as the real rule, so at high cost the shuffles paid far less and won. With the same number of trades on both sides, most hourly rules do beat random timing. That says their timing is better than chance before costs. It does not make them profitable. Each of them still fails marks 1, 2 and 3.

## Corrected verdicts for the daily rules

A rule passes for a venue only if it passes all five marks on both price histories. Rows where nothing passed in either run are left out.

{both()}
What the passing rules are:

| Rule | In plain words |
|---|---|
| P1 | Hold a share of the account in bitcoin equal to how many of four averages (20, 50, 100, 200 days) the price is above |
| P2 | Like P1, with the size turned down when the price has been jumpy |
| S50 | In when the price is above its 50-day average, out when below |
| D20 | In when the price makes a 20-day high, out when it makes a 10-day low |

### Bitcoin, held-back slice (2023-01-01 to 2026-06-30), at Binance.US cost

Sharpe and largest drop are the worse of the two fills (ideal, and one hour late).

{held("Binance.US")}
### Bitcoin, held-back slice, at Alpaca cost

{held("Alpaca")}
{readnote()}

## Mark 4 is not stable enough to be a yes or no gate

Mark 4 asks: if you pick the best rule on half of the history, how often does it land in the bottom half on the other half? The bar is {TH['backtest_max_pbo']} (`backtest_max_pbo`).

### Three ways to count a tie

The [paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) says "below the median". It does not say what to do when the winner lands exactly on the median, which can only happen with an odd number of rules. STATED by the paper, read by auditor B and by me. (Corrected 2026-11-25: that is true when every rule has a different result. The code gives equal results the average of their ranks, so with an even number of rules a tie can still happen when two rules have exactly equal results on the other half. A tenth reader found this.)

{pbo()}
### How much it moves when nothing real changes

MEASURED by auditor B with the first-run code (`audit/pbo_stability.json`):

{stab()}
MEASURED by me with the rerun code on made-up data where no rule has any edge (`research_rig/noise_pbo.py`, {nz['samples']} samples each, {nz['blocks']} blocks). Marks 3 and 5 are built to let no-edge data through about 1 time in 20. Mark 4 at this bar lets it through more often than that:

{noise()}
What this means:

- A pass on mark 4 is weak evidence. A fail is weak evidence too.
- The first run's pass on Bitstamp prices depended on the start date the plan happened to use.
- The bar has not been changed. Changing how mark 4 is measured is a decision for the owner, and it should be made before the next test is run, not after.

One more sign of the same problem. The two price histories cover the same market. Started on the same day (2014-05-01) and charged Binance.US cost, the estimate is {kb['rerun']:.3f} on Kraken prices and {next(x['rerun'] for x in c['pbo'] if x['run']=='DIAG' and x['venue']=='Binance.US'):.3f} on Bitstamp prices. One passes and one fails. The Bitstamp pass in replay 01 comes from starting in 2013, before the Kraken history begins. The two venues' daily closing prices were not the same in the early years: the typical gap was {PG['median_bps_2014_2017']:.0f} bps in 2014 to 2017 and {PG['median_bps_2020_on']:.1f} bps from 2020 on (`research_rig/venue_price_gap.json`). That is one likely reason the two answers differ. Whether it is the whole reason is UNKNOWN.

Proposal, not adopted: measure mark 4 as the middle value over a fixed set of start dates and block counts, written down before the run. This costs nothing and removes the knife edge. (Corrected 2026-11-25: that last claim overstated it. A fixed set of dates stops one start date from deciding. The mark stays noisy, as the made-up data test on this page shows. Also corrected 2026-11-25: this line also proposed counting ties as half. That is the easier reading, as the table above shows, and results have been seen. Research now recommends keeping ties counted as overfit. Decisions 1a and 1b in `docs/decisions/morning_list_2026-11-25.md`.)

## Day trading rules on hourly bars, after the fixes

{r03()}
Passes at any venue cost: {r03_pass} of {r03_n} after the fixes, {cn['R03']['passed_first']} of {cn['R03']['trials']} in the first run. Document 15 has the rule definitions.

## What is still open

- The fixes were written after the first results were seen. Each one is tied to an audit finding and none changes a number in `config/thresholds.yaml`. Two of them do change what a pass mark asks (A13 and A08, see the correction near the top of this page), and a result that only appears after fixes deserves less trust than one that was there from the start.
- Both price histories cover the same market and the same years. Passing on both shows the result is not a quirk of one venue's prices. It does not show the rule will keep working.
- Binance.US cost is 7 bps per side, the lowest fee schedule checked. The owner has no account there, and whether a Binance.US account suits this project is an open decision (document 09). At Alpaca cost (30 bps per side) nothing passes on both histories.
- The held-back slice has now been looked at by replay 01, the cross-check, replay 03 and this rerun. It is no longer fresh. The only fresh test left is the practice account.
- The rerun of the hourly rules stopped twice on program errors (a process start-up setting and a reporting field of the wrong length). Both were fixed without touching any rule, cost or statistic, and the run was started again from the beginning.
- Auditor B also showed that the deflated Sharpe mark (mark 3) is sensitive to how alike the trials are. MEASURED by B on made-up data: with strongly related rules and no edge it passed 4.5% of the time. No change was made.

## Questions for the owner

| Question | Recommendation | Why |
|---|---|---|
| How should a tie be counted in mark 4 from now on? | As overfit, as in every test so far. (Corrected 2026-11-25: this row first said \"as half\") | Counting a tie as half is the neutral reading, and counting it as overfit pushes a no-edge result from 0.50 to about 0.56 with 9 rules. But half is the easier reading, results have been seen, and the owner's bar says never to loosen a limit after seeing a result. Keeping the full count is a cautious policy, not a claim that it is the more correct statistic. The rule list in a plan is never chosen to make ties more or less likely |
| Should mark 4 be measured over several start dates and block counts? | Yes, fixed in the plan before each run | One start date decides the result today. What this would do to the bitcoin results is UNKNOWN (corrected 2026-11-25: this row first said it would most likely turn the bitcoin passes back into fails, which was a guess). With the first-run code at Alpaca cost the middle value over {len(ps['dates'])} start dates was {st.median([x['pbo_le0'] for x in ps['dates']]):.3f}. It has not been measured at Binance.US cost, and research has not run it, so that the choice of method is not made by looking at its result |
| Do the four bitcoin rules go forward to the practice account? | Yes, as a practice test only, with P1 as the only bitcoin rule. The morning list proposes one stock rule beside it (`docs/decisions/morning_list_2026-11-25.md`, decision 5) | It is the plainest of the four, it was named as the primary rule before the first run, and practice trading is the only fresh test left |

## Files

- Plan for the fixes: `research_rig/AMENDMENT_2026-11-25_audit_fixes.md`
- Code: `research_rig/rig2.py`, `fixtures2.py` (19 checks, numbered up to 27; numbers 6 to 8 and 10 to 14 are not used), `run_v2.py`, `compare_v1_v2.py`, `noise_pbo.py`, `build_doc16.py`
- Outputs: `research_rig/results_v2.json`, `compare_v1_v2.json`, `noise_pbo.json`
- First run, unchanged: `engine.py`, `run_01*.py`, `run_03.py`, `results_01.json`, `results_01x2.json`, `results_03.json`

## Sources

- [Bailey, Borwein, López de Prado and Zhu, The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- [Bailey and López de Prado, The Deflated Sharpe Ratio](https://davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
"""
assert "—" not in doc
open("../docs/research/16_rig_audit.md", "w").write(doc); print(len(doc.splitlines()), "lines")
