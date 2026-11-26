# Idea Round 53: Untested Forced and Scheduled Flows

Written: 2026-11-26 20:46 UTC.
Scope: forced or scheduled flows by participants who must trade for a reason other than price, checked for novelty against `docs/QUEUE.md` (all sections), `research_rig/TRIAL_LEDGER.md`, and `docs/research/95_where_we_stand_after_32_tests.md`, evaluated for a $500 US retail account (stocks long-only under $2,000; coins US spot at about 75 bp per side, or 150 bp round trip) under Doc 117's power screen (`N_eff * (net_edge / paired_noise)^2 >= 4` for 50% power, `>= 8` for 80% power).
No price data was opened and no return calculation was run in this round.

## Repo overlap audit of requested candidate families

Most candidate families in the Round 53 brief are already tested, blocked on licensing, or dropped in `docs/QUEUE.md` and `docs/research/95_where_we_stand_after_32_tests.md`. They are listed here with exact repo references and not repeated:
- Leveraged and inverse ETF close rebalancing on large-move days: already dropped in Round 19 (`docs/QUEUE.md` skip list), Round 9 (`docs/QUEUE.md` dropped list), Round 34 (`docs/QUEUE.md` skip list: US crypto LETFs `BITX`, `BITU`, `MSTU`, `MSTX`, `CONL`, Woo Aug 2026 null, screen 0), and Round 36 (`docs/QUEUE.md` skip list: single-stock and VIX or sector LETFs, Lenkey 2024 QFE no profitable strategy; Vidovich and Zerjal Nov 2026 -3.5 bps, t = -1.3, screen 0).
- Closed-end fund rights offerings: already dropped in Round 25 (`docs/QUEUE.md` skip list), Round 27 (`docs/QUEUE.md` dropped list: 343 transferable and 97 non-transferable filings; Khorana, Wahal and Zenner 2002 premium-to-discount slide requires shorting; Brigham LSU dissertation post-expiry rebound is very weak), and Round 39 (`docs/QUEUE.md` skip list, screen 0). Only CEF at-the-market (ATM) equity issuance is new and evaluated below.
- Crypto index products (`CoinDesk 20`, `Bitwise 10` / `BITW`, `Grayscale` / `GDLC`): already dropped in Round 27 (`docs/QUEUE.md` dropped list: `GDLC` ~20 quarters < 30; `BITW` 14 8-K filings with >90% BTC and ETH) and Round 28 (`docs/QUEUE.md` skip list: `CD20` launched Jan 2024, 11 to 12 quarters < 30; `NCI` and `COIN50` dropped).
- MSCI quarterly reviews: already dropped in Round 9 (`docs/QUEUE.md` dropped list: MSCI quarterly additions, Colombian result starts before announcement) and Round 27 (`docs/QUEUE.md` dropped list: MSCI Small Cap requires paid licensed data).
- Nasdaq-100 annual reconstitution: already dropped or blocked in Round 24 (`docs/QUEUE.md` skip list: addition effect shrank to 2.0% including pre-announcement days, many names trade above $250 to $600), Round 27 (`docs/QUEUE.md` dropped list: 10 annual dates < 30), and Row 87 (`docs/QUEUE.md` Next list: Nasdaq Legal Section 11 prohibits storing archives, archives return HTTP 403).
- ARK's daily published trades: already dropped in `docs/QUEUE.md` dropped list (`docs/research/50_public_filers_evidence_checked.md`).
- Priced overnight follow-ons (SEOs), IPO lock-up expiries, and convertible-note hedging: all three already dropped. Overnight SEOs are closed in Row 59 (Plan 42) and Round 32 (`docs/QUEUE.md` skip list: Gustafson 2018 JFQA, Row 59 negative post-SEO returns, screen 0.00). IPO lock-up expiries were dropped in Rounds 16, 32, and 41 (`docs/QUEUE.md` skip list: Bradley et al. 2001 -2% permanent decline with no rebound, short-only, screen 0.00). Convertible-note hedging was dropped in Round 41 (`docs/QUEUE.md` skip list: 924 deals 2016 to 2024, overnight short-only drop, post-Lehman rebound flipped to -339 bp, capped-call overlays on 48.7%, Doc 117 2.39 < 4).
- Dividend capture around ADR or special situations: skipped as instructed (`Replay 60` and `Replay 62` did not pass).
- Crypto staking unlock queues, spot ETF creation and redemption flows, exchange delisting notices, and stablecoin mint and burn announcements: all four already covered or dropped. Staking unlock queues were dropped in Rounds 23, 26, and 28 (`docs/QUEUE.md`: 5 to 7 US-spot PoS coins, no directional return evidence). Spot BTC and ETH ETF creation and redemption flows were dropped in Rounds 28, 33, and 35 (`docs/QUEUE.md`: Ashish 2026 p = 0.325 to 0.965, Fabus et al. SSRN 7545019 null after public, screen 0.00). Exchange delisting notices are already tracked as defensive exit harness rules (Rows 72, 79, and 84 live watcher) and dropped as short or profit trials in Round 24 (0 full spot delistings on 29 US-shortable coins 2024 to 2026) and Round 28 (Coinbase and Kraken non-USD removals median +0.1% 24h). Stablecoin mint and burn flows were dropped in `docs/QUEUE.md` dropped list and Round 30 (NY Fed 2025 inflows follow BTC jumps, no free CEX labels, negative net of US spot fees, screen 0).
- Previously tested or dropped month-end, quarter-end, and options-expiry flows: `TLT` month-end (Replay 25 pass), `LQD`/`HYG`/`MBB`/`TIP` month-end (Replay 31 fail), corporate bond quarter-end (Replay 52 fail), `SPY`/`TLT` month-end switch (Replay 41 fail), `MUB`/`VTEB` month-end (Row 69 closed on power), `SPY`/`QQQ`/`IWM`/`TLT` turn-of-month and OpEx (Rounds 19, 36, 37, 46; 0 of 24 US ETF calendar rules promoted OOS in arXiv:2611.03384v1), `VIX` SOQ settlement morning (Round 20), `SPY` vs `EFA`/`VXUS` quarter-end (Round 36), and `IBIT` monthly CME expiry (Replay 35 fail).

