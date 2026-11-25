# Time machine plan TM03: six AI models set how much bitcoin to hold

Made by `timemachine/score_tm03.py` from `timemachine/results_tm03.json`. Do not edit by hand. Pretend money. The plan, with its pass mark fixed before any session ran, is `timemachine/PLAN_TM03_bitcoin_dial.md`.

Sessions in: 39 of 48 are finished and scored here. 6 are running and 3 are not started; those are left out until they finish.

## What was asked

- Can a model that reads prices and dated headlines once a day decide well how much bitcoin to hold, starting fully invested?
- It does not pick trades. It answers one number at each wake: the share of the account to hold in BTC/USD. The rest is cash.

## How it ran

- Each model follows the card `practice/traders/D01_bitcoin_dial.md` and the brief `timemachine/TRADER_BRIEF_WEIGHTS.md`, one session per month, a fresh agent per session, a fresh account of `tm_account_start_usd` each month.
- Months: `tm03_plan.months` (8 months, from April 2026 to November 1 to 24, 2026).
- The account starts fully in bitcoin, bought at the first minute of the month with costs.
- One wake a day at `tm03_plan.wake_hour_utc`. The desk moves the book to the answer at the open of the next recorded minute. A change smaller than `tm_weights_min_change` is not traded. Nothing happens between wakes.
- Costs on the part traded: the fee `practice_crypto_fee_bps_added` and the spread `tm_crypto_half_spread_bps`.
- Each packet holds prices, trailing returns from closed daily bars, the book, and the crypto headlines since the last wake. The trader may look up more bars and headlines.
- Yardsticks. Hold: the same account never changed after the first minute. Shuffled stretches (`shuffle_runs`, the judged set): the model's month cut into stretches of days with the same share, put back in a random order, `tm_weights_twin_draws` times, with the same costs.
- Also printed and not judged: `shuffle` (the daily shares one by one in random order, which trades far more and pays more costs) and `shuffle_decisions` (the model's new shares moved among its own change days).

## What would count

From the plan, fixed before any session ran. For one model, over all months added up:

- Line 1: its gain in dollars is above the gain from holding.
- Line 2: its gain is above percentile `tm_weights_pass_percentile` (90.0) of its own shuffled stretches, added up draw by draw over the same months. A tie counts against the model. A model that never moves ties with everything and has shown nothing.
- For the method: at least `tm03_plan.method_min_models_beating_hold` (5) of the models meet line 1 and at least `tm03_plan.method_min_models_beating_shuffles` (2) meet line 2. Fewer, and it is reported as not shown.
- A line is said as not finished until every month of that model is in.

## Where each model stands

MEASURED, pretend money, months finished so far, added up. "Percentile" is the share of summed shuffled-stretch draws that ended strictly below the model.

| Model | Months counted | Gain summed | Holding, same months | Shuffled stretches: median | Percentile | Line 1 | Line 2 | Verdict |
|---|---|---|---|---|---|---|---|---|
| Claude Opus 5.5 | 8 of 8 | $124.30 | -$64.31 | $140.40 | 37.7 | yes | no | passes line 1 only |
| GPT-6.2 Sol | 8 of 8 | $126.17 | -$64.31 | $159.02 | 26.8 | yes | no | passes line 1 only |
| Gemini Neon | 8 of 8 | $25.05 | -$64.31 | $130.01 | 9.0 | yes | no | passes line 1 only |
| Claude Sonnet 5.5 | 8 of 8 | $138.35 | -$64.31 | $156.98 | 39.4 | yes | no | passes line 1 only |
| Kimi K3 | 3 of 8 | $210.45 | $375.04 | $308.98 | 0.9 | not finished (so far no) | not finished (so far no) | not finished |
| Grok 4.7 | 4 of 8 | $143.26 | $167.81 | $253.24 | 0.1 | not finished (so far no) | not finished (so far no) | not finished |

Method: not finished. So far 4 of 6 models are above holding and 0 of 6 are above the pass percentile of their shuffled stretches, on the months each has finished.

## Each model, month by month

MEASURED. Gain and hold are in dollars on the month's account. "Shuffled stretches" is the judged percentile; when the number of different orders is under the draw count it is shown, and the percentile is coarse. "Day by day" and "change days" are the two shuffles that are not judged. "Changes" counts the wakes where the asked share differs from the one before, the opening position included.

### Claude Opus 5.5

| Month | Gain | Hold | Shuffled stretches | Day by day (not judged) | Change days (not judged) | Average share held | Changes | Costs | Largest drop | Hold's largest drop |
|---|---|---|---|---|---|---|---|---|---|---|
| April 2026 | $114.43 | $114.43 | no timing to judge | 0.0 | 0.0 | 1.00 | 0 | $3.49 | -4.2% | -4.2% |
| May 2026 | $0.35 | -$39.03 | 86.6 (of 120 orders) | 99.1 | 86.7 | 0.65 | 4 | $6.30 | -6.8% | -10.7% |
| June 2026 | -$107.89 | -$207.22 | 38.6 | 60.7 | 61.7 | 0.45 | 9 | $6.25 | -10.8% | -20.7% |
| July 2026 | $33.55 | $69.81 | 0.0 (of 24 orders) | 4.2 | 8.2 | 0.80 | 4 | $4.23 | -5.3% | -5.5% |
| August 2026 | $241.61 | $245.33 | 0.0 (of 6 orders) | 77.1 | 31.7 | 0.98 | 2 | $5.22 | -3.2% | -3.2% |
| September 2026 | $14.54 | $59.89 | 10.0 (of 120 orders) | 17.2 | 13.8 | 0.87 | 4 | $6.87 | -6.2% | -7.0% |
| October 2026 | -$70.59 | -$76.42 | 8.2 (of 24 orders) | 67.5 | 19.9 | 0.75 | 3 | $6.47 | -10.1% | -10.8% |
| November 1 to 24, 2026 | -$101.69 | -$231.10 | 65.2 | 75.9 | 79.5 | 0.42 | 9 | $7.46 | -11.7% | -26.9% |

### GPT-6.2 Sol

| Month | Gain | Hold | Shuffled stretches | Day by day (not judged) | Change days (not judged) | Average share held | Changes | Costs | Largest drop | Hold's largest drop |
|---|---|---|---|---|---|---|---|---|---|---|
| April 2026 | $103.95 | $114.43 | 0.0 (of 6 orders) | 35.0 | 31.7 | 0.98 | 2 | $5.19 | -4.2% | -4.2% |
| May 2026 | $4.88 | -$39.03 | 89.2 (of 120 orders) | 99.2 | 88.0 | 0.60 | 4 | $6.66 | -6.4% | -10.7% |
| June 2026 | -$144.05 | -$207.22 | 5.9 | 3.7 | 25.7 | 0.47 | 7 | $7.14 | -14.4% | -20.7% |
| July 2026 | $62.84 | $69.81 | 62.2 (of 24 orders) | 69.5 | 63.4 | 0.95 | 3 | $6.28 | -5.3% | -5.5% |
| August 2026 | $207.94 | $245.33 | 23.4 (of 120 orders) | 55.2 | 75.9 | 0.91 | 4 | $6.98 | -3.2% | -3.2% |
| September 2026 | $23.83 | $59.89 | 6.9 (of 120 orders) | 24.7 | 10.6 | 0.90 | 4 | $6.85 | -6.8% | -7.0% |
| October 2026 | -$61.04 | -$76.42 | 38.2 (of 360 orders) | 73.1 | 42.9 | 0.69 | 5 | $6.82 | -9.1% | -10.8% |
| November 1 to 24, 2026 | -$72.18 | -$231.10 | 58.1 (of 720 orders) | 84.1 | 90.7 | 0.34 | 5 | $8.19 | -9.4% | -26.9% |

### Gemini Neon

| Month | Gain | Hold | Shuffled stretches | Day by day (not judged) | Change days (not judged) | Average share held | Changes | Costs | Largest drop | Hold's largest drop |
|---|---|---|---|---|---|---|---|---|---|---|
| April 2026 | $83.01 | $114.43 | 0.0 (of 6 orders) | 0.0 | 0.0 | 0.98 | 2 | $7.09 | -4.2% | -4.2% |
| May 2026 | -$15.30 | -$39.03 | 78.8 (of 720 orders) | 96.2 | 69.3 | 0.63 | 5 | $9.83 | -8.3% | -10.7% |
| June 2026 | -$115.73 | -$207.22 | 39.0 | 62.8 | 44.5 | 0.42 | 10 | $14.00 | -11.6% | -20.7% |
| July 2026 | -$2.66 | $69.81 | 1.1 | 5.6 | 0.9 | 0.72 | 10 | $12.32 | -5.1% | -5.5% |
| August 2026 | $220.30 | $245.33 | 15.1 (of 24 orders) | 70.7 | 49.1 | 0.91 | 3 | $8.67 | -3.3% | -3.2% |
| September 2026 | $23.63 | $59.89 | 15.8 (of 120 orders) | 40.9 | 31.8 | 0.85 | 4 | $8.54 | -6.6% | -7.0% |
| October 2026 | -$92.33 | -$76.42 | 2.8 | 38.2 | 4.1 | 0.64 | 7 | $12.76 | -12.1% | -10.8% |
| November 1 to 24, 2026 | -$75.87 | -$231.10 | 58.7 | 73.4 | 75.7 | 0.30 | 8 | $13.31 | -8.4% | -26.9% |

### Claude Sonnet 5.5

| Month | Gain | Hold | Shuffled stretches | Day by day (not judged) | Change days (not judged) | Average share held | Changes | Costs | Largest drop | Hold's largest drop |
|---|---|---|---|---|---|---|---|---|---|---|
| April 2026 | $114.43 | $114.43 | no timing to judge | 0.0 | 0.0 | 1.00 | 0 | $3.49 | -4.2% | -4.2% |
| May 2026 | -$5.51 | -$39.03 | 88.4 (of 24 orders) | 98.4 | 95.4 | 0.69 | 3 | $6.12 | -7.4% | -10.7% |
| June 2026 | -$151.45 | -$207.22 | 3.4 (of 720 orders) | 2.9 | 6.6 | 0.40 | 5 | $7.18 | -15.2% | -20.7% |
| July 2026 | $57.10 | $69.81 | 0.0 (of 2 orders) | 6.4 | 0.0 | 0.98 | 2 | $3.49 | -5.5% | -5.5% |
| August 2026 | $230.18 | $245.33 | 23.0 (of 60 orders) | 75.9 | 42.4 | 0.94 | 4 | $6.61 | -3.3% | -3.2% |
| September 2026 | $54.55 | $59.89 | 0.0 (of 6 orders) | 36.1 | 31.9 | 0.98 | 2 | $5.50 | -7.0% | -7.0% |
| October 2026 | -$60.89 | -$76.42 | 48.9 (of 360 orders) | 80.3 | 22.5 | 0.69 | 5 | $7.31 | -9.1% | -10.8% |
| November 1 to 24, 2026 | -$100.06 | -$231.10 | 64.9 (of 120 orders) | 87.5 | 90.3 | 0.50 | 4 | $6.35 | -13.2% | -26.9% |

### Kimi K3

| Month | Gain | Hold | Shuffled stretches | Day by day (not judged) | Change days (not judged) | Average share held | Changes | Costs | Largest drop | Hold's largest drop |
|---|---|---|---|---|---|---|---|---|---|---|
| April 2026 | not started | | | | | | | | | |
| May 2026 | not started | | | | | | | | | |
| June 2026 | running | | | | | | | | | |
| July 2026 | $22.63 | $69.81 | 6.8 | 34.0 | 15.4 | 0.59 | 8 | $7.75 | -3.9% | -5.5% |
| August 2026 | $202.85 | $245.33 | 10.4 (of 720 orders) | 83.0 | 93.9 | 0.81 | 5 | $8.95 | -3.1% | -3.2% |
| September 2026 | -$15.02 | $59.89 | 5.3 (of 120 orders) | 8.9 | 4.0 | 0.82 | 4 | $8.20 | -6.7% | -7.0% |
| October 2026 | running | | | | | | | | | |
| November 1 to 24, 2026 | not started | | | | | | | | | |

### Grok 4.7

| Month | Gain | Hold | Shuffled stretches | Day by day (not judged) | Change days (not judged) | Average share held | Changes | Costs | Largest drop | Hold's largest drop |
|---|---|---|---|---|---|---|---|---|---|---|
| April 2026 | running | | | | | | | | | |
| May 2026 | running | | | | | | | | | |
| June 2026 | -$97.83 | -$207.22 | 32.6 (of 720 orders) | 31.0 | 47.8 | 0.30 | 5 | $8.33 | -9.8% | -20.7% |
| July 2026 | $31.45 | $69.81 | 0.0 | 0.0 | 0.1 | 0.83 | 9 | $6.56 | -5.4% | -5.5% |
| August 2026 | $226.59 | $245.33 | 0.0 (of 3 orders) | 53.2 | 33.9 | 0.95 | 2 | $6.97 | -3.2% | -3.2% |
| September 2026 | -$16.95 | $59.89 | 2.9 (of 24 orders) | 4.9 | 8.6 | 0.90 | 3 | $8.51 | -7.1% | -7.0% |
| October 2026 | running | | | | | | | | | |
| November 1 to 24, 2026 | running | | | | | | | | | |

## Gain by what the model said drove each change

MEASURED, months finished so far. The month is cut where the asked share changed. A stretch runs from just before its change is filled to just before the next change, so the stretches add up to the gain. "Against holding" is the stretch's gain less what holding bitcoin would have made on the same money over the same wakes. "Opening" is the first stretch when the model kept the opening position.

| Model | Driver | Stretches | Wakes | Gain | Against holding |
|---|---|---|---|---|---|
| Claude Opus 5.5 | both | 23 | 115 | -$120.55 | $169.96 |
| Claude Opus 5.5 | opening | 5 | 80 | $360.73 | -$18.98 |
| Claude Opus 5.5 | price | 12 | 43 | -$115.88 | $23.94 |
| GPT-6.2 Sol | both | 18 | 93 | $33.61 | $152.14 |
| GPT-6.2 Sol | opening | 8 | 54 | -$4.12 | -$27.49 |
| GPT-6.2 Sol | price | 16 | 91 | $96.68 | $50.85 |
| Gemini Neon | both | 43 | 161 | $205.76 | $72.61 |
| Gemini Neon | opening | 7 | 60 | -$35.17 | -$23.97 |
| Gemini Neon | price | 6 | 17 | -$145.55 | $26.26 |
| Claude Sonnet 5.5 | both | 22 | 123 | $210.43 | $199.24 |
| Claude Sonnet 5.5 | opening | 7 | 92 | -$57.17 | -$24.66 |
| Claude Sonnet 5.5 | price | 3 | 23 | -$14.91 | $7.75 |
| Kimi K3 | both | 10 | 45 | $26.18 | -$108.11 |
| Kimi K3 | news | 1 | 3 | $2.11 | -$9.23 |
| Kimi K3 | opening | 2 | 30 | $128.06 | -$7.32 |
| Kimi K3 | price | 6 | 14 | $54.12 | -$53.49 |
| Grok 4.7 | both | 19 | 92 | $220.45 | -$17.91 |
| Grok 4.7 | opening | 3 | 30 | -$77.20 | -$10.29 |

## What it shows so far

- 39 of 48 sessions (one per model per month) are finished. 4 of 6 models have all months in.
- On the months finished, 4 of 6 models gained more than holding, and 0 of 6 are above the pass percentile of their shuffled stretches.
- No verdict is given for a model until all its months are in, and none for the method until every model is.

## What it does not show

- If bitcoin fell over these months, holding less beats holding without any skill. Line 1 alone is not a pass; line 2 is the test of timing.
- When a model makes few changes, its stretches can be put in only a few orders, and its percentile can take only a few values. The tables show the number of orders when it is under the draw count.
- The models read the same headlines and may move together. Six answers are then closer to one, and the counts are easier to reach by luck than they look.
- Some headlines were edited after they were published. Those are marked `edited_later`, and the card says not to act on them.
- Fills are assumed from recorded minute bars, not real. The rule against outside knowledge is given by instruction; lookups are logged, memory is not.
- One run per model per month. Run-to-run variation is not measured.
- The split by driver is what the model said, not a measure of what it used.

## Files

- `timemachine/PLAN_TM03_bitcoin_dial.md`: the plan and its pass mark.
- `practice/traders/D01_bitcoin_dial.md` and `timemachine/TRADER_BRIEF_WEIGHTS.md`: what each trader was given.
- `timemachine/weights.py`: the session and the book. `timemachine/score_weights.py`: the scorer and its twins.
- `timemachine/score_tm03.py`: writes this page and `timemachine/results_tm03.json` from the session folders TM03-D01-<MODEL>-<YYYY-MM> under `$TM_RUNS`.
