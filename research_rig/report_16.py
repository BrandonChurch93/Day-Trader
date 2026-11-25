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


def identity_counts_text(result):
    if "identity_changes" not in result:
        return []
    lines = ["","## Identity status changes against the all-month rule","",
             "| Slice | Year | Spot coin-weeks changed | Perpetual coin-weeks changed |",
             "|---|---|---:|---:|"]
    for name,years in result["identity_changes"].items():
        for year,c in years.items():
            lines.append(f"| {name} | {year} | {c['spot']['changed']} | {c['futures']['changed']} |")
    return lines


def render(result):
    j = result["judgment"]
    lines = ["# Replay 16: the hot five with the market taken out","",
             f"MEASURED. Held-back list with short M: **{j['finding']}**.",
             f"The last complete funding week began Monday {result['last_complete_funding_week_monday_utc']} UTC. "
             f"The exclusive cutoff is {result['cutoff_utc']}. The viewed list and short B are descriptive.","",
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
                      "| Year | Lower costs | Judged costs | Higher costs | Random cutoff (judged) | Short price contribution | Short funding contribution | Short fee debit | Short forced closes | Flagged weeks | Flagged share | Fallback weeks | Live viewed after excluding hot | Live major-weeks | Monday-observed name-weeks | Of those, not allowed under old file gate | All missing-file candidates |",
                      "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
            for year,row in result["years"].items():
                book = row[sample]["shorts"][style]
                b = book["judged"]
                diagnostics = row[sample]["weeks"]
                fallback = sum(bool(w["fallback"]) for w in diagnostics) if style=="M" else 0
                missing = sum(len(w["missing_funding_symbols"]) for w in diagnostics)
                count = lambda k:sum(w.get(k,0) for w in diagnostics)
                lines.append(f"| {year} | {pct(book['low']['end'])} | {pct(b['end'])} | "
                             f"{pct(book['high']['end'])} | {pct(b['random_percentile'])} | "
                             f"{b['short_price']:+.4f} | {b['funding']:+.4f} | {b['short_fees']:.4f} | "
                             f"{b['forced_closes']} | {b['flagged_weeks']} | "
                             f"{b['flagged_week_share_pct']:.2f}% | {fallback} | "
                             f"{count('live_market')} | {count('live_majors')} | "
                             f"{count('monday_live')+count('monday_live_majors')} | "
                             f"{count('file_gate_excluded')+count('file_gate_excluded_majors')} | {missing} |")
        lines += ["",f"### {sample.capitalize()} scale figures, judged costs","",
                  "| Year | Spot all rankable | Long only | Short M only | Short B only | Paper lean (no costs) |",
                  "|---|---:|---:|---:|---:|---:|"]
        for y,book in result["years"].items():
            r = book[sample]
            lines.append(f"| {y} | {pct(r['all_spot_end'])} | {pct(r['long_only']['judged'])} | "
                         f"{pct(r['short_alone']['M']['judged'])} | {pct(r['short_alone']['B']['judged'])} | "
                         f"{pct(r['paper_lean_end'])} |")
    lines += identity_counts_text(result)
    lines += ["","## Interpretation","",
              "STATED. This is a weekly replay on one venue, with a held-back rank slice rather "
              "than a separate set of coins. Contract liveness is inferred from archived bars and "
              "past funding, not verified executable access. The later funding-file gate is not used. "
              "Its counts are historical diagnostics only. Dated identity uses only Monday-available "
              "evidence or permanent notice exclusion; the all-month method is a descriptive "
              "status-count comparison only. An admitted mapping can contain nonmatching months. "
              "Hourly mark or trade bars proxy the "
              "forced close. A stopped contract is settled at its last positive-volume trade close "
              "at cost and unactionable zero-volume hours earn no funding. The book cannot be "
              "replicated as written on a US account.",
              "", "The frozen plan, weekly diagnostics, every random path endpoint and input "
              "fingerprints are preserved with the result."]
    if "trade_hours_without_mark" in result:
        lines += ["",f"MEASURED. {result['trade_hours_without_mark']:,} retained futures trade hours "
                  "had no mark bar. The stress check falls back to the trade high for a short "
                  "and the trade low for a long."]
    return "\n".join(lines)+"\n"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=OUT)
    args = p.parse_args()
    plan = S.plan_bytes()
    result = json.loads(S.RESULT.read_bytes())
    if (result["job"]["plan_sha256"]!=S.F.digest(plan) or
        result["job"]["peer_plan_sha256"]!=S.F.digest(S.peer_plan_bytes())):
        raise SystemExit("refused: result does not match both frozen plans")
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit(f"refused: report already exists: {args.output}")
    S.F.F.write(args.output,render(result).encode())
    print(args.output)


if __name__=="__main__":
    main()
