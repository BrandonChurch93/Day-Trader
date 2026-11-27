# Measurement 133: forward Binance.US USD spot costs

STATED: Ledger 232, queue 137. Measurement 132 closed unread and contributes
no data. Use only [Binance.US public REST](https://docs.binance.us/), without
keys or account access. Observe the original 20 candidates, with no
replacement or denominator reduction for missing or nontrading USD pairs.
No profits, return series, account recommendation or rescore.

For 30 days, wake ten seconds after each UTC hour. A book counts only if
received from +10 through +120 seconds after the top of that UTC hour,
both ends included; earlier or later is missed. For $25 and $250, walk either
side by dollar amount, compare the resulting average fill to the midpoint,
then add the STATED taker fee once per side (2 bp; BNB/USD 1 bp). Unavailable,
refused, crossed, late and thin books do not contribute a fill. Classify
BTC-drop hours from the two adjacent closed hourly BTC/USD closes, using a
log drop of at least 1.5%; an unknown candle cannot label a drop hour.

The lead reads once after the last wake, reporting count, median and p90 cost
by coin, size and side for all, midnight UTC, and BTC-drop hours. Use the
25 bp cost line only if at least 15 of the original 20 each have paired
$250 buy/sell costs on at least 25 of the 30 UTC midnights and a separate median
no greater than 25 bp on both sides. Otherwise retain 75 bp. Neither outcome
changes a finished test.

After an independent CLEAR audit, the lead writes `M133_START=<frozen build hash>`
on row 232 in committed local main, then uses `start` and `loop` from the
frozen worktree. Readout needs a separate `M133_READ` for the same build.
Use `/home/user/workspace/rig/data/measure_133` for private observations.
The public file carries pooled costs and counts, not prices or per-wake rows.
All project Binance.US collectors share a durable cooldown after HTTP 429 and
a durable stop after HTTP 418, 401, 403 or 451. Never backfill missed slots.
