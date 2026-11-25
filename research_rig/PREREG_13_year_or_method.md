# Pre-registration 13: the owner's method in 2021 and in every other year

Status: frozen 2026-11-25 19:27 UTC by the builder. Written 2026-11-25 18:44 UTC before any price was collected for it. The code was then checked by two other models: one read it against this text and found faults that were fixed; the other rebuilt the rules from this text alone and matched the code trade for trade on made-up data, and found the missing-hour fault fixed in the last block below. No return was worked out before this line. Nothing in this file or in `replay_13_plan` changes after it. Ledger rows 144 and 145 in `research_rig/TRIAL_LEDGER.md`. Pretend trades on past prices. No AI model takes part.

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

Hot five: each Monday 00:00 UTC, the `replay_13_plan.hot_n` listed coins with the largest gain over the `replay_13_plan.rise_days` days before.

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
2. In those same years it also ends above the `replay_13_plan.random_percentile`th percentile of yardstick (b).
3. At least one of those years is a year in which yardstick (a) fell.

Otherwise the finding is "the year": the rule was paid when coins rose and not otherwise. The same three lines are worked out for rule A. Reported and not judged: every year's figures for both rules and all yardsticks, the 3x version, the other cost levels, the number of trades and the share that hit the stop.

A support here would mean worth a time machine test with a rule trader on 2026 months and then the practice desk. It would not mean it makes money.

## Definitions fixed before the run

Written 2026-11-25 18:46 UTC after the code builder read the draft and listed what it left open. No price had been collected.

- When a coin list applies: a snapshot is dated on a Sunday. Its list is used from the Monday 00:00 UTC that follows, until the next snapshot's Monday. The December 2019 snapshot covers the first days of 2020. A missing snapshot is reported as a hole; the earlier list is carried and the weeks are flagged.
- The list: the first `replay_13_plan.universe_top_n` coins by rank at the time after the exclusions, chosen before looking at whether Binance had a pair. A coin with no pair is not replaced by the next one down. BNB stays in: it trades freely on this venue. Coins are tracked by the snapshot's own coin identity, not by ticker. A renamed or re-issued coin maps only to the pair that traded at the time, every hand-made mapping is listed, and no price series is joined across a re-issue.
- What is known at an hour: at hour t the close of the hour that just ended is known. The 7-day comparison uses the close 168 hours before that one. The dip is measured against the highest of the `replay_13_plan.dip_lookback_hours` closes before the signal close. A fill is always the next bar's open; nothing is bought or sold inside a bar at 1x.
- The hot `replay_13_plan.hot_n` are the largest 7-day gains even when some are negative. Ties go by coin identity. If fewer coins can be ranked, the unused parts stay in cash.
- Years: each calendar year is scored on its own, starting in cash with 1.00 at its first Monday 00:00 UTC. Everything is sold at the first open of the next January 1, and the new year waits for its first Monday. 2026 ends at Monday 2026-11-23 00:00 UTC, the end of the last whole week on file. Gains compound week to week. A year's figure is the compounded gain after costs.
- Within a part of the account: no sale and new purchase at the same open, no new purchase at a forced week-end or year-end sale, idle cash earns nothing. The holding clock runs from the fill. When several reasons to sell hold at once the order is: forced close-out (3x only), end of week or year, stop, take, time limit. Stop and take count when the close reaches the level or beyond.
- Missing prices: nothing trades at a missing bar; a queued sale waits for the next bar of the same pair. If a pair's bars stop for good, the position is sold at the last close seen, flagged and counted. A year in which more than `replay_13_plan.max_flagged_share_pct` percent of the account-part weeks are flagged is reported and cannot count toward the mark.
- Random yardstick: five coins drawn without replacement each Monday from the same rankable list, each of the `replay_13_plan.random_draws` draws carried through the whole year as one path. For rule B it runs rule B on them. For rule A it holds them for the week. The percentile is `replay_13_plan.random_percentile`, and "above" means strictly above.
- A year in which the rule closed fewer than `replay_13_plan.min_trades_per_year` trades is reported and cannot count toward the mark, so that sitting in cash through a bad year is not scored as skill.
- The three possible findings: supported (the three lines under "What would count" hold); paid only when coins rose (it ended above yardstick (a) only in years when (a) rose); not paid (neither).
- Costs are charged on the amount traded, each side. At `replay_13_plan.shown_leverage` times: fees on the full position, financing every `replay_13_plan.financing_interval_hours` hours on the borrowed two thirds, close-out when an hourly low, the entry bar included, is `replay_13_plan.liquidation_drop_pct` percent or more below the fill; the part of the account is then zero until the next Monday's re-split. This is a simulation and not any venue's margin rules. Judged leverage is `replay_13_plan.judged_leverage`.
- The run refuses to start while this file is a draft, takes a lock before reading any real price, and refuses a second run. The self-test uses made-up bars only.

