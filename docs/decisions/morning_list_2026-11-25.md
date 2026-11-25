# Morning list, 2026-11-25

Written by research at the end of the overnight run. Rewritten at 08:36 UTC after the audits and the second set of tests, corrected at 08:51 UTC after three fresh models read the repo cold, rewritten again at 09:29 UTC after three more did, corrected at 09:44 UTC after a seventh, and put in a new order at 09:55 UTC after an eighth. Status: proposed. Nothing here is an owner decision. The record of the night is `docs/decisions/0005-overnight-research-2026-11-25.md` and `docs/decisions/0006-audit-and-second-night-2026-11-25.md`. The current state, with every result, is `docs/STATUS.md`. How your answers get recorded is in `docs/decisions/README.md`.

## The short version

- No rule has a credited pass, and nothing tested or read supports fast money. The detail is under "Where things stand".
- Four things from you unblock the most. They are under "Start here", next.
- Research slipped against your rules several times overnight. Each slip is written down under "What research got wrong". Every pass in the table came from a run with one of those slips in it, so research recommends that none is credited (question 18b).
- The repo now has a map, a status page, a glossary and a checker, and has been read cold by eight fresh models. Every round found real faults. The ones found are fixed and recorded. Expect more.
- Plain meanings of the words on this page are at the very end, under "Words used in this list".

## Start here

Four things, one at a time, in this order. The first three unblock the two stock tests and the practice record, which are the things that could change this picture. The fourth settles what last night's numbers are called.

1. Practice account keys. Item 1 under "Things only you can do". A yes approves practice trading with pretend money and nothing else.
2. The data purchase. Item 2 in the same list. $29.99 for one month.
3. Decision 1: how pass mark 4 is measured. Research recommends the steadier way. A yes changes how new tests are judged and does not move the bar.
4. Question 18b: which of last night's results are credited. Research recommends no pass is. A yes means no rule is called passed and every figure stays as a measurement.

Everything else on this page can wait for those four.

## Where things stand

No rule has a credited pass. Results are in the table in `docs/STATUS.md`, which is written from the output files. In words:

| Test | What happened | Full write-up |
|---|---|---|
| Slow trend rules on bitcoin and ether | Some bitcoin rules clear the five marks on both price histories (named in the status table), at the lowest venue cost only, only in the rerun after the audits, and within a hair of the bar on one mark. No ether rule does. Research recommends the rerun is not credited as a pass (question 18b) | `docs/research/16_rig_audit.md` |
| Day trading rules on bitcoin and ether | None pass at any venue cost. Most show a small gain per trade before fees, and none stays ahead of holding the coin at twice the lowest fee modeled | `docs/research/16_rig_audit.md` |
| Trend rules on a wide basket of coins | None pass. The basket grew far less than holding bitcoin | `docs/research/23_replay_04_coin_basket.md` |
| Slow trend rules on the US stock market from 1927 | Two runs, because an audit found one rule's code did not match the plan. First run: no rule passes at the two lower cost levels. Corrected run: several rules pass at every cost level (named in the status table). No rule passes in both runs at every cost level. Research recommends that neither run is credited as a pass (question 18b) | `docs/research/22_replay_05_stock_trend.md` |
| AI models making the daily call | Inconclusive, as the plan said before it ran | `docs/research/14_ai_calls_pilot_02.md` |
| What it costs to trade a small size | Sampled on two venues on one day. Interim | `docs/research/24_order_book_costs.md` |

What the tests agree on, and what real funds built on the same rules also show: slow trend rules cut the worst drop and give up some growth. That is a smoother ride. It is not fast money. The reading on traders, funds and AI systems with real money says the same (`docs/research/25_what_the_evidence_supports.md`).

The one lead worth following on stocks: in the corrected run, which research recommends should not be credited (question 18b below), the rule that holds the three strongest industry groups when the market is above its ten-month average grew nearly as much as holding, with a much smaller largest drop. It carries three cautions, listed in `docs/research/22_replay_05_stock_trend.md`. It has not been tested on anything that can be bought.

What has not been tested at all: funds that can be bought, and day trading SPY and QQQ. The first waits on a data purchase. The second waits on your answer to item 6 below or on the same purchase. Both also wait on decisions 1, 4a and 4b.

