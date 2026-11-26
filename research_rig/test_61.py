"""Artificial Plan 61 witnesses. No live approval, credential, or data path."""
from datetime import date, timedelta
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import score_61 as s
from test_43 import condition
from test_60 import Fixture


BOOT = """
import runpy,sys
from pathlib import Path
from hashlib import sha256
root,data=map(Path,sys.argv[1:3])
g=runpy.run_path(str(root/"research_rig/score_61.py"))["main"].__globals__
s,p,blind=g["s"],g["p"],g["blind"]
inp=data/"plan43_successor_inputs"
changes=dict(ROOT=root,DATA=data,INPUT=inp,DOCKET=data/"docket.jsonl",COLLECTOR=data/"collector.py",
             COLLECTOR_SHA256=sha256((data/"collector.py").read_bytes()).hexdigest(),PREVIOUS_VALIDATION=sys.argv[4])
p.__dict__.update(changes)
p.git.__globals__.update(changes)
s.load_vendor.__globals__.update(VENDOR=data/"plan60_vendor_actions")
s.VENDOR=data/"plan60_vendor_actions"
blind.IDS, blind.ACTIONS, blind.BARS = (sha256((inp/n).read_bytes()).hexdigest()
    for n in ("identities.json","actions.json","bars.json"))
g.update(ROOT=root,RUN=data/"replay_61",VENDOR_APPROVAL=sys.argv[3])
if sys.argv[5]=="--validate-inputs":
    def forbidden(*a,**k):
        raise AssertionError("validation must not calculate returns")
    g.update(score=forbidden,economic=forbidden)
sys.argv=["score_61.py",*sys.argv[5:]]
raise SystemExit(g["main"]())
"""


class Temp61:
    def __init__(self, path, *, frozen=True, wire_fault=None, create=True, large=False):
        old = Fixture(path, wire_fault=wire_fault, large=large)
        self.old, self.f = old, old.f
        f = self.f
        self.run = f.data / "replay_61"
        if create:
            self.run.mkdir(mode=0o700)
        for n in s.SOURCES - s.INHERITED - {s.p.CONFIG}:
            blob = (s.ROOT / n).read_bytes()
            if n == s.PLAN:
                # Freeze only this private synthetic fixture. DRAFT test uses
                # explicit DRAFT text whether the real checkout is frozen or not.
                blob = blob.replace(b"Status FROZEN.", b"Status DRAFT.")
                if frozen:
                    blob = blob.replace(b"Status DRAFT.", b"Status FROZEN.")
            f.put(n, blob)
        for n, num in (("research_rig/TRIAL_LEDGER.md", s.LEDGER), ("docs/QUEUE.md", s.QUEUE)):
            f.put(n, (f.root / n).read_bytes() + f"| {num} | {s.PLAN} | synthetic |\n".encode())
        pins = s.p.render({n: sha256((f.root / n).read_bytes()).hexdigest() for n in s.SOURCES})
        f.put(s.PINS, pins)
        self.freeze = f.commit()
        historic = sha256((f.root / s.s.VALID).read_bytes()).hexdigest()
        a = (f"Approved by the lead: plan 61 ledger 203, adopt Plan 60 validation commit {old.val}, "
             f"Plan 60 validation approval SHA-256 {historic}, freeze commit {self.freeze}, "
             f"freeze SHA-256 {sha256(pins).hexdigest()}, no price acquisition.\n").encode()
        self.adoption = f.commit(s.ADOPT, a)
        v = (f"Approved by the lead: plan 61 ledger 203, validation only, adoption commit {self.adoption}, "
             f"adoption approval SHA-256 {sha256(a).hexdigest()}.\n").encode()
        self.validation = f.commit(s.VALID, v)

    def cli(self, mode, commit=None):
        return subprocess.run([sys.executable, "-I", "-B", "-c", BOOT, str(self.f.root), str(self.f.data),
                               self.old.val, self.old.prior, "--" + mode, "--approval-commit",
                               commit or self.validation], capture_output=True, text=True, timeout=90)

    def go(self, pin=None):
        if pin is None:
            pin = sha256((self.run / f"validation.{self.validation}.json").read_bytes()).hexdigest()
        return self.f.commit(s.GO, (f"Approved by the lead: plan 61 ledger 203, one scored run, validation approval "
                                   f"commit {self.validation}, validation receipt SHA-256 {pin}.\n").encode())


def artificial(wrong_date=False):
    q, days, C, _, ids, bars, actions = condition()
    e = q[0]
    cfg = s.s.config((s.ROOT / s.p.CONFIG).read_bytes())
    verified = s.p.identity_actions(q, days, cfg, ids, actions)
    target = verified[1][e.a]["stock"][1]
    vendor = {e.a: {"stock": (True, [(target+timedelta(days=wrong_date), "cash", Fraction(1), None)]),
                    "IWM": (True, [])}}
    return q, days, C, cfg, verified, vendor, bars["records"]


