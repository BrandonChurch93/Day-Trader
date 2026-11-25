# Status

Last updated: 2026-11-25 09:30 UTC

This page is the current state of the project. It is the second thing to read, after `AGENTS.md`. If another page disagrees with this one about a result or about where things stand, this page stands. The map of every file is `docs/INDEX.md`. Terms, test names and rule names are defined in `docs/GLOSSARY.md`.

`AGENTS.md` still names `docs/playbook/00_START_HERE.md` as the second read and says to load `docs/playbook/` by default. Only the owner may change that file, so it has not been changed. Until he decides, every playbook page opens with a dated note that says it was written before any test and sends the reader here for results. A reader who follows `AGENTS.md` to the letter still arrives at this page. The exact lines and the proposed wording are in `docs/decisions/morning_list_2026-11-25.md`, item 5 of "Things only you can do".

## Phase

- Research. Nothing is built. Building has not been approved by the owner.
- No broker account, no keys, no purchases, no real trades.
- A research rig in `research_rig/` replays rules on past prices. It is not the product.
- Owner direction that applies now, with dates, is in `docs/decisions/0002-historical-testing-and-risk-posture.md` (test on past data, a middle risk level, a small moonshot share only where there is a reason) and `docs/decisions/0003-quality-bar-adopted.md`.

## Every test so far

The Result column is written by `tools/status_table.py` from the output files. Do not edit it by hand.

- Where the table shows a bar, it is the value stored in the output file when the test was run. The value in force is in `config/thresholds.yaml`.
- The keys the tests are judged on have the status "proposed" in that file. Research uses them to judge research replays. That use approves nothing: no bar is an owner decision until he says so.
- Pilot 02 was a replay on past prices. `AGENTS.md` hard rule 7 does not count that as evidence of model skill, for or against. It tested the harness and how the models behave.

