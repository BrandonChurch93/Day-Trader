"""Plan 23 result page, from the stored results only. Opens no bar.

  python3 report_23.py --freeze-sha256 <sha>   writes RUN/page_23.md from RUN/results_23.json

Refuses if the freeze record's code pins differ from the files here, or if the results were made under another freeze.
Every number on the page comes from results_23.json.
"""
import argparse, json, os

import common_23 as C
import fetch_23 as F

MARKS = [("n_trades", "at least min_trades trades"), ("mean_above_zero", "mean net return above 0"),
         ("t_stat", "t of the mean at least min_t_stat"), ("mean_without_best", "mean above 0 without the best drop_best"),
         ("median_above_zero", "median above 0"), ("year_share", "positive mean in at least min_year_share_pct of years with min_year_trades or more"),
         ("excess_vs_spy", "mean return minus SPY above 0, t at least min_t_stat"),
         ("recent_mean", "mean above 0 on events priced from recent_from")]


def pct(x):
    return "undefined" if x is None or x != x else f"{100 * x:.2f}%"


def num(x):
    return "undefined" if x is None or x != x else f"{x:.2f}"


def page(res, p):
    j, f = res["judgment"], res["judgment"]["figures"]
    L = ["# Replay 23: early index buying after large US listings", "",
         f"MEASURED. One run, {res['job']['start_utc']} to {res['finished_utc']}. Freeze {res['job']['freeze_sha256']}.",
         f"Judged cost {p['judged_bps']} bps a side. Result: {'passed' if j['passed'] else 'did not pass'}, "
         f"{sum(map(bool, j['marks'].values()))} of {len(j['marks'])} marks.", "", "## Marks", "",
         "| Mark | Asks | Held |", "|---|---|---|"]
    for k, text in MARKS:
        L.append(f"| {k} | {text} | {'yes' if j['marks'][k] else 'no'} |")
    L += ["", "## Figures", "", "| Figure | Value |", "|---|---|",
          f"| trades | {f['n']} |", f"| mean net | {pct(f['mean'])} |", f"| t | {num(f['t'])} |",
          f"| mean without the best | {pct(f['mean_without_best'])} |", f"| median | {pct(f['median'])} |",
          f"| years counted / positive | {len(f['years_counted'])} / {len(f['years_positive'])} |",
          f"| mean minus SPY | {pct(f['excess_mean'])} (t {num(f['excess_t'])}) |",
          f"| from {p['recent_from']}: trades, mean | {f['recent_n']}, {pct(f['recent_mean'])} |",
          "", "## Shown only, not judged", "", "| Cell | Trades | Mean | Median | t |", "|---|---|---|---|---|"]
    s = res["shown"]
    for k in ("second_day_open", "band_1_0_to_1_5", "near_0_67_to_1_5", "at_shown_bps", "at_no_auction_bps", "without_mega",
              "first_close_below_offer", "first_close_at_or_above_offer"):
        x = s[k]
        L.append(f"| {k} | {x['n']} | {pct(x['mean'])} | {pct(x['median'])} | {num(x['t'])} |")
    L += ["", "| Year | Trades | Mean | Median |", "|---|---|---|---|"]
    for y, x in s["by_year"].items():
        L.append(f"| {y} | {x['n']} | {pct(x['mean'])} | {pct(x['median'])} |")
    L += ["", "## Counts", ""] + [f"- {k}: {v}" for k, v in res["pre_lock_status"].items()]
    L += [f"- exit {k}: {v}" for k, v in s["exit_how"].items()]
    L += ["", "## Limits", "",
          "- The size test is a stand-in for CRSP's own share counts and its US, PFIC and float screens.",
          "- 424B1 listings and direct listings are missing. ADS rows without a value are missing.",
          "- The daily bar close is the last consolidated trade, not the closing auction print. The at_no_auction_bps line "
          f"({p['no_auction_bps']} bps a side) is for a buyer who cannot use a closing-auction order.",
          "- Raw bars: a split or dividend inside the five sessions is not adjusted. SPY is raw too.",
          "- The common-shares check reads the 424B4 cover text with fixed patterns; it is not a CUSIP match."]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--freeze-sha256", required=True)
    a = ap.parse_args()
    P = F.paths()
    raw = open(P["freeze"], "rb").read()
    if C.sha256_bytes(raw) != a.freeze_sha256:
        raise SystemExit("P23_FREEZE_SHA")
    for f, h in json.loads(raw)["code_sha256"].items():
        if C.sha256_file(os.path.join(C.HERE, f)) != h:
            raise SystemExit("P23_CODE_CHANGED " + f)
    res = json.load(open(os.path.join(P["run"], "results_23.json")))
    if res["job"]["freeze_sha256"] != a.freeze_sha256:
        raise SystemExit("P23_RESULT_OTHER_FREEZE")
    with open(os.path.join(P["run"], "page_23.md"), "w") as fh:
        fh.write(page(res, res["parameters"]))
    print(os.path.join(P["run"], "page_23.md"))


if __name__ == "__main__":
    main()
