# 0003 - Quality bar adopted, review items actioned

Date: 2026-11-24

## What the owner said, 2026-11-24

- On wiring `archive/quality/` into `AGENTS.md` and `README.md`: "I approve that change to AGENTS.md."
- On the review positions and the TRANSLATED lines put to him: "I'll go with you recommendations."
- On run limits, he accepted a two-hour cap on research runs at the time. He removed that cap on 2026-11-25.
- "We are still in research. Do not start building."

What he approved, as it was put to him: yes to review items 3 to 9 and 12 as written, yes to the source check in item 10, and the TRANSLATED lines confirmed with changes to five of them. The two scope calls in item 2 were not part of this approval. They go to him one at a time.

## TRANSLATED lines

All are now marked "OWNER, confirmed 2026-11-24" in `archive/quality/`.

| # | File | Line | Outcome |
|---|---|---|---|
| T1 | 00 | Capital gates are evidence gates; all software is finished in v1 | Confirmed. Added: live order code is tested on paper only and reported as open until he approves live |
| T2 | 00, 01 | Capital and risk limits are the owner's numbers only | Confirmed |
| T3 | 01 | The surfaces are whatever the owner watches and touches | Changed. The surface list is provisional until the owner's-seat research is done. The no-stand-in rule stays |
| T4 | 01 | Python conventions for this repo | Confirmed |
| T5 | 01 | Numbers and results section | Confirmed. Added: it applies to our own results; cited figures keep their label and link |
| T6 | 01 | Never run the held-back slice twice | Changed. One defined rerun when a machine check proves the engine was wrong; logged, counted as a trial, reported as a rerun |
| T7 | 01 | The decide, log, continue rule sits under `AGENTS.md` | Confirmed |
| T8 | 02 | A kit sits beside `AGENTS.md` and the playbook | Confirmed. The kit lives in `kit/` at the repo root |
| T9 | 02 | Stops are gathered into as few as possible | Changed. One planned build stop, for paper keys. The live go is an evidence gate after `BUILD COMPLETE`, on a written owner decision |
| T10 | 02 | Pictures here are charts, tables and screenshots | Confirmed |
| T11 | 02 | Auditor brief additions f, g, h | Changed. Added (i): any way to switch from paper to live without a decision record |
| T12 | 02 | Research and planning runs carry a time limit | Confirmed at the time. The owner removed the cap on 2026-11-25. |
| T13 | 03 | "Owner decision" only for what he said | Confirmed. Decisions 0001 and 0002 were relabelled to match |
| T14 | 04 | The ten hand-overs before a kit | Changed. Added an eleventh: a fresh check of the sources |

## Review items from `archive/quality/05_repo_review_2026-11-24.md`

| Item | Status |
|---|---|
| 1 Owner's seat research, then a derby | Agreed. Not started. Comes after the two scope calls |
| 2 Two scope calls recorded as decided by the evidence | Decision 0001 relabelled: rows 1 and 2 are scope calls not yet put to the owner. Each goes to him on its own |
| 3 Thresholds repeated across files | Done. `config/thresholds.yaml` holds each one. Playbooks and decisions name the key |
| 4 Live money numbers in playbook 06 | Done. They are open owner keys with a `recommended` field and no value |
| 5 Nine open items without a pick | Done. Each open item in 0001 and 0002 has a recommended pick, a reason and a cost. A broker study started on 2026-11-24 may change picks B and C |
| 6 Research 06 still shows a model returning a trade intent | Done. Superseded notes at sections 2, 3, 6 and the closing list |
| 7 Backtester checked only against itself | Draft fixture list at `docs/research/08_backtester_fixtures_draft.md`. Expected values are worked out at kit time |
| 8 Cost comparison typed in three places | Done. It lives in playbook 05 only |
| 9 Build durations in research 06 | Done. Removed. Sample sizes stay |
| 10 Audits checked playbooks against their own research | Done for playbooks 01 to 03. See `source_check_2026-11-24.md`. Playbooks 04 to 06 not yet checked |
| 11 No kit files yet | Nothing now. Still in research |
| 12 Em dashes | Done in research 03, audits 02 and 04 |

## Other changes in this commit

- `docs/research/07_tradingview_and_operator_access.md` added, answering the owner's question of 2026-11-24. One do-not line added to playbook 04.
- Proposed value changed: `intraday_trend_max_round_trip_bps` from 2 to 1, to match its source.
- Proposed keys added: `max_kelly_fraction`, `drawdown_derisk_band`.

## Still open

- The two scope calls (0001 rows 1 and 2).
- Every key with status `open` in `config/thresholds.yaml`.
- Every key with status `proposed`. None is confirmed by the owner.
- Who the Builder is and where it runs.
- The replay comparison of models on dates after their training cutoff. Offered, not approved.
