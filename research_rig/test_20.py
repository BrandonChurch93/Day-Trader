"""Made-up Plan 20 inputs only."""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from . import common_20 as C


def suite(p):
    class Tests(unittest.TestCase):
        def setUp(self):
            self.p = dict(p, start=0, end=480)
            self.tape = C.Tape(-24, 480)
            for h in range(-24, 480):
                for key, v in dict(open=100, high=101, close=100, volume=1, mark=100).items():
                    self.tape.set(key, h, v)
                if h % 8 == 0:
                    self.tape.funding[h] = 8, -0.001
            self.tape.finish()

        def put(self, key, h, value):
            self.tape.fields[key][h - self.tape.start] = value

        def test_source_compares_prior_close_not_open(self):
            self.put("close", -1, 104)
            self.put("open", 0, 99)
            self.put("close", 23, 101)
            self.put("high", 6, 114)
            s = C.setup(self.tape, 6*60+17, self.p)
            self.assertEqual((s.entry, s.high), (25, 114))
            self.assertNotIn(5, s.signals)

        def test_red_day_wait_and_early_no_trade(self):
            self.assertIsNone(C.setup(self.tape, 60, self.p))
            self.put("close", 71, 99)
            self.assertEqual(C.setup(self.tape, 60, self.p).entry, 73)
            self.put("close", 47, 98)
            self.assertEqual(C.setup(self.tape, 60, self.p).entry, 49)
            self.put("volume", 23, 0)
            self.assertEqual(C.setup(self.tape, 60, self.p).entry, 49)

        def test_hourly_variant_no_lookahead(self):
            self.put("high", 7, 133)
            self.assertEqual(C.setup(self.tape, 6*60+10, self.p, earlier=False).entry, 8)
            self.assertIsNone(C.setup(self.tape, 6*60+10, self.p, earlier=True))
            self.assertEqual(C.setup(self.tape, 6*60+10, self.p, earlier=True, screen=False).entry, 7)
            self.assertEqual(C.setup(self.tape, 6*60, self.p, earlier=False, screen=False).entry, 7)
            with self.assertRaises(LookupError):
                C.setup(self.tape, 6*60, self.p, earlier=True)

        def test_stop_cap_and_worse_open(self):
            s = C.Setup(25, 150, (), 12)
            self.put("high", 26, 125)
            self.assertEqual(C.execution_hours(self.tape, s, self.p), (26, 125, "stop"))
            self.put("open", 26, 130)
            self.put("high", 26, 140)
            t = C.evaluate(self.tape, s, self.p)
            self.assertAlmostEqual(t.price, -0.30)
            self.assertAlmostEqual(t.net(15), -0.30345)

        def test_horizon_uses_open_and_funding_includes_exit(self):
            s = C.Setup(24, 130, (), 4)
            self.put("open", 96, 85)
            self.put("high", 96, 200)
            t = C.evaluate(self.tape, s, self.p)
            self.assertFalse(t.stopped)
            self.assertAlmostEqual(t.price, 0.15)
            self.assertAlmostEqual(t.funding, -0.009)

        def test_missing_funding_never_silently_zero(self):
            s = C.Setup(24, 130, (), 4)
            del self.tape.funding[56]
            self.tape.finish()
            with self.assertRaises(LookupError):
                C.evaluate(self.tape, s, self.p)

        def test_zero_volume_entry_no_fill_stop_skipped_timed_exit_deferred(self):
            s = C.Setup(25, 130, (9,), 4)
            self.put("high", 40, 200)
            for h in (9, 40, 97, 98):
                self.put("volume", h, 0)
            C.evaluate(self.tape, s, self.p, validate_only=True)
            self.assertEqual(C.execution_hours(self.tape, s, self.p), (99, 100, "deferred_time"))
            self.put("volume", 25, 0)
            with self.assertRaises(C.NoFill):
                C.evaluate(self.tape, s, self.p)

        def test_terminal_close_not_internal_gap_and_funding_to_close(self):
            s = C.Setup(25, 130, (), 4)
            self.tape.last_trade = 58
            self.put("close", 58, 90)
            self.tape.funding = {h: x for h, x in self.tape.funding.items() if h <= 58}
            self.tape.finish()
            trade = C.evaluate(self.tape, s, self.p)
            self.assertEqual(trade.exit_reason, "terminal_close")
            self.assertAlmostEqual(trade.price, 0.1)
            self.assertAlmostEqual(trade.funding, -0.004)
            self.put("open", 45, C.NAN)
            with self.assertRaises(LookupError):
                C.evaluate(self.tape, s, self.p)

        def test_trigger_needs_live_candle(self):
            self.put("high", 6, 130)
            for key in ("open", "close", "high"):
                self.put(key, 7, C.NAN)
            self.put("close", 23, 95)
            outcomes = defaultdict(int)
            self.assertEqual(len(list(C.ordinary(self.tape, [], self.p, outcomes))), 0)
            self.assertEqual(outcomes["not_trading_at_trigger"], 1)

        def test_notice_exclusion_and_greedy_dedupe(self):
            for h in (6, 14, 200):
                self.put("high", h, 130)
            for h in (23, 215):
                self.put("close", h, 95)
            self.assertEqual(len(list(C.ordinary(self.tape, [], self.p))), 2)
            self.assertEqual(len(list(C.ordinary(self.tape, [4*60], self.p))), 1)

        def test_planted_edge_passes_and_no_edge_does_not(self):
            pools = {2025: [0.001, -0.001] * 50}
            edge = [(2025, x) for x in [0.039, 0.041] * 20]
            no_edge = [(2025, x) for x in [-0.001, 0.001] * 20]
            self.assertTrue(C.judgment(self.p, edge, pools)["passes"])
            self.assertFalse(C.judgment(self.p, no_edge, pools)["passes"])
            self.assertFalse(C.judgment(self.p, edge, {2026: pools[2025]})["marks"]["placebo"])

        def test_three_outliers_cannot_make_a_pass(self):
            sample = [(2025, -0.01)] * 37 + [(2025, 0.30)] * 3
            outcome = C.judgment(self.p, sample, {2025: [0.0] * 80})
            self.assertTrue(outcome["marks"]["mean"])
            self.assertFalse(outcome["marks"]["trimmed"])

        def test_clock_scan_categorizes_without_float_conversion(self):
            from . import score_20 as S
            start = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp()) // 3600
            m = start * 3_600_000
            with TemporaryDirectory() as tmp:
                path = Path(tmp) / "fixture.zip"
                with ZipFile(path, "w") as z:
                    z.writestr("fixture.csv", f"{m},100,101,99,100,0,{m + 3_599_999}\n")
                counts = defaultdict(int)
                with patch.object(S, "float", side_effect=AssertionError, create=True):
                    S.decode_archive("klines", start, start + 24, path, S.digest(path.read_bytes()), p, counts)
                self.assertEqual(dict(counts), {"klines": 1, "zero_volume": 1})

        def test_validation_failure_leaves_lock_and_result_absent(self):
            from . import score_20 as S
            with TemporaryDirectory() as tmp:
                lock, result = Path(tmp) / "lock", Path(tmp) / "result"

                def refuse():
                    raise S.Refused("P20_FIXTURE", lock)

                with self.assertRaises(S.Refused):
                    S.claim(lock, result, {}, refuse, lambda _: self.fail("scored before claim"))
                self.assertFalse(lock.exists())
                self.assertFalse(result.exists())

    return unittest.defaultTestLoader.loadTestsFromTestCase(Tests)


