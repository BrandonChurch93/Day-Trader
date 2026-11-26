<!-- Built from the pinned Plan 71 aggregates by research_rig/build_doc154_plan71_search.py. -->
# Plan 71 search: two new finalists, neither carried

MEASURED: The second grid used 112 rules, taking the sweep to 300. Two new rules qualified without taking 70-102's place. All three sweep finalist places were used. Both new rules fell short of the 33% carry line, so the vault stayed sealed and the search allowance is used up.

## What was searched

STATED: The second grid used the same 20-coin Binance global spot USDT proxy, January 2020 through December 2023, costs, adverse funding, matched baseline and cutoff as [Plan 70](152_plan_70_coin_sweep_search.md). It tested only the BTC overextension idea. The variants changed the size and length of the move, hold length, side, entry clock, BTC hedge or number of selected coins.

MEASURED: The input header reported 589,679 rows kept, 122 wrong-close rows left missing and 589,801 in-range rows. Only summaries are used here. No private ticket file or vault file is an input.

## Results by block

MEASURED: “Above zero” counts the plain net means for all rules, including thin ones. The t and median net columns use only eligible rules; “lost clearly” uses Doc 152's descriptive label, negative plain net and matched t at or below -2 on eligible rules.

| Block | Rules | Eligible | Above zero | Lost clearly | Median t | Best t | Median net bp |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Long, immediate, 2-hour hold | 34 | 20 | 34 | 0 | 1.97 | 3.59 | +39.5 |
| Long, immediate, other holds | 16 | 11 | 16 | 0 | 1.81 | 3.54 | +49.2 |
| Mirror short, immediate | 14 | 8 | 1 | 6 | -2.86 | -1.71 | -50.3 |
| Delayed by one hour | 16 | 8 | 3 | 5 | -2.26 | -1.28 | -35.9 |
| BTC hedge | 16 | 8 | 8 | 4 | -2.55 | 2.22 | -16.7 |
| Top two | 16 | 8 | 8 | 4 | -0.79 | 3.02 | -10.1 |

MEASURED: All 50 basic immediate longs had positive net means (median +71.1 bp). One hour later, 6 of 8 long rules were negative. Mirror shorts were negative in 34 of 38 rules including the three variant blocks. The hedged longs had 6 positive rules out of 8, with a median of +31.0 bp, or 44% of the basic immediate-long median. These are block comparisons, not matched pairs. A high t alone did not make a rule a finalist.

## Finalists and carry

### 71-035

STATED: Compare the last completed hourly close with the close 1 hour earlier. If BTC fell at least 0.015 in log terms, buy the non-BTC coin that fell strictly more than 2.0 times as much and has the largest excess drop. Break ties alphabetically; hold one position, unhedged, from that hourly open to the open one hour later. Skip tickets that span maintenance.

| Slice | Tickets | UTC dates | Plain net bp | Matched net bp | Matched t |
| --- | --- | --- | --- | --- | --- |
| Whole | 415 | 269 | +56.8 | +55.3 | 3.54 |
| 2020 through 2021 | 298 | 184 | +63.3 | +59.2 | 2.96 |
| 2022 through 2023 | 117 | 85 | +40.1 | +39.8 | 1.79 |

MEASURED: After dropping the best 1%, plain net was +34.5 bp a ticket. The simple annual result at 1x was +58.93%. 2 selected tickets did not resolve. Funding sensitivities were 0.25 bp per hour: +59.71%, 5 bp per hour: +54.78%; the spot-fee-only version was -69.39% simple a year.

MEASURED: 3,622 of 20,000 carry draws passed all vault marks at half the search mean (18.11%, seed 702035). Not carried.

### 71-013

STATED: Compare the last completed hourly close with the close 1 hour earlier. If BTC fell at least 0.015 in log terms, buy the non-BTC coin that fell strictly more than 2.0 times as much and has the largest excess drop. Break ties alphabetically; hold one position, unhedged, from that hourly open to the open 2 hours later. Skip tickets that span maintenance.

| Slice | Tickets | UTC dates | Plain net bp | Matched net bp | Matched t |
| --- | --- | --- | --- | --- | --- |
| Whole | 382 | 267 | +84.1 | +81.3 | 3.52 |
| 2020 through 2021 | 272 | 182 | +86.3 | +78.6 | 2.76 |
| 2022 through 2023 | 110 | 85 | +78.4 | +78.3 | 2.03 |

MEASURED: After dropping the best 1%, plain net was +60.5 bp a ticket. The simple annual result at 1x was +80.28%. 2 selected tickets did not resolve. Funding sensitivities were 0.25 bp per hour: +81.71%, 5 bp per hour: +72.64%; the spot-fee-only version was -36.97% simple a year.

MEASURED: 4,150 of 20,000 carry draws passed all vault marks at half the search mean (20.75%, seed 702013). Not carried.

## Limits and next steps

- **Repeated search:** The first grid had already selected this mechanism. These are the best of a 300-rule sweep on shared dates, not a second independent test.
- **Reachability:** The difference between the immediate and delayed entries raises a question about the first hourly print. [Doc 153](153_overextension_lead_outside_evidence.md) gives outside evidence and describes spread bounce, stale prints, outage artifacts and BTC beta. It does not prove which explains these results.
- **Venue and costs:** The roster uses hindsight and the prints are spot proxies, not measured US fills. Both finalists lose under the spot-fee-only comparison. True costs, funding and crash-hour depth are UNKNOWN.
- **Sealed vault:** No three-rule sweep finalist cleared carry. The existing ZEC gap in the vault is unchanged; no vault result exists.
- **Next:** Plan 72 is a separate fixed-rule check on Coinbase USD prints from 2017 through 2019, starting with a count and power gate. Its search-date repricing is shown as a diagnosis, not as an independent test.

STATED: The search summary and carry receipt hashes are `babd3544e7ae86bd13b9cbfeca7b4d3b72ee8b33fda4492c6ef6fab1a2dd5558` and `843d20afbe0b0d5822a6cb899bfdbd6714b96ac2832be5b02f4fd66391437930`. The builder opens only those aggregates and the two checked-in grids.
