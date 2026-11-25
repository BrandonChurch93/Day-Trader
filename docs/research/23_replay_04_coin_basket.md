# 23. Replay 04: trend rules on a wide basket of coins

Status: research result. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Plan written before any rule in it was run (STATED in the plan): `research_rig/PREREG_04_coin_basket_trend.md`, measured as set out in `research_rig/AMENDMENT_2026-11-25_audit_fixes.md`. Every number below is MEASURED by `research_rig/run_04.py` and placed here by `research_rig/build_doc23.py`, unless it is tagged STATED or UNKNOWN.

## Bottom line

- Rules that pass all five marks: 0 of 25 rule and venue pairs. By venue: Binance.US: none; Alpaca: none; Kraken $10k tier: none; Kraken entry: none; Coinbase entry: none.
- The three wide-basket rules (K1, K2, K3) had a lower Sharpe ratio than holding bitcoin in the held-back slice in 15 of 15 rule and venue pairs. They had a higher Sharpe ratio than holding the basket in: none. They lost money in the held-back slice in 13 of 15 pairs.
- Mark that fails for every rule at every venue: 3 deflated Sharpe. The highest deflated Sharpe was 0.933 (K4 at Binance.US), against a bar of 0.95 (`replay_min_deflated_sharpe`).
- K4 (bitcoin and ether) and K5 (bitcoin only) came closest. Mark 1 passes for K4 at: Binance.US; for K5 at: none. Both still fail mark 3 everywhere.
- Dead coins were kept in the data. Coins held at some point whose history later ended, at Kraken $10k tier: K1 3; K2 3; K3 7; K4 0; K5 0. No position was ever closed because a coin's history ended (0 such sales across all rules and venues). So the half-value loss test on those sales tested no real loss. The code for those sales also uses hindsight (audit finding 04-01). It never fired here, but must be fixed before reuse.
- An independent audit rebuilt K1, K4 and both comparisons from the raw files and matched them to rounding. It found faults, listed below. None of the changes it tested turned a fail into a pass (MEASURED by the auditor, `audit/2026-11-25_replay_04_audit.md`).
- Taxes are not in these numbers. A rule that sells pays tax sooner than holding does.

Closest miss: K4 at Binance.US, which fails only 3 deflated Sharpe (deflated Sharpe 0.933 against a bar above 0.95, `replay_min_deflated_sharpe`). A near miss is a fail.

## What the rules are

The trend weight P1 is the same as in replay 01. It is the share of four tests that are true: the close is above its 20, 50, 100 and 200 day average. So it is 0, one quarter, one half, three quarters or all of a coin's slot.

| Id | Rule |
|---|---|
| K1 | Each month, the 10 coins with the most dollar trading. Each coin has one tenth of the account as its slot and holds P1 times its slot. The primary rule |
| K2 | Each month, of those 10 coins, the 5 that rose most over the last 90 days. One fifth each, times P1 |
| K3 | Each month, the 20 coins with the most dollar trading. One twentieth each, times P1 |
| K4 | Bitcoin and ether only. Half each, times P1 |
| K5 | Bitcoin only. Four pairs of fast and slow weighted averages of the daily close. The share held is the share of pairs where the fast one is at or above the slow one. Set once a week, at Wednesday's close. The plan reads this from the CoinDesk trend indicator method (STATED) |

Every rule is long or cash only, with one shared cash balance that earns nothing. A coin trades when its weight is off target by more than one eighth of its slot. Orders are set at the close and fill at the next open on a day the coin really traded. Otherwise the order waits. The two comparisons are holding bitcoin, bought once at the start, and holding the basket: the same top 10 each month, one tenth each, traded back toward equal parts at each month start and not traded in between. It is not exactly equal parts after costs, because trade sizes use the account value before costs (corrected after the audit, finding 04-02). Both pay the same costs as the rules.

Costs per side are the venue fee plus slippage: 5 bps for bitcoin and ether and 25 bps for every other coin. The slippage is assumed, not measured. Venue fees in bps: Binance.US 2, Alpaca 25, Kraken $10k tier 38, Kraken entry 80, Coinbase entry 90. Only the Kraken levels are a place where the whole basket can be bought (STATED in the plan).

## How the basket is chosen

