# Time machine plan TM04: six AI models pick which stocks to hold

Made by `timemachine/score_tm04.py` from `timemachine/results_tm04.json`. Do not edit by hand. Pretend money. The plan, with its pass mark fixed before any session ran, is `timemachine/PLAN_TM04_stock_basket.md`.

Sessions in: 11 of 12 are finished and scored here. Still running: 1. Not started: 0. Those are left out until they finish.

## What was asked

- Can a model that reads a week of prices, company filings and headlines choose a basket of stocks that does better than baskets drawn at random from the same list?
- The account is always fully invested, so the test is of choosing, not of timing or of how much to hold.

## How it ran

- Each model follows the card `practice/traders/D02_stock_basket.md` and the brief `timemachine/TRADER_BRIEF_WEIGHTS.md`. One session per model covers the whole period. Each model runs twice with fresh agents, run 1 and run 2.
- The list is `tm04_plan.symbols`. The period is `tm04_plan.start` to `tm04_plan.end`.
- One wake a week, on the last regular trading day of the week at `tm04_plan.wake_time_ny` New York time. The model names exactly `tm04_plan.basket_size` stocks, held in equal shares. The desk trades only the difference, at the open of the next minute. A change smaller than `tm_weights_min_change` is not traded.
- Costs: the spread `tm_stock_half_spread_bps` on what is traded. The account starts in cash.
- Yardsticks. Judged: equal shares of the whole list held from the first wake, and random baskets (`random_basket`, `tm_weights_twin_draws` draws, swapping as many names each week as the model did). For scale only: SPY held. Also printed and not judged: the model's own baskets in shuffled order (`shuffle_runs`, `shuffle`, `shuffle_decisions`).

## What would count

From the plan, fixed before any session ran.

- For one run: its final gain is above the equal-weight hold of the list and above percentile `tm_weights_pass_percentile` (90.0) of its random baskets. A tie counts against the model.
- For the method, on run 1 of each model: at least `tm04_plan.method_min_models_above_median` (5) runs end above the median of their random baskets and at least `tm04_plan.method_min_models_above_percentile` (2) end above the pass percentile. Fewer, and it is reported as not shown.
- Run 2 is not part of the mark. It shows how much one model's answer changes from run to run.

## Each run

MEASURED, pretend money, in dollars on the account. "Percentile" is the share of random baskets that ended strictly below the run.

| Model | Run | Gain | Equal-weight hold | Random baskets: median | Percentile | Above median | Above pass percentile | Passes | SPY (scale only) |
|---|---|---|---|---|---|---|---|---|---|
| Claude Opus 5.5 | r1 | -$66.83 | -$41.48 | -$39.28 | 34.8 | no | no | does not pass | -$64.86 |
| Claude Opus 5.5 | r2 | -$36.90 | -$41.48 | -$41.14 | 52.6 | yes | no | does not pass | -$64.86 |
| GPT-6.2 Sol | r1 | -$2.69 | -$41.48 | -$39.45 | 68.5 | yes | no | does not pass | -$64.86 |
| GPT-6.2 Sol | r2 | $32.44 | -$41.48 | -$39.73 | 82.4 | yes | no | does not pass | -$64.86 |
| Gemini Neon | r1 | -$106.52 | -$41.48 | -$32.40 | 14.6 | no | no | does not pass | -$64.86 |
| Gemini Neon | r2 | -$147.54 | -$41.48 | -$40.22 | 5.9 | no | no | does not pass | -$64.86 |
| Claude Sonnet 5.5 | r1 | -$52.42 | -$41.48 | -$34.18 | 39.7 | no | no | does not pass | -$64.86 |
| Claude Sonnet 5.5 | r2 | -$103.69 | -$41.48 | -$39.04 | 16.2 | no | no | does not pass | -$64.86 |
| Kimi K3 | r1 | -$123.01 | -$41.48 | -$35.93 | 10.8 | no | no | does not pass | -$64.86 |
| Kimi K3 | r2 | running | | | | | | | |
| Grok 4.7 | r1 | $17.29 | -$41.48 | -$30.35 | 78.0 | yes | no | does not pass | -$64.86 |
| Grok 4.7 | r2 | -$37.35 | -$41.48 | -$35.04 | 48.5 | no | no | does not pass | -$64.86 |

Method, on run 1: not shown. 6 of 6 first runs are in; 2 are above the median of their random baskets and 0 above the pass percentile.

## Not judged

MEASURED. The model's own baskets put in another order: `shuffle_runs` (stretches with the same basket), `shuffle` (week by week) and `shuffle_decisions` (new baskets among the model's change weeks). These test when, not which. Also: names swapped over the run, costs paid, and the largest drop of the run and of the equal-weight hold.

