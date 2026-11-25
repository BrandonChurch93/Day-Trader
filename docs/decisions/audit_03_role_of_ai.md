# Audit: docs/playbook/03_role_of_ai.md

Audited against: docs/research/03_llm_trading_agents_evidence.md
Auditor: broker_data_compliance_researcher
Date: 2026-11-24

Overall: the playbook matches the report's direction (deterministic core, LLM periphery) and has no fabricated claims. The issues are one over-tagged rule, three mis-sourced or mislabeled key numbers, and several dropped safety items that matter for the build.

## Spot verification (fetched 2026-11-24)
- VERIFIED: rta-bench-1 reports 0 of 91 runs with significant 4-factor alpha, a mean of -2.3%/yr (95% CI -4.7% to +0.1%), a 5.2 pp seed spread, a best LLM at +8.1% vs +19.0% for trend-following, and calendar-date joins at +32.0 bps vs -6.7 bps per trade under publication-time replay ([arXiv:2611.19530](https://arxiv.org/html/2611.19530)).
- VERIFIED: Alpha Arena shows 31 of 38 accounts lost money, with $43k in fees on $380k of stakes, recomputed from Hyperliquid data ([TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)).
- VERIFIED: Profit Mirage reports 51.48% to 62.23% Sharpe decay across five GPT-4o frameworks, Q2-Q3 2021 vs Q3-Q4 2024 ([arXiv:2510.07920](https://arxiv.org/html/2510.07920)).

## Findings

1. FIX (claim stronger than evidence). The rule "Validate every LLM-assisted workflow with 60–90 trading days ... [MEASURED] (research §3, §6)": the 60-90 day figure is the report's own recommendation (Implications §5), not a measured result. The report also says that at a 0.68-year test length, a true Sharpe of 1.0 has only a 19% chance of reaching significance (§2), so 60-90 days is a minimum gate, not proof of an edge. Replace with:
   "- Gate every LLM-assisted workflow on at least 60–90 trading days of post-cutoff paper trading, using point-in-time publication timestamps, realistic fees and slippage, and multiple seeds, against SPY/BTC buy-and-hold and trend-following baselines; treat passing as a minimum bar, not proof of edge, because even a true Sharpe of 1.0 reaches significance only 19% of the time over 0.68 years [STATED] (research §2, Implications)."

2. FIX (wrong label and source). Key numbers row "Post-cutoff news headline drift | ~90% initial hit rate (non-tradable); ~51% per-headline": the ~90% figure is the immediate, non-tradable reaction, not drift. The ~51% comes from the Fortune source, not the JFE link. The cost caveat is also missing. Replace with:
   "| GPT-4 headline sentiment (post-cutoff) | ~90% hit rate on immediate non-tradable reaction; ~51% single-headline accuracy; edge erased above ~2.7 bps/side costs | 2026-10 | MEASURED | [Lopez-Lira & Tang JFE](https://www.sciencedirect.com/science/article/abs/pii/S0304405X26001066) |"

3. FIX (source mismatch). Key numbers row "Real-world agent fund drains | Freysa $47k; AIXBT $106.2k; Grok/Bankrbot $150k–$200k | 2026-05 | AI Incident DB 7549": that source supports only the Grok/Bankrbot incident. Freysa (Nov 2024) and AIXBT (Mar 2025) come from other sources. Replace with:
   "| Grok/Bankrbot prompt-injection drain | ~$150k–$200k in DRB tokens (Morse-code indirect injection) | 2026-05 | MEASURED | [AI Incident DB 7549](https://incidentdatabase.ai/reports/7549/) |"
   (If Freysa and AIXBT are kept, cite [Zelcore](https://zelcore.io/academy/news-explained/ai-agent-risks-key-custody-prompt-injection) and [MIT AI Risk 1003](https://airisk.mit.edu/ai-incidents/1003-alleged-fraudulent-prompts-via-aixbt-dashboard-led) and use their own dates.)

4. FIX (imprecise number). Row "rta-bench-1 ... 78% beta": the paper says market and style factor exposures accounted for 78% of the absolute size of return components in the median run, which is not the same as "beta". Replace the value with:
   "0 of 91 runs significant; mean -2.3%/yr (95% CI -4.7% to +0.1%); factor exposures explain 78% of median-run returns"

5. BLOCKER (dropped money-safety item). The report documents that Alpaca's official MCP server lacks destructive-action annotations, so `cancel_all_orders` and `close_all_positions` look like reads to MCP clients, and that the hosted live URL places live orders with no broker-side approval (§7). The build uses Alpaca, so this must be a rule. Add to Rules for the build:
   "- Wrap Alpaca MCP tools in our own allowlist; treat `cancel_all_orders`, `close_all_positions`, and `update_account_config` as destructive, block them from agents, and never point an agent at the hosted live URL until the human-approval gate is built [MEASURED] (research §7)."

6. FIX (dropped design-relevant evidence for the tiered, periodic design). The report finds that most news and earnings price discovery happens within the first hour, with no significant edge left by the next open (§4, rta-bench-1). This directly limits a periodic-polling screener. Add to Rules:
   "- Do not route news-reaction trades through slow periodic LLM escalation; most earnings/news price discovery occurs within the first hour and no significant edge remains by the next open [MEASURED] (research §4)."

7. FIX (dropped key comparison). The report's strongest apples-to-apples result is that classical ML and simple rules beat LLM agents: in live crypto, TCN returned +62.94% and XGBoost +41.93% while every LLM method lost money; in the 2026 rally, trend-following returned +19.0% vs +8.1% for the best LLM (§1). Suggest replacing the "Large-model output consistency" or "cascade cost" row with:
   "| Baselines vs LLM agents | Crypto live: XGBoost +41.93%, TCN +62.94% vs all LLM agents negative; 2026 stock rally: trend-following +19.0% vs best LLM +8.1% | 2026-11 | MEASURED | [Wang 2026](https://arxiv.org/html/2611.19530) |"
   (Cite [arXiv:2609.34510](https://arxiv.org/html/2609.34510v1) for the crypto half if splitting.)

8. FIX (dropped injection defense for trades, not just transfers). The Do-not-do bullet covers untrusted text triggering fund transfers, but the report also shows fabricated headlines pushing agents into synchronized losing trades, and 14 of 15 frameworks exposed to indirect injection through news (§5). Add to Do not do:
   "- Do not let a single unverified news item trigger an order; require cross-source provenance and a price/volume confirmation computed in code."

9. NOTE (dropped broker caveats). The report notes that revoking IBKR AI access does not cancel pending orders, that Robinhood MCP accounts have per-order approval off by default and no documented paper mode for agents (§7), and that options agents can propose unbounded-loss strategies even with per-order approval (§7 note). The broker playbook (04) covers the IBKR and Robinhood points, so an optional addition here would be:
   "- Do not allow agents to propose options strategies with undefined max loss; compute max loss in code before any order is shown for approval."

10. NOTE (context for Alpha Arena row). The 31-of-38 result comes from two roughly two-week contests (Season 1: Oct 17 to Nov 3, 2025; Season 1.5: Nov 19 to Dec 3, 2025), so the sample is small. Suggest changing "As of" from 2026-11 to "Oct–Dec 2025".

11. NOTE (tag nuance). The rule "Pass raw primary evidence alongside screener tags ... [MEASURED]": the AgentRouter step-1 corruption finding is measured, but applying it to trading is the report's inference (§6 last paragraph). Acceptable, but [STATED] is more accurate.
