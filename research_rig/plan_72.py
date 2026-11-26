"""Lead-only staged Plan 72 runner. Offline test mode never touches custody or network."""
import argparse
from contextlib import contextmanager
import fcntl
import json
import math
import os
import re
import subprocess
import sys

import carry_70 as p70
import sweep_70 as old
import sweep_71 as p71
import follow_71 as follow
import coinbase_72 as feed
import model_72 as model
from coverage_70 import exact_parent

BASE = "e47a8db3fee6108e5d16298a8ac23d15fe4f5ad3"
CONFIG = "research_rig/CONFIG_72.json"
PLAN = "minute_plan.json"
APPROVAL = "go_approval.json"
LOCK = "go.lock"
SEARCH71_SHA = "babd3544e7ae86bd13b9cbfeca7b4d3b72ee8b33fda4492c6ef6fab1a2dd5558"
CARRY71_SHA = "843d20afbe0b0d5822a6cb899bfdbd6714b96ac2832be5b02f4fd66391437930"
GRID71_SHA = "c41aa5189ca406a26fac733cc08f36e05d5af6a0d86e5afc192adf4cfb34efb5"
EXTRA = tuple(dict.fromkeys((*p71.EXTRA, CONFIG, "research_rig/coinbase_72.py", "research_rig/model_72.py",
                            "research_rig/plan_72.py")))


def freeze(args):
    if not args.lead_authorize or not (sys.flags.ignore_environment and sys.dont_write_bytecode
                                       and sys.pycache_prefix == "/dev/null"):
        raise ValueError("need lead authorization and python -E -B -X pycache_prefix=/dev/null")
    if (args.grid_sha256, args.grid71_sha256) != (p70.GRID_SHA, GRID71_SHA):
        raise ValueError("the inherited rule grid pins differ")
    if not re.fullmatch("[0-9a-f]{64}", args.config_sha256 or ""):
        raise ValueError("independent Plan 72 config pin required")
    repo = old.HERE.parent
    blobs = old.checked_freeze(repo, args.freeze_commit, p70.GRID_SHA, args.settings_sha256, EXTRA, ancestor=BASE)
    if p70.digest(blobs[CONFIG]) != args.config_sha256 or p70.digest(blobs[p71.GRID_PATH]) != GRID71_SHA:
        raise ValueError("Plan 72 config or Plan 71 grid differs from pin")
    earlier = json.loads(blobs[old.GRID_PATH])
    later = json.loads(blobs[p71.GRID_PATH])
    specs = {r["id"]: r for r in (*earlier, *later) if r["id"] in (model.PRIMARY, *model.SHOWN)}
    if set(specs) != {model.PRIMARY, *model.SHOWN} or any(r["side"] != 1 or r["btc_hedge"] for r in specs.values()):
        raise ValueError("unexpected fixed rule list")
    fees = inherited_fees(repo, blobs)
    cfg = json.loads(blobs[CONFIG])
    if not set(cfg["sources"]) <= set(old.ALLOWED) or not 0.5 <= cfg["request_delay_seconds"] <= 5.:
        raise ValueError("unapproved source or request pace")
    return cfg, fees, later, specs


def inherited_fees(repo, blobs):
    fees = old.parse_config(blobs[old.COVERAGE_PATH], blobs[old.SETTINGS_PATH], blobs[old.GRID_PATH])
    git_env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    git_env["GIT_NO_REPLACE_OBJECTS"] = "1"
    original_settings = subprocess.check_output(["git", "--no-optional-locks", "-C", str(repo), "show",
                                                  f"{p70.SEARCH_FREEZE}:{old.SETTINGS_PATH}"], env=git_env)
    if (p70.digest(original_settings) != p70.SETTINGS_SHA
            or fees != old.parse_config(blobs[old.COVERAGE_PATH], original_settings, blobs[old.GRID_PATH])):
        raise ValueError("the inherited Plan 70 settings section differs from its original freeze")
    return fees


def authority(args):
    return {"runner_freeze_commit": args.freeze_commit, "config_sha256": args.config_sha256,
            "settings_sha256": args.settings_sha256, "grid_sha256": args.grid_sha256,
            "grid71_sha256": args.grid71_sha256, "search71_sha256": SEARCH71_SHA, "carry71_sha256": CARRY71_SHA}


