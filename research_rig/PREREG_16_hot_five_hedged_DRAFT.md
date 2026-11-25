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
- Funding: every recorded funding payment after the entry time and up to and including the exit time, at its own rate, on the contract's dollar size at the last completed hourly trade close with volume before the payment. A short receives a positive rate and pays a negative one. Funding is reported apart from the price gain.
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
- Live, in full: a contract is live on a Monday when (i) it has a trade bar at the entry hour, (ii) it had a funding payment in the `replay_16_plan.live_funding_lookback_hours` hours before, and (iii) removed before the freeze, see "Changed before the freeze".
- This is a stand-in read from the files, not the venue's own listing record. The venue stopped new orders about two days before settlement on at least two contracts while bars and payments went on. Stated as a limit.
- A contract that stops paying: checked each hour with past facts only. When a contract has had no funding payment in the trailing `replay_16_plan.live_funding_lookback_hours` hours, it is closed at the next hour's open. If there is no such bar it is closed at the last trade close on file, flagged. Its part stays in dollars until Monday.
- Weekly exit with no bar: a contract with no bar at the exit Monday hour is closed at the last trade close on file, flagged. Nothing is carried into the next week.
- Basket count: the number of live contracts is counted after leaving out the week's five named coins. All five named coins are left out of the short, also when their long side was not filled.
- Short B: if one of the two contracts is not live the whole short goes to the other. If neither is, the week has no short and is flagged.
- Order inside an hour: a funding payment stamped on the hour is applied first. Then the forced close is checked on that hour's high, the entry hour included. If the hour opens at or above the forced-close level, the close is at the open. The weekly exit comes last. Payment times are rounded to the minute.
- Mark or trade bar: chosen hour by hour. A missing mark bar means the trade bar's high is used for that hour.
- Losses are not capped at a contract's part. A loss beyond it is taken from the rest of the account. If the account reaches zero the year ends there at a total loss.
- Only dollars back the short. Coins held on the long side and lots waiting to be sold are not counted as backing. The account is ruined when the whole book's value, waiting spot lots included, reaches zero.
- Random draws: five coins from the rankable list as in plan 13, the same weeks, the same Monday-only fill rule, the short leaving out that draw's five coins. The same `replay_16_plan.random_draws` draws are used at every cost level.
- A week is flagged when the coin list was carried from an earlier snapshot, when the short fell back to short B or had no short, when any contract in it was closed at a last close, or when a held coin misses more than `replay_16_plan.max_missing_hours` hours. A year with more than `replay_16_plan.max_flagged_week_share_pct` percent of its weeks flagged is reported and cannot count toward marks 1 to 3. Mark 4 applies to all seven years.
- Scale figures: rule A without the short is the long side at full size with this plan's Monday-only fills. The short alone is the short side at the book's size with the long part left in dollars. The paper lean is each week's gain of the hot five less the gain of all rankable coins of the same sample, before costs, compounded week by week inside the year.
- Contract maps: spot pairs and futures contracts each have their own dated segments. A bundled or re-used futures ticker gets its own segment and is never joined to another.
- The held-back list is read again from the saved snapshot pages (the stored plan 13 lists stop too early). The top list must come out identical to plan 13's, and the fingerprints of both lists are stored before any price is collected for the new coins.

## Definitions added 2026-11-25 19:48 UTC

Still before any futures price or funding rate was read.

- The venue's live data service refuses requests from this machine's location. It is not read by another route. Funding comes from the public bulk archive alone, which does not yet hold November 2026. So for this plan 2026 ends at the last Monday whose whole week of funding is in the archive, and the date is printed in the result. This shortens 2026 against plan 13.
- Condition (iii) of "live" was removed before the freeze.
- At the exit hour only the open counts: the position is closed there, and that hour's high is not used. If that open is at or above the forced-close level, it is a forced close at the open. The entry hour's high does count.
- The two coin lists were read from the saved pages and fingerprinted before any new price was collected: viewed list `ccb0fe0d5485`, held-back list `f5bea224faad`, both together `3cc9dcf9bed1` (first twelve characters).

## Which coin is which (first written 2026-11-25 20:34 UTC, rewritten before the freeze)

Written before the freeze and before any return was computed. Reason: two Binance tickers on the list turned out to be other assets (QQQUSDT and EWTUSDT are stock fund products there, not the coins with those tickers on CoinMarketCap). A ticker alone is not proof of identity. The first version of this section judged each mapping once, using every saved month up to 2026. Two code audits found that this let later months decide earlier weeks. This version decides each Monday with what was known by that Monday.

