INFERENCE: Published empirical research does not support trading thin-venue price lags, standalone resting bids at a 0% maker fee, or venue-specific crisis dislocations for a small US cash-spot account.
MEASURED (by the cited source): Cross-exchange Bitcoin arbitrage net returns turned negative for US investors after April 2018, live crypto maker orders suffer negative post-fill markout drift, and Binance.US's 2023 price dislocations were caused by cut banking rails and a 20-month USD trading halt.
MEASURED (by the cited source): Outside trend (Plan 75) and washout rebounds (Plan 76), daily volume-shock reversal turns negative on Binance large coins, weekly multi-indicator cross-sectional factors depend on shorting and outlier exclusions, and weekly minimum-variance weighting lowers risk across five large coins at 10 bp cost without proving superior risk-adjusted return.
INFERENCE: Calls for this round are 0 test, 0 count first, 2 watch (resting-bid execution as an overlay only on an already-passing crash-rebound rule; low-volatility/minimum-variance sizing as a passive risk benchmark), and 4 skip (lagging-venue prices, standalone resting bids, venue dislocations, and daily/weekly cross-sectional alpha rules).
STATED: Every source below was opened directly on 2026-11-26; no exchange market data or repo price files were read, and no forbidden crypto-news domains were collected or cited.

## Scope and permitted data map

MEASURED (from repo `docs/research/194_data_source_terms_audit.md` and `docs/QUEUE.md`): Coinbase market data is barred by its Market Data Terms s3 (no algorithm, agent, automated system, or AI research without prior express written consent); Kalshi, CoinMarketCap, and Polymarket (US Restricted Persons) are also barred.

Permitted or usable data sources from `docs/research/194_data_source_terms_audit.md` for crypto research in this project:
- Binance Vision (`data.binance.vision`): STATED in doc 194 as allowed with limits under CC BY-NC-SA 4.0 for purely personal non-production historical backtesting; bars live proprietary execution and requires attribution plus ShareAlike on public derivative works.
- Bitstamp (`www.bitstamp.net`): STATED in doc 194 as allowed with limits (API page permits creating ratios, calculations, new original works, and statistics; commercial users need a Data License Agreement; US terms UNKNOWN).
- Kraken (`api.kraken.com`, `assets.kraken.com`): STATED in doc 194 as allowed with limits for private backtesting and research; raw redistribution barred without consent.
- Gemini (`api.gemini.com`): STATED in doc 194 as allowed with limits for personal or internal price and market analysis; raw redistribution barred without consent.
- Binance.US (`api.binance.us` and its historical market data page): STATED in doc 194 as full Terms of Use UNKNOWN (only the intro opened); used only through documented public endpoints with detail kept off the repo until full terms are read.
- Supporting non-price sources: STATED in doc 194 as allowed or allowed with limits for SEC EDGAR, Treasury Fiscal Data, GDELT, Wikipedia, AlphaGrowth unlocks (with credit), and DefiLlama (private non-commercial).

