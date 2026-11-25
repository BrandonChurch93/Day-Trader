"""Invented session and fund prices only. Never opens vendor data."""

import calendar
from datetime import date, timedelta
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

import run_06 as run06


def synthetic():
    cfg = run06.cfg()
    sym = tuple(cfg["data"]["symbols"])
    lo, hi = date(2019, 1, 1), date(2021, 4, 30)
    days = [lo + timedelta(days=i) for i in range((hi - lo).days + 1)]
    dates = tuple(d.isoformat() for d in days if d.weekday() < 5)
    month_ends = {a for a, b in zip(dates, dates[1:]) if a[:7] != b[:7]}
    if hi.day == calendar.monthrange(hi.year, hi.month)[1]:
        month_ends.add(hi.isoformat())
    prices = np.tile(np.linspace(100, 170, len(dates))[:, None], (1, len(sym)))
    for s in ("BIL", "IEF"):
        prices[:, sym.index(s)] = 100
    return cfg, run06.Market(dates, sym, prices.copy(), prices), month_ends


class ReplayFixtures(unittest.TestCase):
    def test_gain_and_loss(self):
        # Same always-in rule: wins against a flat holding on a rise, loses on a fall.
        plan = np.array([[[1.0, 0.0]], [[np.nan, np.nan]], [[np.nan, np.nan]]])
        hold = plan.copy()
        hold[0, 0] = [0, 1]
        for expected, prices in ((1.5, [100, 110, 150]), (0.6, [100, 90, 60])):
            market = np.column_stack((prices, [100, 100, 100]))
            rule = run06.simulate(plan, market, market, 1, 0)
            baseline = run06.simulate(hold, market, market, 1, 0)
            self.assertAlmostEqual(rule["eq"][-1], expected)
            self.assertAlmostEqual(baseline["eq"][-1], 1)
            self.assertEqual(rule["eq"][-1] > baseline["eq"][-1], expected > 1)
            self.assertEqual(rule["sides"], 1)

    def test_fee_buy_then_switch(self):
        plan = np.array([[[1.0, 0.0]], [[0.0, 1.0]]])
        market = np.array([[100, 100], [110, 100]])
        fee = 5 / 10_000
        row = run06.simulate(plan, market, market, 1, 5)
        self.assertAlmostEqual(row["eq"][1], 1 / (1 + fee))
        self.assertAlmostEqual(row["eq"][2], 1.1 * (1 - fee) / (1 + fee) ** 2)
        self.assertEqual(row["sides"], 3)

    def test_month_end_lookahead(self):
        config, m, month_ends = synthetic()
        start, end = m.dates.index("2020-02-03"), m.dates.index("2020-03-05") + 1
        self.assertEqual(m.dates[start - 1], "2020-01-31")
        old = run06.targets(m, start, end, month_ends, config["rules"], "BIL")
        c = m.close.copy()
        sp = m.symbols.index("SPY")
        c[start:, sp] = 1
        after = run06.targets(run06.Market(m.dates, m.symbols, m.opening, c), start, end,
                              month_ends, config["rules"], "BIL")
        for r in run06.RULES:
            np.testing.assert_array_equal(old[r][0], after[r][0])
        self.assertEqual(old["G4"][0, 0, sp], 1)
        k = m.dates.index("2020-03-02") - start
        self.assertEqual(list(np.flatnonzero(np.isfinite(old["G4"][:, 0, 0]))), [0, k])
        self.assertEqual(old["G4"][k, 0, sp], 1)
        self.assertEqual(after["G4"][k, 0, sp], 0)

    def test_trading_band_uses_prior_close_not_next_open(self):
        plan = np.array([[[.50, .50]], [[.60, .40]], [[.70, .30]]])
        opening = np.array([[100, 100], [1000, 100], [100, 100]])
        close = np.full((3, 2), 100)
        row = run06.simulate(plan, opening, close, 1, 0, band=.10)
        self.assertEqual(row["instructions"].ravel().tolist(), [True, False, True])
        late = run06.simulate(plan, opening, close, 1, 0, band=.10,
                              fixed=row["instructions"], late=True)
        self.assertEqual(row["instructions"].ravel().tolist(), late["instructions"].ravel().tolist())

    def test_held_reset_and_impossible_shuffle(self):
        config, m, month_ends = synthetic()
        a = run06.Slice(m, "2020-02-03", "2020-12-31", month_ends, config)
        b = run06.Slice(m, "2021-01-01", "2021-04-30", month_ends, config)
        self.assertAlmostEqual(b.base["SPY"]["eq"][0], 1)
        self.assertGreater(a.base["SPY"]["eq"][-1], 1)
        self.assertEqual(b.base["SPY"]["sides"], 1)
        self.assertIsNone(run06.timing("G6", (a, b), config, np.random.default_rng(17)))
        self.assertIsNone(run06.timing("G4", (a, b), config, np.random.default_rng(17)))

    def test_leaders_tie_and_rebalance_targets(self):
        config, m, month_ends = synthetic()
        a = run06.Slice(m, "2020-02-03", "2021-01-04", month_ends, config)
        top = np.flatnonzero(a.plan["G5"][0, 0])
        self.assertEqual(sorted(m.symbols[i] for i in top), ["DBC", "EFA", "GLD"])
        self.assertAlmostEqual(a.plan["G6"][0, 0, m.symbols.index("SPY")], .6)
        points = np.flatnonzero(np.isfinite(a.plan["G6"][:, 0, 0]))
        self.assertEqual([a.dates[i] for i in points], ["2020-02-03", "2021-01-01"])
        self.assertAlmostEqual(sum(a.matched("G2")["average_weights"].values()), 1)

    def test_authorization_guards_before_prices(self):
        with TemporaryDirectory() as d:
            repo = Path(d)
            (repo / run06.PLAN).parent.mkdir()
            (repo / run06.DRAFT).write_text("draft")
            with self.assertRaisesRegex(ValueError, "rename the draft"):
                run06.authorize(repo)
            (repo / run06.DRAFT).unlink()
            (repo / run06.PLAN).write_text("frozen")
            (repo / run06.LEDGER).write_text("| Not replay 06 | G1 to G6 |")
            with self.assertRaisesRegex(ValueError, "ledger rows"):
                run06.authorize(repo)
            (repo / run06.LEDGER).write_text(
                "| 115 to 120 | planned | PREREG_06_fund_trend_paid_data.md | G1 to G6 | planned |\n")
            self.assertIsNone(run06.authorize(repo))
            with self.assertRaisesRegex(ValueError, "requires --prereg-commit"):
                run06.authorize(repo, held=True)

    def test_design_output_has_no_held_marks(self):
        config, m, month_ends = synthetic()
        a = run06.Slice(m, "2020-02-03", "2020-03-31", month_ends, config)
        result = run06.score({"design": a}, config)
        self.assertEqual(list(result["slices"]), ["design"])
        self.assertNotIn("pbo", result)
        self.assertEqual(result["costs_bps_per_side"]["base"], 5)

    def test_holdout_reservation_is_single_use(self):
        with TemporaryDirectory() as d:
            folder = Path(d)
            output = folder / "result.json"
            output.write_text("{}")
            with self.assertRaisesRegex(FileExistsError, "held result already exists"):
                run06.reserve_holdout(folder, output, "fixture")
            output.unlink()
            run06.reserve_holdout(folder, output, "fixture")
            with self.assertRaises(FileExistsError):
                run06.reserve_holdout(folder, output, "fixture")

    def test_two_slice_scoring_and_serialization(self):
        config, m, ends = synthetic()
        idx = np.arange(len(m.dates))
        prices = m.close.copy()
        prices[:, m.symbols.index("SPY")] *= 1 + .20 * np.sin(idx / 10)
        m = run06.Market(m.dates, m.symbols, prices, prices)
        config["data"] = dict(config["data"], design_start="2020-02-03")
        config["stats"] = dict(config["stats"], pbo_later_starts=["2020-04-01", "2020-06-01"])
        config["null"] = dict(config["null"], pbo_blocks=4, draws=7)
        a = run06.Slice(m, "2020-02-03", "2020-12-31", ends, config)
        b = run06.Slice(m, "2021-01-01", "2021-04-30", ends, config)
        result = run06.score({"design": a, "held": b}, config)
        self.assertEqual(set(result["rules"]), set(run06.RULES))
        self.assertEqual(len(result["pbo"]), 3)
        self.assertIsNotNone(result["rules"]["G2"]["shuffle"])
        self.assertIsNotNone(result["rules"]["G4"]["shuffle"])
        self.assertFalse(result["rules"]["G6"]["marks"]["m5"])
        json.dumps(run06.clean(result), allow_nan=False)

    def test_passing_and_failing_verdict(self):
        hold = dict(sharpe=.5, maxdd=-.2)
        safe = dict(sharpe=2, maxdd=-.05)
        bad = dict(sharpe=-1, maxdd=-.4)
        be = dict(status="bracketed", bps=30)
        self.assertTrue(run06.rig.five_marks(safe, hold, be, 5, 1, .1, 1)["passed"])
        self.assertFalse(run06.rig.five_marks(bad, hold, be, 5, 1, .1, 1)["passed"])


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ReplayFixtures)
    return int(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())


if __name__ == "__main__":
    raise SystemExit(run())
