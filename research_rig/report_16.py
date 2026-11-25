"""Format an existing Replay 16 result, never open data or resimulate."""
from pathlib import Path
import argparse
import json

try:
    from . import score_16 as S
except ImportError:
    import score_16 as S

OUT = S.F.F.ROOT/"docs/research/56_replay_16_hot_five_hedged.md"


def pct(x):
    return f"{100*(x-1):+.2f}%"


def render(result):
    j = result["judgment"]
    lines = ["# Replay 16: the hot five with the market taken out","",
             f"MEASURED. Held-back list with short M: **{j['finding']}**.",
             f"The 2026 cutoff is {result['cutoff_utc']}. The viewed list and short B are descriptive.","",
             "## Four preregistered marks",""]
    marks = ("Positive in enough eligible years","Beat the random cutoff in those years",
             "Enough such years where the sample fell","No year beyond the maximum permitted loss")
    for label,met in zip(marks,j["marks"]):
        lines.append(f"- {label}: {'met' if met else 'not met'}.")
    for label,key in (("Eligible years","eligible"),("Positive years","positive"),
                      ("Years above both","above_both"),("Falling market years above both","falling"),
                      ("Years beyond the maximum loss","over_max_loss")):
        lines.append(f"- {label}: {', '.join(j[key]) or 'none'}.")
    for sample in ("held","viewed"):
        for style in ("M","B"):
            lines += ["",f"## {sample.capitalize()} list, short {style}","",
                      "| Year | Lower costs | Judged costs | Higher costs | Random cutoff (judged) | Short price contribution | Short funding contribution | Short fee debit | Short forced closes | Flagged weeks | Fallback weeks | Missing funding name-weeks |",
                      "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
            for year,row in result["years"].items():
                book = row[sample]["shorts"][style]
                b = book["judged"]
                diagnostics = row[sample]["weeks"]
                fallback = sum(bool(w["fallback"]) for w in diagnostics) if style=="M" else 0
                missing = sum(len(w["missing_funding_symbols"]) for w in diagnostics)
                lines.append(f"| {year} | {pct(book['low']['end'])} | {pct(b['end'])} | "
                             f"{pct(book['high']['end'])} | {pct(b['random_percentile'])} | "
                             f"{b['short_price']:+.4f} | {b['funding']:+.4f} | {b['short_fees']:.4f} | "
                             f"{b['forced_closes']} | {b['flagged_weeks']} | {fallback} | {missing} |")
        lines += ["",f"### {sample.capitalize()} scale figures, judged costs","",
                  "| Year | Spot all rankable | Long only | Short M only | Short B only | Paper lean (no costs) |",
                  "|---|---:|---:|---:|---:|---:|"]
        for y,book in result["years"].items():
            r = book[sample]
            lines.append(f"| {y} | {pct(r['all_spot_end'])} | {pct(r['long_only']['judged'])} | "
                         f"{pct(r['short_alone']['M']['judged'])} | {pct(r['short_alone']['B']['judged'])} | "
                         f"{pct(r['paper_lean_end'])} |")
    lines += ["","## Interpretation","",
              "STATED. This is a weekly replay on one venue, with a held-back rank slice rather "
              "than a separate set of coins. Contract liveness is inferred from archived bars and "
              "past funding, not verified executable access. Hourly mark or trade bars proxy the "
              "forced close. The book cannot be replicated as written on a US account.",
              "", "The frozen plan, weekly diagnostics, every random path endpoint and input "
              "fingerprints are preserved with the result."]
    return "\n".join(lines)+"\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=OUT)
    args = p.parse_args()
    plan = S.plan_bytes()
    result = json.loads(S.RESULT.read_bytes())
    if result["job"]["plan_sha256"]!=S.F.digest(plan):
        raise SystemExit("refused: result does not match the frozen plan")
    if args.output.exists():
        raise SystemExit(f"refused: report already exists: {args.output}")
    S.F.F.write(args.output,render(result).encode())
    print(args.output)


if __name__=="__main__":
    main()
