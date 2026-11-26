# Round 14: Index-Rebalancing and Forced-Flow Relatives Reachable Through US-Listed Funds

Date: 2026-11-26
Author: idea_scout
Scope: Relatives of the one US-reachable pass (Treasury month-end index buying, Replay 25 / Plan 31) across fixed income, currencies, international equities, volatility, commodities, closed-end funds, and retirement payroll flows that a $500 US retail account can hold long through US-listed funds. No returns were computed in this note. All figures are verbatim from cited primary sources. Claims are labeled MEASURED (empirical result in the source), STATED (official index rule, fund structure, or qualitative statement in the source), or UNKNOWN (not published in the retrieved sources).

Nothing is repeated from Rounds 1 to 13 without new evidence. Replay 25 and Plan 31 covered nominal US Treasury month-end (`TLT`, `TMF`, `UBT`); Round 13 covered equity turn-of-the-month (`SPY`, `IWM`), which faded post-2008.

## Lead-Agent Ruling on the Top Three

Ruling by the lead agent: Replay 31 (`docs/research/80_replay_31_bond_fund_month_end.md`, run 04:44 UTC) already tested `LQD`, `HYG`, `MBB`, and `TIP` at month-end. The plain basket rose (+0.127% a window, t = 3.09), but the residual after Treasury and stock exposure was -0.034% (t = -1.69), passing 2 of 10 marks. Therefore, TIPS (`TIP`, `LTPZ`), agency MBS (`MBB`, `VMBS`), and investment-grade corporate (`LQD`, `VCLT`) month-end are the Treasury month-end effect again, not separate edges; `LTPZ` and `VCLT` would be longer-duration copies of the same thing. None of those three are queued as new tests. Only the two WATCH items from Round 14 (municipal bond month-end `MUB`/`VTEB` and closed-end fund DRIP pay dates) are added to `docs/QUEUE.md` as rows 69 and 70.

## Summary Table

