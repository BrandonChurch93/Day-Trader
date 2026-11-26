"""No network and no real custody. All examples and feeds are invented."""
from collections import deque
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from research_rig.feeds import news_forward as n

FEEDS = {"toy": "https://toy.example/feed"}
START = 1_800_000_000


def rss(*entries):
    nodes = []
    for key, title, date in entries:
        published = f"<pubDate>{date}</pubDate>" if date else ""
        nodes.append(f"<item><guid>{key}</guid><title>{title}</title>"
                     f"<link>https://toy.example/{key}</link>{published}"
                     "<description>Unneeded synthetic payload.</description></item>")
    return ("<rss version='2.0'><channel>" + "".join(nodes) + "</channel></rss>").encode()


def ok(*entries, **headers):
    return 200, headers, rss(*entries)


class Offline(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.s = n.Store(Path(tmp.name) / "log", min_free=0)
        self.s.mkdir()
        self.time = START
        self.responses, self.requests = deque(), []

    def get(self, url, headers):
        self.requests.append((self.time, url, dict(headers)))
        return self.responses.popleft()

    def logger(self):
        return n.Logger(self.s, FEEDS, self.get, now=lambda: self.time)

    def tick(self, logger, response, advance=n.INTERVAL):
        self.time += advance
        self.responses.append(response)
        self.assertTrue(logger.poll("toy"))

    def test_capture_edits_dedup_missing_time_conditional_and_backlog(self):
        log = self.logger()
        self.tick(log, ok(("old", "Initial", "future time"), ETag='"one"'), 0)
        self.time += n.INTERVAL - 1
        self.assertFalse(log.poll("toy"))
        self.tick(log, (304, {}, b""), 1)
        self.assertEqual(self.requests[-1][2]["etag"], '"one"')
        self.tick(log, ok(("old", "Revised initial", None), ("new", "First sight", None),
                          ("new", "Second same-ID entry", None),
                          **{"Last-Modified": "Mon, 04 Jan 2027 00:00:00 GMT"}))
        self.tick(log, ok(("new", "Edited", "Mon, 04 Jan 1999 00:00:00 GMT")))
        self.assertEqual(self.requests[-1][2]["modified"], "Mon, 04 Jan 2027 00:00:00 GMT")
        self.tick(log, ok(("new", "Edited", None)))
        rows = list(self.s.rows())
        self.assertEqual(len(rows), 4)
        self.assertEqual([r["backlog"] for r in rows], [True, True, False, False])
        self.assertEqual(rows[2]["published"], None)
        self.assertEqual(rows[2]["item_hash"], rows[3]["item_hash"])
        self.assertEqual([x["title"] for x in n.available(rows, START + 9 * n.INTERVAL)], ["First sight", "Edited"])
        self.assertNotIn("Unneeded", str(rows))
        self.assertEqual(os.stat(self.s.root).st_mode & 0o777, 0o700)
        self.assertTrue(all(p.stat().st_mode & 0o777 == 0o600 for p in self.s.root.iterdir()))

    def test_no_future_and_exact_delay(self):
        rows = [{"capture_utc": START, "backlog": True, "title": "Backlog"},
                {"capture_utc": START + 1, "backlog": False, "title": "Visible"},
                {"capture_utc": START + 7, "backlog": False, "title": "Future"}]
        edited = rows[:-1] + [{**rows[-1], "title": "Future mutation"}]
        self.assertEqual(n.available(rows, START + n.DELAY), [])
        for wake in range(START + 1 + n.DELAY, START + 7 + n.DELAY):
            self.assertEqual(n.available(rows, wake), [rows[1]])
            self.assertEqual(n.available(rows, wake), n.available(edited, wake))
        self.assertEqual(n.available(rows, START + 7 + n.DELAY), rows[1:])

    def test_restart_recovers_dedup_and_quarantines_downtime_items(self):
        log = self.logger()
        self.tick(log, ok(), 0)
        self.tick(log, ok(("one", "New in live poll", None)))
        restarted = self.logger()
        self.assertFalse(restarted.poll("toy"))
        self.tick(restarted, ok(("one", "New in live poll", None), ("two", "Observed on restart", None)))
        self.tick(restarted, ok(("three", "New after restart", None)))
        rows = list(self.s.rows())
        self.assertEqual([r["title"] for r in rows], ["New in live poll", "Observed on restart", "New after restart"])
        self.assertEqual([r["backlog"] for r in rows], [False, True, False])
        restarted.heartbeat()
        status = self.s.load("heartbeat.json")
        self.assertEqual((status["rows"], status["backlog_rows"], status["attempts"]), (3, 1, 4))
        self.assertTrue(all(type(v) is int for v in status.values()))

    def test_malformed_xml_backoff_and_doctype(self):
        log = self.logger()
        self.tick(log, (200, {}, b"<rss>"), 0)
        self.assertEqual(log.state["toy"]["next_utc"], START + 2 * n.INTERVAL)
        self.assertEqual(log.state["toy"]["errors"], 1)
        self.time += n.INTERVAL
        self.assertFalse(log.poll("toy"))
        self.tick(log, ok(("one", "Valid after error", None)))
        self.assertTrue(next(self.s.rows())["backlog"])
        with self.assertRaisesRegex(ValueError, "unsafe"):
            n.items(b'<!DOCTYPE rss [<!ENTITY a "test">]><rss><channel/></rss>')

    def test_blocked_feeds_never_retry_across_restarts(self):
        response = deque([403, 429])
        log = n.Logger(self.s, {**FEEDS, "another": "https://else.example/feed"},
                       lambda *_: (response.popleft(), {"Retry-After": "600"}, b""),
                       now=lambda: self.time)
        self.assertTrue(log.poll("toy"))
        self.assertTrue(log.poll("another"))
        self.time += 30 * n.INTERVAL
        second = n.Logger(self.s, log.feeds, log.get, now=lambda: self.time)
        for feed in log.feeds:
            self.assertFalse(second.poll(feed))
        second.heartbeat()
        self.assertEqual(self.s.load("heartbeat.json")["dropped_feeds"], 2)

    def test_cap_stops_before_append_and_final_heartbeat_still_fits(self):
        log = self.logger()
        self.s.cap = self.s.size() + n.CONTROL_RESERVE + 8192 + 5000
        self.responses.append(ok(*((f"item{i}", "A" * 980, None) for i in range(10))))
        with self.assertRaises(n.Full):
            log.poll("toy")
        log.heartbeat(running=0, cap_stop=1)
        self.assertEqual(self.s.load("heartbeat.json")["cap_stop"], 1)
        self.assertEqual(list(self.s.rows()), [])
        self.assertLessEqual(self.s.size(), self.s.cap)

    def test_atom_and_prohibited_link(self):
        feed = b'''<feed xmlns="http://www.w3.org/2005/Atom">
        <entry><id>first</id><title>Example</title><updated>2026-10-10</updated>
        <link rel="self" href="https://toy.example/metadata"/>
        <link href="https://toy.example/report"/></entry>
        <entry><id>drop</id><title>Excluded</title><link href="https://x.nasdaq.com/item"/></entry></feed>'''
        self.assertEqual(list(n.items(feed).values()), [("Example", "https://toy.example/report", "2026-10-10")])

    def test_interrupted_request_is_held_at_restart(self):
        log = self.logger()
        log.get = MagicMock(side_effect=KeyboardInterrupt)
        with self.assertRaises(KeyboardInterrupt):
            log.poll("toy")
        state = self.s.load("state.json")
        self.assertTrue(state["toy"]["pending"])
        self.time += 10 * n.INTERVAL
        restarted = self.logger()
        self.assertFalse(restarted.poll("toy"))
        restarted.heartbeat()
        self.assertEqual(self.s.load("heartbeat.json")["interrupted_feeds"], 1)

    def test_wire_headers_declared_and_conditional(self):
        fake = MagicMock()
        cm = fake.open.return_value.__enter__.return_value
        cm.geturl.return_value = FEEDS["toy"]
        cm.headers.get_content_type.return_value = "application/rss+xml"
        cm.read.return_value = rss()
        cm.status = 200
        with patch.object(n.urllib.request, "build_opener", return_value=fake) as builder:
            get = n.transport("TestReader local-contact")
        self.assertIsInstance(builder.call_args.args[0], n.NoRedirect)
        self.assertEqual(get(FEEDS["toy"], {"etag": '"last"', "modified": "Wed, 07 Jul 2021 01:02:03 GMT"})[0], 200)
        req = fake.open.call_args.args[0]
        self.assertEqual(req.get_header("User-agent"), "TestReader local-contact")
        self.assertEqual(req.get_header("If-none-match"), '"last"')
        self.assertEqual(req.get_header("If-modified-since"), "Wed, 07 Jul 2021 01:02:03 GMT")

    def test_status_prints_heartbeat_numbers_only(self):
        log = self.logger()
        self.tick(log, ok(("one", "Private item", None)), 0)
        log.heartbeat()
        with patch.object(n, "Store", return_value=self.s), patch("sys.argv", ["script", "status"]), \
                patch("builtins.print") as output:
            self.assertEqual(n.main(), 0)
        packed = json.loads(output.call_args.args[0])
        self.assertEqual(packed["rows"], 1)
        self.assertTrue(all(type(v) is int for v in packed.values()))
        self.assertNotIn("Private", str(packed))


if __name__ == "__main__":
    unittest.main()
