# Role of AI in the Trading System
Source: docs/research/03_llm_trading_agents_evidence.md
Last verified: 2026-11-24

## Bottom line
Do not deploy an LLM as an autonomous day trader; in live and look-ahead-free tests, most lose money or earn factor exposure, not alpha. Models never emit orders or trade intents: deterministic code generates all orders through the risk engine, while LLMs emit evidence tags, watchlist candidates, veto/pause flags, offline codegen, and review.

## Rules for the build
- Enforce strict separation: models emit only evidence tags, watchlist candidates, and veto/pause flags for deterministic rules; deterministic strategy code generates all orders through the risk engine, and shadow mode only logs outputs (our recommendation) [STATED] (research §6).
- Read balances, positions, and open orders from broker APIs; never trust LLM conversation history or vector memory for account state (our recommendation) [STATED] (research §5, §6).
- Wrap Alpaca MCP tools in our allowlist; block destructive tools (`cancel_all_orders`, `close_all_positions`, `update_account_config`) from agents, and never point an agent at the hosted live URL before building human approval [MEASURED] (research §7).
- Disable withdrawal scopes and `update_account_config` on all brokers; enforce JSON schema checks, symbol allowlists, per-order notional caps, rate limits, and draft-then-approve or paper sandboxes (our recommendation) [STATED] (research §5, §7).
- Do not route news-reaction trades through slow periodic LLM escalation; most news/earnings price discovery occurs within the first hour, leaving no significant edge by next open [MEASURED] (research §4).
- Limit cheap small-model screeners to structured JSON extraction (event type, polarity, novelty, provenance) on news, 8-K filings, and earnings calls; use the Perplexity Agent API for new Perplexity work since legacy Sonar Chat Completions ended Sep 27, 2026 (our recommendation) [STATED] (research §4, §6).
- Pass raw primary evidence (headline, timestamp, ticker, price/volume delta) with screener tags to the frontier model so summaries do not corrupt escalation (our recommendation) [STATED] (research §6).
- Limit frontier models to infrequent catalyst review, qualitative veto/pause flags, offline strategy codegen, and post-trade journaling (our recommendation) [STATED] (research §4, §6).
- Gate tiny live capital on at least 60 trading days AND 100 closed paper trades (models off, then shadow) using publication timestamps, realistic fees/slippage, and multiple seeds against buy-and-hold and trend baselines; require 6–12 months live evidence to scale and a written owner decision in `docs/decisions/` for any promotion (our recommendation; 0.68-year test gives true Sharpe 1.0 only 19% power) [STATED] (research §2, §3, §6).

## Key numbers
| Item | Value | As of | Tag | Source |
|---|---|---|---|---|
| Alpha Arena losing accounts | 31 of 38 accounts lost; $43k fees on $380k capital | Oct–Dec 2025 | MEASURED | [TradingAgentStack Audit](https://tradingagentstack.com/alpha-arena-results/) |
| Look-ahead-free 4-factor alpha (rta-bench-1) | 0 of 91 runs significant; mean -2.3%/yr (95% CI -4.7% to +0.1%); factor exposures explain 78% of median-run returns | 2026-11 | MEASURED | [Wang 2026](https://arxiv.org/html/2611.19530) |
| Stock baselines vs LLM agents (2026 rally) | Trend-following +19.0% vs best LLM +8.1% | 2026-11 | MEASURED | [Wang 2026](https://arxiv.org/html/2611.19530) |
| Crypto baselines vs LLM agents (live/paper) | TCN +62.94%, XGBoost +41.93% vs all LLM agents negative (-9.16% to -68.62%) | 2026-10 | MEASURED | [Can AI Make Money in Crypto](https://arxiv.org/html/2609.34510v1) |
| Post-cutoff agent Sharpe decay | 51.48% to 62.23% drop across 5 frameworks | 2025-10 | MEASURED | [Profit Mirage](https://arxiv.org/html/2510.07920) |
| 20-year LLM backtest alpha (FINSABER) | No significant alpha (p > 0.34); B&H beats LLMs (p <= 0.0117) | 2026-08 | MEASURED | [FINSABER KDD 2026](https://waylonli.com/files/finsaber-slides.pdf) |
| Pre-cutoff S&P 500 memorization (GPT-4o) | 0.61% MAPE pre-cutoff vs 16.87% post-cutoff | 2025-04 | MEASURED | [Lopez-Lira et al.](https://arxiv.org/html/2504.14765v2) |
| GPT-4 headline sentiment (post-cutoff) | ~90% hit rate on immediate non-tradable reaction; predicts 1–2 day drift in small caps | 2026-10 | MEASURED | [Lopez-Lira & Tang JFE](https://www.sciencedirect.com/science/article/abs/pii/S0304405X26001066) |
| Large-model output consistency at T = 0 | 12.5% on 120B vs 100% on 7B–8B models | 2025-11 | MEASURED | [LLM Output Drift](https://arxiv.org/html/2511.07585) |
| Seed-to-seed return variance | 5.2 pp average spread across identical model/period | 2026-11 | MEASURED | [Wang 2026](https://arxiv.org/html/2611.19530) |
| Multi-step cascade cost reduction | 72% savings (<3% quality loss) vs 31%–44% single-turn | 2026-07 | MEASURED | [AgentRouter ICML 2026](https://arxiv.org/pdf/2609.22951) |
| Grok/Bankrbot prompt-injection drain | ~$150k–$200k in DRB tokens (Morse-code indirect injection) | 2026-05 | MEASURED | [AI Incident DB 7549](https://incidentdatabase.ai/reports/7549/) |

## Do not do
- Do not trust pre-cutoff LLM backtests or calendar-date news joins.
- Do not call LLMs per intraday bar for price forecasting, math, or latency-sensitive entries.
- Do not grant unbounded order authority, withdrawal scopes, or `update_account_config` access.
- Do not let untrusted web, social, or news text trigger transfers or unvalidated instructions.
- Do not let a single unverified news item trigger an order; require cross-source provenance and code-computed price/volume confirmation.
- Do not let agents propose undefined-max-loss options strategies; compute max loss in code before showing any order for approval.
- Do not use remote MCP with high-reasoning models for unattended Coinbase execution where orders stall.
- Do not omit fees, slippage, and turnover; LLM overtrading burns small accounts.

## Must measure ourselves
- Net return, Sharpe, turnover, and fee drag over 60+ trading days and 100+ closed paper trades (models off vs shadow).
- False-positive escalation rate and latency of our small-to-large cascade.
- Run-to-run output consistency of screening and review models at T = 0.
- Incremental alpha of LLM evidence tags and veto/pause flags over deterministic baselines.
- Daily API token spend versus expected net P&L at target account size.
