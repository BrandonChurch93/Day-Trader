# Replay 01: slow trend rules on bitcoin and ether, with real fees

Run on 2026-11-25 (UTC), the evening of 2026-11-24 in Idaho. This is the first result from the research rig in `research_rig/`.

Status: research evidence. Proposed by research. Nothing in this file is an owner decision. The rig is a research tool. It is not the product and no product code was written.

Update, later the same night: a cross-check on a second venue's prices (`docs/research/12b_replay_01_kraken_crosscheck.md`) found that the bitcoin passes below depend on including 2013 and early 2014. On a history that starts 2014-05-01, no bitcoin rule passes mark 4, on either venue's prices. The numbers in this file were not changed. Read the passes below with that in mind.

Tags: every result number in this file is MEASURED by our own rig from Bitstamp's public price bars, by the commands listed at the end. That means "our code worked this out from that data". It does not mean "this will happen with real money".

## The question

Does a plain rule that holds a coin while its price trend is up, and sits in cash when it is not, beat simply holding the coin, after the fees a US retail account really pays?

## Bottom line

- Bitcoin, at low fees: yes on this history. At Binance.US cost, 5 of 9 rules passed all five pass marks. At Alpaca cost, 3 of 9 passed.
- The rule named in advance as the main one (P1) failed at Alpaca cost. It missed the first mark by a hair: Sharpe 0.99 against 1.00 for holding, on the held-back years. The bar was not moved. It is a fail.
- Bitcoin, at high fees: no. At Kraken's $10,000 tier, Kraken entry and Coinbase entry cost, no rule passed.
- Ether: no rule passed at any venue. The rules beat holding on paper, but the result fails both checks for luck (marks 3 and 4).
- What the rules really did: they cut the worst falls roughly in half, and they gave up a large part of the gains in strong years. Since 2023 they earned less than holding bitcoin at every venue's cost.
- These are multi-day rules. They trade about 18 times the account a year. This is not day trading, and it says nothing yet about day trading.
- A pass here means "worth running in the practice account". It does not mean "makes money".

## Plain words used below

| Word | Meaning |
|---|---|
| Hold | Buy once at the start and never sell |
| Sharpe | Average return divided by how bumpy the ride was, per year. Higher is better. Cash is counted as earning nothing |
| Largest drop | The biggest fall from a high point to a later low point |
| bps | Hundredths of a percent. 30 bps is 0.30% |
| Cost per side | What one buy or one sell costs: the venue's taker fee plus 5 bps for spread and price impact |
| Break-even cost | The cost per side at which the rule stops beating hold |
| Held-back slice | 2023-01-01 to 2026-06-30. The rules were fixed before they were run on it |
| Deflated Sharpe | A Sharpe that is marked down for the number of rules tried. Above the mark means luck alone is an unlikely explanation |
| Overfitting probability | How often the rule that looked best on one half of the history did worse than the middle of the pack on the other half |
| Shuffle percentile | The rule's own in and out spells, put in random order 1,000 times. The share of those random orders that the real rule beat |

## What was fixed before the run

The full text is `research_rig/PREREG_01_daily_crypto_trend.md`, written at 06:35 UTC before any rule touched the data. One amendment was made at 06:37 UTC, before the first run: ether data moved from Coinbase to Bitstamp, and the second source moved from Coinbase to Kraken, because of Coinbase's data terms and one bad bar.

| Item | Fixed value |
|---|---|
| Data | Bitstamp daily bars. Bitcoin 2013-01-01 to 2026-11-24. Ether 2018-03-05 to 2026-11-24 |
| Fills | The rule decides on the daily close. The trade fills at the next open |
| Venues and cost per side | Binance.US 7 bps, Alpaca 30, Kraken $10,000 tier 43, Kraken entry 85, Coinbase entry 95. Fees are from `docs/research/09_brokers_and_venues.md` |
| Cash | Earns nothing |
| Leverage, shorting | None |
| Trials | 9 rules on each coin, plus 2 half-and-half portfolios: 20 trials, all in `research_rig/TRIAL_LEDGER.md` |
| Slices | Development to 2022-12-31. Held back 2023-01-01 to 2026-06-30. After the model's knowledge cutoff 2026-07-01 to 2026-11-24 |

The nine rules:

