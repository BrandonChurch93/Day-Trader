# 22. Replay 05: slow trend rules on the US stock market, free data from 1927

Status: research result. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Plan written and pushed before the run: `research_rig/PREREG_05_stock_trend_free_data.md`. Correction written and pushed before the corrected run: `research_rig/AMENDMENT_05_I2_equal_thirds.md`. Every number below is MEASURED by `research_rig/run_05.py` and placed here by `research_rig/build_doc22.py`, unless it says it is the auditor's.

## How this was run, including what went wrong

- Before the full run, the script was tried once with 3 shuffles at the middle cost to see that it worked. I saw rough results from that try. No rule or setting was changed afterwards.
- Two full starts were lost to process problems on the test machine and were restarted unchanged. No result from them was read.
- The first full run finished and is kept as `research_rig/results_05.json`.
- An independent audit then found that the code for rule I2 did not do what the plan says (`audit/2026-11-25_replay_05_audit.md`, finding 1). The plan says one third in each of three industry groups. The code split the account in three once, in 1927, and never again. MEASURED by the auditor: by 2026-06-30 one third had grown to 87.8% of the account.
- The correction was written down and pushed, then the run was repeated with only that change. It is kept as `research_rig/results_05b.json`.
- The auditor had already measured what the correction would do before it was written down. So a pass that appears only in the corrected run is a pass after a correction whose effect was known. This page reports it as that.
- The audit found no look-ahead in any of the eight rules, and its own separate rebuild of holding the market and of rule T1 from the raw file matched the rig exactly (MEASURED by the auditor).

## Bottom line

