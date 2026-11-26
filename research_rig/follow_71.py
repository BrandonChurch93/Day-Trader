"""Lead-only Plan 71 carry and authorization for the same single-use vault."""
import json
import math
import re

import numpy as np

import carry_70 as custody
import sweep_70 as old
import sweep_71 as new
import vault_70 as sealed
from vault_gate_70 import VAULT_HOURS, VAULT_START, bootstrap, marks

RECEIPT = "sweep_70/carry71_results.json"
VECTORS = "sweep_70/carry71_tickets.json"
APPROVAL = "sweep_70/vault71_approval.json"
COLUMNS = ["non_btc_legs", "entry_utc_seconds", "exit_utc_seconds", "plain_net", "reference", "matched_net"]


def accepted_search(root, args, config, grid):
    raw = custody.pinned(root, new.SEARCH_REL, args.search71_sha256)
    head, *rows = map(json.loads, raw.splitlines())
    if (set(head) != {"input_counts", "reserved_places", "sweep_finalists"}
            or [r["rule"] for r in rows] != [r["id"] for r in grid]
            or set(head["reserved_places"]) != {new.ANCHOR}):
        raise ValueError("not the pin's exact Plan 71 search grid and reservation")
    chosen = sorted((r for r in rows if r["finalist_rank"] is not None), key=lambda r: r["finalist_rank"])
    final_ids = head["sweep_finalists"]
    if (not 1 <= len(final_ids) <= config["search_marks"]["finalist_cap"]
            or head["reserved_places"][new.ANCHOR] not in final_ids
            or len(set(final_ids)) != len(final_ids)
            or [r["finalist_rank"] for r in chosen] != list(range(1, len(chosen) + 1))
            or [r["rule"] for r in chosen] != [rid for rid in final_ids if rid != new.ANCHOR]
            or any(not r["meets_search_marks"] or r["duplicate_of"] is not None
                   or final_ids.index(r["rule"]) + 1 != r["sweep_finalist_rank"] for r in chosen)):
        raise ValueError("Plan 71 finalist list does not respect sweep places")
    return head["input_counts"], chosen


def input_pins(args):
    return {"runner_freeze_commit": args.freeze_commit, "grid_sha256": args.grid_sha256,
            "grid71_sha256": args.grid71_sha256, "settings_sha256": args.settings_sha256,
            "search_summary_sha256": args.search_summary_sha256, "search71_sha256": args.search71_sha256,
            "prior_carry_sha256": new.PRIOR_CARRY_SHA, "search_manifest_sha256": custody.MANIFEST_SHA}


def carry_run(root, args, cfg, old_grid, grid):
    expected, chosen = accepted_search(root, args, cfg, grid)
    forecasts, vectors = [], []
    if chosen:
        panel, counts, _ = new.load_inputs(root, cfg, old_grid, True)
        if counts != expected:
            raise ValueError("Plan 71 search loader counts differ")
        coins = cfg["coins"]
        tape = old.Tape(coins, panel)
        costs = new.cost_vector(cfg, coins)
        by_id = {r["id"]: r for r in grid}
        for row in chosen:
            rule = by_id[row["rule"]]
            actual, _ = new.evaluate(tape, rule, costs, cfg)
            want = {k: v for k, v in row.items() if k != "sweep_finalist_rank"}
            if actual != {**want, "finalist_rank": None}:
                raise ValueError("Plan 71 finalist summary fails reconciliation")
            js, ix, _, net, ref, unresolved, _ = new.ticket_legs(
                tape, rule, costs, cfg["funding_adverse_bp_per_hour"])
            paired = net - ref
            day = (tape.hours[ix] - old.START) // 86400
            if (not len(ix) or len(ix) != row["trades"] or np.unique(day).size != row["active_days"]
                    or unresolved != row["unresolved_selected_tickets"] or np.any(np.diff(ix) <= 0)
                    or tape.hours[ix[-1]] + rule["hold_hours"] * old.HOUR >= old.STOP
                    or tape.hours[ix[0]] < old.START or not np.all(np.isfinite(paired))
                    or net.mean() != row["plain_mean"] or paired.mean() != row["paired_mean"]):
                raise ValueError("Plan 71 finalist vectors fail reconciliation")
            vectors.append({"rule": rule["id"], "tickets": [
                [[coins[j] for j in legs if j >= 0], int(tape.hours[i]),
                 int(tape.hours[i]) + rule["hold_hours"] * old.HOUR, float(n), float(r), float(m)]
                for legs, i, n, r, m in zip(js.T, ix, net, ref, paired)]})
            forecasts.append(bootstrap(rule["id"], net, paired, day, cfg))
    raw = old.rows_bytes([{"columns": COLUMNS, "rules": vectors}])
    receipt = {**input_pins(args), "vectors_sha256": custody.digest(raw) if chosen else None,
               "forecasts": forecasts, "carried_ids": [r["rule"] for r in forecasts if r["carry"]]}
    if chosen:
        custody.create_private(root, VECTORS, raw)
    data = old.rows_bytes([receipt])
    custody.create_private(root, RECEIPT, data)
    return data