Added 2026-11-25 19:03 UTC after a second model read the code against this plan. No return had been worked out.

- Left out of the list, by the coin's identity in the snapshot and before the first 50 are counted: bitcoin and ether; coins made to track the dollar, also after they lost the peg; coins backed by gold; wrapped and staked copies of another coin; tokens issued by a central exchange other than BNB. The first build used a fixed ticker list and let ten such coins through (RLUSD, U, USDG, USDN, USTC, AMPL, WTRX, KCS, GT, ZB). On reading the full list three more were added on the same rule: KBC (sold as gold-backed), FLG and CNX (each issued by a central exchange). Tokens of lenders and brokers (NEXO, CEL, VGX) and of trading protocols with no company exchange behind them stay in. They are added, the lists are rebuilt, and the full list of every coin that ever enters is stored with the result so it can be read.
- A coin can be ranked on a Monday only when every hourly bar of the 7 days before is on file. A coin with a hole in those days is left out that week and counted.
- The Monday re-split is the one exception to "no sale and new purchase at the same open": the new week's parts may buy at the same open at which last week's positions are sold, also in the same coin, and both costs are paid.
- Stop and take are judged on hourly closes only, as written above. A bar that touched both levels inside the hour counts by its close.
- Financing at 3x is charged by the hour held: one eighth of `replay_13_plan.financing_bps_per_8h` per hour on the borrowed part.
- A sale that a missing bar delays past a year's end counts in the year the position was opened. The check of bar times found no such case.
- A position whose sale is waiting on a missing bar frees no money until a real bar fills it. If no bar ever comes, it is valued at its last close in the year's figure and its money takes no part in any later re-split of that year. That way nothing decided on a Monday depends on bars after that Monday.
- A part of the account in a week is flagged when the coin list was carried from an earlier snapshot, when its coin has a missing hourly bar in that week, when its sale was delayed by a missing bar, or when it was sold at a last close because bars stopped. A part left in cash because fewer than `replay_13_plan.hot_n` coins could be ranked is counted and not flagged.
- Years that cannot count toward the mark are also left out when choosing between the three findings.
- Every yardstick is worked out at each cost level, not only the judged one. The 3x figures are shown at the judged cost only.
- The percentile of the random paths uses straight-line interpolation between sorted paths. The random draws come from one seeded stream in date order.

Added 2026-11-25 19:16 UTC after a third model rebuilt the rules from this text alone and compared trade by trade on made-up data. No return had been worked out. Bar times only were read: the venue's own stops left 15 runs of missing hours, 31 hours in all, the longest 5 hours, 8 runs in 2020, 6 in 2021 and 1 in 2023, each one missing for every pair at once. Under the lines above, one missing hour would have blocked every entry for the next 7 days and the next Monday's ranking, and would have put 2020 and 2021 out of the judgment. A trader at the time lost the stopped hours and not the week, so the lines below replace the stricter ones above.

- Missing hours allowed: `replay_13_plan.max_missing_hours`. It was set after reading how many hours were missing (times only): in every coin-week on file the count of missing hours is either at most 6 or more than 12.
- A 7-day window can be used, for the Monday ranking and for the dip signal alike, when the bar at each end of it is on file and no more than that many hourly bars are missing inside it. This replaces "every hourly bar of the 7 days before".
- The highest close of the last `replay_13_plan.dip_lookback_hours` hours is taken over the bars on file.
- A part of the account in a week is flagged for missing bars only when its coin misses more than that many hours in the week. The flags for a carried coin list, a delayed sale and a sale at a last close stay as written.
- Yardstick (a) holds every coin that can be ranked that Monday, the same pool the rules and the random yardstick choose from. Before this line it held every listed coin with a bar in the hour before, which left it invested on days when the rules could not rank anything.
- When a chosen coin has no bar at Monday 00:00, rule A and both yardsticks buy at its first hourly open on file in that week. If none comes within `replay_13_plan.max_missing_hours` hours the part stays in cash for the week and is flagged.
- When two coin identities point at the same pair in one week, the pair is counted once under the higher-ranked identity, and the number of such weeks is reported.

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
