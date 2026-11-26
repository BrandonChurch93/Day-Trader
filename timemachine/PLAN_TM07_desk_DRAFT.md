# Time machine plan 07 draft: the desk

Does a desk with cheap scouts, a bigger boss and a plain order program beat the same boss alone? This is a pretend replay, not a live trade. Dates, arms, costs and marks below are fixed before any TM07 run. No real tape or model was run to build this branch.

## Arms and input

- Use TM06 Part S. Use the same hourly UTC wakes, five tradable coins per week, and 20-coin watch list. Start each week at the same cash amount. Use the registered TM06 costs, min change and maintenance thresholds, with the TM07 order and liquidation rules below. Judge at 1x and 12 bp per side. Show 1 and 25 bp and 2x and 3x for scale. Coinbase spot minute bars stand in for futures prices.
- Bosses: `claude_fable_5_2` and `claude_opus_5_5`. A is a fresh solo boss. It sees the full raw packet. B is the same boss with scouts. C is the same boss with scouts and standing orders. B and C see the notes, their own book and the clock. All arms have the same three lookups per wake. The TM06 archive is shown only. It is never the judged baseline.
- Scouts: two `gemini_neon` roles. Both read the same raw packet on all 20 coins at every wake. One looks for price and volume evidence. The other looks for news and attention evidence. Neither sees a book or an answer. Each can send two short notes with visible evidence IDs and no advice. Plain code merges to at most four and adds the visible price and volume row. The notes carry the date, coin, raw evidence and a short description.
- Run the neutral scouts once per week. Seal their note stream and copy it independently into each desk arm with its hash. Neither desk can edit or see a sibling's notes, account, picks, files or results. Model workers need separate sandboxes, scoped role tokens and no outbound tools or shared disk. The scorer is the only reader of different arms after replies are sealed. At the TM06 handoff boundary use only same-arm notes and state.
- No wider source is added for the screen. Only use the existing tape. Use vendor rows only with rights and an original-version proof. They must have been public by that wake. Use independently confirmed news or a primary record, not reposts of one report. If the existing tape cannot prove a row's version, omit it. Missing attention is UNKNOWN, not zero. Label an available-feed comparison plainly if proof is thin.
- UNKNOWN: how many existing news and attention rows qualify. A dated original accession, a versioned news archive or a finalized chain log could supply future point-in-time data with permission. Current WordPress, social search, historical counters and sampled trend results do not prove old versions. No such feed is imported in this branch.

## Weeks

Months refer to UTC. Ends are excluded. Same five coins as TM06 on the screen dates.

| Monday start | Five coins | Use |
|---|---|---|
| 2026-05-11 | ENA, NEAR, ONDO, SUI, ZEC | Diagnostic only |
| 2026-07-20 | LINK, LTC, ONDO, PEPE, ZEC | Screen |
| 2026-08-31 | BNB, HYPE, LINK, SOL, ZEC | Screen |
| 2026-10-05 | AAVE, ADA, BNB, HBAR, XLM | Screen |

