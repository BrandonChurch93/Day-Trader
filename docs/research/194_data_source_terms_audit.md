# 194. Terms audit of every outside data source

What this is: a read of the terms each outside data provider publishes, set against what this project reads from it and what it publishes. It was written on 2026-11-26 (UTC) after the five crypto forward loggers were paused on Coinbase's Market Data Terms (see the PAUSE NOTE in [the queue](../QUEUE.md)).

This is not legal advice. It says what each provider's page says, and where the wording can be read more than one way. Labels:

- MEASURED: I read it on the provider's own page today; the inline link goes to that page, with the page's updated date where it shows one.
- STATED: read in a search excerpt only, page not opened in full.
- UNKNOWN: the page did not open, was blocked, or says nothing on the point.

How this was done: the code was read only (no script run, no data file opened, no price call). Hosts were found by reading the source of `practice/`, `research_rig/`, `timemachine/`, `tools/`, `.github/workflows/` and the two named off-repo watchers. Hosts that appear only as citation strings in report scripts are left out. Sealed or vault folders were not read.

## Inventory

These are the hosts the code fetches from (MEASURED from source). "Published" means results derived from the host, or raw data, sit in tracked files of this public repo.

- `api.exchange.coinbase.com` (Coinbase Exchange public REST). Read by `practice/forward_e06.py`, `practice/forward_e09.py`, `practice/forward_e10.py`, `practice/measure_132.py` (and `practice/forward_e11.py` through its imports), `research_rig/coinbase_72.py`, `research_rig/score_47.py`, `research_rig/feeds/product_status_watcher.py`, the off-repo watcher `/home/user/workspace/rig/bin/product_status_watcher.py` and `docs/research/09_raw/orderbook_sampler.py`. Candles, level-1 books, product lists. The loggers are paused. The off-repo status watcher was still running at 300 s when read. Published: pretend-trade logs `practice/forward/E09_log.json`, `practice/forward/E10_log.json`, `practice/forward/E11_log.json`, `practice/forward/M132_log.json` are tracked (not opened here), plus cards and readouts.
- `api.coinbase.com` (Advanced Trade public market endpoints). `practice/forward_e09.py`, `practice/sampler_p58_quotes.py`, and the off-repo Upbit watcher `/home/user/workspace/rig/data/upbit_forward/watcher.py` (futures product list). Books and product lists. Live in the Upbit watcher.
- `api.binance.us`. `practice/forward_e10.py`, `practice/measure_132.py`, `docs/research/09_raw/orderbook_sampler.py`. Live books and candles, now paused. Published in the same logs, and raw book samples in `docs/research/09_raw/orderbook_snapshots.jsonl` (venues taken from the sampler code; the file was not opened).
- `api.kraken.com`. `research_rig/fetch.py`, both product status watchers, the Upbit watcher, the 09 sampler. Asset pairs and status (live in the watchers), books (09 raw samples, published), history.
- `assets.kraken.com`. `research_rig/fetch_kraken_archive.py`. Downloadable OHLCVT files. History.
- `futures.kraken.com`. `research_rig/feeds/collect_context.py`. Tickers. Context feed.
- `api.gemini.com`. `docs/research/09_raw/orderbook_sampler.py`. Books. History, raw samples published in `docs/research/09_raw/orderbook_snapshots.jsonl`.
- `www.bitstamp.net`. `research_rig/fetch.py`, `research_rig/build_doc12b.py`. Prices. History.
- `api.upbit.com`. The off-repo Upbit watcher. Market list. Live at 300 s.
- `external-api.kalshi.com` (margin markets) in the off-repo Upbit watcher, live; `api.elections.kalshi.com` markets in `research_rig/feeds/collect_context.py`. Market lists.
- `data.alpaca.markets`, `paper-api.alpaca.markets`. `practice/market.py`, `practice/broker.py`, `practice/forward_e01.py`, `practice/forward_e03.py`, `practice/forward_e07.py`, `practice/forward_e08.py`, many `research_rig/` fetch and score scripts, `timemachine/record.py`, and the off-repo logger `/home/user/workspace/rig/data/reverse_split_forward/logger.py`. Stock bars, quotes, pretend orders. Live, including the GitHub Actions run of `practice/trader.py` from `.github/workflows/practice-trader.yml`. Published: practice logs such as `practice/forward/E07_log.json` (not opened).
- `www.sec.gov`, `data.sec.gov`. `practice/forward_e03.py`, `research_rig/fetch_11_edgar.py`, `research_rig/count_107.py`, `research_rig/feeds/collect_context.py`, `research_rig/feeds/news_forward.py`, `timemachine/record.py` and others. Filings and press feeds. Live and history.
- `efts.sec.gov` (SEC full-text search). The off-repo reverse split logger. Live. This search was on the earlier "known refusal, do not retry" list for agents; flagged below.
- `data.binance.vision` and its buckets. `research_rig/fetch_13.py`, `research_rig/stage_20.py`, `research_rig/repair_month_edges_16_17.py`. History files.
- `www.binance.com` announcements. `research_rig/fetch_16.py`. Notices. History.
- `coinmarketcap.com`. `research_rig/archive_18.py`, `research_rig/fetch_13.py`. Market pages. History.
- `web.archive.org`. `research_rig/feeds/announcements.py`. Archived listing pages. History.
- `en.wikipedia.org`. `research_rig/build_members_14.py`. Index member lists. History. No Wikipedia page-view call was found in the code.
- `alphagrowth.io` token unlocks API. The off-repo logger `/home/user/workspace/rig/data/unlocks_forward/logger.py`. Live.
- Context feed hosts in `research_rig/feeds/collect_context.py`: `community-api.coinmetrics.io`, `stablecoins.llama.fi`, `gateway.polymarket.us`, `gamma-api.polymarket.com`, `home.treasury.gov`, `api.fiscaldata.treasury.gov`, `cdn.cboe.com`, `www.finra.org`, `www.federalreserve.gov`.
- `data.gdeltproject.org` (`research_rig/feeds/news_77.py`), `bitcoinops.org` (`research_rig/feeds/news_forward.py`), `mba.tuck.dartmouth.edu` (`research_rig/fetch_french.py`), `www.nyse.com` calendar (`practice/forward_e07.py`).
- GitHub Actions runs the practice desk on a ten-minute cron.
- `timemachine/record.py` also names news hosts on this project's banned list. Those sites were not opened.

