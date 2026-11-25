# 47. Replay 12: following stock purchases disclosed by members of Congress

Status: research result, pretend trades on past prices. Built by `research_rig/report_12.py` from `research_rig/prices_12_summary.json` and `research_rig/events_12_summary.json`, `research_rig/results_12_design.json`, `research_rig/results_12_heldback.json`. The plan is `research_rig/PREREG_12_congress_followers.md`; its numbers are in the config key `replay_12_plan`. Design half scored 2026-11-25 19:12 UTC. Held-back half scored 2026-11-25 19:20 UTC.

Labels: MEASURED means computed from the stored files. UNKNOWN means not known.

## What is tested

- A member's purchases of one stock on one filing day are one event. The pretend trade buys at the open of the first trading day after the filing day and sells at the close after the hold (`replay_12_plan.holds_days`; main hold `replay_12_plan.main_hold_days`). The filing day, never the trade day, decides the entry.
- Every result is also worked out with the entry `replay_12_plan.late_entry_trading_days` trading days later and `replay_12_plan.late_entry_calendar_days` calendar days later.
- Open positions are held in equal weight, reset each day. Cost is `replay_12_plan.cost_bps_per_side` basis points on each day's turnover. The yardstick is SPY held with the same weights on the same days, with no cost.
- The bootstrap resamples calendar months in circular blocks of consecutive months, the block the hold in trading days divided by `replay_12_plan.bootstrap_days_per_month`, rounded up. MEASURED 2026-11-25 18:53 UTC by `research_rig/noedge_12.py` on 1,000 made-up data sets with no edge in them, 48 months long. With nothing there, mark 2 passed 4.8% of the time at the 21-day hold (blocks of 1 month), 6.6% of the time at the 63-day hold (blocks of 3 months), 7.1% of the time at the 126-day hold (blocks of 6 months). The intent is 5%. Mark 2 is one of five marks that must all hold.
- The design half (filed `replay_12_plan.design_filed_from` to `replay_12_plan.design_filed_to`) only chooses one set-up. The held-back half (filed from `replay_12_plan.heldback_filed_from`) judges it once.

## Data in hand

- MEASURED. Daily bars adjusted for splits and dividends (2018-12-01 to 2026-11-24, feed sip) were asked for 2998 symbols. Of 2996 tickers in buy and sell rows, 2390 have bars and 606 have none.
- MEASURED. 338 tickers' bars start after 2019-01-02 and 558 end before 2026-11-24. NANC has bars from 2023-02-07.
- MEASURED. 85291 rows give 29379 stock purchase events and 30565 sale events from 204 members buying 2381 tickers. The busiest buyer, Ro Khanna, has 40.9% of purchase events.

| Half | Side | Events | Large | Members | No bar on main entry day | Share | With call or exercise words |
|---|---|---|---|---|---|---|---|
| design | buy | 15457 | 1216 | 153 | 410 | 2.6% | 36 |
| heldback | buy | 13922 | 555 | 116 | 471 | 3.4% | 195 |
| design | sell | 15698 | 1419 | 184 | 588 | 3.8% | 38 |
| heldback | sell | 14867 | 1266 | 183 | 652 | 4.4% | 101 |

No bar on the main entry day, by filing year (purchases): 2019 99, 2020 215, 2021 55, 2022 41, 2023 128, 2024 43, 2025 104, 2026 196.

- MEASURED. The rename list `research_rig/renames_12.csv`, built from public sources before scoring, maps 19 old tickers to the same company's new ticker and leaves out 55 (takeovers, share-class changes, delistings, preferred shares and names not confirmed). Events it gives a bar on the main entry day, by filing year: purchases, design 2019 18, 2020 27, 2021 21, 2022 15; purchases, held-back 2023 14, 2024 11, 2025 24, 2026 2; sales, design 2019 12, 2020 22, 2021 12, 2022 11; sales, held-back 2023 16, 2024 12, 2025 28, 2026 1.
- MEASURED. Dated lines, for tickers whose price file holds another company's history for earlier rows (found in passing, not hunted for): 4 send rows filed before a date to the right ticker and 3 leave such rows out, counted as no price. The filing day chooses the line. Events moved, by line (ticker before date): purchases, design BBT<2025-09-02 2, CCC<2025-10-31 2, RBC<2021-10-05 2, WTW<2019-04-22 1, WTW<2022-01-10 1; purchases, held-back none; sales, design AM<2019-03-13 4, BBT<2025-09-02 1, HR<2022-07-21 1; sales, held-back BBT<2025-09-02 1.

Named members matched in trades.csv (full name and rows):

