# 0001 - Starting decisions from the research round

Date: 2026-11-24
Status: proposed by the research team; items marked OWNER need the owner's confirmation.

## Decided by the evidence (default until overturned)

| # | Decision | Why | Where |
|---|---|---|---|
| 1 | The product is a deterministic trading service; AI is a research and review layer beside it | Live and forward tests of LLM traders mostly lost money or showed no alpha; LLM strengths are text, code and review | playbook 03, research 03 |
| 2 | Start with multi-day trend following plus volatility sizing on liquid ETFs and BTC/ETH spot, not pure intraday | Best-evidenced families; intraday edges are small, cost-fragile and decayed after publication | playbook 01, 02 |
| 3 | Tiered models: no-model scanners, cheap-model triage, rare top-model escalation | Cascade literature supports large savings; list-price arithmetic shows roughly 6x cheaper than top model on every scan at 15-minute cadence | playbook 05 |
| 4 | Always-on service runs on our own small server, not inside Perplexity Computer | Computer automations have a 15-minute public minimum and no socket or latency guarantee; it is a research and build tool | playbook 05, 06 |
| 5 | One monorepo: trading service plus agent harness and evals plus docs | Shared data models, one audit trail | playbook 06 |
| 6 | Paper trading before any live capital, with pre-registered pass criteria | Base rates; paper fills are optimistic | playbook 06 |
| 7 | Two-layer docs: playbook (default) and research (audit trail) | Keeps agent context small without losing sources | README |
| 8 | Models never emit orders or trade intents; they emit evidence tags, watchlist candidates and pause or veto flags that fixed rules may consume | LLM trade-picking showed no alpha; provider policies require human review of personalized buy/sell recommendations | playbook 03, 05, 06 |
| 9 | Paper gate before tiny live capital: 60 trading days and 100 closed paper trades with models off, then shadow. Scaling needs 6 to 12 months of live evidence | Reconciles the three reports' differing durations; short tests are underpowered | playbook 06 |
| 10 | Promotion to live is never automatic; it needs a written owner decision here | Legal responsibility sits with the account owner | AGENTS.md |

The playbook files refer to four cross-cutting decisions by short label: D1 is row 8, D2 is row 10, D3 is row 9, and D4 is the choice of the Perplexity Agent API for new API work, since legacy Sonar Chat Completions support ended September 27, 2026.

The audits that tested each playbook file against its research report are in `audit_01` to `audit_06` in this folder. Every blocker and fix they raised was applied; where an author narrowed an audit item, the reason is in the audit trail of this round.

## OWNER decisions still open

- Starting capital for the eventual live phase and the most you are willing to lose in total and per day.
- Brokers: Alpaca (simplest API, paper built in) versus Interactive Brokers (ring-fenced AI partition) for stocks; Kraken, Alpaca or Binance.US for crypto.
- Whether crypto is spot only (recommended) or may later include regulated futures.
- Hosting: small rented server (about 5 to 6 dollars a month) or a machine you own.
- Which Perplexity plan and API budget to run research and reviews on.
- Model policy: several providers' terms restrict using their models for personalized trading decisions. Keeping models on research and fixed-rule review, not buy/sell calls, is the conservative reading. Confirm you are comfortable with that scope.
