# Historical data and practice accounts: what to test on, and where to practise

Last verified: 2026-11-25.

Scope: past-price data for replaying stock, ETF and crypto rules, and practice accounts, for a US retail individual in Idaho trading his own money. No account was opened, no key requested and no order placed.

How it was made: three researchers wrote reports from primary pages and public price endpoints. One fresh checker re-opened the sources for 14 load-bearing claims and tried to prove them wrong. The raw reports are `docs/research/10_raw/stock_history_data.md`, `docs/research/10_raw/crypto_history_data.md` and `docs/research/10_raw/practice_environments.md`. The check table is `docs/research/10_raw/check/result_data.md`. Where the checker changed a figure, this file carries the checker's figure.

Tags: MEASURED means read on a primary page or measured from a public endpoint. STATED means someone's claim, not confirmed. UNKNOWN means not found, which is not the same as absent.

Status of everything recommended here: proposed by the research team. Nothing in this file is an owner decision.

> Note added 2026-11-25. The first data purchase recommended below is the Kibot end-of-day plan. Later the same night two stock tests were planned that need one-minute prices as well as daily ones, so the purchase now put to the owner is one month of the EODHD plan with both (`archive/decisions/morning_list_2026-11-25.md`). Row 3 of the table below is also superseded: research now proposes Kraken's published files as the main crypto history, with Bitstamp as the cross-check, because Bitstamp's terms are unclear about collecting its prices (item 3 of "Things only you can do" in the same list). The rest of this page stands.

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
- Every planned ETF traded before 2008, HYG only from April 2007. Start dates are in `docs/research/10_raw/stock_history_data.md`.

## Price history inside the workspace

Added 2026-11-25 by research. Status: a finding and a proposal. No rule has been run on this data, and no owner decision is recorded here.

The Perplexity workspace that research runs in has its own price history lookup. Research had not tried it for bulk history until 2026-11-25. What a probe of it showed, MEASURED from the files it returned (kept outside the repo in `research_rig/data/platform_probe/`):

- Daily prices go back to a fund's first trading day. The first SPY row is 1993-01-29 and the first XLE row is 1998-12-22.
- One-minute prices exist for SPY in March 2005 and March 2012, the two months probed first, with 390 rows for each regular trading day. Times are in UTC. Hours outside the regular session are not included.
- One request returns at most 5,000 daily rows, or 1,170 one-minute rows, which is three trading days. When a request covers more, it returns the last rows of the range and says nothing.
- A request for dates with no data does not fail. It returns the most recent days. So every file has to be checked against the dates that were asked for.
- It refused requests when six were sent at once.
- It has no dividend history. Daily closes look adjusted for splits and not for dividends. That is research's inference from the first SPY rows, not a statement by the provider.

What is UNKNOWN:

- Who the data comes from, and how it is adjusted.
- What its terms say about keeping copies and using them for tests. Research found no terms for it. The owner works at Perplexity and can ask. This is item 6 of "Things only you can do" in `archive/decisions/morning_list_2026-11-25.md`.
- Whether the prices are right. The check below looks for gaps and broken rows. It does not compare a price with a second source, and nothing has.
- Whether a day the check calls a holiday really was one. The check's holiday calendar was written from memory by the collecting agent, not taken from the exchange.

### What was collected, and what a gap check found

Added 2026-11-25 after the collection finished. Research collected one-minute prices for SPY and QQQ, and daily prices for the funds in the second table below. Those are the funds named in the draft fund plan (`research_rig/PREREG_06_fund_trend_paid_data.md`), plus a long bond fund, a whole-market fund and the sector funds, which no plan names yet. The files are on the research machine and not in the repo. STATED by research: no trading rule has been run on them and no return over time has been worked out from them. Nothing in the repo can prove that.

How the tables below are made:

- `research_rig/platform_bars_consolidate.py` joined the pulls into one file per fund for daily prices, and one per fund and year for one-minute prices.
- `research_rig/platform_bars_integrity.py` checked them for gaps and broken rows.
- `research_rig/platform_bars_crosscheck.py` compared the one-minute files with the daily files, day by day. Its bands were fixed and pushed before it was run.
- `tools/bars_coverage.py` copied the dates and counts into `research_rig/platform_bars_coverage.json`, which holds no price, and wrote the tables from that file and from `research_rig/platform_bars_crosscheck.json`. Nothing in the tables is typed.

Every figure in the tables is MEASURED by those scripts, on files only the research machine has. A reader of the repo can check that the tables match the two summary files, and that the summary names the same files as `research_rig/provenance.json`. A reader cannot check the counts themselves without the price files.

<!-- bars:start (written by tools/bars_coverage.py, do not edit by hand) -->

One-minute prices, regular session only:

| Fund | First day | Last day | Trading days | Rows | Days with 390 different times | Days with exactly the 390 minutes of a full session | Short days that are not a known early close | Weekdays with no data that are not a holiday | Repeated times |
|---|---|---|---|---|---|---|---|---|---|
| SPY | 2003-09-10 | 2026-11-24 | 5,838 | 2,264,958 | 5,759 | 5,759 | 26 | 2 | 0 |
| QQQ | 2011-03-23 | 2026-11-24 | 3,943 | 1,531,562 | 3,880 | 3,880 | 29 | 0 | 0 |

Daily prices:

| Fund | First day | Last day | Rows | Weekdays with no row that are not a holiday | Repeated days | Days with zero volume | Days where two pulls disagreed |
|---|---|---|---|---|---|---|---|
| SPY | 1993-01-29 | 2026-11-24 | 8,514 | 0 | 0 | 0 | 1 |
| QQQ | 1999-03-10 | 2026-11-24 | 6,972 | 0 | 0 | 0 | 0 |
| EFA | 2001-08-17 | 2026-11-24 | 6,355 | 0 | 0 | 0 | 0 |
| IEF | 2002-07-30 | 2026-11-24 | 6,121 | 0 | 0 | 0 | 0 |
| VNQ | 2004-09-29 | 2026-11-24 | 5,575 | 0 | 0 | 0 | 0 |
| DBC | 2006-02-03 | 2026-11-24 | 5,235 | 0 | 0 | 0 | 0 |
| BIL | 2007-05-30 | 2026-11-24 | 4,905 | 0 | 0 | 0 | 0 |
| GLD | 2004-11-18 | 2026-11-24 | 5,539 | 0 | 0 | 0 | 0 |
| TLT | 2002-07-30 | 2026-11-24 | 6,121 | 0 | 0 | 0 | 0 |
| VTI | 2001-05-31 | 2026-11-24 | 6,410 | 0 | 0 | 0 | 0 |
| IWM | 2000-05-26 | 2026-11-24 | 6,664 | 0 | 0 | 0 | 0 |
| XLB | 1998-12-22 | 2026-11-24 | 7,024 | 0 | 0 | 0 | 0 |
| XLE | 1998-12-22 | 2026-11-24 | 7,024 | 0 | 0 | 0 | 0 |
| XLF | 1998-12-22 | 2026-11-24 | 7,024 | 0 | 0 | 0 | 0 |
| XLI | 1998-12-22 | 2026-11-24 | 7,024 | 0 | 0 | 1 | 0 |
| XLK | 1998-12-22 | 2026-11-24 | 7,024 | 0 | 0 | 0 | 0 |
| XLP | 1998-12-22 | 2026-11-24 | 7,024 | 0 | 0 | 0 | 0 |
| XLU | 1998-12-22 | 2026-11-24 | 7,024 | 0 | 0 | 0 | 0 |
| XLV | 1998-12-22 | 2026-11-24 | 7,024 | 0 | 0 | 0 | 0 |
| XLY | 1998-12-22 | 2026-11-24 | 7,024 | 0 | 0 | 0 | 0 |
| XLC | 2018-06-19 | 2026-11-24 | 2,121 | 0 | 0 | 0 | 0 |
| XLRE | 2015-10-08 | 2026-11-24 | 2,799 | 0 | 0 | 5 | 0 |

