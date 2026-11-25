# Status

Last updated: 2026-11-25 16:41 UTC

What has been tested and what happened. Read it after `AGENTS.md`. If another page disagrees with this one about a result, this page stands. What gets tested next is in `docs/QUEUE.md`. Words and test names are in `docs/GLOSSARY.md`.

## Where things stand

- Nothing tested so far is good enough to trade. That is the list below, and it is a short list.
- Three machines exist or are being built: the rig (`research_rig/`, working), the practice desk (`practice/`, running), the time machine (`timemachine/`, working, running AI sessions on crypto since 2026-11-25).
- The practice desk is running on GitHub's timer with pretend money since 2026-11-25 16:31 UTC, with the two fixed rules. What it has done is on the owner's screen and in the summary file on the `practice-records` branch. This page does not repeat it.
- No real-money account. No purchases. No real trades.

## Every test so far

The Result column is written by `tools/status_table.py` from the output files. Do not edit it by hand.

- "Pass" in the table means a rule cleared the five pass marks in that run (`research_rig/README.md` lists them). No pass from 2026-11-25 is counted. Each came from a run where the pass mark or the costs changed after results had been seen, or where the ledger row was late. Under "Honest testing" in `AGENTS.md` that makes it a new attempt, not a result. Fails stand.
- Where the table says "question 18b" or "the morning list", it points at `archive/decisions/morning_list_2026-11-25.md`, which is history. The builder settled it as written in the line above.
- A counted pass would mean "worth running on the practice desk". It would not mean "makes money".

