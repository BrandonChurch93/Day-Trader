# Replay 48 identity review

Ledger 200, queue 100. Opened and closed 2026-11-26 (Mountain Time) by the lead agent. **Outcome: the Replay 48 pass stands; the picks are unchanged.** This is a review of a finished run, not a new trial. The locked Replay 48 result stays as it is.

## Why

MEASURED. An identity sweep of the Replay 48 roster against SEC records, done without prices or results, found that the fund with CIK 0001232860 traded on the NYSE as MUI through 2024 but is listed in `roster.csv` under the symbol MUNUX for turns 2016 to 2024. A read-only audit of the run then found that MUNUX has no usable bars in those nine turns, so the fund was absent from the test.

MEASURED by the same audit. Nothing else was wrong on identity. The six funds merged away in January 2019 were ineligible before entry on missing sessions. The two merged away in January 2026 (NXC, NXN) were eligible, ranked 57 and 84 of 91, were not picked, and were priced at their last traded bar under the missing-exit cost. The twelve pre-entry delistings and ten IPO-year funds have no bars outside their own listing life and were ineligible. No fund lacking an exit bar was removed from the ranking.

## The question

Would MUI have been one of the five picks in any of turns 2016 to 2024?

## Steps, fixed before any MUI price is read

1. The custodian collects MUI raw and split-adjusted SIP daily bars for each turn's anchor-to-exit span, turns 2016 to 2024, with the Replay 48 collector settings, into a new directory outside the repo. The Replay 48 packet is not changed.
2. A checker applies the frozen Replay 48 eligibility and formation-ranking rules (`common_48.py`, unchanged) to MUI using only bars from the anchor through the formation session, and compares MUI's formation figure with the locked run's fifth-worst formation figure for that turn. Output per turn: eligible yes or no, and in the worst five yes or no. No bar after the entry session is read in this step and no return after entry is computed.
3. If MUI is outside the worst five in all nine turns, the picks, the nine marks and the pass are unchanged. The review closes with that statement and a note that the shown equal-weight roster line omitted one fund.
4. If MUI is inside the worst five in any turn, the pass is suspended. A corrected re-score is then run once, as Replay 48-R, with the same frozen scorer, marks and costs, a corrected pinned roster, and a new pinned packet that adds MUI bars, closing quotes, split evidence and January distributions. Both results are reported. Whatever Replay 48-R shows stands.

## Limits

The checker has seen the Replay 48 results. Step 2 is mechanical and uses pre-entry bars only. Third-party reuse of a roster symbol by an unrelated issuer was checked from bar start and end dates for the 22 flagged fund-turns, not from a vendor symbol history.

## Result

MEASURED, 2026-11-26. Step 1: 18 SIP requests, MUI raw and split-adjusted daily bars for turns 2016 to 2024, every session present with volume, raw equal to split-adjusted on every session. Files stay outside the repo; the pre-entry cut has SHA-256 `00773a005bb1c2f388cab3afb2e166d3d0ada06757d174f3042e9e17d0c857c3`.

MEASURED. Step 2: MUI was eligible in all nine turns and outside the worst five in all nine. The figure is the formation close divided by the anchor close; lower is worse. The fifth pick is the least-bad of the five funds the locked run held.

| Turn | MUI | Fifth pick | Fifth pick's figure | MUI's rank among eligible | In the worst five |
|---|---:|---|---:|---:|---|
| 2016 | 0.971831 | BNY | 0.893086 | 104 of 133 | No |
| 2017 | 1.001446 | PYN | 0.936613 | 47 of 138 | No |
| 2018 | 0.908567 | NMT | 0.823447 | 97 of 130 | No |
| 2019 | 1.109290 | MHF | 1.062323 | 42 of 124 | No |
| 2020 | 1.032123 | PCK | 0.891972 | 87 of 124 | No |
| 2021 | 1.032301 | NCA | 0.946479 | 55 of 100 | No |
| 2022 | 0.740668 | BFK | 0.654793 | 69 of 102 | No |
| 2023 | 1.024476 | PNF | 0.858708 | 86 of 104 | No |
| 2024 | 1.030534 | MQY | 0.932355 | 86 of 104 | No |

The table was produced by the checker from the pre-entry cut and the locked run's inputs. The lead agent recomputed MUI's figure and each held fund's figure for every turn with a separate script and got the same values; the rank column is the checker's.

Step 3 applies. All 50 picks, the portfolio and benchmark figures, the marks and the pass are unchanged. No bar after the entry session was read and no return after entry was computed, so no re-score was run and none is needed.

## What stays wrong on the page

- The shown-only equal-weight roster line in Replay 48 left out one eligible fund (MUI) in turns 2016 to 2024. It is not a mark.
- Replay 48 remains ten yearly turns, with the limits already written on its page.

## Lesson

A roster built from today's SEC ticker field carries today's symbol back in time. Rosters need a stable fund identifier with the symbol that was live in each year, and a check against filings for symbol changes, mergers and delistings inside each window. Plan 53 now does this.
