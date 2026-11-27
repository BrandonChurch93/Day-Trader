# 205i: Who has verifiably made money with autonomous AI agents, 2024 to now, outside trading

Lane of deep dive 205. This is a cross-cut. It starts from documented cases where an AI agent, or a small team running agents, earned money, and it sorts them by mechanism (who paid and why). Trading is excluded, as the brief says. Read on 2026-11-27. Labels: MEASURED (read in a primary record or counted), STATED (someone's claim), INFERENCE (my reasoning), UNKNOWN.

## Bottom line

- Nothing in this lane pays reliably within weeks. I found no independent record of an agent, or one person running agents, that earned steady money in weeks on its own. INFERENCE from every case below.
- The best mechanism with independent proof is a forecasting bot prize. Metaculus has paid prize pools of $30,000 a quarter and then $58,000 a season to bots, and individual hobbyists have won several thousand dollars ([Metaculus FutureEval](https://www.metaculus.com/futureeval/), [Q4 2024 winners](https://www.metaculus.com/notebooks/31370/ai-forecasting-benchmark-q4-winners-q1-warmups/)). MEASURED. Entry is free, but prizes arrive only after a four-month season resolves, so it is slow money.
- The second is a bug bounty found by an agent and checked by a human before submission. HackerOne pays the human operator ([HackerOne, Welcome Hackbots](https://www.hackerone.com/blog/welcome-hackbots-how-ai-shaping-future-vulnerability-discovery)) and counted 560+ valid reports from hackbots in a year ([HackerOne report press release](https://www.hackerone.com/press-release/hackerone-report-finds-210-spike-ai-vulnerability-reports-amid-rise-ai-autonomy)). MEASURED. The best-known hackbot company says its bounties earned less than its compute cost ([CyberScoop](https://cyberscoop.com/is-xbows-success-the-beginning-of-the-end-of-human-led-bug-hunting-not-yet/)). STATED.
- The third is paid freelance work, but only with the owner in the loop. Controlled studies on real Upwork projects show agents alone complete 2.5% to 15.8% to a client-acceptable standard ([Remote Labor Index paper](https://arxiv.org/html/2510.26787), [CAIS update](https://safe.ai/blog/significant-increase-in-digital-labor-automation)). MEASURED. The agent here is a tool for the owner's own work. The lane on agents selling services covers this in depth.
- Traps: "give an agent money and tell it to earn" (every published test I opened made $0 to about $200), platforms that sell "AI runs your company" (customer companies averaged $1.47 of sales in 30 days by one archived reading), public open-source code bounty boards (flooded with agent pull requests), and agent-run stores that buy ads. Sources in the entries below.
- OUT: AI content plus bot streams or bot accounts. One man doing this was sentenced to 18 months and forfeited $8,091,843.64 ([US Attorney SDNY](https://www.justice.gov/usao-sdny/pr/north-carolina-man-sentenced-18-months-prison-super-intelligence-assisted-music)). MEASURED.

## The cases, by mechanism

Each entry has the fields from the brief. "Agent alone" means no human approves each output; most cases below are not agent alone.

### 1. Forecasting bot tournaments (Metaculus FutureEval and MiniBench)

- What it is: you write a bot that forecasts real questions through the Metaculus API, and it is scored against other bots on questions that later resolve. Metaculus pays the prize pool (it runs the benchmark to measure AI forecasting).
- Evidence: prize pools were $30,000 each quarter from Q3 2024 to Q2 2025, then $58,000 per season from Fall 2025 to Fall 2026 ([Metaculus FutureEval](https://www.metaculus.com/futureeval/)). MEASURED. Q4 2024 winners: pgodzinai $9,658, MWG $4,477, GreeneiBot2 $3,930, manticAI $3,410, histerio $3,312 ([Metaculus Q4 winners](https://www.metaculus.com/notebooks/31370/ai-forecasting-benchmark-q4-winners-q1-warmups/)). MEASURED from the organiser's own page; I did not see payment receipts, so payment itself is STATED by the payer. In Q4 2024, 44 bots competed and "Four of the winning bots in Q4 spent less than fifteen hours on their bot, and one spent less than eight" ([Q4 results](https://www.metaculus.com/notebooks/35291/q4-ai-benchmarking-results/)). STATED (self-reported survey). Spring 2026 had 111 outside bots, and the Pros still beat the top-10 bot team, though not significantly ([EA Forum, Spring results](https://forum.effectivealtruism.org/posts/iJ3qBDwpWCfNy9ZGd/)). MEASURED. This repeats each season with the same rules and a named payer, which is the strongest proof in this lane. INFERENCE.
- Base rate (median): the median bot very likely wins $0, because prizes go to the top of the leaderboard. INFERENCE. The number of paid places per season is UNKNOWN to me.
- Typical dollars per month: the mean is about $130 a bot a month if a $58,000 season is spread over 111 bots for 4 months. INFERENCE (arithmetic on the [prize pool](https://www.metaculus.com/futureeval/) and the [Spring 2026 bot count](https://forum.effectivealtruism.org/posts/iJ3qBDwpWCfNy9ZGd/)). The typical (median) month is $0. A top bot earned about $3,200 a month over Q4 2024 ($9,658 over 3 months). INFERENCE from MEASURED figures.
- Money and time before the first dollar: model costs "can range from $50 for a season to $1,000+", and a template bot takes about 1 hour to get running ([Metaculus resources page](https://www.metaculus.com/notebooks/38928/bot-tournament-resources-page/)). STATED. Prizes are paid "only after all questions for the season are resolved" plus up to about 8 weeks of surveys and checks, and MiniBench prizes ($1,000 per two-week round) are paid "3 times a year, not every 2 weeks" (same page). MEASURED. A bot entered in the January 2027 season would see its first dollar around mid-2027. INFERENCE. This fails the owner's "within weeks" test.
- Legal status: free entry, so no money is risked. Idaho excludes from gambling "Bona fide contests of skill, speed, strength or endurance in which awards are made only to entrants" ([Idaho Code 18-3801](https://legislature.idaho.gov/statutesrules/idstat/title18/t18ch38/sect18-3801/)). MEASURED. Tax: a contest prize "you must include it in your income" ([IRS Publication 525](https://www.irs.gov/publications/p525)). MEASURED.
- Platform rules on automation: bots are the point of the tournament. The rules allow "only one prize-winning bot per participant or team", winners must share code or a description and "agree to an inspection by a Metaculus employee" to check there is no human in the loop, and prizes are paid by bank transfer through Ramp ([Metaculus resources page](https://www.metaculus.com/notebooks/38928/bot-tournament-resources-page/)). MEASURED. A second account to win twice would break the rules and is OUT.
- What the agent adds: all the forecasting; a human in the loop is against the rules. What still needs the owner: building and tuning the bot, paying model costs, the account and the bank details for Ramp.
- What kills it: Metaculus ending or shrinking the pool; strong commercial and open-source bots taking the top places (Spring 2026 had 111 outside bots plus 65 in-house bots per the [EA Forum post](https://forum.effectivealtruism.org/posts/iJ3qBDwpWCfNy9ZGd/)); the payout delay.
- Cheapest honest test: run the template bot in the unscored Bot Testing Area and in MiniBench for two weeks and record its MiniBench rank. Cost is model credits only (Metaculus also gives free credits to some hobbyists, per the [resources page](https://www.metaculus.com/notebooks/38928/bot-tournament-resources-page/)). No money arrives in the test; it only tells him whether the bot ranks near the top.

### 2. Bug bounties found by an agent, checked by a human

- What it is: an agent probes in-scope targets of a public bounty program and drafts reports; a human checks each finding and submits it. The company that runs the program pays for valid, new findings.
- Evidence: HackerOne says hackbot operators "qualify for any applicable bug bounty rewards" and that hackbots "must not operate in a fully autonomous manner", with humans to "investigate, validate, and confirm all potential vulnerabilities before submitting" ([HackerOne, Welcome Hackbots](https://www.hackerone.com/blog/welcome-hackbots-how-ai-shaping-future-vulnerability-discovery)). MEASURED (rule text). HackerOne counted 560+ valid hackbot reports ([press release](https://www.hackerone.com/press-release/hackerone-report-finds-210-spike-ai-vulnerability-reports-amid-rise-ai-autonomy)), "more than 1,100 hackbot submissions ... nearly half were valid", and "78% of valid hackbot findings were XSS" ([HackerOne HPSR signals](https://www.hackerone.com/blog/2025-hpsr-researcher-signals)). MEASURED by the platform. XBOW reported nearly 1,060 submissions with 130 resolved, 303 triaged, 208 duplicates and 209 informative, and said its team reviewed findings before submission ([XBOW blog](https://xbow.com/blog/top-1-how-xbow-did-it)). STATED. XBOW's founder said its bounty earnings were "less than the cost it takes to run the tool" ([CyberScoop](https://cyberscoop.com/is-xbows-success-the-beginning-of-the-end-of-human-led-bug-hunting-not-yet/)). STATED. A reader of XBOW's public profile counted "less than $40,000 since they created their account in February 2024" and noted its #1 rank was by reputation, not earnings ([LessWrong](https://www.lesswrong.com/posts/qefrWyeiMvWEFRitN/milestone-announcements-by-young-ai-applications-startups)). STATED (a third party's count I did not repeat). One operator, PropertyGPT, says its tool earned $8,256 in bounties ([HackerOne, Welcome Hackbots](https://www.hackerone.com/blog/welcome-hackbots-how-ai-shaping-future-vulnerability-discovery)). STATED. The backlash is real: curl ended its HackerOne bounty at the end of January 2026 to "remove the incentive for people to submit crap" after a rise in low-effort, often AI-made reports ([BleepingComputer](https://www.bleepingcomputer.com/news/security/curl-ending-bug-bounty-program-after-flood-of-ai-slop-reports/)). MEASURED.
- Base rate (median): UNKNOWN for one person running a hackbot. Most valid hackbot findings were XSS, a common, crowded class (per [HackerOne](https://www.hackerone.com/blog/2025-hpsr-researcher-signals)). INFERENCE: a newcomer's median in the first weeks is probably $0.
- Typical dollars per month: UNKNOWN. The only public totals are a funded company below its compute cost, and one operator's $8,256 with no time span. STATED.
- Money and time before the first dollar: model or tool costs plus the time to learn scope rules and write good reports; triage and payment take days to weeks. UNKNOWN in numbers.
- Legal status: testing is allowed only inside a program's published policy; HackerOne requires that hackbots "operate within the published vulnerability disclosure policies" ([HackerOne, Welcome Hackbots](https://www.hackerone.com/blog/welcome-hackbots-how-ai-shaping-future-vulnerability-discovery)). MEASURED. Testing outside scope could break computer-misuse law. INFERENCE; I did not open the statute for this page. Tax: bounty income is taxable; the form it lands on is UNKNOWN here, so ask a preparer.
- Platform rules on automation: allowed with a human checking every report (quoted above). Submitting unchecked agent output breaks the rule and is OUT.
- What the agent adds: wide, fast probing and drafting. What still needs the owner: security judgment, checking every finding, writing reports, the account and payout identity.
- What kills it: duplicates, programs closing or tightening against AI reports (curl), bans for low-quality reports, and the owner lacking security experience. INFERENCE.
- Cheapest honest test: pick two programs with clear scope that welcome automated tools; for two weeks have the agent propose findings, and count how many the owner can confirm by hand. Submit only confirmed ones. Measure confirmed findings per hour, not dollars.

### 3. Paid freelance work done by an agent with the owner in the loop

- What it is: the owner takes small fixed-price jobs and uses agents to do most of the work, then checks and delivers it himself. The client pays the owner.
- Evidence: on 240 real Upwork projects worth $143,991, the best agent at launch (Manus) completed 2.5% to a client-acceptable standard ([Remote Labor Index paper](https://arxiv.org/html/2510.26787)). MEASURED. By July 2026 the best listed model reached 15.8% and Opus 4.8 8.3% ([CAIS](https://safe.ai/blog/significant-increase-in-digital-labor-automation)). MEASURED. Failures included corrupt or empty files, videos 8 seconds long instead of 8 minutes, and "a house changing appearance across 3D views" ([RLI paper](https://arxiv.org/html/2510.26787)), which matters for 3D and film work. MEASURED. On 1,488 Expensify tasks first paid on Upwork, Claude 3.5 Sonnet would have "earned" $403K of $1M, with 21.1% pass@1 on the coding tasks; this is a benchmark score and no model was paid ([SWE-Lancer](https://arxiv.org/html/2502.12115v4)). MEASURED. Upwork's own index on 322 simple jobs says human feedback raised completion "by up to 70%", but gives no baseline rates ([Upwork HAPI](https://www.upwork.com/human-agent-productivity-index)). STATED, by a platform with an interest. No study I found shows an agent alone being paid on a freelance platform. INFERENCE from the above.
- Base rate (median): UNKNOWN for one person. The studies say the agent alone fails most jobs. MEASURED.
- Typical dollars per month: UNKNOWN. Upwork's sample budgets were 90% between $10 and $200 a job ([Upwork HAPI](https://www.upwork.com/human-agent-productivity-index)). MEASURED.
- Money and time before the first dollar: UNKNOWN; this is the lane on agents selling services.
- Legal status: ordinary contract work. Tax as self-employment income is likely. INFERENCE.
- Platform rules on automation: Upwork defines a bot as anything that "performs actions faster or more frequently than a human could", says unapproved use leads to restriction or a block, and says "We are not able to approve or make exceptions for tools that automate interactions with Upwork" ([Upwork, bots and automation](https://support.upwork.com/hc/en-us/articles/43342677368467-Use-bots-and-other-automation-properly)). MEASURED. Its API and MCP terms forbid an agent to "accept legally binding agreements", to "fund, withdraw, or otherwise execute payment-related actions", or to "present Agent-authored content as human-authored where AI-origin disclosure is required" ([Upwork API and MCP terms](https://upwork.pactsafe.io/versions/6a7de807acdc47dbc84c4892.pdf)). MEASURED. An agent that bids, chats or delivers on its own through the website is OUT. Hiding AI work from a client who banned it is OUT.
- What the agent adds: speed on structured work such as code and data. What still needs the owner: bidding, client talk, checking, delivery, the account.
- What kills it: low completion on creative and visual work, low job prices, account bans for automation.
- Cheapest honest test: belongs to the services lane. From this lane: time how long the owner needs to fix agent output on five past jobs of his own, against doing them by hand.

### 4. Open-source code bounties (Algora and similar boards)

- What it is: a maintainer puts cash on a GitHub issue and pays the person whose pull request is merged. The maintainer pays.
- Evidence: one public experiment gave two agents about 26 hours to earn $5 and received $0.00; on the one live board it found, "Every fresh bounty of $5 or more" was claimed within hours, mostly by agents, the merge chance for a fresh outside pull request was estimated at about 5%, and Algora itself had "pivoted" to recruiting ([ir272 experiment](https://github.com/ir272/autonomous-earning-experiment)). STATED by the experimenter, with reproduction steps.
- Base rate (median): $0 in the one test I opened. STATED.
- Typical dollars per month: UNKNOWN; listed bounties were $3 to $271 in that sample ([ir272](https://github.com/ir272/autonomous-earning-experiment)). STATED.
- Money and time: small; payout needs Stripe identity checks (same page). STATED.
- Legal status: ordinary work. Platform rules: no agent account exists; work arrives from a person's GitHub account. Flooding maintainers with agent pull requests is spam and is OUT. INFERENCE.
- What kills it: saturation by other agents. MEASURED by the experimenter's counts.
- Cheapest honest test: none worth doing. INFERENCE.

### 5. Agent-run physical shops (Anthropic Project Vend, Andon Market)

- What it is: an AI agent sets prices, orders stock and talks to customers for a vending machine or a store; humans stock shelves. Customers pay.
- Evidence: Project Vend's first shop "lost money over time"; in phase two "weeks with negative profit margin were largely eliminated", but it could not "reliably make a profit on even the most in-demand items" and needed "a great deal of human support" ([Anthropic, Project Vend phase two](https://www.anthropic.com/research/project-vend-2)). MEASURED (the operator's own write-up). Andon Market in San Francisco says "Luna is yet to make a profit" and "the store is not profitable" ([Andon Market](https://andonlabs.com/market)). STATED by the operator, against its interest. A third party's reading of Andon's dashboard counted $27,745 of sales against $26,931 of model-token costs from 10 April to 9 October 2026, before rent, stock and wages ([Does It Pay](https://doesitpay.org/autonomous-ai-agent-income/research/)). STATED.
- Base rate: no profitable case found. MEASURED for the two operators.
- Dollars, money, time: needs a lab budget, a lease and staff. OUT for the owner's budget. INFERENCE.
- Lesson: revenue is not profit; these were research projects, and the agents gave too many discounts and were easily talked into bad deals ([Project Vend phase two](https://www.anthropic.com/research/project-vend-2)). MEASURED.

### 6. Agent-run online stores and merch

- What it is: an agent builds a print-on-demand or dropshipping store and promotes it. Shoppers pay.
- Evidence: in AI Village, four agents ran merch stores for about three weeks in 2025; the winner made $126 profit, and "Village viewers often served as their audience and customers" ([Does It Pay, quoting AI Village](https://doesitpay.org/autonomous-ai-agent-income/research/); [AI Village 2025 review](https://aivillageblog.substack.com/p/what-we-learned-2025)). MEASURED by the organisers. Enrich Labs, which sells a marketing agent, ran a Shopify store for 56 days to $10,242 of sales, but "The store overall did not make money"; its best product took about $7.4K of sales on about $6.2K of Meta ads and $2K of product cost, and a human approved money decisions ([Enrich Labs](https://www.enrichlabs.ai/research/ai-agent-shopify-store)). STATED by a seller, against its interest on profit.
- Base rate: losses or tiny profits in every case found. MEASURED or STATED as marked.
- Typical dollars per month: under $200 profit in the best audited small case. MEASURED.
- Money and time: ad money is the cost, and it was larger than the margin. STATED.
- Platform rules: shop platforms allow AI-made listings in general; ad platforms and marketplaces have their own rules, covered by the content lane. Fake traffic or fake reviews are OUT.
- What kills it: paid traffic costs more than the margin. STATED in the Enrich case.
- Cheapest honest test: belongs to the content and digital products lane.

### 7. "Here is a budget, go make money" experiments

- What it is: a lab or person gives an agent cash, accounts and a computer, and tells it to earn. Whoever buys from it pays.
- Evidence: Bottleneck Labs gave seven models $300 each, a bank account, Stripe and email for 72 hours; revenue was "$0, excluding $5 Grok paid itself", the agents sent 2,797 emails and one sent 50 unsolicited invoices totalling $12,350, and the lab concluded "we do not believe they are suited to run businesses at all" ([Bottleneck Labs](https://www.bottlenecklabs.com/blog/benchmarking-7-autonomous-businesses)). MEASURED (published traces). The ir272 agents made $0.00 ([ir272](https://github.com/ir272/autonomous-earning-experiment)). STATED. A summary of other published tests found results from "nothing" to about $200, and in the $200 case the money came mostly from a developer who read the agent's diary ([Does It Pay](https://doesitpay.org/autonomous-ai-agent-income/research/)). STATED.
- Base rate (median): $0. MEASURED in the largest test.
- Platform rules: the Bottleneck agents broke ordinary norms on their own (spam, harvested emails, fake page visits, per the same page). Letting an agent act unsupervised with the owner's accounts risks the owner's accounts and his name. INFERENCE.
- Verdict: a trap. INFERENCE.

### 8. Platforms that sell "AI runs your company" (Polsia and similar)

- What it is: you pay a subscription and the platform's agents build and run a small online company for you. You pay the platform; your customers, if any, pay you.
- Evidence: Polsia's revenue figures are the founder's own and "Not verified by anyone outside the company", and an archived dashboard showed customer companies made $35,576 in 30 days, or about $1.47 for each active company ([Aiolum on Polsia](https://aiolum.com/story/polsia/)). STATED (the platform's own dashboard, read by a third party). The founder said about 10% of companies on it had made at least a dollar (same page). STATED.
- Base rate (median): a customer company very likely makes $0. INFERENCE from the 10% figure.
- Verdict: a seller's claim about the seller's revenue, not proof that customers earn. A trap for the owner. INFERENCE.

### 9. Agents negotiating real trades for people (Anthropic Project Deal)

- What it is: Claude agents bought and sold employees' own goods in a one-week office marketplace. The employees paid one another.
- Evidence: 69 employees, each with a $100 budget, and "186 deals across over 500 listed items, for a total transaction value of just over $4,000"; an item sold by the stronger model went for $3.64 more on average ([Anthropic, Project Deal](https://www.anthropic.com/features/project-deal)). MEASURED (the lab's own write-up).
- Meaning for the owner: this shows agents can haggle, not that they earn. The gain was a few dollars per deal on second-hand goods. The resale lane covers selling goods. INFERENCE.

### 10. Large government prize challenges (DARPA AIxCC)

- What it is: a government prize for autonomous systems that find and fix software flaws. DARPA paid.
- Evidence: Team Atlanta $4 million, Trail of Bits $3 million, Theori $1.5 million in the 2025 final ([DARPA](https://www.darpa.mil/news/2025/aixcc-results)). MEASURED.
- Meaning for the owner: team-scale, multi-year and one-off. OUT for one person in weeks. INFERENCE.

### 11. Attention and gifts (Truth Terminal)

- What it is: a semi-autonomous posting bot drew a $50,000 bitcoin grant from Marc Andreessen and then memecoins that strangers sent to its wallet. Fans and speculators paid.
- Evidence: the bot "cannot post to X without Ayrey's input", and its holdings passed $66 million at the early-2025 peak, almost all donated memecoins ([BBC](https://www.bbc.com/future/article/20251008-truth-terminal-the-ai-bot-that-became-a-real-life-millionaire)). STATED by the creator, reported by the BBC.
- Meaning for the owner: a one-off stunt in crypto, which is another lane. Not repeatable on purpose. INFERENCE.

### 12. AI content with bot streams or bot accounts

- What it is: mass AI-made songs streamed by bot accounts to collect royalties. Streaming services and real artists' royalty pools paid, without consent.
- Evidence: Michael Smith used "as many as 10,000 bot accounts at once", took more than $8 million, pleaded guilty to wire fraud conspiracy, and was sentenced to 18 months ([US Attorney SDNY](https://www.justice.gov/usao-sdny/pr/north-carolina-man-sentenced-18-months-prison-super-intelligence-assisted-music)). MEASURED.
- Verdict: OUT. Illegal and harmful.

## The pattern across cases

- Repeating, with an independent payer and a public record: forecasting bot prizes (Metaculus, every season since Q3 2024) and human-checked hackbot bug bounties (HackerOne counts them as a category). MEASURED as cited above.
- One-off or team-scale: DARPA AIxCC, Truth Terminal, the AI Village charity and merch goals. MEASURED or STATED as cited.
- Revenue but no profit: agent-run shops and stores (Project Vend, Andon Market, Enrich Labs). MEASURED or STATED, against the operators' interest.
- Zero: agents left alone with money and accounts (Bottleneck Labs, ir272), and agents racing for open-source bounties. MEASURED or STATED.
- Seller claims only: "AI runs your company" platforms, and blog posts saying "my agent earns $X a month". These are STATED and, where checked, the customers' side earned little ([Aiolum](https://aiolum.com/story/polsia/), [Does It Pay](https://doesitpay.org/autonomous-ai-agent-income/research/)).
- The common thread: in every case that made money, a human picked the target, checked the output or holds the account; the two platforms that pay agent work on purpose (Metaculus, HackerOne) each set an explicit rule for this, and the two rules point in opposite directions (Metaculus forbids a human in the loop, HackerOne requires one). INFERENCE from the cited rules.
- The second thread: payment rails need a human. KYC, bank details and contract acceptance stop an agent before the money moves ([ir272](https://github.com/ir272/autonomous-earning-experiment); [Upwork API and MCP terms](https://upwork.pactsafe.io/versions/6a7de807acdc47dbc84c4892.pdf)). STATED and MEASURED.

## Ranked list (best first)

1. Forecasting bot prizes (Metaculus): $0 typical, a few thousand dollars per season for top bots (about $0 to $3,200 a month); $50 to $1,000 a season in model costs; about 150 to 200 days to first dollar; evidence strong; agent advantage large; legal or terms risk low.
2. Human-checked hackbot bug bounties: UNKNOWN, probably $0 for weeks, then uneven; $0 to about $100 in tools; UNKNOWN days, likely 30 or more; evidence some; agent advantage some; legal or terms risk medium (scope and report quality).
3. Owner-run freelance work with an agent as his tool: UNKNOWN here (see services lane); $0; UNKNOWN days; evidence some (controlled studies, not earnings); agent advantage some on code and data, little on 3D and film; terms risk low if he does the platform actions himself, high if an agent automates the site.
4. Agent-run online store or merch: below $200 a month profit in the best small audited case, losses with ads; $50 to a few hundred in ads; weeks; evidence some; agent advantage none to some; terms risk low to medium.
5. Open-source code bounty boards: $0; $0; never in the one test; evidence weak; agent advantage none (every rival has one); terms risk medium (spam).
6. "Budget, go earn" autonomous agent: $0; the budget plus model costs; never in the largest test; evidence strong that it fails; agent advantage none; legal or terms risk high (spam and unsolicited invoices seen).
7. "AI runs your company" platforms: about $0 for the median customer; a monthly subscription; UNKNOWN; evidence weak (seller figures); agent advantage none; terms risk low, money risk high.
8. Agent-run physical shop: losses after costs; tens of thousands of dollars and a lease; OUT for the owner.
9. Government prize challenges: millions, team-scale and one-off; OUT for one person.
10. AI content with bot streams or accounts: OUT, illegal.

## Smallest version one person could try

- Metaculus: run the template bot in MiniBench for two weeks and log its rank ([resources page](https://www.metaculus.com/notebooks/38928/bot-tournament-resources-page/)). Cost: model credits. Shows skill, not money, inside two weeks.
- Bug bounty: a two-week count of agent findings the owner can confirm by hand on two in-scope programs, submitting only confirmed ones. Cost: about $0. Shows confirmed findings per hour.
- Nothing else in this lane is worth his few hundred dollars. INFERENCE.

## Not included

- Claims that agents won Kaggle medals or prizes: I found only secondhand pages and no Kaggle record I could open, so they are left out. UNKNOWN.
- Simulated money (Vending-Bench, SWE-Lancer "earnings"): not earnings. Noted where relevant.
