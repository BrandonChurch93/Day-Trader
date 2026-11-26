"""Rebuild Doc 157 from pinned aggregates only. No bars, private plans, or tickets."""
import argparse
from hashlib import sha256
import json
from math import ceil, isclose, isfinite, sqrt
from statistics import NormalDist

from build_doc152_plan70_search import CUSTODY, ROOT, bp, fmt_t, table
from coverage_70 import read_snapshot

OUT = ROOT / "docs/research/157_plan_73_first_minute_diagnosis.md"
GO_SHA = "096c68b3abf97def82c6c65d75463cefe71685a0e5abac367d248e5ab00cdf8f"
COUNT_SHA = "1184602c216b6867c188307ed49d3f049e0bb2ca3a6b1dae6e07127817c0a633"
SEARCH_SHA = "babd3544e7ae86bd13b9cbfeca7b4d3b72ee8b33fda4492c6ef6fab1a2dd5558"
RULE = "71-013"
PLAN, EARLIER, LEDGER = 73, 72, 221
FIRST_DATED, LAST_DATED = 2017, 2019
# Ledger 221's two day-count scenarios and inherited test line.
DAY_SCENARIOS = (115, 315)
POWER_LINE = .33
T_LINE = 2.
EFFECT_SHARE = .5
SEARCH, HOURLY, REACH, LATE = ("frozen_search_plain_net", "coinbase_hourly_open",
                               "coinbase_reachable_minute", "coinbase_entry_5m_late")
CLOCKS = ((SEARCH, "Saved search net"), (HOURLY, "Coinbase hourly open print"), (REACH, "One minute after the hour"),
          (LATE, "Enter five minutes late"), ("coinbase_entry_15m_late", "Enter fifteen minutes late"),
          ("coinbase_worst_minute", "Worst price inside the minute"))


def pinned(root, path, digest, *, mode=None):
    raw = read_snapshot(root, path) if mode is None else read_snapshot(root, path, mode=mode)
    if sha256(raw).hexdigest() != digest:
        raise ValueError(f"immutable report input differs: {path}")
    return raw


def follow_on(full_search, reachable):
    # Reproduce ledger 221's back-of-envelope figure using its stated precision.
    mean_bp = round(full_search["plain_mean"] * 10000, 4)
    matched_t = round(full_search["paired_day_t"], 2)
    search_days = full_search["active_days"]
    rough_se = mean_bp / matched_t
    spread = rough_se * sqrt(search_days)
    edge = reachable * 10000 * EFFECT_SHARE
    normal = NormalDist()
    powers = [1 - normal.cdf(T_LINE - edge * sqrt(n) / spread) for n in DAY_SCENARIOS]
    needed = ceil(((T_LINE - normal.inv_cdf(1 - POWER_LINE)) * spread / edge) ** 2)
    return mean_bp, matched_t, search_days, spread, edge, powers, needed


