# research_rig: a research tool, not the product

This folder holds the test rig used during research to replay rules on past prices. It exists to produce evidence for `docs/research/`. Current results are summarised in `docs/STATUS.md`. Read that first.

- It is not the trading system. For the builder's current workflow, see `AGENTS.md`, "How the work goes".
- It places no orders, holds no keys and talks to no broker.
- Raw price files are not stored in the repo. Scripts read them from `research_rig/data/`, a local folder that git ignores. A fresh copy of the repo does not have it. See "Raw data" below before running anything.
- Terms, test names and rule names are defined in `docs/GLOSSARY.md`.

## Two versions of the engine

| Version | Files | Use it for |
|---|---|---|
| v2, current | `rig2.py`, `fixtures2.py` (checks), `basket.py`, `fixtures_basket.py` | Every new test. Built after two code audits (`docs/research/16_rig_audit.md`). Reads every bar from `config/thresholds.yaml` |
| v1, kept as the record | `engine.py`, `fixtures.py`, `common_01.py` | Nothing new. It produced the first-run numbers in documents 12, 12b and 15, which document 16 corrects |

`rules.py` (the nine daily trend rules) and `common_03.py` (the eight hourly rules) hold rule definitions only. Both versions use them. The audits found no fault in them.

What the engine is and is not:

- `rig2.py` fills an order at the next bar's opening price. It was written for the crypto replays.
- Replay 05 does not use those fills. Its data is daily returns of an index, with no opening prices, so `run_05.py` trades one day late at that day's close-to-close return. It uses `rig2.py` for the statistics only.
- Pilot 02 was scored with the v1 engine and has not been scored again with v2. Its result was inconclusive by design, so the audit fixes would not change what it says.
- It is a research replay. It is not a simulator of a broker and no part of it is product code.

## Every test, in one table

"Plan" is written and pushed before the run and is not edited afterwards. "Doc" is built by the script named, from the output file, so no number is typed by hand.