def calibrate(p):
    # Stylized after-cost trade returns with heavy-tailed shocks and common
    # year regimes. Matching controls share the year shock but not trade noise.
    # This exercises the actual judgment, not the archive loader.
    counts = defaultdict(int)
    for i in range(p["calibration_seeds"]):
        rng = Random(p["calibration_seed"] + i)
        base, pools = [], {}
        year_count = 6
        samples = p["calibration_trades"] // year_count
        for y in range(2020, 2020 + year_count):
            drift = rng.gauss(0, p["calibration_year_sigma"])

            def noise():
                return drift + rng.gauss(0, p["calibration_trade_sigma"]) * (2.0 if rng.random() < 0.08 else 1.0)

            pools[y] = [noise() for _ in range(120)]
            base.extend((y, noise()) for _ in range(samples))
        for edge in p["calibration_edges_pct"]:
            planted = [(y, r + edge / 100) for y, r in base]
            counts[edge] += C.judgment(p, planted, pools)["passes"]
    for edge in p["calibration_edges_pct"]:
        print(f"synthetic net plant {edge}%: {counts[edge]}/{p['calibration_seeds']} all marks")


def run(p, *, calibration):
    if calibration:
        calibrate(p)
        return 0
    return int(not unittest.TextTestRunner(verbosity=2).run(suite(p)).wasSuccessful())
