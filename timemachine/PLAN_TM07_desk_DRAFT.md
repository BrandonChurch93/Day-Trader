# Time machine plan 07 draft: the desk

Does a desk with cheap scouts, a bigger boss and a plain order program beat the same boss alone? This is a pretend replay, not a live trade. Dates, arms, costs and marks below are fixed before any TM07 run. No real tape or model was run to build this branch.

## Arms and input

- Use TM06 Part S. Use the same hourly UTC wakes, five tradable coins per week, and 20-coin watch list. Start each week at the same cash amount. Match the fixed spreads, fee ladder, funding, min change, maintenance and exit rules. Judge at 1x and 12 bp per side. Show 1 and 25 bp and 2x and 3x for scale. Coinbase spot minute bars stand in for futures prices.
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
- Keep both TM06 one-model marks. Chain the net weekly gains. Beat the five coins held equally and the 90th percentile of the 1,000 shuffled timing twins. Shuffle full answers within each week. Keep exit distances and condition distances relative to the new wake price. Preserve time to live. A shuffled keep with no active match does nothing. Show twin fills and turnover. Do not claim the realized trigger count stays fixed.
- The one-sided per-claim cap is 1.25%. There are four claims, B/A and C/A for each of two bosses. The limit is 16 wins out of all 20 weeks, including the three used for the gate. The table uses the unconditional binomial tail. Requiring the screen gate can only make the combined rule stricter under that null. Display the weekly lift and the two TM06 marks separately. C/B is descriptive only.

| Weeks | Wins | One-sided fair-coin tail |
|---:|---:|---:|
| 3 | 3 | 12.5000% |
| 4 | 4 | 6.2500% |
| 20 | 15 | 2.0695% |
| 20 | 16 | 0.5909% |

MEASURED by exact arithmetic, not market results. The test assumes independent weeks. Timing, season and common headlines can make that assumption weak. Report the weekly pattern, not only the p-value. Forty weeks of post-cutoff past do not exist. Forward weeks from the live recorder can be proposed later under a new plan, not appended after seeing results.

## Orders and evidence

- Weights and optional protective exits are the existing TM06 answers. In C the boss may also ask for a weight after a strict above/below signal. Use a price or a percent from the last finished mark. Use one to six hours and at most two active orders. Cancel a condition not kept at the next wake. A kept condition keeps its first price, expiry and source IDs.
- Check the high or low only once the minute has ended. If touched, wait for the first recorded open with a price for the order and every held coin, strictly before expiry. A flat coin is still watched. Each immediate move waits for a common open for all held and affected coins, in all arms. A missing common open freezes that move, not the simulated clock. For the judged set, preflight coverage before workers start. A required twin that cannot replay the full move makes that fixed week invalid. Never replace it.
- Before new fills in each minute, apply the same full-book maintenance rule in A, B and C. Use that complete minute bar's low for every long, high for every short, and the holding's last bar close if that coin has no bar. If stressed equity falls below maintenance, no new order fills in that minute. Close the whole book at those adverse marks with fees and penalty, record the proxy at bar close, and floor the resulting equity at zero. Do not wait for a better open. This deliberately assumes all adverse extremes happened together and may be materially worse than real liquidation. Real-venue accuracy is UNKNOWN.
- Settle each observed funding rate at its own recorded stamp. A completed-bar protective hit is a resting-order proxy at its level and is reported as observed at bar close, not as an open fill. A fresh or updated stop or target first goes live on the next recorded minute bar, not at the open where it is installed. If that next bar opens through the level, use that open.
- Immediate fills come before triggered orders. Count at most one physical open fill per coin. Recheck actual gross after costs; if the book has drifted over the cap, accept only a move that demonstrably reduces it. Missing simultaneous marks never authorize a new fill. Size the equal-held basket and BTC holds together from after-cost equity so a 1x yardstick is fully invested without exceeding 1x or leaving a coin out.
- Role checks and wake keys guard all requests. Each recorded trade links to its cited evidence where available. Journal the wake, condition transitions, observable trigger, open, fee and spread. A note link says what the boss cited, not what made the gain. Save genuine provider token usage for each role and call. The cost of the reusable neutral stream is charged once in study totals and once per arm in standalone comparisons. No token telemetry means UNKNOWN.
- Scouts can miss the one event that matters. An absence can mean tape failure. A small historical sample can reward simple drift. Bar opens are not executable quotes. A move may slip, arrive late or fill only in part. Show a delayed-open check and a higher fee check. Neither can rescue a failed main mark.

