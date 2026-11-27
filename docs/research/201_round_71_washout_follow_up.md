# 201. Round 71: Washout Reversal Follow-Up on Thin Pairs and Resting Bids

This note builds on our newest held-back result, Plan 76 (`docs/research/200_plan_76_heldback_result.md`, ledger 229), and live practice card E14 (ledger 233). It does not rescore or re-cut Plan 76's held-back trades, makes no claim that any washout rule works, and makes zero requests to Binance.US.

Labels used throughout:

- MEASURED: observed directly in our own repo runs or read directly from a primary paper or venue documentation page opened for this note.
- STATED: a venue fee, policy, or author claim taken as reported without independent execution proof.
- UNKNOWN: not reported in the opened sources or not measurable without a live book or custodian pull.

Summary of the starting point from `docs/research/200_plan_76_heldback_result.md` (MEASURED): buying the largest one-hour faller of 5% or more among 11 coins on Bitstamp USD hourly bars and holding 24 hours earned +1.88% per trade before costs across 83 held-back trades (2024 to 2026). It met 3 of 4 marks and failed 1 of 4 at 75 bp a side (+0.36% mean; only the mean without each year's best trade failed, at -0.28%) and met all 4 marks at 15 bp a side (+1.57% mean, +0.93% without each year's best trade). The blind recompute showed the gain sat in 2024 (+3.71% over 42 trades, vs -0.44% over 25 trades in 2025 and -0.91% over 16 trades in 2026) and in the four thinnest pairs (AAVE, SHIB, HBAR, LINK: 54 of 83 signals, +2.90% at 15 bp; the other 29 trades lost 0.89%).

## Second check and ruling

Second-check tally across 13 cited sources: 10 confirmed, 3 corrected, 0 not found (the three corrections are applied below). Lead ruling: neither Plan A nor Plan B is registered as written.

Reasons neither plan is registered:

- Plan A's tie-break looked ahead: picking the largest hourly close-to-close faller of hour `t + 1` requires knowing how the hour ends when a resting bid fills mid-hour.
- Survivor risk in the pair list: requiring pairs continuously listed from 2022 to 2026 strips out delisted thin coins that crashed and never rebounded.
- Candle fills can be phantom (total bar quote volume does not prove volume traded below `bid`), and Plan A's 25 bp adverse-selection haircut is invented and uncalibrated.
- Neither plan is independent of Plan 76, because altcoins fall together during the same 2024 to 2026 market drops.
- Both spans straddle Binance.US's June 2023 to early 2025 disruption, mixing pre-lawsuit, crypto-only distress, and post-restoration regimes.
- The 80-fill count floor gives only about 26% power on the t mark alone at +1.5% net and 10% SD, under the plan's own 33% power floor (and true power across all five day-clustered marks is lower still).
- The cost gate was unpinned and could be tuned after seeing Measurement 133, E14, or design results.
- Plan B duplicates live practice card E14 on less realistic candle data.

## 1. Outside evidence from primary papers

Short-term reversal in crypto is heavily concentrated in small, low-volume, illiquid coins, while the largest liquid coins show momentum or near-zero net reversal. Across primary papers that apply realistic trading costs on single venues, net returns shrink sharply or turn negative, and recent 2025 to 2026 data show measurable decay even before depth and adverse selection are priced.

Illiquidity concentration and survival after spreads:

