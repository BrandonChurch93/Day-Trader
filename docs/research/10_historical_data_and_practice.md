# Historical data and practice accounts: what to test on, and where to practise

Last verified: 2026-11-25.

Scope: past-price data for replaying stock, ETF and crypto rules, and practice accounts, for a US retail individual in Idaho trading his own money. No account was opened, no key requested and no order placed.

How it was made: three researchers wrote reports from primary pages and public price endpoints. One fresh checker re-opened the sources for 14 load-bearing claims and tried to prove them wrong. The raw reports are `docs/research/10_raw/stock_history_data.md`, `crypto_history_data.md` and `practice_environments.md`. The check table is `docs/research/10_raw/check/result_data.md`. Where the checker changed a figure, this file carries the checker's figure.

Tags: MEASURED means read on a primary page or measured from a public endpoint. STATED means someone's claim, not confirmed. UNKNOWN means not found, which is not the same as absent.

Status of everything recommended here: proposed by the research team. Nothing in this file is an owner decision.

> Note added 2026-11-25. The first data purchase recommended below is the Kibot end-of-day plan. Later the same night two stock tests were planned that need one-minute prices as well as daily ones, so the purchase now put to the owner is one month of the EODHD plan with both (`docs/decisions/morning_list_2026-11-25.md`). The rest of this page stands.

## Words used here

| Word | Meaning |
|---|---|
| Bar | One row of price history for a time slice: open, high, low, close and volume |
| Replay | Running a rule over past bars to see how it would have done |
| Practice account | Pretend money and pretend fills against live prices. Also called paper trading |
| SIP | The full US stock market feed, all exchanges combined |
| IEX | One single exchange. Its feed shows only a small part of all trades |
| Spread | The gap between the best price to buy and the best price to sell |
| Basis point (bp) | One hundredth of one percent |
| Effective spread | Twice the distance from your fill price to the midpoint |
| Rule 605 report | A broker's required monthly report on how it filled orders |
| Slippage | The difference between the price a rule expected and the price it got |
| Taker fee | The fee charged when an order fills at once against a resting order |
| Dead-coin problem | Testing only on coins still listed today, which hides the ones that failed |

## Bottom line

| # | Question | Proposal | Main reason |
|---|---|---|---|
| 1 | First stock and ETF data purchase | **Kibot** end-of-day plan, $14 for one month, as a one-time download | Lowest price found for decades of daily history, and the licence lets him keep the data for good. It is not a daily feed |
| 2 | Runner-up | **EODHD** EOD Historical, $19.99 a month | Its help pages expressly allow keeping data after cancelling and using it with his own ChatGPT or Claude account |
| 3 | Crypto data | Keep Bitstamp public bars for bitcoin and ether, cross-checked with Kraken's free files | Already used by the rig (`docs/research/12_replay_01_crypto_trend.md`). Our right to use Bitstamp's bars for research is UNKNOWN until the US terms are read |
| 4 | Practice venue | Alpaca practice account, as proposed in `docs/research/09_brokers_and_venues.md` | Same connection as live, covers stocks and crypto. Its fills differ from real fills, so we add costs ourselves |
| 5 | Cost for small ETF orders | Keep `cost_model_bps_per_side_liquid_etf` | Alpaca's October 2026 spreads sit well under it, so it errs toward too much cost |

## Stock and ETF history

