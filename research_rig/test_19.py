"""Synthetic Plan 19 tests. No real bars, manifests or canonical lock."""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from . import common_19 as C, score_19 as S


def setup(**changes):
    return C.policy(dict(first_date="2023-01-01", last_date="2024-02-01",
                         cme_cut="2023-11-24T21:00:00+00:00", sunday_hour_ny=19,
                         hold_hours=24, funding_hours=8, funding_jitter_seconds=30,
                         judged_bps=5, shown_bps=[1, 10], min_sharpe=1.,
                         min_positive_years=1, placebo_percentile=95, annual_days=365) | changes)


def fixtures(p, planted):
    bars = range(p["start"], p["end"] + 1)
    settlements = {h: 0. for h in bars if h % p["funding_hours"] == 0}
    opens = dict.fromkeys(bars, 100.)
    closes = {h: 100. + .00001 * (h - p["start"]) for h in bars}
    if planted:
        for i, h in enumerate(C.starts(p, 0)):
            opens[h] -= 3. + i % 5
    return {s: C.Tape(opens.copy(), closes.copy(), dict.fromkeys(settlements, 100.),
                      settlements.copy()) for s in C.SYMBOLS}


class Plan19(unittest.TestCase):
    def test_planted_effect_passes_all_marks(self):
        p = setup()
        r = C.measure(fixtures(p, True), p)
        self.assertEqual(len(r["placebo"]["sharpes"]), 167)
        self.assertEqual(r["placebo"]["defined"], 167)
        self.assertTrue(all(r["marks"].values()), r["marks"])
        pair = r["main"]["pair"]
        self.assertGreater(pair["post_cme_weeks"], 0)
        self.assertAlmostEqual(pair["whole"]["net"], pair["price_pnl"] + pair["funding_pnl"] - pair["fees"])
        self.assertEqual(set(r["shown_signals"]), {"long", "one_candle"})

    def test_no_edge_fails_and_fees_are_costs(self):
        p = setup()
        r = C.measure(fixtures(p, False), p)
        self.assertFalse(r["passes"])
        for bps in ("1", "10"):
            self.assertLess(r["shown_costs"][bps]["pair"]["whole"]["net"], 0.)
        self.assertLess(r["shown_costs"]["10"]["pair"]["whole"]["net"],
                        r["shown_costs"]["1"]["pair"]["whole"]["net"])
        self.assertFalse(r["marks"]["sharpe"])
        self.assertFalse(r["marks"]["post_cme"])

    def test_undefined_placebos_never_pass(self):
        p = setup()
        tapes = fixtures(p, False)
        for t in tapes.values():
            t.closes = dict.fromkeys(t.closes, 100.)
        r = C.measure(tapes, p)
        self.assertIsNone(r["main"]["pair"]["whole"]["sharpe"])
        self.assertEqual(r["placebo"]["defined"], 0)
        self.assertIsNone(r["placebo"]["percentile"])
        self.assertFalse(r["marks"]["placebo"])

    def test_new_york_seasonal_clock_and_dst_folds(self):
        p = setup()
        starts = C.starts(p, 0)
        self.assertIn(C.hour("2023-02-06T00:00:00Z"), starts)
        self.assertIn(C.hour("2023-07-02T23:00:00Z"), starts)
        spring = C.starts(p, (2 - p["sunday_hour_ny"]) % C.WEEK)
        self.assertNotIn("2023-03-12", [C.utc(h).astimezone(C.NY).date().isoformat() for h in spring])
        fall = C.starts(p, (1 - p["sunday_hour_ny"]) % C.WEEK)
        self.assertIn(C.hour("2023-11-05T05:00:00Z"), fall)
        self.assertNotIn(C.hour("2023-11-05T06:00:00Z"), fall)
        self.assertEqual(len({tuple(C.starts(p, n)) for n in range(C.WEEK)}), C.WEEK)

    def test_actual_next_candle_open_and_24_hour_close_direction(self):
        p = setup()
        t = fixtures(p, False)[C.SYMBOLS[0]]
        start = C.starts(p, 0)[0]
        end = start + p["hold_hours"]
        t.opens[start - 1] = 110.
        t.opens[start] = 80.
        t.opens[end - 1] = 90.
        t.opens[end] = 100.
        t.opens[end + 1] = 170.
        self.assertEqual(C.direction(t, start, p, "momentum"), 1)
        self.assertEqual(C.direction(t, start, p, "one_candle"), -1)
        r = C.replay([t], p, [start], 0)
        self.assertAlmostEqual(r["whole"]["net"], 100 / 80 - 1)
        t.closes[start - 1] = t.closes[start - p["hold_hours"] - 1]
        self.assertEqual(C.direction(t, start, p, "momentum"), 0)

    def test_funding_exit_not_entry_and_pair_half_cash(self):
        p = setup()
        t, u = fixtures(p, False).values()
        start = C.hour("2023-02-08T00:00:00Z")
        end = start + p["hold_hours"]
        t.rates[start] = .50
        t.rates[end] = .02
        u.closes[start - 1] = u.closes[start - p["hold_hours"] - 1]
        r = C.replay([t, u], p, [start], 0)
        self.assertAlmostEqual(r["funding_pnl"], -.01)
        self.assertAlmostEqual(r["whole"]["net"], -.01)
        t.closes[start - 1] = 1.
        self.assertAlmostEqual(C.replay([t, u], p, [start], 0)["funding_pnl"], .01)

    def test_cme_cut_marks_position_instead_of_assigning_whole_trade(self):
        p = setup()
        t = fixtures(p, False)[C.SYMBOLS[0]]
        cut = p["cut"]
        entry = cut - 3
        t.opens[cut] = 110.
        t.opens[entry + p["hold_hours"]] = 120.
        r = C.replay([t], p, [entry], 0)
        self.assertAlmostEqual(r["before_cme"]["net"], .10)
        self.assertAlmostEqual(r["after_cme"]["net"], 120 / 110 - 1)
        self.assertEqual(r["post_cme_weeks"], 0)

    def test_require_complete_coverage_and_valid_archive_clock(self):
        p = setup()
        tapes = fixtures(p, False)
        self.assertIsNone(next(S.validate_tapes(tapes, p), None))
        t = tapes[C.SYMBOLS[0]]
        start = p["start"]
        t.rates.pop(start)
        self.assertEqual(next(S.validate_tapes(tapes, p)), (C.SYMBOLS[0], "fundingRate", start))
        ms = start * C.HOUR * 1000
        S.add_row(t, "fundingRate", start, start + 24, [str(ms + 1000), "8", "0.0001"], p)
        self.assertEqual(t.rates[start], .0001)
        with self.assertRaisesRegex(C.Incomplete, "clock"):
            S.add_row(t, "fundingRate", start, start + 24, [str(ms + 60000), "8", "0.0001"], p)
        with self.assertRaisesRegex(C.Incomplete, "duplicate"):
            S.add_row(t, "fundingRate", start, start + 24, [str(ms), "8", "0.0001"], p)

    def test_manifest_refuses_overlapping_monthly_and_daily(self):
        p = setup()
        payload = dict(where="replay_19", sha256="a" * 64)
        monthly = "data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2023-01.zip"
        daily = "data/futures/um/daily/klines/BTCUSDT/1h/BTCUSDT-1h-2023-01-01.zip"
        with self.assertRaisesRegex(C.Incomplete, "overlapping"):
            list(S.select({monthly: payload, daily: payload}, p))
        with self.assertRaisesRegex(C.Incomplete, "stops short"):
            S.verify_inventory({}, p)

    def test_draft_stops_before_old_files_or_real_store(self):
        fake = "a" * 40
        with patch.object(S, "git") as git, patch.object(Path, "read_bytes", return_value=b"Status DRAFT.\n"):
            git.side_effect = [fake.encode(), b""] + [b"Status DRAFT.\n"] * len(S.PINNED)
            with self.assertRaisesRegex(C.Incomplete, "remains a draft"):
                S.authorize(fake, "b" * 64)

    def test_failed_claim_is_not_reset_and_success_is_consumed(self):
        with TemporaryDirectory() as d:
            lock, result = Path(d) / "lock", Path(d) / "result"

            def fail(_prepared):
                raise RuntimeError("invented")

            with self.assertRaises(RuntimeError):
                S.claim(lock, result, {}, lambda: None, fail)
            self.assertIn('"failed"', lock.read_text())
            self.assertFalse(result.exists())
            with self.assertRaisesRegex(S.Refused, "P19_CONSUMED"):
                S.claim(lock, result, {}, lambda: None, lambda _: {})
            new_lock = lock.with_name("other synthetic lock")
            S.claim(new_lock, result, {}, lambda: {"made_up": 1}, lambda prepared: prepared)
            self.assertIn('"completed"', new_lock.read_text())
            self.assertIn('"made_up"', result.read_text())
            with self.assertRaisesRegex(S.Refused, "P19_CONSUMED"):
                S.claim(new_lock, result, {}, lambda: None, lambda _: {})

    def test_prepare_failure_does_not_claim_and_scoring_starts_after_claim(self):
        with TemporaryDirectory() as d:
            lock, result = Path(d) / "lock", Path(d) / "result"

            def fail():
                self.assertFalse(lock.exists())
                raise S.Refused("P19_LOAD_REFUSED", Path(d) / "invented.zip")

            def prepare():
                self.assertFalse(lock.exists())
                return 42

            def calculate(prepared):
                self.assertIn('"consumed"', lock.read_text())
                return {"prepared": prepared}

            with self.assertRaisesRegex(S.Refused, "P19_LOAD_REFUSED"):
                S.claim(lock, result, {}, fail, calculate)
            self.assertFalse(lock.exists())
            self.assertFalse(result.exists())
            S.claim(lock, result, {}, prepare, calculate)
            self.assertIn('"prepared": 42', result.read_text())

    def test_bad_payload_load_and_cli_refusal_are_path_only(self):
        p = setup()
        z = Path("/synthetic/fake.zip")
        rec = (z, "a" * 64, C.SYMBOLS[0], "klines", p["start"], p["end"])
        with patch.object(S.A, "read_pinned", side_effect=ValueError("synthetic-private-value")):
            with self.assertRaises(S.Refused) as seen:
                S.load([rec], p)
        self.assertEqual(seen.exception.code, "P19_LOAD_REFUSED")
        self.assertEqual(seen.exception.path, z)
        out, err = StringIO(), StringIO()
        with (patch.object(S, "go", side_effect=seen.exception),
              patch("sys.argv", ["score_19", "--go"]),
              redirect_stdout(out), redirect_stderr(err), self.assertRaises(SystemExit)):
            S.main()
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(err.getvalue(), "P19_LOAD_REFUSED /synthetic/fake.zip\n")
