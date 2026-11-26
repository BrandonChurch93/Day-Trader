# Replay 25. Treasury ETF month-end window

MEASURED. The unlevered TLT rule passed **9 of 9 marks** at 2 basis points per side. It averaged +0.2562% net over 130 monthly windows, with a t-statistic of 2.36. This is the first counted trading-replay pass in this project, not a result from live trading.

STATED. The [frozen plan](../../research_rig/PREREG_25_treasury_month_end.md) buys at the fourth-last session's close, sells at the last session's close, and otherwise holds cash with no yield. January 2016 through October 2026 is judged; the November extension supplies a shown comparison only. The run used raw SIP daily bars and dated issuer cash distributions, not adjusted closes.

## Nine judged marks

| Mark | Measured | Verdict |
| --- | ---: | --- |
| At least 100 monthly windows | 130 | met |
| Net mean above zero | +0.2562% | met |
| Net window t at least 2.0 | 2.36 | met |
| Net mean above zero after dropping the best three | +0.1904% | met |
| Gross inside-minus-outside mean above zero and Welch t at least 2.0 | +0.1148 pp per day; Welch t 2.56 | met |
| At least 60% of years have positive net means | 10 of 11 (90.9%) | met |
| Net mean above zero from January 2020 | +0.1469% | met |
| Net mean above zero omitting any single year | 11 of 11; lowest +0.2203% omitting 2019 | met |
| At least 60% of years have a positive gross daily difference | 10 of 11 (90.9%) | met |

MEASURED. Gross daily means were +0.0993% across 390 inside intervals and -0.0155% across 2,332 outside intervals. These daily comparisons do not subtract strategy fees.

## Calendar years

MEASURED. Net means and window t-statistics use the judged strategy and cost. The daily columns are gross. The final year covers only January through October.

| Year | Windows | Net mean | Window t | Inside n | Inside mean | Outside n | Outside mean | Daily gap | Welch t |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | 12 | +0.4424% | 1.64 | 36 | +0.1616% | 215 | -0.0211% | +0.1827 pp | 1.43 |
| 2017 | 12 | +0.2119% | 0.68 | 36 | +0.0838% | 215 | +0.0290% | +0.0548 pp | 0.51 |
| 2018 | 12 | +0.5078% | 1.96 | 36 | +0.1828% | 215 | -0.0362% | +0.2190 pp | 2.05 |
| 2019 | 12 | +0.6093% | 1.70 | 36 | +0.2155% | 216 | +0.0285% | +0.1870 pp | 1.64 |
| 2020 | 12 | +0.1844% | 0.49 | 36 | +0.0762% | 217 | +0.0749% | +0.0013 pp | 0.01 |
| 2021 | 12 | +0.2786% | 0.71 | 36 | +0.1083% | 216 | -0.0354% | +0.1438 pp | 0.80 |
| 2022 | 12 | +0.1651% | 0.32 | 36 | +0.0696% | 215 | -0.1762% | +0.2458 pp | 1.19 |
| 2023 | 12 | +0.1599% | 0.46 | 36 | +0.0687% | 214 | +0.0090% | +0.0597 pp | 0.34 |
| 2024 | 12 | +0.3802% | 0.85 | 36 | +0.1393% | 216 | -0.0575% | +0.1968 pp | 1.35 |
| 2025 | 12 | +0.2942% | 0.99 | 36 | +0.1121% | 214 | +0.0039% | +0.1083 pp | 0.84 |
| 2026 | 10 | -0.5501% | -1.50 | 30 | -0.1707% | 179 | +0.0149% | -0.1855 pp | -1.56 |

## Leaving out one year at a time

MEASURED. This mark requires a positive mean in each reduced sample, not a t-statistic of 2.0.
The rows overlap, so they are not independent replications.

