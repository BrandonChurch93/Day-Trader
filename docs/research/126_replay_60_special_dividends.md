# Replay 60. Special-dividend declarations

MEASURED. Did not pass, **6 of 7 frozen marks** in the single scored run at 2026-11-26 09:59:20 UTC. Missed Paired IWM. The average stock return was +1.96% net and the paired lead over IWM was +0.96%, but its clustered t was 1.23.

## The rule

STATED from the [frozen plan](../../research_rig/PREREG_60_special_dividends.md). Require positive stock volume on every one of the 5 frozen padding sessions and at least $100,000 in median daily dollar volume over those sessions. Buy whole shares on $500 at the session +2 open and plan to sell at the session +20 close. If the planned exit bar is absent or has no volume, use the first positive-volume open in the next 5 sessions. No usable entry means no fill; gaps inside a hold are carried. IWM uses the same actual clocks. Charge the larger of 5 bp of trade value or $0.01 per share per side. Use independently verified actions for cash and share changes.

## Frozen marks

MEASURED. All 7 marks were required. The t statistics group observations by entry month.

| Mark | Frozen bar | Measured | Verdict |
| --- | --- | --- | --- |
| Placed pairs | At least 300 pairs | 339 | met |
| Net mean | Stock mean above zero | +1.96% | met |
| Stock clustered t | Positive stock mean and t at least 2 | 2.38 | met |
| Without best events | Mean above zero after dropping the best 1%, rounded up | +1.01%; removed 4 | met |
| Positive years | At least 7 positive acceptance years | 9 of 11 | met |
| Recent mean | Mean above zero from 2020 onward | +1.87% | met |
| Paired IWM | Positive stock minus IWM mean and clustered t at least 2 | +0.96%; t 1.23 | not met |

## Judged block

MEASURED. A placed pair uses the same stock and IWM clocks, each on its own starting allocation. The IWM mean below is the stock mean less the saved mean of the paired differences. Stock minus IWM is a difference in percentage points.

| Line | Pairs | Mean net | Clustered t | Entry months |
| --- | --- | --- | --- | --- |
| Stock | 339 | +1.96% | 2.38 | 108 |
| Matched IWM | 339 | +1.00% | not stored | 108 |
| Stock minus IWM | 339 | +0.96% | 1.23 | 108 |

## By acceptance year

MEASURED. Stock means use only judged pairs. The result does not store annual IWM or paired means.

| Year | Filing events | Judged pairs | Stock mean net | Missing padding | Low volume | Vendor basis refusals | Fractional lot refusals | Stock capital misses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2016 | 46 | 36 | +4.40% | 4 | 5 | 1 | 0 | 0 |
| 2017 | 43 | 31 | +2.58% | 4 | 5 | 3 | 0 | 0 |
| 2018 | 40 | 27 | -0.68% | 5 | 6 | 2 | 0 | 0 |
| 2019 | 37 | 27 | +1.35% | 4 | 5 | 0 | 0 | 1 |
| 2020 | 48 | 38 | +6.14% | 4 | 2 | 4 | 0 | 0 |
| 2021 | 67 | 55 | +0.79% | 1 | 6 | 3 | 0 | 2 |
| 2022 | 56 | 41 | +0.14% | 5 | 3 | 4 | 0 | 2 |
| 2023 | 30 | 24 | +2.63% | 1 | 3 | 0 | 0 | 2 |
| 2024 | 32 | 26 | +1.91% | 0 | 3 | 1 | 0 | 2 |
| 2025 | 31 | 24 | -0.14% | 0 | 4 | 3 | 0 | 0 |
| 2026 | 13 | 10 | +1.63% | 0 | 0 | 3 | 0 | 0 |

## Decisions and refusal reasons

MEASURED. The 443 filing events each have one terminal decision. There were 0 delayed exits and 3 unavailable sessions carried inside holds. The counts below do not replace any mark.

| Decision | Events |
| --- | --- |
| Placed stock and matched IWM pair | 339 |
| Frozen noncash exclusion | 1 |
| Outside universe: missing or zero-volume padding session | 28 |
| Outside universe: low median dollar volume | 42 |
| Unfilled stock entry: missing or zero-volume bar | 0 |
| Refused: no permitted exit | 0 |
| Refused: stock or IWM vendor basis | 24 |
| Refused: judged lot would become fractional | 0 |
| Unfilled stock entry: whole share not affordable | 9 |
| Unfilled IWM control: matched clock unavailable | 0 |
| Unfilled IWM control: whole share not affordable | 0 |

MEASURED. Vendor diagnostic tags below count stock or IWM legs across the docket, not distinct refused events. There were 24 terminal event refusals for this reason. A leg can carry a tag on an event already excluded for another reason.

| Vendor basis diagnostic | Stock or IWM legs |
| --- | --- |
| Vendor mapping or coverage incomplete | 11 |
| Unsupported vendor action | 3 |
| Vendor action date not a regular session | 0 |
| Adjusted bars did not match the reconstructed basis | 11 |
| Unsupported same-session actions | 0 |
| Cash action lacked a usable reference close | 7 |
| Too few usable raw and adjusted pairs | 0 |

## Shown only

MEASURED, shown only. None of these figures can count toward a mark. The inclusion checks add otherwise feasible vendor-basis refusals as a sensitivity; they do not establish those raw bars are correct.

