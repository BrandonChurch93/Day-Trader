# Round 74: Payers and Contests That Explicitly Allow Unattended AI Agents

Date: November 27, 2026
Queue: 148
Scope: Non-Metaculus payers and contests across six candidate families checked from primary organizer rules pages read on November 27, 2026.

## Verdict

Ranked list: none.

MEASURED: Across all six candidate families examined today outside Metaculus FutureEval and MiniBench, zero payers or contests satisfy all four gates simultaneously: an explicit published rule permitting an unattended AI agent or fully automated entry, a standing or currently open cash prize reachable by a US resident, compatibility with building and running from a work account without hitting a private-tool, employer-consent, or non-commercial clause, and a published record of who was paid.

Scope boundary: This round does not repeat Metaculus FutureEval and MiniBench (covered in `docs/research/207_forecasting_bot_entry_facts.md` and `practice/PLAN_B01_forecast_bot_DRAFT.md`), paid code bounty boards (Expensify, Algora, tscircuit, IssueHunt, and Gitcoin in `practice/PLAN_J01_agent_code_jobs_DRAFT.md` and `docs/research/205d_bounties_and_competitions.md`), or the security, ML, and quant platforms already reviewed in `docs/research/205d_bounties_and_competitions.md` (HackerOne/XBOW, Bugcrowd, Intigriti, Google VRP, Microsoft MSRC, Immunefi, Code4rena, Sherlock, Cantina, Kaggle Gemma 4 / Santa 2026 / Physical Engineering's Last Exam, DrivenData DaT / K-12, CrunchDAO general platform, Numerai, WorldQuant BRAIN/IQC, Quantiacs, Firebase #BuildHybridAI, ARC Prize 2026, DARPA AIxCC, NLnet, and Sovereign Tech).

Summary of the closest non-Metaculus candidates checked and why each fails one or more gates:

- AtCoder Long-Term Heuristic Contest (With AI division): explicitly allows free generative AI use, including automated editorial generation, but prizes in the latest contest checked (AHC074) are yen Amazon gift cards restricted to Japan residents, and its rules explicitly bar internal organization tools or non-public harnesses developed with anyone else ([AtCoder Long-Term AHC Rules](https://info.atcoder.jp/entry/long-ahc-llm-rules-en), [AtCoder AHC074](https://atcoder.jp/contests/ahc074)).
- Prophet Arena: explicitly permits API-based AI forecasting agents and ran a $1,000 midterm election prize, but submissions closed November 2, 2026 with no recurring cash contest stated and no published payout record on the rules page ([Prophet Arena Election Challenge](https://www.prophetarena.co/docs/election)).
- ADIA Lab Structural Break Open Benchmark Challenge (hosted on CrunchDAO): offers $6,000 USD per quarter through December 31, 2026 for deterministic Python code submissions, but the benchmark rules neither state explicit permission for unattended AI agents nor publish who was paid ([ADIA Lab Structural Break Open Benchmark Docs](https://docs.crunchdao.com/competitions/competitions/structural-break-open-benchmark), [ADIA Lab Announcement](https://www.adialab.ae/structural-break-open-benchmark)).
- All checked open data-labeling platforms (Amazon Mechanical Turk, Outlier/Remotasks/Scale AI, and Prolific) explicitly bar bots and automated agents and are marked OUT ([MTurk Acceptable Use Policy](https://www.mturk.com/acceptable-use-policy), [Outlier Community Guidelines](https://outlier.ai/legal/community-guidelines), [Prolific Data Quality Pack](https://researcher-help.prolific.com/en/articles/621821-methodological-justification-pack-how-prolific-protects-data-quality)).
- All checked live mainnet verifiable-compute protocols require bonded slashable stake and are skipped under the no-staking rule ([Symbiotic Decentralized Compute Docs](https://docs.symbiotic.fi/get-started/use-cases/decentralized-compute-ai-verification)).

## Family 1: Other Bot or AI Forecasting Contests With Cash

### Prophet Arena - CLOSED / ONE-OFF

- Status: CLOSED for cash prizes as of November 27, 2026 ([Prophet Arena Election Challenge](https://www.prophetarena.co/docs/election)).
- Automated-entry rule (STATED): The organizer's Election Challenge page describes building an agent, supplies an API for submitting forecasts, and states that AI predictions are included in its post-election report ([Prophet Arena Election Challenge](https://www.prophetarena.co/docs/election)).
- Owner-only steps (UNKNOWN): The rules page states that terms and conditions apply and requires forecasting at least 75 of 100 events, but does not publish account, identity, or tax-form requirements on that page ([Prophet Arena Election Challenge](https://www.prophetarena.co/docs/election)).
- Published payout record (UNKNOWN): The rules page announces a $1,000 prize to the single most accurate forecaster once events settle, but publishes no entrant count, winner count, or payout table ([Prophet Arena Election Challenge](https://www.prophetarena.co/docs/election)).
- Round duration (STATED): Submissions for the 2026 midterm challenge closed Monday, November 2, 2026 at 5:00 PM ET; the page does not state that any cash contest recurs ([Prophet Arena Election Challenge](https://www.prophetarena.co/docs/election)).
- Model-call cost (UNKNOWN): Depends on the entrant's own forecasting pipeline; no benchmark token cost is published on the organizer page ([Prophet Arena Election Challenge](https://www.prophetarena.co/docs/election)).
- Company-resources or commercial rule (UNKNOWN): Not stated on the Election Challenge rules page ([Prophet Arena Election Challenge](https://www.prophetarena.co/docs/election)).
- Honest private test (INFERENCE): A local forecast pipeline could be scored privately against settled Kalshi and Polymarket event outcomes without entering, but there is no live recurring cash round to enter afterward.

### ForecastBench - OUT (NO CASH PRIZE)

- Status: OUT (benchmark only, no cash prize listed) ([ForecastBench](https://www.forecastbench.org/)).
- Automated-entry rule (STATED): The organizer page describes a public tournament leaderboard of LLM forecasting accuracy where tool use is allowed and models may be scaffolded, fine-tuned, or ensembled, without stating an explicit unattended-bot payment rule ([ForecastBench](https://www.forecastbench.org/)).
- Owner-only steps (UNKNOWN): Not applicable for payouts because no cash prize is offered ([ForecastBench](https://www.forecastbench.org/)).
- Published payout record (MEASURED): None; the page mentions no cash prizes ([ForecastBench](https://www.forecastbench.org/)).
- Round duration (UNKNOWN): No submission or update cadence is stated on the homepage ([ForecastBench](https://www.forecastbench.org/)).
- Model-call cost (UNKNOWN): Not stated on the organizer page ([ForecastBench](https://www.forecastbench.org/)).
- Company-resources or commercial rule (UNKNOWN): Not stated on the homepage ([ForecastBench](https://www.forecastbench.org/)).
- Honest private test (INFERENCE): Public benchmark questions can be evaluated offline, but passing them yields no cash payout.

## Family 2: Algorithm or Optimization Contests With Standing Cash Prizes

### AtCoder Long-Term Heuristic Contest (With AI Division) - OUT (JAPAN-ONLY PRIZES AND WORK-TOOL RULE)

- Status: OUT for US cash payouts and work-account internal tools, despite having the clearest explicit AI-agent permission found outside Metaculus ([AtCoder Long-Term AHC Rules](https://info.atcoder.jp/entry/long-ahc-llm-rules-en), [AtCoder AHC074](https://atcoder.jp/contests/ahc074)).
- Automated-entry rule (STATED): Version 20261026 of the Long-Term AHC rules states verbatim: "You may use generative AI freely. The restrictions of the previous generative AI usage rules and of the Human Only division do not apply." ([AtCoder Long-Term AHC Rules](https://info.atcoder.jp/entry/long-ahc-llm-rules-en)). The accompanying format announcement adds that entrants may generate the post-contest editorial automatically by having generative AI read execution logs ([AtCoder Long-Term AHC Format Announcement](https://atcoder.jp/posts/long-ahc-divisions-2026_en)). Note that short-term AHCs follow separate rules that prohibit generative AI in principle.
- Owner-only steps (STATED): For AHC074 (HACK TO THE FUTURE 2027), prize eligibility requires residing in Japan and truthfully completing every field of the registration form; minors require parental consent ([AtCoder AHC074](https://atcoder.jp/contests/ahc074)). Tax reporting rules are UNKNOWN on the contest page ([AtCoder AHC074](https://atcoder.jp/contests/ahc074)).
- Published payout record (UNKNOWN): The AHC074 page lists prize slots (¥1,000 Amazon gift card for up to 200 preliminary qualifiers including the top 66 With AI entrants, plus final-round Amazon gift cards from ¥100,000 down to ¥10,000 across 10 overall ranks, 5 job-seeker ranks, and 3 youth ranks for a 56-person final), but does not publish how many entered or were actually paid ([AtCoder AHC074](https://atcoder.jp/contests/ahc074)).
- Round duration (STATED): AHC074 ran 10 days from October 30, 2026 10:00 UTC to November 9, 2026 10:00 UTC ([AtCoder AHC074](https://atcoder.jp/contests/ahc074)).
- Model-call cost (UNKNOWN): Depends entirely on the entrant's own AI search loop; AtCoder notes that paid public models are allowed ([AtCoder Long-Term AHC Rules](https://info.atcoder.jp/entry/long-ahc-llm-rules-en)).
- Company-resources or commercial rule (STATED - BLOCKING): The rules state verbatim: "However, since AHC is an individual contest, you may not use AI models or harnesses that are not publicly available and that anyone other than yourself was involved in developing." ([AtCoder Long-Term AHC Rules](https://info.atcoder.jp/entry/long-ahc-llm-rules-en)). Prohibited examples explicitly include "private models or internal tools of your organization, and harnesses provided to you individually by others", while tools "developed solely by yourself, and those available to anyone (including paid ones)" are permitted ([AtCoder Long-Term AHC Rules](https://info.atcoder.jp/entry/long-ahc-llm-rules-en)).
- Honest private test (INFERENCE): Past AtCoder heuristic problems and local testers are public, so a local benchmark is straightforward, but US non-residents cannot collect the yen Amazon gift cards in AHC074.

### Topcoder Marathon Match Tournament 2026-2027 - OUT (NO AUTOMATED-ENTRY PERMISSION, NO PRIZE TABLE, EMPLOYER CONSENT REQUIRED)

- Status: OUT ([Topcoder Marathon Match Rules](https://www.topcoder.com/marathon-match-tournament/rules-regulations), [Topcoder Terms and Conditions](https://www.topcoder.com/community/how-it-works/terms)).
- Automated-entry rule (MEASURED): Neither the Marathon Match Tournament rules page nor Topcoder's general Terms and Conditions explicitly permits an unattended AI agent or automated submission pipeline ([Topcoder Marathon Match Rules](https://www.topcoder.com/marathon-match-tournament/rules-regulations), [Topcoder Terms and Conditions](https://www.topcoder.com/community/how-it-works/terms)). General Terms bar launching any bot or script that may harm or corrupt the website or other systems ([Topcoder Terms and Conditions](https://www.topcoder.com/community/how-it-works/terms)).
- Owner-only steps (STATED): General Terms state verbatim: "You may only set up one account." ([Topcoder Terms and Conditions](https://www.topcoder.com/community/how-it-works/terms)). Redeeming a cash prize requires an Identity verification request form, an Affidavit of Eligibility and Liability and Publicity Release if requested, IRS Form W-9 or W-8BEN, a Topcoder Competition Assignment Agreement for tournament finals, and post-competition surveys; USD prizes are paid within 90 days ([Topcoder Terms and Conditions](https://www.topcoder.com/community/how-it-works/terms)).
- Published payout record (UNKNOWN): The Marathon Match Tournament rules page references a cash prize table but omits the table and dollar amounts, and neither page publishes entrant counts or historical payout medians ([Topcoder Marathon Match Rules](https://www.topcoder.com/marathon-match-tournament/rules-regulations)).
- Round duration (STATED): The online qualifying season runs June 1, 2026 to March 31, 2027, followed by a 24-hour online Championship Round for the top 12 point-earners ([Topcoder Marathon Match Rules](https://www.topcoder.com/marathon-match-tournament/rules-regulations)).
- Model-call cost (UNKNOWN): Not applicable without explicit automated-entry permission.
- Company-resources or commercial rule (STATED - BLOCKING): Topcoder Terms state verbatim: "You hereby represent that you have obtained the necessary approvals and consents from all third parties including your employer for the purpose of participating in Topcoder Competitions." ([Topcoder Terms and Conditions](https://www.topcoder.com/community/how-it-works/terms)). Winners must also assign all intellectual property rights in winning submissions to Topcoder ([Topcoder Terms and Conditions](https://www.topcoder.com/community/how-it-works/terms)).
- Honest private test (INFERENCE): Offline practice on past Marathon Match problems is possible, but live automated participation lacks explicit organizer permission.

## Family 3: Machine-Learning and Data Contests

### Zindi - OUT (EXPLICIT AUTOML BAN AND NO PAID TOOLS)

- Status: OUT ([Zindi Challenge Rules](https://zindi.world/rules)).
- Automated-entry rule (STATED): Zindi's Challenge Rules state verbatim: "Automated machine learning tools such as AutoML are not permitted." ([Zindi Challenge Rules](https://zindi.world/rules)). The rules further require: "The solution must use publicly-available, open-source packages only." and "You may only use tools available to everyone i.e. no paid services or free trials that require a credit card." ([Zindi Challenge Rules](https://zindi.world/rules)).
- Owner-only steps (STATED): Rules state verbatim: "Multiple accounts per user are not permitted, and neither is collaboration or membership across multiple teams." ([Zindi Challenge Rules](https://zindi.world/rules)). The top 3 winners must submit proof of identification, proof of residence, and a bank letter confirming banking details; winners pay all prize taxes and international bank transfer fees for prizes of $500 or more ([Zindi Challenge Rules](https://zindi.world/rules)).
- Published payout record (UNKNOWN): Not published on the general Challenge Rules page ([Zindi Challenge Rules](https://zindi.world/rules)).
- Round duration (UNKNOWN): Varies by challenge; not fixed on the general rules page ([Zindi Challenge Rules](https://zindi.world/rules)).
- Model-call cost (STATED): Paid LLM API services requiring a credit card are barred by rule ([Zindi Challenge Rules](https://zindi.world/rules)).
- Company-resources or commercial rule (STATED - BLOCKING): Paid services and non-public tools are barred by the rule above ([Zindi Challenge Rules](https://zindi.world/rules)).
- Honest private test (INFERENCE): Irrelevant because both automated ML tools and paid model APIs are explicitly barred.

### AIcrowd - OUT (NO AUTOMATED-ENTRY PERMISSION AND DISCRETIONARY REWARDS)

- Status: OUT ([AIcrowd Terms of Use](https://www.aicrowd.com/terms), [AIcrowd Participation Terms](https://www.aicrowd.com/participation_terms)).
- Automated-entry rule (MEASURED): Neither AIcrowd's Terms of Use nor its Participation Terms explicitly permits an unattended AI agent ([AIcrowd Terms of Use](https://www.aicrowd.com/terms), [AIcrowd Participation Terms](https://www.aicrowd.com/participation_terms)). The Terms of Use prohibit unauthorized monitoring, spidering, or bulk extraction of the platform ([AIcrowd Terms of Use](https://www.aicrowd.com/terms)).
- Owner-only steps (STATED): Account holders must be of legal age (or 16+ with legal representative consent), and prize eligibility requires providing an accurate mailing address and any information reasonably requested to send rewards and file tax documentation; participants bear sole tax responsibility ([AIcrowd Terms of Use](https://www.aicrowd.com/terms), [AIcrowd Participation Terms](https://www.aicrowd.com/participation_terms)).
- Published payout record (UNKNOWN): Neither terms page publishes entrant counts or payout records; Participation Terms Clause 3.5 states verbatim: "Participants have no claim to receive any Reward. The responsible Organizer has the right to make the final decision at its entire discretion on the winner of a given Challenge." ([AIcrowd Participation Terms](https://www.aicrowd.com/participation_terms)).
- Round duration (UNKNOWN): Set per individual challenge guidelines ([AIcrowd Terms of Use](https://www.aicrowd.com/terms)).
- Model-call cost (UNKNOWN): Depends on each individual challenge.
- Company-resources or commercial rule (STATED): Clause 5.2 of the Participation Terms states verbatim: "You confirm that your participation to a Challenge does not put you in breach of any agreement you may be bound by, in particular but not limited to, any breach of any employment contract, consultancy contract or confidentiality contract with any third party." ([AIcrowd Participation Terms](https://www.aicrowd.com/participation_terms)). Accounts created for a legal entity require authorization to bind that entity ([AIcrowd Terms of Use](https://www.aicrowd.com/terms)).
- Honest private test (INFERENCE): Local evaluation is possible on open datasets, but platform terms lack explicit unattended-agent permission and a standing published payout record.

### Kaggle (Platform-Wide Rules Check, Supplementing Doc 205d) - OUT (NON-COMMERCIAL CLAUSE AND AUTOMATED ACCESS BAR)

- Status: OUT for work-account commercial use and automated platform interaction ([Kaggle Terms of Use](https://www.kaggle.com/terms)).
- Automated-entry rule (MEASURED): Platform Terms do not grant general permission for unattended AI agents; Clause 3 prohibits automated spidering or bulk data extraction of any page, data, or portion of the Services ([Kaggle Terms of Use](https://www.kaggle.com/terms)).
- Owner-only steps (STATED): Platform Terms state verbatim: "You also may not have, control, or operate under more than one active Kaggle account or Kaggle User ID." and "You are not allowed to allow multiple individuals to operate under one Kaggle User ID, even if you are an organization or entity." ([Kaggle Terms of Use](https://www.kaggle.com/terms)). Prize tax terms are not stated on the general Terms page ([Kaggle Terms of Use](https://www.kaggle.com/terms)).
- Published payout record (UNKNOWN): Not published on the general Terms page ([Kaggle Terms of Use](https://www.kaggle.com/terms)).
- Round duration (UNKNOWN): Varies per host competition ([Kaggle Terms of Use](https://www.kaggle.com/terms)).
- Model-call cost (UNKNOWN): Varies per host competition.
- Company-resources or commercial rule (STATED - BLOCKING): Platform Terms state verbatim: "You will only use the Services for your own internal, personal, non-commercial use, and not on behalf of or for the benefit of any third party, and only in a manner that complies with all laws that apply to you." ([Kaggle Terms of Use](https://www.kaggle.com/terms)).
- Honest private test (INFERENCE): Public historical Kaggle datasets can be tested locally, but live work-account commercial entry conflicts with the personal non-commercial use clause.

## Family 4: Benchmarks With Prize Pools Open to Outside Entrants

### ADIA Lab Structural Break Open Benchmark Challenge (on CrunchDAO) - NEAR-MISS / OUT

- Status: NEAR-MISS, marked OUT against Round 74's full bar because neither the benchmark docs nor announcement explicitly permits unattended AI agents or publishes who was paid ([ADIA Lab Structural Break Open Benchmark Docs](https://docs.crunchdao.com/competitions/competitions/structural-break-open-benchmark), [ADIA Lab Announcement](https://www.adialab.ae/structural-break-open-benchmark)).
- Automated-entry rule (MEASURED): Participants submit deterministic Python code implementing `train()` and `infer()` functions directly to the CrunchDAO platform, where predictions must match within `1e-8` on a 30% rerun and stay at or below 95% Spearman correlation with the pinned top 10 reference models ([ADIA Lab Structural Break Open Benchmark Docs](https://docs.crunchdao.com/competitions/competitions/structural-break-open-benchmark)). Neither the benchmark documentation nor the ADIA Lab announcement explicitly states whether an unattended AI agent may generate and submit entries ([ADIA Lab Structural Break Open Benchmark Docs](https://docs.crunchdao.com/competitions/competitions/structural-break-open-benchmark), [ADIA Lab Announcement](https://www.adialab.ae/structural-break-open-benchmark)).
- Owner-only steps (UNKNOWN): Neither the benchmark documentation nor the ADIA Lab announcement states KYC, identity, or tax-form steps; only the team leader is ranked and eligible for a reward ([ADIA Lab Structural Break Open Benchmark Docs](https://docs.crunchdao.com/competitions/competitions/structural-break-open-benchmark)).
- Published payout record (UNKNOWN): Both pages state the quarterly prize pool ($3,000 USD for 1st, $2,000 USD for 2nd, $1,000 USD for 3rd per quarter), but neither page publishes entrant counts, winner lists, or payout tables for Q1 to Q3 2026 ([ADIA Lab Structural Break Open Benchmark Docs](https://docs.crunchdao.com/competitions/competitions/structural-break-open-benchmark), [ADIA Lab Announcement](https://www.adialab.ae/structural-break-open-benchmark)).
- Round duration (STATED): Continuous submissions scored quarterly at midnight UTC on March 31, June 30, September 30, and December 31, 2026, with a one-week scoring downtime; submitted code must execute within 15 hours per week ([ADIA Lab Structural Break Open Benchmark Docs](https://docs.crunchdao.com/competitions/competitions/structural-break-open-benchmark)).
- Model-call cost (INFERENCE): Submitted code runs deterministically on the CrunchDAO platform without external API calls during inference, so recurring inference token cost is $0, while offline code-generation model cost is UNKNOWN.
- Company-resources or commercial rule (UNKNOWN): Neither benchmark page states employer or commercial restrictions ([ADIA Lab Structural Break Open Benchmark Docs](https://docs.crunchdao.com/competitions/competitions/structural-break-open-benchmark), [ADIA Lab Announcement](https://www.adialab.ae/structural-break-open-benchmark)).
- Honest private test (INFERENCE): Local cross-validation on public time-series break datasets is possible before entering, though the 95% Spearman originality check against the pinned top 10 reference models cannot be reproduced offline without those models' predictions.

## Family 5: Open Data-Labeling or Evaluation Tasks (All Checked Platforms Bar Automation)

### Amazon Mechanical Turk (MTurk) - OUT

- Status: OUT ([MTurk Acceptable Use Policy](https://www.mturk.com/acceptable-use-policy)).
- Automated-entry rule (STATED): The Acceptable Use Policy explicitly prohibits "Using bots, scripts, or other automated methods to complete HITs" and states verbatim: "We take this seriously, so if we determine that you are using bots, scripts, or other automated methods to complete HITs, we may suspend or terminate your account, and your rewards balance may be forfeited." ([MTurk Acceptable Use Policy](https://www.mturk.com/acceptable-use-policy)).
- Owner-only steps, payout record, duration, model cost, company-resources rule, and private test (UNKNOWN / NOT APPLICABLE): Disqualified at the first gate by the explicit automated-completion ban ([MTurk Acceptable Use Policy](https://www.mturk.com/acceptable-use-policy)).

### Outlier / Remotasks / Scale AI - OUT

- Status: OUT ([Outlier Community Guidelines](https://outlier.ai/legal/community-guidelines)).
- Automated-entry rule (STATED): The Community Guidelines (covering Outlier, Remotasks, HFC, and any other platform operated by Scale AI, Inc.) state verbatim: "Complete all tasks by yourself to the best of your ability without seeking the assistance of other persons, technological automation such as bots or scripts, or third-party materials or tools - unless specifically required by a Service administrator." ([Outlier Community Guidelines](https://outlier.ai/legal/community-guidelines)).
- Owner-only steps, payout record, duration, model cost, company-resources rule, and private test (UNKNOWN / NOT APPLICABLE): Disqualified at the first gate by the explicit ban on bots and scripts ([Outlier Community Guidelines](https://outlier.ai/legal/community-guidelines)).

### Prolific - OUT

- Status: OUT ([Prolific Data Quality Pack](https://researcher-help.prolific.com/en/articles/621821-methodological-justification-pack-how-prolific-protects-data-quality)).
- Automated-entry rule (STATED): Prolific explicitly targets and excludes "AI-powered bots", "agentic AI", and "autonomous agents", enforcing a closed pool where participants must pass government ID verification matched to a live video selfie (Entrust), surprise video selfie re-checks, IP deduplication, and 110+ automated Protocol checks, with permanent bans for removed accounts ([Prolific Data Quality Pack](https://researcher-help.prolific.com/en/articles/621821-methodological-justification-pack-how-prolific-protects-data-quality)).
- Owner-only steps, payout record, duration, model cost, company-resources rule, and private test (UNKNOWN / NOT APPLICABLE): Disqualified at the first gate by the explicit human-only identity and anti-bot enforcement ([Prolific Data Quality Pack](https://researcher-help.prolific.com/en/articles/621821-methodological-justification-pack-how-prolific-protects-data-quality)).

## Family 6: Protocol-Run Tasks Paid on Verifiable Output

### Symbiotic Relay (Decentralized Compute and AI Verification) - OUT (STAKING REQUIRED)

- Status: OUT under the no-staking rule ([Symbiotic Decentralized Compute Docs](https://docs.symbiotic.fi/get-started/use-cases/decentralized-compute-ai-verification)).
- Automated-entry rule (STATED): Designed for automated off-chain compute nodes and container jobs producing verifiable receipts (including TEE quote hashes or zero-knowledge proofs) that trigger on-chain escrow payments once verified ([Symbiotic Decentralized Compute Docs](https://docs.symbiotic.fi/get-started/use-cases/decentralized-compute-ai-verification)).
- Staking / capital blocker (STATED): The documented workflow requires operators to enroll and lock slashable stake ("stake-backed, verifiable receipt" from "bonded operators") to secure payment release and cover fraud or missed-SLA slashing ([Symbiotic Decentralized Compute Docs](https://docs.symbiotic.fi/get-started/use-cases/decentralized-compute-ai-verification)).
- Owner-only steps, payout record, duration, model cost, company-resources rule, and private test (UNKNOWN / SKIPPED): Skipped because real-money staked collateral is required, and no live zero-stake mainnet verifiable-output protocol with published cash payouts was found in this round ([Symbiotic Decentralized Compute Docs](https://docs.symbiotic.fi/get-started/use-cases/decentralized-compute-ai-verification)).
