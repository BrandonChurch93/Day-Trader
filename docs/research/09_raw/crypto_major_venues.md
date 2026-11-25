> Raw researcher report, kept as evidence. Some figures here were corrected after a fresh check. The corrected version is `docs/research/09_brokers_and_venues.md`, which wins where the two differ. Known corrections: the Coinbase Advanced entry fee is 0.50% maker and 0.90% taker, not 0.40% and 0.60%; an Alpaca duplicate order id returns HTTP 422, not 409.

# Major US spot crypto venues with an API, for an Idaho resident

Researcher: crypto_major_venue_researcher. Pages opened on 2026-11-24. Scope: Coinbase (Advanced Trade API), Kraken (Kraken Pro spot API), Gemini (ActiveTrader / exchange API), Alpaca Crypto, Robinhood Crypto Trading API.

Tags: MEASURED = read on the firm's own page or live public API today. STATED = third party or marketing claim not confirmed on a primary page. UNKNOWN = not found.

## Unfinished or not verified (read first)

- Coinbase Advanced exact fee table: UNKNOWN on a public primary page. Coinbase's Advanced fee help page says the rates are only shown after sign-in. The public `coinbase.com/advanced-fees` page did not load for me. I used the public Coinbase Exchange fee schedule (same company, same order books) as the best primary proxy and say so in every place it is used. Third-party sites disagree on which number is maker and which is taker (details in the Coinbase section).
- Coinbase Advanced REST rate limits for retail keys: UNKNOWN (the Advanced rate-limit page did not load; only Coinbase Exchange and WebSocket limits were readable).
- Robinhood: per-coin minimum order size, key scopes, IP allowlist and key expiry are UNKNOWN (the docs do not state them; the help article on the API did not load).
- Coinbase and Gemini: no Merkle-tree proof-of-reserves report found (UNKNOWN). Both make 1:1 custody statements.
- Kraken Idaho money-transmitter licence: UNKNOWN (the US licences page did not load). Kraken's support page lists only Maine and New York as excluded states.
- Gemini Idaho licence entry: UNKNOWN (licence page shows only NMLS IDs). Gemini says it serves all 50 states.
- Sign-up approval times: no firm-stated times found for any of the five (UNKNOWN).
- Outage history: only the 20 Oct 2025 AWS outage is well documented (Coinbase retrospective). I did not do a full outage review for Kraken, Gemini or Alpaca.

## Top findings in one place

1. Cheapest at the lowest tier by a wide margin: Alpaca Crypto, 15 bps maker / 25 bps taker (MEASURED). Round trip 30 bps maker-maker, 50 bps taker-taker. But Alpaca has about 20+ coins and a $200k per-order cap.
2. Most expensive entry tier: Gemini, 60 bps maker / 120 bps taker (MEASURED, effective 1 Sep 2026). Round trip 240 bps taker-taker.
3. Kraken raised nothing but its Tier 1 is 40/80 bps; Tier 2 starts at only $2.5K of 30-day volume (30/60), and Tier 3 can be reached by holding $20K on the platform (22/38) (MEASURED, change effective 9 Jul 2026).
4. Robinhood API v2 orders are currently charged the standard (taker) fee even for resting limit orders "until reduced/standard is fully rolled out" (MEASURED). At the lowest tier that is 95 bps per side.
5. Every venue except Robinhood documents a way to make a key that can trade but cannot withdraw. Coinbase, Kraken and Gemini document IP allowlists. Gemini and Robinhood terms explicitly cover AI agents placing orders.
6. Sandbox quality differs a lot: Gemini has a full test exchange with simulated order flow; Alpaca paper trading covers crypto; Coinbase's sandbox is static mocked responses only; Kraken spot test environment is "on request via Account Manager"; Robinhood has none documented.

---

## 1. Coinbase (Coinbase, Inc.), Advanced Trade API

### Eligibility
| Item | Finding | Tag | Source |
|---|---|---|---|
| Idaho | Coinbase lists "Idaho Money Transmitters License, MTL-169". Coinbase, Inc. NMLS ID 1163082. | MEASURED | https://www.coinbase.com/legal/licenses |
| Advanced Trading availability | "Coinbase does not offer Advanced Trading to customers in all jurisdictions." | MEASURED | https://www.coinbase.com/legal/user_agreement/united_states |
| Minimum deposit / minimum to use API | Not stated. Order minimum on BTC-USD and ETH-USD is $1 quote (see below). | UNKNOWN / MEASURED | public API (below) |
| Entity/LLC accounts | Not researched for this file. | UNKNOWN | |

