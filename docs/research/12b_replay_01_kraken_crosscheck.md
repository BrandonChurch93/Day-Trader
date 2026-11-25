# Replay 01 cross-check X2: the same rules on a second venue's full price history

Correction, 2026-11-25: two separate code audits found faults in how this run measured its results. The verdict tables below are the first run and are kept as the record. The corrected verdicts are in `docs/research/16_rig_audit.md`. Read that before using any number here.

Run on 2026-11-25 (UTC), the night of 2026-11-24 in Idaho. Uses the research rig in `research_rig/`.

Status: research evidence. Proposed by research. Nothing in this file is an owner decision. No account, key or order was involved.

Tags: every result number here is MEASURED by our own rig from Kraken's published daily price files. It does not mean "this will happen with real money".

## The question

Replay 01 (`docs/research/12_replay_01_crypto_trend.md`) used Bitstamp's prices. Does each pass or fail hold when the same rules are run on Kraken's own prices? A result that shows up on only one venue's prices is not a result.

## Bottom line

- 82 of 90 verdicts are the same on both venues' prices. 8 changed.
- Bitcoin rules that pass on both sets of prices: at Binance.US cost none; at Alpaca cost none; at Kraken $10,000 tier cost none; at Kraken entry cost none; at Coinbase entry cost none.
- Ether: 0 passes on Bitstamp prices and 0 on Kraken prices, over 9 rules and 5 venue costs.
- Every change went the same way: a bitcoin rule that passed on Bitstamp prices failed on Kraken prices. 7 of the 8 changes come from mark 4 alone, the overfitting check.
- The held-back years reproduce almost exactly. The prices are not the cause.
- The cause is the dates. Kraken's bitcoin history starts 16 months later. A check made after the run shows the same rules fail mark 4 on Bitstamp's own prices too, once 2013 and early 2014 are left out.
- So replay 01's bitcoin passes depended on including 2013 and early 2014. That is a weakness in replay 01, and it is reported as one. Under the rule written before the run, a rule that passes on one set and fails on the other is treated as failed until explained. The explanation does not rescue the passes.
- What still stands: the held-back-years figures are nearly the same on both venues' prices (tables below), and every bitcoin rule has a higher whole-sample Sharpe than holding at Alpaca cost on both. What does not stand: the claim that one of the nine rules can be picked as the best.
- The longer ether sample (S2, from 2016-03-01) had 0 passes over 9 rules and 5 venue costs. It is a longer sample, not a second chance.

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
| Days compared | 4,591 | 3,187 |
| Median gap between daily closes (bps) | 4.33 | 3.01 |
| Gap on the worst 1% of days (bps) | 357.2 | 32.7 |
| Largest gap (bps) | 1839.6 on 2014-09-18 | 496.7 on 2019-07-14 |
| Days with no Kraken trades, filled with the last close | 12 (10 after the test start) | 6 (1 after the test start) |
| Kraken file against Kraken public bars, largest close gap over 665 shared days (bps) | 0.0 | 0.0 |

The largest bitcoin gap is in 2014, early in Kraken's history.

## Verdicts side by side

Rows where the rule failed on both venues' prices with the same marks are left out. All of them are in `research_rig/results_01x2.json`.

