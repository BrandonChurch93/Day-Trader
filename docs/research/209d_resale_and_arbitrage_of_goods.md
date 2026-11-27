# Deep Dive 209, Lane D: Buying and Reselling Outside Financial Markets

Date: 2026-11-27
Lane: Buying and reselling outside financial markets (10 methods screened, 5 deep dives)
Scope: Evaluate whether an autonomous AI agent, backed by one-time owner setup (`OWNER ONCE`) and code/pipeline setup (`SCAFFOLDING`), can buy and resell goods outside financial markets with reliable positive net profit, no recurring human labor (`OWNER EVERY TIME`), explicit platform permission for automation, and an honest test before capital is committed.

Owner's words (2026-11-27): "feel free to research potential other options for AI to autonomously make money and that might mean you doing searches for ways that humans can make money and looking into the process to see if it can be automated by AI I don't mind building the scaffolding, the towing, or anything else that needs to be involved to autonomously do this", "This is an experiment, testing if AI can actually make reliable money autonomously without major human involvement.", "It has to work in test testing and in theory before we can try it in a real environment."

## Executive Summary

Most physical and digital resale markets fail at least one of three hard gates: explicit bans on automated buying/scraping, recurring physical labor (`OWNER EVERY TIME`), or high platform fees combined with entrenched bot competition.

