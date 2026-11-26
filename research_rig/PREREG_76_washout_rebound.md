# Plan 76: Buy the washout rebound

STATED: Queue 134 and [ledger 229](TRIAL_LEDGER.md) register a price-only spot test of a single coin's hourly fall followed by a roughly one-day hold. The old queue 28 fee is not used. This is the same buy-after-a-fall family as E09 and E11, counted once. Those cards hold one to two hours and also require a Bitcoin fall. Plans 70 and 71 did not search this plain single-coin drop at a 12- or 24-hour hold.

## Source and limits

STATED: Source pending the lead agent's ruling on ledger 229. The scorer accepts ordinary US dollar spot hourly bars, not stablecoin quotes, perpetuals, futures or a converted proxy approved by the builder. Any venue whose bars stand in for another venue's reachable price must be named and the limitation recorded before use. [The custody contract](COLLECTOR_76.md) specifies the source-neutral format. Do not touch the sealed Plan 70 vault, repurpose Plan 75 inputs, or use raw bars or snapshots in Git.

STATED: The 20 coins were chosen with hindsight. Use the Plan 75 roster and [doc 172's full-trading intervals](../docs/research/172_us_spot_access_dates_20_coins.md), not an assumption that prices prove access. AAVE, ADA, AVAX, BCH, BNB, BTC, DOGE, DOT, ETH, HBAR, LINK, LTC, NEAR, PEPE, SHIB, SOL, SUI, XLM, XRP and ZEC remain the roster even when a name has no admissible or available observations. DOT is never admitted; BNB and PEPE are not admitted in the design years; XRP's restrictions and return, ZEC's removal, and the doc's all-coin May 2026 closed day are in the frozen config. Access flags are daily UTC approximations, not a complete intraday incident history. Confirm identity, not just ticker.

STATED: [Round 66's second check](../docs/research/192_round_66_crypto_hype_and_reversal.md) notes three public versions of forced-selling rebounds lost after fees. [Miralles-Quirós and Miralles-Quirós, Table 2](https://www.econstor.eu/bitstream/10419/314207/1/1841191159.pdf), report a 24-hour gross rebound of 3.132% after a 5% shock and 2.299% after a 3.5% shock. That paper used Bitcoin on Kraken in 2016–2021, starts at the signal close, uses overlapping windows, reports no count for each trigger and includes no costs. This is not evidence that the same gross mean is reachable on these coins. The expectation, written before any price, is that the main-cost line fails.

STATED: An hourly open is the bucket's first print, not an order fill available to a bot. [Plan 73](../docs/research/157_plan_73_first_minute_diagnosis.md) lost about half its searched gain at the one-minute comparison and used different, already-selected trades. A more conservative clock is shown here, not judged. The 15 bp line is a hypothetical cheaper venue; execution there can only be measured forward on Binance.US books.

## The frozen book

STATED: Use consecutive hourly closes for the signal. The fall is the plain percentage change, current close divided by previous close minus one. A fall of at least 5% qualifies for the primary line; 3.5% is shown only unless the count branch switches the judged arm. Compare without rounding. No gap-filling or stale data. Both signal closes and the next scheduled open must fall inside the modeled full-trading interval. At an eligible open, choose the largest faller; resolve an exact tie alphabetically. If that winner lacks an open, skip rather than substitute the runner-up. The signal hour is the last closed bucket; buy at the next bucket's open.

STATED: One position at a time across all coins. Sell at the open 24 hours after entry. If the open is missing or restricted, hold to the first later full-trading hourly open with a bar. No new position until sale; sale then new buy at the same hourly open is allowed. The 12-hour book reruns the identical rules with its own shorter occupancy and is shown only. The shown-only delayed entry takes the original ticket's entry-bucket close, the close of the first hour after the signal, and sells at exactly the original exit. If that close is absent, report it missing rather than reschedule or replace the ticket.

STATED: Net per trade is sale price divided by entry price, multiplied by ((1-f)/(1+f)), minus one. The fee (f) is 75 bp a side for the main line and 15 bp a side for the cheap line. A proportional charge applies on both actual sides; no funding, leverage, compounding, price impact claim or capacity claim. Report the equal-weight mean across completed trades, not total portfolio return.

## Three separate stages

- **Count, January 1, 2020 through December 31, 2023 UTC:** Count uses chronological adjacent closes and scheduled lockout, no peeking at entry/exit bars; assigns UTC entry year and refuses boundary tickets that cannot finish scheduled hold inside fence. Each candidate is decided from its own signal hour and earlier closes only; the input has no opens. A different later signal may use its own closed bars. Each arm has its own all-coin occupancy. Judge 5% if at least 30 non-overlapping trades are counted in each of 2022 and 2023; otherwise judge 3.5% if it reaches the same floor in both years; otherwise close on count.
- **Design, same 2020–2023 fence:** Go-on check only. Use only the frozen arm selected by count for the branch: go on if its mean is strictly above zero at main cost or at the cheap line. Print every other output as shown only; never select an arm, fee, delay, coin or alternate horizon here. The shown alternate arm, 12-hour book, late-entry clock and other marks do not decide this stage.
- **Held-back, from January 1, 2024 UTC:** Use one newly prepared custodian copy. The exclusive UTC end is the confirmed published-source cutoff recorded in a signed manifest before decoding. No carryover state or warm-up across either fence, and no out-of-fence bars anywhere in the tape. Real scorer holds through missing/restricted exits until first later full-trading open; unresolved at fence excluded and blocks new entries to fence. Print both fence counts: free-slot nominations refused because the scheduled exit would be beyond the fence and opened positions unresolved there. The count stage also prints fence refusals but cannot check real unresolved exits, so that field is null there.

STATED: The delayed close shown-only keeps primary portfolio and exit timestamps. It is not a new calendar or parameter search. All stage outputs are aggregate only. Count numbers are proposed slots, not completed fills.

## Held-back controls and result

STATED: Match each completed trade exactly on coin/UTC entry hour-of-week, build full random portfolios with identical entry/exit admissibility and no overlapping intervals; seeded draws with fixed finite retry cap; if no full benchmark, rank mark cannot pass. Hour-of-week begins Monday 00:00 UTC. For each real ticket the candidate pool comprises that coin's full-trading observed opens in its exact hour-of-week within the held-back fence, with a completed sale under the same scheduled hold and delayed-sale rule. No fall is required and the real entry date can be drawn. The controls do not use signal size or returns to select dates.

STATED: Sort the strata for pool construction and keep candidate dates chronological. Initialize Python's seeded random generator once with seed 760229. For each of 999 books, shuffle the order of the real ticket strata, including multiplicity. For each item, take the first non-overlapping entry and exit interval in a fresh, uniformly random permutation of its pool. Touching endpoints are legal. If any item fails, discard the whole attempted book and retry, up to 20 attempts for that book. If any book still cannot be drawn, the full benchmark is unavailable; do not pass the rank mark or relax the constraints. Book dates may repeat across draws; within a book, no intervals overlap across any coins. This is randomized sequential placement, not a uniform draw from the space of all possible valid complete calendars. Match neither return, year nor market state beyond those fixed conditions.

STATED: At each fee, the same completed tickets, seeded books, costs and four marks apply. The main line judges:

- **Positive:** Mean net per trade strictly above zero.
- **Matched:** The strategy's mean net strictly exceeds the mean net of more than 90% of the full random books. Ties are not wins.
- **Trimmed:** Mean is still strictly positive after removing the best net trade in every represented UTC entry year. A one-trade year contributes nothing to this trimmed mean; an empty remainder fails.
- **Count:** At least 64 completed trades. Below that, close on count regardless of either line's other marks.

STATED: Clearing all main marks earns a forward card only. If only the 15 bp line clears all four, the outcome is “forward card on Binance.US books, not a counted pass.” Otherwise the plan does not pass. No result authorizes real money.

## Invented-data power

STATED: `power_76.py` puts zero, half or all of each published gross mean on made-up 24-hour returns for the respective branch. It conditions on completed counts of 64, 96 or 144, roughly evenly split over three entry years, with Student-t noise (five degrees of freedom) scaled to residual standard deviation of 4%, 5% or 6% before truncation, and a 0.6%-SD regime shift shared by all trades in a year. Residuals are clipped at ±80% for bounded arithmetic. Controls share the same year mix and regime shocks; their portfolio-mean residual is approximated by a normal with SD equal to the per-trade residual SD divided by the square root of count. Each scenario uses 2,000 worlds and the fixed seed in config. That makes the model conditional on having enough signals, executable exits and complete random books; it does not estimate how often any of those conditions holds. It does not model the hourly open losing any of the paper's edge. Full-edge results are a favorable sensitivity, not a forward expectation.

UNKNOWN: Actual count, matched-calendar coverage, average returns, power under real dependence, and fill quality. No price has been opened for this plan.

MEASURED, simulation only: The table gives the share of worlds clearing all four marks at the middle (5%) residual SD. Each cell is main / cheap cost. Zero and full are included to show the consequences of the most pessimistic and favorable edge assumptions; the half-paper main-cost result is 26.60% at the 64-trade floor for the primary arm and 10.65% if the alternate is selected.

| Count | Arm | No edge | Half paper | Full paper |
| ---: | --- | ---: | ---: | ---: |
| 64 | 5% | 0.20% / 6.50% | 26.60% / 85.30% | 95.00% / 100.00% |
| 64 | 3.5% | 0.20% / 6.50% | 10.65% / 64.75% | 68.30% / 98.20% |
| 96 | 5% | 0.05% / 7.75% | 31.30% / 92.20% | 98.20% / 100.00% |
| 96 | 3.5% | 0.05% / 7.75% | 12.85% / 75.15% | 76.35% / 99.75% |
| 144 | 5% | 0.00% / 5.95% | 34.15% / 96.05% | 99.30% / 100.00% |
| 144 | 3.5% | 0.00% / 5.95% | 11.65% / 84.05% | 83.35% / 99.95% |
