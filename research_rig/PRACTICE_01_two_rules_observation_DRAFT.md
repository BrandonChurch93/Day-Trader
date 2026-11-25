# Practice plan 01 (draft): two slow rules watched in the practice account

Status: DRAFT, written 2026-11-25 10:21 UTC by research. Not frozen. Nothing runs from it. It becomes a plan only when the owner has said yes to decision 5 in `docs/decisions/morning_list_2026-11-25.md`, practice keys exist (item 1 on the same page), and every line under "To settle before this is frozen" has an answer. Proposed by research. Nothing here is an owner decision.

## What this is, and what it is not

- It is a forward record. Two rules that were already run on past prices are run day by day with pretend money, and every order and fill is written down.
- It is not a test with a pass or a fail. Neither rule has a credited pass (question 18b on the morning list). Both stay labelled "not passed" while they are watched.
- It is not a step through the practice gate. `docs/playbook/00_START_HERE.md` phase 2 asks for `paper_min_trading_days` and `paper_min_closed_trades`, and for slippage and errors "within tolerance". No tolerance is defined yet (question 17), so no rule can pass that gate. Whether these days ever count toward it is the owner's to say. Question 17 proposes that days before he sets the allowed amounts do not count.
- It is not real money. `AGENTS.md` hard rule 3 keeps paper mode the default and needs the owner's written go for anything else.

## Why do it

- The held-back years are spent for both rules, so past prices cannot give a clean answer for them any more. Days that have not happened yet can.
- It shows what a real order costs against what the replays assumed, which is the measure question 17 needs.
- It exercises the plain machinery (prices in, a fixed rule, one order, a record) before anything larger is built.

What it cannot show quickly: both rules trade rarely. The stock rule is checked once a month. Weeks of watching will say more about the machinery and the fills than about either rule. Trade counts from the replays are in `research_rig/results_v2.json` and `research_rig/results_05b.json`.

## The two rules

| Name here | Rule | Defined in | Compared with |
|---|---|---|---|
| P1 on bitcoin | The trend rule P1, on BTC/USD, checked once a day | `research_rig/PREREG_01_daily_crypto_trend.md`, row P1 | Buying bitcoin on the first day and holding |
| T1 on a total market fund | The ten-month rule T1, checked at each month end | `research_rig/PREREG_05_stock_trend_free_data.md`, row T1 | Buying the fund on the first day and holding |

The rule logic already exists: P1 in `research_rig/rules.py`, and T1 inside `research_rig/run_05.py`. That second file is a test script and is not run again. The timer program would carry its own copy of that one function, checked against a small case with a known answer. No setting of either rule is changed. If either rule is changed, that is a new variant, and `AGENTS.md` hard rule 8 wants a ledger row before it runs.

## Who sends the orders

`AGENTS.md` hard rule 1 says no language model or chat automation is ever in the path that submits, sizes, cancels or retries an order. Research is a language model. So research does not send these orders, even though they are pretend.

- The orders come from a plain program on a timer. It reads prices, works out the rule, sends at most one order per rule per check, and writes a record. It has no model in it and runs with every model switched off.
- Research reads the records afterwards and reports on them. With a read-only key it may also read the practice account (positions, orders, balances). It does not place, change or cancel an order.
- The key that can send orders goes only to the timer program's own secret store. It is never entered where an agent can use it.
- Hard rule 13 holds: no agent gets a tool that can change the account's settings, cancel all orders or close all positions.

## What is written down for every check

One line per rule per check, kept as a file that is added to and never edited:

- The time of the check, and a fingerprint of the price rows the rule read.
- The rule's answer: the share of the pretend amount it wants held.
- What the account held, read from the broker at that moment (hard rule 5), and the order that follows, if any.
- For an order: when it was sent, the price the rule assumed, the price and size of each fill, and the gap between the two in basis points.
- The costs the practice account does not charge and that the record adds itself: the crypto fee on crypto fills, regulatory fees on stock sells, and dividends as cash. The list and its sources are in `docs/research/10_historical_data_and_practice.md`, "What we must add ourselves in replay and practice".
- Anything that went wrong: an order refused, a partial fill, missing or late prices, a failed lookup.

