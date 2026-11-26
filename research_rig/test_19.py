"""Synthetic Plan 19 tests. No real bars, manifests or canonical lock."""
from contextlib import redirect_stderr, redirect_stdout
from io import BytesIO, StringIO
import json
from math import expm1, log1p
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import zipfile

from . import common_19 as C, score_19 as S


def setup(**changes):
    return C.policy(dict(first_date="2023-01-01", last_date="2024-02-01",
                         cme_cut="2023-11-24T21:00:00+00:00", sunday_hour_ny=19,
                         hold_hours=24, funding_hours=8, funding_jitter_seconds=30,
                         judged_bps=5, shown_bps=[1, 10], min_sharpe=1.,
                         min_positive_years=1, min_trade_pct=90, placebo_percentile=95,
                         annual_days=365, calibration_seed=19001, calibration_seeds=20,
                         calibration_edges_bps=[0, 10, 20, 40],
                         calibration_hourly_common_sigma=.002,
                         calibration_hourly_idio_sigma=[.0015, .0025],
                         calibration_funding_bps=.5) | changes)


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


def tiny_archive_set(p, volume_hour, volume):
    """One invented ZIP per coin and series, with full coverage of a short sample."""
    records, blobs = [], {}
    for symbol in C.SYMBOLS:
        for kind in sorted(S.FOLDERS):
            lines = []
            for hour in range(p["start"], p["end"]):
                ms = hour * C.HOUR * 1000
                if kind == "fundingRate":
                    if hour % p["funding_hours"] == 0:
                        lines.append(f"{ms},{p['funding_hours']},0\n")
                else:
                    qty = volume if symbol == "ETHUSDT" and hour == volume_hour and kind == "klines" else 1
                    lines.append(f"{ms},100,101,99,100,{qty},{ms + C.HOUR * 1000 - 1}\n")
            buffer = BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr("synthetic.csv", "".join(lines))
            path = Path(f"/synthetic/{symbol}/{kind}.zip")
            blobs[path] = buffer.getvalue()
            records.append((path, S.digest(blobs[path]), symbol, kind, p["start"], p["end"]))
    return records, blobs


def noisy(p, seed, edge_bps):
    rng = Random(seed)
    entries = set(C.starts(p, 0))
    tapes = [C.Tape({}, {}, {}, {}) for _ in C.SYMBOLS]
    levels, drifts = [100.] * len(tapes), [0.] * len(tapes)
    stop = p["start"]
    for h in range(p["start"], p["end"] + 1):
        common = rng.gauss(0, p["calibration_hourly_common_sigma"])
        for i, tape in enumerate(tapes):
            noise = common + rng.gauss(0, p["calibration_hourly_idio_sigma"][i])
            levels[i] *= 1 + expm1(noise + (drifts[i] if h <= stop else 0.))
            if h > p["start"]:
                tape.closes[h - 1] = levels[i]
            if h == p["end"]:
                continue
            tape.opens[h] = levels[i]
            if h % p["funding_hours"] == 0:
                tape.marks[h] = levels[i]
                tape.rates[h] = p["calibration_funding_bps"] / 10000
            if h in entries:
                side = C.direction(tape, h, p, "momentum")
                drifts[i] = log1p(side * edge_bps / 10000) / p["hold_hours"]
        if h in entries:
            stop = h + p["hold_hours"]
    return dict(zip(C.SYMBOLS, tapes))


