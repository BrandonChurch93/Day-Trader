"""Plan 22 calibration on planted paths. Invented markets only; no real bars.

Each seed draws calibration_coins random-walk coins over calibration_days days.
Volume is raised at every natural fresh range break. After such a break the price
drifts up by edge percent over calibration_drift_hours (edge 0 = no follow-through).
With --timing, each gain fades back to zero over calibration_fade_days after the rise,
so the edge is in timing only and coins do not trend.
The judged machinery (rule A, hold, 500 twins, five tests) is run unchanged.
With --write-plan, writes the plan's power paragraph from the two output files."""
import json
import math
import random
import sys
import time

import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import common_22 as G
import paths_22 as PA


def walk(steps, noise, u, fade, g, ramp, n, rd, warm, p, py, v0, v1, edge_pct):
    x = np.cumsum(steps) + math.log(100)
    qv = 1e6 * np.exp(noise)
    drift = len(ramp)
    breaks = 0
    i = warm * 24 + p["wake_hour_utc"]
    while i < n:
        d0 = i - i % 24
        c = np.exp(x[d0 - rd - 24:i])
        o = np.exp(np.concatenate(([x[d0 - rd - 25]], x[d0 - rd - 24:i - 1])))
        h = np.maximum(o, c) * (1 + u[0, d0 - rd - 24:i])
        level = h[24:24 + rd].max()
        prev_level = h[:rd].max()
        last, prev = c[-1], c[-25]
        if (last > level and prev <= level and prev <= prev_level
                and last <= level * (1 + p["max_above_level_pct"] / 100)):
            qv[i - 24:i] *= py.uniform(v0, v1)
            breaks += 1
            if edge_pct:
                m = min(drift, n - i)
                x[i:i + m] += ramp[:m]
                if fade:
                    f = min(fade, max(0, n - i - m))
                    x[i + m:i + m + f] += np.linspace(g, 0, f, endpoint=False)
                else:
                    x[i + m:] += g
        i += 24
    return x, qv, breaks


def market(seed, p, edge_pct, timing=False):
    """Random-walk coins. At every natural fresh range break (rule A's price tests)
    the 24 hours of volume before the wake are raised, and with an edge the price
    then drifts up by edge_pct over calibration_drift_hours. No price is moved
    before a break, so edge 0 is a plain random walk with volume at breaks."""
    sigma, spread = p["calibration_sigma_hourly"], p["calibration_hl_spread"]
    drift = p["calibration_drift_hours"]
    v0, v1 = p["calibration_volume_boost"]
    rng = np.random.default_rng(seed)
    py = random.Random(seed)
    warm = p["volume_days"] + p["range_days"]           # days of bars before the first wake
    start = p["judged_start_h"] - warm * 24
    n = (p["calibration_days"] + warm) * 24
    rd = p["range_days"] * 24
    tapes, assets = {}, []
    for k in range(p["calibration_coins"]):
        steps = rng.normal(0, sigma, n)
        u = rng.uniform(0, spread, (2, n))
        noise = rng.normal(0, 0.3, n)
        g = math.log(1 + edge_pct / 100)
        ramp = np.linspace(0, g, drift)
        # Timing mode: after the rise, the gain fades back to zero over calibration_fade_days,
        # so a break leaves no lasting move and coins do not trend.
        fade = p["calibration_fade_days"] * 24 if timing else 0
        x, qv, _ = walk(steps, noise, u, fade, g, ramp, n, rd, warm, p, py, v0, v1, edge_pct)
        c = np.exp(x)
        o = np.concatenate(([c[0]], c[:-1]))
        h = np.maximum(o, c) * (1 + u[0])
        l = np.minimum(o, c) * (1 - u[1])
        pair = "BTCUSDT" if k == 0 else f"X{k}USDT"
        tapes[pair] = G.Tape(start, o, h, l, c, qv)
        assets.append(G.Asset(1 if k == 0 else 1000 + k, pair, start, 10**9))
    return tapes, assets


def one(seed, edge, p, timing=False):
    tapes, assets = market(seed, p, edge, timing)
    start, end = p["judged_start_h"], p["judged_start_h"] + p["calibration_days"] * 24
    members = lambda w: assets
    ws = G.wakes(start, end, p)
    sched = G.rule_a(tapes, members, ws, p)
    j = p["judged_cost_bps"]
    r = G.book(sched, tapes, start, end, j, p["min_parts"], p["wake_hour_utc"])
    hold = G.book(G.membership(tapes, members, ws), tapes, start, end, j, 1, p["wake_hour_utc"])
    finals, tc = G.twins(sched, tapes, members, ws, start, end, j, p, seed=p["twin_seed"] + seed)
    out = G.judge(G.summary(r, p), G.summary(hold, p), finals, p)
    out["unplaced_share"] = tc.get("twin_entries_not_placed", 0) / max(1, p["twins"] * len(sched))
    out["trades"] = len(sched)
    out["rule_final"] = r.equity[-1]
    out["hold_final"] = hold.equity[-1]
    out["twin_rank"] = float(np.mean(np.asarray(finals) < r.equity[-1]))
    return out


