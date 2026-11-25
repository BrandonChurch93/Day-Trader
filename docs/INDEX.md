# Index of every file

What this page is: the map of the repository. Every tracked file is listed here, or sits under a folder listed here with a trailing slash. `tools/check_repo.py` fails if that stops being true.

What this page is not: the current state of the project. That is `docs/STATUS.md`. Read it first.

## How to use this page

- Find your task in the first table and read only the files it names.
- The State column says whether a file has been replaced. It does not say whether the owner has approved it or whether a result in it is proven. Many CURRENT files are proposals, first looks or dated audits, and each says so in its own text. What is approved is only what `docs/decisions/` records as an owner decision with a date.
- Terms, test names and rule names are defined in `docs/GLOSSARY.md`.
- `tools/check_repo.py` checks that every tracked file is listed here and that paths and config keys named in the map files exist. It does not check that a file's State is right or that a claim is true.

| State | Meaning |
|---|---|
| CURRENT | Not replaced by a later file. Use it, and read its own labels: CURRENT does not mean approved or proven |
| RECORD | Kept as history. A later file corrects or replaces part of it. The row says which |
| DRAFT | Not agreed and not in force |
| RAW | Working papers behind a CURRENT file. Open only to trace one claim to its source |

## Start from your task

| If you are about to | Read, in this order |
|---|---|
| Do anything at all | `AGENTS.md`, then `docs/STATUS.md`. `AGENTS.md` still names the playbook as the second read; the playbook pages open with a note that sends you to the status page. A change to that line waits on the owner |
| Understand a term, a test name or a rule name | `docs/GLOSSARY.md` |
| Talk to the owner or hand work to him | `docs/quality/03_working_with_the_owner.md`, `docs/decisions/morning_list_2026-11-25.md` |
| Plan, build or review anything | `docs/quality/00_READ_FIRST.md`, then the file it points to for your topic |
| Use or change a number | `config/thresholds.yaml`. Then add a dated note in `docs/decisions/` |
| Run, rerun or add a test on past prices | `research_rig/README.md`, `docs/research/16_rig_audit.md`, `research_rig/TRIAL_LEDGER.md` |
| Judge whether a trading idea is worth testing | `docs/research/25_what_the_evidence_supports.md`, then the playbook page for that market |
| Choose a broker, a venue or a data source | `docs/playbook/04_brokers_data_rules.md`, `docs/research/09_brokers_and_venues.md`, `docs/research/10_historical_data_and_practice.md` |
| Put an AI model anywhere near a trading decision | `AGENTS.md` hard rules 1 and 7, `docs/playbook/03_role_of_ai.md`, `docs/research/11_ai_trader_experiment_design.md` |
| Design the product | `docs/playbook/06_architecture_and_build.md`, `docs/quality/02_how_we_build.md`. Nothing is built yet and building has not been approved |
| Reopen something already settled | `docs/decisions/` first |

## Top level

| File | What it is | State |
|---|---|---|
| `AGENTS.md` | The rules every agent follows. It wins over everything else. Changing it needs the owner | CURRENT |
| `README.md` | Front page. Points here and to the status page | CURRENT |
| `.gitignore` | Keeps price files, logs and private data out of the repo | CURRENT |
| `config/thresholds.yaml` | Every threshold and every owner number, once. Documents name the key and never repeat the value | CURRENT |
| `tools/check_repo.py` | Checks this index, the paths named in the main pages, the config keys named in documents and the results table in the status page. Run before every commit | CURRENT |
| `tools/status_table.py` | Writes the results table in `docs/STATUS.md` from the output files | CURRENT |

## docs/

| File | What it is | State |
|---|---|---|
| `docs/STATUS.md` | Where the project stands today: what was tested, what passed, what waits on the owner, what is next | CURRENT |
| `docs/INDEX.md` | This page | CURRENT |

## docs/quality/ (the owner's standard)

Lines marked OWNER in these files are rules. Lines marked TRANSLATED are proposals.

| File | What it is | State |
|---|---|---|
| `docs/quality/00_READ_FIRST.md` | Entry to the quality bar. Says which of the other files to open for which topic | CURRENT |
| `docs/quality/01_the_bar.md` | What finished work has to look like | CURRENT |
| `docs/quality/02_how_we_build.md` | The build method: plan once, build once, check against the plan | CURRENT |
| `docs/quality/03_working_with_the_owner.md` | How to write to the owner and how decisions get made | CURRENT |
| `docs/quality/04_research_to_build.md` | What has to be true before research turns into building | CURRENT |
| `docs/quality/05_repo_review_2026-11-24.md` | A review of this repo against the bar on that date | RECORD. The repo has changed since. See `docs/STATUS.md`. `docs/quality/00_READ_FIRST.md` says to delete it when its items are closed. It is the owner's file, so whether it is deleted or kept is his call (morning list, item 5) |

