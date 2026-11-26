"""Lead-only Plan 70 carry forecast; never opens vault bars."""
import argparse
import hashlib
import json
import os
import re
import sys

import numpy as np

import sweep_70 as search
from coverage_70 import exact_parent, read_snapshot
from vault_gate_70 import bootstrap

SEARCH_FREEZE = "96a0efdac14c57f0447f38fedac4f18d20aaae3f"
SEARCH_REL = "sweep_70/search_summary.out"
SEARCH_SHA = "13e5375a3ed8207eb07fee034af0d7fba088bebbdce951a234bbd61373a1b607"
GRID_SHA = "ac16d46df925a3270b55563b82d5bf1a5d0bd4b4840b45f57a3ce8a286dc5842"
SETTINGS_SHA = "91ec26101a503e196e9aad47168ba7ceaa9a0c9268a78418287897a821a6c1c2"
MANIFEST_SHA = "042ac622f7d083f52c0f8341b30c09c515154936200bcb81153e7e8e54bfa320"
CARRY_REL = "sweep_70/carry_results.json"
VECTORS_REL = "sweep_70/carry_tickets.json"
VECTOR_COLUMNS = ["coin", "entry_utc_seconds", "exit_utc_seconds", "plain_net", "reference", "matched_net"]
EXTRA = tuple("research_rig/" + s for s in ("carry_70.py", "vault_70.py", "vault_gate_70.py", "vault_census_70.py"))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(root, rel, sha, *, mode=None):
    if not re.fullmatch(r"[0-9a-f]{64}", sha or ""):
        raise ValueError(f"full independent SHA-256 required for {rel}")
    raw = read_snapshot(root, rel) if mode is None else read_snapshot(root, rel, mode=mode)
    if digest(raw) != sha:
        raise ValueError(f"changed pinned input: {rel}")
    return raw


def freeze_args(parser):
    for name in ("freeze-commit", "grid-sha256", "settings-sha256", "search-summary-sha256"):
        parser.add_argument("--" + name, required=True)


def freeze(args):
    if not (sys.flags.ignore_environment and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null"):
        raise ValueError("required python -E -B -X pycache_prefix=/dev/null")
    if (args.grid_sha256, args.settings_sha256, args.search_summary_sha256) != (GRID_SHA, SETTINGS_SHA, SEARCH_SHA):
        raise ValueError("pins differ from the authorized search")
    blobs = search.checked_freeze(search.HERE.parent, args.freeze_commit, GRID_SHA, SETTINGS_SHA,
                                  EXTRA, ancestor=SEARCH_FREEZE)
    config = search.parse_config(blobs[search.COVERAGE_PATH], blobs[search.SETTINGS_PATH], blobs[search.GRID_PATH])
    if config["private_manifest_sha256"] != MANIFEST_SHA or tuple(config["coins"]) != search.ALLOWED:
        raise ValueError("search custody pin or roster changed")
    return config, json.loads(blobs[search.GRID_PATH])


def finalists(raw, rules, cap):
    rows = [json.loads(line) for line in raw.splitlines()]
    if (len(rows) != len(rules) + 1 or set(rows[0]) != {"input_counts"}
            or [r["rule"] for r in rows[1:]] != [r["id"] for r in rules]):
        raise ValueError("search summary does not enumerate the exact grid")
    chosen = sorted((r for r in rows[1:] if r["finalist_rank"] is not None),
                    key=lambda r: r["finalist_rank"])
    if (len(chosen) > cap or [r["finalist_rank"] for r in chosen] != list(range(1, len(chosen) + 1))
            or any(not r["meets_search_marks"] or r["duplicate_of"] is not None for r in chosen)):
        raise ValueError("invalid finalist list")
    return rows[0]["input_counts"], chosen


def create_at(parent, name, raw):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
    with os.fdopen(fd, "wb") as wire:
        os.fchmod(wire.fileno(), 0o600)
        wire.write(raw)
        wire.flush()
        os.fsync(wire.fileno())
    os.fsync(parent)


def create_private(root, rel, raw):
    """Durable, exclusive mode-0600 output; no symlinks or alternate lock."""
    with exact_parent(root, rel) as (parent, name):
        create_at(parent, name, raw)


def reconcile(tape, rule, costs, config, frozen):
    funding = config["funding_adverse_bp_per_hour"]
    row, _ = search.evaluate(tape, rule, costs, funding, config["funding_stress_bp_per_hour"],
                             config["spot_taker_round_trip_bp"], config["search_marks"])
    if row != {**frozen, "finalist_rank": None}:
        raise ValueError(f"finalist differs from audited search: {rule['id']}")
    coin, ix, _, net, reference, unresolved, _ = search.ticket_legs(tape, rule, costs, funding)
    paired = net - reference
    day = (tape.hours[ix] - search.START) // 86400
    if (not len(ix) or len(ix) != frozen["trades"] or np.unique(day).size != frozen["active_days"]
            or unresolved != frozen["unresolved_selected_tickets"] or np.any(np.diff(ix) <= 0)
            or tape.hours[ix[-1]] + rule["hold_hours"] * search.HOUR >= search.STOP
            or tape.hours[ix[0]] < search.START
            or net.mean() != frozen["plain_mean"] or paired.mean() != frozen["paired_mean"]):
        raise ValueError(f"unreconciled search ticket vectors: {rule['id']}")
    return coin, ix, net, reference, paired, day


def run(root, config, rules, summary, freeze_commit):
    counts, chosen = finalists(summary, rules, config["search_marks"]["finalist_cap"])
    forecasts, vectors = [], []
    if chosen:
        panel, actual = search.load_frozen(root, root / search.MANIFEST_REL, config)
        if counts != actual:
            raise ValueError("search loader counts differ from frozen summary")
        coins = config["coins"]
        tape = search.Tape(coins, panel)
        costs = np.array([config["futures_round_trip_bp"][c] for c in coins])
        by_id = {r["id"]: r for r in rules}
        for frozen in chosen:
            rule = by_id[frozen["rule"]]
            js, ix, net, reference, paired, day = reconcile(tape, rule, costs, config, frozen)
            vectors.append({"rule": rule["id"], "tickets": [
                [coins[j], int(tape.hours[i]), int(tape.hours[i]) + rule["hold_hours"] * search.HOUR,
                 float(n), float(r), float(p)] for j, i, n, r, p in zip(js, ix, net, reference, paired)]})
            forecasts.append(bootstrap(rule["id"], net, paired, day, config))
    details = search.rows_bytes([{"columns": VECTOR_COLUMNS, "rules": vectors}])
    receipt = {"search_freeze_commit": SEARCH_FREEZE, "runner_freeze_commit": freeze_commit,
               "search_summary_sha256": digest(summary), "search_manifest_sha256": MANIFEST_SHA,
               "grid_sha256": GRID_SHA, "settings_sha256": SETTINGS_SHA,
               "vectors_sha256": digest(details) if chosen else None, "forecasts": forecasts,
               "carried_ids": [r["rule"] for r in forecasts if r["carry"]]}
    if chosen:
        create_private(root, VECTORS_REL, details)
    create_private(root, CARRY_REL, search.rows_bytes([receipt]))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    freeze_args(parser)
    parser.add_argument("--lead-authorize-carry", action="store_true", required=True)
    args = parser.parse_args()
    config, rules = freeze(args)
    summary = pinned(search.CUSTODY, SEARCH_REL, args.search_summary_sha256)
    sys.stdout.buffer.write(search.rows_bytes([run(search.CUSTODY, config, rules, summary, args.freeze_commit)]))


if __name__ == "__main__":
    main()
