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

- One line of state (waiting for the key, running, or stopped), with the last check in Mountain Time (the owner asked for Mountain Time on 2026-11-26). The UTC time is in the tooltip. Every stamp on the screen is shown in Mountain Time; the stored data stays UTC.
- The whole account: pretend value, gain since the start, wins, losses, win rate and closed trades.
- The traders, best gain first: kind (rule or AI, with the model), gain, the gain from just holding its benchmark, wins and losses, holdings, and a stopped note with the reason. Opening a trader shows its holdings with the exit in force, its last pick with the thesis and sources, its orders with the reason for each, and its closed trades.
- Gain over time in percent: the whole account, just holding, and a thin line per trader. One trader can be picked out.
- All trades, newest first, with the reason, and closed trades marked win, loss or even. The records file keeps the newest 300 of each.
- Symbols stopped, when there are any, and the problems list.

When the practice desk's row in the queue page's Running now table starts with "PAUSED <time> by the lead agent", the export writes `practice_pause` and the section says Paused with that time and the time of the last record, the traders show Paused rather than Trading, and the value is labelled as of the last record. The page shows the copy in `data.json` first. Then it asks `practice_live_url` for a newer copy. If that copy is newer, the section is redrawn from it. If the request fails, the page keeps the copy it has and says "Could not check for newer records". When `practice` is empty, or the desk is still waiting for its key, the section says so and shows no totals. The section only reads. It cannot place, change or cancel an order.

## What we believe now section

The "What we believe now" section sits right above "Where things stand". It shows `believed` from `data.json`, which `research_rig/export_dashboard.py` reads from the bullets under "## What is believed now" in `docs/STATUS.md` each time it runs. Nothing in it is typed into the exporter. Each bullet gives a short lead (up to the first colon or the first sentence end), the rest of the text without backticks or "(`path`)", and a link for each `docs/...` page it names that exists. Bullets with a time stamp "2026-11-25 HH:MM UTC" come first, newest first, then the rest in file order. The first 6 are shown, and "Show all" opens the rest.

## Time machine section

The "Time machine" section comes right after the Practice account section. It shows the scored replay plans from `timemachine` in `data.json`, which `research_rig/export_dashboard.py` builds from the stored results files. It reads no prices and runs nothing. When `docs/STATUS.md` has a "HOLD by the lead agent" bullet for a time machine study, `tm_hold` in `data.json` puts a plain on-hold note at the top of the section, with no weekly figure.

- TM01 and TM02: from `timemachine/results_tm01.json` and `timemachine/results_tm02.json`.
- TM03, the bitcoin dial: from `timemachine/results_tm03.json` (`timemachine/score_tm03.py`). One row per model: months in, gain over the months added up, holding bitcoin over the same months, the percentile against the model's own answers in random order, and the plan's verdict words as the script writes them. A model whose months are not all in shows "Not finished" and no figures. When `timemachine/dial_rules_tm03.json` exists, one line shows the best plain trend rule's sum next to the best model's sum.
- TM04, the stock basket: from `timemachine/results_tm04.json` (`timemachine/score_tm04.py`). One row per model and run: gain, equal shares of the list, the percentile among random baskets, and the verdict. A run that is not finished shows its verdict ("running" or "not started") and no figures. Until the file exists the plan says "Being scored".


## Running now and newest results

The "Running now" strip at the top lists the rows of the "Running now" table in `docs/QUEUE.md`: the row number and the first sentence of each row, with file pointers removed. A row whose current step starts with STOPPED, PAUSED, HOLD or Registered gets a small state tag (for example "Stopped 2026-11-26 4:47 PM MT on data terms" or "Registered ..., not started"). It is read each time the export runs.

"Newest results" comes next. It holds five cards made by `research_rig/newest_cards.py`. The Plan 75 card comes first: it reads the two pinned aggregate files that the builder of doc 181 reads (the official run's output and the blind recompute's result), with the same SHA-256 pins, stops the export if a pin or a figure stops fitting, and says "Figures not on this computer" when the files are absent. The coin sweep card (plans 70 and 71) and the plan 73 card read the pinned summary files that the builders of docs 152, 154 and 157 read, with the same SHA-256 pins, and stop the export if a pin or a figure stops fitting. Those files are kept off the repo; on a computer without them the two cards say "Figures not on this computer" and show no figure. The Plan 75 and plan 73 cards have a small bar chart drawn in plain HTML, with each value written beside its bar. The E09 and E10 cards say they were stopped on data terms. Each reads its stop time and its replacement (E12, E13) from its own row in the queue page (rows 114 and 131), which must start with "STOPPED ... on data terms", and the export stops if that row no longer says so. They show only the count of wakes before the stop, from `practice/forward/E09_log.json` and `practice/forward/E10_log.json`; the E10 file must still have the shape that `practice/forward_e10.py publish` writes. No price, cost or profit is shown. Times are shown in Mountain Time with the label MT.

## Files

- `index.html`: page layout
- `styles.css`: look, light and dark themes
- `app.js`: reads `data.json` and fills the page
- `data.json`, `curves_cache.json`: made by the export script. Git ignores both, so a fresh copy of the repo has neither
- `fonts/`: interface font. Git ignores this folder, so a fresh copy of the repo does not have it and the page falls back to the system font
- `vendor/chart.umd.min.js`: Chart.js, unchanged copy of the published file
