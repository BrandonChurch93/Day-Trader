# Pre-registration 03: rules that trade inside the day, on hourly bitcoin and ether bars

Written 2026-11-25 07:04 UTC, before any of these rules was run on any data. This file is not edited after the first run. Changes go in a new numbered file.

Status: research rig, not the product. Proposed by research. No owner decision is recorded here.

## Question

Replay 01 tested rules that hold for days or weeks. The project is about day trading. So: does any plain rule that gets in and out inside one day, on spot BTC and ETH, make money after the fees a US retail account really pays?

## What research expects, written before the run

This is an expectation, not a result. One buy and one sell at Alpaca costs about 60 bps with slippage. A typical half-day move in bitcoin is of that size or smaller. The one published study we hold on this found a break-even cost near 10 bps ([University of Reading manuscript](https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf)). Research expects most or all of these rules to fail at every venue except perhaps Binance.US. The run is done to measure it and not to assume it.

## Data

| Series | Source | Dates |
|---|---|---|
| BTC/USD hourly bars | Bitstamp public API | from 2013-01-01 |
| ETH/USD hourly bars | Bitstamp public API | from 2017-08-16 |
| Daily bars for the trend filter in H7 | Bitstamp, the same files as replay 01 | as replay 01 |

- Bars are UTC hours. A day is a UTC day, hours 0 to 23. This is a choice. Crypto has no market open.
- Last bar used: the 23:00 bar of 2026-11-24.
- Missing hours are filled with the last close and zero volume, and are counted and reported.
- Start date, fixed by a data-only check before any rule runs: the first January 1 from which every later calendar year has under 1% of hours with zero volume or missing, and at least 4,800 hours of earlier data exist for warm-up. For ETH, if no January 1 qualifies with warm-up, the start is 4,800 hours after the first bar, moved to the next UTC midnight.

## Slices

Same dates as replay 01.

| Slice | Dates | Use |
|---|---|---|
| Development | start to 2022-12-31 | look freely |
| Held back | 2023-01-01 to 2026-06-30 | each frozen rule is run on it once |
| After the designer's knowledge cutoff | 2026-07-01 to 2026-11-24 | reported separately |

Honest limits, stated before the run:

- The held-back slice is not fresh. Replay 01 already ran daily rules on it, and research saw those results. These hourly rules have not been run on it.
- The model that chose these rules has read about crypto markets up to mid 2026.
- Hourly bars from one venue. A fill at the hourly open with 5 bps slippage is an assumption, not a measurement.

## Fill and cost rules

- A signal uses bars up to and including bar t. The trade fills at the open of bar t+1.
- Cost per side: venue taker fee plus 5 bps. Same five venues and fees as replay 01: Binance.US 2, Alpaca 25, Kraken at its $10,000 tier 38, Kraken entry 80, Coinbase Advanced entry 90 bps. Source: `docs/research/09_brokers_and_venues.md`.
- Long or flat only. Fully in or fully out. Cash earns nothing.
- "Exit at day end" means the sell fills at the open of the next day's hour 0 bar.

## Rules, frozen (8 per asset, 2 assets: 16 trials, numbers 27 to 42)

"Day open" is the open of the hour 0 bar.

| Id | Rule |
|---|---|
| H1 | Half-day momentum, the primary rule. After the hour 11 bar closes, if its close is above the day open, buy. Exit at day end |
| H2 | Opening range breakout. The range is the highest high of the hour 0 to 3 bars. Buy after the first hourly close above it (hour 4 to 22 bars). Exit at day end |
| H3 | Last hour timing, an hourly version of the Reading paper's idea. If the hour 0 bar closed above the prior day's last close, and the hour 22 bar closed above the hour 21 close, hold during the hour 23 bar only |
| H4 | Buy the dip. If an hourly return is below minus 2 times the standard deviation of the previous 168 hourly returns, buy and hold for 4 bars. A new trigger while holding restarts the 4 bars |
| H5 | H4, but only when the close is above its 4,800 hour (200 day) simple average |
| H6 | Hourly trend with no day-end exit. In when close is above its 24 hour average and the 24 hour average is above the 168 hour average. Included to compare a faster trend rule with replay 01. It is not strictly day trading |
| H7 | H1, but only on days when the daily trend weight P1 from replay 01, as of the prior day's close, is 0.5 or more |
| H8 | Noise band, after the SPY rule of Zarattini, Aziz and Barbon. For each hour, the band is the average size of the move from day open to that hour's close over the prior 14 days. Buy after the first hourly close (hours 1 to 22) above day open times (1 + band). Sell if an hourly close falls below the day open, or at day end. One entry a day |

## Controls (not trials, no pass marks)

- Hold the coin.
- C1: always hold from 12:00 to 24:00 UTC, with no signal. Shows what H1's signal adds.
- Shuffled timing: the rule's own in and out spells in random order, 1,000 times, seed 7.

## What is measured

All performance figures use returns from one UTC day's end to the next, so they compare with replay 01. Net yearly growth, Sharpe (365 days, zero cash rate), largest drop, share of time invested, round trips per year, average net result per round trip in bps, share of round trips that made money. Break-even cost per side against zero growth and against hold. Deflated Sharpe counting every trial in the ledger on these two coins so far: 20 from replay 01 plus these 16, so 36. The spread of Sharpe across trials is taken over all 36, with the earlier 20 rerun at the same venue cost. Overfitting probability across the 8 rules per asset (16 blocks). 90% range of the Sharpe difference against hold (block 30 days, 2,000 draws, seed 7).

## Pass marks, unchanged from replay 01

A rule passes for a venue only if all five hold. Values are the keys in `config/thresholds.yaml`.

1. Held-back slice, net: Sharpe above hold, and largest drop no more than `replay_max_drop_ratio_vs_hold` times the drop from holding.
2. Whole sample: break-even cost against hold is at least `backtest_min_breakeven_cost_multiple` times the venue's modeled cost per side.
3. Whole sample: deflated Sharpe above `replay_min_deflated_sharpe`, 36 trials counted.
4. Overfitting probability under `backtest_max_pbo`.
5. The rule's Sharpe is above `replay_min_shuffle_percentile` of its shuffles.

Also reported for every rule and venue, as a plain yes or no: did it make money at all, net, on the whole sample and on the held-back slice. A rule that makes a little money but fails mark 1 is still a fail. A pass means "worth running in the practice account" and nothing more.

## Engine checks that must pass first

The fast hourly simulator must give the same result as the engine used in replay 01 on random in and out signals (to 1e-9). The existing engine checks must still pass.
