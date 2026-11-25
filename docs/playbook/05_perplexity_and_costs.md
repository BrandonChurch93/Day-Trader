# Perplexity and model costs
Source: docs/research/05_perplexity_platform_options.md
Last verified: 2026-11-24

## Bottom line
Run market data, state, risk and paper execution in a deterministic service. Use Perplexity APIs for evidence triage and Computer for briefs, reviews and code maintenance. Models never emit orders or trade intents.

## Rules for the build
- Keep venue streams, order state, freshness, reconciliation and kill switches outside AI. Generate orders only in deterministic strategy code and send every order through the risk engine (our recommendation; research §4) [STATED]
- Limit model outputs to evidence tags, watchlist candidates and veto/pause flags. Fixed deterministic rules may consume them outside shadow mode; in shadow mode, only log them (our recommendation; decisions D1–D3) [STATED]
- Require at least `paper_min_trading_days` trading days AND `paper_min_closed_trades` closed paper trades with models off, then shadow (values in `config/thresholds.yaml`). Never promote to live automatically: require a written owner decision in `docs/decisions/`; require `scale_live_evidence_months` months of live evidence before scaling beyond tiny capital (our recommendation; decisions D2–D3) [STATED]
- Start with a daily Computer brief on Pro and weekly review before buying Max. Alert on missed briefs: repeated skips pause automation until manually re-enabled (our recommendation; research §1) [STATED]
- Use Agent API for new Perplexity model work, Search/Monitor for catalysts, and Context/Decisions or a cheap model for triage. Deduplicate and handle out-of-order deliveries (our recommendation; research §2) [STATED]
- Send only deduplicated, timestamped public evidence to larger models. Pin the model/configuration, cap steps and output, and validate citations and timestamps in code (our recommendation; research §2) [STATED]
- Use an explicit MCP tool allowlist; don't rely on approval defaults or give research tools live trade or transfer scope (our recommendation; research §1) [STATED]
- Treat Coinbase as viewing and IBKR as draft-for-review only; don't rely on native Alpaca paper support until verified (our recommendation; research §1) [STATED]
- Build on a permitted fallback rather than assume Fable 5.2 access. Agent API requires non-zero-data-retention access by request for Fable; keep broker/account data out of research payloads (our recommendation; research §2) [STATED]
- Do not rely on Claude consumer access to buy/sell securities or for securities advice; automated access requires an Anthropic API key or explicit permission. Anthropic's AUP requires qualified review before personalized investment recommendations (including digital assets) are delivered or implemented, and disclosure of AI use (research §3) [MEASURED]
- Plan for Perplexity's January 1, 2027 AUP version, which requires human oversight for consequential automated financial decisions about individuals (research §3) [MEASURED]
- Treat the provision's applicability to personal self-trading as unverified, not permission for unattended live trading (research §3) [UNKNOWN]

## Key numbers
| Item | Value | As of | Tag | Source |
|---|---|---|---|---|
| Computer recurrence | 15 min public minimum; can start minutes late | 2026-11-24 | STATED | [Computer Automations](https://www.perplexity.ai/help-center/en/articles/11521526-perplexity-tasks) |
| Monitor recurrence | 1 min minimum; ≤10% interval jitter, ≤10 min cron jitter | 2026-11-24 | STATED | [Monitor docs](https://docs.perplexity.ai/docs/monitors/overview.md) |
| Search Fast / Monitor Search | $0.001 per successful request / run | 2026-11-24 | MEASURED | [Perplexity API pricing](https://docs.perplexity.ai/docs/getting-started/pricing) |
| Decisions Flash | $0.01 per million input tokens, excluding optional grounding | 2026-11-24 | MEASURED | [Perplexity API pricing](https://docs.perplexity.ai/docs/getting-started/pricing) |
| Agent model rates per million input/output tokens | Haiku 5.5 $0.10/$0.50 at ≤100k input; GPT-6 Luna $0.10/$0.50 at ≤272k; Sonnet 5.5 $2/$10; Opus 5.5 $4/$20; Fable 5.2 $8/$40 | 2026-11-24 | MEASURED | [Agent model pricing](https://docs.perplexity.ai/docs/agent-api/models) |
| Illustrative API cost at published rates | 2,880 checks + 60 deep dives/month: $14.80 tiered vs. $88.74 all-Fable, excluding data, hosting, trading costs and tax | 2026-11-24 | MEASURED | [Perplexity API pricing](https://docs.perplexity.ai/docs/getting-started/pricing) |
| Computer credits | 100 = $1; Pro weekly included use, no standard monthly allocation; Max 10,000/month | 2026-11-24 | MEASURED | [Computer credit policy](https://www.perplexity.ai/help-center/en/articles/13838041-how-credits-work-on-perplexity) |
| Individual Computer subscriptions | Pro $20/month; Max $200/month | 2026-11-24 | MEASURED | [Perplexity pricing comparison](https://www.perplexity.ai/hub/blog/ai-costs) |
| Enterprise Computer subscriptions | Pro $40/seat/month; Max $325/seat/month | 2026-11-24 | MEASURED | [Perplexity Enterprise billing](https://www.perplexity.ai/help-center/en/articles/10352986-enterprise-pricing-and-billing-frequently-asked-questions) |
| Claude Max / Ultra subscriptions | $100 / $200 monthly; Fable up to half weekly usage | 2026-11-24 | MEASURED | [Claude pricing](https://claude.com/pricing) |
| Claude Max / Ultra API credits | Claimable $100 / $200 monthly; expire each cycle; linked Console org required. Not a cash discount; Perplexity retrieval fees not covered | 2026-11-24 | MEASURED | [Claude API credit rules](https://support.claude.com/en/articles/17154008-monthly-api-credits-for-max-ultra-and-team-plans) |

## Do not do
- Do not let models, browsers, sites or notifications submit, size, cancel or retry orders.
- Do not store live keys or authoritative trading state in agents or Project memory.
- Do not infer trade permission from connector capabilities.
- Do not use model output as final investment advice or a live order decision.
- Do not use API prices or run counts to predict Computer credits.
- Do not build on or budget for legacy Sonar Chat Completions; support ended September 27, 2026 ([Sonar migration guide](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/overview)).

## Must measure ourselves
- Measure queue age, freshness, duplicates and alert precision/recall against a deterministic baseline.
- Measure Computer and API spend per useful alert.
- Measure paper and shadow results net of realistic fees, spreads, slippage, latency and partial fills using point-in-time data and locked out-of-sample windows.
- Verify API retention settings and model access; Monitor cannot run in zero-data-retention organizations ([Monitor docs](https://docs.perplexity.ai/docs/monitors/overview.md)).
- Verify Teammate seat eligibility before buying.