<!-- results:start (written by tools/status_table.py, do not edit by hand) -->
| Test | What was asked | Result, MEASURED | Full write-up |
|---|---|---|---|
| Replay 01 with cross-check X2, rerun after the audits | Nine slow trend rules on bitcoin and on ether, daily, five venue costs, two price histories | 9 of 90 rule, coin and venue combinations pass on Bitstamp prices and 4 of 90 on Kraken prices. Pass on both histories: P1, P2, S50, D20 on BTC, at Binance.US cost only. Not credited as passes: the rerun also carried a stricter pass mark and a change to what holding pays (question 18b in the morning list). In the first run, before the audit fixes, none passed on both histories (8 on Bitstamp prices, 0 on Kraken prices). Knife edge: the overfitting estimate on Kraken prices is 0.2409 against a bar of 0.25 when it was run (`backtest_max_pbo`), and 0.4205 on Bitstamp prices from the same start date, which fails. | `docs/research/16_rig_audit.md` |
| Replay 03, rerun after the audits | Eight day trading rules on hourly bitcoin and ether, five venue costs | 0 of 80 rule, coin and venue combinations pass. | `docs/research/16_rig_audit.md`, rule definitions in `docs/research/15_replay_03_intraday_crypto.md` |
| Pilot 02 | Six AI model runs making one call a day on bitcoin and ether | Inconclusive, as the plan said before it ran. 6 model runs, 147 calls each. Too few days to tell skill from luck. | `docs/research/14_ai_calls_pilot_02.md` |
| Replay 04 | Trend rules on a wide basket of coins, dead coins kept | 0 of 25 rule and venue combinations pass. Highest deflated Sharpe 0.933 (K4 at Binance.US) against a bar of 0.95 when it was run (`replay_min_deflated_sharpe`). Held-back years at Binance.US cost: the top 10 coin rule K1 grew +2.7% a year, holding bitcoin grew +43.5%. An independent audit rebuilt the result and found faults that do not change it. | `docs/research/23_replay_04_coin_basket.md` |
| Replay 05, first run and corrected run | Eight slow trend rules on the US stock market index from 1927, three cost levels | First run: none at 2 bps; none at 5 bps; T1, T5, V1, I1 at 10 bps. Corrected run, after an audit found one rule did not match the plan: T1, T2, T4, T5, V1, I1, I2 at 2 bps; T1, T5, V1, I1, I2 at 5 bps; T1, T5, V1, I1, I2 at 10 bps. Pass in both runs at every cost: none. Not credited as passes in either run: the first run's ledger row was late and the corrected run was made before asking the owner (question 18b in the morning list). Fails stand. Held-back years at 5 bps, the same in both runs: the ten-month rule T1 grew +9.1% a year with a largest drop of -21.9%, holding the market grew +11.5% with -54.6%. | `docs/research/22_replay_05_stock_trend.md` |
| Replay 09 | New timing, rank, lead and risk rules on Alpaca crypto bars | 0 of 7 pass at 35 bps per side (`practice_crypto_fee_bps_added` plus `tm_crypto_half_spread_bps`). Held back 2026-07-01 to 2026-11-24: best rule CAP grew +2.1%; holding bitcoin grew +1.7%. | `docs/research/28_replay_09_crypto_methods.md` |
| Replay 07 | Eight day trading rules on SPY and QQQ one-minute bars, judged at 2 and 5 bps per side | SPY: 0 of 8 rules pass all five marks at both 2 bps and 5 bps per side; QQQ: 0 of 8 rules pass all five marks at both 2 bps and 5 bps per side. Highest break-even cost against holding, round trip, whole sample: 1.8 bps (N2 on QQQ). Prices from the workspace's own price lookup, dividend adjustment UNKNOWN, days that failed the bar check not used. | `docs/research/27_replay_07_intraday_spy_qqq.md` |
| Order-book samples | What it cost to trade a small size at once, sampled on two venues on one day | 254 rounds from 2026-11-25 07:28:03 to 2026-11-25 16:27:34 UTC. Bitcoin, middle cost of one order, fees not included: $1,000 cost 0.0 bps on Kraken and 0.8 bps on Binance.US; $10,000 cost 0.5 and 1.6 bps. Replay 04 assumed 5 bps for this on bitcoin and ether (read from its output). The rerun of replays 01 and 03 used the same figure, set in `research_rig/rig2.py` and not stored in its output. One sample of 9.0 hours only. The sampler was set to stop by itself at about 16:30 UTC on 2026-11-25, so a last time here before that means this is an interim summary. | `docs/research/24_order_book_costs.md` |
| Smaller checks: X1, S1, S2, the diagnostic, two mixed portfolios | The same rules on other prices, start dates and fill times, and bitcoin and ether held together | Not separate tests and not in the trial count. S2, ether from an earlier start on Kraken prices: 0 of 45 combinations pass. X1 and S1 carry no pass marks. The diagnostic is the Bitstamp figure in the first row. The two mixed portfolios are reported with growth and largest drop and are not judged on the five marks. Each name is defined in `docs/GLOSSARY.md`. | `docs/research/12_replay_01_crypto_trend.md`, `docs/research/12b_replay_01_kraken_crosscheck.md`, `docs/research/16_rig_audit.md` |
| Trial count check | The owner's rule counts a rerun after an engine fault as a trial. The two reruns were not counted when they ran. Does counting them change a result | Worked out from the stored outputs with 93 trials counted. It covers the outputs now judged: the rerun of replays 01 and 03 with its cross-checks, replay 04, and both runs of replay 05. The first-run outputs of replays 01 and 03 came from the engine with the faults and are not worked out again. Of 34 passes in those outputs, across all cost levels, none become fails. 66 of 378 rows could not be worked out again from what was stored, and none of those had passed mark 3. The closest is M90 on Binance.US, BTCUSD in R01, at 0.951 against a bar of 0.95 (`replay_min_deflated_sharpe`). Pass mark 3 alone changes from pass to fail in 29 rows that had already failed another mark. | `research_rig/TRIAL_LEDGER.md`, `research_rig/ledger_count_check.json` |
<!-- results:end -->

## What is believed now

Each line says how far to trust it.

