# 42. Small and fast crypto coins on Alpaca versus Coinbase

Status: research measurement. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Every market number below is MEASURED from Alpaca historical crypto bars and quotes and public Coinbase Exchange and Kraken market data, placed here by gen_doc_42_small_coins.py from crypto_small_alpaca.json and crypto_small_external.json (kept outside the repo in the rig folder). Prior test buy counts and fee assumptions are STATED from the builder's records.

## Why

Earlier crypto time-machine tests used only eight large coins (BTC/USD, ETH/USD, SOL/USD, XRP/USD, DOGE/USD, AVAX/USD, LINK/USD, LTC/USD) and charged a flat 10 bps half-spread on every coin. On a $300 account, larger daily moves matter more, so we measured every USD crypto pair Alpaca serves to see which smaller, faster coins are tradeable on Alpaca, what half-spread each one actually carries, and whether thinness comes from the coins themselves or from Alpaca's own venue.

## How the measurements were taken

- Window (MEASURED): 2026-04-01 to 2026-11-24 (238 calendar days, 342,720 minutes).
- Pairs checked (MEASURED): 36 active USD pairs with bars on Alpaca's US crypto feed, plus 5 legacy symbols that returned quotes but zero bars in the window (ALGO/USD, MATIC/USD, MKR/USD, NEAR/USD, TRX/USD).
- Daily volume and range (MEASURED): from Alpaca daily bars over the window. Daily range is (high minus low) divided by open. Median daily dollar volume is the median of daily close times volume on Alpaca's own venue.
- Minute activity (MEASURED): from Alpaca one-minute bars over the same window. Alpaca emits quote-driven bars even when zero volume traded, so we report both the share of minutes with any bar and the share of minutes with an actual trade (volume above zero).
- Historical half-spread (MEASURED): regular sampling of Alpaca historical crypto quotes across the window, every 4 days at 00:00, 06:00, 12:00 and 18:00 UTC (240 regular timestamps per coin). At each timestamp we took the first valid two-sided quote within a 30-second window and computed (ask minus bid) divided by (2 times midpoint) in bps.
- External US-open venue check (MEASURED): public Coinbase Exchange endpoints for 34 pairs and public Kraken endpoints for the two stablecoins not listed as USD spot on Coinbase (USDC/USD and USDG/USD). Median daily dollar volume is over the trailing 30 days; half-spread is the median of three live top-of-book samples.

## Pass rule for a $300 account on Alpaca

To pass onto the Alpaca tape as a believable next-minute fill for a $300 account, a new pair had to meet all four checks:

- At least 2.0% of minutes with an actual trade (volume above zero), matching the floor of the existing eight coins (LTC/USD is at 2.14%).
- At least $2,000 median daily dollar volume on Alpaca, so a $300 order is at most 15% of a typical day's venue volume.
- At least 65% of minutes with a one-minute bar present.
- Not a stablecoin or gold-pegged token.

## Bottom line

- MEASURED: Thinness is overwhelmingly Alpaca's venue, not the coins. On Alpaca, even BTC/USD prints a trade in only 34.61% of minutes and ETH/USD in 16.61%. Quote-driven zero-volume bars appear in 20.6% to 97.0% of minutes, which makes the feed look fuller than actual trading.
- MEASURED: Only 5 new pairs pass on Alpaca (UNI/USD, AAVE/USD, DOT/USD, ADA/USD, BCH/USD). Another 19 pairs fail as too thin on Alpaca (0.24% to 1.12% traded minutes, median daily Alpaca volume $38.64 to $1,173), and 4 fail as pegs (PAXG/USD, USDT/USD, USDC/USD, USDG/USD).
- MEASURED: The same rejected coins trade deeply on Coinbase, a US-open venue. HYPE/USD trades $37,997,397 a day on Coinbase at 1.70 bps half-spread (32,399 times its $1,173 Alpaca volume and 26.32 bps Alpaca half-spread). PEPE/USD trades $4,549,439 a day on Coinbase versus $883 on Alpaca; ONDO/USD trades $4,052,043 at 3.84 bps versus $587 at 26.72 bps.
- MEASURED: Passing coins are also much cheaper on Coinbase. UNI/USD is 2.18 bps on Coinbase versus 12.52 bps on Alpaca; ADA/USD is 2.11 bps versus 22.96 bps.
- MEASURED: Only a small tail of coins are genuinely light even on Coinbase: SUSHI/USD ($90,106 a day), XTZ/USD ($90,675 a day), YFI/USD ($121,266 a day), LDO/USD ($139,126 a day).
- UNKNOWN: Live fill slippage during fast moves on either venue is not measured here; these figures are top-of-book quoted half-spreads from regular samples.

