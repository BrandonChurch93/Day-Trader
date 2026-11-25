# 45. Coin attention counts: what can be collected with honest dates, and whether they lead price

Status: measured 2026-11-25 by a helper, checked by the builder. Not a counted test. The store is on the research machine and is not in the repo; `timemachine/attention.py` reads it for a trader as of a simulated time.

## In plain words

- The owner's method picks "the hot coins people are targeting". This page asks whether a free, dated count of attention exists that a time-machine trader could have seen at the time.
- Usable: Wikipedia page views for 17 of 23 coins, by day. Partly usable: Reddit community post counts for 15 coins (today's snapshot only). Not usable so far: news article counts (the service refused most requests), Google Trends, YouTube.
- Looked at after the fact, a rise in Wikipedia or Reddit attention had no link to what the coin did over the next 1, 3 or 7 days, and buying the five coins with the biggest rise lost to buying all of them once costs were paid. Table at the bottom.
- So a plain attention count is not a way to pick the hot coin. It can still be shown to an AI trader as one input, and that trader then has to beat this plain count to show anything.

MEASURED. The local store is the attention store on the research machine. Its coin list is the 23 Coinbase USD spot pairs from the fast tape. The requested attention window covers 2025-01-01 through 2026-11-24 UTC. The separate return description ends on 2026-03-31 UTC. It is not a test.

## What each source gave us

| Source | MEASURED coverage | Time and faults |
|---|---|---|
| Wikipedia | 17/23 mapped, 10,698 stored daily rows (4,155 pass the default vintage filter). 2,256 hours from the dump audit only (1,128 pass the filter). First label 2025-01-01 on most covered titles. | Daily UTC user views by article title. The per-article API has daily and monthly buckets, not hourly ([Wikimedia specification](https://wikimedia.org/api/rest_v1/metrics/pageviews/api-spec.json)). STATED availability: day end +36h for ordinary API rows. Known late files are capture-only. Original evidence and its limits are below. |
| GDELT DOC 2.0 | 16 stored day/hour buckets on 1/23 coins. Full-span request status: 502 × 13, 429 × 2, not tried × 8. No complete hourly response was retained. | STATED availability for valid buckets: period end +6h. GDELT describes publication-time query windows and distinct counts ([GDELT DOC guide](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)). Articles indexed after the assumed gate could appear in today's count without having been visible then. UNKNOWN first indexing time and the size of that gap or of false matches. |
| Alpaca tape | 11,726 articles overall, 2026-04-29 to 2026-11-24; 52 coin-title matches on 8/23 coins. 209 dated days with retained articles; hourly and daily count rows. 0/11,726 marked edited later. | UTC article `created` and `updated` in the tape ([Alpaca news endpoint](https://docs.alpaca.markets/us/reference/news-3.md)). STATED availability: +6h from period end or most recent marked edit, whichever is later. UNKNOWN first ingest and edits not present in the tape. |
| Reddit / Arctic Shift | 15/23 mapped subreddit series, 9,694 dated daily counts. Most start 2025-01-01. An hourly DOGE query returned no rows. | Only posts in the named community, not Reddit-wide mentions. The time series may lag, and the archive can later merge edits or removals ([Arctic Shift API](https://github.com/ArthurHeitmann/arctic_shift/blob/master/api/README.md), [archive format](https://github.com/ArthurHeitmann/arctic_shift/blob/2025_12/file_content_explanations.md)). No verified non-revised series; capture-only. Missing bins stay missing. |
| Google Trends | MEASURED: three fixed-window requests returned 429, including the repeated fixed-window pair. No values to compare. | UNKNOWN repeat stability. The public result is sampled and scaled to the chosen time and place ([Google Trends FAQ](https://support.google.com/trends/answer/4365533)). A single full-window query is not safe for past-day ranking. |
| YouTube | MEASURED: the public DOGE search returned 14 video entries on its first loaded page, plus a continuation. Cards used relative ages, including one saying 2 days ago despite a January 2025 qualifier. No exact daily count. | UNKNOWN historical coverage. The keyed search API has publication filters but its result count is approximate ([YouTube search API](https://developers.google.com/youtube/v3/docs/search/list)). No key requested. |
| Other | MEASURED: CoinGecko returned a live list. No verified original historical daily count found. | CoinGecko's [trending API](https://docs.coingecko.com/reference/trending-search) is a recent snapshot. [CoinMarketCap](https://coinmarketcap.com/api/resources/how-to-retrieve-trending-most-visited-cryptocurrencies/) puts its API for most-visited coins on paid plans. [LunarCrush](https://lunarcrush.com/pricing) advertises historical data on paid plans; [Santiment](https://academy.santiment.net/sanapi/historical-and-realtime-data-restrictions/) documents free history limits. UNKNOWN for keyless, dated and versioned [Farcaster](https://docs.farcaster.xyz/reference/farcaster/api) or [X](https://docs.x.com/x-api/posts/counts/introduction.md) coin counts. Not stored. |

## How the timestamps and checks work

- STATED. `ts_utc` is the right edge of a UTC hour or day, not a time at which the count was usable. `known_at_utc` is the availability gate. The reader filters on both the period end and this gate. Original means supported by a dated archive file. Assumed lag is not proof of a past vintage. Capture-only is excluded by default and uses the collection timestamp.
- STATED. Wikipedia page titles were checked against their linked English Wikipedia pages. Some pages describe a whole protocol rather than the token alone. The current title can miss past names and redirects. A missing record is not a zero. Wikimedia describes different processing for [legacy hourly files](https://wikitech.wikimedia.org/wiki/Analytics/Data_Lake/Traffic/Pageviews) and [Pageview Complete](https://dumps.wikimedia.org/other/pageview_complete/readme.html).
- STATED. Wikimedia's analytics team reports daily updates usually between 01:00 and 03:00 UTC and possible caching ([Wikimedia analytics thread](https://lists.wikimedia.org/hyperkitty/list/analytics@lists.wikimedia.org/message/HSJYUNO6AXVRLMC4YGFOZXMH3JIFEOG3/)). The +36h gate is deliberately later than that ordinary schedule. It does not rule out reprocessing.
- MEASURED. The like-for-like audit summed the hourly user subtotals from the daily dump for each checked page and compared against API user views. 0/94 article-days differed (0.0%), on 6 dates. Median absolute difference 0; largest 0 views. This is a smaller sample than the proposed 20 × 30 audit. The separate legacy hourly requests did not yield a complete day. Equality now does not rule out a past revision.
- STATED. Audit hours are shown only after their entire archived daily file was available. They are not an hour-by-hour publish feed. Audit hours from late archive files are capture-only.
- MEASURED. [2025-01-01 user dump](https://dumps.wikimedia.org/other/pageview_complete/2025/2025-01/pageviews-20250101-user.bz2) carried HTTP Last-Modified 2025-01-02T01:11:01Z. Applying today's counts to dates before that file's observed timestamp would not be verified by this file.
- MEASURED. [2025-07-01 user dump](https://dumps.wikimedia.org/other/pageview_complete/2025/2025-07/pageviews-20250701-user.bz2) carried HTTP Last-Modified 2025-10-04T02:04:33Z. Applying today's counts to dates before that file's observed timestamp would not be verified by this file.
- MEASURED. [2026-03-01 user dump](https://dumps.wikimedia.org/other/pageview_complete/2026/2026-03/pageviews-20260301-user.bz2) carried HTTP Last-Modified 2026-05-04T01:31:26Z. Applying today's counts to dates before that file's observed timestamp would not be verified by this file.
- MEASURED. [2026-04-29 user dump](https://dumps.wikimedia.org/other/pageview_complete/2026/2026-04/pageviews-20260429-user.bz2) carried HTTP Last-Modified 2026-04-30T02:31:45Z. Applying today's counts to dates before that file's observed timestamp would not be verified by this file.
- MEASURED. [2026-10-01 user dump](https://dumps.wikimedia.org/other/pageview_complete/2026/2026-10/pageviews-20261001-user.bz2) carried HTTP Last-Modified 2026-11-19T00:18:46Z. Applying today's counts to dates before that file's observed timestamp would not be verified by this file.
- MEASURED. [2026-11-18 user dump](https://dumps.wikimedia.org/other/pageview_complete/2026/2026-11/pageviews-20261118-user.bz2) carried HTTP Last-Modified 2026-11-19T03:05:17Z. Applying today's counts to dates before that file's observed timestamp would not be verified by this file.
- MEASURED. The [daily archive listings](https://dumps.wikimedia.org/other/pageview_complete/) contained 692 of the 693 requested date labels. 422 file timestamps were later than the proposed +36h gate. The store does not assign these suspect dates ordinary historical availability. The timestamp can show a replacement, not the original publication time. A timestamp within the lag cannot prove the API value was never revised. All July through September 2026 are affected, along with most of October. Do not treat the resulting gap as low interest.
- STATED. GDELT used disambiguated phrases, not naked NEAR, ONDO, HYPE or PEPE tickers. Query examples: NEAR Protocol, Ondo Finance, Hyperliquid in crypto context, and Pepe token, Pepe memecoin or Pepe coin. The entity names were checked against [NEAR's project page](https://en.wikipedia.org/wiki/NEAR_(blockchain_platform)), [Ondo Finance](https://ondo.finance/), [Hyperliquid's project entry](https://iq.wiki/wiki/hyperliquid) and the [PEPE token entry](https://iq.wiki/wiki/pepe-cryptocurrency). Project and protocol mentions are not exact token demand. Article-list checks are reported separately.
- MEASURED. Short-range and title-check request status: 502 × 5, 200 × 1, 429 × 1. HTTP errors are gaps, not zero counts. The requests were spaced and backed off after 429s; responses are cached off repo.
- MEASURED. Alpaca had no matching exact ticker tags on the tape for these USD pairs. The count uses distinct retained headlines matched by a manual name or a disambiguated ticker, not article text or other crypto news sources. A zero means none matched on a day with a retained article, not proof of no coverage elsewhere. Counts assign a headline to its creation bucket; a recorded later edit delays availability.
- STATED. For a prospective Google Trends check, request the same short window of fully completed UTC days ending at each as-of day, with fixed region, category, search type and shared anchor term. Keep two spaced pulls of that exact request. Compare equal-window values and anchor-scaled cross-coin ranks before using them, and keep each first observed dataset. Do not extend the window or renormalize old snapshots with later peaks ([Google Trends FAQ](https://support.google.com/trends/answer/4365533)).

## Coverage by coin

MEASURED. Dates in this table name the first supplied bucket, not when it became known. For Wikipedia the second count is the number of days in the default reader once their gates pass. GDELT lists counts of daily and hourly buckets separately; an unmeasured coin is not a zero-attention coin. The Alpaca columns count all matching headlines and give the first nonzero date.

| Coin | Wikipedia title | Wiki days / replay days; first | GDELT days / hours; span | Alpaca headlines; first hit | Reddit community; days; first |
|---|---|---|---|---|---|
| AAVE | [Aave](https://en.wikipedia.org/wiki/Aave) | 505 / 225; 2025-01-01 | 0 / 0; - | 1; 2026-09-28 | - |
| ADA | [Cardano (blockchain platform)](https://en.wikipedia.org/wiki/Cardano_(blockchain_platform)) | 693 / 271; 2025-01-01 | 0 / 0; - | 0; - | [r/cardano](https://www.reddit.com/r/cardano/); 687; 2025-01-01 |
| AVAX | [Avalanche (blockchain platform)](https://en.wikipedia.org/wiki/Avalanche_(blockchain_platform)) | 693 / 271; 2025-01-01 | 0 / 0; - | 0; - | [r/Avax](https://www.reddit.com/r/Avax/); 625; 2025-01-02 |
| BCH | [Bitcoin Cash](https://en.wikipedia.org/wiki/Bitcoin_Cash) | 693 / 271; 2025-01-01 | 0 / 0; - | 0; - | [r/Bitcoincash](https://www.reddit.com/r/Bitcoincash/); 658; 2025-01-01 |
| BNB | No verified coin-specific article | 0 / 0; - | 0 / 0; - | 0; - | - |
| BTC | [Bitcoin](https://en.wikipedia.org/wiki/Bitcoin) | 693 / 271; 2025-01-01 | 0 / 0; - | 29; 2026-04-29 | [r/Bitcoin](https://www.reddit.com/r/Bitcoin/); 693; 2025-01-01 |
| DOGE | [Dogecoin](https://en.wikipedia.org/wiki/Dogecoin) | 693 / 271; 2025-01-01 | 0 / 0; - | 0; - | [r/dogecoin](https://www.reddit.com/r/dogecoin/); 693; 2025-01-01 |
| DOT | [Polkadot (blockchain platform)](https://en.wikipedia.org/wiki/Polkadot_(blockchain_platform)) | 693 / 271; 2025-01-01 | 0 / 0; - | 0; - | [r/Polkadot](https://www.reddit.com/r/Polkadot/); 685; 2025-01-01 |
| ENA | No verified coin-specific article | 0 / 0; - | 0 / 0; - | 1; 2026-06-02 | - |
| ETH | [Ethereum](https://en.wikipedia.org/wiki/Ethereum) | 693 / 271; 2025-01-01 | 0 / 0; - | 6; 2026-04-29 | [r/ethereum](https://www.reddit.com/r/ethereum/); 693; 2025-01-01 |
| HBAR | [Hedera (distributed ledger)](https://en.wikipedia.org/wiki/Hedera_(distributed_ledger)) | 654 / 232; 2025-02-09 | 0 / 0; - | 0; - | [r/Hedera](https://www.reddit.com/r/Hedera/); 693; 2025-01-01 |
| HYPE | No verified coin-specific article | 0 / 0; - | 0 / 0; - | 5; 2026-05-14 | - |
| LINK | [Chainlink (blockchain oracle)](https://en.wikipedia.org/wiki/Chainlink_(blockchain_oracle)) | 693 / 271; 2025-01-01 | 0 / 0; - | 3; 2026-05-06 | [r/Chainlink](https://www.reddit.com/r/Chainlink/); 542; 2025-01-01 |
| LTC | [Litecoin](https://en.wikipedia.org/wiki/Litecoin) | 693 / 271; 2025-01-01 | 0 / 0; - | 0; - | [r/litecoin](https://www.reddit.com/r/litecoin/); 675; 2025-01-01 |
| NEAR | [NEAR (blockchain platform)](https://en.wikipedia.org/wiki/NEAR_(blockchain_platform)) | 408 / 148; 2025-10-13 | 0 / 0; - | 0; - | [r/nearprotocol](https://www.reddit.com/r/nearprotocol/); 560; 2025-01-01 |
| ONDO | No verified coin-specific article | 0 / 0; - | 16 / 0; 2026-03-01 to 2026-03-16 | 0; - | - |
| PAXG | No verified coin-specific article | 0 / 0; - | 0 / 0; - | 0; - | - |
| PEPE | No verified coin-specific article | 0 / 0; - | 0 / 0; - | 0; - | - |
| SOL | [Solana (blockchain platform)](https://en.wikipedia.org/wiki/Solana_(blockchain_platform)) | 693 / 271; 2025-01-01 | 0 / 0; - | 5; 2026-05-04 | [r/solana](https://www.reddit.com/r/solana/); 693; 2025-01-01 |
| SUI | [Sui (blockchain platform)](https://en.wikipedia.org/wiki/Sui_(blockchain_platform)) | 122 / 27; 2026-07-26 | 0 / 0; - | 0; - | - |
| XLM | [Stellar (payment network)](https://en.wikipedia.org/wiki/Stellar_(payment_network)) | 693 / 271; 2025-01-01 | 0 / 0; - | 0; - | [r/Stellar](https://www.reddit.com/r/Stellar/); 604; 2025-01-01 |
| XRP | [XRP Ledger](https://en.wikipedia.org/wiki/XRP_Ledger) | 693 / 271; 2025-01-01 | 0 / 0; - | 2; 2026-05-01 | [r/XRP](https://www.reddit.com/r/XRP/); 692; 2025-01-01 |
| ZEC | [Zcash](https://en.wikipedia.org/wiki/Zcash) | 693 / 271; 2025-01-01 | 0 / 0; - | 0; - | [r/zec](https://www.reddit.com/r/zec/); 501; 2025-01-01 |

## GDELT query notes

- AAVE: `"Aave" (crypto OR token OR DeFi)`.
- ADA: `"Cardano" (blockchain OR cryptocurrency)`.
- AVAX: `("Avalanche blockchain" OR "Avalanche network")`.
- BCH: `"Bitcoin Cash"`.
- BNB: `("BNB Chain" OR "Binance Coin")`.
- BTC: `"Bitcoin" (crypto OR cryptocurrency)`.
- DOGE: `"Dogecoin"`.
- DOT: `"Polkadot" (blockchain OR cryptocurrency)`.
- ENA: `("Ethena" OR "Ethena Labs") (crypto OR blockchain OR DeFi)`.
- ETH: `"Ethereum"`.
- HBAR: `("Hedera Hashgraph" OR "Hedera network" OR "HBAR token")`.
- HYPE: `"Hyperliquid" (crypto OR perpetuals OR token)`.
- LINK: `"Chainlink" (blockchain OR crypto OR token)`.
- LTC: `"Litecoin"`.
- NEAR: `"NEAR Protocol"`.
- ONDO: `"Ondo Finance"`.
- PAXG: `("Pax Gold" OR "Paxos Gold" OR "PAXG token")`.
- PEPE: `("Pepe token" OR "Pepe memecoin" OR "Pepe coin")`.
- SOL: `"Solana" (blockchain OR cryptocurrency OR crypto)`.
- SUI: `("Sui blockchain" OR "Sui network" OR "SUI token")`.
- XLM: `("Stellar Lumens" OR "Stellar blockchain" OR "XLM token")`.
- XRP: `("XRP" OR "XRP Ledger") (crypto OR Ripple OR cryptocurrency)`.
- ZEC: `"Zcash"`.

UNKNOWN. Phrase checks reduce obvious common-word collisions, but I did not measure a general false-hit rate. An article with PEPE and a different similarly named coin can still match.

## After-the-fact description, not a test

MEASURED. The read-only SQL selected only Coinbase USD daily candle starts from 2025-01-01 through 2026-03-31 UTC. A candle close is the end of its labeled day. No April candle or later return was read. The final possible signal date is earlier for each forward horizon, so every return ends within the description window.

STATED. For a coin with both counts, attention change is today's log(1 + count) minus yesterday's. For each day and horizon, compute Spearman rank correlation across at least six coins with both that change and a forward return; skip constant ranks. The reported correlation is the average of those daily values. Coin symbol breaks ties at the top-five cutoff. Top five is equal weighted. The comparison holds all eligible Coinbase pairs with both closes on that date, whether or not they have attention data. The cost column deducts 30 bps once for the top-five basket per holding window, with the all-coins yardstick left frictionless. Charging the same round-trip cost to both sides would leave the spread unchanged.

STATED. This deliberately pairs counts for the labeled day with returns from that day's close, before assumed source delays. It uses today's source snapshots, including capture-only rows. It is not a claim that the count was tradable then. The coin list was assembled later and is not a historical listing universe. The holding windows overlap. Do not read these rows as independent bets or use them as a pass mark.

| Source | Forward days | Dates used | Avg coins ranked | Avg Spearman | Top five minus all, gross bps | Top five minus all, net bps |
|---|---:|---:|---:|---:|---:|---:|
| Wikipedia | 1 | 453 | 14.8 | -0.0117 | +0.63 | -29.37 |
| Wikipedia | 3 | 451 | 14.8 | -0.0123 | +4.45 | -25.55 |
| Wikipedia | 7 | 447 | 14.8 | +0.0012 | +33.40 | +3.40 |
| Reddit | 1 | 453 | 13.6 | -0.0034 | -2.00 | -32.00 |
| Reddit | 3 | 451 | 13.6 | -0.0010 | -0.98 | -30.98 |
| Reddit | 7 | 447 | 13.6 | -0.0003 | +10.48 | -19.52 |

UNKNOWN for the horizons with no eligible days: GDELT, Alpaca, Google Trends, YouTube, Other. An absent result is not a zero return.

## What this changes for our queue

Written by the builder, 2026-11-25.

- The picker in the owner's method card (`practice/traders/F01_hot_coin_swing.md`) is judged against a plain yardstick that buys the coins with the biggest attention rise, next to the biggest-risers rule. Both are cheap and both are now known to be near zero before costs.
- No counted test is planned on attention counts alone.
- The news-count source is retried later from a different address; until then headlines for coins come only from the stock news feed, which has 52 matching headlines in seven months.
