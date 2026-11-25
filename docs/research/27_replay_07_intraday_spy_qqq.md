# Replay 07: day trading rules on SPY and QQQ one-minute bars

Written by `research_rig/build_doc27.py` from `research_rig/results_07.json`. Do not edit by hand. Every figure here is MEASURED by `research_rig/run_07.py` (run 2026-11-25 15:35 UTC, command `python3 run_07.py --full`, code at commit 9d49997, with changes not yet committed: `run_07.py` was new and uncommitted when it ran, so the code that ran is the first committed version of `run_07.py`) unless it is labelled otherwise.

Plan: `research_rig/PREREG_07_intraday_spy_qqq.md`, frozen and pushed before the run. Ledger rows 56 to 71 in `research_rig/TRIAL_LEDGER.md`. The held-back years were run once.

Price source: one-minute and daily bars from the workspace's own price lookup, collected 2026-11-25; dividend and split adjustment UNKNOWN; calendar from memory. Known gaps are in `docs/research/10_historical_data_and_practice.md`; the days this test did not use are counted below. There is no second price source, so there is no cross-check.

Costs per side: 0.5 bps (`replay_07_costs.low_bps_per_side`), 2 bps (`cost_model_bps_per_side_liquid_etf`, lower end), 5 bps (`cost_model_bps_per_side_liquid_etf`, upper end). Pass marks are judged at 2 bps and 5 bps only. Commission 0. Cash earns nothing. Long only, no leverage.

## Result

- SPY: 0 of 8 rules pass all five marks at both judged costs.
- SPY at 2 bps: passes none.
- SPY at 5 bps: passes none.
- QQQ: 0 of 8 rules pass all five marks at both judged costs.
- QQQ at 2 bps: passes none.
- QQQ at 5 bps: passes none.
- A pass means "worth running on the practice desk". It does not mean "makes money".

## Days used

| Fund | Used days | First result day | Last day | Early closes used | Days not used | Why not used |
|---|---|---|---|---|---|---|
| SPY | 5617 | 2003-10-21 | 2026-11-24 | 47 | 209 | last one-minute close away from daily close: 120; no one-minute data: 2; not every regular minute exactly once: 26; one-minute high above daily high: 22; one-minute low below daily low: 35; timestamp not on a whole minute: 4 |
| QQQ | 3893 | 2011-04-12 | 2026-11-24 | 33 | 36 | last one-minute close away from daily close: 3; not every regular minute exactly once: 29; one-minute high above daily high: 1; one-minute low below daily low: 2; timestamp not on a whole minute: 1 |

The first `replay_07_data` warm-up days of each fund are left out of every result. Check on the prices: N5 and N6 together match holding before costs to within a log gap of 2.3e-16 (SPY), 2.3e-16 (QQQ).

## Pass marks, held-back slice for mark 1

Mark 1 compares the rule with holding the same fund on the held-back slice (`replay_max_drop_ratio_vs_hold`). Mark 2 is the break-even cost against holding (`backtest_min_breakeven_cost_multiple`). Mark 3 is the deflated Sharpe ratio (`replay_min_deflated_sharpe`), count 116. Mark 4 is the largest overfitting estimate over the fixed start dates (`backtest_max_pbo`). Mark 5 is shuffled timing (`replay_min_shuffle_percentile`). N5 and N6 cannot pass mark 5 by construction, as the plan says.

### SPY at 2 bps per side