## Full table of all 36 active Alpaca USD pairs

Sorted by median daily range (high minus low over open), descending. All columns are MEASURED.

| Pair | Days | Alpaca med $/d | Any 1m bar | Traded 1m (v>0) | Range med | Range p90 | Alpaca HS (bps) | Alpaca HS p90 | Ext venue | Ext med $/d (30d) | Ext HS (bps) | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|
| TRUMP/USD | 238 | $110 | 75.52% | 0.57% | 8.87% | 38.51% | 24.84 | 26.39 | coinbase | $1,246,389 | 4.87 | Fail (thin on Alpaca) |
| WIF/USD | 238 | $71.50 | 84.12% | 0.40% | 8.20% | 21.76% | 22.77 | 24.67 | coinbase | $348,766 | 4.17 | Fail (thin on Alpaca) |
| LDO/USD | 238 | $99.03 | 81.56% | 0.40% | 7.93% | 16.94% | 27.56 | 28.88 | coinbase | $139,126 | 11.65 | Fail (thin on Alpaca) |
| BAT/USD | 238 | $141 | 68.71% | 0.71% | 7.39% | 16.01% | 45.11 | 46.81 | coinbase | $206,854 | 3.98 | Fail (thin on Alpaca) |
| BONK/USD | 238 | $119 | 88.18% | 0.54% | 7.38% | 19.09% | 45.66 | 53.86 | coinbase | $610,296 | 24.10 | Fail (thin on Alpaca) |
| PEPE/USD | 238 | $883 | 77.78% | 1.12% | 7.33% | 32.74% | 25.81 | 35.19 | coinbase | $4,549,439 | 14.81 | Fail (thin on Alpaca) |
| ARB/USD | 238 | $301 | 86.55% | 0.65% | 7.13% | 17.34% | 22.72 | 24.32 | coinbase | $1,113,776 | 2.75 | Fail (thin on Alpaca) |
| CRV/USD | 238 | $501 | 80.55% | 0.96% | 7.02% | 15.39% | 12.39 | 14.11 | coinbase | $912,628 | 5.87 | Fail (thin on Alpaca) |
| FIL/USD | 238 | $265 | 83.04% | 0.57% | 6.95% | 17.76% | 22.53 | 24.35 | coinbase | $1,077,546 | 3.79 | Fail (thin on Alpaca) |
| ONDO/USD | 238 | $587 | 85.50% | 0.70% | 6.94% | 15.03% | 26.72 | 28.45 | coinbase | $4,052,043 | 3.84 | Fail (thin on Alpaca) |
| SUSHI/USD | 238 | $169 | 78.70% | 0.60% | 6.93% | 16.73% | 12.70 | 14.37 | coinbase | $90,106 | 9.93 | Fail (thin on Alpaca) |
| RENDER/USD | 238 | $264 | 77.67% | 0.57% | 6.69% | 15.85% | 24.69 | 26.35 | coinbase | $1,426,707 | 3.97 | Fail (thin on Alpaca) |
| UNI/USD | 238 | $4,255 | 83.80% | 4.32% | 6.62% | 14.53% | 12.52 | 14.02 | coinbase | $7,038,317 | 2.18 | Pass (added) |
| AAVE/USD | 238 | $3,601 | 83.50% | 3.10% | 6.06% | 14.41% | 12.63 | 14.55 | coinbase | $3,910,786 | 3.24 | Pass (added) |
| GRT/USD | 238 | $290 | 71.51% | 0.61% | 5.70% | 14.10% | 25.89 | 27.60 | coinbase | $311,275 | 5.90 | Fail (thin on Alpaca) |
| HYPE/USD | 238 | $1,173 | 83.26% | 0.70% | 5.65% | 14.03% | 26.32 | 27.74 | coinbase | $37,997,397 | 1.70 | Fail (thin on Alpaca) |
| XTZ/USD | 238 | $148 | 69.24% | 0.38% | 5.62% | 13.47% | 45.12 | 46.68 | coinbase | $90,675 | 11.78 | Fail (thin on Alpaca) |
| SKY/USD | 238 | $123 | 66.75% | 0.47% | 5.55% | 13.75% | 12.33 | 14.27 | coinbase | $211,860 | 5.02 | Fail (thin on Alpaca) |
| DOT/USD | 238 | $2,690 | 79.16% | 3.70% | 5.53% | 9.73% | 12.46 | 14.26 | coinbase | $1,235,852 | 3.86 | Pass (added) |
| ADA/USD | 238 | $3,502 | 78.28% | 3.84% | 5.24% | 10.84% | 22.96 | 24.70 | coinbase | $7,814,427 | 2.11 | Pass (added) |
| AVAX/USD | 238 | $5,800 | 74.93% | 4.23% | 5.05% | 10.12% | 44.78 | 46.67 | coinbase | $5,022,264 | 2.33 | Already on tape |
| YFI/USD | 238 | $62.66 | 64.95% | 0.33% | 4.88% | 18.64% | 16.77 | 18.62 | coinbase | $121,266 | 11.52 | Fail (thin on Alpaca) |
| POL/USD | 238 | $38.64 | 67.82% | 0.24% | 4.87% | 12.69% | 25.45 | 27.25 | coinbase | $459,066 | 4.66 | Fail (thin on Alpaca) |
| BCH/USD | 238 | $2,069 | 69.25% | 2.36% | 4.81% | 12.61% | 44.73 | 46.70 | coinbase | $2,320,958 | 4.03 | Pass (added) |
| SHIB/USD | 238 | $505 | 79.84% | 0.86% | 4.69% | 12.73% | 25.32 | 31.75 | coinbase | $328,143 | 14.31 | Fail (thin on Alpaca) |
| LINK/USD | 238 | $6,587 | 74.24% | 4.27% | 4.61% | 8.81% | 12.34 | 14.33 | coinbase | $7,932,017 | 1.14 | Already on tape |
| SOL/USD | 238 | $24,758 | 73.23% | 12.24% | 4.29% | 8.22% | 18.33 | 26.87 | coinbase | $86,349,748 | 0.73 | Already on tape |
| DOGE/USD | 238 | $3,578 | 71.53% | 3.39% | 4.25% | 8.46% | 22.39 | 23.95 | coinbase | $7,272,231 | 1.84 | Already on tape |
| LTC/USD | 238 | $2,128 | 66.17% | 2.14% | 3.83% | 9.02% | 44.85 | 46.54 | coinbase | $7,000,257 | 1.94 | Already on tape |
| XRP/USD | 238 | $20,228 | 69.70% | 13.94% | 3.80% | 7.69% | 25.26 | 27.63 | coinbase | $86,391,239 | 1.09 | Already on tape |
| ETH/USD | 238 | $48,392 | 67.78% | 16.61% | 3.61% | 6.65% | 4.54 | 7.63 | coinbase | $286,255,906 | 0.48 | Already on tape |
| PAXG/USD | 238 | $6,759 | 37.27% | 12.65% | 2.75% | 4.74% | 81.13 | 84.02 | coinbase | $1,730,772 | 4.35 | Fail (peg) |
| BTC/USD | 238 | $117,615 | 96.99% | 34.61% | 2.72% | 5.47% | 4.85 | 7.88 | coinbase | $769,657,441 | 0.00 | Already on tape |
| USDT/USD | 237 | $10,534 | 20.59% | 0.61% | 0.14% | 0.20% | 6.64 | 8.06 | coinbase | $39,226,638 | 0.05 | Fail (peg) |
| USDC/USD | 236 | $1,784,152 | 27.57% | 1.37% | 0.05% | 0.05% | 2.55 | 352.05 | kraken | $93,698,460 | 0.50 | Fail (peg) |
| USDG/USD | 140 | $182,991 | 26.68% | 0.06% | 0.00% | 0.00% | 0.10 | 354.25 | kraken | $2,155,262 | 0.50 | Fail (peg) |

