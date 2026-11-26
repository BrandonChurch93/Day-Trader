"""Synthetic Plan 33 prices only; public calendar metadata can be tested offline."""
import contextlib
from datetime import date
from decimal import Decimal as D
from hashlib import sha256
from io import StringIO
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_33 as p

DAY = date(2026, 3, 11)
OTHER = date(2026, 3, 4)
ENTRY, EXIT = "2026-03-11T17:10:00Z", "2026-03-11T19:59:00Z"


def native(ts=ENTRY, bid=99, ask=100, bid_n=100, ask_n=100, cond=None):
    return {"t": ts, "bp": bid, "ap": ask, "bs": bid_n, "as": ask_n, "bx": "P", "ax": "P",
            "z": "B", "c": ["R"] if cond is None else cond}


def qt(ts=ENTRY, **kwargs):
    row = native(ts, **kwargs)
    return p.quote(row, DAY, p.timestamp(ts), 1)


def current_fees():
    return p.fees_table((p.HERE / "fees_33.csv").read_bytes())


class Inputs(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "native").mkdir(mode=0o700)
        self.i = 0

    def write(self, rel, blob):
        path = self.root / rel
        path.write_bytes(blob)
        path.chmod(0o600)
        return {"path": rel, "sha256": sha256(blob).hexdigest(), "bytes": len(blob)}

    def page(self, rows, nxt=None, incoming=None, kind="quotes", ticker="IEF", empty=None):
        self.i += 1
        obj = {kind: {ticker: rows} if empty is None else None, "next_page_token": nxt}
        return {"page_token": incoming, **self.write(f"native/{self.i}.json", p.encode(obj))}

    def series(self, pages, kind="quotes"):
        return p.series(self.root, pages, kind, DAY, "IEF", p.timestamp(ENTRY), set())

    def manifest(self, customize=lambda w: None):
        windows = []
        for d in [DAY, OTHER]:
            for c in p.CLOCKS:
                w = {"date": str(d), "symbol": "IEF", "clock": c, "quotes": [self.page([])],
                     "bars": [self.page([], kind="bars")]}
                customize(w)
                windows.append(w)
        m = {"schema": "plan33-alpaca-native-v1", "feed": "sip", "windows": windows}
        return self.write("manifest.json", p.encode(m))["sha256"]

    def test_empty_vendor_map_or_explicit_null(self):
        self.assertEqual(self.series([self.page([])]), [])
        self.assertEqual(self.series([self.page([], empty=True)]), [])
        self.assertIs(self.series([self.page([], kind="bars")], "bars"), False)

    def test_terminal_page_and_matching_tokens(self):
        one = self.page([native()], nxt="continue")
        two = self.page([native(ask=109)], incoming="continue")
        rows = self.series([one, two])
        self.assertEqual([q.ordinal for q in rows], [1, 2])
        self.assertEqual(p.select(rows, [qt(EXIT)])[0].ask, D(100))
        for pages in ([one], [one, {**two, "page_token": "different"}]):
            with self.subTest(pages=pages), self.assertRaises(p.Refused):
                self.series(pages)

    def test_duplicate_token_and_file(self):
        one = self.page([native()], nxt="a")
        two = self.page([native()], nxt="a", incoming="a")
        three = self.page([native()], incoming="a")
        with self.assertRaisesRegex(p.Refused, "PAGINATION"):
            self.series([one, two, three])
        with self.assertRaisesRegex(p.Refused, "PAGE"):
            self.series([one, {**one, "page_token": "a"}])

    def test_ns_inclusive_and_never_backward(self):
        at_end = native("2026-03-11T17:10:15.000000000Z")
        self.assertEqual(len(self.series([self.page([native(), at_end])])), 2)
        for rows in ([at_end, native()], [native("2026-03-11T17:10:15.000000001Z")],
                     [native("2026-03-11T17:09:59.999999999Z")]):
            with self.subTest(rows=rows), self.assertRaisesRegex(p.Refused, "NATIVE_CLOCK_OR_ORDER"):
                self.series([self.page(rows)])

    def test_extreme_offsets_and_dst(self):
        self.assertEqual(p.timestamp("2026-01-13T18:10:00Z"), p.clock_ns(date(2026, 1, 13), "13:10"))
        self.assertEqual(p.timestamp(ENTRY), p.clock_ns(DAY, "13:10"))
        self.assertEqual(p.timestamp(EXIT), p.clock_ns(DAY, "15:59"))
        self.assertEqual(p.timestamp(ENTRY) + 1, p.timestamp("2026-03-11T17:10:00.000000001Z"))

    def test_bad_bytes_and_symbol_not_empty(self):
        for kwargs in ({"ticker": "TLT"},):
            with self.assertRaisesRegex(p.Refused, "SYMBOL"):
                self.series([self.page([], **kwargs)])
        allowed = self.page([])
        (self.root / allowed["path"]).write_bytes(b'{"quotes": null}')
        with self.assertRaisesRegex(p.Refused, "SIZE|HASH"):
            self.series([allowed])
        for obj in (b'{"quotes":null}', b'{"quotes":null,"next_page_token":null,"x":[]}'):
            record = self.write("native/z.json", obj) | {"page_token": None}
            with self.assertRaisesRegex(p.Refused, "NATIVE"):
                self.series([record])

    def test_duplicate_json_and_numeric_strings(self):
        row = native(bid="99.0")
        with self.assertRaisesRegex(p.Refused, "NATIVE_NUMBER"):
            self.series([self.page([row])])
        blob = b'{"quotes":{},"quotes":{},"next_page_token":null}'
        rec = self.write("native/z.json", blob) | {"page_token": None}
        with self.assertRaisesRegex(p.Refused, "JSON_DUPLICATE"):
            self.series([rec])

    def test_invalid_late_row_refuses_full_window(self):
        later = native("2026-03-11T17:10:01Z")
        del later["as"]
        with self.assertRaisesRegex(p.Refused, "QUOTE_ROW"):
            self.series([self.page([native(), later])])

    def test_bar_labels_wont_accept_duplicate(self):
        b = {"t": ENTRY, "o": 1, "h": 2, "l": 1, "c": 2, "v": 2, "n": 2, "vw": 1.5}
        self.assertTrue(self.series([self.page([b], kind="bars")], "bars"))
        with self.assertRaisesRegex(p.Refused, "BAR_DUPLICATE"):
            self.series([self.page([b, b], kind="bars")], "bars")

    def test_empty_pair_coverage_not_data_error(self):
        pin = self.manifest()
        obs, errors = p.load_inputs(self.root, pin, [(DAY, OTHER, "IEF")])
        self.assertEqual(errors, [])
        self.assertEqual(len(obs), 2)
        self.assertEqual(p.coverage(list(obs.values()))["missing_exit"], 2)
        self.assertEqual(p.coverage(list(obs.values()))["missing_trade_bars"], 4)
        self.assertEqual(p.coverage(list(obs.values()))["placed"], 0)

    def test_absent_bar_does_not_block_fill(self):
        def update(w):
            if w["date"] == str(DAY):
                old = self.root / w["quotes"][0]["path"]
                old.unlink()
                w["quotes"] = [self.page([native(ENTRY if w["clock"] == "13:10" else EXIT)])]
        obs, errors = p.load_inputs(self.root, self.manifest(update), [(DAY, OTHER, "IEF")])
        self.assertEqual(errors, [])
        got = obs[DAY, "IEF"]
        self.assertEqual(got.bars, (False, False))
        self.assertTrue(got.placed)

    def test_collect_errors_across_all_cells(self):
        def update(w):
            if w["date"] == str(DAY):
                q = w["quotes"][0]
                self.write(q["path"], b"oops")
        obs, errors = p.load_inputs(self.root, self.manifest(update), [(DAY, OTHER, "IEF")])
        self.assertEqual(len(errors), 2)
        self.assertIn("13:10", errors[0])
        self.assertIn("15:59", errors[1])
        self.assertFalse((DAY, "IEF") in obs)

    def test_extra_native_and_private_files_refused(self):
        pin = self.manifest()
        self.write("native/unused.json", b"{}")
        with self.assertRaisesRegex(p.Refused, "EXTRA_NATIVE"):
            p.load_inputs(self.root, pin, [(DAY, OTHER, "IEF")])
        (self.root / "manifest.json").chmod(0o644)
        with self.assertRaisesRegex(p.Refused, "PRIVATE"):
            p.load_inputs(self.root, pin, [(DAY, OTHER, "IEF")])


