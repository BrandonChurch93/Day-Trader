"""Format an existing Replay 17 JSON. Never load data or resimulate."""
import argparse
import json
from pathlib import Path
from statistics import median

try:
    from . import score_17 as S
except ImportError:
    import score_17 as S

OUT = S.F.F.ROOT/"docs/research/57_replay_17_short_the_peak.md"
LABELS = {"judged":"Judged costs","low":"Lower costs","no_cost_no_funding":"No costs or funding"}


def pct(x):
    return f"{100*(x-1):+.2f}%"


def render(result):
    rule = result["judgment"]["judged"]
    lines = ["# Replay 17: short the peak","",
             f"MEASURED. The held-back 1x short rule was **{rule['finding']}** at judged costs.",
             f"The 2026 UTC cutoff was {result['cutoff_utc']}. Viewed-list results and the 3x and "
             "bounce variants are descriptive.","",
             "## Preregistered marks","",
             "| Assumptions | Positive years | Also beat the hot hold | Also rising years |",
             "|---|---|---|---|"]
    for level,row in result["judgment"].items():
        cells = ["met" if x else "not met" for x in row["marks"]]
        lines.append(f"| {LABELS[level]} | "+" | ".join(cells)+" |")
    lines += ["",f"Judged eligible years: {', '.join(rule['eligible']) or 'none'}. "
              f"Positive: {', '.join(rule['positive']) or 'none'}. Also beat hot hold: "
              f"{', '.join(rule['above_hold']) or 'none'}. Also rising: {', '.join(rule['rising']) or 'none'}.",
              ("The marks hold without cost or funding but not at judged costs."
               if result["failed_on_costs"] else
               "The contrast between no costs or funding and judged costs does not meet the preregistered definition of failure on costs."),
              ""]
    for sample in ("held","viewed"):
        lines += [f"## {sample.capitalize()} list","",
                  "| Year | Rule S (low) | Rule S (judged) | Rule S (high) | Rule S (no cost or funding) | Hot hold (judged) | All live short | All rankable spot | Random median | 3x | Bounce | Trades | Flagged parts | Idle parts |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for y,row in result["years"].items():
            data = row[sample]
            s = data["swing"]
            r = s["judged"]
            cells = [pct(s[k]["end"]) for k in ("low","judged","high","no_cost_no_funding")]
            cells += [pct(data[k]) for k in ("all_short","spot_all")]
            cells.insert(4,pct(data["hot_hold"]["judged"]))
            cells += [pct(median(r["random_ends"])),pct(data["shown"]["levered"]["end"]),
                      pct(data["shown"]["bounce"]["end"]),str(r["trades"]),
                      f"{r['flag_share_pct']:.1f}%",str(r["idle_parts"])]
            lines.append(f"| {y} | "+" | ".join(cells)+" |")
        lines += ["",f"### {sample.capitalize()} list components at judged costs","",
                  "| Year | Rule S price contribution | Funding contribution | Fees | 3x forced closes |",
                  "|---|---:|---:|---:|---:|"]
        for y,row in result["years"].items():
            r = row[sample]["swing"]["judged"]
            lines.append(f"| {y} | {r['price']:+.4f} | {r['funding']:+.4f} | {r['fees']:.4f} | "
                         f"{row[sample]['shown']['levered']['forced']} |")
        lines.append("")
    lines += ["## Interpretation","",
              "STATED. The rank slice is held back, not an independent market. Contract liveness "
              "is an archive proxy, and the hourly fill cannot establish what an order would have "
              "received in a squeeze. The source venue is not available to a US account as written.",
              "", "Every random endpoint, weekly coverage count and input fingerprint is saved in the "
              "result JSON. It also records the identity boundaries that are not independently verified.",
              ""]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=OUT)
    args = p.parse_args()
    plan = S.A.peer_plan_bytes()
    result = json.loads(S.RESULT.read_bytes())
    if result["job"]["plan_sha256"]!=S.F.digest(plan):
        raise SystemExit("refused: result does not match the frozen plan")
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit(f"refused: report already exists: {args.output}")
    S.F.F.write(args.output,render(result).encode())
    print(args.output)


if __name__=="__main__":
    main()
