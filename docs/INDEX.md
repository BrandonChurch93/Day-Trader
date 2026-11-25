# Index of every file

What this page is: the map of the repository. Every tracked file has its path in the first column of a table on this page, or sits under a folder that has its own row there with a trailing slash. `tools/check_repo.py` fails if that stops being true. A new file needs its own row unless it sits under a folder that has one. A folder named in passing, outside the first column, does not cover it.

Read `AGENTS.md` first, then `docs/STATUS.md` for current results and `docs/QUEUE.md` for what's next.

## How to use this page

- Find your task in the first table and read only the files it names.
- The State column says whether a file has been replaced. It does not say whether the owner has approved it or whether a result in it is proven. Many CURRENT files are proposals, first looks or dated audits, and each says so in its own text. Standing owner decisions are recorded in `docs/DECISIONS.md`.
- Terms, test names and rule names are defined in `docs/GLOSSARY.md`.
- `tools/check_repo.py` checks that every tracked file is listed here and that the paths and config keys named in the map files, playbook and research pages exist. It does not check paths in `archive/`, the raw reports or the plans in `research_rig/`. It does not check that a file's State is right or that a claim is true.

| State | Meaning |
|---|---|
| CURRENT | Not replaced by a later file. Use it, and read its own labels: CURRENT does not mean approved or proven |
| RECORD | Kept as history. A later file corrects or replaces part of it. The row says which |
| DRAFT | Not agreed and not in force |
| RAW | Working papers behind a CURRENT file. Open only to trace one claim to its source |

## Start from your task

| If you are about to | Read, in this order |
|---|---|
| Do anything at all | `AGENTS.md`, then `docs/STATUS.md` and `docs/QUEUE.md` |
| Understand a term, a test name or a rule name | `docs/GLOSSARY.md` |
| Work on the practice trader, or read what it did | `practice/README.md`, then `practice/PLAN_02_ai_desk.md` |
| Talk to the owner or hand work to him | `AGENTS.md`, "Writing to the owner" and "What comes from the owner" |
| Plan, build or review anything | `AGENTS.md`, "How the work goes", and `docs/QUEUE.md` |
| Use or change a number | `config/thresholds.yaml` and `AGENTS.md`, "Honest testing" and "What comes from the owner" |
| Confirm a stored result or plan a new attempt | `research_rig/README.md`, "How each stored output was made", and `AGENTS.md`, "Honest testing". Check stored output with `python3 tools/check_repo.py --builders` |
| Add a new test on past prices | `research_rig/README.md`, then `research_rig/TRIAL_LEDGER.md`. `docs/research/16_rig_audit.md` for what the audits changed in the rig |
| Judge whether a trading idea is worth testing | `docs/research/25_what_the_evidence_supports.md`, then the playbook page for that market |
| Choose a broker, a venue or a data source | `docs/playbook/04_brokers_data_rules.md`, `docs/research/09_brokers_and_venues.md`, `docs/research/10_historical_data_and_practice.md` |
| Put an AI model anywhere near a trading decision | `AGENTS.md`, "How a trader behaves" and "Honest testing", then `practice/traders/ROSTER.md` |
| Design the product | `AGENTS.md`, `docs/QUEUE.md`, then `docs/playbook/06_architecture_and_build.md` for background |
| Reopen something already settled | `docs/DECISIONS.md` for standing owner decisions, `docs/QUEUE.md` for test priorities |
| Record something the owner decided | `docs/DECISIONS.md` |

## Top level

| File | What it is | State |
|---|---|---|
| `AGENTS.md` | The rules every agent follows. It wins over everything else. Changing it needs the owner | CURRENT |
| `README.md` | Front page. Points here and to the status page | CURRENT |
| `.gitignore` | Keeps price files, logs and private data out of the repo | CURRENT |
| `config/thresholds.yaml` | Every threshold and every owner number, once. Documents name the key and never repeat the value | CURRENT |
| `tools/check_repo.py` | Checks this index, paths named in the map, playbook and research pages, config keys named in documents, the results table in the status page, the coverage tables in `docs/research/10_historical_data_and_practice.md`, and stored outputs against `research_rig/provenance.json`. With `--builders` it also runs the document builders and fails if a built page changes | CURRENT |
| `tools/status_table.py` | Writes the results table in `docs/STATUS.md` from the output files | CURRENT |
| `tools/bars_coverage.py` | With `--write`, writes the coverage tables in `docs/research/10_historical_data_and_practice.md` from `research_rig/platform_bars_coverage.json` and `research_rig/platform_bars_crosscheck.json`, so no figure there is typed. With `--summarise`, on a machine that has the price files, rebuilds the first of those two files from the gap check's output | CURRENT |

