# Pre-registration 12: buying what members of Congress buy, after the trade becomes public

Status: frozen 2026-11-25 19:09 UTC by the builder. Written 2026-11-25 18:27 UTC before any price was joined to any disclosed trade; the code was then checked twice by a second model, which found seven faults that were fixed and said it was safe to run once. Nothing in this file or in `replay_12_plan` changes after this line. Ledger rows 135 to 143 in `research_rig/TRIAL_LEDGER.md`. Pretend trades on past prices.

## The claim

The owner, 2026-11-25 (`docs/DECISIONS.md`): people say you cannot go wrong following the stock trades of members of Congress such as Nancy Pelosi. The claim tested: a small account that buys a stock on the first trading day after a member's purchase becomes public, and holds it for a fixed time, does better than holding the S&P 500 fund SPY.

## What is known before the test

- A member has up to 45 days to report a trade. MEASURED on the collected record: the middle delay between trade and filing is 28 days, one in ten is 48 days or more, and 11% are over 45. A follower can only act after the filing. So every trade here is dated by its filing, never by the day of the trade.
- MEASURED 2026-11-25 from our price feed, dividends included: the fund that copies Democratic members' disclosures with real money (NANC) made +85.3% from its first day, 2023-02-07, to 2026-11-24. SPY made +81.5% and QQQ +110.3%. The Republican fund (KRUZ, renamed GOP in March 2025) made +61.0%. A second public source gives the same three figures ([Total Real Returns](https://totalrealreturns.com/n/NANC,GOP,SPY)).
- Published tests that buy after the filing found no gain over the market for the average disclosed purchase (`docs/research/48_congress_trades_evidence.md`). The expectation written down before the run: the all-members group does not pass. The open question is the two smaller groups.

## Data

- Trades: every Periodic Transaction Report of both chambers filed from `replay_12_plan.design_filed_from` on, 85,291 rows of stock and stock-option trades, each with the day of the trade and the day its first version was filed. Kept on the research machine, not in the repo. The helper that built it computed no return. A seeded sample of rows is checked against the original filings and the match rate is reported.
- One event is one member buying one stock in filings of one day, whatever the number of rows. Stock purchases only. Options are left out of the judged groups because the record does not always say what kind.
- The filing day is the day the report was received, as the official record gives it. It is not proof of the hour the public could first read it, and paper filings can appear later. So the main entry is the first trading day after the filing day, and every result is also worked out with the entry `replay_12_plan.late_entry_trading_days` trading days later and `replay_12_plan.late_entry_calendar_days` calendar days later.
- Prices: daily bars adjusted for splits and dividends. Entry is the open of the first trading day after the filing day. Exit is the close `replay_12_plan.holds_days` trading days later, counting the entry day as day 1.
- Costs: `replay_12_plan.cost_bps_per_side` basis points a side.
- A stock with no price history in our feed (many are companies that were later taken over or went under) cannot be traded here. The count and share of such events is reported next to every result. This flatters the buys, and it flatters each yardstick that uses the same stocks by the same amount.

## The three groups

1. All members, all stock purchases.
2. Large purchases: events where a row's reported value starts at `replay_12_plan.large_buy_min_usd` dollars or more.
3. Proven members: every `replay_12_plan.proven_refresh_days` trading days, the `replay_12_plan.proven_top_members` members whose own purchases, filed in the `replay_12_plan.proven_lookback_days` days before and with their holds already finished, did best against SPY (at least `replay_12_plan.proven_min_events` such events each). Only their new purchases are followed until the next refresh. Nothing from after the refresh day is used.

One member files far more than anyone else (about four in ten of all purchase events). So that one account does not decide the answer, the portfolio is built by member: on each day, every member with a purchase inside its holding time gets an equal share, split equally among that member's stocks. The same portfolio built by stock, every stock an equal share, is shown beside it and not judged.

## How it is measured

A calendar portfolio, because disclosed trades bunch on the same days and the same stocks and cannot be counted as separate bets. Each day the portfolio holds the stocks whose purchase was filed and whose holding time is still running. Its daily gain, after costs on what is traded, is set against SPY's on the same day.

Yardsticks:

