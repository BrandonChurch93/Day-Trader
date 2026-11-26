# Round 40: Verifiable Trading Track Records (2023 to 2026)

Date: 2026-11-26 11:41 UTC
Status: Reading only, no data pull and no return calculation run by us.
Queue rows added: 0 (rows from 110 stay unused).

## Scope and prior coverage

Three consecutive published-rule rounds (Rounds 37, 38, and 39) queued only one new rule (`Row 109`) for a $500 US retail account. Round 40 shifts from published academic rules to trade-by-trade verifiable live track records from 2023 to 2026, crypto first and stocks second, using only third-party empirical measurements already published with links. No wallet, vault, or leaderboard data was collected by us, and no automated calls were made to any venue.

Prior repo docs already covered named discretionary traders (`docs/research/17_verified_traders_and_their_methods.md`), AI trading contests (`docs/research/18_ai_systems_with_live_records.md`, `docs/research/59_why_the_ai_traders_lost.md`), social callers (`docs/research/46_becker_calls_measured.md`), members of Congress (`docs/research/48_congress_trades_evidence.md`), 13F fund managers (`docs/research/50_public_filers_evidence_checked.md`), and meme-coin pump groups (`docs/research/13_high_risk_sleeve_evidence.md`). Those are not repeated here.

## Summary table

| Source | Market | Persistent winners measured? | Follower / out-of-sample outcome | $500 US reachable? | Doc 117 screen | Verdict |
|---|---|---|---|---|---|---|
| 1. Hyperliquid User Vaults vs HLP | Crypto perps | HLP yes (protocol MM + backstop liquidations); user vaults no | STATED: User-vault depositors 64% down (`-$32.3M`); HLP 91% ahead (`+$140.7M`) | No (US Restricted Person under Terms §1.6(a)) | 0.00 (user vaults negative; HLP unreachable) | DROP |
| 2. Hyperliquid Full Public Leaderboard | Crypto perps | No behavioral early warning for blow-ups | STATED: 2,621 blow-ups from 10,395 masters; 69% sudden; detector AUC 0.49 | No (US Restricted Person) | 0.00 (no reachable positive edge) | DROP |
| 3. Ethereum CEX-DEX MEV Searchers | Crypto spot / DEX | Yes (top 3 capture 90% of volume and value by Q1 2025) | STATED: 19 searchers extracted `$233.8M` over 7.2M trades; no follower access | No (exclusive block-builder integration + latency) | UNKNOWN (unreachable infrastructure) | DROP |
| 4. Binance, Bybit, MEXC, TraderWagon Copy Trading | Crypto perps | Leaders earn 50% to 75% of profit from copier commissions | STATED: 97.04% leaders positive vs 43.61% followers positive; post-promotion collapse in ~6 days | No (offshore futures copy trading unavailable in US) | 0.00 (negative or negligible per-copier edge) | DROP |
| 5. Polymarket On-Chain Smart-Money Wallets | Crypto prediction markets | Weak short-term weekly persistence (2.63x odds) | STATED: Live copy trading lost `-3.04 USDC` across 20 trades (median 112s gap); 444-wallet test lost 0.90c per dollar after fees | Restricted / Polymarket US limited; live copy lost | 0.00 (live net edge negative) | DROP |
| 6. ZuluTrade Real-Money Leaders (2023 to 2026) | FX / multi-asset | No (top fifth lost in 10 of 14 quarters) | STATED: Top fifth lost `-7.7%` per quarter (`-72.5%` cumulative before fees) | Not as a positive-edge strategy | 0.00 (negative pre-fee OOS mean) | DROP |
| 7. eToro Social Mirror Trading | Stocks, ETFs, FX, crypto | No (performance uncorrelated over time) | STATED: Mirrored trades averaged `-61.24 bps` vs `-6.88 bps` self-initiated | No (negative edge; US CFD/copy restrictions) | 0.00 (negative net edge) | DROP |
| 8. USIC, Robbins WCTC, Collective2, Darwinex | US stocks, futures, FX | Rare repeat winners exist, but fills and rules are not public | STATED: 17% profitable in 2026 USIC mid-year; C2 fees `$25` to `$249/mo` (`60%` to `598%/yr` drag on `$500`) | No (`$10k` to `$1M` minimums, UK-only Darwinex, or fee drag on C2) | UNKNOWN (no public trade-by-trade fill log) | DROP |

