# Plan 61: one-session special-dividend ex-day replay

Status DRAFT.

Queue 105, ledger 203, from [idea round 33, rank 2](../docs/127_idea_round_33.md). This is a new return window, not a revision of Replay 60. STATED: we know the paired and stock returns over the earlier announcement-clock hold in aggregate and know its shown-only yield groups. In [Replay 60](../docs/research/126_replay_60_special_dividends.md), the group whose ex-date fell inside the hold averaged +1.94% stock net over the full hold; the shown yield bands below 1%, from 1% to below 3%, and 3% or more averaged +3.56%, +2.59% and +0.86%, respectively. No one has computed a Plan 61 target ex-day return. The separately approved pre-freeze observations below are placebo dispersion only. No yield bucket may select events.

## Clock, universe and return

- Use only the Replay 60 docket and the exact sealed Plan 43 raw and adjusted bars, identity map, and independently verified actions that Replay 60 adopted. Reuse the same pinned Plan 60 vendor-action projection, native v2 index and rebuild adapter. No new issuer list, prices, vendor request, or network call.
- The target is the actual exchange ex-date on which the stock trades without the cash, not the record or payment date. For very large specials this can be the deferred ex-date after the payment date, as covered by [FINRA Rule 11140](https://www.finra.org/rules-guidance/rulebooks/finra-rules/11140). With unchanged identity mapping, cross-check exact cash amount and ex-date against the verified filing-action target. Remove at most one exact same-date, same-amount vendor record for each other verified cash action; require one remaining equal-amount vendor cash record within the original padded window and exact agreement on date. Refuse a missing, ambiguous or disagreeing match, or unusable vendor mapping, on the event only and show all counts. Use the verified action for credited cash, not the vendor amount as a replacement. Do not infer the clock from the dividend size, payment or record dates, settlement rules, or a price move.
- Buy the stock at the regular close immediately before the verified ex-date and sell at the regular ex-date close. Use the same clocks for IWM, the small-cap benchmark. Both closes must fall inside the original sealed window, and stock and IWM need present positive-volume raw bars on both dates. The filing must be accepted strictly before the official entry close, including an early close. All five frozen padding sessions must finish strictly before entry. No later substitute fill. The vendor and filing action packets do not independently prove when an exchange posted or changed the verified ex-date. UNKNOWN: an orderable point-in-time ex-date archive is unavailable here, and a filing accepted shortly before close may miss the broker's market-on-close deadline.
- Reuse the five frozen stock padding sessions and USD 100,000 median of raw close times raw volume from Plan 60, inclusive. Require positive volume on all five. Reuse the exact Plan 60 per-event stock and IWM vendor-basis checks over the full original padded window, with one common positive tail multiplier for both adjusted views, the same half-cent-plus-slack tolerance and no refit or imputation. This is a retrospective data check, not an entry signal. Do not apply the Plan 60 announcement-hold entry or delayed-exit rules. No event-level refusal cap.
- Allocate USD 500 independently to each leg and buy the largest whole-share lot affordable after entry cost. Leave unused cash idle. Charge the greater of 5 bp of trade value or USD 0.01 per share per side, separately on stock and IWM. Use verified splits and cash actions whose ex-date falls strictly after entry through exit, including cash for the target on the ex-date, even if paid on a different date. Refuse stock or IWM lots that become fractional; do not model cash in lieu. This is a retrospective omission and may remove an action unknown at entry. Report net P&L divided by USD 500 on each leg; the paired difference subtracts the IWM return on the same clock. That removes the matched benchmark return by construction, not all market risk, and is not a modeled short with financing or borrowing.
- STATED: the replay uses printed closes. A live version would use market-on-close orders; closing-auction fill size, actual execution price and order acceptance at USD 500 are UNKNOWN. No realized spread claim is made. The judged line is before tax. In a taxable U.S. account, a one-day hold fails the qualified-dividend holding period, so a taxable cash dividend is ordinary income; issuer-classified return of capital can differ ([IRS Publication 550](https://www.irs.gov/publications/p550)). The 24% line is only a scenario on the target cash credit, not an individualized tax calculation.

## Five frozen marks, all required

| Mark | Bar |
| --- | --- |
| Placed pairs | At least 250 |
| Money | Raw mean stock minus IWM return above zero |
| Evidence | Clip each paired difference symmetrically at plus and minus 600 bp before computing its mean and ex-date clustered t. Require positive clipped mean and t at least 2. The cap is fixed and is not refit. |
| Trim | Raw mean above zero after dropping the best 1% of the raw paired differences, rounding the drop count up |
| Year breadth | At least 7 ex-date years with a positive raw paired mean; an empty year is not positive |

The event is the unit of return. The cluster is the exchange ex-date, not the filing date or entry month. For raw and clipped series, the finite-group variance is G/(G−1) times the sum of squared cluster sums of de-meaned returns divided by N squared. An undefined t does not meet the evidence mark. Clipping changes neither the raw money, trim and year marks nor the cost or target selection.

STATED pre-return reading: A pass is evidence, not proof of future performance. A miss is weak evidence against the rule because this test would miss a true 30 bp edge more often than not. If the raw paired mean is positive and the winsorized t is at least 1 but below 2, write **not shown, not refuted**; only a forward pretend-money log may be considered. If the winsorized t is below 1 or the raw mean is at or below zero, close the row. For any other miss, including an undefined t or a t of at least 2 with another mark unmet, report that it did not pass with no automatic forward approval.

## Shown only, cannot count

Use the same judged events unless the comparison itself requires a feasible alternative lot or earlier clock. Show observation counts and means, including zero or unavailable counts. These comparisons cannot meet any of the five marks.

- Plain ex-date-clustered t of the raw paired series, and the one-session stock-only mean on the matched sample.
- Three yield buckets using the earlier Plan 60 breaks: below 1%, 1% to below 3%, at least 3%. Divide the declared cash by the stock entry close. No bucket is a selection gate.
- The subset at or above USD 1 million median dollar volume on the same five padding sessions. This was dropped as a judged universe before any target return.
- A new whole-share calculation at 10 bp per side, with the same cent floor. A missing or fractional stress lot omits only this line.
- Reduce the target stock cash dividend by 24%, holding prices, lots, other verified cash actions and the IWM return fixed. Do not model other taxes or capital-loss offsets.
- Enter a session earlier, at the close of ex minus 2, and keep the ex-date close exit for both legs. Require that earlier close inside the window, the filing and completed padding strictly before it, positive-volume bars and affordable integral lots. Apply verified actions over that actual hold. If it is infeasible, omit only this line.

## Pre-freeze measurements and power

MEASURED price-blind count: 391 possible events across 345 distinct ex-date clusters out of 443 docket filings. Before using any close values, the counter found 17 clocks outside the sealed window, one filing not public strictly before the entry close, one missing verified cash ex-date, one known noncash exclusion, one clock on the last padding close, 27 stock padding volume failures and four stock clock volume failures. No remaining candidate missed IWM clock volume. This is an upper bound before dollar volume, vendor ex-date agreement and basis, affordability or fractional shares. It is not a measured placement rate.

MEASURED pre-freeze placebo dispersion, after auditor source review and separate lead authorization. For each possible event, take at most the three nearest adjacent regular-session stock-minus-IWM raw close-to-close percent changes whose latest endpoint is at least three sessions before entry, both endpoints inside the sealed window and positive-volume for both legs. Put splits and verified cash on the correct basis; do not model whole shares or costs here. Decode neither target entry nor ex-date closes for that event. The second mode also reads only the required five earlier raw stock closes and volume for the USD 1 million screen. Print only the approved aggregate dispersion fields and counts, not any mean, median, sign or individual observation.

| Screen | Candidates | Events contributing | Observations | Sample SD, bp | Scaled MAD, bp | Between-ex-date share of total sum of squares |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full price-blind candidate pool | 391 | 391 | 1172 | 476.89 | 193.67 | 29.63% |
| USD 1 million subset | 259 | 259 | 777 | 526.94 | 174.93 | 28.71% |

The raw sample SD is the floor for synthetic ex-day noise. The central case is 1.5 times that floor; 2 times is shown for stress. The bell-shaped fit was superseded before any ex-day return. The adopted power model is a centered two-normal mixture with a 95% calm and 5% broad regime, drawn once per ex-date. Fit marginal SD and scaled MAD; fit the expected descriptive between-date sum-of-squares fraction, allowing for the finite number of observations per date. The fraction is not the intracluster correlation. The fitted calm/broad standard deviations are 183.46/1977.13 bp for the full pool and 165.50/2243.42 bp for the liquidity subset; fitted date correlations are +0.0036 and −0.0254. The subset supplied counts, not dates, so its synthetic schedules are uniform subsets of the full aggregated year/date cluster shape. Each scenario uses 6000 trials and independently assumed 80% or 70% placement, not measured fills. Edges are already net. Model shares are not guarantees.

The cells are all-five pass percentages, plain version then winsorized version. Both versions use the same raw money, trim, count and year marks. Only the latter is judged.

| Candidate pool | Placement | Noise scale | 0 bp | 15 bp | 30 bp | 50 bp |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full | 80% | 1.0 (476.89 bp) | 1.73 / 1.58 | 8.32 / 14.73 | 21.27 / 43.92 | 47.55 / 78.43 |
| Full | 80% | 1.5 (715.34 bp) | 1.73 / 1.37 | 4.92 / 7.48 | 11.72 / 23.48 | 25.00 / 51.32 |
| Full | 80% | 2.0 (953.78 bp) | 1.73 / 1.27 | 3.70 / 5.12 | 8.32 / 13.93 | 16.08 / 33.38 |
| Full | 70% | 1.0 (476.89 bp) | 1.90 / 1.92 | 7.18 / 14.17 | 19.28 / 43.82 | 43.85 / 78.27 |
| Full | 70% | 1.5 (715.34 bp) | 1.90 / 1.78 | 4.85 / 8.32 | 10.43 / 22.65 | 23.00 / 52.10 |
| Full | 70% | 2.0 (953.78 bp) | 1.90 / 1.67 | 3.77 / 5.63 | 7.18 / 14.25 | 15.07 / 33.20 |
| USD 1 million | 80% and 70% | 1.0 (526.94 bp) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| USD 1 million | 80% and 70% | 1.5 (790.41 bp) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| USD 1 million | 80% and 70% | 2.0 (1053.89 bp) | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |

STATED decision by the lead, before a target return: keep the full Plan 60 liquidity universe and use the winsorized evidence mark. The USD 1 million subset's scaled MAD was smaller, but standard deviation was higher and no placement trial reached 250 from 259 candidates. At 80% placement, the chosen version has 43.9% and 78.4% power at 30 and 50 bp at the floor, and 23.5% and 51.3% at central noise. The [idea note](../docs/127_idea_round_33.md) reports about 56 bp gross in the published unpredicted-dividend study, or about 46 bp after an illustrative 10 bp round trip; the actual cent floor can bind and neither that edge nor those fills are established for this docket. The lead's rough power estimate at that illustrative edge is 47% to 75% from central to floor noise, not a separately simulated grid point. The largest simulated zero-edge pass share across all cases is 1.92%, below the 10% ceiling. The lead is choosing to run despite falling below the usual 50% power at 30 bp because the replay requires no new data, no vendor call or acquisition cost, and a false pass was uncommon in these simulated null worlds.

Pre-freeze code SHA-256:

- Count and shared price-blind selector, backed by [COUNT_61.json](COUNT_61.json): `1256c78d2086a9e962506dd18ffcf8814c137bcb10a80b8059e93351fdd46c8f`.
- Full-only placebo version used for [PLACEBO_61.json](PLACEBO_61.json): `d4434814d8d955ef790e71de46babe6eacc09f3a35e68a0b022796efb0a891af`.
- Same placebo method with the reviewed extra subset flag, used for [PLACEBO_LIQUID_61.json](PLACEBO_LIQUID_61.json): `bbfc99af13f2a58a3b973d0036ee3d01a3a38744a81e8e0195e46932b101d80e`.
- Power simulation backing [POWER_61.json](POWER_61.json): `fa8e49559b5018bd9b7d49e99247f14f75ef72336521ffa545d4b4792ae34092`.

## Custody and one-run protocol

Retain the Plan 60 exact approval at `8babbf959c0133549c8961733941ebab35875872`, which supplies the vendor projection and native index hashes and the adopted Plan 43 lineage. Rebuild the native bars and vendor projection from pinned native companions, verify the original identity and independently verified action packets, and verify the vendor endpoint, coverage, alias flags and exact page-token chain. Global checks protect file provenance, byte integrity, schema binding and approvals. Ordinary event failure, incomplete coverage flags, bad event bars, missing lots, action disagreements and vendor-basis failures are per event, never whole-run market-data coverage gates. Missing or malformed evidence of sealed packet integrity is not a market-data refusal and stops safely.

The future freeze pins all sources and both measurements, changes only status and pins, and contains no approval file. Separate lead-only, single-parent sole-file additions follow the clean freeze, in order. Each approval is one ASCII line with a final LF:

- `research_rig/ADOPTION_61.md`: `Approved by the lead: plan 61 ledger 203, adopt Plan 60 validation commit <Plan 60 validation commit>, Plan 60 validation approval SHA-256 <historical approval file hash>, freeze commit <freeze>, freeze SHA-256 <manifest hash>, no price acquisition.`
- `research_rig/APPROVAL_61.md`: `Approved by the lead: plan 61 ledger 203, validation only, adoption commit <adoption>, adoption approval SHA-256 <adoption file hash>.`
- `research_rig/GO_61.md`: `Approved by the lead: plan 61 ledger 203, one scored run, validation approval commit <validation>, validation receipt SHA-256 <receipt hash>.`

From the exact clean checkout, the lead creates an empty private `rig/data/replay_61/` run directory with owner-only mode 0700. A missing run directory reports `P61_RUN_FOLDER_MISSING` with this remedy. Validation command: `python3 -I -B research_rig/score_61.py --validate-inputs --approval-commit <validation>`. It checks all evaluable gates across the docket in one pass, prints only status counts and `P61_VALIDATED`; overlapping failures are counted and non-evaluable gates labeled. It does not compute a return, and any detailed decisions and validation receipt remain in the owner-only run directory. Scoring command, only with separate GO: `python3 -I -B research_rig/score_61.py --go --approval-commit <go>`. It reproduces the gate record, checks the approved receipt and frozen lineage, writes an exclusive durable lock before the calculation, then writes one private result. No replay of the scoring command is authorized.
