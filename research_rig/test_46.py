"""Invented inputs only; the CLI fixture is confined to a disposable Git repo."""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import common_46 as C
import score_46 as S


def cfg():
    return C.config(dict(entry_lag_days=2, a_min_hold_days=5, b_start_days=1, b_hold_days=7, min_events=3,
                         trim_dates=1, a_fee_bps=60, a_sensitivity_fee_bps=120, a_half_spread_bps=12,
                         b_fee_bps=12, b_half_spread_bps=10,
                         b_funding_bps_per_day=3, spot_btc_half_spread_bps=2, perp_btc_half_spread_bps=2,
                         source="coinbase_exchange_utc_daily", queue=83, ledger={"A": 179, "B": 181},
                         min_dates={"A": 2, "B": 2}, min_t=Decimal("2.0"), rows=3,
                         first_post="2025-01-01", asof="2025-02-01"))


def details():
    return [dict(post=f"2025-01-{p:02d}", launch=f"2025-01-{l:02d}", coin="ZZZ", venue=v,
                 detail=f"https://www.cftc.gov/IndustryOversight/IndustryFilings/TradingOrganizationProducts/{p}",
                 filing=f"https://www.cftc.gov/filings/ptc/f{p}.pdf")
            for p, l, v in [(1, 8, "CME"), (2, 8, "COIN"), (16, 16, "CDNA")]]


def fixture_packet(path, docket, config, *, profile="complete"):
    planned, _ = C.planned(C.docket(details(), config), config)
    world = C.required(planned)
    source = config["source"]
    docket_pin = sha256(docket).hexdigest()
    file_pins, native_pins, receipt = {}, {}, {}
    asof = max(max(days) for days in world.values())
    start_clock = asof + timedelta(days=1)
    collected = f"{start_clock}T00:00:00Z"

    def put(name, obj):
        file = path / name
        body = S.encode(obj)
        file.write_bytes(body)
        file.chmod(0o600)
        return sha256(body).hexdigest()

    for coin, days in world.items():
        name = coin + "-USD"
        missing_here = profile in {"gaps", "unresolved"} and coin == "ZZZ"
        no_tick = {min(days)} if missing_here else set()
        listed_late = {min(days) + timedelta(days=1)} if missing_here else set()
        absent = no_tick | listed_late
        fields = [9, 13, 10, 12, 4]
        file_pins[name + ".json"] = put(name + ".json", {str(d): None if d in absent else fields for d in days})
        native_body = [[int(datetime.combine(d, time(), timezone.utc).timestamp()), *fields]
                       for d in sorted(days - absent)]
        start, end = str(min(days)), str(max(days) + timedelta(days=1))
        req = dict(start=start, end=end, retrieved_utc=end + "T00:00:00Z", status=200, body=native_body)
        extra = req | {"start": str(min(days) - timedelta(days=1))}
        if coin == "ZZZ" and profile in {"mismatch", "conflict"}:
            changed = [list(row) for row in native_body]
            changed[0][4] += 1
            if profile == "mismatch":
                req = req | {"body": changed}
            else:
                extra = extra | {"body": changed}
        requests = [req, extra] if (missing_here and profile == "gaps") or profile == "conflict" else [req]
        native_name = name + ".native.json"
        notice = {str(d): dict(url="https://www.coinbase.com/blog/fixture",
                               excerpt="Synthetic date-specific evidence of a product not yet listed.")
                  for d in listed_late}
        native_pins[native_name] = put(native_name, dict(product=name, requests=requests, not_listed=notice))
        receipt[name + ".json"] = dict(normalized_sha256=file_pins[name + ".json"], native_sha256=native_pins[native_name],
                                       missing=({str(d): "absent_from_confirmed_responses" for d in no_tick}
                                                | {str(d): "official_not_listed" for d in listed_late}))
    receipt_pin = put("source_reconciliation.json", dict(schema=1, source=source, docket_sha256=docket_pin,
                      review="independent_exact_native_grid_and_gap_check", reviewed_utc=collected, files=receipt))
    early = f"{asof}T23:59:59Z"
    manifest = dict(schema=2, source=source, docket_sha256=docket_pin,
                    collected_utc=early if profile == "early" else collected, files=file_pins,
                    native_files=native_pins, reconciliation_sha256=receipt_pin)
    return put("manifest.json", manifest), manifest


