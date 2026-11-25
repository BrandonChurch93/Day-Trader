# 16. Audit of the test rig, and the corrected results

Status: research result. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. This document replaces the verdict tables in documents 12, 12b and 15. Those documents stay as the record of the first run.

Every number below is MEASURED by `research_rig/run_v2.py` and read from its output by `research_rig/build_doc16.py`, unless it is tagged otherwise.

## Bottom line

- Two different AI models audited the rig code line by line, separately. Neither found a rule that used future prices. Both found faults in how results were measured.
- I wrote down every fix and pushed it before rerunning anything (`research_rig/AMENDMENT_2026-11-25_audit_fixes.md`). No slice was changed. Correction added later on 2026-11-25: an earlier version of this line also said no rule, cost or pass mark was changed. That was wrong. Two rows of that list are not engine fixes. A13 made pass mark 1 stricter than the plan wrote it, so that it must also hold with the fill one hour late. A08 changed what buy and hold pays when the break-even cost is worked out, from a flat 5 bps to the same cost as the rule. A third row, A12, is an engine fix to the 0.10 band check that changes the trades of one rule, P2. So a pass in this rerun did not come from engine fixes alone, and research recommends that none is credited (question 18b in `docs/decisions/morning_list_2026-11-25.md`).
- After the fixes, rules that pass on both price histories: Binance.US cost: P1, P2, S50, D20. In the first run that list was: none.
- So the fixes turned four failures into passes at the cheapest venue only. That is a result found after the fact. It is a reason to test in the practice account, not a result to rely on.
- The pass sits on a knife edge. The overfitting estimate for bitcoin on Kraken prices at Binance.US cost is 0.2409 against a bar of 0.25 (`backtest_max_pbo`). With the latest days dropped instead of the earliest it is 0.2645, which fails. On Bitstamp prices started on the same day as the Kraken history it is 0.4205, which fails.
- Mark 4 itself is too jumpy to trust as a yes or no. On made-up data with no edge at all, 8% of samples still came in under the bar. Moving the start date by one month flips the first run's result.
- At every other venue cost, including Alpaca and Kraken, no rule passes on both histories. Ether passes nowhere.
- Day trading rules on hourly bars: 0 of 80 rule, coin and venue combinations pass after the fixes. 16 of 16 lose money over the whole sample at Alpaca cost.

## Who audited, and how

| Auditor | Model | What it did | Report |
|---|---|---|---|
| A | GPT-6.2 Sol | Read every file. Wrote its own separate replay from scratch and compared it with the rig day by day. 18 findings | `audit/2026-11-25_auditor_a.md`, `audit/replay_independent.py`, `audit/diagnostics.py` |
| B | Gemini Neon | Checked the statistics against the original papers, ran them on made-up data, tested each hourly rule for use of future prices by changing future bars and watching for any change in earlier signals. 11 findings | `audit/2026-11-25_auditor_b.md`, `audit/pbo_stability.json` |

What they agreed on:

- No rule uses a price it could not have known. Signals use the close of bar t and fill at the open of bar t+1. MEASURED by both.
- The rule definitions match their written plans. MEASURED by both. The engine's 0.10 band check did not follow the plan's words for moves to or from zero, which changed the trades of one rule, P2 (fix A12).
- Auditor A's separate replay matched the rig's daily account value and Sharpe ratio to rounding. MEASURED by A.

## What was wrong, in plain words

