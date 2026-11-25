> Raw researcher report, kept as evidence. Some figures here were corrected after a fresh check. The corrected version is `docs/research/09_brokers_and_venues.md`, which wins where the two differ. Known corrections: the Coinbase Advanced entry fee is 0.50% maker and 0.90% taker, not 0.40% and 0.60%; an Alpaca duplicate order id returns HTTP 422, not 409.

# Account setup, minimums, rules and taxes for an automated retail trading setup (US, Idaho)

Researcher: account_setup_rules_researcher. All pages opened on 2026-11-24 unless noted.
Tags: MEASURED = read on a primary page today. STATED = third party or claim not confirmed on a primary page. UNKNOWN = not found.

## Unfinished or not verified (read this first)

- Coinbase Advanced fee table: the primary fee page (coinbase.com/advanced-fees) did not load, and the help page says tiers are only shown after sign-in. Third-party pages disagree with each other. UNKNOWN on a primary page. See section 2.
- Coinbase Advanced minimum order sizes per pair: the "Market Information" page was not opened. UNKNOWN.
- Alpaca firm-stated approval time for a live account: not found on a primary page. Only a 2020-era forum reply from staff ("Generally, live accounts take 24 hours to be reviewed"). STATED.
- IBKR firm-stated approval time: not found on a primary page. Third-party reviews say 1 to 3 business days. STATED.
- Kraken API key issuance steps for individuals were read only from the API docs summary (permissions table). Key expiry rules not checked.
- Alpaca brokerage fee schedule PDF did not load, so Alpaca's exact pass-through rate table is not confirmed today.
- Spread costs: no primary page gives a number for typical spreads. The arithmetic below uses fees only and shows spreads as a formula.
- Selling signals: I found the statutory definitions but no primary page that applies them to a "signal service". This needs a securities lawyer.

## Top findings

1. The $25,000 pattern day trader rule is gone at the FINRA level. FINRA replaced it with intraday margin standards effective June 4, 2026. Brokers may phase in until October 20, 2027. MEASURED.
2. Alpaca has already switched. IBKR says some existing accounts may still be under PDT rules during the phase-in, and one older IBKR FAQ still states the $25,000 rule. MEASURED (conflict reported in section 1).
3. $2,000 equity is still the floor for using leverage or short selling. Below that, you trade only with your own cash. MEASURED.
4. Crypto wash sales: still not covered by law as of today. H.R. 10357 (Digital Asset Tax Certainty Act) passed committee 38-5 on 2026-09-16 but has not passed the House. MEASURED.
5. Form 1099-DA: brokers must report gross proceeds for all digital asset sales after 2025, and basis for assets bought after 2025 in the same custodial account. MEASURED.
6. The Section 475(f) mark-to-market election for tax year 2027 must be made by the unextended due date of the 2026 return (April 15, 2027 for a calendar-year individual). The 2026 deadline has passed. MEASURED (rule) and STATED (the April 15 dates come from tax-firm pages).

---

## 1. Day trading rules today

### 1.1 FINRA Rule 4210 change (the end of the PDT rule)

| Item | What the source says | Tag | Source |
|---|---|---|---|
| SEC approval | Release 34-105226, April 14, 2026: "Order Granting Accelerated Approval of a Proposed Rule Change, as Modified by Amendment No. 1, to Amend FINRA Rule 4210 (Margin Requirements) to Replace the Day Trading Margin Provisions with Intraday Margin..." | MEASURED | https://www.sec.gov/rule-release/34-105226 |
| What was removed | "FINRA has adopted new intraday margin standards to replace in their entirety the outdated day trading margin requirements, including the day trade count requirements for designating a customer as a 'pattern day trader' and the $25,000 pattern day trader minimum equity requirement." | MEASURED | https://www.finra.org/rules-guidance/notices/26-10 (Notice dated April 20, 2026) |
| Effective date and phase-in | Effective June 4, 2026. "Phase-in Period: Ends October 20, 2027." Firms that need more time may phase in over 18 months. | MEASURED | same |
| Which accounts | Each customer margin account "other than a good faith account or portfolio margin account". Cash accounts are not part of this rule. | MEASURED | same |
| When tested | On each day with an "IML-reducing transaction". Real-time monitoring is allowed but "not a requirement"; firms may make "a single calculation". | MEASURED | same |
| Key definition | "The term 'IML-reducing transaction' refers, broadly, to any transaction that reduces the amount that the customer could withdraw while still meeting the maintenance margin requirement (for example, the execution of a short sale or the purchase of a security other than to cover a short position would generally be IML-reducing transactions)." | MEASURED | same |
| How a deficit must be met | "the member must require such intraday margin deficit to be satisfied as promptly as possible." A deficit "remains outstanding until satisfied or until immediately after the close of business on the 15th business day after the date of the intraday margin deficit." | MEASURED | same |
| Penalty | "If a customer makes a practice of failing to satisfy intraday margin deficits as promptly as possible and fails to satisfy an intraday margin deficit by the close of business on the fifth business day after it occurs, the member must enforce written policies and procedures reasonably designed to prevent the customer from creating or increasing a short position or debit balance (other than by closing a short position) for 90 calendar days after such fifth business day or until the intraday margin deficit has been satisfied." Small deficits that do not exceed the lesser of 5% of equity or $1,000 do not count as "making a practice". | MEASURED | same |
| Investor summary | "There's no $25,000 minimum equity requirement for day trading." and "$2,000 is the minimum equity required to engage in leveraged trading (trading on margin)." and "You can trade in a margin account with less than $2,000 in equity, but you cannot use leverage". Maintenance margin of at least 25% of long margin-eligible equity value applies throughout the day. Page dated April 20, 2026. | MEASURED | https://www.finra.org/investors/insights/intraday-margin-requirements |