class Rules(unittest.TestCase):
    def test_quote_filters_lock_and_all_shares(self):
        lane = [qt(bid=101), qt(cond=["R", "N"]), qt(ask_n=1), qt(ask=251),
                qt(bid=100, ask=100), qt(ask=90, bid=89)]
        out = [qt(EXIT, bid_n=1), qt(EXIT, bid=110, ask=111), qt(EXIT, bid=120, ask=121)]
        e, x, size = p.select(lane, out)
        self.assertEqual((e.bid, e.ask, x.bid, size), (D(100), D(100), D(110), 2))

    def test_size_scale_changes_only_at_boundary(self):
        row = native(bid_n=1, ask_n=1)
        old = p.quote(row, date(2025, 11, 2), 0, 1)
        new = p.quote(row, date(2025, 11, 3), 0, 1)
        self.assertEqual((old.az, new.az), (100, 1))

    def test_no_lookahead_to_resize_and_assessment(self):
        first = qt(ask=80, bid=79)
        second = qt(ask=100)
        e, x, q = p.select([first, second], [qt(EXIT, bid_n=2)])
        self.assertEqual((e, x, q), (first, None, 3))
        ob = p.Observation(DAY, "IEF", e, x, q, (True, True), (2, 1), True)
        self.assertEqual(ob.missing, ["exit"])
        self.assertEqual(p.Observation(DAY, "IEF", None, None, 0, (False, False), (0, 2), True).missing,
                         ["entry"])

    def test_cash_exact_boundary(self):
        self.assertEqual(p.entry_size(D(125)), 2)
        self.assertEqual(p.entry_size(D("125.00000000000000000000000000001")), 1)
        q = p.entry_size(D(".01"))
        self.assertLessEqual(q * D(".01") + p.cat(q), D(250))
        self.assertGreater((q+1) * D(".01") + p.cat(q+1), D(250))

    def test_rate_date_boundaries_and_customer_exemptions(self):
        table = current_fees()
        self.assertEqual(p.statutory(table, date(2025, 5, 13), D(1000), 100)[0], D(".0278"))
        self.assertEqual(p.statutory(table, date(2025, 5, 14), D(1000), 100)[0], 0)
        self.assertEqual(p.statutory(table, date(2026, 4, 4), D(1000), 100)[0], D(".0206"))
        self.assertEqual(p.statutory(table, date(2026, 9, 30), D(200), 2)[1], D(".000390"))
        self.assertEqual(p.statutory(table, date(2026, 10, 1), D(200), 2)[1], 0)
        self.assertEqual(p.retail(table, date(2026, 4, 4), D(500), 50), (0, 0, 0))
        self.assertEqual(p.retail(table, date(2026, 4, 4), D("500.01"), 51), (D(".02"), D(".01"), 0))
        self.assertEqual(p.cat(3334), D(".01"))

    def test_spread_not_double_charged_and_shown_fees(self):
        a, x = qt(), qt(EXIT, bid=101, ask=102)
        obs = p.Observation(DAY, "IEF", a, x, 2, (False, False), (1, 1), True)
        base = p.trade(obs, current_fees())
        self.assertEqual((base["net_bps"], base["idle_usd"], base["net_usd"]), (100, 50, 2))
        self.assertAlmostEqual(base["entry_half_spread_bps"], 10000 / 199)
        self.assertLess(p.trade(obs, current_fees(), slip=1)["net_bps"], 100)
        self.assertLess(p.trade(obs, current_fees(), unwaived=True)["net_bps"], 100)

    def test_undefined_t_and_cluster(self):
        self.assertIsNone(p.stats([])["t"])
        self.assertIsNone(p.stats([1, 1])["t"])
        self.assertEqual(p.clustered([(DAY, 1), (DAY, 3), (OTHER, 6)])["weeks"], 2)

    def test_paired_comparison_uses_only_complete_pairs(self):
        empty = p.Observation(OTHER, "IEF", None, None, 0, (False, False), (0, 0), False)
        placed = p.Observation(DAY, "IEF", qt(), qt(EXIT), 2, (False, False), (1, 1), True)
        obs = {(o.day, o.symbol): o for o in (empty, placed)}
        out = p.summary([(DAY, OTHER, "IEF")], obs, {k: p.trade(o, current_fees()) for k, o in obs.items()})
        self.assertEqual(out["auctions"]["net_bps"]["n"], 1)
        self.assertEqual(out["paired_diff_bps"]["n"], 0)
        self.assertEqual(len(out["pairs_incomplete"]), 1)

    def test_public_calendar_metadata_only(self):
        blobs = {n: (p.HERE / n).read_bytes() for n in p.PIN_NAMES
                 if n.endswith((".csv", ".txt"))}
        pairs = p.plan_dates(blobs)
        self.assertEqual(len(pairs), 260)
        self.assertIn((date(2024, 7, 11), date(2024, 5, 30), "TLT"), pairs)
        self.assertEqual(sum(p.regime(d) for d, _, _ in pairs), 54)
        fomc = p.dates(blobs["fomc_dates_33.txt"])
        self.assertEqual(sum(a in fomc or c in fomc for a,c,_ in pairs), 23)

    def test_full_marks_and_pair_denominator_on_invented_quotes(self):
        blobs = {n: (p.HERE / n).read_bytes() for n in p.PIN_NAMES
                 if n.endswith((".csv", ".txt"))}
        pairs = p.plan_dates(blobs)
        obs, fee, meetings = {}, p.fees_table(blobs["fees_33.csv"]), p.dates(blobs["fomc_dates_33.txt"])
        for i, (a, c, s) in enumerate(pairs):
            for d, sell in ((a, 101 + i % 3), (c, 99)):
                obs[d, s] = p.Observation(d, s, qt(), qt(EXIT, bid=sell, ask=sell+1), 2,
                                          (False, True), (1, 1), True)
        res = p.outcome({}, pairs, obs, fee, meetings)
        self.assertTrue(res["pass"])
        self.assertEqual(len(res["marks"]), 11)
        self.assertEqual(res["after_2024_07_31_paper_sample"]["auctions"]["coverage"]["placed"], 54)
        self.assertEqual(res["shown_only"]["exclude_either_fomc_statement_date"]["paired_diff_bps"]["n"], 237)
        for _, c, s in pairs[:14]:
            obs[c, s] = p.Observation(c, s, None, None, 0, (True, True), (0, 0), False)
        res = p.outcome({}, pairs, obs, fee, meetings)
        self.assertFalse(res["pass"])
        self.assertTrue(res["marks"]["placed_95_percent"])
        self.assertFalse(res["marks"]["pairs_95_percent"])
        self.assertEqual(res["overall"]["paired_diff_bps"]["n"], 246)


