# 201. Round 71: Washout Reversal Follow-Up on Thin Pairs and Resting Bids

This note builds on our newest held-back result, Plan 76 (`docs/research/200_plan_76_heldback_result.md`, ledger 229), and live practice card E14 (ledger 233). It does not rescore or re-cut Plan 76's held-back trades, makes no claim that any washout rule works, and makes zero requests to Binance.US.

Labels used throughout:

- MEASURED: observed directly in our own repo runs or read directly from a primary paper or venue documentation page opened for this note.
- STATED: a venue fee, policy, or author claim taken as reported without independent execution proof.
- UNKNOWN: not reported in the opened sources or not measurable without a live book or custodian pull.

Summary of the starting point from `docs/research/200_plan_76_heldback_result.md` (MEASURED): buying the largest one-hour faller of 5% or more among 11 coins on Bitstamp USD hourly bars and holding 24 hours earned +1.88% per trade before costs across 83 held-back trades (2024 to 2026). It failed 3 of 4 marks at 75 bp a side (+0.36% mean, -0.28% without each year's best trade) and met all 4 marks at 15 bp a side (+1.57% mean, +0.93% without each year's best trade). The blind recompute showed the gain sat in 2024 (+3.71% over 42 trades, vs -0.44% over 25 trades in 2025 and -0.91% over 16 trades in 2026) and in the four thinnest pairs (AAVE, SHIB, HBAR, LINK: 54 of 83 signals, +2.90% at 15 bp; the other 29 trades lost 0.89%).

## 1. Outside evidence from primary papers

Short-term reversal in crypto is heavily concentrated in small, low-volume, illiquid coins, while the largest liquid coins show momentum or near-zero net reversal. Across primary papers that apply realistic trading costs on single venues, net returns shrink sharply or turn negative, and recent 2025 to 2026 data show measurable decay even before depth and adverse selection are priced.

Illiquidity concentration and survival after spreads:

