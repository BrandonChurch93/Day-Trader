"""Render the Replay 23 result page (doc 72) from the pinned saved run outputs. Opens no bar and does not score.

  python3 tools/report_saved_23.py [--run DIR] [--calibration FILE] [--out FILE]

Reads results_23.json and events_frozen.csv from the off-repo run folder and calibration_23.json from the draft folder.
Refuses if any of the three differs from the sha256 pinned below. Every number on the page comes from those files.
The page names tickers and statuses only; it carries no price.
"""
import argparse
import csv
from hashlib import sha256
import json
import os
from pathlib import Path

RIG = Path(os.path.expanduser("~/workspace/rig"))
RESULT_SHA = "4834554deb1864e7b1a3d2f9794d4d3bb89d33e3ea8854a01cdd199e7e6dcae1"
EVENTS_SHA = "a4ef7fe749d973091fdfec13e0ba1b392a9cff94e548a03298a644008e180f76"
CALIB_SHA = "71f9be0632a8b999a92bccc2bc6e22b3bf1bcc62baff046b7d83b1b86bb89351"
FREEZE_SHA = "57e12dfe68f9222888e6a7a416d43c954a26b3c4b81d673977d31235bb7dc5c6"
APPROVAL = "a087351cbb483a95bb8beaa3ecda354f63a8e31b"
FREEZE_COMMIT = "4c8fe2c759f88e9c583662a1b4256c10fe43a5a1"
OUT = Path(__file__).resolve().parent.parent / "docs/research/72_replay_23_ipo_fast_track.md"

MARKS = [("n_trades", "At least `min_trades` trades"), ("mean_above_zero", "Mean net return above 0"),
         ("t_stat", "t of the mean at least `min_t_stat`"),
         ("mean_without_best", "Mean above 0 without the best `drop_best` trades"),
         ("median_above_zero", "Median above 0"),
         ("year_share", "Positive mean in at least `min_year_share_pct`% of years with `min_year_trades` or more trades"),
         ("excess_vs_spy", "Mean minus SPY above 0 with t at least `min_t_stat`"),
         ("recent_mean", "Mean above 0 on events priced from `recent_from`")]
SHOWN = [("second_day_open", "Buy at the second day's open instead"),
         ("at_shown_bps", "Cost `shown_bps` a side"),
         ("at_no_auction_bps", "Cost `no_auction_bps` a side (no closing-auction order)"),
         ("without_mega", "Without listings above `mega_usd`"),
         ("first_close_at_or_above_offer", "First close at or above the offer price"),
         ("first_close_below_offer", "First close below the offer price"),
         ("band_1_0_to_1_5", "Listings at 1.0 to 1.5 times the cut-off"),
         ("near_0_67_to_1_5", "Listings at 0.67 to 1.5 times the cut-off")]


def load(path, want):
    blob = Path(path).read_bytes()
    if sha256(blob).hexdigest() != want:
        raise SystemExit(f"P23_PAGE_PIN {path}")
    return blob


def pct(x):
    return "undefined" if x is None else f"{100 * x:+.2f}%"


def num(x):
    return "undefined" if x is None else f"{x:.2f}"


def row(*cells):
    return "| " + " | ".join(map(str, cells)) + " |"