class Gate(unittest.TestCase):
    def test_bound_frozen_and_approval_bytes(self):
        approve, freeze, inputs = "a"*40, "b"*40, "c"*64
        blobs = {n: n.encode() for n in p.PIN_NAMES}
        blobs[p.PLAN] = b"script\nStatus FROZEN.\n"
        blobs[p.PINS] = p.encode({n: sha256(raw).hexdigest() for n, raw in blobs.items()})
        fp = sha256(blobs[p.PINS]).hexdigest()
        auth = f"Approved by the lead: plan 33, validation and one scored run, freeze commit {freeze}, freeze SHA-256 {fp}, input SHA-256 {inputs}.\n".encode()
        repo = {commit: {f"research_rig/{name}": raw for name, raw in blobs.items()}
                for commit in (approve, freeze)}
        repo[approve][f"research_rig/{p.APPROVAL}"] = auth
        repo[freeze]["docs/QUEUE.md"] = b"| 52 | Plan 33 | Ledger 168 |\n"
        repo[freeze]["research_rig/TRIAL_LEDGER.md"] = f"| 168 | time | `research_rig/{p.PLAN}` |\n".encode()

        def fake_git(*args, **kw):
            command, word = args[:2]
            if command == "show":
                c, f = word.split(":", 1)
                return SimpleNamespace(stdout=repo[c][f], returncode=0)
            if command == "cat-file" and word == "-e":
                return SimpleNamespace(returncode=1)
            out = {"rev-parse": approve.encode()+b"\n", "status": b"", "cat-file": b"commit\n", "merge-base": b""}
            return SimpleNamespace(stdout=out[command], returncode=0)

        with patch.object(p, "git", side_effect=fake_git), patch.object(
                p, "read_file", side_effect=lambda path, *a: auth if path.name == p.APPROVAL else blobs[path.name]):
            self.assertEqual(p.authorize(approve)[:3], (freeze, fp, inputs))
            repo[approve]["research_rig/fees_33.csv"] = b"changed rates"
            with self.assertRaisesRegex(p.Refused, "FREEZE"):
                p.authorize(approve)

    def test_exclusive_claim_starts_before_calculation_and_consumes_failure(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            def explode():
                self.assertTrue((root / "score_33.lock").exists())
                raise ValueError("synthetic score error")
            with self.assertRaises(ValueError):
                p.claim(root, {"fixture": 1}, explode)
            self.assertFalse((root / "results_33.json").exists())
            with self.assertRaisesRegex(p.Refused, "CONSUMED"):
                p.claim(root, {}, lambda: self.fail("spent"))

    def test_no_score_no_claim_validation_dispatch(self):
        o = p.Observation(DAY, "IEF", qt(), qt(EXIT), 2, (True, True), (1, 1), True)
        c = p.Observation(OTHER, "IEF", None, None, 0, (True, True), (0, 0), False)
        with contextlib.ExitStack() as ctx:
            for name, val in {"refusal_environment": None, "resources": None,
                              "authorize": ("f", "fp", "ip", {"fees_33.csv": b"", "fomc_dates_33.txt": b""}),
                              "plan_dates": [(DAY, OTHER, "IEF")], "fees_table": {}, "dates": set(),
                              "load_inputs": ({(DAY, "IEF"): o, (OTHER, "IEF"): c}, [])}.items():
                ctx.enter_context(patch.object(p, name, return_value=val))
            for name in ("claim", "outcome", "trade", "write_exclusive", "statutory"):
                ctx.enter_context(patch.object(p, name, side_effect=AssertionError(name)))
            ctx.enter_context(patch.object(sys, "argv", ["score_33.py", "--validate-inputs", "--approval-commit", "x"]))
            stdout = ctx.enter_context(contextlib.redirect_stdout(StringIO()))
            p.main()
            self.assertEqual(p.decode(stdout.getvalue().encode())["complete_pairs"], 0)

    def test_mismatched_head_refused(self):
        with patch.object(p, "git", return_value=SimpleNamespace(stdout=b"different\n")):
            with self.assertRaisesRegex(p.Refused, "APPROVAL"):
                p.authorize("a"*40)

    def test_env_override_refused(self):
        flags = SimpleNamespace(isolated=1, dont_write_bytecode=1, optimize=0)
        with patch.object(sys, "flags", flags), patch.dict(p.os.environ, {"P33_INPUTS": "/somewhere"}, clear=True):
            with self.assertRaisesRegex(p.Refused, "ENVIRONMENT"):
                p.refusal_environment()


if __name__ == "__main__":
    unittest.main()
