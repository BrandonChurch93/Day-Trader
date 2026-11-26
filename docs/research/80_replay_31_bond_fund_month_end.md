# Replay 31. Bond funds at month-end

MEASURED. Replay 31 did not pass: **2 of 10 marks**. The four-fund basket rose +0.1268% net per window at 2 basis points per side (t 3.09), but after subtracting its modeled Treasury and stock exposures, the average was -0.0338% (t -1.69) across 126 months.

STATED. The [frozen rule](../../research_rig/PREREG_31_bond_etf_month_end.md) put equal dollars in LQD, HYG, MBB and TIP from the fourth-last New York trading session's close to the last close. It used raw SIP closes and issuer payouts. Earlier days outside the window set each month's two slopes: IEF for LQD, MBB and TIP, IEI for HYG, and SPY for all four. The residual subtracts the contemporaneous gross benchmark returns scaled by those slopes; the benchmark legs were not traded.

## Ten frozen marks

| Mark | Measured | Verdict |
| --- | ---: | --- |
| At least 100 judged months | 126 | met |
| Mean net residual above zero | -0.0338% | not met |
| Monthly residual t at least 2.0 | -1.69 | not met |
| Residual mean above zero without the best three months | -0.0485% | not met |
| Daily residual gap above zero and Welch t at least 2.0 | +0.0064% per day; t 0.87 | not met |
| At least 7 years with positive mean monthly residuals | 4 of 11 | not met |
| Mean monthly residual above zero from January 2020 | -0.0493% | not met |
| Mean residual above zero after each single-year omission | 0 of 11 | not met |
| At least 7 years with a positive daily residual gap | 5 of 11 | not met |
| Plain long-only net mean above zero | +0.1268% | met |

MEASURED. The pooled gross daily residual averaged +0.0020% inside the window (378 intervals) and -0.0043% outside (2,263 intervals). The difference was +0.0064% per day, with Welch t 0.87.

## Cost and fund breakdown

MEASURED. All rows use the same judged months. Costs apply to the actual long funds only. The 5 and 10 basis point cases and all individual fund rows are shown without verdicts.

| Bps per side | Fund | Plain net mean | Plain t | Residual net mean | Residual t |
| ---: | --- | ---: | ---: | ---: | ---: |
| 2 | Equal-weight pool | +0.1268% | 3.09 | -0.0338% | -1.69 |
| 2 | LQD | +0.1448% | 2.52 | -0.0865% | -2.80 |
| 2 | HYG | +0.0982% | 1.61 | -0.0302% | -0.71 |
| 2 | MBB | +0.1244% | 3.19 | +0.0085% | 0.46 |
| 2 | TIP | +0.1397% | 2.90 | -0.0269% | -0.71 |
| 5 | Equal-weight pool | +0.0667% | 1.63 | -0.0938% | -4.70 |
| 5 | LQD | +0.0847% | 1.48 | -0.1466% | -4.74 |
| 5 | HYG | +0.0382% | 0.63 | -0.0902% | -2.12 |
| 5 | MBB | +0.0644% | 1.65 | -0.0516% | -2.79 |
| 5 | TIP | +0.0796% | 1.65 | -0.0870% | -2.30 |
| 10 | Equal-weight pool | -0.0333% | -0.81 | -0.1939% | -9.72 |
| 10 | LQD | -0.0153% | -0.27 | -0.2466% | -7.98 |
| 10 | HYG | -0.0618% | -1.02 | -0.1902% | -4.47 |
| 10 | MBB | -0.0357% | -0.92 | -0.1516% | -8.21 |
| 10 | TIP | -0.0204% | -0.42 | -0.1870% | -4.94 |

MEASURED. LQD's residual was -0.0865% at 2 basis points per side (t -2.80). That is an observation from a shown-only row, not a finding about LQD or a separately tested short trade.

## By year

MEASURED. Residuals use 2 basis points per side for the monthly columns; the daily comparison is gross. The 2016 and 2026 rows cover only May to December and January to October, respectively.

