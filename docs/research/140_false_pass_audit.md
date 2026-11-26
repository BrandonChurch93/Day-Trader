# 140. False-pass audit: how many of our 3 passes could be luck

Written 2026-11-26 13:24 UTC by `research_rig/build_doc140_false_pass_audit.py`, which reads every figure below from repo files. No scorer was run, no price or result file off the repo was opened, and no return was computed.

Labels: MEASURED means a no-edge pass rate counted on made-up data by the plan's own pre-run file. MEASURED, one mark means only one of the marks was counted that way, so the all-mark rate is lower. NOMINAL means no rate was measured; the figure is the textbook tail of the plan's mark (a one-sided normal tail for a t of 2, or a percentile tail), worked out here, not measured. STATED means taken from a plan or results page as written. UNKNOWN means not on the repo.

## Headline

- Expected passes by luck across all 44 scored tests: low 0.68, high 4.13. Counted passes: 3.
- About half of the high figure comes from the 9 AI time-machine tests (0.32 to 2.03). Their marks were loose (a model above the 80th or 90th percentile of its own twins), but a clearing there is reported as shown, never as a counted pass, so they cannot explain the 3.
- Expected luck passes in the 34 trading tests that could give a counted pass: low 0.36, high 2.09. Against 3 seen, that is 1.4 to 8.2 times what luck alone gives.
- Chance of 3 or more passes by luck alone in those 34: 0.49% on the low figures, 34.92% on the high figures (independent tests assumed; the month-end tests share windows, which widens this).
- Rates: 13 tests have a measured all-mark no-edge rate, 8 have one measured mark only, 20 have no measured rate (UNKNOWN) and are bracketed by the nominal tail of their own t or percentile mark as the high and a stated low of 0.005 per test, and 3 could not pass at all (design only, inconclusive by design, a cost gate).
- Ideas closed before any return on count, power, cost, coverage, validation or feasibility: 35 (7 on count, 13 on power). They had no chance to pass by luck, so they add nothing to the luck figure.

## Assumptions, stated

- Low bracket where only a nominal t tail exists: 0.005 per test. The other marks (count floors, trims, year breadth) can only cut the tail, and the passes that did happen cleared the t mark by a small margin, so this is a floor, not an estimate.
- High bracket for a nominal t mark: the one-sided normal tail at t of 2, 2.28%, times the number of separately judged legs. It ignores the other marks, so it is a ceiling under normal errors. Fat tails, overlapping windows or few clusters can push a real no-edge rate above it; that is UNKNOWN for each such test.
- High bracket for a measured count: the one-sided 95% upper limit for that count. A 0 of 20 calibration still allows up to 13.91% by this rule, which is why those tests have wide highs.
- Tests are summed as if independent. Several are not (Replays 25, 31, 41 and 65 share month-end windows; Replays 48 and 53 share dates). Dependence does not change the expected count; it makes clusters of luck passes or misses more likely.

## The 44 tests