STATED by Anthropic: both [Fable 5.2](https://platform.claude.com/docs/en/models/fable-5-2/overview.md) and [Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview.md) have a June 2026 training cutoff. July 1 is the earliest scored day on that evidence. Check the exact build and scout knowledge line too. Use the later line. An unresolved model or a later cutoff blocks the affected weeks. Do not move the dates.

These are the 17 fixed Monday starts for extension. The last week ends November 23. Use the TM06 rising-five selector on the two completed Sunday closes before each start. Apply its symbol tie rule. Freeze the selected coins and hashes without reading the extension answers or returns.

| Month | Extension Monday starts in 2026 |
|---|---|
| July | 06, 13, 27 |
| August | 03, 10, 17, 24 |
| September | 07, 14, 21, 28 |
| October | 12, 19, 26 |
| November | 02, 09, 16 |

## Marks

- Open the extension only for a boss and desk arm that beats fresh A to the cent in all three screen weeks. A tie is not a win. A missing or invalid week is not a win. Do not replace a week. An incomplete comparison cannot pass. Different bosses on the same week are not two independent weeks.
- Keep both TM06 one-model marks. Chain the net weekly gains. Beat the five coins held equally and the 90th percentile of the 1,000 shuffled timing twins. Compute equal hold and BTC hold with the unchanged pre-TM07 replay on separately frozen legacy inputs. Do not apply the TM07 target sizing rule to those yardsticks. Run optional displays separately and report unsupported cells as `not computed`; they cannot invalidate the judged week. Shuffle full answers within each week. Keep exit distances and condition distances relative to the new wake price. Preserve time to live. A shuffled keep with no active match does nothing. Show twin fills and turnover. Do not claim the realized trigger count stays fixed.
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
- Check the high or low only once the minute has ended. If touched, wait for the first recorded open with a price for the order and every held coin, strictly before expiry. A flat coin is still watched. Each immediate move waits for a common open for all held and affected coins, in all arms. A missing common open freezes that move, not the simulated clock. For the judged set, preflight coverage before workers start. A required twin that cannot replay the full move makes that fixed week invalid. Never replace it.
- Before new fills in each minute, apply the same full-book maintenance rule in A, B and C. Use that complete minute bar's low for every long, high for every short, and the holding's last bar close if that coin has no bar. If stressed equity falls below maintenance, no new order fills in that minute. Close the whole book at those adverse marks with fees and penalty, record the proxy at bar close, and floor the resulting equity at zero. Do not wait for a better open. This deliberately assumes all adverse extremes happened together and may be materially worse than real liquidation. Real-venue accuracy is UNKNOWN.
- Settle each observed funding rate at its recorded stamp on the quantity then held in the simulation. At a shared boundary, account for the previous bar's close events, settle funding using the pre-open-fill quantity, then process the new bar. Mid-minute funding precedes a protective exit inferred from the complete bar. That exit is accounted at bar close, even if a real touch could have occurred earlier. The true order of funding and touch is UNKNOWN. A fresh or updated stop or target first goes live on the next recorded bar for its coin. For a completed bar that could hit both levels, take the stop. Use the open only if it is already through the selected level.
- Immediate fills come before triggered entries. A real immediate fill can cancel a conflicting older condition at that open. Count at most one physical open fill per coin. Scale all legs of a boss target together if needed to fit within the cap after the costs of the actual quantity changes. Recheck actual gross after costs; if the book has drifted over the cap, accept only a move that demonstrably reduces it. Missing simultaneous marks never authorize a new immediate or standing entry; the maintenance check still uses all holdings.
- Role checks and wake keys guard all requests. Each recorded trade links to its cited evidence where available. Journal the wake, condition transitions, observable trigger, open, fee and spread. A note link says what the boss cited, not what made the gain. Save genuine provider token usage for each role and call. The cost of the reusable neutral stream is charged once in study totals and once per arm in standalone comparisons. No token telemetry means UNKNOWN.
- Walk nested evidence and proof fields before any packet or lookup can use them. Reject the entire row for a future or unparseable clock value; keep the full fraction when checking zoned ISO stamps. Typed quote rows require their own observation stamp. A bars lookup cannot manufacture a quote from an unstamped mark. Count drops by kind in the operator journal only.
- Scouts can miss the one event that matters. An absence can mean tape failure. A small historical sample can reward simple drift. Bar opens are not executable quotes. A move may slip, arrive late or fill only in part. Show a delayed-open check and a higher fee check. Neither can rescue a failed main mark.

## Build and limits

- `desk.py`: frozen packets, role checks, note storage, a short lookup list, decisions and usage. `desk_orders.py`: arm and cancel, scan bars, queue and fill. `score_tm07.py`: replay checks, twins, paired marks and the extension calendar. `test_tm07.py`: made-up bars and records only. `TRADER_BRIEF_DESK.md`: role and answer rules.
- Separate small changes wire the guarded server, weights dispatch and replay helpers. Keep legacy paths when there is no desk. Prove parity with fixture books, records, fills and final value. No recorder, ledger or config change belongs in the build.
- The [worker probe](TM07_WORKER_PROBE.md) is a bounded rehearsal check, not proof of deployed isolation. The operator must separately review the actual deployment policy and wrapper and run the real-launcher rehearsal before approving any session.

## Review answers

### Third pass at `be0a560`

- M1 / P3-B1: Scale an exact-cap target as a basket on the common open, net of actual position delta costs. MEASURED: +1, −1 and .5/.5 enter fully to just under the cap; the fixtures cover an existing position, a ready standing entry and a genuine refusal. This is not a change to legacy sizing.
- M2 / P3-B2: Call unchanged pre-TM07 `P.run_perp` on frozen legacy hold inputs for the equal hold and BTC holds. MEASURED: five-name equal hold and BTC long and short match to the cent on the falling, flat and rising toy tape. This supersedes the costed yardstick in Opr R1 and Sol R03.
- M3 / P3-B4: Before new fills, stress all held coins together. Use each long's low and each short's high; substitute the last close for a missing bar. If equity is under maintenance, liquidate the entire book at those marks with the penalty, floor at zero and block that minute's new fills. MEASURED: jointly adverse shorts close before the recovering open; with the second coin's bar missing, both holdings close before the ordinary stop. This replaces the later-open liquidation in Sol R02 and Opr R2.
- M4 / P3-S2: Main replay, its required benchmarks and twins are judged separately. A failed display cell, optional twin or delayed replay is `not computed`, not a reason to invalidate main. MEASURED: independently unsupported 2x and 3x display cells leave the $1,000 idle main available.
- M5 / P3-B3: Recurse through evidence and proof fields; reject the row for future or unparseable dates. Quote rows and bars lookups require an observation stamp. MEASURED: signed future nested news and proof metadata, a malformed origin stamp, a funding stamp 0.900 seconds after wake and an unstamped quote are excluded. At-wake zero fractions pass; a fraction positive only past six digits still fails. Verify packet, citation, lookup and the operator drop tally. This extends Sol R04 and Opr R5; real vendor coverage is UNKNOWN.
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
- B09: Seal the registered calendar, exact model builds, cost and runner identity, fixture hashes and designated scout. The judged path uses exactly 1,000 twins, seed 1 and the 90th percentile. An extension needs a sealed 3/3 gate and a recorded attempt before its launch. Preview results cannot pass.
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
