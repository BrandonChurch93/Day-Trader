# Plan 62: special-dividend ex-day replay, same-date vendor cash

Status FROZEN.

Queue 105, ledger 205. This succeeds [Plan 61](PREREG_61_special_dividend_ex_day.md), which was validated without computing a return, was not scored, and is closed to scoring permanently. All of its frozen terms apply except the narrow vendor gate change, the two added shown-only lines, and the new approval chain. In particular, Replay 60's aggregate results were already known.

## One changed gate

- MEASURED: Plan 61's no-return validation placed 230 of 443 docket events, under the frozen 250 mark. There were 88 more whose only failed judged gate was the absence of a residual exact-amount vendor cash match. This was measured from gate statuses, not returns.
- STATED: Before the price-blind class count, the lead fixed the exception now adopted. Preserve the original exact-match logic and admit an otherwise eligible missing-match event only if at least one supported USD vendor cash record for the resolved stock identity is on the verified docket ex-date, in the original padded window, and its amount is at least the docket special amount less USD 0.01. Call this Class A. Apply the threshold to individual records, not their sum. Keep the original removal of other verified cash actions for exact matching. Disagreement, ambiguity, and unusable mapping or coverage still refuse, as do all unchanged gates, including stock and IWM vendor basis. No Class B, C, D, E or F exception.
- MEASURED: The separately approved [count](COUNT_62.json) found A 86, B 2, C 0, D 0, E 0, F 0. After A, B is same-date cash below its threshold; C is no same-date cash but at least half the special within ten XNYS sessions on either side, in the original window; D is only farther in-window cash; E is no in-window supported USD vendor cash; F is no same-date cash and only sub-half amounts within ten sessions. The verified action packet records no structured distinction between a date stated by both hosts and a date derived from the record date for any of the 88. Expected placed pairs: 316 (230 plus 86), measured from these two no-return exercises, not a mark. The change came after both exercises and before any target return existed. The marks did not move.
- STATED: A Class A record can be within a cent below the special or at or above it, as a combined regular-plus-special record would be. If a record genuinely combines both and the verified packet lacks the regular part, the replay understates cash rather than overstating it. Same-date vendor cash does not prove composition or entitlement. A wrong docket date can still put the trade on an ordinary day and bias the mean upward when the special is credited. Credit only the verified docket special and other verified cash, never the vendor amount.

## Unchanged trade and marks

Use the same sealed docket, actual exchange ex-date, prior-session close entry and ex-date close exit for stock and IWM. Preserve the strict filing cutoff, five prior padding sessions, the USD 100,000 median raw dollar-volume floor, both frozen basis checks, independent USD 500 whole-share lots, idle cash, and independent per-side fees of the greater of 5 bp or USD 0.01 per share. Preserve the frozen split, cash and refusal rules. Printed closes are not realized auction fills. The broker cutoff, actual execution, point-in-time exchange-date evidence and individual tax treatment have the same limitations as in Plan 61.

| Mark | Required |
| --- | --- |
| Placed pairs | At least 250 |
| Money | Raw mean stock minus IWM return above zero |
| Evidence | Positive paired mean after symmetric clipping at plus and minus 600 bp, with ex-date clustered t at least 2 |
| Trim | Positive raw paired mean after removing the best 1%, rounding the drop count up |
| Year breadth | At least 7 ex-date years with a positive raw paired mean; an empty year is not positive |

All five marks are required. The variance, clustering and miss reading are unchanged. If the raw paired mean is positive and the winsorized t is at least 1 but below 2, report **not shown, not refuted**; only forward pretend-money logging may be considered. A t below 1 or nonpositive raw mean closes the row. Other misses are reported as not passing, with no automatic forward approval.

## Shown only, cannot count

- Keep the raw paired ex-date clustered t and stock and IWM means on matched pairs; the three yield bands; the USD 1 million liquidity subset; the 10 bp per-side whole-share and cost stress; the 24% verified-target-cash haircut; and the entry one session earlier, at the close of ex minus 2. All definitions and feasibility rules stay as frozen in Plan 61.
- Add count and raw paired mean for the placed exact vendor-match subset and the placed Class A subset. Neither line enters any mark. Validation reports total placed pairs and counts by the two subsets, with no means.

## Power and custody

STATED: The 316 expected pairs are three more than the 313 used in the full-pool 80% placement scenario in [POWER_61.json](POWER_61.json), less than a 1% sample-size change. This does not materially alter the prior power reading under the same noise and synthetic schedule assumptions; power for the actual retained schedule is UNKNOWN. The prior model's winsorized power at a true net 30 or 50 bp edge was 43.9% or 78.4% at the noise floor and 23.5% or 51.3% at central noise. Reuse the prior aggregate evidence only and do not rerun any placebo.

Adopt the frozen Plan 61 design and Plan 60 and Plan 43 sealed custody lineage. Rebuild native price and vendor evidence offline with unchanged pinned code. No new request or acquisition. Plan 62 does not open Plan 61's run folder or decisions file. The freeze pins source and the aggregate count and has no Plan 62 replay approvals. Use a clean exact checkout and an empty, owner-only 0700 /home/user/workspace/rig/data/replay_62. The lead alone adds ADOPTION_62.md, APPROVAL_62.md and GO_62.md in order, each as the sole addition in a separate one-parent commit. The three exact line formats are in the pinned scorer.

Validation prints the aggregate gate and placement counts and P62_VALIDATED, with no calculation of returns. The separate one-run GO binds the exact validation receipt and decisions, then writes a durable exclusive lock before computing any return. Neither validation nor this preregistration authorizes a scored run.
