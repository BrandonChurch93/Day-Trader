# Replay 62. Special-dividend ex-day

## The rule

- STATED. Buy whole shares at the close before the verified ex-date and sell at the ex-date close. Match both closes with IWM.
- STATED. Start each leg with $500; charge the greater of 5 bp or $0.01 per share per side. Credit only verified cash.

## Did it pass?

MEASURED. Did not pass, **1 of 5 frozen marks**, in the one scored run at 2026-11-26 10:45:40 UTC. Only the placement mark was met: 316 matched pairs from 443 filing events. The frozen decision is to close the row.

## Frozen marks

MEASURED. Each mark was required. The paired values are stock minus IWM in percentage points (pp); the t statistic groups differences by ex-date across 285 dates.

| Mark | Frozen bar | Measured | Verdict |
| --- | --- | --- | --- |
| Placed pairs | At least 250 pairs | 316 | met |
| Raw paired mean | Above zero | -0.0607 pp | not met |
| Clipped evidence | Clip at ±600 bp; positive mean and ex-date clustered t at least 2 | -0.0815 pp; t -0.63 | not met |
| Trimmed paired mean | Above zero after dropping the best 1%, rounding up | -0.1806 pp; dropped 4 | not met |
| Positive ex-date years | At least 7 | 4 of 11 | not met |

## What happened by year

MEASURED. The mean paired result was positive in 4 of 11 ex-date years. These are raw paired means, after costs and before tax.

- 2016: -0.0028 pp.
- 2017: -0.5048 pp.
- 2018: +0.3730 pp.
- 2019: -0.2214 pp.
- 2020: +0.1282 pp.
- 2021: -0.3949 pp.
- 2022: +0.0857 pp.
- 2023: +1.3912 pp.
- 2024: -0.5595 pp.
- 2025: -0.2632 pp.
- 2026: -0.8666 pp.

## Shown only

MEASURED. These comparisons cannot count toward a mark. Rows show net stock minus IWM except for the named single-leg returns.

- Earlier entry (ex minus 2 close through ex-date close): +0.2915 pp on 316 pairs.
- Stock only: -0.1068% on 316 pairs.
- Matched IWM leg: -0.0461% on 316 pairs.
- Higher cost (10 bp per side, same cent floor): -0.0486 pp on 316 pairs.
- 24% haircut to verified special cash: -1.1766 pp on 316 pairs.
- At least $1,000,000 median dollar volume: -0.0813 pp on 229 pairs.
- Yield below 1%: -0.1602 pp on 69 pairs.
- Yield from 1% to below 3%: +0.1793 pp on 91 pairs.
- Yield at least 3%: -0.1567 pp on 156 pairs.
- Vendor exact match: -0.0375 pp on 230 pairs.
- Vendor Class A: -0.1229 pp on 86 pairs.
- Plain paired t, grouped by ex-date without clipping: -0.43.

## How the rule changed

- STATED. [Plan 61](../../research_rig/PREREG_61_special_dividend_ex_day.md) was frozen first. MEASURED. Its no-return validation found 230 placed pairs, below the 250 mark. It was not scored.
- STATED. The first proposal to accept all missing vendor matches was withdrawn before drafting. A wrong ex-date could put a trade on an ordinary day and still credit the dividend, overstating the return.
- STATED. Before counting, the lead fixed a narrower rule: accept an otherwise eligible missing exact match only when one supported vendor cash record on the verified ex-date was at least the docket special less $0.01. The recorded vendor amount never replaced the verified cash.
- MEASURED. The [price-blind count](../../research_rig/COUNT_62.json) found that 86 of 88 missing-only events met this Class A rule.
- STATED. [Plan 62](../../research_rig/PREREG_62_special_dividend_ex_day_v2.md) froze the change with all marks unchanged, before any target return.

## Gaps

- STATED. Printed closes were used. Actual closing-auction fills, broker cutoffs and how much could have been filled are UNKNOWN.
- UNKNOWN. The replay does not establish whether the ex-date was known at entry or when the exchange first posted or changed it.
- STATED. The judged results are before tax. The haircut is a sensitivity, not an account's tax result.
- STATED. The filing docket is the same as [Replay 60](126_replay_60_special_dividends.md), whose aggregate results were already known. This is a different holding window, not an independent set of filings.

## What it means

MEASURED. The published ex-day effect discussed in the [idea note](../127_idea_round_33.md) did not show on these 316 events after costs. The raw paired mean was -0.0607 pp; the row closes. This does not establish what would happen on other events.

## Run record

- MEASURED. Freeze: `fce6ae7383c50bc46d7cec54bac7b63fa7a3c25f`.
- MEASURED. Scoring approval: `d2d3407b04c5dafbb1713b6ef77cd082a35bc6df`.
- MEASURED. Saved aggregate result SHA-256: `14ab97954d2b8b02e4b5fdbe35fd803b9978328ec0bc5e10ad509d17f03aa99b`.
