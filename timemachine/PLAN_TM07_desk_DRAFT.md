# Time machine plan 07 draft: the desk

Does a desk with cheap scouts, a bigger boss and a plain order program beat the same boss alone? This is a pretend replay, not a live trade. Dates, arms, costs and marks below are fixed before any TM07 run. No real tape or model was run to build this branch.

## Arms and input

- Use TM06 Part S. Keep the original 20-coin watch list, hourly UTC wakes and five tradable coins per week. BTC is a reference, not a watch name; ETH is out. Start each week at the same simulated cash amount. Keep the registered TM06 cost assumptions, minimum change and maintenance thresholds, and use the TM07 order and liquidation rules below. Judge all arms, equal hold and timing twins at 1x and the same 12 bp per side. Show recomputed results at 25 and 40 bp per side and at 2x and 3x for scale only. None can rescue a failed main result.
- Bosses: `claude_fable_5_2` and `claude_opus_5_5`. A is a fresh solo boss. It sees the full raw packet. B is the same boss with scouts. C is the same boss with scouts and standing orders. B and C see the notes, their own book and the clock. All arms have the same three lookups per wake. The TM06 archive is shown only. It is never the judged baseline.
- Scouts: two `gemini_neon` roles. Both read the same raw packet on all 20 coins at every wake. The price scout looks for price and volume; the news role remains but has no news or attention evidence in this replay. Neither sees a book or an answer. Each can send two short notes with visible evidence IDs and no advice, or none. Plain code merges to at most four and adds the visible price and volume row. The notes carry the date, coin, raw evidence and a short description.
- Run the neutral scouts once per week. Seal their note stream and copy it independently into each desk arm with its hash. Workers are sibling agents on the same host as uid 2000. Give each a written brief and only its role bearer; for handoff start a new agent with only its own server handoff text. The desk serves only its own authenticated routes. The scorer runs under the desk's service account and compares arms after replies are sealed.
- Price-only means no news or attention input. The dated headline store carries created and updated clocks but no `known_at` clock proving when an exact version was available. Missing news is UNKNOWN, not a zero event count. The prospective status logger is separate future work. No feed was added.

## Venue and proxy gaps

