"""Build doc 161 from the two off-repo Plan 69 aggregate files; reads no bars and no trade rows."""
import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research/161_plan_69_stock_sweep_search.md"
CUSTODY = Path("/home/user/workspace/rig/data")
SEARCH, SEARCH_SHA = "sweep_69_search.out", "b7a035f9ffcc5c3f0f2d1bd92c8264d8f15bc1ccfffc2f75bfe48b67990cdb61"
CHECK, CHECK_SHA = "sweep_69_validate2.out", "ad25bc12d20eea7208fa2b44e9f29406975d8998769608bde79ae1975ee62c09"
GRID_SHA = "1dc2e3f5d97959f80733047175123c5d625c7a85f2a13c94050343531186c2ef"
FREEZE = "2a5e95554f53cf2de4673efdb0f950dac60c1356"
LABELS = {
    "S1": "leveraged funds, late-day move carries on",
    "S2": "rebound overnight after forced late selling",
    "S3": "fade a late push into the close",
    "S4": "fade the opening gap",
    "S5": "fund and index gap closes by the close",
    "S6": "dealer hedging before the close",
    "S7": "buy late selling, hold overnight",
    "S8": "same half-hour repeats on later days",
    "S9": "pressure to cut risk before the close",
    "S10": "Friday to Monday reversal",
    "S11": "rebound after sharp selling on heavy volume",
}
FUND_WORDS = {"broad": "broad stock funds", "sector": "sector funds", "bond": "bond funds",
              "bull": "leveraged long funds", "inverse": "inverse funds"}
STATUS_WORDS = {"miss": "enough trades, missed the marks", "too_thin": "too few trades or days",
                "unpriced_exit": "not scorable: an exit had no print", "shown_short_unscored": "short side, shown only"}


def pinned(path, pin):
    raw = path.read_bytes()
    if pin is not None and hashlib.sha256(raw).hexdigest() != pin:
        raise SystemExit(f"report input differs from its pin: {path.name}")
    return raw


def table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"]
                     + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def bp(x):
    return "n/a" if x is None else f"{1e4 * x:+.1f}"


def tt(x):
    return "n/a" if x is None else f"{x:.2f}"