| Id | Question | Plan | Run script | Output | Doc builder | Doc | Engine | State |
|---|---|---|---|---|---|---|---|---|
| Replay 01 | Nine slow trend rules on bitcoin and ether, Bitstamp prices | `PREREG_01_daily_crypto_trend.md` | `run_01.py`, `run_01b.py` | `results_01.json`, `passmarks_01.json` | `build_doc12.py` | `docs/research/12_replay_01_crypto_trend.md` | v1 | Superseded by the rerun |
| S1 | Does a later fill change replay 01 | `PREREG_01_S1_fill_delay.md` | `run_01c.py`, `report_01d.py` | `results_01c.json`, `results_01d.json` | `build_doc12.py` | same | v1 | Superseded by the rerun |
| X2, S2 | Replay 01 on Kraken's price history | `PREREG_01_X2_kraken_full_history.md` | `run_01x2.py`, `diag_x2_pbo.py` | `results_01x2.json`, `diag_x2_pbo.json` | `build_doc12b.py` | `docs/research/12b_replay_01_kraken_crosscheck.md` | v1 | Superseded by the rerun |
| Pilot 02 | Six AI model runs making daily calls | `PREREG_02_ai_calls_pilot.md` | `pilot/server.py`, `score_02.py` | `pilot/decisions.jsonl`, `results_02.json` | `build_doc14.py` | `docs/research/14_ai_calls_pilot_02.md` | v1 | Current. Inconclusive by design |
| Replay 03 | Eight day trading rules on hourly bitcoin and ether | `PREREG_03_intraday_crypto.md` | `run_03.py` | `results_03.json` | `build_doc15.py` | `docs/research/15_replay_03_intraday_crypto.md` | v1 | Superseded by the rerun |
| Rerun | Replays 01, X2, S2 and 03 again with the audit fixes | `AMENDMENT_2026-11-25_audit_fixes.md` | `run_v2.py`, `compare_v1_v2.py`, `noise_pbo.py` | `results_v2.json`, `compare_v1_v2.json`, `noise_pbo.json`, `venue_price_gap.json` | `build_doc16.py` | `docs/research/16_rig_audit.md` | v2 | Current measurement for replays 01 and 03. Its passes are not credited: besides engine fixes, one of which changes one rule's trades, it carried two changes that were not engine faults: a stricter pass mark and a change to what holding pays (question 18b). Its fails stand |
| Replay 04 | Trend rules on a wide basket of coins, with coins that died included | `PREREG_04_coin_basket_trend.md` | `run_04.py` | `results_04.json`, `NOTES_04_builder.md` | `build_doc23.py` | `docs/research/23_replay_04_coin_basket.md` | v2 | Current. Nothing passes. Ledger row was added after the run started (question 18b). Audited: `archive/audit/2026-11-25_replay_04_audit.md`. `basket.py` has known faults, see below |
| Replay 05 | Slow trend rules on the US stock market from 1927, free index data | `PREREG_05_stock_trend_free_data.md`, `AMENDMENT_05_I2_equal_thirds.md` | `run_05.py` (corrected run: `R05_POOL=1`) | `results_05.json` (first run), `results_05b.json` (corrected run) | `build_doc22.py` | `docs/research/22_replay_05_stock_trend.md` | v2 | Current measurement, both runs. Passes not credited in either run: the first run's ledger row was late, and the corrected run was made before asking the owner (question 18b). Audited: `archive/audit/2026-11-25_replay_05_audit.md` |
| Replay 06 | Slow trend rules on funds that can be bought | `PREREG_06_fund_trend_paid_data.md` | `run_06.py` | `results_06.json` | `report_06.py` | `docs/research/35_replay_06_fund_trend.md` | v2 pass marks, calendar-aware fund runner | MEASURED. Held slice run once after the design run. Ledger rows 115 to 120. None passed at 5 bps per side |
| Replay 07 | Day trading SPY and QQQ on one-minute bars | `PREREG_07_intraday_spy_qqq.md` | `run_07.py` | `results_07.json` | `build_doc27.py` | `docs/research/27_replay_07_intraday_spy_qqq.md` | v2 pass marks, own calendar-aware bar check | Run once. Ledger rows 56 to 71 |
| Replay 08 | Buying after insiders buy, daily, stocks that later died kept | `PREREG_08_insider_buying_DRAFT.md` | not written | | | | v2 | Draft plan. Runs nothing. Needs dated filings, prices that include stocks that later died, and final test settings from the builder. See `docs/QUEUE.md` |
| Replay 09 | New long-only rules on Alpaca hourly and daily crypto bars | `PREREG_09_crypto_methods.md` | `run_09.py` | `results_09.json` | `build_doc28.py` | `docs/research/28_replay_09_crypto_methods.md` | replay 09 fills, v2 pass marks | Run once. See the write-up for coverage and verdicts |
| Replay 18 | Three-day funding carry on dated USD-M contracts. Four current US rosters shown only | `PREREG_18_funding_carry.md` | `score_18.py` | None yet | None | `PLAN_18_rank_page_coverage.md` (metadata only) | Plan 18 in threshold config | Frozen after two audits. The lead agent holds the off-repo seal; real preflight and run wait for publication |
| Practice desk | Fixed rules and AI traders using pretend money on live prices | `practice/PLAN_02_ai_desk.md` | not a rig test | | | | | The program and its records are in `practice/`, not in the rig. See `practice/README.md` |

Side tools:

| File | What it does |
|---|---|
| `TRIAL_LEDGER.md` | The count of every rule variant tried and every rerun. A result with no row here does not count |
| `ledger_count_check.py`, `ledger_count_check.json` | Works out pass mark 3 again from the stored outputs with both reruns counted as trials. Runs no rule and reads no prices |
| `check_data.py` | Says in a second which raw data sets are present, whether they match the files the stored outputs were made from, and how to get the missing ones |
| `provenance.py`, `provenance.json` | For each stored output: the command, the code files, the commits that first stored it and last changed it, its fingerprint, and the fingerprint of each raw input file. The check compares outputs and inputs with their fingerprints. It lists the code files and does not fingerprint them, so it cannot show that the code now in the repo is the code that made an output. Built after the fact from git history and the files on the research machine, because the runs did not record it themselves |
| `requirements.txt` | The Python package versions the stored outputs were made with |
| `fetch.py`, `fetch_kraken_archive.py`, `fetch_french.py`, `build_kraken_daily.py`, `kraken_daily_build.json` | Download and prepare public price history into `research_rig/data/` |
| `data_notes_french.md` | Where the stock index data for replay 05 came from and how each file is laid out |
| `platform_bars_consolidate.py`, `platform_bars_integrity.py`, `platform_bars_coverage.json`, `platform_bars_crosscheck.py`, `platform_bars_crosscheck.json` | Join and gap-check the stock prices collected through the workspace's own price lookup on 2026-11-25, and compare its one-minute files with its daily files. The two json files hold dates, counts, gaps in basis points and file fingerprints, no price. `tools/bars_coverage.py` writes the tables in `docs/research/10_historical_data_and_practice.md` from them. The join script was not run again from the repo and has known limits, listed in that document. No rule has been run on these prices. Confirm the terms for storing and using them before running a rule |
| `books_summary.py`, `books_summary.json` | What it cost to trade $100, $1,000 and $10,000 at once, from order-book samples taken on 2026-11-25 (`docs/research/24_order_book_costs.md`) |
| `feeds/` | A small collector of public context readings (bill rates, insider filings, Fed dates). `feeds/SOURCES.md` lists each source and its terms |
| `export_dashboard.py` | Builds `dashboard/data.json` for the owner's screen in `dashboard/`. The figures come from the output files. The five charts come from saved curves in `dashboard/curves_cache.json`, which is not committed. With `--resimulate` it replays five stored runs, of three rules, on raw prices, held-back years included, to remake those curves: that is a held-back run, see "How each stored output was made" |
| `tables_01.py`, `tables_01.md`, `report_01.py` | Helper tables for document 12 |