| Fault | What it did to the results | Fixed in the rerun |
|---|---|---|
| Shuffled timing test (mark 5) mixed up the in and out spells | For in-or-out rules the shuffles traded about half as often as the real rule, so they paid less cost and were harder to beat. For the fractional rule P2 the shuffles traded about three times as often, so they were easier to beat | Yes. Shuffles now keep the same number of trades and the same time held |
| First day of each slice was dropped, and holding the coin was restarted from cash in each slice | Small. Holding paid an extra entry cost inside the held-back slice | Yes |
| Overfitting estimate (mark 4) used blocks of unequal size | Small shifts in the estimate | Yes. Equal blocks |
| Overfitting estimate counted an exact tie with the middle rank as overfit | With 9 rules this happens in about 1 split in 12. It moved the estimate from under the bar to just over it in the first cross-check | Reported three ways. The verdict keeps the first reading. See the section on mark 4 |
| Orders filled on bars with no trades | A few bars on each history | Yes. The order waits for the next bar that traded |
| Break-even cost search stopped at 600 bps and compared against holding at a fixed 5 bps | Reported numbers were capped. Slightly unfair to the rules | Yes. Search to 2,560 bps, holding pays the same cost |
| The one-hour-late fill was a side table | Mark 1 only used the ideal fill | Yes. Mark 1 must hold with the fill one hour late as well. The worse of the two is shown |
| Checks printed a failure but did not stop the run | None seen, but a failed check could have been missed | Yes. A failed check stops everything |
| Pass mark numbers were typed into scripts | None, but against the rule that each number lives in one place | Yes. Read from `config/thresholds.yaml` at run time |
| Cross-check X1 was described as Kraken prices | It was a mix of two sources | Relabelled as a mixed-source check. X2 replaces it |

The full list, with file and line for each, is in the two audit reports and the amendment.

## Rerun: how many verdicts moved

| Run | Rule and venue pairs | Passed, first run | Passed, rerun | Single marks that changed |
|---|---|---|---|---|
| Replay 01 (Bitstamp prices) | 90 | 8 | 9 | 15 |
| Cross-check X2 (Kraken prices) | 90 | 0 | 4 | 19 |
| Sensitivity S2 (ether from 2016, Kraken prices) | 45 | 0 | 0 | 3 |
| Replay 03 (hourly rules) | 80 | 0 | 0 | 62 |

Every mark that changed on the daily rules, in both directions:

| Run | Venue cost | Coin | Rule | What changed (first run to rerun) |
|---|---|---|---|---|
| R01 | Kraken $10k tier | Bitcoin | P1 | mark 4 overfitting: fail to PASS |
| R01 | Kraken $10k tier | Bitcoin | P2 | mark 4 overfitting: fail to PASS |
| R01 | Kraken $10k tier | Bitcoin | S50 | mark 4 overfitting: fail to PASS; verdict: fail to PASS |
| R01 | Kraken $10k tier | Bitcoin | S100 | mark 4 overfitting: fail to PASS |
| R01 | Kraken $10k tier | Bitcoin | S200 | mark 4 overfitting: fail to PASS |
| R01 | Kraken $10k tier | Bitcoin | D20 | mark 4 overfitting: fail to PASS |
| R01 | Kraken $10k tier | Bitcoin | D55 | mark 4 overfitting: fail to PASS |
| R01 | Kraken $10k tier | Bitcoin | M30 | mark 4 overfitting: fail to PASS |
| R01 | Kraken $10k tier | Bitcoin | M90 | mark 4 overfitting: fail to PASS |
| R01 | Kraken $10k tier | Ether | S100 | mark 2 break-even: fail to PASS |
| R01 | Kraken $10k tier | Ether | S200 | mark 1 held-back: PASS to fail |
| R01 | Kraken entry | Bitcoin | M30 | mark 5 shuffle: fail to PASS |
| R01 | Coinbase entry | Bitcoin | M30 | mark 5 shuffle: fail to PASS |
| R01 | Coinbase entry | Bitcoin | M90 | mark 5 shuffle: fail to PASS |
| R01 | Coinbase entry | Ether | S50 | mark 5 shuffle: fail to PASS |
| X2 | Binance.US | Bitcoin | P1 | mark 4 overfitting: fail to PASS; verdict: fail to PASS |
| X2 | Binance.US | Bitcoin | P2 | mark 4 overfitting: fail to PASS; verdict: fail to PASS |
| X2 | Binance.US | Bitcoin | S50 | mark 4 overfitting: fail to PASS; verdict: fail to PASS |
| X2 | Binance.US | Bitcoin | S100 | mark 4 overfitting: fail to PASS |
| X2 | Binance.US | Bitcoin | S200 | mark 4 overfitting: fail to PASS |
| X2 | Binance.US | Bitcoin | D20 | mark 4 overfitting: fail to PASS; verdict: fail to PASS |
| X2 | Binance.US | Bitcoin | D55 | mark 4 overfitting: fail to PASS |
| X2 | Binance.US | Bitcoin | M30 | mark 4 overfitting: fail to PASS |
| X2 | Binance.US | Bitcoin | M90 | mark 4 overfitting: fail to PASS |
| X2 | Binance.US | Ether | S50 | mark 3 deflated Sharpe: PASS to fail |
| X2 | Kraken $10k tier | Ether | P2 | mark 3 deflated Sharpe: PASS to fail |
| X2 | Kraken $10k tier | Ether | S100 | mark 2 break-even: fail to PASS |
| X2 | Kraken $10k tier | Ether | S200 | mark 1 held-back: PASS to fail |
| X2 | Kraken $10k tier | Ether | D55 | mark 3 deflated Sharpe: PASS to fail |
| X2 | Kraken entry | Bitcoin | S100 | mark 5 shuffle: fail to PASS |
| X2 | Kraken entry | Bitcoin | M30 | mark 5 shuffle: fail to PASS |
| X2 | Kraken entry | Bitcoin | M90 | mark 3 deflated Sharpe: PASS to fail |
| X2 | Coinbase entry | Bitcoin | S100 | mark 5 shuffle: fail to PASS |
| X2 | Coinbase entry | Bitcoin | M30 | mark 5 shuffle: fail to PASS |
| S2 | Kraken $10k tier | Ether | S200 | mark 1 held-back: PASS to fail |
| S2 | Kraken entry | Ether | S200 | mark 5 shuffle: fail to PASS |
| S2 | Coinbase entry | Ether | S200 | mark 5 shuffle: fail to PASS |

