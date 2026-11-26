# Round 30: High-Count Crypto Candidates Under the Pre-Data Power Screen

Date: 2026-11-26
Status: 0 queued (queue row 99 stays unused)
Lens: Crypto strategies with at least several hundred independent events and a published net edge clearing the pre-data power screen in `docs/research/117_power_screen_before_data.md` (independent events times (net edge divided by paired noise) squared at least 4 for 50% power).

## Summary

Zero of seven primary crypto families (and zero of three bonus checks) clear the pre-data power screen of 4 after US retail trading costs. Queue row 99 stays unused.

US retail fee anchor used for net-edge screening (STATED): [TradersSecondBrain (Nov 10, 2026)](https://traderssecondbrain.com/guides/coinbase-advanced-vs-kraken) reports: "Coinbase's public Advanced tier page lists Intro at 0.500% maker and 0.900% taker from $0" and "Kraken's public cross-platform Spot Crypto schedule displayed 0.400% maker and 0.800% taker from $0". Even under this project's lower benchmark assumption of 12 bps per side (24 bps round trip) or an optimistic 5 bps per side (10 bps round trip), every high-frequency crypto signal audited below turns negative or falls far below 4 on the power screen.

## Power screen summary table

All rows below are STATED from published empirical studies and checked against prior repo tests and skips. Net edge deducts round-trip costs at the optimistic 10 to 24 bps benchmark (entry-tier $500 US retail fees of 80 to 180 bps round trip are even harsher). Any candidate with negative net edge scores 0 and is dropped.

| Candidate | Prior repo status | Effective independent events (N) | Published net edge (per event) | Paired or per-event noise | Screen: N * (edge / noise)^2 | Decision |
|---|---|---:|---:|---:|---:|---|
| 1. Funding-rate extremes on US-shortable coins | Tested and failed (Replay 18, Replay 24, Plan 10, Rounds 21 and 24) | 280 (72h BTC neg-funding, 2020 to 2026) | +0.22% (at 24 bps RT; negative on extreme-positive shorts) | 4.50% (72h BTC vol) | 0.67 | DROP (< 4) |
| 2. Stablecoin supply or exchange-flow signals | Stablecoin issuance dropped (doc 43); no free CEX wallet labels (Round 23) | 3 to 4 cycles (supply) or hourly (no free feed) | <= 0% net after 24 bps RT (1 to 2h flow) | 1.50% (2h BTC vol) | 0.00 | DROP (< 4, no free feed) |
| 3. Perpetual basis extremes (spot vs perp) | Checked (docs 41, 62); same-coin carry failed (Replay 24) | ~2,000 daily turns | -0.20% to -0.45% (3.2 bps CFTC mean basis minus 2-leg RT fees) | 0.50% | 0.00 | DROP (< 4) |
| 4. Large liquidation days as reversal entries | Skipped (Round 21, Row 28, doc 58) | 72 (6-yr OOS alt rebound) | +0.68% (BTC-hedged +0.98% p=0.182 minus 30 bps RT) | 6.00% (48h alt vs BTC) | 0.92 | DROP (< 4, low N) |
| 5. Cross-sectional 1 to 3 day reversal (Coinbase and Kraken) | New for crypto (Round 17 skipped equity monthly; Replay 16 tested 7d momentum) | ~1,700 daily turns (2022 to 2026) | -0.21% per day (Binance EW net in Bianchi et al. Table 7; -28.5% p.a. in 2025 to 2026) | 5.92% per day | 0.00 | DROP (< 4) |
| 6. Post-listing drift on Coinbase itself | Dropped (doc 43, Queue line 133; Row 80 roadmap closed) | ~200 to 250 listings (2020 to 2026) | <= 0% (-1% to -3% 1w post-open; new tokens unshortable in US) | 15.0% (7d alt vs BTC) | 0.00 | DROP (< 4) |
| 7. Time-of-day windows other than 21:00 to 23:00 UTC BTC (Plan 58) | Monday Asia failed (Replay 19); 21:00 to 23:00 UTC taken (Plan 58) | ~2,100 to 2,500 daily turns | -0.06% to -0.20% (gross +0.028% to +0.038% minus 10 to 24 bps RT) | 1.12% (8h session) | 0.00 | DROP (< 4) |
| Bonus A. 24-hour intraday reversal in crypto | New check | ~2,000 daily turns | <= 0% (eliminated by realistic trading costs) | 2.60% | 0.00 | DROP (< 4) |
| Bonus B. CME Bitcoin weekend gap fill | New check | 458 weekends (regime ended May 2026) | -0.32% to -0.72% after 10 bps RT | 4.35% (24h) | 0.00 | DROP (< 4, regime ended) |
| Bonus C. 12-hour daytime and overnight BTC/ETH reversal on Kraken | New check | ~3,650 turns (2016 to 2025) | Not statistically significant at any cost level (even 0 to 2 bps) | 2.00% | 0.00 | DROP (< 4) |

## Detailed audit by family

### 1. Funding-rate extremes on US-shortable coins

Prior repo coverage: Replay 18 (`docs/research/65_replay_18_funding_carry.md`) failed at -44.61% net (Sharpe -0.339); Replay 24 (`docs/research/68_replay_24_same_coin_carry.md`) failed at +0.036% per year; Plan 10 (`research_rig/PREREG_10_negative_funding.md`) closed on count (1 to 11 triggers in 4 design years); Round 21 and Round 24 (`docs/research/99_round_24_forced_flow_and_shortable_coins.md`) skipped funding-rate extremes.

Checked 2026 evidence (STATED):

- [FundingArb (Oct 28, 2026)](https://fundingarb.net/learn/funding-rate-extremes-directional-backtest) tested 895 Binance perpetuals including delisted coins (Jan 2022 to Aug 2026), shorting at or above +30% annualized and longing at or below -40% annualized: "Both sides lost, and the funding income was a rounding error next to the price moves." Shorting extreme positive funding returned -6.7% APR (Sharpe -0.32) and longing extreme negative funding returned -6.0% APR (Sharpe -0.18).
- [MarketTrace (Nov 9, 2026)](https://markettrace.ai/blog/funding-rate-extremes) tested 789 days (May 2024 to Jul 2026) across BTC, ETH, SOL, BNB, XRP, and DOGE: "Deeply negative funding (<=10th percentile) predicted nothing on any of the six assets: median 72-hour forward returns between -0.48% and +0.62%, hit rates between 46.6% and 54.1%." Top-decile BTC funding produced only 37 non-overlapping 72-hour episodes in two years (-1.18% median).
- [MyProfitFactor (Oct 18, 2026)](https://myprofitfactor.com/en/crypto/negative-funding-rate-bitcoin-rebounds/) measured 280 independent negative-funding BTC episodes (2020 to 2026, 72-hour cooldown): "The median 72-hour return after 280 negative events was +0.462%, and 57.1% of observations were positive. Yet the worst 72-hour outcome was -13.575%."
- [TradingStrategies.work (Nov 22, 2026)](https://tradingstrategies.work/blog/funding-rate-signal-btc-backtest) tested BTC funding Z-score below -1.5 (Sep 2019 to Jun 2026, 93 trades, 5-day average hold, +1.14% gross): "After fees, probably zero or negative. Not a viable strategy."
- [Note / BraveDog (Nov 15, 2026)](https://note.com/brave_dog8445/n/n971d95751ff2?hl=en) compared BTC negative funding against random days (Sep 2019 to Nov 2026): "The average after 30 days is +4.56%, and +4.13% when bought on a random day."

Power screen: Best-case 72-hour negative-funding BTC bounce (N = 280, +0.46% gross minus 0.24% RT = +0.22% net, 4.5% 72h noise) gives 280 * (0.22 / 4.5)^2 = 0.67, well below 4. DROP.

### 2. Stablecoin supply or exchange-flow signals with public dated data

Prior repo coverage: Following stablecoin issuance was dropped in `docs/research/43_crypto_events_evidence_checked.md` (`docs/QUEUE.md` line 133). Round 23 (`docs/research/96_round_23_permitted_small_coin_sources.md`) already documented that no free point-in-time CEX deposit wallet label registry exists in public BigQuery or RPC feeds.

Checked 2025 to 2026 evidence (STATED):

- [Federal Reserve Bank of New York, Liberty Street Economics (Apr 2025)](https://libertystreeteconomics.newyorkfed.org/2025/04/stablecoins-and-crypto-shocks-an-update/) analyzed Jan 2021 through Jan 2025 and found stablecoin inflows follow rather than lead Bitcoin jumps: "Our estimates, reported in the chart below, show that capital flows into all stablecoins, regardless of the riskiness of their reported collateral, over the days following large increases in bitcoin prices."
- [Tilburg University thesis (2026)](http://arno.uvt.nl/show.cgi?fid=187959) notes that year-over-year stablecoin supply growth acts only as a slow macro liquidity regime ("the stablecoin supply trend closely tracks the Global Liquidity Index (R^2 = 0.86)"), spanning only 3 to 4 independent crypto market cycles since 2019 (far below several hundred events).
- [arXiv:2411.06327 (2024/2026)](https://arxiv.org/pdf/2411.06327) tested intraday on-chain exchange netflows for BTC, ETH, and USDT: "BTC net inflows generally lack predictive power for BTC returns (except at 4 hours)" and "USDT net inflows into exchanges predict higher BTC and ETH returns (every 1 and 2 hours)". However, historical hourly CEX-labeled USDT netflows require paid analytics subscriptions (Glassnode or CryptoQuant), and 1-to-2-hour flow regression moves are single-digit basis points gross, negative after 24 to 80 bps US retail round-trip fees.

Power screen: Macro stablecoin supply has N of 3 to 4 cycles; intraday exchange netflow has net edge <= 0 after US retail fees and no free lawful historical feed (score 0). DROP.

### 3. Perpetual basis extremes (spot vs perpetual)

Prior repo coverage: Checked in `docs/research/41_fast_lane_evidence_checked.md` and `docs/research/62_round_7_outside_evidence.md`; same-coin spot-perpetual carry failed in Replay 24 (`docs/research/68_replay_24_same_coin_carry.md`).

Checked 2026 evidence (STATED):

- [Ackerer, Hugonnier, and Jermann (arXiv:2212.06888, updated 2026)](https://arxiv.org/html/2212.06888) document severe post-2022 compression in perpetual-spot deviations: "After 2022, the average deviation reduces by almost 80% with volatility shrinking by more than 50% for most tokens." They add: "Furthermore, we find that after the year 2022, futures-spot spreads become much closer and anchored to 0 compared to earlier samples."
- [Fracassi (2026, CFTC perpetuals study)](https://cesare-fracassi.github.io/files/pdf/Research/Fracassi_2026_CFTC_247_Perpetuals.pdf) measures perpetual basis directly on offshore and US CFTC-regulated perpetuals: "On perpetuals, funding-based convergence anchors more tightly than dated futures expiration, with CME dated Bitcoin futures running a mean absolute basis of 41 basis points against 2.6 to 4.9 for offshore perpetuals and 3.2 for a CFTC-regulated one".

Power screen: A 3.2 bps mean absolute basis on a CFTC-regulated US perpetual (or 2.6 to 4.9 bps offshore) is strictly negative after two-leg US retail round-trip fees (>= 24 to 48 bps RT), giving score 0. DROP.

### 4. Large liquidation days as reversal entries

Prior repo coverage: Already skipped in Round 21 (`docs/QUEUE.md` line 15) and tracked in Row 28 (`docs/research/58_crowded_trades_evidence_checked.md`, noting three public bounce tests lost after fees).

Checked 2026 evidence (STATED):

- [Liqwall (Oct 28, 2026)](https://liqwall.com/learn/research/btc-after-liquidation-cascades) examined the 20 worst Bitcoin liquidation cascades from March 2025 to October 2026: "In 11 of 20 cases price was pushed even lower within the next 24 hours." It concludes: "A liquidation cascade is neither the bottom nor a buy signal."
- [Faulkner (Zenodo, Nov 2026)](https://zenodo.org/records/19975149/files/forced-liquidation-cascades-v1.0.pdf?download=1) tracked $176.6 billion in forced exits across 365 days (Mar 2025 to Feb 2026): "The cascade pushes price down and holds it there because the capital that would drive recovery has been extracted. The forced selling does not reverse. It depletes."
- [claude-quant OOS audit of Tigro Blanc (May 2026)](https://github.com/Isk4R1oT/claude-quant/blob/main/research/2026-05-27-liquidation-cascade-and-ofi.md) audited 72 altcoin cascade-bounce entries over 6 years (48-hour hold): gross return was +2.33% per trade, but "the strategy as commonly written produces gross Sharpe 3.58 because 54% of return is BTC beta (beta=1.158)" and "The only public OOS test (Tigro 2026) finds alpha p=0.182 - cannot reject zero."

Power screen: At N = 72 events over 6 years (well under several hundred), paired alpha net of 30 bps RT is +0.68% (statistically insignificant) against ~6.0% 48-hour paired noise, giving 72 * (0.68 / 6.0)^2 = 0.92, well below 4. DROP.

### 5. Cross-sectional short-term reversal at 1 to 3 days on Coinbase and Kraken lists

Prior repo coverage: Not previously tested in crypto (Round 17 skipped equity monthly short-term reversal; Replay 16 tested 7-day momentum on rank 51 to 100 coins and failed).

Checked 2021 to 2026 evidence (STATED):

- [Bianchi, Babiak, and Dickerson (2022, Journal of Banking and Finance / CERGE-EI WP 730)](http://www.cerge-ei.cz/pdf/wp/Wp730.pdf) documented a gross equal-weighted daily reversal of +2.2% per day (+1.687% fee-adjusted on the pooled sample), but Table 5 shows the value-weighted fee-adjusted daily reversal drops to +0.058% (StdDev 9.212%, Sharpe 0.006, insignificant), and they note: "the strategy expected returns tend to be concentrated in low volume pairs."
- Exchange-level Table 7 of Bianchi, Babiak, and Dickerson (2022), summarized by [Karaptic Research (Oct 23, 2026)](https://karaptic.com/research/reversal/), shows that on a liquid major venue, fees flip the sign negative: "The paper's own exchange-by-exchange breakdown (its Table 7) is unusually specific: on Binance, net-of-fees returns flip negative (-0.213% per day equal-weighted, -0.341% value-weighted, both significant), while on the other four exchanges the net-of-fees result stays positive and significant, reaching +0.811% per day net on GateIO equal-weighted."
- [Mercik (2021, International Review of Financial Analysis)](https://ideas.repec.org/a/eee/finana/v78y2021ics1057521921002349.html) across 3,600 coins concludes: "We argue that the daily reversals result from the illiquidity of the vast majority of traded cryptocurrencies. In consequence, the pattern is cross-sectionally dependent on liquidity, and the handful of largest and most tradeable coins exhibit daily momentum rather than a reversal."
- [prams2104 (Oct 30, 2026)](https://github.com/prams2104/crypto-momentum-backtest) tested 1-day cross-sectional reversal across 25 liquid cryptocurrencies (2020 to 2026): "138% daily turnover creates 101% annual cost drag, turning +73% gross return into -29% net return." Net Sharpe was -3.21 (2020 to 2022), -4.51 (2023 to 2024), and -1.73 (2025 to 2026).
- [WhatDoesntWork (Oct 22, 2026)](https://whatdoesntwork.com/research/one-day-crypto-mean-reversion/) tested 1-day reversal across 9 major coins (Jan 2022 to Aug 2026, 15,201 daily trades): "The pooled strategy averaged -1.12 basis points per trade before costs and -11.12 bps after a 10 bps round-trip fee. In the recent out-of-sample segment, that fell to -24.45 bps net."
- [arXiv:2608.21888 (Oct 2026)](https://arxiv.org/html/2608.21888v1) on 15-minute reversal across 183 Binance pairs (refetched on Coinbase, OKX, Bybit): "The gross edge peaks near 1.3 bp per trade against a 5 bp round-trip cost".

Power screen: On liquid US-listed exchange pairs (Coinbase and Kraken have higher entry fees than Binance), daily turnover of ~138% destroys gross reversal, leaving negative net returns (-0.213% per day on Binance EW in Bianchi et al. Table 7; -28.5% per year in prams2104 2025 to 2026). Score 0. DROP.

### 6. Post-listing drift on Coinbase itself

Prior repo coverage: Chasing exchange listings was dropped in `docs/research/43_crypto_events_evidence_checked.md` (`docs/QUEUE.md` line 133). Row 80 / Plan 44 (Coinbase listing roadmap additions on another US venue) closed on feasibility.

Checked 2021 to 2026 evidence (STATED):

- [The TIE (Nov 4, 2026)](https://www.thetie.io/insights/what-does-an-exchange-listing-actually-deliver-in-2026) analyzed 1,844 listing events across 5 major exchanges including Coinbase (Jan 2023 to Jun 2026, BTC-adjusted): "Once the token starts trading on the new venue, the move largely dissipates, with the adjusted return going flat or turning negative shortly after listing." It adds: "The post-listing drift is short-lived and largely mean-reverts within two weeks."
- [The Block (Nov 26, 2026)](https://www.theblock.co/research/institutional/measuring-the-coinbase-effect-34648) found: "We found that Coinbase listing announcement provides a median return of 7% for an asset" and "However, this effect appears to be short-lived as median returns turn negative after one day".
- [HackerNoon citing The Block data](https://hackernoon.com/what-is-the-coinbase-effect-and-is-it-worth-relying-on) reports: "Then the rates dropped during 24 hours from the trades opening, 1% towards USD per day on average. 5 out of 19 assets showed a positive trend. Within a week after listing, most of the assets kept on downward movement -3% towards USD and -1% to BTC on average."
- [Ante (2021, Springer)](https://link.springer.com/content/pdf/10.1007/s10203-021-00323-0.pdf) across 250 cross-listings found: "Abnormal returns are achieved especially before and on the listing day, whereas the CAAR is negative for virtually all post-listings windows."

Power screen: Long-only post-listing drift on Coinbase itself is flat to negative once live trading starts (score 0), and newly listed tokens on Coinbase are not shortable on Coinbase CFM or Kraken Pro margin. DROP.

### 7. Time-of-day effects other than 21:00 to 23:00 UTC on Bitcoin (Plan 58)

Prior repo coverage: Replay 19 (`docs/research/64_replay_19_monday_asia.md`) tested Monday Asia 24-hour momentum and failed (-53.88%, ranked 95th of 168 start hours). The 21:00 to 23:00 UTC Bitcoin window is already taken as Plan 58.

Checked 2026 evidence (STATED):

- [WhyCoinMoves (Nov 6, 2026)](https://whycoinmoves.com/research/best-time-to-trade-crypto-by-hour) states: "Bitcoin's average return in each UTC hour ranged from -2.7 to +3.7 basis points (hundredths of a percent). The hour starting 21:00 UTC averaged +3.7 bp (t 2.44) and the hour starting 23:00 UTC -2.7 bp (t -2.11); both kept their sign in each of 2024, 2025 and 2026."
- [Swolecharts (Nov 23, 2026)](https://swolecharts.com/seasonality/btc) across 69,113 BTC hourly returns (Jan 2019 to Nov 2026): "Bitcoin's strongest UTC hour on average was 21:00 (+0.042%, up 54.6% of the time) and its weakest 23:00 (-0.027%)". Across 2,054 sessions, Asia (00:00 to 08:00 UTC) averaged -0.028% (-2.8 bps per session) and US NYSE hours averaged +0.007% (+0.7 bps per session).
- [Janorium (Nov 10, 2026)](https://janorium.com/articles/bitcoin-weekend-time-of-day-returns) (2020 to 2026) shows Europe (08:00 to 13:00 UTC) compounded +160.6% on BTC (~+3.8 bps per session gross) and +87.5% on ETH (~+2.5 bps gross), while Asia (00:00 to 08:00 UTC) compounded -18.0% on BTC (~-0.8 bps per session gross).

Power screen: Once Plan 58's 21:00 to 23:00 UTC window is excluded, every other UTC hour or session has a gross mean return of at most +3.8 bps per day (or avoiding -2.8 bps in Asia). Paying even 10 to 24 bps per daily round trip makes every alternative window strictly negative net (-6 to -20 bps per day), giving score 0. DROP.

### Bonus checks screened in Round 30

- Bonus A (24-hour intraday reversal in crypto, STATED): [NUS (Oct 27, 2026)](https://scholarbank.nus.edu.sg/entities/publication/7b89eafc-8618-47c2-b2de-ba8441e2a2fa) documents a 24-hour clock-time reversal but concludes: "When realistic trading costs are incorporated, reversal profits are eliminated, supporting the limits-to-arbitrage framework." Score 0. DROP.
- Bonus B (CME Bitcoin futures weekend gap fill, STATED): [RipBacktest (Nov 25, 2026)](https://ripbacktest.com/posts/bitcoin-cme-gap-fill/) tested 458 weekends (Dec 2017 to Sep 2026) and found: "fading gaps of 1% or more from the Sunday reopen lost -0.213 R a trade with a stop one gap away and -0.183 R with no stop." [Hum (Nov 11, 2026)](https://hum.pub/analysis/bitcoin-s-cme-gaps-fill-82-of-the-time-gaps-that-don-t-exist) tested 356 weekends: "Fading the gap wins 83% of trades and loses money on average after a 0.1% fee, thanks to a handful of weekends that kept running." Further, [TradingStrategies.work (Nov 26, 2026)](https://tradingstrategies.work/blog/gap-fill-myth-cme-gap) notes CME moved to 24/7 crypto trading in May 2026: "its predictive power for the future is now exactly zero - because the cause of the pattern, CME's closed weekends, was abolished." Score 0. DROP.
- Bonus C (12-hour daytime and overnight BTC and ETH reversal on Kraken, STATED): [MDPI (Nov 25, 2026)](https://www.mdpi.com/1911-8074/19/9/692) evaluated 25 session-reversal rules on hourly Kraken prices (2016 to 2025) at 0, 1, and 2 bps costs and reported: "None of the strategy-benchmark differences is statistically significant at any transaction-cost level." Score 0. DROP.
