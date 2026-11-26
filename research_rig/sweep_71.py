"""Plan 71 second grid. All custody actions are lead-only and independently pinned."""
import argparse
import json
import math
import re
import sys

import numpy as np

import carry_70 as custody
import sweep_70 as old
import vault_70 as sealed
from build_grid_71 import build, grid_bytes

GRID_PATH = "research_rig/GRID_71.json"
SEARCH_REL = "sweep_70/search71_summary.out"
PRIOR_CARRY_SHA = "6837579d1e6b805cb2c5aa679b2c7b6a75cc244c604c57c8b7c3a3f7ea4e09cf"
ANCHOR = "70-102"
ANCESTOR = "bcba79c3db5f707b1e02aceb7d864368fe7130a6"
EXTRA = (*custody.EXTRA, GRID_PATH, "research_rig/build_grid_71.py", "research_rig/sweep_71.py",
         "research_rig/follow_71.py")


def ticket_legs(tape, rule, costs, funding):
    delay, top = rule["delay_hours"], rule["top_coins"]
    if not delay and top == 1:
        coin, i, signs, net, ref, unresolved, adjust = old.ticket_legs(tape, rule, costs, funding)
        return coin[None, :], i, signs, net, ref, unresolved, adjust
    strength = old.score_signal(tape, rule)
    if delay:
        strength = old.shift(strength, delay)
    first, i = old.order_times(tape, rule, strength)
    # Stable coin ordering on known signal strengths, never on fill observability.
    if top == 2:
        ranks = np.argsort(-np.where(np.isfinite(strength[:, i]), strength[:, i], -np.inf),
                           axis=0, kind="stable")[:2].copy()
        if len(tape.coins) < 2:
            raise ValueError("basket requires at least two roster entries")
        ranks[1] = np.where(np.isfinite(strength[ranks[1], i]), ranks[1], -1)
    else:
        ranks = first[None, :]
    side, hold = rule["side"], rule["hold_hours"]
    gross, baseline = tape.fill(hold)
    valid = np.all((ranks < 0) | np.isfinite(gross[ranks, i]), axis=0)
    unresolved = int((~valid).sum())
    ranks, i = ranks[:, valid], i[valid]
    legs = ranks >= 0
    size = legs.sum(axis=0)
    signs = side * np.where(legs, gross[ranks, i], 0).sum(axis=0) / size
    fixed = np.where(legs, costs[ranks], 0).sum(axis=0) / size
    net = signs - (fixed + hold * funding) / 10000

    def adjust(which, loc):
        active = legs[:, loc]
        refs = baseline[which][ranks[:, loc], tape.clock[i[loc]]]
        return side * np.where(active, refs, 0).sum(axis=0) / size[loc]

    ref = adjust(0, np.ones(len(i), dtype=bool))
    if not np.all(np.isfinite(net)) or not np.all(np.isfinite(ref)):
        raise ValueError("missing full reference for resolved Plan 71 ticket")
    return ranks, i, signs, net, ref, unresolved, adjust


def cost_vector(config, coins):
    return np.array([config["futures_round_trip_bp"][c] for c in coins])


def evaluate(tape, rule, costs, config):
    return old.evaluate(tape, rule, costs, config["funding_adverse_bp_per_hour"],
                        config["funding_stress_bp_per_hour"], config["spot_taker_round_trip_bp"],
                        config["search_marks"], ticket_fn=ticket_legs)


def select(scored, anchors, marks):
    """Reserve prior places, allowing a stronger duplicate to inherit a place."""
    scored = [(r.copy(), d) for r, d in scored]
    qualifying = sorted(((r, d) for r, d in scored if r["meets_search_marks"]),
                        key=lambda x: (-x[0]["paired_day_t"], x[0]["rule"]))
    rank = lambda x: (-x[0]["paired_day_t"], x[0]["rule"])
    chosen, matched, replacements = [], set(), {}
    threshold = marks["duplicate_corr"]
    for anchor in anchors:
        duplicates = [x for x in qualifying if old.duplicate_corr(x[1], anchor[1]) > threshold]
        replacement = next((x for x in duplicates if x[0]["rule"] not in matched and rank(x) < rank(anchor)
                            and all(old.duplicate_corr(x[1], d) <= threshold for _, d in chosen)), None)
        owner = replacement if replacement is not None else anchor
        chosen.append(owner)
        replacements[anchor[0]["rule"]] = owner[0]["rule"]
        for row, _ in duplicates:
            rid = row["rule"]
            if rid not in matched and rid != owner[0]["rule"]:
                row["duplicate_of"] = anchor[0]["rule"]
            matched.add(rid)
    for row, daily in qualifying:
        if row["rule"] in matched:
            continue
        dup = next((r["rule"] for r, d in chosen if old.duplicate_corr(daily, d) > threshold), None)
        if dup is not None:
            row["duplicate_of"] = dup
        elif len(chosen) < marks["finalist_cap"]:
            chosen.append((row, daily))
    selected_ids = {r["rule"] for r, _ in scored}
    ordered = sorted(chosen, key=rank)
    n = 0
    for i, (row, _) in enumerate(ordered, 1):
        if row["rule"] in selected_ids:
            n += 1
            row["finalist_rank"] = n
            row["sweep_finalist_rank"] = i
    return [r for r, _ in scored], {"reserved_places": replacements,
                                     "sweep_finalists": [r["rule"] for r, _ in ordered]}


