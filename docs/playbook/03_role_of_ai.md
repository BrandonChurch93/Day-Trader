# Role of AI in the Trading System
Source: docs/research/03_llm_trading_agents_evidence.md
Last verified: 2026-11-24. Corrected 2026-11-24 after a fresh source check (`docs/decisions/source_check_2026-11-24.md`).

> Note added 2026-11-25. This page is from reading only. Our own pilot since then had six AI model runs make daily calls on past prices. It was inconclusive by design and every run behaved like a simple trend rule (`docs/research/14_ai_calls_pilot_02.md`). A review of AI systems with live money found none that beat holding (`docs/research/18_ai_systems_with_live_records.md`). Nothing here changes the rules below. The lines under "Rules for the build" on this page are research recommendations from reading. None is an owner decision, except where a line repeats a hard rule from `AGENTS.md`: that rule is in force whatever this page calls it. The owner's quality files pick no strategy and no stack, and nothing is built until he has approved a written spec (`docs/quality/00_READ_FIRST.md`). Current state: `docs/STATUS.md`.

## Bottom line
Do not deploy an LLM as an autonomous day trader; in live and look-ahead-free tests, none showed reliable alpha. Most lost money or earned factor exposure, and the few that made money did not beat buy and hold. Models never emit orders or trade intents: deterministic code generates all orders through the risk engine, while LLMs emit evidence tags, watchlist candidates, veto/pause flags, offline codegen, and review.

