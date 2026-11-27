# 209g: Base rates for small and automated online businesses with verified income

Lane g of deep dive 209. Read on 2026-11-27. The question: which kinds of small automated business have verified income at all, what the median looks like where a full table exists, and what work the human still did. Labels: MEASURED (I opened the page or file today and it says so, or I counted from it), STATED (someone's claim, including vendor and survey figures), INFERENCE (my reasoning), UNKNOWN.

What I did not repeat: [205e](205e_content_and_digital_products.md) already carries RevenueCat's subscription-app bands, TrustMRR's revenue bands and $240 Stripe median, the 112-extension BigIdeasDB set, Acquire.com's 3.9x multiple, Etsy, author surveys and YouTube's entry thresholds. [205i](205i_verified_agent_earners.md) already covers agent-run shops and stores (Andon, Vend), budget-and-earn experiments, agent-business platforms (Polsia), Metaculus bot prizes and hackbot bounties. Those stand; this page adds new tables and points back where needed.

## Bottom line

- Verified income for small automated businesses exists almost only for sellers of software tools. On the largest payment-verified list I found, the high earners sell automation to other people (AI sales agents, outreach, SEO bots, video makers, agent hosting). I found no payment-verified record of a business that is itself autonomous and earns from end customers, such as a faceless channel paid by ads or a self-running store. INFERENCE from the [TrustMRR top 100](https://trustmrr.com/) and the [OpenClaw category](https://trustmrr.com/special-category/openclaw), MEASURED as lists.
- Where a full table exists, the median is small. On TrustMRR, median all-time revenue is $237 for Stripe-connected listings, $380 for RevenueCat, $12 for Polar, $4 for Whop and $3 for DodoPayment ([TrustMRR stats](https://trustmrr.com/stats)). MEASURED, but founders choose to list, so the true median of all attempts is lower. INFERENCE.
- Wider base rates point the same way. Half of Chase customers who sold on online selling platforms took in less than $60 a month in early 2018 ([JPMorgan Chase Institute 2018](https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/institute/pdf/institute-ope-2018.pdf)), and 64.22% of Chrome extensions have fewer than 100 users ([arXiv 2406.12710](https://arxiv.org/html/2406.12710)). MEASURED (the pages say so).
- What the human still did: built the product, found customers, and kept at it. On TrustMRR, revenue tracks time in business (r = 0.45) and domain rating (r = 0.43) more than founder follower count (r = 0.24) ([TrustMRR stats](https://trustmrr.com/stats)). MEASURED. That means marketing and staying power, not the product code, separate earners from the rest. INFERENCE.
- Lane ranking: one method worth a pipeline-only test (a small paid tool sold to businesses with card checkout), one to watch (agent hosting and setup), and nothing else. Neither has a test that proves demand without posting in public.

## Base-rate tables found

### TrustMRR median all-time revenue by payment provider

TrustMRR says "Revenue is verified by reading data directly from your connected payment provider", listing is free and founders choose to list, and "discrepancies of up to 30% can occur depending on the provider and how they handle things like refunds, trials, prorations, and currency conversions" ([TrustMRR FAQ](https://trustmrr.com/faq)). MEASURED. App Store revenue is shown before Apple's commission ([TrustMRR FAQ](https://trustmrr.com/faq)). MEASURED. The site shows $1,999,373,903 of verified revenue across 70M transactions ([TrustMRR stats](https://trustmrr.com/stats)). MEASURED.

All figures below are from [TrustMRR stats](https://trustmrr.com/stats), MEASURED on 2026-11-27.

| Provider | Median all-time revenue | Share of listings | Share at $0 |
|---|---|---|---|
| Stripe | $237 | 53.7% | 24% |
| RevenueCat | $380 | 15.5% | 15% |
| DodoPayment | $3 | 12.7% | 44% |
| Polar | $12 | 8.0% | 42% |
| LemonSqueezy | $113 | 3.6% | 28% |
| Paddle | $18 | 2.4% | 36% |
| Creem | $36 | 1.6% | 35% |
| Whop | $4 | 1.2% | 41% |
| App Store | $130 | 1.1% | 22% |
| Superwall | $2,780 | 0.7% | 8% |
| Shopify | $265 | 0.5% | 43% |
| Razorpay | $124 | 0.5% | 4% |

- Reading: this is all-time revenue, not monthly. Across most providers the middle listing has earned under $400 in its whole life. INFERENCE from the table.
- Superwall listings (a paywall tool for apps that already have traffic) have the highest median, $2,780. INFERENCE: that reflects who uses the tool (apps already earning), not a method anyone can copy.
- Founder follower counts: 52.5% of listings have 0 to 1K followers on X, 11.8% 1K to 10K, 2.3% 10K to 100K, 0.3% over 100K, 33.1% unknown ([TrustMRR stats](https://trustmrr.com/stats)). MEASURED.
- Correlations with revenue: followers r = 0.24 (n = 6,567), time in business r = 0.45 (n = 8,262), domain rating r = 0.43 (n = 7,379) ([TrustMRR stats](https://trustmrr.com/stats)). MEASURED.

### US nonemployer businesses by receipts, 2024

Source: Census Bureau Nonemployer Statistics 2024 file [NS00NONEMP.zip](https://www2.census.gov/programs-surveys/nonemployer-statistics/data/2024/NS00NONEMP.zip), U.S. level, all legal forms. I opened the file and counted the shares. MEASURED. The universe is businesses with no paid employees, subject to federal income tax, with receipts of $1,000 or more ([Census, About NES](https://www.census.gov/programs-surveys/nonemployer-statistics/about.html)). MEASURED. Anyone who earned under $1,000 is not counted, so these are a floor on how many earn little. INFERENCE.

| Industry (2022 NAICS) | Businesses | Under $5,000 | Under $10,000 | Under $25,000 | Median band |
|---|---|---|---|---|---|
| All sectors (00) | 31,985,874 | 22.4% | 37.3% | 60.4% | $10,000 to $24,999 |
| Retail trade (44-45) | 2,178,016 | 28.9% | 46.5% | 68.3% | $10,000 to $24,999 |
| Publishing (513) | 53,900 | 29.8% | 46.1% | 66.2% | $10,000 to $24,999 |
| Broadcasting and content providers (516) | 51,651 | 35.4% | 53.0% | 73.2% | $5,000 to $9,999 |
| Hosting and data processing (518) | 65,001 | 28.5% | 46.8% | 70.1% | $10,000 to $24,999 |
| Web portals and other information services (519) | 49,649 | 31.7% | 47.8% | 68.2% | $10,000 to $24,999 |
| Computer systems design (5415) | 334,886 | 21.5% | 36.0% | 56.6% | $10,000 to $24,999 |
| Independent artists, writers, performers (7115) | 1,115,783 | 35.6% | 54.6% | 76.3% | $5,000 to $9,999 |

- These are gross receipts for a year, not profit. The mean across all sectors is about $58,000, pulled up by the top. INFERENCE (arithmetic: $1,861,386,279 thousand over 31,985,874 businesses in the same file).
- Nothing here says how much of the work was automated. It is the general base rate for one-person businesses that cleared $1,000. INFERENCE.

### Online selling platforms (bank-account data)

- In the first quarter of 2018, "over half of active sellers consistently generate less than $60 per month", and "the top 10 percent of sellers accounted for 80 percent of total earnings in that sector" ([JPMorgan Chase Institute, Online Platform Economy in 2018](https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/institute/pdf/institute-ope-2018.pdf)). MEASURED (the report says so; the data are Chase deposit records).
- In the later study, "Selling platform conditional revenues stayed constant at around $100 throughout the sample timeframe", covering 38 platforms from April 2018 to June 2021 ([JPMorgan Chase Institute, October 2021](https://www.jpmorganchase.com/institute/all-topics/labor-markets-and-workforce/online-platform-economy-through-the-pandemic)). MEASURED. That is the median monthly platform revenue among families who earned anything that month. These are revenues, not profits.

### Chrome extensions (users, not revenue)

- In a full Chrome Web Store dataset from 2020 to 2023, "64.22% of extensions have less than 100 users", with 17.51% at 100 to 1k, 9.70% at 1k to 10k, 4.17% at 10k to 100k, 1.13% at 100k to 1M and 0.27% over 1M ([arXiv 2406.12710](https://arxiv.org/html/2406.12710)). MEASURED (research paper using ChromeStats data).
- A random sample of 2,947 extensions from October 2026 found a median of 13 weekly users and 9.2% at 1,000 or more ([Extenify on DEV](https://dev.to/extensionbooster/chrome-extension-usage-statistics-the-median-is-13-users-2689)). STATED (vendor's own sample; the page gives no revenue data).

### Small independent software (survey)

- MicroConf's 2024 survey of 469 independent SaaS founders, collected in late 2023, says "28% of independent SaaS companies are doing under $1,000 in MRR. That's the single largest group in the entire survey" ([MicroConf](https://microconf.com/founders/0-10k-arr)). STATED (self-reported survey of conference-adjacent founders, so it leans toward survivors).

### Open-revenue pledge lists

- Baremetrics Open Startups, the original open-revenue list, showed only two entries today and no revenue figures in the page text ([Baremetrics Open Startups](https://baremetrics.com/open-startups)). MEASURED. No base rate can be drawn from it.
- TrustMRR has taken over this role with thousands of payment-connected listings. INFERENCE from the [TrustMRR stats](https://trustmrr.com/stats) sample sizes (n up to 8,262).

## Verified earners, sorted by what they sell and how automated

Figures are TrustMRR MRR or 30-day revenue as shown today, payment-connected but self-listed. Descriptions are the founders' own words, so the product claims are STATED; the revenue figure is MEASURED as shown by TrustMRR. Note the FAQ's 30% discrepancy warning above.

1. AI tools that do sales or marketing work for other businesses. AiSDR $170,841, DM Champ $135,927, PROSP $128,005, RankAI $56,533, Bazzly $44,741, SEOBOT $29,210, Postiz $479,441 ([TrustMRR top 100](https://trustmrr.com/)). The product runs automated; the founder built it, sells it and supports customers. INFERENCE.
2. AI video and content makers sold to creators. Gomotion AI $70,525 (pitched for "YouTube automation"), Speel.co $62,951, Vid.AI $54,772, a stealth faceless-channel posting tool $47,529, Produce.so $27,371 ([TrustMRR top 100](https://trustmrr.com/)). These earn from people who want to run automated channels, not from the channels. INFERENCE.
3. Agent hosting and setup (OpenClaw). 186 listings with $602,151 in 30-day revenue, of which Clawdi alone shows about $439k and CreativeClaw about $106k; most of the visible rest show $99 to $4.1k for 30 days ([TrustMRR OpenClaw category](https://trustmrr.com/special-category/openclaw)). MEASURED. Heavily concentrated in two sellers. INFERENCE.
4. Done-for-you services that use AI with people. White Glove Content $53,905 (scripting, AI voiceover and editing for faceless channels), Evergreen Support $25,100 (human support) ([TrustMRR top 100](https://trustmrr.com/)). A person does work for each order. INFERENCE.
5. Courses on making money with AI. AI MONEY GROUP about $23k in 30 days in the OpenClaw category ([TrustMRR OpenClaw category](https://trustmrr.com/special-category/openclaw)). MEASURED. This is a course seller, so its own income claims are never a base rate under the brief. Stripe bars "schemes that claim to offer high rewards for very little effort or up-front work; and sites that promise fast and easy money" ([Stripe restricted businesses](https://stripe.com/legal/restricted-businesses)). MEASURED. OUT for us.
6. Mobile subscription apps. Median all-time revenue $380 on RevenueCat listings and $130 on App Store listings ([TrustMRR stats](https://trustmrr.com/stats)). MEASURED. See [205e](205e_content_and_digital_products.md) for RevenueCat's own bands.
7. Online stores (Shopify). Median $265 all-time, 43% at $0, 0.5% of listings ([TrustMRR stats](https://trustmrr.com/stats)). MEASURED. Wider seller base rate: under $60 a month for half of active sellers in 2018 ([Chase Institute 2018](https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/institute/pdf/institute-ope-2018.pdf)). MEASURED. Agent-run stores are in [205i](205i_verified_agent_earners.md).
8. Browser extensions with outside checkout. No payment table found beyond the 205e set. Users: 64.22% under 100 ([arXiv 2406.12710](https://arxiv.org/html/2406.12710)). MEASURED. Revenue median UNKNOWN.
9. Fully automated end businesses (faceless ad-paid channels, self-running content sites). No payment-verified record found in anything I read today. UNKNOWN. YouTube's own policy now names "AI-generated content made with generic or unoriginal templates giving the impression of mass production" as not allowed to monetize ([YouTube monetization policies](https://support.google.com/youtube/answer/1311392)). MEASURED.

Pattern: categories 1 to 3 have verified income and their delivery is automated, but finding customers was done by a person. Category 9, the thing the owner most wants, has no verified income on record that I found. INFERENCE.

## Deep entries

### A. Small paid tool or API sold to businesses with card checkout

Process from nothing to money in bank:

1. Pick a narrow job a business pays for (for example, a data clean-up or report). AGENT ALONE.
2. Build the tool, a landing page and docs. AGENT ALONE, then SCAFFOLDING for hosting.
3. Open a payment account (Stripe or a merchant of record) with identity check and bank link. OWNER ONCE. INFERENCE (all processors I know require a named person).
4. Wire checkout, license keys or API keys, and usage limits. SCAFFOLDING.
5. Get the first customers to the page: posts, directory listings, outreach. OWNER EVERY TIME in practice, or barred (see rules). This is the blocking step. INFERENCE from the follower and domain-rating correlations on [TrustMRR stats](https://trustmrr.com/stats).
6. Delivery: automatic on payment. AGENT ALONE.
7. Customer messages: an agent can answer most, a person must take disputes and edge cases. SCAFFOLDING plus OWNER EVERY TIME for escalations. INFERENCE.
8. Refunds and chargebacks: a refund rule can be automatic; chargeback replies need the account holder. SCAFFOLDING plus OWNER EVERY TIME. INFERENCE.
9. Payout to bank: automatic after setup. SCAFFOLDING.
10. Tax form: tax identity at account setup, yearly filing by the owner. OWNER ONCE then yearly. INFERENCE.
- Blocking step: step 5, getting customers without a person posting or selling.
- Rules. Stripe's prohibited list mentions AI only as "Any artificial-intelligence generated content that meets the above criteria", under adult content ([Stripe restricted businesses](https://stripe.com/legal/restricted-businesses)). MEASURED. On AI-written software it is silent, so UNKNOWN. Polar lists "AI Content Generation tools (text, image, video, voice);" under "Restricted businesses that require closer review", and prohibits "lead generation, bulk SMS and automated outreach" ([Polar acceptable use](https://polar.sh/docs/merchant-of-record/acceptable-use)). MEASURED. So a tool that does automated outreach for customers is OUT on Polar, and our own automated outreach to find customers is OUT there too.
- Evidence. Median all-time revenue $237 on Stripe listings, 24% at $0 ([TrustMRR stats](https://trustmrr.com/stats)). MEASURED for self-listed businesses. Survey: 28% under $1,000 MRR as the largest group ([MicroConf](https://microconf.com/founders/0-10k-arr)). STATED. True median of all launches is below $237 all-time. INFERENCE.
- Needs before first dollar: a domain and hosting, a verified payment account, and an audience or channel that will see the page. Money small (INFERENCE); time to first sale UNKNOWN.
- Why an agent might be better: it can build and maintain many narrow tools cheaply and answer support around the clock. Already crowded: TrustMRR alone shows thousands of listings, mostly small. INFERENCE.
- Honest test before money: a full dry run in the processor's test mode proves the pipeline (checkout, key delivery, refund, webhook) without real money. INFERENCE. No honest test of demand exists without posting in public, which the rules for now forbid.
- Verdict: WORTH A TEST, pipeline dry run only; demand stays UNKNOWN until the owner allows public posting.

### B. Agent hosting and setup (OpenClaw and similar)

Process from nothing to money in bank:

1. Build a one-click hosted setup for an open agent framework. AGENT ALONE plus SCAFFOLDING (servers).
2. Payment account and identity. OWNER ONCE.
3. Listing and launch posts. OWNER EVERY TIME in practice. Blocking step. INFERENCE.
4. Provisioning per customer: automatic. SCAFFOLDING.
5. Support for broken installs and keys: frequent, technical. Agent first, OWNER EVERY TIME for escalations. INFERENCE.
6. Refunds, payout, tax: as in entry A.
- Rules: same payer rules as A; Stripe silent on AI-built hosting, so UNKNOWN ([Stripe restricted businesses](https://stripe.com/legal/restricted-businesses)). MEASURED as silent. The framework's trademark and terms for resellers: UNKNOWN, not read today.
- Evidence: 186 listings, $602,151 in 30 days, most of it in Clawdi (about $439k) and CreativeClaw (about $106k); the visible small sellers show $99 to $4.1k for 30 days ([TrustMRR OpenClaw category](https://trustmrr.com/special-category/openclaw)). MEASURED. Clawdi shows MRR near $1.8k, so most of its 30-day revenue is one-off. MEASURED from the same page. Median per listing UNKNOWN (only 30 of 186 shown). An October reading by a third party put 158 of 188 listings at about $37 each for 30 days ([doesitpay](https://doesitpay.org/autonomous-ai-agent-income/research/)). STATED.
- Needs before first dollar: server money per customer, a payment account, and timing (this rides one framework's popularity). INFERENCE.
- Why an agent might be better: setup and monitoring are scriptable. Already crowded: 186 sellers for one framework. INFERENCE.
- Honest test: a dry run on our own machine, provisioning fake customers in processor test mode. INFERENCE. No demand test without posting.
- Verdict: WATCH. Real money exists but sits with two sellers; a new entrant's median looks tiny.

### C. Fully automated faceless video channel paid by YouTube ads

Process from nothing to money in bank:

1. Create a Google account and channel. OWNER ONCE.
2. Generate and upload videos on a schedule. AGENT ALONE plus SCAFFOLDING.
3. Reach the Partner Program thresholds (in [205e](205e_content_and_digital_products.md)). Time, not a step anyone can do.
4. Apply; YouTube reviewers check how the content was made ([YouTube monetization policies](https://support.google.com/youtube/answer/1311392)). OWNER ONCE, and the blocking step.
5. AdSense payout and tax info. OWNER ONCE.
6. Comments and claims. Agent first, OWNER EVERY TIME for disputes. INFERENCE.
- Rules: content must "Not be mass-produced, generic, repetitive, or manipulative", and not allowed to monetize is "AI-generated content made with generic or unoriginal templates giving the impression of mass production without adding the creator's original, authentic insights or perspective"; tools are allowed if "the final product must still demonstrate your creative vision" ([YouTube monetization policies](https://support.google.com/youtube/answer/1311392)). MEASURED. A channel with no human creative input is exactly what the rule describes. INFERENCE.
- Evidence: no payment-verified faceless channel found; the verified money is with the tool sellers in category 2 above ([TrustMRR top 100](https://trustmrr.com/)). MEASURED as a list. Content-provider nonemployers that cleared $1,000 have a median in the $5,000 to $9,999 a year band ([Census NES 2024](https://www2.census.gov/programs-surveys/nonemployer-statistics/data/2024/NS00NONEMP.zip)). MEASURED, not automation-specific.
- Needs: months of uploads before review; the review itself.
- Why an agent might be better: volume. That is what the policy targets, and the channel is crowded with the exact tools listed above. INFERENCE.
- Honest test: none that predicts the monetization review before months of public uploads.
- Verdict: OUT. The platform's own rule bars the fully automated form, and the human-creative form is not autonomous.

## Lane ranking

1. Small paid tool or API with card checkout: WORTH A TEST as a test-mode pipeline dry run only. Median verified outcome is $237 all-time on Stripe listings ([TrustMRR stats](https://trustmrr.com/stats)), and getting customers needs a person.
2. Agent hosting and setup: WATCH. Concentrated in two sellers ([TrustMRR OpenClaw category](https://trustmrr.com/special-category/openclaw)).
3. None. No other kind of small automated business I read has verified income that an agent could earn without a person finding the customers.

Partner note: the honest answer to the owner's question is that payment-verified "automated businesses" are mostly people selling automation to other people. The code runs alone; the selling does not. INFERENCE.
