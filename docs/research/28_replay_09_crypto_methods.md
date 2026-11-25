# Replay 09: new crypto methods on Alpaca

MEASURED. 0 of 7 rules passed all marks. Pass: none. Fail: ASIA, WKND, MOM, REV, LEAD, VOL, CAP. In the held-back slice, 1 rule made money and 1 beat holding bitcoin. The best net growth was +2.13% (CAP), versus +1.73% for bitcoin. That rule closed 1 trade. These are replay figures, not returns from a real account.

## What ran

- STATED. The [frozen plan](../../research_rig/PREREG_09_crypto_methods.md) was pushed in commit `74ad30c`. Development ran 2024-01-01 through 2026-06-30. Held back ran 2026-07-01 through 2026-11-24 (`replay_09_dates`, inclusive UTC days). Each slice restarted with cash. Prior market episodes were already visible in earlier research; the replay was held back for these rule versions, not a blind forward test.
- STATED. The modeled cost was 25 bps [Alpaca entry-tier taker fee](https://docs.alpaca.markets/us/docs/crypto-fees) (`practice_crypto_fee_bps_added`) plus 10 bps assumed adverse fill (`tm_crypto_half_spread_bps`) per side, 35 bps nominal on each buy or sell. The fee is taken from the received asset. Bitcoin buy-and-hold paid to buy and was marked without a closing sale. There were no maker, price impact, minimum-order, queue, partial-fill or tax assumptions.
- MEASURED. Rules used hourly and daily bars from the [Alpaca US market data API](https://data.alpaca.markets/v1beta3/crypto/us/bars). The fixed candidate set was AVAX, BTC, DOGE, ETH, LINK, LTC, SOL, XRP (`replay_09_basket`). The test did not include other pairs, dead coins, or more venues.

## Held-back results at modeled Alpaca cost

Net growth is for the slice, not annualized. Largest drop and Sharpe use daily closing equity, not intraday lows. The random twin uses the same symbols, weights, durations and number of filled sides, with the timing moved. UNKNOWN means the exact match could not be constructed.

| Rule | Net growth | Largest drop | Sharpe | Filled sides | Missed entries | Delayed sales | Still open | Random twin net growth |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HOLD BTC | +1.73% | -32.08% | 0.304 | 1 | n/a | n/a | 1 | n/a |
| ASIA | -65.14% | -65.32% | -11.567 | 294 | 0 | 0 | 0 | -65.65% |
| WKND | -6.80% | -12.75% | -1.205 | 42 | 0 | 0 | 0 | -15.19% |
| MOM | -31.01% | -44.69% | -1.360 | 40 | 0 | 1 | 0 | -47.74% |
| REV | -68.77% | -71.00% | -4.881 | 292 | 1 | 3 | 0 | -62.86% |
| LEAD | -0.80% | -0.80% | -1.576 | 2 | 0 | 0 | 0 | -0.23% |
| VOL | -16.97% | -36.55% | -1.007 | 40 | 0 | 0 | 0 | -17.42% |
| CAP | +2.13% | +0.00% | 1.576 | 2 | 0 | 0 | 0 | -1.28% |

## Pass marks

MEASURED. Mark 3 counted 100 ledger rule trials (`replay_09_statistics.trial_count`). Mark 4 used the worst overfitting estimate across the frozen starts (`replay_09_dates.pbo_starts`): 2024-01-01: 0.149, 2025-01-01: 0.380, 2026-01-01: 0.189. The cap is 0.250 (`backtest_max_pbo`). Mark 2 is against holding bitcoin; zero denotes never ahead at zero friction. A whole-sample shuffle is UNKNOWN if either slice cannot be matched exactly; the held-only twin can still be reported. See the plan for the five keys, the daily-return spread proxy and exact rule definitions.

| Rule | Mark 1 held | Mark 2 cost | Mark 3 deflated Sharpe | Mark 4 overfit | Mark 5 shuffle | Result | Break-even bps | Deflated Sharpe | Matched draws beaten |
|---|---|---|---|---|---|---|---:|---:|---:|
| ASIA | fail | fail | fail | fail | fail | fail | 0.00 | 0.000 | 54.70% |
| WKND | fail | fail | fail | fail | fail | fail | 0.00 | 0.000 | 44.80% |
| MOM | fail | fail | fail | fail | fail | fail | 26.29 | 0.000 | UNKNOWN |
| REV | fail | fail | fail | fail | fail | fail | 0.00 | 0.000 | UNKNOWN |
| LEAD | fail | fail | fail | fail | fail | fail | 0.00 | 0.000 | 80.10% |
| VOL | fail | fail | fail | fail | fail | fail | 0.00 | 0.000 | UNKNOWN |
| CAP | pass | fail | fail | fail | fail | fail | 0.00 | 0.000 | 82.20% |

## Data coverage

MEASURED. The coverage check lists every USD pair named on [Alpaca's published pair list](https://alpaca.markets/support/what-cryptocurrencies-does-alpaca-currently-support), 36 pairs in total. Internal gaps exclude time outside each file's first and last timestamps. The [historical bars API](https://docs.alpaca.markets/us/reference/cryptobars-1) can paginate before the requested row limit. Where the full hourly pull was not ready, the table shows replay-window coverage or marks the download as not yet available. Neither means prices did not exist. A recent pass means that each of the last 30 days was present and median daily dollar volume was at least 10,000 USD (`replay_09_liquidity`). It does not prove the market was liquid enough to fill any order. No other venue's feed was added. These are the public API's bars, not a complete historical catalog of every pair ever listed.

| Symbol | Hourly query | First hourly bar UTC | Last hourly bar UTC | Hourly bars | Hours missing inside range | Longest gap, hours | Zero-volume hours | First daily bar UTC | Daily bars | Days missing inside range | Zero-volume days | Recent liquidity screen |
|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| AAVE/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2021-07-15 00:00:00 | 1959 | 0 | 35 | no |
| ADA/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-13 00:00:00 | 285 | 0 | 8 | no |
| ARB/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-16 00:00:00 | 282 | 0 | 17 | no |
| AVAX/USD | replay window only | 2023-12-01 00:00:00 | 2026-11-24 23:00:00 | 26156 | 4 | 2 | 10356 | 2021-11-18 00:00:00 | 1833 | 0 | 33 | no |
| BAT/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2021-01-01 00:00:00 | 2154 | 0 | 52 | no |
| BCH/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2021-01-01 00:00:00 | 2154 | 0 | 15 | no |
| BONK/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-16 00:00:00 | 282 | 0 | 18 | no |
| BTC/USD | replay window only | 2023-12-01 00:00:00 | 2026-11-24 23:00:00 | 26156 | 4 | 2 | 732 | 2021-01-01 00:00:00 | 2154 | 0 | 0 | yes |
| CRV/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2023-08-18 00:00:00 | 1195 | 0 | 58 | no |
| DOGE/USD | replay window only | 2023-12-01 00:00:00 | 2026-11-24 23:00:00 | 26153 | 7 | 3 | 7364 | 2021-01-01 00:00:00 | 2154 | 0 | 2 | no |
| DOT/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2023-08-18 00:00:00 | 1195 | 0 | 28 | no |
| ETH/USD | replay window only | 2023-12-01 00:00:00 | 2026-11-24 23:00:00 | 26156 | 4 | 2 | 2244 | 2021-01-01 00:00:00 | 2154 | 0 | 0 | yes |
| FIL/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-16 00:00:00 | 282 | 0 | 16 | no |
| GRT/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2021-07-15 00:00:00 | 1959 | 0 | 10 | no |
| HYPE/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-17 00:00:00 | 281 | 0 | 16 | no |
| LDO/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-17 00:00:00 | 281 | 0 | 46 | no |
| LINK/USD | replay window only | 2023-12-01 00:00:00 | 2026-11-24 23:00:00 | 26151 | 9 | 2 | 10404 | 2021-01-01 00:00:00 | 2154 | 0 | 5 | no |
| LTC/USD | replay window only | 2023-12-01 00:00:00 | 2026-11-24 23:00:00 | 26156 | 4 | 2 | 12579 | 2021-01-01 00:00:00 | 2154 | 0 | 5 | no |
| ONDO/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-17 00:00:00 | 281 | 0 | 18 | no |
| PAXG/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2021-01-01 00:00:00 | 1183 | 971 | 8 | no |
| PEPE/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2025-01-29 00:00:00 | 665 | 0 | 36 | no |
| POL/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-19 00:00:00 | 279 | 0 | 52 | no |
| RENDER/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-19 00:00:00 | 279 | 0 | 18 | no |
| SHIB/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2023-03-14 00:00:00 | 1352 | 0 | 41 | no |
| SKY/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2025-09-27 00:00:00 | 424 | 0 | 51 | no |
| SOL/USD | replay window only | 2024-08-26 16:00:00 | 2026-11-24 23:00:00 | 19681 | 7 | 2 | 3126 | 2021-01-01 00:00:00 | 1736 | 418 | 11 | yes |
| SUSHI/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2021-07-23 00:00:00 | 1951 | 0 | 212 | no |
| TRUMP/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2025-01-22 00:00:00 | 672 | 0 | 91 | no |
| UNI/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2021-01-01 00:00:00 | 2154 | 0 | 126 | no |
| USDC/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2023-08-18 00:00:00 | 1191 | 4 | 213 | yes |
| USDG/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2025-05-19 00:00:00 | 457 | 98 | 178 | yes |
| USDT/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2021-01-01 00:00:00 | 2153 | 1 | 38 | yes |
| WIF/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2026-02-19 00:00:00 | 279 | 0 | 47 | no |
| XRP/USD | replay window only | 2024-01-01 06:00:00 | 2026-11-24 23:00:00 | 25373 | 37 | 28 | 976 | 2024-01-01 00:00:00 | 1059 | 0 | 0 | yes |
| XTZ/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2023-08-18 00:00:00 | 1195 | 0 | 81 | no |
| YFI/USD | not yet downloaded | n/a | n/a | n/a | n/a | n/a | n/a | 2021-12-02 00:00:00 | 1819 | 0 | 448 | no |

MEASURED. The recorded tape was checked separately and not used for fills. Missing counts below are inside each recorded minute span, so they do not count time outside its endpoints.

| Symbol | First minute UTC | Last minute UTC | Recorded minutes | Internal missing minutes | Zero-volume minutes |
|---|---|---|---:|---:|---:|
| AVAX/USD | 2026-01-01T00:00:00+00:00 | 2026-11-24T23:59:00+00:00 | 348517 | 123803 | 329816 |
| BTC/USD | 2026-01-01T00:00:00+00:00 | 2026-11-24T23:59:00+00:00 | 458938 | 13382 | 299517 |
| DOGE/USD | 2026-01-01T00:01:00+00:00 | 2026-11-24T23:59:00+00:00 | 343346 | 128973 | 327546 |
| ETH/USD | 2026-01-01T00:01:00+00:00 | 2026-11-24T23:59:00+00:00 | 329847 | 142472 | 252797 |
| LINK/USD | 2026-01-01T00:00:00+00:00 | 2026-11-24T23:59:00+00:00 | 348765 | 123555 | 329233 |
| LTC/USD | 2026-01-01T00:00:00+00:00 | 2026-11-24T23:59:00+00:00 | 318813 | 153507 | 307830 |
| SOL/USD | 2026-01-01T00:02:00+00:00 | 2026-11-24T23:59:00+00:00 | 351555 | 120763 | 296875 |
| XRP/USD | 2026-01-01T00:00:00+00:00 | 2026-11-24T23:59:00+00:00 | 335540 | 136780 | 271263 |

## What is still unknown

- UNKNOWN. Live fills, actual spreads, depth, latency, adverse selection and venue size limits. A zero-volume bar may show quote marks ([Alpaca crypto bar notes](https://docs.alpaca.markets/us/docs/real-time-crypto-pricing-data)) but cannot fill an order here. Even on a bar with volume, the opening mark is only a proxy for a contemporaneous executable quote.
- UNKNOWN. Whether any calendar effect or ranking signal persists in a truly unseen market. The pair shortlist is based on markets known now, and the held-back span is short. A smaller loss than BTC is not positive net growth.
- Next test: preregister one resting-limit rule, using timestamped Alpaca trades and quotes rather than highs and lows. Require an actual trade beyond the resting limit, then compare it with small paper orders for a fill-rate check.

Built by `research_rig/build_doc28.py` from `research_rig/results_09.json`. The result stores the command, code fingerprints and fingerprints of each input bar file. Raw prices stay off the repo.
