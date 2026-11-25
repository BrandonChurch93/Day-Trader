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
- (c) N stocks drawn at random from the list each month, `replay_14_plan.random_draws` draws, seed `replay_14_plan.seed`, each draw carried through the whole period.
- For scale, not judged: SPMO and MTUM.

## What would count, fixed now

Each set-up is judged on its own. It passes when all four hold, after costs:

1. It ends the whole period above SPY.
2. It ends the whole period above yardstick (b).
3. It ends above the `replay_14_plan.random_percentile`th percentile of yardstick (c).
4. It ends above SPY in each half taken apart: ranking days up to `replay_14_plan.first_half_end`, and after.

No set-up is chosen after the fact; both are counted as trials. A pass means: worth running on the practice desk with pretend money as a slow sleeve, and the rule becomes the yardstick for AI stock pickers. It does not mean it makes money. Reported and not judged: each calendar year, the largest drop against SPY's, turnover, the result without flagged stocks, and how the top N overlap with what SPMO held where that is public.

## How often this passes with no edge

Measured 2026-11-25 19:47 UTC on 400 made-up worlds with no edge built in, before any return on real prices (`research_rig/noedge_14.json` holds the first 100): mark 3 alone passed in 30 of 400 worlds for the small basket and 36 of 400 for the wide one, more than the 5 in 100 its percentile suggests. All four marks together passed in 27 and 31 of 400. So one set-up passes by luck about 7 times in 100, and with two set-ups counted the chance that at least one passes by luck is higher than that. The cause is UNKNOWN; a likely one is that the rule picks the stocks that move most, which spreads its results wider than a random basket's. The marks are left as they are. A pass will be reported with this figure next to it.

## Definitions fixed before the run

Written 2026-11-25 19:00 UTC after the code builder read the draft and listed what it left open. No price had been collected.

- Month-end: the last trading day of SPY in a calendar month. The gain used for ranking on a month-end is the close one month-end before, divided by the close twelve month-ends before, minus one. Both closes must exist on those exact days; a stock without them cannot be ranked that month and is counted.
- First ranking day 2017-01-31, first purchase at the open of 2017-02-01. Last ranking day 2026-10-30, held to the close of 2026-11-24. The final sale is charged like any other, for the rule and for every yardstick, SPY included.
- Member days: from the day added up to, not including, the day removed. A stock removed in the middle of a month stays held until the next re-form.
- Two share classes of one company (for example GOOG and GOOGL): only the first by ticker in alphabetical order can be ranked or drawn, in the rule and in every yardstick, so a basket does not hold one company twice.
- Yardstick (b) holds every member that has a close on the ranking day and an open on the purchase day. Yardstick (c) draws from the same stocks the rule could rank that month, a fresh draw each month inside each of the paths, tickers sorted before drawing. "Above" means strictly above.
- Inside a month the parts drift with prices. At each re-form they are reset to equal. The cost is charged on the sum of the differences between the new parts and the drifted parts; the first purchase counts as all of it traded.
- A stock in the top N with no open on the purchase day is skipped for the next one down.
- A held stock whose prices stop is sold at its last close, flagged, and that money sits in cash until the next re-form. A gap with prices later is carried at the last close.
- Halves: the first half is every holding formed on ranking days up to `replay_14_plan.first_half_end`; the second is the rest. SPY is measured over the same open-to-open spans.
- Renamed companies keep one history. A takeover or merger into a new company ends the old history; the new company joins as new and cannot be ranked until it has twelve month-ends. Each such case is listed.
- "Without flagged stocks" removes every stock that was ever flagged from the start. That uses hindsight and is labelled so. Overlap with SPMO's holdings is printed only if a dated public record of them is found; otherwise UNKNOWN. Whether the price feed adjusts for spin-offs is UNKNOWN and is said in the result.
- The run refuses to start while this file is a draft, takes a lock before reading any real price for a return, and refuses a second run.

## How this can fool us

- Ten years, one long rising market with two sharp falls. Momentum rules are known to fall hard when a market turns.
- The list of members is rebuilt from a public record of changes. A missed change puts a stock in or out on the wrong days.
- Stocks removed from the index because they failed may have no price in the feed. That flatters every stock-picking rule and the equal-parts yardstick alike; the count is printed.
- A top-10 basket of stocks that all rose for the same reason is close to one bet.

## Order of work

1. Build the member list by date and collect prices. No return is worked out before this plan is frozen.
2. Code and a self-test on made-up data. A second model checks the code.
3. Freeze. One run. Results stored with the command and input fingerprints.
4. Result page in `docs/research/` and a line in `docs/STATUS.md`.
