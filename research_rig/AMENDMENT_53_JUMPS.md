# Plan 53 raw-close jumps and historical identity amendment

Status FROZEN.

This is the frozen replacement for Plan 53, not an approval to validate or score. The reviewed draft `5fe158e322772926a658ced877ee6b44ebc2a8fe` is a direct child of the prior cash amendment freeze `06b7bba1c979ed1a4a443711e9f397bd4667dfa8`. STATED: Validation stopped at an unexplained close change before any lock or scored result. The author did not open the packet. This amendment does not change the cash rules, ranking rule, calendars, costs, yardsticks, seven marks, or shared Replay 48 engine.

## Rule

- Keep `replay_48_plan.split_check_ratio` unchanged. For every Plan 53 roster fund and PCEF, use the same check on consecutive usable raw closes from anchor through judged exit, inclusive. Skip missing and zero-volume bars when identifying the next usable close. A pair only flags if the factor is outside the inclusive reciprocal-to-factor range and the later date is not a recorded split day. Run the existing bar, quote, split evidence and raw-versus-adjusted split controls as before.
- Recompute every flag. Require exactly one clearance for each exact roster pair keyed by turn, ticker, earlier date and later date. Multiple pairs in the same fund-turn require separate rows. Refuse an unknown class, a missing clearance, or any stale or extra clearance. Reject duplicate or unsorted keys and invalid evidence references or hashes. PCEF has no clearance route: refuse on a PCEF flag or a PCEF clearance row.
- `GENUINE_MOVE`: keep the raw bars unchanged and apply ordinary eligibility. The evidence must confirm the historical security and both closes, document a corroborating series or independent tape evidence and the corporate-action review, and support that this is a genuine move, not a split, tape error or identity break. Do not add or rescale a close by hand.
- `IDENTITY_BREAK`: use only when the historical security mismatch cannot be repaired with an identity-continuous series. Document the effective break on the later close date. If it is on or before entry, exclude the exact fund-turn from ranking and the eligible roster yardstick, as with a pre-entry split. Preserve its slot in the frozen roster and do not exclude it from other turns. Count that fund-turn once and list its flagged pairs. If the break is after entry, refuse rather than removing a possibly held position. The existing minimum eligible count still applies.
- Do not use a clearance to admit an actual missed split, waive a bad bar or cover an unresolved problem. Correct supported input errors upstream and re-pin, or stop. The custodian and second reviewer verify the evidence and its digest off-packet. The scorer checks the approved clearance file and structural pin, not the merits of or bytes behind each private evidence reference.

## Historical identity

- Join ticker changes within a fund-turn using the same historical security, not a literal ticker shared by different securities. Preserve the actual raw prices and dates; a ticker change does not rescale prices or shares. Join before the same jump check, including across ticker boundaries. After entry, use the correct alias for the exit close rather than excluding a held fund at the rename. Quote, corporate-action and adjusted-control collection uses the historically valid ticker for the date, assembled under the stable roster key and independently attested in private evidence.
- Add an actual source `symbol` field to every roster bar row in `bars_Y.json`; the benchmark retains its old schema. An undeclared fund-turn accepts only the roster ticker. A declaration accepts only the assigned historical symbol on each session. Shared validation still checks ordering, duplicate sessions, timestamps, volume and usable closes. The source tag is an approved custody attestation; the scorer does not look up symbol identity externally.
- Query native split evidence for every actual segment or literal ticker using the original padded query window. Bind an in-window split record for a segment only to the roster identity active on its ex-date; an overlapping claim to the same source symbol and session for different funds refuses. Adjusted-check counts still describe the assembled stable roster series. Keep raw queries and issuer support in private custody.
- A declared schedule starts at anchor. Segment date ranges are inclusive NYSE sessions, ordered, non-overlapping and contiguous, even across a weekend or market holiday. A normal schedule tiles through the judged exit; a documented permanent cessation allows a terminal schedule ending earlier, and bars outside that schedule are refused even if the ticker text is later reused. A single full-span alias is allowed when it differs from the roster ticker. An unchanged single full-span row is redundant and refused. Scheduled coverage never creates a price: missing and zero-volume sessions within a valid segment are still treated as missing bars.
- Still require usable closes for every session through entry. Reasons are disjoint: a fallback identity break takes priority, then documented termination before entry, missing entry, missing formation, another pre-entry gap, a pre-entry split, or an unaffordable share. A documented delisting before entry leaves the name in the frozen roster but not in the eligible set. Keep the old after-entry treatment for a genuinely missing exit.
- Correct the one documented roster ticker typo upstream. Re-pin `replay_53_plan.roster_attestation.roster_sha256`, `PINNED_53.json` (`packet:roster.csv`) and all corrected packet components. The original preregistration's printed digest remains the historical v1 value, not the approved v4 digest.

## Packet and approval

- Use manifest mode `plan53_raw_sip_v4` and add both `jump_clearances.csv` and `identity_segments.csv` to the file map. Both are off-repo and owner-only. Use ASCII with LF line endings, the exact headers below, and no quoting or blank lines. An empty file has only the header and its final LF. The jump rows are strictly ascending by turn year, ticker, earlier date and later date. Segment rows are strictly ascending by turn year, roster ticker and first session. Segment identity is the exact ten-digit historical fund CIK from the roster. Every date is a session of the turn.
- `evidence_ref` is a credential-free HTTPS reference without userinfo, query, fragment or comma, or `evidence:<identifier>` with ASCII letters, digits, dot, underscore or hyphen. `evidence_sha256` is the lower-case SHA-256 of the exact retained evidence bundle bytes, not of the reference text. A shared evidence bundle must expressly attest each pair and class it covers. Keep evidence and bars out of Git.

```text
turn_year,ticker,earlier_date,later_date,classification,evidence_ref,evidence_sha256
```

```text
turn_year,roster_ticker,fund_identifier,segment_ticker,first_session,last_session,evidence_ref,evidence_sha256
```

Only the lead can approve validation and one score. The sole newly added file `research_rig/APPROVAL_53.md` is in a direct child commit of the replacement freeze, with this exact ASCII sentence and final LF. All SHA values are lowercase hexadecimal.

```text
Approved by the lead: plan 53, validation and one scored run, freeze commit <freeze-commit>, freeze SHA-256 <freeze-pin>, input SHA-256 <input-pin>, roster SHA-256 <roster-pin>, distributions SHA-256 <distributions-pin>, jump clearances SHA-256 <jump-clearances-pin>, identity segments SHA-256 <identity-segments-pin>.
```

```text
python3 -I -B research_rig/score_53.py <--validate-inputs|--go> --approval-commit <approval-commit> --freeze-sha256 <freeze-pin> --input-sha256 <input-pin> --roster-sha256 <roster-pin> --distributions-sha256 <distributions-pin> --jump-clearances-sha256 <jump-clearances-pin> --identity-segments-sha256 <identity-segments-pin>
```

Both new digests must also match their input manifest entries. `--calibrate` remains synthetic and takes no pins. For a structurally valid packet, validation emits a sorted `P53_JUMP_REPORT` JSON line with the union of flagged and clearance keys and each outcome, including on a jump policy refusal. It prints no closes, ratios, evidence references, ranks or marks and takes no lock. A malformed structure or failed pin can stop before the report. Successful validation also prints the count line. A failure refuses before the once-only lock. Scoring keeps the same report in shown-only results, with no additional decision. Nothing here authorizes a real run or a second score.