| Id | Rule |
|---|---|
| P1 | The main rule. Hold a quarter of the money for each of these that is true: the close is above its 20, 50, 100, 200 day average |
| P2 | P1, scaled down when the coin has been very bumpy over the last 30 days |
| S50, S100, S200 | All in when the close is above its 50, 100 or 200 day average. Otherwise cash |
| D20, D55 | Buy on the highest close of the last 20 (55) days. Sell on the lowest close of the last 10 (20) days |
| M30, M90 | All in when the close is above the close 30 (90) days ago. Otherwise cash |

The five pass marks. A rule passes for a venue only if all five hold at that venue's cost:

| Mark | Test | Threshold key in `config/thresholds.yaml` |
|---|---|---|
| 1 | Held-back slice: Sharpe above hold, and largest drop no more than a set share of hold's largest drop | `replay_max_drop_ratio_vs_hold` |
| 2 | Whole sample: break-even cost against hold is at least a set multiple of the venue's cost | `backtest_min_breakeven_cost_multiple` |
| 3 | Whole sample: deflated Sharpe above the mark, with all 20 trials counted | `replay_min_deflated_sharpe` |
| 4 | Overfitting probability under the mark | `backtest_max_pbo` |
| 5 | Shuffle percentile above the mark | `replay_min_shuffle_percentile` |

Three of those keys are new house numbers that this replay proposed. They are in the config with status `proposed`.

## Engine checks that passed first

Run with `python3 fixtures.py`. All passed before any result was read.

- A hand-worked trade gives the hand-worked profit.
- A hand-worked trade with fees gives the hand-worked result.
- Holding equals the coin's return less one side of cost.
- A rule allowed to peek at tomorrow's close does far better than the honest one. So the one-bar delay is real.
- Random entries on a price with no drift lose about what they pay in costs.
- The account never borrows.
- Two runs give the same output.

## Results

### Whole sample, at Alpaca cost (30 bps a side)

Bitcoin

| Rule | Growth a year | Sharpe | Largest drop | Time invested | Trades | Turnover a year | Break-even cost per side vs holding (bps) | Sharpe difference vs holding, 90% range |
|---|---|---|---|---|---|---|---|---|
| Hold | 83.2% | 1.18 | -84.9% | 100% | 1 | | | |
| P1 | 88.8% | 1.45 | -68.3% | 57% | 875 | 17.9x | 110 | -0.01 to +0.53 |
| P2 | 60.6% | 1.68 | -40.2% | 41% | 864 | 13.3x | 146 | +0.14 to +0.78 |
| S50 | 88.5% | 1.40 | -71.6% | 56% | 260 | 18.2x | 97 | -0.13 to +0.54 |
| S100 | 93.8% | 1.40 | -70.3% | 57% | 170 | 11.8x | 140 | -0.09 to +0.49 |
| S200 | 82.6% | 1.28 | -71.2% | 61% | 95 | 6.7x | 115 | -0.17 to +0.36 |
| D20 | 85.8% | 1.53 | -65.2% | 40% | 217 | 15.4x | 137 | -0.03 to +0.68 |
| D55 | 82.7% | 1.46 | -68.0% | 37% | 88 | 6.2x | 251 | -0.11 to +0.67 |
| M30 | 76.9% | 1.28 | -81.7% | 56% | 393 | 27.6x | 51 | -0.24 to +0.43 |
| M90 | 77.4% | 1.23 | -70.3% | 59% | 178 | 12.6x | 55 | -0.23 to +0.34 |

Ether

| Rule | Growth a year | Sharpe | Largest drop | Time invested | Trades | Turnover a year | Break-even cost per side vs holding (bps) | Sharpe difference vs holding, 90% range |
|---|---|---|---|---|---|---|---|---|
| Hold | 8.1% | 0.51 | -90.3% | 100% | 1 | | | |
| P1 | 34.5% | 0.83 | -56.2% | 50% | 605 | 18.7x | 117 | -0.14 to +0.64 |
| P2 | 25.7% | 0.94 | -35.1% | 30% | 544 | 11.1x | 142 | -0.07 to +0.76 |
| S50 | 38.0% | 0.85 | -60.8% | 50% | 166 | 18.8x | 131 | -0.22 to +0.71 |
| S100 | 23.0% | 0.66 | -76.3% | 52% | 129 | 14.6x | 86 | -0.42 to +0.55 |
| S200 | 27.0% | 0.71 | -73.8% | 51% | 58 | 6.4x | 208 | -0.29 to +0.64 |
| D20 | 40.5% | 0.92 | -51.6% | 38% | 144 | 16.0x | 158 | -0.14 to +0.74 |
| D55 | 38.1% | 0.93 | -48.3% | 33% | 58 | 6.4x | 328 | -0.22 to +0.83 |
| M30 | 41.9% | 0.89 | -64.8% | 51% | 229 | 25.4x | 117 | -0.10 to +0.69 |
| M90 | 14.1% | 0.53 | -76.7% | 53% | 112 | 12.6x | 36 | -0.51 to +0.46 |

