# 209. Deep dive: ways people earn money that an agent could run alone

Date: 2026-11-27. Queue 149 and 150, ledger 240. Written by the lead agent from eight lane pages (209a to 209h), two second checks that re-opened the top rows, and one count run for this page.

The owner's words that opened it (2026-11-27): "feel free to research potential other options for AI to autonomously make money and that might mean you doing searches for ways that humans can make money and looking into the process to see if it can be automated by AI".

Labels: MEASURED (read or counted by us), STATED (a provider's own claim), UNKNOWN, INFERENCE (the lead agent's reading).

## Short answer

- None of the methods clears the bar yet. The bar, as told to the owner: no person doing work every time, no rule against automation, and an honest test before money.
- More than 120 methods were screened and 35 were taken apart step by step. Seven came back ranked first in their lane. After the second check and one count, none of the seven is a build today: five are WATCH (one of them has a paper test that needs the owner's account) and two are closed.
- INFERENCE, the pattern in every lane: making and delivering the thing can run alone. Finding the buyer cannot, or needs money and time with no figure for what comes back. Where a store both brings the buyers and allows agents, agents have already filled it.
- MEASURED, the clearest case (Count 150 below): the Apify Store, which two lanes ranked first, lists 116,534 paid tools from 6,370 publishers. 77% of those tools had at most one user in the last 30 days, and that count includes the publisher.

## The seven lane leaders after the second check

| # | Method | What held up | What the second check or the count changed | Ruling |
|---|---|---|---|---|
| 1 | Paid tool on the Apify Store ([209c](209c_software_tools_and_api_stores.md), [209e](209e_services_and_agent_marketplaces.md)) | MEASURED: the publisher gets 80% of fees less run costs ([publishing terms](https://docs.apify.com/legal/store-publishing-terms-and-conditions)); a tool can be listed and updated by program ([Update Actor page](https://docs.apify.com/api/v2/actor-put)); account, identity check and payout setup are the owner once | MEASURED: Count 150 missed all three marks set before the run. STATED: the "$2M paid out monthly" banner has no month and no count of people paid ([creator page](https://apify.com/partners/actor-developers)) | WATCH, no build. A second count on 2026-12-27 will show what new publishers got in their first month |
| 2 | Expired domain names bought at GoDaddy Auctions and listed on Afternic ([209d](209d_resale_and_arbitrage_of_goods.md)) | MEASURED: the API terms name "autonomous agents" as allowed ([API terms](https://www.godaddy.com/legal/agreements/godaddy-api-terms-of-use)); commission 15% to 30%, $15 minimum ([Afternic](https://www.afternic.com/sell-domains)) | MEASURED: reading auction results needs a paid Auctions membership and a key on the owner's account ([membership terms](https://www.godaddy.com/legal/agreements/auctions-membership-agreement), [key page](https://developer.godaddy.com/en/docs/api-users/auth)). UNKNOWN: any sell-through rate or median return. INFERENCE: names sell over months or years, which is not the owner's "within a few weeks" | WATCH. A paper test is possible but starts with a purchase on the owner's account, so it waits for his word |
| 3 | Code utilities for game engines on the Unity Asset Store and Fab ([209a](209a_digital_goods_marketplaces.md)) | MEASURED: Unity allows disclosed AI-made assets ([Unity support](https://support.unity.com/hc/en-us/articles/16456407029524-Can-I-publish-and-sell-content-generated-with-AI-on-the-Asset-Store)); Fab says it paid more than $24 million to more than 20,000 publishers in 2025 ([Fab review](https://www.unrealengine.com/news/fab-2025-year-in-review)), median UNKNOWN | MEASURED: neither store has a way to publish by program. Unity needs its portal and editor ([Unity workflow](https://docs.unity.com/en-us/asset-store/publishing/asset-packages/workflow)); Fab needs a portal upload for every engine version ([Fab publishing](https://dev.epicgames.com/documentation/fab/publishing-assets-for-sale-or-free-download-in-fab?lang=en-US)). The publisher also owes support and updates | CLOSED for an agent alone: a person every release |
| 4 | Paid alerts on federal contracts and grants from public data ([209h](209h_wide_sweep_of_human_methods.md)) | MEASURED: the public data may be shared and resold within stated limits ([SAM.gov terms](https://sam.gov/about/terms-of-use), [Grants.gov API terms](https://grants.gov/api/terms-conditions)) | MEASURED: free official email alerts already exist ([Grants.gov subscriptions](https://grants.gov/connect/manage-subscriptions/)); paid services already sell AI summaries from $500 a year ([HigherGov pricing](https://www.highergov.com/pricing/), [GovTribe pricing](https://govtribe.com/pricing)). The lane's claimed gap is not there | WATCH, no build |
| 5 | Reference site computed from public data, paid by ads later ([209b](209b_content_and_audience.md)) | INFERENCE: computed pages are not what the search rules against mass-made pages describe | UNKNOWN: no figure for what such a site earns. The only test is public: a site and a search account in the owner's name, then months of waiting | WATCH |
| 6 | Small paid tool sold directly with card checkout ([209g](209g_verified_small_automated_businesses.md), [209e](209e_services_and_agent_marketplaces.md)) | MEASURED: among self-listed products with read-only payment data, median all-time revenue is $237 on Stripe and $12 on Polar ([TrustMRR figures](https://trustmrr.com/stats)) | MEASURED: revenue on that list tracks time in business and site standing, which is selling work, not building work. No test shows demand without posting in public | WATCH |
| 7 | On-chain jobs built for bots ([209f](209f_onchain_jobs_built_for_bots.md)) | MEASURED: paid machine roles exist with public records | MEASURED: on the best one, ten IDs with the operator's own label took 97.3% of displayed fees ([Brevis dashboard](https://provernet.brevis.network/)). UNKNOWN: any newcomer's net after stake and running costs | CLOSED |

## Count 150: does the Apify Store bring users to ordinary publishers

One pass over the public listing on 2026-11-27, 3:30 to 3:36 PM MT, 120 requests, no key ([endpoint page](https://docs.apify.com/api/v2/store-get)). Marks were written on ledger row 240 before the run. Figures come from `python3 research_rig/count_150_apify_store.py report`.

| Mark set before the run | Needed | MEASURED | Met |
|---|---|---|---|
| A. Share of paid tools with 10 or more users in 30 days | 20% or more | 5.2% | No |
| B. Median publisher's 30-day users, summed over its paid tools | 5 or more | 4 | No |
| C. Share of those users held by the top 100 publishers | 80% or less | 80.9% | No |

- MEASURED: 119,232 tools listed, 116,534 paid, 6,370 publishers with a paid tool.
- MEASURED: 77.4% of paid tools had at most one user in 30 days; 0.8% had 100 or more; 93.1% have no review.
- MEASURED: 245 publishers list 100 or more paid tools each and hold 60,200 of them between them. The largest lists 1,986. INFERENCE: these are made by program, which is what we would be doing.
- MEASURED: 2,183 publishers had 10 or more 30-day users, 614 had 100 or more, 140 had 1,000 or more. So the store is not empty for everyone.
- Limits written before the run: a user is not a payer and not a dollar; each count includes the publisher; the listing has no publish date, so new publishers cannot be split out; a user of two tools counts twice in a publisher's sum.
- UNKNOWN: dollars per publisher. The only stated total is "more than $1.7 million per month" across "more than 4,500 independent developers and official partners" ([company notice, 2026-11-10](https://www.globenewswire.com/news-release/2026/11/10/3399579/0/en/apify-unveils-new-ai-agent-capabilities-and-server-actors-to-support-growing-demand.html)), with no count of people paid.
- INFERENCE: most of the tools with real use read large social and shopping sites. This project does not go around a site's terms, so the busiest part of that store is closed to us anyway.

## Corrections the second check made to the lane pages

- 209a: "$0 listing fee" on Fab is not on the page cited. Publishing on Unity and Fab is by hand.
- 209c: the Shopify "$1.3 billion" covers its whole ecosystem, not the app store alone ([Shopify post](https://www.shopify.com/news/billion-dollar-ecosystem)); it cannot be divided by the number of apps.
- 209d: `.com` renewal is $22.99 a year standard and $10.99 only inside a $359.88 a year plan ([plan page](https://www.godaddy.com/resources/news/introducing-the-new-must-have-membership-for-domain-investors)).
- 209f: the bridge bot's "simulation mode" still sends approval transactions, so only past records may be used, never the live bot.
- 209g: the Census table does not drop all businesses under $1,000. The payment-list medians are all-time figures for sellers who chose to list.
- 209h: the paid-alert gap is already served, see row 4.

## Ruled out, with the rule

Each lane page has the quote and link. In short: Etsy, Envato, Shutterstock, Pond5 and TurboSquid bar AI-made or bot-made listings (209a). Faceless video, AI podcasts and AI article sites are cut off from pay or removed (209b). Upwork and Fiverr need a person on each job (209e). Amazon and eBay bar retail-to-marketplace dropshipping; Steam, GovDeals and Rakuten bar bots (209d). Local lead sites break Google's rules at scale; unclaimed-property finding is limited by Idaho Code 14-5-1301 (209h).

## What the lead agent does next

- Count 151, set for 2026-12-27: the same Apify listing once more, matched to today's by publisher name. Publishers present then and absent today are the newcomers; the count is their users after their first weeks. This measures the one figure every lane marked UNKNOWN. Its ledger row and marks are written before that run.
- No build from this round. The Apify route is not built unless Count 151 changes the picture.
- The forecasting bot (queue 147) stays the only payer found whose rules ask for unattended agents. It is built and switched off, waiting on the owner's entry steps.
- The practice cards E12 to E15 and Measurement 134 keep running; they are unaffected.

## Waiting on the owner

- Nothing new is required. Two optional steps exist if he wants a real-world reading sooner than the counts give one: the forecasting entry, and a GoDaddy Auctions membership for a paper test of domain names. Each costs his time or a small fee, and neither has evidence of paying.
