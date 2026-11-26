# TM07 registration package (ledger 198)

STATED. Draft for review, written 2026-11-26. It fixes every week, coin, arm, prompt, cost and mark before any TM07 session. No trader, worker, model or listener has been started. No arm, twin, yardstick or rule arm has been replayed, and no return has been computed on the snapshot. The package becomes the frozen registration only when the lead approves it and the operator seals it (see "What the seal still needs").

## What is pinned

- Engine and plan: commit `058a54320c2bc13043761633d828c1b2a78fbb82` on branch `tm07` (checkout `dt-tm07`, fast-forwarded from `f37e431` through `bdc5f6a` and `4408b7c`, which auditor b cleared; `058a543` only tightens the sudo review after auditor b's notes; not merged into work, which stays the lead's call). It carries the lead's 2026-11-26 rulings: the t-based weekly mark with no screen gate, raw-copy denial in all 20 weeks, and the soft, audited sudo boundary. It replaces the earlier pin `bdc5f6a722a0e78036d50c3dd08c964c97703d6f`. `desk_orders.py`, `perp.py` and `tm06.py` are byte-identical to that pin. The files used, by SHA-256 at the new commit:

| File at `058a543` | SHA-256 |
|---|---|
| `timemachine/PLAN_TM07_desk_DRAFT.md` | `0581ff2f6dfb3cd59d8c32b31ad539bc389157682c9254dc84f09db89d36f1ab` |
| `timemachine/desk.py` | `bbbde294cbee2676b4eec4781bf2ff6f07f16a0b8f3ac8aa15ab9eceddfba236` |
| `timemachine/desk_orders.py` | `fcbbf8cd8946dd1921ea8011f967928e6611e0b4c502f1d7b62b9250f5c8c3d8` |
| `timemachine/score_tm07.py` | `058f241ff71bf04b483ed211212bbcab3086286b2d6eed8a490d67e66924a0df` |
| `timemachine/server.py` | `6dbcfe25f37a0d6d174f49bc1531b41394906ce27ae8732948b2adfdeeb3f3e3` |
| `timemachine/perp.py` | `1a98dc755d358394ac88512cbde6cff49c1e94ff398c899ac0e7089d2b1cf2c1` |
| `timemachine/tm06.py` | `65e5561e92b72bd7b6042c5047a2ec5e437a4e76154094d91c0d09834cba1613` |
| `timemachine/TRADER_BRIEF_DESK.md` | `2467d44c90e82ca858cc99dc0fb06a348736dc9c2fc409c3484c3bb8e7f8a20f` |
| `timemachine/TM07_WORKER_PROBE.md` | `75074f0aae86b7a992f060208601d1d581cabc82778f9f00590323218291d3bd` |
| `timemachine/tm07_isolation_probe.py` | `6d3ddfadb382108528c4edec7fa85ea402fffb0e63f6850777e1b4ea7f2b654f` |
| `timemachine/test_tm07.py` | `9e8d7b89d586c2dd74bb1f00174b497da6039cf7ff49e7636a0e6094353b9f2b` |

- Price snapshot, MEASURED: `rig/tm07_custody/tm07_coinbase_all21_20261126.sqlite`, SHA-256 `6346be0d4a10976a3531f2f2c70dd99132bfad331c47564366e0e6f4c2e486eb`, mode 0400, 21 symbols (the 20 watch coins and BTC), 4,115,728 bar rows, 74,445 funding rows. The bars are Coinbase Exchange spot one-minute and daily candles. Funding comes from the Kraken `PF_` series, as in TM06. A second fetch cannot rebuild it, so the hash is the record.
- Week table: `timemachine/TM07_REGISTRATION_weeks.json`, built by `tools/build_tm07_registration.py` from the snapshot and the engine's own `score_tm07.week_selection` and `select_five`. It holds names, counts, reasons and digests only.
- Cost profile hash (`score_tm07.canonical_cost_hash`, the unchanged TM06 thresholds): `d81f75815df38c114eee30b54fdb433e03be17009f57395471db5ea74fca3d8d`. Screen roster hash (`tm07_screen` config): `6dcf0169720db8ce85f8179dafaeae56fdf33dc3948f27d649850eebee311432`.