| Venue cost | Coin | Rule | On Bitstamp prices | On Kraken prices | Marks that differ |
|---|---|---|---|---|---|
| Binance.US | Bitcoin | P1 | PASS | fail | mark 4 overfitting |
| Binance.US | Bitcoin | P2 | PASS | fail | mark 4 overfitting |
| Binance.US | Bitcoin | S50 | PASS | fail | mark 4 overfitting |
| Binance.US | Bitcoin | S100 | fail | fail | mark 4 overfitting |
| Binance.US | Bitcoin | S200 | fail | fail | mark 4 overfitting, mark 5 shuffle |
| Binance.US | Bitcoin | D20 | PASS | fail | mark 4 overfitting |
| Binance.US | Bitcoin | D55 | fail | fail | mark 4 overfitting |
| Binance.US | Bitcoin | M30 | fail | fail | mark 4 overfitting |
| Binance.US | Bitcoin | M90 | PASS | fail | mark 4 overfitting, mark 5 shuffle |
| Binance.US | Ether | P2 | fail | fail | mark 3 deflated Sharpe |
| Binance.US | Ether | S50 | fail | fail | mark 3 deflated Sharpe |
| Binance.US | Ether | D20 | fail | fail | mark 3 deflated Sharpe |
| Binance.US | Ether | D55 | fail | fail | mark 3 deflated Sharpe |
| Binance.US | Ether | M30 | fail | fail | mark 3 deflated Sharpe |
| Alpaca | Bitcoin | P1 | fail | fail | mark 4 overfitting |
| Alpaca | Bitcoin | P2 | PASS | fail | mark 4 overfitting |
| Alpaca | Bitcoin | S50 | PASS | fail | mark 4 overfitting |
| Alpaca | Bitcoin | S100 | fail | fail | mark 4 overfitting |
| Alpaca | Bitcoin | S200 | fail | fail | mark 4 overfitting, mark 5 shuffle |
| Alpaca | Bitcoin | D20 | PASS | fail | mark 4 overfitting |
| Alpaca | Bitcoin | D55 | fail | fail | mark 4 overfitting |
| Alpaca | Bitcoin | M30 | fail | fail | mark 4 overfitting |
| Alpaca | Bitcoin | M90 | fail | fail | mark 4 overfitting, mark 5 shuffle |
| Alpaca | Ether | P2 | fail | fail | mark 3 deflated Sharpe |
| Alpaca | Ether | D20 | fail | fail | mark 3 deflated Sharpe |
| Alpaca | Ether | D55 | fail | fail | mark 3 deflated Sharpe |
| Kraken $10k tier | Bitcoin | S200 | fail | fail | mark 5 shuffle |
| Kraken $10k tier | Bitcoin | M90 | fail | fail | mark 5 shuffle |
| Kraken $10k tier | Ether | P2 | fail | fail | mark 3 deflated Sharpe |
| Kraken $10k tier | Ether | D55 | fail | fail | mark 3 deflated Sharpe |
| Kraken entry | Bitcoin | S100 | fail | fail | mark 5 shuffle |
| Kraken entry | Bitcoin | S200 | fail | fail | mark 5 shuffle |
| Kraken entry | Bitcoin | M90 | fail | fail | mark 5 shuffle |
| Coinbase entry | Bitcoin | S100 | fail | fail | mark 5 shuffle |
| Coinbase entry | Bitcoin | S200 | fail | fail | mark 5 shuffle |
| Coinbase entry | Bitcoin | D55 | fail | fail | mark 2 break-even |
| Coinbase entry | Bitcoin | M90 | fail | fail | mark 3 deflated Sharpe |
| Coinbase entry | Ether | S50 | fail | fail | mark 5 shuffle |
| Coinbase entry | Ether | D55 | fail | fail | mark 1 held-back |

## Every change of verdict

