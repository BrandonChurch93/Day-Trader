"""Writes docs/research/52_replay_14_large_stock_momentum.md from stored files only: results_14.json (the one run),
and noedge_14.json (the made-up no-edge check from test_14.py). Reads no price and runs nothing. Every figure on the
page comes from those files; none is typed by hand. Gaps are printed next to the results they touch.

   python3 report_14.py                      writes the page (refuses if results_14.json does not exist)
   python3 report_14.py --from DIR --out F   reads the files from DIR and writes F (used by the tests)"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGE = os.path.join(ROOT, "docs", "research", "52_replay_14_large_stock_momentum.md")
MARKS = {"1_above_spy": "1. Ends the whole period above SPY",
         "2_above_everyone": "2. Ends above every member in equal parts (yardstick b)",
         "3_above_random_percentile": "3. Ends above the set percentile of random baskets (yardstick c)",
         "4_above_spy_each_half": "4. Above SPY in each half taken apart"}

def load(d, name):
    p = os.path.join(d, name)
    if not os.path.exists(p): return None
    with open(p) as fh: return json.load(fh)

def pc(x, d=1): return "none" if x is None else f"{x * 100:+.{d}f}%"
def yn(b): return "pass" if b else "fail"

def build(src):
    R = load(src, "results_14.json")
    if R is None: raise SystemExit("refused: results_14.json does not exist; the page is written only from the one run")
    NE = load(src, "noedge_14.json")
    res, cov, inp, run = R["result"], R["coverage"], R["inputs"], R["run"]
    P = inp["config_replay_14_plan"]
    o = []; w = o.append
    w("# Replay 14: plain momentum on large stocks, held a month at a time"); w("")
    w(f"MEASURED {run['utc']} UTC by `research_rig/score_14.py --run`, one run, commit `{run['commit'][:12]}`. Plan: `{R['plan']}`. "
      f"Ledger rows 146 and 147. Pretend trades on past prices, after costs. Not advice and not a forecast.")
    w("")
    w("## Answer"); w("")
    for k in ("small", "wide"):
        S = res["setups"][k]
        w(f"- Set-up N = {S['n']} (ledger row {S['ledger_row']}): {'PASSES all four marks' if S['passes'] else 'FAILS'} "
          f"({sum(S['marks'].values())} of 4 marks hold). MEASURED.")
    w("")
    w("A pass means: worth running on the practice desk with pretend money as a slow sleeve, and the rule becomes the yardstick for AI stock pickers. It does not mean it makes money. STATED in the plan.")
    w("")
    w("## Period and data"); w("")
    w(f"- Ranking days: {res['ranking_days']}, from {res['first_ranking_day']} to {res['last_ranking_day']}. First purchase at the open of {res['first_purchase_day']}; held to the close of {res['last_day']}. MEASURED.")
    w(f"- Second half starts with the ranking day {res['second_half_first_ranking_day']}. MEASURED.")
    me = cov["month_end_lines"]
    w(f"- Member lines on a month-end: {min(m['lines'] for m in me)} to {max(m['lines'] for m in me)}; after keeping one share class per company and dropping lines with no price file: {min(m['with_series'] for m in me)} to {max(m['with_series'] for m in me)}. MEASURED.")
    rk = cov["ranking_days"]
    w(f"- Stocks that could be ranked on a ranking day: {min(r['rankable'] for r in rk)} to {max(r['rankable'] for r in rk)}; that could not (no close on one of the two month-ends): {min(r['unrankable'] for r in rk)} to {max(r['unrankable'] for r in rk)}. MEASURED.")
    nb = cov["lines_without_bars_by_year"]
    w("- Gap: member lines with no price on any of their days, by year: " + ", ".join(f"{y} {v['count']}" for y, v in nb.items()) + ". Every rule and yardstick b miss these alike. MEASURED.")
    w(f"- Gap: member lines whose prices stop before their removal day: {len(cov['bars_stop_before_removal'])} (most are takeovers whose last trade was a few days before removal). MEASURED.")
    w(f"- Inputs: members.csv sha256 `{inp['members_csv_sha256'][:16]}`, {inp['bars']['files']} price files sha256 `{inp['bars']['sha256'][:16]}`, config sha256 `{inp['config_replay_14_plan_sha256'][:16]}`. Full fingerprints in `research_rig/results_14.json`.")
    w("- UNKNOWN: whether the price feed adjusts for spin-offs. A spin-off inside a holding month may show as a fall.")
    w("")
    w("## The four marks, after costs"); w("")
    w(f"Cost {P['cost_bps_per_side']} basis points per side on what is traded. SPY pays one buy and one sell. STATED in the plan.")
    w("")
    spy = res["spy"]; ev = res["everyone"]
    for k in ("small", "wide"):
        S = res["setups"][k]; m = S["marks"]; rd = S["random"]; rp = S["reported"]
        w(f"### N = {S['n']}"); w("")
        w("| mark | this set-up | yardstick | result |"); w("|---|---|---|---|")
        w(f"| {MARKS['1_above_spy']} | {pc(S['total'])} | SPY {pc(spy['total'])} | {yn(m['1_above_spy'])} |")
        w(f"| {MARKS['2_above_everyone']} | {pc(S['total'])} | every member {pc(ev['total'])} | {yn(m['2_above_everyone'])} |")
        w(f"| {MARKS['3_above_random_percentile']} | {pc(S['total'])} | {rd['percentile']}th percentile of {rd['draws']} random baskets {pc(rd['value_at_percentile'])} (median {pc(rd['median'])}) | {yn(m['3_above_random_percentile'])} |")
        w(f"| {MARKS['4_above_spy_each_half']} | first {pc(S['first_half'])}, second {pc(S['second_half'])} | SPY first {pc(spy['first_half'])}, second {pc(spy['second_half'])} | {yn(m['4_above_spy_each_half'])} |")
        w("")
        w(f"Gaps next to this result: {rp['flagged_holdings']} holdings were sold at a last close because their prices stopped (flagged); "
          f"{rp.get('carried_through_gap', 0)} times a held stock had no open at a re-form and was carried at its last close; "
          f"{rp['short_baskets']} months had fewer than {S['n']} stocks with an open to buy; it beat {pc(rd['share_of_draws_beaten'], 0).lstrip('+')} of random baskets. "
          f"Without every flagged stock, removed from the start (uses hindsight, reported only): {pc(rp['total_without_flagged_hindsight'])}. MEASURED.")
        w("")
    w("## Reported, not judged"); w("")
    years = sorted(spy["by_year"])
    w("| year | N small | N wide | every member | SPY |"); w("|---|---|---|---|---|")
    for y in years:
        w(f"| {y} | {pc(res['setups']['small']['reported']['by_year'].get(y))} | {pc(res['setups']['wide']['reported']['by_year'].get(y))} | {pc(ev['by_year'].get(y))} | {pc(spy['by_year'].get(y))} |")
    w("")
    w(f"- Largest drop from a high, daily closes: N small {pc(res['setups']['small']['reported']['max_drop'])}, N wide {pc(res['setups']['wide']['reported']['max_drop'])}, every member {pc(ev['max_drop'])}, SPY {pc(spy['max_drop'])}. MEASURED.")
    w(f"- Share of the basket changed at a re-form, average: N small {pc(res['setups']['small']['reported']['mean_turnover'], 0).lstrip('+')}, N wide {pc(res['setups']['wide']['reported']['mean_turnover'], 0).lstrip('+')}, every member {pc(ev['mean_turnover'], 0).lstrip('+')}. MEASURED.")
    sc = res["scale"]
    w("- For scale, the same days, one buy and one sell: " + ", ".join(f"{s} {pc(v['total']) if v else 'no price on the first purchase day'}" for s, v in sc.items()) + ". MEASURED.")
    w(f"- Overlap with SPMO's holdings: {res['setups']['small']['reported']['spmo_overlap']}.")
    w("")
    if NE:
        w("## How often a mark passes by chance"); w("")
        w(f"MEASURED by `research_rig/test_14.py` on {NE['worlds']} made-up price sets with no momentum in them, run through the same scorer. Passes:")
        w("")
        w("| mark | N small | N wide |"); w("|---|---|---|")
        for k in list(MARKS) + ["all_four"]:
            w(f"| {MARKS.get(k, 'All four')} | {NE['passes']['small'][k]} | {NE['passes']['wide'][k]} |")
        w("")
    w("## How this can fool us"); w("")
    w("- Ten years, one long rising market with two sharp falls. Momentum rules are known to fall hard when a market turns. STATED in the plan.")
    w("- The member list is rebuilt from a public record of changes and checked against a second one; disagreements are listed off-repo in members_note.md. A missed change puts a stock in or out on the wrong days.")
    w("- Stocks with no price are left out of every rule alike; the counts are above.")
    w("- A basket of stocks that all rose for the same reason is close to one bet.")
    return "\n".join(o) + "\n"

if __name__ == "__main__":
    a = sys.argv[1:]
    src, out = HERE, PAGE
    if "--from" in a: src = a[a.index("--from") + 1]
    if "--out" in a: out = a[a.index("--out") + 1]
    open(out, "w").write(build(src))
    print("wrote", os.path.relpath(out, ROOT) if out.startswith(ROOT) else out)
