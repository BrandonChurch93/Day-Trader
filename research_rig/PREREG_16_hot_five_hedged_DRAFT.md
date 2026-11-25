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
- A contract is live on a Monday when it has a bar at the entry hour and at least one funding payment in the `replay_16_plan.live_funding_lookback_hours` hours before. Past facts only. A contract that stops paying funding during the week is closed by the rule under the added definitions, which uses past facts only, and its part stays in dollars until Monday.
- Forced close: a contract whose hourly high reaches `replay_16_plan.short_stop_pct` percent above its entry is closed there at that loss plus the cost. It is not reopened that week. The mark-price bar is used when on file, the trade bar otherwise. Every such close is counted and reported.

## Costs

- Three cost levels, each a set of three figures in basis points a side for spot, basket futures and bitcoin and ether futures: `replay_16_plan.cost_low`, `replay_16_plan.cost_judged`, `replay_16_plan.cost_high`. Only the judged set counts. The other two are shown.
- Funding: every recorded funding payment after the entry time and up to and including the exit time, at its own rate, on the contract's dollar size at the last completed hourly trade close at or before the payment. A short receives a positive rate and pays a negative one. Funding is reported apart from the price gain.
- Costs are charged on every side of every weekly reset, also for a coin that stays in the list, as plan 13 did. Costs come out of the dollar part.

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
- Funding comes from the venue's public bulk archive only. See the note on the last weeks of 2026 below.
- Random draws use the same weeks, the same costs, the same short and the same rule for parts left in dollars.

## Definitions added 2026-11-25 19:46 UTC

Written after the builder read the draft and listed what it left open. No futures price, no funding rate and no price of a held-back coin had been read.

- Long fills: a hot coin with no bar at the Monday 00:00 hour leaves its part in dollars for the week. Plan 13 waited up to six hours; this plan does not, because the short has to be sized at one moment.
- Short size: the dollar value of the coins really bought on Monday at their fill prices. Set once, never adjusted in the week.
- Live, in full: a contract is live on a Monday when (i) it has a trade bar at the entry hour, (ii) it had a funding payment in the `replay_16_plan.live_funding_lookback_hours` hours before, and (iii) funding records for the contract cover the week (the month's archive file exists, or the venue's public history returns payments). (iii) is a filter on our files, counted and reported.
- This is a stand-in read from the files, not the venue's own listing record. The venue stopped new orders about two days before settlement on at least two contracts while bars and payments went on. Stated as a limit.
- A contract that stops paying: checked each hour with past facts only. When a contract has had no funding payment in the trailing `replay_16_plan.live_funding_lookback_hours` hours, it is closed at the next hour's open. If there is no such bar it is closed at the last trade close on file, flagged. Its part stays in dollars until Monday.
- Weekly exit with no bar: a contract with no bar at the exit Monday hour is closed at the last trade close on file, flagged. Nothing is carried into the next week.
- Basket count: the number of live contracts is counted after leaving out the week's five named coins. All five named coins are left out of the short, also when their long side was not filled.
- Short B: if one of the two contracts is not live the whole short goes to the other. If neither is, the week has no short and is flagged.
- Order inside an hour: a funding payment stamped on the hour is applied first. Then the forced close is checked on that hour's high, the entry hour included. If the hour opens at or above the forced-close level, the close is at the open. The weekly exit comes last. Payment times are rounded to the minute.
- Mark or trade bar: chosen hour by hour. A missing mark bar means the trade bar's high is used for that hour.
- Losses are not capped at a contract's part. A loss beyond it is taken from the rest of the account. If the account reaches zero the year ends there at a total loss.
- Only dollars back the short. Coins held on the long side are not counted as backing.
- Random draws: five coins from the rankable list as in plan 13, the same weeks, the same Monday-only fill rule, the short leaving out that draw's five coins. The same `replay_16_plan.random_draws` draws are used at every cost level.
- A week is flagged when the coin list was carried from an earlier snapshot, when the short fell back to short B or had no short, when any contract in it was closed at a last close, or when a held coin misses more than `replay_16_plan.max_missing_hours` hours. A year with more than `replay_16_plan.max_flagged_week_share_pct` percent of its weeks flagged is reported and cannot count toward marks 1 to 3. Mark 4 applies to all seven years.
- Scale figures: rule A without the short is the long side at full size with this plan's Monday-only fills. The short alone is the short side at the book's size with the long part left in dollars. The paper lean is each week's gain of the hot five less the gain of all rankable coins of the same sample, before costs, compounded week by week inside the year.
- Contract maps: spot pairs and futures contracts each have their own dated segments. A bundled or re-used futures ticker gets its own segment and is never joined to another.
- The held-back list is read again from the saved snapshot pages (the stored plan 13 lists stop too early). The top list must come out identical to plan 13's, and the fingerprints of both lists are stored before any price is collected for the new coins.