| Rule | Growth a year | Sharpe | Largest drop | Drop vs holding | Deflated Sharpe | Shuffle share beaten | 1 | 2 | 3 | 4 | 5 | All five |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Holding SPY | +16.0% | 0.89 | -34.2% | | | | | | | | | |
| N1 | -3.3% | -0.64 | -26.4% | 0.77 | 0.000 | 0.662 | fail | fail | fail | pass | fail | fail |
| N2 | -0.6% | -0.14 | -15.2% | 0.45 | 0.000 | 1.000 | fail | fail | fail | pass | pass | fail |
| N3 | -6.5% | -2.25 | -40.0% | 1.17 | 0.000 | 0.404 | fail | fail | fail | pass | fail | fail |
| N4 | -52.2% | -6.82 | -99.6% | 2.91 | 0.000 | 1.000 | fail | fail | fail | pass | pass | fail |
| N5 | +1.3% | 0.16 | -28.0% | 0.82 | 0.000 | 0.000 | fail | fail | fail | pass | fail | fail |
| N6 | -6.4% | -0.42 | -48.3% | 1.41 | 0.000 | 0.387 | fail | fail | fail | pass | fail | fail |
| N7 | -3.0% | -0.27 | -32.1% | 0.94 | 0.000 | 0.687 | fail | fail | fail | pass | fail | fail |
| N8 | -5.5% | -1.87 | -34.5% | 1.01 | 0.000 | 0.950 | fail | fail | fail | pass | fail | fail |

Mark 4, overfitting estimate by start date: 2004-01-01: 0.098, 2007-01-01: 0.151, 2010-01-01: 0.012, 2013-01-01: 0.043. Largest 0.151. Mark 3 spread per day, all counted trials: 0.2037; this plan's 16 alone: 0.1351.

### SPY at 5 bps per side

| Rule | Growth a year | Sharpe | Largest drop | Drop vs holding | Deflated Sharpe | Shuffle share beaten | 1 | 2 | 3 | 4 | 5 | All five |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Holding SPY | +16.0% | 0.89 | -34.2% | | | | | | | | | |
| N1 | -10.4% | -2.10 | -57.0% | 1.66 | 0.000 | 0.619 | fail | fail | fail | pass | fail | fail |
| N2 | -7.4% | -1.84 | -44.2% | 1.29 | 0.000 | 0.999 | fail | fail | fail | pass | pass | fail |
| N3 | -14.1% | -4.92 | -67.4% | 1.97 | 0.000 | 0.042 | fail | fail | fail | pass | fail | fail |
| N4 | -86.1% | -13.86 | -100.0% | 2.92 | 0.000 | 1.000 | fail | fail | fail | pass | pass | fail |
| N5 | -13.0% | -1.06 | -66.5% | 1.94 | 0.000 | 0.000 | fail | fail | fail | pass | fail | fail |
| N6 | -19.5% | -1.54 | -81.8% | 2.39 | 0.000 | 0.032 | fail | fail | fail | pass | fail | fail |
| N7 | -10.4% | -1.10 | -58.9% | 1.72 | 0.000 | 0.619 | fail | fail | fail | pass | fail | fail |
| N8 | -13.1% | -4.50 | -64.5% | 1.89 | 0.000 | 0.309 | fail | fail | fail | pass | fail | fail |

Mark 4, overfitting estimate by start date: 2004-01-01: 0.011, 2007-01-01: 0.042, 2010-01-01: 0.003, 2013-01-01: 0.006. Largest 0.042. Mark 3 spread per day, all counted trials: 0.2138; this plan's 16 alone: 0.2530.

### QQQ at 2 bps per side

| Rule | Growth a year | Sharpe | Largest drop | Drop vs holding | Deflated Sharpe | Shuffle share beaten | 1 | 2 | 3 | 4 | 5 | All five |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Holding QQQ | +23.4% | 1.03 | -35.6% | | | | | | | | | |
| N1 | -1.6% | -0.16 | -19.7% | 0.55 | 0.000 | 0.913 | fail | fail | fail | pass | fail | fail |
| N2 | +3.4% | 0.62 | -7.5% | 0.21 | 0.000 | 1.000 | fail | fail | fail | pass | pass | fail |
| N3 | -6.3% | -1.78 | -40.9% | 1.15 | 0.000 | 0.249 | fail | fail | fail | pass | fail | fail |
| N4 | -43.5% | -4.14 | -98.6% | 2.77 | 0.000 | 1.000 | fail | fail | fail | pass | pass | fail |
| N5 | +4.2% | 0.36 | -28.9% | 0.81 | 0.000 | 0.000 | fail | fail | fail | pass | fail | fail |
| N6 | -3.2% | -0.09 | -44.2% | 1.24 | 0.000 | 0.447 | fail | fail | fail | pass | fail | fail |
| N7 | +2.9% | 0.29 | -16.7% | 0.47 | 0.000 | 0.753 | fail | fail | fail | pass | fail | fail |
| N8 | -4.9% | -1.43 | -32.1% | 0.90 | 0.000 | 0.723 | fail | fail | fail | pass | fail | fail |

