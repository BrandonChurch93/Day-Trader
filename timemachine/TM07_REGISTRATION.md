# TM07 registration package (ledger 198)

STATED. Draft for review, written 2026-11-26. It fixes every week, coin, arm, prompt, cost and mark before any TM07 session. No trader, worker, model or listener has been started. No arm, twin, yardstick or rule arm has been replayed, and no return has been computed on the snapshot. The package becomes the frozen registration only when the lead approves it and the operator seals it (see "What the seal still needs").

## What is pinned

- Engine and plan: commit `bdc5f6a722a0e78036d50c3dd08c964c97703d6f` on branch `tm07` (checkout `dt-tm07`; not merged into work, which stays the lead's call). The files used, by SHA-256 at that commit:

| File at `bdc5f6a` | SHA-256 |
|---|---|
| `timemachine/PLAN_TM07_desk_DRAFT.md` | `a64b81d01d1893a6905cc345102fdc6b8fbc0e459b353526f81b18e19c03e57b` |
| `timemachine/desk.py` | `260f3ed8d6b761ec140c070d670d6faa6546f876e3e4bd39091e267eb21b2479` |
| `timemachine/desk_orders.py` | `fcbbf8cd8946dd1921ea8011f967928e6611e0b4c502f1d7b62b9250f5c8c3d8` |
| `timemachine/score_tm07.py` | `d88cd806fe0644332d4ba1fb9b15f43f441357f0f69f58b9452155fee7a68db6` |
| `timemachine/server.py` | `5a02526969bd81744c59f7cfff8874e7372919324449d4c21a71f69f5058b303` |
| `timemachine/perp.py` | `1a98dc755d358394ac88512cbde6cff49c1e94ff398c899ac0e7089d2b1cf2c1` |
| `timemachine/tm06.py` | `65e5561e92b72bd7b6042c5047a2ec5e437a4e76154094d91c0d09834cba1613` |
| `timemachine/TRADER_BRIEF_DESK.md` | `28bd33070f68f668ad9426887430aa8ae6d6ae2f538b2f6ea8fda78fedf57156` |
| `timemachine/TM07_WORKER_PROBE.md` | `46a16741d8afc711cb089db02cac05c684866ebabe1ce275cd565f1d1f1129eb` |
| `timemachine/tm07_isolation_probe.py` | `25f96d485e61f538e37d2f1c941257de38955296a4c5e4ded1528f50d2b1e967` |

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

MEASURED, and a decision for the lead before the seal. The 90% minute rule, written before any of these bars were fetched, removes four of the 15 TM06 screen names: PEPE in July, BNB in August, and AAVE and BNB in October. So the three screen weeks are no longer exactly the TM06 swing baskets. Coinbase spot has no candle for a minute without a trade, which is why only 8 to 18 of the 20 watch coins reach 90% in a given week. The table applies the rule as written. Any change to the rule now would be made after seeing coverage counts, though before any return. It would need its own line in this package.

The scored set is the three screen weeks plus the 17 extension weeks: 20 weeks. May 11 is diagnostic only and is never scored.

## Arms and prompts

- Bosses: `claude_fable_5_2` and `claude_opus_5_5`. Scouts: two `gemini_neon` roles (price and news). The news role has no input, because TM07 is price-only.
- Arms for each boss and week: A (fresh solo boss, sees the full raw packet), B (boss with the scouts' notes, its own book and the clock) and C (B plus up to two standing orders). Each arm gets three lookups per wake. That makes 2 bosses × 3 arms × 20 weeks = 120 boss sessions.
- The scouts run once per week, as one neutral stream. The stream is sealed and copied by hash into each B and C arm of that week: 20 scout streams, each with 2 roles.
- Order rules, fills, maintenance, funding and the min-change floor are as in the plan at `bdc5f6a` ("Orders and evidence"). The program scales every vector to 1x gross after costs (`tm06_plan.swing_max_gross`).
- Prompt for every role: `timemachine/TRADER_BRIEF_DESK.md` at `bdc5f6a`, unchanged, SHA-256 above. It goes with the launch text below, in which only the placeholders change. A worker gets this text and its own bearer through the operator, nothing else. At a handoff, the next agent gets the same text and only the server's handoff packet.

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

R1, R2 and R3 are as in the plan at `bdc5f6a` ("Fixed-rule arms (no AI)"). They are shown only, with no claims and no marks. The scorer computes them only after the registered sessions of that week are sealed. Their judged test is the forward card E06 (`practice/traders/E06_forward_hot_coin_rules.md`), which has been running since its freeze `e128e7d`.

## Costs, fixed now

- Main: fee `tm06_plan.main_fee_bps` (12 bp) per side. Each coin also pays its half spread from `tm_perp_half_spread_bps`, falling back to `tm_crypto_half_spread_bps_by_coin`.
- Funding: Kraken `PF_` settlements at their recorded stamps, with the configured fallback where none is observed. Maintenance and liquidation penalty are as in `perp.p_params`, and the min-change floor is the TM06 value. All of these are pinned by the cost profile hash above.
- Leverage: 1x for every judged line.
- Shown only: the same replay at 25 and 40 bp per side, at 2x and 3x, and with a delayed-open check. None of these can rescue a failed main result.

## Marks, fixed now

For each boss, the comparisons B against A and C against A make four claims.

- Gate: the extension opens for a claim only if that arm beats fresh A to the cent in all three screen weeks. A tie, a missing week or an invalid week is not a win.
- Weekly mark: at least 16 wins out of all 20 weeks, with the three screen weeks included. The one-sided per-claim cap is 1.25%, and the fair-coin tail at 16 of 20 is 0.5909% (`score_tm07.sign_tail`).
- Both TM06 one-model marks must also hold, on chained net weekly gains. The arm must beat the week's five coins held equally, and it must beat the 90th percentile of 1,000 shuffled timing twins (seed 1).
- C against B is descriptive only. Different bosses on the same week are not independent weeks.

## Synthetic power

MEASURED by exact arithmetic (`tools/tm07_power.py`), with no market data. Weeks are taken as independent, with one weekly win chance. A claim passes its weekly part only if it wins all three screen weeks and at least 13 of the 17 extension weeks. The two chained-gain lines are extra conditions, so every figure below is an upper bound.

| Weekly win chance | Screen gate passes | Claim passes the weekly part |
|---:|---:|---:|
| 0.50 (null) | 12.50% | 0.31% |
| 0.60 | 21.60% | 2.72% |
| 0.70 | 34.30% | 13.33% |
| 0.75 | 42.19% | 24.21% |
| 0.80 | 51.20% | 38.82% |
| 0.85 | 61.41% | 55.35% |
| 0.90 | 72.90% | 71.29% |

Under the null, the chance that any of the four claims passes is at most 1.22%. STATED: the design is powered only for an arm that wins about 85% or more of its weeks against fresh A; at 70% it fails most of the time. Under the queue screen ([doc 117](../docs/research/117_power_screen_before_data.md)), it is a weakly powered test of a modest edge. It can still catch a large one.

## Isolation design

What each role sees at wake k (hour t). It comes from `desk.py` at `bdc5f6a`:

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
- A request outside the allowed stage is refused before any week file is opened. For extension sessions, the launcher checks that every listed raw-bar copy is unreadable by uid 2000, both before the listener starts and after it stops.

MEASURED, open gaps that block the extension as written:

- Every price copy on this host is owned by `user`, uid 2000, which is the worker uid. That covers the custody snapshot (`rig/tm07_custody`, mode 0700 but owned by uid 2000), the three-week TM07 file, and `rig/tm_store/tape.sqlite` and `tape_fast.sqlite`, which hold these months for the watch coins. Passwordless sudo also works for uid 2000.
- So the fixed extension gate (raw bars unreadable by uid 2000 without sudo, throughout extension sessions) cannot pass until the operator moves or re-owns every copy behind the service account. That would also cut off the ports 8765 to 8767 servers that read `tape_fast.sqlite`, so it needs its own decision.
- For the screen weeks, raw bars stay readable as in TM06. That is a stated limit, not a control.
- UNKNOWN: whether a worker uses sudo, the web or any readable copy, and what provider-side memory holds. The brief forbids all three; that is an instruction, not proof.

## What the seal still needs

These are operator steps under the service account, after approval and before any session. None of them reads a return.

- Build each week's fixture with `desk.prepare_week` from a protected copy of the snapshot. Record the fixture hash and the funding settlement hash (`score_tm07.funding_profile_hash`) for each week, and assign one unique neutral run ID per week.
- Record the exact platform model IDs for the three participants, with their first-after-cutoff dates. The runner ID is `tm07_desk_v1`, and the study root is one absolute canonical path.
- Sign the registration body with the operator key. `score_tm07.Registration` refuses a body that is missing any of these.
- Run the real-host rehearsal in `TM07_WORKER_PROBE.md`. The independent isolation review (`/root/rig_code_auditor_b`) comes before any registered session.

## Ledger and queue text

Ledger row 198 (`research_rig/TRIAL_LEDGER.md`), as added in this commit:

> 198 | 2026-11-26 MT | `timemachine/TM07_REGISTRATION.md` | Queue 33, TM07 desk. Two bosses (`claude_fable_5_2`, `claude_opus_5_5`), arms A, B and C, two `gemini_neon` scouts, price-only, hourly, 1x, 12 bp per side plus TM06 half spreads and Kraken funding proxy, on Coinbase spot minute bars, snapshot `6346be0d…`. 20 scored weeks fixed by the registered coverage and Sunday-close rule (3 screen, 17 extension), May 11 diagnostic. Four claims B/A and C/A per boss: 3 of 3 screen gate, then 16 of 20 weekly wins and both TM06 one-model marks. R1, R2, R3 shown only. | DRAFT registration. No session, no replay and no return. MEASURED synthetic upper-bound power 13.33% at a 0.70 weekly win chance and 55.35% at 0.85; null at most 1.22% across four claims. Extension blocked until every raw copy is unreadable by uid 2000. Isolation review pending.

Queue row 33, last column (`docs/QUEUE.md`):

> Registration package drafted (ledger 198, `timemachine/TM07_REGISTRATION.md`): 20 weeks and coins fixed from snapshot `6346be0d…`, costs and marks fixed, synthetic power stated. Waiting on the lead's ruling on the four screen names displaced by the minute rule, the isolation review, operator sealing, and protected raw copies for the extension. Engine branch `tm07` not merged.
