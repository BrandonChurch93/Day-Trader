"""Price-blind tests for Plan 52. The one-shot rehearsal uses only a disposable Git repo."""
from copy import deepcopy
from datetime import datetime, time, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zoneinfo import ZoneInfo

import common_52 as C
import score_52 as S

BASE = Path(__file__).resolve().parent.parent
CFG = S.read_config((BASE / S.CONFIG).read_bytes())
DAYS = C.calendar([S.parse((BASE / name).read_bytes()) for name in S.CALENDARS], CFG)
SPANS = C.windows(DAYS, CFG)
SYMS = C.symbols(CFG)


def digest(payload):
    return sha256(payload).hexdigest()


def fixture():
    ny = ZoneInfo("America/New_York")
    closes = [
        {"t": datetime.combine(d, time(), ny).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "o": 100, "h": 101 + i % 2, "l": 99, "c": 100, "v": 1000}
        for i, d in enumerate(DAYS)
    ]
    years = {d.year: d for d in DAYS}
    actions = {"schema": 1, "coverage_start": str(DAYS[0]), "coverage_end": str(DAYS[-1]), "funds": {
        sym: {"source": "https://example.org/fixture", "splits": deepcopy(CFG["expected_splits"].get(sym, [])),
              "cash": [{"id": str(y), "ex_date": str(d), "amount": 0.125} for y, d in years.items()]}
        for sym in SYMS
    }}
    return closes, actions


class Engine(unittest.TestCase):
    def test_clock(self):
        self.assertEqual(str(SPANS["quarters"][0][0]), "2016-03-31")
        self.assertEqual(str(SPANS["quarters"][0][1][-1]), "2016-04-05")
        self.assertEqual(str(SPANS["quarters"][-1][1][-1]), "2026-01-06")
        self.assertEqual(str(SPANS["shown"][-1][1][-1]), "2026-10-05")
        self.assertEqual(str(next(held[-1] for e, held in SPANS["controls"] if str(e) == "2019-04-30")), "2019-05-03")

    def test_actions_bad_and_good(self):
        _, actions = fixture()
        self.assertEqual(C.cash_actions(actions, DAYS, SPANS, CFG)[1], 1)
        actions["funds"]["JNK"]["splits"] = []
        with self.assertRaisesRegex(C.Refused, "ACTION_SPLIT_SET"):
            C.cash_actions(actions, DAYS, SPANS, CFG)
        actions["funds"]["JNK"]["splits"] = deepcopy(CFG["expected_splits"]["JNK"])
        event = C.day(CFG["expected_splits"]["JNK"][0]["ex_date"])
        with self.assertRaisesRegex(C.Refused, "ACTION_SPLIT_WINDOW"):
            C.cash_actions(actions, DAYS, SPANS | {"shown": [(C.day("2019-05-03"), (event,))]}, CFG)
        actions["funds"]["LQD"]["cash"].append(actions["funds"]["LQD"]["cash"][0])
        with self.assertRaisesRegex(C.Refused, "ACTION_CASH"):
            C.cash_actions(actions, DAYS, SPANS, CFG)

    def test_bad_bars(self):
        closes, _ = fixture()
        examples = [("BAR_CLOCK", "t", "2016-01-04T06:00:00Z"), ("BAR_VALUES", "v", 0),
                    ("BAR_VALUES", "c", True), ("BAR_VALUES", "h", 90), ("BAR_FIELDS", "extra", 1)]
        for error, key, value in examples:
            with self.subTest(key=key, value=value):
                rows = [closes[0] | {key: value}, *closes[1:]]
                with self.assertRaisesRegex(C.Refused, error):
                    C.bars(rows, DAYS, CFG)
        rows = [row | {"h": 101} for row in closes]
        with self.assertRaisesRegex(C.Refused, "BAR_STALE"):
            C.bars(rows, DAYS, CFG)
        with self.assertRaisesRegex(C.Refused, "BAR_COVERAGE"):
            C.bars(closes[1:], DAYS, CFG)

    def test_math_and_proxy_map(self):
        prices = {s: dict.fromkeys(DAYS, 100) for s in SYMS}
        cash = {s: {} for s in SYMS}
        entry, held = SPANS["quarters"][0]
        cash["LQD"] = {entry: 900, held[0]: 2, held[-1]: 1}
        cash["IEF"] = {held[1]: 4}
        prices["IEI"][held[-1]] = 98
        outcomes = C.evaluate(SPANS, prices, cash, CFG)
        event = outcomes["events"]["quarters"][0]
        fee = CFG["cost_bps_per_side"] / C.BPS
        expected = (100*(1-fee) + 3/4) / (100*(1+fee)) - 1
        self.assertAlmostEqual(event["net"], expected)
        self.assertAlmostEqual(event["proxy_net"], expected - (0.04 - 0.02) / 2)
        self.assertAlmostEqual(event["net_usd"], expected * CFG["budget_usd"])
        self.assertEqual(set(outcomes["events"]), {"quarters", "shown", "controls"})

    def test_judgment(self):
        labels = [e.month != 12 for e, _ in SPANS["quarters"]]
        n = len(labels)
        varied = [0.02 + (i % 2) * 0.001 for i in range(n)]
        self.assertTrue(C.judge(varied, varied, [0], labels, CFG)["supported"])
        strict = CFG | {"marks": CFG["marks"] | {"raw_t_required": True, "breadth": "sixty_percent"}}
        self.assertFalse(C.judge([0.02] * n, varied, [0], labels, strict)["marks"]["t_net"])
        selected = C.judge([0.02] * n, varied, [0], labels, CFG)
        self.assertIsNone(selected["net"]["t"])
        self.assertEqual("t_net" in selected["marks"], CFG["marks"]["raw_t_required"])
        self.assertEqual("positive_quarters" in selected["marks"], CFG["marks"]["breadth"] != "none")
        self.assertFalse(C.judge(varied, [0.02] * n, [0], labels, CFG)["marks"]["t_proxy_net"])
        self.assertFalse(C.judge(varied, varied, varied, labels, CFG)["marks"]["above_non_quarter_month_ends"])
        only_best = [0] * n
        only_best[:CFG["marks"]["drop_best"]] = [1] * CFG["marks"]["drop_best"]
        self.assertFalse(C.judge(only_best, varied, [0], labels, CFG)["marks"]["trimmed_net"])
        december_only = [-0.001 if keep else 0.04 for keep in labels]
        self.assertFalse(C.judge(december_only, varied, [0], labels, CFG)["marks"]["non_december_net"])

    def test_shown_gap(self):
        shown = C.shown_gap([2, 4], [0, 2])
        self.assertEqual(shown["net_mean_difference"], 2)
        self.assertAlmostEqual(shown["welch_t"], 2**0.5)
        self.assertIsNone(C.shown_gap([5, 5], [0, 0])["welch_t"])

    def test_claim_survives_failure(self):
        with TemporaryDirectory() as d:
            run = Path(d)
            old = os.umask(0o077)
            try:
                with self.assertRaisesRegex(RuntimeError, "after claim"):
                    def fail():
                        raise RuntimeError("after claim")
                    S.once(run, {}, (), fail)
                self.assertEqual({p.name for p in run.iterdir()}, {"score_52.lock"})
                with self.assertRaisesRegex(S.Refused, "CONSUMED"):
                    S.once(run, {}, (), dict)
            finally:
                os.umask(old)


