# Plan 02: the practice desk with AI traders

Written 2026-11-25 by the builder. It replaces plan 01 (`archive/practice_PLAN_01_two_rules_observation.md`), which had two fixed rules and no AI traders. The owner's words behind it are in `docs/DECISIONS.md`, 2026-11-25: AI traders make the trade decisions, with pretend money.

## What the desk is for

To find out, with live prices and no hindsight, which traders make pretend money and which do not. Each trader starts with the same pretend budget (`practice_amount_per_trader_usd`) and is compared with simply holding its benchmark from its first day, and with the other traders.

## How a decision becomes an order

1. An AI trader reads what its method card says to read, and writes a pick: a small file with its reason, its sources, what to buy or sell, and optional exits (a stop price, a target price, a time). The form is in `practice/picks.py`. A fixed rule has no pick: the program works its decision out from prices.
2. The pick is pushed to the `practice-picks` branch. The trader has no broker key and cannot place an order.
3. The timer runs `practice/trader.py` about every thirty minutes (`practice_timer_minutes`). It reads cash, holdings and every order from the broker and rebuilds each trader's books from the broker's order list.
4. The first time the program sees a pick it freezes a copy in the records. A later edit or removal of the file changes nothing. A pick that arrives after its own expiry is marked late and never traded.
5. For each action the program checks: the pick fits the form, the trader has the pretend cash or the holding, the order is inside the size limits, the trader is inside its daily order count, the price is fresh, the market for that symbol is open, and nobody else on the desk has an open order in that symbol.
6. It writes the intent down and saves it to the `practice-records` branch. If that save fails, the order is not sent.
7. It sends one order with a fixed name that says which trader and which pick it belongs to, waits for the fill, and writes down the result.
8. On every later run it checks the pick's exits against live prices and sells when one is hit.

## What the limits are

All in `config/thresholds.yaml`, keys starting `practice_`. The builder sets them and changes them when the evidence says so. They are sized so that one trader's mistake cannot spend another trader's pretend money, not to hold a trader back.

## What is written down

On the `practice-records` branch, under `records/`:

| File | One line for |
|---|---|
| `picks.jsonl` | Each pick when first seen (frozen copy and fingerprint), and what happened to each of its actions |
| `orders.jsonl` | Each order: the intent before it is sent, then sent, filled, refused, not sent, or unclear |
| `checks.jsonl` | Each time a fixed rule looked at a new price day and what it wanted |
| `starts.jsonl` | Each trader's first day and its benchmark's price then |
| `points.jsonl` | The desk's value and the value of holding, at each run |
| `problems.jsonl` | Anything that went wrong, in plain words |
| the summary file | Everything the owner's screen shows: each trader's value, gain, wins, losses, open holdings, last pick, and the list of trades |

## When a trader stops

- An order was sent and the answer never came back clearly. It is never sent again. The trader stops until a person clears it by naming that order when starting the workflow by hand.
- Its books do not add up against the account. That symbol is not traded until they do.
- Three exits in a row for the same holding failed.

A stopped trader shows on the owner's screen with the reason.

## The two fixed rules on the desk

| Trader | Rule | Defined in | Compared with |
|---|---|---|---|
| P1-BTC | The trend rule P1 on BTC/USD, checked once a day | `research_rig/PREREG_01_daily_crypto_trend.md`, row P1 | Holding bitcoin from the first day |
| T1-VTI | The ten-month rule T1 on a total market fund, checked at each month end | `research_rig/PREREG_05_stock_trend_free_data.md`, row T1 | Holding the fund from the first day |

Neither has a counted pass (`docs/STATUS.md`). They are on the desk as a known slow yardstick for the AI traders and to exercise the machinery. Both trade rarely.

## The AI traders

The roster and the method cards are in `practice/traders/`. A trader joins the desk when it has a ledger row, a frozen card and model, and a line in `practice/traders.json`. Where the time machine has data for its market, it runs there first (`docs/QUEUE.md`).

Every AI trader gets two twins that cost almost nothing to run: one that holds its benchmark, and one that makes random picks of the same size and frequency. A trader that cannot beat its random twin has shown nothing.

## What the desk cannot do yet

- Long only. No short sales, margin, options or futures.
- Stocks trade only in regular hours, with market orders in dollar amounts.
- Exits are checked about every thirty minutes (every ten until 2026-11-25 16:34 UTC), and GitHub's timer can run late. A stop can be filled well past its price.
- One practice account is shared by every trader, so two traders cannot have open orders in the same symbol at the same moment.
- Crypto fees: the program adds `practice_crypto_fee_bps_added` to each crypto trade in the books until the first real fill shows how the practice account charges them.
- The desk does not run the AI traders. Each one runs as an agent on a schedule and pushes picks. That scheduling is set up when the first AI trader joins.

## What would count

Decided before any AI trader starts, so it cannot drift after results come in. A trader is worth a larger test when, over at least `paper_min_trading_days` trading days and `paper_min_closed_trades` closed trades, it beats both holding its benchmark and its random twin after fees. Worth a larger test means more pretend money, more time and varied copies. It does not mean real money. That is the owner's call.