## docs/

| File | What it is | State |
|---|---|---|
| `docs/STATUS.md` | Where the project stands today: what was tested, what passed, what waits on the owner, what is next | CURRENT |
| `docs/INDEX.md` | This page | CURRENT |
| `docs/GLOSSARY.md` | Plain definitions of the terms, test names and rule names used in the repo | CURRENT |
| `docs/DECISIONS.md` | The owner's standing decisions in his words, with dates | CURRENT |
| `docs/QUEUE.md` | What is running, what to test next, and what finished | CURRENT |

## archive/ (historical records)

`archive/` is history only, not in force. The current rules are in `AGENTS.md`.

| File or folder | What it is | State |
|---|---|---|
| `archive/README.md` | What is kept here and where the current rules and decisions are | RECORD |
| `archive/quality/` | Old quality and build instructions | RECORD |
| `archive/audit/` | Independent code audits and the auditors' scripts | RECORD |
| `archive/decisions/` | Dated decisions, source checks, and the frozen morning list | RECORD |
| `archive/practice_PLAN_01_two_rules_observation.md` | The first practice plan, two fixed rules and no AI traders. Replaced by `practice/PLAN_02_ai_desk.md` | RECORD |

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
| `docs/research/26_insider_buying_evidence.md` | What the evidence says about buying after insiders buy: the 2012 paper, later samples, funds that tried it, the data a test needs. Reading only, no test | CURRENT |
| `docs/research/27_replay_07_intraday_spy_qqq.md` | Results for eight day trading rules on SPY and QQQ one-minute bars, with break-even costs | CURRENT |
| `docs/research/28_replay_09_crypto_methods.md` | Results for new crypto timing, ranking, lead and risk rules on Alpaca | CURRENT |
| `docs/research/29_time_machine_tm01_crypto_price_only.md` | Results so far for six AI models trading crypto from prices alone in the time machine, with why each trade was made. Rebuilt as sessions finish | CURRENT |
| `docs/research/30_time_machine_tm02_crypto_with_news.md` | Results so far for the same six AI models with dated headlines added, the "did the news help" table, and the headlines each buy named | CURRENT |
| `docs/research/31_model_knowledge_lines.md` | Where each model's memory of crypto prices stops, measured with one dated question, so the replay months can be read with that in mind | CURRENT |
| `docs/research/32_exit_replay.md` | Exit replay (TMX1) of logged TM01 and TM02 AI and random-twin crypto buys under five fixed exit templates (A to E), written by `timemachine/exit_replay.py` | CURRENT |
| `docs/research/33_ideas_round_2_and_3_checked.md` | Checked public AI trading results, twelve candidate ideas, and four published designs. Reading only, no test | CURRENT |
| `docs/research/34_time_machine_tm03_bitcoin_dial.md` | Final results for plan TM03: six AI models set how much bitcoin to hold once a day, against holding and their own shuffled stretches. Written wholly by `timemachine/score_tm03.py` | CURRENT |
| `docs/research/36_time_machine_tm04_stock_basket.md` | Results so far for plan TM04: six AI models name eight of 38 stocks to hold once a week, two runs each, against random baskets, with an after-the-fact, not-judged look at what they added and dropped. Written wholly by `timemachine/score_tm04.py` | CURRENT |
| `docs/research/35_replay_06_fund_trend.md` | Replay 06 results on Alpaca daily fund bars, with yardsticks, costs, pass marks and timing controls | CURRENT |
| `docs/research/37_tm03_plain_dials.md` | Plain fixed dials (A to E and hindsight F) run through `timemachine/weights.py` against the completed TM03 AI models, written wholly by `timemachine/dial_rules_tm03.py --write` | CURRENT |
| `docs/research/39_leverage_replay_tm03.md` | The stored TM03 bitcoin dials, holding and dials B and C replayed at 2x, 3x and 5x with financing and forced close-outs. Looked at after the fact, not a counted trial. Written wholly by `timemachine/leverage_replay_tm03.py` | CURRENT |
| `docs/research/40_leverage_venues_checked.md` | Where a US account in Idaho can trade crypto with leverage: eleven venues with product, order API, practice API, coins, most leverage, fee per side and what is still unknown, each claim checked against the venue's own pages | CURRENT |
| `docs/research/41_fast_lane_evidence_checked.md` | Checked reading on short holds in small coins with leverage: price patterns after costs, futures funding and basis, how leveraged retail accounts fare, six proposed tests and the verdict on each. Reading only, no test | CURRENT |
| `docs/research/42_small_coins_measured.md` | Every USD coin pair on Alpaca measured for trading activity, daily range and half-spread, set beside Coinbase; which coins a small account could fill, and what the flat spread in TM01 and TM02 left out | CURRENT |
| `docs/research/38_ideas_round_4_checked.md` | Checked avoid signals, risk controls, four proposed tests, and five AI fund filings. Reading only, no test | CURRENT |

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
| `docs/research/24_order_book_costs.md` | What it cost to trade small sizes on two venues, sampled on 2026-11-25 | CURRENT |

