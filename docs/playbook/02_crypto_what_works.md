# Crypto: what to test and what to rule out
Source: docs/research/02_crypto_trading_evidence.md
Last verified: 2026-11-24

## Bottom line
Paper-test low-turnover BTC/ETH spot trend first; observe fully collateralized, regulated fixed-expiry basis. Neither has verified durable small-account profitability.

## Rules for the build
- Start long or flat in cash BTC/USD and ETH/USD on state-eligible U.S. venues; walk frozen multi-hour/daily rules forward against cash and risk-matched passive exposure. (Our recommendation; research: Implications for our build.) [STATED]
- Price both legs at the actual account tier with spread, impact, delays, partial fills and rejects. (Our recommendation; research: U.S. spot pricing: small-account tiers.) [STATED]
- Keep dated carry observation-only until both legs clear financing and collateral costs, margin stress, and an unwind without instant transfers. (Our recommendation; research: Implications for our build.) [STATED]
- Use news, funding, on-chain activity and seasonality as risk or execution alerts, not directional triggers. (Our recommendation; research: What the strategies actually earned in studies.) [STATED]
- Permit models to emit only evidence tags, watchlist candidates and veto/pause flags, never orders or trade intents. Log outputs only in shadow; otherwise fixed rules may consume them. Only deterministic strategy code generates orders, always through the risk engine. (Our recommendation; D1.) [STATED]
- Put sizing, limits, reconciliation and stale-feed halts in deterministic code; provide independent exposure checks and a manual cancel/flatten procedure. Keep credentials out of model context; use scoped trade-only keys, disable transfers where supported, and allowlist IPs. (Our recommendation; research: Risks that change the build.) [STATED]
- Keep idle funds off execution venues where practicable; never rely on exchange stops alone to cap tail losses through thin books. (Our recommendation; research: Risks that change the build.) [STATED]
- Screen pairs by verified book depth, not printed volume; handle venue maintenance and weekend/overnight derivatives margin changes explicitly. (Our recommendation; research: What U.S. retail can access; Risks that change the build.) [STATED]
- Log timestamped fills, fees, USD values, wallet/account lots, funding and transfer IDs; reconcile wallet and broker records. Separate futures/funding from spot for tax. (Our recommendation; research: U.S. tax and records.) [STATED]
- Treat crypto-for-crypto investment swaps as generally taxable recognition events. (Research: U.S. tax and records.) [MEASURED]
- Require at least `paper_min_trading_days` trading days and `paper_min_closed_trades` closed paper trades with models off, then shadow before tiny live capital. Require `scale_live_evidence_months` months of live evidence to scale beyond tiny capital. Values: `config/thresholds.yaml`. (Our recommendation; D3.) [STATED]
- Never promote automatically. Require a written owner decision in `docs/decisions/` before going live or scaling. (Our recommendation; D2.) [STATED]

## Key numbers

| Item | Value | As of | Tag | Source |
|---|---|---|---|---|
| Historical BTC intraday timing | ~10 bps unlevered break-even cost for the best of three variants (others 3 and 7). The paper does not say one-way or round trip, so do not compare it with the fee rows below. The authors call it unprofitable at the venue's 25 bps fee | Data through Dec 2020 | MEASURED | [University of Reading manuscript](https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf) |
| Binance.US, most spot pairs | 4 bps taker round trip, fee only | Nov 24, 2026 | MEASURED | [Binance.US fees](https://www.binance.us/fees) |
| Alpaca spot entry | 50 bps taker round trip, fee only | Nov 24, 2026 | MEASURED | [Alpaca fees](https://docs.alpaca.markets/us/docs/crypto-fees) |
| Kraken Pro spot entry | 160 bps taker round trip, fee only | Nov 24, 2026 | MEASURED | [Kraken Pro fees](https://www.kraken.com/pro/fees) |
| Coinbase Advanced spot entry | 180 bps taker round trip, fee only (0.50% maker, 0.90% taker) | Sep 16, 2026 | MEASURED | [Coinbase announcement](https://www.coinbase.com/blog/were-lowering-fees-for-many-active-traders-on-coinbase-advanced) |
| Robinhood Exchange Routing spot entry | 190 bps taker round trip, fee only | Nov 24, 2026 | MEASURED | [Robinhood fee schedule](https://cdn.robinhood.com/assets/robinhood/legal/rhc-fee-schedule.pdf) |
| Gemini ActiveTrader spot entry | 240 bps taker round trip, fee only | Sep 1, 2026 | MEASURED | [Gemini fee schedule](https://www.gemini.com/fees/activetrader-fee-schedule) |
| IBKR spot commission | 0.12%–0.18% per order; $1.75 minimum capped at 1% | Nov 24, 2026 | MEASURED | [IBKR commissions](https://portal.interactivebrokers.com/en/pricing/commissions-cryptocurrencies.php) |
| Kraken U.S. BTC perp sizing | 0.0001 BTC minimum, from a Kraken announcement and not the contract specification page. Not offered in Maine or New York | Nov 23, 2026 | MEASURED | [Kraken fractional perps](https://blog.kraken.com/product/kraken-derivatives/us-fractional-crypto-perps) |
| Custodial broker 1099-DA, 2025 | Gross proceeds from reportable sales; basis optional | Tax year 2025 | MEASURED | [IRS 2025 Form 1099-DA instructions](https://www.irs.gov/pub/irs-prior/i1099da--2025.pdf) |
| Custodial broker 1099-DA, 2026 onward | Gross proceeds on reportable sales; mandatory basis only for covered assets acquired after 2025 and held in the same custodial account until sale | Apr 30, 2026 | MEASURED | [IRS 2026 Form 1099-DA instructions](https://www.irs.gov/instructions/i1099da) |

## Do not do
- Use Agent API for new Perplexity work, not Sonar Chat Completions ([legacy support ended September 27, 2026](https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/overview)). (Our recommendation; D4.) [STATED]
- Do not deploy retail HFT, market making, memecoin sniping or DEX arbitrage in the first build. (Our recommendation.) [STATED]
- Do not use Hyperliquid’s hosted interface as a U.S. user; its [terms exclude U.S. users](https://app.hyperliquid.xyz/terms). (Research: What U.S. retail can access.) [MEASURED]
- Do not use VPNs or alternate frontends to bypass U.S. restrictions. (Our recommendation; research: What U.S. retail can access.) [STATED]
- Do not use leverage for initial directional tests or treat stablecoins as USD. (Our recommendation.) [STATED]
- Do not treat a backtest, bot template or touched limit as proof of executable profits. (Our recommendation.) [STATED]

## Must measure ourselves
- Account-tier fees and venue, product and API entitlements. [UNKNOWN]
- Decision-to-fill costs and missed-fill rates by venue, size and time. [UNKNOWN]
- Net walk-forward and shadow results; live retail capture of news and on-chain signals. [UNKNOWN]
- Contract-specific margin, funding, unwind and transfer constraints on both carry legs. [UNKNOWN]
