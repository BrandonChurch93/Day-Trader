# B02 crypto_swing_with_news

Status: builder settings, 2026-11-25. Untested. Market: the eight crypto pairs on the recorded tape, against USD. Holding time: hours to days. The same trader as `practice/traders/B01_crypto_swing_price_only.md` with one thing added: it can read dated crypto headlines.

## What it tries to do

It lets a model trade crypto swings with its own judgment from prices and the news of the day, inside the same fixed lines as B01. It answers one question: does reading the news make the same model trade better than it does from prices alone, on the same days?

## Why this might work, and why it might not

- MEASURED: crypto prices moved a lot on regulatory headlines in a BIS study ([BIS regulatory news study](https://www.bis.org/publ/qtrpdf/r_qt1809f.htm), via `docs/research/02_crypto_trading_evidence.md`).
- UNKNOWN: whether a model that reads headlines twice a day gets anything after costs. By the time it wakes the news can be up to twelve hours old.
- A weak point of the test itself: a headline can remind a model of what it already knows about that period, if the period is before its knowledge line. That would look like skill and is not.

## What it looks at each time it wakes

- The packet: time, its cash and holdings, the feed of prices for the eight pairs, and recent dated headlines.
- Lookups of bars for any of the eight pairs, and lookups of headlines for a coin or for crypto as a whole, within the lookup limit.
- Nothing else. No web, no memory of what happened after the packet date.

## How it decides

- Its own judgment. It writes its reasoning in the pick's thesis in plain words, and one reason per action.
- When a headline is part of the reason for a buy, the reason names the headline and its time, and the pick's `sources` list holds it.
- A headline marked `edited_later` may hold facts added after its time. It is not used as the reason for a trade.
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

- Written in `timemachine/PLAN_TM02_crypto_with_news.md` before any session ran.