- Pelosi: Nancy Pelosi (142 rows)
- Khanna: Ro Khanna (32284 rows)
- McCaul: Michael T. McCaul (7659 rows)
- Gottheimer: Josh Gottheimer (3209 rows)
- Cisneros: Gilbert Ray Cisneros, Jr. (2781 rows)
- Lisa C. McClain: Lisa C. McClain (1421 rows)
- Tuberville: Tommy Tuberville (1192 rows)
- Greene: Marjorie Taylor Greene (507 rows)
- Mullin: Markwayne Mullin (386 rows)
- Bresnahan: Robert P. Bresnahan, Jr. (607 rows)
- Goldman: Daniel S. Goldman (1151 rows)
- Crenshaw: Dan Crenshaw (32 rows)
- Wasserman Schultz: Debbie Wasserman Schultz (47 rows)

## The design half (used only to choose a set-up, not to judge)

| Set-up | Entry | Events traded | No price | Growth | SPY mirror | Per-year excess | Sales per-year excess | Bootstrap 5th pct, monthly | No daily reset (not judged) |
|---|---|---|---|---|---|---|---|---|---|
| every stock purchase, hold 21 trading days | main entry | 15047 | 410 | 1.595 | 1.714 | -1.75% | -3.40% | -0.640% | 1.688 |
| every stock purchase, hold 21 trading days | entry 5 trading days later | 15042 | 415 | 1.547 | 1.694 | -2.21% | +2.11% | -0.650% | 1.637 |
| every stock purchase, hold 21 trading days | entry 30 calendar days later | 15028 | 429 | 1.156 | 1.579 | -7.41% | -0.47% | -1.080% | 1.237 |
| every stock purchase, hold 63 trading days | main entry | 15047 | 410 | 1.717 | 1.731 | -0.20% | +0.99% | -0.463% | 1.783 |
| every stock purchase, hold 63 trading days | entry 5 trading days later | 15042 | 415 | 1.604 | 1.687 | -1.18% | +0.85% | -0.505% | 1.666 |
| every stock purchase, hold 63 trading days | entry 30 calendar days later | 15028 | 429 | 1.427 | 1.644 | -3.30% | +0.45% | -0.685% | 1.480 |
| every stock purchase, hold 126 trading days | main entry | 15047 | 410 | 1.925 | 1.873 | +0.61% | +2.63% | -0.357% | 1.986 |
| every stock purchase, hold 126 trading days | entry 5 trading days later | 15042 | 415 | 1.944 | 1.842 | +1.21% | +3.65% | -0.315% | 2.006 |
| every stock purchase, hold 126 trading days | entry 30 calendar days later | 15028 | 429 | 1.881 | 1.816 | +0.79% | +2.33% | -0.329% | 1.938 |
| purchases of at least large_buy_min_usd, hold 21 trading days | main entry | 1166 | 50 | 1.771 | 1.646 | +1.82% | -3.19% | -0.462% | 1.911 |
| purchases of at least large_buy_min_usd, hold 21 trading days | entry 5 trading days later | 1166 | 50 | 1.656 | 1.564 | +1.42% | +0.60% | -0.504% | 1.787 |
| purchases of at least large_buy_min_usd, hold 21 trading days | entry 30 calendar days later | 1166 | 50 | 1.328 | 1.617 | -4.77% | +0.02% | -1.166% | 1.441 |
| purchases of at least large_buy_min_usd, hold 63 trading days | main entry | 1166 | 50 | 1.952 | 1.649 | +4.10% | +1.28% | -0.080% | 2.032 |
| purchases of at least large_buy_min_usd, hold 63 trading days | entry 5 trading days later | 1166 | 50 | 1.811 | 1.633 | +2.49% | +3.35% | -0.297% | 1.884 |
| purchases of at least large_buy_min_usd, hold 63 trading days | entry 30 calendar days later | 1166 | 50 | 1.531 | 1.656 | -1.84% | +3.87% | -0.753% | 1.595 |
| purchases of at least large_buy_min_usd, hold 126 trading days | main entry | 1166 | 50 | 1.979 | 1.828 | +1.80% | +3.46% | -0.157% | 2.041 |
| purchases of at least large_buy_min_usd, hold 126 trading days | entry 5 trading days later | 1166 | 50 | 2.074 | 1.778 | +3.52% | +4.96% | -0.057% | 2.139 |
| purchases of at least large_buy_min_usd, hold 126 trading days | entry 30 calendar days later | 1166 | 50 | 2.152 | 1.819 | +3.85% | +4.82% | -0.118% | 2.219 |
| purchases by the proven list, hold 21 trading days | main entry | 1338 | 49 | 1.407 | 1.471 | -1.40% | -14.44% | -1.415% | 1.482 |
| purchases by the proven list, hold 21 trading days | entry 5 trading days later | 931 | 35 | 1.675 | 1.405 | +5.65% | -7.99% | -0.792% | 1.772 |
| purchases by the proven list, hold 21 trading days | entry 30 calendar days later | 1429 | 35 | 1.003 | 1.595 | -12.04% | -17.92% | -2.071% | 1.074 |
| purchases by the proven list, hold 63 trading days | main entry | 1173 | 35 | 0.676 | 1.416 | -18.01% | +2.31% | -2.479% | 0.703 |
| purchases by the proven list, hold 63 trading days | entry 5 trading days later | 1162 | 36 | 0.716 | 1.434 | -17.01% | +2.24% | -2.647% | 0.744 |
| purchases by the proven list, hold 63 trading days | entry 30 calendar days later | 2126 | 50 | 1.261 | 1.523 | -4.99% | -2.22% | -1.094% | 1.309 |
| purchases by the proven list, hold 126 trading days | main entry | 1321 | 27 | 1.423 | 1.548 | -2.25% | -2.42% | -1.314% | 1.465 |
| purchases by the proven list, hold 126 trading days | entry 5 trading days later | 1363 | 38 | 1.579 | 1.563 | +0.29% | -3.61% | -0.833% | 1.626 |
| purchases by the proven list, hold 126 trading days | entry 30 calendar days later | 1589 | 30 | 1.666 | 1.589 | +1.28% | -6.34% | -1.381% | 1.714 |

