"""Invented HTTP only. Gate files are always isolated under a temp directory."""
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import io
import json
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from urllib.error import HTTPError

import venue_binance_us as bx

T = datetime(2027, 1, 1, tzinfo=timezone.utc)


class Opener:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = []

    def open(self, req, timeout):
        self.calls.append(req.full_url)
        status, headers = self.replies.pop(0)
        if status != 200:
            raise HTTPError(req.full_url, status, "", headers, io.BytesIO())
        return io.BytesIO(b"[]")


class SharedGate(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "gate" / "cooldown.json"
        self.now = T

    def clock(self):
        return self.now

    def gate(self):
        return bx.Gate(self.path, clock=self.clock)

    def pages(self, opener):
        return bx.PublicPages(opener=opener, sleep=lambda _: None, gate=self.gate(), clock=self.clock)

    def test_429_next_endpoint_other_collector_restart_and_deadline(self):
        opener = Opener((429, {"Retry-After": "75"}), (200, {}))
        old = self.pages(opener)
        other = self.pages(opener)
        old.deadline = T + timedelta(seconds=2)
        with self.assertRaises(bx.Cooldown) as first:
            old.pairs()
        until = T + timedelta(seconds=75)
        self.assertEqual(first.exception.not_before, until)
        self.assertEqual(json.loads(self.path.read_text()), {"not_before_utc": bx.precise_utc(until)})
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.path.parent.stat().st_mode), 0o700)
        self.now = T + timedelta(seconds=1)
        with self.assertRaises(bx.Cooldown):
            old.book(bx.VENUE, "ETH")
        with self.assertRaises(bx.Cooldown):
            other.klines("BTC", T, 2)
        restarted = self.pages(opener)
        self.now = until - timedelta(microseconds=1)
        with self.assertRaises(bx.Cooldown):
            restarted.book(bx.VENUE, "BTC")
        self.assertEqual(len(opener.calls), 1)
        self.now = until
        with self.assertRaisesRegex(bx.Failure, "wake_window_elapsed"):
            old.book(bx.VENUE, "BTC")
        self.assertEqual(restarted.book(bx.VENUE, "BTC"), [])
        self.assertEqual(len(opener.calls), 2)

    def test_http_date_and_missing_invalid_retry_after(self):
        date = T + timedelta(minutes=6)
        for header, expect in (
            (format_datetime(date, usegmt=True), date), (None, T + timedelta(minutes=1)),
            ("nonsense", T + timedelta(minutes=1)), ("0", T + timedelta(seconds=1)),
        ):
            with self.subTest(header=header):
                self.path.unlink(missing_ok=True)
                opener = Opener((429, {"Retry-After": header}))
                with self.assertRaises(bx.Cooldown) as caught:
                    self.pages(opener).book(bx.VENUE, "BTC")
                self.assertEqual(caught.exception.not_before, expect)
                self.assertEqual(len(opener.calls), 1)

    def test_permanent_stop_has_no_expiry_and_refuses_start_and_requests(self):
        for code in bx.BLOCKS:
            with self.subTest(code=code):
                stop = self.path.parent / "stop.json"
                stop.unlink(missing_ok=True)
                self.now = T
                opener = Opener((code, {}))
                with self.assertRaises(bx.Blocked):
                    self.pages(opener).book(bx.VENUE, "BTC")
                self.assertEqual(json.loads(stop.read_text()),
                                 {"host": bx.HOST, "http_status": code, "stopped_utc": bx.precise_utc(T)})
                self.assertEqual(stat.S_IMODE(stop.stat().st_mode), 0o600)
                self.now += timedelta(days=45)
                with self.assertRaises(bx.Refuse):
                    bx.check_start(self.gate())
                with self.assertRaises(bx.Blocked):
                    self.pages(opener).klines("ETH", T, 3)
                self.assertEqual(len(opener.calls), 1)

    def test_lock_covers_observation_and_atomic_429_update(self):
        entered, outcome = threading.Event(), []
        first = self.gate()

        def next_collector():
            entered.set()
            try:
                with self.gate().attempt():
                    outcome.append("sent")
            except bx.Cooldown:
                outcome.append("paused")

        with self.assertRaises(bx.Cooldown), first.attempt():
            other = threading.Thread(target=next_collector)
            other.start()
            self.assertTrue(entered.wait(1))
            first.http_error(429, "15")
        other.join(2)
        self.assertEqual(outcome, ["paused"])

    def test_malformed_gate_fails_closed(self):
        self.gate().check_start()
        self.path.write_text('{"not_before_utc":"not a timestamp"}')
        self.path.chmod(0o600)
        opener = Opener()
        with self.assertRaises(bx.Refuse):
            self.pages(opener).book(bx.VENUE, "BTC")
        self.assertEqual(opener.calls, [])


if __name__ == "__main__":
    unittest.main()
