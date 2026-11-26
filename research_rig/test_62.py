"""Synthetic Plan 62 witnesses; no private inputs, credentials or real CLI modes."""
from fractions import Fraction as F
import json
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import score_62 as s
from test_61 import artificial, Temp61


class Plan62(unittest.TestCase):
    def test_real_queue_and_ledger_point_to_preregistration(self):
        for n, path in ((s.QUEUE, "docs/QUEUE.md"), (s.LEDGER, "research_rig/TRIAL_LEDGER.md")):
            rows = [x for x in (s.ROOT / path).read_bytes().splitlines() if x.startswith(f"| {n} |".encode())]
            self.assertEqual(len(rows), 1)
            self.assertIn(s.PLAN.encode(), rows[0])

    def test_gate_does_not_relabel_disagreement_ambiguity_or_mapping(self):
        q, days, _, _, verified, _, _ = artificial()
        e = q[0]
        act = verified[1][e.a]["stock"]
        ex = act[1]
        prev = days[days.index(ex) - 1]
        cash = lambda day, amount: (day, "cash", F(amount), None)
        for expected, complete, items in (
                ("pass", True, [cash(ex, 1)]),
                (s.CLASS_A, True, [cash(ex, ".99")]),
                (s.CLASS_A, True, [cash(ex, "1.70")]),
                ("vendor_ex_missing", True, [cash(ex, ".989"), cash(ex, ".989")]),
                ("vendor_ex_missing", True, [cash(prev, "1.70")]),
                ("vendor_ex_missing", True, [(ex, "unsupported", "cash", None)]),
                ("vendor_ex_disagrees", True, [cash(ex, "1.70"), cash(prev, 1)]),
                ("vendor_ex_ambiguous", True, [cash(ex, "1.70"), cash(prev, 1), cash(ex, 1)]),
                ("vendor_mapping_or_coverage", False, [cash(ex, "1.70")]),
        ):
            with self.subTest(expected=expected, items=items):
                self.assertEqual(s.vendor_status(e, act, (complete, items)), expected)

    def test_class_a_basis_remains_required_and_cash_economics_do_not_change(self):
        q, days, C, cfg, verified, vendor, bars = artificial()
        e = q[0]
        args = q, days, C, verified, vendor, bars, cfg
        exact_decisions, exact_placed = s.prepare(*args)
        self.assertEqual(len(exact_placed), 1)
        exact = s.score(exact_placed, exact_decisions, s.summary(exact_decisions), cfg, [exact_placed[0][2].year])
        ex, _, _, _ = vendor[e.a]["stock"][1][0]
        # Unchanged adjusted data do not explain this larger vendor term.
        vendor[e.a]["stock"] = True, [(ex, "cash", F("1.50"), None)]
        bad, not_placed = s.prepare(*args)
        self.assertEqual(bad[e.a]["gates"]["vendor_ex_agreement"], s.CLASS_A)
        self.assertEqual(bad[e.a]["gates"]["stock_vendor_basis"], "vendor_basis_mismatch")
        self.assertFalse(not_placed)
        # An already verified explicit adjustment factor may preserve the
        # unchanged basis; the higher cash amount still cannot feed economics.
        prior_close = s.p.exact(exact_placed[0][3]["stock"][0][days[days.index(ex) - 1]].c)
        vendor[e.a]["stock"] = True, [(ex, "cash", F("1.50"), 1 - 1 / prior_close)]
        new_decisions, new_placed = s.prepare(*args)
        self.assertEqual(len(new_placed), 1)
        self.assertEqual(new_placed, exact_placed)
        counts = s.summary(new_decisions)
        self.assertEqual(counts["placed_by_vendor_ex_status"], {"vendor_exact_match": 0, "vendor_class_a": 1})
        result = s.score(new_placed, new_decisions, counts, cfg, [ex.year])
        self.assertEqual(result["judged"], exact["judged"])
        self.assertEqual(result["shown_only"]["vendor_class_a"], exact["shown_only"]["vendor_exact_match"])
        self.assertEqual(result["shown_only"]["vendor_exact_match"], {"n": 0, "paired_mean": None})
        for line, value in result["shown_only"].items():
            if not line.startswith("vendor_"):
                self.assertEqual(value, exact["shown_only"][line])

    def test_git_authorization_has_separate_freeze_and_excludes_plan61_go(self):
        with TemporaryDirectory() as tmp:
            prior = Temp61(Path(tmp))
            f = prior.f
            for path in s.COUNT_FILES:
                f.put(path, (s.ROOT / path).read_bytes())
            count_approval = f.commit()
            for path in s.SOURCES - s.INHERITED - s.COUNT_FILES:
                blob = (s.ROOT / path).read_bytes()
                f.put(path, blob.replace(b"Status DRAFT.", b"Status FROZEN.") if path == s.PLAN else blob)
            for n, path in ((s.QUEUE, "docs/QUEUE.md"), (s.LEDGER, "research_rig/TRIAL_LEDGER.md")):
                kept = b"".join(x for x in (f.root / path).read_bytes().splitlines(keepends=True)
                                if not x.startswith(f"| {n} |".encode()))
                f.put(path, kept + f"| {n} | {s.PLAN} | synthetic |\n".encode())
            pins = s.p.render({n: sha256((f.root / n).read_bytes()).hexdigest() for n in s.SOURCES})
            f.put(s.PINS, pins)
            freeze = f.commit()
            digest = sha256((f.root / s.b.VALID).read_bytes()).hexdigest()
            adopt = (f"Approved by the lead: plan 62 ledger 205, adopt Plan 61 validation commit {prior.validation}, "
                     f"Plan 61 validation approval SHA-256 {digest}, freeze commit {freeze}, "
                     f"freeze SHA-256 {sha256(pins).hexdigest()}, no price acquisition.\n").encode()
            adoption = f.commit(s.ADOPT, adopt)
            validation = f.commit(s.VALID, (
                f"Approved by the lead: plan 62 ledger 205, validation only, adoption commit {adoption}, "
                f"adoption approval SHA-256 {sha256(adopt).hexdigest()}.\n").encode())
            with patch.multiple(s, ROOT=f.root, PRIOR_VALID=prior.validation, PRIOR_FREEZE=prior.freeze,
                                COUNT_APPROVAL=count_approval), \
                    patch.dict(s.p.git.__globals__, {"ROOT": f.root}), \
                    patch.object(s.b, "VENDOR_APPROVAL", prior.old.val), \
                    patch.object(s.b, "historical", return_value=("unused", "price", {}, "vendor", "index")):
                _, job = s.authorize(validation, "validate")
                self.assertEqual(job["validation_commit"], validation)
                self.assertEqual(job["count_approval_commit"], count_approval)
                with self.assertRaises(s.p.Refused):
                    s.authorize(validation, "go")
                go = f.commit(s.GO, (f"Approved by the lead: plan 62 ledger 205, one scored run, "
                                     f"validation approval commit {validation}, validation receipt SHA-256 "
                                     + "1"*64 + ".\n").encode())
                _, job = s.authorize(go, "go")
                self.assertEqual(job["go_commit"], go)

    def test_validation_and_one_shot_go_use_only_new_folder(self):
        q, days, C, cfg, verified, vendor, bars = artificial()
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            run, old = root / "replay_62", root / "replay_61"
            run.mkdir(mode=0o700)
            old.mkdir(mode=0o700)
            (old / "sentinel").write_bytes(b"unchanged")
            val = dict(validation_commit="validation")
            job = val.copy()
            with patch.multiple(s, RUN=run, authorize=lambda *_: ({s.p.CONFIG: b""}, job.copy()),
                                sys=SimpleNamespace(stdout=SimpleNamespace(buffer=SimpleNamespace(write=lambda _: None)))), \
                    patch.object(s.b.s, "config", return_value=cfg), patch.object(s.p, "resources"), \
                    patch.object(s.b, "check_proof", return_value=[days[0].year]), \
                    patch.object(s.b, "load", return_value=(q, days, C, verified, vendor, bars)):
                with patch.object(s, "score", side_effect=AssertionError("validation scored")):
                    s.execute("validation", "validate")
                self.assertFalse((run / "score.lock").exists())
                self.assertFalse((run / "result.json").exists())
                receipt = (run / "validation.validation.json").read_bytes()
                job.update(go_commit="go", validation_receipt_sha256=sha256(receipt).hexdigest())
                s.execute("go", "go")
                scored = json.loads((run / "result.json").read_bytes())
                self.assertEqual(scored["outcome"]["gate_counts"]["placed_pairs"], 1)
                with self.assertRaisesRegex(s.p.Refused, "P43_CONSUMED"):
                    s.execute("go", "go")
            self.assertEqual(list(old.iterdir()), [old / "sentinel"])
            self.assertEqual((old / "sentinel").read_bytes(), b"unchanged")


if __name__ == "__main__":
    unittest.main()