Reading this table:

- The bitcoin figures are dominated by 2013 and 2017. Nobody should expect those years again.
- The 90% range for the Sharpe difference against hold includes zero for every bitcoin rule except P2, and for every ether rule. So on the whole sample only P2 on bitcoin is clearly better than hold on a risk-adjusted basis.
- P1 made 875 bitcoin trades in under 14 years. It moves in quarter steps, so it trades often.

### The held-back years, 2023-01-01 to 2026-06-30, at each venue's cost

Bitcoin

| Venue | Cost per side (bps) | Hold Sharpe | Hold drop | P1 Sharpe | P1 growth a year | P1 drop | P2 Sharpe | P2 growth a year | P2 drop | Hold growth a year |
|---|---|---|---|---|---|---|---|---|---|---|
| Binance.US | 7 | 1.00 | -53.1% | 1.15 | 38.1% | -28.6% | 1.22 | 35.0% | -21.1% | 43.3% |
| Alpaca | 30 | 1.00 | -53.1% | 0.99 | 31.3% | -31.1% | 1.06 | 29.2% | -23.9% | 43.2% |
| Kraken $10k tier | 43 | 1.00 | -53.1% | 0.91 | 27.6% | -32.5% | 0.97 | 26.0% | -25.4% | 43.2% |
| Kraken entry | 85 | 0.99 | -53.1% | 0.63 | 16.5% | -37.7% | 0.68 | 16.2% | -33.0% | 43.0% |
| Coinbase entry | 95 | 0.99 | -53.1% | 0.56 | 13.9% | -39.7% | 0.61 | 13.9% | -34.9% | 43.0% |

Ether

| Venue | Cost per side (bps) | Hold Sharpe | Hold drop | P1 Sharpe | P1 growth a year | P1 drop | P2 Sharpe | P2 growth a year | P2 drop | Hold growth a year |
|---|---|---|---|---|---|---|---|---|---|---|
| Binance.US | 7 | 0.44 | -67.6% | 0.77 | 25.3% | -37.7% | 0.88 | 22.9% | -27.6% | 8.0% |
| Alpaca | 30 | 0.43 | -67.6% | 0.65 | 19.7% | -41.2% | 0.76 | 18.8% | -30.3% | 7.9% |
| Kraken $10k tier | 43 | 0.43 | -67.6% | 0.58 | 16.6% | -43.0% | 0.69 | 16.6% | -31.8% | 7.8% |
| Kraken entry | 85 | 0.43 | -67.6% | 0.37 | 7.2% | -48.7% | 0.47 | 9.6% | -36.4% | 7.7% |
| Coinbase entry | 95 | 0.43 | -67.6% | 0.32 | 5.1% | -50.0% | 0.42 | 8.0% | -37.5% | 7.7% |

Reading this table:

- Bitcoin: hold grew faster than P1 and P2 at every venue. The rules only win on Sharpe, and only at Binance.US cost (and P2 at Alpaca cost). They do have much smaller drops.
- Ether: hold did poorly in these years, so the rules beat it at Binance.US, Alpaca and Kraken's $10,000 tier. At Kraken entry and Coinbase entry cost the fees take most or all of the gain.

### Pass marks

Bitcoin. Each cell: marks 1 to 5 in order (Y passed, n failed), then the verdict.

| Rule | Binance.US | Alpaca | Kraken $10k tier | Kraken entry | Coinbase entry |
|---|---|---|---|---|---|
| P1 | YYYYY PASS | nYYYY fail | nYYnY fail | nnYnY fail | nnYnY fail |
| P2 | YYYYY PASS | YYYYY PASS | nYYnY fail | nnYnY fail | nnYnY fail |
| S50 | YYYYY PASS | YYYYY PASS | YYYnY fail | nnYnY fail | nnYnY fail |
| S100 | nYYYY fail | nYYYY fail | nYYnY fail | nnYnY fail | nnYnY fail |
| S200 | nYYYY fail | nYYYY fail | nYYnY fail | nnYnY fail | nnYnY fail |
| D20 | YYYYY PASS | YYYYY PASS | nYYnY fail | nnYnY fail | nnYnY fail |
| D55 | nYYYY fail | nYYYY fail | nYYnY fail | nYYnY fail | nYYnY fail |
| M30 | nYYYY fail | nnYYY fail | nnYnY fail | nnnnn fail | nnnnn fail |
| M90 | YYYYY PASS | nnYYY fail | nnYnY fail | nnYnY fail | nnYnn fail |

