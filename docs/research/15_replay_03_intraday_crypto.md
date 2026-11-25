# Replay 03: rules that trade inside the day, on hourly bitcoin and ether bars

Run on 2026-11-25 (UTC), the night of 2026-11-24 in Idaho. Uses the research rig in `research_rig/`.

Status: research evidence. Proposed by research. Nothing in this file is an owner decision. No account, key or order was involved.

Tags: every result number here is MEASURED by our own rig from Bitstamp's public hourly price bars. That means "our code worked this out from that data". It does not mean "this will happen with real money".

## The question

Replay 01 tested rules that hold for days or weeks. This one tests day trading itself: does any plain rule that gets in and out inside one day, on spot bitcoin and ether, make money after the fees a US retail account really pays?

## Bottom line

- No. Of 16 rule and coin pairs, 0 passed at Binance.US cost, 0 at Alpaca cost, and 0 at Kraken or Coinbase cost.
- At Alpaca cost and above, every rule lost money, and most lost nearly everything. The primary rule on bitcoin went from +40.8% a year before costs to -53.9% a year after them.
- The patterns show up before costs. Seven of the eight rules made money before costs on both coins. The average gain per round trip, before costs, was between +0.1 and +36.3 bps.
- The cost is larger than the pattern. One buy and one sell costs 60 bps at Alpaca. The best rule's average gain per round trip was 36.3 bps.
- Break-even cost per side ran from 0.0 to 15.4 bps. Only Binance.US, at 7 bps per side, is under the better rules' break-even, and not by the margin the project requires (`backtest_min_breakeven_cost_multiple`).
- At Binance.US cost, 9 of 16 made some money over the whole sample, and none passed. They made less than holding, and they fail the check for luck (mark 3).
- This matches what research expected and wrote down before the run. It is in line with the one published study we hold, which research read as putting break-even cost near 10 bps ([University of Reading manuscript](https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf)). The patterns exist, and a retail fee eats them.

## Words used below

The same words as `docs/research/12_replay_01_crypto_trend.md`. Two more:

| Word | Meaning |
|---|---|
| Round trip | One buy and the sell that closes it |
| Day open | The price at 00:00 UTC. Crypto never closes, so the day is a choice |

## What was fixed before the run

The full text is `research_rig/PREREG_03_intraday_crypto.md`. It was pushed to the repo in commit d91ebba before any of these rules was run.

| Item | Fixed value |
|---|---|
| Data | Bitstamp hourly bars. Bitcoin test starts 2016-01-01, ether 2019-01-01, set by a data-only rule (under 1% of hours empty in every later year, and 4,800 hours of warm-up) |
| Fills | Signal on the close of one hourly bar, fill at the open of the next |
| Cost per side | Venue taker fee plus 5 bps: Binance.US 7, Alpaca 30, Kraken $10,000 tier 43, Kraken entry 85, Coinbase entry 95 |
| Rules | 8 per coin, 16 trials, numbers 27 to 42 in the trial ledger |
| Slices | Development to 2022-12-31. Held back 2023-01-01 to 2026-06-30. After the designer's knowledge cutoff 2026-07-01 to 2026-11-24 |
| Pass marks | The same five as replay 01, with 36 trials counted |

The rules:

| Id | Rule |
|---|---|
| H1 | Half-day momentum, the primary rule. At 12:00 UTC, if price is above the day open, buy. Sell at day end |
| H2 | Opening range breakout. Buy after the first hourly close above the high of the first four hours. Sell at day end |
| H3 | Last hour timing. If the first hour was up and the 22:00 hour was up, hold for the last hour only |
| H4 | Buy the dip. After an hourly fall of more than 2 standard deviations, buy and hold four hours |
| H5 | H4, only when price is above its 200 day average |
| H6 | Hourly trend with no day-end exit. Not strictly day trading |
| H7 | H1, only on days when the daily trend weight from replay 01 is 0.5 or more |
| H8 | Noise band. Buy when price moves above the day open by more than its usual move for that hour. Sell if it falls back under the day open, or at day end |

## Before costs: are the patterns there

Bitcoin, whole sample:

