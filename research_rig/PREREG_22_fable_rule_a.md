# Plan 22. Rule A from the Fable 5.2 picker, one fixed version

Status: FROZEN 2026-11-26 10:25 UTC. Frozen by the drafter on the lead's go-ahead. The config block came first, in its own commit.

STATED. Queue row 40 and ledger row 159 (reserved by the lead). Drafted off repo in `rig/plan22_draft/`, audited by auditor B (blockers B1 to B3 and should-fix items S1 and S2 fixed), with the lead's rulings on the drafter's choices and on the twins mark. No return on real bars has been worked out. The only real files read so far are bar timestamps, row counts and checksums (for coverage), the saved CMC rank pages (raw ranks 1 to 30 only), the plan 16/17 identity evidence, and the archives opened by `score_22.py --validate-inputs`, which computes no return and prints counts only. The held-back list (ranks 51 to 100) was not used.

## Question

STATED. The Fable 5.2 picker (TM06, April to November 2026) appeared to buy a fresh break of a multi-week range on high volume. The autopsy `rig/ideas/fable_picker_autopsy.md` wrote this down as rule A. Plan 22 asks one question: does rule A, fixed before any data, beat simply holding the same coins over 2020-01 to 2026-03, after costs?

Rule B of the autopsy is not in this plan. Rule C is shown only. The funding and open-interest filters are left out of the judged version.

## Rule A as judged

Each setting is one config key in `replay_22_plan`.

- Wake once a day at `wake_hour_utc` = 14 UTC. Only hourly bars that closed by the wake are used: the last one is the 13:00 bar.
- Breakout level: the highest hourly high over the `range_days` = 21 full UTC days before the wake's day.
- Signal for a coin, all of these:
  - the last hourly close is above the level;
  - fresh: the close 24 hours earlier was not above this level, and at the previous wake the coin was not already above that wake's own level;
  - the last hourly close is no more than `max_above_level_pct` = 3% above the level;
  - volume ratio of `min_volume_ratio` = 1.5 or more. The volume ratio is the quote volume of the `volume_window_hours` = 24 hours before the wake divided by the mean 24-hour quote volume of the `volume_days` = 30 days before those.
- Buy at the open of the 14:00 bar, the next bar after the signal.
- At most `max_names` = 5 names. If more coins qualify than there are free slots, take the highest volume ratios.
- Size: after any wake where the set held changes, every name held is reset to 1 / max(`min_parts` = 3, names held) of the account. The rest is cash at zero yield. Spot only, long only, no leverage.
- Exit at a wake, at that wake's 14:00 open, if either:
  - the last daily close (the 23:00 bar, read at 00:00 UTC) after entry is under the breakout level; or
  - at least `stall_days` = 2 days have passed since entry, no hourly high in the 2 days after the fill was above the highest high of the 24 hours before the fill, and the volume ratio is under `stall_volume_ratio` = 1.0.
- No profit target, no time limit.

## Coins and bars

- List: the saved monthly CMC page that plan 18 uses (`rig/data/replay_13/snapshots.json`), raw ranks 1 to `top_rank` = 30. A page counts only strictly after its next-day 00:00 UTC clock and while it is at most `max_page_age_days` = 45 days old. MEASURED: no page in the file is a hole and no gap between pages is above 35 days, so the age limit never binds.
- Out: stablecoins and other pegged tokens, wrapped or staked copies, and gold tokens, by CMC ID (`EXCLUDE_22` in `paths_22.py`). BTC, ETH and exchange tokens stay in.
- Pair mapping: the plan 13 spot segments (`fetch_13.segments`, including the renames such as MATIC to POL). A coin counts as tradable only while its plan 16/17 spot identity row is CONFIRMED at the wake (`identity_asof_16_17.Timeline`). ETH and FTT have no such row, because plan 13 left them out; each is admitted on its one Binance pair.
- Bars: Binance spot 1h archives, the same source as plans 16 and 17 (`rig/data/replay_13/archives`). Missing months (ETH, FTT, the November and December 2019 warm-up and others) were collected from data.binance.vision with their published checksums into `rig/data/replay_22/archives`. `manifest_22.json` pins every file.
- A coin that leaves the list, loses its identity or ends its pair segment while held is sold at the next wake. A coin that stops trading while held is sold at the next bar with volume; if none comes, at the close of its last bar with volume. It is never dropped.

## Judged window and costs

