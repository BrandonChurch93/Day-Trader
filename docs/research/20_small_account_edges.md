# 20. Edges that favour a small account

Status: research summary. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Written by a research agent, then the claims that matter most for decisions were checked against their sources by a second model. Claims not listed in the check log were not rechecked. The check log is in `docs/research/17_21_checklogs/`.

## Bottom line

- The only near-certain gain is earning interest on idle cash: US T-bills paid 4.11% to 4.59% on 24 November 2026 ([Treasury daily bill rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&field_tdr_date_value_month=202611)), and Alpaca High-Yield Cash paid up to 3.56% APY as of 22 September 2026 for eligible non-PDT accounts ([Alpaca High-Yield Cash](https://alpaca.markets/blog/alpaca-launches-high-yield-cash-program-for-trading-api-users-enabling-growth-on-deposits/)). Leaving cash at 0% is a measurable drag.
- Odd-lot cash tender offers are real and small-account only, but Alpaca's $100 voluntary corporate action fee kills most of them ([Alpaca brokerage fee schedule](https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf)). Most of the 17 above-market deals found from 2021 to 2026 paid $10 to $350 before fees, so they only work at a $0-fee broker such as Schwab or IBKR ([Schwab pricing guide](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors), [IBKR other fees](https://investors.interactivebrokers.com/en/pricing/other-fees.php)).
- Split-off exchange offers (such as J&J/Kenvue, Cummins/Atmus and Lennar/Millrose) gave odd-lot holders a 6% to 7% discount with no proration over 4 to 5 weeks, roughly once a year ([Kenvue 424B3](https://www.sec.gov/Archives/edgar/data/1944048/000162828023029376/kenvue424b3.htm), [Cummins 425](https://www.sec.gov/Archives/edgar/data/0000026172/000110465924032467/tm245336d53_425.htm), [Lennar 425](https://www.sec.gov/Archives/edgar/data/920760/000119312525288294/d66226d425.htm)). In a long-only account, you hold the parent stock unhedged.
- Overnight-only IWM beat buy and hold in 2020 to 2026 in daily Yahoo data, but lost to buy and hold in 2010 to 2019 ([Yahoo IWM daily data](https://query1.finance.yahoo.com/v8/finance/chart/IWM?interval=1d&period1=1230768000&period2=1800000000)), and real-money NightShares ETFs lost money and liquidated in 2023 ([ETF Strategy](https://www.etfstrategy.com/night-effect-etfs-to-close-10339/), [NightShares 497 filing](https://www.sec.gov/Archives/edgar/data/1199046/000158064223004244/nightshares500_497.htm)). It breaks down at a few basis points per round trip.
- Dead or near-dead for this account: January effect in small stocks since 2013, PEAD outside microcaps, pre-FOMC drift, turn of month, index deletion rebound, spinoff first-month buying, SPY gap fade rules, BTC hour-of-day and weekday patterns, token unlock buying, SPAC trust floor at Alpaca, CEF activist tenders and stablecoin depeg buying.
- Small all-cash merger arbitrage is real and capacity-constrained, but spreads have shrunk and losses behave like short put options ([Mitchell and Pulvino 2001](https://andreisimonov.com/N4106/pdf/MitchellPulvinoJFDec2001.pdf), [Jetley and Ji 2010](https://www.analysisgroup.com/globalassets/uploadedfiles/content/insights/publishing/jetley_and_ji_shrinking_merger_arbitrage_spread.pdf)). It is not yet backtested here.

## What was found

### Odd-lot issuer tender offers and broker fees

| Item | Finding | Tag and source |
|---|---|---|
| SEC odd-lot rule | Issuers may accept all shares from holders of fewer than 100 shares who tender all, before proration. Offers must stay open at least 20 business days, and 10 business days after a price change. Any price increase is paid to all accepted holders. | MEASURED, [17 CFR 240.13e-4](https://www.law.cornell.edu/cfr/text/17/240.13e-4) |
| Alpaca fee | Voluntary Corporate Actions Processing is $100 per unique election (fee schedule revised 17 November 2026). | MEASURED, [Alpaca brokerage fee schedule](https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf) |
| Alpaca process | Elections go through a third-party vendor by email, cost $100 per client per voluntary corporate action, may be rejected if cash is short, and DTC allocation normally takes one to two weeks after election. No API election endpoint is described. | MEASURED process, [Alpaca voluntary corporate actions](https://docs.alpaca.markets/us/docs/voluntary-corporate-actions). API election: UNKNOWN |
| Alpaca Broker API | Voluntary Corporate Action Processing is $100 per unique election. | MEASURED, [Alpaca Broker API Exhibit B](https://files.alpaca.markets/disclosures/library/BrokerAPIExhibitB.pdf) |
| Schwab | Security reorganization (voluntary, mandatory and post-effective) is $0. Only whole shares, not fractional shares, are eligible for voluntary corporate actions such as tender offers. | MEASURED, [Schwab pricing guide](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors), [Schwab One account agreement](https://www.schwab.com/legal/schwab-one-account-agreement) |
| IBKR | Corporate actions under All Other (Mandatory, Voluntary, With Options, etc.) are Free. | MEASURED, [IBKR other fees](https://investors.interactivebrokers.com/en/pricing/other-fees.php) |
| E*TRADE | Voluntary reorganizations (such as tender offers) cost $38. | MEASURED, [E*TRADE pricing](https://us.etrade.com/what-we-offer/pricing-and-rates) |
| Fidelity | Voluntary reorganizations were $38 per transaction, waived for households meeting certain asset and trade minimums, in a 2016-copyright document. Current fee is UNKNOWN. | MEASURED (old), [Fidelity fee document](https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/595_online_equity.pdf) |
| Robinhood | Accepts tender elections through an emailed voluntary election site or support contact. No fee is stated on the support page. | MEASURED process, [Robinhood support](https://robinhood.com/us/en/support/articles/mergers-stock-splits-and-more/). Fee: UNKNOWN |

Frequency and size of cash issuer tenders (approximate screen, MEASURED from SEC EDGAR and Yahoo data). A pull of SC TO-I filings from 2021-01-01 to 2026-11-25 mentioning odd lot or modified Dutch auction via [SEC full-text search](https://efts.sec.gov/LATEST/search-index?q=%22odd%20lot%22&forms=SC%20TO-I) and [SEC submissions data](https://data.sec.gov/submissions/), matched against daily closes from Yahoo chart data (for example [Yahoo PAMT daily data](https://query1.finance.yahoo.com/v8/finance/chart/PAMT?interval=1d&period1=1743465600&period2=1744243200)), yielded about 61 listed common-stock cash issuer tenders with usable prices. In 17 deals (about 3 per year), the fixed offer price or Dutch auction minimum exceeded the commencement-day close.

| Ticker and start | Offer | Close at start | Final result | Days to final | 99-share gross gain | Note |
|---|---|---|---|---|---|---|
| GTIM 2021-08 | $4.60 fixed | 4.39 | $4.60 | 32 | +4.8%, ~$21 | From EDGAR/Yahoo screen |
| AAMI 2021-11 | $31.50 fixed | 30.05 | $31.50 | 35 | +4.8%, ~$144 | From EDGAR/Yahoo screen |
| ULH 2022-05 | $25 to $28 Dutch | 24.60 | $28.00 | 39 | +13.8%, ~$337 | From EDGAR/Yahoo screen |
| PLTK 2022-08 | $11.58 fixed | 11.04 | $11.58 | 43 | +4.9%, ~$53 | From EDGAR/Yahoo screen |
| ADT 2022-09 | $9.00 fixed | 8.66 | $9.00 | 44 | +3.9%, ~$34 | From EDGAR/Yahoo screen |
| PMCB 2023-05 | $3.25 fixed | 3.09 | $3.25 | 35 | +5.2%, ~$16 | From EDGAR/Yahoo screen |
| OPY 2023-05 | $40 fixed | 39.21 | $40.00 | 36 | +2.0%, ~$78 | From EDGAR/Yahoo screen |
| TNET 2023-08 | $107 fixed | 104.61 | $107.00 | 30 | +2.3%, ~$237 | ~$10,356 position for 99 shares |
| PAMT 2024-04 | $15.50 to $18 Dutch | 14.54 | $18.00 | 34 | +23.8%, ~$343 | Low volume, ~31,000 shares/day |
| PAMT 2025-04 | $14 to $17 Dutch | 11.11 (Apr 3 close; Apr 4 close 13.58) | $17.00, proration 99.51545% | 34 | +53% from Apr 3 (~$583), +25% from Apr 4 (~$339) | MEASURED, [PAMT 2025 final press release](https://www.sec.gov/Archives/edgar/data/798287/000121390025040376/ea024113201exa1i_p.htm), [Yahoo PAMT](https://query1.finance.yahoo.com/v8/finance/chart/PAMT?interval=1d&period1=1743465600&period2=1744243200). Offer doc quoted prior-day $12.14 |
| SQFT 2025-04 | $0.68 fixed | 0.59 | $0.68 | 29 | +15.1%, ~$9 | From EDGAR/Yahoo screen |
| ANEB 2025-12 | $3.50 fixed, up to 300,000 shares | 1.72 | UNKNOWN | UNKNOWN | +103% if completed (~$176) | Outcome not verified; parser flagged terminated |
| MLCI 2025-12 | $9.43 fixed | 8.22 | $9.43, proration 28.23% | 39 | +14.7%, ~$120 | MEASURED, [MLCI 2026 final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/2051820/000205182026000024/mlci-sctoxi_ano3feb2026fin.htm). Odd-lot priority drives the edge |
| YEXT 2026-02 | $5.75 to $6.50 Dutch | 5.61 | $5.75 | 38 | +2.5%, ~$14 | From EDGAR/Yahoo screen |
| EXFY 2026-05 | $0.98 to $1.20 Dutch | 1.14 | $1.20 | 30 | +5.3%, ~$6 | From EDGAR/Yahoo screen |
| NFJ 2026-09 | 99% of NAV (CEF) | 15.41 | $15.9192, oversubscribed and prorated | 37 | +3.3% if odd-lot priority applied | Odd-lot treatment in final result UNKNOWN |
| UTMD 2026-09 | $75 fixed, 650,000 shares | 74.75 | $75.00 | 35 | +0.3%, ~$25 | From EDGAR/Yahoo screen |

Other findings from the same EDGAR/Yahoo screen (STATED from the author's automated regex pull, not individually re-audited row by row):

- Among 39 Dutch auctions with a minimum price below market at start, 24 settled above the start close with a median gross gain of +2.6%.
- Some tenders are priced far below market (such as RUM at $7.50 vs a $13.43 close), so terms must be checked deal by deal.
- Nine tickers were excluded for currency or price-matching issues (IMO, WHLR, MTEX, NHP, CVLG, TORO, RBNE, INVE, XBIT).
- At Alpaca's $100 voluntary election fee ([Alpaca brokerage fee schedule](https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf)), only 6 of the 17 deals (ULH, PAMT twice, TNET, AAMI, MLCI, plus ANEB if completed) clear $100 before taxes, and TNET required roughly $10,356 for 99 shares.

### Split-off exchange offers with odd-lot priority

| Deal | Terms | Final result | Tag and source |
|---|---|---|---|
| J&J to Kenvue, Jul to Aug 2023 | 7% discount (~$107.53 of Kenvue per $100 of J&J), upper limit 8.0549, odd lots not prorated, expiry 18 Aug 2023 | 1,533,830,450 Kenvue for 190,955,436 J&J shares (computed ratio 8.0324, below upper limit), proration 23.231832%, all 6,529,526 odd-lot shares accepted | MEASURED, [Kenvue 424B3](https://www.sec.gov/Archives/edgar/data/1944048/000162828023029376/kenvue424b3.htm), [J&J final results](https://www.sec.gov/Archives/edgar/data/0000200406/000162828023030298/a425-pressrelease08232023.htm) |
| Cummins to Atmus, Feb to Mar 2024 | 7% discount (~$107.53 per $100), upper limit 13.3965, odd lots not prorated | Ratio 12.0298, proration 6.99255200%, all odd-lot tenders accepted | MEASURED, [Cummins 425](https://www.sec.gov/Archives/edgar/data/0000026172/000110465924032467/tm245336d53_425.htm), [Cummins final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/26172/000110465924035612/tm245866-7_sctoia.htm) |
| Lennar to Millrose, Oct to Nov 2025 | 6% discount (~$106.38 per $100), upper limit 4.1367, odd lots not prorated | Proration 8.604228%, all 778,625 odd-lot shares accepted | MEASURED, [Lennar 425](https://www.sec.gov/Archives/edgar/data/920760/000119312525288294/d66226d425.htm), [Lennar final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/920760/000119312525300679/d876414dsctoia.htm) |
| 3M to Neogen, Aug to Sep 2022 | Discount terms not checked (UNKNOWN) | Ratio 6.7713, proration ~7.346065%, odd-lot tenders fully accepted | MEASURED final only, [3M final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/66740/000114036122032385/ny20004937x37_sctoia.htm) |
| DuPont to N&B/IFF, Jan to Feb 2021 | Discount terms not checked (UNKNOWN) | Proration 52.53%, odd-lot tenders fully accepted | MEASURED final only, [DuPont final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/1666700/000119312521027295/d125432dsctoia.htm) |
| Medtronic to MiniMed, Sep to Oct 2026 | Discount terms not checked (UNKNOWN) | Oversubscribed, proration 18.289133%, all 757,890 odd-lot shares accepted | MEASURED final only, [Medtronic final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/1613103/000162828026065823/mdt-amendedno4scheduleissu.htm) |

In a long-only account, you hold the parent unhedged for roughly 4 weeks and then hold the new shares until delivery clears. The exchange ratio is set from 3-day VWAPs near expiry, so the 6% to 7% discount is against that ending average, not your entry price. Buying 99 shares of large-cap parents required roughly $9,000 to $25,000; smaller holdings (such as 10 shares) still qualify for odd-lot priority at a $0-fee broker, but fail after Alpaca's $100 fee.

### Merger arbitrage, SPACs, closed-end funds and CVRs

| Item | Finding | Tag and source |
|---|---|---|
| Merger arb long run | 4,750 US deals (1963 to 1998): ~4% a year excess after costs (~2% for individuals without interest on short proceeds); returns resemble writing uncovered index puts; raising starting capital from $1M to $10M cut annual returns by 3.79 percentage points. | MEASURED (old, in-sample), [Mitchell and Pulvino 2001](https://andreisimonov.com/N4106/pdf/MitchellPulvinoJFDec2001.pdf) |
| Shrinking spreads | 2,182 deals (1990 to 2007): median first-day arbitrage spread for successful deals fell from 6.39% (1990 to 1995) to 4.62% (1996 to 2001) to 1.91% (2002 to 2007). | MEASURED, [Jetley and Ji 2010](https://www.analysisgroup.com/globalassets/uploadedfiles/content/insights/publishing/jetley_and_ji_shrinking_merger_arbitrage_spread.pdf) |
| Small-deal manager | Pender arbitrage funds reported +5.0% and +5.9% in 2025 vs +10.3% for HFRI Merger Arbitrage; held 52 deals under $2B (42 under $1B); SPACs searching for targets yielded 3.99% to maturity; 287 SPACs held $40B+ in trust. | STATED (manager letter), [Pender December 2025 letter](https://penderfund.com/wp-content/uploads/2026/01/Pender-Alternative-Arbitrage-Fund-Comment-December-2025-FA.pdf) |
| SPAC trust floor | 458 SPAC IPOs (2010 to 2020): equal-weight annualized return 23.9% during the SPAC period (median 5.6%), driven by 2020 to 2021 mergers (33.2%); liquidated SPACs returned 2.0%/year and ongoing 2.3%/year. | MEASURED, [Gahng, Ritter and Zhang](https://site.warrington.ufl.edu/ritter/files/SPACs.pdf) |
| SPAC volume and redemptions | SPAC IPOs: 86 (2022), 31 (2023), 57 (2024), 144 (2025), and 62, 56, 35 in 2026 Q1 to Q3. Average deSPAC redemption rates were 85.8% to 98.1% across 2023 to 2024 quarters, and 76.7% to 82.0% in 2026 Q1 to Q3. | MEASURED, [Ritter IPO and SPAC tables](https://site.warrington.ufl.edu/ritter/files/IPOs-SPACs.pdf) |
| CEF discounts and activists | Equity CEF discounts moved from 7.0% (year-end 2024) to 4.8% (Aug 2025) to 5.6% (year-end 2025). Activists filed 25 campaigns on 24 CEFs in 2025 (80% by three activists). Across 41 forced-tender CEFs (2015 to Aug 2024), average excess discount went from -5.3% to -2.5% to -0.5% during the tender, then widened back to -3.1% a year later; activists fully exited 72%. | MEASURED, [ICI Perspective 32-03](https://www.ici.org/system/files/2026-04/per-32-03.pdf) |
| CEF open-ending | Claim that open-ending attempts halve discounts (1988 to 2003) could not be verified because the journal page did not return an abstract. | UNKNOWN, [Bradley et al. 2010 link](https://doi.org/10.1016/j.jfineco.2009.01.005) |
| CVRs and stubs | No primary evidence on CVR or merger stub returns was opened. | UNKNOWN |

Account fit: SPAC redemptions, CEF tenders and third-party cash tender offers (SC TO-T) are voluntary elections, triggering Alpaca's $100 fee ([Alpaca brokerage fee schedule](https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf)). A closing cash merger or SPAC liquidation is mandatory and avoids the voluntary fee.

### Event effects in stocks

| Effect | Finding | Tag and source |
|---|---|---|
| Spinoffs, long horizon | 146 US spinoffs (2001 to 2012): subsidiaries beat benchmarks by +17.1% over 22 months, which authors note worked "perhaps by luck rather than skill"; the spinoff ETF fell 55.2% in 2008. | MEASURED, [McConnell, Sibley and Xu](https://business.purdue.edu/faculty/mcconnell/publications/The%20Stock%20Price...2013%20jpm.2015.42.1.143.pdf) |
| Spinoffs, first month | 516 US spinoffs (1989 to 2015): spun-off entities averaged -1.37% excess over 5 days (hit rate 39.5%) and -2.28% over 30 days (hit rate 42.9%), both significant at 1%. Three-month excess (+1.18%) was not significant; 1-year was +8.39% and 3-year +22.08% (hit rates near 50%). | MEASURED, [S&P Global spinoff study](https://www.spglobal.com/content/dam/spglobal/mi/en/documents/general/Capital-Market-Implications-Of-Spinoffs.pdf) |
| Index deletions | S&P 500 deletion announcement abnormal return shrank from -16.11% (1990s) and -12.39% (2000s) to -0.62% (2010 to 2020, not significant). | MEASURED, [Greenwood and Sammon, HBS](https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf) |
| January effect | Value-weighted small-minus-big decile January return: +9.03% (1927 to 1979), +3.01% (1980 to 1999), +4.38% (2000 to 2012, t = 2.92), +0.62% (2013 to 2025, t = 0.36, positive in 5 of 13 years), and +0.83% (2013 to 2026, t = 0.51, positive in 6 of 14 years). December 2000 to 2025: +1.30% (t = 1.92, n = 26). Gross, no costs. | MEASURED, recomputed from [Ken French size portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_ME_CSV.zip) |
| Muni CEF January effect | Abstract reports the January effect in municipal bond CEFs became stronger in recent years, while in municipal bond ETFs it is smaller. Full paper paywalled. | STATED (abstract only), [Carrion 2024](https://onlinelibrary.wiley.com/doi/10.1111/jfir.12384) |
| PEAD | Gone for all-but-microcap stocks since 2006; in microcaps, 60-day drift is gone since 2016 and any remaining drift is confined to days 2 to 5. | MEASURED, [Martineau](https://cfr.ivo-welch.org/forthcoming/papers/martineau2021rest.pdf) |
| Rights offerings | 8,238 rights offers (1995 to 2008, 69 countries): rights had zero return on 55% of trading days and wide spreads. US-specific returns UNKNOWN. Exercise is a $100 voluntary action at Alpaca. | MEASURED global illiquidity, [INSEAD working paper](https://flora.insead.edu/fichiersti_wp/inseadwp2013/2013-120.pdf) |

### Calendar, overnight and reversal effects in index funds

| Effect | Finding | Tag and source |
|---|---|---|
| Overnight vs intraday, literature | US stocks (1993 to 2013): CRSP market earned 0.55%/month overnight vs 0.38%/month intraday; short-term reversal earned +0.93% overnight three-factor alpha (t = 4.28) vs -1.05% intraday CAPM alpha (t = -3.25). Gross, long-short. | MEASURED, [Lou, Polk and Skouras](https://researchonline.lse.ac.uk/id/eprint/87481/7/Polk_Tug%20of%20War.pdf) |
| Overnight, real money | NightShares 500 (NPSY) lost 4.72% and NightShares 2000 (NIWM) lost 7.61% from 28 June 2022 launch to 1 August 2023, vs +21.8% and +16.6% daytime returns. NightShares 500 497 filing set liquidation on or about 8 September 2023. | STATED returns, [ETF Strategy](https://www.etfstrategy.com/night-effect-etfs-to-close-10339/); MEASURED liquidation, [NightShares 497 filing](https://www.sec.gov/Archives/edgar/data/1199046/000158064223004244/nightshares500_497.htm) |
| Overnight cross-check | Recomputing SPY on the same 28 June 2022 to 1 August 2023 window gives -3.6% cumulative overnight (-3.3%/year) vs +23.9% cumulative intraday (+21.7%/year), matching NightShares' real-money loss. | MEASURED, [Yahoo SPY daily data](https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&period1=1230768000&period2=1800000000) |
| Pre-FOMC drift | 49 bp (0.492%) in 1994 to 2011 (n = 131); fell to 9.2 bp (0.092%, n = 20, not significant) for press-conference meetings in 2016 to 2019, and 4.7 bp across all 70 meetings in 2011 to 2019. | MEASURED, [Kurov, Wolfe and Gilbert, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/) |
| Turn of month | SPY last trading day plus first 3 trading days: 2020 to 2026-11 mean 9.4 bp/day (t = 1.49, n = 332) vs 5.2 bp other days; 2010 to 2019 mean 6.1 bp (t = 1.39, n = 480) vs 5.3 bp. Gross. | MEASURED, [Yahoo SPY daily data](https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&period1=1230768000&period2=1800000000) |
| Turn of month, international | Significant in 14 of 15 indices in 1983 to 2013, but faded in 2014 to 2022 in 14 of 15 (only New Zealand remained significant). Dash for Cash slides document T-4 reversals without an after-cost retail test. | MEASURED, [Aalto thesis](https://aaltodoc.aalto.fi/server/api/core/bitstreams/27ca8cf2-8edd-4ac5-b81f-20b11032661a/content), [Etula et al. slides](https://www.aalto.fi/sites/default/files/2021-03/dash4cashpresentation_bi_r.pdf) |
| Pre-holiday | SPY trading day before US market holidays: 2020 to 2026-11 mean 20.8 bp (t = 2.64, n = 65); 2010 to 2019 mean 3.7 bp (t = 0.40, n = 91). Gross, unstable across decades. | MEASURED, [Yahoo SPY daily data](https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&period1=1230768000&period2=1800000000) |
| Short-term reversal costs | Short-term reversal does not survive transaction costs above $9 billion in the US ($13 billion globally). Already covered in playbook 01 rule 4. | MEASURED, [Frazzini, Israel and Moskowitz](https://www.hbs.edu/faculty/Shared%20Documents/events/328/TradingCostEfficiency_FULL_112912.pdf) |
| SPY gap fade | Correlation of overnight gap with same-day intraday return: 0.032 (2010 to 2019) and 0.021 (2020 to 2026-11). After gaps above +0.5%, intraday averaged +12.1 bp (n = 346) and +5.6 bp (n = 319); after gaps below -0.5%, -2.1 bp (n = 286) and +3.8 bp (n = 258). Gross. | MEASURED, [Yahoo SPY daily data](https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&period1=1230768000&period2=1800000000) |

Overnight-only daily replay (MEASURED, recomputed from Yahoo daily adjusted data for [SPY](https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&period1=1230768000&period2=1800000000), [IWM](https://query1.finance.yahoo.com/v8/finance/chart/IWM?interval=1d&period1=1230768000&period2=1800000000) and [QQQ](https://query1.finance.yahoo.com/v8/finance/chart/QQQ?interval=1d&period1=1230768000&period2=1800000000)). Buy at close, sell at next open, every trading day, gross of cash yield. Cost is per round trip (compare `cost_model_bps_per_side_liquid_etf` and `backtest_min_breakeven_cost_multiple` in `config/thresholds.yaml`).

| Fund | Period | Overnight 0 bp | Overnight 2 bp | Overnight 5 bp | Intraday only | Buy and hold |
|---|---|---|---|---|---|---|
| SPY | 2010 to 2019 | +8.6%/yr | +3.3%/yr | -4.3%/yr | +4.5%/yr | +13.5%/yr |
| SPY | 2020 to 2026-11 | +9.9%/yr | +4.5%/yr | -3.1%/yr | +3.7%/yr | +13.9%/yr |
| IWM | 2010 to 2019 | +10.5%/yr | +5.1%/yr | -2.6%/yr | +1.2%/yr | +11.8%/yr |
| IWM | 2020 to 2026-11 | +17.6%/yr | +11.9%/yr | +3.8%/yr | -7.8%/yr | +8.5%/yr |
| QQQ | 2010 to 2019 | +13.1%/yr | +7.6%/yr | -0.2%/yr | +4.2%/yr | +17.9%/yr |
| QQQ | 2020 to 2026-11 | +12.9%/yr | +7.3%/yr | -0.5%/yr | +4.5%/yr | +18.0%/yr |

Caveats: Yahoo daily open may not match the official opening auction print; this is one dataset and one post-hoc decade split; daily trading creates short-term tax drag and wash sales in a taxable account.

### Crypto, long only, spot only

| Effect | Finding | Tag and source |
|---|---|---|
| BTC hour of day and weekday | 51,660 hourly candles (Jan 2021 to Nov 2026): hourly means ranged from -4.65 to +3.30 bp, with correlation -0.08 between 2021 to 2023 and 2024 to 2026 (no persistence). Weekday correlation was 0.47, still far below trading fees. | MEASURED, [Coinbase BTC-USD hourly candles](https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600) |
| Calendar literature | Over 15 million observations across seven Bitcoin exchanges showed time-varying effects but "no consistent or persistent patterns across the sample period." | MEASURED (abstract), [Baur, Cahill, Godfrey and Liu 2019](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3088472) |
| Spot ETF flows | $100M net flow into the five largest US spot BTC ETFs coincided with 53 bp same-day return and predicted next-day returns (Newey-West t = 3.12), Jan 2024 to Apr 2025 (313 days). Single independent author, short sample, no trading cost test. | STATED (abstract), [Lim, SSRN 6592830](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6592830) |
| Token unlocks | Blockchain Capital cites Keyrock finding 90% of 16,000+ unlocks created negative price pressure (secondhand; Keyrock page not opened). TrueHold's study of 310 unlocks across 14 tokens found the 7 days after an unlock (-2.3% vs BTC) matched an ordinary week (-2.5%). Long only, this is at best an avoid signal. | STATED, [Blockchain Capital](https://blockchaincapital.com/blog/the-tomb-we-built), [TrueHold](https://www.truehold.xyz/unlocks/price-impact) |
| Stablecoin depegs | In March 2023, Circle confirmed $3.3B (about 8% of USDC reserves) stuck at SVB and announced the de-peg closed on 12 to 13 March 2023 after USDC fell to $0.8774. Counterexample: Terra/UST collapsed in three days in May 2022 (run started 7 May 2022), wiping out $50B. | MEASURED Circle/NBER, [Circle press release](https://www.circle.com/pressroom/3-3-billion-of-usdc-reserve-risk-removed-dollar-de-peg-closes), [NBER w31160](https://www.nber.org/papers/w31160); STATED low price, [Cointelegraph](https://cointelegraph.com/news/usdc-depegs-as-circle-confirms-3-3b-stuck-with-silicon-valley-bank) |
| Crypto weekend effect | Negative weekend returns across 20 large cryptocurrencies predict Monday equity declines; positive weekend returns have no effect. A stock timing signal, not a long-only crypto buy rule. | STATED (abstract), [Mourey et al.](https://hal.science/hal-05415054v1/file/A%20crypto-stock%20weekend%20effect.%20Predicting%20Monday%20stock%20returns%20using%20weekend%20cryptocurrency%20returns.pdf) |

### Idle cash

| Item | Finding | Tag and source |
|---|---|---|
| US T-bills, 24 Nov 2026 | Coupon equivalent yields: 4-week 4.11%, 13-week 4.28%, 26-week 4.50%, 52-week 4.59%. | MEASURED, [Treasury daily bill rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&field_tdr_date_value_month=202611) |
| Alpaca High-Yield Cash | Up to 3.56% APY as of 22 September 2026 (variable), for eligible non-PDT Trading API accounts, via FDIC bank sweep up to $2.5M, still usable as buying power. | MEASURED, [Alpaca High-Yield Cash](https://alpaca.markets/blog/alpaca-launches-high-yield-cash-program-for-trading-api-users-enabling-growth-on-deposits/) |
| Bank and broker sign-up bonuses | Not researched. | UNKNOWN |

## What it means for a small automated long-only account

- Earning about 3.5% to 4.5% on idle cash is the largest reliable improvement here, and every backtest must credit idle cash at the T-bill rate or comparisons to buy and hold will be distorted.
- The genuine small-account edges (odd-lot cash tenders, odd-lot split-offs and SC TO-T tender merger arbitrage) require voluntary corporate action elections. At Alpaca, those cost $100 per election and run through email rather than an API ([Alpaca brokerage fee schedule](https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf), [Alpaca voluntary corporate actions](https://docs.alpaca.markets/us/docs/voluntary-corporate-actions)). They only make sense as manual trades at a $0-fee broker such as Schwab or IBKR.
- The 99-share odd-lot ceiling keeps dollar profits modest even when percentage returns are high, which fits a small account but limits annual dollar upside.
- Fast, fully automatable calendar, gap and crypto-timing effects are mostly dead or unstable after costs. Overnight-only IWM is the only one with a strong 2020 to 2026 replay, but it failed in 2010 to 2019, failed in real money at NightShares, and is tightly squeezed by `cost_model_bps_per_side_liquid_etf` and `backtest_min_breakeven_cost_multiple` in `config/thresholds.yaml`.
- None of these edges removes market risk. Long-only split-offs and merger arbitrage carry full unhedged equity and deal-break risk.

## What is worth testing here

Ranked from fastest honest value to most fragile:

| Rank and idea | Why it might work | Best evidence | Main weakness | Test to confirm or kill | Free data tonight, no keys |
|---|---|---|---|---|---|
| 1. Idle cash yield (Alpaca HYC or 4 to 13 week T-bills) | Contractual interest, not a market anomaly | T-bills 4.11% to 4.59% ([Treasury](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&field_tdr_date_value_month=202611)); Alpaca up to 3.56% APY ([Alpaca](https://alpaca.markets/blog/alpaca-launches-high-yield-cash-program-for-trading-api-users-enabling-growth-on-deposits/)) | Alpaca HYC excludes PDT accounts; rates float; T-bills tie up cash until maturity | Check account eligibility and live APY; add daily T-bill return to idle cash in every backtest | Yes for backtest credit; enrolment needs owner |
| 2. Split-off exchange offers with odd-lot priority at a $0-fee broker | Funds hold over 100 shares and face heavy proration (7% to 53%); odd lots are exempt | Six deals checked all accepted 100% of odd lots, with 6% to 7% discounts in J&J, Cummins and Lennar ([Kenvue 424B3](https://www.sec.gov/Archives/edgar/data/1944048/000162828023029376/kenvue424b3.htm), [Cummins final](https://www.sec.gov/Archives/edgar/data/26172/000110465924035612/tm245866-7_sctoia.htm), [Lennar final](https://www.sec.gov/Archives/edgar/data/920760/000119312525300679/d876414dsctoia.htm)) | About 1 deal/year; 4 to 5 weeks unhedged parent risk; upper limit can cut discount; manual election; $100 fee at Alpaca | Pull all SC TO-I exchange offers since 2010 from EDGAR, record discount, final ratio and actual parent-to-subsidiary return from commencement to first post-delivery trading day | Yes (EDGAR and Yahoo); live execution is manual |
| 3. Odd-lot cash issuer tenders priced above market at a $0-fee broker | Proration and the 99-share cap keep institutions out | 17 deals in 2021 to 2026 (~3/year), e.g., PAMT 2025 and MLCI 2025 ([PAMT final](https://www.sec.gov/Archives/edgar/data/798287/000121390025040376/ea024113201exa1i_p.htm), [MLCI final](https://www.sec.gov/Archives/edgar/data/2051820/000205182026000024/mlci-sctoxi_ano3feb2026fin.htm)) | Small dollars ($10 to $350 typical); $100 Alpaca fee kills most; deals can terminate or lack odd-lot priority | Manually verify all 17 deals plus 2015 to 2020 from SEC filings using next-day open entry and $0 vs $100 fees | Yes (EDGAR and Yahoo); live execution is manual |
| 4. Overnight-only IWM via closing and opening auctions | Overnight carried most equity returns in 1993 to 2013 and IWM intraday was -7.8%/yr in 2020 to 2026 | [Lou, Polk and Skouras](https://researchonline.lse.ac.uk/id/eprint/87481/7/Polk_Tug%20of%20War.pdf); Yahoo IWM +11.9%/yr at 2 bp vs +8.5% buy and hold in 2020 to 2026 ([Yahoo IWM](https://query1.finance.yahoo.com/v8/finance/chart/IWM?interval=1d&period1=1230768000&period2=1800000000)) | Lost to buy and hold 2010 to 2019 (+5.1% vs +11.8%); NightShares failed in real money; breaks down near 5 bp round trip; wash-sale drag | Rerun 2005 to 2026 with official NYSE Arca auction prints and test against `backtest_min_breakeven_cost_multiple`, then paper trade Alpaca opg/cls fills | Daily Yahoo test done; official auction test needs market data keys |
| 5. Small all-cash merger arbitrage (closing mergers only at Alpaca) | Capacity constraints limit big funds in small deals | ~4% excess 1963 to 1998 ([Mitchell and Pulvino 2001](https://andreisimonov.com/N4106/pdf/MitchellPulvinoJFDec2001.pdf)); Pender +5% to +6% in 2025 STATED ([Pender letter](https://penderfund.com/wp-content/uploads/2026/01/Pender-Alternative-Arbitrage-Fund-Comment-December-2025-FA.pdf)) | Spreads shrank to 1.91% median by 2002 to 2007 ([Jetley and Ji 2010](https://www.analysisgroup.com/globalassets/uploadedfiles/content/insights/publishing/jetley_and_ji_shrinking_merger_arbitrage_spread.pdf)); sharp put-like break losses; SC TO-T triggers $100 Alpaca fee | Pull DEFM14A and SC TO-T all-cash deals since 2015 from EDGAR, enter 1 day after announcement, include broken deals and measure worst 5% tail | Partially (Yahoo drops delisted tickers, creating survivor bias) |
| 6. Pre-holiday index filter (do not sell before US holidays) | Long-documented pre-holiday drift | SPY +20.8 bp (t = 2.64, n = 65) in 2020 to 2026 ([Yahoo SPY](https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&period1=1230768000&period2=1800000000)) | Only +3.7 bp (t = 0.40) in 2010 to 2019; ~9 days/year; filter only, not a standalone strategy | Extend to 1993, test by decade after costs, and test only as a trade-delay filter | Yes |

Ideas ruled out for this account:

- January effect in small stocks: +0.83% small-minus-big in 2013 to 2026 (t = 0.51, MEASURED, [Ken French size portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_ME_CSV.zip)).
- PEAD: gone outside microcaps since 2006 and confined to days 2 to 5 in microcaps since 2016 (MEASURED, [Martineau](https://cfr.ivo-welch.org/forthcoming/papers/martineau2021rest.pdf)).
- Pre-FOMC drift: 9.2 bp and not significant in 2016 to 2019 (MEASURED, [Kurov, Wolfe and Gilbert](https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/)).
- Turn of month: weak and not significant in SPY, and faded in 14 of 15 international indices in 2014 to 2022 (MEASURED, [Yahoo SPY](https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&period1=1230768000&period2=1800000000), [Aalto thesis](https://aaltodoc.aalto.fi/server/api/core/bitstreams/27ca8cf2-8edd-4ac5-b81f-20b11032661a/content)).
- Index deletion rebound: announcement drop shrank to -0.62% in 2010 to 2020 (MEASURED, [Greenwood and Sammon](https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf)).
- Spinoff first-month buying: -2.28% average 30-day excess return (MEASURED, [S&P Global](https://www.spglobal.com/content/dam/spglobal/mi/en/documents/general/Capital-Market-Implications-Of-Spinoffs.pdf)).
- SPY gap fade or continuation: near-zero correlation (0.021 to 0.032, MEASURED, [Yahoo SPY](https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&period1=1230768000&period2=1800000000)).
- BTC hour-of-day and weekday timing: tiny means and -0.08 hourly correlation across halves, far below fees (MEASURED, [Coinbase BTC-USD](https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600)).
- Token unlocks: mixed evidence and long-only can only avoid, not short (STATED, [Blockchain Capital](https://blockchaincapital.com/blog/the-tomb-we-built), [TrueHold](https://www.truehold.xyz/unlocks/price-impact)).
- SPAC trust floor: yields roughly T-bill rates (3.99% STATED, [Pender letter](https://penderfund.com/wp-content/uploads/2026/01/Pender-Alternative-Arbitrage-Fund-Comment-December-2025-FA.pdf)) minus Alpaca's $100 redemption fee; T-bills are simpler.
- CEF activist tenders: prorated, and excess discounts re-widen within a year (MEASURED, [ICI Perspective 32-03](https://www.ici.org/system/files/2026-04/per-32-03.pdf)).
- Stablecoin depeg buying: USDC recovered in days, but UST wiped out $50B in three days with no reliable way to separate survivors ahead of time (MEASURED, [Circle](https://www.circle.com/pressroom/3-3-billion-of-usdc-reserve-risk-removed-dollar-de-peg-closes), [NBER w31160](https://www.nber.org/papers/w31160)).

## Not verified or unfinished

- ANEB 2025 tender offer final outcome is UNKNOWN.
- NFJ 2026 tender offer odd-lot priority treatment is UNKNOWN.
- Discount terms for the 3M/Neogen, DuPont/N&B/IFF and Medtronic/MiniMed split-off offers were not checked (only final proration and odd-lot acceptance were verified).
- Fifteen of the 17 rows in the 2021 to 2026 odd-lot cash tender table rely on the author's automated regex/Yahoo screen and were not individually re-audited against SEC final-result filings; pre-2021 deals were not collected.
- Current Fidelity and Robinhood voluntary corporate action fees are UNKNOWN (Fidelity's opened document is from 2016; Robinhood's support page omits fees).
- Whether Alpaca offers any Trading API endpoint for voluntary corporate action elections is UNKNOWN.
- Small cash merger arbitrage backtest (including delisted and broken deals) has not been run.
- Bradley, Brav, Goldstein and Jiang 2010 (CEF open-ending) could not be opened due to publisher paywall/error.
- Keyrock's primary token unlock report was not opened; the 16,000-event figure is secondhand.
- CVR returns, merger stubs, US-specific rights offering returns and bank/broker sign-up bonuses remain UNKNOWN.

## Sources

- [17 CFR 240.13e-4](https://www.law.cornell.edu/cfr/text/17/240.13e-4)
- [Alpaca brokerage fee schedule](https://files.alpaca.markets/disclosures/library/BrokFeeSched.pdf)
- [Alpaca voluntary corporate actions](https://docs.alpaca.markets/us/docs/voluntary-corporate-actions)
- [Alpaca Broker API Exhibit B](https://files.alpaca.markets/disclosures/library/BrokerAPIExhibitB.pdf)
- [Alpaca High-Yield Cash](https://alpaca.markets/blog/alpaca-launches-high-yield-cash-program-for-trading-api-users-enabling-growth-on-deposits/)
- [Schwab pricing guide](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors)
- [Schwab One account agreement](https://www.schwab.com/legal/schwab-one-account-agreement)
- [IBKR other fees](https://investors.interactivebrokers.com/en/pricing/other-fees.php)
- [E*TRADE pricing](https://us.etrade.com/what-we-offer/pricing-and-rates)
- [Fidelity fee document](https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/595_online_equity.pdf)
- [Robinhood support](https://robinhood.com/us/en/support/articles/mergers-stock-splits-and-more/)
- [SEC full-text search](https://efts.sec.gov/LATEST/search-index?q=%22odd%20lot%22&forms=SC%20TO-I)
- [SEC submissions data](https://data.sec.gov/submissions/)
- [PAMT 2025 final press release](https://www.sec.gov/Archives/edgar/data/798287/000121390025040376/ea024113201exa1i_p.htm)
- [Yahoo PAMT daily data](https://query1.finance.yahoo.com/v8/finance/chart/PAMT?interval=1d&period1=1743465600&period2=1744243200)
- [MLCI 2026 final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/2051820/000205182026000024/mlci-sctoxi_ano3feb2026fin.htm)
- [Kenvue 424B3](https://www.sec.gov/Archives/edgar/data/1944048/000162828023029376/kenvue424b3.htm)
- [J&J final results](https://www.sec.gov/Archives/edgar/data/0000200406/000162828023030298/a425-pressrelease08232023.htm)
- [Cummins 425](https://www.sec.gov/Archives/edgar/data/0000026172/000110465924032467/tm245336d53_425.htm)
- [Cummins final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/26172/000110465924035612/tm245866-7_sctoia.htm)
- [Lennar 425](https://www.sec.gov/Archives/edgar/data/920760/000119312525288294/d66226d425.htm)
- [Lennar final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/920760/000119312525300679/d876414dsctoia.htm)
- [3M final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/66740/000114036122032385/ny20004937x37_sctoia.htm)
- [DuPont final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/1666700/000119312521027295/d125432dsctoia.htm)
- [Medtronic final SC TO-I/A](https://www.sec.gov/Archives/edgar/data/1613103/000162828026065823/mdt-amendedno4scheduleissu.htm)
- [Mitchell and Pulvino 2001](https://andreisimonov.com/N4106/pdf/MitchellPulvinoJFDec2001.pdf)
- [Jetley and Ji 2010](https://www.analysisgroup.com/globalassets/uploadedfiles/content/insights/publishing/jetley_and_ji_shrinking_merger_arbitrage_spread.pdf)
- [Pender December 2025 letter](https://penderfund.com/wp-content/uploads/2026/01/Pender-Alternative-Arbitrage-Fund-Comment-December-2025-FA.pdf)
- [Gahng, Ritter and Zhang](https://site.warrington.ufl.edu/ritter/files/SPACs.pdf)
- [Ritter IPO and SPAC tables](https://site.warrington.ufl.edu/ritter/files/IPOs-SPACs.pdf)
- [ICI Perspective 32-03](https://www.ici.org/system/files/2026-04/per-32-03.pdf)
- [Bradley et al. 2010 link](https://doi.org/10.1016/j.jfineco.2009.01.005)
- [McConnell, Sibley and Xu](https://business.purdue.edu/faculty/mcconnell/publications/The%20Stock%20Price...2013%20jpm.2015.42.1.143.pdf)
- [S&P Global spinoff study](https://www.spglobal.com/content/dam/spglobal/mi/en/documents/general/Capital-Market-Implications-Of-Spinoffs.pdf)
- [Greenwood and Sammon, HBS](https://www.hbs.edu/ris/Publication%20Files/23-025_563e45c6-df92-4d9c-ae05-608d4d0acab1.pdf)
- [Ken French size portfolios](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_ME_CSV.zip)
- [Carrion 2024](https://onlinelibrary.wiley.com/doi/10.1111/jfir.12384)
- [Martineau](https://cfr.ivo-welch.org/forthcoming/papers/martineau2021rest.pdf)
- [INSEAD working paper](https://flora.insead.edu/fichiersti_wp/inseadwp2013/2013-120.pdf)
- [Lou, Polk and Skouras](https://researchonline.lse.ac.uk/id/eprint/87481/7/Polk_Tug%20of%20War.pdf)
- [Yahoo SPY daily data](https://query1.finance.yahoo.com/v8/finance/chart/SPY?interval=1d&period1=1230768000&period2=1800000000)
- [Yahoo IWM daily data](https://query1.finance.yahoo.com/v8/finance/chart/IWM?interval=1d&period1=1230768000&period2=1800000000)
- [Yahoo QQQ daily data](https://query1.finance.yahoo.com/v8/finance/chart/QQQ?interval=1d&period1=1230768000&period2=1800000000)
- [ETF Strategy](https://www.etfstrategy.com/night-effect-etfs-to-close-10339/)
- [NightShares 497 filing](https://www.sec.gov/Archives/edgar/data/1199046/000158064223004244/nightshares500_497.htm)
- [Kurov, Wolfe and Gilbert, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/)
- [Aalto thesis](https://aaltodoc.aalto.fi/server/api/core/bitstreams/27ca8cf2-8edd-4ac5-b81f-20b11032661a/content)
- [Etula et al. slides](https://www.aalto.fi/sites/default/files/2021-03/dash4cashpresentation_bi_r.pdf)
- [Frazzini, Israel and Moskowitz](https://www.hbs.edu/faculty/Shared%20Documents/events/328/TradingCostEfficiency_FULL_112912.pdf)
- [Coinbase BTC-USD hourly candles](https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=3600)
- [Baur, Cahill, Godfrey and Liu 2019](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3088472)
- [Lim, SSRN 6592830](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6592830)
- [Blockchain Capital](https://blockchaincapital.com/blog/the-tomb-we-built)
- [TrueHold](https://www.truehold.xyz/unlocks/price-impact)
- [Cointelegraph](https://cointelegraph.com/news/usdc-depegs-as-circle-confirms-3-3b-stuck-with-silicon-valley-bank)
- [Circle press release](https://www.circle.com/pressroom/3-3-billion-of-usdc-reserve-risk-removed-dollar-de-peg-closes)
- [NBER w31160](https://www.nber.org/papers/w31160)
- [Mourey et al.](https://hal.science/hal-05415054v1/file/A%20crypto-stock%20weekend%20effect.%20Predicting%20Monday%20stock%20returns%20using%20weekend%20cryptocurrency%20returns.pdf)
- [Treasury daily bill rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&field_tdr_date_value_month=202611)
