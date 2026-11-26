# Round 42: High-count long-only closed-end fund rules

Written: 2026-11-26 12:19 UTC. No market prices were opened and no returns were computed.

## Summary and decision

STATED. This round screens high-count, long-only US closed-end fund (CEF) rules outside items already in `docs/QUEUE.md` (rows 48, 53, 55, 63, 64, 70, 102, 104, and Done). Every candidate must clear two gates: (a) at least 300 dated events or 300 fund-weeks per year from lawful free sources without shorting, and (b) a post-2010 published net-of-spread edge at a tradable print that clears the [Doc 117 power screen](research/117_power_screen_before_data.md) (`events * (net edge / noise)^2 >= 4`).

STATED. Zero new rows are queued (rows from 110 stay unused). None of the five prompted areas clears both the lawful-data / tradable-net-edge bar and the Doc 117 screen once US CEF bid-ask spreads (`16 to 265+ bp` full spread in 2025 primary filings) and post-2009 discount persistence are applied.

| Area | Candidate | Lawful free inputs | Post-2010 published net edge | First count | Doc 117 screen | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Peer-relative short-term reversal (5 to 20 sessions, price-only) | SIP bars only (no NAV) | None positive; Durmaz et al. 2025 say short-horizon reversals unlikely; equity weekly reversal negative net | ~20,800 fund-weeks/yr | `0.00 < 4` | DROP |
| 2 | Discount z-score mean reversion (plus NAV source audit) | None timely (N-PORT 60d lag; N-CSR 70d; MFQS paid; CEFConnect/CEFData forbid automated archive) | Pre-2012 gross only (Patro et al. 2014); Durmaz et al. 2025 show post-2009 persistence (8.10 mo median half-life) | 0 lawful free daily NAV series | `0.00` to `0.83 < 4` | DROP |
| 3 | Distribution cut announcements (overshoot and rebound) | Rule 19a-1 not filed on EDGAR; press releases on paid wires | Opposite sign: `-190 bp` further discount widening from Day +1 to Day +90 (CEFA 2024, `n = 1,075`) | ~86 cuts >10%/yr (~860/10yr, off-EDGAR) | `0.00 < 4` | DROP |
| 4 | Same-sponsor sibling-fund pairs (long-only switching) | No lawful free daily NAV; structural mandate/leverage gaps | Zero published post-2010 backtest; double CEF spread cost (`32 to 100+ bp` per switch) | ~30 to 50 pairs (~1,500 to 2,500 pair-weeks/yr) | `0.00 < 4` | DROP |
| 5a | CEF insider / director open-market purchases (SEC Form 4) | Free dated SEC Form 4 under Section 30(h) | UK 1999 to 2008 `+49.7 bp` `[+2,+15]` gross, authors call unexploitable after spreads; US CEF study finds no timing ability | ~500+ non-overlapping / 10yr (overlaps Row 102) | `1.21 < 4` | DROP |
| 5b | CEF open-market share repurchase announcements (SRP) | No standardized real-time EDGAR form | Kim, Kim, and Song (2013): SRP announcements do not significantly reduce discounts | ~100 to 250 / 10yr (`< 300`) | `0.00 < 4` | DROP |

## Closed-end fund trading cost baseline

MEASURED in our own [Doc 136](research/136_measured_stock_trading_costs.md): across 56 sampled stocks and ETFs (June to November 2026), the pooled regular-hours median quoted half-spread was `1.126 bp` (`2.422 bp` first 30 min, `0.843 bp` last 30 min; `0.210 bp` broad equity ETFs, `0.610 bp` `TLT`, `1.668 bp` single stocks). Closed-end funds are explicitly `UNKNOWN` in Doc 136 (`Closed-end funds (none in roster)`). Replay 48 (muni CEFs) and Replay 53 (taxable CEFs) charged own closing half-spread plus `5 bp` per side (`50 bp` floor for missing exits).

MEASURED from primary 2025 US CEF filings and academic benchmarks, CEF spreads are roughly `7x to 25x` wider than Doc 136 large stocks and ETFs:

