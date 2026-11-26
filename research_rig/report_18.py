"""Print Replay 18's result page. The saved JSON is the only file read."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

RESULT = Path(__file__).with_name("results_18.json")
# Recorded by the lead during the authorized run, not fields of the scorer JSON.
PUBLISHED_UTC = "2026-11-26 02:28 UTC"
CLAIMED_UTC = "2026-11-26 02:30:04 UTC"
PREFLIGHT = (("Funding", 3065, 320353), ("Mark", 3128, 2263673), ("Trade", 3177, 2238542))
FTT_STAMP_ANOMALIES = 0
REASONS = {
    "occupied_funding_coverage_gap": "Funding coverage gap in an open leg",
    "dated_accounting_fence": "Dated limit on this contract's accounting",
    "trade_gap_or_fence": "Trade gap or dated accounting limit",
}
CLASSES = {
    "non_perpetual_asset": "No separate underlying perpetual in the registered scope",
    "outside_registered_scope": "Outside the registered scope",
}
LABELS = {"robinhood": "Robinhood", "kalshi": "Kalshi", "coinbase": "Coinbase", "kraken": "Kraken"}


def pct(x):
    if x is None:
        return "undefined"
    return f"{x:+.4%}" if 0 < abs(x) < 0.00005 else f"{x:+.2%}"


def sr(x):
    return "undefined" if x is None else f"{x:+.3f}"


def pp(x):
    return f"{100 * x:+.2f}"


def stamp(hour):
    return datetime.fromtimestamp(hour * 3600, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def comparison(name, book):
    if book["refusal"] is not None:
        return f"| {name} | Refused: {book['refusal']} |"
    b = book["result"]
    return (f"| {name} | {pct(b['final'] - 1)} | {sr(b['sharpe'])} | {b['max_drawdown']:.2%} | "
            f"{sum(r > 0 for r in b['years'].values())} | {b['traded']} | {b['forced_count']} |")


def render(r, digest):
    book = r["judged"]["result"]
    marks, scope, rand = book["marks"], r["scope"], r["random"]
    years = book["years"]
    good_years = [y for y, value in years.items() if value > 0]
    plan = "[frozen plan](../../research_rig/PREREG_18_funding_carry.md)"
    print(f"""# Replay 18: funding carry

MEASURED. The three-day funding carry rule **{'passed' if all(marks) else 'did not pass'}**. At 12 bps per side on net changes in position size, it met **{sum(marks)} of {len(marks)} marks**, returned {pct(book['final'] - 1)} net, and had a daily net Sharpe of {sr(book['sharpe'])}.

STATED. The {plan} takes three low-funding longs and three high-funding shorts from a reconstructed subset of the saved monthly top 30. It uses a full funding-interval lag, then enters at the next hourly open. Only this turnover-only book at the judged cost has marks. It is not a result for all ranked coins or for US fills.

## Judged marks

| Mark | Measured | Verdict |
|---|---:|---|
| Net Sharpe at least 1.0 | {sr(book['sharpe'])} | {'met' if marks[0] else 'not met'} |
| Largest fall at most 25% | {book['max_drawdown']:.2%} | {'met' if marks[1] else 'not met'} |
| Positive in at least three of five years | {len(good_years)} of {len(years)}, {', '.join(good_years)} | {'met' if marks[2] else 'not met'} |

MEASURED. In percentage points of starting equity, price moves contributed {pp(book['price_pnl'])}, funding {pp(book['funding_pnl'])}, and fees {pp(-book['fees'])}. There were {book['qualified_slots']} qualified slots and {book['traded']} traded slots. There were {book['cash_slots']} cash slots, {book['too_few']} slots with too few names and {book['no_open']} with no usable opening fill.

| Year | Net return |
|---|---:|""")
    for y, value in years.items():
        print(f"| {y}{', partial' if y == max(years) else ''} | {pct(value)} |")

    print(f"""
## Forced closes

MEASURED. There were {book['forced_count']} forced closes. None was written to zero. The reasons below are the recorded accounting reasons, not claims about why the venue stopped printing data.

| UTC | Contract | Side | Recorded reason |
|---|---|---|---|""")
    for event in book["forced"]:
        print(f"| {stamp(event['hour'])} | {event['key'].split('/')[1]} | {event['side']} | {REASONS.get(event['reason'], event['reason'])} |")

    ftt = scope["ftt_coverage"]
    charge = book["ftt_stress"] is not None
    print(f"""
## FTT coverage

MEASURED. The FTT branch was `{ftt['branch']}`. {'The separate stress debit applied.' if charge else 'No separate stress debit applied, so there is no alternate uncharged line.'} The protected window was complete, although the full segment was not. The ordinary FTT forced close above is separate from that branch decision. The plan pinned {scope['ftt_checksum_pinned_archive_files']} FTT files by published checksum.

| FTT input | Whole segment | Protected window |
|---|---:|---:|""")
    for key, label in (("trade_bars", "Trade bars"), ("mark_bars", "Mark bars"), ("funding_settlements", "Funding settlements")):
        c = ftt["counts"][key]
        print(f"| {label} | {c['observed']:,} of {c['expected']:,} | {c['protected_observed']:,} of {c['protected_expected']:,} |")

    print(f"""
## What was covered

MEASURED. {scope['top_ids_with_dated_mapping']} of {scope['historical_top_ids']} distinct ranked IDs had dated mappings, and {scope['top_ids_with_any_archive']} had an archive. No scheduled saved rank page was missing. The judged book recorded {book['funnel']['rankable']:,} rankable name-slots out of {book['funnel']['scope']:,} in scope. The saved JSON has the full funnel and coverage exclusions by decision date and ID.