Mark 4, overfitting estimate by start date: 2011-06-01: 0.022, 2012-06-01: 0.027, 2013-06-01: 0.033, 2014-06-01: 0.058. Largest 0.058. Mark 3 spread per day, all counted trials: 0.2037; this plan's 16 alone: 0.1351.

### QQQ at 5 bps per side

| Rule | Growth a year | Sharpe | Largest drop | Drop vs holding | Deflated Sharpe | Shuffle share beaten | 1 | 2 | 3 | 4 | 5 | All five |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Holding QQQ | +23.4% | 1.03 | -35.6% | | | | | | | | | |
| N1 | -8.8% | -1.09 | -51.3% | 1.44 | 0.000 | 0.884 | fail | fail | fail | pass | fail | fail |
| N2 | -3.3% | -0.56 | -25.5% | 0.72 | 0.000 | 1.000 | fail | fail | fail | pass | pass | fail |
| N3 | -13.8% | -4.04 | -67.3% | 1.89 | 0.000 | 0.049 | fail | fail | fail | pass | fail | fail |
| N4 | -82.2% | -10.17 | -100.0% | 2.81 | 0.000 | 1.000 | fail | fail | fail | pass | pass | fail |
| N5 | -10.4% | -0.71 | -58.8% | 1.65 | 0.000 | 0.000 | fail | fail | fail | pass | fail | fail |
| N6 | -16.8% | -0.92 | -78.9% | 2.22 | 0.000 | 0.001 | fail | fail | fail | pass | fail | fail |
| N7 | -4.4% | -0.28 | -40.3% | 1.13 | 0.000 | 0.778 | fail | fail | fail | pass | fail | fail |
| N8 | -12.5% | -3.79 | -63.3% | 1.78 | 0.000 | 0.129 | fail | fail | fail | pass | fail | fail |

Mark 4, overfitting estimate by start date: 2011-06-01: 0.090, 2012-06-01: 0.133, 2013-06-01: 0.173, 2014-06-01: 0.138. Largest 0.173. Mark 3 spread per day, all counted trials: 0.2138; this plan's 16 alone: 0.2530.

## Break-even cost

Round trip in bps (two sides), whole sample. Against holding: the first cost where the rule's Sharpe ratio stops being above holding's, holding paying the same cost. Against zero: the first cost where the average daily return stops being above zero. Set beside `intraday_trend_max_round_trip_bps` = 1 bps.

| Fund | Rule | Against holding | Against zero |
|---|---|---|---|
| SPY | N1 | never ahead, even at 0 | 0.77 |
| SPY | N2 | 1.64 | 3.61 |
| SPY | N3 | never ahead, even at 0 | 0.02 |
| SPY | N4 | 0.01 | 0.25 |
| SPY | N5 | never ahead, even at 0 | 2.39 |
| SPY | N6 | never ahead, even at 0 | 1.63 |
| SPY | N7 | never ahead, even at 0 | 2.26 |
| SPY | N8 | never ahead, even at 0 | 0.73 |
| QQQ | N1 | never ahead, even at 0 | 2.38 |
| QQQ | N2 | 1.80 | 5.68 |
| QQQ | N3 | never ahead, even at 0 | never ahead, even at 0 |
| QQQ | N4 | 0.19 | 0.66 |
| QQQ | N5 | 0.38 | 4.81 |
| QQQ | N6 | never ahead, even at 0 | 2.27 |
| QQQ | N7 | never ahead, even at 0 | 3.35 |
| QQQ | N8 | never ahead, even at 0 | 0.50 |

