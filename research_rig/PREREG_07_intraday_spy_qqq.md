# Pre-registration 07: day trading SPY and QQQ on one-minute bars

Status: FROZEN, written 2026-11-25 15:12 UTC from the draft plan of the same name ending in _DRAFT, before any rule was run on any of the data named here. Decided by the builder. Ledger rows 56 to 71 in `TRIAL_LEDGER.md`. Every number below that is not part of a rule's definition is a key in `config/thresholds.yaml`, named in backticks. Not edited after the run except a dated note at the bottom.

## Why

Day trading was the first thing asked for. Replay 03 tested it on bitcoin and ether and fees sank every rule. Stocks at Alpaca carry no commission, so the cost is the spread and slippage only. The published day trading rules for SPY and QQQ are author backtests, and the one independent reproduction in the repo puts break-even cost below `intraday_trend_max_round_trip_bps` for a round trip (`docs/research/01_stock_daytrading_evidence.md`). Research expects most of these to fail. The test is to measure it.

## Data

- One price source only: the one-minute and daily bars collected through the workspace's own price lookup on 2026-11-25, on the research machine at `research_rig/data/platform_bars/` or the folder in `PLATFORM_BARS_DIR`. The builder has decided they may be used for tests on the research machine. They are never copied into the repo or printed in bulk. There is no second source, so there is no cross-check.
- SPY one-minute bars from 2003-09-10, QQQ from 2011-03-23, both to 2026-11-24. The gap check is in `research_rig/data/platform_bars/INTEGRITY.md` and `docs/research/10_historical_data_and_practice.md`.
- UNKNOWN: whether the prices are adjusted for dividends or splits. The one-minute and daily files agree on most days (median gap 0 bps, `platform_bars_crosscheck.json`), so they are likely on the same basis, which is not shown to be either.
- UNKNOWN: the stock calendar. The holidays and early closes are the rule-based calendar in `platform_bars_integrity.py`, written from memory, checked against the exchange's record to December 2007 only. `run_07.py` imports it.

### Dividends and rule N5

Settled: N5 is kept, and no second dividend source is used. Every ex-dividend drop happens overnight. So N5 and holding the fund take the same drops and get the same treatment of the dividend, whichever way the file is built. If the prices are not adjusted, both miss the dividend income, about the fund's yield a year, and the day-only rules miss nothing because they hold no night. That would make holding look worse than it was and so favour every day-only rule against the comparison in marks 1 and 2. The write-up says so next to the result.

### Which days are used

A rule written here, applied by `run_07.py` to every day before any rule sees it. A day is used only if all of these hold:

1. It is a weekday and not a holiday in the calendar.
2. After the bars are put in New York time, it holds every regular minute exactly once and no other minute on a whole minute: 09:30 to 15:59 (390 bars) on a full day, 09:30 to 12:59 (210 bars) on an early close in the calendar. On an early close, bars after 12:59 are dropped first, because they are outside regular hours. A timestamp that is not on a whole minute fails the day.
3. Every bar has positive prices, high at least open, close and low, low at most open and close.
4. The one-minute day agrees with the daily file: the day's highest one-minute high is not above the daily high, the lowest one-minute low is not below the daily low, and the last one-minute close is not away from the daily close, each by more than `replay_07_data.max_gap_vs_daily_bps`. A day with no daily row fails. This is how a day whose one-minute bars may hold a price that never happened is found. Which file is wrong is not known, so the day is not used.

What happens to a day that is not used:

- No day trading rule trades on it. It is left out of every rule's daily series.
- Holding the fund carries through it: the next used day's return runs from the last used day's close.
- N5 holds through it: a position bought at the close of a used day is sold at 09:31 on the next used day.
- The count and dates of days not used, by reason, go in the output. No price does.
- The first `replay_07_data.warmup_days` used days of each fund are warm-up for N2 and are not in any result. Results start on the next used day, from the close of the day before it.

## Fill and cost rules