| # | Test | Family | Result (doc 95) | Label | Low | High | Where the figure comes from | Note |
|---:|---|---|---|---|---:|---:|---|---|
| 1 | Replay 01 (R1) | momentum | Failed / not credited (4/90 both feeds) | MEASURED, one mark | 0.50% | 4.50% | `docs/research/16_rig_audit.md`: deflated Sharpe mark (0.95) passed 4.5% of no-edge samples; overfitting mark let 8% through; plan `research_rig/PREREG_01_daily_crypto_trend.md` | measured for one mark of five; all marks together is lower and was not measured |
| 2 | Pilot 02 | AI discretionary | Inconclusive by design (6 runs) | STATED | 0.00% | 0.00% | `docs/research/14_ai_calls_pilot_02.md`: inconclusive by design | no pass mark, so no pass by luck was possible |
| 3 | Replay 03 (R1) | chart pattern | Failed (0/80 combinations pass) | MEASURED, one mark | 0.50% | 4.50% | `docs/research/16_rig_audit.md`: deflated Sharpe mark (0.95) passed 4.5% of no-edge samples; overfitting mark let 8% through; plan `research_rig/PREREG_03_intraday_crypto.md` | measured for one mark of five; all marks together is lower and was not measured |
| 4 | Replay 04 | momentum | Failed (0/25 combinations pass) | MEASURED, one mark | 0.50% | 4.50% | `docs/research/16_rig_audit.md`: deflated Sharpe mark (0.95) passed 4.5% of no-edge samples; overfitting mark let 8% through; plan `research_rig/PREREG_04_coin_basket_trend.md` | measured for one mark of five; all marks together is lower and was not measured |
| 5 | Replay 05 (R2) | momentum | Failed / not credited (0 both runs) | MEASURED, one mark | 0.50% | 4.50% | `docs/research/16_rig_audit.md`: deflated Sharpe mark (0.95) passed 4.5% of no-edge samples; overfitting mark let 8% through; plan `research_rig/PREREG_05_stock_trend_free_data.md` | measured for one mark of five; all marks together is lower and was not measured |
| 6 | Replay 06 | momentum | Failed (0/6 pass; best 1/5 marks) | MEASURED, one mark | 0.50% | 4.50% | `docs/research/16_rig_audit.md`: deflated Sharpe mark (0.95) passed 4.5% of no-edge samples; overfitting mark let 8% through; plan `research_rig/PREREG_06_fund_trend_paid_data.md` | measured for one mark of five; all marks together is lower and was not measured |
| 7 | Replay 07 | chart pattern | Failed (0/8 SPY, 0/8 QQQ pass) | MEASURED, one mark | 0.50% | 4.50% | `docs/research/16_rig_audit.md`: deflated Sharpe mark (0.95) passed 4.5% of no-edge samples; overfitting mark let 8% through; plan `research_rig/PREREG_07_intraday_spy_qqq.md` | measured for one mark of five; all marks together is lower and was not measured |
| 8 | Replay 09 | momentum | Failed (0/7 pass at 35 bps/side) | MEASURED, one mark | 0.50% | 4.50% | `docs/research/16_rig_audit.md`: deflated Sharpe mark (0.95) passed 4.5% of no-edge samples; overfitting mark let 8% through; plan `research_rig/PREREG_09_crypto_methods.md` | measured for one mark of five; all marks together is lower and was not measured |
| 9 | Replay 11 (design) | AI discretionary | Design only (held-back 2,146 open) | STATED | 0.00% | 0.00% | `docs/research/44_replay_11_earnings_reader.md`: design half only | held-back half not run, so no verdict and no pass by luck was possible |
| 10 | Replay 12 | copy-trading | Failed (2/5 marks on held-back) | MEASURED, one mark | 0.50% | 8.04% | `research_rig/noedge_12.json`: holds.63.pass_rate_blocks = 0.066 (66 of 1000), the chosen 63-day hold | measured for the bootstrap mark only; all five marks together is lower |
| 11 | Replay 13 Rule A | momentum | Relative marks met, not counted pass | NOMINAL | 0.50% | 1.29% | `config/thresholds.yaml` replay_13_plan: above the 75th percentile of random in at least 5 of 7 years | binomial tail of the random-percentile mark alone with independent years; not measured |
| 12 | Replay 13 Rule B | chart pattern | Failed (not paid, 0/7 vs random) | NOMINAL | 0.50% | 1.29% | `config/thresholds.yaml` replay_13_plan: above the 75th percentile of random in at least 5 of 7 years | binomial tail of the random-percentile mark alone with independent years; not measured |
| 13 | Replay 14 | momentum | Failed (1/4 marks each) | MEASURED | 4.25% | 12.32% | `research_rig/noedge_14.json`: by_cost.cost_5_bps.{small,wide}.passes.all_four = 17/400 and 16/400 | two judged lists; low is the larger list alone, high adds both upper limits |
| 14 | Replay 16 | momentum | Failed (0/4 marks) | MEASURED | 0.00% | 13.91% | `research_rig/PREREG_16_hot_five_hedged.md`: no edge, all four marks (0 of 20) | high is the one-sided 95% upper limit for that count |
| 15 | Replay 17 | chart pattern | Failed (0/3 marks) | MEASURED | 0.00% | 13.91% | `research_rig/PREREG_17_short_the_peak.md`: no edge, all three marks (0 of 20) | high is the one-sided 95% upper limit for that count |
| 16 | Replay 18 | carry | Failed (1/3 marks) | MEASURED | 0.00% | 13.91% | `research_rig/PREREG_18_funding_carry.md`: zero edge, all marks (0 of 20) | high is the one-sided 95% upper limit for that count |
| 17 | Replay 19 | calendar | Failed (1/5 marks) | MEASURED | 0.00% | 13.91% | `research_rig/PREREG_19_monday_asia.md`: 0 bps plant, all five marks (0 of 20) | high is the one-sided 95% upper limit for that count |
| 18 | Replay 20 | event | PASSED (5/5 marks, viewed dates) | MEASURED | 0.00% | 13.91% | `research_rig/PREREG_20_upbit_listing_short.md`: 0% plant, all five marks (0 of 20) | high is the one-sided 95% upper limit for that count |
| 19 | Replay 23 | forced flow | Failed (7/8 marks) | MEASURED | 5.00% | 21.61% | `research_rig/PREREG_23_ipo_fast_track.md`: no edge, all eight marks (1 of 20) | high is the one-sided 95% upper limit for that count |
| 20 | Replay 24 | carry | Failed (1/5 marks) | NOMINAL | 0.50% | 5.00% | `research_rig/PREREG_24_same_coin_carry.md`: above the 95th percentile of 500 twins | tail of the twin mark alone; not measured |
| 21 | Replay 25 | forced flow | PASSED (9/9 marks at 2 bps/side) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_25_treasury_month_end.md`: t marks (window t and Welch t) at 2 | one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| 22 | Replay 31 | forced flow | Failed (2/10 marks) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_31_bond_etf_month_end.md`: t marks at 2 | one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| 23 | Replay 33 | forced flow | Failed (3/11 marks, placement only) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_33_treasury_auctions.md`: t marks at 2 | one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| 24 | Replay 35 | forced flow | Failed (1/6 marks) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_35_ibit_cme_expiry.md`: t marks at 2 | one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| 25 | Replay 39 | calendar | Failed (5/7 marks) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_39_iwm_preholiday.md`: t marks at 2 | one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| 26 | Replay 41 | forced flow | Failed (4/8 marks) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_41_pension_month_end.md`: t mark at 2 | one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| 27 | TM01 | AI discretionary | Failed (0/6 beat BTC or twins) | NOMINAL | 10.00% | 73.79% | `timemachine/PLAN_TM01_crypto_price_only.md`: any of 6 models above BTC and above the 80th percentile of 20 twins | low: one model, models moving together, beating BTC a coin flip; high: twin mark alone, six independent models |
| 28 | TM02 | AI discretionary | Failed trading (0/6 beat BTC/twins) | NOMINAL | 10.00% | 73.79% | `timemachine/PLAN_TM02_crypto_with_news.md`: any of 6 models above BTC and above the 80th percentile of 20 twins | low: one model, models moving together, beating BTC a coin flip; high: twin mark alone, six independent models |
| 29 | TM03 | AI discretionary | Failed (0/6 above 90th pct) | NOMINAL | 3.00% | 11.43% | `timemachine/PLAN_TM03_bitcoin_dial.md` and `config/thresholds.yaml`: method needs 2 of 6 models above the 90th percentile and 5 of 6 above the middle | six independent no-skill models; low counts both method lines, high the percentile line alone |
| 30 | TM04 | AI discretionary | Failed (2/6 median, 0/6 90th pct) | NOMINAL | 3.00% | 11.43% | `timemachine/PLAN_TM04_stock_basket.md` and `config/thresholds.yaml`: method needs 2 of 6 models above the 90th percentile and 5 of 6 above the middle | six independent no-skill models; low counts both method lines, high the percentile line alone |
| 31 | TM06-P-g / TM06-R | AI discretionary | Mixed / did not repeat | NOMINAL | 0.10% | 10.00% | `timemachine/TM06R_addendum.md`: one model, three runs, each judged above the 90th percentile of its twins | low: all three runs clear by luck; high: one run clears |
| 32 | Measurement 15 | chart pattern | Failed fill gate (idea dropped) | STATED | 0.00% | 0.00% | `docs/research/66_measure_15_breakout_fills.md`: fill-cost gate, not a return mark | a cost measurement cannot produce a counted pass |
| 33 | TM06-P six models | AI discretionary | Shown by its marks, not counted pass | NOMINAL | 3.00% | 11.43% | `timemachine/PLAN_TM06_hot_coin_swing.md` and `config/thresholds.yaml`: method needs 2 of 6 models above the 90th percentile and 5 of 6 above the middle | six independent no-skill models; low counts both method lines, high the percentile line alone |
| 34 | TM06-S six models | AI discretionary | Failed (not shown, 0/6 clear both marks) | NOMINAL | 3.00% | 11.43% | `timemachine/PLAN_TM06_hot_coin_swing.md` and `config/thresholds.yaml`: method needs 2 of 6 models above the 90th percentile and 5 of 6 above the middle | six independent no-skill models; low counts both method lines, high the percentile line alone |
| 35 | Replay 21 | event | Did not pass (4 of 6 marks) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_21_odd_lot_tenders.md`: t mark at (its planted-0% calibration count is not on the repo) 2 | one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| 36 | Replay 46 Leg A | event | Did not pass (3 of 6 marks) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_46_cftc_altcoin_futures.md`: paired clustered t mark at 2 | one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| 37 | Replay 46 Leg B | event | Did not pass (5 of 6 marks) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_46_cftc_altcoin_futures.md`: paired clustered t mark at 2 | one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| 38 | Replay 48 | forced flow | Passed (7 of 7 marks) | MEASURED | 4.39% | 4.74% | `research_rig/CALIBRATION_48.json`: pass_rate.zero_edge = 0.0439 (439 of 10000) | high is the one-sided 95% upper limit for that count |
| 39 | Replay 52 | forced flow | Did not pass (0 of 6 marks) | MEASURED | 1.48% | 1.79% | `research_rig/CALIBRATION_52.json`: selected variant (breadth none, raw t False), scenarios.quarter_only.0.rate = 0.0148 (74 of 5000); high is its null_upper_wilson |  |
| 40 | Replay 53 | forced flow | Did not pass (5 of 7 marks) | MEASURED | 4.39% | 4.74% | `research_rig/CALIBRATION_53.json`: pass_rate.zero_edge = 0.0439 (439 of 10000) | file is identical to CALIBRATION_48.json (same seed and marks); high is the one-sided 95% upper limit for that count |
| 41 | Replay 60 | event | Did not pass (6 of 7 marks) | MEASURED | 0.00% | 1.44% | `research_rig/CALIBRATION_60.json`: cases.0.65 and cases.0.75 all_mark_passes at edge 0 = 0 and 8 of 1000 | two placement assumptions; high is the upper limit of the 0.75 case |
| 42 | Replay 62 | event | Did not pass (1 of 5 marks) | MEASURED for plan 61, STATED for 62 | 1.37% | 1.64% | `research_rig/POWER_61.json`: full.by_placement.0.8.counts.1.5.winsor_t at 0 bp (82 of 6000) | plan 62 reuses plan 61's power run (`research_rig/PREREG_62_special_dividend_ex_day_v2.md`); high is the one-sided 95% upper limit for that count |
| 43 | Replay 22 | momentum | Did not pass (1 of 5 marks) | MEASURED | 5.00% | 21.61% | `research_rig/calibration_22.json`: edges_pct.0.pass_share = 0.05 (1 of 20) | high is the one-sided 95% upper limit for that count |
| 44 | Replay 65 | forced flow | Did not pass (3 of 5 marks) | NOMINAL | 0.50% | 2.28% | `research_rig/PREREG_65_stock_bond_rebalance_spread.md`: clustered t mark at 2 | `research_rig/POWER_65.json` has no zero-edge row (lowest Sharpe 0.3), so no measured rate; one-sided normal tail of the t mark alone; not measured; the other marks can only lower it, fat tails or overlap can raise it |
| | Total, all 44 | | | | 0.68 | 4.13 | | |
| | Total, 34 trading tests that could give a counted pass | | | | 0.36 | 2.09 | | |

Results are copied from `docs/research/95_where_we_stand_after_32_tests.md`. Results pages are those cited there.

## How that compares with 3

- MEASURED and NOMINAL together: luck alone would give about 0.36 to 2.09 counted passes, so 3 is more than luck predicts even on the high figures.
- It is not far more. On the high figures 3 or more by luck happens 34.92% of the time. One of the three being luck is quite possible; all three being luck is unlikely.
- Three other results met their own marks and were not counted: Replay 13 Rule A (Relative marks met, not counted pass); TM06-P six models (Shown by its marks, not counted pass); TM06-P-g / TM06-R (Mixed / did not repeat). Counting every result that met its marks, {3 + len(met_marks)} of 44 cleared, against a luck figure of 0.68 to 4.13. Read that way the scoreboard is close to what luck gives.

## The three passes

### Replay 25, TLT over the last three sessions of the month

- No-edge pass rate: NOMINAL, 0.50% to 2.28%. No calibration was run for this plan; only the t marks give a figure.
- How far past its marks (MEASURED, `docs/research/69_replay_25_treasury_month_end.md`): window t 2.36 against 2.0, Welch t 2.56 against 2.0. The marks it cleared:

- At least 100 monthly windows | 130 | met
- Net mean above zero | +0.2562% | met
- Net window t at least 2.0 | 2.36 | met
- Net mean above zero after dropping the best three | +0.1904% | met
- Gross inside-minus-outside mean above zero and Welch t at least 2.0 | +0.1148 pp per day; Welch t 2.56 | met
- At least 60% of years have positive net means | 10 of 11 (90.9%) | met
- Net mean above zero from January 2020 | +0.1469% | met
- Net mean above zero omitting any single year | 11 of 11; lowest +0.2203% omitting 2019 | met
- At least 60% of years have a positive gross daily difference | 10 of 11 (90.9%) | met

- Relatives that did not pass (MEASURED): Replay 31: Failed (2/10 marks); Replay 33: Failed (3/11 marks, placement only); Replay 41: Failed (4/8 marks); Replay 52: Did not pass (0 of 6 marks); Replay 65: Did not pass (3 of 5 marks). Measurement 34 (TMF, UBT) used the same windows and is not new evidence; Replay 26 (2002 to 2015) was blocked at input validation and never scored. So 1 of 6 scored month-end and bond-flow tests passed.
- Overlap with the source sample (STATED, `docs/research/74_round_10_forced_flow_ideas.md`): Hartley and Schwarz cover 1990 to 2018 Treasuries, so 2016 to 2018 of the 2016 to 2026 window overlap; the rest does not.
- Forward log (STATED, `practice/traders/E01_tlt_month_end_close.md`): E01 records the same window each month from December 2026. MEASURED: no E01 record yet (forward logs on the repo: E07_log.json).
- Trust today: a modest pass with no measured null, sitting among 5 failed relatives, so treat it as a lead that E01 must confirm, not as a found edge.

### Replay 48, muni closed-end fund losers into January

- No-edge pass rate: MEASURED, 4.39% (upper 4.74%) from `research_rig/CALIBRATION_48.json`, set before the run.
- How far past its marks (MEASURED, `docs/research/103_replay_48_muni_cef_january.md`):

- Turns | all 10 turns scored | 10 of 10 | met
- Net mean | yearly portfolio mean above zero | +1.39% | met
- Positive years | at least 8 of 10 above zero | 8 of 10 | met
- Against MUB, mean | mean of portfolio minus MUB above zero | +1.30% | met
- Against MUB, years | at least 7 of 10 years ahead of MUB | 8 of 10 | met
- Without best year | mean above zero after removing the best 1 | +0.66% | met
- Loser effect | portfolio minus roster equal weight above zero, with documented cash and price only | +0.80% with cash, +0.79% price only | met

- Closest mark: positive years, 8 of 10 against a bar of at least 8 of 10; one losing year more and it would not have passed. Ten turns is a small sample.
- Relatives (MEASURED): Replay 53: Did not pass (5 of 7 marks). Its yearly results had a correlation of +0.802 with Replay 48 (`docs/research/122_replay_53_taxable_fund_january_rebound.md`), so it is a near copy that failed on breadth. Three more tax-loss relatives (preferreds, BDCs, Plan 54) were closed on power before prices.
- Overlap with the source sample (STATED, `research_rig/PREREG_48_muni_cef_tax_loss.md`): Turns 2016 to 2019 overlap the Carrion and Zhang sample; turns 2020 to 2025 do not overlap either paper.
- Forward log (STATED, `practice/traders/E04_muni_cef_january_watch.md`): E04, pretend entry Thu 2026-12-31, judged Fri 2027-01-29. MEASURED: no E04 record yet.
- Trust today: the best-founded of the three (a measured null near 4%, six of ten turns outside the paper), but ten turns at the edge of its breadth mark and a near copy that failed; one more January is the next real evidence.

### Replay 20, short after an Upbit listing red day

- No-edge pass rate: MEASURED, 0.00% measured (upper 13.91%) in `research_rig/PREREG_20_upbit_listing_short.md`.
- How far past its marks (MEASURED, `docs/research/71_replay_20_upbit_listing_short.md`): per-trade t 2.839 against 2.0. 2026 supplied 69% of the summed net returns.

- At least 30 judged trades | 139 | met
- Mean net return above zero | +3.2088% | met
- Mean net above the 95th percentile of control draws | +3.2088% versus +0.056% | met
- Positive mean without the best 3 trades | +2.537% | met
- Per-trade t at least 2.0 | 2.839 | met

- Relatives that did not pass (MEASURED): Replay 21: Did not pass (4 of 6 marks); Replay 46 Leg A: Did not pass (3 of 6 marks); Replay 46 Leg B: Did not pass (5 of 6 marks); Replay 60: Did not pass (6 of 7 marks); Replay 62: Did not pass (1 of 5 marks). Crypto short rules: Replay 17: Failed (0/3 marks).
- Overlap with the source (STATED, plan): "All dates have already been viewed." "The author selected the hold after viewing results and tried other variants." The source's own sample period is UNKNOWN on the repo. The window is wholly inside what the source author looked at.
- Forward log (STATED): no pretend-money log; the desk roster says "It does not place short sales" (`practice/traders/ROSTER.md`). Queue row 49: Upbit KRW listing forward watcher, live since 2026-11-26: polls Upbit notices and logs point-in-time US shortable overlap off repo; it logs listings, not returns.
- Trust today: least of the three; the null was low but the dates were already seen, the rule was picked by its author after viewing results, most of the gain is from one partial year, and there is no US-reachable forward check.

## Ideas closed before a return

MEASURED from `research_rig/TRIAL_LEDGER.md` and the Done section of `docs/QUEUE.md`, one count per idea (queue rows already in the ledger are not counted twice): 35 ideas closed before any return was computed.

- cost: 1
- count: 7
- coverage: 1
- feasibility: 4
- other, before prices: 6
- power: 13
- validation: 3

- ledger 163: research_rig/PREREG_26_treasury_month_end_early.md, closed on validation
- ledger 171: research_rig/PREREG_36_form4_cluster_buys.md, closed on coverage
- ledger 180: research_rig/PREREG_47_edgar_altcoin_treasuries.md, closed on count
- ledger 184: research_rig/PREREG_50_cef_liquidations.md, closed on count
- ledger 185: research_rig/PREREG_51_momentum_when_it_pays.md, closed on power
- ledger 189: research_rig/CLOSE_54_on_power.md, closed on power
- ledger 190: research_rig/CLOSE_ROWS_91_92_on_power.md, closed on power
- ledger 191: research_rig/CLOSE_ROWS_91_92_on_power.md, closed on power
- ledger 192: research_rig/CLOSE_55_on_power.md, closed on power
- ledger 193: research_rig/CLOSE_56_on_power.md, closed on power
- ledger 195: research_rig/AMENDMENT_43_BASIS.md, closed on validation
- ledger 196: research_rig/PREREG_58_btc_hour_of_day.md, closed on cost
- ledger 202: research_rig/COUNT_101_earnings_date_advancers.md, closed on count
- ledger 203: research_rig/PREREG_61_special_dividend_ex_day.md, closed on count
- ledger 209: research_rig/COUNT_107_dividend_month_coverage.md, closed on count
- ledger 210: research_rig/PREREG_66_third_friday_settlement.md, closed on power
- ledger 211: research_rig/PREREG_67_rsi2_pullback.md, closed on power
- ledger 213: research_rig/PREREG_68_earnings_drift_plain.md (screen page only; no plan was frozen), closed on other, before prices
- ledger 214: none yet (screen first; a plan only if it clears), closed on other, before prices
- ledger 215: none yet (screen first; plans only if a row clears), closed on other, before prices
- ledger 216: none yet (screen first; a plan only if it clears), closed on other, before prices
- queue 48: Plan 28, US-reachable Upbit listing short version: data scouting compl, closed on other, before prices
- queue 59: Plan 42, marketed non-overnight seasoned equity offerings, closed on feasibility
- queue 61: Blocked. Plan 37, US DoD daily contract awards: long-only, 3 to 5 trad, closed on other, before prices
- queue 62: Plan 38, going-private Schedule 13E-3 first filings, long-only post-an, closed on feasibility
- queue 74: Plan 43, declaration drift: `research_rig/PREREG_43_special_dividends., closed on validation
- queue 30: Dip entries against breakout entries for the AI crypto trader: the sam, closed on power
- queue 67: Overnight versus intraday return gap in SPY and QQQ, as a low-frequenc, closed on power
- queue 68: Option expiry week in SPY, closed on power
- queue 69: Municipal bond month-end index extension and June, July, December rein, closed on power
- queue 97: US corporate forward stock split announcements via SEC Form 8-K, closed on power
- queue 89: Count-first audit of going-private or going-dark reverse-split cash-ou, closed on count
- queue 79: Plan 45: retrospective test of Binance Monitoring Tags and Upbit/Bithu, closed on feasibility
- queue 80: Plan 44: buy Coinbase listing roadmap additions on another US spot ven, closed on feasibility
- queue (no number): Buy spot after a day of negative perpetual funding, closed on count

What that does to the reading:

- These ideas never had a chance to pass by luck, so they do not raise the luck figure. The denominator for luck is the scored tests, not every idea looked at.
- They were closed on count, power, cost or data checks, read without returns, so the closing did not pick winners by their results.
- Closing weak-power ideas early also means the scored tests were, on paper, ones that could detect a real edge. That raises the share of real effects among the passes a little, but no figure for it is measured.
- It does not remove the earlier choices that shaped each idea (which source, which window, which fund). Those are not counted anywhere and are UNKNOWN.

## What stays UNKNOWN

- The all-mark no-edge rate for every NOMINAL row; only the t or percentile mark was used.
- How correlated the month-end tests are with each other.
- Any forward month for E01 or E04; none has happened yet.
