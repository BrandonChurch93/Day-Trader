"""Made-up Plan 20 inputs only."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
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

        def test_labelled_missing_funding_uses_floor_then_larger_file_peak(self):
            s = C.Setup(24, 130, (), 4)
            del self.tape.funding[56]
            self.put("mark", 56, 110)
            self.tape.finish()
            C.evaluate(self.tape, s, self.p, self.contract, validate_only=True)
            t = C.evaluate(self.tape, s, self.p, self.contract)
            self.assertEqual(t.missing_funding_settlements, 1)
            self.assertAlmostEqual(t.missing_funding_debit, 0.022)
            self.assertAlmostEqual(t.funding, -0.030)
            self.tape.funding_peaks[self.contract] = 0.035
            t = C.evaluate(self.tape, s, self.p, self.contract)
            self.assertAlmostEqual(t.missing_funding_debit, 0.0385)
            self.assertAlmostEqual(C.summary([t], 15)["missing_funding_debit_sum_entry_notional"], 0.0385)
            self.put("mark", 56, C.NAN)
            with self.assertRaises(C.InputFault) as error:
                C.evaluate(self.tape, s, self.p, self.contract, validate_only=True)
            self.assertEqual((error.exception.kind, error.exception.hour), ("markPriceKlines", 56))

        def test_aligned_interval_switch_charges_only_observed_settlements(self):
            self.assertEqual(C.funding_clock_gap(54, 2, 56, 4)[0], "consistent_interval_change")
            self.assertEqual(C.funding_clock_gap(56, 8, 60, 4)[0], "consistent_interval_change")
            self.assertEqual(C.funding_clock_gap(54, 2, 60, 4)[0], "unlabelled_gap")
            self.tape.funding[54] = 2, -0.003
            self.tape.funding[56] = 4, 0.004
            self.tape.finish()
            s = C.Setup(48, 130, (), 4)
            t = C.evaluate(self.tape, s, self.p, self.contract)
            self.assertEqual(t.missing_funding_settlements, 0)
            self.assertAlmostEqual(t.funding, -0.007)
            del self.tape.funding[56]
            self.tape.finish()
            with self.assertRaises(C.InputFault) as error:
                C.evaluate(self.tape, s, self.p, self.contract, validate_only=True)
            self.assertEqual(error.exception.kind, "fundingRate")

        def test_missing_clock_at_entry_excluded_and_at_exit_charged(self):
            for h in (24, 96):
                del self.tape.funding[h]
            self.tape.finish()
            t = C.evaluate(self.tape, C.Setup(24, 130, (), 4), self.p, self.contract)
            self.assertEqual(t.missing_funding_settlements, 1)
            self.assertAlmostEqual(t.missing_funding_debit, 0.02)

        def test_verified_terminal_projects_trailing_grid_but_other_expiry_refuses(self):
            self.tape.funding = {h: (4, 0.0) for h in range(0, 33, 4)}
            self.tape.finish()
            ended = C.Contract("TESTUSDT", "asset-test", 0, 40 * 60)
            t = C.evaluate(self.tape, C.Setup(24, 130, (), 4), self.p, ended)
            self.assertEqual(t.exit_reason, "terminal_close")
            self.assertEqual(t.missing_funding_settlements, 2)
            self.assertAlmostEqual(t.missing_funding_debit, 0.04)
            with self.assertRaises(C.InputFault) as error:
                C.evaluate(self.tape, C.Setup(24, 130, (), 4), self.p, self.contract, validate_only=True)
            self.assertEqual(error.exception.kind, "fundingRate")

        def test_pre_expiry_exit_needs_no_right_anchor_when_next_due_is_after_verified_end(self):
            self.tape.funding = {0: (8, -0.001), 8: (8, -0.002)}
            self.tape.finish()
            self.put("high", 4, 140)
            signal = C.Setup(1, 130, (), 0)
            verified = C.Contract("TESTUSDT", "asset-test", 0, 4 * 60 + 30)
            trade = C.evaluate(self.tape, signal, self.p, verified)
            self.assertEqual((trade.exit_minute, trade.funding), (4 * 60, 0))
            # The next due clock at 8 must be strictly after the end. An archive
            # tail, rather than an official end, cannot supply this exception.
            del self.tape.funding[8]
            self.tape.finish()
            for end, tail in ((8 * 60, None), (9 * 60, None), (None, 5 * 60)):
                with self.subTest(end=end, tail=tail), self.assertRaises(C.InputFault) as error:
                    C.evaluate(self.tape, signal, self.p, C.Contract("TESTUSDT", "asset-test", 0, end, tail))
                self.assertEqual((error.exception.kind, error.exception.hour), ("fundingRate", 4))
            self.tape.funding[0] = (3, 0)
            self.tape.finish()
            with self.assertRaises(C.InputFault):
                C.evaluate(self.tape, signal, self.p, verified)

        def test_reused_ticker_cannot_supply_left_or_right_funding_anchor(self):
            s = C.Setup(24, 130, (), 4)
            for h in (24, 104):
                del self.tape.funding[h]
            self.tape.finish()
            newer = C.Contract("TESTUSDT", "new-asset", 20 * 60, None)
            older = C.Contract("TESTUSDT", "old-asset", 0, 108 * 60)
            for contract, expected_hour in ((newer, 24), (older, 96)):
                with self.subTest(contract=contract.asset), self.assertRaises(C.InputFault) as error:
                    C.evaluate(self.tape, s, self.p, contract, validate_only=True)
                self.assertEqual((error.exception.kind, error.exception.hour), ("fundingRate", expected_hour))

        def test_mixed_grid_gap_outside_short_is_not_a_refusal(self):
            self.tape.funding = {24: (8, -0.001), 36: (4, -0.001)}
            self.tape.finish()
            self.put("high", 27, 140)
            t = C.evaluate(self.tape, C.Setup(25, 130, (), 4), self.p, self.contract)
            self.assertEqual(t.exit_minute, 27 * 60)
            self.assertEqual(t.funding, 0.0)
            self.put("high", 28, 140)
            self.put("high", 27, 120)
            with self.assertRaises(C.InputFault) as error:
                C.evaluate(self.tape, C.Setup(25, 130, (), 4), self.p, self.contract)
            self.assertEqual((error.exception.kind, error.exception.hour), ("fundingRate", 28))

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

        def test_announced_halt_disallows_entry_but_does_not_cover_existing_short(self):
            contract = C.Contract("TESTUSDT", "asset-test", -24 * 60, 59 * 60,
                                  new_positions_halted_minute=58 * 60 + 30)
            with self.assertRaises(C.NoFill):
                C.execution(self.tape, C.Setup(59, 130, (), 4), self.p, contract)
            before_halt = C.Setup(58, 130, (), 4)
            self.assertEqual(C.execution(self.tape, before_halt, self.p, contract)[:3],
                             (59 * 60, 125, "terminal_close"))

        def test_gap_pass_flip_keeps_loser_and_all_31_trades(self):
            signal = C.Setup(25, 130, (), 12)
            for key in ("open", "high", "close", "volume"):
                self.put(key, 50, C.NAN)
            self.put("open", 51, 160)
            self.put("high", 51, 161)
            losing = C.evaluate(self.tape, signal, self.p, self.contract)
            self.assertEqual(losing.exit_reason, "gap_stop")
            self.assertAlmostEqual(losing.price, -0.60)
            other = [(1970, x) for x in [0.037, 0.047] * 15]
            pool = {1970: [0] * 60}
            self.assertTrue(C.judgment(self.p, other, pool)["passes"])
            self.assertFalse(C.judgment(self.p, other + [(1970, losing.net(15))], pool)["passes"])
            del self.tape.funding[40]
            self.tape.finish()
            self.put("mark", 40, C.NAN)
            with self.assertRaises(C.InputFault) as err:
                C.evaluate(self.tape, signal, self.p, self.contract, validate_only=True)
            self.assertEqual(err.exception.kind, "markPriceKlines")

        def test_unseen_stop_inside_missing_hour_closed_even_if_next_open_below_stop(self):
            s = C.Setup(25, 130, (), 4)
            self.put("high", 50, 132)
            self.assertEqual(C.execution(self.tape, s, self.p, self.contract)[:3], (50 * 60, 125, "stop"))
            for name in ("open", "high", "close", "volume"):
                self.put(name, 50, C.NAN)
            self.put("volume", 51, 0)
            t = C.evaluate(self.tape, s, self.p, self.contract)
            self.assertEqual((t.exit_minute, t.exit_reason), (52 * 60, "gap_stop"))
            self.assertAlmostEqual(t.price, -0.25)
            self.assertAlmostEqual(t.funding, -0.003)
            self.assertAlmostEqual(t.turnover, 2.25)
            continued = C.evaluate(self.tape, s, self.p, self.contract, continue_gaps=True)
            self.assertEqual((continued.exit_minute, continued.exit_reason), (97 * 60, "time"))
            self.assertAlmostEqual(continued.price, 0.0)

        def test_trailing_gap_is_counted_at_official_terminal_cover(self):
            ending = C.Contract("TESTUSDT", "asset-test", -1440, 59 * 60)
            for h in (57, 58):
                for name in ("open", "high", "close", "volume"):
                    self.put(name, h, C.NAN)
            t = C.evaluate(self.tape, C.Setup(25, 130, (), 4), self.p, ending)
            self.assertEqual((t.exit_minute, t.exit_reason), (59 * 60, "gap_terminal_close"))
            self.assertAlmostEqual(t.price, -0.25)
            self.assertTrue(t.terminal_close and t.gap_close)

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
            with patch.object(S, "load", side_effect=lambda files, _, **kw: tapes[files[0][3].name]), \
                    patch.object(S, "affected", return_value=Path("fixture-mark.zip")), \
                    patch.object(S.C, "ordinary", side_effect=lambda *a, **k: iter(()) if k["validate_only"] else iter(controls)):
                out = S.evaluate_book(books, notice_data, roster, set(), self.p)
                self.assertEqual(out["notice_disposition"]["traded"], 31)
                self.assertFalse(out["judgment"]["passes"])
                shown = out["shown_missing_hold_bar_continuation"]
                self.assertEqual(out["judged"]["missing_hold_bar_closes"], 1)
                self.assertEqual(shown["by_arm"]["listing"]["closes"], 1)
                self.assertEqual(shown["listing"]["count"], 31)
                self.assertIsNotNone(shown["joint_comparison"])
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

        def test_scoped_clock_skip_uses_full_time_hold_not_realized_stop(self):
            self.put("high", 6, 140)
            self.put("close", 23, 95)
            self.put("mark", 40, C.NAN)
            scope = {"TESTUSDT": [("markPriceKlines", 40, 41)]}
            self.put("high", 26, 140)
            self.assertEqual(self.controls([])[0][0].exit_minute, 26 * 60)
            for high in (140, 101):
                self.put("high", 26, high)
                skipped = Counter()
                self.assertEqual(self.controls([], calendar_skip=scope, skipped=skipped), [])
                self.assertEqual(skipped, {("TESTUSDT", "1970-01"): 1})
            skipped = Counter()
            with self.assertRaises(C.InputFault):
                self.controls([], calendar_skip={"TESTUSDT": [("markPriceKlines", 41, 42)]}, skipped=skipped)
            self.assertFalse(skipped)
            # Direct event evaluation never receives a calendar skip.
            with self.assertRaises(C.InputFault):
                C.evaluate(self.tape, C.Setup(25, 140, (), 8), self.p, self.contract, validate_only=True)

        def test_scheduled_control_funding_rejects_missing_left_and_right_coverage(self):
            for observed, hours in (({32: (8, 0), 104: (8, 0)}, (25,)),
                                    ({24: (8, 0)}, (32, 97)), ({}, (25, 97))):
                self.tape.funding = observed
                self.tape.finish()
                faults = C.scheduled_control_faults(self.tape, 25, self.p, self.contract)
                self.assertEqual([(e.kind, e.hour) for e in faults], [("fundingRate", h) for h in hours])

        def test_allowlisted_fault_cannot_mask_other_calendar_faults(self):
            self.put("high", 6, 140)
            self.put("close", 23, 95)
            variants = (
                ({24: 8, 40: 4, 56: 8, 104: 8}, 39, 44, False),
                ({24: 8, 40: 8, 56: 4, 104: 4}, 55, 44, True),
            )
            for observations, last_allowed, actual_funding_fault, no_projected_mark in variants:
                self.tape.funding = {h: (i, 0) for h, i in observations.items()}
                self.tape.finish()
                self.put("mark", 32, C.NAN if no_projected_mark else 100)
                scoped = {"TESTUSDT": [("fundingRate", 28, last_allowed + 1)]}
                skipped = Counter()
                with self.assertRaises(C.InputFault) as error:
                    self.controls([], calendar_skip=scoped, skipped=skipped)
                # The strict path still reports its first funding fault.
                want_hour = actual_funding_fault if no_projected_mark else 28
                self.assertEqual((error.exception.kind, error.exception.hour), ("fundingRate", want_hour))
                self.assertFalse(skipped)

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

        def test_funding_file_peak_includes_rows_outside_tape_but_not_other_lifetime(self):
            from . import score_20 as S
            start = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp()) // 3600
            old = C.Contract("TESTUSDT", "old-asset", start * 60, (start + 12) * 60)
            new = C.Contract("TESTUSDT", "new-asset", (start + 24) * 60, None)
            tape = C.Tape(start + 24, start + 48, (old, new))
            clocks = ((0, -0.036), (8, 0.007), (16, 0.90), (24, 0.080), (48, 0.09))
            with TemporaryDirectory() as tmp:
                path = Path(tmp) / "fixture.zip"
                with ZipFile(path, "w") as z:
                    z.writestr("fixture.csv", "".join(f"{(start + h) * 3600},8,{rate}\n" for h, rate in clocks))
                S.decode_archive("fundingRate", start, start + 72, path, S.digest(path.read_bytes()),
                                 p, defaultdict(int), tape=tape)
            self.assertEqual(tape.funding_peak(old), 0.036)
            self.assertEqual(tape.funding_peak(new), 0.09)
            self.assertEqual(set(tape.funding), {start + 24})

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

        def test_shared_validation_collects_input_faults_without_claim_or_scoring(self):
            from . import score_20 as S
            symbols = ("BADUSDT", "ONEUSDT", "TWOUSDT")
            roster = {sym: [C.Contract(sym, sym, -1440, None)] for sym in symbols}
            with TemporaryDirectory() as tmp:
                root = Path(tmp)
                bad = [root / "bad-kline.zip", root / "bad-funding.zip"]
                mark = {sym: root / f"{sym}-mark.zip" for sym in symbols[1:]}
                groups = {symbols[0]: [(kind, 0, 480, path, "0" * 64)
                                       for kind, path in zip(("klines", "fundingRate"), bad)]}
                for sym in symbols[1:]:
                    groups[sym] = [("markPriceKlines", 0, 480, mark[sym], "0" * 64)]
                tape = self.tape
                tape.fields["mark"][8 - tape.start] = C.NAN
                tape.fields["mark"][16 - tape.start] = C.NAN
                signal = C.Setup(1, 120, (), 0)
                original_load = S.load

                def load(files, policy, **kw):
                    return tape if files[0][3] in mark.values() else original_load(files, policy, **kw)

                mapped = {}, {}, {}
                with patch.object(S, "authorize") as authorize, patch.object(S, "claim", side_effect=AssertionError), \
                        patch.object(S.C.Trade, "net", side_effect=AssertionError), \
                        patch.object(S.C, "Trade", side_effect=AssertionError), \
                        patch.object(S.C, "policy", return_value=self.p), patch.object(S, "inventory", return_value=groups), \
                        patch.object(S, "identities"), patch.object(S, "dated_roster", return_value=roster), \
                        patch.object(S, "notices", return_value=mapped), patch.object(S, "load", side_effect=load), \
                        patch.object(S.A, "read_pinned", return_value=b""), \
                        patch.object(S.US, "rows", return_value=[]), patch.object(S, "memory"), \
                        patch.object(C, "pump_triggers", side_effect=lambda _, sym, __: iter(((0, sym),))), \
                        patch.object(C, "setup", return_value=signal), patch("builtins.print") as emit:
                    with self.assertRaises(S.Refused) as error:
                        S.prepare(self.p)
                    self.assertEqual((error.exception.code, error.exception.path), ("P20_ARCHIVE_PIN", bad[0]))
                    self.assertEqual(S.validate_inputs("approved-fixture"), 1)
                    authorize.assert_called_once_with("approved-fixture")
                    rows = json.loads(emit.call_args.args[0])
                expected = sorted({("P20_ARCHIVE_PIN", str(path)) for path in bad} |
                                  {("P20_REQUIRED_MARKPRICEKLINES", str(path)) for path in mark.values()})
                self.assertEqual(rows, {"distinct_refusal_pairs": 4, "coverage": {"blocked_control_components": 1},
                                        "refusals": [{"code": code, "path": path} for code, path in expected]})

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
