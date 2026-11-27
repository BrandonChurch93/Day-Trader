# Deep Dive 209a: Digital Goods Marketplaces

Date: 2026-11-27
Lane: Digital goods sold on marketplaces (design templates, print-on-demand, stock photos, video, music and 3D assets, self-published books and low-content books, fonts, printables, game assets, courses, prompt and GPT stores, theme and plugin stores).
Question: Can an AI agent plus one-time owner scaffolding earn reliable money autonomously on digital goods marketplaces, verified against each marketplace's own AI-content and payout rules opened today?

## Lane Summary and Screening of All Nine Methods

People earn in this lane by uploading reusable digital files (code packages, themes, books, images, audio, print-on-demand designs, templates, courses, or prompts) to marketplaces that already hold buyer search traffic and handle checkout. Under the 2026-11-27 brief, one-time setup of accounts, tax forms, payout rails, and build tooling is allowed (`OWNER ONCE` and `SCAFFOLDING`), while recurring human labor (`OWNER EVERY TIME`), platform bans on AI or bot-generated work, and untestable economics still disqualify a method.

Across the nine distinct methods in this lane, four are blocked outright or effectively closed by marketplace AI policies or lack of published payout programs, three fail on severe bot crowding or recurring human labor, and only one (narrow, test-verified game engine code utilities) merits an honest zero-cash pilot.