## Source 1: Hyperliquid User Vaults vs Hyperliquid Provider (HLP) Vault

What is verifiable and by whom: STATED from [Bitquery's November 20, 2026 on-chain investigation](https://bitquery.io/investigations/hyperliquid-vaults-depositors), every vault deposit, withdrawal, and position on the Hyperliquid blockchain is publicly readable on-chain: "On Hyperliquid, any trader can open a vault and trade the USDC that other wallets deposit. 45,275 wallets have put money into these user vaults, and 64% of them are down. Taken together, the wallets have lost $32.3 million. HLP, the exchange's own vault, made its 94,626 depositors $140.7 million."

Survivor problem: STATED from [Bitquery](https://bitquery.io/investigations/hyperliquid-vaults-depositors), the on-chain snapshot includes closed depositors who withdrew everything ("The records include wallets that withdrew everything. We cannot rule out that some records were removed before our snapshots began."), covering 45,275 depositor wallets across 2,965 user-vault leaders with at least one depositor and 94,626 depositors in HLP. By contrast, exchange front-end leaderboards highlight surviving vaults above TVL thresholds; even among the 60 user vaults over $100,000 scored by [Cipher Intelligence on November 26, 2026](https://cipher-intelligence.io/blog/hyperliquid-vaults/), "The median vault returned −2.7% with a 12.9% drawdown, against +1.51% and 0.31% for HLP, and none beat HLP on both counts."

What persistent winners are measured to do: STATED from [CoinGecko's HLP vault analysis](https://www.coingecko.com/learn/hyperliquid-hlp-vault-analysis), the sole persistent vault winner at scale is HLP, the exchange's own protocol vault, whose edge is structural market-making and liquidation-engine flow rather than directional chart picking: "Anyone holding USDC on Hyperliquid can deposit into it, and in return depositors share proportionally in the vault's PnL from three sources: market-making spreads across the exchange's 100-plus listed perps, funding rate capture, and backstop liquidations." CoinGecko reports "$136.9M in cumulative profit since its May 2023 launch" and shows that two crash-day backstop liquidation events (October 10, 2025 at `$41.5M` and January 31, 2026 at `$15M`) drove much of lifetime profit: "Combined, these two events account for roughly 41% of HLP's all-time profit, despite covering a combined span of less than two weeks out of the vault's nearly three-year history." For directional user-vault leaders, holding times, leverage, and maker/taker splits are heterogeneous and UNKNOWN across the full 2,965-leader set, but as a group leaders themselves lost money: "The traders who run user vaults lost $55.9 million on their own stake, more than their depositors lost." ([Bitquery](https://bitquery.io/investigations/hyperliquid-vaults-depositors)).

Out-of-sample persistence: STATED from [Bitquery](https://bitquery.io/investigations/hyperliquid-vaults-depositors), user-vault leaders do not deliver positive aggregate persistence even after their 10% profit-share cut: "Leaders also get their cut of the profits, which Hyperliquid pays straight into their accounts. That money sits outside the vault. The exchange's public records show $6.1 million paid to leaders. Count it in, and leaders as a group are still down $49.8 million, more than their followers." In [Cipher Intelligence](https://cipher-intelligence.io/blog/hyperliquid-vaults/), "None of the 60 beat HLP's 30-day return (+1.51%) with a smaller 30-day drawdown (0.31%)."

What a follower actually earned after delay and costs: STATED from [Bitquery](https://bitquery.io/investigations/hyperliquid-vaults-depositors), user-vault depositors pay a 10% profit share on profitable withdrawals ("A vault leader keeps 10% of your profit when you cash out. If you leave at a loss, you pay no fee. HLP charges none.") and lost `$32.3 million` net across 45,275 wallets (median `-$8.58`, 64% down). On the cleanest within-wallet comparison: "The fairest test uses the 17,929 wallets that tried both. In HLP, 91% of them are ahead. With the traders, 62% of the same depositors are behind, and the group is down overall."

US $500 reachability: STATED from [Cipher Intelligence's review of Hyperliquid's June 15, 2026 Terms of Use](https://cipher-intelligence.io/blog/hyperliquid-us/), US persons are barred from Hyperliquid (as well as Lighter, Aster, and edgeX): Section 1.6(a) defines Restricted Persons to include "persons or entities who reside in, are located in, are incorporated in, or have a registered office in the United States of America or Ontario, Canada" who are "strictly prohibited from accessing or using the Interface". Nor can a $500 retail account on Coinbase or Kraken replicate HLP's zero-fee 100-perp market-making engine and exchange backstop-liquidation privilege.

Doc 117 screen: `0.00` for user vaults (negative net follower edge `-$32.3M` across 45,275 wallets); `UNKNOWN` / unreachable for HLP (legally blocked for US persons and structurally an exchange house engine).

Verdict: DROP. User vaults lose money for both leaders and depositors, while HLP is a US-restricted exchange market-making and liquidation-backstop vault that cannot be replicated on a $500 US retail spot or futures account.

## Source 2: Hyperliquid Full Public Leaderboard (Copy-Trading Blow-Up Study)

What is verifiable and by whom: STATED from [arXiv:2611.27988v1 (November 2026)](https://arxiv.org/html/2611.27988v1), a pre-registered, full-universe on-chain study of Hyperliquid perpetual leaderboard accounts tracked every equity trajectory and trade bucket on-chain.

Survivor problem: STATED from [arXiv:2611.27988v1](https://arxiv.org/html/2611.27988v1), the authors froze the universe at `T0 = 2025-06-01 UTC` and followed it forward through `2026-04-30 UTC` with no survival filter: out of `37,895` total leaderboard addresses, `10,395` met the "master worth copying" filter (at least `$25,000` pre-`T0` peak equity and at least two equity points). Over the 11-month forward window, `2,621` masters suffered genuine loss-driven idiosyncratic blow-ups across `48` independent crash-day clusters.

What persistent winners are measured to do: STATED from [arXiv:2611.27988v1](https://arxiv.org/html/2611.27988v1), the paper evaluates leveraged perpetual traders across 4-hour behavioral buckets (leverage, adding to losers, stop-attach rate). Where early warning existed at all (`216` of `2,477` blow-ups, about 9%), it was "almost entirely an exposure phenomenon" (`215` of `216` carried by leverage/exposure). Exact strategy taxonomy of the `973` stable masters in the behavioral sub-cohort is UNKNOWN from this paper.

Out-of-sample persistence and blow-up risk: STATED from [arXiv:2611.27988v1](https://arxiv.org/html/2611.27988v1), blow-ups among top-looking masters are predominantly sudden and unpredictable from prior trading behavior: "Behavior leads equity for only 216 of 2,477 (≈9%) masters." "Fully 69% blow up with no gradual behavioral signal at all—they are sudden" "Over the 762 cases where both timestamps exist, the median lead is negative (-8 days): when behavior moves at all, it more often lags the equity than leads it." On the sealed test set (`990` blow-up and `404` stable masters), the pre-registered drift detector scored at chance: "its continuous drift-evidence score separates blow-up from stable masters with AUC=0.49 (event-clustered 95% CI [0.47, 0.51], straddling the 0.5 chance line), and as a binary alarm it fires early on only 2% of blow-ups." Conclusion: "Behavioral early warning is therefore not a viable general safety net for copy-trading blow-ups".

What a follower actually earned after delay and costs: UNKNOWN in this paper (measured at master account equity level without follower slippage); for actual Hyperliquid follower outcomes see Source 1 above.

US $500 reachability: STATED as No; Hyperliquid Terms of Use §1.6(a) bar US persons ([Cipher Intelligence](https://cipher-intelligence.io/blog/hyperliquid-us/)).

Doc 117 screen: `0.00` (no positive reachable net edge; `25.2%` of pre-`T0` "worth copying" masters blew up idiosyncratically within 11 months, 69% suddenly).

Verdict: DROP. Frozen-cohort on-chain evidence shows leveraged perp leaderboard leaders blow up suddenly at high rates and cannot be safely filtered ahead of time, and the venue is US-restricted.

## Source 3: Ethereum On-Chain CEX-DEX Arbitrage Searchers

What is verifiable and by whom: STATED from [Wu et al. (June 2025, arXiv:2507.13023v1)](https://arxiv.org/html/2507.13023v1), Ethereum DEX swaps and block-builder inclusion records are publicly verifiable on-chain and matched against centralized-exchange price feeds across Ethereum blocks `17,866,488` to `21,998,438` (August 8, 2023 to March 8, 2025): "Using the estimation methodology outlined in Section 4, we analyze a total of 7,203,560 CEX-DEX arbitrages with a total volume of 241.7B USD executed by 19 labeled searchers between August 8, 2023 and March 8, 2025."

Survivor problem: STATED from [arXiv:2507.13023v1](https://arxiv.org/html/2507.13023v1), `23` major labeled searcher entities accounted for `99.74%` of total CEX-DEX volume (`19` analyzed for PnL), and competition rapidly concentrated: "The figure further reduced to 11 by Q1 2025, with three leading searchers capturing 90% of the total volume (cf. Appendix D Figure 15)."

What persistent winners are measured to do: STATED from [arXiv:2507.13023v1](https://arxiv.org/html/2507.13023v1), persistent on-chain winners run sub-second cross-venue CEX-DEX arbitrage at massive trade counts (`7.2M` trades in 19 months) using exclusive block-builder relationships: "We refer to these searchers, who send more than 50% of their volume to one builder, as the exclusive searcher (including integrated searchers SCP and Wintermute) for that builder, and correspondingly label their primary recipient builder as their exclusive builder." Holding time is one block / sub-second hedge; maker/taker mix is atomic DEX execution hedged on CEX inventory.

Out-of-sample persistence: STATED from [arXiv:2507.13023v1](https://arxiv.org/html/2507.13023v1), persistence is extreme among the top three institutional searchers (Wintermute, SCP, and Kayle): "According to our estimation, a total of 233.8M USD is extracted by these 19 searchers through CEX-DEX arbitrages." "Furthermore, these top three players dominate arbitrage opportunities even more decisively, jointly accounting for around 90% of the extracted value by Q1 2025."

What a follower actually earned after delay and costs: Not applicable (atomic single-block arbitrage cannot be copy-traded after inclusion; any follower arriving one block later faces an already-closed spread).

US $500 reachability: No. Requires institutional CEX inventory, VIP zero/negative maker fees, private order flow, and exclusive Ethereum block-builder integration.

Doc 117 screen: `UNKNOWN` (edge belongs solely to builder-integrated institutional infrastructure; zero retail access).

Verdict: DROP. Confirms that the second genuinely persistent verified on-chain profit source in crypto is latency-and-builder-gated institutional arbitrage, completely unreachable on a $500 US retail account.

## Source 4: Exchange Crypto Copy-Trading Leaderboards (Binance, Bybit, MEXC, TraderWagon)

What is verifiable and by whom: STATED from [Kawai et al. (ACM CHI 2024)](https://dl.acm.org/doi/fullHtml/10.1145/3613904.3642715) (studying TraderWagon/Binance Futures from October 26, 2022 to August 31, 2023 and Bybit from February 18, 2023 to August 31, 2023) and [DoesItPay (October 2026)](https://doesitpay.org/copy-trading/research/) (summarizing YieldFund's 90-day multi-exchange study of `1,486` lead traders and `100,236` follower outcomes across Binance, Bybit, and MEXC collected in October 2025), exchange copy-trading dashboards expose leader and aggregated follower PnL, though full individual trade histories are exchange-hosted rather than independently audited.

Survivor problem: STATED from [DoesItPay](https://doesitpay.org/copy-trading/research/), exchange leaderboards drop failed leaders: in the 90-day YieldFund sample, lead traders removed after heavy losses are not included, and even in the surviving sample profits "were concentrated in a few leaders" while MEXC followers suffered overall net losses (`-210,040.51 USDT`) due to "occasional significant losses".

What persistent winners are measured to do: STATED from [Kawai et al. (ACM CHI 2024)](https://dl.acm.org/doi/fullHtml/10.1145/3613904.3642715), leaderboard "winners" monetize copier volume rather than repeatable alpha: "leaders holding a portfolio listed on the leaderboard page make over half to three quarters of their total profit from copiers' commissions." On Bybit, "the number of copiers a given portfolio has is the dominant factor for its ranking." On Binance Futures, [DoesItPay](https://doesitpay.org/copy-trading/research/) quotes the fee incentive: "Up to 30% profit share from their copy traders' earnings. A 10% commission on their copy traders' trading fees." Trade-by-trade holding times and maker/taker splits are UNKNOWN across the full leaderboard.

Out-of-sample persistence: STATED from [Kawai et al. (ACM CHI 2024)](https://dl.acm.org/doi/fullHtml/10.1145/3613904.3642715), leaderboard rank fails to persist out of sample: "Neither of the ranking choices is directly correlated with long-term performance." After Bybit Gold-level promotion, "For about one week, copiers make a profit, but their PnL plummets and even goes negative" and "the majority collapses about six days later."

What a follower actually earned after delay and costs: STATED from [Kawai et al. (ACM CHI 2024)](https://dl.acm.org/doi/fullHtml/10.1145/3613904.3642715), per-copier PnL past the top 50 averages only `$1` to `$25`, and "copying top-ranked leaders does not lead to substantial investment profits." In [DoesItPay](https://doesitpay.org/copy-trading/research/), the leader-versus-follower gap is stark: "97.04% of the leaders in our sample recorded a positive PnL, while only 43.61% produced a positive follower PnL." Across all `100,236` follower outcomes, "we found that 48,592 trades were winning, while 51,644 trades resulted in losses."

US $500 reachability: No. Binance Futures, Bybit, and MEXC perpetual copy trading are unavailable to US retail residents.

Doc 117 screen: `0.00` (majority of follower outcomes lose, leader rankings collapse in ~6 days, and 10% to 30% profit shares plus taker slippage eliminate any residual).

Verdict: DROP. Exchange crypto copy-trading leaderboards are structurally misaligned (leaders earn most profit from copier commissions) and unavailable to US accounts.

## Source 5: Polymarket On-Chain Smart-Money Copy-Trading Wallets

What is verifiable and by whom: STATED from [arXiv:2610.34754 (October 2026)](https://arxiv.org/html/2610.34754), Polymarket trades settle on Polygon and are reconstructed wallet by wallet on-chain (`1,101` candidate smart-money wallets; `1,088` wallets with `3,207` complete weekly pairings; `283` paper copy-trading entries and `20` live copy-trading entries).

Survivor problem: STATED from [arXiv:2610.34754](https://arxiv.org/html/2610.34754), the study pre-selects a cohort of `1,101` candidate smart-money wallets and evaluates held-out weekly observations (`2,156` full sample; `1,625` excluding zero-PnL weeks). Separately, [EdgeOrMyth](https://edgeormyth.com/tests/copy-trading-leaders/) summarizes its Test 037 cohort of `444` Polymarket wallets from 2024 tracked out of sample into 2025.

What persistent winners are measured to do: STATED from [arXiv:2610.34754](https://arxiv.org/html/2610.34754), candidate smart-money wallets take directional binary-event positions (no leverage; maker/taker mix of source wallets UNKNOWN; followers submit Fill-or-Kill taker BUY orders within a 300-second expiry window).

Out-of-sample persistence: STATED from [arXiv:2610.34754](https://arxiv.org/html/2610.34754), short-term weekly persistence is positive in the full sample (`AUC = 0.681`) but weakens materially once zero-PnL weeks are dropped (`AUC = 0.577`): "Candidate smart-money wallets exhibit short-term profitability persistence, with previously profitable wallets showing 2.63 times higher odds of remaining profitable in the following week. However, this advantage weakens after excluding zero-PnL observations, suggesting limited robustness."

What a follower actually earned after delay and costs: STATED from [arXiv:2610.34754](https://arxiv.org/html/2610.34754), execution delay (median confirmation gap `112 seconds`, representative range `46` to `188 seconds`; mean adverse price gap `+0.00619 USDC/share`) erased profits in live execution: "The main paper account records 283 BUY entries and a total profit of 44.18 pUSD, whereas 20 live purchases result in a loss of 3.04 USDC." Even the paper profit depended on one missed trade: "The single most profitable ETH trade generates +56.07 pUSD but was not executed live because of a data-validity check (Polymarket, 2026; PolygonScan, 2026); excluding this trade reduces aggregate paper PnL to -11.89 pUSD." "These results confirm the feasibility of real-time on-chain copy trading but do not establish consistent profitability." Consistent with [EdgeOrMyth's summary of Test 037](https://edgeormyth.com/tests/copy-trading-leaders/): "2024's top fifth of 444 wallets stayed 0.15 cents a dollar ahead of the rest in 2025; copied a cent late they earned +0.12 cents, and with fees later lost 0.90."

US $500 reachability: Offshore Polymarket restricts US users; even where prediction markets are reachable in the US (Kalshi, already tracked in Queue rows 22, 44, and 53), Kalshi does not expose public wallet-by-wallet on-chain trade histories to copy.

Doc 117 screen: `0.00` (live net PnL `-3.04 USDC` on 20 trades; paper ex-outlier `-11.89 pUSD`; 444-wallet 2025 copy test `-0.90` cents per dollar after fees).

Verdict: DROP. Even where weak wallet-level persistence exists on-chain, confirmation latency and taker slippage turn follower returns negative.

## Source 6: ZuluTrade Real-Money Copy-Trading Leaders (2023 to June 2026)

What is verifiable and by whom: STATED from [EdgeOrMyth (October 20, 2026)](https://edgeormyth.com/tests/copy-trading-leaders/), ZuluTrade publishes broker-linked daily real-money equity records for its signal providers: "We started from ZuluTrade's list of leaders of 7 October 2026 and took every real-money leader who had been on the platform for at least 156 weeks, about three years: 1,314 leaders, of whom 1,310 had a daily record we could read."

Survivor problem: STATED from [EdgeOrMyth](https://edgeormyth.com/tests/copy-trading-leaders/), "The list keeps leaders who stopped." Each quarterly ranking included `135` to `273` active leaders who had at least one year of history on the ranking date, avoiding retrospective removal of stopped leaders across `14` quarterly rosters from December 31, 2022 through June 2026.

What persistent winners are measured to do: STATED as multi-asset / FX retail copy-trading strategies (individual holding time, leverage, and maker/taker breakdown UNKNOWN from the aggregate study).

Out-of-sample persistence: STATED from [EdgeOrMyth](https://edgeormyth.com/tests/copy-trading-leaders/), past winners did not stay positive out of sample. Across `14` consecutive quarters (January 2023 to June 2026), the top fifth lost money in `10` of `14` quarters (worst single quarter `-39.6%`): "In the average quarter, the best fifth of leaders by their past year lost 7.7%, all leaders still trading lost 11.1%, and the worst fifth lost 24.6%."

What a follower actually earned after delay and costs: STATED from [EdgeOrMyth](https://edgeormyth.com/tests/copy-trading-leaders/), even with zero fees and zero slippage, following the top fifth wiped out most of the account: "A follower who formed the roster again every quarter, from January 2023 to June 2026, would have lost 72.5% of the money, before any fee." "Nothing was charged for following: no subscription, no share of profits, no slippage on copied trades." "We counted no fees; a follower who pays a subscription or a share of profits would have done worse."

US $500 reachability: Irrelevant given `-72.5%` pre-fee loss; retail FX copy trading also faces US NFA/CFTC leverage and broker restrictions.

Doc 117 screen: `0.00` (negative out-of-sample mean `-7.7%` per quarter before fees).

Verdict: DROP. Clean 2023 to 2026 survivorship-aware test shows top-quintile real-money leaders lose heavily out of sample even before fees or delay.

## Source 7: eToro Social Mirror Trading (Stocks, ETFs, FX, Crypto)

What is verifiable and by whom: STATED from [arXiv:2507.01817](https://arxiv.org/html/2507.01817) (analyzing eToro's anonymized trade-by-trade database of `87.5 million` trades and `164,634` active traders, of whom `119,864` used mirror trading and `44,770` traded only independently; note that although published on arXiv in July 2025, the underlying trade records are from 2010 to 2013 and serve here as the largest trade-by-trade equity/multi-asset mirror benchmark).

Survivor problem: STATED from [arXiv:2507.01817](https://arxiv.org/html/2507.01817), the dataset captures every active trader with at least two trades in the observation window (`164,634` traders), eliminating public leaderboard survivorship bias.

What persistent winners are measured to do: STATED from [arXiv:2507.01817](https://arxiv.org/html/2507.01817), there are no persistent leaderboard winners to extract; individual trader performance is noise-dominated across time, while popularity persists far more slowly than returns.

Out-of-sample persistence: STATED from [arXiv:2507.01817](https://arxiv.org/html/2507.01817), "On the other hand, we find that traders' performance is highly volatile and uncorrelated over time, meaning that past performance, which initially drives popularity, is not predictive of future performance (see SI Appendix Text 5.3)." "This aligns with the intuition that a trader's performance on a given day does not predict their future performance."

What a follower actually earned after delay and costs: STATED from [arXiv:2507.01817](https://arxiv.org/html/2507.01817), copying was nearly nine times worse per trade than trading independently: "During our observation period, the average individual trading performance, defined as the mean Return of Investment (ROI) ρit across all orders of trader i at different times t, is negative, with −7.67±0.41 basis points (bps; Figure 1C)." "Specifically, among mirror traders, mirrored trades yield an average performance of −61.24±0.98 bps, while their individually initiated trades yield a better, though still negative performance of −6.88±0.43 bps."

US $500 reachability: No positive edge; eToro US also restricts CFD and copy-trading features compared to offshore eToro.

Doc 117 screen: `0.00` (net edge `-61.24 bps` per mirrored trade).

Verdict: DROP. Trade-by-trade social mirroring severely underperforms even random or self-initiated retail trades.

## Source 8: Audited Real-Money Contests and Broker-Verified Marketplaces (USIC, Robbins WCTC, Collective2, Darwinex)

What is verifiable and by whom: STATED from [The Complete Trader's Edge on USIC](https://completetradersedge.com/us-investing-championship/), [Trading-Tournaments on USIC](https://trading-tournaments.com/articles/us-investing-championship-rules-and-winners), [The Complete Trader's Edge on Robbins WCTC](https://completetradersedge.com/world-cup-trading-championships/), and [DoesItPay on Collective2 and Darwinex](https://www.doesitpay.org/trading-bots/research/):

- USIC: "The verification is real: entrants nominate an account in advance and results are checked against brokerage statements, with live account walkthroughs when the organiser wants them." However, "Statement verification is far stricter than a screenshot on X and far looser than a GIPS audit." Full trade-by-trade fills are NOT public.
- Robbins WCTC: "The organiser audits the results." "The results are audited contest accounts, not GIPS composites". Full trade-by-trade fills are NOT public.
- Collective2 and Darwinex: Broker-linked platforms that record every trade, though public pages display only surviving headline strategies ("A leaderboard shows only those who lasted." [DoesItPay](https://www.doesitpay.org/trading-bots/research/)).

Survivor problem: STATED plainly across all four platforms:

- USIC ([Complete Trader's Edge](https://completetradersedge.com/us-investing-championship/)): "The year-end table is a survivorship funnel applied to a survivorship funnel." "appearing in the monthly standings is optional." In 2022 (ten months), only `26` of `316` entrants (`8%`) reported a profit; in first-half 2026, only `115` of `688` (`17%`) were profitable (when the S&P 500 was up `10.2%`), falling to `85` of `712` (`12%`) through September 2026. Five interim 2026 leaders (including `+2,854%`, `+1,919.5%`, and `+1,038%`) disappeared from later monthly boards.
- Robbins WCTC ([Complete Trader's Edge](https://completetradersedge.com/world-cup-trading-championships/)): "Only winners are remembered." "The accounts that were wiped out do not appear in the headline." Entrants may run multiple contest accounts and "only the best-performing account is used for ranking", meaning "The published row can be the survivor of several attempts."
- Collective2 and Darwinex ([DoesItPay](https://www.doesitpay.org/trading-bots/research/)): Overall entrant counts and survival rates are UNKNOWN; Darwinex Zero reported `9,418` participants and `1,799` strategies with allocations (~1 in 5), with total payouts unstated.

What persistent winners are measured to do: STATED from [Complete Trader's Edge USIC](https://completetradersedge.com/us-investing-championship/) and [WCTC](https://completetradersedge.com/world-cup-trading-championships/), a small set of repeat winners exists (e.g., Sean Ryan with 7 consecutive profitable USIC years 2019 to 2025; Vibha Jha with 4 top `$1M+` finishes; Andrea Unger with 3 consecutive WCTC annual futures titles 2008 to 2010; Serghey Magala with 2023 and 2024 WCTC titles). However, neither contest publishes trade-by-trade fills, holding times, leverage, trade counts, or maker/taker splits (all UNKNOWN at the fill level). Public winner interviews describe concentrated discretionary momentum/breakout stock trading with margin (USIC) or multi-system leveraged futures portfolios (WCTC), neither of which yields a verifiable, mechanical rule from the public record.

Out-of-sample persistence: STATED as UNKNOWN across the full entrant population (only winning survivors are published; as [Complete Trader's Edge WCTC](https://completetradersedge.com/world-cup-trading-championships/) notes, "A championship shows that a real account made that return under these rules. It does not show that the same trader will repeat it, or that the approach would survive a larger account.").

What a follower actually earned after delay and costs: STATED from [DoesItPay](https://www.doesitpay.org/trading-bots/research/), Darwinex headline figures "are before the fees investors pay" (`15%` performance fee), and on Collective2 "Every one of these managers sells subscriptions to the strategy, at $25 to $249 a month". On a `$500` account, `$25` to `$249/month` (`$300` to `$2,988/year`) is a `-60%` to `-598%` annual fixed-fee drag before a single trade or slippage. Follower returns on Robbins World Cup Advisor AutoTrade are UNKNOWN in aggregate.

US $500 reachability: No. USIC requires `$20,000` (`$475` entry fee) or `$1,000,000` (`$1,000` entry fee); WCTC requires `$10,000` for annual futures and `$5,000` for annual forex; Darwinex is a UK-regulated broker ("Darwinex is a UK-regulated broker that records every trade and pays a trader 15% of the profits made by investors who follow the strategy", [DoesItPay](https://www.doesitpay.org/trading-bots/research/)); Collective2 subscription fees overwhelm a `$500` account.

Doc 117 screen: `UNKNOWN` (no trade-by-trade fill log exists for USIC/WCTC; Collective2 fixed subscription fees make net edge deeply negative on `$500`).

Verdict: DROP. Audited contests prove that rare individuals can compound over multiple years, but they do not publish verifiable trade-by-trade fills or extractable mechanical rules, and broker-verified copy marketplaces are either UK-restricted or destroyed by fixed subscription fees on `$500`.

## Synthesis: what the verified 2023 to 2026 records actually show

Across all eight trade-by-trade verifiable sources, two structural findings repeat consistently:

- Persistent, verifiable winners in 2023 to 2026 crypto are not directional chart traders. They are protocol market-making and backstop-liquidation vaults (Hyperliquid HLP: `+$140.7M`, 91% of depositors ahead, ~41% of lifetime profit from two crash-day liquidation bursts) and vertically integrated CEX-DEX arbitrage searchers (top 3 capture `90%` of volume and extracted value via exclusive Ethereum block-builder integration). Both rely on exchange-level or block-builder infrastructure that a `$500` US retail account on Coinbase, Kraken, or a US stock broker cannot legally or technically access.
- Directional retail leaders and copy-trading systems fail out of sample across every measured venue. Hyperliquid user vaults lost `-$32.3M` for depositors (64% down) and `-$55.9M` for leaders; 69% of Hyperliquid leaderboard master blow-ups happened suddenly with no behavioral warning; ZuluTrade's top fifth lost `-7.7%` per quarter (`-72.5%` cumulative before fees); Binance/Bybit/MEXC leaders earned 50% to 75% of profit from copier commissions while only 43.61% of followers were positive; eToro mirrored trades averaged `-61.24 bps`; Polymarket live smart-money copy trading lost `-3.04 USDC` due to 112-second confirmation gaps; and only 17% of 2026 USIC entrants were profitable at mid-year.

Because no persistent, trade-by-trade verifiable style is both reachable on a `$500` US account and positive under the Doc 117 screen, **0 new queue rows are added** in Round 40 (rows from 110 stay unused).
