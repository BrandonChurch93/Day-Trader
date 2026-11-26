"""Rebuild doc 154 using only two pinned aggregate files and the checked-in grids."""
import argparse
import json
from statistics import median

from build_doc152_plan70_search import CUSTODY, ROOT, bp, checked, fmt_t, pp, table

OUT = ROOT / "docs/research/154_plan_71_second_coin_grid.md"
SUMMARY_SHA = "babd3544e7ae86bd13b9cbfeca7b4d3b72ee8b33fda4492c6ef6fab1a2dd5558"
CARRY_SHA = "843d20afbe0b0d5822a6cb899bfdbd6714b96ac2832be5b02f4fd66391437930"
GRID70_SHA = "ac16d46df925a3270b55563b82d5bf1a5d0bd4b4840b45f57a3ce8a286dc5842"
GRID71_SHA = "c41aa5189ca406a26fac733cc08f36e05d5af6a0d86e5afc192adf4cfb34efb5"


def block(rule):
    if rule["delay_hours"]:
        return "Delayed by one hour"
    if rule["btc_hedge"]:
        return "BTC hedge"
    if rule["top_coins"] == 2:
        return "Top two"
    if rule["side"] < 0:
        return "Mirror short, immediate"
    return "Long, immediate, 2-hour hold" if rule["hold_hours"] == 2 else "Long, immediate, other holds"


