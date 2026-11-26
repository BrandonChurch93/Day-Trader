# Round 66: Crypto Hype and Reversal Over Minutes to Days

Date: 2026-11-26 23:33 UTC. Second check 2026-11-26 by a separate helper; corrections are folded into the text and listed at the end.

## Five-Line Plain Answer

1. Shorting crypto hype pops does not work for a $500 to $2,000 US retail account. Live venue API counts on 2026-11-26 give 24 Coinbase CFM perpetual-style contracts and 29 Kraken US spot margin pairs (one is USDC), 32 symbols together; adding the Kalshi, Robinhood, Kraken US perps and Crypto.com US perps rosters in doc 60 brings the union to about 35 coins. Almost no new listings, small-cap top gainers or launchpad memecoins are among them (MEASURED; STATED via doc 60).
2. On liquid coins that can be shorted, this project's replays and the published evidence show shorting pops loses: Replay 17's US-shortable roster lost in 7 of 7 years at 38 and 80 bp, Plan 71's mirror shorts were negative in 34 of 38 rules, and 15-minute reversal in 2025 to 2026 peaks near 1.3 bp gross against a 5 bp round trip (MEASURED; STATED via [arXiv 2608.21888v1](https://arxiv.org/html/2608.21888v1)).
3. The one published long-side result, a BTC-only rebound 6h to 24h after hourly drops of 2.5% to 5% on 2016 to 2021 Kraken data, has no event count, overlapping windows and no costs, and its idea is already on the queue as row 28 and on the Round 21 and Round 30 skip lists (STATED via [Miralles-Quirós and Miralles-Quirós 2022](https://www.econstor.eu/bitstream/10419/314207/1/1841191159.pdf); STATED in docs/QUEUE.md).
4. Weekend and retail-hours ideas find no support: weekend Bitcoin volume fell from 0.78 of weekday volume in 2016 to 0.43 to 0.46 in 2024 to 2025, and a study of 10 major coins plus 407 of the top 500 found no robust return seasonality (STATED via [MDPI Wall Street Time](https://www.mdpi.com/1911-8074/19/9/707/pdf) and [Finance Research Letters 2024](https://www.sciencedirect.com/science/article/pii/S1544612324004598)).
5. Zero ideas earn TEST ON HISTORY and none earns a new COUNT FIRST row; the 6h to 24h price-only rebound is at most a price-only arm of queue row 28, and the other five ideas are DROP (INFERENCE from the checks below).

## US Retail Short-Access Count and Repo Overlap

Live read-only catalog checks of the venues' own public APIs on 2026-11-26 (MEASURED, no prices read; compare `docs/research/98_kraken_and_coinbase_short_access.md` and `docs/research/60_us_venue_costs_checked.md`):

| US venue | Short mechanism | Count | Roster notes and limits |
|---|---|---|---|
| Coinbase Financial Markets (CFM) | Perpetual-style futures (`-20DEC30-CDE`) from `https://api.coinbase.com/api/v3/brokerage/market/products?product_type=FUTURE&limit=250` | 24 crypto roots (HTTP 200, 117 products in all, the rest dated expiries or non-crypto) (MEASURED) | AAVE, ADA, AVAX, BCH, BNB, BTC, DOGE, DOT, ENA, ETH, HBAR, HYPE, LINK, LTC, NEAR, ONDO, PAXG, PEPE, SHIB, SOL, SUI, XLM, XRP, ZEC; whole-contract sizing; Idaho account approval UNKNOWN |
| Kraken US spot margin (provided by Kraken Derivatives US, an FCM; API venue tag `bitnomial_exchange`, pair suffix `:BTNL`) | Spot margin from `https://api.kraken.com/0/public/AssetPairs?execution_venue=bitnomial_exchange` | 29 online pairs, 28 coins plus USDC (HTTP 200) (MEASURED) | AAVE, ADA, ALGO, AVAX, BCH, BTC, CRV, DOGE, DOT, ETH, HBAR, HYPE, LINK, LTC, NEAR, PAXG, PENGU, PEPE, RENDER, SHIB, SOL, SUI, TRX, UNI, USDC, WLD, XLM, XRP, ZEC. Kraken's page says spot margin "is provided by NinjaTrader Clearing, LLC d/b/a Kraken Derivatives US, a CFTC-registered Futures Commission Merchant" and that clients who self-certified as an Eligible Contract Participant "are not eligible for US spot margin" (STATED via [Kraken US margin](https://support.kraken.com/articles/unlock-us-margin-trading)). That page does not name Bitnomial; only the API tag does. Kraken's licensing page excludes Maine and New York only and says margin "is available to eligible US retail clients", so Idaho is not excluded, but approval for this account is UNKNOWN (STATED via [Kraken licensing](https://support.kraken.com/articles/where-is-kraken-licensed-or-regulated?country=us)) |
| Kalshi perpetuals | Margin markets from `https://external-api.kalshi.com/trade-api/v2/margin/markets` | 19 active crypto markets (HTTP 200) (MEASURED) | AAVE, ADA, BCH, BNB, BTC, DOGE, ETH, HYPE, KSHIB, LINK, LTC, NEAR, SOL, SUI, UNI, VVV, WLD, XRP, ZEC; VVV is not on the two rosters above |
| Robinhood perpetuals | Long or short perpetual futures | 8 coins | BTC, ETH, SOL, XRP, DOGE, ADA, LINK, HYPE; the page says "Open long and short positions" and the product is "rolling out to eligible customers" (STATED via [Robinhood perps](https://robinhood.com/us/en/support/articles/about-perpetual-futures/); also in doc 60) |
| Kraken US fractional perps and Crypto.com US perps | Perpetual futures | 17 and 9 coins per doc 60 | Doc 60 adds XTZ (Kraken) and CRO, SEI (Crypto.com). The current [Crypto.com US perps help page](https://help.crypto.com/en/articles/17741688-perpetual-trading-in-the-us) lists no coins, so today's Crypto.com roster is UNKNOWN |
| Binance.US | Spot only | 0 | STATED in doc 60 |
| Union | All of the above | 32 symbols on Coinbase CFM plus Kraken margin; about 36 symbols, about 35 coins without USDC, with the other venues | Memecoins among them: DOGE, SHIB (and KSHIB), PEPE, PENGU. No new listing or launchpad coin (MEASURED for the catalogs; STATED for doc 60 rosters) |

Correction: the first draft said Binance.US and Robinhood had 0 shortable coins and cited doc 60 for "no US retail crypto margin shorting". Doc 60 says the opposite for Robinhood, Kalshi, Kraken perps and Crypto.com; that line was wrong.

Prior repo coverage, checked by the second check against the files (STATED in the docs named):

- Replay 20 (Upbit listing short): passed, not US-executable.
- Plan 75 (coin trend rule with rising stop): passed, forward on E10.
- E09 and E11 (rules 70-102, 71-013, 71-035): buy the coin that fell more than twice BTC when BTC falls at least 1.5% (log), hold 1h or 2h; judged at 150 trades or 2027-11-30; E11 runs on Binance.US.
- Plan 70 (doc 152): the hourly shock family, rules 70-065 to 70-076, faded single-hour moves of at least 1.5%, 2.5% or 4% with volume at least 3 times the 24h mean, both sides, 1h or 2h holds, on 20 coins, 2020 to 2023. 12 eligible, 7 clearly lost, median -20.2 bp, best 70-074 at +38.2 bp on 373 trades with t 1.51.
- Plan 71 (doc 154): the BTC-overextension family with holds of 1, 2, 4 and 6 hours. All 50 immediate longs were positive at the futures cost (median +71.1 bp); mirror shorts were negative in 34 of 38; delayed one hour, 6 of 8 were negative. The spot-fee versions shown for finalists lost (71-035 -69.39% a year, 71-013 -36.97% a year).
- Plan 73 (doc 157): +75.6 bp at the print, +39.4 bp one minute later, -28.1 bp at the worst of that minute, on 182 trades.
- Replay 17 (doc 57): weekly short of hot coins 5% off peak. At no cost the held list was positive only in 2022 and 2025, so it lost in 5 of 7 years; the US-shortable roster was negative in all 7 years at 38 and 80 bp.
- Replay 16 (hot five, weekly momentum) and Replay 19 (Monday Asia window, -53.88% net).
- Queue row 28 and doc 58: "Buying the bounce after a forced-selling flush", held 2 to 24 hours; three public tests lost after fees. The Round 21 skip list says future rounds skip liquidation-cascade bounces, and the Round 30 skip list and doc 119 row 4 drop large liquidation days as reversal entries. The first draft missed this overlap.
- Queue 110 and doc 148: the dip gate closed with a 2.11% chance to pass; Replays 13, 17 and 22 show no dip edge.
- Round 30 (doc 119): 1 to 3 day cross-sectional reversal, 24h reversal (NUS thesis), 12h Kraken reversal and CME weekend gaps all dropped. Round 21 also skips weekend thin-book reversals and Robinhood first-minute listing chases; Round 30 also skips post-listing drift on Coinbase.
- Docs 13, 43, 45, 46, Round 22 (narrative rotation, doc 94), Round 61 and Survey 187d.

## Crowd Behavior Ideas and Evidence

### 1. Exchange Top-Gainers Lists and Large 1-Hour or 1-Day Jumps: Shorting the Pop

- What it is, who the crowd is, and status: PRIOR REPO DOC (Replay 17 `docs/research/57_replay_17_short_the_peak.md`, Plan 71 `docs/research/154_plan_71_second_coin_grid.md`, Round 30 `docs/research/119_round_30_high_count_crypto_power_screen.md`). The theory is that retail buyers chase coins after big gains and that the pop reverses. Kogan, Makarov, Niessner and Schoar show retail eToro traders "follow a momentum-like strategy in cryptocurrencies" and "are not actively rebalancing out of them when prices rise sharply"; that study covers BTC, ETH and XRP only, not top-gainers lists, so applying it to small hot coins is INFERENCE (STATED via [Kogan et al. 2024 JFE](https://eprints.lse.ac.uk/122266/3/Are_cryptos_different.pdf)).
- Why an AI agent can do it and why market makers do not leave it: An agent can watch hourly candles on the roughly 35 US-shortable coins around the clock. The arXiv study finds the 15-minute reversal is real but tiny before costs; that market makers are the ones taking it is INFERENCE (STATED via [arXiv 2608.21888v1](https://arxiv.org/html/2608.21888v1)).
- Evidence. First, [Kogan et al. (Journal of Financial Economics 159, 2024, article 103897, peer reviewed)](https://eprints.lse.ac.uk/122266/3/Are_cryptos_different.pdf) studied 199,927 eToro investors from 1/1/2015 to 12/15/2019 (200 stocks, BTC, ETH, XRP, gold) and wrote: "Using data from eToro, we show that retail traders are contrarian in stocks and gold, yet the same traders follow a momentum-like strategy in cryptocurrencies." Second, [arXiv 2608.21888v1 (22 August 2026, preprint)](https://arxiv.org/html/2608.21888v1) tested 183 Binance USDT pairs against 187 US stocks and ETFs (primary 2025-01-01 to 2026-02-11; holdout 2026-02-12 to 2026-08-08; Coinbase, OKX and Bybit replications): 164 of 183 pairs (90%) show significant 15-minute reversal, 58% of 169 at one hour, and "The gross edge peaks near 1.3 bp per trade against a 5 bp round-trip cost"; not one pair clears the 5 bp maker band. In the holdout the significant share falls to 60% and the signal is gone by four hours. Third, [Miralles-Quirós and Miralles-Quirós, Journal of Applied Economics 25(1) 2022, pages 1294 to 1313, peer reviewed](https://www.econstor.eu/bitstream/10419/314207/1/1841191159.pdf) (listed on [RePEc](https://ideas.repec.org/a/taf/recsxx/v25y2022i1p1294-1313.html); BTC only, Kraken hourly closes, 1 March 2016 to 30 June 2021) report 24h average cumulative returns after positive hourly shocks from +0.218% (+1%) to +2.001% (+5%, t 2.054), mostly insignificant at 1h to 6h and before costs, so there is no reliable reversal to short. In this repo, Replay 17 and Plan 71 lost as listed above (MEASURED in repo; STATED).
- Can a $500 to $2,000 US account place it, and dollars a year: Only on the roughly 35 listed coins, at round trips from a few tens of bp up to about 160 bp (Kraken margin at 80 bp taker a side) plus opening, rollover or funding charges per doc 60; with at most 1.3 bp gross, expected profit is $0 or a loss (STATED via doc 60; INFERENCE).
- Data needed: Free venue hourly candles (not rechecked in the second check; the first draft reported HTTP 200 from the Coinbase and Binance.US candle endpoints). No free historical archive of app "Top Gainers" screens is known (UNKNOWN).
- Independent trades a year: Many hourly jumps on the shortable coins, but negative net in the repo tests (MEASURED in Replay 17 and Plan 71).
- Strongest reason it is false or already gone: Reversal at 15 minutes is far below costs, larger BTC pops tend to keep going rather than reverse, and US venues cannot short the small coins that top gainers lists (STATED; MEASURED).
- Verdict: DROP.

### 2. Long-Only Rebound 6h to 24h After a Sharp Hourly Drop

- What it is, who the crowd is, and status: OVERLAPS QUEUE ROW 28 AND THE ROUND 21 AND ROUND 30 SKIP LISTS (liquidation-cascade bounces held 2 to 24 hours; three public tests lost after fees, doc 58), and is near Plan 70's hourly shock family and E09 and E11. The rule: buy a coin (BTC included) after its own closed hourly log return is -3.5% or less, or -5% or less, and hold 6h to 24h. The paper calls this overreaction after bad news; that the sellers are forced or late retail holders is INFERENCE.
- How it differs from what was already searched: E09 and E11 need BTC to fall at least 1.5% and the coin to fall more than twice BTC, and hold 1h or 2h. Plan 70's hourly shock family used the coin's own single-hour move (1.5%, 2.5%, 4%) but required volume at least 3 times the 24h mean and held only 1h or 2h (best t 1.51). Plan 71 went to 6h holds, but only for the BTC-relative version. No 12h or 24h hold and no plain price-only drop held 6h to 24h was searched (STATED in docs 152 and 154, GRID_70.json, GRID_71.json). So the new part is the 12h to 24h hold on a plain drop.
- Evidence: One paper. [Miralles-Quirós and Miralles-Quirós (2022)](https://www.econstor.eu/bitstream/10419/314207/1/1841191159.pdf), Table 2, BTC only: after a -3.5% hour, +0.533% at 1h (t 3.302), +1.471% at 6h (t 4.894), +2.299% at 24h (t 4.629); after a -5% hour, +0.875% (t 2.473), +2.394% (t 3.419), +3.132% (t 2.908); after -2.5%, +0.745% at 6h and +1.320% at 24h. They write: "Our results show clear evidence of overreaction after negative shocks" and that overreactions "that occur between 6 and 24 hours after the event" are "especially important." Limits found in the second check: the paper does not report how many events each filter has; every hour past the filter counts as an event, so 24h windows in a crash overlap and the t values, which treat events as independent, are overstated; returns start from the close of the event hour; "These returns do not incorporate transaction costs"; there is no subperiod test; it covers BTC only, so carrying it to other coins is INFERENCE (STATED). A 2025 NUS thesis finds a 24h reversal whose profits are "eliminated" once "realistic trading costs are incorporated" (STATED via [Tan 2025 NUS](https://scholarbank.nus.edu.sg/entities/publication/7b89eafc-8618-47c2-b2de-ba8441e2a2fa); already in Round 30). In this repo, Plan 73 showed about half of the 1h to 2h dip gain gone one minute after the print (MEASURED in doc 157).
- Does the published effect survive non-overlapping counting and post-2022 data: UNKNOWN. Nothing opened tests it. Without N, the size of the overlap problem cannot be read from the paper (UNKNOWN).
- Can a $500 to $2,000 US account place it, and dollars a year: Yes, spot long on Binance.US (about 7 to 8 bp a side on liquid pairs per Measurement 132's design, read out after 2026-12-26) or Coinbase (about 60 bp a side). At $1,000 a trade, +50 to +100 bp net on 30 to 50 independent days would be $150 to $500 a year; whether any such edge exists after 2022 is UNKNOWN (INFERENCE).
- Independent signals a year on the coins listed on Binance.US: UNKNOWN. A blog count of BTC down days of 7% or more found 25 in 2013, 22 in 2017 and 14 in 2021 but 1 in 2023, 3 in 2024, 2 in 2025 and 1 in 2026 (STATED via [Kumocast](https://www.kumocast.io/research/bitcoin-after-big-daily-drops), not peer reviewed). Alt-coin hourly drops are more frequent but bunch on the same market-wide days, so after a 24h lockout across all coins, fewer than 30 independent days a year after 2022 is plausible (INFERENCE).
- Data and vault: Binance.US dollar pairs had no trades from August 2023 through January 2025 (STATED in STATUS and docs 185 and 186), so any count uses Coinbase USD hourly candles, with each coin admitted from its Coinbase USD start date in doc 172 (BNB from October 2025, PEPE from November 2024, gaps on DOT and ZEC). The Plan 70 vault, 2024-01-01 to 2026-10-31 on the same 20 coins' hourly bars, is sealed (ledger 218); a count over 2024 to 2026 reads vault-period prices and needs a lead ruling first. 2022 to 2023 is inside the already-searched Plan 70 window.
- No-price count, if the lead wants it: on 2022-01-01 to 2023-12-31 Coinbase USD hourly candles only, for BTC and each of the 20 Plan 70 coins once listed, mark each closed hour whose log return is -3.5% or less (and separately -5% or less). Group all marks across all coins into events with a 24h lockout from the first mark, one event per lockout, and count events per calendar year. Read no return after any mark.
- Pre-fixed pass mark: at least 30 independent events in each of 2022 and 2023 at the -3.5% filter. Then the doc 117 screen, \(N(\text{edge}/\text{noise})^2 \ge 4\), with edge set to half the paper's 24h figure net of a 15 bp round trip (about 100 bp) and noise taken as 400 to 600 bp a day (INFERENCE), needs about 64 to 144 independent events in whatever unseen span would be tested. Fail either and close it with no price test.
- Strongest reason it is false or already gone: The only support is BTC-only, ends June 2021, has no count, overlapping windows and no costs; the same trade under the liquidation-bounce name already lost three public tests; and big drops have become rare.
- Verdict: FOLD INTO QUEUE ROW 28 as its price-only, 12h to 24h arm; no new COUNT FIRST row. Run the count above only if the lead chooses to reopen row 28 and rules on the vault.

### 3. New Listings on Coinbase, Kraken, Binance.US, or Robinhood (Post-2022)

- What it is, who the crowd is, and status: PRIOR REPO DOC (doc 43, doc 119 row 6, Round 21 and Round 30 skip lists; Replay 20 passed on Upbit, not US-executable). Retail buyers rush into new listings; the trade would short the Day 0 pop or buy the later dump.
- Why an AI agent can do it and why market makers do not leave it: An agent can watch listing notices, but The Tie finds the move comes before trading starts; that pre-listing holders and market makers sell into it is INFERENCE (STATED via [The Tie July 2026](https://www.thetie.io/insights/what-does-an-exchange-listing-actually-deliver-in-2026)).
- Evidence: [The Tie (July 13, 2026, industry study, not peer reviewed)](https://www.thetie.io/insights/what-does-an-exchange-listing-actually-deliver-in-2026) covers 1,844 spot listings from January 2023 to June 2026. Its introduction says 5 major exchanges while its method names 7 (Binance, Coinbase, OKX, Bybit, Kraken, Upbit, Bithumb). It uses daily VWAP, BTC-adjusted, and states no trading costs. It writes "the listing itself is less of a price catalyst than the announcement," "Price jumps in the days leading up to listing, then quickly goes flat or negative once trading begins," and "The durable benefit of a major exchange listing is volume, not price." It says gains largely mean-revert within one to two weeks, without percentages, and establishes no post-dump rebound (STATED).
- Can a $500 to $2,000 US account place it, and dollars a year: $0. New listings are not on any US short roster on Day 0, and buying the fade on thin new Coinbase pairs costs about 120 bp a round trip (MEASURED for rosters; STATED via doc 60).
- Data needed: A free point-in-time listing-notice archive is not known; Coinbase and Kraken news and blog pages are excluded by the brief (UNKNOWN).
- Independent trades a year: 0 executable US Day 0 shorts (MEASURED from the rosters).
- Strongest reason it is false or already gone: Gains come before Day 0 and the short side cannot be placed (STATED; MEASURED).
- Verdict: DROP.

### 4. Social-Media Attention Bursts (X, Reddit, Google Trends, Wikipedia)

- What it is, who the crowd is, and status: PRIOR REPO DOC (docs 43, 45, 46, Survey 187d; Round 22 narrative rotation is watch-only in doc 94). Retail attention rises after rallies; the trade would fade coins after a burst.
- Why an AI agent can do it and why market makers do not leave it: An agent can score mention counts, but the thesis below finds attention follows rallies and does not predict crashes. That paid sentiment feeds already sell these spikes to funds is INFERENCE.
- Evidence: [Nguyen (2026, Aalto University MSc thesis, not peer reviewed)](https://aaltodoc.aalto.fi/server/api/core/bitstreams/87f0ee93-9178-430f-a19b-e3d036fd8082/content) uses a weekly panel of 8 coins (BTC, ETH, XRP, DOGE, BNB, TRX, ADA, SOL), January 2016 to January 2026, with attention measured by Google Trends search volume (not X or Reddit), and writes: "Investor attention in cryptocurrency markets is thus gain-chasing: it is recruited by rallies, not by crashes" and "Prior-week investor attention, measured strictly before the crash-risk window, contains no predictive information about next-week crash risk on average." Doc 43 records CFR WP 25-02 (2018 to 2022) at +11 bp next-day per 1-SD tweet spike before costs and Haase et al. at -4.7 bp at hour +1; doc 45 found no 1 to 7 day lead from Wikipedia and Reddit counts (STATED; MEASURED in doc 45).
- Can a $500 to $2,000 US account place it, and dollars a year: $0; 5 to 11 bp gross is below Binance.US (about 15 bp) and Coinbase (about 120 bp) round trips (STATED; INFERENCE).
- Data needed: X and Santiment are paid. Doc 45 got mostly HTTP 502s plus some 429s from Wikimedia and news services and 429s from Google Trends; Survey 187d got HTTP 200 from Wikimedia but notes the timestamp is the UTC bucket, not when the count became visible (STATED in docs 45 and 187d).
- Independent trades a year: Many spikes, none with free honest timestamps and a positive net edge (STATED in doc 45).
- Strongest reason it is false or already gone: Attention follows rallies, and the published effects sit below costs (STATED).
- Verdict: DROP.

### 5. Retail Hours and Weekend Crowd Buying (US Evenings and Weekends)

- What it is, who the crowd is, and status: PRIOR REPO DOC (Replay 19 failed at -53.88% net; Round 30 dropped 12h Kraken session reversal, time-of-day windows and CME weekend gaps; Round 21 skips weekend thin-book reversals). The theory is that retail buys in US evenings and weekends and gives it back on weekdays.
- Why an AI agent can do it and why market makers do not leave it: An agent can trade fixed clock windows every day; that a fixed clock pattern is easy for funds to remove is INFERENCE.
- Evidence: [MDPI Journal of Risk and Financial Management 19:707 (2026, peer reviewed)](https://www.mdpi.com/1911-8074/19/9/707/pdf) uses 87,672 hourly Kraken XBT/USD bars, 2016 to 2025, and writes: "The volatility ratio falls from 0.96 in 2016, weekends almost as volatile as weekdays, to roughly 0.60 by 2024 to 2025" and "The volume ratio falls from 0.78 to about 0.45 over the same span" (0.43 in 2024, 0.46 in 2025; 0.46 in 2022 as well). It measures activity, not signed weekend returns, so it does not by itself refute a return reversal. [Mueller (Finance Research Letters 64, June 2024, article 105429, peer reviewed)](https://www.sciencedirect.com/science/article/pii/S1544612324004598) tests 10 coins from April 28, 2013 to February 29, 2024 plus 407 of the top 500 coins and states: "No evidence of robust return seasonalities in crypto currencies," "A (significant) positive Monday effect in Bitcoin returns does not persist after 2015," and "Crypto currencies are traded less frequently on weekends" (STATED).
- Can a $500 to $2,000 US account place it, and dollars a year: Executable on US spot, but expected profit is $0 or a loss given Mueller's result and Replay 19 (STATED; MEASURED in Replay 19).
- Data needed: Free hourly spot candles (not rechecked in the second check).
- Independent trades a year: About 52 weekends or about 365 evenings, with no measured edge (INFERENCE).
- Strongest reason it is false or already gone: Weekend volume has shrunk to under half of weekday volume and the 407-coin study finds no robust seasonality (STATED).
- Verdict: DROP.

### 6. Pump Groups and On-Chain Memecoin Launches

- What it is, who the crowd is, and status: PRIOR REPO DOC (doc 13 covers Li, Shin and Wang, Hamrick et al., arXiv 2609.10246 and arXiv 2610.39458; two 2026 studies added here). Creators and bots fake volume on launchpad coins to lure buyers before dumping (STATED via [Mongardini and Mei USENIX Security 2026](https://www.usenix.org/conference/usenixsecurity26/presentation/mongardini)).
- Why an AI agent can do it and why market makers do not leave it: Jupiter and Raydium say they do not serve US residents (STATED in doc 13). That sniping needs sub-second builder access and that regulated funds avoid these coins is INFERENCE.
- Evidence: [Mongardini and Mei (USENIX Security 2026, peer reviewed)](https://www.usenix.org/conference/usenixsecurity26/presentation/mongardini) analyzed 34,988 tokens on Ethereum, BSC, Solana and Base; 82.89% of tokens that gained more than 100% showed artificial growth, with more than 17,000 victims losing more than $9.3 million; they write: "We find that profit extraction schemes, such as pump and dumps and rug pulls, typically follow initial manipulations like wash trading or LPI, indicating how early manipulations create the foundation for later exploitation." [Kamat (arXiv 2607.02823v3, preprint)](https://arxiv.org/html/2607.02823v3) tracked 832,941 Pump.fun mints from 2026-05-08 to 2026-06-10: 1,651 graduated and 831,290 timed out, 0.198% as a lower bound, against 0.63% on 655,770 launches in Marino et al. (STATED). Doc 13 records about 1.02% of 15.25 million launches graduating over 2024 to 2026.
- Can a $500 to $2,000 US account place it, and dollars a year: $0. About 99% to 99.8% of launches never graduate (doc 13 and Kamat), the main Solana front ends exclude US residents, and the only memecoins on US short rosters are mature ones (DOGE, SHIB, PEPE, PENGU) (STATED; MEASURED for rosters).
- Data needed: Chain logs; no lawful free US execution route exists (INFERENCE).
- Independent trades a year: 0 on US retail venues (MEASURED for rosters).
- Strongest reason it is false or already gone: Most big launchpad gainers are manipulated and US accounts cannot trade them on the main venues (STATED).
- Verdict: DROP.

## Ranked List of Things Worth Testing

Zero ideas earn TEST ON HISTORY, and no new COUNT FIRST row is proposed.

1. Optional, only if the lead reopens queue row 28: the no-price count in idea 2 (2022 to 2023 Coinbase USD hourly candles, 24h lockout across all coins, at least 30 independent events in each year, then the doc 117 screen). Why it could fail: one BTC-only 2016 to 2021 paper with no count, overlapping windows and no costs; three public liquidation-bounce tests lost after fees; big drops have become rare after 2022; and 2024 to 2026 bars sit in the sealed Plan 70 vault.

## Second Check, Claim by Claim

Confirmed:

- Coinbase CFM 24 perpetual-style crypto roots; Kraken US spot margin 29 online pairs; union 32 (MEASURED 2026-11-26).
- Kogan et al.: JFE 2024, 199,927 investors, 2015 to 2019, BTC/ETH/XRP plus 200 stocks, abstract quote.
- arXiv 2608.21888v1: 183 pairs, 90% significant, 58% of 169 at one hour, 1.3 bp against 5 bp, no pair clears 5 bp, dates and replications.
- Miralles-Quirós Table 2 negative-shock figures and t values, the two overreaction quotes and the no-costs quote; +2.001% at 24h after +5% jumps.
- The Tie: July 13, 2026, 1,844 listings, January 2023 to June 2026, the three quotes, daily VWAP, BTC-adjusted.
- Nguyen: 8 coins, January 2016 to January 2026, both quotes.
- MDPI: 87,672 bars, 0.96 to 0.60, 0.78 to about 0.45, 0.43 in 2024 and 0.46 in 2025.
- Mueller: 10 coins, 407 of the top 500, the three quotes.
- USENIX: 34,988 tokens, 82.89%, more than 17,000 victims, more than $9.3 million, quote.
- Kamat: 832,941 mints, 1,651 against 831,290, 0.198%, Marino 0.63% on 655,770.
- Replay 17 losing 7 of 7 years on the US-shortable roster; Plan 71 mirror shorts 34 of 38 negative; Plan 73 one-minute decay; Round 30 drops.

Wrong, now fixed:

- "Binance.US and Robinhood Crypto: 0 shortable coins" and the doc 60 citation: Robinhood offers long and short perps on 8 coins, and doc 60 also lists Kalshi, Kraken perps and Crypto.com perps. The union is about 35 coins, not 32.
- "Kraken Pro US (Bitnomial route)": Kraken's page names Kraken Derivatives US (NinjaTrader Clearing, an FCM) as the provider; Bitnomial appears only as the API venue tag. One of the 29 pairs is USDC.
- The EconStor source is a peer-reviewed Journal of Applied Economics 2022 article, not a working paper, and the positive-shock 24h range starts at +0.218%, not +0.286%.
- "Plan 71 ... all lost at Coinbase spot fees": only finalists' spot-fee versions were shown, and those lost.
- Round 30's -0.21% a day is Bianchi et al.'s Binance net figure; the 2025 to 2026 figure is a separate -28.5% a year backtest.
- Wikimedia HTTP 429 was in doc 45 (mixed 502, 429 and 200), not doc 43; Survey 187d got HTTP 200.
- "Binance.US 18-month USD gap from July 2023 to February 2025": the repo records no trades from August 2023 through January 2025.
- Nguyen measures attention with Google Trends, not X or Reddit, and is an MSc thesis.
- The Tie's introduction says 5 major exchanges; its method names 7.
- "500-coin" and "2018 to 2024" for Mueller: 407 coins; the 10-coin sample runs from 2013.
- Several MEASURED or STATED labels on opinions (fixed clock easy to arbitrage, market makers absorb bursts, market makers step back, paid feeds sell spikes, sniping needs builders, regulated funds avoid launchpads) are now INFERENCE.
- Idea 2's status missed queue row 28 and the Round 21 and Round 30 skip lists.

Not found on the page:

- The MDPI paper does not test signed weekend returns, so "no signed weekend return reversal" and "directly refute" are not supported there.
- Kogan et al. do not study top-gainers lists or small coins.
- The Miralles-Quirós paper gives no event counts, no non-overlapping test and no subperiods.
- The Tie gives no percentages for the reversal within one to two weeks.
- The Coinbase and Binance.US candle endpoint results were not rechecked; the second check collected no prices.
