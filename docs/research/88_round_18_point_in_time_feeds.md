# Round 18: Point-in-Time Information Feeds for Time Machine Scouts (2021 to 2026)

Date: 2026-11-26 05:17 UTC. Reading and source audit only; no bulk collection was run and no market or feed data was stored in the repo. Claims are labeled MEASURED (verified from primary docs, sample responses, or repo audits), STATED (documented by the provider or a published paper), or UNKNOWN (not published).

## Lead-Agent Rulings

- Build source 2 first (Wayback-verified exchange announcements across Binance, Bybit, OKX, Upbit, Kraken, and Coinbase), assigned to `context_feed_builder` (queue row 77).
- Sources 1 and 3 (Common Crawl News `CC-NEWS` and GDELT 2.0 raw 15-minute files) wait on disk space because the research machine has about 2 GiB of disk free (queue row 78).
- The leak and legal traps documented below go directly into the time machine feed rules so no future builder or scout ingests retroactively edited, rescaled, or legally restricted archives.

## Already Built in the Time Machine (Not Repeated Below)

- Prices, funding, and open interest: `timemachine/tape.py` and `timemachine/tm06.py` already serve strict as-of spot and perpetual bars, funding, and open interest.
- Alpaca news tape (`timemachine/tape.py`, `docs/research/45_attention_feed_measured.md`): 11,726 articles from 2026-04-29 to 2026-11-24 (`created`/`updated`), with 52 coin-title matches across 8 of 23 coins.
- Attention store (`timemachine/attention.py`, `docs/research/45_attention_feed_measured.md`): Wikipedia daily page views (17 of 23 coins from 2025-01-01, `+36h` gate; 422 of 693 dump files had later `Last-Modified` timestamps), Reddit/Arctic Shift daily subreddit counts (15 of 23 coins, capture-only), plus failed checks on GDELT DOC 2.0 (HTTP 502/429) and Google Trends (HTTP 429).
- Context collector (`research_rig/feeds/SOURCES.md`, `docs/research/19_information_feeds.md`): live terms already documented for SEC EDGAR, Coin Metrics Community (CC BY-NC 4.0), DefiLlama stablecoins, Federal Reserve FOMC calendar, FRED (AI and storage bans in Sections k and l), and Wikimedia CC0.

## Ranked Table of 14 Candidate Sources (Usefulness for Small/Mid Coins vs Leak Risk)