Chosen by the fixed rule (highest per-year excess at the main entry): purchases of at least large_buy_min_usd, hold 63 trading days. It alone is scored on the held-back half, once. The best of 9 looks better than it is; that is why this half does not judge.

## The held-back half (the judge)

Set-up: purchases of at least large_buy_min_usd, hold 63 trading days.

| Entry | Events traded | No price | Stopped | Growth | SPY mirror | Per-year excess | Sales per-year excess | Bootstrap 5th pct, monthly | QQQ, for scale | NANC, for scale |
|---|---|---|---|---|---|---|---|---|---|---|
| main entry | 543 | 5 | 2 | 1.985 | 2.062 | -1.00% | -2.09% | -0.801% | -7.35% | -1.64% |
| entry 5 trading days later | 543 | 5 | 2 | 1.617 | 2.045 | -6.01% | -0.95% | -1.271% | -12.17% | -6.32% |
| entry 30 calendar days later | 543 | 5 | 2 | 1.672 | 1.819 | -2.21% | -3.47% | -0.995% | -6.41% | -2.23% |

Pass marks, fixed before:

- 1. ends above the SPY mirror: no
- 2. bootstrap 5th percentile of the mean monthly difference above zero: no. MEASURED 2026-11-25 18:53 UTC by `research_rig/noedge_12.py` on 1,000 made-up data sets with no edge in them, 48 months long. With nothing there, mark 2 passed 4.8% of the time at the 21-day hold (blocks of 1 month), 6.6% of the time at the 63-day hold (blocks of 3 months), 7.1% of the time at the 126-day hold (blocks of 6 months). The intent is 5%. Mark 2 is one of five marks that must all hold.
- 3. per-year excess above the sales portfolio's: yes
- 4. at least replay_12_plan.min_events events traded: yes
- 5. with the late5 entry, still ends above SPY: no

MEASURED. Verdict: does not pass.

### Side lines (reported, not judged)

- one position per stock, not per member: per-year excess +1.48%, events traded 543.
- without the busiest member (Michael T. McCaul): per-year excess -0.76%, events traded 331.
- without events whose rows mention a call or an exercise: per-year excess -1.20%, events traded 526.
- without trades whose prices stop inside the hold: per-year excess -1.27%, events traded 541.
- the same stocks on random filing days (yardstick c, 200 draws): share of draws at or above the real result 58.5%.

### Each year apart, main entry (reported, not judged)

| Year | Days held | Growth | SPY mirror |
|---|---|---|---|
| 2023 | 249 | 1.185 | 1.254 |
| 2024 | 252 | 1.106 | 1.247 |
| 2025 | 250 | 1.166 | 1.174 |
| 2026 | 203 | 1.299 | 1.124 |

### No price, by filing year

2023 2, 2024 1, 2025 2, 2026 0

### The 20 largest single-event returns, chosen hold, main entry

