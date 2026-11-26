"""Render Replay 46 from one saved result and its frozen settings. Never score or open prices."""
import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess


RESULT_SHA = "b941fb1a7d3f55d14fff063f8b4918e0ede4ce73d4470b9f0ceec586d9b96edb"
ROOT = Path(__file__).resolve().parents[1]
PAGE = "docs/research/101_replay_46_cftc_altcoin_futures.md"
TRX_GAP_DATES = 24
TRX_CAPTURES = (
    ("2026-05-21", "20260521161041", ""),
    ("2026-08-27", "20260827123223", ""),
    ("2026-09-14", "20260914031920", "/"),
)


def pct(stat):
    return f"{stat['mean']:+.4%}" if stat["mean"] is not None else "undefined"


def t(stat):
    return f"{stat['t']:.3f}" if stat["t"] is not None else "undefined"


def row(*cells):
    return "| " + " | ".join(map(str, cells)) + " |"


def outcome(leg):
    return f"{'passed' if leg['passed'] else 'did not pass'}, {sum(leg['marks'].values())} of {len(leg['marks'])} marks"


def brief(leg):
    return (f"{outcome(leg)}. {leg['net']['n']} events on {leg['net']['posting_dates']} posting dates, "
            f"{pct(leg['net'])} mean net, {pct(leg['paired'])} paired versus BTC "
            f"(t {t(leg['paired'])}), {pct(leg['trimmed'])} paired without the best posting dates.")


def read_saved(path):
    blob = path.read_bytes()
    if sha256(blob).hexdigest() != RESULT_SHA:
        raise ValueError("saved result hash mismatch")
    data = json.loads(blob)
    job = data["job"]
    freeze = job["freeze_commit"]
    if job["schema"] != 1 or not re.fullmatch(r"[0-9a-f]{40}", freeze) or set(data["legs"]) != {"A", "B"}:
        raise ValueError("saved result identity mismatch")
    config = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{freeze}:config/thresholds.yaml"], text=True)
    cfg = json.loads(config.split("replay_46_plan:\n  value: ", 1)[1].splitlines()[0])
    if (job["queue"], job["ledger"]) != (cfg["queue"], cfg["ledger"]):
        raise ValueError("saved result does not match frozen settings")
    claimed = datetime.fromisoformat(job["claimed_utc"]).astimezone(timezone.utc)
    return job, data["legs"], cfg, claimed.strftime("%Y-%m-%d %H:%M:%S UTC")


def marks(legs, cfg):
    out = {}
    for name, leg in legs.items():
        n, p, cut = (leg[k] for k in ("net", "paired", "trimmed"))
        trimmed_dates = len(leg["removed_posting_dates"])
        observed = {
            "minimum_events": (n["n"], n["n"] >= cfg["min_events"]),
            "minimum_posting_dates": (n["posting_dates"], n["posting_dates"] >= cfg["min_dates"][name]),
            "positive_raw_net": (pct(n), n["mean"] is not None and n["mean"] > 0),
            "positive_paired_net": (pct(p), p["mean"] is not None and p["mean"] > 0),
            "minimum_paired_t": (t(p), p["t"] is not None and p["t"] >= cfg["min_t"]),
            "positive_paired_without_best_dates": (pct(cut), cut["mean"] is not None and cut["mean"] > 0),
        }
        if (leg["ledger"] != cfg["ledger"][name] or len(leg["rows"]) != n["n"] or n["n"] != p["n"]
            or n["posting_dates"] != p["posting_dates"] or trimmed_dates != cfg["trim_dates"]
            or cut["posting_dates"] != p["posting_dates"] - trimmed_dates
            or leg["marks"] != {k: passed for k, (_, passed) in observed.items()}
            or leg["passed"] != all(leg["marks"].values())):
            raise ValueError("saved marks do not reconcile with saved aggregates")
        out[name] = observed
    return out


