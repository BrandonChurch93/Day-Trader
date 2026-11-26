# Round 15: Forced and Scheduled Crypto Events Reachable by a US Spot Account

Date: 2026-11-26
Scout: idea_scout
Constraint: Small and mid-size coins reachable long-only, no leverage, on US spot venues (Coinbase, Kraken, Robinhood) with multi-year published or measurable history. No returns computed.

## US Spot Cost Floor (2026 Published Entry Tiers)

Published 2026 US retail spot fee schedules set a steep hurdle for any long-only event entry on small and mid-size coins.

| Venue and Product | Entry Tier Requirement | Maker Fee (per side) | Taker Fee (per side) | Fee-Only Round-Trip | Notes |
|---|---|---|---|---|---|
| Coinbase Advanced (US spot) | Under $10,000 30-day volume | 0.50% | 0.90% | 1.00% to 1.80% | Plus order-book bid-ask spread and slippage |
| Kraken Pro (Tier 1 spot) | $0+ 30-day volume | 0.40% | 0.80% | 0.80% to 1.60% | Drops at $2,500+ 30-day volume; plus spread |
| Robinhood Crypto (default) | Market-maker routing | 0% commission | 0% commission | ~1.90% (spread) | ~0.95% spread markup per side included in quote |
| Robinhood Crypto (Exchange Routing) | $0 to $10,000 30-day volume | 0.50% (reduced) | 0.95% (standard) | 1.00% to 1.90% | Plus partner exchange spread |