- Only a mapping that is CONFIRMED as of a Monday is used that week, in every sample and every yardstick. An UNKNOWN mapping is left out of that week.
- Price level, as of a Monday: for each saved monthly CoinMarketCap page dated on or before that Monday in which the coin appears, the saved USD price is compared with Binance's hourly bars for the UTC day of the page's own quote time, in the same token unit. The day must be over by that Monday and must lie inside the mapping's own dates (after its start bound and before any date fence). A month matches if the saved price lies between the day's low less 5% and the day's high plus 5%. A month counts only if Binance has a full day of bars. CONFIRMED when there is at least one such month and 80% or more of them match so far. REMOVED when there are at least three and fewer than half match. Otherwise no verdict from prices.
- Notices: with no verdict from prices, a mapping that Binance's own listing or contract notices tie to the project can be confirmed by them, but only if the date of every notice relied on is known and the latest of those dates is before that Monday. Only the date of a notice is stored, not its hour, so a notice dated on the Monday itself does not count until the Monday after. A notice with no checked date cannot confirm.
- Two kinds of removal. A ticker shown to be another asset, or two assets mixed in one file, is removed for every week (QQQ, EWT, UNI COIN, the old PUMP and LIT files, Terra 2.0 on the old LUNA file). A delisting, a swap or a re-denomination is a date fence: the mapping can be used before that hour, if the price-level check as of that Monday confirms it, and not after (SC to 2022-06-17 09:00 UTC, RAY to 2022-11-15 04:00, SRM to 2022-11-15 04:30, HNT to 2023-03-20 09:00, AGIX and OCEAN futures to 2024-06-25 09:00 and spot to 2024-07-01 03:00). The delisting notice is not evidence for the mapping. A bar counts only if it ends at or before the fence, so a bar that crosses a fence is not read at all, and a position still open is closed at the last usable close and flagged. A successor starts at the first hourly open at or after its start. Raydium's later contract (RAYSOLUSDT, from 2024-12-10) is not in the stored files, so Raydium has no contract after the fence.
- Swaps inside one ticker: KNC (2021-05-21 08:00 UTC, approximate), DYDX (2024-05-07 00:00, approximate) and BNX (old ends 2023-02-11 04:00, new starts 2023-02-22 14:45, FORM from 2025-03-17 09:00) are cut at the same hours on spot and on futures, so a ranking look-back never runs across a swap. The KNC and DYDX hours are not checked against the venue's index record.
- Bars older than the coin: a Binance file can start before CoinMarketCap's date-added for the coin (pre-market and launch-pad trading). A lead of 60 days or less is allowed, and then no bar, funding payment or price-level day before the date-added is used for that coin, in ranking, entries, exits or marks. That only sets where the mapping starts; it still needs the price-level check. Where the lead is known only as a range, its upper end is used. A lead of more than 60 days, or one that cannot be bounded, removes the mapping (SUN spot, 264 to 293 days; SENT futures, 69 days).
- These checks read price levels, clocks and volumes and print counts. They compute no return of any rule.
- MEASURED 2026-11-25, using every month (shown for reference, not used to decide a week): 556 mappings checked, 520 CONFIRMED (251 spot, 269 futures), 16 REMOVED, 20 UNKNOWN. Another 340 listed pairs have no stored bars and were never eligible. As of the last scored Monday, 2026-10-19: 522 CONFIRMED, 24 REMOVED, 10 UNKNOWN; a mapping past its date fence counts as removed on that day.
- MEASURED on the stored futures files of both lists together, live coin-weeks on a Monday with a confirmed contract, by year 2020 to 2026. Held-back list: 281, 1413, 1614, 1907, 2060, 2198, 1723. Viewed list: 1322, 2178, 2327, 2406, 2552, 2397, 1952.
- Limits. A confirmed mapping can still have single months outside the range; those months are not removed. The mappings left out were dropped for an identity reason, not a price reason, but a sample without them is not the full list. Early in a coin's life one matching month is enough to confirm it. MEASURED before the run, confirmed coin-weeks that rest on fewer than three comparable months, spot then futures: held-back list 1,112 and 930, viewed list 675 and 777, US roster 225 and 344. Of those, resting on one matching month and no dated notice: 164 and 247, 56 and 229, 25 and 66. How many of these are a wrong asset is UNKNOWN: one price inside a wide range cannot tell two assets with similar price levels apart. On the held-back list, 27 spot and 18 futures coin-weeks confirmed by one or two matching months have no confirmation under the every-month reference. Asking for three months would drop every coin's first two months on the list, which is when a new coin is most likely to be hot, so the rule stays and the result shows these counts.

