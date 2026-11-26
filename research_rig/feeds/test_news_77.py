"""Made-up GKG packets only; point-in-time assertions mirror test_tape."""
from collections import Counter
from io import BytesIO
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from research_rig.feeds import news_77 as news
from research_rig.feeds import calibrate_news_77 as calibration
from research_rig.feeds.build_doc158_news_77 import render


def record(t, title, url, *, published="20991231235959", collection="1"):
    fields = [news.stamp(t) + "-T5", published, collection, "not a trusted domain", url]
    return "\t".join(fields + [""] * 21 + [f"<PAGE_TITLE>{title}</PAGE_TITLE>"]) + "\n"


def packet(t, *rows):
    out = BytesIO()
    with ZipFile(out, "w") as zp:
        zp.writestr(news.stamp(t) + ".gkg.csv", "".join(rows))
    return out.getvalue()


class News77Test(unittest.TestCase):
    def test_scope_is_first_two_scored_weeks_in_pinned_registration(self):
        weeks, jobs = news.batches()
        self.assertEqual(weeks, [("2026-07-06", ("BCH", "HYPE", "SOL", "XLM", "ZEC")),
                                 ("2026-07-13", ("LINK", "LTC", "ONDO", "SUI", "ZEC"))])
        self.assertEqual(Counter(job[1] for job in jobs), {week: 672 for week, _ in weeks})
        for t, week, _ in jobs:
            self.assertLessEqual(news.utc(week), t + news.KNOWN_LAG)
            self.assertLess(t + news.KNOWN_LAG, news.utc(week) + news.WEEK)

    def test_titles_only_first_seen_from_packet_not_publisher_or_body(self):
        t = news.utc("2026-07-05T23:45")
        raw = packet(t, record(t, "Solana &amp; Zcash launch a pilot", "https://www.example.net/abc?utm_campaign=x"),
                     record(t, "Bitcoin Cash lifts cyber freeze", "https://www.binance.com/story"),
                     record(t, "Zcash launches a pilot", "https://finance.nasdaq.com/story"),
                     record(t, "Stellar sale on vacuums", "https://www.example.net/deal"),
                     record(t, "$SOL faces lawsuit", "https://www.example.net/law"),
                     record(t, "Zcash volume doubled", "https://www.example.net/story", collection="6"))
        scanned, rows = news.scan(raw, t, ("BCH", "SOL", "XLM", "ZEC"))
        self.assertEqual(scanned, 6)
        self.assertEqual([row["matched_coin"] for row in rows], ["SOL", "ZEC", "SOL"])
        self.assertEqual(rows[0], {"first_seen_utc": t, "source_domain": "example.net",
                                  "title": "Solana & Zcash launch a pilot", "url": "https://example.net/abc",
                                  "matched_coin": "SOL"})
        self.assertEqual(news.known_at(rows[0]), news.utc("2026-07-06T00:05"))
        with self.assertRaisesRegex(ValueError, "own archive batch"):
            news.scan(packet(t, record(t + news.QUARTER, "Solana", "https://example.net/abc")), t, ("SOL",))

    def test_future_mutation_invariance_and_boundary_inclusion(self):
        t0 = news.utc("2026-07-06T13:05")
        t0_record = t0 - news.KNOWN_LAG
        early = {"first_seen_utc": t0_record, "title": "Solana prior synthetic story"}
        later = {"first_seen_utc": t0_record + news.QUARTER, "title": "Solana future synthetic story"}
        later_edited = {**later, "title": "Dramatic edit to a future synthetic title"}
        self.assertEqual(news.visible([early, later], t0 - 1), [])
        self.assertEqual(news.visible([early, later], t0), [early])
        self.assertEqual(news.visible([early, later_edited], t0), [early])
        self.assertEqual(news.visible([early, later], t0, after_utc=t0), [])
        for wake in random.Random(77).sample(range(t0 - 400, t0 + 400), 200):
            self.assertEqual(news.visible([early, later], wake), news.visible([early, later_edited], wake))
            self.assertTrue(all(news.known_at(row) <= wake for row in news.visible([early, later], wake)))

    def test_earliest_duplicate_survives_and_future_version_cannot_replace_it(self):
        t = news.utc("2026-07-06")
        early = {"first_seen_utc": t, "url": "https://example.net/a",
                 "title": "Solana wins case", "matched_coin": "SOL"}
        newer = {**early, "first_seen_utc": t + news.QUARTER, "title": "Solana case update"}
        syndication = {**newer, "url": "http://another.net/b", "title": "Solana wins case!"}
        self.assertEqual(news.unique_rows([early, newer, syndication], set(), set()), [early])

    def test_week_reader_refuses_cross_week_and_nonbasket_rows(self):
        week2 = news.utc("2026-07-13")
        w1late = {"first_seen_utc": week2 - 2 * news.QUARTER, "matched_coin": "ZEC"}
        w2out = {"first_seen_utc": week2 - news.QUARTER, "matched_coin": "SOL"}
        w2in = {**w2out, "matched_coin": "LTC"}
        self.assertEqual(news.week_visible([w1late, w2out, w2in], week2), [])
        self.assertEqual(news.week_visible([w1late, w2out, w2in], week2 + news.HOUR), [w2in])
        self.assertEqual(news.week_visible([w2in], week2 + news.HOUR, after_utc=week2 + 300), [])
        with self.assertRaisesRegex(ValueError, "outside the two"):
            news.week_visible([], week2 + news.WEEK)

    def test_calibration_counts_before_sol_filter_and_keeps_original_history(self):
        day = news.utc("2026-07-12")
        end = day + calibration.DAY - news.QUARTER
        prior_url = "https://coindesk.com/prior"
        kept = dict(first_seen_utc=day, matched_coin="SOL", source_domain="cointelegraph.com",
                    title="SOLANA and Crypto", url="https://cointelegraph.com/new")
        prior = dict(first_seen_utc=day - news.QUARTER, matched_coin="SOL",
                     source_domain="coindesk.com", title="Previously seen", url=prior_url)
        requests = []

        def get(t):
            requests.append(t)
            if t == day:
                return packet(t, record(t, "Solana — repeated URL", prior_url),
                              record(t, kept["title"], kept["url"]),
                              record(t, "Bitcoin launch and cryptocurrency", "https://cryptoslate.com/new"),
                              record(t, "Solana", "https://unrelated.example/story", collection="6"),
                              record(t, "", "https://decrypt.co/empty"))
            return packet(t, record(t, "Solana rolls across weeks", "https://coindesk.com/late")) if t == end else packet(t)

        with patch.object(news, "check_space"), patch.object(news, "read_file", return_value=[prior, kept]), \
                patch.object(news, "Archive", return_value=SimpleNamespace(get=get)), patch.object(calibration.time, "sleep"):
            c = calibration.scan_day()
        self.assertEqual(requests, list(range(day, end + 1, news.QUARTER)))
        self.assertEqual(c["publishers"]["decrypt.co"]["page_title"], 1)
        self.assertEqual(c["publishers"]["cryptoslate.com"]["crypto"], 0)
        self.assertEqual(c["publishers"]["cryptoslate.com"]["bitcoin"], 1)
        self.assertEqual(c["publisher_solana"]["duplicate"], 1)
        self.assertEqual(c["publisher_solana"]["outside_solana_basket"], 1)
        self.assertEqual(c["publisher_solana"]["non_web_collection"], 0)
        self.assertEqual(c["all_solana"]["non_web_collection"], 1)
        self.assertEqual(c["all_solana"]["kept"], c["original_pilot_solana_kept"])

    def test_budget_checks_fail_before_a_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            with patch.object(news.os, "statvfs", return_value=SimpleNamespace(
                    f_bavail=news.MIN_FREE - 1, f_frsize=1)):
                with self.assertRaisesRegex(ValueError, "3.2 GiB"):
                    news.check_space(root)
            with patch.object(news.os, "statvfs", return_value=SimpleNamespace(
                    f_bavail=2 * (news.MIN_FREE + news.DISK_CAP), f_frsize=1)):
                with self.assertRaisesRegex(ValueError, "400 MB"):
                    news.check_space(root, news.DISK_CAP + 1)

    def test_report_renders_only_counts_and_never_imputes_incomplete_zero(self):
        _, sched = news.batches()
        t, w, coins = sched[0]
        secret_title = "Synthetic proprietary title for Zcash"
        secret_url = "https://publisher.example/synthetic-proprietary-path"
        row = dict(first_seen_utc=t, matched_coin="ZEC", source_domain="publisher.example",
                   title=secret_title, url=secret_url)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            contents = news.encoded(row)
            with news.create(root, "rows.jsonl") as f:
                f.write(contents)
            with news.create(root, "coverage.jsonl") as f:
                f.write(news.encoded(dict(batch_utc=t, week=w, compressed_bytes=15, source_rows=7,
                                          matching_rows=2, kept_rows=1, kept_bytes=len(contents))))
            rows, counts = news.report(root)
        self.assertIn(row["matched_coin"], coins)
        self.assertIsNone(counts["zero_coin_weeks"])
        self.assertEqual(counts["duplicate_coin_matches"], 1)
        key = news.review_key(news.seeded_titles(rows))
        text = render(rows, counts, (0, 0, 1), "STATED: Test only.", key)
        self.assertIn("share of full coin-weeks with no headline is unknown", text)
        self.assertIn("| 2026-07-06 | ZEC | 1 so far | 1 so far |", text)
        self.assertIn("publisher.example", text)
        self.assertNotIn(secret_title, text)
        self.assertNotIn(secret_url, text)
        with self.assertRaisesRegex(ValueError, "deterministic sample size"):
            render(rows, counts, (0, 0, 2), "STATED: Test only.", key)
        with self.assertRaisesRegex(ValueError, "snapshot digest mismatch"):
            render(rows, counts, (0, 0, 1), "STATED: Test only.", "wrong")


if __name__ == "__main__":
    unittest.main()