## Growth a year by slice

### At 0.5 bps per side

| Fund | Rule | development: growth, Sharpe | held back: growth, Sharpe | after the cutoff: growth, Sharpe | whole: growth, Sharpe |
|---|---|---|---|---|---|
| SPY | Holding | +6.2%, 0.44 | +16.0%, 0.89 | -8.8%, -0.47 | +9.0%, 0.58 |
| SPY | N1 | -0.8%, -0.15 | +0.4%, 0.10 | +0.1%, 0.05 | -0.4%, -0.06 |
| SPY | N2 | +3.4%, 0.83 | +2.9%, 0.75 | -3.5%, -1.12 | +3.1%, 0.77 |
| SPY | N3 | -0.6%, -0.17 | -2.5%, -0.84 | -8.4%, -4.69 | -1.4%, -0.45 |
| SPY | N4 | -16.8%, -1.94 | -11.4%, -1.24 | -29.3%, -5.42 | -15.3%, -1.75 |
| SPY | N5 | -0.5%, 0.00 | +9.2%, 0.78 | +19.3%, 1.71 | +2.9%, 0.32 |
| SPY | N6 | +1.5%, 0.18 | +1.0%, 0.14 | -27.3%, -2.61 | +0.7%, 0.12 |
| SPY | N7 | +1.6%, 0.23 | +1.0%, 0.15 | -9.0%, -0.88 | +1.2%, 0.18 |
| SPY | N8 | +0.4%, 0.15 | -1.5%, -0.49 | -8.8%, -5.95 | -0.4%, -0.13 |
| QQQ | Holding | +14.0%, 0.85 | +23.4%, 1.03 | -29.5%, -1.17 | +17.0%, 0.87 |
| QQQ | N1 | +0.5%, 0.11 | +2.2%, 0.31 | +9.0%, 1.25 | +1.5%, 0.26 |
| QQQ | N2 | +4.1%, 0.94 | +7.0%, 1.21 | -1.2%, -0.21 | +5.3%, 1.05 |
| QQQ | N3 | -0.8%, -0.28 | -2.2%, -0.61 | -5.4%, -2.14 | -1.6%, -0.49 |
| QQQ | N4 | -12.3%, -1.32 | +0.5%, 0.10 | -36.1%, -4.35 | -7.1%, -0.62 |
| QQQ | N5 | +6.2%, 0.60 | +12.4%, 0.90 | +7.1%, 0.46 | +9.2%, 0.75 |
| QQQ | N6 | +2.1%, 0.22 | +4.4%, 0.33 | -37.4%, -2.62 | +1.9%, 0.20 |
| QQQ | N7 | -1.3%, -0.07 | +6.9%, 0.57 | -10.1%, -0.81 | +2.3%, 0.25 |
| QQQ | N8 | -0.4%, -0.12 | -0.8%, -0.21 | -6.2%, -3.24 | -0.7%, -0.22 |

### At 2 bps per side