Marks that changed on the hourly rules (the full list is in `research_rig/compare_v1_v2.json`):

- Mark 5 shuffle, fail to PASS: 60 rule, coin and venue combinations.
- Mark 5 shuffle, PASS to fail: 1 rule, coin and venue combinations.
- Mark 1 held-back, PASS to fail: 1 rule, coin and venue combinations.

Why mark 5 moved so much on the hourly rules: in the first run the shuffles traded about half as often as the real rule, so at high cost the shuffles paid far less and won. With the same number of trades on both sides, most hourly rules do beat random timing. That says their timing is better than chance before costs. It does not make them profitable. Each of them still fails marks 1, 2 and 3.

## Corrected verdicts for the daily rules

A rule passes for a venue only if it passes all five marks on both price histories. Rows where nothing passed in either run are left out.

| Venue cost | Coin | Rule | Bitstamp prices | Kraken prices | Both, rerun | Both, first run | Marks failed on Kraken prices |
|---|---|---|---|---|---|---|---|
| Binance.US (7 bps) | Bitcoin | P1 | PASS | PASS | PASS | fail | none |
| Binance.US (7 bps) | Bitcoin | P2 | PASS | PASS | PASS | fail | none |
| Binance.US (7 bps) | Bitcoin | S50 | PASS | PASS | PASS | fail | none |
| Binance.US (7 bps) | Bitcoin | D20 | PASS | PASS | PASS | fail | none |
| Binance.US (7 bps) | Bitcoin | M90 | PASS | fail | fail | fail | 5 shuffle |
| Alpaca (30 bps) | Bitcoin | P2 | PASS | fail | fail | fail | 4 overfitting |
| Alpaca (30 bps) | Bitcoin | S50 | PASS | fail | fail | fail | 4 overfitting |
| Alpaca (30 bps) | Bitcoin | D20 | PASS | fail | fail | fail | 4 overfitting |
| Kraken $10k tier (43 bps) | Bitcoin | S50 | PASS | fail | fail | fail | 4 overfitting |

What the passing rules are:

| Rule | In plain words |
|---|---|
| P1 | Hold a share of the account in bitcoin equal to how many of four averages (20, 50, 100, 200 days) the price is above |
| P2 | Like P1, with the size turned down when the price has been jumpy |
| S50 | In when the price is above its 50-day average, out when below |
| D20 | In when the price makes a 20-day high, out when it makes a 10-day low |

### Bitcoin, held-back slice (2023-01-01 to 2026-06-30), at Binance.US cost

