"""Made-up fixtures, sequential 300-rule luck check, and fixed-rule power."""
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

import carry_70 as custody
import follow_71 as post
import sweep_70 as old
import sweep_71 as new
from build_grid_71 import build, grid_bytes, key
from synthetic_70 import COINS, close_clock_fixture, fake_panel, power_fixture, wire_panel


def make_row(rid, t, passing=True):
    return {"rule": rid, "paired_day_t": t, "meets_search_marks": passing,
            "duplicate_of": None, "finalist_rank": None}


def select_fixture(config):
    marks = config["search_marks"]
    base = np.tile([1., -1., 1., -1.], 100)
    orthogonal = np.tile([1., 1., -1., -1.], 100)
    anchor = (make_row("70-102", 3.51), base)
    low = (make_row("71-001", 3.50), base)
    tie = (make_row("71-002", 3.51), base)
    high = (make_row("71-003", 3.9), base)
    clear = (make_row("71-004", 4.1), orthogonal)
    rows, head = new.select([low, tie, clear], [anchor], marks)
    assert head["reserved_places"] == {"70-102": "70-102"}
    assert [r["duplicate_of"] for r in rows] == ["70-102", "70-102", None]
    rows, head = new.select([low, high, clear], [anchor], marks)
    assert head == {"reserved_places": {"70-102": "71-003"}, "sweep_finalists": ["71-004", "71-003"]}
    assert [r["finalist_rank"] for r in rows] == [None, 2, 1] and rows[0]["duplicate_of"] == "70-102"
    # Above 0.7 rather than inclusive, tested on either side of the threshold.
    for c in (.6999, .7001):
        candidate = (make_row("71-005", 3.9), c * base + np.sqrt(1 - c*c) * orthogonal)
        rows, head = new.select([candidate], [anchor], marks)
        assert (head["reserved_places"]["70-102"] == "71-005") == (c > .7)


def execution_fixture(config, grid):
    core = next(r for r in grid if not r["btc_hedge"] and r["top_coins"] == 1 and not r["delay_hours"]
                and r["side"] == 1 and r["hold_hours"] == 2 and r["parameters"]["lag"] == 2)
    rule = {**core, "parameters": {"lag": 2, "multiple": 2., "threshold": .015}}
    coins = ["ADA", "BTC", "ETH", "SOL"]
    tape_hours = old.HOURS[:48]
    bars = np.full((4, 48, 5), 100.)
    bars[:, 9, 3] *= np.exp([-.06, -.02, -.05, -.05])
    bars[:, 12, 0] = [104, 101, 102, 110]
    tape = old.Tape(coins, bars, hours=tape_hours, split=None)
    sig = old.score_signal(tape, rule)
    assert list(np.where(np.isfinite(sig[:, 10]))[0]) == [0, 2, 3]
    assert np.all(np.isnan(sig[:, :10]))
    costs = np.array([10., 20., 30., 40.])
    seq = np.full_like(sig, np.nan)
    seq[:, 10] = sig[:, 10]
    for form, at, expected_coin, gross, debit in (
        ({"delay_hours": 0, "top_coins": 2}, 10, [0, 2], .03, .0022),
        ({"delay_hours": 1, "top_coins": 1}, 11, [0], 0., .0012),
        ({"delay_hours": 0, "top_coins": 1, "btc_hedge": True}, 10, [0], .015, .0017)):
        with patch.object(old, "score_signal", return_value=seq):
            js, ix, signs, net, ref, unresolved, _ = new.ticket_legs(tape, {**rule, **form}, costs, 1.)
        assert ix.tolist() == [at] and js[:, 0].tolist() == expected_coin and not unresolved
        assert np.isclose(signs[0], gross) and np.isclose(net[0], gross - debit) and np.isfinite(ref[0])
    bars[2, 12, :] = np.nan
    with patch.object(old, "score_signal", return_value=seq):
        _, ix, _, _, _, unresolved, _ = new.ticket_legs(
            old.Tape(coins, bars, hours=tape_hours, split=None), {**rule, "top_coins": 2}, costs, 1.)
    assert not len(ix) and unresolved == 1  # No substitution from the third-ranked alt.
    mirror = bars.copy()
    mirror[:, 9, 3] = 10000 / mirror[:, 9, 3]
    short = old.score_signal(old.Tape(coins, mirror, hours=tape_hours, split=None), {**rule, "side": -1})
    assert np.array_equal(np.isfinite(short[:, 10]), np.isfinite(sig[:, 10]))


