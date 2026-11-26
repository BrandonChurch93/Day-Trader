# Idea round 50: swing-horizon rules (3 to 40 trading days)

Written: 2026-11-26 19:02 UTC.
Author: Idea Scout.
Status: RESEARCH NOTE (no price files read, no existing run, score, or measure scripts executed, no edits to `docs/QUEUE.md` or `research_rig/TRIAL_LEDGER.md`).

## Scope and account constraints

Following the owner's 2026-11-26 direction in `docs/DECISIONS.md`, this round screens 13 swing-horizon rule families (3 to 40 trading days) across US stocks and US-reachable crypto against four gates:

- Published out-of-sample evidence of a net gain per trade of 1% or more after realistic costs, not a few basis points.
- At least about 100 independent events in our data window (US stock bars since 2016, crypto bars since about 2017).
- Tradable in a small US retail account ($500 first, later more; long and, where a US retail account can do it, short).
- Not already closed in our ledger unless the swing-horizon version is materially different.

US retail short-sale floor (STATED): under [FINRA Regulatory Notice 21-24](https://www.finra.org/rules-guidance/notices/21-24) on Rule 4210(b)(4), "Rule 4210(b) requires a customer to deposit margin in cash or securities, which shall be at least the greater of: ... (4) equity of at least $2,000 except that cash need not be deposited in excess of the cost of any security purchased" and "Except for transactions described in (a)(4) and (a)(5) above, every short sale is subject to the $2,000 minimum equity requirement regardless of the amount involved." INFERENCE: at $500 equity, US stock trading is long-only cash; single-stock short rules become reachable only after the account is funded above $2,000 (plus locate and borrow fees). Small-account crypto shorting is legally reachable on US-regulated derivatives venues (Coinbase CFM perpetual-style futures, Kraken Pro margin) where contracts are listed, subject to funding and venue fees.

## Summary of all 13 families

| # | Family | Repo ledger status | Swing-horizon verdict | Ranked? |
|---|---|---|---|---|
| 1 | PEAD with filing-read surprise or guidance trigger | Queue 17 (Plan 68, ledger 213) closed on power; Replay 11 (5-day AI reader) held-back still open | Materially different if keyed to 8-K Item 2.02 guidance raises at 15 to 30 days; free consensus-free parsing unverified | Yes (Rank 2) |
| 2 | Analyst-revision and guidance-raise drift | Skipped in Round 17 (`docs/research/87_round_17_what_the_replication_libraries_say.md`) and `docs/research/95_where_we_stand_after_32_tests.md` | Skip analyst revisions (vanished post-2003; paid I/B/E/S); guidance-raise half folded into Rank 2 | No |
| 3 | 52-week-high and RS with market filter to cash and stop | Plain 52w-high dropped (`docs/research/51_stock_swing_evidence_checked.md`); Replay 14 failed | Materially different with SPY > SMA200 cash gate and hard stop; published OOS backtest has survivorship bias | Yes (Rank 3) |
| 4 | Pullback-in-uptrend entries | Index-ETF RSI(2) closed on power (Queue 109, Plan 67, ledger 211) | Skip single-stock version: 2019 to 2026 holdout is +20.8 bps/trade, far below 1% aim | No |
| 5 | Sector or industry momentum by ETF (1 to 3 months) | Replay 06 failed; plain industry momentum dropped in doc 51 | Skip: 1 to 3 month lookbacks lag SPY and equal-weight post-2009; value is tail risk, not >=1% per-trade alpha | No |
| 6 | Short-interest squeezes and their reversal | Not tested in ledger | Skip: DTC has no edge since 2021; post-squeeze reversal is 1 to 2 days, needs paid loan data and >=$2,000 equity | No |
| 7 | Index additions and deletions | S&P 500, Nasdaq-100, and small-cap index reconstitutions dropped (doc 51, Rounds 24 and 37) | Skip: S&P 500 effect fell to 0.1% to 0.3%; Russell 2000 pro-forma lists are licensed and annual (10 dates < 100) | No |
| 8 | Lock-up expiries and secondary offerings (short side) | Lock-ups skipped (Round 32); SEOs closed at feasibility (Queue 59, Plan 42) | Skip: borrow fees kill lock-up shorts (+0.41% at 20% borrow, -1.01% at 50%); SEO 3 to 21d moves are <1% and 424B late | No |
| 9 | Spin-offs in their first weeks | Closed on power (Queue 58, Plan 55, ledger 192) | Skip: 2011 to 2024 first-week child return is -2.1% (p = 0.06, short-side >=$2,000 + HTB); long rebound is 1 to 3 years | No |
| 10 | Insider cluster buying at multi-week holds | Closed on coverage (Queue 60, Plan 36) and power (Queue 15, Plan 56, ledger 193) | Skip: 20-session power was 9.20% at +53 bps net; overnight gap and 1.73% spread already kill tradable entry | No |
| 11 | Crypto cross-sectional momentum and reversal (1 to 4 weeks) | Replays 13 and 16 failed; Queue 110 closed on power | Skip: 2025 to 2026 OOS momentum alpha fell to -12.5% (t = -0.81); short reversal loses -29% net to turnover | No |
| 12 | Crypto trend following with volatility stop at weekly rebalancing | Replays 01, 04, 09, 22 failed; Plan 51 closed on power | Materially different with Donchian trailing midpoint stop and 25% vol target; >1% per trade gross, flat since April 2025 | Yes (Rank 1) |
| 13 | Token unlock drift | Queue 36 forward watch; Rounds 23, 24, 34 skipped standalone cliffs | Keep as multi-year forward watch only: large gross drop (-25% team unlocks) but <100 US-shortable cliff events | Yes (Rank 4, watch) |

## Family-by-family audit

### 1. PEAD with a surprise or guidance trigger read from the filing

Repo status (MEASURED): Queue 17 (Plan 68, ledger 213) tested plain accounting-SUE earnings drift on SEC filing clocks and closed before prices on synthetic power (7.15% to 10.58% power at +78 to +88 bps net against the 33% line). Replay 11 (AI earnings release reader, 5-day hold) earned +0.97% per trade (-0.58% vs SPY) on its design sample; its 2,146 held-back releases remain unspent. Queue 101 (earnings-date advancers) closed on zero qualifying EDGAR events.

Published evidence (STATED):
- On management guidance drift, [Das, Kim and Patro (NYU Stern conference paper)](https://web-docs.stern.nyu.edu/salomon/docs/conferences/das%20et%20al.pdf) examine 1995 to 2004 (8,386 baseline quarterly management forecasts from First Call): "Examining returns in the post-forecast period from two days after the announcement (day +2) until thirty days after (day +30), we document a significant upward drift in stock prices for both conservative and optimistic forecasts." They report: "In the optimistic group of forecasts the market-adjusted cumulative abnormal return (CAR) from day +2 to day +30 has a median (mean) value of 4.58% (5.45%)." Net of spreads: "For the optimistic group, alphas are significantly positive both over 15-day (1.50%, t = 4.20) and 30-day (2.13%, t = 2.66) holding periods." And: "These alphas are large enough to absorb the estimated mean (median) bid-ask spreads for these firms in the post-event period of 1.03% (0.65%)."
- On text-based earnings drift, [Meursault et al. (Federal Reserve Bank of Philadelphia WP 21-07)](https://www.philadelphiafed.org/-/media/frbp/assets/working-papers/2021/wp21-07.pdf) study 2010 to 2019 (85,160 observations across 4,701 firms): "We report that the text-based post-earnings-announcement drift (PEAD.txt) is larger than PEAD at every calendar quarter mark within a year for our sample of 2010 to 2019 and quintile split portfolios (Figure 1)." They report: "At every calendar quarter mark, PEAD.txt is much larger and growing: 2.87% to 1.54% on trading day 63, 4.61% to 2.7% on trading day 126, 6.51% to 3.87% on trading day 189, and 8.01% to 4.63% on trading day 252." Transaction costs are not explicitly deducted, and the headline figure is a long-short quintile spread from earnings call transcripts.
- On 2015 to 2024 consensus PEAD, [Agentic Sciences (IBES-CRSP PEAD, 2015 to 2024)](https://agentic-sciences.github.io/assets/papers/pead_earnings_surprise.pdf) study 27,318 quarterly earnings events: "Sorting 27,318 quarterly earnings events into quintiles by standardized earnings surprise, we find that stocks in the top surprise quintile (Q5) earn a cumulative abnormal return (CAR) of +3.76% over 60 trading days post-announcement, while bottom quintile stocks (Q1) experience a CAR of −5.08%." Returns are reported "before transaction costs."

Sample, post-sample, frequency, and data (STATED and UNKNOWN):
- Sample years: 1995 to 2004 (guidance drift), 2010 to 2019 (PEAD.txt), 2015 to 2024 (IBES PEAD). Post-2015 out-of-sample evidence specifically for free 8-K Item 2.02 guidance raises without paid I/B/E/S consensus is UNKNOWN.
- Events per year: roughly 800 to 2,700 quarterly filings per year in broad US samples, easily above 100 independent events since 2016.
- Data needed: SEC EDGAR Form 8-K Item 2.02 Exhibit 99.1 filings (free; we already hold SEC filing pipelines and Replay 11 infrastructure) plus daily US stock bars since 2016 (held). Paid I/B/E/S consensus estimates and paid earnings-call transcript archives are NOT held.
- Single most likely failure mode (INFERENCE): a company raising its own prior guidance range in an 8-K can still miss Wall Street consensus and drop, so without paid consensus data a filing-only guidance raise may not isolate positive surprise.

### 2. Analyst-revision and guidance-raise drift

Repo status (MEASURED): Monthly analyst-revision sorts were placed on the skip list in Round 17 (`docs/research/87_round_17_what_the_replication_libraries_say.md`), and copying single analyst upgrades was dropped before testing (`docs/research/95_where_we_stand_after_32_tests.md`).

Published evidence (STATED):
- [Altinkilic, Hansen and Ye (Journal of Financial Economics, 2016)](https://www.sciencedirect.com/science/article/abs/pii/S0304405X15001713) directly test post-revision return drift (PRD) after May 2003: "A key contribution is the observation that the average PRD from May 2003 to 2010 no longer consistently deviates from zero." They add: "Finally out-of tests confirm general absence PRD in the post-period, utilizing international analysts' revisions from other G7 nations Canada,, Germany Italy,, and the UK." And: "The new findings derived from the Earnings sample indicate that, after accounting for PEAD, PRD contains minimal incremental information attributable analysts in post-period confirming the source of drift."

Sample, costs, data, and verdict (STATED and INFERENCE):
- Sample years: May 2003 to 2010 US and G7 out-of-sample; drift vanished after 2003 even before costs.
- Data needed: historical sell-side analyst recommendation and EPS revision feeds (I/B/E/S, paid; not held).
- Single most likely failure mode: zero post-2003 drift after accounting for PEAD, plus paid data requirement. Skip analyst revisions; fold the free management guidance-raise half into Family 1 (Rank 2).

### 3. 52-week-high and relative-strength entries with a market filter to cash and a stop

Repo status (MEASURED): Plain 52-week-high proximity was dropped in `docs/research/51_stock_swing_evidence_checked.md` (`dmurav` 2002 to 2024: +0.098%/month, t = 0.32; `FFTY` IBD 50 breakout ETF trailed SPY +41.2% vs +321.1% over ~11 years). Plain S&P 500 12-month momentum failed Replay 14 (+203.8% and +207.8% vs SPY +264.6%). None of those repo tests combined a market-regime cash filter (SPY < SMA200) with a hard per-position stop-loss.

Published evidence (STATED):
- Point-in-time unfiltered baseline: [Backtested Strategies (52-Week High Momentum, George-Hwang, June 2026)](https://www.backtestedstrategies.com/strategies/52-week-high-momentum-backtest/) tests Norgate Russell 3000 Current and Past over 2001 to 2025 (free preview 2021 to 2025): "The backtest applies the rule to the Norgate Russell 3000 Current & Past universe using point-in-time membership." Across 1,664.6 trades per year, after costs and short-side rules, the strategy delivered CAGR 1.9%, Sharpe 0.3, and max drawdown -14.0%.
- Filtered and stopped OOS test: [AlpaTrade (CAN SLIM relative strength breakout backtest)](https://alpatrade.chat/strategies/6) tests a relative-strength rotation with a market cash filter and stop: "Template relative_strength — relative-strength rotation: every N sessions (at most weekly) hold the strongest names by trailing return (above their trend SMA), equal weight, a holding is kept while it still ranks in the top 2N (hysteresis against churn), cash when SPY < SMA200" with "Sell stop 7-8% below buy point" and "Alpaca SIP daily bars, adjustment=all (splits+dividends); 10 bps slippage per side; signals from the prior close (gap entries use the day's open)." On its out-of-sample window (2022-01-03 to 2026-10-09, 1,531 trades, 43.3% win rate), it reports CAGR +30.4% vs SPY +12.3%, Sharpe 1.34 vs 0.76, and max drawdown -17.5% vs -24.5%. However, the page explicitly warns: "Backtests use today's S&P 500 members, which flatters momentum and relative-strength rules in particular (survivorship bias)." Average gain per trade is not stated.

Sample, frequency, data, and verdict (STATED and INFERENCE):
- Events per year: ~320 trades per year in the AlpaTrade test (>100 independent events since 2016).
- Data needed: US daily stock bars since 2016 (held) plus survivorship-free point-in-time liquid universe membership (must be built from point-in-time ADV and price rules, not today's S&P 500 list).
- Single most likely failure mode: survivorship bias in the published OOS backtest and repeated stop-out whipsaws in choppy regimes, which may pull net return back below SPY as happened in Replay 14 and `FFTY`. Still materially different from Replay 14 because of the cash filter and hard stop; keep as Rank 3 strictly on a point-in-time universe.

### 4. Pullback-in-uptrend entries

Repo status (MEASURED): Queue 109 (Plan 67, ledger 211) tested RSI(2) pullbacks inside an uptrend in four US stock index ETFs and closed before prices on synthetic power (19.29% pass chance at +16.8 bps excess over 3.4 sessions).

Published evidence (STATED):
- Single-stock S&P 500 holdout: [KruegerAlgorithms (PropStockDip, Nov 2026)](https://kruegeralgorithms.com/en/products/propstockdip) tests daily S&P 500 pullbacks: "PropStockDip checks about 500 S&P 500 stocks once a day, shortly before the US close, buys the ones that had a sharp short pullback inside a long term uptrend, and sells them at the first recovery or after about two weeks at the latest." Using point-in-time S&P 500 members with broker costs ("0.02 USD commission per share and side, overnight financing, spread"):
- In-sample 2005 to 2018: "39,922 trades, +17.2 basis points per trade (t 2.1)".
- Holdout 2019 to 2026: "24,750 trades, +20.8 basis points per trade (t 2.0)".
- Multiple-testing verdict: "Global multiple testing correction q 0.21, not passed".

Sample, frequency, data, and verdict (STATED and INFERENCE):
- Gain per trade is +20.8 bps (+0.208%) net in the 2019 to 2026 holdout, roughly one-fifth of our 1% per-trade aim, and fails global multiple testing.
- Single most likely failure mode: edge per trade is too small (tens of basis points) relative to single-stock overnight gap noise and spread on a $500 account. Skip.

### 5. Sector or industry momentum by ETF over 1 to 3 months

Repo status (MEASURED): Replay 06 tested six slow trend and allocation rules on nine broad ETFs (2023 to 2026) and failed (best rule +15.4%/yr vs SPY +18.9%/yr). Plain Fama-French 48-industry momentum was dropped in `docs/research/51_stock_swing_evidence_checked.md` (+0.228%/mo, t = 1.45 in 2002 to 2024).

Published evidence (STATED):
- [horizonzhao (etf-momentum-rotation-backtest, Oct 2026)](https://github.com/horizonzhao/etf-momentum-rotation-backtest/blob/main/README.md) tests monthly dual-momentum rotation across 7 liquid ETFs (`SPY, QQQ, EEM, EWH, TLT, IEF, GLD`, cash `SHY`) from 2006-02 to 2025-12 (split at 2015-12-31, OOS 2016 to 2025, 10 bps one-way cost). Main pre-specified rule (6m, top 3): CAGR 9.7% vs Buy and Hold SPY 10.8%, Sharpe 0.734 vs 0.628, max drawdown -22.0% vs -55.2%. The 3-month lookback best Sharpe setting (3m, K = 7) earned 6.8% CAGR in both IS and OOS. The author concludes: "Honest takeaway: Value = crisis protection, not alpha. The strategy lags in most bull years." And: "Most of the benefit is trend-filtered diversification, not stock-picking. Holding all 7 assets with a trend filter has a Sharpe (0.78) at least as high as holding the top 3 (0.73). Evidence that ranking adds value is weak (beats 94% of random picks with the same filter, one-sided p ≈ 0.06)."

Sample, frequency, data, and verdict (STATED and INFERENCE):
- At monthly rebalancing across 10 years (2016 to 2026), there are ~120 rebalance dates, but net excess return over SPY is negative or near zero (far below 1% per trade).
- Single most likely failure mode: ranking sector ETFs over 1 to 3 months adds turnover without beating SPY or a simple trend filter. Skip.

### 6. Short-interest squeezes and their reversal

Repo status (MEASURED): Not yet tested or closed in our ledger.

Published evidence (STATED):
- Squeeze prediction (long side): [Opulence Alpha (Does short interest predict stock returns?, Sept 2026)](https://opulencealpha.ai/studies/short-interest) tests FINRA twice-monthly short interest and days-to-cover across 1,763 NYSE and Nasdaq common stocks from 2021 to Aug 2026: "Not in a way we could measure. Since 2021, the fifth of US stocks with the most days to cover beat the median stock over the next month 49 times in 100, against 50 for the fifth with the fewest: no measurable edge." Conclusion: "Heavy short interest did not reliably forecast a squeeze, nor, measured as days to cover, a fall."
- Post-squeeze reversal (short side): [Xu and Liu (PHBS Working Paper, Short Squeezes)](https://www.phbs.pku.edu.cn/__local/5/9E/3F/7595465FE19F6C2FFEFECF56742_EE82C28B_A7B2E.pdf?e=.pdf) study 57,052 firm-trading-day jump events across NYSE, AMEX, and NASDAQ from June 2006 through December 2020 using daily short-lending data: "In particular, for stocks in both the highest capital constraint decile and the highest short sale constraint decile, the average next-day price reversal is -4.79% (the second greatest among all portfolio groups); in contrast, for stocks in both the lowest capital constraint decile and the lowest short sale constraint decile, the average next-day daily return is 0.48% (i.e., no price reversal at all)." However, they warn on borrow costs: "We find that although almost all portfolios experience an increase in the cost of borrowing following the event, those that are more likely to have experienced a short squeeze (i.e., stocks with greater capital constraint and greater short sale constraint) saw the greatest jumps." And: "with the greatest magnitude (11.64%) observed in the portfolio with both the highest Day 0 Raw Return and the lowest Loanable Shares."

Sample, frequency, data, and verdict (STATED and INFERENCE):
- Long-side squeeze prediction has no measurable edge since 2021. Short-side post-squeeze reversal occurs on Day +1 (not 3 to 40 trading days), requires paid daily securities-lending utilization data (not held; free FINRA short interest is twice-monthly and 8 business days lagged), is blocked at $500 equity by FINRA Rule 4210 ($2,000 minimum), and hits severe borrow-cost spikes and recall risk on the exact stocks that reverse.
- Single most likely failure mode: unavailable locate, borrow fee spikes, and short-squeeze blow-up risk in a small US retail account. Skip.

### 7. Index additions and deletions

Repo status (MEASURED): S&P 500 additions and deletions were dropped in `docs/research/51_stock_swing_evidence_checked.md` (with 5-year NIXT deletions kept only as a long-horizon idea); Nasdaq-100 annual additions were skipped in Round 24; S&P SmallCap 600, CRSP US Small Cap, and MSCI Small Cap reconstitutions were skipped in Round 37 (paid or prohibited pro-forma archives); Replay 23 (large US IPOs ahead of indexing) failed its 2023+ freshness mark (-1.42% on 42 trades).

Published evidence (STATED):
- S&P 500 and broad index families: [Greenwood and Sammon (Journal of Finance 2025, HBS abstract)](https://www.hbs.edu/faculty/Pages/item.aspx?num=65745) report: "The abnormal return associated with a stock being added to the S&P 500 has fallen from an average of 7.4% in the 1990s to 0.3% over the past decade." And: "A similar pattern has occurred for index deletions, with large negative abnormal returns during the 1990s, but only 0.1% between 2010 and 2020." And: "Finally, we document a similar decline in the index effect among other families of indices."
- Small-cap reconstitutions: [Dimensional Fund Advisors (Index Reconstitution Effect Within Small Caps, 2025/2026)](https://www.dimensional.com/chmedia/490356/source/index-reconstitution-effect-within-small-caps.pdf) examines 2014 to 2023: "From 2014 to 2023, stocks that migrate into or out of the Russell 2000 Index exhibit returns in excess of the index in the month leading up to reconstitution (1.4% on average), with a reversal in month after (1.5% reversal on average)."

Sample, frequency, data, and verdict (STATED and INFERENCE):
- S&P 500 additions and deletions are now 0.1% to 0.3% gross (far below 1%). Russell 2000 reconstitution happens once a year in June (only ~10 independent calendar clusters since 2016, far below 100 independent events), pro-forma historical lists are paid/licensed, and shorting additions is blocked under $2,000 equity.
- Single most likely failure mode: decayed S&P 500 edge, licensed historical pro-forma data, and only 10 independent annual Russell dates since 2016. Skip.

### 8. Lock-up expiries and secondary offerings (short side)

Repo status (MEASURED): IPO lock-up expiries were skipped in Round 32 (`docs/121_idea_round_32.md`); marketed SEOs were closed at feasibility in Queue 59 (Plan 42: final 424B pricing supplements arrived 1 to 2 business days late in 12 of 14 sampled filings, and post-SEO 10-day returns in 2008 to 2021 were -0.29% mean). Re-checked here for the short side given the owner's willingness to short once the account grows above $2,000.

Published evidence (STATED):
- IPO lock-up expiries (short side): [What Works in Trading (US IPO lockup expirations, 2007 to 2025, Aug 2026)](https://whatworksintrading.substack.com/p/us-ipo-lockup-expirations-20072025) studies 1,123 US lockup expirations: "The lockup effect is real and replicates: −1.9663% mean abnormal return over the (−10, +1) window across 1,123 US lockup expirations, 2007–2025, t = −4.47." Subperiods hold: "2013–2018: −2.6759% (t = −3.48). 2019–2025: −1.9216% (t = −3.24)." However, borrow costs destroy the short: "Per event, net of institutional costs and zero borrow, the short makes +1.3663% and wins 54.68% of the time. At 20% borrow: +0.4139%, 48.98%. At 50%: −1.0146%." And: "Breakeven is roughly 10% annual borrow." Portfolio result: "Traded properly, the best realistic configuration returns 5.3639% a year against SPY’s 11.2252%, with a negative information ratio and a deflated Sharpe ratio of 0.000057."
- Secondary offerings / SEOs (short side): [Krishnan and Wu (MDPI JRFM, Oct 2022)](https://www.mdpi.com/1911-8074/15/10/473) examine 2,138 US SEO announcements from 2010 to 2015. Across the full sample, announcement-period abnormal returns over 3, 7, and 21 days vs S&P 500 were -0.24%, -0.57%, and +0.48% (VW: -0.26%, -0.63%, +0.32%; EW: -0.28%, -0.73%, -0.18%); six-month post-issue CAR was -2.97% (SP), -3.21% (VW), and -0.83% (EW).

Sample, frequency, data, and verdict (STATED and INFERENCE):
- Both families require stock shorting (blocked under $2,000 by FINRA Rule 4210). Even above $2,000, IPO lock-up shorting breaks even at ~10% annual borrow and turns negative at 50% borrow, while 3 to 21 day post-SEO moves average under 1% and EDGAR 424B pricing dates arrive 1 to 2 days late (Queue 59).
- Single most likely failure mode: hard-to-borrow fees (20% to 100%+ APR on recent IPOs) and late EDGAR pricing timestamps for SEOs. Skip both.

### 9. Spin-offs in their first weeks

Repo status (MEASURED): Queue 58 (Plan 55, ledger 192) closed before prices on synthetic power: 100 dated US spin-off distributions (2016 to 2025) gave 32.86% central synthetic power against a 50% floor at the closest published short-window gross gain (+2.11%, insignificant). The `CSD` spin-off ETF trailed SPY (+251.8% vs +321.1% over ~11 years, `docs/research/51_stock_swing_evidence_checked.md`).

Published evidence (STATED):
- [Trading Studio (Corporate Spinoffs, April 2026)](https://blog.tradingstudio.finance/corporate-spinoff-event-study-us/) tests 30 major US corporate spinoffs from 2011 to 2024 with next-day close entry: "The forced-selling effect is real: children underperform by -2.1% in the first week after entry, with 61% underperforming SPY. That's close to statistical significance (t = -1.95, p = 0.06) but doesn't clear the 5% bar." Long-horizon rebound takes a full year and is skew-driven: "Children show +8.0% mean excess return at T+252, with a median of +0.2%."

Sample, frequency, data, and verdict (STATED and INFERENCE):
- Only ~10 US spin-offs per year (~100 over 2016 to 2025, already measured in Plan 55). The first-week move is on the short side (-2.1%, p = 0.06), blocked under $2,000 equity and difficult to borrow in a newly distributed child stock; the long-side rebound is a 1-year hold (outside 3 to 40 trading days) with median +0.2%.
- Single most likely failure mode: low event count (~10/yr), borderline significance (p = 0.06), and short-borrow friction on new spin-off shares. Keep closed.

### 10. Insider cluster buying at multi-week holds

Repo status (MEASURED): Queue 60 (Plan 36, Form 4 officer and director cluster buys, 20-session hold) closed inconclusive on coverage (5.71% unresolved against 5% cap). Queue 15 (Plan 56, ledger 193) closed before prices on synthetic power: 2,391 clocked filing candidates (2016 to 2025) at a 20-session hold versus IWM had 9.20% central power at a modeled +53 bps net, far short of 50%.

Published evidence (STATED, already audited in `docs/research/51_stock_swing_evidence_checked.md`):
- As documented in `docs/research/51_stock_swing_evidence_checked.md`, Zhao (2026, `arXiv:2602.06198v2`) showed that the bulk of Form 4 cluster-buy excess return occurs in an untradable overnight gap (+3.27%) before a retail trader can enter at the next open, while average bid-ask spreads in the small-cap signal names are 1.73%, leaving modeled 20-session net excess at roughly +53 bps (Plan 56).

Sample, frequency, data, and verdict (STATED and INFERENCE):
- Already closed on power at 20 trading days (9.20% power). Extending the hold to 30 or 40 trading days increases return variance faster than drift and does not recover the overnight gap or narrow the small-cap spread.
- Single most likely failure mode: overnight gap leakage before next-open entry plus small-cap spread drag. Keep closed.

### 11. Crypto cross-sectional momentum and reversal at 1 to 4 week holds

Repo status (MEASURED): Replay 13 Rule A (weekly top-5 large coins) lost -66% to -76% in 2022, 2025, and 2026; Replay 16 (long hot 5, short futures) failed 0 of 4 marks; Queue 110 (weekly dip vs breakout) closed before prices on power (2.11% pass chance using Grobys et al. 2025 top-30 weekly winner-minus-loser spread of -0.19%, t = -0.13 in Aug 2020 to Dec 2023).

Published evidence (STATED):
- [prams2104 (crypto-momentum-backtest, Feb 2026)](https://github.com/prams2104/crypto-momentum-backtest) tests 25 liquid cryptocurrencies (`BTC, ETH, BNB, XRP, ADA, SOL, DOGE, AVAX, DOT, MATIC, LINK, UNI, LTC, ATOM, ETC, XLM, TRX, NEAR, APT, ALGO, VET, ICP, FIL, AAVE, SHIB`) across Training (2020 to 2022), Validation (2023 to 2024), and Out-of-Sample (2025-01-01 to 2026-02-05).
- For 20-day cross-sectional momentum: Training (2020 to 2022) net Sharpe 0.42, annual alpha 36.2%, t-stat 2.02 (p < 0.05); Validation (2023 to 2024) net Sharpe -0.48, annual alpha 13.5%, t-stat 1.08 (p = 0.28); Out-of-Sample (2025 to 2026) net Sharpe -2.18, annual alpha -12.5%, t-stat -0.81 (p = 0.42). Mechanism: "Pre-2023: Cross-sectional dispersion averaged 3.20%, momentum gross Sharpe = 1.12. Post-2023: Dispersion collapsed to 1.98% (-38%), momentum gross Sharpe fell to -0.68."
- For short-term cross-sectional reversal (1-day): "Real alpha exists in OOS (highly significant, t = 4.64***) but strategy is UNIMPLEMENTABLE. 138% daily turnover creates 101% annual cost drag, turning +73% gross return into -29% net return."

Sample, frequency, data, and verdict (STATED and INFERENCE):
- Both 1-to-4-week cross-sectional momentum (collapsed post-2022) and short-term reversal (killed by turnover and US retail fees) fail out of sample.
- Single most likely failure mode: post-2022 collapse in altcoin cross-sectional dispersion and US retail fee drag (40 to 90 bps/side). Keep closed.

### 12. Crypto trend following with a volatility stop at weekly rebalancing

Repo status (MEASURED): Replay 01 (BTC/ETH daily trend) failed PBO; Replay 04 (wide coin trend) failed 0 of 25; Replay 09 (7 crypto rules at Alpaca 35 bps) failed 0 of 7; Replay 22 (Fable range-break) failed 1 of 5 with 79.4% max drawdown; Plan 51 closed on power. None of those tests combined a monotone trailing stop with volatility-targeted sizing and a rebalance deadband.

Published evidence (STATED):
- [Zarattini, Pagani and Barbon (Catching Crypto Trends, Concretum Research, Feb 2026)](https://concretumgroup.com/wp-content/uploads/2026/02/Catching-Crypto-Trends.pdf) test Donchian Channel breakouts (lookbacks 5, 10, 20, 30, 60, 90, 150, 250, 360 days) with a monotone trailing midpoint stop and 25% annualized volatility targeting (using 90-day realized volatility, capped at 200%, with a 20% volatility-rebalance threshold) on survivorship-free CoinMarketCap data from January 2015 through March 2025.
- Rules: "A trend-following system is constructed such that as soon as the closing price hits the upper boundary of the Donchian Channel, a new long position is established. Each position is then maintained until the first closure below a trailing stop which is updated daily" where "the prevailing Trailing Stop used in day t+1 is the maximum between the Trailing Stop used in day t and the middle line of the Donchain channel computed at the end of day t."
- Bitcoin trade-level statistics (Table 2, Jan 2015 to Mar 2025, before costs): 10-day model had 156 trades, 40% win rate, +2.0% AvgRet (+4.7% AvgRet x Unit), Sharpe 1.55, MDD 27%; 20-day model had 78 trades, 47% win rate, +4.3% AvgRet (+10% AvgRet x Unit), Sharpe 1.60, MDD 26%; 30-day model had 49 trades, 49% win rate, +7.4% AvgRet (+17% AvgRet x Unit), Sharpe 1.61, MDD 24%.
- Diversified top-20 coins net of 10 bps cost and 20% rebalance threshold (Table 4): "A diversified strategy targeting the top 20 most actively traded cryptocurrencies would have produced net-of-fees Sharpe ratio 1.57, a maximum drawdown of just 11%, and a statistically significant alpha of 11% relative to Bitcoin." Cost sensitivity on BTC: "For instance, at 50 bps, the CAGR of the 5-day model is significantly reduced (from 34% to 18%) while longer-term models are less affected."
- Post-publication out-of-sample check: [AlgoEdge Insights (Nov 2026)](https://algoedgeinsights.beehiiv.com/p/catching-crypto-trends-the-nine-model-strategy-that-cut-bitcoin-s-worst-crash-from-83-to-20) replicated the Bitcoin 9-model ensemble at 0.10% per trade and tracked it after the paper's March 2025 cutoff: "Since April 2025, after the paper's data ends, it has been flat: a Sharpe of 0.05." And: "Bitcoin closed at a record of about $125,000 in October 2025, then fell 53% by June 2026. The strategy's worst loss in that period was −15%, but it made no money either."
- Additional 2022 to 2024 OOS reference: [Bui (arXiv:2602.11708, AdaptiveTrend)](https://ar5iv.labs.arxiv.org/html/2602.11708) tests 150+ Binance perpetuals (Jan 2022 to Dec 2024 OOS, 4 bps taker + slippage + funding) with ATR trailing stops: Vol-Scaled TSMOM earned 22.8% annualized return, Sharpe 1.83, MDD -16.1%; AdaptiveTrend (70/30) earned 40.5%, Sharpe 2.41, MDD -12.7%, but notes: "More frequent rebalancing (e.g., weekly) leads to excessive parameter instability and higher turnover costs, while quarterly rebalancing fails to adapt to the rapid regime shifts characteristic of crypto markets."

Sample, frequency, data, and verdict (STATED and INFERENCE):
- Across BTC, ETH, and 10 to 20 US-spot liquid coins since 2017, 10-to-30-day Donchian breakouts with a trailing midpoint stop generate well over 100 independent trades, average +2.0% to +7.4% gross per trade (large enough to clear 10 to 40 bps maker fees), work long-only in a $500 US spot account (cap weight at 100% rather than 200% leverage), and use coin daily bars we ALREADY HOLD.
- Single most likely failure mode: US retail fee tier (50 to 90 bps taker on Coinbase Intro) and extended sideways-chop regimes like April 2025 to October 2026 (Sharpe 0.05 post-publication). Keep as Rank 1 (restrict to 10-to-30-day horizons and weekly or deadband-throttled sizing to avoid 5-day fee bleed).

### 13. Token unlock drift

Repo status (MEASURED): Queue 36 tracks token unlocks; Rounds 23, 24, and 34 skipped standalone cliff unlocks on US-shortable coins because unlocks below 2% of supply show no material effect and only 1 confirmed >5% cliff unlock existed in the next 60 days across the 29 US-shortable coins (`ONDO` on January 18, 2027).

Published evidence (STATED):
- [Keyrock (From Locked to Liquidity, Dec 2024)](https://keyrock.com/from-locked-to-liquidity-what-16000-token-unlocks-teach-us/) analyzed 16,000+ unlock events across 40 tokens: "90% of unlocks create negative price pressure, regardless of size or type." Timing: "Token price impacts often start 30 days before the unlock event." And: "After the unlock, prices tend to stabilise within roughly 14 days, returning to neutral." By recipient: "Team unlocks trigger the worst crashes (-25%) with unsophisticated sell-offs." While: "Ecosystem development unlocks are among the few with positive effects (+1.18% on average)."
- [Tokenomist (What the Market Does Around a Token Unlock, Nov 2026)](https://tokenomist.ai/research/what-the-market-does-around-a-token-unlock) analyzed 846 unlocks from 2022 to November 2026: "For unlocks of 10% of market cap or more, funding was negative on 44 of every 100 unlock days, against 24 on ordinary days." And: "Part 1 of this series read 236 of those dates against price. It found that the price effect sat in young tokens with a thin float (few tokens trading freely), and that most of the move came before the date."

Sample, frequency, data, and verdict (STATED and INFERENCE):
- Gross price moves (-4.85% peer-relative to -25% on team cliffs) clearly exceed 1% per trade and occur over 7 to 30 days, and small-account US crypto shorting is legally possible on Coinbase CFM or Kraken Pro where listed.
- However, historical event count on US-shortable venues is far below 100 (Round 24 found 1 upcoming >5% cliff across 29 US-shortable coins in 60 days), and negative funding on 44% of big-unlock days erodes pre-unlock short carry.
- Single most likely failure mode: insufficient event count on US-shortable coins and crowded negative perpetual funding ahead of public unlock dates. Keep as Rank 4 (multi-year forward watch under Queue 36, not an immediate backtest).

## Ranked short list (4 candidates, at most 6)

Only 4 of the 13 families clear or plausibly approach the Round 50 gates without duplicating a closed ledger row:

1. **Rank 1 (Test first: data already held, $500 US spot long-only): Crypto 10-to-30-day Donchian breakout with monotone trailing midpoint stop and 25% volatility sizing (capped at 100% cash, weekly or 20% deadband rebalance).**
Basis: Zarattini, Pagani and Barbon (2026) show +2.0% to +7.4% gross per trade on BTC (10d to 30d) and Sharpe 1.57, MDD 11% net of 10 bps across top-20 coins; post-publication check (April 2025 to Oct 2026) is flat (Sharpe 0.05, MDD -15% during -53% BTC crash). Must be tested net of real US retail fees (40 to 50 bps/side) and judged on 2023+ and post-April-2025 holdout.

2. **Rank 2 (Feasibility and count first: free EDGAR 8-K, $500 US cash long-only): Form 8-K Item 2.02 explicit quantitative guidance raise ("beat-and-raise") held 15 to 30 trading days.**
Basis: Das, Kim and Patro found +1.50% (15d, t = 4.20) to +2.13% (30d, t = 2.66) alpha after spreads; PEAD.txt (2010 to 2019) showed text surprises beat accounting SUE. Distinct from closed Queue 17 (plain XBRL SUE) and Replay 11 (5-day hold). Must pass a no-price feasibility and count audit verifying how many 8-K Item 2.02 exhibits contain an unambiguous self-referenced guidance raise (new range midpoint strictly above prior range midpoint stated in the same release) without paid consensus data.

3. **Rank 3 (Point-in-time universe check first: $500 US cash long-only): 52-week-high and relative-strength breakout with SPY > SMA200 cash filter and 7% to 8% hard stop-loss (10 to 40 trading days).**
Basis: AlpaTrade OOS (2022 to 2026, 1,531 trades, 10 bps/side) reported +30.4% CAGR vs SPY +12.3% (Sharpe 1.34, MDD -17.5%) with the cash gate and stop, whereas unfiltered George-Hwang (Backtested Strategies 2026) and Replay 14 failed. Because AlpaTrade used current S&P 500 members (survivorship bias), our test MUST run on a survivorship-free point-in-time US liquid stock universe (built from historical dollar-volume and price filters before any return check) and pass pre-data power.

4. **Rank 4 (Forward watch only: do not backtest yet): Pre-unlock short drift (T-14 to T+1) on >=5% circulating-supply team/investor cliff unlocks listed on US-shortable crypto venues (Coinbase CFM or Kraken Pro).**
Basis: Keyrock (16,000+ unlocks, -25% team unlocks) and Tokenomist (846 unlocks, 2022 to 2026) confirm large gross moves, and US retail accounts can short listed crypto contracts at $500. Blocked from immediate replay by tiny US-shortable event count (<100) and negative funding drag (44% of >=10% unlock days). Continue forward logging under existing Queue 36 until >=30 US-shortable >=5% cliff events accumulate.

## Proposed queue rows (text only; `docs/QUEUE.md` not edited)

| Proposed ID | Candidate | First gate before any price or replay | Why it is not a repeat |
|---|---|---|---|
| R50-A | Crypto Donchian breakout (10d, 20d, 30d ensemble) + monotone trailing midpoint stop + 25% vol sizing (capped at 100%, 20% rebalance deadband), long-only US spot coins since 2017 | Pre-data power screen at US retail maker/taker fees (25 bps and 50 bps/side) and explicit post-April-2025 OOS mark | Replays 01, 04, 09, 22 had no volatility targeting or monotone midpoint trailing stop |
| R50-B | US stock Form 8-K Item 2.02 self-referenced quantitative guidance raise (new midpoint > prior midpoint in Exhibit 99.1), next-open entry, 20-trading-day hold vs SPY, long-only | No-price EDGAR feasibility and count pilot on 2016 to 2025 filings (target >=400 clean dated raises without paid consensus) + synthetic power screen | Queue 17 used XBRL SUE only (no guidance text); Replay 11 is a 5-day hold |
| R50-C | US stock 52-week-high / relative-strength breakout + SPY > SMA200 cash filter + 8% hard stop, point-in-time liquid universe, 10 to 40 day swing hold, long-only | Build survivorship-free point-in-time liquid stock roster (no price-return peek) + pre-data synthetic power screen against SPY | Replay 14 had no SPY cash filter and no hard stop; Doc 51 dropped unfiltered 52w-high |
| R50-D | Fold into existing Queue 36 (forward watch): log >=5% team/investor cliff unlocks on US-shortable Coinbase CFM and Kraken Pro pairs with live funding rates | Count-only forward watch; do not test until >=30 US-shortable events exist | Extends Queue 36 with explicit funding-rate logging from Tokenomist (2026) |
