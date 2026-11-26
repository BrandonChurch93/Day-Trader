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
            self.contract = C.Contract("TESTUSDT", "asset-test", -24 * 60, None)
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
            s = C.setup(self.tape, 6*60+17, self.p, self.contract)
            self.assertEqual((s.entry, s.high), (25, 114))
            self.assertNotIn(5, s.signals)

        def test_red_day_wait_and_early_no_trade(self):
            self.assertIsNone(C.setup(self.tape, 60, self.p, self.contract))
            self.put("close", 71, 99)
            self.assertEqual(C.setup(self.tape, 60, self.p, self.contract).entry, 73)
            self.put("close", 47, 98)
            self.assertEqual(C.setup(self.tape, 60, self.p, self.contract).entry, 49)
            self.put("volume", 23, 0)
            self.assertEqual(C.setup(self.tape, 60, self.p, self.contract).entry, 49)

        def test_hourly_variant_no_lookahead(self):
            self.put("high", 7, 133)
            self.assertEqual(C.setup(self.tape, 6*60+10, self.p, self.contract, earlier=False).entry, 8)
            self.assertIsNone(C.setup(self.tape, 6*60+10, self.p, self.contract, earlier=True))
            self.assertEqual(C.setup(self.tape, 6*60+10, self.p, self.contract, earlier=True, screen=False).entry, 7)
            self.assertEqual(C.setup(self.tape, 6*60, self.p, self.contract, earlier=False, screen=False).entry, 7)
            self.assertIsNone(C.setup(self.tape, 6*60, self.p, self.contract, earlier=True))

        def test_stop_cap_and_worse_open(self):
            s = C.Setup(25, 150, (), 12)
            self.put("high", 26, 125)
            self.assertEqual(C.execution(self.tape, s, self.p, self.contract), (26 * 60, 125, "stop", None))
            self.put("open", 26, 130)
            self.put("high", 26, 140)
            t = C.evaluate(self.tape, s, self.p, self.contract)
            self.assertAlmostEqual(t.price, -0.30)
            self.assertAlmostEqual(t.net(15), -0.30345)

        def test_horizon_uses_open_and_funding_includes_exit(self):
            s = C.Setup(24, 130, (), 4)
            self.put("open", 96, 85)
            self.put("high", 96, 200)
            t = C.evaluate(self.tape, s, self.p, self.contract)
            self.assertFalse(t.stopped)
            self.assertAlmostEqual(t.price, 0.15)
            self.assertAlmostEqual(t.funding, -0.009)

        def test_missing_funding_never_silently_zero(self):
            s = C.Setup(24, 130, (), 4)
            del self.tape.funding[56]
            self.tape.finish()
            with self.assertRaises(LookupError):
                C.evaluate(self.tape, s, self.p, self.contract)

        def test_zero_volume_entry_no_fill_stop_skipped_timed_exit_deferred(self):
            s = C.Setup(25, 130, (9,), 4)
            self.put("high", 40, 200)
            for h in (9, 40, 97, 98):
                self.put("volume", h, 0)
            C.evaluate(self.tape, s, self.p, self.contract, validate_only=True)
            self.assertEqual(C.execution(self.tape, s, self.p, self.contract), (99 * 60, 100, "deferred_time", None))
            self.put("volume", 25, 0)
            with self.assertRaises(C.NoFill):
                C.evaluate(self.tape, s, self.p, self.contract)

        def test_adverse_roster_end_skips_zero_volume_and_books_funding(self):
            s = C.Setup(25, 130, (), 4)
            ended = C.Contract("TESTUSDT", "asset-test", -24 * 60, 59 * 60)
            self.put("close", 57, 90)
            self.put("close", 58, 70)
            self.put("volume", 58, 0)
            self.tape.funding = {h: x for h, x in self.tape.funding.items() if h <= 58}
            self.tape.finish()
            trade = C.evaluate(self.tape, s, self.p, ended)
            self.assertEqual(trade.exit_reason, "terminal_close")
            self.assertAlmostEqual(trade.price, -0.25)
            self.assertAlmostEqual(trade.funding, -0.004)
            self.assertAlmostEqual(C.last_close_version(trade).price, 0.1)

        def test_archive_tail_is_not_a_terminal_cover(self):
            s = C.Setup(25, 130, (), 4)
            tail = C.Contract("TESTUSDT", "asset-test", -24 * 60, None, 59 * 60)
            with self.assertRaises(C.InputFault) as caught:
                C.evaluate(self.tape, s, self.p, tail, validate_only=True)
            self.assertEqual((caught.exception.kind, caught.exception.hour), ("unverified_end", 59))
            self.put("high", 58, 131)
            self.assertEqual(C.execution(self.tape, s, self.p, tail)[2], "stop")

        def test_gap_pass_flip_keeps_loser_and_all_31_trades(self):
            signal = C.Setup(25, 130, (), 12)
            for key in ("open", "high", "close", "volume"):
                self.put(key, 50, C.NAN)
            self.put("open", 51, 160)
            self.put("high", 51, 161)
            losing = C.evaluate(self.tape, signal, self.p, self.contract)
            self.assertEqual(losing.exit_reason, "stop")
            self.assertAlmostEqual(losing.price, -0.60)
            other = [(1970, x) for x in [0.037, 0.047] * 15]
            pool = {1970: [0] * 60}
            self.assertTrue(C.judgment(self.p, other, pool)["passes"])
            self.assertFalse(C.judgment(self.p, other + [(1970, losing.net(15))], pool)["passes"])
            del self.tape.funding[40]
            self.tape.finish()
            with self.assertRaises(C.InputFault) as err:
                C.evaluate(self.tape, signal, self.p, self.contract, validate_only=True)
            self.assertEqual(err.exception.kind, "fundingRate")

        def test_after_trigger_notice_cancels_through_entry_only(self):
            self.put("high", 6, 130)
            self.put("close", 23, 95)
            self.assertEqual(len(self.controls([])), 1)
            self.assertEqual(self.controls([7 * 60 + 1]), [])
            self.assertEqual(self.controls([25 * 60]), [])
            later = self.controls([25 * 60 + 1])
            self.assertEqual(len(later), 1)
            self.assertFalse(later[0][1])

        def test_prior_close_cannot_predate_launch(self):
            self.put("close", -1, C.NAN)
            self.put("close", 47, 99)
            launched = C.Contract("TESTUSDT", "new", 6 * 60, None)
            counts = defaultdict(int)
            signal = C.setup(self.tape, 6 * 60, self.p, launched, counts=counts)
            self.assertEqual(signal.entry, 49)
            self.assertEqual(counts["days_with_no_prelaunch_prior_close"], 1)

        def test_entry_open_above_stop_is_two_fees(self):
            s = C.Setup(25, 120, (), 4)
            self.put("open", 25, 130)
            self.put("high", 25, 135)
            trade = C.evaluate(self.tape, s, self.p, self.contract)
            self.assertEqual(trade.exit_reason, "stop")
            self.assertAlmostEqual(trade.net(15), -0.003)

        def test_cow_map_overrules_old_path_flag(self):
            from . import score_20 as S, stage_20
            csvs = {
                S.NOTICE: b"notice_id,coin_ticker,market,published_at_utc,binance_um_perp_at_notice\n"
                          b"7,COW,KRW,2025-02-25T08:39Z,no\n",
                S.NOTICE_MAP: b"notice_id,coin_ticker,published_at_utc,matched_symbol,mapping_category,"
                              b"binance_um_perp_at_notice,old_store_flag,differs_from_old_flag,"
                              b"matched_launch_time_utc,matched_launch_precision\n"
                              b"7,COW,2025-02-25T08:39Z,COWUSDT,trading_at_notice,yes,no,yes,2024-11-06T13:30Z,hour\n",
                S.DATED_ROSTER: b"symbol,underlying_asset,contract_type,multiplier,launch_time_utc,"
                                b"launch_time_precision,launch_time_source,launch_source_url,last_trading_time_utc,"
                                b"last_trading_precision,last_trading_source,last_trading_source_url,quote_asset\n"
                                b"COWUSDT,COW,PERPETUAL,1,2024-11-06T13:30Z,hour,binance_launch_announcement,"
                                b"https://www.binance.com/en/support/announcement/detail/0123456789abcdef0123456789abcdef,,,,,USDT\n",
                S.LIFETIMES: b"symbol,lifetime_seq,asset_id,quote_asset,multiplier,launch_time_utc,launch_time_precision,"
                              b"launch_time_source,launch_source_url,end_time_utc,end_time_precision,end_time_source,end_source_url\n"
                              b"COWUSDT,1,cow,USDT,1,2024-11-06T13:30Z,hour,binance_launch_announcement,"
                              b"https://www.binance.com/en/support/announcement/detail/0123456789abcdef0123456789abcdef,,,,\n",
                S.IDENTITIES: b"notice_id,coin_ticker,published_at_utc,notice_asset_id,mapping_category,matched_symbol,"
                               b"matched_lifetime_seq,matched_asset_id,matched_launch_time_utc,matched_end_time_utc,matched_end_time_source\n"
                               b"7,COW,2025-02-25T08:39Z,cow,trading_at_notice,COWUSDT,1,cow,2024-11-06T13:30Z,,\n",
            }
            with patch.object(S.A, "read_pinned", side_effect=lambda path, _: csvs[path]):
                ids = S.identities()
                roster = S.dated_roster(identity_data=ids)
                notices = S.notices(p, roster, identity_data=ids)
            first, index, _ = notices
            notice, contract = first["cow"]
            self.assertEqual((notice.ticker, contract.symbol), ("COW", "COWUSDT"))
            self.assertEqual(index["cow"], [notice.minute])
            wanted = stage_20.required(first, p)
            self.assertEqual({k[:2] for k in wanted},
                             {("COWUSDT", "klines"), ("COWUSDT", "markPriceKlines"), ("COWUSDT", "fundingRate")})
            with self.assertRaises(S.Refused) as error:
                S.evaluate_book({}, notices, roster, set(), p, validate_only=True)
            self.assertEqual(error.exception.code, "P20_REQUIRED_KLINES")
            self.assertIn("COWUSDT", str(error.exception.path))

        def test_book_does_not_pass_by_losing_gap_or_missing_mark(self):
            from . import score_20 as S
            tapes, roster, first = {}, {}, {}
            for i in range(31):
                sym = f"T{i}USDT"
                contract = C.Contract(sym, sym, -1440, None)
                first[sym] = (C.Notice(sym, sym, 8 * 60), contract)
                roster[sym] = [contract]
                tape = tapes[sym] = C.Tape(-24, 480)
                for h in range(-24, 480):
                    values = {"open": 100, "high": 120, "close": 99 if h == 23 else 100,
                              "volume": 1, "mark": 100}
                    if h == 8:
                        values["high"] = 130
                    if h == 97:
                        values.update(open=94 + i % 2, high=100, close=95)
                    if i == 30 and h == 51:
                        values.update(open=160, high=165, close=160)
                    if i != 30 or h != 50:
                        for name, value in values.items():
                            tape.set(name, h, value)
                    if h % 8 == 0:
                        tape.funding[h] = 8, 0.0
                tape.finish()
            books = {symbol: [("klines", -24, 480, Path(symbol), "")] for symbol in tapes}
            notice_data = first, {}, {}
            controls = [(C.Trade(1970, 0, 0, 0, "time"), True)] * 3
            with patch.object(S, "load", side_effect=lambda files, _: tapes[files[0][3].name]), \
                    patch.object(S, "affected", return_value=Path("fixture-mark.zip")), \
                    patch.object(S.C, "ordinary", side_effect=lambda *a, **k: iter(()) if k["validate_only"] else iter(controls)):
                out = S.evaluate_book(books, notice_data, roster, set(), self.p)
                self.assertEqual(out["notice_disposition"]["traded"], 31)
                self.assertFalse(out["judgment"]["passes"])
                tapes["T30USDT"].fields["mark"][48 + 24] = C.NAN
                with self.assertRaises(S.Refused) as error:
                    S.evaluate_book(books, notice_data, roster, set(), self.p, validate_only=True)
                self.assertEqual(error.exception.code, "P20_REQUIRED_MARKPRICEKLINES")

        def test_trigger_needs_live_candle(self):
            self.put("high", 6, 130)
            for key in ("open", "close", "high"):
                self.put(key, 7, C.NAN)
            self.put("close", 23, 95)
            outcomes = defaultdict(int)
            self.assertEqual(len(self.controls([], outcomes)), 0)
            self.assertEqual(outcomes["not_trading_at_trigger"], 1)

        def controls(self, notices, counts=None, **options):
            tapes = {self.contract.symbol: self.tape}
            return list(C.ordinary(tapes, {self.contract.symbol: (self.contract,)},
                                   {self.contract.asset: notices}, self.p, counts, **options))

        def test_notice_exclusion_and_greedy_dedupe(self):
            for h in (6, 14, 200):
                self.put("high", h, 130)
            for h in (23, 215):
                self.put("close", h, 95)
            self.assertEqual(len(self.controls([])), 2)
            self.assertEqual(len(self.controls([4*60])), 1)

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