| Fund | Rule | development: growth, Sharpe | held back: growth, Sharpe | after the cutoff: growth, Sharpe | whole: growth, Sharpe |
|---|---|---|---|---|---|
| SPY | Holding | +6.2%, 0.44 | +16.0%, 0.89 | -8.8%, -0.47 | +9.0%, 0.58 |
| SPY | N1 | -4.5%, -0.94 | -3.3%, -0.64 | -3.6%, -0.93 | -4.1%, -0.83 |
| SPY | N2 | -0.3%, -0.06 | -0.6%, -0.14 | -6.6%, -2.09 | -0.6%, -0.12 |
| SPY | N3 | -4.4%, -1.48 | -6.5%, -2.25 | -12.3%, -6.74 | -5.2%, -1.80 |
| SPY | N4 | -57.4%, -7.88 | -52.2%, -6.82 | -61.3%, -11.53 | -55.8%, -7.57 |
| SPY | N5 | -7.8%, -0.73 | +1.3%, 0.16 | +10.6%, 1.00 | -4.6%, -0.36 |
| SPY | N6 | -5.9%, -0.39 | -6.4%, -0.42 | -32.6%, -3.24 | -6.6%, -0.45 |
| SPY | N7 | -2.1%, -0.20 | -3.0%, -0.27 | -12.9%, -1.32 | -2.6%, -0.24 |
| SPY | N8 | -3.6%, -1.24 | -5.5%, -1.87 | -12.1%, -7.73 | -4.4%, -1.52 |
| QQQ | Holding | +14.0%, 0.85 | +23.4%, 1.03 | -29.5%, -1.17 | +17.0%, 0.87 |
| QQQ | N1 | -3.3%, -0.63 | -1.6%, -0.16 | +5.1%, 0.74 | -2.2%, -0.30 |
| QQQ | N2 | +0.5%, 0.14 | +3.4%, 0.62 | -3.9%, -0.72 | +1.8%, 0.37 |
| QQQ | N3 | -4.8%, -1.66 | -6.3%, -1.78 | -9.3%, -3.66 | -5.6%, -1.76 |
| QQQ | N4 | -52.8%, -6.66 | -43.5%, -4.14 | -63.9%, -8.49 | -48.9%, -5.34 |
| QQQ | N5 | -1.5%, -0.08 | +4.2%, 0.36 | -0.7%, 0.05 | +1.2%, 0.16 |
| QQQ | N6 | -5.3%, -0.31 | -3.2%, -0.09 | -42.0%, -3.06 | -5.5%, -0.27 |
| QQQ | N7 | -5.0%, -0.42 | +2.9%, 0.29 | -13.9%, -1.17 | -1.5%, -0.07 |
| QQQ | N8 | -4.4%, -1.60 | -4.9%, -1.43 | -9.4%, -4.82 | -4.8%, -1.55 |

### At 5 bps per side

| Fund | Rule | development: growth, Sharpe | held back: growth, Sharpe | after the cutoff: growth, Sharpe | whole: growth, Sharpe |
|---|---|---|---|---|---|
| SPY | Holding | +6.2%, 0.44 | +16.0%, 0.89 | -8.8%, -0.47 | +9.0%, 0.58 |
| SPY | N1 | -11.5%, -2.48 | -10.4%, -2.10 | -10.7%, -2.83 | -11.1%, -2.35 |
| SPY | N2 | -7.4%, -1.76 | -7.4%, -1.84 | -12.4%, -3.81 | -7.5%, -1.81 |
| SPY | N3 | -11.6%, -3.99 | -14.1%, -4.92 | -19.6%, -10.06 | -12.6%, -4.37 |
| SPY | N4 | -88.8%, -15.15 | -86.1%, -13.86 | -88.4%, -17.30 | -88.0%, -14.74 |
| SPY | N5 | -20.7%, -2.18 | -13.0%, -1.06 | -4.9%, -0.42 | -18.0%, -1.73 |
| SPY | N6 | -19.1%, -1.54 | -19.5%, -1.54 | -42.1%, -4.50 | -19.7%, -1.59 |
| SPY | N7 | -9.2%, -1.05 | -10.4%, -1.10 | -20.3%, -2.18 | -9.8%, -1.09 |
| SPY | N8 | -11.1%, -3.93 | -13.1%, -4.50 | -18.2%, -10.27 | -11.9%, -4.20 |
| QQQ | Holding | +14.0%, 0.85 | +23.4%, 1.03 | -29.5%, -1.17 | +17.0%, 0.87 |
| QQQ | N1 | -10.3%, -2.10 | -8.8%, -1.09 | -2.2%, -0.28 | -9.4%, -1.41 |
| QQQ | N2 | -6.2%, -1.39 | -3.3%, -0.56 | -8.9%, -1.70 | -4.9%, -0.94 |
| QQQ | N3 | -12.1%, -4.29 | -13.8%, -4.04 | -16.4%, -6.42 | -13.1%, -4.18 |
| QQQ | N4 | -86.3%, -13.26 | -82.2%, -10.17 | -88.5%, -13.57 | -84.5%, -11.65 |
| QQQ | N5 | -15.3%, -1.44 | -10.4%, -0.71 | -14.6%, -0.76 | -13.0%, -1.02 |
| QQQ | N6 | -18.6%, -1.37 | -16.8%, -0.92 | -50.1%, -3.94 | -18.8%, -1.19 |
| QQQ | N7 | -12.0%, -1.13 | -4.4%, -0.28 | -21.2%, -1.88 | -8.7%, -0.70 |
| QQQ | N8 | -11.9%, -4.42 | -12.5%, -3.79 | -15.4%, -7.45 | -12.3%, -4.11 |

