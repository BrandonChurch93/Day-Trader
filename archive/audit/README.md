# archive/audit/

Status: RECORD. Written 2026-11-25.

Independent audits of the code in `research_rig/`, each done by a model that did not write the code. The reports are the record of what each auditor found. What was done about each finding is in `docs/research/16_rig_audit.md`, `docs/research/22_replay_05_stock_trend.md` and `docs/research/23_replay_04_coin_basket.md`. The current state is `docs/STATUS.md`.

Before you use anything here:

- The scripts are the auditors' own probes, kept as they were run. `replay_05_probes.py` and `replay_04_independent.py` hold folder paths from the research machine and will not run on another machine until those lines are changed. The reports quote the same paths. The run scripts in `research_rig/` no longer use them.
- The probes read the held-back slice. The same limit applies to them as to the run scripts: do not run one without the owner's yes (`research_rig/README.md`, "How each stored output was made").
- Nothing here is product code.

| File | What it is |
|---|---|
| `2026-11-25_auditor_a.md` | First audit of the first rig's code |
| `2026-11-25_auditor_b.md` | Second audit, of the statistics |
| `replay_independent.py`, `diagnostics.py` | Auditor A's own separate replay and checks |
| `pbo_stability.json` | Auditor B's measurement of how much pass mark 4 moves |
| `2026-11-25_replay_04_audit.md`, `replay_04_independent.py`, `replay_04_probes.py` | Audit of replay 04, with its own rebuild from the raw files |
| `2026-11-25_replay_05_audit.md`, `replay_05_probes.py` | Audit of replay 05. One finding led to the corrected run |
