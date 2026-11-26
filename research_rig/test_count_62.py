"""Synthetic tests only. Never call the approved measurement."""
from datetime import date, timedelta
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

tool = SimpleNamespace(**runpy.run_path(str(Path(__file__).with_name("count_62.py"))))


class VendorExCount(unittest.TestCase):
    def setUp(self):
        first = date(2025, 1, 6)
        self.days = [first + timedelta(days=i) for i in range(45)
                     if (first + timedelta(days=i)).weekday() < 5]
        self.schedule = {day: i for i, day in enumerate(self.days)}
        self.ex = self.days[15]
        self.e = SimpleNamespace(a="synthetic", declared=Decimal("2.00"), start=self.days[0], end=self.days[-1])

    def classify(self, *rows):
        return tool.classify(self.e, self.ex, [(self.days[15+i], F(v)) for i, v in rows], self.schedule)

    def test_partition_and_inclusive_boundaries(self):
        for expected, rows in [
            ("A", [(0, "1.99"), (1, "3")]),
            ("A", [(0, "2.50")]),
            ("B", [(0, "1.989"), (10, "1")]),
            ("B", [(0, "1.10"), (0, "1.10")]),
            ("C", [(-10, "1")]),
            ("C", [(10, "1")]),
            ("D", [(11, "1")]),
            ("D", [(-11, "3")]),
            ("E", []),
            ("F", [(-10, ".99"), (11, "2")]),
        ]:
            with self.subTest(expected=expected, rows=rows):
                self.assertEqual(self.classify(*rows), expected)

    def test_cohort_ignores_shown_only_and_nothing_about_placed_is_output(self):
        q = [SimpleNamespace(a=str(i)) for i in range(90)]
        gate = dict.fromkeys(tool.base.GATES, "pass") | dict.fromkeys(tool.base.SHOWN_GATES, "not_evaluable")
        rows = {e.a: dict(gates=gate | {"vendor_ex_agreement": tool.MISSING},
                         placed=False, stress_placed=False, liquid_placed=False, earlier_placed=False) for e in q}
        rows["88"]["gates"]["stock_vendor_basis"] = "vendor_basis_mismatch"
        rows["89"]["gates"]["vendor_ex_agreement"] = "pass"
        rows["89"]["placed"] = True
        self.assertEqual(tool.cohort({"summary": {}, "decisions": rows}, q), {e.a for e in q[:88]})

    def test_packet_scope_aggregation_and_provenance(self):
        e = self.e
        dates = self.days[1:-1]
        e.start, e.end = dates[0], dates[-1]
        cfg = {"action_checker": "reviewer", "custodian": "custodian"}
        act_row = {"id": "verified", "ex": str(self.ex), "kind": "special", "value": "2.00",
                   "payment": str(self.ex), "available": str(self.ex),
                   "sources": ["https://one.example/synthetic", "https://two.example/synthetic"]}
        actions = dict(version=1, reviewer="reviewer", records={e.a: {"stock": {
            "identity": "synthetic", "status": "complete", "start": str(e.start), "end": str(e.end),
            "target": "verified", "target_disclosure": {"accession": e.a}, "items": [act_row]}}})
        vendor_items = [{"type": "cash", "cash_usd": "1.00", "ex": str(self.days[-1])},
                        {"type": "unsupported", "ex": str(self.ex)}]
        vendor = dict(version=2, custodian="custodian", endpoint=tool.s.VENDOR_ENDPOINT, adoption={},
                      native_index_sha256="pin", records={e.a: {"stock": {
                          "identity": "synthetic", "start": str(e.start), "complete": True,
                          "views": {"all": "synthetic", "filing_all": "synthetic"}, "items": vendor_items}}})
        args = ([e], self.days, {e.a}, actions, vendor, cfg, {}, "pin")
        counts = tool.count(*args)
        self.assertEqual(counts, {"vendor_ex_missing_only": 1,
                                 "classes": dict.fromkeys(tool.BUCKETS, 0) | {"E": 1},
                                 "verified_action_ex_date_provenance": {
                                     "no_structured_ex_date_provenance": 1, "unrecognized_extra_fields": 0}})
        act_row["unstandardized"] = True
        vendor_items.append({"type": "cash", "cash_usd": "2.01", "ex": str(self.ex)})
        counts = tool.count(*args)
        self.assertEqual(counts["classes"]["A"], 1)
        self.assertEqual(counts["verified_action_ex_date_provenance"]["unrecognized_extra_fields"], 1)
        vendor_items.append({"type": "cash", "cash_usd": "2.00", "ex": str(self.ex)})
        with self.assertRaises(tool.p.Refused):
            tool.count(*args)

    def test_measurement_reads_exactly_four_pinned_private_inputs(self):
        blobs = {tool.p.CONFIG: b"cfg"} | dict.fromkeys(tool.p.CALENDARS, b"calendar")
        price = {"docket_sha256": "d", "actions.json": "a", "identities.json": "i", "bars.json": "b"}
        seen = []

        def read(path, digest, cap, *, private):
            self.assertTrue(private)
            seen.append((path, digest))
            return b"synthetic"

        scope = tool.measure.__globals__
        with patch.object(tool.s, "config", return_value={"docket_sha256": "d"}), \
                patch.object(tool.p, "calendar"), patch.object(tool.p, "events"), \
                patch.object(tool.p, "parse"), patch.object(tool.p, "file_bytes", side_effect=read), \
                patch.dict(scope, {"cohort": lambda *_: set(), "count": lambda *_: {}}):
            self.assertEqual(tool.measure("decisions-pin", blobs, price, "vendor-pin", "index-pin"), {})
        self.assertEqual(seen, [(tool.p.DOCKET, "d"), (tool.DECISIONS, "decisions-pin"),
                                (tool.p.INPUT / "actions.json", "a"), (tool.s.VENDOR / tool.s.VENDOR_NAME, "vendor-pin")])


if __name__ == "__main__":
    unittest.main()
