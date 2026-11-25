# The owner's decisions

Brandon's own words, with the date he wrote them, and what each one settles. Newest first. A line is added here only when he says something that changes how the project runs. The longer records these came from are in `archive/decisions/` and are history.

The rules that follow from these are in `AGENTS.md`. This page is the evidence for them.

## 2026-11-25

| His words | What it settles |
|---|---|
| "You are my partner on this, me and you are building a method, process, harness, whatever you wanna call it to build and facilitate AI trading methods to see what actually works." "You were not confined to any of the rules here. The rules are simply being built by me and you to get the results that we want, more profitability." "this is a Greenfield project and I don't want anything limiting you" | Said a second time so it is clear. The partners are the architects. Rules in this repo are for the trader agents and are changed by the partners to make the traders more profitable. Nothing limits the builder. |
| "there's really two types of documentation that we're doing here. We're doing research, and then we're figuring out the harness or whatever we're calling it, that agents will abide to when doing trades. You and me or observers here, architects, building out this thing. So if you're limited by rules, then you're unable to do your part of the job properly." | Two kinds of writing: research, and the harness the traders follow. `AGENTS.md` is laid out that way. |
| "It makes sense to me to build our own application that the agents can access. We can connect to stock APIs and we could set it up so the agent cannot access current prices, and we will put them at a moment in time, whether that's a week ago or a month ago, and we can essentially let them do their trades in super speed. to see how they play out. I'll leave it up to you to figure out what actually makes sense and closest to a real world environment." | The time machine (`timemachine/`) is the main test bed. How close it is to the real market is the builder's call. |
| "That way we can test all these different algorithms and we can keep going around the clock, see what actually works and why it worked. Did it look at the news? Did it have a certain pattern on screen, and so on." | Every replay records what the trader looked at and why it traded, so a result can be traced to its cause. |
| "Now there is no money involved, soon there will be play money involved, and that's where the fun part starts, and at first the first bit of money I put in the platform, whether it's $300 or $500, is in my mind already gone. It's just going to be for testing purposes. Of course I'd like to keep the money and make it profitable, but this is a risk, and I understand that, but weeks from now once this is matured, and hopefully are seeing progress and I put more money on it, yes we need to be a bit more strict with our money and only use the methods that worked" | Three stages of money: none now; then a small first amount he treats as test money; then more, with tighter limits and only methods that worked. |
| "I would love for you to be working around the clock, spitting up new agents, looking up new methods, testing them out, researching what works" | The builder starts agents, finds methods and tests them without asking. |
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