| Model | Run | Shuffled stretches | Week by week | Change weeks | Names swapped | Costs | Largest drop | Equal-weight largest drop |
|---|---|---|---|---|---|---|---|---|
| Claude Opus 5.5 | r1 | 28.8 (median -$29.34) | 41.0 (median -$48.53) | 41.9 (median -$52.84) | 9 | $1.57 | -10.4% | -9.7% |
| Claude Opus 5.5 | r2 | 28.2 (median -$10.87) | 36.8 (median -$22.77) | 53.2 (median -$40.27) | 9 | $1.53 | -8.3% | -9.7% |
| GPT-6.2 Sol | r1 | 8.9 (median $82.71) | 10.9 (median $77.94) | 12.8 (median $60.91) | 17 | $2.51 | -4.1% | -9.7% |
| GPT-6.2 Sol | r2 | 25.7 (median $75.60) | 29.0 (median $69.67) | 42.0 (median $51.04) | 18 | $2.64 | -5.3% | -9.7% |
| Gemini Neon | r1 | 13.3 (median -$32.75) | 17.1 (median -$42.50) | 21.2 (median -$41.79) | 14 | $2.05 | -12.0% | -9.7% |
| Gemini Neon | r2 | 4.2 (median -$18.45) | 5.3 (median -$19.60) | 4.3 (median -$17.49) | 18 | $2.54 | -16.5% | -9.7% |
| Claude Sonnet 5.5 | r1 | 34.2 (median -$34.83) | 42.7 (median -$43.86) | 55.7 (median -$60.15) | 8 | $1.42 | -6.8% | -9.7% |
| Claude Sonnet 5.5 | r2 | 6.0 (median $30.64) | 7.9 (median $11.47) | 8.2 (median $13.98) | 25 | $3.40 | -11.7% | -9.7% |
| Kimi K3 | r1 | 6.2 (median -$4.17) | 7.2 (median -$15.61) | 11.3 (median -$36.48) | 19 | $2.75 | -16.2% | -9.7% |
| Grok 4.7 | r1 | 29.5 (median $41.56) | 36.7 (median $32.89) | 41.6 (median $28.76) | 11 | $1.79 | -5.4% | -9.7% |
| Grok 4.7 | r2 | 22.0 (median -$1.93) | 22.5 (median -$5.19) | 25.9 (median -$3.66) | 11 | $1.77 | -7.5% | -9.7% |

## Run 1 against run 2

MEASURED, for models with both runs finished. Names in common: the mean, over the weeks, of how many of the basket's names the two runs held at the same time.

| Model | Gain, run 1 less run 2 | Names in common each week | Share in common | Percentile, run 1 less run 2 |
|---|---|---|---|---|
| Claude Opus 5.5 | -$29.93 | 5.56 | 0.69 | -17.8 |
| GPT-6.2 Sol | -$35.13 | 6.24 | 0.78 | -13.9 |
| Gemini Neon | $41.02 | 5.76 | 0.72 | +8.7 |
| Claude Sonnet 5.5 | $51.27 | 4.64 | 0.58 | +23.5 |
| Grok 4.7 | $54.64 | 6.08 | 0.76 | +29.5 |

## Adds and drops

Looked at after the fact, not judged, and not part of the plan's mark. It asks whether the stocks a model added had already risen, and whether the stocks it dropped then fell more than any dropped stock would.

- An added stock: its return over the `tm_adds_drops_before_weeks` (4) weekly wakes before it was added, and over the wakes it was held.
- A dropped stock: its return over each count of weekly wakes in `tm_adds_drops_after_weeks` (1, 4, 8) after it was dropped, and to the end of the window.
- "Less the list" is that return minus the mean return of all listed stocks over the same dates.
- Random swaps: at each of the model's swap weeks, the same number of held stocks dropped at random and the same number of stocks not held added at random, `tm_weights_twin_draws` draws. "Random below" is the share of draws whose mean less the list is below the model's.
- The reading says "lower than chance" or "higher than chance" when fewer than `tm_adds_drops_chance_pct` (5) percent of draws reach the model's mean on that side, and "within chance" otherwise. It is a reading aid, not a mark.

### All runs pooled

| Measure | Events | Mean | Random: median | Mean less the list | Random: median less the list | Random below | Reading |
|---|---|---|---|---|---|---|---|
| added stock, weeks before it was added | 159 | +11.46% | -0.40% | +11.25% | -0.61% | 100.0% | higher than chance |
| added stock, while held | 159 | -1.08% | -2.18% | +1.67% | +0.56% | 82.6% | within chance |
| dropped stock, 1 week after it was dropped | 159 | -0.03% | +0.01% | -0.54% | -0.49% | 42.4% | within chance |
| dropped stock, 4 weeks after it was dropped | 141 | +0.26% | -0.38% | -0.56% | -1.20% | 87.2% | within chance |
| dropped stock, 8 weeks after it was dropped | 124 | +2.22% | -0.22% | -0.18% | -2.61% | 100.0% | higher than chance |
| dropped stock, to the end of the window | 159 | -8.73% | -10.02% | -2.13% | -3.42% | 86.8% | within chance |