| Ticker | Member | Filed | Entry | Exit | Stopped | Return |
|---|---|---|---|---|---|---|
| OPEN | Cleo Fields | 2025-08-06 | 2025-08-07 | 2025-11-04 | no | +259.48% |
| IREN | Cleo Fields | 2025-08-06 | 2025-08-07 | 2025-11-04 | no | +256.31% |
| SNDK | Lisa C. McClain | 2025-11-21 | 2025-11-24 | 2026-02-25 | no | +206.87% |
| HUMA | Tommy Tuberville | 2024-04-15 | 2024-04-16 | 2024-07-16 | no | +193.00% |
| SNDK | Ro Khanna | 2026-02-06 | 2026-02-09 | 2026-05-08 | no | +163.83% |
| MU | John Fetterman | 2026-04-03 | 2026-04-06 | 2026-07-06 | no | +163.49% |
| AMD | Julia Letlow | 2026-03-12 | 2026-03-13 | 2026-06-11 | no | +146.55% |
| AMD | Ro Khanna | 2026-03-09 | 2026-03-10 | 2026-06-08 | no | +142.13% |
| AMD | Gilbert Ray Cisneros, Jr. | 2026-03-09 | 2026-03-10 | 2026-06-08 | no | +142.13% |
| MU | Ro Khanna | 2026-03-09 | 2026-03-10 | 2026-06-08 | no | +141.03% |
| MU | Tony Wied | 2026-03-09 | 2026-03-10 | 2026-06-08 | no | +141.03% |
| MU | Gilbert Ray Cisneros, Jr. | 2026-03-09 | 2026-03-10 | 2026-06-08 | no | +141.03% |
| INTC | Gilbert Ray Cisneros, Jr. | 2026-02-13 | 2026-02-17 | 2026-05-15 | no | +136.82% |
| AMD | Cleo Fields | 2026-02-24 | 2026-02-25 | 2026-05-26 | no | +134.56% |
| HOOD | Byron Donalds | 2025-04-14 | 2025-04-15 | 2025-07-16 | no | +133.65% |
| MRNA | Ro Khanna | 2026-07-06 | 2026-07-07 | 2026-10-02 | no | +131.44% |
| AZN | Gilbert Ray Cisneros, Jr. | 2025-11-18 | 2025-11-19 | 2026-02-20 | no | +130.42% |
| SNDK | Gilbert Ray Cisneros, Jr. | 2026-02-13 | 2026-02-17 | 2026-05-15 | no | +130.00% |
| AZN | Lisa C. McClain | 2025-11-21 | 2025-11-24 | 2026-02-25 | no | +129.53% |
| MU | Gilbert Ray Cisneros, Jr. | 2026-04-07 | 2026-04-08 | 2026-07-08 | no | +128.59% |

## Named members, held-back half (reported, not judged)

Per event, entry open to exit close, less SPY over the same days. Call purchases are shown as the underlying stock after the purchase: these are stock returns, not option returns.