- At each month start the basket is chosen from data up to the day before only. A check in `research_rig/fixtures_basket.py` changes all later data and confirms the basket does not change.
- Left out: coins with less than 200 days of history, coins with no trades on more than 10 of the last 90 days, and coins whose price barely moves (yearly swing under 0.20, from the last 90 daily moves). That last test is meant to remove dollar coins, currency pairs and gold tokens.
- Left out: copies. A coin whose last 90 daily moves track a coin with more dollar trading almost exactly (correlation above 0.98) is dropped.
- The rest are ranked by their middle daily dollar trading over the last 90 days.
- The gold token PAXGUSD was not always removed by the price-swing test. It was in the top 20 in 12 months (2020-06-01, 2020-09-01, 2025-12-01, 2026-01-01, 2026-02-01, 2026-03-01, 2026-04-01, 2026-05-01, 2026-06-01, 2026-07-01, 2026-08-01, 2026-09-01) and in the top 10 in 2 months (2026-04-01, 2026-05-01). Coins dropped as copies of it: XAUTUSD. This is the plan's test, applied as written.
- The plan counts 760 Kraken files ending in USD (STATED). 753 were used. Corrected after the audit: the 7 left out are not all coins priced in another coin. 3 are, 1 (MERLUSD) is a real dollar market wrongly left out by a name test, and 3 are files with one row (MEASURED by the auditor, finding 04-05). Restoring MERLUSD changes no monthly list.
- The test starts at the first month start with at least 10 coins that qualify: 2018-06-01. The basket was chosen 100 times, from 2018-06-01 to 2026-09-01. 39 different coins were ever in a top 10 and 84 in a top 20. In 22 months fewer than 20 coins qualified (the fewest was 13), and K3 held only those.
- Coins in a top 10 whose history ended before 2026-09-25: EOSUSD, FTMUSD, MATICUSD. In a top 20: EOSUSD, FTMUSD, ICXUSD, MATICUSD, REPUSD, RNDRUSD, WAVESUSD. Whether each of these failed, was delisted or was renamed is not checked here (UNKNOWN). Two of them, RNDRUSD and FTMUSD, were still chosen in the month after their last trade (MEASURED by the auditor, finding 04-06).
- Every month's list is in `research_rig/results_04.json` under `membership`.

## Held-back slice

2023-01-01 to 2026-06-30. Each slice starts from the account value on the day before it.

### Binance.US (7 bps a side for bitcoin and ether, 27 bps for other coins)

| Rule | Growth a year | Sharpe | Largest drop | Sharpe minus hold bitcoin | Sharpe minus hold the basket |
|---|---|---|---|---|---|
| Hold bitcoin | +43.5% | 1.00 | -53.1% | | |
| Hold the basket | -1.4% | 0.33 | -79.9% | | |
| K1 | +2.7% | 0.26 | -56.7% | -0.74 | -0.07 |
| K2 | -2.6% | 0.16 | -68.3% | -0.84 | -0.16 |
| K3 | +2.6% | 0.25 | -57.4% | -0.75 | -0.08 |
| K4 | +32.9% | 1.02 | -29.7% | +0.02 | +0.69 |
| K5 | +37.1% | 1.13 | -33.3% | +0.13 | +0.80 |

### Alpaca (30 bps a side for bitcoin and ether, 50 bps for other coins)

| Rule | Growth a year | Sharpe | Largest drop | Sharpe minus hold bitcoin | Sharpe minus hold the basket |
|---|---|---|---|---|---|
| Hold bitcoin | +43.5% | 1.00 | -53.1% | | |
| Hold the basket | -2.1% | 0.32 | -80.2% | | |
| K1 | -3.0% | 0.11 | -60.3% | -0.90 | -0.21 |
| K2 | -8.6% | 0.02 | -71.1% | -0.98 | -0.30 |
| K3 | -3.0% | 0.10 | -60.8% | -0.90 | -0.22 |
| K4 | +26.7% | 0.88 | -32.2% | -0.13 | +0.56 |
| K5 | +34.5% | 1.07 | -34.2% | +0.07 | +0.75 |

### Kraken $10k tier (43 bps a side for bitcoin and ether, 63 bps for other coins)

