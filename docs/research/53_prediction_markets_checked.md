# 53. Prediction markets as a place for an AI trader: the reading, checked

Status: one helper wrote the reading on 2026-11-25 and a second opened every source: 26 claims confirmed, 8 wrong as first written, 3 not found. The wrong ones are corrected below. Nothing here was measured by us on market data; no return was worked out. Written 2026-11-25 19:04 UTC.

Why: the standing job is to keep finding places where an AI that reads a lot could have an edge. A prediction market pays 1 dollar if an event happens and nothing if it does not, so the price is a probability. An AI that judges probabilities better than the crowd would make money there. This page asks whether anyone has shown that, and whether we can test it honestly.

## The short answer

- Open to a US account with small money and an API: yes, three venues.
- AI models beating the market price: not shown by anyone. The largest checks say the opposite.
- The one result in this field that keeps coming back is not about forecasting at all: people who rest orders and wait (makers) do better than people who take the price (takers). We cannot test that honestly from free history, because the free history has no order book.
- So: one cheap AI test is possible and is expected to fail; the more promising idea needs us to record order books first.

## Venues a US resident can use, STATED by the venues and reviewers

- Kalshi: regulated exchange since November 2020, its own clearing house registered August 2024 ([CryptoSlate](https://cryptoslate.com/prediction-markets/us-regulated/)). Minimum deposit 10 dollars. Taker fee 0.07 x price x (1 - price) per contract, rounded up, so 1.75 cents at a price of 50 cents; no fee at settlement; no fee for bank withdrawals ([Kalshi fee schedule, 2026-07-07](https://kalshi.com/docs/kalshi-fee-schedule.pdf)).
- Kalshi makers: free by default, but the same fee schedule charges makers 0.0175 x price x (1 - price) on the big sports and economic-release markets, which one study puts at 61% to 66% of all volume ([Vladosyna](https://github.com/Vladosyna/kalshi-makers-takers-persistence/blob/master/reports/final/paper_a_composition.md)). The first reading said "makers free on most markets"; by count of markets perhaps, by volume no.
- Kalshi has a free API and a practice site with pretend money ([Kalshi demo documentation](https://docs.kalshi.com/getting_started/demo_env)). Whether a practice account needs approval: NOT FOUND.
- Polymarket US: a separate regulated venue, minimum 1 dollar, taker fee 0.095 down to 0.0695 by volume, makers free on standard markets, not open in Nevada ([RG.org review](https://rg.org/predictions/review/polymarket)). API open to any verified account; trades sent by API get the 0.0695 rate and a 70% rebate until 2026-12-31 ([Polymarket US documentation](https://docs.polymarket.us/getting-started/quickstart)). No practice site for small accounts ([TradoxVPS](https://tradoxvps.com/polymarket-us-api/)).
- Interactive Brokers ForecastTrader: no commission plus 1 cent a contract, through the same API as the rest of an Interactive Brokers account ([ChanceLedger](https://chanceledger.com/prediction-markets/comparison/), [Rivo Markets](https://rivo.markets/best-prediction-market-apps)). Its minimum and whether its paper account covers these contracts: NOT FOUND.

## Free history, MEASURED by two helpers on 2026-11-25 (the addresses answered; no data was scored)

- Kalshi: every trade with price, size, which side took, and time, plus one-minute candles, back to 2021, with no key. Settled markets older than 2026-09-26 sit in a separate archive ([Kalshi historical data](https://docs.kalshi.com/getting_started/historical_data)).
- Polymarket: market lists back to 2020 and price history for newer markets; the US venue from 2025-10-29.
- What the free history does not have: the order book of the past. Only today's book can be read for free. A data vendor says it sells Kalshi's past order books ([BMLL announcement](https://www.bmlltech.com/news/press-releases-and-news/bmll-and-kalshi-partner-to-expand-institutional-access-to-prediction-market-data)); its price and coverage are UNKNOWN.

## AI forecasters against the market price, STATED by the studies

- ForecastBench, 2026-11-17: the best AI scores 69.4 against 68.1 for the median superforecaster overall ([ForecastBench](https://www.forecastbench.org/leaderboards/human_leaderboard_overall.html)). That lead comes from questions about data series. On questions that have a market price, 0 of 527 entries beat the price shown to them by a margin clear of chance, and 442 were clearly worse ([EA Forum, "The Copier Line"](https://forum.effectivealtruism.org/posts/8YuG9EuhyYqaNBt7F/the-copier-line-what-forecastbench-s-market-scores-actually)).
- Prophet Arena, 1,367 Kalshi events: the best model's error score tied the market's (0.184 against 0.187) and 0 of 23 models broke even on pretend trading ([Rillor summary](https://rillor.com/insights/llm-forecasting-accuracy-benchmarks/report)).
- Metaculus, spring 2026: the bot team against professional forecasters, no clear difference on 99 shared questions ([Rillor summary](https://rillor.com/insights/llm-forecasting-accuracy-benchmarks/report)).

## AI models trading real money there, STATED

- Prediction Arena, six leading models with real money: on Kalshi over 57 days (2026-01-12 to 2026-03-09) every one lost, between 16.0% and 30.8%. Over the 28 days when both venues ran, they averaged -22.6% on Kalshi and -1.1% on Polymarket ([Prediction Arena paper](https://arxiv.org/html/2604.07355)). The first reading gave -22.6% as the 57-day average; it is the 28-day one. Whether fees are inside those figures the paper does not say.
- One small run made money: 200 dollars became 360.67 in 26 days on Kalshi in April and May 2026, 236 orders filled of 396 sent ([Prophet Arena live pilot](https://arxiv.org/html/2607.06166)). With the best three and worst three trades removed it is +24.2%. One run, 26 days, one model; the 90% range on its Sharpe ratio runs from 0.90 to 6.12.

## Who makes money, STATED

- Polymarket: 84.1% of traders are behind overall and 2% ever made more than 1,000 dollars ([The Defiant](https://thedefiant.io/news/research-and-opinion/polymarket-profitability-report-april-2026)); the top 1% of wallets took 76.5% of the profit ([Akey and others, 2026](https://www.paris-december.eu/sites/default/files/papers/2026/7337_chamar_2026_complete.pdf)).
- Kalshi, 2021 to April 2025: takers lost 31.46% of what they staked and makers 9.64%; makers at prices of 50 cents and above made 2.6%. That was before makers paid any fee ([George Washington University working paper](https://www2.gwu.edu/~forcpgm/2026-001.pdf)).
- Later studies agree on the direction and are weaker than first written. One gives makers +1.12% and takers -1.12% before fees ([Becker, January 2026](https://www.jbecker.dev/research/prediction-market-microstructure); a different Becker from the one in `docs/research/46_becker_calls_measured.md`). Another's "+2.40%" after May 2025 is the gap between makers and takers, not what a maker earned ([Vladosyna](https://github.com/Vladosyna/kalshi-makers-takers-persistence/blob/master/reports/final/paper_a_composition.md)).
- Cheap long shots are the worst deal: takers lose about 89 cents per dollar on contracts priced at 0 to 2 cents and 0% to 2% on favourites ([hrishi-tailor](https://github.com/hrishi-tailor/prediction-market-calibration)).
- Prices on the two venues differ by a median 0.78 cents, less than the fees to trade both ([PredictMarketCap, census of 2026-08-30](https://predictmarketcap.com/analysis/prediction-market-arbitrage-study)). Dropped.
- After an economic release, Kalshi takes about 41 seconds to make half its move and Polymarket about 30, against 3 to 4 seconds for futures; the first trade after the release prints 10 to 12 seconds in ([unaifmm](https://github.com/unaifmm/prediction-markets-fed)).

## What can be tested here, and how honestly

- Resting orders that take the other side of long-shot buyers on Kalshi. This is where the published edge is. It cannot be tested from free history: without the past order book we cannot know whether our order would have been filled or how many were ahead of it. Counting every touch as a fill flatters it; counting only prices that traded through punishes it; the gap between the two is larger than the 1% to 2% at stake. To test it we would first have to record the live order book ourselves for some weeks, or place very small real orders.
- An AI model that reads the news up to a date, gives its own probability, and takes the price when it disagrees by a wide margin. This can be tested as a taker on Kalshi markets settled after 2026-04-01, after the models' knowledge line, buying at the next minute's price and paying the full fee. Expectation written down first: it does not pass, because 0 of 527 forecasters and 0 of 23 models managed it in the studies above.
- Trading the seconds after an economic release. Not testable from free history, and each such market charges makers as well as takers.

## What this means for the project

- The honest place for a small account here is as the patient side of the trade, which is a job for a fixed rule with good plumbing more than for an AI forecaster.
- Recording Kalshi order books ourselves is not open to us as things stand. Checked 2026-11-25 19:08 UTC before anything was recorded: the venue's developer agreement lets API data be stored only to help one's own trading on Kalshi ([Kalshi Developer Agreement](https://assets.kalshi.com/Kalshi-Developer-Agreement.pdf)), and we have no account there. No recorder was started. If the owner opens an account to trade there, recording for that trading is what the agreement allows.
- A real account on any of these venues is the owner's to open. Nothing has been opened.