class Calendar(unittest.TestCase):
    def test_calendar_and_overlap(self):
        rows = C.docket(details(), cfg())
        holds, skips = C.planned(rows, cfg())
        self.assertEqual([len(holds[k]) for k in C.LEGS], [1, 2])
        self.assertEqual(skips, {"A": {"short_notice": 2}, "B": {"same_coin_overlap": 1}})
        a_start, a_stop = holds["A"][0][0], holds["A"][0][4]
        self.assertEqual(C.endpoints("A", a_start, a_stop), (date(2025, 1, 3), date(2025, 1, 7), "close"))
        self.assertEqual(C.endpoints("B", holds["B"][0][0], holds["B"][0][4]),
                         (date(2025, 1, 9), date(2025, 1, 16), "open"))
        self.assertEqual(sum(map(len, C.required(holds).values())), 42)
        self.assertTrue(holds["B"][0][-2])
        self.assertEqual(holds["B"][1][0], date(2025, 1, 18))

    def test_launch_before_archive_and_unknown(self):
        rows = details()
        rows[0]["launch"] = None
        rows[2]["launch"] = "2025-01-12"
        holds, skips = C.planned(C.docket(rows, cfg()), cfg())
        self.assertEqual(holds["A"], [])
        self.assertEqual(skips["B"], {"unknown_trade_date": 1})
        self.assertEqual(holds["B"][1][0], date(2025, 1, 18))
        self.assertFalse(holds["B"][0][-2])

    def test_reject_bad_urls_dates_and_duplicate(self):
        for key, value in (("filing", "https://notcftc.gov/a.pdf"), ("post", "2025-1-01"), ("coin", "BTC")):
            rows = details()
            rows[0][key] = value
            with self.assertRaises(C.Refused):
                C.docket(rows, cfg())
        with self.assertRaisesRegex(C.Refused, "DOCKET_DUPLICATE"):
            C.docket([details()[0]] * 3, cfg())


class Math(unittest.TestCase):
    def test_both_cost_directions(self):
        c = cfg()
        self.assertGreater(C.return_net("A", 100, 110, 5, c), 0)
        self.assertGreater(C.return_net("B", 100, 90, 7, c), 0)
        self.assertLess(C.return_net("A", 100, 100, 5, c), 0)
        self.assertAlmostEqual(C.return_net("B", 100, 100, 7, c), -0.0065)
        self.assertGreater(C.return_net("B", 100, 100, 7, c, btc=True), -0.0065)

    def test_cluster_math_and_no_first_only_mark(self):
        s = C.clustered([("x", 1), ("x", 1), ("y", 3)])
        self.assertAlmostEqual(s["mean"], 5 / 3)
        self.assertAlmostEqual(s["clustered_se"], 8 / 9)
        self.assertAlmostEqual(s["t"], 15 / 8)
        rows = [dict(post=str(i), net=x, paired=x, first_in_docket=i == 0)
                for i, x in enumerate((-1, 2, 3, 100))]
        scored = C.assess(rows, cfg(), "A")
        self.assertEqual(scored["removed_posting_dates"], ["3"])
        self.assertAlmostEqual(scored["trimmed"]["mean"], 4 / 3)
        self.assertEqual(scored["shown_only_first_in_docket"]["paired"]["mean"], -1)
        self.assertNotIn("first_in_docket", scored["marks"])
        self.assertIsNone(C.clustered([("x", 1), ("y", 1)])["t"])
        self.assertIsNone(C.clustered([("x", .1), ("y", .1), ("y", .1)])["t"])
        near = C.clustered([("x", 1e-17), ("y", 2e-17), ("z", 3e-17)])
        self.assertGreater(near["t"], 0)
        self.assertLess(near["clustered_se"], 1e-15)