| Rule | Growth a year | Sharpe | Largest drop | Sharpe minus hold bitcoin | Sharpe minus hold the basket |
|---|---|---|---|---|---|
| Hold bitcoin | +43.5% | 1.00 | -53.1% | | |
| Hold the basket | -2.5% | 0.31 | -80.3% | | |
| K1 | -6.0% | 0.02 | -62.1% | -0.98 | -0.29 |
| K2 | -11.8% | -0.06 | -73.4% | -1.06 | -0.37 |
| K3 | -5.9% | 0.01 | -62.6% | -0.99 | -0.30 |
| K4 | +23.3% | 0.79 | -33.6% | -0.21 | +0.48 |
| K5 | +33.0% | 1.04 | -34.7% | +0.03 | +0.72 |

The other two venues (Kraken entry, Coinbase entry) cost more, and every rule has a lower held-back Sharpe ratio there than at Kraken $10k tier. Their numbers are in the output file.

## Pass marks

The same five marks as before, at each venue, with the numbers read from `config/thresholds.yaml`. Mark 1: a higher Sharpe ratio than holding bitcoin in the held-back slice, with a largest drop no more than 0.6 times holding's (`replay_max_drop_ratio_vs_hold`). Mark 2: break-even cost at least 2 times the bitcoin cost per side (`backtest_min_breakeven_cost_multiple`). Mark 3: deflated Sharpe above 0.95 (`replay_min_deflated_sharpe`), counting 49 trials. Mark 4: overfitting estimate below 0.25 (`backtest_max_pbo`). Mark 5: the rule beats more than 0.95 of 1,000 shuffles of its own timing (`replay_min_shuffle_percentile`).

| Rule | Venue | 1 held-back | 2 break-even | 3 deflated Sharpe | 4 overfitting | 5 shuffle | Verdict | Same marks against holding the basket (reported, not the verdict) |
|---|---|---|---|---|---|---|---|---|
| K1 | Binance.US | fail | fail | fail | PASS | PASS | fail | fail |
| K1 | Alpaca | fail | fail | fail | PASS | PASS | fail | fail |
| K1 | Kraken $10k tier | fail | fail | fail | PASS | PASS | fail | fail |
| K1 | Kraken entry | fail | fail | fail | PASS | PASS | fail | fail |
| K1 | Coinbase entry | fail | fail | fail | PASS | PASS | fail | fail |
| K2 | Binance.US | fail | fail | fail | PASS | PASS | fail | fail |
| K2 | Alpaca | fail | fail | fail | PASS | PASS | fail | fail |
| K2 | Kraken $10k tier | fail | fail | fail | PASS | PASS | fail | fail |
| K2 | Kraken entry | fail | fail | fail | PASS | PASS | fail | fail |
| K2 | Coinbase entry | fail | fail | fail | PASS | PASS | fail | fail |
| K3 | Binance.US | fail | fail | fail | PASS | PASS | fail | fail |
| K3 | Alpaca | fail | fail | fail | PASS | PASS | fail | fail |
| K3 | Kraken $10k tier | fail | fail | fail | PASS | PASS | fail | fail |
| K3 | Kraken entry | fail | fail | fail | PASS | PASS | fail | fail |
| K3 | Coinbase entry | fail | fail | fail | PASS | PASS | fail | fail |
| K4 | Binance.US | PASS | PASS | fail | PASS | PASS | fail | fail |
| K4 | Alpaca | fail | PASS | fail | PASS | PASS | fail | fail |
| K4 | Kraken $10k tier | fail | PASS | fail | PASS | PASS | fail | fail |
| K4 | Kraken entry | fail | fail | fail | PASS | PASS | fail | fail |
| K4 | Coinbase entry | fail | fail | fail | PASS | PASS | fail | fail |
| K5 | Binance.US | fail | PASS | fail | PASS | fail | fail | fail |
| K5 | Alpaca | fail | PASS | fail | PASS | fail | fail | fail |
| K5 | Kraken $10k tier | fail | PASS | fail | PASS | fail | fail | fail |
| K5 | Kraken entry | fail | fail | fail | PASS | fail | fail | fail |
| K5 | Coinbase entry | fail | fail | fail | PASS | fail | fail | fail |

The numbers behind the marks at Kraken $10k tier:

