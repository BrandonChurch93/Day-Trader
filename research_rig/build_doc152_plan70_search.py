"""Build doc 152 from the accepted aggregate Plan 70 files; no bars or ticket vectors."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

import yaml

from coverage_70 import read_snapshot

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research/152_plan_70_coin_sweep_search.md"
CUSTODY = Path("/home/user/workspace/rig/data")
SEARCH_SHA = "13e5375a3ed8207eb07fee034af0d7fba088bebbdce951a234bbd61373a1b607"
CARRY_SHA = "6837579d1e6b805cb2c5aa679b2c7b6a75cc244c604c57c8b7c3a3f7ea4e09cf"
GRID_SHA = "ac16d46df925a3270b55563b82d5bf1a5d0bd4b4840b45f57a3ce8a286dc5842"
# Only the fields rendered in doc 152, from the config pinned at build commit b3cd740.
REPORT_SETTINGS = {
    "funding_adverse_bp_per_hour": 1,
    "spot_taker_round_trip_bp": 160,
    "search_marks": {
        "min_trades": 200,
        "min_days": 100,
        "min_days_each_half": 40,
        "full_t": 3.5,
        "half_t": 1.5,
        "trim_share": 0.01,
        "annual_min": 0.12,
    },
    "vault_marks": {"min_pre_vault_power": 0.33},
}


def checked(root, rel, pin):
    raw = read_snapshot(root, rel)
    if hashlib.sha256(raw).hexdigest() != pin:
        raise ValueError(f"immutable report input differs: {rel}")
    return raw


def report_settings(root):
    cfg = yaml.safe_load(read_snapshot(root, "config/thresholds.yaml"))

    def select(actual, expected, path):
        if isinstance(expected, dict):
            if not isinstance(actual, dict):
                raise ValueError(f"immutable report threshold differs: {path}")
            selected = {}
            for key, pin in expected.items():
                field = f"{path}.{key}"
                if key not in actual:
                    raise ValueError(f"immutable report threshold missing: {field}")
                selected[key] = select(actual[key], pin, field)
            return selected
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f"immutable report threshold differs: {path}")
        return actual

    layout = {"replay_70_plan": {"value": REPORT_SETTINGS}}
    return select(cfg, layout, "config/thresholds.yaml")["replay_70_plan"]["value"]


def measure(custody):
    search = checked(custody, "sweep_70/search_summary.out", SEARCH_SHA)
    receipt = json.loads(checked(custody, "sweep_70/carry_results.json", CARRY_SHA))
    grid = json.loads(checked(ROOT, "research_rig/GRID_70.json", GRID_SHA))
    cfg = report_settings(ROOT)
    header, *rows = map(json.loads, search.splitlines())
    if [r["rule"] for r in rows] != [r["id"] for r in grid] or len(rows) != 188:
        raise ValueError("unexpected search grid")
    chosen = [r for r in rows if r["finalist_rank"] is not None]
    if (len(chosen) != 1 or chosen[0]["rule"] != "70-102" or receipt["carried_ids"]
            or receipt["search_summary_sha256"] != SEARCH_SHA
            or len(receipt["forecasts"]) != 1 or receipt["forecasts"][0]["rule"] != chosen[0]["rule"]):
        raise ValueError("receipt does not report the accepted single finalist and no carry")
    return header["input_counts"], rows, chosen[0], receipt, grid, cfg


def bp(x):
    return f"{x * 10000:+.1f}" if x is not None else "n/a"


def pp(x):
    return f"{x:+.2%}"


def fmt_t(x):
    return f"{x:.2f}" if x is not None else "n/a"


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |",
                      *("| " + " | ".join(map(str, row)) + " |" for row in rows)])


def render(custody):
    counts, rows, finalist, receipt, grid, cfg = measure(custody)
    kept = counts["rows_kept_by_coin"]
    drops = counts["rows_dropped_by_reason_and_coin"]["wrong_close_clock"]
    bad = counts["rows_dropped_by_reason"]["wrong_close_clock"]
    if sum(drops.values()) != bad or set(kept) != set(drops):
        raise ValueError("input counts do not reconcile")
    full = defaultdict(list)
    for row in rows:
        full[row["family"]].append(row)
    fam = []
    for name, group in sorted(full.items()):
        eligible = [r for r in group if not r["too_thin"]]
        t = [r["paired_day_t"] for r in eligible if r["paired_day_t"] is not None]
        net = [r["plain_mean"] for r in eligible if r["plain_mean"] is not None]
        lost = sum(r["plain_mean"] < 0 and r["paired_day_t"] <= -2
                   for r in eligible if r["plain_mean"] is not None and r["paired_day_t"] is not None)
        fam.append((name.replace("_", " "), len(group), len(eligible), lost, fmt_t(max(t, default=None)),
                    bp(median(net) if net else None), bp(max(net, default=None))))
    ranked = sorted((r for r in rows if r["paired_day_t"] is not None),
                    key=lambda r: (-r["paired_day_t"], r["rule"]))[:10]
    top = table(("Rule", "Family", "Trades", "UTC dates", "Eligible", "Matched t", "Plain net bp"),
                [(r["rule"], r["family"].replace("_", " "), r["trades"], r["active_days"],
                  "no" if r["too_thin"] else "yes", fmt_t(r["paired_day_t"]), bp(r["plain_mean"])) for r in ranked])
    f, carry = finalist, receipt["forecasts"][0]
    rule = next(r for r in grid if r["id"] == f["rule"])
    params, opts = rule["parameters"], cfg["search_marks"]
    owner = (ROOT / "research_rig/PREREG_70_coin_sweep.md").read_text().split(
        "### Rule 70-102 in plain words\n\n", 1)[1].split("\n\n", 1)[0]
    halves = table(("Search slice", "Trades", "UTC dates", "Plain net bp", "Matched net bp", "Matched t"), [
        ("Whole", f["trades"], f["active_days"], bp(f["plain_mean"]), bp(f["paired_mean"]), fmt_t(f["paired_day_t"])),
        *((p, f["half_trades"][i], f["half_active_days"][i], bp(f["half_plain_mean"][i]),
           bp(f["half_paired_mean"][i]), fmt_t(f["half_paired_day_t"][i]))
          for i, p in enumerate(("2020 through 2021", "2022 through 2023")))])
    fees = ", ".join(f"{k} bp per hour: {pp(v)}" for k, v in f["funding_stress_simple_annual"].items())
    return f"""<!-- Built by research_rig/build_doc152_plan70_search.py from the pinned aggregate files only. -->