## The 20 scored weeks

MEASURED from the snapshot by the registered rule, with no return read. The rule keeps a TM06 name only if it was first seen before Monday 00:00 UTC and has recorded bars in at least `tm07_screen.min_minute_coverage_pct` (90%) of the week's 10,080 minutes. Each vacancy, and all five names of an extension week, is filled from the remaining eligible watch coins. They are ranked by the ratio of the two prior completed Sunday daily closes, largest rise first, with the engine's symbol tie rule. Every week has all 20 Sunday pairs, and no week is blocked. Prices and ranking ratios stayed in memory. Mondays are UTC; each week runs Monday 00:00 to the next Monday 00:00, end excluded, with 168 hourly wakes.

| Monday start | Use | Five coins | Change from the TM06 basket | Watch coins at 90% minute coverage | Listed |
|---|---|---|---|---:|---:|
| 2026-05-11 | Diagnostic only | LINK, ONDO, SOL, SUI, ZEC | ENA, NEAR out on minute coverage; LINK, SOL in by rank | 12 of 20 | 18 of 20 |
| 2026-07-06 | Extension | BCH, HYPE, SOL, XLM, ZEC | no TM06 basket; all five by rank | 13 of 20 | 20 of 20 |
| 2026-07-13 | Extension | LINK, LTC, ONDO, SUI, ZEC | no TM06 basket; all five by rank | 10 of 20 | 20 of 20 |
| 2026-07-20 | Screen | LINK, LTC, ONDO, XRP, ZEC | PEPE out on minute coverage; XRP in by rank | 9 of 20 | 20 of 20 |
| 2026-07-27 | Extension | DOGE, LINK, LTC, ONDO, XRP | no TM06 basket; all five by rank | 10 of 20 | 20 of 20 |
| 2026-08-03 | Extension | ADA, SOL, XLM, XRP, ZEC | no TM06 basket; all five by rank | 8 of 20 | 20 of 20 |
| 2026-08-10 | Extension | ADA, AVAX, LTC, SOL, ZEC | no TM06 basket; all five by rank | 9 of 20 | 20 of 20 |
| 2026-08-17 | Extension | AVAX, DOGE, HYPE, LINK, NEAR | no TM06 basket; all five by rank | 16 of 20 | 20 of 20 |
| 2026-08-24 | Extension | DOGE, ENA, HYPE, XRP, ZEC | no TM06 basket; all five by rank | 15 of 20 | 20 of 20 |
| 2026-08-31 | Screen | AVAX, HYPE, LINK, SOL, ZEC | BNB out on minute coverage; AVAX in by rank | 16 of 20 | 20 of 20 |
| 2026-09-07 | Extension | ADA, DOT, LINK, NEAR, ZEC | no TM06 basket; all five by rank | 14 of 20 | 20 of 20 |
| 2026-09-14 | Extension | DOT, LTC, NEAR, XLM, XRP | no TM06 basket; all five by rank | 17 of 20 | 20 of 20 |
| 2026-09-21 | Extension | AVAX, ENA, NEAR, SUI, ZEC | no TM06 basket; all five by rank | 18 of 20 | 20 of 20 |
| 2026-09-28 | Extension | BCH, ENA, NEAR, ONDO, SUI | no TM06 basket; all five by rank | 18 of 20 | 20 of 20 |
| 2026-10-05 | Screen | ADA, AVAX, HBAR, LINK, XLM | AAVE, BNB out on minute coverage; AVAX, LINK in by rank | 16 of 20 | 20 of 20 |
| 2026-10-12 | Extension | ADA, AVAX, ENA, NEAR, ONDO | no TM06 basket; all five by rank | 15 of 20 | 20 of 20 |
| 2026-10-19 | Extension | DOGE, HBAR, LTC, SOL, XRP | no TM06 basket; all five by rank | 14 of 20 | 20 of 20 |
| 2026-10-26 | Extension | ENA, HYPE, SOL, XRP, ZEC | no TM06 basket; all five by rank | 14 of 20 | 20 of 20 |
| 2026-11-02 | Extension | HYPE, LINK, ONDO, XLM, ZEC | no TM06 basket; all five by rank | 13 of 20 | 20 of 20 |
| 2026-11-09 | Extension | DOGE, HBAR, LINK, SOL, ZEC | no TM06 basket; all five by rank | 16 of 20 | 20 of 20 |
| 2026-11-16 | Extension | AVAX, HBAR, HYPE, LTC, XLM | no TM06 basket; all five by rank | 16 of 20 | 20 of 20 |

