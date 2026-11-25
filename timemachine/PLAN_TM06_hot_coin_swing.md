# Time machine plan 06: the owner's method, pick the hot coins and trade their swings

Written 2026-11-25 18:25 UTC by the builder, before the tool for it was finished and before any session of this plan was made. Pretend money.

## What is asked

The owner traded like this (`docs/DECISIONS.md`, 2026-11-25; card `practice/traders/F01_hot_coin_swing.md`): find the coins people are piling into, then buy the dips and sell the peaks over a few hours, with leverage. Two questions, tested apart so we can tell which part carries a result:

- Part P, the picker. Can a model, once a day, name coins that then do better than coins named by a plain rule or at random?
- Part S, the swing trader. On coins that are already running, can a model that wakes every hour do better than simply holding those coins, by more than its amount of trading alone would explain?

What is already measured against it, so the marks below are set where they are: a plain count of attention did not lead price (`docs/research/45_attention_feed_measured.md`); the caller he followed lost to bitcoin on the middle call in every kind of market (`docs/research/46_becker_calls_measured.md`); no published short-hold pattern clears a small US account's fees (`docs/research/41_fast_lane_evidence_checked.md`); and every model tested so far bought what had already risen (`docs/STATUS.md`).

## Before any session: the control run

A fixed rule with no model, run on the futures book first: on bitcoin, after a 15-minute move of more than `tm06_plan.control_move_bps` basis points, take the other side for the next 15 minutes. Run at each leverage in `tm06_plan.control_leverage` and each fee in `tm_perp_fee_levels_bps`, on the whole of `tm06_plan.picker_start` to `tm06_plan.picker_end`. Published work says this loses after fees (`docs/research/41_fast_lane_evidence_checked.md`, test 6). If our book shows a gain at 12 or 25 basis points a side, no session of this plan starts until the fault is found. Trial TM06-0.

## Traders

Card `practice/traders/F01_hot_coin_swing.md`. Six models, one run each in each part.

| Trials | Part | Models |
|---|---|---|
| TM06-P-a to TM06-P-f | picker | Claude Opus 5.5, GPT-6.2 Sol, Gemini Neon, Claude Sonnet 5.5, Kimi K3, Grok 4.7 |
| TM06-S-a to TM06-S-f | swing trader | the same six |

## Shared lines

- Coins: `tm06_plan.coins`, the 20 coins on the second price store that have a US-listed future, without bitcoin, ether and the gold token. The list was made on 2026-11-25 from coins that are still traded, so it leaves out coins that died. Every yardstick is drawn from the same list and shares that.
- Prices: Coinbase one-minute bars. An order fills at the open of the next minute. The futures book uses the spot price as the futures price.
- Costs: a fee per side on what is traded, judged at `tm06_plan.main_fee_bps` basis points and also shown at the other levels in `tm_perp_fee_levels_bps`, plus half the spread per coin (`tm_crypto_half_spread_bps_by_coin`), plus funding on the whole position.
- Dates: after every model's knowledge line (`timemachine/knowledge_lines.json`; the latest is February 2026).
- Leverage: both parts are judged at 1x. Part S answers are also carried at each multiple in `tm06_plan.carried_leverage` with forced close-out, and shown beside the 1x result. That is shown, not judged. Nothing above 3x is run.
- No web, by instruction.

## Part P: the picker

- Period `tm06_plan.picker_start` to `tm06_plan.picker_end`, one session per calendar month per model.
- One wake a day at `tm06_plan.picker_wake_hour_utc`:00 UTC. The model names from none to `tm06_plan.picker_max_names` coins. The desk holds the named coins in equal parts adding up to 1x, long only, and trades only the difference from the day before. No names means cash.
- The packet shows, for every coin on the list as of the wake: its price and change over 1 hour, 24 hours, 7 days and 30 days; its volume against its own usual; the latest funding rate; the change in open interest; the attention counts that had been published by then; dated headlines where the tape has any.

Yardsticks, all with the same costs and the same trading time:

1. All the coins in equal parts, held.
2. Plain rule: the `tm06_plan.picker_max_names` coins that rose most over the last `tm06_plan.picker_rise_days` days, renamed every day.
3. Plain rule: the coins whose attention count rose most.
4. Random picks: `tm_weights_twin_draws` runs that swap as many names each day as the model did, drawn at random from the list.
5. Bitcoin held, for scale only.