<!-- results:start (written by tools/status_table.py, do not edit by hand) -->
| Test | What was asked | Result, MEASURED | Full write-up |
|---|---|---|---|
| Replay 01 with cross-check X2, rerun after the audits | Nine slow trend rules on bitcoin and on ether, daily, five venue costs, two price histories | 9 of 90 rule, coin and venue combinations pass on Bitstamp prices and 4 of 90 on Kraken prices. Pass on both histories: P1, P2, S50, D20 on BTC, at Binance.US cost only. In the first run, before the audit fixes, none passed on both histories (8 on Bitstamp prices, 0 on Kraken prices). Knife edge: the overfitting estimate on Kraken prices is 0.2409 against a bar of 0.25 when it was run (`backtest_max_pbo`), and 0.4205 on Bitstamp prices from the same start date, which fails. | `docs/research/16_rig_audit.md` |
| Replay 03, rerun after the audits | Eight day trading rules on hourly bitcoin and ether, five venue costs | 0 of 80 rule, coin and venue combinations pass. | `docs/research/16_rig_audit.md`, rule definitions in `docs/research/15_replay_03_intraday_crypto.md` |
| Pilot 02 | Six AI model runs making one call a day on bitcoin and ether | Inconclusive, as the plan said before it ran. 6 model runs, 147 calls each. Too few days to tell skill from luck. | `docs/research/14_ai_calls_pilot_02.md` |
| Replay 04 | Trend rules on a wide basket of coins, dead coins kept | 0 of 25 rule and venue combinations pass. Highest deflated Sharpe 0.933 (K4 at Binance.US) against a bar of 0.95 when it was run (`replay_min_deflated_sharpe`). Held-back years at Binance.US cost: the top 10 coin rule K1 grew +2.7% a year, holding bitcoin grew +43.5%. An independent audit rebuilt the result and found faults that do not change it. | `docs/research/23_replay_04_coin_basket.md` |
| Replay 05, first run and corrected run | Eight slow trend rules on the US stock market index from 1927, three cost levels | First run: none at 2 bps; none at 5 bps; T1, T5, V1, I1 at 10 bps. Corrected run, after an audit found one rule did not match the plan: T1, T2, T4, T5, V1, I1, I2 at 2 bps; T1, T5, V1, I1, I2 at 5 bps; T1, T5, V1, I1, I2 at 10 bps. Pass in both runs at every cost: none. Which run counts is the owner's to say (questions 18a and 18b in the morning list); until then the first run stands, and research recommends it keep standing. Held-back years at 5 bps, the same in both runs: the ten-month rule T1 grew +9.1% a year with a largest drop of -21.9%, holding the market grew +11.5% with -54.6%. | `docs/research/22_replay_05_stock_trend.md` |
| Order-book samples | What it cost to trade a small size at once, sampled on two venues on one day | 18 rounds from 2026-11-25 07:28:03 to 2026-11-25 08:02:03 UTC. Bitcoin, middle cost of one order, fees not included: $1,000 cost 0.0 bps on Kraken and 0.8 bps on Binance.US; $10,000 cost 0.2 and 1.8 bps. The crypto replays assume 5 bps for this on bitcoin and ether. One sample of 34 minutes only. | `docs/research/24_order_book_costs.md` |
| Smaller checks: X1, S1, S2, the diagnostic, two mixed portfolios | The same rules on other prices, start dates and fill times, and bitcoin and ether held together | Not separate tests and not in the trial count. S2, ether from an earlier start on Kraken prices: 0 of 45 combinations pass. X1 and S1 carry no pass marks. The diagnostic is the Bitstamp figure in the first row. The two mixed portfolios are reported with growth and largest drop and are not judged on the five marks. Each name is defined in `docs/GLOSSARY.md`. | `docs/research/12_replay_01_crypto_trend.md`, `docs/research/12b_replay_01_kraken_crosscheck.md`, `docs/research/16_rig_audit.md` |
| Trial count check | The owner's rule counts a rerun after an engine fault as a trial. The two reruns were not counted when they ran. Does counting them change a result | Worked out from the stored outputs with 93 trials counted. It covers the outputs now judged: the rerun of replays 01 and 03 with its cross-checks, replay 04, and both runs of replay 05. The first-run outputs of replays 01 and 03 came from the engine with the faults and are not worked out again. Of 34 passes in those outputs, across all cost levels, none become fails. 66 of 378 rows could not be worked out again from what was stored, and none of those had passed mark 3. The closest is M90 on Binance.US, BTCUSD in R01, at 0.951 against a bar of 0.95 (`replay_min_deflated_sharpe`). Pass mark 3 alone changes from pass to fail in 29 rows that had already failed another mark. | `research_rig/TRIAL_LEDGER.md`, `research_rig/ledger_count_check.json` |
<!-- results:end -->

A pass means "worth running in a practice account". It does not mean "makes money". The five pass marks and their config keys are in `research_rig/README.md`. Each plan can add its own conditions on top, such as passing on both price histories.

## What is believed now

Each line says how far to trust it.

