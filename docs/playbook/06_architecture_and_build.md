# Architecture and Build Playbook
Source: docs/research/06_architecture_and_build_process.md
Last verified: 2026-11-24

> Note added 2026-11-25. This page is from reading only. Nothing here is built and no build has started. The code in `research_rig/` is a test rig for past prices and is not the product or a start on it. The owner's build method is in `docs/quality/`, and it comes before this page. The lines under "Rules for the build" on this page are research recommendations from reading. None is an owner decision, except where a line repeats a hard rule from `AGENTS.md`: that rule is in force whatever this page calls it. The owner's quality files pick no strategy and no stack, and nothing is built until he has approved a written spec (`docs/quality/00_READ_FIRST.md`). Current state: `docs/STATUS.md`.

## Bottom line
Build a deterministic Python daemon over `alpaca-py`, `CCXT`, and `vectorbt`. Models never emit orders or `TradeIntent` objects; the keyless harness outputs only evidence tags, watchlist candidates, and veto/pause flags (shadow-logged only), while deterministic strategy code produces every `TradeIntent` for the risk engine. Keep model output research-only unless post-cutoff shadow testing beats baseline net of costs and latency, and require a written owner decision in `docs/decisions/` before live capital.

## Rules for the build
- Start with a thin Python daemon over `alpaca-py`, `CCXT`, and `vectorbt`; adopt `NautilusTrader` or `LEAN` only after paper profitability (our recommendation) [STATED] (research §1).
- Defer IBKR in MVP; before adding it, verify the TWS/IB Gateway Protobuf minimum with IBKR and test a Protobuf-capable client (our recommendation) [STATED] (research §1).
- Generate `TradeIntent` objects and orders only in deterministic strategy code gated by the risk engine; limit the keyless harness to evidence tags, watchlist candidates, and veto/pause flags (shadow-logged only; our recommendation) [STATED] (research §2).
- Keep daemon and harness in one monorepo; use Perplexity Agent API for new grounded research (Sonar Chat Completions ended Sep 27, 2026) and keep Computer/Teammates out-of-band (our recommendation) [STATED] (research §3).
- Pin the paper endpoint for the MVP and verify account/mode at startup and before every submission; reject live flags/keys, separate secret stores, and require a written `docs/decisions/` approval for live deployment (our recommendation) [STATED] (research §4, §8).
- Run on a static-egress Linux VPS with `chrony` UTC sync, reconnect/backfill, and startup broker reconciliation; halt new entries and alert on state mismatches, stale quotes, or sustained broker failure (our recommendation) [STATED] (research §2, §5).
- Persist one `client_order_id` UUID per attempt and disable auto-retries; on ambiguous submission, reconcile the original ID and halt/alert if unresolved rather than resubmit (our recommendation) [STATED] (research §5).
- Pre-register costs, walk-forward/CPCV, trial-adjusted DSR, and a project PBO heuristic (under `backtest_max_pbo`); require at least `paper_min_trading_days` trading days AND `paper_min_closed_trades` closed paper trades (models off, then shadow) before tiny live capital, and `scale_live_evidence_months` months live before scaling. Live capital and loss limits are owner numbers and are open: `live_starting_capital_usd`, `live_max_position_usd`, `live_max_daily_loss_usd`, `live_max_total_loss_usd`. No agent may assume a value for them. All keys: `config/thresholds.yaml` (our recommendation) [STATED] (research §6).
- Gate Phase 3 shadow on `shadow_min_escalated_events` escalated events, `shadow_min_schema_validity` schema validity, `shadow_max_injection_escapes` injection escapes in red-team tests, and post-cutoff ablation net of token costs and latency (our recommendation) [STATED] (research §6, §7).
- Disable withdrawal scopes, use IP-allowlisted least-privilege keys on a ring-fenced sub-account, isolate untrusted text in a tool-less extractor, and red-team injection resistance ourselves (our recommendation) [STATED] (research §8).

```text
[Alpaca/CCXT WS + News] -> [Deterministic Scanners]
          |                          |
          | (Read-only context)      | (Market state + optional consumed signals)
          v                          v
[Sandboxed LLM Harness]     [Deterministic Strategy Rules] -> [TradeIntent]
(No keys; Triage->Frontier)          ^                              |
          |                          |                              v
          +-> [Evidence Tags / Watchlist / Veto-Pause Flags]  [Deterministic Risk Engine]
          |   (Logged only in shadow; NO arrow to OMS)        (Size, Loss, Stale-Quote, Kill)
          v                                                         |
[Append-Only Shadow Journal & Ablation Metrics]                     v
                                                      [Idempotent OMS: UUID, No Auto-Retry]
                                                                    |
                                                                    v
                                                      [Broker Fill Reconciler + WAL State]
```

## Key numbers

| Item | Value | As of | Tag | Source |
|---|---|---|---|---|
| PBO methodology | CSCV estimates overfitting probability; the project threshold `backtest_max_pbo` is our heuristic, not a universal paper cutoff | 2015 | MEASURED | [Bailey et al. 2015](https://papers.ssrn.com/sol3/Delivery.cfm?abstractid=2326253) |
| Static-egress VPS | Verify checkout region, SKU, egress IP, and backup cost before committing; comparison prices are not deployment quotes | 2026-11-24 | UNKNOWN | [xCloud 2026](https://xcloud.host/best-docker-hosting-providers/) |
| LLM trading paper audit | 38/75 trading tests deduct no costs; 50/51 known-or-possible overlap tests lack specified chronological controls | 2026-11 | MEASURED | [Zhang 2026](https://arxiv.org/html/2611.18934v1) |
| CaMeL injection benchmark | 77% tasks solved with 0 policy violations under CaMeL's stated AgentDojo threat model; not validation of our harness | 2025-03 | MEASURED | [Debenedetti et al. 2025](https://arxiv.org/html/2503.18813) |
| Legacy Perplexity Sonar API | Legacy Sonar Chat Completions ended Sep 27, 2026; use Perplexity Agent API for new work | 2026-11 | MEASURED | [Perplexity Migration Docs](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/overview) |
| Upstream `Backtrader` status | Frozen since v1.9.78.123 (Apr 19, 2023) | 2026-11 | MEASURED | [BacktestScore 2026](https://www.backtestscore.com/tools/backtrader) |

## Do not do
- Do not let models emit orders or `TradeIntent` objects, or wire a model-to-OMS route.
- Do not promote to live capital automatically; require a written `docs/decisions/` decision.
- Do not use upstream Backtrader, crypto-only bots for equities, or direct LLM-to-order frameworks.
- Do not run live execution on serverless cron, GitHub Actions, Oracle Always Free, or residential ISPs.
- Do not treat pre-cutoff LLM backtests as proof of alpha.
- Do not enable `Withdraw` or `Add Withdrawal Address` on bot keys.
- Do not commit `.env` files or share paper/live keys under one variable.
- Do not auto-retry ambiguous submissions; reconcile `client_order_id` and halt/alert if unresolved.

## Must measure ourselves
- Simulated fills/slippage in Phase 2 separately from actual fills/slippage if Phase 4 live is authorized.
- Incremental net Sharpe and veto precision of triage/frontier models vs. deterministic baseline in Phase 3 shadow.
- End-to-end model latency and intraday signal decay.
- API token spend as a share of gross P&L under live volume.
- Red-team prompt-injection escape rate against our harness before strategy rules consume model outputs.
