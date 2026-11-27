# 197. Idea Round 69: Dated Public Crypto Events Where Forced Flow Meets a Crowd

Date: 2026-11-26
Scope: Dated, public crypto events where a forced or predictable flow meets a hype-driven crowd, and where a slow, small, long-only US cash-spot desk ($500 to $2,000 on Binance.US or Kraken spot, holding hours to a few weeks) could act after the first public time stamp.

Method and constraints:
- No market price data was pulled, no return calculation was run, and no held-back script was executed.
- Every external link below was opened directly in this round, and each outside claim carries its source link and exact verbatim sentence.
- Banned news and data sources (CoinDesk, Cointelegraph, The Block, CryptoSlate, CryptoPotato, NewsBTC, Bitcoin Magazine, DL News, Decrypt, Coinbase/Kraken news or blog pages, Coinbase market data, Kalshi, CoinMarketCap, and Polymarket) were not opened or cited.
- Cost baseline used across all candidates: 75 bp per side (150 bp round trip) for thin coins, and about 7 to 8 bp per side (14 to 16 bp round trip) measured once on Binance.US large coins (STATED).
- Labels: MEASURED (verified directly in repo files or opened primary documents), STATED (reported by an opened outside study, filing, or issuer page), UNKNOWN (not verified or unavailable in cleared sources).

## Summary of Calls

| # | Candidate family | Direction for $500 US spot | Rough count per year | Overlap with prior rounds / queue | Call |
|---|---|---|---|---|---|
| 1 | Protocol upgrades and hard forks | Long-only post-activation | 1 to 5 on US coins (STATED) | Dropped in Round 32 (`docs/121_idea_round_32.md`) | SKIP |
| 2 | Token burns and buyback programs | Long-only post-notice | 5 to 10 first notices (STATED) | Dropped in Rounds 26 and 28 (`docs/QUEUE.md`) | SKIP |
| 3 | Airdrop snapshot and claim dates | Short-only in evidence | 50+ EVM drops, few US day-1 (STATED) | Airdrop farming dropped in Round 65 | SKIP |
| 4 | Staking unlock and withdrawal queues (Lido / Beacon Chain) | Long-only stETH discount | Continuous daily queue (STATED) | Already queued as COUNT FIRST in Round 65 (`docs/QUEUE.md`) | WATCH |
| 5 | Delisting and trading-halt notices | Protective exit veto only | 20 to 40+ globally, few on US cleared feeds (STATED) | Protective exit already COUNT FIRST in Round 64 / row 72 | SKIP |
| 6 | Stablecoin depeg recoveries (USDC / USDT below $1.00) | Long-only below par | 1,136 at >2 bp on Binance; >=25/50 bp count UNKNOWN | Dropped qualitatively in Round 28 without Kraken threshold census | COUNT FIRST |
| 7 | Spot crypto ETF daily creation/redemption flows | Long-only next-day flow | ~250 US trading days (STATED) | Dropped in Rounds 33 and 35 | WATCH |
| 8 | Court-dated bankruptcy distributions (Mt. Gox, FTX, Celsius, Genesis) | Long-only post-transfer or pre-date | 3 to 6 major dates globally (STATED) | Bankruptcy claims dropped in Round 65 | SKIP |
| 9 | Crypto index and basket rebalances (BITW, GDLC, NCIQ) | Long-only entrant buy | 12 monthly dates, few changes (STATED) | Dropped in Rounds 27 and 28 | SKIP |
| 10 | Bonus: Large cliff token unlocks (>=1% supply) on US-listed coins | Protective veto or post-72h rebound | ~15 to 25+ major unlocks/yr globally (STATED); US-spot count UNKNOWN | Short-only unlocks dropped in Round 26; US-spot veto/rebound uncounted | COUNT FIRST |

