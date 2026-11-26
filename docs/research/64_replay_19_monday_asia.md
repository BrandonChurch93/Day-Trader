# Replay 19: the Monday Asia window

MEASURED. The equal-weight bitcoin and ether rule **did not pass**. It met **1 of 5 marks** at 5 bps per side. The account returned -53.88% net, with a Sharpe of -0.280.

STATED. [Concretum Group](https://concretumgroup.com/seasonality-in-bitcoin-intraday-trend-trading/) describes an approximate window for its private trend benchmark but gives no entry, exit or directional signal. This replay uses our stand-in and does not test their models. All dates were already viewed, 2020-01-01 through the 2026-10-31 UTC close. There is no held-back period.

STATED. The local [frozen plan](../../research_rig/PREREG_19_monday_asia.md) commit and [ledger row 155](../../research_rig/TRIAL_LEDGER.md) were in place before the run at 2026-11-26 01:24 UTC. GitHub pushes were refused before the run, so the public GitHub timestamp is necessarily after the run, not evidence of a public freeze beforehand.

MEASURED. The first invocation stopped before the lock on a zero-volume trade candle. It never scored a book or consumed the run. The dated amendment in the [frozen plan](../../research_rig/PREREG_19_monday_asia.md) let zero-volume candles mark the value of an open position, but kept them out of the judged signal, entry and exit. Opens and closes still had to be finite and positive, and trade volume finite and nonnegative.

## Preregistered marks

STATED. At Sunday 19:00 New York time, compare the last fully closed candle with the close 24 hours earlier. Go long if it rose, short if it fell, and stay flat on a tie. Fill at the next hourly open and exit 24 hours later. The pair starts each window in equal parts, with no leverage at entry.

| Mark | Measured | Verdict |
|---|---:|---|
| Net Sharpe of at least 1.0 | -0.280 | not met |
| Positive in at least 4 full years | 1 of 6, 2022 | not met |
| Positive after the CME cutoff | -10.06% | not met |
| Above the 95th percentile of shifted windows | -0.280 vs. +0.403 | not met |
| Trade at least 90% of windows overall and after the cut | 356 of 356 overall; 22 of 22 after | met |

MEASURED. The rule ranked **95th of 168 start hours**, best to worst. Of the 167 defined shifted Sharpes, 94 were higher and 0 tied. No shifted book failed or had an undefined Sharpe. The shifted windows overlap, so the rank is not a significance test.

## Year by year

MEASURED. The pair's net returns below use 5 bps per side and include funding. The last year is partial.

| Year | Net return |
|---|---:|
| 2020 | -5.44% |
| 2021 | -26.58% |
| 2022 | +12.41% |
| 2023 | -3.37% |
| 2024 | -2.12% |
| 2025 | -17.02% |
| 2026, partial | -24.69% |

MEASURED. The pair's largest fall was 60.24%. In percentage points of starting equity, price changes contributed -26.23, funding -1.57 and fees -26.08. The loss was not just fees.

MEASURED. The pair returned -48.72% before the split (Sharpe -0.233) and -10.06% after it (Sharpe -2.040). The split is 2026-05-29 21:00 UTC, as scheduled in the [CME Globex notice](https://www.cmegroup.com/notices/electronic-trading/2026/05/20260511.html). The later period covers only 22 scheduled windows and does not show that the CME change caused the loss.

## Shown only

MEASURED. The comparisons below are not extra marks. The [cheaper fee](60_us_venue_costs_checked.md) is a sensitivity, not evidence of a real fill at that price.

| Variant | Net return | Sharpe | Net after the CME cut |
|---|---:|---:|---:|
| Bitcoin alone, 5 bps per side | -45.86% | -0.199 | -17.02% |
| Ether alone, 5 bps per side | -65.57% | -0.294 | -2.93% |
| Pair 24-hour momentum, 1 bp per side | -38.62% | -0.126 | -8.45% |
| Pair 24-hour momentum, 10 bps per side | -67.73% | -0.472 | -12.02% |
| One-candle direction, 5 bps per side | +125.79% | +0.573 | -0.81% |
| Always long in the window, 5 bps per side | +106.91% | +0.514 | +2.97% |

MEASURED. Price changes added to both coins' always-long books. The plain reading is that always-long gained because bitcoin and ether rose during its holds over this period, not that Monday has an edge. The replay did not test whether always-long in this window beat holding continuously or taking the same long exposure at other hours.

## Zero-volume candles

- BTCUSDT: 1 at 2024-10-28 20:00 UTC.
- ETHUSDT: 1 at 2024-10-28 20:00 UTC.

MEASURED. None supplied a judged signal or fill. The shifted windows touched one in 4 cases: 2 as a signal, 1 at entry and 1 at exit.

## Made-up arithmetic check

MEASURED on invented bars before the run. The [frozen plan](../../research_rig/PREREG_19_monday_asia.md) records these joint passes out of 20 seeds at each planted gross edge:

| Gross plant per trade | Seeds clearing all marks |
|---|---:|
| 0 bps | 0 of 20 |
| 10 bps | 0 of 20 |
| 20 bps | 3 of 20 |
| 40 bps | 19 of 20 |

STATED. Under this invented noise, the marks usually caught the 40 bps edge and seldom caught the 20 bps edge. This is an arithmetic guide, not a power estimate or a minimum detectable edge for real prices.

UNKNOWN. This all-viewed replay does not establish a live fill or a repeatable window edge. The [saved result](../../research_rig/results_19.json) is bound to local commit `54c20f72e5617f3332f37d8a3a675d121eefb0e3`, the ledger and the archive manifest. Its SHA-256 is `527c5c3bbb948945e5f9de09cebf054a279e34edc62a61bb0d1f2addeefba45d`. The [report script](../../research_rig/report_19.py) reads only the saved result.
