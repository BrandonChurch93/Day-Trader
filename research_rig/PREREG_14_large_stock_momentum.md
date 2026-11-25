# Pre-registration 14 (draft): plain momentum on large stocks, held a month at a time

Status: DRAFT written 2026-11-25 18:55 UTC by the builder, before any price was collected for it. It becomes final when the code has been checked by a second model and this line is changed to "frozen" with the time. Ledger rows 146 and 147 in `research_rig/TRIAL_LEDGER.md`. Pretend trades on past prices. No AI model takes part.

## The claim

The owner, 2026-11-25 (`docs/DECISIONS.md`): big stocks are for holding weeks or months, and he wants that explored beside day trading. Of the well-known ways to pick such stocks, one has a real-money fund ahead of SPY in our own measurement: holding the large stocks that rose most over the past year (`docs/research/51_stock_swing_evidence_checked.md`). The claim tested: a plain version of that rule, with a number of stocks a small account can hold, beats SPY after costs.

This is also built as a yardstick. Our AI stock pickers bought what had already risen and did not beat random baskets (`docs/STATUS.md`). If a one-line rule does the job, an AI picker has to beat the rule, not just the market.

## What is known before the test

- MEASURED: SPMO made +442.5% against SPY +325.8% from January 2016 to 2026-11-24 and was ahead in 6 of 11 calendar years. MTUM, a similar fund, was behind SPY over the same days.
- STATED in the checked reading: the published lead of SPMO is not clear of chance (t = 1.01), and the long-run academic momentum result is weaker after 2002.
- SPMO's own rule is not the plain one: it adjusts each stock's rise for how much it swings, weights by company size, and re-forms twice a year. This plan tests the plain rule, so a fail here does not say SPMO's rule fails.
- The expectation written down first: uncertain. Ahead of SPY over the whole period is more likely than not; clearing the random-basket mark is less likely than not.

## Data

- Which stocks were in the S&P 500 on each date, rebuilt from the public record of additions and removals. A stock is in the list only from the day it was added until the day it was removed.
- Daily prices with splits and dividends from our price feed, `replay_14_plan.start` to `replay_14_plan.end`. The feed starts in January 2016, so the first ranking day is twelve months later.
- Renamed companies are mapped the same way as in plan 12. A member with no price is left out and counted by year.
- Raw prices stay on the research machine.

## The rule

On the last trading day of each month, for every stock in the list that day, take its gain over the `replay_14_plan.lookback_months` months before, leaving out the most recent `replay_14_plan.skip_months` month. Buy the top N in equal parts at the next trading day's open and hold until the next month's re-form.

- Set-up 1 (ledger 146): N = `replay_14_plan.n_small`. What a small account can hold.
- Set-up 2 (ledger 147): N = `replay_14_plan.n_wide`. Closer to a fund.

Cost: `replay_14_plan.cost_bps_per_side` per side on what is traded at each re-form. A stock whose prices stop inside a month is sold at its last close, flagged and counted.

## Yardsticks

- (a) SPY held, with dividends.
- (b) Every stock in the list held in equal parts, reset monthly, same cost. Equal parts of 500 stocks is not the same as SPY, so both are needed.
- (c) `replay_14_plan.random_draws` random paths of N stocks, seed `replay_14_plan.seed`, drawn from the stocks the rule could rank that month that have an open on the purchase day. On the first ranking day each path draws N. At each later re-form a path keeps exactly as many of its holdings as the rule kept that day (fewer if it has fewer eligible holdings left), chosen at random, and draws the rest at random from the eligible stocks it did not hold. Same costs and stop handling as the rule.
- For scale, not judged: SPMO and MTUM.

## What would count, fixed now

Each set-up is judged on its own. It passes when all four hold, after costs:

1. It ends the whole period above SPY.
2. It ends the whole period above yardstick (b).
3. It ends above the `replay_14_plan.random_percentile`th percentile of yardstick (c).
4. It ends above SPY in each half taken apart: ranking days up to `replay_14_plan.first_half_end`, and after.

No set-up is chosen after the fact; both are counted as trials. A pass means: worth running on the practice desk with pretend money as a slow sleeve, and the rule becomes the yardstick for AI stock pickers. It does not mean it makes money. Reported and not judged: each calendar year, the largest drop against SPY's, turnover, the result without flagged stocks, and how the top N overlap with what SPMO held where that is public.

## How often this passes with no edge

Measured 2026-11-25 21:48 UTC on 400 made-up worlds with no edge built in, before any return on real prices (`research_rig/noedge_14.json`), with the turnover-matched yardstick (c). Out of 400, at the plan's cost: mark 1 passed 138 (N small) and 147 (N wide), mark 2 138 and 134, mark 3 18 and 18, mark 4 65 and 61, all four 17 and 16. At zero cost: mark 1 156 and 181, mark 2 155 and 167, mark 3 18 and 18, mark 4 71 and 78, all four 17 and 16. The share of random paths beaten averaged 0.47 and 0.46 with the spread of a uniform draw, at both costs. So one set-up passes all four by luck about 4 times in 100; with two set-ups the chance that at least one does is higher. An earlier yardstick that redrew every name each month gave mark 3 a head start from lower turnover (30 and 36 of 400 passed mark 3 with it); it was replaced before the freeze. A pass will be reported with these figures next to it.

