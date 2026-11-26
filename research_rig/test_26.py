"""Offline synthetic fixtures only. No feeds or research data are opened."""
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import common_26 as C
import score_26 as S


def fixture_days():
    return (C.FIRST, C.FIRST + timedelta(days=1)) + tuple(
        date(y, m, d) for y in C.YEARS for m in range(1, 13) if (y, m) >= (2002, 8)
        for d in (1, 2, 3, 4, 5, 6, 7, 8)
    )


class ScheduleAndMarks(unittest.TestCase):
    def test_july_partial_and_fixed_tail(self):
        days = fixture_days()
        spans = C.windows(days, 3)
        self.assertEqual(len(spans), 161)
        self.assertEqual(spans[0], (date(2002, 8, 5), date(2002, 8, 8),
                                    tuple(date(2002, 8, d) for d in (6, 7, 8))))
        following = C.next_three(days)
        self.assertEqual(len(following), 160)
        self.assertEqual(following[0][0:2], (date(2002, 8, 8), date(2002, 9, 3)))
        self.assertEqual(following[-1][0:2], (date(2015, 11, 8), date(2015, 12, 3)))

    def test_later_half_and_common_pricing(self):
        days = fixture_days()
        prices = {}
        held_days = {d for _, _, held in C.windows(days, 3) for d in held}
        for i, d in enumerate(days):
            factor = (1 + (i % 4 + 1) / 1000) if d.year < 2009 else 0.999
            c = prices[days[i-1]].c * factor if i and d in held_days else 100.0
            prices[d] = C.engine.Bar(c, c, c, c, 1)
        pay = {date(2002, 8, 5): 10.0, date(2002, 8, 8): 0.02}
        actual, shown = C.scored(days, prices, pay, True)
        returns = C.engine.window_values(prices, pay, C.windows(days, 3), 2)
        expected = C.engine.pack([v for _, v in returns])
        self.assertEqual({k: actual[k] for k in expected}, expected)
        self.assertEqual(actual["later_half_mean"],
                         C.engine.mean([v for d, v in returns if d >= date(2009, 1, 1)]))
        self.assertFalse(actual["gates"]["later_half_positive"])
        self.assertEqual(len(actual["gates"]), 9)
        self.assertEqual(len(actual["daily_comparison_by_year"]), 14)
        self.assertEqual(len(actual["leave_one_year_out"]), 14)
        self.assertEqual(actual["daily_comparison"]["inside_n"], 483)
        self.assertEqual(actual["daily_comparison"]["outside_n"], len(days) - 484)
        self.assertEqual(shown["next_month_first_three_at_2bps"]["n"], 160)
        self.assertNotIn("gates", C.scored(days, prices, pay, False)[0])


