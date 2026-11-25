"""Builds docs/research/12b from results_01x2.json and passmarks_01.json. Run after run_01x2.py."""
import json
x=json.load(open("results_01x2.json")); p0=json.load(open("passmarks_01.json")); r0=json.load(open("results_01.json")); B=x["build"]
V=["Binance.US","Alpaca","Kraken $10k tier","Kraken entry","Coinbase entry"]; COST={"Binance.US":7,"Alpaca":30,"Kraken $10k tier":43,"Kraken entry":85,"Coinbase entry":95}
AN={"BTCUSD":"Bitcoin","ETHUSD":"Ether"}; RL=list(x["X2"]["BTCUSD"]["rules"]); MK=["m1","m2","m3","m4","m5"]
MN={"m1":"mark 1 held-back","m2":"mark 2 break-even","m3":"mark 3 deflated Sharpe","m4":"mark 4 overfitting","m5":"mark 5 shuffle"}
pc=lambda v,d=1: f"{v*100:+.{d}f}%"; yn=lambda b: "PASS" if b else "fail"
def km(a,r,v,src=None): return (src or x["X2"][a])["rules"][r]["venues"][v]["marks"]
changes=[]; same=0; tot=0; both=[]
vt="| Venue cost | Coin | Rule | On Bitstamp prices | On Kraken prices | Marks that differ |\n|---|---|---|---|---|---|\n"
for v in V:
    for a in AN:
        for r in RL:
            o=p0[f"{v}|{a}|{r}"]; k=km(a,r,v); tot+=1; diff=[MN[m] for m in MK if o[m]!=k[m]]
            if o["passed"]==k["passed"]: same+=1
            else: changes.append((v,a,r,o["passed"],k["passed"],diff))
            if o["passed"] and k["passed"]: both.append((v,a,r))
            if o["passed"] or k["passed"] or diff: vt+=f"| {v} | {AN[a]} | {r} | {yn(o['passed'])} | {yn(k['passed'])} | {', '.join(diff) if diff else 'none'} |\n"
def chg():
    if not changes: return "No verdict changed in either direction.\n"
    t=""
    for v,a,r,o,k,d in changes:
        m=km(a,r,v); q=p0[f"{v}|{a}|{r}"]; h=x["X2"][a]["rules"][r]["venues"][v]["held"]; b=x["X2"][a]["bh"][v]["held"]
        t+=f"- {AN[a]} {r} at {v} cost: {yn(o)} on Bitstamp prices, {yn(k)} on Kraken prices. Differs on {', '.join(d)}. Held-back Sharpe {q['held_sharpe']:.2f} against {q['bh_held_sharpe']:.2f} for holding on Bitstamp, {h['sharpe']:.2f} against {b['sharpe']:.2f} on Kraken. Drop ratio {q['dd_ratio']:.2f} and {m['dd_ratio']:.2f}. Deflated Sharpe {q['dsr']:.2f} and {m['dsr']:.2f}. Shuffle {q['shuffle']:.2f} and {m['shuffle']:.2f}.\n"
    return t
def heldtab(a,v):
    t="| Rule | Held-back Sharpe, Bitstamp | Held-back Sharpe, Kraken | Largest drop, Bitstamp | Largest drop, Kraken | Growth a year, Bitstamp | Growth a year, Kraken |\n|---|---|---|---|---|---|---|\n"
    hb=r0["assets"][a]["bh"][v]["held"]; hk=x["X2"][a]["bh"][v]["held"]
    t+=f"| Hold the coin | {hb['sharpe']:.2f} | {hk['sharpe']:.2f} | {pc(hb['maxdd'])} | {pc(hk['maxdd'])} | {pc(hb['cagr'])} | {pc(hk['cagr'])} |\n"
    for r in RL:
        o=r0["assets"][a]["rules"][r]["venues"][v]["held"]; k=x["X2"][a]["rules"][r]["venues"][v]["held"]
        t+=f"| {r} | {o['sharpe']:.2f} | {k['sharpe']:.2f} | {pc(o['maxdd'])} | {pc(k['maxdd'])} | {pc(o['cagr'])} | {pc(k['cagr'])} |\n"
    return t