Each day one more line gives the value of each rule's pretend amount next to the value of just holding from the same first day.

## When it stops by itself

- A missing or late price: no order is sent at that check, and the record says so.
- An order whose result is not clear (a timeout or a failed lookup): that rule stops and the owner is told. It is never sent again blindly. This is hard rule 12.
- An order outside the fixed limits in the program: refused by the program, and the record says so. The limits are a list of two symbols, a largest order size, and a largest number of orders per rule per day. Their values go in `config/thresholds.yaml` as new keys when this plan is frozen, and nowhere else.

## What is known about the practice account

- Its address is `https://paper-api.alpaca.markets`, and a practice account has "a different API key from your live account" ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). STATED by Alpaca.
- A practice-only account needs an email address and no funding ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). STATED by Alpaca.
- It starts with a pretend balance that Alpaca sets by default, and the balance can only be changed by resetting the account ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). STATED by Alpaca.
- A practice-only account gets prices from one exchange only, IEX ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). STATED by Alpaca. So its stock prices can differ from the full market's.
- Practice fills are made at the best current market price, with no check of how much is on offer, and with random partial fills. What it does not simulate is listed in `docs/research/10_historical_data_and_practice.md`.
- Alpaca's page on keys describes read-only keys and keys limited to chosen parts of the account ([Alpaca credentials](https://docs.alpaca.markets/us/docs/credential-management)). STATED by Alpaca. A post on Alpaca's forum says individual accounts cannot make a read-only key ([Alpaca forum](https://forum.alpaca.markets/t/feature-request-read-only-api-keys-for-retail-accounts/19937)). STATED by a forum user. So whether the owner can make one is UNKNOWN until he looks at the key screen.
- Whether the crypto fee is charged on practice fills is UNKNOWN. Whether practice keys are refused by the live address is UNKNOWN. Whether its price history is adjusted for dividends in the way T1 needs is UNKNOWN. Each is checked once keys exist, by reading only, before this plan is frozen.

## To settle before this is frozen

Each is a choice for the owner, or a fact to check once keys exist. Research's suggestion is given where it has one.

1. Where the timer program runs. It is the first code that sends an order, even a pretend one, so the choice is the owner's. It is also a small case of decision 13 (who the Builder is and where it runs). Research's suggestion: the smallest thing that has no model in it and keeps the keys out of the repo, prompts and logs (hard rule 4).
2. Who writes the timer program. It is small, and the rule code exists. Hard rule 1 limits who may run it, not who may write it. Research can write it for review, or the Builder can.
3. Which fund stands for "a total market fund". Research's suggestion: one large, low-fee fund that holds the whole US market.
4. The pretend amount for each rule. It should be close to what would be used with real money, because what a fill costs depends on the size of the order. That real amount is `live_starting_capital_usd`, which is the owner's and has no value. Nothing here assumes one.
5. Which prices the rules read. Research's suggestion: the practice account's own prices, because those are the prices a live service would see. The record then also says how far they were from the price history the replays used.
6. The time of day of each check, and the kind of order. For bitcoin the replays used the close of each day in UTC. For the fund the replay had daily closes and no opening prices: it checked the ten-month rule at each month end and filled at the next day's close. The draft fund test fills at the next day's open (`research_rig/PREREG_06_fund_trend_paid_data_DRAFT.md`).
7. What happens on the first day. A rule that already wants to be in the market either buys at once or waits for its next change. Research's suggestion: buy at once, and say so in the record, so that the record is the rule's position from day one.
8. Whether a line goes in the trial ledger when the watching starts. Research's suggestion: yes, one line, marked as a forward record and not counted as a trial, since no new variant is tried.
9. The UNKNOWN facts about the practice account listed above, the read-only key among them.