- **Coinbase Advanced and Kraken Pro:** STATED at [NachoNacho](https://nachonacho.com/software-comparisons/coinbase-vs-kraken): "At their published entry U.S. spot tiers, Coinbase Advanced lists 0.50% maker and 0.90% taker fees, while Kraken Pro lists 0.40% maker and 0.80% taker fees." Confirmed at [Kraken Learn](https://www.kraken.com/learn/kraken-vs-coinbase): "Spot fees on Kraken Pro start at 0.40% maker and 0.80% taker at the base tier."
- **Robinhood Crypto:** STATED at [Robinhood Crypto Standard Pricing Fee Schedule](https://cdn.robinhood.com/assets/robinhood/legal/rhc-fee-schedule.pdf): "Volume Tier Standard Fee Reduced Fee $0-$10K 0.95% 0.50% $10K-$50K 0.75% 0.35% $50K-$250K 0.25% 0.125%"
- **Cost implication:** A long-only entry and exit on a small or mid-size coin at a US retail spot venue faces roughly 1.0% to 2.5% all-in round-trip friction once small-cap bid-ask spreads and event-window slippage are added. By contrast, an AVOID or immediate EXIT rule on a negative event pays at most one-way exit cost (0.40% to 0.95% plus spread) to sidestep large multi-day drawdowns.

## Lead-Agent Rulings

None of the 13 candidates becomes a profit test, because the only strong post-notice effect is an avoid signal and a US spot account cannot short.

- **Delisting notices (queue row 72):** Recorded as a candidate desk rule ("exit a held coin at once on a delisting notice from a major exchange"), not a profit trial; queued as row 72 ("harness rule candidate, to be written into the desk rule set when TM07 lands").
- **Large scheduled cliff unlocks as avoid (folded into queue row 36):** Folded into existing row 36 (the token-unlock logger) with the three new sources (Keyrock Dec 2024, Kim 2026 SSRN 6632838, Albiez 2026 SSRN 7567460) and the drift-controlled design note separating 30-day pre-unlock drift from 3-day post-unlock reaction. No new queue row.
- **Binance spot listings of coins already on US venues (queue row 73):** Queued as row 73, WATCH; first step is an event count for 2021 to 2026 from public listing notices (count only).
- **Airdrop snapshot dates:** WATCH noted in this document only (no queue row).
- **Nine remaining families:** Dropped (no queue rows). Prior crypto work in Rounds 1 to 14 is skipped unless new evidence applies, including Replay 19 (Monday Asia crypto window), Replay 20 (Upbit listing short), Replay 09 (seven crypto methods at Alpaca fees), negative perpetual funding, Round 11 (CME Bitcoin monthly expiry), and Round 13 (crypto weekend, time-of-day, and spot Bitcoin ETF creation flows).

## Verdict Summary

| # | Event Family | Role for US Spot | Stated Post-Notice Effect | US Spot Cost Hurdle | Ruling / Disposition |
|---|---|---|---|---|---|
| 1 | Exchange delisting notices (Binance, Kraken, Coinbase) | Avoid / immediate exit | -16.8% median 24h, -32.7% 7d (Binance, from +3 min) | 0.40% to 0.95% one-way exit | Desk rule candidate (queue row 72) |
| 2 | Large scheduled cliff token unlocks | Avoid signal | Split: -16.97% 72h (n=52) vs -0.14% 3d (n=913) | 0% to avoid new buys | Folded into existing row 36 |
| 3 | Binance spot listings on already-US-listed coins | Long-only entry | ~+7% median BTC-adj by Day 9 (n=14); broad 0.0% 1h / -0.1% 24h | 1.0% to 2.5% RT | WATCH (queue row 73, count first) |
| 4 | Airdrop snapshot dates (parent coin) | Avoid / exit before snapshot | -4.65% immediate, -12.29% 5d post-distribution | 0.40% to 0.95% one-way exit | WATCH (doc only, no queue row) |
| 5 | Coinbase listing announcements and roadmap adds | Long-only entry | Front-loaded pre-Day 0; median turns negative after 1d | 1.0% to 2.5% RT | DROP |
| 6 | Robinhood crypto listing announcements | Long-only entry | Post-intro order imbalance shifts to net sales; front-run >1h | 1.0% to 2.5% RT | DROP |
| 7 | Kraken listing announcements | Long-only entry | Late-stage venue; sharp post-listing declines reported | 1.0% to 2.5% RT | DROP |
| 8 | Grayscale (GDLC) and Bitwise (BITW) index rebalances | Long-only entry | UNKNOWN; forced flow ~$2M to $15M in top-10 coins | 1.0% to 2.5% RT | DROP |
| 9 | Coinbase 50 Index (COIN50) quarterly changes | Long-only entry | UNKNOWN; not pre-announced publicly; ~3 tracking products | 1.0% to 2.5% RT | DROP |
| 10 | Scheduled token burns and protocol buybacks | Long-only entry | Buyback-and-burn -35% avg; burn events -13.3 pp 30d | 1.0% to 2.5% RT | DROP |
| 11 | Mainnet launch dates | Long-only entry | Positive only 47% of the time; sell-the-news | 1.0% to 2.5% RT | DROP |
| 12 | Stablecoin mint and treasury supply jumps (USDT/USDC) | Market-wide long | 0% at 12h, +0.63% weakly sig at 24h; 5 to 30 min fade | 1.0% to 1.8% RT | DROP |
| 13 | Altcoin scheduled halvings and emission cuts | Long-only entry | Negative CAR around halving; no 6m outperformance | 1.0% to 2.5% RT | DROP |

## Retained Candidates (Desk Rule, Row 36 Addition, and WATCH)

### 1. Exchange Delisting Notices as a Desk Rule Candidate (Queue Row 72)

Who is forced to trade and when: Every spot holder on the delisting exchange who does not want to withdraw on-chain or be stranded must liquidate before the trading-halt deadline (typically 7 to 14 days on Kraken, 2 to 4 weeks on Binance and Coinbase), while market makers pull bids immediately upon notice. [OurCryptoTalk](https://ourcryptotalk.com/reports/how-exchange-delistings-destroy-web3-projects-overnight): "Between January and mid-May 2026, Binance ran three batch delistings (19 tokens) and Kraken removed 28" and notice periods run 7 to 14 days on Kraken and 2 to 4 weeks on Binance and Coinbase.

Best published evidence and post-publication persistence: MEASURED across 2,843 coins in 1,842 official announcements from August 2022 through November 2026 on Binance, Bybit, OKX, Upbit, and Bithumb, priced 3 minutes after publication so a fast reader could actually execute. [CoinSight](https://getcoinsight.com/en/research/exchange-announcement-study): "Binance delisting notices: from 3 minutes after the notice, the median coin was -16.8% after 24 hours (-16.6% relative to BTC) and -32.7% after 7 days, and 20% of coins fell more than 30% within a day (n = 95)." Across all five exchanges combined (n = 395 delistings), the median move from +3 minutes was -6.8% at 24 hours (-7.0% vs BTC) and -16.2% at 7 days, whereas the control group of single trading-pair removals (n = 635) had a +0.1% median 24-hour move. [CoinSight](https://getcoinsight.com/en/research/exchange-announcement-study): "Control group: when an exchange removes just one trading pair, the median 24-hour move is +0.1% (n = 635)" Earlier academic event-study evidence matches the asymmetry. [Oget 2022 via RePEc](https://ideas.repec.org/a/ahs/journl/v7y2022i1p16-31.html): "As a result of the analysis, 22 significant abnormal return values related to negative events and eight significant abnormal return values related to positive events were determined at 1% significance level within the event window (-5, +10)."

Free and lawful historical source of event timestamps: Official exchange announcement archives and public RSS/support pages (Binance Support Announcements, Kraken Support delisting notices such as [Kraken Support](https://support.kraken.com/articles/asset-delistings-november-2026), and Coinbase Assets public X posts at [@CoinbaseAssets](https://x.com/CoinbaseAssets)).

US spot cost vs stated effect: Paying 0.40% to 0.95% one-way taker fee plus spread to exit immediately upon a major-exchange delisting notice avoids a -16.8% median 24-hour drop and -32.7% 7-day drop.

Ruling: Candidate desk rule ("exit a held coin at once on a delisting notice from a major exchange"), not a profit trial; queued as row 72 to be written into the desk rule set when TM07 lands.

### 2. Large Scheduled Cliff Token Unlocks as an Avoid Signal (Folded into Queue Row 36)

Who is forced to trade and when: Early investors, VCs, and core team members whose tokens vest on a fixed smart-contract cliff date gain liquidity to monetize holdings, while speculators sell ahead of the known supply overhang.

Best published evidence and post-publication persistence: Published results are split between broad 30-day studies and a 2026 drift-adjusted 3-day study. On the negative side, [Keyrock](https://keyrock.com/from-locked-to-liquidity-what-16000-token-unlocks-teach-us/) studied over 16,000 unlock events across 40 tokens (published December 2024): "90% of unlocks create negative price pressure, regardless of size or type." and "Token price impacts often start 30 days before the unlock event." [6th Man Ventures](https://6thman.ventures/writing/token-unlocks) analyzed over 5,000 unlocks across 20 protocols (2023): "Small unlock events, those that increase circulating supply by 0% to 1%, had no meaningful relationship to price." and "Larger unlocks, those that increase circulating supply by greater than 1%, correlated to a noticeable, negative relationship: as unlock size increased, prices decreased." More recently, [Kim 2026 (SSRN 6632838)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6632838) examined 52 major Binance-listed unlock events from January 2023 to December 2025: "First, 46 of 52 events (88.5%; binomial test p = 2.2 × 10⁻⁹; robust to Bonferroni correction across 17 formal hypothesis tests) exhibit negative returns within 72 hours of unlock, with a mean return of-16.97%." However, a larger 2026 academic study contradicts the 3-day shock claim once baseline token drift is removed. [Albiez 2026 (SSRN 7567460)](https://papers.ssrn.com/sol3/Delivery.cfm?abstractid=7567460) tested 913 scheduled cliff unlocks of Binance-listed tokens: "Markets absorb unlocks far better: net of token-specific drift, prices show no detectable three-day response (market-model abnormal return-0.14%, 95% CI-0.81% to +0.53%)."

Free and lawful historical source of event timestamps: Free public unlock calendars on Tokenomist, CoinMarketCap, and DefiLlama, plus the repo's existing unlock logger. [Kim 2026 GitHub summary](https://github.com/fivetaku/vibe-investing-toss/blob/main/01.Trading%20Strategy/Token%20unlock%2072h%20shock%20analysis%20/Token%20unlock%2072h%20shock%20ssrn%20v3%201%20en.MD): "freely available on platforms such as Tokenomist, CoinMarketCap, and DefiLlama"

US spot cost vs stated effect: Avoiding new long entries ahead of a cliff unlock exceeding 1% to 5% of circulating supply costs 0 bps in extra fees. Because Albiez (2026) found -0.14% abnormal return over the 3-day window across 913 cliffs while Keyrock and 6th Man Ventures found multi-week pre-unlock weakness, any test on the existing unlock logger must separate the 30-day pre-unlock window from the 3-day post-unlock reaction and control for baseline token drift.

Ruling: Folded into existing queue row 36 with the three new sources and the drift-controlled design note; no new queue row.

### 3. Binance Spot Listing Announcements on Coins Already Listed on US Venues (Queue Row 73, WATCH)

Who is forced to trade and when: Global retail traders, offshore market makers, and momentum bots on Binance acquire spot inventory when Binance opens trading on a token that was previously listed on Coinbase or Kraken but not yet on Binance.

Best published evidence and post-publication persistence: Broad Binance spot listings no longer work as a post-announcement long trade. MEASURED across 87 Binance spot listings from August 2022 to November 2026, [CoinSight](https://getcoinsight.com/en/research/exchange-announcement-study) found that entering 3 minutes after publication produced a median return of 0.0% at 1 hour, -0.1% at 24 hours (-0.5% vs BTC), and -6.1% at 7 days. Over longer horizons, [Empirica](https://empirica.io/blog/the-binance-effect-a-7-year-analysis-for-token-founders/) analyzed all Binance listings since 2017 and found: "The cumulative price change for tokens listed on Binance in 2024 is -31.20% compared to the market, which is a big underperformance." Earlier studies from 2017 to 2022 showed large spikes (for example, [Amsden 2019](https://spectrum.library.concordia.ca/id/eprint/985163/1/Amsden_MSc_S2019.pdf) reported a two-day CAR(0,1) of 13.6% on 44 listings from September 2017 to June 2018), which faded after publication. However, one narrow sub-cohort directly relevant to US spot accounts showed a different pattern in 2026. [The TIE](https://www.linkedin.com/pulse/what-does-binance-listing-actually-buy-thetie-sdiuc) studied 14 tokens that received a Binance spot listing after already trading on three or more major exchanges (including Coinbase and Kraken): "The median BTC-adjusted return for this cohort continues to drift upward after Day 0, reaching a post-listing peak of roughly 7% around Day 9 before fluctuating near flat through approximately Day 21 and then entering a more sustained decline."

Free and lawful historical source of event timestamps: Official Binance Support New Listings announcements and public exchange listing logs; US spot prices from Coinbase and Kraken public OHLCV APIs.

US spot cost vs stated effect: Round-trip cost of 1.0% to 2.5% on Coinbase Advanced or Kraken Pro is smaller than the ~7% median 9-day BTC-adjusted drift reported by The TIE, but the sample is only 14 tokens and broad Binance listings (n = 87) are flat to negative after minute +3.

Ruling: Queued as row 73, WATCH. First step is an event count for 2021 to 2026 from public listing notices (count only).

### 4. Airdrop Snapshot Dates as a Long-Only Avoid Signal (WATCH, Doc Only)

Who is forced to trade and when: Speculators who bought a parent coin solely to qualify for a snapshot-based airdrop or hard fork sell immediately after the snapshot block is taken, while recipients who claim the new token rapidly liquidate it.

Best published evidence and post-publication persistence: MEASURED across 67 hard fork and airdrop events from 2014 to 2020, [Liebi 2022 (University of St. Gallen / SSRN 4174286)](https://alexandria.unisg.ch/server/api/core/bitstreams/109f497f-c2d6-4e53-9213-626d6d13c957/content) found no pre-announcement edge and a sharp post-snapshot drop: "The announcement of a hard fork or airdrop does not affect parent coin prices. In contrast, the distribution of coins immediately decreases the prices of the parent coin by 4.65%. The cumulative average abnormal return over the 5-day post-distribution date equals -12.29%." For newly claimed airdrop tokens themselves, [Messias et al. 2023 (arXiv 2312.02752)](https://arxiv.org/html/2312.02752) studied nine major Ethereum and Layer-2 airdrops: "are rapidly sold, often in recipients' first post-claim transaction." (up to 66% of claimed tokens in some cases). Post-2020 persistence for pre-announced parent-coin snapshots is UNKNOWN because most modern DeFi airdrops use retroactive or unannounced snapshots to deter farming.

Free and lawful historical source of event timestamps: No clean, single free multi-year historical database of pre-announced snapshot dates exists; events must be reconstructed from project governance forums, official blogs, and exchange support notices.

US spot cost vs stated effect: Coinbase, Kraken, and Robinhood rarely distribute third-party on-chain airdrops to spot custody accounts, so a US spot holder who sits through a known parent-coin snapshot absorbs the -4.65% to -12.29% post-snapshot drop without receiving the offsetting airdrop.

Ruling: WATCH noted in this document only (no queue row).

## Dropped Candidates (DROP)

### 5. Coinbase Listing Announcements and Asset Roadmap Additions (DROP)

Who is forced to trade and when: US retail and institutional accounts restricted to Coinbase can buy only after trading opens, while speculators on other venues trade the public Asset Roadmap notice (introduced April 11, 2022) and the separate listing announcement.

Best published evidence and post-publication persistence: Pre-2022 studies documented large average pops (for example, [Li (Loyola)](https://www.loyola.edu/_media/sellinger-business/documents/academics/departments/finance/wealth-management-conference/speakers/J_Li.pdf): "For example, the average first day returns around listing announcement on Coinbase is 32.8%, and that on Binance is 22.7%." and [Messari via Yahoo Finance](https://finance.yahoo.com/news/coinbase-effect-means-average-91-161123386.html): "Coinbase listings have the highest average return standing at 91%, but also have the widest distribution of ranging from -32% to 645%"), but those returns were heavily front-run and skewed by outliers. [Felez-Vinas, Johnson, and Putnins (SSRN 4184367)](https://www.scribd.com/document/883521869/ssrn-4184367) studied 146 Coinbase listings from September 2018 to May 2022: "On average, there is a 19.9% run-up in cumulative abnormal returns prior to the announcement. On the announcement day, the tokens have an average return of 6.1% because of new information". Post-2022 evidence shows rapid mean reversion. [The Block](https://www.theblock.co/research/institutional/measuring-the-coinbase-effect-34648): "We found that Coinbase listing announcement provides a median return of 7% for an asset" and "However, this effect appears to be short-lived as median returns turn negative after one day". Across 1,844 listing events on five major exchanges from January 2023 to June 2026, [The TIE](https://www.thetie.io/insights/what-does-an-exchange-listing-actually-deliver-in-2026) concluded: "Once the token starts trading on the new venue, the move largely dissipates, with the adjusted return going flat or turning negative shortly after listing." and "From a price return perspective, no exchange consistently delivers a superior BTC-adjusted outcome." For roadmap additions specifically, roughly one-third never even list. [CryptoRank citing CryptoCompare 2024](https://cryptorank.io/news/feed/e5de1-coinbase-kat-listing-roadmap-2025): "However, the same study noted that only approximately 65% of roadmap assets ultimately receive full listing approval."

Free and lawful historical source of event timestamps: Coinbase blog and official [@CoinbaseAssets](https://x.com/CoinbaseAssets) X posts.

US spot cost vs stated effect: A US spot account cannot buy a coin on Coinbase before Coinbase lists it, so the trader is restricted to coins already on Kraken or Robinhood, must beat sub-minute bots after the announcement, and faces 1.0% to 2.5% round-trip fees on a median move that turns negative after Day 1.

Verdict: DROP.

### 6. Robinhood Crypto Listing Announcements (DROP)

Who is forced to trade and when: Robinhood retail accounts gain access on listing day, while market makers who receive Robinhood's payment for order flow (PFOF) internalize retail flow rather than sending directional market orders to public order books.

Best published evidence and post-publication persistence: MEASURED by [Boulton, Shohfi, Walz, and Miller (SEC DERA Working Paper 2501 / SSRN 4961610)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4961610): "Using Robinhood Crypto token introductions as a PFOF shock, we find that trading volume decreases for most crypto assets except Bitcoin and Ethereum after the token introductions. In addition, after the shock, order imbalances shift to net sales, while average trade sizes, implied spreads, and return volatility generally rise." Separate market-microstructure monitoring also flagged pre-announcement front-running. [BitRss citing Kaiko](https://bitrss.com/kaiko-flags-frontrunning-risk-ahead-of-robinhood-token-listings-207656): "A Kaiko data debrief points to conspicuous activity that, in some cases, preceded public signals by more than an hour and could reflect either privileged access or highly effective front-running strategies based on public indicators."

Free and lawful historical source of event timestamps: Robinhood Newsroom press releases and official Robinhood X announcements; spot prices on Coinbase and Kraken.

US spot cost vs stated effect: Post-introduction order imbalances shift to net sales and spreads widen, offering no positive post-announcement drift to cover 1.0% to 2.5% US spot round-trip fees.

Verdict: DROP.

### 7. Kraken Listing Announcements (DROP)

Who is forced to trade and when: Kraken users gain access, but Kraken typically lists mid-size assets well after Binance, OKX, Bybit, or Coinbase, so no large trapped pool of forced buyers arrives.

Best published evidence and post-publication persistence: [The TIE](https://www.thetie.io/insights/what-does-an-exchange-listing-actually-deliver-in-2026) (1,844 events, January 2023 to June 2026): "Kraken consistently appears as a later-stage listing rather than an initial one." Earlier academic samples for Kraken were tiny and statistically insignificant ([Ante 2019, BRL Working Paper 3](https://www.blockchainresearchlab.org/wp-content/uploads/2019/10/Exploring-Market-Reactions-to-Exchange-Listings-of-Cryptocurrencies-BRL-working-paper3.pdf): "The two US-based exchanges Poloniex and Kraken have exclusively positive (though insignificant) event returns (their samples each comprise three listings each)."). Recent secondary-listing studies report negative post-listing performance on Kraken. [ChainCatcher](https://www.chaincatcher.com/en/article/2175717): "while Kraken and KuCoin also performed poorly in the 7-day period, especially Kraken, which saw declines of -23.5% and -27.9% in January and March, respectively."

Free and lawful historical source of event timestamps: Kraken Blog and official Kraken X listing announcements.

US spot cost vs stated effect: Negative recent 7-day post-listing returns fail to clear 0.80% to 1.80% round-trip US spot costs.

Verdict: DROP.

### 8. Grayscale (GDLC) and Bitwise (BITW) Index-Product Rebalances (DROP)

Who is forced to trade and when: Passive crypto index funds must buy added constituents and sell removed constituents on fixed schedules. For Grayscale CoinDesk Crypto 5 ETF (GDLC), [SEC Form 8-K (January 30, 2026)](https://www.sec.gov/Archives/edgar/data/1729997/000119312526037738/gdlc-20260130.htm): "The Index is rebalanced quarterly, during a period beginning 30 days before the last business day of each January, April, July and October." For Bitwise 10 Crypto Index Fund (BITW), [Bitwise Methodology](https://bitwiseinvestments.com/indexes/methodologies/bitwise-crypto-asset-index-methodology): "the Bitwise Crypto Indexes are reconstituted monthly at 4 p.m. Eastern Time on the last Business Day of the month. The indexes have a “record date” on which the new assets entering the index are determined as of 4 p.m. Eastern Time one week prior to the rebalance date."

Best published evidence and post-publication persistence: UNKNOWN for crypto-specific index funds; no peer-reviewed or large-sample empirical study measures positive post-notice returns on GDLC or BITW additions. Crucially, the forced flow is tiny relative to constituent liquidity. GDLC holds only five large-cap coins with $295.5 million in AUM ([Grayscale GDLC](https://etfs.grayscale.com/gdlc): "ASSETS UNDER MANAGEMENT (NON-GAAP) $295,500,316"), where altcoin weights are 2.59% to 4.58% ($7.7 million to $13.5 million of total position size spread across a 30-day rebalance period). BITW holds roughly $758 million in AUM ([Altcoin Investor](https://altcoininvestor.com/crypto-index-fund/): "BITW holds $758M in assets. GDLC holds $414M."), where its 6th through 10th constituents (HYPE, LINK, ADA, XLM, NEAR) each carry 0.28% to 1.00% weight (~$2 million to $7.6 million of forced flow in multi-billion-dollar coins), and monthly rebalances frequently have zero constituent changes ([Bitwise Rebalance Notification, Nov 2026](https://bitwiseinvestments.com/indexes/rebalance-notifications/bitwise-crypto-asset-indexes): "Bitwise 10 Large Cap Crypto Index - No changes").

Free and lawful historical source of event timestamps: SEC EDGAR 8-K and 10-Q filings for GDLC and Bitwise's public rebalance-notification pages for BITW.

US spot cost vs stated effect: A $2 million to $15 million rebalance flow in a top-10 coin executed over days or via OTC desks cannot reliably generate more than 1.0% to 1.8% round-trip US spot fees, and GDLC/BITW do not reach small and mid-size coins.

Verdict: DROP.

### 9. Coinbase 50 Index (COIN50) Quarterly Changes (DROP)

Who is forced to trade and when: Products tracking the Coinbase 50 Index rebalance quarterly at 17:00 CET on the last business day of February, May, August, and November. [MarketVector Insights](https://prod.marketvector.com/insights/mvis-insights/why-crypto-needs-its-own-sandp-500): "Quarterly reviews in February, May, August and November; rebalanced at 17:00 CET on the last business day."

Best published evidence and post-publication persistence: UNKNOWN. COIN50 has only been live since November 12, 2024 (~8 quarters, 26 total additions) and has very few tracking products. [CCi30 Comparison](https://cci30.com/crypto-indices-comparison/coinbase-50/): "Live since 12 November 2024" and "Quarterly reconstitution; 3 products tracking it". Constituent changes are not pre-announced to the public before execution. [MarketVector COIN50E Index Guide](https://prod.marketvector.com/rulebooks/download/COIN50E_Index_Guide.pdf): "Adjustments to constituents will be announced only to the Index Owner on the fourth from the last business day in November, February, May and August at 23:00 CET/CEST."

Free and lawful historical source of event timestamps: Coinbase Institutional public post-rebalance posts on X and Virtune ETP rebalance notices (post-execution only, ~8 quarters of history).

US spot cost vs stated effect: Without public pre-announcement or substantial passive tracking AUM, there is no forced post-announcement buying wave to overcome 1.0% to 2.5% US spot round-trip costs.

Verdict: DROP.

### 10. Scheduled Token Burns and Protocol Buybacks (DROP)

Who is forced to trade and when: Protocols with automated fee-switch buybacks (e.g., AAVE, HYPE, SKY) purchase tokens continuously on-chain from protocol revenue, while scheduled quarterly burns (e.g., BNB Auto-Burn) destroy tokens already held or formulaically allocated without a sudden burst of open-market spot buying on the burn date.

Best published evidence and post-publication persistence: MEASURED across multiple 2025 to 2026 empirical studies showing negative average performance. [cp0x DeFi Token Value Research](https://github.com/cp0x-org/cp0x-defi-token-value-research/blob/main/01-buyback-event-study/README.md) studied 43 dated DAO buyback and supply-cut decisions across 16 protocols from February 2022 to September 2026: "Buyback events that burned the bought tokens showed no premium, with a 30-day median of -13.3 percentage points against the basket and -5.3 points against matched tokens (n=5), and all four burn votes and activations were negative on both controls." Only first-time buyback announcements were positive on both controls. Across 159 protocols, [Novora Research via CoinMarketCap](https://coinmarketcap.com/academy/article/crypto-token-buybacks-hit-record-are-they-working) found: "Novora Research, which scored 159 protocols across six value-accrual models, found buyback-and-burn programs returned an average of -35%. Excluding Hyperliquid, that fell to -56%." Similarly, [BestChange citing Bill Hsu](https://www.bestchange.com/blog/token-buybacks): "In other words, approximately 70% of projects implementing buyback programs failed to generate positive excess returns relative to Bitcoin." (only AAVE, HYPE, and SKY beat BTC out of 10 major buyback tokens). For BNB quarterly burns specifically, [Bitcoin Suisse](https://files.bitcoinsuisse.com/assets/pdf/BTCS_Decrypt_S1E18.pdf): "Binance’s quarterly token burns do not have a significant impact on the Binance Coin (BNB) price, but they do affect positively the rate of change/ growth rate in BNB’s price."

Free and lawful historical source of event timestamps: Protocol governance forums, DefiLlama, Tokenomist buyback dashboards, and BNB Chain burn announcements.

US spot cost vs stated effect: Negative average excess returns (-13.3 pp to -56%) make scheduled burns and buybacks a losing long-only trade even before 1.0% to 2.5% US spot fees.

Verdict: DROP.

### 11. Mainnet Launch Dates (DROP)

Who is forced to trade and when: Nobody is forced to buy on a mainnet launch date; instead, early investors and testnet participants who bought ahead of the scheduled launch often use mainnet go-live as exit liquidity, and team/investor unlocks frequently begin at or after mainnet.

Best published evidence and post-publication persistence: MEASURED by The TIE and eToro (Q3 2020) across SigDev news events: [The TIE / eToro via Scribd](https://www.scribd.com/document/899114938/What-Actually-Moves-the-Prices-of-Cryptocurrencies): "A Mainnet Launch or Upgrade results in a positive price increase for the coin only 47% of the time." Earlier, [TokenGazer 2019 via BeInCrypto](https://beincrypto.com/learn/what-is-a-mainnet/) examined 11 mainnet launches from September 2017 to June 2018: "According to research conducted by crypto research house TokenGazer in 2019 of 11 mainnet launches between September 2017 and June 2018, token prices generally “increased before the mainnet launch and dropped after it.”"

Free and lawful historical source of event timestamps: No clean, survivorship-free free multi-year database of mainnet launch dates for US-listed coins exists.

US spot cost vs stated effect: A 47% hit rate with sell-the-news post-launch drift cannot overcome 1.0% to 2.5% round-trip US spot fees.

Verdict: DROP.

### 12. Stablecoin Mint and Treasury Supply Jumps (USDT and USDC) as a Market-Wide Signal (DROP)

Who is forced to trade and when: Institutional desks or exchanges wire dollars to Tether or Circle to mint USDT/USDC, or Tether pre-mints "authorized but not issued" treasury inventory before actual market deployment. Because treasury mints often reflect inventory replenishment or already-completed OTC purchases, no forced buying occurs after the public on-chain mint alert.

Best published evidence and post-publication persistence: MEASURED across multiple peer-reviewed studies showing the post-mint return is either zero, pre-event, or far below US spot fees. [Wei 2018 (Economics Letters)](https://www.sciencedirect.com/science/article/pii/S0165176518302556): "We find no empirical evidence supporting the notion that Tether grants cause subsequent Bitcoin returns to rise on a daily basis." [Ante, Fiedler, and Strehle 2021 (BRL Working Paper 11 / Finance Research Letters)](https://www.blockchainresearchlab.org/wp-content/uploads/2020/05/The_Influence_of_Stablecoin_Issuances_on_Cryptocurrency_Markets_BRL_Working_Paper_No_11.pdf) examined 565 stablecoin issuances of $1 million or more from April 2019 to March 2020: "The abnormal return of BTC in the 24 hours prior to USDT issuances is 0.88%, and 0.43% in the 12 hours before issuances." As summarized in [arXiv 2501.05232](https://arxiv.org/pdf/2501.05232): "No significantly abnormal returns were observed during the 12 hours after a minting event, but weakly significant abnormal returns (0.63%) were noted 24 hours after." At intraday resolution (2014 to 2021), [Saggu 2022 (Finance Research Letters)](https://www.sciencedirect.com/science/article/abs/pii/S154461232200321X) found: "Bitcoin exhibits a positive reaction to minting activities within 5- to 30-minute windows, although this reaction begins to wane after 60 minutes." A companion study of 1,587 large stablecoin transfers ([Ante, Fiedler, and Strehle, BRL Working Paper 15](https://www.blockchainresearchlab.org/wp-content/uploads/2020/05/BRL-Working-Paper-15-v2.pdf)) confirmed: "For transfers initiated by stablecoin treasuries, i.e. the expected issuance of new capital into the cryptocurrency market, the expected positive subsequent effect on returns could not be confirmed."

Free and lawful historical source of event timestamps: Free public Ethereum and Tron blockchain RPC/explorer logs (ERC-20 Mint/Issue events on Tether and Circle contracts) and DefiLlama daily stablecoin supply API.

US spot cost vs stated effect: A weakly significant +0.63% 24-hour move (or a 5 to 30 minute intraday blip) is smaller than the 0.80% to 1.80% round-trip fee on Kraken Pro or Coinbase Advanced before spread.

Verdict: DROP.

### 13. Altcoin Scheduled Halvings and Emission Cuts (DROP)

Who is forced to trade and when: Miners experience a 50% cut in block-reward issuance on a fully known future block height (e.g., Litecoin, Bitcoin Cash, Zcash), which reduces marginal daily miner sell pressure gradually over months rather than creating a forced spot buying event on the halving date.

Best published evidence and post-publication persistence: MEASURED across multi-asset studies showing no outperformance or negative abnormal returns around halvings. [Pacific-Basin Finance Journal 2025 via RePEc](https://ideas.repec.org/a/eee/pacfin/v94y2025ics0927538x25002501.html): "Contrary to expectations of a bull market surge, our results reveal a negative cumulative average abnormal return around halving dates, suggesting a “scarcity narrative curse.”" [Strix Leviathan via CryptoSlate](https://cryptoslate.com/the-myth-of-cryptocurrency-halving-events-a-deeper-analysis/) tested 32 halvings across 24 cryptocurrencies against 320 market benchmarks: "We found no evidence that cryptocurrency assets experiencing a halving event outperform the broader market in the six months leading up to and following a reduction in miner rewards." Wall Street research reached the same conclusion on Litecoin's 2015, 2019, and 2023 halvings ([Citi via CNBC](https://www.cnbc.com/2023/12/26/will-bitcoin-rally-after-halving-in-april-heres-what-history-shows.html)): "Following Litecoin’s last three halvings in 2015, 2019 and 2023, the coin either tracked historical returns or significantly underperformed them."

Free and lawful historical source of event timestamps: Public blockchain block timestamps for Litecoin, Bitcoin Cash, Zcash, Dash, and other Proof-of-Work networks.

US spot cost vs stated effect: Zero or negative abnormal returns around halving dates cannot beat 1.0% to 2.5% US spot round-trip costs, and events occur only once every 2 to 4 years per coin.

Verdict: DROP.