- No day trading rule on crypto passes at any venue cost tested. MEASURED, eight rules on hourly bitcoin and ether. At the lowest venue cost a few ether rules have a positive Sharpe ratio in the held-back years and none passes. At Alpaca cost every one lost money in the held-back years (`docs/research/16_rig_audit.md`).
- Slow trend rules cut the largest drop and give up growth. MEASURED on bitcoin and on the US stock market index, and it matches the live record of funds built on the same rules (`docs/research/21_systematic_funds_and_published_rules.md`). In the held-back years most grew less than holding.
- A wide basket of smaller coins grew far less than holding bitcoin in the held-back years. MEASURED (`docs/research/23_replay_04_coin_basket.md`).
- Fixed rules that anyone can write down in one line have not given fast money here. MEASURED for the rules in the table. It says nothing about ideas not yet tested, and it is the reason the next tests are of AI traders that read far more than a rule can.
- AI models making the trading call: nothing shown so far. Public live records do not show it working (`docs/research/18_ai_systems_with_live_records.md`). Our own pilot was six model runs of 147 calls each, too few to tell skill from luck (`docs/research/14_ai_calls_pilot_02.md`). In the time machine, MEASURED on the months finished by 2026-11-25 16:08 UTC (23 from prices alone, 9 with headlines, pretend 1,000 dollars each): no model is ahead of holding bitcoin over its finished months, 57 of 173 closed trades won, and in the one month where random twins are complete no model stands clear of them (`docs/research/29_time_machine_tm01_crypto_price_only.md`). The models stay in cash at most wakes, so they lose less than holding in falling months and fall far behind in rising ones. Not finished: the plan's verdict needs all five months and all twins.
- The models' exits cost them most of what they lost, and their entries show no skill. MEASURED by replaying every buy they made under four fixed exits (`docs/research/32_exit_replay.md`, 176 buys from prices alone): as traded the buys lost 394 dollars in total; held five days with a stop 8% below, the same buys lost 43. But bitcoin bought at the same moments and held the same way gained 121, and random twins' buys did better than the models' buys under every fixed exit. A second look at months already traded, so it earns a new test and is not a result.
- Do dated headlines help an AI trader: early and not settled. In 8 of the first 9 paired months the same model ended higher with headlines than without, and it also bought less often, in months that mostly fell. The one rising month paired so far went the other way (`docs/research/30_time_machine_tm02_crypto_with_news.md`). The plan's test is six of six models over five months.
- The six models do not know the replay months. MEASURED: asked for month-end prices of three coins from January 2025 to November 2026, none answered any month from July 2026 on; the latest any knows is about February 2026 (`docs/research/31_model_knowledge_lines.md`). Replays on months after that are not trading from memory. Not checked: whether a model can reach the web during a session against its instructions.
- The closest thing to a lead on stocks is rule I2 in replay 05: hold the three strongest industry groups when the market is above its ten-month average. It grew nearly as much as holding with a much smaller largest drop, on an index that cannot be bought, in a run that is not counted. A reason for the next test, not a result (`docs/research/22_replay_05_stock_trend.md`).
- Day trading SPY and QQQ with fixed rules does not pay after costs. MEASURED, eight rules on one-minute prices of each fund (`docs/research/27_replay_07_intraday_spy_qqq.md`): none beat holding the fund in the held-back years at either cost judged. One rule on QQQ beat holding only if a round trip costs less than about 1.8 hundredths of a percent, which has not been measured at a real desk.
- Seven more crypto methods at Alpaca's fees: none passed. MEASURED (`docs/research/28_replay_09_crypto_methods.md`).
- Single stocks that can be bought are UNKNOWN. No rule has been run on them. The tape now holds 56 stocks and funds minute by minute from June 2026, with company filings and one headline site as dated news, so AI sessions on stocks are next.
- Pass mark 4, the overfitting estimate, is not steady enough to be a yes or no on its own. MEASURED three ways (`docs/research/16_rig_audit.md`). From the next plan on it is measured over start dates fixed before the run.

## What has been replaced