- **Route and calendar, MEASURED / STATED:** This is a present-targeted proxy for Coinbase Financial Markets US perpetual-style futures, not venue-true execution. The November 2026 public catalog contains the original 20 names. [Doc 98](../docs/research/98_kraken_and_coinbase_short_access.md) records first positive-volume UTC daily candles, with some names first seen in December 2025, February 2026 or June 2026. Those are not verified listing-minute clocks. Retail API access requires derivatives approval; actual account eligibility is UNKNOWN ([Coinbase futures API guide](https://docs.cdp.coinbase.com/coinbase-business/advanced-trade-apis/guides/futures)).
- **Fills and funding, STATED:** Fill prices are Coinbase spot minute bars, not futures trades or quotes. The existing non-US Kraken funding series and the configured fallback are proxies, not CDE funding. It is not an execution, spread, slippage, funding or margin claim.
- **Fees, STATED / UNKNOWN:** The flat 12 bp proxy is above the published 0.05% introductory variable component. Adding the separate $0.15 per contract per side, it exceeds that illustrative combined reference only for a contract worth more than about $214.29; this is not a verified fee schedule. The true entry-tier rate is UNKNOWN ([Coinbase fee references in Doc 98](../docs/research/98_kraken_and_coinbase_short_access.md#coinbase-financial-markets-us-perpetual-style-futures), [Coinbase US derivatives pricing](https://www.coinbase.com/derivatives-trading/us-derivatives), [Coinbase futures API guide](https://docs.cdp.coinbase.com/coinbase-business/advanced-trade-apis/guides/futures)).
- **Whole contracts, MEASURED / UNKNOWN:** The replay ignores whole-contract minimums. Doc 98's public snapshot shows roughly $9 to $306 of intraday short initial margin across its table (about $13 to $306 for the watch). At $100 of collateral per name on a $500 account, one lot does not fit intraday for AAVE, BNB, ENA, HYPE, NEAR, XLM or ZEC. Only ADA, AVAX and DOT fit that equal allocation overnight. Even for one position using the full $500, NEAR ($859.62) and ZEC ($748.17) do not fit overnight. For the original baskets in the order below, one lot per name would require $766.94, $483.32, $617.16 and $516.41 intraday, and $2,229.41, $1,609.81, $1,844.18 and $1,148.67 overnight. So a $500 account could not hold all five whole contracts for every basket; only the July basket fits intraday on pooled collateral before costs and all four fail overnight. These are illustrative short initial margins at the November snapshot, not replay-week margin or order previews ([Doc 98 margin table](../docs/research/98_kraken_and_coinbase_short_access.md#coinbase-financial-markets-us-perpetual-style-futures), [Coinbase margin sessions](https://help.coinbase.com/en/coinbase/derivatives/us-derivatives-leverage-margin)).

## Weeks

Months refer to UTC. Ends are excluded. The table preserves the five original TM06 names per screen and optional diagnostic. MEASURED against Doc 98: all original fixed names meet the first-seen check, so no listing swaps are needed. BNB and HYPE were not yet observed in the May diagnostic week and cannot be substitutes there. All 20 clear the listing check in every scored week. Exact minute coverage remains UNKNOWN.

| Monday start | Five coins | Use |
|---|---|---|
| 2026-05-11 | ENA, NEAR, ONDO, SUI, ZEC | Diagnostic only |
| 2026-07-20 | LINK, LTC, ONDO, PEPE, ZEC | Screen |
| 2026-08-31 | BNB, HYPE, LINK, SOL, ZEC | Screen |
| 2026-10-05 | AAVE, ADA, BNB, HBAR, XLM | Screen |

### Model clocks and build gap

The [TM06 knowledge check](../docs/research/31_model_knowledge_lines.md) records the models' own statements, not verified training dates. For each TM07 participant, take the day after the later stated bound; for a month, take its last day as the bound. The latest participant bound makes July 1, 2026 the earliest scored day. May remains diagnostic only. If the declared model changes, recheck the cutoff before approval; a later date blocks affected fixed weeks rather than moving them.

| Participant | Platform model ID | Maker cutoff | TM06 self-report | Earliest after both |
|---|---|---|---|---|
| Claude Fable 5.2 | `claude_fable_5_2` | STATED: June 2026 ([Anthropic](https://platform.claude.com/docs/en/models/fable-5-2/overview.md)) | STATED: February 2026 | 2026-07-01 |
| Claude Opus 5.5 | `claude_opus_5_5` | STATED: June 2026 ([Anthropic](https://platform.claude.com/docs/en/models/opus-5-5/overview.md)) | STATED: January 2026 | 2026-07-01 |
| Gemini 4 Neon | `gemini_neon` | STATED: March 2026 ([Google DeepMind](https://deepmind.google/models/model-cards/gemini-4-neon/)) | STATED: March 2026 | 2026-04-01 |

For each run record the exact platform model ID and actual UTC run date. Run date is UNKNOWN until launch; the immutable weights or serving build are UNKNOWN because the platform does not export them here. A matching platform ID is not proof of an unchanged build. Seal the three approved platform IDs in the registration model fields and record runner ID `tm07_desk_v1`. An unresolved platform ID blocks launch.

The other four models from the original TM06 six are context only and do not veto TM07 weeks:

| TM06 model | Maker cutoff | TM06 self-report | Later planning bound (not a TM07 gate) |
|---|---|---|---|
| GPT-6.2 Sol | STATED: June 1, 2026 ([OpenAI model page](https://developers.openai.com/api/docs/models/gpt-6.2-sol)) | STATED: December 2025 | 2026-06-01 |
| Claude Sonnet 5.5 | STATED: June 2026 ([Anthropic](https://platform.claude.com/docs/en/models/sonnet-5-5/overview)) | STATED: November 2025 | 2026-06-30 |
| Kimi K3 | UNKNOWN: no cutoff established in [Moonshot's model guide](https://platform.moonshot.ai/docs/guide/kimi-k3-quickstart) | STATED: July 2025 | 2026-06-30 as a conservative planning bound only, not a cutoff claim |
| Grok 4.7 | STATED: May 2026 knowledge cutoff ([xAI API docs](https://docs.x.ai/developers/grok-4-7.md)); June pretraining, supplemental data as late as August 2026 ([xAI model card](https://media.x.ai/v1/website/card4p7-3a96f40b.pdf)) | STATED: January 2025 | 2026-08-31, conservatively including supplemental data |

These are the 17 fixed Monday starts for extension. The last week ends November 23. For each week require a first-seen date before Monday 00:00 UTC and at least 90% distinct minute coverage. Keep eligible original fixed names. For vacancies in a fixed basket, and all five names for extension, rank eligible candidates by the ratio of the two prior completed Sunday closes, largest rise first, with the descending symbol tie rule. Record each displaced name, reason and replacement in the sealed registration before any session. Missing exact counts, missing required Sunday pairs, or fewer than five eligible names block the week; never move the week or choose replacements after the freeze. Freeze without reading answers or returns.

| Month | Extension Monday starts in 2026 |
|---|---|
| July | 06, 13, 27 |
| August | 03, 10, 17, 24 |
| September | 07, 14, 21, 28 |
| October | 12, 19, 26 |
| November | 02, 09, 16 |

## Marks

- Open the extension only for a boss and desk arm that beats fresh A to the cent in all three screen weeks. A tie is not a win. A missing or invalid week is not a win. Do not replace a week. An incomplete comparison cannot pass. Different bosses on the same week are not two independent weeks. The fixed extension also requires raw bars for all 17 weeks to be unreadable by uid 2000 without sudo throughout extension sessions; failed or missing checks block the extension.
- Keep both TM06 one-model marks. Chain the net weekly gains. Beat the five coins held equally and the 90th percentile of the 1,000 shuffled timing twins. Those are the only mandatory judge lines. Compute equal hold and BTC holds with the unchanged pre-TM07 replay on separately frozen legacy inputs. Do not apply the TM07 target sizing rule to those yardsticks. BTC long, BTC short and other optional displays report failures as `not computed`; missing BTC display coverage cannot block registration unless BTC is itself a required trading coin. Shuffle full answers within each week. Keep exit distances and condition distances relative to the new wake price. Preserve time to live. A shuffled keep with no active match does nothing. Show twin fills and turnover. Do not claim the realized trigger count stays fixed.
- The one-sided per-claim cap is 1.25%. There are four claims, B/A and C/A for each of two bosses. The limit is 16 wins out of all 20 weeks, including the three used for the gate. The table uses the unconditional binomial tail. Requiring the screen gate can only make the combined rule stricter under that null. Display the weekly lift and the two TM06 marks separately. C/B is descriptive only.

| Weeks | Wins | One-sided fair-coin tail |
|---:|---:|---:|
| 3 | 3 | 12.5000% |
| 4 | 4 | 6.2500% |
| 20 | 15 | 2.0695% |
| 20 | 16 | 0.5909% |

MEASURED by exact arithmetic, not market results. The test assumes independent weeks. Timing, season and common headlines can make that assumption weak. Report the weekly pattern, not only the p-value. Forty weeks of post-cutoff past do not exist. Forward weeks from the live recorder can be proposed later under a new plan, not appended after seeing results.

## Orders and evidence

- Weights and optional protective exits use the existing TM06 reply fields. In C the boss may also ask for a weight after a strict above/below signal. Use a price or a percent from the last finished mark. Use one to six hours and at most two active orders. New conditions, replacements and omissions have no effect during the install minute; they take effect on that coin's next recorded bar. A kept condition keeps its first price, expiry and source IDs.
- For a standing condition, check the high or low only once the minute has ended. If touched, wait for the first recorded open with a price for the order and every held coin, strictly before expiry. A flat coin is still watched. Each immediate move waits for a common open for all held and affected coins, in all arms. A missing common open freezes that move, not the simulated clock. For the judged set, preflight coverage before workers start. A required twin that cannot replay the full move makes that fixed week invalid. Never replace it.
- Standing orders triggered by the same completed minute wait for a common open for all still-live orders in that group and every holding. Solve that group in one basket with one post-cost scale. Leave unrelated holdings fixed. If multiple trigger minutes wait for the same open, consider the older group first.
- A protective exit is the exception to keeping the entire submitted basket. It cancels an already submitted but unfilled leg for that coin, even when other legs are waiting for an open. The remaining legs do not need another open for the exited coin and are sized from their original requested weights.
- Compare each explicit vector with actual holdings at its eligible common open, including assets acquired by standing orders. A held coin absent from the vector has a zero target. A `no_change` reply does not rebalance; ordinary exits, maintenance and standing orders still run. The saved holdings display is derived from the live book and checked after each transition. It is not an input to execution.
- Use one full-book maintenance rule in A, B and C. Price each long at its minute low, each short at its high, and a holding without a bar at its last bar close. Check the carried book before any open fill. If it fails, close it there and suppress the open fills. After the open fills, stress the new book against the same bar's range, with a check at bar close before ordinary resting exits. New exposure has no free minute. At each funding stamp, net all debits and credits on the quantities held at that instant, then check once at that minute's adverse marks. This applies at exact-hour and off-minute stamps. At session end use the frozen final marks for the final check, after any settlement. A failed check closes the whole book at its check marks with fees and penalty, and floors equity at zero.
- Settle each observed funding rate at its recorded stamp on the quantity then held in the simulation. At a shared boundary, account for the previous bar's close events, settle funding using the pre-open-fill quantity, then process the new bar. Mid-minute funding precedes a protective exit inferred from the complete bar. That exit is accounted at bar close, even if a real touch could have occurred earlier. The true order of funding and touch is UNKNOWN. A fresh or updated stop or target first goes live on the next recorded bar for its coin. For a completed bar that could hit both levels, take the stop. Use the open only if it is already through the selected level.
- Immediate fills come before triggered entries. A real immediate fill can cancel a conflicting older condition at that open. Count at most one physical open fill per coin. Fill a solved basket at one open, with no intermediate book between its legs. Charge the spread and fee on each position change. Check gross, equity and maintenance only on the combined post-cost book. If needed, scale the entire eligible basket by one common factor. Apply the min-change floor only if the whole basket is below it; closing or reversing a position still counts as a move. A standing basket cannot fix an over-cap book if the unchanged holdings alone leave no room. Missing simultaneous marks never authorize a new immediate or standing entry; the maintenance check still uses all holdings.
- Role checks and wake keys guard all requests. Each recorded trade links to its cited evidence where available. Journal the wake, condition transitions, observable trigger, open, fee and spread. A note link says what the boss cited, not what made the gain. Save genuine provider token usage for each role and call. The cost of the reusable neutral stream is charged once in study totals and once per arm in standalone comparisons. No token telemetry means UNKNOWN.
- Rebuild packet evidence and lookup rows from the typed field list. Reject a row with undeclared fields or a malformed or future clock. An evidence clock is integer Unix seconds or a decimal string with its full fraction; a JSON float is not a valid clock. Sources and proofs stay with the operator. Quote rows require an observation stamp, and a bars lookup cannot manufacture a quote from an unstamped mark. Rebuild scout notes against the admitted evidence again before a boss sees them. Do not forward note metadata. Count dropped evidence rows by kind in the operator journal only.
- Scouts can miss the one event that matters. An absence can mean tape failure. A small historical sample can reward simple drift. Bar opens are not executable quotes. A move may slip, arrive late or fill only in part. Show a delayed-open check and a higher fee check. Neither can rescue a failed main mark.
- The carried-book check deliberately looks ahead to the full minute and can block a reduction that a real trader might have made at the open. The boss does not see that bar in advance. For new exposure, the simulator places the open first and treats the same bar's range as available for stress afterward. An exact funding debit can use that range before the bar ends. We do not know when either extreme really occurred or whether different coins hit them together. This is pessimistic marking, not a guarantee of worse returns for every arm. Real-venue accuracy is UNKNOWN.

## Build and limits

- `desk.py`: frozen packets, role checks, note storage, a short lookup list, decisions and usage. `desk_orders.py`: arm and cancel, scan bars, queue and fill. `score_tm07.py`: replay checks, twins, paired marks and the extension calendar. `test_tm07.py`: made-up bars and records only. `TRADER_BRIEF_DESK.md`: role and answer rules.
- Separate small changes wire the guarded server, weights dispatch and replay helpers. Keep legacy paths when there is no desk. Prove parity with fixture books, records, fills and final value. No recorder, ledger or config change belongs in the build.
- The [same-host launch gate](TM07_WORKER_PROBE.md) requires a separate Unix service account and a mode-0700 registered root for tape copies, journals, notes, bearers and scores. Each registered session starts with a fresh rehearsal as uid 2000, a checked sudo canary, and a single-use, 10-minute startup receipt bound to the launch and root inode. An extension also checks its raw bar inventory without reading content in that launch and after it stops. A request outside the allowed stage is refused before opening week files. The operator reviews the root-owned sudo log before and after each session; unexplained sudo use or missing evidence blocks or invalidates it. The diagnostic is not eligible through the registered listener.
- UNKNOWN: whether a worker deliberately uses passwordless sudo, the web, or other price files. The screen raw bars under `/home/user/workspace/rig` remain readable, as in TM06. Provider-side memory and the full provider request are also UNKNOWN. There is no wrapper or worker launcher to control these; instructions and sudo log review do not prove compliance. Actual host setup and rehearsal have not been run.

## Review answers

### Eighth pass at `e08f4c3`

- Opr A1 / Sol A1: The supervisor runs a fresh rehearsal and raw access check as applicable, then seals a nonce-bound receipt with the root device and inode, port, stage, release, named session and 10-minute expiry. The server atomically consumes it. MEASURED: a replay, changed inode, port or stage, expiry, and missing extension proof fail before listener creation. A genuine sudo canary must grow the root-owned log and appear in the new bytes; an empty log and growth without the canary both fail. Pre- and post-session sizes and hashes are saved.
- Opr A2 / Sol A2: MEASURED: a readable raw file is named and refused without calling read. All six routes refuse the wrong stage using the private attempt index before loading or checking any week file.
- Opr C1 / Sol C1: MEASURED: each runbook shell block passes `bash -n` and both launch command lines pass the real argument parser with execution mocked. The operator still needs to rehearse on the actual host. Privileged log tampering and continuous access denial between samples are not proven.

### Seventh pass at `24e6c66`

- Opr B1: The saved display check allows a few ULPs of relative rounding difference. Symbol membership and exit ownership still match exactly. MEASURED: three ULPs pass; stale values, nonfinite values and missing or extra names fail. This does not change legacy valuation, sizing or replay.
- Lead launch ruling: The same-host gate above replaces earlier launcher, namespace, egress and provider-wrapper rehearsal requirements in these review notes. The receipt covers what the uid-2000 probe can observe. It does not assert isolation from sudo, from the web or from provider-side memory.

### Sixth pass at `293635e`

- Opr A1: MEASURED: after a −1 short at $100 and a drift to $80, a standing +.25 order buys 2.99520910 B. The next explicit `{A: -1}` resizes A and closes B. Actual holdings set the eligible common open and the saved display reflects the resulting book.
- Sol A1: MEASURED: the two-wake arm C witness buys 3.98723065 B via a standing +.50 order. A restarted session shows B, the explicit `{A: -1}` closes it, and the journal and scoring replay agree at $1,196.17. An otherwise identical `no_change` keeps B and ends at $1,157.57 on the $90 terminal mark. The explicit `-.999999` control agrees to the cent. No nominal cap veto was restored.
- Both reports: No B or C findings. MEASURED: the invariant rejects a stale saved display when an update is deliberately skipped. The 96 legacy slow/fast checks are unchanged. Deployed isolation, real-venue behavior and feed coverage remain UNKNOWN. The actual launcher rehearsal and independent deployment review are still required.

### Fifth pass at `51b947f`

- Opr A1: Use one atomic open-fill step for immediate, simultaneous standing and surviving protective-override baskets. Price each delta and check only the combined post-cost book. There is no gross-reduction ordering or intermediate guard. MEASURED: both audited reversals now fill, and 108 seeded portfolios plus a maintenance-limited basket produce identical economic books under three label permutations. Feasible targets retain size; cap- or maintenance-bound targets scale together.
- Sol A1 / Opr A2: Standing orders triggered in the same minute share one solve and wait for a common open. MEASURED: the two .50 legs both fill and the result is unchanged when the rising and falling paths swap labels or one first open is missing.
- Sol A2 / Opr A3: A protective exit is the named exception to basket completeness. It cancels the affected unfilled target leg, including while a common open is pending; the scan journal lists the cancellation and the boss brief states the rule. MEASURED: audited gap-stop cases leave the requested surviving leg, and the missing-bar path does not bring the stopped leg back. An intrabar stop before a delayed open produces the same cancellation.
- Sol A3 / Opr A4: Net all simultaneous funding on the quantities held at that stamp, then check maintenance. MEASURED: both credit and debit are booked in the two audit cases at the hour and 45 seconds after it, with no ticker effect. A net debit that truly breaches maintenance still liquidates at that stamp.
- Sol C1: The completed-minute high/low rule is explicitly scoped to standing-trigger observation. The separate maintenance proxy still uses the whole minute.
- Deployment gate: Actual isolation and real-venue behavior are UNKNOWN. The real-launcher rehearsal and independent policy review remain required before any registered session.

### Fourth pass at `9301c83`

- Sol B1 / Opr P4-B1: Use the whole post-cost solve below, at and above the nominal cap. A near-cap long, short or two-name basket no longer loses legs because costs consume the remaining cushion. This supersedes the exact-cap-only path.
- Sol B2: Superseded by Opr A1 in the fifth pass. The four-pass fix ordered reductions first, which closed the nine-unit case but did not cover every feasible reversal.
- Opr P4-B2: BTC long and short are independently optional in the score. MEASURED: a missing BTC-only price passes registered preflight, and a BTC-only score failure leaves a valid equal hold and the timing twins.
- Sol S1 and S2 / Opr P4-B3: Recheck adverse maintenance on the entry minute and after each debit, then once more at the session-end marks. MEASURED: the new short is closed using its entry bar's high; both reported debit examples liquidate at the exact debit stamp; a separate end-mark breach closes at the frozen end mark.
- Opr P4-S1: The plan states the difference between pre-open look-ahead on carried exposure and the post-open stress on new exposure. Worse marks do not guarantee worse reported returns; timing bias and venue accuracy remain UNKNOWN.
- Sol B3 / Opr P4-B4: A typed whitelist replaces date-key guessing. MEASURED: an unknown nested field carrying a later time, an origin with an unknown numeric clock, a declared clock one nanosecond after wake, and a JSON number rounded to the wake are excluded. A valid decimal string at wake passes. Neither a packet nor a lookup forwards origin metadata, and even a correctly sealed scout note is rebuilt before a boss sees it. The operator tally follows the admission decision.
- Sol L1 / Opr deployment gate: The sampled receipt is unchanged. The real-launcher rehearsal and independent deployment-policy review are still required; no operating evidence is claimed.
- Sol V1–V3 / Opr V1–V3: MEASURED: 55 synthetic TM07 fixtures and 96 unchanged legacy comparisons passed (108 closeouts, 1,016 exits). The registered calendar, gate and cent ties are unchanged. No real tape, worker, model, listener or probe was used and no study result is claimed.

### Third pass at `be0a560`

- M1 / P3-B1: Scale an exact-cap target as a basket on the common open, net of actual position delta costs. MEASURED: +1, −1 and .5/.5 enter fully to just under the cap; the fixtures cover an existing position, a ready standing entry and a genuine refusal. This is not a change to legacy sizing.
- M2 / P3-B2: Call unchanged pre-TM07 `P.run_perp` on frozen legacy hold inputs for the equal hold and BTC holds. MEASURED: five-name equal hold and BTC long and short match to the cent on the falling, flat and rising toy tape. This supersedes the costed yardstick in Opr R1 and Sol R03.
- M3 / P3-B4: Before new fills, stress all held coins together. Use each long's low and each short's high; substitute the last close for a missing bar. If equity is under maintenance, liquidate the entire book at those marks with the penalty, floor at zero and block that minute's new fills. MEASURED: jointly adverse shorts close before the recovering open; with the second coin's bar missing, both holdings close before the ordinary stop. This replaces the later-open liquidation in Sol R02 and Opr R2.
- M4 / P3-S2: Main replay, its required benchmarks and twins are judged separately. A failed display cell, optional twin or delayed replay is `not computed`, not a reason to invalidate main. MEASURED: independently unsupported 2x and 3x display cells leave the $1,000 idle main available.
- M5 / P3-B3: Superseded by fourth-pass Sol B3 / Opr P4-B4. Quote rows and bars lookups still require an observation stamp, and a future or malformed clock still excludes a row. Real vendor coverage is UNKNOWN.
- M6: Activate new or updated resting changes strictly after the install minute and only on the coin's next recorded bar. A newly installed stop cannot cancel an already-ready condition at that same open. MEASURED: the older order still acts; a replacement on a coin with a missing next bar waits for that coin. A real immediate fill retains precedence over a conflicting older condition. When the completed bar can hit both exits, take the stop.
- M7: Book intra-minute funding before non-gap exits inferred from that complete bar. Book those inferred exits at bar close, not at an invented touch time. MEASURED: the five-unit 1% fixture charges $5 before the inferred stop. True funding-versus-touch order is UNKNOWN. This qualifies the simulated quantity claim in Sol R05; the source settlement stamp is still exact.
- S1 / P3-S1: The later-open recovery bias is no longer the liquidation rule. Simultaneous adverse extrema with a penalty are deliberately worse than a real venue could be. This can penalize arms that hit maintenance more often, especially at leverage. Real-venue accuracy is UNKNOWN.
- L1 / P3-S3 / Opr deployment gate: The receipt is sealed and release-bound but declares sampled rehearsal only; an unscoped or overstated receipt is refused in mock tests. The real launcher, mounts and shared writable state, egress lanes and sidecars, request assembly, and rehearsal equivalence require separate independent operator review and real-launcher rehearsal before a session. This qualifies Opr R4 and Sol R06. Production boundary evidence is UNKNOWN. The launch gate remains open.
- Sol V1 / Opr V1: All arms share the TM07 engine. The 96 legacy parity checks pass with 108 closeouts and 1,016 exits. This checks the unchanged legacy path, not parity between legacy and the new TM07 risk policy.
- Sol V2 / Opr V2: The fixed calendar, strict cent tie, 3/3 gate, 16/20 mark and 1,000 timed twins at the 90th percentile are unchanged. The tests do not establish independent weeks, exact deployed model cutoffs or tape coverage.
- Sol V3 / Opr V3: Verification used 49 synthetic fixtures with a memory ceiling and `nice -n 10`. No real tape, model, registered run, production listener, launcher or socket probe was used. No operating result or launch clearance is claimed.

### First audit

Sol's review of the first branch flagged the findings below. The fixes were tested on made-up bars. The 96 legacy perp parity checks were rerun after each commit. This does not clear a real-tape run.

- B01: Wake and end marks now use only completed closes. A newer published close wins; the finer bar breaks ties. A later bar cannot change a past quote or a percent trigger.
- B02: All arms wait for a common open. A later B open cannot size an earlier A fill. The same rule applies after C cancels its last standing order.
- B03: Initially moved off-hour funding to the next lawful hourly charge. Superseded by re-audit Sol R05: use the source settlement stamp exactly, without rounding or redistribution.
- B04: Vendor evidence requires an operator seal over the exact version, rights, timing, and independence records. A claimed confirmation after the wake does not count. Note exports are sealed against their fixture, designated neutral run, wake, and visible evidence. Actual vendor coverage is UNKNOWN.
- B05: A dedicated listener serves no legacy routes. Role tokens are unique across its root. The listener refuses launch without a sealed record of worker-isolation probes. Production sandbox and probe execution are not yet proven.
- B06: A real immediate fill cancels a queued condition on that name at the same open, even if the submitted target for that name did not change.
- B07: Use all held prices from the same open. Book due funding and check maintenance before new fills. Recompute after costs. A move over the gross cap can only reduce existing gross risk. No same-open maintenance breach may be traded through.
- B08: Keep the whole shuffled bundle. Missing marks or no common required open make the fixed week invalid. Do not change the draw, resample it, or replace the week.
- B09: Seal the registered calendar, exact platform model IDs and cutoff bounds, cost and runner identity, fixture hashes and designated scout. The immutable serving builds are UNKNOWN. The judged path uses exactly 1,000 twins, seed 1 and the 90th percentile. An extension needs a sealed 3/3 gate and a recorded attempt before its launch. Preview results cannot pass.
- S01: Count exposure through gaps; book due funding without skipping a wake boundary. The complete made-up book matches TM06 in the gap fixture.
- S02: A legacy session keeps its ID, including IDs that start with `TM07-`. The guarded desk route is separate.
- S03: Stops and conditions validate only against visible marks in the book, a note, the solo packet, or a metered bars lookup.
- S04: A lookup request ID is scoped to its wake. Retrying the same request returns the same saved reply, and changing it requires a new ID.
- S05: Record each twin's immediate and standing fills and turnover. Compute lift from the cent-rounded endpoints used for wins. Missing token fields stay UNKNOWN and incomplete receipts are shown separately.

The first Opus audit did not produce a formal report. The delivered repros were handled: Opus R1 pick-reply invariance (Sol B02 and a protocol fixture), R2 saved targets above cap after a standing fill (separate guard), R3 missing twin open (Sol B08), R4 bearer reused across arms (Sol B05), and R5 two fills at one open (Sol B06). These are script IDs, not a review verdict.

### Opr re-audit at `651f4a9`

- R1: Superseded by third-pass M2 / P3-B2. The then-current fix used a dedicated atomic allocation based on after-cost equity.
- R2: The later common-open liquidation is superseded by M3 / P3-B4, and resting order details are superseded by M6 and M7. A bar-close observation at the next open's timestamp still keeps the attribution of the position it actually exited.
- R3: Register one canonical study root. Finalizing the designated neutral export binds its hash once in the root ledger. B/C creation, scoring and each standalone gate check that binding; a different stream under the same ID is refused.
- R4: Added the [operator-run isolation probe](TM07_WORKER_PROBE.md), synthetic checks, and a release-bound receipt. The real launcher and request wrapper must still pass the operator's dry-run probes. No deployed execution is claimed.
- R5: Typed price and bar rows have allow-listed fields. Completed bars, the observed quote stamp and the nested funding stamp are checked before the rows can become visible or cited.
- R6: An initially flat no-op advances even when the hour has no opens. A requested move still needs a complete open.
- N1: TM07 and legacy fixture verification is synthetic. Legacy trading and scoring still use their original paths.
- N2: A real runner, model context and usable real vendor coverage remain UNKNOWN. Nothing in this review authorizes a real run.

### Sol re-audit at `651f4a9`

- R01 (B06): Fresh entries and updated exits cannot close in the install minute. Tested both an already crossed entry and an exit update held until a delayed common open; updated the boss brief.
- R02 (B07): Superseded by third-pass M3 / P3-B4. The then-current policy observed a breach and required a subsequent common open.
- R03: Superseded by third-pass M2 / P3-B2. The then-current policy used the same after-cost allocation as Opr R1.
- R04 (B04): Signed attention must describe its own completed period and agree with the envelope, proof and independent confirmation clocks. Reject unknown typed payload fields; count dropped rows by kind in the operator journal, not in the model packet.
- R05 (B09): Rebuild effective cost parameters from the unchanged TM06 thresholds and compare them to the registered hash and each fixture. Register the independently derived source settlement digest and check symbol and BTC-opening coverage. Reject wrong half-spreads, maintenance and future or mutated settlement stamps. Settle using the exact second and the quantity then held, using the latest mark available at that instant. An interval with no observed settlement uses the configured conservative fallback.
- R06 (B05): See Opr R4. Run the rehearsal with the real launcher and deliberate scorer, cross-role, filesystem, egress and fresh-context checks. The production boundary is still UNKNOWN until the operator verifies and seals that actual deployment.
- R07: Count completed crossing detections separately from standing fills, even when an order was triggered but refused.
- N01: The 96 legacy slow/fast checks were rerun after each fix. Test changes to TM07's protective-observation timestamps do not change the legacy engine.
- N02: The calendar, cent-tie rule and 16/20 mark are unchanged. No new claim about the independence of weeks.
- N03: Only invented data and mock deployment tests were used. No real tape, model call, live probe, ledger or config write, or main write.
