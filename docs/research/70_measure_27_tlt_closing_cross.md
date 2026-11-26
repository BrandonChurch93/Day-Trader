# 70. Measurement 27: closing cross against the consolidated close on TLT month-end sessions

Written by `research_rig/measure_27.py --report` from `research_rig/measure_27_summary.json`, which was made from the off-repo per-session result of 2026-11-26 04:04 UTC (sha256 b32ccb2b76afe971). Plan: `research_rig/MEASURE_27_tlt_closing_cross.md`, ledger row 164, queue row 47. A fill measurement. No window return was computed.

## Result

- MEASURED: mark 1 is not met, so by the frozen rule the replay's 2 bps a side is not supported by the closing cross as measured. Marks 2 and 3 are met on the sessions where the cross was found. The miss is one of labels, not prices: see the section written after the run.
- Mark 1, cross print found: 124 of 260 sessions (47.7%), limit 95%: not met.
- Mark 2, mean signed cost per side: entry 0.000 bps, exit 0.000 bps, limit 1.0 bp each: met.
- Mark 3, 95th percentile of the absolute gap: 0.000 bps, limit 3 bps: met.
- The cross price equalled the SIP daily close on 124 of 124 found sessions. The Nasdaq official close print (condition M) was found on 122 and equalled the cross price on 122.
- Cross size: median 2,264,559 shares, 5th percentile 641,031, smallest 232,965.

## Signed cost by side

MEASURED. Basis points against the SIP daily close the replay used. Positive is a cost: a buy at the cross above the close, or a sell below it. Percentiles use linear interpolation.

| side | n | mean | median | p95 | min | max |
|---|---|---|---|---|---|---|
| entry | 63 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| exit | 61 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| pooled | 124 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

Absolute gap, all found sessions: n 124, mean 0.000, median 0.000, p95 0.000, max 0.000 bps.

## By year

MEASURED. Both sides together.

| year | sessions | found | mean signed | median signed | p95 absolute |
|---|---|---|---|---|---|
| 2016 | 24 | 0 | n/a | n/a | n/a |
| 2017 | 24 | 0 | n/a | n/a | n/a |
| 2018 | 24 | 0 | n/a | n/a | n/a |
| 2019 | 24 | 0 | n/a | n/a | n/a |
| 2020 | 24 | 0 | n/a | n/a | n/a |
| 2021 | 24 | 16 | 0.000 | 0.000 | 0.000 |
| 2022 | 24 | 23 | 0.000 | 0.000 | 0.000 |
| 2023 | 24 | 17 | 0.000 | 0.000 | 0.000 |
| 2024 | 24 | 24 | 0.000 | 0.000 | 0.000 |
| 2025 | 24 | 24 | 0.000 | 0.000 | 0.000 |
| 2026 | 20 | 20 | 0.000 | 0.000 | 0.000 |

## Early-close sessions

MEASURED. Scheduled close 1:00 pm New York.

| session | side | found | signed bps |
|---|---|---|---|
| 2016-11-25 | entry | no | n/a |
| 2019-11-29 | exit | no | n/a |
| 2022-11-25 | entry | yes | 0.000 |
| 2024-11-29 | exit | yes | 0.000 |
| 2025-11-28 | exit | yes | 0.000 |

## Sessions with no cross print found

MEASURED: 136 sessions, first 2016-01-26, last 2023-11-30. All are listed in the summary file. The by-year table above shows where they fall.

## Written after the run: the cross labelled Q or T

Not a mark and not part of the frozen result. Looking at the sessions with no Q cross print showed why: on all sessions before April 2021 and on some in 2021 to 2023, Alpaca's historical tape labels the Nasdaq closing cross as exchange T (NASDAQ Int), not Q (NASDAQ OMX). It is the same print, with conditions 6 and X, a very large size, at 4:00 pm. This view takes the largest condition-6 print on Q or T, with nothing else changed.

- Found: 258 of 260 sessions (99.2%).
- Mean signed cost: entry 0.018 bps, exit −0.007 bps. 95th percentile of the absolute gap: 0.000 bps.
- The cross price equalled the SIP daily close on 251 of 258 sessions. Largest single gap: 2.486 bps.
- Cross size: median 1,170,026 shares, 5th percentile 271,090, smallest 121,400.
- Not found: 2016-01-26 entry, 2016-01-29 exit. On those two sessions the only condition-6 prints are large ones on NYSE Arca (P), which suggests TLT was still listed there in January 2016. The date of the move is not checked here.

| side | n | mean | median | p95 | min | max |
|---|---|---|---|---|---|---|
| entry | 129 | 0.018 | 0.000 | 0.000 | 0.000 | 1.513 |
| exit | 129 | −0.007 | 0.000 | 0.000 | −2.486 | 2.444 |
| pooled | 258 | 0.006 | 0.000 | 0.000 | −2.486 | 2.444 |

Label of the cross print, by year:

| year and label | sessions |
|---|---|
| 2016 T | 22 |
| 2016 none | 2 |
| 2017 T | 24 |
| 2018 T | 24 |
| 2019 T | 24 |
| 2020 T | 24 |
| 2021 Q | 16 |
| 2021 T | 8 |
| 2022 Q | 23 |
| 2022 T | 1 |
| 2023 Q | 17 |
| 2023 T | 7 |
| 2024 Q | 24 |
| 2025 Q | 24 |
| 2026 Q | 20 |

## Method

- Sessions: the fourth-last and last session of each month January 2016 to October 2026 in `research_rig/calendar_25.json`, by the Replay 25 rule. 260 sessions. The replay's results file was not read.
- Trades: Alpaca historical trades, SIP feed, TLT, from −1 s to +300 s around the scheduled close (4:00 pm, or 1:00 pm on early closes).
- Cross print: the largest trade on exchange Q (Nasdaq) with condition 6 (Closing Prints). Official close: the first Q trade with condition M.
- Consolidated close: the SIP daily bar close in the Replay 25 input file, checked against its manifest.
- Trades and per-session prices stay off repo. This page and the summary carry aggregates only.

## Limits

- The cross price is what a market-on-close order receives. Commissions and the very small SEC and FINRA sell fees are not counted.
- An order large enough to move the auction would pay more. The cross size above is the guide to what it absorbs.
- This measures the replay's price, not its result. It does not change the Replay 25 verdict.