### 1.2 How brokers have implemented it

| Broker | What the broker says | Tag | Source |
|---|---|---|---|
| Alpaca | "We have officially lifted the Pattern Day Trader rule and replaced it with the new intraday margin framework in production for both Trading API users and Broker API partners." Removed: PDT designation, $25,000 minimum, "Day trade counting and buying power logic." "Intraday Buying Power replaces Day Trade Buying Power." "Pre-Trade Checks will reject orders that would put your account into a margin deficit". "For leverage-enabled accounts, the minimum equity requirement for 4x intraday buying power has been lowered from $25,000 to $2,000." Last updated June 4, 2026. | MEASURED | https://alpaca.markets/blog/finra-retires-the-pdt-rule-introducing-alpacas-new-intraday-margin-framework/ |
| Alpaca (FAQ) | "The previous '4-trade limit' has been eliminated. You may enter and exit positions as frequently as you choose, provided your account has sufficient equity to cover the intraday risk requirements set by your broker." and "individual firms may still maintain their own 'house' requirements". | MEASURED | https://docs.alpaca.markets/us/docs/intraday-margin-rule-for-non-leverage-margin-accounts |
| Alpaca (account type) | "All accounts are opened as margin accounts. Accounts with $2,000 or more equity will have access to margin trading and short selling." Accounts under $2,000 are "restricted to 1x buying power". Crypto cannot be margin collateral. | MEASURED | https://docs.alpaca.markets/us/docs/account-plans ; https://alpaca.markets/support/determine-margin-account |
| IBKR (rule-change FAQ) | "new margin accounts will generally not be subject to the pattern day trading (PDT) rules. However, depending on your account setup, your account may remain subject to the PDT rules during the implementation period specified by FINRA". "For accounts trading on margin and/or executing short sales, the minimum equity requirement is $2,000 to trade with leverage or execute short sales." | MEASURED | https://www.interactivebrokers.com/support/faq/articles/1460026643 |
| IBKR (older minimum-deposit FAQ) | Still says: "a minimum deposit of USD 25,000 ... is required by regulation. If you open a margin account with less than USD 25,000, you will be limited to 4 day trades in a rolling 5 day span." No date on page. | MEASURED, conflicts with the FAQ above | https://www.interactivebrokers.com/support/faq/content/minimum-deposit-open-account-interactive-32659392 |
| IBKR margin page | Still says: "Customers that these organizations classify as Pattern Day Traders are subject to special Day Trading Restrictions". Initial margin "26.25% * Stock Value (minimum of USD 2,000 or 100% of the purchase price, whichever is less)". | MEASURED | https://portal.interactivebrokers.com/en/trading/margin-stocks.php |

Plain reading: at IBKR, check the account's status after approval. The newer FAQ says new margin accounts are "generally" not under PDT, but IBKR's own pages still disagree.

### 1.3 Cash accounts, T+1, good faith and free-riding

| Item | Quote | Tag | Source |
|---|---|---|---|
| T+1 | SEC adopted rules "to shorten the standard settlement cycle for most broker-dealer transactions in securities from two business days after the trade date (T+2) to one (T+1)." "The compliance date for the final rules is May 28, 2024." | MEASURED | https://www.sec.gov/newsroom/press-releases/2023-29 |
| Cash account rule | Reg T lets a broker buy in a cash account if "There are 'sufficient funds' in the account; or" the broker accepts in good faith that the investor will "promptly make 'full cash payment' for the security before selling it". | MEASURED (page updated August 7, 2026) | https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/updated-9 |
| Free-riding | "If an investor buys and sells a security before paying for it, the investor is 'freeriding' which is not permitted under the Federal Reserve Board's Regulation T and may require the investor's broker to 'freeze' the investor's cash account for 90 days. During this 90-day period, an investor may still purchase securities with the cash account, but the investor must fully pay for any purchase on the date of the trade." | MEASURED | https://www.sec.gov/answers/freeride.htm |
| Good faith violation | Not defined on the SEC page. Broker definitions: "A GFV is issued when a position is opened using unsettled funds and then the position is subsequently closed before the funds used to make the opening trade have settled." (E*TRADE). Fidelity: "A good faith violation occurs when a security purchased in a customer's cash account is sold before being paid for with the settled funds in the account." | STATED (broker pages, not regulator) | https://us.etrade.com/knowledge/library/stocks/understanding-cash-account-violations ; https://www.fidelity.com/trading/faqs-trading-restrictions |

What this means for a small account that trades often (stocks):

- In a true cash account, a bot can only buy with settled cash. Sale proceeds settle the next business day (T+1). If the bot buys with today's sale proceeds and sells that new position the same day, that is the free-riding or good faith pattern described above.
- So a $1,000 cash account can turn over about $1,000 of purchases per day in settled cash, not more, unless it waits for settlement.
- In a margin account (even with less than $2,000 and no leverage), the T+1 wait is not the constraint. Alpaca says margin accounts "are often utilized to avoid the delays associated with T+1 settlement" (MEASURED, Alpaca FAQ above). Exactly how Alpaca treats unsettled proceeds in a sub-$2,000 margin account is not stated. UNKNOWN.
- Spot crypto is not under Reg T or Rule 4210. Alpaca: "Margin Trading for Crypto is not applicable." (MEASURED). Kraken: deposits "are available instantly for trading" (MEASURED, see 3.4). Coinbase: "Crypto purchased with cash that is on hold can be sold or traded on Coinbase." (MEASURED).

---

## 2. Minimums and the cost arithmetic

### 2.1 Account and order minimums

