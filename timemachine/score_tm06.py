"""Plan TM06's scorer. Reads only finished TM06 sessions (session.json with tm06, and result.json) under $TM_RUNS and writes
timemachine/results_tm06.json with every figure the write-up needs. It starts no session and changes no session folder.

For each session, at each fee per side in tm_perp_fee_levels_bps (tm06_plan.main_fee_bps is the main line):
  part P (picker)   the model's gain, largest drop, costs, funding, trades, time in market and forced close-outs; yardsticks
                    (a) equal_all_held, (b) top_7d_rise, (c) top_attention_rise, (e) btc_held, each with model_above; and
                    (d) random_swap_twins (tm_weights_twin_draws seeded draws) with the model's percentile.
  part S (swing)    the same at 1x and at each tm06_plan.carried_leverage (a replay, not a session), with equal_hold, hold_long and
                    shuffled_order_twins (the session's own answers in shuffled order) carried at the same multiple.
  part C (control)  the reversal rule at each leverage in tm06_plan.control_leverage, and its symbol held.
Each session's replay must match its recorded final value to the cent, or the scorer stops.

joined: for each model, at tm06_plan.main_fee_bps and 1x, its sessions joined end to end (gain = product of (1 + g) minus 1):
  picker  its months against joined equal_all_held and top_7d_rise, and against the random-swap twins joined draw by draw
          (draw i of every month compounded); the marks are both yardsticks and the tm_weights_pass_percentile of the twins.
  swing   its weeks against joined equal_hold and the shuffled-order twins joined the same way (the marks), with joined
          hold_long of the benchmark shown for scale, not judged. Each week is called rising or falling by the sign of its
          equal-hold gain (zero counts as falling), and the model is set against equal hold in each group.
  method  models above the middle of their joined twins against tm06_plan.method_min_models_above_median, and models clearing
          every mark against tm06_plan.method_min_models_above_percentile: "shown" or "not shown", or "not finished" while a
          model lacks a month (picker_start to picker_end) or a plan week.

python3 timemachine/score_tm06.py [--only PREFIX] [--draws N] [--out FILE] [--check]
"""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT / "practice"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from timemachine import session as S, tm06, score_weights as SW

OUT = "timemachine/results_tm06.json"


def finished(prefix=None):
    out = []
    for d in sorted(S.runs_dir().glob("*")) if S.runs_dir().exists() else []:
        f = d / "session.json"
        if not f.exists() or not (d / "result.json").exists() or (prefix and not d.name.startswith(prefix)):
            continue
        meta = json.loads(f.read_text())
        if meta.get("tm06") and meta.get("instrument") == "perp" and json.loads((d / "progress.json").read_text()).get("done"):
            out.append((d.name, meta["tm06"]["part"]))
    return out


def summary_line(sc):
    """The main-line figures of one session, flat, for a table in the write-up."""
    f = f"{sc['main_fee_bps']:g}"
    if sc["part"] == "P":
        b = sc["by_fee"][f]; m = b["model"]
        return dict(session=sc["session"], part="P", model=sc["model"], gain_pct=m["final_gain_pct"], twin_percentile=b["random_swap_twins"]["model_percentile"],
                    above=sorted(k for k, v in b["yardsticks"].items() if v["model_above"]), trades=m["trades"], time_in_market_share=m["time_in_market_share"],
                    closeouts=m["closeouts"], attention_rule_left_out_per_wake=sc["attention_rule_left_out_per_wake"], list_size_per_wake=sc["list_size_per_wake"])
    if sc["part"] == "S":
        out = dict(session=sc["session"], part="S", model=sc["model"])
        for mult, by in sc["by_multiple"].items():
            b = by[f]; m = b["model"]
            out[mult] = dict(gain_pct=m["final_gain_pct"], twin_percentile=b["shuffled_order_twins"]["model_percentile"],
                             above=sorted(k for k, v in b["yardsticks"].items() if v["model_above"]), trades=m["trades"],
                             time_in_market_share=m["time_in_market_share"], closeouts=m["closeouts"])
        return out
    return dict(session=sc["session"], part="C", **{mult: dict(gain_pct=by[f]["final_gain_pct"], trades=by[f]["trades"], closeouts=by[f]["closeouts"])
                                                    for mult, by in sc["by_multiple"].items()})


def chain(gs):
    """Gains in percent joined end to end."""
    v = 1.0
    for g in gs:
        v *= 1 + g / 100.0
    return (v - 1) * 100


