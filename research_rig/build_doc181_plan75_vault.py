#!/usr/bin/env python3
"""Builds docs/research/181_plan_75_heldback_result.md from four files held outside the repo.

Inputs (aggregate only, no price or fill row):
  the one official held-back run's stdout, the blind recompute's VAULT_RESULT.json,
  the recompute memo (three counterfactual aggregates are read from it), and the
  independent audit's made-up-data power table.
Each is pinned by SHA-256 below; the script refuses if a file differs.
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
WS = pathlib.Path("/home/user/workspace")
PINS = {
    WS / "rig/data/plan_75_vault_run.out": "39d43825bcb9c32d468793953eca7607d0ee641b90a41bd36248fe416eac8d20",
    WS / "rig/data/plan75_recompute/VAULT_RESULT.json": "673f9fef8072cebc765ac1c4933af51c245505bb6e3fc0dfa5dc974154c330c8",
    WS / "rig/data/plan75_recompute/VAULT_RECOMPUTE.md": "cb8c26a204917a41542d06d08510906e732b6169e008b5d76e112d1755d86310",
    WS / "out/plan75_vault_audit_delta.md": "5b71b7f5339e7f983076d8fea7a0b976a6644c68263a783fa5a633c985ae1b68",
}
OUT = ROOT / "docs/research/181_plan_75_heldback_result.md"


def load(path):
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != PINS[path]:
        sys.exit(f"REFUSE_PIN {path.name}")
    return blob.decode("utf-8")


def pct(x, d=1):
    return f"{100 * x:+.{d}f}%"


def upct(x, d=1):
    return f"{100 * x:.{d}f}%"


def one(pattern, text):
    found = re.findall(pattern, text)
    if len(found) != 1:
        sys.exit(f"REFUSE_PARSE {pattern!r}: {len(found)} matches")
    return found[0]


def main():
    paths = list(PINS)
    lines = load(paths[0]).splitlines()
    tag = lambda t: [json.loads(l[len(t) + 1:]) for l in lines if l.startswith(t + " ")]
    main_, harsh = tag("VAULT_MAIN")[0], tag("VAULT_HARSH_SHOWN_ONLY")[0]
    marks, adm = tag("VAULT_MARKS")[0], tag("ADMISSION_COIN_DAYS")[0]
    shown = {(s["cost_line"], s["book"]): s["summary"] for s in tag("VAULT_SHOWN_ONLY")}
    result = one(r"^VAULT_RESULT (\w+)$", "\n".join(l for l in lines if l.startswith("VAULT_RESULT")))
    rec = json.loads(load(paths[1]))
    memo = load(paths[2])
    audit = load(paths[3])

    p, h, b = main_["primary"], harsh["primary"], main_["btc"]
    y, hy = p["years"], h["years"]
    r75 = rec["75_bp_per_side"]
    r145 = rec["145_bp_per_side"]
    cf_warm = float(one(r"full-stretch net to `([\d.]+)` with 2,280 fills", memo))
    cf_both = float(one(r"gave `([\d.]+)` full-stretch net, 2,281 fills", memo))
    null0 = one(r"\| Null, no drift \| (\d+) / (\d+) ", audit)
    null1 = one(r"\| Null, 15% drift \| (\d+) / (\d+) ", audit)
    edge0 = one(r"\| Half anchor, no drift \| (\d+) / (\d+) ", audit)
    share = lambda t: upct(int(t[0]) / int(t[1]), 2)
    total_days = sum(adm.values())
    admitted = adm["PROVED"] + adm["INFERRED"]
    months = 34  # 2024-01-01 to 2026-10-31, the plan's fixed stretch
    per_year = (1 + p["net"]) ** (12 / months) - 1
    assert all(marks.values()) == (result == "PASS")
    assert p["net"] == shown[("main", "three_legs_200_cap")]["net"]

    o = []
    a = o.append
    a("# Plan 75, the held-back run: a coin trend rule with a stop that only moves up")
    a("")
    a("- Status: RECORD. Built by `research_rig/build_doc181_plan75_vault.py` from four aggregate files held outside the repo, each pinned by SHA-256; no price or fill row is in the repo.")
    a("- Plan and every rule change: [the plan](../../research_rig/PREREG_75_coin_trend_ratchet.md). Ledger row 225. Earlier stage on years the paper had seen: [doc 173](173_plan_75_repeat_result.md). Access dates: [doc 172](172_us_spot_access_dates_20_coins.md). Source of the idea: [doc 171](171_idea_round_50_swing_horizon.md).")
    a("- This is the judged test. The sealed stretch 2024-01-01 to 2026-10-31 was opened once, by the data custodian, from a clean checkout at commit `8a1397d`, after an independent audit of the code and a written go on the ledger. It cannot be run again.")
    a("")
    a("## Short answer")
    a("")
    a(f"- MEASURED: all four marks fixed before the run are met. Result line: `{result}`.")
    a(f"- MEASURED: after 75 bp a side the rule returned {pct(p['net'])} over {months} months, about {pct(per_year)} a year.")
    a(f"- MEASURED: all of the gain came in 2024 ({pct(y['2024'])}). 2025 was {pct(y['2025'])} and 2026 to the end of October {pct(y['2026'])}.")
    a(f"- MEASURED: at the harsher cost line of 145 bp a side, shown only, the rule lost: {pct(h['net'])}.")
    a("- Reading: a pass by the rules we set, and a thin one. It is not fast money. By the plan, a pass earns a forward practice card with pretend money and nothing else.")
    a("")
    a("## The four marks")
    a("")
    a("| Mark, fixed before any held-back price | Measured | Met |")
    a("|---|---|---|")
    a(f"| Net return above zero after 75 bp a side | {pct(p['net'], 2)} | {str(marks['positive_net']).lower()} |")
    a(f"| Above Bitcoin held at matched volatility, after its costs | {pct(p['net'], 2)} against {pct(b['matched_net'], 2)} (scale {b['scale']:.3f}; Bitcoin unscaled {pct(b['unscaled_net'], 2)}) | {str(marks['above_matched_btc_net']).lower()} |")
    a(f"| Largest fall from a high under 40% | {upct(p['drawdown'], 2)} | {str(marks['drawdown_under_ceiling']).lower()} |")
    a(f"| From the 2025-03-19 close, after the paper's sample, at least -10% | {pct(main_['after_paper_net'], 2)} | {str(marks['after_paper_at_or_above_floor']).lower()} |")
    a("")
    a("## The run in numbers")
    a("")
    a(f"- MEASURED, main line: {p['fill_count']} fills, {p['hold_days']['n']} holding spells, median hold {p['hold_days']['median']:.0f} days, 90th percentile {p['hold_days']['p90']:.0f} days, longest {p['hold_days']['max']} days, {p['hold_days']['over_60']} over 60 days. Costs paid on fills came to {upct(p['cost_on_fills'])} of starting capital. Daily Sharpe, yearly rate: {p['sharpe']:.2f}.")
    a(f"- MEASURED, harsh line, shown only: net {pct(h['net'])}; years {pct(hy['2024'])}, {pct(hy['2025'])}, {pct(hy['2026'])}; largest fall {upct(h['drawdown'])}; after the paper's sample {pct(harsh['after_paper_net'])}; costs on fills {upct(h['cost_on_fills'])} of starting capital; Bitcoin at matched volatility {pct(harsh['btc']['matched_net'])}.")
    legs = ", ".join(f"{k}-day {pct(shown[('main', k)]['net'])} (largest fall {upct(shown[('main', k)]['drawdown'])}, {shown[('main', k)]['fill_count']} fills)" for k in ("10", "20", "30"))
    a(f"- MEASURED, shown only, each leg alone at 75 bp a side: {legs}. At 145 bp: " + ", ".join(f"{k}-day {pct(shown[('harsh', k)]['net'])}" for k in ("10", "20", "30")) + ". The slower legs trade less and lost less to costs. This is a look after the fact and counts for nothing; a slower-leg rule would be a new plan on new data.")
    paper, paper_h = shown[("main", "the paper's rule as printed")], shown[("harsh", "the paper's rule as printed")]
    a(f"- MEASURED, shown only, the paper's nine-leg rule as printed: {pct(paper['net'])} at 75 bp a side (largest fall {upct(paper['drawdown'])}, {paper['fill_count']} fills, longest hold {paper['hold_days']['max']} days); {pct(paper_h['net'])} at 145 bp.")
    a("- MEASURED: the three-leg blend with the paper's 200% cap in place of our 100% gave the same book to the last digit, so the cap never bound.")
    a(f"- MEASURED from the access ledger: of {total_days} coin-days, {adm['PROVED']} were admitted on a dated full-trading notice, {adm['INFERRED']} on a dated report of the dollar order book opening plus seven days, and {adm['NOT_ADMITTED']} were not admitted. That is {upct(admitted / total_days)} admitted, {upct(adm['INFERRED'] / admitted)} of it on the weaker level.")
    a("")
    a("## Independent recompute")
    a("")
    a("- A helper who had not read the scorer, its tests, its audits or its output wrote a second implementation from the plan text alone, ran it on the same sealed inputs, and reported before being told any official number.")
    a(f"- MEASURED, 75 bp a side, official then recompute: net {pct(p['net'], 2)} and {pct(r75['primary_net'], 2)}; largest fall {upct(p['drawdown'], 2)} and {upct(r75['primary_drawdown'], 2)}; fills {p['fill_count']} and {r75['primary_fills']}; 2024 {pct(y['2024'], 2)} and {pct(r75['primary_calendar_year_net']['2024'], 2)}; 2025 {pct(y['2025'], 2)} and {pct(r75['primary_calendar_year_net']['2025'], 2)}; 2026 {pct(y['2026'], 2)} and {pct(r75['primary_calendar_year_net']['2026'], 2)}; after the paper's sample {pct(main_['after_paper_net'], 2)} and {pct(r75['after_paper_net'], 2)}; Bitcoin at matched volatility {pct(b['matched_net'], 2)} and {pct(r75['matched_btc_net'], 2)}.")
    a(f"- MEASURED: the recompute also has all four marks true and the same result line. At 145 bp a side: {pct(h['net'], 2)} and {pct(r145['primary_net'], 2)}.")
    a(f"- MEASURED: the two differ by {abs(p['net'] - r75['primary_net']) * 100:.2f} percentage points on the net return and by {abs(p['fill_count'] - r75['primary_fills'])} fills, almost all of it in 2024. That is larger than in the 2020 to 2023 stage, so the helper was then given the scorer and traced it.")
    a("- MEASURED cause: the first difference is the first day either book could invest, 2024-04-01. The plan says a leg waits for 90 valid daily returns before it carries risk. The official scorer keeps each leg's signal and stop running during that wait and only delays the money; the recompute did not let a signal begin until the wait was over. On 2024-04-01 the official book therefore bought eight coins whose signals had begun earlier, and the recompute waited for fresh signals.")
    a(f"- MEASURED: with that one choice switched in the recompute, its net moves from {pct(r75['primary_net'], 2)} to {pct(cf_warm, 2)}; also carrying signal state through days a coin was not admitted gives {pct(cf_both, 2)}, against the official {pct(p['net'], 2)}. What is left is a difference in how a target weight is turned into a coin amount at the open. No reading changes any mark.")
    a("- Lead agent's ruling: the plan text allows both readings, so this is an ambiguity in the plan and not an error in either implementation. The official figure stands because that code was frozen and audited before the run. The honest range for the result is +9.0% to +10.1%.")
    a("")
    a("## How much a pass like this proves")
    a("")
    a(f"- MEASURED by the independent auditor on made-up price worlds with no edge, same code and same four marks: {null0[0]} of {null0[1]} worlds passed ({share(null0)}); with a 15% yearly upward drift in coin prices, {null1[0]} of {null1[1]} ({share(null1)}). With half of the paper's stated edge planted, {edge0[0]} of {edge0[1]} passed ({share(edge0)}). The edge model in those worlds is the auditor's assumption.")
    a("- INFERENCE: the four marks are hard to pass by luck in those worlds, and they do not ask how big the edge is. A pass says the rule was not harmful and beat a like-risk Bitcoin hold in this stretch. It does not say the rule earns enough to matter.")
    a("- MEASURED: one of three calendar years was positive. Two of the older diagnostics borrowed from Replay 22, a Sharpe of 1.0 and most years positive, were not met here; that set was replaced by the four marks before any price, for the reason written in the plan.")
    a("")
    a("## What this does and does not show")
    a("")
    a("- It shows that a published trend rule, cut down to its three fastest legs before any test and not tuned after, on holds of days to weeks, did not lose money after realistic costs on years its authors had not seen, and stayed ahead of Bitcoin at the same risk.")
    a("- It does not show a way to make money quickly. The whole gain is one year, the two years since are both losses, and a harsher cost line turns the result negative.")
    a("- Costs decide it. The rule paid about a seventh of its capital in costs. What a small US account really pays per trade is now the first thing to measure.")
    a("- STATED limits carried from the plan: the 20 coins were picked with hindsight, which flatters a long-only rule by an unknown amount; Binance USDT bars stand in for a US venue; most admitted coin-days rest on the weaker access level; the paper's liquidity filter is not carried over; an earlier daily break rule of ours failed on overlapping dates.")
    a("- Next: practice card E10, a forward log of this rule on live US venue quotes with pretend money. It records the real spread at each order and whether orders are even placeable at $500. No real money follows from this result.")
    OUT.write_text("\n".join(o) + "\n")
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
