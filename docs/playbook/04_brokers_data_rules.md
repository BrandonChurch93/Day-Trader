# Brokers, Data, Compliance and Tax Rules

Source: docs/research/04_brokers_data_compliance.md
Last verified: 2026-11-24

## Bottom line
Run deterministic strategy code on Alpaca paper with free IEX data, then a ring-fenced live cash account after a written owner decision. The $25k PDT rule was replaced on 2026-06-04; settlement, fees, and short-term tax are the real constraints. You are legally responsible for every order, so only deterministic code places orders, through a risk engine.

## Rules for the build
- Generate orders only in deterministic strategy code, always through the risk engine; models emit only evidence tags, watchlist candidates, and veto/pause flags, logged only in shadow mode (our recommendation, D1). [STATED] (research §5, §7)
- Read broker account flags and buying power at runtime; brokers may phase in the new rule until 2027-10-20. [MEASURED] (research Headline)
- Default to cash accounts; track T+1 settled cash to avoid good-faith violations. [MEASURED] (research §4)
- Check shortable status and Reg SHO Rule 201 before shorting; treat LULD halts as unfillable and assume stops gap. [MEASURED] (research §4)
- Enforce in code: max daily loss, orders/minute, notional per symbol, cancel-to-fill cap, and cross-account self-trade prevention (our recommendation). [STATED] (research §5, §7)
- Use trade-only keys with IP allowlists, held only by the execution service; keep secrets out of prompts, logs, and model context (our recommendation). [STATED] (research §7)
- Run a dead-man's switch: Kraken CancelAllOrdersAfter natively, elsewhere a heartbeat watchdog that cancels all orders. [MEASURED] (research §7)
- Fund live trading only via a dedicated account or sub-account (single-portfolio Coinbase key for crypto) holding money you can lose entirely (our recommendation). [STATED] (research §7, Recommended stacks)
- Add modeled fees and slippage to paper fills; treat IEX as plumbing-only and buy SIP ($99/mo) before trading spread, volume, or breakout signals; check history for survivorship bias (our recommendation). [STATED] (research §3, Recommended stacks)
- Paper gate: at least 60 trading days AND 100 closed trades with models off, then shadow; live promotion needs a written owner decision in docs/decisions/; scaling past tiny capital needs 6-12 months live evidence (our recommendation, D2/D3). [STATED] (Implications)
- Log every fill (time, venue, lot, fees): wash sales span accounts including IRAs, and 1099-DA basis is required only for covered digital assets, so our ledger is the Form 8949 record. [MEASURED] (research §6)
- Check each vendor's license before sending feeds to hosted LLMs. [UNKNOWN] (research §3)

## Key numbers
| Item | Value | As of | Tag | Source |
|---|---|---|---|---|
| PDT replaced by intraday margin rule | Effective 2026-06-04; broker phase-in until 2027-10-20 | 2026-04-20 | MEASURED | [FINRA RN 26-10](https://www.finra.org/sites/default/files/2026-04/Regulatory-Notice-26-10.pdf) |
| Alpaca free data | IEX only, 30 websocket symbols, 200 historical calls/min, latest 15 min of SIP history restricted; SIP $99/mo | 2026-11 | MEASURED | [Alpaca market data](https://docs.alpaca.markets/us/docs/about-market-data-api) |
| IEX share of US equity volume | About 4% overall | Q2 2026 | MEASURED | [IEX](https://www.iex.io/article/iex-expands-market-data-distribution-through-new-vendor-partnership-program) |
| Alpaca Trading API rate limit | 200 requests/min per key | 2026-11 | MEASURED | [Alpaca docs](https://github.com/alpacahq/alpaca-docs/blob/master/content/api-references/crypto-api/_index.md) |
| Alpaca crypto fees, entry tier | 0.15% maker / 0.25% taker | 2026-11 | MEASURED | [Alpaca crypto fees](https://docs.alpaca.markets/us/docs/crypto-fees) |
| Kraken spot fees, Tier 1 | 0.40% maker / 0.80% taker | 2026-10-30 | MEASURED | [Kraken fee tiers](https://support.kraken.com/articles/cross-platform-fee-tier-changes) |
| Coinbase fees, entry tier | 0.60% maker / 1.20% taker | 2026-11 | STATED | [APIs.io Coinbase plans](https://apis.io/plans/coinbase/coinbase-plans-pricing/) |
| IBKR Autonomous AI limits | Cash only, stocks/equity options only, no shorts/fractional, day orders, 10 human-approved trades over 2 weeks | 2026-11 | MEASURED | [IBKR AI integrations](https://portal.interactivebrokers.com/en/trading/ai-integrations.php) |
| Federal short-term gains tax | Ordinary rates; single: 24% over $105,700, 32% over $201,775 | 2026 | MEASURED | [IRS 2026 adjustments](https://www.irs.gov/newsroom/irs-releases-tax-inflation-adjustments-for-tax-year-2026-including-amendments-from-the-one-big-beautiful-bill) |
| Idaho income tax | Flat 5.3% | 2025-01-01 | MEASURED | [Idaho Tax Commission](https://tax.idaho.gov/wp-content/uploads/forms/EIN00046/EIN00046_03-02-2026.pdf) |
| Section 475(f) election for 2027 | Due by 2027-04-15 (unextended due date of 2026 return) | 2026-11 | MEASURED | [IRS Topic 429](https://www.irs.gov/taxtopics/tc429) |

## Do not do
- Do not place orders meant to be cancelled before fill or sized to move price (spoofing/layering).
- Do not trade or signal for others without RIA/CTA registration analysis.
- Do not enable withdraw, transfer, or add-withdrawal-address on any key, or link browser agents to a broker login (unrestricted control).
- Do not execute via broker agent products (Robinhood MCP, IBKR Autonomous, trade-capable Alpaca MCP) (D1); Robinhood MCP approvals default off, and revoking IBKR AI access does not cancel open orders.
- Do not treat crypto as SIPC-protected.
- Do not rely on crypto loss harvesting; pending H.R. 10357 would apply wash sales to sales after 2026-09-14 [STATED].
- Do not day trade crypto on Coinbase, Gemini, tastytrade, or Webull entry tiers (about 2%+ round trip).
- Do not promote to live automatically (D2).

## Must measure ourselves
- API uptime, latency, and reject rates.
- Paper-versus-live slippage at our sizes.
- Tradier/Webull/E*TRADE rate limits; Kraken spot sandbox.
- With a CPA before 2027-04-15: trader tax status for bot trading, 475(f) election, and crypto coverage.
- Whether vendor licenses permit hosted-LLM processing.
