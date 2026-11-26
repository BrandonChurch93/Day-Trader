"""Synthetic Plan 47 unit and full command-line approval/validation/one-shot tests."""
from datetime import timedelta
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from research_rig import common_47 as c
from research_rig import score_47 as s

ROOT = Path(__file__).resolve().parents[1]
ACC = "0001111111-25-000007"
NOW = "2025-06-12T13:25:02Z"
NATIVE = b"synthetic native candle response\n"
DIGEST = s.digest(NATIVE)


def event(**edits):
    return {"cik": "0001111111", "accession": ACC, "coin": "XRP", "form": "8-K", "accepted_utc": NOW,
            "event_date": "2025-06-10", "public_when": "2025-06-12", "clock_basis": "public_date",
            "filing_url": f"https://www.sec.gov/Archives/edgar/data/1111111/{ACC.replace('-', '')}/example.htm",
            "clock_url": f"https://www.sec.gov/Archives/edgar/data/1111111/{ACC.replace('-', '')}/ex991.htm",
            "origin_key": "transaction-one", "venue": "coinbase", "market_url": "https://help.coinbase.com/listing",
            "coinbase_status": "listed", "coinbase_status_url": "https://help.coinbase.com/listing"} | edits


def roster(*rows):
    return dict(schema=1, status="REVIEWED", docket_sha256=DIGEST, review_sha256=DIGEST, events=list(rows))


def fixtures(cfg, rows, pin):
    scope = c.bar_keys(rows, cfg)
    start = min(t for _, _, t in scope)
    return {"schema": 1, "manifest_sha256": pin, "granularity_seconds": 60,
            "rows": [dict(venue=v, product=k, time=t, source_sha256=DIGEST, open="100" if t == start or
                     k == "BTC-USD" else "105", volume="5", state="observed") for v, k, t in sorted(scope)]}


def settings():
    return s.load((ROOT / s.CONFIG).read_bytes(), (ROOT / s.ENGINE).read_bytes())[1]