## docs/playbook/ (short pages written before the tests)

Written 2026-11-24 from reading, before the project ran any test of its own. Where a playbook line and `docs/STATUS.md` disagree, the status page stands, because it reports our own tests. Every page opens with a dated note that says so. CURRENT here means no later playbook page replaces it. Its statements about what works are reading, not results. Where a page says something "is finished in v1", it describes the planned product. Nothing is built.

| File | What it is | State |
|---|---|---|
| `docs/playbook/00_START_HERE.md` | The whole project in two pages: verdict, what is to be built, where Perplexity fits, phases and gates | CURRENT |
| `docs/playbook/01_stocks_what_works.md` | Stocks: what the published evidence supports | CURRENT |
| `docs/playbook/02_crypto_what_works.md` | Crypto: what the published evidence supports | CURRENT |
| `docs/playbook/03_role_of_ai.md` | What AI models may and may not do here | CURRENT |
| `docs/playbook/04_brokers_data_rules.md` | Brokers, data and the rules that apply to a small account | CURRENT |
| `docs/playbook/05_perplexity_and_costs.md` | Which Perplexity pieces do which job, and list-price cost arithmetic | CURRENT |
| `docs/playbook/06_architecture_and_build.md` | The shape of the product and the build phases | CURRENT |

## docs/decisions/ (dated record)

"Owner decision" is used only for something the owner said, with the date. Everything else is a proposal.

| File | What it is | State |
|---|---|---|
| `docs/decisions/morning_list_2026-11-25.md` | What the owner is being asked to do and decide next, one item at a time | CURRENT |
| `docs/decisions/0001-starting-decisions.md` | The first list of open decisions and proposed starting values | CURRENT |
| `docs/decisions/0002-historical-testing-and-risk-posture.md` | Owner direction on testing with past data and on a middle risk level with a small moonshot share | CURRENT |
| `docs/decisions/0003-quality-bar-adopted.md` | The quality bar was adopted and wired into the repo | CURRENT |
| `docs/decisions/0004-broker-research-2026-11-25.md` | What the broker research proposed | CURRENT |
| `docs/decisions/0005-overnight-research-2026-11-25.md` | Record of the first overnight research run | RECORD. Its results are corrected by `docs/decisions/0006-audit-and-second-night-2026-11-25.md` |
| `docs/decisions/0006-audit-and-second-night-2026-11-25.md` | Record of the code audits, the rerun, replays 04 and 05, the new research summaries and the repo map | CURRENT |
| `docs/decisions/audit_01_stocks_what_works.md`, `docs/decisions/audit_02_crypto_what_works.md`, `docs/decisions/audit_03_role_of_ai.md`, `docs/decisions/audit_04_brokers_data_rules.md`, `docs/decisions/audit_05_perplexity_and_costs.md`, `docs/decisions/audit_06_architecture_and_build.md` | Line by line audits of the six playbook pages against their sources, done 2026-11-24 | RECORD |
| `docs/decisions/source_check_2026-11-24.md`, `docs/decisions/source_check_2026-11-24_crypto.md`, `docs/decisions/source_check_2026-11-24_role_of_ai.md`, `docs/decisions/source_check_2026-11-24_stocks.md` | Checks of cited sources on that date | RECORD |

## docs/research/ (full reports with every source)

Reading reports. Open one when a playbook line or the status page points to it.

| File | What it is | State |
|---|---|---|
| `docs/research/01_stock_daytrading_evidence.md` | Published evidence on day trading stocks | CURRENT |
| `docs/research/02_crypto_trading_evidence.md` | Published evidence on trading crypto | CURRENT |
| `docs/research/03_llm_trading_agents_evidence.md` | Published evidence on AI models as traders | CURRENT |
| `docs/research/04_brokers_data_compliance.md` | First pass on brokers, data and rules | RECORD. `docs/research/09_brokers_and_venues.md` goes further |
| `docs/research/05_perplexity_platform_options.md` | What each Perplexity product can do for this project, with list prices | CURRENT |
| `docs/research/06_architecture_and_build_process.md` | Full architecture and build process proposal | CURRENT |
| `docs/research/07_tradingview_and_operator_access.md` | TradingView and how the owner can run things from Claude Code | CURRENT |
| `docs/research/08_backtester_fixtures_draft.md` | Draft list of checks a backtester must pass | DRAFT |
| `docs/research/09_brokers_and_venues.md` | Brokers and crypto venues compared, with fees | CURRENT |
| `docs/research/10_historical_data_and_practice.md` | Where to get past prices, what may be kept, and practice accounts | CURRENT. The purchase recommendation is updated in the morning list |
| `docs/research/11_ai_trader_experiment_design.md` | How to test an AI trader fairly | CURRENT |
| `docs/research/13_high_risk_sleeve_evidence.md` | Penny stocks, memecoins, pump groups, copy trading: what the evidence says | CURRENT |
| `docs/research/17_verified_traders_and_their_methods.md` | Traders with a checked record and what they say they did | CURRENT |
| `docs/research/18_ai_systems_with_live_records.md` | AI trading systems that have a live record | CURRENT |
| `docs/research/19_information_feeds.md` | News and data feeds: which help, which do not, and which may be used. The dated correction at its end stands over the text above it | CURRENT |
| `docs/research/20_small_account_edges.md` | Small edges open to a small account | CURRENT |
| `docs/research/21_systematic_funds_and_published_rules.md` | Rule-based funds and published rules, with their live records | CURRENT |
| `docs/research/25_what_the_evidence_supports.md` | One page that pulls the reading and all our tests together, with the ranked list of what to test next | CURRENT |