def render(job, legs, cfg, claim):
    observed = marks(legs, cfg)
    a, b = legs["A"], legs["B"]
    dates = cfg["min_dates"]
    cut = cfg["trim_dates"]
    start = cfg["entry_lag_days"]
    hold = cfg["b_hold_days"]
    min_hold = cfg["a_min_hold_days"]
    stats_headers = (
        row("Leg or view", "Events", "Posting dates", "Mean net", "Net t", "Mean paired vs BTC", "Paired t"),
        row("---", "---:", "---:", "---:", "---:", "---:", "---:"),
    )

    def stats(label, n, p):
        return row(label, p["n"], p["posting_dates"], pct(n) if n else "not judged",
                   t(n) if n else "not judged", pct(p), t(p))

    lines = [
        "# Replay 46. CFTC-certified altcoin futures", "",
        "MEASURED. Neither leg passed. The pre-launch spot long lost money at the frozen cost. "
        "The post-launch short proxy was positive, but its advantage over matched BTC was too small "
        "relative to the variation across posting dates to clear the frozen t mark.", "",
        f"- A, before launch: {brief(a)}",
        f"- B, after launch: {brief(b)}", "",
        "## What was tested", "",
        f"STATED. The [frozen plan](../../research_rig/PREREG_46_cftc_altcoin_futures.md) used the CFTC archive "
        f"date plus {start} calendar days at midnight UTC as the posting proxy, not an observed release time. "
        f"A bought the spot open on that day and sold at the last UTC daily close before the stated launch date; "
        f"it needed at least {min_hold} elapsed days to the launch boundary. B used the later of the first midnight "
        f"after the stated launch date or the archive-date proxy, then held for {hold} days. "
        "Both benchmark positions used BTC-USD in the same direction on the same price fields and dates.", "",
        "## Frozen marks", "",
        "MEASURED. Paired means the altcoin net return minus the matched BTC net return. "
        "Events have equal weight; the t-statistic groups events by CFTC archive date. "
        "All marks were required for each leg.", "",
        row("Required mark", "A result", "B result"), row("---", "---:", "---:"),
    ]
    labels = (
        ("minimum_events", f"At least {cfg['min_events']} placed events"),
        ("minimum_posting_dates", f"At least {dates['A']} posting dates for A and {dates['B']} for B"),
        ("positive_raw_net", "Mean net above zero before subtracting BTC"),
        ("positive_paired_net", "Mean paired net above zero"),
        ("minimum_paired_t", f"Paired date-clustered t at least {cfg['min_t']:.1f}"),
        ("positive_paired_without_best_dates", f"Mean paired net above zero without best {cut} posting dates"),
    )
    for key, label in labels:
        values = [observed[k][key] for k in ("A", "B")]
        lines.append(row(label, *(f"{value} ({'met' if met else 'not met'})" for value, met in values)))
    lines.extend(["", "## Net returns and counts", "", "MEASURED. These are per-event means, not compounded "
                  "portfolio returns. The trim removes every event on the best posting dates by mean paired return.",
                  "", *stats_headers])
    for name, leg in legs.items():
        lines.append(stats(f"{name}, full judged sample", leg["net"], leg["paired"]))
        lines.append(stats(f"{name}, paired without best {cut} posting dates", None, leg["trimmed"]))

    lines.extend(["", "## Skips", "", "MEASURED. Calendar exclusions are counted before price checks. "
                  "The planned count is the placed count plus the input-gap exclusions.", "",
                  row("Leg", "Planned", "Placed", "Calendar exclusions by reason", "Input gaps by reason"),
                  row("---", "---:", "---:", "---", "---")])
    wording = {
        "short_notice": "too little notice", "unknown_trade_date": "unknown trade date",
        "right_censored": "window extended past the cutoff", "same_coin_overlap": "overlapping same-coin window",
        "coin_gap": "altcoin spot candle gap",
    }
    for name, leg in legs.items():
        calendar, gaps = leg["calendar_skips"], leg["data_skips"]
        reasons = lambda counter: "; ".join(f"{wording[code]} ({n})" for code, n in counter.items()) or "none"
        placed = leg["net"]["n"]
        if placed + sum(calendar.values()) + sum(gaps.values()) != cfg["rows"]:
            raise ValueError("exclusions do not reconcile with frozen docket count")
        lines.append(row(name, placed + sum(gaps.values()), placed, reasons(calendar), reasons(gaps)))

    lines.extend(["", "## Shown only", "", "MEASURED. These lines do not alter the verdicts. Earliest in the "
                  "docket means the earliest roster record for a coin, not the first listing ever.", "", *stats_headers])
    fee = a["shown_only_fee_sensitivity"]["fee_bps_per_side"]
    if fee != cfg["a_sensitivity_fee_bps"]:
        raise ValueError("fee sensitivity does not match the freeze")
    for label, leg, key in (
        ("A, earliest in this docket (shown only)", a, "shown_only_first_in_docket"),
        (f"A, {fee} bp fee per side (shown only)", a, "shown_only_fee_sensitivity"),
        ("B, earliest in this docket (shown only)", b, "shown_only_first_in_docket"),
        ("B, without negative-notice events (shown only)", b, "shown_only_without_negative_notice"),
    ):
        view = leg[key]
        lines.append(stats(label, view["net"], view["paired"]))

    captures = ", ".join(f"[{day}](https://web.archive.org/web/{stamp}/https://api.exchange.coinbase.com/products{tail})"
                         for day, stamp, tail in TRX_CAPTURES)
    lines.extend([
        "", "## Costs and what the replay cannot show", "",
        f"- STATED. A charged {cfg['a_fee_bps']} bp taker fee and {cfg['a_half_spread_bps']} bp adverse half-spread "
        f"per side on altcoins, and the same fee plus {cfg['spot_btc_half_spread_bps']} bp half-spread for BTC. "
        "The fee is the frozen [Coinbase Exchange schedule](https://help.coinbase.com/en/exchange/trading-and-funding/exchange-fees) "
        "assumption, not an observed fee paid on an order.",
        f"- STATED. B charged {cfg['b_fee_bps']} bp fee and {cfg['b_half_spread_bps']} bp adverse half-spread per "
        f"side on altcoins, plus {cfg['b_funding_bps_per_day']} bp a day in adverse funding "
        f"({hold * cfg['b_funding_bps_per_day']} bp total). BTC faced the same fee and funding with "
        f"{cfg['perp_btc_half_spread_bps']} bp half-spread. The funding assumption cancels in the paired mean, "
        "not in the outright net mean. None of these B costs is a measured venue fill.",
        "- STATED. The prices are Coinbase Exchange USD spot daily bars. The first or last trade of a UTC bucket "
        "is a price reference, not an order fill. B is a spot-reference short proxy, not a short we could execute.",
        "- UNKNOWN. Actual fill prices at the chosen clocks, realized funding, futures basis, venue fees, account "
        "access, and executable depth are not established. The replay does not price the listed futures contracts.",
        f"- MEASURED. TRX-USD was absent from the Coinbase Exchange product-list captures on {captures}. "
        f"STATED. Under the lead agent's ruling, the capture evidence was used to infer absence on {TRX_GAP_DATES} "
        "requested dates. Those grid dates were not directly captured. A listing that opened and was removed "
        "entirely between captures is UNKNOWN. The date-level gap count is not the count of skipped trades.",
        "", "## Record", "",
        f"- MEASURED. The lead agent claimed the one allowed run at {claim}, queue {job['queue']}, "
        f"ledger {job['ledger']['A']} and {job['ledger']['B']}. Approval commit `{job['approval_commit']}`; "
        f"freeze commit `{job['freeze_commit']}`.",
        f"- MEASURED. Saved result SHA-256 `{RESULT_SHA}`; approved input SHA-256 `{job['input_sha256']}`. "
        "Only aggregates are reproduced here; the saved trade rows and input packet stay off repo.",
        "- MEASURED. An independent recompute, written by a second agent from the frozen plan text, docket and settings without reading the scorer, matched every count, every skip, all 12 marks and all 153 events; the largest per-event difference was under 1e-15. Its comparison file stays off repo (SHA-256 `2e358264f1bc857615e5eae595d3fbae9dc148966bfba3cc3396ca0448b49556`).",
        "- STATED. Neither rule advances; this result is not a trade recommendation.",
    ])
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("saved_result", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--write", action="store_true", help="write the generated report")
    modes.add_argument("--notes", action="store_true", help="print aggregate closeout wording for other pages")
    args = parser.parse_args()
    job, legs, cfg, claim = read_saved(args.saved_result)
    report = render(job, legs, cfg, claim)
    if args.write:
        (ROOT / PAGE).write_text(report, encoding="utf-8")
    elif args.notes:
        for name, leg in legs.items():
            print(f"[Replay 46 Leg {name}](research/{Path(PAGE).name}), run once {claim}. MEASURED. "
                  + brief(leg).capitalize().replace("btc", "BTC") + " Rule not advanced.")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