class Plan61(unittest.TestCase):
    def test_real_queue_and_ledger_rows_name_exact_preregistration(self):
        for number, name in ((s.QUEUE, "docs/QUEUE.md"), (s.LEDGER, "research_rig/TRIAL_LEDGER.md")):
            rows = [line for line in (s.ROOT / name).read_bytes().splitlines()
                    if line.startswith(f"| {number} |".encode())]
            self.assertEqual(len(rows), 1, name)
            self.assertIn(s.PLAN.encode(), rows[0], name)

    def test_cli_synthetic_validation_then_once(self):
        with TemporaryDirectory() as d:
            f = Temp61(Path(d))
            val = f.cli("validate-inputs")
            self.assertEqual((val.returncode, val.stderr), (0, ""))
            unparsed, signal = val.stdout.rsplit("\n", 2)[:2]
            self.assertEqual(signal, "P61_VALIDATED")
            summary = json.loads(unparsed)
            self.assertEqual(summary["placed_pairs"], 1)
            self.assertEqual(summary["gate_counts"]["vendor_ex_agreement"], {"not_evaluable": 1, "pass": 1})
            self.assertFalse((f.run / "score.lock").exists())
            self.assertFalse((f.run / "result.json").exists())
            self.assertEqual(f.cli("validate-inputs").stdout, val.stdout)
            go = f.go()
            scored = f.cli("go", go)
            self.assertEqual((scored.returncode, scored.stdout, scored.stderr), (0, "P61_SCORED_ONCE\n", ""))
            result = json.loads((f.run / "result.json").read_bytes())
            self.assertEqual(result["outcome"]["gate_counts"], summary)
            self.assertEqual(result["outcome"]["shown_only"]["earlier_entry"]["n"], 1)
            self.assertEqual(result["outcome"]["shown_only"]["liquidity_at_least_1m"]["n"], 0)
            self.assertIn("plain_clustered_t", result["outcome"]["shown_only"])
            self.assertFalse(result["outcome"]["judged"]["passed"])
            stopped = f.cli("go", go)
            self.assertEqual((stopped.returncode, stopped.stderr), (2, "P43_CONSUMED\n"))

    def test_cli_draft_and_private_dir(self):
        with TemporaryDirectory() as d:
            f = Temp61(Path(d), frozen=False)
            val = f.cli("validate-inputs")
            self.assertEqual((val.returncode, val.stderr), (2, "P61_DRAFT_NOT_FROZEN\n"))
        with TemporaryDirectory() as d:
            f = Temp61(Path(d), create=False)
            val = f.cli("validate-inputs")
            self.assertEqual(val.returncode, 2)
            self.assertIn("P61_RUN_FOLDER_MISSING: create the private run directory empty with mode 0700", val.stderr)
            f.run.mkdir(mode=0o755)
            val = f.cli("validate-inputs")
            self.assertEqual((val.returncode, val.stderr), (2, "P61_RUN_FOLDER_NOT_PRIVATE\n"))

    def test_cli_wrong_receipt_and_wire_tamper(self):
        with TemporaryDirectory() as d:
            f = Temp61(Path(d))
            self.assertEqual(f.cli("validate-inputs").returncode, 0)
            proc = f.cli("go", f.go("0"*64))
            self.assertEqual((proc.returncode, proc.stderr), (2, "P61_VALIDATION_RECEIPT\n"))
            self.assertFalse((f.run / "score.lock").exists())
        with TemporaryDirectory() as d:
            f = Temp61(Path(d))
            with (f.old.vendor / s.s.VENDOR_NAME).open("ab") as file:
                file.write(b" ")
            val = f.cli("validate-inputs")
            self.assertEqual((val.returncode, val.stderr), (2, "P43_PIN\n"))
            self.assertFalse(any(f.run.iterdir()))

    def test_malformed_ohlc_is_an_event_gate_not_a_run_stop(self):
        with TemporaryDirectory() as d:
            f = Temp61(Path(d), wire_fault="ohlc")
            val = f.cli("validate-inputs")
            self.assertEqual((val.returncode, val.stderr), (0, ""))
            counts = json.loads(val.stdout.rsplit("\n", 2)[0])
            self.assertEqual(counts["gate_counts"]["stock_bars"], {"bar_invalid": 1, "not_evaluable": 1})
            self.assertEqual(counts["gate_counts"]["iwm_bars"], {"pass": 1, "not_evaluable": 1})
            self.assertEqual(counts["placed_pairs"], 0)

    def test_full_synthetic_scope_has_all_gate_counts_and_no_return(self):
        with TemporaryDirectory() as d:
            f = Temp61(Path(d), large=True)
            val = f.cli("validate-inputs")
            self.assertEqual((val.returncode, val.stderr), (0, ""))
            counts = json.loads(val.stdout.rsplit("\n", 2)[0])
            self.assertEqual(counts["placed_pairs"], 442)
            self.assertTrue(all(sum(v.values()) == 443 for v in counts["gate_counts"].values()))
            self.assertFalse((f.run / "result.json").exists())

    def test_vendor_ex_disagreement_is_reported_even_if_basis_fails(self):
        q, days, C, cfg, verified, vendor, bars = artificial(wrong_date=True)
        details, placed = s.prepare(q, days, C, verified, vendor, bars, cfg)
        gate = details[q[0].a]["gates"]
        self.assertEqual(gate["vendor_ex_agreement"], "vendor_ex_disagrees")
        self.assertNotEqual(gate["stock_vendor_basis"], "pass")
        self.assertEqual(gate["stock_clock_volume"], "pass")
        self.assertFalse(placed)

    def test_vendor_crosswalk_uses_cash_amount_and_ex_not_pay_date(self):
        q, _, _, _, verified, vendor, _ = artificial()
        e = q[0]
        act = verified[1][e.a]["stock"]
        target = act[1]
        self.assertEqual(s.crosscheck_ex(e, act, vendor[e.a]["stock"]), "pass")
        self.assertEqual(s.crosscheck_ex(e, act, (True, [(target, "cash", Fraction(2), None)])), "vendor_ex_missing")
        items = [(target, "cash", Fraction(1), None)] * 2
        self.assertEqual(s.crosscheck_ex(e, act, (True, items)), "vendor_ex_ambiguous")
        self.assertLess(act[0][0][3], target)  # Synthetic deferred ex-date.

    def test_vendor_crosswalk_consumes_one_record_per_other_verified_cash_action(self):
        q, days, _, _, verified, _, _ = artificial()
        e = q[0]
        seq, target = verified[1][e.a]["stock"]
        earlier = days[days.index(target)-1]
        ordinary = lambda d: (d, "ordinary", Fraction(1), d, d)
        vendor = lambda d: (d, "cash", Fraction(1), None)
        self.assertEqual(s.crosscheck_ex(e, (seq+[ordinary(target)], target),
                                         (True, [vendor(target), vendor(target)])), "pass")
        self.assertEqual(s.crosscheck_ex(e, (seq+[ordinary(earlier)], target),
                                         (True, [vendor(earlier), vendor(earlier), vendor(target)])),
                         "vendor_ex_ambiguous")

    def test_close_clocks_holding_basis_fees_and_haircut(self):
        _, _, _, cfg, *_ = artificial()
        entry, ex = date(2024, 6, 5), date(2024, 6, 6)
        raw = {entry: SimpleNamespace(o=499, c=100), ex: SimpleNamespace(o=999, c=98)}
        seq = [(ex, "special", Fraction(3), entry, ex)]
        net, special = s.economic((raw, seq, ex), entry, ex, 5, cfg)
        self.assertEqual(net, Fraction(901, 125000))
        self.assertEqual(special, Fraction(12, 500))
        self.assertEqual(net - s.TAX * special, Fraction(181, 125000))
        raw[ex].c = 490
        with self.assertRaisesRegex(s.Stop, "SCORE_LOT"):
            s.economic((raw, [(ex, "split", Fraction(1, 3), None, None)], ex), entry, ex, 5, cfg)

    def test_earlier_clock_is_strict_and_both_clocks_use_calendar_sessions(self):
        q, days, *_ = artificial()
        e = q[0]
        ex = days[days.index(e.early)+1]
        self.assertEqual(s.blind.ex_clock(e, ex, days), (None, e.early, ex))
        self.assertEqual(s.earlier_clock(e, ex, days), ("padding_not_complete_before_entry", None))
        e.at = days.closes[e.early]
        self.assertEqual(s.blind.ex_clock(e, ex, days)[0], "filing_not_public_before_entry_close")

    def test_disposition_uses_raw_money_and_winsorized_evidence(self):
        day = date(2020, 1, 1)
        win = [Fraction(4, 100), Fraction(4, 100), Fraction(1, 100), -Fraction(1, 100)]
        self.assertEqual(s.marks([], [2020])["disposition"], "not_shown_no_forward_disposition")
        rows = [(day+timedelta(days=i), str(i), x) for i,x in enumerate(win)]
        result = s.marks(rows, [2020])
        self.assertEqual(result["disposition"], "not_shown_not_refuted_forward_pretend_only")
        big = [
            (day, "tail", Fraction(3, 4)),
            *((day+timedelta(days=i+1), str(i), Fraction(-2, 100)) for i in range(9)),
        ]
        result = s.marks(big, [2020])
        self.assertGreater(result["paired"]["mean"], 0)
        self.assertLess(result["winsorized_paired"]["mean"], 0)
        self.assertEqual(result["disposition"], "close_row")

    def test_all_marks_can_pass_and_raw_values_remain_unclipped_for_money(self):
        years = range(2016, 2027)
        rows = [(date(y, 1, 1)+timedelta(days=i), f"{y}-{i}", Fraction(2 if i % 2 else 8, 100))
                for y in years for i in range(25)]
        result = s.marks(rows, years)
        self.assertTrue(result["passed"])
        self.assertTrue(all(result["marks"].values()))
        self.assertGreater(result["paired"]["mean"], result["winsorized_paired"]["mean"])
        self.assertEqual(result["trim_removed"], 3)


if __name__ == "__main__":
    unittest.main()