class CLI(unittest.TestCase):
    def test_disposable_git(self):
        env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
               "GIT_CONFIG_GLOBAL": "/dev/null"}
        with TemporaryDirectory(prefix="synthetic-plan52-") as d:
            top = Path(d)
            repo, data = top / "repo", top / "synthetic"
            repo.mkdir()
            data.mkdir(mode=0o700)
            packet, run = data / "plan52_inputs", data / "replay_52"
            packet.mkdir(mode=0o700)
            run.mkdir(mode=0o700)

            def git(*args):
                return subprocess.check_output(
                    ["/usr/bin/git", "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.org", *args],
                    cwd=repo, env=env, stderr=subprocess.PIPE, text=True).strip()

            def write(parent, name, content, mode=0o600):
                dest = parent / name
                dest.parent.mkdir(exist_ok=True, parents=True)
                dest.write_bytes(content)
                dest.chmod(mode)
                return digest(content)

            def cli(*args, ok=True):
                cmd = [sys.executable, "-IB", str(repo / "research_rig/score_52.py"), *args]
                r = subprocess.run(cmd, cwd=repo, env={"PATH": env["PATH"], "LC_ALL": "C"}, capture_output=True, timeout=35)
                self.assertEqual(r.returncode, 0 if ok else 2, (r.stdout, r.stderr))
                return r

            git("init", "-q")
            test_pins = {}
            for name in sorted(S.PIN_NAMES):
                source = (BASE / name).read_bytes()
                if name == S.PLAN:
                    source = re_status(source)
                if name.endswith("/score_52.py"):
                    original = str(S.DATA).encode()
                    self.assertEqual(source.count(original), 1)
                    source = source.replace(original, str(data).encode())
                test_pins[name] = write(repo, name, source)
            for name, row in (("research_rig/TRIAL_LEDGER.md", CFG["ledger_row"]), ("docs/QUEUE.md", CFG["queue_row"])):
                write(repo, name, f"| {row} | `{S.PLAN}` |\n".encode())
            freeze_pin = write(repo, S.PINS, S.encode(test_pins))
            git("add", ".")
            git("commit", "-qm", "synthetic freeze")
            freeze = git("rev-parse", "HEAD")

            closes, actions = fixture()
            hashes = {f"{s}.json": write(packet, f"{s}.json", S.encode(closes)) for s in SYMS}
            actions_pin = hashes["cash_actions.json"] = write(packet, "cash_actions.json", S.encode(actions))
            manifest = {"schema": 1, "vendor": "synthetic", "feed": "sip", "adjustment": "raw", "frequency": "daily",
                        "start": str(DAYS[0]), "end": str(DAYS[-1]), "collected_utc": "2026-10-06T00:01:00Z", "files": hashes}
            input_pin = write(packet, "manifest.json", S.encode(manifest))
            template = ("Approved by the lead: plan 52, validation and one scored run, freeze commit "
                        f"{freeze}, freeze SHA-256 {freeze_pin}, input SHA-256 {input_pin}, "
                        f"actions SHA-256 {actions_pin}.\n").encode()

            def flags():
                return ("--approval-commit", git("rev-parse", "HEAD"), "--freeze-sha256", freeze_pin,
                        "--input-sha256", input_pin, "--actions-sha256", actions_pin)

            synthetic_cal = cli("--calibrate")
            self.assertEqual(synthetic_cal.stdout, (BASE / S.CALIBRATION).read_bytes())
            calibrated = json.loads(synthetic_cal.stdout)
            self.assertTrue(calibrated["synthetic_only"])
            self.assertEqual(len(calibrated["variants"]), 6)
            self.assertEqual(calibrated["selected"], {k: CFG["marks"][k] for k in ("raw_t_required", "breadth")})
            for row in calibrated["variants"]:
                quarter, both = (row["scenarios"][k] for k in ("quarter_only", "all_month_ends"))
                self.assertEqual(quarter["0"], both["0"])
                self.assertTrue(all(both[x]["count"] <= quarter[x]["count"] for x in quarter))
            self.assertEqual(cli("--go", ok=False).stderr, b"P52_ARGUMENTS\n")
            self.assertEqual(cli("--go", *flags(), ok=False).stderr, b"P52_APPROVAL\n")
            write(repo, S.APPROVAL, template)
            write(repo, "extra.txt", b"disallowed\n")
            git("add", ".")
            git("commit", "-qm", "invalid extra-file approval")
            self.assertEqual(cli("--go", *flags(), ok=False).stderr, b"P52_APPROVAL\n")
            git("reset", "--hard", freeze)
            write(repo, S.APPROVAL, template)
            git("add", S.APPROVAL)
            git("commit", "-qm", "sole-file synthetic approval")

            write(repo, "dirty", b"dirty")
            self.assertEqual(cli("--go", *flags(), ok=False).stderr, b"P52_APPROVAL\n")
            (repo / "dirty").unlink()
            bar = packet / f"{SYMS[0]}.json"
            bar.chmod(0o644)
            self.assertEqual(cli("--validate-inputs", *flags(), ok=False).stderr, b"P52_PRIVATE\n")
            bar.chmod(0o600)
            write(packet, bar.name, b"\"tampered\"")
            self.assertEqual(cli("--go", *flags(), ok=False).stderr, b"P52_PIN\n")
            write(packet, bar.name, S.encode(closes))
            self.assertFalse(list(run.iterdir()))
            validation = cli("--validate-inputs", *flags())
            self.assertRegex(validation.stdout, rb"^P52_INPUTS_OK( [a-z_]+ [0-9]+)+\n$")
            self.assertIn(b"splits_checked 1 crossed_splits 0", validation.stdout)
            self.assertFalse(list(run.iterdir()))
            self.assertEqual(cli("--go", *flags()).stdout, b"P52_RESULT_WRITTEN\n")
            output = (run / "results_52.json").read_bytes()
            self.assertIn("judged", json.loads(output))
            self.assertIn("welch_t", json.loads(output)["shown_only"]["quarter_minus_control_net"])
            self.assertEqual(cli("--go", *flags(), ok=False).stderr, b"P52_CONSUMED_OR_NOT_EMPTY\n")
            self.assertEqual((run / "results_52.json").read_bytes(), output)


def re_status(blob):
    rows = blob.splitlines(keepends=True)
    return b"".join(b"Status FROZEN.\n" if s.startswith(b"Status ") else s for s in rows)


if __name__ == "__main__":
    unittest.main()