| Venue | Rules that pass all five | Overfitting probability |
|---|---|---|
| Binance.US | P1, P2, S50, D20, M90 | 0.12 |
| Alpaca | P2, S50, D20 | 0.20 |
| Kraken $10k tier | none | 0.26 |
| Kraken entry | none | 0.40 |
| Coinbase entry | none | 0.41 |

Ether. Each cell: marks 1 to 5 in order (Y passed, n failed), then the verdict.

| Rule | Binance.US | Alpaca | Kraken $10k tier | Kraken entry | Coinbase entry |
|---|---|---|---|---|---|
| P1 | YYnnY fail | nYnnY fail | nYnnY fail | nnnnY fail | nnnnY fail |
| P2 | YYnnY fail | YYnnY fail | YYnnY fail | YnnnY fail | nnnnY fail |
| S50 | nYnnY fail | nYnnY fail | nYnnY fail | nnnnY fail | nnnnn fail |
| S100 | nYnnn fail | nYnnn fail | nnnnn fail | nnnnn fail | nnnnn fail |
| S200 | YYnnn fail | YYnnn fail | YYnnn fail | nYnnn fail | nYnnn fail |
| D20 | nYnnY fail | nYnnY fail | nYnnY fail | nnnnY fail | nnnnY fail |
| D55 | YYnnY fail | YYnnY fail | YYnnY fail | YYnnY fail | YYnnY fail |
| M30 | nYnnY fail | nYnnY fail | nYnnY fail | nnnnY fail | nnnnY fail |
| M90 | nYnnn fail | nnnnn fail | nnnnn fail | nnnnn fail | nnnnn fail |

| Venue | Rules that pass all five | Overfitting probability |
|---|---|---|
| Binance.US | none | 0.75 |
| Alpaca | none | 0.86 |
| Kraken $10k tier | none | 0.82 |
| Kraken entry | none | 0.70 |
| Coinbase entry | none | 0.66 |

Detail for the two main rules:

| Venue | Coin | Rule | Held-back Sharpe, rule vs hold | Drop ratio | Break-even vs needed (bps) | Deflated Sharpe | Overfitting probability | Shuffle percentile | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| Binance.US | BTC | P1 | 1.15 vs 1.00 | 0.54 | 110 vs 14 | 0.999 | 0.12 | 1.000 | PASS |
| Binance.US | BTC | P2 | 1.22 vs 1.00 | 0.40 | 146 vs 14 | 1.000 | 0.12 | 1.000 | PASS |
| Binance.US | ETH | P1 | 0.77 vs 0.44 | 0.56 | 117 vs 14 | 0.804 | 0.75 | 0.989 | fail |
| Binance.US | ETH | P2 | 0.88 vs 0.44 | 0.41 | 142 vs 14 | 0.893 | 0.75 | 1.000 | fail |
| Alpaca | BTC | P1 | 0.99 vs 1.00 | 0.59 | 110 vs 60 | 0.999 | 0.20 | 1.000 | fail |
| Alpaca | BTC | P2 | 1.06 vs 1.00 | 0.45 | 146 vs 60 | 1.000 | 0.20 | 1.000 | PASS |
| Alpaca | ETH | P1 | 0.65 vs 0.43 | 0.61 | 117 vs 60 | 0.734 | 0.86 | 0.992 | fail |
| Alpaca | ETH | P2 | 0.76 vs 0.43 | 0.45 | 142 vs 60 | 0.829 | 0.86 | 1.000 | fail |
| Kraken $10k tier | BTC | P1 | 0.91 vs 1.00 | 0.61 | 110 vs 86 | 0.998 | 0.26 | 1.000 | fail |
| Kraken $10k tier | BTC | P2 | 0.97 vs 1.00 | 0.48 | 146 vs 86 | 1.000 | 0.26 | 1.000 | fail |
| Kraken $10k tier | ETH | P1 | 0.58 vs 0.43 | 0.64 | 117 vs 86 | 0.688 | 0.82 | 0.995 | fail |
| Kraken $10k tier | ETH | P2 | 0.69 vs 0.43 | 0.47 | 142 vs 86 | 0.801 | 0.82 | 1.000 | fail |
| Kraken entry | BTC | P1 | 0.63 vs 0.99 | 0.71 | 110 vs 170 | 0.990 | 0.40 | 1.000 | fail |
| Kraken entry | BTC | P2 | 0.68 vs 0.99 | 0.62 | 146 vs 170 | 0.999 | 0.40 | 1.000 | fail |
| Kraken entry | ETH | P1 | 0.37 vs 0.43 | 0.72 | 117 vs 170 | 0.507 | 0.70 | 0.996 | fail |
| Kraken entry | ETH | P2 | 0.47 vs 0.43 | 0.54 | 142 vs 170 | 0.628 | 0.70 | 1.000 | fail |
| Coinbase entry | BTC | P1 | 0.56 vs 0.99 | 0.75 | 110 vs 190 | 0.986 | 0.41 | 1.000 | fail |
| Coinbase entry | BTC | P2 | 0.61 vs 0.99 | 0.66 | 146 vs 190 | 0.998 | 0.41 | 1.000 | fail |
| Coinbase entry | ETH | P1 | 0.32 vs 0.43 | 0.74 | 117 vs 190 | 0.458 | 0.66 | 0.996 | fail |
| Coinbase entry | ETH | P2 | 0.42 vs 0.43 | 0.55 | 142 vs 190 | 0.577 | 0.66 | 1.000 | fail |

