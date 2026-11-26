# Round 61: What a Thin, Cheap US Venue Allows (and Does Not Allow)

Date: 2026-11-26 22:45 UTC
Scope: Microstructure, execution, and venue-risk review of what a thin, low-fee US spot venue (Binance.US: 0.00% maker, 0.02% taker on most USD pairs, 0.01% on BNBUSD; Measurement 132 first hour near 7 to 8 bp a side at $250 vs about 62 bp on Coinbase, one snapshot, not a verdict, `docs/research/182_measurement_132_venue_cost.md`) allows on a $500 to $2,000 Idaho account that a busy, dear venue does not. Round 60 (`docs/research/185_round_60_using_the_cost_finding.md`) ruled that Measurement 132 is used forward only; E10 and E11 already price two existing rules on Binance.US books.

## Summary Table

| Question | Angle | Verdict | Core reason |
|---|---|---|---|
| 1 | Stale quotes (cross-venue lead-lag) | WATCH | Lead-lag on liquid coins lives at milliseconds to low seconds and simple taker rules lose after fees; thin altcoin multi-second lag is UNKNOWN and untestable on history |
| 2 | Two-venue inventory price gaps (no transfers) | DROP | Busy-venue retail fees (40 to 90 bp/side), 7-day ACH holds, wire fees, stablecoin basis, and IRS wallet-by-wallet tax lots kill it at $500 to $2,000 |
| 3 | Resting orders at 0% maker fee | KEEP (narrow overlay only; DROP standalone market making) | Standalone passive market making loses to adverse selection even with a rebate; only a time-capped `LIMIT_MAKER` entry/exit overlay on E10 (Plan 75) is worth testing forward |
| 4 | Binance.US venue risk | WATCH (mandatory pre-account gate) | SEC suit dismissed with prejudice, but no cryptographic proof of reserves, unnamed USD custodial banks, 7-day ACH holds, and a proven 18-month USD rail outage in 2023 to 2025 |
| 5 | Single-venue idiosyncratic dislocation mean reversion | KEEP | Uses Binance.US's 2 bp taker fee alone (no second-venue fee or transfer) to test whether local thin-book selloffs revert toward Coinbase's midpoint; forward-only |

## Question 1: Stale Quotes (Cross-Venue Lead-Lag)

### What Published Work Says