| Rule | Largest drop as a share of hold bitcoin's | Break-even cost a side, against hold bitcoin | Deflated Sharpe | Overfitting estimate (all five rules) | Share of shuffles beaten |
|---|---|---|---|---|---|
| K1 | 117% | never ahead | 0.245 | 0.107 | 99.8% |
| K2 | 138% | never ahead | 0.138 | 0.107 | 97.9% |
| K3 | 118% | never ahead | 0.186 | 0.107 | 99.8% |
| K4 | 63% | 89 bps | 0.804 | 0.107 | 99.5% |
| K5 | 65% | 88 bps | 0.698 | 0.107 | 91.4% |

The same at Binance.US:

| Rule | Largest drop as a share of hold bitcoin's | Break-even cost a side, against hold bitcoin | Deflated Sharpe | Overfitting estimate (all five rules) | Share of shuffles beaten |
|---|---|---|---|---|---|
| K1 | 107% | never ahead | 0.504 | 0.096 | 99.4% |
| K2 | 129% | never ahead | 0.345 | 0.096 | 96.6% |
| K3 | 108% | never ahead | 0.428 | 0.096 | 99.4% |
| K4 | 56% | 89 bps | 0.933 | 0.096 | 99.2% |
| K5 | 63% | 88 bps | 0.820 | 0.096 | 91.4% |

Notes on the marks:

- Break-even cost is the same at every venue: it is the cost per side on bitcoin and ether at which the rule stops being ahead of holding bitcoin, with every other coin paying 20 bps more. K1: never ahead; K2: never ahead; K3: never ahead; K4: 89 bps; K5: 88 bps.
- The overfitting estimate is between 0.067 and 0.109 across venues, under the bar everywhere. Exact ties with the middle rank were 1.6% to 2.7% of splits. With the latest days dropped instead of the earliest it is 0.064 to 0.105. There are only five trials, so this mark says little here.
- The shuffles move each coin's own trend weights to a random start and wrap them around, inside that coin's own history, and leave the monthly baskets as they were. K1, K2 and K3 beat 96.6% to 100.0% of their shuffles. Corrected after the audit: the shuffles of K1 to K3 hold less and trade less than the rules (finding 04-04), so this is not a test matched on time in the market, and mark 5 means less for them. K5 beat 91.4% to 91.7%, a fail.

## Year by year

Kraken $10k tier. Change in account value over each calendar year.

| Year | K1 | K4 | Hold bitcoin | Hold the basket |
|---|---|---|---|---|
| 2018 (from 2018-06-01) | -23.9% | -11.8% | -50.9% | -69.1% |
| 2019 | +20.5% | +48.2% | +94.2% | +11.5% |
| 2020 | +77.5% | +209.3% | +304.0% | +189.4% |
| 2021 | +133.0% | +116.2% | +59.4% | +304.4% |
| 2022 | -41.1% | -32.9% | -64.2% | -75.2% |
| 2023 | +35.5% | +55.4% | +155.6% | +133.4% |
| 2024 | +23.3% | +40.7% | +121.0% | +45.2% |
| 2025 | -41.6% | +5.2% | -6.3% | -55.2% |
| 2026 (to 2026-09-30) | +7.2% | +14.3% | -4.5% | -0.2% |

## Sensitivities

Each sensitivity changes one thing from the base run. They are reported, not marked.

Held-back Sharpe ratio, base run / with 50 bps slippage on every coin other than bitcoin and ether:

| Rule | Binance.US | Alpaca | Kraken $10k tier | Kraken entry | Coinbase entry |
|---|---|---|---|---|---|
| K1 | 0.26 / 0.12 | 0.11 / -0.03 | 0.02 / -0.11 | -0.25 / -0.38 | -0.32 / -0.45 |
| K2 | 0.16 / 0.04 | 0.02 / -0.09 | -0.06 / -0.17 | -0.30 / -0.41 | -0.36 / -0.47 |
| K3 | 0.25 / 0.10 | 0.10 / -0.05 | 0.01 / -0.14 | -0.26 / -0.42 | -0.33 / -0.49 |
| K4 | 1.02 / 1.02 | 0.88 / 0.88 | 0.79 / 0.79 | 0.53 / 0.53 | 0.47 / 0.47 |
| K5 | 1.13 / 1.13 | 1.07 / 1.07 | 1.04 / 1.04 | 0.93 / 0.93 | 0.90 / 0.90 |