| Rule | Time invested | Round trips a year | Hours held | Average gain per round trip, before costs (bps) | Round trips that gained | Growth a year before costs | Break-even cost per side (bps) |
|---|---|---|---|---|---|---|---|
| H1 Half-day momentum (primary) | 26% | 186 | 12.0 | +21.5 | 55% | +40.8% | 9.2 |
| H2 Opening range breakout | 35% | 224 | 13.5 | +20.2 | 52% | +45.7% | 8.4 |
| H3 Last hour timing | 1% | 93 | 1.0 | +0.1 | 49% | -0.1% | 0.0 |
| H4 Buy the dip | 10% | 187 | 4.7 | +12.5 | 57% | +21.6% | 5.2 |
| H5 Buy the dip in an uptrend | 6% | 114 | 4.7 | +18.2 | 59% | +20.4% | 8.1 |
| H6 Hourly trend, no day-end exit | 31% | 287 | 9.6 | +16.0 | 25% | +46.7% | 6.7 |
| H7 Half-day momentum, uptrend days only | 17% | 122 | 12.0 | +31.2 | 56% | +40.9% | 14.1 |
| H8 Noise band | 25% | 181 | 12.1 | +20.1 | 43% | +35.6% | 8.4 |

Ether, whole sample:

| Rule | Time invested | Round trips a year | Hours held | Average gain per round trip, before costs (bps) | Round trips that gained | Growth a year before costs | Break-even cost per side (bps) |
|---|---|---|---|---|---|---|---|
| H1 Half-day momentum (primary) | 25% | 185 | 12.0 | +27.9 | 52% | +52.3% | 11.4 |
| H2 Opening range breakout | 34% | 218 | 13.5 | +32.2 | 52% | +80.2% | 13.5 |
| H3 Last hour timing | 1% | 93 | 1.0 | +0.2 | 49% | -0.3% | 0.0 |
| H4 Buy the dip | 10% | 188 | 4.6 | +6.5 | 56% | +8.0% | 2.0 |
| H5 Buy the dip in an uptrend | 5% | 104 | 4.6 | +14.7 | 57% | +13.7% | 6.2 |
| H6 Hourly trend, no day-end exit | 29% | 275 | 9.3 | +13.9 | 24% | +32.9% | 5.2 |
| H7 Half-day momentum, uptrend days only | 16% | 117 | 12.0 | +36.3 | 53% | +43.3% | 15.4 |
| H8 Noise band | 26% | 184 | 12.6 | +31.1 | 43% | +61.2% | 13.0 |

Break-even cost per side is the cost at which the rule's growth falls to zero.

## After costs: growth a year, whole sample

Bitcoin:

| Rule | Binance.US (7 bps) | Alpaca (30 bps) | Kraken $10k tier (43 bps) | Kraken entry (85 bps) | Coinbase entry (95 bps) |
|---|---|---|---|---|---|
| Hold the coin | +57.1% | +57.1% | +57.1% | +57.1% | +57.1% |
| H1 | +8.5% | -53.9% | -71.6% | -94.1% | -95.9% |
| H2 | +6.5% | -62.0% | -78.8% | -96.8% | -97.9% |
| H3 | -12.3% | -42.7% | -54.9% | -79.3% | -82.8% |
| H4 | -6.4% | -60.4% | -75.6% | -94.9% | -96.5% |
| H5 | +2.6% | -39.4% | -55.0% | -82.8% | -86.3% |
| H6 | -1.7% | -73.7% | -87.5% | -98.9% | -99.4% |
| H7 | +18.8% | -32.2% | -50.6% | -82.3% | -86.1% |
| H8 | +5.2% | -54.3% | -71.4% | -93.8% | -95.7% |
| C1 control: always hold 12:00 to 24:00 | -15.4% | -84.2% | -93.9% | -99.7% | -99.9% |

Ether:

| Rule | Binance.US (7 bps) | Alpaca (30 bps) | Kraken $10k tier (43 bps) | Kraken entry (85 bps) | Coinbase entry (95 bps) |
|---|---|---|---|---|---|
| Hold the coin | +37.0% | +37.0% | +37.0% | +37.0% | +37.0% |
| H1 | +17.5% | -49.9% | -69.0% | -93.5% | -95.5% |
| H2 | +32.8% | -51.3% | -72.4% | -95.6% | -97.1% |
| H3 | -12.5% | -42.9% | -55.1% | -79.4% | -82.9% |
| H4 | -17.1% | -65.1% | -78.6% | -95.6% | -97.0% |
| H5 | -1.7% | -39.0% | -53.4% | -80.5% | -84.1% |
| H6 | -9.6% | -74.5% | -87.5% | -98.8% | -99.3% |
| H7 | +21.7% | -28.8% | -47.4% | -80.2% | -84.3% |
| H8 | +24.6% | -46.4% | -66.7% | -92.9% | -95.1% |
| C1 control: always hold 12:00 to 24:00 | -9.7% | -83.1% | -93.5% | -99.7% | -99.9% |