def guard_fixture(cfg):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "sweep_70").mkdir()
        a = SimpleNamespace(approval71_sha256="a" * 64, use_vault=True, validate_vault_inputs=False)
        with patch.object(new.sealed, "load", side_effect=AssertionError("no vault input allowed")) as load:
            try:
                post.use_vault(root, a, cfg, [])
            except FileNotFoundError:
                pass
            else:
                raise AssertionError("vault without signed approval was accepted")
            load.assert_not_called()
            assert list((root / "sweep_70").iterdir()) == []
        vector = {"columns": custody.VECTOR_COLUMNS, "rules": [{"rule": "70-102", "tickets": [
            ["ADA", old.START, old.START + 2 * old.HOUR, 0.01, 0.004, 0.006]]}]}
        raw = old.rows_bytes([vector])
        summary = old.rows_bytes([{"input_counts": {}}, {**make_row("70-102", 3.51),
                                 "finalist_rank": 1, "trades": 1, "active_days": 1}])
        receipt = old.rows_bytes([{"carried_ids": [], "search_summary_sha256": custody.SEARCH_SHA,
                                 "search_freeze_commit": custody.SEARCH_FREEZE, "vectors_sha256": custody.digest(raw)}])
        doc = {custody.SEARCH_REL: summary, custody.CARRY_REL: receipt, custody.VECTORS_REL: raw}
        grid = [{"id": "70-102", "hold_hours": 2}]
        with patch.object(custody, "pinned", side_effect=lambda _r, rel, *_a, **_k: doc[rel]) as reads:
            with patch.object(new.np, "bincount", side_effect=AssertionError("preflight derived returns")):
                _, anchor = new.acknowledge_anchor(root, grid, cfg, need_daily=False)
                assert anchor is None
            _, anchor = new.acknowledge_anchor(root, grid, cfg, need_daily=True)
            assert anchor[1][0] == .01 and np.count_nonzero(anchor[1]) == 1
            assert sum(c.args[1] == custody.VECTORS_REL for c in reads.call_args_list) == 2
        with (patch.object(new, "load_inputs", return_value=(None, {"counts": 1}, None)),
              patch.object(old, "Tape", side_effect=AssertionError("validation reached pricing"))):
            assert new.render(root, cfg, [], [], True) == old.rows_bytes([{"input_counts": {"counts": 1}}])
        summary_pin = custody.digest(summary)
        signed = old.rows_bytes([{"carried_ids": [], "search_summary_sha256": summary_pin,
                                "search_freeze_commit": custody.SEARCH_FREEZE, "vectors_sha256": custody.digest(raw)}])
        for rel, data in ((custody.SEARCH_REL, summary), (custody.CARRY_REL, signed)):
            (root / rel).write_bytes(data)
        vp = root / custody.VECTORS_REL
        vp.write_bytes(raw + b" ")
        vp.chmod(0o600)
        with (patch.object(custody, "SEARCH_SHA", summary_pin), patch.object(new, "PRIOR_CARRY_SHA", custody.digest(signed)),
              patch.object(old, "load_frozen", side_effect=AssertionError("archive before anchor auth")) as loader):
            for validation in (False, True):
                try:
                    new.render(root, cfg, grid, [], validation)
                except ValueError as exc:
                    assert "changed pinned input" in str(exc)
                else:
                    raise AssertionError("anchor mutation not refused")
            loader.assert_not_called()


def approved_vault_fixture(cfg):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "sweep_70").mkdir()
        rule = {"id": "71-001", "hold_hours": 2, "top_coins": 2}
        row = {**make_row("71-001", 3.7), "finalist_rank": 1, "sweep_finalist_rank": 2,
               "trades": 1, "active_days": 1}
        summary = old.rows_bytes([{"input_counts": {}, "reserved_places": {"70-102": "70-102"},
                                  "sweep_finalists": ["70-102", "71-001"]}, row])
        vectors = old.rows_bytes([{"columns": post.COLUMNS, "rules": [{"rule": "71-001", "tickets": [
            [["ADA", "ETH"], old.START, old.START + 2 * old.HOUR, .01, .005, .005]]}]}])
        man = old.rows_bytes([{}])
        args = SimpleNamespace(freeze_commit="test", grid_sha256=custody.GRID_SHA, grid71_sha256="new",
                               settings_sha256=custody.SETTINGS_SHA, search_summary_sha256=custody.SEARCH_SHA,
                               search71_sha256=custody.digest(summary), vault_manifest_sha256=custody.digest(man),
                               validate_vault_inputs=True)
        fixed = {**post.input_pins(args), "vectors_sha256": custody.digest(vectors), "carried_ids": ["71-001"]}
        receipt = old.rows_bytes([{**fixed, "forecasts": [{"rule": "71-001", "passes": 6600, "draws": 20000,
                                                            "seed": 702001, "probability": .33, "carry": True}]}])
        args.carry71_sha256 = custody.digest(receipt)
        approval = old.rows_bytes([{**fixed, "carry71_sha256": args.carry71_sha256,
                                    "vault_manifest_sha256": args.vault_manifest_sha256,
                                    "lead_authorizes_single_use": True}])
        args.approval71_sha256 = custody.digest(approval)
        for rel, data in ((new.SEARCH_REL, summary), (post.RECEIPT, receipt), (post.VECTORS, vectors),
                          (post.APPROVAL, approval), (new.sealed.MANIFEST, man)):
            custody.create_private(root, rel, data)

        def fake_load(*_):
            assert (root / new.sealed.LOCK).exists() is (not args.validate_vault_inputs)
            return None, {"kept": 1}

        with (patch.object(new.sealed, "VAULT_MANIFEST_SHA", args.vault_manifest_sha256),
              patch.object(new.sealed, "check_manifest"),
              patch.object(new.sealed, "load", side_effect=fake_load) as load,
              patch.object(old, "Tape", side_effect=RuntimeError("score stopped")) as price):
            assert post.use_vault(root, args, cfg, [rule]) == old.rows_bytes([{"input_counts": {"kept": 1}}])
            price.assert_not_called()
            args.validate_vault_inputs = False
            try:
                post.use_vault(root, args, cfg, [rule])
            except RuntimeError as exc:
                assert str(exc) == "score stopped"
            else:
                raise AssertionError("fake score did not stop")
            args.validate_vault_inputs = True
            try:
                post.use_vault(root, args, cfg, [rule])
            except FileExistsError:
                pass
            else:
                raise AssertionError("shared vault accepted a second invocation")
            assert load.call_count == 2


