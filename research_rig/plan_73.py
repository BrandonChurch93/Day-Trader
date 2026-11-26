"""Plan 73 lead-only, same-ticket Coinbase clock diagnosis. No fresh data or power."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

import numpy as np

import coinbase_72 as feed
import model_72 as model
import plan_72 as prior

BASE = "79cd10162f96982e6b1e12ce2ee65fef73261e87"
CONFIG = "research_rig/CONFIG_73.json"
CLOCK_SHA = "616b78712aa2e2313541814a18c9f8c3cc49011ff04ead12060035ff3eb0dbb1"
DATA = Path("/home/user/workspace/rig/data/plan73")
PLAN = "minute_plan.json"
STAGE = "diagnostic"
HOLD_HOURS = 2
YEARS = tuple(str(y) for y in range(2020, 2024))
SEARCH = "frozen_search_plain_net"
OPEN = "coinbase_hourly_open"
REACH = "coinbase_reachable_minute"
LATE = "coinbase_entry_5m_late"
NO_PASS = "This diagnosis uses already-searched tickets. No reading is a pass or allows money."


def freeze(args):
    if not args.lead_authorize or not (sys.flags.ignore_environment and sys.dont_write_bytecode
                                       and sys.pycache_prefix == "/dev/null"):
        raise ValueError("need lead authorization and python -E -B -X pycache_prefix=/dev/null")
    if (args.grid_sha256, args.grid71_sha256) != (prior.p70.GRID_SHA, prior.GRID71_SHA):
        raise ValueError("the inherited rule grid pins differ")
    repo = prior.old.HERE.parent
    blobs = prior.old.checked_freeze(repo, args.freeze_commit, args.grid_sha256, args.settings_sha256,
                                     (*prior.EXTRA, CONFIG, "research_rig/plan_73.py"), ancestor=BASE)
    if (prior.p70.digest(blobs[CONFIG]) != args.config_sha256 or prior.p70.digest(blobs[prior.CONFIG]) != CLOCK_SHA
            or prior.p70.digest(blobs[prior.p71.GRID_PATH]) != prior.GRID71_SHA):
        raise ValueError("Plan 73 config, inherited clocks or Plan 71 grid pin differs")
    cfg = json.loads(blobs[CONFIG])
    clocks = json.loads(blobs[prior.CONFIG])
    cfg.update({key: clocks[key] for key in ("minutes", "outage_utc_dates", "request_delay_seconds")})
    fees = prior.inherited_fees(repo, blobs)
    grid = json.loads(blobs[prior.p71.GRID_PATH])
    if (len([r for r in grid if r["id"] == model.PRIMARY and r["hold_hours"] == HOLD_HOURS
             and r["top_coins"] == 1 and r["side"] == 1 and not r["btc_hedge"]]) != 1
            or fees["funding_adverse_bp_per_hour"] != 1):
        raise ValueError("inherited rule or funding differs from registration")
    return cfg, fees, grid


def year(stamp):
    return str(datetime.fromtimestamp(stamp, timezone.utc).year)


def outage_days(cfg):
    return {model.stamp(d) // model.DAY for d in cfg["outage_utc_dates"]}


def tickets_from_prior(root, grid, cfg, *, economics=False):
    chosen, _ = prior.prior_summary(root, grid)
    tickets = prior.old_tickets(root, grid, chosen, economics=economics)
    if len(tickets) != cfg["expected_search_tickets"]:
        raise ValueError("prior ticket count differs from the registration")
    prior.check_tickets([t[:3] for t in tickets], prior.old.ALLOWED, HOLD_HOURS, feed.DIAG)
    return tickets


def canonical_plan(args, cfg, tickets):
    # Check all clocks before an exclusion can hide a bad timestamp.
    prior.check_tickets(tickets, prior.old.ALLOWED, HOLD_HOURS, feed.DIAG)
    outage = outage_days(cfg)
    retained = [t for t in tickets if not model.outage_touch(t[1], t[2], outage)]
    union = model.window_jobs({}, retained, cfg)
    jobs = [feed.validate(j, STAGE) for j in sorted(union, key=lambda j: (j[1] != feed.HOUR, j))]
    counts = {"search_tickets": len(tickets), "outage_date_exclusions": len(tickets) - len(retained),
              "candidate_pairs": sorted({coin + "-USD" for coin, *_ in tickets}),
              "requested_pairs": sorted({coin + "-USD" for coin, *_ in retained}),
              "hourly_requests": sum(j[1] == feed.HOUR for j in jobs),
              "minute_requests": sum(j[1] == feed.MINUTE for j in jobs), "total_requests": len(jobs)}
    return {"binding": prior.authority(args), "tickets": tickets, "requests": jobs, "counts": counts}


def approval(root, args):
    binding = {**prior.authority(args), "plan_sha256": args.plan_sha256}
    doc = json.loads(prior.p70.pinned(root, prior.APPROVAL, args.approval_sha256, mode=0o600))
    if doc != {**binding, "lead_authorizes_one_use": True} or doc.get("lead_authorizes_one_use") is not True:
        raise ValueError("lead approval does not bind the exact count plan and freeze")
    return {**binding, "approval_sha256": args.approval_sha256}


def any_print_evidence(coin, a, b, data, cfg):
    """One observed print supports pair availability; empty windows cannot prove listing status."""
    hours = data.get((coin, feed.HOUR), {})
    if a in hours or b in hours:
        return True
    minutes = cfg["minutes"]
    offsets = [(a, n) for n in (minutes["judged"], *minutes["shown_late"])] + [(b, minutes["judged"])]
    return any(model.first_minute(data, coin, hour, offset, cfg, feed.DIAG) is not None
               for hour, offset in offsets)


def diagnosis(tickets, data, cfg, fees):
    clocks, detail = model.diagnostic(tickets, data, cfg, fees, detailed=True)
    counts = Counter(dict.fromkeys(("outage_date", "no_pair_evidence_at_ticket", "missing_hourly_open",
                                    "missing_minute"), 0))
    missing = Counter(dict.fromkeys(clocks, 0))
    complete = []
    for coin, a, b, saved, priced in detail:
        if priced is None:
            counts["outage_date"] += 1
            continue
        for clock, (value, _) in priced.items():
            missing[clock] += value is None
        if any(v[0] is None for v in priced.values()):
            if not any_print_evidence(coin, a, b, data, cfg):
                counts["no_pair_evidence_at_ticket"] += 1
            else:
                counts["missing_hourly_open" if priced[OPEN][0] is None else "missing_minute"] += 1
            continue
        complete.append((coin, a, {SEARCH: saved, **{k: v[0] for k, v in priced.items()}}))

    def mean(vals):
        return float(np.mean(vals)) if len(vals) else None

    def contrast(other):
        diffs = np.array([v[REACH] - v[other] for _, _, v in complete])
        days = np.array([(a - feed.DIAG[0]) // model.DAY for _, a, _ in complete], dtype=int)
        return {"paired_mean_difference": mean(diffs), "utc_day_clustered_t": prior.old.t_cluster(diffs, days),
                "utc_entry_days": len(np.unique(days))}

    means = {k: mean([v[k] for _, _, v in complete]) for k in (*clocks, SEARCH)}
    threshold = means[SEARCH] * cfg["search_mean_fraction"] if means[SEARCH] is not None else None
    n = len(complete)
    if n < cfg["minimum_compared_tickets"]:
        reading = "UNREADABLE"
    elif means[REACH] < threshold:
        reading = "ARTIFACT"
    elif means[LATE] > 0:
        reading = "REACHABLE"
    else:
        reading = "PARTLY"
    coin_count = Counter(coin for coin, _, _ in complete)
    return {"kind": "shown_search_dates_not_a_test", "notice": NO_PASS,
            "pair_evidence_notice": "No print in any ticket window leaves historical listing status UNKNOWN.",
            "reading": reading, "search_tickets": len(tickets), "compared_tickets": n,
            "compared_by_year": {y: sum(year(a) == y for _, a, _ in complete) for y in YEARS},
            "compared_coin_count": len(coin_count), "compared_by_coin": dict(coin_count),
            "dropped_by_exclusive_reason": dict(counts), "unavailable_by_clock_after_outage_filter": dict(missing),
            "net_mean_by_clock": means,
            "reading_inputs": {"compared_tickets": n, "minimum_compared_tickets": cfg["minimum_compared_tickets"],
                               "search_mean_fraction": cfg["search_mean_fraction"], "search_mean": means[SEARCH],
                               "reachable_mean": means[REACH], "reachable_minimum_mean": threshold,
                               "five_minute_late_mean": means[LATE], "five_minute_late_must_exceed": 0.},
            "paired_reachable_minus_search": contrast(SEARCH), "paired_reachable_minus_coinbase_open": contrast(OPEN),
            "reachable_net_mean_by_year": {y: mean([v[REACH] for _, a, v in complete if year(a) == y]) for y in YEARS}}


def dispatch(root, prior_root, args, cfg, fees, grid):
    if args.count:
        feed.ensure_dir(root)
    feed.private_dir(root)
    with prior.unused(root) as (fd, lock):
        if args.count:
            planned = canonical_plan(args, cfg, tickets_from_prior(prior_root, grid, cfg))
            raw = feed.lines(planned)
            prior.p70.create_private(root, PLAN, raw)
            return feed.lines({**planned["counts"], "plan_sha256": prior.p70.digest(raw), "private_request_plan": PLAN})

        raw = prior.p70.pinned(root, PLAN, args.plan_sha256, mode=0o600)
        binding = approval(root, args)
        if args.go:
            # Claim before any old vector or priced Coinbase input is even opened.
            if (not isinstance(args.windows_manifest_sha256, str) or len(args.windows_manifest_sha256) != 64
                    or any(ch not in "0123456789abcdef" for ch in args.windows_manifest_sha256)):
                raise ValueError("independent windows manifest hash required")
            prior.p70.create_at(fd, lock, feed.lines({**binding,
                                                     "windows_manifest_sha256": args.windows_manifest_sha256}))
        tickets = tickets_from_prior(prior_root, grid, cfg, economics=args.go)
        canonical = canonical_plan(args, cfg, [t[:3] for t in tickets])
        if feed.lines(canonical) != raw:
            raise ValueError("saved minute plan is not byte-identical to the authenticated search ticket schedule")
        jobs = canonical["requests"]
        if args.collect:
            return feed.lines(feed.collect(root, STAGE, jobs, binding, cfg["request_delay_seconds"]))
        data = feed.load(root, STAGE, args.windows_manifest_sha256, jobs, binding)
        if args.validate_inputs:
            return feed.lines({"input_counts": {**canonical["counts"],
                                               "hourly_rows": sum(len(v) for k, v in data.items() if k[1] == feed.HOUR),
                                               "minute_rows": sum(len(v) for k, v in data.items() if k[1] == feed.MINUTE)}})
        return feed.lines(diagnosis(tickets, data, cfg, fees))


def synthetic():
    """Made-up prices, mock HTTP and temporary paths only."""
    from email.message import Message
    from io import BytesIO
    import os
    import stat
    import tempfile
    from types import SimpleNamespace
    import unittest
    from unittest.mock import patch
    from urllib.error import HTTPError

    repo = prior.old.HERE.parent
    cfg = json.loads((repo / CONFIG).read_bytes())
    clocks = json.loads((repo / prior.CONFIG).read_bytes())
    cfg.update({k: clocks[k] for k in ("minutes", "outage_utc_dates", "request_delay_seconds")})
    fees = prior.old.parse_config(*((repo / p).read_bytes() for p in
                                   (prior.old.COVERAGE_PATH, prior.old.SETTINGS_PATH, prior.old.GRID_PATH)))
    H, M, D = feed.HOUR, feed.MINUTE, model.DAY

    def bar(x):
        return (x, x, x, x, 1.)

    def prices(n, exit_price, late=100.):
        tickets, data = [], {("ETH", H): {}, ("ETH", M): {}}
        for i in range(n):
            y, day = divmod(i, 50)
            a = model.stamp(f"{2020+y}-01-01") + day*D + 10*H
            b = a + HOLD_HOURS*H
            tickets.append(["ETH", a, b, .02])
            data["ETH", H].update({a: bar(100.), b: bar(103.)})
            # In the first two cases both +1 and +5 fall back to :06.
            data["ETH", M].update({a+6*M: bar(100.), a+15*M: bar(100.),
                                   b+M: bar(exit_price + .002*(i % 3))})
            if late != 100.:
                data["ETH", M].update({a+M: bar(100.), a+5*M: bar(late)})
        return tickets, data

    class Tests(unittest.TestCase):
        def test_clock_readings_and_paired_statistics(self):
            n = cfg["minimum_compared_tickets"]
            for exit_price, late, expected in ((100., 100., "ARTIFACT"), (102., 100., "REACHABLE"),
                                               (102., 103., "PARTLY")):
                tickets, data = prices(n, exit_price, late)
                out = diagnosis(tickets, data, cfg, fees)
                self.assertEqual(out["reading"], expected)
                self.assertEqual(out["compared_by_year"], dict(zip(YEARS, (50, 50, 50, 0))))
                self.assertEqual(out["compared_by_coin"], {"ETH": n})
                self.assertLess(out["paired_reachable_minus_coinbase_open"]["utc_day_clustered_t"], 0)
                self.assertIn("No reading is a pass", out["notice"])
                self.assertIn("coinbase_worst_minute", out["net_mean_by_clock"])

        def test_unreadable_and_four_exclusive_drop_reasons(self):
            n = cfg["minimum_compared_tickets"] - 1
            tickets, data = prices(n, 102.)
            d = model.stamp("2021-05-19") + D + H
            a = model.stamp("2023-05-03") + 10*H
            extra = [["ETH", d, d+2*H, .01], ["LINK", a, a+2*H, .01],
                     ["XRP", a+2*H, a+4*H, .01], ["LTC", a+4*H, a+6*H, .01]]
            data["XRP", M] = {a+2*H+M: bar(100.)}
            data["LTC", H] = {a+4*H: bar(100.), a+6*H: bar(102.)}
            out = diagnosis(tickets + extra, data, cfg, fees)
            self.assertEqual(out["reading"], "UNREADABLE")
            self.assertEqual(out["compared_tickets"], n)
            self.assertEqual(set(out["dropped_by_exclusive_reason"].values()), {1})

        def test_strict_date_fence_and_explicit_product_not_found(self):
            client = feed.Client(.55)
            a, b = feed.DIAG
            with patch.object(client.opener, "open") as wire, patch.object(feed.time, "sleep"):
                for tick in (a-H, b):
                    with self.assertRaises(ValueError):
                        client.get(("ETH", H, tick, tick+H), STAGE)
                    with self.assertRaises(ValueError):
                        canonical_plan(None, cfg, [["ETH", tick, tick+2*H]])
                wire.assert_not_called()
                headers = Message()
                headers["Content-Type"] = "application/json"
                raw = b'{"message":"Product not found"}'
                window = ("ETH", H, b-H, b)
                wire.side_effect = HTTPError(feed.URL, 404, "simulated", headers, BytesIO(raw))
                self.assertEqual(client.get(window, STAGE), raw)
                self.assertEqual(feed.parse(raw, window, STAGE), {})
                self.assertIn("end=2023-12-31T23%3A59%3A59Z", wire.call_args.args[0].full_url)
                for code, body in ((404, b'{"message":"ambiguous"}'), (404, b'{"message":"NotFound"}'),
                                   (404, b'{"message":"Bad gateway","message":"Product not found"}'),
                                   (404, b'[["message","Product not found"]]'), (429, raw), (403, raw)):
                    wire.side_effect = HTTPError(feed.URL, code, "simulated", headers, BytesIO(body))
                    with self.assertRaises(HTTPError):
                        client.get(window, STAGE)

        def test_mock_private_flow_checks_tickets_before_wire_and_claims_before_prices(self):
            finalists = ("71-035", model.PRIMARY)
            grid = [{"id": rid, "hold_hours": hold, "top_coins": 1} for rid, hold in zip(finalists, (1, 2))]
            a = feed.DIAG[0] + 10*H
            summary = feed.lines({"input_counts": {}}) + b"".join(feed.lines(
                {"rule": rid, "finalist_rank": i, "trades": 1, "active_days": 1})
                for i, rid in enumerate(finalists, 1))
            vectors = {"columns": prior.follow.COLUMNS, "rules": [
                {"rule": r["id"], "tickets": [[["ETH"], a, a+r["hold_hours"]*H, .02, .01, .01]]} for r in grid]}
            raw = feed.lines(vectors)
            search_pin = prior.p70.digest(summary)
            receipt = feed.lines({"search71_sha256": search_pin, "grid71_sha256": prior.GRID71_SHA,
                                  "carried_ids": [], "forecasts": [{"rule": rid} for rid in finalists],
                                  "vectors_sha256": prior.p70.digest(raw)})
            args = SimpleNamespace(count=True, collect=False, validate_inputs=False, go=False,
                                   freeze_commit="a"*40, config_sha256="b"*64, settings_sha256="c"*64,
                                   grid_sha256="d"*64, grid71_sha256="e"*64)
            small = {**cfg, "expected_search_tickets": 1}
            real_pinned, real_fsync = prior.p70.pinned, os.fsync
            syncs, order = [], []
            with tempfile.TemporaryDirectory() as temp:
                root, old_root = Path(temp) / "plan73", Path(temp) / "prior"
                feed.ensure_dir(old_root)
                (old_root / "sweep_70").mkdir(mode=0o700)
                for path, blob in ((prior.p71.SEARCH_REL, summary), (prior.follow.RECEIPT, receipt),
                                   (prior.follow.VECTORS, raw)):
                    prior.p70.create_private(old_root, path, blob)

                def tracked_pin(home, path, sha, **kwargs):
                    if args.go and (path == prior.follow.VECTORS or path.startswith(STAGE)):
                        self.assertTrue((root / prior.LOCK).exists())
                        self.assertEqual(syncs, [stat.S_IFREG, stat.S_IFDIR])
                    return real_pinned(home, path, sha, **kwargs)

                def sync(fd):
                    syncs.append(stat.S_IFMT(os.fstat(fd).st_mode))
                    return real_fsync(fd)

                def candles(job, stage):
                    self.assertEqual(stage, STAGE)
                    order.append(job[1])
                    return feed.lines([[job[2], 100, 100, 100, 100, 1]])

                with (patch.object(prior, "SEARCH71_SHA", search_pin),
                      patch.object(prior, "CARRY71_SHA", prior.p70.digest(receipt)),
                      patch.object(prior.p70, "pinned", side_effect=tracked_pin),
                      patch.object(feed.Client, "get", side_effect=candles) as wire):
                    counted = json.loads(dispatch(root, old_root, args, small, fees, grid))
                    self.assertEqual(counted["candidate_pairs"], ["ETH-USD"])
                    self.assertNotIn(b"plain_net", (root / PLAN).read_bytes())
                    args.count, args.collect = False, True
                    args.plan_sha256 = counted["plan_sha256"]
                    approved = feed.lines({**prior.authority(args), "plan_sha256": args.plan_sha256,
                                           "lead_authorizes_one_use": True})
                    prior.p70.create_private(root, prior.APPROVAL, approved)
                    args.approval_sha256 = prior.p70.digest(approved)
                    old_file = old_root / prior.follow.VECTORS
                    vectors["rules"][1]["tickets"][0][0] = ["LTC"]
                    for changed in (raw + b" ", feed.lines(vectors)):
                        old_file.write_bytes(changed)
                        with self.assertRaisesRegex(ValueError, "changed pinned input"):
                            dispatch(root, old_root, args, small, fees, grid)
                    wire.assert_not_called()
                    old_file.write_bytes(raw)
                    collected = json.loads(dispatch(root, old_root, args, small, fees, grid))
                    self.assertEqual(order, sorted(order, reverse=True))
                    args.collect, args.validate_inputs = False, True
                    args.windows_manifest_sha256 = collected["manifest_sha256"]
                    with patch.object(model, "diagnostic", side_effect=AssertionError("pricing forbidden")):
                        self.assertIn("input_counts", json.loads(dispatch(root, old_root, args, small, fees, grid)))
                    self.assertFalse((root / prior.LOCK).exists())
                    args.validate_inputs, args.go = False, True
                    with patch.object(os, "fsync", side_effect=sync):
                        result = json.loads(dispatch(root, old_root, args, small, fees, grid))
                    self.assertEqual(result["reading"], "UNREADABLE")
                    for mode in ("count", "collect", "validate_inputs", "go"):
                        with self.assertRaises(FileExistsError):
                            closed = SimpleNamespace(**{**vars(args), "go": False, mode: True})
                            dispatch(root, old_root, closed, small, fees, grid)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for flag in ("synthetic", "count", "collect", "validate-inputs", "go"):
        modes.add_argument("--" + flag, action="store_true")
    for flag in ("freeze-commit", "config-sha256", "settings-sha256", "grid-sha256", "grid71-sha256",
                 "plan-sha256", "windows-manifest-sha256", "approval-sha256"):
        parser.add_argument("--" + flag)
    parser.add_argument("--lead-authorize", action="store_true")
    args = parser.parse_args()
    if args.synthetic:
        synthetic()
        return
    sys.stdout.buffer.write(dispatch(DATA, prior.old.CUSTODY, args, *freeze(args)))


if __name__ == "__main__":
    main()
