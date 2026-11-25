# research_rig: a research tool, not the product

This folder holds the test rig used during research to replay rules on past prices. It exists to produce evidence for `docs/research/`. Current results are summarised in `docs/STATUS.md`. Read that first.

- It is not the trading system and no part of it is meant to become the trading system. The product is built once, from an approved plan, as `docs/quality/` says.
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
| Rerun | Replays 01, X2, S2 and 03 again with the audit fixes | `AMENDMENT_2026-11-25_audit_fixes.md` | `run_v2.py`, `compare_v1_v2.py`, `noise_pbo.py` | `results_v2.json`, `compare_v1_v2.json`, `noise_pbo.json`, `venue_price_gap.json` | `build_doc16.py` | `docs/research/16_rig_audit.md` | v2 | Current. This is the verdict for replays 01 and 03 |
| Replay 04 | Trend rules on a wide basket of coins, with coins that died included | `PREREG_04_coin_basket_trend.md` | `run_04.py` | `results_04.json`, `NOTES_04_builder.md` | `build_doc23.py` | `docs/research/23_replay_04_coin_basket.md` | v2 | Current. Audited: `audit/2026-11-25_replay_04_audit.md`. `basket.py` has known faults, see below |
| Replay 05 | Slow trend rules on the US stock market from 1927, free index data | `PREREG_05_stock_trend_free_data.md`, `AMENDMENT_05_I2_equal_thirds.md` | `run_05.py` (corrected run: `R05_POOL=1`) | `results_05.json` (first run), `results_05b.json` (corrected run) | `build_doc22.py` | `docs/research/22_replay_05_stock_trend.md` | v2 | Current. Audited: `audit/2026-11-25_replay_05_audit.md` |
| Replay 06 | Slow trend rules on funds that can be bought | `PREREG_06_fund_trend_paid_data_DRAFT.md` | not written | | | | v2 | Draft plan. Waits for a data purchase |
| Replay 07 | Day trading SPY and QQQ on one-minute bars | `PREREG_07_intraday_spy_qqq_DRAFT.md` | not written | | | | v2 | Draft plan. Waits for a data purchase |

Side tools:

| File | What it does |
|---|---|
| `TRIAL_LEDGER.md` | The count of every rule variant tried and every rerun. A result with no row here does not count |
| `ledger_count_check.py`, `ledger_count_check.json` | Works out pass mark 3 again from the stored outputs with both reruns counted as trials. Runs no rule and reads no prices |
| `check_data.py` | Says in a second which raw data sets are present and how to get the missing ones |
| `fetch.py`, `fetch_kraken_archive.py`, `fetch_french.py`, `build_kraken_daily.py`, `kraken_daily_build.json` | Download and prepare public price history into `research_rig/data/` |
| `data_notes_french.md` | Where the stock index data for replay 05 came from and how each file is laid out |
| `books_summary.py`, `books_summary.json` | What it cost to trade $100, $1,000 and $10,000 at once, from order-book samples taken overnight (`docs/research/24_order_book_costs.md`) |
| `feeds/` | A small collector of public context readings (bill rates, insider filings, Fed dates). `feeds/SOURCES.md` lists each source and its terms |
| `export_dashboard.py` | Builds `dashboard/data.json` from the output files for the owner's screen in `dashboard/` |
| `tables_01.py`, `tables_01.md`, `report_01.py` | Helper tables for document 12 |

## The five pass marks

Every replay is judged on the same five marks. The numbers are in `config/thresholds.yaml` and are read from there by the code.

- These keys have the status "proposed" in the config file. Research uses them to judge research replays. That use approves nothing. A bar becomes the owner's only when he says so.
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

