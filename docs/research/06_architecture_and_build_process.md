# System Architecture, Open-Source Stack, and Phased Build Process

## Executive Summary

Building an autonomous day-trading system for both US equities and crypto requires separating deterministic trading infrastructure from probabilistic language-model reasoning. In 2026, open-source trading engines such as [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) and [QuantConnect LEAN](https://github.com/QuantConnect/Lean) provide true multi-asset, event-driven backtest-to-live parity (MEASURED), while lightweight broker SDKs such as [alpaca-py](https://github.com/alpacahq/alpaca-py), [ib_async](https://github.com/ib-api-reloaded/ib_async), and [CCXT](https://github.com/ccxt/ccxt) offer clean execution primitives without framework lock-in (MEASURED). By contrast, academic audits of LLM trading papers show that 51% deduct no trading costs and 98% of papers whose test windows may overlap model training data fail to control for look-ahead leakage ([Zhang 2026](https://arxiv.org/html/2611.18934v1)) (MEASURED). The engineering implication is strict: build a deterministic, always-on Python trading service first, isolate the LLM inside a schema-constrained agent harness that can only emit structured trade intents, and require forward shadow evaluation before risking live capital.

---

## 1. Open-Source Algorithmic Trading Frameworks (November 2026)

No single library dominates both fast research and multi-asset live execution. The table below compares 13 widely cited frameworks and execution SDKs verified against their repositories, release histories, and documentation as of November 2026.

| Framework / SDK | Asset Classes (Stocks + Crypto in One Engine?) | Backtest-Live Parity | Engine Style | Language | License | Maintenance Activity (Nov 2026) | Learning Curve |
|---|---|---|---|---|---|---|---|
| **NautilusTrader** | Yes: equities, crypto (CEX/DEX), FX, futures, options, betting via adapters ([NautilusTrader README](https://github.com/nautechsystems/nautilus_trader)) (MEASURED) | High: same event-driven strategy code runs in backtest and live ([NautilusTrader Releases](https://github.com/nautechsystems/nautilus_trader/releases)) (MEASURED) | Event-driven (tick/order-book) | Rust core + Python API | LGPL-3.0 ([NautilusTrader README](https://github.com/nautechsystems/nautilus_trader)) (MEASURED) | Very active: v1.231.0 (Aug 2026) and v2.0.0rc9 Rust+PyO3 (Nov 10, 2026) ([NautilusTrader Releases](https://github.com/nautechsystems/nautilus_trader/releases)) (MEASURED) | Steep (Rust/event concepts, breaking v2 API changes) |
| **QuantConnect LEAN** | Yes: 9 asset classes including equities, options, futures, FX, and crypto in one portfolio ([QuantConnect LEAN](https://www.lean.io/market)) (MEASURED) | High: unified engine for local/cloud backtest and 20+ brokerages ([QuantConnect GitHub](https://github.com/QuantConnect)) (MEASURED) | Event-driven | C# core + Python API (PythonNet) | Apache-2.0 ([LEAN License](https://github.com/QuantConnect/Lean/blob/master/LICENSE)) (MEASURED) | Very active: continuous commits Nov 2026; CLI v1.0.234 (Nov 18, 2026) ([LEAN CLI Releases](https://github.com/QuantConnect/lean-cli/releases)) (MEASURED) | Steep (C#/.NET build, local data formatting, paid cloud data ecosystem) |
| **Lumibot** | Yes: stocks, options, futures, forex, crypto, prediction markets via 12+ brokers/CCXT ([Lumibot Brokers](https://lumibot.lumiwealth.com/brokers.html)) (MEASURED) | High: same strategy class for backtest, paper, and live ([Lumibot Docs](https://lumibot.lumiwealth.com/lumibot_vs_openalice.html)) (STATED) | Event-driven | Python | GPL-3.0 ([Lumibot GitHub](https://github.com/Lumiwealth)) (MEASURED) | Very active: v4.6.95 released Nov 22, 2026 ([Lumibot Releases](https://github.com/Lumiwealth/lumibot/releases/tag/v4.6.95)) (MEASURED) | Low to Moderate |
| **Backtrader** | Partial: equities, FX, futures; limited crypto via third-party/CCXT add-ons ([AlgoDrill 2026](https://algodrill.app/backtesting-frameworks)) (MEASURED) | Partial: legacy IBKR/OANDA live hooks ([BacktestScore 2026](https://www.backtestscore.com/tools/backtrader)) (MEASURED) | Event-driven | Python | GPL-3.0 ([BacktestScore 2026](https://www.backtestscore.com/tools/backtrader)) (MEASURED) | Frozen upstream: last PyPI release 1.9.78.123 on Apr 19, 2023; active fork cloudQuant/backtrader v1.4.0 Sep 2026 ([PyPI back-trader-python](https://pypi.org/project/back-trader-python/)) (MEASURED) | Moderate |
| **vectorbt (OSS) / vectorbt PRO** | Yes (array columns): any OHLCV series including stocks and crypto ([VectorBT GitHub](https://github.com/polakowo/vectorbt)) (MEASURED) | None (OSS): research/backtest only; PRO adds streaming/order rules but is research-focused ([VectorBT PRO](https://vectorbt.pro/getting-started/)) (MEASURED) | Vectorized (NumPy/Numba + optional Rust) | Python + Numba/Rust | OSS: Apache-2.0 + Commons Clause (fair-code); PRO: Proprietary ($25/mo, $240/yr, $500 lifetime) ([BacktestScore 2026](https://www.backtestscore.com/tools/vectorbt)) (MEASURED) | Active: OSS v1.2.1 (Nov 11, 2026) ([VectorBT Releases](https://github.com/polakowo/vectorbt/releases)); PRO v2026.10.5 ([VectorBT PRO](https://vectorbt.pro/)) (MEASURED) | Moderate to Steep (array broadcasting, easy look-ahead bugs) |
| **Zipline-reloaded** | Primarily US equities/ETFs and futures; crypto only via custom bundles ([BacktestScore Zipline](https://www.backtestscore.com/tools/zipline-reloaded)) (MEASURED) | None: backtest-only ([BacktestScore Zipline](https://www.backtestscore.com/tools/zipline-reloaded)) (MEASURED) | Event-driven (minute/daily bars) | Python | Apache-2.0 ([Zipline-reloaded GitHub](https://github.com/stefan-jansen/zipline-reloaded/)) (MEASURED) | Maintained (maintenance-only): v3.2.1 Oct 25, 2026 for Python 3.11-3.14 ([Zipline Releases](https://github.com/stefan-jansen/zipline-reloaded/releases)) (MEASURED) | Steep (bundle ingestion, Pipeline API) |
| **Freqtrade** | No (crypto only): 12+ spot and 7 futures exchanges via CCXT ([Fincode 2026](https://fincodelabs.com/en/blog/open-source-crypto-trading-bot)) (MEASURED) | High for crypto: dry-run, backtest, hyperopt, and live share strategy code ([Fincode 2026](https://fincodelabs.com/en/blog/open-source-crypto-trading-bot)) (MEASURED) | Event-driven + vectorized pandas indicators | Python | GPL-3.0 ([Fincode 2026](https://fincodelabs.com/en/blog/open-source-crypto-trading-bot)) (MEASURED) | Very active: monthly releases, v2026.10 on Oct 30, 2026 ([Manifold-BT 2026](https://www.manifoldbt.com/guide/best-python-backtesting-libraries)) (MEASURED) | Moderate |
| **Hummingbot** | No (crypto only): CEX and DEX market-making and arbitrage ([Fincode 2026](https://fincodelabs.com/en/blog/open-source-crypto-trading-bot)) (MEASURED) | Moderate for crypto: paper-trade connectors and controllers ([Fincode 2026](https://fincodelabs.com/en/blog/open-source-crypto-trading-bot)) (MEASURED) | Event-driven (async connectors) | Python (+ TypeScript Gateway) | Apache-2.0 ([TradeBot Check 2026](https://tradebotcheck.com/compare/freqtrade-vs-jesse-vs-hummingbot/)) (MEASURED) | Active: v2.17.0 on Sep 22, 2026, commits Nov 2026 ([Fincode 2026](https://fincodelabs.com/en/blog/open-source-crypto-trading-bot)) (MEASURED) | Steep (market-making focus) |
| **Jesse** | No (crypto only): spot and perpetual futures ([TradeBot Check 2026](https://tradebotcheck.com/compare/freqtrade-vs-jesse-vs-hummingbot/)) (MEASURED) | High for crypto, but paper/live requires paid official plugin ([Fincode 2026](https://fincodelabs.com/en/blog/open-source-crypto-trading-bot)) (MEASURED) | Event-driven | Python | MIT (core); proprietary live plugin ([Fincode 2026](https://fincodelabs.com/en/blog/open-source-crypto-trading-bot)) (MEASURED) | Active: v3.6.0 on PyPI Nov 3, 2026 ([Fincode 2026](https://fincodelabs.com/en/blog/open-source-crypto-trading-bot)) (MEASURED) | Moderate |
| **backtesting.py** | Single-instrument OHLCV (stocks, FX, or crypto one at a time) ([Manifold-BT 2026](https://www.manifoldbt.com/guide/best-python-backtesting-libraries)) (MEASURED) | None: backtest-only ([PyPI backtesting](https://pypi.org/project/backtesting/)) (MEASURED) | Event-driven (bar-by-bar) | Python | AGPL-3.0 ([backtesting.py GitHub](https://github.com/kernc/backtesting.py)) (MEASURED) | Active again: v0.6.6 on Jul 22, 2026 after 2021-2025 hiatus ([backtesting.py Changelog](https://github.com/kernc/backtesting.py/blob/master/CHANGELOG.md)) (MEASURED) | Low |
| **alpaca-py** | Yes (broker SDK): US equities, options, and crypto via Alpaca ([Alpaca Docs](https://docs.alpaca.markets/us/docs/getting-started-with-trading-api)) (MEASURED) | N/A (execution/data SDK only; identical REST/WS spec for paper and live) ([Alpaca Paper Docs](https://docs.alpaca.markets/us/docs/paper-trading)) (MEASURED) | REST + WebSocket SDK | Python | Apache-2.0 ([alpaca-py GitHub](https://github.com/alpacahq/alpaca-py)) (MEASURED) | Very active: v0.45.0 on Nov 5, 2026 ([alpaca-py Releases](https://github.com/alpacahq/alpaca-py/releases/tag/v0.45.0)) (MEASURED) | Low |
| **ib_async** | Yes (broker SDK): stocks, options, futures, FX, crypto (where IBKR-supported) ([ib_async GitHub](https://github.com/ib-api-reloaded/ib_async)) (MEASURED) | N/A (execution/data SDK only; requires TWS or IB Gateway) ([ib_async GitHub](https://github.com/ib-api-reloaded/ib_async)) (MEASURED) | Async event-driven SDK | Python | BSD-2-Clause ([ib_async GitHub](https://github.com/ib-api-reloaded/ib_async)) (MEASURED) | Active: v2.0.1 (Jun 2026) and v3.0 next-protobuf for mandatory Dec 2026 TWS 10.51+ protobuf protocol ([ib_async Protobuf Docs](https://github.com/ruvr/ib_async)) (MEASURED) | Moderate (IB Gateway/IBC ops) |
| **CCXT** | No (crypto + prediction markets): 104 exchanges REST, 76 WebSocket ([CCXT Docs](https://docs.ccxt.com/docs/comparisons/ccxt-vs-xchange)) (MEASURED) | N/A (execution/data SDK only; no simulation layer) ([CCXT Docs](https://docs.ccxt.com/docs/comparisons/ccxt-vs-xchange)) (MEASURED) | Async/sync REST + WS SDK | TS, JS, Python, C#, PHP, Go, Java, Rust | MIT ([CCXT License](https://github.com/ccxt/ccxt/blob/master/LICENSE.txt)) (MEASURED) | Very active: near-daily releases, v4.5.93 on Nov 17, 2026 ([CCXT Releases](https://github.com/ccxt/ccxt/releases)) (MEASURED) | Low to Moderate |

### Framework Fit Analysis

For a solo developer targeting both US equities and crypto, three architectural paths stand out:

1. **Thin custom Python service over alpaca-py + CCXT (or ib_async) + vectorbt for research.** This avoids heavy framework abstractions, keeps execution code auditable in a few hundred lines, and lets you own the exact risk engine and LLM escalation pipeline. For IBKR users, IBKR is migrating to a Protobuf wire protocol ([IBKR Protobuf Docs](https://ibkrcampus.com/docs/tws-api/protobuf/introduction)) (MEASURED), and the community `ib_async` repository states TWS/IB Gateway 10.51+ becomes mandatory in December 2026 ([ib_async Protobuf Docs](https://github.com/ruvr/ib_async)) (STATED); verify directly with IBKR before integrating.
2. **NautilusTrader** if you need true tick-level order-book simulation and multi-venue execution parity in one engine. Its Rust core eliminates Python loop bottlenecks and enforces deterministic event replay ([NautilusTrader GitHub](https://github.com/nautechsystems/nautilus_trader)) (MEASURED), though the ongoing v2.0 release-candidate transition carries API churn ([NautilusTrader Releases](https://github.com/nautechsystems/nautilus_trader/releases)) (MEASURED).
3. **Avoid** upstream Backtrader (frozen since April 2023), crypto-only bots (Freqtrade, Hummingbot, Jesse) as a unified stocks+crypto engine, and Lumibot's built-in "AI agents that place trades directly" pattern ([Lumibot GitHub](https://github.com/Lumiwealth)) (STATED), because giving an LLM direct order-placement tools collapses the boundary between probabilistic reasoning and deterministic risk control.

---

## 2. Reference Architecture for an AI-Assisted Trading System

> Superseded 2026-11-24. The diagram and text below show a model returning a `TradeIntent`. Models never emit orders or trade intents; deterministic strategy code produces every `TradeIntent`. The current diagram is in `docs/playbook/06_architecture_and_build.md`. `AGENTS.md` and `docs/decisions/0001-starting-decisions.md` win. This text is kept as the audit trail.


An LLM should never hold broker credentials or directly invoke `submit_order`. LLMs are non-deterministic, vulnerable to prompt injection from external market news ([OWASP Prompt Injection Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)) (MEASURED), and prone to overconfident narrative bias ([Evaluating LLMs in Finance 2026](https://arxiv.org/html/2602.14233)) (MEASURED). Instead, the system should be built as a deterministic event-driven pipeline where the LLM operates as an advisory analyst that outputs strictly typed JSON trade intents validated by a deterministic risk engine.

```
+-----------------------------------------------------------------------------------+
|                        1. DATA INGESTION LAYER (Always-On)                        |
|  [Alpaca/IBKR WS: US Equities]  [CCXT WS: Crypto]  [News/Filings/Macro Feeds]     |
+-----------------------------------------+-----------------------------------------+
                                          | Normalized MarketEvent / NewsEvent
                                          v
+-----------------------------------------------------------------------------------+
|                 2. DETERMINISTIC SCANNERS & SIGNAL ENGINE (Pure Code)             |
|  Feature Store (Bars, VWAP, ATR, Spread, Vol) -> Rule Filters -> Candidate Setups |
+-----------------------------------------+-----------------------------------------+
                                          | CandidateSignal (rate-limited)
                                          v
+-----------------------------------------------------------------------------------+
|                     3. EVENT BUS & ESCALATION GATE (Pure Code)                    |
|  Dedup, Cooldowns, Market-Hours Gate, Spread/Liquidity Gate, Token Budget Cap     |
+---------------------+---------------------------------------+---------------------+
                      | Baseline Path (No LLM)                | Escalated Events Only
                      |                                       v
                      |             +-----------------------------------------------+
                      |             |    4. LLM ANALYST TIER (Sandboxed Harness)    |
                      |             |  [Tier 1: Cheap/Fast Model -> Triage/Score]   |
                      |             |         | (Only high-conviction escalations)  |
                      |             |         v                                     |
                      |             |  [Tier 2: Frontier Model -> TradeIntent JSON] |
                      |             |  (No broker keys; strict Pydantic schema)     |
                      |             +-----------------------+-----------------------+
                      |                                     | TradeIntent (or Shadow Log)
                      v                                     v
+-----------------------------------------------------------------------------------+
|                 5. DETERMINISTIC RISK ENGINE (Hard Veto Authority)                |
|  - Max Position Size & Gross Exposure   - Allowed Symbol Whitelist                |
|  - Max Daily Realized + Unrealized Loss - Market-Hours & Stale-Quote Check        |
|  - Max Orders/Min & Duplicate Check     - Global Kill Switch (File/DB/API Flag)   |
+-----------------------------------------+-----------------------------------------+
                                          | ApprovedOrder (with pre-assigned UUID)
                                          v
+-----------------------------------------------------------------------------------+
|              6. ORDER MANAGEMENT & EXECUTION (OMS / Broker Adapters)              |
|  Idempotent client_order_id -> [alpaca-py / ib_async / CCXT] -> Fill Reconciler   |
+---------------------+---------------------------------------+---------------------+
                      |                                       |
                      v                                       v
+-------------------------------------------+   +-----------------------------------+
|      7. STATE STORE & AUDIT JOURNAL       |   |   8. MONITORING, ALERTS & UI      |
|  Postgres / SQLite (WAL):                 |   |  - Healthchecks & Heartbeats      |
|  - Positions, Orders, Fills, Balances     |   |  - Discord/Slack/SMS Alerts       |
|  - Append-Only Decision Journal (Prompt,  |   |  - Read-Only Web Dashboard        |
|    Context Snapshot, Model Output, Risk   |   |  - Emergency Kill-Switch Endpoint |
|    Verdict, Execution Slippage)           |   +-----------------------------------+
+-------------------------------------------+
```

### Layer Responsibilities

- **Data Ingestion:** Maintains persistent WebSocket connections for US equities (e.g., Alpaca or IBKR) and crypto (CCXT/exchange WS), normalizes symbols and timestamps to UTC, and writes raw bars and news items into a point-in-time store.
- **Deterministic Scanners and Signal Engine:** Computes technical features, liquidity checks, and baseline entry/exit signals in pure Python/NumPy. Running deterministic baselines continuously provides a benchmark to test whether the LLM adds net value.
- **Event Bus and Escalation Gate:** Prevents LLM cost blowups and thrashing by enforcing per-symbol cooldowns, minimum volatility/volume thresholds, and daily API spend caps before invoking any model.
- **LLM Analyst Tier:** Operates in two stages. Tier 1 (a cheap, fast model) triages news/headlines and market snapshots into a structured relevance score; only events exceeding a pre-set threshold escalate to Tier 2 (a frontier reasoning model). Both tiers emit JSON validated against a strict Pydantic `TradeIntent` schema (symbol, direction, thesis, confidence, invalidation price, TTL). Any parse error or out-of-schema field defaults to `NO_ACTION`.
- **Deterministic Risk Engine:** Holds absolute veto power over every `TradeIntent` before it reaches the OMS. It enforces hard limits: max notional per trade, max portfolio concentration, max daily drawdown (e.g., 1.5%-2.0% of equity), max orders per minute, symbol allowlist, regular-trading-hours enforcement for equities, stale-quote rejection (e.g., reject if last tick >5 seconds old), and an external kill switch.
- **Order Management System (OMS):** Persists a pre-generated `client_order_id` UUID to the state store before sending the HTTP/FIX request so network timeouts can be reconciled idempotently ([Alpaca Audit Trail Guide](https://alpaca.markets/learn/ai-agent-audit-trail-alpaca-paper-order)) (MEASURED).
- **State Store and Append-Only Journal:** SQLite (in WAL mode) is sufficient for a single-node personal bot; PostgreSQL is better if you run multiple workers or a separate dashboard container. Every decision cycle logs the exact `trace_id`, market snapshot, prompt hash, raw model response, parsed `TradeIntent`, risk engine checks, and final fill price so you can audit slippage and replay decisions offline.
- **Monitoring, Alerting, and Dashboard:** Tracks WebSocket disconnects, order rejections, daily P&L, API token spend, and heartbeats (e.g., Dead Man's Snitch / Healthchecks.io). Alerts fire to Slack/Telegram/SMS on kill-switch trips or reconciliation mismatches.

---

## 3. Harness vs. Application: Concrete Split

> Superseded 2026-11-24. The harness described below returns a `TradeIntent`. It returns only evidence tags, watchlist candidates and pause or veto flags. `AGENTS.md` and `docs/decisions/0001-starting-decisions.md` win. This text is kept as the audit trail.


Conflating the agent harness with the trading application is a common architectural mistake. Define them strictly:

- **The Trading Application (Always-On Service):** A deterministic Python daemon running 24/7 on a VPS. It owns WebSocket feeds, bar aggregation, deterministic signals, the risk engine, order execution, state reconciliation, and the kill switch. It must function cleanly with the LLM completely disabled.
- **The Agent Harness (Library + Eval Suite):** The loop, prompt templates, read-only context builders, strict JSON schemas, model-routing logic, replay runner, and offline evaluation suite that allow an LLM to inspect market context and return a `TradeIntent`.
- **Perplexity Surface (Skills, Automations, Teammates):** Best used for asynchronous research, daily pre-market/post-market briefings, strategy ideation, news-catalyst deep dives, and reviewing journaled trade postmortems.

**Recommended Split:** Keep the Python trading application and the agent harness in the same monorepo so they share identical domain models (`MarketSnapshot`, `TradeIntent`, `RiskDecision`) and cannot drift out of sync. Do not use Perplexity Computer or scheduled chat automations as the live order-execution loop: chat/automation platforms are designed for asynchronous, high-latency workflows without persistent WebSocket state, sub-second stop-loss monitoring, or deterministic crash recovery. Instead, call the Perplexity Agent API (legacy Sonar Chat Completions ended Sep 27, 2026; [Perplexity Sonar Migration](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/overview)) (MEASURED) or other LLM APIs from inside the harness's Tier 1/Tier 2 analyst layer when grounded web/news synthesis is needed, and use Perplexity Computer/Teammates out-of-band to audit daily performance logs and research new hypotheses.

---

## 4. Proposed Monorepo Layout, CI, and Safe Paper/Live Switching

A single monorepo keeps research, strategy code, risk rules, agent prompts, and deployment manifests versioned together. Secrets never enter the repository.

```text
trading-platform/
├── .env.example                  # Documented env vars with dummy values ONLY
├── .gitignore                    # Blocks .env, *.key, data/, *.db, logs/
├── pyproject.toml                # uv/pip dependencies, ruff, mypy, pytest config
├── docs/
│   ├── research/                 # Strategy hypotheses, pre-registered specs
│   ├── adr/                      # Architecture Decision Records
│   └── runbooks/                 # Incident response, kill-switch, recovery steps
├── config/
│   ├── paper.yaml                # Paper endpoints, relaxed shadow logging
│   ├── live.yaml                 # Live endpoints, strict notional & loss caps
│   └── universe.yaml             # Explicitly whitelisted equity & crypto symbols
├── src/
│   ├── core/                     # Shared Pydantic models (Bar, TradeIntent, Order)
│   ├── data/                     # Market data ingestors, point-in-time cache
│   ├── strategies/               # Deterministic baseline scanners & signal rules
│   ├── backtests/                # vectorbt / event-driven replay + cost models
│   ├── agents/                   # Agent harness (NO broker write credentials)
│   │   ├── prompts/              # Versioned prompt templates (YAML/Jinja)
│   │   ├── schemas/              # Strict structured output schemas
│   │   ├── router.py             # Tier 1 cheap -> Tier 2 frontier escalation
│   │   └── evals/                # Offline replay, schema-validity, injection tests
│   ├── risk/                     # Deterministic risk engine & kill-switch logic
│   ├── execution/                # OMS, alpaca-py, ib_async, CCXT adapters
│   └── services/                 # Always-on FastAPI/asyncio daemon & dashboard
├── infra/
│   ├── Dockerfile
│   ├── docker-compose.yml        # Trading service + Postgres + Prometheus/Grafana
│   └── systemd/                  # Process supervision & auto-restart units
├── tests/
│   ├── unit/                     # Risk rules, schema validation, sizing math
│   ├── integration/              # Broker paper-sandbox mocks, idempotency tests
│   └── regression/               # Deterministic backtest golden-output checks
└── .github/workflows/
    └── ci.yml                    # Lint, mypy, pytest, gitleaks, backtest regression
```

### CI Pipeline Ideas

- **Static and Secret Checks:** Run `ruff`, `mypy --strict`, and `gitleaks` (or `trufflehog`) on every PR to block accidental API key commits.
- **Risk Engine Unit Suite:** Require 100% branch coverage on `src/risk/` (verifying max loss vetoes, stale-quote halts, symbol allowlists, and kill-switch overrides).
- **Backtest Regression Test:** Run a fast deterministic backtest on a fixed historical fixture and assert that Sharpe, trade count, and fill prices match a locked baseline, catching unintended indicator or cost-model regressions.
- **Agent Harness Evals:** Replay recorded market+news fixtures against prompt changes to verify JSON schema compliance, latency, token budget, and resistance to embedded prompt-injection payloads.

### Safe Paper-to-Live Switching

Environment misconfiguration is a real source of accidental live orders. For example, Alpaca's own engineering guidance warns that `ALPACA_PAPER_TRADE` only stays in paper mode for explicit truthy values and that typos or conflicting CLI flags can silently route orders to live endpoints ([Alpaca Audit Trail Guide](https://alpaca.markets/learn/ai-agent-audit-trail-alpaca-paper-order); [Alpaca Skills Paper-Trading Guard](https://github.com/alpacahq/alpaca-skills/blob/HEAD/skills/trading-api/paper-trading-cli/SKILL.md)) (MEASURED). Enforce four-key safety on startup:

1. **Default to Paper:** If `TRADING_MODE` is unset or anything other than the exact string `LIVE`, fail closed or boot in `PAPER`.
2. **Separate Secret Stores:** Store paper keys and live keys under distinct variable names (e.g., `ALPACA_PAPER_KEY` vs. `ALPACA_LIVE_KEY`) injected via a secret manager (1Password CLI, Doppler, AWS Secrets Manager, or encrypted systemd credentials), never in `.env` files committed to git.
3. **Explicit Live Confirmation Flag:** Require both `TRADING_MODE=LIVE` and `CONFIRM_LIVE_CAPITAL=YES_I_UNDERSTAND` plus a non-empty `MAX_DAILY_LOSS_USD` cap.
4. **Startup Endpoint Assertion:** On boot, query the broker account endpoint and assert that the resolved base URL (`https://paper-api.alpaca.markets` vs. `https://api.alpaca.markets`) and account ID match `TRADING_MODE`; abort with a non-zero exit code on any mismatch ([Alpaca Paper-Trading Guard](https://github.com/alpacahq/alpaca-skills/blob/39111abee6b60af7c11d40b5fc892dfc4fd791a4/skills/trading-api/paper-trading/SKILL.md)) (MEASURED).

---

## 5. Hosting Options, Monthly Costs, and Operational Reliability

A trading bot needs persistent WebSocket connections, stable outbound IP addresses (for exchange IP allowlisting), local disk/database durability, and predictable uptime.

| Hosting Option | Estimated Monthly Cost (Nov 2026) | Always-On WS Support | Static IP for Allowlisting | Key Trade-Offs |
|---|---|---|---|---|
| **Hetzner Cloud (CX23: 2 vCPU, 4 GB RAM, 40 GB NVMe)** | EUR 5.49-5.99/mo excl. VAT (~$6-$7/mo) after Apr/Jun 2026 price hikes ([xCloud 2026](https://xcloud.host/best-docker-hosting-providers/); [xCloud AI Hosting](https://xcloud.host/best-ai-agent-hosting/index.md)) (MEASURED) | Yes | Yes | Best price/performance; DIY Linux/Docker ops; US locations (Ashburn/Hillsboro) available. |
| **DigitalOcean Droplet** | $4/mo (512 MB) to $24/mo (4 GB / 2 vCPU) ([Fly.io Docker Comparison](https://fly.io/learn/docker-hosting/); [xCloud 2026](https://xcloud.host/best-docker-hosting-providers/)) (MEASURED) | Yes | Yes | Simple flat billing and strong docs; higher cost per GB RAM than Hetzner. |
| **Fly.io (MicroVMs)** | $1.94-$2.19/mo (256 MB) to $6.39/mo (1 GB) + $0.15/GB volumes ([Fly.io Docker Comparison](https://fly.io/learn/docker-hosting/); [xCloud 2026](https://backend.xcloud.host/best-docker-hosting-providers/)) (MEASURED) | Yes | Dedicated IPv4 extra | Fast container deploys near US East exchanges (Ashburn); no permanent free tier since Oct 2024 ([SnapDeploy 2026](https://snapdeploy.dev/state-of-free-hosting)) (MEASURED). |
| **Railway (Hobby)** | $5/mo minimum (incl. $5 usage); ~$15+/mo for a 24/7 0.5 vCPU/0.5 GB service ([xCloud AI Hosting](https://xcloud.host/best-ai-agent-hosting/index.md)) (MEASURED) | Yes | Outbound IP not fixed on Hobby | Easy Git-push + Postgres; metered billing can spike on memory-heavy Python services. |
| **Oracle Cloud Always Free** | $0/mo (halved on Jun 15, 2026 to 2 Arm OCPUs, 12 GB RAM, 200 GB disk) ([Oracle Free Tier Docs](https://docs.oracle.com/iaas/Content/FreeTier/freetier.htm); [SnapDeploy 2026](https://snapdeploy.dev/state-of-free-hosting)) (MEASURED) | Yes | Yes | Secondary reports state idle instances (<20% utilization over 7 days) may be reclaimed and capacity errors are frequent ([SnapDeploy 2026](https://snapdeploy.dev/state-of-free-hosting)) (STATED). Avoid for live capital. |
| **Home Machine / Raspberry Pi** | ~$1-$3/mo electricity + hardware | Yes | Usually dynamic IP | Vulnerable to residential ISP drops, power outages, and dynamic IP breaks on exchange allowlists. Acceptable for Phase 1-2 research/paper, risky for live day trading. |
| **Serverless / Cron (AWS Lambda, Cloudflare Workers, GitHub Actions)** | $0 within free tiers: Lambda 1M req/mo, Workers 100k req/day (10 ms CPU cap), GH Actions 5-min cron floor ([SnapDeploy 2026](https://snapdeploy.dev/state-of-free-hosting); [PublicAPIs 2026](https://publicapis.dev/blog/free-api-hosting)) (MEASURED) | No | No (without paid NAT gateway) | Unsuitable for always-on execution: cold starts, no persistent WebSockets, cron jitter, and no continuous stop-loss monitoring. Note AWS also replaced its old 12-month EC2 free tier in Jul 2025 with $200 expiring credits ([SnapDeploy 2026](https://snapdeploy.dev/state-of-free-hosting)) (MEASURED). |

### Reliability Engineering Requirements

- **Reconnect and Gap Backfill:** WebSocket clients must implement exponential backoff with jitter, heartbeat pings, and automatic REST backfill for missed bars upon reconnection.
- **Idempotent Order Submission:** Generate and persist a deterministic `client_order_id` UUID before every order request; if a network timeout occurs, query the broker by `client_order_id` before ever retrying ([Alpaca Audit Trail Guide](https://alpaca.markets/learn/ai-agent-audit-trail-alpaca-paper-order)) (MEASURED).
- **Clock Synchronization:** Run `chrony` or `systemd-timesyncd` so system time stays within milliseconds of UTC; exchange APIs (such as Kraken nonces and signed HMAC timestamps) reject requests with drifted clocks ([Kraken Error Docs](https://docs.kraken.com/exchange/guides/general/errors)) (MEASURED).
- **Restart Recovery:** Treat the broker as the source of truth on startup. Before enabling new signals, reconcile local SQLite/Postgres positions and open orders against broker state; halt and alert if an unexplained discrepancy appears.
- **Broker Outage Handling:** Trip an automatic circuit breaker on consecutive 5xx/rate-limit errors or stale quotes, cancel resting entry orders where possible, and avoid placing blind market orders into degraded feeds.

---

## 6. Phased Build Plan and Go/No-Go Gates

> Superseded 2026-11-24. The sample sizes, the Phase 1 Sharpe and profit-factor gates, the Phase 3 `TradeIntent` wording and the live money figures in this table are replaced by the keys in `config/thresholds.yaml`. Live capital and loss limits are owner numbers and are open. Build durations were removed on 2026-11-24 because agent time estimates are not used here; sample sizes stay as evidence. `AGENTS.md` and `docs/decisions/0001-starting-decisions.md` win. This text is kept as the audit trail.


Never jump from an idea to live autonomous trading. Each phase requires pre-registered exit criteria written before the phase starts to prevent moving the goalposts.

| Phase | Scope | Minimum Duration / Sample | Concrete Go/No-Go Exit Criteria |
|---|---|---|---|
| **Phase 0: Research and Strategy Spec** | Define universe, timeframe, holding period, deterministic entry/exit rules, cost assumptions, and exact role of LLM tier. | No minimum sample | Signed strategy spec in `docs/research/`; explicit fee/spread/slippage model; zero code written for live execution yet. |
| **Phase 1: Data and Backtesting** | Build point-in-time data pipeline and deterministic backtests with realistic fees, spread, slippage, and borrow/funding costs. Validate via walk-forward and Combinatorial Purged Cross-Validation (CPCV). | Multi-regime history (bull, bear, high-vol) | Out-of-sample net Sharpe > 1.0 (STATED heuristic), Deflated Sharpe Ratio (DSR) statistically significant after trial-count adjustment ([Bailey & Lopez de Prado 2014](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)) (MEASURED), Probability of Backtest Overfitting (PBO) < 0.25 ([Bailey et al. 2015](https://papers.ssrn.com/sol3/Delivery.cfm?abstractid=2326253)) (MEASURED), profit factor > 1.3, max drawdown within risk budget. |
| **Phase 2: Deterministic Paper Trading** | Deploy the always-on Python service (LLM disabled) against Alpaca paper and crypto sandbox/paper feeds. | 4-8 weeks and >= 100 closed trades | Zero unhandled crashes or duplicate orders; realized slippage within 1.5x of backtest cost model; paper equity curve and win rate consistent with out-of-sample backtest distribution. |
| **Phase 3: LLM Tier in Shadow Mode** | Enable Tier 1 + Tier 2 LLM harness in parallel. The deterministic baseline still trades paper; the LLM logs structured `TradeIntent` verdicts without executing. | 4-8 weeks and >= 100 escalated events | Schema validity >= 99.5%; zero prompt-injection escapes in red-team tests; shadow LLM portfolio outperforms deterministic baseline net of LLM API token costs and realistic decision-latency slippage. |
| **Phase 4: Tiny Live Capital** | Switch to a ring-fenced live account ($500-$2,000 total; max $100-$200 per position; hard $25-$50 daily loss kill switch). | 4-8 weeks and >= 50 live trades | Realized live slippage, fill rate, and net expectancy match Phase 2/3 paper results within pre-set tolerance (e.g., within 20% of expected cost/slippage); zero risk-engine bypasses. |
| **Phase 5: Gradual Scale** | Increase capital in fixed tranches (e.g., 2x per quarter) only after reviewing full journaled attribution. | Ongoing quarterly reviews | Rolling 60-day live Sharpe, max drawdown, and turnover stay inside pre-registered bounds; immediate auto-derisk if drawdown hits 1.5x backtest max drawdown. |

### Core Metrics to Track Continuously

- **Risk-Adjusted Return and Overfitting Control:** Net Sharpe ratio, Deflated Sharpe Ratio (DSR) accounting for total strategy trials ([Bailey & Lopez de Prado 2014](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)) (MEASURED), and Combinatorial Purged Cross-Validation (CPCV), which synthetic controlled experiments show achieves lower PBO and better DSR than standard K-fold or walk-forward alone ([Arian et al. 2024](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID4686376_code4361537.pdf?abstractid=4686376&mirid=1)) (MEASURED).
- **Execution Quality:** Realized slippage (bps) vs. modeled slippage, fill ratio on limit orders, and average decision-to-submission latency.
- **Strategy Health:** Max drawdown, profit factor, hit rate vs. payoff ratio, daily turnover, and fee drag as a percentage of gross P&L.
- **LLM Value-Add:** Decision agreement rate with the deterministic baseline, veto precision (when the LLM rejects a baseline trade, did that trade lose money?), incremental net P&L minus API token spend, and latency-adjusted alpha decay.

---

## 7. Evaluating the LLM Tier and Preventing Look-Ahead Leakage

Historical backtesting of LLM trading agents is fundamentally unreliable inside a model's pre-training window. Recent empirical research identifies two distinct leakage channels: **parametric look-ahead bias**, where model weights already memorize historical price paths and macro outcomes, and **retrieval/RAG leakage**, where web or news indices return edited or post-hoc articles ([Evaluating LLMs in Finance 2026](https://arxiv.org/html/2602.14233); [Li et al. 2026 FinCAD](https://arxiv.org/html/2605.24564)) (MEASURED). A November 2026 audit of 91 LLM trading papers found that 40% never discuss training leakage, 32% only acknowledge it without control, and only 7% simultaneously control for costs, leakage, and multiple-testing trial counts ([Zhang 2026](https://arxiv.org/html/2611.18934v1)) (MEASURED). Furthermore, benchmarking shows that LLMs cannot reliably self-report whether they already know a historical outcome, meaning prompting a model to "pretend it is 2022" fails as a guardrail ([Qian et al. 2026](https://arxiv.org/html/2611.06808)) (MEASURED). Even statistical corrections like DSR cannot catch leakage: a deliberately leaky feature posting a Sharpe of 35 passes DSR and PBO tests completely ([Leakage-Safe Strategy Discovery 2026](https://arxiv.org/html/2608.27734)) (MEASURED).

### Concrete Evaluation Protocol

1. **Ablation Matrix in Forward Shadow Mode:** Never evaluate the LLM in isolation. Run three parallel shadow tracks on live post-cutoff market data: (A) Deterministic baseline only, (B) Deterministic + Tier 1 cheap triage filter, and (C) Deterministic + Tier 1 triage + Tier 2 frontier model. Only promote (B) or (C) if it beats (A) net of API token costs and realistic execution delay (e.g., pricing the fill 5-15 seconds after the signal timestamp to reflect LLM inference latency).
2. **Strict Post-Cutoff Forward Testing:** Treat any historical LLM backtest prior to the model's training cutoff as a smoke test for code and prompt formatting only, never as evidence of alpha ([Benhenda 2026 Look-Ahead-Bench](https://web3.arxiv.org/pdf/2601.13770)) (MEASURED).
3. **Entity Anonymization for Offline Prompt Iteration:** When testing news-sentiment prompts on historical headlines, strip company names, tickers, and dates as demonstrated by [Glasserman & Lin (2023/2025)](https://arxiv.org/html/2309.17322) (MEASURED) to reduce both memorization and company-name distraction effects.
4. **Point-in-Time Context Snapshots:** Save immutable JSON snapshots of every bar, quote, and news item at exact arrival time during paper trading so offline harness evals replay strictly causal inputs.

---

## 8. Security Architecture

Autonomous trading systems combine two high-risk attack surfaces: API keys controlling real money and LLM agents ingesting untrusted text from the open internet.

### Credential and Account Isolation

- **Withdrawal-Disabled, Least-Privilege Keys:** Every exchange and broker API key used by the bot must have `Withdraw` and `Add Withdrawal Address` permissions strictly disabled; grant only balance/position read and order create/cancel scopes ([Kraken API Key Permissions](https://docs.kraken.com/exchange/guides/rest/api-keys)) (MEASURED).
- **IP Allowlisting:** Bind every crypto exchange API key to the static IPv4 address of your VPS so a leaked key cannot be used from any other host ([Coinbase CDP Security Best Practices](https://docs.cdp.coinbase.com/get-started/authentication/security-best-practices); [Kraken API Key Permissions](https://docs.kraken.com/exchange/guides/rest/api-keys)) (MEASURED).
- **Ring-Fenced Capital:** Fund a dedicated sub-account or separate brokerage account holding only the capital allocated to the bot (e.g., $500-$2,000 in Phase 4). Never connect an autonomous bot to a primary retirement or savings account ([CoinQuant 2026](https://www.coinquant.ai/blog/api-key-permissions-trading-bots-ai-agents)) (STATED).
- **Key Rotation and Expiry:** Set API key expiration dates where supported (e.g., Kraken) and rotate keys every 60-90 days ([Kraken Org API Keys](https://support.kraken.com/articles/organizations-api-keys)) (MEASURED).

### Prompt-Injection Defenses for Web-Reading Agents

Prompt injection is ranked as the #1 risk in the OWASP Top 10 for LLM Applications (LLM01:2025) ([OWASP Prompt Injection Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)) (MEASURED). An attacker who embeds hidden instructions in a financial blog, SEC filing comment, X post, or token metadata could attempt to trick a web-reading trading agent into buying an illiquid ticker or dumping a position.

- **Architectural Control-Data Separation (CaMeL / Dual-LLM Pattern):** System-level defenses such as Google DeepMind's CaMeL separate trusted control flow from untrusted data flow, solving 77% of AgentDojo tasks under attack with zero policy violations in its threat model versus 84% undefended ([Debenedetti et al. 2025](https://arxiv.org/html/2503.18813)) (MEASURED). Apply this principle directly: the LLM that reads untrusted web/news text is a **quarantined extractor** with zero write tools. It can only output a fixed JSON schema (e.g., `catalyst_type`, `sentiment_score`, `cited_facts`, `confidence`).
- **No Arbitrary Tool Execution:** The LLM never selects broker endpoints, never constructs arbitrary order parameters outside whitelisted enums, and never sees environment variables or API keys.
- **Deterministic Post-Validation:** Every field produced by the LLM is validated by the deterministic risk engine against hard allowlists (permitted liquid symbols only, max notional, max daily loss, price-collar check against live NBBO/mid-price). Even a fully hijacked LLM cannot trade a micro-cap pump-and-dump ticker outside `config/universe.yaml` or exceed your daily loss cap.
- **Human Approval Gates:** Require out-of-band human confirmation (e.g., Telegram/Slack signed button or manual config commit) for any capital-limit increase, universe expansion, or transition from paper to live mode.

---

## Implications for Our Build

> Superseded 2026-11-24. Durations in this list are superseded by `config/thresholds.yaml`. `AGENTS.md` and `docs/decisions/0001-starting-decisions.md` win. This text is kept as the audit trail.


1. **Start with a thin Python service over `alpaca-py` (US equities) and `CCXT` (crypto), paired with `vectorbt` for fast offline research.** Avoid Backtrader (frozen since 2023) and avoid heavy multi-language frameworks like LEAN or NautilusTrader v2 RC until a deterministic strategy proves positive net expectancy in paper trading. If you later need IBKR execution, build on `ib_async` 3.0 (`next-protobuf`) for IBKR's mandatory December 2026 protocol change.
2. **Build the deterministic system first and treat the LLM as a guilty-until-proven-innocent plugin.** Run the deterministic baseline in Phase 2 paper trading for at least 4-8 weeks, then add the cheap-triage-to-frontier LLM harness in Phase 3 shadow mode. Keep the LLM only if forward, post-cutoff shadow results beat the deterministic baseline net of API token costs and inference latency.
3. **Use Perplexity Computer and Teammates out-of-band, not as the execution loop.** Host the always-on Python daemon on a ~$6-$7/month Hetzner CX23 (or $12-$24/month DigitalOcean Droplet) with a static IP, `chrony` time sync, SQLite WAL (or Postgres), and pre-persisted `client_order_id` UUIDs. Use Perplexity products for pre-market research, catalyst synthesis (via API inside the quarantined harness), and automated post-trade journal reviews.
4. **Enforce hard deterministic security and risk boundaries from day one.** Use withdrawal-disabled, IP-allowlisted API keys on a ring-fenced sub-account, pin paper-mode startup assertions in code, isolate untrusted web/news text inside a schema-only quarantined LLM, and give the deterministic risk engine absolute veto power and a one-click kill switch.
