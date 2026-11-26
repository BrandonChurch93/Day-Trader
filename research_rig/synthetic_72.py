"""Offline made-up Plan 72 data, never actual credentials, API, or custody."""
import copy
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

import coinbase_72 as feed
import model_72 as model
import plan_72 as runner
import sweep_70 as old

BASE = old.HERE.parent
CFG = json.loads((BASE / runner.CONFIG).read_bytes())
FEES = old.parse_config(*( (BASE / path).read_bytes() for path in (old.COVERAGE_PATH,old.SETTINGS_PATH,old.GRID_PATH) ))
ALL = [*json.loads((BASE / old.GRID_PATH).read_bytes()), *json.loads((BASE / runner.p71.GRID_PATH).read_bytes())]
SPECS = {row["id"]: row for row in ALL if row["id"] in (model.PRIMARY, *model.SHOWN)}
H, M, D = feed.HOUR, feed.MINUTE, model.DAY


def candle(x, hi=None, lo=None):
    return (x, hi if hi is not None else x, lo if lo is not None else x, x, 2.)


class Tests(unittest.TestCase):
    def test_dates_endpoint_and_timestamp_fence(self):
        t = feed.DIAG[1] - H
        job = ("BTC", H, t, t + H)
        ok = f'[[{t-H}, BAD, FORBIDDEN],[{t},1,3,2,2,5],[{t+H},NEVER,DECODE]]'.encode()
        self.assertEqual(feed.parse(ok, job, "windows"), {t: (2, 3, 1, 2, 5)})
        with self.assertRaises(ValueError):
            feed.validate(("BTC", M, t, feed.DIAG[1] + M), "windows")
        with self.assertRaises(ValueError):
            feed.validate(job, "hourly")
        with self.assertRaises(ValueError):
            feed.validate(("NOTALLOWED", M, t, t + M), "windows")
        with self.assertRaises(ValueError):
            feed.parse(f'[[{t},1,3,2,2,5],[{t},1,3,2,2,5]]'.encode(), job, "windows")
        with self.assertRaises(ValueError):
            feed.parse(f'[[{t},1,3,2,2,-1]]'.encode(), job, "windows")
        client = feed.Client(.55)
        with patch.object(client.opener, "open") as transport:
            response = transport.return_value.__enter__.return_value
            response.status = 200
            response.headers.get_content_type.return_value = "application/json"
            response.read.return_value = b"[]"
            self.assertEqual(client.get(job, "windows"), b"[]")
            u = transport.call_args.args[0].full_url
            self.assertTrue(u.startswith(feed.URL + "/products/BTC-USD/candles?"))
            self.assertIn("end=2023-12-31T23%3A59%3A59Z", u)
            self.assertNotIn("2024", u)

    def test_collection_seals_raw_bytes_and_refuses_block_and_edit(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "plan72"
            a = feed.FRESH[0]
            jobs = [("BTC", H, a, a+H), ("BTC", H, a+H, a+2*H)]
            raw = f"[[{a}, 1, 3, 2, 2, 5]]\n".encode()
            with patch.object(feed.Client, "get", side_effect=[raw, PermissionError("simulated block")]) as get:
                with self.assertRaises(PermissionError):
                    feed.collect(root, "hourly", jobs, {"bind": True}, .55)
                self.assertEqual(get.call_count, 2)
                with self.assertRaises(FileExistsError):
                    feed.collect(root, "hourly", jobs, {"bind": True}, .55)
                self.assertEqual(get.call_count, 2)
            self.assertFalse((root / "hourly_manifest.json").exists())
            self.assertEqual((root / feed.path_for(jobs[0], "hourly")).read_bytes(), raw)
            root = Path(temp) / "complete"
            with patch.object(feed.Client, "get", return_value=raw):
                out = feed.collect(root, "hourly", jobs[:1], {}, .55)
            path = root / feed.path_for(jobs[0], "hourly")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(feed.load(root, "hourly", out["manifest_sha256"], jobs[:1], {})["BTC", H][a][0], 2)
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                feed.load(root, "hourly", out["manifest_sha256"], jobs[:1], {})
            path.chmod(0o600)
            path.write_bytes(raw + b" ")
            with self.assertRaisesRegex(ValueError, "changed pinned input"):
                feed.load(root, "hourly", out["manifest_sha256"], jobs[:1], {})

    def test_first_full_day_and_count_ignores_open_price(self):
        a = feed.FRESH[0]
        bars = {("BTC", H): {a+i*H: candle(100) for i in range(48)},
                ("ETH", H): {a+i*H: candle(100) for i in range(1, 48)},
                ("LTC", H): {a+i*H: candle(100) for i in range(48)}}
        cut = a + 33 * H
        for coin, drop in (("BTC", .02), ("ETH", .06), ("LTC", .06)):
            bars[coin, H][cut-H] = candle(100*np.exp(-drop))
        cfg = {**CFG, "sources": dict.fromkeys(["BTC", "ETH", "LTC"], "2017-01-01")}
        hours, first = model.activated(bars, cfg)
        self.assertEqual(first, {"BTC": a, "ETH": a+D, "LTC": a})
        plan = model.schedule(hours, SPECS)
        self.assertEqual(plan[model.PRIMARY], [["ETH", cut, cut+2*H]])
        for coin in hours:
            for stamp, bar in list(hours[coin].items()):
                hours[coin][stamp] = (11., *bar[1:])
        self.assertEqual(model.schedule(hours, SPECS), plan)
        self.assertEqual(model.count_fields(plan[model.PRIMARY]), {
            "coins": ["ETH"], "days": 1, "tickets": 1, "tickets_per_year": {"2017": 1, "2018": 0, "2019": 0}})
        self.assertTrue(all(k not in model.count_fields(plan[model.PRIMARY]) for k in ("returns", "t")))
        with patch.object(old, "maintenance", side_effect=lambda t: t == cut + H):
            self.assertEqual(model.schedule(hours, SPECS)[model.PRIMARY], [])

    def test_count_creates_only_non_economic_plan(self):
        t = feed.FRESH[0] + 10*H
        fresh = {model.PRIMARY: [["ETH", t, t+2*H]], **{k: [] for k in model.SHOWN}}
        args = SimpleNamespace(freeze_commit="a"*40, config_sha256="b"*64, settings_sha256="c"*64,
                               grid_sha256="d"*64, grid71_sha256="e"*64, hourly_manifest_sha256="f"*64)
        starts = {coin: model.stamp(d) for coin, d in CFG["sources"].items()}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "private"
            feed.ensure_dir(root)
            with (patch.object(runner, "load_hourly", return_value={}),
                  patch.object(model, "activated", return_value=({}, starts)),
                  patch.object(model, "schedule", return_value=fresh),
                  patch.object(runner, "prior_summary", return_value=([], .02)),
                  patch.object(runner, "old_tickets", return_value=[]) as prior,
                  patch.object(feed, "collect", side_effect=AssertionError("network forbidden")),
                  patch.object(model, "ticket_value", side_effect=AssertionError("payoff forbidden")),
                  patch.object(model, "hourly_reference", side_effect=AssertionError("reference forbidden"))):
                self.assertEqual(runner.build_plan(root, root, args, CFG, [], SPECS),
                                 model.count_fields(fresh[model.PRIMARY]))
                self.assertEqual(sorted(os.listdir(root)), [runner.PLAN])
                self.assertEqual(prior.call_args.kwargs, {"economics": False})
                raw = (root / runner.PLAN).read_bytes()
                args.plan_sha256 = runner.p70.digest(raw)
                plan, jobs, pinned = runner.read_plan(root, args, CFG, SPECS)
                self.assertEqual(pinned, raw)
                self.assertEqual(plan["request_count"], len(jobs))
                self.assertEqual(plan["request_count"], plan["minute_requests"])
                self.assertNotIn(b"plain_mean", raw)

    def test_comparator_fallback_late_entry_worst_hedge_and_diagnostic(self):
        a = feed.FRESH[0] + 10*H
        q = a + 2*H
        primary = ["ETH", a, q]
        rough_mid = 104/100-1
        fee = (FEES["futures_round_trip_bp"]["ETH"] + 2*FEES["funding_adverse_bp_per_hour"])/10000
        hourly = {"ETH": {a: candle(100), a+H: candle(103), q: candle(106),
                          a+D: candle(100), a+D+H: candle(100), q+D: candle(102)}}
        ref = model.hourly_reference(hourly, [2])
        self.assertAlmostEqual(ref["ETH", a//H%24, 2], .04)  # includes ticket's own day (.06)
        data = {("ETH", M): {a+4*M: candle(100, 102, 98), a+5*M: candle(102),
                             a+15*M: candle(103), q+M: candle(104, 106, 102)},
                ("BTC", M): {a+M: candle(100), q+M: candle(102)}}
        for kind, clocks, expected in (
            ("midpoint", (1, 1), rough_mid), ("worst", (1, 1), 0),
            ("midpoint", (5, 1), 104/102-1), ("midpoint", (15, 1), 104/103-1),
            ("hourly", (0, 0), .06)):
            realized, cause = model.ticket_value(primary, kind, clocks, data, hourly, CFG, FEES)
            self.assertIsNone(cause)
            self.assertAlmostEqual(realized, expected-fee)
        hedged, _ = model.ticket_value(primary, "hedged", (1, 1), data, hourly, CFG, FEES)
        both = ((FEES["futures_round_trip_bp"]["ETH"] + FEES["futures_round_trip_bp"]["BTC"])/2+2)/10000
        self.assertAlmostEqual(hedged, (.04-.02)/2-both)
        dropped = model.aggregate([primary], {}, hourly, ref, CFG, FEES, "midpoint", (1, 1), CFG["proposed_marks"])
        self.assertEqual(dropped["rows_dropped_by_reason"], {"missing_entry_minute": 1})
        jobs = model.window_jobs({model.PRIMARY: [primary]}, [], CFG)
        self.assertTrue(all(gran == 60 and a <= lo < hi <= q + 7*M for _, gran, lo, hi in jobs))
        self.assertTrue(any(c == "BTC" for c, *_ in jobs))
        self.assertFalse(any(gran == H for _, gran, *_ in jobs))
        two_a = model.stamp("2021-05-19") + 10*H
        move = two_a-a
        shifted = {k: {t+move: b for t, b in v.items()} for k, v in data.items()}
        shifted["ETH", H] = {two_a: candle(100), two_a+2*H: candle(106)}
        hist = model.diagnostic([["ETH", two_a, two_a+2*H, .05]], shifted, CFG, FEES)
        self.assertEqual(hist["same_tickets_all_clocks"]["tickets"], 1)
        self.assertAlmostEqual(hist["same_tickets_all_clocks"]["share_of_same_population_search_mean"]
                               ["coinbase_hourly_open"], (.06-fee)/.05)
        self.assertEqual(hist["same_tickets_after_named_outage_dates"]["tickets"], 0)
        self.assertEqual(hist["scheduled_after_named_outage_dates"], 0)
        self.assertEqual(set(hist["observed_by_clock_after_named_outage_dates"].values()), {0})

    def test_collection_rederives_the_exact_fresh_and_prior_tickets_before_network(self):
        t = feed.FRESH[0] + 10*H
        q = feed.DIAG[0] + 10*H
        fresh = {model.PRIMARY: [["ETH", t, t+2*H]], **{k: [] for k in model.SHOWN}}
        diag = [["ETH", q, q+2*H]]
        starts = {coin: model.stamp(d) for coin, d in CFG["sources"].items()}
        jobs = model.window_jobs(fresh, diag, CFG)
        args = SimpleNamespace(collect_hourly=False, count=False, power=False, collect_minutes=True,
                               freeze_commit="a"*40, config_sha256="b"*64, settings_sha256="c"*64,
                               grid_sha256="d"*64, grid71_sha256="e"*64, hourly_manifest_sha256="f"*64)
        plan = {"fresh": fresh, "diagnostic": diag, "first_full_day": starts,
                "binding": {**runner.authority(args), "hourly_manifest_sha256": args.hourly_manifest_sha256},
                "counts": model.count_fields(fresh[model.PRIMARY]), "requests": jobs, "request_count": len(jobs),
                "minute_requests": sum(j[1] == M for j in jobs)}
        raw = feed.lines(plan)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "private"
            feed.ensure_dir(root)
            with (patch.object(runner, "read_plan", return_value=(plan, jobs, raw)) as get_plan,
                  patch.object(runner, "load_hourly", return_value={}),
                  patch.object(model, "activated", return_value=({}, starts)),
                  patch.object(model, "schedule", return_value={k: [] for k in fresh}) as get_fresh,
                  patch.object(runner, "prior_summary", return_value=([], .02)),
                  patch.object(runner, "approve", return_value=({}, {"approval_sha256": "test"})),
                  patch.object(runner, "old_tickets", return_value=[]) as get_old,
                  patch.object(feed, "collect", return_value={"fake": True}) as collect):
                with self.assertRaisesRegex(ValueError, "not byte-identical"):
                    runner.dispatch(root, root, args, CFG, FEES, [], SPECS)
                get_fresh.return_value = fresh
                with self.assertRaisesRegex(ValueError, "not byte-identical"):
                    runner.dispatch(root, root, args, CFG, FEES, [], SPECS)
                get_old.return_value = diag
                get_plan.return_value = plan, jobs, raw + b" "
                with self.assertRaisesRegex(ValueError, "not byte-identical"):
                    runner.dispatch(root, root, args, CFG, FEES, [], SPECS)
                collect.assert_not_called()
                get_plan.return_value = plan, jobs, raw
                runner.dispatch(root, root, args, CFG, FEES, [], SPECS)
                collect.assert_called_once_with(root, "windows", jobs, {"approval_sha256": "test"},
                                                CFG["request_delay_seconds"])
                self.assertEqual(get_old.call_args.kwargs, {"economics": False})

    def test_power_validation_and_single_use(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "private"
            feed.ensure_dir(root)
            cfg = copy.deepcopy(CFG)
            cfg["proposed_marks"] = {"matched_t": 1., "trim_share": .01, "positive_years": 2,
                                     "min_tickets": 2, "min_days": 2}
            cfg["power"].update({"draws": 32, "day_noise_bp": 1, "ticket_noise_bp": 1})
            t = feed.FRESH[0] + 10*H
            tickets = [["ETH", t, t+2*H], ["ETH", model.stamp("2018-01-10"), model.stamp("2018-01-10")+2*H]]
            self.assertEqual(model.power([], .01, cfg, cfg["proposed_marks"])["probability"], 0)
            self.assertGreater(model.power(tickets, .01, cfg, cfg["proposed_marks"])["probability"], .33)
            plan = {"fresh": {model.PRIMARY: tickets}, "diagnostic": [], "first_full_day": {"BTC": t},
                    "binding": {"freeze": "fabricated"}, "counts": model.count_fields(tickets)}
            args = SimpleNamespace(plan_sha256="a"*64, windows_manifest_sha256="b"*64, collect_hourly=False,
                                   count=False, power=False, collect_minutes=False, validate_inputs=True)
            mark = cfg["proposed_marks"]
            power = runner.design_power(plan, cfg, mark, .02)
            approval = feed.lines({**plan["binding"], "plan_sha256": args.plan_sha256, "marks": mark,
                                   "power": power, "lead_authorizes_one_use": True})
            args.approval_sha256 = runner.p70.digest(approval)
            runner.p70.create_private(root, runner.APPROVAL, approval)
            with self.assertRaisesRegex(ValueError, "does not bind"):
                runner.approve(root, SimpleNamespace(**{**vars(args), "plan_sha256": "0" * 64}), cfg, plan)
            with self.assertRaisesRegex(ValueError, "under the fixed power line"):
                runner.approve(root, args, {**cfg, "power": {**cfg["power"], "min_probability": 1.01}},
                               plan)
            calls = []
            syncs = []
            real_fsync = os.fsync

            def observe_fsync(fd):
                syncs.append(stat.S_IFMT(os.fstat(fd).st_mode))
                return real_fsync(fd)

            def fake_hour(*_):
                locked = (root / runner.LOCK).exists()
                self.assertEqual(syncs, [stat.S_IFREG, stat.S_IFDIR] if locked else [])
                calls.append(locked)
                return {}

            with (patch.object(runner, "prior_summary", return_value=([], None)) as summary,
                  patch.object(runner, "old_tickets", return_value=[]) as vectors,
                  patch.object(os, "fsync", side_effect=observe_fsync),
                  patch.object(runner, "load_hourly", side_effect=fake_hour),
                  patch.object(runner, "read_plan", return_value=(plan, [], b"{}")),
                  patch.object(model, "activated", return_value=({}, {"BTC": t})),
                  patch.object(feed, "load", return_value={}),
                  patch.object(model, "schedule", side_effect=RuntimeError("scoring path")),
                  patch.object(runner, "design_power", side_effect=AssertionError("power forbidden"))):
                output = runner.dispatch(root, root, args, cfg, FEES, [], SPECS)
                self.assertEqual(list(json.loads(output)), ["input_counts"])
                self.assertEqual(sorted(os.listdir(root)), [runner.APPROVAL])
                args.validate_inputs = False
                with self.assertRaisesRegex(RuntimeError, "scoring path"):
                    runner.dispatch(root, root, args, cfg, FEES, [], SPECS)
                self.assertEqual(calls, [False, True])
                self.assertTrue(all(not call.kwargs for call in summary.call_args_list))
                self.assertEqual([call.kwargs for call in vectors.call_args_list], [{"economics": False}])
                self.assertEqual((root / runner.LOCK).stat().st_mode & 0o777, 0o600)
                for mode in ("collect_hourly", "count", "power", "collect_minutes", "validate_inputs", "go"):
                    with self.subTest(mode=mode), self.assertRaises(FileExistsError):
                        runner.dispatch(root, root, SimpleNamespace(**{**vars(args), mode: True}), cfg, FEES, [], SPECS)

    def test_actual_minute_overlap_stops_before_any_pricing(self):
        t = feed.FRESH[0] + 10*H
        q = t + 2*H
        fresh = {model.PRIMARY: [["ETH", t, q], ["LTC", q, q+2*H]], **{k: [] for k in model.SHOWN}}
        starts = {"BTC": t, "ETH": t, "LTC": t}
        plan = {"fresh": fresh, "first_full_day": starts, "diagnostic": []}
        before = {("ETH", M): {t+M: None, q+6*M: None}, ("LTC", M): {q+M: None, q+2*H+M: None}}
        self.assertEqual(model.actual_overlaps(fresh[model.PRIMARY], before, CFG, "midpoint", (1, 1)), {q})
        equal = {**before, ("LTC", M): {q+6*M: None, q+2*H+M: None}}
        self.assertEqual(model.actual_overlaps(fresh[model.PRIMARY], equal, CFG, "midpoint", (1, 1)), set())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "private"
            feed.ensure_dir(root)
            args = SimpleNamespace(windows_manifest_sha256="a"*64)
            with (patch.object(runner, "approve", return_value=(CFG["proposed_marks"], {})),
                  patch.object(runner, "load_hourly", return_value={}),
                  patch.object(model, "activated", return_value=({}, starts)),
                  patch.object(feed, "load", return_value=before),
                  patch.object(model, "schedule", return_value=fresh),
                  patch.object(model, "hourly_reference", side_effect=AssertionError("pricing forbidden")),
                  patch.object(model, "aggregate", side_effect=AssertionError("pricing forbidden")),
                  patch.object(runner, "prior_summary", side_effect=AssertionError("diagnostic forbidden")),
                  runner.unused(root) as claim):
                out = json.loads(runner.pricing(root, root, args, CFG, FEES, [], SPECS, plan, [],
                                                validation=False, claim=claim))
            self.assertEqual(out["input_counts"]["actual_minute_overlap"], 1)
            self.assertEqual(out["input_counts"]["scheduled_judged_tickets"], 2)
            self.assertEqual(out["unscorable"], "actual_minute_overlap_above_limit")

    def test_prior_vector_corruption_rejects_standalone_preflight_without_claim(self):
        t = feed.DIAG[0] + 10*H
        rules = [SPECS["71-035"], SPECS[model.PRIMARY]]
        prior_rows = b"".join(feed.lines(r) for r in ({"input_counts": {}}, *[
            {"rule": r["id"], "finalist_rank": i, "trades": 1, "active_days": 1}
            for i, r in enumerate(rules, 1)]))
        vectors = {"columns": runner.follow.COLUMNS,
                   "rules": [{"rule": r["id"],
                              "tickets": [[["ETH"], t, t+r["hold_hours"]*H, .01, .002, .008]]} for r in rules]}
        vector_bytes = feed.lines(vectors)
        searched = [["ETH", t, t+2*H]]
        with tempfile.TemporaryDirectory() as temp:
            root, prior = Path(temp) / "plan72", Path(temp) / "prior"
            feed.ensure_dir(root)
            feed.ensure_dir(prior)
            (prior / "sweep_70").mkdir(mode=0o700)
            prior_pin = runner.p70.digest(prior_rows)
            receipt = {"search71_sha256": prior_pin, "grid71_sha256": runner.GRID71_SHA, "carried_ids": [],
                       "vectors_sha256": runner.p70.digest(vector_bytes), "forecasts": [{"rule": r["id"]} for r in rules]}
            receipt_bytes = feed.lines(receipt)
            runner.p70.create_private(prior, runner.p71.SEARCH_REL, prior_rows)
            runner.p70.create_private(prior, runner.follow.RECEIPT, receipt_bytes)
            path = prior / runner.follow.VECTORS
            args = SimpleNamespace(collect_hourly=False, count=False, power=False, collect_minutes=False,
                                   validate_inputs=True)
            with (patch.object(runner, "SEARCH71_SHA", prior_pin),
                  patch.object(runner, "CARRY71_SHA", runner.p70.digest(receipt_bytes)),
                  patch.object(runner, "approve", return_value=(CFG["proposed_marks"], {})),
                  patch.object(runner, "read_plan", return_value=({"diagnostic": searched}, [], b"{}")),
                  patch.object(runner, "coinbase_inputs", return_value=({}, {}, {}, {"input_counts": {}})) as get_inputs):
                with self.assertRaises(FileNotFoundError):
                    runner.dispatch(root, prior, args, CFG, FEES, rules, SPECS)
                self.assertFalse((root / runner.LOCK).exists())
                runner.p70.create_private(prior, runner.follow.VECTORS, vector_bytes + b" ")
                with self.assertRaisesRegex(ValueError, "changed pinned input"):
                    runner.dispatch(root, prior, args, CFG, FEES, rules, SPECS)
                self.assertFalse((root / runner.LOCK).exists())
                path.write_bytes(vector_bytes)
                args.validate_inputs = True
                self.assertEqual(json.loads(runner.dispatch(root, prior, args, CFG, FEES, rules, SPECS)),
                                 {"input_counts": {}})
                get_inputs.assert_called_once()
                searched[0][1] += H
                with self.assertRaisesRegex(ValueError, "prior search tickets"):
                    runner.dispatch(root, prior, args, CFG, FEES, rules, SPECS)
                self.assertFalse((root / runner.LOCK).exists())


def main():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