| Do not rely on | Use instead | Why |
|---|---|---|
| Verdicts in `docs/research/12_replay_01_crypto_trend.md`, `docs/research/12b_replay_01_kraken_crosscheck.md`, `docs/research/15_replay_03_intraday_crypto.md` | `docs/research/16_rig_audit.md` | Two code audits found faults in the first rig. The rerun changed verdicts |
| Engine v1 (`research_rig/engine.py`) | Engine v2 (`research_rig/rig2.py`) | Same reason |
| Either run of replay 05 read alone | Both runs side by side in `docs/research/22_replay_05_stock_trend.md` | The code for rule I2 did not match its plan in the first run |
| Playbook lines that read as settled findings | This page | The playbook was written from reading on 2026-11-24, before any test of our own |
| Anything in `archive/` read as a rule | `AGENTS.md` | The owner retired the old rule layer on 2026-11-25 (`docs/DECISIONS.md`) |

## Known faults in the tools

Only what someone using the tools needs to know. The longer account of each slip on the first nights is in `archive/decisions/0006-audit-and-second-night-2026-11-25.md` and `archive/audit/`.

- `research_rig/basket.py` closes a position in a coin whose history ends by using knowledge of the full file. It never fired in replay 04. Fix it before the file is used again (`archive/audit/2026-11-25_replay_04_audit.md`, findings 04-01 to 04-03).
- The held-back years of the first replays have been looked at more than once: two reruns, cross-checks on a second price history, and a script for the owner's screen that replayed stored runs each time it ran (fixed, it now reads stored outputs unless asked with `--resimulate`). Treat every held-back figure in the table as used. New tests need new held-back data: the practice desk and time machine months that no rule here was tuned on.
- Ledger rows for replay 04 and the first run of replay 05 were written after the runs started. Two reruns were added to the ledger afterwards. The count of 93 trials includes them.
- Outputs from the first nights were not stored with their command and input fingerprints at run time. `research_rig/provenance.json` rebuilds that record after the fact.
- Pass mark 3 screened nothing in replay 05, because of how its plan defined the spread of Sharpe ratios. The next plan defines it across all counted trials.
- Bitstamp's terms are unclear about collecting its prices. Kraken's published files are the main crypto history from here on.
- Stock prices collected from the workspace's built-in price history have gaps, and some one-minute prices sit outside the day's range in its daily file. They stay on the research machine, are never published, and any test that uses them says so.
- Time machine, found and fixed on 2026-11-25 while sessions were running, each written into the plans with its time: crypto traders were shown the previous day's stock fund movers for about 18 minutes; a pick sent twice after a lost reply was taken twice (five wakes, all "no pick"); exits are checked every few minutes, so a one-minute spike through a stop or target between checks is missed. The results tables count the first two per session.
- The time machine's stock list was chosen on 2026-11-25 from today's large companies. It leans toward companies that did well. Twins drawn from the same list share that lean, so compare with twins, not with zero.
- The practice desk checks exits about every ten minutes, GitHub's timer can run late, and stocks trade only in regular hours. A stop can be filled late. Results from the desk include that.

## Waiting on the owner

Nothing waits on him today.

Real money, and the limits for it, are his when that day comes (`docs/DECISIONS.md`, "Not decided yet").

## Done by the owner

On 2026-11-25:

- The data key, saved in the secure form. MEASURED at 16:23 UTC: it returns minute and daily prices for the whole US stock market back to 2016, the bid and ask at any past moment, and dated stock news from 2026-04-29 on and nothing older.
- The practice account key, added to the repo's secrets at 16:31 UTC. The practice desk ran at 16:31 UTC and its first order filled.
- He made the repo private at about 16:30 UTC and public again at about 16:40 UTC. The desk's timer is back to every ten minutes and the owner's screen reads the practice records live.

## Keeping this page true

- A commit that adds or changes a result changes this page in the same commit and moves the "Last updated" line.
- After any new output file: `python3 tools/status_table.py --write`.
- Before every commit: `python3 tools/check_repo.py`.
- Write beliefs with their label. Do not raise a label without a new source or a new logged test.