### Claude Opus 5.5, both runs

| Measure | Events | Mean | Random: median | Mean less the list | Random: median less the list | Random below | Reading |
|---|---|---|---|---|---|---|---|
| added stock, weeks before it was added | 18 | +12.16% | +0.28% | +11.80% | -0.08% | 100.0% | higher than chance |
| added stock, while held | 18 | +0.44% | -3.18% | +5.10% | +1.46% | 84.1% | within chance |
| dropped stock, 1 week after it was dropped | 18 | -0.91% | +0.31% | -1.97% | -0.75% | 8.1% | within chance |
| dropped stock, 4 weeks after it was dropped | 16 | +0.57% | -0.25% | -0.13% | -0.95% | 68.3% | within chance |
| dropped stock, 8 weeks after it was dropped | 15 | +2.69% | +0.25% | +0.05% | -2.40% | 82.8% | within chance |
| dropped stock, to the end of the window | 18 | -10.52% | -13.05% | -3.67% | -6.22% | 74.6% | within chance |

### GPT-6.2 Sol, both runs

| Measure | Events | Mean | Random: median | Mean less the list | Random: median less the list | Random below | Reading |
|---|---|---|---|---|---|---|---|
| added stock, weeks before it was added | 35 | +10.73% | -0.64% | +10.26% | -1.11% | 100.0% | higher than chance |
| added stock, while held | 35 | +1.32% | -2.56% | +3.78% | -0.11% | 96.6% | higher than chance |
| dropped stock, 1 week after it was dropped | 35 | -0.52% | +0.03% | -0.60% | -0.05% | 18.0% | within chance |
| dropped stock, 4 weeks after it was dropped | 33 | +1.04% | +0.89% | +0.38% | +0.24% | 55.6% | within chance |
| dropped stock, 8 weeks after it was dropped | 27 | +0.96% | +0.73% | -1.09% | -1.32% | 56.2% | within chance |
| dropped stock, to the end of the window | 35 | -9.27% | -5.05% | -2.40% | +1.82% | 3.9% | lower than chance |

### Gemini Neon, both runs

| Measure | Events | Mean | Random: median | Mean less the list | Random: median less the list | Random below | Reading |
|---|---|---|---|---|---|---|---|
| added stock, weeks before it was added | 32 | +15.78% | -0.08% | +15.29% | -0.57% | 100.0% | higher than chance |
| added stock, while held | 32 | -3.73% | -2.20% | -0.78% | +0.74% | 24.0% | within chance |
| dropped stock, 1 week after it was dropped | 32 | +0.94% | -0.29% | +0.37% | -0.86% | 95.6% | higher than chance |
| dropped stock, 4 weeks after it was dropped | 28 | +1.01% | -1.82% | +0.69% | -2.15% | 98.1% | higher than chance |
| dropped stock, 8 weeks after it was dropped | 23 | +4.66% | -1.26% | +2.69% | -3.23% | 99.9% | higher than chance |
| dropped stock, to the end of the window | 32 | -8.78% | -13.55% | -1.76% | -6.53% | 95.1% | higher than chance |

### Claude Sonnet 5.5, both runs

| Measure | Events | Mean | Random: median | Mean less the list | Random: median less the list | Random below | Reading |
|---|---|---|---|---|---|---|---|
| added stock, weeks before it was added | 33 | +10.19% | -0.45% | +9.93% | -0.72% | 100.0% | higher than chance |
| added stock, while held | 33 | -1.67% | -1.26% | +0.25% | +0.67% | 42.6% | within chance |
| dropped stock, 1 week after it was dropped | 33 | +0.91% | +0.23% | +0.13% | -0.55% | 87.7% | within chance |
| dropped stock, 4 weeks after it was dropped | 30 | -0.66% | -0.59% | -1.89% | -1.82% | 48.3% | within chance |
| dropped stock, 8 weeks after it was dropped | 27 | +0.85% | -1.35% | -1.93% | -4.13% | 91.5% | within chance |
| dropped stock, to the end of the window | 33 | -9.51% | -10.62% | -3.14% | -4.26% | 67.2% | within chance |

### Kimi K3, run 1 only