- Judged: `judged_start` = 2020-01-01 to `judged_end` = 2026-04-01 (exclusive). Start in cash at 1.0.
- Shown only, labelled "the months the rule came from": `shown_start` = 2026-04-01 to `shown_end` = 2026-10-26, a fresh account. 2026-10-26 is the end of the plan 16/17 identity evidence.
- Judged cost `judged_cost_bps` = 12 bps a side on every trade. Shown at `shown_cost_bps` = 1, 25 and 40.

## Pass

Pass needs all five, at 12 bps:

1. End value above holding the same list in equal weights after the same costs.
2. Daily Sharpe of `min_sharpe` = 1.0 or more.
3. Largest fall of `max_drawdown` = 40% or less.
4. End value above the `twin_percentile` = 95th percentile of `twins` = 500 random twins (seed `twin_seed` = 22001).
5. Positive in at least `min_positive_years` = 5 of the 7 calendar years (2026 counted to March).

## Shown only

- Rule A with the rule C cash switch: off when BTC's last hourly close is under the lowest low of the `btc_line_days` = 7 full days before the wake's day; back on at the first wake after a daily close above that same line.
- Rule A with the lead's shorter exit: no new high in the 2 days after entry, without the volume condition.
- Bitcoin held; time in cash; trades per year; exit reasons; the result without the best `drop_best` = 3 trades; by-year table; costs at 1, 25 and 40 bps; the April to October 2026 source months.
- Gaps next to results: held hours without a bar, sales after the wake, coins closed at their last bar, buys skipped for want of a fill, coin-wakes not tradable by reason, and pair-days absent from the archive.

## Choices made by the drafter

Where the autopsy or the lead's brief leaves a detail open, the plainest reading was taken. Each one is listed here.

