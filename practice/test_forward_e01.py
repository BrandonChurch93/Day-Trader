"""Tests for practice/forward_e01.py with pretend data. No network, no key. Run: python3 practice/test_forward_e01.py"""
import json, sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forward_e01 as F

DEC = ["2026-12-%02d" % d for d in (1, 2, 3, 4, 7, 8, 9, 10, 11, 14, 15, 16, 17, 18, 21, 22, 23, 24, 28, 29, 30, 31)]


def bar(day, c):
    return {"t": f"{day}T05:00:00Z", "o": c, "h": c, "l": c, "c": c, "v": 1000}


class Fake:
    def __init__(self, days=DEC, entry_cross=80.00, exit_cross=81.00, venue="Q", div=None):
        self.days, self.calls = days, []
        self.entry_cross, self.exit_cross, self.venue, self.div = entry_cross, exit_cross, venue, div

    def __call__(self, path, params):
        assert any(__import__("re").fullmatch(p, path) for p in F.READS), path
        self.calls.append((path, dict(params)))
        if path.endswith("/bars"):
            return {"bars": [bar(d, 80.0 if d == "2026-12-28" else 81.0 if d == "2026-12-31" else 79.0) for d in self.days], "next_page_token": None}
        if path.endswith("/trades"):
            px = self.entry_cross if params["start"].startswith("2026-12-28") else self.exit_cross
            return {"trades": [{"t": "x", "x": self.venue, "p": px, "s": 1000000, "c": ["@", "6", "X"]},
                               {"t": "y", "x": self.venue, "p": px, "s": 1000000, "c": ["@", "M"]},
                               {"t": "z", "x": "P", "p": 1.0, "s": 5000000, "c": ["@", "6"]}], "next_page_token": None}
        if path == "/v1/corporate-actions":
            return {"corporate_actions": {"cash_dividends": self.div or []}, "next_page_token": None}
        raise AssertionError(path)


AFTER = datetime(2026, 12, 31, 21, 30, tzinfo=timezone.utc)


class T(unittest.TestCase):
    def test_return_matches_replay_formula(self):
        full, _, line = F.record("2026-12", get=Fake(), now=AFTER)
        f = 2 / 1e4
        self.assertAlmostEqual(full["net_return"], 81.0 * (1 - f) / (80.0 * (1 + f)) - 1, places=12)
        self.assertEqual((line["entry_cross_cost_bps"], line["exit_cross_cost_bps"]), (0.0, 0.0))
        self.assertTrue(line["counted"]); self.assertEqual(full["entry"]["cross_venue"], "Q")

    def test_signed_cost(self):
        _, _, line = F.record("2026-12", get=Fake(entry_cross=80.08, exit_cross=80.919), now=AFTER)
        self.assertAlmostEqual(line["entry_cross_cost_bps"], 10.0, places=3)   # bought 10 bps above the close
        self.assertAlmostEqual(line["exit_cross_cost_bps"], 10.0, places=3)    # sold 10 bps below it

    def test_t_label_counts_as_nasdaq(self):
        full, _, _ = F.record("2026-12", get=Fake(venue="T"), now=AFTER)
        self.assertEqual(full["entry"]["cross_venue"], "T")

    def test_distribution_only_on_held_sessions(self):
        div = [{"symbol": "TLT", "ex_date": "2026-12-29", "rate": 0.30, "id": "a"},
               {"symbol": "TLT", "ex_date": "2026-12-28", "rate": 9.99, "id": "b"}]  # ex on the entry day is not earned
        full, _, line = F.record("2026-12", get=Fake(div=div), now=AFTER)
        self.assertEqual(line["distribution_ex_dates"], ["2026-12-29"]); self.assertAlmostEqual(full["distribution_per_share"], 0.30)

    def test_refusals(self):
        with self.assertRaises(F.Refuse):
            F.record("2026-12", get=Fake(), now=datetime(2026, 12, 31, 21, 10, tzinfo=timezone.utc))  # too soon
        with self.assertRaises(F.Refuse):
            F.record("2026-12", get=Fake(days=DEC[:-1]), now=AFTER)  # bars do not match the pinned sessions
        with self.assertRaises(F.Refuse):
            F.record("2026-11", get=Fake(), now=AFTER)  # not in the table
        with self.assertRaises(F.Refuse):
            F.curl_get("/v2/orders", {})  # not a read on the list

    def test_late_record_is_not_counted(self):
        _, _, line = F.record("2026-12", get=Fake(), now=datetime(2027, 1, 1, 5, 1, tzinfo=timezone.utc))
        self.assertFalse(line["counted"])

    def test_save_once_and_stable(self):
        with tempfile.TemporaryDirectory() as d:
            log, off = Path(d) / "forward" / "E01_log.json", Path(d) / "off"
            _, blob, line = F.record("2026-12", get=Fake(), now=AFTER)
            F.save("2026-12", blob, line, log=log, off=off)
            a = log.read_text()
            self.assertNotIn("sip_close", a); self.assertNotIn("cross_price", a)  # no prices in the repo log
            with self.assertRaises(F.Refuse):
                F.save("2026-12", blob, line, log=log, off=off)
            self.assertEqual(a, log.read_text())
            _, blob2, line2 = F.record("2026-12", get=Fake(), now=AFTER)
            self.assertEqual(blob, blob2)

    def test_sessions_table(self):
        self.assertEqual(len(F.SESSIONS), 13)
        for m, (e, h) in F.SESSIONS.items():
            self.assertTrue(e < h[0] < h[1] < h[2]); self.assertEqual(h[2][:7], m)


if __name__ == "__main__":
    unittest.main(verbosity=1)