## Definitions added 2026-11-25 19:48 UTC

Still before any futures price or funding rate was read.

- The venue's live data service refuses requests from this machine's location. It is not read by another route. Funding comes from the public bulk archive alone, which does not yet hold November 2026. So for this plan 2026 ends at the last Monday whose whole week of funding is in the archive, and the date is printed in the result. This shortens 2026 against plan 13.
- Condition (iii) of "live" is a statement about which files we hold, fixed before collection. It is never read from a later payment.
- At the exit hour only the open counts: the position is sold there, and that hour's high is not used. The entry hour's high does count.
- The two coin lists were read from the saved pages and fingerprinted before any new price was collected: viewed list `ccb0fe0d5485`, held-back list `f5bea224faad`, both together `3cc9dcf9bed1` (first twelve characters).

## Definitions added 2026-11-25 20:34 UTC: which coin is which

Added before the freeze and before any return was computed. Reason: two Binance tickers on the list turned out to be other assets (QQQUSDT and EWTUSDT are stock fund products there, not the coins with those tickers on CoinMarketCap). A ticker alone is not proof of identity.

- Only mappings with status CONFIRMED are used, in every sample and every yardstick. The policy file's fingerprint is 4965f08c2692. Both scorers refuse a different fingerprint.
- Route 1, notices: Binance's own listing and contract notices tie the pair to the project. A notice can confirm or remove.
- Route 2, price level: for each saved monthly CoinMarketCap page where the coin appears, the saved USD price is compared with Binance's hourly bars for the UTC day of the page's own quote time, in the same token unit. A month matches if the saved price lies between the day's low less 5% and the day's high plus 5%. A month counts only if Binance has a full day of bars. With at least three such months: CONFIRMED at 80% or more matching, REMOVED under 50%, UNKNOWN between. With fewer than three there is no verdict from this route.
- Final status: REMOVED if either route removes. CONFIRMED if the price-level route confirms, or if it gives no verdict and a notice confirms. Everything else is UNKNOWN and left out.
- This check reads price levels and prints only counts of matching months. It computes no return of any rule.
- A first version compared the saved price with one hourly close within 5%. It was tried and replaced before the freeze, because it measured clock mismatch and not identity. MEASURED, mappings with three or more comparable months, by share of months matching in tenths from 0-10% to 90-100%: hourly close 4, 2, 3, 13, 10, 30, 90, 166, 113, 62; UTC day range 0, 0, 1, 1, 0, 1, 0, 1, 1, 488.
- MEASURED result: 556 mappings checked, 514 CONFIRMED (248 spot, 266 futures), 22 REMOVED, 20 UNKNOWN. Another 340 listed pairs have no stored bars and were never eligible.
- MEASURED held-back list, live coin-weeks with a confirmed contract by year 2020 to 2026: 279, 1343, 1582, 1902, 2069, 2175, 1711 (before the identity check: 283, 1427, 1612, 1927, 2108, 2223, 1774). Viewed list: 1375, 2185, 2273, 2408, 2552, 2393, 1952.
- Limits. A confirmed mapping can still have single months outside the range, for example around a token swap; those months are not removed. KNC and DYDX each have two CoinMarketCap ids that both confirm against one ticker, and the spot pairs of those and of BNX run across a swap without a break, so the hour of the swap is not resolved. The 42 left out were dropped for an identity reason, not a price reason, but a sample without them is not the full list.

UNKNOWN, left out (CoinMarketCap id, then pair):

- spot (10); 1414 XZCUSDT, 1521 KMDUSDT, 1785 GASUSDT, 2062 AIONUSDT, 2691 PNTUSDT, 13631 MANTAUSDT, 29676 AEVOUSDT, 35429 LAYERUSDT, 36119 WALUSDT, 38337 0GUSDT.
- futures (10); 693 XVGUSDT, 1230 STEEMUSDT, 1727 BNTUSDT, 1757 FUNUSDT, 2090 LAUSDT, 5026 OXTUSDT, 5665 HNTUSDT, 7288 XVSUSDT, 8857 ANCUSDT, 18679 XCNUSDT.

REMOVED (CoinMarketCap id, then pair):

- spot (12); 1518 SKYUSDT, 1765 AUSDT, 2239 AAVEUSDT, 3513 SUSDT, 3773 FETUSDT, 3890 POLUSDT, 4086 EGLDUSDT, 4113 UNIUSDT, 4256 KAIAUSDT, 6636 DOTUSDT, 6892 EGLDUSDT, 10529 SUNUSDT.
- futures (10); 1042 SCUSDT, 4113 UNIUSDT, 4644 QQQUSDT, 5268 EWTUSDT, 8526 RAYUSDT, 20314 LUNAUSDT, 36507 PUMPUSDT, 36645 XPLUSDT, 38868 SENTUSDT, 39125 LITUSDT.

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