- A signal worked out from bars up to and including minute m is filled at the open of minute m+1.
- The end of the session is the close of the last bar (15:59, or 12:59 on an early close). A rule that is still holding sells there, which is a market-on-close order in practice. Every day trading rule is flat after it. Cash earns nothing.
- A stop is filled at the stop price if the bar opens above it and its low reaches it, else at the bar's open if the bar opens at or below it.
- Costs per side: `replay_07_costs.low_bps_per_side`, and the lower and upper end of `cost_model_bps_per_side_liquid_etf`. Pass marks are judged at the two config levels only. The low level is reported so the result can be read against `intraday_trend_max_round_trip_bps`.
- A trade's cost: buying spends cash divided by one plus the cost, selling returns the proceeds times one minus the cost, as in `rig2.py`.
- Long only, one fund at a time, the whole account in or out. No leverage, no shorting, no 3x funds. The papers' headline numbers use leverage or shorting, so these will be smaller by design.
- Results are daily. `replay_07_statistics.days_per_year` days a year.
- Sensitivities, reported and not judged: every fill at a minute's open moves one minute later (the close of the session and stop prices do not move); every stop pays one more cost.

## Rules (8 rules on each of SPY and QQQ, 16 trials)

Times are New York time. "Open" is the 09:30 bar's open. "Previous close" is the close of the last bar of the last used day. VWAP at minute m is the sum of (high + low + close) / 3 times volume over the bars from 09:30 to m, divided by their volume, or the close of m if that volume is zero.