- STATED in Nuveen's [SEC Form 425 filing (January 23, 2026, data as of July 31, 2025)](https://www.sec.gov/Archives/edgar/data/1266585/000199937126001517/nxj-425_012325.htm): 6-month average full bid-ask spreads for four NYSE-listed municipal CEFs were `15.63 bps` (`NMZ`, ~`7.8 bp`/side), `21.16 bps` (`NXJ`, ~`10.6 bp`/side), `28.37 bps` (`NQP`, ~`14.2 bp`/side), and `265.44 bps` (`NOM`, ~`132.7 bp`/side). The filing states: "NXJ, NQP, and NOM common shareholders through the merger into NMZ should experience significant bid/ask spread improvement as well as materially greater liquidity."
- STATED in Cherkes, Sagi, and Stanton (RFS 2009; [working paper](http://faculty.haas.berkeley.edu/stanton/pdf/CEF.pdf), Table 2 Panel c, printed p. 6 and p. 8, 1993 to 2004 TAQ subsample): mean one-way trading cost across all US CEFs was `0.49%` (`49 bp` one-way, `98 bp` round-trip), split by sector as `0.40%` Muni, `0.54%` Taxable FI, `0.51%` Domestic Equity, `0.68%` Foreign Equity, and `0.52%` Other. Quote (p. 8): "Across fund types, one-way trading costs average under half a percent, and the number of trades per day is comparable to that of mid and small capitalization stocks on the NYSE (see Chordia et al., 2005)."
- STATED in Andriosopoulos, Steliaros, and Thomas (2014, [European Journal of Finance](https://strathprints.strath.ac.uk/47338/1/Directors_Purchases_EJoF_.pdf), Table VII, printed p. 27): UK CEF quoted bid-ask spreads averaged `2.16%` (`1.23%` large funds, `2.52%` small funds).

STATED. For Doc 117 screening on a `$500` US cash account, modern round-trip taker crossing costs are `16 to 30 bp` on the largest liquid CEFs and `40 to 100+ bp` across the broader ~400-fund roster.

## Candidate 1: Peer-relative short-term reversal (5 to 20 sessions, price-only)

STATED. Hypothesis: buy a US CEF that fell over `N` days relative to its category (muni, taxable bond, equity, or sponsor siblings) using SIP price bars only, and hold 5 to 20 sessions with no short leg.

Published size after 2010 and later samples:

- STATED. No post-2010 academic study documents a positive, net-of-spread, long-only 5-to-20-day price-only peer-relative reversal strategy in US CEFs.
- STATED in Anderson, Beard, Kim, and Stern (2012, [Auburn WP 2012-03](https://cla.auburn.edu/econwp/Archives/2012/2012-03.pdf), 16 bond CEFs and 16 equity CEFs, daily 2004 to 2011, Tables IV and V pp. 34 to 35, Table VIII p. 37): short-run equity CEF prices behave like random walks, while bond CEF predictability comes from stale NAVs lagging prices, not from prices snapping back. Quote (p. 4): "In particular, our approach allows us to show that both price and NAV series for equity funds essentially behave like random walks, but bond fund series are more predictable." Quote (p. 17 to 18): "Therefore, we conclude that in the post-crisis period, bond fund share prices 'cause' NAVs of bond funds, but the converse is not true."
- STATED in Durmaz, Kim, Lee, and Sun (May 2025, [Auburn WP 2025-02](https://cla.auburn.edu/econwp/Archives/2025/2025-02.pdf), published 2026 in Studies in Nonlinear Dynamics and Econometrics, 31 US CEFs, 1999 to 2018 plus post-crisis July 2009 to December 2019 in footnote 22 p. 17, Table 3 p. 30): deviations from NAV have a median half-life of `8.10 months` and mean half-life of `13.70 months`. Quote (p. 18): "Price reversals are unlikely to occur within short investment horizons."
- STATED in De Groot, Huij, and Zhou (2011, [Erasmus University](https://repub.eur.nl/pub/25718/AnotherLook_2011.pdf), Section 5.1, printed p. 20): even in the 1,500 largest US stocks (much tighter spreads than CEFs, with both long and short legs), a 5-day weekly reversal yields `41.2 bp/week` gross and negative net returns. Quote (p. 20): "Nonetheless, the net returns of the weekly reversal strategy for the 1,500 largest stocks are significantly negative because the gross returns of the strategy are also much lower than for the daily strategy."

Count, spread costs, Doc 117 screen, and failure modes:

- STATED. First count: ~400 US CEFs across 52 weeks gives ~`20,800` fund-weeks per year (well above 300), though clustered by category rate/equity moves.
- STATED. Spread cost: `20 to 50+ bp` round-trip in liquid to mid-tier CEFs (`15.63 to 265.44 bp` full spread in Nuveen 2025 Form 425).
- STATED. Doc 117 screen: event count ~`500` weekly turns (10 years), published net edge `<= 0 bp` (no positive post-2010 CEF result; negative net after spreads), noise guess `250 to 350 bp` per 5-to-20-day peer-relative trade -> `500 * (0 / 300)^2 = 0.00 < 4`.
- STATED. How it could fool us: bid-ask bounce on thin CEFs creates artificial 1-to-5-day close-to-close reversal that disappears on bid/ask fills; leveraged CEFs (30% to 40% leverage) fall harder than unlevered category peers during rate selloffs so buying losers adds leverage beta rather than mispricing; category-wide rate shocks collapse independent event count; merged and liquidated funds create survivorship bias on live rosters.
- STATED. Verdict: DROP.

## Candidate 2: Discount z-score mean reversion and lawful free NAV audit

STATED. Hypothesis: buy CEFs when their discount-to-NAV z-score is unusually wide and hold until mean reversion, without shorting.

Audit of lawful free dated NAV sources:

- STATED. SEC Form N-PORT: under the active 2019 interim final rule ([SEC Release IC-33384](https://www.sec.gov/file/ic-33384)), only the third month of each fiscal quarter becomes public, 60 days after quarter-end. Quote: "The monthly report on Form N-PORT for the third month of the quarter (the 'quarter-end report') will continue to become publicly available [...] not later than 60 days after the end of that fiscal quarter." The August 2024 monthly-public amendments ([SEC Release IC-35308](https://www.sec.gov/files/rules/final/2024/ic-35308.pdf), still a 60-day lag) were delayed in 2025 ([SEC Release IC-35538](https://www.sec.gov/files/rules/final/2025/ic-35538.pdf)) to November 17, 2027 ("delaying the effective date for the amendments to Form N-PORT that were published on September 11, 2024, from November 17, 2025, to November 17, 2027"), and in 2026 the SEC proposed reverting public disclosure back to quarterly ([SEC Press Release 2026-19](https://www.sec.gov/newsroom/press-releases/2026-19-sec-proposes-amendments-reduce-burdens-reporting-fund-portfolio-holdings): "Reduce the publication of reports from monthly to quarterly"). A 60-day quarterly lag cannot power a short-horizon z-score rule.
- STATED. SEC Form N-CSR and N-CSRS: semi-annual only, filed up to 70 days after period end ([SEC ADI 2024-13](https://www.sec.gov/about/divisions-offices/division-investment-management/accounting-disclosure-information/short-form-registration): "Thus, registrants generally have 70 days to file Form N-CSR after the end of a reporting period.").
- STATED. Exchange NAV symbols (Nasdaq MFQS / Nasdaq Fund Network `X___X`): paid commercial data. The [Nasdaq MFQS User Guide](https://nasdaqtrader.com/content/TechnicalSupport/UserGuides/DataProducts/mfqsch1-5.pdf) states: "A monthly fee is charged." On Nasdaq Data Link ([NFN Mutual Fund Reports](https://data.nasdaq.com/databases/MFR)), the commercial pricing summary table (`NFN/MFRPS`) explicitly states: "This report provides data only for live securities and excludes closed-end funds."
- STATED. Fund press releases on EDGAR and free web portals: CEFs do not file daily NAVs on EDGAR. Free display portals prohibit automated extraction and database archiving: [CEFConnect Legal Terms](https://www.cefconnect.com/footer/legal.aspx) forbid users to "make use of any data mining, robots, or similar data gathering and extraction tools," and [CEFData Terms](https://cefdata.com/legal-page) forbid users to "store, download, archive, cache, aggregate, compile, index, maintain, import, export, or transfer CEFData Content into a spreadsheet, database, research system."
- STATED. Price-only proxy for discount: no post-2010 published study validates a price-only proxy (such as price return minus category ETF return) as a substitute for true NAV in a short-term long-only CEF z-score rule.

Published size after 2010 and later samples:

- STATED in Patro, Piccotti, and Wu (October 2014, [CUNY working paper](https://www.gc.cuny.edu/sites/default/files/2021-07/Exploiting-Closed-End-Fund-Discounts_CUNY-talk.pdf), 377 US CEFs, out-of-sample February 1998 to December 2011, Tables V and VI pp. 33 to 34, Table XII p. 40): monthly-rebalanced quintile portfolios using Morningstar/CRSP NAVs earned `+14.9%/yr` (`t = 5.667`) benchmark Q5-Q1 and `+18.2%/yr` (`t = 7.154`) parametric RADF Q5-Q1, with long-only Q5 minus `MRKT` at `+9.3%/yr` (benchmark) and `+10.7%/yr` (RADF). Quote (p. 12): "The full sample annualized mean arbitrage return of the benchmark strategy is 14.9 percent and is statistically significant at the 1 percent level." All returns are gross before bid-ask spreads, end in December 2011, and benchmark long Q5 against broad stocks (`MRKT`) rather than a CEF peer index.
- STATED in Durmaz, Kim, Lee, and Sun (May 2025, [Auburn WP 2025-02](https://cla.auburn.edu/econwp/Archives/2025/2025-02.pdf), Table 3 p. 30, footnote 22 p. 17): in post-crisis data (July 2009 to December 2019), discounts became MORE persistent with an `8.10`-month median half-life (`13.70`-month mean). Quote (p. 17): "In contrast, the post-crisis period shows fewer unit root rejections and a greater persistence in deviations from NAVs, with many structural breaks proving statistically insignificant."
- STATED in QuantifiedStrategies ([ETG single-fund discount RSI(2) backtest](https://www.quantifiedstrategies.com/closed-end-fund-strategy/)): buying `ETG` when 2-day RSI of discount/premium crosses below 10 and selling above 60 produced `207` trades averaging `+0.48%` gross and `4.8%` CAGR, underperforming buy-and-hold `6.8%` CAGR even before spreads.

Count, spread costs, Doc 117 screen, and failure modes:

- STATED. First count: `0` lawful free dated daily NAV records for 2016 to 2026 backtesting (monthly rebalancing across 2016 to 2026 would give `120` monthly turns if paid NAV data existed).
- STATED. Spread cost: `20 to 50+ bp` round-trip per switch, plus unmeasured cost of paid daily NAV data.
- STATED. Doc 117 screen: post-2009 net edge over a CEF peer index is `UNKNOWN` and likely `<= 0 bp` (`0.00 < 4`); even assuming a generous `+25 bp/mo` net edge over `120` monthly turns with `300 bp` monthly noise gives `120 * (25 / 300)^2 = 0.83 < 4`.
- STATED. How it could fool us: stale bond/illiquid NAVs (Anderson et al. 2012 Table VIII p. 37: bond fund share prices lead NAVs with `p = 0.000` while NAVs do not lead prices, `p = 0.298`) make a falling fund look artificially cheap; mapping N-PORT or N-CSR NAVs to period-end instead of filing date introduces 60-to-70-day look-ahead bias; structural trend breaks (Durmaz et al. 2025) turn wide discounts into multi-year value traps; leverage and survivorship distort historical z-scores.
- STATED. Verdict: DROP (remains on Round 34 skip list).

## Candidate 3: Distribution cut announcements (overshoot and rebound)

STATED. Hypothesis: buy a US CEF after a distribution cut announcement to capture an overreaction rebound, counting events from Rule 19(a) notices or press releases on EDGAR.

Filing and data-source check:

- STATED. SEC Rule 19a-1 notices are NOT filed on EDGAR in real time. Per the SEC's [Paperwork Reduction Act Supporting Statement for Rule 19a-1](https://www.reginfo.gov/public/do/DownloadDocument?objectID=52855601): "Rule 19a-1 does not require the filing of any documents with the Commission." Only funds operating under Section 19(b) Managed Distribution Plan exemptive orders attach past 19(a) notices as exhibits to their next semi-annual Form N-CSR up to 70 days after period end ([SEC Form 40-APP/A example](https://www.sec.gov/Archives/edgar/data/0000863900/000089418916008354/mxe_40-appa.htm): "will file with the Commission the information contained in such 19(a) Notice [...] as an exhibit to its next filed Form N-CSR"). Distribution cut press releases go out via commercial newswires (such as Business Wire) rather than mandatory Form 8-K filings.

Published size after 2010 and later samples:

- STATED. Empirical evidence shows the OPPOSITE sign to a rebound: discounts keep widening for months after a distribution cut.
- STATED in John Cole Scott / Closed-End Fund Advisors ([AICA Episode 275, August 30, 2024](https://aicalliance.org/john-cole-scott-on-how-funds-perform-after-tenders-closings-and-dividend-changes/)): across `1,075` US CEF distribution cuts greater than 10% over 12.5 years (~`86/yr`, average cut `> 20%`), the average discount widened from `-3.8%` at Day `-90` to `-5.2%` at Day `-1`, `-6.3%` at Day `+1`, and `-8.2%` at Day `+90` (`-190 bp` of further widening AFTER Day `+1`). Quote: "in the last 12.5 years there's 1,075 dividend downsides over 10%, the average cut was just over 20%, and 90 days before that announcement the average fund in that group over the 12.5 years was a 3.8% discount. One day before, a 5.2% discount [...] One day after, a 6.3% discount. Ninety days after, an 8.2% discount, so what that means is a negative four and mid-change negative alpha to experience a dividend cut."
- STATED in Xu ([UT Dallas working paper](https://personal.utdallas.edu/~yexiaoxu/CFDDP.pdf)): "Therefore, any changes in the dividend policy will likely have permanent effects, which should make discounts persistent."
- STATED. No post-2010 peer-reviewed event study documents a statistically significant 5-to-20-day positive rebound after US CEF distribution cuts.

Count, spread costs, Doc 117 screen, and failure modes:

- STATED. First count: ~`86` cuts `> 10%` per year (~`860` over 10 years, above 300 in total), but NOT freely countable in real time from EDGAR.
- STATED. Spread cost: `20 to 50+ bp` round-trip, likely wider on cut-announcement days when retail volume spikes.
- STATED. Doc 117 screen: post-announcement Day `+1` to Day `+90` discount change is `-190 bp` (wrong sign for long-only) before spreads -> `0.00 < 4`.
- STATED. How it could fool us: retail income investors exit slowly over weeks and months after a cut, producing negative drift rather than a quick bounce; cuts cluster across entire sponsor suites during rate-hike cycles (such as 2022 to 2023), collapsing independent N; leverage-driven NAV erosion precedes cuts; serial cutters are often merged into sibling funds (survivorship bias).
- STATED. Verdict: DROP.

## Candidate 4: Same-sponsor sibling-fund pairs (long-only switching)

STATED. Hypothesis: rotate long-only between two CEFs from the same sponsor with similar mandates (for example Nuveen muni siblings or PIMCO taxable siblings) when one trades cheaply relative to the other.

Published size after 2010 and later samples:

- STATED. No post-2010 peer-reviewed academic study documents a positive, net-of-spread, long-only CEF sibling-fund switching strategy.
- STATED in John Cole Scott ([AICA, September 9, 2024](https://aicalliance.org/intra-sector-fund-swapping-a-strategy-for-unlocking-value-through-closed-end-funds/) and [show notes](https://aicalliance.org/wp-content/uploads/2024/09/Relative-Disocunt-Swap-Podcast-Notes-2024-0909.pdf)): practitioner commentary presents 10 single-date snapshot examples of same-sponsor swaps averaging ~`14%` to `15%` wider discounts (for example `ISD` at `-2%` vs `SDHY` at `-10%`). Quote: "He then collected average data for high-yielding premium funds and discounted funds that displayed a roughly 15% average wider discount for about the same allocation." No historical return backtest, holding-period return, or spread-adjusted Sharpe is reported.
- STATED in Chen and Alexiou (September 2025, [Journal of Asset Management 26(5), pp. 464 to 488](https://ideas.repec.org/a/pal/assmgt/v26y2025i5d10.1057_s41260-025-00416-0.html)): even in 30 tight-spread ETF pairs (2000 to 2024), cointegration breaks down in short windows. Quote: "Short trading windows, where cointegration holds, limit long-term profitability."
- STATED in Eisele, Nefedova, Parise, and Peijnenburg (2020, [Journal of Financial Economics 135(2), pp. 359 to 378](https://ideas.repec.org/a/eee/jfinec/v135y2020i2p359-378.html)) and [SEC DERA Working Paper (September 2026)](https://www.sec.gov/files/dera-cross-trad-mut-fund-fam-wp-2609.pdf): fund families cross-trade across affiliated siblings, creating persistent performance dispersion rather than pure noise reversion. Quote (Eisele et al. 2020): "While cross-trades should reduce transaction costs for both trading parties, we find that the price of cross-trades is set strategically to reallocate performance among sibling funds."

Count, spread costs, Doc 117 screen, and failure modes:

- STATED. First count: ~`30 to 50` plausible same-sponsor CEF sibling pairs across Nuveen, BlackRock, PIMCO, Eaton Vance, and Cohen & Steers (~`1,500 to 2,500` pair-weeks/yr if traded weekly), but `0` lawful free daily NAV discount-spread series.
- STATED. Spread cost: every long-only swap pays TWO CEF spreads (sell one fund at bid, buy the sibling at ask) = `32 to 100+ bp` per switch based on Nuveen's 2025 Form 425 spreads (`15.63 to 265.44 bp` per fund).
- STATED. Doc 117 screen: no published post-2010 net-of-spread edge (`UNKNOWN / <= 0 bp` after double CEF spread drag) -> `0.00 < 4`.
- STATED. How it could fool us: "near-identical" siblings often differ in duration (`ISD` vs `SDHY`), state tax exemption (`NMZ` vs `NXJ`/`NQP`/`NOM`), leverage ratio, call protection, or managed-distribution yield, creating permanent discount gaps that never converge; stale bond NAVs distort discount spreads; double spread drag kills frequent switching; within-family mergers (such as Nuveen's 2025/2026 muni consolidations) create survivorship and corporate-action traps.
- STATED. Verdict: DROP.

## Candidate 5: Other high-count long-only CEF mechanisms not in QUEUE.md

STATED. Two additional CEF mechanisms outside `docs/QUEUE.md` were checked for `>= 300` events and a post-2010 net edge.

### Candidate 5a: CEF insider / director open-market purchases (SEC Form 4)

STATED. Under Section 30(h) of the 1940 Act ([SEC Form 4 Instructions](https://www.sec.gov/about/forms/form4.pdf)), registered CEF directors, officers, advisers, and `>10%` holders file Form 4 within 2 business days on EDGAR (lawful, free, dated, no NAV required). Quote: "Persons reporting pursuant to Section 30(h) of the Investment Company Act of 1940 must report each transaction resulting in a change in beneficial ownership of any class of securities (equity or debt) of the registered closed-end investment company."

Published size, count, spread costs, and Doc 117 screen:

- STATED in Andriosopoulos, Steliaros, and Thomas (2014, [European Journal of Finance](https://strathprints.strath.ac.uk/47338/1/Directors_Purchases_EJoF_.pdf), 178 UK CEFs, `847` non-overlapping director purchases from 1,979 raw purchases, January 1999 to January 2008, Table I p. 20, Table II p. 22, Table VII p. 27): NAV-adjusted CAR is `+0.245%` on Day 0 (`t = 5.06`), `+0.497%` over `[+2,+15]` (`t = 2.75`), and `+1.172%` over `[+2,+50]` (`t = 4.10`). However, the authors explicitly conclude it is not profitably exploitable after spreads (printed p. 13): "Although average CARs over day -1 to +50 total 1.55%, a strategy of buying the fund and selling the NAV benchmark (and subsequently closing out both positions) would incur two sets of round-trip transactions costs totalling around 2.4% (including 0.5% stamp duty and estimated commission of 0.1%) - and that assumes that the NAV can be cheaply and efficiently replicated. It is therefore unlikely that these short-term abnormal returns could be profitably exploited." Footnote 5 (p. 13) adds that the largest CARs (`> 6%` at day `+50`) came from illiquid private-equity and venture-capital funds.
- STATED in a US CEF Form 4 study (University of Missouri dissertation, [Chapter 4](https://mospace.umsystem.edu/xmlui/bitstream/handle/10355/4400/research.pdf?sequence=3), 37 US equity CEFs, 1994 to 2004): "In summary, while the pooled results relative to absolute discounts are significant, it does not appear that insiders have any timing ability even with respect to their own funds." No post-2010 US CEF Form 4 study documents positive net-of-spread returns.
- STATED. First count: ~`500+` non-overlapping US CEF Form 4 Code P filings over 2016 to 2026 (clears 300), though many `>10%` holder filings are activists (Saba, Bulldog, Karpus) that directly overlap `Row 102 / Plan 63`.
- STATED. Doc 117 screen: applying the UK post-announcement `[+2,+15]` gross CAR (`+49.7 bp`) minus `30 bp` US CEF round-trip spread = `+19.7 bp` net, against `400 bp` 14-day CEF noise across `N = 500` events -> `500 * (19.7 / 400)^2 = 1.21 < 4`.
- STATED. How it could fool us: activist `>10%` Form 4 buys duplicate `Row 102`; small illiquid CEFs drive headline CARs while carrying `100 to 265 bp` spreads; director buys cluster in broad market selloffs (shared rate/equity beta); stale NAVs in private-asset CEFs distort apparent discounts.
- STATED. Verdict: DROP.

### Candidate 5b: CEF open-market share repurchase program (SRP) announcements

- STATED in Kim, Kim, and Song (2013, [International Review of Economics and Finance 27, pp. 345 to 356](https://econpapers.repec.org/article/eeereveco/v_3a27_3ay_3a2013_3ai_3ac_3ap_3a345-356.htm)): US equity CEF share repurchase announcements do not produce significant discount narrowing. Quote: "Using the data from the U.S. equity funds, we find that funds adopting an MDP significantly reduce their discounts at the announcements of the policy, but funds adopting an SRP do not."
- STATED in Yang (2018, [South African Journal of Business Management 49(1)](https://sajbm.org/index.php/sajbm/article/download/14/104), 3,229 UK CEF repurchase executions across 76 funds): "The median price returns for the repurchase sample were insignificantly larger than those for the non-repurchase sample."
- STATED. First count: ~`100 to 250` US CEF SRP announcements over 10 years (`< 300`, not standardized on a real-time EDGAR form, many are routine annual renewals with zero shares repurchased).
- STATED. Doc 117 screen: `0.00 < 4` (no significant announcement discount narrowing in Kim et al. 2013; fails both count and screen).
- STATED. Verdict: DROP.

## Bottom line for the queue

STATED. The high-count CEF space has ~400 funds on SIP bars, but short-horizon, long-only CEF rules outside the already-queued calendar and corporate-action effects (`Replay 48 / E04`, `Replay 53 / E08`, `Row 102 / Plan 63`, `Row 104 / Plan 64`, `Row 55`, `Row 70`) run into four structural blockers: wide CEF bid-ask spreads (`16 to 265+ bp` full spread), post-2009 discount persistence (`8.10`-month median half-life), absence of any lawful free timely historical NAV feed, and wrong-sign negative drift after distribution cuts (`-190 bp`). Zero rows are added to `docs/QUEUE.md`.
