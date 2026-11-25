# Time machine plan 05, DRAFT: the model names the stocks to leave out

DRAFT, written 2026-11-25 by the builder. Not final, not run, and no session of it has been made. The lead fixes it; until then nothing here is a mark. The numbers named below are in `config/thresholds.yaml` under `tm05_plan` with status builder. Pretend money.

## What is asked

Can a model that reads a week of prices, company filings and headlines pick out the stocks to avoid, so that the rest of the list held in equal shares does better than leaving out the same number of stocks at random?

The account is always fully invested. TM04 asked the model to pick a few names to hold. This asks the opposite: hold nearly everything and drop a few. A model may find it easier to spot trouble than to spot winners. UNKNOWN whether it can do either.

## Why not use TM04 to judge this

- The TM04 months (`tm04_plan.start` to `tm04_plan.end`) are spent. The adds and drops section of `docs/research/36_time_machine_tm04_stock_basket.md` was looked at after those runs, and this plan was written after reading it. Nothing from those months can count for or against this plan.
- What that section says, looked at after the fact: the names the models dropped fell over the rest of the window about as much as random drops at the same weeks. That is the reason to ask the question cleanly, not evidence for an answer.

## Which dates are fresh

MEASURED on the tape on 2026-11-25, `tm04_plan.symbols` only:

- Minute bars for all 38 stocks start on 2026-04-01. Daily bars start on 2024-01-02, so the one-month and three-month changes in the packet can be worked out from the first wake.
- Headlines and filings are on the tape from 2026-04-01. In April and May there are fewer broker headlines a week than in June to November (about 240 against about 380), and about the same number of filings and other headlines.
- The tape ends with the 2026-11-24 session.

So the only fresh months already on the tape are April and May 2026, before the first TM04 wake. That gives 9 weekly wakes, too few alone. This draft adds a forward stretch that has not happened yet.

| Stretch | Dates | Weekly wakes | On the tape now | Why fresh |
|---|---|---|---|---|
| A | `tm05_plan.stretch_a` (2026-04-01 to 2026-05-29) | 9, MEASURED with the tool's wake rule | yes | before TM04. No TM session used it. STATED, not checked: no one on the team has studied these weeks' stock moves. It is after every model's stated latest month in `docs/research/31_model_knowledge_lines.md`, but that test was of crypto prices, so for stocks it is UNKNOWN. |
| B | `tm05_plan.stretch_b` (2026-11-30 to 2027-02-26) | 13, counted by hand from the exchange calendar, not yet on the tape | no | after today, so no model, no list choice and no one on the team can know it. |

What must be collected for stretch B:

- `timemachine/record.py` run after every session day from 2026-11-30 to 2027-02-26: 1Min and 1Day bars for the 38 stocks and SPY, the broker headlines, the other news source and SEC filings, as for TM04.
- A check after the last day that no session day is missing, by the tape tests.
- One half day to watch: 2026-12-24 closes early, so that week's wake at `tm05_plan.wake_time_ny` falls after the close and its trades fill at the next regular open. The tool already does this. No change asked.

Stretch A can run as soon as the tool can take this answer. Stretch B runs after 2027-02-26.

Why two stretches and not one long forward test: stretch A can be run now and shows whether the setup works. Stretch B is the clean one. Together about 22 weekly choices, a little fewer than TM04's 25.

## Trader

Card `practice/traders/D03_avoid_list.md`, brief `timemachine/TRADER_BRIEF_WEIGHTS.md` with a short leave-out section added. The same six models as TM04. Each model runs once per stretch (run 1) with a fresh agent. A second run on stretch A only (run 2) shows how much the answer changes; it is not part of the mark.

## Dates, costs, how a session runs

- The list: `tm04_plan.symbols`, the same 38 companies. It was chosen on 2026-11-25 with hindsight, so in stretch A it leans toward companies that did well since. In stretch B it does not: the list is fixed before those months.
- One wake a week: the last regular trading day of the week at `tm05_plan.wake_time_ny` New York time.
- The model names from 0 to `tm05_plan.leave_out_max` stocks to leave out. The desk holds the rest in equal shares and trades only the difference, at the open of the next minute. Naming no stock means hold all 38.
- Between weeks the book drifts with prices. It is put back to equal shares only on a week the leave-out list changes. Keeping last week's list is free.
- Costs per side: the spread `tm_stock_half_spread_bps` on what is traded. No fee.
- The account starts in cash. The first book is bought at the first wake.
- For every stock it adds to or takes off the leave-out list, the model writes one plain line of reason and marks what drove it: price, filing, headline, or more than one.

## Yardsticks

1. Judged: random leave-outs. `tm_weights_twin_draws` runs in which each week the same number of stocks is left out as the model left out, and, on a week the model changes its list, as many names change as the model changed, drawn at random from the list, with the same costs. This is the existing `random_basket` twin applied to the stocks held.
2. Printed, not judged: all 38 in equal shares bought at the first wake and held (`hold_equal_weight`).
3. Printed, not judged: SPY held, for scale only.
4. Printed, not judged: the model's own lists in shuffled order (`shuffle_runs`), as in TM04.

## What would count, a draft for the lead to fix

For one model: the sum of its run 1 gains over stretches A and B is above percentile `tm_weights_pass_percentile` of the summed random leave-outs. Draw i of stretch A is added to draw i of stretch B, as `timemachine/score_weights.py --sum` does. A tie counts against the model.

For the method, on run 1: at least `tm05_plan.method_min_models_above_median` of the six models end above the median of their summed random leave-outs, and at least `tm05_plan.method_min_models_above_percentile` above the pass percentile. Fewer, and it is reported as not shown.

Stretch A alone is reported as it comes in, marked as a part. No verdict is given until stretch B is in.

## What the weights tool needs

`timemachine/weights.py` cannot run this as it stands. Three changes, none to TM04 behaviour:

- A leave-out answer. Today a basket session takes weights and checks that exactly `basket_size` names have equal shares. Here the model would have to type 30 to 38 shares like 1/33 that add to one. Proposed: a session flag `leave_out_max`. The answer is a list of names to leave out, from 0 to that many, plus reasons. The desk turns it into equal shares of the rest. The packet shows the standing leave-out list.
- The smallest change. Equal shares of 30 to 38 names are about 0.026 to 0.033, below `tm_weights_min_change`. Today a stock added back from the leave-out list would not be bought and the cash would sit idle. Proposed: the session takes `tm05_plan.min_change` in place of `tm_weights_min_change`, and the draft value is zero. The cost is still the spread on what is traded, so small trades cost little.
- The book re-spread only when the list changes, as described above. Today an answer with the same target as last week trades nothing, and a changed target brings every name to its new share. That is already the rule, so this needs only a test.

What the scorer needs:

- `random_basket` already keeps the count each week and swaps as many names as the model. It needs a test that it does so when 30 to 38 names are held.
- A `timemachine/score_tm05.py` in the manner of `score_tm04.py`, summing the two stretches per model as `score_tm03.py` does months.

## How this can fool us

- About 22 weekly choices over two short stretches. One sector moving can decide it.
- Leaving out 8 of 38 changes the book less than holding 8 of 38. The model's result and the random ones will sit close together, so a real but small skill may not show at this length. A pass earns a longer test; it is not proof.
- Stretch A sits right after the stated memory line of some models. A model that half remembers April 2026 would look skilled. Stretch B cannot have this problem.
- In stretch A the list leans toward later winners. Random leave-outs share the lean, SPY does not.
- Fills are assumed from recorded minute bars at the assumed spread. The no-web rule is by instruction.
