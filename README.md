# Day-Trader

Research toward an AI-assisted trading system for US stocks and crypto. The product is not built and building has not been approved. A research rig exists for testing ideas on past prices. No broker account or key is connected.

This page does not hold results. Results change, and they live in one place: `docs/STATUS.md`.

## Read in this order

| Step | File | What you get | Length |
|---|---|---|---|
| 1 | `AGENTS.md` | The rules. They win over everything else | One page |
| 2 | `docs/STATUS.md` | Where the project stands today: every test and its result, what is believed now, what waits on the owner, what is next | One page |
| 3 | `docs/INDEX.md` | The map. Find your task in its first table and read only the files it names | Look up, do not read through |

Then, only if your task needs it:

- `docs/quality/00_READ_FIRST.md` before you plan, build or review anything. It is the owner's standard.
- `docs/playbook/00_START_HERE.md` for the shape of the product and where Perplexity fits.
- `research_rig/README.md` before you run or add a test.
- `config/thresholds.yaml` before you use or change a number.

## Five rules that are easy to break

1. A number is written once, in `config/thresholds.yaml`. Documents name the key.
2. A test's plan and its trial ledger rows are pushed before the test runs.
3. Numbers in documents are written by a script from an output file, never typed.
4. A result or decision changes `docs/STATUS.md` in the same commit. A new, moved or retired file changes `docs/INDEX.md` in the same commit.
5. Run `python3 tools/check_repo.py` before every commit. It fails if the map is not true.

## Which file wins when two disagree

1. `AGENTS.md`
2. `config/thresholds.yaml` for any number
3. `docs/STATUS.md` for any result or the current state
4. A dated note in `docs/decisions/` over an undated page
5. The newer of two dated pages

The playbook pages were written from reading on 2026-11-24, before the project ran a test of its own. Where they and the status page disagree, the status page stands.

## Layout

```text
Day-Trader/
├── AGENTS.md              the rules
├── README.md              this page
├── config/                every threshold and owner number, once
├── docs/
│   ├── STATUS.md          the current state (read second)
│   ├── INDEX.md           the map of every file
│   ├── quality/           the owner's quality bar and build method
│   ├── playbook/          short decision pages per topic
│   ├── research/          full reports and the results of our own tests
│   └── decisions/         dated record of choices and what the owner is asked next
├── research_rig/          the test rig: plans, scripts, outputs. Not the product
├── audit/                 independent audits of the rig code
├── dashboard/             the owner's screen for tests and trades
└── tools/                 the check that keeps the map true
```

## Evidence labels

- MEASURED: independent data, official rule text, a published price page, or our own logged test.
- STATED: claimed by a vendor, author or promoter and not independently verified.
- UNKNOWN: could not be verified. A thing to test, not a fact.

This repository is research and engineering documentation, not financial advice.