- Bianchi, Babiak, and Dickerson (2022), [Trading Volume and Liquidity Provision in Cryptocurrency Markets](https://www.riksbank.se/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf) (MEASURED from paper, 300+ USD pairs across 80+ exchanges via CryptoCompare, March 1, 2017 to March 1, 2022, daily rebalance within the top 100 pairs by prior-month Amihud ratio): conditional on low de-trended volume, daily reversal earned +1.226% per day gross equal-weighted (Sharpe 0.299) and +0.625% value-weighted, versus +0.543% equal-weighted and -0.187% value-weighted in high-volume coins. Cost assumption: Table 5 applies a flat 20 bp long and 30 bp short per daily rebalance (50 bp round-trip; Section 2.2 prose states 30 bp long and 40 bp short). After Table 5 costs, only equal-weighted low-volume reversal stayed positive and significant (+0.726% per day, p < 0.01); value-weighted mid- and high-volume portfolios turned significantly negative (-0.570% and -0.687% per day). On a single liquid venue (Binance USDT, Table 7, October 1, 2018 to March 1, 2022), low-volume reversal fell to +0.187% per day gross equal-weighted (+0.059% value-weighted) and turned negative after fees at -0.213% equal-weighted and -0.341% value-weighted. Average spread proxies in the low-return, low-volume bucket were 9.87% (Abdi-Ranaldo) and 4.59% (Corwin-Schultz).
- Zaremba, Bilgin, Long, Mercik, and Szczygielski (2021), [Up or Down? Short-Term Reversal, Momentum, and Liquidity Effects in Cryptocurrency Markets](https://www.wir.ue.wroc.pl/docstore/download/UEWR135bdc5e34ad49868fe8a5e77fa021c7/Mercik_Up_or_down_Short-term_reversal.pdf) (MEASURED from paper, 3,607 coins averaging 1,126 per day, January 1, 2015 to March 1, 2021): daily loser-minus-winner reversal was +13.19% equal-weighted (+3.84% value-weighted) in the smallest 98% of coins and +7.12% equal-weighted (+1.75% value-weighted) in the 98% most illiquid coins by Amihud ratio. The top 2% largest and most liquid coins (about 23 coins, 94%+ of market cap) showed daily momentum instead (+0.22% to +0.31% winner-minus-loser; note the paper's tables label mean daily excess return while one prose line says per month). Cost assumption: no numerical net-of-cost backtest was run; the authors note Roll-estimated spreads reach several percent in small and mid-cap coins and conclude that reversal is hard to implement in practice.

Bid-ask bounce and stale prices:

- Zaremba et al. (2021) attribute illiquid-coin reversal to both bid-ask bounce and temporary liquidity shocks, without separating their shares numerically (STATED).
- Kitron and Wengrowicz (2026), [Short-Horizon Mean Reversion in Cryptocurrency Markets](https://arxiv.org/html/2608.21888v1) (MEASURED from paper, 183 highest-volume Binance USDT spot pairs vs 187 US stocks and ETFs on 15-minute bars, primary sample January 1, 2025 to February 11, 2026, holdout February 12, 2026 to August 8, 2026, plus 2021 to 2026 on BTC, ETH, SOL, XRP): directly tests bounce and staleness. Using quote-midprice bars (Dukascopy bid/ask averages, where bid-ask bounce cannot occur) leaves the signal unchanged (BTC AUC 0.529, ETH AUC 0.537). Adding a one-bar gap between features and labels retains 71% of the excess AUC over stocks (crypto AUC drops from 0.531 to 0.522, 81% of pairs still significant); dropping flat bars moves AUC from 0.531 to 0.520; both controls together still leave a +0.011 AUC gap over stocks (0.5093 vs 0.4980). Across the 183-pair volume cross-section, volume-quintile mean AUC is flat at 0.518 to 0.524 on non-flat bars only (raw ex-ante volume-quintile mean AUC is 0.530 to 0.538). Even so, the gross edge peaks at just 1.3 bp per trade (0.46 bp median pair at threshold 0.02; 0.15 bp on 5-minute bars). Cost assumption: 5 bp round-trip maker band and 10 to 20 bp round-trip taker band (explicit spot fees only, excluding depth, latency, and adverse selection). Zero of 183 pairs clear even the 5 bp maker band at any threshold.

What the papers say about the years after 2022:

- In [Kitron and Wengrowicz (2026)](https://arxiv.org/html/2608.21888v1), 15-minute directional reversal remains statistically present in all 24 of 24 focal coin-years from 2021 through partial 2026 (AUC 0.523 to 0.550), but attenuates in the 2026 holdout: mean crypto AUC falls from 0.531 (2025-01 to 2026-02) to 0.522 (2026-02 to 2026-08), the FDR-significant share falls from 90% to 60%, and 77% of that drop is genuine decay on a fixed universe rather than pair turnover.
- Ballis and Ioannidis (2026), [Market Efficiency in a Changing Asset Population](https://arxiv.org/html/2610.23283v2) (MEASURED from paper, 8,970 coins, April 2013 to July 2026): does not test short-term reversal, but tracks the broader illiquid-coin premium through the consolidation era (July 2021 to July 2026). Under a 2% one-way cost assumption, the bottom-decile weekly net return is +1.28%/week at a $10,000 daily volume floor, drops to -0.08%/week at a $100,000 volume floor (+0.38%/week at 1% one-way cost), and falls to -3.69%/week at a $1,000,000 volume floor.
- Whether a 1-hour-drop, 24-hour-hold washout reversal on thin US-reachable pairs survived costs after 2024 is UNKNOWN in the primary literature; our own Plan 76 held-back sample lost money in both 2025 (-0.44%) and 2026 (-0.91%) even at 15 bp a side (MEASURED).

## 2. The resting-bid version, adverse selection, and candle fill rules

Replacing a post-washout market order with a resting bid below the last hourly close removes the entry taker fee and avoids crossing the entry spread, but it replaces spread cost with adverse selection: resting bids fill with near-certainty when price keeps falling and miss the fast bounces.

Primary evidence on limit-order fills and adverse selection:

- Albers, Cucuringu, Howison, and Shestopaloff (2025), [The Market Maker's Dilemma](https://arxiv.org/html/2502.18625) (MEASURED from live Binance BTC perpetual experiment, 232,897 continuous-quoting orders with 127,051 fills in February 2024, plus 172,800 periodic orders in August 2024): conditioned on the immediate mid-price change, a resting maker order fills with probability 0 when that change is favorable (positive) and probability 1 when it is zero or adverse (negative). Every single queue-position bucket had a negative 1-second markout (-0.058 bp to -1.157 bp before rebates), and the overall 5-second expected markout was -0.8 bp (-0.3 bp net of a 0.5 bp/side maker rebate). A naive market-making loop lost -0.44 bp per round trip even after 1 bp round-trip rebates (losing almost 60% of equity in 3 days and 7 hours, annualized Sharpe -109.0).
- DeLise (2024), [The Negative Drift of a Limit Order Fill](https://arxiv.org/html/2407.16527v1) (MEASURED from TY Treasury futures live simulation, 1,683 orders and 576,670-event backtest comparison): resting limit orders filled 99% of the time during adverse price moves (P(fill | adverse) = 0.99). Average post-fill drift over the next 100 events was -0.45 ticks, nearly equal to half-tick market-order slippage. A naive backtest assuming 100% fills against arriving market orders produced 11,859 fills vs 1,985 in the live simulation and severely overstated profit.
- Bieganowski and Slepaczuk (2026), [Explainable Patterns in Cryptocurrency Microstructure](https://arxiv.org/html/2602.00776) (MEASURED on 1-second Binance Futures order books across BTC, LTC, ETC, ENJ, ROSE, January 2022 to October 2025): zero of five coins showed statistically significant maker profits (ENJ -81%/year compounded, ETC -7%/year). During the October 10, 2025 flash crash, passive bids were repeatedly picked off into one-way selling with no offsetting ask fills, wiping out thousands of dollars in simulated equity.
- Our own Measurement 121 (`docs/research/170_m121_result.md`, ledgers 223 and 224, MEASURED): pretend $500 bids resting at the best bid for 30 minutes across 23 US closed-end funds filled 7.56% of the time (227 of 3,003), and five minutes after a fill the best bid was 26.6 bp below the fill price on average (95% interval -30.3 to -23.0 bp, median -22.0 bp) on the 136 markable fills.

Honest, conservative fill rule on candle data:

- Compute the bid price strictly from the last closed bar (`bid = close_t * (1 - d)` for a fixed drop distance `d`), and allow the order to rest only during the next bar `t + 1`.
- Count a fill only if three conditions all hold on bar `t + 1`: (1) `open_{t+1} > bid` (if the bar opens at or below `bid`, a post-only order placed after bar `t` closed would reject or cross as taker, so treat it as no fill), (2) `low_{t+1} < bid` strictly below the limit price (never `<=`), and (3) bar `t + 1` quote volume is at least 10 times our order size ($2,500 for a $250 ticket) so a single tiny dust print cannot trigger a fill.
- Record the entry price at `bid` (never at `low_{t+1}`), with 0% maker fee (STATED by Binance.US).
- Exit strictly on a later bar (for example 24 hours after the fill bar closes) as a taker at that exit bar's open, minus the 2 bp taker fee (STATED) and minus a full exit half-spread and walk-cost term. Never use an intra-bar stop or profit target on the fill bar.

What this conservative candle fill rule still gets wrong:

- Volume above vs below the limit price is UNKNOWN on candles: a bar with $5,000 of total volume and `low < bid` can have $4,995 traded above `bid` and a single $5 print one tick below `bid`, which would not fill a $250 resting order.
- Queue position and penny-jumping are invisible: as [Albers et al. (2025)](https://arxiv.org/html/2502.18625) note for synthetic orders, inserting a hypothetical $250 bid into a thin book ignores market impact. In live trading, other bots step one tick ahead of visible resting bids on thin pairs, causing our order to miss shallow bounces and fill disproportionately on deep selloffs.
- Missed-fill selection bias cannot be calibrated from candles: candle bars cannot distinguish a quick 2-second dip that barely trades through `bid` from sustained selling, so the true live fill rate on winners vs losers remains UNKNOWN until tested on live books.
- Intra-bar timing is hidden: on hourly bars, a fill at minute 1 and a fill at minute 59 are treated identically even though the 24-hour exit clock differs by almost an hour.
- Exit prints are last-trade prices, not live walked bids: candle opens bounce between bid and ask, so exit slippage on a thin pair can be larger than a fixed flat spread estimate.

## 3. Data we may use from Binance.US

No live data request was sent to Binance.US this round. Every figure below is MEASURED from Binance.US documentation pages or `docs/research/194_data_source_terms_audit.md` and ledgers 230 to 233.

Terms and access status:

- [Binance.US API Documentation](https://docs.binance.us/) marks public endpoints with no listed security type (`NONE`, including GET /api/v3/klines and GET /api/v3/aggTrades) as freely accessible without an API key, with no general legal terms on that page (MEASURED from docs).
- [Binance.US Historical Market Data](https://www.binance.us/institutions/market-history) provides daily and monthly ZIP archives on `data.binance.us` for klines, trades, and aggTrades across all pairs, bars commercial uses without written consent (trading services using its quotes, data feeds, or monetized apps), and subjects all use to Binance.US Terms of Use (MEASURED from docs). Because full Terms of Use are unreadable, the file archive's full legal terms are marked UNKNOWN for now and must be checked by a helper before any archive pull.
- Full [Binance.US Terms of Use](https://www.binance.us/terms-of-use) remain UNKNOWN because only the intro loads (`docs/research/194_data_source_terms_audit.md`); ledgers 230 to 232 carry an explicit condition on those unread terms.

Documented endpoints, weights, and limits ([Binance.US API Documentation](https://docs.binance.us/), MEASURED from docs):

- GET /api/v3/klines: weight 1, maximum 1,000 bars per request, supported intervals include 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M; optional `startTime` and `endTime` in milliseconds.
- GET /api/v3/aggTrades: weight 4, maximum 1,000 aggregate trades per request; `startTime` and `endTime` can be used individually (the old 1-hour window cap was removed).
- IP rate limits: `REQUEST_WEIGHT` 6,000 per minute and `RAW_REQUESTS` 61,000 per 5 minutes, shared across REST and WebSocket. In our setup, any custodian pull must share the single stored cool-down gate with the four live loops (ledgers 230 to 233).

Do one-minute bars go back far enough on thin USD pairs?

- No for a continuous multi-year sample. Per [Binance.US Crypto-Only State Guide](https://support.binance.us/en/articles/9843321-a-complete-guide-to-using-binance-us-in-a-crypto-only-state), most USD Advanced Trading pairs were removed on June 26, 2023, and USD services only returned in February 2025 (available in most supported states as of February 19, 2025). Per [Binance.US Expands to 50+ USD Trading Pairs](https://support.binance.us/en/articles/10595018-binance-us-expands-to-50-usd-trading-pairs), Binance.US reached 50+ USD pairs on March 12, 2025 (MEASURED from support docs).
- That leaves a roughly 20-month hole (June 2023 to February 2025) on thin USD pairs, and only about 20 months of continuous recent history (March 2025 to November 2026). The exact earliest 1-minute retention date on REST or in `data.binance.us` ZIPs per thin pair is UNKNOWN without querying the venue, and [Binance.US Historical Market Data](https://www.binance.us/institutions/market-history) does not list whether 1m ZIPs exist for every pair.
- By contrast, Binance.US USDT pairs stayed open continuously through the 2023 to 2025 crypto-only period, and [Binance.US Fees](https://www.binance.us/fees) charges the exact same Tier I fee schedule on all non-BNB/USD pairs: 0% maker and 0.02% (2 bp) taker without BNB (STATED).

What a custodian would need to pull and rough request counts:

- Recommended roster: 20 thin, non-stablecoin Binance.US USDT pairs excluding all 11 Plan 76 coins, selected strictly point-in-time on January 1, 2022 to June 30, 2022 volume without any survival filter (including coins later delisted). Using USDT avoids the 20-month USD outage while staying on Binance.US, though volumes still dropped sharply during the June 2023 to early 2025 banking cutoff.
- Hourly bars (1h) for 20 USDT pairs across 4.9 years (January 1, 2022 to November 26, 2026, about 42,960 hours per pair): 43 requests per pair x 20 pairs = 860 requests, total weight 860. At a polite 1 request per second, this finishes in under 15 minutes and uses 1% of the 6,000/minute IP budget.
- Hourly bars (1h) for 20 USD pairs across the 21 post-restoration months (March 15, 2025 to November 26, 2026, about 14,900 hours per pair): 15 requests per pair x 20 = 300 requests, total weight 300.
- Full-span 1-minute bars (1m) over REST are heavy: 525,600 minutes per year = 526 requests per pair per year. Pulling 4.9 years of 1m bars for 20 USDT pairs takes about 51,560 requests (weight 51,560, or about 8.6 hours at 100 requests per minute). Pulling 21 months of 1m bars for 20 USD pairs takes about 17,880 requests (weight 17,880).
- Practical shortcut: pull 1h bars for the full span first (860 requests), run the price-blind count stage, and pull 1m bars only around signal windows (for example 26 hours = 1,560 minutes = 2 requests per signal; 400 signals = 800 requests, weight 800). Pull `aggTrades` (weight 4) only if a forward card or targeted fill check needs trade-level prints (1 to 5 requests per signal hour = weight 4 to 20 per signal).

## 4. Two draft plans (not registered, not to be run as written)

Both drafts below are kept for the record only. Neither plan is registered, neither may be run as written, and any pass in a future revised form could earn only a forward practice card on live Binance.US books, never live money.

Shared draft span structure:

- Universe selection window (no returns read): January 1, 2022 to June 30, 2022, targeting 20 thin non-stablecoin Binance.US USDT pairs outside Plan 76's 11 symbols (AAVE, ADA, BCH, BTC, ETH, HBAR, LINK, LTC, SHIB, XLM, XRP), at a fixed $250 non-compounded ticket.
- Design span: July 1, 2022 to June 30, 2024 (24 months).
- Held-back span: July 1, 2024 to November 26, 2026 (about 29 months, spanning 2024 H2, 2025, and 2026).

### Plan A (draft, not registered, not to be run as written): Resting-Bid Catch on Thin Binance.US Pairs

- Draft signal: at the close of every UTC hour `t`, for each of the 20 frozen pairs whose closed hour `t` had quote volume at least $2,500, place a resting post-only buy limit at `bid = close_t * (1 - 0.05)` valid for hour `t + 1` only. (Draft tie-break was largest close-to-close fall in hour `t + 1`, rejected as look-ahead.)
- Draft fill rule: hour `t + 1` counts as a fill if `open_{t+1} > bid`, `low_{t+1} < bid` strictly, and hour `t + 1` quote volume is at least $2,500, filled at `bid`.
- Draft exit: 24 hours after hour `t + 1` closes, exited as a taker.
- Draft cost line: 0 bp maker entry fee (STATED) + 2 bp taker exit fee (STATED) + 30 bp provisional exit half-spread and walk cost + 25 bp candle-fill adverse-selection haircut = 57 bp round-trip (20 bp and 100 bp shown only), with an unpinned M133/E14 upward-only cost gate.
- Draft count floor and marks: 80 fills per span, 33% synthetic power floor at +1.5% net, design positive overall and without each year's best trade, and five held-back marks (at least 80 fills, net mean > 0%, net mean > 0% without each calendar year's single best trade, one-sided day-clustered t >= 2.0 and above 95% of 1,000 random books, and at least 2 of 3 held-back calendar years positive).

Changes required before Plan A could be registered:

- Replace the look-ahead tie-breaker with a strictly causal rule executable at an hourly wake (for example, pre-select at most one eligible coin before hour `t + 1` opens using only `t` data, or split the $250 budget equally across all resting bids that fill in hour `t + 1`).
- Remove survivorship bias: construct the 2022 H1 Binance.US USDT universe point-in-time from historical archives (once archive terms are cleared) including all coins later delisted, and pre-register a harsh delisting-exit price rule for any open position caught by a delisting.
- Replace candle-bar fill checks with trade-through volume strictly at or below `bid` of at least $2,500 from `aggTrades` (not total bar volume), or skip a historical candle replay altogether and run a forward-only resting-bid paper test on live Binance.US books after E12's resting-bid line, M133, and E14 report.
- Align the count floor with the 33% power bar: raise the held-back count floor from 80 fills to the exact count needed for at least 33% synthetic power across all five simultaneous day-clustered marks at +1.5% net (roughly 140 to 160+ fills at 10% SD).
- Pin the cost-gate formula to one exact scalar before any design or held-back return is read (for example `exit_walk_bp = max(30, E14_20_signal_median_walk_bp)`), and bar running the design span before Measurement 133 and E14 cost outputs are published.
- Label any 2024 to 2026 held-back test explicitly as same-family and same-regime as Plan 76 (not an independent confirmation), and account for the June 2023 to early 2025 Binance.US disruption.

### Plan B (draft, not registered, not to be run as written): Post-Washout Taker Rebound on Non-Plan-76 Thin Binance.US Pairs

- Draft signal: at the close of every UTC hour `t`, any of the 20 frozen pairs whose close-to-close return from hour `t - 1` to hour `t` is -5.0% or worse, with hour `t` quote volume at least $2,500; largest faller if multiple trigger; one $250 position at a time, no overlap.
- Draft fill and exit: taker entry at the open of the 1-minute bar starting 1 minute after hour `t` closes; taker exit 24 hours later (`t + 24h + 1m`).
- Draft cost line: 2 bp/side taker fee (STATED) + 35 bp/side provisional half-spread and walk cost = 74 bp round-trip (30 bp and 150 bp shown only), with the same draft count floor (80 trades) and five held-back marks as Plan A.

Changes required before Plan B could be registered:

- Plan B is set aside now because it duplicates live practice card E14 (ledger 233) on less realistic candle data over an overlapping 2024 to 2026 span.
- Before any future taker replay could be registered, it would need to wait for E14's result, remove survivorship bias via a point-in-time 2022 H1 roster with delistings included, raise the held-back count floor to roughly 140 to 160+ trades to meet 33% all-marks power at +1.5% net, pin one exact cost-gate scalar before any design read, and be labeled same-family with Plan 76 and E14.

Expected power (STATED rough math; true dispersion on these pairs is UNKNOWN until measured):

- Assuming per-trade return standard deviation of 10% and 80 to 150 non-overlapping held-back trades, the standard error of the mean is 1.12% (at 80 trades) to 0.82% (at 150 trades).
- At a +1.5% true net edge per trade, 80 trades gives expected t = 1.34 (roughly 26% power on t >= 2.0 alone, and under 20% once day-clustering and all five marks are enforced), failing the 33% floor. Clearing 33% power across all five simultaneous day-clustered marks at +1.5% net requires roughly 140 to 160+ fills. At +2.5% net, 150 trades reaches roughly 85% power; at +0.5% net, power is under 10%.

## Two-step watch (replaces run-first advice)

- Step 0 (send nothing): Wait for Measurement 133's single read (after 2026-12-26) and E14's cost-only reading after 20 signals. Stop the entire thin-pair washout line if E14's walked entry cost is 80 bp a side or more, or if Measurement 133's calm $250 cost is above 25 bp on most coins.
- Step 1 (only if Step 0 survives, and only after a helper has read the terms of Binance.US's file archive, whose terms are marked UNKNOWN for now): Build the 2022 first-half Binance.US USDT pair list without any survivor filter, count delistings and dead pairs, and count non-overlapping fills against the roughly 140 to 160 needed for 33% power on all marks, with no return read.

## 5. What would make this whole line a dead end

Stop the entire thin-coin washout line early if any of three readings arrive: E14's 20-signal cost-only readout shows median walked entry cost after a 5% fall on Binance.US is 80 bp a side or higher (leaving almost no margin against Plan 76's 92.9 bp gross break-even even if 2024's bounce returned); Measurement 133 shows median $250 walk cost on Binance.US exceeds 25 bp on most coins even in calm hours, confirming the venue's books are too thin for $250 tickets; or a future survivorship-free count and resting-bid test comes back short of the 140 to 160 fill power floor, negative in both 2025 and 2026 (repeating Plan 76's -0.44% in 2025 and -0.91% in 2026), or fails without each year's best trade. If neither post-drop taker entries nor zero-fee resting bids survive after 2024 on thin pairs, the 2024 gain in Plan 76 was a one-year regime burst rather than a durable liquidity-provision edge worth further testing.