### API
| Item | Finding | Tag | Source |
|---|---|---|---|
| Official API | Advanced Trade REST API (`https://api.coinbase.com/api/v3/brokerage`) plus WebSocket. Page states there is an "OpenAPI spec". | MEASURED | https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/rest-api |
| Python SDK | Official `coinbase-advanced-py` (REST and WebSocket clients). | MEASURED | https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/sdk , https://github.com/coinbase/coinbase-advanced-py/ |
| Order types | Market, `limit_limit_gtc`, `limit_limit_gtd`, `sor_limit_ioc`, stop-limit GTC/GTD, bracket (`trigger_bracket_gtc/gtd`), attached TP/SL. | MEASURED | https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/guides/orders |
| Idempotency | `client_order_id` field on create order. | MEASURED | same page; FAQ https://docs.cdp.coinbase.com/coinbase-business/advanced-trade-apis/faq |
| Min order size BTC-USD | `base_min_size` 0.00000001 BTC, `quote_min_size` $1, `base_increment` 0.00000001. | MEASURED (live public API today) | https://api.coinbase.com/api/v3/brokerage/market/products/BTC-USD |
| Min order size ETH-USD | `base_min_size` 0.00000001 ETH, `quote_min_size` $1. | MEASURED (live public API today) | https://api.coinbase.com/api/v3/brokerage/market/products/ETH-USD |
| Rate limits | Advanced Trade WebSocket: one docs page says connections "750 per second per IP" and unauthenticated messages "8 per second per IP"; another Coinbase docs page says both are "8 per second per IP". The two pages disagree. Advanced REST private limits: UNKNOWN (page did not load). Coinbase Exchange (different product) REST private: 15 req/s per profile, bursts to 30. | MEASURED (conflict) / UNKNOWN | https://docs.cdp.coinbase.com/coinbase-business/advanced-trade-apis/websocket/websocket-rate-limits , https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-rate-limits , https://docs.cdp.coinbase.com/exchange/introduction/rate-limits-overview |
| Key permissions | "A CDP API key needs `view`, `trade`, or `transfer`." `trade` covers orders and portfolio create/edit/delete. `transfer` covers `POST /portfolios/move_funds` and futures sweeps. | MEASURED | https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/rest-scopes |
| Trade-only, no withdraw | Coinbase's own agent setup guide: "Enable Trade and Transfer (View is enabled by default)", which means Transfer is a separate box you can leave off. The scopes page does not mention external withdrawals. A View+Trade key with no Transfer is the documented least-privilege option. | MEASURED (inference that no-Transfer blocks withdrawals is mine, not stated) | https://docs.cdp.coinbase.com/coinbase-for-agents/skill |
| IP allowlist | "Restrict the use of your Secret API key to specific IPs (IPv4 and IPv6 supported)." | MEASURED | https://docs.cdp.coinbase.com/get-started/authentication/security-best-practices |
| Token expiry | "JWTs expire after 2 minutes". Secret key expiry: not stated; rotation is by creating a new key and deleting the old. | MEASURED | same page |
| Portfolios to isolate a bot | "Portfolios let you create new trading environments and segregate trading strategies". "Transfers between portfolios are instantaneous and free." Max 100 portfolios. "Each API key is scoped to specific portfolio and, unless otherwise noted, can only view and create data that belongs to its own portfolio." Portfolios can be deleted by API only. | MEASURED | https://docs.cdp.coinbase.com/coinbase-business/advanced-trade-apis/guides/portfolios |
| Sandbox | Static only. "All responses are static and pre-defined." "Only Accounts and Orders related endpoints are currently available in the sandbox. All responses are mocked but have the same format as production." No auth needed. URL `https://api-sandbox.coinbase.com/api/v3/brokerage/`. Useful for request-format tests only, not for strategy testing. | MEASURED | https://docs.cdp.coinbase.com/coinbase-business/advanced-trade-apis/sandbox |
| AI agents | Coinbase runs a remote MCP server; its docs list "Perplexity Computer, Claude, Claude Code, and Codex CLI" among allowlisted harnesses, and suggest a dedicated portfolio "fund it with only what they're willing to risk". | MEASURED | https://docs.cdp.coinbase.com/coinbase-for-agents/skill |

### Terms on automation
- User Agreement: "By accessing Advanced Trading or the Coinbase API for Advanced Trading, you accept and agree to be bound by the Trading Rules." It also says you may not give access to your Trading Account to anyone "that is not your employee or agent." No ban on automation found. MEASURED. https://www.coinbase.com/legal/user_agreement/united_states (page date 2025-11-18 per search index)
- Trading Rules, self-trade prevention: "Traders are not able to place an Order which would result in self-execution". No order-to-fill ratio rule found for retail. MEASURED. https://www.coinbase.com/legal/trading_rules

### Costs
Coinbase Advanced help page: "To see your current rates and qualification criteria, sign in to your Coinbase.com account and open the Coinbase Advanced fees page." Tier is "based on the trading volume or USDC balance criteria most favorable to you." No spread on Advanced: "No spread is included for Coinbase Advanced because you're interacting directly with the order book." MEASURED. https://help.coinbase.com/en/coinbase/trading-and-funding/advanced-trade/advanced-trade-fees , https://help.coinbase.com/en/coinbase/trading-and-funding/pricing-and-fees/fees

