# Round 13: Known-Clock Long-Only Premia for a $500 US Account (December and January Focus)

Date: 2026-11-25
Author: idea_scout
Scope: Known-clock calendar and recurring-flow premia that a $500 US retail account can hold long with one or two tickers, weighted toward what is timely for December and January and checked against post-publication out-of-sample evidence. No returns were computed in this note. All figures are verbatim from cited primary sources. Claims are labeled MEASURED (empirical result in the source), STATED (structural rule, cost, or qualitative statement in the source), or UNKNOWN (not published in the retrieved sources).

Nothing is repeated from Rounds 1 to 12 without new evidence. Replay 19 already covered the Monday Asia crypto window, and Replay 25 (with Plan 31 and Measurement 34) already covered the Treasury month-end window. Replay 07 already tested eight intraday rules on SPY and QQQ one-minute bars. Candidate 2 (market-wide dividend payment-day pressure) was already taken in Round 10 and is already row 51, blocked on payment-date data, so it does not receive a new queue row here.

## Summary Table

| # | Candidate | Primary Paper (Sample End) | Post-Publication / After-Sample Result | Size After Retail Costs | Trades/Yr | Data We Hold | Dec/Jan Timely? | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Earnings announcement premium | Frazzini & Lamont 2007 (2004) | Vanished after 2004 (EW 0.3 bps/wk, VW 8.7 bps/wk, insignificant) | Zero/negative after spreads | ~4/stock | Alpaca SIP 2016+ | No | DROP (faded) |
| 2 | Dividend payment-day market pressure (SPY) and dividend month premium | Hartzmark & Solomon 2013 (2011); 2025 AER | Top quintile dividend payout days earn 4x lowest quintile in SPY; German post-2013 replication positive | High net room on SPY (~1 bp spread) | ~20 to 50 days/yr | Alpaca SIP SPY 2016+ (missing historical pay dates) | YES (Dec is peak payout month) | ALREADY ROW 51 (blocked on payment-date data) |
| 3 | Late-December tax-loss selling rebound in beaten-down small stocks | Grinblatt & Keloharju 2004; Lehigh ToY (2005) | Index-level Jan effect gone, but conditional extreme-loser rebound untested post-2005 on Alpaca | +14.0% Jan-Dec gap in extreme losers (wide small-cap spreads) | 1/yr (10 to 15 trading days) | Alpaca SIP 2016+ (10 Dec-Jan turns) | YES (first live window late Dec 2026) | QUEUE ROW 66 (Plan 40, feasibility first) |
| 4 | Turn of the month in US stocks (SPY/IWM) | McConnell & Xu 2008 (2005) | Faded post-2008 (2009 to 2026: 24% of SPY return on 19% of days, p=0.33; 2006 to 2019 t=-0.07) | Negative vs SPY (-9.6%/yr at 5 bps/side) | 12/yr | Alpaca SIP 2016+ | Minor (Dec/Jan turn) | DROP (faded) |
| 5 | Overnight vs intraday return gap (SPY/QQQ) | Lou, Polk & Skouras 2019 (2013); Boyarchenko et al. 2022 (2020) | ES futures 1998 to 2020: OTC (+5.12%) beat CTO (+3.53%); London-open drift insignificant after spread | ~252 round-trips/yr eats 5 to 10%/yr at 1 to 2 bps/side | 252/yr | Alpaca SIP minute/daily 2016+ | Year-round | WATCH (Queue Row 67) |
| 6 | Last-half-hour intraday momentum (SPY/QQQ) | Gao, Han, Li & Zhou 2018 (2013) | Rosa 2022 JFM: predictability disappears out-of-sample; Replay 07 failed on SPY/QQQ | Negative after spreads/slippage | 252/yr | Alpaca SIP minute 2016+ | Year-round | DROP (faded + Replay 07) |
| 7 | Pre-holiday sessions in small caps (IWM) | Ariel 1990 (1982); Ko & Yang 2021 (2019) | Large-cap SPY vanished post-1990, but small-cap EW survived 1983 to 2019 at +0.37%/day | Strong net room on IWM (~1 to 2 bps spread) | 8 to 9/yr | Alpaca SIP IWM 2016+ | YES (Thanksgiving, Christmas, New Year, MLK) | QUEUE ROW 65 (Plan 39) |
| 8 | Pre-FOMC announcement drift (SPY) | Lucca & Moench 2015 (2011) | Kurov et al. 2021 & 2024 0DTE study: essentially disappeared after 2015 | Near zero / insignificant | 8/yr | Alpaca SIP minute 2016+ | Dec FOMC | DROP (faded) |
| 9 | FOMC cycle even weeks (SPY) | Cieslak, Morse & Vissing-Jorgensen 2019 (2016) | Fed FEDS 2026-023 & HHS 2023: reversed sign in 2017 to 2022 (even weeks lower than odd) | Negative post-2016 | ~26 wks/yr | Alpaca SIP 2016+ | Year-round | DROP (reversed) |
| 10 | Quarter-end / year-end window dressing | Agarwal, Gay & Ling 2014 (2008); Parise & Rubin 2025 | Fund-level effect is negative (-40 to -60 bps); stock-level ESG CAR is only +0.20% over 3 days | Tiny (+0.8%/yr gross across 4 quarter-ends) | 4/yr | Alpaca SIP 2016+ | Dec 31 | DROP (too small) |
| 11 | Unconditional January small-stock effect (IWM) | Keim 1983; PapersWithBacktest (2025) | Dead for 38 years: Russell 2000 minus S&P 500 in Jan is -0.05% (1988 to 2025) and -0.43% (2010 to 2025) | Negative | 1/yr | Alpaca SIP IWM/SPY 2016+ | Jan | DROP (faded) |
| 12 | Option expiry (OpEx) week (SPY / S&P 100) | Stivers & Sun 2013 (2008) | SPY OpEx week ~+0.20%/wk since 1993, but weakened in recent 3 years; Jan OpEx negative | Modest (~2% CAGR at 18% exposure; 1 bp SPY spread) | 12/yr | Alpaca SIP SPY 2016+ | Weak in Jan | WATCH (Queue Row 68) |
| 13 | Crypto weekend and US time-of-day patterns | Kaiko 2024 to 2026; Janorium (Sep 2026) | Weekends have lower volatility (0.56x), no reliable return edge; daily switching crushed by fees (-99.87%) | Negative after 10 to 15 bps retail crypto fees | 52 to 365/yr | Binance archives + Coinbase hourly | Year-round | DROP (no net edge) |
| 14 | Bitcoin ETF creation flow days (IBIT / spot) | WhyCoinMoves, DWF Labs, Concordia (Oct 2026) | Flows track same-day (0.44) and prior 5d (0.54); next-24h corr is 0.01, Granger p=0.289 to 0.943 | Zero / negative after fees | ~252/yr | Alpaca IBIT + Coinbase/Binance | Year-round | DROP (no forward signal) |