## Rules for the build
- Enforce strict separation: models emit only evidence tags, watchlist candidates, and veto/pause flags for deterministic rules; deterministic strategy code generates all orders through the risk engine, and shadow mode only logs outputs (our recommendation) [STATED] (research §6).
- Read balances, positions, and open orders from broker APIs; never trust LLM conversation history or vector memory for account state (our recommendation) [STATED] (research §5, §6).
- Wrap Alpaca MCP tools in our allowlist; block destructive tools (`cancel_all_orders`, `close_all_positions`, `update_account_config`) from agents, and never point an agent at the hosted live URL before building human approval (our recommendation) [STATED]. That these tools exist is [MEASURED] from [Alpaca's tool reference](https://docs.alpaca.markets/us/docs/trading-api-mcp) (research §7).
- Disable withdrawal scopes and `update_account_config` on all brokers; enforce JSON schema checks, symbol allowlists, per-order notional caps, rate limits, and draft-then-approve or paper sandboxes (our recommendation) [STATED] (research §5, §7).
- Do not route news-reaction trades through slow periodic LLM escalation (our recommendation) [STATED]. In one 2026 study of ten large stocks, buying at the next open after a headline and selling at the next close kept +0.31% after earnings news and +0.04% after other news, neither statistically significant (t=1.0 and 0.6). The first hour held under half of the whole move (+0.40% of +0.92% for earnings news, +0.09% of +0.36% for other news). A slower five-day drift after good earnings news was significant (+0.34% over SPY, t=2.2). Single preprint, one year of minute data [MEASURED] ([Wang 2026](https://arxiv.org/html/2611.19530)) (research §4).
- Limit cheap small-model screeners to structured JSON extraction (event type, polarity, novelty, provenance) on news, 8-K filings, and earnings calls; use the Perplexity Agent API for new Perplexity work since support for legacy Sonar Chat Completions ended Sep 27, 2026; synchronous requests still run, rerouted as Agent API requests (our recommendation) [STATED] (research §4, §6).
- Pass raw primary evidence (headline, timestamp, ticker, price/volume delta) with screener tags to the frontier model so summaries do not corrupt escalation (our recommendation) [STATED] (research §6).
- Limit frontier models to infrequent catalyst review, qualitative veto/pause flags, offline strategy codegen, and post-trade journaling (our recommendation) [STATED] (research §4, §6).
- Gate tiny live capital on at least `paper_min_trading_days` trading days AND `paper_min_closed_trades` closed paper trades (models off, then shadow; values in `config/thresholds.yaml`) using publication timestamps, realistic fees/slippage, and multiple seeds against buy-and-hold and trend baselines; require `scale_live_evidence_months` months live evidence to scale and a written owner decision in `docs/decisions/` for any promotion (our recommendation). The day, trade and month counts are house rules. No source derives them. Short tests are weak: an audit of published LLM trading papers puts the power to detect a true Sharpe of 1.0 at 19% for a 145-trading-day test, its median test length; working paper, not replicated ([audit output](https://raw.githubusercontent.com/Navid-A-08/LLM-Trading-Audit/main/results/summary_statistics.txt)) [STATED] (research §2, §3, §6).

## Key numbers
| Item | Value | As of | Tag | Source |
|---|---|---|---|---|
| Alpha Arena losing accounts | 31 of 38 accounts lost; $43k fees on $380k capital. Two short seasons, 6 and 8 models; a third party's recomputation from venue records | Oct-Dec 2025 | STATED | [TradingAgentStack Audit](https://tradingagentstack.com/alpha-arena-results/) |
| Look-ahead-free 4-factor alpha (rta-bench-1) | 0 of 91 runs significant; mean -2.3%/yr (95% CI -4.7% to +0.1%). In the median run, factor exposures were 78% of the absolute size of the return's parts; median R-squared 0.66. Runs on 2022 and 2020 cover dates the models may remember. Single preprint | 2026-11 | MEASURED | [Wang 2026](https://arxiv.org/html/2611.19530) |
| Stock baselines vs LLM agents (2026 rally) | Trend-following +19.0%, SPY +12.1%, best LLM average +8.1%. In the 2022 bear market the same trend rule made -5.9% (SPY -18.6%) and four of six models did better than it. Simulation, single preprint | 2026-11 | MEASURED | [Wang 2026](https://arxiv.org/html/2611.19530) |
| Crypto, 2025 historical backtest only | TCN +62.94%, XGBoost +41.93%; LLM and agent methods -9.16% to -68.62% | 2026-10 | MEASURED | [Can AI Make Money in Crypto](https://arxiv.org/html/2609.34510v1) |
| Crypto, exchange paper trading, Jun 4 to Sep 21, 2026 | The backtest order nearly reversed. Two of eight ML methods stayed profitable (XGBoost +27.53%, LSTM +34.08%; TCN -33.20%). All six LLM, agent and RL methods were positive (Qwen +37.77%). Buy and hold +30.35% | 2026-10 | MEASURED | [same paper](https://arxiv.org/html/2609.34510v1) |
| Crypto, real money, Aug 24 to Sep 21, 2026 | Four methods traded. Qwen +3.72%, LSTM -0.33%, XGBoost -0.79%, TRA -14.74%. Bitcoin buy and hold +11.63%. None beat it and all four had negative alpha. Four weeks, single preprint | 2026-10 | MEASURED | [same paper](https://arxiv.org/html/2609.34510v1) |
| Post-cutoff agent Sharpe decay | 51.48% to 62.23% drop across 5 frameworks | 2025-10 | MEASURED | [Profit Mirage](https://arxiv.org/html/2510.07920) |
| 20-year LLM backtest alpha (FINSABER) | No significant alpha (p > 0.34); B&H beats LLMs (p <= 0.0117) | 2026-08 | MEASURED | [FINSABER KDD 2026](https://waylonli.com/files/finsaber-slides.pdf) |
| Pre-cutoff S&P 500 memorization (GPT-4o) | 0.61% MAPE pre-cutoff vs 16.87% post-cutoff, for recalling index levels with no recent prices given | 2026-08 revision | MEASURED | [Lopez-Lira et al.](https://arxiv.org/html/2504.14765v2) |
| GPT-4 headline sentiment (post-cutoff) | About 90% of portfolio-days had the right sign for the immediate, non-tradable reaction. This is not accuracy per headline. Prices kept drifting the same way for 1 to 2 days, most in smaller stocks and after bad news. Before trading costs | 2026-10 | MEASURED | [Lopez-Lira & Tang JFE](https://www.sciencedirect.com/science/article/abs/pii/S0304405X26001066) |
| Output consistency at T = 0, three named setups | GPT-OSS-120B 12.5% (95% CI 3.5% to 36.0%); Granite-3-8B and Qwen2.5:7B 100%. 16 runs each. Measures repeatability, not correctness, and does not separate model size from provider | 2025-11 | MEASURED | [LLM Output Drift](https://arxiv.org/html/2511.07585) |
| Seed-to-seed return difference | 5.2 points on average between two seeds of the same model and period (54 pairs). A rerun with the same seed differed by 5.4 points (24 pairs) | 2026-11 | MEASURED | [Wang 2026](https://arxiv.org/html/2611.19530) |
| Multi-step cascade cost reduction | 72% lower cost at 97.3% of top-model quality. Two older routers applied per step on the same tasks saved 31% and 44%. Authors' own benchmark on planning, coding, research and data tasks, not trading. Workshop paper | 2026-07 | STATED | [AgentRouter ICML 2026](https://arxiv.org/pdf/2609.22951) |
| Grok/Bankrbot prompt-injection drain | 3 billion DRB tokens moved on-chain, worth $150k to $174k at the time by the report's estimate (Morse-code indirect injection). The operator says 80% was returned | 2026-05 | MEASURED for the transfer, STATED for the dollar value | [AI Incident DB 7549](https://incidentdatabase.ai/reports/7549/) |

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
- Net return, Sharpe, turnover, and fee drag over the paper gate in `config/thresholds.yaml` (models off vs shadow).
- False-positive escalation rate and latency of our small-to-large cascade.
- Run-to-run output consistency of screening and review models at T = 0.
- Incremental alpha of LLM evidence tags and veto/pause flags over deterministic baselines.
- Daily API token spend versus expected net P&L at target account size.
