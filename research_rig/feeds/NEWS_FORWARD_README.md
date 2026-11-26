# Forward headline capture (queue 120)

STATED: This private logger polls only the reader feeds listed as enabled below. It never fetches a linked page. Each UTF-8 RSS or Atom response is processed in memory. The append-only daily UTC JSONL files contain capture time (integer UTC seconds), source ID, publisher-stated time (null if absent), headline, link, the SHA-256 of the item ID (or link if absent), and a backlog flag. Nothing from the article body, feed summary, or raw XML is written, and no live rows go into Git.

## Source review

STATED: A feed advertised for personal reading does not by itself authorize this research archive. On November 26, 2026 MT, these three published reader feeds were confirmed as RSS or Atom. Publisher and rights notices apply; the store is private and no feed content is republished.

| Enabled source | Official terms and feed evidence |
| --- | --- |
| Bitcoin Optech | The [publisher's About page](https://bitcoinops.org/en/about/) says “All material produced by Bitcoin Optech is open source and released under the MIT license.” The [MIT grant](https://opensource.org/license/mit) includes the rights to “use, copy”; this applies to Optech's own material, not third-party works. The publisher supplies its own [Atom feed](https://bitcoinops.org/feed.xml). |
| Federal Reserve Board press releases | The [Board's feed guide](https://www.federalreserve.gov/feeds/feeds.htm) says “The reader automatically incorporates changes for RSS subscribers when content in the feed has been updated or changed.” The [Board disclaimer](https://www.federalreserve.gov/disclaimer.htm) says “Unless otherwise indicated, information on Board's website is in the public domain and may be copied and distributed without permission. Please cite to the Board as the source of the information.” The [press feed](https://www.federalreserve.gov/feeds/press_all.xml) is Board material. |
| SEC press releases | The [SEC webmaster FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions) says “We allow scripted access to sec.gov content” and “All Government-created content on sec.gov and EDGAR public filing content are free to access and reuse.” It requires a declared user agent; the operator supplies a real contact. The [SEC reader directory](https://www.sec.gov/file/secrssshtml) supplies the [press feed](https://www.sec.gov/rss/news/press.xml). |

| Not enabled | Official evidence or reason |
| --- | --- |
| CoinDesk | [Terms](https://www.coindesk.com/terms): “You agree that you will not use any robot, spider, scraper, or other automated means to access the Services for any purpose without our express written permission.” |
| Cointelegraph | [Terms](https://cointelegraph.com/terms-and-privacy): “Redistribution, reproduction, automated scraping, or creation of independent content pipelines based on Cointelegraph reputation is strictly prohibited without prior written authorization.” |
| Decrypt | The [terms page](https://decrypt.co/terms) was blocked during review. One review block, no permission quote verified and no attempt to get around it or poll the feed. |
| The Block | [Terms](https://www.theblock.co/terms-service) forbid “conduct any systematic or automated data collection activities (including without limitation scraping, data mining, data extraction and data harvesting) on or in relation to the Service or the Content.” |
| CryptoSlate | The [feed page](https://cryptoslate.com/feeds/) says “These feeds are for personal, informational and non-commercial reading.” Its [terms](https://cryptoslate.com/terms-and-conditions/) forbid bots and scripts “to access, copy, extract, monitor, or interfere with CryptoSlate without prior written permission.” |
| Blockworks | Its [terms](https://blockworks.com/terms) restrict its Data customers from “engage in any mass or bulk extraction or scraping of the Data or Platform”; that is not a reader-feed storage license. No applicable authorization for the research archive was verified. |
| DL News | Its dedicated [RSS terms](https://www.dlnews.com/rss/) say “We allow the use of DLnews.com RSS feeds for personal use in a news reader or as part of a non-commercial blog.” Kept off because automated, durable research logging is not expressly covered. |
| Bitcoin Magazine | [Terms](https://bitcoinmagazine.com/terms-of-use): “Unauthorized reproduction, distribution, or modification is prohibited without our prior written consent.” No affirmative permission for this archive was verified. |
| Coinbase blogs and status | Coinbase [publishes reader feeds for its status page](https://status.coinbase.com/), but its [US agreement](https://www.coinbase.com/legal/user_agreement/united_states) says “You agree you will not copy, transmit, distribute, sell, license, reverse engineer, modify, publish, or participate in the transfer or sale of, create derivative works from, or in any other way exploit any of the Content, in whole or in part without the prior written consent of Coinbase.” No separate permission for persistent logging of either source was verified. |
| Kraken blogs and status | The [status page](https://status.kraken.com/) says “Get the Atom Feed or RSS Feed.” [Global terms](https://www.kraken.com/legal/global-terms) forbid “create, use, operate, or employ any bots, robots, parsers, spiders, scripts, programs, routines, or any other forms of automation to engage in any activity on Our Content” and no separate archive permission for either source was verified. |

STATED: The transport has a fixed allowlist and never follows redirects. Binance, Upbit, Bithumb, PR Newswire, Business Wire, Nasdaq and CoinGecko are excluded, including links to those domains inside otherwise admitted feeds.

## Capture clock and operation

STATED: Known-at is **our UTC capture time plus 60 seconds**, allowing time to persist the private row before a replay wake. The publisher-stated time never gates visibility. Anything first observed in a feed's opening snapshot is backlog, as is an edit first observed in the opening snapshot after downtime. The reader withholds backlog and all later edits to a backlogged item. An unchanged item is not logged twice; a changed title appends a row and never changes its earlier row. A conditional 304 confirms that the previous snapshot is unchanged. The logger waits at least ten minutes between requests to each feed, uses ETag or Last-Modified when supplied, and runs requests sequentially. Temporary errors back off; explicit blocks (including 403 and 429) and redirects persist a drop and are never worked around.

STATED: From the audited checkout, run these in the foreground with a real contact address designated by the operator. Captured data stays under the private, mode-0700 `/home/user/workspace/rig/data/news_forward` directory with mode-0600 files; it is not created until the run command.

```sh
python3 -B -m research_rig.feeds.news_forward run --contact "${NEWS_FORWARD_CONTACT:?set a real operator email first}"
python3 -B -m research_rig.feeds.news_forward status
```

STATED: Check status from a second terminal. `running=1` and an increasing heartbeat timestamp with low `age_seconds` indicate activity; a stale heartbeat is not a healthy process. The status output contains only counts, integer flags and clock values. For a clean restart, stop the foreground process with Ctrl-C or SIGTERM, wait for `running=0`, then repeat the same run command. A second writer is refused. Restarts re-read private rows for deduplication, not for historical fetching; they never backfill. If a process dies during a poll, the unresolved feed is held and counted until operator review rather than assuming the response was not a block. Stop on `cap_stop=1`; the 300 MB cap and 3.2 GiB workspace reserve are checked before polling and writes. No data is deleted or rotated away automatically. A partial write that cannot be read back stops for inspection instead of silently rewriting custody.

MEASURED: The acceptance tests use invented RSS and Atom only. No live logger was started for this build.
