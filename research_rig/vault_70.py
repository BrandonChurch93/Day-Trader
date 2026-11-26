"""Lead-only Plan 70 vault, with a durable single-use scoring lock."""
import argparse
import json
import re
import sys
from io import BytesIO
from zipfile import ZipFile

import numpy as np

import carry_70 as carry
import sweep_70 as search
from coverage_70 import WRONG_CLOSE_CLOCK, read_snapshot
from vault_census_70 import MANIFEST, MONTHS, archive_info, month_info
from vault_gate_70 import VAULT_HOURS, VAULT_START, VAULT_STOP, marks

APPROVAL = "sweep_70/vault_approval.json"
LOCK = "sweep_70/vault_used.lock"
VAULT_MANIFEST_SHA = "eef9e0fcacaec3eb3801d41ee8b3b0555f944101b2a63149d6640b545e3f88a2"
ABSENT_REASON = "declared_absent_archive"
DECLARED_ABSENT = frozenset(("ZEC", f"2024-{m:02}") for m in range(2, 7))


def check_manifest(roster):
    if set(roster) != set(search.ALLOWED):
        raise ValueError("vault manifest roster differs")
    absence = set()
    for coin in search.ALLOWED:
        rows = roster[coin]
        if tuple(r["month"] for r in rows) != MONTHS:
            raise ValueError("vault manifest must list each fixed month in order")
        for row in rows:
            tag = row["month"]
            if row.get("missing_archive") is True:
                if set(row) != {"month", "missing_archive"}:
                    raise ValueError("bad absent-archive record")
                absence.add((coin, tag))
                continue
            first, hours, _ = month_info(tag)
            if (set(row) != {"month", "path", "sha256", "rows", "expected", "wrong_close_clock",
                             "first_utc_seconds", "last_utc_seconds"}
                    or row["path"] not in archive_info(coin, tag)[1]
                    or not re.fullmatch("[0-9a-f]{64}", row["sha256"])
                    or row["expected"] != hours or not 0 <= row["wrong_close_clock"] <= row["rows"] <= hours
                    or not row["rows"]
                    or not first <= row["first_utc_seconds"] <= row["last_utc_seconds"] < first + hours * search.HOUR
                    or any(row[k] % search.HOUR for k in ("first_utc_seconds", "last_utc_seconds"))):
                raise ValueError("malformed or out-of-fence vault manifest record")
    if absence != DECLARED_ABSENT:
        raise ValueError("vault archive absences differ from the five declared ZEC months")


def load(root, roster):
    check_manifest(roster)
    coins = search.ALLOWED
    panel = np.full((len(coins), len(VAULT_HOURS), 5), np.nan)
    kept, bad, absent = (dict.fromkeys(coins, 0) for _ in range(3))
    for j, coin in enumerate(coins):
        for record in roster[coin]:
            if record.get("missing_archive"):
                absent[coin] += 1
                continue
            month = record["month"]
            name, _ = archive_info(coin, month)
            first, hours, ticks = month_info(month)
            stop = first + hours * search.HOUR
            base = (first - VAULT_START) // search.HOUR
            raw = carry.pinned(root, record["path"], record["sha256"])
            physical = set()
            dropped = 0
            with ZipFile(BytesIO(raw)) as z, z.open(name + ".csv") as wire:
                for i, row in search.read_hour_rows(wire, first, stop, ticks):
                    if i in physical:
                        raise ValueError("duplicate physical vault row")
                    physical.add(i)
                    if row is None:
                        dropped += 1
                    else:
                        panel[j, base + i] = row
                        kept[coin] += 1
            if (len(physical) != record["rows"] or dropped != record["wrong_close_clock"]
                    or first + min(physical) * search.HOUR != record["first_utc_seconds"]
                    or first + max(physical) * search.HOUR != record["last_utc_seconds"]):
                raise ValueError("vault opening or closing clock counts changed")
            bad[coin] += dropped
    return panel, {"rows_kept_by_coin": kept,
                   "rows_dropped_by_reason": {WRONG_CLOSE_CLOCK: sum(bad.values())},
                   "rows_dropped_by_reason_and_coin": {WRONG_CLOSE_CLOCK: bad},
                   "archives_dropped_by_reason": {ABSENT_REASON: sum(absent.values())},
                   "archives_dropped_by_reason_and_coin": {ABSENT_REASON: absent}}


