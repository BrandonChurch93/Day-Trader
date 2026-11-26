"""Synthetic-only Plan 41 tests; never touch the private input or run directories."""
from contextlib import redirect_stdout
from datetime import date, datetime, time, timedelta
from fractions import Fraction
from hashlib import sha256
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import common_41 as C
import score_41 as S

HERE = Path(__file__).resolve().parent
DRAFT = HERE / "thresholds_41.yaml"
CONFIG = DRAFT if DRAFT.exists() else HERE.parent / S.CONFIG
CALENDAR = (HERE.parents[1] / "dt-work" / S.CALENDAR) if DRAFT.exists() else HERE / "calendar_25.json"
CFG = S.read_config(CONFIG.read_bytes())
CAL = CALENDAR.read_bytes()


def digest(blob):
    return sha256(blob).hexdigest()


def packet(root):
    days, _ = C.calendar(S.parse(CAL), CFG)
    root.mkdir(mode=0o700)
    splits_clear = {"source": "https://example.test/issuer", "splits": [],
                    "cash": [{"id": "fabricated", "ex_date": str(days[2]), "amount": 1}]}
    actions = {"schema": 1, "coverage_start": str(days[0]), "coverage_end": str(days[-1]),
               "funds": {s: splits_clear for s in C.SYMBOLS}}
    rows = []
    for i, d in enumerate(days):
        ts = C.NY.utcoffset(datetime.combine(d, time()))
        px = 100 + i % 3
        rows.append({"t": f"{d}T{-(ts // timedelta(hours=1)):02}:00:00Z",
                     "o": px, "h": px, "l": px, "c": px, "v": 10})
    payloads = {s + ".json": S.encode(rows) for s in C.SYMBOLS} | {"cash_actions.json": S.encode(actions)}
    pins = {}
    for name, blob in payloads.items():
        (root / name).write_bytes(blob)
        (root / name).chmod(0o600)
        pins[name] = digest(blob)
    m = S.encode({"schema": 1, "mode": "raw_dated_distributions", "feed": "sip", "adjustment": "raw",
                  "start": str(days[0]), "end": str(days[-1]), "collected_utc": "2026-11-26T00:00:00Z",
                  "files": pins})
    (root / "manifest.json").write_bytes(m)
    (root / "manifest.json").chmod(0o600)
    return digest(m), pins["cash_actions.json"]


