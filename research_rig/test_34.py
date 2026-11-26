"""No real input opens. Synthetic economics, schema refusals and CLI lifecycle."""
import contextlib
import io
import json
import os
import tempfile
import unittest
from datetime import date, timedelta
from hashlib import sha256
from itertools import permutations
from pathlib import Path
from unittest.mock import patch

import common_25 as C
import measure_34 as M

HERE = Path(__file__).resolve().parent
ZERO = "0" * 64
ONE = "1" * 64


def model():
    spans = []
    for i in range(4):
        a = date(2024 + i // 2, 3 + (i % 2), 24)
        d = [a + timedelta(days=j) for j in (1, 2, 3)]
        spans.append((a, d[-1], tuple(d)))
    prices = lambda k: {day: x for i, (a, _, ds) in enumerate(spans)
                        for day, x in zip((a, *ds), (100, 100, 100, 100 + (i + 1) * k))}
    q = {d: (99.9, 100.1) for a, b, _ in spans for d in (a, b)}
    return spans, (prices(1), {}, {}), {"TMF": (prices(3), {}, {}, (q, 1)), "UBT": (prices(2), {}, {}, (q, 2))}


def row(day, quotes):
    a, b = M.quote_bounds(day)
    return dict(session=day.isoformat(), request_start=a, request_end=b, complete=True, quotes=quotes)


def quote(at, bid=99, ask=101, size=2):
    return {"t": at, "bp": bid, "ap": ask, "bs": size, "as": size}


class TestM34(unittest.TestCase):
    def test_pinned_sessions(self):
        _, w, days, endpoints = M.plan_schedule(C, json.loads((HERE / "calendar_25.json").read_bytes()))
        self.assertEqual((len(w), len(days), len(endpoints)), (130, 520, 260))
        self.assertEqual((w[0][0].isoformat(), w[-1][1].isoformat()), ("2016-01-26", "2026-10-30"))

    def test_closes_standard_daylight_and_early(self):
        self.assertEqual(M.quote_bounds(date(2016, 1, 29))[1], "2016-01-29T21:00:00Z")
        self.assertEqual(M.quote_bounds(date(2026, 10, 30))[1], "2026-10-30T20:00:00Z")
        self.assertEqual(M.quote_bounds(date(2024, 11, 29)), ("2024-11-29T17:59:00Z", "2024-11-29T18:00:00Z"))

    def test_latest_nanosecond_and_locked_quote(self):
        d = date(2024, 11, 29)
        q1 = quote("2024-11-29T17:59:59.999999990Z")
        q2 = quote("2024-11-29T17:59:59.999999991Z", 102, 102)
        self.assertEqual(M.quote_book([row(d, [q1, q2, q2])], [d]), ({d: (102, 102)}, 1))

    def test_bad_final_cannot_fall_back(self):
        d = date(2024, 11, 29)
        valid = quote("2024-11-29T17:59:00Z")
        t = "2024-11-29T17:59:59Z"
        for bad in (quote(t, 102, 101), quote(t, 0, 101), quote(t, size=0), quote(t, True, 101)):
            with self.subTest(bad=bad), self.assertRaisesRegex(M.Refused, "QUOTE_FINAL"):
                M.quote_book([row(d, [valid, bad])], [d])

    def test_latest_max_relative_spread_is_order_independent(self):
        d = date(2024, 11, 29)
        t = "2024-11-29T17:59:59Z"
        earlier = quote("2024-11-29T17:59:58Z", 1, 500)
        # 98/100 and 49/50 have a wider relative spread than 998/1002.
        group = [quote(t, 98, 100), quote(t, 49, 50), quote(t, 998, 1002)]
        for order in permutations(group):
            self.assertEqual(M.quote_book([row(d, [earlier, *order])], [d]), ({d: (49, 50)}, 1))

    def test_malformed_latest_tie_refused_in_both_orders(self):
        d = date(2024, 11, 29)
        t = "2024-11-29T17:59:58Z"
        good = quote(t, size=1)
        bad = good | {"bs": True}
        for rows in ([good, bad], [bad, good]):
            with self.assertRaisesRegex(M.Refused, "QUOTE_FINAL"):
                M.quote_book([row(d, rows)], [d])
            q = quote("2024-11-29T17:59:59Z")
            self.assertEqual(M.quote_book([row(d, [*rows, q])], [d]), ({d: (99, 101)}, 0))

    def test_flat_guard_resets_after_unobserved_gap(self):
        d = tuple(date(2024, m, j) for m in (6, 7) for j in (25, 26, 27, 28))
        rows = [dict(t=f"{day}T04:00:00Z", o=99, h=100, l=98, c=99, v=1) for day in d]
        self.assertEqual(M.check_tape(C, rows, d, width=4), dict.fromkeys(d, 99))
        with self.assertRaisesRegex(C.Refused, "FLAT_RUN"):
            M.check_tape(C, rows, d)

    def test_clock_scope_order_and_coverage(self):
        d = date(2024, 11, 29)
        a, b = M.quote_bounds(d)
        for qs in ([quote(b)], [quote("2024-11-29T17:58:59.999999999Z")],
                   [quote("2024-11-29T17:59:50Z"), quote(a)]):
            with self.subTest(qs=qs), self.assertRaisesRegex(M.Refused, "QUOTE_CLOCK"):
                M.quote_book([row(d, qs)], [d])
        with self.assertRaisesRegex(M.Refused, "QUOTE_COVERAGE"):
            M.quote_book([row(d, [quote(a)]) | {"complete": False}], [d])

    def test_split_and_cash_entry_excluded_exit_included(self):
        a = date(2024, 1, 26)
        b, c, d = [a + timedelta(days=i) for i in (1, 2, 3)]
        w = a, d, (b, c, d)
        path = M.window_path(w, {a: 100, b: 50, c: 52, d: 55}, {a: (99,), b: (1,), d: (1, 2)},
                             {a: (3, 1), b: (2, 1)}, .01, .02)
        self.assertEqual([z[0] for z in path], [a, b, c, d])
        self.assertAlmostEqual(path[0][1], 100 / 101)
        self.assertAlmostEqual(path[1][1], 102 / 101)
        self.assertAlmostEqual(path[-1][1], (110 * .98 + 8) / 101)

    def test_daily_drawdown_inside_winning_window(self):
        a = date(2024, 5, 27)
        b, c, d = [a + timedelta(days=i) for i in (1, 2, 3)]
        x, dd, equity = M.simulate([(a, d, (b, c, d))], ({a: 100, b: 120, c: 60, d: 110}, {}, {}), {})
        self.assertAlmostEqual(equity, 1.1)
        self.assertAlmostEqual(x[0][-1], .1)
        self.assertEqual(dd, dict(fraction=.5, peak=b.isoformat(), trough=c.isoformat()))

    def test_scenarios_ratios_worst_trim_and_no_ubt_marks(self):
        r = M.evaluate({}, model())["funds"]
        self.assertAlmostEqual(r["TMF"]["gross_tracking_ratio"], 3)
        self.assertAlmostEqual(r["UBT"]["gross_tracking_ratio"], 2)
        self.assertNotIn("marks", r["UBT"])
        self.assertEqual([r[s]["tied_quote_endpoints"] for s in ("TMF", "UBT")], [1, 2])
        self.assertIn("conservative tied-endpoint estimate", r["TMF"]["tied_quote_policy"])
        for name in ("TMF", "UBT"):
            arms = r[name]["arms"]
            self.assertEqual(list(arms), list(M.ARMS))
            self.assertLess(arms["fixed_10bps"]["mean_net"], arms["fixed_5bps"]["mean_net"])
            fixed = arms["fixed_2bps"]
            self.assertEqual(fixed["n"], 4)
            self.assertAlmostEqual(fixed["worst_window"]["net"], fixed["trimmed_mean"])
            self.assertEqual(fixed["worst_year_compounded"], "2024")
            self.assertEqual(fixed["positive_year_share"], 1)
            self.assertEqual(arms["measured_half_spread"]["net_tracking_reference"], "TLT_fixed_2bps")
            self.assertEqual(arms["fixed_5bps"]["net_tracking_reference"], "TLT_fixed_5bps")

    def test_additive_mark_not_spread_only(self):
        spans, tlt, funds = model()
        a = {d: 100 if d in [w[0] for w in spans] else 100.035 for w in spans for d in (w[0], *w[2])}
        bids = {d: (99.995, 100.005) for d in funds["TMF"][-1][0]}
        funds["TMF"] = (a, {}, {}, (bids, 0))
        r = M.evaluate({}, (spans, tlt, funds))["funds"]["TMF"]
        self.assertGreater(r["arms"]["measured_half_spread"]["mean_net"], 0)
        self.assertLess(r["arms"]["fixed_2bps_plus_half_spread"]["mean_net"], 0)
        self.assertFalse(r["marks"]["positive_net_at_fixed_2bps_plus_half_spread"])

    def test_zero_tlt_mean_ratio_undefined(self):
        spans, (_, cash, splits), funds = model()
        flat = {d: 100 for w in spans for d in (w[0], *w[2])}
        out = M.evaluate({}, (spans, (flat, cash, splits), funds))
        self.assertIsNone(out["funds"]["TMF"]["gross_tracking_ratio"])
        self.assertFalse(out["funds"]["TMF"]["marks"]["gross_tracking_band"])

    def test_actions_issuer_known_splits_and_basis(self):
        d0, d1, d2 = date(2023, 12, 4), date(2020, 8, 18), date(2016, 8, 25)
        issuer_497 = "https://www.sec.gov/Archives/edgar/data/1424958/000119312516658234/0001193125-16-658234.txt"
        expected = {
            "TMF": {d0: (1, 10, "https://www.direxion.com/press-release/direxion-announces-reverse-splits-of-tmf-and-labu"),
                    d2: (4, 1, issuer_497)},
            "UBT": {d1: (2, 1, "https://www.proshares.com/press-releases/proshares-announces-etf-share-splits-80420")},
        }
        days = [d0, d1, d2]
        for sym, effective in (("TMF", d0), ("UBT", d1)):
            source = "https://www." + M.FUNDS[sym] + "/test-issuer"
            splits = [dict(id=d.isoformat(), effective_date=d.isoformat(), new=n, old=o, source=u)
                      for d, (n, o, u) in expected[sym].items()]
            a = dict(schema=1, symbol=sym, currency="USD", coverage_start="2016-01-04", coverage_end="2026-10-30",
                     share_basis="contemporaneous_ex_date_post_split", reviewer="toy",
                     cash=[dict(id="p", ex_date=effective.isoformat(), amount=.5, source=source)],
                     splits=splits)
            self.assertEqual(M.fund_actions(a, sym, days), ({effective: [.5]},
                             {d: v[:2] for d, v in expected[sym].items()}))
            for invalid in (splits[:-1], splits[:-1] + [splits[-1] | {"source": issuer_497 + "?other"}],
                            splits[:-1] + [splits[-1] | {"new": splits[-1]["new"] + 10}],
                            splits + [splits[-1] | {"id": "extra", "effective_date": "2018-01-02"}]):
                with self.assertRaisesRegex(M.Refused, "KNOWN_SPLIT"):
                    M.fund_actions(a | {"splits": invalid}, sym, [*days, date(2018, 1, 2)])
            with self.assertRaisesRegex(M.Refused, "ACTION_COVERAGE"):
                M.fund_actions(a | {"share_basis": "adjusted"}, sym, days)
            with self.assertRaisesRegex(M.Refused, "ACTION_ROW"):
                M.fund_actions(a | {"cash": [a["cash"][0] | {"source": issuer_497}]}, sym, days)

    def test_manifest_refuses_one_fund_incomplete_pins_or_wrong_source(self):
        m = dict(schema=1, symbols=["TMF", "UBT"], feed="sip", adjustment="raw", currency="USD",
                 bars_route="/v2/stocks/{symbol}/bars", quotes_route="/v2/stocks/{symbol}/quotes",
                 quote_scope="close_minus_60s_inclusive_to_close_exclusive", collected_utc="2026-11-26T00:00:00Z",
                 files=dict.fromkeys(M.INPUT_NAMES, ONE))
        M.manifest_check(m)
        for bad in ({"feed": "iex"}, {"adjustment": "all"}, {"symbols": ["TMF"]}, {"files": {"TMF.json": ONE}}):
            with self.subTest(bad=bad), self.assertRaises(M.Refused):
                M.manifest_check(m | bad)
        with self.assertRaisesRegex(M.Refused, "M34_PIN"):
            M.manifest_check(m | {"files": m["files"] | {"TMF.json": "wrong"}})

    def test_pin_refusal_no_open_and_private_no_link(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "x"
            with self.assertRaisesRegex(M.Refused, "PIN"):
                M.pinned(p, "broken", private=True)
            p.write_bytes(b"{}")
            p.chmod(0o600)
            h = sha256(b"{}").hexdigest()
            self.assertEqual(M.pinned(p, h, private=True), b"{}")
            with self.assertRaisesRegex(M.Refused, "DIGEST"):
                M.pinned(p, ZERO, private=True)
            link = p.with_name("link")
            link.symlink_to(p)
            with self.assertRaises(OSError):
                M.pinned(link, h, private=True)
            link.unlink()
            os.link(p, link)
            with self.assertRaisesRegex(M.Refused, "CUSTODY"):
                M.pinned(p, h, private=True)

    def test_strict_json(self):
        for b in (b'{"x":7,"x":6}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.assertRaisesRegex(M.Refused, "JSON"):
                M.decode(b)

    def test_validate_stops_before_return_or_claim(self):
        argv = ["measure_34.py", "--validate-inputs", "--approved-freeze-sha256", ONE, "--approved-input-sha256", ZERO]
        with patch.object(M.sys, "argv", argv), patch.object(M, "prepare", return_value=None) as prepare, \
             patch.object(M, "claim", side_effect=AssertionError), patch.object(M, "evaluate", side_effect=AssertionError), \
             contextlib.redirect_stdout(io.StringIO()) as out:
            M.main()
        prepare.assert_called_once_with(ONE, ZERO)
        self.assertTrue(out.getvalue().startswith("M34_INPUTS_OK"))

    def test_lock_exists_before_calculation_and_no_rerun(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            calls = []
            def evaluate():
                self.assertTrue((root / "run_34.lock").exists())
                self.assertFalse((root / "results_34.json").exists())
                calls.append("called")
                return {"toy": 1}
            M.claim(root, {"approved": True}, evaluate)
            with self.assertRaisesRegex(M.Refused, "ALREADY_RUN"):
                M.claim(root, {}, evaluate)
            self.assertEqual(calls, ["called"])
            self.assertEqual(json.loads((root / "results_34.json").read_bytes()), {"toy": 1})

    def test_durable_lock_then_eval_then_durable_result(self):
        import stat
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            order = []
            original = os.fsync
            def sync(fd):
                order.append("dir" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
                original(fd)
            def evaluate():
                order.append("eval")
                return {}
            with patch.object(M.os, "fsync", side_effect=sync):
                M.claim(root, {}, evaluate)
            self.assertEqual(order, ["file", "dir", "eval", "file", "dir"])

    def test_failure_after_claim_is_consumed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def bad():
                raise ArithmeticError
            with self.assertRaises(ArithmeticError):
                M.claim(root, {}, bad)
            self.assertTrue((root / "run_34.lock").exists())
            self.assertFalse((root / "results_34.json").exists())
            with self.assertRaisesRegex(M.Refused, "ALREADY_RUN"):
                M.claim(root, {}, lambda: {})


if __name__ == "__main__":
    unittest.main()
