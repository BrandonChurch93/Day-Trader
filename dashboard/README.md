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

`data.json` is made by `research_rig/export_dashboard.py` (run it from inside `research_rig/`). The figures on the cards and in the tables come from the stored output files of the second rig, `results_v2.json` and `compare_v1_v2.json`, and from `results_02.json`, `results_04.json`, `results_05.json` (first run) and `results_05b.json` (corrected run). The stock card shows both runs. Research recommends that no pass from either is credited (question 18b in `archive/decisions/morning_list_2026-11-25.md`).

The five charts need curves and trade lists that the output files do not hold. They are read from `curves_cache.json` in this folder, which is not stored in the repo. With no flag the script reads that file and touches no price. If the file is missing it stops and says so. `python3 export_dashboard.py --resimulate` makes the file again by replaying the five charted rules on raw prices, held-back years included, and comparing four whole-sample figures with `results_v2.json`, for the rule and for holding (growth a year, Sharpe ratio, largest drop, total return), plus the trade count for the three daily charts. The curves, the year-by-year figures and the trade lists come out of that replay and are compared with nothing. No stored output holds them, so they are not a counted result, and they cannot be rebuilt from the repo alone. The verdict shown beside each chart is not taken from the saved file. It is worked out from the stored results each time the export runs. A replay is a held-back run. See `AGENTS.md`, "Honest testing", and `research_rig/README.md`, "How each stored output was made", before considering a run on held-back dates. Until 2026-11-25 the script did this every time it ran; that is disclosed in `research_rig/TRIAL_LEDGER.md`.

The "Test results so far" panel uses the same row functions as `docs/STATUS.md` (`tools/status_table.py`), so the two cannot disagree. The "Only you can do" panel reads the listed actions under "Waiting on the owner" in `docs/STATUS.md` each time the export runs. `data.json` is not stored in the repo. Reload the dashboard after exporting to see the updated snapshot.

## Practice account section

The "Practice account" section at the top of the page is a scoreboard for the practice desk. The desk runs several traders in one Alpaca practice account. Some are fixed rules and some are AI traders. Each has its own pretend budget and its own books. A plain program checks and places every order. The section reads two fields of `data.json`. `practice` is a copy of the desk's `summary.json` (`Run.summary` in `practice/trader.py`) from the `practice-records` branch, and `practice_live_url` is the address of the newest `summary.json` on that branch. Both are written by `research_rig/export_dashboard.py`.

From the top, the section shows:

- One line of state (waiting for the key, running, or stopped), with the last check in local time. The UTC time is in the tooltip.
- The whole account: pretend value, gain since the start, wins, losses, win rate and closed trades.
- The traders, best gain first: kind (rule or AI, with the model), gain, the gain from just holding its benchmark, wins and losses, holdings, and a stopped note with the reason. Opening a trader shows its holdings with the exit in force, its last pick with the thesis and sources, its orders with the reason for each, and its closed trades.
- Gain over time in percent: the whole account, just holding, and a thin line per trader. One trader can be picked out.
- All trades, newest first, with the reason, and closed trades marked win, loss or even. The records file keeps the newest 300 of each.
- Symbols stopped, when there are any, and the problems list.

The page shows the copy in `data.json` first. Then it asks `practice_live_url` for a newer copy. If that copy is newer, the section is redrawn from it. If the request fails, the page keeps the copy it has and says "Could not check for newer records". When `practice` is empty, or the desk is still waiting for its key, the section says so and shows no totals. The section only reads. It cannot place, change or cancel an order.

## Time machine section

The "Time machine" section comes right after the Practice account section. It shows the scored replay plans from `timemachine` in `data.json`, which `research_rig/export_dashboard.py` builds from the stored results files. It reads no prices and runs nothing.

- TM01 and TM02: from `timemachine/results_tm01.json` and `timemachine/results_tm02.json`.
- TM03, the bitcoin dial: from `timemachine/results_tm03.json` (`timemachine/score_tm03.py`). One row per model: months in, gain over the months added up, holding bitcoin over the same months, the percentile against the model's own answers in random order, and the plan's verdict words as the script writes them. A model whose months are not all in shows "Not finished" and no figures. When `timemachine/dial_rules_tm03.json` exists, one line shows the best plain trend rule's sum next to the best model's sum.
- TM04, the stock basket: from `timemachine/results_tm04.json` (`timemachine/score_tm04.py`). One row per model and run: gain, equal shares of the list, the percentile among random baskets, and the verdict. A run that is not finished shows its verdict ("running" or "not started") and no figures. Until the file exists the plan says "Being scored".


## Files

- `index.html`: page layout
- `styles.css`: look, light and dark themes
- `app.js`: reads `data.json` and fills the page
- `data.json`, `curves_cache.json`: made by the export script. Git ignores both, so a fresh copy of the repo has neither
- `fonts/`: interface font. Git ignores this folder, so a fresh copy of the repo does not have it and the page falls back to the system font
- `vendor/chart.umd.min.js`: Chart.js, unchanged copy of the published file