class Semantics(unittest.TestCase):
    def setUp(self):
        self.p = settings()

    def test_exact_clock_and_earliest_event(self):
        p = self.p
        self.assertEqual(c.u(c.earliest(c.stamp(NOW), p)), "2025-06-12T13:56:00Z")
        self.assertEqual(c.u(c.earliest(c.stamp("2025-06-12T13:25:00Z"), p)), "2025-06-12T13:55:00Z")
        self.assertEqual(len(c.events(roster(event()), p)), 1)
        with self.assertRaisesRegex(c.Incomplete, "STALE"):
            c.events(roster(event(clock_basis="8k_event_date", public_when="2025-06-10")), p)
        self.assertTrue(c.fresh(event(clock_basis="public_time", public_when="2025-06-11T13:25:02Z"), c.stamp(NOW), p))
        self.assertFalse(c.fresh(event(clock_basis="public_time", public_when="2025-06-11T13:25:01Z"), c.stamp(NOW), p))
        self.assertTrue(c.fresh(event(form="6-K", event_date=None, clock_basis="filing_only", public_when=None), c.stamp(NOW), p))
        self.assertTrue(c.fresh(event(clock_basis="filing_only", public_when=None), c.stamp(NOW), p))
        for when, day, valid in [("2025-06-13T03:59:59Z", "2025-06-12", True),
                                 ("2025-06-13T04:00:00Z", "2025-06-12", False),
                                 ("2025-12-13T04:59:59Z", "2025-12-12", True),
                                 ("2025-12-13T05:00:00Z", "2025-12-12", False)]:
            self.assertEqual(c.fresh(event(event_date=None, public_when=day), c.stamp(when), p), valid)

    def test_duplicate_campaign_and_precedence(self):
        with self.assertRaisesRegex(c.Incomplete, "DUPLICATE"):
            c.events(roster(event(), event()), self.p)
        with self.assertRaisesRegex(c.Incomplete, "VENUE"):
            c.events(roster(event(venue="kraken", market_url="https://support.kraken.com/listing")), self.p)
        with self.assertRaisesRegex(c.Incomplete, "^VENUE$"):
            c.events(roster(event(venue="kraken", coinbase_status="unlisted", market_url="https://support.kraken.com/listing",
                coinbase_status_url="https://x.com/CoinbaseMarkets/status/1981013406141551062")), self.p)
        with self.assertRaisesRegex(c.Incomplete, "VENUE_SOURCE"):
            c.events(roster(event(coinbase_status_url="https://x.com/CoinbaseMarkets/status/1981013406141551062")), self.p)
        for (cik, accession, coin, accepted), url in c.FIRST_OPENING.items():
            path = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}"
            x = event(cik=cik, accession=accession, coin=coin, accepted_utc=accepted, public_when=accepted[:10],
                      filing_url=f"{path}/{accession}-index.html", clock_url=f"{path}/ex991.htm")
            with self.assertRaisesRegex(c.Incomplete, "^VENUE$"):
                c.events(roster(x), self.p)
            kr = x | dict(venue="kraken", coinbase_status="unlisted", market_url=c.KRAKEN_LISTING[coin],
                          coinbase_status_url=url)
            self.assertEqual(c.events(roster(kr), self.p)[0][3], "kraken")
            with self.assertRaisesRegex(c.Incomplete, "VENUE_SOURCE"):
                c.events(roster(kr | {"coinbase_status_url": url + "?extra=1"}), self.p)
            with self.assertRaisesRegex(c.Incomplete, "VENUE_SOURCE"):
                c.events(roster(kr | {"accepted_utc": c.u(c.stamp(accepted) + timedelta(seconds=1))}), self.p)

    def test_exact_source_and_failures(self):
        p = self.p
        rows = c.events(roster(event()), p)
        want = c.bar_keys(rows, p)
        self.assertEqual(len(want), 8)
        pck = fixtures(p, rows, DIGEST)
        wrong = pck["rows"][0].copy()
        with self.assertRaisesRegex(c.Incomplete, "BAR_KEY"):
            c.validate(pck | {"rows": pck["rows"][:-1] + [wrong]}, want, DIGEST)
        with self.assertRaisesRegex(c.Incomplete, "BUNDLE"):
            c.validate(pck | {"rows": pck["rows"][:-1]}, want, DIGEST)
        with self.assertRaisesRegex(c.Incomplete, "BAR_STATE"):
            c.validate(pck | {"rows": [wrong | {"state": "api_timeout"}] + pck["rows"][1:]}, want, DIGEST)
        with self.assertRaisesRegex(c.Incomplete, "BAR_NUMBER"):
            c.validate(pck | {"rows": [wrong | {"volume": 0}] + pck["rows"][1:]}, want, DIGEST)
        for fields in ({"schema": True}, {"granularity_seconds": Decimal("60.0")}):
            with self.assertRaisesRegex(c.Incomplete, "BUNDLE"):
                c.validate(pck | fields, want, DIGEST)
        with self.assertRaisesRegex(c.Incomplete, "DOCKET"):
            c.events(roster(event()) | {"schema": True}, p)

    def test_documented_missing_one_hold(self):
        p = self.p
        rows = c.events(roster(event()), p)
        want = c.bar_keys(rows, p)
        pck = fixtures(p, rows, DIGEST)
        end = c.u(c.earliest(rows[0][0], p) + timedelta(hours=p["hold_h"]))
        for row in pck["rows"]:
            if row["product"] == "XRP-USD" and row["time"] == end:
                row.update(state="documented_missing", open=None, volume=None)
        out = c.evaluate(rows, c.validate(pck, want, DIGEST), p)
        self.assertEqual(out["windows"]["24"]["summary"]["n"], 0)
        self.assertEqual(out["windows"]["1"]["summary"]["n"], 1)
        self.assertEqual(out["refusals_by_hold"]["24"][0]["missing"], ["coin_exit"])

    def test_cluster_and_sensitivity(self):
        rows = [dict(cluster_day=d, coin=x, raw_net=.02 + y, excess=y) for (d,x,y) in
                [(1,"SOL",.03),(1,"SOL",.03),(2,"SOL",.01),(2,"XRP",.01)]]
        marks = c.judge(rows, self.p)
        self.assertEqual(marks["clusters"], 2)
        self.assertAlmostEqual(marks["excess_cluster_t"], 2.)
        self.assertEqual(marks["without_SOL"]["n"], 1)
        self.assertEqual(marks["without_best"]["excess_mean"], .01)
        with_cap = c.judge(rows + [dict(cluster_day=3, coin="SOL", raw_net=1, excess=1)], self.p)
        self.assertAlmostEqual(with_cap["coin_cap"]["excess_mean"], .02)
        self.assertLess(c.payoff(Decimal("1"), Decimal("1"), self.p, "kraken"),
                        c.payoff(Decimal("1"), Decimal("1"), self.p))
        self.assertLess(c.payoff(Decimal("1"), Decimal("1"), self.p, sensitivity=True),
                        c.payoff(Decimal("1"), Decimal("1"), self.p))
        self.assertEqual(c.payoff(Decimal("1"), Decimal("1"), self.p, "kraken", True),
                         c.payoff(Decimal("1"), Decimal("1"), self.p, "kraken"))

    def test_midnight_keeps_acceptance_cluster(self):
        p = self.p
        rows = c.events(roster(event(accepted_utc="2025-06-12T23:49:01Z")), p)
        packet = fixtures(p, rows, DIGEST)
        out = c.evaluate(rows, c.validate(packet, c.bar_keys(rows, p), DIGEST), p)
        trade = out["windows"]["24"]["trades"][0]
        self.assertEqual(trade["entry"], "2025-06-13T00:20:00Z")
        self.assertEqual(trade["cluster_day"], "2025-06-12")

    def test_exactly_constant_excess_cannot_pass(self):
        rows = [dict(cluster_day=i, coin="XRP", raw_net=.0023, excess=.0023) for i in range(30)]
        result = c.judge(rows, self.p)
        self.assertEqual(result["clusters"], 30)
        self.assertIsNone(result["excess_cluster_t"])
        self.assertTrue(result["marks"]["enough_events"])
        self.assertFalse(result["marks"]["excess_positive_cluster_t"])
        self.assertFalse(result["passes"])

    def test_exactly_balanced_nonconstant_clusters_cannot_pass(self):
        base = [1/64, 1/32, 1/16]
        for sizes in ([3] * 10, [3, 6, 9, 12]):
            rows = [dict(cluster_day=i, coin="XRP", raw_net=x, excess=x)
                    for i, size in enumerate(sizes) for x in base * (size // 3)]
            result = c.judge(rows, self.p)
            self.assertEqual(result["clusters"], len(sizes))
            self.assertIsNone(result["excess_cluster_t"])
            self.assertTrue(result["marks"]["enough_events"])
            self.assertFalse(result["passes"])


class ActualCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.repo, self.private = base / "repo", base / "private"
        self.repo.mkdir()
        self.private.mkdir(mode=0o700)
        self.inputs, self.run = self.private / "inputs", self.private / "score"
        self.inputs.mkdir(mode=0o700)
        self.native = self.inputs / "native"
        self.native.mkdir(mode=0o700)
        self.run.mkdir(mode=0o700)
        self.marker = base / "evaluate_called"
        self.git("init", "-q")
        for k, v in (("user.name", "Synthetic tester"), ("user.email", "synthetic@example.org"), ("commit.gpgsign", "false")):
            self.git("config", k, v)
        is_kraken = self._testMethodName == "test_cli_kraken"
        cfg = settings() | {"min_events": 1}
        e = event()
        if is_kraken:
            cik, acc, coin, time = ("0000744452", "0001104659-25-094465", "BNB", "2025-09-29T20:01:35Z")
            sec = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}"
            e = event(cik=cik, accession=acc, coin=coin, accepted_utc=time, event_date="2025-09-23",
                      public_when="2025-09-29", venue="kraken", coinbase_status="unlisted",
                      market_url="https://blog.kraken.com/product/pro/new-assets-and-pairs-available-for-margin-trading-bnb-avnt-and-stbl",
                      coinbase_status_url="https://x.com/CoinbaseMarkets/status/1981013406141551062",
                      filing_url=f"{sec}/{acc}-index.html",
                      clock_url="https://www.sec.gov/Archives/edgar/data/744452/000110465925095401/tm2527342d1_ex99-1.htm")
        if self._testMethodName == "test_cli_maturity_gate":
            e = event(accepted_utc="2099-06-12T13:25:02Z", event_date="2099-06-10", public_when="2099-06-12")
            cfg["last"] = "2099-12-31"
        if self._testMethodName == "test_cli_count_floor":
            cfg["min_events"] = 2
        docket_pin = (DIGEST if self._testMethodName == "test_cli_docket_binding" else
                      s.digest((ROOT / s.DOCKET).read_bytes()))
        test_manifest = roster(e) | {"docket_sha256": docket_pin}
        self.manifest_pin = self.put(self.inputs / "manifest.json", test_manifest, private=True)
        self.fixture = fixtures(cfg, c.events(test_manifest, cfg), self.manifest_pin)
        self.objects = {}
        for r in self.fixture["rows"]:
            product = r["product"]
            d = c.stamp(r["time"])
            ts = int(d.timestamp())
            x = int(r["open"])
            body = b"synthetic single official archive bytes" if is_kraken else s.enc([[ts, x, x, x, x, 5]])
            # Intentionally share literal responses where venue, product are established by distinct receipts.
            sha = s.digest(body)
            r["source_sha256"] = sha
            (self.native / sha).write_bytes(body)
            (self.native / sha).chmod(0o600)
            self.objects.setdefault(sha, {})[product] = ("https://support.kraken.com/synthetic-archive" if is_kraken else
                                                          f"https://api.exchange.coinbase.com/products/{product}/candles")
        self.bundle_pin = self.put(self.inputs / "bundle.json", self.fixture, private=True)
        for file in s.NAMES:
            p = self.repo / file
            p.parent.mkdir(exist_ok=True, parents=True)
            text = (ROOT / file).read_text()
            if file == s.PLAN:
                text = f"Status FROZEN.\nEVENT_MANIFEST_SHA256: {self.manifest_pin}\n"
            elif file == s.ENGINE:
                text += ("\n_evaluate = evaluate\ndef evaluate(*args):\n"
                         f"    open({str(self.marker)!r}, 'x').close()\n"
                         f"    if __import__('pathlib').Path({str(self.marker.with_suffix('.fail'))!r}).exists():\n"
                         "        raise ValueError('synthetic evaluate tripwire')\n    return _evaluate(*args)\n")
            elif file.endswith("score_47.py"):
                text = text.replace(str(s.PRIVATE), str(self.private))
                self.assertIn(str(self.private), text)
                self.assertNotIn(str(s.PRIVATE), text)
            elif file == s.CONFIG:
                before, after = text.split("replay_47_plan:\n  value: ", 1)
                _, rest = after.split("\n", 1)
                text = before + "replay_47_plan:\n  value: " + json.dumps(cfg) + "\n" + rest
            p.write_text(text)
        (self.repo / "docs").mkdir()
        for file, row in [("docs/QUEUE.md", 82), ("research_rig/TRIAL_LEDGER.md", 180)]:
            (self.repo / file).write_text(next(x for x in (ROOT / file).read_text().splitlines()
                                               if x.startswith(f"| {row} |")) + "\n")
        self.package = self.put(self.repo / s.PINS, {n:s.digest((self.repo / n).read_bytes()) for n in s.NAMES})
        self.git("add", ".")
        self.git("commit", "-qm", "frozen")
        self.freeze = self.git("rev-parse", "HEAD").strip()

    def put(self, path, obj, private=False):
        b = s.enc(obj)
        path.write_bytes(b)
        if private:
            os.chmod(path, 0o600)
        return s.digest(b)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True)

    def approve(self, extra=None, text=None):
        (self.repo / s.APPROVAL).write_text(text or ("Approved by the lead: plan 47, one custodian collection, "
            f"validation and one scored run, freeze commit {self.freeze}, freeze SHA-256 {self.package}, "
            f"event manifest SHA-256 {self.manifest_pin}.\n"))
        if extra:
            (self.repo / "unauthorized_extra").write_text("extra\n")
        self.git("add", ".")
        self.git("commit", "-qm", "approval")
        self.seal()

    def seal(self, **edits):
        self.bundle_pin = self.put(self.inputs / "bundle.json", self.fixture, private=True)
        native = {}
        for sha, urls in self.objects.items():
            rr = [[r["venue"], r["product"], r["time"], r["state"]] for r in self.fixture["rows"] if r["source_sha256"] == sha]
            note = {"keys": rr, "status": 200, "synthetic": True}
            h = s.digest(s.enc(note))
            self.put(self.native / (h + ".json"), note, private=True)
            native[sha] = {"receipt_sha256": h, "urls": urls}
        self.custody = {"schema": 1,
            "status": "INDEPENDENT_NATIVE_NO_RETURN_REVIEW_COMPLETE",
            "approval_commit": self.git("rev-parse", "HEAD").strip(), "manifest_sha256": self.manifest_pin,
            "bundle_sha256": self.bundle_pin, "objects": native,
            "keys": sorted([r["venue"], r["product"], r["time"], r["state"], r["source_sha256"]]
                           for r in self.fixture["rows"])} | edits
        self.custody_pin = self.put(self.inputs / "custody.json", self.custody, private=True)

    def cli(self, mode, pin=None, freeze=None, custody=None, extra_env=None):
        env = {"PATH": os.environ["PATH"], "LC_ALL": "C"} | (extra_env or {})
        args = ["python3", "-IB", "research_rig/score_47.py", mode, "--approval-commit", self.git("rev-parse", "HEAD").strip(),
                "--freeze-sha256", freeze or self.package]
        if mode != "--scope":
            args.extend(("--bundle-sha256", pin or self.bundle_pin, "--custody-sha256", custody or self.custody_pin))
        return subprocess.run(args, cwd=self.repo, env=env, capture_output=True, text=True, timeout=60)

    def test_cli_validation_no_return_score_and_lock(self):
        self.approve()
        sc = self.cli("--scope")
        self.assertEqual(sc.returncode, 0, sc.stderr)
        self.assertEqual(len(json.loads(sc.stdout)["want"]), 8)
        self.marker.with_suffix(".fail").touch()
        v = self.cli("--validate-inputs")
        self.assertEqual((v.returncode, v.stdout), (0,"P47_VALIDATED\n"), v.stderr)
        self.assertFalse(self.marker.exists())
        self.assertEqual(list(self.run.iterdir()), [])
        self.marker.with_suffix(".fail").unlink()
        go = self.cli("--go")
        self.assertEqual(go.returncode, 0, go.stderr)
        self.assertTrue(self.marker.exists())
        self.assertTrue((self.run / "score_47.lock").exists())
        outcome = json.loads((self.run / "results_47.json").read_bytes())["outcome"]["windows"]["24"]
        self.assertFalse(outcome["summary"]["passes"])
        trade = outcome["trades"][0]
        self.assertAlmostEqual(trade["raw_net"], .03436738530375411)
        self.assertAlmostEqual(trade["btc_net"], -.014888204472615133)
        self.assertAlmostEqual(trade["excess"], .04925558977636924)
        sealed = {f.name: s.digest(f.read_bytes()) for f in self.run.iterdir()}
        self.assertEqual(self.cli("--go").stderr,"P47_CONSUMED_OR_NOT_EMPTY\n")
        self.assertEqual({f.name: s.digest(f.read_bytes()) for f in self.run.iterdir()}, sealed)

    def test_cli_extra_or_invalid_approval(self):
        self.approve(extra=True)
        self.assertEqual(self.cli("--validate-inputs").stderr,"P47_APPROVAL\n")
        self.git("reset","--hard", self.freeze)
        self.approve(text="not an approval line\n")
        self.assertEqual(self.cli("--validate-inputs").stderr,"P47_APPROVAL\n")
        self.assertFalse(self.marker.exists())
        self.assertEqual(list(self.run.iterdir()), [])

    def test_cli_source_failure_no_lock(self):
        self.approve()
        b = self.fixture
        b["rows"][0].update(state="source_unavailable", open=None, volume=None)
        p = self.put(self.inputs / "bundle.json", b, private=True)
        self.assertEqual(self.cli("--validate-inputs", pin=p).stderr,"P47_REFUSED\n")
        self.assertEqual(self.cli("--go", pin=p).stderr,"P47_REFUSED\n")
        self.assertFalse(self.marker.exists())
        self.assertEqual(list(self.run.iterdir()), [])

    def test_cli_corrupt_native_and_postclaim_failure(self):
        self.approve()
        obj = self.native / self.fixture["rows"][0]["source_sha256"]
        before = obj.read_bytes()
        obj.write_bytes(b"corrupt\n")
        self.assertEqual(self.cli("--validate-inputs").stderr, "P47_NATIVE_HASH\n")
        self.assertEqual(list(self.run.iterdir()), [])
        obj.write_bytes(before)
        self.marker.with_suffix(".fail").touch()
        self.assertEqual(self.cli("--go").stderr, "P47_REFUSED\n")
        self.assertTrue(self.marker.exists())
        self.assertTrue((self.run / "score_47.lock").exists())
        self.assertFalse((self.run / "results_47.json").exists())
        self.assertEqual(self.cli("--go").stderr, "P47_CONSUMED_OR_NOT_EMPTY\n")

    def test_cli_binding_and_source_mapping(self):
        self.approve()
        nope = "0" * 64
        for opts, code in [({"freeze": nope}, "APPROVAL"), ({"pin": nope}, "DIGEST"),
                           ({"custody": nope}, "DIGEST"), ({"extra_env": {"TZ": "UTC"}}, "ENVIRONMENT")]:
            self.assertEqual(self.cli("--validate-inputs", **opts).stderr, f"P47_{code}\n")
        (self.repo / "dirty").touch()
        self.assertEqual(self.cli("--scope").stderr, "P47_APPROVAL\n")
        (self.repo / "dirty").unlink()
        fp = self.inputs / "manifest.json"
        fp.chmod(0o644)
        self.assertEqual(self.cli("--scope").stderr, "P47_PRIVATE\n")
        fp.chmod(0o600)
        native_receipt = self.native / (next(iter(self.custody["objects"].values()))["receipt_sha256"] + ".json")
        source_note = native_receipt.read_bytes()
        native_receipt.write_bytes(b"{}\n")
        self.assertEqual(self.cli("--validate-inputs").stderr, "P47_DIGEST\n")
        native_receipt.write_bytes(source_note)
        self.seal(keys=self.custody["keys"][:-1])
        self.assertEqual(self.cli("--validate-inputs").stderr, "P47_CUSTODY_COVERAGE\n")
        sha = self.fixture["rows"][0]["source_sha256"]
        self.objects[sha]["BTC-USD"] = "https://api.exchange.coinbase.com/products/XRP-USD/candles"
        self.seal()
        self.assertEqual(self.cli("--validate-inputs").stderr, "P47_CUSTODY_URL\n")
        self.assertFalse(self.marker.exists())
        self.assertEqual(list(self.run.iterdir()), [])

    def test_cli_wrong_event_pin(self):
        self.approve()
        manifest = (self.inputs / "manifest.json").read_bytes()
        (self.inputs / "manifest.json").write_bytes(manifest + b"\n")
        self.assertEqual(self.cli("--scope").stderr, "P47_DIGEST\n")

    def test_cli_count_floor(self):
        self.approve()
        for mode in ("--scope", "--validate-inputs", "--go"):
            result = self.cli(mode)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (2, "", "P47_COUNT_FLOOR\n"))
        self.assertFalse(self.marker.exists())
        self.assertEqual(list(self.run.iterdir()), [])

    def test_cli_maturity_gate(self):
        self.approve()
        for mode in ("--scope", "--validate-inputs"):
            result = self.cli(mode)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (2, "", "P47_SOURCE_NOT_YET_MATURE\n"))
        self.assertEqual(list(self.run.iterdir()), [])

    def test_cli_docket_binding(self):
        self.approve()
        self.assertEqual(self.cli("--scope").stderr, "P47_DOCKET_BINDING\n")

    def test_cli_documented_missing_consumes_only_affected_hold(self):
        self.approve()
        row = next(x for x in self.fixture["rows"] if x["product"] == "XRP-USD" and x["time"] == "2025-06-13T13:56:00Z")
        sha = row["source_sha256"]
        del self.objects[sha]
        body = s.enc([])
        sha = s.digest(body)
        row.update(state="documented_missing", open=None, volume=None, source_sha256=sha)
        (self.native / sha).write_bytes(body)
        (self.native / sha).chmod(0o600)
        self.objects[sha] = {"XRP-USD": "https://api.exchange.coinbase.com/products/XRP-USD/candles"}
        self.seal()
        self.assertEqual(self.cli("--validate-inputs").stdout, "P47_VALIDATED\n")
        go = self.cli("--go")
        self.assertEqual(go.returncode, 0, go.stderr)
        res = json.loads((self.run / "results_47.json").read_bytes())["outcome"]["windows"]
        self.assertEqual([res[x]["missing_candle_refusals"] for x in ("1","24","72")], [0,1,0])
        self.assertTrue(json.loads((self.run / "results_47.json").read_bytes())["outcome"]["descriptive_only_below_count"])

    def test_cli_kraken(self):
        self.approve()
        scope = self.cli("--scope")
        self.assertEqual(scope.returncode, 0, scope.stderr)
        self.assertEqual({(v, p) for v, p, _ in json.loads(scope.stdout)["want"]}, {("kraken", "BTC-USD"), ("kraken", "BNB-USD")})
        self.assertEqual(self.cli("--validate-inputs").stdout, "P47_VALIDATED\n")
        go = self.cli("--go")
        self.assertEqual(go.returncode, 0, go.stderr)
        outcome = json.loads((self.run / "results_47.json").read_bytes())["outcome"]
        trade = outcome["windows"]["24"]["trades"][0]
        self.assertEqual(trade["venue"], "kraken")
        self.assertAlmostEqual(trade["raw_net"], (105 / 100) * (.9985 * .992) / (1.0015 * 1.008) - 1)
        self.assertAlmostEqual(trade["raw_net"], outcome["coinbase_fee_sensitivity_shown_only"]["raw_mean"])


if __name__ == "__main__":
    unittest.main()