| Year | Months | Monthly residual | Monthly t | Inside n | Inside mean | Outside n | Outside mean | Daily gap | Welch t |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | 8 | +0.0860% | 1.13 | 24 | +0.0422% | 146 | +0.0029% | +0.0393% | 1.74 |
| 2017 | 12 | +0.0205% | 0.59 | 36 | +0.0202% | 215 | -0.0075% | +0.0277% | 2.50 |
| 2018 | 12 | -0.0675% | -0.97 | 36 | -0.0094% | 215 | -0.0069% | -0.0025% | -0.12 |
| 2019 | 12 | -0.0279% | -0.50 | 36 | +0.0041% | 216 | +0.0103% | -0.0062% | -0.41 |
| 2020 | 12 | +0.0102% | 0.15 | 36 | +0.0163% | 217 | -0.0188% | +0.0350% | 0.85 |
| 2021 | 12 | +0.0962% | 1.10 | 36 | +0.0456% | 216 | -0.0161% | +0.0617% | 2.60 |
| 2022 | 12 | -0.1654% | -2.39 | 36 | -0.0414% | 215 | +0.0039% | -0.0454% | -1.53 |
| 2023 | 12 | -0.0701% | -0.98 | 36 | -0.0101% | 214 | +0.0008% | -0.0108% | -0.47 |
| 2024 | 12 | -0.0155% | -0.27 | 36 | +0.0081% | 216 | -0.0084% | +0.0166% | 0.86 |
| 2025 | 12 | -0.0972% | -1.60 | 36 | -0.0191% | 214 | -0.0016% | -0.0175% | -0.86 |
| 2026 | 10 | -0.1143% | -3.00 | 30 | -0.0253% | 179 | -0.0037% | -0.0216% | -0.99 |

## Leaving out one year at a time

MEASURED. These subsets overlap; they are not independent tests. This mark checks the mean, not the t-statistic.

| Omitted year | Months left | Mean residual | t |
| --- | ---: | ---: | ---: |
| 2016 | 118 | -0.0419% | -2.04 |
| 2017 | 114 | -0.0395% | -1.82 |
| 2018 | 114 | -0.0302% | -1.45 |
| 2019 | 114 | -0.0344% | -1.61 |
| 2020 | 114 | -0.0384% | -1.84 |
| 2021 | 114 | -0.0475% | -2.40 |
| 2022 | 114 | -0.0199% | -0.97 |
| 2023 | 114 | -0.0300% | -1.44 |
| 2024 | 114 | -0.0357% | -1.68 |
| 2025 | 114 | -0.0271% | -1.28 |
| 2026 | 116 | -0.0268% | -1.26 |

## Beta ranges and warm-up

MEASURED. Ranges are from the judged months only. Each beta was fitted on earlier out-of-window days, not selected to improve the month-end result.

| Fund | Treasury ETF | Treasury beta range | SPY beta range |
| --- | --- | ---: | ---: |
| LQD | IEF | 0.746 to 1.002 | 0.069 to 0.275 |
| HYG | IEI | -0.093 to 0.523 | 0.351 to 0.555 |
| MBB | IEF | 0.233 to 0.684 | 0.009 to 0.088 |
| TIP | IEF | 0.680 to 0.854 | 0.052 to 0.134 |

MEASURED. The four warm-up months were shown at 2 basis points per side, not judged. They were also excluded from the daily comparison.

| Warm-up month | Fit intervals | Plain net | Residual net |
| --- | ---: | ---: | ---: |
| 2016-01 | 14 | +0.5144% | -0.1324% |
| 2016-02 | 15 | +0.8103% | +0.8199% |
| 2016-03 | 32 | +0.7804% | +0.1725% |
| 2016-04 | 51 | +0.6508% | +0.4712% |

## Reading and limits

MEASURED. The long-only bond funds rose into month-end in this sample. There was no positive average left after the Treasury and stock benchmarks, and the daily comparison did not meet its mark. STATED. This looks like the month-end rise seen in [Replay 25](69_replay_25_treasury_month_end.md) showing up in other bond funds, not evidence of a second effect. This test cannot say how much of the rise came from Treasuries versus stocks or prove that a smaller separate effect is absent.

STATED. The window was borrowed from Replay 25 and only 126 months were judged. The adjustment uses one Treasury ETF and one stock ETF per fund; it does not remove every yield-curve, credit, inflation or mortgage risk. The t-statistics are descriptive and do not adjust for serial dependence. The SIP close and fixed fees are not a live-fill test. UNKNOWN. What a retail order would have earned.

## Run record

MEASURED. The pinned result records a claim at 2026-11-26 04:44:34 UTC with ledger 166 and queue 50. STATED. The lead agent reports one scored run after counts-only validation and the independent issuer payout review. This page reads the saved result only.

- Approval commit `d39ca6867bcb68806d5b22a326be4a376bdb873d`
- Strategy freeze commit `c42056742fa407c3081f2f6076cdd9320faef339`
- Saved result SHA-256 `42133558d711352ce132a496924b1b9b01d781d765d8ce9a38c11e19a89daca2`
- Freeze manifest SHA-256 `044e36030d588daa0612440cc298a82450848e91279188975d699135d11d253b`
- Input manifest SHA-256 `6d84b4e8e39218117ec10682047feefd21a9c6ef9a857c07db1e87c12de76f0b`
- Cash-action packet SHA-256 `2cd82c88e967cf76026215a451c6da07fa5285bbceef7bab0281d95d90fbed6e`
- Independent payout review SHA-256 `c8fea227114a2e22832333994a86c6db853eb7c87261dc47734407cae8c5b868`
