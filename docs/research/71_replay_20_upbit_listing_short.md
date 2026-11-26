# Replay 20. Short after an Upbit listing and a red UTC day

MEASURED. Replay 20 passed **5 of 5 marks** on already viewed dates. The unlevered listing book averaged +3.2088% net per trade over 139 trades, at 15 bps per side plus funding. This is the second counted trading-replay pass in about 26 tests, not evidence of US execution or an independent test on unseen dates.

STATED. The [frozen rule](../../research_rig/PREREG_20_upbit_listing_short.md) starts with the first Upbit KRW notice for each dated asset. It waits for the first down UTC day among the notice day and the following two days, then shorts at 01:00 UTC the next day. Cover at the highest high from the notice candle through the last pre-entry candle, capped at 25% above entry, or after 72 hours. Shorts that are opened stay in the book, including adverse covers when the data or contract ends.

## Five judged marks

| Mark | Measured | Verdict |
| --- | ---: | --- |
| At least 30 judged trades | 139 | met |
| Mean net return above zero | +3.2088% | met |
| Mean net above the 95th percentile of control draws | +3.2088% versus +0.056% | met |
| Positive mean without the best 3 trades | +2.537% | met |
| Per-trade t at least 2.0 | 2.839 | met |

MEASURED. The median was +2.522%; 64.7% won and 12.2% stopped. Funding averaged -0.887% of entry notional per trade; the net returns already include it.

## Listing trades by year

| UTC year | Trades | Mean net | Median net | Mean funding | Stopped | Worst |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2020 | 6 | +0.763% | +0.470% | +0.069% | 33.3% | -5.612% |
| 2021 | 8 | +0.565% | +0.074% | +0.189% | 12.5% | -5.923% |
| 2022 | 2 | -1.541% | -1.541% | -0.019% | 0.0% | -2.153% |
| 2023 | 7 | +4.749% | +1.757% | -0.010% | 0.0% | +0.282% |
| 2024 | 17 | +0.165% | -0.218% | +0.102% | 5.9% | -13.731% |
| 2025 | 54 | +1.810% | +4.709% | -1.241% | 22.2% | -28.768% |
| 2026 | 45 | +6.806% | +5.425% | -1.330% | 2.2% | -20.959% |

MEASURED. 2025 and the partial 2026 year account for 99 of 139 trades. 2026 averaged +6.8% and supplied 69% of the summed net returns at equal entry notional. This sum is not the return of a portfolio.

## Notice disposition and stress charges

MEASURED. There were 269 first notices at the frozen cutoff (2026-10-24T00:00Z). Of those, 156 had an eligible contract trading at publication. The counts below reconcile to the full first-notice set.

| Disposition | Count |
| --- | ---: |
| Traded | 139 |
| Trading at notice, no qualifying red day | 17 |
| Not trading at notice | 113 |
| Otherwise eligible, no fill | 0 |
| Other | 0 |

MEASURED. The listing book had 1 labelled missing settlement on 1 trade, with a stress debit of -1.611% of that trade's entry notional. The ordinary book separately charged 1 missing settlement on 1 control trade, -2.029% of its entry notional. These were adverse charges, not recovered funding rates. The rule applies the larger of 2% or the largest absolute pinned rate for the contract to that settlement's mark notional, not to entry notional.

## Ordinary-jump controls

MEASURED. The 1,000 year-matched control draws averaged -1.84% per trade across the draw means. The judged pool held 974 trades: 950 from the Plan 16 store and 24 from supplement-only symbols. The shown clean-through-exit pool additionally rules out notices arriving before the exit.

| UTC year | Judged control pool | Shown clean-through-exit pool |
| --- | ---: | ---: |
| 2020 | 45 | 45 |
| 2021 | 216 | 216 |
| 2022 | 110 | 110 |
| 2023 | 69 | 69 |
| 2024 | 98 | 98 |
| 2025 | 241 | 240 |
| 2026 | 195 | 195 |

MEASURED. The calendar-only gate skipped 8 otherwise executable ordinary entries in the two predeclared archive-coverage ranges. No listing trade was skipped on this basis. The eligibility check never used the realized stop or return, but it changed the control mix.

| Contract | UTC entry month | Skipped |
| --- | --- | ---: |
| ICPUSDT | 2021-05 | 1 |
| 币安人生USDT | 2025-10 | 1 |
| 币安人生USDT | 2025-11 | 3 |
| 币安人生USDT | 2026-01 | 1 |
| 币安人生USDT | 2026-04 | 1 |
| 币安人生USDT | 2026-07 | 1 |

