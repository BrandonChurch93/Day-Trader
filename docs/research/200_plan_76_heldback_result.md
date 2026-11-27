# 200. Plan 76, the held-back run: buy a coin after a one-hour fall, hold a day

- MEASURED: did not pass. After 75 bp a side the rule made +0.36% a trade on years it had never seen, but -0.28% with each year's best trade taken out, so one of the four marks failed.
- INFERENCE: the closest miss so far on a rule that trades in days. At 15 bp a side all four marks were met, which earns practice card E14 on Binance.US books, not a counted pass.

## Where the result comes from

Source of this section: the independent auditor's blind recompute report, `/home/user/workspace/out/p76_blind_recompute.md` (SHA-256 `ce70a457aa66`, kept off the repo, aggregates only). The stage results hold no per-trade rows, so these lines are not computed here and the scorer was not run again. This script checks that each breakdown adds back to the official 15 bp mean.

- MEASURED by the auditor, by entry year at 15 bp a side: 2024 +3.71% (42 trades); 2025 -0.44% (25 trades); 2026 -0.91% (16 trades).
- MEASURED by the auditor: SHIB made +8.19% a trade over 11 trades. Without SHIB the other 72 trades average +0.56% at 15 bp a side and -0.64% at 75 bp.
- MEASURED by the auditor: the 4 pairs with the most hours of no price change (AAVE, SHIB, HBAR, LINK) carry 54 of the 83 signals and average +2.90% at 15 bp a side. The other 29 average -0.89% at 15 bp.
- INFERENCE: the result rests on 2024 and on thinly traded pairs, whose hourly opens are the least likely to be real fills. Both later years lose even at 15 bp a side. It earns a forward card only.

Built by `research_rig/report_76.py` from the three stage results, each pinned by the SHA-256 on ledger row 229. No price, bar or trade row is in the repo. Plan: [`research_rig/PREREG_76_washout_rebound.md`](../../research_rig/PREREG_76_washout_rebound.md). bp means a hundredth of a percent. Labels: MEASURED is from the runs, STATED is from the plan or the ledger, INFERENCE is a reading, UNKNOWN is not measured.

## The rule in plain words

- STATED: 11 coins on Bitstamp US dollar hourly bars: AAVE, ADA, BCH, BTC, ETH, HBAR, LINK, LTC, SHIB, XLM, XRP. Source page: [Bitstamp API](https://www.bitstamp.net/api/).
- STATED: when a coin's hourly close is 5% or more below the close an hour before, buy it at the next hour's open. If several fell, buy the one that fell most.
- STATED: sell 24 hours later. One position at a time, so trades never overlap.
- STATED: the judged cost is 75 bp a side. A cheaper 15 bp a side line is shown; it can only earn a forward card.
- STATED: four marks, all at 75 bp a side: at least 64 trades; mean net per trade above zero; still above zero with each year's best trade taken out; better than more than 90% of 999 random books that buy the same coins at the same hours of the week.

## The held-back figures

- MEASURED: 2024-01-01 to 2026-11-26, run once at commit `8915352`. 83 completed trades: 42 in 2024, 25 in 2025, 16 in 2026. Void trades: 0. Delayed sales: 0.

| Mark | At 75 bp a side | Met | At 15 bp a side | Met |
|---|---|---|---|---|
| At least 64 trades | 83 | yes | 83 | yes |
| Mean net per trade above zero | +0.36% | yes | +1.57% | yes |
| Above zero without each year's best trade | -0.28% | no | +0.93% | yes |
| Better than more than 90% of random books | 998 of 999 | yes | 998 of 999 | yes |
| Marks met | 3 of 4 | | 4 of 4 | |

## What cost the rule can stand

- MEASURED, worked out here from the two lines with the plan's net formula: before costs the rule made +1.88% a trade.
- MEASURED, worked out here: the mean net reaches zero at 92.9 bp a side.
- MEASURED, worked out here: the failed mark, without each year's best trade, reaches zero at 61.1 bp a side. A flat cost does not change which trade is best or how the rule ranks against the random books, so all four marks hold at any flat cost under that figure.
- UNKNOWN: what a $250 order really costs in the hour after a 5% fall on a venue we can use. That is what E14 measures.

## Shown only, these decide nothing

- MEASURED: the 3.5% fall: 204 trades, -0.15% a trade at 75 bp a side, +1.05% at 15 bp.
- MEASURED: a 12-hour hold: 98 trades, -0.31% and +0.89%.
- MEASURED: buying one hour late: 83 trades, +0.44% and +1.65%.

## The two earlier stages

- MEASURED, count stage, no return read: signals that did not overlap, by entry year, 5% fall: 40 in 2020, 53 in 2021, 41 in 2022, 33 in 2023; 3.5% fall: 68 in 2020, 113 in 2021, 108 in 2022, 94 in 2023. One signal in each arm fell past the end date and was refused.
- STATED: the 5% arm needed at least 30 in each of 2022 and 2023, had them, and so became the judged arm.
- MEASURED, design stage, 2020-01-01 to 2023-12-31: 56 trades (40 in 2020, 16 in 2023), +2.15% a trade at 75 bp a side and +3.38% at 15 bp, better than 999 of 999 random books. Without each year's best trade: -2.07% and -0.88%. It went on to the held-back stage because the mean was above zero, as the plan says.
- STATED by the data custodian on ledger row 229: the design figure rests on one XRP position, entered 2020-12-28 23:00 UTC and sold 2023-07-14 00:00 UTC under the registered wait rule, when the coin could be bought again. It held the only slot for 927 days and is the largest trade in that book. The design figure is not evidence for the rule.

## Limits

- STATED: this is one test of 46 scored so far, with 4 counted passes.
- STATED: the prices are Bitstamp hourly bars, not Binance.US order books. Source: [Bitstamp API](https://www.bitstamp.net/api/).
- STATED: a 5% hourly move on a thin pair can be one stale print. A bar test cannot tell that from a real fall.
- UNKNOWN: the cost on a venue we can use in the hour after a fall.

## What happens next

- STATED: practice card E14 (queue 138, ledger 233) runs this rule forward on Binance.US books with pretend money, judged at 60 trades or 2028-11-30. Now: Running since 2026-11-26 6:20 PM MT (first hourly wake 7:03 PM MT) from the frozen build `e8248e9` after independent audit CLEAR with one accepted limit (ledger 233).
- STATED: Measurement 133 (queue 137), the hourly cost of a small trade on Binance.US, stopped 2026-11-26 7:00 PM MT on a build fault at its second wake and is closed unread. Its replacement, Measurement 134 (queue 139, ledger 234), records the same cost every hour for 720 wakes. Now: Running since 2026-11-26 7:24 PM MT.
- Blind recompute: done, stamped 2026-11-26 6:04 PM MT before the official result was opened, and it agrees on every mark. MEASURED, official then recompute: 83 and 83 trades; at 75 bp a side mean net +0.36% and +0.36%, without each year's best -0.28% and -0.28%; at 15 bp +1.57% and +1.57%.
- STATED by the auditor: it had seen the pass and fail pattern in a commit subject before it started; its figures were blind.
- UNKNOWN: whether the auditor's random draws match the scorer's call for call. The shares agree.
