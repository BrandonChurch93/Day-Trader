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
| `tools/status_table.py` | Writes the results table in `docs/STATUS.md` from output files and the generated Replay 24 result page | CURRENT |
| `tools/report_saved_25.py` | Renders the Replay 25 result page from the pinned saved aggregate JSON. Does not open market inputs or score | CURRENT |
| `tools/report_saved_31.py` | Renders the Replay 31 result page from one pinned saved aggregate JSON. Does not open market inputs or score | CURRENT |
| `tools/report_saved_35.py` | Renders the Replay 35 result page and summary lines from one pinned saved aggregate. Does not open market inputs or score | CURRENT |
| `tools/report_saved_23.py` | Renders the Replay 23 result page from the pinned saved run outputs (off repo). Does not open bars or score | CURRENT |
| `tools/report_saved_20.py` | Renders the Replay 20 result page from the pinned saved aggregate JSON. Does not open market inputs or score | CURRENT |
| `tools/report_saved_tm06r.py` | Renders the TM06-R result page from the three pinned picker result files and the shown-items file (off repo). Does not open prices or score | CURRENT |
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
| `docs/research/43_crypto_events_evidence_checked.md` | Checked reading on dated crypto events (listings, unlocks, governance votes, hacks, attention, sector moves): 14 claims confirmed, 6 wrong, 1 not found, and the builder's call on each of five proposed tests | CURRENT |
| `docs/research/44_replay_11_earnings_reader.md` | Replay 11: an AI reads each earnings press release and says buy or skip. Design-sample table for six set-ups, reader agreement, the set-up chosen, and what is still to come. Held-back verdict is added when scored | CURRENT |
| `docs/research/45_attention_feed_measured.md` | Which free attention counts per coin can be collected with honest dates (Wikipedia yes, Reddit partly, news counts and Trends no) and an after-the-fact look showing attention rises did not lead price | CURRENT |
| `docs/research/46_becker_calls_measured.md` | 1,855 dated buy or hold mentions from Alex Becker's videos (2020 to 2025) set against prices before and after, other callers' records, what happened to AI and gaming coins after hot stretches, and free dated data for "what was hot" | CURRENT |
| `docs/research/47_replay_12_congress_followers.md` | Replay 12: following stock purchases disclosed by members of Congress. Data in hand and counts now; design and held-back results are added when scored | CURRENT |
| `docs/research/48_congress_trades_evidence.md` | Following members of Congress: the collected record of 85,291 dated trades and how it was checked, what the two real-money copy funds did against SPY, the published studies, the Pelosi figures and where they come from, and pending rule changes | CURRENT |
| `docs/research/49_governance_votes_look.md` | A first look at coin returns around governance votes: 945 votes, nearly all on one coin, nothing after costs; parked | CURRENT |
| `docs/research/50_public_filers_evidence_checked.md` | Copying other public filers after the public date (fund holdings, large-stake filings, ARK, short sellers, lobbying and contracts, analysts) and drift after earnings: the reading with every source checked, and what it changes in the queue | CURRENT |
| `docs/research/51_stock_swing_evidence_checked.md` | Buy-only methods for single stocks held weeks to months: the reading with every source checked, and eight real-money funds measured against SPY from our own feed | CURRENT |
| `docs/research/53_prediction_markets_checked.md` | Prediction markets (Kalshi, Polymarket US, Interactive Brokers): fees, free history, AI forecasters against market prices, who makes money, what can be tested honestly; every source checked | CURRENT |
| `docs/research/52_replay_14_large_stock_momentum.md` | Replay 14: plain 12-month momentum on S&P 500 members by date, top 10 and top 50, 2017 to 2026. Did not pass: behind SPY, above every member in equal parts, not above the 95th percentile of random baskets. Written by script from the one run | CURRENT |
| `docs/research/54_replay_13_year_or_method.md` | Replay 13: the owner's dip-and-peak method as a fixed rule on the hottest coins, each year 2020 to 2026. The dip rule was not paid, 2021 included; holding the hot five met its marks and still lost money in three years | CURRENT |
| `docs/research/55_stocks_in_play_evidence_checked.md` | Day trading stocks in play: the published opening-range rule, rebuilds that lose once real fills are charged, other single-stock day rules after costs, and what real day traders made. Checked reading, nothing measured by us | CURRENT |
| `docs/research/56_replay_16_hot_five_hedged.md` | Replay 16: the hot five on spot against a same-size futures short, weekly, 2020 to 2026, coins ranked 51 to 100. Not supported, 0 of 4 marks. Written by script from the one run | CURRENT |
| `docs/research/57_replay_17_short_the_peak.md` | Replay 17: the short side of the owner's method as a fixed rule on futures, year by year. Not supported, 0 of 3 marks, with or without costs; US fee levels and the US-shortable list shown beside it. Written by script from the one run | CURRENT |
| `docs/research/58_crowded_trades_evidence_checked.md` | Shorting crowded coin futures and buying the bounce after a flush: what Binance's public archive holds, the published and public tests after costs (most lose once dead coins are kept), and which coins a US account can short today. Checked reading, nothing measured on our own prices | CURRENT |
| `docs/research/61_look_after_the_peak_signal.md` | Ledger 152 look at what happened after the Plan 17 entry signal on the viewed list, with matched random hours. No pass mark | CURRENT |
| `docs/research/59_why_the_ai_traders_lost.md` | Why the AI traders lost: every written reason in plans TM01 to TM04 sorted into fixed categories and joined to what happened next (entries, stops, costs, bitcoin dial moves, stock picks), with 12 quotes and record faults. After the fact, not a test. Written from `timemachine/autopsy/autopsy_results.json` | CURRENT |
| `docs/research/60_us_venue_costs_checked.md` | What a small US account pays to go long or short crypto: venue fees, checked coin lists, and worked costs with limits | CURRENT |
| `docs/research/62_round_7_outside_evidence.md` | Checked outside evidence on AI crypto traders, funding and basis, trading hours, and token unlocks. Reading only, no test | CURRENT |
| `docs/research/63_round_8_outside_evidence.md` | Checked outside evidence on eight dated-event ideas. Keeps the fast-track IPO test and small-lot tender audit; reading only, no test | CURRENT |
| `docs/research/64_replay_19_monday_asia.md` | Monday Asia stand-in on viewed dates. Run once, did not pass, one of five marks | CURRENT |
| `docs/research/65_replay_18_funding_carry.md` | Funding carry on the reconstructed ranked subset. Did not pass, one of three marks; four US rosters shown only | CURRENT |
| `docs/research/66_measure_15_breakout_fills.md` | Measurement 15: what a breakout order on stocks in play really paid. Entry plus stop-exit slippage 0.2089 of the stop distance against a limit of 0.05; idea dropped | CURRENT |
| `docs/research/67_round_9_outside_evidence.md` | Checked outside evidence on dated and forced flows, with two test candidates, a broker and issuer audit, and a fill calibration | CURRENT |
| `docs/research/68_replay_24_same_coin_carry.md` | Same-coin funding carry on viewed dates. Run once, did not pass, one of five marks | CURRENT |
| `docs/research/69_replay_25_treasury_month_end.md` | Treasury ETF month-end rule. First counted trading-replay pass, 9 of 9 marks at 2 bps per side, with higher costs and fill limits shown | CURRENT |
| `docs/research/70_measure_27_tlt_closing_cross.md` | Measurement 27: TLT closing cross against the SIP close on Replay 25's 260 sessions. Frozen mark 1 not met (124 of 260 found under exchange Q); where found the cross equalled the SIP close every time. After-run view with Q or T labels shown | CURRENT |
| `docs/research/71_replay_20_upbit_listing_short.md` | Upbit listing short after a red UTC day. Second counted trading-replay pass, 5 of 5 on viewed dates; US availability and concentration limits | CURRENT |
| `docs/research/72_replay_23_ipo_fast_track.md` | Early index buying after large US listings. Run once, did not pass, 7 of 8 marks; worked on paper 2017 to 2021, not since 2022 | CURRENT |
| `docs/research/73_replay_26_blocked_at_source_check.md` | Earlier Treasury month-end replication blocked at the frozen SIP source check. Aggregate discrepancies only; no score and no lock claim | CURRENT |
| `docs/research/74_round_10_forced_flow_ideas.md` | Round 10 forced-flow and known-clock scouting for a $500 US retail account (13 candidates: 2 KEEP, 4 KEEP WITH CHANGES, 7 DROP; top three named) | CURRENT |
| `docs/research/75_reverse_split_round_up_feasibility.md` | Reverse-split round-ups: issuer wording, broker handling, EDGAR counts 2023 to 2026, Trial 60 dollars, risks. Decision: forward log with no money; real one-share check waits on the owner | CURRENT |
| `docs/research/76_round_11_larger_moves.md` | Round 11 larger-per-trade forced-flow and known-clock scouting for a $500 US retail account (15 candidates across US small-stock events, US-reachable crypto events, and levered Replay 25 Treasury ETFs: 2 KEEP, 3 KEEP WITH CHANGES, 10 DROP; top three named) | CURRENT |
| `docs/research/77_round_12_public_document_events.md` | Round 12 timestamped public-document drift scouting for a reading agent on a $500 US retail account (14 candidates: 3 TEST, 2 WATCH, 9 DROP; top three named: Form 4 cluster buys, DoD daily 5 p.m. contract awards, going-private 13E-3 first filings) | CURRENT |
| `docs/research/78_time_machine_tm06r_fable_repeat.md` | TM06-R: the Claude Fable 5.2 picker repeated twice on the same eight months. Mixed: one repeat cleared both marks, one did not. Generated by `tools/report_saved_tm06r.py` | CURRENT |
| `docs/research/79_round_13_known_clock_premia.md` | Round 13 known-clock long-only premia for a $500 US account with December and January focus (14 candidates: 2 new queued tests in IWM pre-holiday sessions and late-December tax-loss small-cap rebound, 1 already row 51 blocked on payment-date data, 2 WATCH, 9 DROP) | CURRENT |
| `docs/research/80_replay_31_bond_fund_month_end.md` | Bond fund month-end replay. Plain basket rose; pooled return after Treasury and stock benchmarks was negative, 2 of 10 marks | CURRENT |
| `docs/research/81_replay_35_cme_bitcoin_expiry_ibit.md` | IBIT at monthly CME Bitcoin expiry. Full placement, negative net mean and Friday gap; shorter window, friction and spot checks shown | CURRENT |
| `docs/research/82_measurement_34_tmf_ubt_month_end.md` | Measurement 34 results: leveraged Treasury month-end tracking, spreads, net results and drawdown on the same Replay 25 windows; not a new trial | CURRENT |
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
| `research_rig/report_11.py` | Writes the Replay 11 page (research doc 44) from the stored design and held-back results; reads no price | CURRENT |
| `research_rig/PREREG_07_intraday_spy_qqq.md` | Frozen plan for replay 07, day trading rules on SPY and QQQ one-minute bars. Ledger rows 56 to 71 | CURRENT |
| `research_rig/run_07.py`, `research_rig/results_07.json`, `research_rig/build_doc27.py` | Replay 07: script with its checks, output from the one held-back run, and the builder of document 27 | CURRENT |
| `research_rig/PREREG_08_insider_buying_DRAFT.md` | Plan for a test of buying after insiders buy. Runs nothing. Waits on decision 11, decisions 1a and 1b, prices that include dead stocks, and the owner's yes to reading SEC filing lists | DRAFT |
| `research_rig/PREREG_11_earnings_release_reader.md` | Frozen plan for an AI that reads each earnings release and says buy or skip for the next open: 4,285 releases from large, mid and small companies, six set-ups, two holds, pass marks and costs fixed before any reader ran. Ledger rows 121 to 134. Queue row 9b | CURRENT |
| `research_rig/PREREG_12_congress_followers.md` | Plan for following stock purchases disclosed by members of Congress: bought after the filing, three groups, three holds, design half chooses, held-back half judges once. Frozen 2026-11-25 19:09 UTC | CURRENT |
| `research_rig/fetch_12_prices.py` | Plan 12: collects adjusted daily bars for every ticker in the buy and sell rows plus SPY, QQQ and NANC into the research machine, and writes a counts-only summary | CURRENT |
| `research_rig/prices_12_summary.json` | Plan 12: counts and dates of the collected bars, no price values | CURRENT |
| `research_rig/common_12.py` | Plan 12 shared code: events, entry days, trades, merging, the daily portfolio with turnover cost, the SPY mirror and the bootstrap | CURRENT |
| `research_rig/score_12.py` | Plan 12 scoring: --counts, --selftest, --design once, --heldback once | CURRENT |
| `research_rig/results_12_design.json` | Plan 12: the nine set-ups scored on the design half (filings 2019 to 2022), three entry days each, and the set-up chosen for the held-back half. Written once by score_12.py --design | CURRENT |
| `research_rig/score_12_design.lock` | Plan 12: marks that the design half was scored; a second run is refused | CURRENT |
| `research_rig/results_12_heldback.json` | Plan 12: the chosen set-up scored once on the held-back half (filings from 2023), with the five pass marks. Written once by score_12.py --heldback | CURRENT |
| `research_rig/score_12_heldback.lock` | Plan 12: marks that the held-back half was scored; a second run is refused | CURRENT |
| `research_rig/events_12_summary.json` | Plan 12: event counts, no-bar counts by year and named-member matches, no returns | CURRENT |
| `research_rig/test_12.py` | Plan 12 tests on made-up data, with a planted-edge check and a no-edge check | CURRENT |
| `research_rig/report_12.py` | Writes the Replay 12 page (research doc 47) from the stored summaries and results; reads no price | CURRENT |
| `research_rig/missing_tickers_12.md` | Plan 12: what the tickers with no prices are, and a seeded look at 40 of them | CURRENT |
| `research_rig/renames_12.csv` | Plan 12 rename list, frozen with the plan: old ticker, new ticker, date, public source and status (mapped, left_out, reuse_seen) | CURRENT |
| `research_rig/noedge_12.py` | Plan 12: runs the block bootstrap mark on 1,000 made-up data sets with no edge and writes the pass rates | CURRENT |
| `research_rig/noedge_12.json` | Plan 12: the measured no-edge pass rates of mark 2 at each hold, quoted by report_12.py | CURRENT |
| `research_rig/PREREG_13_year_or_method.md` | Plan: a fixed dip-and-peak rule on the five hottest coins, scored year by year 2020 to 2026 against all coins, random coins and bitcoin, to tell the method from the year. Frozen 2026-11-25 19:27 UTC | CURRENT |
| `research_rig/common_13.py` | Plan 13 rules: weekly coin list, hot five, hold rule A, dip rule B, yardsticks, flags, the judge | CURRENT |
| `research_rig/fetch_13.py` | Plan 13 data: monthly coin lists and hourly Binance archives, stored outside the repo with a manifest | CURRENT |
| `research_rig/score_13.py` | Plan 13 scorer: --selftest on made-up bars; --run once on the frozen plan, lock first | CURRENT |
| `research_rig/test_13.py` | Plan 13 self-tests on made-up bars, 34 checks | CURRENT |
| `research_rig/results_13.json` | Plan 13 result: each year's figures for both rules and every yardstick at three cost levels, flags, and the finding. Written once by score_13.py --run | CURRENT |
| `research_rig/score_13.lock` | Plan 13: marks that the run was made; a second run is refused | CURRENT |
| `research_rig/report_13.py` | Writes the plan 13 result page from results_13.json; reads no price | CURRENT |
| `research_rig/PREREG_14_large_stock_momentum.md` | Plan: plain 12-month momentum on S&P 500 members by date, top 10 and top 50, monthly, against SPY, all members and random baskets. Frozen 2026-11-25 22:23 UTC, run once 22:39 UTC | CURRENT |
| `research_rig/results_14.json` | Plan 14 result: both set-ups against SPY, every member and random baskets, by half and by year, with flags and input fingerprints. Written once by score_14.py --run | CURRENT |
| `research_rig/score_14.lock` | Plan 14: marks that the run was made; a second run is refused | CURRENT |
| `research_rig/build_members_14.py` | Plan 14 member list: S&P 500 members by date from two public sources, renames listed, written outside the repo | CURRENT |
| `research_rig/fetch_14.py` | Plan 14 data: daily bars one ticker at a time, stored outside the repo, prints counts only | CURRENT |
| `research_rig/common_14.py` | Plan 14 rules: calendar, 12-month ranking, the baskets, the yardsticks and the simulation | CURRENT |
| `research_rig/score_14.py` | Plan 14 scorer: --selftest on made-up prices, --coverage for counts, --run once on the frozen plan with locks first | CURRENT |
| `research_rig/test_14.py` | Plan 14 self-tests on made-up prices, 16 checks, and the no-edge worlds | CURRENT |
| `research_rig/noedge_14.json` | Plan 14: how often each mark passes in made-up worlds with no edge. Made-up data only | CURRENT |
| `research_rig/coverage_14.json` | Plan 14: counts of members, rankable stocks and missing price files by date. No prices | CURRENT |
| `research_rig/report_14.py` | Writes the plan 14 result page from the stored result; reads no price | CURRENT |
| `research_rig/check_adjust_14.py` | Plan 14 check that the vendor's adjusted prices differ from raw by a factor that steps only on listed ex-dates; prints yes or no per company, no return | DRAFT |
| `research_rig/fetch_16.py` | Collects plans 16 and 17 inputs from the Binance bulk archive only (spot, futures and mark bars, funding) with hashes and a coverage count; data stays off the repo | DRAFT |
| `research_rig/common_16.py`, `research_rig/score_16.py`, `research_rig/test_16.py`, `research_rig/report_16.py` | Plan 16 rules, scorer (refuses until plans 16 and 17 are both frozen), self-tests on made-up prices, and the result page writer; not audited yet | DRAFT |
| `research_rig/common_17.py`, `research_rig/score_17.py`, `research_rig/test_17.py`, `research_rig/report_17.py` | Plan 17 rules, scorer (refuses until plans 16 and 17 are both frozen), self-tests on made-up prices, and the result page writer; not audited yet | DRAFT |
| `research_rig/look_17_signal.py`, `research_rig/look_17_signal.json` | Viewed-only ledger 152 signal-look builder and aggregate measurements | CURRENT |
| `research_rig/PREREG_18_funding_carry.md`, `research_rig/PLAN_18_rank_page_coverage.md`, `research_rig/common_18.py`, `research_rig/archive_18.py`, `research_rig/score_18.py`, `research_rig/test_18.py` | Frozen Queue 27 funding carry, rank-page mapping and exclusions, audited-clock proxy and shown US rosters. Sealed one-shot completed by the lead agent | CURRENT |
| `research_rig/results_18.json` | Saved one-shot aggregate return, scope and coverage, comparison books and forced accounting closes | CURRENT |
| `research_rig/report_18.py` | Prints the Replay 18 result page from saved JSON only. No scoring or market-data reads | CURRENT |
| `research_rig/PREREG_19_monday_asia.md`, `research_rig/common_19.py`, `research_rig/score_19.py`, `research_rig/test_19.py` | Frozen Queue 35 Monday Asia trend proxy for BTC and ETH, shifted-hour placebos and synthetic-only tests. Local one-shot complete | CURRENT |
| `research_rig/MEASURE_15_breakout_fills.md` | Frozen measurement for queue 23: what a breakout order on stocks in play really paid on 60 fixed mornings, with the decision rule fixed before any trade or quote was collected. Not a trial | CURRENT |
| `research_rig/MEASURE_27_tlt_closing_cross.md` | Frozen measurement 27 plan, TLT closing cross against the SIP close, ledger 164 | CURRENT |
| `research_rig/measure_27.py` | Measurement 27: checks the sessions and Replay 25 input closes, reads TLT SIP trades around each close once (kept off repo), and writes the summary and doc 70 from the off-repo result | CURRENT |
| `research_rig/measure_27_summary.json` | Measurement 27 aggregates only (counts, bps statistics, cross sizes, session dates not found). No trade or price | CURRENT |
| `research_rig/MEASURE_34_tmf_month_end.md` | Frozen Measurement 34, queue 56 and ledger 169: TMF instrument tracking, cost and drawdown on Replay 25's windows, with UBT shown only | CURRENT |
| `research_rig/measure_34.py`, `research_rig/test_34.py` | Measurement 34: offline no-return input validation, an exclusive one-run lock and synthetic tests. Bar and quote inputs and run results stay off repo | CURRENT |
| `research_rig/FREEZE.json` | Measurement 34 freeze manifest: pins the approved plan, code, tests and reused Replay 25 calendar and common code. No market inputs | CURRENT |
| `research_rig/report_34.py` | Formats the pinned saved Measurement 34 aggregate into doc 82 and an optional dashboard card. No scoring or market-data reads | CURRENT |
| `research_rig/PREREG_35_ibit_cme_expiry.md`, `research_rig/config_35.json`, `research_rig/PINNED_35.json` | Frozen Plan 35 IBIT expiry window, queue 57 and ledger 170. Exact settings and audited byte pins; no market inputs | CURRENT |
| `research_rig/score_35.py`, `research_rig/test_35.py` | Plan 35 no-return input validator, approved one-shot runner and synthetic-only tests. Private independently staged inputs and results stay off repo | CURRENT |
| `research_rig/PREREG_36_form4_cluster_buys.md` | Frozen Plan 36, Queue 60 and Ledger 171. Original Form 4 officer and director cluster purchases, matched fund and nine pass marks | CURRENT |
| `research_rig/INPUT_CONTRACT_36.md` | Plan 36 independent data custody, point-in-time source roster and sparse market input contract. Payloads stay off repo | CURRENT |
| `research_rig/PINNED_36.json` | SHA-256 pins for the Plan 36 freeze files | CURRENT |
| `research_rig/calendar_36.json` | Pinned Plan 36 XNYS sessions, early closes and UTC timestamps | CURRENT |
| `research_rig/common_36.py` | Plan 36 event, liquidity, spread, action and comparator logic; nine scoring marks | CURRENT |
| `research_rig/score_36.py` | Plan 36 no-return validator and approval-gated one-shot runner | CURRENT |
| `research_rig/test_36.py` | Plan 36 synthetic-only clock, coverage, outcome and gate tests | CURRENT |
| `research_rig/measure_15_summary.json` | Measurement 15 aggregates only (counts, medians, means, 90th percentiles, outlier check). No trade, quote, price, time or symbol; the per-stock-day output stays off repo | CURRENT |
| `research_rig/report_15.py` | Writes the Measurement 15 summary from the off-repo output, and prints doc 66 from the summary only. No rule run and no market-data reads | CURRENT |
| `research_rig/results_19.json` | Saved one-shot result, aggregate returns and costs, shifted-hour Sharpes and run fingerprints. No raw bars | CURRENT |
| `research_rig/report_19.py` | Prints the Replay 19 result page from the saved JSON. Does not score or read market data | CURRENT |
| `research_rig/PREREG_20_upbit_listing_short.md`, `research_rig/common_20.py`, `research_rig/score_20.py`, `research_rig/test_20.py`, `research_rig/stage_20.py` | Queue 29 red-day Upbit short, ordinary-jump comparison, checksum-only staging and offline clock scan. Scored once; see doc 71 | CURRENT |
| `research_rig/PREREG_23_ipo_fast_track.md` | Frozen Queue 37 IPO fast-track index buying, ledger 160, eight marks. No bar collected or result | CURRENT |
| `research_rig/common_23.py`, `research_rig/fetch_23.py`, `research_rig/score_23.py`, `research_rig/report_23.py`, `research_rig/calibrate_23.py`, `research_rig/test_23.py` | Replay 23 engine and approval gate, off-repo bar collector and freeze, one-shot scorer, page writer, planted-path calibration, invented-input fixtures | CURRENT |
| `research_rig/PINNED_23.json` | Replay 23 frozen plan, code and config-block hashes read by the approval gate. No bars, breakpoints or prices | CURRENT |
| `research_rig/APPROVAL_23.md` | The lead agent's approval line for replay 23: one collection and one scored run, names the freeze commit. Read by the approval gate | CURRENT |
| `research_rig/PREREG_25_treasury_month_end.md` | Frozen Queue 41 Treasury ETF month-end window, ledger 162, nine marks. No data collected or result | CURRENT |
| `research_rig/PREREG_26_treasury_month_end_early.md` | Earlier Treasury ETF month-end replication, queue 45 and ledger 163. Nine marks and a separate no-return vendor overlap check | CURRENT |
| `research_rig/calendar_26.json`, `research_rig/source_26.json`, `research_rig/PINNED_26.json` | Replay 26 exchange calendar, private-source provenance pins and freeze manifest. No price data | CURRENT |
| `research_rig/APPROVAL_26.md` | The lead agent's approval line for replay 26: validation and one scored run, names the freeze commit. Read by the approval gate | CURRENT |
| `research_rig/APPROVAL_31.md` | The lead agent's approval line for replay 31: validation and one scored run, names the freeze commit and the three pinned hashes. Read by the approval gate | CURRENT |
| `research_rig/APPROVAL_35.md` | The lead agent's approval line for replay 35: validation and one scored run, names the freeze commit and the two pinned hashes. Read by the approval gate | CURRENT |
| `research_rig/APPROVAL_39.md` | The lead agent's approval line for replay 39: validation and one scored run, names the freeze commit and the three pinned hashes. Read by the approval gate | CURRENT |
| `research_rig/common_26.py`, `research_rig/score_26.py`, `research_rig/test_26.py` | Replay 26 schedule, offline input validator, one-shot gate and synthetic tests. Reuses Replay 25 numerical helpers | CURRENT |
| `research_rig/PREREG_31_bond_etf_month_end.md`, `research_rig/PINNED_31.json` | Queue 50 and ledger 166. Frozen bond ETF month-end test against Treasury and equity factors. No input bars or payouts | CURRENT |
| `research_rig/common_31.py`, `research_rig/score_31.py`, `research_rig/test_31.py` | Replay 31 pooled residual math, offline no-return validation, one-shot approval gate and synthetic tests | CURRENT |
| `research_rig/PREREG_39_iwm_preholiday.md`, `research_rig/calendar_39.json`, `research_rig/PINNED_39.json` | Queue 65 and ledger 174. Frozen IWM pre-holiday replay, official calendar and strategy hashes. No price or payout rows | CURRENT |
| `research_rig/common_39.py`, `research_rig/score_39.py`, `research_rig/test_39.py` | Replay 39 calendar and payout math, no-return validator, one-shot approval gate and synthetic tests | CURRENT |
| `research_rig/PREREG_33_treasury_auctions.md`, `research_rig/PINNED_33.json` | Queue 52 and ledger 168. Frozen intraday Treasury auction-day test: long IEF or TLT from 13:10 to 15:59 ET on 10-year and 30-year auction days, judged on executable quotes. No vendor data | CURRENT |
| `research_rig/score_33.py`, `research_rig/test_33.py` | Replay 33 scorer with offline no-return validation, one-shot approval gate, and synthetic tests | CURRENT |
| `research_rig/auction_calendar_33.csv`, `research_rig/control_pairs_33.csv`, `research_rig/sessions_33.csv`, `research_rig/fees_33.csv`, `research_rig/fomc_dates_33.txt`, `research_rig/nonbill_auction_days_33.txt` | Replay 33 pinned public inputs: official auction calendar, the 260 matched control dates, exchange sessions, regulator fee table, FOMC dates, and other coupon auction days. Public metadata only | CURRENT |
| `research_rig/PREREG_24_same_coin_carry.md` | Frozen Queue 39 same-coin funding carry, ledger 161, five marks, reviewed off-repo metadata hashes. No real result | CURRENT |
| `research_rig/common_24.py` | Replay 24 spot and perpetual event accounting, fees and matched controls | CURRENT |
| `research_rig/score_24.py` | Replay 24 owner-gated no-claim input validator, one-shot scorer and result renderer | CURRENT |
| `research_rig/test_24.py` | Replay 24 invented-input fixtures and planted calibration | CURRENT |
| `research_rig/report_24.py` | Generates doc 68 from the off-repo saved result and owner run records without reading market data | CURRENT |
| `research_rig/common_25.py`, `research_rig/fetch_25.py`, `research_rig/score_25.py`, `research_rig/test_25.py` | Replay 25 accounting, raw-only off-repo collector, pinned one-shot scorer, invented-input fixtures and calibration | CURRENT |
| `research_rig/calendar_25.json`, `research_rig/PINNED.json` | Replay 25 session-date calendar and frozen code and plan hashes. No bars, issuer amounts or other vendor rows | CURRENT |
| `research_rig/check_identity_levels_16_17.py`, `research_rig/diagnose_identity_daily_16_17.py` | Plans 16 and 17 identity check: does a Binance pair carry the coin on the saved list, by matching saved price levels; prints counts only, computes no return | DRAFT |
| `research_rig/PREREG_16_hot_five_hedged.md` | Plan 16, frozen 2026-11-25: last week's five biggest risers long, a same-size futures short, weekly, judged on a held-back coin list. Run once, not supported | CURRENT |
| `research_rig/build_identity_asof_16_17.py` | Builds the shared dated identity policy for plans 16 and 17 and counts changes against the every-month check | CURRENT |
| `research_rig/held_live_coverage_16_17.py` | Counts held-back list contracts live on each Monday, no returns | CURRENT |
| `research_rig/identity_asof_16_17.py` | Applies saved identity evidence as of each replay Monday | CURRENT |
| `research_rig/identity_chronology_16_17.py` | Measures the gap between a Binance file's first bar and the coin's saved listing date | CURRENT |
| `research_rig/identity_review.py` | Rebuilds the shared identity evidence from saved pages and pinned archives | CURRENT |
| `research_rig/measure_replay_load_16_17.py` | Measures the loaders' peak memory without running either replay | CURRENT |
| `research_rig/repair_month_edges_16_17.py` | Scans monthly archive files for cut-off edges and adds checksum-verified daily files | CURRENT |
| `research_rig/replay_clock_audit_16_17.py` | Counts Monday liveness, zero-volume spells and hours with no mark bar, no returns | CURRENT |
| `research_rig/us_roster_17.py` | Verifies the pinned US-shortable roster and maps its coins to CoinMarketCap ids | CURRENT |
| `research_rig/us_roster_coverage_17.py` | Reports stored spot and futures coverage for the shown-only US roster of plan 17 | CURRENT |
| `research_rig/PREREG_17_short_the_peak.md` | Plan 17, frozen 2026-11-25: the short side of the owner's method as a fixed rule on futures, judged on the held-back coin list. Run once, not supported | CURRENT |
| `research_rig/results_16.json` | Plan 16 result: both lists and both shorts by year at three cost levels, random draws, flags and input fingerprints. Written once by score_16.py --run | CURRENT |
| `research_rig/score_16.lock` | Plan 16: marks that the run was made; a second run is refused | CURRENT |
| `research_rig/results_17.json` | Plan 17 result: the short rule by year on the held-back, viewed and US-shortable lists, yardsticks, 3x and bounce variants, US fee levels, flags and input fingerprints. Written once by score_17.py --run | CURRENT |
| `research_rig/score_17.lock` | Plan 17: marks that the run was made; a second run is refused | CURRENT |
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
| `research_rig/results_11_design.json` | Plan 11: the six set-ups scored on the 450-release design sample, the agreement between readers, and the set-up chosen to read the held-back half. Written once by score_11.py --design | RECORD |
| `research_rig/answers_11_heldback_hashes.json` | Plan 11: hashes of the chosen reader's 2,146 held-back answers, pushed before any held-back price is read | RECORD |
| `research_rig/reader_notes_11.md` | Plan 11: what went differently from the reader brief (files sent back once, readers that said they ran a command) | RECORD |
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
| `practice/traders/E01_tlt_month_end_close.md` | E01, the forward log of Replay 25's TLT month-end window from December 2026: data only, no orders, a month counts only if written before the next month starts. A fixed rule, not an AI trader, and not in `practice/traders.json` | CURRENT |
| `practice/forward_e01.py`, `practice/test_forward_e01.py` | The E01 recorder (`plan`, `record YYYY-MM`) through the saved data credential, and its checks with a pretend data source and no network. Full records stay off repo; the log in the repo holds no prices | CURRENT |
| `practice/PROPOSAL_E01_paper_order_leg.md` | Proposal only: a practice-account market-on-close leg for E01, the broker change it needs, the key names, and why a practice fill is not the auction price | DRAFT |
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
| `timemachine/TM06_LAUNCH_BRIEFS.md` | Plan TM06: the exact text pasted to each agent of a picker or swing session, with placeholders, and how hand-offs are made | CURRENT |
| `timemachine/perp.py` | Perp mode for weights sessions (instrument perp): signed weights up to max_gross, hourly or 8 hour funding from stored files, per-symbol fee and half spread, maintenance and close-out on the minute low or high, stops and targets, wakes from 15 minutes to daily. Its scorer replays the session to the cent, then scores the same answers at each fee in `tm_perp_fee_levels_bps` with the random sign twin, the signs flipped yardstick and long and short holds | CURRENT |
| `timemachine/attention.py` | Reads the attention store (Wikipedia page views, headline counts, Reddit counts per coin) as of a simulated time; serves only periods that were complete and published by then | CURRENT |
| `timemachine/test_attention.py` | Checks that the attention reader never serves a count before its availability time and treats a missing row as unknown | CURRENT |
| `timemachine/code_traders.py`, `timemachine/run_code_trader.py` | Traders that need no model (hold, random, the fixed rules, the perp rules perp_hold and bar_trend), and the command that runs one through a session. Its `rule` subcommand runs any Python function of the packet through a weights or perp session at full speed | CURRENT |
| `timemachine/PLAN_TM01_crypto_price_only.md` | Plan for the first AI replays: six models, one card, crypto prices only, with the pass mark fixed before any session | CURRENT |
| `timemachine/PLAN_TM02_crypto_with_news.md` | Plan for the second AI replays: the same six models and months with dated crypto headlines added, and the test for whether the news helped | CURRENT |
| `timemachine/PLAN_TM03_bitcoin_dial.md` | Plan for the third AI replays: each model sets once a day how much bitcoin to hold, starting fully invested. Marks fixed before any session | CURRENT |
| `timemachine/PLAN_TM04_stock_basket.md` | Plan for the fourth AI replays: each model names once a week eight of 38 stocks to hold. Marks fixed before any session | CURRENT |
| `timemachine/PLAN_TM06_hot_coin_swing.md` | Plan for the owner's method in two parts tested apart: a daily picker of hot coins and an hourly swing trader, with a control run of the futures book first. Marks fixed before any session | CURRENT |
| `timemachine/TM06R_addendum.md` | Addendum to plan TM06 that repeats the Claude Fable 5.2 picker twice more on the same eight months, with the marks for repeats, did not repeat and mixed fixed before the sessions | CURRENT |
| `timemachine/tm06_fix_weeks.py` | Works out once, from daily bars, the four test weeks and the five coins of each swing session in plan TM06 | CURRENT |
| `timemachine/tm06.py` | Plan TM06's tools: the fast tape's funding and open interest as of the wake, picker sessions (part P), swing sessions (part S), the 15-minute reversal control, and their yardsticks, twins and carried leverage | CURRENT |
| `timemachine/score_tm06.py`, `timemachine/results_tm06.json` | Scores plan TM06 from the finished TM06 sessions: each at every fee level, its yardsticks, its twins' percentile, trades, time in market and forced close-outs; swing sessions also at 2x and 3x. The JSON is its stored output | CURRENT |
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
| `timemachine/perp_fast.py`, `timemachine/test_perp_fast.py` | A faster twin scorer for TM06 and its checks; not proven equal to the slow scorer on a stored session, so switched off by default | DRAFT |
| `timemachine/autopsy/README.md` | Start here for the read-through of the traders' reasons: what it is, how to rerun, what it reads, paths and flags | CURRENT |
| `timemachine/autopsy/autopsy.py` | The read-through script: reads TM01 to TM04 session folders, twins and the tape read only, writes `timemachine/autopsy/autopsy_results.json` | CURRENT |
| `timemachine/autopsy/core.py` | Its pure helpers: table cells and the under-30 rule, spread per fill, round trips from the desk's closed list, label id check | CURRENT |
| `timemachine/autopsy/load.py` | Reads answers, fills and per-stock reasons from TM01 to TM04 session folders, never TM06 or void sessions | CURRENT |
| `timemachine/autopsy/prices.py` | Minute prices from the recorded tape, read only, at or before each time | CURRENT |
| `timemachine/autopsy/classify.py` | Word rules that place each buy, sell, dial and basket reason in a category, and the buy flags | CURRENT |
| `timemachine/autopsy/settings.py` | Run folder, tape and output paths of the read-through (flags, environment, defaults) | CURRENT |
| `timemachine/autopsy/test_autopsy.py` | Offline tests of the read-through on made-up records | CURRENT |
| `timemachine/autopsy/categories.md` | The category list, fixed 2026-11-25 21:27 UTC before any outcome was joined | RECORD |
| `timemachine/autopsy/labels_by_hand.jsonl` | The analyst's hand labels, by id only (no text) | RECORD |
| `timemachine/autopsy/hand_checks.json` | Hand checks by id only: blind sample ids, blind relabel, two rule checks, contradiction check, later-date and cross-session verdicts | RECORD |
| `timemachine/autopsy/quotes.json` | The 12 quotes used in the page, with session and kind | RECORD |
| `timemachine/autopsy/autopsy_results.json` | Results of the read-through, written by `timemachine/autopsy/autopsy.py` | CURRENT |

## dashboard/ (the owner's screen)

| Folder | What it is | State |
|---|---|---|
| `dashboard/` | A single page that shows the tests, the trades inside them and what waits on the owner. Its data file is built by `research_rig/export_dashboard.py` and is not stored in the repo. `dashboard/README.md` says how to run it | CURRENT |

## Keeping this page true

- A commit that adds, moves or retires a file changes this page in the same commit.
- A commit that changes a result or a decision changes `docs/STATUS.md` in the same commit.
- Retire a file by changing its State to RECORD and naming what replaces it. Do not delete results.
- Run `python3 tools/check_repo.py` before every commit.
