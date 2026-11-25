"""Builds docs/research/15 from results_03.json. Run after run_03.py."""
import json
o=json.load(open("results_03.json")); V=["Binance.US","Alpaca","Kraken $10k tier","Kraken entry","Coinbase entry"]; COST={"Binance.US":7,"Alpaca":30,"Kraken $10k tier":43,"Kraken entry":85,"Coinbase entry":95}
N=["H1","H2","H3","H4","H5","H6","H7","H8"]; AN={"BTCUSD":"Bitcoin","ETHUSD":"Ether"}
DESC={"H1":"Half-day momentum (primary)","H2":"Opening range breakout","H3":"Last hour timing","H4":"Buy the dip","H5":"Buy the dip in an uptrend","H6":"Hourly trend, no day-end exit","H7":"Half-day momentum, uptrend days only","H8":"Noise band"}
pc=lambda x,d=1: f"{x*100:+.{d}f}%"
def gross(a):
    A=o["assets"][a]; t="| Rule | Time invested | Round trips a year | Hours held | Average gain per round trip, before costs (bps) | Round trips that gained | Growth a year before costs | Break-even cost per side (bps) |\n|---|---|---|---|---|---|---|---|\n"
    for n in N:
        r=A["rules"][n]; g=r["gross_trips"]
        t+=f"| {n} {DESC[n]} | {r['exposure']*100:.0f}% | {g['per_year']:.0f} | {g['hours']:.1f} | {g['avg_bps']:+.1f} | {g['win']*100:.0f}% | {pc(r['gross']['all']['cagr'])} | {r['be_zero_bps']:.1f} |\n"
    return t
def net(a,sl="all"):
    A=o["assets"][a]; t="| Rule | "+" | ".join(f"{v} ({COST[v]} bps)" for v in V)+" |\n|---|"+"---|"*len(V)+"\n"
    t+="| Hold the coin | "+" | ".join(pc(A["bh"][v][sl]["cagr"]) for v in V)+" |\n"
    for n in N: t+=f"| {n} | "+" | ".join(pc(A["rules"][n]["venues"][v][sl]["cagr"]) for v in V)+" |\n"
    t+="| C1 control: always hold 12:00 to 24:00 | "+" | ".join(pc(A["C1"][v][sl]["cagr"]) for v in V)+" |\n"
    return t
def held(a,v):
    A=o["assets"][a]; b=A["bh"][v]["held"]; t="| Rule | Growth a year | Sharpe | Largest drop | Made money |\n|---|---|---|---|---|\n"
    t+=f"| Hold the coin | {pc(b['cagr'])} | {b['sharpe']:.2f} | {pc(b['maxdd'])} | {'yes' if b['total']>0 else 'no'} |\n"
    for n in N:
        h=A["rules"][n]["venues"][v]["held"]; t+=f"| {n} | {pc(h['cagr'])} | {h['sharpe']:.2f} | {pc(h['maxdd'])} | {'yes' if h['total']>0 else 'no'} |\n"
    return t
def marks(v):
    t="| Coin | Rule | Mark 1 held-back | Mark 2 break-even | Mark 3 deflated Sharpe | Mark 4 overfitting | Mark 5 shuffle | Result |\n|---|---|---|---|---|---|---|---|\n"
    for a in AN:
        for n in N:
            r=o["assets"][a]["rules"][n]; m=r["venues"][v]["marks"]; yn=lambda b: "pass" if b else "fail"
            t+=f"| {AN[a]} | {n} | {yn(m['m1'])} | {yn(m['m2'])} ({r['be_vs_bh_bps']:.1f} against {2*COST[v]} needed) | {yn(m['m3'])} ({m['dsr']:.2f}) | {yn(m['m4'])} ({o['assets'][a]['pbo'][v]:.2f}) | {yn(m['m5'])} ({m['shuffle']:.2f}) | {'PASS' if m['passed'] else 'fail'} |\n"
    return t
npass={v:sum(o["assets"][a]["rules"][n]["venues"][v]["marks"]["passed"] for a in AN for n in N) for v in V}
nmoney={v:sum(o["assets"][a]["rules"][n]["venues"][v]["marks"]["made_money_all"] for a in AN for n in N) for v in V}
nmoneyh={v:sum(o["assets"][a]["rules"][n]["venues"][v]["marks"]["made_money_held"] for a in AN for n in N) for v in V}
be=[o["assets"][a]["rules"][n]["be_zero_bps"] for a in AN for n in N]; bestbe=max(be)
gt=[o["assets"][a]["rules"][n]["gross_trips"]["avg_bps"] for a in AN for n in N]
summ="| Venue | Cost per side (bps) | Rules that passed all five marks, of 16 | Rules that made any money, whole sample | Rules that made any money, held-back years |\n|---|---|---|---|---|\n"
for v in V: summ+=f"| {v} | {COST[v]} | {npass[v]} | {nmoney[v]} | {nmoneyh[v]} |\n"
ngross=min(sum(o["assets"][a]["rules"][n]["gross"]["all"]["total"]>0 for n in N) for a in AN)
WORD={5:"Five",6:"Six",7:"Seven",8:"All eight"}[ngross]
for a in AN:
    assert max(o["assets"][a]["rules"],key=lambda n:o["assets"][a]["rules"][n]["be_zero_bps"])=="H7"
    assert all(o["assets"][a]["rules"][n]["venues"]["Binance.US"]["all"]["cagr"]<o["assets"][a]["bh"]["Binance.US"]["all"]["cagr"] for n in N)