Results of our own tests. `research_rig/README.md` has the plan, script and output for each.

| File | What it is | State |
|---|---|---|
| `docs/research/12_replay_01_crypto_trend.md` | Replay 01, first run: slow trend rules on bitcoin and ether | RECORD. Verdicts corrected by `docs/research/16_rig_audit.md` |
| `docs/research/12b_replay_01_kraken_crosscheck.md` | Replay 01 on a second price history, first run | RECORD. Verdicts corrected by `docs/research/16_rig_audit.md` |
| `docs/research/14_ai_calls_pilot_02.md` | Pilot 02: six AI model runs making daily calls. Inconclusive by design | CURRENT |
| `docs/research/15_replay_03_intraday_crypto.md` | Replay 03, first run: day trading rules on hourly bitcoin and ether. Holds the rule definitions | RECORD. Verdicts corrected by `docs/research/16_rig_audit.md` |
| `docs/research/16_rig_audit.md` | Two code audits, the fixes, and the corrected verdicts for replays 01 and 03. Also why pass mark 4 is unstable | CURRENT |
| `docs/research/22_replay_05_stock_trend.md` | Replay 05: slow trend rules on the US stock market from 1927 | CURRENT |
| `docs/research/23_replay_04_coin_basket.md` | Replay 04: trend rules on a wide basket of coins | CURRENT |
| `docs/research/24_order_book_costs.md` | What it cost to trade small sizes on two venues, sampled overnight | CURRENT |

Working papers.

| Folder | What it is | State |
|---|---|---|
| `docs/research/09_raw/` | Agent reports and claim checks behind document 09. `docs/research/09_raw/orderbook_sampler.py` and `docs/research/09_raw/orderbook_snapshots.jsonl` are an earlier, separate sample. They are not the overnight sample behind `docs/research/24_order_book_costs.md` | RAW |
| `docs/research/10_raw/` | Behind document 10 | RAW |
| `docs/research/11_raw/` | Behind document 11 | RAW |
| `docs/research/13_raw/` | Behind document 13 | RAW |
| `docs/research/17_21_checklogs/` | Second-model check logs for documents 17 to 21 | RAW |

## audit/ (the code audits)

| File | What it is | State |
|---|---|---|
| `audit/2026-11-25_auditor_a.md` | First audit of the first rig's code, 18 findings | CURRENT |
| `audit/2026-11-25_auditor_b.md` | Second audit, of the statistics, 11 findings | CURRENT |
| `audit/replay_independent.py`, `audit/diagnostics.py` | Auditor A's own separate replay and checks | CURRENT |
| `audit/pbo_stability.json` | Auditor B's measurement of how much pass mark 4 moves | CURRENT |
| `audit/2026-11-25_replay_04_audit.md`, `audit/replay_04_independent.py`, `audit/replay_04_probes.py` | Independent audit of replay 04, with its own rebuild from the raw files, 15 findings | CURRENT |
| `audit/2026-11-25_replay_05_audit.md`, `audit/replay_05_probes.py` | Independent audit of replay 05, 5 findings. One led to a corrected run | CURRENT |

## research_rig/ (the test rig, not the product)

`research_rig/README.md` is the map of this folder: which engine version to use, and for each test its plan, script, output and document.