| Id | Rule | Source of the idea |
|---|---|---|
| N1 | Opening range. If the 09:34 close is above the open, buy at the 09:35 open, if that open is above the stop. Stop: the lowest low from 09:30 to 09:34, live from the 09:35 bar. Otherwise sell at the session's close | [Zarattini and Aziz 2023](https://www.semanticscholar.org/paper/Can-Day-Trading-Really-Be-Profitable-Evidence-of-in-Zarattini-Aziz/4d55f526cc56f08662cb8976796cd3b719ef6d2b) |
| N2 | Noise band. For each minute t of the day, the move is the average, over the last 14 used days that have minute t, of the size of the move from that day's open to the close of t. Band at t: the larger of the open and the previous close, times one plus the move. Checked on the closes of 09:59, 10:29 and every half hour to 15:29 (to 12:29 on an early close). Flat and close above the band: buy. Holding and close below the band or below VWAP: sell. Fills at the next minute's open | [Zarattini, Aziz, Barbon 2024](https://econpapers.repec.org/paper/chfrpseri/rp2497.htm). The band uses the larger of the open and the previous close, as the paper does. The draft said the open only |
| N3 | First half hour, last half hour. If the 09:59 close is above the previous close, buy at the 15:30 open and sell at the session's close. Not traded on an early close | [Gao, Han, Li, Zhou 2018](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414) |
| N4 | Above the average price. On the close of each minute from 09:34 to 15:58, hold for the next minute if the close is above VWAP, else be flat. Changes fill at the next minute's open | [Zarattini and Aziz 2023, VWAP](https://papers.ssrn.com/abstract=4631351) |
| N5 | Night only. Buy at the session's close, sell at the 09:31 open of the next used day. Not a day trade | [Lou, Polk, Skouras](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf) |
| N6 | Day only. Buy at the 09:31 open, sell at the session's close, every used day. A yardstick | |
| N7 | Coin flip. On each used day, in date order, draw a number with seed `replay_07_statistics.seed`; below one half, do what N6 does. A yardstick | |
| N8 | Rest of day, last half hour. If the 15:29 close is above the previous close, buy at the 15:30 open and sell at the session's close. Not traded on an early close. Added at freeze: a later study by other authors that finds the same last half hour effect across many futures markets (STATED by its authors), with a different signal window from N3 | [Baltussen, Da, Lammers, Martens 2021](https://doi.org/10.1016/j.jfineco.2021.04.029) |

N5 and N6 together compound to holding the fund before costs, by construction. Each rule is compared with holding the same fund, bought at the close of the day before results start and never sold, paying the same cost per side once.

Settled: N8 is the one rule added. It is added for its source, before any rule was run, and not to change how likely a tie is in mark 4. Nothing was dropped.

## Slices

| Slice | Dates | Use |
|---|---|---|
| Development | first used day after warm-up to `replay_07_dates.dev_end` | look freely. QQQ's is shorter, from 2011 |
| Held back | `replay_07_dates.held_start` to `replay_07_dates.held_end` | each frozen rule run once |
| After the designer's knowledge cutoff | `replay_07_dates.post_start` to `replay_07_dates.last_day` | reported |

Settled: QQQ is judged on its own shorter development slice and the same held-back slice. Its rules are not left out.

`run_07.py --dev` reads no file after the development slice and cuts every series at its end. `run_07.py --full` is the one run of the held-back years. It is run once, after this plan and the ledger rows are pushed.

## Pass marks

The five marks of `research_rig/README.md`, numbers from `config/thresholds.yaml`, code from `rig2.py`. Worked out for each fund, rule and judged cost.

1. Held-back slice: Sharpe ratio above holding's and largest drop at most `replay_max_drop_ratio_vs_hold` of holding's.
2. Whole sample: the break-even cost per side against holding (the first cost where the rule's Sharpe ratio stops being above holding's, holding paying the same cost) is at least `backtest_min_breakeven_cost_multiple` times the cost judged.
3. Whole sample: deflated Sharpe ratio of the daily returns above `replay_min_deflated_sharpe`. Trial count `replay_07_statistics.trial_count`: the 93 counted in the ledger before this plan, the 7 of the frozen plan 09 (`replay_09_statistics`), which have no ledger rows yet, and these 16. Settled, spread of Sharpe ratios across all counted trials: the standard deviation of the yearly whole-sample Sharpe ratios of every stored row of the counted trials (replays 01 and 03 in the rerun `results_v2.json`, replay 04, both runs of replay 05; cross-checks X2 and S2 are not trials and are left out) and of these 16 at the cost judged, divided by the square root of `replay_07_statistics.days_per_year` to make it daily. The spread across these 16 alone is reported next to it.
4. The overfitting estimate (`rig2.pbo_cscv`, `replay_07_statistics.pbo_blocks` blocks, earliest days dropped, a tie counts as overfit) across the 8 rules of the fund at the cost judged, worked out from each start date in `replay_07_dates.pbo_starts_spy` or `replay_07_dates.pbo_starts_qqq` to the last day. Settled: the mark passes only if the largest of these is below `backtest_max_pbo`. Every value is reported.
5. Shuffled timing: `replay_07_statistics.shuffles` draws, seed `replay_07_statistics.seed`. Settled method: each used day's trades (their entry and exit minutes) are kept and moved to another used day of the same kind (full day or early close) by a random reordering of the days, then priced on that day's bars. This keeps the number of trades, the time held and the time of day, and breaks the link between the signal and that day's prices. A stop exit becomes a sale at the close of the same minute in a draw. The mark asks that the rule's daily Sharpe ratio beat more than `replay_min_shuffle_percentile` of the draws. N5 and N6 trade on every used day, so every draw equals the rule and they cannot pass this mark. That is known before the run. N5 overnight trades are moved with the day they end on.

A trial is called a pass only if it clears all five marks at both judged costs. A pass means "worth running on the practice desk". It does not mean "makes money".

Reported next to the marks: break-even cost for a round trip in bps (two sides) against holding and against zero (the first cost where the average daily return stops being above zero), set beside `intraday_trend_max_round_trip_bps`; growth a year, Sharpe ratio and largest drop by slice; results year by year; the share of the whole-sample log growth that came from the best 10 days; trades and days with a position; both sensitivities.

## Checks that must pass first

`run_07.py` stops before reading prices if any fails:

- `fixtures2.py`.
- The stock-calendar bar check, with its own fixtures: a full day passes; a missing minute, a repeated minute, a timestamp off the whole minute, a bar at 16:00, a weekend day and a holiday each fail; an early close with bars after 12:59 passes once they are dropped and ends at 12:59; the same timestamps in winter and summer time give the right New York minute; a one-minute high above the daily high by more than the band fails the day.
- A hand-worked day for N1 that hits its stop, one that gaps through it, and one that holds to the close, with costs.
- N6 and N5 together equal holding before costs on a synthetic history with a day not used.
- On the prices, after reading them: N6 and N5 together equal holding before costs within one part in a million, for each fund.