def vector_shape(raw, chosen, grid):
    obj = json.loads(raw)
    rules = {r["id"]: r for r in grid}
    if (not isinstance(obj, dict) or set(obj) != {"columns", "rules"} or obj["columns"] != COLUMNS
            or not isinstance(obj["rules"], list) or len(obj["rules"]) != len(chosen)):
        raise ValueError("bad Plan 71 carry vector shape")
    for row, vector in zip(chosen, obj["rules"]):
        if (not isinstance(vector, dict) or set(vector) != {"rule", "tickets"}
                or vector["rule"] != row["rule"] or not isinstance(vector["tickets"], list)
                or len(vector["tickets"]) != row["trades"] or not vector["tickets"]):
            raise ValueError("bad Plan 71 carry vector identity or count")
        rule = rules[row["rule"]]
        next_open, days = old.START, set()
        for t in vector["tickets"]:
            if not isinstance(t, list) or len(t) != len(COLUMNS):
                raise ValueError("bad Plan 71 carry ticket fields")
            basket, entry, exit, *values = t
            if (not isinstance(basket, list) or not 1 <= len(basket) <= rule["top_coins"]
                    or any(c not in old.ALLOWED or c == "BTC" for c in basket)
                    or len(set(basket)) != len(basket) or type(entry) is not int or type(exit) is not int
                    or entry < next_open or entry % old.HOUR or exit >= old.STOP
                    or exit - entry != rule["hold_hours"] * old.HOUR
                    or any(type(x) is not float or not math.isfinite(x) for x in values)):
                raise ValueError("invalid Plan 71 carry ticket or clock")
            next_open = exit
            days.add(entry // 86400)
        if len(days) != row["active_days"]:
            raise ValueError("bad Plan 71 carry date count")


def vault_commitment(root, args, cfg, grid):
    # Presence and independent digest of this lead-written file are mandatory.
    approval = json.loads(custody.pinned(root, APPROVAL, args.approval71_sha256))
    _, chosen = accepted_search(root, args, cfg, grid)
    receipt = json.loads(custody.pinned(root, RECEIPT, args.carry71_sha256, mode=0o600))
    fixed = input_pins(args)
    if (any(receipt[k] != v for k, v in fixed.items())
            or [r["rule"] for r in receipt["forecasts"]] != [r["rule"] for r in chosen]
            or not re.fullmatch(r"[0-9a-f]{64}", receipt["vectors_sha256"] or "")):
        raise ValueError("Plan 71 carry receipt differs from the frozen search")
    supported = []
    for row in receipt["forecasts"]:
        draws = cfg["vault_power"]["draws"]
        if type(row["passes"]) is not int or not 0 <= row["passes"] <= draws:
            raise ValueError("invalid Plan 71 carry count")
        prob = row["passes"] / draws
        keep = prob >= cfg["vault_marks"]["min_pre_vault_power"]
        if (row["draws"] != draws or row["seed"] != cfg["vault_power"]["seed_base"] + int(row["rule"][3:])
                or row["probability"] != prob or row["carry"] is not keep):
            raise ValueError("invalid Plan 71 carry forecast")
        if keep:
            supported.append(row["rule"])
    if not supported or receipt["carried_ids"] != supported:
        raise ValueError("Plan 71 vault stays sealed without a nonempty accepted carry")
    lock = {**fixed, "carry71_sha256": args.carry71_sha256, "vault_manifest_sha256": args.vault_manifest_sha256,
            "carried_ids": supported, "vectors_sha256": receipt["vectors_sha256"]}
    if approval.get("lead_authorizes_single_use") is not True or approval != {**lock, "lead_authorizes_single_use": True}:
        raise ValueError("lead approval does not authorize this exact Plan 71 vault use")
    vector_shape(custody.pinned(root, VECTORS, lock["vectors_sha256"], mode=0o600), chosen, grid)
    return {**lock, "approval71_sha256": args.approval71_sha256}


def use_vault(root, args, cfg, grid):
    with sealed.unused_vault(root) as (parent, name):
        record = vault_commitment(root, args, cfg, grid)
        if args.vault_manifest_sha256 != sealed.VAULT_MANIFEST_SHA:
            raise ValueError("vault manifest differs from the frozen census pin")
        roster = json.loads(custody.pinned(root, sealed.MANIFEST, args.vault_manifest_sha256))
        sealed.check_manifest(roster)
        if not args.validate_vault_inputs:
            custody.create_at(parent, name, old.rows_bytes([record]))
        panel, counts = sealed.load(root, roster)
        head = {"input_counts": counts}
        if args.validate_vault_inputs:
            return old.rows_bytes([head])
        coins = cfg["coins"]
        tape = old.Tape(coins, panel, hours=VAULT_HOURS, split=None)
        costs = new.cost_vector(cfg, coins)
        results = [head]
        for rid in record["carried_ids"]:
            rule = next(r for r in grid if r["id"] == rid)
            _, ix, _, net, ref, unresolved, _ = new.ticket_legs(tape, rule, costs, cfg["funding_adverse_bp_per_hour"])
            day = (VAULT_HOURS[ix] - VAULT_START) // 86400
            results.append({"rule": rid, "family": rule["family"], "unresolved_selected_tickets": unresolved,
                            **marks(net, net - ref, day, cfg["vault_marks"])})
        return old.rows_bytes(results)


def guarded_follow(root, args, cfg, old_grid, grid):
    if args.carry:
        return carry_run(root, args, cfg, old_grid, grid)
    return use_vault(root, args, cfg, grid)