def prior_summary(root, grid, *, economics=False):
    raw = p70.pinned(root, p71.SEARCH_REL, SEARCH71_SHA)
    _, *rows = map(json.loads, raw.splitlines())
    chosen = sorted((r for r in rows if r["finalist_rank"] is not None), key=lambda r: r["finalist_rank"])
    if ([r["rule"] for r in rows] != [r["id"] for r in grid]
            or [r["rule"] for r in chosen] != ["71-035", model.PRIMARY]):
        raise ValueError("prior Plan 71 summary does not match the judged rule")
    identities = [{k: row[k] for k in ("rule", "trades", "active_days")} for row in chosen]
    mean = next(r["plain_mean"] for r in chosen if r["rule"] == model.PRIMARY) if economics else None
    if economics and (type(mean) not in (int, float) or not math.isfinite(mean)):
        raise ValueError("prior Plan 71 summary lacks a finite judged plain mean")
    return identities, mean


def old_tickets(root, later, chosen, *, economics):
    receipt = json.loads(p70.pinned(root, follow.RECEIPT, CARRY71_SHA, mode=0o600))
    if (receipt["search71_sha256"] != SEARCH71_SHA or receipt["grid71_sha256"] != GRID71_SHA
            or receipt["carried_ids"] or [r["rule"] for r in receipt["forecasts"]] != [r["rule"] for r in chosen]):
        raise ValueError("prior frozen Plan 71 carry receipt differs")
    raw = p70.pinned(root, follow.VECTORS, receipt["vectors_sha256"], mode=0o600)
    obj = follow.vector_shape(raw, chosen, later)
    ts = next(row["tickets"] for row in obj["rules"] if row["rule"] == model.PRIMARY)
    out = []
    for legs, entry, exit, net, _, _ in ts:
        if len(legs) != 1 or not feed.DIAG[0] <= entry < exit < feed.DIAG[1]:
            raise ValueError("not a valid search-only 71-013 ticket")
        out.append([legs[0], entry, exit, net] if economics else [legs[0], entry, exit])
    return out


def load_hourly(root, args, cfg):
    return feed.load(root, "hourly", args.hourly_manifest_sha256, model.hourly_jobs(cfg), authority(args))


def check_tickets(tickets, allowed, hold, fence):
    next_allowed = fence[0]
    if not isinstance(tickets, list):
        raise ValueError("invalid minute plan ticket list")
    for t in tickets:
        if not isinstance(t, list) or len(t) != 3:
            raise ValueError("invalid minute plan ticket shape")
        coin, a, b = t
        if (coin not in allowed or coin == "BTC" or type(a) is not int or type(b) is not int
                or a % feed.HOUR or not next_allowed <= a < b < fence[1] or b-a != hold*feed.HOUR):
            raise ValueError("minute plan ticket outside its fixed venue/time/hold fence")
        next_allowed = b


def canonical_plan(root, prior_root, args, cfg, earlier, specs):
    batch = load_hourly(root, args, cfg)
    hours, starts = model.activated(batch, cfg)
    fresh = model.schedule(hours, specs)
    chosen, _ = prior_summary(prior_root, earlier)
    diag = old_tickets(prior_root, earlier, chosen, economics=False)
    jobs = model.window_jobs(fresh, diag, cfg)
    counts = model.count_fields(fresh[model.PRIMARY])
    plan = {"binding": {**authority(args), "hourly_manifest_sha256": args.hourly_manifest_sha256},
            "first_full_day": starts, "fresh": fresh, "diagnostic": diag, "counts": counts,
            "requests": jobs, "request_count": len(jobs), "minute_requests": sum(j[1] == feed.MINUTE for j in jobs)}
    return plan


def build_plan(root, prior_root, args, cfg, earlier, specs):
    plan = canonical_plan(root, prior_root, args, cfg, earlier, specs)
    p70.create_private(root, PLAN, feed.lines(plan))
    return plan["counts"]


def read_plan(root, args, cfg, specs):
    raw = p70.pinned(root, PLAN, args.plan_sha256, mode=0o600)
    plan = json.loads(raw)
    if (plan["binding"] != {**authority(args), "hourly_manifest_sha256": args.hourly_manifest_sha256}
            or set(plan["fresh"]) != set(specs)
            or set(plan["first_full_day"]) != set(cfg["sources"])):
        raise ValueError("minute plan does not match the manifest, roster and freeze")
    for rid, tickets in plan["fresh"].items():
        check_tickets(tickets, cfg["sources"], specs[rid]["hold_hours"], feed.FRESH)
    check_tickets(plan["diagnostic"], old.ALLOWED, specs[model.PRIMARY]["hold_hours"], feed.DIAG)
    jobs = model.window_jobs(plan["fresh"], plan["diagnostic"], cfg)
    if (jobs != [tuple(j) for j in plan["requests"]] or plan["request_count"] != len(jobs)
            or plan["minute_requests"] != sum(j[1] == feed.MINUTE for j in jobs)
            or plan["counts"] != model.count_fields(plan["fresh"][model.PRIMARY])):
        raise ValueError("minute request count, exact union or schedule differs")
    return plan, jobs, raw