Venue fee and access baseline for a small Idaho cash-spot account ($500 to $2,000, $250 test size):
- STATED on the [Binance.US fee schedule](https://www.binance.us/fees): "Binance.US charges a flat 0% maker and 0.01% taker fee on the Tier 0 pair (currently BNB/USD only), and 0% maker and 0.02% taker on all other pairs."
- MEASURED (from repo `docs/QUEUE.md` and Round 68 brief): Binance.US all-in cost at $250 was measured once at about 7 to 8 bp per side; Idaho is listed as a supported state in doc 193.
- STATED on the [Binance.US crypto-only state guide](https://support.binance.us/en/articles/9843321-a-complete-guide-to-using-binance-us-in-a-crypto-only-state): "Most USD Advanced Trading pairs were removed from our platform on June 26, 2023." and "As of February 19, 2025, USD services are available for most supported states."

## 1. Lagging-venue prices (slow trader, seconds to minutes)

Mechanism: A slow trader watches a liquid global price feed (such as Binance or CME) and buys or sells on a thin US venue (such as Binance.US, Bitstamp, Gemini, or Kraken) when the thin venue trails a move, expecting local retail or slow quotes to catch up. In theory, passive retail traders or stale automated market makers on the thin venue are on the other side and keep losing until they update their quotes.

Primary evidence and cost treatment:
- MEASURED (by the cited source) in [Crépellière, Pelster and Zeisberger (TAF Working Paper 067, 2022)](https://en.wiwi.uni-paderborn.de/fileadmin-wiwi/cetar/TAF_Working_Paper_Series/TAF_WP_067_CrepellierePelsterZeisberger2022_rev.pdf), covering 2017 through 2021 across 18 fiat-to-crypto exchanges (including Bitstamp, Gemini, Kraken, and Coinbase) and 10 crypto-to-crypto exchanges (including Binance): "We find that price deviations hardly exist since April 2018, which is the end of the time period analyzed by Makarov and Schoar (2020)."
- MEASURED (by the cited source) in [Crépellière, Pelster and Zeisberger (2022)](https://en.wiwi.uni-paderborn.de/fileadmin-wiwi/cetar/TAF_Working_Paper_Series/TAF_WP_067_CrepellierePelsterZeisberger2022_rev.pdf): The BTC cross-platform strategy averaged +104 bp gross, +93 bp after bid-ask spreads, +25 bp after institutional fees ($1 million 30-day volume), and -12 bp at maximum retail taker fees, excluding blockchain withdrawal fees; for a US investor with geographic restrictions and transaction costs, the mean return was -16 bp, and zero-cost returns from April 2018 onward were negative on average. They conclude: "Summarizing these findings, we conclude that arbitrage in the market for cryptocurrencies is hardly possible anymore, as price differences across exchanges are relatively low given present frictions."
- MEASURED (by the cited source) in [SEC NYSE Arca Exhibit 3A (2021)](https://www.sec.gov/files/rules/sro/nysearca/2021/34-93445-ex3a.pdf), analyzing December 18, 2017 to September 30, 2020: CME Bitcoin futures led every major spot exchange by seconds, not minutes, with full-period lead-lag times of 6.51s (95% CI 5.91 to 7.11s) for Gemini, 6.52s (5.96 to 7.08s) for Bitstamp, 7.28s (6.53 to 8.03s) for Binance, 8.42s (7.65 to 9.18s) for Coinbase, 9.03s (8.33 to 9.73s) for Bitfinex, and 17.19s (16.00 to 18.38s) for Kraken. The filing states: "The results of our TSLL analysis align with the results of our IS/CS analysis and demonstrate that the CME bitcoin futures market leads all evaluated spot trading platforms over the duration of the study."
- UNKNOWN: No published post-2022 empirical study was found showing positive after-cost returns for a slow (seconds-to-minutes) trader hitting lagging Binance.US, Bitstamp, or Gemini quotes.

How it could fool us:
- Backtesting on 1-minute candle closes assumes a stale quote could actually be hit; on a thin book, top-of-book size often vanishes or reprices in milliseconds once a global move starts.
- Cross-venue transfers expose capital to confirmation delays (Crépellière et al. model 2 hours for BTC and 1 hour for ETH) and lump-sum withdrawal fees that dwarf a $250 order.
- A one-venue directional trade (buying Binance.US when it lags an upward move) suffers adverse selection whenever the thin venue is not lagging but reacting to local selling, or whenever the leading venue reverses before the exit.

US retail feasibility and permitted data source:
- INFERENCE: A US customer with $250 can trade Binance.US spot at 0% maker / 0.02% taker (about 7 to 8 bp/side measured once), whereas Kraken, Gemini, and Bitstamp retail taker fees are much higher; however, latency-sensitive stale-quote picking is structurally unsuited to a slow retail API.
- Permitted data source (doc 194): Binance.US public endpoints (kept off-repo until full Terms are read) paired with Bitstamp or Kraken/Gemini public books for private use only; Coinbase is barred.
- Call: SKIP. This matches the existing drop of two-venue inventory gaps in `docs/research/186_round_61_thin_cheap_venue.md`.

## 2. Resting orders on a thin book at 0% maker fee

Mechanism: On a 0% maker venue such as Binance.US, a patient trader posts resting buy limit orders below the market in large coins during sharp falls, hoping panicked market sellers hit the bids and prices rebound. The other side is forced or impatient sellers crossing the spread to exit immediately.

Primary evidence and cost treatment:
- MEASURED (by the cited source) in [Albers et al. (2025, arXiv:2502.18625)](https://ar5iv.labs.arxiv.org/html/2502.18625), a live trading experiment placing 232,897 continuous (Feb 12 to 19, 2024) and 172,800 periodic (Aug 21 to 31, 2024) minimum-sized maker orders on Binance linear Bitcoin perpetual: "For maker orders, we find a negative correlation between fill likelihood and subsequent short-term returns, posing a significant challenge for maker order-based strategies, while the main hurdle with taker orders is overcoming the taker fee."
- MEASURED (by the cited source) in [Albers et al. (2025, arXiv:2502.18625)](https://ar5iv.labs.arxiv.org/html/2502.18625): Across the sample, filled maker orders suffered an expected 5-second markout return of about -0.8 bp gross, or -0.3 bp even after a -0.5 bp maker rebate (Binance.US pays 0 bp, not a rebate). Average 1-second markouts before rebates were negative in all 16 queue-size and queue-position buckets, ranging from -0.058 bp (front 10% of a large near-side queue) to -1.157 bp (back 25% of a large near-side queue). Their 173-feature ML reversal model reached +0.71 bp per round trip only by including 1.0 bp of total maker rebates across both legs, and the authors caution: "Even though we demonstrated an apparently profitable Reversal strategy, it required a relatively sophisticated analysis, offered relatively few trading opportunities, and its scalability is uncertain."
- MEASURED (by the cited source) in [Ślepaczuk (2026, arXiv:2602.00776)](https://arxiv.org/html/2602.00776), studying 1-second Binance Futures order books for BTC, LTC, ETC, ENJ, and ROSE from January 1, 2022 to October 12, 2025: during the October 10, 2025 flash crash, passive maker bids failed catastrophically because informed and directional sellers swept the bids repeatedly: "As the market plummeted, the strategy was repeatedly filled on its bid-side quotes, forcing it to accumulate a growing, and increasingly unprofitable, long position." and "During periods of high volatility and strong directional conviction, like a flash crash, the probability of trading against informed flow increases dramatically."
- MEASURED (from repo `docs/research/170_m121_result.md` and `docs/QUEUE.md` row 121): Our own resting-bid measurement in closed-end funds found a 7.56% fill rate and -26.6 bp average 5-minute markout after fills, closing standalone spread-capture resting bids there.
- UNKNOWN: No published study was found measuring multi-hour (e.g., 24-hour) post-fill net returns of conditional resting bids placed several percent below market on Binance.US spot during sharp falls.

How it could fool us:
- Candle-based backtests that assume a resting bid fills whenever a bar's low touches the limit price overstate returns: in live trading, bids fill 100% of the time when price crashes straight through them and often fail to fill when price bounces at the level.
- Albers et al. state the core mechanism plainly: "Our observations suggest a dilemma: maker orders are either likely to fill but with a negative short-term return (loss-making) or unlikely to fill and having a positive return (failing to realize a profit)."
- On a thin venue like Binance.US, queue priority and book depth during a crash are unmeasured historically; zero maker fee eliminates the 2 bp taker fee, not the adverse-selection loss.

US retail feasibility and permitted data source:
- STATED on [Binance.US fees](https://www.binance.us/fees): A US customer in Idaho with $250 can post 0% maker limit orders on Tier I pairs ("Trade Tier 1 pairs at 0% maker / 0.02% taker.").
- Permitted data source (doc 194): Binance.US public order-book endpoints (kept off-repo) or Kraken/Gemini/Bitstamp private L2 feeds for prospective fill-quality logging; no permitted free historical L3 queue archive exists for Binance.US.
- Call: SKIP standalone resting-bid liquidity provision; WATCH only as a narrow execution overlay on an already-passing crash-rebound rule (such as Plan 76 or E12/E13, consistent with doc 186).

## 3. Venue-specific dislocations (Binance.US 2023 and similar episodes)

Mechanism: A single US exchange's price for a large coin departs from global venues by far more than trading costs for hours or days because of local banking-rail disruptions, withdrawal freezes, or market-maker departures. A trader tries to buy on the discounted venue (or sell on the premium venue) and wait for parity to return.

Primary evidence and cost treatment:
- MEASURED (by the cited source) in [Kaiko (May 9, 2023)](https://www.kaiko.com/resources/binance-halts-withdrawals-as-btc-fees-surge): "In potentially related news, BTC is trading at a 2.5% premium on Binance.US compared with other U.S. exchanges." Kaiko tied the dislocation directly to banking-rail loss and illiquidity: "The premium on Binance.US is more likely related to the exchange's struggles to find a banking partner since the closure of Signature and Silvergate."
- STATED in [Investopedia (June 9, 2023)](https://www.investopedia.com/binance-us-halts-usd-deposits-7510231): After the SEC sought an asset freeze, Binance.US suspended USD deposits on June 9, 2023 and warned that banking partners were expected to pause USD withdrawals as early as June 13, 2023, quoting the exchange: "We encourage customers to withdraw their USD via bank transfer (ACH) by June 13, 2023. Due to elevated volumes and weekend bank closures, ACH withdrawals may take longer than the usual process (e.g. up to several days),"
- STATED on the [Binance.US crypto-only state guide](https://support.binance.us/en/articles/9843321-a-complete-guide-to-using-binance-us-in-a-crypto-only-state): "Most USD Advanced Trading pairs were removed from our platform on June 26, 2023." and "As of February 19, 2025, USD services are available for most supported states."
- UNKNOWN: No peer-reviewed study was found measuring the exact frequency, duration, and net executable return of US single-venue dislocations after banking-rail delays, stablecoin conversion costs, and counterparty failure risk.

How it could fool us:
- The dislocation is usually not free money; it is the market price of trapped fiat or insolvency risk. In May 2023, selling BTC at a 2.5% premium on Binance.US left the seller holding USD on an exchange losing its banking partners. In June 2023, buying discounted BTC/USD required already having USD stuck on Binance.US while USD deposits were suspended.
- Episode count is far too small for statistical testing (one major Binance.US banking-rail crisis in 2023, followed by roughly 20 months with no USD trading on most pairs).
- Even one exchange freeze or bankruptcy (such as FTX or Bittrex) wipes out 100% of capital on the venue, erasing dozens of small dislocation gains.

US retail feasibility and permitted data source:
- INFERENCE: A US customer with $250 could only trade a single-venue dislocation if balances were already sitting on the distressed venue, which directly exposes the account to withdrawal freezes and counterparty loss.
- Permitted data source (doc 194): Private forward monitoring comparing Binance.US public quotes (kept off-repo) against Bitstamp, Kraken, or Gemini public quotes (Coinbase is barred).
- Call: SKIP as a trading strategy. Keep the venue-risk gate from doc 186 and passive monitoring under Measurement 133.

## 4. Slow cross-sectional rules on large coins at daily to weekly horizons

This section checks published after-cost evidence outside the Plan 75 trend family and outside prior skip lists (which already dropped unconditional 1 to 3 day cross-sectional reversal, weekly momentum/size spreads on Coinbase/Kraken, funding carry, and micro-cap hype).

### 4a. Daily volume-shock conditional reversal (liquidity provision)

Mechanism: Buy coins that fell yesterday and short coins that rose yesterday, conditioned on abnormally low trailing trading volume (where liquidity supply is scarce and price impact is temporary rather than informed). Impatient traders demanding immediacy in quiet markets are on the other side.

Primary evidence and cost treatment:
- MEASURED (by the cited source) in [Bianchi, Babiak and Dickerson (Sveriges Riksbank Working Paper No. 413, 2022)](https://www.riksbank.se/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf), studying the top 100 most liquid USD pairs across >80 exchanges from March 1, 2017 to March 1, 2022: "We provide empirical evidence within the context of cryptocurrency markets that the returns from liquidity provision, proxied by the returns of a short-term reversal strategy, are primarily concentrated in trading pairs with lower levels of market activity."
- MEASURED (by the cited source) in [Bianchi, Babiak and Dickerson (2022)](https://www.riksbank.se/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf) Table 5 (net of stated 20 bp long / 30 bp short in the Table 5 caption; main text states 30/40 bp): Equal-weighted low-volume reversal earned +0.726% per day (p < 0.01), but value-weighted low-volume reversal fell to +0.125% per day (not significant), and value-weighted medium-volume (-0.570% per day) and high-volume (-0.687% per day) reversals were strongly negative. The authors state: "For larger, more liquid, and less volatile assets the reversal strategy returns tend to be close to zero and are not statistically significant."
- MEASURED (by the cited source) in [Bianchi, Babiak and Dickerson (2022)](https://www.riksbank.se/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf) Table 7 (individual exchanges, Binance USDT pairs October 1, 2018 to March 1, 2022): Binance low-volume reversal earned only +0.187% per day gross (+18.7 bp) equal-weighted and +0.059% per day gross (+5.9 bp) value-weighted, turning negative net of costs at -0.213% per day equal-weighted and -0.341% per day value-weighted (both p < 0.01).
- INFERENCE (arithmetic netting of Table 7 Binance gross figures on daily turnover): Even at 10 bp per side (20 bp round trip), Binance low-volume reversal nets -1.3 bp per day equal-weighted and -14.1 bp per day value-weighted; at 75 bp per side (150 bp round trip), it nets -131.3 bp per day equal-weighted and -144.1 bp per day value-weighted.
- MEASURED (by the cited source) in [Farag, Luo, Yarovaya and Zieba (2025, Journal of Banking & Finance 175:107411)](https://pure-oai.bham.ac.uk/ws/portalfiles/portal/264447617/Farag2022Returns.pdf): A separate Nagel-style short-reversal liquidity-provision measure on 122 Coinpaprika coins (January 1, 2017 to December 31, 2022) reports a 0.720% mean per 5-minute interval (SD 4.526%), stating: "We obtain data on 5-minute cryptocurrency prices, market capitalization, and trading volume from Coinpaprika.com for the period between January 1, 2017, and December 31, 2022." However, the strategy formula includes no transaction-cost term, requires 5-minute rebalancing, and requires shorting, making it unexecutable on a $250 US cash-spot account.

How it could fool us:
- Aggregated multi-exchange indices (CryptoCompare across >80 exchanges) mix thin offshore venues (HitBTC, GateIO) with liquid venues; once restricted to Binance or large value-weighted coins, the daily reversal disappears and turns negative after costs.
- The strategy is long-short; a small US cash-spot account cannot short the winner leg.

US retail feasibility and permitted data source:
- INFERENCE: Not feasible as a profitable long-only cash-spot rule on Binance.US or Kraken; gross returns on large coins are already below 10 bp per side.
- Permitted data source (doc 194): Binance Vision (CC BY-NC-SA 4.0) for historical verification; Kraken OHLCVT / Bitstamp for private US checks.
- Call: SKIP.

### 4b. Weekly multi-indicator cross-sectional factors and size screens

Mechanism: Sort the top 100 coins weekly by combined price and volume technical indicators (CTREND) or by market capitalization, buying top-ranked coins and shorting bottom-ranked coins to capture slow retail underreaction or neglect premia.

Primary evidence and cost treatment:
- MEASURED (by the cited source) in [Pang and Wang (November 2026, arXiv:2611.01951v1)](https://arxiv.org/html/2611.01951v1), reassessing Fieberg et al. (2025, JFQA) CTREND over 2014 to 2022 (335 cost-computable weeks): on the uncleaned universe (D0), the long-short CTREND factor earns +0.102% per week gross and -0.869% per week net (Sharpe -0.157) at the lowest assumed fee schedule (30 bp long / 40 bp short), and -1.415% per week net at 50/60 bp. On the 100 largest cryptocurrencies (D0), gross return is +1.00% per week and net return at 30/40 bp is +0.10% per week (t = 0.08). Only after whole-history exclusions of INNBCL and 27 event-related assets (D2) does full-universe long-short CTREND reach +1.619% per week net at 30/40 bp (95% HAC CI 0.091% to 3.148%), dropping to +1.079% per week (CI -0.455% to 2.613%, not significant) at 50/60 bp. The authors note: "At the lowest assumed fees, the P0/M1/D1 mean is 1.770% per week, with a HAC interval of [0.241%, 3.299%]; D2 gives 1.619%, with interval [0.091%, 3.148%]." and "Proportional trading fees do not measure whether a required position can be opened at scale." No standalone long-only net return series is reported.
- INFERENCE (netting at 10 bp vs 75 bp per side): Because the largest-100 D0 net return at 30/40 bp is +0.10% per week (t = 0.08, implying ~90 bp per week of cost drag from high turnover), cutting costs to 10 bp per side still leaves a weak, noisy gross return (~1.00% gross on D0, t = 0.80), while 75 bp per side pushes even the cleaned D2 long-short factor near or below zero.
- MEASURED (by the cited source) in [arXiv:2610.23283v2 (October 2026)](https://arxiv.org/html/2610.23283v2), testing 8,970 coins across 690 weekly cross-sections from April 28, 2013 to July 12, 2026: "The bottom decile earns 27.5% per week on paper and nothing among assets that trade, on capacity of $293,000." and "Compensation for neglect exists precisely where trading does not." In the consolidation era with a $1,000,000 daily volume screen, re-formed decile returns rise weakly with size (-2.00% per week in decile 1 to -0.08% per week in decile 10), and the screened full-universe bottom decile earns -2.71% per week gross and -3.69% per week net of 2% costs.

How it could fool us:
- Headline factor papers rely on shorting illiquid coins, excluding specific historical outliers, and CoinMarketCap-style universes with uninvestable micro-caps.
- Re-running on a 20-coin US cash-spot universe without shorting removes the short leg that drives most reported alpha.

US retail feasibility and permitted data source:
- INFERENCE: Long-short weekly factor strategies are not executable on a $500 US cash-spot account, and no robust long-only large-coin net edge is shown.
- Permitted data source (doc 194): Binance Vision (CC BY-NC-SA 4.0) for historical backtesting; Kraken OHLCVT / Bitstamp for private checks.
- Call: SKIP.

### 4c. Weekly low-volatility / minimum-variance allocation across large coins

Mechanism: Rebalance weekly across a small basket of large coins using trailing volatility or minimum-variance weights instead of equal weight or return forecasts. Retail traders often chase high-volatility altcoins for lottery payoffs; overweighting lower-volatility large coins reduces drawdown and turnover.

Primary evidence and cost treatment:
- MEASURED (by the cited source) in [MDPI Risks 14(11):256 (November 2026)](https://www.mdpi.com/2227-9091/14/11/256/pdf), testing five large coins (BTC, ETH, BNB, SOL, XRP) from January 22, 2022 to January 14, 2026, with a 724-day rolling out-of-sample evaluation (January 22, 2024 to January 14, 2026) at weekly rebalancing and a proportional transaction cost of 10 bp per unit traded: Rolling minimum-variance achieved a net Sharpe of 1.37 (excess Sharpe 1.28, gross 1.38) at 1.8x annualized turnover, and rolling minimum-CVaR achieved a net Sharpe of 1.25 (1.9x turnover), compared with equal weight at 1.15 net Sharpe (2.5x turnover). High-turnover optimizers lost to equal weight: rolling maximum-Sharpe scored 0.92 net Sharpe (8.0x turnover) and GARCH-DCC minimum-variance scored 0.94 net Sharpe (25.1x turnover).
- MEASURED (by the cited source) in [MDPI Risks 14(11):256 (November 2026)](https://www.mdpi.com/2227-9091/14/11/256/pdf): The authors conclude cautiously: "Optimization lowers risk, whereas evidence that it improves risk-adjusted performance is inconclusive." and "The evidence thus does not support the claim that conditional covariance modelling adds value to a long-only five-asset allocation at a weekly rebalancing frequency; its contribution lies in risk measurement and monitoring, not in portfolio construction."
- INFERENCE (netting at 10 bp vs 75 bp per side): At 1.8x annual turnover, 10 bp per side costs about 0.18% per year and 75 bp per side costs about 1.35% per year, so slow minimum-variance weighting survives both cost levels in fee drag, unlike GARCH-DCC (25.1x turnover, ~18.8% per year drag at 75 bp).
- STATED in [Pyo and Jang (2026, Finance Research Letters 97:109851, RePEc abstract)](https://ideas.repec.org/a/eee/finlet/v97y2026ics1544612326003818.html): "Contrary to early evidence suggesting that high-volatility cryptocurrencies earn higher returns, we document a statistically and economically meaningful low-volatility premium in the post-2017 period." Full text is paywalled, so exact large-coin net-of-cost numbers and whether the result is long-only or long-short are UNKNOWN.

How it could fool us:
- On a 5-coin basket in 2024 to 2026, minimum-variance largely acts as a heavy Bitcoin tilt because Bitcoin has the lowest realized volatility; it may simply reflect Bitcoin outperforming altcoins in that 2-year window rather than a general cross-sectional edge.
- It is a long-only allocation benchmark (always invested in crypto beta), not an absolute-return trading edge that protects capital in a crypto bear market.

US retail feasibility and permitted data source:
- INFERENCE: Fully feasible for a $500 US cash-spot account on Binance.US (0% maker / 0.02% taker, 1 USDT minimum, Idaho supported) or Kraken/Bitstamp, because it is long-only, weekly, and low turnover.
- Permitted data source (doc 194): Binance Vision (CC BY-NC-SA 4.0) for historical backtests on top 10 to 20 coins; Kraken OHLCVT or Bitstamp for private US-venue checks.
- Call: WATCH as a passive risk-sizing benchmark only, not a standalone profit test.

## 5. Breadth and patience on doc 194 usable data

Mechanism: Use an automated agent's patience and ability to watch many coins or events 24/7 without chasing speed, restricted strictly to data sources cleared in `docs/research/194_data_source_terms_audit.md` (Binance Vision CC BY-NC-SA 4.0 for history, Kraken/Gemini/Bitstamp/Binance.US for private venue checks, plus AlphaGrowth unlocks, DefiLlama, SEC EDGAR, and Treasury Fiscal Data).

Primary evidence and cost treatment:
- MEASURED (by the cited source) in [arXiv:2606.00060 (May 2026)](https://arxiv.org/html/2606.00060), testing 70,128 hourly BTC/USDT evaluation bars from January 1, 2018 through 2025 (27 walk-forward folds) at 10 bp transaction costs: naive sign-based ML strategies collapse once 10 bp costs are applied (long-only XGBoost drops from +73.50% gross ARC to -64.00% net ARC; LSTM drops from +72.43% to -50.65%; iTransformer drops from +129.07% to -83.93%). Adding a cost-aware execution threshold cuts long-only XGBoost to 251 trades and restores +65.40% net ARC (Sharpe 1.09) in the selected configuration; the authors write: "The main result is that prediction quality matters only after the execution rule decides which forecasts are worth trading." Stability across out-of-sample coins, 75 bp costs, and unchosen hyperparameters is UNKNOWN.
- INFERENCE: Across the five areas checked in this round, no new thin-venue or cross-sectional crypto edge clears the bar for a `test` or `count first` call. The one crypto mechanism with honest empirical support for a slow, patient cash-spot desk remains buying forced or panicked washouts (already in build as Plan 76, with cheap-venue forward checks E12, E13, and Measurement 133 on Binance.US).

How it could fool us:
- Mistaking "cheap fees on Binance.US" for "an edge on Binance.US": doc 180 already showed that 23 of 44 prior repo tests lost before costs. Lowering costs from 75 bp to 8 bp per side cannot rescue rules whose gross return on large coins is zero or negative.
- Building a high-turnover rule on Binance Vision history (which bars live proprietary execution under CC BY-NC-SA 4.0) and assuming Binance.US thin books will match Binance global fills.

US retail feasibility and permitted data source:
- INFERENCE: Any future slow, broad crypto test must be long-only, have low enough turnover or large enough per-trade gross moves to clear 10 bp/side easily (and ideally survive stress testing), and use Binance Vision for historical screening plus Kraken/Bitstamp/Binance.US (off-repo) for private venue verification.
- Call: SKIP new ML/thresholded single-coin forecasting; keep effort focused on Plan 76 and Measurement 133.

## Summary table

| Idea | Mechanism | Best primary evidence (costs noted) | US $250 venue | Permitted data (doc 194) | Call |
|---|---|---|---|---|---|
| 1. Lagging-venue prices (seconds to minutes) | Hit stale thin-venue quotes after global move | [Crépellière et al. 2022](https://en.wiwi.uni-paderborn.de/fileadmin-wiwi/cetar/TAF_Working_Paper_Series/TAF_WP_067_CrepellierePelsterZeisberger2022_rev.pdf): US net -16 bp, max-fee -12 bp (no withdrawal fee); [SEC Ex 3A](https://www.sec.gov/files/rules/sro/nysearca/2021/34-93445-ex3a.pdf): lags are 6.5s to 17.2s | Binance.US (0% / 0.02%), but latency kills it | Binance.US (off-repo) + Bitstamp/Kraken/Gemini (private) | SKIP |
| 2. Resting orders on 0% maker book | Post bids below market during falls | [Albers et al. 2025](https://ar5iv.labs.arxiv.org/html/2502.18625): -0.8 bp gross 5s markout, -0.3 bp with rebate; [Ślepaczuk 2026](https://arxiv.org/html/2602.00776): bids swept in crash | Binance.US Tier I (0% maker) | Binance.US / Kraken / Bitstamp private L2 books | SKIP standalone; WATCH as Plan 76 overlay |
| 3. Venue-specific dislocations | Buy/sell one-venue gap (Binance.US 2023) | [Kaiko 2023](https://www.kaiko.com/resources/binance-halts-withdrawals-as-btc-fees-surge): 2.5% premium; [Investopedia 2023](https://www.investopedia.com/binance-us-halts-usd-deposits-7510231) and [Binance.US](https://support.binance.us/en/articles/9843321-a-complete-guide-to-using-binance-us-in-a-crypto-only-state): USD halted 2023-06 to 2025-02; net UNKNOWN | Binance.US (requires trapped balances / bank risk) | Binance.US (off-repo) + Bitstamp/Kraken (private) | SKIP |
| 4a. Daily volume-shock reversal | Buy losers / short winners in low volume | [Bianchi et al. 2022](https://www.riksbank.se/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf): Binance net -0.213% EW / -0.341% VW per day; large coins ~0 | Not feasible (short leg + negative net) | Binance Vision (CC BY-NC-SA 4.0) / Kraken OHLCVT | SKIP |
| 4b. Weekly CTREND / size factors | Sort top 100 coins on technicals or size | [Pang & Wang 2026](https://arxiv.org/html/2611.01951v1): D0 top-100 net +0.10%/wk (t 0.08) at 30/40 bp; [arXiv:2610.23283v2](https://arxiv.org/html/2610.23283v2): $1M screen size gone | Not feasible (short leg + weak D0) | Binance Vision (CC BY-NC-SA 4.0) / Kraken OHLCVT | SKIP |
| 4c. Weekly min-variance / low-vol sizing | Weight large coins by low volatility | [MDPI Risks 2026](https://www.mdpi.com/2227-9091/14/11/256/pdf): 5 coins OOS net Sharpe 1.37 (1.8x turn) vs EW 1.15 at 10 bp; inconclusive risk-adj gain | Binance.US / Kraken / Bitstamp (long-only) | Binance Vision (CC BY-NC-SA 4.0) / Kraken OHLCVT | WATCH (risk benchmark only) |
