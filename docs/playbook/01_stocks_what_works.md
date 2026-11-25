# Stocks: What Works and What Does Not
Source: docs/research/01_stock_daytrading_evidence.md
Last verified: 2026-11-24

## Bottom line
Assume no edge until logged out-of-sample results show otherwise; retail day traders mostly lose, and the popular day-trading papers are author backtests. Start with low-turnover daily/weekly trend and factor tilts that hold overnight. Treat intraday signals as experiments.

## Rules for the build
- Prioritize: (1) daily/weekly trend with volatility targeting on liquid ETFs; (2) factor tilts under 50% monthly turnover; (3) regime-conditional intraday trend on SPY/QQQ; (4) large-cap weekly reversal via limit orders; (5) stocks-in-play ORB, speculative. Our recommendation. [STATED] (research §5, shortlist)
- Models never emit orders or trade intents. Model outputs are only evidence tags, watchlist candidates, and veto/pause flags that fixed deterministic rules may consume. Orders come only from deterministic strategy code and always pass the risk engine. In shadow mode, model outputs are only logged. Our recommendation. [STATED] (research, Implications)
- Model spread plus slippage of at least 2-5 bps per side for liquid ETFs, and more for single stocks; reject any strategy whose break-even cost is under 2x modeled cost. Our recommendation. [STATED] (research §2, §4)
- Log every trial; compute Deflated Sharpe and PBO, require t > 3 for new predictors, and set a trial budget (roughly 45 variants for five years of daily data). [MEASURED] (research §4)
- Use roughly 50% post-publication decay as a sizing stress test, not a forecast (the measured average was 58% across 97 predictors). [MEASURED] (research §2)
- Size by volatility target, at most quarter-Kelly of the stress-tested edge, and cut exposure as drawdown approaches 15-20%, following the Grossman-Zhou cushion idea. Our recommendation. [STATED] (research §6)
- Test strategy stop losses for trend; do not assume they help mean reversion. Keep separate system-level loss limits. [MEASURED] (research §6)
- Enforce hard daily loss and order-count circuit breakers in code as operational safety; their effect on returns is unverified. [UNKNOWN] (research §6)
- Use closed bars only, survivorship-free universes, and point-in-time timestamps. Our recommendation. [STATED] (research §4)
- Before enabling live intraday orders, verify and enforce the chosen broker's current PDT or intraday-margin controls; FINRA's implementation phase-in runs through October 20, 2027. [MEASURED] (research §1)
- Paper gate before tiny live capital: at least 60 trading days AND 100 closed paper trades with models off, then shadow mode; go tiny live only after cost-aware out-of-sample and paper gates pass, with prewritten kill criteria. Scaling beyond tiny capital needs 6-12 months of live evidence. Keep SPY/QQQ intraday trend experimental unless a regime filter validates out of sample and actual round-trip costs are well below 2 bps. Our recommendation. [STATED] (research §2, Implications)
- Promotion to live capital is never automatic; it requires a written owner decision in docs/decisions/. Our recommendation. [STATED] (research, Implications)

## Key numbers
| Item | Value | As of | Tag | Source |
|---|---|---|---|---|
| Taiwan day traders predictably profitable net of fees | under 1% | 1992-2006 | MEASURED | [Barber et al. 2014](https://ideas.repec.org//a/eee/finmar/v18y2014icp1-24.html) |
| Brazil day traders (300+ days) who lost money | 97% | 2013-2015 starters | MEASURED | [Chague et al.](https://ideas.repec.org/p/fgv/eesptd/525.html) |
| India intraday equity traders who lost | 71% | FY23 | MEASURED | [SEBI](https://www.sebi.gov.in/sebi_data/attachdocs/jul-2024/1721818140715.pdf) |
| Retail SPX 0DTE losses | Estimated loss about $241k/day; $350k/day from May 16, 2022; excludes broker, regulatory and clearing fees | Feb 2021-Sep 2023 | STATED | [Beckmeyer et al.](https://wp.lancs.ac.uk/fofi2024/files/2024/04/FoFI-2024-146-Leander-Gayda.pdf) |
| PDT $25k minimum replaced by intraday margin standards | effective June 4, 2026; phase-in ends Oct 20, 2027 | 2026-11-24 | MEASURED | [FINRA Notice 26-10](https://www.finra.org/rules-guidance/notices/26-10) |
| Published predictor returns post-publication | 58% lower on average | 97 predictors | MEASURED | [McLean and Pontiff](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12365) |
| Basic high-turnover anomaly portfolios, before cost mitigation | Above 1% estimated monthly trading cost | US equities | MEASURED | [Novy-Marx and Velikov](https://www.nber.org/system/files/working_papers/w20721/w20721.pdf) |
| QQQ VWAP, independent reproduction | In-sample Sharpe 1.754 (authors: 2.1); out-of-sample Sharpe about 0.7; estimated break-even below about 1 bp round trip | Sep 2023+ | STATED | [QuantConnect reproduction](https://www.quantconnect.com/terminal/cache/embedded_backtest_b115d0894231d55994b1068202f6c0ae.html) |
| Intraday signal families passing walk-forward gates | 0 of 14 | Futures study, primarily MNQ, 2021-25 | STATED | [Mesfin 2026](https://arxiv.org/pdf/2605.04004) |
| Stocks-in-play ORB, top 20 (author backtest) | Sharpe 2.81, over 1,600% net | 2016-2023 | STATED | [Zarattini et al.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284) |
| Robinhood top-bought stocks | -4.7% average 20-day abnormal return | Robintrack sample | MEASURED | [Barber et al. 2022](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13183) |

## Do not do
- Do not buy 0DTE options. [STATED]
- Do not trade attention or news momentum; Robinhood top buys averaged -4.7% over 20 days. [MEASURED]
- Do not build sub-minute or spread-dependent scalping; HFT profits concentrate in the fastest firms. [MEASURED]
- Do not use leverage or 3x ETFs to reach published backtest returns. Our recommendation. [STATED]
- Do not let any model iterate strategies without the trial ledger. Our recommendation. [STATED]
- Do not force flat-at-close on momentum/reversal signals; their premia accrue overnight. [MEASURED]
- Do not let a model output an order, size, or trade intent, or auto-promote anything to live capital. Our recommendation. [STATED]

## Must measure ourselves
- Real fill slippage and effective spread on our broker for target ETFs and stocks.
- Whether intraday SPY/QQQ momentum exists in current (0DTE-era) regimes after costs.
- Whether stocks-in-play ORB survives realistic fills and pre-2016 data.
- Whether daily loss limits change returns for our strategies.
- Whether paper fills match tiny-live fills.
