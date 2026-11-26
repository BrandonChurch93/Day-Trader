"""Synthetic and calendar-only tests; no real market packets."""
from datetime import datetime, time, timezone
from hashlib import sha256
from io import StringIO
import math
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import common_31 as C
import score_31 as S

HERE = Path(__file__).resolve().parent
CAL_PIN = "e8f8a4322f988fcec6f937a19cfbfd0162a28f9b70813f305065c9e10ccb7c6b"


class DesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = S.pinned(HERE / "calendar_25.json", CAL_PIN)
        cls.days = C.calendar(S.parse(cls.raw))
        cls.schedule = C.design(cls.days)

    def test_clock_and_no_lookahead(self):
        all_inside = set().union(*(set(r[2]) for r in self.schedule.values()))
        observed = {k: len(r[3]) for k, r in list(self.schedule.items())[:5]}
        self.assertEqual(list(observed.values()), [14, 15, 32, 51, 69])
        observed = [k for k, r in self.schedule.items() if r[-1]]
        self.assertEqual((len(observed), observed[0], observed[-1]), (126, (2016, 5), (2026, 10)))
        for k, (buy, _, _, fit, _) in self.schedule.items():
            self.assertFalse(set(fit) & all_inside)
            if k == C.JAN:
                self.assertTrue(all(d < buy for d in fit))
            else:
                self.assertTrue(all((d.year, d.month) < k for d in fit))
        n_daily = sum((d.year, d.month) in observed for d in self.days[1:])
        self.assertEqual((n_daily, n_daily - 3*126), (2641, 2263))

    def test_two_factor_intercept_fit(self):
        x1 = [0.0, -0.2, 0.1, 0.5, 0.4]
        x2 = [0.0, 0.1, -0.1, 0.6, -0.4]
        y = [0.3 + 1.7*a - 0.6*b for a, b in zip(x1, x2)]
        p, q = C.slopes(y, x1, x2)
        self.assertAlmostEqual(p, 1.7)
        self.assertAlmostEqual(q, -0.6)
        with self.assertRaisesRegex(C.Refused, "FIT_SINGULAR"):
            C.slopes(y, x1, [2*x + 1 for x in x1])
        with self.assertRaisesRegex(C.Refused, "FIT_SINGULAR"):
            C.slopes(y, x1, [1]*5)

    def test_full_synthetic_pool_and_marks(self):
        bars = {sym: {} for sym in C.SYMBOLS}
        cash = {sym: {} for sym in C.SYMBOLS}
        levels = {sym: 100.0 for sym in C.SYMBOLS}
        all_inside = set().union(*(set(r[2]) for r in self.schedule.values()))
        for i, day in enumerate(self.days):
            a, b, s = 0.0006*math.sin(i/7), 0.0005*math.cos(i/13), 0.001*math.sin(i/17)
            changes = {"IEF": a, "IEI": b, "SPY": s}
            for j, sym in enumerate(C.FUNDS, 1):
                t = changes[C.PROXY[sym]]
                changes[sym] = (0.7+j/10)*t + (-0.1+j/10)*s + (0.0007 if day in all_inside else 0)
            for sym, r in changes.items():
                levels[sym] *= 1+r
                p = levels[sym]
                bars[sym][day] = C.prior.Bar(p, p*1.01, p*0.99, p, 100)
        report = C.evaluate(self.days, bars, cash, self.schedule)
        judged = report["judged"]
        self.assertEqual(judged["n"], 126)
        self.assertEqual(len(judged["gates"]), 10)
        self.assertTrue(judged["passes"], judged["gates"])
        self.assertEqual((judged["daily"]["inside_n"], judged["daily"]["outside_n"]), (378, 2263))
        self.assertEqual([r["fit_intervals"] for r in report["shown"]["warmup_months"]], [14, 15, 32, 51])
        by_cost = report["shown"]["by_cost"]
        for cost, bucket in by_cost.items():
            self.assertAlmostEqual(bucket["residual"]["mean_net"],
                                   C.prior.fmean(f["residual"]["mean_net"] for f in bucket["by_fund"].values()))
            self.assertFalse(any("gates" in f for f in bucket["by_fund"].values()))
        self.assertGreater(by_cost["2"]["plain"]["mean_net"], by_cost["10"]["plain"]["mean_net"])

    def test_tenth_mark_does_not_follow_residual(self):
        dummy = {c: (-0.01, 0.01, {s: -0.01 for s in C.FUNDS}, {s: 0.01 for s in C.FUNDS})
                 for c in C.prior.COSTS}
        beta = {s: (1, 2) for s in C.FUNDS}
        sample = [(2020, dummy, beta), (2021, dummy, beta)]
        results = C.summarize(sample, [], {y: ([0.02, 0.01], [0.0, 0.001]) for y in C.prior.YEARS},
                              [0.02, 0.01], [0.0, 0.001])["judged"]
        self.assertTrue(results["gates"]["residual_positive_mean"])
        self.assertFalse(results["gates"]["plain_net_pooled_positive"])

    def test_pinned_private_packet_and_actions(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            src, dst = root / "input", root / "output"
            src.mkdir(mode=0o700)
            dst.mkdir(mode=0o700)
            session = lambda d: datetime.combine(d, time(), C.prior.NY).astimezone(timezone.utc).isoformat()
            bars = [{"t": session(d), "o": n+100, "h": n+102, "l": n+99, "c": n+101, "v": 100}
                    for n, d in enumerate(self.days)]
            first_by_year = {y: next(d for d in self.days if d.year == y) for y in C.prior.YEARS}
            actions = {"schema": 1, "coverage_start": str(C.START), "coverage_end": str(C.END),
                       "funds": {s: {"source": "https://example.test", "splits": [],
                                     "cash": [{"id": str(y), "ex_date": str(d), "amount": 0.5}
                                              for y, d in first_by_year.items()]} for s in C.SYMBOLS}}
            files = {s + ".json": S.encode(bars) for s in C.SYMBOLS}
            files["cash_actions.json"] = S.encode(actions)
            pins = {name: sha256(data).hexdigest() for name, data in files.items()}
            body = {"schema": 1, "vendor": "Synthetic", "feed": "sip", "adjustment": "raw", "frequency": "1Day",
                    "start": str(C.START), "end": str(C.END), "collected_utc": "2026-11-26T00:00:00Z", "files": pins}
            files["manifest.json"] = S.encode(body)
            for name, data in files.items():
                f = src / name
                f.write_bytes(data)
                f.chmod(0o600)
            m_pin = sha256(files["manifest.json"]).hexdigest()
            a_pin = pins["cash_actions.json"]
            with patch.object(C, "daily_returns", side_effect=AssertionError("must not score")):
                actual = S.load_inputs(src, dst, m_pin, a_pin, C, self.raw)
            self.assertEqual(len(actual[1]), 7)
            self.assertFalse(list(dst.iterdir()))
            with self.assertRaisesRegex(S.Refused, "ACTION_PIN"):
                S.load_inputs(src, dst, m_pin, "b"*64, C, self.raw)
            with self.assertRaisesRegex(S.Refused, "PIN"):
                S.load_inputs(src, dst, "b"*64, a_pin, C, self.raw)
            (src / "SPY.json").write_bytes(b"[]")
            with self.assertRaisesRegex(S.Refused, "PIN"):
                S.load_inputs(src, dst, m_pin, a_pin, C, self.raw)

    def test_cash_includes_exit_but_not_entry(self):
        buy, sell, earned, _, _ = self.schedule[(2016, 5)]
        fixed_bar = C.prior.Bar(100, 100, 100, 100, 1)
        bars = {buy: fixed_bar, sell: fixed_bar}
        dividends = {buy: 50, sell: 1}
        w = [(buy, sell, earned)]
        self.assertAlmostEqual(C.prior.window_values(bars, dividends, w, 0)[0][1], 0.01)
        self.assertAlmostEqual(C.prior.window_values(bars, dividends, w, 2)[0][1], 100.98/100.02 - 1)


class GateTests(unittest.TestCase):
    def test_frozen_manifest_roundtrips_through_scorer(self):
        # Index equals the committed tree in the clean operator worktree; using it
        # also checks the exact candidate during the precommit test.
        index_blob = S.git("show", f":research_rig/{S.PINS}").stdout
        manifest_blob = S.pinned(HERE / S.PINS, sha256(index_blob).hexdigest())
        self.assertEqual(manifest_blob, index_blob)
        pins = S.parse(manifest_blob)
        self.assertIs(type(pins), dict)
        self.assertEqual(set(pins), S.PIN_NAMES)
        for name, pin in pins.items():
            self.assertTrue(S.is_pin(pin))
            self.assertEqual(S.pinned(HERE / name, pin),
                             S.git("show", f":research_rig/{name}").stdout)

    def test_fixed_codes_only_on_bad_argument(self):
        stderr = StringIO()
        with patch.object(sys, "stderr", stderr), patch.object(sys, "argv", ["score_31.py", "--unknown-secret"]):
            with self.assertRaises(SystemExit):
                S.main()
        self.assertEqual(stderr.getvalue(), "P31_ARGUMENTS\n")

    def test_pin_syntax_checks_before_file_open(self):
        with patch.object(os, "open", side_effect=AssertionError("opened")):
            with self.assertRaisesRegex(S.Refused, "PIN"):
                S.pinned(Path("/does-not-exist"), "A"*64)

    def test_approval_line_binds_all_digests(self):
        commit, parent = "1"*40, "2"*40
        f, i, a = "f"*64, "1"*64, "a"*64
        line = (f"Approved by the lead: plan 31, validation and one scored run, freeze commit {parent}, "
                f"freeze SHA-256 {f}, input SHA-256 {i}, cash actions SHA-256 {a}.\n").encode()
        def git(*args, allow=False):
            if args[0] == "rev-parse":
                return SimpleNamespace(stdout=commit.encode())
            if args[0] == "status":
                return SimpleNamespace(stdout=b"")
            if args[0] == "show":
                return SimpleNamespace(stdout=line)
            raise AssertionError("approval mismatch must stop before ancestry or file reads")
        with patch.object(S, "git", git):
            with self.assertRaisesRegex(S.Refused, "APPROVAL"):
                S.authorize(commit, f, "b"*64, a)

    def test_claim_precedes_math_and_failed_math_consumes_attempt(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            durable = []
            def sync(path):
                self.assertTrue((path / "score_31.lock").exists())
                durable.append(path)
            def calculate():
                self.assertTrue((root / "score_31.lock").exists())
                self.assertEqual(durable, [root])
                raise ArithmeticError()
            with patch.object(S, "sync_dir", sync), self.assertRaises(ArithmeticError):
                S.once(root, {"ledger": 166}, (), calculate)
            self.assertFalse((root / "results_31.json").exists())
            with self.assertRaisesRegex(S.Refused, "CONSUMED"):
                S.once(root, {}, (), self.fail)

    def test_order_success_and_old_result_refusal(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            S.once(root, {"ledger": 166}, (), lambda: {"judged": {"n": 100}})
            result = S.parse((root / "results_31.json").read_bytes())
            self.assertEqual(result["judged"]["n"], 100)
            self.assertEqual(S.parse((root / "score_31.lock").read_bytes()), result["job"])
            with self.assertRaisesRegex(S.Refused, "CONSUMED"):
                S.unused(root)


if __name__ == "__main__":
    unittest.main()
