# Pre-registration 12 (draft): buying what members of Congress buy, after the trade becomes public

Status: DRAFT written 2026-11-25 18:27 UTC by the builder, before any price was joined to any disclosed trade. It becomes final when the code has been checked by a second model and this line is changed to "frozen" with the time. Ledger rows 135 to 143 in `research_rig/TRIAL_LEDGER.md`. Pretend trades on past prices.

## The claim

The owner, 2026-11-25 (`docs/DECISIONS.md`): people say you cannot go wrong following the stock trades of members of Congress such as Nancy Pelosi. The claim tested: a small account that buys a stock on the first trading day after a member's purchase becomes public, and holds it for a fixed time, does better than holding the S&P 500 fund SPY.

## What is known before the test

- A member has up to 45 days to report a trade. MEASURED on the collected record: the middle delay between trade and filing is 28 days, one in ten is 48 days or more, and 11% are over 45. A follower can only act after the filing. So every trade here is dated by its filing, never by the day of the trade.
- MEASURED 2026-11-25 from our price feed, dividends included: the fund that copies Democratic members' disclosures with real money (NANC) made +85.3% from its first day, 2023-02-07, to 2026-11-24. SPY made +81.5% and QQQ +110.3%. The Republican fund (KRUZ, renamed GOP in March 2025) made +61.0%. A second public source gives the same three figures ([Total Real Returns](https://totalrealreturns.com/n/NANC,GOP,SPY)).
- The published studies and their sources go into the research page for this replay when the helper's reading has been checked.

## Data

- Trades: every Periodic Transaction Report of both chambers filed from `replay_12_plan.design_filed_from` on, 85,291 rows of stock and stock-option trades, each with the day of the trade and the day its first version was filed. Kept on the research machine, not in the repo. The helper that built it computed no return. A seeded sample of rows is checked against the original filings and the match rate is reported.
- One event is one member buying one stock in filings of one day, whatever the number of rows. Stock purchases only. Options are left out of the judged groups because the record does not always say what kind.
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

## Two halves, one judged

- Design half: filings from `replay_12_plan.design_filed_from` to `replay_12_plan.design_filed_to`. Used once to choose one set-up out of nine (three groups, three holding times): the one whose portfolio beat SPY by the most per year. Choosing among nine flatters the winner, so this half is not the judge.
- Held-back half: filings from `replay_12_plan.heldback_filed_from` on, leaving out filings so late that the holding time has not finished on the last day of prices. Scored once, for the chosen set-up only. The proven-members list at the start of the held-back half is built from the design half's finished trades, as a follower would have had it.

## What would count, fixed now

On the held-back half, the chosen set-up passes when all four hold:

1. Its portfolio ends above SPY over the same days, after costs.
2. Its monthly gain less SPY's, resampled by whole months `replay_12_plan.bootstrap_draws` times, has its 5th percentile above zero.
3. Its portfolio ends above the same portfolio built from sales, yardstick (b).
4. It has at least `replay_12_plan.min_events` purchase events.

A pass means worth running on the practice desk with pretend money as a slow sleeve. It does not mean it makes money. Reported and not judged: the other eight set-ups, yardstick (c), each year apart, the by-stock portfolio, and the result with the busiest member left out.

## Named members, reported and not judged

Nancy Pelosi and the members most followed in the press (the list and its sources come from the helper's reading and are fixed in this plan before it is frozen). For each: the number of purchase events, and what they did from the filing day against SPY at each holding time. Pelosi's household reports many purchases of call options; for this table only, a call option purchase is treated as a purchase of the stock, and the count of such rows is shown. A single member has too few events to judge, and that is said beside each row.

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