Working papers.

| Folder | What it is | State |
|---|---|---|
| `docs/research/09_raw/` | Agent reports and claim checks behind document 09. `docs/research/09_raw/orderbook_sampler.py` and `docs/research/09_raw/orderbook_snapshots.jsonl` are an earlier, separate sample. They are not the overnight sample behind `docs/research/24_order_book_costs.md` | RAW |
| `docs/research/10_raw/` | Behind document 10 | RAW |
| `docs/research/11_raw/` | Behind document 11 | RAW |
| `docs/research/13_raw/` | Behind document 13 | RAW |
| `docs/research/17_21_checklogs/` | Second-model check logs for documents 17 to 21 | RAW |

## research_rig/ (the test rig, not the product)

`research_rig/README.md` is the map of this folder: which engine version to use, and for each test its plan, script, output and document.

| Files | What they are | State |
|---|---|---|
| `research_rig/README.md` | Map of the folder and how to add a test | CURRENT |
| `research_rig/TRIAL_LEDGER.md` | Count of every rule variant tried, and of every rerun. Its Status column is the record of what was written at the time; current verdicts are in `docs/STATUS.md` | CURRENT |
| `research_rig/ledger_count_check.py`, `research_rig/ledger_count_check.json` | Works out pass mark 3 again from the stored outputs with the two reruns counted as trials. Runs no rule | CURRENT |
| `research_rig/provenance.py`, `research_rig/provenance.json` | The record of how each stored output was made: command, code files, commits, its fingerprint and the fingerprint of each raw input file. Built after the runs. `python3 provenance.py` checks the repo against it and writes nothing | CURRENT |
| `research_rig/requirements.txt` | The Python package versions the stored outputs were made with | CURRENT |
| `research_rig/rig2.py`, `research_rig/fixtures2.py`, `research_rig/basket.py`, `research_rig/fixtures_basket.py` | Engine v2 and its checks | CURRENT |
| `research_rig/rules.py`, `research_rig/common_03.py` | Rule definitions used by both engine versions | CURRENT |
| `research_rig/engine.py`, `research_rig/fixtures.py`, `research_rig/common_01.py` | Engine v1 | RECORD. Use v2 |
| `research_rig/PREREG_01_daily_crypto_trend.md`, `research_rig/PREREG_01_S1_fill_delay.md`, `research_rig/PREREG_01_X2_kraken_full_history.md`, `research_rig/PREREG_02_ai_calls_pilot.md`, `research_rig/PREREG_03_intraday_crypto.md`, `research_rig/PREREG_04_coin_basket_trend.md`, `research_rig/PREREG_05_stock_trend_free_data.md` | Plans written before each test. Not edited after the run | CURRENT |
| `research_rig/AMENDMENT_2026-11-25_audit_fixes.md` | The audit fixes, written before the rerun | CURRENT |
| `research_rig/PREREG_06_fund_trend_paid_data.md` | Frozen plan for slow trend rules on nine funds, Alpaca daily bars. Ledger rows 115 to 120 | CURRENT |
| `research_rig/audit_06_fund_coverage.py`, `research_rig/fund_coverage_06.json` | NYSE dates and counts for the Alpaca daily fund bars. No prices or rule returns | CURRENT |
| `research_rig/audit_06_fund_adjustments.py`, `research_rig/fund_adjustments_06.json` | Adjustment checks against issuer returns, and a power sketch for replay 06. No rule returns | CURRENT |
| `research_rig/run_06.py`, `research_rig/fixtures_06.py` | Fund replay runner with freeze and holdout guards, and invented-price tests. Held slice already used once; do not rerun on real data | CURRENT |
| `research_rig/results_06.json` | Replay 06 results for both slices, with frozen thresholds and run-time input fingerprints | CURRENT |
| `research_rig/report_06.py` | Writes or checks the Replay 06 page from stored summaries; reads no market bars | CURRENT |
| `research_rig/PREREG_07_intraday_spy_qqq.md` | Frozen plan for replay 07, day trading rules on SPY and QQQ one-minute bars. Ledger rows 56 to 71 | CURRENT |
| `research_rig/run_07.py`, `research_rig/results_07.json`, `research_rig/build_doc27.py` | Replay 07: script with its checks, output from the one held-back run, and the builder of document 27 | CURRENT |
| `research_rig/PREREG_08_insider_buying_DRAFT.md` | Plan for a test of buying after insiders buy. Runs nothing. Waits on decision 11, decisions 1a and 1b, prices that include dead stocks, and the owner's yes to reading SEC filing lists | DRAFT |
| `research_rig/PREREG_11_earnings_release_reader.md` | Frozen plan for an AI that reads each earnings release and says buy or skip for the next open: 4,285 releases from large, mid and small companies, six set-ups, two holds, pass marks and costs fixed before any reader ran. Ledger rows 121 to 134. Queue row 9b | CURRENT |
| `research_rig/fetch_11_edgar.py` | Collects the item 2.02 8-K filings and press release texts for plan 11 from SEC EDGAR. Reads no price | CURRENT |
| `research_rig/build_prereg_11.py` | Writes the plan 11 file from its summary files and config. Reads no price | CURRENT |
| `research_rig/common_11.py` | Plan 11 shared paths, calendar, event ids and the price-file map for renamed tickers | CURRENT |
| `research_rig/prep_11.py` | Plan 11: filters and splits the events, draws the design sample, builds prompts and reader folders. Reads no price after a filing | CURRENT |
| `research_rig/reader_instruction_11.txt` | Plan 11: the exact instruction every reader sees | CURRENT |
| `research_rig/READER_BRIEF_11.md` | Plan 11: the message the lead pastes to spawn one reader helper, and the no-tools gap | CURRENT |
| `research_rig/check_11_answers.py` | Plan 11: checks a reader's answers file and collects a phase's answers with their hashes | CURRENT |
| `research_rig/score_11.py` | Plan 11 scorer. Refuses unless the answer hashes are pushed; --heldback runs once | CURRENT |
| `research_rig/test_11.py` | Plan 11 tests on made-up events, texts and prices | CURRENT |
| `research_rig/extract_check_11.py` | Plan 11 extraction check: extracted texts against the raw filings | CURRENT |
| `research_rig/EXTRACTION_CHECK_11.md` | Plan 11 extraction check, reading notes on 20 texts | RECORD |
| `research_rig/events_11_summary.json` | Plan 11 event, text, coverage and size counts, written by prep_11.py summary | RECORD |
| `research_rig/extraction_check_11.json` | Plan 11 extraction check counts, written by extract_check_11.py | RECORD |
| `research_rig/split_check_11.py` | Plan 11 split check: are the daily price files split-adjusted | CURRENT |
| `research_rig/split_check_11.json` | Plan 11 split check result, written by split_check_11.py | RECORD |
| `research_rig/answers_11_design_hashes.json` | Plan 11: the hash of each reader's collected answers on the design sample, pushed before the scorer may run | RECORD |
| `research_rig/PREREG_09_crypto_methods.md` | Frozen plan for new long-only crypto rules at Alpaca cost | CURRENT |
| `research_rig/run_09.py`, `research_rig/fixtures_09.py` | Replay engine and synthetic timing, fees, gaps and matching checks for replay 09 | CURRENT |
| `research_rig/fetch_09_alpaca.py` | Public Alpaca USD bar downloader; raw bars live on the research machine | CURRENT |
| `research_rig/audit_09_alpaca.py` | Data-only gap check of the later full-hourly pulls for steady-volume USD pairs | CURRENT |
| `research_rig/alpaca_coverage_09.json` | Full-hourly coverage and comparison with the original replay inputs; no rule rerun | CURRENT |
| `research_rig/build_doc28.py` | Writes the replay 09 report from stored results, without replaying any price | CURRENT |
| `research_rig/results_09.json` | Replay 09 results, input fingerprints and coverage snapshot | CURRENT |
| `research_rig/PREREG_10_negative_funding.md` | Fixed plan for a spot rule using negative perpetual funding. Not run: too few events in the design years | RECORD |
| `research_rig/count_10_design.py`, `research_rig/design_counts_10.json` | Funding coverage audit and design-only entry counts for replay 10. No price returns or held-back signals | CURRENT |
| `research_rig/run_v2.py`, `research_rig/compare_v1_v2.py`, `research_rig/noise_pbo.py`, `research_rig/build_doc16.py`, `research_rig/results_v2.json`, `research_rig/compare_v1_v2.json`, `research_rig/noise_pbo.json`, `research_rig/venue_price_gap.json` | The rerun after the audits and its outputs | CURRENT |
| `research_rig/run_04.py`, `research_rig/results_04.json`, `research_rig/build_doc23.py`, `research_rig/NOTES_04_builder.md` | Replay 04 | CURRENT |
| `research_rig/run_05.py`, `research_rig/AMENDMENT_05_I2_equal_thirds.md`, `research_rig/results_05.json`, `research_rig/results_05b.json`, `research_rig/build_doc22.py`, `research_rig/i2_2020_note.py`, `research_rig/i2_2020_note.json`, `research_rig/data_notes_french.md` | Replay 05: script, the correction to rule I2, first-run output, corrected-run output | CURRENT |
| `research_rig/run_01.py`, `research_rig/run_01b.py`, `research_rig/run_01c.py`, `research_rig/run_01x2.py`, `research_rig/run_03.py`, `research_rig/report_01.py`, `research_rig/report_01d.py`, `research_rig/tables_01.py`, `research_rig/tables_01.md`, `research_rig/diag_x2_pbo.py`, `research_rig/build_doc12.py`, `research_rig/build_doc12b.py`, `research_rig/build_doc15.py` | First-run scripts for replays 01 and 03 | RECORD |
| `research_rig/results_01.json`, `research_rig/results_01c.json`, `research_rig/results_01d.json`, `research_rig/results_01x2.json`, `research_rig/results_03.json`, `research_rig/passmarks_01.json`, `research_rig/diag_x2_pbo.json` | First-run outputs | RECORD |
| `research_rig/pilot/`, `research_rig/score_02.py`, `research_rig/results_02.json`, `research_rig/build_doc14.py` | Pilot 02: the server that released one day at a time, every answer the models gave, and the scoring | CURRENT |
| `research_rig/check_data.py`, `research_rig/fetch.py`, `research_rig/fetch_kraken_archive.py`, `research_rig/fetch_french.py`, `research_rig/build_kraken_daily.py`, `research_rig/kraken_daily_build.json` | Say which raw data is present, and download and prepare public price history into `research_rig/data/`, a local folder that git ignores. The table of data sets is in `research_rig/README.md` | CURRENT |
| `research_rig/books_summary.py`, `research_rig/books_summary.json`, `research_rig/build_doc24.py` | Order-book cost samples | CURRENT |
| `research_rig/platform_bars_crosscheck.py` | Compares each day's open, high, low and close rebuilt from the one-minute files with the daily file, for SPY and QQQ, from the same lookup. Gaps in basis points only. No rule and no return | CURRENT |
| `research_rig/platform_bars_consolidate.py`, `research_rig/platform_bars_integrity.py`, `research_rig/platform_bars_coverage.json`, `research_rig/platform_bars_crosscheck.json` | How the stock prices collected through the workspace's own price lookup were joined, checked for gaps and compared with each other (one-minute files against daily files), and the dates and counts those checks gave. No price is in the repo and no rule was run. Whether the files may be kept is item 6 of the morning list | CURRENT |
| `research_rig/feeds/` | Collector of public context readings, its source notes and a trimmed sample | CURRENT |
| `research_rig/export_dashboard.py` | Builds the data file for the owner's screen | CURRENT |

