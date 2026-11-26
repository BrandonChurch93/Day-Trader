# Day-Trader

A platform for building and testing AI traders on US stocks and crypto with pretend money, until something earns the right to trade real money. It belongs to Brandon Church. It is built by him and his AI partner.

## The goal, in the owner's words

> There has to be a way to build a successful trader, you are Fable 5.2 you have solved millennium math  problems and and the Rieman hypothesis. As an agent you have real time access to vast amounts of real time data that a normal human cannot process, there is a way for us to make a profitable strategy.

Brandon, 2026-11-25. The aim is a method that earns money, not just a replay that looks good.

## Read in this order

| Step | File | What you get |
|---|---|---|
| 1 | [Agent guide](AGENTS.md) | The owner's goal and the honest-testing rules |
| 2 | [Status](docs/STATUS.md) | Read the top for passes, active work and owner blockers. Follow the scorecard for every scored test |
| 3 | [Queue](docs/QUEUE.md) | Check what is in work before taking the top unblocked item under Next |
| 4 | [Index](docs/INDEX.md) | The map of every file. Look things up, do not read it through |

Then only what your task needs: `docs/GLOSSARY.md` for a word, `docs/DECISIONS.md` for what the owner said, the README of the folder you work in.

## The three machines

| Machine | Folder | What it does |
|---|---|---|
| Rig | `research_rig/` | Runs a fixed rule over years of past prices in seconds. Cheap filter |
| Time machine | `timemachine/` | Sets the clock to a past day and lets an AI trader work forward one step at a time, seeing only what was known then. A month in one sitting |
| Practice desk | `practice/` | Traders use pretend money at live prices in a broker's practice account. This is the judge |

An idea moves left to right. Most stop at the first machine. That is the point of having it.

## Layout

```text
Day-Trader/
├── AGENTS.md          the rules
├── README.md          this page
├── config/            every setting, once
├── docs/
│   ├── STATUS.md      what has been tested and what happened
│   ├── QUEUE.md       what gets tested next
│   ├── DECISIONS.md   the owner's decisions, in his words
│   ├── INDEX.md       the map of every file
│   ├── GLOSSARY.md    words used here
│   ├── playbook/      what the evidence says, by topic
│   └── research/      full reports and test write-ups
├── research_rig/      the rig, and the trial ledger
├── timemachine/       the time machine
├── practice/          the practice desk
├── dashboard/         the owner's screen
├── tools/             the check that keeps the map true
└── archive/           old rule files, decision records and audits. History only
```

## Three habits that keep this repo usable

1. Settings live in `config/thresholds.yaml`. Documents name the key. Test numbers come from stored output.
2. A result changes `docs/STATUS.md` in the same commit. A new or moved file changes `docs/INDEX.md` in the same commit.
3. Run `python3 tools/check_repo.py` before a commit. It fails if the map is not true.

No real-money account is connected. This repository is research and engineering work, not financial advice.
