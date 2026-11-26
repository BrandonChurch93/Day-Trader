"""Tests and predeclared synthetic calibration; reads only the pinned schedule."""
import argparse
from datetime import date
import json
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import common_25 as C
import fetch_25 as F
import score_25 as S


def dates():
    return C.check_calendar(json.loads(F.pinned(F.HERE / "calendar_25.json",
                            "e8f8a4322f988fcec6f937a19cfbfd0162a28f9b70813f305065c9e10ccb7c6b")))


def plant(days, seed, drift, edge):
    r = Random(seed)
    inside = {d for _, _, ds in C.windows(days, 3) for d in ds}
    # Preserve the previous seeded synthetic paths on all surviving sessions.
    px = 100.0 * (1 + drift + r.gauss(0, 0.004))
    tape = {}
    for d in days:
        old = px
        px *= 1 + drift + (edge if d in inside else 0) + r.gauss(0, 0.004)
        tape[d] = C.Bar(old, max(old, px), min(old, px), px, 100)
    return tape


def auditor_one_regime(days):
    rng = Random(2026)
    inside = {d for _, _, ds in C.windows(days, 3) for d in ds}
    px, tape = 100.0 * (1 + 0.00019 + rng.gauss(0, 0.00006)), {}
    for d in days:
        prev = px
        r = (0.00019 if d.year <= 2021 else 0) + rng.gauss(0, 0.00006)
        if d.year == 2022 and d in inside:
            r += 0.008
        px *= 1+r
        tape[d] = C.Bar(prev, max(prev, px), min(prev, px), px, 1)
    return tape


def calibration():
    # Fixed diagnostic paths, not estimates of TLT power or an optimization.
    days = dates()
    shapes = {"zero_drift_null": (0, 0), "positive_drift_only": (0.0012, 0),
              "positive_month_end_edge": (0, 0.0020)}
    report = {}
    for label, (drift, edge) in shapes.items():
        runs = [C.evaluate(days, plant(days, seed, drift, edge), {})["judged"] for seed in range(2500, 2532)]
        report[label] = {"passes": sum(r["passes"] for r in runs),
                         "daily_gate": sum(r["gates"]["daily_difference_and_t"] for r in runs),
                         "window_mean_positive": sum(r["gates"]["positive_mean"] for r in runs)}
    witness = C.evaluate(days, auditor_one_regime(days), {})["judged"]
    print(json.dumps({"synthetic_only": True, "paths_per_case": 32, "cases": report,
                      "one_regime_witness": {"gates": witness["gates"], "passes": witness["passes"],
                                             "ex_2022_mean_net": witness["leave_one_year_out"]["2022"]["mean_net"],
                                             "positive_daily_year_share": witness["positive_daily_year_share"]}},
                     sort_keys=True))