- **One method clears the rules and labor gates for a $0 paper test:** Domain names and expired domains bought through the GoDaddy Auctions Expiry API and resold on Afternic. GoDaddy's API Terms of Use explicitly allow autonomous agents (`STATED`, [GoDaddy API Terms of Use](https://www.godaddy.com/legal/agreements/godaddy-api-terms-of-use)), there is no physical handling, and the strategy can be paper-traded on recorded auction closes and resale prices before spending capital (`INFERENCE`). However, institutional drop-catchers already automate this market, Afternic charges 15% to 30% commission with a $15 minimum (`STATED`, [Afternic Sell Domains](https://www.afternic.com/sell-domains)), and the median net return for a small portfolio is `UNKNOWN`. Verdict: `WORTH A TEST` (paper-trade only first).
- **One method is `WATCH`:** Vaulted trading cards on COMC. COMC removes physical shipping and offers its own internal automated "COMC Buying Agent" (`STATED`, [COMC User Agreement](https://www.comc.com/UserAgreement)), but its User Agreement is silent on external third-party bots (`UNKNOWN`, not allowed without permission) and charges a 5% transaction fee plus a 10% cash-out fee (`STATED`, [COMC Cash-Out](https://www.comc.com/Cashout)).
- **Eight of ten methods are `OUT`:** Online arbitrage via Amazon FBA + prep center, dropshipping (Shopify/Amazon/eBay), in-game items (Steam Community Market), used books by scanner, liquidation pallets, gift card arbitrage, government and estate auctions, and cashback/price-error hunting all fail on explicit automation bans, non-withdrawable currency, or recurring human labor (`OWNER EVERY TIME`).

## Screening Table: All 10 Methods in Lane D

| # | Method | Primary Automation / Bot Rule | Recurring Human Labor? | Capital Needed Before $1 | Verdict | Deep Dive? |
|---|---|---|---|---|---|---|
| 1 | Domain names and expired domains (GoDaddy API + Afternic) | Explicitly allowed via API for autonomous agents (`STATED`, [GoDaddy API Terms of Use](https://www.godaddy.com/legal/agreements/godaddy-api-terms-of-use)) | No (`OWNER ONCE` + `SCAFFOLDING`) | Auctions membership + domain buys + annual renewals (`STATED`, [GoDaddy Auctions Agreement](https://www.godaddy.com/legal/agreements/auctions-membership-agreement)) | `WORTH A TEST` (paper-trade first) | Yes (#1) |
| 2 | Collectibles and trading cards (COMC vaulted / TCGplayer) | COMC silent on external bots (`UNKNOWN`, [COMC User Agreement](https://www.comc.com/UserAgreement)); eBay bans buy-for-me bots (`STATED`) | No on COMC vault; Yes on raw cards | Store credit + 5% sale fee + 10% cash-out fee (`STATED`, [COMC Cash-Out](https://www.comc.com/Cashout)) | `WATCH` | Yes (#2) |
| 3 | Online and retail arbitrage (Amazon FBA + prep center) | Repricing allowed via SP-API (`STATED`, [Amazon Automate Pricing](https://sellercentral.amazon.com/help/hub/reference/external/G201994820?locale=en-US)); retail-site checkout bots generally blocked and retail receipts fail brand gating (`INFERENCE`) | Yes: retail sourcing exceptions, brand/authenticity appeals (`OWNER EVERY TIME`) | $39.99/mo Pro fee + inventory + prep + FBA fees (`STATED`) | `OUT` | Yes (#3) |
| 4 | Dropshipping (Shopify wholesale vs Amazon/eBay) | Retail-to-marketplace dropshipping banned on [eBay](https://www.ebay.com/help/selling/posting-items/setting-postage-options/drop-shipping?id=4176) and [Amazon](https://sellercentral.amazon.com/help/hub/reference/external/G201808410?language=en_US) (`STATED`); Shopify TOS bars automated access/scraping of Shopify Services (`STATED`, [Shopify Terms](https://www.shopify.com/legal/terms)) | Yes: supplier disputes, chargebacks, ad creative testing (`OWNER EVERY TIME`) | $29-$39/mo Shopify Basic + 2.9% + $0.30/txn + ad spend (`STATED`, [Shopify Pricing](https://www.shopify.com/pricing)) | `OUT` | Yes (#4) |
| 5 | In-game items and digital collectibles (Steam Community Market) | Explicitly banned: no bots/scripts AND Steam Wallet has no cash value (`STATED`, [Steam Subscriber Agreement](https://store.steampowered.com/agreement/)) | Blocked by rules and no cash-out | Wallet funds cannot be withdrawn to bank (`STATED`, [Steam Market FAQ](https://help.steampowered.com/en/faqs/view/61F0-72B7-9A18-C70B)) | `OUT` | Yes (#5) |
| 6 | Used books by scanner | Marketplace repricing allowed, but physical book scouting at thrift stores/library sales cannot be done by an agent (`INFERENCE`) | Yes: driving, scanning, packing (`OWNER EVERY TIME`) | Inventory + scanner app + Amazon/eBay fees (`STATED`) | `OUT` | Screened |
| 7 | Liquidation pallets | B-Stock/freight auctions require buyer pickup or freight dock, physical inspection, testing, and disposal of damaged units (`INFERENCE`) | Yes: receiving freight, testing, listing defects (`OWNER EVERY TIME`) | Hundreds to thousands per pallet plus freight (`UNKNOWN` exact floor) | `OUT` | Screened |
| 8 | Gift card arbitrage | Cashback portals ban bots (`STATED`, [Rakuten Terms](https://www.rakuten.com/help/article/terms-conditions)); resellers enforce anti-bot fraud blocks (`STATED`, [CardCash TOS](https://www.cardcash.com/tos/)) | Yes: fraud holds, manual ID checks (`OWNER EVERY TIME`) | Card float minus 8%-20% resale haircut (`UNKNOWN` net spread) | `OUT` | Screened |
| 9 | Government and estate auctions | Explicitly banned: GovDeals forbids spiders, crawlers, or robots (`STATED`, [GovDeals User Agreement](https://www.govdeals.com/en/content/site-terms)) | Yes: mandatory in-person packing, loading, and pickup (`OWNER EVERY TIME`) | Bid deposit + freight/pickup costs (`STATED`, [GovDeals User Agreement](https://www.govdeals.com/en/content/site-terms)) | `OUT` | Screened |
| 10 | Cashback and price-error hunting | Explicitly banned: Rakuten forbids electronic agents, bots, and scripts (`STATED`, [Rakuten Terms](https://www.rakuten.com/help/article/terms-conditions)) | Yes: canceled price-error orders and manual checkout (`OWNER EVERY TIME`) | Working capital float for merchandise (`UNKNOWN`) | `OUT` | Screened |

Notes on the five screened-out methods (items 6 to 10):

- **Used books by scanner:** Physical scouting at thrift stores, library sales, and estate sales requires a human body on site every time (`OWNER EVERY TIME`), which fails the autonomy rule before fees are even counted (`INFERENCE`).
- **Liquidation pallets:** Manifested or unmanifested return pallets require freight delivery, physical sorting, functional testing, and disposing of broken items (`OWNER EVERY TIME`), with no clean zero-touch pipeline (`INFERENCE`).
- **Gift card arbitrage:** Stacking discounted gift cards with cashback portals hits Rakuten's explicit ban on automated access (`STATED`, [Rakuten Terms & Conditions](https://www.rakuten.com/help/article/terms-conditions)), while bulk card resellers such as CardCash run automated anti-bot fraud blocks (`STATED`, [CardCash Terms](https://www.cardcash.com/tos/)).
- **Government and estate auctions:** GovDeals prohibits any automated access ("spiders, crawlers, robots or any other similar means") and sells items "AS IS, WHERE IS" with the buyer required to handle packing, loading, and physical removal (`STATED`, [GovDeals User Agreement](https://www.govdeals.com/en/content/site-terms)), failing both the rules gate and the labor gate.
- **Cashback and price-error hunting:** Rakuten Section 5.1 explicitly prohibits users from accessing the service "by expert system, electronic agent, 'bot' or other automated means" or using "scripts or disguised redirects to derive financial benefit from Rakuten" (`STATED`, [Rakuten Terms & Conditions](https://www.rakuten.com/help/article/terms-conditions)). Retail price-error flipping is also dominated by paid Discord monitor groups and routinely reversed by retailer pricing-error cancellation clauses (`INFERENCE`).

## Deep Dive 1: Domain Names and Expired Domains (GoDaddy Expiry API + Afternic)

### 1. End-to-End Steps (Nothing to Bank Account)

1. Open a GoDaddy account, add a payment method, and purchase a GoDaddy Auctions membership (or Discount Domain Club Domain Pro, which includes GoDaddy Auctions membership) (`OWNER ONCE`).
2. Complete Afternic payee profile and tax information (ACH, PayPal, Check, or Wire) (`OWNER ONCE`).
3. Generate GoDaddy API credentials and build the valuation, bidding, DNS-update, and Afternic listing pipeline (`SCAFFOLDING`).
4. Poll GoDaddy Auctions Expiry APIs for expiring domains, score each name using recorded comparable sales and trademark checks, and submit bids within preset dollar caps (`AGENT ALONE`).
5. On winning bids, GoDaddy automatically charges the payment method on file for the bid amount plus a mandatory 1-year renewal fee and ICANN fee within 48 hours (`AGENT ALONE` / automated billing, `STATED`, [GoDaddy Auctions Membership Agreement](https://www.godaddy.com/legal/agreements/auctions-membership-agreement)).
6. Point winning domains to GoDaddy Aftermarket / Afternic nameservers to qualify for the reduced commission tier and list at fixed Buy-Now prices with Fast Transfer enabled (`AGENT ALONE`).
7. When a buyer purchases a Buy-Now domain via Afternic Fast Transfer, domain delivery is automated without seller intervention; no buyer messaging is required for Buy-Now listings (`AGENT ALONE` / platform automated).
8. Handle refunds or disputes: expired domain auction purchases are binding contracts (`STATED`, [GoDaddy Auctions Bid/Offer/Buy Agreement](https://www.godaddy.com/legal/agreements/auctions-bid-offer-buy-agreement)), and trademark (UDRP) complaints are rare if trademark screening is enforced, though any legal dispute escalates to the owner (`OWNER EVERY TIME` only on legal exception).
9. Receive payout to bank account (ACH/wire/PayPal) minus Afternic commission, typically within 48 to 72 hours after domain delivery on GoDaddy Auctions or 6 to 20 days on aftermarket channels (`STATED`, [GoDaddy Domain Investing](https://www.godaddy.com/domains/domain-investing)).
10. Track cost basis, renewal fees, and proceeds for US self-reported tax filing; GoDaddy explicitly states it does not issue 1099 forms for domain sales through GoDaddy Auctions or List for Sale (`OWNER ONCE` annual tax filing; `STATED`, [GoDaddy Buying Domains Help](https://www.godaddy.com/help/buying-domains-through-godaddy-auctions-890)).

### 2. Step Labels and Blocking Step

- `OWNER ONCE`: Account creation, payment method, Auctions membership, Afternic payee setup, annual tax reporting.
- `SCAFFOLDING`: API integration, trademark filter, valuation model, automated DNS and Buy-Now listing scripts.
- `AGENT ALONE`: Daily expiry scanning, bidding, DNS pointing, repricing, renewal/drop decisions.
- `OWNER EVERY TIME`: None in normal fixed-price Buy-Now flow (only legal/UDRP exceptions if trademark screening fails).
- **Blocking step:** None on rules or physical labor. The real risk is economic (negative expected return after commissions, annual renewals, and bot competition).

### 3. Platform Rule on Automated / AI Work

GoDaddy explicitly allows autonomous AI agents through its API (`STATED`, opened 2026-11-27, [GoDaddy API Terms of Use](https://www.godaddy.com/legal/agreements/godaddy-api-terms-of-use)):

> "The API is designed to enable customers to build applications, integrations, automations, and AI-assisted workflows that interact with GoDaddy products and services in secure and reliable ways, including through software, scripts, automations, artificial intelligence tools, coding assistants, autonomous agents, integrated development environments, browser extensions, middleware, orchestration platforms, plugins, and similar technologies or services that generate, submit, relay, or execute API requests on your behalf (collectively, 'Automated Tools')."

GoDaddy further confirms: "You may access and use the API directly or through Automated Tools to build applications, integrations, automations, and AI-assisted workflows that interact with GoDaddy products and services, provided that you comply with these API Terms" (60 requests/minute default rate limit) (`STATED`, [GoDaddy API Terms of Use](https://www.godaddy.com/legal/agreements/godaddy-api-terms-of-use)). GoDaddy Auctions also publishes dedicated Expiry APIs for Auctions members to automate expired domain discovery and acquisition (`STATED`, [GoDaddy Auctions Expiry APIs](https://www.godaddy.com/resources/uk/news/godaddy-auctions-expiry-apis-automate-domain-acquisition)). By contrast, Sedo's General Terms prohibit "data mining or scraping using robots or in some other way" (`STATED`, [Sedo General Terms](https://sedo.com/us/about-us/policies/general-terms-and-conditions/)).

### 4. Evidence That It Pays

- **Published commission and cost structure (`STATED`):** Afternic charges 20% commission with Afternic Boost (15% Basic) when domains use GoDaddy Aftermarket nameservers, or 30% Boost (25% Basic) without them, with a $15 minimum commission on every sale (`STATED`, [Afternic Sell Domains](https://www.afternic.com/sell-domains)). Standard `.com` renewals at GoDaddy are $22.99/year without Discount Domain Club, or $10.99 to $14.99/year with Discount Domain Club (`STATED`, [GoDaddy Discount Domain Club](https://www.godaddy.com/domains/discount-domain-club)).
- **Median sell-through rate and net ROI (`UNKNOWN`):** Neither GoDaddy nor Afternic publishes audited median net returns or portfolio sell-through rates for small automated buyers. Public anecdotes of large domain flips suffer from severe survivorship bias (`INFERENCE`).

### 5. What It Needs Before the First Dollar

- **Money:** GoDaddy Auctions membership (or Discount Domain Club Domain Pro at $359.88/year, which includes Auctions membership and lower `.com` renewals at $10.99/yr, `STATED`, [GoDaddy Domain Pro](https://www.godaddy.com/resources/news/introducing-the-new-must-have-membership-for-domain-investors)), plus working capital for domain purchases and 1-year renewals (every unsold domain burns $10.99+ per year if renewed).
- **Time:** Domains are illiquid; holding periods before a retail Buy-Now sale can be months or years (`INFERENCE`).
- **Hard-to-get items:** No audience, no storefront reviews, and no approval queue beyond standard GoDaddy API eligibility requirements (`STATED`, [GoDaddy API Terms of Use](https://www.godaddy.com/legal/agreements/godaddy-api-terms-of-use)).

### 6. Agent Edge vs Bot Crowding

- **Where an agent helps:** An LLM can read thousands of expiring brandable two-word domains daily, check semantic quality, run automated trademark screening, and price names consistently without fatigue (`INFERENCE`).
- **Why it is crowded:** Professional domain investors and institutional drop-catchers already run automated bidding scripts on GoDaddy's Expiry APIs, DropCatch, and SnapNames, bidding up obvious short or high-backlink names close to wholesale clearing value (`INFERENCE`).

### 7. Honest Paper Test Before Spending Money

- Record daily GoDaddy expired-domain auction closing prices (plus the mandatory $10.99 renewal fee) for a fixed universe of candidate domains over 30 to 90 days using public/member feeds without bidding real money (`INFERENCE`).
- Have the agent log its exact virtual bid cap and Buy-Now resale price before each auction closes (strictly non-peeking).
- Track whether virtual winners sell on public domain-sale records or receive comparable wholesale bids over a fixed window, subtracting the 15% to 20% Afternic commission ($15 minimum) and annual renewal burn (`INFERENCE`). If simulated net ROI after commissions and renewals is not clearly positive, stop before spending a dollar.

### 8. Verdict

`WORTH A TEST` (paper-trade only first): It is the only resale method in Lane D where the primary marketplace explicitly permits autonomous AI agents by API with zero recurring physical labor, making a $0 recorded-price paper test cheap and clean.

## Deep Dive 2: Vaulted Trading Cards and Collectibles (COMC + TCGplayer)

### 1. End-to-End Steps (Nothing to Bank Account)

1. Create a COMC account and fund COMC Store Credit (`OWNER ONCE`).
2. Configure payout method (PayPal or mailed US check) and provide tax compliance information when requested by COMC (`OWNER ONCE`, `STATED`, [COMC User Agreement](https://www.comc.com/UserAgreement)).
3. Build a valuation and price-comparison pipeline comparing COMC listed cards against recorded eBay/COMC sold prices (`SCAFFOLDING`).
4. Purchase mispriced vaulted cards already stored in COMC's warehouse using Store Credit, or configure COMC's optional built-in "COMC Buying Agent" with category/date/budget rules (`AGENT ALONE` if external automation were permitted, or `OWNER ONCE` rules on COMC's internal agent).
5. Relist purchased cards immediately inside COMC's vault at target Buy-Now prices or send them to COMC's eBay auction channels without ever physically touching a card (`AGENT ALONE` / COMC vault).
6. COMC handles physical storage, scanning, packing, shipping, and buyer customer service (`SCAFFOLDING` / platform handled).
7. Handle refunds/disputes: COMC handles buyer fulfillment disputes; however, all purchases made via COMC's Buying Agent are final and non-refundable (`STATED`, [COMC User Agreement](https://www.comc.com/UserAgreement)).
8. Pay transaction fees (5% on COMC sales, or 4% to 8% plus flat fees on COMC eBay auctions) and monthly storage fees ($0.01/month per card after 90 days for items priced over $0.25) (`STATED`, [COMC Blog Fee Update](https://blog.comc.com/2018/11/09/huge-announcement/) and [COMC Ingestion/Auction Update](https://blog.comc.com/2025/10/01/ingestion-service-level-update-october-1-2025/)).
9. Convert Store Credit to cash via PayPal or check, paying COMC's 10% Cash-Out Fee (plus $1 if under $250, or $5 for a check), or use COMC Direct-to-Cash eBay auctions (92% payout minus $5 under $1,000; 95% over $1,000) (`OWNER ONCE` / periodic withdrawal; `STATED`, [COMC Cash-Out](https://www.comc.com/Cashout) and [COMC Direct 2 eBay](https://blog.comc.com/2026/07/20/direct-2-ebay-live-the-fastest-way-to-turn-your-cards-into-cash/)).
10. Report net capital gains or business income on US taxes (`OWNER ONCE` annually).

### 2. Step Labels and Blocking Step

- `OWNER ONCE`: Account creation, Store Credit funding, PayPal/check payout setup, annual taxes.
- `SCAFFOLDING`: Card valuation model using recorded sales.
- `AGENT ALONE`: Only if external API/bot access is permitted; otherwise blocked.
- `OWNER EVERY TIME`: Manual clicking if external automation is barred.
- **Blocking step:** External bot/API permission on COMC is `UNKNOWN` (not stated as allowed), while eBay explicitly prohibits buy-for-me agents and automated scraping (`STATED`), and TCGplayer prohibits scraping/bots outside approved API access (`STATED`, [TCGplayer Terms of Service](https://help.tcgplayer.com/hc-en-us/articles/205004918-Terms-of-Service)).

### 3. Platform Rule on Automated / AI Work

COMC's User Agreement explicitly describes COMC's own optional internal "COMC Buying Agent" ("Agentic Buyer") feature, where COMC buys cards on your behalf using preset category, date, and Store Credit budget rules (`STATED`, opened 2026-11-27, [COMC User Agreement](https://www.comc.com/UserAgreement)):

> "COMC may offer an optional feature that allows you to delegate purchasing decisions to an automated 'Buying Agent' acting on your behalf ('COMC Agent'). By enabling this feature, you authorize COMC to use your Store Credit to purchase items matching criteria that you specify (such as card category, year or date range, and budget)... All purchases made by the Buying Agent are final and non-refundable, regardless of the specific items selected."

However, the COMC User Agreement is **silent** on whether a user may run external third-party bots or scrapers against COMC, and prohibits actions that "could unfairly manipulate the pricing, selling, or trading process" (`STATED`, [COMC User Agreement](https://www.comc.com/UserAgreement)). Under our rules, silence means `UNKNOWN`, not allowed. On TCGplayer, external scraping/bots without approved API access are prohibited (`STATED`, [TCGplayer Terms of Service](https://help.tcgplayer.com/hc-en-us/articles/205004918-Terms-of-Service)), and TCGplayer charges 10.25% to 10.75% commission plus 2.5% + $0.30 payment processing (`STATED`, [TCGplayer Fees](https://help.tcgplayer.com/hc-en-us/articles/201357836-TCGplayer-Fees)).

### 4. Evidence That It Pays

- **Published fee drag (`STATED`):** Flipping inside COMC and cashing out Store Credit costs 5% on each sale plus 10% on cash-out (an effective 14.5% round-trip drag on a single flip, plus storage fees after 90 days) (`STATED`, [COMC Cash-Out](https://www.comc.com/Cashout), [COMC Store Credit](https://www.comc.com/addcredit)). Using COMC Cash eBay Auctions for vaulted cards costs 8% + $5 on cards under $1,000, or 5% on cards over $1,000 (`STATED`, [COMC October 2025 Update](https://blog.comc.com/2025/10/01/understanding-comcs-new-ebay-auction-options/)).
- **Median flipper profit (`UNKNOWN`):** No audited study or platform disclosure publishes median net profit for COMC vaulted-card flippers.

### 5. What It Needs Before the First Dollar

- **Money:** Store Credit float (no fee to deposit 1:1, `STATED`, [COMC FAQ](https://www.comc.com/FAQ)); enough capital to absorb 14.5% fee drag or target $100+ cards for Cash eBay Auctions.
- **Time:** Weeks to months for relisted cards to sell at Buy-Now prices, or 1 to 2 weeks turnaround for eBay auctions (`STATED`, [COMC Ingestion Update](https://blog.comc.com/2025/10/01/ingestion-service-level-update-october-1-2025/)).
- **Hard-to-get items:** Written permission or official API access from COMC for external agent execution.

### 6. Agent Edge vs Bot Crowding

- **Where an agent helps:** Trading cards have hundreds of thousands of parallel variants, print runs, and player-news price moves; an AI agent can match exact parallel/grade comps faster than a human (`INFERENCE`).
- **Why it is crowded:** COMC flippers already monitor newly processed cards daily, and COMC's own internal "COMC Buying Agent" automates category/budget buying for all users, compressing easy mispricings (`INFERENCE`).

### 7. Honest Paper Test Before Spending Money

- Log publicly visible COMC Buy-Now asking prices alongside recorded eBay/COMC sold prices for the exact card parallel and grade over 30 days.
- Simulate buying only when the ask is at least 25% below recent median sold comps, then track whether the card clears at target ask within 30 to 60 days after subtracting either the 14.5% Store-Credit round-trip fee or the 8% + $5 Cash eBay Auction fee (`INFERENCE`).

### 8. Verdict

`WATCH`: Vaulted cards solve physical shipping, but COMC's external automation rule is `UNKNOWN` (not allowed without confirmation) and the 14.5% cash-out drag requires large mispricings.

## Deep Dive 3: Online Arbitrage via Amazon FBA + 3PL Prep Center

### 1. End-to-End Steps (Nothing to Bank Account)

1. Register a US business entity/tax ID, open an Amazon Professional Seller account ($39.99/month), pass identity/video verification, and enroll in FBA (`OWNER ONCE`).
2. Contract with an FBA 3PL prep center to receive retail shipments, inspect, polybag/label, and forward cartons to Amazon FBA (`OWNER ONCE`).
3. Build SP-API repricing and product-profitability software using Amazon's permitted Automate Pricing / SP-API price-update rules (`SCAFFOLDING`).
4. Source discounted retail products online (Target, Walmart, Kohl's, etc.) and ship them to the prep center (`OWNER EVERY TIME`: most retail sites block checkout bots, enforce per-household quantity limits, and cancel bulk reseller orders).
5. Prep center receives, inspects, labels, and ships inventory to Amazon FBA warehouses (`SCAFFOLDING` / paid third-party service).
6. Reprice active FBA listings automatically via Amazon Automate Pricing or SP-API (`AGENT ALONE`).
7. Amazon FBA picks, packs, ships, and handles routine buyer returns (`SCAFFOLDING` / platform handled).
8. Respond to Amazon brand-gating, IP complaints, and Section 3 authenticity/supply-chain invoice audits (`OWNER EVERY TIME`: retail store receipts are frequently rejected by Amazon in favor of authorized wholesale invoices).
9. Receive biweekly ACH disbursements to bank account minus referral fees, FBA fulfillment fees, monthly storage fees, and return deductions (`AGENT ALONE` / automated payout).
10. Reconcile IRS Form 1099-K and inventory cost of goods sold (`OWNER ONCE` annually).

### 2. Step Labels and Blocking Step

- `OWNER ONCE`: Amazon Pro account verification, 3PL prep center contract, tax setup.
- `SCAFFOLDING`: SP-API repricing and fee calculator.
- `AGENT ALONE`: Repricing active FBA inventory.
- `OWNER EVERY TIME`: Purchasing from online retailers (anti-bot checkout walls and order cancellations) and defending Amazon IP/authenticity/brand-gating claims.
- **Blocking step:** Automated retail purchasing and Amazon authenticity/invoice verification cannot be run autonomously by an agent (`OWNER EVERY TIME`).

### 3. Platform Rule on Automated / AI Work

Amazon explicitly permits automated repricing on Seller Central via its Automate Pricing tool and Selling Partner API (`STATED`, [Amazon Automate Pricing](https://sellercentral.amazon.com/help/hub/reference/external/G201994820?locale=en-US) and [Amazon Price Update Policy](https://sellercentral.amazon.com/help/hub/reference/external/G3VA4VWKFMR9R48M?locale=en-US)). However, online arbitrage requires purchasing from third-party retail websites that routinely deploy anti-bot checkout defenses and cancel bulk reseller orders, and Amazon strictly prohibits direct retailer-to-customer drop shipping (`STATED`, [Amazon Drop Shipping Policy](https://sellercentral.amazon.com/help/hub/reference/external/G201808410?language=en_US)).

### 4. Evidence That It Pays

- **Base-rate seller survival (`MEASURED` from prior repo record):** As documented in our repo's prior audit (`docs/research/205f_offers_and_resale_arbitrage.md`), Marketplace Pulse data shows severe seller attrition and concentration on Amazon, where only a small minority of third-party sellers survive five years or generate meaningful volume (`INFERENCE` for small online-arbitrage entrants; exact current median net profit for automated OA sellers is `UNKNOWN`).
- **Fee stack (`STATED`):** Amazon Professional accounts cost $39.99/month plus referral fees (commonly 15%), FBA pick-and-pack fees, monthly storage fees, and prep-center fees (typically $1 to $2+ per unit) (`STATED` / `INFERENCE`).

### 5. What It Needs Before the First Dollar

- **Money:** $39.99/month Pro subscription, initial inventory float, prep-center intake fees, inbound FBA shipping, and software subscriptions (`STATED` / `INFERENCE`).
- **Time:** Weeks for account approval, prep-center receiving, and FBA check-in.
- **Hard-to-get items:** Brand and category ungating approvals (requiring authorized distributor invoices, not retail receipts).

### 6. Agent Edge vs Bot Crowding

- **Where an agent helps:** Parsing clearance feeds and calculating FBA fees quickly (`INFERENCE`).
- **Why it is crowded:** Thousands of human and software-assisted sellers use identical OA scanning software (Keepa, Tactical Arbitrage, SellerAmp) on the same retail clearance sales, causing rapid price-tank wars as soon as FBA shipments check in (`INFERENCE`).

### 7. Honest Paper Test Before Spending Money

- Record retail clearance prices alongside Amazon Buy Box prices and sales-rank velocity over 30 days, then simulate a 14-day lag (representing shipping to a prep center plus FBA check-in) before measuring the realized Amazon Buy Box price minus referral, FBA, storage, and prep fees (`INFERENCE`). That 14-day lag exposes the price-tank effect honestly.

### 8. Verdict

`OUT`: Automated buying on retail sites hits anti-bot/order-cancellation walls, and Amazon brand-gating/authenticity audits require human intervention and wholesale invoices (`OWNER EVERY TIME`).

## Deep Dive 4: Dropshipping (Shopify Storefront + Wholesale Supplier vs Amazon/eBay)

### 1. End-to-End Steps (Nothing to Bank Account)

1. Form a business/tax profile, open a Shopify Basic store ($29/month billed annually or $39/month billed monthly), and activate Shopify Payments (2.9% + $0.30 online standard card rate) (`OWNER ONCE`, `STATED`, [Shopify Pricing](https://www.shopify.com/pricing)).
2. Vet and sign a direct wholesale or dropshipping supplier agreement where your store is the sole seller of record (`OWNER ONCE`).
3. Build storefront theme, product catalog sync, automated order-routing webhook to the supplier, and tracking-number sync (`SCAFFOLDING`).
4. Acquire traffic via paid ads (Meta, Google, TikTok) or SEO; a standalone Shopify store starts with zero built-in traffic (`OWNER EVERY TIME` for ad account compliance, creative testing, and budget risk; `INFERENCE`).
5. Customer checks out on Shopify; payment is captured by Shopify Payments and order routes automatically to the wholesale supplier (`AGENT ALONE` / `SCAFFOLDING`).
6. Supplier packs and ships directly to the customer (`SCAFFOLDING` / third-party supplier).
7. Handle customer support emails, damaged/late shipments, returns, and credit-card chargebacks (`OWNER EVERY TIME` on chargeback evidence, supplier failures, and edge-case refunds).
8. Receive Shopify Payments bank payouts minus 2.9% + $0.30 card fees (or +2% third-party transaction fee if not using Shopify Payments) (`AGENT ALONE` / automated payout, `STATED`, [Shopify Pricing](https://www.shopify.com/pricing)).
9. File sales tax (Shopify Tax charges 0.35% after introductory threshold, `STATED`, [Shopify Pricing](https://www.shopify.com/pricing)) and annual income taxes (`OWNER ONCE` annually).

### 2. Step Labels and Blocking Step

- `OWNER ONCE`: Shopify account, Shopify Payments KYC, wholesale supplier contract, tax setup.
- `SCAFFOLDING`: Storefront, inventory/order sync apps, email templates.
- `AGENT ALONE`: Routine order forwarding and basic FAQ replies.
- `OWNER EVERY TIME`: Paid customer acquisition (ad-account compliance, creative iteration), supplier stockout/quality failures, and payment-processor chargeback disputes.
- **Blocking step:** On eBay and Amazon, retail-arbitrage dropshipping is explicitly banned (`STATED`). On Shopify, the Terms of Service prohibit accessing or monitoring Shopify Services via automated means (`STATED`), and standalone dropshipping is really a paid-advertising customer-acquisition business with recurring human risk (`OWNER EVERY TIME`).

### 3. Platform Rule on Automated / AI Work

- **eBay Drop Shipping Policy (`STATED`, opened 2026-11-27, [eBay Drop Shipping](https://www.ebay.com/help/selling/posting-items/setting-postage-options/drop-shipping?id=4176)):**

> "Drop shipping, where you fulfill orders directly from a wholesale supplier, is allowed on eBay... However, listing an item on eBay and then purchasing the item from another retailer or marketplace that ships directly to your customer is not allowed on eBay."

- **Amazon Drop Shipping Policy (`STATED`, opened 2026-11-27, [Amazon Drop Shipping Policy](https://sellercentral.amazon.com/help/hub/reference/external/G201808410?language=en_US)):**

> "Purchasing products from a third party, including Amazon or another seller in Amazon's stores, and having that third party ship directly to customers, if the shipment does not identify you as the seller of record or if anyone other than you (including the third party) appears on packing slips, invoices, or external packaging, it is strictly prohibited without exception"

- **Shopify Terms of Service (`STATED`, opened 2026-11-27, [Shopify Terms of Service](https://www.shopify.com/legal/terms)):**

> "You agree not to access the Services or monitor any material or information from the Services using any robot, spider, scraper, or other automated means."

Shopify permits building apps via official Shopify APIs under its API Terms (`STATED`, [Shopify Pricing](https://www.shopify.com/pricing)), but prohibits unauthorized automated access/scraping of the Services.

### 4. Evidence That It Pays

- **Published platform costs (`STATED`):** Shopify Basic costs $29/month (annual) or $39/month (monthly) plus 2.9% + $0.30 per online card sale (`STATED`, [Shopify Pricing](https://www.shopify.com/pricing)), and Shopify's own blog estimates a dropshipping automation app stack costs $100 to $500/month (`STATED`, [Shopify Automated Dropshipping](https://www.shopify.com/blog/automated-dropshipping)).
- **Median store profitability (`UNKNOWN`):** Shopify does not publish median net profit or survival rates for dropshipping stores.

### 5. What It Needs Before the First Dollar

- **Money:** Shopify subscription ($1/month for first 3 months promo, then $29 to $39/month, `STATED`, [Shopify Pricing](https://www.shopify.com/pricing)), domain name, automation apps, and significant paid ad spend to acquire initial customers (`INFERENCE`).
- **Time:** Weeks to months to test products, ads, and supplier reliability.
- **Hard-to-get items:** Profitable customer-acquisition channel (paid ad ROI or organic audience) and a reliable wholesale supplier willing to accept low initial volume.

### 6. Agent Edge vs Bot Crowding

- **Where an agent helps:** Writing product descriptions, syncing inventory feeds, and drafting routine support replies (`INFERENCE`).
- **Why it is crowded:** Commodity dropshipping is saturated with thousands of identical stores bidding on the same Meta/Google/TikTok ad auctions, driving customer-acquisition cost above gross margin (`INFERENCE`).

### 7. Honest Paper Test Before Spending Money

- There is no realistic $0 paper test for paid-ad conversion rates; testing whether strangers will buy a marked-up wholesale item requires live ad spend and live checkout tests (`INFERENCE`).

### 8. Verdict

`OUT`: Retail-to-marketplace dropshipping is explicitly banned on Amazon and eBay, standalone Shopify dropshipping requires paid customer acquisition and recurring chargeback/supplier management (`OWNER EVERY TIME`), and it cannot be honestly paper-tested without spending real ad money.

## Deep Dive 5: In-Game Items and Digital Collectibles (Steam Community Market)

### 1. End-to-End Steps (Nothing to Bank Account)

1. Create a Steam account, enable Steam Guard Mobile Authenticator, and fund Steam Wallet (`OWNER ONCE`).
2. Buy underpriced virtual items (e.g., CS2 skins) on Steam Community Market (`BLOCKED` by Automation ban).
3. Relist items at higher prices on Steam Community Market (`BLOCKED` by Automation ban).
4. Attempt to withdraw Steam Wallet proceeds to a bank account (`BLOCKED` permanently: Steam Wallet funds cannot be withdrawn to a bank or third-party account).
5. Attempt to cash out via third-party skin marketplaces (`BLOCKED`: Valve explicitly states it does not recognize transfers outside Steam and restricts Steam to personal, non-commercial use except where expressly permitted).

### 2. Step Labels and Blocking Step

- **Blocking steps (two hard kills):** (1) Steam explicitly bans all scripts, bots, and non-human-controlled automation; (2) Steam Wallet funds have zero cash value and cannot be withdrawn to a bank account.

### 3. Platform Rule on Automated / AI Work

Steam's Subscriber Agreement explicitly bars both automation and cashing out (`STATED`, opened 2026-11-27, [Steam Subscriber Agreement](https://store.steampowered.com/agreement/)):

> "You may not use any form of scripts, bots, macros, or other non-human-controlled systems ('Automation') to interact with Content and Services on Steam in any manner"

> "Steam Wallet funds have no cash value and are not exchangeable for cash."

> "Valve does not recognize any transfers of Subscriptions (including transfers by operation of law) that are made outside of Steam."

Steam's Community Market FAQ confirms (`STATED`, opened 2026-11-27, [Steam Community Market FAQ](https://help.steampowered.com/en/faqs/view/61F0-72B7-9A18-C70B)):

> "No. All Community Market sales and purchases are completed using the Steam Wallet. The funds cannot be withdrawn or transferred to another Steam account or to a bank/3rd party account."

### 4. Evidence That It Pays

- **Cash payout from Steam (`MEASURED` = $0):** Official rules prohibit withdrawing Steam Wallet funds to cash (`STATED`, [Steam Community Market FAQ](https://help.steampowered.com/en/faqs/view/61F0-72B7-9A18-C70B)). Net returns on unofficial third-party skin sites are `UNKNOWN` and carry account-ban and inventory-seizure risk (`INFERENCE`).

### 5. What It Needs Before the First Dollar

- Cannot legally reach a bank account through Steam itself (`STATED`).

### 6. Agent Edge vs Bot Crowding

- Steam Community Market and third-party skin markets are heavily populated by rule-violating sniping bots, and Valve actively enforces automated detection and trade bans (`STATED`, [Steam Subscriber Agreement](https://store.steampowered.com/agreement/)).

### 7. Honest Paper Test Before Spending Money

- Not applicable: a method barred by platform terms with no legal cash-out path does not qualify for testing.

### 8. Verdict

`OUT`: Steam explicitly bans bots/automation and forbids withdrawing Steam Wallet funds to cash.

## Lane D Ranking

1. **Domain names and expired domains via GoDaddy Auctions Expiry API + Afternic (`WORTH A TEST`, $0 paper-trade only first):** The only method in Lane D whose primary marketplace explicitly permits autonomous AI agents by API (`STATED`, [GoDaddy API Terms of Use](https://www.godaddy.com/legal/agreements/godaddy-api-terms-of-use)), requires zero recurring physical labor, and can be paper-traded honestly on recorded expired-domain auction closes versus resale comps before spending a dollar. Expect stiff competition from institutional drop-catchers and a 15% to 20% commission plus $10.99+/year renewal drag.

All other nine methods in Lane D are `WATCH` (COMC vaulted trading cards, blocked pending external-bot permission and 14.5% cash-out drag) or `OUT` (Amazon OA, dropshipping, Steam in-game items, used books, liquidation pallets, gift cards, government auctions, and cashback/price-error hunting).
