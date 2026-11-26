# Replay 41. Switching to the month-end laggard

MEASURED. The laggard switch did not pass: **4 of 8 frozen marks**. The rule averaged +0.2357% net per window (t 2.29) but added only +0.0148% (t 0.14) over always holding TLT in the same 130 windows. The paired mean was -0.0676% from 2020 and -0.0810% without the best three months.

STATED. The [frozen rule](../../research_rig/PREREG_41_pension_month_end.md) used raw SIP closes and issuer cash distributions. It chose the worse-performing ETF (SPY or TLT) by month-to-date total return at the fifth-last NYSE session's close, bought at the fourth-last close, and sold at the last close. Each month reset to $500, sized in whole shares. The judged cost was 2 basis points per side. The January 2016 signal starts at the first session's close; subsequent months start at the previous month-end.

## Frozen marks

MEASURED. Paired means the rule minus always-TLT with the same window, budget and fee convention. All marks were required, and zero is not positive.

| Fixed bar | Measured | Verdict |
| --- | ---: | --- |
| At least 100 judged months | 130 | met |
| Paired mean above zero | +0.0148% | met |
| Paired t at least 2.0 | 0.14 | not met |
| Paired mean above zero after dropping the best three months | -0.0810% | not met |
| Positive paired annual mean in at least 7 of 11 years | 6 of 11 | not met |
| Paired mean above zero from January 2020 | -0.0676% | not met |
| Conditional rule's own net mean above zero | +0.2357% | met |
| Net laggard minus winner mean above zero | +0.1456% | met |

## Net returns at the judged cost

MEASURED. The always-TLT return is shown for context and supplies the judged subtraction; its standalone return, like always-SPY, has no separate pass mark. Laggard minus winner compares two separately sized long-only arms; it is not a short trade.

| Comparison | Months | Mean net per window | t |
| --- | ---: | ---: | ---: |
| Conditional rule | 130 | +0.2357% | 2.29 |
| Always TLT (benchmark level, shown only) | 130 | +0.2209% | 2.29 |
| Always SPY (shown only) | 130 | +0.1049% | 1.06 |
| Conditional minus always TLT (judged) | 130 | +0.0148% | 0.14 |
| Paired, without best three | 127 | -0.0810% | -0.89 |
| Paired, January 2020 through October 2026 | 82 | -0.0676% | -0.46 |
| Laggard minus winner (judged sign) | 130 | +0.1456% | 1.00 |

MEASURED. The signal selected TLT in 87 months, SPY in 43, and cash on 0 signal ties. In 12 SPY-selected months, even one share plus the buy fee did not fit. STATED. The frozen rule held idle cash with zero return, did not substitute TLT or use fractional shares, and kept these months in the paired comparison. Selecting TLT contributed a zero paired difference by construction.

## Paired result by calendar year

MEASURED. The year is assigned by the month-end exit. The 2026 row ends in October.

| Year | Months | Mean net difference | t |
| --- | ---: | ---: | ---: |
| 2016 | 12 | +0.4156% | 1.22 |
| 2017 | 12 | +0.2432% | 1.21 |
| 2018 | 12 | +0.1562% | 0.55 |
| 2019 | 12 | -0.1932% | -0.70 |
| 2020 | 12 | -0.6583% | -1.15 |
| 2021 | 12 | -0.2153% | -1.47 |
| 2022 | 12 | +0.2553% | 0.36 |
| 2023 | 12 | +0.1081% | 0.98 |
| 2024 | 12 | +0.1886% | 0.61 |
| 2025 | 12 | -0.1291% | -0.55 |
| 2026 | 10 | -0.0132% | -0.09 |

## Cost sensitivity

MEASURED. Same windows, with whole shares recalculated for each entry cost. Only 2 basis points per side were judged; 5 and 10 are shown only.

| Basis points per side | Use | Rule mean | Rule t | Paired mean | Paired t | Laggard minus winner mean | Laggard minus winner t |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | judged | +0.2357% | 2.29 | +0.0148% | 0.14 | +0.1456% | 1.00 |
| 5 | shown only | +0.1906% | 1.86 | +0.0237% | 0.22 | +0.1433% | 0.99 |
| 10 | shown only | +0.1133% | 1.10 | +0.0350% | 0.33 | +0.1337% | 0.92 |

## Shown only at 2 basis points per side

MEASURED. SPY groups use the signal, not whether a share could be bought. The fixed mix averages two independently sized benchmark sleeves; the mirror picks the winner. The next-session spread uses the winner minus laggard from the prior signal; October 2026 has no next session in scope.

| Comparison | Months | Mean net per window | t |
| --- | ---: | ---: | ---: |
| SPY in SPY-selected months | 43 | +0.3451% | 1.57 |
| SPY in other months | 87 | -0.0139% | -0.14 |
| Fixed 50/50 mix | 130 | +0.1629% | 2.49 |
| Conditional minus fixed mix | 130 | +0.0728% | 1.00 |
| Mirror (choose winner) | 130 | +0.0901% | 0.98 |
| Paired without January 2016 | 129 | +0.0096% | 0.09 |
| Next-session winner minus laggard | 129 | +0.2021% | 1.94 |

## What this adds

MEASURED. Nearly all of the conditional rule's pooled net gain was present in always-TLT (+0.2209% versus +0.2357%). STATED. The practical reading is that the rule mostly held TLT at month-end, the same 130 windows as [Replay 25](69_replay_25_treasury_month_end.md), with a different whole-share budget denominator. It does not establish a second effect or a reason to switch.

STATED. [Harvey, Mazzoleni and Melone, NBER Working Paper 33554, January 2026 revision](https://www.nber.org/system/files/working_papers/w33554/w33554.pdf) simulate a monthly 60/40 reset and use the resulting stock/bond weight drift to predict next-day futures returns in the final five sessions, strongest in the last four. Their strategy uses long and short futures, including ten-year Treasury futures, and a separate reversal signal. This replay instead fixes a fifth-last close ETF signal and holds one long-only ETF at a time for three close-to-close intervals, with long-duration TLT rather than a ten-year futures leg. It tests the predicted direction in a retail-sized proxy, not their exact strategy and not who traded. T-statistics are descriptive and unadjusted for serial dependence or prior related tests. UNKNOWN. Whether a real close order could get these fills.

## Run record

MEASURED. The saved result records the claim at 2026-11-26 05:33:58 UTC for queue 54 and ledger 176. STATED. The lead agent reports one scored run after counts-only validation. This report reads the saved result only; there was no rerun and the lock stays.

- Approval commit `0c62505118bd8689848f92ca143ac207bde3dec4`
- Strategy freeze commit `2dd8dd9a0f093d383cb6fc4b60624ea55206e63b`
- Saved result SHA-256 `509f68fdac4088d6c10e0a8674990804a561c8e0313c7a4610d0481f85487bea`
- Freeze manifest SHA-256 `9bcbe028b644c8a70ccbf22e904d1b7fbbb42ce9d0a0b78723c1ffef4bf27ecb`
- Input manifest SHA-256 `39f96aaa63b71ed771e2caa793969544a4ba79b64a57b2ad723ab7f15035aa15`
- Cash-action packet SHA-256 `e694a551c3a5455edb89a08b26c9b074a3a1556230d0ad7415fba175655f99e6`