class Guard(unittest.TestCase):
    def test_full_synthetic_git_approval_validate_and_dispatch(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            packet, run = root / S.INPUTS.name, root / S.RUN.name
            for p in (packet, run):
                p.mkdir(mode=0o700)

            def put(relative, raw):
                path = repo / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)

            def git(*args):
                return subprocess.check_output(["/usr/bin/git", "-C", str(repo), "-c", "user.name=Fixture",
                                                "-c", "user.email=fixture@example.invalid", *args],
                                               env={"PATH": "/usr/bin:/bin", "LC_ALL": "C",
                                                    "GIT_CONFIG_NOSYSTEM": "1",
                                                    "GIT_CONFIG_GLOBAL": "/dev/null"}).decode().strip()

            git("init", "-q")
            real_cfg = S.read_config((S.REPO / S.CONFIG).read_bytes())
            conf = real_cfg | {"min_t": 2, "first_post": cfg()["first_post"], "asof": cfg()["asof"], "rows": 3}
            docket = S.encode(details())
            scorer = "research_rig/score_46.py"
            source = Path(S.__file__).read_bytes()
            real_data_literal = f'DATA = Path("{S.DATA}")'.encode()
            synthetic_data_literal = f'DATA = Path("{root}")'.encode()
            self.assertEqual(source.count(real_data_literal), 1)
            synthetic = source.replace(real_data_literal, synthetic_data_literal, 1)
            self.assertNotIn(str(S.DATA).encode(), synthetic)
            for real, mocked in ((S.INPUTS, packet), (S.RUN / "score_46.lock", run / "score_46.lock"),
                                 (S.RUN / "results_46.json", run / "results_46.json")):
                self.assertNotEqual(real, mocked.resolve())
                self.assertTrue(mocked.resolve().is_relative_to(root))
            engine = Path(C.__file__).read_bytes() + (
                f"\nfrom pathlib import Path as FixturePath\n"
                f"fixture_return_net = return_net\n"
                f"def return_net(*args, **kwargs):\n"
                f"    assert FixturePath({str(run / 'score_46.lock')!r}).is_file()\n"
                f"    if FixturePath({str(root / 'fail_after_claim')!r}).is_file():\n"
                f"        raise RuntimeError('synthetic post-claim failure')\n"
                f"    return fixture_return_net(*args, **kwargs)\n"
            ).encode()
            for key in S.PIN_NAMES:
                put(key, {S.PLAN: b"Status FROZEN.\n", S.ENGINE: engine,
                          S.DOCKET: docket, scorer: synthetic,
                          S.CONFIG: b"replay_46_plan:\n  value: " + json.dumps(conf).encode() + b"\n"
                          }.get(key, b"synthetic fixture\n"))
            pins = S.encode({key: sha256((repo / key).read_bytes()).hexdigest() for key in S.PIN_NAMES})
            put(S.PINS, pins)
            for tracker, ids in (("research_rig/TRIAL_LEDGER.md", (179, 181)), ("docs/QUEUE.md", (83,))):
                exact_rows = [line for line in (S.REPO / tracker).read_bytes().splitlines()
                              if any(line.startswith(f"| {i} |".encode()) for i in ids)]
                self.assertEqual(len(exact_rows), len(ids))
                put(tracker, b"\n".join(exact_rows) + b"\n")
            git("add", ".")
            git("commit", "-qm", "freeze")
            freeze = git("rev-parse", "HEAD")
            fp = sha256(pins).hexdigest()
            def prepare(profile):
                git("checkout", "--detach", "-q", freeze)
                ip, _ = fixture_packet(packet, docket, conf, profile=profile)
                put(S.APPROVAL, (f"Approved by the lead agent for plan 46 legs A and B, validation and one scored run, "
                                 f"freeze commit {freeze}, freeze SHA-256 {fp}, input SHA-256 {ip}.\n").encode())
                git("add", S.APPROVAL)
                git("commit", "-qm", "approval")
                return git("rev-parse", "HEAD"), ip

            def cli(mode, approval_hash, packet_hash):
                return subprocess.run(
                    ["/usr/bin/python3", "-IB", str(repo / scorer), mode,
                     "--approval-commit", approval_hash, "--freeze-sha256", fp, "--input-sha256", packet_hash],
                    cwd=repo, env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
                    capture_output=True, text=True, timeout=120,
                )
            approval, ip = prepare("complete")
            for bad in (cli("--go", "0" * 40, ip), cli("--go", approval, "0" * 64)):
                self.assertEqual((bad.returncode, bad.stdout, bad.stderr), (2, "", "P46_APPROVAL\n"))
            valid = cli("--validate-inputs", approval, ip)
            self.assertEqual((valid.returncode, valid.stderr), (0, ""))
            self.assertEqual(valid.stdout, "P46_INPUTS_OK symbols 2 A planned 1 placed 1 posting_dates 1 "
                             "B planned 2 placed 2 posting_dates 2\n")
            self.assertEqual(list(run.iterdir()), [])
            tape = packet / "ZZZ-USD.json"
            backup = tape.read_bytes()
            tape.write_bytes(b"FIXTURE_SENSITIVE")
            corrupt = cli("--go", approval, ip)
            self.assertEqual((corrupt.returncode, corrupt.stdout, corrupt.stderr), (2, "", "P46_PIN\n"))
            self.assertEqual(list(run.iterdir()), [])
            tape.write_bytes(backup)
            self.assertEqual(sha256(tape.read_bytes()).hexdigest(), sha256(backup).hexdigest())
            scored = cli("--go", approval, ip)
            self.assertEqual((scored.returncode, scored.stdout, scored.stderr), (0, "P46_RESULT_WRITTEN\n", ""))
            result = json.loads((run / "results_46.json").read_bytes())
            lock = json.loads((run / "score_46.lock").read_bytes())
            self.assertEqual(lock, result["job"])
            self.assertEqual(lock["freeze_commit"], freeze)
            a = result["legs"]["A"]
            b = result["legs"]["B"]
            self.assertAlmostEqual(a["net"]["mean"], (11.97 - 10.025 - .006 * (11.97 + 10.025)) / 10)
            self.assertAlmostEqual(b["net"]["mean"], -.0075)
            self.assertAlmostEqual(b["paired"]["mean"], -.0026)
            self.assertEqual(result["legs"]["B"]["paired"]["n"], 2)
            self.assertEqual(result["legs"]["A"]["shown_only_fee_sensitivity"]["fee_bps_per_side"], 120)
            snapshot = {p.name: sha256(p.read_bytes()).hexdigest() for p in run.iterdir()}
            used = cli("--go", approval, ip)
            self.assertEqual((used.returncode, used.stdout, used.stderr), (2, "", "P46_CONSUMED_OR_NOT_EMPTY\n"))
            self.assertEqual({p.name: sha256(p.read_bytes()).hexdigest() for p in run.iterdir()}, snapshot)
            run.rename(root / "completed_synthetic_case")
            run.mkdir(mode=0o700)
            for profile, code in (("unresolved", "SOURCE_UNRESOLVED"), ("early", "MANIFEST_CLOCK"),
                                  ("mismatch", "SOURCE_MISMATCH"), ("conflict", "SOURCE_CONFLICT")):
                rejected = cli("--go", *prepare(profile))
                self.assertEqual((rejected.returncode, rejected.stdout, rejected.stderr), (2, "", f"P46_{code}\n"))
                self.assertEqual(list(run.iterdir()), [])
            gap_ok = cli("--validate-inputs", *prepare("gaps"))
            self.assertEqual((gap_ok.returncode, gap_ok.stderr), (0, ""))
            self.assertIn("A planned 1 placed 0 posting_dates 0 B planned 2 placed 2 posting_dates 2", gap_ok.stdout)
            self.assertEqual(list(run.iterdir()), [])
            (root / "fail_after_claim").touch()
            approval, ip = prepare("complete")
            failed = cli("--go", approval, ip)
            self.assertEqual((failed.returncode, failed.stdout, failed.stderr), (2, "", "P46_REFUSED\n"))
            self.assertEqual({p.name for p in run.iterdir()}, {"score_46.lock"})
            claim = (run / "score_46.lock").read_bytes()
            duplicate = cli("--go", approval, ip)
            self.assertEqual((duplicate.returncode, duplicate.stdout, duplicate.stderr),
                             (2, "", "P46_CONSUMED_OR_NOT_EMPTY\n"))
            self.assertEqual((run / "score_46.lock").read_bytes(), claim)

    def test_validation_no_return_and_malformed_tape(self):
        config = cfg()
        docket = json.dumps(details()).encode()
        with TemporaryDirectory() as root:
            path = Path(root)
            path.chmod(0o700)
            pin, manifest = fixture_packet(path, docket, config)
            m = path / "manifest.json"
            with patch.object(C, "return_net", side_effect=AssertionError("pre-lock return")):
                _, stats = S.load_inputs(path, pin, C, docket, config)
            self.assertEqual(len(stats["A"][0]), 1)
            with self.assertRaisesRegex(S.Refused, "PIN"):
                S.load_inputs(path, "0" * 64, C, docket, config)
            extra = path / "unexpected.json"
            extra.touch()
            with self.assertRaisesRegex(S.Refused, "MANIFEST_FILES"):
                S.load_inputs(path, pin, C, docket, config)
            extra.unlink()
            tape = path / "ZZZ-USD.json"
            tape.chmod(0o644)
            with self.assertRaisesRegex(S.Refused, "PRIVATE"):
                S.load_inputs(path, pin, C, docket, config)
            tape.unlink()
            with self.assertRaisesRegex(S.Refused, "MANIFEST_FILES"):
                S.load_inputs(path, pin, C, docket, config)
            bad = S.encode(manifest | {"collected_utc": "2025-01-25T23:59:59Z"})
            m.write_bytes(bad)
            with self.assertRaisesRegex(S.Refused, "MANIFEST_CLOCK"):
                S.load_inputs(path, sha256(bad).hexdigest(), C, docket, config)
            pin, _ = fixture_packet(path, docket, config, profile="gaps")
            _, stats = S.load_inputs(path, pin, C, docket, config)
            self.assertEqual(stats["A"][1], {"coin_gap": 1})
        d = date(2025, 1, 1)
        self.assertEqual(C.candle_tape({str(d): None}, {d}), {})
        with self.assertRaisesRegex(C.Refused, "RANGE"):
            C.candle_tape({str(d): [9, 11, 10, 12, 4]}, {d})
        with self.assertRaisesRegex(C.Refused, "GRID"):
            C.candle_tape({}, {d})

    def test_native_responses_conflict_and_missing_evidence(self):
        day = date(2025, 1, 25)
        when = datetime(2025, 1, 26, tzinfo=timezone.utc)
        ts = int((when - timedelta(days=1)).timestamp())
        req = dict(start="2025-01-25", end="2025-01-26", retrieved_utc="2025-01-26T00:00:00Z",
                   status=200, body=[])
        raw = dict(product="ZZZ-USD", requests=[req], not_listed={})
        normal = {str(day): None}
        with self.assertRaisesRegex(S.Refused, "SOURCE_UNRESOLVED"):
            S.justify_native(raw, normal, {day}, when, "ZZZ-USD", C)
        a = req | {"body": [[ts, 9, 13, 10, 11, 4]]}
        b = req | {"start": "2025-01-24", "body": [[ts, 9, 13, 10, 12, 4]]}
        with self.assertRaisesRegex(S.Refused, "SOURCE_CONFLICT"):
            S.justify_native(raw | {"requests": [a, b]}, normal, {day}, when, "ZZZ-USD", C)
        with self.assertRaisesRegex(S.Refused, "SOURCE_MISMATCH"):
            S.justify_native(raw | {"requests": [a, req | {"start": "2025-01-24"}]},
                             {str(day): [9, 13, 10, 11, 4]}, {day}, when, "ZZZ-USD", C)
        documented = {str(day): dict(url="https://www.coinbase.com/blog/fixture",
                                     excerpt="This is a synthetic dated not-listed statement.")}
        self.assertEqual(S.justify_native(raw | {"requests": [], "not_listed": documented},
                                          normal, {day}, when, "ZZZ-USD", C),
                         {str(day): "official_not_listed"})

    def test_lock_claim_precedes_eval_and_failure_consumes(self):
        with TemporaryDirectory() as root:
            path = Path(root)
            path.chmod(0o700)
            def failed():
                self.assertTrue((path / "score_46.lock").exists())
                raise ValueError
            with self.assertRaises(ValueError):
                S.once(path, {}, (), failed)
            self.assertFalse((path / "results_46.json").exists())
            with self.assertRaisesRegex(S.Refused, "CONSUMED"):
                S.once(path, {}, (), lambda: {})
        with TemporaryDirectory() as root:
            path = Path(root)
            path.chmod(0o700)
            S.once(path, {"testing": True}, (), lambda: {"legs": {}})
            self.assertEqual(set(p.name for p in path.iterdir()), {"score_46.lock", "results_46.json"})
