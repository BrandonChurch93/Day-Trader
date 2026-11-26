# E09: Forward log of rule 70-102, the coin that fell more than twice as far as bitcoin

Status: written 2026-11-26 at the lead's request, queue row 114, with the lead's update after plan 71 and [doc 153](../../docs/research/153_overextension_lead_outside_evidence.md). Pretend money only: no AI, no account, no login, no broker, no orders, no real money. A fixed rule, not an AI trader, and not in `practice/traders.json`.

## What this is, and what it is not

STATED. Rule 70-102 was the one finalist of the plan 70 search on 2020 to 2023 hourly bars ([plan 70](../../research_rig/PREREG_70_coin_sweep.md), ledger 218 in [the trial ledger](../../research_rig/TRIAL_LEDGER.md)). It was NOT carried to the vault. At half its search mean it passed every vault mark in 20.67% of draws, under the 33% line fixed before any bar was read. The vault (2024-01-01 to 2026-10-31) stays sealed. So this card follows a shown lead, not a pass. Nothing on this card says the rule makes money.

STATED. Plan 71 (ledger 219) found two more finalists of the same family, 71-013 and 71-035. Neither was carried (20.75% and 18.11%, both under 33%). In the same search, buying one hour later was below zero in 6 of 8 rules, so the gain sits in the first hour after the signal. Doc 153 lists ways the hourly open print can fool a backtest, such as the print being a sell at the bid in a falling hour, or a print no order could reach.

So the forward log measures reachability directly. It records the real best bid and ask at the moment each wake fires and at 1, 5 and 15 minutes after, and the judged line trades at those quotes, not at the open print.

## The rules, as plans 70 and 71 froze them

The logger does not restate the arithmetic. It calls `score_signal` and `order_times` from [sweep_70.py](../../research_rig/sweep_70.py) on a six-hour tape built at each wake. Plan 71 prices its no-delay, one-coin rules through that same code ([sweep_71.py](../../research_rig/sweep_71.py), `ticket_legs`).

