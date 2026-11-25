# Audit: docs/playbook/05_perplexity_and_costs.md
Audited against: docs/research/05_perplexity_platform_options.md
Auditor: stock_daytrading_evidence_researcher
Date: 2026-11-24

Overall: numbers and dates match the report, all 10 table rows trace to it, and length limits are met (about 363 words of prose; one 8-row table). The main gaps are legal-safety items that the report states as MEASURED policy text but the playbook drops or blurs.

## Spot-verification of load-bearing claims (fetched 2026-11-24)
- Agent model rates: confirmed on [Agent API Models](https://docs.perplexity.ai/docs/agent-api/models). Haiku 5.5 is $0.10/$0.50 only at 100k input tokens or fewer, GPT-6 Luna $0.10/$0.50 at 272k or fewer; Opus 5.5 $4/$20; Fable 5.2 $8/$40; Fable requires non-ZDR access by contacting api@perplexity.ai. PASS.
- Computer automation cadence: confirmed on [Automations in Computer](https://www.perplexity.ai/help-center/en/articles/11521526-perplexity-tasks). Minimum 15 minutes; runs may start a few minutes late; skipped if credits or access are unavailable; repeated skips pause the task, and it stays paused until manually re-enabled. PASS (see FIX 4 on the dropped "stays paused" detail).
- Anthropic consumer terms: confirmed on [Anthropic Consumer Terms](https://www.anthropic.com/legal/consumer-terms). They prohibit automated or non-human access except via an Anthropic API key or explicit permission, and they prohibit relying on the Services "to buy or sell securities or to provide or receive advice about securities." PASS, but the playbook omits this (see BLOCKER 1).

## Findings

BLOCKER 1. Rule 8 drops the explicit Anthropic securities prohibition and the automated-access restriction, both MEASURED in the report. This is the most important legal constraint on the user's plan.
Replace rule 8 with:
"- Do not rely on Claude consumer (subscription) access to buy/sell securities or for securities advice: Anthropic's consumer terms prohibit this and restrict automated access unless using an Anthropic API key or explicit permission. Anthropic's AUP treats personalized investment recommendations, including digital assets, as high risk, requiring qualified human review before reliance; keep AI output non-final research or fixed-rule processing (research §3) [MEASURED]"

BLOCKER 2. The playbook drops the forward-dated Perplexity AUP (January 1, 2027), which calls for human oversight of consequential automated financial decisions. It takes effect about five weeks after the verification date, so a build agent needs it.
Add to "Rules for the build" (or to "Must measure ourselves", if the rule budget is full):
"- Plan for Perplexity's AUP version dated January 1, 2027, which calls for human oversight of consequential automated financial decisions; applicability to personal self-trading is unverified, so keep a human approval step before any live order (research §3) [MEASURED text; applicability UNKNOWN]"

FIX 1. Rule 7 is garbled. "Start with a permitted fallback if Fable 5.2 access is unavailable" reads as conditional, and it drops the report's data-handling instruction.
Replace with:
"- Do not assume Fable 5.2 access: on the Agent API it requires non-zero-data-retention access by request, so build on a permitted fallback model and keep broker/account data out of research payloads (research §2) [STATED]"

FIX 2. The Agent model rates row omits the context bands that make the cheap rates valid. A build agent sending long filings will be billed more.
Replace value with:
"Haiku 5.5 $0.10/$0.50 (at 100k input tokens or fewer) or GPT-6 Luna $0.10/$0.50 (at 272k or fewer); Sonnet 5.5 $2/$10; Opus 5.5 $4/$20; Fable 5.2 $8/$40 per million input/output tokens"

FIX 3. The Claude Max / Ultra row cites only claude.com/pricing, but the API-credit expiry and linked-Console requirement come from the support article. The report also says not to count these credits as a cash discount.
Replace Source with [API credit rules](https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans), and append to the value: "credits expire each cycle, need a linked Console org; not a cash discount; Perplexity retrieval fees not covered".

FIX 4. Rule 2 says "allow for delayed, skipped or paused runs" but omits that a paused task stays paused until it is manually re-enabled. That is an operational failure mode for monitoring.
Replace the end of rule 2 with: "...allow for late starts and skipped runs; repeated skips pause the automation until manually re-enabled, so alert on missed briefs (research §1) [STATED]"

NOTE 1. Legacy Sonar Chat Completions support ended September 27, 2026 (report, STATED). Consider adding to "Do not do": "- Do not price or build on legacy Sonar Chat Completions; support ended September 27, 2026."

NOTE 2. Zero-retention organizations cannot create or run Monitors (report, STATED). If the org enables ZDR for privacy, the Monitor-based design breaks. Consider adding to "Must measure ourselves": "- Confirm our API org's data-retention setting permits Monitors and the chosen models."

NOTE 3. Subscription prices are dropped: Pro $20/month, Max $200/month, Enterprise Pro $40/seat, Enterprise Max $325/seat (report, MEASURED). That is acceptable for build agents, but the lead may want one row for budgeting.

NOTE 4. Teammate eligibility is UNKNOWN in the report (official docs conflict on Enterprise Pro versus Enterprise Max). Rule 2's "before paying for a Max Teammate" is fine, but consider adding "verify Teammate seat eligibility for the account" to "Must measure ourselves".

NOTE 5. The Monitor row should mention that webhooks are at-least-once and may arrive out of order; rule 3 covers this, so no change is strictly needed.

NOTE 6. The 2,880-check scenario row is correct ($14.80 tiered, $88.74 all-Fable, matching the report), and it is correctly tagged as illustrative.
