"""Made-up-data tests for Plan 70 carry and vault; never access real custody."""
import copy
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile

import numpy as np
import yaml

import carry_70 as carry
import sweep_70 as search
import vault_70 as vault
import vault_gate_70 as gate
from vault_census_70 import MONTHS, archive_info, month_info, month_record

SETTINGS = yaml.safe_load((search.HERE.parent / search.SETTINGS_PATH).read_bytes())["replay_70_plan"]["value"]
CLOCK = vault.WRONG_CLOSE_CLOCK


def mock_manifest():
    out = {}
    for c in search.ALLOWED:
        out[c] = []
        for m in MONTHS:
            start, expected, _ = month_info(m)
            row = ({"missing_archive": True} if (c, m) in vault.DECLARED_ABSENT else
                   {"path": archive_info(c, m)[1][0], "sha256": "a" * 64, "rows": 1,
                    "expected": expected, "wrong_close_clock": 0,
                    "first_utc_seconds": start, "last_utc_seconds": start})
            out[c].append({"month": m, **row})
    return out


class SyntheticPost(unittest.TestCase):
    def test_bootstrap_pairs_calendar_trim_and_independent_pcg(self):
        day = np.repeat(np.arange(search.DAYS), 2)
        plain = np.where(np.arange(len(day)) % 3 == 0, -0.03, 0.02)
        paired = 0.4 * plain + 0.004
        pairs, mask = gate.day_matrix(plain, paired, day, .5)
        self.assertTrue(mask.all())
        np.testing.assert_allclose(pairs[1, :, 0], plain[2:4] - .5 * plain.mean())
        np.testing.assert_allclose(pairs[1, :, 1], paired[2:4] - .5 * paired.mean())
        np.testing.assert_array_equal(gate.sampled_days(np.array([search.DAYS - 2]), 7),
                                      [search.DAYS - 2, search.DAYS - 1, 0, 1, 2, 3, 4])
        cfg = copy.deepcopy(SETTINGS)
        cfg["vault_power"]["draws"] = 12
        rng = np.random.default_rng(702102)
        yes = 0
        for _ in range(12):
            days = np.array([(int(a) + b) % search.DAYS for a in rng.integers(
                search.DAYS, size=(gate.VAULT_DAYS + 6) // 7) for b in range(7)][:gate.VAULT_DAYS])
            plus = (2 * days[:, None] + np.array([0, 1])).ravel()
            target = np.repeat(np.arange(gate.VAULT_DAYS), 2)
            p, q = plain[plus] - .5 * plain.mean(), paired[plus] - .5 * paired.mean()
            annual = p.sum() * 365.25 / gate.VAULT_DAYS
            yes += (p.mean() > 0 and search.t_cluster(q, target) >= 2.4
                    and np.sort(p)[:-int(np.ceil(.01 * len(p)))].mean() > 0 and annual >= .08
                    and sum(p[gate.HALF_YEAR[target] == h].sum() > 0 for h in range(6)) >= 4)
        got = gate.bootstrap("70-102", plain, paired, day, cfg)
        self.assertEqual(got, {"carry": yes / 12 >= .33, "probability": yes / 12, "passes": yes,
                               "draws": 12, "seed": 702102, "rule": "70-102"})
        self.assertEqual(gate.HALF_YEAR[-1], 5)
        self.assertEqual(np.bincount(gate.HALF_YEAR).tolist(), [182, 184, 181, 184, 181, 123])
        with self.assertRaises(ValueError):
            gate.day_matrix(plain, paired, day + 1, .5)

    def test_census_both_units_and_wrong_clock_before_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for m in ("2024-01", "2025-01"):
                start, _, ticks = month_info(m)
                name, paths = archive_info("BTC", m)
                raw = (root / paths[0])
                raw.parent.mkdir(parents=True, exist_ok=True)
                stamp = start * 1000 * ticks
                step = search.HOUR_MS * ticks
                with ZipFile(raw, "w") as z:
                    z.writestr(name + ".csv", f"{stamp},100,100,100,100,0,{stamp + step - 1},x\n"
                               f"{stamp+step},invalid,invalid,invalid,invalid,invalid,{stamp+2*step},x\n")
                row = month_record(root, "BTC", m)
                self.assertEqual((row["rows"], row[CLOCK]), (2, 1))
                with ZipFile(raw) as z, z.open(name + ".csv") as wire:
                    self.assertEqual(list(search.read_hour_rows(wire, start, start + 7200, ticks)), [
                        (0, (100, 100, 100, 100, 0)), (1, None)])
                with ZipFile(raw) as z, z.open(name + ".csv") as wire:
                    self.assertEqual(list(search.read_hour_rows(wire)), [])

    def test_zec_gap_and_exact_absence(self):
        roster = mock_manifest()
        vault.check_manifest(roster)
        wrong = copy.deepcopy(roster)
        wrong["BTC"][0] = {"month": MONTHS[0], "missing_archive": True}
        with self.assertRaisesRegex(ValueError, "five declared"):
            vault.check_manifest(wrong)
        calendar = gate.VAULT_HOURS[:100]
        prices = np.full((2, len(calendar), 5), 100.)
        prices[1, :10] = np.nan
        tape = search.Tape(["BTC", "ZEC"], prices, hours=calendar, split=None)
        self.assertTrue(np.all(np.isnan(tape.lag(2)[1, :13])))
        self.assertEqual(tape.lag(2)[1, 13], 0)

    def test_shared_vault_dispatch_lock_order_retry_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sweep_70").mkdir()
            args = SimpleNamespace(search_summary_sha256="x", carry_sha256="y", approval_sha256="z",
                                   vault_manifest_sha256="a", validate_inputs=True)
            counts = {"rows_kept_by_coin": {"BTC": 1}}
            roster = mock_manifest()
            lock = {"carried_ids": ["70-102"]}
            syncs = []
            real_fsync = os.fsync

            def trace_sync(fd):
                syncs.append(stat.S_IFMT(os.fstat(fd).st_mode))
                return real_fsync(fd)

            def fake_read(root, rel, pin):
                return json.dumps(roster if rel == vault.MANIFEST else {}).encode()

            def fake_load(*_):
                self.assertEqual((root / vault.LOCK).exists(), not args.validate_inputs)
                self.assertEqual(syncs, [stat.S_IFREG, stat.S_IFDIR] if not args.validate_inputs else [])
                if not args.validate_inputs:
                    self.assertEqual(stat.S_IMODE((root / vault.LOCK).stat().st_mode), 0o600)
                return "panel", counts

            with (patch.object(carry, "pinned", side_effect=fake_read),
                  patch.object(vault, "commitment", return_value=lock),
                  patch.object(carry.os, "fsync", side_effect=trace_sync),
                  patch.object(vault, "load", side_effect=fake_load) as loader,
                  patch.object(vault, "score", side_effect=RuntimeError("no scoring")) as scorer):
                preflight = vault.dispatch(root, args, {}, [])
                self.assertEqual(preflight, search.rows_bytes([{"input_counts": counts}]))
                self.assertFalse((root / vault.LOCK).exists())
                scorer.assert_not_called()
                args.validate_inputs = False
                with self.assertRaisesRegex(RuntimeError, "no scoring"):
                    vault.dispatch(root, args, {}, [])
                with self.assertRaises(FileExistsError):
                    vault.dispatch(root, args, {}, [])
                self.assertEqual(loader.call_count, 2)

    def test_pinned_signed_receipt_requires_exact_ids_and_authorization(self):
        args = SimpleNamespace(freeze_commit="runner", search_summary_sha256="search", grid_sha256="grid",
                               settings_sha256="settings", carry_sha256="carry", vault_manifest_sha256="vault",
                               approval_sha256="approval", carried_id=["70-102"])
        summary = search.rows_bytes([{"input_counts": {}}, {"rule": "70-102", "finalist_rank": 1,
                                                            "duplicate_of": None, "meets_search_marks": True}])
        base = {"runner_freeze_commit": "runner", "search_freeze_commit": carry.SEARCH_FREEZE,
                "search_summary_sha256": "search", "grid_sha256": "grid", "settings_sha256": "settings",
                "search_manifest_sha256": carry.MANIFEST_SHA, "vectors_sha256": "a" * 64,
                "carried_ids": ["70-102"]}
        receipt = {**base, "forecasts": [{"rule": "70-102", "seed": 702102, "draws": 20000, "passes": 6600,
                                         "carry": True, "probability": .33}]}
        approval = {**base, "carry_sha256": "carry", "vault_manifest_sha256": "vault",
                    "lead_authorizes_single_use": True}
        rules = [{"id": "70-102"}]
        lock = vault.commitment(args, SETTINGS, rules, summary, receipt, approval)
        self.assertEqual(lock["carried_ids"], ["70-102"])
        for change in ({"lead_authorizes_single_use": False}, {"carried_ids": []}, {"carry_sha256": "other"}):
            with self.assertRaises(ValueError):
                vault.commitment(args, SETTINGS, rules, summary, receipt, {**approval, **change})
        args.carried_id.append("70-101")
        with self.assertRaises(ValueError):
            vault.commitment(args, SETTINGS, rules, summary, receipt, approval)

    def test_vault_loader_replays_pinned_months_and_does_not_fill_gap(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            roster = mock_manifest()
            for coin, entries in roster.items():
                for r in entries:
                    if r.get("missing_archive"):
                        continue
                    m = r["month"]
                    first, _, ticks = month_info(m)
                    t = first * 1000 * ticks
                    wrong_clock = coin == "BTC" and m == "2026-10"
                    close = t + search.HOUR_MS * ticks - 1 + wrong_clock
                    raw = root / r["path"]
                    raw.parent.mkdir(parents=True, exist_ok=True)
                    fields = "junk,junk,junk,junk,junk" if wrong_clock else "1,1,1,1,0"
                    with ZipFile(raw, "w") as z:
                        z.writestr(archive_info(coin, m)[0] + ".csv", f"{t},{fields},{close},x\n")
                    r["sha256"] = carry.digest(raw.read_bytes())
                    r[CLOCK] = int(wrong_clock)
            panel, counts = vault.load(root, roster)
            gap_start, gap_stop = [(month_info(m)[0] - gate.VAULT_START) // search.HOUR
                                   for m in ("2024-02", "2024-07")]
            zec = search.ALLOWED.index("ZEC")
            self.assertTrue(np.isnan(panel[zec, gap_start:gap_stop]).all())
            self.assertEqual(panel[zec, gap_stop, 0], 1)
            self.assertEqual(counts["archives_dropped_by_reason"], {"declared_absent_archive": 5})
            self.assertEqual(counts["rows_dropped_by_reason"], {CLOCK: 1})
            self.assertEqual(counts["rows_kept_by_coin"]["BTC"], 33)
            self.assertEqual(counts["rows_kept_by_coin"]["ZEC"], 29)

    def test_ticket_reconciliation_on_fabricated_search(self):
        coins = ["BTC", "ZEC"]
        rng = np.random.default_rng(33)
        close = 100 * np.exp(np.cumsum(rng.normal(0., .01, size=(2, len(search.HOURS))), axis=1))
        bars = np.repeat(close[:, :, None], 5, axis=2)
        rule = next(r for r in json.loads((search.HERE / "GRID_70.json").read_bytes()) if r["id"] == "70-102")
        t = search.Tape(coins, bars)
        fees = np.array([16.58, 15.26])
        r, _ = search.evaluate(t, rule, fees, SETTINGS["funding_adverse_bp_per_hour"],
                               SETTINGS["funding_stress_bp_per_hour"], SETTINGS["spot_taker_round_trip_bp"],
                               SETTINGS["search_marks"])
        r["finalist_rank"] = 1
        _, ix, net, reference, paired, _ = carry.reconcile(t, rule, fees, SETTINGS, r)
        self.assertEqual(r["trades"], len(ix))
        self.assertGreater(len(ix), 0)
        np.testing.assert_array_equal(net - reference, paired)
        with self.assertRaises(ValueError):
            carry.reconcile(t, rule, fees, SETTINGS, {**r, "paired_mean": 0})
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sweep_70").mkdir()
            carry.create_private(root, carry.VECTORS_REL, b"made-up")
            path = root / carry.VECTORS_REL
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            with self.assertRaises(FileExistsError):
                carry.create_private(root, carry.VECTORS_REL, b"refuse overwrite")


if __name__ == "__main__":
    unittest.main()