UNKNOWN on the every-month reference (CoinMarketCap id, then pair):

- spot (10); 1414 XZCUSDT, 1521 KMDUSDT, 1785 GASUSDT, 2062 AIONUSDT, 2691 PNTUSDT, 13631 MANTAUSDT, 29676 AEVOUSDT, 35429 LAYERUSDT, 36119 WALUSDT, 38337 0GUSDT.
- futures (10); 693 XVGUSDT, 1230 STEEMUSDT, 1727 BNTUSDT, 1757 FUNUSDT, 2090 LAUSDT, 5026 OXTUSDT, 7288 XVSUSDT, 8857 ANCUSDT, 9903 CVXUSDT, 18679 XCNUSDT.

REMOVED on the every-month reference (CoinMarketCap id, then pair):

- spot (9); 1518 SKYUSDT, 1765 AUSDT, 2239 AAVEUSDT, 3513 SUSDT, 3890 POLUSDT, 4086 EGLDUSDT, 4113 UNIUSDT, 4256 KAIAUSDT, 10529 SUNUSDT. Seven of these are an old coin's id pointed at its successor's pair; the old coin's own pair is not removed.
- futures (7); 4113 UNIUSDT, 4644 QQQUSDT, 5268 EWTUSDT, 20314 LUNAUSDT, 36507 PUMPUSDT, 38868 SENTUSDT, 39125 LITUSDT.

The full dated policy is one file on the research machine. Both scorers refuse any other file.

Shared identity policy SHA-256 5b6aca5959b5c2a4a30033278794937f447f2c899cb6bd828eff81d3df3a248c.

## Changed before the freeze

Every change below was made on 2026-11-25 between 20:40 and 22:10 UTC, after two code audits by other models (16 findings and 12 findings) and before any return of a rule or a yardstick was worked out on real prices. Where a line below differs from a line above, the line below holds.

- Which coin is which: rewritten as above, decided week by week with past facts.
- Live contract: part (iii), which asked for a funding file covering the week ahead, is removed, because it looked at a file that did not yet exist on that Monday. A contract is live on a Monday when it has a trade bar with volume at the entry hour and a recorded funding payment before the entry and inside the look-back, under the same coin identity and not inside a dead spell. Funding paid at the entry hour is not earned. The result shows how many coin-weeks the old part (iii) would have left out (MEASURED before the run: none in any year).
- The last scored week starts Monday 2026-10-19 UTC and ends at 2026-10-26 00:00 UTC. A funding payment stamped at that minute counts for that week, as the funding rule says, and no later payment is read. The futures bar that opens at that minute is read the way every week's exit bar is: its open is the exit price and its volume says whether that open could trade. A dead spell is counted only on bars up to and including that one. No new position opens at or after that minute. Only the first later spot open can change a waiting lot; the other fields of that bar are checked for being well formed and are not used.
- Cut-off files: a scan of all 44,713 stored monthly files found files that stopped short or started late (futures trades in February and April 2022, mark prices in July 2021 and July 2022, and four single files). Their good rows were kept and the missing whole days were filled from the venue's daily files, 349 of them, each checked against the venue's published checksum. Nothing was made up and no other route to the venue was used. Five days of one contract remain missing (ICP futures, 2022-09-22 to 2022-09-26); the contract counts as not trading on those days.
- Dead spells: a bar with no volume cannot fill an order. From the first hour of a run of 24 or more hourly trade bars in a row with no volume, a contract is not available until a bar with volume. Missing hours do not count toward the 24, and do not end a dead spell once it has started. An open position is closed at the last close that had volume, pays the normal cost, earns no funding in the dead spell, is flagged, and is not reopened that week. The same holds for the yardsticks. Whether a quiet hour is the start of a 24-hour run is known only afterwards, also when the 24th quiet hour falls after the week ended; this is a rule about what could have been traded, not an order a trader could have sent. A part that holds nothing when its contract goes dead is retired for the rest of the week and flagged, with no price effect. A signal is not taken when its look-back touches a dead spell. The rule applies to futures only: the spot files are read without volume, so spot buys and sells are not checked for it. It does not touch the rule and the yardsticks alike: a yardstick that always holds is closed at the last good close and pays the fee, while a rule that is flat loses nothing. The result shows the number of dead-spell closes for the rule and for each yardstick.
- Forced close with no mark bar: when an hour has a trade bar and no mark-price bar, the trade bar's high is used for a short. (The low for a long applies only to a long with a forced close; no scored cell has one.) The result shows how many stored hours have no mark bar (MEASURED: 20,341 in plan 16's files, 26,110 in plan 17's).
- A spot sale that cannot fill before the year ends is filled at the first open of the same coin under the same dated mapping, also in the next year. It belongs to the year the position was opened in and pays for nothing in the next year's account. With no later open it is marked at its last close and flagged.
- Freeze record: after both plans are final, one record is written with the fingerprints of both plan files, all scoring and reporting code, the settings, the coin lists, the US roster file, the three file lists of the archive and the identity policy. The lead keeps the record's own fingerprint apart and gives it to each run. A run refuses before taking its lock if anything differs, and checks again after the lock and before opening a bar. A change found by that second check uses up the one run without a bar being read.
- Result pages are written from the stored results only. They refuse if either plan's fingerprint differs, and they do not open a bar.
- The loader reads with two workers. Measured on a load with no scoring: 977,736 KiB at peak for plan 16 and 1,310,472 KiB for plan 17 (about 1.00 and 1.34 GB). The lead runs each scorer once, with nothing else heavy on the machine.

