"""Render Replay 20 from the pinned saved result. No scorer or market inputs."""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from statistics import fmean

RESULT_SHA = "285c74cbe2573fe51b08b0672f84293dbb3e2e53b599884c862278d6368fe6a2"


def pct(x, digits=3):
    return f"{x:+.{digits}%}"


def row(*cells):
    return "| " + " | ".join(map(str, cells)) + " |"


def render(data):
    o, p, job = data["outcome"], data["policy"], data["job"]
    judged, verdict = o["judged"], o["judgment"]
    n, mean = judged["count"], verdict["mean"]
    years, pool = judged["by_year"], verdict["placebo_pool_by_year"]
    clean_pool = o["shown_clean_ordinary"]["placebo_pool_by_year"]
    marks = verdict["marks"]
    counts, skips = o["notice_disposition"], o["ordinary_calendar_skips"]
    controls = o["ordinary_trade_counts_by_source"]
    checks = [
        ("count", f"At least {p['min_trades']} judged trades", n),
        ("mean", "Mean net return above zero", pct(mean, 4)),
        ("placebo", f"Mean net above the {p['placebo_percentile']}th percentile of control draws",
         f"{pct(mean, 4)} versus {pct(verdict['placebo_cut'])}"),
        ("trimmed", f"Positive mean without the best {p['drop_best']} trades", pct(verdict["trimmed_mean"])),
        ("t_stat", f"Per-trade t at least {p['min_t_stat']:.1f}", f"{verdict['t_stat']:.3f}"),
    ]
    if ({k for k, _, _ in checks} != set(marks) or verdict["passes"] != all(marks.values())
            or n != sum(x["count"] for x in years.values()) or n != counts["traded"] or mean != judged["mean"]
            or sum(counts.values()) != o["first_notices"]
            or sum(pool.values()) != sum(controls.values())
            or skips["total"] != sum(s["count"] for s in skips["by_symbol_month"])):
        raise ValueError("saved result does not reconcile")
    passed = sum(marks.values())
    concentrated = sum(years[y]["count"] for y in ("2025", "2026"))
    recent = years["2026"]
    share = recent["count"] * recent["mean"] / (n * mean)
    began = datetime.fromisoformat(job["started_utc"]).strftime("%Y-%m-%d %H:%M:%S UTC")
    shown = (
        (f"Same listings, {p['shown_bps']} bps per side", o["higher_fee"]),
        ("US-today symbol filter, Binance prices", o["us_today"]),
        ("Hourly proxy, 25% jump screen", o["hourly_25pct"]),
        ("Hourly proxy, without jump screen", o["hourly_all_jumps"]),
        ("Hourly proxy, screened entry one candle earlier", o["hourly_earlier_25pct"]),
        ("High strictly after the notice candle", o["shown_post_notice_high"]),
        ("Terminal cover at last close", o["shown_last_close"]),
        ("Continue after a missing in-hold bar", o["shown_missing_hold_bar_continuation"]["listing"]),
    )
    lines = [
        "# Replay 20. Short after an Upbit listing and a red UTC day", "",
        f"MEASURED. Replay 20 {'passed' if verdict['passes'] else 'did not pass'} "
        f"**{passed} of {len(marks)} marks** on already viewed dates. "
        f"The unlevered listing book averaged {pct(mean, 4)} net per trade over {n} trades, "
        f"at {p['judged_bps']} bps per side plus funding. This is the second counted trading-replay pass "
        "in about 26 tests, not evidence of US execution or an independent test on unseen dates.", "",
        "STATED. The [frozen rule](../../research_rig/PREREG_20_upbit_listing_short.md) starts with the first "
        "Upbit KRW notice for each dated asset. It waits for the first down UTC day among the notice day and "
        f"the following two days, then shorts at {p['entry_hour_utc']:02}:00 UTC the next day. Cover at the "
        f"highest high from the notice candle through the last pre-entry candle, capped at "
        f"{p['stop_cap_pct']}% above entry, or after {p['hold_hours']} hours. "
        "Shorts that are opened stay in the book, including adverse covers when the data or contract ends.", "",
        "## Five judged marks", "",
        row("Mark", "Measured", "Verdict"), row("---", "---:", "---"),
    ]
    lines.extend(row(label, value, "met" if marks[key] else "not met") for key, label, value in checks)
    lines.extend([
        "",
        f"MEASURED. The median was {pct(judged['median'])}; {judged['winners']:.1%} won and "
        f"{judged['stopped']:.1%} stopped. Funding averaged {pct(judged['funding'])} of entry notional "
        "per trade; the net returns already include it.", "",
        "## Listing trades by year", "",
        row("UTC year", "Trades", "Mean net", "Median net", "Mean funding", "Stopped", "Worst"),
        row("---", "---:", "---:", "---:", "---:", "---:", "---:"),
    ])
    for year, x in sorted(years.items()):
        lines.append(row(year, x["count"], pct(x["mean"]), pct(x["median"]), pct(x["funding"]),
                         f"{x['stopped']:.1%}", pct(x["worst"])))
    lines.extend([
        "",
        f"MEASURED. 2025 and the partial 2026 year account for {concentrated} of {n} trades. "
        f"2026 averaged {pct(recent['mean'], 1)} and supplied {share:.0%} of the summed net returns "
        "at equal entry notional. This sum is not the return of a portfolio.", "",
        "## Notice disposition and stress charges", "",
        f"MEASURED. There were {o['first_notices']} first notices at the frozen cutoff "
        f"({p['last_event_utc']}). Of those, {o['trading_at_notice']} had an eligible contract trading at "
        "publication. The counts below reconcile to the full first-notice set.", "",
        row("Disposition", "Count"), row("---", "---:"),
    ])
    lines.extend(row(label, counts[key]) for key, label in (
        ("traded", "Traded"), ("no_red_day", "Trading at notice, no qualifying red day"),
        ("not_trading_at_notice", "Not trading at notice"), ("no_fill", "Otherwise eligible, no fill"),
        ("other", "Other")))
    ordinary_debit = o["ordinary_missing_funding_debits"]["ordinary"]
    lines.extend([
        "",
        f"MEASURED. The listing book had {judged['missing_funding_settlements']} labelled missing settlement "
        f"on {judged['missing_funding_trades']} trade, with a stress debit of "
        f"{pct(-judged['missing_funding_debit_sum_entry_notional'])} of that trade's entry notional. "
        f"The ordinary book separately charged {ordinary_debit['settlements']} missing settlement on "
        f"{ordinary_debit['trades_with_debit']} control trade, "
        f"{pct(-ordinary_debit['debit_sum_entry_notional'])} of its entry notional. These were adverse charges, "
        "not recovered funding rates. The rule applies the larger of "
        f"{p['missing_funding_floor_pct']:.0f}% or the largest absolute pinned rate for the contract to "
        "that settlement's mark notional, not to entry notional.", "",
        "## Ordinary-jump controls", "",
        f"MEASURED. The {verdict['placebo_draws']:,} year-matched control draws averaged "
        f"{pct(fmean(verdict['placebo_set_means']), 2)} per trade across the draw means. "
        f"The judged pool held {sum(pool.values())} trades: {controls['store_symbols']} from the Plan 16 "
        f"store and {controls['supplement_only_symbols']} from supplement-only symbols. The shown "
        "clean-through-exit pool additionally rules out notices arriving before the exit.", "",
        row("UTC year", "Judged control pool", "Shown clean-through-exit pool"),
        row("---", "---:", "---:"),
    ])
    lines.extend(row(year, size, clean_pool[year]) for year, size in sorted(pool.items()))
    lines.extend([
        "",
        f"MEASURED. The calendar-only gate skipped {skips['total']} otherwise executable ordinary entries "
        "in the two predeclared archive-coverage ranges. No listing trade was skipped on this basis. "
        "The eligibility check never used the realized stop or return, but it changed the control mix.", "",
        row("Contract", "UTC entry month", "Skipped"), row("---", "---", "---:"),
    ])
    lines.extend(row(s["symbol"], s["entry_month_utc"], s["count"]) for s in skips["by_symbol_month"])
    lines.extend([
        "", "## Shown only", "",
        "MEASURED. These are alternate summaries, not extra passes. The hourly proxy rows enter off the "
        "notice time instead of using the judged red-day wait.", "",
        row("Variant", "Trades", "Mean net", "Median net", "Worst"),
        row("---", "---:", "---:", "---:", "---:"),
    ])
    lines.extend(row(label, x["count"], pct(x["mean"]), pct(x["median"]), pct(x["worst"])) for label, x in shown)
    cont = o["shown_missing_hold_bar_continuation"]["by_arm"]
    lines.extend([
        "",
        f"MEASURED. There were {cont['listing']['closes']} listing and {cont['ordinary']['closes']} ordinary "
        "missing-bar closes, so continuing after a missing bar did not change the comparison. "
        f"With the clean-through-exit controls, the shown 95th percentile was "
        f"{pct(o['shown_clean_ordinary']['placebo_cut'])}.", "",
        "## Freeze history and run record", "",
        "STATED. There were four freezes, not four scored runs. Earlier refusals stopped before the lock "
        "and produced no scored return. The third freeze's diagnostic was a no-return validation.", "",
        row("Freeze", "What happened"), row("---", "---"),
        row("`6d9aba2`", "First attempted start refused on an unverified ordinary-control contract end."),
        row("`3585a68`", "Nine official ends pinned; the next start refused on the missing February 2023 "
            "ANKRUSDT mark-price day needed for ordinary settlements."),
        row("`6169441`", "Official daily archives plugged ANKR's missing day. A no-return validation found "
            "16 distinct code/path pairs: four trade-bar edges, SRM's right funding anchor, ICP's early "
            "funding, five repairable mark months and five unavailable marks for 币安人生USDT."),
        row("`20701a0`", "Pinned four verified ends and more daily marks, clarified SRM's verified expiry "
            "boundary, and allowed only the two narrow calendar-based ordinary skips. No-return validation "
        "reported zero pairs at 03:54:46 UTC before the lead agent authorized the single score."),
        "",
        f"MEASURED. The saved result records ledger {job['ledger']} and a start at {began} from "
        f"`{job['commit']}`. Saved result SHA-256 `{RESULT_SHA}`. "
        "This page uses only that saved result for numerical performance.", "",
        "UNKNOWN. Independent recompute of the listing trades is pending. The lead agent will record it here.", "",
        "## Limits", "",
        "STATED. Binance.com perpetuals are not available to US accounts, and we do not go around that "
        "restriction ([CFTC Binance order announcement](https://www.cftc.gov/PressRoom/PressReleases/8825-23)). "
        f"The US-today filter contains only {o['us_today']['count']} trades and uses today's list, not the "
        "historical US list. Even those returns use Binance prices, not US fills or costs.", "",
        "STATED. Trades overlap in time, so the per-trade t can overstate how much independent evidence "
        "there is. The notice candle can include trades from before publication, and hour bars do not tell "
        "us which print came first. The ordinary pool covers only the pinned archives and omits the "
        "predeclared gaps; it is not a full census of comparable jumps.", "",
        f"MEASURED. The worst listing trade lost {abs(judged['worst']):.1%} of entry notional even without "
        f"leverage. Most trades and much of the result came from 2025–2026. It is the second pass in about "
        "26 tests, not a basis for live trading.", "",
    ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, help="Off-repo saved results_20.json")
    args = parser.parse_args()
    raw = args.result.read_bytes()
    if sha256(raw).hexdigest() != RESULT_SHA:
        parser.exit(1, "P20_REPORT_RESULT_PIN\n")
    print(render(json.loads(raw)), end="")


if __name__ == "__main__":
    main()
