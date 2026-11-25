# B01 crypto_swing_price_only

Status: builder settings, 2026-11-25. Untested. Market: the eight crypto pairs on the recorded tape, against USD. Holding time: hours to days. Written for the time machine while its crypto tape has prices and no news.

## What it tries to do

It lets a model trade crypto swings from prices alone, with its own judgment, inside a few fixed lines. It is the plainest question we can ask first: given the same price history a person would chart, does a model's judgment beat holding bitcoin, and beat a random trader of the same size and pace?

## Why this might work, and why it might not

- UNKNOWN: whether a model reading price bars has any edge. Public live records do not show one (`docs/research/18_ai_systems_with_live_records.md`).
- MEASURED: fixed price rules on hourly bitcoin and ether passed at no venue cost here (`docs/STATUS.md`). A model reading the same prices starts from that.
- The reason to run it anyway: it is the base case. A later trader that also reads news has to beat this one, or the news added nothing.

## What it looks at each time it wakes

- The packet: time, its cash and holdings, the feed of prices for the eight pairs.
- Lookups of daily and minute bars for any of the eight pairs, within the lookup limit.
- Nothing else. No web, no news, no memory of what happened after the packet date.

## How it decides

- Its own judgment. It writes its reasoning in the pick's thesis in plain words, and one reason per action.
- It may hold cash. Doing nothing is a valid answer.

## Fixed lines

1. Only the eight pairs on the tape: BTC/USD, ETH/USD, SOL/USD, XRP/USD, DOGE/USD, AVAX/USD, LINK/USD, LTC/USD.
2. At most three holdings at once.
3. One buy is at most 40% of the starting budget.
4. Every buy carries a stop price in the pick's exits. A target price and an exit-by time are optional.
5. Long only. No borrowing.
6. It counts the cost before it trades: the fee is `practice_crypto_fee_bps_added` per side and the spread assumed is `tm_crypto_half_spread_bps` per side. A trade that needs a move smaller than twice that to pay off is not worth making.

## When it wakes

- At the hours in `tm_crypto_wake_hours_utc`. Exits are checked by the desk between wakes.

## How it is judged

- Written in `timemachine/PLAN_TM01_crypto_price_only.md` before any session ran.