def marks_checked(m):
    ints = ("positive_years", "min_tickets", "min_days")
    if (not isinstance(m, dict) or set(m) != {*ints, "matched_t", "trim_share"}
            or any(type(m[k]) is not int or m[k] < 1 for k in ints) or m["positive_years"] > 3
            or any(type(m[k]) not in (int, float) or not math.isfinite(m[k]) for k in ("matched_t", "trim_share"))
            or not 0. < m["matched_t"] or not 0. < m["trim_share"] < 1.):
        raise ValueError("invalid lead-fixed marks")
    return m


def design_power(plan, cfg, m, prev_mean):
    return model.power(plan["fresh"][model.PRIMARY], prev_mean * cfg["power"]["mean_multiplier"], cfg, m)


def approve(root, args, cfg, plan):
    doc = json.loads(p70.pinned(root, APPROVAL, args.approval_sha256, mode=0o600))
    m = marks_checked(doc["marks"])
    outcome = doc["power"]
    binding = {**plan["binding"], "plan_sha256": args.plan_sha256}
    if (doc.get("lead_authorizes_one_use") is not True
            or doc != {**binding, "marks": m, "power": outcome, "lead_authorizes_one_use": True}):
        raise ValueError("lead approval does not bind the counted schedule, marks and stated power")
    if (not isinstance(outcome, dict)
            or set(outcome) != {"draws", "passes", "probability", "half_edge_bp", "schedule_tickets", "schedule_days"}
            or type(outcome["draws"]) is not int or outcome["draws"] != cfg["power"]["draws"]
            or type(outcome["passes"]) is not int or not 0 <= outcome["passes"] <= outcome["draws"]
            or type(outcome["probability"]) is not float
            or outcome["probability"] != outcome["passes"] / outcome["draws"]
            or type(outcome["half_edge_bp"]) is not float or not math.isfinite(outcome["half_edge_bp"])
            or outcome["schedule_tickets"] != plan["counts"]["tickets"]
            or outcome["schedule_days"] != plan["counts"]["days"]):
        raise ValueError("lead approval has invalid power output for the frozen count")
    if outcome["probability"] < cfg["power"]["min_probability"]:
        raise ValueError("under the fixed power line: close the row without a run")
    return m, {**binding, "approval_sha256": args.approval_sha256}


def confirmed_schedule(hours, starts, plan, specs):
    if starts != plan["first_full_day"]:
        raise ValueError("first full Coinbase day differs from counted schedule")
    fresh = model.schedule(hours, specs)
    if fresh != plan["fresh"]:
        raise ValueError("frozen fresh signal schedule does not match the count")
    return fresh


def confirmed_diagnostic(prior_root, grid, chosen, plan, *, economics):
    diag = old_tickets(prior_root, grid, chosen, economics=economics)
    if [t[:3] for t in diag] != plan["diagnostic"]:
        raise ValueError("prior search tickets differ from the minute plan")
    return diag


