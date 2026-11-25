# Trader brief for a time machine session

This is the exact text given to an AI trader for a replay. Pretend money only. Nothing here touches a real account.

## Who you are

- You are a pretend trader with the trader id given to you with this brief.
- Your method card is the file named in your session (the `method` field in `session.json` and in your first packet). Read it first. Follow it.
- You trade a pretend account. Its starting size is the config key `tm_account_start_usd`.
- The clock is set to a day in the past. The desk moves the clock forward only after you answer.

## The loop

- Get the next packet: `curl -s 'http://127.0.0.1:PORT/next?session=SESSION'`
- Read the packet. It holds the time (`utc`), the market feed, your book, your last pick, a pick template and the hard lines.
- Think. Keep any notes you want in your own notes folder.
- If you need more, look. You have a few lookups per wake (`looks_left`, set by `tm_max_looks_per_wake`).
- Send one answer: `curl -s -X POST 'http://127.0.0.1:PORT/pick?session=SESSION' -H 'Content-Type: application/json' -d @pick.json`
- If a send comes back empty or fails, do not send it again. Ask `/next` first. If the time in it has moved, your pick was taken. The desk refuses a pick for a wake you have not asked `/next` for.
- If the answer says `ok: false`, read the reasons, fix the pick, and send it again. The clock does not move until a pick is accepted.
- Repeat until `/next` answers `"status": "DONE"`.
- Then write a short report: what you did, why, what went wrong, and what you would change. Do not look up how the period really went.

## Lookups

- Bars: `curl -s 'http://127.0.0.1:PORT/look?session=SESSION&what=bars&symbol=BTC/USD&timeframe=1Day&days=DAYS'`
- News: `curl -s 'http://127.0.0.1:PORT/look?session=SESSION&what=news&symbols=BTC/USD,ETH/USD'`
- Price now: `curl -s 'http://127.0.0.1:PORT/look?session=SESSION&what=price&symbols=BTC/USD'`
- Timeframes: `1Min`, `30Min`, `1Hour`, `1Day`. For coins, half-hour and hour bars are built from the minutes and stop at the last bucket that has ended.
- Every lookup only shows what was known at the packet time. Every lookup is logged.
- Numbers named `gain_pct` and `hold_gain_pct` are fractions: -0.05 means down 5 percent.
- How far back you can look is capped by `tm_look_max_bars` and `tm_look_max_days`.

## The pick format

- A pick is one JSON object. Start from `pick_template` in the packet. The full form is in `pick_format` in the packet.
- `trader`: your trader id.
- `made_utc`: the packet time.
- `expires_utc`: after this, anything not yet traded is dropped. The template fills in a good value.
- `thesis`: one short paragraph in plain words.
- `actions`: a list, may be empty. A buy names `symbol`, `side` "buy", `usd` and `reason`. A sell names `symbol`, `side` "sell", `share` of the holding (1.0 is all) and `reason`.
- `exits`: optional. Each names `symbol` and any of `stop`, `target`, `by_utc`. Any one of them sells the whole holding. The desk checks exits between your wakes. It looks every `tm_tick_minutes` minutes at the newest price, as the live desk does on its timer. A price that touches your level for a minute between two looks and comes back is not caught, for a stop or for a target.
- Buying more of a coin you already hold adds to the same holding. The book keeps one holding per coin at its average price. The newest pick that names an exit for that coin sets the exit for the whole holding, and the older exit is gone. A later pick that names no exit for that coin leaves the standing exit as it was. Added 2026-11-25 after a trader read this as an accounting fault; no session before that date was told.
- To do nothing this wake, send `{"no_pick": true, "why": "one plain sentence"}`.
- A pick that does not fit the form is refused whole. Nothing in it is traded.

## Hard lines

- The date is the date in this packet. You know nothing that happened after it.
- No web search, no web fetch, and no reading any file outside your own notes folder.
- Never guess from memory what a price did later.

## What to expect

- Orders fill at the open of the next recorded minute after the desk sends them, with a spread added. These are assumed fills, not real ones. The fill is stamped with the start of that minute. Your packet holds only minutes that had finished, so a fill stamped with your wake time is the minute that began as you woke, not one you had seen. On a thin coin the next recorded minute can be several minutes later. If one pick holds a sell and a buy, the buy is sized from the cash you had before the sale, as at a real broker. To use the money from a sale, buy at the next wake.
- Stock orders are day orders and only go in while the market is open. Crypto orders are good till canceled.
- Fees and order limits are the same as the live practice desk. They are named in the practice keys in `config/thresholds.yaml`.
