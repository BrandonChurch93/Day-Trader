# Practice plan 01: two slow rules watched in the practice account

Status: IN FORCE since 2026-11-25 14:30 UTC. It was a draft from 2026-11-25 10:21 UTC. The owner said yes to building the practice trader on 2026-11-25 (`archive/decisions/0007-owner-goal-and-practice-trader-2026-11-25.md`). The points the draft left open were settled by research so the build could go on, and each is listed under "What was settled, and where to change it". The owner can change any of them. The program is `practice/trader.py`. How to run and read it is in `practice/README.md`.

The trader sends no order until the owner has put the practice key in the repo's secrets. He is told that adding the key starts the pretend trading.

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

The rule logic already exists: P1 in `research_rig/rules.py`, and T1 inside `research_rig/run_05.py`. That second file is a test script and is not run again. The timer program carries its own copy of both rules in `practice/rules.py`, checked against small cases worked by hand in `practice/test_trader.py`. No setting of either rule is changed. If either rule is changed, that is a new variant, and `AGENTS.md` hard rule 8 wants a ledger row before it runs.

## Who sends the orders

`AGENTS.md` hard rule 1 says no language model or chat automation is ever in the path that submits, sizes, cancels or retries an order. So research, which is a model, does not send these orders.

- The orders come from `practice/trader.py`, run once an hour by GitHub's timer (`.github/workflows/practice-trader.yml`). It has no model in it and runs with every model switched off.
- The key that can send orders is a secret in the repo's settings, entered by the owner. Research never sees it. It is not in the repo, a prompt, a log or agent memory (hard rule 4).
- Research wrote the program and can change it by pushing code. Every change is in the git history. That is the one way research can affect an order, and the owner should know it.
- The program can read the account, read prices and send one order. It has no code to cancel an order, close a position or change the account (hard rule 13), and it refuses any address but the practice one. `practice/test_trader.py` checks this before every run.
- Research reads the records afterwards and reports on them.

## What is written down

All of it goes to the `practice-records` branch, in `records/`. Lines are added and never edited.

- `checks.jsonl`: one line each time a rule looks at a new price day: the time, a fingerprint of the prices it read, the share of its money the rule wants in the market, what the account held as read from the broker (hard rule 5), and whether an order follows.
- `orders.jsonl`: one line when an order is about to be sent, one when the broker answers, one when it fills: size, the newest price the program had read when it sent the order, the fill price, and the gap between the two in basis points.
- `closed.jsonl`: one line each time a rule goes back to holding nothing, with the gain or loss since it last held nothing. This is what the screen counts as a win or a loss.
- `daily.jsonl`: once a day, the value of each rule's pretend money next to the value of just holding from the same first price.
- `problems.jsonl`: anything that went wrong, in plain words.
- The crypto fee is added by the program on every crypto fill (`practice_crypto_fee_bps_added`). Not added yet: regulatory fees on stock sells, and dividends. Just holding is shown without dividends too, so the two are compared like for like. Both are open items.

## When it stops by itself

- Prices missing, out of order or too old (`practice_max_price_age_hours_crypto`, `practice_max_price_age_days_stock`): no order is sent, and the record says so.
- An order whose result is not clear, and which the broker does not know by its fixed name: that rule stops and the run ends with an error, so GitHub tells the owner. It is never sent again blindly (hard rule 12). The rule starts again only when the owner says so.
- The account holds something the records do not explain: that rule stops the same way.
- An order outside the program's own limits (`practice_max_order_usd`, `practice_max_orders_per_rule_per_day`): refused by the program, and the record says so.
- The stock market is closed: the fund rule waits and looks again on the next run.
- Any check in `practice/test_trader.py` fails: the timer does not run the trader at all.

## What is known about the practice account

- Its address is `https://paper-api.alpaca.markets`, and a practice account has "a different API key from your live account" ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). STATED by Alpaca.
- A practice-only account needs an email address and no funding ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). STATED by Alpaca.
- It starts with a pretend balance that Alpaca sets by default, and the balance can only be changed by resetting the account ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). STATED by Alpaca.
- A practice-only account gets prices from one exchange only, IEX ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). STATED by Alpaca. So its stock prices can differ from the full market's.
- Practice fills are made at the best current market price, with no check of how much is on offer, and with random partial fills. What it does not simulate is listed in `docs/research/10_historical_data_and_practice.md`.
- Alpaca's page on keys describes read-only keys and keys limited to chosen parts of the account ([Alpaca credentials](https://docs.alpaca.markets/us/docs/credential-management)). STATED by Alpaca. A post on Alpaca's forum says individual accounts cannot make a read-only key ([Alpaca forum](https://forum.alpaca.markets/t/feature-request-read-only-api-keys-for-retail-accounts/19937)). STATED by a forum user. So whether the owner can make one is UNKNOWN until he looks at the key screen.
- Whether the crypto fee is charged on practice fills is UNKNOWN. Whether practice keys are refused by the live address is UNKNOWN. Whether its price history is adjusted for dividends in the way T1 needs is UNKNOWN. Each is checked once keys exist, by reading only, before this plan is frozen.

## What was settled, and where to change it

Research decided each of these on 2026-11-25 so the build could go on. None is an owner decision. To change one, change the place named.

| # | Open point in the draft | What research chose | Why | Where to change it |
|---|---|---|---|---|
| 1 | Where the timer program runs | GitHub's timer, in this repo, once an hour | Nothing new to set up or pay for, no model in it, and the key sits in GitHub's own secret store | `.github/workflows/practice-trader.yml` |
| 2 | Who writes it | Research wrote it. Another model checked it | The owner said yes to this on 2026-11-25 | `practice/` |
| 3 | Which fund | VTI | A large, low-fee fund that holds the whole US stock market | `SPECS` in `practice/trader.py` |
| 4 | The pretend amount per rule | `practice_amount_per_rule_usd` | Close to research's suggestion for a first real amount, so orders are a realistic size. It is pretend money and sets no real-money number | `config/thresholds.yaml` |
| 5 | Which prices the rules read | The practice account's own price service | Those are the prices a live service would see | `practice/broker.py` |
| 6 | When each rule is checked, and the kind of order | Bitcoin: on the first hourly run after a day's prices are finished. Fund: on the first hourly run in a new month while the stock market is open. Both send one market order | Close to the replays, which decided on a finished day and traded at the next open | `practice/trader.py` |
| 7 | The first day | A rule that wants to be in the market buys at once | So the record is the rule's position from day one | `practice/trader.py` |
| 8 | A line in the trial ledger | One line, marked as a forward record and not counted as a trial | No new variant is tried | `research_rig/TRIAL_LEDGER.md` |
| 9 | Facts not known about the practice account | Read from the first runs' records and written here when known | They cannot be checked without the key | This file |

Still UNKNOWN until the first runs with a key: whether the practice account charges the crypto fee itself (if it does, the program's added fee counts it twice and the key `practice_crypto_fee_bps_added` goes to zero), which stock price feed the account allows, the time of day its daily bitcoin prices end, and whether VTI can be bought in parts of a share there.
