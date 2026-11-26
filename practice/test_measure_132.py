"""Invented tests: no network and no real logger directory."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
import urllib.error

import measure_132 as m


class Pages:
    def __init__(self):
        self.calls = []
        self.block = False
        self.fail_coin = None
        self.status = dict.fromkeys(m.COINS, "TRADING")

    def pairs(self):
        self.calls.append("pairs")
        return self.status

    def candles(self, wake):
        self.calls.append("candles")
        end = int(m.hour(wake).timestamp())
        return [[end - 3600, 1, 1, 901, 98, 1], [end - 7200, 1, 1, 1, 100, 1]]

    def book(self, venue, coin):
        self.calls.append((venue, coin))
        if self.block and venue == "Binance.US":
            raise m.Blocked(m.VENUES[venue], 403)
        if coin == self.fail_coin:
            raise m.Failure("timeout")
        return {"bids": [["100", "100"]], "asks": [["100", "100"]]}


class Logger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.off = Path(self.tmp.name) / "private"
        self.pages = Pages()
        self.now = datetime(2030, 1, 1, 22, 15, tzinfo=timezone.utc)
        self.header = m.start(self.off, self.pages, self.clock)
        self.first = m.parse(self.header["first_wake"])

    def clock(self):
        return self.now

    def test_schedule_pins_permissions_void_and_no_repeat(self):
        self.assertEqual(self.first, self.now.replace(hour=23, minute=0, second=10))
        self.assertEqual(m.parse(self.header["last_wake"]) - self.first, 719 * m.HOUR)
        self.assertEqual(set(self.header["sha256"]), {"plan", "logger", "config_block"})
        self.assertEqual(stat.S_IMODE(self.off.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.off / "log.jsonl").stat().st_mode), 0o600)
        self.now = self.first + m.WINDOW
        m.record(self.off, self.pages, self.clock)
        self.assertEqual(self.pages.calls, ["pairs"])
        self.assertEqual(m.read_log(self.off)[-1]["kind"], "void")
        self.now = self.first + m.HOUR
        m.record(self.off, self.pages, self.clock)
        self.assertEqual(len(self.pages.calls), 42)
        m.record(self.off, self.pages, self.clock)
        self.assertEqual(len(self.pages.calls), 42)
        self.assertEqual([r["kind"] for r in m.read_log(self.off)], ["header", "pairs", "void", "begin", "wake"])

    def test_abort_on_403_and_cannot_resume(self):
        self.now = self.first
        self.pages.block = True
        with self.assertRaisesRegex(m.Refuse, "api.binance.us.*403"):
            m.record(self.off, self.pages, self.clock)
        self.assertEqual(self.pages.calls, ["pairs", "candles", ("Coinbase", "AAVE"), ("Binance.US", "AAVE")])
        self.now += m.HOUR
        with self.assertRaisesRegex(m.Refuse, "already stopped"):
            m.record(self.off, self.pages, self.clock)
        stop = m.report(self.off, "alive", self.clock)["stop"]
        self.assertEqual(stop, {"host": "api.binance.us", "http_status": 403})

    def test_tail_tamper(self):
        f = self.off / "log.jsonl"
        f.write_bytes(f.read_bytes().replace(b"TRADING", b"UNTRADING", 1))
        with self.assertRaisesRegex(m.Refuse, "chain broken"):
            m.read_log(self.off)

    def test_read_before_end_and_public_only_aggregate(self):
        self.now = self.first + m.HOUR
        self.pages.fail_coin = "BTC"
        m.record(self.off, self.pages, self.clock)
        with self.assertRaisesRegex(m.Refuse, "last wake has not passed"):
            m.report(self.off, "read", self.clock)
        out = m.report(self.off, "publish", self.clock)
        self.assertEqual(out, json.loads((self.off / "M132_log.json").read_text()))
        self.assertEqual(stat.S_IMODE((self.off / "M132_log.json").stat().st_mode), 0o600)
        self.assertEqual(out["book_counts"]["Coinbase"]["timeout"], 1)
        self.assertEqual(out["costs"]["Binance.US"]["25"]["buy"]["n"], 19)
        self.assertNotIn("AAVE", json.dumps(out))
        self.assertNotIn("log_return", json.dumps(out))
        self.now = m.parse(self.header["last_wake"]) + m.WINDOW
        final = m.report(self.off, "read", self.clock)
        self.assertEqual(len(final["table"]), 240)
        self.assertEqual(final["wake_counts"]["void"], 719)
        self.assertEqual(final["decision"]["main_cost_line_bp"], 75)

    def test_crash_claim_void_without_reissue(self):
        self.now = self.first
        with m.locked(self.off):
            rows = m.read_log(self.off)
            m.append(self.off, rows, kind="begin", wake=m.iso(self.first), made_utc=m.iso(self.now))
        m.record(self.off, self.pages, self.clock)
        self.assertEqual(self.pages.calls, ["pairs"])
        self.assertEqual(m.read_log(self.off)[-1]["reason"], "incomplete_attempt_not_retried")

    def test_25_paired_midnights_and_both_sides_gate_15_coins(self):
        def side(value):
            return {"status": "ok", "cost_bp": str(value)} if value is not None else {"status": "too thin"}

        rows = [self.header]
        for i in range(25):
            books = {c: {"status": "ok", "sizes": {"250": {
                "buy": side(25), "sell": side(25 if j < 15 else 26)}}} for j, c in enumerate(m.COINS)}
            rows.append({"kind": "wake", "wake": m.iso(self.first + m.HOUR + timedelta(days=i)),
                         "bitcoin": {"status": "missing_adjacent_candle"}, "books": {"Binance.US": books}})
        out = m.summarize(rows, full=True)
        self.assertEqual(out["decision"]["qualifying_coins"], m.COINS[:15])
        self.assertTrue(out["decision"]["met"])
        rows[-1]["books"]["Binance.US"][m.COINS[14]]["sizes"]["250"]["sell"] = side(None)
        out = m.summarize(rows, full=True)
        self.assertFalse(out["decision"]["met"])
        self.assertEqual(out["decision"]["paired_midnights_by_coin"][m.COINS[14]], 24)


class Arithmetic(unittest.TestCase):
    def test_book_walk_both_wire_formats(self):
        for venue, fee, extra in (("Coinbase", 60, ["1"]), ("Binance.US", 2, [])):
            with self.subTest(venue=venue):
                quote = m.ticket({"bids": [["98", "5"] + extra, ["99", "1"] + extra],
                                  "asks": [["102", "5"] + extra, ["101", "1"] + extra]}, [25, 250], fee)
                self.assertEqual(D(quote["midpoint"]), D(100))
                self.assertEqual(D(quote["sizes"]["25"]["buy"]["cost_bp"]), 100 + fee)
                self.assertEqual(D(quote["sizes"]["25"]["sell"]["cost_bp"]), 100 + fee)
                buy, sell = quote["sizes"]["250"]["buy"], quote["sizes"]["250"]["sell"]
                self.assertEqual(D(buy["fill_price"]), D(250) / (1 + D(149)/102))
                self.assertEqual(D(sell["fill_price"]), D(250) / (1 + D(151)/98))

    def test_thin_one_side_and_no_price(self):
        book = {"bids": [["99", "1"]], "asks": [["101", "5"]]}
        quote = m.ticket(book, [25, 250], 1)
        self.assertEqual(quote["sizes"]["250"]["sell"], {"status": "too thin"})
        self.assertEqual(D(quote["sizes"]["250"]["buy"]["cost_bp"]), 101)

    def test_exact_closed_candle_and_nearest_rank(self):
        wake = datetime(2030, 1, 2, 0, 0, 10, tzinfo=timezone.utc)
        end = int(m.hour(wake).timestamp())
        rows = Pages().candles(wake) + [[end, 1, 1, 1, 120, 1]]
        self.assertTrue(m.candle_signal(rows, wake, 0.015)["drop"])
        with self.assertRaisesRegex(m.Failure, "missing_adjacent_candle"):
            m.candle_signal(rows[::2], wake, 0.015)
        self.assertEqual(m.stats(list(map(D, range(1, 11)))), {"n": 10, "median_bp": 5.5, "p90_bp": 9})

    def test_transport_backoff_and_refusal_no_real_http(self):
        class Opener:
            def __init__(self, statuses):
                self.statuses = iter(statuses)
                self.calls = []

            def open(self, req, timeout):
                self.calls.append(req.full_url)
                status = next(self.statuses)
                if status == 200:
                    return io.BytesIO(b"{}")
                raise urllib.error.HTTPError(req.full_url, status, "invented", {}, None)

        tick = [0.0]
        sleeps = []

        def sleep(seconds):
            sleeps.append(seconds)
            tick[0] += seconds

        opener = Opener([429, 429, 200, 403])
        pages = m.PublicPages(opener, sleep, lambda: tick[0])
        self.assertEqual(pages.book("Binance.US", "BTC"), {})
        self.assertEqual(len(set(opener.calls)), 1)
        self.assertIn(1, sleeps)
        self.assertIn(2, sleeps)
        with self.assertRaises(m.Blocked):
            pages.book("Binance.US", "BTC")
        self.assertEqual(len(opener.calls), 4)


if __name__ == "__main__":
    unittest.main()
