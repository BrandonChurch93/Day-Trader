# Morning list, 2026-11-25

Written by research at the end of the overnight run. Rewritten at 08:36 UTC after the audits and the second set of tests, corrected at 08:51 UTC after three fresh models read the repo cold, and rewritten again on 2026-11-25 09:29 UTC after three more did. Status: proposed. Nothing here is an owner decision. The record of the night is `docs/decisions/0005-overnight-research-2026-11-25.md` and `docs/decisions/0006-audit-and-second-night-2026-11-25.md`. The current state, with every result, is `docs/STATUS.md`. How your answers get recorded is in `docs/decisions/README.md`.

## The short version

- No rule has a clean pass, and nothing tested or read supports fast money. The detail is under "Where things stand".
- Three answers from you unblock the most: decision 1 (how pass mark 4 is measured), question 18 (which runs count), and the practice account keys (item 1 below).
- Research slipped against your rules several times overnight. Each slip is written down under "What research got wrong". Two of them decide which run of a test counts, and that is yours to settle (question 18).
- The repo now has a map, a status page, a glossary and a checker, and has been read cold by six fresh models. Each round found real faults. They are fixed and recorded.

## Things only you can do

In this order. None uses real money for trading.

1. Open an Alpaca account for practice trading and create practice keys. This approves practice trading only. It does not approve funding the account. Detail is in `docs/research/09_brokers_and_venues.md`.
2. Buy one month of stock price data. Research recommends the EODHD plan with daily and one-minute prices, $29.99 for the month ([EODHD pricing](https://eodhd.com/pricing/)). It is no longer the only way to get one-minute stock prices (item 6), but it is the only source found for dividend history, which the fund test needs, and it gives a second source to check the first against. A second source changed a result once already. Terms for keeping the files are in `docs/research/10_historical_data_and_practice.md`.
3. Say whether Kraken's published price files may be the main crypto history. Research recommends yes. Bitstamp's terms are unclear about collecting its prices.
4. Say whether the order-book sampler may run again on Kraken's public price feed. Kraken's general terms bar automation on its content ([Kraken Global Terms](https://www.kraken.com/legal/global-terms)). Research reads the documented public feed as offered for this use. That is research's reading, not Kraken's word. The sampler stops by itself this morning and will not be restarted without your yes.
5. Say whether `AGENTS.md` and `docs/quality/00_READ_FIRST.md` may be changed so that they point to `docs/STATUS.md` and `docs/INDEX.md`. `AGENTS.md` says any change to it needs you, and the quality files are yours, so neither was touched. The exact lines are in the next section. Three fresh models read the repo cold on 2026-11-25 and all three named this as the thing most likely to send a new model the wrong way.
6. Say whether stock prices from this workspace's own built-in price history may be used and kept for tests. Found on 2026-11-25: it returns one-minute prices for SPY back to 2004 and daily prices for funds back to their first day. It has no dividend history. Research is collecting it and checking it for gaps, and has run no rule on it. What its terms say about keeping the files is UNKNOWN to research. You work at Perplexity and can ask. Detail is in `docs/research/10_historical_data_and_practice.md`, "Price history inside the workspace".

## Where things stand

No rule has a clean pass. Results are in the table in `docs/STATUS.md`, which is written from the output files. In words:

| Test | What happened | Full write-up |
|---|---|---|
| Slow trend rules on bitcoin and ether | Some bitcoin rules pass on both price histories (named in the status table), at the lowest venue cost only, only after audit fixes, and within a hair of the bar on one mark. No ether rule passes | `docs/research/16_rig_audit.md` |
| Day trading rules on bitcoin and ether | None pass at any venue cost. Most show a small gain per trade before fees, and none stays ahead of holding the coin at twice the lowest fee modeled | `docs/research/16_rig_audit.md` |
| Trend rules on a wide basket of coins | None pass. The basket grew far less than holding bitcoin | `docs/research/23_replay_04_coin_basket.md` |
| Slow trend rules on the US stock market from 1927 | Two runs, because an audit found one rule's code did not match the plan. First run: no rule passes at the two lower cost levels. Corrected run: several rules pass at every cost level (named in the status table). No rule passes in both runs at every cost level. The first run stands until you answer question 18 | `docs/research/22_replay_05_stock_trend.md` |
| AI models making the daily call | Inconclusive, as the plan said before it ran | `docs/research/14_ai_calls_pilot_02.md` |
| What it costs to trade a small size | Sampled on two venues on one day. Interim | `docs/research/24_order_book_costs.md` |

What the tests agree on, and what real funds built on the same rules also show: slow trend rules cut the worst drop and give up some growth. That is a smoother ride. It is not fast money. The reading on traders, funds and AI systems with real money says the same (`docs/research/25_what_the_evidence_supports.md`).

The one lead worth following on stocks: in the corrected run, which research recommends should not count as the result (question 18b below), the rule that holds the three strongest industry groups when the market is above its ten-month average grew nearly as much as holding, with a much smaller largest drop. It carries three cautions, listed in `docs/research/22_replay_05_stock_trend.md`. It has not been tested on anything that can be bought.

What has not been tested at all: funds that can be bought, and day trading SPY and QQQ. The first waits on a data purchase. The second waits on your answer to item 6 above or on the same purchase.

## What research got wrong

For you to know. Each is also in `docs/STATUS.md` under "Known faults and slips".

- Two second runs of tests were reported as reruns but were not written in the trial ledger or counted as trials, which your rule requires. The rows are there now, marked late. Counting them was checked on the stored results and turns no pass into a fail. The closest call is in the "Trial count check" row of the table in `docs/STATUS.md`.
- The second run of the stock test fixed one rule's code, not the engine. Your rule names the engine only. Research reran before asking you, and for a while its pages gave your rule more widely than you wrote it. They now quote you. Questions 18a and 18b.
- The rerun of the bitcoin and ether tests rests on research's reading of "machine check" and "engine", which you were never asked about. Question 18c.
- Stored tests were repeated without your yes: one small script once, and the script behind your screen several times. No new number came out of either. Question 16.
- Results were not saved with their command, code version and input fingerprints when they ran, which your bar asks for. That record was rebuilt afterwards and says what it cannot prove (`research_rig/provenance.json`).
- Ledger rows for two tests were added after those tests had started. Their plans were pushed before.

## Decisions waiting, one at a time

Research's recommendation is given for each, with the reason. The order is the order research would take them in. Questions 14 to 19 are about scope and about your own rules, and came out of the cold-read tests.

| # | Decision | Research recommends | You would be approving | You would not be approving |
|---|---|---|---|---|
| 1 | How pass mark 4 is measured | Count ties as half, and measure it over a fixed set of start dates and block counts, so one number does not decide. Detail in `docs/research/16_rig_audit.md` | A steadier way to measure. It would most likely turn the bitcoin passes back to fails. Its effect on the stock rules is UNKNOWN until rerun | Any change to the bar in `backtest_max_pbo` |
| 2 | How pass mark 3 is measured | Take the spread across every trial counted in the ledger, not only the trials in one plan. In replay 05 the mark screened nothing | A stricter mark 3 in every future plan | Any change to `replay_min_deflated_sharpe` |
| 3 | Audits | Every replay gets an independent audit by a different model before its result is believed. Tonight's audits changed results twice. Research works this way already | Making that a standing rule for research | |
| 4 | What to test next | Replay 06, slow trend on funds that can be bought, with the industry rule added on sector funds. Then replay 07, day trading SPY and QQQ. Each with its plan and ledger rows pushed first | Two more research replays, once the data is bought | Any building or any trade |
| 5 | Watching rules in the practice account | Run two slow rules with pretend money as observation, labelled as not passed: the bitcoin trend rule P1, and the ten-month rule on a total market fund | A forward record that starts the count toward `paper_min_trading_days` and `paper_min_closed_trades` | Calling either a strategy. Real money |
| 6 | Crypto day trading and wide coin baskets | Drop both. No rule passed in either, at any venue cost | Closing those two lines of work | Dropping crypto altogether |
| 7 | Interest on idle cash | Credit Treasury bill interest on cash in every replay. Trend rules sit in cash a lot and the crypto replays credit nothing | One rig change with its own plan | |
| 8 | The three pass marks proposed last night | Keep them | `replay_max_drop_ratio_vs_hold`, `replay_min_deflated_sharpe`, `replay_min_shuffle_percentile` | |
| 9 | Broker plan | Alpaca individual account for stocks and all practice. Live crypto venue left open | The plan in `docs/research/09_brokers_and_venues.md` | Funding anything |
| 10 | AI forward test | Run it in the practice account only if you want that question answered, with the rules in `docs/research/11_ai_trader_experiment_design.md` fixed first | A practice-only test | Real money on AI calls |
| 11 | High-risk share | Fund it only with ideas that pass a replay. First in line: insider buying that is not routine, in listed stocks | The order in `docs/research/25_what_the_evidence_supports.md` | Any penny stock or memecoin purchase |
| 12 | Open numbers | Yours alone: `live_starting_capital_usd`, `live_max_position_usd`, `live_max_daily_loss_usd`, `live_max_total_loss_usd`, `moonshot_sleeve_share`, `moonshot_max_position_share`, `api_model_spend_cap_usd_month` | Nothing until you set them | |
| 13 | Who the Builder is and where it runs | Decide after a rule passes in practice, not before | | |
| 14 | Scope call from 2026-11-24, never put to you: the product is a fixed-rule trading service, and AI is a research and review layer beside it (`docs/decisions/0001-starting-decisions.md`, row 1) | Yes. No AI system with a live record was found that beat holding, and our pilot was inconclusive. `AGENTS.md` hard rule 1 already keeps models out of the order path whatever you decide here | The shape of the product | Any build, any stack, any AI test in practice (that is decision 10) |
| 15 | Scope call from 2026-11-24, never put to you: start with slow rules that hold for days or longer, on liquid funds and on bitcoin and ether, not with day trading (same file, row 2) | Yes, with replay 07 kept as the one day trading test still worth running. Every test since has pointed the same way | Where the first product rules come from | Dropping day trading for good. Replay 07 decides that for stocks |
| 16 | May a stored test be run again, unchanged and on the same data, only to check that it gives the same file? Your rule says never run the held-back slice a second time for the same version of a rule, and names one exception. You should know this has already happened without your yes. A small script that describes one year of data was run a second time and gave the same file. And the script that makes the data for your screen replayed five already-tested rules over the whole price history each time it ran, several times, to draw their curves. It checked every figure against the stored results and made no new number. It no longer does this | Yes, as a check only, because a result nobody can reproduce is weaker than one that can be: unchanged code, the same input files by fingerprint, output written outside the repo and compared, and the check written in the ledger. Until you answer, nobody runs a test script | Reproduction checks as described, and that the repeats already made stand as disclosed and uncounted | Any run with a rule, a cost, a date or a bar changed |
| 17 | The practice account gate and the live gate both say results must be "within tolerance" (`docs/playbook/00_START_HERE.md`), and no number exists for either. So today no rule can pass from practice to real money, whatever it does | Leave both numbers unset for now, and have research propose values from the first weeks of practice trades, because a tolerance picked before any real fill would be a guess. Nothing moves past the practice account until you set them | That these two numbers are yours to set, and that the gate stays shut until you do | Any value today |
| 18a | Your rerun rule names one case: "when a machine check proves the engine itself was wrong". From now on, should it also cover a rule whose code turns out not to match its written plan, when the engine was right? | Yes, with four conditions: an independent check proves the mismatch against the plan as it was pushed; the correction and the ledger row are pushed before the rerun; it is counted as trials and reported as a rerun; both outputs are kept. Reason: a rule that does not match its plan tests something nobody wrote down, so without a rerun the plan's question is never answered. The conditions keep it from becoming a second try at a result someone did not like | A second kind of allowed rerun, from now on | Any rerun because a result was disappointing |
| 18b | Does the corrected run of the stock test (replay 05) count as its result? Research ran it before asking you. It does not meet the conditions in 18a: the correction was pushed before the rerun, but the ledger row was added after it. Also, the auditor had already measured what the correction would do before it was written down, so its effect was known. And the correction to one rule moved pass mark 4 for rules whose own trades did not change | No. The first run stands: no stock rule passes at 2 or 5 basis points a side. The corrected run stays in the repo beside it, labelled, as the reason to test the industry rule properly on real funds in replay 06. Reason: it fails the conditions research itself proposes, and your bar says not to shop for a pass | That replay 05's result is the first run | Throwing the corrected run away. It is kept and disclosed |
| 18c | Was the rerun of the bitcoin and ether tests after the code audits covered by your rule? Two other AI models audited the test code, ran their own checks, and found faults in how trades were simulated and in how two pass marks were worked out. Research read that as "a machine check proves the engine itself was wrong" and reran. You have not been asked before whether an audit by a model is a machine check, or whether the pass-mark code is part of the engine. It matters: in the first run no rule passed on both price histories. In the rerun four bitcoin rules do, at the lowest venue fee only | Yes, it was covered: the faults were in the shared test code and not in any one rule, every change was listed in a file pushed before the rerun, and verdicts moved in both directions. From now on, "machine check" should mean a test with a known answer or a second build from the raw data that disagrees, not a model's opinion alone | That the rerun after the audits is the result for replays 01 and 03, and a plain meaning for "machine check" | That the four bitcoin passes are proven. They sit a hair inside one bar and decision 1 would most likely turn them back to fails |
| 19 | May a replay of an AI model on past dates count as evidence if every date is after the model's training cutoff? `AGENTS.md` hard rule 7 ends "Only forward paper or shadow results count". `docs/decisions/0002-historical-testing-and-risk-posture.md` proposed that such a replay could start the model comparison, and pilot 02 was one | Keep hard rule 7 as written, because a cutoff date is the maker's claim and cannot be checked from outside, and a forward test in the practice account costs nothing but time. Pilot 02 stays an inconclusive first look and is not cited as evidence | That hard rule 7 stands as written | Any change to `AGENTS.md` |

## Item 5 in detail

Today `AGENTS.md` wins every conflict and sends the reader to the playbook, which was written before any test. Until you decide, each playbook page opens with a dated note that sends the reader to `docs/STATUS.md`. That works, and it is a patch.

| File and line | Says now | Research proposes |
|---|---|---|
| `AGENTS.md` line 3 | Read this first, then `docs/playbook/00_START_HERE.md` | Read this first, then `docs/STATUS.md`, then `docs/INDEX.md` |
| `AGENTS.md` line 27 | Load `docs/playbook/` by default | Load `docs/STATUS.md` by default. `docs/playbook/` is background reading from before the tests |
| `AGENTS.md` line 29 | Open `docs/research/` only when a playbook line points you there | Open `docs/research/` when `docs/STATUS.md` or `docs/INDEX.md` points you there |
| `AGENTS.md` line 31 | When you learn something, update the playbook line | Update `docs/STATUS.md` in the same commit, and the playbook line if there is one |
| `docs/quality/00_READ_FIRST.md` line 12 | What the evidence says: `docs/playbook/` wins | Our own test results: `docs/STATUS.md` wins. Reading done before the tests: `docs/playbook/` |
| `docs/quality/00_READ_FIRST.md` line 51 | Delete `05_repo_review_2026-11-24.md` when its items are closed | Your call. `docs/INDEX.md` keeps old files and marks them RECORD. Say delete or keep |

- You would be approving: these six wording changes and nothing else.
- You would not be approving: any change to a hard rule, a number or a limit.
- One more thing to know: hard rule 9 in `AGENTS.md` says "at least twice the modeled cost". The same number is the key `backtest_min_breakeven_cost_multiple`, which the config file marks as proposed. They agree today, and the config file now says the value may not go below the rule. Research recommends you say that this key is yours, so its status can be changed from proposed to owner. That approves the number you already have in `AGENTS.md` and nothing else.

Not needed yet: written permission from five data sources (Cboe, FINRA, Kraken Futures, Kalshi, Polymarket) before their feeds may be collected. The collector has them switched off. Research recommends leaving them off until a test needs one (`docs/research/19_information_feeds.md`).

## What research would say to a partner

- You asked for fast. Nothing tested or read supports fast, and the routes that look fast are the ones where the records show losses: borrowed money, day trading against fees, small coins, and letting a model pick trades.
- What the evidence supports is slower: rules that cut the worst drop, interest on idle cash, and a short list of narrow ideas that have a reason and have not been tested yet.
- The honest next month is cheap: one data purchase, a practice account, two stock tests, and two rules watched with pretend money. If those say no, the answer is no, and research will say so.

## One recommendation

Do items 1 and 2 of "Things only you can do" this morning, and take decision 1 and question 18. That unblocks the two stock tests and the practice record, which are the things that could change this picture, and it settles which results stand.