## Definitions fixed before the run

Written 2026-11-25 19:00 UTC after the code builder read the draft and listed what it left open. No price had been collected.

- Month-end: the last trading day of SPY in a calendar month. The gain used for ranking on a month-end is the close one month-end before, divided by the close twelve month-ends before, minus one. Both closes must exist on those exact days; a stock without them cannot be ranked that month and is counted.
- First ranking day 2017-01-31, first purchase at the open of 2017-02-01. Last ranking day 2026-10-30, held to the close of 2026-11-24. The final sale is charged like any other, for the rule and for every yardstick, SPY included.
- Member days: from the day added up to, not including, the day removed. A stock removed in the middle of a month stays held until the next re-form.
- Two share classes of one company (for example GOOG and GOOGL): only the first by ticker in alphabetical order can be ranked or drawn, in the rule and in every yardstick, so a basket does not hold one company twice.
- Yardstick (b) holds every member that has a close on the ranking day and an open on the purchase day. Yardstick (c) is drawn as described under Yardsticks, tickers sorted before drawing. "Above" means strictly above.
- Inside a month the parts drift with prices. At each re-form they are reset to equal. The cost is charged on the sum of the differences between the new parts and the drifted parts; the first purchase counts as all of it traded.
- A stock in the top N with no open on the purchase day is skipped for the next one down.
- A held stock whose prices stop is sold at its last close, flagged, charged the cost on that day, and that money sits in cash until the next re-form. A gap with prices later is carried at the last close. A held stock with no open on a re-form day but prices later is carried through that re-form at its drifted size, neither sold nor added to, and counted.
- Halves: the first half is every holding formed on ranking days up to `replay_14_plan.first_half_end`; the second is the rest. SPY is measured over the same open-to-open spans.
- A renamed company keeps one history where the feed keeps it in one file. Where it is in two files they are not joined, and the stock cannot be ranked until the new file has twelve month-ends: Andeavor (TSO; ANDV from 2017-08-01), Aptiv (DLPH; APTV from 2017-12-05), Paramount (CBS; VIAC from 2019-12-05; PARA from 2022-02-17; SKYD from 2025-08-07), Howmet (ARNC; HWM from 2020-04-01), Bath & Body Works (LB; BBWI from 2021-08-03), Coterra (COG; CTRA from 2021-10-04), Dayforce (CDAY; DAY from 2024-02-01). A takeover or merger into a new company ends the old history; the new company joins as new and cannot be ranked until it has twelve month-ends.
- "Without flagged stocks" removes every stock that was ever flagged from the start. That uses hindsight and is labelled so. Overlap with SPMO's holdings is printed only if a dated public record of them is found; otherwise UNKNOWN. Adjustment, measured before the run (`research_rig/check_adjust_14.py`): for five dividend payers the adjusted close is the raw close times a factor that is constant between the feed's listed ex-dates and steps on them, and for three companies with spin-offs it also steps on each spin-off date. So gains include dividends and spin-offs. A single wrong corporate action at the vendor remains possible.
- A member's bar with zero volume, or inside a run of five or more rows with identical open, high, low and close, is treated as no bar. A run like that, or a gap of more than five trading days, cuts a file. SPY, SPMO and MTUM are read as they are. Whether a row is inside such a run is known only after the run; this is cleaning of the vendor's padding, applied the same way to the rule and to every yardstick, and it is stated as a limit.
- The run refuses to start while this file is a draft, or unless the four pins under "Pins" match the member list, the bar files, the code and the config as they stand, or while any data check flag has no line under "Data check flags" below. It takes a lock before reading any real price for a return, and refuses a second run.

## Changed before the freeze

Every change below was made on 2026-11-25 between 19:55 and 21:50 UTC, after two code audits by other models and before any return of the rule or of a yardstick was worked out on real prices. The audits used real files only for dates, volumes and whether a bar exists.

