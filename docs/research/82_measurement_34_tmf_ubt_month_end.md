# Measurement 34. TMF and UBT at Treasury month-end

MEASURED. TMF gross tracking 2.5853x vs 2.7x to 3.1x (fail); marked net mean +0.6483% (pass); marked worst window -8.7%. UBT shown only. The unlevered TLT gross mean was +0.2963% per window.

Reading: This uses the same 130 windows as [Replay 25](69_replay_25_treasury_month_end.md). It measures the cost and tracking of the same effect through leveraged funds, not a second piece of evidence. TMF's worst window was about -8.6% at fixed cost of 2 bp per side and -8.66% at the marked cost. The quoted spread is an estimate, not an observed fill.

## Gross tracking and frozen marks

| Fund | Gross mean per window | Gross mean / TLT gross mean | Frozen band | Tracking mark |
| --- | ---: | ---: | --- | --- |
| TMF | +0.7660% | 2.5853x | 2.7x to 3.1x | Fail |
| UBT | +0.5236% | 1.7673x | 1.8x to 2.1x | Informational only |

MEASURED. TMF's other mark, strictly positive mean at fixed 2 bp + half-spread per side: Pass (+0.6483%). UBT has no pass/fail marks.

## Closing-minute SIP half-spread

| Fund | Side | Endpoints | Mean, bp | Median, bp | P95, bp | Max, bp |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TMF | Entry | 130 | 3.652 | 2.876 | 8.146 | 12.092 |
| TMF | Exit | 130 | 4.041 | 3.490 | 9.770 | 14.327 |
| UBT | Entry | 130 | 10.186 | 7.282 | 26.861 | 78.983 |
| UBT | Exit | 130 | 11.369 | 7.981 | 27.246 | 122.278 |

MEASURED. Multiple raw rows at the final timestamp: TMF 20 of 260; UBT 13 of 260. The frozen policy is a conservative tied-endpoint estimate: maximum half spread at the final timestamp. It validates every row in the final-timestamp group and ignores vendor row order.

## Net cost comparisons

Costs are per side; trimmed means drop the three best windows. Fixed-cost ratios use TLT at the same fixed cost; quote-cost ratios use TLT at fixed 2 bp per side, so the costs differ. Drawdown is from the rule's own equity on daily closes, including inside held windows. The last calendar year is partial.

### TMF

| Cost per side | Mean net | t | Trimmed mean | Worst window (entry to exit) | Worst compounded year | Worst mean year | Positive mean years | Net ratio vs TLT | Max drawdown (peak to trough) |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |
| Fixed 2 bp | +0.7257% | 2.233 | +0.5244% | -8.63% (2024-06-25 to 2024-06-28) | 2026 (-15.36%) | 2026 (-1.60%) | 10 of 11 | 2.8328x | 24.86% (2025-08-28 to 2026-10-28) |
| Half-spread only | +0.6886% | 2.119 | +0.4869% | -8.62% (2024-06-25 to 2024-06-28) | 2026 (-15.52%) | 2026 (-1.62%) | 10 of 11 | 2.6878x | 25.02% (2025-08-28 to 2026-10-28) |
| Fixed 2 bp + half-spread | +0.6483% | 1.996 | +0.4467% | -8.66% (2024-06-25 to 2024-06-28) | 2026 (-15.85%) | 2026 (-1.66%) | 10 of 11 | 2.5306x | 25.44% (2025-08-28 to 2026-10-28) |
| Fixed 5 bp | +0.6653% | 2.049 | +0.4641% | -8.69% (2024-06-25 to 2024-06-28) | 2026 (-15.86%) | 2026 (-1.66%) | 10 of 11 | 3.3935x | 25.49% (2025-08-28 to 2026-10-28) |
| Fixed 10 bp | +0.5647% | 1.741 | +0.3637% | -8.78% (2024-06-25 to 2024-06-28) | 2026 (-16.70%) | 2026 (-1.76%) | 10 of 11 | 5.8880x | 26.57% (2025-07-29 to 2026-10-28) |

Annual net mean / compounded return by cost:

| Exit year | Windows | Fixed 2 bp | Half-spread only | Fixed 2 bp + half-spread | Fixed 5 bp | Fixed 10 bp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | 12 | +1.23% / +15.24% | +1.19% / +14.72% | +1.15% / +14.17% | +1.17% / +14.41% | +1.07% / +13.05% |
| 2017 | 12 | +0.60% / +6.77% | +0.55% / +6.21% | +0.51% / +5.70% | +0.54% / +6.00% | +0.43% / +4.74% |
| 2018 | 12 | +1.54% / +19.65% | +1.50% / +19.15% | +1.46% / +18.58% | +1.48% / +18.79% | +1.38% / +17.37% |
| 2019 | 12 | +1.79% / +22.87% | +1.76% / +22.32% | +1.72% / +21.73% | +1.73% / +21.98% | +1.63% / +20.53% |
| 2020 | 12 | +0.58% / +6.36% | +0.55% / +5.89% | +0.51% / +5.38% | +0.52% / +5.59% | +0.42% / +4.33% |
| 2021 | 12 | +0.84% / +9.58% | +0.81% / +9.24% | +0.77% / +8.72% | +0.78% / +8.79% | +0.68% / +7.49% |
| 2022 | 12 | +0.42% / +3.53% | +0.34% / +2.54% | +0.30% / +2.05% | +0.36% / +2.79% | +0.26% / +1.57% |
| 2023 | 12 | +0.32% / +3.22% | +0.22% / +1.98% | +0.18% / +1.49% | +0.26% / +2.48% | +0.16% / +1.26% |
| 2024 | 12 | +1.09% / +12.59% | +1.10% / +12.76% | +1.06% / +12.22% | +1.03% / +11.78% | +0.93% / +10.44% |
| 2025 | 12 | +0.78% / +9.27% | +0.78% / +9.27% | +0.74% / +8.75% | +0.72% / +8.49% | +0.62% / +7.20% |
| 2026 | 10 | -1.60% / -15.36% | -1.62% / -15.52% | -1.66% / -15.85% | -1.66% / -15.86% | -1.76% / -16.70% |

