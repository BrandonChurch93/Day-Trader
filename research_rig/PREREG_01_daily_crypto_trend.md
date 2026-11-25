# Pre-registration 01: daily trend rules on spot bitcoin and ether

Written 2026-11-25 06:35 UTC, before any strategy was run on the data. This file is not edited after the first run. Changes go in a new numbered file.

Status: research rig, not the product. Proposed by research. No owner decision is recorded here.

## Question

Does a plain long-or-cash trend rule on spot BTC and ETH, on daily bars, beat holding the coin after the fees a US retail account actually pays?

## Data

| Series | Source | Dates used |
|---|---|---|
| BTC/USD daily bars | Bitstamp public API | 2013-01-01 to 2026-11-24 |
| ETH/USD daily bars | Coinbase Exchange public API | 2016-06-01 to 2026-11-24 |
| BTC/USD daily bars, second source for a cross-check | Coinbase Exchange public API | 2015-07-20 to 2026-11-24 |

Bars are UTC days. The unfinished bar for 2026-11-25 is dropped. Indicators may use bars from before the first test date as warm-up.

## Slices

| Slice | Dates | Use |
|---|---|---|
| Development | first date to 2022-12-31 | look freely |
| Held back | 2023-01-01 to 2026-06-30 | each frozen rule is run on it once |
| After the designer's knowledge cutoff | 2026-07-01 to 2026-11-24 | reported separately. It is short |

Honest limit, stated before the run: the rules below are textbook rules, and the model that chose them has read the price history of BTC and ETH up to June 2026. The held-back slice therefore guards against tuning inside this run. It does not guard against the rules being popular because they worked in the past.

## Fill and cost rules

- A signal is worked out from closes up to and including day t. The trade fills at the open of day t+1.
- Cost per side, taken from the traded dollar amount: the venue's taker fee plus `slip` of 5 bps for spread and impact. Venue taker fees per side in bps: Binance.US 2, Alpaca 25, Kraken at its $10,000 tier 38, Kraken entry 80, Coinbase Advanced entry 90. Source: `docs/research/09_brokers_and_venues.md`.
- Cash earns nothing. This is against the strategy, which sits in cash part of the time.
- Long or flat only. No leverage, no shorting.
- Fractional exposure is traded only when the target differs from the current weight by more than 0.10.

## Rules, frozen (9 per asset, 2 assets, plus 2 portfolios: 20 trials)

| Id | Rule |
|---|---|
| P1 | Trend ensemble, the primary rule. Weight = the share of these four that are true: close above its 20, 50, 100 and 200 day simple average |
| P2 | P1 times min(1, 0.40 / realised volatility), where realised volatility is the annualised standard deviation of the last 30 daily returns (365 days a year) |
| S50, S100, S200 | Fully in when close is above its 50, 100 or 200 day simple average, otherwise in cash |
| D20, D55 | Enter when close is the highest close of the last 20 (55) days. Exit when close is the lowest close of the last 10 (20) days |
| M30, M90 | Fully in when the close is above the close 30 (90) days ago, otherwise in cash |
| PORT-P1, PORT-P2 | Half the account runs the rule on BTC and half on ETH, from 2016-06-01, rebalanced only by the rules' own trades |

## Comparisons

- Buy and hold of the same coin over the same dates, paying one side of cost at the start.
- Shuffled timing: the rule's own in and out spells, put in random order 1,000 times with seed 7. This keeps the same time in the market and about the same number of trades. It asks whether the timing is doing anything.

## What is measured

Net yearly growth rate, yearly volatility, Sharpe ratio (daily returns, 365 days, zero cash rate), largest drop from a peak, share of time invested, number of trades, turnover per year. Break-even cost: the cost per side at which the rule's Sharpe ratio falls to that of buy and hold, and the cost per side at which its growth rate falls to zero. Deflated Sharpe ratio with 20 trials. Probability of backtest overfitting across the 9 rules per asset (16 blocks). A 90% range for the Sharpe difference against buy and hold from a block bootstrap (block 30 days, 2,000 draws, seed 7).

## Pass marks, set before the run

A rule passes this replay for a venue only if all of these hold. Thresholds are named by their keys in `config/thresholds.yaml`.

1. Held-back slice, net of that venue's cost: Sharpe ratio above buy and hold, and largest drop no more than 0.6 times the buy and hold drop.
2. Whole sample: break-even cost against buy and hold is at least `backtest_min_breakeven_cost_multiple` times that venue's modeled cost per side.
3. Whole sample: Deflated Sharpe ratio above 0.95 with all 20 trials counted.
4. Probability of backtest overfitting under `backtest_max_pbo`.
5. Shuffled timing: the rule's Sharpe ratio is above 95% of the shuffles.

A pass means "worth running in the practice account". It does not mean "makes money". A fail is reported as a fail. The 0.6 in mark 1 and the 0.95 in marks 3 and 5 are new house numbers proposed here. If the owner keeps them they move into `config/thresholds.yaml`.

## Engine checks that must pass first

Hand-worked profit. Hand-worked costs. Buy and hold equals the coin's return less one side of cost. A rule that peeks at the next close must give a different, better result than the same rule run honestly (proves the one-bar delay is real). Random entries lose about their costs. Two runs give identical output.

## Amendment 1, 2026-11-25 06:37 UTC, before any rule was run

Two data changes, made after the data researcher's report arrived and before the first run:

- ETH uses Bitstamp, not Coinbase. Coinbase's market data terms limit what may be done with its data, and its daily candle endpoint returned a wrong bar for 2026-11-13. Bitstamp ETH/USD starts 2017-08-16, so with 200 days of warm-up the ETH test and both portfolios start 2018-03-05, not 2016-06-01.
- The second source for the cross-check is Kraken's public daily bars, which reach back 720 days, not Coinbase.

Nothing else changes: same rules, same slices, same costs, same pass marks, 20 trials.
