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
- Never put to the owner and now on his list: the two scope calls of 2026-11-24 (14, 15), whether a stored test may be run again unchanged as a check (16), and what "within tolerance" means in the practice and live gates (17). (Note added later the same day: question 16 is now 16a and 16b, and question 18 is now 18a, 18b and 18c.)
- `rig2.py` cannot yet judge a one-rule test or check stock bars. Measured and written in `research_rig/README.md`.

## Third addendum, 2026-11-25 09:31 UTC: what a sixth cold reader found

After the second addendum was pushed (commit 17f250c), one more fresh model read the repo cold on a clean machine. This is what it found and what was changed. Nothing here is an owner decision.

- `research_rig/export_dashboard.py` replayed five already-tested rules on the whole price history, held-back years included, every time it ran, to draw the curves on the owner's screen. `research_rig/README.md` said it only read output files. It ran several times and the count was not recorded. It checked each figure against the stored results and made no new number. (Wrong on both counts. See the fourth addendum below.) It now reads saved curves and replays nothing unless given `--resimulate`, which is a held-back run. Disclosed in `research_rig/TRIAL_LEDGER.md`.
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

- The rerun after the code audits (R1) was described as engine fixes. Two rows of its change list are not engine fixes: A13 made pass mark 1 stricter, and A08 changed what holding pays when the break-even cost is worked out. (Corrected the same morning after an eighth reader checked the code: this line first also named A12 as a change to the code of rule P2. A12 is in the engine's 0.10 band check. It is an engine fix that changes the trades of one rule.) The hourly part also stopped twice and was restarted, and the ledger row was late. Document 16 and the owner's screen said "no rule, cost or pass mark was changed". That was wrong and is corrected in both.
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
- The glossary named a file that does not exist as the first engine. Corrected to `engine.py`. (This line first said `engine.py` with `passmarks.py`. No such file exists. An eighth reader found it.)
- The morning list packed questions 14 to 19 into table cells that could not be read. They are now one short block each. Decision 4 is split into 4a and 4b, and the question about hard rule 9's config key is its own question, 20.

## Fifth addendum, 2026-11-25 09:58 UTC: what an eighth cold reader found

After the fourth addendum was pushed (commit 47bd710), an eighth fresh model, from a third maker, read the repo cold on a clean machine. Its verdict: the status page can be trusted as the governing account, the pages around it still contradicted it, and the morning list did not follow the owner's own rules for how a decision is put to him. It traced five numbers on the status page to their stored output files and all five matched. What it found, and what changed:

- The fourth addendum's account of rerun R1 was itself wrong in one place. It called change A12 a change to the code of one rule. A12 is an engine fix: the shared check in the engine now follows the plan's words, and only rule P2's trades change. The two changes in R1 that are not engine fixes are A13, which made pass mark 1 stricter, and A08, which besides fixing a search limit changed what holding pays when the break-even cost is worked out. Corrected in the status page, the ledger, document 16, document 25, the glossary, the morning list and the owner's screen.
- Four pages still called the bitcoin results passes without saying that research recommends they are not credited: two playbook notes, decision record 0001 and one glossary line. Corrected.
- One playbook line gave `AGENTS.md` hard rule 13 as a recommendation with a condition. It now gives the rule as it is. Fifteen playbook lines that repeat a hard rule now say so on the line. The build page now says its "MVP", "defer" and "only after" lines predate the owner's bar that the whole product is in v1.
- The morning list quoted two lines of `AGENTS.md` in short form, and its proposed wording would have dropped a clause from each. They are now quoted in full and nothing is removed. The question about one line of `docs/quality/00_READ_FIRST.md` was folded into that item and is now its own question, 21.
- The morning list put decisions 1 to 13 in a table with empty cells and gave decision 10 no plain recommendation. Each is now a short block with the recommendation, the reason, what a yes approves and what it does not. Decisions 8 and 12 asked about numbers without showing them. A new tool, `tools/owner_numbers.py`, writes them from `config/thresholds.yaml`, and `tools/check_repo.py` fails if they go stale. The page now opens with the four things research would ask first, the same four as on the status page.
- `tools/check_repo.py` checked paths in five files only. It now checks the glossary, the dashboard notes and every page under `docs/decisions/`, `docs/playbook/` and `docs/research/`. That found six more paths written in short form, now written in full. Its first lines say what it still does not check.
- `research_rig/README.md` did not say that the provenance check fingerprints outputs and inputs and not the code files it lists. It does now.
- Lines that said a collection or a sampler "is running" had no date. They are dated. Document 10 still named Bitstamp as the main crypto history, and now carries a note that Kraken's published files are the proposed main one.
- The draft plan for replay 07 was missing three things the draft for replay 06 already had. They are added.
- The status table's order-book row said the crypto replays assume a figure that is stored in only one of their outputs. The row now says where the figure is read from.
- Thirteen terms used in the repo were not in the glossary. Added.

Not changed: `AGENTS.md`, the owner's files in `docs/quality/`, the audit reports, any stored result, any threshold. No rule was run.

## Sixth addendum, 2026-11-25 10:07 UTC: a ninth reader on the morning list alone

After the fifth addendum was pushed (commit 1aa4d69), a ninth fresh model read only what the owner will read first, the morning list, and checked it against the files behind it. It confirmed that the two number tables match the config file, that the four items under "Start here" match the status page, and that the quoted rules and line numbers are right. What it found, and what changed:

- Decision 1 recommended two changes to pass mark 4 as one, and called the pair "steadier". One of the two, counting a tie as half, makes the mark easier to pass, and the audit had kept the stricter count for that reason. Results had been seen. This was a recommendation to loosen a mark without saying so. It is now two decisions. Research recommends yes to fixed start dates (1a) and no to the easier tie count (1b). Document 16's own recommendation is corrected with a dated note. This changes a recommendation, not a result or a number.
- The item on `AGENTS.md` said its lines were quoted in full and that nothing was removed. Line 3 was quoted without its first and last sentences, and the last is the one that says `AGENTS.md` wins every conflict. It is now quoted whole and that sentence is kept word for word. The page now says plainly what does change.
- "Start here" said three answers unblock the stock tests and the practice record. Each of those also needs its own yes. It now says so, and says no practice trading starts on the keys alone.
- Decision 8 said the three bars "did their job", which contradicted decision 2 on the same page. It also did not say which form of pass mark 1 was being approved, and the bar for mark 4 was not put to the owner anywhere. All three are corrected.
- Question 18b listed the runs with a problem but left out the first run of the bitcoin and ether tests, the two restarts of the hourly rerun, and the fact that keeping the fails is research's choice and not what hard rule 8 says when read strictly. Added.
- Two data collections were started overnight without asking the owner, and neither was listed as a slip. Both are now in the status page and in the morning list under "What research got wrong".
- Several lines read stronger than the status page: "the one lead worth following", "turns the stock index result into something that could be traded", a practice record that "starts the count", and "the honest next month", which is a time prediction. Each is reworded.
- No block ended with the recommendation, which the owner's rules ask for. Every block now ends with it. Items 2, 3, 4 and 6 of "Things only you can do" now say what a yes covers. Item 1 now says where the practice keys go.
- Counts and one config value typed into the page are replaced by pointers to the status table and the key.

Not changed: `AGENTS.md`, the owner's files in `docs/quality/`, any stored result, any threshold. No rule was run.

## Seventh addendum, 2026-11-25 10:13 UTC: a tenth reader on the rewritten morning list

After the sixth addendum was pushed (commit efcde2e), a tenth fresh model, from a different maker than the ninth, checked the rewritten morning list against the files behind it. It confirmed the quoted rules, the line numbers and the two number tables. What it found, and what changed:

- The new decision 1b, and document 16 before it, said a tie in pass mark 4 can only happen with an odd number of rules. The code gives equal results the average of their ranks, so with an even number a tie still happens when two rules have exactly equal results. Corrected in both. The page also suggested picking an even number of rules to avoid ties. That would be choosing rules to steer a statistic, and it is removed. Both draft plans now say a rule is never added or dropped for that reason.
- Decision 1a said the fixed set of start dates would "most likely" turn the bitcoin results back to fails. The one measurement behind that used the first-run code on one price history at a higher cost. The effect is now given as UNKNOWN, and the page says the method does not make the mark steady. Document 16's line that it "removes the knife edge" is corrected the same way.
- Decision 8 said no result argues for a different bar. That was a judgment. The values are rules of thumb and none is calibrated. They are now asked for as provisional. The decision also described the late-fill form of pass mark 1 as applying to the crypto rules in general. It applied to the daily rules only (amendment row A13), and it is not part of the decision.
- "Start here" tied all three first answers to all three next steps. Each next step now lists only what it waits on.
- The item on the data purchase called it the only source found for dividend history. Other vendors in `docs/research/10_raw/stock_history_data.md` have it too. Corrected.
- The item on the workspace's price history gave a start date for one-minute data that is not in the repo. It is now marked interim.
- Question 16a asked for a rerun check where the code is "shown by its commit". The provenance record says it cannot show that for last night's runs. The proposal now covers only runs that record their own code and inputs when they are made.
- Question 17 would have set the allowed amounts after seeing practice results that then count. The first weeks now do not count toward the gate.
- Question 18b's lead said every run broke a rule. It now says every pass came from a run with a problem, and its three parts can be answered separately.
- "What research got wrong" left out five things that are on the status page. Added, one line each.
- Several blocks bundled separate asks. Each now says the parts can be answered one at a time.
- `research_rig/AMENDMENT_2026-11-25_audit_fixes.md` says pass marks and costs do not change, which its own rows A13 and A08 contradict. Its first lines allow a dated note at the bottom. That note is now there. Nothing above it was changed.
- The descriptions of pass marks 3 and 5 in the number table said "at least" where the code asks for "above". Corrected.

Not changed: `AGENTS.md`, the owner's files in `docs/quality/`, any stored result, any threshold. No rule was run.

## Eighth addendum, 2026-11-25 10:32 UTC: a check of the last fixes, a finding test, and the practice and insider drafts

Four things happened after the seventh addendum (commit 7596e22).

A draft plan for the practice account was written (`research_rig/PRACTICE_01_two_rules_observation_DRAFT.md`). It runs nothing. Writing it showed a gap in the morning list: item 1 said research would connect to the practice account and decision 5 spoke of placing practice trades, and neither said who sends the orders. `AGENTS.md` hard rule 1 keeps every model out of the order path, pretend money included, and hard rule 13 keeps tools that can cancel orders or close positions away from agents. Item 1 and decision 5 now say research reads only, that pretend orders would come from a plain timer program with no model in it, and that research does not hold a key that can trade. Item 1 had also said practice keys work only on Alpaca's practice address. Alpaca's page says only that the practice account has its own key. Corrected, and the rest marked UNKNOWN.

A fresh model checked every change since the sixth addendum (commits efcde2e to 50a8f2b) for errors of fact, contradictions and asks that were wider than what they said they approve. It found eight. All eight were checked against the files and fixed:

- The practice draft said replay 05 had month-end values only. It had daily closes, checked the rule at month end and filled at the next day's close.
- The questions table in document 16 still said fixed start dates would "most likely" turn the bitcoin passes into fails. The seventh addendum had changed that to UNKNOWN elsewhere. Now the same there.
- Two lines in the morning list still spoke of an AI test "in the practice account". Decision 10 makes it a shadow test with no orders. Both lines now say so.
- Question 17's guard was missing from its approving line, and three pages that mention whether early practice days count did not point to it. Added.
- The approving lines of decision 11 and of item 6 were narrower than what they proposed. Widened to match, with the parts answerable apart.
- "Start here" item 4 described question 18b as one yes or no. It has three parts. Corrected.
- Item 1 left open that research might hold a full key. It now says research does not.

Three fresh models, from three makers, were each given only the repo address and sixteen questions a new agent has to be able to answer: what the state is, what must not be run, where a number lives, what waits on the owner, who may change which file. The questions and the expected answers were written down before any of them started. The two that have reported answered all sixteen correctly, most from the first three files. The third had not reported when this was written. What they said slowed them down, and what changed:

- The owner's files still route a reader to the playbook first. That is item 5 of "Things only you can do" and is not research's to change.
- No page said plainly that every file in `docs/quality/` is the owner's. `README.md` now has a short section, "Files you do not change", and `docs/INDEX.md` says it at the head of that folder's table.
- `docs/INDEX.md` listed the glossary under the wrong folder. Moved.
- The index sent anyone asked to rerun a test through three documents. It now has its own row with the short answer: do not run it.
- `research_rig/README.md` told a reader how to rerun a test if the owner says yes to question 16a, without saying his yes would not cover last night's runs. It now says so.
- The replay 05 report said eight rules cannot tie. They can. No tie occurred, and the line now says that.

A researcher read what came after the 2012 paper on insider buying, and research opened the main sources again (`docs/research/26_insider_buying_evidence.md`). The case is weaker than decision 11 made it sound, and decision 11 now says so. One figure in the researcher's notes was wrong and was corrected before it reached the page. A draft plan that runs nothing is `research_rig/PREREG_08_insider_buying_DRAFT.md`.

Not changed: `AGENTS.md`, the owner's files in `docs/quality/`, any stored result, any threshold. No rule was run and no price data was downloaded for the insider idea.

## Ninth addendum, 2026-11-25 12:41 UTC: the stock price collection finished and was gap-checked

This is a record of what research did. It is not an owner decision.

The pull of stock prices from the workspace's own price history, started overnight under the owner's latitude, finished. It holds one-minute prices for SPY and QQQ and daily prices for the funds named in the draft fund plan and some more that no plan names yet (wording corrected in the eleventh addendum). The files are on the research machine only.

What was added to the repo:

- The two scripts that joined the pulls and checked them for gaps (`research_rig/platform_bars_consolidate.py`, `research_rig/platform_bars_integrity.py`). The check was run again from the repo copy and gave the same output file, byte for byte. MEASURED.
- A summary with dates, counts and file fingerprints and no price (`research_rig/platform_bars_coverage.json`), and a script that writes the coverage tables in `docs/research/10_historical_data_and_practice.md` from it (`tools/bars_coverage.py`). `tools/check_repo.py` now fails if those tables are not what the script writes.
- The price files are in `research_rig/provenance.json` by fingerprint and in `research_rig/check_data.py` as a data set that a script cannot fetch.

What the check showed, in words (the figures are in the tables; MEASURED, on files only the research machine has; wording corrected in the eleventh addendum): no repeated time and no missing or zero price; some rows with no volume and a few rows not on a whole minute; some short days and some missing days in the SPY one-minute files; one-minute history for QQQ starts years after SPY's. The draft plan for the day trading test now names that as a point to settle before it is frozen.

What is still UNKNOWN: whether the prices are right (nothing has compared them with a second source), whether the check's holiday calendar is right (the collecting agent wrote it from memory), who the data comes from, how it is adjusted, and what its terms say about keeping copies.

Not done, STATED by research: no rule was run on these prices and no return was worked out from them. No price was committed, which the repo history shows. Item 6 of "Things only you can do" in the morning list asks the owner whether the files may be kept, and says research deletes them if he says no.

Not changed: `AGENTS.md`, the owner's files in `docs/quality/`, any stored result, any threshold.

## Tenth addendum, 2026-11-25 12:43 UTC: the third finding-test reader, and a hole in the repo check

This is a record of what research did. It is not an owner decision.

The third fresh model in the finding test reported. It answered all sixteen questions correctly against the answer key, so three models from three makers each did. MEASURED by research against a key research wrote; the key and the answers are not in the repo. It read the repo before the eighth addendum's fixes were pushed, and three of the faults it listed were already fixed by them. Two were new:

- The repo check did not do what three pages said it did. It was meant to fail when a tracked file has no row in `docs/INDEX.md`. It passed a new file under `docs/research/` or `research_rig/` with no row, because the index names those folders in passing and the check took any folder named anywhere on the page as covering everything under it. The reader showed this with a throwaway file. Research confirmed it, then changed the check: only a path or folder in the first column of a table row counts. Tested both ways with a throwaway file in each folder: the check now fails, and passes again when the file is removed. MEASURED. No tracked file turned out to be unlisted.
- The status page did not say that no pass is credited until after the results table, whose rows say "pass". It now says so above the table.

Left as they are, with the reason: the reading order in `AGENTS.md` still points to the playbook first (the owner's file, item 5 of "Things only you can do"); the status page gives the bar a test was run with and the config file gives the value in force (by design, so a number lives once).

What this test does and does not show. Three fresh models found the right answer to sixteen set questions from the repo address alone (MEASURED as above). It does not show that a model would follow the rules under pressure, or find what the questions did not ask about. Every round of outside reading so far has found a real fault, this one included.

## Eleventh addendum, 2026-11-25 12:55, added to at 13:04 UTC: a second check on the collected stock prices, and the faults an outside check found in the first

This is a record of what research did. It is not an owner decision.

What was run, under the same overnight latitude as the collection itself:

- `research_rig/platform_bars_crosscheck.py`, once. For SPY and QQQ it rebuilds each day's open, high, low and close from the one-minute files and compares them with the daily file. Its bands were fixed in the script and pushed before it was run (commit 22b0f2a). It runs no trading rule and works out no return over time. Its output, `research_rig/platform_bars_crosscheck.json`, holds counts, dates and gaps in basis points, and no price.
- `research_rig/platform_bars_integrity.py`, again, after the calendar fixes below.

What the comparison showed, in words (the figures are in the tables in `docs/research/10_historical_data_and_practice.md`; MEASURED, on files only the research machine has):

- The yearly middle gap between the two closes stays small. Research's reading, not a measurement: the two sets of files look to be adjusted the same way. It does not say which way.
- On some days a one-minute high is above the daily high or a one-minute low is below the daily low, which cannot be if both files are right. Which file is wrong is not shown.
- Both sets come from the same lookup, so none of this shows that either is right.

An outside model read the commits that added the coverage work (a832c01 to f5079be). What it found, and what was done:

- The pages said the daily files cover the funds named in the two draft stock plans, with a typed count. Wrong: only the draft fund plan names funds, and it names fewer than were collected. Reworded with no count in document 10, the morning list, the ninth addendum and the rig's README.
- "No repeated or broken rows" said too much: there are rows with no volume and rows not on a whole minute. Reworded to what was counted.
- The check's calendar had some days as both a holiday and an early close, and missed one early close in December 2003. Fixed in the script. The December 2003 close is from the exchange's own record of special closings, linked in document 10. Research then compared the script's early closes with that record for September 2003 to December 2007: they match. MEASURED. After 2007 the calendar is still unchecked.
- The days with no SPY one-minute data were trading days, and some short days fall on days of known halts. The sources are in document 10.
- The script that keeps the tables in step with the summary looked at the first block only. It now requires exactly one block. The repo check now also fails if the file fingerprints in the summary do not add up to the two in `research_rig/provenance.json`.
- The repo check counted a file as listed if it was named in any table on the index page, the task table included. Now only a row in a file table counts.
- `research_rig/check_data.py` looked for two of the price files. It now looks for every file the summary names.
- Several sentences gave a cause, a judgment or a typed time as if measured. Reworded or labelled.
- The join script has limits that cannot be fixed without collecting again. They are now listed in document 10 and not fixed.

Added by research while fixing these: the gap check now also counts rows without six fields and values that are not finite or are below zero. It found none. MEASURED.

What changed for the owner: item 6 of "Things only you can do" now says the two sets of files disagree on some days. The draft plan for the day trading test says a rule for those days has to be written before it is frozen.

A second outside model then read these fixes (commits 22b0f2a to afbe506). It opened all five linked sources and found each supports its sentence, tried four ways to break the repo check and failed, and found the calendar right for the span of the data. STATED by that checker. It also found faults, now fixed:

- Research had written that the one-minute files hold bad bars, as if measured. The comparison shows only that the two files disagree in a way that cannot be if both are right. Reworded everywhere, with research's view labelled as a view.
- The script wrote "does not grow going back in time" into the table text with nothing computing it. The script now states only the yearly figures. The reading is in the prose, labelled as a reading.
- The comparison did not leave out short days, where a gap is to be expected. The table text now counts how many of the large gaps fall on short days, and the prose says so.
- The new count of rows without six fields would have stopped with an error on a short row. Fixed and tried on made-up rows. MEASURED.
- A sentence gave a wrong last year for the early closes that run past 13:00, and the halt on June 1, 2005 was given as the cause of a short day whose data stops before the halt. Both reworded.
- Two limits listed as not fixable were limits of the gap check, which can be rerun. Both are now fixed and the check was run again.
- Smaller ones: a script listed twice in the index, a docstring that named a price the file does not hold, and typed counts in two sentences.

Not done, STATED by research: no rule was run on these prices and no return over time was worked out from them.

Not changed: `AGENTS.md`, the owner's files in `docs/quality/`, any stored result of a test, any threshold.