| Method | Primary marketplaces checked today | AI-content rule opened today | Payout rule opened today | Screen result |
|---|---|---|---|---|
| 1. Game engine code utilities and 3D assets | Unity Asset Store, Fab (Epic Games), TurboSquid | Unity allows disclosed AI with value check ([Unity Support](https://support.unity.com/hc/en-us/articles/16456407029524-Can-I-publish-and-sell-content-generated-with-AI-on-the-Asset-Store)); Fab notes AI disclosure controls ([Unreal Engine](https://www.unrealengine.com/news/fab-2025-year-in-review)); TurboSquid bans AI ([TurboSquid](https://www.turbosquid.com/help/en/articles/12633683-turbosquid-s-policy-on-publishing-ai-generated-content)) | Fab pays 88% with $100 min at ~30 days ([Epic Games Dev](https://dev.epicgames.com/documentation/fab/publisher-get-started-in-fab?lang=en-US)); Unity pays 70% monthly via PayPal or quarterly wire above $250 ([Unity Legal](https://unity.com/legal/asset-store-provider-agreement)) | Deep dive (best candidate) |
| 2. Theme and plugin stores | Shopify Theme Store, Envato Market (ThemeForest, CodeCanyon) | Envato bans AI as standalone or primary item ([Envato Author Support](https://help.author.envato.com/hc/en-us/articles/13313674070681-AI-generated-content-policy-for-Market-and-Elements)); Shopify Theme Store AI rule is `UNKNOWN` on revenue-share page ([Shopify Dev](https://shopify.dev/docs/storefronts/themes/store/revenue-share)) | Shopify Theme Store pays 85% of gross sales (15% rev share) minus 2.9% processing, $0 listing fee ([Shopify Dev](https://shopify.dev/docs/storefronts/themes/store/revenue-share)) | Deep dive |
| 3. Self-published eBooks and low-content books | Amazon KDP | Allows AI-generated text, images, and translations with mandatory disclosure ([Amazon KDP](https://kdp.amazon.com/en_US/help/topic/G200672390)) | 35% or 70% minus delivery costs for eBooks ([Amazon KDP Royalties](https://kdp.amazon.com/en_US/help/topic/G200644210)); paid ~60 days after month end, $0 EFT min / $100 wire or check min ([Amazon KDP Payouts](https://kdp.amazon.com/en_US/help/topic/GK2MKZUL6U3SFBPZ)) | Deep dive |
| 4. Stock photos, illustrations, video, and music | Adobe Stock, Shutterstock, Pond5, Envato (VideoHive, AudioJungle) | Adobe Stock allows labeled generative AI but bans similar prompt iterations ([Adobe Stock](https://helpx.adobe.com/stock/contributor/submit-your-content/submit-generative-ai-content/generative-ai-content-guidelines.html)); Shutterstock ([Shutterstock](https://submit.shutterstock.com/help/en/articles/10594622-content-policy-updates-ai-generated-content)), Pond5 ([Pond5](https://www.pond5.com/help/en/articles/10086182-does-pond5-allow-ai-generated-content-for-licensing)), and Envato ([Envato Author Support](https://help.author.envato.com/hc/en-us/articles/13313674070681-AI-generated-content-policy-for-Market-and-Elements)) ban AI | Adobe Stock pays $25 min after 45-day wait via PayPal, Payoneer, or Skrill ([Adobe Stock Payment](https://helpx.adobe.com/stock/contributor/payments-earnings/payment-taxes/payment-requirements.html)) | Deep dive |
| 5. Prompt marketplaces and GPT stores | PromptBase, OpenAI GPT Store | PromptBase exists for prompts (no separate AI ban found; `UNKNOWN` on automated bulk upload); OpenAI GPT Store allows publishing by verified builders on eligible plans ([OpenAI Help](https://help.openai.com/en/articles/8798878-sharing-and-publishing-gpts)) | PromptBase pays 80% on marketplace sales, 100% on referrals, $1.25 per Select download ([PromptBase](https://promptbase.com/help/fees)); OpenAI GPT Store publishes no builder payout rate or revenue-share program ([OpenAI Help](https://help.openai.com/en/articles/8798878-sharing-and-publishing-gpts)) | Deep dive |
| 6. Design templates and printables | Etsy, Envato GraphicRiver | Etsy explicitly bans bot-generated content, mass-automated listings without individual human oversight, AI prompt bundles, and AI-generated functional guides ([Etsy Handbook](https://www.etsy.com/seller-handbook/article/1275449912004), [Etsy Nov 2026 Update](https://www.etsy.com/seller-handbook/article/1522733284810)); Envato bans AI primary items ([Envato Author Support](https://help.author.envato.com/hc/en-us/articles/13313674070681-AI-generated-content-policy-for-Market-and-Elements)) | Etsy charges $0.20 listing fee plus 6.5% transaction fee plus Etsy Payments fee ([Etsy Fees](https://www.etsy.com/legal/fees/)) | `OUT` (rule bars automation) |
| 7. Print-on-demand apparel and merch | Redbubble, TeePublic (Articore Group) | Articore deploys AI duplicate detection across its library to filter repetitive uploads ([Articore FY24 Report](https://www.articore.com/FormBuilder/_Resource/_module/VFV_6YfHZ0qKveaD4XGZZA/files/presentations/FY24_Annual_Report.pdf)); explicit AI-upload rule `UNKNOWN` | `MEASURED`: $59 million total artist earnings across 0.7 million selling artists in FY24, an arithmetic mean of about $84 per selling artist per year ([Articore FY24 Report](https://www.articore.com/FormBuilder/_Resource/_module/VFV_6YfHZ0qKveaD4XGZZA/files/presentations/FY24_Annual_Report.pdf)) | `OUT` (saturated, ~$84/yr mean) |
| 8. Online courses | Udemy | Udemy's 2025 10-K does not state an AI ban and notes providing AI-assisted authoring tools to instructors ([Udemy 2025 10-K](https://www.sec.gov/Archives/edgar/data/1607939/000160793926000034/udmy-20251231.htm)); standalone AI-video rule `UNKNOWN` | `MEASURED`: $168 million paid across 91,000+ instructors in 2025 (~$1,846/yr mean), heavily skewed with top 11 instructors each over $1M and only ~1,600 above home-country average income ([Udemy 2025 10-K](https://www.sec.gov/Archives/edgar/data/1607939/000160793926000034/udmy-20251231.htm)) | `OUT` (extreme skew, high Q&A and video upkeep) |
| 9. Fonts and typefaces | Envato GraphicRiver, specialty font foundries | Envato bans AI-generated primary assets ([Envato Author Support](https://help.author.envato.com/hc/en-us/articles/13313674070681-AI-generated-content-policy-for-Market-and-Elements)); independent foundry AI rules `UNKNOWN` | Specialty font marketplace base rates `UNKNOWN` | `OUT` (high manual glyph/kerning QA and Envato ban) |

## Deep Dive 1: Game Engine Code Utilities on Unity Asset Store and Fab

Focus on deterministic code tools, editor scripts, shaders, and procedural utilities rather than raw AI-generated 3D art, because code packages can be compiled and tested automatically while TurboSquid already bans AI-generated 3D models ([TurboSquid](https://www.turbosquid.com/help/en/articles/12633683-turbosquid-s-policy-on-publishing-ai-generated-content)).

1. Process from nothing to bank account:
1. Create a publisher account, complete Trader Verification, agree to the distribution agreement, submit tax forms, and connect the payout provider (PayPal or wire on Unity; third-party payout provider on Fab) ([Epic Games Dev](https://dev.epicgames.com/documentation/fab/publisher-get-started-in-fab?lang=en-US), [Unity Legal](https://unity.com/legal/asset-store-provider-agreement)).
2. Research recurring developer pain points in Unity or Unreal Engine issue trackers and forums to select a narrow utility tool (for example, an asset-import validator, batch LOD optimizer, or automated UI layout checker).
3. Write the C# or C++ plugin source code, sample scene, unit tests, and Markdown/PDF documentation.
4. Build and run automated compile and unit-test checks across supported Unity or Unreal Engine versions in headless CI.
5. Package the asset, generate store screenshots from the real running engine, write the listing description with transparent AI disclosure if AI tools generated code or art, and submit to the marketplace review queue.
6. Pass the human marketplace review and address any rejection notes (API compliance, folder structure, or licensing checks).
7. Marketplace handles automated checkout, file hosting, and digital delivery to buyers.
8. Monitor buyer support emails, bug reports, and engine-version updates; issue patches for breaking Unity or Unreal releases.
9. Handle refund or chargeback disputes (Unity may refund assets priced under $50 and charge them back to the provider at its discretion) ([Unity Legal](https://unity.com/legal/asset-store-provider-agreement)).
10. Receive payouts (monthly via PayPal or quarterly wire above $250 on Unity; ~30 days after month end once balance reaches $100 on Fab) and log 1099/tax records ([Unity Legal](https://unity.com/legal/asset-store-provider-agreement), [Epic Games Dev](https://dev.epicgames.com/documentation/fab/publisher-get-started-in-fab?lang=en-US)).

2. Automation breakdown by step:
Step 1 (account, Trader Verification, tax form, bank/PayPal): `OWNER ONCE`.
Step 2 (pain-point research and tool spec): `AGENT ALONE`.
Step 3 (writing code, tests, and docs): `AGENT ALONE`.
Step 4 (headless Unity/Unreal build and test verification): `SCAFFOLDING`.
Step 5 (packaging, real-engine screenshots, listing upload): `SCAFFOLDING` for packaging and screenshots; `OWNER ONCE` or `OWNER EVERY TIME` if publisher portal upload lacks an official API and enforces human CAPTCHA/2FA on submission.
Step 6 (responding to marketplace review feedback): `AGENT ALONE` for code fixes; `OWNER EVERY TIME` only if human portal resubmission is required.
Step 7 (checkout and digital delivery): handled by marketplace (`SCAFFOLDING` = none needed).
Step 8 (bug fixes, engine upgrades, buyer support email): `AGENT ALONE` with `SCAFFOLDING` (automated email triage and PR/test pipeline), with `OWNER EVERY TIME` only for novel legal/refund escalations.
Step 9 (refund/chargeback disputes): `OWNER EVERY TIME` when a dispute is escalated, though low-frequency for tested utilities.
Step 10 (payout receipt and annual taxes): `OWNER ONCE` for payout rails; annual tax filing is standard business overhead.
Primary blocker to 100% unattended operation: manual publisher portal submission/2FA on each new listing and occasional human-escalated refund or engine-policy disputes.

3. Platform AI-content rule (opened today):
Unity Asset Store (`MEASURED`): "The Asset Store allows content generated with AI/ML (Artificial Intelligence/Machine Learning) systems to be published, sold, or distributed for free." It adds: "All packages that include any AI/ML (Artificial Intelligence/Machine Learning) generated content, including images or other AI content, must transparently disclose this information within the product listing." Submissions must also "have significant value and usability in a professional development pipeline" and are rejected if they plagiarize or lack significant value ([Unity Support](https://support.unity.com/hc/en-us/articles/16456407029524-Can-I-publish-and-sell-content-generated-with-AI-on-the-Asset-Store)).
Fab (`MEASURED`): Epic's Fab 2025 Year in Review states: "We've made it easier to report incorrect product listings and have strengthened how we handle AI disclosures and spam prevention" ([Unreal Engine](https://www.unrealengine.com/news/fab-2025-year-in-review)). Fab's Publisher Get Started page does not state an AI ban ([Epic Games Dev](https://dev.epicgames.com/documentation/fab/publisher-get-started-in-fab?lang=en-US)), so disclosed, high-utility tools are permitted, while spammy bulk AI uploads are policed (`INFERENCE`).
TurboSquid (`MEASURED`): `OUT`. "TurboSquid will not accept content uploaded and sold on our marketplace that is generated by AI" ([TurboSquid](https://www.turbosquid.com/help/en/articles/12633683-turbosquid-s-policy-on-publishing-ai-generated-content)).

4. Evidence that it pays:
`MEASURED` (Fab official 2025 totals): Epic Games reported that creators earned "more than $24 million" in 2025 across "more than 20,000" publishers and "over 420,000 live listings" ([Unreal Engine](https://www.unrealengine.com/news/fab-2025-year-in-review)). That implies an arithmetic mean of roughly $1,200 per publisher per year across all publishers (`INFERENCE`), though median earnings and the share of publishers earning $0 are `UNKNOWN`. Event sales generated up to 50% of a month's revenue on average, and flash sales contributed 25% ([Unreal Engine](https://www.unrealengine.com/news/fab-2025-year-in-review)).
`MEASURED` (payout tables): Fab pays "88% of the revenue generated by your product sales" approximately 30 days after month end once unpaid earnings reach $100 USD (or after one year regardless of amount) ([Epic Games Dev](https://dev.epicgames.com/documentation/fab/publisher-get-started-in-fab?lang=en-US)). Unity pays "70% of the sales price" less refunds, bank fees, and taxes, monthly via PayPal or quarterly by wire above $250 ([Unity Legal](https://unity.com/legal/asset-store-provider-agreement)).
Unity Asset Store median publisher earnings and base rate: `UNKNOWN`.

5. What it needs before the first dollar:
Money: $0 listing fee on both Unity Asset Store and Fab (`MEASURED` for Fab via [Epic Games Dev](https://dev.epicgames.com/documentation/fab/publisher-get-started-in-fab?lang=en-US); Unity personal engine license is free below revenue caps). Optional $0 to minimal compute cost for headless engine CI.
Time: 1 to 3 weeks to build, test, document, and clear the marketplace's human submission review queue (`INFERENCE`).
Hard-to-get prerequisites: passing human technical review (clean compile, no warnings, real screenshots), earning initial 5-star reviews to overcome cold start, and participating in official marketplace event sales that drive up to half of monthly volume on Fab ([Unreal Engine](https://www.unrealengine.com/news/fab-2025-year-in-review)).

6. Agent advantage vs. automation crowding:
Raw AI-generated 3D art, textures, and icon packs are heavily crowded with automated slop, which is why Fab strengthened spam prevention ([Unreal Engine](https://www.unrealengine.com/news/fab-2025-year-in-review)) and Unity explicitly rejects low-value AI art ([Unity Support](https://support.unity.com/hc/en-us/articles/16456407029524-Can-I-publish-and-sell-content-generated-with-AI-on-the-Asset-Store)). By contrast, clean, well-tested C# and C++ editor utilities have a concrete verification loop (compiler + unit tests + sample project), and an agent can maintain compatibility across new Unity/Unreal versions faster than a solo human developer (`INFERENCE`).

7. Honest test before spending money:
Build one narrow Unity editor utility (for example, an automated asset/material dependency and build-size auditor), compile and run automated tests against two Unity LTS versions in a private repo, and release a free open-source lite version on GitHub or as a $0 Asset Store package first. Measure real organic installs, GitHub issues, and user retention for 30 to 60 days before spending a dollar on ads or building a paid Pro tier.

8. Verdict:
`WORTH A TEST` for narrow, test-verified Unity/Unreal code utilities (not AI 3D art), because the rules explicitly allow disclosed AI, payout splits are 70% to 88%, listing cost is $0, and product quality can be proven in automated engine tests before launch.

## Deep Dive 2: Storefront Themes on Shopify Theme Store

Envato's ThemeForest and CodeCanyon are `OUT` because Envato explicitly bars AI-generated content as a standalone item or primary component ([Envato Author Support](https://help.author.envato.com/hc/en-us/articles/13313674070681-AI-generated-content-policy-for-Market-and-Elements)). Shopify Theme Store remains the main high-ticket code storefront marketplace to evaluate.

1. Process from nothing to bank account:
1. Register a Shopify Partner account, verify business email and business details, and set up Hyperwallet payouts and tax forms ([Shopify Dev](https://shopify.dev/docs/storefronts/themes/store/revenue-share)).
2. Design and code a complete Shopify Online Store 2.0 theme (Liquid, CSS, JS, JSON templates, accessibility, performance, and multi-preset demo stores) meeting Shopify Theme Store requirements.
3. Run automated Lighthouse performance, accessibility, Liquid linter, and Playwright browser checks on a free Shopify development store.
4. Submit the theme package and demo stores for Shopify Theme Store review ($0 submission fee) ([Shopify Dev](https://shopify.dev/docs/storefronts/themes/store/revenue-share)).
5. Iterate through Shopify's strict manual design, UX, and code review rounds until approved.
6. Shopify hosts the listing, lets merchants run free trials, and bills merchants automatically when they publish or edit theme code.
7. Provide ongoing merchant technical support, bug fixes, and Shopify platform-update patches.
8. Handle billing adjustments and monitor Partner payouts via the Payouts dashboard or Shopify Partner API ([Shopify Dev](https://shopify.dev/docs/storefronts/themes/store/revenue-share)).

2. Automation breakdown by step:
Step 1 (Partner account, business verification, Hyperwallet, tax forms): `OWNER ONCE`.
Step 2 (theme architecture, Liquid/JS/CSS coding, demo-store setup): `AGENT ALONE` for code; `OWNER EVERY TIME` if subjective visual polish requires human design sign-off to clear Shopify's curated bar.
Step 3 (Lighthouse, accessibility, Playwright QA): `SCAFFOLDING`.
Step 4 (submission): `OWNER ONCE` per theme via Partner Dashboard.
Step 5 (curated UX/design review rounds): `AGENT ALONE` for code fixes, `OWNER EVERY TIME` if reviewer feedback requires human visual/brand judgment.
Step 6 (checkout and delivery): handled by Shopify.
Step 7 (merchant support and updates): `SCAFFOLDING` + `AGENT ALONE` for documentation/triage/patches; `OWNER EVERY TIME` when merchants ask for custom store debugging in private admin panels.
Step 8 (payouts and accounting): `OWNER ONCE` (Partner API supports automated reporting).
Primary blocker: Shopify's strict manual curation queue and ongoing merchant support expectations.

3. Platform AI-content rule (opened today):
Shopify Theme Store (`UNKNOWN`): Shopify's official Theme Store revenue-share documentation makes no mention of an AI-content ban or disclosure rule ([Shopify Dev](https://shopify.dev/docs/storefronts/themes/store/revenue-share)). Because the rule is silent on that page rather than explicitly permitting fully autonomous AI submissions, status is `UNKNOWN` and would require checking Shopify's full Theme Store requirements before building.
Envato ThemeForest and CodeCanyon (`MEASURED`): `OUT`. "You may not publish or submit AI-generated content, either as a standalone item or as the primary component of your item's final download file" ([Envato Author Support](https://help.author.envato.com/hc/en-us/articles/13313674070681-AI-generated-content-policy-for-Market-and-Elements)).

4. Evidence that it pays:
`MEASURED` (payout table): Shopify states "there are no fees for submitting themes for listing," "total theme revenues are subject to a 15% revenue share" calculated on gross sales (meaning developers keep 85% before payment processing), and "All billing is subject to a 2.9% processing fee and applicable sales tax" ([Shopify Dev](https://shopify.dev/docs/storefronts/themes/store/revenue-share)).
Median theme developer earnings, approval rate, and base rate of accepted themes: `UNKNOWN` (no official Shopify median earnings table was found today).

5. What it needs before the first dollar:
Money: $0 listing fee ([Shopify Dev](https://shopify.dev/docs/storefronts/themes/store/revenue-share)) and free development store; domain and support helpdesk cost minimal.
Time: months of build and multiple review cycles to meet Shopify's high design and performance standards (`INFERENCE`).
Hard-to-get prerequisites: passing Shopify's manual Theme Store approval gate (which rejects generic or derivative themes) and earning initial merchant reviews.

6. Agent advantage vs. automation crowding:
Because Shopify manually curates the Theme Store, it is far less flooded with low-effort bots than KDP or stock sites (`INFERENCE`). Agents excel at Liquid boilerplate, accessibility compliance, and automated browser/Lighthouse regression testing, but visual design originality remains the hardest part to automate cleanly.

7. Honest test before spending money:
Build a complete theme on a free Shopify development store, run Shopify's automated Theme Check linter and Lighthouse performance/accessibility audits locally, and verify whether it passes every published technical requirement before submitting to the review queue ($0 cash at risk).

8. Verdict:
`WATCH` because the 85% revenue share and $0 listing fee are strong and testable at zero cash, but Shopify's explicit AI policy is `UNKNOWN` here and the manual design-curation gate plus merchant support burden make it slower and less autonomous than narrow Unity/Unreal code utilities.

## Deep Dive 3: Self-Published eBooks and Low-Content Books on Amazon KDP

1. Process from nothing to bank account:
1. Create an Amazon KDP account, complete identity verification, submit tax interview (W-9), and link a bank account for EFT direct deposit ([Amazon KDP Payouts](https://kdp.amazon.com/en_US/help/topic/GK2MKZUL6U3SFBPZ)).
2. Research underserved book niches and buyer search demand without violating trademarks or existing copyrights.
3. Draft manuscript text, cover design, and interior layout (EPUB or print-ready PDF).
4. Run automated formatting, link, spelling, and factual verification checks.
5. Upload title metadata, manuscript, and cover in the KDP portal, and complete the mandatory AI-generated content disclosure questionnaire ([Amazon KDP](https://kdp.amazon.com/en_US/help/topic/G200672390)).
6. Pass KDP automated and manual content/IP review (typically up to 72 hours).
7. Amazon handles checkout, Kindle delivery, print-on-demand fulfillment, customer service, and returns automatically.
8. Monitor sales, reviews, and return rates; update files if defects are reported.
9. Receive monthly royalty EFT payouts approximately 60 days after the end of the month in which sales were reported ([Amazon KDP Payouts](https://kdp.amazon.com/en_US/help/topic/GK2MKZUL6U3SFBPZ)).

2. Automation breakdown by step:
Step 1 (KDP account, identity, tax interview, bank): `OWNER ONCE`.
Step 2 (niche research): `AGENT ALONE`.
Step 3 (drafting, cover, EPUB/PDF layout): `AGENT ALONE` + `SCAFFOLDING`.
Step 4 (EPUB/PDF validation and fact-checking): `SCAFFOLDING`.
Step 5 (KDP portal upload and mandatory AI disclosure): `OWNER EVERY TIME` (KDP has no official public publishing API, and automated browser bots logging into Amazon seller portals risk account termination).
Step 6 (KDP review): handled by Amazon.
Step 7 (checkout, delivery, returns): handled by Amazon.
Step 8 (review monitoring and file updates): `AGENT ALONE` for monitoring/revisions, `OWNER EVERY TIME` for portal re-upload.
Step 9 (payouts): automatic EFT after `OWNER ONCE` setup.
Primary blocker: no official publishing API (requiring human upload per title) and near-zero organic discoverability without paid Amazon Ads or an external audience.

3. Platform AI-content rule (opened today):
Amazon KDP (`MEASURED`): "We require you to inform us of AI-generated content (text, images, or translations) when you publish a new book or make edits to and republish an existing book through KDP." KDP defines AI-generated as "text, images, or translations created by an AI-based tool... even if you applied substantial edits afterwards," and states: "You are responsible for verifying that all AI-generated and/or AI-assisted content adheres to all content guidelines, including by complying with all applicable intellectual property rights" ([Amazon KDP](https://kdp.amazon.com/en_US/help/topic/G200672390)).

4. Evidence that it pays:
`MEASURED` (royalty and payout tables): KDP pays 35% of list price without VAT, or 70% of list price without VAT minus delivery costs (averaging $0.06 per unit) in eligible 70% territories ([Amazon KDP Royalties](https://kdp.amazon.com/en_US/help/topic/G200644210)). Royalties are paid monthly "about 60 days after the end of the month in which the sale was reported," with no minimum threshold for direct deposit (EFT) and a $100 USD minimum for wire or check payments ([Amazon KDP Payouts](https://kdp.amazon.com/en_US/help/topic/GK2MKZUL6U3SFBPZ)).
Median KDP author earnings and base rate of titles earning more than $0: `UNKNOWN` (Amazon does not publish an official median royalty table).

5. What it needs before the first dollar:
Money: $0 to publish on KDP (`MEASURED`), though competing in crowded categories usually pushes publishers toward paid Amazon Ads (`INFERENCE`).
Time: days to produce a book, plus a 60-day payout lag after the first sale month ([Amazon KDP Payouts](https://kdp.amazon.com/en_US/help/topic/GK2MKZUL6U3SFBPZ)).
Hard-to-get prerequisites: organic search ranking, verified buyer reviews, and an external audience or ad budget.

6. Agent advantage vs. automation crowding:
KDP low-content books (journals, planners, coloring books) and generic AI eBooks are among the most heavily bot-flooded markets on the internet (`INFERENCE`). An agent has no edge in low-content spam. The only plausible agent edge is structured, fact-checked technical reference or workflow guides where accuracy and rapid updating matter, and even there discoverability without ads is hard.

7. Honest test before spending money:
Publish 1 to 3 disclosed, high-accuracy niche technical eBooks at $0 ad spend and measure organic impressions, page reads, and net units sold over 90 days. If organic sales are zero without paid ads, stop immediately with $0 lost.

8. Verdict:
`WATCH` only for disclosed, high-accuracy technical reference eBooks tested at $0 ad spend; `OUT` for low-content books and generic AI publishing because of extreme bot crowding and manual portal upload friction.

## Deep Dive 4: Generative AI Stock Assets on Adobe Stock

Shutterstock ([Shutterstock](https://submit.shutterstock.com/help/en/articles/10594622-content-policy-updates-ai-generated-content)), Pond5 ([Pond5](https://www.pond5.com/help/en/articles/10086182-does-pond5-allow-ai-generated-content-for-licensing)), and Envato ([Envato Author Support](https://help.author.envato.com/hc/en-us/articles/13313674070681-AI-generated-content-policy-for-Market-and-Elements)) all explicitly ban AI-generated stock photos, videos, and audio/music (`OUT`). Adobe Stock is the only major stock marketplace checked today that still allows generative AI uploads.

1. Process from nothing to bank account:
1. Create an Adobe Stock Contributor account, verify identity, submit a tax form (otherwise Adobe withholds 30%), and link PayPal, Payoneer, or Skrill ([Adobe Stock Payment](https://helpx.adobe.com/stock/contributor/payments-earnings/payment-taxes/payment-requirements.html)).
2. Generate commercial-safe images or illustrations, inspect for artifacts and IP/brand resemblance, and filter out near-duplicates.
3. Upload assets via SFTP or Contributor Portal, add titles/keywords, and check the mandatory "Created using generative AI tools" checkbox (and "People and Property are fictional" when applicable) ([Adobe Stock](https://helpx.adobe.com/stock/contributor/submit-your-content/submit-generative-ai-content/generative-ai-content-guidelines.html)).
4. Wait for Adobe Stock moderation approval.
5. Adobe handles licensing, checkout, and buyer delivery automatically.
6. Wait at least 45 days after the first sale and accumulate at least US $25 in royalties, then request payout ([Adobe Stock Payment](https://helpx.adobe.com/stock/contributor/payments-earnings/payment-taxes/payment-requirements.html)).

2. Automation breakdown by step:
Step 1 (account, identity, tax form, PayPal/Payoneer/Skrill): `OWNER ONCE`.
Step 2 (generation, upscaling, artifact/IP screening): `AGENT ALONE` + `SCAFFOLDING`.
Step 3 (upload, keywording, mandatory AI checkboxes): `SCAFFOLDING` for SFTP upload; `OWNER EVERY TIME` or brittle UI automation for final portal metadata and AI-checkbox submission.
Step 4 (moderation): handled by Adobe.
Step 5 (checkout and delivery): handled by Adobe.
Step 6 (payout request): `OWNER EVERY TIME` (manual payout button once above $25).
Primary blocker: Adobe's ban on submitting multiple similar prompt iterations and severe per-asset dilution from millions of competing AI uploads.

3. Platform AI-content rule (opened today):
Adobe Stock (`MEASURED`): "You must always select the Created using generative AI tools checkbox, regardless of whether a release is required or not, for all content created with generative AI." Under "Don'ts," Adobe explicitly forbids contributors to "Submit multiple versions from the same prompt or similar iterations of a prompt," warning: "Violations of this policy may result in the removal of content or the termination of the account" ([Adobe Stock](https://helpx.adobe.com/stock/contributor/submit-your-content/submit-generative-ai-content/generative-ai-content-guidelines.html)).
Shutterstock (`MEASURED`): `OUT`. "Shutterstock will not allow AI-generated content to be submitted by contributors for licensing on our platform" ([Shutterstock](https://submit.shutterstock.com/help/en/articles/10594622-content-policy-updates-ai-generated-content)).
Pond5 (`MEASURED`): `OUT`. "At this time, Pond5 does not allow the submission of AI-generated content in our Marketplace" ([Pond5](https://www.pond5.com/help/en/articles/10086182-does-pond5-allow-ai-generated-content-for-licensing)).

4. Evidence that it pays:
`MEASURED` (payout requirements): Contributors must reach "US $25 in royalties" and wait "45 days since first Adobe Stock sale" before requesting payout to PayPal, Payoneer, or Skrill; without a valid tax form, Adobe withholds 30% ([Adobe Stock Payment](https://helpx.adobe.com/stock/contributor/payments-earnings/payment-taxes/payment-requirements.html)).
Median contributor earnings and average earnings per AI image uploaded: `UNKNOWN`.

5. What it needs before the first dollar:
Money: $0 listing fee, plus image-generation API/compute costs (`INFERENCE`).
Time: moderation queues plus a mandatory 45-day waiting period after the first sale and a $25 minimum payout floor ([Adobe Stock Payment](https://helpx.adobe.com/stock/contributor/payments-earnings/payment-taxes/payment-requirements.html)).
Hard-to-get prerequisites: standing out in a massive generative-AI catalog without triggering Adobe's duplicate-prompt termination rule.

6. Agent advantage vs. automation crowding:
Already massively crowded with automated image-generation pipelines (`INFERENCE`). Every competitor has access to the exact same image models, pushing expected revenue per upload toward pennies while moderation queues and account-termination risks rise.

7. Honest test before spending money:
Upload a small, strictly deduplicated batch of 20 to 50 labeled generative AI assets using zero paid ads and track acceptance rate and 90-day royalties per asset. Even as a free test, expected return does not justify the setup effort.

8. Verdict:
`OUT` because Shutterstock, Pond5, and Envato ban AI completely, while Adobe Stock is flooded with competing image generators and enforces strict anti-iteration account-termination rules over low per-download payouts.

## Deep Dive 5: Prompt Marketplaces and GPT Stores (PromptBase and OpenAI GPT Store)

1. Process from nothing to bank account:
1. Create a PromptBase seller account and connect Stripe for bank payouts (tax and KYC setup).
2. Design, test, and document repeatable prompts (with verified sample outputs) for popular models.
3. Submit prompt listings with pricing and examples for PromptBase marketplace review.
4. PromptBase handles checkout and instant digital delivery of prompt text.
5. Respond to occasional buyer messages if a prompt breaks after an upstream model update.
6. Wait for PromptBase's regular payout cycle ($0 payout fee; early payout costs $3.99) ([PromptBase](https://promptbase.com/help/fees)).
Note on OpenAI GPT Store: OpenAI's official publishing documentation states that personal ChatGPT accounts cannot publish new GPTs, requires a verified domain or builder profile, and publishes no builder payout rate or revenue-share program ([OpenAI Help](https://help.openai.com/en/articles/8798878-sharing-and-publishing-gpts)). As a direct marketplace payer, OpenAI GPT Store is `OUT`.

2. Automation breakdown by step:
Step 1 (account, Stripe KYC, tax): `OWNER ONCE`.
Step 2 (prompt engineering and output testing): `AGENT ALONE` + `SCAFFOLDING`.
Step 3 (marketplace listing upload): `OWNER EVERY TIME` (no public seller upload API documented).
Step 4 (checkout and delivery): handled by PromptBase.
Step 5 (buyer questions and model-update fixes): `AGENT ALONE` draft, `OWNER EVERY TIME` to reply/update in portal.
Step 6 (payouts): automatic after `OWNER ONCE` Stripe setup.
Primary blocker: no verifiable demand base rate, trivial copying by free prompt libraries, and manual portal listing/support.

3. Platform AI-content rule (opened today):
PromptBase (`UNKNOWN` on bulk automation): The marketplace exists specifically to sell AI prompts, so AI-related goods are the core product, though an explicit rule on unattended bulk submission was not found on its fee page ([PromptBase](https://promptbase.com/help/fees)).
OpenAI GPT Store (`MEASURED`): Allows verified builders on eligible plans to publish GPTs subject to automated sharing and policy checks, but publishes no monetization or payout program on its publishing help page ([OpenAI Help](https://help.openai.com/en/articles/8798878-sharing-and-publishing-gpts)).

4. Evidence that it pays:
`MEASURED` (PromptBase fee table): PromptBase takes a "20%" fee on marketplace sales (seller keeps $8.00 from a $10.00 sale), "0%" on referral-link sales, "10%" on custom jobs, and pays "a flat $1.25 each time a Select subscriber downloads one of your prompts," with $0 fee on regular payouts and a "$3.99" fee for early payouts ([PromptBase](https://promptbase.com/help/fees)).
Median PromptBase seller earnings and base rate of prompts that ever sell: `UNKNOWN`.
OpenAI GPT Store direct payout rate: `NONE PUBLISHED` (`MEASURED` on [OpenAI Help](https://help.openai.com/en/articles/8798878-sharing-and-publishing-gpts)).

5. What it needs before the first dollar:
Money: $0 listing fee on PromptBase (`MEASURED` via [PromptBase](https://promptbase.com/help/fees)).
Time: hours to create and test prompts, plus marketplace approval.
Hard-to-get prerequisites: buyer willingness to pay for text prompts when free prompt repositories and newer models reduce prompt sensitivity.

6. Agent advantage vs. automation crowding:
Extremely crowded with low-barrier submissions and eroded by free alternatives (`INFERENCE`). An agent can generate thousands of prompts cheaply, which is the exact reason standalone prompts have almost no durable moat.

7. Honest test before spending money:
List 5 tested prompts on PromptBase at $0 cash outlay and measure organic marketplace sales over 60 days without external promotion.

8. Verdict:
`OUT` because OpenAI GPT Store publishes no builder payout program, PromptBase has no published seller earnings base rate (`UNKNOWN`), and standalone prompts face extreme crowding and near-zero moat.

## Lane Ranking (Top 3)

1. Game engine code utilities on Unity Asset Store and Fab (`WORTH A TEST`): The only method in this lane that combines explicit AI-permitted disclosure rules on Unity ([Unity Support](https://support.unity.com/hc/en-us/articles/16456407029524-Can-I-publish-and-sell-content-generated-with-AI-on-the-Asset-Store)), high published revenue shares of 70% to 88% ([Unity Legal](https://unity.com/legal/asset-store-provider-agreement), [Epic Games Dev](https://dev.epicgames.com/documentation/fab/publisher-get-started-in-fab?lang=en-US)), verified ecosystem payouts above $24 million on Fab ([Unreal Engine](https://www.unrealengine.com/news/fab-2025-year-in-review)), automated compiler/unit-test quality verification, and a clean $0 dry-run test via a free open-source or $0 store lite package.
2. Storefront themes on Shopify Theme Store (`WATCH`): Strong 85% gross revenue share with $0 listing fee ([Shopify Dev](https://shopify.dev/docs/storefronts/themes/store/revenue-share)) and automated QA tooling, held back by an unconfirmed AI submission policy (`UNKNOWN`), strict manual design curation, and ongoing merchant support.
3. Disclosed niche technical reference eBooks on Amazon KDP (`WATCH`): Explicitly allows disclosed AI-generated books ([Amazon KDP](https://kdp.amazon.com/en_US/help/topic/G200672390)) at $0 upfront cost and 35% to 70% eBook royalties ([Amazon KDP Royalties](https://kdp.amazon.com/en_US/help/topic/G200644210)), but manual portal uploads, 60-day payout lag, and heavy bot crowding make it viable only as a narrow $0-ad-spend experiment, never as low-content volume publishing.