## The five pass marks

Every replay is judged on the same five marks. The numbers are in `config/thresholds.yaml` and are read from there by the code.

- These keys have the status "builder" in the config file. The builder fixes them before a test and does not change them after seeing its result (`AGENTS.md`, "Honest testing", item 2).
- A plan can add conditions on top of the five marks. The crypto rerun asks for a pass on both price histories and uses the worse of two fill times for mark 1. Read the plan of the test you are looking at.
- The "comparison" is what the rule is measured against: simply holding the same thing over the same dates, paying the same cost per side.

| Mark | What it asks | Config key |
|---|---|---|
| 1 | Held-back slice: a better Sharpe ratio than the comparison, and a largest drop no more than a set share of the comparison's | `replay_max_drop_ratio_vs_hold` |
| 2 | Whole sample: the rule stays ahead of the comparison up to a cost that is a set multiple of the modeled cost | `backtest_min_breakeven_cost_multiple` |
| 3 | Whole sample: deflated Sharpe ratio, with the trials in the ledger counted. Past runs used the count when their plan was frozen, without the reruns (`TRIAL_LEDGER.md`, "Reruns and how they are counted") | `replay_min_deflated_sharpe` |
| 4 | The overfitting estimate across the set of rules in the plan | `backtest_max_pbo` |
| 5 | The rule beats a set share of versions of itself with the timing shuffled | `replay_min_shuffle_percentile` |

A pass means "worth running in a practice account". It does not mean "makes money". Mark 1 does not ask for more growth than holding.

## How to add a test

`AGENTS.md`, "Honest testing", sets the rules. The rest of this table describes how the rig records and checks the work.

| # | Step | Where it comes from |
|---|---|---|
| 1 | Write `PREREG_NN_name.md`: question, data, fill and cost rules, the rules frozen, slices, comparisons, pass marks by config key, checks | A written plan shows what was set before the run (`AGENTS.md`, "Honest testing", item 2) |
| 2 | Add its rows to `TRIAL_LEDGER.md` with the time before the run | `AGENTS.md`, "Honest testing", item 1 |
| 3 | Before opening the held-back slice, preserve a dated copy of the ledger and plan | This makes the order of events checkable (`AGENTS.md`, "Honest testing", items 1 to 3) |
| 4 | Write `run_NN.py` on `rig2.py`. Run `fixtures2.py` first and stop if a check fails. The run writes `results_NN.json` | The rig checks the engine against known answers and writes the result to a file |
| 5 | Have a different model audit the code against the plan before the result is believed. It should rebuild at least one rule from the raw data in its own code | This is a research check. Earlier audit reports are in `archive/audit/` |
| 6 | If a test changes, write an amendment and give the new attempt its own ledger row before it runs. Keep and report both outputs. Do not reuse a held-back slice for the same strategy version | `AGENTS.md`, "Honest testing", items 1 to 3. Earlier reruns are recorded in `TRIAL_LEDGER.md` |
| 7 | Write `build_docNN.py` that turns the output into `docs/research/NN_name.md`. The document number is the next free number in that folder, not the replay number | Numbers come from script outputs (`AGENTS.md`, "Honest testing", item 6) |
| 8 | Add a row function to `tools/status_table.py`, run `python3 tools/status_table.py --write`, update `docs/STATUS.md`, `docs/INDEX.md` and the table of tests above in the same commit, and run `python3 tools/check_repo.py` | Practice. It keeps the map true |

Things a new test must also get right:

