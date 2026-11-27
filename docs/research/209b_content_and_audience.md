# 209b. Content and audience income an agent could run on its own

Status: deep dive 209, lane b, written 2026-11-27 by a helper. Not a test. Nothing was posted, listed, signed up for or bought, and no one was contacted. Every link below was opened on 2026-11-27.

Labels: MEASURED means the page opened today says so (a platform's own rule or help page, or a study's own page). STATED means someone's claim, including press reports, vendor blogs and self-reported results. INFERENCE is this page's reasoning. UNKNOWN means no source found.

Prior work: [doc 205e](205e_content_and_digital_products.md) covered this ground for a human-plus-agent owner and its second check corrections stand. This page asks the narrower 209 question: which content methods can run with no person doing work each time, under rules that allow it, with a test before money goes in.

## Bottom line

- Lane ranking: 1. a reference site built from public data (WORTH A TEST, unmonetized indexing pilot only), 2. a data-driven email newsletter on the owner's own sending setup (WATCH), 3. an automated informational X account (WATCH). Nothing in this lane is a reliable earner; no base rate for any of these exists (UNKNOWN).
- Platforms now write rules against the agent's main strength, volume. beehiiv bars "Publications that rely entirely on AI-generated material without meaningful human input"; Raptive wants content "reviewed, fact-checked, and edited by a human"; TikTok bars "the use of automation to ... distribute high-volume commercial content"; YouTube will not pay channels "where content feels interchangeable from video to video" (all MEASURED, quoted below).
- Enforcement is real and recent: four Google spam updates in 2026 (March, June, August, September), YouTube removal of AI channels with about 5.9 and 5.8 million subscribers in January 2026, and the largest AI podcast network (more than 15,000 shows) stopping its own shows in 2026 (sources below).
- The one honest gap: Google, AdSense and Spotify judge value, not authorship. A site whose pages are computed from public data, with fixed templates the owner reviews once, is not what the scaled content policy describes (INFERENCE). Whether Google indexes and sends clicks to it can be tested without spending ad money.

## Common facts for every method