## Ranked evaluation of new and time-critical forced-flow candidates

Six candidates were evaluated in full: the time-critical re-examination of held Row 66 (individual small-stock year-end tax-loss selling), two untested slices from the brief (CEF ATM issuance and crypto quarterly futures roll), and three fresh additions not in `docs/QUEUE.md` (sector ETF intramonth momentum cycle, `SVXY` on the day before monthly VIX expiration, and monthly commodity ETF roll front-running and curve switching). None clears Doc 117 for a historical count or replay stage. Only Rank 1 warrants consideration as a zero-cost December 2026 forward watch card (pretend money only, not a tested edge).

### Rank 1 (Time-critical re-examination of held Row 66): Year-end tax-loss selling rebound in individual beaten-down US small stocks

Repo status: ALREADY HELD as `Queue 66` (`Plan 40`, `docs/research/79_round_13_known_clock_premia.md`: "Held 2026-11-26: no point-in-time list of small common shares for each December, costs of small losers UNKNOWN, ten turns only; reopen if a lawful free point-in-time universe is found"). Re-examined here specifically because the December 2026 window opens in about three weeks and a live forward practice card does not require a historical point-in-time universe.

Who is forced, why, and when:
- STATED ([Alpha Strategic Growth, Sep 2026](https://www.alphastrategicgrowth.com/blog/january-effect/)): "Individuals sell losers in December to realize losses against gains, which pushes beaten-down names below fair value; the selling pressure stops abruptly in January and the names rebound." US taxable investors face a hard December 31 trade-date deadline to realize 2026 capital losses and a 30-day IRS wash-sale restriction preventing immediate repurchase ([EquityCompass, Oct 2022](https://www.equitycompass.com/content/Insights/content/mccann_tax_loss_selling_oct2022.pdf): "Repurchasing the shares, or 'substantially similar' securities, before the 30-day period—known as the 'wash sale' rule—could disallow the loss.").

Exact rule supported by the literature:
- STATED ([Alpha Strategic Growth, Sep 2026](https://www.alphastrategicgrowth.com/blog/january-effect/)): universe of US common stocks with market capitalization above $300 million and price above $5 at November 30 (to exclude microcap bid-ask bounce), selection of names down 30% or more from January 1 to November 30, equal-weight entry at the close of December 31 (with sensitivity checks on December 15 and December 20), exit at the close of January 15, judged against the equal-weight universe (or IWM) over the same window.
- STATED alternative screen ([EquityCompass, Oct 2022](https://www.equitycompass.com/content/Insights/content/mccann_tax_loss_selling_oct2022.pdf)): Russell 3000 stocks down more than 50% through October 31, held from End December to Mid January.

Stated numbers, sample, years, costs, and newest evidence:
- STATED ([EquityCompass, Oct 2022](https://www.equitycompass.com/content/Insights/content/mccann_tax_loss_selling_oct2022.pdf)): across 5,514 unique US stocks (40,521 observations, 2003 to 2021), stocks down more than 50% through October 31 averaged +5.6% from End December to Mid January (+3.5% excluding 2020), raw before costs and before benchmark subtraction. Recent years in Table 2 were highly volatile: 2015 -19.5%, 2016 +11.3%, 2017 +8.5%, 2018 +25.2%, 2019 +9.6%, 2020 +16.1%, 2021 -9.5%. "During the 19-year time period analyzed, the strongest performing segment from mid-December through mid-January were those stocks that had previously performed the worst through the end of October."
- STATED survivorship-free S&P 500 benchmark ([Xfinlink, Nov 2026](https://xfinlink.com/blog/january-effect-survivorship-bias-python)): "On point-in-time S&P 500 rosters, the fifth of members with the worst calendar-year return beat the best fifth by 2.22 percentage points in the average January of 2000-2024, against -0.09 points in the other months." "The January figure has a t-statistic of 1.46, and 2001 supplies most of it." "Without 2001 the January average drops to 0.98 points, and the median January is 0.42." Crucially, in the recent half (2013 to 2024), the January losers-minus-winners spread fell to +0.66% gross (and 14 of 25 Januaries positive overall). Using today's survivor roster omits 51.2% of point-in-time December losers and inflates January loser returns from +1.85% to +2.43%.
- STATED recent small-cap after-cost reality ([Alpha Strategic Growth, Sep 2026](https://www.alphastrategicgrowth.com/blog/january-effect/)): a 50-name small-cap basket pays about 40 basis points round-trip in spread and impact, cutting a hypothetical +1.8% excess return to +1.4% with 6% year-to-year standard deviation (t = 1.5 over 25 years; needs about 44 years to reach t = 2). "December does not cause the bounce; December selling of a large loser cohort does."
- STATED unconditional small-cap index ([PapersWithBacktest, Nov 2026](https://paperswithbacktest.com/strategies/january-effect)): Russell 2000 minus S&P 500 in January averaged -0.05% (1988 to 2025) and -0.43% (2010 to 2025), while December averaged +0.97%.
- STATED 2021 to 2024 check ([chungderson, Nov 2026](https://github.com/chungderson/loss-harvesting-and-january-effect)): prior-year return negatively predicted January returns (`Beta = -0.0148, p < 0.01`), "massive in Jan 2023 (after the 2022 bear market) but non-existent in Jan 2024."

Data needed, event count, Doc 117 power statement, $500 fit, and how it could fool us:
- Data: historical backtesting remains blocked (no free point-in-time 2016 to 2025 small-cap roster without survivorship bias). A live December 2026 forward watch needs only a frozen November 30, 2026 screen of US common stocks (`> $300M` market cap, `> $5` price, down `>= 30%` YTD) plus Alpaca SIP closes on December 31, 2026 and January 15, 2027.
- Event count: 1 independent turn per year (10 historical turns 2016 to 2025).
- Doc 117 power statement: at 10 annual turns, even an optimistic +2.5% net excess return over IWM with 8% annual basket-spread noise gives `10 * (0.025 / 0.08)^2 = 0.98`, far below 4 (50% power requires 41 years). At Alpha Strategic Growth's +1.4% net and 6% SD, `10 * (0.014 / 0.06)^2 = 0.54 < 4`. Cannot reach power historically or in any short forward test.
- $500 US account fit: YES (long-only; e.g., 5 equal-weight $100 fractional positions in `$5+` stocks on Alpaca, though 5 single names carry much higher idiosyncratic noise than a 50-name basket).
- How it could fool us: survivorship bias in unverified screens (Xfinlink shows 51.2% of losers later leave the index); bid-ask bounce in low-priced stocks; regime dependence (weak or absent after strong equity years like 2023/2024 when the loser cohort is small); single-stock bankruptcy or dilution risk inside a 5-name $500 basket; and 1 forward turn cannot separate edge from a general January risk-on rally.
- Plain recommendation: do NOT reopen Row 66 for a historical count or replay stage (fails Doc 117 at 0.54 to 0.98 < 4 and lacks a free point-in-time 2016 to 2025 universe). ONLY if the owner wants a zero-cost live log alongside E04 and E08, open a pretend-money forward watch card for December 31, 2026 to January 15, 2027 using the exact `$300M+`, `$5+`, down `>= 30%` Nov 30 rule, labeled explicitly as an untested watch, not a trading edge.

### Rank 2 (Added family): US Sector ETF Intramonth Momentum Cycle (Day +1 momentum, Days +2 to +3 reversal)

Who is forced, why, and when:
- Institutional monthly inflows (401(k), payroll, pension allocations, and automated model-portfolio rebalances) concentrated on the first trading day of the month (`D+1`) push trailing 12-month winning sector ETFs higher, followed by mean-reversion on `D+2` and `D+3` once the monthly inflow subsides.

Exact rule as stated:
- STATED ([QuantPedia, Aug 2026](https://quantpedia.com/sectoral-intramonth-momentum-cycle/)): "Sector momentum 'works' on the first day of the month, reverses sharply on days two and three, and then reasserts itself in the window stretching from ten to five trading days before month-end." At each month-end close, rank the 9 Select Sector SPDR ETFs (`XLB`, `XLE`, `XLF`, `XLI`, `XLK`, `XLP`, `XLU`, `XLV`, `XLY`) by trailing 252-trading-day total return; hold top 3 on `D+1` and reverse (bottom 3 in a long-only adaptation) on `D+2` through `D+3`, hedged against `SPY` (`Strat1-SPY`) or bottom 3 (`Strat2`).

Stated numbers, sample, years, costs, and newest evidence:
- STATED ([QuantPedia, Aug 2026](https://quantpedia.com/sectoral-intramonth-momentum-cycle/)): sample December 22, 1998 through June 30, 2026 (~330 months). `Strat2` (long top 3, short bottom 3) earned 2.83% annualized (Sharpe 0.42) on `D+1`, 3.26% annualized (Sharpe 0.46) reversed on `D+2` to `D+3`, and 5.99% composite (Sharpe 0.55, max drawdown -21.72%). However, `Strat1-SPY` (long top 3 vs short `SPY`) earned only 0.23% annualized (Sharpe 0.15) on `D+1` and 0.69% annualized (Sharpe 0.31) reversed on `D+2` to `D+3`. Exact t-statistics, transaction costs, and a post-2015 subsample split are UNKNOWN (not reported).

Data needed, event count, Doc 117 power statement, $500 fit, and how it could fool us:
- Data: already held (Alpaca SIP daily bars 2016 to 2026 for all 9 SPDRs and `SPY`).
- Event count: 12 monthly cycles per year (120 turns from 2016 to 2025).
- Doc 117 power statement: a long-only $500 account cannot short the bottom 3 sectors (`Strat2`). Against `SPY`, `D+1` is only 0.23% per year (about 1.9 bp per month gross, zero or negative after 2 to 4 bp ETF round-trip spreads), giving power 0. Even the unreachable long-short `Strat2` reversed leg (3.26% per year = 27 bp per month gross, 23 bp net, 7.13% annual vol = 206 bp monthly SD) over 120 months gives `120 * (0.0023 / 0.0206)^2 = 1.50 < 4`.
- $500 US account fit: long-only leg only (weakest arm); short leg unreachable.
- How it could fool us: data-mined intramonth day boundaries (`D-10` to `D-5`, `D+1`, `D+2` to `D+3`) with no post-2015 split and no reported t-stats; short leg drives nearly all of the return.
- Plain recommendation: DROP (fails Doc 117 at 0 to 1.50 < 4 and lacks post-2015 evidence).

### Rank 3 (Added family, distinct from Round 20's VIX SOQ settlement): Long `SVXY` on the day before monthly VIX options expiration (`OE-1`)

Who is forced, why, and when:
- VIX options and futures hedgers and dealers unwinding or rolling expiring front-month VIX contracts on `OE-1` (the last full trading day, usually Tuesday, before Wednesday morning monthly VIX SOQ settlement, 30 days prior to the next month's third Friday SPX OpEx).

Exact rule as stated:
- STATED ([CXO Advisory, Jul 2015](https://www.cxoadvisory.com/calendar-effects/vix-calendar-effects/)): hold short VIX futures exposure (long `SVXY`, -0.5x short-term VIX futures, in a $500 long-only account) over `OE-1` (close of `OE-2` to close of `OE-1`, or `OE-1` open to close), 12 monthly dates per year.

Stated numbers, sample, years, costs, and newest evidence:
- STATED ([CXO Advisory, Jul 2015](https://www.cxoadvisory.com/calendar-effects/vix-calendar-effects/)): across 77 monthly `OE-1` dates for `VXX` (February 2009 through early July 2015), "Results indicate that changes in VIX and VXX are abnormally negative for OE-1." "For VXX close-to-close (open-to-close), 56 (57) of 77 OE-1 returns are negative; however, there are 4 (2) positive returns of at least 5%." "VXX return calculations are gross. Trading frictions diminish any exploitability."
- Post-2015 evidence: exact `OE-1` mean return and post-2015 performance are UNKNOWN (no 2016 to 2026 study found). Weekly VIX options launched October 8, 2015, diluting monthly expiration concentration, and extreme VIX spikes (February 5, 2018 Volmageddon; August 5, 2024 spike to 65.73) forced `SVXY` to cut leverage from -1x to -0.5x.

Data needed, event count, Doc 117 power statement, $500 fit, and how it could fool us:
- Data: free CBOE VIX expiration calendar rule plus Alpaca SIP bars for `SVXY` (held).
- Event count: 12 monthly dates per year (120 events 2016 to 2025).
- Doc 117 power statement: exact post-2015 mean is UNKNOWN; at `SVXY` daily SD of roughly 2.5% to 3.5%, clearing 4 on 120 dates requires +46 to +64 bp net per single `OE-1` day (+5.5% to +7.7% per year from 12 days), unverified post-2015.
- $500 US account fit: YES (`SVXY` trades long-only under $100 per share).
- How it could fool us: one Volmageddon-style VIX spike on an `OE-1` Tuesday can wipe out years of small gains; weekly VIX options since Oct 2015 may have eliminated the monthly `OE-1` drop.
- Plain recommendation: DROP (no post-2015 quantitative evidence and severe single-day tail risk).

### Rank 4 (Added family, distinct from Round 24's annual January BCOM/GSCI rebalance): Monthly commodity ETF (`USO`, `UNG`) roll front-running and curve switching

Who is forced, why, and when:
- Front-month commodity futures ETFs (`USO` for WTI crude, `UNG` for natural gas) must mechanically roll expiring front-month NYMEX futures every month on a published schedule.

Exact rule as stated:
- STATED early-roll rule ([qrlow.me, Aug 2026](https://qrlow.me/blog/oil-etf/)): roll WTI futures 1 to 4 trading days ahead of `USO`'s published monthly roll schedule.
- STATED ETF switching rule ([Gaurav Gupta, Nov 2026](https://guptagaurav.info/articles/commodity-roll-cost)): "At each month-end, hold the front-month fund next month if its realised roll over the previous one, three or six months was positive; otherwise hold the strip" (`USO` vs `USL`, `UNG` vs `UNL`).

Stated numbers, sample, years, costs, and newest evidence:
- STATED ([qrlow.me, Aug 2026](https://qrlow.me/blog/oil-etf/)): "January 2011 - April 2020: a four-day roll beginning two calendar weeks before the nearest contract's last trading day." "Before 2020, every early-roll strategy beat the published roll. The strongest result came from moving the schedule three days earlier, which added 4.89% of compounded relative wealth over almost nine years." However, from "May 2020 - December 2025: a ten-trading-day roll beginning on the first trading day of each month" was adopted, and "it seems like the edge has eroded since..." (exact post-2020 figures not given; assumes zero commissions or slippage at settlement).
- STATED ([Gaurav Gupta, Nov 2026](https://guptagaurav.info/articles/commodity-roll-cost)): 2008 to Oct 2026 on `USO`/`USL` and `UNG`/`UNL`: "After a positive three-month roll, the front month still trailed the strip the following month by 0.49% on average." "The pre-specified switching rule trailed the strip at every lookback."

Data needed, event count, Doc 117 power statement, $500 fit, and how it could fool us:
- Data: NYMEX futures curve required for early-roll (not held, unreachable on $500); ETF bars held for switching.
- Event count: 12 monthly rolls per year (120 events 2016 to 2025).
- Doc 117 power statement: negative net edge (-49 bp per month for ETF switching; eroded post-2020 for futures early-roll) gives power 0.
- $500 US account fit: futures early-roll NO; ETF switching YES but loses money.
- How it could fool us: `USO` changed its roll schedule in May 2020 (and again in 2023 to 2024), breaking pre-2020 roll-window patterns.
- Plain recommendation: DROP.

### Rank 5 (Untested slice from brief): Closed-end fund at-the-market (ATM) equity issuance

Who is forced, why, and when:
- Nobody is forced to buy. Under Section 23(b) of the Investment Company Act of 1940, a CEF may issue ATM shares only at a premium to NAV, dribbled into normal exchange volume at the manager's discretion ([BlackRock CEF ATM](https://www.blackrock.com/us/individual/literature/investor-education/cef-at-the-market.pdf): "In no event will a fund issue shares at a price below the fund's NAV per common share plus any sales commission charged in connection with the ATM Offering.").

Exact rule, stated numbers, data, power, and $500 fit:
- STATED ([BlackRock CEF ATM](https://www.blackrock.com/us/individual/literature/investor-education/cef-at-the-market.pdf)): "the issuance of additional common shares may also have an adverse effect on prices in the secondary market for the fund's common shares by increasing the supply of common shares available for sale."
- STATED ([Cohen and Steers, 2012](https://forums.capitallink.com/cef/2012/pres/cohen.pdf)): "Minimal market impact – 42% of filers posted positive 2-day performance" (17 CEF ATM filings in 2011 to 2012). Post-2015 CEF ATM long-only return is UNKNOWN (no positive study found).
- Data and timing blocker: SEC 424B5 shelf filings authorize an ATM program without disclosing the exact future days on which shares are sold, and no free daily CEF NAV/premium archive exists (Round 42).
- Doc 117 power statement: wrong sign for a long-only $500 account (incremental share supply depresses premiums) and no dated execution clock; power = 0.
- Plain recommendation: DROP.

### Rank 6 (Untested slice from brief): Crypto quarterly delivery futures roll

Who is forced, why, and when:
- Traders holding quarterly delivery BTC and ETH futures (Deribit, Binance, CME) must roll or settle on the last Friday of March, June, September, and December (4 dates per year).

Exact rule, stated numbers, data, power, and $500 fit:
- STATED ([Blasco, Corredor and Satrustegui, 2023](https://zaguan.unizar.es/record/125822/files/texto_completo.pdf)): while intraday CME monthly expiration effects appeared in earlier samples (which already failed on `IBIT` in Replay 35 at -0.1626%, t = -0.72), "Finally, other expiration dates such as quarterly expiration dates in Binance are assumed not to cause the monthly reactions detected."
- STATED ([TDZNBEER, Nov 2026](https://github.com/TDZNBEER/crypto-backtest-lab/blob/main/BASIS_FINDINGS.md)): across 2,622 daily observations of Deribit BTC quarterly futures basis from December 31, 2018 through August 2, 2026 (32 quarters), "None of the three basis-timing directions beats simple buy-and-hold on total return".
- STATED ([BSIC, Nov 2025](https://bsic.it/carry-trading-dynamics-in-cryptocurrency-markets/)): mean annualized quarterly delivery carry (2021 to Oct 2025) was 8.68% for BTC and 8.18% for ETH, which requires shorting quarterly futures against spot (unreachable on $500 US spot at 150 bp round trip).
- Event count and Doc 117 power statement: only 4 quarterly dates per year (28 to 32 quarters since 2019) and no positive long-only spot edge after 150 bp US spot round-trip fees; power = 0.
- Plain recommendation: DROP.
