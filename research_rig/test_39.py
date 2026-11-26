"""Plan 39 tests: official date metadata and invented inputs only."""
from collections import Counter
from datetime import datetime, time
from hashlib import sha256
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from unittest import TestCase, main, mock

import common_39 as C
import score_39 as S

HERE = Path(__file__).resolve().parent
CALENDAR = (HERE / "calendar_39.json").read_bytes()
DAYS, EVENTS = C.calendar(S.parse(CALENDAR))


def invented(event_changes):
    tape, cash = {DAYS[0]: 100.0}, {}
    for i, (buy, sell) in enumerate(zip(DAYS[:-1], DAYS[1:], strict=True)):
        change = event_changes(sell, i) if sell in EVENTS else 0.0001 * ((i % 5) - 2)
        cash[sell] = 0.05 if i % 29 == 0 else 0
        tape[sell] = tape[buy] * (1 + change) - cash[sell]
    return tape, cash


def put(path, value):
    blob = S.encode(value)
    path.write_bytes(blob)
    path.chmod(0o600)
    return sha256(blob).hexdigest()


def fixture(directory):
    rows = []
    for i, d in enumerate(DAYS):
        close = 100 + i / 10
        rows.append({"t": datetime.combine(d, time(), C.NY).isoformat(),
                     "o": close, "h": close + 1, "l": close - 1, "c": close, "v": 10})
    actions = {"schema": 1, "coverage_start": str(C.FIRST), "coverage_end": str(C.LAST),
               "funds": {s: {"source": "https://fixture.invalid/", "splits": [],
                             "cash": [{"id": "invented", "ex_date": str(DAYS[1]), "amount": 0.5}]}
                         for s in C.SYMBOLS}}
    pins = {s + ".json": put(directory / (s + ".json"), rows) for s in C.SYMBOLS}
    action_pin = pins["cash_actions.json"] = put(directory / "cash_actions.json", actions)
    manifest = {"schema": 1, "mode": "raw_dated_distributions", "adjustment": "raw", "feed": "sip",
                "start": str(C.FIRST), "end": str(C.LAST), "collected_utc": "2026-11-26T00:00:00Z", "files": pins}
    return put(directory / "manifest.json", manifest), action_pin, manifest


class Calendar(TestCase):
    def test_pinned_grid_and_splits(self):
        self.assertEqual(len(DAYS), 2723)
        self.assertEqual(len(EVENTS), 102)
        self.assertEqual(sum(s >= C.POST for s in EVENTS), 65)
        self.assertEqual(sum(row[3] for row in EVENTS.values()), 11)
        self.assertEqual([Counter(d.year for d in EVENTS)[y] for y in C.YEARS],
                         [9, 9, 10, 9, 9, 8, 10, 10, 10, 11, 7])
        ref = HERE / "calendar_25.json"
        if ref.exists():
            self.assertEqual(list(map(str, DAYS)), [s for s in S.parse(ref.read_bytes())["sessions"]
                                                    if s <= str(C.LAST)])

    def test_actual_special_early_and_observed(self):
        cases = (("2018-12-04", "2018-12-03", "2018-12-05", False),
                 ("2025-01-08", "2025-01-07", "2025-01-09", False),
                 ("2025-07-03", "2025-07-02", "2025-07-04", True),
                 ("2022-12-30", "2022-12-29", "2023-01-02", False),
                 ("2025-12-31", "2025-12-30", "2026-01-01", False),
                 ("2026-07-02", "2026-07-01", "2026-07-03", False))
        for sell, buy, holiday, early in cases:
            b, h, _, e = EVENTS[C.exact_day(sell)]
            self.assertEqual((str(b), str(h), e), (buy, holiday, early))
        self.assertNotIn(C.exact_day("2021-12-31"), EVENTS)
        self.assertIn(C.exact_day("2021-12-31"), DAYS)
        self.assertNotIn(C.exact_day("2016-01-04"), EVENTS)


