# 47. Replay 12: following stock purchases disclosed by members of Congress

Status: research result, pretend trades on past prices. Built by `research_rig/report_12.py` from `research_rig/prices_12_summary.json` and `research_rig/events_12_summary.json`. The plan is `research_rig/PREREG_12_congress_followers.md`; its numbers are in the config key `replay_12_plan`. The design half is not scored yet. The held-back half is not scored yet, so there is no verdict yet.

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

## Results

Not scored yet. This page will be rewritten from the result files when they exist.

