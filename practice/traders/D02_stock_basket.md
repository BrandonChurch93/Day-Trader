# D02 stock_basket

Status: builder settings, 2026-11-25. Untested. Market: the 38 single stocks in `tm04_plan.symbols`. It is always fully invested. Once a week it names the stocks to hold.

## What it tries to do

It holds `tm04_plan.basket_size` stocks in equal shares and each week keeps or swaps them after reading the week's prices, company filings and headlines. It answers one question: can a model choose which stocks to hold better than chance?

## Why this might work, and why it might not

- STATED by its authors: one language-model system that chose a stock basket once a month was ahead of holding over 19 months ([MarketSenseAI live validation](https://arxiv.org/html/2604.17327v1)). Our check of the paper on 2026-11-25: the figures are as quoted, but they are signals made at the time and scored on later prices before costs. No money was traded and nobody outside checked it.
- MEASURED by others and here: models that traded often from prices did not beat holding.
- UNKNOWN: whether choosing among 38 large, closely watched companies leaves anything to find. News on them is priced fast.

## What it looks at each time it wakes

- The packet: the time, the account, and for every stock on the list its price and its change over a day, a week, a month and three months.
- Filings (with their item numbers) and headlines dated since the last wake, and lookups of bars, filings and headlines within the lookup limit.
- Nothing else. No web, no memory of what happened after the packet date.

## How it decides

- Its own judgment. It names exactly `tm04_plan.basket_size` stocks.
- For every stock it adds or drops it writes one plain line of reason and marks what drove it: price, filing, headline, or more than one.
- Keeping last week's basket is a valid answer and is free.

## Fixed lines

1. Only the stocks on the list. Long only. No cash held back, no borrowing.
2. Equal shares. No stops and no targets. Nothing happens between wakes.
3. It counts the cost before it swaps: the spread assumed is `tm_stock_half_spread_bps` per side on what is traded.

## When it wakes

- The last regular trading day of each week at `tm04_plan.wake_time_ny` New York time.

## How it is judged

- Written in `timemachine/PLAN_TM04_stock_basket.md` before any session ran.
