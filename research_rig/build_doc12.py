"""Builds docs/research/12 from tables_01.md. Run after tables_01.py."""
import re,subprocess
t=open("tables_01.md").read()
def sec(name):
    m=re.search(r"### "+re.escape(name)+r"[^\n]*\n(.*?)(?=\n### |\Z)",t,re.S); return m.group(1).strip()
T1=sec("T1"); T2=sec("T2"); T3=sec("T3 pass marks"); T3b=sec("T3b"); T4=sec("T4"); T5=sec("T5"); T6=sec("T6"); T7=sec("T7")
T4t,T4d=T4.rsplit("\n",1)
for a,b in [("BTCUSD","Bitcoin"),("ETHUSD","Ether")]:
    T1=T1.replace(a,b); T2=T2.replace(a,b); T3=T3.replace(a,b); T5=T5.replace(a,b); T6=T6.replace(a,b)
doc=f"""# Replay 01: slow trend rules on bitcoin and ether, with real fees

Run on 2026-11-25 (UTC), the evening of 2026-11-24 in Idaho. This is the first result from the research rig in `research_rig/`.

Status: research evidence. Proposed by research. Nothing in this file is an owner decision. The rig is a research tool. It is not the product and no product code was written.

Update, later the same night: a cross-check on a second venue's prices (`docs/research/12b_replay_01_kraken_crosscheck.md`) found that the bitcoin passes below depend on including 2013 and early 2014. On a history that starts 2014-05-01, no bitcoin rule passes mark 4, on either venue's prices. The numbers in this file were not changed. Read the passes below with that in mind.

Tags: every result number in this file is MEASURED by our own rig from Bitstamp's public price bars, by the commands listed at the end. That means "our code worked this out from that data". It does not mean "this will happen with real money".

## The question

Does a plain rule that holds a coin while its price trend is up, and sits in cash when it is not, beat simply holding the coin, after the fees a US retail account really pays?

## Bottom line

- Bitcoin, at low fees: yes on this history. At Binance.US cost, 5 of 9 rules passed all five pass marks. At Alpaca cost, 3 of 9 passed.
- The rule named in advance as the main one (P1) failed at Alpaca cost. It missed the first mark by a hair: Sharpe 0.99 against 1.00 for holding, on the held-back years. The bar was not moved. It is a fail.
- Bitcoin, at high fees: no. At Kraken's $10,000 tier, Kraken entry and Coinbase entry cost, no rule passed.
- Ether: no rule passed at any venue. The rules beat holding on paper, but the result fails both checks for luck (marks 3 and 4).
- What the rules really did: they cut the worst falls roughly in half, and they gave up a large part of the gains in strong years. Since 2023 they earned less than holding bitcoin at every venue's cost.
- These are multi-day rules. They trade about 18 times the account a year. This is not day trading, and it says nothing yet about day trading.
- A pass here means "worth running in the practice account". It does not mean "makes money".

## Plain words used below

| Word | Meaning |
|---|---|
| Hold | Buy once at the start and never sell |
| Sharpe | Average return divided by how bumpy the ride was, per year. Higher is better. Cash is counted as earning nothing |
| Largest drop | The biggest fall from a high point to a later low point |
| bps | Hundredths of a percent. 30 bps is 0.30% |
| Cost per side | What one buy or one sell costs: the venue's taker fee plus 5 bps for spread and price impact |
| Break-even cost | The cost per side at which the rule stops beating hold |
| Held-back slice | 2023-01-01 to 2026-06-30. The rules were fixed before they were run on it |
| Deflated Sharpe | A Sharpe that is marked down for the number of rules tried. Above the mark means luck alone is an unlikely explanation |
| Overfitting probability | How often the rule that looked best on one half of the history did worse than the middle of the pack on the other half |
| Shuffle percentile | The rule's own in and out spells, put in random order 1,000 times. The share of those random orders that the real rule beat |

## What was fixed before the run

The full text is `research_rig/PREREG_01_daily_crypto_trend.md`, written at 06:35 UTC before any rule touched the data. One amendment was made at 06:37 UTC, before the first run: ether data moved from Coinbase to Bitstamp, and the second source moved from Coinbase to Kraken, because of Coinbase's data terms and one bad bar.

| Item | Fixed value |
|---|---|
| Data | Bitstamp daily bars. Bitcoin 2013-01-01 to 2026-11-24. Ether 2018-03-05 to 2026-11-24 |
| Fills | The rule decides on the daily close. The trade fills at the next open |
| Venues and cost per side | Binance.US 7 bps, Alpaca 30, Kraken $10,000 tier 43, Kraken entry 85, Coinbase entry 95. Fees are from `docs/research/09_brokers_and_venues.md` |
| Cash | Earns nothing |
| Leverage, shorting | None |
| Trials | 9 rules on each coin, plus 2 half-and-half portfolios: 20 trials, all in `research_rig/TRIAL_LEDGER.md` |
| Slices | Development to 2022-12-31. Held back 2023-01-01 to 2026-06-30. After the model's knowledge cutoff 2026-07-01 to 2026-11-24 |

The nine rules:

| Id | Rule |
|---|---|
| P1 | The main rule. Hold a quarter of the money for each of these that is true: the close is above its 20, 50, 100, 200 day average |
| P2 | P1, scaled down when the coin has been very bumpy over the last 30 days |
| S50, S100, S200 | All in when the close is above its 50, 100 or 200 day average. Otherwise cash |
| D20, D55 | Buy on the highest close of the last 20 (55) days. Sell on the lowest close of the last 10 (20) days |
| M30, M90 | All in when the close is above the close 30 (90) days ago. Otherwise cash |

The five pass marks. A rule passes for a venue only if all five hold at that venue's cost:

| Mark | Test | Threshold key in `config/thresholds.yaml` |
|---|---|---|
| 1 | Held-back slice: Sharpe above hold, and largest drop no more than a set share of hold's largest drop | `replay_max_drop_ratio_vs_hold` |
| 2 | Whole sample: break-even cost against hold is at least a set multiple of the venue's cost | `backtest_min_breakeven_cost_multiple` |
| 3 | Whole sample: deflated Sharpe above the mark, with all 20 trials counted | `replay_min_deflated_sharpe` |
| 4 | Overfitting probability under the mark | `backtest_max_pbo` |
| 5 | Shuffle percentile above the mark | `replay_min_shuffle_percentile` |

Three of those keys are new house numbers that this replay proposed. They are in the config with status `builder` (called `proposed` at the time).

## Engine checks that passed first

Run with `python3 fixtures.py`. All passed before any result was read.

- A hand-worked trade gives the hand-worked profit.
- A hand-worked trade with fees gives the hand-worked result.
- Holding equals the coin's return less one side of cost.
- A rule allowed to peek at tomorrow's close does far better than the honest one. So the one-bar delay is real.
- Random entries on a price with no drift lose about what they pay in costs.
- The account never borrows.
- Two runs give the same output.

## Results

### Whole sample, at Alpaca cost (30 bps a side)

{T1}

Reading this table:

- The bitcoin figures are dominated by 2013 and 2017. Nobody should expect those years again.
- The 90% range for the Sharpe difference against hold includes zero for every bitcoin rule except P2, and for every ether rule. So on the whole sample only P2 on bitcoin is clearly better than hold on a risk-adjusted basis.
- P1 made 875 bitcoin trades in under 14 years. It moves in quarter steps, so it trades often.

### The held-back years, 2023-01-01 to 2026-06-30, at each venue's cost

{T2}

Reading this table:

- Bitcoin: hold grew faster than P1 and P2 at every venue. The rules only win on Sharpe, and only at Binance.US cost (and P2 at Alpaca cost). They do have much smaller drops.
- Ether: hold did poorly in these years, so the rules beat it at Binance.US, Alpaca and Kraken's $10,000 tier. At Kraken entry and Coinbase entry cost the fees take most or all of the gain.

### Pass marks

{T3}

Detail for the two main rules:

{T3b}

Reading these tables:

- Mark 1 is the one that separates the venues for bitcoin. The same rule passes at 7 bps and fails at 43.
- Ether fails marks 3 and 4 everywhere. Which ether rule looked best changed from one part of the history to another, which is what choosing by luck looks like.
- Three bitcoin rules pass at Alpaca cost and the main rule does not. Nine rules were run on the same held-back years, so one or two passing mark 1 by chance is expected. Marks 3 to 5 guard against that only in part.

### Half bitcoin, half ether, from 2018-03-05

{T4t}

Deflated Sharpe for the portfolios, at Alpaca cost: {T4d.replace("Portfolio deflated Sharpe: ","")}. Both are under the mark, so both portfolios fail mark 3. The "after cutoff" rows are yearly rates worked out from only 147 days, so they look larger than the plain returns in the section below.

### Year by year, at Alpaca cost

This table was not in the pre-registration. It describes the same trials and adds no new rule. 2026 runs to November 24.

{T5}

The pattern is the same in every cycle. In falling years the rules lost far less (2018, 2022, 2026). In strong years they made far less (2017, 2020, 2021, 2023, 2024). In flat, choppy years they lost a little to costs and false starts (2025 for bitcoin).

### After the model's knowledge cutoff, 2026-07-01 to 2026-11-24

This slice is 147 days. It is too short to prove anything and is reported because it was promised.

- Bitcoin: hold -0.7%, P1 +8.5%, P2 +7.9%. Other rules ranged from -17.7% (M90) to +21.3% (M30).
- Ether: hold +4.0%, P1 +11.9%, P2 +6.6%. Other rules ranged from -22.0% (M90) to +36.9% (S50).

The spread between rules in one short window is larger than any difference between a rule and hold. That is the noise level to keep in mind.

## Two checks on the method

### Second price source

Kraken's public daily bars cover the last 720 days. Same rules, same cost, Alpaca's 30 bps.

{T7}

The two sources agree to about 1 bp on a normal day and the results match. P2's target differs on many days because it is a sliding scale, and the differences are tiny. Over these 720 days both coins fell hard, and bitcoin P1 still lost 11.2%. A trend rule limits a fall. It does not turn a falling market into a gain.

### What if the fill is late

Crypto never closes, so on these bars the next open is the same moment as the close the rule just read. A real program needs time to act. This check was written down in `research_rig/PREREG_01_S1_fill_delay.md` before it was run. It adds no new rule and has no pass mark. Each cell shows Sharpe for three fills: at the next open / one hour late / one full day late.

{T6}

- One hour late changes almost nothing, even though the price typically moves 29 bps (bitcoin) or 41 bps (ether) in that hour. The moves are in both directions and wash out.
- One day late is a different story for ether: P1's held-back Sharpe falls from 0.65 to 0.46 at Alpaca cost. Bitcoin barely moves.
- So the program must act within the hour after the daily close, and the ether result is fragile.

## What this does not show

- The rules were picked by a model that has read the price history of both coins up to June 2026. They are textbook rules, and textbooks keep the rules that worked. The held-back slice cannot fix that. Only running forward can.
- Taxes are not in it. P1 made hundreds of trades, and gains on anything held a year or less are taxed as ordinary income. Holding puts the tax off. After tax, the gap between a trading rule and hold gets worse for the rule. How much depends on his tax position. UNKNOWN.
- Cash earned nothing here. In real life idle dollars can earn interest. That would help the rules, which sit in cash about 40% to 70% of the time.
- Real fills on small orders were not measured. The 5 bps allowance comes from one evening of order book readings in research 09.
- Drops are measured on daily closes. Falls inside a day were deeper.
- One exchange's price history. Bitstamp's terms for personal research use could not be read (the page did not load). UNKNOWN. The raw bars are not stored in this repo. `fetch.py` downloads them again.
- Nothing here is intraday. Whether true day trading survives these fees has not been tested yet.

## What research proposes from this

None of this is decided. Each line is for the owner to accept, change or decline.

Update: research withdraws proposal 1 as worded here. The replacement is in `docs/research/12b_replay_01_kraken_crosscheck.md`. Proposal 5's first test is done: `docs/research/15_replay_03_intraday_crypto.md`.

1. Carry three bitcoin rules into practice trading as candidates: P2, S50 and D20. They passed at Alpaca cost. P1 goes too, clearly labelled as having failed mark 1 at Alpaca cost, so its live behaviour can be compared.
2. Run ether in practice for observation only, labelled as having failed the replay.
3. Treat fees as part of the rule. At 85 bps a side and above, nothing passed. This supports not trading crypto on Kraken entry or Coinbase entry tiers, and keeps the live crypto venue question open until practice results exist.
4. At the time, the recommendation was to keep the three new house numbers as proposed in the config until the owner confirmed or changed them.
5. Test next, each with its own written plan before it runs: intraday rules on hourly bars against each venue's fees. A slow trend rule on a wider basket of liquid coins, which needs price history that includes dead coins. Trend rules on stock funds, which needs a licensed data source (see research 10).

## How to reproduce

From `research_rig/`, with Python 3, numpy, pandas and scipy:

| Step | Command | Output |
|---|---|---|
| Download the bars | `python3 fetch.py crypto`, then `kraken`, then `hourly` | `data/` (not stored in the repo) |
| Engine checks | `python3 fixtures.py` | prints ALL PASS |
| Replay | `python3 run_01.py` | `results_01.json` |
| Pass marks per venue | `python3 run_01b.py` | `passmarks_01.json` |
| Cross-check and fill delay | `python3 run_01c.py` | `results_01c.json` |
| Year table | `python3 report_01d.py` | `results_01d.json` |
| The tables in this file | `python3 tables_01.py` | `tables_01.md` |

Seed 7 throughout. Bars downloaded later will include new days, so the last rows will differ. The unfinished bar for the download day is dropped.
"""
BANNER = "Correction, 2026-11-25: two separate code audits found faults in how this run measured its results. The verdict tables below are the first run and are kept as the record. The corrected verdicts are in `docs/research/16_rig_audit.md`. Read that before using any number here."
head, rest = doc.split("\n", 1); doc = head + "\n\n" + BANNER + "\n" + rest   # the correction note is part of the page, so a rebuild keeps it
open("../docs/research/12_replay_01_crypto_trend.md","w").write(doc)
print(len(doc))