What would count, fixed now. For one model, its eight months joined end to end: the gain is above yardstick 1, above yardstick 2, and above the `tm_weights_pass_percentile`th percentile of yardstick 4. For the method: at least `tm06_plan.method_min_models_above_median` of six models end above the middle of their random picks and at least `tm06_plan.method_min_models_above_percentile` clear all three marks. Fewer, and it is reported as not shown.

## Part S: the swing trader

- Four one-week sessions per model. The weeks and their coins were fixed by `timemachine/tm06_fix_weeks.py` from daily bars before any session: all 33 whole weeks from 2026-04-06 were ranked by the gain of the list held in equal parts, and the weeks at the 10th, 30th, 70th and 90th percentile were taken, so two are falling weeks and two are rising weeks and none is the extreme. The five coins of a week are the five that rose most over the seven days before it starts, which is what "already running" means here and could be known at the start.

| Week (UTC, Monday to Monday) | The list held in equal parts | Coins |
|---|---|---|
| 2026-05-11 to 2026-05-18 | -10.1% | ENA, NEAR, ONDO, SUI, ZEC |
| 2026-07-20 to 2026-07-27 | +2.6% | LINK, LTC, ONDO, PEPE, ZEC |
| 2026-08-31 to 2026-09-07 | +14.6% | BNB, HYPE, LINK, SOL, ZEC |
| 2026-10-05 to 2026-10-12 | -3.9% | AAVE, ADA, BNB, HBAR, XLM |

- One wake every `tm06_plan.swing_wake_minutes` minutes, day and night. At each wake the model sets how much of the account is in each of the five coins: long or nothing, adding up to at most `tm06_plan.swing_max_gross`x. It may set a stop and a target on each.
- The packet shows recent one-minute and hourly bars for the five coins, volume against usual, funding, and the account.

Yardsticks:

1. The five coins in equal parts, held for the week.
2. The model's own answers with their order shuffled within the week, `tm_weights_twin_draws` times. This keeps how much it held and how often it traded and breaks only the timing. In a falling week a trader that sits in cash beats holding without any skill; this yardstick is the one that takes that away.

What would count, fixed now. For one model, its four weeks joined end to end at `tm06_plan.main_fee_bps` basis points: the gain is above yardstick 1 and above the `tm_weights_pass_percentile`th percentile of yardstick 2. For the method: at least `tm06_plan.method_min_models_above_median` of six models end above the middle of their shuffled runs and at least `tm06_plan.method_min_models_above_percentile` clear both marks. Fewer, and it is reported as not shown. Reported beside it and not judged: rising weeks and falling weeks apart, the number of trades, the share of time in the market, the result at each fee level, and the carried 2x and 3x results with any forced close-out.

## What a pass earns

A pass in either part earns a longer test of that part on dates not used here, and a plan that puts the two parts together. It does not earn real money. If neither part passes, the write-up says which yardstick each model lost to, and the method goes to the dropped list unless the owner's answers about his own trading (which years, and whether he also sold short) point at something this plan did not test.

## How this can fool us

- One stretch of one year, April to November 2026. The owner's good runs were years ago, in markets where most small coins rose.
- The coin list is today's survivors. Coins that died are missing, which flatters every buyer of small coins. The yardsticks share the flattery, so only the comparisons mean anything, not the gains.
- Six models tend to like the same coins. If those led, all six look good together, and that is one bet, not six.
- Four weeks is a small sample for part S, even with 168 answers a week. A pass there is a reason for a longer test and no more.
- The owner watched charts and acted when he saw the shape. The model acts once an hour and fills at the next minute. A method that needs to act inside the hour is not tested here.
- The futures price is taken to be the spot price. Funding comes from the venues the second price store could collect, and for some coins that is a stand-in venue. Real futures can trade away from spot when it matters most.
- Spreads for the smaller coins were sampled on one day. Fast markets have wider spreads than that.
- Attention counts are partly dated by an assumed delay, not a proven one (`docs/research/45_attention_feed_measured.md`).
- A forced close-out in the time machine stops the loss at the deposit. A real venue can leave a debt (`docs/research/40_leverage_venues_checked.md`).
- A week of hourly answers may be too long for one agent. If a session has to be split between agents, the hand-over note is the only thing the second one gets, and the split is recorded in the session.
- The no-web rule is an instruction and is not enforced.