- Do not look early. While writing and debugging `run_NN.py`, use the fixtures and the development slice only. No current script has a switch that leaves the held-back dates out, so a test run of the whole script shows held-back results. Build that switch into the next run script, and do not run the whole script until step 3 is done.
- The trial count for pass mark 3 is the count in `TRIAL_LEDGER.md` on the day the plan is frozen, plus the new trials, and it includes reruns. Write the number in the plan.
- The builder records which spread it uses for pass mark 3 and how it will measure pass mark 4 in the plan before the test runs.
- A plan whose file name ends in `_DRAFT` is not frozen. To freeze it: settle every line in it that says "to settle before this plan is frozen", write the trial count in it, rename the file without `_DRAFT`, add its ledger rows, and push that as one commit before anything is run (steps 1 to 3). Change the file name in `docs/INDEX.md`, `docs/STATUS.md` and the table of tests above in the same commit.
- A new test also has to be added by hand to three lists, or the checks will not know about it: the inputs and outputs in `provenance.py`, the data sets in `check_data.py` if it reads a new one, and the tables "How each stored output was made" and "Held-back scripts" on this page. Then `python3 provenance.py --record` after the commit that holds the output, and commit the record.
- Check that a faulty backtest or reused held-back slice cannot turn a loss into a credited pass (`AGENTS.md`, "Honest testing", items 3 and 7).
- Record with each output the command, the commit of the code and the fingerprint of the input data. `provenance.py` does this for the stored outputs after the fact. A new run script should write them into its own output.
- `rig2.py` cannot yet judge a test with one rule. Measured on 2026-11-25: with one rule `pbo_cscv` returns 1.0, because every split is a tie and a tie counts as overfit, so mark 4 fails; and the spread of Sharpe ratios across one rule is undefined, so mark 3 comes back undefined and counts as a fail. The builder has to choose how to measure marks 3 and 4 in a one-rule plan before it runs.
- `rig2.check_bars` expects a bar for every day or hour with no gaps, which is right for crypto. It rejects stock or gold bars, which have no weekends. Replay 05 did not use it: it read daily returns. A test on stock bars needs a calendar-aware check with its own fixtures first.
- The pass marks say nothing about the practice account. What counts as a pass there is not fully defined yet (`docs/GLOSSARY.md`, "Practice account pass").

## Raw data

Run `python3 check_data.py` from this folder first. It takes a few seconds, lists each data set as present or missing, says whether each present file matches the fingerprint on record in `provenance.json`, and prints the command that fetches a missing one. A script that needs a missing file stops with a file-not-found error. No script reads from anywhere outside the repo folder unless one of the variables below is set.

| Data set | Where scripts look | Variable that overrides it | How to get it | Used by |
|---|---|---|---|---|
| Bitstamp daily and hourly bars, bitcoin and ether | `data/bitstamp_*.csv` | none | `python3 fetch.py crypto`, `python3 fetch.py hourly` | Replays 01 and 03, the rerun, pilot 02 |
| Kraken recent daily bars from its public endpoint | `data/kraken_*.csv` | none | `python3 fetch.py kraken` | X1, `build_kraken_daily.py` |
| Kraken published archive, bitcoin and ether, daily and hourly | `data/kraken/full_*.csv` | `KRAKEN_DIR` | `python3 fetch_kraken_archive.py full` | The rerun, `build_kraken_daily.py` |
| Kraken full daily history, built from the Kraken archive, the Kraken recent bars and the Bitstamp daily bars (all three rows above) | `data/krakenfull_*.csv` | none | `python3 build_kraken_daily.py` | X2, S2, the rerun, document 16 |
| Kraken published archive, every US dollar pair, daily | `data/kraken/daily/` | `KRAKEN_DAILY_DIR` | `python3 fetch_kraken_archive.py daily` | Replay 04 |
| Alpaca US crypto hourly and daily bars | ~/workspace/rig/data/alpaca_crypto/ | none | `python3 fetch_09_alpaca.py --prioritize-replay-window`; `--steady-only` pulls full hourly histories for recent steady-volume pairs | Replay 09. The minute tape is checked for gaps only and not used for rules |
| Alpaca US stocks SIP fund daily bars, all-adjusted and split-only | ~/workspace/rig/data/funds_daily/ | none | Saved Alpaca data credential and the historical stock bars endpoint. `audit_06_fund_coverage.py` checks dates and counts against XNYS (`exchange_calendars`); `audit_06_fund_adjustments.py` checks distributions and published total returns | Replay 06. The rules used all-adjusted bars; split-only bars were for audit |
| Kenneth French library: market return and twelve industry groups, daily | `data/french/` | `FRENCH_DIR` | `python3 fetch_french.py` | Replay 05, `i2_2020_note.py` |
| Stock prices from the workspace's own price lookup: one-minute SPY and QQQ, daily for the funds listed in document 10 | `data/platform_bars/` | `PLATFORM_BARS_DIR` | Cannot be fetched by a script. Collected by an agent on 2026-11-25. Dates and counts are in `platform_bars_coverage.json` | Nothing yet |
| Order-book samples from one day | `data/books/books.csv` | first argument of `books_summary.py` | Cannot be fetched again. The summary is in `books_summary.json` | `books_summary.py` |
| Context readings | `data/feeds_cache/` | `FEEDS_CACHE_DIR` | From the repo root: `python3 research_rig/feeds/collect_context.py` | Nothing yet |

