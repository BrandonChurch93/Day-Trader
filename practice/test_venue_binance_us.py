"""Invented HTTP only. Gate files are always isolated under a temp directory."""
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import io
import json
from multiprocessing import get_context
import os
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import URLError
from urllib.error import HTTPError

import venue_binance_us as bx

T = datetime(2027, 1, 1, tzinfo=timezone.utc)


def crash_during_request(path, generation):
    with bx.Gate(path).attempt(generation=generation):
        os._exit(0)


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
        self.generation = self.gate().check_start()

    def clock(self):
        return self.now

    def gate(self):
        return bx.Gate(self.path, clock=self.clock)

    def pages(self, opener):
        return bx.PublicPages(opener=opener, sleep=lambda _: None, gate=self.gate(), clock=self.clock,
                              generation=self.generation)

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
                self.generation = self.gate().check_start()
                opener = Opener((code, {}))
                with self.assertRaises(bx.Blocked):
                    self.pages(opener).book(bx.VENUE, "BTC")
                self.assertEqual(json.loads(stop.read_text()),
                                 {"host": bx.HOST, "http_status": code, "stopped_utc": bx.precise_utc(T)})
                self.assertEqual(stat.S_IMODE(stop.stat().st_mode), 0o600)
                self.now += timedelta(days=45)
                with self.assertRaises(bx.Refuse):
                    bx.check_start(self.gate())
                with self.assertRaises(bx.GateGeneration):
                    self.pages(opener).klines("ETH", T, 3)
                self.assertEqual(len(opener.calls), 1)

    def test_lock_covers_observation_and_atomic_429_update(self):
        entered, outcome = threading.Event(), []
        first = self.gate()

        def next_collector():
            entered.set()
            try:
                gate = self.gate()
                with gate.attempt(generation=self.generation):
                    outcome.append("sent")
                    gate.reply_received()
            except bx.Cooldown:
                outcome.append("paused")

        with self.assertRaises(bx.Cooldown), first.attempt(generation=self.generation):
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

    def test_marker_write_failure_does_not_send(self):
        opener = Opener()
        pages = self.pages(opener)
        original = bx.Gate.write

        def fault(path, value):
            if path.name == bx.INFLIGHT:
                raise OSError("invented disk error")
            original(path, value)

        with patch.object(pages.gate, "write", side_effect=fault), self.assertRaises(bx.GateStorage) as caught:
            pages.book(bx.VENUE, "BTC")
        self.assertEqual(caught.exception.reason, "gate_storage")
        self.assertEqual(opener.calls, [])

    def test_429_write_failure_keeps_marker_and_is_terminal(self):
        opener = Opener((429, {"Retry-After": "75"}))
        pages = self.pages(opener)
        original = bx.Gate.write

        def fault(path, value):
            if path == self.path:
                raise OSError("invented disk error")
            original(path, value)

        with patch.object(pages.gate, "write", side_effect=fault), self.assertRaises(bx.GateStorage):
            pages.book(bx.VENUE, "BTC")
        marker = self.path.parent / bx.INFLIGHT
        self.assertEqual(json.loads(marker.read_text())["generation"], self.generation)
        self.assertEqual(stat.S_IMODE(marker.stat().st_mode), 0o600)
        with self.assertRaises(bx.GateUncertain):
            self.pages(opener).klines("ETH", T, 3)
        with self.assertRaises(bx.GateUncertain):
            self.gate().check_start()
        self.assertEqual(len(opener.calls), 1)

    def test_crashed_process_marker_blocks_sibling_and_restart_even_much_later(self):
        process = get_context("fork").Process(target=crash_during_request, args=(self.path, self.generation))
        process.start()
        process.join(5)
        self.assertEqual(process.exitcode, 0)
        marker = self.path.parent / bx.INFLIGHT
        self.assertEqual(json.loads(marker.read_text())["pid"], process.pid)
        self.now += timedelta(days=30)
        opener = Opener()
        with self.assertRaises(bx.GateUncertain):
            self.pages(opener).book(bx.VENUE, "ETH")
        with self.assertRaises(bx.GateUncertain):
            self.gate().check_start()
        self.assertEqual(opener.calls, [])

    def test_explicitly_unsent_does_not_checkpoint_or_reset(self):
        gate = self.gate()
        self.no_reply(TimeoutError("invented"), self.pages(Opener()))
        self.now += timedelta(seconds=60)
        with gate.attempt(generation=self.generation):
            gate.cancel_unsent()
        self.assertFalse((self.path.parent / bx.INFLIGHT).exists())
        self.assertEqual(self.read_streak(), 1)

    def no_reply(self, error, pages):
        with patch.object(pages.opener, "open", side_effect=error) as send, self.assertRaises(bx.Cooldown) as caught:
            pages.book(bx.VENUE, "ETH")
        send.assert_called_once()
        return caught.exception.not_before

    def read_streak(self):
        return json.loads((self.path.parent / bx.NO_STATUS_STREAK).read_text())["consecutive"]

    def test_no_status_timeout_cools_then_sibling_proceeds_without_stale_marker(self):
        failing = self.pages(Opener())
        failing.deadline = T + timedelta(seconds=20)
        until = self.no_reply(TimeoutError("invented before headers"), failing)
        self.assertEqual(until, T + timedelta(seconds=60))
        self.assertEqual(json.loads(self.path.read_text()), {"not_before_utc": bx.precise_utc(until)})
        self.assertFalse((self.path.parent / bx.INFLIGHT).exists())
        self.assertEqual(self.read_streak(), 1)
        self.assertEqual(self.gate().check_start(), self.generation)
        opener = Opener((200, {}))
        sibling = self.pages(opener)
        self.now = until - timedelta(microseconds=1)
        with self.assertRaises(bx.Cooldown):
            sibling.book(bx.VENUE, "BTC")
        self.assertEqual(opener.calls, [])
        self.now = until
        with self.assertRaisesRegex(bx.Failure, "wake_window_elapsed"):
            failing.book(bx.VENUE, "ETH")
        self.assertEqual(sibling.book(bx.VENUE, "BTC"), [])
        self.assertEqual(self.read_streak(), 0)

    def test_third_shared_no_status_is_fifteen_minutes_then_http_reply_resets(self):
        for i, (err, seconds) in enumerate((
            (TimeoutError("invented timeout"), 60),
            (URLError("invented DNS"), 60),
            (ConnectionResetError("invented reset"), 900),
            (TimeoutError("invented subsequent timeout"), 900),
        )):
            with self.subTest(attempt=i):
                until = self.no_reply(err, self.pages(Opener()))
                self.assertEqual((until - self.now).total_seconds(), seconds)
                self.assertEqual(self.read_streak(), min(i + 1, 3))
                self.assertFalse((self.path.parent / bx.INFLIGHT).exists())
                self.now = until
        # A non-success status is still an HTTP reply.
        pages = self.pages(Opener((404, {})))
        with self.assertRaisesRegex(bx.Failure, "http_404"):
            pages.book(bx.VENUE, "BTC")
        self.assertEqual(self.read_streak(), 0)
        until = self.no_reply(TimeoutError("invented after reset"), self.pages(Opener()))
        self.assertEqual((until - self.now).total_seconds(), 60)

    def test_known_http_status_with_body_timeout_resets_streak(self):
        class TimeoutBody(io.BytesIO):
            def read(self, *_):
                raise TimeoutError("invented after headers")

        self.now = self.no_reply(TimeoutError("invented before headers"), self.pages(Opener()))
        pages = self.pages(Opener())
        with patch.object(pages.opener, "open", return_value=TimeoutBody()), \
                self.assertRaisesRegex(bx.Failure, "^timeout$"):
            pages.book(bx.VENUE, "ETH")
        self.assertEqual(self.read_streak(), 0)
        self.assertFalse((self.path.parent / bx.INFLIGHT).exists())

    def test_no_status_cooldown_write_failure_is_terminal_and_retains_marker(self):
        pages = self.pages(Opener())
        original = bx.Gate.write

        def fault(path, value):
            if path == self.path:
                raise OSError("invented cooldown persistence failure")
            original(path, value)

        with patch.object(pages.gate, "write", side_effect=fault), \
                patch.object(pages.opener, "open", side_effect=TimeoutError("invented live fault")), \
                self.assertRaises(bx.GateStorage):
            pages.book(bx.VENUE, "ETH")
        self.assertTrue((self.path.parent / bx.INFLIGHT).exists())
        with self.assertRaises(bx.GateUncertain):
            self.gate().check_start()

    def test_lost_generation_cannot_initialize_zero_even_on_restart(self):
        counter = self.path.parent / bx.GENERATION
        counter.unlink()
        opener = Opener()
        with self.assertRaises(bx.GateStorage):
            self.pages(opener).book(bx.VENUE, "ETH")
        with self.assertRaises(bx.GateStorage):
            self.gate().check_start()
        self.assertFalse(counter.exists())
        self.assertEqual(opener.calls, [])

    def test_gate_io_during_policy_read_is_terminal_before_request(self):
        pages = self.pages(Opener())
        original = bx.Gate.read

        def fault(path):
            if path.name == bx.GENERATION:
                raise PermissionError("invented gate read fault")
            return original(path)

        with patch.object(pages.gate, "read", side_effect=fault), self.assertRaises(bx.GateStorage):
            pages.book(bx.VENUE, "BTC")
        self.assertEqual(pages.opener.calls, [])


if __name__ == "__main__":
    unittest.main()
