# 0005 - Overnight research run, 2026-11-25

Date: 2026-11-25 (UTC). The night of 2026-11-24 in Idaho.
Status: proposed by the research team. Nothing here is an owner decision.

> Note added 2026-11-25. This is the record of the first half of the night. Two code audits later found faults in the rig, the tests were rerun, and several results named here changed. Read `docs/decisions/0006-audit-and-second-night-2026-11-25.md` for what changed and `docs/STATUS.md` for the current state. The pass-mark numbers this note proposed are still proposals.

What the owner said, 2026-11-24: "Feel free to continue doing your research, anything else that would benefit the project". Later the same night: "you free to do anything that will benefit the project and the overall goal of you being successful at making money day trading crypto and stocks. Free for you to look up to penny stocks and high-risk, high-return crypto as well".

What research did with that, and what it kept to: research only. No account was opened, no key was requested, no order was placed and no product code was written. A small research rig was built to test ideas on past prices. It is kept apart from the product in `research_rig/`. `AGENTS.md` was not changed.

## What was added

| Item | Where |
|---|---|
| The research rig: replay engine, engine checks, written test plans, trial ledger | `research_rig/` |
| Replay 01: slow trend rules on bitcoin and ether with real fees | `docs/research/12_replay_01_crypto_trend.md` |
| Pilot 02: six AI model runs making daily calls on past prices | `docs/research/14_ai_calls_pilot_02.md` |
| Cross-check X2: replay 01 on Kraken's published full history, and a check of why verdicts changed | `docs/research/12b_replay_01_kraken_crosscheck.md` |
| Replay 03: eight rules that trade inside the day, hourly bitcoin and ether bars | `docs/research/15_replay_03_intraday_crypto.md` |
| Summary: historical data and practice accounts | `docs/research/10_historical_data_and_practice.md` |
| Summary: how to test an AI trader | `docs/research/11_ai_trader_experiment_design.md` |
| Summary: penny stocks, small stocks and high-risk crypto | `docs/research/13_high_risk_sleeve_evidence.md` |
| Raw reports and the second fact check behind 10, 11 and 13 | `docs/research/10_raw/`, `11_raw/`, `13_raw/` |

## Numbers added to the config

Three house numbers were used as pass marks in replay 01. They were fixed in writing before the replay ran. They are now in `config/thresholds.yaml` with status `proposed`, so that documents can name them:

| Key | What it is |
|---|---|
| `replay_max_drop_ratio_vs_hold` | Pass mark 1: how large the rule's biggest drop may be, as a share of the biggest drop from holding |
| `replay_min_deflated_sharpe` | Pass mark 3: the smallest deflated Sharpe ratio that passes |
| `replay_min_shuffle_percentile` | Pass mark 5: the share of shuffled timings the rule must beat |

These are research's own choices, not published cutoffs. The owner can confirm, change or decline each one. If one changes, replay 01's pass table must be worked out again with `run_01b.py`.

## What the evidence now says, in short

The detail and every limit are in the two research files.

- Slow trend rules on bitcoin passed all five marks at Binance.US cost and, for three of nine rules, at Alpaca cost. The rule named in advance as the main one failed narrowly at Alpaca cost. Nothing passed at Kraken or Coinbase entry cost.
- No trend rule on ether passed at any venue.
- The rules cut the worst falls roughly in half and gave up much of the gain in strong years.
- Six AI model runs on 147 days of prices all behaved like trend followers and were not distinguishable from a four-line trend rule. The pilot was declared inconclusive before it ran.

## What changed later the same night

- Cross-check X2 ran the same nine rules on Kraken's own price history, which starts 16 months later for bitcoin. All 8 bitcoin passes from replay 01 failed there, 7 of them on mark 4 (overfitting) alone. A check made after the run shows the cause is the dates and not the prices: on Bitstamp's own prices from 2014-05-01 mark 4 fails too. The held-back years reproduce almost exactly on both venues' prices.
- So no bitcoin rule has a clean pass. Research withdraws proposal 1 as first worded. The replacement is proposal 1 below.
- Replay 03 tested eight rules that trade inside the day. 0 of 16 passed at any venue's cost. At Alpaca cost and above every rule lost money.
- Bitstamp's general terms are unclear about collecting its prices for research ([Bitstamp terms](https://www.bitstamp.net/terms-of-use/)). The US terms page was not opened. UNKNOWN. Kraken publishes its history as files for download.
- No bar was lowered. `backtest_max_pbo` and the other marks are unchanged.

## Proposals for the owner, one at a time

None is approved. Each is stated in the research file it comes from.

| # | Proposal | From |
|---|---|---|
| 1 | Withdrawn: carry P2, S50 and D20 as passed candidates. Replaced by: if the slow bitcoin trend is run in practice, run P1 only, as observation, labelled as not passed | research 12b |
| 2 | Run ether in practice for observation only, labelled as failed | research 12 |
| 3 | Keep the three new pass marks as they are | this note |
| 4 | Keep the one-day-at-a-time harness as the way to test AI calls, and run it forward in the practice account only if he wants that question answered | research 14 |
| 5 | Do not day trade crypto at Alpaca, Kraken or Coinbase taker fees | research 15 |
| 6 | Put the day trading question to stocks next, once minute data is bought, with the plan written first | research 15, research 10 |
| 7 | Use Kraken's published files as the rig's main crypto history and Bitstamp as the second source | research 12b |
| 8 | Buy one month of data as a one-time download. EODHD's daily plus one-minute plan if the stock day trading test is next, because that test needs minute bars. Kibot's end-of-day plan if only daily replays are wanted. Prices and keep-after-cancel terms are in research 10 | research 10, research 15 |
| 9 | Fund the high-risk sleeve only with ideas that pass a replay; first three replays named in research 13 | research 13 |
| 10 | Possible next test, to be written down before it runs: one blended rule that holds the average of the nine trend rules, so nothing is picked | research 12b |
