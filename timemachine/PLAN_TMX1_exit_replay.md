# Time machine exit replay plan TMX1: fixed exit templates on logged AI buys

Written 2026-11-25 16:20 UTC before any replay numbers were run or read. Pretend money only.

## Question

Did our AI traders in the crypto time machine lose through their exits? Published research suggests that small fixed profit targets paired with tight stop-losses hurt net performance. This replay holds every logged AI entry fixed and tests whether replacing the trader's exits with simple fixed exit templates improves summed dollar gains.

## Scope and inputs

- Sessions: all finished sessions (`result.json` present) for plans `TM01` (`TM01-B01-<MODEL>-2026-<MM>`) and `TM02` (`TM02-B02-<MODEL>-2026-<MM>`), plus their finished random twin sessions (`TWIN-TM01-...` and `TWIN-TM02-...`), across the six models (`OPUS`, `SOL`, `NEON`, `SONNET`, `KIMI`, `GROK`) and five months (July, August, September, October, and November 1 to 24, 2026). Unfinished sessions at run time are excluded and listed with the UTC timestamp from `date -u`.
- Trades: every logged filled BUY order (its fill time, coin, fill price, and filled quantity/dollar size as recorded in the session's `result.json`), replayed one trade at a time on its own without re-simulating the cash book.
- Prices: `1Min` bars from `/home/user/workspace/rig/tm_store/tape.sqlite` (read-only).
- Costs: read from `config/thresholds.yaml` (`tm_crypto_half_spread_bps`, `practice_crypto_fee_bps_added`, `practice_crypto_fee_in_coin`), matching `timemachine/simbroker.py`. The logged BUY fill price already includes the buy half-spread; a simulated sell fills at the next recorded minute's open less the half-spread, with the same crypto fee applied on both sides.

## Five fixed exit templates (no others)

- **A (as traded):** realized dollar gain from the session records (`closed` trades matched to the logged buys; any position still open at the session end is marked to the session's final recorded 1Min close, net of entry costs, matching the session books).
- **B (48h time only):** sell at the first recorded 1Min bar open at or after 48 hours from the fill timestamp.
- **C (120h time only):** sell at the first recorded 1Min bar open at or after 120 hours from the fill timestamp.
- **D (8% stop, 120h):** check each 1Min close strictly after the fill minute; if close is at or below 0.92 times the fill price, trigger a stop and sell at the next recorded 1Min bar open. No profit target. Otherwise sell at the 120-hour time exit.
- **E (8% stop, +3% trigger / 5% trail, 120h):** check each 1Min close strictly after the fill minute. Maintain the highest 1Min close seen since entry (starting from the fill price). Initial stop is 0.92 times the fill price. Once any 1Min close is at or above 1.03 times the fill price, the stop becomes the greater of the 8% initial stop and 0.95 times the highest 1Min close seen so far. If a 1Min close is at or below the active stop, trigger and sell at the next recorded 1Min bar open. Otherwise sell at the 120-hour time exit.

For templates B through E, every trade still open at the session's last minute is closed at the session's final recorded 1Min bar open (or if a trigger fires on the final minute with no next minute inside the session, closed at that final minute's close) with the sell half-spread and fee.

## Marks and yardsticks, fixed now

- **Primary mark ("helps"):** On finished `TM01` AI buys, a template **helps** only if its summed dollar gain beats Template A in **at least 4 of the 5 months** AND for **at least 5 of the 6 models**.
- **Second-look caveat:** This is a second look at months already traded. A "helps" verdict does not prove a rule is profitable and is not a result to trade on; it only earns a fresh test on new months.
- **Random twin comparison:** The exact same five templates are run on all finished random twin buys (`TWIN-TM01-...` and `TWIN-TM02-...`). The report shows **AI buys minus twin buys** (using the mean summed dollar gain across each session's finished twins so scale matches one AI session) under each template. That difference is the only sign of entry skill.
- **Bitcoin hold over the same windows:** Because holding longer in a rising month gains from the market alone, the report also shows the summed dollar gain of holding bitcoin over the exact same entry-to-exit windows and dollar sizes as each template's trades (using the same spread and fee model).
