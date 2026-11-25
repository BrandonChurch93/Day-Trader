# Check log for 19. Information feeds

Checked 2026-11-25 against /home/user/workspace/research2/information_feeds/REPORT.md. Each source was opened by the checker. Live endpoints were called with curl.

| # | Claim in report | Verdict | Source opened |
|---|---|---|---|
| 1 | Lopez-Lira and Tang: Oct 2021 to May 2024, 159,137 firm-headline days, 4,123 firms; long-short 34 bps a day, Sharpe 2.97; long-only 8 bps, Sharpe 0.78, hit 50.90%; short 26 bps | Confirmed | [arXiv 2304.07619](https://arxiv.org/html/2304.07619) |
| 2 | Lopez-Lira and Tang: turnover about 190%; EW Sharpe minus 0.394 at 20 bps; VW minus 0.398 at 5 bps; yearly Sharpe 6.54, 3.68, 2.33, 1.22 | Confirmed | [arXiv 2304.07619](https://arxiv.org/html/2304.07619) |
| 3 | Lopez-Lira and Tang published in JFE | Could not verify (arXiv page names no journal). Removed "JFE" | [arXiv 2304.07619](https://arxiv.org/html/2304.07619) |
| 4 | Large-cap combined drift 0.00% (Sharpe 0.06) | Could not verify. Removed | [arXiv 2304.07619](https://arxiv.org/html/2304.07619) |
| 5 | Martineau: PEAD gone for large caps since 2006; gone for microcaps "by 2016-2019"; a post-pandemic rebound paper | Corrected. Abstract says microcaps only "recently", no years. Rebound claim had no source; removed | [EconPapers](https://econpapers.repec.org/article/nowjnlcfr/104.00000122.htm) |
| 6 | Cohen, Malloy, Pomorski: 82 bps a month VW for opportunistic trades; routine about zero | Confirmed. Sample 1989 to 2007 and "over 50% routine" not shown on page; now STATED or dropped | [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.2012.01740.x) |
| 7 | NBER WP 35041: 2012 to 2023, 71,333 trades, 334 members, 3,403 firms; minus 5 bps and 26 bps; buys minus 69 bps; leaders minus 4.37; committee minus 2.77; delay 33.1 days | Confirmed. Authors added (Chen and Sacerdote) | [NBER PDF](https://www.nber.org/system/files/working_papers/w35041/w35041.pdf) |
| 8 | NBER: neither on-time nor late filers beat the market; follow analyst consensus and retail attention | Confirmed (quoted). "Chasing analyst upgrades" reworded to "follow analyst consensus" | [NBER PDF](https://www.nber.org/system/files/working_papers/w35041/w35041.pdf) |
| 9 | Da, Engelberg, Gao: plus 30 bps over 2 weeks | Corrected. Abstract gives direction and timing only, no magnitude. Number removed | [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111%2Fj.1540-6261.2011.01679.x) |
| 10 | Curme et al.: search strategies fail false-discovery correction against shuffled nulls | Corrected. Politics and business categories survived FDR (p 0.01, 0.04); only shuffled data failed | [PNAS](https://www.pnas.org/doi/10.1073/pnas.1324054111) |
| 11 | Challet and Ayed: Trends adds no predictability beyond prices | Confirmed in substance; added the 17 bps a week figure | [arXiv 1403.1715](https://arxiv.org/pdf/1403.1715) |
| 12 | Bradley et al.: WSB predictability gone after GME | Confirmed | [RFS](https://academic.oup.com/rfs/article-abstract/37/5/1409/7486572) |
| 13 | Betzer and Harries: zero alpha 1 day to 1 year; high attention linked to minus 7.66% to minus 8.5% | Partly corrected. No-alpha confirmed; the minus 7.66% to minus 8.5% figures not on the page; removed | [Springer](https://link.springer.com/article/10.1007/s11408-022-00415-w) |
| 14 | Cookson and Niessner: Stocktwits polarity does not predict next-day returns | Corrected. Paper says disagreement predicts volume, and sentiment does predict returns (professional bullish beat bearish by almost 2% over 60 days) | [Cookson and Niessner PDF](https://mipp.cl/wp-content/uploads/2018/10/CooksonNiessner2016.pdf) |
| 15 | Guégan and Renault: BTC Stocktwits signal up to 15 minutes, "2017-2018" | Corrected period to Aug 2017 to Dec 2019; added authors' no-profit conclusion | [HAL](https://hal.science/hal-03205154/document) |
| 16 | Rapach et al.: R-squared 12.89% in and 13.24% out of sample; "1.24% monthly" | Annual figures confirmed. Monthly 1.24% and 1973 to 2014 period not on page; removed | [IDEAS](https://ideas.repec.org/a/eee/jfinec/v121y2016i1p46-65.html) |
| 17 | International replication: 24 of 32 countries | Confirmed. Author added (Gorbenko). Period 2006 to 2016 not shown; removed | [RAPS](https://academic.oup.com/raps/article/13/4/691/7127046) |
| 18 | Boehmer, Huszar, Jordan: low short interest outperforms | Downgraded to STATED. Only a citation in another paper was opened | [HAL 04211499](https://hal.science/hal-04211499/document) |
| 19 | Fabus et al.: 386 sessions; 4.89 points per 1 billion; no association after alignment | Confirmed. Added 1.67 after-close coefficient and exact end date 2025-07-28 | [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7545019) |
| 20 | Ashish: 494 days, p 0.325 to 0.943, returns predict flows p under 0.001 | Confirmed. Noted it is an MSc thesis | [Concordia](https://spectrum.library.concordia.ca/id/eprint/997714/) |
| 21 | Molnar: MVRV peaks 5.88, 4.72, 3.96, 2.74; zero of 36 cells survive BH; missed Nov 2021 and Oct 2025 tops | Confirmed. Nov 2021: MVRV fired 240 days early, outside the 60-day window | [arXiv 2607.26188](https://arxiv.org/html/2607.26188) |
| 22 | Borri et al.: carry Sharpe 6.45, 4.06 from 2024, negative 2025 | Confirmed | [arXiv 2510.14435v2](https://arxiv.org/html/2510.14435v2) |
| 23 | BIS WP 1087: high carry predicts crashes | Confirmed (quoted) | [BIS](https://www.bis.org/publications/working-paper-1087-crypto-carry) |
| 24 | ScienceDirect 2026: funding improves out-of-sample vol forecasts at daily, weekly, monthly | Softened. Abstract says improvements "particularly from funding rates and at longer forecast horizons", not at each horizon | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0927539826000939) |
| 25 | FEDS 2026-010: Kalshi FOMC-day MAE 0.000; CPI MAE 0.063 vs Bloomberg 0.081, p under 0.01 | Corrected significance. CPI is one star, p under 0.10. FOMC-day is p under 0.05 vs fed funds futures 0.010 | [Fed FEDS PDF](https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf) |
| 26 | Prediction Arena: six models lost minus 16.0% to minus 30.8% on Kalshi | Confirmed. Added Polymarket minus 2.68% to 0.00% and dates | [arXiv 2604.07355](https://arxiv.org/html/2604.07355) |
| 27 | PNAS 2026: 1.014 million contracts | Confirmed (1,014,122 items, four platforms) | [PNAS](https://www.pnas.org/doi/10.1073/pnas.2615627123?doi=10.1073/pnas.2615627123) |
| 28 | Chi et al.: BTC inflows lack predictability except at 4 hours | Confirmed | [arXiv 2411.06327](https://arxiv.org/pdf/2411.06327) |
| 29 | Lookahead bias paper | Confirmed | [arXiv 2512.23847](https://arxiv.org/html/2512.23847) |
| 30 | FRED terms (k) AI ban, (l) storage ban; 120 requests a minute | Clauses confirmed verbatim. No numeric rate limit on the page; 120 removed | [FRED terms](https://fred.stlouisfed.org/legal/terms/) |
| 31 | SEC: 10 requests a second, User-Agent; latency under 1 s and under 1 min; nightly ZIP | Confirmed | [SEC fair access](https://www.sec.gov/edgar/searchedgar/accessing-edgar-data.htm), [SEC APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) |
| 32 | Tiingo: AI inference allowed via Approved Inference Providers on Power; train predictive models on Power; delete on cancellation | Corrected scope. Prompt use with approved providers applies to all plans; training non-generative predictive models is Power only; deletion confirmed for paid plans. Price and news depth not verified | [Tiingo terms](https://www.tiingo.com/tos/) |
| 33 | Massive: AI on your behalf only; no training; delete within 30 days | Confirmed; 30 days is in the market data terms section 8, not the individuals terms | [Massive individuals](https://massive.com/legal/individuals-terms-of-service), [Massive market data](https://massive.com/legal/market-data-terms-of-service) |
| 34 | Finnhub: personal use, delete on end, 60 per minute, 30 per second | 60 per minute not on terms page; removed. Rest confirmed | [Finnhub terms](https://www.finnhub.io/terms-of-service) |
| 35 | X API: 0.005 per post, 0.010 per user, no free tier, 3M cap, UTC dedup | Confirmed. "No free tier" softened: page lists promo credits | [X pricing](https://docs.x.com/x-api/getting-started/pricing.md) |
| 36 | Quiver prices | Confirmed; added Startup yearly 2,500 | [Quiver plans](https://api.quiverquant.com/docs/plans-and-access) |
| 37 | Wikimedia: 200 per minute compliant, 10 unidentified, 3 concurrent, CC0 | Confirmed | [Rate limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits), [Access policy](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html) |
| 38 | Alpaca news: since 2015, Basic 0 dollars includes it, 200 per minute | Could not verify on opened pages. Benzinga as a source confirmed by example. Moved to UNKNOWN | [Alpaca historical](https://docs.alpaca.markets/us/docs/historical-news-data), [Alpaca reference](https://docs.alpaca.markets/us/reference/news-3.md) |
| 39 | NewsAPI Developer plan development only; prices 449 dollars | Terms confirmed; prices not on terms page, removed | [NewsAPI terms](https://newsapi.org/terms) |
| 40 | GDELT use "academic, commercial, or personal" | Corrected wording to "academic, commercial, or governmental" | [GDELT about](https://www.gdeltproject.org/about.html) |
| 41 | Google Trends alpha, 5 years, 2-day lag | Alpha and 5 years confirmed; lag not stated; removed | [Google Trends API](https://developers.google.com/search/apis/trends) |
| 42 | DefiLlama unlocks Pro-only; Pro 300 dollars | Unlocks are "API Plan" confirmed; 300 dollars is listed for a premium plan; perp funding endpoint is also paid | [DefiLlama docs](https://defillama.com/docs/api) |
| 43 | Coin Metrics licence CC BY-NC, 10 requests per 6 s | Could not verify. Docs page shows neither. Marked UNKNOWN. BTC MVRV history from 2010-07-18 confirmed live | [Coin Metrics docs](https://docs.coinmetrics.io/api/v4/), live endpoint |
| 44 | Fear and Greed since Feb 2018 | Confirmed live: 3,216 rows from 2018-02-01. Terms: attribution required | [Alternative.me](https://alternative.me/crypto/fear-and-greed-index/), live endpoint |
| 45 | FINRA short interest 7th business day; CFTC Friday 3:30 pm for Tuesday | Confirmed | [FINRA](https://www.finra.org/finra-data/browse-catalog/equity-short-interest), [CFTC](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) |
| 46 | Cboe VIX since 1990, VIX3M since Sep 2009 | Confirmed live (1990-01-02, 2009-09-18). Licence wording "personal use, no redistribution" not found; UNKNOWN | Live files, [Cboe page](https://www.cboe.com/tradable_products/vix/vix_historical_data) |
| 47 | Live endpoint statuses | Confirmed for all, except SEC browse-edgar Atom returned 200 (report said 400). Cboe needs redirect follow | Live curl |
| 48 | New finding: FRED BAMLH0A0HYM2 CSV starts 2023-11-27 | Added (report implied long history) | Live curl |
| 49 | New finding: Kraken historical funding endpoint returns about one year only | Added; weakens the funding test | Live curl |
| 50 | Test designs used invented cost numbers (10 bps, 20 to 40 bps) | Replaced with config key cost_model_bps_per_side_liquid_etf and replay pass-mark keys | config/thresholds.yaml |
| 51 | VIX term structure filter "well documented" | Downgraded. No study was cited or opened; edge marked UNKNOWN | none |
| 52 | Perplexity API prices and AUP row | Removed (covered by docs/research/05; not rechecked) | n/a |
