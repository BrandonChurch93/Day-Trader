# D03 avoid_list

Status: DRAFT, builder settings, 2026-11-25. Untested, and the tool cannot run it yet (see `timemachine/PLAN_TM05_avoid_list_DRAFT.md`). Market: the 38 single stocks in `tm04_plan.symbols`. It is always fully invested. Once a week it names the stocks to leave out.

## What it tries to do

It holds every stock on the list in equal shares except up to `tm05_plan.leave_out_max` it names to leave out. Each week it keeps or changes that list after reading the week's prices, company filings and headlines. It answers one question: can a model pick the stocks to avoid better than chance?

## Why this might work, and why it might not

- UNKNOWN: whether trouble is easier to see than strength. A filing of a lawsuit or a cut forecast is plain to read; whether the price has already moved is not.
- MEASURED here, looked at after the fact and not judged: in TM04 the names the models dropped fell later about as much as random drops at the same weeks (`docs/research/36_time_machine_tm04_stock_basket.md`). That does not settle this question, since TM04 asked for winners, not for names to avoid.
- MEASURED by others and here: models that traded often from prices did not beat holding.
- Leaving out a few of 38 changes the book only a little, so any edge will be small next to the noise.

## What it looks at each time it wakes

- The packet: the time, the account, its standing leave-out list, and for every stock on the list its price and its change over a day, a week, a month and three months.
- Filings (with their item numbers) and headlines dated since the last wake, and lookups of bars, filings and headlines within the lookup limit.
- Nothing else. No web, no memory of what happened after the packet date.

## How it decides

- Its own judgment. It names from 0 to `tm05_plan.leave_out_max` stocks to leave out. Naming none means hold all 38.
- For every stock it adds to or takes off the leave-out list it writes one plain line of reason and marks what drove it: price, filing, headline, or more than one.
- Keeping last week's list is a valid answer and is free.

## Fixed lines

1. Only the stocks on the list. Long only. No cash held back, no borrowing.
2. Equal shares of the stocks held. No stops and no targets. Nothing happens between wakes; the book drifts with prices and is put back to equal shares only when the list changes.
3. It counts the cost before it changes the list: the spread assumed is `tm_stock_half_spread_bps` per side on what is traded.

## When it wakes

- The last regular trading day of each week at `tm05_plan.wake_time_ny` New York time.

## How it is judged

- To be written in `timemachine/PLAN_TM05_avoid_list_DRAFT.md`, then fixed by the lead before any session runs.