Steps 1 to 3 and the first half of step 6 are rules (`AGENTS.md` hard rule 8 and the owner's bar in `docs/quality/01_the_bar.md`). The rest is how research works now. Two parts of it, the independent audit in step 5 and the wider spread for mark 3, are proposals to the owner and are not approved rules (`docs/decisions/morning_list_2026-11-25.md`, decisions 2 and 3).

1. Write `PREREG_NN_name.md`: question, data, fill and cost rules, the rules frozen, slices, comparisons, pass marks by config key, checks.
2. Add its rows to `TRIAL_LEDGER.md` with the time, in the same commit as the plan. `AGENTS.md` hard rule 8.
3. Commit and push. Only then run anything on the held-back slice.
4. Write `run_NN.py` on `rig2.py`. It must run `fixtures2.py` first and stop if a check fails. It writes `results_NN.json`.
5. Have a different model audit the code against the plan before the result is believed. The audit report goes in `audit/`. It should rebuild at least one rule from the raw data in its own code.
6. If the audit proves the code was wrong or does not match the plan: write `AMENDMENT_NN_name.md`, add a rerun row to `TRIAL_LEDGER.md` in the same commit, and push. Then run once more into a new output file, using a trial count that includes the rerun. Keep the first output. Report both, and call the second one a rerun. This is the only case in which the held-back slice is run a second time.
7. Write `build_docNN.py` that turns the output into `docs/research/NN_name.md`. No number is typed.
8. Add a row function to `tools/status_table.py`, run `python3 tools/status_table.py --write`, and update `docs/STATUS.md`, `docs/INDEX.md` and the table above in the same commit. Run `python3 tools/check_repo.py`.

## Raw data

Run `python3 check_data.py` from this folder first. It takes a second, lists each data set as present or missing, and prints the command that fetches a missing one. A script that needs a missing file stops with a file-not-found error. No script reads from anywhere outside the repo folder unless one of the variables below is set.

| Data set | Where scripts look | Variable that overrides it | How to get it | Used by |
|---|---|---|---|---|
| Bitstamp daily and hourly bars, bitcoin and ether | `data/bitstamp_*.csv` | none | `python3 fetch.py crypto`, `python3 fetch.py hourly` | Replays 01 and 03, the rerun, pilot 02 |
| Kraken recent daily bars from its public endpoint | `data/kraken_*.csv` | none | `python3 fetch.py kraken` | X1, `build_kraken_daily.py` |
| Kraken published archive, bitcoin and ether, daily and hourly | `data/kraken/full_*.csv` | `KRAKEN_DIR` | `python3 fetch_kraken_archive.py full` | The rerun, `build_kraken_daily.py` |
| Kraken full daily history, built from the two rows above | `data/krakenfull_*.csv` | none | `python3 build_kraken_daily.py` | X2, S2, the rerun, document 16 |
| Kraken published archive, every US dollar pair, daily | `data/kraken/daily/` | `KRAKEN_DAILY_DIR` | `python3 fetch_kraken_archive.py daily` | Replay 04 |
| Kenneth French library: market return and twelve industry groups, daily | `data/french/` | `FRENCH_DIR` | `python3 fetch_french.py` | Replay 05, `i2_2020_note.py` |
| Order-book samples from one night | `data/books/books.csv` | first argument of `books_summary.py` | Cannot be fetched again. The summary is in `books_summary.json` | `books_summary.py` |
| Context readings | `data/feeds_cache/` | `FEEDS_CACHE_DIR` | `python3 feeds/collect_context.py` from the repo root | Nothing yet |

- A fresh download is not the same data. The public endpoints return history up to today, Kraken's recent-bars endpoint reaches back about 720 days only, and the French library rebuilds its whole history at each update. The scripts cut every series at fixed dates, so most of it will match, and small differences are possible. A run on a fresh download is a new run. Say so when reporting it.
- Terms of use differ by source and some are open questions for the owner (`docs/STATUS.md`, "Waiting on the owner"). Do not add a source without reading its terms.
- Until 2026-11-25 the scripts defaulted to folders on the research machine. That was changed to the paths above. Only the path lines changed. In `basket.py` only line 4 changed, and its three known faults are still there.

## How to run a test again

Read this first. The commands below rebuild the documented outputs from the same code and data, to check that they can be reproduced. They are not permission to run the held-back slice again with anything changed. The owner's rule (`docs/quality/01_the_bar.md`): never change a threshold, a cost or a held-back window after seeing a result, and never run the held-back slice a second time for the same version of a rule. The one exception is a rerun after a check proves the engine was wrong, and that rerun gets a ledger row first, is counted as a trial and is reported as a rerun. The document builders (`build_docNN.py`) read stored outputs only and are safe to run. `build_doc16.py` also rebuilds `venue_price_gap.json` when the raw prices are present.

From this folder:

| To rebuild | Run |
|---|---|
| The rerun of replays 01, X2, S2, 03 and document 16 | `python3 run_v2.py`, `python3 compare_v1_v2.py`, `python3 noise_pbo.py`, `python3 build_doc16.py` |
| Replay 04 and document 23 | `python3 run_04.py`, `python3 build_doc23.py` |
| Replay 05 and document 22 | `python3 run_05.py` (first run, writes `results_05.json`), `R05_POOL=1 python3 run_05.py` (corrected run, writes `results_05b.json`), `python3 i2_2020_note.py`, `python3 build_doc22.py` |
| The trial count check | `python3 ledger_count_check.py` |
| Document 24 | `python3 books_summary.py`, `python3 build_doc24.py` |
| The table in the status page | from the repo root, `python3 tools/status_table.py --write` |

`R05_POOL=1` switches on the correction in `AMENDMENT_05_I2_equal_thirds.md`: when rule I2 comes back from all cash, the account is split into three equal thirds again. Without it the script reproduces the first run, where the thirds were set once in 1927 and drifted.

## Things that have gone wrong here before

- Python 3.14 starts worker processes fresh by default. A pool whose workers rely on data loaded by the parent must use `multiprocessing.get_context("fork")`.
- A long run started in the background must be fully detached, or it dies when the shell that started it exits and its results are lost.
- The overfitting estimate (mark 4) moves a lot with the start date, and it is worked out across the whole set of rules, so correcting one rule moves it for all of them. Do not read one value as a yes or no (`docs/research/16_rig_audit.md`, `docs/research/22_replay_05_stock_trend.md`).
- Mark 3 screens nothing if the spread of Sharpe ratios is taken across a few rules that all trade the same market. Research proposes taking it across all counted trials in the next plan. That is a proposal to the owner, not an approved rule.
- A rerun is a trial. Two reruns were left out of the ledger and out of the count, and had to be added late (`TRIAL_LEDGER.md`, rows R1 and R2).
- Scripts once defaulted to data folders on one machine, so on that machine a fresh copy of the repo silently read data it did not own. Defaults now sit inside the repo folder.
- `basket.py` has three known faults that did not change replay 04 and must be fixed before it is used again: the sale of a coin whose history ends uses knowledge of the full file, trades are sized on the account value before costs, and the monthly comparison can drop a buy it could not fund (`audit/2026-11-25_replay_04_audit.md`, findings 04-01 to 04-03).
- A slot that is split once and never again drifts. Replay 05's rule I2 ended up almost all in one slot (`AMENDMENT_05_I2_equal_thirds.md`).
- A table column must say what it counts. "Trade sides" in replay 05 counted days with a trade.

Needs Python 3 with numpy, pandas, scipy and PyYAML. The run scripts start worker processes with the "fork" method, so they need Linux or macOS. Run on Python 3.14. No version file is kept.