def commitment(args, config, rules, summary, receipt, approval):
    _, chosen = carry.finalists(summary, rules, config["search_marks"]["finalist_cap"])
    if (receipt["search_freeze_commit"] != carry.SEARCH_FREEZE
            or receipt["runner_freeze_commit"] != args.freeze_commit
            or receipt["search_summary_sha256"] != args.search_summary_sha256
            or receipt["search_manifest_sha256"] != carry.MANIFEST_SHA
            or receipt["grid_sha256"] != args.grid_sha256 or receipt["settings_sha256"] != args.settings_sha256
            or not re.fullmatch("[0-9a-f]{64}", receipt["vectors_sha256"] or "")
            or [f["rule"] for f in receipt["forecasts"]] != [r["rule"] for r in chosen]):
        raise ValueError("carry record does not match the signed search and current freeze")
    expected = []
    for row in receipt["forecasts"]:
        draws = config["vault_power"]["draws"]
        seed = config["vault_power"]["seed_base"] + int(row["rule"].split("-")[1])
        p = row["passes"] / draws
        if (type(row["passes"]) is not int or not 0 <= row["passes"] <= draws or row["draws"] != draws
                or row["seed"] != seed or row["probability"] != p
                or row["carry"] is not (p >= config["vault_marks"]["min_pre_vault_power"])):
            raise ValueError("invalid fixed carry forecast")
        if row["carry"]:
            expected.append(row["rule"])
    if not expected or receipt["carried_ids"] != expected or args.carried_id != expected:
        raise ValueError("requires the exact nonempty carried IDs, in rank order")
    record = {"runner_freeze_commit": args.freeze_commit, "search_freeze_commit": carry.SEARCH_FREEZE,
              "grid_sha256": args.grid_sha256, "settings_sha256": args.settings_sha256,
              "search_summary_sha256": args.search_summary_sha256, "search_manifest_sha256": carry.MANIFEST_SHA,
              "carry_sha256": args.carry_sha256, "vault_manifest_sha256": args.vault_manifest_sha256,
              "vectors_sha256": receipt["vectors_sha256"], "carried_ids": expected}
    if (approval.get("lead_authorizes_single_use") is not True
            or approval != {**record, "lead_authorizes_single_use": True}):
        raise ValueError("lead sign-off does not match the pinned run")
    return {**record, "approval_sha256": args.approval_sha256}


def score(panel, config, rules, ids):
    coins = config["coins"]
    tape = search.Tape(coins, panel, hours=VAULT_HOURS, split=None)
    costs = np.array([config["futures_round_trip_bp"][c] for c in coins])
    by_id = {r["id"]: r for r in rules}
    for rid in ids:
        rule = by_id[rid]
        _, ix, _, net, reference, unresolved, _ = search.ticket_legs(
            tape, rule, costs, config["funding_adverse_bp_per_hour"])
        day = (VAULT_HOURS[ix] - VAULT_START) // 86400
        yield {"rule": rid, "family": rule["family"], "unresolved_selected_tickets": unresolved,
               **marks(net, net - reference, day, config["vault_marks"])}


def dispatch(root, args, config, rules):
    summary = carry.pinned(root, carry.SEARCH_REL, args.search_summary_sha256)
    receipt = json.loads(carry.pinned(root, carry.CARRY_REL, args.carry_sha256))
    approval = json.loads(carry.pinned(root, APPROVAL, args.approval_sha256))
    lock = commitment(args, config, rules, summary, receipt, approval)
    roster = json.loads(carry.pinned(root, MANIFEST, args.vault_manifest_sha256))
    check_manifest(roster)
    if not args.validate_inputs:
        # Never open even the first archive until file and directory are synced.
        carry.create_private(root, LOCK, search.rows_bytes([lock]))
    panel, counts = load(root, roster)
    header = {"input_counts": counts}
    if args.validate_inputs:
        return search.rows_bytes([header])
    return search.rows_bytes([header, *score(panel, config, rules, lock["carried_ids"])])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    carry.freeze_args(parser)
    for pin in ("carry-sha256", "vault-manifest-sha256", "approval-sha256"):
        parser.add_argument("--" + pin, required=True)
    parser.add_argument("--carried-id", action="append", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-inputs", action="store_true")
    mode.add_argument("--use-vault", action="store_true")
    args = parser.parse_args()
    config, rules = carry.freeze(args)
    if args.vault_manifest_sha256 != VAULT_MANIFEST_SHA:
        raise ValueError("pin differs from the frozen timestamp-only vault census")
    sys.stdout.buffer.write(dispatch(search.CUSTODY, args, config, rules))


if __name__ == "__main__":
    main()