Reading these tables:

- Mark 1 is the one that separates the venues for bitcoin. The same rule passes at 7 bps and fails at 43.
- Ether fails marks 3 and 4 everywhere. Which ether rule looked best changed from one part of the history to another, which is what choosing by luck looks like.
- Three bitcoin rules pass at Alpaca cost and the main rule does not. Nine rules were run on the same held-back years, so one or two passing mark 1 by chance is expected. Marks 3 to 5 guard against that only in part.

### Half bitcoin, half ether, from 2018-03-05

| Rule | Venue | Slice | Rule growth a year | Rule Sharpe | Rule drop | Hold growth a year | Hold Sharpe | Hold drop |
|---|---|---|---|---|---|---|---|---|
| P1 | Binance.US | Whole sample | 38.4% | 0.98 | -49.0% | 15.8% | 0.56 | -81.2% |
| P1 | Binance.US | Held back | 30.2% | 0.95 | -30.3% | 28.9% | 0.76 | -57.6% |
| P1 | Binance.US | After cutoff | 33.0% | 1.04 | -16.1% | 2.2% | 0.26 | -35.0% |
| P1 | Alpaca | Whole sample | 32.4% | 0.87 | -52.9% | 15.8% | 0.56 | -81.2% |
| P1 | Alpaca | Held back | 24.1% | 0.81 | -32.7% | 28.9% | 0.76 | -57.6% |
| P1 | Alpaca | After cutoff | 28.1% | 0.93 | -16.6% | 2.2% | 0.26 | -35.0% |
| P1 | Coinbase entry | Whole sample | 16.8% | 0.58 | -62.5% | 15.7% | 0.56 | -81.4% |
| P1 | Coinbase entry | Held back | 8.4% | 0.41 | -40.9% | 28.9% | 0.76 | -57.6% |
| P1 | Coinbase entry | After cutoff | 15.4% | 0.60 | -17.9% | 2.2% | 0.26 | -35.0% |
| P2 | Binance.US | Whole sample | 30.0% | 1.14 | -34.1% | 15.8% | 0.56 | -81.2% |
| P2 | Binance.US | Held back | 28.5% | 1.11 | -21.7% | 28.9% | 0.76 | -57.6% |
| P2 | Binance.US | After cutoff | 23.8% | 0.92 | -14.7% | 2.2% | 0.26 | -35.0% |
| P2 | Alpaca | Whole sample | 25.8% | 1.01 | -36.1% | 15.8% | 0.56 | -81.2% |
| P2 | Alpaca | Held back | 23.5% | 0.95 | -23.5% | 28.9% | 0.76 | -57.6% |
| P2 | Alpaca | After cutoff | 19.1% | 0.77 | -15.3% | 2.2% | 0.26 | -35.0% |
| P2 | Coinbase entry | Whole sample | 15.7% | 0.69 | -41.7% | 15.7% | 0.56 | -81.4% |
| P2 | Coinbase entry | Held back | 10.4% | 0.51 | -30.2% | 28.9% | 0.76 | -57.6% |
| P2 | Coinbase entry | After cutoff | 6.9% | 0.37 | -16.8% | 2.2% | 0.26 | -35.0% |