## Queue Routing From Round 13

- Queue row 65 (Plan 39, ledger 174, author `repo_archivist`): Pre-holiday sessions in IWM (Candidate 7). Ko & Yang (2021, Critical Finance Review) showed the large-cap SPY pre-holiday effect vanished after 1990 while the small-cap equal-weighted pre-holiday premium survived 1983 to 2019 at +0.37%/day. One ticker (IWM, ~1 to 2 bps spread), 8 to 9 trades/year, directly testable on held Alpaca SIP IWM bars from 2016 to 2026, and timely for Thanksgiving Eve, Christmas Eve, New Year's Eve, and MLK Day Eve.
- Queue row 66 (Plan 40, ledger 175, author `trader_methods_researcher`, feasibility first): Late-December tax-loss selling rebound in beaten-down small stocks (Candidate 3). Conditional extreme 11-month losers earned +14.0% January-minus-December abnormal return (+26.4% for small underperformers after down years in 1999 to 2005). Directly testable across 10 December-to-January turns on held Alpaca SIP 2016 to 2026 bars; first live window is late December 2026.
- Queue row 67 (Waiting): Overnight vs intraday return gap in SPY/QQQ (Candidate 5). Needs a low-frequency conditional filter rather than blind daily close-to-open switching (252 round-trips/year).
- Queue row 68 (Waiting): Option expiry week in SPY / S&P 100 (Candidate 12). Needs a post-2016 check on whether the effect survived weekly and 0DTE options growth.
- Candidate 2 (market-wide dividend payment-day pressure on SPY): already row 51, blocked on payment-date data.