def plan_months(cfg):
    p = cfg["tm06_plan"]; a, b = p["picker_start"][:7], p["picker_end"][:7]; out = []
    y, m = int(a[:4]), int(a[5:])
    while f"{y:04d}-{m:02d}" <= b:
        out.append(f"{y:04d}-{m:02d}"); y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def join_one(blocks, marks, twin_key, pp):
    """blocks: one main-line block per session, in date order. marks: yardstick names (or prefixes) the model must beat."""
    model = chain(b["model"]["final_gain_pct"] for b in blocks); ys = {}
    for name in marks:
        ks = [next(k for k in b["yardsticks"] if k == name or k.startswith(name)) for b in blocks]
        ys[name] = chain(b["yardsticks"][k]["stats"]["final_gain_pct"] for b, k in zip(blocks, ks))
    d = [b[twin_key]["_draw_gains_pct"] for b in blocks]; assert len({len(x) for x in d}) == 1, "the sessions have different draw counts"
    tw = [chain(x) for x in zip(*d)]; j = SW.judge(tw, model, pp)
    return dict(gain_pct=model, yardsticks_gain_pct=ys, above=dict({k: model > v for k, v in ys.items()}, twins_median=j["model_above_median"],
                twins_pass_percentile=j["model_above_pass_percentile"]), twin_percentile=j["model_percentile"], twin_median_gain_pct=SW.summary(tw)["median"])


def joined(scores, cfg):
    """Each model's months (picker) and weeks (swing) joined, the method counts, and rising and falling weeks apart."""
    pl = cfg["tm06_plan"]; pp = cfg.get("tm_weights_pass_percentile"); f = lambda sc: f"{sc['main_fee_bps']:g}"
    weeks = {w["start"]: i + 1 for i, w in enumerate(pl["swing_weeks"])}; months = plan_months(cfg); out = {}
    for part, need, marks, twin in (("P", months, ["equal_all_held", "top_7d_rise"], "random_swap_twins"), ("S", list(weeks.values()), ["equal_hold_"], "shuffled_order_twins")):
        by = {}
        for sc in sorted((x for x in scores.values() if x["part"] == part), key=lambda x: x["window"]["start"]):
            by.setdefault(sc["model"], []).append(sc)
        models = {}
        for mdl, scs in sorted(by.items()):
            blocks = [x["by_fee"][f(x)] if part == "P" else x["by_multiple"]["1x"][f(x)] for x in scs]
            have = sorted({x["window"]["start"][:7] for x in scs}) if part == "P" else sorted({weeks[x["window"]["start"]] for x in scs if x["window"]["start"] in weeks})
            r = dict(sessions=[x["session"] for x in scs], covered=have, missing=[k for k in need if k not in have], **join_one(blocks, marks, twin, pp))
            r["clears_all_marks"] = all(r["above"][k] for k in marks) and bool(r["above"]["twins_pass_percentile"])
            if part == "S":
                r["hold_long_gain_pct"] = chain(b["yardsticks"][next(k for k in b["yardsticks"] if k.startswith("hold_long_"))]["stats"]["final_gain_pct"] for b in blocks)
                grp = {}
                for x, b in zip(scs, blocks):
                    eqg = b["yardsticks"][next(k for k in b["yardsticks"] if k.startswith("equal_hold_"))]["stats"]["final_gain_pct"]
                    grp.setdefault("rising" if eqg > 0 else "falling", []).append((weeks.get(x["window"]["start"]), b["model"]["final_gain_pct"], eqg))
                r["by_week_direction"] = {k: dict(weeks=[w for w, _, _ in v], gain_pct=chain(g for _, g, _ in v), equal_hold_gain_pct=chain(e for _, _, e in v),
                                                  model_above=chain(g for _, g, _ in v) > chain(e for _, _, e in v)) for k, v in sorted(grp.items())}
            models[mdl] = r
        n_med = sum(1 for r in models.values() if r["above"]["twins_median"]); n_all = sum(1 for r in models.values() if r["clears_all_marks"])
        done = bool(models) and all(not r["missing"] for r in models.values())
        verdict = "not finished" if not done else "shown" if n_med >= pl["method_min_models_above_median"] and n_all >= pl["method_min_models_above_percentile"] else "not shown"
        out[{"P": "picker", "S": "swing"}[part]] = dict(models=models, models_above_twin_median=n_med, models_clearing_all_marks=n_all,
                                                        need_above_median=pl["method_min_models_above_median"], need_all_marks=pl["method_min_models_above_percentile"], verdict=verdict)
    return out


def build(prefix=None, draws=None):
    sessions = finished(prefix); cfg = tm06.full_config(); scores = {}
    for sid, part in sessions:
        scores[sid] = tm06.score(sid, draws=draws)
    return dict(plan="TM06", scorer="timemachine/score_tm06.py", sessions=[s for s, _ in sessions], fee_levels_bps=cfg["tm_perp_fee_levels_bps"],
                twin_draws=int(draws if draws is not None else cfg["tm_weights_twin_draws"]), main_line=[summary_line(scores[s]) for s, _ in sessions], joined=joined(scores, cfg), scores=tm06.public(scores),
                limits=tm06.LIMITS)


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0]); a.add_argument("--only"); a.add_argument("--draws", type=int)
    a.add_argument("--out"); a.add_argument("--check", action="store_true"); x = a.parse_args(argv)
    js = json.dumps(build(x.only, x.draws), indent=1, sort_keys=True) + "\n"; out = Path(x.out) if x.out else ROOT / OUT
    if x.check:
        ok = out.exists() and out.read_text() == js; print("ok" if ok else f"stale: {out}"); sys.exit(0 if ok else 1)
    out.write_text(js); print(f"wrote {out}: {js.count(chr(10))} lines")


if __name__ == "__main__":
    main()
