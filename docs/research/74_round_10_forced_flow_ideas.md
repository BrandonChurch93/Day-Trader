# Round 10: Forced-flow and known-clock ideas for a $500 US retail account

Status: CURRENT as of 2026-11-25 UTC. Metadata and published evidence only; no return calculations run, no repo files modified, and no dropped ideas from Rounds 1 to 9 repeated without new evidence. All sources linked below were opened directly.

## Top three to test first

1. Candidate 1: Market-wide dividend payment-day buying pressure (`SPY` long on top-quintile aggregate dividend pay days, Q1 to Q3). Why first: peer-reviewed in the American Economic Review lineage with 90+ years of US data plus 58 international markets, strongest in the three decades after 1990, 100% long-only `SPY` (zero shorting, ~1 bp spread on a $500 US retail account), ~35 to 50 trades per year, and uses Alpaca SIP `SPY` we already hold plus a public S&P 500 dividend pay-date calendar (2019 to 2026 is clean post-sample).
2. Candidate 2: Corporate bond and credit ETF month-end index extension (`LQD`, `HYG`, `MBB`, `TIP` long for the final 3 sessions of the month). Why second: direct mechanical extension of Replay 25 (`TLT` month-end, which passed 9 of 9 marks) to non-Treasury fixed-income benchmarks that rebalance on the exact same last-business-day clock, 100% long-only with 1 to 2 bps spreads on a $500 account, 12 trades per year per ETF, and requires zero new data because Alpaca SIP from 2016 already holds all four ETFs.
3. Candidate 3: Intraday Treasury auction-day concession and reversal (`TLT` and `IEF` around 1:00 PM ET 10Y and 30Y auctions). Why third: backed by 33 years of intraday NY Fed evidence through July 2024 showing a clean 6-hour inverted-V yield cycle (~6 to 10 bps ETF price swing vs 1 to 2 bps spread), ~24 auctions per year, and uses Alpaca SIP minute bars we already hold plus the free public TreasuryDirect auction calendar. Crucially, post-2010 HBS evidence rules out the naive multi-day post-auction hold, so we test only the tightly timed intraday auction-day window.

## Summary table (13 candidates)

| # | Candidate | Tradable on $500 US account | Trades/yr | Data held? | Verdict |
|---|---|---|---|---|---|
| 1 | Market-wide dividend pay-day buying pressure (`SPY`) | Long `SPY` | 35 to 50 | Partial (SIP held; need pay-date calendar) | KEEP |
| 2 | Credit and MBS ETF month-end extension (`LQD`, `HYG`, `MBB`, `TIP`) | Long ETFs | 12 per ETF | Yes (Alpaca SIP 2016+) | KEEP |
| 3 | Intraday Treasury auction-day cycle (`TLT`, `IEF`, `TBF`) | Long `TLT`/`IEF`, inverse `TBF` | ~24 | Partial (SIP minute bars held; need free TreasuryDirect dates) | KEEP WITH CHANGES |
| 4 | Kalshi favorite-longshot bias on settlement clocks (maker >=75c) | Kalshi binary contracts | 100+ | Partial (Kalshi public API) | KEEP WITH CHANGES |
| 5 | Target-Date Fund quarter-end equity-bond rebalancing (`SPY`/`TLT`) | Long `SPY`/`TLT`, inverse `SH`/`TBF` | 4 to 12 | Yes (Alpaca SIP 2016+) | KEEP WITH CHANGES |
| 6 | Closed-end fund post-rights-offering snapback | Long CEFs post-expiry | 5 to 15 | Partial (SIP held; need SEC N-2 event table) | KEEP WITH CHANGES |
| 7 | Leveraged ETF MOC-to-next-open reversal | Long/inverse index ETFs | 20 to 40 | Yes (Alpaca SIP 2016+) | DROP |
| 8 | S&P 500 and Nasdaq 100 quarterly reconstitutions | Long single stocks | 15 to 25 | Partial (SIP held; need index notices) | DROP |
| 9 | Commodity index Goldman Roll (`USO`/`SCO` days 5 to 9) | Outright `USO`/`SCO` only | 12 | Yes (Alpaca SIP 2016+) | DROP |
| 10 | Option expiration market-maker hedge rebalancing (`SPY`/`QQQ`) | Index ETFs | 12 | No (needs paid options OI/gamma) | DROP |
| 11 | Closed-end fund activist and periodic tender offers | Long CEFs into Schedule TO | 10 to 20 | Partial (SIP held; need Schedule TO) | DROP |
| 12 | Token cliff unlocks on the 36 US-shortable coins | US perps / Kraken US margin | <5 clean cliffs | Partial (Coinbase/Kalshi candles; need unlock DB) | DROP |
| 13 | US exchange listing notices for already-US-shortable coins | US perps / Kraken US margin | ~0 to 2 | Partial (Coinbase/Kalshi candles; need listing notices) | DROP |

