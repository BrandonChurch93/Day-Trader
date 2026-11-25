# The bar

What "good" means to Brandon. A line with no label is OWNER. A TRANSLATED line is Claude's application to this project and needs his yes before it is a rule.

## Who the work is for

- Brandon Church owns this repo. Founder, AI product engineer and design engineer. Equal parts designer and engineer.
- On these builds he is not hands-on. Agents build unattended while he directs, reviews and steers.
- He arrives with most of the product already worked out in his head. Planning gets it out of his head and into the repo, in full, before anything is built. What is not written in the repo, the Builder does not know.
- What he cares about most is the experience of solving a real problem, done with taste.
- He is often on a phone or a tablet. He reads statuses there and steers from there.

## What premium means

| Principle | What it rules out |
|---|---|
| Quality before speed, always | Token budgets, screenshot caps, cheaper fallbacks, anything left at good enough |
| Everything in v1 | "Later" phases, cut-down first versions, timelines, week estimates |
| Take more care | Solving a difficulty by removing a feature, lowering a count, loosening a limit or weakening a gate |
| Truth | A picture, a label or a line of copy that disagrees with the data behind it |
| Transparency | Hidden state, static pictures standing in for real components, placeholders |
| His own, not everyone's | Template defaults and anything that looks like every other product of its kind |
| Speed is part of quality | First-load stalls and first-use stalls. Load what is needed up front, behind a designed preloader if it takes time |

The target is not an improvement on average. It is a new level: something he is proud of.

## The standard, surface by surface

### Anything on a screen

- A derby first. Three directions over the same content, published so he can flip through them. He picks one or mixes pieces.
- Then a reference prototype at the chosen direction: a working page, iterated with screenshots until he approves it. The reference ships inside the kit as the floor. Everything shipped must be clearly better than it.
- World class on phone, tablet, desktop and 4K. Touch works everywhere.
- Controls are at least 44 px on touch layouts and every control has a visible focus ring. Text contrast is at least 4.5 to 1.
- No pure black and no pure white surfaces.
- Motion is deliberate and driven by GSAP. Nothing pops in or out with no motion, outside reduced motion.
- Every state is designed. No placeholder image, empty thumbnail, sample text or unfinished state ships.
- No misalignment, uneven spacing, clipped or overflowing text, or overlapping panels.
- Screens are judged from screenshots that are opened and looked at, each with a written verdict against a checklist. Shots are named, deterministic and repeatable, and a script enforces the list.
- Anything made for him to read as a designed page (a report, a brief) uses a warm off-white background with charcoal text, not black on white.
- TRANSLATED: in this project the surfaces are whatever the owner watches and touches: a dashboard, alerts, a daily brief, a trade journal, a pause or kill control. A stock monitoring board or an admin template is a stand-in, not the product.

### 3D and cinematic motion, only if a surface uses it

- Hyper-realistic means the viewer believes they are looking at something real, even when the subject could not exist. It never means "limited to real things".
- The standard is a top-budget film or a AAA game cinematic. Never cartoon, flat, plastic or a web 3D demo.
- Vanilla Three.js owned by one `World` class.

### Copy: everything the product shows

- No em dashes. Use a period, a comma or an interpunct (·).
- Present tense, plain words, no exclamation points.
- No model version strings. They go stale with every release.
- It reads the way he speaks: serious, direct, not a sales pitch.
- A claim in copy is checked against the code and the data before it ships.

### Code

- TypeScript strict wherever TypeScript is used. No `any` unless a comment gives the reason.
- CSS Modules. Design tokens live once.
- Every constant appears once and is imported everywhere.
- Logic that can be pure is pure, with no interface code in it, and is tested.
- Almost no code comments. Keep one only when it explains a non-obvious reason that someone could otherwise undo.
- TRANSLATED: these conventions were written for his web builds. For a Python service the same intent is the strictest type checking the toolchain offers, typed data models, one config module that holds every constant, and pure tested logic for risk and sizing. `docs/research/06_architecture_and_build_process.md` section 4 already proposes `mypy --strict`, Pydantic models and full branch coverage on the risk engine, which fits.

### Documents and kits

- Plain imperative sentences, short lists and tables.
- Every number lives once, in a config file. A document names the key, never the value.
- One vocabulary table. One "which file wins" table.
- Every gate line can be checked with evidence.
- Every stop message is spelled out exactly, with the prompt that resumes from it.

### Numbers and results

TRANSLATED, all of this section. In a trading system the numbers are the product, so this is where the bar bites hardest.

- A result is a file that a script produced, stored with the command and the commit that made it. No result is typed into a document by hand.
- A gate must not be passable while the product is wrong. The backtester proves itself on fixtures with known answers before any strategy result counts: a price series with profit worked out by hand, a rule that peeks at the future and must be caught, a cost model checked against a published fee table.
- Do not shop for a pass. Rerunning a test with a new seed, window or cost number until it passes is shopping. `AGENTS.md` rules 8 and 9 already forbid the trading form of this.
- A failed strategy is a finished result. It is recorded as failed and kept.

## The Never list

OWNER, from the showcase kit, with its film terms generalized. The Builder never:

- lowers a threshold
- drops a reviewer
- rewords a rubric
- removes an item from the judged list
- picks easier comparisons
- replaces an approved reference
- cuts scope
- ships a stand-in
- reports a limit reached as a pass

TRANSLATED for this repo. The Builder also never changes a threshold, a cost assumption or a held-back test window after seeing a result, never runs the held-back slice a second time, and never counts a result that has no trial ledger entry.

## The decision rule

OWNER, from the PC builder kit, with its subject generalized. When the kit does not say, the Builder decides in this order and logs the decision in one line.

1. What does the real thing look like, or how do people who do this for real do it? Look it up.
2. Which option is truer to the data?
3. Which option takes more care? Prefer it.
4. Which option is consistent with what is already built?

Never decide by picking what is faster. Never resolve a difficulty by removing a feature, lowering a count, loosening a limit or weakening a gate.

TRANSLATED: this rule sits under `AGENTS.md`. Anything on its stop-and-ask list is never the Builder's call.

## What done means

- A phase is done only when its gate passes and the evidence is written down.
- `BUILD COMPLETE` is one block. It lists what was built with links, every item that passed, every item that a limit ended and which limit, the open items, the declined issues, the failed QA items, the time used against the budget, and one to three lines on what the Builder would improve next.
- An open item reported as open is the system working. A limit reported as a pass is the failure this bar exists to prevent.

## Cost

| Kind of cost | Rule |
|---|---|
| Build effort (tokens, agent time on his plans) | Not a constraint. Never a reason to cut scope or swap a technique for a cheaper one. Loops are still bounded so a build finishes |
| API-billed runtime spend | A hard cap, a projection gate before any expensive run, a ledger, and scripts started with the remaining budget inline. Running out of credit is a blocker, never data |
| TRANSLATED: trading capital and risk limits | The owner's numbers only. No agent sets, raises or assumes one. `AGENTS.md` governs |
