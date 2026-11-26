# Measurement 121 result: what a small resting bid in a closed-end fund keeps

- Status: RECORD. Built by `research_rig/build_doc170_m121_result.py` from two aggregate files held outside the repo; no order row is in the repo.
- Plan, rule changes and the stop record of the first attempt: [doc 166](166_m121_cef_resting_bid.md). Ledger rows 223 (first attempt, stopped with nothing kept) and 224 (this run).
- This is a measurement of order handling on past quotes and trades. It is not a profit test and no order was sent anywhere.

## Short answer

- MEASURED: a pretend $500 buy order resting at the best bid for 30 minutes filled 7.56% of the time (227 of 3003 placed orders).
- MEASURED: on the fills that could be marked, the best bid five minutes after the fill was -26.6 bp from the fill price on average, median -22.0 bp (136 of 227 fills). 95% interval -30.3 to -23.0 bp by fund-day, -31.2 to -21.9 bp by calendar day. Both are wholly below zero.
- MEASURED: the order earned half the spread, +12.6 bp, and then the middle price moved against it by 23.5 bp within five minutes. Selling back at the bid would give up another 15.7 bp. The bid fills mostly when the price is about to fall.
- By the decision line fixed before the run: the coverage floors were not met and the interval is below zero, so no strategy test follows from this. The idea of earning the spread with a patient bid in these funds is closed.

## Counts

| Group | Scheduled | Could not be judged | No placement | Placed | Filled | Fill rate |
|---|---|---|---|---|---|---|
| Stock funds | 2,112 | 985 | 14 | 1,113 | 101 | 9.07% |
| Taxable bond funds | 1,848 | 874 | 17 | 957 | 70 | 7.31% |
| Muni funds | 2,112 | 1,169 | 10 | 933 | 56 | 6.00% |
| All | 6,072 | 3,028 | 41 | 3,003 | 227 | 7.56% |

- MEASURED: 264 more slots (24 fund-days, one fund) were left out before the run under Amendment 1.
- MEASURED: 3,028 of 6,072 slots could not be judged, 2,889 of them because the quote at the placement time was older than the plan allows. So only 50.1% of slots are known, against a floor of 90% in every group. These funds quote too seldom for the rule as written.
- MEASURED: 136 of 227 fills (59.9%) had a usable five-minute mark, against a floor of 90%. The floors on distinct funds, fund-days and dates were met (22 funds, 108 fund-days, 23 dates).
- The figures below are therefore from the half of the sample that could be judged. UNKNOWN: whether the other half would look the same.

## After a fill

| Mark | Fills marked | Mean, bid against fill price | Median |
|---|---|---|---|
| 60 seconds | 150 | -26.5 bp | -22.1 bp |
| 300 seconds (the main mark) | 136 | -26.6 bp | -22.0 bp |
| 900 seconds | 139 | -28.1 bp | -22.1 bp |
| Just before the close | 222 | -40.6 bp | -24.7 bp |

| Group | Fills marked at 300 s | Mean | 95% interval by fund-day |
|---|---|---|---|
| Stock funds | 65 | -25.8 bp | -31.4 to -20.0 bp |
| Taxable bond funds | 43 | -30.7 bp | -37.3 to -24.1 bp |
| Muni funds | 28 | -22.3 bp | -28.0 to -16.8 bp |
| All | 136 | -26.6 bp | -30.3 to -23.0 bp |

- MEASURED, description only: against the best ask at the moment the order was placed, a filled order paid 24.2 bp less (21.6 to 26.8). That saving is on the 7.6% that filled; the other 92.4% bought nothing.
- INFERENCE: five minutes after a fill the bid sits 26.6 bp under the fill price and the ask about two half-spreads above that bid, so a buyer who simply waited and took the ask would have paid about the same. The patient bid is not cheaper in a way we can use; it is roughly a wash, with a 92% chance of not buying at all.

## Check

- MEASURED: an independent auditor recomputed every count and mean from the kept order rows with its own program, without reading the runtime's report code or its summary. This builder refuses to write the page unless the counts match exactly and the means match to a hundredth of a basis point.
- MEASURED: the auditor's own 95% intervals for the main mark, from a different random stream, are -30.2 to -23.0 bp by fund-day and -31.1 to -21.8 bp by calendar day.

## Limits

- STATED by the runtime: Two dated filings do not establish daily listing or rule out a ticker changing and changing back, or a historical vendor-feed ticker collision with another issuer.
- One window of 24 sessions in September and October 2025, 23 funds drawn by a fixed hash from SEC filings. A fill is inferred from a later exchange trade at least one cent through the limit that covers the whole order; real queue position is not known, so the true fill rate could be lower or higher.
- Halt and pause data covered only part of each session. Gross figures: no commission, no regulatory fee.
- What it is good for: any later closed-end fund rule should assume it pays the spread to get in. A patient bid does not lower the cost.