class Arithmetic(TestCase):
    def test_formula(self):
        self.assertAlmostEqual(C.one_return(100, 101, 0.75, 2),
                               (101 * 0.9998 + 0.75) / 100.02 - 1)
        self.assertIsNone(C.sample_t([0.02] * 5))
        self.assertIsNone(C.comparison([.04] * 5, [.03] * 4)["welch_t"])
        self.assertAlmostEqual(C.comparison([2, 3, 4], [0, 1, 2])["welch_t"], (6 ** .5))

    def test_planted_signal_and_control(self):
        tape, cash = invented(lambda _, i: 0.002 + 0.0001 * (i % 7))
        spy, spycash = invented(lambda _, i: -.001 - .0001 * (i % 7))
        result = C.evaluate(DAYS, EVENTS, {"IWM": tape, "SPY": spy}, {"IWM": cash, "SPY": spycash})
        p = result["IWM_judged_2_bps_per_side"]
        self.assertTrue(p["passes"])
        self.assertEqual(len(p["gates"]), 7)
        self.assertEqual(p["post_2019"]["n"], 65)
        self.assertEqual(p["daily_comparison_gross"]["outside"]["n"], 2620)
        self.assertLess(result["SPY_same_events_shown_only_2_bps_per_side"]["mean"], 0)
        self.assertLess(result["IWM_cost_sensitivity_shown_only"][10]["mean"],
                        result["IWM_cost_sensitivity_shown_only"][5]["mean"])

    def test_post_and_breadth_fail(self):
        tape, cash = invented(lambda d, i: (0.004 if d < C.POST else -0.001) + 0.0001 * (i % 5))
        p = C.evaluate(DAYS, EVENTS, dict.fromkeys(C.SYMBOLS, tape),
                       dict.fromkeys(C.SYMBOLS, cash))["IWM_judged_2_bps_per_side"]
        self.assertTrue(p["gates"]["net_mean"])
        self.assertFalse(p["gates"]["post_2019_net_mean"])
        self.assertFalse(p["gates"]["positive_year_breadth"])
        self.assertFalse(p["passes"])


