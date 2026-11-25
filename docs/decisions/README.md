# docs/decisions/: what is in this folder and how a decision gets recorded

Status: research's working practice. Proposed by research. No owner decision is recorded here.

## What is here

- Numbered files (`0001-...md` and up) are dated records. Some record what the owner said. Some record what research did or proposed. Each says which at the top.
- `morning_list_2026-11-25.md` is the open list of things the owner is asked to do and decide. Nothing on it is decided.
- `audit_*.md` and `source_check_*.md` are checks of the playbook from 2026-11-24.

## What counts as an owner decision

- Only his own words, with the date he said them, written in a numbered file in this folder.
- A recommendation he has not answered is a proposal, however it is worded and wherever it is written.
- "Sounds good" to a list is recorded as approval of that list as it stood at that time, with the list quoted or linked by commit.

## How to record one, in one commit

1. Add a new file `docs/decisions/NNNN-short-name.md`, where NNNN is the next free number. Put in it the date, his words as he wrote them, the item it answers, and what it does and does not approve.
2. In the open list, do not delete the item. In the "Decisions waiting" table, start its second column with "Decided, see NNNN". In "Things only you can do", start the item with "Done, see NNNN".
3. If the decision sets or changes a number, change `config/thresholds.yaml` in the same commit and name the key in the file from step 1.
4. Update `docs/STATUS.md`: the "Waiting on the owner" section, "Next in the queue" if the queue moves, and "Last updated".
5. Add the new file to `docs/INDEX.md`.
6. Run `python3 tools/check_repo.py --builders`.

A later list of open items is a new dated file. When one is added, change the two lines in `research_rig/export_dashboard.py` that name the list, and the rows in `docs/INDEX.md`.

## What only the owner may change

- `AGENTS.md`, and every file in `docs/quality/`.
- A value in `config/thresholds.yaml` whose status is owner.
- Anything that spends money, opens an account, or places a trade.
