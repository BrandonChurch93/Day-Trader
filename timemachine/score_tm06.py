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

python3 timemachine/score_tm06.py [--only PREFIX] [--draws N] [--out FILE] [--check]
"""
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (str(ROOT / "practice"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)
from timemachine import session as S, tm06

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
                    closeouts=m["closeouts"])
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


def build(prefix=None, draws=None):
    sessions = finished(prefix); cfg = tm06.full_config(); scores = {}
    for sid, part in sessions:
        scores[sid] = tm06.score(sid, draws=draws)
    return dict(plan="TM06", scorer="timemachine/score_tm06.py", sessions=[s for s, _ in sessions], fee_levels_bps=cfg["tm_perp_fee_levels_bps"],
                twin_draws=int(draws if draws is not None else cfg["tm_weights_twin_draws"]), main_line=[summary_line(scores[s]) for s, _ in sessions], scores=scores,
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