- Tax: platforms and payment processors issue Form 1099-K only above $20,000 and 200 transactions a year ([IRS 1099-K FAQ](https://www.irs.gov/newsroom/form-1099-k-faqs-general-information), MEASURED). The income is taxable either way, and filing is a yearly owner step (INFERENCE).
- AdSense pays at $100 for a US dollar account, with tax information and identity checks from $0 and address verification at $10 ([AdSense payment thresholds](https://support.google.com/adsense/answer/1709871?hl=en), MEASURED).
- FTC: affiliates must disclose the relationship "clearly" ([FTC Endorsement Guides FAQ](https://consumer.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking), MEASURED), and AI-written fake reviews are banned ([FTC final rule, August 14, 2024](https://www.ftc.gov/news-events/news/press-releases/2024/08/federal-trade-commission-announces-final-rule-banning-fake-reviews-testimonials), MEASURED).
- Search clicks: Pew's panel of 900 US adults and 68,879 searches found a regular result was clicked on 8% of visits with an AI summary against 15% without, and a link inside the summary on 1% ([Pew Research, July 22, 2025](https://www.pewresearch.org/short-reads/2025/07/22/google-users-are-less-likely-to-click-on-links-when-an-ai-summary-appears-in-the-results/), MEASURED by Pew).
- Agents cannot open payment, tax or ad accounts, pass identity checks or sign agreements. In every method those are OWNER ONCE steps (INFERENCE from the payout pages above).

## Methods looked at

| # | Method | Depth | Verdict |
|---|---|---|---|
| 1 | Reference or comparison site computed from public data, ads and affiliate links | Deep | WORTH A TEST (unmonetized pilot) |
| 2 | Data-driven email newsletter with affiliate links and sponsors | Deep | WATCH |
| 3 | Faceless video and short video (YouTube, Shorts, TikTok, Facebook) | Deep | OUT |
| 4 | AI podcast network | Deep | OUT |
| 5 | AI-written niche article site | Short | OUT |
| 6 | Deal and coupon alert site on Amazon data | Short | WATCH, folded into 1 and 2 |
| 7 | Automated informational X account with Creator Revenue Sharing | Short | WATCH |
| 8 | Paid communities (Discord server subscriptions, Patreon, similar) | Short | OUT for autonomy |
| 9 | Pinterest affiliate pins | Short | OUT |
| 10 | Medium Partner Program | Short | UNKNOWN (rule page blocked to this machine, not retried) |

## Deep method 1: reference site computed from public data

What it is: a site where each page answers one narrow question from a public data set with a clear reuse licence (for example a government table), with the numbers computed by code, not written by a language model per page. Money comes from display ads (AdSense first) and affiliate links where a page compares buyable things.

### Steps

| # | Step | Who |
|---|---|---|
| 1 | Pick a public data set with a reuse licence and a question people search for; record the licence text | AGENT ALONE |
| 2 | Owner approves the data set, the niche and the site name | OWNER ONCE |
| 3 | Buy the domain and hosting | OWNER ONCE |
| 4 | Build the generator: fetch, clean, compute, render pages, a methods page, an automation note, an affiliate disclosure, a corrections address | SCAFFOLDING |
| 5 | Owner reviews the page templates and the methods page once; no per-page language-model text | OWNER ONCE |
| 6 | Automatic checks before each publish: every number traced to a source row, no empty or near-duplicate pages, page count capped | SCAFFOLDING |
| 7 | Verify the site in Google Search Console | OWNER ONCE |
| 8 | Publish and wait for Google to index and rank pages | AGENT ALONE to deploy; Google decides the rest. BLOCKING STEP |
| 9 | Measure indexing, impressions and clicks weekly | AGENT ALONE |
| 10 | Apply to AdSense; give tax and identity information; verify address | OWNER ONCE |
| 11 | Apply to affiliate programs (for Amazon Associates, three qualifying sales within 180 days or the application can be withdrawn) | OWNER ONCE, then AGENT ALONE |
| 12 | Refresh data and pages on schedule; prices from Amazon only through its API with a time stamp | AGENT ALONE |
| 13 | Reader messages: corrections handled by the agent against the source data, anything else held for the owner | AGENT ALONE with escalation |
| 14 | Refunds: none, there is no sale | not needed |
| 15 | Payout: AdSense at $100 to the owner's bank; affiliate payouts to the same | OWNER ONCE to set up, then AGENT ALONE |
| 16 | Yearly tax filing from the 1099 forms | OWNER EVERY TIME (once a year) |

The step that blocks full automation is step 8. Nothing the agent does controls whether Google indexes the pages or sends clicks, and an update can remove the traffic overnight (evidence below). Step 5 keeps this inside the rules: Google's guidance says "It is critical to manually factcheck and review all AI-generated content" ([Google on generative AI content, updated 2026-10-01](https://developers.google.com/search/docs/fundamentals/using-gen-ai-content), MEASURED), so the design avoids per-page AI text and puts the owner's review on the templates once (INFERENCE).

### The rules, quoted

- Google: scaled content abuse "is typically focused on creating large amounts of unoriginal content that provides little to no value to users, no matter how it's created", with examples including "Scraping feeds, search results, or other content to generate many pages" and "Stitching or combining content from different web pages without adding value"; and "Sites that violate our policies may rank lower in results or not appear in results at all" ([Google spam policies](https://developers.google.com/search/docs/essentials/spam-policies), MEASURED). The same page says "Good affiliate sites add value by offering meaningful content or features", naming "additional information about price, original product reviews, rigorous testing and ratings, navigation of products or categories, and product comparisons" (MEASURED). Verdict on the rule: allowed if the pages add value; not OUT.
- AdSense: "We do not allow Google-served ads on screens: without publisher-content or with low-value content" and not on screens "with embedded or copied content from others without additional commentary, curation, or otherwise adding value" ([Google Publisher Policies](https://support.google.com/adsense/answer/10502938?hl=en), MEASURED). On AI or automation the page is silent: UNKNOWN.
- Raptive: content "should have meaningful, thoughtful human involvement ... Your content has been reviewed, fact-checked, and edited by a human" ([Raptive AI policy](https://help.raptive.com/hc/en-us/articles/23945568132123-What-are-Raptive-s-policies-around-AI-generated-content), MEASURED), and "Little-to-no meaningful human involvement" is listed as a violation ([Raptive content and traffic policies](https://help.raptive.com/hc/en-us/articles/29872333292443-Raptive-Content-and-Traffic-Policies), MEASURED). Raptive is OUT for an unattended site.
- Mediavine: "We do not monetize low-quality, mass-produced, unedited or undisclosed AI content that is scraped from other websites" ([Mediavine on AI](https://www.mediavine.com/ai-and-our-commitment-to-a-creator-first-future/), MEASURED). A computed data site is not plainly covered; treat as UNKNOWN and expect vetting to reject it (INFERENCE).
- Ezoic: "If you use AI and generative tools, ensure that you are adding value rather than repurposing already published content" and "If you are using AI tools to generate content, meticulously review and refine the output" ([Ezoic content guidelines](https://support.ezoic.com/kb/article/ezoic-content-guidelines), MEASURED). Allowed with value, but it asks for review; a review of fixed templates once may or may not satisfy it (UNKNOWN).
- Amazon Associates: sites "must contain original content", and "Original content utilizing third-party materials must contain significant commentary, analysis, or transformation" ([Associates Program Policies](https://affiliate-program.amazon.com/help/operating/policies), MEASURED). The same page sets agent rules: an Agent must identify itself in the user-agent string "as `Agent/[agent name]`", must not mimic human patterns or solve CAPTCHAs, and must "respond truthfully" if asked whether it is a human (MEASURED). Prices may be shown only from Amazon's links or APIs, cached at most 24 hours, with a date and time stamp when refreshed less often than hourly (MEASURED). The API itself is closed to a new site: an account "will lose access to Product Advertising API 5.0 if it has not generated referring sales for a consecutive 30-day period" ([PA-API rate limits](https://webservices.amazon.com/paapi5/documentation/troubleshooting/api-rates.html), MEASURED). Amazon commission rates run from 20% (Amazon Games) to low single digits for most goods ([Amazon commission income statement](https://affiliate-program.amazon.com/help/node/topic/GRXPHT8U84RAYDXZ/), MEASURED).

### Evidence it pays

- Base rate for new sites: UNKNOWN. No study of how many new sites earn anything was found.
- Content site sales at one broker fell from about 70 (2023) to about 50 (2024) to about 30 by late May 2025, and multiples from about 30x to 27x to 24x monthly profit ([Empire Flippers](https://empireflippers.com/you-can-sell-your-business-for-life-changing-money-in-2025-heres-the-secret/), STATED by the broker).
- Programmatic page sets in 2026, as gathered by a vendor blog from site owners' posts: a 960,000-page game directory with about 40% of pages indexed and about 1,000 clicks in its first month; a skincare site whose impressions fell from about 1,400 a day to 18 overnight in September 2026; a home-services site whose clicks fell from 207 a day to 13 after the August 2026 spam update ([RankControl summary](https://rctrl.com/blog/programmatic-seo-results), STATED, self-reported, not audited). None gives revenue.
- Google ran spam updates starting 24 March, 24 June, 18 August and 24 September 2026, plus core updates ([Google Search Status history](https://status.search.google.com/products/rGHU1u87FJnkP6W2GwMi/history), MEASURED).
- Dollars a month at small scale: UNKNOWN.

### Before the first dollar

- A domain and hosting (owner buys once), the generator, Search Console, an AdSense account approved and $100 earned, months of indexing (INFERENCE from the thresholds above).

### Agent edge or crowded

- The agent's edge is cheap upkeep: refreshing data, fixing errors and adding pages only where the data supports a distinct answer (INFERENCE). The field is crowded with template sites, which is why updates keep hitting them; the edge holds only if each page has a number nobody else shows (INFERENCE).

### Honest test before money goes in

- Unmonetized indexing pilot: publish 200 to 500 computed pages on a fresh domain with no ads, fix pass marks in writing before launch (for example share of pages indexed at week 8, impressions and clicks at week 12, and no drop through one spam update), and read Search Console only. It can fail the method cheaply; it cannot prove income, because ad revenue per visit is only learned after ads go on (INFERENCE).
- Cost: the domain and hosting. Publishing is posting, so the owner must approve it.
- Offline part with no publishing: a dry run of the generator and the automatic checks against the source data.

### Verdict

WORTH A TEST, as the unmonetized indexing pilot only: the rules allow computed pages that add value, and the one blocking question (will Google index and send clicks) can be answered before any ad or affiliate money is involved.

## Deep method 2: data-driven email newsletter

What it is: a weekly or daily email built from public data (for example a digest of new public records in a niche), earning from affiliate links, an ad network and sponsors.

### Steps

| # | Step | Who |
|---|---|---|
| 1 | Pick the data source and niche; check licence | AGENT ALONE |
| 2 | Choose the sending platform; open the account; sign its terms | OWNER ONCE |
| 3 | Sender domain, sign-up page, unsubscribe, physical address in the footer | SCAFFOLDING |
| 4 | Build the issue generator and accuracy checks | SCAFFOLDING |
| 5 | Grow subscribers (search page, referrals, cross-promotion, paid acquisition) | BLOCKING STEP: organic growth is not in the agent's control; cross-promotion means contacting people; paid acquisition is money in |
| 6 | Send issues on schedule | AGENT ALONE |
| 7 | Affiliate links with disclosure | AGENT ALONE once approved (OWNER ONCE to apply) |
| 8 | Sponsors: find, price, sign, invoice | OWNER EVERY TIME, unless the platform's own ad network fills the slots |
| 9 | Reader replies and unsubscribes | AGENT ALONE with escalation |
| 10 | Refunds: only if paid subscriptions are sold; handled by the platform's processor | SCAFFOLDING |
| 11 | Payout and tax form | OWNER ONCE, then yearly OWNER EVERY TIME |

### The rules, quoted

- beehiiv: "Publications that rely entirely on AI-generated material without meaningful human input are not permitted", and it bars "AI-driven 'content farms' that mass-produce templated marketing material with little or no human input" and "Using AI to mass-produce repetitive material, such as templated listicles, daily trivia" ([beehiiv Acceptable Use Policy](https://www.beehiiv.com/aup), MEASURED). An unattended newsletter is OUT on beehiiv, and so is its ad network.
- Substack: no rule on AI-written or automated publications was found; the page bars spam and purchased or scraped lists and says "you may not create publications for spamming or phishing purposes" ([Substack content guidelines](https://substack.com/content), MEASURED). On automation: UNKNOWN.
- Amazon allows links in email only when "such communications are solicited (i.e., opted into by the receiving customer)" ([Associates Program Policies](https://affiliate-program.amazon.com/help/operating/policies), MEASURED).
- Own sending setup: the platform rule then depends on the email service chosen (UNKNOWN until one is picked); US email law applies either way (INFERENCE).

### Evidence it pays

- Substack reported 5 million paid subscriptions in March 2025 ([Substack](https://post.substack.com/p/5-million), MEASURED as Substack's own count). It gives no distribution per writer, and paid subscriptions are bought for a person's writing (INFERENCE).
- Base rate for a new automated newsletter: UNKNOWN. Dollars per subscriber: UNKNOWN.

### Before the first dollar

- A list of opted-in readers large enough for affiliate sales or a sponsor; how large is UNKNOWN.

### Agent edge or crowded

- An agent can read a data source daily and never miss an issue, which human niche newsletters often do (INFERENCE). The weak point is that inboxes are crowded and readers can unsubscribe in one click; growth, not writing, is the limit (INFERENCE).

### Honest test before money goes in

- Private dry run: four to eight weeks of issues sent only to the owner, scored for accuracy against the source and for whether he would open them. This tests the generator, not the audience.
- Audience growth cannot be tested without publishing a sign-up page; that pilot would need owner approval and costs no ad money if it uses only the search page from method 1 (INFERENCE).

### Verdict

WATCH: allowed on Substack (rule silent) or the owner's own sender, but the blocking step is growth, which needs either people work or money in.

## Deep method 3: faceless video and short video

What it is: channels whose videos are scripted, voiced and edited by AI with no presenter, paid through YouTube Partner Program revenue share, TikTok Creator Rewards or Facebook content monetization.

### Steps

| # | Step | Who |
|---|---|---|
| 1 | Channel account, identity, payout and tax setup | OWNER ONCE |
| 2 | Pick topics, write scripts, make voice, visuals, captions, thumbnails | AGENT ALONE |
| 3 | AI disclosure label where realistic | AGENT ALONE |
| 4 | Upload on schedule | SCAFFOLDING (platform upload tools) |
| 5 | Reach the payout threshold | BLOCKING STEP |
| 6 | Pass the monetization review for originality | BLOCKING STEP, a human reviewer at the platform |
| 7 | Comments and brand requests | AGENT ALONE for moderation; OWNER EVERY TIME for deals |
| 8 | Refunds: none | not needed |
| 9 | Payout and tax form | OWNER ONCE, then yearly |

### The rules, quoted

- YouTube: "channels where content feels interchangeable from video to video are not allowed to monetize", and not allowed are channels with content "that appears to be produced using a template" ([YouTube channel monetization policies](https://support.google.com/youtube/answer/1311392/), MEASURED). The policy was renamed "inauthentic content" on July 15, 2025 to cover content "that is repetitive or mass-produced" (MEASURED). AI as such is allowed: "channels that use AI in their content remain eligible to monetize" ([YouTube, July 10, 2025](https://support.google.com/youtube/thread/356734251/response-to-creator-questions-about-ypp-policies-july-2025?hl=en), MEASURED), with realistic AI disclosed ([YouTube disclosure help](https://support.google.com/youtube/answer/14328491?hl=en), MEASURED).
- YouTube thresholds: from February 1, 2027, new applicants need 8,000 watch hours in 365 days or 20 million Shorts views in 90 days; Shorts revenue sharing needs 10 million Shorts views in 90 days; creators get 55% of long-form and 45% of Shorts pool revenue ([YouTube blog, August 10, 2026](https://blog.youtube/news-and-events/youtube-partner-program-updates-2027-new-opportunities-earn/), MEASURED).
- TikTok Creator Rewards: "Original content ... is quality content that's designed, filmed, and produced by you that showcases your expertise, talent, or creativity"; not original includes "Content that contains looping videos, single or multiple photos, or only text overlays"; entry needs 10,000 followers and 100,000 views in 30 days, and videos must be at least one minute ([TikTok Creator Rewards Program](https://support.tiktok.com/en/business-and-creator/creator-rewards-program/creator-rewards-program), MEASURED). The page is silent on AI: UNKNOWN. TikTok's guidelines bar "the use of automation to register or operate accounts in bulk, distribute high-volume commercial content" and require a label on realistic AI content ([TikTok integrity and authenticity](https://www.tiktok.com/community-guidelines/en/integrity-authenticity), MEASURED).
- Facebook: accounts that repeatedly reuse others' content "will not only lose access to Facebook monetisation programmes for a period of time, but will also receive reduced distribution"; Meta acted on about 500,000 spammy accounts and took down about 10 million impersonator profiles in the first half of 2025 ([Meta for Creators, July 14, 2025](https://creators.facebook.com/blog/combating-unoriginal-content/), MEASURED). The page does not mention AI: UNKNOWN.

### Evidence it pays, and enforcement

- In a new account's first 500 YouTube Shorts, 104 (21%) were AI-generated ([Kapwing](https://www.kapwing.com/blog/ai-slop-report-the-global-rise-of-low-quality-ai-videos/), STATED, one account, one sample). Its earnings figures, such as about $4.25 million a year for one channel, are Social Blade estimates from views (STATED, modelled, not a base rate).
- YouTube removed 11 channels flagged by Kapwing for "spam, deceptive practices, and scams", including channels of more than 5.9 and 5.8 million subscribers ([The Verge, January 28, 2026](https://www.theverge.com/news/869684/youtube-top-ai-channels-removed-kapwing), STATED with a YouTube spokesperson). YouTube terminated the AI trailer channels Screen Culture and KH Studio, "well over 2 million subscribers", for "spam and misleading-metadata" ([Deadline, December 2025](https://deadline.com/2025/12/youtube-terminates-screen-culture-kh-studio-fake-ai-trailer-1236652506/), STATED).
- Base rate for a new faceless channel: UNKNOWN. YouTube says YPP has over 3 million creators but gives no payout spread (MEASURED, blog above).

### Agent edge or crowded

- Crowded with bots by the platforms' own enforcement record. The agent's edge, many videos cheaply, is the thing the rules name (INFERENCE).

### Honest test

- None that tells anything about income without uploading. A private render test shows only that the pipeline works (INFERENCE).

### Verdict

OUT: TikTok's originality rule ("designed, filmed, and produced by you") and its bar on automated high-volume posting, plus YouTube's template rule, cover an unattended channel, and the field is the one platforms are clearing out.

## Deep method 4: AI podcast network

What it is: many AI-voiced shows generated from text sources and paid by programmatic ads or Spotify's Partner Program.

### Steps

| # | Step | Who |
|---|---|---|
| 1 | Hosting account, show listings in Apple and Spotify | OWNER ONCE |
| 2 | Generate scripts and AI voices; add AI disclosure in audio and notes | AGENT ALONE |
| 3 | Publish episodes | AGENT ALONE |
| 4 | Reach an audience and the payout threshold | BLOCKING STEP |
| 5 | Ad network or Spotify Partner Program application | OWNER ONCE |
| 6 | Listener messages | AGENT ALONE |
| 7 | Payout and tax | OWNER ONCE, then yearly |

### The rules, quoted

- Apple: "Creators using AI to generate audio or video content ... must prominently disclose this to audiences in the content and metadata for each episode and show" ([Apple Podcasts content guidelines, 1.11](https://podcasters.apple.com/support/891-content-and-subscription-guidelines), MEASURED). Allowed with disclosure.
- Spotify Partner Program: at least 3 episodes, 2,000 consumption hours and an audience of 1,000 on Spotify in the last 30 days; to stay in, an episode and at least $10 earned in every 6 months ([Spotify Partner Program](https://support.spotify.com/us/creators/article/spotify-partner-program/), MEASURED). The page is silent on AI: UNKNOWN.

### Evidence it pays

- Inception Point AI made more than 15,000 AI shows, some for "$1 per episode or less", then stopped them and let them fall dormant "no longer monetizing the shows"; ad marketplaces could not tell advertisers which shows were AI-made, and advertisers wanted to know ([The Hollywood Reporter, November 17, 2026](https://www.hollywoodreporter.com/business/digital/the-5000-episodes-a-week-ai-podcast-company-pivot-1236754759), STATED). No revenue figures were given.
- Listen Notes counts at least 3,838,196 podcasts and says it excludes "AI-generated audio" from its database ([Listen Notes podcast stats](https://www.listennotes.com/en/podcast-stats/), MEASURED as its own stated method). Directories already filter this out (INFERENCE).
- Base rate: UNKNOWN.

### Honest test

- None that measures income without publishing.

### Verdict

OUT: the best-funded attempt at exactly this stopped monetizing its own shows, and ad buyers avoid AI shows; the rules allow it, the market does not.

## Short methods

- AI-written niche article site: Google's scaled content policy names "Using generative AI tools or other similar tools to generate many pages without adding value for users" ([Google spam policies](https://developers.google.com/search/docs/essentials/spam-policies), MEASURED), and Raptive requires human editing (MEASURED above). Any value would come from first-hand testing, which is a person every time. OUT.
- Deal and coupon alerts on Amazon: Amazon price data needs its API, which a site without sales cannot keep, and prices must carry a time stamp and disclaimer ([Associates Program Policies](https://affiliate-program.amazon.com/help/operating/policies); [PA-API limits](https://webservices.amazon.com/paapi5/documentation/troubleshooting/api-rates.html), MEASURED). Amazon bars rewards for using links: "You will not offer any person or entity any consideration, reward, or incentive ... for using Special Links" (MEASURED). beehiiv bars "High-frequency promotional blasts focused primarily on discounts, offers, or sales events" ([beehiiv AUP](https://www.beehiiv.com/aup), MEASURED). WATCH only as a feature inside methods 1 and 2, not alone.
- Automated informational X account: X allows "automated posts based on sources of outside information ... such as an RSS feed, weather data" but not "duplicative or substantially similar posts" or automated posts about trending topics ([X automation rules](https://help.x.com/en/rules-and-policies/x-automation), MEASURED). Revenue sharing needs a paid Premium subscription, 5 million organic impressions in 3 months and 500 verified followers ([X Help, Creator Revenue Sharing](https://help.x.com/en/using-x/creator-revenue-sharing), MEASURED), and X may "adjust any future payments, or to suspend payment" if it finds content manipulated "using bots or other automated means" ([X Creator Revenue Sharing Terms](https://legal.x.com/en/creator-revenue-sharing-terms), MEASURED). Whether a labelled automated account is paid is UNKNOWN. Test: run it unmonetized and count impressions, which needs posting and owner approval; the Premium fee is money in before revenue. WATCH.
- Paid communities: Discord needs the server's "membership and activity" not to be mostly "bots or inactive accounts" and is silent on AI ([Discord Monetization Policy](https://support.discord.com/hc/en-us/articles/10575066024983-Monetization-Policy), MEASURED). Patreon permits AI-generated works within its guidelines ([Patreon AI policy page](https://support.patreon.com/hc/en-us/articles/34055590411789-Understanding-Patreon-s-AI-policies-for-Adult-18-creators), MEASURED). Members pay for access to a person and a group; that is work every time (INFERENCE). OUT for autonomy.
- Pinterest: "Don't use automation that hasn't been explicitly approved by Pinterest" and "Don't create or save content that is repetitive, deceptive, or irrelevant in an attempt to make money" ([Pinterest Community Guidelines](https://policy.pinterest.com/en/community-guidelines), MEASURED). OUT unless through an approved partner tool, and even then the repetitive rule bites.
- Medium Partner Program: its AI policy page was blocked to this machine earlier today and was not retried. UNKNOWN.

## Lane ranking

1. Reference site computed from public data: WORTH A TEST as an unmonetized indexing pilot with pass marks fixed in advance. It is the only method here where the rules allow unattended work with value and a test exists before money goes in. Expect small or no income; no base rate exists.
2. Data-driven newsletter on Substack or the owner's own sender: WATCH. The writing can run alone; growth cannot.
3. Automated informational X account: WATCH. Automation is explicitly allowed, but the payout bar is high, Premium costs money first, and X keeps wide discretion over automated content.

Faceless video, AI podcasts, AI article sites, Pinterest and paid communities are OUT for an unattended agent. If the owner wants only methods with evidence that they pay, the honest answer for this lane is none.
