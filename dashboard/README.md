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

`data.json` is made by `research_rig/export_dashboard.py` (run it from inside `research_rig/`). It reads the second rig (`rig2.py`) and its results, `results_v2.json` and `compare_v1_v2.json`, and re-simulates the curves and trade lists, stopping if they do not match those results. Stock and coin basket cards appear by themselves once `results_05.json` or `results_04.json` exist. The "Test results so far" panel uses the same row functions as `docs/STATUS.md` (`tools/status_table.py`), so the two cannot disagree. The "Waiting on you" list is read from `docs/decisions/morning_list_2026-11-25.md` each time the export runs; nothing in it is typed into the exporter. Stock cards read `results_05.json` (first run) and `results_05b.json` (corrected run). `data.json` is not stored in the repo; run the export script to create it in this folder. Every number and status line on the page is read from that file when the page loads, so a new export shows up on the next reload.

## Files

- `index.html`: page layout
- `styles.css`: look, light and dark themes
- `app.js`: reads `data.json` and fills the page
- `fonts/`: interface font (falls back to the system font if missing)
- `vendor/chart.umd.min.js`: Chart.js, unchanged copy of the published file
