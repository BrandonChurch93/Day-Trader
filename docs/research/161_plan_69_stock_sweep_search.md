<!-- Built by research_rig/build_doc161_plan69_search.py from the pinned aggregate files only. -->
# Plan 69 search: no stock or fund rule made the cut

MEASURED: None of the 188 scored rules met the search marks on US stocks and exchange-traded funds, 2016-01-04 to 2021-12-31. The highest t of any rule was 2.35 (S11-04, 26 trades, too few to count) against a bar of 3.5. Among the 53 rules with enough trades the highest t was 1.25. There is no finalist, so the vault (2022-01-03 to 2026-10-30) stays sealed and Plan 69 is closed (ledger 217, queue 111).

## What was searched

STATED: 189 rules written before any price was read, in 11 families, each family tied to a published reason why a price might move at a set time of day. 188 are long-only and scored; one short rule is shown only. The list was 33 large stocks from a 2014 fund filing and 77 funds from dated exchange and issuer lists (13 broad stock funds, 26 sector funds, 14 bond funds, 10 leveraged long funds, 14 inverse funds), none chosen for being liquid or alive today. Trades are five-minute prints with $500 of settled cash, one position, one entry a day, whole shares, the measured half-spreads of doc 136 on each side, and no reuse of unsettled cash.

STATED: To count, a rule needed at least 200 trades on 100 days with 40 days in each half. To clear, it also needed positive net in both halves, a day-clustered t of 3.5 against the same instrument held over the same clock on all days, t of 1.5 in each half, positive net without its best 1% of trades, and 12% simple net a year on $500.

MEASURED, input check before any return (freeze `2a5e955`): 14,445,884 five-minute bars in the archive, 11,499,703 in regular hours, 1,511 sessions, 108 of 110 listed instruments with bars, 159,406 instrument-days, 39 splits on file. 1 instrument-day was left out whole for an unexplained price jump (AMGN 2016-10-25), under the ruling made before any return was computed. No trade was dropped because of it (0 dropped).

## Result by family

MEASURED: t here is on net return minus the same-clock baseline, grouped by entry day. "Best t" is over every rule in the family that produced one, including rules too thin to count.

| Family | Idea | Rules | Enough trades, missed | Too thin | Not scorable | Best t | Trades in that rule |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | leveraged funds, late-day move carries on | 16 | 13 | 1 | 2 | 1.25 | 206 |
| S2 | rebound overnight after forced late selling | 18 | 0 | 0 | 17 | 0.46 | 58 |
| S3 | fade a late push into the close | 16 | 0 | 16 | 0 | 0.45 | 69 |
| S4 | fade the opening gap | 16 | 1 | 11 | 4 | 0.15 | 7 |
| S5 | fund and index gap closes by the close | 15 | 11 | 4 | 0 | -0.90 | 249 |
| S6 | dealer hedging before the close | 18 | 3 | 13 | 2 | 0.70 | 18 |
| S7 | buy late selling, hold overnight | 16 | 2 | 10 | 4 | 1.14 | 24 |
| S8 | same half-hour repeats on later days | 20 | 12 | 4 | 4 | -0.22 | 92 |
| S9 | pressure to cut risk before the close | 15 | 11 | 4 | 0 | 0.07 | 380 |
| S10 | Friday to Monday reversal | 15 | 0 | 10 | 5 | 0.51 | 149 |
| S11 | rebound after sharp selling on heavy volume | 24 | 0 | 22 | 2 | 2.35 | 26 |

MEASURED: status of all 189 rules: too few trades or days 95, enough trades, missed the marks 53, not scorable: an exit had no print 40, short side, shown only 1.

## Ten highest t values

MEASURED: before the trade-count floor or any other mark. A high t on few trades is not a pass. Net is mean basis points a trade after costs; the last column is simple net a year on $500 with idle days at zero.

| Rule | Idea | Trades | Status | t | Net bp | First half bp | Second half bp | Net a year |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S11-04 | rebound after sharp selling on heavy volume | 26 | too few trades or days | 2.35 | +67.6 | +46.8 | +78.5 | +2.67% |
| S11-22 | rebound after sharp selling on heavy volume | 46 | too few trades or days | 2.06 | +36.8 | +28.4 | +43.8 | +2.54% |
| S1-14 | leveraged funds, late-day move carries on | 206 | enough trades, missed the marks | 1.25 | +10.4 | +14.5 | +7.8 | +3.49% |
| S11-08 | rebound after sharp selling on heavy volume | 51 | too few trades or days | 1.21 | +6.5 | -6.0 | +14.6 | +0.51% |
| S11-09 | rebound after sharp selling on heavy volume | 36 | too few trades or days | 1.19 | +9.3 | -5.1 | +15.6 | +0.47% |
| S11-23 | rebound after sharp selling on heavy volume | 38 | not scorable: an exit had no print | 1.16 | +20.1 | +7.5 | +67.6 | +1.11% |
| S7-04 | buy late selling, hold overnight | 24 | too few trades or days | 1.14 | +128.0 | -76.8 | +274.3 | +4.03% |
| S1-13 | leveraged funds, late-day move carries on | 254 | enough trades, missed the marks | 0.84 | +6.1 | +8.1 | +4.8 | +2.48% |
| S11-10 | rebound after sharp selling on heavy volume | 5 | too few trades or days | 0.80 | +36.0 | -16.5 | +114.9 | +0.27% |
| S6-09 | dealer hedging before the close | 18 | too few trades or days | 0.70 | +21.5 | +70.6 | -39.9 | +0.59% |

## What it says

- MEASURED: 55 of 188 scored rules had a positive net mean; of the 53 with enough trades, 11 did and 18 lost clearly (negative net and t at or below -2).
- MEASURED: 2 rules had t of 2 or more, both with fewer than 200 trades. None reached 3.
- MEASURED: the best simple net a year on $500 among rules with enough trades was +4.83% (S9-09); over every scored rule it was +4.83% (S9-09, 380 trades, t 0.07, so no better than holding the same fund over the same clock on any day). The mark was 12%.
- MEASURED: 40 rules were not scorable because at least one entered trade had no print at its exit clock; the plan does not let a taken trade be erased. On their priced trades the highest t was 1.16 (S11-23), so none of them was near the bar either.
- MEASURED: 312 chosen entries across all rules had no print at the entry clock and were not replaced.

## Limits

- STATED: 95 of 188 rules were too thin. On about 100 names and one entry a day, most of these triggers fire too rarely in six years to be judged at this bar. That is a limit of the grid, not evidence the ideas are false.
- STATED: the 16:00 and 09:30 prices are five-minute bar prints, not auction fills. Dividends are not credited. Costs are the measured half-spreads of doc 136, with the cautious bucket for unmeasured names; fees, impact and fill quality beyond that are UNKNOWN.
- STATED: the real-run numbers were not recomputed by a second program. The script found a planted rule on made-up data and stayed clean on 100 of 100 made-up worlds in audit; with no finalist to carry, no recompute was ordered.
- UNKNOWN: anything about 2022 onward. No vault price was read by this plan.

STATED: The search output and the input-check output are held off the repository under `/home/user/workspace/rig/data` with SHA-256 `b7a035f9ffcc5c3f0f2d1bd92c8264d8f15bc1ccfffc2f75bfe48b67990cdb61` and `ad25bc12d20eea7208fa2b44e9f29406975d8998769608bde79ae1975ee62c09`. The builder reads only those two files, the checked-in grid and the shared settings. See the [plan](../../research_rig/PREREG_69_stock_sweep.md) and the [sweep design](../150_discovery_sweep_design.md).