def render(root):
    raw = checked(root, "sweep_70/search71_summary.out", SUMMARY_SHA)
    receipt = json.loads(checked(root, "sweep_70/carry71_results.json", CARRY_SHA))
    grid70 = json.loads(checked(ROOT, "research_rig/GRID_70.json", GRID70_SHA))
    grid = json.loads(checked(ROOT, "research_rig/GRID_71.json", GRID71_SHA))
    header, *rows = map(json.loads, raw.splitlines())
    if (len(rows) != 112 or len(grid70) != 188 or [r["rule"] for r in rows] != [r["id"] for r in grid]
            or receipt["search71_sha256"] != SUMMARY_SHA or receipt["carried_ids"]):
        raise ValueError("aggregate files do not describe the accepted sweep")
    finalists = sorted((r for r in rows if r["finalist_rank"] is not None), key=lambda r: r["finalist_rank"])
    if ([r["rule"] for r in finalists] != [r["rule"] for r in receipt["forecasts"]]
            or header["sweep_finalists"] != [r["rule"] for r in finalists] + ["70-102"]
            or any(f["carry"] for f in receipt["forecasts"])):
        raise ValueError("unexpected finalist or carry list")
    by_id = {r["id"]: r for r in grid}
    groups = {}
    for row in rows:
        groups.setdefault(block(by_id[row["rule"]]), []).append(row)
    block_rows = []
    for name, g in groups.items():
        eligible = [r for r in g if not r["too_thin"]]
        stats = [r["paired_day_t"] for r in eligible if r["paired_day_t"] is not None]
        net = [r["plain_mean"] for r in eligible if r["plain_mean"] is not None]
        lost = sum(r["plain_mean"] < 0 and r["paired_day_t"] <= -2 for r in eligible
                   if r["plain_mean"] is not None and r["paired_day_t"] is not None)
        block_rows.append((name, len(g), len(eligible), sum((r["plain_mean"] or 0) > 0 for r in g), lost,
                           fmt_t(median(stats) if stats else None), fmt_t(max(stats, default=None)),
                           bp(median(net) if net else None)))

    def subgroup(side, predicate=lambda r: True):
        scores = [r for r in rows if by_id[r["rule"]]["side"] == side and predicate(by_id[r["rule"]])]
        means = [r["plain_mean"] for r in scores if r["plain_mean"] is not None]
        return len(scores), sum(m > 0 for m in means), sum(m < 0 for m in means), median(means)

    core = subgroup(1, lambda r: not r["delay_hours"] and not r["btc_hedge"] and r["top_coins"] == 1)
    late = subgroup(1, lambda r: r["delay_hours"] == 1)
    shorts = subgroup(-1)
    hedge = subgroup(1, lambda r: r["btc_hedge"])
    finalist_text = []
    for r, carry in zip(finalists, receipt["forecasts"]):
        rule = by_id[r["rule"]]
        p = rule["parameters"]
        detail = table(("Slice", "Tickets", "UTC dates", "Plain net bp", "Matched net bp", "Matched t"), [
            ("Whole", r["trades"], r["active_days"], bp(r["plain_mean"]), bp(r["paired_mean"]), fmt_t(r["paired_day_t"])),
            *((name, r["half_trades"][i], r["half_active_days"][i], bp(r["half_plain_mean"][i]),
               bp(r["half_paired_mean"][i]), fmt_t(r["half_paired_day_t"][i]))
              for i, name in enumerate(("2020 through 2021", "2022 through 2023")))])
        funding = ", ".join(f"{k} bp per hour: {pp(v)}" for k, v in r["funding_stress_simple_annual"].items())
        hold = "one hour" if rule["hold_hours"] == 1 else f'{rule["hold_hours"]} hours'
        finalist_text.append(f"""### {r["rule"]}

STATED: Compare the last completed hourly close with the close {p["lag"]} hour earlier. If BTC fell at least {p["threshold"]:.3f} in log terms, buy the non-BTC coin that fell strictly more than {p["multiple"]:.1f} times as much and has the largest excess drop. Break ties alphabetically; hold one position, unhedged, from that hourly open to the open {hold} later. Skip tickets that span maintenance.

{detail}

MEASURED: After dropping the best 1%, plain net was {bp(r["plain_trimmed_mean"])} bp a ticket. The simple annual result at 1x was {pp(r["simple_net_annual"])}. {r["unresolved_selected_tickets"]} selected tickets did not resolve. Funding sensitivities were {funding}; the spot-fee-only version was {pp(r["simple_spot_taker_fee_only_annual"])} simple a year.

MEASURED: {carry["passes"]:,} of {carry["draws"]:,} carry draws passed all vault marks at half the search mean ({carry["probability"]:.2%}, seed {carry["seed"]}). Not carried.""")

    counts = header["input_counts"]
    dropped = counts["rows_dropped_by_reason"]["wrong_close_clock"]
    kept = sum(counts["rows_kept_by_coin"].values())
    block_table = table(("Block", "Rules", "Eligible", "Above zero", "Lost clearly", "Median t", "Best t", "Median net bp"), block_rows)
    sections = "\n\n".join(finalist_text)
    return f"""<!-- Built from the pinned Plan 71 aggregates by research_rig/build_doc154_plan71_search.py. -->
# Plan 71 search: two new finalists, neither carried

MEASURED: The second grid used {len(grid)} rules, taking the sweep to {len(grid) + len(grid70)}. Two new rules qualified without taking 70-102's place. All three sweep finalist places were used. Both new rules fell short of the 33% carry line, so the vault stayed sealed and the search allowance is used up.

## What was searched

STATED: The second grid used the same 20-coin Binance global spot USDT proxy, January 2020 through December 2023, costs, adverse funding, matched baseline and cutoff as [Plan 70](152_plan_70_coin_sweep_search.md). It tested only the BTC overextension idea. The variants changed the size and length of the move, hold length, side, entry clock, BTC hedge or number of selected coins.

MEASURED: The input header reported {kept:,} rows kept, {dropped:,} wrong-close rows left missing and {kept+dropped:,} in-range rows. Only summaries are used here. No private ticket file or vault file is an input.

## Results by block

MEASURED: “Above zero” counts the plain net means for all rules, including thin ones. The t and median net columns use only eligible rules; “lost clearly” uses Doc 152's descriptive label, negative plain net and matched t at or below -2 on eligible rules.

{block_table}

MEASURED: All {core[0]} basic immediate longs had positive net means (median {bp(core[3])} bp). One hour later, {late[2]} of {late[0]} long rules were negative. Mirror shorts were negative in {shorts[2]} of {shorts[0]} rules including the three variant blocks. The hedged longs had {hedge[1]} positive rules out of {hedge[0]}, with a median of {bp(hedge[3])} bp, or {hedge[3]/core[3]:.0%} of the basic immediate-long median. These are block comparisons, not matched pairs. A high t alone did not make a rule a finalist.

## Finalists and carry

{sections}

## Limits and next steps

- **Repeated search:** The first grid had already selected this mechanism. These are the best of a 300-rule sweep on shared dates, not a second independent test.
- **Reachability:** The difference between the immediate and delayed entries raises a question about the first hourly print. [Doc 153](153_overextension_lead_outside_evidence.md) gives outside evidence and describes spread bounce, stale prints, outage artifacts and BTC beta. It does not prove which explains these results.
- **Venue and costs:** The roster uses hindsight and the prints are spot proxies, not measured US fills. Both finalists lose under the spot-fee-only comparison. True costs, funding and crash-hour depth are UNKNOWN.
- **Sealed vault:** No three-rule sweep finalist cleared carry. The existing ZEC gap in the vault is unchanged; no vault result exists.
- **Next:** Plan 72 is a separate fixed-rule check on Coinbase USD prints from 2017 through 2019, starting with a count and power gate. Its search-date repricing is shown as a diagnosis, not as an independent test.

STATED: The search summary and carry receipt hashes are `{SUMMARY_SHA}` and `{CARRY_SHA}`. The builder opens only those aggregates and the two checked-in grids.
"""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    result = render(CUSTODY)
    if args.check:
        if OUT.read_text() != result:
            raise SystemExit("doc 154 differs from its pinned aggregates")
    else:
        OUT.write_text(result)


if __name__ == "__main__":
    main()
