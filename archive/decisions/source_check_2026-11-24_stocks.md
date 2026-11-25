# Fact Check: `Day-Trader/docs/playbook/01_stocks_what_works.md`

Checked against primary sources on 2026-11-24.
Scope: all 11 rows of the "Key numbers" table and all 8 bullets in "Rules for the build" that carry a number or a `[MEASURED]` tag. "Bottom line" contains no sentences with a number or a `[MEASURED]` tag.

## Key numbers

1. **Claim:** "Taiwan day traders predictably profitable net of fees | under 1% | 1992-2006 | MEASURED"
   - **Source URL:** https://ideas.repec.org//a/eee/finmar/v18y2014icp1-24.html (full text checked at https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/The%20Cross-Section%20of%20Speculator%20Skill.pdf)
   - **Verdict:** VERIFIED
   - **Source quote:** "Less than 1% of the day trader population is able to predictably and reliably earn positive abnormal returns net of fees." (Abstract). Full paper: "In the average year during our 1992-2006 sample period, about 450,000 Taiwanese individuals engaged in day trading." and "less than 1% of day traders (4,000 out of 450,000) are able to outperform consistently."
   - **Tag check:** Right. Peer-reviewed empirical study in the Journal of Financial Markets using full Taiwan Stock Exchange records (3.7 billion two-sided transactions).
   - **Omitted context:** Taiwan imposed a 0.3% (30 bps) transaction tax on all stock sales during 1992-2006 plus 5 to 14.25 bps one-way commissions, much higher than modern zero-commission US equity trading. In a typical single year, 17% to 20% of Taiwan day traders earned positive net returns; the "under 1%" figure specifically counts traders who can be predictably identified from prior-year returns as earning reliably positive abnormal returns in the following year (4,000 out of 450,000 at 5 bps commission, or 1,000 to 4,000 at the 14.25 bps statutory cap).

2. **Claim:** "Brazil day traders (300+ days) who lost money | 97% | 2013-2015 starters | MEASURED"
   - **Source URL:** https://ideas.repec.org/p/fgv/eesptd/525.html (full text checked at https://repositorio.fgv.br/bitstreams/0f00dd78-6909-4f91-84d5-aef8803e6436/download)
   - **Verdict:** OVERSTATED
   - **Severity:** Minor
   - **Source quote:** "We observe all individuals who began to day trade between 2013 and 2015 in the Brazilian equity futures market, the third in terms of volume in the world, and who persisted for at least 300 days: 97% of them lost money" (Abstract). Table 2 (p. 17) reports 88.5% lost gross, 91.0% lost after exchange fees, and 97.0% lost after both exchange and estimated brokerage fees (1,551 persistent traders out of 19,646 starters).
   - **Tag check:** Needs caveat. The data comes from Brazil's securities regulator (CVM), which is independent empirical data, but the cited document is an unrefereed FGV discussion paper (Working Paper 525) and brokerage fees were estimated rather than observed.
   - **Omitted context:** The study covers a single leveraged equity-index futures contract (mini-Ibovespa futures), not Brazilian cash-equity day traders, which is omitted in a stocks playbook. Only 1,551 of the 19,646 starters traded 300+ days; loss rates were lower for shorter tenures (e.g., 70.2% for 1-day traders). The analysis also excludes days where buy and sell contract counts differed, and omits income taxes, platform fees, and course costs.

3. **Claim:** "India intraday equity traders who lost | 71% | FY23 | MEASURED"
   - **Source URL:** https://www.sebi.gov.in/sebi_data/attachdocs/jul-2024/1721818140715.pdf
   - **Verdict:** VERIFIED
   - **Source quote:** "7 out of 10 individual intraday traders (71%) in equity cash segment incurred net losses in FY23." (Executive Summary, p. 2).
   - **Tag check:** Right. Official regulator report by SEBI using client-level data from the top 10 NSE brokers (covering about 86% of NSE cash-segment individuals; 68.9 lakh intraday traders in FY23).
   - **Omitted context:** The sample is heavily skewed toward very small, infrequent participants: 56% had annual intraday turnover under Rs. 50,000 and 63% executed fewer than 10 trades in FY23 (77% of the smallest turnover group lost). Among traders with 3 years of experience (active across FY19, FY22, and FY23), 54% lost in FY23, whereas 80% of very frequent traders (>500 trades/year) and 76% of traders with turnover above Rs. 1 crore lost. Net P/L deducts Indian brokerage, exchange, SEBI, stamp duty, STT, and GST charges.