| Item | Value | Tag | Source |
|---|---|---|---|
| Alpaca individual account minimum | "There is no minimum deposit required to open an account." | MEASURED (page last updated March 18, 2026) | https://alpaca.markets/learn/live-trading-account-us-resident |
| Alpaca business (LLC) account minimum | "There is a $30,000 minimum deposit required for opening a business account at Alpaca." | MEASURED | https://docs.alpaca.markets/us/docs/account-plans |
| IBKR cash account | "There is no minimum required deposit to open a Cash Account at Interactive Brokers for IBLLC clients." | MEASURED | https://www.interactivebrokers.com/support/faq/content/minimum-deposit-open-account-interactive-32659392 |
| IBKR margin account | "minimum deposit requirement is USD 2,000" | MEASURED | same |
| IBKR individual / org account minimum (pricing page) | "Account Minimums USD 0.00", "Inactivity Fees USD 0.00" for IBKR Pro and Lite | MEASURED | https://us1.interactivebrokers.com/en/accounts/required-minimums.php |
| IBKR old registration help text | "Individual accounts require 10,000 USD or the non-USD equivalent to open an account." This conflicts with the two rows above and looks out of date. | MEASURED, conflict | https://gdcdyn.interactivebrokers.com/Universal/servlet/Registration_v3.formHelp?s=p1101 |
| Margin floor (all brokers) | $2,000 equity for leverage or short sales | MEASURED | FINRA investor page, section 1.1 |
| Alpaca fractional stock minimum | "we enforce a minimum 1 USD notional amount for Buy entry orders." Fractional orders work for market, limit, stop and stop limit with time_in_force day. | MEASURED (FAQ dated April 2026) | https://alpaca.markets/support/can-we-submit-orders-smaller-than-1-usd-in-notional-value ; https://docs.alpaca.markets/us/docs/fractional-trading |
| Alpaca crypto minimum | Two Alpaca pages disagree. API docs: "For USD pairs, the minimum order size calculation is: 10/USD asset price" (about $10). Support FAQ: "calculated dynamically based on a $1 USD notional equivalent minimum". Treat the API docs value ($10) as the safer design input and read min_order_size from the asset endpoint at run time. | MEASURED, conflict | https://docs.alpaca.markets/us/docs/crypto-trading-1 ; https://alpaca.markets/support/alpaca-crypto-coin-pair-faq |
| Kraken crypto minimum | Two tests: a base-currency volume minimum per asset ("The minimum order size goes by base currency"), and a quote-currency cost minimum of "US Dollar 0.5 USD". API field: ordermin in /0/public/AssetPairs. | MEASURED | https://support.kraken.com/articles/360001389303-overview-of-cryptocurrency-minimums ; https://support.kraken.com/articles/12425041458708-cost-minimum-for-trading ; https://docs.kraken.com/exchange/guides/general/errors.md |
| Coinbase Advanced minimum | Help page example error: "Minimum order is 0.0001 BTC" or "Minimum order size is $5.00." Per-pair minimums are on a Market Information page not opened today. | STATED (example only; page dated 2025-02-14) | https://help.coinbase.com/en/coinbase/trading-and-funding/advanced-trade/error-messages |

### 2.2 Sourced fee inputs

| Fee | Rate | Tag | Source |
|---|---|---|---|
| Alpaca stock commission | "Alpaca stock trading remains commission-free" | MEASURED | https://docs.alpaca.markets/us/docs/crypto-fees |
| SEC Section 31 fee (sells only) | $20.60 per million dollars of sales from April 4, 2026 | MEASURED | https://www.sec.gov/rules-regulations/fee-rate-advisories/2026-2 |
| Alpaca SEC fee rounding | "this fee is rounded up to the nearest penny" | MEASURED | https://alpaca.markets/support/regulatory-fees |
| FINRA TAF (sells only) | $0.00 for trades October 1 to December 31, 2026 (fee holiday). The bracketed pre-holiday 2026 rate in FINRA's filing is $0.000195 per share, max $9.79 per trade. FINRA's rulebook page returned a different figure ($0.000166, max $8.30), possibly an older cached version. | MEASURED, conflict noted | https://www.finra.org/rules-guidance/guidance/faqs/finra-billingcollections ; https://www.sec.gov/file/34-106409-ex5 ; https://www.finra.org/rules-guidance/rulebooks/corporate-organization/section-1-member-regulatory-fees |
| CAT fee | USD 0.000003 per share (as listed by IBKR) | MEASURED | https://www.interactivebrokers.com/en/pricing/commissions-stocks.php |
| IBKR Pro Fixed | USD 0.005 per share, minimum USD 1.00 per order, maximum 1% of trade value | MEASURED | same |
| IBKR Pro Tiered | USD 0.0035 per share up to 300,000 shares a month, minimum USD 0.35 per order. Exchange and clearing fees are added on Tiered; those were not read today. | MEASURED (rate), UNKNOWN (add-on fees) | same |
| IBKR Lite | USD 0.00 for US exchange-listed stocks and ETFs, with exceptions (for example overnight trading and some outside-RTH orders above a volume threshold use Fixed pricing) | MEASURED | same |
| Alpaca crypto | Tier 1 (0 to $100,000 30-day volume): maker 0.15%, taker 0.25% | MEASURED | https://docs.alpaca.markets/us/docs/crypto-fees |
| Kraken Pro spot | Tier 1 ($0+): maker 0.40%, taker 0.80%. Tier 2 ($2.5K+ volume): 0.30% / 0.60%. Tier 3 ($10K+ volume or $20K+ assets on platform): 0.22% / 0.38%. Changed July 9, 2026: tier is "based on your Spot volume or Assets on Platform, whichever qualifies you for the best rate." An older Kraken Pro marketing page still says "Maker fees start at 0.25% and taker fees at 0.40%". | MEASURED, conflict noted | https://www.kraken.com/pro/fees ; https://support.kraken.com/articles/cross-platform-fee-tier-changes ; https://www.kraken.com/pro/tradingview |
| Kraken instant buy | "1% trading fee on instant and recurring trades" plus a spread | MEASURED | https://www.kraken.com/features/fee-schedule |
| Coinbase Advanced | Tier table not visible on a primary page today. Coinbase Exchange help page (a related product on the same order books) lists $0 to $10K: taker 60 bps, maker 40 bps. A third-party site says US entry rates changed on September 16, 2026 to 0.50% maker / 0.90% taker. Not confirmed. | UNKNOWN for Advanced; MEASURED for Exchange; STATED for the claimed change | https://help.coinbase.com/en/exchange/trading-and-funding/exchange-fees ; https://cryptoresearch.news/guides/coinbase-advanced-fees |
| Coinbase simple trade | Spread included, plus "a separate limit order execution fee equal to 1%" for simple limit orders, and "may also charge a 1.875% Coinbase fee (varies by payment method)." | MEASURED | https://help.coinbase.com/en/coinbase/trading-and-funding/pricing-and-fees/fees |