@contextmanager
def unused(root):
    with exact_parent(root, LOCK) as (fd, name):
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            os.stat(name, dir_fd=fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise FileExistsError("Plan 72's single use is already claimed")
        yield fd, name


def coinbase_inputs(root, args, cfg, plan, jobs, binding):
    raw_hour = load_hourly(root, args, cfg)
    hours, starts = model.activated(raw_hour, cfg)
    data = feed.load(root, "windows", args.windows_manifest_sha256, jobs, binding)
    if starts != plan["first_full_day"]:
        raise ValueError("first full Coinbase day differs from counted schedule")
    header = {"input_counts": {"hourly_rows": sum(map(len, raw_hour.values())),
                               "window_hourly_rows": sum(len(x) for k, x in data.items() if k[1] == feed.HOUR),
                               "minute_rows": sum(len(x) for k, x in data.items() if k[1] == feed.MINUTE),
                               "requests": len(jobs)}}
    return hours, starts, data, header


def preflight(root, prior_root, args, cfg, grid, plan, jobs):
    _, binding = approve(root, args, cfg, plan)
    chosen, _ = prior_summary(prior_root, grid)
    confirmed_diagnostic(prior_root, grid, chosen, plan, economics=False)
    _, _, _, header = coinbase_inputs(root, args, cfg, plan, jobs, binding)
    return header


def pricing(root, prior_root, args, cfg, fees, grid, specs, plan, jobs, *, validation, claim):
    if validation:
        return feed.lines(preflight(root, prior_root, args, cfg, grid, plan, jobs))
    m, binding = approve(root, args, cfg, plan)
    fd, name = claim
    p70.create_at(fd, name, feed.lines({**binding, "windows_manifest_sha256": args.windows_manifest_sha256,
                                       "rule": model.PRIMARY}))
    hours, starts, data, header = coinbase_inputs(root, args, cfg, plan, jobs, binding)
    fresh = confirmed_schedule(hours, starts, plan, specs)
    e = cfg["minutes"]["judged"]
    overlaps = model.actual_overlaps(fresh[model.PRIMARY], data, cfg, "midpoint", (e, e))
    scheduled = len(fresh[model.PRIMARY])
    overlap_share = len(overlaps) / scheduled if scheduled else 0.
    header["input_counts"].update({"scheduled_judged_tickets": scheduled, "actual_minute_overlap": len(overlaps)})
    if overlap_share > cfg["minutes"]["max_actual_overlap_share"]:
        return feed.lines({**header, "unscorable": "actual_minute_overlap_above_limit"})
    chosen, _ = prior_summary(prior_root, grid)
    diag = confirmed_diagnostic(prior_root, grid, chosen, plan, economics=True)
    ref = model.hourly_reference(hours, sorted({r["hold_hours"] for r in specs.values()}))
    results = [header]
    opts = [(model.PRIMARY, "judged_midpoint", "midpoint", (e, e), True),
            (model.PRIMARY, "worst_of_minute", "worst", (e, e), False),
            (model.PRIMARY, "hourly_open", "hourly", (0, 0), False),
            (model.PRIMARY, "beta_one_gross_hedge", "hedged", (e, e), False),
            *((model.PRIMARY, f"entry_{n}m_late", "midpoint", (n, e), False) for n in cfg["minutes"]["shown_late"]),
            *((r, "shown_sweep_cousin", "midpoint", (e, e), False) for r in model.SHOWN)]
    for rule, label, mode, offsets, judged in opts:
        answer = model.aggregate(fresh[rule], data, hours, ref, cfg, fees, mode, offsets, m,
                                 overlaps if judged else None)
        if not judged:
            answer.pop("meets_marks")
        results.append({"rule": rule, "label": label, "judged": judged, **answer})
    results.append(model.diagnostic(diag, data, cfg, fees))
    return b"".join(map(feed.lines, results))


def dispatch(root, prior_root, args, cfg, fees, grid, specs):
    if args.collect_hourly:
        feed.ensure_dir(root)
    feed.private_dir(root)
    with unused(root) as claim:
        if args.collect_hourly:
            return feed.lines(feed.collect(root, "hourly", model.hourly_jobs(cfg), authority(args),
                                           cfg["request_delay_seconds"]))
        if args.count:
            return feed.lines(build_plan(root, prior_root, args, cfg, grid, specs))
        plan, jobs, frozen_plan = read_plan(root, args, cfg, specs)
        if args.power:
            _, prev_mean = prior_summary(prior_root, grid, economics=True)
            m = (json.loads(p70.pinned(root, "confirmed_marks.json", args.marks_sha256, mode=0o600))
                 if args.marks_sha256 else cfg["proposed_marks"])
            return feed.lines(design_power(plan, cfg, marks_checked(m), prev_mean))
        if args.collect_minutes:
            _, binding = approve(root, args, cfg, plan)
            canonical = canonical_plan(root, prior_root, args, cfg, grid, specs)
            if feed.lines(canonical) != frozen_plan:
                raise ValueError("saved minute plan is not byte-identical to the authenticated schedules")
            return feed.lines(feed.collect(root, "windows", jobs, binding, cfg["request_delay_seconds"]))
        return pricing(root, prior_root, args, cfg, fees, grid, specs, plan, jobs,
                       validation=args.validate_inputs, claim=claim)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    modes = p.add_mutually_exclusive_group(required=True)
    for flag in ("synthetic", "collect-hourly", "count", "power", "collect-minutes", "validate-inputs", "go"):
        modes.add_argument("--" + flag, action="store_true")
    for flag in ("freeze-commit", "config-sha256", "settings-sha256", "grid-sha256", "grid71-sha256",
                 "hourly-manifest-sha256", "plan-sha256", "windows-manifest-sha256", "approval-sha256", "marks-sha256"):
        p.add_argument("--" + flag)
    p.add_argument("--lead-authorize", action="store_true")
    args = p.parse_args()
    if args.synthetic:
        from synthetic_72 import main as test
        test()
        return
    sys.stdout.buffer.write(dispatch(feed.DATA, old.CUSTODY, args, *freeze(args)))


if __name__ == "__main__":
    main()
