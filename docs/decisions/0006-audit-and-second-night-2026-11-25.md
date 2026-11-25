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
