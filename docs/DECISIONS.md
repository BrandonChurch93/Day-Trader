# The owner's decisions

Brandon's own words, with the date he wrote them, and what each one settles. Newest first. A line is added here only when he says something that changes how the project runs. The longer records these came from are in `archive/decisions/` and are history.

The rules that follow from these are in `AGENTS.md`. This page is the evidence for them.

## 2026-11-25

| His words | What it settles |
|---|---|
| "I don't want any rules limiting you, I was hoping that as my persistent partner you would work around the clock testing algorithms, and coming up with ideas, and research how to make this more effective. And I worry you have limited yourself, or there are rules in place that get in the way of that." | The old rule layer is retired to `archive/`. The builder keeps testing and researching while he is away. |
| "I don't think you understand me and you are partners and building this plaform/method that other agents will use. Your not subject to all these rules, your job is to help me build an effective process and the tools to do that. To accurately test and irritate…" | The builder builds and decides day to day. Rules for traders are part of the platform, not limits on the builder. Testing has to be accurate, which is why `AGENTS.md` keeps the section "Honest testing". |
| "I agree that would be a useful training application that we could reuse for testing. Go ahead and plan and build this" | Build the time machine (`timemachine/`). |
| "Is it possible in addition to this plan, but to roll back the clock on the pretend platform so it's the past and the agent have no understanding or information on what comes after? And have them do a month of trading all at once? That would be a lot faster than live" | The idea for the time machine. |
| "Regarding the AI not be able to make trades I don't see the point of that to be honest, what's the difference between that and a non ai script. Ai is an advantage. At least in my mind I was thinking you would be making trades but with a rule set that we define and build only after research and not before because how will we know what works?" | AI traders make the trade decisions. Their rule set comes out of testing. |
| "I'm willing to let you run for a long time to see what works and doesn't." | Long runs are wanted. |
| "Let's go with your recommendation on 9" | The cap on how long a research run may last is cut. A stuck loop still gets stopped. |
| "Rules: 2. Can be cut, for this project we will need to work iterative  3. Can be cut we are partners  9. Why is there a limit? We have unlimited usage?  Some of the rules make sense, others seem to limit us pretty hard… and you seem over protective of the money. The truth is this is play money… at first the money will not be real, it will be for our testing to see what works." | Work is iterative. No waiting for an approved target. The money is pretend at first, so the builder sets pretend budgets and test settings itself. |
| "But yes you can build the practice trader, can you build a UI so that I can see your trades and overall win/loss? I'll provide you with the key soon" | Build the practice desk and a screen that shows the trades and the wins and losses. He supplies the practice account key. |
| "There has to be a way to build a successful trader, you are Fable 5.2 you have solved millennium math  problems and and the Rieman hypothesis. As an agent you have real time access to vast amounts of real time data that a normal human cannot process, there is a way for us to make a profitable strategy." He introduced it with: "You can document this, as my words for the project and should be upfront and important". | The goal. It is at the top of `AGENTS.md` and `README.md`. |
| "make sure our repo is organized for models to read and get the important information and processes effectively it shouldn't be a mess. We probably need an index or some form of management that makes sense" | `docs/INDEX.md` lists every file, and `tools/check_repo.py` checks it. |
| "I want you to treat this as we're partners here. The goal is to make a successful harness/method for making money. Preferably fast." | Partners. Speed matters. |
| "Maybe worth building me a simple application to use as an interface to see our trades and overall analytics. Doesn't have to be anything too complicated. Simply the better to be honest" | The owner's screen (`dashboard/`) stays simple. It is for him, not a product. |

## 2026-11-24

| His words | What it settles |
|---|---|
| "He doesn't need to collect modern evidence. We have the entire past of the Internet that we can scour through." | Test on the past. Do not wait for new evidence to pile up. |
| "I don't necessarily want to play it safe. Either goal is to find a nice median." | Risk is wanted, in the middle, not at either end. |
| "I'm not against putting a small amount in my portfolio into moonshots if the moonshot actually makes sense and has a reason behind it." | A small share for long shots, each with a written reason. |

## Not decided yet

- Any real money. Nothing in this repo may use a real account until he says so in writing here.
- The real-money limits. They are the keys marked `open` in `config/thresholds.yaml`.