class InputsAndClaim(TestCase):
    def test_git_approval_seal_with_invented_repo(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            rig = root / "research_rig"
            rig.mkdir()
            docs = root / "docs"
            docs.mkdir()

            def git(*args):
                return subprocess.check_output(["/usr/bin/git", "-C", temp, *args],
                                               stderr=subprocess.DEVNULL).decode().strip()

            git("init", "-q")
            git("config", "user.name", "Invented")
            git("config", "user.email", "invented@example.invalid")
            for name in S.PIN_NAMES:
                (rig / name).write_bytes((HERE / name).read_bytes())
            freeze_pin = put(rig / S.PINS, {name: sha256((rig / name).read_bytes()).hexdigest()
                                           for name in S.PIN_NAMES})
            label = f' | {chr(96)}research_rig/{S.PLAN}{chr(96)} | fixture |\n'
            (rig / "TRIAL_LEDGER.md").write_text("| 174 | frozen" + label)
            (docs / "QUEUE.md").write_text("| 65 | frozen" + label)
            git("add", ".")
            git("commit", "-qm", "invented freeze")
            freeze = git("rev-parse", "HEAD")
            input_pin, actions_pin = "1" * 64, "2" * 64
            approval_file = rig / S.APPROVAL
            approval_file.write_text(f"Approved by the lead: plan 39, validation and one scored run, "
                                     f"freeze commit {freeze}, freeze SHA-256 {freeze_pin}, input SHA-256 "
                                     f"{input_pin}, cash actions SHA-256 {actions_pin}.\n")
            git("add", ".")
            git("commit", "-qm", "invented approval")
            approval = git("rev-parse", "HEAD")
            with mock.patch.object(S, "HERE", rig), mock.patch.object(S, "REPO", root):
                bound, blobs = S.authorize(approval, freeze_pin, input_pin, actions_pin)
                self.assertEqual(bound, freeze)
                self.assertEqual(set(blobs), S.PIN_NAMES)
                with self.assertRaisesRegex(S.Refused, "APPROVAL"):
                    S.authorize(approval, freeze_pin, "3" * 64, actions_pin)
                (docs / "QUEUE.md").write_text("dirty")
                with self.assertRaisesRegex(S.Refused, "APPROVAL"):
                    S.authorize(approval, freeze_pin, input_pin, actions_pin)

    def test_validation_and_modified_input(self):
        with TemporaryDirectory() as temp:
            path = Path(temp)
            pin, actions, _ = fixture(path)
            with mock.patch.object(C, "one_return", side_effect=AssertionError("return attempted")):
                days, events, _, _ = S.load_inputs(path, pin, actions, C, CALENDAR)
            self.assertEqual((days, events), (DAYS, EVENTS))
            self.assertEqual(len(list(path.iterdir())), 4)
            with self.assertRaisesRegex(S.Refused, "MANIFEST_FILES"):
                S.load_inputs(path, pin, "0" * 64, C, CALENDAR)
            with (path / "IWM.json").open("ab") as f:
                f.write(b" ")
            with self.assertRaisesRegex(S.Refused, "PIN"):
                S.load_inputs(path, pin, actions, C, CALENDAR)

    def test_malformed_and_unprivate(self):
        with self.assertRaisesRegex(S.Refused, "JSON_DUPLICATE"):
            S.parse(b'{"a":1,"a":1}')
        with self.assertRaisesRegex(S.Refused, "JSON_NUMBER"):
            S.parse(b'{"a":NaN}')
        with TemporaryDirectory() as temp:
            path = Path(temp)
            pin, actions, m = fixture(path)
            (path / "SPY.json").chmod(0o644)
            with self.assertRaisesRegex(S.Refused, "PRIVATE"):
                S.load_inputs(path, pin, actions, C, CALENDAR)
            (path / "SPY.json").chmod(0o600)
            m["adjustment"] = "all"
            with self.assertRaisesRegex(S.Refused, "MANIFEST"):
                S.load_inputs(path, put(path / "manifest.json", m), actions, C, CALENDAR)

    def test_lock_before_evaluation_and_never_retry(self):
        with TemporaryDirectory() as temp:
            path = Path(temp)
            calls = []

            def calculate():
                self.assertTrue((path / "score_39.lock").exists())
                calls.append(1)
                return {"invented": 7}

            S.once(path, {"trial": 174}, (), calculate)
            self.assertEqual(S.parse((path / "results_39.json").read_bytes())["invented"], 7)
            with self.assertRaisesRegex(S.Refused, "CONSUMED"):
                S.once(path, {}, (), calculate)
            self.assertEqual(calls, [1])

    def test_failure_still_consumes_claim(self):
        with TemporaryDirectory() as temp:
            path = Path(temp)
            evaluate = mock.Mock(side_effect=ArithmeticError)
            with self.assertRaises(ArithmeticError):
                S.once(path, {}, (), evaluate)
            self.assertFalse((path / "results_39.json").exists())
            with self.assertRaisesRegex(S.Refused, "CONSUMED"):
                S.once(path, {}, (), evaluate)
            evaluate.assert_called_once()

    def test_environment_refusal_precedes_approval(self):
        fake = ["score_39.py", "--validate-inputs", "--approval-commit", "0" * 40,
                "--freeze-sha256", "0" * 64, "--input-sha256", "0" * 64, "--actions-sha256", "0" * 64]
        old = os.umask(0o077)
        try:
            with mock.patch.object(S.sys, "argv", fake), mock.patch.object(S.sys, "flags", mock.Mock(isolated=1, optimize=0)), \
                 mock.patch.object(S.sys, "dont_write_bytecode", True), \
                 mock.patch.dict(os.environ, {"P39_ROOT": "/wrong"}, clear=True), \
                 mock.patch.object(S, "authorize") as authorization, \
                 mock.patch.object(S.Parser, "exit", side_effect=SystemExit) as refusal:
                with self.assertRaises(SystemExit):
                    S.main()
                authorization.assert_not_called()
                refusal.assert_called_once_with(2, "P39_ENVIRONMENT\n")
        finally:
            os.umask(old)


if __name__ == "__main__":
    main()