1. Bars are hourly. Daily bars are UTC days (00:00 to 24:00) built from them. The daily close is the close of the 23:00 bar.
2. The wake sees the 13:00 bar's close as the last close. Signals use nothing from 14:00 on.
3. "Prior 21 daily bars" means the 21 full UTC days before the wake's day. The part of today before the wake is not in the level.
4. Fresh, as the autopsy writes it ("below that same level 24 hours earlier"), can never fail under choice 3: the bar 24 hours earlier is inside the 21 days, so its close is under the level by construction. Rule A's own words "first day of the break" are read as: at the previous wake the coin was not already above that wake's level. The autopsy's test is kept as well; it never binds alone. Accepted by the lead.
5. Volume is quote volume in USDT, not coin units, so it stays comparable across price moves.
6. Volume ratio: the 24 bars before the wake, over one thirtieth of the 720 bars before those.
7. Every hourly bar of the 31 days before the wake must exist for a signal. Hours with zero volume count as bars. One missing hour means no signal that wake for that coin.
8. The 3% test is on the last close at the wake, the price the trader sees, not the fill.
9. A buy needs a 14:00 bar with volume. Without one there is no buy. The coin is not bought later on that signal. Coins are ranked for the free slots on signals alone (bars to 13:00), then the fill is checked. A chosen coin with no 14:00 volume leaves its slot in cash; the next coin in the ranking does not take it. Changed after audit B (S2), so the 14:00 bar cannot change who gets a slot.
10. Free slots are 5 minus names held. Ties in volume ratio go to the lower CMC ID. A coin sold at a wake is not bought back at the same wake.
11. Exit wording. The autopsy's second exit is "no new high in the 2 days after entry AND volume ratio back under 1.0". The lead's brief says "no new high in 2 days". The lead decided: the autopsy's exit is judged; the shorter version is shown only.
12. "New high" means an hourly high in the 48 hours after the fill above the highest hourly high of the 24 hours before the fill. The stall exit can fire at any wake from 48 hours after entry on, while the volume ratio is under 1.0. If the volume ratio cannot be read (a missing hour), the stall exit does not fire that wake.
13. The daily-close exit uses the latest daily close after the fill, checked at each wake. The level stays the one set at entry.
14. Exit fills are the wake's 14:00 open. If that bar is missing or has no volume, the next bar with volume in the pair segment. If none comes, the close of its last bar with volume. A delayed sale that falls due at the hour of a later wake fills first, at that hour's open, after the 00:00 mark if that hour is one, and before the wake's own exits, buys and reset. Every wake is an event in the account, so a delayed sale counts as a change in the set held at the first wake at or after its fill, and the reset happens there even when nothing else trades at that wake. Added after audit B (S1) and the final audit.
15. Equal parts: weights are reset only when the set held changes, and then for every name held. In between they drift. With one or two names each has one third and the rest is cash. The reset target is found in three fixed-point steps for costs. If that target would take cash below zero (possible after large gains since the last reset), the target is instead the largest one, found by bisection, that is at most equity less costs over the parts and leaves cash at or above zero. Cash may not go below zero by more than 1e-9 times equity. Added after the final audit.
16. "Leaves the list" includes losing plan 16/17 spot identity confirmation and the end of a pair segment.
17. Plan 18's loader is for perpetual contracts, so it cannot be reused as is for spot. Plan 22 keeps its rank rules (raw ranks 1 to 30, the next-day clock, the 45-day limit, the same saved pages) and takes the spot mapping and identity from plans 13, 16 and 17. Accepted by the lead.
18. Stablecoins, other pegged tokens, wrapped or staked copies and gold tokens are out. Exchange tokens stay in. Most have no Binance spot pair (LEO, OKB, CRO, HT, BGB), so they count as listed but not tradable.
19. ETH and FTT are admitted directly on ETHUSDT and FTTUSDT. FTT's end is handled by its real last bars, with no survivor filter. Accepted by the lead.
20. The equal-weight hold enters a coin at its first wake on the list with a fill, sells it when it leaves, and resets to equal weights whenever the set changes. Same costs.
21. Twins: for each real trade, a random wake in the same calendar month and a random coin among the tradable list coins with a fill at that wake. The holding length in wakes is the same; a trade open at the end stays open to the end. A twin never holds one coin twice at once or more than 5 names. After 1000 failed draws (`twin_max_draws`) the entry is dropped and counted. A twin coin that leaves the list is sold then. Same book, same costs.
22. "Above the 95th percentile" means the end value is greater than numpy's linear 95th percentile of the 500 twin end values.
23. Marks are daily at 00:00 UTC on the last hourly close. Sharpe is the mean over the sample standard deviation of daily simple returns, times the square root of `annual_days` = 365. With fewer than two daily returns, or all of them exactly equal, Sharpe is 0, so the Sharpe mark fails (added after the final audit). The largest fall is on daily marks.
24. A year's return runs from its 1 January mark to the next one. 2020 starts at 1.0 on 2020-01-01. 2026 ends on 2026-04-01.
25. The end value pays the cost of selling what is still held, at the last close.
26. Rule C: the line is the lowest hourly low over the 7 full UTC days before the wake's day. When it fires, all names are sold at that wake and nothing is bought. "That line" is the line on the day it fired. Back on at the first wake whose latest daily close is above it. Rule A then starts again from fresh signals only. Nothing is imputed for missing BTC hours: if the line or the wake's last close is missing, the switch stays on and the wake is counted as `btc_switch_unreadable`; if it is off and the 23:00 close it needs is missing, it stays off and the wake is counted as `btc_switch_recovery_unreadable`.
27. The source months run to 2026-10-26, not 23 November, because the plan 16/17 identity evidence ends there.
28. Without the best three: the three trades with the highest fill-to-fill return are taken out of the schedule and the book is rerun. Freed slots are not refilled.
29. Time in cash is the share of judged wakes, after that wake's trades, with no name held.

## Calibration on planted paths

