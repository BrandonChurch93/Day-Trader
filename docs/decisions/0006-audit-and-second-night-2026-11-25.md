# 0006 - Code audits, rerun, replays 04 and 05, and the repo map, 2026-11-25

Date: 2026-11-25 (UTC). The second half of the night of 2026-11-24 in Idaho.
Status: proposed by the research team. Nothing here is an owner decision.

This note continues `docs/decisions/0005-overnight-research-2026-11-25.md` and corrects the results reported there. The current state is always `docs/STATUS.md`.

## What the owner said, 2026-11-25 (UTC)

- On using the rest of the night: "I don't see the point in stopping your work. Maybe worth building me a simple application to use as an interface to see our trades and overall analytics. Doesn't have to be anything too complicated. Simply the better to be honest".
- On how to work: "I want you to treat this as we're partners here. The goal is to make a successful harness/method for making money. Preferably fast." He asked for research on plans, news, API connections, successful traders, and AI systems that trade with success, and said to use as many agents as needed.
- On the repo: "make sure our repo is organized for models to read and get the important information and processes effectively it shouldn't be a mess. We probably need an index or some form of management that makes sense".

These are directions for research and for how the repo is kept. None of them approves building the product, an account, a key, a purchase or a trade.

## What was done

| Item | Where |
|---|---|
| Two independent code audits of the first rig | `audit/2026-11-25_auditor_a.md`, `audit/2026-11-25_auditor_b.md` |
| The fixes, written down before the rerun | `research_rig/AMENDMENT_2026-11-25_audit_fixes.md` |
| Engine v2 and the rerun of replays 01, X2, S2 and 03, with corrected verdicts | `research_rig/rig2.py`, `docs/research/16_rig_audit.md` |
| Replay 04: trend rules on a wide basket of coins, then an independent audit of it | `docs/research/23_replay_04_coin_basket.md`, `audit/2026-11-25_replay_04_audit.md` |
| Replay 05: slow trend rules on the US stock market from 1927, an independent audit, a correction and a corrected run | `docs/research/22_replay_05_stock_trend.md`, `audit/2026-11-25_replay_05_audit.md`, `research_rig/AMENDMENT_05_I2_equal_thirds.md` |
| Order-book cost samples on two venues | `docs/research/24_order_book_costs.md` |
| Five research summaries, each checked by a second model: verified traders, AI systems with live records, information feeds, small-account edges, systematic funds | `docs/research/17_verified_traders_and_their_methods.md` to `docs/research/21_systematic_funds_and_published_rules.md`, check logs in `docs/research/17_21_checklogs/` |
| A collector of public context readings, with a terms review of each source | `research_rig/feeds/` |
| Draft plans for two stock tests that wait for a data purchase | `research_rig/PREREG_06_fund_trend_paid_data_DRAFT.md`, `research_rig/PREREG_07_intraday_spy_qqq_DRAFT.md` |
| One page that pulls the reading and the tests together, with a ranked test queue | `docs/research/25_what_the_evidence_supports.md` |
| The owner's screen | `dashboard/` |
| The repo map: a front page, a status page, an index of every file, and a check that fails when the map is not true | `README.md`, `docs/STATUS.md`, `docs/INDEX.md`, `tools/check_repo.py`, `tools/status_table.py` |

## What this corrects in 0005

- 0005 says no bitcoin rule has a clean pass. After the audit fixes, four bitcoin rules pass all five marks on both price histories, at the lowest venue cost only. That is still not a clean pass: it appeared after corrections, it sits within a hair of the bar on mark 4, and it fails on the other history from the same start date. The figures are in `docs/research/16_rig_audit.md`.
- 0005 says 0 of 16 day trading rules passed. The rerun counts every rule, coin and venue combination and the answer is the same: none pass.
- The verdict tables in documents 12, 12b and 15 are kept as the record of the first run. Each carries a banner that points to document 16.

## Slips, stated plainly

- Ledger rows late. `AGENTS.md` hard rule 8 says every variant is logged in the trial ledger before it runs. For replays 04 and 05 the plans naming the trials were pushed before the runs, and the ledger rows were added after the runs had started. The count used in the statistics was the right one. The rows now exist with a note. From now on the ledger row and the plan go in the same commit, and `research_rig/README.md` says so.
- Replay 05, rule I2. The code did not hold equal thirds as the plan says. An independent audit found it. The correction was written and pushed before the corrected run, and both runs are reported side by side. The effect of the correction was known before it was written down, so a pass that appears only in the corrected run is reported as that.
- Two full runs of replay 05 were lost to process problems on the test machine and restarted unchanged. No result from them was read.
- Replay 04. The independent audit found three faults in `research_rig/basket.py` that did not change the result. They are listed in `docs/STATUS.md` and must be fixed before the file is used again. The code was not changed after the run.
- Feeds. A terms review found that five sources named in `docs/research/19_information_feeds.md` need written permission before automated collection. The collector has them switched off. The correction is appended to that document.

