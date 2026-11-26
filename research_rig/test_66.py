"""Plan 66 tests: calendar metadata and invented inputs only. No market data."""
from datetime import date
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main, mock

import common_66 as C
import score_66 as S

HERE = Path(__file__).resolve().parent
EVENTS = C.calendar(json.loads((HERE / "calendar_66.json").read_text()))


def put(path, value):
    blob = S.encode(value)
    path.write_bytes(blob)
    path.chmod(0o600)
    return sha256(blob).hexdigest()


def invented_actions(cash=None, unverified=(), splits=()):
    funds = {c: {"source": "https://fixture.invalid/", "cash": [], "unverified_cash": [], "splits": []}
             for c in (C.SPY_CUSIP, C.SPLG_CUSIP, *C.SH_CUSIPS)}
    for i, (cusip, d, amt) in enumerate(cash or []):
        funds[cusip]["cash"].append({"id": f"inv{i}", "ex_date": d, "amount": amt})
    for cusip, d in unverified:
        funds[cusip]["unverified_cash"].append(d)
    for cusip, d in splits:
        funds[cusip]["splits"].append(d)
    return {"schema": 1, "funds": funds}


def invented_marks(fund_move=0.002, sh_move=0.002, skip=()):
    rows = []
    for e in sorted(EVENTS):
        if e in skip:
            continue
        sh = C.SH_CUSIPS[0] if e < date(2024, 11, 7) else C.SH_CUSIPS[1]
        rows.append({"expiration": e.isoformat(), "fund_cusip": C.leg1_cusip(e), "sh_cusip": sh,
                     "fund_entry_close": 100.0, "fund_open": 100.0 * (1 + fund_move),
                     "sh_open": 40.0, "sh_close": 40.0 * (1 + sh_move)})
    return {"schema": 1, "open_rule": C.OPEN_RULE, "rows": rows}


class Calendar(TestCase):
    def test_counts_and_shifts(self):
        self.assertEqual(len(EVENTS), 131)
        self.assertEqual(sum(e >= C.POST for e in EVENTS), 38)
        self.assertEqual({e for e in EVENTS if e.weekday() != 4}, C.SHIFTED)
        self.assertEqual(EVENTS[date(2026, 6, 18)], date(2026, 6, 17))
        self.assertEqual(EVENTS[date(2016, 1, 15)], date(2016, 1, 14))

    def test_rule_dates_match_pinned(self):
        self.assertEqual(C.synthetic_dates(), sorted(EVENTS))

    def test_sessions_exist_in_xnys_snapshot(self):
        sessions = set(json.loads((HERE / "calendar_25.json").read_text())["sessions"])
        for e, entry in EVENTS.items():
            self.assertIn(e.isoformat(), sessions)
            self.assertIn(entry.isoformat(), sessions)

    def test_refuses_edited_calendar(self):
        raw = json.loads((HERE / "calendar_66.json").read_text())
        raw["expirations"].pop()
        with self.assertRaises(C.Refused):
            C.calendar(raw)


class Legs(TestCase):
    def test_two_bp_floor(self):
        # 5 shares at $100: 2 bp of $500 = $0.10 per side beats 5 cents.
        self.assertAlmostEqual(C.leg(100.0, 101.0), (5 * 1.0 - 0.10 - 0.101) / 500)

    def test_cent_rule_binds_on_cheap_shares(self):
        # 50 shares at $10: 2 bp = $0.10, one cent a share = $0.50 per side.
        self.assertAlmostEqual(C.leg(10.0, 10.0), -1.0 / 500)

    def test_zero_shares(self):
        self.assertIsNone(C.leg(600.0, 601.0))

    def test_cash_credit(self):
        self.assertGreater(C.leg(100.0, 99.0, 1.0), C.leg(100.0, 99.0))