- STATED: In liquid Bitcoin markets, cross-venue lead-lag operates at **sub-second to low-second** horizons, and dominant global derivatives venues lead spot venues. [Fragmentation, Price Formation, and Cross-Impact in Bitcoin Markets (arXiv:2108.09750)](https://ar5iv.labs.arxiv.org/html/2108.09750) states: "Perpetual swaps and quarterly futures on Binance and Huobi were found to be particularly strong leading markets, while the Bybit and FTX perpetuals were found to be strong laggards." and "It demonstrates that it is possible and indeed quite feasible to anticipate future price moves in Bitcoin markets on sub-1s time scales, and it is a reassuring demonstration of the utility of our features."
- STATED: Simple cross-venue taker rules lose money after exchange fees unless a venue lags beyond its fee barrier. The same [arXiv:2108.09750 paper](https://ar5iv.labs.arxiv.org/html/2108.09750) states: "Evidence in support of this assertion was provided in the previous subsection, where we observed that a single market’s features are insufficient to produce ‘alpha’ in excess of execution cost on another market (with rare exceptions for VIP traders that receive heavy fee discounts)." and "Only when a market exhibits lagging behaviour in excess of the laggardness to which it is naturally predisposed by its fee structure do we obtain trading ‘alpha’ that can be exploited to generate positive PnL values on the market in question."
- UNKNOWN: Whether Binance.US's thin USD altcoin books (outside BTC and ETH) lag Coinbase Exchange or Binance global by **multiple seconds** with enough $250 depth to clear Binance.US's 2 bp taker fee plus spread is not measured in published literature and **cannot be tested on history**, because neither Binance.US nor Coinbase publishes free historical order-book archives (`docs/research/185_round_60_using_the_cost_finding.md`).

### What a No-Account Forward Measurement Looks Like (and What It Cannot Prove)

- INFERENCE: Using only public WebSocket or REST book endpoints (no account, no API key), log paired top-of-book and $250 depth snapshots on Coinbase Exchange and Binance.US every 1 to 2 seconds on the 20 Plan 70 USD coins, stamped on one local collector clock. When Coinbase's midpoint jumps by at least 30 bp over 5 seconds, check whether Binance.US's $250 ask (or bid) 2 seconds later is still at least 15 bp behind Coinbase's new midpoint and whether Binance.US catches up within 10 to 60 seconds.
- INFERENCE: What this public measurement **cannot prove**: (1) whether a real taker order sent from Idaho or a cloud box would actually fill before the market maker cancels or a faster colocated taker sweeps the level (latency-induced adverse selection), (2) true matching-engine timestamp alignment across two separate venues, and (3) whether the resting size was real or already in flight.

### Verdict: WATCH

INFERENCE: **Watch**, do not keep as a standalone strategy yet. On BTC and ETH, sub-second competition makes a home-latency stale-quote taker hopeless. On thin Binance.US USD altcoins, multi-second lag is UNKNOWN and untestable on history; it is worth watching only as a low-cost diagnostic alongside Question 5's paired-book logger, not as a dedicated build.

## Question 2: Price Gaps Held With Inventory on Both Venues (No Transfers)

### What Published Work Says

- STATED: [Makarov and Schoar (2020, Journal of Financial Economics)](https://dspace.mit.edu/bitstream/handle/1721.1/130495/SSRN-id3171204.pdf) studied 34 exchanges across 19 countries and found large, multi-day gaps mostly **across** countries with capital controls, not within the US: "Second, price deviations are much larger across countries (or regions) than within the same country." and "In contrast, the price deviations between exchanges in the same country typically do not exceed 1%, on average." and "While, in theory, prices across exchanges may not converge for a long time, Fig. 4 shows that, in practice, arbitrage opportunities in any given market open for less than two days, on average, and even in the extreme never existed for more than a month."
- UNKNOWN: Exact 2025 to 2026 median gap size and half-life between Coinbase Exchange USD and Binance.US USD on our 20 coins is not published; Measurement 132 will show hourly snapshots over 30 days.

### What Kills It for a $500 to $2,000 Account

- STATED (busy-venue fees): Even if Binance.US costs 2 bp taker, the second leg on a busy US venue destroys the trade at small-account volume tiers. [Kraken Support](https://support.kraken.com/articles/cross-platform-fee-tier-changes) states Tier 1 ($0+ spot volume) is 0.40% maker and 0.80% taker (40 to 80 bp per side); `docs/research/180_round_57_cost_as_the_binding_limit.md` documents Coinbase retail taker fees at 60 bp+ (and Alpaca at 25 bp taker + spread). A round-trip rebalancing across Binance.US and Coinbase or Kraken starts in an 80 to 160 bp hole before spreads.
- STATED (withdrawal holds and wire fees): Once inventory builds up on one side, moving cash back is slow and costly. [Binance.US Help Center](https://support.binance.us/en/articles/9842927-why-can-t-i-withdraw) states: "Binance.US applies a 7-day withdrawal hold (equal to 168 hours) to all ACH deposits to ensure financial security." and "Additionally, this hold applies to both the USD deposit and any cryptocurrency purchased with those funds, including stablecoins such as USDT." and "No, the 7-day hold period cannot be waived, shortened, or bypassed under any circumstances." Wire withdrawals cost $25 ($100 minimum) and take 1 to 5 business days (`support.binance.us`, checked 2026-11-26).
- MEASURED (minimum order size and depth): Binance.US `minNotional` is $1.00 across all 20 Plan 70 USD pairs (`exchangeInfo`, 2026-11-26), so minimum size is not the blocker; thin altcoin top-of-book depth during fast moves is.
- INFERENCE (USD vs stablecoin basis): If one venue holds USDT or USDC while the other holds USD, even a 10 to 30 bp stablecoin basis wobble swamps a typical within-US price gap.
- STATED (US tax-lot fragmentation): Under final IRS digital-asset regulations effective January 1, 2025, [IRS Rev. Proc. 2024-28](https://www.irs.gov/pub/irs-drop/rp-24-28.pdf) states: "Section 1.1012-1(h) and (j) of the 2024 final regulations will apply to all acquisitions and dispositions of digital assets on or after January 1, 2025." and that § 1.1012-1(j) rules "apply the specific identification or FIFO rules to units held within a single wallet or account." Holding the same coin on two exchanges splits tax lots across separate accounts and creates taxable short-term dispositions on every arbitrage sell leg.

### Verdict: DROP

INFERENCE: **Drop**. Two-venue inventory arbitrage between US dollar exchanges is structurally unworkable at $500 to $2,000 because the dear venue's entry-tier fee (40 to 90 bp/side) is larger than typical within-US USD price gaps, and rebalancing hits 7-day ACH holds, $25 wire fees, and per-account IRS tax-lot fragmentation.

## Question 3: Resting Orders at a Zero Maker Fee

### What Published Work Says About Adverse Selection

- STATED: Live experiments show that passive maker orders suffer severe adverse selection even on the deepest crypto book in the world and even with a negative maker rebate. [Albers, Cucuringu, Howison, and Shestopaloff (2025, arXiv:2502.18625)](https://arxiv.org/html/2502.18625v1) ran two live experiments totaling 405,697 minimum-sized maker orders on Binance's BTCUSDT perpetual (127,051 fills in Continuous Quoting Mode; 95,998 fills in Periodic Quoting Mode) and reported: "For maker orders, we find a negative correlation between fill likelihood and subsequent short-term returns, posing a significant challenge for maker order-based strategies, while the main hurdle with taker orders is overcoming the taker fee."
- STATED: Same paper on the mechanical cause and bottom line: "If the next price move is against a maker order in the top-of-book queue, that order automatically fills, with probability 1, a phenomenon sometimes referred to as adverse selection." Even assuming Binance's best VIP tier (-0.5 bp maker rebate), the authors conclude: "The naive market making strategy is thus a recipe for poverty – heaven help the starry-eyed novice traders, fresh from academia, who, seduced by maker rebates, attempt to implement this strategy in practice."
- INFERENCE: In thin equity or thin altcoin books, wider spreads look tempting to a small passive trader, but adverse selection is worse when informed flow hits a thin book and the passive trader cannot cancel in milliseconds.

### US Maker Rebate Programs for a Small Idaho Account

- STATED: **No US spot venue offers a maker rebate (negative fee) to a $500 to $2,000 retail account.**
- STATED: On [Kraken Pro](https://support.kraken.com/articles/cross-platform-fee-tier-changes), Tier 1 ($0+ 30-day spot volume) pays **0.40% maker / 0.80% taker**; reaching 0.0% spot maker requires $10M+ 30-day spot volume (or $10M Assets on Platform), and Kraken's spot table shows no negative spot maker fee (negative futures maker rebates of -0.0030% start at Tier 11: $5M+ spot volume, $250M+ futures volume, or $5M AoP).
- STATED: On Binance.US (`docs/research/180_round_57_cost_as_the_binding_limit.md`), the lowest tier is **0.00% maker / 0.02% taker** (0.01% on BNBUSD) for Idaho accounts, which is zero fee rather than a negative rebate.

### Binance.US Order Rules (STATED and MEASURED)

STATED from the [Binance.US API Documentation](https://docs.binance.us/):

- Post-only orders (`LIMIT_MAKER`): "This is a LIMIT order that will be rejected if the order immediately matches and trades as a taker. This is also known as a POST-ONLY order" (rejection message: "Order would immediately match and take").
- Tick size (`PRICE_FILTER`): "tickSize defines the intervals that a price/stopPrice can be increased/decreased by" and orders must satisfy `price % tickSize == 0`.
- Minimum notional (`NOTIONAL`): `price * quantity >= minNotional`.
- Self-trade prevention (`selfTradePreventionMode`): "STP is a measure to prevent users from trading against their own account or other accounts that share the same tradeGroupId" with default `EXPIRE_MAKER` and supported modes `EXPIRE_TAKER`, `EXPIRE_MAKER`, `EXPIRE_BOTH`, `DECREMENT`, and `TRANSFER`.

MEASURED directly from `api.binance.us` `exchangeInfo` on 2026-11-26 across all 20 Plan 70 USD pairs:

- All 20 pairs (`AAVEUSD`, `ADAUSD`, `AVAXUSD`, `BCHUSD`, `BNBUSD`, `BTCUSD`, `DOGEUSD`, `DOTUSD`, `ETHUSD`, `HBARUSD`, `LINKUSD`, `LTCUSD`, `NEARUSD`, `PEPEUSD`, `SHIBUSD`, `SOLUSD`, `SUIUSD`, `XLMUSD`, `XRPUSD`, `ZECUSD`) have `status = TRADING`, `LIMIT_MAKER` enabled, `minNotional = $1.00`, and `defaultSelfTradePreventionMode = EXPIRE_MAKER`.
- Tick sizes are fine enough for tight quoting: `$0.1` on `BCHUSD`; `$0.01` on `BTCUSD`, `ETHUSD`, `LTCUSD`, `BNBUSD`, `ZECUSD`, `SOLUSD`, `AAVEUSD`; `$0.001` on `LINKUSD`, `AVAXUSD`, `DOTUSD`, `NEARUSD`; `$0.0001` on `SUIUSD`, `XRPUSD`; `$0.00001` on `ADAUSD`, `XLMUSD`, `HBARUSD`, `DOGEUSD`; and `$0.00000001` on `SHIBUSD`, `PEPEUSD`.

### Verdict: KEEP (Narrow Execution Overlay Only; DROP Standalone Market Making)

- DROP standalone passive market making: Albers et al. (2025) proves naive passive quoting loses to adverse selection even with a -0.5 bp rebate, and no US venue pays a rebate to a small Idaho account.
- KEEP a narrow **time-capped `LIMIT_MAKER` execution overlay** on an existing directional rule (**Plan 75 / E10** at 00:00 UTC, median 8-day hold), where the signal already decides direction and the only question is whether resting at the top bid/ask for 3 minutes before crossing as a 2 bp taker saves net spread cost.

### Specification for Kept Idea 1 (Time-Capped `LIMIT_MAKER` Overlay on E10)

- Exact thing measured: On every E10 (Plan 75) 00:00 UTC buy or sell signal on Binance.US USD pairs, compare two paper fills on the same trade: (A) immediate $250 market/taker fill at 00:00:10 UTC (ask/bid walk + 2 bp fee) versus (B) a hypothetical resting `LIMIT_MAKER` order posted at the 00:00:10 UTC best bid (for buys) or best ask (for sells), marked filled at 0 bp fee only if public Binance.US trade prints trade strictly through our limit price (or clear the initial displayed queue size at our price) within 180 seconds, and otherwise crossed at the 00:03:10 UTC market-order book + 2 bp fee.
- Data needed and availability: Public Binance.US order-book depth snapshots (`depth`) and public aggregate trades (`aggTrades`) over the 180-second window after 00:00 UTC. Both are free with **no account and no API key** (`docs.binance.us`).
- Testable on history? **No.** Free historical klines and `aggTrades` lack historical top-of-book quotes and queue sizes, so nothing here is testable on history; it must run strictly forward.
- Pass mark fixed in advance: Over at least 60 E10 trade signals (minimum 60 days), the time-capped `LIMIT_MAKER` overlay beats immediate taker execution by a median net saving of at least **3 bp per side** (including the adverse-move penalty on unfilled orders that cross 180 seconds later), with positive mean net saving after trimming the best 5% of fills.
- Strongest reason it could be false: Classic passive adverse selection: the orders that fill within 180 seconds are disproportionately the ones where price keeps moving against us, while the orders that run away unfilled force us to chase at a worse price 3 minutes later, making the 3-minute wait cost more than the 5 to 8 bp spread it tried to save.

## Question 4: Venue Risk on Binance.US (Official Venue and Regulator Pages Only)

### Banking and USD Rails (STATED by Binance.US)

- STATED: USD deposits and withdrawals resumed in 2025 via ACH and Wire. [Binance.US Help Center](https://support.binance.us/en/articles/9842927-why-can-t-i-withdraw) states: "Withdrawals are only available via ACH and Wire." and "Binance.US applies a 7-day withdrawal hold (equal to 168 hours) to all ACH deposits to ensure financial security." and "Additionally, this hold applies to both the USD deposit and any cryptocurrency purchased with those funds, including stablecoins such as USDT." and "No, the 7-day hold period cannot be waived, shortened, or bypassed under any circumstances."
- STATED: ACH deposits and withdrawals have $0 Binance.US fees, link via Plaid ($3,000 daily deposit limit for Basic Verification), and ACH withdrawals take 1 to 5 business days depending on the bank (`support.binance.us`). Wire deposits are $0 from Binance.US; wire withdrawals have a $100 minimum, a $25 fee, and take 1 to 5 business days (`support.binance.us`).
- MEASURED (historical rail fragility): Binance.US lost USD trading pairs for 18 consecutive months from 2023-08 through 2025-01 (`docs/research/185_round_60_using_the_cost_finding.md`), proving banking-partner interruption is a real historical risk, not a hypothetical.

### Custody, Proof of Reserves, and FDIC Status (STATED by Binance.US)

- STATED from [Binance.US Trust and Security](https://www.binance.us/trust): "The exchange keeps user assets 1:1 and stores the majority of crypto in offline, U.S.-based cold storage, secure from online threats." and "Binance.US never lends or trades your funds without your permission."
- STATED on audits: "Binance.US completed a SOC 2 Type II audit and holds ISO 27001:2022 and ISO 27701:2019 certifications, all issued by independent auditors." and "SOC 2 Type II is a voluntary audit that examines security controls over an extended period of time."
- UNKNOWN (critical gap): The [Binance.US Trust page](https://www.binance.us/trust) does **not** publish a cryptographic Merkle-tree proof-of-reserves or an independent CPA financial/reserve attestation; SOC 2 Type II and ISO 27001/27701 audit IT security and privacy controls, not balance-sheet solvency.
- STATED on FDIC and USD custody: "No, cryptocurrency is not FDIC insured." and "FDIC and SIPC do not cover digital assets at any exchange." and "USD balances are held at custodial institutions." The Trust page does **not** name those custodial institutions, so the identity of the partner bank(s) and whether pass-through FDIC applies to a specific customer balance are UNKNOWN.

### Regulator Status (Official Regulator Pages)

- STATED (SEC): On May 29, 2025, [SEC Litigation Release No. 26316](https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26316) announced: "The Securities and Exchange Commission today filed a joint stipulation with Defendants Binance Holdings Limited, BAM Trading Services Inc., BAM Management US Holdings Inc., and Changpeng Zhao to dismiss, with prejudice, the Commission’s ongoing civil enforcement action against them." It adds: "the Commission’s decision to seek dismissal of this Litigation does not necessarily reflect the Commission’s position on any other litigation or proceeding."
- STATED (CFTC): The CFTC's 2023 enforcement action ([CFTC Release No. 8837-23](https://www.cftc.gov/PressRoom/PressReleases/8837-23), Dec 18, 2023) resolved charges against offshore Binance Holdings and Changpeng Zhao (BAM Trading Services Inc. was not a defendant). As of November 2026, [CFTC Industry Filings](https://www.cftc.gov/IndustryOversight/IndustryFilings/TradingOrganizations) list `BAM Derivatives LLC` as a pending DCM application (dated 11/19/2026) and `BAM Clearing LLC` as a pending DCO application (dated 09/21/2026).
- STATED (state money-transmitter scope): BAM Trading Services Inc. is registered with FinCEN as an MSB and licensed as a money transmitter in 33 states ([Binance.US Trust](https://www.binance.us/trust)), with 12 states and 4 territories still excluded and Wisconsin crypto-only (Idaho is eligible with USD; `docs/research/180_round_57_cost_as_the_binding_limit.md`). Whether any non-public state examination or inquiry remains open is UNKNOWN.

### Verdict: WATCH (Mandatory Pre-Account Gate)

INFERENCE: **Watch**. The federal SEC overhang is formally dismissed with prejudice, but Binance.US still carries meaningful venue risk: no cryptographic or CPA proof of reserves, unnamed USD custodial banks, unwaivable 7-day ACH holds, and a recent 18-month USD outage. If an account is ever considered after Measurement 132 and forward paper logs pass, cap exposure strictly to a small test balance ($500 to $1,000), never park idle savings there, and test a small ACH round-trip deposit and withdrawal first.

## Question 5: Single-Venue Idiosyncratic Dislocation Mean Reversion

### The Mechanism (Why It Fits a Thin, Cheap Venue)

- STATED: [Makarov and Schoar (2020, JFE)](https://dspace.mit.edu/bitstream/handle/1721.1/130495/SSRN-id3171204.pdf) documented that single-exchange dislocations predict local mean reversion: "When the price on any exchange deviates above (below) from the average price on other exchanges, subsequent returns on this exchange are predicted to be lower (higher) than the returns on other exchanges."
- INFERENCE: Unlike Question 2 (which requires inventory on two exchanges and pays Coinbase's 60 to 90 bp fee), a **single-venue dislocation fade** holds USD only on Binance.US. When an uninformed local market sell pushes Binance.US's $250 USD ask far below Coinbase Exchange's live midpoint on one of our 20 coins (for example, >= 40 bp cheap and persisting for at least 10 seconds so it is not a single-tick glitch), a trader buys on Binance.US alone (2 bp taker fee) and exits back on Binance.US once the local bid reverts within 10 bp of Coinbase's midpoint or after a fixed time stop (for example, 4 hours). Total round-trip exchange fee is 4 bp, zero transfers, single-venue tax lots, and hold time is minutes to a few hours.

### Verdict: KEEP (Zero-Account Forward Measurement First)

- Exact thing measured: Using paired live public books on Coinbase Exchange and Binance.US across the 20 Plan 70 USD coins, detect every event where Binance.US's $250 executable ask sits at least **40 bp below** Coinbase's live midpoint across two consecutive polls 10 seconds apart (confirming persistence beyond a 1-second stale print). Mark a hypothetical $250 taker buy on Binance.US at the second poll (+2 bp fee), and mark the exit at Binance.US's $250 executable bid (+2 bp fee) at the first poll where Binance.US's bid returns within 10 bp of Coinbase's midpoint, or at a hard 4-hour time stop, whichever comes first. Compare against the matched Coinbase midpoint return over the exact same entry-to-exit timestamps to separate local basis reversion from general market drift.
- Data needed and availability: Public order-book depth snapshots on Coinbase Exchange and Binance.US polled every 5 to 10 seconds (or WebSocket book streams). Both are free with **no account and no API key**.
- Testable on history? **No.** Historical Binance.US klines cannot distinguish an executable $250 ask discount from a single stale print, lack paired synchronized Coinbase books, and are missing 18 months of USD history (2023-08 through 2025-01). Only a live forward measurement is honest.
- Pass mark fixed in advance: Over 60 calendar days, require at least **30 distinct dislocation events** across at least **15 separate UTC days**, positive plain net return per event (after executable $250 book walk and 4 bp RT taker fee) of at least **+15 bp**, positive mean after removing the top 5% of events, and a day-clustered t-statistic of at least **2.0** on the paired basis-reversion return (Binance.US net return minus matched Coinbase midpoint return).
- Strongest reason it could be false: Persistent venue-specific discounts or toxic local flow. If Binance.US trades at a discount to Coinbase because of a Binance.US banking or withdrawal rumor (as in June 2023) or because an informed seller is dumping on Binance.US first, the local price does not revert to Coinbase; instead Coinbase falls to meet Binance.US, or Binance.US stays discounted past the 4-hour stop, turning every fade into a losing catch of a falling knife.