def synthetic_main():
    root = old.HERE.parent
    legacy_bytes = (root / old.GRID_PATH).read_bytes()
    legacy = json.loads(legacy_bytes)
    cfg = old.parse_config((root / old.COVERAGE_PATH).read_bytes(), (root / old.SETTINGS_PATH).read_bytes(), legacy_bytes)
    raw = (root / new.GRID_PATH).read_bytes()
    grid = json.loads(raw)
    assert raw == grid_bytes(build(legacy))
    assert len(grid) == 112 and len(grid) + len(legacy) == 300
    assert set(map(key, grid)).isdisjoint(key(r) for r in legacy if r["family"] == "btc_overextension_fade")
    close_clock_fixture()
    select_fixture(cfg)
    execution_fixture(cfg, grid)
    guard_fixture(cfg)
    approved_vault_fixture(cfg)
    costs = new.cost_vector(cfg, COINS)
    panel = fake_panel(70001, plant=True)
    fenced = wire_panel(panel, [f"{old.STOP*1000},poison,do,not,decode,price\n".encode()])
    t, other = old.Tape(COINS, panel), old.Tape(COINS, fenced)
    # The writer fixture rebuilds hourly bars and identical search rows from the same panel.
    a, b = [new.evaluate(t, r, costs, cfg)[0] for r in grid], [new.evaluate(other, r, costs, cfg)[0] for r in grid]
    assert old.rows_bytes(a) == old.rows_bytes(b)
    n_new = n_sweep = 0
    new_fail, combined_fail = [], []
    for seed in range(70100, 70200):
        panel = fake_panel(seed)
        tape = old.Tape(COINS, panel)
        prior = old.sweep(COINS, panel, legacy, costs, cfg)
        ranked = sorted((r for r in prior if r["finalist_rank"] is not None), key=lambda r: r["finalist_rank"])
        lookup = {r["id"]: r for r in legacy}
        anchors = [(r, old.evaluate(tape, lookup[r["rule"]], costs, cfg["funding_adverse_bp_per_hour"],
                    cfg["funding_stress_bp_per_hour"], cfg["spot_taker_round_trip_bp"], cfg["search_marks"])[1])
                   for r in ranked]
        hits = [new.evaluate(tape, r, costs, cfg) for r in grid]
        _, alone = new.select(hits, [], cfg["search_marks"])
        _, union = new.select(hits, anchors, cfg["search_marks"])
        n_new += not alone["sweep_finalists"]
        n_sweep += not union["sweep_finalists"]
        if alone["sweep_finalists"]:
            new_fail.append([seed, alone["sweep_finalists"]])
        if union["sweep_finalists"]:
            combined_fail.append([seed, union["sweep_finalists"]])
    out = {"seeds": 100, "grid_71_rules": len(grid), "combined_rules": len(grid) + len(legacy),
           "new_only_clean": n_new, "sequential_sweep_clean": n_sweep, "new_only_false_finalists": new_fail,
           "sweep_false_finalists": combined_fail, "fixed_rule_power": power_fixture(cfg),
           "mechanical_guards_passed": True, "post_cutoff_output_bytes_identical": True}
    print(json.dumps(out, indent=2, sort_keys=True))
    assert min(n_new, n_sweep) >= 95


if __name__ == "__main__":
    synthetic_main()