The slice after the cutoff is a few months long, so its growth a year is a short sample stretched to a year.

## Trades and the best days

Whole sample at 2 bps. The share of the log growth from the best 10 days is shown only where the whole-sample growth is above zero.

| Fund | Rule | Trades | Share of days with a trade | Share of log growth from the best 10 days |
|---|---|---|---|---|
| SPY | N1 | 2814 | 0.50 | n/a |
| SPY | N2 | 2692 | 0.34 | n/a |
| SPY | N3 | 2989 | 0.53 | n/a |
| SPY | N4 | 48308 | 1.00 | n/a |
| SPY | N5 | 5617 | 1.00 | n/a |
| SPY | N6 | 5617 | 1.00 | n/a |
| SPY | N7 | 2862 | 0.51 | n/a |
| SPY | N8 | 3032 | 0.54 | n/a |
| QQQ | N1 | 1945 | 0.50 | n/a |
| QQQ | N2 | 1753 | 0.32 | 1.05 |
| QQQ | N3 | 2120 | 0.54 | n/a |
| QQQ | N4 | 30744 | 0.99 | n/a |
| QQQ | N5 | 3893 | 1.00 | 2.17 |
| QQQ | N6 | 3893 | 1.00 | n/a |
| QQQ | N7 | 1954 | 0.50 | n/a |
| QQQ | N8 | 2132 | 0.55 | n/a |

## Sensitivities, reported and not judged

At 2 bps. One minute later: every fill at a minute's open moved one minute later. N1 extra stop cost: every stop pays one more cost.

| Fund | Rule | held back: Sharpe as run | held back: Sharpe one minute later | whole: Sharpe as run | whole: Sharpe one minute later |
|---|---|---|---|---|---|
| SPY | N1 | -0.64 | -0.60 | -0.83 | -0.88 |
| SPY | N2 | -0.14 | -0.23 | -0.12 | -0.32 |
| SPY | N3 | -2.25 | -2.21 | -1.80 | -1.77 |
| SPY | N4 | -6.82 | -7.02 | -7.57 | -7.64 |
| SPY | N5 | 0.16 | 0.12 | -0.36 | -0.33 |
| SPY | N6 | -0.42 | -0.39 | -0.45 | -0.48 |
| SPY | N7 | -0.27 | -0.22 | -0.24 | -0.27 |
| SPY | N8 | -1.87 | -1.79 | -1.52 | -1.48 |
| QQQ | N1 | -0.16 | -0.18 | -0.30 | -0.43 |
| QQQ | N2 | 0.62 | 0.51 | 0.37 | 0.28 |
| QQQ | N3 | -1.78 | -1.72 | -1.76 | -1.77 |
| QQQ | N4 | -4.14 | -4.70 | -5.34 | -5.68 |
| QQQ | N5 | 0.36 | 0.35 | 0.16 | 0.23 |
| QQQ | N6 | -0.09 | -0.08 | -0.27 | -0.33 |
| QQQ | N7 | 0.29 | 0.27 | -0.07 | -0.15 |
| QQQ | N8 | -1.43 | -1.37 | -1.55 | -1.52 |