### UBT

| Cost per side | Mean net | t | Trimmed mean | Worst window (entry to exit) | Worst compounded year | Worst mean year | Positive mean years | Net ratio vs TLT | Max drawdown (peak to trough) |
| --- | ---: | ---: | ---: | --- | --- | --- | ---: | ---: | --- |
| Fixed 2 bp | +0.4834% | 2.215 | +0.3500% | -6.04% (2024-06-25 to 2024-06-28) | 2026 (-11.60%) | 2026 (-1.20%) | 10 of 11 | 1.8871x | 19.40% (2025-07-29 to 2026-10-28) |
| Half-spread only | +0.3072% | 1.409 | +0.1711% | -6.29% (2024-06-25 to 2024-06-28) | 2026 (-13.78%) | 2026 (-1.45%) | 10 of 11 | 1.1992x | 22.39% (2025-07-29 to 2026-10-28) |
| Fixed 2 bp + half-spread | +0.2671% | 1.225 | +0.1311% | -6.32% (2024-06-25 to 2024-06-28) | 2026 (-14.12%) | 2026 (-1.49%) | 8 of 11 | 1.0426x | 22.85% (2025-07-29 to 2026-10-28) |
| Fixed 5 bp | +0.4232% | 1.940 | +0.2898% | -6.09% (2024-06-25 to 2024-06-28) | 2026 (-12.12%) | 2026 (-1.26%) | 10 of 11 | 2.1585x | 20.12% (2025-07-29 to 2026-10-28) |
| Fixed 10 bp | +0.3228% | 1.481 | +0.1896% | -6.19% (2024-06-25 to 2024-06-28) | 2026 (-13.00%) | 2026 (-1.36%) | 10 of 11 | 3.3659x | 21.31% (2025-07-29 to 2026-10-28) |

Annual net mean / compounded return by cost:

| Exit year | Windows | Fixed 2 bp | Half-spread only | Fixed 2 bp + half-spread | Fixed 5 bp | Fixed 10 bp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | 12 | +0.90% / +11.12% | +0.53% / +6.30% | +0.49% / +5.79% | +0.84% / +10.32% | +0.74% / +9.01% |
| 2017 | 12 | +0.59% / +7.01% | +0.41% / +4.71% | +0.37% / +4.21% | +0.53% / +6.24% | +0.43% / +4.98% |
| 2018 | 12 | +1.08% / +13.61% | +1.05% / +13.12% | +1.01% / +12.58% | +1.02% / +12.79% | +0.92% / +11.45% |
| 2019 | 12 | +1.23% / +15.39% | +1.21% / +15.19% | +1.17% / +14.64% | +1.17% / +14.56% | +1.07% / +13.19% |
| 2020 | 12 | +0.52% / +6.01% | +0.31% / +3.40% | +0.27% / +2.91% | +0.46% / +5.25% | +0.36% / +3.99% |
| 2021 | 12 | +0.59% / +6.90% | +0.54% / +6.23% | +0.50% / +5.72% | +0.53% / +6.14% | +0.43% / +4.87% |
| 2022 | 12 | +0.18% / +1.44% | +0.07% / +0.14% | +0.03% / -0.33% | +0.12% / +0.71% | +0.02% / -0.49% |
| 2023 | 12 | +0.18% / +1.81% | +0.00% / -0.31% | -0.04% / -0.79% | +0.12% / +1.08% | +0.02% / -0.13% |
| 2024 | 12 | +0.64% / +7.40% | +0.42% / +4.62% | +0.38% / +4.12% | +0.58% / +6.63% | +0.48% / +5.36% |
| 2025 | 12 | +0.34% / +3.88% | +0.00% / -0.18% | -0.04% / -0.66% | +0.28% / +3.13% | +0.18% / +1.90% |
| 2026 | 10 | -1.20% / -11.60% | -1.45% / -13.78% | -1.49% / -14.12% | -1.26% / -12.12% | -1.36% / -13.00% |

## Run and custody

MEASURED. The lead ran the [refrozen measurement](../../research_rig/MEASURE_34_tmf_month_end.md) once at 2026-11-26 04:51:41 UTC from commit `90d8877d1cc37a20f10d19c790418787fc8924d5` under a 600 MB address-space cap (`ulimit -v 600000`). The run is locked; do not rerun it.

MEASURED. The second-source payout and split review passed before the run. The off-repo payout review (PAYOUT_REVIEW.md) is pinned at SHA-256 `e04e0c61a7fe10c4348d6b3fc47012ff2eebd8059f73c41283791528dbf82dd2`. This page was generated only from the saved aggregate result; no market payload was opened.

- Result SHA-256: `b0c574ae97c085a962523909ec8ff6a78013b447f69c5bf0336ab15936803a63`
- Freeze SHA-256: `e68946c97b172368a5dc67d3761c1a997e809784ed8ead7837a6832948ec13a9`
- Input manifest SHA-256: `d79137b683c7c558357396ed2ab8897bf91e8b46b65dfa73204bf19a3d75f252`
- Replay 25 TLT manifest SHA-256: `43f92b5249c8a2aa8778139f928cf643814e47b778d5892a903227830777aa9a`
