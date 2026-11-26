# Plan 63B closed on coverage

STATED, lead agent, November 26, 2026: Plan 63B (queue 102, ledger 206) is closed. Even the more permissive of the two audited coverage rules left fewer than 200 eligible day-by-filer groups at every hold. This is a coverage stop, not a verdict on the trading idea.

## What the plan was

- **STATED: question.** Test whether listed US closed-end funds behave differently after activist SEC Schedule 13D filings, using the PCEF fund as the benchmark. The plan first needed matched earlier windows in the same funds, called placebos, to judge how much noise the test would face. The holds were 5, 20 and 60 trading sessions. The placebo window could not touch the same security's raw filing embargo or an applicable successor date.
- **STATED: stop rule.** Close without projection if all three holds have fewer than 200 eligible acceptance-day-by-filer groups. A group is one filer on one SEC acceptance calendar day in New York, even if several eligible fund windows share it. The counts below are always in 5 / 20 / 60-session order. Window counts and group counts are not interchangeable.

## Where the coverage went

- **MEASURED: starting exclusions and denies.** The original scope excluded 12 subjects with unresolved identity and one with no mature window. Nine further funds were out of the placebo arm under the earlier custody repair. All 86 original deny rows, covering 42 distinct exclusion tuples, stayed at their full original bounds in both arms. Of the 52 deny rows under review, 10 matched replayed CUSIP evidence, 29 had an SEC fund-report ticker observation, and 13 stayed exclusions on policy alone. A policy exclusion was not called primary proof. The completed deny join found no additional retained-name or PCEF collision. Before the later identity gaps, the working placebo count was 262 / 253 / 230 groups across 341 / 327 / 301 eligible windows.
- **MEASURED: missing identity proof.** Whole-range gaps covered subjects without adequate dated identity proof. Dated gaps covered unresolved tail periods, alias transitions and missing ticker evidence. The identity pass kept 280 / 267 / 251 windows, or 218 / 210 / 196 day-by-filer groups. Compared with the earlier eligible windows, 42 / 41 / 36 were lost to whole-range gaps and 19 / 19 / 14 to dated gaps. Removing a subject from the eligible placebo set did not remove its raw filing embargo.
- **MEASURED: disputed CUSIPs.** The auditor found two pairs in which an apparent conflicting CUSIP was printed in a filing. Other filings listed a different CUSIP, but held primary evidence did not prove a correction or resolve the identity conflict. The lead quarantined all four subjects and preserved the full embargo for each possible match. Another 6 / 5 / 5 eligible windows were lost. The audited baseline before the successor scan was 274 / 262 / 246 windows and 216 / 208 / 194 day-by-filer groups.
- **MEASURED: benchmark evidence.** Dated SEC evidence supported the same PCEF class, ticker and exchange through its name change. The second quarter of 2018 and October 1 to November 16, 2026 were flagged as class-only where the CUSIP was not proved. These were flags, not exclusions: 3 / 2 / 4 otherwise eligible windows in the quarantine baseline, 1 / 0 / 2 under the whole-range successor rule, and 2 / 1 / 3 under the dated-tail rule. No eligible window at any hold needed a PCEF print after the proved end date under either rule. A possible benchmark identity collision would still have stopped the test.
- **MEASURED: successor scan.** The custodian checked the held and new SEC submissions indexes for all 186 subjects left after the full identity and collision gaps. The auditor verified 156 with no flagged in-span change and 30 with unresolved events in their spans: 19 had relevant form hits and 11 had name-history changes. The hits were risk signals, not proof that a merger, liquidation or change of class had taken place. Requests went from 510 after the cover replay to 741 after the bounded identity check, then to **890 of 1,500** after the successor scan. The last 149 requests were 141 main indexes and eight older pages.
- **MEASURED: whole-range successor rule.** Gapping all 30 flagged subjects for their whole histories left 218 / 209 / 196 eligible windows and **179 / 171 / 160** day-by-filer groups. The auditor reproduced these counts from the v4 package. All three holds were below 200.
- **STATED: lead agent's refinement.** Using the coverage counts only, the lead asked the auditor to retain any otherwise proved time before the first unresolved event and gap only from that event onward. The earlier identity gaps, collision quarantine, and full raw embargo stayed in place. The 200-group stop line did not move, and no other refinement was authorized.
- **MEASURED: dated-tail upper bound.** The auditor independently counted 234 / 223 / 210 eligible windows and **193 / 183 / 172** day-by-filer groups under that refinement. This is an upper bound: adding further conservative gaps can only lower it. It left every hold below 200, so the lead closed the row without building another custody package.

## What was not done

- **STATED: no run.** The earlier projection approval was withdrawn, and the replacement source freeze never received a projection approval. No bars were opened for this work. There was no projection, measurement, live-data power run or target run. The earlier sealed capture remains untouched; no test result exists.

## Evidence pins

The following SHA-256 pins identify the held material behind the counts. The dated-tail bound was counted in memory by the auditor using the same pinned inputs and was not written as a separate package. No custody rows or filing excerpts are published with this record.

- **MEASURED: freeze manifest** for commit `32eaef7316e87c9712e5063f4a53c1abea239cfa`: `f2cc56f041bc25f9cb95003d2143559be990de03888841192a97df750a98c029`.
- **MEASURED: original Stage A scope and deny authority:** `39e62436a4a5162bb212a9f2bea212a06a7f3b58bf4d98f28434f48aff9a0a56`.
- **MEASURED: replayed SEC cover-prefix manifest:** `31a420e093e7223c2a58669530c7fe65c83d1e5535ef8852765a465ff540971f`.
- **MEASURED: bounded SEC identity scan and count:** `4b4c802f41c16872bb071e63c78204648f5c582285a3b3db942711ab714b73b9` and `e8a7b0dea059d82dda2b5dff637ff75e5357a85257aae782923431a1d30657d4`.
- **MEASURED: PCEF primary evidence manifest:** `cf35e66e69551d64fd3587c549b8853ac082b77d4c6bea52d2662fcd8571a2e1`.
- **MEASURED: v3 quarantine package manifest:** `dbda96a331b8af33c9d022834763b7d50e8c73c3052775f1bdd256fc6eb157f3`.
- **MEASURED: v4 whole-range package manifest:** `475e8183c0ae97c0c88977890e30a1db72382d17216feb1a8b44c0a0470c5142`.
- **MEASURED: SEC successor index scan:** `79c03b6320922cb8404ac5bd14f4d3fd4e6e06e4b111927ef4d73c1a24810506`.
- **MEASURED: SEC request log:** `158479dc32ed8b38d632497034ac80a64962ff46d5943ad095d9fa86bfc84bfd`.

## Lessons

- **STATED: count usable coverage first.** Apply the strictest dated identity standard, including possible CUSIP collisions and unresolved successor events, before building the projection and measurement code. The filing count alone did not say how much usable placebo coverage remained.
- **STATED: check the frozen code before ruling.** Check whether a frozen runner can represent an exclusion kept on policy, a narrow date gap or a benchmark class without a proved CUSIP. If it cannot, change and audit the source before any approval, rather than stretching the evidence to fit.