class Placement(TestCase):
    def test_all_placed_and_refusals(self):
        e0, e1 = date(2016, 3, 18), date(2018, 6, 15)
        acts = C.actions_packet(invented_actions(unverified=[(C.SPY_CUSIP, e1.isoformat())],
                                                 splits=[(C.SH_CUSIPS[0], e0.isoformat())]))
        marks = C.marks_packet(invented_marks(skip={date(2020, 2, 21)}), EVENTS)
        placed = C.place(EVENTS, marks, acts)
        self.assertEqual(placed[e0], ("REFUSED", "SPLIT_ON_EVENT"))
        self.assertEqual(placed[e1], ("REFUSED", "CASH_UNVERIFIED"))
        self.assertEqual(placed[date(2020, 2, 21)], ("REFUSED", "NO_MARKS"))
        self.assertEqual(sum(v[0] == "PLACED" for v in placed.values()), 128)

    def test_wrong_fund_refused(self):
        raw = invented_marks()
        raw["rows"][0]["fund_cusip"] = C.SPLG_CUSIP  # SPLG before it tracked the S&P 500
        placed = C.place(EVENTS, C.marks_packet(raw, EVENTS), C.actions_packet(invented_actions()))
        self.assertEqual(placed[date(2016, 1, 15)], ("REFUSED", "FUND_ID"))

    def test_dividend_on_expiration_is_credited(self):
        e = date(2017, 3, 17)
        with_cash = C.actions_packet(invented_actions(cash=[(C.SPY_CUSIP, e.isoformat(), 1.0)]))
        marks = C.marks_packet(invented_marks(), EVENTS)
        a = C.place(EVENTS, marks, with_cash)[e][1]
        b = C.place(EVENTS, marks, C.actions_packet(invented_actions()))[e][1]
        self.assertAlmostEqual(a - b, 0.01)

    def test_pass_and_fail(self):
        acts = C.actions_packet(invented_actions())
        up = C.evaluate(EVENTS, C.marks_packet(invented_marks(0.004, 0.004), EVENTS), acts)
        self.assertEqual(up["judged_net_per_expiration"]["n"], 131)
        self.assertFalse(up["judged_net_per_expiration"]["gates"]["t_at_least_2"])  # zero variance fails t
        down = C.evaluate(EVENTS, C.marks_packet(invented_marks(-0.004, 0.0), EVENTS), acts)
        self.assertFalse(down["judged_net_per_expiration"]["passes"])

    def test_marks_with_noise(self):
        dated = {e: 0.003 + (0.001 if i % 2 else -0.001) for i, e in enumerate(sorted(EVENTS))}
        gates, detail = C.marks(dated)
        self.assertTrue(all(gates.values()))
        self.assertEqual(detail["positive_years"], 11)


class Power(TestCase):
    def test_zero_edge_rarely_passes_and_big_edge_does(self):
        self.assertLess(C.synthetic_power(0, 104.6, sims=1000, seed=1)["power"], 0.03)
        self.assertGreater(C.synthetic_power(80, 104.6, sims=1000, seed=1)["power"], 0.95)


class Runner(TestCase):
    def test_validate_refuses_without_private_inputs(self):
        with TemporaryDirectory() as tmp, mock.patch.object(S, "INPUTS", Path(tmp) / "missing"):
            with self.assertRaises(Exception):
                S.load_inputs(S.INPUTS, "0" * 64, C, (HERE / "calendar_66.json").read_bytes())

    def test_private_packet_round_trip(self):
        with TemporaryDirectory() as tmp:
            d = Path(tmp) / "in"
            d.mkdir(mode=0o700)
            pins = {"marks.json": put(d / "marks.json", invented_marks()),
                    "actions.json": put(d / "actions.json", invented_actions())}
            m = {"schema": 1, "mode": "plan66_marks", "feed": "sip", "adjustment": "raw",
                 "open_rule": C.OPEN_RULE, "collected_utc": "2026-11-27T00:00:00Z", "files": pins}
            pin = put(d / "manifest.json", m)
            events, marks, acts = S.load_inputs(d, pin, C, (HERE / "calendar_66.json").read_bytes())
            self.assertEqual(len(marks), 131)
            with self.assertRaises(S.Refused):
                S.load_inputs(d, "f" * 64, C, (HERE / "calendar_66.json").read_bytes())

    def test_go_refuses_without_approval(self):
        with self.assertRaises(S.Refused):
            S.authorize("0" * 40, "0" * 64, "0" * 64)


if __name__ == "__main__":
    main()