### 2.3 Arithmetic: when per-order fees stop dominating

These are calculations from the fee numbers above, not forecasts. Spreads are extra and not included. Spread cost per round trip is roughly (ask minus bid) divided by price, paid once per round trip when you buy at the ask and sell at the bid.

Stocks, IBKR Pro Fixed (minimum $1.00 per order, so $2.00 per round trip at small sizes):

| Order size | Commission per round trip | As % of order |
|---|---|---|
| $100 | $2.00 ($1.00 minimum per side; the 1% cap is also $1.00 here) | 2.0% |
| $500 | $2.00 | 0.40% |
| $1,000 | $2.00 | 0.20% |
| $2,000 | $2.00 | 0.10% |
| $10,000 (100 shares at $100: 100 x $0.005 = $0.50, so the $1.00 minimum applies) | $2.00 | 0.02% |

The $1.00 minimum stops being the main cost once the per-share charge exceeds it: 200 shares or more per order (200 x $0.005 = $1.00).

Same table on IBKR Pro Tiered (minimum $0.35, before exchange and clearing add-ons): $0.70 per round trip, so 0.70% on $100, 0.14% on $500, 0.07% on $1,000.

Stocks, Alpaca (commission $0, pass-through fees only, sells only for SEC fee):

| Sale size | SEC fee before rounding | After Alpaca rounds up to the penny | As % of sale |
|---|---|---|---|
| $10 | $0.000206 | $0.01 | 0.10% |
| $100 | $0.00206 | $0.01 | 0.01% |
| $1,000 | $0.0206 | $0.03 | 0.003% |

At Alpaca the penny rounding is the only fee effect that matters for tiny sells. TAF is $0 until December 31, 2026; at the pre-holiday rate of $0.000195 per share it adds about $0.01 per sale for most small orders after rounding (Alpaca rounds TAF up to the penny per trade, MEASURED on the Alpaca regulatory fees page).

Crypto: fees are a percentage, so account size alone does not shrink them. Trade frequency is what matters. Round trip = buy fee + sell fee.

| Venue and tier | Round trip, both taker | Round trip, both maker |
|---|---|---|
| Alpaca tier 1 | 0.25% + 0.25% = 0.50% | 0.15% + 0.15% = 0.30% |
| Kraken Pro tier 1 | 0.80% + 0.80% = 1.60% | 0.40% + 0.40% = 0.80% |
| Kraken Pro tier 3 (reachable with $20,000 held on Kraken) | 0.38% + 0.38% = 0.76% | 0.22% + 0.22% = 0.44% |

Yearly fee drag if the bot turns over the whole account once per day (one round trip per day, 365 days for crypto): Alpaca taker 0.50% x 365 = 182.5% of account value per year in fees. Kraken tier 1 taker 1.60% x 365 = 584%. At one round trip per week (52 per year): Alpaca taker 26%, Kraken tier 1 taker 83.2%. The strategy's average gross edge per round trip must exceed the round-trip fee just to break even.

