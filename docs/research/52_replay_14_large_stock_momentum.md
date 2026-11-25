# Replay 14: plain momentum on large stocks, held a month at a time

MEASURED 2026-11-25 22:39:55 UTC by `research_rig/score_14.py --run`, one run, commit `a54da056823f`. Plan: `research_rig/PREREG_14_large_stock_momentum.md`. Ledger rows 146 and 147. Pretend trades on past prices, after costs. Not advice and not a forecast.

## Answer

- Set-up N = 10 (ledger row 146): FAILS (1 of 4 marks hold). MEASURED.
- Set-up N = 50 (ledger row 147): FAILS (1 of 4 marks hold). MEASURED.

A pass means: worth running on the practice desk with pretend money as a slow sleeve, and the rule becomes the yardstick for AI stock pickers. It does not mean it makes money. STATED in the plan.

## Period and data

- Ranking days: 118, from 2017-01-31 to 2026-10-30. First purchase at the open of 2017-02-01; held to the close of 2026-11-24. MEASURED.
- Second half starts with the ranking day 2022-01-31. MEASURED.
- Member lines on a month-end: 503 to 505; after keeping one share class per company and dropping lines with no price file: 495 to 501. MEASURED.
- Stocks that could be ranked on a ranking day: 492 to 500; that could not (no close on one of the two month-ends): 0 to 7. MEASURED.
- Gap: member lines with no price on any of their days, by year: 2016 7, 2017 1, 2018 2, 2019 3, 2020 0, 2021 0, 2022 0, 2023 0, 2024 0, 2025 0, 2026 0. Every rule and yardstick b miss these alike. MEASURED.
- Gap: member lines with prices whose prices stop before their removal day: 50 (17 by 1 trading day, 15 by 2 trading days, 14 by 3 trading days, 3 by 4 trading days, 1 by 5 trading days); most are takeovers whose last trade was a few days before removal. MEASURED.
- Gap: lines with no bar at all inside their membership, also counted above by year: TFCF (to 2019-03-20), TFCFA (to 2019-03-20). MEASURED.
- Gap: 7 companies have their history in more than one price file. Files are not joined, so the history restarts and the stock cannot be ranked until the new file has twelve month-ends (plan rule). MEASURED:
  Andeavor: files TSO, ANDV; restarts 2017-08-01.
  Aptiv: files DLPH, APTV; restarts 2017-12-05.
  Skydance: files CBS, VIAC, PARA@2023-06-01, SKYD; restarts 2019-12-05, 2022-02-17, 2025-08-07.
  Howmet Aerospace: files ARNC, HWM; restarts 2020-04-01.
  Bath & Body Works, Inc.: files LB, BBWI; restarts 2021-08-03.
  Coterra Energy: files COG, CTRA; restarts 2021-10-04.
  Dayforce: files CDAY, DAY; restarts 2024-02-01.
- Data check, flat zero-volume runs of five sessions or more inside a row's window: 0 rows. MEASURED.
- Data check, file not the same stock as the feed's file for that ticker on the row's first day: 8 rows: BNY@2026-05-21, CB@2016-01-04, META@2022-06-09, TFCF@2019-03-19, TFCFA@2019-03-19, DOC@2024-03-04, IR@2020-03-03, CZR@2021-03-22. Each is listed with a reason in the plan. MEASURED.
- Data check, one company counted twice: 0 rows. MEASURED.
- Inputs: members.csv sha256 `b41774f515c94079`, 732 price files sha256 `4b39929e7bdbec22`, config sha256 `a69c3d5a738ca00b`. Full fingerprints in `research_rig/results_14.json`.
- Adjustment: on five dividend payers and three companies with spin-offs, the feed's adjusted close is the raw close times a factor that stays constant between the feed's listed ex-dates and steps on them, spin-offs included (research_rig/check_adjust_14.py, before the run). MEASURED. Vendor errors in single corporate actions remain possible.

## The four marks, after costs

Cost 5 basis points per side on what is traded. SPY pays one buy and one sell. STATED in the plan. As built, what is traded at a re-form is the sum of the changes in each stock's share of the account before the fee is taken; an exact trade-by-trade fee differs by a few millionths of the account. A held stock with no open at a re-form is carried at its last close, not traded.

### N = 10

