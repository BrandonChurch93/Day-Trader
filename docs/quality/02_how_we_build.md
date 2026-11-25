# How we build

Brandon's standing method for building without being hands-on. A line with no label is OWNER. A TRANSLATED line is Claude's application to this project and needs his yes.

## The shape

1. **Settle the product in chat.** Decisions first, details second. Brainstorm, recommend one with reasons, he picks, then lock decisions one at a time. Scope it start to finish. Research anything that describes the world today (library versions, platform limits, API shapes, prices) before it goes into a kit, and record what was found.
2. **Targets first.** For every visual surface: a derby of three directions, then a reference prototype he approves. Nothing is built until he has approved what it is building toward.
3. **Write the kit** for a model with no memory. Every constant appears once. Nothing lives only in the chat.
4. **Audit.** Once yourself, then fresh agents with the strict brief below. Fix everything. Re-audit what changed.
5. **Hand off** with one kickoff prompt. He pastes it and walks away.
6. **Review** with two roles, below. Changes arrive as numbered addenda.
7. **Close out.** Say what the build taught and propose the change to the method.

## Two roles

| Role | What it does | What it never does |
|---|---|---|
| Builder | Runs unattended from kickoff to `BUILD COMPLETE`. Decides, logs, continues | Asks Brandon a question outside a named stop |
| Partner | Interactive. Reviews the build with Brandon, takes his dislikes, writes minimal fix prompts or numbered addenda | Writes product code |

His dislikes go to the Partner, not straight to the Builder.

## Kit anatomy

```text
AGENTS.md or CLAUDE.md     Builder and Partner modes, memory protocol, stops, the quality rule, conventions, git rules
config/                    Every number, once. Kit files name the key, never the value
kit/00-README.md           Reading order, which file wins on each topic, working protocol, vocabulary
kit/01-PRODUCT.md          Name, audience, principles, every surface, the owner's journey, copy voice
kit/02..0N                 One spec file per domain
kit/07-QUALITY-BAR.md      The standard with named references, the checks, the reviewers, the one table of limits, the decision rule
kit/08-BUILD-ORDER.md      Phases, each with Read first, steps and a gate. Any planned stop with its exact message and resume prompt
kit/09-QA-GAUNTLET.md      Numbered acceptance items, each with its evidence
kit/10-KICKOFF.md          For Brandon: setup steps, every prompt, what he will see, the limits he chose
kit/PROGRESS.md            The Builder's memory, as a template
kit/data/                  Fixtures: known inputs and outputs the logic must reproduce exactly
kit/reference/             Approved references. The floor the Builder must beat
kit/addenda/               Empty until the first change after v1
```

How kit files are written:

- Plain imperative sentences, short lists and tables.
- Every gate line can be checked with evidence. Every gate line that depends on a loop ends "or its limit was reached".
- One vocabulary table and one "which file wins" table, both in `kit/00-README.md`.

OWNER, confirmed 2026-11-24: this repo already has `AGENTS.md` as its top rule file and `docs/playbook/` as its evidence layer. A kit sits beside them and `AGENTS.md` stays on top. The kit lives in `kit/` at the repo root.

## Rules every kit encodes

### Memory

- The Builder has no memory between sessions or after a compaction. `PROGRESS.md` is its memory.
- At the start of every session and after every compaction it reads `PROGRESS.md`, then every addendum, then the current phase's "Read first" files, from disk.
- It never types a number, name, id or path from memory. It looks it up every time.
- It logs like a lab notebook: what it did, what it measured, what it decided and why, what is next.
- It pushes what matters, because workspace files may not survive a task.

### The floor

- The floor is the list of work that must be done before a build may call itself complete.
- No count and no clock cancels floor work. A budget stop pauses it and it carries on when Brandon says continue.
- Nothing is ever left as a stand-in. A stand-in check cannot be satisfied by logging the stand-in.

### Limits

- Every loop has a count limit in the config and a row in one limits table.
- A round is counted when it starts, in a file that is pushed, so a restart cannot reset the count.
- Anything repeated that is not in the table gets three tries and then becomes an open item.
- A limit is not permission to stop early. While a severe or major issue is open and both count and clock allow another round, the Builder runs it.
- No single item may hold up the rest.
- The run budget is Brandon's answer to one question: how long may this run before it must stop and show me where it is? It is his cap, not a forecast. At the cap an unfinished build stops with a budget report and waits for him.
- The clock limits extra rounds, not ambition. It never changes a threshold, and nothing is marked finished because a budget ran out.

### Waits

Nothing waits without a limit.