- SPY N1 with one more cost per stop: whole-sample Sharpe -1.23, growth a year -6.1%.
- QQQ N1 with one more cost per stop: whole-sample Sharpe -0.57, growth a year -4.1%.

## Year by year

Growth in each calendar year at 2 bps. The first and last years are part years.

### SPY

| Year | Holding | N1 | N2 | N3 | N4 | N5 | N6 | N7 | N8 |
|---|---|---|---|---|---|---|---|---|---|
| 2003 | +6.1% | +0.9% | +1.1% | -1.6% | -13.2% | +0.1% | +2.3% | +1.3% | -0.8% |
| 2004 | +9.0% | -5.9% | -0.5% | -5.6% | -58.8% | -8.9% | -0.9% | +0.4% | -3.9% |
| 2005 | +2.7% | -5.9% | -2.8% | -6.3% | -61.9% | -0.9% | -14.0% | -4.4% | -4.4% |
| 2006 | +13.6% | -4.1% | -2.2% | -4.2% | -61.7% | -2.4% | -3.5% | +2.8% | -6.1% |
| 2007 | +3.5% | -1.9% | -0.9% | -0.9% | -58.9% | -6.7% | -7.4% | -6.1% | -1.1% |
| 2008 | -38.4% | +11.7% | +3.7% | +0.1% | -30.4% | -38.8% | -12.3% | +10.2% | +6.4% |
| 2009 | +23.5% | -7.8% | +8.8% | -2.8% | -57.0% | -6.8% | +8.7% | -9.7% | -6.0% |
| 2010 | +12.8% | -6.5% | +0.2% | -1.6% | -52.7% | -5.7% | -2.0% | -1.2% | -1.9% |
| 2011 | -0.1% | -8.1% | -0.6% | -2.4% | -54.5% | -7.1% | -11.9% | -11.3% | -0.4% |
| 2012 | +13.4% | -5.9% | +5.4% | -2.9% | -52.3% | -8.1% | +1.2% | +5.7% | -4.6% |
| 2013 | +29.6% | -0.9% | -2.4% | -3.1% | -55.6% | +2.1% | +3.8% | +10.0% | -2.3% |
| 2014 | +11.4% | -3.8% | -3.4% | -5.4% | -52.1% | -1.4% | -7.6% | -3.7% | -3.8% |
| 2015 | -0.8% | -9.1% | -3.5% | -5.1% | -57.4% | -8.8% | -11.1% | -0.7% | -2.9% |
| 2016 | +9.6% | -6.0% | -2.8% | -5.1% | -56.2% | -12.0% | +1.9% | -2.1% | -5.4% |
| 2017 | +19.4% | -4.7% | -4.1% | -7.1% | -57.8% | -0.3% | -2.0% | -3.8% | -7.1% |
| 2018 | -6.3% | -5.8% | +0.1% | -9.3% | -60.7% | +1.7% | -24.5% | -14.4% | -6.9% |
| 2019 | +28.7% | +0.3% | -1.5% | -4.6% | -55.2% | +0.1% | +5.3% | +6.8% | -4.2% |
| 2020 | +16.1% | -9.2% | -0.9% | -5.7% | -48.1% | +6.4% | -10.3% | -1.1% | -2.9% |
| 2021 | +27.0% | -4.1% | +4.0% | -13.3% | -49.3% | +6.5% | -2.3% | -5.0% | -9.7% |
| 2022 | -19.5% | +6.3% | +5.7% | -8.2% | -50.8% | -17.0% | -20.6% | -10.0% | -0.9% |
| 2023 | +24.6% | -4.9% | +2.0% | -2.8% | -52.1% | -2.7% | +5.3% | +1.5% | -4.6% |
| 2024 | +22.9% | -6.3% | -2.5% | -6.8% | -53.9% | +8.8% | -7.6% | -4.9% | -9.0% |
| 2025 | +16.4% | -5.5% | -7.1% | -5.1% | -50.7% | +7.3% | -11.1% | -8.1% | -6.9% |
| 2026 | +5.4% | -2.0% | -6.5% | -6.4% | -54.3% | +6.9% | -17.6% | -5.8% | -7.3% |

