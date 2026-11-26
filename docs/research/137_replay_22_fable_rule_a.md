# Replay 22. Fable rule A, no AI

## The rule

- STATED, from the [frozen plan](../../research_rig/PREREG_22_fable_rule_a.md). Rule A was read off the Fable 5.2 picker's notes and run here as a fixed rule, with no AI, on the monthly top 30 coins.
- STATED. Wake once a day at 14:00 UTC. A coin signals when its last hourly close is above the highest hourly high of the 21 full days before and was not above it at the last wake, is at most 3% above that level, on a volume ratio of 1.5 or more.
- STATED. Buy at the next hourly open. Hold at most 5 names, each reset to 1 over the larger of 3 and the names held. The rest is cash at zero yield.
- STATED. Sell when a daily close falls under the breakout level, or after 2 days with no new high while the volume ratio is under 1.
- STATED. Judged from 2020-01-01 to 2026-04-01 (end not included) at 12 bp a side, against holding the same list in equal weights at the same cost.

## Did it pass?

MEASURED. Did not pass, **1 of 5 frozen marks**, in the one scored run, started 2026-11-26 11:21:18 UTC. Only the mark against holding was met, and only just: the rule ended at +275.40% and holding the same coins at +274.25%. Its daily Sharpe was 0.67, its largest fall 79.40%, it was positive in 3 of 7 years, and 57% of the random-entry twins ended at or above it. The row closes.

## Frozen marks

MEASURED at the judged cost of 12 bp a side. All five were required. End values are total returns over the judged window.

| Mark | Frozen bar | Measured | Verdict |
| --- | --- | --- | --- |
| Beats holding | End value above holding the same list in equal weights, same costs | +275.40% against +274.25% | met |
| Daily Sharpe | At least 1.0 | 0.67 | not met |
| Largest fall | 40% or less | 79.40% | not met |
| Random twins | End value above the 95th percentile of 500 random-entry twins | +275.40% against +1,202.24%; 57% of twins at or above the rule | not met |
| Positive years | At least 5 of 7 calendar years (2026 to March) | 3 of 7 | not met |

## By year

MEASURED at 12 bp a side. Each year runs from its 1 January mark to the next. 2026 runs to 1 April only.

| Year | Rule A | Same-list hold |
| --- | --- | --- |
| 2020 | -2.43% | +160.14% |
| 2021 | +182.67% | +338.15% |
| 2022 | -63.14% | -73.91% |
| 2023 | +139.54% | +95.72% |
| 2024 | +125.60% | +58.79% |
| 2025 | -20.29% | -45.23% |
| 2026 (to March) | -14.28% | -26.06% |

## Shown only

MEASURED. Each line below was named in the plan as shown only. None of them can count toward a mark.

- Bitcoin held over the judged window: +843.35%, largest fall 76.63%, daily Sharpe 0.90. Cannot count toward a mark.
- Time in cash: 5.96% of judged wakes with no name held. Cannot count toward a mark.
- Trades: 111 in all, 17.8 a year. Cannot count toward a mark.
- Exit reasons: daily close under the breakout level 103; still held at the end of the window 5; stall exit 2; left the list 1. Cannot count toward a mark.
- Without the best 3 trades: -11.14%, largest fall 85.56%, positive in 3 of 7 years. Cannot count toward a mark.
- Rule A with the rule C cash switch: +254.15%, largest fall 53.76%, daily Sharpe 0.78, positive in 3 of 7 years. The switch was off at 1,440 of 2,282 wakes; 67 wakes could not read it. Cannot count toward a mark.
- Shorter exit (no new high in 2 days, without the volume condition): +269.15%, largest fall 79.40%. Cannot count toward a mark.
- Cost at 1 bp a side: rule +311.45%, same-list hold +282.48%. Cannot count toward a mark.
- Cost at 25 bp a side: rule +236.84%, same-list hold +264.76%. Cannot count toward a mark.
- Cost at 40 bp a side: rule +197.25%, same-list hold +254.11%. Cannot count toward a mark.
- The months the rule came from, 2026-04-01 to 2026-10-26, a fresh account at 12 bp: rule +7.51%, same-list hold +19.63%, Bitcoin held +17.39%; 20 trades, 54.33% of wakes in cash, -8.43% without the best 3 trades. Cannot count toward a mark.

## Gaps

- MEASURED. Held hours without a bar: 126 for the rule, 706 for the same-list hold.
- MEASURED. Stale marks (a daily mark on an old close): 0 for the rule, 33 for the hold. Positions closed at their last bar: 0 and 5.
- MEASURED. Coin-wakes not tradable because the spot identity was not confirmed: 7,312 of 51,335 listed coin-wakes. Without a pair segment: 31. With a missing hour, so no signal could be read: 4,268.
- MEASURED. Listed coins with no Binance pair: none.
- MEASURED. Pair-days absent from the archive: 2,792 across 9 pairs (FTTUSDT, HYPEUSDT, KLAYUSDT, MKRUSDT, TONUSDT, UMAUSDT, WLFIUSDT, XEMUSDT, XMRUSDT). Bitcoin had 35 missing hours.
- MEASURED. Twin entries not placed after 1,000 draws: 403 of 55,500 (500 twins times 111 trades).
- MEASURED on planted paths before the run. Power was low. With a true 16% edge the five marks passed in 0.25 of seeds when the gain lasted and 0.20 when it faded; with no edge, in 0.05. So a fail says little about a small edge.
- UNKNOWN. How many dead coins the saved list pages left out. The result covers the tradable subset that could be rebuilt.
- STATED. The rule's shape came from eight months of one agent's notes. The judged window is outside those months.

## What it means

MEASURED. The rule ended about level with holding the same coins (+275.40% against +274.25%) and fell about as far as they did (79.40% against 84.01%). 57% of random-entry twins did as well or better, so on these marks it cannot be told apart from random entries. Without its best 3 trades it lost money (-11.14%). STATED. The row closes.

## Independent recompute

Pending.

## Run record

- STATED by the lead agent. Scored exactly once, from 2026-11-26 11:21:18 UTC to 2026-11-26 11:22:26 UTC, exit 0. Ledger 159, queue 40.
- MEASURED. Freeze: `015e8f8064d38a7de52ed980f32ad0eb5aa5c45b`.
- MEASURED. Scoring approval: `951cd96cf49494efd4f54ef46ce8832e47d79181`.
- MEASURED. Saved aggregate result SHA-256: `0529b20bf2c0430a149be0179ea0f2662f7e7050288cad589ec59f8fb6f4717f`.
