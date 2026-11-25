# D01 bitcoin_dial

Status: builder settings, 2026-11-25. Untested. Market: BTC/USD only. It does not pick trades. Once a day it says how much of the account to hold in bitcoin.

## What it tries to do

It starts fully invested, like someone who just holds. Each day it reads the prices and the dated headlines and decides whether to stay in, step partly out, or come back. It answers one question: can a model's reading of the day do better than holding, by timing and not only by holding less?

## Why this might work, and why it might not

- MEASURED here on 2026-11-25: models that picked single crypto trades sat in cash at most wakes, lost less than holding in falling months and fell far behind in rising ones (`docs/research/29_time_machine_tm01_crypto_price_only.md`). Starting invested removes the second problem.
- UNKNOWN: whether a model can tell a day to step out from a day to stay. Stepping out on every scary headline misses the rebounds, and each change costs money.

## What it looks at each time it wakes

- The packet: the time, the account, bitcoin's price and its change over a day, a week, a month and three months, and the dated crypto headlines since the last wake.
- Lookups of bars and headlines within the lookup limit.
- Nothing else. No web, no memory of what happened after the packet date.

## How it decides

- Its own judgment. It answers with one number from 0 to 1.
- It writes why in one or two plain sentences and marks what drove the answer: price, news, both, or nothing new.
- A headline marked `edited_later` may hold facts added after its time. It is not used as a reason.
- Keeping yesterday's number is a valid answer and is free.

## Fixed lines

1. BTC/USD only. Long only. No borrowing: the number is never above 1.
2. No stops and no targets. Nothing happens between wakes.
3. A change smaller than `tm_weights_min_change` is not traded.
4. It counts the cost before it moves: the fee is `practice_crypto_fee_bps_added` per side and the spread assumed is `tm_crypto_half_spread_bps` per side, on the part that is traded. Stepping out and back in pays both twice.

## When it wakes

- Once a day at the hour in `tm03_plan.wake_hour_utc`.

## How it is judged

- Written in `timemachine/PLAN_TM03_bitcoin_dial.md` before any session ran.
