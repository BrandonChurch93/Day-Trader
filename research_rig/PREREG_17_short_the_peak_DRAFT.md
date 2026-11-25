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
- Shown only, not a mark: the 1x rule at each of `replay_17_plan.us_costs_bps` a side, for every list. These are the fees for an order that takes the price on Kraken spot and US margin, at the $10,000 tier and at the entry tier, read from the venue's fee page on 2026-11-25. Added before the freeze because the judged cost is that of a large futures exchange, far below what a new US account pays where it can short these coins today. They change the fee only: that venue's own spreads, margin charges, prices and funding are not in them.
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
- Signals and fills use the contract's own trade bars. Spot bars rank the coins on Monday and make the all-coins figure; they give the rule no signal and no fill.
- The 7-day comparison inside the rule uses the contract's close 168 hours before the signal close. A contract with less history than that gives no signal.
- A short's loss is not capped at its part at 1x. A loss beyond the part is taken from the rest of the account. If the account reaches zero the year ends there.
- "Short, then the bounce": the long is opened on the same contract at the open where the short covered at its target, only then, and is closed at the next hour's open when the last close is `replay_17_plan.take_pct` percent above its entry, `replay_17_plan.stop_pct` percent below it, or after `replay_17_plan.max_hold_hours` hours. After it closes the part is in dollars again.
- Random draws: five coins from the rankable list each Monday as in plan 13, the same weeks and the same rule. A drawn coin with no live contract leaves its part in dollars, exactly as a hot coin does. Nothing is drawn again to fill the gap.

## Definitions added 2026-11-25 19:54 UTC

Written after the builder read the draft and listed what it left open. No futures price, no funding rate and no price of a held-back coin had been read.