BEGIN = "<!-- calibration figures: written by calibrate_22.py --write-plan from calibration_22.json and calibration_timing_22.json; do not type -->"
END = "<!-- end of calibration figures -->"


def limits_text(cal, calt):
    """The plan's power paragraph. Every figure comes from the two calibration files."""
    def share(d, e):
        return d["edges_pct"][e]["pass_share"]
    def twins(d, e):
        return d["edges_pct"][e]["test_pass_share"]["twins"]
    edges = sorted(cal["edges_pct"], key=float)
    lo, hi, mid = edges[0], edges[-1], edges[len(edges) // 2]
    top = max(share(cal, hi), share(calt, hi))
    if not (float(lo) == 0 and top <= 0.25):
        raise SystemExit("the power wording below no longer fits the calibration files")
    return (f"- MEASURED on planted paths (`calibration_22.json` and `calibration_timing_22.json`, "
            f"{cal['edges_pct'][lo]['seeds']} seeds each). With no edge the five tests together pass in "
            f"{share(cal, lo):.2f} of seeds. With a true edge of {hi}% they pass in {share(cal, hi):.2f} of seeds "
            f"when the gain lasts and {share(calt, hi):.2f} when it fades over `calibration_fade_days` = "
            f"{calt['config']['calibration_fade_days']} days: about a quarter of seeds or fewer. At {mid}% they pass "
            f"in {share(cal, mid):.2f} and {share(calt, mid):.2f}. The twins test alone passes in "
            f"{twins(cal, hi):.2f} and {twins(calt, hi):.2f} at {hi}%. So a fail tells us little and a pass tells us "
            f"a lot. Rule A holds rising coins for weeks or months, so twins with the same holding lengths share most "
            f"of a lasting gain, and most of a short-lived gain is given back before the rule exits. Two other twins "
            f"marks (daily Sharpe, and mean return per trade) were tried on the same planted paths before the freeze; "
            f"neither raised power, and the lead kept end value.")


def write_plan():
    here = PA.HERE
    cal = json.loads((here / "calibration_22.json").read_text())
    calt = json.loads((here / "calibration_timing_22.json").read_text())
    if cal.get("timing_only") is not False or calt.get("timing_only") is not True:
        raise SystemExit("calibration files are not the lasting and timing runs")
    plan = next(x for x in (here / "PREREG_22_fable_rule_a.md", here / "PREREG_22_fable_rule_a_DRAFT.md") if x.exists())
    text = plan.read_text()
    a, b = text.index(BEGIN) + len(BEGIN), text.index(END)
    plan.write_text(text[:a] + "\n" + limits_text(cal, calt) + "\n" + text[b:])
    print("written", plan.name)


def main():
    if "--write-plan" in sys.argv[1:]:
        return write_plan()
    p = PA.policy(final=False)
    timing = "--timing" in sys.argv[1:]
    seeds = range(p["calibration_seed"], p["calibration_seed"] + p["calibration_seeds"])
    res = {}
    t0 = time.time()
    for edge in p["calibration_edges_pct"]:
        rows = [one(s, edge, p, timing) for s in seeds]
        res[str(edge)] = {
            "seeds": len(rows),
            "pass_share": float(np.mean([r["pass"] for r in rows])),
            "test_pass_share": {k: float(np.mean([r["tests"][k] for r in rows])) for k in rows[0]["tests"]},
            "max_unplaced_share": float(max(r["unplaced_share"] for r in rows)),
            "median_unplaced_share": float(np.median([r["unplaced_share"] for r in rows])),
            "median_trades": float(np.median([r["trades"] for r in rows])),
            "median_twin_rank": float(np.median([r["twin_rank"] for r in rows])),
            "median_rule_final": float(np.median([r["rule_final"] for r in rows])),
            "median_hold_final": float(np.median([r["hold_final"] for r in rows])),
        }
        print(edge, json.dumps(res[str(edge)]), f"{time.time() - t0:.0f}s", flush=True)
    name = "calibration_timing_22.json" if timing else "calibration_22.json"
    (PA.HERE / name).write_text(json.dumps(
        {"edges_pct": res, "timing_only": timing, "config": {k: v for k, v in p.items() if k.startswith("calibration_")}}, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