- Two trade bugs found by an auditor's own rebuild of the rule on made-up bars: a held stock with no open at a re-form was sold at an old close, and the cost of a stop was charged a day late. Both fixed; wording under Definitions.
- Yardstick (c) replaced. The first version redrew every name each month, traded more than the rule and so started behind it, which let mark 3 pass in 30 and 36 of 400 made-up worlds with no edge. The new version trades as much as the rule. Mark 3 now passes in 18 of 400, near the 20 a 95th percentile gives.
- Frozen bars. The feed pads some files with a last price repeated at zero volume after a takeover or a failure, and one ticker file can hold two companies. The member list was rebuilt with files cut at such runs. Rows whose file now ends at the last real trade: ADT (to 2016-04-29), CA (2018-11-02), CHK (2020-06-26, after removal), DNB (2019-02-07, after removal), DO (2020-04-24, after removal), EMC (2016-09-06), LB (2021-08-02), LLL (2019-06-28), MNK (2020-10-09, after removal), MON (2018-06-06), SE (2017-02-24), XL (2018-09-11), INFO (2022-02-25). Files started after a frozen run: CTRA from 2021-10-04, SMCI from 2020-01-14, EXE from 2021-02-10. Signature Bank (SBNY) ends at its last real trade before the failure through the bar rule above.
- Files changed. Dow: the old Dow Chemical ends 2017-08-31 and the new Dow Inc. starts 2019-04-02. Old DuPont: the plain DD file before 2017-09-01 holds Dow Chemical's bars, so old DuPont reads the feed's file for the company that had the ticker DD on 2017-06-01. Paramount: CBS rows read the CBS file, VIAC rows the VIAC file, PARA rows from 2022-02-17 the feed's file for PARA on 2023-06-01; the plain PARA file has zero volume until 2024.
- A builder bug found while making those cuts: a row starting right after a gap had its file ended before the row (Coterra). Fixed.
- Three data checks added, on dates and volumes only: frozen runs inside a row's window, whether a row's file is the same stock as the feed's file for that ticker on that day, and one company counted twice. Result: frozen 0, counted twice 0, identity 8 flags explained below, and 4 rows the check could not cover (TFCF and TFCFA, never priced while members; NFX, 1 day; UAA 2016-04-08 to 2016-12-06, because the feed maps UA on that day to the class C share).
- Coverage after the rebuild (`research_rig/coverage_14.json`): member lines with no bars by year 2016 7, 2017 1, 2018 2, 2019 3, none after; 50 lines whose prices stop 1 to 5 trading days before the removal date.
- Re-check by the second auditor at 22:20 UTC, on made-up bars and on dates and volumes only: all 10 must-fix items of both audits fixed, 0 not fixed. Its own rebuild of the rule agreed with this code on 20 made-up worlds with gaps, stops and renames. Three notes, none changing a result: the data checks need about 1.1 GB of memory and run again after the lock, so the run is made with that much free; the code pin covers `config/thresholds.yaml`, so no commit touches that file between the pins and the run; the self-test rewrites the no-edge file, which is not pinned, so it is not run again before the run.
- The stored pick labels use the ticker in force that day. The result page shows all 400 no-edge worlds at both costs and lists every company on two files.

## Data check flags

Each flag is a row whose file differs from what the feed returns for that ticker on an earlier day, with the reason it is still the right company.

- BNY@2026-05-21 is the same company because the feed's BNY on 2025-04-16 was another security, and the file matches BK@2025-04-16.
- META@2022-06-09 is the same company because the feed's META on 2021-05-05 was another security, and the file matches FB@2021-05-05.
- DOC@2024-03-04 is the same company because the feed's DOC on 2023-01-29 was Physicians Realty, and the file matches PEAK@2023-01-29.
- IR@2020-03-03 is the same company because the feed's IR on 2019-01-28 was Ingersoll-Rand plc (now TT), and the file matches GDI@2019-01-28 (Gardner Denver).
- CZR@2021-03-22 is the same company because the feed's CZR on 2020-02-16 was the old Caesars, and the file matches ERI@2020-02-16 (Eldorado).
- CB@2016-01-04 is Chubb Ltd because the feed's CB on 2016-01-04 was the old Chubb Corp, and the file matches ACE@2016-01-04.
- TFCF@2019-03-19 and TFCFA@2019-03-19 are one-day rows because the files are cut on 2019-03-18; they are never ranked or held.

## Pins

Filled in at the freeze from `python3 research_rig/score_14.py --pins`. The run refuses unless each matches.

PINS_GO_HERE

## How this can fool us

- Ten years, one long rising market with two sharp falls. Momentum rules are known to fall hard when a market turns.
- The list of members is rebuilt from a public record of changes. A missed change puts a stock in or out on the wrong days.
- Stocks removed from the index because they failed may have no price in the feed. That flatters every stock-picking rule and the equal-parts yardstick alike; the count is printed.
- A top-10 basket of stocks that all rose for the same reason is close to one bet.
- The member list and its price files were chosen with later bars in view: which file a row uses, where a file is cut, and which bars count as frozen padding. That cannot be avoided with this feed. It acts on the rule and the yardsticks alike.
- A stock that fails can stop trading before the feed's last real bar shows the full loss. Such stocks are sold at the last real close, which can be kinder than what a holder got. They are flagged, and the result without flagged stocks is shown.

## Order of work

1. Build the member list by date and collect prices. No return is worked out before this plan is frozen.
2. Code and a self-test on made-up data. A second model checks the code.
3. Freeze. One run. Results stored with the command and input fingerprints.
4. Result page in `docs/research/` and a line in `docs/STATUS.md`.
