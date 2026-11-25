# 19. Information feeds: what exists and what has evidence

Status: research summary. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Written by a research agent, then the claims that matter most for decisions were checked against their sources by a second model. Claims not listed in the check log were not rechecked. The check log is in `docs/research/17_21_checklogs/`.

## Bottom line

- Most feeds a retail trader can reach do not work as stand-alone buy signals for a long-only account. In recent studies, Congress trades, WallStreetBets posts, Google search spikes, earnings drift in large stocks and lagged Bitcoin ETF flows show no usable edge after the data becomes public.
- A few feeds have real evidence as risk filters, not buy triggers: market-wide short interest, crypto futures funding rates (as a crowding and volatility warning) and prediction market odds (as calm, well-calibrated event odds).
- The one stock-level buy screen with a clear mechanism is insider buying that is not routine. The key study is old (published 2012) and must be retested on recent data after costs.
- LLM headline scoring made money mainly on the short side and in small stocks. It turns negative at modest trading costs and its yearly Sharpe fell every year from 2021 to 2024. For us it is at most a bad-news veto.
- A useful free, no-key stack answered live on 2026-11-25: SEC EDGAR, Cboe VIX and VIX3M files, FINRA daily short volume, Kraken Futures funding, Coin Metrics Community, DefiLlama stablecoins, Kalshi, Polymarket, Fed and BLS RSS, Treasury Fiscal Data, CFTC COT and Wikimedia pageviews.
- Two data traps were found. FRED's API terms ban use "in connection with" AI or machine learning development and ban storing FRED content in a database. FRED's free high-yield credit spread file only goes back to 2023-11-27, and Kraken's free funding history only goes back about one year.
- No paid news or social feed is justified before a strategy proves itself on free data.

## What was found

This builds on the existing notes on Perplexity tools (docs/research/05_perplexity_platform_options.md, docs/playbook/05_perplexity_and_costs.md) and on price data vendors (docs/research/10_historical_data_and_practice.md). It does not repeat them.

Tags: MEASURED means the checker opened the primary page, file or live endpoint and saw it. STATED means a vendor or another party says it and it was not confirmed. UNKNOWN means not established.

### Feeds that answered live with no key (checked 2026-11-25)

