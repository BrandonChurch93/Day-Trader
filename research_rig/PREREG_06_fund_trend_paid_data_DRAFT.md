# Pre-registration 06 (draft): slow trend rules on funds that can be bought

Status: DRAFT, written 2026-11-25. Not frozen and not in the trial ledger. It is frozen and logged on the day the price data is in hand, before any rule is run on it. Proposed by research. No owner decision is recorded here.

Blocked on: one month of daily fund prices with opening prices and dividend adjustment (a purchase, `docs/decisions/morning_list_2026-11-25.md`).

Written with this knowledge, stated so nobody has to guess: replay 05 (`docs/research/22_replay_05_stock_trend.md`) had already been run on index data when this draft was written. The rules below are published rules chosen from the reading in `docs/research/21_systematic_funds_and_published_rules.md`. None was tuned on replay 05.

## Why

Replay 05 used index returns with no opening prices and nothing that can be bought. This test repeats the slow rules on real funds, filled at the next day's open, across more than one kind of asset. The published case for trend rules is strongest across several kinds of asset at once, not on the stock market alone ([Faber paper](https://www.cambriainvestments.com/wp-content/uploads/2026/09/A-Quantitative-Approach-to-Tactical-Asset-Allocation.pdf)).

## Data needed

| Fund | Stands for | First full year |
|---|---|---|
| SPY | US large companies | 1994 |
| EFA | Developed markets outside the US | 2002 |
| IEF | US 7 to 10 year Treasury bonds | 2003 |
| VNQ | US property companies | 2005 |
| DBC | Commodities | 2007 |
| GLD | Gold | 2005 |
| QQQ, IWM | US technology and small companies | 2000, 2001 |
| BIL | Treasury bills (cash) | 2008 |

Daily open, high, low, close, volume, splits and dividends. Before BIL exists, cash earns the bill rate from the French library file used in replay 05. Raw files stay out of the repo.

## Fill and cost rules

- Signal from closes up to day t. Order filled at the open of day t+1. Sensitivity, reported: filled at the close of day t+1.
- Cost per side at both ends of `cost_model_bps_per_side_liquid_etf`, and at twice the upper end. A move between a fund and cash pays two sides.
- Dividends are added on the day they go ex. Fund fees are inside the fund prices already.
- Long or cash only. No leverage, no shorting. 252 days a year. Sharpe ratios use returns above the bill rate.
- Fractional weights are traded only when the target differs from the current weight by more than 0.10.

## Rules (6 trials)

| Id | Rule | Compared with |
|---|---|---|
| G1 | Faber's five-asset rule: SPY, EFA, IEF, VNQ, DBC, one fifth each. At each month end a fund is held if its dividend-adjusted price is above the average of its last 10 month-end values, else that fifth sits in cash | The five funds held in equal parts, rebalanced yearly |
| G2 | The same five funds, each on the four-average ensemble used for bitcoin (P1), checked daily | Same |
| G3 | Twelve-month momentum on SPY alone: hold SPY if its 12-month return beats bills, else IEF ([Antonacci 2013](https://www.naaim.org/wp-content/uploads/2013/10/00D_Absolute-Momentum_gary_antonacci.pdf)) | Holding SPY |
| G4 | Ten-month rule on SPY alone, filled at the open | Holding SPY |
| G5 | Three leaders: each month end hold the three of SPY, QQQ, IWM, EFA, IEF, VNQ, DBC, GLD with the highest 12-month return that are also above their ten-month average. Empty slots sit in cash | The eight funds held in equal parts, rebalanced yearly |
| G6 | 60% SPY and 40% IEF, rebalanced yearly. No timing at all. This is a yardstick and it is counted as a trial | Holding SPY |

## Slices

| Slice | Dates | Use |
|---|---|---|
| Development | first date all funds in the rule exist, to 2015-12-31 | look freely |
| Held back | 2016-01-01 to 2026-06-30 | each frozen rule run once |
| After the designer's knowledge cutoff | 2026-07-01 to the last day in the file | reported |

Known weakness, stated now: the five-fund rules cannot start before 2007, so the development slice is short and holds one large fall.

## Pass marks

The five marks used in the other replays, with the tie rule and shuffle method of `AMENDMENT_2026-11-25_audit_fixes.md`, numbers read from `config/thresholds.yaml`. Trials counted in the deflated Sharpe ratio: every trial in the ledger on the day this is frozen, plus these 6. This draft is not frozen until the owner has settled how mark 4 is to be measured (`docs/research/16_rig_audit.md`, and `docs/STATUS.md`, "Next in the queue"). The method he picks is named here before the plan is frozen.

Also reported: whether each rule beat a fixed mix of its comparison and cash with the same average share invested, as in replay 05.

A pass means "worth running in the practice account". It does not mean "makes money".

## Checks that must pass first

`fixtures2.py`; dividend handling checked by hand on one fund and one ex date; a held fund's growth matches the provider's total-return figure for a full year within 0.1 percentage points.
