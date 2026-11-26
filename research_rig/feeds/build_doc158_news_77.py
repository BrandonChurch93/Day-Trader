"""Write the counts-only TM09 feed note. Never render a publisher title or URL."""
import argparse
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from research_rig.feeds import news_77 as news

OUT = news.REPO / "docs/research/158_dated_news_feed_for_tm09.md"
MT = ZoneInfo("America/Boise")


def table(header, rows):
    return "\n".join(["| " + " | ".join(header) + " |",
                      "| " + " | ".join(["---"] * len(header)) + " |",
                      *("| " + " | ".join(map(str, row)) + " |" for row in rows)])


def render(rows, counts, reviewed, recommendation, sample_key=None):
    weeks, _ = news.batches()
    full = counts["completed_batches"] == counts["planned_batches"]
    day_columns = ("Scored week start (UTC)", "Coin", "Distinct headlines", "Visible by final hourly wake")
    day_counts = []
    for week, per_coin in counts["counts_by_week"].items():
        complete = counts["batches_by_week"].get(week, 0) == news.WEEK // news.QUARTER
        for coin, n in per_coin.items():
            visible = counts["visible_by_final_wake"][week][coin]
            day_counts.append((week, coin, n if complete else f"{n} so far",
                               visible if complete else f"{visible} so far"))
    domain_rows = table(("Publisher domain", "Distinct coin-headlines"), counts["top_domains"])
    titles = news.seeded_titles(rows)
    samples = len(titles)
    duplicate_count, matches = counts["duplicate_coin_matches"], counts["raw_coin_matches"]
    duplicates = (f"{duplicate_count:,} of {matches:,} eligible coin-matches, or {duplicate_count / matches:.1%}"
                  if matches else "none observed; share undefined because there were no eligible matches")
    zero = counts["zero_coin_weeks"]
    n_coins = sum(len(coins) for _, coins in weeks)
    replay_requests = 20 * news.WEEK // news.QUARTER
    starts = ", ".join(datetime.fromtimestamp(news.utc(day), timezone.utc).astimezone(MT)
                       .strftime("%b %-d, %Y at %-I:%M %p %Z") for day, _ in weeks)
    if reviewed is not None:
        recap, event, other = reviewed
        if news.review_key(titles) != sample_key:
            raise ValueError("title-review snapshot digest mismatch")
        if min(reviewed) < 0 or sum(reviewed) != samples:
            raise ValueError("title-review counts differ from the deterministic sample size")
        n_scope = f"all {samples} available distinct titles" if samples < news.SAMPLE_N else f"{samples} distinct titles"
        title_line = (f"MEASURED: I read {n_scope} from {'both weeks' if full else 'the captured prefix'}, "
                      f"drawn without replacement using seed {news.SEED}. "
                      f"{recap} were price or volume recaps and forecasts, {event} described concrete events "
                      f"relevant to the matched asset, and {other} were other, commentary, false matches, or unclear. "
                      "These are title-only judgments, not verified events. Multiple titles can describe one event.")
    else:
        title_line = (f"UNKNOWN: The title review is incomplete. The deterministic sample would contain "
                      f"{samples} titles from the captured prefix; neither a recap share nor an event share "
                      "is measured for both weeks.")
    coverage = (f"MEASURED: {zero} of {n_coins} coin-weeks had no retained headline ({zero / n_coins:.0%})."
                if full else "UNKNOWN: Because the batch pull is incomplete, the share of full coin-weeks "
                "with no headline is unknown. The table contains prefix counts, not final weekly zeros.")
    if not recommendation.startswith(("STATED: ", "MEASURED: ", "UNKNOWN: ")):
        raise ValueError("recommendation needs an evidence label")
    return f"""<!-- Counts only; built by python3 -m research_rig.feeds.build_doc158_news_77. -->
# A dated headline feed for TM09

STATED: TM07's registration gives its news scout no input. This sample asks whether TM09 can add useful headlines that were already known at each replay wake. Only the first two scored weeks in the [TM07 registration](../../timemachine/TM07_REGISTRATION.md) were in scope; the earlier diagnostic week was left out. The selected starts are {starts}. Scripts use UTC.

## Source and clock

STATED: The [GDELT Project](https://www.gdeltproject.org/) says, “You may redistribute, rehost, republish, and mirror any of the GDELT datasets in any form.” Its [Terms of Use](https://gdeltproject.org/about.html) also require credit and a link to GDELT. This is a source for date-stamped metadata, not permission to copy publishers' article bodies.

STATED: The [GDELT DOC API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) limits start dates to the preceding three months, too recent for these weeks. The sampler instead uses the historical GKG ZIPs, which carry titles in [the XMLExtras PAGE_TITLE field](https://blog.gdeltproject.org/gkg-2-0-now-includes-page-titles/). It checks the archive label against the record ID's [update-batch prefix](https://data.gdeltproject.org/documentation/GDELT-Global_Knowledge_Graph_Codebook-V2.1.pdf). It never uses the publisher's article date.

STATED: Treat the archive's UTC label as the conservative start of a {news.QUARTER // 60}-minute batch, then wait {news.BUFFER // 60} more minutes for delivery and staging. The replay reader allows a row only at or after that known-at time. A title from a later batch cannot overwrite an earlier duplicate. The timestamp is the first matching batch observed in these sampled windows, not proof of the first time the article appeared on the web.

MEASURED: The batch prefix, member layout and ZIP integrity were checked. UNKNOWN: The vendor's archive digests were not verified against its manifest as [Doc 88](88_round_18_point_in_time_feeds.md) requires for historic replay. This pilot measures coverage, not replay eligibility.

STATED: Keep only batch time, publisher domain, title, URL and matched coin off repo. Coin matching uses project names, cashtags, and context-gated ambiguous names or tickers. Binance, Upbit, Bithumb, PR Newswire, Business Wire, Nasdaq and CoinGecko source domains are excluded. No publisher pages are fetched and the URLs are provenance only; do not follow them during replay. The sampler transfers one GDELT archive at a time, pauses between starts, and stops on a block or unexpected response.

## Sample coverage

MEASURED: {counts["completed_batches"]:,} of {counts["planned_batches"]:,} planned batches completed. They streamed {counts["compressed_bytes"] / 1e9:.2f} GB and scanned {counts.get("scanned_source_rows", 0):,} GKG records without saving the ZIPs. Duplicates were {duplicates}, using normalized URL or title within each coin and keeping the earliest. There were {counts["kept_coin_headlines"]:,} retained coin-headlines.

{coverage}

MEASURED: The table separates full UTC-week counts from counts available by the last registered hourly wake, Sunday at 23:00 UTC. Its scope is the five tradables for each week, not the whole price watchlist.

{table(day_columns, day_counts)}

MEASURED: The leading {len(counts["top_domains"])} source domains by retained coin-headlines were:

{domain_rows}

{title_line}

## Decision

{recommendation}

STATED: A replay-grade 20-week pull would need the published manifest and a digest check for every archive, plus {replay_requests:,} serial ZIP requests. At this pilot's {news.PAUSE:.2f}-second minimum start spacing, request spacing alone would take just over two hours, before slower transfers or longer politeness pauses. Stream archives without writing them to disk and check the 400 MB private-store cap and 3.2 GiB workspace reserve throughout.

UNKNOWN: The feed cannot show whether a scout used the news well or whether news improved trading. Only the dated headlines' availability and title mix are measured here. The remaining scored weeks were not requested.
"""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review", type=int, nargs=3, metavar=("RECAP", "EVENT", "OTHER"))
    p.add_argument("--review-key", help="SHA-256 printed with the exact seeded sample reviewed.")
    p.add_argument("--recommendation", required=True, help="Counts-only conclusion with status label.")
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    page = render(*news.report(), args.review, args.recommendation, args.review_key)
    if args.check:
        if OUT.read_text() != page:
            raise SystemExit("Doc 158 differs from its counts-only inputs")
    else:
        OUT.write_text(page)


if __name__ == "__main__":
    main()
