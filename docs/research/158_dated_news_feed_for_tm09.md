<!-- Counts only; built by python3 -m research_rig.feeds.build_doc158_news_77. -->
# A dated headline feed for TM09

STATED: TM07's registration gives its news scout no input. This sample asks whether TM09 can add useful headlines that were already known at each replay wake. Only the first two scored weeks in the [TM07 registration](../../timemachine/TM07_REGISTRATION.md) were in scope; the earlier diagnostic week was left out. The selected starts are Jul 5, 2026 at 6:00 PM MDT, Jul 12, 2026 at 6:00 PM MDT. Scripts use UTC.

## Source and clock

STATED: The [GDELT Project](https://www.gdeltproject.org/) says, “You may redistribute, rehost, republish, and mirror any of the GDELT datasets in any form.” Its [Terms of Use](https://gdeltproject.org/about.html) also require credit and a link to GDELT. This is a source for date-stamped metadata, not permission to copy publishers' article bodies.

STATED: The [GDELT DOC API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) limits start dates to the preceding three months, too recent for these weeks. The sampler instead uses the historical GKG ZIPs, which carry titles in [the XMLExtras PAGE_TITLE field](https://blog.gdeltproject.org/gkg-2-0-now-includes-page-titles/). It checks the archive label against the record ID's [update-batch prefix](https://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf). It never uses the publisher's article date.

STATED: Treat the archive's UTC label as the conservative start of a 15-minute batch, then wait 5 more minutes for delivery and staging. The replay reader allows a row only at or after that known-at time. A title from a later batch cannot overwrite an earlier duplicate. The timestamp is the first matching batch observed in these sampled windows, not proof of the first time the article appeared on the web.

MEASURED: The batch prefix, member layout and ZIP integrity were checked. UNKNOWN: The vendor's archive digests were not verified against its manifest as [Doc 88](88_round_18_point_in_time_feeds.md) requires for historic replay. This pilot measures coverage, not replay eligibility.

STATED: Keep only batch time, publisher domain, title, URL and matched coin off repo. Coin matching uses project names, cashtags, and context-gated ambiguous names or tickers. Binance, Upbit, Bithumb, PR Newswire, Business Wire, Nasdaq and CoinGecko source domains are excluded. No publisher pages are fetched and the URLs are provenance only; do not follow them during replay. The sampler transfers one GDELT archive at a time, pauses between starts, and stops on a block or unexpected response.

## Sample coverage

MEASURED: 1,344 of 1,344 planned batches completed. They streamed 5.85 GB and scanned 1,390,818 GKG records without saving the ZIPs. Duplicates were 2 of 57 eligible coin-matches, or 3.5%, using normalized URL or title within each coin and keeping the earliest. There were 55 retained coin-headlines.

MEASURED: 0 of 10 coin-weeks had no retained headline (0%).

MEASURED: The table separates full UTC-week counts from counts available by the last registered hourly wake, Sunday at 23:00 UTC. Its scope is the five tradables for each week, not the whole price watchlist.

| Scored week start (UTC) | Coin | Distinct headlines | Visible by final hourly wake |
| --- | --- | --- | --- |
| 2026-07-06 | BCH | 1 | 1 |
| 2026-07-06 | HYPE | 14 | 14 |
| 2026-07-06 | SOL | 17 | 15 |
| 2026-07-06 | XLM | 2 | 2 |
| 2026-07-06 | ZEC | 5 | 5 |
| 2026-07-13 | LINK | 3 | 3 |
| 2026-07-13 | LTC | 6 | 6 |
| 2026-07-13 | ONDO | 1 | 1 |
| 2026-07-13 | SUI | 1 | 1 |
| 2026-07-13 | ZEC | 5 | 5 |

MEASURED: The leading 15 source domains by retained coin-headlines were:

| Publisher domain | Distinct coin-headlines |
| --- | --- |
| finance.yahoo.com | 11 |
| bravenewcoin.com | 6 |
| cointelegraph.com | 4 |
| manilatimes.net | 4 |
| tickerreport.com | 4 |
| coinspeaker.com | 3 |
| fool.com | 3 |
| themarketsdaily.com | 3 |
| theportugalnews.com | 3 |
| banklesstimes.com | 2 |
| dailypolitical.com | 2 |
| artemis.bm | 1 |
| coindesk.com | 1 |
| daily-tribune.com | 1 |
| forbes.com | 1 |

MEASURED: I read all 55 available distinct titles from both weeks, drawn without replacement using seed 77. 20 were price or volume recaps and forecasts, 14 described concrete events relevant to the matched asset, and 21 were other, commentary, false matches, or unclear. These are title-only judgments, not verified events. Multiple titles can describe one event.

## Decision

STATED: This feed is too thin and noisy to justify the TM09 backfill as configured. All ten coin-weeks had at least one retained headline, but four had only one or two. Only about a quarter of the reviewed titles described a concrete event relevant to the matched coin; some name or ticker matches referred to another asset. Do not use this pilot as replay input.

STATED: A replay-grade 20-week pull would need the published manifest and a digest check for every archive, plus 13,440 serial ZIP requests. At this pilot's 0.55-second minimum start spacing, request spacing alone would take just over two hours, before slower transfers or longer politeness pauses. Stream archives without writing them to disk and check the 400 MB private-store cap and 3.2 GiB workspace reserve throughout.

UNKNOWN: The feed cannot show whether a scout used the news well or whether news improved trading. Only the dated headlines' availability and title mix are measured here. The remaining scored weeks were not requested.
