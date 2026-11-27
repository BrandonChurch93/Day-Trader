"""Invented candles, books and trade prints. Never runs the score command."""
import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import forward_e12 as e
from test_measure_133 import FREEZE, klines

T = datetime(2027, 2, 1, 4, tzinfo=e.UTC)
DEPTH = {"bids": [["99", "10"]], "asks": [["101", "10"]]}


class Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += timedelta(seconds=seconds)


class Pages:
    def __init__(self):
        self.calls = []
        self.pair_states = dict.fromkeys(e.COINS, "NO_USD_PAIR") | {"BTC": "TRADING", "ETH": "TRADING"}
        self.deadline = None
        self.pair_error = None
        self.candle_error = None
        self.prints = []

    def pairs(self):
        self.calls.append(("pairs",))
        if self.pair_error:
            raise self.pair_error
        return self.pair_states

    def candles(self, coin, wake):
        self.calls.append(("candles", coin))
        if coin == self.candle_error:
            raise e.Failure("invalid_candle")
        return klines(wake, [100, 100, {"BTC": 98, "ETH": 90}.get(coin, 80)])

    def depth(self, coin):
        self.calls.append(("depth", coin))
        return DEPTH

    def agg(self, coin, **params):
        self.calls.append(("agg", coin))
        return self.prints