def render():
    cfg_raw = (ROOT / "config/thresholds.yaml").read_bytes()
    plan = json.loads(re.search(rb"^replay_69_plan:\n  value: (\{[^\n]+\})$", cfg_raw, re.M).group(1))
    marks = plan["marks"]
    grid_raw = pinned(ROOT / "research_rig/GRID_69.json", GRID_SHA)
    grid = json.loads(grid_raw)
    rows = [json.loads(line) for line in pinned(CUSTODY / SEARCH, SEARCH_SHA).splitlines() if line.strip()]
    check_raw = pinned(CUSTODY / CHECK, CHECK_SHA)
    check = json.loads(check_raw)
    if len(rows) != len(grid["rules"]) or {r["id"] for r in rows} != {r["id"] for r in grid["rules"]}:
        raise SystemExit("search rows do not match the grid")
    if {r["bars_sha256"] for r in rows} != {"29abd63c9b371cb61e7e21ff65197bdedbd8b96451f8adcad847003c5985cd9e"}:
        raise SystemExit("search rows are not all from the pinned archive")
    scored = [r for r in rows if "trades" in r]
    status = Counter(r["status"] for r in rows)
    cleared = [r for r in rows if r["status"] in ("finalist", "duplicate", "cap", "eligible")]
    if cleared:
        raise SystemExit("a rule cleared the marks: this page is written for the no-finalist outcome only")
    enough = [r for r in scored if r["status"] == "miss"]
    has_t = [r for r in scored if r["t"] is not None]
    best_all = max(has_t, key=lambda r: r["t"])
    best_enough = max((r for r in enough if r["t"] is not None), key=lambda r: r["t"])
    best_annual = max(scored, key=lambda r: r["annual_net_500"])
    best_annual_enough = max(enough, key=lambda r: r["annual_net_500"])
    positive = sum(r["net_mean"] is not None and r["net_mean"] > 0 for r in scored)
    positive_enough = sum(r["net_mean"] > 0 for r in enough)
    lost_clearly = sum(r["net_mean"] < 0 and r["t"] is not None and r["t"] <= -2 for r in enough)
    over2 = sum(r["t"] >= 2 for r in has_t)
    unpriced = [r for r in scored if r["status"] == "unpriced_exit" and r["t"] is not None]
    best_unpriced = max(unpriced, key=lambda r: r["t"])

    by = defaultdict(list)
    for r in rows:
        by[r["family"]].append(r)
    fam = []
    for f in sorted(by, key=lambda s: int(s[1:])):
        rs = by[f]
        sc = [r for r in rs if r.get("t") is not None]
        c = Counter(r["status"] for r in rs)
        b = max(sc, key=lambda r: r["t"]) if sc else None
        fam.append((f, LABELS[f], len(rs), c["miss"], c["too_thin"], c["unpriced_exit"],
                    tt(b["t"]) if b else "n/a", f'{b["trades"]:,}' if b else "n/a"))
    top = [(r["id"], LABELS[r["family"]], f'{r["trades"]:,}', STATUS_WORDS[r["status"]], tt(r["t"]), bp(r["net_mean"]),
            bp(r["net_mean_h1"]), bp(r["net_mean_h2"]), f'{r["annual_net_500"]:+.2%}')
           for r in sorted(has_t, key=lambda r: (-r["t"], r["id"]))[:10]]
    masked_pairs = ", ".join(f"{m} {d}" for m, d in check["masked_member_day_pairs"])
    drops = sum(r["masked_trade_drops"] for r in scored)
    missed_entries = sum(r["missed_entry_prints"] for r in scored)
    uni = grid["universe"]
    if set(uni) != {"stocks", *FUND_WORDS}:
        raise SystemExit("grid universe groups changed")

    return f"""<!-- Built by research_rig/build_doc161_plan69_search.py from the pinned aggregate files only. -->
# Plan 69 search: no stock or fund rule made the cut

MEASURED: None of the {len(scored)} scored rules met the search marks on US stocks and exchange-traded funds, {plan["first"]} to {plan["last"]}. The highest t of any rule was {tt(best_all["t"])} ({best_all["id"]}, {best_all["trades"]} trades, too few to count) against a bar of {marks["t"]}. Among the {len(enough)} rules with enough trades the highest t was {tt(best_enough["t"])}. There is no finalist, so the vault ({plan["vault_first"]} to {plan["vault_last"]}) stays sealed and Plan 69 is closed (ledger 217, queue 111).

## What was searched

STATED: {len(rows)} rules written before any price was read, in {len(by)} families, each family tied to a published reason why a price might move at a set time of day. {len(scored)} are long-only and scored; one short rule is shown only. The list was {len(uni["stocks"])} large stocks from a 2014 fund filing and {sum(len(v) for k, v in uni.items() if k != "stocks")} funds from dated exchange and issuer lists ({", ".join(f"{len(uni[k])} {w}" for k, w in FUND_WORDS.items())}), none chosen for being liquid or alive today. Trades are five-minute prints with $500 of settled cash, one position, one entry a day, whole shares, the measured half-spreads of doc 136 on each side, and no reuse of unsettled cash.

STATED: To count, a rule needed at least {marks["trades"]} trades on {marks["days"]} days with {marks["half_days"]} days in each half. To clear, it also needed positive net in both halves, a day-clustered t of {marks["t"]} against the same instrument held over the same clock on all days, t of {marks["half_t"]} in each half, positive net without its best {marks["trim"]:.0%} of trades, and {marks["annual"]:.0%} simple net a year on $500.

MEASURED, input check before any return (freeze `{FREEZE[:7]}`): {check["archive_rows"]:,} five-minute bars in the archive, {check["regular_rows"]:,} in regular hours, {check["sessions"]:,} sessions, {check["instruments_with_regular_rows"]} of {check["registered_instruments"]} listed instruments with bars, {check["active_member_days"]:,} instrument-days, {check["registered_splits"]} splits on file. {check["masked_member_days"]} instrument-day was left out whole for an unexplained price jump ({masked_pairs}), under the ruling made before any return was computed. No trade was dropped because of it ({drops} dropped).

## Result by family

MEASURED: t here is on net return minus the same-clock baseline, grouped by entry day. "Best t" is over every rule in the family that produced one, including rules too thin to count.

{table(("Family", "Idea", "Rules", "Enough trades, missed", "Too thin", "Not scorable", "Best t", "Trades in that rule"), fam)}

MEASURED: status of all {len(rows)} rules: {", ".join(f"{STATUS_WORDS[k]} {v}" for k, v in sorted(status.items(), key=lambda kv: -kv[1]))}.

## Ten highest t values

MEASURED: before the trade-count floor or any other mark. A high t on few trades is not a pass. Net is mean basis points a trade after costs; the last column is simple net a year on $500 with idle days at zero.

{table(("Rule", "Idea", "Trades", "Status", "t", "Net bp", "First half bp", "Second half bp", "Net a year"), top)}

## What it says

- MEASURED: {positive} of {len(scored)} scored rules had a positive net mean; of the {len(enough)} with enough trades, {positive_enough} did and {lost_clearly} lost clearly (negative net and t at or below -2).
- MEASURED: {over2} rules had t of 2 or more, both with fewer than {marks["trades"]} trades. None reached 3.
- MEASURED: the best simple net a year on $500 among rules with enough trades was {best_annual_enough["annual_net_500"]:+.2%} ({best_annual_enough["id"]}); over every scored rule it was {best_annual["annual_net_500"]:+.2%} ({best_annual["id"]}, {best_annual["trades"]} trades, t {tt(best_annual["t"])}, so no better than holding the same fund over the same clock on any day). The mark was {marks["annual"]:.0%}.
- MEASURED: {status["unpriced_exit"]} rules were not scorable because at least one entered trade had no print at its exit clock; the plan does not let a taken trade be erased. On their priced trades the highest t was {tt(best_unpriced["t"])} ({best_unpriced["id"]}), so none of them was near the bar either.
- MEASURED: {missed_entries:,} chosen entries across all rules had no print at the entry clock and were not replaced.

## Limits

- STATED: {status["too_thin"]} of {len(scored)} rules were too thin. On about 100 names and one entry a day, most of these triggers fire too rarely in six years to be judged at this bar. That is a limit of the grid, not evidence the ideas are false.
- STATED: the 16:00 and 09:30 prices are five-minute bar prints, not auction fills. Dividends are not credited. Costs are the measured half-spreads of doc 136, with the cautious bucket for unmeasured names; fees, impact and fill quality beyond that are UNKNOWN.
- STATED: the real-run numbers were not recomputed by a second program. The script found a planted rule on made-up data and stayed clean on 100 of 100 made-up worlds in audit; with no finalist to carry, no recompute was ordered.
- UNKNOWN: anything about 2022 onward. No vault price was read by this plan.

STATED: The search output and the input-check output are held off the repository under `/home/user/workspace/rig/data` with SHA-256 `{SEARCH_SHA}` and `{hashlib.sha256(check_raw).hexdigest()}`. The builder reads only those two files, the checked-in grid and the shared settings. See the [plan](../../research_rig/PREREG_69_stock_sweep.md) and the [sweep design](../150_discovery_sweep_design.md).
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render()
    if args.check:
        if OUT.read_text() != rendered:
            raise SystemExit("doc 161 differs from pinned aggregates")
    else:
        OUT.write_text(rendered)


if __name__ == "__main__":
    main()