What the check found that looks wrong:

- SPY one-minute: no data on 2004-12-31, 2010-12-31, which the check's calendar has as trading days.
- SPY one-minute: 26 short days that are not a known early close, the first on 2003-09-12 with 150 rows and the last on 2026-03-09 with 389. Every date is in `research_rig/platform_bars_coverage.json`.
- SPY one-minute: rows that are not on a whole minute: 4. Days with more than 390 rows: 4.
- SPY one-minute: rows with zero volume: 164.
- SPY one-minute: days whose last bar is not at the expected time (15:59 New York time, or 12:59 on a day the check's calendar has as an early close): 27. Every date is in the same file.
- SPY one-minute: of the 49 days the check's calendar has as early closes, 13 do not have the 210 rows of a 13:00 close. The most rows on one is 227.
- SPY one-minute: 19 request windows never returned a row inside the dates asked for, as the join script recorded them. Of those, 17 were for dates before the first day in the table.
- QQQ one-minute: 29 short days that are not a known early close, the first on 2011-04-25 with 389 rows and the last on 2026-02-09 with 389. Every date is in `research_rig/platform_bars_coverage.json`.
- QQQ one-minute: rows that are not on a whole minute: 1. Days with more than 390 rows: 1.
- QQQ one-minute: rows with zero volume: 456.
- QQQ one-minute: days that do not start at 09:30 New York time: 1.
- QQQ one-minute: 20 request windows never returned a row inside the dates asked for, as the join script recorded them. Of those, 20 were for dates before the first day in the table.
- Daily: two pulls of the same day gave different values for SPY. The join script kept the row from the file written last. Nothing checked that the later one is the right one.

What the check counted and found none of: a repeated time in a one-minute file, a repeated day in a daily file, a weekend row in any file, a missing or zero price (text that is not a number counts as missing), a high below a low, an open or close outside the bar's high and low, a row without six fields, a value that is not finite or is below zero, or a one-minute bar outside the regular session.

Do the one-minute files and the daily files agree with each other? For every day in both, the day's open, high, low and close were rebuilt from the one-minute bars and compared with the daily row. The gap is in basis points of the daily figure (1 bps is 0.01%). Each cell is a count of days, except in the last column:

| Fund | Figure | Days compared | Up to 1 bps | Over 1, up to 5 bps | Over 5, up to 10 bps | Over 10, up to 25 bps | Over 25 bps | Largest gap |
|---|---|---|---|---|---|---|---|---|
| SPY | open | 5,838 | 5,586 | 161 | 43 | 31 | 17 | -389.6 bps on 2008-12-16 |
| SPY | high | 5,838 | 5,578 | 111 | 51 | 46 | 52 | +4,074.0 bps on 2005-02-17 |
| SPY | low | 5,838 | 5,563 | 85 | 53 | 67 | 70 | -8,944.4 bps on 2004-03-16 |
| SPY | close | 5,838 | 2,484 | 2,269 | 504 | 449 | 132 | +221.5 bps on 2008-10-10 |
| QQQ | open | 3,943 | 3,899 | 36 | 1 | 6 | 1 | -27.5 bps on 2026-02-09 |
| QQQ | high | 3,943 | 3,885 | 41 | 6 | 5 | 6 | +228.2 bps on 2016-08-01 |
| QQQ | low | 3,943 | 3,911 | 19 | 5 | 2 | 6 | -273.3 bps on 2019-12-03 |
| QQQ | close | 3,943 | 1,823 | 1,871 | 209 | 37 | 3 | +84.2 bps on 2020-03-13 |

What that comparison found:

- SPY: the middle close gap for each year lies between -2.90 bps (2003) and +0.93 bps (2009). The year furthest from zero is 2003.
- SPY: days where the one-minute high is above the daily high by more than 1 bps: 33. Days where the one-minute low is below the daily low by more than 1 bps: 43. Neither should happen if both files are right, cover the same session and are adjusted the same way. The comparison does not show which of those fails, or which file is off.
- SPY: the comparison did not leave out the short days that are not a known early close, where minutes are missing from the one-minute files. The yearly middle gaps above include them. Days over 25 bps that are such short days: open 0 of 17, high 4 of 52, low 3 of 70, close 7 of 132.
- QQQ: the middle close gap for each year lies between -0.39 bps (2020) and +0.31 bps (2022). The year furthest from zero is 2020.
- QQQ: days where the one-minute high is above the daily high by more than 1 bps: 4. Days where the one-minute low is below the daily low by more than 1 bps: 2. Neither should happen if both files are right, cover the same session and are adjusted the same way. The comparison does not show which of those fails, or which file is off.
- QQQ: the comparison did not leave out the short days that are not a known early close, where minutes are missing from the one-minute files. The yearly middle gaps above include them. Days over 25 bps that are such short days: open 1 of 1, high 0 of 6, low 0 of 6, close 0 of 3.
- Every date with a gap over 25 bps is in `research_rig/platform_bars_crosscheck.json`, with the gap and no price.

<!-- bars:end -->

How to read this:

- A first day in the one-minute table is the first day this collection got. It is not proven to be the first day the lookup has. Requests for earlier dates returned no row inside the dates asked for.
- The days with no SPY one-minute data, named in the list above, were trading days. The exchange index closed on Friday, December 31, 2004 ([Boston Fed year-end report](https://www.bostonfed.org/-/media/Documents/stock-market-report/smrye04.pdf)), and stocks traded on the last day of 2010 ([Reuters](https://www.reuters.com/article/markets/stocks/snapshot-wall-st-posts-double-digit-gains-in-2010-idUSWEN4939/)). MEASURED from those two pages. So these are gaps in the data.
- Research's reading, not a measurement: the yearly middle gaps in the list above are small, which is what one would see if the one-minute files and the daily files are adjusted the same way. It does not prove it. No test against a dividend history was done, a yearly middle can hide errors that cancel, and those figures include days with minutes missing. Which way the files are adjusted is UNKNOWN, and the provider has not said.
- A close gap of a few basis points on most days is what research expects, because the daily close is set after the last one-minute bar ends. Research has not checked that against a source.
- On some days a one-minute price sits outside the day's range in the daily file. MEASURED, in the list above. That should not happen if both files are right and comparable. Which file is off on those days is not shown, and nothing has tested it. If the one-minute bar is the wrong one, a stop or a breakout rule could trade on a price that never happened. So a test on this data needs a written rule for these days before it runs.
- The comparison did not leave out the short days that are not a known early close. Where the missing minutes are at the end of the day, the last one-minute price is not the day's close, and a close gap there is not a fault in either file. Missing minutes cannot explain a one-minute price outside the daily range.
- Research's view, not a measurement: this data can be used to write and debug a test. A result from it should not be believed until a second source agrees, and nothing has compared it with one.

The short days are of three kinds, and only some have been told apart:

- Days of known halts. Trading on the New York Stock Exchange stopped at 3:56 pm on June 1, 2005 and did not resume ([exchange record of special closings](https://www.ltadvisors.net/Info/research/closings.pdf)). The SPY data for that day stops earlier than that. The halt does not explain the minutes missing before it. All US stock trading stopped for 15 minutes on March 9, 12, 16 and 18, 2020 ([SEC filing on the circuit breaker](https://www.sec.gov/files/rules/sro/nyse/2021/34-92428-ex3.pdf)). Trading in Nasdaq-listed shares was shut for three hours on August 22, 2013, as reported by [CNBC](https://www.cnbc.com/2013/08/22/nasdaq-connectivity-issue-led-to-threehour-shutdown.html). Each of these dates is in the list of short days in `research_rig/platform_bars_coverage.json`.
- Days with one or two minutes missing. Whether no trade happened in that minute or the data lost it is UNKNOWN.
- Days with a large part missing and no event research could find, the first weeks of the SPY data among them. Treat these as gaps in the data.

About the calendar the check uses:

- Its holidays and early closes were written from memory by the collecting agent.
- An outside checker found some days it had as both a holiday and an early close, and one early close it missed in December 2003. Both are fixed in the script.
- For September 2003 to December 2007 its early closes now match the exchange record linked above, whose last entry is dated December 24, 2007. MEASURED by research against that record. After 2007 they are unchecked.
- On some early closes the SPY files run past 13:00. The dates and row counts are in `research_rig/platform_bars_coverage.json`. Research has not found out why.

What the join script does not do. An outside read of the code found these. They are not fixed, because research has not run the join again: its inputs are the original pulls, which are fingerprinted nowhere.

- It skips a pull file whose name or header it does not expect, and rows outside the dates asked for, without stopping. It counts them in its own log, which is not in the repo.
- When two pulls disagree on a row it keeps the one from the file written last. Nothing shows the later one is better.
- The original pulls and the check's full output are not fingerprinted in `research_rig/provenance.json`. Only the joined files are.

Two limits of the gap check that the same read found are now fixed, and the check was run again: it counts the days that hold exactly the minutes of a full session, and it looks for weekend rows in the one-minute files too.

What this means for the tests and the purchase:

- Replay 07 (day trading SPY and QQQ on one-minute prices) could run its day-only rules without a purchase, if the owner allows this data and the plan first says how the faults listed above are handled. As drafted it cannot run in full: its night-only rule N5 needs dividend history (the draft plan, since frozen as `research_rig/PREREG_07_intraday_spy_qqq.md`, which settles it). On this data alone N5 would have to be dropped, and the plan would have to say so before it is frozen.
- Replay 06 (slow trend on funds that can be bought) still needs dividend history, which this lookup does not have. The purchase above is still the recommended source for it.
- The purchase is still worth making for a second reason. A second source changed a result once already: no bitcoin rule that passed on Bitstamp's history in the first run passed on Kraken's (`docs/research/12b_replay_01_kraken_crosscheck.md`). A test on one unchecked source should not be believed.
- Until the owner answers, research runs no rule on this data. The files stay out of the repo, like all raw prices.

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

The dead-coin problem. Bitstamp's public bars drop delisted pairs, so a Bitstamp basket beyond bitcoin and ether would hold only survivors. Coinbase still serves several delisted pairs. Kraken and Binance.US keep some. MEASURED, in `docs/research/10_raw/crypto_history_data.md`. A fair test needs the coin list as it stood on each past date, which no free source here supplies. Bitcoin and ether alone avoid the problem.

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

Alpaca staff posts add, as STATED, that paper does not process splits and treats auction orders as plain market orders. Detail is in `docs/research/10_raw/practice_environments.md`.

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

1. (Superseded on 2026-11-25. The purchase now put to the owner is one month of the EODHD plan with daily and one-minute prices, because two planned tests need one-minute prices and dividends. See the note at the top of this page and item 2 of `archive/decisions/morning_list_2026-11-25.md`. The line as first written follows.) Buy one month of the Kibot $14 end-of-day plan and download the full daily ETF archive once, because it is the cheapest durable archive and may be kept permanently; EODHD at $19.99 is the runner-up if its plain AI permission matters more.
2. Before relying on Bitstamp bars further, have the owner or a professional read Bitstamp's US terms, because the general terms are mixed and the US page could not be opened.
3. Keep bitcoin and ether as the only coins in crypto replays, because no free source here was found that avoids the dead-coin problem for others.
4. Use the Alpaca practice account to debug programs, not to judge results, and add fees, dividends and stop slippage in our own records, because the practice account does not simulate them.
5. Keep `cost_model_bps_per_side_liquid_etf` for ETF replays, because Alpaca's October 2026 small-order spreads sit well under it.
6. Drop the Binance.US 2025-02-19 bar and check every data set for gaps, because both faults were measured.