| Source | Price | Depth | Keep and AI use | Tag |
|---|---|---|---|---|
| Kibot end-of-day | $14 a month ([Kibot plans](https://www.kibot.com/subscribe.html)) | Up to 64 years of daily history | Delivered data "is his to keep permanently" ([Kibot licence](https://www.kibot.com/license.html)). The raw report reads the licence as also allowing own-use cloud and AI analysis | MEASURED |
| EODHD | $19.99 a month daily, $29.99 a month daily plus one-minute ([EODHD pricing](https://eodhd.com/pricing/)) | US one-minute since 2004 ([EODHD intraday](https://eodhd.com/financial-apis/intraday-historical-data-api)) | Keep after cancelling for private, non-commercial use ([EODHD storage](https://eodhd.com/help/storage)). Own ChatGPT or Claude account needs no separate permission ([EODHD AI tools](https://eodhd.com/help/ai-tools)) | MEASURED |
| Alpaca Basic | Free. The $99 plan does not reach further back ([Alpaca market data](https://docs.alpaca.markets/us/docs/about-market-data-api.md)) | Since 2016 | Personal, non-commercial use ([Alpaca terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf)). Keep-after-close and AI use UNKNOWN | MEASURED |
| Norgate Platinum | $630 a year ([Norgate packages](https://norgatedata.com/stockmarketpackages.php)) | To 1990, with delisted names and past index members | Data must be destroyed when the subscription lapses | MEASURED |
| Sharadar direct | $39 a month full history, $69 bundle ([Sharadar subscribe](https://sharadar.com/subscribe)) | Daily, from late 1997 | Raw data deleted within 30 days of ending ([Sharadar terms](https://sharadar.com/terms)) | MEASURED |
| Tiingo free tier | $0 | Daily back to 1962 where available | Free tier may not store data at all ([Tiingo terms, updated November 5, 2026](https://www.tiingo.com/tos/)) | MEASURED |
| Yahoo Finance | $0 to view | Not confirmed | Terms bar automated collection "for any purpose without our express, prior permission" ([Yahoo terms](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html)) | MEASURED |

What matters for the choice:

- The Kibot $14 plan refreshes only "the day the subscription starts and every 3 months after that" ([Kibot FAQ](https://www.kibot.com/faq.html)). It suits one archive download, not a daily update. MEASURED.
- EODHD's keep and AI permissions are help-centre text, not the Terms themselves. MEASURED.
- Alpaca's free plan gives full-market (SIP) history as long as the request ends at least 15 minutes ago ([Alpaca market data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq.md)). But Alpaca's paper page says "As an Alpaca Paper Only Account holder, you are only entitled to receive and make use of IEX market data" ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). Free full-market history may therefore depend on account type. MEASURED.
- Sharadar's $39 product already includes the S&P 500 membership table, with history to 1998 ([Sharadar bundle](https://sharadar.com/bundle)). The $69 bundle is not needed for that. MEASURED.
- If single stocks are ever tested, Norgate is the clearest option, though its delisted coverage is "for select delisted security types" ([Norgate packages](https://norgatedata.com/stockmarketpackages.php)). MEASURED.
- Every planned ETF traded before 2008, HYG only from April 2007. Start dates are in `10_raw/stock_history_data.md`.

## Crypto history

| Source | Price | Bitcoin from | Ether from | Limits | Tag |
|---|---|---|---|---|---|
| Bitstamp public bars | $0, no key ([Bitstamp API](https://www.bitstamp.net/api/)) | 2011-09-02 daily | 2017-08-16 daily | 1,000 bars per call. Delisted pairs return an error | MEASURED |
| Kraken files | $0, direct download ([Kraken OHLCVT files](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data)) | 2013-10-06 | 2015-08-07 | Quarterly. Latest runs through September 30, 2026 | MEASURED |
| Coinbase public bars | $0, no key | 2015-07-20 daily | 2016-05-18 daily | 300 to 350 bars per call. Keeps delisted pairs | MEASURED |
| Alpaca crypto bars | $0, no key | 2021-01-01 | 2021-01-01 | Misses 2018. No-trade bars use quote midpoints ([Alpaca market data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq.md)) | MEASURED |
| Binance.US public bars | $0, no key | 2019-09-17 | 2019-09-18 | No US dollar pair data from 2023-07-14 to 2025-02-19 | MEASURED |

What the terms say:

- Bitstamp's general terms say its materials "should not be copied, reproduced ... collected or distributed in any form or by any means, whether manual or automated", and also "You may view, print and/or download a copy of the Materials ... solely for your personal, informational and/or non-commercial use" ([Bitstamp terms](https://www.bitstamp.net/terms-of-use/)). MEASURED.
- Bitstamp's US terms page could not be opened, by the researcher or the checker. Our use of its public bars for research is UNKNOWN until read by the owner or a professional. Commercial users must sign a data licence ([Bitstamp API](https://www.bitstamp.net/api/)). MEASURED.
- Coinbase's market data terms, as passed through in [Tardis terms](https://docs.tardis.dev/legal/terms-of-service) clause 23.1, bar using Coinbase data for any AI model or "automated system". MEASURED through that page. Coinbase's own page did not open.
- Kraken's file terms are not stated, and its developer guide says "Kraken does not provide a bulk historical data dump" ([Kraken historical data guide](https://docs.kraken.com/exchange/guides/general/historical-data)). The newer support page and files say otherwise. MEASURED.
- Binance's offshore archive bans "live proprietary trading execution" ([Binance Vision terms](https://raw.githubusercontent.com/binance/binance-public-data/master/TERMS_AND_CONDITIONS.md)), and Binance bars US persons. Do not use it. MEASURED.

Data faults to handle in the replay:

- The first Binance.US bar after the gap, 2025-02-19, is a bad print: 0.29 BTC volume and a low of 77,838 against an open of 96,236. Drop it. MEASURED.
- A Bitstamp request that starts far before the first bar returns an empty list, which a careless loop can read as no data. Early bars are thin. MEASURED.
- Coinbase's older daily endpoint gave a bitcoin close for 2026-11-13 about 6% off. Cross-check daily bars against a second venue. MEASURED.

The dead-coin problem. Bitstamp's public bars drop delisted pairs, so a Bitstamp basket beyond bitcoin and ether would hold only survivors. Coinbase still serves several delisted pairs. Kraken and Binance.US keep some. MEASURED, in `10_raw/crypto_history_data.md`. A fair test needs the coin list as it stood on each past date, which no free source here supplies. Bitcoin and ether alone avoid the problem.

## Practice accounts

| Venue | How practice fills work | Tag |
|---|---|---|
| Alpaca | Fills at the best current market price (NBBO). Order size is not checked against what is on offer. Random partial fills 10% of the time ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)) | MEASURED |
| Interactive Brokers | Fills from the top of the book. Dividends and splits not processed ([IBKR paper limits](https://www.interactivebrokers.com/support/faq/content/limitations-paper-trading-account-35807733)) | MEASURED |
| Kraken command-line practice | Buys at the ask, sells at the bid, 0.26% fee by default, no partial fills ([Kraken CLI](https://github.com/krakenfx/kraken-cli)) | MEASURED |
| tastytrade test system | Fills at the midpoint, resets every 24 hours ([tastytrade sandbox](https://developer.tastytrade.com/docs/sandbox)) | MEASURED |
| Gemini test exchange | Bots make the order book ([Gemini sandbox](https://developer.gemini.com/get-started/sandbox)) | MEASURED |
| Coinbase test system | Fixed replies only, not a simulator ([Coinbase sandbox](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/sandbox)) | MEASURED |
| Binance.US | A test order is checked but never filled. No practice exchange found | MEASURED test order, practice exchange UNKNOWN |

Alpaca's paper page lists as not simulated: market impact, slippage from delay, queue position, price improvement, regulatory fees and dividends ([Alpaca paper trading](https://docs.alpaca.markets/us/docs/paper-trading.md)). MEASURED. It says "Paper trading simulates crypto trading as well", but says nothing on whether the crypto fee is charged on practice fills. UNKNOWN. Alpaca's live crypto taker fee at the lowest tier is 0.25% and the maker fee 0.15% ([Alpaca crypto trading](https://docs.alpaca.markets/us/docs/crypto-trading.md)). That is 0.50% for a round trip as a taker. MEASURED.

Alpaca staff posts add, as STATED, that paper does not process splits and treats auction orders as plain market orders. Detail is in `10_raw/practice_environments.md`.

What we must add ourselves in replay and practice:

- The crypto taker fee on every crypto fill.
- Regulatory fees on stock sells.
- Dividends, as cash, since practice pays none.
- Slippage for stop orders and for orders larger than the shown size.
- Limit orders that fill only when price trades through them.

## Small-order spreads on the main ETFs

From Alpaca's own Rule 605 file for October 2026 ([Alpaca 605 reports](https://alpaca.markets/disclosures/605-reports), [October 2026 file](https://files.alpaca.markets/disclosures/library/SEC+Rule+605/APCA202610.zip)), plain market orders in regular hours, all size buckets pooled and weighted by shares. MEASURED, recomputed by the checker from the per-symbol file, because the PDF prints only totals.

| Fund | Average effective spread (bps) | Note |
|---|---|---|
| SPY | 0.12 | |
| QQQ | 0.17 | |
| TLT | 0.51 | |
| GLD | 0.34 | |
| IBIT | 2.27 | Driven by 106 orders of $200,000 and over. Small orders were 0.69 to 1.43 bps |

- These are full effective spreads. One-way cost is half. MEASURED.
- One month, regular hours only, no auctions. MEASURED.
- Stop market orders cost far more: SPY 0.97 bps, QQQ 3.70 bps, on small samples. MEASURED, in `10_raw/605_symbols.txt`.
- One quiet-evening snapshot of crypto books put Alpaca's own book at about 4 to 5 bps per side for $1,000 to $10,000, before the fee. At our sizes the fee is the main cost. MEASURED, in `10_raw/books_out.txt`.

## What the check changed

One checker checked 14 claims: 11 held, 3 were overstated, none wrong. With one checker there was no disagreement to settle.

| Claim | Change carried here |
|---|---|
| Kibot $14 plan | Holds, but refreshes only every three months |
| Sharadar | The $39 product already includes S&P 500 membership |
| Alpaca free history | Paper-only accounts are entitled to IEX data only, so free full-market history may depend on account type |
| Alpaca practice crypto fee | The 0.25% fee is true, but no page says whether practice charges it. Now UNKNOWN |
| IBIT spread | 2.27 bps holds for all orders. Small orders were 0.69 to 1.43 bps |
| Bitstamp terms | General terms both allow a personal download and bar automated collection. US terms not opened |
| Binance.US gap | Holds. The 2025-02-19 bar is a bad print |
| Bitstamp bitcoin start | Raw report said 2011-08-18 daily. The checker's call returned 2011-09-02. This file carries the later date |

## Not verified or unfinished

- Bitstamp's US terms of use. UNKNOWN.
- Whether Alpaca practice charges the crypto fee. UNKNOWN.
- Whether a paper-only Alpaca account gets free full-market history. UNKNOWN until tried.
- Kraken file terms, and Kibot's earliest bar for each ETF. UNKNOWN.
- A free source of past coin listings for a fair test beyond bitcoin and ether. Not found.

## What research proposes

1. Buy one month of the Kibot $14 end-of-day plan and download the full daily ETF archive once, because it is the cheapest durable archive and may be kept permanently; EODHD at $19.99 is the runner-up if its plain AI permission matters more.
2. Before relying on Bitstamp bars further, have the owner or a professional read Bitstamp's US terms, because the general terms are mixed and the US page could not be opened.
3. Keep bitcoin and ether as the only coins in crypto replays, because no free source here was found that avoids the dead-coin problem for others.
4. Use the Alpaca practice account to debug programs, not to judge results, and add fees, dividends and stop slippage in our own records, because the practice account does not simulate them.
5. Keep `cost_model_bps_per_side_liquid_etf` for ETF replays, because Alpaca's October 2026 small-order spreads sit well under it.
6. Drop the Binance.US 2025-02-19 bar and check every data set for gaps, because both faults were measured.