class Inputs(unittest.TestCase):
    def source(self, pins="b" * 64, normalizer="c" * 64):
        return dict(name="fixture", route="example_route", terms_url="https://example.org/terms",
                    terms_note="fixture only", upstream_adjustment="none", adjustment="raw",
                    status="lead_selected", export_manifest_sha256=pins, export_adjust_flag="fixture raw",
                    normalizer_sha256=normalizer)

    def test_pending_vendor_or_non_raw_source_refused(self):
        source = self.source()
        self.assertEqual(S.source_contract(source), source)
        for update in (dict(status="pending"), dict(adjustment="split"), dict(terms_url="")):
            with self.assertRaisesRegex(C.Refused, "P26_SOURCE"):
                S.source_contract(source | update)

    def test_overlap_inclusive_threshold_and_cent(self):
        ref = {C.FIRST + timedelta(days=i): Decimal("100") for i in range(200)}
        bars = {d: Decimal("100.01") for d in ref}
        bars[max(bars)] = Decimal("100.011")
        self.assertEqual(C.compare_closes(bars, ref), (199, 200))
        bars[min(bars)] = Decimal("99.989")
        with self.assertRaisesRegex(C.Refused, "P26_OVERLAP_AGREEMENT"):
            C.compare_closes(bars, ref)
        bars.pop(min(bars))
        with self.assertRaisesRegex(C.Refused, "P26_OVERLAP_CLOCK"):
            C.compare_closes(bars, ref)

    def test_overlap_cannot_round_just_over_one_cent_into_agreement(self):
        self.assertEqual(C.compare_closes({C.FIRST: Decimal("1.01")}, {C.FIRST: Decimal("1")}), (1, 1))
        with self.assertRaisesRegex(C.Refused, "P26_OVERLAP_AGREEMENT"):
            C.compare_closes({C.FIRST: Decimal("1.0100000000000000000000000000000001")}, {C.FIRST: Decimal("1")})

    def test_vendor_rejects_duplicate_clock_nonpositive_close_and_alternate_close(self):
        d = date(2012, 10, 31)
        a = dict(date=d.isoformat(), open="100", high="102", low="98", close="101", volume="9000")
        b = a | {"date": "2012-11-01"}
        days = (d, date(2012, 11, 1))
        self.assertEqual(C.vendor_bars([a, b], days)[1][d], Decimal("101"))
        for rows, code in (
            ([a], "P26_BAR_CLOCK"),
            ([a, a], "P26_BAR_CLOCK"),
            ([a, b | {"close": "0"}], "P26_BAR_NUMBER"),
            ([a, b | {"close": 101}], "P26_CLOSE_TEXT"),
            ([a, b | {"adjclose": "101.1"}], "P26_BAR_SCHEMA"),
        ):
            with self.subTest(code=code), self.assertRaisesRegex(C.Refused, code):
                C.vendor_bars(rows, days)

    def test_bad_exdate_and_duplicates(self):
        days = tuple(C.FIRST + timedelta(days=i) for i in range(161))

        def cash():
            return [dict(id=str(i), ex_date=d.isoformat(), amount=0.01) for i, d in enumerate(days)]

        raw = {"schema": 1, "coverage_start": str(C.FIRST), "coverage_end": str(C.LAST),
               "funds": {s: dict(source="https://www.ishares.com/", splits=[], cash=cash()) for s in C.SYMBOLS}}
        self.assertEqual(len(C.cash_actions(raw, days)["TLT"]), 161)
        raw["funds"]["IEF"]["cash"][0]["ex_date"] = "2002-01-01"
        with self.assertRaisesRegex(C.Refused, "P26_ACTIONS_CLOCK"):
            C.cash_actions(raw, days)
        raw["funds"]["IEF"]["cash"][0]["ex_date"] = days[1].isoformat()
        with self.assertRaisesRegex(C.Refused, "P26_ACTIONS_CLOCK"):
            C.cash_actions(raw, days)

    def test_pin_order_mismatch_duplicate_json_and_permissions(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "fixture"
            for bad in (None, "", "E" * 64, "f" * 63 + "\n"):
                with self.subTest(bad=bad), self.assertRaisesRegex(C.Refused, "P26_PIN"):
                    S.pinned(p, bad)
            p.write_bytes(b"{}")
            p.chmod(0o600)
            self.assertEqual(S.pinned(p, S.digest(b"{}"), True), b"{}")
            with self.assertRaisesRegex(C.Refused, "P26_PIN"):
                S.pinned(p, "1" * 64)
            p.chmod(0o644)
            with self.assertRaisesRegex(C.Refused, "P26_INPUT_PRIVATE"):
                S.pinned(p, S.digest(b"{}"), True)
            s = Path(tmp) / "symlink"
            s.symlink_to(p)
            with self.assertRaises(OSError):
                S.pinned(s, S.digest(b"{}"))
        with self.assertRaisesRegex(C.Refused, "P26_JSON_DUPLICATE_KEY"):
            S.parse(b'{"a": 1, "a": 2}')

    def test_no_p26_variable(self):
        with patch.dict(os.environ, {"P26_NO_OVERRIDE": ""}):
            with self.assertRaisesRegex(C.Refused, "P26_ENVIRONMENT"):
                S.authorize("1" * 40, "2" * 64)

    def test_lock_order_failure_and_no_retry(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock = root / "score_26.lock"

            def refused():
                self.assertFalse(lock.exists())
                raise C.Refused("P26_FIXTURE")

            def good():
                self.assertFalse(lock.exists())
                return 7

            def crash(marker):
                self.assertEqual(marker, 7)
                self.assertTrue(lock.is_file())
                raise ArithmeticError

            not_called = lambda *_: self.fail("unexpected call")
            with self.assertRaisesRegex(C.Refused, "P26_FIXTURE"):
                S.once(root, {}, refused, not_called)
            self.assertFalse(lock.exists())
            with self.assertRaises(ArithmeticError):
                S.once(root, {}, good, crash)
            self.assertTrue(lock.exists())
            self.assertFalse((root / "results_26.json").exists())
            with self.assertRaisesRegex(C.Refused, "P26_CONSUMED"):
                S.once(root, {}, not_called, not_called)

    def test_prepare_full_calendars_with_invented_prices_then_refuses_mixed_inputs(self):
        verified = {n: (S.HERE / n).read_bytes() for n in ("calendar_25.json", "calendar_26.json")}
        days = C.calendar(S.parse(verified["calendar_26.json"]))
        days25 = C.engine.check_calendar(S.parse(verified["calendar_25.json"]))
        overlap = tuple(d for d in days25 if d <= C.OVERLAP_LAST)
        def save(folder, name, data):
            blob = S.encode(data)
            p = folder / name
            p.write_bytes(blob)
            p.chmod(0o600)
            return S.digest(blob)

        calendar_prices = {d: 100 + i % 3 for i, d in enumerate(days + days25)}

        def vendor(sessions):
            return [dict(date=str(d), open=calendar_prices[d], high=105, low=99,
                         close=str(calendar_prices[d]), volume=200) for d in sessions]

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            inputs, sip, actions_dir = root / "inputs", root / "sip", root / "actions"
            inputs.mkdir(mode=0o700)
            natives = inputs / "native"
            natives.mkdir(mode=0o700)
            sip.mkdir(mode=0o700)
            actions_dir.mkdir(mode=0o700)
            normalizer = save(inputs, S.NORMALIZER, "synthetic fixture, not executed")
            actions = {"schema": 1, "coverage_start": str(C.FIRST), "coverage_end": str(C.LAST),
                       "funds": {s: dict(source="https://www.ishares.com/", splits=[],
                                         cash=[dict(id=str(d), ex_date=str(d), amount=0.01) for d in days[2:163]])
                                 for s in C.SYMBOLS}}
            action_pin = save(actions_dir, "cash_actions.json", actions)
            action_path = actions_dir / "cash_actions.json"
            m = {"schema": 1, "route": "example_route", "adjust_flag": "fixture raw", "terms_note": "fixture only",
                 "pull_cap_note": "fixture at fixed split", "funds": {}}
            a_days = days + tuple(d for d in overlap if d <= C.PULL_A_LAST)
            b_days = tuple(d for d in overlap if d >= C.PULL_B_FIRST)
            refs = {}
            for s in C.SYMBOLS:
                m["funds"][s] = {}
                for part, sessions in (("a", a_days), ("b", b_days)):
                    name = f"{s}_{part}.json"
                    vendor_pin = save(inputs, name, vendor(sessions))
                    native_name = f"{s}_{part}_native.csv"
                    native_pin = save(natives, native_name, f"synthetic native {part} {s}")
                    m["funds"][s][part] = dict(file=name, sha256=vendor_pin, source_sha256=native_pin,
                                               source_file=f"native/{native_name}",
                                               pulled_utc="2026-11-26T04:00:00Z", row_count=len(sessions),
                                               first=str(sessions[0]), last=str(sessions[-1]),
                                               normalization=dict(script=S.NORMALIZER, script_sha256=normalizer,
                                                                  recipe="synthetic fixture"))
                refs[s + ".json"] = save(sip, s + ".json", [
                    dict(t=datetime.combine(d, time(), C.engine.NY).isoformat(), c=calendar_prices[d])
                    for d in days25])
            m_pin = save(inputs, "manifest.json", m)
            verified["source_26.json"] = S.encode(self.source(m_pin, normalizer))
            sip_pin = save(sip, "manifest.json",
                           dict(feed="sip", adjustment="raw", draft_sha256=C.SIP_DRAFT_SHA, files=refs))
            with patch.object(C, "ACTIONS_SHA", action_pin), patch.object(C, "SIP_MANIFEST_SHA", sip_pin), \
                 patch.object(C, "scored", side_effect=AssertionError("prepare scored")):
                data = S.prepare(root, m_pin, verified, inputs, action_path, sip)
                self.assertEqual(data[0], days)
                self.assertEqual(data[3], {s: {"a": (1259, 1259), "b": (1486, 1486), "all": (2723, 2723)}
                                           for s in C.SYMBOLS})
                self.assertFalse((root / "score_26.lock").exists())
                self.assertFalse((root / "results_26.json").exists())
                native = "IEF_b_native.csv"
                save(natives, native, "edited synthetic native")
                with self.assertRaisesRegex(C.Refused, "P26_PIN"):
                    S.prepare(root, m_pin, verified, inputs, action_path, sip)
                save(natives, native, "synthetic native b IEF")
                for part, mode, code in (
                    ("b", "duplicate", "P26_JOIN_CLOSE"),
                    ("a", "segment", "P26_OVERLAP_AGREEMENT"),
                    ("b", "segment", "P26_OVERLAP_AGREEMENT"),
                ):
                    with self.subTest(part=part, mode=mode):
                        sessions = a_days if part == "a" else b_days
                        rows = vendor(sessions)
                        name = f"IEF_{part}.json"
                        previous = m["funds"]["IEF"][part]["sha256"]
                        if mode == "duplicate":
                            rows[0]["close"] += ".0"  # Same numeric close, different provider text.
                        else:
                            start, end = (3381, 3388) if part == "a" else (22, 30)
                            for row in rows[start:end]:
                                row["close"] = str(int(row["close"]) + 1)
                        m["funds"]["IEF"][part]["sha256"] = save(inputs, name, rows)
                        new_pin = save(inputs, "manifest.json", m)
                        verified["source_26.json"] = S.encode(self.source(m_pin, normalizer))
                        with self.assertRaisesRegex(C.Refused, "P26_EXPORT_PIN"):
                            S.prepare(root, new_pin, verified, inputs, action_path, sip)
                        verified["source_26.json"] = S.encode(self.source(new_pin, normalizer))
                        with self.assertRaisesRegex(C.Refused, code):
                            S.prepare(root, new_pin, verified, inputs, action_path, sip)
                        self.assertEqual(save(inputs, name, vendor(sessions)), previous)
                        m["funds"]["IEF"][part]["sha256"] = previous


if __name__ == "__main__":
    unittest.main()
