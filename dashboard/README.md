# Day Trader: trades and results screen

A small, read-only web page for looking at the project's accounts, test results, past-price test comparisons and trades. It only reads `data.json`. It cannot place, change or cancel any trade, and it holds no keys.

## Open it locally

```
cd dashboard
python3 -m http.server 8000
```

Then open http://127.0.0.1:8000 in a browser. Opening `index.html` straight from disk will not work, because browsers block reading `data.json` from a `file://` page.

The chart library (Chart.js 4.4.6, MIT licence) is kept in `vendor/`, so the page works without an internet connection.

## Where the data comes from

`data.json` is made by `research_rig/export_dashboard.py` (run it from inside `research_rig/`). The figures on the cards and in the tables come from the stored output files of the second rig, `results_v2.json` and `compare_v1_v2.json`, and from `results_02.json`, `results_04.json`, `results_05.json` (first run) and `results_05b.json` (corrected run). The stock card shows both runs. Research recommends that no pass from either is credited (question 18b in `docs/decisions/morning_list_2026-11-25.md`).

The five charts need curves and trade lists that the output files do not hold. They are read from `curves_cache.json` in this folder, which is not stored in the repo. With no flag the script reads that file and touches no price. If the file is missing it stops and says so. `python3 export_dashboard.py --resimulate` makes the file again by replaying the five charted rules on raw prices, held-back years included, and comparing four whole-sample figures with `results_v2.json`, for the rule and for holding (growth a year, Sharpe ratio, largest drop, total return), plus the trade count for the three daily charts. The curves, the year-by-year figures and the trade lists come out of that replay and are compared with nothing. No stored output holds them, so they are not a counted result, and they cannot be rebuilt from the repo alone. The verdict shown beside each chart is not taken from the saved file. It is worked out from the stored results each time the export runs. A replay is a held-back run. Do not do it without the owner's yes (questions 16a and 16b in `docs/decisions/morning_list_2026-11-25.md`, and `research_rig/README.md`, "How each stored output was made"). Until 2026-11-25 the script did this every time it ran; that is disclosed in `research_rig/TRIAL_LEDGER.md`.

The "Test results so far" panel uses the same row functions as `docs/STATUS.md` (`tools/status_table.py`), so the two cannot disagree. The "Waiting on you" list is read from `docs/decisions/morning_list_2026-11-25.md` each time the export runs; nothing in it is typed into the exporter. How an owner decision is recorded is in `docs/decisions/README.md`. `data.json` is not stored in the repo either. Every number and status line on the page is read from it when the page loads, so a new export shows up on the next reload.

## Files

- `index.html`: page layout
- `styles.css`: look, light and dark themes
- `app.js`: reads `data.json` and fills the page
- `data.json`, `curves_cache.json`: made by the export script. Git ignores both, so a fresh copy of the repo has neither
- `fonts/`: interface font. Git ignores this folder, so a fresh copy of the repo does not have it and the page falls back to the system font
- `vendor/chart.umd.min.js`: Chart.js, unchanged copy of the published file
