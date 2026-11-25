# Replay 06: slow trend rules on funds

MEASURED. 0 of 6 passed at the assumed 5 bps per side. G5 passed only the cost mark. In the held-back slice, 0 beat SPY hold on yearly gain. These are simulated results, not a practice or live account record.

## What was asked

- STATED. Can slow trend rules on funds you can buy cut losses and still beat holding after costs? Each rule faced its own holding yardstick, and every rule was also shown against SPY hold. Where a pass mark uses a holding yardstick, it uses the rule's own. G6 was a fixed mix, not a timing rule.

## How it ran

- MEASURED. Design: 2017-02-01 through 2022-12-30 (1,490 sessions). Held back: 2023-01-03 through 2026-11-24 (978 sessions). The held period ran once against [the frozen plan](../../research_rig/PREREG_06_fund_trend_paid_data.md) in `af8554c`. Mark 3 counted 122 trials: 116 prior plus 6 new, including the G6 context row (`replay_06_statistics` and the ledger).
- STATED. The runner used [Alpaca SIP daily bars](https://docs.alpaca.markets/reference/stockbars) adjusted for distributions and splits: SPY, EFA, IEF, VNQ, DBC, GLD, QQQ, IWM, BIL. Signals used data through the decision close, with fills at the next session's open. Inactive trend sleeves held BIL. Each slice started from cash; no sale was added at its end. The simulated opening price is not proof that an order would fill there.
- STATED. The judging cost was 5 bps on each buy or sell (`cost_model_bps_per_side_liquid_etf`), including the first buy for each yardstick and trades in BIL. It was an allowance for spread and slippage, not a measured charge.
- STATED. The basket yardsticks held equal parts and rebalanced yearly. G6 started at 60% SPY and 40% IEF, and reset yearly. The equal SPY/IEF yardstick is extra context for G3.

## Rules against holding

MEASURED. Each result cell shows yearly gain / annualized Sharpe above BIL / largest drop from a closing peak / trade sides. All use 5 bps per side. A buy or sell in a fund is a side. SPY appears twice where it is both the main yardstick and the common comparison.

### Design

| Rule | Rule result | Own holding yardstick | Yardstick result | SPY hold |
|---|---:|---|---:|---:|
| G1: Month-end trend, core funds | 4.67% / 0.54 / -7.94% / 119 | Core funds hold | 6.25% / 0.47 / -25.54% / 30 | 10.98% / 0.58 / -33.79% / 1 |
| G2: Daily trend ensemble, core funds | 4.47% / 0.55 / -7.27% / 3,154 | Core funds hold | 6.25% / 0.47 / -25.54% / 30 | 10.98% / 0.58 / -33.79% / 1 |
| G3: SPY momentum versus bills, else IEF | 4.86% / 0.30 / -33.79% / 11 | SPY hold | 10.98% / 0.58 / -33.79% / 1 | 10.98% / 0.58 / -33.79% / 1 |
| G4: Month-end trend on SPY | 5.42% / 0.39 / -22.89% / 25 | SPY hold | 10.98% / 0.58 / -33.79% / 1 | 10.98% / 0.58 / -33.79% / 1 |
| G5: Top ranked funds above trend | 9.15% / 0.66 / -16.34% / 248 | All eligible funds hold | 7.61% / 0.54 / -24.91% / 48 | 10.98% / 0.58 / -33.79% / 1 |
| G6: Fixed SPY/IEF mix, no timing | 6.87% / 0.56 / -21.38% / 12 | SPY hold | 10.98% / 0.58 / -33.79% / 1 | 10.98% / 0.58 / -33.79% / 1 |

Extra yardstick for G3, equal SPY/IEF hold: 5.80% / 0.54 / -20.68% / 12. This yardstick was not used to judge G3.

### Held

| Rule | Rule result | Own holding yardstick | Yardstick result | SPY hold |
|---|---:|---|---:|---:|
| G1: Month-end trend, core funds | 6.52% / 0.29 / -8.20% / 87 | Core funds hold | 10.47% / 0.64 / -10.52% / 20 | 18.93% / 0.92 / -18.75% / 1 |
| G2: Daily trend ensemble, core funds | 4.65% / 0.05 / -6.21% / 2,355 | Core funds hold | 10.47% / 0.64 / -10.52% / 20 | 18.93% / 0.92 / -18.75% / 1 |
| G3: SPY momentum versus bills, else IEF | 14.62% / 0.69 / -18.75% / 3 | SPY hold | 18.93% / 0.92 / -18.75% / 1 | 18.93% / 0.92 / -18.75% / 1 |
| G4: Month-end trend on SPY | 10.74% / 0.52 / -11.46% / 15 | SPY hold | 18.93% / 0.92 / -18.75% / 1 | 18.93% / 0.92 / -18.75% / 1 |
| G5: Top ranked funds above trend | 15.40% / 0.83 / -11.90% / 168 | All eligible funds hold | 14.08% / 0.84 / -11.82% / 32 | 18.93% / 0.92 / -18.75% / 1 |
| G6: Fixed SPY/IEF mix, no timing | 12.24% / 0.78 / -10.35% / 8 | SPY hold | 18.93% / 0.92 / -18.75% / 1 | 18.93% / 0.92 / -18.75% / 1 |

Extra yardstick for G3, equal SPY/IEF hold: 10.56% / 0.70 / -8.48% / 8. This yardstick was not used to judge G3.

### Holding with exposure matched in hindsight

MEASURED. This check uses each rule's own yardstick and BIL, with 5 bps per side. The rule's average weight outside BIL sets the yardstick's target weight. That weight is known only after the slice, so this is not a trading rule or pass mark. The cells use the same units as the tables above.

| Rule | Design yardstick with BIL | Held yardstick with BIL |
|---|---:|---:|
| G1 | 4.56% / 0.48 / -16.30% / 36 | 9.07% / 0.63 / -8.00% / 24 |
| G2 | 4.57% / 0.48 / -16.36% / 36 | 8.56% / 0.62 / -7.06% / 24 |
| G3 | 10.98% / 0.58 / -33.79% / 1 | 18.93% / 0.92 / -18.75% / 1 |
| G4 | 9.22% / 0.56 / -28.61% / 2 | 17.62% / 0.91 / -17.31% / 2 |
| G5 | 7.07% / 0.54 / -22.58% / 54 | 14.02% / 0.84 / -11.74% / 36 |
| G6 | 10.98% / 0.58 / -33.79% / 1 | 18.93% / 0.92 / -18.75% / 1 |

## Pass marks

- STATED. In the held period, mark 1 requires higher Sharpe than the main yardstick and a largest drop at most 60.00% as large (`replay_max_drop_ratio_vs_hold`).
- STATED. Mark 2 uses compounded growth across both reset slices. The rule must beat its yardstick at no cost and stay ahead through 10 bps per side (`backtest_min_breakeven_cost_multiple`).
- STATED. Mark 3 requires whole-sample deflated Sharpe above 0.95 (`replay_min_deflated_sharpe`). This mark raises the bar because many rules were tried.
- MEASURED. Mark 4 used the worst overfitting estimate, 49.49%, against a cap of 25.00% (`backtest_max_pbo`). Estimates by fixed start: 2017-02-01: 32.49%; 2019-01-02: 49.49%; 2021-01-04: 49.10%.
- STATED. Mark 5 requires beating more than 95.00% of the matched timing draws (`replay_min_shuffle_percentile`). G6 has no timing control, so it cannot pass mark 5.

MEASURED. These are the stored verdicts at a judging cost of 5 bps per side.

| Rule | Mark 1 | Mark 2 | Mark 3 | Mark 4 | Mark 5 | Overall | Break-even bps/side | Deflated Sharpe | Timing draws beaten |
|---|---|---|---|---|---|---|---:|---:|---:|
| G1 | fail | fail | fail | fail | fail | fail | never ahead at zero | 0.59 | 30.60% |
| G2 | fail | fail | fail | fail | fail | fail | never ahead at zero | 0.49 | 57.90% |
| G3 | fail | fail | fail | fail | fail | fail | never ahead at zero | 0.59 | 1.70% |
| G4 | fail | fail | fail | fail | fail | fail | never ahead at zero | 0.59 | 1.00% |
| G5 | fail | pass | fail | fail | fail | fail | 30.39 | 0.87 | 59.90% |
| G6 | fail | fail | fail | fail | fail | fail | never ahead at zero | 0.80 | n/a |

## Cost and fill checks

MEASURED. The table shows yearly gain. The cost-free and doubled-cost checks fill at the next open. The next-close check uses the same 5 bps per side as the main run. These are checks, not new pass verdicts.

| Rule or yardstick | Design: 0 bps | Design: 10 bps | Design: next close | Held: 0 bps | Held: 10 bps | Held: next close |
|---|---:|---:|---:|---:|---:|---:|
| G1: Month-end trend, core funds | 4.88% | 4.46% | 4.71% | 6.74% | 6.29% | 5.83% |
| G2: Daily trend ensemble, core funds | 6.14% | 2.83% | 4.09% | 6.57% | 2.76% | 4.95% |
| G3: SPY momentum versus bills, else IEF | 4.96% | 4.76% | 4.86% | 14.67% | 14.58% | 14.57% |
| G4: Month-end trend on SPY | 5.64% | 5.20% | 6.48% | 10.96% | 10.53% | 10.39% |
| G5: Top ranked funds above trend | 9.46% | 8.84% | 8.11% | 15.69% | 15.11% | 14.84% |
| G6: Fixed SPY/IEF mix, no timing | 6.88% | 6.86% | 6.91% | 12.26% | 12.22% | 12.45% |
| SPY: SPY hold | 10.99% | 10.97% | 11.03% | 18.94% | 18.91% | 19.21% |
| HOLD_CORE: Core funds hold | 6.26% | 6.23% | 6.29% | 10.48% | 10.45% | 10.67% |
| HOLD_ALL: All eligible funds hold | 7.63% | 7.60% | 7.65% | 14.10% | 14.06% | 14.31% |
| SPY_IEF: Equal SPY/IEF hold | 5.82% | 5.79% | 5.84% | 10.58% | 10.54% | 10.75% |

## Timing control

MEASURED. The control used 1,000 timing draws per rule where available. It rotated each rule's target schedule within each slice, kept fund targets together and charged the same 5 bps per side. It did not force the same turnover. Turnover is traded dollars divided by account value, per year. Each pair is rule / mean control. Non-BIL weight is the average share of the account outside BIL.

| Rule | Design turnover | Held turnover | Design non-BIL weight | Held non-BIL weight |
|---|---:|---:|---:|---:|
| G1 | 392.99% / 405.62% | 425.22% / 461.10% | 64.00% / 63.41% | 76.52% / 76.44% |
| G2 | 3167.75% / 3204.59% | 3640.73% / 3696.74% | 64.23% / 63.60% | 67.90% / 67.78% |
| G3 | 184.23% / 217.23% | 77.24% / 127.53% | 100.00% / 100.00% | 100.00% / 100.00% |
| G4 | 422.27% / 416.88% | 386.59% / 431.53% | 78.86% / 78.86% | 89.37% / 89.35% |
| G5 | 572.54% / 591.10% | 505.10% / 535.54% | 90.53% / 90.62% | 99.34% / 99.29% |
| G6 | 23.39% / n/a | 32.07% / n/a | 100.00% / n/a | 100.00% / n/a |

MEASURED. Each twin figure is total gain for the first timing draw in that slice, not yearly gain. The last column compares compounded growth across both slices; ties do not count as wins.

| Rule | Design twin total gain | Held twin total gain | Whole-sample draws beaten |
|---|---:|---:|---:|
| G1 | 48.61% | 46.92% | 30.60% |
| G2 | 10.81% | 32.03% | 57.90% |
| G3 | 78.82% | 66.25% | 1.70% |
| G4 | 30.70% | 114.52% | 1.00% |
| G5 | 21.74% | 100.96% | 59.90% |
| G6 | n/a | n/a | n/a |

## What it shows

- MEASURED. G5 earned 15.40% per year versus 14.08% for holding its funds and 18.93% for SPY. It broke even against its own yardstick at 30.39 bps per side over the combined slices. Its held-back Sharpe was lower than that yardstick's (0.83 versus 0.84).
- MEASURED. G4, the closest comparison to the practice trend rule, earned 10.74% a year with a -11.46% drawdown versus 18.93% and -18.75% for SPY hold. The smaller drop did not make it a pass.

## What it does not show

- MEASURED. The held period contains 46 complete months (`fund_coverage_06.json`). The bars begin 2016-01-04 (`replay_06_data.first_bar`); they do not include the 2008 financial crisis.
- STATED. Months and funds can move together. The fund list was chosen from funds that survived. Backward dividend adjustments can change with vendor revisions. The replay used a single price source and did not test capacity, tax, real dividend reinvestment or actual fill costs.
- STATED. With independent months, 10.00% assumed annual active volatility and 80.00% power, the sketch needs about 12.7 percentage points of yearly edge at a one-sided 5.00% cutoff (`replay_06_statistics`). This is for a simple mean-return check, not the five marks. The slice cannot confirm a small edge. Even a pass here would be weak evidence.
- UNKNOWN. Whether the same rules hold up through other regimes or on future practice fills.

## What it means for T1 on VTI

- STATED. The practice desk uses T1 on VTI; G4 used the same 10-month idea on SPY and did not test T1 on VTI. G4's result is a warning about the trade-off, not a reason to count T1 as profitable, declare it broken or promote it beyond pretend money. Keep T1 as a forward control and judge it against holding VTI with the practice records and actual costs.

## Rows to paste

Status results table:

```markdown
| Replay 06 | Slow trend and allocation rules on Alpaca daily fund bars | 0 of 6 passed at 5 bps per side. G5 passed only the cost mark: held back 2023-01-03 through 2026-11-24, 15.40% a year versus 14.08% for its yardstick and 18.93% for SPY hold. | `docs/research/35_replay_06_fund_trend.md` |
```

Queue Done table:

```markdown
| 14 | Replay 06: fund trend rules on daily prices | Done. Held-back slice run once. 0 of 6 passed at 5 bps per side. G5 beat its own yardstick on yearly gain, but not SPY hold or all the marks (`docs/research/35_replay_06_fund_trend.md`). |
```

Generated by `research_rig/report_06.py` from `results_06.json`, `fund_coverage_06.json` and `fund_adjustments_06.json`. The report reads no market bars and runs no rule.
