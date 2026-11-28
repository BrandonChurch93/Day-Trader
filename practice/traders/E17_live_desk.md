# E17: the live desk, scouts propose and code decides

STATED. E17 copies [E15](E15_live_desk.md) so their frozen trading code can be compared directly. The trading rules, scout models and prompt are unchanged. E17 changes only how the desk hands off a scout request, accounts for an unclaimed request, and checks both models before starting. The desk never calls a model, and no credential goes in any handoff file.

STATED. Pretend money, forward in real time, Binance.US public data only. There is no venue account or key, no real order and no compounding. The code is `practice/desk_e17.py` and the settings are `forward_e17` and `practice_e17_*` in `config/thresholds.yaml`. Use [ledger row 242](../../research_rig/TRIAL_LEDGER.md) with E15's fixed rules on row 237.

## What runs

- One wake every hour, inside HH:20:00 to HH:25:00 UTC (`window_open_s`, `book_cutoff_s`, `window_close_s`). No request is sent before the window opens or at or after the book cutoff (`book_cutoff_s`, 290 s after opening). No request is ever made before `not_before_utc`.
- Every request goes through `practice/venue_binance_us.py`, unchanged (blob ccd1e045), and through `forward_e14.request`. An unsent request that finds the shared gate busy retries in short steps for at most `busy_wait_s` and only inside the window. After that it is counted as lost and never crashes the loop.
- Gate outcomes:
  - A shared cooldown is respected.
  - HTTP 418, 401, 403 or 451, or any gate custody fault, stops the desk with a stop record. The gate is held only per request.
- Order inside a wake:
  - Due exits.
  - Pair status and 48 closed hourly candles for the 20 USD coins.
  - The filters.
  - Pre-decision book summaries for qualifiers (card S also uses them as its scan).
  - Scout calls. All requests are finished first, and no gate is held during a call.
  - Rule and random choices.
  - `practice/gate.py` rechecks every line.
  - One fresh post-decision entry book per chosen coin, shared by every line and card that chose it.
- Fills:
  - Walk the asks for `size_usd` ($250).
  - At the due wake, sell the same base amount into a fresh exit book's bids.
  - Taker fee `practice_e17_fee_bps_per_side` (2 bp) on each leg, BNB 1 bp (`forward_e10_binance_us`).
  - Net is a fraction of the $250.
  - Missing, late, thin or busy books void the entry, which takes no slot. An exit that does not fill retries at each later wake, up to `exit_retry_wakes` or the card's last exit wake, whichever comes first, and is then closed as void. Nothing is requested for a card after its last exit wake. An exit is never filled at an assumed price.
  - Terminal fence. After a gate stop inside a wake, no further entry or exit is priced, even from a book already fetched. Entries and exits priced before the stop stay on record as they were.