| # | Candidate | Primary Paper or Official Index Rule (Sample End) | Post-Publication / After-Sample Evidence | Size After Retail Costs | Trades/Yr | Data We Hold | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Month-end currency hedge rebalancing into London 4pm fix (`UUP`, `FXE`, `FXY`) | Melvin & Prins 2015 JFM (pre-2015) | 2005 to 2026 replication failed (EUR/USD -1,911 pips, others flat); post-2015 fix reform narrowed reversals | Negative after 2 to 5 bps FX ETF spreads | 12/yr | Alpaca SIP 2016+ | DROP (faded) |
| 2 | MSCI index review effective days in country ETFs (`EEM`, `EFA`, `EW*`) | MSCI Index Policies; Escobar 2026 (2006 to 2017) | Single-stock add/delete CARs (+6.65% mean) cancel inside broad country ETFs; Feb 2023 quarterly shift cut turnover to 0.7% on ACWI | Near zero at country-ETF level | 4/yr | Alpaca SIP 2016+ | DROP (cancels in ETF) |
| 3 | FTSE index review effective days in US-listed funds (`VWO`, `VEA`, `IWM`) | FTSE Russell schedule; Reading CentAUR 76714 | Single-stock index-add effects diminished post-crisis; adds and deletes net out inside index ETFs | Near zero at index-ETF level | 2 to 4/yr | Alpaca SIP 2016+ | DROP (cancels in ETF) |
| 4 | Municipal bond month-end index extension (`MUB`, `VTEB`) | Bloomberg / S&P / ICE Muni Index Methodologies | Official monthly month-end reset on $1.6T / ~57,000 bonds (OAD ~6.1 yrs); no published ETF return test | UNKNOWN; modest ~6 yr duration limits bps per event | 12/yr | Alpaca SIP 2016+ | WATCH (Queue Row 69) |
| 5 | TIPS month-end index extension (`TIP`, `LTPZ`, `SCHP`) | Bloomberg Fixed Income Methodology; Soebhag et al. 2026 | Replay 31 (`docs/research/80_replay_31_bond_fund_month_end.md`) already tested `TIP` in the bond basket; residual after Treasury and stocks was -0.034%, t = -1.69 | Not a separate edge beyond Treasury month-end | 12/yr | Alpaca SIP 2016+ | NOT QUEUED (covered by doc 80) |
| 6 | Agency MBS month-end index extension (`MBB`, `VMBS`) | Bloomberg US MBS / Agg Methodology; MortgageNewsDaily | Replay 31 (`docs/research/80_replay_31_bond_fund_month_end.md`) already tested `MBB` in the bond basket; residual after Treasury and stocks was -0.034%, t = -1.69 | Not a separate edge beyond Treasury month-end | 12/yr | Alpaca SIP 2016+ | NOT QUEUED (covered by doc 80) |
| 7 | US Corporate & HY bond month-end rebalancing (`VCLT`, `LQD`, `HYG`) | Ottonello 2019 SEC FIMSAC; Dimensional Aug 2026 (2017 to 2024) | Replay 31 (`docs/research/80_replay_31_bond_fund_month_end.md`) already tested `LQD` and `HYG` in the bond basket; residual after Treasury and stocks was -0.034%, t = -1.69 | Not a separate edge beyond Treasury month-end | 12/yr | Alpaca SIP 2016+ | NOT QUEUED (covered by doc 80) |
| 8 | VIX ETP daily roll and EOD rebalancing (`VXX`, `UVXY`, `SVXY`) | Brøgger 2021 JBF; Todorov 2024; Barbon 2024 | Brøgger 2021: zero excess profit from trading ahead of predictable VIX ETP rebalancing; pressure evaporates at next open | Negative after wide VIX ETP spreads and daily turnover | 252/yr | Alpaca SIP 2016+ | DROP (no net edge) |
| 9 | Equity index futures roll weeks (quarterly IMM in `SPY`/`IWM`) | CME Group 2025; Carchano & Pardo 2011 (1991 to 2008) | Anomaly is in futures calendar-spread financing vs SOFR, not directional ETF returns; no IMM roll-week ETF anomaly | Zero directional ETF edge | 4/yr | Alpaca SIP 2016+ | DROP (spread only) |
| 10 | Month-end and quarter-end in gold funds (`GLD`, `IAU`) | Górska 2014; QuantifiedStrategies; IJME 2024 | Gold TOM effect "low to non-existing" (2.2% CAGR vs 7.6% B&H); Baur autumn effect reversed; no index extension buyer | Sub-benchmark | 4 to 12/yr | Alpaca SIP 2016+ | DROP (no forced flow) |
| 11 | Japan (JGB) and UK (Gilt) bond index extension via US funds (`IGOV`, `BWX`) | Bloomberg / ITC Markets; BlackRock / SSGA holdings | Large local extensions (Gilts +0.14 to +0.36 yrs, JGBs +0.04 to +0.23 yrs), but NO pure US-listed JGB or Gilt ETF exists | Buried under 100+ bps unhedged FX noise in `IGOV`/`BWX` | 12/yr | Alpaca SIP 2016+ | DROP (no pure US fund) |
| 12 | Closed-end fund (CEF) distribution reinvestment (DRIP) dates | Blouin & Cloyd 2005; Berkman & Koch JFQA | Pay-date DRIP pressure holds in high-yield illiquid names, but premium CEFs issue new shares and DRIPs span up to 30 days | Wide CEF spreads (15 to 50 bps) + missing DRIP/NAV dataset | 12/fund | Alpaca SIP (no NAV/DRIP calendar) | WATCH (Queue Row 70) |
| 13 | 401(k) / payroll contribution flow days (1st and 15th/16th in `SPY`) | AEA 2022 401(k) study; Ma & Pratt 2018; Quanterlab (2012 to 2026) | AEA 2022: zero 401(k) TOM effect and only +5 bps mid-month in top 401(k) stocks; bi-weekly shift eroded 16th-day effect | Zero/negative after spreads vs passive SPY | 12 to 24/yr | Alpaca SIP 2016+ | DROP (faded / +5 bps) |
| 14 | Commodity index monthly roll (GSCI / BCOM days 5 to 9 in `DBC`/`USO`) | Mou 2011 (2000 to 2010); Irwin, Sanders & Yan 2022 AEPP | Irwin et al. 2022: "Spread impacts disappear in the post-financialization period (2012-2019)"; requires futures calendar spreads | Zero / disappeared post-2012 | 12/yr | Alpaca SIP 2016+ | DROP (faded + futures only) |

## Top Three Scouted Candidates (Superseded by Doc 80 Ruling)