- (a) SPY held over the same days. The main one.
- (b) The same groups built from the members' disclosed sales in place of purchases. If what they sell does as well as what they buy, the filings carry no information.
- (c) The same stocks bought on random days: for each event, the same stock bought on a day drawn within `replay_12_plan.random_date_window_days` days either side of the filing, `replay_12_plan.random_date_draws` times. This separates "they buy stocks that were going up anyway" from "the filing day matters".
- Shown for scale, not judged: QQQ, and NANC from its first day.

## Definitions fixed before the run

Written 2026-11-25 after the code builder read the draft and listed what it left open. No price had been joined to any trade when these were written.

- Time of day: every filing in the record carries only a day. Entry is never on the filing day.
- Entry days: everything is worked out three ways. Main: the open of the first trading day after the filing day. Later: `replay_12_plan.late_entry_trading_days` trading days after that. Latest: take the day that is `replay_12_plan.late_entry_calendar_days` calendar days after the filing day; the entry is the open of the first trading day after that day.
- "Did best against SPY" for the proven list: for each member, the mean over events of the stock's return less SPY's, each from the entry open to the exit close at the set-up's own hold, no costs. A hold is finished when its exit day is before the refresh day. Refresh days run every `replay_12_plan.proven_refresh_days` trading days from the first trading day of each half. A list applies to events filed on or after its refresh day and before the next. Ties go by name. In the design half the list is empty until members have enough finished events, so that group's portfolio starts later.
- "SPY over the same days": a mirror portfolio with the same weights on the same days and every stock swapped for SPY, no cost on the mirror. Days with no position are left out of both. "Beat SPY by the most per year" is the portfolio's growth divided by the mirror's, raised to 252 over the number of days, less 1. The bootstrap resamples the calendar months of the portfolio's gain less the mirror's in blocks of consecutive months, the block as long as the hold (the hold in trading days divided by `replay_12_plan.bootstrap_days_per_month`, rounded up: 1, 3 or 6 months). Blocks wrap from the last month to the first. MEASURED 2026-11-25 18:51 UTC on 1,000 made-up data sets with no edge in them, 48 months long: this mark passed 4.8% of the time at the 21-day hold, 6.6% at 63 days and 7.1% at 126 days, where 5% is the intent. So at the two longer holds mark 2 lets through about 7 in 100 with nothing there. It is one of five marks that must all hold, and this is said in the result.
- Purchases against sales (mark 3): the two portfolios hold on different days, so each is set against its own SPY mirror per year as above. Purchases pass when their figure is the higher. For the proven group, the sales side is the same members' sales. A large sale is a row whose range starts at `replay_12_plan.large_buy_min_usd` dollars or more.
- Costs: the portfolio is reset to its target weights each day and `replay_12_plan.cost_bps_per_side` is charged on that day's turnover (the sum of the gaps between target and drifted weights), which covers entries, exits and the reset. The same portfolio with no daily reset, charged on entries and exits only, is shown and not judged.
- A stock whose prices stop inside a hold is sold at its last close, flagged and counted; the result without such trades is shown and not judged. An event with no price on its entry day, or whose prices start after its filing day, is left out and counted by year. This holds for all three entry days.
- The same member buying the same stock again while a hold is running is one position, held until the last hold ends.
- Stock bought by using a call option is reported as a stock purchase and stays in the judged groups, because the judged path reads no free text. Such rows are counted, and each judged figure is shown again without them, not judged.
- The feed finds prices by ticker. A ticker later reused by another company could join the wrong history. This is not detectable from the feed; the 20 largest single-event returns are printed so a wrong join shows.
- In design mode every price file is cut at the last day a design event or a design random draw needs, so no held-back event is scored and no price after that day is read. That day falls in 2023, because late 2022 design holds and the shifted random draws run into it.
- Renamed companies, added 2026-11-25 18:49 UTC: the price feed keeps a renamed company's whole history under its new ticker, so a purchase filed under the old ticker finds no price (MEASURED: 162 purchase events sit under one-to-four-letter tickers with no bars, among them MMC 55 and FI 28). Leaving them out would drop companies for a reason that has nothing to do with the trade. A rename list is built from public sources before scoring, each line with the old ticker, the new one, the date and the source, and is fixed with this plan. A ticker is mapped only when it is the same company; a takeover by another company is not a rename and ends the history. Tickers with no bars that are not on the list (mostly foreign shares that do not trade on a US exchange) stay out and are counted.
- Reused tickers seen while building the rename list, added 2026-11-25 19:02 UTC, before any return: four tickers in the record point at another company's price history in the feed (BBT before the BB&T merger, CCC for Clarivate in 2020, AM before Antero Midstream's 2019 merger, HR before the 2022 Healthcare Realty merger). Each gets a dated line in the rename list: mapped to the right company where it still trades under another ticker, left out and counted where it was taken over. A buyer that took the bought company's name and ticker (JBT, WGP, AMGP, BHLB, DEAC) is treated as the same company.
- In the design run no proven list is built after the last design filing day. A shifted filing day in yardstick (c) that falls before the first price day has no price.
- Yardstick (c) on the held-back half: an event whose filing day shifted later would exit after the last day of prices is left out of that draw. Not judged.
- The freeze needs the scorer, the shared code and the rename list on the main branch exactly as run, and the held-back run refuses if any of the three has changed since the design run.
- Held-back events must have a finished hold under all three entry days at the chosen hold, so the three versions cover the same events. Filings too late for that are left out and counted.
- NANC first traded 2023-02-07. Design-half holds that run into 2023 show a few days of it. It is for scale only.
- A surname in `replay_12_plan.named_members` must match exactly one member. Where two members share one, the list gives the full name.
- The proven group may fall short of `replay_12_plan.min_events` on the held-back half. That is a fail on count, said as such.

