# Pre-registration 16: the hot five with the market taken out

Status: DRAFT written 2026-11-25 19:42 UTC, before any futures price or funding rate was read and before any price of a coin outside plan 13's list was read. Ledger rows 148 and 149. Not frozen. Nothing is run until the code has been read by two other models and this file is renamed without DRAFT.

## The question

Replay 13 (`docs/research/54_replay_13_year_or_method.md`) found that last week's five biggest risers ended the year ahead of the average coin in five of seven years, and still lost about 70% in each of three years because they fell with everything else. Does that lean make money once the market's own move is taken out with a short on futures, after costs and funding?

## What this cannot answer

- Whether the owner's eye beats a fixed rule. That is the six-model sessions (`timemachine/PLAN_TM06_hot_coin_swing.md`).
- Whether a US account can do it. The short side here is Binance futures, which a US trader cannot use. Coinbase and Kraken list futures on about 20 coins. A pass leads to a second test on that short list, not to a trade.

## Two samples, one judged

- Viewed sample: plan 13's list, the largest `replay_13_plan.universe_top_n` coins. Its hot five and its average coin were already seen. Shown, not judged.
- Held-back sample: the next coins down in the same saved monthly snapshots, ranks `replay_16_plan.held_rank_from` to `replay_16_plan.held_rank_to` after the same exclusions, with the same list rules as plan 13. No result has been worked out for this list. Judged.
- Limit, stated now: coins move between the two lists as they grow and shrink, so the two samples share some coins in different months. The held-back sample is a new list, not new coins.

## The book

Each Monday 00:00 UTC, with the account's value E:

- Long side: `replay_16_plan.long_share` of E buys the sample's hot five on spot in equal parts, by plan 13's rule A and plan 13's code, at Monday's first open, sold at the next Monday's first open. A hot coin that cannot be ranked or filled leaves its part in dollars.
- Short side: a short of the same dollar size as what the long side really bought, backed by the other part of E held in dollars. No borrowing beyond that: the whole book is 1x.
- Short M, the market basket (judged): equal parts of every coin on plan 13's list that has a live Binance USD-M perpetual contract that Monday, leaving out that week's hot five. If fewer than `replay_16_plan.min_basket_names` contracts are live, that week uses short B and is flagged.
- Short B, bitcoin and ether (shown): half each, the two perpetual contracts.
- A contract is live on a Monday when it has a bar at the entry hour and at least one funding payment in the `replay_16_plan.live_funding_lookback_hours` hours before. Past facts only. A contract whose funding payments stop during the week is closed at the open of the first hour after its last payment, and its part stays in dollars until Monday.
- Forced close: a contract whose hourly high reaches `replay_16_plan.short_stop_pct` percent above its entry is closed there at that loss plus the cost. It is not reopened that week. The mark-price bar is used when on file, the trade bar otherwise. Every such close is counted and reported.

## Costs

- Spot: `replay_16_plan.spot_cost_bps_per_side` a side, as in plan 13. Shown at each of `replay_16_plan.other_spot_costs_bps`.
- Futures: `replay_16_plan.perp_cost_bps_per_side` a side for the basket, `replay_16_plan.perp_cost_bps_per_side_majors` for bitcoin and ether. Shown at each of `replay_16_plan.other_perp_costs_bps`.
- Funding: every recorded funding payment between entry and exit, at its own time and rate, on the contract's dollar size at the last hourly close before the payment. A short receives a positive rate and pays a negative one. Funding is reported apart from the price gain.
- Costs are charged on every side of every weekly reset, also for a coin that stays in the list, as plan 13 did.

## Yardsticks

- (a) Zero. The book has to make money.
- (b) The same book with five coins drawn at random from the sample's list each Monday in place of the hot five, `replay_16_plan.random_draws` draws, seed `replay_16_plan.seed`. This separates "hot coins add something" from "being short the market paid".
- Shown for scale: rule A without the short, the short side alone, and the lean alone on paper (hot five less the sample's own all-coins figure, on spot, no cost on the short side).

## What would count, fixed now

Each calendar year is scored apart and starts from 1.00, as in plan 13. On the held-back sample with short M at the judged costs, the idea is supported when all four hold:

1. The book ends the year above 1.00 in at least `replay_16_plan.min_years_above` of the 7 years.
2. In those same years it also ends above the `replay_16_plan.random_percentile`th percentile of yardstick (b).
3. At least `replay_16_plan.min_falling_years` of those years are years in which the sample's all-coins figure fell.
4. No year ends more than `replay_16_plan.max_year_loss_pct` percent down.

Anything else is "not supported". Reported and not judged: the viewed sample with both shorts, the held-back sample with short B, every cost level, funding apart from price, forced closes, the number of live contracts per week, and the weeks that fell back to short B.

A support would mean: worth a second test on the coins a US venue lists, then the time machine and the practice desk. It would not mean it makes money.

## Definitions fixed before the run

- Everything not written here follows `research_rig/PREREG_13_year_or_method.md`: when a list applies, coin identity, what is known at an hour, ties, years, the missing-hour rule (`replay_16_plan.max_missing_hours`).
- The held-back list is the coins at ranks `replay_16_plan.held_rank_from` to `replay_16_plan.held_rank_to` counted after the exclusions, chosen before looking at whether Binance had a pair. A coin with no pair is not replaced.
- Contract identity: a contract maps to a coin only for the dates it traded under that coin. Contracts quoted per 1,000 coins map to the coin. A re-used ticker is never joined across a gap. Every hand-made mapping is listed in the result.
- The short side's entry and exit are the contract's first open of the Monday hour. If that bar is missing the contract is not live that week.
- The short's size is set once on Monday and not adjusted inside the week.
- November 2026 funding, which the bulk archive does not hold yet, is read from the venue's public funding history for every contract used. A contract-week whose funding cannot be read is reported and charged no funding, and the count is shown.
- Random draws use the same weeks, the same costs, the same short and the same rule for parts left in dollars.

## How this can fool us

- The short basket is made of larger coins than the held-back long side, so the book also carries "small coins against large coins". The paper lean figure shows how much of the result that is.
- Small coins cost more to trade than the judged spot cost. The dearer cost level is shown.
- Hourly bars cannot show a squeeze inside the hour. A real short can be closed out at a worse price than the forced-close rule charges.
- One venue. Coins that never had a pair there are missing, and so are contracts that venue never listed.
- A bar on file is not proof that an order could be filled, least of all in a contract's last days.
- Two samples and two shorts are four results. Only one is judged, named above.

## Order of work

1. Ledger rows, this draft and the config entry are committed before any code.
2. The builder writes the collection and scoring code with tests on made-up prices. No return on real prices.
3. Two other models read the code against this plan. Their findings are fixed or written here.
4. Freeze: this file renamed, status frozen, code pushed. One run by the lead. Result page `docs/research/56_replay_16_hot_five_hedged.md` written by script.