| Omitted year | Remaining windows | Net mean | Window t |
| --- | ---: | ---: | ---: |
| 2016 | 118 | +0.2373% | 2.03 |
| 2017 | 118 | +0.2607% | 2.25 |
| 2018 | 118 | +0.2306% | 1.97 |
| 2019 | 118 | +0.2203% | 1.93 |
| 2020 | 118 | +0.2635% | 2.31 |
| 2021 | 118 | +0.2539% | 2.24 |
| 2022 | 118 | +0.2654% | 2.44 |
| 2023 | 118 | +0.2660% | 2.32 |
| 2024 | 118 | +0.2436% | 2.19 |
| 2025 | 118 | +0.2523% | 2.17 |
| 2026 | 120 | +0.3234% | 2.89 |

## Shown only

MEASURED. No alternate cost, width, or instrument was used to select the judged result. The assumed return on uninvested cash was 0%.

| Variant | Windows | Net mean | Window t |
| --- | ---: | ---: | ---: |
| TLT last three, 5 bps per side | 130 | +0.1961% | 1.80 |
| TLT last three, 10 bps per side | 130 | +0.0959% | 0.88 |
| TLT last 1 session, 2 bps per side | 130 | +0.0425% | 0.59 |
| TLT last 2 sessions, 2 bps per side | 130 | +0.1019% | 1.13 |
| TLT last 4 sessions, 2 bps per side | 130 | +0.2444% | 1.97 |
| TLT last 5 sessions, 2 bps per side | 130 | +0.3523% | 2.48 |
| TLT next month's first three sessions, 2 bps per side | 130 | -0.0099% | -0.06 |
| IEF last three, 2 bps per side | 130 | +0.1864% | 3.46 |
| TLT calendar 2022 only, 2 bps per side | 12 | +0.1651% | 0.32 |

## Limits

UNKNOWN. The consolidated SIP close is not a proven auction fill. A live order could fill at a different price, and the study has no measured slippage beyond the assumed costs ([Alpaca Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)). The same window's mean slips to +0.1961% at 5 bps and +0.0959% at 10 bps per side, and both shown t-statistics are below 2.

MEASURED. In the [Measurement 27](70_measure_27_tlt_closing_cross.md) after-run check, not a judged mark, the Nasdaq closing cross equalled Replay 25's TLT SIP close on 251 of 258 entry or exit sessions with a cross identified; in the [Replay 26 source check](73_replay_26_blocked_at_source_check.md), a second vendor differed from SIP by more than one cent on 55 of 1,508 TLT and IEF fund-sessions (3.6%) in 2016–2018, usually by no more than five cents, with the cause UNKNOWN.

MEASURED. A t-statistic of 2.36 is modest. It uses the usual sample standard error and does not adjust for testing many ideas or for dependence over time. One pass in about 25 tests is not strong confirmation. The partial 2026 year lost money, averaging -0.5501% a window. Twelve times the judged monthly mean is about 3.1% a year unlevered, before taxes. That is a way to put the size in context, not measured compound growth or a forecast.

STATED. The 2016–2018 years overlap the source paper's 1990–2018 sample. Its roughly 0.25% monthly figure came from a modeled 10-year Treasury position net of repo, not an ETF purchase ([Hartley and Schwarz](https://kristaschwarz.com/EOM.pdf)). This replay is not a fully independent test of the original idea. The planned fixed-rule check on older data from a different vendor was blocked before scoring, so it does not confirm or refute this result.

## Run record

MEASURED. The saved result records ledger 162, queue 41, and a claim at 2026-11-26 03:49:53 UTC. STATED. The run owner reports one score from clean commit `a23980332e241ba2813d4433b5313aa81e925863`. The replay figures come from the saved aggregate result; the later checks are linked above.

- Saved result SHA-256 `902482a78439835871582986aeb40265acd1d6442c95f8ffc90955c788d029a8`
- Freeze manifest SHA-256 `c4c0108467c0acfcd95781b9a73379b4a1022a43ca8229f8654a2a445e777bd8`
- Input manifest SHA-256 `43f92b5249c8a2aa8778139f928cf643814e47b778d5892a903227830777aa9a`
- Cash-action packet SHA-256 `e92772b92724b67c34b13640f2c5e383f565a000fd7f33f011da95dbd5af9732`
