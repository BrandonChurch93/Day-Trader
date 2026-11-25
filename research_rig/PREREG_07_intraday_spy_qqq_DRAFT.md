# Pre-registration 07 (draft): day trading SPY and QQQ on one-minute bars

Status: DRAFT, written 2026-11-25. Not frozen and not in the trial ledger. It is frozen and logged only when every gate below is met (the data, the owner's yes to decision 4b, and his decision on pass mark 4), and before any rule is run on it. Proposed by research. No owner decision is recorded here.

Blocked on: one-minute prices for SPY and QQQ. Two possible sources: a purchase, or the workspace's own price history if the owner allows it and it passes a gap check (`docs/research/10_historical_data_and_practice.md`, "Price history inside the workspace", and items 2 and 6 of `docs/decisions/morning_list_2026-11-25.md`). The workspace's own price history has no dividends, and rule N5 below needs them. So on that source alone, N5 must either get dividends from a second source or be dropped, and the plan must say which before it is frozen. Also waits on the owner's yes to decision 4b and his decision on pass mark 4. If both sources are in hand, the plan must say before it is frozen which one is the test and which one is the cross-check.

## Why

Day trading was the first thing asked for. Replay 03 tested it on bitcoin and ether and fees sank every rule. Stocks at Alpaca carry no commission, so the cost is the spread and slippage only. The published day trading rules for SPY and QQQ are all author backtests, and the one independent reproduction held in the repo puts break-even cost below `intraday_trend_max_round_trip_bps` for a round trip (`docs/research/01_stock_daytrading_evidence.md`). Research expects most of these to fail. The test is to measure it.

## Data needed

One-minute open, high, low, close, volume for SPY and QQQ, regular hours 09:30 to 16:00 New York time, as far back as the provider goes, with a calendar of half days. Daily dividend data for overnight holds. Raw files stay out of the repo.

## Fill and cost rules

- A signal worked out from bars up to and including minute m is filled at the open of minute m+1. Sensitivity, reported: filled at the open of minute m+2.
- A stop is filled at the stop price if the bar opens on the good side of it, else at the bar's open. Sensitivity: every stop pays one more cost.
- Cost per side at three levels: 0.5 bps, the lower end of `cost_model_bps_per_side_liquid_etf`, and the upper end. The lowest level is reported so the result can be read against `intraday_trend_max_round_trip_bps`. Marks are judged at the two config levels only. To settle before this plan is frozen: the 0.5 bps is typed here and is not a key in `config/thresholds.yaml`. It needs a key, with a dated note in `docs/decisions/`, or a line saying why it is not a threshold.
- Long only. No leverage, no shorting, no 3x funds. The papers' headline numbers use leverage or shorting, so ours will be smaller by design.
- Every day trading rule is flat at 15:59. Cash earns nothing inside the day.
- 252 days a year.

## Rules (7 rules on each of SPY and QQQ, 14 trials)

| Id | Rule | Source of the idea |
|---|---|---|
| N1 | Opening range: if the first 5-minute bar closes above its open, buy at 09:35. Stop at that bar's low. Sell at 15:59 | [Zarattini and Aziz 2023](https://www.semanticscholar.org/paper/Can-Day-Trading-Really-Be-Profitable-Evidence-of-in-Zarattini-Aziz/4d55f526cc56f08662cb8976796cd3b719ef6d2b) |
| N2 | Noise band: at each half hour from 10:00, hold if price is above the day's open plus the average absolute move from the open to that time of day over the last 14 days. Leave when price falls back under the band or under the day's volume-weighted average price | [Zarattini, Aziz, Barbon 2024](https://econpapers.repec.org/paper/chfrpseri/rp2497.htm) |
| N3 | First half hour, last half hour: if the return from yesterday's close to 10:00 is positive, buy at 15:30 and sell at 15:59 | [Gao, Han, Li, Zhou 2018](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414) |
| N4 | Above the average price: from 09:35, hold while price is above the day's volume-weighted average price, checked each minute | [Zarattini and Aziz 2023, VWAP](https://papers.ssrn.com/abstract=4631351) |
| N5 | Night only: buy at 15:59, sell at 09:31 the next day. Not a day trade. Included because the reading says the night is where the return has been | [Lou, Polk, Skouras](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf) |
| N6 | Day only: buy at 09:31, sell at 15:59, every day. A yardstick | |
| N7 | Coin flip: on a random half of days (seed 7) do what N6 does. A yardstick for what trading every other day at these costs looks like | |

Each rule is compared with holding the fund.

## Slices

| Slice | Dates | Use |
|---|---|---|
| Development | first day of data to 2018-12-31 | look freely |
| Held back | 2019-01-01 to 2026-06-30 | each frozen rule run once. Most of it lies after the papers' samples or after they were published |
| After the designer's knowledge cutoff | 2026-07-01 to the last day in the file | reported |

To settle before this plan is frozen: if a rule is added or dropped, the rule list, the trial count, the fixtures and the set of rules that mark 4 is worked out over are all rewritten here first. No rule is added or dropped to change how likely a tie is in mark 4.

To settle before this plan is frozen: on the workspace's own price history, one-minute data for QQQ starts years later than for SPY (`docs/research/10_historical_data_and_practice.md`, "What was collected, and what a gap check found"). If that source is used, the plan has to say first whether the QQQ rules are judged on their own shorter development slice or left out. The short days and missing days that the gap check lists also have to be handled by a rule written here, not case by case. On some days a one-minute price also sits outside the day's range in the daily file from the same source, which cannot be if both are right (MEASURED by `research_rig/platform_bars_crosscheck.py`, same section of that document). Which file is wrong is not shown. A stop or a breakout rule would trade on such a bar. The plan has to say, before it is frozen and before any rule sees the data, how such a day is found and what is done with it.

## Pass marks

The five marks used in the other replays, numbers read from `config/thresholds.yaml`, with the methods of `AMENDMENT_2026-11-25_audit_fixes.md`. Shuffle for these rules: the rule's daily profit or loss is kept and the days it traded are redrawn at random with the same count, 1,000 times, seed 7. Trials counted in the deflated Sharpe ratio: every rule trial in the ledger on the day this is frozen, reruns included, plus these 14. Today that count is the one `TRIAL_LEDGER.md` gives under "Reruns and how they are counted"; the six AI model runs in rows 21 to 26 are scored a different way and are not in it. This draft is not frozen until the owner has settled how mark 4 is to be measured (`docs/STATUS.md`, "Next in the queue").

Reported next to the marks: break-even cost for a round trip in bps, set beside `intraday_trend_max_round_trip_bps`; results year by year; the share of the profit that came from the best 10 days.

A pass means "worth running in the practice account". It does not mean "makes money".

## Checks that must pass first

`fixtures2.py`; a bar check that knows the stock calendar, with its own fixtures, because `rig2.check_bars` rejects bars with no weekends (`research_rig/README.md`); half days end at the right minute; no bar outside regular hours is used; a hand-worked day for N1 including the stop; N6 plus N5 compounds to holding the fund within rounding before costs.