- Bitcoin P1 at Binance.US cost: PASS on Bitstamp prices, fail on Kraken prices. Differs on mark 4 overfitting. Held-back Sharpe 1.15 against 1.00 for holding on Bitstamp, 1.15 against 1.00 on Kraken. Drop ratio 0.54 and 0.54. Deflated Sharpe 1.00 and 1.00. Shuffle 1.00 and 1.00.
- Bitcoin P2 at Binance.US cost: PASS on Bitstamp prices, fail on Kraken prices. Differs on mark 4 overfitting. Held-back Sharpe 1.22 against 1.00 for holding on Bitstamp, 1.23 against 1.00 on Kraken. Drop ratio 0.40 and 0.39. Deflated Sharpe 1.00 and 1.00. Shuffle 1.00 and 1.00.
- Bitcoin S50 at Binance.US cost: PASS on Bitstamp prices, fail on Kraken prices. Differs on mark 4 overfitting. Held-back Sharpe 1.38 against 1.00 for holding on Bitstamp, 1.39 against 1.00 on Kraken. Drop ratio 0.51 and 0.50. Deflated Sharpe 1.00 and 1.00. Shuffle 1.00 and 1.00.
- Bitcoin D20 at Binance.US cost: PASS on Bitstamp prices, fail on Kraken prices. Differs on mark 4 overfitting. Held-back Sharpe 1.17 against 1.00 for holding on Bitstamp, 1.18 against 1.00 on Kraken. Drop ratio 0.54 and 0.54. Deflated Sharpe 1.00 and 1.00. Shuffle 1.00 and 1.00.
- Bitcoin M90 at Binance.US cost: PASS on Bitstamp prices, fail on Kraken prices. Differs on mark 4 overfitting, mark 5 shuffle. Held-back Sharpe 1.04 against 1.00 for holding on Bitstamp, 1.04 against 1.00 on Kraken. Drop ratio 0.55 and 0.55. Deflated Sharpe 0.99 and 0.98. Shuffle 0.98 and 0.93.
- Bitcoin P2 at Alpaca cost: PASS on Bitstamp prices, fail on Kraken prices. Differs on mark 4 overfitting. Held-back Sharpe 1.06 against 1.00 for holding on Bitstamp, 1.07 against 1.00 on Kraken. Drop ratio 0.45 and 0.45. Deflated Sharpe 1.00 and 1.00. Shuffle 1.00 and 1.00.
- Bitcoin S50 at Alpaca cost: PASS on Bitstamp prices, fail on Kraken prices. Differs on mark 4 overfitting. Held-back Sharpe 1.24 against 1.00 for holding on Bitstamp, 1.24 against 1.00 on Kraken. Drop ratio 0.54 and 0.54. Deflated Sharpe 1.00 and 1.00. Shuffle 1.00 and 1.00.
- Bitcoin D20 at Alpaca cost: PASS on Bitstamp prices, fail on Kraken prices. Differs on mark 4 overfitting. Held-back Sharpe 1.04 against 1.00 for holding on Bitstamp, 1.05 against 1.00 on Kraken. Drop ratio 0.59 and 0.58. Deflated Sharpe 1.00 and 1.00. Shuffle 1.00 and 1.00.

## Why the verdicts changed: the prices or the dates

This check was written after seeing the result above. It was not in the plan. It adds no trial and changes no verdict. The program is `research_rig/diag_x2_pbo.py`.

Mark 4 is the probability of overfitting. It asks: if the rule that looked best in one part of the history is picked, how often does it land in the bottom half in the other part. It must be under `backtest_max_pbo`. Bitcoin, by venue cost:

| Venue cost | Bitstamp prices from 2013-01-01 (replay 01) | Bitstamp prices from 2014-05-01 | Kraken prices from 2014-05-01 (X2) |
|---|---|---|---|
| Binance.US | 0.120 | 0.468 | 0.250 |
| Alpaca | 0.203 | 0.625 | 0.404 |
| Kraken $10k tier | 0.262 | 0.725 | 0.511 |
| Kraken entry | 0.401 | 0.689 | 0.784 |
| Coinbase entry | 0.411 | 0.627 | 0.756 |

Whole-sample Sharpe of each rule at Alpaca cost, for the same three cases:

| Rule | Bitstamp from 2013-01-01 | Bitstamp from 2014-05-01 | Kraken from 2014-05-01 |
|---|---|---|---|
| Hold the coin | 1.18 | 0.92 | 0.91 |
| P1 | 1.45 | 1.20 | 1.18 |
| P2 | 1.68 | 1.31 | 1.30 |
| S50 | 1.40 | 1.24 | 1.26 |
| S100 | 1.40 | 1.12 | 1.08 |
| S200 | 1.28 | 1.05 | 1.02 |
| D20 | 1.53 | 1.21 | 1.17 |
| D55 | 1.46 | 1.21 | 1.15 |
| M30 | 1.28 | 1.07 | 1.03 |
| M90 | 1.23 | 0.96 | 0.95 |

