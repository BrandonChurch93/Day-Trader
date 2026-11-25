# Pre-registration 17: the short side of the owner's method

Status: DRAFT written 2026-11-25 19:52 UTC, before any futures price or funding rate was read and before any price of a coin on the held-back list was read. Ledger rows 150 and 151. Not frozen. Nothing is run until the code has been read by two other models and this file is renamed without DRAFT. This plan and `research_rig/PREREG_16_hot_five_hedged_DRAFT.md` are both frozen before either is run, because they share the held-back list.

## The question

The owner said on 2026-11-25 that most of his trades were shorts: wait for a peak on a hot coin, go short on the way down, cover when the fall stalls (`docs/DECISIONS.md`). Replay 13 tested the buying side of that pattern and it lost in six of seven years (`docs/research/54_replay_13_year_or_method.md`). Does the same signal taken short make money after costs and funding, and in rising years as well as falling ones?

## What this cannot answer

- Whether his eye beats a fixed rule. The six-model sessions test judgment (`timemachine/PLAN_TM06_hot_coin_swing.md`).
- Whether a US account can do it. The futures here are Binance contracts. Coinbase and Kraken list futures on about 20 coins. A pass leads to a test on that short list, not to a trade.

## Samples

- Held-back list, judged: ranks `replay_16_plan.held_rank_from` to `replay_16_plan.held_rank_to` in the saved monthly snapshots, the list fixed and fingerprinted in plan 16. Closer to the lower market cap coins he traded than the top list.
- Viewed list, shown: plan 13's list.
- Stated now: the idea for this test came after seeing the buying side lose on the viewed list. The two lists move with the same market, so the held-back list is a new list and not a clean second world.

## The rule

Hot five: each Monday 00:00 UTC, the `replay_17_plan.hot_n` listed coins with the largest gain over the `replay_17_plan.rise_days` days before, ranked on spot prices as in plan 13. A hot coin with no live futures contract that Monday (plan 16's definition of live) leaves its part in dollars for the week.

- Rule S (ledger 150), short the drop from the peak: the account is split in five, one part per coin. When a part is in dollars, go short on the coin's perpetual contract at the next hour's open if the contract's last hourly close is at least `replay_17_plan.dip_pct` percent below its highest close of the `replay_17_plan.dip_lookback_hours` hours before and still above its close `replay_17_plan.rise_days` days ago. Cover at the next hour's open when the last close is `replay_17_plan.take_pct` percent below the entry, or `replay_17_plan.stop_pct` percent above it, or after `replay_17_plan.max_hold_hours` hours. Everything is covered at the week's end.
- This is the trigger of plan 13's rule B with the trade turned round. The numbers are the same round figures and are not tuned.
- Shown and not judged (ledger 151): the same rule at `replay_17_plan.shown_leverage` times with a forced close at a total loss of the part when the hourly high reaches `replay_17_plan.forced_close_rise_pct` percent above entry; the same rule on the viewed list; and "short, then the bounce", in which a part that covers at its target goes long at that same open and sells at the same three exits.

## Costs

- `replay_17_plan.cost_bps_per_side` a side on the futures, judged. Shown at each of `replay_17_plan.other_costs_bps`.
- Funding: every recorded payment while a short is open, by plan 16's funding rules. A short receives a positive rate and pays a negative one. Reported apart from the price gain.

## Yardsticks

- (a) Zero. The rule has to make money.
- (b) Short the hot five and hold them all week, equal parts, same costs and funding. This separates the timing from simply being short what had just risen.
- Shown for scale: the rule on five listed coins drawn at random each Monday (`replay_17_plan.random_draws` draws, seed `replay_17_plan.seed`), a short of all listed coins with a live contract held all week, and the sample's all-coins figure on spot.

## What would count, fixed now

Each calendar year is scored apart and starts from 1.00. 2026 ends where plan 16 ends it. On the held-back list at 1x and the judged cost, the short side is supported when all three hold:

1. Rule S ends the year above 1.00 in at least `replay_17_plan.min_years_above` of the 7 years.
2. In those same years it also ends above yardstick (b).
3. At least `replay_17_plan.min_rising_years` of those years are years in which the sample's all-coins figure rose. Making money short while coins fall is not the test.

Otherwise the finding is "not supported", and the write-up says whether it failed on costs, on rising years or on timing. A year with fewer than `replay_17_plan.min_trades_per_year` closed trades, or with more than `replay_17_plan.max_flagged_share_pct` percent of its account-part weeks flagged, is reported and cannot count.

A support would mean: worth a second test on the coins a US venue lists, then a rule trader in the time machine and the practice desk. It would not mean it makes money.

## Definitions fixed before the run

- Lists, coin identity, years, ties, what is known at an hour, and missing bars follow `research_rig/PREREG_13_year_or_method.md`. Contract identity, the definition of a live contract, the funding rules, the contract that stops paying, the order inside an hour, and the archive-only funding source follow `research_rig/PREREG_16_hot_five_hedged_DRAFT.md`.
- Signals and fills use the contract's own trade bars. Only the Monday ranking uses spot bars.
- The 7-day comparison inside the rule uses the contract's close 168 hours before the signal close. A contract with less history than that gives no signal.
- A short's loss is not capped at its part at 1x. A loss beyond the part is taken from the rest of the account. If the account reaches zero the year ends there.
- "Short, then the bounce": the long is opened on the same contract at the open where the short covered at its target, only then, and is closed at the next hour's open when the last close is `replay_17_plan.take_pct` percent above its entry, `replay_17_plan.stop_pct` percent below it, or after `replay_17_plan.max_hold_hours` hours. After it closes the part is in dollars again.
- Random draws use coins with a live contract that Monday, the same weeks and the same rule.

## How this can fool us

- Hourly bars. A stop at 5% is checked on the close and filled at the next open; a real stop on a fast coin can fill far worse in a squeeze, and a short's loss has no ceiling.
- A bar on file is not proof an order could be filled, and small contracts are thin. The dearer cost level is shown.
- One venue, and only coins it listed a contract for. Coins that were hot and had no contract are not in the test, and those may be the ones he traded.
- A fixed 5% is not his eye for where a fall stalls.
- The idea was chosen after seeing the buying side fail on a list that moves with this one.

## Order of work

1. Ledger rows, this draft and the config entry are committed before any code.
2. The builder adds the rule to the plan 16 code base with tests on made-up prices. No return on real prices.
3. Two other models read the code against this plan.
4. Freeze both plans. One run each by the lead. Result page `docs/research/57_replay_17_short_the_peak.md` written by script.
