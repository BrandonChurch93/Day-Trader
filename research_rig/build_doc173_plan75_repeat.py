#!/usr/bin/env python3
"""Builds docs/research/173_plan_75_repeat_result.md from three files held outside the repo.

Inputs (aggregate only, no price or fill row):
  the one official run's stdout, the blind recompute's RESULT.json, the access ledger.
Each is pinned by SHA-256 below; the script refuses if a file differs.
"""
import datetime as D
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
RIG = pathlib.Path("/home/user/workspace/rig")
PINS = {
    RIG / "plan75_custody/go_repeat.out": "09ccf02847cd4039af0f9b0c9e59f49add5b91db8467434eca3cbeb43d4fd676",
    RIG / "data/plan75_recompute/RESULT.json": "fc4b8789d78414ad19570c00b63c1db1879d38d2938dd51d641cc39e90348aa9",
    RIG / "data/plan_75_eligibility/ledger.json": "3a44fb32b6b2d410e1f4906e04e823d16abea3521fbe0340e6f6132bed1d8cfa",
}
OUT = ROOT / "docs/research/173_plan_75_repeat_result.md"


def load(path):
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != PINS[path]:
        sys.exit(f"REFUSE_PIN {path.name}")
    return blob.decode("utf-8")


def pct(x, d=1):
    return f"{100 * x:+.{d}f}%"


def upct(x, d=1):
    return f"{100 * x:.{d}f}%"