- A queued order whose next bar is missing waits for the next bar of the same contract, as in plan 13.
- A part in a week is flagged when its contract misses more than `replay_16_plan.max_missing_hours` hours in the week, when an order was delayed by a missing bar, when it was closed at a last close, or when the coin list was carried. A part left in dollars because its coin had no live contract is counted and not flagged.
- Rule S at 1x has no forced close. Its own stop is the exit, and a loss is whatever the fill gives. Yardstick (b) and the short of all coins are held for the week and use plan 16's forced close.
- At `replay_17_plan.shown_leverage` times, a forced close costs the whole part and nothing more, as in plan 13. It is checked on each hour's high, the entry hour included. A cover order already queued fills at the next open; if that open is at or above the forced-close level the part is lost.
- Exits are decided on the hourly close. If more than one holds at the same close the order is target, then stop, then time.
- "Short, then the bounce": the long is at 1x, pays funding with the sign turned round, has no forced close, and is opened only after a short that covered at its target. No bounce follows a stop, a time exit, a contract that stopped paying or the week's end.
- Each part is sized from its own value after each closed trade and compounds inside the week, as in plan 13's rule B. The five parts are made equal again each Monday. A part at or below zero stays idle until Monday and its shortfall is taken from the account then. The account is checked for zero at each closed trade and each Monday.
- A contract closed because it stopped paying funding is not traded again that week, also if payments come back.
- The year's end follows plan 16.
- Reported beside the judged figures: each mark at the lower cost level and with no cost and no funding at all. "Failed on costs" means the marks hold with no cost and not at the judged cost.

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
- Limits. A confirmed mapping can still have single months outside the range; those months are not removed. The mappings left out were dropped for an identity reason, not a price reason, but a sample without them is not the full list. Early in a coin's life one matching month is enough to confirm it. MEASURED before the run, confirmed coin-weeks that rest on fewer than three comparable months, spot then futures: held-back list 1,112 and 930, viewed list 675 and 777, US roster 225 and 344. Of those, resting on one matching month and no dated notice: 164 and 247, 56 and 229, 25 and 66. How many of these are a wrong asset is UNKNOWN: one price inside a wide range cannot tell two assets with similar price levels apart. On the held-back list, 27 spot and 18 futures coin-weeks confirmed by one or two matching months have no confirmation under the every-month reference. Asking for three months would delay some confirmations that rest on prices alone, in a coin's first months on the list, which is when a new coin is most likely to be hot, so the rule stays. These counts are recorded here and are not worked out again in the result.

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
- The last scored week starts Monday 2026-10-19 UTC and ends at 2026-10-26 00:00 UTC. A funding payment stamped at that minute counts for that week, as the funding rule says, and no later payment is read. The futures bar that opens at that minute is read the way every week's exit bar is: an ordinary exit uses its open if that open could trade, its volume says whether it could, and a forced close or a close at the last good price follows its own rule. A dead spell is counted only on bars up to and including that one. No new position opens at or after that minute. Only the first later spot open can change a waiting lot; the other fields of that bar are checked for being well formed and are not used.
- Cut-off files: a scan of all 44,713 stored monthly files found files that stopped short or started late (futures trades in February and April 2022, mark prices in July 2021 and July 2022, and four single files). Their good rows were kept and the missing whole days were filled from the venue's daily files, 349 of them, each checked against the venue's published checksum. Nothing was made up and no other route to the venue was used. Five days of one contract remain missing (ICP futures, 2022-09-22 to 2022-09-26); the contract counts as not trading on those days.
- Dead spells: a bar with no volume cannot fill an order. From the first hour of a run of 24 or more hourly trade bars in a row with no volume, counted inside one dated mapping only, a contract is not available until a bar with volume. Missing hours do not count toward the 24, and do not end a dead spell once it has started. An open position is closed at the last close that had volume, pays the normal cost, earns no funding in the dead spell, is flagged, and is not reopened that week. The same holds for the yardsticks. Whether a quiet hour is the start of a 24-hour run is known only afterwards, also when the 24th quiet hour falls after the week ended; this is a rule about what could have been traded, not an order a trader could have sent. A part that holds nothing when its contract goes dead is retired for the rest of the week and flagged, with no price effect. A signal is not taken when its look-back touches a dead spell. The rule applies to futures only: the spot files are read without volume, so spot buys and sells are not checked for it. It does not touch the rule and the yardsticks alike: a yardstick that always holds is closed at the last good close and pays the fee, while a rule that is flat loses nothing. The result shows the number of dead-spell closes for the rule and for each yardstick.
- Forced close with no mark bar: when an hour has a trade bar and no mark-price bar, the trade bar's high is used for a short. (The low for a long applies only to a long with a forced close; no scored cell has one.) The result shows how many stored hours have no mark bar (MEASURED: 20,341 in plan 16's files, 26,110 in plan 17's).
- In this plan spot prices rank the coins every Monday, for every list. Spot positions are opened only for the all-coins figure. A spot sale that cannot fill before the year ends is filled at the first open of the same coin under the same dated mapping, also in the next year. It belongs to the year the position was opened in and pays for nothing in the next year's account. With no later open it is marked at its last close and flagged.
- Freeze record: after both plans are final, one record is written with the fingerprints of both plan files, all scoring and reporting code, the settings, the coin lists, the US roster file, the three file lists of the archive and the identity policy. The lead keeps the record's own fingerprint apart and gives it to each run. A run refuses before taking its lock if anything differs, and checks again after the lock and before opening a bar. A change found by that second check uses up the one run without a bar being read.
- Result pages are written from the stored results only. They refuse if either plan's fingerprint differs, and they do not open a bar.
- The loader reads with two workers. Measured on a load with no scoring: 977,736 KiB at peak for plan 16 and 1,310,472 KiB for plan 17 (about 1.00 and 1.34 GB). The lead runs each scorer once, with nothing else heavy on the machine.

Plan 17 only:

