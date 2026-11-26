# E10: Coin trend ratchet forward practice

STATED. Plan 75 earned this practice card only, not an authorization to trade. No keys, login, orders, real money, or access to Plan 75's replay packets. The lead agent starts the log only after audit.

## Rule and market

STATED. Use the Plan 75 primary book for decisions: 10-, 20- and 30-day legs, 25% volatility target on 90 daily returns, 100% cap per leg, stops that only move up while live, and a 20-point band on volatility resizes only. Equal coin envelopes reset monthly. Decisions use completed UTC daily closes, for the next midnight UTC open. Use the frozen scorer's upper-branch precedence and stop comparison. The official scorer governs warm-up: keep signal and stop state as soon as the lookback exists; gate sizing at 91 consecutive closes. No profit before the first recorded wake.

STATED. Use public Coinbase Exchange USD daily candles, including completed pre-start closes for warm-up. Plan 75 used Binance USDT bars; USD and Coinbase are deliberate differences. Read the 20 Plan 70 coins and record the public product flags at each observed wake. No USD product, unknown state, trading disabled, cancel-only, or post-only permits neither buys nor sells. Limit-only removes the coin and forbids new positions or adds, but allows sales at the bid. Returns to the roster follow the frozen monthly rule. If all products disallow both sides, carry the previous roster and mask opens; closes still feed indicators and marks.

## Clock, execution and size

STATED. At 10 seconds after midnight UTC the loop starts a sequential public observation, fetching product state then best bid and ask. For every candidate order, try level-one snapshots again at 1, 5 and 15 minutes after midnight; keep actual receipt times. Do not reconstruct missed snapshots. The first scheduled wake is the next UTC date after start. A missed wake or a coin quote absent or later than 15 minutes voids its new buys. Pending sells wait for an observed sellable wake, including a recorded late wake. Queued-sell counts are queue-at-wake counts, not unique orders. Completed closes from missed dates may feed later decisions and mark existing positions, but never create fills for missed dates.

STATED. Main fills use the wake ask to buy and bid to sell, with the 60 bp fee per side inherited from replay_47_plan. Main proposed sizing uses the midpoint, not the eventual execution side. Shown books use the candle open and Plan 75 flat 75 bp and harsh 145 bp per-side costs. Compare $500 fractional pretend principal with a $5,000 shown-only placeability book. Use explicitly reported base minimum and minimum market funds, requiring both if both exist. If neither is reported, skip and count separately rather than inventing a minimum. Count net coin attempts, including observable voided orders. No quote means no measured spread or main fill.

## Readout

STATED. Alive and publish report counts and costs only: wakes, void, missed and late wakes, orders, fills, sub-minimum and unknown-size skips, quote misses, void buys, queued sales, coin-level median and 90th percentile half-spread and all-in cost by side versus the flat line. All-in cost is versus contemporaneous midpoint and includes the stated fee on notional; the fee itself is not measured. No second-feed decision comparison. No prices or profit in public output.

STATED. Score refuses before 365 days after the first recorded wake and until the closing observation is recorded. It prints net return, largest fall and matched-volatility BTC at all three cost lines, whole period and by UTC calendar quarter, once for the lead agent. Held positions are marked at the last valid close with stale marks disclosed; no fictitious liquidation. BTC buys at the first wake ask and holds, with the cost-line fee on scaled entry notional. A missing or late first ask or missing BTC close makes the comparison unscorable, not a later entry. Each quarter uses its own volatility match; BTC is not repurchased at quarter boundaries.

STATED. The reported held-back Sharpe was near 0.36. A forward year cannot confirm or reject the rule; profit is a record, not a verdict. Costs and placeability are the parts that can settle something. Runtime numbers are kept under forward_e10 and its inherited keys in config/thresholds.yaml.

## Operation and audit

STATED. Use the private folder /home/user/workspace/rig/data/forward_e10 (0700 folder, 0600 files). The hash chain and durable tip detect edits or truncation under ordinary corruption, not someone who can rewrite both. An interrupted write with mismatched tip refuses pending audit. Pin SHA-256 of the card, logger, frozen decision module and config. One loop and one writer at a time. Only the stated Coinbase public host; back off on 429 and persistently stop on 401, 403 or 451. Do not route around a refusal.

UNKNOWN. Live field availability, placeability, snapshot latency and forward outcomes until audit and observation. Plan is offline; start freezes and schedules; record handles the current wake; loop schedules wakes; score is for the lead agent. The CLI does not authenticate that role; the lead controls the private folder and invocation.