| Measure | Events | Mean | Random: median | Mean less the list | Random: median less the list | Random below | Reading |
|---|---|---|---|---|---|---|---|
| added stock, weeks before it was added | 19 | +12.74% | -0.20% | +12.25% | -0.69% | 100.0% | higher than chance |
| added stock, while held | 19 | -3.83% | -1.26% | -1.55% | +1.02% | 17.9% | within chance |
| dropped stock, 1 week after it was dropped | 19 | -1.28% | -0.41% | -1.10% | -0.22% | 21.5% | within chance |
| dropped stock, 4 weeks after it was dropped | 16 | -1.53% | -1.35% | -2.49% | -2.32% | 45.4% | within chance |
| dropped stock, 8 weeks after it was dropped | 15 | -0.64% | -1.03% | -3.20% | -3.60% | 55.7% | within chance |
| dropped stock, to the end of the window | 19 | -9.63% | -14.03% | -2.96% | -7.37% | 92.7% | within chance |

### Grok 4.7, both runs

| Measure | Events | Mean | Random: median | Mean less the list | Random: median less the list | Random below | Reading |
|---|---|---|---|---|---|---|---|
| added stock, weeks before it was added | 22 | +6.59% | -1.39% | +7.65% | -0.34% | 100.0% | higher than chance |
| added stock, while held | 22 | +0.99% | -2.80% | +3.96% | +0.16% | 89.8% | within chance |
| dropped stock, 1 week after it was dropped | 22 | -0.29% | +0.31% | -1.13% | -0.53% | 16.2% | within chance |
| dropped stock, 4 weeks after it was dropped | 18 | +0.52% | +0.89% | -0.66% | -0.29% | 39.6% | within chance |
| dropped stock, 8 weeks after it was dropped | 17 | +5.21% | +1.63% | +2.65% | -0.94% | 92.8% | within chance |
| dropped stock, to the end of the window | 22 | -4.35% | -6.54% | +1.25% | -0.95% | 73.4% | within chance |

What the pooled table says about drops, in plain words:

- Dropped stock, 1 week after it was dropped: the model's drops moved -0.03%, random drops at the same weeks +0.01% (median). Against the list: -0.54% and -0.49%. 42.4% of random draws did worse than the model's drops. Reading: within chance.
- Dropped stock, 4 weeks after it was dropped: the model's drops moved +0.26%, random drops at the same weeks -0.38% (median). Against the list: -0.56% and -1.20%. 87.2% of random draws did worse than the model's drops. Reading: within chance.
- Dropped stock, 8 weeks after it was dropped: the model's drops moved +2.22%, random drops at the same weeks -0.22% (median). Against the list: -0.18% and -2.61%. 100.0% of random draws did worse than the model's drops. Reading: higher than chance.
- Dropped stock, to the end of the window: the model's drops moved -8.73%, random drops at the same weeks -10.02% (median). Against the list: -2.13% and -3.42%. 86.8% of random draws did worse than the model's drops. Reading: within chance.
- The model's drops fell by more than random drops, beyond chance, on 0 of 4 drop measures. They fell by less than random drops, beyond chance, on 1.
- So the plain answer: on these measures, what the model drops then falls about as much as any stock dropped from its basket at the same weeks would. The fall matches the falling market and the basket, not the choice. At 8 weeks after the drop, the model's drops did better than random drops, so the model let go of stocks that later recovered.

What the pooled table says about adds, in plain words:

- Added stock, weeks before it was added: +11.25% against the list, random adds -0.61% (median). 100.0% of random draws were below. Reading: higher than chance.
- Added stock, while held: +1.67% against the list, random adds +0.56% (median). 82.6% of random draws were below. Reading: within chance.

Many measures are looked at here, per model and pooled. At the `tm_adds_drops_chance_pct` (5) percent reading, about that share would read beyond chance by luck alone.

## What it shows so far

- 11 of 12 sessions are finished. 6 of 6 first runs are in.
- Of the runs finished, 0 pass the plan's line for a run.
- The method verdict is: not shown.

## What it does not show

- About 25 weekly choices over one stretch of one market. One strong sector can carry a basket. A pass earns a longer test; it is not proof.
- The list was picked with hindsight. Random baskets share that lean; SPY does not, so SPY is for scale only.
- Models may like the same names. Six runs that agree are closer to one bet than to six.
- The adds and drops section was chosen after the runs were seen. It can suggest a next test; it cannot pass or fail this one.
- Fills are assumed from recorded minute bars. The rule against outside knowledge is given by instruction.

## Files

- `timemachine/PLAN_TM04_stock_basket.md`: the plan and its pass mark.
- `practice/traders/D02_stock_basket.md` and `timemachine/TRADER_BRIEF_WEIGHTS.md`: what each trader was given.
- `timemachine/weights.py`: the session and the book. `timemachine/score_weights.py`: the scorer and its twins.
- `timemachine/score_tm04.py`: writes this page and `timemachine/results_tm04.json` from the session folders TM04-D02-<MODEL>-r1 and -r2 under `$TM_RUNS`.