How to read it:

- At Binance.US cost on Kraken prices the miss is by a hair: 0.2501 against a limit of 0.25 (`backtest_max_pbo`). The bar was not moved. At Alpaca cost it is not close.
- With the same start date, Bitstamp prices give a worse mark 4 than Kraken prices. So Kraken's prices are not what broke the pass.
- Research's reading: with 2013 and early 2014 included, the nine rules keep much the same order across the history, and mark 4 passes. With those months left out, the order is not stable, and mark 4 fails.
- Every rule still has a higher whole-sample Sharpe than holding at Alpaca cost in all three cases. Mark 4 does not say the trend rules are worse than holding. It says the data cannot tell which of the nine is best.
- The nine rules are close cousins. Picking a winner among them is the part that is not supported.

## The held-back years on both venues' prices

Bitcoin at Alpaca cost:

| Rule | Held-back Sharpe, Bitstamp | Held-back Sharpe, Kraken | Largest drop, Bitstamp | Largest drop, Kraken | Growth a year, Bitstamp | Growth a year, Kraken |
|---|---|---|---|---|---|---|
| Hold the coin | 1.00 | 1.00 | -53.1% | -53.1% | +43.2% | +43.4% |
| P1 | 0.99 | 0.99 | -31.1% | -31.4% | +31.3% | +31.2% |
| P2 | 1.06 | 1.07 | -23.9% | -23.8% | +29.2% | +29.4% |
| S50 | 1.24 | 1.24 | -28.7% | -28.8% | +44.3% | +44.5% |
| S100 | 0.93 | 0.93 | -38.1% | -38.0% | +30.9% | +31.0% |
| S200 | 0.94 | 0.94 | -33.1% | -33.1% | +33.3% | +33.4% |
| D20 | 1.04 | 1.05 | -31.1% | -31.0% | +30.2% | +30.5% |
| D55 | 0.99 | 0.89 | -34.4% | -37.6% | +28.3% | +24.7% |
| M30 | 0.85 | 0.84 | -39.8% | -40.7% | +26.4% | +25.9% |
| M90 | 0.95 | 0.95 | -32.0% | -32.1% | +32.4% | +32.4% |

Bitcoin at Binance.US cost:

| Rule | Held-back Sharpe, Bitstamp | Held-back Sharpe, Kraken | Largest drop, Bitstamp | Largest drop, Kraken | Growth a year, Bitstamp | Growth a year, Kraken |
|---|---|---|---|---|---|---|
| Hold the coin | 1.00 | 1.00 | -53.1% | -53.1% | +43.3% | +43.4% |
| P1 | 1.15 | 1.15 | -28.6% | -28.8% | +38.1% | +38.0% |
| P2 | 1.22 | 1.23 | -21.1% | -20.9% | +35.0% | +35.2% |
| S50 | 1.38 | 1.39 | -26.8% | -26.8% | +51.5% | +51.8% |
| S100 | 1.03 | 1.03 | -35.6% | -35.6% | +35.8% | +35.9% |
| S200 | 0.99 | 1.00 | -31.6% | -31.6% | +36.1% | +36.2% |
| D20 | 1.17 | 1.18 | -28.9% | -28.7% | +35.6% | +36.0% |
| D55 | 1.06 | 0.96 | -32.8% | -35.6% | +30.7% | +27.2% |
| M30 | 1.07 | 1.06 | -35.5% | -35.6% | +36.4% | +35.9% |
| M90 | 1.04 | 1.04 | -29.0% | -29.1% | +36.8% | +36.9% |

Ether at Binance.US cost:

