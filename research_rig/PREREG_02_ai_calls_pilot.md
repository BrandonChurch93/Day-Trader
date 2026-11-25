# Pre-registration 02: pilot of AI making the calls, replayed on dates after the models' knowledge cutoffs

Written 2026-11-25 06:43 UTC, before any model saw a packet. Not edited after the first model decision. Research rig, not the product. Proposed by research. No owner decision is recorded here.

## What this pilot is, and is not

- It is a first look and a test of the method: can a model make one call a day on BTC and ETH from prices alone, in strict time order, and how does it behave against a plain trend rule after costs?
- It is not evidence that a model can or cannot trade. The sample is 147 days in one market. The design research (`docs/research/11`) says a fair test must run forward on days that have not happened yet. This replay does not replace that test.
- No pass mark is set. The result on skill is declared inconclusive before it starts. What it can show: whether the harness works, how far apart identical runs land, what the models cost in turnover, and whether a model simply copies the trend rule.

## Setup

| Item | Value |
|---|---|
| Decisions | One per day after the UTC close, 2026-06-30 to 2026-11-23: 147 decisions. Fills at the next open. Marked to the close of 2026-11-24 |
| Assets | BTC/USD and ETH/USD, Bitstamp daily bars. Half the account is assigned to each |
| Allowed answers | For each coin: hold 0, 0.25, 0.5, 0.75 or 1 of its half. Long or cash only |
| What the model sees | Step 1: the last 120 daily closes. Every step: the day's open, high, low, close, volume; 1, 7, 30 and 90 day change; 20, 50, 100 and 200 day averages; 30 day volatility; distance from the 365 day high; account value, holdings and costs paid. No news, no web |
| Cost | 30 bps of each dollar traded (Alpaca's 25 bps taker fee plus 5 bps for spread), the same as the trend rule is charged |
| Execution rule | Same engine and same 0.10 band as pre-registration 01 |
| Order of time | A local server releases one day at a time and stamps each decision. A run cannot see day t+1 before its answer for day t is recorded |

## Runs (6 trials, logged in the trial ledger)

| Run | Model | Stated cutoff |
|---|---|---|
| r_fable_a, r_fable_b, r_fable_c | Claude Fable 5.2, three separate runs with the same prompt | Training data June 2026 (Anthropic's model page, MEASURED by the design researcher) |
| r_opus | Claude Opus 5.5 | Training data June 2026 (MEASURED, same source type) |
| r_sol | GPT-6.2 Sol | Knowledge cutoff June 1, 2026. Training cutoff UNKNOWN |
| r_neon | Gemini Neon | Cutoff UNKNOWN. Not checked |

The three Fable runs are the main arm. The other three are described only.

## Comparisons

- Primary: rule P1 from pre-registration 01 (the trend ensemble) on the same dates, same costs, half the account per coin.
- Holding both coins the whole time.
- Shuffled timing: each run's own spells in random order, 1,000 times, seed 7.

## What is reported

For every run, good or bad: net return, largest drop, share of time invested, number of trades, cost paid, and the daily return difference against P1 with a 90% range from a block bootstrap (block 10 days, 2,000 draws, seed 7). The spread between the three Fable runs. How often each run's holding matched P1's.

## Known weak points, stated before the run

- The time order is enforced by the server. The ban on web search and on reading other files is an instruction to the model. It is not enforced. STATED control.
- The person who built the pilot (this model) has seen the price path while building the server.
- The models are run as agents with their normal system setup, not through a bare API with fixed settings, so the runs cannot be pinned to an exact model build.
- One market window. BTC fell about 1% and ETH rose about 4% over it, with large swings, so cash-heavy answers look good here for reasons that may not repeat.
- 147 days can only detect a very large edge. Using the design research's formula, 147 independent daily observations give 80% power only for a daily information ratio near 0.2, which is about 3.9 a year. Nothing realistic is that large.