## practice/ (the practice desk: pretend money, live prices)

| File | What it is | State |
|---|---|---|
| `practice/README.md` | Start here for the practice desk: what it is, the files, how to work on it, where its records are | CURRENT |
| `practice/PLAN_02_ai_desk.md` | The plan in force: how a decision becomes an order, what is written down, when a trader stops, what the desk cannot do yet, what would count | CURRENT |
| `practice/trader.py` | The program that places orders for every trader, keeps each inside its pretend budget, enforces exits and writes the records | CURRENT |
| `practice/picks.py` | The form an AI trader's pick must take, and the check that it does | CURRENT |
| `practice/books.py` | Works out each trader's cash, holdings, closed trades, wins and losses from the broker's order list | CURRENT |
| `practice/broker.py`, `practice/market.py` | The only code that talks to the broker (practice address only, a short fixed list of actions), and the price reads | CURRENT |
| `practice/rules.py` | The two fixed rules on the desk | CURRENT |
| `practice/traders.json` | The traders on the desk now | CURRENT |
| `practice/traders/` | `practice/traders/ROSTER.md` and one method card for each AI trader, A01 to A09, B01, B02, C01, C02, D01 and D02, the draft D03, and F01, the owner's own method written down for testing | CURRENT |
| `practice/test_trader.py`, `practice/test_review.py`, `practice/test_market.py` | Checks with a pretend broker and no network. The timer runs them before every real run | CURRENT |
| `.github/workflows/practice-trader.yml` | The timer: runs the checks, then the desk, and saves the records to the `practice-records` branch | CURRENT |

