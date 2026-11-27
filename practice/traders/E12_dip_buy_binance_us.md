# E12: forward dip buy on Binance.US

STATED: Ledger 230, queue 135. Pretend money, forward only, no account,
orders, key, compounding or imported observations. E09 and E11 closed
unjudged; the three cards count as one family. No profit claim before the
judging point. The frozen rules were found on other venues' bars; Binance.US
candles can give different signals.

Use the original list restricted to exact Binance.US USD listings on the first
scheduled wake, including nontrading listings. If that wake cannot freeze the
list, or BTC/USD is missing, stop. Closed hourly USD candle panels feed the
unchanged 70-102 rule (judged) and 71-013 / 71-035 rules (shown). A missing
panel voids new entries, not scheduled exits. Never substitute another pair or
pick a later roster.

Walk a fresh post-decision ask for a pretend $250 and sell the resulting base
amount into the exit bid. The judged line voids missing, refused, late
(over 120 seconds from the hour) or thin books; keep the slot until its fixed
exit. A late first book cannot seed a shown fill, resting bid or trade-page
request. Taker fees are STATED at 2 bp per side (BNB/USD 1 bp). Judge once,
at 150 closed valid 70-102 trades or the final wake on November 30, 2027:
positive net mean, UTC entry-day clustered t of at least 2.0, and positive
mean omitting the best two trades. Below 60, report too few to judge.

Show $25 and books at 1, 5 and 15 minutes after each first book. Show a $250
resting buy at the first bid only if a public trade prints strictly below it
within 300 seconds. Missing proof of coverage without a qualifying print is
UNKNOWN. The maker entry fee is STATED at zero; the exit is a taker.
Compare scheduled midpoints to the limit on all signals and separate
before-fill observations from after-fill figures. Show confirmed missed trades
as a separate aggregate; do not relabel unknown fills as misses.

Only [Binance.US public REST](https://docs.binance.us/) is permitted.
After an independent CLEAR audit, the lead records `E12_START=<frozen build hash>`
on row 230 in committed local main. Use `start` to create the private header,
then `loop` from the frozen worktree. Readout needs a separate `E12_SCORE`
for the same build. Public output contains counts, timing and cost aggregates
only; detail is kept in `/home/user/workspace/rig/data/forward_e12`.
All project Binance.US collectors share a durable cooldown after HTTP 429 and
a durable stop after HTTP 418, 401, 403 or 451. Never backfill missed slots.
A stop invalidates every run bound to the old gate generation, even if the
lead clears the active stop. A new run above generation zero additionally
needs `E12_START_GENERATION=<n>` on the same committed ledger row. An in-flight
marker with no live lease blocks all requests until the lead inspects it.
A live network failure with no HTTP status waits 60 seconds across collectors;
the third consecutive failure waits 15 minutes until an HTTP reply resets the count.