- A fresh download is not the same data. The public endpoints return history up to today, Kraken's recent-bars endpoint reaches back about 720 days only, and the French library rebuilds its whole history at each update. The scripts cut every series at fixed dates, so most of it will match, and small differences are possible. A run on a fresh download is a new run. Say so when reporting it.
- Terms of use differ by source and some are open questions for the owner (`docs/STATUS.md`, "Waiting on the owner"). Do not add a source without reading its terms.
- Until 2026-11-25 the scripts defaulted to folders on the research machine. That was changed to the paths above. Only the path lines changed. In `basket.py` only line 4 changed, and its three known faults are still there.

## How each stored output was made

Read this first. This table is a record of which command made which file. It is not permission to run anything.

- The document builders (`build_docNN.py`), `compare_v1_v2.py`, `ledger_count_check.py`, `provenance.py`, `check_data.py`, `tools/status_table.py` and `export_dashboard.py` with no flag read stored outputs only, with one exception: when the two daily bitcoin files are on the machine, `build_doc16.py` also reads them and compares their closing prices day by day, which runs no rule, and writes `venue_price_gap.json` again. On unchanged files that gives the same bytes. On a fresh download it need not, and then `tools/check_repo.py --builders` fails; restore the stored file with `git checkout research_rig/venue_price_gap.json`. `noise_pbo.py` reads no prices at all: it draws random numbers. None of these runs a rule on any price and all are safe to run at any time. On an unchanged copy of the repo they change no tracked file. `python3 tools/check_repo.py --builders` checks that.
- Held-back scripts. The scripts that run a rule, or score or collect trading calls, on prices that include held-back dates are `run_*.py` (including `run_06.py --held`, which must not be rerun), `report_01d.py`, `diag_x2_pbo.py`, `score_02.py`, `pilot/server.py` and `export_dashboard.py --resimulate`. `i2_2020_note.py` runs no rule: it multiplies up industry returns for one held-back year. It is kept on this do-not-run list by practice, because its output describes held-back prices. `provenance.json` marks each stored output of these "held-back". The dashboard files are not committed and are not in that record. Five more scripts read raw prices with held-back dates and run no rule (`build_kraken_daily.py`, `build_doc16.py`, `platform_bars_consolidate.py`, `platform_bars_integrity.py` and `platform_bars_crosscheck.py`). `provenance.json` marks their stored outputs "prices-no-rule". `AGENTS.md`, "Honest testing", items 2 and 3: fix thresholds, costs and dates before running a test, and use the held-back slice only once per strategy version.
- To check a stored result, use `python3 tools/check_repo.py --builders` rather than rerunning its held-back test. Until 2026-11-25 `export_dashboard.py` replayed its five runs, of three rules, every time it ran. No stored output changed, but those replays made the curves, yearly figures and trade lists that were shown on the screen. `i2_2020_note.py` was also rerun once after its data path changed, with identical output. These are historical reruns, not new evidence (`TRIAL_LEDGER.md`, "Reruns and how they are counted").
- A run on freshly downloaded data is a new run on different data, not a reproduction. `provenance.json` holds the fingerprint of every input file as it was on the research machine when the record was taken, on 2026-11-25 after the runs, and `check_data.py` says whether the files on this machine match. No input file was modified after the output that used it was first stored, which is what the record can show. It cannot prove the bytes were the same at run time. If you download data yourself, `check_data.py` and `tools/check_repo.py` will say your files differ from the record. That is expected. Do not run `provenance.py --record --replace` to make the message go away: it would overwrite the record of the files the stored results came from. Commit from a copy of the repo with no data folder, or set the folder aside.

