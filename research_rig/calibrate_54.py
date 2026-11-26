"""Price-blind Plan 54 gate. Numeraire returns are simulated in basis points."""
import json
import sys
from pathlib import Path
from random import Random

def settings():
    path = Path(__file__).resolve().parents[1] / "config" / "thresholds.yaml"
    block = path.read_text().split("\nplan_54_closure:\n", 1)[1]
    return json.loads(block.splitlines()[0].split("value: ", 1)[1])


def judged(market, roster, losers, turns, marks):
    ib = [a-b for a, b in zip(losers, market, strict=True)]
    paired = [a-b for a, b in zip(losers, roster, strict=True)]
    mean = sum(paired) / turns
    var = sum((x-mean)**2 for x in paired) / (turns-1)
    paired_positive = mean > 0
    paired_t = paired_positive and var > 0 and mean**2 * turns >= marks["paired_t"]**2 * var
    trim = sum(sorted(losers, reverse=True)[:marks["drop_best"]])
    raw_pass = (sum(losers) > 0 and sum(x > 0 for x in losers) >= marks["positive_years"]
                and sum(ib) > 0 and sum(x > 0 for x in ib) >= marks["ahead_years"]
                and sum(losers) > trim and paired_positive)
    # Full simulated coverage, and no cash differential: price-only equals total return here.
    return raw_pass, raw_pass and paired_t, paired_t


def simulation(c, turns, marks, market_sd, roster_sd, relative_sds):
    rng = Random(c["seed"])
    shifts = [(edge, 0) for edge in c["gross_edge_bps"]] + [(0, c["shared_edge_bps"])]
    counts = {(sd, edge, shared): [0, 0, 0] for sd in relative_sds for edge, shared in shifts}
    worlds = c["worlds"]
    for _ in range(worlds):
        market = [rng.gauss(0, market_sd) for _ in range(turns)]
        tracking = [rng.gauss(0, roster_sd) for _ in range(turns)]
        residual = [rng.gauss(0, 1) for _ in range(turns)]
        for sd in relative_sds:
            base_roster = [m + r for m, r in zip(market, tracking, strict=True)]
            base_losers = [r + sd*d for r, d in zip(base_roster, residual, strict=True)]
            for edge, shared in shifts:
                results = judged([v + shared - c["benchmark_cost_bps"] for v in market],
                                 [v + shared - c["roster_cost_bps"] for v in base_roster],
                                 [v + shared + edge - c["loser_cost_bps"] for v in base_losers],
                                 turns, marks)
                old = counts[sd, edge, shared]
                counts[sd, edge, shared] = [a+b for a, b in zip(old, results, strict=True)]
    return {"synthetic_only": True, "worlds": worlds, "seed": c["seed"], "turns": turns,
            "market_sd_bps": market_sd, "roster_relative_sd_bps": roster_sd,
            "assumed_round_trip_bps": {k: c[k+"_cost_bps"] for k in ("benchmark", "roster", "loser")},
            "scenarios": [{"loser_relative_sd_bps": sd, "planted_loser_gross_edge_bps": e,
                           "shared_gross_edge_bps": s, "plan48_style_pass_rate": n[0]/worlds,
                           "also_require_paired_t_pass_rate": n[1]/worlds,
                           "paired_t_alone_pass_rate": n[2]/worlds}
                          for (sd, e, s), n in counts.items()]}


def main():
    plan = settings()
    if sys.argv[1:] == ["--cef"]:
        c = plan["cef_sensitivity"]
        pairs = zip(c["market_sd_bps"], c["roster_sd_bps"], c["relative_sd_bps"], strict=True)
        out = [simulation(c, plan["turns"], plan["marks"], m, r, [s]) for m, r, s in pairs]
    elif not sys.argv[1:]:
        c = plan["calibration"]
        out = simulation(c, plan["turns"], plan["marks"], c["market_sd_bps"],
                         c["roster_sd_bps"], c["relative_sd_bps"])
    else:
        raise SystemExit("usage: calibrate_54.py [--cef]")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