- No rule has a clean pass. MEASURED. Every pass in the table came after a code correction, or exists at one cost level only, or sits within a hair of a bar. Five stock rules pass at every cost in the corrected run of replay 05 and none of them passes at every cost in the first run. The corrected run fixed a fault in the code of one rule, not in the engine. The owner's rule allows a second run of the held-back slice only when the engine itself was wrong, so it may not cover this one. That is question 18 in `docs/decisions/morning_list_2026-11-25.md`. Until he answers, the first run is the one that stands: no stock rule passes at the two lower cost levels.
- Slow trend rules cut the largest drop and give up growth. MEASURED on bitcoin and on the US stock market, and it matches the live record of funds built on the same rules (`docs/research/21_systematic_funds_and_published_rules.md`). In the held-back years most of them grew less than simply holding: three of the four passing bitcoin rules on each price history (`docs/research/16_rig_audit.md`), and the ten-month stock rule in the table above.
- No day trading rule on crypto passes the five marks at any venue cost tested. MEASURED. That is not the same as every rule losing money: at the lowest venue cost a few ether rules have a positive Sharpe ratio in the held-back years, and none passes. At Alpaca cost every one of them lost money in the held-back years (`docs/research/16_rig_audit.md`, the table of hourly rules).
- A wide basket of smaller coins grew far less than holding bitcoin in the held-back years, and no basket rule passes. MEASURED. The figures are in the table above.
- Nothing tested so far supports fast money. MEASURED for the rules in the table, which is a short list. The reading on traders, funds and AI systems with real money points the same way (`docs/research/25_what_the_evidence_supports.md`). A no on these rules is strong for these rules. It does not rule out ideas that have not been tested.
- Pass mark 4, the overfitting estimate, is not steady enough to be a yes or no on its own. MEASURED three ways: it moves with the start date, it passes on made-up data with no edge in a share of samples that document 16 gives, and in replay 05, where it is one number per cost level across all eight rules, it went from failing to passing at the two lower cost levels when one of the eight rules was corrected. At the highest cost level it already passed in the first run (`docs/research/16_rig_audit.md`, `docs/research/22_replay_05_stock_trend.md`). The bar in `backtest_max_pbo` has not been changed.
- AI models making the trading call: no evidence that it works, from live public records (`docs/research/18_ai_systems_with_live_records.md`). Our own pilot was a replay on past prices and cannot count either way (`docs/research/14_ai_calls_pilot_02.md`). Models stay out of the order path (`AGENTS.md` hard rule 1).
- The closest thing to a lead on stocks is rule I2 in replay 05: hold the three strongest industry groups when the market is above its ten-month average. In the corrected run, which does not stand as the result until the owner answers question 18 and which research recommends should not stand, it grew nearly as much as holding with a much smaller largest drop. It carries three cautions listed in `docs/research/22_replay_05_stock_trend.md`, and it has not been tested on anything that can be bought. Treat it as a reason for the next test, not as a result.
- Stocks have been tested only on a free index that cannot be bought. Funds that can be bought, and day trading SPY and QQQ, are UNKNOWN. No rule has been run on either.

## What has been replaced

| Do not rely on | Use instead | Why |
|---|---|---|
| Verdicts in `docs/research/12_replay_01_crypto_trend.md`, `docs/research/12b_replay_01_kraken_crosscheck.md`, `docs/research/15_replay_03_intraday_crypto.md` | `docs/research/16_rig_audit.md` | Two code audits found faults in the first rig. The rerun changed verdicts |
| Engine v1 (`research_rig/engine.py`) | Engine v2 (`research_rig/rig2.py`) | Same reason |
| `docs/decisions/0005-overnight-research-2026-11-25.md` where it reports results | `docs/decisions/0006-audit-and-second-night-2026-11-25.md` and the table above | Results changed after the audits |
| Either run of replay 05 read alone | Both runs side by side in `docs/research/22_replay_05_stock_trend.md`. The first run stands until the owner answers question 18 in the morning list | The code for rule I2 did not match the plan. That is a rule fault, not an engine fault, and the owner's rerun rule names the engine only |
| Playbook lines that read as settled findings | This page | The playbook was written from reading on 2026-11-24, before any test of our own |

## Known faults and slips