Public primary proxy: Coinbase Exchange fee schedule (applies to "clients outside of our Liquidity Program"). The Advanced Trade API FAQ says Advanced has "the same volume-based fee structure" as Coinbase Pro. MEASURED. https://help.coinbase.com/en/exchange/trading-and-funding/exchange-fees , https://docs.cdp.coinbase.com/coinbase-business/advanced-trade-apis/faq

| 30-day volume | Maker | Taker |
|---|---|---|
| $0-$10K | 40 bps | 60 bps |
| $10K-$50K | 25 bps | 40 bps |
| $50K-$100K | 15 bps | 25 bps |
| $100K-$1M | 10 bps | 20 bps |
| $1M-$15M | 8 bps | 18 bps |

Third-party conflict (STATED): skrumble.com and comparecex.com give 0.40% maker / 0.60% taker at entry (matches the Exchange table). cryptoryancy.com gives 0.60% maker / 0.40% taker and different breakpoints; I treat that as likely a transposition but cannot confirm on a signed-out primary page. https://skrumble.com/learn/coinbase-fees/ , https://www.cryptoryancy.com/coinbase-advanced-trading-fees/

Coinbase One effect on Advanced (MEASURED): "Coinbase Advanced is excluded from the zero trading fees benefits", but there is a "25% fee rebate on fees for spot trades that gets credited back to your account in USDC." Tiers: Basic $4.99/mo, no Advanced rebate. Preferred $29.99/mo, 25% rebate up to $100/month. Premium $299.99/mo, 25% unlimited. "There may be a cap on the aggregate amount of USDC rebated each month." https://help.coinbase.com/en/coinbase/other-topics/coinbase-one/account , https://help.coinbase.com/en/coinbase/other-topics/coinbase-one/benefit-disclosures

USDC to USD conversion: 0.0% up to $2M net (effective 1 Jun 2026). MEASURED. Exchange fees page above.

### Execution and outages
- 20 Oct 2025 AWS outage: "Coinbase trading services experienced periods of unavailability." "Transfers, withdrawals, and deposits were delayed or failed." "All Coinbase services were restored at 6:45pm ET". MEASURED. https://www.coinbase.com/blog/Retrospective-AWS-Outage-Impact-and-Coinbase-Next-Steps

### Safety
- Custody: "Coinbase always holds customer assets 1:1." "We do not lend or take any action with your assets, unless you specifically instruct us to." MEASURED (firm statement). https://help.coinbase.com/en/coinbase/other-topics/legal-policies/what-does-coinbase-do-with-my-digital-assets
- US custodian Coinbase Custody Trust Company is "a qualified custodian regulated by the New York Department of Financial Services". MEASURED. https://www.coinbase.com/blog/how-coinbase-protects-customer-assets
- Proof of reserves (Merkle): UNKNOWN, none found.
- SEC civil action dismissed 27 Feb 2025, "not on any assessment of the merits". MEASURED. https://www.sec.gov/newsroom/press-releases/2025-47
- May 2025 data breach: insiders at overseas support copied data for "less than 1% of Coinbase monthly transacting users", including names, addresses, government ID images, masked SSN. Not taken: "Login credentials or 2FA codes", "Private keys". MEASURED. https://www.coinbase.com/blog/protecting-our-customers-standing-up-to-extortionists