h1b=o["assets"]["BTCUSD"]["rules"]["H1"]; h1e=o["assets"]["ETHUSD"]["rules"]["H1"]
doc=f"""# Replay 03: rules that trade inside the day, on hourly bitcoin and ether bars

Run on 2026-11-25 (UTC), the night of 2026-11-24 in Idaho. Uses the research rig in `research_rig/`.

Status: research evidence. Proposed by research. Nothing in this file is an owner decision. No account, key or order was involved.

Tags: every result number here is MEASURED by our own rig from Bitstamp's public hourly price bars. That means "our code worked this out from that data". It does not mean "this will happen with real money".

## The question

Replay 01 tested rules that hold for days or weeks. This one tests day trading itself: does any plain rule that gets in and out inside one day, on spot bitcoin and ether, make money after the fees a US retail account really pays?

## Bottom line

- No. Of 16 rule and coin pairs, {npass['Binance.US']} passed at Binance.US cost, {npass['Alpaca']} at Alpaca cost, and {npass['Kraken $10k tier']+npass['Kraken entry']+npass['Coinbase entry']} at Kraken or Coinbase cost.
- At Alpaca cost and above, {'every rule lost money' if nmoney['Alpaca']==0 else str(nmoney['Alpaca'])+' rules made money'}, and most lost nearly everything. The primary rule on bitcoin went from {pc(h1b['gross']['all']['cagr'])} a year before costs to {pc(h1b['venues']['Alpaca']['all']['cagr'])} a year after them.
- The patterns show up before costs. {WORD} of the eight rules made money before costs on both coins. The average gain per round trip, before costs, was between {min(gt):+.1f} and {max(gt):+.1f} bps.
- The cost is larger than the pattern. One buy and one sell costs 60 bps at Alpaca. The best rule's average gain per round trip was {max(gt):.1f} bps.
- Break-even cost per side ran from {min(be):.1f} to {bestbe:.1f} bps. Only Binance.US, at 7 bps per side, is under the better rules' break-even, and not by the margin the project requires (`backtest_min_breakeven_cost_multiple`).
- At Binance.US cost, {nmoney['Binance.US']} of 16 made some money over the whole sample, and none passed. They made less than holding, and they fail the check for luck (mark 3).
- This matches what research expected and wrote down before the run. It is in line with the one published study we hold, which research read as putting break-even cost near 10 bps ([University of Reading manuscript](https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf)). The patterns exist, and a retail fee eats them.

## Words used below

The same words as `docs/research/12_replay_01_crypto_trend.md`. Two more:

| Word | Meaning |
|---|---|
| Round trip | One buy and the sell that closes it |
| Day open | The price at 00:00 UTC. Crypto never closes, so the day is a choice |

## What was fixed before the run

The full text is `research_rig/PREREG_03_intraday_crypto.md`. It was pushed to the repo in commit d91ebba before any of these rules was run.

| Item | Fixed value |
|---|---|
| Data | Bitstamp hourly bars. Bitcoin test starts {o['start']['BTCUSD']}, ether {o['start']['ETHUSD']}, set by a data-only rule (under 1% of hours empty in every later year, and 4,800 hours of warm-up) |
| Fills | Signal on the close of one hourly bar, fill at the open of the next |
| Cost per side | Venue taker fee plus 5 bps: Binance.US 7, Alpaca 30, Kraken $10,000 tier 43, Kraken entry 85, Coinbase entry 95 |
| Rules | 8 per coin, 16 trials, numbers 27 to 42 in the trial ledger |
| Slices | Development to 2022-12-31. Held back 2023-01-01 to 2026-06-30. After the designer's knowledge cutoff 2026-07-01 to 2026-11-24 |
| Pass marks | The same five as replay 01, with 36 trials counted |

The rules:

| Id | Rule |
|---|---|
| H1 | Half-day momentum, the primary rule. At 12:00 UTC, if price is above the day open, buy. Sell at day end |
| H2 | Opening range breakout. Buy after the first hourly close above the high of the first four hours. Sell at day end |
| H3 | Last hour timing. If the first hour was up and the 22:00 hour was up, hold for the last hour only |
| H4 | Buy the dip. After an hourly fall of more than 2 standard deviations, buy and hold four hours |
| H5 | H4, only when price is above its 200 day average |
| H6 | Hourly trend with no day-end exit. Not strictly day trading |
| H7 | H1, only on days when the daily trend weight from replay 01 is 0.5 or more |
| H8 | Noise band. Buy when price moves above the day open by more than its usual move for that hour. Sell if it falls back under the day open, or at day end |

## Before costs: are the patterns there

Bitcoin, whole sample:

{gross('BTCUSD')}
Ether, whole sample:

{gross('ETHUSD')}
Break-even cost per side is the cost at which the rule's growth falls to zero.

## After costs: growth a year, whole sample

Bitcoin:

{net('BTCUSD')}
Ether:

{net('ETHUSD')}
The control C1 buys every day at 12:00 UTC and sells at day end, with no signal. It shows what paying the fee once a day does on its own.

## The held-back years, 2023-01-01 to 2026-06-30

At Binance.US cost, bitcoin:

{held('BTCUSD','Binance.US')}
At Binance.US cost, ether:

{held('ETHUSD','Binance.US')}
At Alpaca cost, bitcoin:

{held('BTCUSD','Alpaca')}
At Alpaca cost, ether:

{held('ETHUSD','Alpaca')}
## Pass marks

{summ}
Every mark for every rule at Binance.US cost, the only venue where anything came close:

{marks('Binance.US')}
At Alpaca cost:

{marks('Alpaca')}
Notes on reading the marks:

- Mark 4 (overfitting) passes easily at the high-cost venues. That is not good news. It passes because the ranking of the rules is stable: they all lose, in the same order.
- Mark 3 (deflated Sharpe) is harsh here because 36 trials are counted and their results are spread wide. That is how it was set before the run.

## After the designer's knowledge cutoff, 2026-07-01 to 2026-11-24

Growth over the slice is stated as a yearly rate, so short-slice figures look large. Bitcoin:

{net('BTCUSD','post')}
Ether:

{net('ETHUSD','post')}
## What this does and does not show

- It shows that eight textbook day trading rules on the two most liquid coins do not survive the taker fees of the venues an Idaho account can use, except possibly Binance.US, where they still fail the pass marks.
- It does not show that no day trading rule can work. Eight rules is not every rule. A rule nobody has published could exist. The base rate in `docs/research/01_stock_daytrading_evidence.md` says most people who look do not find one.
- Limit orders were not tested. A limit order pays the lower maker fee, or none, but it only fills when the price comes to it, which is often when the trade is about to go wrong. The rig cannot model that from hourly bars. UNKNOWN.
- Hourly bars from one venue. A fill at the hourly open with 5 bps of slippage is an assumption.
- The held-back years were already used by replay 01 for daily rules.
- Stocks were not tested here. Stock day trading has no fee at Alpaca and much smaller spreads on the large funds, so the answer for stocks could differ. That needs minute data, which is a purchase (`docs/research/10_historical_data_and_practice.md`).
- The first run of the program stopped at the step that saves the results, before any result was read. The save step was fixed and the run repeated. No rule, cost or mark was changed.

## What research proposes from this

None of this is decided.

1. Do not day trade crypto at Alpaca, Kraken or Coinbase taker fees. Every rule tested lost money there, most of them nearly all of it.
2. Treat the fee as the first question for any fast rule. A rule needs an average gain per round trip of at least twice the round trip cost before it is worth a practice run. `intraday_trend_max_round_trip_bps` in the config already says this for stocks.
3. Keep H7 (half-day momentum on uptrend days only) on a watch list for Binance.US, not for practice trading. It had the highest break-even cost on both coins and it still failed.
4. Put the day trading question to stocks next, where the fee is zero, once minute data is bought. Write the plan down first.
5. Keep the slow trend rules from replay 01 as the only crypto idea still under test. They trade far less often (turnover figures are in `docs/research/12_replay_01_crypto_trend.md`). Their own weakness is in `docs/research/12b_replay_01_kraken_crosscheck.md`.

## How to reproduce

From `research_rig/`: `python3 fetch.py hourly`, then `python3 run_03.py` (writes `results_03.json`), then `python3 build_doc15.py` (writes this file). Seed 7.
"""
BANNER = "Correction, 2026-11-25: two separate code audits found faults in how this run measured its results. The verdict tables below are the first run and are kept as the record. The corrected verdicts are in `docs/research/16_rig_audit.md`. Read that before using any number here."
head, rest = doc.split("\n", 1); doc = head + "\n\n" + BANNER + "\n" + rest   # the correction note is part of the page, so a rebuild keeps it
open("../docs/research/15_replay_03_intraday_crypto.md","w").write(doc); print(len(doc), npass, nmoney, nmoneyh)