class TestPlan41(unittest.TestCase):
    def test_calendar(self):
        days, windows = C.calendar(S.parse(CAL), CFG)
        self.assertEqual((len(days), len(windows)), (2723, 130))
        self.assertEqual(tuple(map(str, windows[0])), ("2016-01-04", "2016-01-25", "2016-01-26",
                                                      "2016-01-29", "2016-02-01"))
        self.assertEqual(windows[1][0], windows[0][3])
        self.assertEqual((str(windows[-1][3]), windows[-1][4]), ("2026-10-30", None))
        self.assertEqual(sum(row[-1] is not None for row in windows), 129)

    def test_signal_causal_and_ex_date_boundaries(self):
        days = tuple(date(2016, 1, i) for i in range(4, 9))
        tapes = {s: dict(zip(days, map(Fraction, (100, 100, 100, 100, 100)))) for s in C.SYMBOLS}
        cash = {"TLT": {days[1]: Fraction(1)}, "SPY": {days[0]: Fraction(50), days[3]: Fraction(100)}}
        tapes["SPY"][days[4]] = Fraction(9999)
        self.assertEqual(C.signal_side(days, tapes, cash, days[0], days[2]), ("SPY", "TLT"))
        cash["TLT"].clear()
        self.assertEqual(C.signal_side(days, tapes, cash, days[0], days[2]), ("CASH", "CASH"))

    def test_decimal_inequality_and_exact_zero(self):
        d1, d2 = date(2016, 1, 4), date(2016, 1, 5)
        p, q = S.parse(b"[100.0,100.000000000000001]")
        self.assertTrue(C.positive_number(p) and C.positive_number(q))
        self.assertGreater(C.exact(q), C.exact(p))
        tapes = {"SPY": {d1: C.exact(p), d2: C.exact(q)},
                 "TLT": {d1: C.exact(p), d2: C.exact(p)}}
        self.assertEqual(C.signal_side((d1, d2), tapes, {"SPY": {}, "TLT": {}}, d1, d2), ("TLT", "SPY"))
        values = [C.exact(v) for v in S.parse(b"[0.1,0.2,-0.3]")]
        self.assertEqual(C.summary(values)["mean"], 0.0)
        rows = [{"exit": d1, "difference": v, "conditional": v, "laggard_minus_winner": v} for v in values]
        self.assertFalse(C.assess(rows, CFG)["marks"]["positive_mean"])

    def test_shares_cost_cash_and_distribution(self):
        d1, d2 = date(2016, 1, 4), date(2016, 1, 5)
        net, n = C.side_return({d1: Fraction(100), d2: Fraction(102)},
                               {d1: Fraction(9), d2: Fraction(1)}, d1, d2, 2, Fraction(500))
        self.assertEqual(n, 4)
        self.assertEqual(net, 4 * (102 * Fraction(4999, 5000) + 1 - 100 * Fraction(5001, 5000)) / 500)
        self.assertEqual(C.side_return({d1: Fraction(500), d2: Fraction(510)}, {}, d1, d2, 2, Fraction(500)), (0, 0))

    def test_every_month_comparator_and_diagnostics(self):
        days, windows = C.calendar(S.parse(CAL), CFG)
        tapes = {s: {d: 100 for d in days} for s in C.SYMBOLS}
        for i, (_, decision, entry, exit_, _) in enumerate(windows):
            # Both signs and exact ties; reset each anchor's exit closes to 100.
            if i % 3 == 0:
                tapes["SPY"][decision], tapes["TLT"][entry] = 101, 95
            elif i % 3 == 1:
                tapes["TLT"][decision], tapes["SPY"][entry] = 101, 90
        out = C.evaluate(days, windows, tapes, {"SPY": [], "TLT": []}, CFG)
        tlt, spy, tie = out["monthly"][:3]
        self.assertEqual([tlt["selected"], spy["selected"], tie["selected"]], ["TLT", "SPY", "CASH"])
        self.assertEqual(tlt["difference"], 0)
        self.assertGreater(spy["difference"], 0)
        self.assertEqual(tie["conditional"], 0)
        self.assertEqual(tie["laggard_minus_winner"], 0)
        self.assertEqual(out["shown_only"]["first_next_session_winner_minus_laggard"]["n"], 129)
        self.assertEqual(out["judged"]["difference"]["n"], 130)
        self.assertTrue(out["judged"]["passed"])
        self.assertEqual(len(out["judged"]["marks"]), 8)
        self.assertEqual(out["shown_only"]["cost_sensitivity"]["10"]["difference"]["n"], 130)

    def test_undefined_t_and_zero_not_positive(self):
        _, windows = C.calendar(S.parse(CAL), CFG)
        rows = [{"exit": w[3], "difference": 0, "conditional": 0, "laggard_minus_winner": 0} for w in windows]
        out = C.assess(rows, CFG)
        self.assertEqual([k for k, ok in out["marks"].items() if ok], ["minimum_months"])
        self.assertIsNone(out["difference"]["t"])

    def test_synthetic_full_validation_and_bad_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            mpin, apin = packet(root)
            with patch.object(C, "evaluate", side_effect=AssertionError("no evaluation")):
                args = S.load_inputs(root, mpin, apin, C, CAL, CFG)
            self.assertEqual(len(args[1]), 130)
            with self.assertRaisesRegex(S.Refused, "P41_PIN"):
                S.load_inputs(root, mpin.upper(), apin, C, CAL, CFG)
            with self.assertRaisesRegex(S.Refused, "P41_MANIFEST_FILES"):
                S.load_inputs(root, mpin, "0" * 64, C, CAL, CFG)
            (root / "SPY.json").chmod(0o644)
            with self.assertRaisesRegex(S.Refused, "P41_PRIVATE"):
                S.load_inputs(root, mpin, apin, C, CAL, CFG)

    def test_no_return_main_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packet"
            mpin, apin = packet(root)
            argv = ["score_41.py", "--validate-inputs", "--approval-commit", "a" * 40,
                    "--freeze-sha256", "b" * 64, "--input-sha256", mpin, "--actions-sha256", apin]
            blobs = {S.CONFIG: CONFIG.read_bytes(), S.CALENDAR: CAL, S.ENGINE: (HERE / "common_41.py").read_bytes()}
            old_umask = os.umask(0o077)
            try:
                with (patch.object(S, "INPUTS", root), patch.object(S, "resources"),
                      patch.object(S, "authorize", return_value=("c" * 40, blobs)),
                      patch.object(S, "once") as once, patch.object(S, "load_engine", return_value=C),
                      patch.object(C, "evaluate", side_effect=AssertionError("no evaluation")),
                      patch.object(S.sys, "argv", argv), patch.object(S, "check_environment"),
                      redirect_stdout(io.StringIO()) as out):
                    S.main()
                    once.assert_not_called()
                self.assertEqual(out.getvalue(), "P41_INPUTS_OK symbols 2 sessions_per_symbol 2723 planned_months 130 planned_reversals 129\n")
            finally:
                os.umask(old_umask)

    def test_lock_precedes_evaluation_and_failure_consumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_umask = os.umask(0o077)
            try:
                def crash():
                    self.assertTrue((root / "score_41.lock").is_file())
                    self.assertFalse((root / "results_41.json").exists())
                    raise ValueError("invented failure")
                with self.assertRaises(ValueError):
                    S.once(root, {}, [], crash)
                with self.assertRaisesRegex(S.Refused, "P41_CONSUMED_OR_NOT_EMPTY"):
                    S.once(root, {}, [], lambda: self.fail("consumed"))
            finally:
                os.umask(old_umask)

    def test_actual_git_approval_shape_and_corrupted_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def git(*args):
                return subprocess.run(["/usr/bin/git", "-C", str(root), *args], check=True,
                                      capture_output=True, text=True).stdout.strip()

            def put(name, blob):
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(blob)

            git("init", "-q")
            git("config", "user.email", "synthetic@example.test")
            git("config", "user.name", "Synthetic Test")
            pins = {}
            for name in S.PIN_NAMES:
                blob = b"Status FROZEN.\n" if name == S.PLAN else ("invented: " + name + "\n").encode()
                put(name, blob)
                pins[name] = digest(blob)
            manifest = S.encode(pins)
            fp, ip, ap = digest(manifest), "a" * 64, "b" * 64
            put(S.PINS, manifest)
            put("research_rig/TRIAL_LEDGER.md", f"| 176 | `{S.PLAN}` |\n".encode())
            put("docs/QUEUE.md", f"| 54 | `{S.PLAN}` |\n".encode())
            git("add", ".")
            git("commit", "-qm", "synthetic freeze")
            freeze = git("rev-parse", "HEAD")
            body = (f"Approved by the lead: plan 41, validation and one scored run, freeze commit {freeze}, "
                    f"freeze SHA-256 {fp}, input SHA-256 {ip}, cash actions SHA-256 {ap}.\n").encode()
            with patch.object(S, "REPO", root):
                put(S.APPROVAL, body)
                put("extra", b"not permitted\n")
                git("add", ".")
                git("commit", "-qm", "bad synthetic approval")
                with self.assertRaisesRegex(S.Refused, "P41_APPROVAL"):
                    S.authorize(git("rev-parse", "HEAD"), fp, ip, ap)
                git("reset", "--hard", freeze)
                put(S.APPROVAL, body)
                git("add", S.APPROVAL)
                git("commit", "-qm", "clean synthetic approval")
                head = git("rev-parse", "HEAD")
                self.assertEqual(S.authorize(head, fp, ip, ap)[0], freeze)
                with self.assertRaisesRegex(S.Refused, "P41_APPROVAL"):
                    S.authorize(head, fp, ip, "c" * 64)
                put("untracked", b"dirty\n")
                with self.assertRaisesRegex(S.Refused, "P41_APPROVAL"):
                    S.authorize(head, fp, ip, ap)
                (root / "untracked").unlink()
                put(S.PINS, manifest + b" ")
                with self.assertRaisesRegex(S.Refused, "P41_PIN"):
                    S.pinned(root / S.PINS, fp)


if __name__ == "__main__":
    unittest.main()