4. **Claim:** "Retail SPX 0DTE losses | Estimated loss about $241k/day; $350k/day from May 16, 2022; excludes broker, regulatory and clearing fees | Feb 2021-Sep 2023 | STATED"
   - **Source URL:** https://wp.lancs.ac.uk/fofi2024/files/2024/04/FoFI-2024-146-Leander-Gayda.pdf
   - **Verdict:** VERIFIED
   - **Source quote:** "between February 2021 and September 2023, retail investors lost $241,000 on an average day; since the introduction of a daily expiration calendar in May of 2022, this number has grown to average losses of $350,000 per day." (Abstract). Main text: "On the average day, retail investors have lost $241,000 and since May 16th of 2022 $350,000 on 0DTE trades." Conclusion: "These numbers are conservative estimates as we disregard potential commissions paid to brokers, as well as regulatory and clearing fees."
   - **Tag check:** Right. This is an unrefereed conference working paper (Dec 2023 / FoFI 2024), so STATED is appropriate.
   - **Omitted context:** Retail trades are inferred indirectly from Cboe AIM price-improvement auction codes (SLAN/MLAT), which only capture orders up to 10 contracts, and trade direction is inferred via the Muravyev (2016) quote rule. Over $90M of the >$125M cumulative loss was due to effective bid-ask spreads, and gross-of-spread cumulative losses were flat after November 2022. Losses were driven by single-leg and debit orders ($364k/day average loss on debit orders), while credit orders averaged +$122k/day and some multi-leg strategies (such as put and call spreads) had positive median margin-adjusted returns.

5. **Claim:** "PDT $25k minimum replaced by intraday margin standards | effective June 4, 2026; phase-in ends Oct 20, 2027 | 2026-11-24 | MEASURED"
   - **Source URL:** https://www.finra.org/rules-guidance/notices/26-10
   - **Verdict:** VERIFIED
   - **Source quote:** "FINRA has adopted new intraday margin standards to replace in their entirety the outdated day trading margin requirements, including the day trade count requirements for designating a customer as a 'pattern day trader' and the $25,000 pattern day trader minimum equity requirement." and "Effective Date: June 4, 2026; Phase-in Period: Ends October 20, 2027".
   - **Tag check:** Right. Official FINRA Regulatory Notice rule text qualifies as MEASURED.
   - **Omitted context:** Brokers are permitted to phase in implementation over 18 months until October 20, 2027, so individual brokers may still enforce legacy PDT controls during the transition. The new rule introduces intraday margin deficit tracking (either real-time or end-of-day) and a 90-day freeze for customers who make a practice of failing to satisfy deficits above the lesser of 5% of equity or $1,000 within 5 business days; standard maintenance margin rules remain unchanged.

6. **Claim:** "Published predictor returns post-publication | 58% lower on average | 97 predictors | MEASURED"
   - **Source URL:** https://onlinelibrary.wiley.com/doi/10.1111/jofi.12365 (full text checked at https://gwern.net/doc/economics/2016-mclean.pdf)
   - **Verdict:** VERIFIED
   - **Source quote:** "We study the out-of-sample and post-publication return predictability of 97 variables shown to predict cross-sectional stock returns. Portfolio returns are 26% lower out-of-sample and 58% lower post-publication." (Abstract).
   - **Tag check:** Right. Peer-reviewed empirical study in the Journal of Finance.
   - **Omitted context:** The 97 predictors are exclusively cross-sectional long-short stock return predictors ("We do not study time-series predictability"), evaluated on gross returns without deducting transaction costs, mostly equal-weighted (96 of 97), with the sample ending in 2013. Of the 58% total decline, 26% occurred out-of-sample before publication and 32% after publication. Twelve of the 97 predictors had in-sample t-statistics below 1.50 in the authors' replication. Applying this figure to intraday or time-series strategies extrapolates beyond the study's scope.