Deflated Sharpe for the portfolios, at Alpaca cost: P1 0.77 P2 0.879. Both are under the mark, so both portfolios fail mark 3. The "after cutoff" rows are yearly rates worked out from only 147 days, so they look larger than the plain returns in the section below.

### Year by year, at Alpaca cost

This table was not in the pre-registration. It describes the same trials and adds no new rule. 2026 runs to November 24.

Bitcoin

| Year | Hold | Hold worst drop | P1 | P1 worst drop | P2 | P2 worst drop |
|---|---|---|---|---|---|---|
| 2013 | 5462.6% | -71.0% | 3677.8% | -68.3% | 1031.6% | -25.3% |
| 2014 | -56.1% | -66.2% | -14.1% | -32.4% | -7.1% | -13.3% |
| 2015 | 34.2% | -46.6% | 38.6% | -24.0% | 39.2% | -21.1% |
| 2016 | 124.3% | -29.6% | 88.0% | -26.4% | 93.9% | -16.9% |
| 2017 | 1336.4% | -35.1% | 878.6% | -32.4% | 263.4% | -21.0% |
| 2018 | -73.4% | -81.5% | -41.2% | -50.2% | -20.8% | -24.3% |
| 2019 | 94.1% | -48.8% | 82.9% | -38.0% | 71.3% | -23.4% |
| 2020 | 304.5% | -53.3% | 201.5% | -23.8% | 129.2% | -17.6% |
| 2021 | 59.4% | -53.1% | 36.8% | -38.6% | 14.0% | -22.6% |
| 2022 | -64.2% | -67.0% | -33.4% | -34.6% | -25.1% | -25.9% |
| 2023 | 155.7% | -20.1% | 83.9% | -21.0% | 65.3% | -21.4% |
| 2024 | 121.0% | -26.2% | 65.0% | -31.1% | 68.5% | -23.2% |
| 2025 | -6.3% | -32.1% | -10.8% | -22.8% | -9.4% | -20.1% |
| 2026 | -31.7% | -39.6% | 3.9% | -12.6% | 4.8% | -12.6% |

Ether

| Year | Hold | Hold worst drop | P1 | P1 worst drop | P2 | P2 worst drop |
|---|---|---|---|---|---|---|
| 2018 | -84.6% | -90.3% | -21.1% | -37.3% | -7.9% | -15.2% |
| 2019 | -1.6% | -63.6% | 21.6% | -43.8% | 23.1% | -26.7% |
| 2020 | 473.1% | -61.7% | 199.7% | -43.7% | 126.9% | -20.5% |
| 2021 | 398.8% | -57.3% | 216.4% | -52.9% | 84.3% | -20.6% |
| 2022 | -67.5% | -74.0% | -30.2% | -31.8% | -20.3% | -21.4% |
| 2023 | 90.9% | -27.4% | 36.3% | -29.0% | 31.8% | -25.4% |
| 2024 | 46.1% | -45.3% | 26.7% | -37.7% | 31.9% | -28.3% |
| 2025 | -10.9% | -60.1% | 23.8% | -27.0% | 15.6% | -16.2% |
| 2026 | -43.5% | -53.3% | -1.9% | -19.4% | -3.1% | -17.8% |

The pattern is the same in every cycle. In falling years the rules lost far less (2018, 2022, 2026). In strong years they made far less (2017, 2020, 2021, 2023, 2024). In flat, choppy years they lost a little to costs and false starts (2025 for bitcoin).

### After the model's knowledge cutoff, 2026-07-01 to 2026-11-24

This slice is 147 days. It is too short to prove anything and is reported because it was promised.

- Bitcoin: hold -0.7%, P1 +8.5%, P2 +7.9%. Other rules ranged from -17.7% (M90) to +21.3% (M30).
- Ether: hold +4.0%, P1 +11.9%, P2 +6.6%. Other rules ranged from -22.0% (M90) to +36.9% (S50).

The spread between rules in one short window is larger than any difference between a rule and hold. That is the noise level to keep in mind.

## Two checks on the method

### Second price source

Kraken's public daily bars cover the last 720 days. Same rules, same cost, Alpaca's 30 bps.

