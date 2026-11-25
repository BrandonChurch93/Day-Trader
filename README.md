# Day-Trader

Research toward an AI-assisted trading system for US stocks and crypto. The product is not built and building has not been approved. A research rig exists for testing ideas on past prices. No broker account or key is connected.

This page does not hold results. Results change, and they live in one place: `docs/STATUS.md`.

## Read in this order

| Step | File | What you get | Length |
|---|---|---|---|
| 1 | `AGENTS.md` | The rules. They win over everything else | One page |
| 2 | `docs/STATUS.md` | Where the project stands today: every test and its result, what is believed now, what waits on the owner, what is next | One page |
| 3 | `docs/INDEX.md` | The map. Find your task in its first table and read only the files it names | Look up, do not read through |

One conflict is known and open. `AGENTS.md` names `docs/playbook/00_START_HERE.md` as the second read and says to load the playbook by default, and `docs/quality/00_READ_FIRST.md` line 12 names `docs/playbook/` as the place for what the evidence says. Only the owner may change those files. Until he decides, every playbook page opens with a dated note that sends the reader to `docs/STATUS.md`, so both routes end at the same page. The proposed wording is in `docs/decisions/morning_list_2026-11-25.md`.

Then, only if your task needs it:

- `docs/GLOSSARY.md` when a term, a test name or a rule name is not clear.
- `docs/quality/00_READ_FIRST.md` before you plan, build or review anything. It is the owner's standard.
- `docs/playbook/00_START_HERE.md` for the shape of the product and where Perplexity fits.
- `research_rig/README.md` before you run or add a test.
- `config/thresholds.yaml` before you use or change a number.

## Five things that are easy to break

The first three are the owner's rules (`AGENTS.md`, and lines marked OWNER in `docs/quality/01_the_bar.md`). Where a line adds research's own practice on top of a rule, it says so. The last two are how research keeps the map true. The owner has not been asked to approve them. The owner wrote the lines in `docs/quality/01_the_bar.md` for the Builder, the mode that builds from a kit. Research applies them to its own tests as well. That is research's choice, not his instruction.

1. Rule. A number is written once, in `config/thresholds.yaml`. Documents name the key.
2. Rule. Every rule variant is logged in the trial ledger before it is run (`AGENTS.md` hard rule 8). The held-back slice is run once for a version of a rule. The one exception, in the owner's words: "when a machine check proves the engine itself was wrong, the slice is rerun once the fix is in. That rerun is written in the trial ledger, counted as a trial and reported as a rerun". Practice on top of the rule: the test's written plan and its ledger rows are pushed before the test runs, and a rerun gets its ledger row before it runs.
3. Rule. Numbers in documents are written by a script from an output file, never typed.
4. Practice. A result or decision changes `docs/STATUS.md` in the same commit. A new, moved or retired file changes `docs/INDEX.md` in the same commit.
5. Practice. Run `python3 tools/check_repo.py` before every commit. It fails if the map is not true. `python3 tools/check_repo.py --builders` also checks that no built document was edited by hand.

## Which file wins when two disagree

1. `AGENTS.md`
2. `config/thresholds.yaml` for any number
3. `docs/quality/` for the standard of finished work and how work is planned and run. A line marked OWNER there is the owner's rule. A line marked TRANSLATED is a proposal
4. `docs/STATUS.md` for any result or the current state. This line is research's practice and is not approved yet. `docs/quality/00_READ_FIRST.md` line 12 gives that place to `docs/playbook/`, which was written before any test here. Item 5 of "Things only you can do" in the morning list asks the owner to settle it
5. A dated note in `docs/decisions/` over an undated page
6. The newer of two dated pages

Only what `docs/decisions/` records as an owner decision, with a date, is approved. Everything else that research wrote is a proposal or a working practice, even when it is worded as a step to follow.

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
│   ├── GLOSSARY.md        terms, test names and rule names in plain words
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