## timemachine/ (the time machine: pretend money, past days)

| File | What it is | State |
|---|---|---|
| `timemachine/README.md` | Start here: what it is, how to start a session, how a trader steps through it | CURRENT |
| `timemachine/TRADER_BRIEF.md` | What an AI trader is told at the start of a replay | CURRENT |
| `timemachine/tape.py`, `timemachine/record.py` | The store of recorded past prices and news, with reads that never return anything dated after the pretend now, and the recorder that fills it | CURRENT |
| `timemachine/attention.py`, `timemachine/test_attention.py` | Read-only attention counts filtered by simulated time and evidence of availability; invented data checks | CURRENT |
| `timemachine/simdata.py`, `timemachine/simbroker.py` | Stand-ins for the price reads and the broker, so the practice desk's own order program runs unchanged on past days | CURRENT |
| `timemachine/session.py`, `timemachine/server.py`, `timemachine/new_session.py` | One replay session, the local server a trader steps through, and the command that starts a session | CURRENT |
| `timemachine/weights.py`, `timemachine/score_weights.py` | Weights sessions: the trader sets what share of the book to hold in each symbol at each wake. The session and book, and the scorer with its shuffle, random basket and hold twins | CURRENT |
| `timemachine/TRADER_BRIEF_WEIGHTS.md` | What an AI trader is told at the start of a weights session | CURRENT |
| `timemachine/perp.py` | Perp mode for weights sessions (instrument perp): signed weights up to max_gross, hourly or 8 hour funding from stored files, per-symbol fee and half spread, maintenance and close-out on the minute low or high, stops and targets, wakes from 15 minutes to daily. Its scorer replays the session to the cent, then scores the same answers at each fee in `tm_perp_fee_levels_bps` with the random sign twin, the signs flipped yardstick and long and short holds | CURRENT |
| `timemachine/code_traders.py`, `timemachine/run_code_trader.py` | Traders that need no model (hold, random, the fixed rules, the perp rules perp_hold and bar_trend), and the command that runs one through a session. Its `rule` subcommand runs any Python function of the packet through a weights or perp session at full speed | CURRENT |
| `timemachine/PLAN_TM01_crypto_price_only.md` | Plan for the first AI replays: six models, one card, crypto prices only, with the pass mark fixed before any session | CURRENT |
| `timemachine/PLAN_TM02_crypto_with_news.md` | Plan for the second AI replays: the same six models and months with dated crypto headlines added, and the test for whether the news helped | CURRENT |
| `timemachine/PLAN_TM03_bitcoin_dial.md` | Plan for the third AI replays: each model sets once a day how much bitcoin to hold, starting fully invested. Marks fixed before any session | CURRENT |
| `timemachine/PLAN_TM04_stock_basket.md` | Plan for the fourth AI replays: each model names once a week eight of 38 stocks to hold. Marks fixed before any session | CURRENT |
| `timemachine/PLAN_TM05_avoid_list_DRAFT.md` | DRAFT plan for the fifth AI replays: each model names once a week up to `tm05_plan.leave_out_max` of the 38 stocks to leave out, judged against random leave-outs on April to May 2026 and a forward stretch not yet recorded. Not fixed, not run; needs tool changes | DRAFT |
| `timemachine/score_tm01.py`, `timemachine/results_tm01.json` | Scores plan TM01 from the finished sessions: each model against holding bitcoin and its random twins, and a "why" row for every buy. The JSON is its stored output | CURRENT |
| `timemachine/results_tm02.json` | Stored scores of plan TM02, written by `timemachine/score_tm01.py --plan TM02` | CURRENT |
| `timemachine/score_tm03.py`, `timemachine/results_tm03.json` | Scores plan TM03 from the finished sessions with the weights scorer: each model's months against holding and its shuffled stretches, the plan's two lines, and the gain by stated driver. The JSON is its stored output | CURRENT |
| `timemachine/score_tm04.py`, `timemachine/results_tm04.json` | Scores plan TM04 from the finished sessions with the weights scorer: each run against equal-weight hold and random baskets, run 1 against run 2, the method count, and the adds and drops against random swaps (not judged) | CURRENT |
| `timemachine/leverage_replay_tm03.py`, `timemachine/leverage_replay_tm03.json` | Replays every finished TM03 session's answers at the multiples in `tm_lev_replay_multiples` through the weights book with leverage; 1x must match each session to the cent | CURRENT |
| `timemachine/dial_rules_tm03.py`, `timemachine/dial_rules_tm03.json` | Runs fixed dials A to E and hindsight dial F through `timemachine/weights.py` against the completed TM03 models, writes `docs/research/37_tm03_plain_dials.md` (`--write`), checks freshness (`--check`), and tests made-up prices (`--test`). The JSON is its stored output | CURRENT |
| `timemachine/PLAN_TMX1_exit_replay.md` | Plan for exit replay TMX1: five fixed exit templates on logged AI and random-twin crypto buys, with marks fixed before running | CURRENT |
| `timemachine/exit_replay.py`, `timemachine/results_tmx1.json` | Replays logged TM01/TM02 AI and twin buys under templates A to E on 1Min tape bars and writes `docs/research/32_exit_replay.md`. The JSON is its stored output | CURRENT |
| `timemachine/check_news_dates.py`, `timemachine/news_date_check.json` | Checks the news sites for stories dated earlier than they were made, and the stored counts | CURRENT |
| `timemachine/knowledge_line.py`, `timemachine/knowledge_lines.json` | The memory test of the models: the question, the scoring against the tape, and the stored answers and hit marks | CURRENT |
| `timemachine/SESSIONS.jsonl` | One line for every session ever started, so no replay goes uncounted | CURRENT |
| `timemachine/test_tape.py`, `timemachine/test_sim.py`, `timemachine/__init__.py` | Checks with no network, and the package marker | CURRENT |

## dashboard/ (the owner's screen)

| Folder | What it is | State |
|---|---|---|
| `dashboard/` | A single page that shows the tests, the trades inside them and what waits on the owner. Its data file is built by `research_rig/export_dashboard.py` and is not stored in the repo. `dashboard/README.md` says how to run it | CURRENT |

## Keeping this page true

- A commit that adds, moves or retires a file changes this page in the same commit.
- A commit that changes a result or a decision changes `docs/STATUS.md` in the same commit.
- Retire a file by changing its State to RECORD and naming what replaces it. Do not delete results.
- Run `python3 tools/check_repo.py` before every commit.
