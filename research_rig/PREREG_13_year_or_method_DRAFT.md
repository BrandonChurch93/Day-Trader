# Pre-registration 13 (draft): the owner's method in 2021 and in every other year

Status: DRAFT written 2026-11-25 18:44 UTC by the builder, before any price was collected for it. It becomes final when the code has been checked by a second model and this line is changed to "frozen" with the time. Ledger rows 144 and 145 in `research_rig/TRIAL_LEDGER.md`. Pretend trades on past prices. No AI model takes part.

## The question

The owner, 2026-11-25 (`docs/DECISIONS.md`): he bought dips and sold peaks on the coins people were piling into, held a few hours, used leverage, and turned 500 dollars into 10,000 several times. He believes it was 2021. Most coins rose strongly in 2021. The question: did a plain version of that method make money because of the method, or because of the year?

An AI model cannot be tested on 2021, because the models know those prices (`docs/research/31_model_knowledge_lines.md`). A fixed rule can. This plan tests a fixed rule on every year from 2020 to 2026. The AI version of the method is tested apart, on 2026 only (`timemachine/PLAN_TM06_hot_coin_swing.md`).

## What this cannot answer

A fixed rule is not the owner. He chose coins by reading what people were talking about and read charts by eye. If the rule fails in a year, that does not show he would have. What it can show is how much a simple dip-and-peak rule on hot coins was paid in 2021 against other years.

## Data

- Hourly bars from Binance's public archive, pairs against USDT, `replay_13_plan.start` to `replay_13_plan.end`, pairs that were later removed included.
- The coin list is fixed at each month's start from that month's saved CoinMarketCap snapshot: the largest `replay_13_plan.universe_top_n` coins at the time, without bitcoin, ether, coins tied to the dollar, wrapped coins and exchange tokens, that had a Binance USDT pair trading then. A coin that later died is in the list for the months it was large.
- Raw bars and snapshots stay on the research machine.

## The rules

Hot five: each Monday 00:00 UTC, the five listed coins with the largest gain over the `replay_13_plan.rise_days` days before.

- Rule A (ledger 144), hold the hot five: buy the five in equal parts at Monday's first open, sell at the next Monday's first open.
- Rule B (ledger 145), swing the hot five: the account is split in five, one part per coin. When a part is in cash, buy at the next hour's open if the last hourly close is at least `replay_13_plan.dip_pct` percent below the highest close of the `replay_13_plan.dip_lookback_hours` hours before and still above the close `replay_13_plan.rise_days` days ago. Sell at the next hour's open when the last close is `replay_13_plan.take_pct` percent above the entry, or `replay_13_plan.stop_pct` percent below it, or after `replay_13_plan.max_hold_hours` hours. Everything is sold at the week's end.

The numbers were set once, here, as round figures before any price was read. They are not tuned and will not be changed after the run. A different set of numbers would be a new plan with new ledger rows.

Costs: `replay_13_plan.cost_bps_per_side` per side, judged. Also shown at each of `replay_13_plan.other_costs_bps`.

Leverage: judged at 1x. Shown and not judged: rule B at `replay_13_plan.shown_leverage` times, each position closed at a total loss of its part when the hourly low falls `replay_13_plan.liquidation_drop_pct` percent below entry, with `replay_13_plan.financing_bps_per_8h` charged on the borrowed part.

## Yardsticks

- (a) All listed coins held in equal parts, reset each Monday, same costs.
- (b) Rule B on five listed coins drawn at random each Monday, `replay_13_plan.random_draws` draws, seed `replay_13_plan.seed`. This separates "the dip rule works" from "hot coins matter".
- Bitcoin held, for scale.

## What would count, fixed now

Each calendar year is scored apart (2026 to its last day of prices). "The method, not the year" is supported for rule B when, at 1x after the judged cost, all three hold:

1. It ends the year above yardstick (a) in at least `replay_13_plan.min_years_above` of the 7 years.
2. In those same years it also ends above the 75th percentile of yardstick (b).
3. At least one of those years is a year in which yardstick (a) fell.

Otherwise the finding is "the year": the rule was paid when coins rose and not otherwise. The same three lines are worked out for rule A. Reported and not judged: every year's figures for both rules and all yardsticks, the 3x version, the other cost levels, the number of trades and the share that hit the stop.

A support here would mean worth a time machine test with a rule trader on 2026 months and then the practice desk. It would not mean it makes money.

## How this can fool us

- One venue's prices. Fills are at the next hour's open with a fixed cost; a fast coin's real spread at that moment can be wider.
- Coins that were hot but not on Binance against USDT are missed.
- Seven years is seven data points. Two rules and round-number settings keep the count of tries low, but a pass on five of seven is still weak evidence.
- The 3x version uses spot prices and hourly lows. A real leveraged account pays funding that changes hour to hour and can be closed inside the hour.

## Order of work

1. Collect snapshots and bars. No return is worked out before this plan is frozen.
2. Code and a self-test on made-up data. A second model checks the code.
3. Freeze. One run. Results stored with the command and input fingerprints.
4. Result page in `docs/research/` and a line in `docs/STATUS.md`.