As stated in the lead-agent ruling above, Replay 31 (`docs/research/80_replay_31_bond_fund_month_end.md`) already tested `LQD`, `HYG`, `MBB`, and `TIP` at month-end and found the residual after Treasury and stock benchmarks was -0.034% (t = -1.69, 2 of 10 marks). Accordingly, the three fixed-income candidates scouted in Round 14 are recorded for completeness and are not queued as new tests:

1. Candidate 5: TIPS month-end index duration extension (`LTPZ` and `TIP`).
2. Candidate 6: Agency MBS month-end index duration extension (`MBB` and `VMBS`).
3. Candidate 7: US Long Investment-Grade Corporate Bond month-end duration extension (`VCLT` and `LQD`).

Queue additions from Round 14:
- Queue row 69 (Waiting): Municipal bond month-end index extension (`MUB`, `VTEB`). Needs a check on whether tax-exempt municipal month-end returns carry any residual beyond Treasury duration exposure (given doc 80's negative residual on `LQD`, `HYG`, `MBB`, and `TIP`).
- Queue row 70 (Waiting): Closed-end fund (CEF) distribution reinvestment (DRIP) pay dates. Needs a historical discount-to-NAV and exact payable-date dataset plus spread measurement in discounted CEFs.

---

## Detailed Candidate Reviews

### 1. Month-End Currency Hedge Rebalancing Into London 4pm Fix (`UUP`, `FXE`, `FXY`)

Paper and sample end:
- MEASURED: Melvin & Prins (2015, Journal of Financial Markets, [RePEc](https://ideas.repec.org/a/eee/finmar/v22y2015icp50-72.html)): "The findings show that equity market appreciation over the month can be used to predict currency depreciation before the end-of-month fix, providing evidence that hedging activity plays a role in exchange rate determination."
- STATED: CME Group (2026, [CME](https://www.cmegroup.com/articles/2026/month-end-fx-flows-how-to-prepare.html)): "To keep the executed rate close to the valuation rate, funds instruct their banks to trade at or near the fix itself, calculated over a five-minute window centered on 4:00 p.m. London time (typically 11:00 a.m. in New York and 10:00 a.m. in Chicago)."

What happened after publication:
- MEASURED: Post-2015 5-minute fix reform study, Ito & Yamada (NBER w23327, [NBER PDF](https://www.nber.org/system/files/working_papers/w23327/w23327.pdf)): "The reversal seems to happen at the end of fixing window (or 4:02 pm) for both intra-month and end of month samples, but the magnitude is relatively small."
- MEASURED: Independent 2005 to 2026 replication across major USD pairs ([GitHub trading-review/forex.md](https://github.com/Timothymycompc/trading-review/blob/master/forex.md)): "Month-end hedge rebalancing into the London 4pm fix | Melvin & Prins, Journal of Financial Markets 2015 | Fails. EUR/USD -1,911 pips; others ~flat."

Size after costs, trades/year, data held, verdict:
- MEASURED: Negative out-of-sample in spot FX before even accounting for unlevered US currency ETF spreads (2 to 5 bps in `UUP`, `FXE`, `FXY`). Trades: 12/year. Held data: Alpaca SIP 2016+. Verdict: DROP (failed out-of-sample).

---

### 2. MSCI Index Review Effective Days in US-Listed Country ETFs (`EEM`, `EFA`, `EW*`)

Official rule and paper:
- STATED: MSCI Index Review Schedule (November 2026, [MSCI PDF](https://www.msci.com/eqb/pressreleases/archive/ir_dates.pdf)): MSCI conducts quarterly reviews in February, May, August, and November, with effective dates on March 1, June 1, September 1, and December 1 (implemented as of the prior trading day's close).
- MEASURED: Escobar (2026, GWU Working Paper 2026-008, [GWU PDF](https://www2.gwu.edu/~forcpgm/2026-008.pdf), 2006 to 2017): "As expected, passive mutual funds and ETFs concentrate their purchases on the implementation date and trade little between the announcement and implementation dates (on average, 88% of their trading occurs on the implementation day)." "The median CAR is 5.45%, and the mean is 6.65%, statistically different from 0 at the 1% level."

What happened after publication and ETF-level structure:
- STATED: MSCI Index Rebalancing Brochure (2024, [MSCI PDF](https://www.msci.com/downloads/documents/indexes/quarterly-index-reviews/Index+Rebalancing+Brochure+Jan+2024.pdf)): "In February 2023, MSCI transitioned to a comprehensive schedule for the quarterly reviews of its market cap indexes... in 2023, we witnessed a lower quarterly average turnover compared to the semi-annual index reviews conducted in May and November for preceding years." In August 2026 ([MSCI PDF](https://www.msci.com/downloads/web/msci-com/indexes/quarterly-index-review/index-rebalance-aug-cfs-en.pdf)): "Index turnover for the MSCI ACWI and ACWI Small Cap Indexes at the Standard/Small Cap level will be 0.7% and 4.7%, respectively."
- MEASURED: Indonesia/Malaysia event study on MSCI reviews (May 2026, [ISBEST PDF](https://conference.ut.ac.id/index.php/isbest/article/download/9074/3498/22011)): "These findings indicate that the MSCI Index Review announcement influenced trading activity rather than stock returns."

Size after costs, trades/year, data held, verdict:
- STATED: The documented price pressure is cross-sectional (individual added stocks vs deleted stocks, mostly non-US local shares inaccessible to a $500 US account). Inside a US-listed country or EM ETF (`EEM`, `EFA`, `EW*`), additions and deletions largely offset each other and total ACWI turnover is under 1%. Trades: 4/year. Held data: Alpaca SIP 2016+. Verdict: DROP (cross-sectional effect cancels in country ETFs).

---

### 3. FTSE Index Review Effective Days in US-Listed Funds (`VWO`, `VEA`, `IWM`)

Official rule and paper:
- STATED: Index Rebalancing Calendar 2026 ([Ultumus](https://www.ultumus.com/rebalance-calendar)): "FTSE UK and FTSE MIB reviews are quarterly... Effective dates: 23 March, 22 June, 21 September and 21 December." Russell US indexes shifted to semi-annual membership reviews in June and December starting in 2026 ([MarketGenius](https://marketgenius.app/articles/explainers/what-is-index-rebalancing-schedule-rules-and-effects)).
- MEASURED: Post-crisis equity index rebalance evidence (University of Reading, [CentAUR 76714](https://centaur.reading.ac.uk/76714/)): "The results show for the first time, that there are currently no tradable abnormal returns between announcement and event dates in the post-crisis" environment.

Size after costs, trades/year, data held, verdict:
- STATED: Same structural issue as MSCI: index-level US ETFs (`VWO`, `VEA`, `IWM`) hold both additions and deletions simultaneously, so rebalancing flows net out at the fund level. Trades: 2 to 4/year. Held data: Alpaca SIP 2016+. Verdict: DROP (cancels at index-ETF level).

---

### 4. Municipal Bond Month-End Index Extension (`MUB`, `VTEB`)

Official rule and index structure:
- STATED: S&P Municipal Bond Index Methodology ([MSRB PDF](https://www.msrb.org/sites/default/files/Standard-and-Poors-Index-Methodology.pdf)): "The index is normally reviewed and rebalanced on a monthly basis. Additions, deletions and other changes to the index arising from the monthly rebalancing are published, after the close of business, three business days prior to the last business day of the month ('the announcement date'). Index changes published in the announcement are not normally subject to revision and become effective after the close on the last business day of the month ('the rebalancing date')."
- STATED: Bloomberg Municipal Index Monthly ([Bloomberg PDF](https://assets.bbhub.io/professional/sites/10/Bloomberg-Municipal-Index-Monthly-December-2023.pdf)): $1.58T to $1.63T market value across ~56,942 tax-exempt bonds, with option-adjusted duration ~6.10 to 6.18 years and ~500+ bonds entering and exiting each month-end.

After-publication evidence, size after costs, trades/year, data held, verdict:
- UNKNOWN: No retrieved peer-reviewed study directly measures month-end ETF excess returns in `MUB` or `VTEB`.
- STATED: `MUB` has ~1 to 2 bps spreads and 12 trades/year, with Alpaca SIP bars from 2016 onward held, but its ~6.1 year duration is less than half of `TLT`'s ~16+ year duration and any test would need to show a residual beyond Treasury duration (given doc 80). Verdict: WATCH (Queue Row 69).

---

### 5. TIPS Month-End Index Extension (`TIP`, `LTPZ`, `SCHP`)

Official rule and paper:
- STATED: Bloomberg Fixed Income Index Methodology ([Bloomberg PDF](https://assets.bbhub.io/professional/sites/27/Fixed-Income-Index-Methodology.pdf)): "At the close of the last business day of each month, the Bloomberg Indices are reset and bonds formally enter and exit the index, while cash that has accumulated in the Returns Universe during the month is removed."
- MEASURED: Bloomberg Projected Index Duration Extension Report ([Bloomberg PDF](https://assets.bwbx.io/documents/users/iqjWHBFdfxIU/rKfPhv4XjmPg/v0)): "US TIPS (Series-L) empirical extension at 0.08 and real extension at 0.09 years" (compared with US Treasury 0.05 to 0.09 years).
- MEASURED: Soebhag, Verwijmeren & Martinetti (2026, [SSRN 7601879](https://papers.ssrn.com/sol3/Delivery.cfm?abstractid=7601879&mirid=1)): "Major fixed-income indices rebalance at month-end, systematically increasing index duration. We show that the resulting demand for duration generates predictable price pressure in highly liquid government bond markets. Duration-scaled government bond futures earn 1.19 basis points on the last trading day, versus 0.07 basis points on other days, with month-ends accounting for 47% of average monthly returns."

Ruling and verdict:
- MEASURED: Replay 31 (`docs/research/80_replay_31_bond_fund_month_end.md`) already tested `TIP` alongside `LQD`, `HYG`, and `MBB` and found a negative residual (-0.034%, t = -1.69) after Treasury and stock exposure. Verdict: NOT QUEUED (duplicate of Treasury month-end).

---

### 6. Agency MBS Month-End Index Extension (`MBB`, `VMBS`)

Official rule and index structure:
- STATED: FTSE US Mortgage Index ([FTSE Russell](https://research.ftserussell.com/Analytics/FactSheets/Home/DownloadSingleIssue?issueName=MTG&IsManual=True)) and S&P US MBS Methodology ([S&P PDF](https://spglobal.com/spdji/en/documents/methodologies/methodology-sp-us-mbs-index.pdf)): rebalanced monthly on the last business day of the month (announcement T-3, reference T-4).
- MEASURED: Bloomberg Historical Duration Extensions ([Bloomberg PDF](https://assets.bwbx.io/documents/users/iqjWHBFdfxIU/rKfPhv4XjmPg/v0)): Historical monthly duration extensions for US Mortgage Backed Securities range from +0.05 to +0.16 years per month. ITC Markets ([ITC](https://www.itcmarkets.com/itc-month-end-flow-summary/)): "Bloomberg-Barclay Index Extensions US Tsys 0.06Y, MBS 0.07Y."
- STATED: Mortgage News Daily ([MND](https://www.mortgagenewsdaily.com/markets/mbs-day-ahead-12182019)): "Barclays publishes 'index extensions' once a month that let investors know how much they have to increase their bond market holdings in order to keep pace with the rest of the market. That creates net-buying needs in MBS and Treasuries at or near the end of the month."

Ruling and verdict:
- MEASURED: Replay 31 (`docs/research/80_replay_31_bond_fund_month_end.md`) already tested `MBB` in the bond basket and found no residual beyond Treasury and stock exposure (-0.034%, t = -1.69). Verdict: NOT QUEUED (duplicate of Treasury month-end).

---

### 7. US Corporate and High-Yield Bond Month-End Rebalancing (`VCLT`, `LQD`, `HYG`)

Paper and official rule:
- MEASURED: Ottonello (2019, SEC FIMSAC background paper, [SEC PDF](https://www.sec.gov/file/fimsac-110419-background-ottonellopdf)): "Benchmarking has a large impact on bond prices, as funds re-balance in response to mechanical index weight changes. On average, a long/short portfolio of bonds with a mechanical increase/decrease in index weights generates a monthly alpha of 40 bps." "For high yield (HY) (investment grade, [IG]) bonds, the excess return is 88.97 (14.77) bps, with an alpha of 88.10 bps (13.43 bps)."
- MEASURED: Garg & Wang (August 2026, Dimensional Fund Advisors, [Dimensional](https://www.dimensional.com/us-en/insights/the-hidden-costs-of-index-reconstitution-bond-edition), sample 2017 to 2024): "Across these events, trade volumes peak on index rebalance days and are associated with price pressure that hurts index returns... in the 20 trading days up until reconstitution, these [downgrade deletion] bonds have an average cumulative excess return of -2.17% versus a credit- and duration-matched portfolio. However, in the 20 days after deletion from the index, they recover some of the underperformance (+0.48% on average)."

Ruling and verdict:
- MEASURED: Replay 31 (`docs/research/80_replay_31_bond_fund_month_end.md`) already tested `LQD` and `HYG` in the bond basket and found no residual beyond Treasury and stock exposure (-0.034%, t = -1.69). `VCLT` would be a longer-duration copy of the same effect. Verdict: NOT QUEUED (duplicate of Treasury month-end).

---

### 8. VIX ETP Daily Roll and End-of-Day Rebalancing (`VXX`, `UVXY`, `SVXY`)

Paper and sample end:
- MEASURED: Brøgger (2021, Journal of Banking & Finance, [RePEc](https://ideas.repec.org/a/eee/jbfina/v133y2021ics0378426621002363.html)): "While the daily rebalancing imposes an implicit cost on investors by putting pressure on closing prices, there is no evidence that the cost is driven by predatory trading. On the contrary, I show that larger and more predictable flows have smaller price impact coefficients, and that there are no excess profits from trading ahead of rebalancing flows during the sample period."
- MEASURED: Barbon et al. (2024, [PDF](https://abarbon.com/assets/Liquidity_Provision_to_Rebalancing_Flows_from_Leveraged_ETFs_and_Equity_Options.pdf)): "While leveraged ETF-induced price pressure evaporates at the next-day opening, that arising from delta-hedging is significantly longer-lived."
- MEASURED: SEC comment summary of Todorov (2019/2024) and Brøgger ([SEC PDF](https://www.sec.gov/comments/sr-cboebzx-2020-053/srcboebzx2020053-8385718-229360.pdf)): "bid-ask spreads to be narrower, order book deeper, and market resiliency larger on days when ETFs performed a rebalance, finding that this increased liquidity stemmed from a larger number of trading accounts that supplied liquidity to exploit the predictable order flow."

Size after costs, trades/year, data held, verdict:
- MEASURED: No excess profit from trading ahead of daily EOD rebalancing, and daily turnover (~252 trades/year) in volatility ETPs carries wide spreads and extreme overnight gap risk. Held data: Alpaca SIP 2016+. Verdict: DROP (no net edge).

---

### 9. Equity Index Futures Roll Weeks (Quarterly IMM Roll in `SPY` / `IWM`)

Paper and official rule:
- STATED: CME Group (2025, [CME](https://www.cmegroup.com/articles/2025/quantifying-and-hedging-equity-financing-risk.html)): Equity index futures expire quarterly on the third Friday of March, June, September, and December; the documented pricing anomaly is in the futures calendar-spread implied financing rate vs 3-month SOFR and option box rates (e.g., Mar-Jun roll trading at 3mL -28 bps), not in directional spot index returns.
- MEASURED: Carchano & Pardo Tornero (2011, [SSRN 1958587](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1958587), 1991 to 2008): "we present a comprehensive study of 188 possible cyclical anomalies in S&P 500, DAX and Nikkei stock index futures contracts from 1991 to 2008. By applying a percentile-t-bootstrap and Monte Carlo methods, our analysis reveals that the turn-of-the-month effect in S&P 500 futures contracts is the only calendar effect that is statistically and economically significant."

Size after costs, trades/year, data held, verdict:
- STATED: A $500 US equity ETF account cannot trade futures calendar spreads, and no directional long-only ETF edge is documented for IMM roll weeks (4/year). Held data: Alpaca SIP 2016+. Verdict: DROP (calendar-spread financing effect only).

---

### 10. Month-End and Quarter-End in Gold Funds (`GLD`, `IAU`)

Paper and sample end:
- MEASURED: Górska (2014, [CEJSH PDF](http://cejsh.icm.edu.pl/cejsh/element/bwmeta1.element.desklight-3de7a6b6-1310-4a82-8afd-88a5ac7ddaca/c/MIBE_T15_z2_37.pdf), 2008 to 2013): "First of all, we find almost no evidence of calendar effects on London gold market (the only exception is September effect under GARCH methodology), that implies its efficiency."
- MEASURED: Extended reproduction of Baur (2013) ([IJME 2024 PDF](https://reference-global.com/download/article/10.2478/ijme-2024-0011.pdf)): "The main conclusion is that, the autumn effect on the gold market has been reversed and replaced by the winter effect, which is linked to the AMH."
- MEASURED: QuantifiedStrategies GLD turn-of-the-month backtest ([QuantifiedStrategies](https://www.quantifiedstrategies.com/turn-of-the-month-trading-strategy/)): "Because the gold price is 'detached' from the stock market, the effect is low to non-existing. Below is our backtest on GLD: CAGR/annual return: 2.2% (buy and hold GLD dividends reinvested: 7.6%)."

Size after costs, trades/year, data held, verdict:
- STATED: Physical gold has no bond-like duration-extension index buyer at month-end or quarter-end, and historical GLD turn-of-month returns are weak. Trades: 4 to 12/year. Held data: Alpaca SIP 2016+. Verdict: DROP (no forced-flow mechanism).

---

### 11. Japan (JGB) and UK (Gilt) Government Bond Index Extension via US-Listed Funds (`IGOV`, `BWX`)

Official rule and market structure:
- MEASURED: Bloomberg / ITC Markets ([ITC](https://www.itcmarkets.com/itc-month-end-flow-summary/) and [Bloomberg PDF](https://assets.bwbx.io/documents/users/iqjWHBFdfxIU/rKfPhv4XjmPg/v0)): UK Sterling Gilts post some of the largest month-end duration extensions in global fixed income (+0.14 to +0.36 years in refunding/drop months), and JGBs post +0.04 to +0.23 years.
- STATED: US-listed ETF availability ([MyETF 2026](https://myetf.app/market/us/category/international-government-bonds), [BlackRock IGOV](https://www.blackrock.com/us/individual/products/239830/ishares-international-treasury-bond-etf), [SSGA BWX](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-bloomberg-international-treasury-bond-etf-bwx)): Only 6 US-listed international government bond ETFs exist (`IGOV`, `BWX`, `ISHG`, `FLIA`, `BWZ`, `FAIL`), and ZERO pure US-listed JGB or UK Gilt ETFs exist. Pure UK Gilt ETFs (`IGLT`, `VGOV`) are UCITS funds on the LSE not registered for US retail sale, and pure JGB ETFs (`573A.T`, `2561`) trade in Tokyo.
- STATED: In US-listed `IGOV`, Japan is only 11.40% and UK Gilts only 6.29% of holdings, unhedged in USD; in `BWX`, Japan is ~23% and UK ~6%, also unhedged in USD.

Size after costs, trades/year, data held, verdict:
- STATED: A ~15 to 25 bps local JGB or Gilt month-end bond move diluted to 6 to 23% weight inside `IGOV` or `BWX` is ~2 to 5 bps of fund return, completely swamped by 100+ bps of unhedged USD/JPY and USD/GBP currency volatility and ETF spreads. Trades: 12/year. Held data: Alpaca SIP 2016+. Verdict: DROP (no pure US-listed fund).

---

### 12. Closed-End Fund (CEF) Distribution Reinvestment (DRIP) Dates

Paper and fund mechanics:
- MEASURED: Blouin & Cloyd (2005, [SSRN 676632](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=676632)): "Abnormal volume, returns and intraday data around dividend payment dates provide evidence consistent with upward price pressure created as DRIP agents reinvest dividends in fund shares."
- MEASURED: Berkman & Koch (Journal of Financial and Quantitative Analysis, [Cambridge Core](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/drips-and-the-dividend-pay-date-effect/8851243D828E20A290B7730FCD0613CE)): "On the day that dividends are paid, we find a significant positive mean abnormal return that is completely reversed over the following days... concentrated among stocks with dividend reinvestment plans (DRIPs) and is larger for stocks with a higher dividend yield, greater DRIP participation, and greater limits to arbitrage."
- STATED: CEF DRIP rules ([PreferredIncome](https://www.preferredincome.com/closed-end-funds/) and [Morningstar PDF](http://advisor.morningstar.com/Principia/pdf/PRN_QA_for_Closed_End_changes.pdf)): "When the market price is above NAV, new shares will be issued to participants in the Plan at the higher of NAV or 95% of the then current market price" (so open-market buying occurs only when the CEF trades at a discount to NAV). Furthermore, "funds typically have the flexibility to reinvest distributions within a wide date range after the payment date... in some cases up to 30 days."

Size after costs, trades/year, data held, verdict:
- STATED: Real mechanism, but only fires when a CEF trades at a discount to NAV, open-market DRIP windows can stretch up to 30 days, CEF spreads are wide (15 to 50 bps), and we do not hold a historical CEF NAV-discount plus payable-date dataset (similar data gap to Queue row 51). Verdict: WATCH (Queue Row 70).

---

### 13. 401(k) and Payroll Contribution Flow Days (First Sessions of Month, Mid-Month 15th/16th in `SPY`)

Paper and sample end:
- MEASURED: Ma & Pratt (2018, [SSRN 3257064](https://papers.ssrn.com/sol3/Delivery.cfm/SSRN_ID3257064_code1398990.pdf?abstractid=3257064&mirid=1)): "Our results indicate that the 16th day of the month statistically and economically outperforms all other calendar days except the 1st and 2nd. As more and more institutions transition into bi-weekly pay schedule, however, the mid-month payday anomaly becomes less prominent."
- MEASURED: AEA 2022 Working Paper (Price Pressure and the Turn-of-the-Month Effect: Evidence from Retirement Accounts, [AEA](https://www.aeaweb.org/conference/2022/preliminary/paper/iQikdBKZ)): "We test this hypothesis using a hand-collected comprehensive sample of mutual funds contained in 401K retirement accounts in the US... We find no evidence to support this hypothesis. While the ToM effect is still present in the data, stocks held by retirement funds which get large inflows of capital at ends-of-month do not exhibit a stronger ToM effect." "We consistently find that stock returns are not significantly different on average on middle-of-the-month days. However, returns are on average 5 basis points higher in the middle of the month for stocks that are heavily held by retirement funds."
- MEASURED: Quanterlab (November 2026, [Quanterlab](https://quanterlab.com/research/in-search-of-the-market-s-payday), 2012 to 2026): "Owning SPY at the turn of the month turned $1 into $1.31 from 2012 to 2026, owning it on all the other days $3.80, and holding SPY $5.76. They were in the market a fifth of the time, and keeping a fifth of the money in SPY all the time, with the rest in cash, did about as well: $1.43 against their $1.41 before trading costs."

Size after costs, trades/year, data held, verdict:
- MEASURED: Zero 401(k) turn-of-month effect, only +5 bps mid-month in heavily held stocks (not significant on average market days), and bi-weekly payrolls plus 1 to 7 business-day 401(k) deposit lags smear flows across the month. Trades: 12 to 24/year. Held data: Alpaca SIP 2016+. Verdict: DROP (faded / sub-spread).

---

### 14. Commodity Index Monthly Roll (S&P GSCI and BCOM Days 5 to 9 in `DBC` / `GSG` / `USO`)

Paper and sample end:
- MEASURED: Mou (2011, [CFTC PDF](https://www.cftc.gov/ucm/groups/public/@swaps/documents/file/plstudy_33_yu.pdf), sample 1980 to March 2010): "In the rolling month, both the SP-GSCI and DJ-UBSCI have a rolling period of 5 business days... Two trading strategies, devised to exploit this anomaly, yielded excess returns with positive skewness and Sharpe ratios as high as 4.39 from 2000 to March 2010." (Implemented via long-short futures calendar spreads, shorting nearby and longing deferred contracts ahead of business days 5 to 9.)

What happened after publication:
- MEASURED: Irwin, Sanders & Yan (2022, Applied Economic Perspectives and Policy, [PDF](https://scotthirwin.com/wp-content/uploads/2022/02/Irwin_Sanders_Yan_AEPP_All.pdf)): "Spread impacts disappear in the post-financialization period (2012-2019)."

Size after costs, trades/year, data held, verdict:
- MEASURED: Post-2012 roll spread impacts disappeared, and the trade requires long-short futures calendar spreads unavailable to a $500 long-only US ETF account (`DBC`, `USO`). Trades: 12/year. Held data: Alpaca SIP 2016+. Verdict: DROP (disappeared post-2012 + futures calendar-spread only).