## What was not changed

- No value in `config/thresholds.yaml` was changed. `backtest_max_pbo` and the other marks stand as they were.
- `AGENTS.md` was not changed. It says any change to it needs the owner.
- No account was opened, no key was requested, no purchase was made, no order was placed, and no product code was written. The rig and the screen are research tools.

## Notes added to playbook pages

The playbook was written from reading on 2026-11-24. A dated note was added at the top of four pages on 2026-11-25. Each says the page is from reading only, says in one or two sentences what our own tests have found since, and points to `docs/STATUS.md`. No playbook rule and no number was changed.

| Page | What the note says our tests added |
|---|---|
| `docs/playbook/00_START_HERE.md` | No rule has a clean pass. Slow trend rules cut the worst drop and give up growth. Day trading rules on crypto lost to fees |
| `docs/playbook/01_stocks_what_works.md` | Replay 05 on a free stock index: less growth than holding, a much smaller drop. Funds that can be bought are untested |
| `docs/playbook/02_crypto_what_works.md` | Bitcoin trend passes only at the lowest cost and on a knife edge. No ether rule passes. The wide basket lost to holding bitcoin |
| `docs/playbook/03_role_of_ai.md` | The pilot was inconclusive. No AI system with live money was found that beat holding |

## Proposals for the owner, one at a time

None is approved. The full list with what each approves and does not approve is `docs/decisions/morning_list_2026-11-25.md`.

| # | Proposal | From |
|---|---|---|
| 1 | Add one line to `AGENTS.md` so that it points to `docs/STATUS.md` and `docs/INDEX.md` after itself. Today it points to `docs/playbook/00_START_HERE.md`. Only the owner can approve a change to that file | this note |
| 2 | Decide how pass mark 4 is measured: count ties as half, and measure it over fixed start dates and block counts. Research recommends yes. This would most likely turn the bitcoin passes back to fails | `docs/research/16_rig_audit.md` |
| 3 | In every future plan, take the spread of Sharpe ratios for pass mark 3 across all counted trials, not only the trials in that plan | `docs/research/22_replay_05_stock_trend.md` |
| 4 | Every replay gets an independent audit before its result is believed | this note |
| 5 | The ranked test queue | `docs/research/25_what_the_evidence_supports.md` |

## Addendum, 2026-11-25 08:56 UTC: what three cold readers found

Three fresh models were each given only the repo address and a set of questions a new worker would ask. This is what they found that this note had wrong or left out. The text above is left as it was written.

Corrections to "Slips, stated plainly":

- "The count used in the statistics was the right one" was wrong. The owner's rule in `docs/quality/01_the_bar.md` says a rerun after a proved engine fault is written in the trial ledger, counted as a trial and reported as a rerun. The rerun of replays 01 and 03 and the corrected run of replay 05 were reported as reruns. They were not in the ledger and were not counted. Rows R1 and R2 were added late, and the count from now on is 93.
- Does counting them change a result? `research_rig/ledger_count_check.py` worked pass mark 3 out again from the stored outputs at that count, running no rule and reading no prices. MEASURED: 378 rows checked, 34 passes as run, 0 of them become fails. The closest is rule M90 (Binance.US, BTCUSD, replay 01) at 0.951 against the bar `replay_min_deflated_sharpe`. 66 rows could not be worked out again from what was stored, and none of those had passed mark 3. The output is `research_rig/ledger_count_check.json`.
- The held-back slice was looked at more than once for the same rules: the first run, the cross-checks, the diagnostic, a try with fewer shuffles, and the rerun. Only the rerun is covered by the owner's exception. The slice is no longer fresh for any rule tested, and a practice account is the only fresh test left for them.
- The plans for replay 01 and pilot 02 were pushed in the same commit as their results (b393482). They were written before the runs, and the repo cannot prove it.
- The wider spread for pass mark 3 and the independent audit of every replay were written into `research_rig/README.md` as steps to follow. They are proposals 3 and 4 below and are not approved. The wording there now says so.

Corrections to other pages:

- The notes added to playbook pages 00 and 02 said every day trading rule lost to fees. MEASURED from `research_rig/results_v2.json`: none passed. At every venue cost but the lowest, all 16 rule and coin pairs lost money in the held-back years. At the lowest cost 14 of 16 did. Both notes are corrected and dated.
- Playbook pages 04, 05 and 06 had no dated note. They have one now.
- Every script that reads raw data defaulted to a folder on the research machine, so a fresh copy of the repo could not run them and gave no reason. Defaults now sit in `research_rig/data/`, `research_rig/check_data.py` says what is missing and how to fetch it, and `research_rig/README.md` has the table. Only path lines changed in the run scripts.
- `docs/STATUS.md` and `docs/research/25_what_the_evidence_supports.md` listed two different test queues. The one in force is in `docs/STATUS.md`.
- Terms and test names were used without being defined. `docs/GLOSSARY.md` defines them.

Still open, and only the owner can close it: `AGENTS.md` names the playbook as the second read and as the default source, and `docs/quality/00_READ_FIRST.md` names it as the winner on evidence. Research may not edit either file. The exact lines and the proposed wording are in `docs/decisions/morning_list_2026-11-25.md`, item 5.

## Second addendum, 2026-11-25 09:11 UTC: what two more cold readers and a fresh-copy test found

After the first addendum was pushed (commit c7956c4), the repo was copied fresh and every builder and check was run in the copy, and two more fresh models read that commit on clean machines. This is what they found. The text above is left as it was written.

- Three document builders deleted the dated correction notes from documents 12, 12b and 15 when run again, because the notes had been added to the pages by hand and not to the builders. Document 24 no longer matched its builder. All four are fixed, and `python3 tools/check_repo.py --builders` now fails if any built page differs from what its builder writes.
- The owner's rerun rule was written into `research_rig/README.md` and `docs/GLOSSARY.md` more widely than he wrote it. His words: "when a machine check proves the engine itself was wrong". The pages said "the engine or the code". Rerun R1 followed engine faults. The corrected run of replay 05, R2, did not: the engine was right and rule I2 was coded differently from its plan. Research reran before asking. Both pages now quote him, the first run of replay 05 stands until he answers, and it is question 18 in `docs/decisions/morning_list_2026-11-25.md`.
- Ledger row R1 said the hourly rerun was done in one go. Document 16 records that it stopped twice on program errors and was started again. The row now says so. Whether any figure was seen at those stops was not recorded.
- No stored output carried its command, commit or input fingerprints, which `docs/quality/01_the_bar.md` asks for. `research_rig/provenance.json` rebuilds that after the fact. MEASURED from it: no input file was modified after the output that used it was first stored. It cannot prove the bytes at run time.
- `research_rig/README.md` listed `compare_v1_v2.py` and `noise_pbo.py` among the scripts that read the held-back slice. Read from the code: the first reads stored outputs only and the second draws random numbers. It left out `report_01d.py`, `diag_x2_pbo.py` and `score_02.py`, which do read held-back prices. Corrected.
- `i2_2020_note.py` was run once more after its path line changed. Output identical. Disclosed in the ledger and not counted.
- Document 16 said the engine has 27 fixture checks. Counted from the code: 19, numbered up to 27.
- Rule and practice were mixed. The front page, the rig's "How to add a test" and the playbook notes now say for each line whether it is the owner's rule, research practice or a proposal.
- `docs/decisions/0002-historical-testing-and-risk-posture.md` proposed counting a replay of a model on dates after its training cutoff. `AGENTS.md` hard rule 7 says only forward paper or shadow results count. Hard rule 7 stands, and it is question 19.
- Never put to the owner and now on his list: the two scope calls of 2026-11-24 (14, 15), whether a stored test may be run again unchanged as a check (16), and what "within tolerance" means in the practice and live gates (17).
- `rig2.py` cannot yet judge a one-rule test or check stock bars. Measured and written in `research_rig/README.md`.

## Third addendum, 2026-11-25 09:31 UTC: what a sixth cold reader found

After the second addendum was pushed (commit 17f250c), one more fresh model read the repo cold on a clean machine. This is what it found and what was changed. Nothing here is an owner decision.