def calibrate(p):
    for edge in p["calibration_edges_bps"]:
        passes = 0
        for i in range(p["calibration_seeds"]):
            S.memory()
            tapes = noisy(p, p["calibration_seed"] + i, edge)
            result = C.measure(tapes, p, check=S.memory)
            if (len(result["placebo"]["sharpes"]) != C.WEEK - 1 or result["placebo"]["undefined"]
                    or result["placebo"]["failed"]):
                raise AssertionError("synthetic calibration needs a complete finite placebo grid")
            passes += result["passes"]
        print(f"{edge} bps gross plant: {passes}/{p['calibration_seeds']} clear all five marks", flush=True)


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

    def test_sparse_fixture_passes_old_marks_but_fails_breadth(self):
        p = setup(first_date="2020-01-01", last_date="2026-10-31",
                  cme_cut="2026-05-29T21:00:00Z", min_positive_years=4)
        tapes = fixtures(p, False)
        chosen = []
        for year, n in ((2020, 2), (2021, 2), (2022, 1), (2023, 1), (2026, 1)):
            chosen.extend([h for h in C.starts(p, 0) if
                           (C.utc(h).year, C.utc(h).month) == (year, 7)][:n])
        for h in C.starts(p, 0):
            for tape in tapes.values():
                if h in chosen:
                    tape.opens[h + 1] = 100 * (1 + p["judged_bps"] / 10000)
                    tape.opens[h + p["hold_hours"]] = 101.2
                else:
                    tape.closes[h - 1] = tape.closes[h - p["hold_hours"] - 1]
        r = C.measure(tapes, p)
        pair = r["main"]["pair"]
        self.assertEqual((pair["traded_weeks"], pair["post_cme_traded_weeks"]), (7, 1))
        self.assertTrue(all(v for k, v in r["marks"].items() if k != "breadth"), r["marks"])
        self.assertFalse(r["marks"]["breadth"])
        self.assertFalse(r["passes"])
        self.assertTrue(C.breadth(dict(scheduled_weeks=10, traded_weeks=9,
                                      post_cme_weeks=10, post_cme_traded_weeks=9), 90))
        self.assertFalse(C.breadth(dict(scheduled_weeks=10, traded_weeks=9,
                                       post_cme_weeks=10, post_cme_traded_weeks=8), 90))

    def test_late_missing_and_stale_candle_cannot_store_signal_close(self):
        p = setup()
        start = C.starts(p, 0)[0]
        h = start - 1
        ms = h * C.HOUR * 1000
        close_ms = ms + C.HOUR * 1000 - 1
        prefix = [str(ms), "100", "130", "99", "130", "20"]
        tape = C.Tape({}, {h - p["hold_hours"]: 100.}, {}, {})
        for row in (prefix, prefix + [str(close_ms - 1)],
                    prefix + [str(close_ms + C.HOUR * 1000)]):
            with self.assertRaises(C.Incomplete):
                S.add_row(tape, "klines", h, h + 1, row, p)
            self.assertNotIn(h, tape.closes)
            with self.assertRaises(KeyError):
                C.direction(tape, start, p, "momentum")
        S.add_row(tape, "klines", h, h + 1,
                  [str(ms * 1000), *prefix[1:], str(close_ms * 1000 + 999)], p)
        self.assertEqual(C.direction(tape, start, p, "momentum"), 1)
        with self.assertRaises(C.Incomplete):
            S.add_row(tape, "markPriceKlines", h, h + 1, prefix + [str(close_ms + 1)], p)

    def test_zero_volume_midwindow_candle_loads_for_path_marking(self):
        p = setup(first_date="2023-02-03", last_date="2023-02-07", cme_cut="2023-02-04T00:00Z")
        entry, = C.starts(p, 0)
        h = entry + 2
        records, blobs = tiny_archive_set(p, h, 0)
        with patch.object(S.A, "read_pinned", side_effect=lambda path, _: blobs[path]):
            tapes = S.load(records, p)
        self.assertEqual(tapes["ETHUSDT"].zero_trade, {h})
        self.assertEqual(tapes["BTCUSDT"].zero_trade, set())
        self.assertIn(h, tapes["ETHUSDT"].opens)
        self.assertIsNone(next(S.validate_tapes(tapes, p), None))

    def test_zero_volume_judged_entry_signal_or_exit_refuse_before_claim(self):
        p = setup(first_date="2023-02-03", last_date="2023-02-07", cme_cut="2023-02-04T00:00Z")
        entry, = C.starts(p, 0)
        candles = C.trade_candle_roles(entry, p)
        for h in (*candles["entry"], *candles["signal"], *candles["exit"]):
            with self.subTest(hour=h), TemporaryDirectory() as d:
                records, blobs = tiny_archive_set(p, h, 0)
                lock, result = Path(d) / "lock", Path(d) / "result"
                with (patch.object(S.A, "read_pinned", side_effect=lambda path, _: blobs[path]),
                      self.assertRaises(S.Refused) as refusal):
                    S.claim(lock, result, {}, lambda: S.load(records, p),
                            lambda _: self.fail("refused load reached scoring"))
                self.assertEqual(refusal.exception.code, "P19_LOAD_REFUSED")
                self.assertEqual(refusal.exception.path, Path("/synthetic/ETHUSDT/klines.zip"))
                self.assertFalse(lock.exists())
                self.assertFalse(result.exists())

    def test_negative_volume_midwindow_still_refuses(self):
        p = setup(first_date="2023-02-03", last_date="2023-02-07", cme_cut="2023-02-04T00:00Z")
        entry, = C.starts(p, 0)
        records, blobs = tiny_archive_set(p, entry + 2, -1)
        with (patch.object(S.A, "read_pinned", side_effect=lambda path, _: blobs[path]),
              self.assertRaises(S.Refused) as refusal):
            S.load(records, p)
        self.assertEqual(refusal.exception.code, "P19_LOAD_REFUSED")
        self.assertEqual(refusal.exception.path, Path("/synthetic/ETHUSDT/klines.zip"))

    def test_placebo_and_per_coin_zero_volume_report(self):
        p = setup()
        h = C.starts(p, 0)[1] + 2
        tapes = fixtures(p, True)
        for tape in tapes.values():
            tape.zero_trade.add(h)
        r = C.measure(tapes, p)
        for stats in r["zero_volume_trade_candles"].values():
            self.assertEqual(stats, dict(count=1, utc_open_stamps=[C.utc(h).isoformat()]))
        self.assertEqual(r["placebo"]["zero_volume_touched_windows"], 4)
        self.assertEqual(r["placebo"]["zero_volume_touched_by_role"],
                         {"signal": 2, "entry": 1, "exit": 1})

    def test_shown_only_bankruptcy_does_not_discard_judged_marks(self):
        p = setup()
        tapes = fixtures(p, True)
        h = C.starts(p, 0)[0]
        for tape in tapes.values():
            tape.opens[h - 1] = 110.
            tape.opens[h + 2] = 400.
        r = C.measure(tapes, p)
        self.assertIn("whole", r["main"]["pair"])
        self.assertEqual(r["shown_signals"]["one_candle"]["pair"], {"refusal": "NONPOSITIVE_EQUITY"})
        self.assertGreater(r["placebo"]["defined"], 0)
        self.assertEqual(len(r["marks"]), 5)

    def test_judged_bankruptcy_is_a_failed_result_and_placebos_rank_low(self):
        p = setup()
        tapes = fixtures(p, True)
        h = C.starts(p, 0)[0]
        for tape in tapes.values():
            tape.closes[h - 1] = 80.
            tape.closes[h] = 79.  # The next start-hour placebo also shorts before the spike.
            tape.opens[h + 2] = 400.
        r = C.measure(tapes, p)
        self.assertEqual(r["main"]["pair"], {"refusal": "NONPOSITIVE_EQUITY"})
        self.assertEqual(r["marks"], dict.fromkeys(C.MARKS, False))
        self.assertFalse(r["passes"])
        self.assertTrue(r["placebo"]["failed"])
        self.assertTrue(all(r["placebo"]["sharpes"][k] is None for k in r["placebo"]["failed"]))
        self.assertEqual(C.placebo_threshold([2., 3.], 2, 95)[1], "finite")
        self.assertAlmostEqual(C.placebo_threshold([2., 3.], 2, 95)[0], 2.85)
        self.assertEqual(C.placebo_threshold([3.], 166, 95), (None, "below_all_finite"))
        with TemporaryDirectory() as d:
            lock, result = Path(d) / "synthetic-lock", Path(d) / "synthetic-result"
            S.claim(lock, result, {}, lambda: None, lambda _: r)
            self.assertEqual(json.loads(result.read_text())["marks"], dict.fromkeys(C.MARKS, False))
            self.assertIn('"completed"', lock.read_text())

    def test_noisy_panel_is_seeded_distinct_and_signed(self):
        p = setup()
        a = noisy(p, p["calibration_seed"], 0)
        b = noisy(p, p["calibration_seed"], 40)
        first = C.starts(p, 0)[0]
        self.assertEqual(a[C.SYMBOLS[0]].opens[first], b[C.SYMBOLS[0]].opens[first])
        self.assertNotEqual(a[C.SYMBOLS[0]].opens, a[C.SYMBOLS[1]].opens)
        self.assertEqual({C.direction(a[C.SYMBOLS[0]], h, p, "momentum") for h in C.starts(p, 0)}, {-1, 1})
        for symbol in C.SYMBOLS:
            side = C.direction(a[symbol], first, p, "momentum")
            end = first + p["hold_hours"]
            self.assertAlmostEqual(b[symbol].opens[end] / a[symbol].opens[end], 1 + side * .004)

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
