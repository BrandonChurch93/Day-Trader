# practice-records

This branch holds only the records written by the practice trader (`practice/trader.py` on `main`). Pretend money. No code lives here.

- `records/summary.json`: what the owner's screen shows. Rebuilt on every run.
- `records/state.json`: where each rule stands. Rebuilt on every run.
- `records/checks.jsonl`, `orders.jsonl`, `closed.jsonl`, `daily.jsonl`, `problems.jsonl`: one line per event, added to and never edited.

Do not edit these by hand. To start a stopped rule again, the owner says so and the change is made in `records/state.json` with a commit that says why. How to read the files is in `practice/README.md` on `main`.