- Missed or interrupted wakes are void and never fetched later.
- Frozen inputs are the `forward_e17` block, its fee row, the shared gate custody block `binance_us_gate`, every `practice_e17_*` gate setting and the pick limits, the prompts and the pinned source files. They are checked before each wake against the values the wake uses, and again after it. A change stops the desk.
- Accepted limit (lead's waiver, same as E14 and Measurement 134): a wall-clock step back between the last guarded time check and the transport's own clock read could send a request early. Its reply is discarded. The host needs synchronized UTC.
- Stated timing limit: when no scout runner is there, the desk waits up to 20 seconds before it gives up. The rule-only and random lines can get their entry books up to 20 seconds later than with a runner present. Every line that chose the same coin still uses the same book. No line sees a later book than another for that coin. This changes timing, not what a line can see before it chooses.

## The three cards

Every card has a random line. It picks uniformly among the qualifiers from `seed`, which is fixed at registration, and it never passes.

Card W, washout pick (with E14 and Plan 76).

- Roster: `cards.W.coins` (the E14 eleven).
- Qualifier: last closed hour closed at least `cards.W.fall` (5%) below the prior close.
- Lines:
  - scout: the small model names one qualifier or passes.
  - rule: the largest fall, ties in roster order.
  - random.
- Hold 24 h, time exit only.
- One card-level slot: no new signal while any W line is open.
- A lost candle page in the roster voids the wake's W decision.
- Gate checks (`E17W.json`): `enough_bars` 2, `fell_at_least` over 1 bar by 0.05.

Card F, BTC-shock alt fade (rule 70-102, with E12).

- Signal: BTC's two-hour log close move at or below -`threshold` (1.5%). An alt qualifies when its move is below `multiple` (2) times BTC's.
- Strength: 2 × BTC move − alt move. The rule pick is the strongest, ties in roster order. No signal when an hour from the wake to the exit is sweep_70's maintenance hour (Friday 17:00 New York).
- Lines: scout, rule, random.
- Hold 2 h. One card-level slot.
- Gate checks (`E17F.json`): `enough_bars` 3, and a per-coin floor `fell_at_least` over 2 bars by 0.0295. The gate has no cross-coin check, so the BTC condition and the relative check are recomputed by the desk from the same candles.

Card S, scout scan.

- Scans at 00:20, 04:20, 08:20, 12:20, 16:20 and 20:20 UTC (`cards.S.scan_hours`).
- Qualifiers: coins whose pair is TRADING, that have 24 closed hours, and whose walked $250 buy cost at the scan (before fee, against the midpoint) is at or below `cards.S.cost_limit_bp`, 25 bp per side. The lead fixed it after Measurement 135 (ledger 236). That measurement covered two calm night hours. MEASURED: 15 of 20 coins were at or below 25 bp per side at $250, and the median across coins was 5.4 bp. 25 bp is also Measurement 134's line.
- Lines:
  - scout_small: the small model.
  - scout_second: `claude_sonnet_5_5`.
  - random.
  Each scout names one qualifier or passes.
- Up to `cards.S.max_open` (6) open tickets per line. Hold 24 h.
- Gate checks (`E17S.json`): `enough_bars` 24.

## Scouts

- The desk writes one request per scout line to `/home/user/workspace/rig/data/desk_e17_scout`. A separate live command runs `practice/scout_runner_e17.py` and makes the structured SDK call with no tools or retries. The runner uses its own live session and checks its pinned files against its checked-out build. The folder and files are private. A claim and reply must match the request id, request hash and desk build.
- Cards W and F call only when their filter finds qualifiers. Card S calls at each scan with qualifiers.
- Each call is capped at `scout_timeout_s` and `scout_max_tokens`. It is cut shorter when the window needs `entry_reserve_s` for entry books, and skipped when less than `scout_min_s` is left. A skipped call is not a call: it is recorded as `scout_no_time`, voids that pair, and does not count toward the repair stop.
- Claim and withdrawal rename the same request, so only one can win. The runner takes the claim time after the rename. It does not call the model if that time is at or after the claim deadline. The desk withdraws an unclaimed request without waiting for the runner's lock. If a rename won but its time has not yet been written, the desk gives it at most two more seconds, never past the reply deadline. Without a valid claim the desk records `scout_no_runner`, voids the pair and does not count a call toward the repair stop. Timely claims count in the desk's dispatch order, even if the runner took them in another order or the desk had to recover an unfinished wake. A claimed request that fails or has no timely reply still counts. The log keeps the error class and short service status, or `UNKNOWN`, but never the error message. Wrong replies are ignored and counted. The desk uses one lock to keep starts and wakes apart. It sweeps and counts old handoff files at start and at the start of each wake, and removes its own handoff files after recording the wake.
- `finish_reason` must be end of turn. The reply has exactly `choice` (a qualifier or `pass`), `tags` (from the fixed list in the code) and `facts` (1 to 1,000 characters). Anything else is a failed reply.
- The scout sees only the packet: returns, volume ratios, 24 relative closes and volumes for the qualifiers, and book summaries. All of it comes from closed candles before the wake and books in this window. It sees no news text and no rule or random choice.
- Small model: `gpt5_mini`. MEASURED for E15 on 2026-11-27 with the same prompt, schema and packet code, on five made-up packets (cards W, F, S, W, S):
  - `gpt5_nano`, the smallest in the SDK list, gave 4 valid replies of 5. One reply failed the tag rule.
  - `gpt5_mini` gave 5 of 5.
  - `claude_sonnet_5_5`, the second model for card S, also gave 5 of 5.
  - Calls from a detached process (setsid, parent pid 1) worked.
  - The records are kept off the repo in `/home/user/workspace/rig/desk_e17_probe`.
- Models, the prompt hash per card and every setting are frozen in the log header. A change is a new attempt.

## Marks, written before the start

Cards W and F:

- The paired difference per signal: scout minus rule, net. A scout pass or gate refusal counts as 0.
- All four must hold:
  - Mean above zero.
  - Mean above zero without the best two differences.
  - t at least 2.0, clustered by UTC entry day.
  - The scout line's own net mean above zero.
- Card W: judged at 60 pairs, under 30 too few, last wake 2028-11-30 23:00 UTC.
- Card F: judged at 150 pairs, under 60 too few, last wake 2028-11-30 23:00 UTC.

Card S:

- The paired difference per scan, each scout line minus the random line, net. A pass counts as 0.
- All four must hold, for each scout line on its own:
  - Mean above zero.
  - Mean above zero after dropping the best two entry days.
  - t at least 2.0, clustered by UTC entry day.
  - The scout line's own net mean above zero.
- Judged at 240 paired scans, under 120 too few. Last exit wake 2027-03-31 20:00 UTC; no entry whose exit falls after it.
- Expectation written before the start: the lead expects no difference (TM04: the models' picks did not beat random baskets).

Rules for every card:

- A pair is void when a needed line's entry or final exit is void, or when the scout's reply failed (call or form). Voids are counted.
- No entry whose exit is after the card's last wake.

## Stops

- Shared gate stop or custody fault: the desk stops with a stop record. A new start needs a ruling.
- More than `repair_max_failed` (5) failed scout replies, by form or by call, in the first `repair_window_calls` (20) scout calls, counted across the desk: stop for repair. The repaired build is a new attempt.
- A changed frozen input: refused.

## Operation

- `start` needs an independent CLEAR audit and `E17_START=<frozen build hash>` on the ledger row in committed local main. Above gate generation zero, it also needs `E17_START_GENERATION=<n>`. Start only after E15 has ended and a runner is active. Both models must return valid replies to small checks. After they answer, the desk checks the frozen build, committed approval and shared gate again, then chooses the first wake from the current time. It writes no receipt if any check fails.
- The live helper runs `python3 -B practice/scout_runner_e17.py --until <UTC-time>` from the frozen checkout. For each wake, the planned command starts about 18 minutes and 30 seconds past the hour and accepts requests until 25 minutes and 30 seconds past. It then finishes in-flight calls and exits. Both `start` and `loop` drop the desk's inherited model credential.
- `start` writes a once-only receipt under `/home/user/workspace/rig/data/desk_e17_authorizations`, so the same key cannot start a second run. Only the lead runs `start`.
- Then `python3 practice/desk_e17.py loop` from the frozen tree.
- `alive` prints counts only. `publish` writes the counts-only public file `practice/forward/E17_log.json` and the private dashboard fields to `/home/user/workspace/rig/data/desk_e17/dashboard.json`.
- On the dashboard, W and F show counts only until judging. S shows every closed pretend trade's net, newest exit first, and the running scout-minus-random gap for both scout lines, under the fixed label "not judged yet; nothing about this card changes before its judging count". The gaps come from the same pairing function the judging will use.
- Judging is not in this build. `judge()` is tested but not called. The judging read is a separate build with its own audit and once-only key.
- Books, candles, packets, replies, fills and decisions stay in the private anchored log `/home/user/workspace/rig/data/desk_e17` (0700 folder, 0600 files). Nothing raw goes in the repo.

UNKNOWN: Binance.US's full Terms of Use (doc 194), how often each card will signal on Binance.US, and every forward outcome.