7. **Claim:** "Basic high-turnover anomaly portfolios, before cost mitigation | Above 1% estimated monthly trading cost | US equities | MEASURED"
   - **Source URL:** https://www.nber.org/system/files/working_papers/w20721/w20721.pdf
   - **Verdict:** VERIFIED
   - **Source quote:** "The cost of trading the high-turnover strategies, at least when designed with complete disregard for trading costs, always exceeds 1% per month." (Section 4.1, p. 20). Table 3 Panel C (p. 19) reports estimated monthly trading costs from 1.06% to 1.78% across the six high-turnover strategies.
   - **Tag check:** Minor defect. Although Novy-Marx and Velikov (2016) was subsequently published in the Review of Financial Studies, the linked URL is the December 2014 NBER working paper, which explicitly states it has not been peer-reviewed.
   - **Omitted context:** The sample spans 1963-2012 (Table 2), including decades with far higher bid-ask spreads than modern US markets (the authors note a sharp downward trend in trading costs after 2000). The strategies are value-weighted long/short decile sorts across all US stocks with 90% to 94% one-sided monthly turnover, and costs are estimated via Hasbrouck (2009) Gibbs-sampler effective spreads assuming market orders (excluding price impact and commissions).

8. **Claim:** "QQQ VWAP, independent reproduction | In-sample Sharpe 1.754 (authors: 2.1); out-of-sample Sharpe about 0.7; estimated break-even below about 1 bp round trip | Sep 2023+ | STATED"
   - **Source URL:** https://www.quantconnect.com/terminal/cache/embedded_backtest_b115d0894231d55994b1068202f6c0ae.html
   - **Verdict:** VERIFIED
   - **Source quote:** Overall Statistics table: "Sharpe Ratio 1.754". Module docstring: "The original paper reports a Sharpe ratio of ~2.10 and a ~671% total return on QQQ (the NASDAQ-100 ETF) over 2018-2023" ... "Out-of-sample (Sep 2023 onward, parameters frozen) the Sharpe ratio decays toward ~0.7: a textbook case of post-publication anomaly decay." ... "The edge disappears under realistic retail transaction costs: the break-even sits below ~1 bp round-trip, well under real QQQ effective spreads."
   - **Tag check:** Right. Anonymous, non-peer-reviewed QuantConnect reproduction is appropriately tagged STATED.
   - **Omitted context:** The embedded backtest on the linked page only runs the in-sample window (`START_DATE = (2018, 1, 2)` to `END_DATE = (2023, 9, 28)`) with `LEVERAGE = 2.0`, `$0.0005/share` commission, and zero slippage/spread. The out-of-sample Sharpe (~0.7) and <1 bp break-even are asserted only in the code's docstring comments referencing an unlinked "full write-up", with no OOS backtest output shown on the page. The table's "As of" entry ("Sep 2023+") applies only to the OOS claim, not the 2018-2023 in-sample Sharpe of 1.754.

9. **Claim:** "Intraday signal families passing walk-forward gates | 0 of 14 | Futures study, primarily MNQ, 2021-25 | STATED"
   - **Source URL:** https://arxiv.org/pdf/2605.04004
   - **Verdict:** VERIFIED
   - **Source quote:** "Fourteen signal families were evaluated on 947 trading days of five-minute bar data spanning 2021 through 2025, under expanding-window walk-forward validation. Each signal had to clear five criteria simultaneously to pass... None passed all five." (Abstract, p. 1).
   - **Tag check:** Right. Single non-peer-reviewed arXiv preprint by an independent researcher is appropriately tagged STATED.
   - **Omitted context:** The 14 families tested were specifically 5-minute OHLCV intraday momentum patterns on Micro E-mini Nasdaq 100 futures (MNQ) and Micro Gold futures (MGC), not US cash equities. Two positive-control signals in the same paper (RTH Confluence Signal, OOS T = 3.11; London Session Signal B, OOS T = 4.30) using GMM regime classification and 60-75 minute holds did pass all five gates (though with disclosed parameter-search and fold-contamination caveats on RTH Confluence and a 1-bar delay sign flip on London Signal B). Out-of-sample testing covered only 2023, 2024, and partial 2025 (Jan-Aug); 2022 was training only. The author also discloses that the study began as a strategy search before being reframed as a falsification study, and used unadjusted concatenated quarterly futures contracts.