## Candidate details

### 1. Market-wide dividend payment-day buying pressure (`SPY`)

- STATED source: Hartzmark and Solomon (working paper Feb 2022, published 2025 in American Economic Review Vol. 115), [Predictable Price Pressure](https://www.fese.eu/app/uploads/2025/01/ppp-021722.pdf). Exact quote: "Buying pressure from dividend payments (announced weeks prior) predicts higher value-weighted market returns, with the top quintile of payment days four times higher than the lowest."
- STATED sample and post-publication test: US CRSP stocks 1926 to 2018 plus 58 international markets 1986 to 2017. The paper notes the three decades after 1990 had the three largest decade coefficients; 2019 to 2026 is untested post-sample.
- STATED mechanical reason: Mutual funds and ETFs receive cash dividends on scheduled payment dates (known weeks in advance) and mechanically reinvest roughly half before month-end, generating uninformed market-wide buying pressure (weak or absent in December/Q4 when mutual funds make year-end distributions). Exact quote: "During the fourth quarter, dividend payments do not predict market returns."
- STATED effect size vs US retail costs: Exact quote: "Daily value-weighted returns are 12.8 b.p. higher if dividends are in the top 5 days of the past 250, and 4.8 b.p. higher if they are in the top 50 days." Against ~1 bp `SPY` bid-ask spread and $0 commission on a $500 US retail account, top-50 (4.8 to 5.9 bps/day) and top-quintile Q1 to Q3 days clear round-trip costs by 2.5x to 6x.
- STATED trades per year: ~35 to 50 trading days per year (top-50 aggregate dividend payment days excluding Q4/December).
- MEASURED / STATED data: We already hold Alpaca SIP `SPY` daily and minute bars from 2016; we only need a public historical S&P 500 constituent dividend payment-date calendar (free via SEC/Nasdaq/Alpaca corporate actions).
- Verdict: KEEP.

### 2. Corporate bond and credit ETF month-end index extension (`LQD`, `HYG`, `MBB`, `TIP`)

- STATED sources: Hartley and Schwarz, [Predictable End-of-Month Treasury Returns](https://www.kristaschwarz.com/EOM.pdf) (insurer month-end benchmark rebalancing), plus S&P DJI [iBoxx iShares USD High Yield Corporate Bond Index Methodology](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-iboxx-ishares-usd-high-yield-corporate-bond-index.pdf) and [iBoxx iShares Investment Grade Corporate Bond Index Guide](https://www.spglobal.com/spdji/en/documents/methodologies/iBoxx%20iShares%20$%20Investment%20Grade%20Corporate%20Bond%20Index%20Guide%20(last%20updated%20September%202022).pdf). Exact quotes: "The excess Treasury returns that we document exploit a systematic richening of Treasury coupon securities in the last days of the month." "The iBoxx iShares USD High Yield Corporate Bond Index is rebalanced monthly on the last business day of the month."
- STATED sample and post-publication test: Hartley and Schwarz cover 1990 to 2018 Treasuries and 1990 to 2016 insurer transactions, citing prior corporate-bond month-end studies (Schneeweis and Woolridge 1979; Jordan and Jordan 1991). Our own Replay 25 verified the Treasury window through 2026; corporate (`LQD`, `HYG`), MBS (`MBB`), and TIPS (`TIP`) ETFs remain untested by us.
- STATED mechanical reason: Like the US Treasury index, corporate, high-yield, MBS, and TIPS benchmarks rebalance on the last business day of each month, adding newly issued bonds that settled during the month and dropping <1-year maturities, forcing passive trackers and insurers to buy duration at month-end.
- STATED effect size vs US retail costs: In Hartley and Schwarz, 10-year Treasuries returned 25 bps/month over the final 3 sessions (Sharpe ~1). `LQD` (~8.5 yr duration), `TIP` (~6.5 yr), `MBB` (~6 yr), and `HYG` (~3.5 yr) trade at 1 to 2 bps spreads with $0 commission; even 10 to 20 bps/month gross clears 2 to 4 bps round-trip costs cleanly.
- STATED trades per year: 12 per ETF (last 3 trading sessions of each month, long-only).
- MEASURED data: Already held in Alpaca SIP from 2016 (`LQD`, `HYG`, `MBB`, `TIP`).
- Verdict: KEEP.

### 3. Intraday Treasury auction-day concession and reversal (`TLT`, `IEF`, `TBF`)

- STATED sources: NY Fed Staff Report 1188, [Intraday Price Pressure and Order Flow Around U.S. Treasury Auctions](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr1188.pdf), and HBS Working Paper 26-033, [What Treasury Auctions Reveal About Investor Demand](https://www.hbs.edu/ris/Publication%20Files/26-033_9bebc98f-09f9-4485-aae6-972388865b19.pdf). Exact quotes: "Panel A indicates that, over the full 1991–2024 sample, temporary yield deviations in the six-hour window around auctions range from about 0.7 to 1.2 bps across maturities, all statistically significant at the 1% level." "After 2010, this trend has reversed and yields no longer fall after auctions."
- STATED sample and post-publication test: NY Fed SR 1188 covers June 1991 to July 2024 (intraday 6-hour window); HBS WP 26-033 covers 1992 to April 2025 (multi-day window). Together they show that multi-day post-auction drift faded after 2010, while the tightly timed 6-hour auction-day inverted-V persisted through 2024.
- STATED mechanical reason: Primary dealers face intraday risk-bearing limits as they absorb scheduled 1:00 PM ET 10-year and 30-year Treasury auctions, pushing yields up in the 3 hours before close and reversing in the 3 hours after results release.
- STATED effect size vs US retail costs: NY Fed SR 1188 reports 1.188 bps total intraday yield pressure on 10Y (+0.418 bps pre-auction, -0.770 bps post-auction) and 0.899 bps on 30Y (+0.629 bps pre-auction, -0.270 bps post-auction). At `IEF` duration (~7.5) and `TLT` duration (~16), that is roughly 6 to 10 bps of ETF price movement against ~1 to 2 bps ETF spreads ($0 commission), tight enough that only clean intraday execution (not multi-day holds) is viable.
- STATED trades per year: ~24 auctions per year (12 monthly 10Y + 12 monthly 30Y auctions; optionally 12 monthly 20Y auctions).
- MEASURED / STATED data: Alpaca SIP minute bars from 2016 are already held; auction dates and release times are free from the public TreasuryDirect Fiscal Data API.
- Verdict: KEEP WITH CHANGES (test only the intraday auction-day window around 1:00 PM ET, not the faded multi-day post-auction hold).

### 4. Kalshi favorite-longshot bias on settlement clocks (maker-side >=75c favorites)

- STATED source: Burgi, Deng, and Whelan (2025/2026), [The Economics of the Kalshi Prediction Market](https://www.ucd.ie/economics/t4media/WP2025_19.pdf). Exact quotes: "Investors who buy contracts costing less than 10c lose over 60 percent of their money." "On average, Makers who buy contracts costing 50c and over make a 2.6% rate of return before commission and a 1.9% rate of return including commission."
- STATED sample and post-publication test: Kalshi inception 2021 through April 2025 across 12,403 events and 46,282 Yes contracts (313,972 prices). Confirmed post-sample in Kalshi Research's 2026 micro-data study of 1 billion trades from October 2025 to September 2026.
- STATED mechanical reason: Retail takers overpay for low-priced lottery-ticket longshots (<10c) ahead of fixed binary settlement clocks; passive makers selling those longshots (equivalently buying >=90c Yes/No favorites) collect the overpricing as contracts converge to 100c at settlement.
- STATED effect size vs US retail costs: +1.9% average net return per trade after Kalshi fees for makers buying >=50c contracts, directly reachable on a $500 Kalshi account. Risk: severe left-tail skewness (a 90c favorite loses 90c on a 10% upset) and passive maker fill-rate risk.
- STATED trades per year: 100+ (daily/weekly macro, weather, and crypto range contracts).
- MEASURED / STATED data: Kalshi public unauthenticated REST API provides historical contract prices and settlements; however, fill-rate simulation for passive maker orders requires order-book or trade-side data, and Round 9 already flagged Kalshi maker strategies as calibration-only until fills are verified.
- Verdict: KEEP WITH CHANGES (restrict to scheduled macro/economic settlement clocks with strict position sizing and conservative maker fill assumptions).

### 5. Target-Date Fund and pension quarter-end equity-bond rebalancing (`SPY` vs `TLT`)

- STATED source: Parker, Schoar, and Sun (2023 Journal of Finance; NBER Working Paper 28028), [Retail Financial Innovation and Stock Market Dynamics](https://www.nber.org/system/files/working_papers/w28028/revisions/w28028.rev1.pdf). Exact quotes: "When the stock market returns 20% more than the bond market, a fund with a 50% desired equity share needs to convert 4.5% of its portfolio from stocks to bonds." "The actions are concentrated in the concurrent quarter and there is no spillover into the following quarter, suggesting that TDFs rebalance within the same quarter as the return shock."
- STATED sample and post-publication test: 2008Q3 to 2018Q4 in Parker, Schoar, and Sun (2023); tested out-of-sample on 2019 to 2022 in Parker and Sun (2025 Journal of Pension Economics and Finance), confirming contrarian TDF rebalancing during the pandemic.
- STATED mechanical reason: Trillions of dollars in Target-Date Funds and 60/40 pensions mechanically sell the outperforming asset class and buy the lagging asset class to restore target weights before quarter-end (passive TDFs rebalance roughly 80 to 90 cents on the dollar).
- STATED effect size vs US retail costs: Cross-sectional stock impact is 3.8 bps per 1% equity-bond spread per 0.7% TDF ownership; aggregate `SPY`/`TLT` index-level effect is smaller and noisier, but trading `SPY` or `TLT` costs only 1 to 2 bps round trip on a $500 account.
- STATED trades per year: 4 quarter-ends (or 6 to 12 month-ends when the MTD equity-bond return gap exceeds a threshold such as 3%).
- MEASURED data: Already held in Alpaca SIP from 2016 (`SPY`, `TLT`, `AGG`, `SH`, `TBF`).
- Verdict: KEEP WITH CHANGES (too few quarter-ends to stand alone; test as a conditioning filter on Replay 25 `TLT` month-end or conditional month-end `SPY`/`TLT` switch).

### 6. Closed-end fund (CEF) post-rights-offering snapback

- STATED source: Khorana, Wahal, and Zenner (2002 JFQA), [Agency Conflicts in Closed-End Funds: The Case of Rights Offerings](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/agency-conflicts-in-closedend-funds-the-case-of-rights-offerings/A9BD552704DEECFB4E2BC7E2627D42EC). Exact quote: "We study 120 rights offerings by closed-end funds from 1988–1998. On average, rights offerings are announced when funds trade at a premium. This premium turns into a discount over the course of the offering."
- STATED sample and post-publication test: 120 US CEF rights offerings from 1988 to 1998; post-2000 academic updates on post-expiration rebound are sparse (UNKNOWN whether the snapback magnitude persisted in 2016 to 2026).
- STATED mechanical reason: Dilutive CEF rights offerings priced below NAV force non-participating holders and arbitrageurs to sell shares into the subscription period, depressing the CEF to a steep discount by expiration day; once the subscription overhang clears after expiry, the discount partially normalizes.
- STATED effect size vs US retail costs: Discount swings of 5% to 15% occur across offerings, easily exceeding 10 to 30 bps CEF bid-ask spreads on a $500 long-only account (buying only after expiration avoids short-borrow constraints).
- STATED trades per year: Roughly 5 to 15 US CEF rights offerings per year.
- MEASURED / STATED data: Alpaca SIP holds CEF prices from 2016, but we do not yet hold a clean historical SEC Form N-2 / press-release rights-offering event table with exact expiration dates.
- Verdict: KEEP WITH CHANGES (long-only post-expiration entry only, contingent on building a clean 2016 to 2026 SEC N-2 rights-offering calendar first).

### 7. Leveraged ETF closing-auction-to-next-open reversal

- STATED source: Barbon, Beckmeyer, Buraschi, and Moerke, [Liquidity Provision to Leveraged ETFs and Equity Options Rebalancing Flows](https://abarbon.com/assets/Liquidity_Provision_to_Rebalancing_Flows_from_Leveraged_ETFs_and_Equity_Options.pdf). Exact quotes: "While leveraged ETF-induced price pressure evaporates at the next-day opening, that arising from delta-hedging is significantly longer-lived and requires almost a full trading day to be reversed." "The findings clearly indicate that the magnitude of the price effects stemming from leveraged ETFs is declining over time, being barely statistically significant in the last part of the sample."
- STATED sample and post-publication test: January 2012 to December 2019 across 72 leveraged ETFs and 24 indices. Distinct from Round 9's dropped 3:30 to 4:00 PM continuation claim, this tests the overnight MOC-to-10:00 AM reversal (-70.9 bps per 1% LETF rebalancing pressure). However, the authors explicitly document that the LETF effect decayed to barely significant by the end of 2019 as liquidity providers adapted to perfectly predictable flows.
- STATED mechanical reason: Daily-reset leveraged and inverse ETFs must rebalance in the same direction as the day's return at 4:00 PM ET, creating transitory closing pressure that reverses overnight.
- STATED effect size vs US retail costs: Faded to near-zero by 2019 in the primary paper; after overnight gap risk and inverse-ETF spread/decay on a $500 account, net edge is unlikely to survive.
- STATED trades per year: 20 to 40 large (>2% index move) days per year.
- MEASURED data: Already held in Alpaca SIP from 2016.
- Verdict: DROP.

### 8. S&P 500 and Nasdaq 100 quarterly reconstitutions

- STATED source: Greenwood and Sammon (2025 Journal of Finance), [The Disappearing Index Effect](https://www.hbs.edu/ris/Publication%20Files/ssrn-4294297_7112837f-ac0f-4b90-a4d0-802c3f79b462.pdf). Exact quotes: "The abnormal return associated with a stock being added to the S&P 500 has fallen from an average of 7.4% in the 1990s to less than 1% over the past decade." "Over the past decade, the well-known index effect for the S&P 500 has disappeared, with the average addition or deletion experiencing abnormal returns near zero."
- STATED sample and post-publication test: S&P 500 1980 to 2020 (153 additions, 87 deletions in the 2010s); Nasdaq 100 1995 to 2020 (declined from 3.9% in the 1990s to 2.0% in the 2010s, insignificant). Russell 2000 was already queued in Round 9.
- STATED mechanical reason: Passive index funds buy additions and sell deletions on the effective date, but over 70% of recent S&P 500 changes are migrations from S&P MidCap 400 and arbitrageurs pre-position weeks ahead.
- STATED effect size vs US retail costs: 2010s S&P 500 effective-date return is 0.26% (insignificant) and total return is 0.83% (insignificant); deletions average -0.62% (insignificant). Too small and noisy for a $500 account.
- STATED trades per year: ~15 to 25 S&P 500 changes per year.
- MEASURED / STATED data: Alpaca SIP held, but would require historical S&P announcement/effective-date tables.
- Verdict: DROP.

### 9. Commodity index Goldman Roll (`USO` and `SCO`, days 5 to 9)

- STATED source: Irwin, Sanders, and Yan (2022 AEPP), [The Order Flow Cost of Index Rolling in Commodity Futures Markets](https://scotthirwin.com/wp-content/uploads/2022/02/Irwin_Sanders_Yan_AEPP_All.pdf). Exact quotes: "The spread between nearby and deferred futures prices decreases significantly in the early and growth phases of financialization (1991-2011), with the spreads reversing back after rolling is completed. Spread impacts disappear in the post-financialization period (2012-2019)."
- STATED sample and post-publication test: 1980 to 2019 across 19 S&P GSCI commodity futures markets; confirms Mou (2011) worked in 1991 to 2011 but disappeared in 2012 to 2019.
- STATED mechanical reason: S&P GSCI and crude ETFs roll front-month futures to second-month between business days 5 and 9 of each month; electronic liquidity and early/late rolling absorbed the pressure after 2011.
- STATED effect size vs US retail costs: Even when active, the effect lived in calendar spreads (front minus second month), not outright WTI price levels; a $500 US retail account limited to outright `USO`/`SCO` ETFs (with 5 to 10 bps spreads and ETF roll drag) cannot isolate the spread.
- STATED trades per year: 12 monthly roll windows.
- MEASURED data: Alpaca SIP holds `USO`/`SCO` from 2016, but futures calendar-spread data is not held and not tradable on $500.
- Verdict: DROP.

### 10. Option expiration (OpEx) market-maker hedge rebalancing (`SPY` and `QQQ`)

- STATED sources: Ni, Pearson, Poteshman, and White (2021 Review of Financial Studies), [Does Option Trading Have a Pervasive Impact on Underlying Stock Prices?](https://academic.oup.com/rfs/article-abstract/34/4/1952/5873587), and Barbon et al., [Liquidity Provision to Leveraged ETFs and Equity Options Rebalancing Flows](https://abarbon.com/assets/Liquidity_Provision_to_Rebalancing_Flows_from_Leveraged_ETFs_and_Equity_Options.pdf). Exact quotes: "This paper provides evidence of a noninformational channel through which option market maker hedge rebalancing affects stock return volatility and the probability of large stock price moves." "On the contrary, the importance of gamma-induced price effects is persistent throughout the sample and, if anything, has been increasing over time."
- STATED sample and post-publication test: Ni et al. (2021) and Barbon et al. (2012 to 2019) confirm that option dealer gamma hedging is persistent, unlike leveraged ETF flows.
- STATED mechanical reason: Option market makers delta-hedge net gamma exposure into the close, dampening or amplifying intraday moves depending on whether dealers are net long or short gamma.
- STATED effect size vs US retail costs: Barbon et al. report +28.1 bps next-day reversal per 1% gamma hedging pressure, but exploiting it requires knowing the sign and magnitude of dealer net gamma by ticker every day (not a static monthly OpEx calendar clock, which Round 9 already dropped).
- STATED trades per year: 12 monthly OpEx dates (or daily with live gamma positioning).
- STATED data: We do not hold historical option open-interest and signed dealer-gamma datasets (CBOE/OptionMetrics are paid institutional feeds).
- Verdict: DROP.

### 11. Closed-end fund (CEF) activist and periodic tender offers

- STATED source: Investment Company Institute review of Bradley, Brav, Goldstein, and Jiang (2010 JFE), [Academic Literature in Support of CEF Activism](https://www.ici.org/25-view-academic-literature-support-cef-activism). Exact quotes: "When an activist targets a fund, the fund’s discount tends to close." "After the tender offer, however, the discount returns within a year or so to about the level seen before the activist attacked the fund."
- STATED sample and post-publication test: Bradley et al. (2010) plus ICI's October 2024 SEC comment-letter update confirm that activist tenders narrow CEF discounts temporarily before discounts re-widen post-tender.
- STATED mechanical reason: Activists (e.g., Saba Capital) pressure CEFs to conduct partial tender offers (typically 5% to 50% of shares at 98% to 99% of NAV) on published SEC Schedule TO dates.
- STATED effect size vs US retail costs: Unlike corporate issuer odd-lot tender offers (Round 8), CEF tender offers almost never include an odd-lot priority clause. A $500 retail account gets pro-rated (often only 10% to 25% of shares accepted at 98% NAV) and is left holding 75% to 90% of shares as the discount widens back after expiration, plus 15 to 40 bps CEF spreads and potential broker corporate-action fees.
- STATED trades per year: ~10 to 20 CEF tender offers per year.
- MEASURED / STATED data: Alpaca SIP holds CEF prices; SEC Schedule TO dates and pro-ration factors would require manual collection.
- Verdict: DROP.

### 12. Scheduled token cliff unlocks on the 36 US-shortable coins

- STATED source: Keyrock (Dec 5, 2024), [From Locked to Liquidity: What 16,000+ Token Unlocks Teach Us](https://keyrock.com/from-locked-to-liquidity-what-16000-token-unlocks-teach-us/). Exact quotes: "Our analysis of 16,000+ unlock events across 40 tokens underscores key trends:" "90% of unlocks create negative price pressure, regardless of size or type." "Token price impacts often start 30 days before the unlock event." "Team unlocks trigger the worst crashes (-25%) with unsophisticated sell-offs."
- STATED sample and post-publication test: 16,000+ composite unlock events across 40 tokens through late 2024; Keyrock does not publish formal t-statistics or out-of-sample 2025 to 2026 splits.
- STATED mechanical reason: Vesting cliffs release locked insider/team tokens into circulating supply on known smart-contract dates, triggering pre-hedging and retail anticipation starting ~30 days prior.
- STATED effect size vs US retail costs: Although team cliff drawdowns are large (-25% in Keyrock's sample), two blockers break this for a $500 US retail account today: (1) holding a short for 30 days ahead of an unlock on Kraken US spot margin incurs 40/80 bps trading fees plus ~180 four-hour rollover debits (easily 4% to 8%+ carry drag), while Kalshi/Coinbase CDE only launched in mid-2026; (2) of our 36 US-shortable coins from Plan 28, nearly all are mature or fully unlocked large caps, leaving only a handful (`SUI`, `ENA`, `WLD`, `ONDO`, `SEI`, `HYPE`, `PENGU`) with active schedules, mostly linear or <2% mcap rather than >5% team cliffs.
- MEASURED / STATED trades per year: Fewer than 5 clean >5% team-cliff events per year across the 36 US-shortable coins.
- MEASURED / STATED data: Coinbase CDE and Kalshi public candles only start mid-2026 (2025-07 for BTC/ETH); historical unlock calendars require a paid token-unlock API (Tokenomist/CryptoRank).
- Verdict: DROP (revisit only if US CFTC venues expand to 100+ newer small-cap coins).

### 13. US exchange listing notices (Coinbase, Robinhood, Kraken) for coins already shortable in the US

- STATED sources: Ante (2019, BRL Working Paper 3), [Market Reaction to Exchange Listings of Cryptocurrencies](https://www.blockchainresearchlab.org/wp-content/uploads/2019/10/Exploring-Market-Reactions-to-Exchange-Listings-of-Cryptocurrencies-BRL-working-paper3.pdf), and The Tie (July 13, 2026, opened in Plan 28), [What Does an Exchange Listing Actually Deliver in 2026?](https://www.thetie.io/insights/what-does-an-exchange-listing-actually-deliver-in-2026). Exact quotes: "The results show a significant average abnormal return of 5.7% on the day of the listing event and 9.2% in the window of three days before until three days after the listing." "The volume premium from a major exchange listing has compressed meaningfully since 2023."
- STATED sample and post-publication test: Ante (2019) covers 327 listings across 22 exchanges from April 2017 to June 2019, where Coinbase's 7 listings had an insignificant -0.6% `[-3,+3]` abnormal return and +0.4% day-0 return. The Tie (July 2026) covers 1,844 listing events from January 2023 to June 2026 and documents sharp post-2023 compression.
- STATED mechanical reason: Unlike Upbit KRW listings (which unlock isolated Korean retail fiat demand for small altcoins already on Binance perps), a coin that already has a CFTC-regulated US short contract on our 36-coin roster is almost always already listed for spot trading on Coinbase, Kraken, and Robinhood.
- STATED effect size vs US retail costs: Near-zero eligible events, and Coinbase/Kraken listing pops are far smaller and more anticipated than Upbit KRW pumps.
- MEASURED / STATED trades per year: ~0 to 2 events per year across the 36 US-shortable coins.
- MEASURED / STATED data: Coinbase/Kalshi candles exist from mid-2026, and historical US exchange listing notices would require manual collection for a near-empty sample.
- Verdict: DROP.
