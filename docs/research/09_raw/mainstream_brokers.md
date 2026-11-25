> Raw researcher report, kept as evidence. Some figures here were corrected after a fresh check. The corrected version is `docs/research/09_brokers_and_venues.md`, which wins where the two differ. Known corrections: the Coinbase Advanced entry fee is 0.50% maker and 0.90% taker, not 0.40% and 0.60%; an Alpaca duplicate order id returns HTTP 422, not 409.

# Mainstream US Retail Stock Brokers for Automated Trading

Date researched: 2026-11-24.
Scope: Mainstream US retail stock brokers and low-minimum direct-access brokers for a US retail individual living in Idaho building a rule-based automated trading system (US stocks, ETFs, and spot crypto where offered).
Claim tags: `MEASURED` (read directly on a primary firm or regulator page today), `STATED` (third-party source or unverified claim), `UNKNOWN` (not found on public pages today).

---

## Brokers Without a Usable or Low-Minimum Official Retail API (One-Row Summary)

| Broker | Official Retail Stock Trading API? | Minimum / Blocker | Source & Tag |
| --- | --- | --- | --- |
| Fidelity | No. No public retail trading API exists; APIs are restricted to institutional/advisor platforms (Wealthscape, Fidelity Digital Assets). | No retail stock API available. | `STATED` ([APIs.io](https://apis.io/providers/fidelity-investments/), [AIStockTradingBots](https://aistocktradingbots.com/blog/fidelity-api/)) |
| Lightspeed | Yes (Lightspeed Connect WebSocket/JSON API for equities, options, short locates; commissions from $0.001/sh). | $30,000 minimum account equity required (Reg-T or cash). | `MEASURED` ([Lightspeed API](https://lightspeed.com/trading/api-trading)) |
| CenterPoint Securities | Yes (REST and WebSocket API; free API if >= 100,000 shares/month). | $50,000 minimum account balance required. | `MEASURED` ([CenterPoint API](https://centerpointsecurities.com/api/)) |
| Cobra Trading | Yes (C#/.NET, CMD, FIX API). | $10,000 day-trading minimum account balance. | `STATED` ([Cobra FAQ](https://www.cobratrading.com/faq/), [Cobra API Services](https://www.cobratrading.com/api-services/)) |

---

## 1. Charles Schwab (Trader API - Individual)

### 1.1 Eligibility
- US retail individual: Yes. "A Schwab brokerage account is required to access Trader APIs." `MEASURED` ([Become Individual Developer](https://developer.schwab.com/user-guides/individual-developer/become-individual-developer), no date printed).
- Idaho residency: Standard US broker-dealer nationwide availability for equities/ETFs. Schwab does not offer direct spot crypto trading via Trader API. `MEASURED` ([Trader API - Individual](https://developer.schwab.com/products/trader-api--individual), no date printed).
- Account types: Cash, margin, IRA, and Schwab One Organization (entity/LLC) accounts exist; Organization accounts have a separate minimum ("contact Schwab"). `MEASURED` ([Schwab Pricing Guide](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors), dated April 2026 / footer 03/26).
- Minimum deposit: $0 for individual Schwab One and IRA accounts. `MEASURED` ([Schwab Pricing Guide](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors)).
- Minimum for API: No separate dollar minimum stated on the public Individual Developer portal; requires an active Schwab brokerage account. `MEASURED` ([Become Individual Developer](https://developer.schwab.com/user-guides/individual-developer/become-individual-developer)).

### 1.2 API
- Official retail trading API: Yes, Schwab Trader API - Individual for self-directed trading on "your own brokerage trading account." `MEASURED` ([Trader API - Individual](https://developer.schwab.com/products/trader-api--individual)).
- Protocols: REST + real-time data mentioned on portal (`MEASURED`, [Trader API - Individual](https://developer.schwab.com/products/trader-api--individual)); WebSocket streaming for quotes/account activity via community docs (`STATED`, [schwab-py docs](https://schwab-py.readthedocs.io/en/latest/auth.html)).
- Official Python SDK / OpenAPI spec: No official Schwab Python SDK is published on the public portal; detailed OpenAPI specs sit behind developer portal login. `UNKNOWN` on public portal; community libraries like `schwab-py` are widely used (`STATED`, [schwab-py docs](https://schwab-py.readthedocs.io/en/latest/auth.html)).
- Sandbox / paper trading: No paper trading endpoint for Trader API. thinkorswim paperMoney is manual/UI only and not accessible via Trader API. `STATED` ([Schwab Trader API Field Notes](https://github.com/Jorg-AI-JorgAI/schwab-trader-api-field-notes)).
- Order types, fractional shares, extended hours, short selling: Standard equity/option order types and extended hours are supported; fractional shares are not supported via the Trader API. `STATED` ([Schwab Trader API Field Notes](https://github.com/Jorg-AI-JorgAI/schwab-trader-api-field-notes)).
- Rate limits: Not published on public unauthenticated portal pages (`UNKNOWN` primary); community reports ~120 requests/minute per account (`STATED`, [MyLinedChart](https://mylinedchart.com/resources/articles/schwab-api-rate-limits-and-token-expiry)).
- Idempotency / client order ID: Not documented on public unauthenticated pages. `UNKNOWN`.
- Key permissions: OAuth 2.0 ("Using OAuth 2.0, clients can authorize your app to access their financial data; without having to share their credentials"). Trade-only vs no-withdraw scopes and IP allowlists are not detailed on public pages. `MEASURED` ([Trader API - Individual](https://developer.schwab.com/products/trader-api--individual)) / `UNKNOWN` for scope granularity.
- Token expiry: Access token expires in 30 minutes; refresh token has a hard 7-day expiry requiring a manual browser OAuth re-login every 7 days. `STATED` ([schwab-py docs](https://schwab-py.readthedocs.io/en/latest/auth.html), [MyLinedChart](https://mylinedchart.com/resources/articles/schwab-api-rate-limits-and-token-expiry)). This breaks unattended automation unless a human re-authenticates weekly.

### 1.3 Terms on Automation
- Public developer portal describes personal self-directed trading apps ("your own brokerage trading account"). `MEASURED` ([Trader API - Individual](https://developer.schwab.com/products/trader-api--individual)).
- Full Individual Developer API Agreement sits behind login; specific clauses on AI agents or order-to-fill ratios could not be inspected without logging in. `UNKNOWN`.

### 1.4 Costs
- Commissions: Pricing Guide explicitly defines "Online Trades" to include "Schwab APIs". $0 online US exchange-listed stocks and ETFs; $6.95 US OTC stocks; $0 + $0.65/contract options; $2.25/contract futures. `MEASURED` ([Schwab Pricing Guide](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors), dated April 2026).
- Regulatory fees: Industry Fee passed through (Section 31, FINRA TAF, ORF, proprietary index, ADR pass-through; exact per-unit rates not printed in summary table). `MEASURED` ([Schwab Pricing Guide](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors)).
- Crypto fees: Not applicable (no spot crypto via Trader API). `MEASURED`.
- Market data / API fees: No separate API fee stated in the Pricing Guide (`MEASURED`).
- Inactivity, wire, transfer fees: $0 inactivity; wires $0 in / $25 out ($15 online; 3 free/quarter at $100k+ household); full outgoing ACATS $50, partial $0. `MEASURED` ([Schwab Pricing Guide](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors)).
- Margin rates (last changed 9/18/2026, base rate 10.25%): $100-$24,999.99 = 12.075%; $25k-$49,999.99 = 11.575%; $50k-$99,999.99 = 10.625%; $100k-$249,999.99 = 10.575%; $250k-$499,999.99 = 10.325%; $500k+ call. `MEASURED` ([Schwab Margin Rates](https://www.schwab.com/margin/margin-rates-and-requirements), effective 9/18/2026).

### 1.5 Execution Quality Signals
- PFOF: Yes ("most orders result in rebates"); Schwab states best execution takes priority and rebates do not affect routing. `MEASURED` ([Order Routing](https://www.schwab.com/legal/order-routing-1), Q3 2026 ending Sep 30, 2026).
- Rule 606 reports: Published quarterly through Q3 2026 at [Schwab Rule 606](https://public.s3.com/rule606/chas). `MEASURED`.
- Outages 2025-2026: Brief web login/website outage reported Nov 17, 2026. `STATED` ([Business Insider](https://www.businessinsider.com/charles-scwab-website-outage-reports-2026-11)).

### 1.6 Safety
- SIPC: Charles Schwab & Co., Inc. is a SIPC member ($500,000 per capacity, $250,000 cash limit). `MEASURED` ([Schwab Account Protection](https://www.schwab.com/legal/account-protection), copyright 2026).
- Excess SIPC: "$600 million aggregate" excess SIPC program (no per-account sublimit stated on page). `MEASURED` ([Schwab Account Protection](https://www.schwab.com/legal/account-protection)).
- Regulators: SEC-registered broker-dealer, FINRA/SIPC member; fully paid securities segregated at DTC and Bank of New York. `MEASURED` ([Schwab Account Protection](https://www.schwab.com/legal/account-protection)).
- Enforcement 2024-2026: On September 1, 2026, FINRA fined Charles Schwab & Co., Inc. $175,000 because it "failed to report to the FINRA/Nasdaq Trade Reporting Facility (TRF) or Over-the-Counter Reporting Facility (ORF) approximately 2.2 million fractional share transactions" from ACATS liquidations and had supervisory gaps. `MEASURED` ([FINRA Disciplinary Actions Nov 2026](https://www.finra.org/sites/default/files/2026-11/disciplinary-actions-november-2026.pdf)).

### 1.7 Sign-Up
- Open a Schwab brokerage account, register on `developer.schwab.com`, add the Individual Developer role in Profile, register an app (callback URL), and await approval. No firm-stated approval timeline is published on the public guide. `MEASURED` ([Become Individual Developer](https://developer.schwab.com/user-guides/individual-developer/become-individual-developer)).

---

## 2. Robinhood (No Retail Stock REST API; Official Agentic Trading MCP Server)

### 2.1 Eligibility
- US retail individual: Yes, requires a primary Robinhood individual investing account in good standing to open a dedicated Robinhood Agentic account (counts toward the 10-account limit). `MEASURED` ([Onboarding an External Agent](https://robinhood.com/us/en/support/articles/onboarding-an-external-agent/), published 2026-05-26).
- Idaho residency: Standard US broker-dealer nationwide availability for equities/ETFs. Crypto is offered via Robinhood Crypto, LLC (NMLS 1702840; separate crypto API covered elsewhere). `MEASURED` ([External Agents](https://invest.robinhood.com/us/en/agents/external-agents/), published 2026-11-20).
- Account types: Dedicated individual Agentic Trading account isolated from main portfolio; no business/LLC API support stated. `MEASURED` ([Robinhood Newsroom](https://robinhood.com/newsroom/robinhood-is-now-open-to-agents/), May 27, 2026).
- Minimum deposit / API minimum: $0 stated minimum to open. `MEASURED` ([RHF Fee Schedule](https://cdn.robinhood.com/assets/robinhood/legal/RHF+Fee+Schedule.pdf)).

### 2.2 API
- Official retail stock REST API: **None.** Robinhood has no general-purpose public REST/WebSocket API for retail stock trading. Instead, on May 27, 2026, Robinhood launched **Robinhood MCP Trading** (beta), a hosted Model Context Protocol (MCP) server at `https://agent.robinhood.com/mcp/trading` for AI agents (Claude Code, Claude Desktop, ChatGPT, Codex, Cursor, Grok, Perplexity). `MEASURED` ([Onboarding an External Agent](https://robinhood.com/us/en/support/articles/onboarding-an-external-agent/), [Robinhood Newsroom](https://robinhood.com/newsroom/robinhood-is-now-open-to-agents/)).
- Capabilities via MCP: Read access to all Robinhood accounts, watchlists, and market data; trade placement restricted strictly to the dedicated Agentic account ("Your agent can only place trades in your Robinhood Agentic account"). Lists tools for equities, options, and crypto. `MEASURED` ([Onboarding an External Agent](https://robinhood.com/us/en/support/articles/onboarding-an-external-agent/)).
- SDK / OpenAPI / Streaming / Paper / Rate limits / Idempotency: Not a traditional programmatic SDK or streaming market-data API. No paper trading endpoint, no public REST rate-limit table, and no `client_order_id` idempotency spec published. `UNKNOWN`.
- Safety controls: Account isolation (dedicated Agentic account), push notifications per trade, and one-tap disconnect in the Robinhood app. `MEASURED` ([Robinhood Newsroom](https://robinhood.com/newsroom/robinhood-is-now-open-to-agents/)).

### 2.3 Terms on Automation
- Explicitly permits AI agent automation through the MCP product: "Robinhood MCP Trading is a new type of brokerage product that allows customers to connect a third-party AI agent to a dedicated Robinhood account to automate investment decisions and order placement." `MEASURED` ([External Agents](https://invest.robinhood.com/us/en/agents/external-agents/), published 2026-11-20).
- Liability disclaimer: Robinhood states it does not "control, supervise, monitor, recommend, or audit" external agents; customer assumes all risk. `MEASURED` ([External Agents](https://invest.robinhood.com/us/en/agents/external-agents/)).
- High order rates (options): Professional options traders (>390 orders/day average) are charged $0.50/contract effective Oct 15, 2026. `MEASURED` ([RHF Fee Schedule](https://cdn.robinhood.com/assets/robinhood/legal/RHF+Fee+Schedule.pdf)).

### 2.4 Costs
- Commissions: $0 US equities, ETFs, and stock/ETF options; index options $0.50/contract ($0.35 with Gold). `MEASURED` ([RHF Fee Schedule](https://cdn.robinhood.com/assets/robinhood/legal/RHF+Fee+Schedule.pdf)).
- Regulatory fees: SEC fee $20.60 per $1M principal on sells (eff. Apr 4, 2026); FINRA TAF $0.000195/sh equity sells, $0.00329/contract option sells, max $9.79 (eff. Jan 1, 2026; note Robinhood support article [Trading Fees](https://robinhood.com/us/en/support/articles/trading-fees-on-robinhood/) notes FINRA paused TAF Oct 1-Dec 31, 2026); ORF+OCC $0.04/contract; CAT $0.000003/sh equities and $0.0003/contract options. `MEASURED`.
- Margin rates (as of Sep 16, 2026): Up to $50k = 5.25%; $50k-$100k = 5.05%; $100k-$1M = 4.75%; $1M-$10M = 4.50%; $10M-$50M = 4.45%; $50M+ = 4.20%. `MEASURED` ([RHF Fee Schedule](https://cdn.robinhood.com/assets/robinhood/legal/RHF+Fee+Schedule.pdf)).
- Other fees: $0 inactivity, $0 incoming wire, $25 outgoing wire, $100 outgoing ACATS. `MEASURED` ([RHF Fee Schedule](https://cdn.robinhood.com/assets/robinhood/legal/RHF+Fee+Schedule.pdf)).

### 2.5 Execution Quality Signals
- PFOF & Rule 606: Yes. Robinhood Securities (RHS) routes equity orders primarily to Virtu Americas, Citadel Securities, and Jane Street Capital, and shares 80% of PFOF revenue with Robinhood Financial (RHF) per Rule 606(a) disclosures. `STATED` ([SEC 8-K summary](https://www.moomoo.com/news/notice/303742107/robinhood-8-k-nms-stocks-and-options-order-routing-public)).
- Outages 2025-2026: No major multi-day brokerage API outage confirmed on primary pages. `UNKNOWN`.

### 2.6 Safety
- SIPC & Excess SIPC: Robinhood Financial LLC (RHF) and Robinhood Securities, LLC (RHS) are SIPC members ($500,000, including $250,000 cash). Additional excess SIPC insurance covers up to "$1 billion" aggregate, "limited to a combined return to any customer of $50 million in securities and $1.9 million in cash." `MEASURED` ([Robinhood SIPC](https://robinhood.com/us/en/support/articles/Account-protection-with-SIPC/), no last-updated date).
- Crypto custody: Robinhood Crypto, LLC (NMLS 1702840); not SIPC or FDIC insured. `MEASURED` ([External Agents](https://invest.robinhood.com/us/en/agents/external-agents/)).
- Enforcement 2024-2026: On January 13, 2025, the SEC fined Robinhood Securities ($33.5M) and Robinhood Financial ($11.5M) a combined **$45 million** for SAR delays, identity-theft/cybersecurity lapses, off-channel communications, database retention, blue sheets, and Reg SHO fractional-share/stock-lending violations ("failed to observe a broad array of significant regulatory requirements"). `MEASURED` ([SEC Press Release 2025-5](https://www.sec.gov/newsroom/press-releases/2025-5)). In March 2025, FINRA also fined Robinhood $26M plus $3.75M restitution (`STATED`, [HOOD 10-Q](https://www.sec.gov/Archives/edgar/data/1783879/000178387926000167/hood-20260930.htm)).

### 2.7 Sign-Up
- Open a standard Robinhood individual account, enable a dedicated Agentic Trading account in-app, and connect an MCP client (e.g., `claude mcp add robinhood-trading --transport http https://agent.robinhood.com/mcp/trading`) via OAuth sign-in. No separate developer review timeline stated. `MEASURED` ([Onboarding an External Agent](https://robinhood.com/us/en/support/articles/onboarding-an-external-agent/)).

---

## 3. Public.com (Public API)

### 3.1 Eligibility
- US retail individual: Yes, personal use for individual Public Investing brokerage customers. `MEASURED` ([Individual API Program](https://public.com/disclosures/individual-API-program), dated June 2026).
- Idaho residency: US brokerage nationwide. For spot crypto (via Zero Hash): "Cryptocurrency trading, powered by zero hash, is available for Public US customers that are physically located in the United States." No state exclusions are listed on that FAQ page, though Idaho is not explicitly named. `MEASURED` ([Zero Hash FAQ](https://help.public.com/en/articles/12550593-where-can-i-trade-with-zerohash), dated Dec 11, 2025).
- Account types: Multiple brokerage accounts (`accountId`), cash, margin (`brokerageAccountType: MARGIN`), and Business Accounts ("Yes - Public Business Accounts get free access to the Public API for trading stocks, ETFs, options, index options, bonds, and crypto"). `MEASURED` ([Public API FAQ](https://public.com/api/docs/faq), [Business API FAQ](https://help.public.com/en/articles/16948003-does-public-support-api-trading-for-business-accounts), dated Sep 14, 2026).
- Minimum deposit / API minimum: $0 deposit minimum; no minimum balance required for API access. `MEASURED` ([Individual API Program](https://public.com/disclosures/individual-API-program)).

### 3.2 API
- Official retail trading API: Yes, modern REST API covering US stocks/ETFs, equity and index options (up to 6 legs), bonds/Treasuries, prediction markets, and spot crypto (Zero Hash). Also offers a hosted MCP server (`https://mcp.public.com/mcp`) and an official Agent Skill. `MEASURED` ([Public API FAQ](https://public.com/api/docs/faq)).
- Protocols & SDKs: REST HTTP (no WebSocket streaming documented on FAQ). Official Python SDK (`publicdotcom-py`), official CLI, and Postman collection. `MEASURED` ([Public API FAQ](https://public.com/api/docs/faq)).
- Sandbox / paper trading: **No paper trading sandbox.** Offers preflight order estimation endpoints only. `MEASURED` ([Public API FAQ](https://public.com/api/docs/faq)).
- Order types: `MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT`, `MARKET_ON_CLOSE`, `LIMIT_ON_CLOSE`; `DAY` or `GTD` (up to 90 days); `SIMPLE`, `BRACKET`, `OCO`, and `OTO` with trailing stops (amount or percentage); cancel-replace (`PUT` with `orderId` and new UUID `requestId`). `MEASURED` ([Place Order Docs](https://public.com/api/docs/resources/order-placement/place-order)).
- Fractional shares: Supported ($5 min / $250k max) during `CORE` regular hours via notional `amount` or fractional `quantity` on sells; extended hours and bracket orders require whole shares. `MEASURED` ([Public API FAQ](https://public.com/api/docs/faq), [Place Order Docs](https://public.com/api/docs/resources/order-placement/place-order)).
- Extended & overnight hours: `EXTENDED` (4:00 AM to 8:00 PM ET, `DAY` TIF) and `TWENTY_FOUR_HOURS` (24/5 session). `MEASURED` ([Place Order Docs](https://public.com/api/docs/resources/order-placement/place-order)).
- Short selling: Supported on margin accounts, with API fields for `shortingAvailability` and `hardToBorrowPercentageRate`. `MEASURED` ([Public API FAQ](https://public.com/api/docs/faq)).
- Rate limits: 10 requests/second per account (returns HTTP `429`). `MEASURED` ([Public API FAQ](https://public.com/api/docs/faq)).
- Idempotency / client order ID: Yes. Caller generates RFC 4122 UUID `orderId` ("must be globally unique over time"); if reused on the same account, "the operation is idempotent." `MEASURED` ([Place Order Docs](https://public.com/api/docs/resources/order-placement/place-order)).
- Auth & token expiry: Generate a persistent secret key in settings, then exchange it programmatically at `POST /userapiauthservice/personal/access-tokens` with custom `validityInMinutes` for a Bearer token. No manual browser re-login loop required. Trade-only vs no-withdraw scopes or IP allowlist are not stated on public FAQ. `MEASURED` ([Public API FAQ](https://public.com/api/docs/faq)) / `UNKNOWN` for IP allowlist.

### 3.3 Terms on Automation
- Explicitly allows personal automated trading ("solely for their own personal use"). `MEASURED` ([Individual API Program](https://public.com/disclosures/individual-API-program), dated June 2026).
- Restrictions: Prohibits mirroring/copying other users' trades or wrapping the API for third parties; Public may throttle or suspend access without notice. Explicitly welcomes AI agents via hosted MCP and Agent Skills. `MEASURED` ([Individual API Program](https://public.com/disclosures/individual-API-program), [Public API FAQ](https://public.com/api/docs/faq)).

### 3.4 Costs
- Stock/ETF commissions: $0 regular hours, $0 extended hours, $0 OTC. `MEASURED` ([Public Fee Schedule](https://public.com/disclosures/fee-schedule), last updated October 13, 2026).
- Order routing choices & fees: Wholesale = $0; Smart Order (SDPs, ATSs, exchanges, no wholesaler PFOF) = $0.003/share; Lit Exchanges Only = $0.003/share. `MEASURED` ([Public Fee Schedule](https://public.com/disclosures/fee-schedule)).
- Options: $0 stock/ETF options (plus $0.06-$0.18/contract rebate if enrolled in Options Rebate Program); $0.35/contract index options + exchange fees. `MEASURED` ([Public Fee Schedule](https://public.com/disclosures/fee-schedule)).
- Crypto API fees (Zero Hash, first-party API & Agentic API): Tiered by monthly volume: $0-$10k = 0.60%, $10k-$50k = 0.50%, $50k-$100k = 0.40%, $100k-$1M = 0.30%, $1M-$15M = 0.20%, $15M-$100M = 0.15%, $100M+ = 0.10%. (Non-API app fee is 1.25% above $500.) `MEASURED` ([Public Fee Schedule](https://public.com/disclosures/fee-schedule)).
- API & market data fees: API is "currently made available without charge." `MEASURED` ([Individual API Program](https://public.com/disclosures/individual-API-program)).
- Margin rates (as of Sep 17, 2026, FFTR = 4.00%): Up to $50k = 5.15% (FFTR+1.15%); $50k-$100k = 5.00%; $100k-$1M = 4.75%; $1M-$10M = 4.50%; $10M-$50M = 4.45%; $50M+ = 4.20%. `MEASURED` ([Public Fee Schedule](https://public.com/disclosures/fee-schedule)).
- Administrative fees: Inactivity fee $3.99/month only if account < $70 total value and no activity for 6 months; incoming ACAT $0, outgoing ACAT $100; incoming wire $0, outgoing domestic wire $25. `MEASURED` ([Public Fee Schedule](https://public.com/disclosures/fee-schedule)).

### 3.5 Execution Quality Signals
- PFOF & routing choice: Wholesale route receives PFOF; customer can opt out into Smart Order or Lit Exchanges Only for $0.003/share (no wholesaler PFOF). `MEASURED` ([Annual Disclosure 2026](https://public.com/disclosures/annual-disclosure-2026), dated 01/2026).
- Rule 606: Quarterly reports published; Rule 606(b) 6-month customer-specific routing report available via `support@public.com`. `MEASURED` ([Annual Disclosure 2026](https://public.com/disclosures/annual-disclosure-2026)).
- Outages 2025-2026: None confirmed on primary status pages. `UNKNOWN`.

### 3.6 Safety
- Regulators & clearing: Open to the Public Investing, Inc. is SEC-registered, FINRA/SIPC member; clears on a fully disclosed basis through **Apex Clearing Corporation**. `MEASURED` ([Annual Disclosure 2026](https://public.com/disclosures/annual-disclosure-2026)).
- SIPC: Up to $500,000 ($250,000 cash). Excess SIPC not specified on the 2026 Annual Disclosure page. `MEASURED` ([Annual Disclosure 2026](https://public.com/disclosures/annual-disclosure-2026)).
- Crypto custody: Zero Hash LLC (not SIPC/FDIC). `MEASURED` ([Individual API Program](https://public.com/disclosures/individual-API-program)).
- Enforcement 2024-2026: No major 2024-2026 SEC/FINRA enforcement actions found in searches today. `UNKNOWN`.

### 3.7 Sign-Up
- Open a Public brokerage account, generate an API secret key in account settings, and exchange it for Bearer tokens immediately. No manual developer review wait stated. `MEASURED` ([Public API FAQ](https://public.com/api/docs/faq)).

---

## 4. Webull (Webull OpenAPI)

### 4.1 Eligibility
- US retail individual: Yes, Retail Individual Mode requires an opened Webull brokerage account. `MEASURED` ([Individual Application API](https://developer.webull.com/apis/docs/authentication/IndividualApplicationAPI/), no date printed).
- Idaho residency: US equities/options/futures nationwide. For crypto, the Webull Crypto Fees page notes limits for customers outside New York, Guam, and the Northern Mariana Islands, without printing a complete state list confirming Idaho explicitly. `MEASURED` ([Webull Crypto Fees & Limits](https://www.webull.com/help/faq/11091-Fees-Limits), no last-updated date).
- Account types: Cash and margin accounts supported; entity/business API eligibility not detailed on Individual Application page. `MEASURED` / `UNKNOWN` for LLCs.
- Minimum deposit / API minimum: "0 commission trades and no deposit minimums." No separate account minimum stated for Individual OpenAPI. `MEASURED` ([Webull Pricing](https://www.webull.com/pricing), [Individual Application API](https://developer.webull.com/apis/docs/authentication/IndividualApplicationAPI/)).

### 4.2 API
- Official retail trading API: Yes, Webull OpenAPI for US Stocks/ETFs, Options, Futures (CME), Crypto, Overnight Session, and Event Contracts. Also provides a Webull CLI and official AI agent skills (`webull-openapi-skills`). `MEASURED` ([Market Data Overview](https://developer.webull.com/apis/docs/market-data-api/overview/), [Trading API Overview](https://developer.webull.com/apis/docs/trade-api/overview/)).
- Protocols & SDKs: REST HTTP (`api.webull.com`), MQTT market data streaming, gRPC order event streaming. Official SDKs for Python 3.8-3.14 (`webull-openapi-python-sdk`) and Java JDK 8+. `MEASURED` ([Webull API FAQ](https://developer.webull.com/apis/docs/faq/)).
- Sandbox / paper trading: Yes, `paperTrade` sandbox auto-approved in minutes for simulated trading. Market data in sandbox is 15-minute delayed unless subscribed in production; resetting any sandbox account resets all sandbox accounts and assigns new Account IDs. `MEASURED` ([Individual Application API](https://developer.webull.com/apis/docs/authentication/IndividualApplicationAPI/), [Market Data Overview](https://developer.webull.com/apis/docs/market-data-api/overview/)).
- Order types: Stocks: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TRAILING_STOP_LOSS`, plus `OTO`, `OCO`, `OTOCO` combos and equity algo orders (TWAP/VWAP/POV). Crypto: `MARKET` (IOC), `LIMIT`, `STOP_LOSS_LIMIT`. `MEASURED` ([Trading API FAQ](https://developer.webull.com/apis/docs/trade-api/faq/), [Order Detail Reference](https://developer.webull.com/apis/docs/reference/order-detail.md), updated 2026-11-10).
- Fractional shares: Order response quantities support 5 decimal places (`MEASURED`, [Changelog](https://developer.webull.com/apis/docs/changelog/)); full fractional order eligibility via API not explicitly confirmed in FAQ (`UNKNOWN`).
- Extended & overnight hours: Supports `CORE`, `ALL`, and `NIGHT` (Overnight Session) trading sessions. `MEASURED` ([Market Data Overview](https://developer.webull.com/apis/docs/market-data-api/overview/)).
- Short selling: Supported (`SHORT` side enum; stock instrument endpoint returns `intraday_margin_short` and `maintenance_margin_short`). `MEASURED` ([Order Detail Reference](https://developer.webull.com/apis/docs/reference/order-detail.md), [Changelog](https://developer.webull.com/apis/docs/changelog/)).
- Rate limits (Production): Place/Replace/Cancel Order = `600/60s`; Batch Place = `150/60s`; Preview = `150/10s`; Order Query / Balance / Positions = `2/2s`; Market Data Non-Display raised to `300/60s` on Oct 17, 2026. Returns HTTP `429`. `MEASURED` ([Rate Limits](https://developer.webull.com/apis/docs/rate-limits/), [Changelog](https://developer.webull.com/apis/docs/changelog/)).
- Idempotency / client order ID: Yes. `client_order_id` is required and "must be unique across all your orders" to track, modify, and cancel orders. `MEASURED` ([Trading API FAQ](https://developer.webull.com/apis/docs/trade-api/faq/)).
- Auth, key permissions & expiry: App Key + App Secret (viewed once; no automatic expiry stated); 2FA enabled by default; optional IP allowlist (not required for individual developers). `MEASURED` ([Individual Application API](https://developer.webull.com/apis/docs/authentication/IndividualApplicationAPI/), [Webull API FAQ](https://developer.webull.com/apis/docs/faq/)).

### 4.3 Terms on Automation
- Built explicitly for programmatic retail trading and AI-assisted workflows (official OpenAPI, CLI, and agent skills). `MEASURED` ([Webull API FAQ](https://developer.webull.com/apis/docs/faq/)).
- Only 1 device may access L1/L2 market data subscriptions at a time. `MEASURED` ([Market Data Overview](https://developer.webull.com/apis/docs/market-data-api/overview/)).

### 4.4 Costs
- Commissions: $0 US exchange-listed stocks, ETFs, and options. Equity Algo Order Types = $0.0050/share; Direct Routing = $0.0040/share ($0.01 min/order); certain index options = $0.50/contract; oversized option orders = $0.10/contract. `MEASURED` ([Webull Pricing](https://www.webull.com/pricing), no last-updated date).
- Regulatory fees: SEC fee $0.0000206 x total trade volume (sells); CAT fee $0.000003 x volume (buys & sells; note OTC table shows $0.00000003, a discrepancy on Webull's page); FINRA TAF currently listed as $0/share. `MEASURED` ([Webull Pricing](https://www.webull.com/pricing)).
- Crypto spread: No direct fee, but a **1% spread (100 bps)** is built into buy and sell orders (excludes stablecoins). `MEASURED` ([Webull Crypto Fees & Limits](https://www.webull.com/help/faq/11091-Fees-Limits)).
- API & market data fees: "There are no extra charges for accessing the API." However, live OpenAPI market data requires separate paid Non-Display subscriptions (Nasdaq Basic L1 or TotalView L2, OPRA, CME, Overnight Consolidated L2); Crypto and Event Contracts need no extra subscription. `MEASURED` ([Webull API FAQ](https://developer.webull.com/apis/docs/faq/), [Market Data Overview](https://developer.webull.com/apis/docs/market-data-api/overview/)).
- Margin rates, wires, inactivity: Margin interest rates, wire fees, and inactivity fees are not printed on the main Pricing page (`UNKNOWN`). Outgoing ACATS stock transfer = $75 (charged by Apex); incoming transfer = $0. `MEASURED` ([Webull Pricing](https://www.webull.com/pricing)).

### 4.5 Execution Quality Signals
- PFOF: Yes; Webull lists PFOF as a revenue stream on its Pricing page, and FINRA's Nov 2026 AWC notes Webull routed non-directed orders to market makers and exchanges paying PFOF. `MEASURED` ([Webull Pricing](https://www.webull.com/pricing), [FINRA AWC](https://www.finra.org/sites/default/files/2026-11/Webull-Financial-LLC-AWC-110426.pdf)).
- Routing choice: Direct Routing available for $0.0040/share. `MEASURED` ([Webull Pricing](https://www.webull.com/pricing)).
- Outages 2025-2026: None confirmed on primary status pages. `UNKNOWN`.

### 4.6 Safety
- SIPC & Excess SIPC: Webull Financial LLC is a SIPC member ($500,000, $250,000 cash). Omnibus accounts cleared through Apex carry excess SIPC up to $100M aggregate ($1.9M cash/customer); fully disclosed accounts carry Apex excess up to $150M aggregate ($37.5M securities, $900k cash/customer). `MEASURED` ([Webull Pricing](https://www.webull.com/pricing)).
- Enforcement 2024-2026: On **November 4, 2026**, FINRA censured Webull Financial LLC and fined it **$4,200,000** for AML program failures (2020-2023), Identity Theft Prevention Program failures (2020-2023), and failing to conduct reasonable best-execution reviews and supervision from Feb 2020 through at least Oct 2025 ("Webull failed to develop and implement a reasonably designed anti-money laundering program"). `MEASURED` ([FINRA AWC 110426](https://www.finra.org/sites/default/files/2026-11/Webull-Financial-LLC-AWC-110426.pdf)).

### 4.7 Sign-Up
- Open a Webull US brokerage account, go to Developer Console -> API Keys -> Apply for API Service. Firm-stated review time: "expected to take 1 to 2 business days at the earliest." Sandbox (`paperTrade`) is auto-approved in minutes. `MEASURED` ([Individual Application API](https://developer.webull.com/apis/docs/authentication/IndividualApplicationAPI/)).

---

## 5. TradeStation (Trading API)

### 5.1 Eligibility
- US retail individual: Yes, available to "individual traders, large corporations, and everything in between." `MEASURED` ([TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api), published 2025-09-22).
- Idaho residency: US equities, options, and futures nationwide. Spot crypto is not part of the TradeStation Securities brokerage API. `MEASURED` ([TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api)).
- Account types: Cash, Margin, Futures, and DVP accounts supported in API. `MEASURED` ([API Specification](https://api.tradestation.com/docs/specification/)).
- Minimum deposit: $0 cash account; $2,000 minimum for margin and short stock. `MEASURED` ([TradeStation Pricing](https://www.tradestation.com/pricing/), published 2025-11-11).
- Minimum for API: **$10,000 minimum funding balance** required to obtain a personal Trading API key ("Fund the account with a minimum balance of $10,000"). `MEASURED` ([TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api)).

### 5.2 API
- Official retail trading API: Yes, REST v3 (`https://api.tradestation.com/v3`) and HTTP streaming for equities, options, and futures (plus FIX for institutional). `MEASURED` ([TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api), [API Docs](https://api.tradestation.com/docs/)).
- Official Python SDK / OpenAPI: OpenAPI spec is published online ([Specification](https://api.tradestation.com/docs/specification/)); supports Python, C#, C++, Ruby, PHP via standard HTTP (no single official Python SDK package mandated). `MEASURED` ([TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api)).
- Sandbox / paper trading: Simulated environment (`sim.api.tradestation.com`) exists and is referenced in API docs ("build in a simulated environment"), though the individual marketing page highlights sandbox primarily for fintech/independent developers. `MEASURED` ([Getting Started](https://www.tradestation.com/insights/getting-started-with-a-trading-platform-api/), [TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api)).
- Order types: Market, limit, stop, stop-limit, bracket, OCO, OSO, multi-leg options, plus intelligent and direct routing. `MEASURED` ([TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api)).
- Fractional shares / extended hours / short selling: Short selling requires $2,000 margin minimum (`MEASURED`, [Pricing](https://www.tradestation.com/pricing/)); extended-hours routing supported (`MEASURED`, [Rule 606/607](https://www.tradestation.com/important-information/sec-rule-606-report-rule-607-disclosure/)). Fractional shares via API not documented (`UNKNOWN`).
- Rate limits: Rolling windows per user/API key: Accounts/Balances/Positions/Order Details = 320 per 5 min; Quote Snapshot / Quote Change / Barchart / TickBar Streams = 500 per 5 min; MarketDepth Stream = 30 per 1 min (10 concurrent); Order/Positions Streams = 40 concurrent; Other Option Endpoints = 90 per 1 min. Returns HTTP `429` with `X-RateLimit-*` and `X-Concurrency-*` headers. `MEASURED` ([Rate Limiting Overview](https://api.tradestation.com/docs/fundamentals/rate-limiting/rate-limiting-overview/)).
- Idempotency / client order ID: Not verified on the pages opened today. `UNKNOWN`.
- Auth, scopes & token expiry: OAuth 2.0 (Auth0) Authorization Code + PKCE with granular scopes (`MarketData`, `ReadAccount`, `Trade`, `offline_access`). Access tokens expire in **20 minutes** (`expires_in: 1200`), renewable via refresh token (`offline_access`). Refresh token expiration length was not printed on the auth-code page. `MEASURED` ([Auth Code Flow](https://api.tradestation.com/docs/fundamentals/authentication/auth-code/), updated 2026-11-20) / `UNKNOWN` for refresh token lifetime.

### 5.3 Terms on Automation
- Built specifically for algorithmic and automated execution ("charting, research, backtesting, and automated execution"). `MEASURED` ([TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api)).
- AI agent-specific clauses and order-to-fill ratio limits not found on public pages. `UNKNOWN`.

### 5.4 Costs
- Commissions: $0 US stocks/ETFs (intelligent routing); Direct Routing = $0.0048/share (0-100k sh/mo) + $0.003/share clearing; sub-dollar/OTC = $0.005/share. Single-leg options tiered $0.80 down to $0/contract; index options $1.00-$0.60; futures $1.75-$0.50/side (micros $0.50-$0.25). `MEASURED` ([TradeStation Pricing](https://www.tradestation.com/pricing/), published 2025-11-11).
- API fees: "with no subscription cost" / "TradeStation does not charge for access to the Fintech API." `MEASURED` ([TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api), [Developer Portal](https://developer.tradestation.com/)).
- Inactivity fee: "$10 per month (FREE if account meets minimum activity)." `MEASURED` ([TradeStation Pricing](https://www.tradestation.com/pricing/)).
- Margin rates: <$50k = 12.00%; $50k-$499,999 = 11.00%; $500k-$1,999,999 = 6.50%; $2M+ = 4.50%. `MEASURED` ([TradeStation Pricing](https://www.tradestation.com/pricing/)).
- Wire / ACAT fees: Not printed on the summary pricing page fetched. `UNKNOWN`.

### 5.5 Execution Quality Signals
- PFOF & routing: Accepts rebates/PFOF ("TradeStation receives rebates from market venues to which orders are routed"), states routing is not based on rebate size, and supports direct exchange routing (member of NYSE, Nasdaq, Arca, IEX, Cboe exchanges). Reports 27 ms average equity market order execution. `MEASURED` ([Rule 606/607](https://www.tradestation.com/important-information/sec-rule-606-report-rule-607-disclosure/), [Developer Portal](https://developer.tradestation.com/)).
- Rule 606: Quarterly PDF and XML reports published through Q2 2026. `MEASURED` ([Rule 606/607](https://www.tradestation.com/important-information/sec-rule-606-report-rule-607-disclosure/)).
- Outages 2025-2026: None confirmed on primary status pages. `UNKNOWN`.

### 5.6 Safety
- Regulators & clearing: TradeStation Securities, Inc. is self-clearing (with Wedbush for select non-member futures exchanges), SEC-registered broker-dealer, CFTC-registered FCM, member FINRA, NFA, SIPC, and major US equity/futures exchanges. `MEASURED` ([Rule 606/607](https://www.tradestation.com/important-information/sec-rule-606-report-rule-607-disclosure/)).
- SIPC: Up to $500,000 ($250,000 cash). Excess SIPC not stated on the Rule 606 page. `MEASURED` ([Rule 606/607](https://www.tradestation.com/important-information/sec-rule-606-report-rule-607-disclosure/)).
- Enforcement 2024-2026: On **March 17, 2026**, OFAC fined TradeStation Securities **$1,110,661** for 481 apparent sanctions violations (trades via mobile app for users in Iran, Syria, and Crimea in 2021-2022). `MEASURED` ([OFAC Release](https://ofac.treasury.gov/media/935351/download?inline)).

### 5.7 Sign-Up
- Open a TradeStation account (promo code `WAPIAFSG`), fund with at least **$10,000**, and TradeStation sends a unique API key (existing account holders email `ClientExperience@tradeStation.com`). Issuing an API key requires internal review and onboarding; no exact day count stated. `MEASURED` ([TradeStation Trading API](https://www.tradestation.com/platforms-and-tools/trading-api), [Brokerage Trading API](https://developer.tradestation.com/trading-api/)).

---

## 6. E*TRADE from Morgan Stanley (E*TRADE API)

### 6.1 Eligibility
- US retail individual: Yes, an E*TRADE brokerage account is required; an individual consumer key only works with its original user. `MEASURED` ([Developer Guides](https://developer.etrade.com/getting-started/developer-guides), no date printed).
- Idaho residency: US brokerage nationwide. No spot crypto trading via API. `MEASURED`.
- Minimum deposit / API minimum: $0 brokerage minimum; no separate API balance minimum stated on the Developer Guides page. `MEASURED` ([Pricing and Rates](https://us.etrade.com/what-we-offer/pricing-and-rates), [Developer Guides](https://developer.etrade.com/getting-started/developer-guides)).

### 6.2 API
- Official retail trading API: Yes, legacy REST API for stocks, ETFs, options, and mutual funds. `MEASURED` ([Developer Guides](https://developer.etrade.com/getting-started/developer-guides)).
- Auth & token expiry (major blocker): Uses legacy **OAuth 1.0a with HMAC-SHA1 only**. Access tokens go inactive after **2 hours** of no API calls (renewable via Renew Access Token) and **hard-expire daily at midnight US Eastern time**, requiring a manual browser OAuth login every trading day. `MEASURED` ([Developer Guides](https://developer.etrade.com/getting-started/developer-guides)).
- Sandbox / paper trading: **Not real paper trading.** Sandbox (`apisb.etrade.com`) returns static stored sample data only (e.g., querying GOOG or MSFT returns AAPL/ORCL/CSCO). `MEASURED` ([Developer Guides](https://developer.etrade.com/getting-started/developer-guides)).
- Protocols, SDK, rate limits, idempotency, fractional shares: REST only (no streaming API); no modern official Python SDK on guide; rate limits and idempotency not specified on Developer Guides page. `UNKNOWN`.

### 6.3 Terms on Automation
- Explicitly strips customer protection guarantee for API usage: "The E*TRADE Customer Protection Guarantee does not apply." `MEASURED` ([Developer Guides](https://developer.etrade.com/getting-started/developer-guides)).
- Daily midnight manual OAuth expiry effectively prevents unattended 24/7 automated trading without fragile browser automation. `MEASURED` ([Developer Guides](https://developer.etrade.com/getting-started/developer-guides)).

### 6.4 Costs
- Commissions: $0 online US stocks/ETFs; OTC $6.95 ($4.95 at 30+ trades/qtr); options $0.65/contract ($0.50 at 30+/qtr); futures $1.50/side. `MEASURED` ([Pricing and Rates](https://us.etrade.com/what-we-offer/pricing-and-rates)).
- Margin rates (base rate 10.20%, effective 09/21/2026): <$10k = 12.70%; $10k-$25k = 12.45%; $25k-$50k = 12.20%; $50k-$100k = 11.70%; $100k-$250k = 11.20%; $250k-$500k = 10.70%. `MEASURED` ([Pricing and Rates](https://us.etrade.com/what-we-offer/pricing-and-rates)).
- Wires & transfers: Incoming wire $0, outgoing wire $25; full outgoing account transfer $75. `MEASURED` ([Pricing and Rates](https://us.etrade.com/what-we-offer/pricing-and-rates)).

### 6.5 Execution Quality Signals
- PFOF: Yes; Morgan Stanley Smith Barney LLC receives PFOF on Self-Directed E*TRADE NMS equity, ETF, option, and OTC orders. `MEASURED` ([Quarterly 606 Report](https://us.etrade.com/l/quarterly-order-routing-report)).
- Rule 606: Quarterly PDF and XML reports published through **Q3 2026**. `MEASURED` ([Quarterly 606 Report](https://us.etrade.com/l/quarterly-order-routing-report)).
- Outages 2025-2026: None confirmed on primary status pages. `UNKNOWN`.

### 6.6 Safety
- Regulators & SIPC: Accounts carried by **Morgan Stanley Smith Barney LLC** (SEC/FINRA/SIPC member, $500,000 SIPC including $250,000 cash). `MEASURED` ([Asset Protection](https://us.etrade.com/l/f/asset-protection)).
- Excess SIPC: Morgan Stanley supplemental policy with "$1 billion for securities and a $1.9 million per client limit for uninvested cash." `MEASURED` ([Asset Protection](https://us.etrade.com/l/f/asset-protection)).
- Enforcement 2024-2026: No E*TRADE-API-specific enforcement found in searches today. `UNKNOWN`.

### 6.7 Sign-Up
- Open an E*TRADE brokerage account, request a sandbox key, then request a production consumer key through E*TRADE Developer Support. No approval timeline stated. `MEASURED` ([Developer Guides](https://developer.etrade.com/getting-started/developer-guides)).

---

## 7. moomoo (Moomoo OpenAPI)

### 7.1 Eligibility
- US retail individual: Yes, requires a Moomoo Financial Inc. US brokerage account. `MEASURED` ([Moomoo OpenAPI Overview](https://open.moomoo.com/api/overview)).
- Idaho residency: US stocks/ETFs/options nationwide. For crypto via Moomoo Crypto Inc. (MCI): requires US resident 18+ with SSN; explicitly restricts Alaska, New York, Texas, Virginia, and Vermont (Idaho is NOT on that restricted list, though the page does not print a full positive list of supported states). `MEASURED` ([Moomoo US Crypto](https://invest.us.moomoo.com/crypto)).
- Account types: Cash and margin accounts; LLC/business API eligibility not verified. `UNKNOWN`.
- Minimum deposit / API minimum: $0 deposit minimum; no separate API balance minimum stated on OpenAPI Overview. `MEASURED` ([Moomoo OpenAPI Overview](https://open.moomoo.com/api/overview)).

### 7.2 API
- Official retail trading API: Yes, modern REST (`https://webapi.moomoo.com`) + WebSocket streaming for quotes (`wss://webapi-quote.moomoo.com/ws`) and trade push (`wss://webapi-trade.moomoo.com/ws`). Covers US Stocks/ETFs, Options, and Crypto on Moomoo US (US Futures and Index Options not live on Moomoo US API). `MEASURED` ([Moomoo OpenAPI Overview](https://open.moomoo.com/api/overview), [Getting Started](https://open.moomoo.com/api/overview/getting-started)).
- SDK / Language: Standard REST/HTTP callable from any language ("No dedicated SDK installation is required"). `MEASURED` ([Getting Started](https://open.moomoo.com/api/overview/getting-started)).
- Sandbox / paper trading: Full simulated/paper trading API for US Stocks, Options, and Futures (not Crypto). `MEASURED` ([Moomoo OpenAPI Overview](https://open.moomoo.com/api/overview)).
- Order types, fractional shares, extended hours, short selling: Standard stock/option/crypto orders and fractional shares exist on Moomoo US (`MEASURED`, [Fees](https://www.moomoo.com/us/support/topic4_66)); exact API support for fractional orders and short locates not individually verified (`UNKNOWN`).
- Rate limits: Entry limit of **100 requests/minute per IP** each for Quote, Trading, Crypto, and Simulated Trading ("each allow at most 100 requests per minute from the same IP"), plus separate business quote/history quotas returning HTTP `429` or business codes `-11`, `-12`, `-13`. `MEASURED` ([Rate Limit](https://open.moomoo.com/api/overview/rate-limit)).
- Idempotency / client order ID: Not verified on the overview pages fetched; docs warn not to blindly retry order-placement writes. `MEASURED` ([Rate Limit](https://open.moomoo.com/api/overview/rate-limit)) / `UNKNOWN` for client order ID.
- Auth, scopes & token expiry: Supports two methods: (1) **OAuth 2.1 + PKCE** with granular scopes (`quote:read`, `quote:write`, `trade:read`, `trade:write`), 2-hour access token, 14-day default refresh token (configurable 3 hours to 30 days; non-rotating); or (2) **Traditional API Key** (Ed25519 or RSA-SHA256 request signing via `X-Api-Key`, `X-Timestamp`, `X-Nonce`) designed for server-side systems and scheduled jobs with no short browser re-login cycle. `MEASURED` ([Getting Started](https://open.moomoo.com/api/overview/getting-started)).

### 7.3 Terms on Automation
- Server-side automated systems and scheduled jobs are explicitly supported via Traditional API Key signing. `MEASURED` ([Getting Started](https://open.moomoo.com/api/overview/getting-started)).
- **Non-retail reclassification risk**: Moomoo US's fee schedule warns that if upstream partners classify trading activity as "non-retail" (e.g., high-frequency/professional patterns), commissions switch from $0 to **$0.0049/share (min $0.99)** for stocks and **$0.65/contract** for options. `MEASURED` ([Moomoo US Fees](https://www.moomoo.com/us/support/topic4_66), updated Oct 1, 2026 EST).

### 7.4 Costs
- Commissions: $0 US stocks, ETFs, ADRs, REITs, fractional shares, and stock/ETF options; $0.50/contract index options. (See non-retail reclassification warning above.) `MEASURED` ([Moomoo US Fees](https://www.moomoo.com/us/support/topic4_66), updated Oct 1, 2026 EST).
- Regulatory fees: SEC $0.0000206 x amount (min $0.01); FINRA TAF $0.00; CAT $0.000003/share; ORF $0.0122/contract; OCC $0.025/contract. `MEASURED` ([Moomoo US Fees](https://www.moomoo.com/us/support/topic4_66)).
- Crypto fees: $0 commission + **0.49% transaction fee** via Moomoo Crypto Inc. `MEASURED` ([Moomoo US Fees](https://www.moomoo.com/us/support/topic4_66)).
- Margin rate: Flat **6.8% p.a.** `MEASURED` ([Moomoo US Fees](https://www.moomoo.com/us/support/topic4_66)).
- Wires & transfers: Incoming wire $0; outgoing domestic wire $20; outgoing international wire $25; outgoing ACATS $100. `MEASURED` ([Moomoo US Fees](https://www.moomoo.com/us/support/topic4_66)).

### 7.5 Execution Quality Signals
- PFOF: Moomoo Financial Inc. states it does not receive PFOF directly, but its affiliated clearing firm **Futu Clearing Inc.** routes orders to venues such as Citadel Securities and Virtu Americas and receives PFOF/rebates. `MEASURED` ([Customer Agreement](https://foss-us-sec.moomoo.com/customer_file_service/prod/disclosure_1717572128614_16222017.pdf), [Rule 606 Report](https://static.moomoo.com/upload/606/3rd%20Quarter,%202023-2bedcd281346c17cdebca63b9139a0cc.pdf)).
- Outages 2025-2026: None confirmed on primary status pages. `UNKNOWN`.

### 7.6 Safety
- Regulators & SIPC: Moomoo Financial Inc. is SEC-registered, FINRA/SIPC member; clears through affiliated Futu Clearing Inc. `MEASURED` ([Moomoo US Disclosures](https://www.moomoo.com/news/notice/303742107/robinhood-8-k-nms-stocks-and-options-order-routing-public)). Excess SIPC limits not verified on pages opened today (`UNKNOWN`).
- Crypto custody: Moomoo Crypto Inc. (MCI), FinCEN-registered MSB, not a broker-dealer; "Cryptocurrency assets held with MCI are not FDIC insured or SIPC protected." `MEASURED` ([Moomoo US Crypto](https://invest.us.moomoo.com/crypto)).
- Enforcement 2024-2026: None confirmed on primary regulator pages today. `UNKNOWN`.

### 7.7 Sign-Up
- Open a Moomoo US brokerage account, then create an AppKey in `https://open.moomoo.com/dashboard` (under AppKey Management) or register an OAuth 2.1 client. No manual review delay stated. `MEASURED` ([Getting Started](https://open.moomoo.com/api/overview/getting-started)).

---

## 8. TradeZero America (Low-Minimum Direct-Access Broker with Retail API)

### 8.1 Eligibility
- US retail individual: Yes. "The API Trading program is for self-directed traders building personal trading tools" on their own TradeZero account. `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs), no date printed).
- Idaho residency: US broker-dealer nationwide for stocks, options, and futures; no spot crypto. `MEASURED` ([TradeZero America](https://tradezero.com/en-us), published 2026-11-06).
- Account types: Cash and Margin accounts; API trading is included even on the Cash Account. `MEASURED` ([TradeZero America](https://tradezero.com/en-us)).
- Minimum deposit & API minimum: **$500** minimum initial deposit for Cash Account (includes API trading); **$2,000** minimum balance for Margin and short selling. `MEASURED` ([TradeZero America](https://tradezero.com/en-us)).

### 8.2 API
- Official retail trading API: Yes, execution-first REST + WebSocket API for equities, options, account/positions, and programmatic **short locates**. Also offers hosted **TradeZero MCP** (OAuth 2.0) for Claude, Claude Code, Perplexity, Grok, Cursor, VS Code, and ChatGPT Business/Enterprise. `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).
- Market data gap: **No market data in the Trading API or MCP** ("Market data... is outside the public Trading API surface, so the hosted MCP server does not return prices"). You must bring an external market-data feed. `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).
- Sandbox / paper trading: Yes, paper trading uses the exact same host and JSON schemas as live (with simulated quote ticks for P&L WebSockets). Short locates are live-only. `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).
- Order types: `Market`, `Limit`, `Stop`, `StopLimit`; `Day`, `Day_Plus`, `GTC_Plus`. No modify endpoint: must cancel, wait for `Canceled`, and submit a new order with a new `clientOrderId`. `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).
- Fractional shares: **Not supported** ("`orderQuantity` must be a whole integer"). `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).
- Extended hours: 7:00 AM to 8:00 PM ET (`Day_Plus` / `GTC_Plus` with `Limit` or `StopLimit`). `MEASURED` ([TradeZero America](https://tradezero.com/en-us), [TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).
- Short selling & locates: Built-in live short locate API (`/quote` valid 30 seconds, `/accept`, Reg SHO Pre-Borrow vs `.SU` Single Use offers). `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).
- Rate limits: Not stated on the Trading API FAQs page. `UNKNOWN`.
- Idempotency / client order ID: Yes; `clientOrderId` is permanently consumed once accepted and reuse returns `R114`. `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).
- Auth & key expiry: Portal API keys have **"No automatic expiry"** (valid until explicitly regenerated or disabled; all lifecycle events logged and emailed). Uses `2TZ`-prefixed account number. `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).

### 8.3 Terms on Automation (Important Restriction)
- Explicitly restricts unattended automation: **"Fully unattended systems that trade without your ongoing control are outside the scope"** of the current API Trading agreement. Designed for personal dashboards, execution assistants, and human-monitored integrations. `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).

### 8.4 Costs
- Commissions: $0 on qualifying NYSE, AMEX, and NASDAQ stocks above $1 (7 AM to 8 PM ET, all order types); options $0 commission + $0.42/contract fee (capped at $20/order); futures $0.39/side micros, $1.29/side E-Mini/Standard. `MEASURED` ([TradeZero America](https://tradezero.com/en-us)).
- Margin rates, short locate pricing, wire/ACAT/inactivity fees: Not printed on homepage or API FAQs. `UNKNOWN`.

### 8.5 Execution Quality Signals
- Execution-first direct-access broker; live routed order confirmation typically settles within ~50 ms. `MEASURED` ([TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).
- PFOF / Rule 606 details and 2025-2026 outages not fetched today. `UNKNOWN`.

### 8.6 Safety
- Regulators & SIPC: TradeZero America, Inc. is SEC-registered and a member of FINRA and SIPC. `MEASURED` ([TradeZero America](https://tradezero.com/en-us)).
- Excess SIPC and 2024-2026 enforcement: Not verified today. `UNKNOWN`.

### 8.7 Sign-Up
- Open a TradeZero America account (can test platforms before funding), fund with at least $500 (cash) or $2,000 (margin/shorting), and generate API keys in the portal. `MEASURED` ([TradeZero America](https://tradezero.com/en-us), [TradeZero API FAQs](https://developer.tradezero.com/docs/documentation/trading-api-faqs)).

---

## Comparison Table

| Broker | Min for API | Auth / Expiry | Paper API | Stocks / Crypto API | Stock Comm. / Routing | Margin (<$50k) | Automation Terms | Key Blocker or Strength |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Public.com** | $0 | Secret key -> Bearer token (no browser loop) | No (preflight only) | Stocks, ETFs, Options, Bonds, Crypto (0.60%-0.10%) | $0 wholesale; $0.003/sh Smart or Lit | 5.15% | Allowed (personal + Business + MCP) | Best all-around modern API + low margin + optional non-PFOF routing; no paper API |
| **Webull** | $0 | App Key + Secret (no auto expiry) | Yes (`paperTrade`, 15m data delay) | Stocks, ETFs, Options, Futures, Crypto (1% spread) | $0; $0.004/sh direct; $0.005/sh algo | `UNKNOWN` | Allowed (OpenAPI + CLI + agent skills) | Strong full-stack API (REST+MQTT+gRPC) + paper; paid non-display data; $4.2M FINRA fine Nov 2026 |
| **moomoo** | $0 | Ed25519/RSA API Key or OAuth 2.1 (14-30d refresh) | Yes (stocks/options; not crypto) | Stocks, ETFs, Options, Crypto (0.49%) | $0 (or $0.0049/sh if non-retail) | 6.80% | Allowed (server-side API key) | Clean REST+WS + paper + crypto; non-retail fee reclassification risk; 100 req/min/IP cap |
| **TradeStation** | $10,000 | OAuth 2.0 (20m access + refresh token) | Yes (`sim.api`) | Stocks, ETFs, Options, Futures (no crypto) | $0 smart; $0.0048+$0.003/sh direct | 12.00% | Built for algo automation | Mature DMA + streaming; $10k API min, high margin rate, $10/mo inactivity if low activity |
| **TradeZero America** | $500 cash / $2,000 margin | API Key (no auto expiry) + MCP | Yes (same host; locates live-only) | Stocks, Options, Short Locates (no crypto) | $0 qualifying stocks >$1 | `UNKNOWN` | **No fully unattended bots** | Lowest-min DMA + short locates API; **no market data** and bans unattended automation |
| **Charles Schwab** | $0 | OAuth 2.0 (**7-day hard refresh expiry**) | No (paperMoney is UI only) | Stocks, ETFs, Options (no crypto) | $0 online/API | 11.575%-12.075% | Personal self-directed | Strong brand/safety, but 7-day manual OAuth re-login + no paper API + no fractional API |
| **Robinhood** | $0 | Hosted MCP OAuth only (no stock REST API) | No | MCP only (isolated Agentic account) | $0 | 5.25% | Explicitly built for AI agents | Great for interactive AI agent MCP; **not** a programmatic REST/streaming engine |
| **E*TRADE** | $0 | OAuth 1.0a (**daily midnight ET expiry**) | No (static mock data) | Stocks, ETFs, Options (no crypto) | $0 | 12.20%-12.70% | Customer Protection Guarantee void | Obsolete OAuth 1.0a daily re-login + fake sandbox; unusable for unattended bots |
| **Fidelity** | N/A | None | No | None | N/A | N/A | N/A | No retail trading API |
| **Lightspeed / CenterPoint / Cobra** | $30k / $50k / $10k | API / FIX | Varies | Equities/Options | Per-share DMA | Varies | Allowed | High account minimums ($10k-$50k) |

---

## Real Options vs. Not Real Options for an Automated System

### Real Options
1. **Public.com**: Best mainstream US retail API for an unattended rule-based system with AI-agent support. Zero minimum, no manual OAuth re-login loop, UUID `orderId` idempotency, bracket/OCO/OTO orders, optional non-PFOF routing ($0.003/sh), 5.15% margin, tiered crypto API (0.60% down to 0.10%), Business/LLC API support, and hosted MCP. Main drawback: no paper-trading sandbox (preflight only) and no WebSocket streaming.
2. **Webull OpenAPI**: Best mainstream option if you need both a paper-trading sandbox and real-time streaming (MQTT quotes + gRPC order events) at a $0 minimum. High order rate limits (600/min), `client_order_id` idempotency, non-expiring App Key/Secret, and official Python SDK/CLI/agent skills. Main drawbacks: requires paid Non-Display market data subscriptions, 1% crypto spread is expensive, and FINRA issued a $4.2M AML/best-execution fine in November 2026.
3. **moomoo OpenAPI**: Strong runner-up with $0 minimum, REST + WebSocket streaming, Ed25519/RSA server-side API keys (no weekly re-login), paper trading for US stocks/options, 6.8% margin, and 0.49% crypto API fee. Main drawbacks: 100 req/min/IP ceiling and risk of being reclassified to $0.0049/share non-retail fees.
4. **TradeStation**: Real option for serious equities/options/futures automation if you are willing to fund **$10,000** for API access and pay higher margin rates (12% under $50k). Mature self-clearing DMA, streaming, and OAuth 2.0 refresh tokens. No spot crypto.

### Not Real Options (and Why)
1. **Fidelity**: No public retail trading API exists.
2. **E*TRADE**: Legacy OAuth 1.0a expires every night at midnight ET (requiring daily manual browser login), sandbox returns static fake data, and API use voids the Customer Protection Guarantee.
3. **Charles Schwab**: Hard 7-day OAuth refresh token expiry requires manual weekly browser re-authentication, no paper trading API (thinkorswim paperMoney is UI-only), no fractional shares via API, and 11.575%-12.075% margin under $50k.
4. **Robinhood**: No public retail REST/streaming API for stocks; the May 2026 Trading MCP server (`agent.robinhood.com/mcp/trading`) is built for AI assistant tool calls into an isolated Agentic account, not a deterministic rule-based execution engine.
5. **TradeZero America**: Impressive $500/$2,000 minimum DMA + short-locate API, but explicitly places **"fully unattended systems that trade without your ongoing control" outside the scope** of its API agreement and provides no market data through the API.
6. **Lightspeed ($30k), CenterPoint ($50k), Cobra ($10k)**: High minimums exclude them as low-minimum retail options.