| Rank | Source | Date range | Timestamp trust and editability | Automated reading and off-repo storage terms | Approximate size (2021-2026) | Primary future-leak risk | Usefulness (small/mid coins) | Leak risk |
|---|---|---|---|---|---|---|---|---|
| 1 | Common Crawl News (`CC-NEWS` WARC) | Aug 2016 to present | HIGH: immutable `WARC-Date` capture second; captures text as seen then | Common Crawl Terms of Use (free AWS S3); original publisher copyright applies; no redistribution | ~180 TB raw WARC (2016-2026); ~1.65 TB processed Parquet (2021-2025) | Low if gated on `WARC-Date`; high if using unverified publisher HTML dates | HIGH (broad crypto and mainstream articles) | LOW |
| 2 | Wayback Machine CDX of exchange notices (Binance, Coinbase, Kraken, Upbit, Bybit, OKX) | 1996 to present (exchanges 2017-2026) | HIGH: immutable CDX `timestamp` and SHA-1 `digest` of captured HTML | Internet Archive CDX API (~1 req/s; tightened 429 limits Sep 2026); original site ToS still applies | Small: ~50 MB to 2 GB for 6 exchange notice sections | Low on captured HTML; missing captures create blind spots; JS SPAs (Binance/OKX/Upbit) often capture shells | VERY HIGH (listings, delistings, halts) | LOW |
| 3 | GDELT 2.0 Raw 15-Min Files / BigQuery GKG and Mentions | Feb 19, 2015 to present (15-min batches) | HIGH: immutable 15-min batch timestamp (`masterfilelist.txt` / `_PARTITIONTIME`) | Free "unlimited and unrestricted use for any academic, commercial, or governmental use" with attribution | ~470 MB/day zipped raw GKG (~1 TB for 2021-2026); BigQuery GKG ~3.6 TB (1 TiB/mo free query) | Low if using batch fields only; HIGH if live-fetching cited URLs today (post-pub edits) | HIGH (global news volume, tone, entities) | LOW |
| 4 | Exchange official announcement archives and RSS (Binance, Bybit, OKX, Upbit, Kraken, Coinbase) | ~2018-2026 (varies; Coinbase live `/products` only) | MEDIUM: official `releaseDate` / `publishTime`, but notices can be edited or deleted silently | Public APIs (Bybit V5, OKX V5, Binance CMS, Upbit notices, Kraken RSS); Kraken/Coinbase blogs block bots; check venue ToS | Tiny: ~30 to 100 MB JSON/text (~37k notices across 10 venues) | MEDIUM-HIGH: silent post-hoc edits (e.g., postponed listing times), deleted notices, missing delisted coins | VERY HIGH (fastest small-coin catalyst) | MEDIUM-HIGH |
| 5 | On-chain data (BigQuery public blockchain sets / public nodes) | Genesis to present (BTC, ETH, SOL, Polygon, Arb, OP, Avax, Tron) | VERY HIGH: immutable block height and block timestamp (after finality) | Google Cloud Public Datasets (CC0 / AS IS); 1 TiB/mo free BigQuery query tier | Multi-TB per chain (`crypto_ethereum` ~7.9 TB, Polygon logs ~32.7 TB); filtered daily coin stats ~1-10 GB | VERY LOW: only chain reorgs (minutes) or using `tokens_latest` / current address-label tables (which leak future labels) | MEDIUM (DEX volume, whale transfers, mints) | VERY LOW (raw) / HIGH (labels) |
| 6 | GitHub commit and release activity (GH Archive) | Feb 2011 to present (Events API Jan 2015+) | HIGH: immutable hourly `YYYY-MM-DD-H.json.gz` event log | GH Archive MIT / CC-BY-4.0 (code/site); public GitHub timeline; 1 TiB/mo BigQuery free tier | ~3 TB total uncompressed; ~5 GB/mo BigQuery scan; crypto-repo subset ~1-5 GB | LOW on event stream; MEDIUM on repo-to-coin mapping (must not use future renames or survivor-only repo lists) | MEDIUM (mainnet launches, urgent patches) | LOW-MEDIUM |
| 7 | SEC and CFTC press releases | SEC 1997-present; CFTC multi-decade | MEDIUM-HIGH: official release date and ID; date-only on index tables (no minute clock) | US government public domain (`17 USC 105`); SEC 10 req/s + User-Agent; CFTC disabled RSS Oct 2026 | Tiny: ~50 to 200 MB HTML/text | LOW-MEDIUM: date-only tables leak intraday timing unless gated to next UTC day (00:00 UTC +1d) | MEDIUM (enforcement, ETF approvals, delisting risk) | LOW-MEDIUM |
| 8 | Fed calendar and FOMC statements (`federalreserve.gov`) | 1936 to 2027 (2021-2027 calendar live) | VERY HIGH: fixed 14:00 ET release clock; scheduled dates known a year ahead | Public domain per Board disclaimer (attribution requested). Avoid FRED/ALFRED API (bans AI and DB storage) | Tiny: <20 MB | VERY LOW: statements immutable once released (unscheduled emergency cuts rare and timestamped) | LOW-MEDIUM (macro regime for all coins) | VERY LOW |
| 9 | Hacker News (Algolia API / Firebase / `open-index` Parquet) | 2006 to present (~49M items) | MIXED: `created_at_i` is reliable, but `points`, `num_comments`, `front_page` are TODAY'S final totals | Free, keyless; Algolia 10k req/hr (1,000 hits/query); YC site ToS bars commercial exploitation; HF mirror ODC-By 1.0 | ~12.2 GB Parquet (all items); crypto subset <200 MB | HIGH if filtering on `points`/`front_page` (leaks post-creation virality); LOW if using raw `created_at_i` title/URL only | LOW-MEDIUM (dev/protocol news, hacks) | HIGH (scores) / LOW (raw) |
| 10 | CoinGecko and CoinMarketCap historical category/trending pages via Wayback | CMC snapshots Apr 2013+; CG categories/trending via Wayback 2021+ | HIGH on Wayback captures; LIVE endpoints have NO historical vintages | CMC/CG terms restrict automated extraction; full CG/CMC historical APIs are paid ($79-$129/mo) and lack vintage categories | ~500 MB to 5 GB HTML snapshots | VERY HIGH on live endpoints (retroactive category tags like "AI" or "Meme" and survivorship); MEDIUM on Wayback (sparse capture cadence) | HIGH (what narratives were hot then) | HIGH (live) / MEDIUM (Wayback) |
| 11 | Wikipedia page views (2021-2024 extension of Doc 45) | 2015 to present (Doc 45 already holds 2025-2026) | MEDIUM: daily UTC user views; Doc 45 proved 422/693 dump files in 2025-2026 had late `Last-Modified` dates | CC0 licence; 200 req/min with User-Agent; bulk `pageview_complete` dumps | ~100 MB/day compressed dumps; 23-coin API extract <10 MB | MEDIUM: reprocessing alters past counts; missing/renamed pages for new coins (Doc 45: 6/23 coins unmapped) | LOW (lagging retail attention; Doc 45 showed no lead) | MEDIUM |
| 12 | DefiLlama historical TVL and stablecoin supply | Sep 2017 to present (hourly/daily) | LOW for historical backtests: maintainer confirms routine retroactive backfills | Free public API (`api.llama.fi`, `stablecoins.llama.fi`); terms clauses 7-8 personal/non-commercial, no republishing | ~500 MB to 2 GB JSON across protocols/chains | VERY HIGH: adding a protocol backfills its past TVL and rewrites historical chain TVL; methodology fixes overwrite history | MEDIUM (DeFi/L1/L2 inflows, stablecoin growth) | VERY HIGH |
| 13 | Reddit public dumps (Pushshift / Arctic Shift / Academic Torrents) | 2005 to Aug/Sep 2026 (Arctic Shift) | LOW-MEDIUM: `created_utc` reliable, but archives merge later edits/removals and final `score` | HIGH LEGAL/ToS RISK: Pushshift mod-only (May 2023); Academic Torrents taken down Jul 2026; Reddit API closes Mar 2027; Reddit sued data firms in 2025 | ~3.8 TB full 2005-2025 compressed (~261 GB Parquet on HF); crypto subreddits ~20-50 GB | HIGH: final upvote scores, deleted-post survivorship, merged edits, plus ToS/legal block | MEDIUM-HIGH (retail hype on small coins) | HIGH (+ Legal block) |
| 14 | Google Trends | 2004 to present | VERY LOW: sampled twice daily and rescaled 0-100 to query window maximum | No open historical API (Alpha gated); public endpoint returned HTTP 429 in Doc 45 | Tiny (<10 MB) | EXTREME: future search spikes compress past values; repeated pulls on different days return different numbers | LOW-MEDIUM (blocked by leak + 429) | EXTREME |