def s2():
    S=x.get("S2_ETH"); 
    if not S: return "Not finished.\n"
    t="| Rule | Whole-sample growth a year at Binance.US cost | Sharpe | Largest drop | "+" | ".join(f"{v}" for v in V)+" |\n|---|---|---|---|"+"---|"*len(V)+"\n"
    b=S["bh"]["Binance.US"]["all"]; t+=f"| Hold the coin | {pc(b['cagr'])} | {b['sharpe']:.2f} | {pc(b['maxdd'])} |"+" |"*len(V)+"\n"
    for r in RL:
        a=S["rules"][r]["venues"]["Binance.US"]["all"]; t+=f"| {r} | {pc(a['cagr'])} | {a['sharpe']:.2f} | {pc(a['maxdd'])} | "+" | ".join(yn(S["rules"][r]["venues"][v]["marks"]["passed"]) for v in V)+" |\n"
    return t
s2pass=sum(x["S2_ETH"]["rules"][r]["venues"][v]["marks"]["passed"] for r in RL for v in V) if "S2_ETH" in x else None
ethx=sum(km("ETHUSD",r,v)["passed"] for r in RL for v in V); eth0=sum(p0[f"{v}|ETHUSD|{r}"]["passed"] for r in RL for v in V)
btcx={v:[r for r in RL if km("BTCUSD",r,v)["passed"]] for v in V}; btc0={v:[r for r in RL if p0[f"{v}|BTCUSD|{r}"]["passed"]] for v in V}
bothv={v:[r for (vv,a,r) in both if vv==v and a=="BTCUSD"] for v in V}
ls=lambda l: ", ".join(l) if l else "none"
D=json.load(open("diag_x2_pbo.json"))
def diag():
    t="| Venue cost | Bitstamp prices from 2013-01-01 (replay 01) | Bitstamp prices from 2014-05-01 | Kraken prices from 2014-05-01 (X2) |\n|---|---|---|---|\n"
    for v in V: t+=f"| {v} | {D['Bitstamp|2013-01-01|'+v]['pbo']:.3f} | {D['Bitstamp|2014-05-01|'+v]['pbo']:.3f} | {D['Kraken|2014-05-01|'+v]['pbo']:.3f} |\n"
    return t
def diagsh(v):
    t="| Rule | Bitstamp from 2013-01-01 | Bitstamp from 2014-05-01 | Kraken from 2014-05-01 |\n|---|---|---|---|\n"
    a,b,c=D['Bitstamp|2013-01-01|'+v],D['Bitstamp|2014-05-01|'+v],D['Kraken|2014-05-01|'+v]
    t+=f"| Hold the coin | {a['bh_sharpe']:.2f} | {b['bh_sharpe']:.2f} | {c['bh_sharpe']:.2f} |\n"
    for r in RL: t+=f"| {r} | {a['sharpe_all'][r]:.2f} | {b['sharpe_all'][r]:.2f} | {c['sharpe_all'][r]:.2f} |\n"
    return t
for k_ in D:
    if '|Alpaca' in k_: assert all(v_>D[k_]['bh_sharpe'] for v_ in D[k_]['sharpe_all'].values())