Where account size does matter for crypto: Kraken (and, per Coinbase's help page, Coinbase Advanced via USDC balance) lets balances held on the platform qualify for a lower tier. On Kraken, $20,000 of assets on platform moves taker from 0.80% to 0.38%. MEASURED.

---

## 3. Sign-up process and firm-stated timelines (individual account)

### 3.1 Alpaca

| Step | Detail | Tag | Source |
|---|---|---|---|
| Paper first | "By signing up and activating MFA, you have only created a paper account." Up to "3 paper trading accounts and 1 live trading account." Paper needs no funding. | MEASURED | https://alpaca.markets/learn/live-trading-account-us-resident |
| Eligibility | "You must be a US tax resident, 18 years or older, and have a valid Social Security Number (SSN)." ITIN possible with manual review. | MEASURED | same |
| Steps | Account type, basic info and Tax ID, agree to customer and crypto agreements, employment, financial profile, disclosures (broker-dealer affiliation, public company insider, political exposure), KYC with "a live selfie". | MEASURED | same |
| Documents | "A valid, government-issued ID", personal details, proof of address "if requested". KYC "typically processed through Trulioo". | MEASURED | same |
| Approval time | Not stated on Alpaca's guide. Staff forum reply: "Generally, live accounts take 24 hours to be reviewed." | STATED | https://forum.alpaca.markets/t/account-taking-longer-than-usual-to-approve/3627 |
| Funding | "ACH linked bank account or wire transfer." | MEASURED | same guide |
| When tradable | "For ACH transfers, up to 3000 USD may be made available instantly ... All other transfer methods require the funds to be fully transferred and posted to your account before trading is permitted." An older Alpaca page says instant ACH applies "when depositing less than $1,000". | MEASURED, conflict | https://alpaca.markets/learn/fund-live-trading-account ; https://alpaca.markets/support/what-is-instant-ach-funding |
| Withdrawal hold | "Alpaca will generally hold ACH deposits for six business days before it can be withdrawn." | MEASURED | https://alpaca.markets/support/deposits-and-withdraws-faqs |
| API keys | Generated in the dashboard as a key ID and secret pair. "Paper and live trading use separate API domains and separate credentials": paper-api.alpaca.markets and api.alpaca.markets. | MEASURED | https://alpaca.markets/learn/api-key-security-best-practices-for-alpaca-builders |

### 3.2 Interactive Brokers

| Step | Detail | Tag | Source |
|---|---|---|---|
| What you need | SSN, employer name, address and phone, bank account numbers. "Interactive Brokers generally verifies US-resident applicants' names and addresses electronically"; extra documents only if that fails. | MEASURED | https://portal.interactivebrokers.com/en/general/what-you-need-inv.php |
| Approval time | Not stated on a primary page. IBKR says "Fund your application to prioritize its review." Third parties say 1 to 3 business days. | MEASURED (funding tip), STATED (days) | https://www.interactivebrokers.com/support/faq/content/current-status-account-application-34485757 ; https://www.brokerage-review.com/online-brokers/application/how-long-to-aprove-ibkr-account.aspx |
| Time to fund | "you have 270 calendar days to fund an approved Individual or IRA account application." | MEASURED | https://www.interactivebrokers.com/support/faq/content/much-time-have-fund-account-28226126 |
| ACH hold | "ACH deposits received before 2pm EST are subject to a 4-business-day hold period from the value date, while those received after 2pm EST require a 5-business-day hold." Another FAQ says funds are "available for trading" after the hold, "Though funds may be released earlier at IBKR's sole discretion". | MEASURED | https://www.interactivebrokers.com/support/faq/content/credit-hold-period-ach-deposits-41556596 ; https://www.interactivebrokers.com/support/faq/content/time-day-ach-deposit-requests-28220803 |
| Paper account | "A paper trading account will not be opened until your account has been funded." IBKR Campus says the account "must be approved" and "you don't need to fund your live account straight away". A separate free trial simulator exists before applying. | MEASURED, conflict | https://www.interactivebrokers.com/support/faq/content/open-paper-trading-account-37128282 ; https://www.interactivebrokers.com/campus/trading-lessons/how-to-open-an-ibkr-paper-trading-account/ ; https://www.interactivebrokers.com/support/faq/content/51680030 |
| API access | Client Portal (Web) API needs "an opened and funded Interactive Brokers account". "Individual clients using the CP Gateway tool must complete a manual login with their IBKR username and password", which requires 2FA. Automated login only with OAuth, which IBKR describes for institutional clients. | MEASURED | https://ibkrcampus.com/campus/trading-lessons/launching-and-authenticating-the-gateway/ ; https://www.interactivebrokers.com/support/faq/articles/56690616 |

### 3.3 Coinbase

| Step | Detail | Tag | Source |
|---|---|---|---|
| Idaho | Coinbase's locations page was not opened. A third-party check dated November 15, 2026 says Coinbase lists only Hawaii as not supported. | STATED | https://coinchoose.com/exchanges/crypto-exchanges-by-us-state/ |
| ID | US: "a driving licence, national identity card, or passport issued in the United States". Proof of address may be requested with a foreign ID. | MEASURED | https://help.coinbase.com/en/coinbase/getting-started/getting-started-with-coinbase/id-doc-verification |
| Timing | "After successful completion of the identification process, you'll typically receive notification of the review status within 4 hours." | MEASURED | same |
| Deposit holds | "Hold periods depend on factors like account history, payment activity, and transaction history." "Crypto purchased with cash that is on hold can be sold or traded on Coinbase." Holds "cannot be altered". | MEASURED | https://help.coinbase.com/en/coinbase/trading-and-funding/sending-or-receiving-cryptocurrency/available-balance-faq |
| API keys | Created on Coinbase Developer Platform: nickname, portfolio, "Permission level (View, Trade, Transfer)", "Allowlist IPs", then 2FA. "API Key authentication should only be used to access your own account." So a trade-only key (no Transfer) with an IP allowlist is possible. | MEASURED (one page is a docs mirror) | https://docs.cdp.coinbase.com/coinbase-business/authentication-authorization/api-key-authentication ; https://main.d39g7xymw2r1c0.amplifyapp.com/advanced-trade/docs/auth |
| Paper | Not checked. UNKNOWN. | UNKNOWN | |

### 3.4 Kraken

| Step | Detail | Tag | Source |
|---|---|---|---|
| Idaho | "Kraken ... does not offer services to residents of: Maine, New York". Idaho not listed. | MEASURED | https://support.kraken.com/articles/where-is-kraken-licensed-or-regulated?country=us |
| Verification | Intermediate needs name, date of birth, phone, address, occupation, SSN, valid ID, proof of address. "Verification processing times can take up to 45 minutes for Intermediate level, and up to 5 days for Pro or Business levels." | MEASURED (requirements page dated 2025-03-01) | https://support.kraken.com/articles/verifying-my-account ; https://support.kraken.com/hc/en-us/articles/201352206-Verification-level-requirements |
| ACH via Plaid | "The estimated processing time for ACH deposits through Plaid is up to five minutes. Once credited to your account, deposits are available instantly for trading and will be available to withdraw after seven days." | MEASURED | https://support.kraken.com/articles/8795459449492-how-do-i-fund-my-account-with-usd-using-ach-via-plaid- |
| API keys | Created at Settings, API with chosen permissions. "Algorithmic spot trading" needs Query Funds, Query Open Orders and Trades, Create and Modify Orders, Cancel/Close Orders. No withdraw permission needed. Kraken warns that Add Withdrawal Addresses plus Withdraw Funds "would allow an attacker to withdraw your assets". | MEASURED | https://docs.kraken.com/exchange/guides/rest/api-keys ; https://support.kraken.com/articles/withdrawal-addresses-api-permission |
| Paper | Not checked. UNKNOWN. | UNKNOWN | |

---

## 4. Individual versus LLC account, data status, registration

### 4.1 Entity account requirements

| Broker | Requirement | Tag | Source |
|---|---|---|---|
| Alpaca | Accepts "Corporations , LLCs and Partnerships". $30,000 minimum deposit. Documents: registration and formation documents, operating agreement, EIN, ID for authorized people and every owner of 10% or more. Business accounts are "for trading purposes, but not for building apps/services." | MEASURED | https://docs.alpaca.markets/us/docs/account-plans ; https://alpaca.markets/learn/live-trading-account-us-resident |
| IBKR | Small business documents include proof of identity and address of the person opening, plus entity documents such as articles, certificate of good standing, operating or LLC agreement. Account minimum USD 0 for "Org" accounts on the required-minimums page. | MEASURED | https://investors.interactivebrokers.com/en/index.php?f=5011 ; https://us1.interactivebrokers.com/en/accounts/required-minimums.php |
| Coinbase | Business account by application, with business and ownership details. One Coinbase business agreement in an SEC filing says eligible entities are "a C-corporation, a multi-member LLC or such other entity as Coinbase in its sole discretion offer". Single-member LLC eligibility not confirmed. | MEASURED (application page), STATED (agreement in a third-party filing) | https://help.coinbase.com/en/pro/getting-started/other/applying-for-a-coinbase-business-account ; https://www.sec.gov/Archives/edgar/data/2082729/000118518526002340/coolbitex10-23.htm |
| Kraken | Business verification "up to 5 days". Bank transfers only to and from a bank account in the business name; crypto only from business-owned wallets. | MEASURED | https://support.kraken.com/articles/verifying-my-account ; https://support.kraken.com/hc/en-us/articles/115004862007-business-account |

### 4.2 Market data professional status

IBKR definition: a non-professional is "any natural person (the definition of a natural person excludes corporations, trusts, organizations, institutions and partnership accounts)" who is not registered with the SEC, CFTC, a state securities agency or exchange, not an "investment advisor", and not employed by an exempt bank in such a role. Professional includes "organizations (corporations, LLCs, partnerships)". MEASURED. https://www.interactivebrokers.com/en/pricing/market-data-pricing.php

Cost effect at IBKR (monthly, Level 1):

| Feed | Non-professional | Professional |
|---|---|---|
| NYSE (Network A/CTA) | USD 1.50 | USD 45.00 |
| NASDAQ (Network C/UTP) | USD 1.50 | USD 25.00 |
| Network B (NYSE American, ARCA, BATS, IEX, regionals) | USD 1.50 | USD 25.00 |
| Total for all three | USD 4.50 | USD 95.00 |

MEASURED, same page. So an LLC account at IBKR pays professional rates (about 21 times higher for these three feeds). Alpaca's own data terms were not opened today; a third-party summary says Alpaca data is for "personal and non-commercial use". STATED. https://github.com/open-meridian/plugin-alpaca

### 4.3 Does trading only your own money need registration?

| Regime | Rule text | Applies to own-money trading? | Tag | Source |
|---|---|---|---|---|
| Investment adviser (federal) | "any person who, for compensation, engages in the business of advising others ... as to the value of securities or as to the advisability of investing in, purchasing, or selling securities" | No. The definition needs advice to others for compensation. | MEASURED | https://www.sec.gov/file/34-69013 ; https://www.sec.gov/resources-small-businesses/capital-raising-building-blocks/investment-advisers |
| Investment adviser (Idaho) | Idaho Code 30-14-102(15): "a person that, for compensation, engages in the business of advising others ..." and 30-14-403(a): "It is unlawful for a person to transact business in this state as an investment adviser unless the person is registered ... or is exempt". | No, same reason. | MEASURED | https://legislature.idaho.gov/statutesrules/idstat/title30/t30ch14/sect30-14-102/ ; https://legislature.idaho.gov/statutesrules/idstat/title30/t30ch14/sect30-14-403/ |
| Commodity trading advisor (CFTC) | 7 USC 1a(12)(A): a person who "for compensation or profit, engages in the business of advising others ... as to the value of or the advisability of trading in" futures, security futures, swaps, certain retail forex or leveraged transactions, or commodity options. | No. Needs advice to others, and spot crypto is not in the listed products. | MEASURED | https://www.law.cornell.edu/uscode/text/7/1a |
| Money transmitter (FinCEN) | FIN-2014-R002: "To the extent that the Company limits its activities strictly to investing in virtual currency for its own account, it is not acting as a money transmitter and is not an MSB under FinCEN's regulations." | No. | MEASURED | https://www.fincen.gov/resources/statutes-regulations/administrative-rulings/application-fincens-regulations-virtual/ |
| Money transmitter (Idaho) | Idaho Code 26-2902: "Money transmission" means "engaging in the business of receiving money for transmission or the business of transmitting money". | Not on its face, since he would not receive money from others. No Idaho Department of Finance guidance page on this was found. | MEASURED (statute), UNKNOWN (agency guidance) | https://legislature.idaho.gov/statutesrules/idstat/title26/t26ch29/sect26-2902/ |

What changes if he trades for other people or sells signals:

- Managing other people's money or giving paid securities advice fits the investment adviser definitions above. Idaho requires registration unless an exemption applies (30-14-403). A securities lawyer is needed before doing this.
- Paid advice on futures, swaps or commodity options fits the CTA definition. Pooling others' money for futures may raise commodity pool operator issues (not researched here). A lawyer is needed.
- Holding or moving other people's crypto or cash could fall into money transmission. A lawyer is needed.
- Selling a signal feed or subscription: the federal and Idaho adviser definitions include advice "through publications or writings" and issuing "analyses or reports concerning securities" for compensation. Whether a given signal product is covered or excluded depends on facts this research did not cover. A securities lawyer is needed.
- Also: once he is registered or acts as an adviser, IBKR's definition makes him a professional market data subscriber, which raises data costs (section 4.2).

---

## 5. Taxes

A tax professional (CPA or enrolled agent who works with active traders) is needed for: trader tax status, the 475(f) election and Form 3115, entity choice, and estimated tax payments. The points below are what the primary sources say.

| Topic | What the source says | Tag | Source |
|---|---|---|---|
| Short-term gains | "If you hold it one year or less, your capital gain or loss is short-term." Count "from the day after the day you acquired the asset up to and including the day you disposed of the asset." | MEASURED | https://www.irs.gov/taxtopics/tc409 |
| Capital loss limit | Deduction is the lesser of "$3,000 ($1,500 if you are married and file a separate return)" or the net loss. | MEASURED | https://www.irs.gov/publications/p550 |
| Wash sale (stocks) | "A wash sale occurs when you sell or trade stock or securities at a loss and within 30 days before or after the sale you: 1. Buy substantially identical stock or securities, 2. Acquire substantially identical stock or securities in a fully taxable trade, 3. Acquire a contract or option to buy substantially identical stock or securities, or 4. Acquire substantially identical stock for your individual retirement arrangement (IRA) or Roth IRA." Disallowed loss is added to the basis of the new shares. Also applies if "your spouse or a corporation you control buys substantially identical stock". | MEASURED | same |
| Wash sale (crypto) | IRS: "A digital asset is treated as property". The wash sale text covers "stock or securities". No law extends it to crypto as of today. H.R. 10357, Digital Asset Tax Certainty Act, latest action "09/16/2026 Ordered to be Reported in the Nature of a Substitute by the Yeas and Nays: 38 - 5." Status: Introduced. The committee's description says its rules would be "effective for taxable years beginning after December 31, 2026" if enacted. H.R. 9172 (June 8, 2026) also proposes this. | MEASURED | https://www.irs.gov/publications/p550 ; https://www.congress.gov/bill/119th-congress/house-bill/10357 ; https://docs.house.gov/meetings/WM/WM00/20260916/119574/HMKP-119-WM00-20260916-SD001.pdf ; https://www.congress.gov/119/bills/hr9172/BILLS-119hr9172ih.pdf |
| Wash sale (tokenized securities) | 1099-DA instructions: "Losses from wash sales of tokenized securities must be reported." | MEASURED | https://www.irs.gov/instructions/i1099da |
| Form 1099-DA | "2026 and beyond: Mandatory reporting of gross proceeds for all digital assets, mandatory reporting of basis information for digital assets that are covered securities". Covered means "acquired after 2025" in a custodial account at that broker and held there until sold. Basis "may be blank if ... the digital assets were acquired prior to 2026", in which case "you will need to determine your basis based on your own books and records." | MEASURED | https://www.irs.gov/instructions/i1099da ; https://www.irs.gov/pub/irs-prior/f1099da--2026.pdf |
| Form 1099-B | Stock and ETF sales are reported by brokers on Form 1099-B; box 2 helps show short or long term. | MEASURED | https://www.irs.gov/publications/p544 |
| Trader tax status | Must meet all: "seek to profit from daily market movements in the prices of securities and not from dividends, interest, or capital appreciation"; "Your activity must be substantial"; "carry on the activity with continuity and regularity." Default: "It doesn't matter whether you call yourself a trader or a day trader, you're an investor for Federal income tax purposes." | MEASURED (page reviewed 09-Nov-2026) | https://www.irs.gov/taxtopics/tc429 |
| 475(f) deadline | "you must make the mark-to-market election by the due date (not including extensions) of the tax return for the year prior to the year for which you intend the election to become effective." New taxpayers: in books and records within "2 months and 15 days after the first day of the year". Then file Form 3115 under Rev. Proc. 2025-23 section 24.01. | MEASURED | same |
| 475(f) effect | Gains and losses become ordinary on Form 4797. "The limitations on capital losses, the wash sale rules, and certain other rules do not apply to traders using the mark-to-market method". | MEASURED | same |
| 475(f) and crypto | Topic 429 speaks of "securities". Whether spot crypto can be covered by a 475(f) election today was not confirmed on an IRS page. The pending bill would add trader rules for digital assets. | UNKNOWN today; ask a tax professional | |
| Dates for 2027 | For tax year 2027, the election is due April 15, 2027 for a calendar-year individual; 2026 deadline passed April 15, 2026. | STATED (tax-firm pages applying the IRS rule) | https://greentradertax.com/category/tax-compliance/ ; https://www.trademomentum.org/blog/day-trading-taxes |
| Idaho rate | Idaho Code 63-3024: "five and three-tenths percent (5.3%) of taxable income over two thousand five hundred dollars ($2,500)" (single), and over $5,000 for joint. Tax Commission: "Effective January 1, 2025, the individual income tax rate is 5.3%." A 2026 bill (H0589) to restore 5.695% for 2026 only shows no action after February 5, 2026. | MEASURED | https://legislature.idaho.gov/statutesrules/idstat/Title63/T63CH30/SECT63-3024/ ; https://tax.idaho.gov/wp-content/uploads/forms/EIN00046/EIN00046_03-02-2026.pdf ; https://legislature.idaho.gov/sessioninfo/2026/legislation/H0589/ |
| Idaho capital gains deduction | Does not apply to stock: intangible property such as "Stocks and bonds" does not qualify. Form CG: "Gains from the sale of stocks and other intangibles don't qualify." | MEASURED (page last updated June 14, 2023) | https://tax.idaho.gov/taxes/income-tax/individual-income/popular-credits-and-deductions/capital-gains/ ; https://tax.idaho.gov/wp-content/uploads/forms/EFO00093/EFO00093_09-18-2025.pdf |
| Idaho conformity | "Idaho conforms to the IRC as of January 1, 2026." | MEASURED | https://tax.idaho.gov/wp-content/uploads/forms/EIN00046/EIN00046_03-02-2026.pdf |

Record keeping the bot should do itself (from the sources above): keep every fill with timestamp, quantity, price, fee and venue; keep cost basis for any crypto bought before 2026 or moved between venues (1099-DA basis can be blank); flag stock wash sales across all accounts (Pub 550 counts IRA and spouse purchases, which a broker cannot see); keep a written record of a 475(f) election if made.

---

## 6. Market conduct rules an automated system must not break

These apply to the trader as well as to brokers. The bot should have controls so it cannot create these patterns by accident.

| Rule | Text | Where it applies | Source |
|---|---|---|---|
| Wash trades and matched orders (securities) | 15 USC 78i(a)(1): "For the purpose of creating a false or misleading appearance of active trading in any security ... (A) to effect any transaction in such security which involves no change in the beneficial ownership thereof, or (B) to enter an order or orders for the purchase of such security with the knowledge that an order or orders of substantially the same size, at substantially the same time, and at substantially the same price, for the sale of any such security, has been or will be entered by or for the same or different parties". | US stocks and ETFs | https://www.law.cornell.edu/uscode/text/15/78i |
| Manipulation (securities) | 15 USC 78i(a)(2): "To effect, alone or with 1 or more other persons, a series of transactions in any security ... creating actual or apparent active trading in such security, or raising or depressing the price of such security, for the purpose of inducing the purchase or sale of such security by others." | US stocks and ETFs | same |
| Spoofing (CFTC) | 7 USC 6c(a)(5)(C): unlawful to engage in trading that "is, is of the character of, or is commonly known to the trade as, 'spoofing' (bidding or offering with the intent to cancel the bid or offer before execution)." Applies to trading "on or subject to the rules of a registered entity". | Futures and other CFTC-registered venues | https://www.law.cornell.edu/uscode/text/7/6c |
| Fraud and manipulation in commodities (CFTC) | 17 CFR 180.1(a): unlawful "in connection with any swap, or contract of sale of any commodity in interstate commerce ... to intentionally or recklessly: (1) Use or employ, or attempt to use or employ, any manipulative device, scheme, or artifice to defraud". | Reaches spot commodity sales in interstate commerce, which the CFTC treats as including crypto (how far is a legal question) | https://www.law.cornell.edu/cfr/text/17/180.1 |
| Layering and spoofing (FINRA, for member firms) | Rule 5210.03 Type 1: "a party enters multiple limit orders on one side of the market at various price levels (the 'Displayed Orders'); and ... the level of supply and demand for the security changes; and ... the party enters one or more orders on the opposite side of the market ... that are subsequently executed; and ... following the execution of the Contra-Side Orders, the party cancels the Displayed Orders." | Brokers must not "engage in or facilitate" it, so they surveil customer orders | https://www.finra.org/rules-guidance/rulebooks/finra-rules/5210 |
| Self-trades (FINRA) | Rule 5210.02: firms "must have policies and procedures in place that are reasonably designed to review their trading activity for, and prevent, a pattern or practice of self-trades resulting from orders originating from a single algorithm". | Same | same |
| General anti-fraud (FINRA) | Rule 2020: "No member shall effect any transaction in, or induce the purchase or sale of, any security by means of any manipulative, deceptive or other fraudulent device or contrivance." | Same | https://www.finra.org/rules-guidance/rulebooks/finra-rules/2020 |
| Market access controls (SEC Rule 15c3-5) | Applies to brokers with market access. They must have controls that "prevent the entry of orders that exceed appropriate pre-set credit or capital thresholds" and "prevent the entry of erroneous orders", including orders that "indicate duplicative orders". | The broker will reject bot orders that trip these checks; the bot should have its own matching limits | https://www.law.cornell.edu/cfr/text/17/240.15c3-5 |
| Coinbase venue rules | "2.63 Market Manipulation specifically includes, without limitation: front-running, wash trading, spoofing, layering, churning, and quote stuffing." Self-trades are blocked: "Traders are not able to place an Order which would result in self-execution". Orders may be cancelled for "using the API in a manner which unreasonably burdens the platform". | Coinbase Advanced and Exchange | https://www.coinbase.com/legal/trading_rules |
| Kraken venue rules | "Clients are prohibited from engaging in any activity that amounts to market abuse and or manipulation on the exchange; examples include wash trading, layering and spoofing." "STP is applied to all orders." "API access is subject to rate limits to protect against malicious usage and order book manipulation." | Kraken | https://www.kraken.com/legal/exchangetradingrules |

Design implications (plain reading of the rules above, not legal advice):

- Do not let the bot place orders it intends to cancel to move the price, and do not let it stack orders on one side then trade the other side and cancel. Log the reason for every cancel.
- Do not let two strategies in the same account trade against each other. Use the venue's self-trade prevention and a pre-trade check.
- Keep pre-trade limits for order size, price distance from the market, open order count, and duplicate orders. Respect venue rate limits.
- A lawyer is needed if the bot will run high cancel rates, market-making style quoting, or anything near the close or open designed to affect a price.

## Where a professional is needed (summary)

- Tax professional: trader tax status, the 475(f) election and Form 3115, whether 475(f) can cover crypto, LLC tax choice, Idaho filing, estimated taxes, and what H.R. 10357 would change if it is enacted.
- Securities or commodities lawyer: trading for anyone else, pooling money, selling signals or subscriptions, any market-making or high-cancel strategy, and whether an LLC is worth the higher data costs and Alpaca's $30,000 business minimum.
