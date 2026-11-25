# Sensitivity S1 to pre-registration 01: what if the fill is late

Written 2026-11-25 06:54 UTC, after replay 01 was run and read, before this check was run. Research rig, not the product.

## Why

Crypto trades around the clock. On Bitstamp daily bars the open of day t+1 is the same moment as the close of day t. So replay 01 lets a rule see the close and trade at that same price. A real program needs time to fetch the bar, decide and send the order. This check measures how much that flatters the result.

## What is run

The same 18 single-asset trials as replay 01. Same data, dates, costs and code. Only the fill price changes.

| Variant | Fill price |
|---|---|
| Base | Open of the daily bar of day t+1 (as in replay 01) |
| One hour late | Open of the Bitstamp hourly bar that starts at 01:00 UTC on day t+1. If that hour is missing, the next hour that exists that day, else the daily open |
| One day late | Open of the daily bar of day t+2 |

Reported at Alpaca cost (30 bps a side) and Binance.US cost (7 bps a side): Sharpe ratio, yearly growth and largest drop, whole sample and held-back slice.

## Rules of the check

- No new rules and no new trials. The trial count stays 20.
- No pass mark. It cannot turn a fail into a pass. If the one-hour-late result is worse, the worse number is the one to carry forward.
- Seed and everything else as in PREREG_01.