| Line | Observations | Mean net |
| --- | --- | --- |
| Session +1 entry | 339 | +2.37% |
| Higher friction (10 bp per side, same cent floor) | 339 | +1.89% |
| Stock minus SPY | 281 | +1.06% |
| Stock mean on deployed cash | 339 | +2.05% |
| Declared ex-date inside actual hold | 306 | +1.94% |
| Declared ex-date outside hold or canceled | 33 | +2.10% |
| First-time declaration: yes | 1 | +6.70% |
| First-time declaration: no | 22 | -0.34% |
| First-time declaration: unknown | 316 | +2.10% |
| Declared yield below 1% | 75 | +3.56% |
| Declared yield at least 1% and below 3% | 98 | +2.59% |
| Declared yield at least 3% | 166 | +0.86% |
| Stock including otherwise feasible vendor-basis refusals | 362 | +2.00% |
| Stock minus IWM including otherwise feasible vendor-basis refusals | 362 | +1.00% |

MEASURED, shown only. There were 2 SPY basis failures, of which 0 alone removed a feasible SPY comparison. There were 120 vendor-only and 227 verified-list-only in-window action instances across event legs. Of 1071 legs with a post-window price action, 0 had a known action product within the fitted interval. UNKNOWN. Absolute tail scale: not established.

| Shown arm | Fractional-lot flags |
| --- | --- |
| Session +1 entry | 0 |
| Higher friction | 0 |
| Paired SPY | 0 |
| Settled sleeves | 0 |

## Settled sleeves on starting cash

MEASURED, shown only. Starting with $500 in 5 settled $100 sleeves, the replay placed 244 orders and made +$422.82 total net, or +84.56% of starting cash. This is a full-period result before taxes, not an annual return and not a mark.

| Sleeve skip | Events |
| --- | --- |
| Whole share not affordable or cash unsettled | 56 |
| Issuer already open or reserved | 0 |
| No free sleeve | 48 |

## Gaps and disclosures

- STATED in the frozen plan. Replay 43 stopped 3 times during validation, without ever computing a return. The lead and auditor knew the earlier refusal counts. This replay carried forward the docket, not an earlier return.
- MEASURED. 24 events were refused because stock or IWM vendor bases did not reproduce or were not established. The judged result does not establish an effect for them.
- STATED. A split can be announced after entry. The fractional-lot refusal therefore depends on hindsight, not on the entry screen. It excluded 0 judged events.
- MEASURED from saved stderr. The first validation stopped with `P60_REFUSED` (exit 2). STATED by the lead. The private run directory did not exist; after it was created empty with private permissions, validation printed `P60_VALIDATED`. No return was computed by validation.
- STATED from the freeze test record. The direct frozen-head suite passed 16 of 17 tests. The draft-rejection fixture copied the frozen status from the checkout. The same test passed with the parent's draft text supplied only to its temporary fixture; the freeze was not changed.
- UNKNOWN. The replay does not establish future fills, future returns, or an effect on the filings that did not place.

## Independent recompute

STATED by /root/decision_autopsy_analyst. Independent recompute: AGREE. The helper did not read the scorer.

- Compared fields: 30; differences: 0.
- Taken as given: Nothing in the final comparison. The 24 vendor-basis refusals were taken as given for a first pass only and then re-derived.
- Rederived: Noncash skip, day 0, session windows, pre-entry liquidity universe, entry, exit, whole-share lot, costs, verified cash and splits for all 443 events; Vendor basis gate on all 442 x 3 legs from the plan text; Placed pairs, net mean, clustered t, paired mean and t against IWM, trimmed mean, recent mean, all 11 acceptance-year means and all seven marks.
- Own numbers were written to disk before the result file was opened.
- Per-event decisions matched on all 443 events and effective exits on all 339 placed pairs.
- On a first reading of the plan text the vendor basis gate differed on 7 stock legs, all in events already outside the universe, so no judged effect. They matched once a zero-volume reference bar before a cash ex-date was treated as absent, which the plan says of zero-volume bars elsewhere.
- Ambiguities in the plan text that did not change any result: one shared or one per-view tail multiplier, the tie order of the trim, and the unnamed calendar file.
- Not recomputed, no mark uses them: the settled sleeves and the shown-only arms.

## Run record

MEASURED. The saved result records a scored run on queue 99 and ledger 199. The saved validation totals exactly match the scored result's decision totals. This report does not rerun validation or scoring.

- Freeze commit `8f4aa8992a6548cbdf1067cffd3d7e0027ccd579`
- Freeze manifest SHA-256 `79e0782afbb8a54eee53495ee4674b12db8a10d75c5fea77d7a5333422a3cd94`
- Adoption commit `9b31c965cc42f44c7e4593284f3a31f5628a7559`
- Validation approval `8babbf959c0133549c8961733941ebab35875872`
- Scoring approval `9089f46c6983d9b3793666983a41dda0635173b4`
- Saved result SHA-256 `c28680d0b3515b8bd0b3827048b3ad10ae28db4c2cae6262411e53500121e3d1`
- Saved validation output SHA-256 `40fc7e591f7eff9b8131112ccc11f534d19d8dc6ac82c9eb342448c041033a0c`