10. **Claim:** "Stocks-in-play ORB, top 20 (author backtest) | Sharpe 2.81, over 1,600% net | 2016-2023 | STATED"
    - **Source URL:** https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284 (full PDF checked at https://concretumgroup.com/wp-content/uploads/2026/02/A-Profitable-Day-Trading-Strategy-For-The-U.S.-Equity-Market.pdf)
    - **Verdict:** VERIFIED
    - **Source quote:** "A portfolio that consisted of the top 20 Stocks in Play achieved a total net performance of over 1,600%, with a Sharpe ratio of 2.81, and an annualized alpha of 36%." (SSRN Abstract). Full PDF reports "a total net return of 1,637%".
    - **Tag check:** Right. Non-peer-reviewed author backtest (co-author Andrew Aziz is affiliated with Bear Bull Traders and Peak Capital Trading), appropriately tagged STATED.
    - **Omitted context:** The backtest applies up to 4x intraday leverage ("We also set a maximum leverage constraint at 4x"). "Net" deducts only $0.0035/share commissions and includes zero bid-ask spread and zero slippage, which is a major omission for volatile breakout entries in news-driven stocks. The unfiltered ORB base strategy earned only a 0.48 Sharpe (3.2% annual return), and the 2016-2023 sample excludes major bear regimes such as 2000-2002 and 2008.

11. **Claim:** "Robinhood top-bought stocks | -4.7% average 20-day abnormal return | Robintrack sample | MEASURED"
    - **Source URL:** https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13183
    - **Verdict:** VERIFIED
    - **Source quote:** "Consistent with models of attention-induced trading, intense buying by Robinhood users forecasts negative returns. Average 20-day abnormal returns are -4.7% for the top stocks purchased each day." (Abstract).
    - **Tag check:** Right. Peer-reviewed empirical study in the Journal of Finance.
    - **Omitted context:** The Robintrack dataset spans only 26 months (May 2018 to August 2020), heavily influenced by the 2020 COVID retail trading boom. The -4.7% figure applies specifically to extreme herding episodes (the top 0.5% of daily positive percentage user changes, about 10 stocks/day). A contemporaneous Journal of Finance study (Welch 2022) found that the aggregate consensus Robinhood portfolio over mid-2018 to mid-2020 had positive timing and alpha, indicating the negative return is specific to extreme attention-herding spikes rather than aggregate retail holdings.

## Rules for the build

12. **Claim:** "Prioritize: (1) daily/weekly trend with volatility targeting on liquid ETFs; (2) factor tilts under 50% monthly turnover; (3) regime-conditional intraday trend on SPY/QQQ; (4) large-cap weekly reversal via limit orders; (5) stocks-in-play ORB, speculative. Our recommendation. [STATED] (research §5, shortlist)"
    - **Source URL:** https://www.nber.org/system/files/working_papers/w20721/w20721.pdf (Novy-Marx and Velikov, cited in research §5 and shortlist for the 50% monthly turnover threshold)
    - **Verdict:** OVERSTATED
    - **Severity:** Minor
    - **Source quote:** "Most of the anomalies that we consider with one-sided monthly turnover lower than 50% continue to generate statistically significant net spreads, at least when designed to mitigate transaction costs. Few of the strategies with higher turnover do." (Abstract).
    - **Tag check:** Right. Explicitly labeled "Our recommendation. [STATED]".
    - **Omitted context:** The rule omits two material qualifiers from Novy-Marx and Velikov: the 50% cutoff is **one-sided** monthly turnover (not total two-sided turnover), and even sub-50% anomalies often fail to produce statistically significant net excess returns without explicit cost-mitigation design (Table 3 Panel B shows several 14%-35% one-sided turnover anomalies had insignificant net returns before cost mitigation).

13. **Claim:** "Model spread plus slippage of at least 2-5 bps per side for liquid ETFs, and more for single stocks; reject any strategy whose break-even cost is under 2x modeled cost. Our recommendation. [STATED] (research §2, §4)"
    - **Source URL:** Research §2 and §4 (closest cost sources: https://www.quantconnect.com/terminal/cache/embedded_backtest_b115d0894231d55994b1068202f6c0ae.html and https://econpapers.repec.org/paper/chfrpseri/rp2497.htm)
    - **Verdict:** NOT IN SOURCE
    - **Severity:** Minor
    - **Source quote:** Neither "2-5 bps per side for liquid ETFs" nor a "2x modeled cost" rejection threshold appears in any primary source cited in research §2 or §4. The cited sources only report a break-even "below ~1 bp round-trip, well under real QQQ effective spreads" (QuantConnect) and "$0.001/share slippage" (Zarattini et al. SPY paper).
    - **Tag check:** Right. Explicitly labeled "Our recommendation. [STATED]".
    - **Omitted context:** Citing "(research §2, §4)" implies those sections' sources back the 2-5 bps and 2x thresholds, when in fact they are author-invented heuristics not grounded in the cited papers.

14. **Claim:** "Log every trial; compute Deflated Sharpe and PBO, require t > 3 for new predictors, and set a trial budget (roughly 45 variants for five years of daily data). [MEASURED] (research §4)"
    - **Source URL:** https://www.nber.org/papers/w20592 (Harvey, Liu, Zhu 2016); https://www.davidhbailey.com/dhbpapers/overfit-tools-at.pdf (Bailey et al. 2016); https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf (Bailey and Lopez de Prado 2014); https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf (Bailey et al. 2015)
    - **Verdict:** OVERSTATED
    - **Severity:** Minor
    - **Source quote:** Harvey, Liu, Zhu: "a newly discovered factor needs to clear a much higher hurdle, with a t-ratio greater than 3.0." Bailey et al. (2016, p. 1): "if only five years of daily stock market data are available as a backtest, then no more than 45 variations of a strategy should be tried on this data, or the resulting strategy will be overfit, in the specific sense that the strategy's Sharpe Ratio (SR) is likely to be 1.0 or greater just by chance (even though the true SR may be zero or negative)."
    - **Tag check:** Wrong. The sentence is a prescriptive build rule derived from theoretical/mathematical models (and cites an unrefereed 2016 tool paper for the 45-variant bound), not independent empirical data, official rule text, or a published price page.
    - **Omitted context:** The 45-variant bound assumes independent trials and specifically guards against a false-positive Sharpe ratio of 1.0 or higher; for lower target Sharpe ratios (such as the 0.5-1.0 range discussed in the research file), fewer independent trials suffice to produce a false positive, while correlated trials reduce the effective trial count. Harvey, Liu, Zhu's t > 3 cutoff is calibrated to cross-sectional academic factor mining and increases over time as more factors are tested.

15. **Claim:** "Use roughly 50% post-publication decay as a sizing stress test, not a forecast (the measured average was 58% across 97 predictors). [MEASURED] (research §2)"
    - **Source URL:** https://onlinelibrary.wiley.com/doi/10.1111/jofi.12365
    - **Verdict:** VERIFIED
    - **Source quote:** "We study the out-of-sample and post-publication return predictability of 97 variables shown to predict cross-sectional stock returns. Portfolio returns are 26% lower out-of-sample and 58% lower post-publication." (Abstract).
    - **Tag check:** Partially wrong. The parenthetical empirical figure (58% across 97 predictors) is MEASURED, but the prescriptive sizing rule ("Use roughly 50% post-publication decay as a sizing stress test") is an author recommendation (STATED).
    - **Omitted context:** As noted in item 6, McLean and Pontiff's 58% figure covers gross, mostly equal-weighted, cross-sectional long-short stock predictors through 2013 and explicitly excludes time-series and intraday strategies.

16. **Claim:** "Size by volatility target, at most quarter-Kelly of the stress-tested edge, and cut exposure as drawdown approaches 15-20%, following the Grossman-Zhou cushion idea. Our recommendation. [STATED] (research §6)"
    - **Source URL:** https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf (MacLean, Thorp, Ziemba 2010); https://onlinelibrary.wiley.com/doi/10.1111/j.1467-9965.1993.tb00044.x (Grossman and Zhou 1993)
    - **Verdict:** NOT IN SOURCE
    - **Severity:** Minor
    - **Source quote:** MacLean, Thorp, Ziemba (p. 4): "long term growth maximizing investors should bet Kelly or less" and "For example, half Kelly is delta = -1 and quarter Kelly is delta = -3" (illustrative only, not a cap). Grossman and Zhou (Abstract): "the optimal policy involves an investment in risky assets at time t in proportion to the 'surplus' W_t - alpha M_t" (no 15-20% drawdown threshold is given).
    - **Tag check:** Right. Explicitly labeled "Our recommendation. [STATED]".
    - **Omitted context:** Neither cited paper derives "at most quarter-Kelly" or a "15-20%" drawdown cutoff. Grossman and Zhou's model assumes continuous-time frictionless trading with a single risky asset and CRRA utility, and relies on an exogenous investor-chosen floor parameter alpha.

17. **Claim:** "Test strategy stop losses for trend; do not assume they help mean reversion. Keep separate system-level loss limits. [MEASURED] (research §6)"
    - **Source URL:** https://econpapers.repec.org/paper/hhssifrwp/0063.htm (Kaminski and Lo 2008 WP); https://dspace.mit.edu/bitstream/handle/1721.1/114876/Lo_When%20Do%20Stop-Loss.pdf?sequence=1 (Kaminski and Lo 2013/2014 JFM manuscript)
    - **Verdict:** OVERSTATED
    - **Severity:** Minor
    - **Source quote:** Kaminski and Lo (MIT manuscript, p. 19): "For a mean-reverting portfolio strategy, rho < 0; hence, the stop-loss policy hurts expected returns to a first-order approximation." and "On the other hand, for a momentum strategy, rho > 0, in which case there is a possibility that the second term dominates the first, yielding a positive stopping premium." (Sufficient condition: rho >= SR, p. 20). The second sentence ("Keep separate system-level loss limits") is not in Kaminski and Lo.
    - **Tag check:** Wrong. The rule combines a zero-cost analytical model with an unsupported operational prescription ("Keep separate system-level loss limits"); tagging the rule MEASURED is incorrect.
    - **Omitted context:** Kaminski and Lo's momentum vs. mean-reversion result is an analytical AR(1) derivation assuming zero transaction costs ("we shall assume kappa = 0 for the remainder of this paper") for a 0/1 portfolio-level switch into cash or bonds, not an empirical test of trade-level stop losses on trend or mean-reversion strategies. Their empirical tests applied stop losses only to a buy-and-hold US equity/futures portfolio switching into long-term bonds (1950-2004 monthly in the 2008 WP; 1993-2011 daily futures in the 2014 JFM version).

18. **Claim:** "Before enabling live intraday orders, verify and enforce the chosen broker's current PDT or intraday-margin controls; FINRA's implementation phase-in runs through October 20, 2027. [MEASURED] (research §1)"
    - **Source URL:** https://www.finra.org/rules-guidance/notices/26-10
    - **Verdict:** VERIFIED
    - **Source quote:** "Members that need more time to implement the rule change will be permitted to phase in their implementation over a period of 18 months, until October 20, 2027."
    - **Tag check:** Partially right. The October 20, 2027 phase-in deadline is official FINRA rule text (MEASURED), though the operational instruction to verify broker controls is a build recommendation.
    - **Omitted context:** Brokers can migrate at any point between June 4, 2026 and October 20, 2027, and may enforce either real-time intraday blocking or end-of-day intraday margin deficit calculations under the new rule.

19. **Claim:** "Paper gate before tiny live capital: at least 60 trading days AND 100 closed paper trades with models off, then shadow mode; go tiny live only after cost-aware out-of-sample and paper gates pass, with prewritten kill criteria. Scaling beyond tiny capital needs 6-12 months of live evidence. Keep SPY/QQQ intraday trend experimental unless a regime filter validates out of sample and actual round-trip costs are well below 2 bps. Our recommendation. [STATED] (research §2, Implications)"
    - **Source URL:** Research §2 and Implications (closest primary source for the cost threshold: https://www.quantconnect.com/terminal/cache/embedded_backtest_b115d0894231d55994b1068202f6c0ae.html)
    - **Verdict:** NOT IN SOURCE
    - **Severity:** Major
    - **Source quote:** No primary source cited in research §2 or Implications contains the 60-trading-day / 100-trade paper gate, the 6-12 month live-scaling gate, or the 2 bps round-trip threshold. The cited QuantConnect VWAP reproduction states: "the break-even sits below ~1 bp round-trip, well under real QQQ effective spreads." Furthermore, the playbook's own source file (`docs/research/01_stock_daytrading_evidence.md`, Implications #9) explicitly states: "Paper trade for 6-12 months, then go live at small size with pre-written kill criteria".
    - **Tag check:** Right. Explicitly labeled "Our recommendation. [STATED]".
    - **Omitted context:** The playbook quietly weakens the research file's own paper-trading requirement from 6-12 months down to 60 trading days (about 3 months) and 100 closed trades, while reassigning "6-12 months" to the live-scaling stage. It also cites "well below 2 bps" round-trip cost for SPY/QQQ intraday trend, which is looser than the cited QuantConnect reproduction's break-even of below ~1 bp round-trip.

## Verdict counts

- VERIFIED: 12
- OVERSTATED: 4
- WRONG: 0
- NOT IN SOURCE: 3
- UNREACHABLE: 0

## Single most serious problem found

Claim 19 ("Rules for the build", line 19, Major severity): the playbook prescribes going live with tiny capital after "at least 60 trading days AND 100 closed paper trades" while citing `(research §2, Implications)`, but neither threshold appears in any cited primary source and the linked research file's own Implications #9 requires "Paper trade for 6-12 months" before going live. The same bullet sets a round-trip cost bar of "well below 2 bps" for SPY/QQQ intraday trend, whereas the cited QuantConnect VWAP reproduction puts break-even below ~1 bp round-trip.
