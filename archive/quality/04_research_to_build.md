# From research to build

Research is step 1 of the method in `02_how_we_build.md`: settle the product. It is finished when a kit can be written with nothing left only in a chat.

This file applies Brandon's kit method to this project. It was written as TRANSLATED. He confirmed it on 2026-11-24 with one addition, row 11, so it is now a requirement. Each row names the OWNER rule it comes from.

## What research hands over

A kit cannot be written, and no build starts, until each of these exists in the repo.

| # | Hand-over | What it looks like here | OWNER rule it comes from |
|---|---|---|---|
| 1 | Every owner decision locked | Each open item in `archive/decisions/` put to him one at a time with a recommendation, the reason and what it costs him. His answer recorded with the date | Recommend one, he picks, lock decisions one at a time |
| 2 | The product from the owner's seat | What he sees, on which device, and when. What he can do: pause, kill, approve, review. What he is told and how. Written as surfaces and a journey, not as services | `kit/01-PRODUCT.md`: audience, principles, pages, user journey, copy voice |
| 3 | An approved target for every surface | A derby and an approved reference prototype for each screen. A written spec with costs and kill criteria for each strategy, which is already the playbook's Phase 0 | Nothing is built until he has approved what it is building toward |
| 4 | One home for every number | One config file. Documents name the key, never the value. Owner numbers that are still open are marked open, not filled in | Every number lives once |
| 5 | Platform facts checked against the live thing | Library versions installed and pinned in a sandbox. API shapes read from current docs. Fees and limits dated and sourced. A list of what must be checked again at build time | Research the world as it is today before it goes in a kit. Later audits fetch the real API |
| 6 | Fixtures with known answers | Inputs and outputs worked out ahead of the build, which the engine must reproduce exactly | A gate must not be passable while the product is wrong |
| 7 | One table of limits | A count or a clock for every loop: strategy variants, critic rounds, retries, fix attempts. What happens when each is reached | Every loop has an exit |
| 8 | The stops | The few places the build needs Brandon, gathered together and placed after everything that can be built without him. Each with its exact message and its resume prompt | At most one planned stop, plus true blockers only |
| 9 | The spend rules | A cap for API-billed spend, a projection before any expensive run, a ledger | A hard spend cap, a projection gate, a ledger |
| 10 | Who the Builder is and where it runs | The agent, the machine and the permissions it has. The rule file and the stop conditions are written for that environment and measured again in the first phase | The kit is written for the Builder that will run it |
| 11 | A fresh check of the sources | Agents that did not write the research check the figures each scope decision rests on against their primary sources, before he locks that decision. Results are kept in `archive/decisions/` | Your first verdict on your own work is too kind |

Then the kit is written, audited as `02_how_we_build.md` describes, and handed off with one kickoff prompt.

## Running the research itself to the bar

| Rule | In practice |
|---|---|
| Describe the world as it is today, with a date and a source | The repo's MEASURED, STATED and UNKNOWN labels and "Last verified" dates already do this. Keep them |
| Check what you wrote | A fresh agent that did not write a report checks its load-bearing claims against the sources. The audits in `archive/decisions/` already do this |
| Recommend, do not just list | A finding ends in a recommendation and its reason. An open question for the owner arrives with the option you would pick |
| Say what could not be verified | UNKNOWN is a result. A thing that could not be checked is listed as a thing to test, not smoothed over |
| Show the work as it comes | Post findings as they land. Do not go quiet for hours and deliver one large report |
| Bound every run | Research runs had a two-hour time limit at the time. The owner removed the cap on 2026-11-25. A tool that fails three times is skipped, noted and moved past |
| No time predictions | Phases are defined by what they produce and by their evidence, not by weeks |
| No scope decided for him | A finding that changes what he asked for is a decision for him, put plainly, not a default the research adopts |

## What this file does not do

It does not say what the product is, which strategies to test, what the screens look like or which stack to use. Those are research findings and owner decisions.