## Shown only

MEASURED. These are alternate summaries, not extra passes. The hourly proxy rows enter off the notice time instead of using the judged red-day wait.

| Variant | Trades | Mean net | Median net | Worst |
| --- | ---: | ---: | ---: | ---: |
| Same listings, 30 bps per side | 139 | +2.915% | +2.228% | -29.106% |
| US-today symbol filter, Binance prices | 15 | +2.003% | +1.824% | -18.596% |
| Hourly proxy, 25% jump screen | 89 | +2.682% | -1.532% | -36.656% |
| Hourly proxy, without jump screen | 156 | +2.316% | -1.128% | -36.656% |
| Hourly proxy, screened entry one candle earlier | 70 | +0.871% | -2.873% | -31.320% |
| High strictly after the notice candle | 139 | +3.230% | +2.522% | -28.768% |
| Terminal cover at last close | 139 | +3.209% | +2.522% | -28.768% |
| Continue after a missing in-hold bar | 139 | +3.209% | +2.522% | -28.768% |

MEASURED. There were 0 listing and 0 ordinary missing-bar closes, so continuing after a missing bar did not change the comparison. With the clean-through-exit controls, the shown 95th percentile was +0.215%.

## Freeze history and run record

STATED. There were four freezes, not four scored runs. Earlier refusals stopped before the lock and produced no scored return. The third freeze's diagnostic was a no-return validation.

| Freeze | What happened |
| --- | --- |
| `6d9aba2` | First attempted start refused on an unverified ordinary-control contract end. |
| `3585a68` | Nine official ends pinned; the next start refused on the missing February 2023 ANKRUSDT mark-price day needed for ordinary settlements. |
| `6169441` | Official daily archives plugged ANKR's missing day. A no-return validation found 16 distinct code/path pairs: four trade-bar edges, SRM's right funding anchor, ICP's early funding, five repairable mark months and five unavailable marks for 币安人生USDT. |
| `20701a0` | Pinned four verified ends and more daily marks, clarified SRM's verified expiry boundary, and allowed only the two narrow calendar-based ordinary skips. No-return validation reported zero pairs at 03:54:46 UTC before the lead agent authorized the single score. |

MEASURED. The saved result records ledger 157 and a start at 2026-11-26 03:54:55 UTC from `20701a0d7bd6c31f329ea52dad96f4aaccd6a5b8`. Saved result SHA-256 `285c74cbe2573fe51b08b0672f84293dbb3e2e53b599884c862278d6368fe6a2`. This page uses only that saved result for numerical performance.

## Independent listing-arm check

MEASURED. A separate implementation written from the frozen plan reproduced 139 listing trades, +3.208846% mean net, t 2.838661, and +2.536671% after dropping the best three. The mean was +0.000046 percentage points above the rounded +3.2088% initially reported. The counts agree: 269 first notices, 156 trading at publication, 139 traded, 17 had no red day, and 0 missed an entry fill. The ordinary-jump control pool and its 95th-percentile mark were not independently recomputed, so this does not independently verify the full pass.

MEASURED, EXPLORATORY ONLY. Across 99 weeks with entries, weighting each week equally gave +2.92% mean net, with a weekly t of 2.59. Three trades at most were open simultaneously. Keeping just the first trade per week gave 99 trades, +3.01% mean net and t 2.37. Reading funding stamps literally rather than aligning them to the time grid changed 22 returns and reduced the mean by 0.0096 percentage points; it did not change trade selection or exits. None of these checks changes a mark.

Independent aggregate report SHA-256 `59d8a2c944715f0f2e7edb3c9a76b8f68d3a4a1e0e71789aac410482c278afe7`. The generator verifies the report before using its figures and does not open the audit's market inputs.

## Limits

STATED. Binance.com perpetuals are not available to US accounts, and we do not go around that restriction ([CFTC Binance order announcement](https://www.cftc.gov/PressRoom/PressReleases/8825-23)). The US-today filter contains only 15 trades and uses today's list, not the historical US list. Even those returns use Binance prices, not US fills or costs.

STATED. Trades overlap in time, so the per-trade t can overstate how much independent evidence there is. The notice candle can include trades from before publication, and hour bars do not tell us which print came first. The ordinary pool covers only the pinned archives and omits the predeclared gaps; it is not a full census of comparable jumps.

MEASURED. The worst listing trade lost 28.8% of entry notional even without leverage. Most trades and much of the result came from 2025–2026. It is the second pass in about 26 tests, not a basis for live trading.