### QQQ

| Year | Holding | N1 | N2 | N3 | N4 | N5 | N6 | N7 | N8 |
|---|---|---|---|---|---|---|---|---|---|
| 2011 | -1.7% | -6.3% | +4.8% | -0.9% | -35.1% | -8.7% | -6.7% | -7.3% | +2.1% |
| 2012 | +16.6% | -5.9% | +2.5% | -3.7% | -49.5% | -2.7% | -1.3% | -1.4% | -4.2% |
| 2013 | +35.1% | +4.3% | -2.6% | -5.8% | -53.3% | +7.8% | +3.4% | +11.2% | -6.7% |
| 2014 | +17.4% | -0.4% | +0.6% | -3.4% | -55.2% | +4.2% | -7.7% | -14.7% | -4.1% |
| 2015 | +8.4% | -7.8% | -0.7% | -5.3% | -53.6% | -7.3% | -4.5% | -8.1% | -4.8% |
| 2016 | +5.9% | +3.9% | -3.2% | -5.2% | -55.7% | -10.9% | -2.7% | +5.9% | -5.4% |
| 2017 | +31.4% | -5.1% | -0.8% | -5.3% | -54.1% | +5.1% | +2.3% | -1.6% | -5.8% |
| 2018 | -1.0% | -6.6% | +3.8% | -6.5% | -48.5% | +2.8% | -21.1% | -18.6% | -4.4% |
| 2019 | +37.8% | +4.5% | +1.9% | -4.9% | -47.3% | +7.0% | +5.3% | +7.5% | -5.1% |
| 2020 | +47.5% | -10.7% | -0.1% | -2.7% | -31.7% | +18.2% | +2.4% | +7.1% | -3.0% |
| 2021 | +26.8% | -3.9% | +3.1% | -12.2% | -38.5% | +7.3% | -3.4% | +0.6% | -6.6% |
| 2022 | -33.0% | +7.8% | +9.5% | -9.3% | -40.6% | -22.5% | -29.3% | -3.9% | +1.1% |
| 2023 | +53.7% | -7.6% | +9.3% | -6.8% | -45.5% | +3.9% | +21.2% | +12.1% | -5.5% |
| 2024 | +24.8% | -1.1% | +1.4% | -6.1% | -50.9% | +14.5% | -10.8% | -7.6% | -8.8% |
| 2025 | +20.2% | +1.9% | +2.7% | -5.6% | -46.1% | +2.8% | -4.3% | +6.4% | -7.6% |
| 2026 | +3.9% | +0.6% | -3.5% | -2.4% | -50.2% | +5.1% | -17.4% | -4.9% | -4.4% |

## What this does and does not show

- MEASURED: the figures above, on this price source, with the fills and costs of the plan.
- UNKNOWN: whether the prices are adjusted for dividends. If they are not, holding the fund and N5 both miss the dividend, about the fund's yield a year, and the day-only rules miss nothing. That favours the day-only rules against holding in marks 1 and 2.
- UNKNOWN: the stock calendar, written from memory. Days whose bars did not match it were not used.
- UNKNOWN: whether the one-minute prices are right on the days used. Days whose one-minute range or last close disagreed with the daily file by more than `replay_07_data` allows were not used. A wrong price inside the range would not be found.
- Not tested: real fills. The costs are assumed, not measured on SPY or QQQ. Market-on-close and opening fills are taken at the bar prices.
- Not tested: shorting, leverage and volatility sizing, which the papers' headline numbers use.