- Bianchi, Babiak, and Dickerson (2022), [Trading Volume and Liquidity Provision in Cryptocurrency Markets](https://www.riksbank.se/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf) (MEASURED from paper, 300+ USD pairs across 80+ exchanges via CryptoCompare, March 1, 2017 to March 1, 2022, daily rebalance within the top 100 pairs by prior-month Amihud ratio): conditional on low de-trended volume, daily reversal earned +1.226% per day gross equal-weighted (Sharpe 0.299) and +0.625% value-weighted, versus +0.543% equal-weighted and -0.187% value-weighted in high-volume coins. Cost assumption: Table 5 applies a flat 20 bp long and 30 bp short per daily rebalance (50 bp round-trip; Section 2.2 prose states 30 bp long and 40 bp short). After Table 5 costs, only equal-weighted low-volume reversal stayed positive and significant (+0.726% per day, p < 0.01); value-weighted mid- and high-volume portfolios turned significantly negative (-0.570% and -0.687% per day). On a single liquid venue (Binance USDT, Table 7, October 1, 2018 to March 1, 2022), low-volume reversal fell to +0.187% per day gross equal-weighted (+0.059% value-weighted) and turned negative after fees at -0.213% equal-weighted and -0.341% value-weighted. Average spread proxies in the low-return, low-volume bucket were 9.87% (Abdi-Ranaldo) and 4.59% (Corwin-Schultz).
- Zaremba, Bilgin, Long, Mercik, and Szczygielski (2021), [Up or Down? Short-Term Reversal, Momentum, and Liquidity Effects in Cryptocurrency Markets](https://www.wir.ue.wroc.pl/docstore/download/UEWR135bdc5e34ad49868fe8a5e77fa021c7/Mercik_Up_or_down_Short-term_reversal.pdf) (MEASURED from paper, 3,607 coins averaging 1,126 per day, January 1, 2015 to March 1, 2021): daily loser-minus-winner reversal was +13.19% equal-weighted (+3.84% value-weighted) in the smallest 98% of coins and +7.12% equal-weighted (+1.75% value-weighted) in the 98% most illiquid coins by Amihud ratio. The top 2% largest and most liquid coins (about 23 coins, 94%+ of market cap) showed daily momentum instead (+0.22% to +0.31% winner-minus-loser; note the paper's tables label mean daily excess return while one prose line says per month). Cost assumption: no numerical net-of-cost backtest was run; the authors note Roll-estimated spreads reach several percent in small and mid-cap coins and conclude that reversal is hard to implement in practice.

Bid-ask bounce and stale prices:

- Zaremba et al. (2021) attribute illiquid-coin reversal to both bid-ask bounce and temporary liquidity shocks, without separating their shares numerically (STATED).
- [Short-Horizon Mean Reversion in Cryptocurrency Markets](https://arxiv.org/html/2608.21888v1) (MEASURED from paper, 183 highest-volume Binance USDT spot pairs vs 187 US stocks and ETFs on 15-minute bars, primary sample January 1, 2025 to February 11, 2026, holdout February 12, 2026 to August 8, 2026, plus 2021 to 2026 on BTC, ETH, SOL, XRP): directly tests bounce and staleness. Using quote-midprice bars (Dukascopy bid/ask averages, where bid-ask bounce cannot occur) leaves the signal unchanged (BTC AUC 0.529, ETH AUC 0.537). Adding a one-bar gap between features and labels retains 71% of the excess AUC over stocks (crypto AUC drops from 0.531 to 0.522, 81% of pairs still significant); dropping flat bars moves AUC from 0.531 to 0.520; both controls together still leave a +0.011 AUC gap over stocks (0.5093 vs 0.4980). Across the 183-pair volume cross-section, AUC is flat across volume quintiles (0.518 to 0.524). Even so, the gross edge peaks at just 1.3 bp per trade (0.46 bp median pair at threshold 0.02; 0.15 bp on 5-minute bars). Cost assumption: 5 bp round-trip maker band and 10 to 20 bp round-trip taker band (explicit spot fees only, excluding depth, latency, and adverse selection). Zero of 183 pairs clear even the 5 bp maker band at any threshold.

What the papers say about the years after 2022:

- In [arXiv:2608.21888v1](https://arxiv.org/html/2608.21888v1), 15-minute directional reversal remains statistically present in all 24 of 24 focal coin-years from 2021 through partial 2026 (AUC 0.523 to 0.550), but attenuates in the 2026 holdout: mean crypto AUC falls from 0.531 (2025-01 to 2026-02) to 0.522 (2026-02 to 2026-08), the FDR-significant share falls from 90% to 60%, and 77% of that drop is genuine decay on a fixed universe rather than pair turnover.
- Ballis and Ioannidis (2026), [Market Efficiency in a Changing Asset Population](https://arxiv.org/html/2610.23283v2) (MEASURED from paper, 8,970 coins, April 2013 to July 2026): does not test short-term reversal, but tracks the broader illiquid-coin premium through the consolidation era (July 2021 to July 2026). Under a 2% one-way cost assumption, the bottom-decile weekly net return is +1.28%/week at a $10,000 daily volume floor, drops to -0.08%/week at a $100,000 volume floor (+0.38%/week at 1% one-way cost), and falls to -3.69%/week at a $1,000,000 volume floor.
- Whether a 1-hour-drop, 24-hour-hold washout reversal on thin US-reachable pairs survived costs after 2024 is UNKNOWN in the primary literature; our own Plan 76 held-back sample lost money in both 2025 (-0.44%) and 2026 (-0.91%) even at 15 bp a side (MEASURED).

## 2. The resting-bid version, adverse selection, and candle fill rules

Replacing a post-washout market order with a resting bid below the last hourly close removes the entry taker fee and avoids crossing the entry spread, but it replaces spread cost with adverse selection: resting bids fill with near-certainty when price keeps falling and miss the fast bounces.

Primary evidence on limit-order fills and adverse selection:

- Albers, Cucuringu, Howison, and Shestopaloff (2025), [The Market Maker's Dilemma](https://arxiv.org/html/2502.18625) (MEASURED from live Binance BTC perpetual experiment, 232,897 continuous-quoting orders with 127,051 fills in February 2024, plus 172,800 periodic orders in August 2024): conditioned on the immediate midprice move, a resting maker order fills with probability 1 on an adverse move and 0 on a favorable move. Every single queue-position bucket had a negative 1-second markout (-0.058 bp to -1.157 bp before rebates), and the overall 5-second expected markout was -0.8 bp (-0.3 bp net of a 0.5 bp/side maker rebate). A naive market-making loop lost -0.43 bp per round trip even after 1 bp round-trip rebates (losing almost 60% of equity in 3 days and 7 hours, annualized Sharpe -109.0).
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
- [Binance.US Historical Market Data](https://www.binance.us/institutions/market-history) provides free daily and monthly ZIP archives on `data.binance.us` for klines, trades, and aggTrades across all pairs, bars commercial uses without written consent (trading services using its quotes, data feeds, or monetized apps), and subjects all use to Binance.US Terms of Use (MEASURED from docs).
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

- Recommended roster: 20 thin, non-stablecoin Binance.US USDT pairs excluding all 11 Plan 76 coins (chosen strictly by lowest median hourly quote volume during a pre-design selection window, January 1, 2022 to June 30, 2022, among pairs listed continuously since January 1, 2022). Using USDT avoids the 20-month USD outage while staying on Binance.US; a secondary 20-month check on the restored USD pairs (March 15, 2025 to November 26, 2026) can be pulled later only if needed.
- Hourly bars (1h) for 20 USDT pairs across 4.9 years (January 1, 2022 to November 26, 2026, about 42,960 hours per pair): 43 requests per pair x 20 pairs = 860 requests, total weight 860. At a polite 1 request per second, this finishes in under 15 minutes and uses 1% of the 6,000/minute IP budget.
- Hourly bars (1h) for 20 USD pairs across the 21 post-restoration months (March 15, 2025 to November 26, 2026, about 14,900 hours per pair): 15 requests per pair x 20 = 300 requests, total weight 300.
- Full-span 1-minute bars (1m) over REST are heavy: 525,600 minutes per year = 526 requests per pair per year. Pulling 4.9 years of 1m bars for 20 USDT pairs takes about 51,560 requests (weight 51,560, or about 8.6 hours at 100 requests per minute). Pulling 21 months of 1m bars for 20 USD pairs takes about 17,880 requests (weight 17,880).
- Practical shortcut: pull 1h bars for the full span first (860 requests), run the price-blind count stage, and pull 1m bars only around signal windows (for example 26 hours = 1,560 minutes = 2 requests per signal; 400 signals = 800 requests, weight 800). Pull `aggTrades` (weight 4) only if a forward card or targeted fill check needs trade-level prints (1 to 5 requests per signal hour = weight 4 to 20 per signal).

## 4. Two candidate plans ready to register

Both plans run on Binance.US USDT pairs that Plan 76 never touched, excluding all 11 Plan 76 symbols (AAVE, ADA, BCH, BTC, ETH, HBAR, LINK, LTC, SHIB, XLM, XRP), at a fixed $250 non-compounded ticket. Neither plan can authorize live money; a pass earns only a forward practice card on live Binance.US books.

Shared roster and span structure (fixed before any return is read):

- Universe selection window (no returns read): January 1, 2022 to June 30, 2022. Among non-stablecoin, non-leveraged Binance.US USDT pairs outside Plan 76's 11 coins that traded continuously over that window with median hourly quote volume between $2,500 and $100,000, take the 20 pairs with the lowest median hourly quote volume (exact list frozen by hash in the count stage).
- Design span (go-on check only): July 1, 2022 to June 30, 2024 (24 months).
- Held-back span (judged once, opened only if design passes and cost gate clears): July 1, 2024 to November 26, 2026 (about 29 months, spanning 2024 H2, 2025, and 2026).

How both plans stay honest before Measurement 133 and E14 finish:

- Both plans fix a conservative provisional judged cost line now, before any bar is read, and include a one-way cost-update gate: once Measurement 133 (finishes December 26, 2026) and E14's 20-signal cost-only readout are published, if the measured median $250 walked cost on thin Binance.US pairs exceeds the provisional spread assumption, the higher measured cost replaces the provisional line before the held-back span is opened. The cost line is never lowered automatically without a separate pre-registered amendment, and never changed after held-back returns are read.

### Plan A: Resting-Bid Catch on Thin Binance.US Pairs (Maker Entry, Taker Exit)

- Exact signal: at the close of every UTC hour `t`, for each of the 20 frozen pairs whose closed hour `t` had quote volume at least $2,500, place a resting post-only buy limit at `bid = close_t * (1 - 0.05)` (5.0% below the last hourly close) valid for hour `t + 1` only. If no position is open and multiple pairs trigger fills in the same hour `t + 1`, take the pair with the largest hourly close-to-close fall in hour `t + 1` as the single $250 position (one position at a time, no overlapping holds; tie-break by alphabetical symbol).
- Exact fill rule: conservative candle rule from Section 2. Hour `t + 1` counts as a fill only if `open_{t+1} > bid`, `low_{t+1} < bid` strictly, and hour `t + 1` quote volume is at least $2,500. Entry price is `bid`.
- Exit: 24 hours after hour `t + 1` closes (open of hour `t + 26`, checked on 1m open of minute `t + 26:01` for signal windows), exited as a taker.
- Cost line: 0 bp maker entry fee (STATED) + 2 bp taker exit fee (STATED) + 30 bp provisional exit half-spread and walk cost + 25 bp candle-fill adverse-selection haircut = 57 bp round-trip judged (20 bp and 100 bp round-trip shown only), subject to the upward-only M133/E14 cost-update gate.
- Count stage (before any return): pull 1h bars only, freeze the 20-pair roster on 2022 H1 volume, and count non-overlapping candidate fills in design and held-back. Floor: at least 80 fills in design and 80 in held-back, plus a doc 117 synthetic power check showing at least 33% chance to clear all held-back marks at a +1.5% net edge per trade using a realistic per-trade dispersion (10% SD if external, never read from held-back returns). Below either floor, close on count.
- Design go-on check (2022-07-01 to 2024-06-30): net mean above 0% and positive without each calendar year's best trade at the judged cost.
- Held-back pass marks (2024-07-01 to 2026-11-26, all five required): (1) at least 80 valid non-overlapping fills, (2) mean net return strictly above 0% at judged cost, (3) mean net return strictly above 0% with each calendar year's single best trade removed, (4) one-sided day-clustered (UTC entry day) t >= 2.0 and above 95% of 1,000 same-coin, same-hour-of-week random books, and (5) positive net mean in at least 2 of the 3 held-back calendar years (2024 H2, 2025, 2026).

### Plan B: Post-Washout Taker Rebound on Non-Plan-76 Thin Binance.US Pairs (Taker Entry, Taker Exit)

- Exact signal: at the close of every UTC hour `t`, any of the 20 frozen pairs whose close-to-close return from hour `t - 1` to hour `t` is -5.0% or worse, with hour `t` quote volume at least $2,500. If multiple pairs trigger, select the largest faller; one $250 position at a time, no overlap.
- Exact fill rule: taker entry at the open of the 1-minute bar starting 1 minute after hour `t` closes (matching Plan 72 and Plan 73's reachable-clock rule; hourly open shown only). Missing 1m bar voids the ticket (counted, never filled in).
- Exit: taker exit at the open of the 1-minute bar 24 hours later (`t + 24h + 1m`).
- Cost line: 2 bp/side taker fee (STATED) + 35 bp/side provisional half-spread and walk cost = 74 bp round-trip (37 bp/side) judged (30 bp and 150 bp round-trip shown only), subject to the upward-only M133/E14 cost-update gate.
- Count stage, design go-on check, and held-back pass marks: identical to Plan A (at least 80 non-overlapping trades per span, 33% synthetic power floor at +1.5% net, design positive overall and without each year's best trade, and all five held-back marks including 2 of 3 calendar years positive).

Expected power for both plans (STATED rough math; true dispersion on these 20 pairs is UNKNOWN until measured):

- Assuming per-trade return standard deviation of 10% (typical of 24-hour thin-coin post-drop holds) and 80 to 150 non-overlapping held-back trades, the standard error of the mean is 1.12% (at 80 trades) to 0.82% (at 150 trades).
- At a +1.5% true net edge per trade, expected t is 1.34 (80 trades, roughly 26% power for t >= 2.0 alone) to 1.84 (150 trades, roughly 44% power). At a +2.5% true net edge, expected t is 2.24 (roughly 60% power) to 3.06 (roughly 85% power). At a +0.5% net edge, power is under 10%. Thus, if the count stage yields near 80 trades, only a large net edge (+2% or more per trade) is reliably detectable.

Which plan to run first, why, and what result kills it:

- Run Plan A first, and wait until Measurement 133 (December 26, 2026) and E14's 20-signal cost-only readout are in before opening any held-back returns.
- Reason: E14 is already testing the live-book taker washout rule, so running Plan B first duplicates E14 on less realistic candle data. Plan A tests the one structural edge a 24/7 agent has on Binance.US (0% maker fees on resting bids across 20 thin pairs simultaneously). If Plan A fails even on candles at 0% maker entry, a taker rule paying entry walk plus fees has even less room to survive.
- Kill condition for Plan A: fewer than 80 fills or under 33% synthetic power at +1.5% net in the count stage; failure on either design mark; failure on any of the five held-back marks (especially negative net mean in both 2025 and 2026, or negative mean without each year's best trade); or, if it advances to a forward card, live 5-minute markouts and missed-fill shortfalls erasing the candle edge.

## 5. What would make this whole line a dead end

Stop the entire thin-coin washout line early if any of three readings arrive: E14's 20-signal cost-only readout shows median walked entry cost after a 5% fall on Binance.US is 80 bp a side or higher (leaving almost no margin against Plan 76's 92.9 bp gross break-even even if 2024's bounce returned); Measurement 133 shows median $250 walk cost on Binance.US exceeds 25 bp on most coins even in calm hours, confirming the venue's books are too thin for $250 tickets; or Plan A's resting-bid test comes back negative in both 2025 and 2026 (repeating Plan 76's -0.44% in 2025 and -0.91% in 2026) or fails without each year's best trade. If neither post-drop taker entries nor zero-fee resting bids survive after 2024 on thin pairs, the 2024 gain in Plan 76 was a one-year regime burst rather than a durable liquidity-provision edge worth further testing.
