# 0001 - Starting proposals from the research round

Date: 2026-11-24
Status: proposed by the research team. Nothing in this file is an owner decision until the owner confirms it. Confirmations are recorded with their date in a later decision file.

Note added 2026-11-25. Row 7 below says the owner agreed in the thread on 2026-11-24. It is the one row recorded here as his. His words are not quoted in this file, so read it as STATED by research until a decision file quotes them. Rows 1 and 2 are now questions 14 and 15 in `docs/decisions/morning_list_2026-11-25.md`.

## Proposed by the research team

Rows 1 and 2 change what the owner asked for. Each is put to him on its own before it counts as decided.

| # | Proposal | Why | Where | Status |
|---|---|---|---|---|
| 1 | The product is a deterministic trading service; AI is a research and review layer beside it | Live and forward tests of LLM traders mostly lost money or showed no alpha; LLM strengths are text, code and review | playbook 03, research 03 | Scope call. Not yet put to the owner |
| 2 | Start with multi-day trend following plus volatility sizing on liquid ETFs and BTC/ETH spot, not pure intraday | Best-evidenced families; intraday edges are small, cost-fragile and decayed after publication | playbook 01, 02 | Scope call. Not yet put to the owner |
| 3 | Tiered models: no-model scanners, cheap-model triage, rare top-model escalation | Cascade literature supports large savings; the list-price working is in playbook 05 | playbook 05 | Proposed. Matches what the owner asked for on 2026-11-24 |
| 4 | Always-on service runs on our own small server, not inside Perplexity Computer | Computer automations have a public minimum interval and no socket or latency guarantee; it is a research and build tool | playbook 05, 06 | Proposed |
| 5 | One monorepo: trading service plus agent harness and evals plus docs | Shared data models, one audit trail | playbook 06 | Proposed |
| 6 | Paper trading before any live capital, with pre-registered pass criteria | Base rates; paper fills are optimistic | playbook 06 | Proposed |
| 7 | Two-layer docs: playbook (default) and research (audit trail) | Keeps agent context small without losing sources | README | Owner agreed in the thread, 2026-11-24 |
| 8 | Models never emit orders or trade intents; they emit evidence tags, watchlist candidates and pause or veto flags that fixed rules may consume | LLM trade-picking showed no alpha; provider policies require human review of personalized buy/sell recommendations | playbook 03, 05, 06 | Follows from row 1. Decided with it |
| 9 | Paper gate before tiny live capital: `paper_min_trading_days` trading days and `paper_min_closed_trades` closed paper trades with models off, then shadow. Scaling needs `scale_live_evidence_months` months of live evidence | Reconciles the three reports' differing durations; short tests are underpowered | playbook 06, `config/thresholds.yaml` | Proposed |
| 10 | Promotion to live is never automatic; it needs a written owner decision here | Legal responsibility sits with the account owner | AGENTS.md | Proposed. Already a hard rule in AGENTS.md |

The playbook files refer to four cross-cutting proposals by short label: D1 is row 8, D2 is row 10, D3 is row 9, and D4 is the choice of the Perplexity Agent API for new API work, since legacy Sonar Chat Completions support ended September 27, 2026.

The audits that tested each playbook file against its research report are in `audit_01` to `audit_06` in this folder. A fresh-agent check of the load-bearing figures against their sources was started on 2026-11-24. Its results are recorded in decision 0003.

## Open owner decisions

Each is put to the owner one at a time. Values named by key live in `config/thresholds.yaml`, where `recommended` is a suggestion and never a value to use.

| # | Decision | Recommended pick | Reason | What it costs him |
|---|---|---|---|---|
| A | Starting live capital and loss limits | The `recommended` values of `live_starting_capital_usd`, `live_max_position_usd`, `live_max_daily_loss_usd` and `live_max_total_loss_usd` | Small enough to lose in full, large enough that fees do not swamp the result | Results on an account this small say little about a larger one |
| B | Stock broker | Alpaca, individual account | The only stock broker checked with a free practice account on the same connection as live, keys that run unattended, no account minimum, and the old $25,000 day trading rule already switched off (research 09) | Free data covers one exchange. Full data is a paid monthly plan. Personal keys cannot be locked to one address or set to expire. Interactive Brokers is the alternative to revisit |
| C | Crypto venue | Alpaca for all practice trading. Live venue not chosen: the front-runner on cost is Binance.US, with conditions; the fallback is spot bitcoin and ether funds in the Alpaca account (research 09) | Fees separate the venues, not order books. Our replay shows the trend rule holding up at low fees and failing at Kraken and Coinbase entry fees (research 12). Corrected 2026-11-25: after two code audits and a rerun, bitcoin trend rules clear the pass marks on both price histories at Binance.US cost only, and narrowly (research 16, which replaces research 12). Research recommends these are not credited as passes (question 18b in `docs/decisions/morning_list_2026-11-25.md`) | Binance.US has no practice environment and no numeric reserve report that was found. The fund route trades only in stock market hours |
| D | Crypto scope | Spot only | Leverage and funding costs are where most retail crypto accounts are lost | No shorting and no leverage in crypto |
| E | Hosting | A small rented server | Always on, fixed address, not tied to home power or internet | A small monthly fee, and one more account to hold |
| F | API-billed model spend cap | The `recommended` value of `api_model_spend_cap_usd_month` | Above the list-price working in playbook 05, low enough to catch a runaway loop | A real escalation may be skipped late in a month when the cap is reached |
| G | Model policy | Decided with row 1 | Several providers restrict using their models for personalized trading decisions | See row 1 |