Sharpe and largest drop are the worse of the two fills (ideal, and one hour late).

| Rule | Sharpe, Bitstamp | Sharpe, Kraken | Largest drop, Bitstamp | Largest drop, Kraken | Growth a year, Bitstamp | Growth a year, Kraken | Share of shuffles beaten, Kraken | Deflated Sharpe, Kraken |
|---|---|---|---|---|---|---|---|---|
| Hold bitcoin | 1.00 | 1.00 | -53.1% | -53.1% | +43.5% | +43.5% | | |
| P1 | 1.15 | 1.15 | -28.6% | -28.8% | +38.0% | +38.0% | 99.4% | 0.999 |
| P2 | 1.21 | 1.21 | -21.9% | -21.9% | +35.0% | +35.2% | 99.8% | 1.000 |
| S50 | 1.37 | 1.37 | -27.9% | -27.7% | +51.5% | +51.7% | 100.0% | 1.000 |
| S100 | 1.02 | 1.02 | -36.6% | -36.7% | +35.7% | +35.9% | 98.9% | 0.995 |
| S200 | 0.99 | 1.00 | -31.6% | -31.6% | +36.1% | +36.2% | 94.3% | 0.989 |
| D20 | 1.17 | 1.17 | -28.9% | -28.8% | +35.6% | +35.9% | 99.7% | 0.999 |
| D55 | 1.06 | 0.96 | -32.8% | -35.6% | +30.7% | +27.2% | 99.7% | 0.997 |
| M30 | 1.07 | 1.06 | -35.5% | -35.6% | +36.4% | +35.9% | 100.0% | 0.997 |
| M90 | 1.01 | 1.01 | -29.0% | -29.1% | +36.8% | +36.8% | 92.6% | 0.981 |

### Bitcoin, held-back slice, at Alpaca cost

| Rule | Sharpe, Bitstamp | Sharpe, Kraken | Largest drop, Bitstamp | Largest drop, Kraken | Growth a year, Bitstamp | Growth a year, Kraken | Share of shuffles beaten, Kraken | Deflated Sharpe, Kraken |
|---|---|---|---|---|---|---|---|---|
| Hold bitcoin | 1.00 | 1.00 | -53.1% | -53.1% | +43.5% | +43.5% | | |
| P1 | 0.99 | 0.99 | -31.1% | -31.4% | +31.3% | +31.2% | 99.3% | 0.998 |
| P2 | 1.05 | 1.05 | -24.1% | -24.1% | +29.2% | +29.3% | 99.8% | 1.000 |
| S50 | 1.22 | 1.23 | -30.1% | -30.0% | +44.3% | +44.5% | 100.0% | 0.999 |
| S100 | 0.91 | 0.91 | -39.2% | -39.3% | +30.8% | +31.0% | 98.9% | 0.994 |
| S200 | 0.94 | 0.94 | -33.1% | -33.1% | +33.2% | +33.4% | 94.2% | 0.988 |
| D20 | 1.03 | 1.03 | -31.1% | -31.0% | +30.2% | +30.5% | 99.7% | 0.998 |
| D55 | 0.99 | 0.89 | -34.4% | -37.6% | +28.3% | +24.7% | 99.7% | 0.997 |
| M30 | 0.85 | 0.84 | -39.9% | -41.3% | +26.4% | +25.9% | 99.9% | 0.990 |
| M90 | 0.92 | 0.92 | -32.0% | -32.2% | +32.3% | +32.4% | 92.6% | 0.976 |

How to read these, at Binance.US cost in the held-back years: on Bitstamp prices 3 of the 4 passing rules grew less than holding bitcoin, and their largest drop was 41% to 54% of the drop from holding; on Kraken prices 3 of the 4 passing rules grew less than holding bitcoin, and their largest drop was 41% to 54% of the drop from holding. A rule passes mark 1 by having a better Sharpe ratio and a much smaller drop. Mark 1 does not ask for more growth than holding.

## Mark 4 is not stable enough to be a yes or no gate

Mark 4 asks: if you pick the best rule on half of the history, how often does it land in the bottom half on the other half? The bar is 0.25 (`backtest_max_pbo`).