## Build and limits

- `desk.py`: frozen packets, role checks, note storage, a short lookup list, decisions and usage. `desk_orders.py`: arm and cancel, scan bars, queue and fill. `score_tm07.py`: replay checks, twins, paired marks and the extension calendar. `test_tm07.py`: made-up bars and records only. `TRADER_BRIEF_DESK.md`: role and answer rules.
- Separate small changes wire the guarded server, weights dispatch and replay helpers. Keep legacy paths when there is no desk. Prove parity with fixture books, records, fills and final value. No recorder, ledger or config change belongs in the build.

## Review answers

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

- R1: Buy-and-hold uses a dedicated atomic allocation. Every leg gets its declared share of after-cost equity. BTC long and short are explicit. A missing opening or final mark invalidates the benchmark rather than filling part or holding cash. The rising and falling toy yardsticks match independent fee, spread and funding arithmetic in either symbol order. This restores the original full-basket yardstick, not the old slightly over-1x notional.
- R2: New or updated protections cannot use the install bar. The next bar can exit at its own open. A previously live intrabar protective hit carries a distinct intrabar phase and a bar-close observation stamp; maintenance liquidation uses a subsequent common open. A bar-close observation at the next open's timestamp keeps the attribution of the position it actually exited.
- R3: Register one canonical study root. Finalizing the designated neutral export binds its hash once in the root ledger. B/C creation, scoring and each standalone gate check that binding; a different stream under the same ID is refused.
- R4: Added the [operator-run isolation probe](TM07_WORKER_PROBE.md), synthetic checks, and a release-bound receipt. The real launcher and request wrapper must still pass the operator's dry-run probes. No deployed execution is claimed.
- R5: Typed price and bar rows have allow-listed fields. Completed bars, the observed quote stamp and the nested funding stamp are checked before the rows can become visible or cited.
- R6: An initially flat no-op advances even when the hour has no opens. A requested move still needs a complete open.
- N1: TM07 and legacy fixture verification is synthetic. Legacy trading and scoring still use their original paths.
- N2: A real runner, model context and usable real vendor coverage remain UNKNOWN. Nothing in this review authorizes a real run.

### Sol re-audit at `651f4a9`

- R01 (B06): Fresh entries and updated exits cannot close in the install minute. Tested both an already crossed entry and an exit update held until a delayed common open; updated the boss brief.
- R02 (B07): A completed extreme can flag a breach but cannot price anyone's liquidation. Tested the late A-high case: the earlier B fill is unchanged, and B liquidates only at the subsequent common open, at that open's B price. If a prior bar's protection is observed at the following open's timestamp, journal attribution orders the observation before that open.
- R03: The all-name equal hold and both BTC directions use the same complete after-cost allocation described under Opr R1. The paired judge no longer compares against a partial basket.
- R04 (B04): Signed attention must describe its own completed period and agree with the envelope, proof and independent confirmation clocks. Reject unknown typed payload fields; count dropped rows by kind in the operator journal, not in the model packet.
- R05 (B09): Rebuild effective cost parameters from the unchanged TM06 thresholds and compare them to the registered hash and each fixture. Register the independently derived source settlement digest and check symbol and BTC-opening coverage. Reject wrong half-spreads, maintenance and future or mutated settlement stamps. Settle using the exact second and the quantity then held, using the latest mark available at that instant. An interval with no observed settlement uses the configured conservative fallback.
- R06 (B05): See Opr R4. Run the rehearsal with the real launcher and deliberate scorer, cross-role, filesystem, egress and fresh-context checks. The production boundary is still UNKNOWN until the operator verifies and seals that actual deployment.
- R07: Count completed crossing detections separately from standing fills, even when an order was triggered but refused.
- N01: The 96 legacy slow/fast checks were rerun after each fix. Test changes to TM07's protective-observation timestamps do not change the legacy engine.
- N02: The calendar, cent-tie rule and 16/20 mark are unchanged. No new claim about the independence of weeks.
- N03: Only invented data and mock deployment tests were used. No real tape, model call, live probe, ledger or config write, or main write.
