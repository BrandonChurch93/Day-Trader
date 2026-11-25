# Time machine plan 03: the model sets how much bitcoin to hold

Written 2026-11-25 16:22 UTC by the builder, before the tool for it was finished and before any session of this plan was made. Pretend money.

## What is asked

Can a model that reads prices and dated headlines once a day decide well how much bitcoin to hold, starting fully invested?

Why this and not more trade picking. MEASURED in plans TM01 and TM02 by 2026-11-25 16:20 UTC: six models picking single trades with stops and targets stayed in cash at most wakes, were not ahead of holding bitcoin and did not stand clear of random twins. They lost less than holding in falling months and fell far behind in rising ones. Tests by others of language-model traders in 2025 and 2026 mostly read the same way; our check of those sources is not finished and is not relied on here. So this plan takes away the picking, the stops and the targets, and starts the model where a holder starts.

## Trader

Card `practice/traders/D01_bitcoin_dial.md`, brief `timemachine/TRADER_BRIEF_WEIGHTS.md`. One model per session, a fresh agent per session.

| Trial | Trader id | Model |
|---|---|---|
| TM03-a | D01-OPUS | Claude Opus 5.5 |
| TM03-b | D01-SOL | GPT-6.2 Sol |
| TM03-c | D01-NEON | Gemini Neon |
| TM03-d | D01-SONNET | Claude Sonnet 5.5 |
| TM03-e | D01-KIMI | Kimi K3 |
| TM03-f | D01-GROK | Grok 4.7 |

## Dates, costs, how a session runs

- Months: the calendar months in `tm03_plan.months`, each a separate session with a fresh `tm_account_start_usd`. All are after every model's knowledge line (`docs/research/31_model_knowledge_lines.md`).
- April and May 2026 need crypto headlines that are not on the tape yet. Those two months start only after the headlines from 2026-04-01 are recorded and the date check of plan TM02 is repeated on them. If they cannot be recorded, the plan runs June to November and this page says so before any session starts.
- The account starts fully in bitcoin, bought at the first minute of the month with costs.
- One wake a day at `tm03_plan.wake_hour_utc`. The model answers with one number from 0 to 1: the share of the account to hold in BTC/USD. The rest is cash. A change smaller than `tm_weights_min_change` is not traded. Nothing happens between wakes: no stops, no targets.
- Costs per side: the fee `practice_crypto_fee_bps_added` and the spread `tm_crypto_half_spread_bps`, on the part that is traded. Fills at the open of the next recorded minute.
- With every answer the model writes why in one or two plain sentences and marks what drove it: price, news, both, or nothing new.

## Yardsticks

1. Hold: the same account, never changed after the first minute.
2. Its own answers in shuffled order: the model's daily numbers for a month, put in a random order across that month's wakes, `tm_weights_twin_draws` times, with the same costs. This keeps how much it held on average and takes away when. It is the test of timing.

## What would count, fixed now

For one model, over all months added up:

1. its gain in dollars is above the gain from holding, and
2. its gain is above the `tm_weights_pass_percentile`th percentile of its own shuffles added up over the same months. A tie counts against the model. A model that never moves the number ties with everything and has shown nothing.

For the method: at least `tm03_plan.method_min_models_beating_hold` of the six models meet line 1 and at least `tm03_plan.method_min_models_beating_shuffles` meet line 2. Fewer, and it is reported as not shown.

Also reported, not part of the mark: largest drop against hold's largest drop, average share held, number of changes, costs paid, and the gain split by what the model said drove each change.

## How this can fool us

- If bitcoin falls over the months, a model that simply holds less beats holding without any skill. Line 2 is there for that. A pass on line 1 alone is not a pass.
- The six models read the same headlines and may move together. Six answers are then closer to one answer, and the counts above are easier to reach by luck than they look.
- About one in eight headlines was edited after it was published (plan TM02). The card tells the trader not to act on those.
- The builder has seen how bitcoin moved from July to November 2026 before writing this. The design does not use it: the default is to hold, which is the yardstick itself.
- Fills are assumed, crypto minutes are thin, and the no-web rule is by instruction.
- One run per model per month. Run-to-run variation is not measured here.