## What this means for earlier tests

- STATED: Plans TM01 and TM02 charged a flat 10 bps half-spread on every coin.
- MEASURED: Actual median Alpaca half-spreads were about 5 bps for BTC/USD (4.85 bps) and ETH/USD (4.54 bps), 12 to 26 bps for LINK/USD (12.34), SOL/USD (18.33), DOGE/USD (22.39) and XRP/USD (25.26), and about 45 bps for AVAX/USD (44.78) and LTC/USD (44.85).
- Therefore those sessions' trading costs were slightly overstated on BTC/USD and ETH/USD and understated on the smaller coins. Earlier results are not recomputed here; the buy counts by coin in those sessions (STATED) are shown beside the measured Alpaca half-spreads below.

| Coin | TM01+TM02 buys (STATED) | Assumed HS (STATED) | Measured Alpaca HS (MEASURED) | Suggested Alpaca HS (bps) |
|---|---:|---:|---:|---:|
| BTC/USD | 147 | 10 bps | 4.85 bps | 5 |
| ETH/USD | 71 | 10 bps | 4.54 bps | 5 |
| SOL/USD | 68 | 10 bps | 18.33 bps | 19 |
| LINK/USD | 40 | 10 bps | 12.34 bps | 13 |
| XRP/USD | 18 | 10 bps | 25.26 bps | 26 |
| AVAX/USD | 16 | 10 bps | 44.78 bps | 45 |
| LTC/USD | 11 | 10 bps | 44.85 bps | 45 |
| DOGE/USD | 2 | 10 bps | 22.39 bps | 23 |