MEASURED, and accepted by the lead on 2026-11-26. The 90% minute rule, written before any of these bars were fetched, removes four of the 15 TM06 screen names: PEPE in July, BNB in August, and AAVE and BNB in October. The lead accepted the rule as written and the replaced names by rank (XRP for PEPE on 2026-07-20, AVAX for BNB on 2026-08-31, AVAX and LINK for AAVE and BNB on 2026-10-05). So the three TM07 screen baskets differ from the TM06 swing baskets for the same weeks. TM07 screen results are not a rerun of the TM06 swing weeks and must not be read as one. Coinbase spot has no candle for a minute without a trade, which is why only 8 to 18 of the 20 watch coins reach 90% in a given week. The rule was not changed after the coverage counts were seen.

The scored set is the three screen weeks plus the 17 extension weeks: 20 weeks. May 11 is diagnostic only and is never scored.

## Arms and prompts

- Bosses: `claude_fable_5_2` and `claude_opus_5_5`. Scouts: two `gemini_neon` roles (price and news). The news role has no input, because TM07 is price-only.
- Arms for each boss and week: A (fresh solo boss, sees the full raw packet), B (boss with the scouts' notes, its own book and the clock) and C (B plus up to two standing orders). Each arm gets three lookups per wake. That makes 2 bosses × 3 arms × 20 weeks = 120 boss sessions.
- The scouts run once per week, as one neutral stream. The stream is sealed and copied by hash into each B and C arm of that week: 20 scout streams, each with 2 roles.
- Order rules, fills, maintenance, funding and the min-change floor are as in the plan at `058a543` ("Orders and evidence", unchanged from `bdc5f6a`). The program scales every vector to 1x gross after costs (`tm06_plan.swing_max_gross`).
- Prompt for every role: `timemachine/TRADER_BRIEF_DESK.md` at `058a543`, SHA-256 above. The only change from `bdc5f6a` is one paragraph: no sudo, no price file, no web price lookup, keep a list of commands and addresses, and any of these voids the week for that arm. It goes with the launch text below, in which only the placeholders change. A worker gets this text and its own bearer through the operator, nothing else. At a handoff, the next agent gets the same text and only the server's handoff packet.

```text
You are the {ROLE} for pretend session {SESSION_ID}, arm {ARM}, a replay of one past week. Model: {MODEL}. Pretend money only; there is no account or broker.
Read the desk brief below first and follow it. The time in each packet is the time now.
The desk is at http://127.0.0.1:{PORT}. Send your bearer, which the operator gave you privately, in the Authorization header. Never write it to a file or a message.
Use only the packets, your three lookups per wake (boss only) and, if you are a later agent, the handoff text the desk gives you.
Do not use sudo, the web, any price file, any other session or any other worker's output. Work only in {SCRATCH_DIR}.
Answer every wake until the desk says done, then stop.
{DESK_BRIEF}
```

## Fixed-rule arms, shown only

R1, R2 and R3 are as in the plan at `058a543` (unchanged from `bdc5f6a`) ("Fixed-rule arms (no AI)"). They are shown only, with no claims and no marks. The scorer computes them only after the registered sessions of that week are sealed. Their judged test is the forward card E06 (`practice/traders/E06_forward_hot_coin_rules.md`), which has been running since its freeze `e128e7d`.

## Costs, fixed now

- Main: fee `tm06_plan.main_fee_bps` (12 bp) per side. Each coin also pays its half spread from `tm_perp_half_spread_bps`, falling back to `tm_crypto_half_spread_bps_by_coin`.
- Funding: Kraken `PF_` settlements at their recorded stamps, with the configured fallback where none is observed. Maintenance and liquidation penalty are as in `perp.p_params`, and the min-change floor is the TM06 value. All of these are pinned by the cost profile hash above.
- Leverage: 1x for every judged line.
- Shown only: the same replay at 25 and 40 bp per side, at 2x and 3x, and with a delayed-open check. None of these can rescue a failed main result.

## Marks, fixed now

For each boss, the comparisons B against A and C against A make four claims.

- Ruling (lead, 2026-11-26, before the seal and before any TM07 return): the weekly mark below replaces the earlier 3 of 3 screen gate plus 16 of 20 mark. The screen gate is removed from the claim. All 20 scored weeks run for every arm, whatever happens in the first three. The two TM06 one-model marks below are unchanged.
- Weekly mark, per claim, on the 20 weekly net differences (arm minus fresh A, 1x, main fee): a one-sided paired t of at least 2.43, at least 12 of 20 winning weeks, and a positive mean after dropping the best week. A tie, a missing week or an invalid week is not a winning week. The one-sided per-claim cap is 1.25%. The 2.43 cutoff was checked by simulation (see "Power of the registered weekly mark") and did not need raising.
- Engine, MEASURED: `score_tm07.py` at `058a543` scores exactly this mark (`weekly_mark`, exact integer arithmetic on whole-cent weekly differences; the start balance is the same each week, so t, wins and the sign of the mean are the same as on percentage points). The 3/3 gate, its seal and launch check are removed, all 20 weeks are scored for every arm, and the 16 of 20 count is a shown line only (`sign_mark_shown`). A missing or invalid (including voided) week leaves the comparison incomplete, and an incomplete comparison cannot pass. Boundary tests: t exactly 2.43 passes and one cent less fails; 11 wins fails and 12 passes; a mean without the best week of exactly zero fails (such a set cannot also reach t 2.43, so that condition is checked on its own).
- Both TM06 one-model marks must also hold, on chained net weekly gains. The arm must beat the week's five coins held equally, and it must beat the 90th percentile of 1,000 shuffled timing twins (seed 1).
- C against B is descriptive only. Different bosses on the same week are not independent weeks.

## Synthetic power of the old mark (history)

History: this is the power of the replaced mark (3 of 3 screen gate plus 16 of 20), kept as written in draft e29d8cf. MEASURED by exact arithmetic (`tools/tm07_power.py`), with no market data. Weeks are taken as independent, with one weekly win chance. A claim passes its weekly part only if it wins all three screen weeks and at least 13 of the 17 extension weeks. The two chained-gain lines are extra conditions, so every figure below is an upper bound.

| Weekly win chance | Screen gate passes | Claim passes the weekly part |
|---:|---:|---:|
| 0.50 (null) | 12.50% | 0.31% |
| 0.60 | 21.60% | 2.72% |
| 0.70 | 34.30% | 13.33% |
| 0.75 | 42.19% | 24.21% |
| 0.80 | 51.20% | 38.82% |
| 0.85 | 61.41% | 55.35% |
| 0.90 | 72.90% | 71.29% |

Under the old mark, the chance that any of the four claims passed under the null was at most 1.22%. That family statement no longer applies: the registered error control is now 1.25% per claim, which bounds the four-claim family at 5% (see "Power of the registered weekly mark"). STATED: the design is powered only for an arm that wins about 85% or more of its weeks against fresh A; at 70% it fails most of the time. Under the queue screen ([doc 117](../docs/research/117_power_screen_before_data.md)), it is a weakly powered test of a modest edge. It can still catch a large one.

## Power of the alternative weekly mark (history)

History: this is the comparison table from draft c89760e that led to the ruling. MEASURED by simulation (`tools/tm07_power_alt.py`, fixed seed), using TM06 results for the noise only. No TM07 bar was read and no TM07 return was computed. The alternative mark the lead asked about, for comparison with 16 of 20: a one-sided paired t of at least 2 on the 20 weekly net differences (arm minus fresh A), at least 12 of 20 winning weeks, and a positive mean after dropping the best week. The registered mark is the 3 of 3 screen gate plus 16 of 20. The alternative is shown alone and with the same screen gate.

The noise is the TM06 week-to-week spread of weekly net differences between two arms on the same week. TM06 has no paired scout and no-scout arms, so every pair of the seven TM06 swing models on the same four weeks (including the May diagnostic week, at 1x and 12 bp) stands in for it. Each pair is centred on its own mean, so a steady gap between two models is not counted as noise. The normal rows use the pooled spread; the resampled rows draw the centred values themselves, which keeps their heavier tails. Weeks are independent draws and the chained-gain lines are not modelled, so these are upper bounds like the table above.

Noise: pooled standard deviation of the weekly net difference between two TM06 swing arms on the same week, 2.79 percentage points, from 84 centred pair-week values (7 arms, 21 pairs, 4 weeks, 1x, 12 bp). 100,000 simulated 20-week sets per cell, seed 1.

| Noise model | True weekly edge (pp) | Registered: 3 of 3 screen and 16 of 20 | Alternative: t at least 2, 12 of 20, mean without best week above 0 | Alternative with the 3 of 3 screen gate |
|---|---:|---:|---:|---:|
| normal | 0.0 (null) | 0.28% | 2.87% | 0.97% |
| normal | 0.5 | 1.55% | 13.03% | 4.69% |
| normal | 1.0 | 5.46% | 35.58% | 13.62% |
| normal | 2.0 | 27.73% | 87.68% | 41.37% |
| normal | 3.0 | 58.11% | 99.60% | 63.10% |
| resampled | 0.0 (null) | 0.21% | 2.77% | 0.90% |
| resampled | 0.5 | 2.52% | 13.77% | 5.29% |
| resampled | 1.0 | 13.90% | 37.70% | 17.81% |
| resampled | 2.0 | 45.59% | 87.46% | 51.11% |
| resampled | 3.0 | 72.81% | 99.48% | 74.00% |

STATED, reading the table:

- At the same true edge, the alternative mark alone has much more power than the registered mark, most clearly at 1 and 2 points.
- Its null false-pass rate alone is above the 1.25% one-sided per-claim cap. A t of 2 with 19 degrees of freedom is about a 3% one-sided test, and the two extra conditions remove little under the null. A cutoff of about 2.43 would match 1.25% on the t alone under normal noise (from the t distribution; not simulated here).
- With the 3 of 3 screen gate added, the null rate falls under the cap per claim, but most of the power gain is lost, because the gate alone fails often for a modest edge.
- The noise figure is a proxy. It comes from TM06 pairs of different models, not the same boss with and without scouts, and has only four weeks per pair. The true spread for TM07 arm pairs could be smaller or larger. UNKNOWN.
- At the time, the registered mark was unchanged by this section. The lead then ruled the change recorded under "Marks, fixed now".

## Power of the registered weekly mark

MEASURED by simulation with the same script, the same noise and the same draw count (`tools/tm07_power_alt.py`, fixed seeds). No TM07 bar was read and no TM07 return was computed. The noise figure is a proxy: it comes from TM06 pairs of different models on the same week, not from the same boss with and without scouts, and it rests on four weeks per pair. Weeks are independent draws and the two TM06 one-model marks are not modelled, so these are upper bounds.

t cutoff used: 2.43 (start 2.43, step 0.01, stop when the null rate per claim is at or under 1.25% under both noise models).

| Noise model | True weekly edge (pp) | Registered mark: t at least the cutoff, 12 of 20, mean without best week above 0, no screen gate |
|---|---:|---:|
| normal | 0.0 (null) | 1.20% |
| normal | 0.5 | 6.78% |
| normal | 1.0 | 23.00% |
| normal | 2.0 | 77.32% |
| normal | 3.0 | 98.73% |
| resampled | 0.0 (null) | 1.11% |
| resampled | 0.5 | 7.25% |
| resampled | 1.0 | 24.61% |
| resampled | 2.0 | 77.40% |
| resampled | 3.0 | 98.39% |

| Noise model | Null rate per claim | Any of four claims, simulated with shared A per boss | Any of four claims, union bound 1-(1-p)^4 |
|---|---:|---:|---:|
| normal | 1.20% | 4.65% | 4.73% |
| resampled | 1.11% | 4.47% | 4.37% |

STATED, reading the tables:

- The null false-pass rate per claim is at or under the 1.25% cap under both noise models at a cutoff of 2.43, so the cutoff was not raised. The normal-noise figure sits close to the cap; with 100,000 draws its simulation error is about 0.03 points.
- Error control (lead ruling 2026-11-26): the registered error control is 1.25% per claim, which bounds the four-claim family at 5%. The cutoff stays at 2.43. The simulated four-claim null rate is in the table above, under that bound. This replaces the old statement that the four-claim rate was at most 1.22%.
- Against the old mark, the new mark has much more power at every edge tested, because no screen gate can stop a claim after three weeks.

## Isolation design

What each role sees at wake k (hour t). It comes from `desk.py` at `058a543`:

| Role | Sees | Never sees |
|---|---|---|
| Scouts (price, news) | For each of the 20 watch coins: the latest completed close, its 1h and 24h change, volume row and last funding stamp; the last 24 hourly bars and the last 30 one-minute bars, each finished by t; the tradable five; the clock | Any book, note from the other scout, answer, fill or later bar |
| Boss, arm A | The same raw packet as the scouts, its own book at t (cash, equity, weights, exits, marks of held coins), live orders, lookups left | Scout notes, other arms, fills or bars after t |
| Boss, arms B and C | The merged scout notes for wake k (at most four, each rebuilt against admitted evidence, with the visible price row added), its own book, live orders, the clock | The raw packet beyond the cited rows, other arms, anything after t |
| Lookups (boss) | Up to three per wake, one tradable coin each: bars rows known by t in the last 24 hours, and a quote stamped at t | Any row with a clock after t |

How the future is withheld:

- The operator builds the whole week's fixture (`desk.prepare_week`) under the service account, in the mode-0700 study root, before workers start. The fixture holds every wake's evidence, the fill opens and the end marks. The server keeps it in that root and sends only the packet for the current step k.
- Every packet row passes the typed field list. A row with a malformed clock, an undeclared field or a `known_at` after t is dropped. Marks use completed closes only.
- Step k advances only when the session's answering side answers k: the boss in a desk arm, the scouts in the neutral run. Each role gets a fresh wake key at each step, and an answer with any other step's key is refused. A packet is hashed into the journal when it is issued, and a retried request gets back the same saved reply.
- Fills use the first recorded open after the decision. The worker never receives that open before it answers.

How the server enforces it, from `server.py`, `TM07_WORKER_PROBE.md` and `tm07_isolation_probe.py`:

- The desk listener runs as a separate Unix service account (`tm07desk`). It binds to loopback only and serves only the desk routes, with no legacy tape routes.
- Every route needs that role's bearer. Bearers are unique across the study root, and each worker gets only its own.
- Launch requires a single-use, 10-minute receipt bound to the registration, session, stage, port, release and study-root inode. Before writing the receipt, the launcher runs a fresh uid-2000 rehearsal, which checks that the study and rehearsal roots cannot be listed or traversed. It also runs a sudo canary that must appear in the root-owned sudo log.
- One scored stage covers all 20 weeks. A request for any other week (such as the May diagnostic) is refused before any week file is opened. For every scored session, the launcher checks that every listed raw-bar copy is unreadable by uid 2000 without sudo, both before the listener starts and after it stops (lead ruling 2026-11-26, removing the old screen-stage exemption).

STATED, the boundary is soft and audited (lead ruling 2026-11-26):

- Passwordless sudo for uid 2000 stays on this host. Removing it could leave the host without an admin route, and it would not close the other open door: a worker with web access could look up past prices. The receipt records `worker_passwordless_sudo: true` as a fact; it is not a refusal.
- The launch requires every listed price copy unreadable by uid 2000 without sudo, and the sudo log present, root-owned and mode 0600, with the launch canary recorded. The after file keeps every sudo log line added during the session.
- After each week the operator checks three things: the sudo log against the operator's own timed command list (`tm07_isolation_probe review`, which prints VOID on any unlisted line), the server log, and the worker's own list of commands and addresses. Any worker sudo entry, any direct read of a price copy, or any outside price lookup voids that week for that arm. Operator sudo commands are listed with their times so they can be told apart.
- The brief tells every worker the same: no sudo, no price file, no web price lookup, keep and hand over the list, and a breach voids the week.
- Cost of a breach (lead ruling 2026-11-26): a voided week, like a missing week, leaves that arm's comparison incomplete, and an incomplete comparison cannot pass. So one voided week ends that claim. Weeks are never replaced.
- UNKNOWN: whether a worker uses sudo and then edits the log as root, uses the web without listing it, or what provider-side memory holds. The audit can catch a careless breach, not a deliberate and hidden one.

MEASURED, host state after the move (2026-11-26, details and rollback in `rig/tm_notes/TM07_HOST_LOG.md`):

- The 20 paths in the approved move list (`rig/tm_notes/TM07_MOVE_LIST.txt`: the first group in the permission plan plus `rig/data/funding`) now sit under `/var/lib/tm07/raw` (`tm07desk`, mode 0700), each checked unreadable by uid 2000. Nothing in `rig/data` that belongs to stock plans moved.
- sudo now logs. The host had sudo-rs, which logs only to syslog, and the host has no `/dev/log`, so no sudo command was logged anywhere. By lead ruling, `sudo` now points at classic sudo (`/usr/bin/sudo.ws`, 1.9.17p2) through `update-alternatives`, and `/etc/sudoers.d/tm07-log` sends every sudo command by `user` to `/var/log/tm07-sudo.log` (root, 0600). The sudo-rs binary `/usr/lib/cargo/bin/sudo` lost its setuid bit. Sudoers rules are otherwise unchanged. Note for other helpers: `rig/tm_notes/HOST_SUDO_CHANGE.md`.
- Launcher Python is pinned. Every root-run launcher and the `tm07desk` service run `/usr/bin/python3.14` (3.14.4, root, 0755), started with `unset PYTHONPATH PYTHONHOME`, `PYTHONNOUSERSITE=1` and `-B`, from the root-owned release copy `/opt/tm07-release-058a543` (git archive of `058a543`). The service inherits that interpreter through `sys.executable`. `test_tm07` passes on it.

STATED limits of the host boundary:

- `/usr/local/bin/python3.14` is mode 0777 (world-writable). It is never run as root or as `tm07desk`. Its mode is left unchanged by ruling.
- `/usr/lib/cargo/bin/su` keeps its setuid bit. It needs a password that nobody has.
- `rig/tm_store/tape.sqlite` and `tape_fast.sqlite` are symlinks to the moved copies. They resolve, but uid 2000 cannot read the targets.
- `tm07desk` is also in group `user`, so the viewer on 8766 can read the repo checkout.
- The viewer on port 8766 serves moved tape rows over loopback to any local user, so it must be down during every TM07 session. It is restarted only when no TM07 session runs, with stop and start times in the host log. Ports 8765, 8767, 8768 and 8769 stay down.
- `tm_notes`, the coverage tsv and tracked repo pages stay where they are. They hold TM06 weekly results and coverage counts, not bars.

MEASURED, host rehearsal on a made-up session (2026-11-26, receipt copies in `rig/tm_notes/TM07_REHEARSAL/`, originals root 0600 in `/var/lib/tm07/control`):

- With 8766 stopped, the launcher ran as root from `/opt/tm07-release-058a543` on session `TM07-rehearsal-toy`, port 8775, stage `scored`, an empty rehearsal study root, a rehearsal-only key and registration, and all 20 moved paths as `--raw-bar`. No real week, no model session, and no worker read of a price copy.
- All eight uid-2000 probe identities (six boss and arm roles, the news scout and the price scout) passed every check: bearer required, desk routes only, own route allowed, sibling and wrong-role tokens denied, study and rehearsal roots unreadable. The sudo canary landed in the log. The raw-copy check passed before the listener started and after it stopped. The desk reported ready, then stopped on the operator's SIGTERM with outcome `operator-stop`.
- The sudo log caught both operator commands made during the session. `review` with both listed found no unlisted entry. A negative control listing only one printed VOID and named the other line.
- SHA-256: audit `3bd8e470…`, after file `630de53a…`, review `9482ffd2…`, negative review `a45dc359…`, launcher output `d83226cc…`. The audit holds no bearer tokens.

## What the seal still needs

These are operator steps under the service account, after approval and before any session. None of them reads a return.

- Build each week's fixture with `desk.prepare_week` from a protected copy of the snapshot. Record the fixture hash and the funding settlement hash (`score_tm07.funding_profile_hash`) for each week, and assign one unique neutral run ID per week.
- Record the exact platform model IDs for the three participants, with their first-after-cutoff dates. The runner ID is `tm07_desk_v1`, and the study root is one absolute canonical path.
- Sign the registration body with the operator key. `score_tm07.Registration` refuses a body that is missing any of these.
- Auditor b cleared engine `4408b7c` and `058a543` (MEASURED). The approved price copies are behind `tm07desk`, sudo logs, and the made-up rehearsal passed (above). Auditor b's host check against the rehearsal receipt comes next. The first scored session is the lead's word after that host CLEAR.

## Ledger and queue text

Ledger row 198 (`research_rig/TRIAL_LEDGER.md`), as added in this commit:

> 198 | 2026-11-26 MT | `timemachine/TM07_REGISTRATION.md` | Queue 33, TM07 desk. Two bosses (`claude_fable_5_2`, `claude_opus_5_5`), arms A, B and C, two `gemini_neon` scouts, price-only, hourly, 1x, 12 bp per side plus TM06 half spreads and Kraken funding proxy, on Coinbase spot minute bars, snapshot `6346be0d…`. 20 scored weeks fixed by the registered coverage and Sunday-close rule (3 screen, 17 extension; screen baskets differ from TM06 by the accepted minute rule), May 11 diagnostic. Four claims B/A and C/A per boss. Lead ruling 2026-11-26, before the seal and before any return: weekly mark is a one-sided paired t of at least 2.43 on the 20 weekly net differences, at least 12 of 20 winning weeks and a positive mean without the best week, with no screen gate (all 20 weeks run for every arm); both TM06 one-model marks unchanged. Replaces 3 of 3 screen gate plus 16 of 20. R1, R2, R3 shown only. | DRAFT registration. No session, no replay and no return. MEASURED simulated upper-bound power of the registered mark in the package, noise a proxy from TM06 pairs of different models; null per claim at or under 1.25%, error control 1.25% per claim, which bounds the four-claim family at 5% (lead ruling). Old mark power kept as history. Engine pinned at `058a543` (branch `tm07`): ruled mark, no screen gate, raw copies denied to uid 2000 in all 20 weeks, passwordless sudo kept as a recorded fact with a soft, audited boundary (any worker sudo, direct price-copy read or outside price lookup voids the week for that arm). Approved price copies moved behind `tm07desk`; sudo switched to logged classic sudo; launcher pinned to `/usr/bin/python3.14`; made-up rehearsal passed. Auditor b cleared `058a543`; host check against the rehearsal receipt pending. No scored week until the lead's word.

Queue row 33, last column (`docs/QUEUE.md`):

> Registration package drafted (ledger 198, `timemachine/TM07_REGISTRATION.md`): 20 weeks and coins fixed from snapshot `6346be0d…`, costs and marks fixed (weekly mark replaced by the lead's t-based ruling, no screen gate), simulated power stated. The lead accepted the 90% minute rule and the four replaced screen names (screen baskets differ from TM06). Engine pinned at `058a543` with the ruled mark and the soft, audited sudo boundary. Price copies moved behind `tm07desk`, sudo logged, made-up rehearsal passed. Waiting on auditor b's host check and operator sealing; first scored week on the lead's word. Engine branch `tm07` not merged.