def render(root):
    result = json.loads(pinned(root, "plan73/go.out", GO_SHA, mode=0o600))
    count = json.loads(pinned(root, "plan73/count.out", COUNT_SHA, mode=0o600))
    raw_search = pinned(root, "sweep_70/search71_summary.out", SEARCH_SHA)
    _, *rows = map(json.loads, raw_search.splitlines())
    full_search, = [r for r in rows if r["rule"] == RULE]
    total, compared = result["search_tickets"], result["compared_tickets"]
    years, coins = result["compared_by_year"], result["compared_by_coin"]
    yearly = result["reachable_net_mean_by_year"]
    drops, means, reading = (result[k] for k in ("dropped_by_exclusive_reason", "net_mean_by_clock", "reading_inputs"))
    against_open, against_search = (result[k] for k in ("paired_reachable_minus_coinbase_open",
                                                       "paired_reachable_minus_search"))
    reach_min = reading["search_mean_fraction"] * means[SEARCH]
    if not (total == count["search_tickets"] == full_search["trades"] == compared + sum(drops.values())
            and compared == sum(years.values()) == sum(coins.values()) == reading["compared_tickets"]
            and len(coins) == result["compared_coin_count"] and set(years) == set(yearly)
            and drops["outage_date"] == count["outage_date_exclusions"]
            and count["total_requests"] == count["hourly_requests"] + count["minute_requests"]
            and set(means) == {key for key, _ in CLOCKS} and all(isfinite(v) for v in means.values())
            and means[SEARCH] != 0. and reach_min == reading["reachable_minimum_mean"]
            and means[REACH] == reading["reachable_mean"] and means[SEARCH] == reading["search_mean"]
            and means[LATE] == reading["five_minute_late_mean"]
            and against_open["utc_entry_days"] == against_search["utc_entry_days"]
            and isclose(against_open["paired_mean_difference"], means[REACH] - means[HOURLY])
            and isclose(against_search["paired_mean_difference"], means[REACH] - means[SEARCH])):
        raise ValueError("aggregate report inputs do not reconcile")
    if not (result["kind"] == "shown_search_dates_not_a_test" and result["reading"] == "REACHABLE"
            and compared >= reading["minimum_compared_tickets"] and means[REACH] >= reach_min
            and means[LATE] > reading["five_minute_late_must_exceed"]):
        raise ValueError("unexpected reading or report kind")

    mean_bp, matched_t, search_days, spread, edge, powers, needed = follow_on(full_search, means[REACH])
    clock_rows = table(("Clock", "Mean net, bp", "Share of same-ticket search mean"),
                       [(label, bp(means[key]), f"{means[key] / means[SEARCH]:.1%}") for key, label in CLOCKS])
    year_rows = table(("UTC entry year", "Compared trades", "One-minute mean net, bp"),
                      [(y, years[y], bp(yearly[y])) for y in sorted(years)])
    margin = (means[REACH] - reach_min) * 10000

    return f"""<!-- Built from pinned aggregates by research_rig/build_doc157_plan73_diagnosis.py. -->
# Plan {PLAN}: about half the search gain was gone after the first minute

MEASURED: On the {compared} search trades with every Coinbase clock available, mean net fell from {bp(means[HOURLY])} basis points at the hourly open to {bp(means[REACH])} one minute after the hour. The fixed reading was **{result["reading"]}**, but the one-minute mean cleared its line by just {margin:.2f} bp. This was a diagnosis, not a pass. No money follows.

## What was asked

STATED: Could the over-extension rule's search gain survive an entry price someone could plausibly reach? Plan {EARLIER}'s earlier-date test closed at the power check before requesting minutes. [Doc 153](153_overextension_lead_outside_evidence.md) had warned that a sharp hourly open print might not be a price people could trade. Plan {PLAN} therefore repriced rule {RULE}'s own already-searched trades instead of opening a new dated test.

## What was compared

MEASURED: {compared} of {total} frozen search trades, on {against_open["utc_entry_days"]} UTC entry days, had every clock and entered every mean below. They covered {len(coins)} coins out of {len(count["candidate_pairs"])} candidate USD pairs. The request plan contained {count["total_requests"]:,} bounded requests: {count["hourly_requests"]:,} hourly and {count["minute_requests"]:,} minute requests.

- **No Coinbase print in any requested window:** {drops["no_pair_evidence_at_ticket"]} trades, or {drops["no_pair_evidence_at_ticket"] / total:.1%} of the original search trades.
- **Named outage dates:** {drops["outage_date"]} trades were set aside before requests were planned.
- **Missing prices after those exclusions:** {drops["missing_hourly_open"]} trades were missing an hourly open; {drops["missing_minute"]} more were dropped for a missing minute.

STATED: Every Coinbase clock uses the same judged costs and funding. The one-minute line uses the midpoint of that minute's high and low, with the fixed fallback for a missing candle. The two late-entry lines keep the same exit. Worst-of-minute buys at the high and sells at the low.

{clock_rows}

MEASURED: On the same trades, the one-minute price gave up {abs(against_open["paired_mean_difference"])*10000:.1f} bp against Coinbase's hourly open (paired t {fmt_t(against_open["utc_day_clustered_t"])}, clustered by UTC entry day). It gave up {abs(against_search["paired_mean_difference"])*10000:.1f} bp against the saved search net (paired day-clustered t {fmt_t(against_search["utc_day_clustered_t"])}).

{year_rows}

MEASURED: The fixed reading required at least {reading["minimum_compared_tickets"]} complete trades, a one-minute mean at least {reading["search_mean_fraction"]:.0%} of the same trades' search mean, and positive net at the five-minute entry. The one-minute mean kept {means[REACH]/means[SEARCH]:.1%} against that {reading["search_mean_fraction"]:.0%} line ({bp(reach_min)} bp). The margin was {margin:.2f} bp; the five-minute mean was {bp(means[LATE])} bp.

## What it does not show

- **STATED, selection:** These are the search's own selected trades. Selection flatters every figure here; the diagnosis is not fresh evidence that the rule earns money.
- **UNKNOWN, fills:** A candle midpoint is not an order fill. The worst-of-minute line lost money, and actual spreads, depth and prices reached are not measured here.
- **UNKNOWN, coverage:** About half of the search trades were in coins for which Coinbase showed no print at their ticket time. Empty windows do not prove a coin was unlisted. The result cannot tell us what those trades would have earned on Coinbase.

## Follow-on sum, not a test

STATED: To reproduce the sum in [ledger row {LEDGER}](../../research_rig/TRIAL_LEDGER.md), take rule {RULE}'s plain search mean of {mean_bp:.4f} bp, its matched day t rounded to {matched_t:.2f}, and its {search_days} active days from the [pinned Plan 71 search summary used for Doc 154](154_plan_71_second_coin_grid.md). Dividing that mean by the t and multiplying by the square root of the search days gives a rough day spread of about {spread:.0f} bp. The t is for matched net, not the plain mean, so this is a scale estimate, not a direct measurement of daily standard deviation.

STATED: Taking {EFFECT_SHARE:.0%} of the reachable mean gives an assumed edge of {edge:.1f} bp. With independent signal days and a normal approximation for clearing a one-sided t line of {T_LINE:.1f}, the sum gives about {powers[0]:.0%} power on the {DAY_SCENARIOS[0]} days counted for Plan {EARLIER}, and {powers[1]:.0%} even on {DAY_SCENARIOS[1]} days. It takes about {needed:,} separate signal days to reach {POWER_LINE:.0%} on that measure. This is a planning sum for the t line alone, not a scored return or a forecast of meeting every test mark.

STATED: No pooled dated test was opened because the available unspent history does not supply enough signal days. The {FIRST_DATED} to {LAST_DATED} dates and the coin vault remain unspent; the [E09 pretend-money forward log](../../practice/traders/E09_overextension_dip_buy.md) continues. No reading is a pass or authorizes money.

STATED: The builder reads only the Plan {PLAN} go and count aggregates and the Plan 71 search summary. Their SHA-256 pins are `{GO_SHA}`, `{COUNT_SHA}` and `{SEARCH_SHA}`, respectively.
"""


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    page = render(CUSTODY)
    if args.check:
        if OUT.read_text() != page:
            raise SystemExit(f"doc {OUT.name} differs from its pinned aggregates")
    else:
        OUT.write_text(page)


if __name__ == "__main__":
    main()
