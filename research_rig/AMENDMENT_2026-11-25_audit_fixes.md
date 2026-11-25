# Amendment, 2026-11-25: fixes after the code audit, written before any rerun

Written 2026-11-25 07:40 UTC. Pushed before `run_v2.py` is run. Not edited after the rerun except to add a dated note at the bottom.

Status: research rig, not the product. Proposed by research. No owner decision is recorded here.

## Why

Two independent models audited the rig after replay 01, cross-check X2 and replay 03 had been run. The first audit report is filed at `audit/2026-11-25_auditor_a.md`. It found no use of future prices. It did find faults in how results were measured and in two of the statistics. This file lists every change, so that the rerun cannot be shaped by its own results.

Honest limit: these fixes are made after the first results were seen. To keep that from helping any rule, every change of verdict is reported in both directions, the first results stay in the repo unchanged, and no pass mark number is changed.

## What does not change

- The rules (9 daily rules, 8 intraday rules, 1 clock control), the venues and costs, the slices, the seed, the trial counts (20 for the daily rules, 36 with the intraday rules).
- The five pass marks and their numbers in `config/thresholds.yaml`.
- The original scripts and JSON outputs. They stay as the record of the first run. The rerun lives in `rig2.py`, `fixtures2.py`, `run_v2.py` and `results_v2.json`.

## Changes, each tied to an audit finding

| Finding | First run | Rerun |
|---|---|---|
| A01 shuffled timing | In and out spells were put in any order. Spells of the same kind could land next to each other and merge, which cut the number of trades about in half and made the shuffles too cheap | In or out rules: the in spells are shuffled among the in slots and the out spells among the out slots, so the shuffles keep the same number of trades, the same time held and the same state at both ends. Fractional rules (P1, P2): the rule's whole sequence of target weights is started at a random point and wrapped around (shift of at least 30 bars). The average number of trades and average weight of the shuffles are reported next to the rule's own, as a check |
| A02, A03 first day and slices | Results were measured from the first day's closing value, which dropped the first day. Slices dropped their first day. Buy and hold in replay 01 was restarted from cash in each slice, while the rule carried its position in | Every equity series starts from the cash put in, one bar before the first bar. Every slice starts from the last value before the slice. Buy and hold is bought once at the start of the whole test and carried through every slice, for every replay |
| A04 dust | Selling everything could leave a tiny balance that was later sold again and counted as a trade | A full sale sets the coin balance to exactly zero. A full buy sets cash to exactly zero. A trade is counted only if it is larger than one billionth of the account |
| A05 overfitting estimate, block sizes | 16 blocks of unequal size when the number of days did not divide by 16 | 16 equal blocks. Days that do not fill a block are dropped from the start of the sample (the most recent data is kept). The result with the days dropped from the end instead is reported next to it. The verdict uses the first |
| A06 undefined values | A rule with no variation in a half of the sample gave an undefined Sharpe ratio that could count as "not overfit" | Such a case gets Sharpe 0 in that half and the number of cases is reported. A deflated Sharpe ratio, overfitting estimate or shuffle result that cannot be worked out fails its mark |
| A07 fills on bars that did not trade | Orders filled at the stated open of bars with zero volume and of days that were filled in because the venue had no trades | An order fills only on a bar that really traded (volume above zero, not filled in). Otherwise it waits for the next bar that traded and uses the newest signal at that time. The number of orders that had to wait is reported |
| A08 break-even cost | Search stopped at 600 bps and reported 600 as if it were the answer. Buy and hold was charged 5 bps whatever the rule was charged | Search on a fixed grid up to 2,560 bps, then narrowed. Reported as "never ahead", a number, or "above 2,560". Buy and hold pays the same cost per side as the rule. If the rule falls behind and then gets ahead again at a higher cost, the first crossing is used and the count of crossings is reported |
| A09 exposure | "Time invested" was the average weight | Both are reported: average weight, and share of days with any position. Turnover is traded dollars divided by the prior close's account value, per 365 days. Break-even, shuffles and the five marks apply to single-coin trials only. The two portfolios are reported with growth, Sharpe, largest drop and deflated Sharpe, as in the first run |
| A10 hourly data quality | Missing hours and zero-volume hours were reported together. The fallback start date was not coded | Reported separately. The fallback (first midnight after 4,800 hours of history) is coded and stops with an error if no year qualifies |
| A11 open positions | Not reported | Whether a rule is still in a position at the last bar is reported. Round trips are assigned to a slice by their entry time, as before, and this is now stated |
| A12 the 0.10 band | Moves to or from zero skipped the band | The plan's own words are followed: a trade happens only when the target differs from the current weight by more than 0.10, with no exception. This affects P2 only |
| A13 one hour late | Reported as a side table; the marks used the base fill only | Each daily rule is also run with the fill one hour late, at every venue (open of the venue's own 01:00 UTC hourly bar, the next traded hour that day if that one did not trade; a day with no traded hour after 01:00 cannot fill). Mark 1 must hold under both fills. The worse of the two is the one shown |
| A14 cross-check X1 | Described as Kraken prices | Not rerun. It is relabelled in the audit document as a mixed-source check, replaced by cross-check X2 |
| A15 checks | A failed check printed FAIL but did not stop anything | `fixtures2.py` exits with an error on any failure, `run_v2.py` runs it first and stops if it fails. Added checks: the fast engine equals the general engine on 1,000 random inputs, with and without bars that cannot fill; the shuffles keep trade count and time held; equal-block overfitting estimate on a hand-made case; break-even search on a known function. The fast engine refuses missing targets |
| A16 thresholds | Typed into each script | Read from `config/thresholds.yaml` at run time and written into the output |
| A17 inputs | Order, gaps and duplicates were assumed | Checked before any signal is worked out. The run stops if a check fails |
| A18 labels | Deflated Sharpe, overfitting estimate, shuffle and bootstrap in `results_01.json` were at Alpaca cost without saying so | Every figure is stored under its venue. The bootstrap range is worked out at every venue |

## What is rerun

| Run | Prices | Start | Was |
|---|---|---|---|
| R01 | Bitstamp daily | BTC 2013-01-01, ETH 2018-03-05 | Replay 01 |
| X2 | Kraken daily | BTC 2014-05-01, ETH 2018-03-05 | Cross-check X2 |
| S2-ETH | Kraken daily | ETH 2016-03-01 | Sensitivity S2 |
| DIAG | Bitstamp daily | BTC 2014-05-01 | The diagnostic written after X2. Still not pre-registered, still labelled as such |
| R03 | Bitstamp hourly | BTC 2016-01-01, ETH 2019-01-01 | Replay 03 |

## How the rerun is read

- Every verdict and every mark that differs from the first run is listed, in both directions.
- A rule passes for a venue only if it passes on both price histories, as in the X2 plan.
- If the rerun produces a pass where the first run had a fail, it is reported as "pass after audit fixes" and treated with the same caution as any result found after the fact: it is a reason to test further, not a result to rely on.