| Name | Member | What | Hold | Entry | Events | Mean less SPY | Median less SPY | Share above SPY |
|---|---|---|---|---|---|---|---|---|
| Pelosi | Nancy Pelosi | stock purchases | 21 | main entry | 13 | +0.25% | -1.03% | 46.2% |
| Pelosi | Nancy Pelosi | stock purchases | 21 | entry 5 trading days later | 13 | -2.73% | -2.48% | 38.5% |
| Pelosi | Nancy Pelosi | stock purchases | 21 | entry 30 calendar days later | 13 | -1.33% | -1.02% | 38.5% |
| Pelosi | Nancy Pelosi | stock purchases | 63 | main entry | 13 | -0.10% | +1.45% | 53.8% |
| Pelosi | Nancy Pelosi | stock purchases | 63 | entry 5 trading days later | 13 | +2.10% | +1.22% | 53.8% |
| Pelosi | Nancy Pelosi | stock purchases | 63 | entry 30 calendar days later | 13 | +2.00% | +1.61% | 61.5% |
| Pelosi | Nancy Pelosi | stock purchases | 126 | main entry | 13 | -2.90% | -0.50% | 46.2% |
| Pelosi | Nancy Pelosi | stock purchases | 126 | entry 5 trading days later | 13 | +0.73% | +0.77% | 61.5% |
| Pelosi | Nancy Pelosi | stock purchases | 126 | entry 30 calendar days later | 13 | -0.58% | +0.16% | 53.8% |
| Pelosi | Nancy Pelosi | stock after call purchases (not option returns) | 21 | main entry | 14 | +3.68% | -3.40% | 28.6% |
| Pelosi | Nancy Pelosi | stock after call purchases (not option returns) | 21 | entry 5 trading days later | 14 | -2.55% | -4.99% | 35.7% |
| Pelosi | Nancy Pelosi | stock after call purchases (not option returns) | 21 | entry 30 calendar days later | 14 | -4.10% | -2.29% | 35.7% |
| Pelosi | Nancy Pelosi | stock after call purchases (not option returns) | 63 | main entry | 14 | +2.02% | -0.94% | 50.0% |
| Pelosi | Nancy Pelosi | stock after call purchases (not option returns) | 63 | entry 5 trading days later | 14 | +3.71% | -0.16% | 50.0% |
| Pelosi | Nancy Pelosi | stock after call purchases (not option returns) | 63 | entry 30 calendar days later | 14 | +2.00% | +2.21% | 50.0% |
| Pelosi | Nancy Pelosi | stock after call purchases (not option returns) | 126 | main entry | 12 | +18.81% | +5.37% | 58.3% |
| Pelosi | Nancy Pelosi | stock after call purchases (not option returns) | 126 | entry 5 trading days later | 12 | +20.56% | +7.58% | 83.3% |
| Pelosi | Nancy Pelosi | stock after call purchases (not option returns) | 126 | entry 30 calendar days later | 12 | +14.41% | +7.96% | 75.0% |
| Khanna | Ro Khanna | stock purchases | 21 | main entry | 5636 | -0.33% | -0.72% | 46.5% |
| Khanna | Ro Khanna | stock purchases | 21 | entry 5 trading days later | 5636 | -0.49% | -0.78% | 45.8% |
| Khanna | Ro Khanna | stock purchases | 21 | entry 30 calendar days later | 5632 | -0.57% | -0.92% | 44.4% |
| Khanna | Ro Khanna | stock purchases | 63 | main entry | 5636 | -2.00% | -2.62% | 42.0% |
| Khanna | Ro Khanna | stock purchases | 63 | entry 5 trading days later | 5636 | -1.99% | -2.66% | 42.1% |
| Khanna | Ro Khanna | stock purchases | 63 | entry 30 calendar days later | 5632 | -1.98% | -2.81% | 41.8% |
| Khanna | Ro Khanna | stock purchases | 126 | main entry | 5249 | -3.82% | -5.09% | 39.2% |
| Khanna | Ro Khanna | stock purchases | 126 | entry 5 trading days later | 5249 | -3.95% | -5.39% | 38.3% |
| Khanna | Ro Khanna | stock purchases | 126 | entry 30 calendar days later | 5055 | -3.93% | -5.55% | 38.8% |
| McCaul | Michael T. McCaul | stock purchases | 21 | main entry | 539 | -0.67% | -0.83% | 46.2% |
| McCaul | Michael T. McCaul | stock purchases | 21 | entry 5 trading days later | 539 | -0.73% | -1.05% | 45.5% |
| McCaul | Michael T. McCaul | stock purchases | 21 | entry 30 calendar days later | 539 | -0.72% | -0.70% | 46.6% |
| McCaul | Michael T. McCaul | stock purchases | 63 | main entry | 539 | -1.84% | -1.92% | 44.9% |
| McCaul | Michael T. McCaul | stock purchases | 63 | entry 5 trading days later | 539 | -1.66% | -1.43% | 44.3% |
| McCaul | Michael T. McCaul | stock purchases | 63 | entry 30 calendar days later | 539 | -0.77% | -1.04% | 48.8% |
| McCaul | Michael T. McCaul | stock purchases | 126 | main entry | 496 | -3.29% | -4.91% | 43.8% |
| McCaul | Michael T. McCaul | stock purchases | 126 | entry 5 trading days later | 496 | -3.09% | -3.67% | 43.5% |
| McCaul | Michael T. McCaul | stock purchases | 126 | entry 30 calendar days later | 482 | -2.85% | -3.95% | 43.6% |
| Gottheimer | Josh Gottheimer | stock purchases | 21 | main entry | 453 | -0.43% | -0.47% | 47.5% |
| Gottheimer | Josh Gottheimer | stock purchases | 21 | entry 5 trading days later | 452 | +0.04% | -0.09% | 49.3% |
| Gottheimer | Josh Gottheimer | stock purchases | 21 | entry 30 calendar days later | 452 | +0.13% | -1.04% | 45.8% |
| Gottheimer | Josh Gottheimer | stock purchases | 63 | main entry | 453 | -0.10% | -2.18% | 45.3% |
| Gottheimer | Josh Gottheimer | stock purchases | 63 | entry 5 trading days later | 452 | +0.26% | -2.04% | 45.8% |
| Gottheimer | Josh Gottheimer | stock purchases | 63 | entry 30 calendar days later | 452 | +1.17% | -1.60% | 45.8% |
| Gottheimer | Josh Gottheimer | stock purchases | 126 | main entry | 445 | -0.93% | -1.83% | 45.6% |
| Gottheimer | Josh Gottheimer | stock purchases | 126 | entry 5 trading days later | 444 | -1.05% | -2.79% | 45.5% |
| Gottheimer | Josh Gottheimer | stock purchases | 126 | entry 30 calendar days later | 437 | -0.79% | -3.32% | 46.0% |
| Gottheimer | Josh Gottheimer | stock after call purchases (not option returns) | 21 | main entry | 13 | +0.59% | +2.95% | 53.8% |
| Gottheimer | Josh Gottheimer | stock after call purchases (not option returns) | 21 | entry 5 trading days later | 13 | +0.18% | -0.22% | 46.2% |
| Gottheimer | Josh Gottheimer | stock after call purchases (not option returns) | 21 | entry 30 calendar days later | 13 | +2.77% | +2.13% | 53.8% |
| Gottheimer | Josh Gottheimer | stock after call purchases (not option returns) | 63 | main entry | 13 | +3.77% | +0.87% | 69.2% |
| Gottheimer | Josh Gottheimer | stock after call purchases (not option returns) | 63 | entry 5 trading days later | 13 | +4.13% | +1.62% | 53.8% |
| Gottheimer | Josh Gottheimer | stock after call purchases (not option returns) | 63 | entry 30 calendar days later | 13 | +7.61% | +8.84% | 76.9% |
| Gottheimer | Josh Gottheimer | stock after call purchases (not option returns) | 126 | main entry | 12 | +6.85% | +6.88% | 75.0% |
| Gottheimer | Josh Gottheimer | stock after call purchases (not option returns) | 126 | entry 5 trading days later | 12 | +5.59% | +6.14% | 75.0% |
| Gottheimer | Josh Gottheimer | stock after call purchases (not option returns) | 126 | entry 30 calendar days later | 12 | +5.75% | +6.80% | 75.0% |
| Cisneros | Gilbert Ray Cisneros, Jr. | stock purchases | 21 | main entry | 700 | +0.23% | -1.03% | 46.1% |
| Cisneros | Gilbert Ray Cisneros, Jr. | stock purchases | 21 | entry 5 trading days later | 700 | +0.07% | -1.29% | 45.4% |
| Cisneros | Gilbert Ray Cisneros, Jr. | stock purchases | 21 | entry 30 calendar days later | 700 | +0.57% | -0.57% | 47.0% |
| Cisneros | Gilbert Ray Cisneros, Jr. | stock purchases | 63 | main entry | 700 | +0.15% | -3.92% | 41.4% |
| Cisneros | Gilbert Ray Cisneros, Jr. | stock purchases | 63 | entry 5 trading days later | 700 | +0.24% | -3.82% | 42.1% |
| Cisneros | Gilbert Ray Cisneros, Jr. | stock purchases | 63 | entry 30 calendar days later | 700 | +0.17% | -3.04% | 43.7% |
| Cisneros | Gilbert Ray Cisneros, Jr. | stock purchases | 126 | main entry | 623 | -1.00% | -6.24% | 39.5% |
| Cisneros | Gilbert Ray Cisneros, Jr. | stock purchases | 126 | entry 5 trading days later | 623 | -0.67% | -5.82% | 39.8% |
| Cisneros | Gilbert Ray Cisneros, Jr. | stock purchases | 126 | entry 30 calendar days later | 586 | -1.91% | -7.30% | 38.1% |
| Lisa C. McClain | Lisa C. McClain | stock purchases | 21 | main entry | 635 | -0.73% | -1.42% | 41.1% |
| Lisa C. McClain | Lisa C. McClain | stock purchases | 21 | entry 5 trading days later | 634 | -1.67% | -2.26% | 36.1% |
| Lisa C. McClain | Lisa C. McClain | stock purchases | 21 | entry 30 calendar days later | 634 | -0.72% | -1.85% | 39.9% |
| Lisa C. McClain | Lisa C. McClain | stock purchases | 63 | main entry | 635 | -1.13% | -4.11% | 38.4% |
| Lisa C. McClain | Lisa C. McClain | stock purchases | 63 | entry 5 trading days later | 634 | -0.94% | -3.41% | 40.1% |
| Lisa C. McClain | Lisa C. McClain | stock purchases | 63 | entry 30 calendar days later | 634 | +0.29% | -2.21% | 43.1% |
| Lisa C. McClain | Lisa C. McClain | stock purchases | 126 | main entry | 635 | +2.56% | -1.78% | 46.8% |
| Lisa C. McClain | Lisa C. McClain | stock purchases | 126 | entry 5 trading days later | 634 | +3.28% | -2.27% | 45.4% |
| Lisa C. McClain | Lisa C. McClain | stock purchases | 126 | entry 30 calendar days later | 634 | +2.82% | -2.43% | 46.2% |
| Tuberville | Tommy Tuberville | stock purchases | 21 | main entry | 129 | +0.12% | -0.52% | 45.7% |
| Tuberville | Tommy Tuberville | stock purchases | 21 | entry 5 trading days later | 129 | +0.77% | -0.66% | 47.3% |
| Tuberville | Tommy Tuberville | stock purchases | 21 | entry 30 calendar days later | 129 | -0.49% | -0.40% | 47.3% |
| Tuberville | Tommy Tuberville | stock purchases | 63 | main entry | 129 | -1.14% | -3.78% | 37.2% |
| Tuberville | Tommy Tuberville | stock purchases | 63 | entry 5 trading days later | 129 | -2.21% | -3.39% | 41.9% |
| Tuberville | Tommy Tuberville | stock purchases | 63 | entry 30 calendar days later | 129 | -2.12% | -1.36% | 42.6% |
| Tuberville | Tommy Tuberville | stock purchases | 126 | main entry | 129 | -2.72% | -4.28% | 44.2% |
| Tuberville | Tommy Tuberville | stock purchases | 126 | entry 5 trading days later | 129 | -3.09% | -3.24% | 44.2% |
| Tuberville | Tommy Tuberville | stock purchases | 126 | entry 30 calendar days later | 129 | -3.73% | -1.67% | 46.5% |
| Tuberville | Tommy Tuberville | stock after call purchases (not option returns) | 21 | main entry | 9 | +8.18% | +4.67% | 77.8% |
| Tuberville | Tommy Tuberville | stock after call purchases (not option returns) | 21 | entry 5 trading days later | 9 | +9.37% | +10.86% | 77.8% |
| Tuberville | Tommy Tuberville | stock after call purchases (not option returns) | 21 | entry 30 calendar days later | 9 | -2.99% | -1.11% | 44.4% |
| Tuberville | Tommy Tuberville | stock after call purchases (not option returns) | 63 | main entry | 9 | +4.93% | -0.31% | 44.4% |
| Tuberville | Tommy Tuberville | stock after call purchases (not option returns) | 63 | entry 5 trading days later | 9 | +5.23% | +7.84% | 55.6% |
| Tuberville | Tommy Tuberville | stock after call purchases (not option returns) | 63 | entry 30 calendar days later | 9 | -5.36% | -9.95% | 44.4% |
| Tuberville | Tommy Tuberville | stock after call purchases (not option returns) | 126 | main entry | 9 | -0.37% | -11.46% | 44.4% |
| Tuberville | Tommy Tuberville | stock after call purchases (not option returns) | 126 | entry 5 trading days later | 9 | -2.53% | -7.14% | 44.4% |
| Tuberville | Tommy Tuberville | stock after call purchases (not option returns) | 126 | entry 30 calendar days later | 9 | -7.85% | -9.10% | 44.4% |
| Greene | Marjorie Taylor Greene | stock purchases | 21 | main entry | 354 | +0.08% | -0.63% | 46.9% |
| Greene | Marjorie Taylor Greene | stock purchases | 21 | entry 5 trading days later | 354 | +0.48% | +0.06% | 50.6% |
| Greene | Marjorie Taylor Greene | stock purchases | 21 | entry 30 calendar days later | 354 | +0.18% | -0.49% | 47.2% |
| Greene | Marjorie Taylor Greene | stock purchases | 63 | main entry | 354 | +0.93% | -0.68% | 47.7% |
| Greene | Marjorie Taylor Greene | stock purchases | 63 | entry 5 trading days later | 354 | +1.10% | -0.27% | 48.6% |
| Greene | Marjorie Taylor Greene | stock purchases | 63 | entry 30 calendar days later | 354 | +1.65% | +0.83% | 51.7% |
| Greene | Marjorie Taylor Greene | stock purchases | 126 | main entry | 354 | +2.39% | -0.89% | 47.7% |
| Greene | Marjorie Taylor Greene | stock purchases | 126 | entry 5 trading days later | 354 | +2.24% | -0.29% | 49.4% |
| Greene | Marjorie Taylor Greene | stock purchases | 126 | entry 30 calendar days later | 354 | +2.97% | +1.26% | 52.5% |
| Mullin | Markwayne Mullin | stock purchases | 21 | main entry | 245 | +1.03% | +0.65% | 56.7% |
| Mullin | Markwayne Mullin | stock purchases | 21 | entry 5 trading days later | 245 | +0.07% | +0.03% | 50.2% |
| Mullin | Markwayne Mullin | stock purchases | 21 | entry 30 calendar days later | 245 | +0.24% | +0.49% | 52.7% |
| Mullin | Markwayne Mullin | stock purchases | 63 | main entry | 245 | +2.31% | +2.02% | 53.9% |
| Mullin | Markwayne Mullin | stock purchases | 63 | entry 5 trading days later | 245 | +1.61% | +1.10% | 52.7% |
| Mullin | Markwayne Mullin | stock purchases | 63 | entry 30 calendar days later | 245 | +1.58% | -0.16% | 49.8% |
| Mullin | Markwayne Mullin | stock purchases | 126 | main entry | 245 | +1.89% | -1.06% | 48.6% |
| Mullin | Markwayne Mullin | stock purchases | 126 | entry 5 trading days later | 245 | +1.42% | -0.05% | 49.8% |
| Mullin | Markwayne Mullin | stock purchases | 126 | entry 30 calendar days later | 245 | +1.01% | -2.72% | 44.1% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock purchases | 21 | main entry | 218 | -0.60% | -1.26% | 42.7% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock purchases | 21 | entry 5 trading days later | 218 | -0.73% | -1.54% | 43.6% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock purchases | 21 | entry 30 calendar days later | 218 | -0.36% | -0.48% | 46.8% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock purchases | 63 | main entry | 218 | -2.28% | -3.02% | 41.7% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock purchases | 63 | entry 5 trading days later | 218 | -1.97% | -2.59% | 42.2% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock purchases | 63 | entry 30 calendar days later | 218 | -1.73% | -3.53% | 38.1% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock purchases | 126 | main entry | 218 | -5.78% | -9.56% | 34.9% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock purchases | 126 | entry 5 trading days later | 218 | -5.01% | -8.74% | 35.3% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock purchases | 126 | entry 30 calendar days later | 218 | -4.90% | -8.50% | 35.8% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock after call purchases (not option returns) | 21 | main entry | 1 | +15.64% | +15.64% | 100.0% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock after call purchases (not option returns) | 21 | entry 5 trading days later | 1 | +13.11% | +13.11% | 100.0% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock after call purchases (not option returns) | 21 | entry 30 calendar days later | 1 | +6.81% | +6.81% | 100.0% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock after call purchases (not option returns) | 63 | main entry | 1 | +8.27% | +8.27% | 100.0% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock after call purchases (not option returns) | 63 | entry 5 trading days later | 1 | +7.00% | +7.00% | 100.0% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock after call purchases (not option returns) | 63 | entry 30 calendar days later | 1 | -11.66% | -11.66% | 0.0% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock after call purchases (not option returns) | 126 | main entry | 1 | -7.01% | -7.01% | 0.0% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock after call purchases (not option returns) | 126 | entry 5 trading days later | 1 | -6.69% | -6.69% | 0.0% |
| Bresnahan | Robert P. Bresnahan, Jr. | stock after call purchases (not option returns) | 126 | entry 30 calendar days later | 1 | -22.62% | -22.62% | 0.0% |
| Goldman | Daniel S. Goldman | stock purchases | 21 | main entry | 238 | -1.87% | -2.37% | 40.8% |
| Goldman | Daniel S. Goldman | stock purchases | 21 | entry 5 trading days later | 238 | -1.50% | -2.22% | 41.2% |
| Goldman | Daniel S. Goldman | stock purchases | 21 | entry 30 calendar days later | 238 | +0.04% | -1.15% | 43.7% |
| Goldman | Daniel S. Goldman | stock purchases | 63 | main entry | 238 | -4.17% | -7.85% | 34.0% |
| Goldman | Daniel S. Goldman | stock purchases | 63 | entry 5 trading days later | 238 | -3.84% | -5.69% | 32.4% |
| Goldman | Daniel S. Goldman | stock purchases | 63 | entry 30 calendar days later | 238 | -2.54% | -4.87% | 35.3% |
| Goldman | Daniel S. Goldman | stock purchases | 126 | main entry | 238 | -6.70% | -8.90% | 32.4% |
| Goldman | Daniel S. Goldman | stock purchases | 126 | entry 5 trading days later | 238 | -7.03% | -8.73% | 32.4% |
| Goldman | Daniel S. Goldman | stock purchases | 126 | entry 30 calendar days later | 238 | -4.53% | -6.56% | 36.1% |
| Wasserman Schultz | Debbie Wasserman Schultz | stock purchases | 21 | main entry | 10 | +0.13% | -4.26% | 40.0% |
| Wasserman Schultz | Debbie Wasserman Schultz | stock purchases | 21 | entry 5 trading days later | 10 | -3.37% | -3.71% | 20.0% |
| Wasserman Schultz | Debbie Wasserman Schultz | stock purchases | 21 | entry 30 calendar days later | 10 | +15.15% | +12.78% | 90.0% |
| Wasserman Schultz | Debbie Wasserman Schultz | stock purchases | 63 | main entry | 10 | +9.44% | +5.33% | 50.0% |
| Wasserman Schultz | Debbie Wasserman Schultz | stock purchases | 63 | entry 5 trading days later | 10 | +2.04% | -7.84% | 40.0% |
| Wasserman Schultz | Debbie Wasserman Schultz | stock purchases | 63 | entry 30 calendar days later | 10 | +13.66% | +17.54% | 60.0% |
| Wasserman Schultz | Debbie Wasserman Schultz | stock purchases | 126 | main entry | 10 | +16.72% | +2.39% | 60.0% |
| Wasserman Schultz | Debbie Wasserman Schultz | stock purchases | 126 | entry 5 trading days later | 10 | +15.25% | -8.07% | 40.0% |
| Wasserman Schultz | Debbie Wasserman Schultz | stock purchases | 126 | entry 30 calendar days later | 10 | +30.36% | +7.32% | 60.0% |

## Limits

- Tickers with no bars are left out and counted. Many are foreign shares sold over the counter, mutual funds, preferreds, and old tickers of companies that were renamed. The price source keeps a renamed company's history under its new ticker, so events under the old ticker have no price. UNKNOWN how much this moves the result.
- Ticker reuse (an old ticker given later to another company) was not checked. UNKNOWN.
- The filing day is the day the report was received. It is not proof of when the public could read it; the later entries are there for that.