### Three ways to count a tie

The [paper](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) says "below the median". It does not say what to do when the winner lands exactly on the median, which can only happen with an odd number of rules. STATED by the paper, read by auditor B and by me. (Corrected 2026-11-25: that is true when every rule has a different result. The code gives equal results the average of their ranks, so with an even number of rules a tie can still happen when two rules have exactly equal results on the other half. A tenth reader found this.)

| Run | Venue cost | Coin | First run | Rerun (ties count as overfit, the verdict) | Ties count as half | Ties count as not overfit | Share of splits that tie | Rerun with the latest days dropped instead |
|---|---|---|---|---|---|---|---|---|
| R01 | Binance.US | Bitcoin | 0.1199 | 0.0911 | 0.0814 | 0.0716 | 2.0% | 0.0951 |
| R01 | Alpaca | Bitcoin | 0.2026 | 0.1608 | 0.1425 | 0.1242 | 3.7% | 0.1664 |
| R01 | Kraken $10k tier | Bitcoin | 0.2619 | 0.2110 | 0.1851 | 0.1593 | 5.2% | 0.2227 |
| R01 | Kraken entry | Bitcoin | 0.4009 | 0.3437 | 0.3001 | 0.2566 | 8.7% | 0.3545 |
| R01 | Coinbase entry | Bitcoin | 0.4113 | 0.3629 | 0.3185 | 0.2741 | 8.9% | 0.3767 |
| X2 | Binance.US | Bitcoin | 0.2501 | 0.2409 | 0.2005 | 0.1601 | 8.1% | 0.2645 |
| X2 | Alpaca | Bitcoin | 0.4042 | 0.3795 | 0.3288 | 0.2782 | 10.1% | 0.4191 |
| X2 | Kraken $10k tier | Bitcoin | 0.5110 | 0.4946 | 0.4387 | 0.3828 | 11.2% | 0.5272 |
| X2 | Kraken entry | Bitcoin | 0.7839 | 0.7775 | 0.6971 | 0.6167 | 16.1% | 0.8054 |
| X2 | Coinbase entry | Bitcoin | 0.7561 | 0.7712 | 0.6967 | 0.6221 | 14.9% | 0.8035 |
| DIAG | Binance.US | Bitcoin | 0.4675 | 0.4205 | 0.3846 | 0.3486 | 7.2% | 0.4151 |
| DIAG | Alpaca | Bitcoin | 0.6253 | 0.5672 | 0.5279 | 0.4885 | 7.9% | 0.5704 |
| DIAG | Kraken $10k tier | Bitcoin | 0.7253 | 0.6646 | 0.6194 | 0.5743 | 9.0% | 0.6631 |
| DIAG | Kraken entry | Bitcoin | 0.6888 | 0.6938 | 0.6418 | 0.5897 | 10.4% | 0.7246 |
| DIAG | Coinbase entry | Bitcoin | 0.6274 | 0.6556 | 0.6098 | 0.5641 | 9.1% | 0.6869 |

### How much it moves when nothing real changes

MEASURED by auditor B with the first-run code (`audit/pbo_stability.json`):

- Start date moved one month at a time from 2013-01-01 to 2015-01-01 (25 start dates, Bitstamp bitcoin, Alpaca cost, first-run code): the estimate ran from 0.203 to 0.744, middle value 0.603. It was under the bar on 1 of 25 start dates. The one that passed is the start date the plan used.
- Number of blocks changed (8, 10, 12, 14, 16, 20) with start 2013-01-01: the estimate ran from 0.203 to 0.287, under the bar for 3 of 6 block counts.
- Number of blocks changed (8, 10, 12, 14, 16, 20) with start 2014-05-01: the estimate ran from 0.520 to 0.714, under the bar for 0 of 6 block counts.

MEASURED by me with the rerun code on made-up data where no rule has any edge (`research_rig/noise_pbo.py`, 100 samples each, 16 blocks). Marks 3 and 5 are built to let no-edge data through about 1 time in 20. Mark 4 at this bar lets it through more often than that:

| Made-up data with no edge | Average | Middle | 5th to 95th percentile | Lowest to highest | Share of samples under the bar |
|---|---|---|---|---|---|
| 9 rules, correlation 0.0 | 0.54 | 0.54 | 0.19 to 0.91 | 0.08 to 0.97 | 8.0% |
| 9 rules, correlation 0.8 | 0.54 | 0.54 | 0.18 to 0.91 | 0.08 to 0.97 | 8.0% |
| 5 rules, correlation 0.8 | 0.62 | 0.66 | 0.20 to 0.95 | 0.04 to 0.99 | 10.0% |
| 8 rules, correlation 0.8 | 0.48 | 0.49 | 0.15 to 0.82 | 0.06 to 0.94 | 12.0% |

What this means:

- A pass on mark 4 is weak evidence. A fail is weak evidence too.
- The first run's pass on Bitstamp prices depended on the start date the plan happened to use.
- The bar has not been changed. Changing how mark 4 is measured is a decision for the owner, and it should be made before the next test is run, not after.

One more sign of the same problem. The two price histories cover the same market. Started on the same day (2014-05-01) and charged Binance.US cost, the estimate is 0.241 on Kraken prices and 0.421 on Bitstamp prices. One passes and one fails. The Bitstamp pass in replay 01 comes from starting in 2013, before the Kraken history begins. The two venues' daily closing prices were not the same in the early years: the typical gap was 45 bps in 2014 to 2017 and 2.0 bps from 2020 on (`research_rig/venue_price_gap.json`). That is one likely reason the two answers differ. Whether it is the whole reason is UNKNOWN.

Proposal, not adopted: measure mark 4 as the middle value over a fixed set of start dates and block counts, written down before the run. This costs nothing and removes the knife edge. (Corrected 2026-11-25: that last claim overstated it. A fixed set of dates stops one start date from deciding. The mark stays noisy, as the made-up data test on this page shows. Also corrected 2026-11-25: this line also proposed counting ties as half. That is the easier reading, as the table above shows, and results have been seen. Research now recommends keeping ties counted as overfit. Decisions 1a and 1b in `docs/decisions/morning_list_2026-11-25.md`.)

## Day trading rules on hourly bars, after the fixes

| Coin | Rule | Round trips a year | Average gain per round trip before costs | Break-even cost per side against holding | Held-back Sharpe at Binance.US cost | Holding, same slice | Held-back growth a year at Alpaca cost | Marks passed at Binance.US cost |
|---|---|---|---|---|---|---|---|---|
| Bitcoin | H1 | 186 | +21.5 bps | 1.4 bps | -0.55 | 1.00 | -64.8% | 2 of 5 |
| Bitcoin | H2 | 224 | +20.2 bps | 1.2 bps | -0.23 | 1.00 | -68.9% | 2 of 5 |
| Bitcoin | H3 | 93 | +0.1 bps | never ahead | -3.63 | 1.00 | -42.7% | 1 of 5 |
| Bitcoin | H4 | 187 | +12.5 bps | never ahead | -1.31 | 1.00 | -68.4% | 2 of 5 |
| Bitcoin | H5 | 114 | +18.2 bps | never ahead | -0.92 | 1.00 | -51.5% | 2 of 5 |
| Bitcoin | H6 | 287 | +16.0 bps | 1.1 bps | -0.77 | 1.00 | -78.2% | 2 of 5 |
| Bitcoin | H7 | 122 | +31.2 bps | 4.2 bps | -0.10 | 1.00 | -45.7% | 2 of 5 |
| Bitcoin | H8 | 181 | +20.1 bps | 0.1 bps | -0.20 | 1.00 | -61.5% | 2 of 5 |
| Ether | H1 | 185 | +27.9 bps | 4.6 bps | -0.38 | 0.44 | -67.4% | 1 of 5 |
| Ether | H2 | 218 | +32.2 bps | 7.5 bps | 0.18 | 0.44 | -64.1% | 2 of 5 |
| Ether | H3 | 93 | +0.2 bps | never ahead | -2.73 | 0.44 | -44.5% | 1 of 5 |
| Ether | H4 | 188 | +6.5 bps | never ahead | -1.00 | 0.44 | -68.5% | 1 of 5 |
| Ether | H5 | 104 | +14.7 bps | never ahead | -0.43 | 0.44 | -42.8% | 2 of 5 |
| Ether | H6 | 275 | +13.9 bps | 0.4 bps | -0.59 | 0.44 | -77.3% | 1 of 5 |
| Ether | H7 | 117 | +36.3 bps | 6.3 bps | 0.44 | 0.44 | -35.7% | 2 of 5 |
| Ether | H8 | 183 | +31.1 bps | 5.8 bps | 0.34 | 0.44 | -55.6% | 2 of 5 |