- Jobs: each long job is logged with the time it should take. Past twice that, it is killed and started once more in smaller pieces. After a second overrun it becomes an open item and the best output that exists is used.
- Agents: a supporting agent that goes silent or runs past its limit is replaced once. If the replacement fails, the Builder does the work itself.
- Tools: a failing tool call gets three tries, then a substitute or an open item.
- A failed push is logged and tried again at the next commit. It is never a blocker.
- The Builder never waits for a reply from Brandon outside a named stop.

### Checks

Three kinds. The kind decides what a red result means.

| Kind | Tests | Red means |
|---|---|---|
| Machine check | The code: build, tests, determinism | A bug. Fixed before any reviewer sees the round |
| Measure | A number on the output | A severe issue in that round. Never a blocker |
| Deliverable check | Files that take long to make | Run only at the phase ends that name them. Still red after three tries: logged as failed and the phase goes on |

### Critics

- You are lenient about your own work. A critic is a fresh agent that has not seen the work being made and is told to find reasons to fail it.
- Every critic is a new agent in every round. It gets files, its rubric word for word and the return format. It never sees the Builder's reasoning, earlier verdicts or other critics.
- Neutral names for agents and files. Spread critic roles across model families and rotate them.
- The judged list is fixed and computed. Items can be added, never removed.
- A fail list with ids, so every verdict cites a specific fault.
- Every rubric carries the same severity anchors, so a fresh critic cannot inflate small things. The anchors below are the film kit's, with "viewer" and "frame" generalized.

| Severity | Anchor |
|---|---|
| Severe | A person would notice it in normal use |
| Major | Visible on inspection at delivery size |
| Minor | Visible only when zoomed past delivery size or by measuring against the target |

- Each phase judges only what that phase builds. Doing later work to please an early critic is how one build lost a night.
- No confirmation round that must pass twice. A second pass from fresh critics is a coin flip.
- Do not shop for a pass. A verdict belongs to one version of one thing. Never argue with a critic and never resend an unchanged item hoping for a better answer. The one exception is a critic that got a fact wrong: check the fact, note it, and send the item to one new critic.

### What the Builder does with a critic's issues

- Fix causes, not symptoms. Never tune the work to please one critic at the cost of another.
- The approved reference and Brandon's stated choices outrank every critic. An issue that asks the work to move away from them is declined, with the reason, in a list he can read. No other severe or major issue may be declined.
- If a fix would undo a change made for an earlier round, the issue is contested. Log it as an open item and do not change that thing again.
- Plateau rule: an issue that survives two rounds means change technique, not try the same thing harder. When the techniques run out it becomes an open item. It is never a blocker.

### The pass bar and what happens at a limit

- A loop ends early only when its pass bar holds: checks green, every critic at or above the pass score, no severe or major issue open.
- When a count or the clock ends a loop first, keep the best judged version, write every open severe and major issue under "Open items" with what was tried and what to try next, and move on.
- A final record round judges the frozen build once. Its scores are the final scores. It is a record and is not followed by fixes.

### Stops

- At most one planned stop, placed after everything that can be built without it. The usual one is an API key gate.
- True blockers only: a capability the kit depends on is missing and has no substitute. A plateau, a red gate, a full disk or a failed publish is not a blocker.
- `BUILD COMPLETE`, and the budget report.
- Everything else the Builder decides and logs under "Decisions made by the Builder".
- Every stop message is written out in the kit, with the exact prompt that resumes from it.
- OWNER, confirmed 2026-11-24 with a change: the stop-and-ask list in `AGENTS.md` sits on top of these: live accounts, keys, money, risk limits and changes to `AGENTS.md`. The build has one planned stop, for paper keys, placed after everything that can be built without him. The live go is not a build stop. It comes after `BUILD COMPLETE`, as an evidence gate, on a written owner decision.

### Showing the work

Brandon must never be left looking at a silent run.

- A status at least every 30 minutes of working time, in every phase, including while a job runs or agents work. One at every phase gate. One that opens every task. Never more often than every 10 minutes. He wants a steady stream, not a flood.
- A status is two or three lines (phase, what changed, what is next, time used out of time allowed), one to four pictures with captions, and a link.
- Pictures are shown inline in the thread. A file he has to download does not count.
- It shows what the Builder and its agents are looking at. Unfinished and bad output is shown.
- If he writes in the thread he is steering. Apply it, log it under "Notes from Brandon" and carry on.
- Commit and push with every status.
- A status is not a question and not a pause.
- OWNER, confirmed 2026-11-24: here the pictures are charts, tables and screenshots: an equity curve, a cost table, a screen as it is being built.

