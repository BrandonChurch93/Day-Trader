# Time machine

Pretend money only. Nothing here touches a real account.

## What it is

- The time machine replays a past window on the practice desk. The clock is set to a day in the past and moves forward in steps.
- An AI trader sees only what was known at the packet time. It picks, the desk trades, the clock moves on.
- The desk is the same code as the live practice desk. `practice/trader.py` Run, `practice/books.py` and `practice/picks.py` are used unchanged.
- Only two things are swapped. The broker is `simbroker.py`, which fills orders from recorded minute bars. The data address is `simdata.py`, which reads the recorded tape and never returns a row after the clock.
- The recorded tape is `$TM_STORE/tape.sqlite`. It is made by `record.py` (see Part A in the build spec).
- Every session that is started is counted, one line each, in `timemachine/SESSIONS.jsonl`. Do not delete lines.

## Files

- `simbroker.py`: the pretend broker. Fills, refusals, and an account file saved after every change.
- `session.py`: makes a session, runs the desk tick by tick, builds packets, takes picks, writes the result.
- `server.py`: a small local web server. A trader agent only needs curl.
- `new_session.py`: makes a new session and prints the curl lines.
- `run_code_trader.py`: runs a plain code trader (hold, random twin) with no server.
- `code_traders.py`: the hold trader and the random twin.
- `TRADER_BRIEF.md`: the exact text given to an AI trader.
- `test_sim.py`: the tests, on a made-up tape.

## How to run a session end to end

Run these from the repo root.

- Make the session: `python3 timemachine/new_session.py --trader T01 --model MODEL --method PATH/TO/METHOD_CARD.md --market crypto --from 2026-10-01 --to 2026-10-31` (add `--news` for a trader that reads headlines)
- It prints the session id and the curl lines.
- Start the server in its own terminal: `python3 timemachine/server.py`
- The port is `TM_PORT` if set, otherwise the default in `server.py`.
- Give the trader agent `TRADER_BRIEF.md`, its trader id, the session id and the port. It loops on `/next` and `/pick` until DONE.
- Check progress any time: `curl -s 'http://127.0.0.1:PORT/status?session=SESSION'`
- When DONE, the result is `$TM_RUNS/SESSION/result.json`.
- Run the hold baseline for the same window: `python3 timemachine/run_code_trader.py hold --symbol BTC/USD --market crypto --from 2026-10-01 --to 2026-10-31` (add `--news` for a trader that reads headlines)
- Run a random twin of the AI session: `python3 timemachine/run_code_trader.py twin --result $TM_RUNS/SESSION/result.json --seed SEED`
- For stocks, use `--market stocks`. The benchmark defaults to SPY.

Folders.

- `TM_STORE` holds the tape. Default `/home/user/workspace/rig/tm_store`.
- `TM_RUNS` holds one folder per session. Default `/home/user/workspace/rig/tm_runs`.
- A session folder holds `session.json`, `progress.json`, `account.json`, `packets/`, `picks/`, the desk records, `looks.jsonl` and at the end `result.json`.

## How the clock moves

- The desk runs every `tm_tick_minutes`, the same as the live timer.
- The trader wakes at `tm_crypto_wake_hours_utc` for crypto and at `tm_stock_wake_times_ny` for stocks.
- Stock ticks only happen while the market is open, plus one at the close.
- Between wakes the desk keeps running, so stops, targets and time exits fire at the right tick.
- When `tm_skip_idle_ticks` is on, a tick with nothing to do is skipped. The first tick of each hour and the last tick always run. A test proves the result is the same with and without skipping.
- A packet is saved the first time it is built. Asking again gives the same packet.

## Fill model

- An order sent at a tick fills at the open of the first recorded minute after it was sent. These are assumed fills, not real ones.
- A buy pays the open plus a half spread. A sell gets the open less a half spread. The half spread is `tm_stock_half_spread_bps` or `tm_crypto_half_spread_bps`.
- For stocks, one minute can fill at most `tm_max_share_of_minute_volume` of that minute's volume. The rest is canceled in that same minute. The order then shows as canceled with a part filled, which is how Alpaca shows a part fill.
- For crypto the cap is `tm_crypto_max_share_of_minute_volume`. Zero means no cap, which is the default. Reason, MEASURED on the October 2026 tape: most recorded crypto minutes show zero or tiny volume, so a cap would leave almost every order unfilled.
- Crypto fees follow `practice_crypto_fee_bps_added` and `practice_crypto_fee_in_coin`, the same keys as the live desk.
- Stock orders are day orders. They expire at the close.
- Gaps in the minute bars are fine. The fill waits for the next recorded minute.
- The account starts with `tm_account_start_usd`. The whole account is the trader's budget.

## What the tests prove

- `python3 timemachine/test_sim.py` runs on a made-up tape. MEASURED: all checks pass. It covers the fill price and time, gaps, the volume cap, refusals, stop and target exits at the right tick, books agreeing with the broker to the cent, no look-ahead (a packet never changes when later tape rows are edited), skip and no-skip giving the same result, a crash and restart giving the same result, a restarted server giving the same result, the lookup limit, the hold trader, the random twin, a stock session, and the session count.
- `python3 practice/test_trader.py` still passes with no change to `practice/`. MEASURED.
- A full real month (hold, BTC/USD, October 2026) ran end to end on the recorded tape. MEASURED: the books from `practice/books.py` matched the broker's cash and holding to the cent. The wall time and tick counts are in `run_facts` in that session's `result.json`.

## Honest limits

- Fills are assumed from recorded minute bars. They are not real fills. Real spreads and queue position are UNKNOWN.
- A model may still know this period if it falls before the model's knowledge line. UNKNOWN how much that helps it.
- The no-search and no-file rule is given by instruction. It is not enforced by this program.
- News headlines and summaries are as first recorded. A story edited later is marked `edited_later`, and its text may hold the later edit.
- The stock list is today's list. Stocks delisted during the window are missing.
- Prices are raw, not adjusted for splits or dividends. A split inside a held position is not handled. Dividends are not paid.
- The screener (movers, most active) is rebuilt from bars. It is not Alpaca's own.
- Tradable and fractionable are assumed true for any symbol the tape has bars for on that date.
- A stock order while the market is closed is refused. The real Alpaca would queue it for the open.
- A stock order is refused if the tape has no minute bars for it that day.
- Sell orders by dollar amount are refused. Buying power is cash less open buys.
- News is off unless a session is made with `--news`. A session made without it shows no headlines in its packets and refuses news lookups, whatever the tape holds. That is how a prices-only trader and a news-reading trader can be run on the same days and compared.
- The crypto tape holds dated headlines from three public news sites from 2026-06-01 (`python3 timemachine/record.py crypto-news`). The time on a headline is the site's own publish time. About one in eight was edited after it was published, and the text kept is the edited one; those are marked `edited_later`. A trader could learn a little from an edit that it should not know yet.
- Real AI sessions have not been run yet. How long one takes is UNKNOWN.
