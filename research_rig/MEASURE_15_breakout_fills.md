# Measurement 15. What a breakout order on stocks in play really paid

Status FROZEN 2026-11-26 01:43 UTC, before any trade or quote was collected.

This is a measurement, not a trial. No return is computed and nothing can pass or fail as a trading rule. It answers one question from queue row 23 and `docs/research/55_stocks_in_play_evidence_checked.md`: when the published opening-range rule says "buy on the break of the first five-minute bar", how far past that level did the first real trade print, and how far past the stop did the exit print.

## Why

- STATED by the paper: the rule made +1,637% from 2016 to 2023 with a commission and no slippage. STATED by one rebuild: measured fills averaged 2.4 cents past the level, about 12% of the stop distance, and with that charge the rule lost. Both are in doc 55 with links.
- UNKNOWN to us until this is run: what our own price feed says the fills were.

## Decision rule, fixed before the run

- Headline figure: mean entry slippage plus mean stop-exit slippage, each as a share of the stop distance, odd lots left out, all 60 days together.
- If that sum is at or below `measure_15_build_max_slip_share_of_stop` (5% of the stop distance), a full plan for the rule is written, with its own ledger rows.
- If it is above, the idea is dropped with our own number and queue row 23 moves to Done.
- Reason for 5%: the stop is a tenth of the daily range, most trades are stopped out, and the rebuild that lost measured about 12%. A cost of a twentieth of the amount risked on every trade is the most a rule of this shape can plausibly carry. This is a judgement by the lead agent, written down before any fill was seen.
- Shown, not part of the decision: medians and 90th percentiles, by year, by price bucket, with odd lots counted, quotes at the trigger and one second later, spreads at 09:35 and before the close.

## Sample, MEASURED before the freeze

- 60 days: the 10th market day of February, April, June, August, October and December, 2016 to 2025.
- 1,200 stock-days in play (20 a day), 1,187 with a direction.
- Dropped before the filters, all days together: 20,422 with no bar on the day, 5,973 with a zero-volume prior day, 1,116 missing a prior day, 934 duplicate-ticker days.
- Sizing note off repo, sha256 `9960aba655a2cecd61cd3eb8afb9c05365b98f4152b3b373d2db3104ead46fea`. Code off repo with these sha256 values: measure 5d70e8b666856934a15dca8d289acc879b679d8d60b4df3dadae279398d1ea3d, fetch a36bc43f1220c25de572e2f09f8c9d75c93cbd563ebe7bf6f5896f5835b8ffcc, tests 04cf286322a73a459299643c1e54708ffc3aad1f4f0c34c36a1fc6931b9a02f5 and 792413f7111d957e18e85d95234748784ca8d0cce554c798f121874f381f7cf2, feed helper 9908ff0878efdb05cc9e6c66784164e953d19ed0bc8312df049ecd72645beaa1.
- The code and the trades and quotes stay off the repo because they are vendor data and vendor-shaped. The result page will carry the summary figures only.

## Definition

- Sample: the 10th market day (SPY daily bars) of February, April, June, August, October and December, 2016 to 2025: 60 days.
- Universe each day: every symbol with Alpaca SIP bars (enumerated, dead ones kept), the 14 prior market days all present with volume above zero, daily bars split adjusted and put back on the day's own share count, an identical day bar under two symbols counted once, ETFs by today's Nasdaq Trader list dropped (exclude_etf_now; the skipped list is saved, the hand check is a stated limit).
- Filters: open above 5.0 dollars (min_open), 14-day mean volume at least 1,000,000 (min_avg_vol), 14-day ATR above 0.5 (min_atr), over 14 days (lookback).
- In play: the day's 09:30 to 09:35 New York 5-minute bar volume over the mean of the same bar on the 14 prior market days (all present), at least 1.0 (min_rel_vol); the top 20 (top_n), ties by symbol.
- Direction: long if that bar closes above its open, short if below, none if equal. Level: the bar's high (long) or low (short) as Alpaca gives it.
- Entry trigger: the first counted trade stamped at or after 09:35:00 New York (breakout_after) priced at or through the level, searched from the first 1-minute bar reaching the level for up to 5 minutes (max_minutes_search); otherwise 'no eligible trade'.
- Counted trades: size above zero and no condition in 4 6 7 8 9 B C G H K L M N P Q R T U V W Z (exclude_conditions). The reopening print 5 counts. Odd lots (I): the headline leaves them out (odd_lots_count False); also reported with them.
- Stop exit: stop = level minus direction times 0.1 times the 14-day ATR (stop_frac). Trigger = the first counted trade at or after the entry trade and before 16:00 priced at or through the stop, found in the entry minutes' trades or from the first later 1-minute bar reaching the stop, for up to 5 minutes; otherwise 'stop not reached by 16:00'.
- Slippage, entry and exit: trigger price minus trigger level in the losing direction, in cents, in basis points of the level, and as a share of the stop distance. Positive is worse.
- Quotes: the last quote stamped at or before the trigger trade with bid and ask above zero, and the same at the trigger plus 1 s (quote_lag_ns). Ask (buy) or bid (sell) minus the level, in cents and basis points. Locked or crossed quotes kept and flagged.
- Spreads: the last quote at or before 09:35:00 and before 16:00:00, in cents and basis points of the mid.
- Report: n, median, mean and 90th percentile (linear interpolation) of every slippage field, entry and exit, both odd-lot settings, for all, by year and by level price bucket with edges (5, 10, 20, 50, 100) (price_buckets); spreads bucketed by the 09:30 open. Counts of no direction, no breakout, no eligible trade, stop not reached. No return is computed.
- Known limits: today's ETF list; tickers never asked (5-letter endings other than A B C K L, dots other than .A .B); the breakout and stop minutes come from 1-minute bars, which may leave out some prints, so the odd-lot version can only trigger inside minutes the bars point to; whether the timestamp is participant or SIP time is UNKNOWN; quotes are taken as the national best bid and offer (likely, not proven).

## Limits, written before the run

- 60 mornings is a sample, not the whole period. Two days a quarter-year cannot show a bad month.
- The first printed trade past the level is the best case for a small market order, not a guarantee of that price.
- A measured cost near zero would not show the rule works. It would only remove the reason to drop it without a test.