def render(res, events, calib):
    j, f, s, p = res["judgment"], res["judgment"]["figures"], res["shown"], res["parameters"]
    held = sum(map(bool, j["marks"].values()))
    years = s["by_year"]
    early = [y for y in years if y < "2022"]
    late = [y for y in years if y >= "2022"]
    early_n = sum(years[y]["n"] for y in early)
    early_mean = sum(years[y]["n"] * years[y]["mean"] for y in early) / early_n
    late_n = sum(years[y]["n"] for y in late)
    late_mean = sum(years[y]["n"] * years[y]["mean"] for y in late) / late_n
    late_pos = sum(years[y]["mean"] > 0 for y in late)
    judged = [e for e in events if e["group"] == "judged"]
    pre = {k.split("|")[1]: v for k, v in res["pre_lock_status"].items() if k.startswith("judged|")}
    listed = sum(pre.values())
    out_before = sum(v for k, v in pre.items() if k in ("shares_unverified", "not_common_security"))
    active = listed - out_before
    dates = {k: sorted(e["ticker"] for e in judged if e["status"] == k) for k in ("prior_bars", "entry_not_real_bar")}
    recent_listed = sum(1 for e in judged if e["status"] not in ("shares_unverified", "not_common_security")
                        and e["pricing_date"] >= p["recent_from"])
    recent_prior = sum(1 for e in judged if e["status"] == "prior_bars" and e["pricing_date"] >= p["recent_from"])
    c = calib["edges_pct"]
    start = res["job"]["start_utc"].replace("T", " ").replace("Z", " UTC")

    L = ["# Replay 23. Early index buying after large US listings", "",
         f"MEASURED. Run once at {start}. Result: did not pass, {held} of {len(j['marks'])} marks at "
         f"{p['judged_bps']} bps a side. {f['n']} trades, mean net {pct(f['mean'])}, t {num(f['t'])}. "
         f"The failed mark is the recent one: {pct(f['recent_mean'])} on the {f['recent_n']} trades priced from {p['recent_from']}.", "",
         "STATED. The [frozen plan](../../research_rig/PREREG_23_ipo_fast_track.md) (ledger 160, queue 37) buys a large new US "
         "listing at its first day's close and sells at the fifth session's close. A listing is judged when the offer price times "
         "the prospectus's own after-offering share total is at least `judged_ratio_min` times the latest published CRSP 98% "
         "breakpoint. The idea is that index funds must buy such a listing within days. The published estimate came from a sample "
         "ending in 2022 ([Murray and Sammon, 2026](https://academic.oup.com/raps/article/16/2/163/8416725)).", "",
         "## In plain words", "",
         f"- It worked on paper from 2017 to 2021: {early_n} trades with a mean of {pct(early_mean)}, a positive mean in each of those {len(early)} years. MEASURED.",
         f"- It has not worked since 2022: {late_n} trades with a mean of {pct(late_mean)}; {late_pos} of {len(late)} years from 2022 had a positive mean, and those were small. MEASURED.",
         f"- The full-sample marks held only because of the busy early years; 2021 alone gave {years['2021']['n']} of the {f['n']} trades. MEASURED.",
         f"- The recent-years mark (mean above 0 from `recent_from`) was fixed before any price was read, because the published sample ends in 2022. It was put there to catch this case, an effect that has faded since it was written up, and it did. STATED in the plan, MEASURED here.",
         f"- The years from 2022 are thin ({late_n} trades over {len(late)} years), so they cannot show the effect is gone for good either. What they show is that it has not been there to collect.",
         "- Nothing here is a reason to trade this rule.", "",
         "## Eight judged marks", "",
         row("Mark", "Measured", "Held"), row("---", "---:", "---")]
    measured = {"n_trades": f["n"], "mean_above_zero": pct(f["mean"]), "t_stat": num(f["t"]),
                "mean_without_best": pct(f["mean_without_best"]), "median_above_zero": pct(f["median"]),
                "year_share": f"{len(f['years_positive'])} of {len(f['years_counted'])} ({f['year_share_pct']:.0f}%)",
                "excess_vs_spy": f"{pct(f['excess_mean'])}, t {num(f['excess_t'])}",
                "recent_mean": f"{pct(f['recent_mean'])} on {f['recent_n']}"}
    for k, text in MARKS:
        L.append(row(text, measured[k], "yes" if j["marks"][k] else "no"))
    L += ["", "## Calendar years", "",
          "MEASURED. Judged trades at the judged cost. Years are the first trading day's calendar year.", "",
          row("Year", "Trades", "Mean net", "Median net"), row("---", "---:", "---:", "---:")]
    for y, x in years.items():
        L.append(row(y, x["n"], pct(x["mean"]), pct(x["median"])))
    L += ["", "## Shown only, not judged", "",
          "MEASURED. None of these was used to pick the judged result.", "",
          row("Cell", "Trades", "Mean net", "Median net", "t"), row("---", "---:", "---:", "---:", "---:")]
    for k, text in SHOWN:
        x = s[k]
        L.append(row(text, x["n"], pct(x["mean"]), pct(x["median"]), num(x["t"])))
    L += ["", f"Every judged trade left at the fifth session close ({s['exit_how'].get('fifth_session', 0)} of {f['n']}).", "",
          f"## Why {f['n']} and not {active}", "",
          f"MEASURED. {listed} judged listings were on the list. {out_before} were left out before the run because their share "
          f"count or security type could not be confirmed ({pre.get('shares_unverified', 0)} shares unverified, "
          f"{pre.get('not_common_security', 0)} not common stock), which left the {active} the plan expected. "
          f"The date checks fixed in the plan then left out {active - f['n']} more, all before the lock:", "",
          f"- {len(dates['prior_bars'])} with bars more than `prior_bar_gap_bdays` sessions before the filing date (`prior_bars`): "
          f"{', '.join(dates['prior_bars'])}. The plan reads these as a reused symbol or another security, so the first day cannot be told apart from older trading. Which of the two applies to each name was not checked. {recent_prior} of them were priced from `recent_from`, which is why the recent mark has {f['recent_n']} trades and not {recent_listed}.",
          f"- {len(dates['entry_not_real_bar'])} whose first bar was not a real trade (`entry_not_real_bar`): {', '.join(dates['entry_not_real_bar'])}.", "",
          "No trade dropped after the lock.", "",
          "## Limits", "",
          f"- Calibration, STATED in the plan and MEASURED on invented paths: with no edge, {c['0']['all_eight']} of {calib['seeds']} "
          f"worlds passed all eight marks, a false pass; with a 2% edge a trade only {c['2']['all_eight']} of {calib['seeds']} passed, "
          f"and with 4% {c['4']['all_eight']} of {calib['seeds']}. So this test can miss a small real edge, and a pass would not have proved one.",
          f"- A t of {num(f['t'])} on the full sample uses the usual standard error. It does not adjust for the many ideas this project has tested or for trades that bunch in hot years.",
          f"- At `no_auction_bps` a side, the cost for a buyer who cannot use a closing-auction order, the full-sample mean falls to {pct(s['at_no_auction_bps']['mean'])} with t {num(s['at_no_auction_bps']['t'])}.",
          "- The size test is a stand-in for CRSP's own share counts and its US, PFIC and float screens. 424B1 listings and direct listings are missing.",
          "- The daily bar close is the last consolidated trade, not the closing auction print.",
          "- Raw bars: a split or dividend inside the five sessions is not adjusted. SPY is raw too.",
          "- The common-shares check reads the 424B4 cover text with fixed patterns; it is not a CUSIP match.", "",
          "## Run record", "",
          f"MEASURED. Freeze commit `{FREEZE_COMMIT}`, approval commit `{APPROVAL}`, one collection and one scored run. "
          "This page was generated by `tools/report_saved_23.py` from the saved outputs only. Bars, offer prices and breakpoints stay off repo.", "",
          f"- Freeze record SHA-256 `{res['job']['freeze_sha256']}`",
          f"- Saved result SHA-256 `{RESULT_SHA}`",
          f"- Frozen event list SHA-256 `{EVENTS_SHA}`",
          f"- Calibration SHA-256 `{CALIB_SHA}`"]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", type=Path, default=RIG / "data/replay_23")
    ap.add_argument("--calibration", type=Path, default=RIG / "plan23_draft/calibration_23.json")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    res = json.loads(load(a.run / "results_23.json", RESULT_SHA))
    if res["job"]["freeze_sha256"] != FREEZE_SHA:
        raise SystemExit("P23_PAGE_OTHER_FREEZE")
    events = list(csv.DictReader(load(a.run / "events_frozen.csv", EVENTS_SHA).decode().splitlines()))
    calib = json.loads(load(a.calibration, CALIB_SHA))
    a.out.write_text(render(res, events, calib))
    print(a.out)


if __name__ == "__main__":
    main()