### Sign-up
Steps, documents and approval time for Coinbase were not confirmed on a primary page today: UNKNOWN. API access: create a CDP secret key at portal.cdp.coinbase.com, choose the portfolio under Accounts, choose permissions and IP allowlist (MEASURED, https://docs.cdp.coinbase.com/coinbase-for-agents/skill).

---

## 2. Kraken (Payward Interactive, Inc.), Kraken Pro spot API

### Eligibility
| Item | Finding | Tag | Source |
|---|---|---|---|
| Idaho | Kraken "does not offer services to residents of: Maine, New York". Idaho is not excluded. Fiat transfer limits apply in IN, LA, MA, UT (not ID). | MEASURED | https://support.kraken.com/articles/where-is-kraken-licensed-or-regulated?country=us |
| US registrations | FinCEN MSB "Payward Interactive, Inc., MSB Registration No. 31000270997766"; Kraken Financial is a Wyoming SPDI; Kraken Securities LLC is SEC/FINRA/SIPC. State MTL list: UNKNOWN (page did not load). | MEASURED / UNKNOWN | same page |
| US contracting entity | Payward Interactive, Inc., Cheyenne, WY. | MEASURED | https://www.kraken.com/legal/global-terms |
| Verification | 18+, SSN or Tax ID, valid ID, proof of address (may be required), face photo in some cases. | MEASURED | https://support.kraken.com/articles/201352206-verification-level-requirements |
| Minimum deposit | Not stated. | UNKNOWN | |

### API
| Item | Finding | Tag | Source |
|---|---|---|---|
| Official API | Spot REST `https://api.kraken.com`, WebSocket v2 `wss://ws.kraken.com/v2`, FIX for spot order entry and market data. 700+ spot pairs. | MEASURED | https://docs.kraken.com/exchange/guides/overview |
| Order types | Limit, market, stop, take-profit, trailing stop, IOC, post-only. | MEASURED | same |
| Python SDK | Not mentioned on overview. Kraken ships `kraken-cli` with "AI agent workflows" and a built-in paper engine. | MEASURED | https://docs.kraken.com/home/cli |
| Sandbox | Spot: "UAT available on request via Account Manager". Derivatives demo is self-service. The CLI has local paper trading "against live prices with no authentication required". | MEASURED | https://docs.kraken.com/exchange/guides/overview , https://docs.kraken.com/home/cli |
| Rate limits | REST call counter: Starter max 15, decay 0.33/s; Intermediate 20, 0.5/s; Pro 20, 1/s. Orders use a separate per-pair engine counter shared across REST, WebSocket, FIX. | MEASURED | https://docs.kraken.com/exchange/guides/rest/ratelimits , https://docs.kraken.com/exchange/guides/general/ratelimits |
| Key permissions | Separate boxes for Query Funds, Deposit Funds, Withdraw Funds, Create & Modify Orders, Cancel/Close Orders, etc. Kraken: a trading key "would almost certainly not require Withdraw Funds permission." | MEASURED | https://docs.kraken.com/exchange/guides/rest/api-keys , https://support.kraken.com/articles/how-to-create-an-api-key-on-kraken-pro?mode=consumerapp |
| IP allowlist | "IP Address Restriction is a security feature that restricts API key use to specific client side IP addresses." | MEASURED | same support page |
| Key expiry | "Key Expiration can be used to create an API key that only works for a specific amount of time, such as a key that is only valid for 1 week." Optional. | MEASURED | same |
| Min order BTC/USD | API: `ordermin` 0.00006 BTC, `costmin` 0.5 USD. Support table: Bitcoin trade minimum 0.00006. Same support page also says "If you are trading BTC, the volume of the order must be 0.0001 BTC or larger." The two lines on one page disagree; the live API says 0.00006. | MEASURED (conflict) | https://api.kraken.com/0/public/AssetPairs?pair=XBTUSD,ETHUSD , https://support.kraken.com/articles/360001389303-overview-of-cryptocurrency-minimums |
| Min order ETH/USD | API: `ordermin` 0.002 ETH, `costmin` 0.5 USD. | MEASURED | API above |
| Idempotency | Not checked today. | UNKNOWN | |

### Terms on automation
- Kraken support: "Clients are welcome to use trading bots to trade our markets." MEASURED. https://support.kraken.com/articles/360001373983-does-kraken-allow-trading-bots-
- Terms Section 9 (Restrictions) says you will not use "bots ... or any other forms of automation to engage in any activity on Our Content" and will not "develop any third-party applications that interact with Our Content without our prior written consent". This reads as aimed at website content, and conflicts on its face with the support article. Section 4 confirms API orders "are executed by us on an agency basis". MEASURED (conflict noted). https://www.kraken.com/legal/global-terms
- No AI-agent clause found.

### Costs (MEASURED, https://www.kraken.com/pro/fees ; tier method effective 9 Jul 2026 per https://blog.kraken.com/product/pro/new-kraken-pro-fee-tiers)
Tier is best of 30-day spot volume or assets on platform (AOP). For US clients futures volume does not count. "AOP is assessed point-in-time ... your AOP-qualified tier adjusts immediately, in either direction." Forex and stablecoin pairs do not count toward volume.

| Tier | 30-day spot volume | or AOP | Maker | Taker |
|---|---|---|---|---|
| 1 | $0+ | n/a | 40 bps | 80 bps |
| 2 | $2.5K+ | n/a | 30 bps | 60 bps |
| 3 | $10K+ | $20K+ | 22 bps | 38 bps |
| 4 | $25K+ | $50K+ | 20 bps | 35 bps |
| 5 | $50K+ | $100K+ | 15 bps | 30 bps |

Stablecoin/FX pairs Tier 1: 20/20 bps. The fee page also says selected spot pairs get "−0.02% off" across tiers. No last-updated date on the fee page.

### Safety
- Proof of reserves: snapshot 30 Sep 2026, BTC reserve ratio 103.2%, ETH 100.7%, done by "an independent 3rd party accountant" with Merkle-tree client verification. MEASURED. https://www.kraken.com/proof-of-reserves
- SEC action dismissed with prejudice, joint stipulation 27 Mar 2025. MEASURED. https://www.sec.gov/enforcement-litigation/litigation-releases/lr-26278
- Status page shows scheduled spot website and API maintenance on 26 Nov 2026 (about 15 minutes), after which "markets will briefly enter cancel-only mode, and then post-only mode". MEASURED. https://status.kraken.com/

### Sign-up
Create account, verify identity (documents above), create API key in Settings > API and tick permissions. Approval time: UNKNOWN.

---

## 3. Gemini (Gemini Trust Company, LLC), ActiveTrader / exchange API

### Eligibility
| Item | Finding | Tag | Source |
|---|---|---|---|
| Idaho | "Gemini is available in 60+ countries, including all 50 U.S. states." | MEASURED | https://support.gemini.com/hc/en-us/articles/204072799-Which-countries-and-U-S-states-does-Gemini-support |
| Registrations | Gemini Trust Company, LLC NMLS #1518126. "a fiduciary and qualified custodian under the New York Banking Law and is licensed by the New York State Department of Financial Services". Idaho licence line: UNKNOWN. | MEASURED / UNKNOWN | https://www.gemini.com/legal/licenses , https://www.gemini.com/trust-center |
| Minimum deposit | Not checked. | UNKNOWN | |

### API
| Item | Finding | Tag | Source |
|---|---|---|---|
| Official API | REST, WebSocket, FIX (FIX not verified today). Python sample code in `github.com/gemini/developer-platform`. | MEASURED | https://developer.gemini.com/docs/docs |
| Order types | `exchange limit`, `exchange stop limit`, `exchange market`; options `maker-or-cancel` (post-only), `immediate-or-cancel`, `fill-or-kill`. `client_order_id` "Recommended", max 100 characters. | MEASURED | https://developer.gemini.com/rest/orders , https://developer.gemini.com/error-codes |
| Sandbox | "full exchange functionality with test funds. Automated bots simulate order book activity and trading." REST `https://api.sandbox.gemini.com`. Best sandbox of the five. | MEASURED | https://developer.gemini.com/get-started/sandbox |
| Rate limits | Private: 600 req/min, recommend not over 5/s. Public: 120 req/min. | MEASURED | https://developer.gemini.com/rate-limit |
| Key roles | Trader (default) can place/cancel orders, cannot withdraw. Fund Manager can withdraw. Auditor is read-only. Withdraw endpoint `/v2/withdraw` is Fund Manager only. | MEASURED | https://developer.gemini.com/roles.md |
| Account scope | Key can be scoped to one sub-account instead of Master. | MEASURED | https://support.gemini.com/hc/en-us/articles/360031080191-How-do-I-create-an-API-key |
| IP allowlist | Key can be "Unrestricted or restricted to Trusted IPs Only"; Gemini "recommends" Trusted IPs. | MEASURED | same |
| Min order BTCUSD | 0.00001 BTC. | MEASURED (live API) | https://api.gemini.com/v1/symbols/details/btcusd |
| Min order ETHUSD | 0.001 ETH. | MEASURED (live API) | https://api.gemini.com/v1/symbols/details/ethusd |
| Key expiry | Not stated. | UNKNOWN | |

### Terms on automation
User Agreement has an "Agentic Trading Services" section covering an AI Agent "connected to the Gemini Platform via the Model Context Protocol ("MCP") or our API". Key lines: "all Orders placed through or by an AI Agent using your Gemini Account ID are your Orders"; "You agree to set appropriate position limits and to monitor AI Agent activity regularly." Use of the API binds you to the API Agreement (https://gemini.com/api-agreement/, not opened). MEASURED. https://www.gemini.com/legal/gemini-trust-user-agreement/

### Costs (MEASURED, effective 1 Sep 2026, https://www.gemini.com/fees/activetrader-fee-schedule)
Tier = better of trailing 30-day volume (stablecoin pairs excluded) or asset balance; recalculated daily about 2am UTC.

| 30-day volume | or balance | Maker | Taker |
|---|---|---|---|
| $0+ | $0+ | 60 bps | 120 bps |
| $10K | $1M | 40 bps | 80 bps |
| $25K | $5M | 25 bps | 50 bps |
| $75K | $15M | 12.5 bps | 25 bps |

Stablecoin pairs: RLUSD/USD, USDC/GUSD, GUSD/USD 0/0.

### Safety
- "Gemini is a full-reserve exchange and custodian ... held 1:1". Audited financial statements dated December 2025 listed. Merkle proof of reserves: UNKNOWN. MEASURED. https://www.gemini.com/trust-center
- NYDFS consent order 28 Feb 2024: "$37 million dollar penalty" and $40 million toward Earn recovery; 100% of Earn assets returned by 20 Jun 2024. MEASURED. https://www.dfs.ny.gov/system/files/documents/2025/03/nysdfs-2024-cpfed-annual-rpt-20250315.pdf
- CFTC consent order, 13 Jan 2025 release: "$5 million civil monetary penalty" for false or misleading statements to the CFTC. MEASURED. https://cftc.gov/PressRoom/PressReleases/9031-25

### Sign-up
Sign up at exchange.gemini.com, then Settings > API, create a key with the Trading scope. MEASURED. https://developer.gemini.com/docs/docs . Approval time: UNKNOWN.

---

## 4. Alpaca Crypto (Alpaca Crypto LLC)

### Eligibility
| Item | Finding | Tag | Source |
|---|---|---|---|
| Idaho | Crypto trading is available in listed US jurisdictions, which include Idaho. That support page carries the date "May 2023". | MEASURED (old date) | https://alpaca.markets/support/alpaca-cryptocurrency |
| Registration | "Alpaca Crypto LLC ... a FinCEN registered money services business (NMLS # 2160858)". State licences: not found. | MEASURED / UNKNOWN | https://docs.alpaca.markets/us/docs/paper-trading |
| Minimum deposit | Not checked in this file (brokerage researchers cover Alpaca account opening). | UNKNOWN | |

### API
| Item | Finding | Tag | Source |
|---|---|---|---|
| Coins | "over 20+ unique crypto assets across 56 trading pairs"; support list dated March 2026 includes BTC, ETH, SOL, XRP, DOGE, LINK, LTC, AVAX and others, quoted in USD, USDC, USDT, BTC. | MEASURED | https://docs.alpaca.markets/us/docs/crypto-trading , https://alpaca.markets/support/what-cryptocurrencies-does-alpaca-currently-support |
| Order types | Market, Limit, Stop Limit; time in force `gtc` and `ioc`; fractional by `notional` or `qty`. (Stated on the Broker API crypto page.) | MEASURED | https://docs.alpaca.markets/us/docs/crypto-trading-1 |
| Max order | "an order (buy or sell) must not exceed $200k in notional." | MEASURED | same |
| Min order BTC and ETH (USD pairs) | "For USD pairs, the minimum order size calculation is: 10/USD asset price." So $10 notional. At today's Coinbase BTC-USD price of $59,099.72 that is about 0.000169 BTC; at ETH-USD $1,655.21 about 0.00604 ETH (my arithmetic, prices from Coinbase public API today). | MEASURED rule, my arithmetic | same; Coinbase API above |
| Paper trading | "Paper trading simulates crypto trading as well." Does not account for market impact, slippage due to latency, queue position, price improvement, regulatory fees. $100k default balance. Partial fills "for a random size 10% of the time". Whether crypto trading fees are simulated in paper: UNKNOWN. | MEASURED / UNKNOWN | https://docs.alpaca.markets/us/docs/paper-trading |
| Auth | Live and paper keys are separate: "you cannot use your live account's credentials for paper trading, or vice versa." CLI supports OAuth for paper. | MEASURED | https://docs.alpaca.markets/us/docs/authentication , https://docs.alpaca.markets/us/docs/alpacas-cli |
| Key scopes / IP allowlist for an individual Trading API key | Fine-grained scopes (Crypto, Funding, Trading, etc.) and expiry are documented for Broker API (BrokerDash) partner keys, not clearly for individual Trading API keys. For an individual account: UNKNOWN. | MEASURED (broker only) / UNKNOWN | https://docs.alpaca.markets/us/docs/credential-management |
| Execution venue | "Alpaca Crypto executes customer trades on our internal central limit order book, self-clears all trades". | MEASURED | https://docs.alpaca.markets/us/docs/alpaca-api-platform |

### Costs (MEASURED, https://docs.alpaca.markets/docs/crypto-fees , page date 2025-09-24 per index)
| Tier | 30-day crypto volume | Maker | Taker |
|---|---|---|---|
| 1 | $0-$100K | 15 bps | 25 bps |
| 2 | $100K-$500K | 12 bps | 22 bps |
| 3 | $500K-$1M | 10 bps | 20 bps |

Wallet withdrawals, two Alpaca pages disagree: the Crypto Wallet FAQ says "Alpaca charges 50bps (0.5%) of the amount withdrawn" plus a fixed gas fee (for example 0.002 ETH); another support page says "Wallets are free to use. The only fees ... are the corresponding network fees". MEASURED (conflict). https://alpaca.markets/support/crypto-wallet-faq , https://alpaca.markets/support/what-are-the-fees-associated-with-alpacas-crypto-wallets

### Safety
- Custody: "Alpaca Crypto maintains its customers' cryptocurrency in wallets secured by Fireblocks' MPC-CMP architecture." Crypto Customer Agreement: Alpaca Crypto "may hold My Cryptocurrency together with the Cryptocurrency of o[ther customers]". Proof of reserves: UNKNOWN. MEASURED. https://alpaca.markets/support/where-does-alpaca-hold-crypto-assets-purchased-through-its-platform , https://files.alpaca.markets/disclosures/library/Crypto%20Customer%20Agreement.pdf
- Enforcement (affiliate, not the crypto entity): SEC order of 24 Sep 2024 against Alpaca Securities LLC for off-channel communications recordkeeping; FINRA 19h-1 notice 6 Mar 2025. MEASURED. https://www.finra.org/sites/default/files/2025-03/SD-2436-Alpaca-03-06-2025.pdf

---

## 5. Robinhood Crypto (Robinhood Crypto, LLC), Crypto Trading API

### Eligibility
| Item | Finding | Tag | Source |
|---|---|---|---|
| Idaho | Robinhood Crypto is available in every US state and DC. Needs age 18+, SSN (not TIN), US address. | MEASURED | https://robinhood.com/us/en/about/crypto/ |
| Registrations | NYDFS virtual currency licence; FinCEN MSB; "applicable U.S. state money transmitter laws". Crypto "not FDIC insured or SIPC protected". | MEASURED | same |
| API availability | "available to customers in the United States only." Keys are created in crypto account settings "on web classic". | MEASURED | https://docs.robinhood.com/crypto/trading/ |

### API
| Item | Finding | Tag | Source |
|---|---|---|---|
| Versions | v1 places orders "without fee tiers" (prices from "partner market makers" and "include a spread"); v2 places orders "with fee tiers" routed to "partner exchanges". | MEASURED | https://docs.robinhood.com/crypto/trading/ |
| Order types | market, limit, stop_loss, stop_limit; GTC shown. Only USD pairs with `is_api_tradable=true`. | MEASURED | same |
| Idempotency | `client_order_id` required: "User input order id for idempotency validation". | MEASURED | same |
| Rate limits | 100 requests/min per account, bursts 300; token bucket, "will fluctuate". | MEASURED | same |
| Auth | Ed25519 key pair; signed headers; "timestamps are only valid for 30 seconds". | MEASURED | same |
| Key scopes, no-withdraw key, IP allowlist, key expiry | Not stated in docs. The API has no documented withdrawal endpoint in the sections read. | UNKNOWN | same |
| Min order size | Per pair from `Get Crypto Trading Pairs` (`min_order_size` v1, `min_order_amount` v2); values need an authenticated call. | UNKNOWN (values) | same |
| Sandbox | None documented. | UNKNOWN | same |

### Terms on automation
Crypto Customer Agreement 20.8 "Use of AI Agents": "I am solely responsible for my investment decisions and for any orders placed in my Account"; "any instruction submitted to Robinhood from an authenticated session of my AI agent shall be final and binding"; the customer must ensure agent activity complies with prohibitions on "spoofing, wash trading". In-app agents may only place orders in an "Agentic Account". Also: "my Account remains self-directed if I authorize an AI agent to place orders in it." MEASURED. https://robinhood.com/us/en/crypto-customer-agreement/

### Costs (MEASURED, https://cdn.robinhood.com/assets/robinhood/legal/rhc-fee-schedule.pdf , document ID 20261102-6078699-19354665, no printed date)
Market maker routing (default, and v1 API): "No commissions"; cost is in the spread; "We receive volume rebates from those market makers." Spread size: not published (UNKNOWN). A third-party site says Robinhood receives "$0.95 per $100 traded from market makers (since 2026-06-15)" (STATED, https://altrookie.com/guide/robinhood-crypto-fees).

Exchange routing (v2 API), routed to EDX Markets and Bitstamp USA:

| 30-day volume | Reduced (maker) | Standard (taker) |
|---|---|---|
| $0-$10K | 50 bps | 95 bps |
| $10K-$50K | 35 bps | 75 bps |
| $50K-$250K | 12.5 bps | 25 bps |

Important: "Executed crypto orders placed through v2 of the Robinhood Crypto Trading API count toward volume, but are charged the standard rate until reduced/standard is fully rolled out." "Market orders and stop orders are always charged a standard fee." v1 API volume does not count. MEASURED. https://robinhood.com/us/en/support/articles/crypto-fee-tiers/

Crypto transfers: "$0" from Robinhood plus network fee. MEASURED (fee schedule PDF).

### Safety and enforcement
- SEC Enforcement closed its Robinhood Crypto investigation with no action (letter 21 Feb 2025). MEASURED. https://robinhood.com/newsroom/sec-closes-investigation-into-robinhood-crypto-with-no-action/
- California AG settlement 4 Sep 2024: $3.9 million for not letting customers withdraw crypto 2018-2022 and incomplete order-handling disclosure. MEASURED. https://www.oag.ca.gov/news/press-releases/attorney-general-bonta-secures-39-million-settlement-cryptocurrency-company
- 20 Oct 2025 AWS outage: users reported Robinhood "trading execution delays and Application Programming Interface (API) issues". STATED (press). https://cointelegraph.com/news/amazon-aws-outage-coinbase-app-robinhood

---

## Round-trip fee at the lowest tier (one buy plus one sell)

Formula: round trip in bps = buy-side fee bps + sell-side fee bps. 1 bps = 0.01%. On a $1,000 round trip (buy $1,000, sell about $1,000), dollars = bps x $0.10.

| Venue | Taker-taker | Maker-maker |
|---|---|---|
| Coinbase Advanced (Exchange schedule proxy, $0-$10K) | 60 + 60 = 120 bps (1.20%, about $12.00 per $1,000) | 40 + 40 = 80 bps (0.80%, about $8.00) |
| Coinbase Advanced with Coinbase One Preferred 25% rebate | 60 x 0.75 = 45; 45 + 45 = 90 bps (rebate capped at $100/month, plus $29.99/month fee) | 40 x 0.75 = 30; 30 + 30 = 60 bps |
| Kraken Pro Tier 1 ($0+) | 80 + 80 = 160 bps (1.60%, $16.00) | 40 + 40 = 80 bps (0.80%, $8.00) |
| Kraken Pro Tier 2 ($2.5K+ volume) | 60 + 60 = 120 bps | 30 + 30 = 60 bps |
| Kraken Pro Tier 3 ($10K+ volume or $20K held) | 38 + 38 = 76 bps | 22 + 22 = 44 bps |
| Gemini ($0+) | 120 + 120 = 240 bps (2.40%, $24.00) | 60 + 60 = 120 bps (1.20%, $12.00) |
| Alpaca Crypto Tier 1 ($0-$100K) | 25 + 25 = 50 bps (0.50%, $5.00) | 15 + 15 = 30 bps (0.30%, $3.00) |
| Robinhood API v2 ($0-$10K), as charged today | 95 + 95 = 190 bps (1.90%, $19.00) | Resting limits charged standard for v2 today: 95 + 95 = 190 bps. Once rolled out: 50 + 50 = 100 bps |
| Robinhood API v1 | No commission; spread both sides, size not published: UNKNOWN | same |

These are fee costs only. They exclude spread paid by takers, slippage, and funding or withdrawal fees.

## Comparison table

| Item | Coinbase Advanced | Kraken Pro | Gemini | Alpaca Crypto | Robinhood Crypto API |
|---|---|---|---|---|---|
| Idaho resident | Yes, Idaho MTL-169 | Yes (only ME, NY excluded) | Yes (all 50 states) | Yes (listed, page dated May 2023) | Yes (all states) |
| Lowest tier maker / taker | 40 / 60 bps (Exchange proxy; Advanced signed-in only) | 40 / 80 bps | 60 / 120 bps | 15 / 25 bps | v2: 50 / 95 bps (95 charged on all v2 today); v1: spread |
| Tier 2 maker / taker and threshold | 25 / 40 at $10K | 30 / 60 at $2.5K | 40 / 80 at $10K | 12 / 22 at $100K | 35 / 75 at $10K |
| Tier 3 maker / taker and threshold | 15 / 25 at $50K | 22 / 38 at $10K or $20K held | 25 / 50 at $25K | 10 / 20 at $500K | 12.5 / 25 at $50K |
| Round trip T1 taker-taker / maker-maker | 120 / 80 bps | 160 / 80 bps | 240 / 120 bps | 50 / 30 bps | 190 / 190 bps today |
| Min order BTC | 0.00000001 BTC and $1 | 0.00006 BTC (API); page also says 0.0001 | 0.00001 BTC | $10 notional | per pair, UNKNOWN |
| Min order ETH | 0.00000001 ETH and $1 | 0.002 ETH | 0.001 ETH | $10 notional | per pair, UNKNOWN |
| Trade-only key, no withdraw | Yes (View+Trade, leave Transfer off) | Yes (leave Withdraw Funds off) | Yes (Trader role) | UNKNOWN for individual keys | UNKNOWN |
| IP allowlist | Yes | Yes | Yes | UNKNOWN for individual keys | UNKNOWN |
| Key expiry | JWT 2 min; key no stated expiry | Optional expiry | UNKNOWN | UNKNOWN | 30 s timestamp window; key expiry UNKNOWN |
| Bot isolation | Portfolios, one key per portfolio | Subaccounts (not detailed here) | Sub-accounts, key scoped to one | Separate account | Agentic Account for in-app agents |
| Sandbox | Static mocked responses | Spot UAT on request; CLI paper engine | Full test exchange with simulated flow | Paper covers crypto | None documented |
| Python SDK | Official | CLI; SDK not stated | Sample code | Official (not checked in this file) | Sample scripts |
| Private rate limit | UNKNOWN for Advanced REST | Counter 15-20, decay by tier | 600/min | Not checked | 100/min, burst 300 |
| AI-agent terms | MCP for agents, listed harnesses | None found; bots allowed per support | Agentic Trading section | Not checked | Section 20.8 AI agents |
| Custody / reserves | 1:1 statement; NYDFS-regulated custodian; no PoR found | PoR 30 Sep 2026, BTC 103.2% | Full-reserve statement; NYDFS trust | Fireblocks MPC; no PoR found | Not SIPC/FDIC; PoR not found |
| 2024-2026 enforcement | SEC case dismissed Feb 2025; May 2025 data breach | SEC case dismissed Mar 2025 | NYDFS $37M (2024), CFTC $5M (2025) | Affiliate SEC recordkeeping order 2024 | CA AG $3.9M (2024); SEC closed probe 2025 |
| Known outage | AWS, 20 Oct 2025 | Scheduled API maintenance 26 Nov 2026 | Not researched | Not researched | AWS, 20 Oct 2025 (press) |