STATED. `calibrate_22.py` runs the judged machinery unchanged on invented markets: `calibration_coins` = 12 random-walk coins over `calibration_days` = 2283 days, `calibration_seeds` = 20 seeds from `calibration_seed` = 22101. Hourly log moves have sd `calibration_sigma_hourly` = 0.006. At every natural fresh range break (rule A's price tests), the 24 hours of volume before the wake are multiplied by a draw from `calibration_volume_boost` = 2 to 4. With an edge, the price then drifts up by `calibration_edges_pct` = 0, 4, 8 or 16% over `calibration_drift_hours` = 72 hours. No price is moved before a break, so edge 0 is a plain random walk. A second run (`calibrate_22.py --timing`, output `calibration_timing_22.json`) makes the edge timing only: each gain fades back to zero over `calibration_fade_days` = 30 days after the rise, so coins do not trend and holding a coin for months earns nothing from the edge. The point is to show that the five tests rarely pass with no edge, and how large an edge they can find. Both output files are in `research_rig/`. The power figures under Limits are written into this plan by `calibrate_22.py --write-plan` from those two files, not typed.

## Limits

- UNKNOWN. How many dead coins the saved CMC pages left out. The judged claim covers the reconstructed tradable subset only.
- Not every listed coin is tradable at every wake (no Binance spot pair, identity not confirmed, or not yet listed). The counts by window, from metadata only, are in `coverage_22.json`.
- The rule was read off eight months of one agent's notes. The judged window is outside those months, but the rule's shape came from them.
- No funding, open interest or page views.
<!-- calibration figures: written by calibrate_22.py --write-plan from calibration_22.json and calibration_timing_22.json; do not type -->
- MEASURED on planted paths (`calibration_22.json` and `calibration_timing_22.json`, 20 seeds each). With no edge the five tests together pass in 0.05 of seeds. With a true edge of 16% they pass in 0.25 of seeds when the gain lasts and 0.20 when it fades over `calibration_fade_days` = 30 days: about a quarter of seeds or fewer. At 8% they pass in 0.10 and 0.10. The twins test alone passes in 0.25 and 0.20 at 16%. So a fail tells us little and a pass tells us a lot. Rule A holds rising coins for weeks or months, so twins with the same holding lengths share most of a lasting gain, and most of a short-lived gain is given back before the rule exits. Two other twins marks (daily Sharpe, and mean return per trade) were tried on the same planted paths before the freeze; neither raised power, and the lead kept end value.
<!-- end of calibration figures -->

## The one judged run

STATED. Built after audit B (B1 to B3), on the pattern of plans 23 and 26.

- `score_22.py --real --approval-commit <c>` refuses unless HEAD is `c` with no tracked change, `c` adds `research_rig/APPROVAL_22.md` with the line "Approved by the lead: plan 22, one scored run, freeze commit <f>.", `f` is the single parent of `c` and does not have that file, `c` adds nothing else, and every plan 22 file (with the plan 13 and 16 modules it imports: `fetch_13.py`, `fetch_16.py`, `common_13.py`, `identity_asof_16_17.py`) is byte for byte the same in `f`, in `c` and on disk, matching `research_rig/PINNED_22.json`. The `replay_22_plan` pin is on the parsed value of that block written as sorted JSON, not on the file's bytes; the file's bytes are bound by the single-parent rule and the clean tracked tree. The plan must say "Status: FROZEN", the draft must be gone and ledger row 159 must name this plan.
- `PINNED_22.json` also pins the off-repo inputs: `manifest_22.json`, `snapshots.json` and `identity_policy_16_17.json`, on their uncompressed bytes; a file kept only as a `.gz` copy is read decompressed. Every archive is pinned by its checksum in the manifest.
- `test_22.py` runs every real-mode path through the command line in a temporary Git repo with fixture data: validation with and without approval under a trap that fails on any return, each gate refusal, each input check with every pin correct, gzip-only inputs, a failure after the lock, one scored run with planted trades in both windows, and the refused second run with both sealed files unchanged.
- No `PLAN22_` or `P22_` environment variable is allowed. Paths are fixed in code. Git is called by absolute path with `--no-replace-objects`, no fsmonitor and no `GIT_` variables. The run assumes a trusted shell and Python; it does not defend against a changed interpreter.
- The off-repo inputs are read once, checked against their pins, and only those bytes are parsed for the score. A refusal or a failure names a check and a path, never a field value.
- `score_22.py --coverage` reads manifest metadata only and opens no archive; it is not a real mode and has no gate.
- `score_22.py --validate-inputs` runs every check that can fail before the lock: it opens every archive and checks its checksum, row count, first and last hour, the hour grid at the file's own resolution (milliseconds, or microseconds from 2025), duplicate hours, number format and bar sanity, that BTCUSDT's bars start before the warm-up and run to the end of the shown months (extent only: missing interior hours are allowed, as for every coin, and counted; see choice 26 for rule C at missing hours), and that every wake has a list page and every listed coin with identity has bars. It computes no return and writes no lock and no result. With `--approval-commit` it runs the gate too. `--real` runs exactly these checks before it takes the lock.
- Then `--real` takes one lock, `rig/data/replay_22/score_22.lock` (create-exclusive, read-only, file and folder synced). A lock or result that exists, even as a dangling link, means the run is used up. After the lock it runs the gate and every pin again, then scores, then writes `results_22.json` create-exclusive and synced.

## Pins

Filled at freeze in `research_rig/PINNED_22.json`. `score_22.py --real` refuses unless every input matches.
