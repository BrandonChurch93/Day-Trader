"""Format an existing Replay 17 JSON. Never load data or resimulate."""
import argparse
import json
from pathlib import Path
from statistics import median

try:
    from . import score_17 as S
    from .report_16 import identity_counts_text, random_dead_text
except ImportError:
    import score_17 as S
    from report_16 import identity_counts_text, random_dead_text

OUT = S.F.F.ROOT/"docs/research/57_replay_17_short_the_peak.md"
LABELS = {"judged":"Judged costs","low":"Lower costs","no_cost_no_funding":"No costs or funding"}


def pct(x):
    return f"{100*(x-1):+.2f}%"


def render(result):
    rule = result["judgment"]["judged"]
    lines = ["# Replay 17: short the peak","",
             f"MEASURED. The held-back 1x short rule was **{rule['finding']}** at judged costs.",
             f"The last complete funding week began Monday {result['last_complete_funding_week_monday_utc']} UTC. "
             f"The exclusive cutoff was {result['cutoff_utc']}. Viewed-list results and the 3x and "
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
              ("The judged rule failed on timing. It was positive in enough eligible years, but did not beat the hot hold in enough of those same years."
               if result.get("failed_on_timing") else
               "The judged rule did not meet the definition of a timing-only failure."),
              ("The judged rule failed on rising years. It cleared the timing mark, but too few of those same years were rising."
               if result.get("failed_on_rising") else
               "The judged rule did not meet the definition of a rising-years-only failure."),
              ""]
    for sample in ("held","viewed"):
        lines += [f"## {sample.capitalize()} list","",
                  "| Year | Rule S (low) | Rule S (judged) | Rule S (high) | Rule S (no cost or funding) | Hot hold (judged) | All live short | All rankable spot | Random median | 3x | Bounce | Trades | Flagged live parts | Flagged share of live parts | Live parts | Idle parts | Monday-observed name-weeks | Of those, not allowed under old file gate | All missing-file candidates |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for y,row in result["years"].items():
            data = row[sample]
            s = data["swing"]
            r = s["judged"]
            cells = [pct(s[k]["end"]) for k in ("low","judged","high","no_cost_no_funding")]
            cells += [pct(data[k]) for k in ("all_short","spot_all")]
            cells.insert(4,pct(data["hot_hold"]["judged"]))
            cells += [pct(median(r["random_ends"])),pct(data["shown"]["levered"]["end"]),
                      pct(data["shown"]["bounce"]["end"]),str(r["trades"]),str(r["flagged_parts"]),
                      f"{r['flag_share_pct']:.1f}%",str(r["live_parts"]),str(r["idle_parts"])]
            w = data["weeks"]
            cells += [str(sum(x.get(k,0) for x in w))
                      for k in ("monday_live","file_gate_excluded","missing_funding_files")]
            lines.append(f"| {y} | "+" | ".join(cells)+" |")
        lines += ["",f"### {sample.capitalize()} list components at judged costs","",
                  "| Year | Rule S price contribution | Funding contribution | Fees | 3x forced closes |",
                  "|---|---:|---:|---:|---:|"]
        for y,row in result["years"].items():
            r = row[sample]["swing"]["judged"]
            lines.append(f"| {y} | {r['price']:+.4f} | {r['funding']:+.4f} | {r['fees']:.4f} | "
                         f"{row[sample]['shown']['levered']['forced']} |")
        lines += ["",f"### {sample.capitalize()} dead-spell closes, judged costs","",
                  "| Year | Rule S | Random Rule S median (range) | Hot hold | All live short | All rankable spot | 3x | Bounce |",
                  "|---|"+"---:|"*7]
        for y,row in result["years"].items():
            data = row[sample]
            s = data["swing"]["judged"]["dead_spell_closes"]
            d = data["dead_spell_closes"]
            three,bounce = (data["shown"][k]["dead_spell_closes"]["rule"] for k in ("levered","bounce"))
            lines.append(f"| {y} | {s['rule']} | {random_dead_text(s['random'])} | "
                         f"{d['hot_hold']['judged']} | {d['all_short']} | {d['spot_all']} | {three} | {bounce} |")
        lines.append("")
    if "shown_us_shortable" in result:
        lines += ["","## US-shortable roster, shown only","",
                  "| Year | 1x Rule S at judged costs | Closed trades | Hot slots | Live hot slots | Dead-spell closes |",
                  "|---|---:|---:|---:|---:|---:|"]
        for y,r in result["shown_us_shortable"].items():
            lines.append(f"| {y} | {pct(r['end'])} | {r['trades']} | {r['hot_slots']} | "
                         f"{r['live_hot_slots']} | {r['dead_spell_closes']['rule']} |")
        lines += ["","STATED. The November 25, 2026 roster looks ahead to which assets survived "
                  "and received US listings. Some were already in Replay 13's viewed list. "
                  "Binance perpetual prices stand in for the US contracts; fees and funding differ. "
                  "This is not a result for US execution or a preregistered mark."]
    if fees := result.get("shown_us_entry_tier_fees"):
        lines += ["","## Rule S 1x, shown only, US entry-tier fees","",
                  "| Year | List | Tier 3 taker fee per side | Tier 3 net return | Tier 1 taker fee per side | Tier 1 net return |",
                  "|---|---|---:|---:|---:|---:|"]
        for sample,label in (("held","Held-back"),("viewed","Viewed"),("us_roster","US-shortable roster")):
            for year,row in fees.get(sample,{}).items():
                t3,t1 = (row[k] for k in ("tier_3_taker","tier_1_taker"))
                lines.append(f"| {year} | {label} | {t3['bps_per_side']:g} bps | {pct(t3['end'])} | "
                             f"{t1['bps_per_side']:g} bps | {pct(t1['end'])} |")
        lines += ["","STATED. These taker-fee sensitivities change only the fee assumption. "
                  "Prices and funding are still Binance perpetual proxies. The table does not "
                  "measure US execution or affect a preregistered mark."]
    lines += identity_counts_text(result)
    lines += ["","## Interpretation","",
              "STATED. The rank slice is held back, not an independent market. Contract liveness "
              "is an archive proxy. The later funding-file requirement no longer gates entry. "
              "Its counts are retrospective diagnostics only. A flagged part's denominator is the "
              "part-weeks assigned a live contract on Monday, even if the rule never opens a trade. "
              "Dead-spell counts cover closes of open positions, not idle or flagged parts. "
              "Every random draw's count and the cost sensitivity counts are in the result JSON. "
              "Dated identity uses only Monday-available evidence or permanent "
              "notice exclusion; the all-month rule is a descriptive status comparison only. "
              "The hourly fill cannot establish what an order would have "
              "received in a squeeze. The source venue is not available to a US account as written.",
              "", "Every random endpoint, weekly coverage count and input fingerprint is saved in the "
              "result JSON. It also records the identity boundaries that are not independently verified.",
              ""]
    if "trade_hours_without_mark" in result:
        lines += [f"MEASURED. {result['trade_hours_without_mark']:,} retained futures trade hours "
                  "had no mark bar. The stress check falls back to the trade high for a short "
                  "and the trade low for a long.",""]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,default=OUT)
    args = p.parse_args()
    plan = S.A.peer_plan_bytes()
    result = json.loads(S.RESULT.read_bytes())
    if (result["job"]["plan_sha256"]!=S.F.digest(plan) or
        result["job"]["peer_plan_sha256"]!=S.F.digest(S.A.plan_bytes())):
        raise SystemExit("refused: result does not match both frozen plans")
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit(f"refused: report already exists: {args.output}")
    S.F.F.write(args.output,render(result).encode())
    print(args.output)


if __name__=="__main__":
    main()