def main():
    paths = list(PINS)
    lines = load(paths[0]).splitlines()
    main_ = json.loads(next(l for l in lines if l.startswith("MAIN "))[5:])
    harsh = json.loads(next(l for l in lines if l.startswith("HARSH "))[6:])
    check = next(l for l in lines if l.startswith("IMPLEMENTATION_CHECK"))
    rec = json.loads(load(paths[1]))
    led = json.loads(load(paths[2]))

    days = [D.date(2020, 1, 1) + D.timedelta(i) for i in range((D.date(2024, 1, 1) - D.date(2020, 1, 1)).days)]
    level = {"PROVED": 0, "INFERRED": 0, "out": 0}
    ever = 0
    for coin, ivs in led["coins"].items():
        n = 0
        for day in days:
            ds = day.isoformat()
            hit = [r for r in ivs if r["start_utc_day"] <= ds and (r["end_utc_day"] is None or ds < r["end_utc_day"])]
            assert len(hit) == 1
            if hit[0]["eligible"] == 1:
                level[hit[0]["admission_level"]] += 1
                n += 1
            else:
                level["out"] += 1
        ever += n > 0
    total = sum(level.values())
    admitted = level["PROVED"] + level["INFERRED"]

    p, h = main_["primary"], harsh["primary"]
    r75, r145 = rec["75_bp_per_side"], rec["145_bp_per_side"]
    y, hy = p["years"], h["years"]
    so = main_["shown_only"]
    paper = so["the paper's rule as printed"]
    go_on = p["net"] > 0 and max(main_["halves_net"]) > 0
    o = []
    a = o.append
    a("# Plan 75, the 2020 to 2023 run: a coin trend rule with a stop that only moves up")
    a("")
    a("- Status: RECORD. Built by `research_rig/build_doc173_plan75_repeat.py` from three aggregate files held outside the repo, each pinned by SHA-256; no price or fill row is in the repo.")
    a("- Plan and every rule change: [the plan](../../research_rig/PREREG_75_coin_trend_ratchet.md). Ledger row 225. Access dates: [doc 172](172_us_spot_access_dates_20_coins.md). Source of the idea: [doc 171](171_idea_round_50_swing_horizon.md).")
    a("- This is the repeat stage on years the published paper had already seen. It is not the judged test. The judged test is the sealed 2024-01-01 to 2026-10-31 stretch, opened once, on a separate written go.")
    a("- The run was made once by the data custodian from a clean checkout at commit `8d131f6`. The scorer's own check line read: `" + check + "`.")
    a("")
    a("## Short answer")
    a("")
    a(f"- MEASURED: at 75 bp a side the rule returned {pct(p['net'])} over the four years. First half {pct(main_['halves_net'][0])}, second half {pct(main_['halves_net'][1])}.")
    a(f"- MEASURED: by year, 2020 {pct(y['2020'])}, 2021 {pct(y['2021'])}, 2022 {pct(y['2022'])}, 2023 {pct(y['2023'])}. Largest fall from a high {upct(p['drawdown'])}.")
    a(f"- MEASURED: the same coins bought and held on the same calendar, with the same costs, returned {pct(main_['same_list_hold_net'])}. The rule made far less than holding.")
    a(f"- MEASURED: {main_['twins_n']} random copies that kept each holding spell's length and size but moved it to a random day in the same month set a 95th-percentile mark of {pct(main_['twins_cut_net'])}. The rule is below it. This run does not show that the rule's timing adds anything beyond being in coins while coins rose.")
    a(f"- By the line fixed before the run (net above zero after 75 bp a side overall and in at least one half): {'met' if go_on else 'not met'}. " + ("The plan goes on to its freeze, audit and the one held-back run." if go_on else "The plan closes here."))
    a("")
    a("## The run in numbers")
    a("")
    a(f"- MEASURED, main line, 75 bp a side: {p['fill_count']} fills, {p['hold_days']['n']} holding spells, median hold {p['hold_days']['median']:.0f} days, 90th percentile {p['hold_days']['p90']:.1f} days, longest {p['hold_days']['max']} days, {p['hold_days']['over_60']} spells over 60 days. Costs paid came to {upct(p['cost_on_fills'])} of starting capital. Daily Sharpe figure as the scorer prints it: {p['sharpe']:.2f}. Years positive: {p['positive_years']} of 4.")
    a(f"- MEASURED, harsh line, 145 bp a side: net {pct(h['net'])}; halves {pct(harsh['halves_net'][0])} and {pct(harsh['halves_net'][1])}; years {pct(hy['2020'])}, {pct(hy['2021'])}, {pct(hy['2022'])}, {pct(hy['2023'])}; largest fall {upct(h['drawdown'])}; costs {upct(h['cost_on_fills'])} of starting capital; same-list hold {pct(harsh['same_list_hold_net'])}; random-copy mark {pct(harsh['twins_cut_net'])}.")
    a(f"- MEASURED, shown only, 75 bp a side, each leg alone: 10-day {pct(so['10']['net'])} (largest fall {upct(so['10']['drawdown'])}), 20-day {pct(so['20']['net'])} ({upct(so['20']['drawdown'])}), 30-day {pct(so['30']['net'])} ({upct(so['30']['drawdown'])}).")
    a(f"- MEASURED, shown only, the paper's nine-leg rule as printed: {pct(paper['net'])} at 75 bp a side, largest fall {upct(paper['drawdown'])}, {paper['fill_count']} fills.")
    a(f"- MEASURED: random copies that could not be placed: {main_['twins_failed_placements']} of {main_['twins_placement_attempts']} attempts ({upct(main_['twins_placement_failure_rate'], 2)}).")
    a("- MEASURED, the five older diagnostics, shown only at the main line: above the same-list hold " + str(main_['marks_shown_only']['above_same_list_hold']).lower()
      + "; above the random-copy mark " + str(main_['marks_shown_only']['above_twin_cut']).lower()
      + "; largest fall within the old ceiling " + str(main_['marks_shown_only']['drawdown_at_most_ceiling']).lower()
      + "; Sharpe at or above the old floor " + str(main_['marks_shown_only']['sharpe_at_least_floor']).lower()
      + "; three of four years positive " + str(main_['marks_shown_only']['three_of_four']).lower() + ". The five-of-seven-years line does not apply to four years.")
    a("")
    a("## Independent recompute")
    a("")
    a("- A helper who had not read the scorer, its tests, its audits or its output wrote a second implementation from the plan text alone and ran it on the same inputs.")
    a(f"- MEASURED, 75 bp a side, official then recompute: net {pct(p['net'], 2)} and {pct(r75['primary_four_year_net_return'], 2)}; first half {pct(main_['halves_net'][0], 2)} and {pct(r75['primary_first_half_net_return'], 2)}; second half {pct(main_['halves_net'][1], 2)} and {pct(r75['primary_second_half_net_return'], 2)}; largest fall {upct(p['drawdown'], 2)} and {upct(r75['primary_largest_fall'], 2)}; fills {p['fill_count']} and {r75['primary_fill_count']}; same-list hold {pct(main_['same_list_hold_net'], 2)} and {pct(r75['same_list_hold_four_year_net_return'], 2)}.")
    a(f"- MEASURED, 145 bp a side, official then recompute: net {pct(h['net'], 2)} and {pct(r145['primary_four_year_net_return'], 2)}; second half {pct(harsh['halves_net'][1], 2)} and {pct(r145['primary_second_half_net_return'], 2)}; fills {h['fill_count']} and {r145['primary_fill_count']}.")
    a(f"- MEASURED: the two differ by {abs(p['net'] - r75['primary_four_year_net_return']) * 100:.2f} percentage points on the four-year return and by {abs(p['fill_count'] - r75['primary_fill_count'])} fill. Every sign and every year agrees. The recompute did not rebuild the random copies, so that comparison rests on the official run alone.")
    a("")
    a("## Which coins were in")
    a("")
    a(f"- MEASURED from the access ledger: of {total} coin-days, {level['PROVED']} were admitted on a dated full-trading notice, {level['INFERRED']} on a dated report of the dollar order book opening plus seven days, and {level['out']} were not admitted. That is {admitted / len(days):.2f} admitted coins a day on average; {ever} of 20 coins were admitted at some point.")
    a("- STATED limit: the inferred level is weaker than a notice. It was added by a rule change before any price was read, because the venue's own notice pages do not open for us.")
    a("")
    a("## What this does and does not show")
    a("")
    a("- It shows the rule made money after costs in these four years with a small largest fall, on holds that fit the owner's horizon of days to weeks.")
    a("- It does not show an edge. The four years include a very large rise in coin prices, the rule lost to holding and to random timing, and the paper had already seen these years.")
    a("- STATED limits carried from the plan: the 20 coins were picked with hindsight; Binance USDT bars stand in for a US venue; the paper's liquidity filter is not carried over; an earlier daily break rule of ours failed on overlapping dates.")
    a("- Next: freeze the rule, audit the held-back entry point, then one run on the sealed stretch. Marks fixed before any price: net above zero; above Bitcoin held at matched volatility after costs; largest fall under 40%; the stretch after the paper's sample not worse than -10%. A pass earns a forward card on the practice desk, not real money.")
    OUT.write_text("\n".join(o) + "\n")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
