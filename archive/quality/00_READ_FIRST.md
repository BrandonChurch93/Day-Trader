# Quality bar: read first

Written 2026-11-24 by Claude, the assistant Brandon plans his builds with. The source is his own build skills (the hands-off build playbook, the showcase kit, the 3D asset playbook) and the kits already written from them. Nothing here is invented for this project unless it is marked TRANSLATED.

This folder tells every agent what "good" means to the owner and how work is run so it gets there. It plans nothing. It picks no strategy, no stack and no design.

## Where this folder sits

| Topic | Winner |
|---|---|
| Trading safety, the order path, model tiers, stop and ask | `AGENTS.md` |
| What the evidence says, topic by topic | `docs/playbook/` |
| What was decided, and when | `archive/decisions/` |
| The standard of the finished product, how a build is planned and run, how to work with Brandon | `archive/quality/` |

If this folder and `AGENTS.md` ever disagree, `AGENTS.md` wins and the conflict gets a dated note in `archive/decisions/`.

## Two labels

- OWNER: a standing rule Brandon set himself, in his skills, his kits or his own words. Treat it like a rule in `AGENTS.md`.
- TRANSLATED: Claude's application of an OWNER rule to a trading system. Brandon has not confirmed it. Treat it as a proposal and put it to him before it becomes a rule.

A line with no label is OWNER.

On 2026-11-24 Brandon confirmed every TRANSLATED line in files 00 to 04, five of them with changes. Those lines are now rules and read "OWNER, confirmed 2026-11-24". The record is `archive/decisions/0003-quality-bar-adopted.md`. A TRANSLATED line added after that date is a proposal again. File 05 stays TRANSLATED: it is a list of observations, and its status table says what was done about each.

## The bar in one page

Owner change, 2026-11-25, for this project only: points 2 and 3 below are cut. His words: "2. Can be cut, for this project we will need to work iterative" and "3. Can be cut we are partners". Work here is iterative, and a build does not wait for an approved target. Where another file in this folder still says otherwise, this line wins. The record is `archive/decisions/0007-owner-goal-and-practice-trader-2026-11-25.md`.

1. **Built once, built premium.** The target is a finished product Brandon is proud of and never has to rework. Quality comes before speed, always. No phase is left at good enough, and the harder right way beats a cheaper fallback.
2. **The whole product in v1.** Scope it start to finish. No "later" phases, no timelines, no week estimates. He does not ship halfway. OWNER, confirmed 2026-11-24: the playbook's capital gates (paper, shadow, tiny live, scale) are evidence gates, not deferred scope. The software that runs every one of them is finished in v1. Live order code is tested on paper only and is reported as an open item until he approves live.
3. **Targets before work.** Nothing is built until he has approved something concrete to build toward: a reference image or working prototype for anything visual, a written spec with its numbers for anything else. Agents iterate well against a target and badly against a description.
4. **A floor, a ceiling and a bar that never touch.** The floor is the work that must be done before anything may call itself complete. The ceiling is the counts, clocks and spend caps that bound every loop. The bar is the pass criteria, and it never moves. When a limit is reached, the open issues are reported as open. They are never called a pass.
5. **Written for a model with no memory.** Everything an agent needs is in the repo. Every number lives once and is named everywhere else. No two files disagree. A progress file is the Builder's memory.
6. **Prove it.** Numbers come from data and a command, never typed from memory. Every gate names its evidence. Your first verdict on your own work is too kind, so fresh agents that never saw your reasoning judge it.
7. **He can always see it.** No silent runs. A short status with pictures shown in the thread at least every 30 minutes of working time. Unfinished and bad work is shown, not held back.
8. **Decide, log, continue.** Outside a short list of named stops, the agent makes the call, writes it down and keeps working. Never decide by picking what is faster.
9. **Every loop and every wait has a limit.** Nothing runs forever, nothing blocks a build from finishing, and nothing lowers the bar to finish sooner.
10. **What he looks at is designed.** He is equal parts designer and engineer. Any surface a person sees is a designed product at the level of his best work, never a default template.
11. **Plain and honest with him.** Say what the evidence says, what a choice costs and exactly what he is approving. Lists over paragraphs. No hype and no time predictions.
12. **Three kinds of cost, three rules.** Build effort is never a reason to cut quality. API-billed runtime spend has a hard cap, a projection before any expensive run, and a ledger. OWNER, confirmed 2026-11-24: trading capital and risk limits are the owner's numbers only, as `AGENTS.md` already says.

## Files

| File | Read it when |
|---|---|
| `00_READ_FIRST.md` | Always. This page is the default load. |
| `01_the_bar.md` | Before any design decision, before judging any output, before calling anything done. |
| `02_how_we_build.md` | Before planning a build, writing a kit, auditing one or running one. |
| `03_working_with_the_owner.md` | Before asking Brandon anything, proposing anything or writing a prompt he will send. |
| `04_research_to_build.md` | During research. It lists what research has to hand over before a kit can be written. |
| `05_repo_review_2026-11-24.md` | Once. A dated review of this repo against the bar. Delete it when its items are closed. |

## See the bar, do not only read about it

Two public repos hold complete kits written to this standard. Reading one is faster than reading a description of one.

| Repo | What it shows | Start with |
|---|---|---|
| `BrandonChurch93/PC-Desktop-Builder` | An interactive app built unattended, start to finish, by a Claude Code Builder with a Partner reviewing | `CLAUDE.md`, `kit/00-README.md`, `kit/07-QUALITY-BAR.md` (the five tests, the fail list with ids, the critic rules, the decision rule), `kit/09-QA-GAUNTLET.md`, `kit/data/fixtures.json` |
| `BrandonChurch93/Sun-Flower-Perplexity` | A kit written for Perplexity Computer as the Builder | `AGENTS.md` (memory, the three things that never touch, waits, stops, showing the work, the Never list), `kit/07-QUALITY-BAR.md`, `kit/08-BUILD-ORDER.md`, `config/showcase.json` |

Those kits are about 3D and film. Take the method from them, not the subject.

## Wiring this folder in

Done on 2026-11-24 with Brandon's yes. `AGENTS.md` points here under "How to use the docs", and `README.md` lists this folder in its reading order and its layout tree. The adoption record is `archive/decisions/0003-quality-bar-adopted.md`.