The control C1 buys every day at 12:00 UTC and sells at day end, with no signal. It shows what paying the fee once a day does on its own.

## The held-back years, 2023-01-01 to 2026-06-30

At Binance.US cost, bitcoin:

| Rule | Growth a year | Sharpe | Largest drop | Made money |
|---|---|---|---|---|
| Hold the coin | +43.4% | 1.00 | -53.1% | yes |
| H1 | -16.7% | -0.55 | -60.9% | no |
| H2 | -10.8% | -0.24 | -66.9% | no |
| H3 | -13.6% | -3.63 | -41.3% | no |
| H4 | -22.6% | -1.31 | -66.2% | no |
| H5 | -12.5% | -0.92 | -40.9% | no |
| H6 | -22.4% | -0.77 | -72.3% | no |
| H7 | -4.2% | -0.10 | -47.7% | no |
| H8 | -8.5% | -0.20 | -52.7% | no |

At Binance.US cost, ether:

| Rule | Growth a year | Sharpe | Largest drop | Made money |
|---|---|---|---|---|
| Hold the coin | +8.0% | 0.44 | -67.6% | yes |
| H1 | -19.7% | -0.38 | -65.2% | no |
| H2 | -0.8% | 0.18 | -47.3% | no |
| H3 | -13.5% | -2.73 | -42.0% | no |
| H4 | -24.3% | -1.00 | -71.8% | no |
| H5 | -7.9% | -0.43 | -38.3% | no |
| H6 | -23.7% | -0.59 | -66.5% | no |
| H7 | +9.1% | 0.44 | -34.7% | yes |
| H8 | +6.2% | 0.34 | -40.0% | yes |

At Alpaca cost, bitcoin:

| Rule | Growth a year | Sharpe | Largest drop | Made money |
|---|---|---|---|---|
| Hold the coin | +43.4% | 1.00 | -53.1% | yes |
| H1 | -64.8% | -3.79 | -97.5% | no |
| H2 | -69.0% | -3.79 | -98.4% | no |
| H3 | -42.8% | -10.62 | -85.8% | no |
| H4 | -68.4% | -5.86 | -98.3% | no |
| H5 | -51.5% | -4.82 | -92.2% | no |
| H6 | -78.2% | -4.58 | -99.6% | no |
| H7 | -45.8% | -2.80 | -89.1% | no |
| H8 | -61.5% | -3.27 | -96.7% | no |

At Alpaca cost, ether:

| Rule | Growth a year | Sharpe | Largest drop | Made money |
|---|---|---|---|---|
| Hold the coin | +8.0% | 0.44 | -67.6% | yes |
| H1 | -67.4% | -2.71 | -98.1% | no |
| H2 | -64.1% | -2.32 | -97.3% | no |
| H3 | -44.5% | -9.22 | -87.3% | no |
| H4 | -68.6% | -4.43 | -98.3% | no |
| H5 | -42.9% | -3.26 | -85.9% | no |
| H6 | -77.3% | -3.58 | -99.5% | no |
| H7 | -35.7% | -1.34 | -79.8% | no |
| H8 | -55.7% | -2.03 | -94.4% | no |

## Pass marks

| Venue | Cost per side (bps) | Rules that passed all five marks, of 16 | Rules that made any money, whole sample | Rules that made any money, held-back years |
|---|---|---|---|---|
| Binance.US | 7 | 0 | 9 | 2 |
| Alpaca | 30 | 0 | 0 | 0 |
| Kraken $10k tier | 43 | 0 | 0 | 0 |
| Kraken entry | 85 | 0 | 0 | 0 |
| Coinbase entry | 95 | 0 | 0 | 0 |

Every mark for every rule at Binance.US cost, the only venue where anything came close:

| Coin | Rule | Mark 1 held-back | Mark 2 break-even | Mark 3 deflated Sharpe | Mark 4 overfitting | Mark 5 shuffle | Result |
|---|---|---|---|---|---|---|---|
| Bitcoin | H1 | fail | fail (1.4 against 14 needed) | fail (0.00) | pass (0.23) | fail (0.85) | fail |
| Bitcoin | H2 | fail | fail (1.2 against 14 needed) | fail (0.00) | pass (0.23) | fail (0.73) | fail |
| Bitcoin | H3 | fail | fail (0.0 against 14 needed) | fail (0.00) | pass (0.23) | fail (0.00) | fail |
| Bitcoin | H4 | fail | fail (0.0 against 14 needed) | fail (0.00) | pass (0.23) | fail (0.79) | fail |
| Bitcoin | H5 | fail | fail (0.0 against 14 needed) | fail (0.00) | pass (0.23) | pass (0.96) | fail |
| Bitcoin | H6 | fail | fail (1.2 against 14 needed) | fail (0.00) | pass (0.23) | fail (0.67) | fail |
| Bitcoin | H7 | fail | fail (4.2 against 14 needed) | fail (0.00) | pass (0.23) | pass (0.99) | fail |
| Bitcoin | H8 | fail | fail (0.2 against 14 needed) | fail (0.00) | pass (0.23) | fail (0.78) | fail |
| Ether | H1 | fail | fail (4.6 against 14 needed) | fail (0.00) | pass (0.15) | pass (0.96) | fail |
| Ether | H2 | fail | fail (7.4 against 14 needed) | fail (0.00) | pass (0.15) | pass (0.99) | fail |
| Ether | H3 | fail | fail (0.0 against 14 needed) | fail (0.00) | pass (0.15) | fail (0.01) | fail |
| Ether | H4 | fail | fail (0.0 against 14 needed) | fail (0.00) | pass (0.15) | fail (0.34) | fail |
| Ether | H5 | fail | fail (0.0 against 14 needed) | fail (0.00) | pass (0.15) | fail (0.77) | fail |
| Ether | H6 | fail | fail (0.5 against 14 needed) | fail (0.00) | pass (0.15) | fail (0.49) | fail |
| Ether | H7 | pass | fail (6.2 against 14 needed) | fail (0.00) | pass (0.15) | pass (0.99) | fail |
| Ether | H8 | fail | fail (5.9 against 14 needed) | fail (0.00) | pass (0.15) | pass (0.97) | fail |

At Alpaca cost:

| Coin | Rule | Mark 1 held-back | Mark 2 break-even | Mark 3 deflated Sharpe | Mark 4 overfitting | Mark 5 shuffle | Result |
|---|---|---|---|---|---|---|---|
| Bitcoin | H1 | fail | fail (1.4 against 60 needed) | fail (0.00) | pass (0.03) | fail (0.00) | fail |
| Bitcoin | H2 | fail | fail (1.2 against 60 needed) | fail (0.00) | pass (0.03) | fail (0.00) | fail |
| Bitcoin | H3 | fail | fail (0.0 against 60 needed) | fail (0.00) | pass (0.03) | fail (0.00) | fail |
| Bitcoin | H4 | fail | fail (0.0 against 60 needed) | fail (0.00) | pass (0.03) | fail (0.01) | fail |
| Bitcoin | H5 | fail | fail (0.0 against 60 needed) | fail (0.00) | pass (0.03) | fail (0.21) | fail |
| Bitcoin | H6 | fail | fail (1.2 against 60 needed) | fail (0.00) | pass (0.03) | fail (0.00) | fail |
| Bitcoin | H7 | fail | fail (4.2 against 60 needed) | fail (0.00) | pass (0.03) | fail (0.11) | fail |
| Bitcoin | H8 | fail | fail (0.2 against 60 needed) | fail (0.00) | pass (0.03) | fail (0.00) | fail |
| Ether | H1 | fail | fail (4.6 against 60 needed) | fail (0.00) | pass (0.02) | fail (0.09) | fail |
| Ether | H2 | fail | fail (7.4 against 60 needed) | fail (0.00) | pass (0.02) | fail (0.10) | fail |
| Ether | H3 | fail | fail (0.0 against 60 needed) | fail (0.00) | pass (0.02) | fail (0.00) | fail |
| Ether | H4 | fail | fail (0.0 against 60 needed) | fail (0.00) | pass (0.02) | fail (0.00) | fail |
| Ether | H5 | fail | fail (0.0 against 60 needed) | fail (0.00) | pass (0.02) | fail (0.04) | fail |
| Ether | H6 | fail | fail (0.5 against 60 needed) | fail (0.00) | pass (0.02) | fail (0.00) | fail |
| Ether | H7 | fail | fail (6.2 against 60 needed) | fail (0.00) | pass (0.02) | fail (0.46) | fail |
| Ether | H8 | fail | fail (5.9 against 60 needed) | fail (0.00) | pass (0.02) | fail (0.24) | fail |

Notes on reading the marks:

- Mark 4 (overfitting) passes easily at the high-cost venues. That is not good news. It passes because the ranking of the rules is stable: they all lose, in the same order.
- Mark 3 (deflated Sharpe) is harsh here because 36 trials are counted and their results are spread wide. That is how it was set before the run.

## After the designer's knowledge cutoff, 2026-07-01 to 2026-11-24

Growth over the slice is stated as a yearly rate, so short-slice figures look large. Bitcoin:

| Rule | Binance.US (7 bps) | Alpaca (30 bps) | Kraken $10k tier (43 bps) | Kraken entry (85 bps) | Coinbase entry (95 bps) |
|---|---|---|---|---|---|
| Hold the coin | -0.9% | -0.9% | -0.9% | -0.9% | -0.9% |
| H1 | +1.5% | -57.9% | -74.4% | -94.9% | -96.5% |
| H2 | -36.4% | -80.0% | -89.6% | -98.7% | -99.2% |
| H3 | -12.3% | -38.2% | -49.3% | -73.3% | -77.1% |
| H4 | -31.3% | -68.9% | -80.2% | -95.3% | -96.7% |
| H5 | -19.0% | -48.9% | -60.6% | -83.0% | -86.1% |
| H6 | +6.5% | -56.6% | -73.8% | -94.9% | -96.6% |
| H7 | +18.1% | -33.5% | -52.0% | -83.2% | -86.9% |
| H8 | +0.4% | -53.0% | -69.4% | -92.3% | -94.5% |
| C1 control: always hold 12:00 to 24:00 | -46.9% | -90.1% | -96.2% | -99.8% | -99.9% |

Ether:

| Rule | Binance.US (7 bps) | Alpaca (30 bps) | Kraken $10k tier (43 bps) | Kraken entry (85 bps) | Coinbase entry (95 bps) |
|---|---|---|---|---|---|
| Hold the coin | +11.2% | +11.2% | +11.2% | +11.2% | +11.2% |
| H1 | +16.5% | -56.1% | -74.8% | -95.8% | -97.2% |
| H2 | -20.8% | -73.6% | -85.8% | -98.1% | -98.8% |
| H3 | -10.1% | -37.8% | -49.5% | -74.2% | -78.0% |
| H4 | -10.2% | -61.2% | -75.9% | -94.8% | -96.4% |
| H5 | -15.8% | -46.9% | -59.0% | -82.3% | -85.5% |
| H6 | +2.7% | -67.3% | -82.9% | -97.9% | -98.7% |
| H7 | +24.7% | -36.7% | -56.9% | -87.5% | -90.7% |
| H8 | +37.7% | -41.2% | -63.6% | -92.3% | -94.7% |
| C1 control: always hold 12:00 to 24:00 | -46.7% | -90.1% | -96.2% | -99.8% | -99.9% |

## What this does and does not show

- It shows that eight textbook day trading rules on the two most liquid coins do not survive the taker fees of the venues an Idaho account can use, except possibly Binance.US, where they still fail the pass marks.
- It does not show that no day trading rule can work. Eight rules is not every rule. A rule nobody has published could exist. The base rate in `docs/research/01_stock_daytrading_evidence.md` says most people who look do not find one.
- Limit orders were not tested. A limit order pays the lower maker fee, or none, but it only fills when the price comes to it, which is often when the trade is about to go wrong. The rig cannot model that from hourly bars. UNKNOWN.
- Hourly bars from one venue. A fill at the hourly open with 5 bps of slippage is an assumption.
- The held-back years were already used by replay 01 for daily rules.
- Stocks were not tested here. Stock day trading has no fee at Alpaca and much smaller spreads on the large funds, so the answer for stocks could differ. That needs minute data, which is a purchase (`docs/research/10_historical_data_and_practice.md`).
- The first run of the program stopped at the step that saves the results, before any result was read. The save step was fixed and the run repeated. No rule, cost or mark was changed.

## What research proposes from this

None of this is decided.

1. Do not day trade crypto at Alpaca, Kraken or Coinbase taker fees. Every rule tested lost money there, most of them nearly all of it.
2. Treat the fee as the first question for any fast rule. A rule needs an average gain per round trip of at least twice the round trip cost before it is worth a practice run. `intraday_trend_max_round_trip_bps` in the config already says this for stocks.
3. Keep H7 (half-day momentum on uptrend days only) on a watch list for Binance.US, not for practice trading. It had the highest break-even cost on both coins and it still failed.
4. Put the day trading question to stocks next, where the fee is zero, once minute data is bought. Write the plan down first.
5. Keep the slow trend rules from replay 01 as the only crypto idea still under test. They trade far less often (turnover figures are in `docs/research/12_replay_01_crypto_trend.md`). Their own weakness is in `docs/research/12b_replay_01_kraken_crosscheck.md`.

## How to reproduce

From `research_rig/`: `python3 fetch.py hourly`, then `python3 run_03.py` (writes `results_03.json`), then `python3 build_doc15.py` (writes this file). Seed 7.
