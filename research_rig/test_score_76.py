"""All bars, dates, approvals and custody receipts in this module are invented."""

from collections import Counter
from copy import deepcopy
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

import numpy as np

import score_76 as s
import power_76


def tape(hours=130, start="2022-12-30", coins=("A", "B")):
    shape = hours, len(coins)
    return s.Tape(s.utc(start), coins, np.full(shape, 100.), np.ones(shape, bool), np.full(shape, 100.))


class Tests(unittest.TestCase):
    def setUp(self):
        self.cfg = s.config()
        self.cfg["control"] |= {"draws": 11, "max_attempts_per_draw": 5}

    def test_count_branch_strong_first_and_no_open_access(self):
        t = tape()
        t.close[(2, 52), 0] = 96
        c = self.cfg | {"count_each_year": 1}
        readable = s.Tape(t.start, t.names, t.close, t.full, None)
        self.assertEqual(s.counts(readable, c)["selected"], "alternate")
        t.close[(2, 52), 0] = 95
        summary = s.counts(readable, c)
        self.assertEqual(summary["selected"], "primary")
        self.assertEqual(summary["counts_by_utc_entry_year"]["primary"], {"2022": 1, "2023": 1})
        t.close[52, 0] = 98
        self.assertEqual(s.counts(readable, c)["outcome"], "closed on count")

    def test_count_reports_all_years_and_refuses_tail_without_future(self):
        t = tape(77, start="2020-01-01")
        t.close[11, 0] = 95
        t.close[28, 0] = 80  # still in the first scheduled slot
        t.close[55, 0] = 95  # can't finish a scheduled hold
        t.close[-1, 0] = 80  # signal at the final close
        out = s.counts(t, self.cfg)
        self.assertEqual(out["counts_by_utc_entry_year"]["primary"]["2020"], 1)
        self.assertEqual(out["refused_at_fence"]["primary"], 2)
        self.assertIsNone(out["unresolved_at_fence"])

    def test_largest_first_tie_exact_boundary_and_no_substitution(self):
        t = tape()
        t.close[4, :] = [95, 94]
        t.open[5, 1] = np.nan  # winner has no price, don't switch to A
        t.close[6, :] = [95, 95]
        t.close[8, :] = [80, 80]  # busy
        t.close[30, 1] = 90  # same open as the first scheduled exit
        t.open[31, 0] = 120
        trades, gaps = s.tickets(t, .05, 24, s.executable(t), s.next_sale(s.executable(t)))
        self.assertEqual([(x.coin, x.entry, x.exit) for x in trades], [(0, 7, 31), (1, 31, 55)])
        self.assertAlmostEqual(trades[0].gross, .20)
        self.assertEqual(gaps["void_missing_entry_bar"], 1)

    def test_delayed_sale_and_unresolved_block_new_entries(self):
        t = tape()
        t.close[3, 0] = 90
        t.full[28:30, 0] = False
        t.open[30, 0] = 120
        t.close[28, 1] = 90  # busy until bar 30
        t.close[49, 0] = 80
        t.full[74:, 0] = False
        t.close[93, 1] = 90  # no sale on the prior position, can't take this
        opens = s.executable(t)
        trades, gaps = s.tickets(t, .05, 24, opens, s.next_sale(opens))
        self.assertEqual([(x.entry, x.exit) for x in trades], [(4, 30)])
        self.assertEqual(gaps, {"void_missing_entry_bar": 0, "void_missing_exit_bar": 0, "delayed_sales": 1,
                               "refused_at_fence": 0, "unresolved_at_fence": 1})

    def test_missing_exit_is_counted_and_missing_close_does_not_bridge(self):
        t = tape()
        t.close[3, 0] = 90
        t.open[28, 0] = np.nan
        t.close[20, 1] = 90  # locked through the scheduled exit
        t.close[30, 0] = np.nan
        t.close[31, 0] = 50  # must not compare across the absent hourly close
        t.close[35, 1] = 85
        valid = s.executable(t)
        trades, gaps = s.tickets(t, .05, 24, valid, s.next_sale(valid))
        self.assertEqual([(q.coin, q.entry, q.exit) for q in trades], [(1, 36, 60)])
        self.assertEqual(gaps["void_missing_exit_bar"], 1)
        self.assertIsNone(s.fill(t, s.next_sale(valid), 0, 4, 24))

    def test_admission_full_trading_windows_and_exact_flags(self):
        names = ("BTC", "XRP", "ZEC", "DOT", "BNB")
        for first, expected in [
            ("2020-12-28", [True, True, True, False, False]),
            ("2020-12-29", [True, False, True, False, False]),
            ("2023-07-14", [True, True, True, False, False]),
            ("2023-09-09", [True, True, False, False, False]),
            ("2025-10-29", [True, True, False, False, True]),
            ("2026-05-08", [False] * 5),
        ]:
            self.assertEqual(s.eligibility(s.utc(first), 24, names, self.cfg).tolist(), [expected] * 24)

    def test_seeded_matching_exact_strata_and_no_overlap(self):
        t = tape(24 * 56)
        t.full[26:29, 0] = False  # a control sale may wait too
        opens = s.executable(t)
        sales = s.next_sale(opens)
        actual = [s.fill(t, sales, 0, 2, 24), s.fill(t, sales, 1, 29, 24),
                  s.fill(t, sales, 0, 2 + 168, 24)]
        def matched(trades):
            return Counter((q.coin, s.hour_of_week(t.clock(q.entry))) for q in trades)
        a = s.random_books(t, actual, 24, opens, sales, self.cfg)
        b = s.random_books(t, actual, 24, opens, sales, self.cfg)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 11)
        self.assertGreater(len({tuple(x.entry for x in book) for book in a}), 1)
        for book in a:
            self.assertEqual(matched(book), matched(actual))
            by_time = sorted(book, key=lambda q: q.entry)
            self.assertTrue(all(q.exit <= r.entry for q, r in zip(by_time, by_time[1:])))
            self.assertTrue(all(q == s.fill(t, sales, q.coin, q.entry, 24) for q in book))

    def test_marks_strict_ties_trim_and_minimum(self):
        c = self.cfg | {"min_heldback_trades": 4}
        controls = [0.] * 11
        good = s.marks([.02] * 4, [2024, 2024, 2025, 2025], controls, c)
        self.assertTrue(all(good["marks"].values()))
        trim_only = s.marks([-.01, .02, -.01, .02], [2024, 2024, 2025, 2025], controls, c)
        self.assertEqual([k for k, v in trim_only["marks"].items() if not v], ["positive_trimmed"])
        tie = s.marks([0.] * 4, [2024] * 4, controls, c)
        self.assertFalse(tie["marks"]["beats_random"])
        self.assertEqual(tie["control_share_strictly_beaten"], 0)
        self.assertIsNone(s.marks([.02], [2024], [], c)["control_share_strictly_beaten"])

    def test_design_branch_and_cheap_card_with_unchanged_delayed_exit(self):
        t = tape()
        for e in (4, 34, 64):
            t.close[e - 1, 0] = 90
            t.close[e, 0] = 100.5
            t.open[e + 24, 0] = 101
        c = self.cfg | {"min_heldback_trades": 3}
        controls = [[s.Trade(0, 0, 24, 0)]] * 11
        with patch.object(s, "random_books", return_value=controls):
            result = s.scored(t, "heldback", "primary", c)
            design = s.scored(t, "design", "primary", c)
            low_count = s.scored(t, "heldback", "primary", c | {"min_heldback_trades": 4})
        self.assertEqual(result["outcome"], "forward card on Binance.US books, not a counted pass")
        self.assertEqual(design["outcome"], "advance to held-back")
        self.assertNotIn("lines", design)
        self.assertIn("selected_arm_marks", design["shown_only"])
        self.assertEqual(low_count["outcome"], "closed on count")
        self.assertAlmostEqual(result["shown_only"]["primary_late"]["mean_net"]["main"], s.net(101 / 100.5 - 1, 75))

    def test_separate_committed_keys_refuse_before_any_input(self):
        key = "P76_" + "COUNT_GO"
        pin = "e" * 64
        led = f"| 229 | `{key}={pin}` |"
        self.assertEqual(s.approval(led, "count", 229), pin)
        with self.assertRaisesRegex(s.Refusal, "REFUSE_LEDGER_GO"):
            s.approval(led, "heldback", 229)
        with self.assertRaisesRegex(s.Refusal, "REFUSE_LEDGER_GO"):
            s.approval(led + "\n" + key, "count", 229)
        with (patch.object(s, "committed_ledger", return_value="| 229 | no keys |"),
              patch.object(s, "open_folder", side_effect=AssertionError("must not open")),
              redirect_stdout(io.StringIO()) as output):
            for mode in s.MODES:
                self.assertEqual(s.main([mode]), 2)
        self.assertEqual(output.getvalue().splitlines(), ["REFUSE_LEDGER_GO"] * len(s.MODES))

    def test_opaque_pin_decode_and_one_shot_lock_on_invented_files(self):
        c = self.cfg | {"design": ["2022-12-30", "2023-01-02"], "admissions": {"A": [["2020-01-01", None]]},
                        "source_coverage": {"min_coins": 1}}
        t = tape(72, coins=("A",))
        price_blob = t.close.astype("<f8").tobytes()
        source_blob = b"made-up separate custodian"
        m = {"schema": 1, "stage": "count", "start": "2022-12-30", "stop_exclusive": "2023-01-02",
             "names": ["A"], "covered_names": ["A"], "hours": 72, "bars_sha256": s.digest(price_blob),
             "source_release": "invented", "source_release_end_exclusive": "2023-01-02",
             "coverage_receipt_sha256": s.digest(b"made-up coverage"),
             "source_receipt_sha256": s.digest(source_blob), "prior_result_sha256": None}
        manifest_blob = json.dumps(m).encode()
        pin = s.digest(manifest_blob)
        receipt_blob = json.dumps({"schema": 1, "stage": "count", "manifest_sha256": pin,
                                   "separate_custodian": True, "permission_confirmed": True}).encode()
        with TemporaryDirectory() as tmp:
            path = Path(tmp)
            for name, blob in (("manifest.json", manifest_blob), ("receipt.json", receipt_blob),
                               ("source_receipt.json", source_blob), ("bars.f64", price_blob)):
                (path / name).write_bytes(blob)
                (path / name).chmod(0o600)
            with s.open_folder(path) as fd:
                with self.assertRaisesRegex(s.Refusal, "REFUSE_PIN"):
                    s.snapshot(fd, "count", "0" * 64, c)
                with patch.object(s, "read_bars", side_effect=AssertionError("opaque only")):
                    manifest, payload = s.snapshot(fd, "count", pin, c)
                self.assertFalse((path / "RUN.lock").exists())
                broken = np.full((72, 1), -1., dtype="<f8").tobytes()
                with self.assertRaisesRegex(s.Refusal, "REFUSE_PRICE_ENCODING"):
                    s.execute(fd, "count", pin, manifest, broken, None, c)
                self.assertFalse((path / "RUN.lock").exists())
                original = s.counts
                def assert_locked(*args):
                    self.assertEqual((path / "RUN.lock").read_text(), pin + "\n")
                    return original(*args)
                with patch.object(s, "counts", side_effect=assert_locked):
                    body = json.loads(s.execute(fd, "count", pin, manifest, payload, None, c))
                self.assertEqual(body["outcome"], "closed on count")
                self.assertEqual((path / "RUN.lock").stat().st_mode & 0o777, 0o600)
                with self.assertRaisesRegex(s.Refusal, "REFUSE_OUTPUT_EXISTS"):
                    s.execute(fd, "count", pin, manifest, payload, None, c)

    def test_heldback_release_end_is_pinned_and_decoder_is_venue_blind(self):
        c = self.cfg | {"admissions": dict.fromkeys(("A", "B"), [["2020-01-01", None]]),
                        "source_coverage": {"min_coins": 1}}
        # Two native layouts from invented sources normalize to the same tape.
        object_bar = {"timestamp": "1704067200", "open": "98", "close": "99"}
        row_bar = [1704067200, "98", "101", "97", "99", "4", "2"]
        fixture = (
            ("invented-object-source", (float(object_bar["open"]), float(object_bar["close"]))),
            ("invented-row-source", (float(row_bar[1]), float(row_bar[4]))),
        )
        meta = {"schema": 1, "stage": "heldback", "start": "2024-01-01", "stop_exclusive": "2024-01-03",
                "source_release_end_exclusive": "2024-01-03", "names": ["A", "B"], "covered_names": ["A"], "hours": 48,
                "coverage_receipt_sha256": s.digest(b"made-up coverage"),
                "source_receipt_sha256": s.digest(b"invented"), "prior_result_sha256": "0" * 64}
        for release, bar in fixture:
            payload = np.full((48, 2, 2), np.nan, dtype="<f8")
            payload[0] = bar
            m = meta | {"source_release": release, "bars_sha256": s.digest(payload.tobytes())}
            decoded = s.read_bars(m, payload.tobytes(), c)
            self.assertEqual((decoded.open[0, 0], decoded.close[0, 0]), (98, 99))
            self.assertTrue(np.isnan(decoded.open[1:, 0]).all())
            self.assertFalse(decoded.full[:, 1].any())  # present source bar, but not covered
        m["source_release_end_exclusive"] = "2024-01-04"
        raw_manifest = json.dumps(m).encode()
        with patch.object(s, "read_file", return_value=raw_manifest) as read:
            with self.assertRaisesRegex(s.Refusal, "REFUSE_RELEASE_END"):
                s.snapshot(None, "heldback", s.digest(raw_manifest), c)
        self.assertEqual(read.call_count, 1)  # refuse before any tape read
        m["covered_names"] = []
        raw_manifest = json.dumps(m).encode()
        with patch.object(s, "read_file", return_value=raw_manifest) as read:
            with self.assertRaisesRegex(s.Refusal, "REFUSE_COVERAGE"):
                s.snapshot(None, "heldback", s.digest(raw_manifest), c)
        self.assertEqual(read.call_count, 1)

    def test_carry_forward_only_for_pinned_advancing_predecessor(self):
        choice = {"coverage_receipt_sha256": s.digest(b"made-up coverage"), "covered_names": ["A"]}
        prior_manifest = json.dumps(choice).encode()
        pin = s.digest(prior_manifest)
        ledger = "| 229 | P76_" + f"COUNT_GO={pin} |"
        result = {"stage": "count", "manifest_sha256": pin, "selected": "alternate",
                  "outcome": "advance to design"}
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "count"
            path.mkdir(mode=0o700)
            with s.open_folder(path) as fd:
                s.new_file(fd, "RUN.lock", (pin + "\n").encode(), "REFUSE_LOCK")
                s.new_file(fd, "manifest.json", prior_manifest, "REFUSE_PREVIOUS_MANIFEST")
                body = json.dumps(result).encode()
                s.new_file(fd, "result.json", body, "REFUSE_OUTPUT_EXISTS")
            manifest = choice | {"prior_result_sha256": s.digest(body)}
            self.assertEqual(s.carry_in(root, "design", manifest, ledger, self.cfg), "alternate")
            with self.assertRaisesRegex(s.Refusal, "REFUSE_PREVIOUS_RESULT"):
                s.carry_in(root, "design", manifest | {"prior_result_sha256": "a" * 64}, ledger, self.cfg)
            with self.assertRaisesRegex(s.Refusal, "REFUSE_SOURCE_CHANGE"):
                s.carry_in(root, "design", manifest | {"coverage_receipt_sha256": "a" * 64}, ledger, self.cfg)

    def test_power_stable_and_not_a_real_count(self):
        cfg = deepcopy(self.cfg)
        cfg["power"] |= {"worlds": 60, "trades": [64], "residual_sd": [.05]}
        first = power_76.simulate(cfg)
        self.assertEqual(first, power_76.simulate(cfg))
        self.assertEqual(len(first["scenarios"]), 12)
        self.assertTrue(all(0 <= row["all_four"] <= 1 for row in first["scenarios"]))


if __name__ == "__main__":
    unittest.main()