## What this does not show

- Order-book depth beyond the top of book on Alpaca or Coinbase. That is UNKNOWN here; a live order-book sampler is needed to measure depth for $300 to $1,500 orders.
- Exchange fee schedules on Coinbase or Kraken, which add to the half-spread on every side.
- Behavior during sudden price jumps, when spreads widen beyond the regular 4-day quote sample.

## Files

- Measurement scripts and raw JSON outputs: kept outside the repo in the rig folder (measure_crypto_alpaca.py, measure_crypto_external.py, crypto_small_alpaca.json, crypto_small_external.json).
- Page generator script: kept outside the repo in the rig folder (gen_doc_42_small_coins.py).
- Related order-book measurement on Kraken and Binance.US: `docs/research/24_order_book_costs.md`.

## What this changes for our queue

Decided by the builder, 2026-11-25 17:47 UTC.

- The fast lane is priced on the venue where these coins really trade. A second price store is being built from Coinbase one-minute candles, kept apart from the Alpaca tape and labeled by venue. Nothing from it goes into this repo, only counts and tables.
- The practice desk stays on Alpaca for stocks, funds and the largest coins. Small coins are not sent to it: a pretend fill there would not be believable.
- From the next crypto plan on, each coin is charged its own measured half-spread, not the flat `tm_crypto_half_spread_bps`. Plans TM01 and TM02 keep their results as scored, with the gap stated above.
- The five coins that passed on Alpaca (UNI, AAVE, DOT, ADA, BCH) are on the Alpaca tape and can be used by any later plan that names them.
