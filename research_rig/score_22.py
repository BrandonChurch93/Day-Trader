"""Plan 22 scorer. One shot on real bars, only after the plan is frozen.

  --coverage         list and identity counts from manifest metadata; opens no bar file.
  --validate-inputs  every pre-lock check on the real inputs: opens and checks every archive,
                     computes no return, writes no lock and no result. With --approval-commit
                     it also runs the approval gate.
  --real --approval-commit <c>
                     the single judged run. Runs the gate and the same checks as --validate-inputs,
                     then takes the one-shot lock, checks every pin again, and only then scores.
                     No PLAN22_ or P22_ environment variable is allowed."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys

import numpy as np
import yaml

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_22 as G
import paths_22 as PA
from paths_22 import EXCLUDE_22, DIRECT, top_rows, page_at  # noqa: F401  (re-exported for tests)

sys.path.insert(0, str(PA.RIG))


class Refused(Exception):
    """A fixed-code refusal. The message names a check and a path or key, never a price."""


PLAN_NAME = "PREREG_22_fable_rule_a.md"
PINNED_NAMES = (PLAN_NAME, "common_22.py", "paths_22.py", "score_22.py", "fetch_22.py", "test_22.py",
                "calibrate_22.py", "fetch_13.py", "fetch_16.py", "common_13.py", "identity_asof_16_17.py")
CONFIG_PIN = "thresholds.yaml#replay_22_plan"
DATA_PINS = ("replay_22/manifest_22.json", "replay_13/snapshots.json", "replay_16/identity_policy_16_17.json")
APPROVAL = "research_rig/APPROVAL_22.md"
PINNED = "research_rig/PINNED_22.json"
APPROVAL_LINE = re.compile(r"(?m)^Approved by the lead: plan 22, one scored run, freeze commit ([0-9a-f]{40})\.$")
LEDGER_ROW = re.compile(rb"(?m)^\| 159 \|[^\n]+PREREG_22_fable_rule_a")
RESULT, LOCK = "results_22.json", "score_22.lock"
GIT = shutil.which("git") or "/usr/bin/git"                # absolute path; GIT_ variables are dropped for each call


def paths():
    """The fixed paths of the judged run. Tests build their own dict; nothing reads the environment."""
    return {"repo": PA.REPO, "here": PA.HERE, "config": PA.CONFIG, "run": PA.DATA,
            "data": PA.WS / "rig/data", "r13": PA.R13, "r16": PA.R16}


def digest(b):
    return hashlib.sha256(b).hexdigest()


def no_env():
    bad = sorted(k for k in os.environ if k.startswith(("PLAN22_", "P22_")))
    if bad:                                           # no variable may steer a judged step (audit B1)
        raise Refused("P22_ENV " + ",".join(bad))


def config_block_sha256(raw):
    return digest(json.dumps(yaml.safe_load(raw)[PA.KEY]["value"], sort_keys=True, default=str).encode())


def authorize(commit, P):
    """Refuse unless HEAD is the lead's approval commit. That commit must: be HEAD with no tracked change;
    add research_rig/APPROVAL_22.md holding the approval line, which names the freeze commit; have that
    freeze commit as its single parent, where the approval file did not exist, and add nothing else; and carry every plan 22 file
    and the replay_22_plan block byte for byte as frozen, matching research_rig/PINNED_22.json, with the
    plan marked FROZEN and ledger row 159. The off-repo inputs must match their pins on disk.
    Returns the pins and the config bytes it checked."""
    root = str(P["repo"])

    def git(*a, ok=False):
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        r = subprocess.run([GIT, "--no-replace-objects", "-c", "core.fsmonitor=false", "-C", root, *a],
                           capture_output=True, env=env)
        if r.returncode and not ok:
            raise Refused("P22_NOT_APPROVED git " + a[0])
        return r

    def show(c, path):
        return git("show", f"{c}:{path}").stdout
    no_env()
    if not re.fullmatch(r"[0-9a-f]{40}", commit or ""):
        raise Refused("P22_NOT_APPROVED no approval commit given")
    rig = Path(root) / "research_rig"
    if Path(P["here"]).resolve() != rig.resolve():
        raise Refused("P22_NOT_APPROVED code is not run from the repo")
    if Path(P["config"]).resolve() != (Path(root) / "config/thresholds.yaml").resolve():
        raise Refused("P22_NOT_APPROVED config path")
    if git("rev-parse", "HEAD").stdout.decode().strip() != commit:
        raise Refused("P22_NOT_APPROVED HEAD is not the approval commit")
    if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        raise Refused("P22_NOT_APPROVED tracked files changed")
    r = git("show", f"{commit}:{APPROVAL}", ok=True)
    m = APPROVAL_LINE.search(r.stdout.decode("utf-8", "replace")) if not r.returncode else None
    if not m:
        raise Refused("P22_NOT_APPROVED " + APPROVAL)
    frozen = m.group(1)
    if frozen == commit or git("merge-base", "--is-ancestor", frozen, commit, ok=True).returncode:
        raise Refused("P22_NOT_APPROVED freeze commit is not an ancestor")
    if git("rev-list", "--parents", "-n", "1", commit).stdout.decode().split() != [commit, frozen]:
        raise Refused("P22_NOT_APPROVED the approval commit's single parent is not the freeze commit")
    if git("diff", "--name-status", "--no-renames", frozen, commit).stdout.decode().splitlines() != ["A\t" + APPROVAL]:
        raise Refused("P22_NOT_APPROVED the approval commit must add only " + APPROVAL)
    if not git("cat-file", "-e", f"{frozen}:{APPROVAL}", ok=True).returncode:
        raise Refused("P22_NOT_APPROVED approval file already in the freeze commit")
    pins = json.loads(show(commit, PINNED))
    if show(frozen, PINNED) != show(commit, PINNED):
        raise Refused("P22_NOT_APPROVED pins changed after the freeze")
    if set(pins) != {*PINNED_NAMES, CONFIG_PIN, *DATA_PINS}:
        raise Refused("P22_NOT_APPROVED pin names")
    for name in PINNED_NAMES:
        path = "research_rig/" + name
        h = digest(show(commit, path))
        if h != pins[name] or h != digest(show(frozen, path)) or h != digest((rig / name).read_bytes()):
            raise Refused("P22_NOT_APPROVED pin " + name)
    cfg = "config/thresholds.yaml"
    disk_cfg = Path(P["config"]).read_bytes()          # read once; the caller parses these same bytes
    h = config_block_sha256(show(commit, cfg))
    if (h != pins[CONFIG_PIN] or h != config_block_sha256(show(frozen, cfg))
            or h != config_block_sha256(disk_cfg)):
        raise Refused("P22_NOT_APPROVED pin " + CONFIG_PIN)
    plan = show(commit, "research_rig/" + PLAN_NAME)
    status = re.findall(rb"(?m)^Status:[^\n]*", plan)
    if len(status) != 1 or not status[0].startswith(b"Status: FROZEN"):
        raise Refused("P22_NOT_APPROVED plan not frozen")
    if git("cat-file", "-e", f"{commit}:research_rig/PREREG_22_fable_rule_a_DRAFT.md", ok=True).returncode == 0:
        raise Refused("P22_NOT_APPROVED draft plan still in the repo")
    if not LEDGER_ROW.search(show(commit, "research_rig/TRIAL_LEDGER.md")):
        raise Refused("P22_NOT_APPROVED ledger row 159")
    load_inputs(P, pins)
    return pins, disk_cfg


def fsync_dir(path):
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def lock_file(path, job):
    """One-shot lock: O_CREAT|O_EXCL, read-only, file and folder synced. A lock that exists means the
    run is used up, whatever happened after it was taken."""
    path = Path(path)
    for x in (path, path.with_name(RESULT)):
        if os.path.lexists(x):
            raise Refused(f"P22_ALREADY_USED {x}")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    except FileExistsError as e:
        raise Refused(f"P22_ALREADY_USED {path}") from e
    with os.fdopen(fd, "w") as f:
        json.dump(job, f, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    fsync_dir(path.parent)


# ---------- list and identity (no prices) ----------

def load_inputs(P, pins=None):
    """Read each off-repo input once. With pins, refuse any whose uncompressed bytes differ. The judged run
    parses only these bytes, so a file changed on disk after this point cannot reach the score."""
    blobs = {}
    for name in DATA_PINS:
        try:
            blobs[name] = PA.read_input(Path(P["data"]) / name)
        except FileNotFoundError:
            raise Refused("P22_INPUT_MISSING " + name) from None
        if pins is not None and digest(blobs[name]) != pins[name]:
            raise Refused("P22_INPUT_CHANGED " + name)
    return blobs


def identity(p, P=None, blobs=None):
    import identity_asof_16_17 as I
    import fetch_13 as F
    blobs = blobs or load_inputs(P or paths())
    info = json.loads(blobs["replay_16/identity_policy_16_17.json"])
    snaps = json.loads(blobs["replay_13/snapshots.json"])
    ids = {r["id"] for s in snaps if not s.get("hole") for r in top_rows(s, p)}
    rows = [r for r in info["as_of_rows"] if r["market"] == "spot" and r["id"] in ids]
    cutoff = F.boundary(info["as_of_cutoff_utc"], 0)
    if p["shown_end_h"] * 3600 > cutoff:
        raise Refused("P22_IDENTITY_CUTOFF")
    return I.Timeline({"as_of_rows": rows}, cutoff), snaps


def members_builder(p, pairs_with_bars, counts, P=None, blobs=None):
    import fetch_13 as F
    timeline, snaps = identity(p, P, blobs)
    pages = sorted((s for s in snaps if not s.get("hole")), key=lambda s: s["known_at"])
    cache = {}

    def members(w):
        if w in cache:
            return cache[w]
        page = page_at(pages, w, p)
        out = []
        if page is None:
            counts["wakes_without_page"] = counts.get("wakes_without_page", 0) + 1
            cache[w] = out
            return out
        conf = timeline.at(w * 3600)["spot"]
        for row in top_rows(page, p):
            seg = [(a, b, pair) for a, b, pair in F.segments(row) if a <= w * 3600 < b]
            key = "listed"
            if not seg:
                key = "no_pair_segment"
            else:
                a, b, pair = seg[0]
                if (row["id"], pair) not in conf and (row["id"], pair) not in DIRECT:
                    key = "not_confirmed"
                elif pair not in pairs_with_bars:
                    key = "no_bars"
                else:
                    floor = getattr(conf, "floors", {}).get((row["id"], pair), -10**12)
                    lo = max(a, floor)
                    out.append(G.Asset(row["id"], pair, -(-lo // 3600), b // 3600 if b < 10**12 else 10**9))
            counts["coin_wakes_" + key] = counts.get("coin_wakes_" + key, 0) + 1
        cache[w] = out
        return out
    return members


# ---------- bars ----------

def load_tapes(manifest, wanted=None, P=None):
    """Open every archive in the manifest and check it. Reads prices into arrays; computes nothing from them."""
    import fetch_13 as F
    P = P or paths()
    by_pair = {}
    for key, meta in manifest["archives"].items():
        pair = key.split("/")[4]
        if wanted is None or pair in wanted:
            by_pair.setdefault(pair, []).append((key, meta))
    tapes = {}
    for pair, files in sorted(by_pair.items()):
        lo = min(m["first"] for _, m in files) // 3600
        hi = max(m["last"] for _, m in files) // 3600 + 1
        cols = np.full((5, hi - lo), np.nan)
        seen = np.zeros(hi - lo, dtype=bool)
        for key, meta in files:
            path = Path(P["data"]) / meta["where"] / "archives" / key
            if not path.is_file():
                raise Refused(f"P22_ARCHIVE_MISSING {key}")
            raw = path.read_bytes()
            if digest(raw) != meta["sha256"]:
                raise Refused(f"P22_ARCHIVE_CHANGED {key}")
            n, first, last = 0, None, None
            try:
                parsed = [(int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[7]))
                          for r in F.zip_rows(raw)]
            except Exception:
                raise Refused(f"P22_BAD_ROW {key}") from None      # redacted: no field value is echoed
            for raw_t, o, hh, ll, c, qv in parsed:
                # exact hour at the file's own resolution (ms, or us from 2025): +1 ms or +1 us is off grid
                unit = 1_000_000 if raw_t >= 10**14 else 1000
                if raw_t % (3600 * unit):
                    raise Refused(f"P22_OFF_GRID {key}")
                t = raw_t // unit
                if not meta["first"] <= t <= meta["last"]:
                    raise Refused(f"P22_OUT_OF_BOUNDS {key}")
                first, last = t if first is None else first, t
                h = t // 3600 - lo
                if (seen[h] or not all(math.isfinite(x) and x > 0 for x in (o, hh, ll, c))
                        or not math.isfinite(qv) or qv < 0 or ll > min(o, c) or hh < max(o, c)):
                    raise Refused(f"P22_BAD_OR_DUPLICATE_BAR {key}")
                seen[h] = True
                cols[:, h] = (o, hh, ll, c, qv)
                n += 1
            if n != meta["n"] or first != meta["first"] or last != meta["last"]:
                raise Refused(f"P22_ROWS_DIFFER {key}")
        tapes[pair] = G.Tape(lo, *cols)
    return tapes


# ---------- the judged run ----------

def run_window(tapes, members, start, end, p, counts, judged):
    ws = G.wakes(start, end, p)
    sched = G.rule_a(tapes, members, ws, p, counts=counts)
    hold = G.membership(tapes, members, ws, counts)
    bps_all = sorted({p["judged_cost_bps"], *p["shown_cost_bps"]})
    out = {"rule_a": {}, "hold": {}}
    res = {}
    for bps in bps_all:
        res[bps] = G.book(sched, tapes, start, end, bps, p["min_parts"], p["wake_hour_utc"])
        out["rule_a"][str(bps)] = {**G.summary(res[bps], p), "gaps": res[bps].gaps}
        hb = G.book(hold, tapes, start, end, bps, 1, p["wake_hour_utc"])
        out["hold"][str(bps)] = {**G.summary(hb, p), "gaps": hb.gaps}
    j = p["judged_cost_bps"]
    r = res[j]
    btc = [a for a in members(ws[0]) if a.pair == "BTCUSDT"]
    btc_asset = btc[0] if btc else G.Asset(1, "BTCUSDT", -10**12, 10**9)
    switch = G.BtcSwitch(tapes["BTCUSDT"], btc_asset, ws, p, counts)
    with_c = G.rule_a(tapes, members, ws, p, switch=switch)
    out["btc_switch_off_wakes"] = len(switch.off_at)
    out["rule_a_with_c"] = G.summary(G.book(with_c, tapes, start, end, j, p["min_parts"], p["wake_hour_utc"]), p)
    short = G.rule_a(tapes, members, ws, p, stall_needs_volume=False)
    out["rule_a_short_exit"] = G.summary(G.book(short, tapes, start, end, j, p["min_parts"], p["wake_hour_utc"]), p)
    out["btc_held"] = G.summary(G.book([G.Trade(btc_asset, ws[0], None, "window_end")], tapes, start, end, j, 1, p["wake_hour_utc"]), p)
    years = (end - start) / 24 / 365.25
    out["trades"] = len(sched)
    out["trades_per_year"] = len(sched) / years
    out["time_in_cash"] = G.time_in_cash(sched, ws)
    out["exit_reasons"] = {k: sum(t.reason == k for t in sched) for k in sorted({t.reason for t in sched})}
    out["without_best"] = G.summary(G.book(G.without_best(sched, r, p["drop_best"]), tapes, start, end, j,
                                           p["min_parts"], p["wake_hour_utc"]), p)
    if judged:
        finals, tc = G.twins(sched, tapes, members, ws, start, end, j, p)
        out["twins"] = {"n": len(finals), "median": float(np.median(finals)),
                        "cut": float(np.percentile(finals, p["twin_percentile"])), "counts": tc,
                        "share_at_or_above_rule": float(np.mean(np.asarray(finals) >= r.equity[-1]))}
        out["judge"] = G.judge(out["rule_a"][str(j)], out["hold"][str(j)], finals, p)
    out["counts"] = dict(counts)
    return out


def validate_inputs(p, P, manifest, blobs=None):
    """Every check that can fail before the lock, on the real inputs. Opens every archive; computes no
    return, writes no lock and no result. --real runs exactly this before it takes the lock."""
    if manifest.get("no_binance_pair"):
        raise Refused("P22_NO_BINANCE_PAIR")
    tapes = load_tapes(manifest, P=P)
    warm = (p["volume_days"] + p["range_days"] + 1) * 24
    btc = tapes.get("BTCUSDT")
    if btc is None:
        raise Refused("P22_NO_BTCUSDT")
    if btc.start > p["judged_start_h"] - warm or btc.end < p["shown_end_h"]:
        raise Refused("P22_BTCUSDT_SHORT")
    # Extent only: interior missing BTC hours are allowed, as for every coin. Rule C counts the wakes it cannot
    # read (btc_switch_unreadable) and stays as it was at those wakes. The count of missing hours is reported.
    a0, b0 = p["judged_start_h"] - warm, p["shown_end_h"]
    counts = {"btc_missing_hours": int((b0 - a0) - (btc.n_present[b0 - btc.start] - btc.n_present[a0 - btc.start]))}
    for name, a, b in (("judged", p["judged_start_h"], p["judged_end_h"]),
                       ("shown", p["shown_start_h"], p["shown_end_h"])):
        c, by_year, per = {}, {}, []
        m = members_builder(p, set(tapes), c, P, blobs)
        for w in G.wakes(a, b, p):
            before = dict(c)
            per.append(len(m(w)))
            y = by_year.setdefault(datetime.fromtimestamp(w * 3600, timezone.utc).strftime("%Y"), {"wakes": 0})
            y["wakes"] += 1
            for k, v in c.items():
                if v != before.get(k, 0):
                    y[k] = y.get(k, 0) + v - before.get(k, 0)
        if c.get("wakes_without_page") or not per or min(per) < 1:
            raise Refused(f"P22_LIST_HOLE {name}")
        if c.get("coin_wakes_no_bars"):
            raise Refused(f"P22_LISTED_PAIR_WITHOUT_BARS {name}")
        counts[name] = {"wakes": len(per), "min_tradable": min(per), "median_tradable": float(np.median(per)),
                        "max_tradable": max(per), **c, "by_year": by_year}
    counts["archives"] = len(manifest["archives"])
    counts["pairs"] = len(tapes)
    counts["rows"] = sum(m["n"] for m in manifest["archives"].values())
    return tapes, counts


def run_real(commit, P=None):
    P = P or paths()
    pins, cfg_bytes = authorize(commit, P)
    p = G.policy(yaml.safe_load(cfg_bytes)[PA.KEY]["value"])
    blobs = load_inputs(P, pins)                       # the only bytes the score will parse
    manifest = json.loads(blobs[DATA_PINS[0]])
    tapes, vcounts = validate_inputs(p, P, manifest, blobs)
    run = Path(P["run"])
    lock = run / LOCK
    job = {"job": "plan 22 judged run", "started_utc": datetime.now(timezone.utc).isoformat(),
           "approval_commit": commit, "pins": pins, "command": [sys.executable, *sys.argv]}
    lock_file(lock, job)
    try:
        if authorize(commit, P)[0] != pins:              # every pin again, after the lock
            raise Refused("P22_CHANGED_AFTER_LOCK")
        counts_j, counts_s = {}, {}
        mj = members_builder(p, set(tapes), counts_j, P, blobs)
        judged = run_window(tapes, mj, p["judged_start_h"], p["judged_end_h"], p, counts_j, True)
        ms = members_builder(p, set(tapes), counts_s, P, blobs)
        shown = run_window(tapes, ms, p["shown_start_h"], p["shown_end_h"], p, counts_s, False)
        out = {"plan": 22, "pins": pins, "approval_commit": commit, "judged": judged,
               "source_months_shown_only": shown, "validation_counts": vcounts,
               "absent_days": manifest.get("absent_days", {}), "no_binance_pair": manifest.get("no_binance_pair", [])}
        result = run / RESULT
        if os.path.lexists(result):
            raise Refused("P22_RESULT_APPEARED")
        with open(result, "x") as f:
            f.write(json.dumps(out, sort_keys=True, indent=1) + "\n")
            f.flush()
            os.fsync(f.fileno())
        fsync_dir(run)
        print("written", result)
    except Exception as exc:
        why = str(exc) if isinstance(exc, Refused) else type(exc).__name__   # redacted: no data in the message
        sys.stderr.write(f"Plan 22 failed after taking the lock; the run is used up: {why}\n")
        raise


def validate_only(commit, P=None):
    """--validate-inputs: the gate when an approval commit is given, then every input check. Prints counts
    only. No lock, no result, no return."""
    P = P or paths()
    no_env()
    pins = None
    if commit:
        pins, cfg_bytes = authorize(commit, P)
        p = G.policy(yaml.safe_load(cfg_bytes)[PA.KEY]["value"])
    else:
        p = PA.policy(final=False)
    blobs = load_inputs(P, pins)
    _, counts = validate_inputs(p, P, json.loads(blobs[DATA_PINS[0]]), blobs)
    print(json.dumps({"validated": True, "gate_checked": bool(commit), **counts}, sort_keys=True))


def coverage():
    """Counts from metadata only: list, identity and archive presence by wake."""
    p = PA.policy(final=False)
    manifest = json.loads(PA.read_input(PA.DATA / "manifest_22.json"))
    pairs = {k.split("/")[4] for k in manifest["archives"]}
    out = {}
    for name, a, b in (("judged", p["judged_start_h"], p["judged_end_h"]),
                       ("shown", p["shown_start_h"], p["shown_end_h"])):
        c = {}
        m = members_builder(p, pairs, c)
        per = [len(m(w)) for w in G.wakes(a, b, p)]
        out[name] = {"wakes": len(per), "min_tradable": min(per), "median_tradable": float(np.median(per)),
                     "max_tradable": max(per), **c}
    out["absent_pair_days"] = {k: len(v) for k, v in manifest.get("absent_days", {}).items()}
    out["no_binance_pair"] = manifest.get("no_binance_pair", [])
    text = json.dumps(out, indent=1, sort_keys=True) + "\n"
    (PA.HERE / "coverage_22.json").write_text(text)
    print(text, end="")


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--real", action="store_true")
    g.add_argument("--validate-inputs", action="store_true")
    g.add_argument("--coverage", action="store_true")
    ap.add_argument("--approval-commit", help="the lead's approval commit; needed for --real")
    a = ap.parse_args()
    try:
        if a.real:
            run_real(a.approval_commit)
        elif a.validate_inputs:
            validate_only(a.approval_commit)
        else:
            coverage()
    except Refused as e:
        print("refused:", e)
        sys.exit(2)
    except Exception as e:                            # redacted: the type only, never a field value
        print("refused: P22_ERROR", type(e).__name__)
        sys.exit(3)


if __name__ == "__main__":
    main()