### Spend, secrets and git

- Spend: a hard cap, a projection gate before any expensive run, a ledger.
- Secrets: the Builder never reads the env file. A check script prints present or missing, and empty counts as missing. Confirm `git status` is clean of secrets before the first push.
- Git: the Builder commits and pushes to the one repo Brandon names, after every phase gate and at `BUILD COMPLETE`. He never pushes by hand.
- Never force push, rewrite pushed history or delete a branch on the remote.
- Fetch and merge, never rebase, at the start of every phase and before every push, because addenda arrive while the build runs.

### Research during the build

- Allowed and expected. When the kit says verify at build time, open the docs and record what was found before coding.
- Pin versions after verifying them.

## The audit

Order: once yourself, then a fresh agent, fix every finding, then one more fresh agent on the areas that changed. Keep going only while an auditor finds something that would stall the build or let it finish falsely. Later audits check platform facts against the live thing: fetch the real API, scaffold the real tool.

### The loop audit, done yourself

- Search every kit file for: until, repeat, again, retry, keep going, wait, loop, as long as, each time. Every hit names a config key that limits it, or states plainly that it does not wait.
- Walk the build order assuming every critic fails every round and every optional tool is missing. Every gate must still be reachable, and the walk must end at `BUILD COMPLETE` with honest open items.
- Check the restarts: a task that starts mid-phase continues it, and a task that starts after completion prints the stored block and builds nothing.
- Check the bar cannot drop quietly: the Never list is in the rule file word for word, and a limit reached is written as open items.
- Then the usual: contradictions between files, names, counts and paths, every config key used exists, every key in the config is used, every command a phase runs is defined.

### Brief for a fresh auditing agent

```text
Read every kit file fully. Do not edit anything. Report only issues that would (a) stall the unattended Builder or let any loop or wait run without a limit, (b) let it declare done falsely or report a limit reached as a pass, (c) lower the quality bar without saying so, (d) contradict another file in a number, name, count, path or phase, or (e) rely on a tool or platform behavior that is wrong or cannot be verified as written. Walk the build order once assuming every critic fails every round and say where the walk gets stuck. Ignore style and any judgment call the Builder is allowed to make. Numbered list, file, exact phrase, why in one line, one-line fix, most severe first, at most 25. End with the single most dangerous issue for an unattended run.
```

OWNER, confirmed 2026-11-24 with one addition, for this repo: (f) any path by which model output could reach an order, against `AGENTS.md` rule 1, (g) a gate that can pass with a wrong backtester or a rerun held-back test, (h) a money number that the owner did not set, (i) any way to switch from paper to live without a decision record.

## Prompt patterns

Every prompt Brandon sends an agent is direct. It opens with the decision or the request. No thanks, no praise.

Kickoff:

```text
BUILD MODE. Read kit/00-README.md and build the whole product from the kit. Work every phase in kit/08-BUILD-ORDER.md in order, verify every gate, log everything in kit/PROGRESS.md, and stop only at <the named stop or BUILD COMPLETE>.
```

Resume:

```text
BUILD MODE. Continue from kit/PROGRESS.md.
```

Status, usable at any time:

```text
Post a status now: the phase, what changed, what is next, the clock, and the current pictures shown inline. Do not stop working.
```

## Why the rules exist

Each rule above was paid for by a build that went wrong without it.

| What happened | The rule it produced |
|---|---|
| A kit said there was no limit on rounds and asked for a top score on gray boxes. The build spent about twelve hours moving cameras before any real work began | Count limits. A lower pass score for early stand-ins. Each phase judges only what it builds |
| Limits held, but one round ran for many hours with nothing pushed | The clock, the job watchdog, the status gap |
| Four hours of unjudged polishing before the first review round | Work goes to its first round as soon as none of it is a stand-in |
| A critic faulted work that matched the approved reference | The approved reference outranks every critic |
| A run regenerated one image for one critic for most of its time and showed nothing for ninety minutes | A take limit per item, and each item posted as it finishes |
| Brandon went most of a day without pictures, and what was shared had to be downloaded | Inline pictures at least every 30 minutes |
| A plan alone took over eight hours | OWNER, confirmed 2026-11-24: research and planning runs carry a time limit too, the way reference runs already do. The cap is `research_run_cap_hours` in `config/thresholds.yaml` |
| A stand-in could be logged away and the build still called complete | The stand-in check cannot be met by logging it |
| An unattended app build sent every screenshot back to fresh critics again and again. A day and a half in, it was a third of the way through | Critic rounds are bounded per item. As good as possible without taking forever |
