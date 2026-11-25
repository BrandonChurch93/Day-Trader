# Practice environments and honest cost modelling

> Checked 2026-11-25 by fresh checkers on different models. Their tables are in `check/`. Lines changed after the check are marked "Corrected 2026-11-25". The corrected summary is the numbered file one folder up.
> Check notes: Alpaca's paper page does not say whether crypto fees are charged on practice fills. Add the fee ourselves. The IBIT figure of 2.27 bps is driven by 106 orders of $200,000 and more. For small orders the October 2026 figure is 0.69 to 1.43 bps.


Report date: 2026-11-24 (America/Boise). Sandbox clock read 2026-11-25 06:2x UTC during the live measurements, which is the evening of 2026-11-24 in Idaho.
Tags: MEASURED = read on a primary page or measured from a public endpoint today. STATED = someone's claim, not confirmed on a primary page. UNKNOWN = not found (does not mean absent).

## Unfinished or not verified

- Alpaca Trading API rate limit (200 requests per minute per account, same for paper and live). I did not find this on an Alpaca primary page today. Only third-party pages: [aifinhub, 2026](https://aifinhub.io/articles/alpaca-api-rate-limits/) and [QuantVPS, 2026](https://www.quantvps.com/blog/alpaca-api-python-trading-bot). STATED.
- Whether Alpaca paper charges the crypto maker/taker fee on simulated fills. UNKNOWN. The paper page lists "regulatory fees" as not simulated but says nothing about crypto fees.
- Whether Alpaca paper simulates the overnight (BOATS) session the same way as live. UNKNOWN. The paper page only says pre-market and after-hours are available.
- Wholesaler-level Rule 605 reports (Citadel, Virtu, Jane Street, GTS). Not opened. I used Alpaca's own broker-level 605 report instead, which now covers Alpaca's routed orders. UNKNOWN for the wholesaler files.
- Gemini sandbox fill mechanics, rate limits, data. The page only says bots simulate the book. UNKNOWN beyond that.
- Webull test environment fill mechanics. UNKNOWN. Developer docs list sandbox hosts only.
- Tradier sandbox fill rules. UNKNOWN. FAQ covers delay and streaming only.
- Binance.US testnet. UNKNOWN (docs do not mention one).
- Crypto venue fee schedules other than Alpaca (Coinbase, Kraken, Gemini, Binance.US). Not checked in this report.
- Bogousslavsky and Muravyev closing-auction paper: journal name not confirmed on the page I opened. Illinois Experts lists it as peer-reviewed journal output.
- Effective-spread measurement for stop orders in Rule 605: the eCFR "average midpoint" definition says stop orders are measured from when they become executable, but the "average effective spread" definition says "time of order receipt" except for midpoint-or-better limit orders. I read the stop numbers as measured from trigger time. Not fully confirmed.
- Live crypto spreads below are a short snapshot on one evening (US night, low activity). They are not a time series.

## Part 1. Practice environments

### Alpaca paper trading (stocks and crypto)

Main source: [Alpaca Paper Trading doc, updatedAt 2026-07-07](https://docs.alpaca.markets/us/docs/paper-trading.md). All rows MEASURED from that page unless tagged.

| Topic | What Alpaca says | Tag and source |
|---|---|---|
| Fill price | "the system simulates the order filling based on the real-time quotes". "all orders submitted in paper trading will be matched against the best available current market price (NBBO)". | MEASURED, [paper doc](https://docs.alpaca.markets/us/docs/paper-trading.md) |
| Fill price detail | Staff: "Buy orders look at the ask price and sell orders use the bid price." "SIP quotes are used to determine fills." Fills "are based upon full market SIP data and independent of which market data plan you are subscribed to". "The latest trade is not relevant." | STATED (staff, Dan Whitnable, 2025-12-09), [forum 18223](https://forum.alpaca.markets/t/18223) |
| Limit orders | Fill only when marketable: a buy limit fills when limit is at or above the best ask; a sell limit when at or below the best bid. So a resting limit never gets filled "at the bid" by a seller hitting it. | MEASURED, paper doc |
| Size vs liquidity | "Your order quantity is not checked against the NBBO quantities." You can get filled far beyond displayed size. | MEASURED, paper doc |
| Partial fills | "they will receive partial fills for a random size 10% of the time". Staff: this is "much larger than one would see in live trading", on purpose. | MEASURED, paper doc; STATED staff, [forum 18681, 2026-04-10](https://forum.alpaca.markets/t/18681) |
| Not simulated | "Market impact", "Information leakage", "Price slippage due to latency", "Order queue position (for non-marketable limit orders)", "Price improvement received", "Regulatory fees", "Dividends". | MEASURED, paper doc |
| Borrow fees | Paper: "⛔️ (Coming Soon!)". Live: yes. | MEASURED, paper doc |
| Locates | Locate endpoints: "This endpoint is not available in paper trading." | MEASURED, [Alpaca docs index](https://docs.alpaca.markets/us/llms.txt) |
| Corporate actions | Staff: "Paper trading currently does not support corporate actions such as stock splits." Users report reverse splits creating fake P/L (QBTX +$4,205). | STATED staff, [forum 18569, 2026-03-14](https://forum.alpaca.markets/t/18569), [forum 19738, 2026-09-23](https://forum.alpaca.markets/t/19738) |
| Auction orders (MOO, MOC) | Staff: paper "treats those orders as regular market orders", filled at bid/ask, not at the auction price; and auction orders "generally always (though not 100%) fill complete" in live but get random partials in paper. Roadmap item, posts from 2021. | STATED staff, [forum 3762, 2021-05-18 and 2021-10-18](https://forum.alpaca.markets/t/3762). Current status UNKNOWN. |
| Latency | Staff: paper median fill about 5 seconds with a long tail, 102 seconds at the 80th percentile. Live median 14 ms, 465 ms at the 99th percentile. Paper slows at the open because of order volume. | STATED staff, [forum 19416, 2026-08-05](https://forum.alpaca.markets/t/19416); [forum 18681, 2026-11-18](https://forum.alpaca.markets/t/18681) |
| User reports of slow opens | Marketable orders getting zero fills for 10 to 45 seconds in the first minutes after the open. | STATED (user), forum 18681, 2026-11-18 |
| Extended hours and overnight | Paper supports pre-market and after-hours. Live supports overnight 8:00pm to 4:00am ET on Blue Ocean ATS (BOATS), limit orders only, `day` orders carry into the next day. Paper support for overnight: UNKNOWN. | MEASURED, paper doc; [24/5 FAQ, updatedAt 2026-07-07](https://docs.alpaca.markets/us/docs/245-trading-for-trading-api.md) |
| Overnight dividends | "purchasing a stock during the overnight session on its ex-dividend date will not entitle you to that stock's dividend." | MEASURED, 24/5 FAQ |
| Market data on free plan | Basic plan is free and default for paper and live: real-time IEX only, 30 websocket symbols, historical API 200 calls per minute, SIP history only if older than 15 minutes. Algo Trader Plus is $99 per month for all US exchanges. "Paper Only Account" holders get IEX data only. | MEASURED, [About Market Data API, updatedAt 2026-10-06](https://docs.alpaca.markets/us/docs/about-market-data-api.md); paper doc |
| Mismatch | So the free plan shows you IEX quotes, but paper fills use SIP NBBO (staff). Your signal quote and your fill quote can differ. | Derived from the two rows above |
| Starting balance and resets | Default $100k. The dashboard now lets you "create and delete paper accounts, rather than resetting them." New API keys needed per account. | MEASURED, paper doc |
| Number of paper accounts | Staff: "Each owner is currently allowed 3 paper accounts and 1 live account." Data plan rate limits are per owner. Alpaca Learn also says up to 3. | STATED staff, [forum 18125, 2025-11-07 and 2026-11-18](https://forum.alpaca.markets/t/18125); [Alpaca Learn](https://alpaca.markets/learn/start-paper-trading) |
| Rate limits | 200 requests per minute per account, same for paper and live. | STATED, third-party only (see top) |
| Order types that behave differently | Stop orders become market orders when elected; stop-limit stays as limit after a gap. Bracket exits: "in extremely volatile and fast market conditions, both orders may fill". Extended hours: limit only, `day` or `gtc`. | MEASURED, [Placing Orders, updatedAt 2026-10-13](https://docs.alpaca.markets/us/docs/orders-at-alpaca.md) |
| Crypto in paper | "Paper trading simulates crypto trading as well." Crypto orders: market, limit, stop_limit; TIF gtc and ioc. No margin, no short. Max $200k notional per order. | MEASURED, paper doc; [Crypto Spot Trading, 2025-09-24](https://docs.alpaca.markets/us/docs/crypto-trading.md); [Crypto Orders](https://docs.alpaca.markets/us/docs/crypto-orders.md) |
| Crypto fees (live) | Tier 1 (0 to $100k 30-day volume): maker 15 bps, taker 25 bps. Fee charged in the asset you receive. "Fees are currently calculated and posted end of day." | MEASURED, Crypto Spot Trading page |
| Crypto paper incidents | Paper crypto buys stuck for about 10 days in Nov 2025, fixed. Users report crypto market orders 10 to 80 minutes slow on 2026-06-02. | STATED staff, [forum 18126](https://forum.alpaca.markets/t/18126); STATED user, [forum 18912](https://forum.alpaca.markets/t/18912) |
| Emails | Paper "does NOT send order fill emails". | MEASURED, paper doc |
| Alpaca's own warning | "it is not a substitute for real trading". "Even small amounts of real money can often provide insight into issues not seen in a simulation environment." Staff: paper's first use case is "to debug one's algo and not necessarily to test one's strategy". | MEASURED, paper doc; STATED staff, forum 3762 |

Plain reading: Alpaca paper fills a market order at the far side of the SIP NBBO, with no size check, random extra partials, no price improvement, no fees, no dividends, no splits. For a liquid ETF this is pessimistic on price (live usually gets price improvement, see Part 2) and optimistic on everything else (dividends missing, splits wrong, auctions wrong, size unlimited).

### Other practice environments (brief)

| Venue | How fills work | Main gaps | Tag and source |
|---|---|---|---|
| Gemini sandbox | Separate exchange copy. "Automated bots simulate order book activity and trading." Test funds ($100,000 USD, 1,000 BTC, 20,000 ETH and others). | Book is bots, not the real market, so prices and depth are not production. Only Testnet BTC deposits. Fill rules, rate limits: UNKNOWN. | MEASURED, [Gemini sandbox page](https://developer.gemini.com/get-started/sandbox) (no date) |
| Kraken CLI paper (spot) | Prices from public Kraken Ticker. Market buys at ask (times optional flat slippage), sells at bid. Default 0.26% taker fee on every fill. "no partial fills". A limit "always rests when placed, even when the market is already through its price" and later fills "at the limit price, not at the better market price". Default slippage 0.0. | No depth, no queue, no maker fee path, limit check only when you run a command. | MEASURED, [kraken-cli README](https://github.com/krakenfx/kraken-cli) |
| Kraken CLI paper (futures) | Bid/ask snapshot, "no depth-based slippage", post-only orders "cancelled rather than simulating maker queue priority". | Not relevant for spot plan. | MEASURED, same README |
| Coinbase Advanced Trade sandbox | "All responses are static and pre-defined." Only accounts and orders endpoints. | Not a simulator at all. Useful only for request format and error handling. | MEASURED, [Coinbase sandbox doc, modified 2026-11-13](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/sandbox) |
| Binance.US test order | `POST /api/v3/order/test` "creates and validates a new order but does not send it into the matching engine." Returns `{}`. | No fills at all. Checks signature and parameters only. Testnet: UNKNOWN. | MEASURED, [Binance.US API docs](https://docs.binance.us/) |
| Interactive Brokers paper | "Fills are simulated from the top of the book; no deep book access." "Stops and other complex order types are always simulated in paper trading". Simulator "will reject the remainder of any exchange-directed market order that partially executes." No Auction, Pegged to Market, VWAP order types. | IBKR Campus: "certain corporate actions like dividends and splits won't be processed." No IPOs, no mutual funds. Simulated fills do not show in Time and Sales. | MEASURED, [IBKR FAQ](https://www.interactivebrokers.com/support/faq/content/limitations-paper-trading-account-35807733) (no date); [IBKR Campus](https://ibkrcampus.com/campus/trading-lessons/paper-trading-vs-live-trading-whats-the-difference/) (comment dated 2026-06-02) |
| Webull | Sandbox hosts exist (api.sandbox.webull.com and others). Press release (2026-07-21): "OpenAPI access for paperTrade" and "A pricing engine designed to better reflect live market conditions". | Fill rules: UNKNOWN. | MEASURED hosts, [Webull SDK page](https://developer.webull.com/apis/docs/sdk/); STATED claims, [PR Newswire via Morningstar, 2026-07-21](https://www.morningstar.com/news/pr-newswire/20260721cn08479/webull-unveils-enhanced-paper-trading-experience-with-professional-grade-and-openapi-multi-asset-simulation) |
| Tradier sandbox | "We delay our market data by the industry standard 15 minutes for all sandbox data." "we do not offer a delayed streaming endpoint for paper trading." | 15-minute delay makes it useless for timing tests. Fill rules: UNKNOWN. | MEASURED, [Tradier FAQ](https://docs.tradier.com/brokerage-api/overview/faq) (no date) |
| tastytrade sandbox | Orders go to a market simulator. Fill at the quote mid rounded to tick (up for buy, down for sell). Size above min(bid size, ask size) steps one tick worse per step. "The environment resets every 24 hours". REST market data returns HTTP 502. Some tickers have scripted outcomes. Crypto "have not been tested". | Mid-based fills are optimistic for wide spreads. Daily wipe. | MEASURED, [tastytrade sandbox doc](https://developer.tastytrade.com/docs/sandbox) |

### What only real money can teach

Each item is something no environment above simulates faithfully, per the sources above.

- Actual price improvement from wholesalers (Alpaca paper: "Price improvement received" not simulated).
- Queue position and adverse selection of resting limit orders (Alpaca, IBKR, Kraken CLI all skip queue).
- Real fill latency (Alpaca staff: live median 14 ms vs paper about 5 s).
- Opening and closing auction fills (Alpaca paper fills MOO/MOC at bid/ask; IBKR paper has no Auction orders).
- Regulatory fees (FINRA TAF on sells, CAT on all equity trades, posted end of day, rounded up to the cent) from [Alpaca Regulatory Fees, 2025-10-03](https://docs.alpaca.markets/us/docs/regulatory-fees.md).
- Crypto fees as actually posted (end of day, in the received asset).
- Dividends, splits, other corporate actions (Alpaca and IBKR paper do not process them).
- Borrow fees and locates for shorts (not in Alpaca paper).
- Halts and LULD pauses as your broker handles them, and stop orders in fast markets.
- Overnight BOATS fills and the overnight ex-dividend trap.
- Account rules that depend on real cash: settlement, buying power after real fills, tax lots, wash sales (Alpaca staff notes wash rules apply across accounts by tax ID, [forum 18125](https://forum.alpaca.markets/t/18125)).

## Part 2. Honest cost modelling

### Liquid ETFs: Alpaca's own Rule 605 report

Alpaca now publishes a broker-level Rule 605 report under the amended rule. I downloaded the October 2026 file for Alpaca Securities (APCA), dated 2026-11-10 inside the zip, from the [Alpaca 605 page](https://alpaca.markets/disclosures/605-reports) ([direct zip](https://files.alpaca.markets/disclosures/library/SEC+Rule+605/APCA202610.zip)). MEASURED.

Definitions: Rule 605 "average effective spread" is "double the amount of difference between the execution price and the midpoint" of the NBBO ([17 CFR 242.600](https://www.ecfr.gov/current/title-17/chapter-II/part-242/subject-group-ECFR3dd95cf4d3f6730/section-242.600)). So one-way cost versus the mid is half the effective spread. Order type codes MXXNN = market, LYNNN = marketable limit, MXXNY = executable stop market, LYNNY = executable stop marketable limit ([Federal Register, 2025-09-15](https://www.federalregister.gov/d/2025-17714)). Covered orders are regular-hours only.

Alpaca summary table, S&P 500 stocks (flag Y), market orders, October 2026 ([APCA202610.pdf in the zip](https://files.alpaca.markets/disclosures/library/SEC+Rule+605/APCA202610.zip)):

| Order size | % shares price-improved | Avg % effective spread | Avg % quoted spread | Effective / quoted |
|---|---|---|---|---|
| Under $250 | 98.67% | 0.0210% | 0.0584% | 35.89% |
| $250 to $1K | 98.63% | 0.0253% | 0.0660% | 38.32% |
| $1K to $5K | 98.01% | 0.0280% | 0.0684% | 41.00% |
| $5K to $10K | 97.24% | 0.0274% | 0.0647% | 42.35% |
| $10K to $20K | 97.96% | 0.0312% | 0.0705% | 44.27% |
| $20K to $50K | 96.75% | 0.0310% | 0.0638% | 48.57% |

Note: ETFs are not S&P 500 members, so the summary table puts SPY and QQQ in the "N" group with small caps. I therefore computed ETF numbers from the per-symbol file inside the zip (APCA202610.txt), share-weighted across all size buckets. Output saved as working notes. MEASURED.

| Symbol | Type | Orders | Mid ($) | Quoted spread (bps) | Effective spread (bps) | Eff/quoted | % shares PI |
|---|---|---|---|---|---|---|---|
| SPY | market | 8,579 | 769.79 | 0.25 | 0.12 | 50% | 87.5% |
| SPY | stop market | 238 | 769.82 | 0.27 | 0.97 | 359% | 33.8% |
| QQQ | market | 11,934 | 731.61 | 0.32 | 0.17 | 51% | 86.2% |
| QQQ | stop market | 625 | 743.36 | 0.30 | 3.70 | 1235% | 16.0% |
| IWM | market | 2,077 | 277.33 | 0.52 | 0.28 | 54% | 82.5% |
| IWM | stop market | 58 | 275.50 | 0.38 | 0.82 | 214% | 3.8% |
| VTI | market | 1,733 | 378.31 | 0.61 | 0.29 | 47% | 87.2% |
| TLT | market | 9,008 | 80.18 | 1.25 | 0.51 | 41% | 96.9% |
| TLT | stop market | 15 | 78.20 | 1.28 | 1.90 | 149% | 8.5% |
| IEF | market | 1,376 | 90.04 | 1.11 | 0.44 | 40% | 99.2% |
| GLD | market | 5,786 | 377.25 | 0.66 | 0.34 | 52% | 86.8% |
| EFA | market | 545 | 103.31 | 0.97 | 0.39 | 41% | 96.6% |
| XLE | market | 4,365 | 66.92 | 1.49 | 0.46 | 31% | 98.9% |
| XLE | stop market | 61 | 67.54 | 1.52 | 2.52 | 166% | 10.8% |
| IBIT | market | 6,991 | 48.35 | 2.07 | 2.27 | 110% | 41.6% |
| FBTC | market | 899 | 71.88 | 1.57 | 0.80 | 51% | 98.4% |
| ETHA | market | 864 | 46.39 | 2.21 | 1.10 | 50% | 96.7% |
| AAPL (reference) | market | 14,118 | 341.02 | 1.53 | 0.88 | 58% | 94.6% |
| AAPL (reference) | stop market | 421 | 340.47 | 1.31 | 19.70 | 1509% | 17.1% |

What this says, in plain words:

- For regular-hours market orders in big ETFs, Alpaca's live fills land at about half the quoted spread from the mid. One-way cost versus mid is under 0.1 bps for SPY and QQQ and under 0.3 bps for TLT, IEF, GLD, XLE. MEASURED.
- Stop market orders cost many times more than plain market orders on the same symbol. SPY stops: 0.97 bps effective, about 8 times plain market. QQQ: 3.7 bps, about 22 times. AAPL: 19.7 bps. MEASURED. Stop counts are small, so treat these as rough.
- Spot bitcoin ETF IBIT had effective spread above quoted (110%), with only 41.6% of shares price-improved. MEASURED.
- None of this covers pre-market, after-hours, overnight, the open and close auctions, or gaps across the overnight. Rule 605 covered orders are regular-hours only (eCFR 242.600, "Covered order").

Routing and payment for order flow (Alpaca 606 report, Q3 2026, July section, S&P 500 stocks, [SEC 606a1 2026Q3 PDF](https://files.alpaca.markets/disclosures/library/SEC+606a1+-+2026Q3.pdf)), MEASURED:

| Wholesaler | % of non-directed orders | Net PFOF on market orders (cents per 100 shares) |
|---|---|---|
| Citadel Securities (CDRG) | 46.73% | 158.38 |
| Jane Street (JNST) | 20.91% | 133.32 |
| Virtu (NITE) | 18.62% | 168.82 |
| GTS Securities (GTSM) | 13.74% | 141.45 |

The same 606 report states marketable orders in the core session earn Alpaca "12% of the spread per share, capped at 5 cents per share", extended hours "9% of the spread", and auction fills "will not receive a rebate nor incur a charge". MEASURED.

Peer-reviewed check on PFOF routes: [Schwarz, Barber, Huang, Jorion, Odean, Journal of Finance 80(5), 2025](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1111/jofi.13467) placed 85,000 simultaneous market orders across six accounts at five brokers. "the mean account-level round-trip cost ranges from 0.07% to 0.46%, excluding any commissions." Wholesalers gave "systematically different execution prices for the same trades to different brokers". Average price improvement was 31% of the NBBO spread. Their sample is not only big ETFs, so their costs are higher than SPY numbers above. MEASURED (abstract and tables via the open-access page). Alpaca was not in their sample.

### Stops, auctions, gaps, halts, short sale limits

| Topic | Evidence | Tag and source |
|---|---|---|
| Stop slippage | Alpaca 605 stop rows above. Peer-reviewed: stop-loss orders "contribute to rapid, self-reinforcing price movements" (price cascades) in FX. | MEASURED; [Osler, J. Int. Money and Finance 24(2), 2005, NY Fed staff report version](https://www.newyorkfed.org/research/staff_reports/sr150.html) |
| Stop elected becomes market | Alpaca: "Once the order is elected, the stop order becomes a market order." Stop-limit after a gap "will remain active as a limit order". | MEASURED, [Placing Orders](https://docs.alpaca.markets/us/docs/orders-at-alpaca.md) |
| Closing auction | Closing auctions were 7.5% of daily volume in 2018. "closing prices typically match pre-close bid or ask prices, and price impact is lower than during continuous trading." Deviations "revert quickly and almost completely on average." | MEASURED abstract, [Bogousslavsky and Muravyev, SSRN 3485840](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840); journal UNKNOWN |
| Alpaca auction orders | MOO/LOO only in opening auction, MOC/LOC only in closing auction. Paper does not simulate auction prices (staff, 2021). | MEASURED, Placing Orders; STATED, forum 3762 |
| LULD | Bands "set at a percentage level above and below the average reference price of a security over the preceding five-minute period". Tier 1 above $3: 5%. "Price Bands are doubled during last 25 minutes". Limit state over 15 seconds leads to "a five-minute Trading Pause". Applies 9:30 to 4:00 ET. | MEASURED, [LULD Plan site](https://www.luldplan.com/) (plan permanent since 2019-04-11) |
| Short sale restriction | Rule 201 applies "only when a stock has triggered a circuit breaker by experiencing a price decline of at least 10 percent in one day" and then "for the remainder of the day as well as the following day." | MEASURED, [SEC press release 2010-26](https://www.sec.gov/news/press/2010/2010-26.htm) |
| Overnight halts | Alpaca: an asset halted overnight "typically persists for the entire session"; orders sit in `accepted`. | MEASURED, 24/5 FAQ |

### BTC and ETH

Peer-reviewed:

- [Dyhrberg, Foley, Svec, Economics Letters 171, 2018](https://econpapers.repec.org/article/eeeecolet/v_3a171_3ay_3a2018_3ai_3ac_3ap_3a140-143.htm): on three US exchanges "average quoted and effective spreads for Bitcoin are lower than spreads on major equity exchanges", and the lowest spreads coincide with US trading hours. MEASURED abstract. Old data.
- [Makarov and Schoar, Journal of Financial Economics 135(2), 2020](https://www.sciencedirect.com/science/article/abs/pii/S0304405X19301746): large, persistent price gaps across crypto exchanges. So the venue's own price matters, not a composite index. MEASURED title and journal; detail from memory not re-read, treat as STATED.
- [Brauneis, Mestel, Riordan, Theissen, Journal of Banking and Finance 124, 2021](https://econpapers.repec.org/article/eeejbfina/v_3a124_3ay_3a2021_3ai_3ac_3as0378426620303022.htm): on how well low-frequency liquidity proxies track real crypto spreads. Abstract not fully read today. STATED.
- Maker fill risk (adverse selection): [Linnainmaa, Journal of Finance 65(4), 2010](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.2010.01576.x): retail limit orders "are price-contingent and suffer from adverse selection", which by itself explains much of the apparent poor performance of individual investors. MEASURED abstract. Stock data, not crypto, but the mechanism is the same: your resting order fills most often when the price is about to move against you, and does not fill when it would have helped.

Live snapshot I measured today from public, keyless order-book endpoints (Coinbase Exchange, Kraken, Gemini, Binance.US, and Alpaca's free crypto order book). Script and raw output kept in working notes. Cost = average buy price versus mid, walking the visible book. MEASURED.

Ten snapshots, about 20 seconds apart, ending 2026-11-25 06:33:45 UTC (evening of 2026-11-24 in Idaho, a quiet time). Medians across the ten. Script: data_run/books.py, raw output: data_run/books_out.txt.

| Venue | Pair | Quoted spread bps (median / max) | Cost vs mid, $1k buy (bps) | $10k | $100k |
|---|---|---|---|---|---|
| Coinbase Exchange | BTC-USD | 0.002 / 0.002 | 0.001 | 0.30 | 0.86 |
| Coinbase Exchange | ETH-USD | 0.51 / 0.91 | 0.38 | 0.53 | 1.83 |
| Kraken | XBT/USD | 0.017 / 0.017 | 0.008 | 0.009 | 0.24 |
| Kraken | ETH/USD | 0.94 / 1.93 | 0.56 | 0.77 | 2.06 |
| Gemini | BTC/USD | 0.85 / 2.19 | 0.90 | 1.36 | 1.66 |
| Gemini | ETH/USD | 0.06 / 9.85 | 0.03 | 0.18 | 3.12 |
| Binance.US | BTC/USD | 0.002 / 2.30 | 0.42 | 1.41 | 4.97 |
| Binance.US | ETH/USD | 0.33 / 0.73 | 0.50 | 1.66 | 6.54 |
| Alpaca (free crypto book) | BTC/USD | 2.66 / 3.69 | 4.40 | 4.91 | 5.67 |
| Alpaca (free crypto book) | ETH/USD | 2.83 / 3.92 | 4.90 | 5.45 | 8.66 |

Endpoints: `api.exchange.coinbase.com/products/{pair}/book?level=2`, `api.kraken.com/0/public/Depth`, `api.gemini.com/v1/book`, `api.binance.us/api/v3/depth`, `data.alpaca.markets/v1beta3/crypto/us/latest/orderbooks` (keyless, per [Alpaca crypto docs](https://docs.alpaca.markets/us/docs/crypto-pricing-data.md)).

Plain reading: for $1k to $10k, spread plus depth cost on the big US venues was under about 2 bps per side tonight. Alpaca's own crypto book was wider, about 4 to 5 bps per side, before its 25 bps taker fee. So on every venue the fee is the main cost for our sizes, not the spread. Spreads widen in stress; one snapshot says nothing about that. Paper crypto on Alpaca fills against Alpaca's book (my reading of the paper doc, which says fills use real-time quotes), so paper crypto results inherit Alpaca's wider spread.

### Recommended pessimistic cost assumptions for the replay test

The aim is to err toward too much cost. Numbers are per side (one way) versus the mid unless stated.

| Case | Assume | Why |
|---|---|---|
| Liquid ETF, market order in regular hours, size under $20k | Full quoted spread per side (not half), plus 1 bp. For SPY/QQQ that is about 1.3 bps; for TLT/XLE about 2.5 bps. | Alpaca 605 shows about half-spread per side. Using the full spread doubles it. Schwarz et al. show broker-to-broker spread of costs is wide. |
| Fill price on daily bars | Fill at next bar's open, not the signal bar's close, plus the cost above. | Avoids look-ahead. Open has its own auction behaviour. |
| Stop exits | If the next open gaps through the stop, fill at that open. Otherwise fill at the stop minus 5 bps for SPY/QQQ-class ETFs, minus 20 bps for single stocks, then add the cost above. | Alpaca 605 stop effective spreads: SPY 0.97 bps, QQQ 3.7 bps, AAPL 19.7 bps (thin samples, so round up). |
| MOO/MOC | Use the official open/close plus one quoted spread. Do not trust paper for this. | Paper fills auctions at bid/ask (staff). |
| Extended hours and overnight | Do not trade there in tests. If you must, assume at least 3 times the regular-hours quoted spread. | Not in 605 data. UNKNOWN costs. |
| BTC/ETH via Alpaca | Taker fee 25 bps plus measured half-spread plus depth cost for your size, on Alpaca's own book. With today's snapshot that is about 29 to 30 bps per side for $1k to $10k (25 fee plus 4.4 to 5.5 measured). Round to 35 bps. | Alpaca fee table and measured Alpaca book. |
| BTC/ETH on other venues | Their taker fee (check the venue's own schedule) plus measured half-spread plus depth cost, plus 2 bps. | Measured books. |
| Resting limit orders (maker) | Do not assume a fill when price only touches your limit. Require trade-through by at least one tick. Then also assume the missed trades are the good ones: count a missed entry as a missed winner. | Linnainmaa 2010; Alpaca and Kraken CLI paper both fill only on cross, with no queue. |
| Halts, LULD, SSR | Rare for these ETFs, but a stop during a pause cannot fill. Model the fill at the reopen price. | LULD plan, Rule 201. |
| Dividends | Use total-return logic for P/L but raw prices for signals and fills (see Part 3). | Alpaca paper does not pay dividends, so paper P/L will be low by the yield. |

Numbers we must measure ourselves.

In the Alpaca practice account:

- Fill price versus the SIP NBBO at submit time, for each order. Expect fills at the far side.
- Time from submit to fill, and how often partials happen. Expect worse than live.
- Whether crypto paper fills are charged a fee.
- Whether overnight orders are simulated.

With small real money:

- Effective spread and price improvement per side for our own ETF orders, by time of day. Compare with the 605 table above.
- Stop order slippage from trigger to fill.
- MOO/MOC fill versus official open/close.
- Crypto fill versus mid at submit, and the fee actually posted end of day.
- Maker fill rate and what price did after a fill (adverse selection) for any resting crypto limits.
- Regulatory fees posted, and dividends credited.
- Latency from our server to fill.

## Part 3. Common ways replay tests fool people

| Trap | Source | Fix |
|---|---|---|
| Look-ahead (using data not known at the time) | [Banz and Breen, J. Finance 41(4), 1986](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.1986.tb04548.x): database practice "may introduce a look-ahead bias and an ex-post-selection bias" that changes conclusions. | Signal on bar t close, trade at bar t+1 open. Store "known at" time for every input. |
| Survivorship | [Brown, Goetzmann, Ibbotson, Ross, Rev. Financial Studies 5(4), 1992](https://academic.oup.com/rfs/article-abstract/5/4/553/1590264). | Use the ETF and coin list as it was on each past date, including closed funds and delisted coins. |
| Overfitting from many trials | [Bailey and López de Prado, J. Portfolio Management 40(5), 2014](https://www.pm-research.com/content/iijpormgmt/40/5/94) (Deflated Sharpe Ratio); [Bailey, Borwein, López de Prado, Zhu, J. Computational Finance (PBO)](https://papers.ssrn.com/sol3/Papers.cfm?abstract_id=2326253): hold-out alone "tend[s] to be unreliable". | Log every variant tried. Report deflated Sharpe with the trial count. Run PBO via CSCV. Keep a final untouched period. |
| Data snooping in published rules | [Sullivan, Timmermann, White, J. Finance 54(5), 1999](https://onlinelibrary.wiley.com/doi/10.1111/0022-1082.00163); [Harvey, Liu, Zhu, RFS 29(1), 2016](https://academic.oup.com/rfs/article-abstract/29/1/5/1843824): new factors need "a t-statistic greater than 3.0"; [McLean and Pontiff, J. Finance 71(1), 2016](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.12365): returns "26% lower out-of-sample and 58% lower post-publication". | Assume a published rule's edge is at most half of what the paper shows. Test only after the paper's sample end. |
| Unrealistic fills | Alpaca paper doc (no size check, no queue); Linnainmaa 2010 (limit orders and adverse selection). | Use the Part 2 cost table. Fill limits only on trade-through. |
| Bid-ask bounce in minute bars | [Roll, J. Finance 39(4), 1984](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.1984.tb03897.x): trades bouncing between bid and ask create negative serial correlation in price changes. | For intraday tests use quote mids, not last-trade closes, for signals. Fill at bid or ask. |
| Adjusted prices used wrongly | Alpaca bars default to `raw`; options `split`, `dividend`, `spin-off`, `all` ([Alpaca stock bars reference](https://docs.alpaca.markets/us/reference/stockbars.md)). Paper does not process splits (forum 18569). | Signals on split- and dividend-adjusted series. Fills, position sizes and order prices on raw prices of that day. Add dividends as cash. |
| Timestamp errors | Alpaca: bar timestamp "is the left side of the interval"; daily bars truncated "to the day (in New York)" ([Market Data FAQ, updatedAt 2026-09-21](https://docs.alpaca.markets/us/docs/market-data-faq.md)). [Holden and Jacobsen, J. Finance 69(4), 2014](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12127): timestamp and quote-matching problems distort liquidity measures in fast markets. | A minute bar stamped 14:52 is only known at 14:53. Align crypto (UTC days) and stock (New York days) carefully. |
| Feed mismatch | Alpaca: IEX had 12,630 eligible AAPL trades on 2023-09-29 versus more than 535,136 across all exchanges (Market Data FAQ). | Backtest on SIP history. Do not compare IEX-based signals with SIP-based fills without noting it. |