- With the higher slippage, K1, K2 and K3 lose 0.11 to 0.16 of held-back Sharpe ratio. K4 and K5 hold only bitcoin and ether, so they are unchanged. Rule and venue pairs that would pass mark 1 with the higher slippage: K4 at Binance.US.
- Half of the last value lost when a coin's history ends: no change at all. No position was open when a coin's history ended (0 such sales across both sensitivities, all rules and all venues), so there was nothing for the loss to act on. This sensitivity did not test any real loss from a dead coin.

## Where the plan could not be followed to the letter

- File count: the plan says 760 files. 753 were used. Corrected after the audit: only 3 of the 7 left out are priced in another coin. MERLUSD was wrongly left out by a name test, and 3 files have one row (finding 04-05).
- Band: the basket engine written for this replay (`basket.simulate_basket`) traded any move to or from zero whatever the band, as the first rig did. The audit amendment (change A12) and the plan's own words say a coin trades only when its weight is off target by more than one eighth of a slot. A new engine follows the plan's words. It still sells a coin that leaves its basket, or whose history ends, whatever the band, because the plan says those coins are sold. The old exception would have fired on 0 coin-days across all rules and venues, so this change made no difference to the results. The old engine is kept unchanged.
- Gold token: the price-swing test did not remove PAXGUSD in 12 months, although the plan says it removes gold tokens.
- Dead coins: the plan expects positions to be sold at a coin's last close when its history ends. That never happened: no coin that died had an open position at the end of its history. Corrected after the audit: not every dead coin had left its basket before its last trade (RNDRUSD and FTMUSD did not, finding 04-06). The code for this sale also uses hindsight (finding 04-01).
- K3: in 22 months fewer than 20 coins qualified. K3 held what qualified, still one twentieth each.
- The one-hour-late fill used in replay 01 is not part of this plan and was not run. Mark 1 uses the next-open fill only.
- The audit amendment (change A09) says break-even, shuffles and marks apply to single-coin trials only. This plan asks for marks on basket rules. This plan was followed.
- Costs differ by coin, so break-even adds the same number of bps to every coin, with other coins keeping their 20 bps extra slippage. Mark 2 compares it with the venue's bitcoin cost.
- K5 uses the daily close at 00:00 UTC in place of the 4 p.m. New York price, and the bar dated Wednesday as Wednesday's close (STATED in the plan).
- Every reading choice made in the code is listed in `research_rig/results_04.json` under `reading_choices` and in `research_rig/NOTES_04_builder.md`.

## What the independent audit found

A different AI model audited `run_04.py` and `basket.py`, rebuilt the selection and K1, K4 and both comparisons in its own code, and probed for use of future data. Its report is `audit/2026-11-25_replay_04_audit.md`, with `audit/replay_04_independent.py` and `audit/replay_04_probes.py`. It found 15 points. None of the changes it tested produced a pass against holding bitcoin. The lead decided not to change `basket.py` or rerun tonight, so the result stands as run, with these faults stated. The figures in this table are the auditor's, not this run's.