- `research_rig/basket.py` closes a position in a coin whose history ends by using knowledge of the full file. It never fired in replay 04. It must be fixed before the file is used again (`audit/2026-11-25_replay_04_audit.md`, finding 04-01, and two more in 04-02 and 04-03).
- Trial ledger rows for replays 04 and 05 were added after the runs started. The plans naming the trials were pushed before the runs. Recorded in `docs/decisions/0006-audit-and-second-night-2026-11-25.md`.
- Two reruns had no ledger row and were not counted as trials. The owner's rule says a rerun after a proved engine fault is written in the ledger, counted as a trial and reported as a rerun (`docs/quality/01_the_bar.md`). The rerun after the audits and the corrected run of replay 05 were reported as reruns and were not in the ledger. Rows R1 and R2 were added late on 2026-11-25. Counting them, as the rule says, was then checked on the stored outputs: the result is the "Trial count check" row in the table above. Every later run uses the larger count (`research_rig/TRIAL_LEDGER.md`).
- The corrected run of replay 05 (ledger row R2) was made under a wider reading of the owner's rerun rule than he wrote. His words allow a rerun "when a machine check proves the engine itself was wrong". In replay 05 the engine was right and one rule was coded differently from its plan. Research reran before asking, and for a time `research_rig/README.md` and `docs/GLOSSARY.md` gave the rule as "the engine or the code". Both now quote him. The ledger row for that run was also added after it, not before. Questions 18a and 18b in the morning list ask him to settle it, and research now recommends that the first run stands.
- The rerun after the code audits (ledger row R1) rests on research's reading of two words in the owner's rule that he has not defined: that an audit by another model which ran its own checks is a "machine check", and that the code which works out the pass marks is part of "the engine itself". He was not asked. Question 18c. If he reads his rule more narrowly, the first results of replays 01 and 03 stand, and in those no rule passes on both price histories.
- `research_rig/export_dashboard.py`, which makes the data for the owner's screen, replayed five already-tested rules on the whole price history, held-back years included, every time it ran, to draw their curves. It ran several times on 2026-11-25 and the count was not recorded. It checked each figure against `results_v2.json` and made no new number. `research_rig/README.md` described it as reading the output files, which was wrong. A cold-read test found this. The script now reads saved curves and replays nothing unless given `--resimulate`. `i2_2020_note.py` was also run a second time, output identical. Whether such repeats are allowed is question 16.
- The owner's lines in `docs/quality/01_the_bar.md` are written for the Builder, the mode that builds from a kit. Research applies them to its own tests. That is research's choice and is stated here so nobody takes it for his instruction.
- Outputs were not stored with their command, commit and input fingerprints at run time, which `docs/quality/01_the_bar.md` asks for. `research_rig/provenance.json` rebuilds that record after the fact, from git history and the files on the research machine. It shows that no input file was modified after the output that used it was first stored. It cannot prove the bytes were the same at run time.
- Three document builders (`build_doc12.py`, `build_doc12b.py`, `build_doc15.py`) left out the dated correction note that had been added by hand to their pages, so running them again deleted it. Found by a fresh-copy test on 2026-11-25 and fixed: the note is now in the builders, and `python3 tools/check_repo.py --builders` fails if any built page differs from what its builder writes.
- `docs/decisions/0002-historical-testing-and-risk-posture.md` proposed that a replay of a model on dates after its training cutoff could count. `AGENTS.md` hard rule 7 says only forward paper or shadow results count. Hard rule 7 stands. Question 19 in the morning list.
- The held-back slice has been looked at more than once per rule. Besides the two reruns: cross-checks on a second price history, one short try of replay 05 with 3 shuffles before its full run, where rough results were seen (`docs/research/22_replay_05_stock_trend.md`), the repeats by the dashboard script in the line above, and the first start of replay 03, which stopped at its save step before any result was read and was started again (`research_rig/TRIAL_LEDGER.md`, rows 27 to 42). No rule or setting was changed after any of these. The held-back slice is no longer fresh for any rule tested so far. The only fresh test left is the practice account.
- The plans for replay 01 and pilot 02 were pushed in the same commit as their results (b393482). The plans carry their own written times, which say they came first. That is STATED and cannot be shown from the commit history. From replay 03 on, each plan was pushed before its run.
- Pass mark 3 screened nothing in replay 05, because of how its plan defined the spread of Sharpe ratios. Research proposes that the next plan defines it across all counted trials. That is a proposal to the owner, not a rule yet.
- Bitstamp's terms are unclear about collecting its prices. Kraken's published files are the proposed main crypto history. Waiting on the owner.

## Waiting on the owner

The full list, one item at a time, with what each approves and does not approve: `docs/decisions/morning_list_2026-11-25.md`. Nothing on it is decided.

Decisions research would take first, because the next tests depend on them:

1. How pass mark 4 is measured from now on (decision 1 in that list).
2. How pass mark 3 is measured (decision 2), and whether every replay gets an independent audit (decision 3). Research works this way already. Neither is an approved rule.
3. What to test next (decision 4) and which rules to watch in the practice account (decision 5).

Older questions that were never put to him and are on the same list now: the two scope calls of 2026-11-24 (decisions 14 and 15), whether a stored test may be run again unchanged as a check (16), and what "within tolerance" means in the practice and live gates, which has no number (17). Two more found by the second pair of cold readers: whether his rerun rule covers a rule coded differently from its plan, which decides which run of replay 05 counts (18a and 18b), whether the rerun after the code audits was covered by his rule at all (18c), and whether a replay of an AI model on dates after its training cutoff can count as evidence against hard rule 7 (19).

Things only he can do:

1. Open an Alpaca account for practice trading and create practice keys.
2. Buy one month of stock price data. Replay 06 needs its dividend history. It also gives a second source to check item 6 against.
3. Say whether Kraken's published files may be the main crypto history.
4. Say whether the order-book sampler may run again on Kraken's public price feed.
5. Say whether `AGENTS.md` and `docs/quality/00_READ_FIRST.md` may be changed so that they point to this page and to `docs/INDEX.md`. The morning list names each line and the proposed wording.
6. Say whether stock prices from the workspace's own built-in price history may be used and kept for tests (`docs/research/10_historical_data_and_practice.md`, "Price history inside the workspace").

Open owner numbers, with no value yet: `live_starting_capital_usd`, `live_max_position_usd`, `live_max_daily_loss_usd`, `live_max_total_loss_usd`, `moonshot_sleeve_share`, `moonshot_max_position_share`, `api_model_spend_cap_usd_month`. Nothing may assume a value for any of them.

## Next in the queue

This is the queue in force. If another page lists a different order, this one stands. It is proposed, not approved: nothing on it that needs the owner starts without him. The reasons for the order are in `docs/research/25_what_the_evidence_supports.md`.

1. Owner decides how pass mark 4 is measured from now on (`docs/research/16_rig_audit.md`, "Questions for the owner"). Every later replay depends on it.
2. Watch two slow rules in the practice account with pretend money, as observation only and labelled as not passed: the bitcoin rule P1 and the ten-month rule on a total market fund. Needs practice keys and the owner's yes to decision 5 in the morning list.
3. Replay 06: slow trend on funds that can be bought. Plan drafted in `research_rig/PREREG_06_fund_trend_paid_data_DRAFT.md`. Needs the data purchase for dividend history, the owner's yes to decision 4, and his decision on pass mark 4 before the plan is frozen. Proposed addition before it is frozen: the industry rule I2 on sector funds, which was picked after seeing the corrected run of replay 05 and must be disclosed as that in the plan.
4. Replay 07: day trading SPY and QQQ on one-minute bars. Plan drafted in `research_rig/PREREG_07_intraday_spy_qqq_DRAFT.md`. Needs one-minute prices, from the data purchase or from the workspace's own price history if the owner allows it (item 6 of "Things only he can do"), his yes to decision 4, and his decision on pass mark 4.
5. Credit Treasury bill interest on idle cash in every replay. A rig change with its own plan. Needs the owner's yes to decision 7.
6. Later, each with its own plan: insider buying that is not routine, a plain statistical model against a tree model logged only, a small-company fund held overnight only, and buying stocks at new highs with tight exits.
7. Only if basket tests continue, which research recommends against (decision 6): fix the three faults in `research_rig/basket.py` first.

Nothing in this queue can start today without the owner except drafting plans.

## Keeping this page true

- Any commit that adds or changes a result, a decision or what waits on the owner changes this page in the same commit, and moves the "Last updated" line.
- After any new output file: `python3 tools/status_table.py --write`.
- Before every commit: `python3 tools/check_repo.py`. It fails if the table above is out of date or a file named here does not exist.
- Write beliefs with their label. Do not raise a label without a new source or a new logged test.