From this folder:

| Output | Made by |
|---|---|
| Replay 06 and document 35 | The builder ran `python3 run_06.py` for design, then `python3 run_06.py --held --prereg-commit af8554c` once. Do not repeat either real-data command. `python3 report_06.py` writes the report from stored summaries only; `python3 report_06.py --check` checks that it is current |
| The rerun of replays 01, X2, S2, 03 and document 16 | `python3 run_v2.py`, `python3 compare_v1_v2.py`, `python3 noise_pbo.py`, `python3 build_doc16.py` |
| Replay 04 and document 23 | `python3 run_04.py`, `python3 build_doc23.py` |
| Replay 05 and document 22 | `python3 run_05.py` (first run, writes `results_05.json`), `R05_POOL=1 python3 run_05.py` (corrected run, writes `results_05b.json`), `python3 i2_2020_note.py`, `python3 build_doc22.py` |
| Replay 07 and document 27 | `python3 run_07.py --full` once, then `python3 build_doc27.py` from results only. `python3 run_07.py --fixtures` runs the checks only; `--dev` runs the development years only and writes to /tmp |
| Replay 09 and document 28 | `python3 run_09.py --held --prereg-commit 74ad30c` once, then `python3 build_doc28.py` from results only. `python3 fetch_09_alpaca.py` pulls data and runs no rule. The replay-only option to inspect rules before the held-back run is `python3 run_09.py --dev` |
| Later full-hourly coverage for Replay 09 | `python3 fetch_09_alpaca.py --steady-only` then `python3 audit_09_alpaca.py`. This writes `alpaca_coverage_09.json`, reading prices but running no rule. The document builder uses that file and the unmodified replay results |
| The trial count check | `python3 ledger_count_check.py` |
| Document 24 | `python3 books_summary.py`, `python3 build_doc24.py` |
| The coverage tables in document 10 | `python3 platform_bars_integrity.py` and `python3 platform_bars_crosscheck.py` (both need the price files), then from the repo root `python3 tools/bars_coverage.py --summarise` and `python3 tools/bars_coverage.py --write` |
| The table in the status page | from the repo root, `python3 tools/status_table.py --write` |
| The record of what made each output, from which inputs | `python3 provenance.py` checks the stored outputs and the present input files against `provenance.json` and writes nothing. `python3 provenance.py --record` rewrites the file after an output changes and has been committed |

`R05_POOL=1` switches on the correction in `AMENDMENT_05_I2_equal_thirds.md`: when rule I2 comes back from all cash, the account is split into three equal thirds again. Without it the script reproduces the first run, where the thirds were set once in 1927 and drifted.

## Things that have gone wrong here before

- Python 3.14 starts worker processes fresh by default. A pool whose workers rely on data loaded by the parent must use `multiprocessing.get_context("fork")`.
- A long run started in the background must be fully detached, or it dies when the shell that started it exits and its results are lost.
- The overfitting estimate (mark 4) moves a lot with the start date, and it is worked out across the whole set of rules, so correcting one rule moves it for all of them. Do not read one value as a yes or no (`docs/research/16_rig_audit.md`, `docs/research/22_replay_05_stock_trend.md`).
- Mark 3 screens nothing if the spread of Sharpe ratios is taken across a few rules that all trade the same market. Research proposes taking it across all counted trials in the next plan. That is a proposal to the owner, not an approved rule.
- A rerun is a trial. Two reruns were left out of the ledger and out of the count, and had to be added late (`TRIAL_LEDGER.md`, rows R1 and R2).
- Scripts once defaulted to data folders on one machine, so on that machine a fresh copy of the repo silently read data it did not own. Defaults now sit inside the repo folder.
- `basket.py` has three known faults that did not change replay 04 and must be fixed before it is used again: the sale of a coin whose history ends uses knowledge of the full file, trades are sized on the account value before costs, and the monthly comparison can drop a buy it could not fund (`archive/audit/2026-11-25_replay_04_audit.md`, findings 04-01 to 04-03).
- A slot that is split once and never again drifts. Replay 05's rule I2 ended up almost all in one slot (`AMENDMENT_05_I2_equal_thirds.md`).
- A table column must say what it counts. "Trade sides" in replay 05 counted days with a trade.

Needs Python 3 with numpy, pandas, scipy and PyYAML. The run scripts start worker processes with the "fork" method, so they need Linux or macOS. The versions used are in `requirements.txt`. All stored outputs were made on Python 3.14.
