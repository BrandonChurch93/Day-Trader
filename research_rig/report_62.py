"""Build Replay 62's report from the pinned saved aggregate; never score or read market inputs."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from math import ceil, isclose
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULT = Path("/home/user/workspace/rig/data/replay_62/result.json")
TARGET = ROOT / "docs/research/130_replay_62_special_dividend_ex_day.md"
HISTORY = ROOT / "research_rig/COUNT_62.json"
RESULT_SHA = "14ab97954d2b8b02e4b5fdbe35fd803b9978328ec0bc5e10ad509d17f03aa99b"
# Frozen terms and the separately recorded Plan 61 no-return count.
CAPITAL, FEE_BP, CENT, STRESS_BP, TAX, LIQUIDITY = 500, 5, .01, 10, 24, 1_000_000
FLOOR, CAP_BP, T_FLOOR, TRIM, YEARS, PRIOR_PLACED = 250, 600, 2, 1, 7, 230
YIELD_LOW, YIELD_HIGH = 1, 3


def read_result(path):
    raw = path.read_bytes()
    if sha256(raw).hexdigest() != RESULT_SHA:
        raise ValueError("Replay 62 saved result does not match its SHA-256")
    return json.loads(raw)


def pct(value, unit="pp"):
    if value is None:
        return "not available"
    return f"{value * 100:+.4f}" + (" pp" if unit == "pp" else "%")


def stat(value):
    return "not available" if value is None else f"{value:.2f}"


def table(head, rows):
    return "\n".join("| " + " | ".join(map(str, row)) + " |"
                     for row in (head, ("---",) * len(head), *rows))


def render(data, history):
    job, o = data["job"], data["outcome"]
    j, counts, shown = (o[k] for k in ("judged", "gate_counts", "shown_only"))
    paired, clipped, years, flags = (j[k] for k in ("paired", "winsorized_paired", "by_ex_year", "marks"))
    n = paired["n"]
    n_years = sum(value is not None and value > 0 for value in years.values())
    pos = lambda v: v is not None and v > 0
    marks = {
        "pairs": ("Placed pairs", f"At least {FLOOR} pairs", n, n >= FLOOR),
        "paired_mean": ("Raw paired mean", "Above zero", pct(paired["mean"]), pos(paired["mean"])),
        "winsorized_ex_date_clustered_t": (
            "Clipped evidence", f"Clip at ±{CAP_BP} bp; positive mean and ex-date clustered t at least {T_FLOOR}",
            f"{pct(clipped['mean'])}; t {stat(clipped['t'])}",
            pos(clipped["mean"]) and clipped["t"] is not None and clipped["t"] >= T_FLOOR),
        "positive_after_trim": ("Trimmed paired mean", f"Above zero after dropping the best {TRIM}%, rounding up",
                                f"{pct(j['trimmed_mean'])}; dropped {j['trim_removed']}", pos(j["trimmed_mean"])),
        "positive_ex_years": ("Positive ex-date years", f"At least {YEARS}", f"{n_years} of {len(years)}", n_years >= YEARS),
    }
    split = counts["placed_by_vendor_ex_status"]
    a, exact = (shown[k]["n"] for k in ("vendor_class_a", "vendor_exact_match"))
    h = history["classes"]
    if ((job["plan"], job["queue"], job["ledger"]) != (o["plan"], o["queue"], o["ledger"])
            or o["plan"] != 62 or job["count_approval_commit"] != "183bf1d65fc7148d4da298672cb779d90f1905d1"
            or set(flags) != set(marks) or any(flags[k] != row[-1] for k, row in marks.items())
            or j["passed"] is not all(flags.values()) or j["disposition"] != "close_row" or j["passed"]
            or counts["placed_pairs"] != n or clipped["n"] != n or paired["groups"] != clipped["groups"]
            or j["trim_removed"] != ceil(n * TRIM / 100) or n != a + exact
            or split != {"vendor_class_a": a, "vendor_exact_match": exact}
            or sum(h.values()) != history["vendor_ex_missing_only"] or h["A"] != a or exact != PRIOR_PLACED
            or not isclose(shown["stock_only"]["mean"] - shown["matched_iwm"]["mean"], paired["mean"])):
        raise ValueError("Replay 62 saved aggregates, history or frozen marks do not reconcile")
    shown_labels = {
        "earlier_entry": "Earlier entry (ex minus 2 close through ex-date close)",
        "stock_only": "Stock only",
        "matched_iwm": "Matched IWM leg",
        "stress_cost": f"Higher cost ({STRESS_BP} bp per side, same cent floor)",
        "cash_special_haircut_24_percent": f"{TAX}% haircut to verified special cash",
        "liquidity_at_least_1m": f"At least ${LIQUIDITY:,} median dollar volume",
        "yield_bucket_0": f"Yield below {YIELD_LOW}%",
        "yield_bucket_1": f"Yield from {YIELD_LOW}% to below {YIELD_HIGH}%",
        "yield_bucket_2": f"Yield at least {YIELD_HIGH}%",
        "vendor_exact_match": "Vendor exact match",
        "vendor_class_a": "Vendor Class A",
    }
    when = datetime.fromisoformat(job["started_utc"]).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return "\n\n".join([
        f"# Replay {o['plan']}. Special-dividend ex-day",
        "## The rule",
        "\n".join([
            "- STATED. Buy whole shares at the close before the verified ex-date and sell at the ex-date close. Match both closes with IWM.",
            f"- STATED. Start each leg with ${CAPITAL}; charge the greater of {FEE_BP} bp or ${CENT:.2f} per share per side. Credit only verified cash.",
        ]),
        "## Did it pass?",
        f"MEASURED. Did not pass, **{sum(flags.values())} of {len(flags)} frozen marks**, in the one scored run at {when}. "
        f"Only the placement mark was met: {n} matched pairs from {counts['events']} filing events. The frozen decision is to close the row.",
        "## Frozen marks",
        f"MEASURED. Each mark was required. The paired values are stock minus IWM in percentage points (pp); the t statistic groups "
        f"differences by ex-date across {paired['groups']} dates.",
        table(("Mark", "Frozen bar", "Measured", "Verdict"),
              [(label, bar, value, "met" if flags[k] else "not met") for k, (label, bar, value, _) in marks.items()]),
        "## What happened by year",
        f"MEASURED. The mean paired result was positive in {n_years} of {len(years)} ex-date years. "
        "These are raw paired means, after costs and before tax.",
        "\n".join(f"- {year}: {pct(value)}." for year, value in sorted(years.items())),
        "## Shown only",
        "MEASURED. These comparisons cannot count toward a mark. Rows show net stock minus IWM except for the named single-leg returns.",
        "\n".join(
            f"- {label}: {pct(shown[k]['mean'], '%') if k in ('stock_only', 'matched_iwm') else pct(shown[k]['paired_mean'])} "
            f"on {shown[k]['n']} pairs." for k, label in shown_labels.items()
        ) + f"\n- Plain paired t, grouped by ex-date without clipping: {stat(shown['plain_clustered_t'])}.",
        "## How the rule changed",
        "\n".join([
            f"- STATED. [Plan {o['plan'] - 1}](../../research_rig/PREREG_61_special_dividend_ex_day.md) was frozen first. "
            f"MEASURED. Its no-return validation found {PRIOR_PLACED} placed pairs, below the {FLOOR} mark. It was not scored.",
            "- STATED. The first proposal to accept all missing vendor matches was withdrawn before drafting. A wrong ex-date could put a trade on an ordinary day and still credit the dividend, overstating the return.",
            f"- STATED. Before counting, the lead fixed a narrower rule: accept an otherwise eligible missing exact match only when one supported "
            f"vendor cash record on the verified ex-date was at least the docket special less ${CENT:.2f}. The recorded vendor amount never replaced the verified cash.",
            f"- MEASURED. The [price-blind count](../../research_rig/COUNT_62.json) found that {h['A']} of {history['vendor_ex_missing_only']} "
            f"missing-only events met this Class A rule.",
            f"- STATED. [Plan {o['plan']}](../../research_rig/PREREG_62_special_dividend_ex_day_v2.md) froze the change with all marks unchanged, before any target return.",
        ]),
        "## Gaps",
        "\n".join([
            "- STATED. Printed closes were used. Actual closing-auction fills, broker cutoffs and how much could have been filled are UNKNOWN.",
            "- UNKNOWN. The replay does not establish whether the ex-date was known at entry or when the exchange first posted or changed it.",
            "- STATED. The judged results are before tax. The haircut is a sensitivity, not an account's tax result.",
            "- STATED. The filing docket is the same as [Replay 60](126_replay_60_special_dividends.md), whose aggregate results were already known. This is a different holding window, not an independent set of filings.",
        ]),
        "## What it means",
        f"MEASURED. The published ex-day effect discussed in the [idea note](../127_idea_round_33.md) did not show on these {n} events "
        f"after costs. The raw paired mean was {pct(paired['mean'])}; the row closes. This does not establish what would happen on other events.",
        "## Run record",
        "\n".join([
            f"- MEASURED. Freeze: `{job['freeze_commit']}`.",
            f"- MEASURED. Scoring approval: `{job['go_commit']}`.",
            f"- MEASURED. Saved aggregate result SHA-256: `{RESULT_SHA}`.",
        ]),
    ]) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, default=RESULT)
    parser.add_argument("--output", type=Path, default=TARGET)
    args = parser.parse_args()
    args.output.write_text(render(read_result(args.result), json.loads(HISTORY.read_bytes())), encoding="utf-8")


if __name__ == "__main__":
    main()