| Rule | Held-back Sharpe, Bitstamp | Held-back Sharpe, Kraken | Largest drop, Bitstamp | Largest drop, Kraken | Growth a year, Bitstamp | Growth a year, Kraken |
|---|---|---|---|---|---|---|
| Hold the coin | 0.44 | 0.44 | -67.6% | -67.6% | +8.0% | +8.0% |
| P1 | 0.77 | 0.77 | -37.7% | -37.6% | +25.3% | +25.5% |
| P2 | 0.88 | 0.88 | -27.6% | -27.7% | +22.9% | +22.9% |
| S50 | 0.96 | 0.96 | -41.5% | -41.4% | +38.2% | +38.3% |
| S100 | 0.69 | 0.70 | -46.3% | -46.1% | +23.0% | +23.2% |
| S200 | 0.72 | 0.72 | -38.1% | -38.2% | +25.0% | +25.0% |
| D20 | 0.32 | 0.32 | -50.5% | -50.5% | +5.0% | +5.2% |
| D55 | 0.64 | 0.63 | -34.7% | -34.7% | +18.0% | +17.6% |
| M30 | 0.85 | 0.86 | -42.0% | -41.9% | +32.2% | +32.6% |
| M90 | 0.65 | 0.66 | -42.5% | -42.5% | +21.6% | +21.9% |

## The longer ether sample, S2, from 2016-03-01

The last five columns show the result against all five marks at each venue's cost.

| Rule | Whole-sample growth a year at Binance.US cost | Sharpe | Largest drop | Binance.US | Alpaca | Kraken $10k tier | Kraken entry | Coinbase entry |
|---|---|---|---|---|---|---|---|---|
| Hold the coin | +65.3% | 1.01 | -94.1% | | | | | |
| P1 | +95.4% | 1.35 | -56.9% | fail | fail | fail | fail | fail |
| P2 | +48.3% | 1.42 | -32.8% | fail | fail | fail | fail | fail |
| S50 | +97.7% | 1.34 | -65.0% | fail | fail | fail | fail | fail |
| S100 | +64.9% | 1.05 | -74.4% | fail | fail | fail | fail | fail |
| S200 | +86.8% | 1.21 | -81.5% | fail | fail | fail | fail | fail |
| D20 | +107.9% | 1.48 | -54.5% | fail | fail | fail | fail | fail |
| D55 | +94.1% | 1.41 | -56.2% | fail | fail | fail | fail | fail |
| M30 | +103.6% | 1.36 | -73.4% | fail | fail | fail | fail | fail |
| M90 | +66.4% | 1.05 | -77.6% | fail | fail | fail | fail | fail |

## Limits

- Kraken's bitcoin history starts later, so the bitcoin samples are not the same length. A mark that differs can come from the missing 2013 and early 2014, not from the prices.
- Two venues agreeing does not make a result true. Both are spot prices for the same coins and move together.
- The terms of use for Kraken's published files are not stated on the page that offers them. UNKNOWN.
- The held-back years were already seen in replay 01.

## What research proposes from this

None of this is decided.

1. Change proposal 1 of `archive/decisions/0005-overnight-research-2026-11-25.md`. No bitcoin rule now has a clean pass. Stop describing P2, S50 and D20 as passed.
2. If practice trading of the slow bitcoin trend goes ahead, run it as observation, labelled "failed mark 4 on the shorter history", with P1 only. P1 was named as the main rule before any run, so using it involves no picking.
3. Do not lower `backtest_max_pbo` and do not drop mark 4. The mark did its job.
4. As a possible next test, written down before it is run: one blended rule that holds the average of the nine, so that nothing is picked. This would be a new trial and would be counted.
5. Use Kraken's published files as the rig's main crypto history from here on, and Bitstamp as the second source. Kraken publishes its files for download. Bitstamp's general terms are unclear about collecting its prices ([Bitstamp terms](https://www.bitstamp.net/terms-of-use/)).
6. Keep ether as observation only.

## How to reproduce

From `research_rig/`: `python3 fetch_kraken_archive.py`, `python3 build_kraken_daily.py`, `python3 run_01x2.py` (writes `results_01x2.json`), `python3 diag_x2_pbo.py` (writes `diag_x2_pbo.json`), then `python3 build_doc12b.py` (writes this file). Seed 7.
