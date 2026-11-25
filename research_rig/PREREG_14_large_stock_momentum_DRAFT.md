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
