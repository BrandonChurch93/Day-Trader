# Replay 48 identity review

Ledger 200, queue 100. Opened 2026-11-26 (Mountain Time) by the lead agent. This is a review of a finished run, not a new trial. The locked Replay 48 result stays as it is.

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
