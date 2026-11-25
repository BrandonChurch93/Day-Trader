# 24. What it costs to cross the order book in small size

Status: research measurement. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Every number is MEASURED from public order books and placed here by `research_rig/build_doc24.py` from `research_rig/books_summary.json`.

## Why

Every replay charges the venue's fee plus a fixed slippage of 5 bps per side for bitcoin and ether, and replay 04 charges 25 bps for smaller coins. Those slippage numbers were assumptions. This checks them against live order books.

## What was done

- Once every two minutes from 2026-11-25 07:28:03 to 2026-11-25 16:27:34 UTC (254 rounds), the public order book was read for the 30 most traded US dollar pairs on Kraken and the 12 most traded on Binance.US.
- For each, the cost of buying or selling $100, $1,000 and $10,000 at once was worked out by walking down the book, in bps against the mid price. One side. Fees are not included.
- Only these summary costs were kept. The order books themselves were not stored.
- Rows for stablecoins and currencies are left out of the tables. 1270 requests returned an error and are not counted.

## Bottom line

- Bitcoin on Kraken: $1,000 cost 0.0 bps in the middle case and 2.1 bps in the worst 5%. $10,000 cost 0.5 and 2.7 bps. Ether: 0.5 and 2.5 bps for $1,000.
- Bitcoin on Binance.US: $1,000 cost 0.8 bps in the middle case and 1.4 bps in the worst 5%. $10,000 cost 1.6 and 2.8 bps. Ether: 0.8 and 1.7 bps for $1,000.
- So in this sample the 5 bps assumed for bitcoin and ether was higher than what the book charged at these sizes. The replays were not flattered by it.
- Smaller coins on Kraken: of 21 coins sampled, 8 cost more than 5 bps for $1,000 in their worst 5% of samples, and 1 cost more than 25 bps for $10,000.
- This is one sample: 254 rounds over 9.0 hours on one day. The sampler stopped by itself and this is the whole sample. Bitcoin on Kraken has 508 readings, counting the buy side and the sell side, so its worst 5% figures rest on about 25 of them. Books are usually thinner in fast moves, which is when trend rules trade. That is STATED from general knowledge and not measured here. Treat these numbers as a floor, not an average.

## Kraken

| Coin | Samples | Quoted spread, middle | $100, middle | $1,000, middle | $1,000, worst 5% | $10,000, middle | $10,000, worst 5% | $10,000, worst seen |
|---|---|---|---|---|---|---|---|---|
| BTC | 254 | 0.0 | 0.0 | 0.0 | 2.1 | 0.5 | 2.7 | 5.4 |
| ETH | 254 | 0.2 | 0.4 | 0.5 | 2.5 | 0.8 | 2.7 | 7.3 |
| XRP | 254 | 1.3 | 0.7 | 0.8 | 2.4 | 1.4 | 3.6 | 13.2 |
| SOL | 254 | 1.5 | 0.7 | 0.7 | 2.2 | 1.5 | 3.3 | 13.0 |
| TRX | 254 | 1.4 | 0.7 | 0.8 | 2.2 | 1.9 | 4.0 | 6.4 |
| LINK | 254 | 4.0 | 2.1 | 2.2 | 4.2 | 2.8 | 5.4 | 10.3 |
| DOGE | 254 | 2.8 | 1.4 | 1.8 | 3.9 | 3.3 | 5.6 | 9.2 |
| SUI | 254 | 3.2 | 1.6 | 1.6 | 3.0 | 3.5 | 5.5 | 13.3 |
| BNB | 254 | 2.8 | 1.5 | 1.5 | 3.2 | 3.5 | 5.7 | 13.9 |
| HYPE | 254 | 1.8 | 1.7 | 2.1 | 4.2 | 3.8 | 6.1 | 13.5 |
| ADA | 254 | 4.1 | 2.1 | 2.5 | 4.6 | 4.1 | 6.8 | 19.3 |
| XLM | 254 | 3.8 | 2.1 | 2.6 | 4.6 | 4.3 | 7.3 | 12.7 |
| LTC | 254 | 2.5 | 2.5 | 2.5 | 4.7 | 4.3 | 6.8 | 9.3 |
| AVAX | 254 | 4.7 | 2.3 | 2.4 | 4.4 | 4.4 | 7.0 | 18.3 |
| ZEC | 254 | 4.8 | 2.5 | 2.7 | 6.5 | 4.6 | 9.6 | 18.8 |
| NEAR | 254 | 5.0 | 2.5 | 3.2 | 4.8 | 5.0 | 7.7 | 16.3 |
| UNI | 254 | 5.6 | 2.9 | 3.4 | 6.1 | 5.3 | 8.8 | 16.6 |
| TAO | 254 | 7.2 | 3.7 | 4.0 | 6.6 | 5.4 | 8.9 | 19.5 |
| XMR | 254 | 9.0 | 4.6 | 4.8 | 9.9 | 6.4 | 12.1 | 36.8 |
| QNT | 254 | 6.5 | 3.7 | 4.2 | 8.3 | 9.4 | 15.7 | 28.9 |
| PEPE | 254 | 8.7 | 4.4 | 5.2 | 11.3 | 11.3 | 23.4 | 40.8 |
| VVV | 254 | 9.2 | 4.7 | 6.0 | 11.5 | 12.2 | 20.0 | 34.4 |
| MON | 254 | 19.4 | 10.1 | 16.4 | 28.1 | 32.6 | 48.4 | 94.2 |

## Binance.US

| Coin | Samples | Quoted spread, middle | $100, middle | $1,000, middle | $1,000, worst 5% | $10,000, middle | $10,000, worst 5% | $10,000, worst seen |
|---|---|---|---|---|---|---|---|---|
| BTC (vs USDT) | 254 | 0.0 | 0.0 | 0.5 | 1.7 | 1.3 | 3.6 | 9.2 |
| BTC | 254 | 0.0 | 0.2 | 0.8 | 1.4 | 1.6 | 2.8 | 6.7 |
| ETH (vs USDT) | 254 | 0.6 | 0.3 | 0.8 | 1.9 | 1.6 | 4.9 | 9.2 |
| ETH | 254 | 0.4 | 0.7 | 0.8 | 1.7 | 1.8 | 4.9 | 9.5 |
| ZEC (vs USDT) | 254 | 2.9 | 3.2 | 3.7 | 6.6 | 5.7 | 11.2 | 17.7 |
| ADA (vs USDT) | 254 | 5.0 | 3.5 | 3.8 | 21.7 | 15.7 | 88.4 | 271.1 |

## What this does not show

- A stressed market. Whether the sample window was calm or not was not measured.
- Hidden costs of a market order that arrives a moment late, or of a book that changes between the read and the trade.
- Coins outside the most traded 30. The wide basket in replay 04 reaches further down the list, where books are thinner.
- Whether a resting limit order would be filled. That needs trade-by-trade data and is not tested.

## Files

- Sampler and raw samples: outside the repo. Summary: `research_rig/books_summary.py`, `research_rig/books_summary.json`