| Finding | What the auditor found (MEASURED by the auditor) | Effect on this result |
|---|---|---|
| 04-01 | The sale of a coin whose history ends uses the last bar of the full archive. That is hindsight: on the day after a last print the engine assumes the coin is gone for good and books a sale at the earlier close. In the auditor's four-row test, adding only a later print changed the account value on an earlier day from 0.49950025 to 0.99950025 | Never fired here: zero such sales in every base and sensitivity run. Must be fixed before `basket.py` is used again |
| 04-02 | Trade sizes use the account value before costs. So the monthly hold-the-basket comparison is not exactly equal parts after costs. Largest gap from equal parts at Binance.US: 0.00046541 of the account (July 2020). Sizing on the value after costs moves held-back Sharpe of hold the basket from 0.328049 to 0.327906 and of K1 from 0.258361 to 0.262360 | K4 deflated Sharpe at Binance.US moves from 0.9331335 to 0.9332411, still a fail. Kraken $10k tier still fails mark 3 |
| 04-03 | In the monthly hold-the-basket comparison, a buy order is cleared once its coin trades, even if there was no cash yet to fund it. A delayed sale could then leave the comparison in cash | Did not happen in this run: both comparisons had zero waiting orders |
| 04-04 | The shuffle test for the basket rules is not matched on time in the market or number of trades, because the monthly baskets are applied after the shift. At Binance.US, K1 made 6,529 trade sides at 45.18% average weight against shuffle means of 6,256.17 and 42.29%; K2 3,474 and 52.01% against 3,252.78 and 43.09%; K3 12,577 and 41.84% against 11,816.43 and 37.71%. K4 was close (1,161 and 52.12% against 1,163.70 and 52.00%). For K5 the shift moves Wednesday signals to other weekdays | Mark 5 means less for K1 to K3. K5 with the weekday kept: 0.919 against 0.914 as run, both fail |
| 04-05 | Of the 7 files left out, 3 are priced in another coin (ETHPYUSD, XBTPYUSD, XRPRLUSD), 1 is the real Merlin Chain dollar market (MERLUSD) wrongly left out by a name test, and 3 are files with one row (CTUSD, OUSDUSD, WOJAKUSD) | Restoring MERLUSD changes no monthly list |
| 04-06 | RNDRUSD (last print 2024-06-30) was still chosen on 2024-07-01, and FTMUSD (last print 2025-03-31) was still chosen on 2025-04-01. Neither had a position to sell | The half-value loss test therefore tested no real loss |
| 04-07 | The price-swing test does not always remove gold. PAXGUSD was in the top 20 in 12 months and the top 10 in April and May 2026 | No code fault. The plan's description of the test is wrong. Removing gold by name now would be a different basket, not a repair |
| 04-13 | Trial ledger rows for the 8 stock trials and the 5 basket trials were missing when the run was made. The determinism line in the builder notes was a placeholder when the audit read it | The lead has since added rows 43 to 55 to `research_rig/TRIAL_LEDGER.md` with a note (STATED by the lead). The run was repeated with the same settings and gave the same output (see `research_rig/NOTES_04_builder.md`) |
| 04-15 | A coin's trend weight calendar ends at its last raw bar, known only from the full archive. When the auditor added one later print to each of 81 ended coins, 18 K3 target coin-days for RNDRUSD in July 2024 changed | No change to any account value, because no coin could be bought on those days |

The other findings (04-08 to 04-12, 04-14) are small or are about checks and wording. See the report.

## What this does and does not show

- In the held-back slice at Kraken $10k tier, holding the basket grew -2.5% a year with a largest drop of -80.3%. Holding bitcoin grew +43.5% a year with a largest drop of -53.1%. K1 to K3 had a lower held-back Sharpe ratio than holding bitcoin at every venue.
- The plan's reason for this test was that trend rules are said to work better across many coins than on one (STATED). In this test, at every venue, K1, K2 and K3 had a lower held-back Sharpe ratio than K4 and K5.
- These rules trade a lot. Over the whole test at Kraken $10k tier, traded dollars a year were K1 22.3, K2 25.3, K3 21.5, K4 19.2, K5 8.1 times the account. Average coins held: K1 6.8, K2 3.8, K3 12.7, K4 1.5, K5 0.7.
- One venue's listings. A coin enters the data when Kraken listed it (STATED in the plan).
- The slippage for small coins is assumed. Document 24 compares it with sampled order books.
- The held-back slice had already been used by replays 01 and 03. It is not fresh.
- The three months after the designer's knowledge cutoff (2026-07-01 to 2026-09-30) are too short to mean anything. At Kraken $10k tier: K1 +29.8%, K2 +45.3%, K3 +32.8%, K4 +26.3%, K5 +9.5%, hold bitcoin +42.8%, hold the basket +65.8%.
- The terms for using Kraken's files are not stated on its page (UNKNOWN).
- Taxes are not modelled.

## Files

- Plan: `research_rig/PREREG_04_coin_basket_trend.md`. Measuring rules: `research_rig/AMENDMENT_2026-11-25_audit_fixes.md`
- Code: `research_rig/run_04.py`, `basket.py`, `rig2.py`, `rules.py`, `build_doc23.py`. Checks: `research_rig/fixtures2.py`, `fixtures_basket.py`
- Output: `research_rig/results_04.json`, `run_04.log`. Builder notes: `research_rig/NOTES_04_builder.md`
- Trials counted so far: 49 (`research_rig/TRIAL_LEDGER.md`)

## Sources

- [Kraken, downloadable historical OHLCVT data](https://support.kraken.com/articles/360047124832-downloadable-historical-ohlcvt-open-high-low-close-volume-trades-data)
- [CoinDesk trend indicator methodology](https://downloads.coindesk.com/cd3/CDI/Trend-Indicator-Methodology.pdf)
