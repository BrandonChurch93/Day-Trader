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

## What the tape holds

The live research tape (`$TM_STORE/tape.sqlite`) holds both crypto and US stock/ETF history (all counts MEASURED):

- Crypto bars (8 pairs: `BTC/USD, ETH/USD, SOL/USD, XRP/USD, DOGE/USD, AVAX/USD, LINK/USD, LTC/USD`): `1Day` from `2024-01-01..2026-11-24` (`SOL/USD` from `2024-08-26`, 8,234 bars) and `1Min` from `2026-01-01..2026-11-24` (2,835,321 bars), recorded keyless from Alpaca crypto endpoints (`record.py crypto`).
- Crypto news (`2026-04-01..2026-11-24`, 8,395 dated headlines): public WordPress REST endpoints of `cryptopotato` (3,283), `cryptoslate` (2,435), and `newsbtc` (2,677) via `record.py crypto-news`.
- Stock and ETF bars (the stock list was chosen on 2026-11-25 — today's Dow 30 plus 8 names picked today: `AMD, AVGO, COIN, META, MSTR, NFLX, PLTR, TSLA` — so it leans toward companies that did well; plus 18 funds `SPY, QQQ, IWM, DIA, VTI, TLT, GLD` and 11 sector ETFs, plus 5 extra on-disk daily ETFs `BIL, DBC, EFA, IEF, VNQ`):
  - `1Day` (`2024-01-02..2026-11-24`): 61 symbols, 728/728 trading days each (44,408 bars, 0 gaps).
  - `1Min` (`2026-04-01..2026-11-24`, plus `SPY` and `QQQ` from `2026-01-02`): 56 symbols, 3,649,989 bars total — April–May 2026 pulled from Alpaca SIP (`894,554 / 895,440` regular-hours minutes = 99.9011% complete across 41 sessions), June–November 2026 from built-in history (`2,787,415` bars including `SPY`/`QQQ` Jan–May; 99.9888% complete across 124 sessions; full June–Nov report in `rig/stock_coverage_report.md`).
- Stock session calendar (`sessions`): 226 NYSE sessions (`2026-01-02..2026-11-24`), including 165 sessions in `2026-04-01..2026-11-24`, derived from `SPY` `1Min` bars via `record.py sessions-from-tape`. Daily liquid `universe` covers 61 stock/ETF symbols per session across `2026-04-01..2026-11-24`.
- Stock news (`2026-04-01..2026-11-24`, 12,958 dated items): `alpaca` (`2026-04-29..2026-11-24`, 11,726 items, 0.0% edited after publish), `sec_edgar` (`2026-04-01..2026-11-24`, 506 filings — 386 Form 8-K, 5 Form 8-K/A with item numbers in the headline, 105 Form 10-Q, 1 Form 10-Q/A, 8 Form 10-K, 1 Form 10-K/A with filing index links and no body text — stamped to the second with UTC `acceptanceDateTime`, 0.0% edited), and `finbold` (`2026-04-01..2026-11-24`, 726 dated stock headlines; 6.6% edited >1h after publish; Finbold headlines are tagged only by name matching).

## Attention counts

`timemachine/attention.py` reads `attention.sqlite` in the tape folder. Call `get_attention(coin, as_of_utc, lookback_days)` with a simulated UTC time. It returns counts only for completed periods and only once their recorded availability time has passed. No row means unknown, not zero.

The default serves original and assumed-lag observations. An assumed lag is an estimate, not proof of the historical value. Use `min_vintage="original"` for verified archive snapshots only. Capture-only data is off by default. The store and the source checks stay off repo.

## TM07 desk, draft

- Read `PLAN_TM07_desk_DRAFT.md` and `TRADER_BRIEF_DESK.md`. The branch does not launch a desk, call a model, change the ledger or change the tape. Run `python3 -B -m unittest timemachine.test_tm07` for synthetic checks only.
- Only a separate replay instance sets `TM07_RUNS_DIR` and uses `server.serve_desk`. The legacy listener does not serve desk routes. The desk listener checks a signed worker-isolation probe record before opening. Put each `TM07-*` arm under that isolated off-repo directory. Create frozen inputs with `desk.prepare_week` and `desk.create_desk` after approval. Pass the operator-sealed registration; the listener only serves that registration. No role token, seal key or tape record belongs in git or a shared handoff file.
- Start with the designated neutral scout stream. Both scout roles get the same raw packet. The operator calls `export_scout(approval_key)` after its last wake, then copies that exact sealed export to B and C. A takes the raw packet without the export. Use `desk.issue_role_tokens` to make independent tokens per role and arm. The local token registry refuses reuse.
- Send `Authorization: Bearer TOKEN`. Read `GET /desk/next?session=ID` or `/desk/status`. POST to `/desk/notes`, `/desk/pick`, `/desk/look` or `/desk/usage` as the role allows. Send the current `wake_key` in each POST. A pick only acknowledges; later evidence belongs to the next packet. The legacy addresses do not serve TM07.
- The runner still needs separate worker sandboxes and a provider wrapper that reports real usage before the wake advances. `score_tm07.score_week` checks the journal, then seals registered results. `score_tm07.paired` accepts only registered results for judgment. The operator must produce the sealed screen gate before any extension arm is created. The TM06 archive remains descriptive.

## Weights sessions

A second kind of session. The trader does not pick trades. At each wake it says what share of the book to hold in each allowed symbol. The rest is cash. Long only.

- Code: `weights.py` (the session, the book, the packet), `score_weights.py` (the scorer and the twins), `TRADER_BRIEF_WEIGHTS.md` (the exact text given to the trader).
- The same server serves both kinds. It opens a weights session when `session.json` has kind `weights`. Pick sessions are unchanged.
- Make a crypto session that starts fully in bitcoin: `python3 timemachine/weights.py new --trader T01 --model MODEL --method practice/traders/D01_bitcoin_dial.md --market crypto --symbols BTC/USD --from 2026-04-01 --to 2026-04-30 --open '{"BTC/USD": 1}' --wakes '[{"every": "day", "utc_hours": [0]}]'` (one wake a day at 00:00 UTC, as plan TM03)
- Make a stock session, weekly, starting in cash, with a basket of 8 and news: `python3 timemachine/weights.py new --trader T02 --model MODEL --method practice/traders/D02_stock_basket.md --market stocks --symbols NVDA,JPM,... --from 2026-06-05 --to 2026-11-20 --wakes weekly --basket-size 8 --news`
- `--wakes` takes `pick-hours` (the hours of pick sessions), `weekly`, or a JSON list of wake rules. `daily` is refused because it was easy to read as one wake a day when for crypto it meant two. A crypto session must say which.
- Other options: `--open cash` (the default), `--benchmark SYMBOL` (default BTC/USD for crypto, SPY for stocks), `--session ID`, `--note TEXT`.
- Start the server: `TM_PORT=PORT python3 timemachine/server.py`. The trader calls `/next`, `/look`, `/pick` and `/status` with `?session=ID`, as the brief says.
- Score it: `python3 timemachine/score_weights.py ID` (add `--json` for the full output).

Wakes.

- `pick-hours`, crypto: at the hours in `tm_crypto_wake_hours_utc`.
- `pick-hours`, stocks: at the times in `tm_stock_wake_times_ny` on session days.
- One wake a day: `[{"every": "day", "utc_hours": [H]}]`.
- Weekly: `tm_weights_weekly_weekday` at `tm_weights_weekly_time_ny` New York time. If that day is not a session day, the last session day before it in that week is used.
- The rules are stored in `session.json` as a list, so a session can have its own.
- A session may span many months. The wake list is made once, when the session is made.

Fill model.

- The book moves to the target at the open of the first recorded minute after the wake. For stocks closed at the wake, at the next regular open. Fills stop at the next wake.
- Weights are shares of the book valued at those opens. Only the difference is traded. Sells go first. Buys are scaled down if cash is short.
- Costs: `tm_crypto_half_spread_bps` plus `practice_crypto_fee_bps_added` for crypto, `tm_stock_half_spread_bps` for stocks.
- A change smaller than `tm_weights_min_change` is skipped. A move to zero is always made.
- No answer, `no_change`, or the same weights as last time trade nothing. Drift is not rebalanced.
- A move with no recorded minute before the next wake is not filled. It is tried again at the next wake.
- An opening book (`--open`) is bought at the first minute of the first wake, with costs.

Records, in the same run folder layout.

- `progress.json` holds the book and every step: the weights asked for, the weights held after fills, the book value, the trades, the skips, the why, and the driver and reasons if given.
- `picks/<TRADER>/<wake>.json` keeps each answer as sent. `packets/<n>.json` keeps each packet. `records/wakes.jsonl` and `account.json` are rewritten after each step.
- `result.json` is written at the end. One line goes in `SESSIONS.jsonl` with kind `weights`.

Twins, in `score_weights.py`. All run through the same book function, without the server, `tm_weights_twin_draws` draws each.

- `shuffle`: the model's target at every wake, in a random order across the same wakes.
- `shuffle_decisions`: only the model's new targets, in a random order across the wakes where it set them.
- `shuffle_runs`: the model's runs (wakes in a row with one target, the first starting at the opening wake) in a random order, each keeping its length. Same targets for the same number of wakes, different timing. A model with one run gets "no timing to judge" and no percentile. When the number of distinct orders is under the draw count, it is printed.
- `random_basket` (stocks): the same number of names at random, swapping as many names each wake as the model did.
- `hold_<benchmark>` and `hold_equal_weight`: fixed weights from the first wake.
- The model's percentile is the share of draws strictly below it. A tie counts against the model.
- Draws are seeded from `tm_weights_twin_seed` and the session id.
- Sum one model's sessions: `python3 timemachine/score_weights.py --sum ID1 ID2 ...`. It adds the model's gains, adds each twin set's gains draw by draw (draw i of each session), and gives the percentile of the summed model gain.
- The scorer reads the tape again, checks it gives the prices the session recorded, and checks the replay of the model's answers gives the recorded final value to the cent. It stops if not.

Plan TM03 results.

- `python3 timemachine/score_tm03.py` scores every finished session TM03-D01-<MODEL>-<YYYY-MM> under `$TM_RUNS` with the weights scorer and writes `timemachine/results_tm03.json` and `docs/research/34_time_machine_tm03_bitcoin_dial.md`. `--check` exits 1 if those files are stale.
- The months and method counts come from `tm03_plan`, the pass percentile from `tm_weights_pass_percentile`. The judged set is `shuffle_runs`. It reads the session folders and changes nothing in them.

MEASURED, scripted answers, temp folders.

- A crypto session from 2026-04-01 to 2026-11-23 with 8 coins has 474 wakes. The answer loop took about 17 seconds. Scoring with 1,000 draws took 18 to 28 seconds.
- A server smoke test on a spare port, crypto for 5 days and stocks for a month, ran all calls in about 1 second. Scoring each took under half a second.

Limits of weights sessions.

- The book is marked at the last price with no cost to sell. Largest drop is measured at the wakes and the end only.
- There is no volume cap on fills.
- The `shuffle` twin moves at more wakes than a model that rarely changes, so it pays more costs. That makes the model look better against it. `shuffle_decisions` keeps the number of moves the same. Its costs are printed next to each set.

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