## The table

| Source | What we read; live or history | Verdict | Key wording (MEASURED unless marked) |
|---|---|---|---|
| Coinbase (Exchange and Advanced Trade public data) | Candles, books, product lists; loggers paused, status watcher live; logs published | BARRED WITHOUT CONSENT | [Market Data Terms, updated Aug 7 2026](https://www.coinbase.com/legal/market_data): s2 licence only "for you or your entity's personal or research purposes"; s3 bars, without "prior express written consent", passing on "Derived Works" to third parties and using Market Data to "develop, train, fine-tune, teach, validate, benchmark, or otherwise improve any ... algorithm, chatbot, agent, or other automated system ... or for any other purpose related to the research, development, or operation of artificial intelligence technologies". Express. |
| Kraken (public REST, futures, downloadable OHLCVT) | Pairs, status (live), books, history; raw books published in 09 raw | ALLOWED WITH LIMITS, wording open | [Global Terms, updated Nov 18 2026](https://www.kraken.com/legal/global-terms) s8: use "only for your own benefit"; s9 bars scraping, "bots ... scripts ... or any other forms of automation to engage in any activity on Our Content", and making Our Content available "to any third party ... in any way". [API notice](https://docs-legacy.kraken.com/api/docs/guides/global-intro/) (no date): permission needed for "any non-personal commercial use of data from publicly accessible endpoints". [Support page, updated Nov 2 2026](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data) invites command-line download and use "in code". [Historical data guide](https://docs.kraken.com/exchange/guides/general/historical-data) (no date): data "for backtesting and research". General boilerplate; no AI clause on data. |
| Binance.US (public API, history page) | Books, candles; paused; logs and raw books published | ALLOWED WITH LIMITS; Terms of Use UNKNOWN | [Terms of Use, updated Jun 5 2026](https://www.binance.us/terms-of-use): only the intro opened; the full text file returned 403 and was not retried. [Historical Market Data page](https://www.binance.us/institutions/market-history) (no date): without written consent bars commercial uses (trading services using its quotes, data feeds, services that profit from its data). [Help article, Jun 3 2026](https://support.binance.us/en/articles/9843310-introducing-historical-market-data-from-binance-us-download-for-free): useful "for backtesting and analysis". No AI clause seen. |
| Bitstamp | Prices, history | ALLOWED WITH LIMITS; US terms UNKNOWN | [API page](https://www.bitstamp.net/api/) (notes to Oct 29 2026): "Bitstamp allows the incorporation and redistribution of our exchange data for commercial purposes. This includes the right to create ratios, calculations, new original works, statistics", with commercial users told to sign a Data License Agreement. 400 requests/s, 10,000 per 10 min. The [Bitstamp USA legal page](https://www.bitstamp.net/legal/usa-inc/) showed no link to US terms here. |
| Gemini | Books (09 raw, published), history | ALLOWED WITH LIMITS | [Market Data Agreement, updated Oct 12 2025](https://www.gemini.com/legal/market-data-agreement): "receive, download, store, and copy" for "personal and/or internal use", "general informational purposes" or "analysis of prices and markets"; bars "distribute, redistribute, disseminate ... Gemini Market Data to any party for any reason" and any purpose "not expressly authorized". [API Agreement, Oct 12 2025](https://www.gemini.com/legal/api-agreement): public endpoints up to 120 requests/min. No AI or automation clause. |
| Binance Vision archive | History files | ALLOWED WITH LIMITS | [Vision Dataset Terms v1.0, updated Aug 26 2026](https://data.binance.vision/Binance_Vision-Terms_of_Use.pdf): CC BY-NC-SA 4.0; permitted "academic research ... algorithmic historical backtesting for purely personal non-production research"; bars "live proprietary trading execution" and paid signal distribution; redistributed derivative works need attribution and the same licence. |
| Binance global announcements | Notices, history | UNKNOWN | Not opened: Binance global is on the known-refusal list. |
| Upbit open API | Market list, live | UNKNOWN; leans limited | The [Open API terms](https://www.upbit.com/open_api_agreement) did not open. The [Dec 10 2026 revision notice](https://docs.upbit.com/kr/changelog/open-api-terms-revision-20261210) changes only a definition and says use, copying or distribution beyond what the Upbit terms allow is barred. STATED from an excerpt of the [2023 revision notice](https://docs.upbit.com/kr/changelog/open_api_agreement_revision): article 5 says copyright in all data belongs to Dunamu and users may not use or change it without permission. |
| Kalshi (two API hosts) | Market lists; live in the Upbit watcher | BARRED WITHOUT CONSENT | [Developer Agreement v1.1](https://assets.kalshi.com/Kalshi-Developer-Agreement.pdf) (no date): API use "expressly limited to facilitating a members own trading"; 3.1 bars "collecting, caching, aggregating, or storing data" otherwise; 3.5 bars access "for purposes of monitoring the availability, performance, or functionality of any of Kalshi's services"; 4.1 requires membership. [Data Terms](https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf) (no date): use of Kalshi Data "for any machine learning and/or artificial intelligence ... is expressly prohibited". Express. |
| Alpaca market data | Stock bars and quotes; live; logs published | ALLOWED WITH LIMITS | [Terms and Conditions](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf) (no date): use "solely for your own personal and non-commercial purposes"; no part of Content may be "republished, uploaded, posted, publicly displayed ... without Alpaca's express prior written consent". No AI clause. |
| SEC EDGAR | Filings; live and history | ALLOWED WITH LIMITS | [Developer Resources, updated Mar 10 2025](https://www.sec.gov/about/developer-resources): no more than 10 requests a second; "does not allow 'unclassified' bots". No reuse limit stated. The full-text search use in the reverse split logger should be checked against our own earlier refusal note. |
| GitHub Actions | Runs the practice desk | ALLOWED WITH LIMITS, wording open | [Terms for Additional Products, effective Aug 27 2026](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features): on GitHub-hosted runners Actions should not be used for "any other activity unrelated to the production, testing, deployment, or publication of the software project associated with the repository", nor for a disproportionate server burden; "You may only access and use GitHub Actions to develop and test your application(s)". A scheduled pretend trader can be read as running the project or as using Actions as a server. |
| Wikipedia | Member lists, history | ALLOWED WITH LIMITS | [Wikipedia:Copyrights, edited Oct 5 2026](https://en.wikipedia.org/wiki/Wikipedia:Copyrights): CC BY-SA 4.0, credit needed on redistribution. [API Usage Guidelines, Aug 26 2024](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_API_Usage_Guidelines): follow rate and User-Agent rules; no prior permission needed. |
| AlphaGrowth unlocks | Token unlocks, live | ALLOWED WITH LIMITS | [Terms, updated Nov 16 2026](https://alphagrowth.io/terms): licence to "use, display, and republish reasonable portions of its data for any lawful purpose, including in AI agent responses, research, and commercial products", with credit "Data: AlphaGrowth (alphagrowth.io)"; 60 requests/min. |
| CoinMarketCap | Market pages, history | BARRED WITHOUT CONSENT | [Terms, updated Nov 24 2025](https://coinmarketcap.com/terms/) s5.1.4 bars "scraping, robot or similar automated" access and storing Content unless expressly authorized; s4.4 personal, non-commercial use only. |
| DefiLlama | Stablecoin data, context feed | ALLOWED WITH LIMITS | [Terms, effective Jun 24 2025](https://defillama.com/terms): personal, non-commercial licence; may not "republish the data in any form without permission"; official public API allowed, other automated access barred. |
| Polymarket (gamma-api) | Markets, context feed | ALLOWED WITH LIMITS | [Terms, effective Aug 11 2026](https://polymarket.com/tos): bars "robots, crawlers ... to scrape" the Site and bars Data use by capital-markets firms; API access is named as a way of accepting the Terms. No AI clause. Polymarket US (`gateway.polymarket.us`): [terms page](https://polymarket.us/terms) showed only a sign-up offer, UNKNOWN. |
| Treasury Fiscal Data | Context feed | ALLOWED | [API documentation](https://fiscaldata.treasury.gov/api-documentation/): data "offered free, without restriction, and available to copy, adapt, redistribute, or otherwise use for non-commercial or commercial purposes". |
| GDELT | News feed | ALLOWED WITH LIMITS | [About page](https://www.gdeltproject.org/about.html): "unlimited and unrestricted use"; redistribution allowed with a citation and link. |
| Coin Metrics community API | Context feed | UNKNOWN | [Community page](https://coinmetrics.io/community-network-data/) and [API docs](https://docs.coinmetrics.io/api/v4/) state no licence. |
| Ken French data library | Factor data, history | UNKNOWN | [Data library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html) shows only a copyright line. |
| Internet Archive | Archived pages, history | UNKNOWN | [Terms page](https://archive.org/about/terms.php) needed JavaScript; only "last updated 12/31/2014" showed. |
| Cboe, FINRA, Federal Reserve, NYSE, Kraken futures, Bitcoin Optech, home.treasury.gov | Context and calendar | UNKNOWN | [Cboe legal page](https://www.cboe.com/legal/) is silent; FINRA's terms page failed to open; the others were not opened in this round. |

## Three readings for the US venues

The lead asked for three uses, each read separately. (a) is one person downloading published history and backtesting privately. (b) is publishing only summary results (no prices, no trades) in a public repo. (c) is a script polling documented public REST at the documented limits, for a private pretend-money log. On Coinbase all three hit s3's express AI and automated-system clause, and (b) also hits its derived-works clause.

Kraken. The s8 and s9 lines are general boilerplate written for the website and conflict on their face with Kraken's own API and curl instructions; there is no data-specific AI clause.

- (a) Allowed with limits. The support page tells users to download by command line and use the files "in code", and s8 allows use "for your own benefit". Open point: whether a public, Perplexity-linked project is "non-personal commercial use" under the API notice.
- (b) Not expressly barred. Kraken has no derived-works clause like Coinbase's. s9 bars making "Our Content" available to third parties, and summary statistics are arguably not Our Content. But "only for your own benefit" can be read against publishing to the public. Asking marketdata@kraken.com would settle it.
- (c) Allowed with limits on the API notice's reading (permission is needed only for non-personal commercial use). Read literally, s9's line against "scripts ... to engage in any activity on Our Content" is the risk.

Binance.US. Express wording exists only for commercial uses; the full Terms of Use did not open.

- (a) Allowed on the pages read: the help article names backtesting.
- (b) Not barred by the commercial list on the history page. The Terms of Use are UNKNOWN.
- (c) Allowed on the pages read: the [API docs](https://docs.binance.us/) (STATED from an excerpt) mark public market-data endpoints as accessible freely. The Terms of Use are UNKNOWN.

Bitstamp. Its wording is the most open of the four, and express.

- (a) Allowed.
- (b) "Statistics" and "new original works" based on exchange data are expressly contemplated, but in a passage about commercial users who sign a Data License Agreement. Non-commercial publication is not addressed, and the US terms are UNKNOWN.
- (c) Allowed at 400 requests/s and 10,000 per 10 minutes.

Gemini. The terms are specific to market data but silent on AI and automation.

- (a) Allowed: storing and analysing the data are named.
- (b) Summaries with no Gemini data in them sit outside the express ban on redistributing "Gemini Market Data". "Derived data" is not defined for ordinary users, and "any purpose not expressly authorized" is barred. That is room, not clearance.
- (c) Allowed at 120 requests/min for "personal and/or internal use" or "analysis of prices and markets".

## Where the paused loggers can move

The paused loggers are E06, E09, E10, E11 and Measurement 132.

- Candles and books. Kraken, Gemini, Bitstamp and Binance.US all offer both on public endpoints that need no key. None of the four pages read has Coinbase's AI or automated-system ban. Gemini's and Bitstamp's wording is the clearest for private use. Kraken's is open on scripts. Binance.US's full terms are UNKNOWN.
- Publishing derived pretend-trade logs in a public repo. None of the four clearly allows it for a non-commercial public project. Bitstamp's wording comes closest. Gemini and Kraken leave room for summaries with no prices, but do not clear it. Gemini, Kraken and Alpaca all bar republishing the raw data itself.
- Keeping the logs off the public repo, or publishing only summaries and asking the venue in writing, removes most of the doubt.

## Flags found on the way

- Raw order book samples from Binance.US, Gemini and Kraken are published in `docs/research/09_raw/orderbook_snapshots.jsonl`. Gemini's agreement bars redistributing its market data "to any party for any reason"; Kraken's s9 bars making Our Content available to third parties. This needs a ruling.
- The off-repo Upbit watcher polls Kalshi's margin market list live. Kalshi's Developer Agreement limits API use to a member's own trading and bars monitoring "availability ... or functionality" of its services. This reads as barred.
- The off-repo status watcher still polls Coinbase's product list. Whether a product-status watcher used for research falls under s3's automated-system clause is open, but s2 limits even the allowed use to personal or research purposes.
- Published practice logs from Alpaca data (for example `practice/forward/E07_log.json`) may contain prices. Alpaca's terms bar republishing Content without consent. The files were not opened here.
- CoinMarketCap history was gathered by script against an express no-scraping clause.
- The reverse split logger uses SEC full-text search, which an earlier brief listed as a refusal for agents.