UNKNOWN. How many of all dead coins the rank provider retained. The archive has settlement times and finalized funding, not the publication time or revision history of those rates. The saved rank pages do not establish original publication or revision times either. The lags are proxies, not proof of what was known then.

MEASURED. These {len(scope['unmatched_judged_ids'])} saved ranked IDs lacked a dated mapping in the registered scope. Neither class proves that a contract never traded anywhere.
""")
    unmatched = scope["unmatched_judged_ids"]
    for key, label in CLASSES.items():
        entries = sorted((int(i), x["reason"]) for i, x in unmatched.items() if x["classification"] == key)
        print(f"### {label} ({len(entries)})\n")
        for i, reason in entries:
            print(f"- ID {i}: {reason}")
        print()
    print(f"""## Shown only: costs and full close and reopen

MEASURED. These alternatives have no marks. The saved all-false mark arrays are placeholders, not failed thresholds. For example, the 1 bp book was positive in {sum(v > 0 for v in r['shown_costs']['1']['result']['years'].values())} years but is not judged.

| Cost and turnover | Net return | Sharpe | Largest fall | Positive years | Traded | Forced closes |
|---|---:|---:|---:|---:|---:|---:|""")
    for fee, variant in sorted(r["shown_costs"].items(), key=lambda pair: int(pair[0])):
        print(comparison(f"{fee} {'bp' if fee == '1' else 'bps'}, net changes", variant))
    print(comparison("12 bps, gross full close and reopen", r["shown_gross_reopen"]))
    print(f"""
## Shown only: matched-pool random books

MEASURED. {rand['complete']} of {rand['requested']} random books completed. {rand['defined_sharpe']} had defined Sharpe, {rand['undefined_sharpe']} had undefined Sharpe and {rand['incomplete']} were refused. Of those with defined Sharpe, {rand['fraction_at_or_above_sharpe']:.1%} ({round(rand['defined_sharpe'] * rand['fraction_at_or_above_sharpe'])}) met or exceeded the judged Sharpe. This is a descriptive comparison, not a mark.

| Measure | 5th percentile | Median | 95th percentile |
|---|---:|---:|---:|""")
    for k, label, fmt in (("final", "Net return", pct), ("sharpe", "Sharpe", sr),
                          ("max_drawdown", "Largest fall", lambda a: f"{a:.2%}"),
                          ("fees", "Fees as a share of starting equity", lambda a: f"{a:.2%}"),
                          ("traded", "Traded slots", lambda a: f"{a:g}"),
                          ("too_few", "Slots with too few names", lambda a: f"{a:g}"),
                          ("no_open", "Slots with no usable open", lambda a: f"{a:g}")):
        values = rand["quantiles"][k]
        print(f"| {label} | " + " | ".join(fmt(values[q]) for q in ("0.05", "0.5", "0.95")) + " |")
    counts = Counter(rand["forced_counts"].values())
    print("\nMEASURED. Forced closes per random book: " +
          "; ".join(f"{n} in {count} books" for n, count in sorted(counts.items())) +
          ". The saved result keeps the counts by seed.")
    print(f"""
## Shown only: today's four US rosters

STATED. These are current lists applied to older Binance contract data. They look ahead to which products are available today. Each venue is separate, costs are assumptions per side, and the Binance inputs cannot establish US fills, fees or funding.
""")
    for venue, label in LABELS.items():
        meta = scope["us_rosters"][venue]
        print(f"### {label}\n\nMEASURED. {meta['mapped']} of {meta['original']} products mapped; "
              f"{meta['with_dated_segment']} had a dated segment. The results below are not judged.\n")
        for product, reason in meta["unmatched"].items():
            print(f"- Unmatched {product}: {reason}")
        for product in meta["mapped_but_no_dated_segment"]:
            print(f"- Mapped but no dated segment: {product}.")
        if meta["unmatched"] or meta["mapped_but_no_dated_segment"]:
            print()
        print("| Cost per side | Net return | Sharpe | Largest fall | Positive years | Traded | Forced closes |\n"
              "|---|---:|---:|---:|---:|---:|---:|")
        for fee, variant in sorted(r["shown_rosters"][venue].items(), key=lambda pair: int(pair[0])):
            print(comparison(f"{fee} {'bp' if fee == '1' else 'bps'}", variant))
        print()
    print(f"""## Run record

STATED. The lead reports that frozen commit `{r['frozen_commit']}` reached the remote main branch at {PUBLISHED_UTC}. The first clock preflight refused with `P18_SEAL_REFUSED` because the shell contained `GIT_CONFIG_COUNT` for GitHub proxy settings. The lead removed just that variable with `env -u GIT_CONFIG_COUNT` and repeated preflight. The refusal was before a claim, with no change to frozen files or inputs.

MEASURED in the lead's clock-only preflight. It reported {FTT_STAMP_ANOMALIES} FTT stamp anomalies. The counts were:

| Input | Files | Rows |
|---|---:|---:|""")
    for label, files, rows in PREFLIGHT:
        print(f"| {label} | {files:,} | {rows:,} |")
    print(f"""
MEASURED. The one-shot lock recorded consumption at {CLAIMED_UTC}, then completion. The [saved result](../../research_rig/results_18.json) binds ledger rows {r['ledger']} and {r['ledger_shown']} and has SHA-256 `{digest}`. The [reporter](../../research_rig/report_18.py) reads only that JSON.
""", end="")


if __name__ == "__main__":
    raw = RESULT.read_bytes()
    render(json.loads(raw), sha256(raw).hexdigest())