class Recorder(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(temp.cleanup)
        self.off = Path(temp.name) / "e12"
        self.venue = Pages()
        self.cfg, self.fees, _, _ = e.settings()

    def approve(self):
        return patch.object(e.m133, "git", return_value=f"| 230 | E12_START=<frozen build hash> E12_START={FREEZE} |")

    def start(self):
        with self.approve(), patch.object(e.m133, "checked_build", return_value=FREEZE):
            h = e.start(T - timedelta(minutes=10), self.off)
        self.assertEqual(h["first_wake"], e.iso(T))
        self.assertEqual(self.venue.calls, [])

    def record(self, t=T, seconds=5):
        clock = Clock(t + timedelta(seconds=seconds))
        return e.record(clock(), self.venue, self.off, clock=clock, sleep=clock.sleep)

    def rows(self):
        return e.m133.read_log(self.off)

    def test_no_approval_means_no_venue_no_start_and_no_resume(self):
        with patch.object(e.m133, "checked_build", return_value=FREEZE), patch.object(e.m133, "git", return_value=""):
            with self.assertRaises(e.Refuse):
                e.start(T, self.off)
        self.assertFalse(self.off.exists())
        self.start()
        with patch.object(e.m133, "git", return_value=f"| 230 | E12_SCORE={FREEZE} |"):
            with self.assertRaises(e.Refuse):
                self.record()
        self.assertEqual(self.venue.calls, [])

    def test_first_roster_includes_nontrading_and_never_adopts_new_listings(self):
        self.venue.pair_states["BNB"] = "BREAK"
        self.start()
        with self.approve():
            self.record(seconds=4)
            self.assertEqual(self.venue.calls, [])
            wake = self.record()
            self.assertEqual(wake["kind"], "wake")
            self.assertEqual({r["coin"] for r in wake["entries"]}, {"BNB"})
            roster = next(r for r in self.rows() if r["kind"] == "roster")
            self.assertEqual(roster["coins"], ["BNB", "BTC", "ETH"])
            self.venue.pair_states["AAVE"] = "TRADING"
            self.record(T + e.HOUR)
        self.assertNotIn(("candles", "AAVE"), self.venue.calls)
        self.assertEqual(sum(r["kind"] == "roster" for r in self.rows()), 1)

    def test_missing_btc_stops_no_late_discovery(self):
        self.venue.pair_states["BTC"] = "NO_USD_PAIR"
        self.start()
        with self.approve():
            self.assertEqual(self.record()["kind"], "stop")
            self.venue.pair_states["BTC"] = "TRADING"
            self.assertEqual(self.record(T + e.HOUR)["kind"], "stopped")
        self.assertEqual(self.venue.calls, [("pairs",)])
        self.assertEqual(e.alive(self.off)["status"], "STOPPED")

    def test_missed_first_wake_stops_without_discovery(self):
        self.start()
        with self.approve():
            self.assertEqual(self.record(seconds=120)["kind"], "stop")
        self.assertEqual(self.venue.calls, [])

    def test_block_is_terminal_in_first_wake(self):
        self.start()
        self.venue.pair_error = e.Blocked(e.m133.HOST, 451)
        with self.approve():
            self.assertEqual(self.record()["http_status"], 451)
            self.assertEqual(self.record(T + e.HOUR)["kind"], "stopped")
        self.assertEqual(self.venue.calls, [("pairs",)])

    def test_stale_claim_not_retried(self):
        self.start()
        with e.m133.locked(self.off):
            e.m133.append(self.off, self.rows(), kind="claim", wake=e.iso(T))
        with self.approve():
            self.assertEqual(self.record()["kind"], "stop")
        self.assertEqual(self.venue.calls, [])

    def test_exit_before_candles_and_fresh_entry_book(self):
        self.start()
        with self.approve():
            self.record()
            self.venue.calls.clear()
            w = self.record(T + e.HOUR)
        self.assertEqual(self.venue.calls[:5],
                         [("pairs",), ("depth", "ETH"), ("candles", "BTC"), ("candles", "ETH"), ("depth", "ETH")])
        self.assertIn("ETH", w["entry_books"])
        self.assertIn("ETH", w["exit_books"])
        self.assertEqual(w["exits"], ["71-035"])

    def test_candle_failure_voids_entries_not_exits_and_there_is_no_repeat(self):
        self.start()
        with self.approve():
            self.record()
            self.venue.candle_error = "BTC"
            w = self.record(T + e.HOUR)
            self.assertEqual(w["entries"], [])
            self.assertTrue(w["entries_void"])
            self.assertIn("ETH", w["exit_books"])
            before = self.venue.calls[:]
            self.record(T + e.HOUR)
        self.assertEqual(self.venue.calls, before)

    def test_public_file_carries_pooled_aggregates_only(self):
        self.start()
        with self.approve():
            self.record()
            self.record(T + e.HOUR)
        target = self.off / "public.json"
        e.publish(self.off, target)
        out = json.loads(target.read_text())
        self.assertEqual(out["frozen_usd_pairs"], 2)
        self.assertGreater(out["cost_per_side_bp"]["250"]["buy"]["n"], 0)
        for detail in ("ETH", "BTC", "signal_bars", "midpoint", "received", "entry_books", "print_price", "net_mean"):
            self.assertNotIn(detail, json.dumps(out))


class Calculations(unittest.TestCase):
    def setUp(self):
        self.cfg, self.fees, _, _ = e.settings()

    def test_frozen_signals_identical_to_sweep_on_synthetic_panel(self):
        pages = Pages()
        roster = ("BTC", "ETH")
        bars, bad = e.collect_candles(pages, T, roster)
        self.assertFalse(bad)
        rules = e.rules()
        for key in e.ARMS:
            coin, strength = e.decide(T, bars, rules[key], roster)
            self.assertEqual(coin, "ETH")
            self.assertAlmostEqual(strength, -math.log(0.9) + 2 * math.log(0.98))
        self.assertIsNone(e.decide(T, bars, rules[e.JUDGED], ("BTC",)))

    def book(self, raw=DEPTH, seconds=10):
        return e.m133.ticket(raw, e.BINANCE, (), 0) | raw | {
            "received": e.iso(T + timedelta(seconds=seconds)), "taken_s": seconds}

    def test_depth_walk_hard_window_thin_and_stated_fee(self):
        start = self.book()
        late = self.book(seconds=121)
        self.assertEqual(e.settle(start, late, 250, Decimal(2), limit=120), {"reason": "late book"})
        self.assertEqual(e.settle(start, self.book(DEPTH | {"bids": [["99", "1"]]}),
                                  250, Decimal(2), limit=120), {"reason": "exit too thin"})
        self.assertAlmostEqual(e.settle(start, start, 250, Decimal(2), limit=120)["net"],
                               (99 / 101) * (1 - 0.0002) - (1 + 0.0002))
        self.assertEqual(e.fee_bp(self.fees, "BNB"), Decimal(1))

    def test_resting_strict_below_and_unknown_if_gap(self):
        pages = Pages()
        book = self.book()
        ms = e.epoch_ms(e.parse(book["received"]))
        pages.prints = [{"a": 10, "T": ms + 1, "p": "99"}]
        self.assertEqual(e.resting(pages, "ETH", book, self.cfg)["status"], "NOT_FILLED")
        pages.prints.append({"a": 12, "T": ms + 2, "p": "98"})
        self.assertEqual(e.resting(pages, "ETH", book, self.cfg)["status"], "UNKNOWN")
        pages.prints[-1]["a"] = 11
        filled = e.resting(pages, "ETH", book, self.cfg)
        self.assertEqual(filled["status"], "FILLED")
        result = e.rest_marks({"coin": "ETH", "wake": e.iso(T)},
                              {(e.iso(T), "ETH", "entry", 0): book,
                               (e.iso(T), "ETH", "entry", 60): self.book(seconds=70)}, filled, self.cfg)
        self.assertEqual(result["60"]["phase"], "AFTER_FILL")
        self.assertGreater(result["60"]["move_bp"], 0)

    def test_score_preflight_count_or_date_plus_separate_go_and_once(self):
        h = {"freeze": FREEZE}
        with patch.object(e.m133, "git", return_value=f"| 230 | E12_SCORE={FREEZE} |"):
            self.assertTrue(e.score_gate([], h, T, 150, self.cfg)[0])
            with self.assertRaises(e.Refuse):
                e.score_gate([], h, T, 149, self.cfg)
            close = e.parse(self.cfg["last_wake_utc"]) + timedelta(seconds=900)
            self.assertFalse(e.score_gate([], h, close, 0, self.cfg)[0])
            with self.assertRaises(e.Refuse):
                e.score_gate([{"kind": "score"}], h, close, 150, self.cfg)
        with patch.object(e.m133, "git", return_value=f"| 230 | E12_START={FREEZE} |"):
            with self.assertRaises(e.Refuse):
                e.score_gate([], h, T, 150, self.cfg)
        self.assertEqual(e.judge([], self.cfg)["verdict"], "too few to judge")


if __name__ == "__main__":
    unittest.main()