## Things only you can do

In this order. None uses real money for trading.

1. Open an Alpaca account for practice trading and create practice keys. This approves practice trading only. It does not approve funding the account. Detail is in `docs/research/09_brokers_and_venues.md`.
2. Buy one month of stock price data. Research recommends the EODHD plan with daily and one-minute prices, $29.99 for the month ([EODHD pricing](https://eodhd.com/pricing/)). It is no longer the only way to get one-minute stock prices (item 6), but it is the only source found for dividend history, which the fund test needs, and it gives a second source to check the first against. A second source changed a result once already. Terms for keeping the files are in `docs/research/10_historical_data_and_practice.md`.
3. Say whether Kraken's published price files may be the main crypto history. Research recommends yes. Bitstamp's terms are unclear about collecting its prices.
4. Say whether the order-book sampler may run again on Kraken's public price feed. Kraken's general terms bar automation on its content ([Kraken Global Terms](https://www.kraken.com/legal/global-terms)). Research reads the documented public feed as offered for this use. That is research's reading, not Kraken's word. As of 09:55 UTC on 2026-11-25 the sampler was still running. It stops by itself at about 16:30 UTC and will not be restarted without your yes. The figures in the repo so far cover its first 34 minutes.
5. Say whether `AGENTS.md` and `docs/quality/00_READ_FIRST.md` may be changed so that they point to `docs/STATUS.md` and `docs/INDEX.md`. `AGENTS.md` says any change to it needs you, and the quality files are yours, so neither was touched. The exact lines are under "Item 5 in detail" near the end of this page. A yes approves those five wording changes and nothing else. Three fresh models read the repo cold on 2026-11-25 and all three named this as the thing most likely to send a new model the wrong way.
6. Say whether stock prices from this workspace's own built-in price history may be used and kept for tests. Found on 2026-11-25: it returns one-minute prices for SPY back to September 2003 and daily prices for funds back to their first day. It has no dividend history, so on its own it cannot run either stock test exactly as drafted: the fund test needs dividends throughout, and the day trading test needs them for its one night-only rule. As of 09:55 UTC on 2026-11-25 research was collecting it on the research machine and checking it for gaps. No rule has been run on it, and none of it is in the repo. What its terms say about keeping the files is UNKNOWN to research. You work at Perplexity and can ask. Detail is in `docs/research/10_historical_data_and_practice.md`, "Price history inside the workspace".

## What research got wrong

For you to know. Each is also in `docs/STATUS.md` under "Known faults and slips".

- Two second runs of tests were reported as reruns but were not written in the trial ledger or counted as trials, which your rule requires. The rows are there now, marked late. Counting them was checked on the stored results and turns no pass into a fail. The closest call is in the "Trial count check" row of the table in `docs/STATUS.md`.
- The second run of the stock test fixed one rule's code, not the engine. Your rule names the engine only. Research reran before asking you, and for a while its pages gave your rule more widely than you wrote it. They now quote you. Questions 18a and 18b.
- The rerun of the bitcoin and ether tests was reported as engine fixes only. It carried two changes that were not engine faults: a stricter pass mark, and what holding the coin pays in one of the marks. It also rests on research's reading of "machine check" and "engine", which you were never asked about. Questions 18b and 18c.
- Stored tests were repeated without your yes: one small script once, and the script behind your screen several times. The first gave the same file. The second made the curves and trade lists on your screen, which nothing checks. Questions 16a and 16b.
- Results were not saved with their command, code version and input fingerprints when they ran, which your bar asks for. That record was rebuilt afterwards and says what it cannot prove (`research_rig/provenance.json`).
- Ledger rows for the coin basket test and the first run of the stock test were added after those runs had started. `AGENTS.md` hard rule 8 says the row comes first. Their plans were pushed before. Question 18b.
- A fresh reader also found that research's own pages overstated two things: that the screen script checked "every figure", and that it "made no new number". Both are corrected.

## Decisions waiting, one at a time

Research's recommendation is given for each. The numbers are fixed so that other pages can point to them. Decision 1 is one of the four to start with.

### 1. How is pass mark 4 measured from now on?

- The issue: pass mark 4, the overfitting estimate, moved from fail to pass with small changes in start date and in the set of rules. One number should not decide.
- Research recommends: count ties as half, and measure it over a fixed set of start dates and block counts. Detail in `docs/research/16_rig_audit.md`, "Questions for the owner".
- Why: it is the steadier way, and every later test depends on it.
- You would be approving: a steadier way to measure, used in every new plan. It would most likely turn the bitcoin results back to fails. Its effect on the stock rules is UNKNOWN until a new test.
- You would not be approving: any change to the bar itself (`backtest_max_pbo`).

### 2. How is pass mark 3 measured from now on?

- The issue: in the stock test, mark 3 screened nothing, because of how its plan worked out the spread between rules.
- Research recommends: take the spread across every trial counted in the ledger, not only the trials in one plan.
- Why: that is what the mark is for.
- You would be approving: a stricter mark 3 in every future plan.
- You would not be approving: any change to the bar itself (`replay_min_deflated_sharpe`).

### 3. Does every replay get an independent audit?

- Research recommends: yes. A different model audits the code against the plan before the result is believed.
- Why: last night's audits changed results twice. Research works this way already.
- You would be approving: making that a standing rule for research.
- You would not be approving: any change to a pass mark, or any spending.

### 4a. Test next: replay 06?

- What it is: slow trend rules on funds that can be bought, with the industry rule added on sector funds.
- Research recommends: yes. Its plan and ledger rows are pushed before it runs.
- Why: it turns the stock index result into something that could be traded.
- You would be approving: one research replay, once the data purchase (item 2) is in hand and decision 1 is made.
- You would not be approving: any building, any trade, or replay 07.

### 4b. Test after that: replay 07?

- What it is: day trading SPY and QQQ on one-minute prices.
- Research recommends: yes. Its plan and ledger rows are pushed before it runs. Research expects a fail and would measure it.
- Why: it is the one day trading case not yet tested.
- One thing to know: as drafted, its night-only rule needs dividend history. On the workspace's own prices alone it would run without that rule, and the plan has to say so before it is frozen.
- You would be approving: one research replay, once one-minute prices are in hand and decision 1 is made.
- You would not be approving: any building or any trade.

### 5. Watch two rules in the practice account?

- Research recommends: yes. Run two slow rules with pretend money as observation, labelled as not passed: the bitcoin trend rule P1, and the ten-month rule on a total market fund.
- Why: the practice account is the one clean test left for rules already run on past prices.
- You would be approving: a forward record that starts the count toward `paper_min_trading_days` and `paper_min_closed_trades`.
- You would not be approving: calling either a strategy, or any real money. Neither can pass the practice gate until question 17 is answered.

### 6. Drop crypto day trading and wide coin baskets?

- Research recommends: yes, drop both.
- Why: no rule passed in either, at any venue cost.
- You would be approving: closing those two lines of work.
- You would not be approving: dropping crypto altogether.

### 7. Credit interest on idle cash in every replay?

- Research recommends: yes. Credit Treasury bill interest on cash.
- Why: trend rules sit in cash a lot, and the crypto replays credit nothing for it.
- You would be approving: one change to the test rig, with its own written plan, used in new tests.
- You would not be approving: any change to a pass mark, or running any stored test again.

### 8. Are pass marks 1, 3 and 5 your bars for research replays?

- The issue: research proposed these three bars on the first night and has judged every replay on them. They are marked "proposed" in the config file. The first table under "The numbers" below shows what each asks and its value.
- Research recommends: keep them as they are.
- Why: they did their job. Nothing weak got through on them alone.
- You would be approving: the values shown for marks 1, 3 and 5, as bars for research replays.
- You would not be approving: marks 2 and 4, which are question 20 and decision 1. Any bar for the practice account or for real money.

### 9. Broker plan

- Research recommends: an Alpaca individual account for stocks and for all practice trading. The live crypto venue is left open.
- Why: `docs/research/09_brokers_and_venues.md`.
- You would be approving: the plan in that document.
- You would not be approving: funding anything.

### 10. Test AI models making the call, going forward?

- Research recommends: not now.
- Why: no AI system with a live record was found that beat holding, the test costs model usage, and the two rule observations in decision 5 come first. If you want the question answered anyway, it runs in the practice account only, with the rules in `docs/research/11_ai_trader_experiment_design.md` fixed first and your number for `api_model_spend_cap_usd_month` set.
- You would be approving: leaving the AI test parked.
- You would not be approving: dropping it for good.

### 11. High-risk share

- Research recommends: fund it only with ideas that pass a replay. First in line: insider buying that is not routine, in listed stocks.
- Why: `docs/research/25_what_the_evidence_supports.md`.
- You would be approving: that order of ideas to test.
- You would not be approving: any penny stock or memecoin purchase.

### 12. Your open numbers

- The issue: seven numbers are yours alone and have no value. The second table under "The numbers" below lists them with research's suggestions.
- Research recommends: leave them open today.
- Why: none is needed until a rule has passed in the practice account. The model spending cap is needed sooner only if you say yes to an AI test.
- You would be approving: nothing.
- You would not be approving: any value. Nothing may assume one until you set it.

### 13. Who the Builder is and where it runs

- Research recommends: decide after a rule passes in practice, not before.
- Why: there is nothing to build until then.
- You would be approving: that this question waits.
- You would not be approving: any choice of builder, host or software.

## Questions about scope and about your own rules

These came out of the cold-read tests. Each stands alone. Answer any one without the others. Question 18b is one of the four to start with.

### 14. Is the product a fixed-rule trading service, with AI beside it for research and review?

- The issue: this scope call was written on 2026-11-24 and never put to you (`docs/decisions/0001-starting-decisions.md`, row 1).
- Research recommends: yes.
- Why: no AI system with a live record was found that beat holding, and our own pilot was inconclusive. `AGENTS.md` hard rule 1 already keeps models out of the order path whatever you decide here.
- You would be approving: the shape of the product.
- You would not be approving: any build, any software choice, or any AI test in the practice account. That last one is decision 10.

### 15. Start with slow rules, not day trading?

- The issue: also written on 2026-11-24 and never put to you (same file, row 2). Start with rules that hold for days or longer, on liquid funds and on bitcoin and ether.
- Research recommends: yes, with replay 07 kept as the one day trading test still worth running.
- Why: every test since has pointed the same way.
- You would be approving: where the first product rules come from.
- You would not be approving: dropping day trading for good. Replay 07 decides that for stocks.

### 16a. From now on, may a stored test be run again, unchanged, only to check that it gives the same file?

- The issue: your rule says never run the held-back slice a second time for the same version of a rule, and names one exception. A check that a result can be reproduced is not that exception.
- Research recommends: yes, as a check only, under these conditions. The code is the same as in the stored run, shown by its commit. The input files are the same, shown by their fingerprints. The check is written in the trial ledger before it runs. The output is written outside the repo and compared with the stored file. If it differs, the stored file is not replaced and you are told.
- Why: a result nobody can reproduce is weaker than one that can be. Nothing new is tried, so it is not counted as a trial.
- You would be approving: reproduction checks as described.
- You would not be approving: any run with a rule, a cost, a date or a pass mark changed. Until you answer, nobody runs a test script.

### 16b. What about the repeats that already happened without your yes?

- What happened, first: `research_rig/i2_2020_note.py` was run a second time. It multiplies up each industry group's daily returns for 2020, which is a held-back year. It runs no rule. One line of it, where it looks for the data, had changed, so it was not strictly unchanged code. The output was identical.
- What happened, second: the script behind your screen replayed five already-tested rules over the whole price history each time it ran. That was several times, and the count was not recorded. Each time it compared four whole-sample figures with the stored results, for the rule and for holding: growth a year, Sharpe ratio, largest drop and total return. For the three daily charts it also compared the number of trades. They matched.
- What that leaves unchecked: the curves, the year-by-year figures and the trade lists on your screen were made in those replays. No stored result holds them, and nothing checks them. They cannot be rebuilt from the repo alone, because the saved curves are kept out of it.
- Research recommends: let both stand as disclosed, and do not count them as trials. The screen now says its charts come from a replay that is not a counted result. It replays nothing any more.
- Why: no rule, cost or date was changed, and no pass or fail was read from them. If you would rather count them, say so. Research can then work pass mark 3 out again at the higher count from the stored results, without running a rule.
- You would be approving: that these repeats stand as disclosed and uncounted.
- You would not be approving: any further repeat. That is question 16a.

### 17. What do "within tolerance" in the practice gate and the live gate mean?

- The issue: `docs/playbook/00_START_HERE.md` says a rule leaves the practice account when "slippage and errors" are "within tolerance" (phase 2), and that more money waits until live results "track paper within tolerance" (phase 4). Neither says what is measured, in what unit, or how much is allowed. So today no rule can pass the practice gate, whatever it does.
- Research recommends: two steps. First, research proposes what to measure and in what unit. For practice: the gap between the price the rule assumed and the price the practice account gave, in basis points per order, and the number of orders that failed or went in wrong out of the orders sent. For live: the gap between live and practice results over the same days. Second, you set how much is allowed, after the first weeks of practice orders show what the numbers look like.
- Why: an allowed amount picked before a single order has been sent would be a guess. Practice orders are pretend. The broker simulates them and no money is at risk.
- You would be approving: that the measures get defined first, that the allowed amounts are yours to set, and that both gates stay shut until you set them.
- You would not be approving: any value today, or any real money.

### 18a. From now on, does your rerun rule cover a rule whose code does not match its written plan?

- The issue: your rule names one case for a second run of the held-back slice: "when a machine check proves the engine itself was wrong". It does not name the case where the engine was right and one rule was coded differently from its pushed plan.
- Research recommends: yes, under four conditions. An independent check proves the mismatch against the plan as it was pushed. The correction and the ledger row are pushed before the rerun. The rerun is counted as trials and reported as a rerun. Both outputs are kept.
- Why: a rule that does not match its plan tests something nobody wrote down, so without a rerun the plan's question is never answered. The conditions keep it from becoming a second try at a result someone did not like.
- You would be approving: a second kind of allowed rerun, from now on.
- You would not be approving: any rerun because a result was disappointing. Nothing from last night. That is 18b.

### 18b. Which of last night's results are credited?

- The issue: every run that produced a pass last night broke a rule, yours or research's. One line each:
- Rerun of the bitcoin and ether tests (ledger row R1). Result: four bitcoin rules clear all five marks, at the lowest venue fee only. Problem: besides engine fixes it made pass mark 1 stricter and changed what holding pays in mark 2, after results had been seen. Its ledger row was late.
- First run of the stock test (ledger rows 43 to 50). Result: no rule clears the marks at the two lower cost levels, four do at the highest. Problem: its ledger row was added after the run started, and a short preview had been looked at.
- Corrected run of the stock test (ledger row R2). Result: five rules clear the marks at every cost level. Problem: research reran before asking you, the effect of the correction was already known, and the ledger row was late.
- Coin basket test (ledger rows 51 to 55). Result: nothing clears the marks. Problem: its ledger row was late.
- Research recommends: credit no pass from last night. Fails stand. Every number stays in the repo as a measurement, and every trial is counted.
- Why: `AGENTS.md` hard rule 8 says the ledger row comes before the run and that a result without one does not count. Your Never list says no pass mark or cost changes after a result is seen. Research should not be the one to wave those through.
- What is lost: very little. A pass in a replay only means "worth watching in the practice account". Decision 5 already proposes watching one bitcoin rule and one stock rule there, labelled as not passed. The held-back years are spent for these rules, so the practice account is the one clean test left for them.
- You would be approving: that no rule is called passed, and that all the figures stay in the repo, labelled by run.
- You would not be approving: throwing any result away, or dropping these rules as leads.
- The full account of each run is in `docs/STATUS.md` under "Known faults and slips".

### 18c. What do "machine check" and "the engine itself" mean in your rerun rule?

- The issue: research reran after two other AI models audited the test code and ran their own checks. Research read that as "a machine check proves the engine itself was wrong". You have not said whether an audit by a model is a machine check, or whether the code that works out the pass marks is part of the engine.
- Research recommends: a machine check is a test with a known answer that the old code fails and the new code passes, or a second build from the raw data that disagrees. A model's opinion alone is not one. The engine is the shared code that simulates trades and works out the marks. It is not the code of any one rule, and it is not the definition of a pass mark. A rerun for an engine fault changes only what the check proved wrong.
- Why: with those meanings a rerun cannot carry other changes along with it, which is what happened in row R1.
- You would be approving: these two meanings, from now on.
- You would not be approving: anything about last night. That is 18b.

### 19. May a replay of an AI model on past dates count as evidence, if every date is after the model's training cutoff?

- The issue: `AGENTS.md` hard rule 7 ends "Only forward paper or shadow results count". `docs/decisions/0002-historical-testing-and-risk-posture.md` proposed that such a replay could start the model comparison, and `docs/playbook/00_START_HERE.md` repeats it. Pilot 02 was one.
- Research recommends: keep hard rule 7 as written.
- Why: a cutoff date is the maker's claim and cannot be checked from outside. A forward test in the practice account puts no trading money at risk. It does cost model usage, which needs your number for `api_model_spend_cap_usd_month` first.
- You would be approving: that hard rule 7 stands as written, and that pilot 02 stays an inconclusive first look that is not cited as evidence.
- You would not be approving: any change to `AGENTS.md`, or any spending on model calls.

### 20. Is the break-even cost multiple your number?

- The issue: hard rule 9 in `AGENTS.md` says "at least twice the modeled cost". The same number is the key `backtest_min_breakeven_cost_multiple`, which the config file marks as proposed. They agree today, and the config file says the value may not go below the rule.
- Research recommends: say that this key is yours, so its status can change from proposed to owner.
- Why: one number should not be a hard rule in one file and a proposal in another.
- You would be approving: the number you already have in `AGENTS.md`, and nothing else.
- You would not be approving: any change to its value.

### 21. When the repo review's items are closed, delete the file or keep it?

- The issue: `docs/quality/00_READ_FIRST.md` line 51 says of `docs/quality/05_repo_review_2026-11-24.md`: "Delete it when its items are closed." The repo's map keeps old files and marks them as records, so the two pull in different directions.
- Research recommends: keep it, marked as a record in `docs/INDEX.md`.
- Why: a later reader can then see what the review found and that it was dealt with. Nothing reads it by default.
- You would be approving: a change to that one line of your file, from "Delete it" to "Mark it as a record".
- You would not be approving: any other change to your quality files. If you say delete, nothing changes and research deletes it when its items are closed.

## Item 5 in detail

Today `AGENTS.md` wins every conflict and sends the reader to the playbook, which was written before any test. Until you decide, each playbook page opens with a dated note that sends the reader to `docs/STATUS.md`. The five lines, quoted in full, with the proposed wording. Nothing is removed from any of them.

- `AGENTS.md` line 3. Now: "Read this first, then `docs/playbook/00_START_HERE.md`." Proposed: "Read this first, then `docs/STATUS.md`, then `docs/INDEX.md`."
- `AGENTS.md` line 27. Now: "Load `docs/playbook/` by default. It is short on purpose." Proposed: "Load `docs/STATUS.md` by default. `docs/playbook/` is background reading from before the tests. It is short on purpose."
- `AGENTS.md` line 29. Now: "Open `docs/research/` only to check a source or when a playbook line points you there. Do not paste research files into prompts wholesale." Proposed: "Open `docs/research/` only to check a source or when `docs/STATUS.md`, `docs/INDEX.md` or a playbook line points you there. Do not paste research files into prompts wholesale."
- `AGENTS.md` line 31. Now: "When you learn something that changes a rule or number, update the playbook line, keep its evidence label honest, and add a dated note in `docs/decisions/`." Proposed: "When you learn something that changes a rule or number, update `docs/STATUS.md` and the playbook line if there is one, keep its evidence label honest, and add a dated note in `docs/decisions/`."
- `docs/quality/00_READ_FIRST.md` line 12, a table row. Now: "What the evidence says, topic by topic" with `docs/playbook/` as the file that wins. Proposed: two rows. "What our own tests found, and where the project stands" with `docs/STATUS.md`. "What the reading said before the tests, topic by topic" with `docs/playbook/`.

- You would be approving: these five wording changes and nothing else.
- You would not be approving: any change to a hard rule, a number or a limit.
- Two related questions are separate: the config key that repeats hard rule 9 is question 20, and the repo review file is question 21.

Not needed yet: written permission from five data sources (Cboe, FINRA, Kraken Futures, Kalshi, Polymarket) before their feeds may be collected. The collector has them switched off. Research recommends leaving them off until a test needs one (`docs/research/19_information_feeds.md`).

## The numbers

Both tables are written by `tools/owner_numbers.py` from `config/thresholds.yaml`. Nothing in them is typed. The first belongs to decision 8, decision 1 and question 20. The second belongs to decision 12.

<!-- numbers:start (written by tools/owner_numbers.py from config/thresholds.yaml, do not edit by hand) -->
| Pass mark | What it asks | Value now | Key | Status in the config file |
|---|---|---|---|---|
| 1 | In the held-back years the rule must have a better Sharpe ratio than holding, and its largest drop may be at most this share of holding's largest drop | 0.6 | `replay_max_drop_ratio_vs_hold` | proposed |
| 2 | The rule must stay ahead of holding up to a cost that is this many times the modeled cost | 2 | `backtest_min_breakeven_cost_multiple` | proposed |
| 3 | The deflated Sharpe ratio, which marks a result down for every rule that was tried, must be at least this | 0.95 | `replay_min_deflated_sharpe` | proposed |
| 4 | The overfitting estimate must be below this | 0.25 | `backtest_max_pbo` | proposed |
| 5 | The rule must beat this share of copies of itself with its in and out spells put in random order | 0.95 | `replay_min_shuffle_percentile` | proposed |

| What the number is | Research's suggestion, not a value in use | Key |
|---|---|---|
| Money in the live account at the start, in dollars | 1000 | `live_starting_capital_usd` |
| The most held in one position, in dollars | 100 | `live_max_position_usd` |
| The most the account may lose in one day before it stops for the day, in dollars | 25 | `live_max_daily_loss_usd` |
| The most the account may lose in total before it stops and waits for you, in dollars | 200 | `live_max_total_loss_usd` |
| Share of the account set aside for high-risk ideas | 0.10 | `moonshot_sleeve_share` |
| The most of the account in any one high-risk idea | 0.02 | `moonshot_max_position_share` |
| The most the running service may spend on AI model calls in a month, in dollars | 25 | `api_model_spend_cap_usd_month` |
<!-- numbers:end -->

## What research would say to a partner

- You asked for fast. Nothing tested or read supports fast, and the routes that look fast are the ones where the records show losses: borrowed money, day trading against fees, small coins, and letting a model pick trades.
- What the evidence supports is slower: rules that cut the worst drop, interest on idle cash, and a short list of narrow ideas that have a reason and have not been tested yet.
- The honest next month is cheap: one data purchase, a practice account, two stock tests, and two rules watched with pretend money. If those say no, the answer is no, and research will say so.

## Words used in this list

The full list is `docs/GLOSSARY.md`. The ones this page leans on:

- Replay: a test of a fixed rule on old prices, with pretend trades.
- Held-back years: the last stretch of the price history, which a rule may be run on once, so the result is not something the rule was fitted to.
- The five pass marks: the five bars a rule has to clear in a replay. Mark 3 asks whether the result survives counting every rule that was tried. Mark 4 is an estimate of how likely the result is luck from trying many rules.
- First run and corrected run: the stock test was run twice. The second time was after an audit found that one rule's code did not match its written plan.
- Basis point: one hundredth of one percent. A cost of 5 basis points a side means $0.50 on a $1,000 order.
- Trial ledger: the list of every rule tried, written before each run (`research_rig/TRIAL_LEDGER.md`).
- Fingerprint: a short code worked out from a file. If the file changes at all, the code changes.
- Fill: what an order really got, in price and size.
- Order path: the code that sends an order to a broker.
- Scope call: a choice about what the project is and is not.
- Liquid funds: funds that trade in large amounts every day, so a small order does not move the price. SPY and QQQ are the two largest, tracking the S&P 500 and the Nasdaq 100.
- Training cutoff: the last date of the text an AI model learned from.
- Shadow: a rule running beside the market and writing down what it would have done, with no orders sent.
