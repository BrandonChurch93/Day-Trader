# Pre-registration 05: slow trend rules on the US stock market, on free data

Written 2026-11-25 07:47 UTC, before any rule in this file was run on this data. Not edited after the run except for dated notes at the bottom.

Status: research rig, not the product. Proposed by research. No owner decision is recorded here.

## Why

Stocks have not been tested at all, because exchange-traded fund prices need a purchase. One free source is good enough for a first, honest look at the slow rules: the Kenneth French data library, which publishes the daily total return of the whole US stock market and of industry groups from 1926 ([French data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)). The research reports written tonight say the same thing from the live record: published trend rules run as real funds have cut some of the drop and given up a lot of the return. This test asks whether that holds on a century of data, under our own marks.

Honest limits, stated before the run:

- These are index returns, not prices of something that can be bought. A fund that tracks the market stands in for them. Fund fees and tracking gaps are left out for both the rule and holding.
- There are no opening prices. Orders are assumed to fill at the next day's close (see fills).
- Taxes are not modeled. In a taxable account a rule that sells pays tax sooner than holding does. This counts against every rule here and is not in the numbers.
- The rules are textbook rules. The model that wrote this plan has read about this history up to June 2026. The held-back slice guards against tuning inside this run only.
- The library rebuilds its history at each update, so a later download can differ slightly.

## Data

| Series | File | Dates |
|---|---|---|
| US market total return, daily | Fama/French 3 factors daily, `Mkt-RF` plus `RF` | 1926-07-01 to 2026-09-30 |
| Cash return, daily | the same file, `RF` (one-month Treasury bill) | same |
| 12 industry groups, value weighted, daily | 12 Industry Portfolios daily | same |

Raw files are not stored in the repo. `research_rig/data_notes_french.md` records where they came from and how they are laid out.

## Fill and cost rules

- A signal is worked out from closes up to and including day t. The trade is made at the close of day t+1. This is one full day late, on purpose.
- Sensitivity, reported and not used for any mark: trade at the close of day t.
- Cost per side at three levels: 2, 5 and 10 bps. The middle one is the upper value of `cost_model_bps_per_side_liquid_etf`. A switch between stocks and cash pays two sides, because cash is held in a Treasury bill fund that also has to be bought or sold.
- Cash earns the bill rate. Sensitivity, reported: cash earns nothing.
- Long or cash only. No leverage, no shorting.
- Fractional weights are traded only when the target differs from the current weight by more than 0.10.
- 252 trading days a year. Sharpe ratios use returns above the bill rate.

## Rules, frozen (8 trials)

| Id | Rule |
|---|---|
| T1 | Ten-month rule. At each month end: hold the market if its total return index is above the average of its last 10 month-end values, else cash. Checked monthly |
| T2 | 200-day rule. Hold the market when the index is above its 200-day simple average, else cash. Checked daily |
| T3 | Twelve-month momentum. At each month end: hold the market if its return over the last 12 months is above the bill return over the same months, else cash |
| T4 | The ensemble used for crypto (P1): weight is the share of these that are true: index above its 20, 50, 100 and 200 day average |
| T5 | Trendpilot, first version of the published rule: five closes in a row above the 200-day average, hold the market. Five closes in a row below it after being in the market, hold half. While not fully in the market, if the 200-day average is below its value five days earlier, hold cash. Only five closes in a row above the average moves back into the market. The later "20% below the average" clause is left out |
| V1 | Size by volatility only, no trend: weight = min(1, 0.10 / volatility), where volatility is the yearly standard deviation of the last 21 daily returns |
| I1 | Twelve industry groups, one twelfth of the account each. Each group follows T1 on its own index. Compared with buying the twelve groups in equal parts at the start and holding them |
| I2 | Leaders with a market filter. At each month end, if T1 says hold the market, hold the three industry groups with the highest 12-month return, one third each, else cash. A third is switched only when its group leaves the top three. Compared with holding the market |

Test starts 1927-08-01, after the longest look-back.

## Slices

| Slice | Dates | Use |
|---|---|---|
| Development | 1927-08-01 to 2006-05-31 | look freely |
| Held back | 2006-06-01 to 2026-06-30 | each frozen rule is run on it once. It starts after the ten-month rule was published, and holds 2008, 2020 and 2022 |
| After the designer's knowledge cutoff | 2026-07-01 to 2026-09-30 | three months, reported, far too short to mean anything |

## Comparisons

- Holding the market (or the twelve groups for I1), bought once at the start, same costs.
- A fixed mix: a constant share in the market and the rest in cash, where the share is the rule's own average weight in the development slice, kept within the 0.10 band. This asks whether the rule does anything that simply holding less stock would not do.
- Shuffled timing, 1,000 times, seed 7. In or out rules: in spells shuffled among in slots, out spells among out slots. Other rules: the whole sequence of targets shifted by a random number of days and wrapped around.

## What is measured

Yearly growth, volatility, Sharpe ratio above bills, largest drop, average weight, share of days with a position, trade sides, turnover; for each slice and each cost level. Break-even cost against the comparison. Deflated Sharpe ratio. Overfitting estimate over the 8 trials with 16 equal blocks, ties counted as overfit, the other tie readings reported. Bootstrap range of the Sharpe difference. Results for 2008, 2020 and 2022 one by one.

## Pass marks, set before the run

The same five marks as the other replays, numbers read from `config/thresholds.yaml`, at each cost level:

1. Held-back slice: Sharpe ratio above the comparison, and largest drop at most `replay_max_drop_ratio_vs_hold` times the comparison's.
2. Whole sample: break-even cost at least `backtest_min_breakeven_cost_multiple` times the cost level.
3. Whole sample: deflated Sharpe ratio above `replay_min_deflated_sharpe`. Trials counted: 44 (36 before, 8 here). The spread of Sharpe ratios used in the formula is taken across these 8 trials.
4. Overfitting estimate under `backtest_max_pbo`.
5. Shuffled timing above `replay_min_shuffle_percentile`.

Also reported next to the marks, in plain words: whether the rule beat the fixed mix on the held-back slice on both Sharpe ratio and largest drop. A rule that passes the five marks and does not beat the fixed mix is reported as "passes the marks, but holding less stock did as well".

A pass means "worth running in the practice account". It does not mean "makes money".

## Checks that must pass first

`fixtures2.py`, plus for the return-based engine: holding equals the compounded market return less the entry cost; a fixed 0 weight equals compounded bills; a hand-worked two-day switch with costs; a rule that sees tomorrow's return beats the honest one; same input gives the same output.