class Tests(unittest.TestCase):
    def test_calendar_and_window_endpoints(self):
        ds = dates()
        spans = C.windows(ds, 3)
        self.assertEqual(len(spans), 130)
        self.assertEqual(spans[0], (date(2016, 1, 26), date(2016, 1, 29),
                                   tuple(date(2016, 1, d) for d in (27, 28, 29))))
        self.assertEqual(spans[-1][1], date(2026, 10, 30))
        self.assertEqual(C.next_three(ds)[-1][1], date(2026, 11, 4))
        self.assertEqual(len(ds), 2740)
        self.assertEqual(ds[0], date(2016, 1, 4))
        self.assertEqual(ds[-1], date(2026, 11, 24))
        self.assertNotIn(date(2018, 12, 5), ds)
        self.assertNotIn(date(2025, 1, 9), ds)

    def test_cash_dividend_on_ex_date_once_and_costs(self):
        buy, middle, sale, after = (date(2020, 1, d) for d in (27, 28, 29, 30))
        bars = {d: C.Bar(p, p, p, p, 1) for d, p in ((buy, 100), (middle, 98), (sale, 105))}
        payouts = C.distributions([dict(ex_date=str(d), amount=a)
                                  for d, a in ((buy, 10), (middle, 2), (sale, 1), (after, 10))])
        spans = [(buy, sale, (middle, sale))]
        self.assertAlmostEqual(C.window_values(bars, payouts, spans, 0)[0][1], 0.08)
        self.assertAlmostEqual(C.window_values(bars, payouts, spans, 2)[0][1],
                               (105 * (1-.0002) + 3) / (100 * (1+.0002)) - 1)
        self.assertAlmostEqual(C.window_values(bars, {}, spans, 0)[0][1], 0.05)

    def test_daily_drift_comparator_and_defined_threshold(self):
        a = [0.01, 0.02, 0.03, 0.04]
        b = [0.00, 0.01, 0.02, 0.03]
        out = C.compare(a, b)
        self.assertAlmostEqual(out["difference"], 0.01)
        self.assertAlmostEqual(out["welch_t"], 0.01 / (2*(0.0005/3)/4)**0.5)
        self.assertIsNone(C.compare([0.02]*3, [0.01]*4)["welch_t"])
        self.assertIsNone(C.one_sample([0.01]*3))

    def test_last_three_not_first_three_and_plant_passes(self):
        ds = dates()
        r = C.evaluate(ds, plant(ds, 2500, 0, 0.003), {})
        self.assertTrue(r["judged"]["passes"])
        self.assertEqual(r["judged"]["daily_comparison"]["inside_n"], 390)
        self.assertEqual(r["judged"]["daily_comparison"]["inside_n"] +
                         r["judged"]["daily_comparison"]["outside_n"],
                         sum(C.FIRST <= d <= C.LAST for d in ds[1:]))
        self.assertLess(r["shown"]["next_month_first_three_at_2bps"]["mean_net"], r["judged"]["mean_net"])
        self.assertLess(r["shown"]["other_costs_same_window"]["10"]["mean_net"],
                        r["shown"]["other_costs_same_window"]["5"]["mean_net"])

    def test_positive_bond_drift_cannot_pass_without_daily_edge(self):
        ds = dates()
        r = C.evaluate(ds, plant(ds, 2500, 0.002, 0), {})["judged"]
        self.assertTrue(r["gates"]["positive_mean"])
        self.assertFalse(r["gates"]["daily_difference_and_t"])
        self.assertFalse(r["passes"])

    def test_auditor_one_regime_passed_original_seven_but_now_fails(self):
        ds = dates()
        judged = C.evaluate(ds, auditor_one_regime(ds), {})["judged"]
        gates = judged["gates"]
        new = {"every_leave_one_year_out_positive", "positive_daily_year_share"}
        self.assertEqual(len(gates), 9)
        self.assertTrue(all(v for k, v in gates.items() if k not in new))
        self.assertFalse(gates["every_leave_one_year_out_positive"])
        self.assertFalse(gates["positive_daily_year_share"])
        self.assertFalse(judged["passes"])
        self.assertLess(judged["leave_one_year_out"]["2022"]["mean_net"], 0)
        self.assertEqual(judged["leave_one_year_out"]["2022"]["n"], 118)
        self.assertEqual(judged["leave_one_year_out"]["2026"]["n"], 120)
        self.assertEqual(judged["daily_comparison_by_year"]["2022"]["inside_n"], 36)
        self.assertEqual(judged["daily_comparison_by_year"]["2026"]["inside_n"], 30)
        self.assertTrue(all({"inside_mean", "outside_mean"} <= set(row)
                            for row in judged["daily_comparison_by_year"].values()))

    def test_flat_run_and_isolated_untradeable_bar(self):
        row = dict(o=10, h=10, l=10, c=10, v=0)
        ds = dates()[:5]
        with self.assertRaisesRegex(C.Refused, "^P25_FLAT_RUN$"):
            C.price_tape([row]*5, ds)
        with self.assertRaisesRegex(C.Refused, "^P25_FLAT_RUN$"):
            C.price_tape([dict(o=10, h=12, l=9, c=11, v=100)]*5, ds)
        with self.assertRaisesRegex(C.Refused, "^P25_ZERO_VOLUME$"):
            C.price_tape([row, row|{"v": 1}], ds[:2])
        with self.assertRaisesRegex(C.Refused, "^P25_ZERO_VOLUME$"):
            C.price_tape([row | dict(o=i, h=i, l=i, c=i) for i in range(10, 15)], ds)

    def test_fetch_pages_query_and_clocks_without_ohlc(self):
        seen = []
        a = {"t": "2020-03-06T05:00:00Z", "v": 1}
        b = {"t": "2020-03-09T04:00:00Z", "v": 3}
        def mock(url):
            seen.append(url)
            return {"bars": {"TLT": [a if len(seen) == 1 else b]},
                    "next_page_token": "token" if len(seen) == 1 else None}
        rows = F.fetch("TLT", mock)
        self.assertEqual(C.check_bar_clocks(rows, (date(2020, 3, 6), date(2020, 3, 9))),
                         (date(2020, 3, 6), date(2020, 3, 9)))
        self.assertIn("feed=sip", seen[0])
        self.assertIn("adjustment=raw", seen[0])
        self.assertIn("start=2016-01-04", seen[0])
        self.assertIn("2026-11-24", seen[0])
        self.assertIn("page_token=token", seen[1])
        with self.assertRaisesRegex(C.Refused, "^P25_BAR_CLOCK$"):
            C.check_bar_clocks([rows[0], rows[0]], (date(2020, 3, 6), date(2020, 3, 9)))

    def test_missing_2015_anchor_removes_only_one_outside_interval(self):
        ds = dates()
        old = (date(2015, 12, 31),) + ds
        spans = C.windows(ds, 3)
        self.assertEqual(spans, C.windows(old, 3))
        self.assertEqual(len(spans), 130)
        bars = {d: C.Bar(100, 100, 100, 100, 1) for d in old}
        before, old_years = C.daily_split(old, bars, {}, spans)
        after, new_years = C.daily_split(ds, bars, {}, spans)
        self.assertEqual((before["inside_n"], after["inside_n"]), (390, 390))
        self.assertEqual((before["outside_n"], after["outside_n"]), (2333, 2332))
        self.assertEqual(old_years["2016"]["outside_n"], new_years["2016"]["outside_n"] + 1)
        self.assertEqual({y: x for y, x in old_years.items() if y != "2016"},
                         {y: x for y, x in new_years.items() if y != "2016"})
        jan = [{"t": f"{d}T05:00:00Z", "v": 1} for d in ds[:3]]
        self.assertEqual(C.check_bar_clocks(jan, ds[:3]), ds[:3])
        with self.assertRaisesRegex(C.Refused, "^P25_BAR_CLOCK$"):
            C.check_bar_clocks(jan[1:], ds[:3])
        with self.assertRaisesRegex(C.Refused, "^P25_BAR_CLOCK$"):
            C.check_bar_clocks([jan[0], jan[2]], ds[:3])

    def test_distribution_metadata_refuses_duplicate_action(self):
        ds = dates()
        row = {"id": "invented", "ex_date": str(ds[3]), "amount": "not checked by fetcher"}
        fund = {"source": "https://example.com", "splits": [], "cash": [row]}
        packet = dict(schema=1, coverage_start=str(C.ACTION_COVERAGE_FROM), coverage_end=str(C.DATA_END),
                      funds={s: fund for s in C.SYMBOLS})
        C.check_actions(packet, ds)
        with self.assertRaisesRegex(C.Refused, "^P25_ACTION_AMOUNT$"):
            C.distributions([row])
        fund["cash"].append(row)
        with self.assertRaisesRegex(C.Refused, "^P25_ACTION_CLOCK$"):
            C.check_actions(packet, ds)

    def test_refusal_no_claim_and_failure_after_claim_stays_claimed(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            lock, result = root / "score_25.lock", root / "results_25.json"
            def fail():
                self.assertFalse(lock.exists())
                raise C.Refused("invented")
            with self.assertRaises(C.Refused):
                S.claim(root, {}, fail, self.fail)
            self.assertFalse(lock.exists())
            def crash(_):
                self.assertTrue(lock.exists())
                raise RuntimeError
            with self.assertRaises(RuntimeError):
                S.claim(root, {}, lambda: None, crash)
            self.assertFalse(result.exists())
            with self.assertRaisesRegex(C.Refused, "^P25_CONSUMED$"):
                S.claim(root, {}, self.fail, self.fail)

    def test_clean_claim_and_limits(self):
        ds = dates()
        tape = {s: plant(ds, 2501, 0, 0.003) for s in C.SYMBOLS}
        with TemporaryDirectory() as d:
            root = Path(d)
            with patch("common_25.evaluate", wraps=C.evaluate) as calc:
                def validate():
                    self.assertEqual(calc.call_count, 0)
                    self.assertFalse((root/"score_25.lock").exists())
                    return {"mode": F.RAW}, ds, tape, {s: {} for s in C.SYMBOLS}
                def run(inputs):
                    self.assertTrue((root/"score_25.lock").exists())
                    return S.outcome({}, inputs)
                S.claim(root, {}, validate, run)
            r = json.loads((root/"results_25.json").read_bytes())
            self.assertIn("passes", r["judged_TLT"])
            self.assertNotIn("passes", r["shown_IEF_same_rule"])
            self.assertTrue(any("auction" in line for line in r["limits"]))
            self.assertTrue(any("raw SIP" in line for line in r["limits"]))

    def test_auditor_null_draft_digests_refuse_before_payload_reads(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            payload = F.encode(dict.fromkeys(F.DRAFT_FILES))
            (root/"PINNED.json").write_bytes(payload)
            (root/F.DRAFT_FILES[0]).write_text("Status FROZEN.\n")
            # Only the correctly pinned outer manifest may be read.
            real_read = Path.read_bytes
            def manifest_only(path):
                self.assertEqual(path.name, "PINNED.json")
                return real_read(path)
            with patch("fetch_25.HERE", root), patch.object(Path, "read_bytes", manifest_only):
                with self.assertRaisesRegex(C.Refused, "^P25_PIN$"):
                    F.draft(F.digest(payload))

    def test_pin_format_checked_before_open(self):
        with patch.object(Path, "stat", side_effect=AssertionError("must not stat")):
            for bad in (None, 3, [], "", "a"*63, "A"*64, "g"*64, "f"*64+"\n"):
                with self.subTest(bad=bad), self.assertRaisesRegex(C.Refused, "^P25_PIN$"):
                    F.pinned(Path("unused"), bad)

    def test_prepare_binds_each_input_and_refuses_mode_mismatch(self):
        ds = (date(2020, 3, 6), date(2020, 3, 9))
        def bars(px):
            return F.encode([dict(t=stamp, o=px, h=px, l=px, c=px, v=10)
                             for stamp in ("2020-03-06T05:00:00Z", "2020-03-09T04:00:00Z")])
        payload = bars(10)
        actions = F.encode(dict(schema=1, coverage_start=str(C.ACTION_COVERAGE_FROM), coverage_end=str(C.DATA_END),
                                funds={s: {"source": "https://example.com", "splits": [],
                                           "cash": [{"id": s, "ex_date": str(ds[0]), "amount": 1}]}
                                       for s in C.SYMBOLS}))
        action_pin = F.digest(actions)
        key = "a"*64
        with TemporaryDirectory() as temp:
            root = Path(temp)
            inp = root / "inputs"
            inp.mkdir(mode=0o700)
            def put(name, data):
                path = inp / name
                path.write_bytes(data)
                path.chmod(0o600)
            files = {s + ".json": F.digest(payload) for s in C.SYMBOLS}
            put("cash_actions.json", actions)
            for name in files:
                put(name, payload)
            files["cash_actions.json"] = action_pin
            index = dict(schema=1, mode=F.RAW, feed="sip", adjustment="raw", start=str(C.BAR_FROM),
                         end=str(C.DATA_END), collected_utc="synthetic", draft_sha256=key, files=files)
            def manifest():
                data = F.encode(index)
                put("manifest.json", data)
                return F.digest(data)
            with patch("fetch_25.draft", return_value=ds):
                pin = manifest()
                with patch("common_25.evaluate", side_effect=AssertionError("must not evaluate")):
                    self.assertEqual(S.prepare(key, pin, action_pin, root)[1], ds)
                put("TLT.json", bars(75))
                with self.assertRaisesRegex(C.Refused, "^P25_PIN$"):
                    S.claim(root, {}, lambda: S.prepare(key, pin, action_pin, root), self.fail)
                self.assertFalse((root/"score_25.lock").exists())
                # Auditor's null-child witness: approve the same outer SHA, then
                # change the synthetic close. Refuse both before reading members.
                files["TLT.json"] = None
                null_pin = manifest()
                real_read = Path.read_bytes
                def manifest_only(path):
                    self.assertEqual(path.name, "manifest.json")
                    return real_read(path)
                for px in (10, 75):
                    put("TLT.json", bars(px))
                    with patch.object(Path, "read_bytes", manifest_only):
                        with self.assertRaisesRegex(C.Refused, "^P25_PIN$"):
                            S.claim(root, {}, lambda: S.prepare(key, null_pin, action_pin, root), self.fail)
                    self.assertFalse((root/"score_25.lock").exists())
                put("TLT.json", payload)
                files["TLT.json"] = F.digest(payload)
                with self.assertRaisesRegex(C.Refused, "^P25_ACTION_PIN$"):
                    S.prepare(key, manifest(), "b"*64, root)
                index.update(mode="adjusted_no_free_dated_source", adjustment="all")
                with self.assertRaisesRegex(C.Refused, "^P25_MANIFEST$"):
                    S.prepare(key, manifest(), action_pin, root)
                index.update(mode=F.RAW, adjustment="raw")
                del files["cash_actions.json"]
                with self.assertRaisesRegex(C.Refused, "^P25_MANIFEST$"):
                    S.prepare(key, manifest(), action_pin, root)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--calibration", action="store_true")
    opt = p.parse_args()
    if opt.calibration:
        calibration()
    else:
        unittest.main(argv=[__file__], verbosity=2)