Plan 16 only:

- New purchases on a Monday are sized from cash plus spot lots still waiting to be sold, marked at their last close. With no cash, nothing is bought, also when that marked value is positive. A purchase with its fee is capped so that the dollars left after it are at least the size of the short, which with a short equal to the purchase means at most half of free cash. The cap binds only when waiting lots tie up cash. The short is sized on the dollars really spent on spot after the buy fee. Cash freed in the week buys nothing before Monday. The check for a ruined account counts waiting lots.
- The market short leaves out the week's five named coins by coin id, through the dated contract map, also a named coin that did not fill and a contract quoted per 1,000 coins. Another coin that only shares a ticker is not left out.
- The stored result holds, by week, the flags, the number of live basket contracts and of bitcoin and ether contracts, and whether the week fell back to short B. The result page shows them by year, with the old part (iii) count.

## How often this passes with no edge

MEASURED by the first auditor on made-up worlds through this plan's own engine, on the code as it stood at the first audit (50 invented coins in two lists of 25, hourly prices with no drift, invented funding, every week eligible, judged cost, 192 worlds of seven years): all four marks together passed in 1 of 192. Limit: a clean tape with no missing bars and no identity gaps, so this is not a false-pass rate for real markets. The plan 17 figure in that plan is a different test and says nothing about this one. A rough guide only: a year lands above the 75th percentile of random fives by luck about one time in four, which is the rank comparison alone and not the rate for any mark. A check on the code as frozen, with no edge and with a planted edge, is run before the freeze and its result is written under this line.

MEASURED before the freeze on made-up worlds through this plan's own engine (20 worlds of seven full years, 140 years per arm, judged cost). With no edge built in, all four marks passed in 0 of 20 worlds; taken one at a time the four marks passed in 1, 0, 1 and 0 of 20. With an edge planted, each Monday's five biggest risers on the held-back list given an extra expected 2% over five days, all four passed in 15 of 20; one at a time 20, 18, 16 and 20. So the test can see an edge of that size about three times in four and misses it about one time in four. These are invented price paths, not a pass rate for real markets and not evidence that the rule has an edge. The check ran on the code before the change that only counts dead-spell closes; two full made-up worlds were run on both versions and matched on every yearly figure, every mark and every recorded trade list.

## How this can fool us

- The short basket is made of larger coins than the held-back long side, so the book also carries "small coins against large coins". The paper lean figure shows how much of the result that is.
- Small coins cost more to trade than the judged spot cost. The dearer cost level is shown.
- Hourly bars cannot show a squeeze inside the hour. A real short can be closed out at a worse price than the forced-close rule charges.
- One venue. Coins that never had a pair there are missing, and so are contracts that venue never listed.
- A bar on file is not proof that an order could be filled, least of all in a contract's last days.
- The price files were repaired and the coin map was built with later files in view. The rules for both use past facts only, but which contracts are in the archive at all is today's knowledge.
- Two samples and two shorts are four results. Only one is judged, named above.

## Order of work

1. Ledger rows, this draft and the config entry are committed before any code.
2. The builder writes the collection and scoring code with tests on made-up prices. No return on real prices.
3. Two other models read the code against this plan. Their findings are fixed or written here.
4. Freeze: this file renamed, status frozen, code pushed. One run by the lead. Result page `docs/research/56_replay_16_hot_five_hedged.md` written by script.
