# Pre-registration 01, cross-check X2: the same rules on Kraken's own full history

Written 2026-11-25 07:10 UTC, before the replay 01 rules were run on this data. Not edited after the run.

Status: research rig, not the product. Proposed by research. No owner decision is recorded here.

## Why

Replay 01 used one venue's prices (Bitstamp). Cross-check X1 covered only the last 720 days. Two things make a full second source worth having:

- A result that only shows up on one venue's prices is not a result.
- The fresh check found that Bitstamp's general terms are unclear about collecting its prices for personal research. Kraken publishes its full price history as files for download ([Kraken support page](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data)). The terms for using those files are not stated on that page. UNKNOWN.

## Data

| Series | Source | Dates |
|---|---|---|
| XBT/USD and ETH/USD daily bars | Kraken's published OHLCVT archive, complete file | first trade to 2026-09-30 |
| The same pairs, 2026-10-01 to 2026-11-24 | Kraken's public daily bars, the file already used in X1 | to 2026-11-24 |

- Kraken's files leave out days with no trades. Those days are filled with the last close and zero volume, and counted.
- Only the four files needed (daily and hourly, two pairs) are read out of the archive. Raw data is not stored in the repo.

## What is run

Nothing new. The same 9 rules, the same fill and cost rules, the same five venues' costs, the same slices, the same five pass marks and the same seed as `PREREG_01_daily_crypto_trend.md`. No new trial is added to the count of 20.

| Run | Coin | Test starts | Note |
|---|---|---|---|
| X2-BTC | Bitcoin | 2014-05-01 | Kraken's first bar is 2013-10-06, then 200 days of warm-up, moved to the next month start. Later than Bitstamp's 2013-01-01, so 2013 and early 2014 are missing |
| X2-ETH | Ether | 2018-03-05 | Same start as replay 01, for a like-for-like comparison |
| S2-ETH | Ether | 2016-03-01 | Kraken's first bar is 2015-08-07, then 200 days of warm-up. This adds two earlier years that Bitstamp does not have. Reported in full with the same marks, and labelled as a longer sample, not as a second chance |

## How it is read

- Agreement of daily closes between the two venues is reported (median and largest gap).
- For each venue cost and rule: does the pass or fail from replay 01 hold on Kraken's prices. Every change of verdict is listed, in both directions.
- If a rule passes on one venue's prices and fails on the other, it is treated as failed until explained.