- 26,014 trading days, 1927-08-01 to 2026-09-30. Eight rules. Held-back slice: 2006-06-01 to 2026-06-30.
- Rules that pass all five marks in the first run: none at 2 bps a side, none at 5 bps, T1, T5, V1, I1 at 10 bps.
- Rules that pass all five marks in the corrected run: T1, T2, T4, T5, V1, I1, I2 at 2 bps a side, T1, T5, V1, I1, I2 at 5 bps, T1, T5, V1, I1, I2 at 10 bps.
- Rules that pass in both runs at all three cost levels: none. That is the only reading with no asterisk. Rules that pass in both runs at 10 bps only: T1, T5, V1, I1.
- Verdicts that changed between the runs: T1 at 2 bps: fail to PASS; T2 at 2 bps: fail to PASS; T4 at 2 bps: fail to PASS; T5 at 2 bps: fail to PASS; V1 at 2 bps: fail to PASS; I1 at 2 bps: fail to PASS; I2 at 2 bps: fail to PASS; T1 at 5 bps: fail to PASS; T5 at 5 bps: fail to PASS; V1 at 5 bps: fail to PASS; I1 at 5 bps: fail to PASS; I2 at 5 bps: fail to PASS; I2 at 10 bps: fail to PASS.
- Verdicts changed for rules whose own trades did not change at all (T1 at 2 bps: fail to PASS; T2 at 2 bps: fail to PASS; T4 at 2 bps: fail to PASS; T5 at 2 bps: fail to PASS; V1 at 2 bps: fail to PASS; I1 at 2 bps: fail to PASS; T1 at 5 bps: fail to PASS; T5 at 5 bps: fail to PASS; V1 at 5 bps: fail to PASS; I1 at 5 bps: fail to PASS). The only thing that moved for them is mark 4, which is worked out across the whole set of eight rules.
- In the first run, the rules that failed mark 4 and nothing else: T1, T2, T4, T5, V1, I1 at 2 bps, T1, T5, V1, I1 at 5 bps, none at 10 bps.
- What the rules did in the held-back slice, in plain terms: holding the market grew +11.5% a year with a largest drop of -54.6%. The seven rules other than I2 grew between +6.5% and +9.7% a year, with largest drops between -19.5% and -40.2%. Rules that grew more than their comparison at 5 bps: none.
- Rules with a better Sharpe ratio than their comparison in the held-back slice: T1, T5, V1, I1, I2. Rules whose largest drop was small enough for mark 1: T1, T2, T4, T5, V1, I1, I2. Rules that pass mark 1: T1, T5, V1, I1, I2.
- Rules that beat a fixed mix of stocks and cash on both Sharpe ratio and largest drop in the held-back slice: T1, T2, T5, V1, I1, I2. The fixed mix holds the rule's own average share in stocks from the development slice.
- Rules whose Sharpe ratio is above the comparison's over the whole sample even at the low end of the resampled range: T2, V1, I2. For every other rule the range includes zero, so the gap could be chance.
- The ten-month rule, the best known of these: +9.1% a year against +11.5% for holding, largest drop -21.9% against -54.6%, in stocks 79% of the time on average.
- Mark 3 screened nothing in this test. The lowest deflated Sharpe of any rule at any cost was 0.9978 against a bar of 0.95 (`replay_min_deflated_sharpe`). The plan takes the spread of Sharpe ratios across these eight rules. They all trade the same market and sit close together, so the hurdle is near zero (auditor's finding 2). The code follows the plan. The plan was not changed after the run.
- Taxes are not in these numbers. A rule that sells pays tax sooner than holding does.

## What this means

- These rules gave up growth and cut the largest drop. That is the same shape the live funds built on these rules show (`docs/research/21_systematic_funds_and_published_rules.md`).
- None of this is fast money. The best case here is a smoother ride at a lower return than holding.
- Whether a rule "passes" here hangs on mark 4, and mark 4 moved from fail to pass when one of the eight rules was corrected. `docs/research/16_rig_audit.md` found the same weakness on bitcoin. The value in `backtest_max_pbo` is not changed. How to measure mark 4 in a steadier way is an open question for the owner.
- A pass means "worth running in the practice account". It does not mean "makes money".

## The overfitting estimate (mark 4), both runs

| Cost per side | First run | First run, latest days dropped | Corrected run | Corrected run, latest days dropped | Bar | Ties |
|---|---|---|---|---|---|---|
| 2 bps | 0.287 | 0.294 | 0.177 | 0.185 | under 0.25 | 0.0% of cases |
| 5 bps | 0.307 | 0.319 | 0.174 | 0.183 | under 0.25 | 0.0% of cases |
| 10 bps | 0.234 | 0.243 | 0.131 | 0.136 | under 0.25 | 0.0% of cases |

With eight rules there are no ties, so the three tie readings are equal.

## Rule I2, first run against corrected run, held-back slice

| Run | Cost per side | Growth a year | Sharpe above bills | Largest drop | Drop as a share of the market's | Mark 1 | All five |
|---|---|---|---|---|---|---|---|
| First run, code as it was | 2 bps | +13.5% | 0.67 | -39.6% | 73% | fail | fail |
| First run, code as it was | 5 bps | +13.3% | 0.66 | -39.7% | 73% | fail | fail |
| First run, code as it was | 10 bps | +13.0% | 0.64 | -39.9% | 73% | fail | fail |
| Corrected run, equal thirds on re-entry | 2 bps | +11.3% | 0.66 | -26.8% | 49% | PASS | PASS |
| Corrected run, equal thirds on re-entry | 5 bps | +11.1% | 0.65 | -26.9% | 49% | PASS | PASS |
| Corrected run, equal thirds on re-entry | 10 bps | +10.7% | 0.63 | -27.1% | 50% | PASS | PASS |

Three cautions about rule I2 in the corrected run:

- It passes only after the correction, and the effect of the correction was known before it was written down.
- Its 2020 year was +65.1%, against +23.8% for the ten-month rule. In 2020 one of the twelve industry groups, Durbl, rose +165.9%. The next highest, BusEq, rose +45.4% (MEASURED from the industry file by `research_rig/i2_2020_note.py`). Which groups I2 held in 2020 is not in the output file, and which companies drove that group is not checked (both UNKNOWN). The likely reading, not proven here, is that one group's one year is a large part of what I2 did in the held-back slice.
- The twelve groups are index groups. They cannot be bought as they are. Sector funds are the nearest thing and they are not the same groups. No sector fund has been tested here.

## What the rules are

| Id | Rule |
|---|---|
| T1 | Hold the market when it is above its ten-month average, else Treasury bills. Checked at month end |
| T2 | Hold the market when it is above its 200-day average, else bills. Checked daily |
| T3 | Hold the market when its last 12 months beat bills, else bills. Checked at month end |
| T4 | Share in stocks equals how many of the 20, 50, 100 and 200 day averages the market is above |
| T5 | The first published version of the Pacer Trendpilot rule: all in, half in, or out, using the 200-day average |
| V1 | No trend. Hold less when the market has been jumpy |
| I1 | Twelve industry groups, each on its own ten-month rule |
| I2 | When the ten-month rule says hold, own the three industry groups that rose most over 12 months, one third each |

The twelve industry sleeves in I1, and in its comparison, start equal in 1927 and are never set back to equal, as the plan says. MEASURED by the auditor: by 2006-06-01 the sleeves of I1 ranged from 2.8% to 18.5% of the account (finding 5).

## Held-back slice, 2006-06-01 to 2026-06-30, at 5 bps a side, corrected run

| Rule | Growth a year | Sharpe above bills | Largest drop | Average share in stocks | Days with a trade, a year |
|---|---|---|---|---|---|
| Hold the market | +11.5% | 0.56 | -54.6% | 100% | |
| Hold the twelve industries | +10.5% | 0.54 | -48.4% | 100% | |
| T1. Ten-month rule | +9.1% | 0.61 | -21.9% | 79% | 1.5 |
| T2. 200-day rule | +8.0% | 0.56 | -24.2% | 78% | 6.4 |
| T3. Twelve-month momentum | +8.4% | 0.50 | -40.2% | 80% | 0.9 |
| T4. Four-average ensemble (P1) | +6.5% | 0.50 | -21.5% | 72% | 52.2 |
| T5. Trendpilot, first version | +9.7% | 0.65 | -27.6% | 79% | 2.1 |
| V1. Size by volatility, no trend | +8.2% | 0.64 | -23.4% | 71% | 17.2 |
| I1. Twelve industries, each on the ten-month rule | +8.1% | 0.60 | -19.5% | 72% | 7.5 |
| I2. Top three industries with a market filter | +11.1% | 0.65 | -26.9% | 79% | 7.0 |

"Days with a trade" counts days, not sides. A switch between stocks and bills pays two sides, and the cost of every side is charged. An earlier draft of this table called the column trade sides (auditor's finding 3).

## Whole sample, 1927-08-01 to 2026-09-30, at 5 bps a side, corrected run

| Rule | Growth a year | Sharpe above bills | Largest drop | Average share in stocks | Days with a trade, a year |
|---|---|---|---|---|---|
| Hold the market | +9.7% | 0.45 | -84.1% | 100% | |
| Hold the twelve industries | +9.9% | 0.47 | -83.5% | 100% | |
| T1. Ten-month rule | +8.9% | 0.52 | -47.6% | 72% | 1.5 |
| T2. 200-day rule | +9.5% | 0.59 | -41.1% | 72% | 5.5 |
| T3. Twelve-month momentum | +9.1% | 0.52 | -46.8% | 70% | 0.9 |
| T4. Four-average ensemble (P1) | +8.3% | 0.55 | -36.8% | 67% | 45.8 |
| T5. Trendpilot, first version | +9.6% | 0.57 | -54.8% | 75% | 2.2 |
| V1. Size by volatility, no trend | +8.4% | 0.54 | -51.2% | 78% | 13.0 |
| I1. Twelve industries, each on the ten-month rule | +9.0% | 0.56 | -56.7% | 69% | 6.8 |
| I2. Top three industries with a market filter | +11.8% | 0.65 | -54.0% | 72% | 5.5 |

## Pass marks

| Rule | Cost per side | 1 held-back | 2 break-even | 3 deflated Sharpe | 4 overfitting | 5 shuffle | All five, corrected run | All five, first run | Beat the fixed mix on the held-back slice |
|---|---|---|---|---|---|---|---|---|---|
| T1 | 2 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| T1 | 5 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| T1 | 10 bps | PASS | PASS | PASS | PASS | PASS | PASS | PASS | yes |
| T2 | 2 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| T2 | 5 bps | fail | PASS | PASS | PASS | PASS | fail | fail | yes |
| T2 | 10 bps | fail | fail | PASS | PASS | PASS | fail | fail | no |
| T3 | 2 bps | fail | PASS | PASS | PASS | PASS | fail | fail | no |
| T3 | 5 bps | fail | PASS | PASS | PASS | PASS | fail | fail | no |
| T3 | 10 bps | fail | PASS | PASS | PASS | PASS | fail | fail | no |
| T4 | 2 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| T4 | 5 bps | fail | fail | PASS | PASS | PASS | fail | fail | no |
| T4 | 10 bps | fail | fail | PASS | PASS | PASS | fail | fail | no |
| T5 | 2 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| T5 | 5 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| T5 | 10 bps | PASS | PASS | PASS | PASS | PASS | PASS | PASS | yes |
| V1 | 2 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| V1 | 5 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| V1 | 10 bps | PASS | PASS | PASS | PASS | PASS | PASS | PASS | yes |
| I1 | 2 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| I1 | 5 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| I1 | 10 bps | PASS | PASS | PASS | PASS | PASS | PASS | PASS | yes |
| I2 | 2 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| I2 | 5 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |
| I2 | 10 bps | PASS | PASS | PASS | PASS | PASS | PASS | fail | yes |

The numbers behind the marks, at 5 bps a side, corrected run:

| Rule | Held-back Sharpe, rule | Comparison | Drop as a share of the comparison's | Break-even cost per side | Deflated Sharpe | Share of shuffles beaten | Sharpe gap to the comparison, whole sample: low end, middle, high end of the resampled range | Fixed mix: share in stocks | Fixed mix: held-back Sharpe | Fixed mix: largest drop |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | 0.61 | 0.56 | 40% | 33 bps | 1.000 | 98.9% | -0.06, +0.07, +0.21 | 70% | 0.58 | -41.5% |
| T2 | 0.56 | 0.56 | 44% | 20 bps | 1.000 | 100.0% | +0.00, +0.14, +0.28 | 71% | 0.56 | -42.7% |
| T3 | 0.50 | 0.56 | 74% | 56 bps | 1.000 | 98.2% | -0.06, +0.07, +0.21 | 68% | 0.58 | -39.4% |
| T4 | 0.50 | 0.56 | 39% | 9 bps | 1.000 | 99.7% | -0.03, +0.11, +0.24 | 66% | 0.57 | -39.7% |
| T5 | 0.65 | 0.56 | 51% | 55 bps | 1.000 | 99.3% | -0.00, +0.13, +0.26 | 74% | 0.56 | -43.9% |
| V1 | 0.64 | 0.56 | 43% | 31 bps | 1.000 | 98.9% | +0.01, +0.09, +0.18 | 80% | 0.56 | -47.1% |
| I1 | 0.60 | 0.54 | 40% | 37 bps | 1.000 | 99.0% | -0.04, +0.09, +0.21 | 68% | 0.56 | -37.7% |
| I2 | 0.65 | 0.56 | 49% | 55 bps | 1.000 | 99.1% | +0.05, +0.20, +0.36 | 70% | 0.58 | -41.5% |

## The three bad years, at 5 bps a side, corrected run

| Rule | 2008 | 2020 | 2022 | Largest drop in 2008 | Largest drop in 2020 | Largest drop in 2022 |
|---|---|---|---|---|---|---|
| Hold the market | -36.5% | +24.2% | -20.0% | -47.7% | -34.2% | -25.4% |
| Hold the twelve industries | -32.5% | +21.3% | -13.1% | -44.0% | -33.6% | -19.8% |
| T1 | +0.3% | +23.8% | -10.4% | -1.5% | -12.7% | -12.5% |
| T2 | -0.9% | +27.4% | -15.8% | -2.6% | -12.9% | -16.7% |
| T3 | -3.2% | -1.8% | -12.6% | -10.8% | -34.2% | -14.9% |
| T4 | -9.0% | +26.5% | -15.5% | -10.5% | -9.2% | -16.3% |
| T5 | -0.1% | +4.0% | -10.1% | -2.8% | -27.6% | -12.1% |
| V1 | -14.5% | +8.2% | -10.4% | -17.0% | -14.9% | -12.8% |
| I1 | -6.6% | +18.7% | -1.5% | -8.7% | -15.4% | -9.0% |
| I2 | +1.1% | +65.1% | -2.8% | -0.8% | -14.3% | -13.5% |

## Does the fill assumption matter

Held-back Sharpe ratio at 5 bps a side, corrected run. The test trades one full day late. "Traded the same close" is the ideal case that cannot be done in practice.

| Rule | Held-back Sharpe as tested | Traded the same close | Cash earns nothing |
|---|---|---|---|
| T1 | 0.61 | 0.65 | 0.59 |
| T2 | 0.56 | 0.57 | 0.54 |
| T3 | 0.50 | 0.54 | 0.48 |
| T4 | 0.50 | 0.43 | 0.46 |
| T5 | 0.65 | 0.63 | 0.63 |
| V1 | 0.64 | 0.65 | 0.61 |
| I1 | 0.60 | 0.61 | 0.56 |
| I2 | 0.65 | 0.69 | 0.63 |

## What this does and does not show

- These are returns of an index that cannot be bought directly. A total market fund is the nearest thing. Fund fees and tracking gaps are left out for the rules and for holding alike.
- The held-back slice holds 2008, 2020 and 2022. The table above shows each year one by one.
- The three months after the designer's knowledge cutoff are far too short to mean anything and are in the output files only.
- This is the cheap first look. A fair test of funds that can be bought needs paid daily prices with opening prices (`docs/decisions/morning_list_2026-11-25.md`, `research_rig/PREREG_06_fund_trend_paid_data_DRAFT.md`).

## Files

- Plan: `research_rig/PREREG_05_stock_trend_free_data.md`. Correction: `research_rig/AMENDMENT_05_I2_equal_thirds.md`. Data notes: `research_rig/data_notes_french.md`
- Audit: `audit/2026-11-25_replay_05_audit.md`, `audit/replay_05_probes.py`
- Code: `research_rig/run_05.py`, `rig2.py`, `build_doc22.py`, `i2_2020_note.py`. Output: `research_rig/results_05.json` (first run), `research_rig/results_05b.json` (corrected run, started with `R05_POOL=1`)
- Trials counted in the deflated Sharpe formula: 44 (`research_rig/TRIAL_LEDGER.md`)

## Sources

- [Kenneth French data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
- [Pacer Trendpilot US Large Cap ETF prospectus, SEC](https://www.sec.gov/Archives/edgar/data/1616668/000089418925006695/pacertrendpilotuslargecape.htm)