- `research_rig/export_dashboard.py` replayed five already-tested rules on the whole price history, held-back years included, every time it ran, to draw the curves on the owner's screen. `research_rig/README.md` said it only read output files. It ran several times and the count was not recorded. It checked each figure against the stored results and made no new number. It now reads saved curves and replays nothing unless given `--resimulate`, which is a held-back run. Disclosed in `research_rig/TRIAL_LEDGER.md`.
- The owner's screen showed the stock test with the corrected run's verdict and examples. It now leads with the first run, which is the one that stands.
- Document 22 gave its bottom-line figures without saying which run each came from. It now names the run on each, and says which figures are the same in both.
- One line in the ledger still gave the owner's rerun rule more widely than he wrote it. It now quotes him.
- Question 18 recommended conditions that the corrected run of replay 05 did not meet: its ledger row was added after the rerun, and the auditor had measured the effect of the correction before it was written. The question is now in three parts. Research recommends that the first run of replay 05 stands (18b).
- The rerun after the code audits (R1) rests on research's reading of "machine check" and "the engine itself". The owner was never asked. That is now question 18c, and both words are in `docs/GLOSSARY.md` with the two readings.
- Several lines called research practice a rule, and the playbook notes called every line a proposal, including lines that repeat `AGENTS.md` hard rules. Both are corrected. The owner's lines in `docs/quality/01_the_bar.md` are written for the Builder; research applies them to itself by choice, and the pages now say so.
- `research_rig/provenance.json` left out one output, called every input "held-back", and stated the commits of the code without saying they were not measured. Corrected, and the record says what it cannot prove.
- Document 24 and the status table called a 34-minute sample "overnight". They now give the length.
- There was no page saying how an owner decision gets recorded. `docs/decisions/README.md` is that page.
- The two draft plans did not say everything that has to be settled before they are frozen. They do now.

Found the same morning, not by the reader: the workspace's own price history has one-minute and daily stock prices. No rule has been run on it. It is in `docs/research/10_historical_data_and_practice.md`, "Price history inside the workspace", and item 6 of the things only the owner can do.


## Fourth addendum, 2026-11-25 09:44 UTC: what a seventh cold reader found

After the third addendum was pushed (commit 80e5875), a seventh fresh model, from a different maker, read the repo cold on a clean machine. Its verdict was that the status page could not yet be trusted as the governing account of what counts. This is what it found and what was changed. Nothing here is an owner decision.

- The rerun after the code audits (R1) was described as engine fixes. Three rows of its change list are not engine fixes: A12 changed the code of rule P2 to match its plan, A13 made pass mark 1 stricter, and A08 changed what holding pays. The hourly part also stopped twice and was restarted, and the ledger row was late. Document 16 and the owner's screen said "no rule, cost or pass mark was changed". That was wrong and is corrected in both.
- The ledger rows for replay 04 and for the first run of replay 05 were added after those runs started. `AGENTS.md` hard rule 8 says a result without a row before the run does not count. This had been recorded as a slip with no statement of what follows from it.
- Taken together: every pass recorded on 2026-11-25 came from a run that broke one of the owner's rules or one of research's own. Research now recommends that no pass from that day is credited, that fails stand, that every number is kept as a measurement, and that every trial is counted. That is question 18b in the morning list. This supersedes the recommendation in the third addendum that the first run of replay 05 "stands".
- Question 18c now proposes meanings for "machine check" and "the engine itself" so that a rerun for an engine fault cannot carry other changes with it.
- The third addendum, the ledger, the status page and the dashboard page said the script behind the owner's screen checked "every figure" and "made no new number". It compared four whole-sample figures and, for the daily charts, the trade count. The curves, yearly figures and trade lists on the screen came out of those replays, are held in no stored output and are checked by nothing. All four pages are corrected. Question 16 is now 16a (from now on) and 16b (what already happened).
- The saved curves file also held each chart's verdict, so a change in the stored results could have left a stale verdict on the screen. The verdict is now worked out from the stored results on every export.
- `i2_2020_note.py` was described as rerun "unchanged". One line of it had changed. It runs no rule. The record now says both.
- `research_rig/provenance.json` left the shared fixture files and the thresholds file out of the code lists for four outputs, and `tools/check_repo.py` did not fail when the provenance check failed. Both corrected.
- Question 17 treated the practice gate and the live gate as one. They are two gates with different things to measure. Neither says what is measured or in what unit. The question now asks for the measures first and the allowed amounts second.
- Question 19 said a forward test "costs nothing but time". Model calls cost money and need the owner's number for `api_model_spend_cap_usd_month`. Corrected, and `docs/playbook/00_START_HERE.md` now carries a dated correction where it repeated the proposal that conflicts with hard rule 7.
- The draft plan for replay 07 needs dividend history for its night-only rule N5. The workspace's own price history has none. So the statement in the third addendum's last paragraph and in document 10 that replay 07 "may not need a purchase" was too wide: on that data alone it would run without N5, and the plan must say so before it is frozen. Both draft plans also said they are frozen "on the day the price data is in hand". They now say every gate must be met.
- Document 10 still recommended a different data purchase in its closing list than the one put to the owner. That line now carries a dated note.
- The glossary named a file that does not exist as the first engine. Corrected to `engine.py` with `passmarks.py`.
- The morning list packed questions 14 to 19 into table cells that could not be read. They are now one short block each. Decision 4 is split into 4a and 4b, and the question about hard rule 9's config key is its own question, 20.