- Flag share for a year: flagged part-weeks divided by all part-weeks that were given a coin with a live contract that Monday, whether or not the rule traded. Parts with no live contract are counted apart and are in neither figure.
- The dated identity rule applies to rule S and to every yardstick.
- The write-up says "failed on timing" when enough of the years that can count (after the trade-count and flag screens) ended above 1.00 and too few of them beat yardstick (b), and "failed on rising years" when marks 1 and 2 hold and too few of those years had a rising all-coins figure.
- One more cell, shown and not judged (ledger 151): rule S at 1x, judged cost and funding, on the coins a US account can short today. The roster is the 29 coins MEASURED on 2026-11-25 as shortable on Kraken or Coinbase, without bitcoin, ether and two coins that are not hot-coin candidates (USDC, PAXG). The roster file's SHA-256 is 50be7cc83aaa8fe22b401ba0531d987a63c3b37a220c9373fd8c5bd200342faf and the freeze record pins it. Each Monday the hot five are up to five roster coins with the largest 7-day gain on spot, same tie rule, with no market-cap rank asked for, each given one fifth of the account. A picked coin trades only if it has a confirmed, live contract that Monday; otherwise its fifth stays in dollars and it is not replaced. A roster coin without a usable 7-day spot look-back under its dated mapping cannot be ranked that week (one coin, VVV, never can).
- Limits of that cell, stated now: the roster is today's list, so it knows which coins lasted and got a US listing. Several of its coins were in plan 13's viewed list. Binance futures prices stand in for US venue prices, and US fees and funding differ. It does not show that a US account could have traded these on those dates.

## How often this passes with no edge

MEASURED by the second auditor on made-up worlds through this plan's own engine (12 coins, hourly prices with no drift, 60 one-year worlds per setting, three settings): at the judged cost all three marks together passed in none; mark 1 alone in about 1 in 1,000 or fewer. With no cost and no funding all three passed in 0.5% to 1.6%, so "failed on costs" can be said by luck about 1 time in 100. Limit: in those worlds the all-coins figure rises in only 25% to 30% of years, so mark 3 is harder there than in real years. A check on the engine as it stood just before the freeze, with no edge and with a planted edge, is run before the freeze and its result is written under this line.

MEASURED before the freeze on made-up worlds through this plan's own engine (20 worlds of seven full years, 140 years per arm, judged cost). With no edge built in, all three marks passed in 0 of 20 worlds, and each mark alone in 0 of 20. With an edge planted, a coin given an extra expected 6% fall over 24 hours after its first signal of the week and then three days of recovery, all three passed in 15 of 20; one at a time 20, 20 and 15. The mark that needs a win in rising years is the one that misses. So the test can see an edge of that size about three times in four. A smaller edge might be missed more often; only this one size was measured, so a fail here does not rule out a small edge. These are invented price paths, not a pass rate for real markets and not evidence that the rule has an edge. The check ran on the code before the change that only counts dead-spell closes; two full made-up worlds were run on both versions and matched on every yearly figure, every mark and every recorded trade list.

## How this can fool us

- Hourly bars. A stop at 5% is checked on the close and filled at the next open; a real stop on a fast coin can fill far worse in a squeeze, and a short's loss has no ceiling.
- A bar on file is not proof an order could be filled, and small contracts are thin. The dearer cost level is shown.
- A pass here is a pass at the costs of a large futures exchange. The two shown-only fee levels show how the rule's yearly net changes under the fees of a US account; no yardstick or mark is worked out again at them.
- One venue, and only coins it listed a contract for. Coins that were hot and had no contract are not in the test, and those may be the ones he traded.
- A fixed 5% is not his eye for where a fall stalls.
- The idea was chosen after seeing the buying side fail on a list that moves with this one.
- The price files were repaired and the coin map was built with later files in view. The rules for both use past facts only, but which contracts are in the archive at all is today's knowledge.

## Order of work

1. Ledger rows, this draft and the config entry are committed before any code.
2. The builder adds the rule to the plan 16 code base with tests on made-up prices. No return on real prices.
3. Two other models read the code against this plan.
4. Freeze both plans. One run each by the lead. Result page `docs/research/57_replay_17_short_the_peak.md` written by script.