| Coin | Days | Median gap between closes (bps) | Largest gap (bps) | Rule | Bitstamp: return, Sharpe, drop, trades | Kraken: return, Sharpe, drop, trades | Days the target differed | Hold return same dates |
|---|---|---|---|---|---|---|---|---|
| BTC | 720 | 1.1 | 10.5 | P1 | -11.2%, -0.14, -26.4%, 147 | -11.0%, -0.13, -26.2%, 147 | 0 | -38.6% |
| BTC | 720 | 1.1 | 10.5 | P2 | -8.7%, -0.10, -24.9%, 152 | -8.6%, -0.10, -24.8%, 154 | 229 | -38.6% |
| ETH | 720 | 1.3 | 14.6 | P1 | 5.8%, 0.26, -35.7%, 135 | 6.6%, 0.27, -35.8%, 135 | 2 | -55.8% |
| ETH | 720 | 1.3 | 14.6 | P2 | 4.5%, 0.21, -23.6%, 129 | 5.0%, 0.22, -23.7%, 126 | 470 | -55.8% |

The two sources agree to about 1 bp on a normal day and the results match. P2's target differs on many days because it is a sliding scale, and the differences are tiny. Over these 720 days both coins fell hard, and bitcoin P1 still lost 11.2%. A trend rule limits a fall. It does not turn a falling market into a gain.

### What if the fill is late

Crypto never closes, so on these bars the next open is the same moment as the close the rule just read. A real program needs time to act. This check was written down in `research_rig/PREREG_01_S1_fill_delay.md` before it was run. It adds no new rule and has no pass mark. Each cell shows Sharpe for three fills: at the next open / one hour late / one full day late.

Bitcoin: median move in the first hour 29 bps, 90th percentile 115 bps, days 5076, hour missing 0

| Rule | Alpaca, whole sample | Alpaca, held back | Binance.US, whole sample | Binance.US, held back |
|---|---|---|---|---|
| P1 | 1.45 / 1.44 / 1.48 | 0.99 / 1.00 / 0.99 | 1.52 / 1.51 / 1.55 | 1.15 / 1.15 / 1.14 |
| P2 | 1.68 / 1.69 / 1.67 | 1.06 / 1.05 / 1.04 | 1.78 / 1.79 / 1.77 | 1.22 / 1.21 / 1.20 |
| S50 | 1.40 / 1.40 / 1.42 | 1.24 / 1.22 / 1.12 | 1.47 / 1.47 / 1.49 | 1.38 / 1.37 / 1.26 |
| S100 | 1.40 / 1.40 / 1.42 | 0.93 / 0.91 / 0.91 | 1.44 / 1.44 / 1.46 | 1.03 / 1.02 / 1.01 |
| S200 | 1.28 / 1.28 / 1.31 | 0.94 / 0.95 / 0.75 | 1.30 / 1.30 / 1.33 | 0.99 / 1.01 / 0.80 |
| D20 | 1.53 / 1.47 / 1.37 | 1.04 / 1.03 / 0.98 | 1.60 / 1.54 / 1.44 | 1.17 / 1.17 / 1.12 |
| D55 | 1.46 / 1.46 / 1.41 | 0.99 / 1.00 / 0.86 | 1.49 / 1.49 / 1.44 | 1.06 / 1.06 / 0.93 |
| M30 | 1.28 / 1.28 / 1.40 | 0.85 / 0.88 / 1.18 | 1.39 / 1.39 / 1.51 | 1.07 / 1.10 / 1.39 |
| M90 | 1.23 / 1.23 / 1.19 | 0.95 / 0.92 / 0.81 | 1.28 / 1.28 / 1.24 | 1.04 / 1.01 / 0.90 |

Ether: median move in the first hour 41 bps, 90th percentile 145 bps, days 3187, hour missing 0