## The Three No-Future Checks

### Build First (Queue Row 77): Wayback-Verified Exchange Announcement Feed (Binance, Bybit, OKX, Upbit, Kraken, Coinbase)

- For every 2021 to 2026 historical announcement, require an independent capture anchor: `known_at_utc = earliest_wayback_capture_ts` (or earliest `CC-NEWS` / GDELT 15-minute mention of that exact announcement URL/title). Do not trust an unanchored live exchange `releaseDate` alone.
- Store the archived text from the earliest Wayback capture (not today's live page) and record the CDX `digest` so post-hoc edits (such as postponed listing times) cannot enter the scout packet.
- Automated test: compare 50 sampled historical notices against their live exchange pages to measure edit/deletion rates, and assert in `timemachine/test_tape.py` that every served notice satisfies `capture_ts <= known_at_utc <= now_utc`.

### Queued on Disk Space (Queue Row 78): Common Crawl News (`CC-NEWS`)

- Stamp every stored row with `warc_date_utc` (from the WARC header) and `known_at_utc = max(warc_date_utc, parsed_pub_utc) + 5 minutes`. Never serve an article using `parsed_pub_utc` alone.
- Drop any record where `parsed_pub_utc` is more than 24 hours after `warc_date_utc` (malformed clock) or where the extracted body fails a SHA-256 round-trip check against the archived WARC record ID.
- Automated test: feed 200 random simulated wakes `now_utc` and assert `max(warc_date_utc) < now_utc`, `max(known_at_utc) <= now_utc`, and zero future-year strings (e.g., `"2025"` or `"2026"` inside a 2023 wake packet).

### Queued on Disk Space (Queue Row 78): GDELT 2.0 Raw 15-Minute GKG and Mentions Index

- Derive `known_at_utc` strictly from the immutable 15-minute batch filename timestamp (`YYYYMMDDHHMMSS.gkg.csv.zip`) plus 15 minutes (or BigQuery `_PARTITIONTIME + 15 minutes`), never from article-internal dates.
- Never re-fetch live article URLs from `DocumentIdentifier`; serve scouts only the fields captured in that 15-minute batch (source domain, URL slug, disambiguated coin match, themes, tone).
- Automated test: verify every ingested 15-minute file's MD5/SHA-256 against `masterfilelist.txt`, confirm zero rows have `batch_ts > now_utc`, and run a planted-future injection test confirming any row stamped `now_utc + 1 second` is withheld.

## Feed Rules and Leak Trap List (Mandatory for All Time Machine Feeds)

- DefiLlama historical TVL and stablecoins are banned for historical replay (forward-log only): maintainer `0xngmi` confirmed routine retroactive backfills when new protocols are listed or adapters are fixed, rewriting past chain TVL ([DefiLlama-Adapters Discussion #6593](https://github.com/DefiLlama/DefiLlama-Adapters/discussions/6593)).
- Third-party Reddit dumps (Pushshift, Arctic Shift, Academic Torrents) are banned for historical replay: Pushshift is moderator-only (May 2023), Watchful1 removed the 2005 to 2025 Academic Torrents dumps on July 24, 2026 at Reddit's request ([ChatterAPI, 2026](https://chatterapi.com/blog/pushshift-vs-pullpush-vs-arctic-shift)), Reddit's public Data API closes March 2027 ([FetchLayer, 2026](https://fetchlayer.dev/blog/pushshift-alternative)), Reddit sued data firms in 2025 ([Think-Pol, 2026](https://think-pol.com/blogs/reddit-archive-api)), and Arctic Shift merges later edits, deletions, and final upvote scores.
- Google Trends is banned for historical replay: sampled twice daily and rescaled 0 to 100 against the query window maximum, injecting future spikes into past dates ([Spatial Demography, 2026](https://link.springer.com/10.1007/s40980-026-00164-8); [arXiv:2504.07032](https://arxiv.org/html/2504.07032v1)).
- Hacker News `points`, `num_comments`, and `front_page` fields are banned in historical replay because they reflect today's final totals, leaking post-creation virality; only raw `created_at_i` titles/URLs are leak-free.
- Live CoinGecko and CoinMarketCap category/trending endpoints are banned for historical replay because today's narrative tags ("AI", "RWA", "Meme") are applied retroactively and dead coins are dropped.
- Live exchange announcement archives cannot be trusted unanchored because exchanges silently edit listing times and delete revoked notices; historical notices require a Wayback CDX or independent capture anchor.
- BigQuery blockchain `tokens_latest` and modern exchange hot-wallet label tables are banned in historical replay; only immutable block/log/transfer fields may be used.
- Date-only SEC and CFTC press release index tables must be gated at `release_date + 1 day 00:00 UTC` unless cross-anchored to an exact intraday capture; CFTC disabled all RSS feeds as of October 2026 ([CFTC RSS](https://www.cftc.gov/RSS/index.htm)).
- FRED/ALFRED API is banned for scout feeds and off-repo databases per `docs/research/19_information_feeds.md` (Sections k and l ban AI/ML use and storage); read FOMC calendars and statements directly from `federalreserve.gov` (public domain).

## Source-by-Source Audit (Dates, Timestamps, Terms, Size, and Leak Modes)

### 1. Common Crawl News (`CC-NEWS`)
- Contents: Full raw HTML of news articles captured continuously from thousands of global and crypto newsrooms (`s3://commoncrawl/crawl-data/CC-NEWS/`).
- Dates: August 26, 2016 to present, released daily as WARC files ([Common Crawl Blog](https://commoncrawl.org/blog/news-dataset-available): "WARC files are released on a daily basis, identifiable by file name prefix which includes year and month. We provide lists of the published WARC files, organized by year and month from 2016 to-date.").
- Timestamp trust and editability: MEASURED/STATED: Every WARC record carries an immutable `WARC-Date` header stamped at capture time; the captured HTML cannot be edited later. A 2026 index paper ([Infini-News, arXiv:2605.18337](https://arxiv.org/html/2605.18337)) extracted 1.37 billion articles across 135,144 hostnames from August 2016 through April 2026.
- Terms and storage: Free to download from AWS S3 under [Common Crawl Terms of Use](https://docs.rcac.purdue.edu/datasets/ai/commoncrawl/): "Users of the Common Crawl dataset must comply with all applicable laws and respect the intellectual property and privacy rights of original content owners." Private off-repo research filtering is standard; never redistribute raw article text. (The pre-processed `Infini-News` HuggingFace corpus is gated for non-commercial academic use only.)
- Size: ~180 TB raw compressed WARC (2016 to 2026); processed 2021 to 2025 English/multilingual Parquet is 1.65 TB (~242 to 378 GB/year per [Infini-News README](https://huggingface.co/datasets/ruggsea/infini-news-corpus/blob/eb61f32f5164be04593258a32b0370eda2908e6b/README.md)); filtering by crypto domains and coin names during streaming yields <20 GB.
- Future-leak risk: LOW if strictly gated on `WARC-Date` (capture time). Leaks only if a parser trusts a page's self-reported `datePublished` metadata when an article was actually updated later.

### 2. Wayback Machine Captures of Exchange Announcement Pages
- Contents: Point-in-time HTML snapshots of listing, delisting, monitoring-tag, and maintenance pages for Binance, Coinbase, Kraken, Upbit, Bybit, and OKX via the Wayback CDX API (web.archive.org CDX endpoint).
- Dates: Internet Archive spans 1996 to present; crypto exchange announcement sections span ~2017 to 2026.
- Timestamp trust and editability: HIGH: CDX returns an immutable 14-digit capture `timestamp` and content `digest` ([Wayback OSINT Guide, 2026](https://maxintel.org/wayback-osint-guide-2026.html)). Text inside an archived snapshot cannot be altered by later exchange edits.
- Terms and storage: Free, keyless CDX and Memento APIs. Rate limits tightened sharply in 2024 to 2026: CDX averages ~60 requests/minute (~1 req/s recommended), and ignoring HTTP 429 triggers escalating IP firewall blocks ([Archivarix, 2026](https://archivarix.com/en/blog/webarchive-2026/): "The CDX API allows an average of 60 requests per minute. When the limit is exceeded, the server responds with a 429 (Too Many Requests) code."). On Sept 15, 2026, Wayback Director Mark Graham confirmed added 429 protections against automated traffic ([Ganglani, 2026](https://www.kunalganglani.com/blog/wayback-machine-rate-limiting-mini-wayback): "internal archiving of third-party content can still violate ToS even if it's technically possible").
- Size: Small (~50 MB to 2 GB for six exchange announcement sections across 2021 to 2026).
- Future-leak risk: LOW for timestamps, but two operational traps exist: (1) JavaScript-rendered support centers (Binance, OKX, Upbit) often archive empty shell pages unless the underlying JSON API endpoint was also captured, and (2) irregular capture cadence means a listing notice may be captured hours after publication (requiring gating on capture time, not claimed publish time).

### 3. GDELT 2.0 Event and Article Index (Raw 15-Minute Files and BigQuery)
- Contents: Every 15 minutes, GDELT 2.0 publishes Events, Mentions, and Global Knowledge Graph (GKG) tables indexing global news URLs, themes, organizations, persons, locations, and tone across 65 languages ([GDELT Data](https://gdeltproject.org/data.html)). Note: Doc 45 tested the GDELT DOC 2.0 API (which is rolling 3 months only and returned HTTP 502/429); the 2021 to 2026 historical route is the raw 15-minute bulk files (`masterfilelist.txt`) or partitioned BigQuery tables (`gdelt-bq.gdeltv2.gkg_partitioned`).
- Dates: February 19, 2015 to present, updated every 15 minutes ([py-gdelt Data Sources](https://rbozydar.github.io/py-gdelt/getting-started/data-sources/)).
- Timestamp trust and editability: HIGH: Each 15-minute zip file is an immutable append-only batch timestamped at ingest (`DATE` / `_PARTITIONTIME`).
- Terms and storage: MEASURED in Doc 19: "available for unlimited and unrestricted use for any academic, commercial, or governmental use" without fee, requiring attribution and link-back to `gdeltproject.org` ([GDELT About](https://www.gdeltproject.org/about.html)). BigQuery grants 1 TiB/month free query processing (`_PARTITIONTIME` filter mandatory to avoid scanning the full 3.6 TB GKG table).
- Size: ~470 MB/day zipped raw GKG (~1 TB for 2021 to 2026); BigQuery GKG is ~3.6 TB, Mentions ~104 GB, Events ~63 GB ([GDELT BigQuery Announcement](https://blog.gdeltproject.org/announcing-partitioned-gdelt-bigquery-tables/)). Filtered crypto Parquet is ~1 to 5 GB.
- Future-leak risk: LOW if scouts read only the fields stored inside the 15-minute batch (URL slug, source domain, themes, organizations, tone). HIGH if a pipeline re-fetches live article URLs today, which returns edited pages and suffers link rot.

### 4. Exchange Official Announcement Archives and RSS
- Contents: Official listing, delisting, margin/perp launch, monitoring tag, contract swap, and wallet-maintenance notices from Binance (support CMS API), Bybit (V5 announcements API), OKX (V5 announcements API), Upbit (public notice API), Kraken (`Asset Listings` blog RSS), and Coinbase (no official historical listings feed; `/products` snapshot diff only) ([CEXReady, 2026](https://cexready.com/new-listings/); [Apify Exchange Monitor](https://apify.com/mrdoe/exchange-listing-monitor)).
- Dates: ~2018 to 2026 on Binance/Upbit/Bybit/OKX archives; Coinbase `/products` is current-only (no backfill).
- Timestamp trust and editability: MEDIUM: Notices carry official UTC release timestamps, but exchanges routinely edit notices in place (e.g., postponing a listing time, adding a disclaimer, or deleting canceled listings) without preserving a public revision log.
- Terms and storage: Public unauthenticated endpoints for Bybit V5, OKX V5, Binance CMS, and Upbit notices; Kraken and Coinbase blogs actively block automated clients ([Apify Exchange Monitor](https://apify.com/mrdoe/exchange-listing-monitor): "Kraken and Coinbase blog: Block automated access"). Kraken Global Terms also bar automated content extraction (`research_rig/feeds/SOURCES.md`).
- Size: Tiny (~30 to 100 MB across all major exchanges; [Tokenearly](https://tokenearly.com/en/announcements) reports 36,896 archived notices across 10+ exchanges).
- Future-leak risk: MEDIUM-HIGH: Silent edits to notice text and deletion of revoked/failed listings create survivorship and look-ahead leaks unless cross-checked against Wayback Machine captures or forward-logged in real time (as done for Upbit in Queue row 49).

### 5. On-Chain Data (BigQuery Public Blockchain Datasets and Public Nodes)
- Contents: Full block headers, transactions, logs, receipts, ERC-20/SPL token transfers, and decoded smart-contract events for Bitcoin, Ethereum (`goog_blockchain_ethereum_mainnet_us` and `crypto_ethereum`), Solana (`crypto_solana_mainnet_us`), Polygon, Arbitrum, Optimism, Avalanche, Cronos, and TRON ([BigQuery Blockchain Skills, 2026](https://github.com/subsquid-labs/bigquery-blockchain-skills/blob/main/bigquery-blockchain-datasets/SKILL.md)).
- Dates: Genesis block of each chain to present, updated near real time.
- Timestamp trust and editability: VERY HIGH: Cryptographically ordered by `block_number` and `block_timestamp`; immutable once finalized (minutes).
- Terms and storage: Hosted in Google Cloud Public Datasets (`CC0` / provided "AS IS" without warranty); BigQuery includes 1 TiB/month free query processing ([Google Cloud Marketplace](https://console.cloud.google.com/marketplace/product/bitcoin/crypto-bitcoin)).
- Size: Multi-terabyte raw tables (`crypto_ethereum` ~7.9 TB, `goog_blockchain_ethereum_mainnet_us.accounts_state` 53.5 TB, Polygon `logs` 32.7 TB). Always prune by both `block_number` and `block_timestamp`; aggregated hourly/daily coin metrics (DEX swaps, active senders, large transfers) are ~1 to 10 GB.
- Future-leak risk: VERY LOW for raw block/transfer counts. HIGH if a query joins against mutable "latest" metadata or address-label tables (`tokens_latest`, or today's CEX hot-wallet labels), which retroactively identify wallets that were anonymous in 2021 to 2024.

### 6. GitHub Commit and Release Activity (GH Archive)
- Contents: Public GitHub timeline events (`PushEvent`, `ReleaseEvent`, `PullRequestEvent`, `IssuesEvent`, `WatchEvent`, `ForkEvent`) for open-source coin repositories ([GH Archive](https://www.gharchive.org/)).
- Dates: February 12, 2011 to present; Events API format from January 1, 2015 to present.
- Timestamp trust and editability: HIGH: Captured hourly into immutable `YYYY-MM-DD-H.json.gz` files and hourly BigQuery tables (`githubarchive.day.YYYYMMDD`). Later repo deletions or force-pushes do not erase past hourly archives.
- Terms and storage: GH Archive code/docs MIT and website CC-BY-4.0; underlying events are public GitHub timeline metadata; BigQuery 1 TiB/month free tier ([GH Archive GitHub](https://github.com/igrigorik/gharchive.org)).
- Size: ~3 TB uncompressed total; querying one month in BigQuery scans ~5 GB ([gharchive-bigquery-examples](https://github.com/davelester/gharchive-bigquery-examples/blob/main/README.md)); filtering to crypto repos yields ~1 to 5 GB for 2021 to 2026.
- Future-leak risk: LOW on the event stream itself. MEDIUM on the coin-to-repo mapping: using today's repo list drops dead/rugged projects that deleted repos and uses renamed org names (`repo_id` must be pinned).

### 7. SEC and CFTC Press Releases
- Contents: Official enforcement actions (crypto fraud, unregistered securities charges), ETF approvals/delays, no-action letters, and rulemaking notices ([SEC Press Releases](https://www.sec.gov/newsroom/press-releases); [CFTC Press Releases](https://www.cftc.gov/PressRoom/PressReleases)).
- Dates: SEC 1997 to present (with RSS feed); CFTC multi-decade HTML archive (note: [CFTC RSS page](https://www.cftc.gov/RSS/index.htm) states "As of October 2026, the CFTC has temporarily disabled all RSS feeds for the below topics.").
- Timestamp trust and editability: MEDIUM-HIGH: Official release dates and sequential release numbers (`2026-117`, `9331-26`), rarely altered (corrections noted). However, historical index tables list calendar date only, not exact publication minute.
- Terms and storage: US federal government works in the public domain (`17 USC 105`), free to access and store off repo; SEC enforces 10 requests/second with a declared `User-Agent` contact header (`research_rig/feeds/SOURCES.md`).
- Size: Tiny (~50 to 200 MB total for 2021 to 2026).
- Future-leak risk: LOW-MEDIUM: Date-only indexing leaks intraday timing if fed at 00:00 UTC on the release date; must gate historical items at `release_date + 1 day 00:00 UTC` (or cross-check exact minute in `CC-NEWS` / GDELT).

### 8. Federal Reserve Calendar and FOMC Statements
- Contents: Scheduled FOMC meeting dates, 14:00 ET policy statements, and minutes ([Federal Reserve FOMC Calendars](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)).
- Dates: 1936 to 2027 (2021 to 2027 live on the main calendar page).
- Timestamp trust and editability: VERY HIGH: Scheduled dates are published a year in advance, and statements release at 14:00 ET sharp; immutable once published.
- Terms and storage: MEASURED in `research_rig/feeds/SOURCES.md`: Board disclaimer states its information "is in the public domain" unless otherwise indicated, with attribution requested. Do NOT use the FRED/ALFRED API for scout feeds or off-repo databases, because `docs/research/19_information_feeds.md` already measured that FRED terms Section (k) bans AI/ML use and Section (l) bans storing or archiving FRED content.
- Size: Tiny (<20 MB).
- Future-leak risk: VERY LOW.

### 9. Hacker News (Algolia API, Firebase v0, and `open-index` Mirror)
- Contents: Tech and crypto stories, Show HN launches, exploit/hack disclosures, and comments.
- Dates: 2006 to present (~49 million items).
- Timestamp trust and editability: MIXED: `created_at_i` (Unix timestamp) is accurate, but `points`, `num_comments`, `front_page` tags, and `dead`/`deleted` flags reflect TODAY'S final state, not what existed at `created_at_i`. Moderators also edit story titles after submission.
- Terms and storage: Official Firebase v0 API (no rate limit) and Algolia HN Search API (10,000 req/hr/IP, 1,000 hits/query cap) are free and keyless, but no data license is published and Y Combinator's site Terms of Use bar commercial exploitation ([AgentAPIList, 2026](https://agentapilist.com/agent-tools/hacker-news-api/)). Community mirror open-index hacker-news on HuggingFace is ODC-By 1.0 ([windex hn-source.md](https://github.com/stevemurr/windex/blob/main/docs/hn-source.md)).
- Size: 12.2 GB Parquet for all 48.87M items; crypto-filtered subset <200 MB.
- Future-leak risk: HIGH if filtering or ranking by `points`, `num_comments`, or `front_page` (leaks whether a post later went viral). LOW only if scouts see raw unranked `created_at_i` titles/URLs, which is noisy.

### 10. CoinGecko and CoinMarketCap Historical Category and Trending Pages (via Archive Captures)
- Contents: CoinMarketCap weekly historical market-cap snapshots (CoinMarketCap historical archive), plus Wayback captures of CoinGecko trending-categories and charts/categories pages and CMC trending pages.
- Dates: CMC weekly snapshots start April 28, 2013 to present ([CoinMarketCap Historical](https://coinmarketcap.com/historical/)); CoinGecko category/trending pages in Wayback cover ~2021 to 2026 intermittently.
- Timestamp trust and editability: HIGH on Wayback captures (immutable capture time), ZERO on live CoinGecko/CMC category APIs (which apply today's category tags retroactively to 2021).
- Terms and storage: Free CoinGecko/CMC API tiers give only 1 year of price history and no historical trending/category endpoints; paid history plans ($79 to $129/mo) still require attribution and lack vintage category snapshots ([Coinranking, 2026](https://coinranking.com/blog/best-historical-crypto-data-apis/)). Automated reading of live HTML pages violates site terms; Wayback captures still carry third-party ToS risk.
- Size: ~500 MB to 5 GB for HTML snapshots across 2021 to 2026.
- Future-leak risk: VERY HIGH on live endpoints (retroactive narrative tags like "AI" or "RWA" and dead-coin survivorship bias); MEDIUM on Wayback captures (sparse, uneven capture timestamps).

### 11. Wikipedia Page Views (2021 to 2024 Extension of Doc 45)
- Contents: Daily UTC user page views per coin article (`docs/research/45_attention_feed_measured.md` already stores 2025 to 2026 for 17 of 23 coins in `timemachine/attention.py`).
- Dates: 2015 to present via Wikimedia REST API and `pageview_complete` dumps.
- Timestamp trust and editability: MEDIUM: `docs/research/45_attention_feed_measured.md` measured that 422 of 693 daily dump files in 2025 to 2026 carried HTTP `Last-Modified` timestamps later than the `+36h` availability gate, showing routine reprocessing that prevents proving original vintage.
- Terms and storage: CC0 license; 200 req/min with compliant User-Agent (already verified in `docs/research/19_information_feeds.md`).
- Size: <10 MB for a 50-coin API extract (2021 to 2026).
- Future-leak risk: MEDIUM (reprocessing, article renames/redirects, and unmapped newer coins: 6 of 23 coins had no Wikipedia article in Doc 45). Low usefulness: Doc 45 already measured zero lead over price.

### 12. DefiLlama Historical TVL and Stablecoin Supply
- Contents: Daily/hourly protocol TVL, chain TVL, stablecoin circulating supply, DEX volumes, and fees (`api.llama.fi`, `stablecoins.llama.fi`).
- Dates: September 2017 to present (meaningful scale post-2019).
- Timestamp trust and editability: LOW FOR HISTORICAL REPLAY: DefiLlama has no point-in-time vintage API and routinely overwrites history. Maintainer `0xngmi` explicitly documented this ([DefiLlama-Adapters Discussion #6593](https://github.com/DefiLlama/DefiLlama-Adapters/discussions/6593)): "We change data (TVL, volume, fees...) retroactively to improve it's accuracy in the following cases: When listing a new protocol we fill in it's historical data... Given that chain TVL is calculated as the sum of TVL of all protocols in the chain, this means that all these protocols being added or updated will lead to changes in historical chain TVL, so you can expect historical data to be changing regularly."
- Terms and storage: MEASURED in `research_rig/feeds/SOURCES.md`: Terms clauses 7 and 8 grant personal, non-commercial use on the official public API only and bar copying or republishing the data without permission.
- Size: ~500 MB to 2 GB JSON across protocols and chains.
- Future-leak risk: VERY HIGH: Backfilling newly listed surviving protocols inflates historical chain TVL and protocol rankings with future knowledge. Usable honestly only if forward-logged daily from today onward.

### 13. Reddit Public Dumps (Pushshift, Arctic Shift, Academic Torrents)
- Contents: Historical Reddit submissions and comments across crypto subreddits (CryptoCurrency, solana, ethereum, and coin subs).
- Dates: 2005 through August/September 2026 via Arctic Shift monthly dumps.
- Timestamp trust and editability: LOW-MEDIUM: `created_utc` is accurate, but as `docs/research/45_attention_feed_measured.md` noted, Arctic Shift merges later edits, removals, and final post scores.
- Terms and legal status (2026): SEVERE LEGAL/ToS BLOCK. Pushshift has been restricted to verified Reddit moderators for moderation only since May 2023 ([ChatterAPI, 2026](https://chatterapi.com/blog/pushshift-vs-pullpush-vs-arctic-shift)). On July 24, 2026, Watchful1 removed the 2005 to 2025 Academic Torrents dumps at Reddit's request ([ChatterAPI, 2026](https://chatterapi.com/blog/pushshift-vs-pullpush-vs-arctic-shift): "Upon reddit's request, I am taking down my academic torrents pages"). Reddit's public Data API stopped new app registrations October 31, 2026 and closes March 2027 ([FetchLayer, 2026](https://fetchlayer.dev/blog/pushshift-alternative)). Reddit actively enforces its Data API Terms and User Agreement, having sued Anthropic (June 2025) and Perplexity, Oxylabs, AWMProxy, and SerpApi (October 2025) ([Think-Pol, 2026](https://think-pol.com/blogs/reddit-archive-api)). Research use outside "Reddit for Researchers" (accredited universities, 6-month delay, non-commercial) violates Reddit policy.
- Size: ~3.8 TB full 2005 to 2025 compressed (~261 GB Parquet on HuggingFace); crypto subreddits ~20 to 50 GB.
- Future-leak risk: HIGH (final upvote scores, deleted-post survivorship, merged edits) combined with clear ToS/legal exposure. Do not build on third-party Reddit dumps.

### 14. Google Trends
- Contents: Normalized 0 to 100 relative search interest (`RSV`) for coin names and topics.
- Dates: 2004 to present (Alpha API gated; public endpoint returned HTTP 429 in `docs/research/45_attention_feed_measured.md`).
- Timestamp trust and editability: VERY LOW: Google draws fresh ad-hoc samples twice per day and normalizes every point to the maximum value inside the requested window ([Spatial Demography, 2026](https://link.springer.com/10.1007/s40980-026-00164-8): "research has shown that executing the exact same query on different days can result in different RSV data"; [arXiv:2504.07032](https://arxiv.org/html/2504.07032v1): "Retrospective application of these techniques could introduce future-looking information").
- Terms and storage: No open historical API license; public endpoint blocks automated requests (429).
- Size: Tiny (<10 MB).
- Future-leak risk: EXTREME. Unusable for historical 2021 to 2026 time-machine replay.
