# 46. Alex Becker's dated coin calls set against prices, and the "buy what is hot" idea

Status: measured 2026-11-25 by a helper; the headline figures were recomputed by the builder from the helper's per-call file and agree. Not a counted test. The call list, the prices and the scripts are on the research machine and are not in the repo (vendor prices and transcript text stay out).

Why this was done: the owner's method (`practice/traders/F01_hot_coin_swing.md`) has two parts, picking the coins people are chasing and trading their swings over a few hours. He followed Alex Becker for picks. This page checks the picking part against the public record. It says nothing about the swing trading part, which needs minute prices.

Labels: MEASURED means computed from the collected files. STATED means a named source says it and it was read there, not checked. UNKNOWN means not found. All moves are spot price changes before fees and leverage.

## Short answer

1. MEASURED. I found 1,855 dated "buy" or "I hold this" mentions of named coins in 137 of his YouTube videos (2020-03-20 to 2025-10-13). 1,591 of them could be priced, covering 186 coins.
2. MEASURED. After the video, the typical called coin fell and did worse than bitcoin at every horizon. The median move after 7, 30 and 90 days was -4.6%, -12.3% and -30.6%. The share that beat bitcoin was 40%, 35% and 26%.
3. MEASURED. Before the video, the typical coin had already been rising. The median move over the 30 days before was +10.9%, against +5.3% for bitcoin. Taking only the first time he named each coin, the median was +45.4%. On the record, he was more often late than early.
4. MEASURED. The picture is the same in rising markets and falling ones. Rising markets make the losses smaller in absolute terms, but not compared with bitcoin.
5. MEASURED. A few calls were huge winners. Sandbox went up about 5x to 6x within 90 days of three calls in Sep and Oct 2021. Those winners lift the averages, so the mean is much better than the median. If you put an equal amount into every coin named in a video, the mean 90-day result was +0.7%, while bitcoin's median over the same windows was -4.9%. Only 52 of 127 of those video baskets beat bitcoin.
6. STATED. In video descriptions he says he advises, consults for or holds heavy positions in coins he discusses. One investigation says he was a "Key Advisor" to MetaGods, a coin he promoted. I found no regulator action against him.
7. The owner's own method of trading swings over a few hours with leverage cannot be tested from this record. That would need intraday prices and his own trade log. UNKNOWN.

## Part A. His dated calls

### How the list was built