Totals: 0 TEST, 2 COUNT FIRST (Candidate 6 stablecoin depeg threshold census on Kraken OHLCVT; Candidate 10 US-spot large cliff unlock census on AlphaGrowth), 2 WATCH (Candidate 4 Lido/Beacon queue stays inside Round 65's existing count-first row; Candidate 7 spot ETF flows waits on a first-public-timestamped issuer archive), 6 SKIP.

## Candidate 1: Protocol Upgrades and Hard Forks

Mechanism: Retail crowds bid up a coin ahead of a scheduled fork or network upgrade expecting free forked coins or demand, while no forced buyer appears after activation.

Outside evidence:
- STATED: [Soiman et al. (2023), "The forking effect"](https://arxiv.org/pdf/2307.11718) analyzed 93 Bitcoin forks between 2014 and 2020 (85 used in main regressions and 22 hard forks in robustness checks, BTC/USD daily closes 2015 to 2020) and found no return edge: "Forking events do not significantly affect the bitcoin's returns but have a strong positive impact on its volatility, especially when considering market dynamics."
- STATED: The same paper reports that volatility stays elevated for three days without directional drift: "Following a fork event, volatility remains elevated for the next three days, regardless of other forking events, and the volatility impact does not increase when multiple forks occur simultaneously on the same day."

Event count: Roughly 1 to 2 major Ethereum upgrades per year and very few US-listed hard forks after 2020 (STATED), far below the 30 independent events needed over a test span.

Data source and public clock: Public protocol GitHub repositories and Ethereum EIP activation block specs carry exact public activation times (ALLOWED, public open-source records). Data access is not the blocker.

Cost check: At 14 to 16 bp round trip on Binance.US large coins or 150 bp round trip on thin coins, a zero-mean return effect loses money after costs.

Repo overlap: MEASURED in `docs/INDEX.md` line 219: Round 32 (`docs/121_idea_round_32.md`) already screened and dropped hard forks under the Doc 117 power screen.

Call: SKIP. No consistent positive post-activation return exists, and US-listed event count is far below 30.

## Candidate 2: Token Burns and Buyback Programs

Mechanism: Protocol treasuries run scheduled buybacks or burns from fee revenue while retail crowds chase burn announcements, leaving the predictable schedule already priced in.

Outside evidence:
- STATED: The [cp0x DeFi Token Value Research buyback event study (Oct 2026)](https://github.com/cp0x-org/cp0x-defi-token-value-research/blob/main/01-buyback-event-study/README.md) examined 43 day-precision governance and announcement events across 16 DeFi protocols from 2022-02-09 to 2026-09-02 (prices through 2026-10-03). First public buyback announcements showed +4.2 percentage points median 30-day excess return vs a control basket (n = 7) and +12.0 pp vs matched tokens (n = 6), but buyback events that burned tokens had -13.3 pp vs the basket and -5.3 pp vs matched tokens (n = 5): "Only first buyback announcements (positive) and late changes (small negative) hold on both controls" and "Programme size did not order outcomes, no premium for burning was visible, and all results are associations in a small sample, not causal effects."

Event count: About 7 first buyback announcements over 4.5 years across DeFi (roughly 1 to 2 per year, and fewer still on US-listed spot venues), far below 30 independent events.

Data source and public clock: On-chain burn transfers and DAO Snapshot/Tally governance proposals have exact block timestamps (public), so data access is not the blocker.

Cost check: Most DeFi governance tokens trade as thin coins at 75 bp per side (150 bp round trip), and burn events specifically show negative median excess returns (-13.3 pp).

Repo overlap: MEASURED in `docs/QUEUE.md` line 199 (Round 26) and `docs/INDEX.md` line 212 (Round 28): both rounds already dropped scheduled token burns and protocol buybacks.

Call: SKIP. Burns show negative excess returns in the 2022 to 2026 sample, and first-announcement counts are far too small.

## Candidate 3: Airdrop Snapshot and Claim Dates

Mechanism: Airdrop recipients receive free tokens at the public claim open and immediately sell into hype buyers, creating heavy post-claim supply pressure.

Outside evidence:
- STATED: [Messias, Yaish and Livshits, "Airdrops: Giving Money Away Is Harder Than It Seems"](https://arxiv.org/html/2312.02752) tracked 9 major airdrops (1inch, Arbitrum, Arkham, DYDX, ENS, Lido, Optimism, Tornado Cash, and Uniswap) and measured that 73% to 87% of eligible accounts claimed on day one (Arbitrum 73%, Lido 77%, Arkham 87%), while large shares sold at exchanges in their very first post-claim transfer (Lido 65.75%, 1inch 58.67%, Optimism 48.21%, ENS 46.74%, Uniswap 43.69%): "Our analysis shows that while airdrops temporarily increase user activity, they often fail to ensure lasting engagement."
- STATED: [Bitquery's 2026 Crypto Airdrops Investigation (Sep 30, 2026)](https://bitquery.io/investigations/crypto-airdrops-2026) tracked 51 EVM airdrops from January 1 to September 29, 2026 (2,023,879 claiming wallets, $809.4M claim-day value) and found a median 73% of claimers moved tokens within one day, with three in four tokens falling afterward: "We found 51 airdrops on Ethereum, BNB Chain, Base and Arbitrum that each paid at least 5,000 wallets and $1 million in 2026, and followed every claimer: 2.02 million wallets and $809 million at claim-day prices." and "Thirty-five of the 46 trade below their first week. Twenty-two are down by half or more, and six by 90% or more. The median change is a fall of 48%."

Event count: 51 large EVM airdrops in 9 months of 2026 (roughly 65+ per year globally, STATED), but UNKNOWN how many list on Binance.US or Kraken spot on day one.

Data source and public clock: On-chain Merkle distributor claim contracts carry exact block timestamps.

Cost and venue check: The documented edge is strongly negative (-48% median), which requires shorting newly launched tokens. A $500 to $2,000 long-only US spot account cannot short these tokens, and most new airdrop tokens do not list on Binance.US or Kraken spot at claim open. No opened study shows a reliable long-only post-claim rebound.

Repo overlap: MEASURED in `docs/QUEUE.md` line 155: Round 65 dropped airdrop farming. Replay 20 was an offshore listing short, closed for US accounts in Plan 28 (`docs/QUEUE.md` line 220).

Call: SKIP. The forced flow pushes prices down on mostly non-US-listed tokens, which a long-only US cash-spot desk cannot short.

## Candidate 4: Staking Unlock and Withdrawal Queues (Lido and Ethereum Beacon Chain)

Mechanism: Impatient stakers facing a multi-day protocol exit queue sell liquid staking tokens (stETH) at a secondary-market discount, while patient buyers can hold stETH through the queue or sell back into recovery.

Outside evidence:
- STATED: A [Swiss National Bank seminar paper on liquid staking (Yuan et al., May 22, 2026)](https://www.snb.ch/dam/jcr:ae3a755a-bb04-451b-95a0-6d7c8678ad15/sem_2026_05_22_yuan.n.pdf) studied Lido from May 2023 to April 2026 using exact on-chain withdrawal events fetched directly from the Ethereum blockchain: "We fetch all withdrawal-related events directly from the Ethereum blockchain by querying the Lido WithdrawalQueueERC721 contract via a public Ethereum RPC node (https://ethereum-rpc.publicnode.com)."
- STATED: That paper establishes two critical facts for a retail buyer. First, the average daily closing stETH/ETH discount is only -0.12% (-12 bp), with an average daily intraday minimum of -0.44%. Second, Granger causality runs from price discount to redemptions (F = 12.80, p = 0.0004 at lag 1) and NOT from redemptions to discount (F = 1.25, p = 0.2647): "The one-directional causality, from price to withdrawal, but not from withdrawal to price, is precisely the mechanism at the heart of our model."

Event count: Daily on-chain queue states exist continuously since May 2023 (~1,250 days, STATED), but extreme queue-spike episodes (such as the September 2025 Beacon Chain exit queue) are rare (count UNKNOWN).

Data source and public clock: Public Ethereum RPC queries of Lido's `WithdrawalQueueERC721` contract (`WithdrawalRequested` and `WithdrawalsFinalized` events) provide an immutable, block-timestamped history with exact first-public times (STATED). Kraken downloadable OHLCVT (`assets.kraken.com`, `ALLOWED WITH LIMITS` for private research in doc 194) carries STETH/ETH and STETH/USD pairs (exact date coverage UNKNOWN).

Cost check: An average -12 bp closing discount does not clear Kraken standard taker fees (40 bp per side) or thin-coin costs (75 bp per side), and stETH is not a standard Binance.US USD spot pair. Only rare deep-discount episodes (>= 50 to 100 bp) could clear costs.

Repo overlap: MEASURED in `docs/QUEUE.md` line 154: Round 65 (`docs/research/191_round_65_small_and_tedious.md`) ALREADY queued `COUNT FIRST, no prices` for Lido withdrawal queue and stETH discount timestamp coverage.

Call: WATCH. Do not open a duplicate count-first row; keep this inside Round 65's existing count-first item, with the SNB May 2026 caveat that normal discounts average only -12 bp and queue length does not Granger-cause discounts.

## Candidate 5: Delisting and Trading-Halt Notices on Readable Venues

Mechanism: Exchange delistings or regulatory security classifications force trapped spot holders to liquidate before trading halts, driving multi-day negative returns.

Outside evidence:
- STATED: [Yang and Kwon (April 4, 2026), Asia-Pacific Journal of Financial Studies](https://onlinelibrary.wiley.com/doi/full/10.1111/ajfs.70045) documented short notice lead times on Binance spot delistings: "An analysis of 104 spot-market delisting announcements issued by Binance between January 2023 and March 2025 reveals that the average announcement timing was 3 days before delisting, with approximately 79% (82 cases) announced just 2 days in advance."
- STATED: [Saggu, Ante and Kopiec (2025), Finance Research Letters 72:106413 (SEC CTF filing copy)](https://www.sec.gov/files/ctf-input-arte-2025-02-19.pdf) analyzed 48 SEC token security-classification events (2019 to 2023, 117 asset-level classifications in Table 1) and measured negative cumulative abnormal returns of -5.2% over [0, 2 days], -12.2% over [0, 6 days], and -17.2% over [0, 30 days]: "Lastly, we identify pre-announcement effects hinting at informed trading."

Event count: Roughly 45 Binance spot delistings per year globally (STATED), but far fewer on US-readable venues (count UNKNOWN).

Data source and clearance check: Per `docs/research/194_data_source_terms_audit.md` and Round 69 rules, Upbit, Bithumb, and Binance global notice pages are blocked, and Coinbase and Kraken news/blog pages are do-not-collect. SEC EDGAR litigation and enforcement releases are `ALLOWED WITH LIMITS` (doc 194). Binance.US support announcements and Bitstamp/Gemini status pages have UNKNOWN archival terms for automated collection; clearing written or published archive terms on Bitstamp or Binance.US support would be required to build a venue notice history.

Cost and direction check: Delistings and security designations produce sharply negative returns, so they cannot serve as a long-only buy rule; they work only as a protective exit veto on coins already held.

Repo overlap: MEASURED in `docs/QUEUE.md` line 150: Round 64 (`docs/research/190_round_64_foreign_language_and_time_zone_sources.md`) ALREADY queued `COUNT FIRST, no prices` for foreign exchange delisting, caution, and suspension notices as a protective exit rule extending row 72. Plan 45 (queue row 79) closed retrospective Binance/Upbit notice testing on HTTP 403 blocks.

Call: SKIP as a long-only buy strategy. Protective exit use is already covered by Round 64 and queue row 72.

## Candidate 6: Stablecoin Depeg Recoveries (Fiat-Backed USDC and USDT)

Mechanism: Venue-level liquidity stress or bank-rail panic pushes a fiat-backed stablecoin (USDC or USDT) below $1.00, while authorized participants redeem at $1.00 par with the issuer and restore the peg once rails clear.

Outside evidence:
- STATED: [Wei Zhang (Sep 5, 2026), SSRN 7415499, "How Much Money Fits Inside a Depeg? A Census of 1,136 Stablecoin Dislocations"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7415499) measured 1,136 Binance USDC/USDT dislocation episodes beyond +/-2 bp from August 2024 to August 2026: "Capacity is a distribution, not a number: floods span four orders of magnitude, from roughly $90,000 at the 25th percentile to $2.1 billion in the October 2025 depeg." and "Weighted by flood, about 97% of dislocation dollars flow through episodes lasting a minute or longer."
- STATED: [Gorton and Zhang (Jan 2026), "Who Restores the Peg?" (arXiv:2601.18991)](https://ar5iv.labs.arxiv.org/html/2601.18991) documented three major recovery episodes: May 12 to 16, 2022 USDT (sub-3-hour empirical recovery half-life), March 11 to 15, 2023 USDC (half-day model recovery estimate once rails reopened), and July 15 to 31, 2023 Binance USDT (30.7-hour half-life): "In the May 2022 USDT episode, stabilization is overwhelmingly driven by primary-market redemptions, consistent with a functional redemption rail and active arbitrage." and "In the March 2023 USDC episode, the primary channel initially contributes negatively due to impaired minting and redemptions, and recovery reflects a joint role of primary and secondary forces once the primary rails are restored."

Event count: 1,136 events at >2 bp on Binance over 2 years (STATED), but 2 bp dips cannot cover retail fees. The count of larger, retail-tradable dips (>= 25 bp or >= 50 bp below $1.00) on a permitted US venue is UNKNOWN.

Data source and public clock: Kraken Downloadable Historical OHLCVT (`assets.kraken.com`, `ALLOWED WITH LIMITS` for private backtesting and research in `docs/research/194_data_source_terms_audit.md`) provides 1-minute bars for USDC/USD and USDT/USD with exact UTC bar timestamps.

Cost and risk check: On Binance.US Tier I or Kraken stablecoin fee tiers, round-trip costs on major stablecoins can sit near 10 to 20 bp (14 to 16 bp STATED on Binance.US large coins; exact live stablecoin fee tiers and stressed spreads to be checked before any price test). Tail risk is severe if an issuer is insolvent (UST-style failure), so any future rule must restrict strictly to regulated fiat-backed USDC and USDT and cap position size.

Repo overlap: MEASURED in `docs/INDEX.md` line 212: Round 28 (`docs/research/115_round_28_us_reachable_crypto_forced_flows.md`) dropped stablecoin depegs qualitatively assuming only 1 to 2 major events per year, without running a multi-year >= 25 bp / >= 50 bp threshold census on Kraken OHLCVT.

Concrete COUNT FIRST step (threshold-episode count only, zero return calculation):
- What is counted: independent below-par episodes where Kraken 1-minute OHLCVT USDC/USD or USDT/USD prints a low <= $0.9975 (>= 25 bp below par) and separately <= $0.9950 (>= 50 bp below par), with episodes separated by at least 72 hours per coin, from 2020-01-01 through 2026-10-31. Record only episode start timestamp, pair, and threshold tier crossed; compute ZERO post-event returns, recovery times, or profits.
- From which page / source: Kraken Downloadable Historical OHLCVT (`assets.kraken.com`, `ALLOWED WITH LIMITS` private research per doc 194).
- Pass number: at least 30 independent episodes at the >= 50 bp threshold (or at least 30 at the >= 25 bp threshold if confirmed US spot stablecoin round-trip cost is <= 10 bp) across at least 3 distinct calendar years. If under 30, close on count without opening returns.

Call: COUNT FIRST.

## Candidate 7: Spot Crypto ETF Creation and Redemption Flow Days

Mechanism: Authorized participants create or redeem spot ETF shares in response to institutional orders, and retail traders watch daily published net flow tables expecting next-day continuation.

Outside evidence:
- STATED: [Fabus, Vartiak, Stalmasekova and Kicova (Sep 30, 2026), SSRN 7545019, "Spot Bitcoin ETF Flows and Bitcoin Returns: Timestamp Alignment and Asymmetric Feedback"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7545019) studied 386 trading sessions (January 11, 2024 to July 28, 2025) and showed that naive UTC-day studies get a spurious +4.89 pp per $1B inflow (adjusted R^2 = 0.228) because the UTC day overlaps the US ETF session. Aligning to 16:00 NY close shrinks the coefficient to 1.67 (adj. R^2 = 0.036), and a window starting after the flow is actually public shows no positive association, while prior 24h returns predict flows (HAC p < 0.001): "Timing matters." and "Timestamp alignment and information timing, rather than a universal flow-to-price coefficient, shape inference about Bitcoin ETF flow-return feedback."
- STATED: [Ashish (2026), Concordia University MSc Thesis, "The Impact of Bitcoin ETF Flows on Price Dynamics"](https://spectrum.library.concordia.ca/id/eprint/997714/1/Ashish_MSc_F2026.pdf) analyzed 494 US trading days (January 12, 2024 to December 31, 2025) across IBIT, FBTC, ARKB, GBTC, and BITB and found no Granger causality from aggregate ETF flows to BTC returns at lags 1 to 10 (p = 0.325 to 0.943), while BTC returns Granger-caused flows at every lag (p < 0.001): "Publicly observable ETF flow data contain no exploitable lagged predictive power for next-day Bitcoin returns, once past returns are taken into account." and "Instead, returns exhibit strong Granger-predictive precedence over subsequent flows, consistent with performance-chasing behavior." (Only GBTC outflows showed lag 8 to 9 significance after Bonferroni correction.)

Event count: Roughly 250 US equity trading sessions per year (~500 since January 2024, STATED).

Data source and clearance gap: Official issuer websites (iShares IBIT, Fidelity FBTC, Bitwise BITB) publish daily shares outstanding late evening ET or next morning, with no immutable historical archive of exact first-public publication timestamps (SEC Form N-PORT is quarterly with a 60-day lag). Clearance needed to ever reopen: read terms on official issuer CSV endpoints (e.g., iShares IBIT and Bitwise BITB) and run a private forward logger recording exact UTC capture timestamps for at least 12 months.

Cost check: BTC/USD costs 14 to 16 bp round trip on Binance.US (STATED), which still loses if post-publication alpha is zero.

Repo overlap: MEASURED in `docs/INDEX.md` lines 220 and 222: Round 33 (`docs/127_idea_round_33.md`) and Round 35 (`docs/131_idea_round_35.md`) already dropped spot BTC/ETH ETF daily flows.

Call: WATCH. Two 2026 studies show the post-publication return effect disappears once timestamp overlap is fixed, and no cleared historical first-public-timestamped daily flow archive exists.

## Candidate 8: Exchange Proof-of-Reserve and Court-Dated Bankruptcy Distributions

Mechanism: Bankruptcy trustees distribute large pools of seized coins or cash to creditors on court-dated schedules, while nervous spot traders sell ahead of or during distribution windows.

Outside evidence:
- STATED: [CryptoKeyhole's Crypto Bankruptcy Repayments ledger (checked Nov 8, 2026)](https://cryptokeyhole.com/crypto-bankruptcy-repayments/) documents every major estate distribution across 2024 to 2026: FTX Recovery Trust made five total distributions (Feb 18, 2025 convenience classes; May 30, 2025 >$5B; Sep 30, 2025 ~$1.6B; Mar 31, 2026 ~$2.2B; Jul 31, 2026 ~$900M, paid in cash/stablecoins); Genesis distributed ~$4B on August 2, 2024; Celsius paid $3.10B across four distributions; and Mt. Gox began BTC/BCH repayments on July 5, 2024 and extended its remaining deadline three more times to October 31, 2027 without pre-announcing individual on-chain transfer dates: "By 31 Oct 2025 about $3.10 billion of the $3.17 billion then eligible had reached creditors, 97.7%" and "On 2 Aug 2024 Genesis distributed about $4 billion in digital assets and US dollars."

Event count: Roughly 3 to 6 major court-dated distribution events per year globally (~10 to 15 total across 2024 to 2026, STATED), far below the 30 independent events required for a statistical test.

Data source and public clock: Court dockets (Kroll/Omni/Tokyo District Court trustee PDFs on `mtgox.com`) carry publication dates, though Mt. Gox wallet transfers themselves occur without advance timestamped notices.

Cost check: Even on BTC at 14 to 16 bp round trip, 10 to 15 confounded macro events cannot distinguish edge from noise.

Repo overlap: MEASURED in `docs/QUEUE.md` line 155: Round 65 dropped bankruptcy claims.

Call: SKIP. Too few independent dated events globally (under 15 in three years), mixed cash vs coin payouts, and unannounced actual transfer timing.

## Candidate 9: Crypto Index and Basket Product Rebalances (BITW, GDLC, NCIQ)

Mechanism: Crypto index ETFs mechanically buy newly added coins and sell deleted coins at their scheduled monthly reconstitution, creating forced flow in smaller constituents.

Outside evidence:
- STATED: The [Bitwise 10 Crypto Index ETF Form 10-K (filed March 2, 2026)](https://www.sec.gov/Archives/edgar/data/1723788/000119312526085428/bitw-20251231.htm) confirms BITW began trading as an NYSE Arca ETF on December 9, 2025, reconstitutes monthly at 4:00 p.m. ET on the last business day of each month, and enforces an 87.5% minimum in SEC-approved ETP components: "The Shares began trading on the Exchange on December 9, 2025." and "Further, on each NYSE trading day, the Index will evaluate its holdings as of 12:00 p.m. ET. If, on any such day, less than 86% of the Index is allocated to Approved Components, the Index will effect a rebalance at 4:00 p.m. ET on the same day so that at least 87.5% of the Index is allocated to Approved Components."
- STATED: [Bitwise's October 2026 Rebalance Results (Oct 29, 2026, as of 4:00 p.m. ET)](https://bitwiseinvestments.com/indexes/rebalance-results/bitwise-crypto-asset-indexes/october-2026) show Bitcoin (76.42%), Ethereum (13.53%), XRP (3.91%), and Solana (2.76%) hold 96.62% of the index, while the entering coin received only a 0.28% weight: "NEAR Protocol (NEAR) enters; Uniswap (UNI) exits".

Event count: Fewer than 12 monthly ETF-era rebalances since December 2025 (with frequent no-change months), far below 30 constituent-change events.

Data source and public clock: SEC EDGAR 10-K/10-Q/8-K filings (`ALLOWED WITH LIMITS` in doc 194) and Bitwise rebalance result pages publish outcomes as of 4:00 p.m. ET with zero advance pre-announcement window for a slow retail desk to act before the rebalance print.

Cost check: A 0.28% index weight on a newly added altcoin is tiny relative to daily spot volume and cannot reliably clear 75 bp per side (150 bp round trip) on thin coins.

Repo overlap: MEASURED in `docs/QUEUE.md` line 200 (Round 27) and `docs/INDEX.md` line 212 (Round 28): both rounds already dropped BITW, GDLC, and Nasdaq Crypto Index rebalances.

Call: SKIP. Tiny entrant weights (~0.3%), fewer than 12 ETF-era months, zero pre-rebalance lead time, and already dropped in Rounds 27 and 28.

## Candidate 10 (Bonus): Large Scheduled Cliff Token Unlocks (>=1% Supply) on US-Listed Coins

Mechanism: Early investors and insiders receive newly unlocked tokens on a pre-published vesting schedule and sell into spot markets over the next 72 hours; a long-only US desk cannot short the unlock, but can use the public schedule as a protective exit/avoidance veto on held coins or test a post-72-hour washout rebound.

Outside evidence:
- STATED: [HoKwang Kim (April 23, 2026), SSRN 6632838, "The 72-Hour Shock? Preliminary Evidence from 52 Token Unlock Events on Binance"](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6632838) examined 52 major Binance token unlock events from January 2023 to December 2025 and found severe 72-hour selling pressure across all market regimes: "46 of 52 events (88.5%; binomial test p = 2.2 × 10⁻⁹; robust to Bonferroni correction across 17 formal hypothesis tests) exhibit negative returns within 72 hours of unlock, with a mean return of-16.97%." and "Second, the same 88.5% of events underperform Bitcoin on a relative basis; one-way ANOVA across five Bitcoin regimes finds no statistically significant modulation of the effect (F-test p = 0.24)."
- Caveat (MEASURED in `docs/QUEUE.md` line 199): Albiez (2026, cited in Round 26) found no detectable 3-day abnormal return across 913 broader cliff unlocks, so unlock size (>= 1.0% or >= 2.0% of circulating supply) and US-spot overlap must be counted cleanly before any return test.

Event count: 52 major events in 3 years on Binance global (~17 per year, STATED); the exact count of >= 1.0% supply cliff unlocks on Kraken or Binance.US USD-spot coins is UNKNOWN.

Data source and public clock: MEASURED in `docs/research/194_data_source_terms_audit.md` line 59: AlphaGrowth unlocks API (`alphagrowth.io`) is `ALLOWED WITH LIMITS` ("use, display, and republish reasonable portions of its data for any lawful purpose, including in AI agent responses, research, and commercial products", credit `"Data: AlphaGrowth (alphagrowth.io)"`, 60 req/min), and the project already operates an off-repo AlphaGrowth unlocks logger.

Cost check: As a protective veto on an existing long-only rule (such as Plan 75 or Plan 76), avoiding a -16.97% 72-hour shock saves far more than 75 bp per side even on thin coins. As a standalone post-72h rebound, it would need to clear 150 bp round trip on thin coins (or 14 to 16 bp on large coins).

Repo overlap: MEASURED in `docs/QUEUE.md` line 199: Round 26 dropped shorting cliff unlocks because shorting small coins is unreachable on $500 US spot. It did not count US-spot-listed large cliff unlocks on AlphaGrowth for a long-only protective veto or post-72h rebound.

Concrete COUNT FIRST step (strictly no prices):
- What is counted: scheduled cliff unlocks >= 1.0% of circulating supply (and separately >= 2.0%) on coins listed on Kraken USD spot (Kraken public AssetPairs endpoint on `api.kraken.com`, `ALLOWED WITH LIMITS` private per doc 194) or Binance.US USD spot (off-repo check once full Terms clear), from 2023-01-01 through 2026-10-31, with unlock UTC timestamp and pre-unlock schedule publication confirmed. Zero price or return files opened.
- From which page / source: AlphaGrowth token unlocks API (`alphagrowth.io`, `ALLOWED WITH LIMITS` per doc 194, credit `"Data: AlphaGrowth (alphagrowth.io)"`).
- Pass number: at least 30 independent US-listed cliff unlock events (>= 1.0% circulating supply, separated by at least 7 days per coin) across at least 15 distinct US-spot coins. If >= 30 pass, evaluate first as a protective avoidance/exit overlay on Plan 75 / Plan 76 before testing any standalone post-72h rebound.

Call: COUNT FIRST.
