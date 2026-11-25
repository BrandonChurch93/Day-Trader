# Pre-registration 04: slow trend on a wider basket of coins, dead coins kept

Written 2026-11-25 07:51 UTC, before any rule in this file was run on this data. Not edited after the run except for dated notes at the bottom.

Status: research rig, not the product. Proposed by research. No owner decision is recorded here.

## Why

Replay 01 tested slow trend rules on bitcoin and ether only. The owner is open to higher-risk coins if there is a reason behind them. The reason worth testing is this: trend rules are said to work better across many coins than on one, and the smaller coins move more. The usual trap is to test only the coins that are still alive today. Kraken's published history holds every pair it ever listed against the dollar, including the ones that were later removed, so the trap can be avoided.

Honest limits, stated before the run:

- One venue's listings. A coin enters the data when Kraken listed it, which is often after its largest rise.
- The spread and slippage for small coins is assumed here, not measured. Real order books are being sampled tonight and will be compared in a separate document.
- The rules are textbook rules, and the model that wrote this has read about this market up to June 2026. The held-back slice guards against tuning inside this run only. It has already been used by replays 01 and 03.
- Terms for using Kraken's files are not stated on its page. UNKNOWN.

## Data

Every file in Kraken's published archive whose pair ends in USD, daily bars, first trade to 2026-09-30 (760 files; 129 of them end before 2026-09-25). Raw files are not stored in the repo.

## Which coins are held, decided by data only

On the first day of each month, using only data up to the day before:

- Left out: pairs quoted in another coin (file names ending PYUSD or RLUSD).
- Left out: pairs with fewer than 200 days of history, or with no trades on more than 10 of the last 90 days.
- Left out: pegged or near-pegged pairs. The test is the standard deviation of the last 90 daily returns, times the square root of 365, under 0.20. This removes dollar coins, currency pairs and gold tokens.
- Left out: copies. A pair whose last 90 daily returns have a correlation above 0.98 with a pair that has more dollar volume is dropped (wrapped and staked versions of the same coin).
- Of what remains, the 10 (or 20) pairs with the highest median daily dollar volume over the last 90 days are the basket for that month.

The test starts on the first month start when at least 10 pairs qualify. That date is worked out from the data before any rule is run and is written into the output.

## Fill and cost rules

- Signal from closes up to day t. Fill at the open of day t+1, only if the pair traded that day. Otherwise the order waits.
- Cost per side: the venue fee plus slippage. Slippage is 5 bps for bitcoin and ether, and 25 bps for every other coin. Sensitivity, reported: 50 bps for every other coin.
- Venue fees as in replay 01 (2, 25, 38, 80, 90 bps per side). Only the Kraken levels match a place where the whole basket can be bought. The others are shown for comparison.
- Shared cash, earns nothing. Long or cash only. No leverage.
- A coin is traded when its weight is off target by more than one eighth of a slot.
- A coin that leaves the basket at a month start is sold. A coin whose history ends is sold at its last close. Sensitivity, reported: the same with half of that last value lost.

## Rules, frozen (5 trials)

P1 is the trend weight from replay 01: the share of these that are true: close above its 20, 50, 100 and 200 day average.

| Id | Rule |
|---|---|
| K1 | Top 10 by volume. Each coin has one tenth of the account as its slot and holds P1 times its slot. The primary rule |
| K2 | Top 10 by volume. Only the 5 with the highest return over the last 90 days are held, chosen at each month start. Each has one fifth as its slot and holds P1 times its slot |
| K3 | Top 20 by volume. One twentieth each, times P1 |
| K4 | Bitcoin and ether only, half each, times P1 |
| K5 | A published rule with a live fund behind it, on bitcoin alone: four pairs of exponentially weighted averages of the daily close (half-lives 1 and 5, 2.5 and 10, 5 and 20, 10 and 40 days, each over the last 180 closes). Weight is the share of pairs where the short average is at or above the long one. Changed once a week, on Wednesday's close. Source: [CoinDesk trend indicator methodology](https://downloads.coindesk.com/cd3/CDI/Trend-Indicator-Methodology.pdf), as read by tonight's research. Daily closes at 00:00 UTC stand in for the 4 p.m. New York price |

## Slices

Development: start to 2022-12-31. Held back: 2023-01-01 to 2026-06-30. After the designer's knowledge cutoff: 2026-07-01 to 2026-09-30.

## Comparisons

- Holding bitcoin, bought once at the start. This is what the marks compare against, because it is the simple thing the owner could do instead.
- Holding the basket: the same monthly top 10, equal parts, always fully invested, put back to equal parts each month, same costs. Reported next to every result.
- Shuffled timing, 1,000 times, seed 7: each coin's own sequence of trend weights is shifted by a random number of days and wrapped around inside that coin's own history. The basket membership is left as it was.

## What is measured

As in the audit amendment of 2026-11-25: growth, volatility, Sharpe ratio, largest drop, average weight, share of days with a position, trade sides, turnover, per slice and venue; break-even cost; deflated Sharpe ratio; overfitting estimate over the 5 trials (16 equal blocks, ties counted as overfit, other readings reported); bootstrap range. Also: how many coins were held on average, how many positions were closed because a coin's history ended, and the result by calendar year.

## Pass marks, set before the run

The same five marks, numbers read from `config/thresholds.yaml`, at each venue. Trials counted: 49 (44 before, 5 here). The spread of Sharpe ratios in the deflated Sharpe formula is taken across these 5 trials.

A pass means "worth running in the practice account". It does not mean "makes money".

## Checks that must pass first

`fixtures2.py` and `fixtures_basket.py` (hand-worked two-coin case, costs, a coin that stops trading, shared cash never below zero, same input gives the same output).
