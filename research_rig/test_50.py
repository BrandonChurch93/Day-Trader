"""Only invented data. All real CLI branches execute in isolated temporary Git repositories."""
from collections import Counter
from datetime import timedelta
from decimal import Decimal
from fractions import Fraction as F
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase, main

import common_50 as C
import score_50 as S

URL = "https://example.invalid/invented"
ENV = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1",
       "GIT_CONFIG_GLOBAL": "/dev/null",
       "GIT_AUTHOR_NAME": "Synthetic", "GIT_AUTHOR_EMAIL": "synthetic@example.invalid",
       "GIT_COMMITTER_NAME": "Synthetic", "GIT_COMMITTER_EMAIL": "synthetic@example.invalid"}


def digest(b):
    return sha256(b).hexdigest()


class Packet:
    def __init__(self, root, *, draft=False, bad_pin=False, missing=False, fail_score=False,
                 bad_identity=False, late_notice=False, raise_floor=False):
        self.root = root
        repo = self.repo = root / "repo"
        repo.mkdir()
        inp = self.inp = root / "private" / "plan50_inputs"
        out = self.out = inp.parent / "replay_50"
        inp.parent.mkdir(mode=0o700)
        inp.mkdir(mode=0o700)
        out.mkdir(mode=0o700)
        for path in S.PIN_NAMES | {S.PINS, "research_rig/TRIAL_LEDGER.md", "docs/QUEUE.md"}:
            (repo / path).parent.mkdir(parents=True, exist_ok=True)
        d = S.parse((S.REPO / S.CALENDAR).read_bytes())
        d["sessions"] = [x for x in d["sessions"] if "2018-12-01" <= x[0] <= "2020-04-01"]
        cal = C.calendar(d)
        ds = list(cal)
        cfg = S.read_config((S.REPO / S.CONFIG).read_bytes())
        cfg.update(first_day="2019-01-01", last_data=ds[-1], last_entry=ds[-181],
                   min_placed=9 if raise_floor else 7)
        cfg["calibration"].update(trials=80, null_ceiling=Decimal("0.10"))
        # Only path substitution in the CLI. The optional failure injection
        # alters a separate synthetic engine before that fixture's freeze.
        runner = (S.REPO / "research_rig/score_50.py").read_text().replace(
            'Path("/home/user/workspace/rig/data")', f"Path({str(inp.parent)!r})")
        (repo / "research_rig/score_50.py").write_text(runner)
        engine = (S.REPO / S.ENGINE).read_text()
        if fail_score:
            engine += "\ndef evaluate(*args):\n    raise RuntimeError('invented post-claim failure')\n"
        (repo / S.ENGINE).write_text(engine)
        shutil.copyfile(__file__, repo / "research_rig/test_50.py")
        (repo / S.CALENDAR).write_bytes(S.encode(d))
        status = "DRAFT." if draft else "FROZEN."
        (repo / S.PLAN).write_text(f"Invented fixture\nStatus {status}\n")
        for name, row in (("research_rig/TRIAL_LEDGER.md", S.LEDGER_ROW), ("docs/QUEUE.md", S.QUEUE_ROW)):
            (repo / name).write_text(f"| {row} | `{S.PLAN}` |\n")
        # A value outside the Plan 50 block also participates in the digest.
        cfg_json = json.dumps(cfg, default=float, separators=(",", ":"))
        (repo / S.CONFIG).write_text("unrelated_setting: audited\nreplay_50_plan:\n  value: " + cfg_json + "\n")
        (repo / S.CALIBRATION).write_bytes(self.cli("--calibrate", args=False).stdout)

        fixtures = [
            ("WIN", "liquidation", "2019-01-10T14:15:00Z", None, "completed", "2019-01-18", "2019-01-09"),
            ("ETF", "open_ending", "2019-02-04", None, "completed", "2019-02-15", "2019-02-15T19:55:00Z"),
            ("TERM", "term", "2018-12-10", "2019-02-15", "completed", "2019-02-14", "2019-02-12"),
            ("LOSS", "open_ending", "2019-03-01", None, "failed", "2019-03-07", None),
            ("CANCEL", "term", "2018-12-14", "2019-04-12", "cancelled", "2019-04-01T13:14:59Z", None),
            ("LIVE", "open_ending", "2019-04-02", None, "no_trigger", None, None),
            ("SILENT", "liquidation", "2019-05-02", None, "completed", "2019-06-03", None),
            ("SPLIT", "liquidation", "2019-05-06", None, "completed", "2019-05-15", "2019-05-13"),
        ]
        if missing:
            fixtures.extend([
                ("NOBAR", "liquidation", "2019-05-02", None, "no_trigger", None, None),
                ("NOEXIT", "open_ending", "2019-05-02", None, "no_trigger", None, None),
                ("CLOCK", "open_ending", "2019-05-06", None, "unresolved", None, None),
            ])
        ev = {"schema": 1, "status": "INDEPENDENT_PRICE_BLIND_REVIEW",
              "excluded": [{"id": "VOTE", "reason": "not_board_backed", "source": URL}], "events": []}
        for ident, k, signal, term, terminal, clock, notice in fixtures:
            ev["events"].append(dict(id=ident, ticker=ident, asset="municipal", kind=k, signal=signal,
                                     term_date=term, terminal=terminal, terminal_clock=clock, terminal_notice=notice,
                                     terminal_notice_source=URL if notice is not None else None,
                                     terms_source=URL, terminal_source=URL, asset_source=URL, listing_source=URL))
        rows = self.rows = C.events(ev, cal, cfg)
        if late_notice:
            next(e for e in ev["events"] if e["id"] == "ETF")["terminal_notice"] = "2019-02-15T21:00:00Z"
        a = {}
        instruments = {}
        for ident, row in rows.items():
            a[ident] = dict(cef=[], benchmark=[], claims=[], intervening=[], coverage=dict(cef=URL, benchmark=URL))
            instruments[ident] = dict(cef_id=ident, cef_exchange="NYSE", benchmark_id="ETF-MUB",
                                      benchmark_exchange="NYSE Arca", benchmark=row["benchmark"],
                                      listing=URL, asset_source=URL, benchmark_source=URL)
        a["WIN"]["cef"] = [dict(id="I", kind="interim", ex_date="2019-01-14", amount=None, source=URL)]
        a["WIN"]["claims"] = [dict(id="F", kind="final", entitlement_date="2019-01-18",
                                  paid_date="2019-01-23", amount=52, source=URL)]
        a["SPLIT"]["intervening"] = [dict(id="S", leg="cef", kind="forward_split", date="2019-05-13", source=URL)]
        bars = []
        for sym, date in sorted(C.bar_keys(rows)):
            absence = ((sym == "NOBAR" and date == rows[sym]["entry"]) or
                       (sym == "NOEXIT" and date == rows[sym]["end"]))
            bars.append(dict(symbol=sym, session=date, state="documented_missing" if absence else "present",
                             security_id="ETF-MUB" if sym == "MUB" else sym,
                             volume=None if absence else 123, open=None if absence else 48,
                             close=None if absence else (49 if sym == "MUB" else 50)))
        quotes = {}
        for sym, date, side in sorted(C.quote_keys(rows)):
            clock = cal[date][side]
            updates = [] if sym == "LIVE" else [
                [(clock + timedelta(seconds=t)).strftime("%Y-%m-%dT%H:%M:%SZ"), 48, 49, 10, 10]
                for t in range(-400, -60, 35)]
            quotes[S.quote_name((sym, date, side))] = dict(schema=1, symbol=sym, session=date, side=side,
                    security_id="ETF-MUB" if sym == "MUB" else sym, updates=updates)
        if bad_identity:
            bars[0]["security_id"] = "REUSED"
        payloads = {"events.json": ev,
                    "instruments.json": dict(schema=1, status="INDEPENDENT_POINT_IN_TIME_INSTRUMENT_REVIEW", rows=instruments),
                    "actions.json": dict(schema=1, status="INDEPENDENT_ISSUER_CASH_AND_ACTION_REVIEW", rows=a),
                    "bars.json": dict(schema=1, bars=bars), **quotes}
        file_hash = {}
        for name, payload in payloads.items():
            file_hash[name] = self.private(name, S.encode(payload))
        self.provenance = tuple(file_hash[x] for x in S.PROVENANCE)
        self.input_pin = self.private("manifest.json", S.encode(dict(schema=1, mode="plan50_raw_sip_v1", feed="sip",
                                      adjustment="raw", first_day=cfg["first_day"], last_data=cfg["last_data"],
                                      collected_utc="2020-04-02T20:00:00Z", files=file_hash)))
        pins = {p: digest((repo / p).read_bytes()) for p in S.PIN_NAMES}
        pins.update({"packet:"+p: file_hash[p] for p in S.PROVENANCE})
        if bad_pin:
            (repo / S.CONFIG).write_text("tampered_other_setting: now\n" + (repo / S.CONFIG).read_text())
        (repo / S.PINS).write_bytes(S.encode(pins))
        self.freeze_pin = digest((repo / S.PINS).read_bytes())
        self.git("init", "-q")
        self.git("add", ".")
        self.git("commit", "-qm", "invented freeze")
        self.freeze = self.head()
        self.approve()

    def git(self, *args):
        return subprocess.run(["/usr/bin/git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, env=ENV, timeout=10).stdout

    def head(self):
        return self.git("rev-parse", "HEAD").decode().strip()

    def approve(self, wrong_parent=False, extra=False):
        if wrong_parent:
            self.git("commit", "--allow-empty", "-qm", "not the approved freeze")
        if extra:
            (self.repo / "also_added").write_text("unapproved scope")
        e, i, a = self.provenance
        (self.repo / S.APPROVAL).write_text(f"Approved by the lead: plan 50, validation and one scored run, "
                                           f"freeze commit {self.freeze}, freeze SHA-256 {self.freeze_pin}, "
                                           f"input SHA-256 {self.input_pin}, events SHA-256 {e}, "
                                           f"instruments SHA-256 {i}, actions SHA-256 {a}.\n")
        self.git("add", ".")
        self.git("commit", "-qm", "invented sole approval")
        self.approval = self.head()

    def private(self, name, b):
        path = self.inp / name
        path.write_bytes(b)
        path.chmod(0o600)
        return digest(b)

    def cli(self, mode, *, args=True, check=True, env=None, isolated=True):
        argv = [] if not args else [x for k, v in zip(
            ("approval-commit", "freeze-sha256", "input-sha256", "events-sha256", "instruments-sha256", "actions-sha256"),
            (self.approval, self.freeze_pin, self.input_pin, *self.provenance)) for x in ("--"+k, v)]
        return subprocess.run([sys.executable, "-IB" if isolated else "-B", "research_rig/score_50.py", mode, *argv],
                              cwd=self.repo, env=env or {"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                              check=check, capture_output=True, timeout=30)


class Tests(TestCase):
    def fixture(self, **kwargs):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return Packet(Path(tmp.name), **kwargs)

    def refused(self, packet, why, mode="--validate-inputs", **kwargs):
        r = packet.cli(mode, check=False, **kwargs)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (2, b"", ("P50_" + why + "\n").encode()))

    def test_every_mode_and_exit(self):
        f = self.fixture()
        self.assertEqual(f.cli("--calibrate", args=False).stdout, (f.repo / S.CALIBRATION).read_bytes())
        result = json.loads(f.cli("--validate-inputs").stdout)
        self.assertEqual(result, dict(status="P50_INPUTS_OK", placed=7,
                                      by_type=dict(liquidation=2, open_ending=3, term=2),
                                      clusters=5, refused=dict(intervening_action=1), unresolved=0,
                                      coverage_ok=True, excluded_preprice=dict(not_board_backed=1)))
        self.assertEqual(list(f.out.iterdir()), [])
        self.assertEqual(f.cli("--go").stdout, b"P50_RESULT_WRITTEN\n")
        self.assertTrue((f.out / "score_50.lock").is_file())
        g = json.loads((f.out / "results_50.json").read_bytes())
        self.assertEqual(Counter(x["exit_type"] for x in g["rows"]),
                         dict(completed=3, failed=1, cancelled=1, time_stop=2))
        byid = {x["id"]: x for x in g["rows"]}
        self.assertEqual(byid["WIN"]["entry"], "2019-01-10")
        self.assertEqual(byid["LOSS"]["exit"], "2019-03-08")
        self.assertEqual(byid["CANCEL"]["exit"], "2019-04-01")
        self.assertEqual(byid["ETF"]["exit"], "2019-02-15")
        self.assertGreater(byid["WIN"]["shown_documented_cash_raw"], byid["WIN"]["raw"])
        self.assertEqual(g["undocumented_interims"], dict(cef=1, benchmark=0))
        self.assertEqual(g["shown_documented_cash"]["n"], 1)
        self.assertFalse(g["passed"])
        self.refused(f, "CONSUMED_OR_NOT_EMPTY", "--go")

    def test_missing_is_inconclusive_counted_without_returns(self):
        f = self.fixture(missing=True)
        validated = json.loads(f.cli("--validate-inputs").stdout)
        self.assertEqual(validated["unresolved"], 3)
        self.assertEqual(validated["refused"],
                         dict(missing_entry=1, missing_exit=1, intervening_action=1, unresolved_exit_clock=1))
        self.assertFalse(validated["coverage_ok"])
        self.assertEqual(list(f.out.iterdir()), [])
        f.cli("--go")
        self.assertTrue(json.loads((f.out / "results_50.json").read_bytes())["inconclusive"])

    def test_freeze_and_full_config(self):
        self.refused(self.fixture(draft=True), "FREEZE")
        self.refused(self.fixture(bad_pin=True), "PIN")
        f = self.fixture()
        f.git("reset", "--hard", f.freeze)
        f.approve(extra=True)
        self.refused(f, "APPROVAL")
        f.git("reset", "--hard", f.freeze)
        f.approve(wrong_parent=True)
        self.refused(f, "APPROVAL")

    def test_private_clean_head_environment_and_packet_mismatch(self):
        f = self.fixture()
        self.refused(f, "ENVIRONMENT", isolated=False)
        (f.repo / "new_file").touch()
        self.refused(f, "APPROVAL")
        (f.repo / "new_file").unlink()
        p = f.inp / "bars.json"
        p.chmod(0o644)
        self.refused(f, "PRIVATE")
        p.chmod(0o600)
        p.write_bytes(p.read_bytes() + b"\n")
        self.refused(f, "PIN")
        self.assertEqual(list(f.out.iterdir()), [])

    def test_failure_consumes(self):
        f = self.fixture(fail_score=True)
        self.refused(f, "REFUSED", "--go")
        self.assertEqual([x.name for x in f.out.iterdir()], ["score_50.lock"])
        self.refused(f, "CONSUMED_OR_NOT_EMPTY", "--go")

    def test_reviewed_notice_and_instrument_identity_still_check(self):
        self.refused(self.fixture(bad_identity=True), "BAR_IDENTITY_OR_DUPLICATE")
        self.refused(self.fixture(late_notice=True), "LAST_REGULAR_NOTICE")

    def test_preprice_floor_precedes_market_file_reads(self):
        f = self.fixture(raise_floor=True)
        (f.inp / "bars.json").unlink()
        self.refused(f, "PREPRICE_COUNT_FLOOR")
        self.assertEqual(list(f.out.iterdir()), [])

    def test_quote_updates_end_previous_state_and_ties_follow_sequence(self):
        p = S.read_config((S.REPO / S.CONFIG).read_bytes())
        valid = [(-360 + 60*i, F(99), F(101)) for i in range(5)]
        self.assertEqual(C.half_spread(valid, p), F(1, 100))
        for bid, ask in [(100, 100), (101, 99), (0, 100)]:
            cut = [t for row in valid for t in [row, (row[0]+1, bid, ask)]]
            self.assertIsNone(C.half_spread(cut, p))
            tied = [t for row in valid for t in [row, (row[0], bid, ask)]]
            self.assertIsNone(C.half_spread(tied, p))
        self.assertEqual(C.costs({"a": None, "b": C.half_spread(valid, p)}, "a", "b", p),
                         (F(55, 10000), F(105, 10000), 1))

    def test_cluster_and_trim_uses_common_months_and_tie_break(self):
        p = S.read_config((S.REPO / S.CONFIG).read_bytes())
        rows = [dict(id="d", raw=F(1, 10), excess=F(1, 10), cluster="X"),
                dict(id="a", raw=F(-1, 10), excess=F(1, 10), cluster="X"),
                dict(id="b", raw=F(-1, 10), excess=F(1, 10), cluster="Y"),
                dict(id="c", raw=F(-1, 10), excess=F(1, 10), cluster="Y")]
        self.assertEqual(C.clustered_t(rows), (2, None))
        self.assertEqual(C.judge(rows, p)["trimmed"]["raw_mean"], 0.1)
        rows[-1]["excess"] = F(-3, 10)
        self.assertEqual(C.clustered_t(rows), (2, 0.0))

    def test_no_publish_for_duplicate_json_and_exact_open_lag(self):
        with self.assertRaisesRegex(S.Refused, "JSON_DUPLICATE"):
            S.parse(b'{"same":1,"same":2}')
        cal = C.calendar(S.parse((S.REPO / S.CALENDAR).read_bytes()))
        self.assertEqual(C.next_open("2019-01-10T14:15:00.000000001Z", cal, 15), "2019-01-11")
        self.assertEqual(C.next_open("2019-01-10T14:15:00Z", cal, 15), "2019-01-10")


if __name__ == "__main__":
    main()