# Plan 70 search: one coin rule made the cut, none carried

MEASURED: One of {len(rows)} rules met the search marks. Its carry forecast passed in {carry["passes"]:,} of {carry["draws"]:,} draws ({carry["probability"]:.2%}), below the {cfg["vault_marks"]["min_pre_vault_power"]:.0%} bar. Nothing carried; the Plan 70 search closed and the vault stayed sealed (ledger 218, queue 112).

## What was searched

STATED: Search ran on hourly Binance global spot USDT bars for {len(kept)} coins, January 2020 through December 2023. The grid tested price fades, clock effects, shocks, ranges, BTC lead and relative moves. Trades used the next hourly open, at most one gross-1x ticket at a time, with rules fixed before the successful run. Net includes the frozen round-trip costs and {cfg["funding_adverse_bp_per_hour"]} bp of adverse funding per gross leg per hour. The matched t compares net with the same coin, UTC hour and holding period, using that block's own-date-inclusive baseline and grouping tickets by UTC entry date.

STATED: Eligibility required at least {opts["min_trades"]} resolved trades on {opts["min_days"]} dates, including {opts["min_days_each_half"]} dates in each half. The marks also required positive plain net in all three slices, matched t of {opts["full_t"]} overall and {opts["half_t"]} in each half, positive mean after trimming the best {opts["trim_share"]:.0%}, and at least {opts["annual_min"]:.0%} simple net a year.