| Feed | What it gives | History seen in the live file | Terms point that matters | Tag |
|---|---|---|---|---|
| SEC EDGAR APIs | Filings (8-K, Form 4, 13F and more) and company facts as JSON. No key needed ([SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)) | Multi-decade; nightly bulk ZIP at about 3:00 a.m. ET ([SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)) | Max 10 requests per second; a User-Agent header with contact details is required ([SEC fair access](https://www.sec.gov/edgar/searchedgar/accessing-edgar-data.htm)) | MEASURED |
| SEC EDGAR update speed | Submissions API typical delay under one second; XBRL APIs under one minute; may be longer at peak times ([SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)) | n/a | n/a | MEASURED |
| Cboe VIX and VIX3M daily files | Daily open, high, low, close ([Cboe VIX historical data](https://www.cboe.com/tradable_products/vix/vix_historical_data)) | VIX from 1990-01-02; VIX3M from 2009-09-18; both to 2026-11-24 | Page gives a no-warranty notice only; no clear reuse licence was found | MEASURED (data), UNKNOWN (licence) |
| FINRA Reg SHO daily short sale volume | Daily short volume and total volume per symbol ([FINRA short sale volume](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data)) | File for 2026-11-24 opened | Short volume is not short interest. Much of it is market-maker activity (not confirmed on the FINRA page) | MEASURED (file), STATED (interpretation) |
| FINRA short interest | Twice-monthly short positions, published on the 7th business day after the settlement date ([FINRA short interest](https://www.finra.org/finra-data/browse-catalog/equity-short-interest)) | Not checked | API access may need a free FINRA account | MEASURED (schedule), UNKNOWN (access) |
| Kraken Futures public tickers | Live funding rate, predicted funding, open interest, mark price | Live snapshot | Public market data | MEASURED |
| Kraken Futures funding history | Hourly funding rates for PF_XBTUSD | 8,898 hourly rows from 2025-11-19 to 2026-11-25 (about one year only) | Public market data | MEASURED |
| Coin Metrics Community API | Daily BTC metrics including CapMVRVCur (MVRV) | BTC MVRV from 2010-07-18 to 2026-11-24 | Licence and limits not found on the [Coin Metrics docs page](https://docs.coinmetrics.io/api/v4/) | MEASURED (data), UNKNOWN (licence) |
| DefiLlama free API | Stablecoin supply, chain and protocol TVL, DEX volume, fees, open interest; no key ([DefiLlama API docs](https://defillama.com/docs/api)) | Multi-year | Token unlock and perp funding endpoints are "API Plan" only; a premium plan is listed at 300 dollars a month; no licence text on the page ([DefiLlama API docs](https://defillama.com/docs/api)) | MEASURED |
| Alternative.me Fear and Greed | Daily 0 to 100 crypto mood score | 3,216 daily rows from 2018-02-01 | Attribution required; commercial use allowed with attribution ([Alternative.me](https://alternative.me/crypto/fear-and-greed-index/)) | MEASURED |
| Kalshi public market data | Event contract prices (FOMC, CPI and others) | Live list opened | Read-only terms not checked | MEASURED (works), UNKNOWN (terms) |
| Polymarket Gamma API | Event contract prices | Live list opened | Read-only terms not checked | MEASURED (works), UNKNOWN (terms) |
| CFTC Commitments of Traders | Weekly futures positioning. Published Fridays 3:30 pm ET with Tuesday data ([CFTC COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)) | Socrata endpoint opened | US government data | MEASURED |
| US Treasury Fiscal Data | Average interest rates, debt, auctions | Average rates from 2001-01-31 | US government open data; terms not read | MEASURED (works), UNKNOWN (terms) |
| FRED public CSV (fredgraph.csv) | Single series as CSV | DGS10 from 1962-01-02. BAMLH0A0HYM2 (high-yield spread) only from 2023-11-27 | See the FRED terms row below | MEASURED |
| Wikimedia pageviews | Daily article views | Live query for "Bitcoin" opened | CC0 licence; User-Agent required ([Wikimedia access policy](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html)); 200 requests per minute with a compliant User-Agent, 10 per minute if unidentified, at most 3 at once ([Wikimedia rate limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits)) | MEASURED |
| Fed monetary policy RSS and BLS latest RSS | Official release notices | Recent items | US government works | MEASURED (works) |
| PR Newswire RSS | Company press releases | Recent items | Reuse terms not read | MEASURED (works), UNKNOWN (terms) |
| Coinbase Exchange /products | Current list of tradable pairs (a listing change can be found by comparing snapshots) | Current only | Public market data | MEASURED |

Endpoints that failed on 2026-11-25: GDELT DOC API (HTTP 502), TreasuryDirect RSS (HTTP 406 with a default client), GlobeNewswire RSS (HTTP 403), Kraken blog listing feed (HTTP 404). All MEASURED.

### Feeds that need a key, an account or money

| Feed | What the opened page shows | What is not established | Tag |
|---|---|---|---|
| Alpaca News API | Real-time news over WebSocket ([Alpaca streaming news](https://docs.alpaca.markets/us/docs/streaming-real-time-news)). Example articles carry source "benzinga" ([Alpaca news reference](https://docs.alpaca.markets/us/reference/news-3.md)). A 403 means the subscription does not cover the data; limits are per minute in response headers | History start date, which plan includes it, numeric limit, and any Benzinga limit on passing text to an outside LLM. The pages opened do not say | MEASURED (shown), UNKNOWN (rest) |
| Finnhub | All listed plans "strictly for personal use"; no redistribution of data or derived results; "All data must be deleted should your subscription to that data ends"; 30 calls per second cap on top of plan limits; no mention of AI ([Finnhub terms](https://www.finnhub.io/terms-of-service)) | Free-tier per-minute limit (not on the terms page) | MEASURED |
| Massive (formerly Polygon) | AI tools may process data "only on your behalf" and not for their own purposes ([Massive individuals terms](https://massive.com/legal/individuals-terms-of-service)). No training, fine-tuning or distilling AI models unless expressly permitted; delete within 30 days after the licence ends ([Massive market data terms](https://massive.com/legal/market-data-terms-of-service)) | Free tier news depth and limits | MEASURED |
| Tiingo | All plans may pass data to an AI model in a prompt or tool call if the provider is an "Approved Inference Provider" (zero retention or no training on inputs) and the data is not used to train models. Power plans may train non-generative predictive models for own use. Paid-plan data must be deleted on cancellation ([Tiingo terms, updated 2026-11-05](https://www.tiingo.com/tos/)) | News API price and history depth on each plan | MEASURED (terms), UNKNOWN (price) |
| NewsAPI.org | Free Developer plan is for "development and testing in a development environment only", not production, "including internally"; no mention of AI ([NewsAPI terms](https://newsapi.org/terms)) | Paid prices (not on the terms page) | MEASURED |
| GDELT | All datasets "available for unlimited and unrestricted use for any academic, commercial, or governmental use" without fee ([GDELT about](https://www.gdeltproject.org/about.html)) | Whether the API is reliable (it was down on the day) | MEASURED |
| FRED API | Section (k) bans using the API "in connection with the development or training" of machine learning including LLMs. Section (l) bans storing, caching or archiving FRED content or putting it in a database. No numeric rate limit is given ([FRED terms](https://fred.stlouisfed.org/legal/terms/)) | Whether the same limits apply to the public CSV download; whether a trading harness that stores series counts as a breach | MEASURED (text), UNKNOWN (reach) |
| Quiver Quantitative | Hobbyist 30 dollars a month or 300 a year; Trader 75 or 750; both personal non-commercial; Startup 250 or 2,500. No free tier stated ([Quiver plans](https://api.quiverquant.com/docs/plans-and-access)) | AI terms; rate limits | MEASURED |
| X API | Pay per use: 0.005 dollars per post read, 0.010 per user read; cap of 3 million post reads per month; same item not billed twice in one UTC day ([X API pricing](https://docs.x.com/x-api/getting-started/pricing.md)) | AI and storage terms (not opened) | MEASURED |
| Google Trends API | Alpha test, not open to everyone; rolling 5 years; daily to yearly ([Google Trends API](https://developers.google.com/search/apis/trends)) | Price, lag, use limits | MEASURED |
| Benzinga direct, Reddit API, Stocktwits, Glassnode, CryptoQuant, Dune, OpenInsider, Capitol Trades, Farside ETF flows | No primary page opened | Prices, limits and AI terms | UNKNOWN |

### Evidence by feed family

| Feed family | Study and sample | What it found | After costs and long-only | Tag |
|---|---|---|---|---|
| LLM headline scoring | [Lopez-Lira and Tang, arXiv version](https://arxiv.org/html/2304.07619): Oct 2021 to May 2024, 159,137 firm-headline days, 4,123 firms | Overnight long-short 34 bps a day, Sharpe 2.97, before costs. Long-only leg 8 bps a day, Sharpe 0.78, hit rate 50.90%. Short leg 26 bps, Sharpe 2.01 | Daily one-way turnover about 190%. Equal-weighted Sharpe 1.289 at 10 bps cost and minus 0.394 at 20 bps. Value-weighted is negative already at 5 bps (minus 0.398). Yearly Sharpe 6.54 (2021 Q4), 3.68 (2022), 2.33 (2023), 1.22 (Jan to May 2024) | MEASURED |
| LLM headline scoring, by size | [Lopez-Lira and Tang](https://arxiv.org/html/2304.07619) | Negative news drift: small minus 0.70%, mid minus 0.18%, large plus 0.06% (reverses). Positive news: 0.05% to 0.11% | Bad news matters mostly in small stocks; in large stocks it reversed | MEASURED |
| LLM backtests before the training cutoff | [Detecting lookahead bias in LLM forecasts](https://arxiv.org/html/2512.23847) | Models' predictive power is inflated where they have likely seen the outcome; the effect loses significance after the training cutoff | Any LLM news test must use only dates after the model's cutoff | MEASURED |
| Earnings drift (PEAD) | [Martineau, Critical Finance Review](https://econpapers.repec.org/article/nowjnlcfr/104.00000122.htm) | Prices now fully reflect surprises on the announcement day. Non-existent in large stocks since 2006; gone only recently in microcaps | No standalone strategy. Earnings dates are still useful to avoid gap risk | MEASURED |
| Insider buying (Form 4) | [Cohen, Malloy and Pomorski 2012, Journal of Finance](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.2012.01740.x) | "Opportunistic" insider trades earn value-weighted abnormal returns of 82 bps a month; routine traders about zero | Long-short abnormal return, before costs, old sample (period not shown on the abstract page). Not retested after 2015 here | MEASURED (abstract), UNKNOWN (current) |
| Congress trades | [Chen and Sacerdote, NBER WP 35041](https://www.nber.org/system/files/working_papers/w35041/w35041.pdf): 2012 to 2023, 71,333 trades, 334 members, 3,403 firms | All trades trail the CRSP value-weighted market by 5 bps (half month) and 26 bps (one year). Buys trail by 69 bps at one year. Party leaders trail by 4.37 points, committee-oversight trades by 2.77 points | Mean disclosure delay 33.1 days. "Neither on-time nor late filers earn statistically significant abnormal returns." Members trade stocks already drawing retail attention and follow analyst consensus | MEASURED |
| Google search attention | [Da, Engelberg and Gao 2011](https://onlinelibrary.wiley.com/doi/full/10.1111%2Fj.1540-6261.2011.01679.x): Russell 3000, 2004 to 2008 | More searches predict higher prices for 2 weeks, then reversal within the year | Temporary retail price pressure, not lasting value | MEASURED |
| Google Trends with machine learning | [Challet and Ayed 2014](https://arxiv.org/pdf/1403.1715) | About 17 bps a week in their backtest, and it hardly depends on whether inputs are past prices, Trends data or both | Trends adds little beyond past prices; keyword choice is the main bias | MEASURED |
| Search and Wikipedia topics | [Curme et al. 2014, PNAS](https://www.pnas.org/doi/10.1073/pnas.1324054111): 2004 to 2012 | Rising searches on politics and business topics tended to precede market falls; those two categories survived false-discovery correction (p = 0.01 and 0.04); shuffled data did not | Market-level, in-sample, old. Not a stock signal | MEASURED |
| WallStreetBets | [Bradley et al. 2024, RFS](https://academic.oup.com/rfs/article-abstract/37/5/1409/7486572) | Due diligence posts predicted returns before the GameStop squeeze; "This predictability is eliminated post-GME" | Gone | MEASURED |
| WallStreetBets, simple strategy | [Betzer and Harries 2022](https://link.springer.com/article/10.1007/s11408-022-00415-w): 2012 to Q1 2021 | Long buy posts, short sell posts: no alpha at holding periods from one day to one year | Gone | MEASURED |
| Stocktwits stock sentiment | [Cookson and Niessner](https://mipp.cl/wp-content/uploads/2018/10/CooksonNiessner2016.pdf) | Disagreement forecasts trading volume, not returns. Sentiment does predict returns; stocks that professionals are bullish on beat their bearish picks by almost 2% over 60 trading days | Long-short, before costs, older sample; would need a paid enterprise feed | MEASURED |
| Stocktwits Bitcoin sentiment | [Guégan and Renault](https://hal.science/hal-03205154/document): Aug 2017 to Dec 2019, about one million messages | Links to returns only up to 15 minutes; gone at lower frequencies | The authors say the effect is too small for a trader to profit | MEASURED |
| Market-wide short interest | [Rapach, Ringgenberg and Zhou 2016, JFE](https://ideas.repec.org/a/eee/jfinec/v121y2016i1p46-65.html) | Called "arguably the strongest known predictor of aggregate stock returns." Annual R-squared 12.89% in sample and 13.24% out of sample | Predicts the market, not single stocks; slow | MEASURED |
| Short interest abroad | [Gorbenko 2023, RAPS](https://academic.oup.com/raps/article/13/4/691/7127046) | Short interest predicts aggregate returns in 24 of 32 countries | Replication of the market-level effect | MEASURED |
| Low short interest stocks | [Meneghetti, Williams and Xiao](https://hal.science/hal-04211499/document), citing Boehmer, Huszar and Jordan 2010 | Bottom-decile short-ratio stocks show positive abnormal returns the next month | Second-hand citation; the 2010 paper itself was not opened | STATED |
| Bitcoin ETF flows | [Fabus et al. 2026, SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7545019): 386 sessions, 2024-01-11 to 2025-07-28 | 4.89 points per 1 billion dollars of inflow only because the UTC day contains the ETF session. Window after the close: 1.67. Window after flows are public: no positive association. Past returns predict flows | Not a tradable signal | MEASURED |
| Bitcoin ETF flows, second study | [Ashish 2026, Concordia MSc thesis](https://spectrum.library.concordia.ca/id/eprint/997714/): 494 days, Jan 2024 to Dec 2025 | Flows add no prediction once past returns are in (p = 0.325 to 0.943, lags 1 to 10). Returns predict flows (p under 0.001). GBTC flows a partial exception | Student thesis, not peer reviewed | MEASURED |
| On-chain cycle gauges (MVRV, Puell) | [Molnar 2026, arXiv](https://arxiv.org/html/2607.26188): BTC 2011 to 2026, four halving cycles, Coin Metrics MVRV | MVRV cycle peaks fell 5.88, 4.72, 3.96, 2.74. Every top-caller was silent at the October 2025 top. No cell of 36 survives false-discovery control | Single independent author; still a clear negative | MEASURED |
| Exchange flows, intraday | [Chi, Chu and Hao, arXiv 2411.06327](https://arxiv.org/pdf/2411.06327): Dec 2017 to Jan 2023 | BTC net inflows lack return predictive power except at 4 hours. USDT inflows predict BTC and ETH returns at 1 to 2 hours | Intraday, needs paid flow data | MEASURED |
| Funding carry as a trade | [Borri, Liu, Tsyvinski and Wu, arXiv](https://arxiv.org/html/2510.14435v2): Aug 2020 to May 2025 | Carry (long spot, short perp) Sharpe 6.45 full sample, 4.06 from 2024, negative in 2025 | We cannot short perps; shown only to note the decay | MEASURED |
| Funding carry as a warning | [Schmeling, Schrimpf and Todorov, BIS WP 1087](https://www.bis.org/publications/working-paper-1087-crypto-carry) | Carry can reach 60% a year; "a high crypto carry predicts future price crashes" | A crowding warning for a long-only holder | MEASURED |
| Funding rates and volatility | [Kim, Journal of Empirical Finance 2026](https://www.sciencedirect.com/science/article/abs/pii/S0927539826000939) | Perp-based predictors improve Bitcoin volatility forecasts in and out of sample, "particularly from funding rates and at longer forecast horizons" | Forecasts volatility, not direction | MEASURED (abstract) |
| Prediction markets, accuracy | [Diercks, Katz and Wright, FEDS 2026-010](https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf): FOMC and CPI since 2022 | On FOMC day, Kalshi median and mode mean absolute error 0.000 vs 0.010 for fed funds futures (p under 0.05). Headline CPI: Kalshi median and mode 0.063 vs Bloomberg consensus 0.081 (p under 0.10) | Good event odds; not an equity or crypto edge | MEASURED |
| Prediction markets, calibration | [Dickerson et al. 2026, PNAS](https://www.pnas.org/doi/10.1073/pnas.2615627123?doi=10.1073/pnas.2615627123): about one million resolved items on Polymarket, Kalshi, Manifold, Metaculus | Overall highly calibrated: p% events happened about p% of the time, with some bias in high-stakes areas | Context, not a trade | MEASURED |
| AI models trading prediction markets | [Prediction Arena, arXiv 2604.07355](https://arxiv.org/html/2604.07355): six models, 10,000 dollars each | Kalshi, 2026-01-12 to 2026-03-09: all six lost, minus 16.0% to minus 30.8%. Polymarket, Feb 9 to Mar 9: minus 2.68% to 0.00% | Real money, short period, small sample. Fits our own pilot finding | MEASURED |

## What it means for a small automated long-only account

- Monthly data fees of 30 to 450 dollars are a large drag on a small account before a single trade. Free feeds should come first.
- The big headline-news profits sat in the short leg, small stocks and very high turnover. A long-only account cannot use the short leg, and the turnover cost kills the rest.
- What remains useful is mostly risk control: when to hold back, size down or skip a name. This fits the playbook line that news, funding and on-chain data are risk alerts, not directional triggers (docs/playbook/02_crypto_what_works.md).
- The data history limits matter for testing. Free Kraken funding history covers about one year. FRED's free credit spread covers about three years. A test on those alone would be short.
- FRED's API terms are a real legal risk for an AI harness that stores data. Treasury Fiscal Data and Cboe files are safer first sources. Their reuse licences were not read, so they are not cleared either.
- Any LLM news test must use only dates after the model's training cutoff ([lookahead study](https://arxiv.org/html/2512.23847)).
- Any rule that passes must still meet the project pass marks: backtest_min_breakeven_cost_multiple, backtest_max_pbo, replay_max_drop_ratio_vs_hold, replay_min_deflated_sharpe and replay_min_shuffle_percentile in config/thresholds.yaml.

## What is worth testing here

Ranked by strength of evidence and fit with a long-only account. Rule settings named below (such as a VIX to VIX3M ratio of 1.0 or a 90th percentile) are test choices to pre-register, not project thresholds. Costs come from cost_model_bps_per_side_liquid_etf for ETFs; single stocks and crypto need their own modeled costs.

| Rank | Idea | Why it might work | Best evidence | Main weakness | Data and test that would confirm or kill it | Tonight, free, no key |
|---|---|---|---|---|---|---|
| 1 | Pause new stock entries when VIX is above VIX3M (curve inverted) | An inverted curve marks acute stress | Clean daily data: VIX from 1990, VIX3M from 2009 (MEASURED, Cboe files). No study on this exact rule was opened, so the edge is UNKNOWN | Stays in cash during fast rebounds | Cboe VIX and VIX3M files plus SPY daily bars; pre-register the ratio; train on early years, hold back the later years; compare with and without the pause after modeled costs. Kill if it fails the replay pass marks | Yes |
| 2 | Cut crypto size when funding is extreme | High carry predicts crashes ([BIS WP 1087](https://www.bis.org/publications/working-paper-1087-crypto-carry)); funding helps forecast volatility ([Kim 2026](https://www.sciencedirect.com/science/article/abs/pii/S0927539826000939)) | Two primary sources (MEASURED) | Funding can stay high for weeks in a bull run; free Kraken history is only about one year | Kraken funding history plus BTC daily prices; pre-register a percentile cut; measure whether worst 30-day drops fall without failing replay_max_drop_ratio_vs_hold. One year is too short to pass; longer history needs another free archive (not found) | Partial: only about one year of free history |
| 3 | Market-wide short interest as a slow stock exposure gauge | Short sellers appear informed about market cash flows ([Rapach et al.](https://ideas.repec.org/a/eee/jfinec/v121y2016i1p46-65.html)), replicated in 24 of 32 countries ([Gorbenko](https://academic.oup.com/raps/article/13/4/691/7127046)) | Peer-reviewed, out-of-sample R-squared 13.24% (MEASURED) | Monthly, market-level, published with a lag; the study data ends years ago | Aggregate FINRA short interest history (access route UNKNOWN), detrended as in the paper; test whether reducing exposure on high readings improves hold-back results | No: FINRA short interest history access not confirmed |
| 4 | Non-routine insider buying screen | Insiders buying with their own cash, outside a routine pattern | 82 bps a month long-short, old sample ([Cohen et al.](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.2012.01740.x)) | Old; long-short not long-only; fast bots now read Form 4; small-stock costs | Form 4 filings from SEC EDGAR for recent years; classify routine vs non-routine as in the paper; enter at the next open after the filing time; compare with the index after single-stock costs. Kill if excess return is indistinguishable from zero | Yes (EDGAR needs only a User-Agent) |
| 5 | Exclude heavily shorted stocks | Low short interest stocks did better in one cited study | Second-hand only (STATED) | Daily short volume is mostly market making; misses squeezes | FINRA daily short volume files plus twice-monthly short interest; exclude the top decile from a long-only rule; compare | Partial: daily files yes, short interest history not confirmed |
| 6 | LLM bad-news veto on held or candidate stocks | Bad news drift was large in small stocks (minus 0.70%) ([Lopez-Lira and Tang](https://arxiv.org/html/2304.07619)) | MEASURED, but large-stock bad news reversed (plus 0.06%) and Sharpe fell every year | Noise, churn, lookahead bias | SEC 8-K filings (free) or Alpaca news (key); only post-cutoff dates; compare a long-only rule with and without the veto | Partial: 8-K yes, Alpaca news needs a key |

Not worth testing as buy signals: Congress trades, WallStreetBets, Google Trends, standalone earnings drift, lagged Bitcoin ETF flows, MVRV top-calling, Fear and Greed as a trigger. Each has a primary study above showing no usable edge, or none was found.

## Not verified or unfinished

- Alpaca news: plan coverage, history start, numeric limits and any Benzinga limit on sending text to an outside LLM. UNKNOWN.
- Licences for Cboe files, Coin Metrics Community, DefiLlama, Kalshi and Polymarket read-only data, PR Newswire RSS and Treasury Fiscal Data were not read. UNKNOWN.
- Whether FRED's API terms reach the public CSV download. UNKNOWN.
- A free funding rate history longer than one year. Not found.
- A free route to the full FINRA short interest history. Not confirmed.
- The Cohen, Malloy and Pomorski sample period and routine-trade rule were not visible on the abstract page. The often-quoted 1989 to 2007 period is STATED.
- The Boehmer, Huszar and Jordan 2010 paper was not opened (only a citation of it).
- The VIX term structure rule has no opened study behind it. The idea is reasonable, but its edge is UNKNOWN until tested.
- Benzinga direct, Reddit, Stocktwits, Glassnode, CryptoQuant, Dune, OpenInsider, Capitol Trades and Farside: no primary pages opened. UNKNOWN.

## Sources

- [SEC EDGAR application programming interfaces](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [SEC accessing EDGAR data, fair access](https://www.sec.gov/edgar/searchedgar/accessing-edgar-data.htm)
- [Cboe VIX historical data](https://www.cboe.com/tradable_products/vix/vix_historical_data)
- [FINRA short sale volume data](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data)
- [FINRA equity short interest](https://www.finra.org/finra-data/browse-catalog/equity-short-interest)
- [CFTC Commitments of Traders](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)
- [Coin Metrics API docs](https://docs.coinmetrics.io/api/v4/)
- [DefiLlama API docs](https://defillama.com/docs/api)
- [Alternative.me Fear and Greed Index](https://alternative.me/crypto/fear-and-greed-index/)
- [Wikimedia analytics API access policy](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html)
- [Wikimedia API rate limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits)
- [Alpaca streaming news](https://docs.alpaca.markets/us/docs/streaming-real-time-news)
- [Alpaca news API reference](https://docs.alpaca.markets/us/reference/news-3.md)
- [Finnhub terms of service](https://www.finnhub.io/terms-of-service)
- [Massive individuals terms of service](https://massive.com/legal/individuals-terms-of-service)
- [Massive market data terms of service](https://massive.com/legal/market-data-terms-of-service)
- [Tiingo terms of service](https://www.tiingo.com/tos/)
- [NewsAPI terms](https://newsapi.org/terms)
- [GDELT about](https://www.gdeltproject.org/about.html)
- [FRED legal terms](https://fred.stlouisfed.org/legal/terms/)
- [Quiver Quantitative plans](https://api.quiverquant.com/docs/plans-and-access)
- [X API pricing](https://docs.x.com/x-api/getting-started/pricing.md)
- [Google Trends API](https://developers.google.com/search/apis/trends)
- [Lopez-Lira and Tang, Can ChatGPT forecast stock price movements](https://arxiv.org/html/2304.07619)
- [Detecting lookahead bias in LLM forecasts](https://arxiv.org/html/2512.23847)
- [Martineau, Rest in peace post-earnings announcement drift](https://econpapers.repec.org/article/nowjnlcfr/104.00000122.htm)
- [Cohen, Malloy and Pomorski, Decoding inside information](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.2012.01740.x)
- [Chen and Sacerdote, NBER WP 35041](https://www.nber.org/system/files/working_papers/w35041/w35041.pdf)
- [Da, Engelberg and Gao, In search of attention](https://onlinelibrary.wiley.com/doi/full/10.1111%2Fj.1540-6261.2011.01679.x)
- [Challet and Ayed, Google Trends predictability](https://arxiv.org/pdf/1403.1715)
- [Curme et al., Quantifying the semantics of search behavior](https://www.pnas.org/doi/10.1073/pnas.1324054111)
- [Bradley et al., Place your bets](https://academic.oup.com/rfs/article-abstract/37/5/1409/7486572)
- [Betzer and Harries, Will the Reddit rebellion take you to the moon](https://link.springer.com/article/10.1007/s11408-022-00415-w)
- [Cookson and Niessner, Why don't we agree](https://mipp.cl/wp-content/uploads/2018/10/CooksonNiessner2016.pdf)
- [Guégan and Renault, Stocktwits sentiment and Bitcoin](https://hal.science/hal-03205154/document)
- [Rapach, Ringgenberg and Zhou, Short interest and aggregate stock returns](https://ideas.repec.org/a/eee/jfinec/v121y2016i1p46-65.html)
- [Gorbenko, Short interest and aggregate stock returns: international evidence](https://academic.oup.com/raps/article/13/4/691/7127046)
- [Meneghetti, Williams and Xiao, The market for corporate control as a limit to short arbitrage](https://hal.science/hal-04211499/document)
- [Fabus et al., Spot Bitcoin ETF flows and Bitcoin returns](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7545019)
- [Ashish, The impact of Bitcoin ETF flows on price dynamics](https://spectrum.library.concordia.ca/id/eprint/997714/)
- [Molnar, Bitcoin runs on a clock](https://arxiv.org/html/2607.26188)
- [Chi, Chu and Hao, On-chain flows](https://arxiv.org/pdf/2411.06327)
- [Borri, Liu, Tsyvinski and Wu, Cryptocurrency as an investable asset class](https://arxiv.org/html/2510.14435v2)
- [Schmeling, Schrimpf and Todorov, BIS WP 1087 Crypto carry](https://www.bis.org/publications/working-paper-1087-crypto-carry)
- [Kim, Perpetual futures as predictors of Bitcoin volatility](https://www.sciencedirect.com/science/article/abs/pii/S0927539826000939)
- [Diercks, Katz and Wright, Kalshi and the rise of macro markets](https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf)
- [Dickerson et al., Calibration across one million collective forecasts](https://www.pnas.org/doi/10.1073/pnas.2615627123?doi=10.1073/pnas.2615627123)
- [Prediction Arena](https://arxiv.org/html/2604.07355)

## Appendix: endpoints checked live on 2026-11-25

Each was called by the checker with a User-Agent header and no key. HTTP status shown. MEASURED.

| Endpoint | Result |
|---|---|
| `https://data.sec.gov/submissions/CIK0000320193.json` | 200 |
| `https://efts.sec.gov/LATEST/search-index?q=insider&forms=4` | 200 |
| `https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=4&output=atom` | 200 |
| `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv` | 307 redirect, then 200 |
| `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv` | 307 redirect, then 200 |
| `https://cdn.finra.org/equity/regsho/daily/CNMSshvol20261124.txt` | 200 |
| `https://futures.kraken.com/derivatives/api/v3/tickers` | 200 |
| `https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol=PF_XBTUSD` | 200, about one year of hourly rows |
| `https://stablecoins.llama.fi/stablecoins` | 200 |
| `https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=btc&metrics=CapMVRVCur` | 200 |
| `https://api.alternative.me/fng/?limit=0` | 200 |
| `https://gamma-api.polymarket.com/events` | 200 |
| `https://api.elections.kalshi.com/trade-api/v2/markets` | 200 |
| `https://publicreporting.cftc.gov/resource/jun7-fc8e.json` | 200 |
| `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates` | 200 |
| `https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10` | 200 |
| `https://fred.stlouisfed.org/graph/fredgraph.csv?id=BAMLH0A0HYM2` | 200, data from 2023-11-27 only |
| `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/Bitcoin/daily/20261101/20261110` | 200 |
| `https://api.exchange.coinbase.com/products` | 200 |
| `https://www.federalreserve.gov/feeds/press_monetary.xml` | 200 |
| `https://www.bls.gov/feed/bls_latest.rss` | 200 |
| `https://www.prnewswire.com/rss/news-releases-list.rss` | 200 |
| `https://api.gdeltproject.org/api/v2/doc/doc` | 502 |
| `https://www.treasurydirect.gov/TA_WS/securities/announced/rss` | 406 |
| GlobeNewswire public companies RSS | 403 |
| `https://blog.kraken.com/product/asset-listings/feed` | 404 |

## Correction, 2026-11-25: terms of use for these feeds

Added after a second model opened each provider's terms. Where this section and the text above disagree, this section stands. The table says what a small private collector may do. It is a careful reading, not legal advice. The collector that follows these readings is `research_rig/feeds/collect_context.py`, with notes in `research_rig/feeds/SOURCES.md`.

What changes in practice:

- Not used until permission is in writing: Cboe VIX files, FINRA short volume files, Kraken Futures funding, Kalshi, global Polymarket.
- Cleared for private research: Treasury, SEC, Federal Reserve, Coin Metrics Community (non-commercial), DefiLlama's official stablecoin API (non-commercial), Polymarket US public API (no republishing).
- Coin Metrics and DefiLlama are non-commercial licences. Research does not assume they cover a strategy trading real money.
- Kraken's general terms also bar automation on its content. Research reads Kraken's documented public API and its published price history files as offered for exactly this use, but that is research's reading. STATED, flagged for the owner in `archive/decisions/morning_list_2026-11-25.md`.

November 25, 2026. A live unauthenticated response is not a licence. These readings apply to the private, automated research collector, not to every use of a provider’s data. MEASURED tags the primary text checked; the resulting scope call is a conservative interpretation, not legal advice.

| Feed | What document 19 says | What the opened terms say | Reading for this collector and next step |
|---|---|---|---|
| Cboe VIX and VIX3M | The historical CSVs work; no clear reuse licence was found. The ratio test is marked “Yes” for free data. | MEASURED: [Cboe website terms §2](https://res.cboe.com/terms) allow “one copy … for your personal non-commercial use,” but bar other storage in “an electronic retrieval system” and creating “a derivative work,” subject to consent or fair use. | **Unclear** for a repeated import that keeps values and a derived ratio. Disable; obtain written permission or choose a clearly licensed source. |
| FINRA Reg SHO daily short volume | Daily file opened. The short-volume check is marked partly testable because the files are available. | MEASURED: The [dataset page](https://www.finra.org/finra-data/browse-catalog/short-sale-volume) says data is “free for non-commercial use.” The linked [website terms](https://www.finra.org/terms-of-use) bar “scraping or harvesting tools (including robots),” and the separate [API agreement §3.4](https://developer.finra.org/finra-api-terms-service) requires “access credentials provided to Developer by FINRA.” | **Not allowed** by the website terms for robotic extraction; no explicit CDN exception found. Omit with no accounts or credentials. Obtain written permission or use the licensed API if the owner later authorizes it and terms fit. |
| Kraken Futures | Funding and open interest are public snapshots. The funding filter is marked partly testable using free public history. | MEASURED: [Kraken Global Terms](https://www.kraken.com/legal/global-terms) bar “any other forms of automation to engage in any activity on Our Content.” The [ticker API reference](https://docs.kraken.com/api-reference/market-data/get-tickers.md) documents a public endpoint, but does not say its data may be retained by this research collector despite those terms. | **Unclear** for this combination of automation and retention. Disable until Kraken confirms permission in writing or an applicable express API grant is located. |
| Coin Metrics Community | BTC data works. Licence and limits were not found. | MEASURED: The [official API source](https://github.com/coinmetrics/docs-website/blob/master/api.md) says “available for free for non-commercial use under a Creative Commons license.” The [official archives](https://github.com/coinmetrics/data) identify CC BY-NC 4.0, and the [licence](https://creativecommons.org/licenses/by-nc/4.0/legalcode.en) excludes uses primarily directed to “commercial advantage or monetary compensation.” The [Community guide](https://kb.talostrading.com/coinmetrics/packages/coin-metrics-community-data) lists 10 requests per six seconds per IP. | **Allowed** for non-commercial research with attribution. Do not assume the same for a live strategy using real money; get provider confirmation before broader use. |
| DefiLlama stablecoins | Free API works, but the API documentation did not show licence text. | MEASURED: [DefiLlama terms clauses 7 and 8](https://defillama.com/terms) grant “personal, non-commercial” use, exempt the “official public API” from the programmatic API restriction, prohibit robots on the Site and prohibit republication “in any form without permission.” The [official docs](https://api-docs.defillama.com/llms.txt) list the actual stablecoin endpoint. | **Allowed** under a narrow read for a private calculated change using the official API only, not site scraping or raw data copying. No repo data sample. Seek written permission for republication or any wider use. |
| Kalshi | Public list answered, and read-only terms were not checked. | MEASURED: [API Developer Agreement §3](https://assets.kalshi.com/Kalshi-Developer-Agreement.pdf) limits API use to “facilitating a members own trading on the Exchange.” [Website data terms](https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf) exclude “development of any software program” without prior written consent. | **Not allowed** for this off-venue collector without written permission. Do not collect, cache or sample. |
| Polymarket global and Polymarket US | The global Gamma list answered; read-only terms were not checked. | MEASURED: The [global terms](https://polymarket.com/tos) bar “data mining tools, robots, crawlers” for extracting data from the interface, though the [global docs](https://docs.polymarket.com/getting-started/api) describe programmatic market data access. The separate [Polymarket US API](https://docs.polymarket.us/api-reference/introduction) says “If you’re building something that displays market information … this is all you need.” The [US rulebook](https://polymarketexchange.com/files/legal/latest/rulebook) prohibits redistributing trading-system information unless authorized. | **Unclear** for global Gamma in this retained workflow, so it is not used. **Allowed** for one-off private reads from the distinct US public API; do not redistribute the prices without written permission. |
| Treasury Fiscal Data and daily bill rates | Treasury Fiscal Data worked, but open-data terms were unchecked. | MEASURED: [Fiscal Data Open Data Policy](https://fiscaldata.treasury.gov/about-us/) says data is “available to copy, adapt, redistribute, or otherwise use for non-commercial and commercial purposes.” The separate [daily bill rates government catalog](https://catalog.data.gov/dataset/daily-treasury-bill-rates-data) lists CC0. | **Allowed**. The Fiscal Data monthly bill average is a fallback, not the daily market rate or an alternative label for it. |
| SEC Form 4 | Non-routine open-market buys are marked feasible to test with EDGAR. | MEASURED: [SEC Webmaster FAQ](https://www.sec.gov/about/webmaster-faq.htm) says public filing content is “free to access and reuse.” The [Form 4 instructions](https://www.sec.gov/divisions/corpfin/topic-topics/forms/form4.pdf) define code P as “Open market or private purchase,” not as open-market-only. | **Allowed** under [SEC fair access](https://www.sec.gov/about/developer-resources). Treat code P as screening only. Open-market status and whether a purchase is non-routine need separate review. |