- Channel listing. MEASURED: the channel has 288 items (239 long videos, 11 shorts, 38 streams). The [Nexlev channel page](https://www.nexlev.io/youtube-stats/@alexbeckerschannel) gives the same total. Files: channel_flat.txt, shorts_flat.txt, streams_flat.txt.
- Removed videos. MEASURED: I found 41 Becker videos that are no longer on the channel (removed_ids.txt). I found them through the titles in his podcast feed (podcast_feed.xml, [Megaphone feed](https://feeds.megaphone.fm/PODAGEN4209796131), [Apple Podcasts](https://podcasts.apple.com/us/podcast/13-crypto-coins-that-will-15x-early-2025-urgent-af/id1818368665?i=1000711034476&l=ko)) and through web search. Their pages and transcripts could still be read from cached copies. Almost all of them date from 2023-11-19 to 2025-08-09.
- Channel gap. MEASURED: the channel today has no long videos at all between 2023-06-23 and 2025-08-13. The whole 2024 to mid-2025 run of coin-list videos has been taken down or made private. A Reddit user noted in Jan 2026 that one 2025 guide video was still up ([Reddit](https://www.reddit.com/r/CryptoCurrency/comments/1q87k14/alex_beckers_cryptocurrency_investment_advice/)). That video, smhbENZS8gE, is now gone. Moonlite Money also describes the channel as "almost silent" from 2023 to mid-2025 ([Moonlite Money](https://moonlitemoney.com/blog/alex-becker-net-worth-hyros-crypto-legit)). STATED.
- Older archives. MEASURED: I parsed Wayback Machine snapshots of the channel's video page from 2021-03, 2021-06, 2022-01 and 2022-09 (wayback). Every video in them is still on the channel, so I found no removed 2021 to 2022 videos. Snapshots from 2023 onward hold only scripts and could not be parsed.
- Transcripts. MEASURED: I have 148 crypto videos saved with a header line and the transcript or description (transcripts). For each one, a language model pulled out every coin he named, with his stance (buy, holding, sell, avoid) and a short quote (calls_raw). I kept only buy and holding mentions, one row per video and coin.
- Quote check. MEASURED: 1,839 of 1,855 quotes match the saved transcript text (at least 80% of the words appear together in one stretch). 9 do not match and 7 come from videos with no transcript. All 16 are flagged in the `quote_found` column of calls.csv. Machine captions misspell coin names, for example "AOS network" for AIOZ and "cdfi" for Seedify. I mapped names to tickers by hand in symbol_map.py.

### How complete the list is

- Fairly complete for YouTube from 2021 to 2025. MEASURED: 2021 has 692 calls, 2022 has 157, 2023 has 45, 2024 has 417 and 2025 has 542.
- Probably missing: removed videos whose titles were never in the podcast feed or in search results; live-stream picks (I read the stream list but extracted few of them); and most 2020 to early 2021 videos, which talked about coins in general. UNKNOWN how many.
- Not covered: X (Twitter) posts and any paid group or newsletter. X search without a login is limited. UNKNOWN.
- Unpriced: 94 calls are NFT collections. 122 names could not be identified. 48 identified coins have no price data or no price on the call date, often because the coin had not launched yet. All of these stay in calls.csv with an empty price. Dead coins are included wherever CoinMarketCap still has their history (for example LUNA, PAID and Polkamon).

### Price method

- Source. MEASURED: CoinMarketCap daily USD closes from its public chart endpoint (https://api.coinmarketcap.com/data-api/v3.1/cryptocurrency/historical?id=ID&convertId=2781&interval=1d). It covers live and dead coins. Coin ids come from CoinMarketCap's [public coin map](https://s3.coinmarketcap.com/generated/core/crypto/cryptos.json) plus its inactive list (cmc_map). The script is fetch_cmc_prices.py, and there is one file per coin id in prices_cmc.
- Entry. The close on the upload date. As a check, I re-ran everything with entry at the next day's close (summary_lag1.md). The results hardly change: the 90-day median was -30.2% instead of -30.6%.
- Bitcoin. Measured the same way.
- Top-20 basket. An equal-weight mix of the top 20 coins in the latest monthly CoinMarketCap snapshot dated before the call, so it uses no future knowledge. Snapshots come from [coinmarketcap.com/historical](https://coinmarketcap.com/historical/20210103/) and are stored in cmc. Stablecoins, wrapped coins and exchange tokens are removed, and so are four odd 2020 entries (999, TAGZ5, HEDG, MIN).
- Renamed coins. For coins that changed ticker (MC to BEAM, MATIC to POL, FTM to S), I measure inside one coin id only, so a 1:100 token swap is not counted as a crash.
- Bitcoin is left out of the "beat bitcoin" counts.
- Scripts in run order: build_calls.py, resolve_ids.py, fetch_cmc_prices.py, compute_moves.py, extra_stats.py, sector_baskets.py. Per-call results are in moves.csv and all summary tables in summary.md.

### Results, all calls (MEASURED, summary.md)

| Window | Calls priced | Median coin | Mean coin | Worst | Beat BTC | Beat top-20 | BTC median | Top-20 median |
|---|---|---|---|---|---|---|---|---|
| 30 days before | 1,470 | +10.9% | +52.8% | -84% | 823 (56%) | 692 (47%) | +5.3% | +14.5% |
| 7 days before | 1,511 | +5.3% | +15.9% | -56% | 846 (56%) | 784 (52%) | +3.5% | +5.2% |
| 7 days after | 1,525 | -4.6% | -1.1% | -68% | 607 (40%) | 570 (37%) | -1.6% | -1.5% |
| 30 days after | 1,525 | -12.3% | -2.3% | -92% | 535 (35%) | 480 (31%) | -3.8% | -3.0% |
| 90 days after | 1,524 | -30.6% | -15.1% | -100% | 401 (26%) | 428 (28%) | -3.6% | -11.0% |

- Uncertainty. MEASURED (extra_stats.json): calls in the same video rise and fall together, so I resampled whole videos to get a range. The share beating bitcoin is 40% at 7 days (range 33% to 47%), 35% at 30 days (30% to 41%) and 26% at 90 days (22% to 31%). Even the top of each range is below one half.
- Swings within 90 days. MEASURED: 33% of calls were at some point 50% or more above the entry price, and 44% were at some point 50% or more below it. The median best point was +26% and the median worst point was -45%. This uses hindsight, since nobody sells at the exact top. It shows the swings were wide in both directions.
- First time he named each coin. MEASURED: 186 coins. Median move in the 30 days before was +45.4%. After the call, the median was -3.4% at 7 days, -13.2% at 30 days and -40.2% at 90 days. 52 of 185 beat bitcoin at 90 days.
- One equal basket per video. MEASURED: 127 videos. Median 90-day move -14.7%, mean +0.7%. 52 of 127 beat bitcoin at 90 days, and 53 of 127 at 30 days.

### Rising and falling markets (MEASURED, summary.md)

Calls are grouped by video date. A positive "Median vs BTC" means the coin did better than bitcoin.

| Period | Calls priced | 30d before, median | 30d after, median | 90d after, median | Beat BTC at 90d | Median vs BTC at 90d |
|---|---|---|---|---|---|---|
| Rising, 2020-10 to 2021-11 | 502 | +25.3% | -11.3% | -36.0% | 186 of 479 | -11.1 points |
| Falling, 2021-11 to 2022-12 | 232 | +0.3% | -17.7% | -50.4% | 51 of 225 | -23.4 points |
| Rising, 2023-10 to 2024-03 | 66 | +107.7% | -0.5% | -25.1% | 16 of 63 | -34.6 points |
| Year 2025 (mixed) | 455 | -8.0% | -13.8% | -18.9% | 93 of 438 | -27.2 points |
| Year 2024, all | 365 | +40.0% | -11.8% | -31.1% | 57 of 347 | -38.7 points |

- 2021 was his best period compared with bitcoin, and the median call still lost to bitcoin at 90 days. The mean beat bitcoin in 2021 because of a few very large winners: three Sandbox calls (+513%, +552% and +596% in 90 days), UFO Gaming (+536%) and Dogecoin (+467%). MEASURED, moves.csv.
- In the early-2024 run, the coins had often already doubled in the month before the video. Example: the 2024-03-09 video "TOP 9 AI Crypto Coins That Can 100x By May", which is now removed. Kondux was up about 15x, OpSec about 16x and Palm AI about 35x in the 30 days before. All three were down 64% to 76% ninety days later, while bitcoin was up 1%. MEASURED.
- The late-2024 and early-2025 AI coin lists fell hard. In the 2024-11-30 video (removed), the 20 priced coins fell 56% to 83% in 90 days, against -13% for bitcoin. In the 2025-01-05 video (removed), the 20 priced coins fell 62% to 92%, against -15%. MEASURED.
- Worst outcomes. MEASURED: Terra LUNA, from calls on 2022-02-15 and 2022-04-01, lost about 100% within 90 days. Mantra (OM), from calls on 2025-03-02 and 2025-03-31, lost about 96% within 90 days. Shiro, from a 2024-12-14 call, lost about 97%.
- Removed and live videos tell the same story. MEASURED: calls in removed videos had a 90-day median vs bitcoin of -30.3 points. Calls in videos still online had -17.2 points.

### Disclosure

- In 2024 and 2025 video descriptions, he points viewers to a list of coins he advises, consults for or holds heavily. STATED: "For a list of coins I advice/consult/have heavy investment in please see my 2024-2025 holds list linked in the BIO of my Twitter/X". This comes from a mirror of JgjGJTrL3hY ([IU mirror](https://uits.iu.edu/video/SY_X_uyv5DJ.html)). The linked sheet is [this Google Sheet](https://docs.google.com/spreadsheets/d/1ayiLPXZcpWuMObzAGz8Fwi-ViypzYOEj8ASOyQBAWy0/).
- MEASURED (calls.csv, column `desc_disclaimer_advises_or_invests`): this note appears in 25 of the 137 videos with calls (4 in 2024 and 21 in 2025). It appears in none of the 2021 to 2023 videos.
- MEASURED: in 425 of 1,855 calls he says in the video that he holds the coin, for example "I own giant bags of these coins". The `says_holds` column was set by simple text matching, so treat it as rough.
- Moonlite Money's check table says "Paid advisor to crypto projects he discusses: Yes, his own YouTube disclaimers" ([Moonlite Money](https://moonlitemoney.com/blog/alex-becker-net-worth-hyros-crypto-legit)). STATED.
- Loock Advisory's MrBeast investigation calls Becker a "Key Advisor to PlayMetaGods" (MGOD), a coin he promoted. It also says MrBeast sent him 14,540 ERN on 8 March 2021, worth $91,670 "as per Arkham", and that Becker "pushed SUPER" ([Loock Advisory](https://loock.io/blog/mrbeast-investigation/)). STATED. These are allegations from a private research firm.
- A Reddit post says he joined WAGMI Games as an official adviser ([Reddit](https://www.reddit.com/r/CryptoMarkets/comments/186762w/alex_becker_has_joined_wagmi_games_as_an_official/)). Tradersunion says he took part in GPUNet's Series A ([Tradersunion](https://tradersunion.com/interesting-articles/alex-becker-crypto-portfolio/)). Both STATED, and I did not check either.
- A 2021 Reddit thread claims on-chain proof that he used YouTube to pump his own coins ([r/Coffeezilla_gg](https://www.reddit.com/r/Coffeezilla_gg/comments/rlajjw/this_guy_just_posted_proof_that_alex_becker_uses/)). STATED, by an anonymous poster. I found no Coffeezilla video about Becker. UNKNOWN.

### Regulators and journalists

- I found no SEC, CFTC or state action naming Alex Becker. UNKNOWN whether any exists. The SEC judgment against a "Jonathan Becker" is a different person ([SEC](https://www.sec.gov/file/judg23-cv-08331becker)).
- A Reddit post says the SEC sued Tai Lopez and Alex Mehr, whom the post calls Becker's business partner ([Reddit](https://www.reddit.com/r/DigitalMarketing/comments/1nr04w5/the_sec_just_filed_a_lawsuit_against_tai_lopez/)). STATED. It is not a case against Becker.
- Moonlite Money, citing SEC filings, says the planned $110M sale of Hyros to Banzai was ended on 2023-08-01 ([Moonlite Money](https://moonlitemoney.com/blog/alex-becker-net-worth-hyros-crypto-legit)). STATED. This matters only because "he sold Hyros for $110M" is often repeated.
- A Sep 2026 post on his X account says his next video will name no coins, and that 90% of his gains last run came from buys made "as soon as BTC started moving" ([X](https://x.com/ZssBecker/status/2096276015194452438)). STATED.

### Other people's checks of Becker

- A Reddit user listed the coins in his 2025 guide video and their falls since. Examples: SuperVerse -81.9%, Destra -89.0%, Beam -86.6%, Seedify -94.1% ([Reddit](https://www.reddit.com/r/CryptoCurrency/comments/1q87k14/alex_beckers_cryptocurrency_investment_advice/)). STATED.
- A Scribd write-up says that of 21 picks in his 2023 gaming portfolio, only SUPER beat bitcoin, and the portfolio was down about 30% in dollars and about 80% against bitcoin ([Scribd](https://www.scribd.com/document/1016694016/New-vs-Old-Crypto-Influencer-Portfolios-Which-Performs-Better)). STATED.
- Numberscrypto followed four of his 14 Sep 2025 portfolios. It found his big-coin picks did worse than the majors, and small coins lost about half in just over a month ([numberscrypto](https://numberscrypto.substack.com/p/alex-becker-september-2025-portfolios)). STATED.
- BuyCrypt logged 7 bitcoin and ether calls from Apr to Sep 2026: 2 played out, 3 open, 2 went against him ([BuyCrypt](https://buycrypt.com/traders/alex-becker/)). STATED.
- One YouTube video argues that his picks did well when measured from his first mention to the cycle peak ([YouTube](https://www.youtube.com/watch?v=WbnyFaabVwU)). STATED. That measures to the top with hindsight, which my fixed 7/30/90-day windows avoid.

## Part A, step 4. Other callers and existing studies

These are third-party logs. I did not rebuild them.

| Caller or study | What was measured | Result | Source |
|---|---|---|---|
| EllioTrades (Becker's Neo Tokyo co-founder) | 211 calls from public videos, checked against Binance/Bybit daily candles | Own-deadline hit rate 9 of 27 (33%) from Sep 2023 to Oct 2026; 1 of 14 in the last 12 months; 30-day direction right 49% of 113 calls; ranked #60 of 68 channels | [Oracle Check](https://oraclecheck.com/guru/elliotrades.html), STATED |
| Lark Davis | 192 to 193 calls, same method | 0 of 8 own-deadline calls (Apr to Nov 2026); 30-day direction right 40% of 84; 36% of 109 resolved | [Oracle Check](https://oraclecheck.com/guru/lark-davis.html), STATED |
| EllioTrades | 7 calls, Sep to Nov 2026 | Average -27.53% | [InfluAlpha](https://influalpha.com/influencer/elliotrades), STATED (from my earlier notes; page not re-opened today) |
| 63 Telegram, YouTube and X callers | 17,820 calls, 2017 to 2026 | 51.9% right; 24 of 63 beat bitcoin; median follower $1,180 vs $1,272 for bitcoin from $1,000; costs not stated | [Zenodo, Freekonomist Research](https://zenodo.org/records/23906438), STATED |
| 180 crypto influencers on X (Merkley, Pacelli, Piorkowski, Williams) | About 36,000 tweets, two years to Dec 2022 | Small positive first-day return, then -2.24% by day 10, -6.53% by day 30, -18.90% by day 90 | [Oxford Law Blog](https://blogs.law.ox.ac.uk/oblb/blog-post/2023/11/crypto-influencers-give-poor-investment-advice-and-sec-taking-notice), [paper PDF](https://d-nb.info/1346220557/34), STATED |

Becker is not on Oracle Check or InfluAlpha. So the closest like-for-like comparison is with the Merkley et al. tweet study. MEASURED for Becker: his median 90-day move was -30.6%, and the mean was -15.1%. That study reports -18.90% for the average influencer tweet (STATED). By this measure Becker does not stand out as better than the typical influencer, and his median is worse. The two methods differ: they use tweets, abnormal returns and a different period. Treat this comparison as rough.

## Part B. The "buy what is hot" idea

### What studies say about attention

- Liu and Tsyvinski, 2011 to 2018. A one-standard-deviation rise in Google searches for "Bitcoin" was followed by about 2.3% higher bitcoin returns two weeks later. A similar rise in Twitter posts was followed by about 2.5% higher returns one week later. Gross, not net of costs, bitcoin and a few large coins only ([NBER working paper](https://www.nber.org/system/files/working_papers/w24877/w24877.pdf), [RFS abstract](https://academic.oup.com/rfs/article-abstract/34/6/2689/5912024)). STATED.
- Öncül and others, 2017 to 2022. The Google search effect on six large coins weakened after 2020 ([paper](https://www.iei1946.it/article/pdf/download/1733/cryptocurrencies-the-role-of-investor-attention)). STATED.
- CFR Cologne working paper, 2018 to 2022, many coins. A one-standard-deviation rise in unusual Twitter attention went with +0.70% the same day and only +0.11% the next day ([CFR working paper 25-02](https://cfr-cologne.de/wp-content/uploads/2026/07/cfr-25-02.pdf)). STATED. Most of the move happens before an ordinary follower could act.
- A cross-section study found coins with unusual Google searches had higher returns afterwards, with only a partial reversal ([Journal of Behavioral and Experimental Finance](https://ideas.repec.org/a/eee/beexfi/v44y2024ics2214635024001060.html)). STATED. Costs not stated.
- ChatGPT launch, Nov 2022. AI-themed coins showed average extra returns of 10.7% to 15.6% in the following month ([arXiv 2305.12739](https://arxiv.org/pdf/2305.12739)). STATED. This is a single event, measured after the fact.
- New exchange listings. Prices ran up +11.9% (Coinbase) and +19.5% (Binance) before the listing news, and +32.8% and +22.7% on the day. The listing day itself was +6.51%, then -1.51% over three days ([Li et al.](https://www.loyola.edu/_media/sellinger-business/documents/academics/departments/finance/wealth-management-conference/speakers/J_Li.pdf), [Ante and Meyer](https://link.springer.com/content/pdf/10.1007/s10203-021-00323-0.pdf); summarised in `docs/research/13_high_risk_sleeve_evidence.md`, ). STATED. Most of the gain comes before or at the news.
- Survivorship. Of 3,904 coins from 2014 to 2021, 1,222 were delisted. Leaving them out inflates equal-weighted returns by 62.19% a year ([Ammann et al.](https://alexandria.unisg.ch/server/api/core/bitstreams/2bc8397d-47dd-4f66-8467-9004b2c9d21), via `docs/research/13_high_risk_sleeve_evidence.md`). STATED. This is the main reason small-coin backtests look better than real life.
- Rotation between themes. CryptoRank found that AI tokens went from fifth place among sectors in Q4 2025 to first in Q1 2026, then back to fifth by Q3 2026 ([CryptoRank](https://cryptorank.io/insights/analytics/which-crypto-narratives-are-booming-2026)). STATED. Leadership between themes does not last.

In short, attention goes with higher prices over days to a couple of weeks, and most of the move comes at or before the news. None of these studies shows a follower making money after costs by buying themes once they are visible.

### What happened to AI and gaming coins after their hot stretches (MEASURED, sector_baskets.py)

The baskets are equal weight and rebalanced daily, using CoinMarketCap closes. The AI basket is FET, RENDER, TAO, AKT, NEAR and AIOZ. The gaming basket is AXS, SAND, MANA, ENJ, GALA, ILV and IMX. They were picked by name with hindsight. They are well-known survivors, so they flatter both sectors.

| Basket | Peak close | Fall from peak to 2026-11-24 | BTC over same time | 90d after peak | 365d after peak | BTC 365d after peak |
|---|---|---|---|---|---|---|
| AI | 2024-12-06 | -83.7% | -40.2% | -66.0% | -82.4% | -10.7% |
| Gaming | 2021-11-25 | -99.2% | +4.3% | -65.0% | -94.1% | -71.2% |

A "hot" signal that could be seen on the day: the basket up more than 100% over the past 90 days. Results after the first hot day of each stretch:

- Gaming. A signal on 2021-01-08 was followed by +1,942% over 90 days. A signal on 2023-02-07 was followed by -40%. A signal on 2024-11-29 was followed by -58% at 90 days and -82% at 365 days.
- AI. A signal on 2021-01-18 was followed by +632% over 90 days. A signal on 2023-11-18 was followed by +173%. A signal on 2024-11-30 was followed by -58% at 90 days and -79% at 365 days.

So a theme being hot told you nothing reliable about the next 90 days. It worked early in the 2021 cycle and failed at the end of each cycle. With 5 to 6 signals per basket, this is far too few to test. MEASURED.

- Coin falls from each coin's own peak close to the latest close, MEASURED: AXS -99.6%, SAND -99.6%, GALA -99.8%, ILV -99.9%, FET -96.7%, RENDER -90.3%, TAO -75.2%, PAAL -99.3%.
- Other sources agree. AI tokens lost about 75% of their value in 2025 ([ForkLog](https://forklog.com/en/ai-token-market-capitalisation-plummets-by-75-over-the-year/)). Gaming tokens sit 98.8% to 99.9% below their peaks ([CryptoTicker](https://cryptoticker.io/en/play-to-earn-explained-gaming-tokens/)). 93% of web3 games are dead, with an average token fall of 95% ([Caladan](https://caladan.xyz/posts/12-billion-in-93-percent-dead-web3-gaming)). All STATED.

### Data that shows "what was hot" on a past date without seeing the future

| Data | What it gives, with timestamp | Free? | Notes |
|---|---|---|---|
| CoinMarketCap historical snapshots | Rank, price and market cap of every listed coin as of a date (weekly) | Yes, HTML pages | MEASURED: used here for 83 monthly snapshots (cmc). Early 2020 pages have odd entries |
| CoinMarketCap chart endpoint | Daily close, volume and market cap per coin, including dead coins | Yes, no key (unofficial endpoint) | MEASURED: used here for 231 coin ids. Volume rank by day can be built from it |
| CoinMarketCap inactive coin list | Ids of delisted coins, so dead coins can be included | Yes | MEASURED: about 31,500 inactive or untracked entries fetched (cmc_map) |
| Exchange candle APIs (Coinbase, Gate, KuCoin, OKX, Kraken) | First trading day on each exchange, which is close to the listing date | Yes | MEASURED working (fetch_prices.py). Binance.com is blocked from this sandbox |
| Wayback Machine CDX | Dated copies of category pages, for example the CoinGecko AI category | Yes | MEASURED: at least 22 monthly captures from 2021-03 to 2024-11 of the [CoinGecko AI category](https://web.archive.org/cdx/search/cdx?url=coingecko.com/en/categories/artificial-intelligence&output=json); CoinMarketCap gaming view captures from 2021-04 |
| Wikipedia pageviews | Daily views per article from 2015 | Yes, CC0 | MEASURED: works (for example Axie Infinity had 161,743 views in Jul 2021). [Wikimedia API](https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Axie_Infinity/monthly/20210101/20220101) |
| YouTube upload dates | When a caller named a coin | Yes, but pages are rate-limited | MEASURED: used here. Removed videos need cached copies |
| GDELT news | News mentions with 15-minute timestamps | Yes | STATED to be free. Its API returned HTTP 502 on 2026-11-25 (`docs/research/19_information_feeds.md`) |
| Google Trends | Relative search interest | Partly | Values are scaled and re-sampled, so they are not true point-in-time data. The official API is in alpha ([Google](https://developers.google.com/search/apis/trends)) |
| CoinGecko | Category history and prices | Free tier is limited to 365 days | MEASURED limit |
| X/Twitter, Reddit history | Social mentions | Not free in bulk now | UNKNOWN cost and coverage |

## Where the evidence is thin

- The coin names were pulled out by a language model and mapped to tickers by me. A wrong mapping is possible for small coins with shared tickers. The ids I chose by hand are in resolve_ids.py.
- Deciding whether he "said buy" relies on transcript wording. Some "holding" rows may be passing mentions.
- Daily closes cannot show intraday swings. The owner's style of trading over a few hours with leverage is untested. UNKNOWN.
- Some calls (about 14%) have no price. Many of them are very small coins that probably did worse, so the results above may be a little better than reality.
- Tweets and paid groups are not covered. UNKNOWN.
- CoinMarketCap closes use USDT and other quotes treated as USD. For tiny coins, early prices can be thin.

## What this changes for our queue

Written by the builder, 2026-11-25.

- "Follow a caller" is not queued as a test. The record above is 1,591 priced calls, and the typical one lost to bitcoin in every kind of market.
- The owner's memory of 5 to 10 times on early entries is consistent with the record: the 2021 winners named above did that inside 90 days. They were a handful among hundreds, and the same kind of call in 2022, 2024 and 2025 mostly lost. So the question for the picker is whether it can tell the early part of a run from the late part, not whether hot coins exist.
- Plan TM06 (the owner's method in the time machine) takes three things from this page. First, the coin list on each past date comes from that date's CoinMarketCap snapshot, dead coins included, because a list made from today's survivors flatters every result. Second, a plain yardstick that buys whatever is up 100% in 90 days runs beside the AI picker. Third, the test dates must include a stretch late in a run as well as early in one.
- Daily closes cannot judge holds of a few hours. That part waits for the minute price store.