| Files | What they are | State |
|---|---|---|
| `research_rig/README.md` | Map of the folder and how to add a test | CURRENT |
| `research_rig/TRIAL_LEDGER.md` | Count of every rule variant tried, and of every rerun. Its Status column is the record of what was written at the time; current verdicts are in `docs/STATUS.md` | CURRENT |
| `research_rig/ledger_count_check.py`, `research_rig/ledger_count_check.json` | Works out pass mark 3 again from the stored outputs with the two reruns counted as trials. Runs no rule | CURRENT |
| `docs/GLOSSARY.md` | Plain definitions of the terms, test names and rule names used in the repo | CURRENT |
| `research_rig/rig2.py`, `research_rig/fixtures2.py`, `research_rig/basket.py`, `research_rig/fixtures_basket.py` | Engine v2 and its checks | CURRENT |
| `research_rig/rules.py`, `research_rig/common_03.py` | Rule definitions used by both engine versions | CURRENT |
| `research_rig/engine.py`, `research_rig/fixtures.py`, `research_rig/common_01.py` | Engine v1 | RECORD. Use v2 |
| `research_rig/PREREG_01_daily_crypto_trend.md`, `research_rig/PREREG_01_S1_fill_delay.md`, `research_rig/PREREG_01_X2_kraken_full_history.md`, `research_rig/PREREG_02_ai_calls_pilot.md`, `research_rig/PREREG_03_intraday_crypto.md`, `research_rig/PREREG_04_coin_basket_trend.md`, `research_rig/PREREG_05_stock_trend_free_data.md` | Plans written before each test. Not edited after the run | CURRENT |
| `research_rig/AMENDMENT_2026-11-25_audit_fixes.md` | The audit fixes, written before the rerun | CURRENT |
| `research_rig/PREREG_06_fund_trend_paid_data_DRAFT.md`, `research_rig/PREREG_07_intraday_spy_qqq_DRAFT.md` | Plans for two stock tests that wait for a data purchase | DRAFT |
| `research_rig/run_v2.py`, `research_rig/compare_v1_v2.py`, `research_rig/noise_pbo.py`, `research_rig/build_doc16.py`, `research_rig/results_v2.json`, `research_rig/compare_v1_v2.json`, `research_rig/noise_pbo.json`, `research_rig/venue_price_gap.json` | The rerun after the audits and its outputs | CURRENT |
| `research_rig/run_04.py`, `research_rig/results_04.json`, `research_rig/build_doc23.py`, `research_rig/NOTES_04_builder.md` | Replay 04 | CURRENT |
| `research_rig/run_05.py`, `research_rig/AMENDMENT_05_I2_equal_thirds.md`, `research_rig/results_05.json`, `research_rig/results_05b.json`, `research_rig/build_doc22.py`, `research_rig/i2_2020_note.py`, `research_rig/i2_2020_note.json`, `research_rig/data_notes_french.md` | Replay 05: script, the correction to rule I2, first-run output, corrected-run output | CURRENT |
| `research_rig/run_01.py`, `research_rig/run_01b.py`, `research_rig/run_01c.py`, `research_rig/run_01x2.py`, `research_rig/run_03.py`, `research_rig/report_01.py`, `research_rig/report_01d.py`, `research_rig/tables_01.py`, `research_rig/tables_01.md`, `research_rig/diag_x2_pbo.py`, `research_rig/build_doc12.py`, `research_rig/build_doc12b.py`, `research_rig/build_doc15.py` | First-run scripts for replays 01 and 03 | RECORD |
| `research_rig/results_01.json`, `research_rig/results_01c.json`, `research_rig/results_01d.json`, `research_rig/results_01x2.json`, `research_rig/results_03.json`, `research_rig/passmarks_01.json`, `research_rig/diag_x2_pbo.json` | First-run outputs | RECORD |
| `research_rig/pilot/`, `research_rig/score_02.py`, `research_rig/results_02.json`, `research_rig/build_doc14.py` | Pilot 02: the server that released one day at a time, every answer the models gave, and the scoring | CURRENT |
| `research_rig/check_data.py`, `research_rig/fetch.py`, `research_rig/fetch_kraken_archive.py`, `research_rig/fetch_french.py`, `research_rig/build_kraken_daily.py`, `research_rig/kraken_daily_build.json` | Say which raw data is present, and download and prepare public price history into `research_rig/data/`, a local folder that git ignores. The table of data sets is in `research_rig/README.md` | CURRENT |
| `research_rig/books_summary.py`, `research_rig/books_summary.json`, `research_rig/build_doc24.py` | Order-book cost samples | CURRENT |
| `research_rig/feeds/` | Collector of public context readings, its source notes and a trimmed sample | CURRENT |
| `research_rig/export_dashboard.py` | Builds the data file for the owner's screen | CURRENT |

## dashboard/ (the owner's screen)

| Folder | What it is | State |
|---|---|---|
| `dashboard/` | A single page that shows the tests, the trades inside them and what waits on the owner. Its data file is built by `research_rig/export_dashboard.py` and is not stored in the repo. `dashboard/README.md` says how to run it | CURRENT |

## Keeping this page true

- A commit that adds, moves or retires a file changes this page in the same commit.
- A commit that changes a result or a decision changes `docs/STATUS.md` in the same commit.
- Retire a file by changing its State to RECORD and naming what replaces it. Do not delete results.
- Run `python3 tools/check_repo.py` before every commit.
