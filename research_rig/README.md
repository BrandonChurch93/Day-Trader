# research_rig: a research tool, not the product

This folder holds the test rig used during research to replay rules on past prices. It exists to produce evidence for `docs/research/`. Current results are summarised in `docs/STATUS.md`. Read that first.

- It is not the trading system and no part of it is meant to become the trading system. The product is built once, from an approved plan, as `docs/quality/` says.
- It places no orders, holds no keys and talks to no broker.
- Raw price files are not stored here. `data/` is a local folder that git ignores.

## Two versions of the engine

| Version | Files | Use it for |
|---|---|---|
| v2, current | `rig2.py`, `fixtures2.py` (checks), `basket.py`, `fixtures_basket.py` | Every new test. Built after two code audits (`docs/research/16_rig_audit.md`). Reads every bar from `config/thresholds.yaml` |
| v1, kept as the record | `engine.py`, `fixtures.py`, `common_01.py`, `common_03.py` | Nothing new. It produced the first-run numbers in documents 12, 12b and 15, which document 16 corrects |

`rules.py` (the nine daily trend rules) and `common_03.py` (the eight hourly rules) hold rule definitions only. Both versions use them. The audits found no fault in them.

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
| `TRIAL_LEDGER.md` | The count of every rule variant tried. A result with no row here does not count |
| `fetch.py`, `fetch_kraken_archive.py`, `build_kraken_daily.py`, `kraken_daily_build.json` | Download and prepare public price history into local folders outside the repo |
| `data_notes_french.md` | Where the stock index data for replay 05 came from and how it is laid out |
| `books_summary.py`, `books_summary.json` | What it cost to trade $100, $1,000 and $10,000 at once, from order-book samples taken overnight (`docs/research/24_order_book_costs.md`) |
| `feeds/` | A small collector of public context readings (bill rates, insider filings, Fed dates). `feeds/SOURCES.md` lists each source and its terms |
| `export_dashboard.py` | Builds `dashboard/data.json` from the output files for the owner's screen in `dashboard/` |
| `tables_01.py`, `tables_01.md`, `report_01.py` | Helper tables for document 12 |

## The five pass marks

Every replay is judged on the same five marks. The numbers are in `config/thresholds.yaml` and are read from there by the code.

| Mark | What it asks | Config key |
|---|---|---|
| 1 | Held-back slice: a better Sharpe ratio than the comparison, and a largest drop no more than a set share of the comparison's | `replay_max_drop_ratio_vs_hold` |
| 2 | Whole sample: the rule stays ahead of the comparison up to a cost that is a set multiple of the modeled cost | `backtest_min_breakeven_cost_multiple` |
| 3 | Whole sample: deflated Sharpe ratio, with every trial in the ledger counted | `replay_min_deflated_sharpe` |
| 4 | The overfitting estimate across the set of rules in the plan | `backtest_max_pbo` |
| 5 | The rule beats a set share of versions of itself with the timing shuffled | `replay_min_shuffle_percentile` |

A pass means "worth running in a practice account". It does not mean "makes money". Mark 1 does not ask for more growth than holding.

## How to add a test

1. Write `PREREG_NN_name.md`: question, data, fill and cost rules, the rules frozen, slices, comparisons, pass marks by config key, checks.
2. Add its rows to `TRIAL_LEDGER.md` with the time, in the same commit as the plan. `AGENTS.md` hard rule 8.
3. Commit and push. Only then run anything on the held-back slice.
4. Write `run_NN.py` on `rig2.py`. It must run `fixtures2.py` first and stop if a check fails. It writes `results_NN.json`.
5. Have a different model audit the code against the plan before the result is believed. The audit report goes in `audit/`. It should rebuild at least one rule from the raw data in its own code.
6. If the audit finds the code does not match the plan: write `AMENDMENT_NN_name.md`, push it, then run again into a new output file. Keep the first output. Report both.
7. Write `build_docNN.py` that turns the output into `docs/research/NN_name.md`. No number is typed.
8. Add a row function to `tools/status_table.py`, run `python3 tools/status_table.py --write`, and update `docs/STATUS.md`, `docs/INDEX.md` and the table above in the same commit. Run `python3 tools/check_repo.py`.

## How to run a test again

Raw price files are not in the repo. `fetch.py`, `fetch_kraken_archive.py` and `build_kraken_daily.py` download public history into local folders, and `data_notes_french.md` says where the stock index files come from. Then, from this folder:

| To rebuild | Run |
|---|---|
| The rerun of replays 01, X2, S2, 03 and document 16 | `python3 run_v2.py`, `python3 compare_v1_v2.py`, `python3 noise_pbo.py`, `python3 build_doc16.py` |
| Replay 04 and document 23 | `python3 run_04.py`, `python3 build_doc23.py` |
| Replay 05 and document 22 | `python3 run_05.py`, `R05_POOL=1 python3 run_05.py`, `python3 build_doc22.py` |
| Document 24 | `python3 books_summary.py`, `python3 build_doc24.py` |
| The table in the status page | from the repo root, `python3 tools/status_table.py --write` |

## Things that have gone wrong here before

- Python 3.14 starts worker processes fresh by default. A pool whose workers rely on data loaded by the parent must use `multiprocessing.get_context("fork")`.
- A long run started in the background must be fully detached, or it dies when the shell that started it exits and its results are lost.
- The overfitting estimate (mark 4) moves a lot with the start date, and it is worked out across the whole set of rules, so correcting one rule moves it for all of them. Do not read one value as a yes or no (`docs/research/16_rig_audit.md`, `docs/research/22_replay_05_stock_trend.md`).
- Mark 3 screens nothing if the spread of Sharpe ratios is taken across a few rules that all trade the same market. Take it across all counted trials.
- `basket.py` has three known faults that did not change replay 04 and must be fixed before it is used again: the sale of a coin whose history ends uses knowledge of the full file, trades are sized on the account value before costs, and the monthly comparison can drop a buy it could not fund (`audit/2026-11-25_replay_04_audit.md`, findings 04-01 to 04-03).
- A slot that is split once and never again drifts. Replay 05's rule I2 ended up almost all in one slot (`AMENDMENT_05_I2_equal_thirds.md`).
- A table column must say what it counts. "Trade sides" in replay 05 counted days with a trade.

Needs Python 3 with numpy, pandas and scipy.
