# 24. What it costs to cross the order book in small size

Status: research measurement. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Every number is MEASURED from public order books and placed here by `research_rig/build_doc24.py` from `research_rig/books_summary.json`.

## Why

Every replay charges the venue's fee plus a fixed slippage of 5 bps per side for bitcoin and ether, and replay 04 charges 25 bps for smaller coins. Those slippage numbers were assumptions. This checks them against live order books.

## What was done

- Once every two minutes from 2026-11-25 07:28:03 to 2026-11-25 08:02:03 UTC (18 rounds), the public order book was read for the 30 most traded US dollar pairs on Kraken and the 12 most traded on Binance.US.
- For each, the cost of buying or selling $100, $1,000 and $10,000 at once was worked out by walking down the book, in bps against the mid price. One side. Fees are not included.
- Only these summary costs were kept. The order books themselves were not stored.
- Rows for stablecoins and currencies are left out of the tables. 90 requests returned an error and are not counted.

## Bottom line

- Bitcoin on Kraken: $1,000 cost 0.0 bps in the middle case and 1.8 bps in the worst 5%. $10,000 cost 0.2 and 2.2 bps. Ether: 0.5 and 2.1 bps for $1,000.
- Bitcoin on Binance.US: $1,000 cost 0.8 bps in the middle case and 1.5 bps in the worst 5%. $10,000 cost 1.8 and 2.4 bps. Ether: 0.9 and 1.5 bps for $1,000.
- So on this night the 5 bps assumed for bitcoin and ether was higher than what the book charged at these sizes. The replays were not flattered by it.
- Smaller coins on Kraken: of 21 coins sampled, 8 cost more than 5 bps for $1,000 in their worst 5% of samples, and 1 cost more than 25 bps for $10,000.
- This is one night. Books are usually thinner in fast moves, which is when trend rules trade. That is STATED from general knowledge and not measured here. Treat these numbers as a floor, not an average.

## Kraken

| Coin | Samples | Quoted spread, middle | $100, middle | $1,000, middle | $1,000, worst 5% | $10,000, middle | $10,000, worst 5% | $10,000, worst seen |
|---|---|---|---|---|---|---|---|---|
| BTC | 18 | 0.0 | 0.0 | 0.0 | 1.8 | 0.2 | 2.2 | 3.1 |
| ETH | 18 | 0.7 | 0.5 | 0.5 | 2.1 | 0.7 | 2.3 | 3.2 |
| SOL | 18 | 1.5 | 0.7 | 0.7 | 3.2 | 0.8 | 4.2 | 5.4 |
| XRP | 18 | 0.5 | 0.3 | 0.5 | 0.9 | 0.9 | 2.1 | 5.0 |
| TRX | 18 | 1.4 | 0.7 | 0.8 | 1.3 | 1.6 | 2.6 | 3.3 |
| LINK | 18 | 3.5 | 1.8 | 1.8 | 4.2 | 2.7 | 5.8 | 10.3 |
| DOGE | 18 | 1.0 | 0.5 | 0.5 | 3.0 | 3.0 | 4.9 | 6.5 |
| SUI | 18 | 3.1 | 1.6 | 1.6 | 3.0 | 3.1 | 5.2 | 6.5 |
| BNB | 18 | 2.3 | 1.2 | 1.3 | 3.2 | 3.5 | 6.1 | 13.6 |
| HYPE | 18 | 3.4 | 1.7 | 1.7 | 3.2 | 3.6 | 5.6 | 5.7 |
| ADA | 18 | 3.8 | 1.9 | 2.3 | 3.6 | 4.0 | 5.0 | 5.4 |
| ZEC | 18 | 5.1 | 2.6 | 2.9 | 5.1 | 4.1 | 7.3 | 9.8 |
| XLM | 18 | 3.5 | 1.9 | 2.4 | 3.6 | 4.3 | 6.8 | 7.3 |
| LTC | 18 | 5.0 | 2.5 | 2.5 | 4.7 | 4.5 | 6.8 | 7.4 |
| AVAX | 18 | 4.7 | 2.3 | 2.7 | 4.7 | 4.6 | 6.6 | 8.2 |
| NEAR | 18 | 4.1 | 2.1 | 2.8 | 4.5 | 5.2 | 8.0 | 10.1 |
| TAO | 18 | 7.9 | 3.9 | 4.0 | 5.5 | 5.3 | 7.9 | 10.9 |
| UNI | 18 | 5.7 | 3.0 | 3.8 | 6.2 | 5.4 | 9.6 | 12.9 |
| XMR | 18 | 8.5 | 4.2 | 4.4 | 7.3 | 6.0 | 10.8 | 13.9 |
| QNT | 18 | 4.9 | 2.9 | 3.2 | 6.1 | 7.9 | 10.6 | 13.7 |
| VVV | 18 | 8.9 | 4.5 | 5.4 | 7.6 | 10.6 | 15.0 | 16.0 |
| PEPE | 18 | 5.8 | 3.2 | 4.3 | 8.5 | 10.7 | 19.8 | 26.5 |
| MON | 18 | 19.1 | 9.6 | 16.1 | 26.6 | 29.7 | 43.0 | 48.6 |

## Binance.US

| Coin | Samples | Quoted spread, middle | $100, middle | $1,000, middle | $1,000, worst 5% | $10,000, middle | $10,000, worst 5% | $10,000, worst seen |
|---|---|---|---|---|---|---|---|---|
| BTC (vs USDT) | 18 | 0.1 | 0.1 | 0.7 | 1.9 | 1.2 | 3.3 | 4.0 |
| ETH (vs USDT) | 18 | 0.5 | 0.3 | 0.7 | 1.8 | 1.7 | 5.1 | 7.2 |
| BTC | 18 | 0.1 | 0.3 | 0.8 | 1.5 | 1.8 | 2.4 | 4.5 |
| ETH | 18 | 0.6 | 0.7 | 0.9 | 1.5 | 1.9 | 4.4 | 7.2 |
| ZEC (vs USDT) | 18 | 3.0 | 3.2 | 3.8 | 6.4 | 7.0 | 12.2 | 14.0 |
| ADA (vs USDT) | 18 | 4.9 | 4.2 | 4.6 | 16.6 | 20.5 | 89.2 | 101.4 |

## What this does not show

- A stressed market. Whether the sample window was calm or not was not measured.
- Hidden costs of a market order that arrives a moment late, or of a book that changes between the read and the trade.
- Coins outside the most traded 30. The wide basket in replay 04 reaches further down the list, where books are thinner.
- Whether a resting limit order would be filled. That needs trade-by-trade data and is not tested.

## Files

- Sampler and raw samples: outside the repo. Summary: `research_rig/books_summary.py`, `research_rig/books_summary.json`