| Rule | Alpaca, whole sample | Alpaca, held back | Binance.US, whole sample | Binance.US, held back |
|---|---|---|---|---|
| P1 | 0.83 / 0.83 / 0.78 | 0.65 / 0.64 / 0.46 | 0.92 / 0.91 / 0.86 | 0.77 / 0.76 / 0.58 |
| P2 | 0.94 / 0.96 / 0.85 | 0.76 / 0.77 / 0.57 | 1.04 / 1.05 / 0.93 | 0.88 / 0.89 / 0.70 |
| S50 | 0.85 / 0.86 / 0.94 | 0.86 / 0.89 / 0.59 | 0.93 / 0.93 / 1.02 | 0.96 / 0.99 / 0.69 |
| S100 | 0.66 / 0.67 / 0.62 | 0.60 / 0.60 / 0.40 | 0.71 / 0.72 / 0.67 | 0.69 / 0.69 / 0.50 |
| S200 | 0.71 / 0.68 / 0.67 | 0.68 / 0.65 / 0.63 | 0.73 / 0.71 / 0.70 | 0.72 / 0.68 / 0.66 |
| D20 | 0.92 / 0.94 / 0.80 | 0.21 / 0.22 / 0.34 | 0.99 / 1.01 / 0.87 | 0.32 / 0.33 / 0.45 |
| D55 | 0.93 / 0.91 / 1.03 | 0.59 / 0.62 / 0.66 | 0.97 / 0.95 / 1.06 | 0.64 / 0.67 / 0.71 |
| M30 | 0.89 / 0.82 / 0.91 | 0.69 / 0.65 / 0.65 | 0.99 / 0.92 / 1.00 | 0.85 / 0.81 / 0.81 |
| M90 | 0.53 / 0.55 / 0.64 | 0.58 / 0.56 / 0.52 | 0.58 / 0.60 / 0.69 | 0.65 / 0.63 / 0.59 |

- One hour late changes almost nothing, even though the price typically moves 29 bps (bitcoin) or 41 bps (ether) in that hour. The moves are in both directions and wash out.
- One day late is a different story for ether: P1's held-back Sharpe falls from 0.65 to 0.46 at Alpaca cost. Bitcoin barely moves.
- So the program must act within the hour after the daily close, and the ether result is fragile.

## What this does not show

- The rules were picked by a model that has read the price history of both coins up to June 2026. They are textbook rules, and textbooks keep the rules that worked. The held-back slice cannot fix that. Only running forward can.
- Taxes are not in it. P1 made hundreds of trades, and gains on anything held a year or less are taxed as ordinary income. Holding puts the tax off. After tax, the gap between a trading rule and hold gets worse for the rule. How much depends on his tax position. UNKNOWN.
- Cash earned nothing here. In real life idle dollars can earn interest. That would help the rules, which sit in cash about 40% to 70% of the time.
- Real fills on small orders were not measured. The 5 bps allowance comes from one evening of order book readings in research 09.
- Drops are measured on daily closes. Falls inside a day were deeper.
- One exchange's price history. Bitstamp's terms for personal research use could not be read (the page did not load). UNKNOWN. The raw bars are not stored in this repo. `fetch.py` downloads them again.
- Nothing here is intraday. Whether true day trading survives these fees has not been tested yet.

## What research proposes from this

None of this is decided. Each line is for the owner to accept, change or decline.

Update: research withdraws proposal 1 as worded here. The replacement is in `docs/research/12b_replay_01_kraken_crosscheck.md`. Proposal 5's first test is done: `docs/research/15_replay_03_intraday_crypto.md`.

1. Carry three bitcoin rules into practice trading as candidates: P2, S50 and D20. They passed at Alpaca cost. P1 goes too, clearly labelled as having failed mark 1 at Alpaca cost, so its live behaviour can be compared.
2. Run ether in practice for observation only, labelled as having failed the replay.
3. Treat fees as part of the rule. At 85 bps a side and above, nothing passed. This supports not trading crypto on Kraken entry or Coinbase entry tiers, and keeps the live crypto venue question open until practice results exist.
4. Keep the three new house numbers as proposed in the config until he confirms or changes them.
5. Test next, each with its own written plan before it runs: intraday rules on hourly bars against each venue's fees. A slow trend rule on a wider basket of liquid coins, which needs price history that includes dead coins. Trend rules on stock funds, which needs a licensed data source (see research 10).

## How to reproduce

From `research_rig/`, with Python 3, numpy, pandas and scipy:

| Step | Command | Output |
|---|---|---|
| Download the bars | `python3 fetch.py crypto`, then `kraken`, then `hourly` | `data/` (not stored in the repo) |
| Engine checks | `python3 fixtures.py` | prints ALL PASS |
| Replay | `python3 run_01.py` | `results_01.json` |
| Pass marks per venue | `python3 run_01b.py` | `passmarks_01.json` |
| Cross-check and fill delay | `python3 run_01c.py` | `results_01c.json` |
| Year table | `python3 report_01d.py` | `results_01d.json` |
| The tables in this file | `python3 tables_01.py` | `tables_01.md` |

Seed 7 throughout. Bars downloaded later will include new days, so the last rows will differ. The unfinished bar for the download day is dropped.
