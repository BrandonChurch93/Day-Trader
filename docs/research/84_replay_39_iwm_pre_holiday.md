# Replay 39. IWM before US market holidays

MEASURED. Replay 39 did not pass: **5 of 7 marks**. At 2 basis points per side, IWM averaged +0.1909% net on 102 pre-holiday sessions, with t 1.91. The gross difference versus other IWM sessions was positive but its Welch t was 1.82. Both t statistics fell short of their fixed 2.0 marks.

STATED. The [frozen plan](../../research_rig/PREREG_39_iwm_preholiday.md) bought IWM at the close two trading sessions before an official NYSE closure and sold at the next session's close, before the holiday. It used raw SIP closes and dated issuer cash payouts. The comparison with other IWM sessions is gross on both sides; the trading result is net. The saved run contains 11 early-close exits, not a separate strategy.

## Seven frozen marks

MEASURED. Each verdict below is the one saved by the scorer; all marks were required.

| Mark | Fixed bar | Measured | Verdict |
| --- | --- | ---: | --- |
| Completed events | At least 80 | 102 | Pass |
| Net IWM mean | Strictly above zero | +0.1909% | Pass |
| Net IWM one-sample t | At least 2.0 | 1.91 | Fail |
| Net mean after dropping the best three | Strictly above zero | +0.1034% | Pass |
| Net mean from January 2020 | Strictly above zero | +0.2183% (65 events) | Pass |
| Gross pre-holiday minus other-session mean | Strictly above zero and Welch t at least 2.0 | +0.1886%; Welch t 1.82 | Fail |
| Calendar years with a positive mean net return | At least 60% (7 of 11) | 8 of 11 | Pass |

## IWM by period and year

MEASURED. Returns are net at 2 basis points per side. The split uses exit date. The earlier block overlaps Ko and Yang's sample years; only the 2020 onward block is after their sample.

| Period | Events | Mean net | One-sample t |
| --- | ---: | ---: | ---: |
| All judged | 102 | +0.1909% | 1.91 |
| 2016–2019 | 37 | +0.1427% | 0.80 |
| 2020–October 2026 | 65 | +0.2183% | 1.81 |

| Exit year | Events | Mean net | One-sample t | Positive net mean |
| --- | ---: | ---: | ---: | --- |
| 2016 | 9 | +0.3622% | 1.11 | Yes |
| 2017 | 9 | -0.0576% | -0.27 | No |
| 2018 | 10 | -0.1964% | -0.37 | No |
| 2019 | 9 | +0.5003% | 2.42 | Yes |
| 2020 | 9 | +0.3646% | 0.66 | Yes |
| 2021 | 8 | -0.1046% | -0.32 | No |
| 2022 | 10 | +0.2251% | 0.64 | Yes |
| 2023 | 10 | +0.2334% | 0.83 | Yes |
| 2024 | 10 | +0.1385% | 0.65 | Yes |
| 2025 | 11 | +0.1233% | 0.68 | Yes |
| 2026 through October | 7 | +0.6315% | 1.99 | Yes |

## Gross daily comparison

MEASURED. Both groups are IWM close-to-close total returns, including cash payouts but before costs. The last row compares the two means using Welch's t.

| Session group | Intervals | Gross mean or gap | t |
| --- | ---: | ---: | ---: |
| Pre-holiday | 102 | +0.2310% | 2.31 |
| All other | 2,620 | +0.0423% | 1.51 |
| Pre-holiday minus all other | n/a | +0.1886% | 1.82 (Welch) |

## Shown only

MEASURED. Same event dates, no additional verdicts. SPY is a comparison, not a hedge or a pass mark.

| Fund | Cost per side | Events | Mean net | One-sample t |
| --- | ---: | ---: | ---: | ---: |
| IWM | 5 bps | 102 | +0.1308% | 1.31 |
| IWM | 10 bps | 102 | +0.0307% | 0.31 |
| SPY | 2 bps | 102 | +0.1104% | 1.43 |

## Reading and limits

A near miss stays a miss. The marks were fixed before the run and are not moved. The mean had the right sign in 8 of 11 years, but at 102 events the effect was too small against its noise to meet the two required t marks. At 10 bps per side the effect largely disappears: the mean is still slightly positive (+0.0307% per event), with t 0.31. This result does not support advancing the rule.

STATED. Limits recorded by the scorer:

- SIP daily close is a proxy for an executable close; per-side costs are fixed assumptions.
- The study's equal-weight CRSP index is not cap-weighted IWM.
- Conventional t statistics are descriptive; no serial-dependence correction. No cash yield or tax.

MEASURED. The saved result records the sole claim at 2026-11-26 04:55:55 UTC, approval commit `ae919413aca8384ccb3793a3f3f89306ab37d0b4`, and freeze commit `0e030222ab66f691e448110b6006e353712d4040`. The result SHA-256 is `53e67d9819a9fdfe66fe9a33ebe861f28113a6668ca4c36ea0a9eeba1c357aa9`. This report reads only that saved result; no replay or raw-bar calculation was repeated.