m4only=sum(1 for c in changes if c[5]==["mark 4 overfitting"])
g=B["BTCUSD_close_gap_vs_bitstamp_bps"]; ge=B["ETHUSD_close_gap_vs_bitstamp_bps"]
doc=f"""# Replay 01 cross-check X2: the same rules on a second venue's full price history

Run on 2026-11-25 (UTC), the night of 2026-11-24 in Idaho. Uses the research rig in `research_rig/`.

Status: research evidence. Proposed by research. Nothing in this file is an owner decision. No account, key or order was involved.

Tags: every result number here is MEASURED by our own rig from Kraken's published daily price files. It does not mean "this will happen with real money".

## The question

Replay 01 (`docs/research/12_replay_01_crypto_trend.md`) used Bitstamp's prices. Does each pass or fail hold when the same rules are run on Kraken's own prices? A result that shows up on only one venue's prices is not a result.

## Bottom line

- {same} of {tot} verdicts are the same on both venues' prices. {len(changes)} changed.
- Bitcoin rules that pass on both sets of prices: at Binance.US cost {ls(bothv['Binance.US'])}; at Alpaca cost {ls(bothv['Alpaca'])}; at Kraken $10,000 tier cost {ls(bothv['Kraken $10k tier'])}; at Kraken entry cost {ls(bothv['Kraken entry'])}; at Coinbase entry cost {ls(bothv['Coinbase entry'])}.
- Ether: {eth0} passes on Bitstamp prices and {ethx} on Kraken prices, over 9 rules and 5 venue costs.
- Every change went the same way: a bitcoin rule that passed on Bitstamp prices failed on Kraken prices. {m4only} of the {len(changes)} changes come from mark 4 alone, the overfitting check.
- The held-back years reproduce almost exactly. The prices are not the cause.
- The cause is the dates. Kraken's bitcoin history starts 16 months later. A check made after the run shows the same rules fail mark 4 on Bitstamp's own prices too, once 2013 and early 2014 are left out.
- So replay 01's bitcoin passes depended on including 2013 and early 2014. That is a weakness in replay 01, and it is reported as one. Under the rule written before the run, a rule that passes on one set and fails on the other is treated as failed until explained. The explanation does not rescue the passes.
- What still stands: the held-back-years figures are nearly the same on both venues' prices (tables below), and every bitcoin rule has a higher whole-sample Sharpe than holding at Alpaca cost on both. What does not stand: the claim that one of the nine rules can be picked as the best.
- The longer ether sample (S2, from 2016-03-01) had {s2pass if s2pass is not None else 'no finished'} passes over 9 rules and 5 venue costs. It is a longer sample, not a second chance.

## What was fixed before the run

The full text is `research_rig/PREREG_01_X2_kraken_full_history.md`, pushed in commit c0ef884 before the rules were run on this data. Nothing new was tested: the same 9 rules, fills, costs, slices, five pass marks and seed as replay 01. No trial was added to the count of 20.

| Run | Coin | Test starts | Note |
|---|---|---|---|
| X2-BTC | Bitcoin | 2014-05-01 | Kraken's history starts later than Bitstamp's, so 2013 and early 2014 are missing. Marks 2 to 5 use this shorter sample |
| X2-ETH | Ether | 2018-03-05 | Same start as replay 01 |
| S2-ETH | Ether | 2016-03-01 | Two earlier years that Bitstamp does not have |

The held-back years (2023-01-01 to 2026-06-30) are the same dates on both venues, so mark 1 differs only because the prices differ.

## How closely the two venues' prices agree

| Measure | Bitcoin | Ether |
|---|---|---|
| Days compared | {g['days']:,} | {ge['days']:,} |
| Median gap between daily closes (bps) | {g['median']:.2f} | {ge['median']:.2f} |
| Gap on the worst 1% of days (bps) | {g['p99']:.1f} | {ge['p99']:.1f} |
| Largest gap (bps) | {g['max']:.1f} on {g['max_date']} | {ge['max']:.1f} on {ge['max_date']} |
| Days with no Kraken trades, filled with the last close | {B['BTCUSD_missing_days_filled']} ({B['BTCUSD_missing_after_test_start']} after the test start) | {B['ETHUSD_missing_days_filled']} ({B['ETHUSD_missing_after_test_start']} after the test start) |
| Kraken file against Kraken public bars, largest close gap over {B['BTCUSD_overlap_days']} shared days (bps) | {B['BTCUSD_archive_vs_api_close_max_bps']:.1f} | {B['ETHUSD_archive_vs_api_close_max_bps']:.1f} |

The largest bitcoin gap is in 2014, early in Kraken's history.

## Verdicts side by side

Rows where the rule failed on both venues' prices with the same marks are left out. All of them are in `research_rig/results_01x2.json`.

{vt}
## Every change of verdict

{chg()}
## Why the verdicts changed: the prices or the dates

This check was written after seeing the result above. It was not in the plan. It adds no trial and changes no verdict. The program is `research_rig/diag_x2_pbo.py`.

Mark 4 is the probability of overfitting. It asks: if the rule that looked best in one part of the history is picked, how often does it land in the bottom half in the other part. It must be under `backtest_max_pbo`. Bitcoin, by venue cost:

{diag()}
Whole-sample Sharpe of each rule at Alpaca cost, for the same three cases:

{diagsh('Alpaca')}
How to read it:

- At Binance.US cost on Kraken prices the miss is by a hair: {D['Kraken|2014-05-01|Binance.US']['pbo']:.4f} against a limit of 0.25 (`backtest_max_pbo`). The bar was not moved. At Alpaca cost it is not close.
- With the same start date, Bitstamp prices give a worse mark 4 than Kraken prices. So Kraken's prices are not what broke the pass.
- Research's reading: with 2013 and early 2014 included, the nine rules keep much the same order across the history, and mark 4 passes. With those months left out, the order is not stable, and mark 4 fails.
- Every rule still has a higher whole-sample Sharpe than holding at Alpaca cost in all three cases. Mark 4 does not say the trend rules are worse than holding. It says the data cannot tell which of the nine is best.
- The nine rules are close cousins. Picking a winner among them is the part that is not supported.

## The held-back years on both venues' prices

Bitcoin at Alpaca cost:

{heldtab('BTCUSD','Alpaca')}
Bitcoin at Binance.US cost:

{heldtab('BTCUSD','Binance.US')}
Ether at Binance.US cost:

{heldtab('ETHUSD','Binance.US')}
## The longer ether sample, S2, from 2016-03-01

The last five columns show the result against all five marks at each venue's cost.

{s2()}
## Limits

- Kraken's bitcoin history starts later, so the bitcoin samples are not the same length. A mark that differs can come from the missing 2013 and early 2014, not from the prices.
- Two venues agreeing does not make a result true. Both are spot prices for the same coins and move together.
- The terms of use for Kraken's published files are not stated on the page that offers them. UNKNOWN.
- The held-back years were already seen in replay 01.

## What research proposes from this

None of this is decided.

1. Change proposal 1 of `docs/decisions/0005-overnight-research-2026-11-25.md`. No bitcoin rule now has a clean pass. Stop describing P2, S50 and D20 as passed.
2. If practice trading of the slow bitcoin trend goes ahead, run it as observation, labelled "failed mark 4 on the shorter history", with P1 only. P1 was named as the main rule before any run, so using it involves no picking.
3. Do not lower `backtest_max_pbo` and do not drop mark 4. The mark did its job.
4. As a possible next test, written down before it is run: one blended rule that holds the average of the nine, so that nothing is picked. This would be a new trial and would be counted.
5. Use Kraken's published files as the rig's main crypto history from here on, and Bitstamp as the second source. Kraken publishes its files for download. Bitstamp's general terms are unclear about collecting its prices ([Bitstamp terms](https://www.bitstamp.net/terms-of-use/)).
6. Keep ether as observation only.

## How to reproduce

From `research_rig/`: `python3 fetch_kraken_archive.py`, `python3 build_kraken_daily.py`, `python3 run_01x2.py` (writes `results_01x2.json`), `python3 diag_x2_pbo.py` (writes `diag_x2_pbo.json`), then `python3 build_doc12b.py` (writes this file). Seed 7.
"""
open("../docs/research/12b_replay_01_kraken_crosscheck.md","w").write(doc); print(same,tot,len(changes)); print(chg()); print("both",bothv,"\nbtc0",btc0,"\nbtcx",btcx,"eth",eth0,ethx,"s2",s2pass)