| mark | this set-up | yardstick | result |
|---|---|---|---|
| 1. Ends the whole period above SPY | +203.8% | SPY +264.6% | fail |
| 2. Ends above every member in equal parts (yardstick b) | +203.8% | every member +190.5% | pass |
| 3. Ends above the set percentile of random baskets (yardstick c) | +203.8% | 95th percentile of 1000 random baskets that keep as many names each month as the rule kept +314.1% (median +175.3%) | fail |
| 4. Above SPY in each half taken apart | first +22.1%, second +148.9% | SPY first +114.7%, second +69.8% | fail |

Gaps next to this result: 3 holdings were sold at a last close because their prices stopped (flagged); 0 times a held stock had no open at a re-form and was carried at its last close; 0 months had fewer than 10 stocks with an open to buy; it beat 64% of random baskets. Without every flagged stock, removed from the start (uses hindsight, reported only): +194.2%. MEASURED.

### N = 50

| mark | this set-up | yardstick | result |
|---|---|---|---|
| 1. Ends the whole period above SPY | +207.8% | SPY +264.6% | fail |
| 2. Ends above every member in equal parts (yardstick b) | +207.8% | every member +190.5% | pass |
| 3. Ends above the set percentile of random baskets (yardstick c) | +207.8% | 95th percentile of 1000 random baskets that keep as many names each month as the rule kept +235.3% (median +178.5%) | fail |
| 4. Above SPY in each half taken apart | first +73.4%, second +77.5% | SPY first +114.7%, second +69.8% | fail |

Gaps next to this result: 15 holdings were sold at a last close because their prices stopped (flagged); 0 times a held stock had no open at a re-form and was carried at its last close; 0 months had fewer than 50 stocks with an open to buy; it beat 81% of random baskets. Without every flagged stock, removed from the start (uses hindsight, reported only): +203.4%. MEASURED.

## Reported, not judged

| year | N small | N wide | every member | SPY |
|---|---|---|---|---|
| 2017 | +4.6% | +15.9% | +15.9% | +19.2% |
| 2018 | -19.0% | -6.8% | -8.0% | -5.0% |
| 2019 | +33.7% | +22.4% | +30.3% | +31.1% |
| 2020 | +4.6% | +16.2% | +12.1% | +18.5% |
| 2021 | +7.8% | +17.8% | +29.9% | +28.6% |
| 2022 | +13.9% | -2.3% | -11.2% | -18.2% |
| 2023 | +21.5% | +9.4% | +14.7% | +26.2% |
| 2024 | +19.9% | +28.8% | +12.6% | +24.9% |
| 2025 | +26.5% | +14.9% | +11.3% | +17.7% |
| 2026 | +13.2% | +7.6% | +12.5% | +6.2% |

- Largest drop from a high, daily closes: N small -52.7%, N wide -36.2%, every member -39.7%, SPY -33.8%. MEASURED.
- Share of the basket changed at a re-form, average: N small 72%, N wide 62%, every member 6%. MEASURED.
- For scale, the same days, one buy and one sell: SPMO +394.3%, MTUM +251.5%. MEASURED.
- Overlap with SPMO's holdings: UNKNOWN: no dated public record of SPMO's holdings was found.

## How often a mark passes by chance

MEASURED by `research_rig/test_14.py` on 400 made-up price sets with no momentum in them, run through the same scorer, written 2026-11-25 21:48 UTC. Passes, out of 400:

| mark | N small, 5 bps | N wide, 5 bps | N small, 0 bps | N wide, 0 bps |
|---|---|---|---|---|
| 1. Ends the whole period above SPY | 138/400 | 147/400 | 156/400 | 181/400 |
| 2. Ends above every member in equal parts (yardstick b) | 138/400 | 134/400 | 155/400 | 167/400 |
| 3. Ends above the set percentile of random baskets (yardstick c) | 18/400 | 18/400 | 18/400 | 18/400 |
| 4. Above SPY in each half taken apart | 65/400 | 61/400 | 71/400 | 78/400 |
| All four | 17/400 | 16/400 | 17/400 | 16/400 |

Share of random paths beaten, mean and variance (a fair yardstick gives 0.5 and 0.083): 5 bps: N small 0.472 / 0.083, N wide 0.461 / 0.081; 0 bps: N small 0.472 / 0.083, N wide 0.461 / 0.081. MEASURED.

## How this can fool us

- Ten years, one long rising market with two sharp falls. Momentum rules are known to fall hard when a market turns. STATED in the plan.
- The member list is rebuilt from a public record of changes and checked against a second one; disagreements are listed off-repo in members_note.md. A missed change puts a stock in or out on the wrong days.
- Stocks with no price are left out of every rule alike; the counts are above.
- A basket of stocks that all rose for the same reason is close to one bet.