MEASURED: {sum(kept.values()) + bad:,} in-range rows; {sum(kept.values()):,} kept and {bad:,} wrong-close rows left missing. The first authorized attempt stopped in the loader with no summary. The refrozen input check and successful search used the same loader.

{table(("Coin", "Rows kept", "Wrong close"), [(c, f"{kept[c]:,}", drops[c]) for c in sorted(kept)])}

## Families and raw leaderboard

MEASURED: The family statistics use only rules meeting the sample floors. “Lost clearly” is a report label, not a preregistered gate: negative plain net and matched t at or below -2. A family with no eligible rule has no summary statistic. Net is mean basis points per resolved trade.

{table(("Family", "Rules", "Eligible", "Lost clearly", "Best matched t", "Median net bp", "Best net bp"), fam)}

MEASURED: These are the ten highest defined matched t values, before sample floors or other marks. A high t on thin data is not a pass.

{top}

## The only finalist

MEASURED: {f["rule"]}, BTC overextension fade. The grid was {params["lag"]} hours, BTC threshold {params["threshold"]:.3f} in log-price terms, {params["multiple"]:.1f} times BTC and a {rule["hold_hours"]}-hour hold. {f["unresolved_selected_tickets"]} selected tickets did not resolve; they are not included in the payoffs.

{owner}

{halves}

MEASURED: Net after trimming the best {opts["trim_share"]:.0%} of tickets was {bp(f["plain_trimmed_mean"])} bp per trade. The cost-model result was {pp(f["simple_net_annual"])} simple net per year at 1x, not a compounded or live return. Funding sensitivity for the same tickets was {fees}; the {cfg["spot_taker_round_trip_bp"]} bp round-trip spot-fee comparison lost at {pp(f["simple_spot_taker_fee_only_annual"])} simple net per year.

MEASURED: At half the search mean, the fixed seven-day block forecast (seed {carry["seed"]}) cleared all vault marks jointly in {carry["passes"]:,} of {carry["draws"]:,} draws. {carry["probability"]:.2%} did not meet the {cfg["vault_marks"]["min_pre_vault_power"]:.0%} carry bar. This forecast does not use any vault observation.

## Limits and next steps

- **Spot proxy:** These are global spot prints, not measured fills on the named US contracts. Real funding, slippage and size feasibility are UNKNOWN.
- **Hindsight list:** The roster was selected with a later view of which coins existed and were eligible, so it is not a live 2020 roster.
- **Selection:** The finalist was best of {len(rows)} tests on the same dates; its t and net are not independent evidence. The spot-fee version lost and {f["unresolved_selected_tickets"]} selected tickets did not resolve.
- **Vault gap:** ZEC lacks February through June 2024 in custody. Those months stay missing, with no downloads. No Plan 70 vault price was read, so vault performance is UNKNOWN.
- **Next:** No Plan 70 vault run. The rule is followed forward on live prices with pretend money as practice card E09 (queue 114), shown as a lead and not a pass. Amendment 3 allows Plan 71 to search a second grid on the same dates. Rule {f["rule"]} already used one of the sweep's three finalist places. Any new finalist must clear the same carry check before the one shared vault use and, after a vault pass, the separate US print, funding and size check.

STATED: The aggregate search and carry files are under `/home/user/workspace/rig/data/sweep_70`, with SHA-256 values `{SEARCH_SHA}` and `{CARRY_SHA}`. The builder reads only those two aggregates and the checked-in grid, settings and rule description. See the [Plan 70 design](../../research_rig/PREREG_70_coin_sweep.md) and [Amendment 3](../150_discovery_sweep_design.md).
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render(CUSTODY)
    if args.check:
        if OUT.read_text() != rendered:
            raise SystemExit("doc 152 differs from pinned aggregates")
    else:
        OUT.write_text(rendered)


if __name__ == "__main__":
    main()