Passes at any venue cost: 0 of 80 after the fixes, 0 of 80 in the first run. Document 15 has the rule definitions.

## What is still open

- The fixes were written after the first results were seen. Each one is tied to an audit finding and none changes a number in `config/thresholds.yaml`. Two of them do change what a pass mark asks (A13 and A08, see the correction near the top of this page), and a result that only appears after fixes deserves less trust than one that was there from the start.
- Both price histories cover the same market and the same years. Passing on both shows the result is not a quirk of one venue's prices. It does not show the rule will keep working.
- Binance.US cost is 7 bps per side, the lowest fee schedule checked. The owner has no account there, and whether a Binance.US account suits this project is an open decision (document 09). At Alpaca cost (30 bps per side) nothing passes on both histories.
- The held-back slice has now been looked at by replay 01, the cross-check, replay 03 and this rerun. It is no longer fresh. The only fresh test left is the practice account.
- The rerun of the hourly rules stopped twice on program errors (a process start-up setting and a reporting field of the wrong length). Both were fixed without touching any rule, cost or statistic, and the run was started again from the beginning.
- Auditor B also showed that the deflated Sharpe mark (mark 3) is sensitive to how alike the trials are. MEASURED by B on made-up data: with strongly related rules and no edge it passed 4.5% of the time. No change was made.

## Questions for the owner

| Question | Recommendation | Why |
|---|---|---|
| How should a tie be counted in mark 4 from now on? | As overfit, as in every test so far. (Corrected 2026-11-25: this row first said "as half") | Counting a tie as half is the neutral reading, and counting it as overfit pushes a no-edge result from 0.50 to about 0.56 with 9 rules. But half is the easier reading, results have been seen, and the owner's bar says never to loosen a limit after seeing a result. Keeping the full count is a cautious policy, not a claim that it is the more correct statistic. The rule list in a plan is never chosen to make ties more or less likely |
| Should mark 4 be measured over several start dates and block counts? | Yes, fixed in the plan before each run | One start date decides the result today. What this would do to the bitcoin results is UNKNOWN (corrected 2026-11-25: this row first said it would most likely turn the bitcoin passes back into fails, which was a guess). With the first-run code at Alpaca cost the middle value over 25 start dates was 0.603. It has not been measured at Binance.US cost, and research has not run it, so that the choice of method is not made by looking at its result |
| Do the four bitcoin rules go forward to the practice account? | Yes, as a practice test only, with P1 as the only bitcoin rule. The morning list proposes one stock rule beside it (`docs/decisions/morning_list_2026-11-25.md`, decision 5) | It is the plainest of the four, it was named as the primary rule before the first run, and practice trading is the only fresh test left |

## Files

- Plan for the fixes: `research_rig/AMENDMENT_2026-11-25_audit_fixes.md`
- Code: `research_rig/rig2.py`, `fixtures2.py` (19 checks, numbered up to 27; numbers 6 to 8 and 10 to 14 are not used), `run_v2.py`, `compare_v1_v2.py`, `noise_pbo.py`, `build_doc16.py`
- Outputs: `research_rig/results_v2.json`, `compare_v1_v2.json`, `noise_pbo.json`
- First run, unchanged: `engine.py`, `run_01*.py`, `run_03.py`, `results_01.json`, `results_01x2.json`, `results_03.json`

## Sources

- [Bailey, Borwein, López de Prado and Zhu, The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf)
- [Bailey and López de Prado, The Deflated Sharpe Ratio](https://davidhbailey.com/dhbpapers/deflated-sharpe.pdf)
