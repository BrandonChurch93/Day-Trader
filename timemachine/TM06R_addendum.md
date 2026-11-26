# TM06-R: repeat of the Claude Fable 5.2 picker (addendum to plan TM06)

The lead agent decided this on 2026-11-26, before any further data, after the arm g result was read.

## Purpose

This separates the model from the draw. It adds two more complete runs (run 2 and run 3) of the Claude Fable 5.2 picker, model id claude_fable_5_2, on arm g's eight months. Arm g is run 1.

## Held the same as arm g

- Months: tm06_plan picker_start to picker_end, the same eight months as TM06-P-g-*.
- Method card: arm g's part-P copy, rig/tm_notes/TM06-g_prep/F01_hot_coin_swing_partP.md, sha256 0314710a8f980018275397b276f91dd2e58389cc643574e4dc37165be852a931 (git fc680b7).
- Config: the same as each TM06-P-g session. This covers the fees (tm_perp_fee_levels_bps, with tm06_plan.main_fee_bps as the main line), the perp block, wakes, coins, tape and the tm06 block. A dry run checked these against arm g with 0 differences. Only session, trader, created_utc and git differ.
- Briefs: TM06_LAUNCH_BRIEFS.md as used for arm g, with only the session name changed and one line added. The added line is: "Off limits: the folders /home/user/workspace/rig/tm_notes/TM06-P-g-* and /home/user/workspace/rig/tm_runs/TM06-P-g-* belong to another run. Do not open, list, search or read anything in them, and do not read any other session's notes or scratch folder."
- Hand-offs: the same as arm g, 2 agents per month (tm06_handoff_picker_split_day).
- Server: the part-P trade server on port 8768, with the same code (timemachine/server.py).
- Twin settings: tm_weights_twin_draws and tm_weights_twin_seed are the same.
  - Note: the scorer keys each draw by session id as well as the seed, at tm06.py line 521, Random("tm06_picker_twin:{seed}:{session_id}:{i}"). Each repeat therefore gets its own set of random-swap twins, as every arm already does. Matching arm g's exact draws would need a code change, and none is made.
- Each session is fresh. It has its own notes and scratch folders and no access to arm g's notes or scratch folders, as the brief says. tm06.key_check refuses any answer whose session or answer_key does not match the current packet.

## Session list (16)

Run 2:

- TM06-P-g2-2026-04
- TM06-P-g2-2026-05
- TM06-P-g2-2026-06
- TM06-P-g2-2026-07
- TM06-P-g2-2026-08
- TM06-P-g2-2026-09
- TM06-P-g2-2026-10
- TM06-P-g2-2026-11

Run 3:

- TM06-P-g3-2026-04
- TM06-P-g3-2026-05
- TM06-P-g3-2026-06
- TM06-P-g3-2026-07
- TM06-P-g3-2026-08
- TM06-P-g3-2026-09
- TM06-P-g3-2026-10
- TM06-P-g3-2026-11

The trader ids are P-G2 and P-G3. The SESSIONS.jsonl lines are held off repo in rig/tm_notes/TM06R_prep/SESSIONS_add.jsonl and get appended to timemachine/SESSIONS.jsonl after the six-model scoring ends.

## Scoring

Scoring starts only after results_tm06_six_fast.json is written and the lead says go.

The scorer joins sessions by model name, and all three runs carry the same name. So each run is scored on its own view with the plan's scorer, score_tm06.py, unchanged:

- rig/tm_score_views/g2 holds TM06-P-g2-*.
- rig/tm_score_views/g3 holds TM06-P-g3-*.

The outputs are rig/tm_notes/results_tm06_g2.json and results_tm06_g3.json, both off repo. Run 1 is results_tm06_g.json, already written (sha256 cd49fb4c...).

## Marks, fixed now

Each run is joined on its own, at tm06_plan.main_fee_bps and 1x.

A run clears when both of these hold in its joined picker block:

- above.equal_all_held is true: the joined gain is above holding all the listed coins.
- above.twins_pass_percentile is true: the joined gain is above its joined random-swap twins at tm_weights_pass_percentile. The scorer counts this strictly, and a tie counts against the model, per score_weights.judge.

Outcomes, judged on runs 2 and 3:

- Repeats: both runs clear.
- Did not repeat: neither run clears.
- Mixed: exactly one run clears.

## Shown, not judged

These come from a small off-repo script over the three result files:

- Each run's May (2026-05): the model's gain against the top_7d_rise yardstick ("May risers") in that month's main-line block.
- Each run joined without its best month, with the best month chosen by the model's own gain.
- For each month, the middle (median) of the three runs' gains.

## Limit, to print with any result

The months are the same, so this tests run-to-run luck on these eight months only. It does not test other markets or other periods.

## Ledger row (for the lead to add as TM06-R)

TM06-R | Repeat of the Claude Fable 5.2 picker (claude_fable_5_2), runs 2 and 3 (TM06-P-g2-*, TM06-P-g3-*, 16 sessions) on arm g's eight months. Same card (fc680b7 copy, sha 0314710a...), config, fees, briefs (plus an off-limits line for TM06-P-g-*), server and twin settings. Each run is scored on its own view by score_tm06.py, unchanged. Repeats if both runs clear above.equal_all_held and above.twins_pass_percentile, did not repeat if neither clears, mixed if one does. Shown: each run's May against top_7d_rise, each run without its best month, and the per-month median of three runs. Limit: same months, so this tests run-to-run luck only, not other markets. Decided 2026-11-26 before any further data. Scoring waits for the six-model file and the lead's go.
