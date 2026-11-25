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
- Check the high or low only once the minute has ended. If touched, fill at the next recorded open before expiry. A flat coin is still checked. An immediate change takes priority over a queued fill on that coin. A protective exit or maintenance can cancel a condition. New conditions cannot read a bar from before acceptance. Reject a conditional-path wake if an immediate move needs asynchronous opens. That gap is an invalid pair, not a guessed fill.
- Role checks and wake keys guard all requests. Each recorded trade links to its cited evidence where available. Journal the wake, condition transitions, observable trigger, open, fee and spread. A note link says what the boss cited, not what made the gain. Save genuine provider token usage for each role and call. The cost of the reusable neutral stream is charged once in study totals and once per arm in standalone comparisons. No token telemetry means UNKNOWN.
- Scouts can miss the one event that matters. An absence can mean tape failure. A small historical sample can reward simple drift. Bar opens are not executable quotes. A move may slip, arrive late or fill only in part. Show a delayed-open check and a higher fee check. Neither can rescue a failed main mark.

## Build and limits

- `desk.py`: frozen packets, role checks, note storage, a short lookup list, decisions and usage. `desk_orders.py`: arm and cancel, scan bars, queue and fill. `score_tm07.py`: replay checks, twins, paired marks and the extension calendar. `test_tm07.py`: made-up bars and records only. `TRADER_BRIEF_DESK.md`: role and answer rules.
- Separate small changes wire the guarded server, weights dispatch and replay helpers. Keep legacy paths when there is no desk. Prove parity with fixture books, records, fills and final value. No recorder, ledger or config change belongs in the build.