---

## Detailed Candidate Reviews

### 1. Earnings Announcement Premium

Paper and sample end:
- MEASURED: Frazzini & Lamont (2007, NBER WP 13090, [Library of Congress PDF](https://tile.loc.gov/storage-services/master/gdc/gdcebookspublic/20/07/61/62/48/2007616248/2007616248.pdf)): "Panel A: Full sample 1973-2004, different methods, 4 prior announcements required previous year." "The premium is large and highly statistically significant across the entire sample period, delivering between 40 and 92 basis points a month."

What happened after publication:
- MEASURED: The Disappearing Earnings Announcement Premium (IIMB ARC 2020, [IIMB PDF](https://www.iimb.ac.in/ARC2020/Papers/The_Disappearing_Earnings_Announcement_Premium.pdf)): "We conduct the analysis for the period 1994 to 2016, resulting in a sample of over 1,100 weeks for both the announcers and non-announcers portfolios."
- MEASURED: Same source ([IIMB PDF](https://www.iimb.ac.in/ARC2020/Papers/The_Disappearing_Earnings_Announcement_Premium.pdf)): "In contrast, our post-regulation sample, which is presented in panel C shows no evidence of the earnings announcement premium. The equal-weight (value-weight) excess returns are 17.8 bps (14.7 bps) for non-announcers and 18.1 bps (23.4 bps) for announcers, which translates into a premium of 0.3 bps (8.7 bps) for announcers relative to non-announcers. These earnings announcement premium estimates are not statistically different from zero and are mirrored in Columns 2 and 3. The post-regulation results from Panel C present strong evidence that the earnings announcement premium has completely vanished after 2004."

Size after retail costs, trades/year, data held, verdict:
- MEASURED: Post-2004 weekly premium of 0.3 bps EW / 8.7 bps VW is zero or negative after retail spreads. Held data: Alpaca SIP 2016 onward. Verdict: DROP (vanished after 2004).

---

### 2. Dividend Payment-Day Market Pressure (SPY) and Dividend Month Premium

Status: Already row 51, blocked on payment-date data.

Paper and sample end:
- MEASURED: Hartzmark & Solomon (2013, Journal of Financial Economics, summarized in [Federal Reserve FEDS 2021-037](https://www.federalreserve.gov/econres/feds/files/2021-037pap.pdf) and [Alpha Architect](https://alphaarchitect.com/2011/10/dividends-can-pay-without-paying/)): sample 1927 to 2011; "Abnormal returns in predicted dividend months are high both relative to all other companies (by 53 basis points per month), and relative to dividend-paying companies in months without a predicted dividend (by 37 basis points per month)." In FEDS 2021-037: "They include everything from dividend seasonality, which was shown to produce a long-short t-stat of 16.2 (Hartzmark and Solomon 2013)."
- MEASURED: Hartzmark & Solomon (2025, American Economic Review 115(9), [AEA](https://www.aeaweb.org/articles?id=10.1257/aer.20231725)): "Buying pressure from dividend payments (announced weeks prior) predicts higher value-weighted market returns, with returns for the top quintile of payment days four times higher than the lowest. This holds internationally and increases when reinvestment is high and market liquidity is low. We estimate a market-level price multiplier of 1.9."

What happened after publication:
- MEASURED: Post-2013 international out-of-sample test in Germany ([Springer 2021](https://link.springer.com/article/10.1057/s41260-021-00215-3)): "Our results are robust across various strategy specifications, and the exploitation of the dividend month premium is still profitable in the period after the publication of Hartzmark and Solomon (2013)."

Size after retail costs, trades/year, data held, verdict:
- STATED: Already queued as row 51 (Plan 32), blocked on historical dividend payment-date data (Alpaca omitted payable dates on 2016 to 2019 cash actions). No new queue row added.

---

### 3. Late-December Tax-Loss Selling Rebound in Beaten-Down Small Stocks

Paper and sample end:
- MEASURED: Grinblatt & Keloharju (2004, NBER w8745, [NBER](https://www.nber.org/system/files/working_papers/w8745/w8745.pdf), sample 1996 to 2000): "An analysis of trades in the Finnish stock market around the turn of the year shows that Finnish investors tend to realize losses more than gains towards the end of December." "The resulting net buying pressure from these 'wash sale' repurchases is greater for stocks with small market capitalizations and has a calendar pattern that is similar to that of stock returns."
- MEASURED: Institutional & Turn-of-the-Year Study (Journal of Banking & Finance, [Lehigh University PDF](https://www.lehigh.edu/~xuy219/research/ToY.pdf)): "We utilize trading data for the period from January 1, 1999 to December 31, 2005." "We begin our study by investigating year-end return patterns during our 1999 to 2005 sample period, and consistent with prior literature, we find that abnormal stock returns are 3.9% (t = 22.31) higher during the first 10 trading days in January when compared to the last 10 trading days in December. The effect is stronger in smaller stocks (6.8%), and stocks with poorer past performance over the prior eleven months (14.0%)." "January minus December returns following DOWN years are 7.4% for the overall sample and that effect is significantly magnified (26.4%) for small underperforming stocks."

What happened after publication:
- MEASURED: The unconditional index-level January small-cap effect disappeared (see Candidate 11), while modern post-2005 US evidence specifically on the conditional extreme-loser small-cap rebound is UNKNOWN in our retrieved peer-reviewed sources and directly testable on Alpaca 2016 to 2026.

Size after retail costs, trades/year, data held, verdict:
- STATED: A 1-trade-per-year hold (late December into early January) in 1 or 2 spread-filtered beaten-down small stocks has substantial gross headroom (+6.8% to +14.0% in 1999 to 2005) above a 20 to 60 bps round-trip spread, though single-stock idiosyncratic risk is high on a $500 account.
- STATED: Held data covers 10 December-to-January turns on Alpaca SIP (2016 to 2026). First live window is late December 2026. Verdict: QUEUE ROW 66 (Plan 40, feasibility first).

---

### 4. Turn-of-the-Month Effect in US Stocks (SPY / IWM)

Paper and sample end:
- MEASURED: McConnell & Xu (2008, Financial Analysts Journal, [Purdue PDF](https://business.purdue.edu/faculty/mcconnell/publications/Equity-Returns-at-the-Turn-of-the-Month.pdf), sample 1926 to 2005): "The turn-of-the-month effect in U.S. equities is found to be so powerful in the 1926-2005 period that, on average, investors received no reward for bearing market risk except at turns of the month."

What happened after publication:
- MEASURED: Gupta (November 2026, [GitHub turn-of-month](https://github.com/guptagaurav-info/turn-of-month) and [PDF](https://guptagaurav.info/articles/turn-of-month/gaurav-gupta-turn-of-month-research-note.pdf), sample Jan 1996 to Oct 2026): "It has faded. 2009-2026: those days earned 24% of SPY's return, 21% of DIA's, 20% of MDY's and 12% of IWM's, close to their 19% share of days. A turn-of-month day averaged 7.3 bp against 5.8 bp for other days; random windows beat it 33% of the time."
- MEASURED: Independent replication on SPY ([GitHub bhoult/correlation](https://github.com/bhoult/correlation/blob/main/experiments/-9.6-turn-of-month.md), 2006 to June 2025): "Our code reproduces their 1926-2005 result exactly (t 8.2), but the effect has vanished since: over 2006-2019 those days earned no more than the rest (t -0.07)." After 5 bps/side, the TOM-only rule trailed SPY by -9.6 percentage points/year.

Size after retail costs, trades/year, data held, verdict:
- MEASURED: No edge post-2008 across SPY, DIA, MDY, and IWM (12 trades/year). Held data: Alpaca SIP 2016+. Verdict: DROP (faded after publication).

---

### 5. Overnight vs Intraday Return Gap in Index Funds (SPY / QQQ)

Paper and sample end:
- MEASURED: Lou, Polk & Skouras (2019, Journal of Financial Economics, [LSE PDF](https://personal.lse.ac.uk/POLK/research/TugOfWar.pdf), sample 1993 to 2013): "We then show that essentially all of the abnormal returns on momentum and short-term reversal strategies occur overnight while the abnormal returns on other strategies occur intraday and that this pattern is not driven by news."
- MEASURED: Collegio Carlo Alberto (2023, [PDF](https://www.carloalberto.org/wp-content/uploads/2023/01/Day-Destroys-The-Night-Night-Extends-The-Day.pdf), SPY 1993Q3 to 2019Q4): "First, the average quarterly overnight return is 1.8% while the average quarterly intraday return is 0."

What happened after publication and cost check:
- MEASURED: Boyarchenko, Larsen & Whelan (2022, NY Fed Staff Report 917, [NY Fed PDF](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf), E-mini S&P 500 futures Jan 1998 to Dec 2020): "Decomposing into intraday versus overnight components open-to-close (OTC) log returns averaged 5.12% while close-to-open (CTO) log returns averaged 3.53%." And as noted in [Northern Finance Association](https://portal.northernfinanceassociation.org/viewp.php?n=2240010836): "In concurrent work, Boyarchenko, Larsen, and Whelan (2020) study whether inventory risk can explain market return around London open and find that the returns are not significant after accounting for the bid-ask spread."

Size after retail costs, trades/year, data held, verdict:
- STATED: Blindly buying SPY at 4:00 p.m. and selling at 9:30 a.m. requires ~252 round-trips/year (504 executions/year); even 1 to 2 bps/side on SPY open/close auctions consumes 5 to 10% per year before intraday bull-market opportunity cost. Held data: Alpaca SIP minute/daily 2016+. Verdict: WATCH (Queue Row 67; only viable with a low-frequency conditional filter).

---

### 6. Last-Half-Hour Intraday Momentum (SPY / QQQ)

Paper and sample end:
- MEASURED: Gao, Han, Li & Zhou (2018, Journal of Financial Economics, [RePEc](https://ideas.repec.org/a/eee/jfinec/v129y2018i2p394-414.html)): "Based on high frequency S & P 500 exchange-traded fund (ETF) data from 1993-2013, we show an intraday momentum pattern: the first half-hour return on the market as measured from the previous day's market close predicts the last half-hour return."

What happened after publication:
- MEASURED: Rosa (2022, Journal of Futures Markets, [Wiley](https://onlinelibrary.wiley.com/doi/10.1002/fut.22375)): "This paper studies the out-of-sample performance of the intraday momentum strategy where the overnight return predicts the return of the last half-hour of trading. The predictability disappears in the out-of-sample period."
- MEASURED: Replay 07 (`docs/research/27_replay_07_intraday_spy_qqq.md`) already tested eight intraday rules on SPY and QQQ one-minute bars with zero passing at 5 bps/side.

Size after retail costs, trades/year, data held, verdict:
- MEASURED: Negative after spreads on 252 trades/year. Held data: Alpaca SIP minute 2016+. Verdict: DROP (disappeared out-of-sample).

---

### 7. Pre-Holiday Sessions in US Stocks (IWM vs SPY)

Paper and sample end:
- MEASURED: Ariel (1990, Journal of Finance, [JSTOR](https://www.jstor.org/stable/2328753)): "Over one third of the total return accruing to the market portfolio over the 1963-1982 period was earned on the eight trading days which each year fall before holiday market closings."

What happened after publication:
- MEASURED: Ko & Yang (2021, Critical Finance Review, [CFR PDF](https://cfr.ivo-welch.info/published/papers/ko2021pre.pdf)): "We extend Ariel's (1990) sample to December 2019." "The average pre-holiday returns of CRSP EW and VW indices decline to 0.37% and 0.14%, respectively." "For large firms, the differences in returns between pre-holidays and non-pre-holidays have become insignificant, and especially after 1990." "(Neither do Dow Jones Industrial Average (DJIA) and the Standard & Poor's (S&P) 500.)"
- MEASURED: Ko & Yang (2021, [CFR PDF](https://cfr.ivo-welch.info/published/papers/ko2021pre.pdf)): "The persistence of the pre-holiday effect among small firms is also consistent with the argument of limits of arbitrage. The CRSP EW index continued to outperform its benchmarks and the CRSP VW index on pre-holidays during the extended period. Thus the pre-holiday premium has largely become a small-firm effect."
- MEASURED: FinzData (November 2026, [FinzData PDF](https://finzdata.com/research/stock-market-thanksgiving-black-friday-2026.pdf), 2000 to 2025): On Thanksgiving Eve, Russell 2000 rose 18 of 26 years with a +0.46% average gain vs +0.22% for the S&P 500.

Size after retail costs, trades/year, data held, verdict:
- STATED: Holding IWM (~1 to 2 bps spread) on the 8 to 9 US pre-holiday sessions per year retains most of the +37 bps/day small-firm historical pre-holiday return (~3% annualized from ~3.5% time in market).
- STATED: Held data: Alpaca SIP IWM daily/minute bars from 2016 to 2026. Immediately timely for Thanksgiving Eve, Christmas Eve, New Year's Eve, and MLK Day Eve. Verdict: QUEUE ROW 65 (Plan 39).

---

### 8. Pre-FOMC Announcement Drift (SPY)

Paper and sample end:
- MEASURED: Lucca & Moench (2015, Journal of Finance, quoted in [PMC Kurov et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/pdf/main.pdf)): "From September 1994 to March 2011, the returns on average increase by 49 basis points during 24 h before the FOMC announcements, accounting for approximately 80% of annual returns."

What happened after publication:
- MEASURED: Kurov, Wolfe & Gilbert (2021, Finance Research Letters, [PMC PDF](https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/pdf/main.pdf)): "The post-LM period from April 2011 to December 2019 contains 70 scheduled meetings: 40 and 30 meetings with and without press conferences, respectively." "We find that after first appearing before FOMC announcements accompanied by the Fed Chair press conferences, the pre-FOMC drift essentially disappeared after 2015 in both announcements accompanied by press conferences and announcements not accompanied by press conferences."
- MEASURED: 0DTE Options Study ([AFA 2025/2026](https://afajof.org/management/viewp.php?n=260400), sample 2011/04 to 2023/12): "Immediately after the introduction of Wednesday-expiring 0DTE options, the pre-announcement drift documented in the literature disappears, indicating that the drift reflected compensation for previously unobservable event uncertainty."

Size after retail costs, trades/year, data held, verdict:
- MEASURED: Statistically indistinguishable from zero post-2015 across 8 FOMC meetings/year. Held data: Alpaca SIP minute 2016+. Verdict: DROP (disappeared after 2015).

---

### 9. FOMC Cycle Even Weeks (SPY)

Paper and sample end:
- MEASURED: Cieslak, Morse & Vissing-Jorgensen (2019, Journal of Finance, summarized in [Federal Reserve FEDS 2026-023](https://www.federalreserve.gov/econres/feds/files/2026023pap.pdf)): "From 1994 to 2016 they find that the realized excess return on stocks over T-bills is, on average, earned entirely in weeks 0, 2, 4, and 6 (the even weeks)." "Excess returns on even-week days are on average 12 bps higher than excess returns on odd-week days (weeks -1, 1, 3, and 5)."

What happened after publication:
- MEASURED: Federal Reserve FEDS 2026-023 ([Federal Reserve PDF](https://www.federalreserve.gov/econres/feds/files/2026023pap.pdf)): "Third, in the subsequent 5-year period from 2017 to 2021, there is a statistically significant opposite cycle in stock returns, with average returns lower in even weeks (Figure 5b; Table 5, columns 5-8)."
- MEASURED: Stockholm School of Economics replication ([HHS PDF](http://arc.hhs.se/download.aspx?MediumId=5734), 2017 to 2022): "Our results reveal that the pattern of significantly higher excess returns in even weeks of the FOMC cycle is no longer present in the 2017 to 2022 period. In this post-sample period, daily US stock returns are on average lower in even weeks than odd weeks in the FOMC cycle."

Size after retail costs, trades/year, data held, verdict:
- MEASURED: Reversed sign post-2016 (~26 weeks/year). Held data: Alpaca SIP 2016+. Verdict: DROP (reversed post-sample).

---

### 10. Quarter-End and Year-End Window Dressing

Paper and sample end:
- MEASURED: Agarwal, Gay & Ling (2014, Review of Financial Studies, [EconStor PDF](https://www.econstor.eu/bitstream/10419/97693/1/788388193.pdf), sample Sept 1998 to Dec 2008): "For the highest WD decile, next quarter's average alphas are -0.66% and -0.74% for BHRG and Rank Gap, respectively." (Fund-level underperformance, not a long-only 1-ticker equity buy signal.)
- MEASURED: Parise & Rubin (2025, Journal of Finance, [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jofi.13499)): "Our results indicate that ESG stocks generate positive cumulative abnormal returns of 0.20% in the three days before fund portfolio disclosure, but these returns revert shortly after disclosure."

What happened after publication, size after costs, trades/year, data held, verdict:
- MEASURED: Even the recent 2025 stock-level ESG window-dressing effect is only +0.20% over 3 days across 4 quarter-ends per year (+0.80%/year gross before spreads), which is too small to justify a standalone $500 strategy. Held data: Alpaca SIP 2016+. Verdict: DROP (too small).

---

### 11. Unconditional January Small-Stock Effect (IWM)

Paper and sample end:
- MEASURED: Classic anomaly (Keim 1983) documented small-cap outperformance in January.
- MEASURED: Long-run and modern check through 2025 ([PapersWithBacktest](https://paperswithbacktest.com/strategies/january-effect)): "Since 2001 it [S&P 500 January] has returned 0.13%, below the average month, and the 2000s were negative at -1.8%." "In the 38 Januaries since 1988, small caps have trailed large caps by 0.05% on average and beaten them in only 39% of them. Split the sample and it does not help: -0.09% in 1988-2000, -0.03% in 2001-2025, -0.43% in 2010-2025."

Size after retail costs, trades/year, data held, verdict:
- MEASURED: Negative small-minus-large spread across all subperiods since 1988 (1 trade/year). Held data: Alpaca SIP IWM/SPY 2016+. Verdict: DROP (dead at the index level).

---

### 12. Option Expiry (OpEx) Week (SPY / S&P 100)

Paper and sample end:
- MEASURED: Stivers & Sun (2013, Journal of Banking & Finance, [RePEc](https://ideas.repec.org/a/eee/jbfina/v37y2013i11p4226-4240.html) and [Quantpedia](https://quantpedia.com/strategies/option-expiration-week-effect)): sample 1996 to 2008; "For S&P 100 stocks, we find that the weekly returns over option-expiration (OE) weeks (a month's third-Friday week) tend to be high." High option-to-stock activity spread averaged 67.9 bps (1996 to 2002) and 70.7 bps (2002 to 2008).

What happened after publication:
- MEASURED: SPY OpEx-week backtest since inception ([QuantifiedStrategies](https://www.quantifiedstrategies.com/options-expiration-week/)): "The CAGR is 2%, and the average gain is 0.2% per week, higher than any other random week. Keep in mind that you are invested only around 18% of the time, and the average number of bars in a trade is slightly less than 5. As you can see, the effect has been weak over the last three years." Also notes: "Only July and January show negative returns during the options expiration week."

Size after retail costs, trades/year, data held, verdict:
- MEASURED: +0.20%/week gross across 12 OpEx weeks/year (~1 bp SPY spread), but weakened in the recent 0DTE/weekly-options era and historically negative in January. Held data: Alpaca SIP SPY 2016+. Verdict: WATCH (Queue Row 68; weakened recently and poor in January).

---

### 13. Crypto Weekend and Time-of-Day Patterns on US Venues (Excluding Replay 19 Monday Asia)

Paper and sample end:
- MEASURED: Janorium (November 2026, [Janorium](https://janorium.com/articles/bitcoin-weekend-time-of-day-returns), Binance BTCUSDT and ETHUSDT hourly candles Jan 2020 to Sep 2026, 59,129 hours): "Weekends are calmer, not richer: an average BTC weekend day moved 1.40% against 2.38% on a weekday, with no reliable difference in return. The hours right after the US close did carry an outsized share of the gains - but holding BTC only during the US session, paying 0.1% fees and 0.05% slippage, ended at -99.87%."
- MEASURED: OptiNod Academy (November 2026, [OptiNod](https://optinod.com/en/learn/bitcoin-weekend-volatility/)) and Kaiko ([Kaiko](https://www.kaiko.com/resources/btc-etfs-impact-on-spot-market-structure)): "In the spot ETF era, weekends moved 0.560 times as much as weekdays." "Currently, the BTC weekend trading volume stands at an all-time low of 16% in 2024, marking a 12 percentage point decrease from its peak of 28% in 2019." DailyCoin ([DailyCoin](https://dailycoin.com/bitcoins-weekend-gap-etfs-shift-liquidity-to-u-s-hours/)): "The average BTC-USDT bid-ask spread more than doubles on weekends, widening from 0.012% on weekdays to 0.028%."

Size after retail costs, trades/year, data held, verdict:
- MEASURED: No reliable weekend return edge (sign flips year by year), wider weekend spreads, and daily time-of-day switching is destroyed by US retail crypto fees (10 to 25 bps/side). Held data: Binance archives + Coinbase hourly. Verdict: DROP (volatility pattern only; negative after fees).

---

### 14. Bitcoin ETF Creation Flow Days (IBIT / Spot)

Paper and sample end:
- MEASURED: WhyCoinMoves (October 2026, [WhyCoinMoves](https://whycoinmoves.com/research/bitcoin-etf-flows-and-price)): "The sample matches 684 US trading days of spot Bitcoin ETF flows with BTC prices, from 11 January 2024 to 2 October 2026." "The rank correlation with Bitcoin's same-day return was 0.44; after the figures were public, correlations with the next 24-hour and 72-hour returns were both 0.01."
- MEASURED: DWF Labs Research (October 2026, [DWF Labs](https://www.dwf-labs.com/research/do-etf-flows-predict-where-bitcoin-goes-next), 694 trading days Jan 11, 2024 to Oct 16, 2026): "IBIT's daily flow correlates 0.08 with BTC's next-day return and 0.04 with the next five days, the same as the ETF complex as a whole. Big IBIT inflows come after rallies, not before them. IBIT's top 10% of inflow days followed a five-day BTC gain of 7.4% on average, up in 88% of cases."
- MEASURED: Ashish (2026, Concordia University MSc Thesis, [Concordia PDF](https://spectrum.library.concordia.ca/id/eprint/997714/1/Ashish_MSc_F2026.pdf), 494 trading days Jan 2024 to Dec 2025): "The central finding is that Hypothesis 1 is not supported: publicly observable ETF flow data contain no exploitable lagged predictive power for next-day Bitcoin returns, once past returns are taken into account. Across all lag specifications tested (1-10 days), p-values range from 0.325 to 0.943."

Size after retail costs, trades/year, data held, verdict:
- MEASURED: Contemporaneous/backward-looking only; zero forward predictability once daily flows are published. Held data: Alpaca IBIT + Coinbase/Binance. Verdict: DROP (no forward signal).
