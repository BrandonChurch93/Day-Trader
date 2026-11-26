# Point-in-time exchange announcements

Version 1 is **sparse context, not a same-day trigger**. This is an offline scaffold: no historical announcement text has been collected, no real store has been staged, and no scout is wired to use it automatically. The only real measurements are CDX metadata counts. Missing rows do not mean an exchange had no announcements.

## Wayback feasibility

MEASURED: These are distinct HTTP 200 HTML index capture times from the [Wayback CDX API](https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server), January 2021 through October 2026 inclusive. Gaps are between adjacent captures, including across empty months; they are not publication-to-capture delays. The full 70-month series is off repo at `/home/user/workspace/rig/ideas/wayback_index_counts_2021_2026.json`.

The counts used metadata only, an identified research user agent, and at least five seconds between index requests. That is at most 12 requests per minute, below the 24 per minute in the [Wayback client’s CDX rate guidance](https://wayback.readthedocs.io/en/stable/_modules/wayback/_client.html). No archived bodies were requested for feasibility.

| Exchange | Index path | Captures | Median gap | Empty months of 70 | Longest interior gap |
| --- | --- | ---: | ---: | ---: | ---: |
| Binance | `www.binance.com/en/support/announcement` | 332 | 1.63 days | 14 | 115.7 days |
| Coinbase | `www.coinbase.com/blog` | 1,274 | 5.43 hours | 22 | 118.4 days |
| Kraken | `blog.kraken.com/category/product/asset-listings` and `blog.kraken.com/category/asset-listings` | 34 | 28.18 days | 46 | 141.9 days |
| OKX | `www.okx.com/help/category/announcements` | 85 | 8.48 days | 35 | 60.9 days |
| Bybit | `announcements.bybit.com/en/` | 118 | 2.08 days | 42 | 93.7 days |

Coinbase's number measures its broad blog index, not listing cadence. Coinbase [announced that it was moving individual listing announcements off its blog](https://www.coinbase.com/blog/update-to-asset-listing-announcements). None of these counts proves that an archived HTML payload contains a notice: a captured shell can have no usable text.

MEASURED: The initial metadata-only Binance article-prefix query timed out after 50 seconds without an HTTP response. After a cooldown of at least ten minutes, the narrower `www.binance.com/en/support/announcement/detail/` query returned HTTP 200 and zero qualifying HTTP 200 HTML rows for January 2022 and July 2021, with neither response at its cap. Requests were at least 30 seconds apart. July 2023 timed out after 60 seconds, so the sample stopped at two completed months out of six. The results and stop reason are off repo at `/home/user/workspace/rig/ideas/wayback_article_binance_probe_2021_2026.json`.

UNKNOWN: A timeout is not a measured zero or a confirmed access refusal. The two zeros apply only to the sampled Binance path and query, not to all Binance articles or all exchange announcements. Other article counts, publication lag, and within-one-day coverage remain unknown. CDX has no publication timestamp field in its [documented fields](https://github.com/internetarchive/wayback/tree/master/wayback-cdx-server), and a date in a URL is not necessarily its publication date. Version 1 therefore uses index captures only.

## What the scout sees

- **Clock:** Among staged evidence, the earliest verified index capture showing a qualifying notice link and headline wins. `known_at` is `capture_ts + 300` UTC seconds, inclusive at wake. Publication, listing and later article times never backdate that observation. A later edit cannot replace the earliest excerpt. A newly verified earlier capture may correct the store during staging. Before replay use, freeze a read-only snapshot and pin its SHA-256 in the replay manifest; do not let replay scouts read a store still being backfilled.
- **Evidence:** A row contains exchange, notice key, category, capture time, known time, CDX digest, exact archived index URL, normalized linked notice URL and at most 240 characters of the captured index headline. The notice URL is an identifier, not a request to fetch live text. No captured article bodies, prices, returns, or threshold settings are stored.
- **Filters:** Only recognizable English listing, delisting, monitoring-tag and trading-halt headlines with supported same-venue notice paths qualify. Generic, explicitly hidden, external, unrecognized and ambiguous links are omitted. There is no JavaScript or CSS rendering, and no child resource or live page is fetched. This favors omission over guessing; it is not a count of all notices.

## Offline use and limits

`announcements.stage_index(IndexCapture(...))` accepts one already acquired, exact raw replay response in memory. It rejects non-200 responses, a redirect or changed replay URL, an inconsistent Memento timestamp, unsupported sources, and payload bytes that do not match the CDX SHA-1 digest. Treat a failure as unusable evidence, not permission to fall back to a live page or a later replay. The scaffold includes no transport, bulk collector, or authority to collect publisher text. Review the [Internet Archive terms](https://archive.org/about/terms) and publisher terms before any real staging, including the automation restrictions in [Kraken’s global terms](https://www.kraken.com/legal/global-terms) and [Bybit’s terms](https://www.bybit.com/common-static/compliance/legal/BYBIT/865a7c292f3e8f9ef497ea2b75e119bf.pdf).

Data stays in a private SQLite file under `/home/user/workspace/rig/data/feeds_announcements/`, off repo. Raw HTML is never written. The database is capped at 32 MiB and staging requires room for the write and rollback while preserving 1 GiB free. The default store is created only when there is eligible evidence to stage. The scaffold needs Python 3.10 or newer and SQLite 3.37 or newer.

From the repo root, call `get_announcements(wake_utc, after_utc=None, exchange=None)` from `research_rig.feeds.announcements`. Times are integer Unix UTC seconds; the optional lower bound is exclusive on `known_at`. The function is read-only and raises if the store does not exist. Run `python -m unittest research_rig.feeds.test_announcements` for synthetic tests, including `capture_ts <= known_at <= wake` over 200 seeded random wakes and exact five-minute boundary checks.