- Judged: 70-102, row `70-102` of [GRID_70.json](../../research_rig/GRID_70.json). At each hourly open, for each coin, take the log of the close of the last fully closed hourly bar less the log of the close two hours before that. If bitcoin fell by 0.015 or more in those log terms, and another coin fell strictly more than twice as much, buy the coin with the largest excess drop (its fall less twice bitcoin's). Ties go to the coin first in alphabetical order. Sell two hours later.
- Shown only: 71-013, row `71-013` of [GRID_71.json](../../research_rig/GRID_71.json). The same, but over bitcoin's last closed hour alone, with a two-hour hold.
- Shown only: 71-035, row `71-035` of GRID_71.json. The same as 71-013, with a one-hour hold.

For each rule:

- A coin with any bar of its look-back missing cannot signal.
- No stop and no target.
- One position at a time. A trade may exit at the same wake where the next one enters.
- Skip any trade whose entry, hold or exit hour starts in the Friday 17:00 to 18:00 New York maintenance hour. No trade may exit after the last wake.
- Each rule keeps its own position, so the three can hold different coins at once. The shown rules never change what the judged rule does.

## Coins and prices

MEASURED on 2026-11-26 from the public Coinbase Exchange product list (`https://api.exchange.coinbase.com/products`): all 20 plan 70 coins have an online USD spot pair. None is left out. The coins are AAVE, ADA, AVAX, BCH, BNB, BTC, DOGE, DOT, ETH, HBAR, LINK, LTC, NEAR, PEPE, SHIB, SOL, SUI, XLM, XRP and ZEC.

The logger reads these public pages only, with no key:

- Hourly candles for every coin: `https://api.exchange.coinbase.com/products/{COIN}-USD/candles`, granularity 3600. They give the signal, and the open prints for one shown line.
- The best spot bid and ask: `https://api.exchange.coinbase.com/products/{COIN}-USD/book?level=1`.
- The best bid and ask of the matching US perpetual-style contract: `https://api.coinbase.com/api/v3/brokerage/market/product_book`. MEASURED on 2026-11-26: the [public futures catalog](https://api.coinbase.com/api/v3/brokerage/market/products?product_type=FUTURE&limit=250) lists a `-20DEC30-CDE` contract for all 20 coins, and the public book answered without a login (doc 153 section c used the same page). The codes are pinned in the logger from the [doc 120](../../docs/research/120_round_31_cfm_futures_cost_rescreen.md) table. If that page refuses or shows no two-sided book, the quote is written as UNKNOWN. The logger never logs in and never goes around a block.

Rate: at most 2.5 requests a second. About 20 candle requests at each wake where a rule is free to trade. On a signal or an exit, four quote rounds, with two requests for each quoted coin. The logger backs off on 429 and stops on 401, 403 or 451.

## Quotes and clocks

- Each hourly open is a wake. A wake is recorded from 10 seconds to 15 minutes after the open. Only bars that opened before the wake feed the signal.
- At every wake with a signal or an exit, the logger records the best spot bid and ask and the best futures bid and ask. It records them for the traded coin and for bitcoin, once as the wake fires and again 1, 5 and 15 minutes after that first quote. Each quote carries the number of seconds after the hour when it was taken.
- A wake whose first quote for the coin is more than 120 seconds after the hour is void for the judged line, at entry or at exit. The trade still keeps its slot and still shows on the shown lines.
- A missed wake is void. It is written to the log as void the next time the logger runs and is never back-filled. A wake whose candle fetch is refused is void too. A trade whose exit wake is void is unresolved: it is counted and shown, it keeps its slot blocked, and no other coin is put in its place.
- A later quote that was not taken (the process stopped) is missing, never filled in later. Only the shown lines that need it lose that trade.
- The private log is append-only and hash-chained at `/home/user/workspace/rig/data/forward_e09/log.jsonl` (folder 0700, file 0600). It holds the candles used, every quote and the trade rows, so it never goes in Git.
- The repo gets this card, the logger and a counts-only file, `practice/forward/E09_log.json`, written by `publish`.

## Freeze and running

- Frozen by the commit that adds this card and `practice/forward_e09.py`. It runs from its own detached worktree at that commit.
- `start` writes the private header once. The header holds the SHA-256 of this card, the logger, `research_rig/sweep_70.py`, `research_rig/coverage_70.py`, `research_rig/GRID_70.json`, `research_rig/sweep_71.py` and `research_rig/GRID_71.json`, the three rules, the plan 70 cost settings, the freeze commit and the first wake. The first wake is the first hourly open after `start`.
- `record` refuses to run if any of those files or settings has changed. On a signal or an exit it stays about 15 minutes for the later quotes.
- `loop` calls `record` 10 seconds after every hourly open, for as long as the process lives. Only one loop can run at a time.

## Money lines, all pretend

Each trade is $1,000 of pretend money, not compounded. The fee is the plan 70 judged futures-route charge for that coin (`replay_70_plan.futures_round_trip_bp` in [thresholds](../../config/thresholds.yaml): clearing fee plus two ticks plus 10 bp commission round trip) plus 1 bp for each hour of the hold (`funding_adverse_bp_per_hour`). Nothing else is added for slippage, because the spread is measured.

- Line (a), judged, rule 70-102 only: buy at the spot ask quoted as the entry wake fired, sell at the spot bid quoted as the exit wake fired, less the fee.
- Shown: the same at the quotes 1, 5 and 15 minutes later (three lines).
- Shown: the futures-priced line. Buy at the contract's ask and sell at its bid, both as the wakes fired, less the same fee. For a US account this is the more relevant line, because the futures contract is what such an account could trade.
- Shown: the spot quotes at the wakes, less 160 bp, the US spot taker fee of 0.80% a side from [doc 98](../../docs/research/98_kraken_and_coinbase_short_access.md) (`spot_taker_round_trip_bp`), with no futures fee.
- Shown: the hourly open prints less the fee, which is the search's own line, kept to compare against the quotes. A trade with a missing hold bar is left out of this line.
- Rules 71-013 and 71-035 get every line above, all shown only.

## What would count, fixed now

These marks are the lead's ruling and are fixed before the first record.

- Line (a) of rule 70-102 is judged once, at its first 150 judged trades (complete, with both first quotes at most 120 seconds after the hour) or at the last wake on 2027-11-30 (23:00 UTC), whichever comes first. After that point no rule opens a trade.
- Pass needs all three on line (a), over those trades:
  1. Net mean above zero.
  2. A day-clustered t of 2.0 or more, using plan 70's `t_cluster`, with days as UTC entry days.
  3. Net mean still above zero without its best 2 trades.
- Under 60 judged trades by the date is "too few to judge".
- The shown lines, the shown rules, and the counts of unresolved and late trades are reported next to the result and never judged.
- No profit figure of any kind is reported before then. `score` refuses until the judging point. At any time, `alive` and `publish` may report counts, void and late wakes, quote clocks and measured half-spreads by coin, and nothing else.

## Limits

- The quotes are top of book only. A $1,000 order could move past the best price; depth is UNKNOWN. Spreads in a crash hour may be much wider than in quiet hours.
- Spot quotes are not futures fills. Funding actually paid, margin, whole-contract size at $500 and price limits on the contracts are UNKNOWN (doc 153 section c).
- The coin list is plan 70's, chosen with hindsight. It is fixed for this card.
- Pass here would still be a practice result on one rule after a search. It is not approval for real money.