## Two halves, one judged

- Design half: filings from `replay_12_plan.design_filed_from` to `replay_12_plan.design_filed_to`. Used once to choose one set-up out of nine (three groups, three holding times): the one whose portfolio beat SPY by the most per year. Figures are compared to six decimals; an exact tie goes to the set-up listed first (groups in the order above, shorter hold first). Choosing among nine flatters the winner, so this half is not the judge.
- Held-back half: filings from `replay_12_plan.heldback_filed_from` on, leaving out filings so late that the holding time has not finished on the last day of prices. Scored once, for the chosen set-up only. The proven-members list at the start of the held-back half is built from the design half's finished trades, as a follower would have had it.

## What would count, fixed now

On the held-back half, the chosen set-up passes when all five hold:

1. Its portfolio ends above SPY over the same days, after costs.
2. Its monthly gain less SPY's, resampled `replay_12_plan.bootstrap_draws` times in blocks of consecutive months as long as the hold, has its 5th percentile above zero.
3. Its portfolio ends above the same portfolio built from sales, yardstick (b). If the sales portfolio has no figure, this mark fails.
4. It has at least `replay_12_plan.min_events` purchase events.
5. With the entry `replay_12_plan.late_entry_trading_days` trading days later, its portfolio still ends above SPY. A result that needs the very first day is one a follower may not be able to get.

A pass means worth running on the practice desk with pretend money as a slow sleeve. It does not mean it makes money. Reported and not judged: the other eight set-ups on the design half, yardstick (c), each year apart, the by-stock portfolio, and the result with the busiest member left out.

## Named members, reported and not judged

The members in `replay_12_plan.named_members`: Nancy Pelosi and the members that trackers and the press name most (`docs/research/48_congress_trades_evidence.md`). The list was fixed before any return was worked out. For each: the number of purchase events, and what they did from the filing day against SPY at each holding time. Pelosi's household reports many purchases of call options; for this table only, a call option purchase is treated as a purchase of the stock, and the count of such rows is shown. A single member has too few events to judge, and that is said beside each row.

## How this can fool us

- 2019 to 2026 was a strong time for large technology stocks, which is what many members hold. A group can beat SPY by holding them and lose to QQQ. Both are shown.
- Stocks that vanished have no prices here. See Data.
- The proven-members group looks for skill in a small number of people from a small number of trades. Past winners in such a list are often luck.
- Filing days are taken from the first public version. A filing that reached the public site later in the day than the close would still be bought at the next open, so this does not help the test.
- Reported values are ranges, not amounts. Every event counts the same within a member, whatever its size.
- The rules may change. A ban on members trading stocks would end the data.

## Order of work

1. Collect daily prices for every ticker in the purchase and sale events, the whole span at once.
2. Code with tests on made-up data; a second model checks it; faults fixed.
3. Freeze this plan. Ledger rows pushed.
4. Design half scored once. Result and chosen set-up committed and pushed.
5. Held-back half scored once, behind a lock file as in replay 11.