def acknowledge_anchor(root, old_rules, config, *, need_daily):
    summary = custody.pinned(root, custody.SEARCH_REL, custody.SEARCH_SHA)
    counts, chosen = custody.finalists(summary, old_rules, config["search_marks"]["finalist_cap"])
    receipt = json.loads(custody.pinned(root, custody.CARRY_REL, PRIOR_CARRY_SHA))
    if ([r["rule"] for r in chosen] != [ANCHOR] or receipt["carried_ids"] != []
            or receipt["search_summary_sha256"] != custody.SEARCH_SHA
            or receipt["search_freeze_commit"] != custody.SEARCH_FREEZE):
        raise ValueError("Plan 70 anchor identity differs from the frozen aggregate custody")
    raw = custody.pinned(root, custody.VECTORS_REL, receipt["vectors_sha256"], mode=0o600)
    obj = sealed.check_vectors(raw, old_rules, chosen)
    if not need_daily:
        return counts, None
    # Shape above is fixed and verified; only this one day's net sum per day survives.
    tickets = obj["rules"][0]["tickets"]
    day = [(t[1] - old.START) // 86400 for t in tickets]
    daily = np.bincount(day, weights=[t[3] for t in tickets], minlength=old.DAYS)
    if not np.all(np.isfinite(daily)):
        raise ValueError("invalid daily sums for the reserved place")
    return counts, (chosen[0], daily)


def load_inputs(root, config, old_grid, validation_only):
    counts, anchor = acknowledge_anchor(root, old_grid, config, need_daily=not validation_only)
    panel, observed = old.load_frozen(root, root / old.MANIFEST_REL, config)
    if counts != observed:
        raise ValueError("pinned search archive input counts differ from Plan 70")
    return panel, observed, anchor


def render(root, config, old_grid, new_grid, validation_only):
    panel, observed, anchor = load_inputs(root, config, old_grid, validation_only)
    if validation_only:
        return old.rows_bytes([{"input_counts": observed}])
    coins = config["coins"]
    tape = old.Tape(coins, panel)
    costs = cost_vector(config, coins)
    rows, selection = select([evaluate(tape, rule, costs, config) for rule in new_grid],
                             [anchor], config["search_marks"])
    return old.rows_bytes([{"input_counts": observed, **selection}, *rows])


def freeze(args):
    if not (sys.flags.ignore_environment and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null"):
        raise ValueError("required python -E -B -X pycache_prefix=/dev/null")
    if (args.grid_sha256, args.settings_sha256, args.search_summary_sha256) != (
            custody.GRID_SHA, custody.SETTINGS_SHA, custody.SEARCH_SHA):
        raise ValueError("old grid, settings or summary independently supplied pins differ")
    if not re.fullmatch("[0-9a-f]{64}", args.grid71_sha256 or ""):
        raise ValueError("independent second-grid SHA-256 required")
    blobs = old.checked_freeze(old.HERE.parent, args.freeze_commit, custody.GRID_SHA, custody.SETTINGS_SHA,
                               EXTRA, ancestor=ANCESTOR)
    config = old.parse_config(blobs[old.COVERAGE_PATH], blobs[old.SETTINGS_PATH], blobs[old.GRID_PATH])
    if config["private_manifest_sha256"] != custody.MANIFEST_SHA or tuple(config["coins"]) != old.ALLOWED:
        raise ValueError("search roster or custody pin differs")
    old_grid = json.loads(blobs[old.GRID_PATH])
    raw = blobs[GRID_PATH]
    if custody.digest(raw) != args.grid71_sha256 or raw != grid_bytes(build(old_grid)):
        raise ValueError("second grid differs from its digest or fixed builder")
    return config, old_grid, json.loads(raw)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    for flag in ("synthetic", "validate-inputs", "audited-search", "carry", "use-vault", "validate-vault-inputs"):
        mode.add_argument("--" + flag, action="store_true")
    for flag in ("freeze-commit", "grid-sha256", "grid71-sha256", "settings-sha256", "search-summary-sha256",
                 "search71-sha256", "carry71-sha256", "approval71-sha256", "vault-manifest-sha256"):
        p.add_argument("--" + flag)
    p.add_argument("--lead-authorize", action="store_true")
    args = p.parse_args()
    if args.synthetic:
        from synthetic_71 import synthetic_main
        synthetic_main()
        return
    if not args.lead_authorize:
        p.error("lead authorization is required")
    cfg, old_grid, new_grid = freeze(args)
    if args.validate_inputs or args.audited_search:
        data = render(old.CUSTODY, cfg, old_grid, new_grid, args.validate_inputs)
    else:
        from follow_71 import guarded_follow
        data = guarded_follow(old.CUSTODY, args, cfg, old_grid, new_grid)
    sys.stdout.buffer.write(data)


if __name__ == "__main__":
    main()
