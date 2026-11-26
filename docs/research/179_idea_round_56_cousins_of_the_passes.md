# Idea Round 56: Close Cousins of the Only Three Passing Tests

Date: 2026-11-26 21:19 UTC
Scope: New close cousins of our only three passing tests out of 44 scored tests: Replay 20 (short a coin after an Upbit KRW listing notice), Replay 25 (TLT at month-end), and Replay 48 (muni closed-end funds, January rebound). No price data opened; no return calculations run; no do-not-collect sites cited.

## Bottom Line

Nothing new clears the bar for a count stage or a forward log right now. After auditing every cousin already tested, closed, or blocked in this repo, eight genuinely new cousins were screened across non-Upbit crypto listings and delistings, bond and fund calendar flows, and US stock event flows. Zero qualify for a count stage, zero qualify for a forward log, one earns a narrow watch verdict (fallen-angel corporate bond month-end rebalancing in `ANGL` or `FALN`, pending a free count of nonzero downgrade months), and seven are dropped.

Three structural walls block almost every new cousin for a $500 to $2,000 US account:

- US crypto short access covers only top-30 large coins, not newly listed or delisted altcoins. MEASURED in `docs/research/98_kraken_and_coinbase_short_access.md`, US retail short access is limited to 27 non-BTC/ETH coins on Kraken Pro spot margin and 22 non-BTC/ETH coins on Coinbase Financial Markets perpetual-style futures, while offshore perp venues exclude US residents (`docs/research/40_leverage_venues_checked.md`).
- Most calendar bond and fund flows outside `TLT` already failed or closed on power in this repo (Replay 31, Replay 33, Replay 35, Replay 41, Replay 52, Replay 53, Replay 65, and Queue Rows 69, 91, 92, 93, and 104).
- In US stocks, the strongest remaining event cousins (IPO lockup expirations, quarter-end window-dressing reversals) either require shorting hard-to-borrow shares or have only 4 calendar events per year, failing `docs/research/117_power_screen_before_data.md`.

## Repo Overlap Audit

Every prior cousin of the three passing tests was checked across `docs/research/` and `docs/QUEUE.md` so nothing already tested, dropped, or blocked is re-proposed.

Cousins of Replay 20 (Upbit KRW listing short) already covered:

- Replay 20 (`docs/research/71_replay_20_upbit_listing_short.md`, Queue Row 29): MEASURED pass (5 of 5 marks on viewed dates, +3.2088% net mean over 139 trades at 15 bp per side plus funding, t = 2.839), but executed on offshore Binance USD-M futures, not US-reachable.
- Plan 28 (Queue Row 48): MEASURED closed with no testable history because only 1 of 205 first Upbit KRW notices in 2024 to 2026 had a US-shortable contract. Queue Row 49 runs a live forward watcher for Upbit notices and US-shortable overlap.
- Plan 44 (Queue Row 80): buy Coinbase listing roadmap additions on another US spot venue -> closed at feasibility.
- Plan 45 (Queue Row 79): Binance Monitoring Tags and Upbit and Bithumb caution designations -> closed at feasibility (direct notice reads returned HTTP 403).
- Queue Row 72 (`docs/research/85_round_15_crypto_scheduled_events.md`): major-exchange delisting notice -> harness exit rule only, not a short trade.
- Queue Row 73 (`docs/research/85_round_15_crypto_scheduled_events.md`): Binance spot listing announcements -> WATCH (broad listings fail from +3 min).
- Queue Row 36 and `docs/research/104_round_26_forced_flow_siblings.md`: cliff token unlocks -> forward logger only; Albiez (2026) found no detectable 3-day abnormal return across 913 cliff unlocks, and small coins cannot be shorted in the US.
- Queue Row 84 (`docs/research/96_round_23_permitted_small_coin_sources.md`): exchange product-status watcher -> live forward-only logger.

Cousins of Replay 25 (`TLT` month-end, last 3 sessions) already covered:

- Replay 25 (`docs/research/69_replay_25_treasury_month_end.md`, `docs/research/149_what_the_passes_are_worth.md`, Queue Row 41): MEASURED pass (9 of 9 marks, +0.2562% net at 2 bp per side over 130 windows, t = 2.36; partial 2026 was -5.50%). Queue Row 46 is the E01 12-month forward log. Queue Row 45 (2002 to 2015 check, Replay 26) was blocked.
- Measurement 27 (`docs/research/70_measure_27_tlt_closing_cross.md`, Queue Row 47): Nasdaq closing cross vs SIP close -> frozen mark 1 not met (cross print on only 124 of 260 sessions).
- Measurement 34 (`docs/research/82_measurement_34_tmf_ubt_month_end.md`, Queue Row 56): `TMF` 3x and `UBT` 2x on Replay 25's exact 130 windows -> `TMF` failed gross tracking (2.5853x vs 2.7x to 3.1x), `UBT` round-trip half-spread was 21.55 bp.
- Replay 31 (`docs/research/80_replay_31_bond_fund_month_end.md`, Queue Row 50): equal-weight `LQD`, `HYG`, `MBB`, and `TIP` on Replay 25's last 3 sessions -> MEASURED failed (2 of 10 marks).
- Replay 33 (`docs/research/89_replay_33_treasury_auction_days.md`, Queue Row 52): intraday 10-year and 30-year Treasury auction reversal (`IEF` and `TLT`, 13:10 to 15:59 ET) -> MEASURED failed.
- Replay 35 (`docs/research/81_replay_35_cme_bitcoin_expiry_ibit.md`, Queue Row 57): long `IBIT` at monthly CME Bitcoin expiry -> MEASURED failed (1 of 6 marks, -0.1626% net).
- Replay 41 (`docs/research/92_replay_41_month_end_laggard_switch.md`, Queue Row 54): month-end pension and target-date proxy (`SPY` vs `TLT` laggard switch) -> MEASURED failed (4 of 8 marks).
- Replay 52 (`docs/research/113_replay_52_quarter_end_corporate_bond_funds.md`, Queue Row 94): quarter-end dealer SLR corporate bond funds -> MEASURED failed (0 of 6 marks, -0.0308% net).
- Replay 65 (`docs/research/139_replay_65_stock_bond_rebalancing.md`, Queue Row 106): daily stock-bond rebalancing (`SPY` vs `IEF`, Harvey, Mazzoleni and Melone) -> MEASURED failed.
- Queue Row 69 (`docs/research/83_round_14_treasury_month_end_relatives.md`): muni bond month-end index extension and Jun, Jul, Dec reinvestment in `MUB` and `VTEB` -> CLOSED on power (below 33% line).

Cousins of Replay 48 (muni CEFs January rebound) already covered:

- Replay 48 (`docs/research/103_replay_48_muni_cef_january.md`, `docs/research/149_what_the_passes_are_worth.md`, Queue Row 86): MEASURED pass (7 of 7 marks, +1.39% mean net over 10 turns, positive in 8 of 10). E04 is the forward watch.
- Replay 53 (`docs/research/122_replay_53_taxable_fund_january_rebound.md`, Queue Row 90): taxable CEF January rebound -> MEASURED failed (5 of 7 marks, positive in 6 of 10); Queue Row 103 is the shown-only E08 fifth-session exit watch.
- Queue Rows 91, 92, and 93 (`docs/research/106_row91_preferred_shares_tax_loss_rebound.md`, `docs/research/107_row92_bdc_tax_loss_rebound.md`, `docs/research/108_row93_mutual_fund_oct31_tax_loss_rebound.md`): preferred shares, BDCs, and Oct 31 mutual-fund tax-loss rebounds -> all CLOSED on synthetic power before prices.
- Queue Row 66 (`docs/research/79_round_13_known_clock_premia.md`) and `docs/research/176_idea_round_53_forced_flows.md`: single small-stock December tax-loss rebound -> watch only (~10 year-turns, no historical test).
- Queue Row 55 (`docs/research/111_round_27_higher_payoff_forced_flows.md`): CEF rights offerings post-expiration -> CLOSED on power.
- Queue Row 70 (`docs/research/83_round_14_treasury_month_end_relatives.md`): CEF DRIP pay-date buying -> WAITING.
- Queue Row 102 (`docs/research/124_count_102_cef_activist_13d_census.md`): CEF activist 13D discount mean reversion -> counted.
- Queue Row 104 (`docs/research/165_plan_64_closed_on_coverage.md`): equity CEF special and irregular distribution ex-date -> CLOSED on identity coverage.
- Queue Row 121 (`docs/research/166_m121_cef_resting_bid.md`): CEF resting bid spread measurement -> Done.
- `docs/research/104_round_26_forced_flow_siblings.md`: royalty trusts, MLPs, reverse-side late-January CEF short, ETF and mutual-fund December capital-gain distributions -> all DROPPED.

## Summary of New Ranked Cousins

| Rank | New cousin | Parent pass | Dated source (free?) | Events/yr | Post-2015 after-cost evidence | Doc 117 power | $500 to $2,000 US fit | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | Fallen-angel corporate bond month-end rebalance (`ANGL` or `FALN`) | Replay 25 | Monthly calendar (free) | 12/yr (lumpy downgrade months) | Long-horizon outperformance STATED; short month-end ETF net edge UNKNOWN | Tight (12/yr; lumpy) | Yes, 1x cash ETF | WATCH |
| 2 | Non-Upbit crypto listing shorts (Bybit, OKX, Bitget, Coinone, Korbit, Robinhood) | Replay 20 | Venue notice APIs/boards (free) | 10 to 300+/yr | Post-listing unloading STATED; Robinhood front-running flagged | Fails on US overlap (~1/yr) | No (not on US short rosters) | DROP |
| 3 | Crypto delisting notice shorts (Bybit, OKX, Bitget, Coinone) | Replay 20 | Venue delisting archives (free) | 30 to 100+/yr | Large gross drops STATED (-5% to -9% 24h), no delisted API tape | Unverifiable (no delisted tape) | No (tail coins unshortable in US) | DROP |
| 4 | Untested bond ETF month-end extension (`EMB`, `BNDX`, `EDV`, `ZROZ`) | Replay 25 | Monthly calendar (free) | 12/yr | None post-2015 after costs; `EDV`/`ZROZ` duplicates `TLT` | Weak (Replay 31 failed) | Yes, 1x cash ETF | DROP |
| 5 | Quarter-end mutual-fund ESG and style window-dressing reversal | Replay 25 and 48 | Quarterly calendar (free) | 4/yr | +16.7 bp gross long-only pre-Q-end; post-Q-end loser bounce null | Fails (4/yr) | Weak (long-only too small) | DROP |
| 6 | Target-date fund rebalancing calendar | Replay 25 | Monthly/quarterly calendar (free) | 4 to 12/yr | Slow 1 to 3 month drift; Vanguard shifted to threshold bands | Fails (Replay 41, 65 failed) | Yes, 1x cash ETF | DROP |
| 7 | Closed-end fund repurchase tender offers | Replay 48 | SEC Schedule TO-I (free) | ~10 to 30/yr | Disappeared after costs (~0.5% gross, insignificant net) | Fails | Poor (manual tender, proration) | DROP |
| 8 | US IPO lockup expiration (short or post-unlock rebound) | Replay 20 and 48 | SEC S-1 and 424B4 (free) | ~100 to 200/yr | Short side driven by borrow constraints; post-unlock rebound is zero | Fails on long side | No (cannot short HTB IPOs) | DROP |

## Ranked Cousin Reviews

### Rank 1: Fallen-Angel Corporate Bond Month-End Rebalance (`ANGL` or `FALN`)

- Parent pass and what is new: Cousin of Replay 25 (`TLT` month-end). Replay 31 tested broad investment-grade (`LQD`) and broad high-yield (`HYG`) in the last 3 sessions and failed, and Replay 52 tested quarter-end dealer SLR in corporate bond funds and failed. Neither tested fallen-angel bond ETFs (`ANGL` or `FALN`), which hold corporate bonds recently downgraded from investment grade to high yield and absorb forced month-end index deletion selling.
- Dated event source: Free monthly calendar (last business day of each month, when investment-grade bond indices expel downgraded issuers and fallen-angel indices add them). STATED in [FTSE Russell Fallen Angels in the US Credit Market](https://www.lseg.com/content/dam/ftse-russell/en_us/documents/research/fallen-angels-us-credit-market.pdf): "Rebalancing Once a month at the end of the month."
- Who is forced to trade and why it could persist: Passive IG bond ETFs, pension mandates, and insurance companies constrained to investment-grade ratings must sell downgraded bonds at or before the month-end index rebalance. STATED in [DNB Asset Management](https://dnbam.com/en/news-and-insights/fallen-angels-the-last-free-lunch): "Rating changes are one of the most common reasons why index members' change and FA bonds are excluded from an IG index at its next monthly rebalancing. To avoid breaches with mandates and increased tracking error, IG investors have strong incentives or are even forced to sell FAs within a short time period, creating short term price pressure."
- Published post-2015 after-cost evidence: Long-horizon outperformance is well documented through 2026. STATED in [VanEck ANGL Value Proposition (June 2026)](https://www.vaneck.com/angl-value-proposition.pdf): "For 15 out of the last 22 calendar years, fallen angel high yield bonds have outperformed the broad U.S. high yield bond market, including original issue high yield bonds." Earlier European bond evidence found a post-rebalance bounce ([CFA Digest summary of Bolognesi 2014](https://rpc.cfainstitute.org/research/cfa-digest/2015/01/the-impact-of-fallen-angels-on-investment-grade-corporate-bonds-portfolios-evidence-from-the-eu)): "When the benchmark index is rebalanced at the end of the month, the price of the fallen angels bounces back to reflect its true market value with respect to its new HY peers." However, post-2015 after-cost short-window (3 to 10 day) ETF-level evidence on `ANGL` or `FALN` around month-end is UNKNOWN.
- Events per year, doc 117 power, and $500 to $2,000 US account fit: 12 monthly rebalances per year (~120 to 130 over 10 to 11 years), matching Replay 25's calendar count, and reachable at 1x on a $500 to $2,000 US cash brokerage account. The key risk is lumpiness: many calm months have zero or tiny IG-to-HY downgrades, so the effective event count of real forced-selling months may be far below 12 per year, and `ANGL` spreads are wider than `TLT`'s 0.610 bp.
- Verdict: WATCH.
- Cheapest honest next step: Without opening price data, count how many months from 2016 to 2026 had nonzero fallen-angel index additions in free monthly VanEck or ICE index reports; if fewer than half of months carry material downgrade volume, drop before any price test.

### Rank 2: Non-Upbit Crypto Listing Shorts (Bybit, OKX, Bitget, Coinone, Korbit, Robinhood, Crypto.com)

- Parent pass and what is new: Direct venue-expansion cousin of Replay 20 (Upbit KRW listing short), checking venues outside Upbit, Bithumb, and Binance.
- Dated event source: Free public venue announcement APIs and boards exist for Bybit V5 (`new_crypto`), OKX V5 (`announcements-new-listings`), Bitget V2 (coin listings), Coinone and Korbit notice boards, and Robinhood Newsroom ([cexready.com](https://cexready.com/new-listings/), [MEXC Disclosure Index](https://www.mexc.com/learn/article/which-exchange-lists-new-coins-first-8-exchanges-5-disclosure-tests-and-only-one-passed-all-five/1), [CoinGaja](https://coingaja.com/en/listing)).
- Who is forced or crowded and post-2015 evidence: Retail buyers chase new-venue listings and later unload. STATED in [Ante and Meyer (2021, Springer)](https://link.springer.com/article/10.1007/s10203-021-00323-0): "We find evidence of unloading effects in the form of significant negative abnormal returns after the cross-listings, though to varying degrees for the individual exchanges." On Robinhood, pre-announcement positioning already eats the initial move; STATED in [BitRss summary of Kaiko (2026)](https://bitrss.com/kaiko-flags-frontrunning-risk-ahead-of-robinhood-token-listings-207656): "Tokens like Zcash (ZEC), Synthetix (SNX), and Near Protocol (NEAR) showed abnormal returns in the hours leading up to and immediately after Robinhood's public listing announcements."
- Events per year, doc 117 power, and $500 to $2,000 US account fit: Global event counts are high (100+ per year on Bybit, OKX, and Bitget; roughly 10 to 30 per year on Coinone, Korbit, and Robinhood), but the US short-access wall kills it. MEASURED in `docs/research/98_kraken_and_coinbase_short_access.md`, US retail short access covers only 27 non-BTC/ETH coins on Kraken Pro spot margin (trade history starting April 2026) and 22 non-BTC/ETH coins on Coinbase CFM perpetual-style futures (candles starting Dec 2025 to Jun 2026), almost all top-30 established coins. Offshore venues (Bybit, OKX, Bitget) exclude US residents; STATED in [SEC Form S-1/A filing (2025)](https://www.sec.gov/Archives/edgar/data/2083106/000119312525243710/ada_s-1_amendment_1.htm): "Bybit does not hold any licenses or registrations in the U.S. and is not available to U.S. based customers" and "OKX does not hold any licenses or registrations in the U.S. and is not available to U.S.-based customers." Just as Plan 28 (Queue Row 48) found only 1 of 205 Upbit notices had a US-shortable contract, newly listed altcoins on these venues almost never overlap our 22 to 27 coin US short roster.
- Verdict: DROP.
- Cheapest honest next step: None; Queue Row 49 and Queue Row 84 already log forward US-shortable overlap.

### Rank 3: Crypto Delisting Notice Shorts (Bybit, OKX, Bitget, Coinone)

- Parent pass and what is new: Mirror-image cousin of Replay 20 using dated delisting notices instead of listing notices, distinct from Queue Row 72 (which is a long-exit harness rule) and Plan 45 (Binance/Upbit/Bithumb caution tags, blocked by HTTP 403).
- Dated event source: Free dated delisting archives on Bybit (7-day notice before halt), OKX (4-day notice), Bitget (6-day notice), and Coinone ([MEXC Disclosure Index](https://www.mexc.com/learn/article/which-exchange-lists-new-coins-first-8-exchanges-5-disclosure-tests-and-only-one-passed-all-five/1), [CoinGaja](https://coingaja.com/en/listing)).
- Who is forced to trade and post-2015 evidence: Holders must liquidate or withdraw before trading halts. STATED in [Blockonomi summary of CoinSight (2026)](https://blockonomi.com/what-happens-when-a-cryptocurrency-gets-delisted-from-an-exchange/) across 1,867 announcements from August 2022 to October 2026: "Upbit delistings had a median 24-hour move of about -9.0%, OKX about -6.3% and Bybit about -5.2%." However, historical verification is blocked by missing delisted price series. STATED in [Yang (2026), Asia-Pacific Journal of Financial Studies](https://onlinelibrary.wiley.com/doi/full/10.1111/ajfs.70045): "Note, however, that major global exchanges such as Bybit, OKX, and Upbit do not provide historical trading data for tokens that have already been delisted, according to our review of publicly available Application Programming Interfaces (APIs) from CCXT, pyupbit, and related libraries."
- Events per year, doc 117 power, and $500 to $2,000 US account fit: 30 to 100+ delistings per year globally, but zero US shortability on a $500 to $2,000 account because dying tail tokens are not on the 22 to 27 large-coin US short rosters in `docs/research/98_kraken_and_coinbase_short_access.md`.
- Verdict: DROP.
- Cheapest honest next step: None; keep delisting notices strictly as a long-exit harness rule under Queue Row 72.

### Rank 4: Month-End Index Extension in Untested Bond ETFs (`EMB`, `BNDX`, `EDV`, `ZROZ`)

- Parent pass and what is new: Direct bond-ETF cousin of Replay 25 (`TLT` month-end) using fixed-income ETFs not tested in Replay 31 (`LQD`, `HYG`, `MBB`, `TIP`) or closed in Queue Row 69 (`MUB`, `VTEB`).
- Dated event source: Free monthly calendar (last 3 sessions of each month, 12 windows per year).
- Who is forced to trade and post-2015 evidence: Passive bond index funds extend duration at month-end when new bonds enter and sub-1-year bonds drop out. For `EDV` and `ZROZ` (US Treasury STRIPS), this is the exact same US Treasury month-end flow as Replay 25, not an independent event set, with wider spreads than `TLT` (similar to `UBT` in Measurement 34). For `EMB` (EM USD sovereigns) and `BNDX` (hedged international bonds), no post-2015 published after-cost month-end ETF return evidence was found, and our own Replay 31 failed 2 of 10 marks on non-Treasury US bond ETFs.
- Events per year, doc 117 power, and $500 to $2,000 US account fit: 12 windows per year, reachable at 1x on a $500 to $2,000 cash account, but Replay 31's failure and Row 69's power closure show non-Treasury bond ETF month-end flows do not clear the bar.
- Verdict: DROP.
- Cheapest honest next step: None; finish E01's 12-month forward log on `TLT` first.

### Rank 5: Quarter-End Mutual-Fund ESG and Style Window-Dressing Reversal

- Parent pass and what is new: Calendar-flow cousin of Replay 25 and Replay 48 using equity mutual-fund quarter-end holdings disclosure rather than Replay 52's corporate-bond dealer SLR.
- Dated event source: Free quarterly calendar (last 5 sessions before quarter-end and first 5 sessions of the new quarter; 4 events per year).
- Who is forced or crowded and post-2015 evidence: Active US equity mutual funds buy high-ESG or winning stocks before quarter-end disclosure to attract inflows and reverse afterward. STATED in [LSE Financial Markets Group DP923 (2025)](https://www.fmg.ac.uk/sites/default/files/2025-03/DP923.pdf) over 2015Q1 to 2022Q2: "Take the value-weighted portfolio for instance, the high-ESG stocks generate an abnormal return of 0.17% (t-stat=4.06) in the five days before quarter ends and then experience a negative return of -0.17% (t-stat=-1.96) in the next five days at the quarter beginning." STATED: "We assume that all transactions occur at the end of each trading day. While this assumption simplifies the estimation, it overlooks two important features: (a) intra-day trading and (b) trading costs, which include trading commissions and price impact."
- Events per year, doc 117 power, and $500 to $2,000 US account fit: Only 4 quarter-ends per year (40 events in 10 years), failing `docs/research/117_power_screen_before_data.md`. On a $500 to $2,000 long-only cash account (no shorting), the pre-quarter-end high-ESG long leg earns only +16.7 bp gross per quarter (~0.67% per year before doc 136 spreads of 1.67 to 3.79 bp per side), while the post-quarter-end low-ESG rebound leg was +4.5 to +11.2 bp gross (t = 0.19 to 0.57, statistically zero).
- Verdict: DROP.
- Cheapest honest next step: None.

### Rank 6: Target-Date Fund Rebalancing Calendar

- Parent pass and what is new: Cousin of Replay 25 testing whether target-date funds (TDFs) create predictable short-window stock-bond calendar flows beyond Replay 41 (month-end `SPY` vs `TLT` laggard switch, failed 4 of 8) and Replay 65 (daily `SPY` vs `IEF` rebalancing from NBER w33554, failed).
- Dated event source: Free monthly or quarterly calendar.
- Who is forced to trade and post-2015 evidence: TDFs rebalance against equity-bond drift, but empirical evidence shows the flow is spread slowly over months and major providers moved off fixed calendar dates. STATED in [Parker, Schoar and Sun (NBER w28028 / Journal of Finance 2023)](https://www.nber.org/system/files/working_papers/w28028/w28028.pdf): "Following monthly differential returns between asset classes, we estimate that roughly 45% of the predicted rebalancing is implemented in the same month, 25% in the following month, and another 10% with a two-month lag." STATED in [Vanguard Research (December 2024)](https://www.vanguardsouthamerica.com/content/dam/intl/americas/documents/latam/en/2024/12/the-rebalancing-edge.pdf): "For a 60% stock/40% bond portfolio (a '60/40' portfolio), Vanguard's threshold-based rebalancing methodology is expected to generate higher annual returns relative to calendar-based rebalancing approaches due to reduced transaction costs."
- Events per year, doc 117 power, and $500 to $2,000 US account fit: Reachable at 1x on a cash account, but there is no sharp 1-day to 3-week calendar clock left to trade, and both repo tests of this mechanism (Replay 41 and Replay 65) already failed.
- Verdict: DROP.
- Cheapest honest next step: None.

### Rank 7: Closed-End Fund Repurchase Tender Offers

- Parent pass and what is new: Direct CEF-discount cousin of Replay 48 (muni CEFs January rebound), distinct from Queue Row 55 (rights offerings, closed on power), Row 70 (DRIP pay dates, waiting), Row 102 (activist 13D), and Row 104 (special distributions, closed on coverage).
- Dated event source: Free SEC Schedule TO-I filings with exact offer expiration dates (~10 to 30 CEF tender offers per year).
- Who is forced to trade and post-2015 evidence: Funds repurchase a fixed share fraction near NAV (typically 95% to 98% of NAV), attracting arbitrageurs before expiration. However, published empirical reexamination shows the edge vanished after costs. STATED in [Kadapakkam, Zhang and Yildirim (2020, Review of Quantitative Finance and Accounting)](https://link.springer.com/content/pdf/10.1007/s11156-020-00935-4.pdf): "Given the rise of event-driven hedge funds, we reexamine this strategy in recent years (2000–2015) and find that abnormal profits from tendering have disappeared." STATED: "Examining a sample of closed-end fund repurchase tender offers during the same period, we find abnormal tendering profits of around 0.5%. However, these profits are no longer significant after adjustments for transaction costs."
- Events per year, doc 117 power, and $500 to $2,000 US account fit: Low event count, zero net edge after costs, proration leaves unhedged NAV exposure on untendered shares, and voluntary corporate-action tender elections are manual and poorly suited to a $500 to $2,000 automated account.
- Verdict: DROP.
- Cheapest honest next step: None.

### Rank 8: US IPO Lockup Expiration (Short Into Unlock or Post-Unlock Rebound)

- Parent pass and what is new: US-stock cousin of Replay 20 and Replay 48 using a fixed, free SEC-dated supply shock (typically 180 days post-IPO) where insiders become free to sell.
- Dated event source: Free SEC Form S-1 and Form 424B4 prospectuses (~100 to 200 US IPOs per year in active years).
- Who is forced to trade and post-2015 evidence: Pre-IPO insiders and VC funds distribute or sell shares once contractual lockups expire, creating predictable negative returns around the unlock date. STATED in [MIT Sloan working paper on 709 US IPOs (2007 to 2015)](https://mitsloan.mit.edu/sites/default/files/inline-files/Short-sales%20Constraints%20and%20Aftermarket%20IPO%20Pricing.pdf): "The average market-adjusted return cumulated from ten trading days before to ten trading days after the lockup expiration is -3.41% with a standard deviation in excess of 15%." However, that same paper shows the anomaly is concentrated in hard-to-borrow small IPOs driven by short-sale constraints. On the long-only post-expiration rebound side, STATED in [Subrahmanyam et al. (UCLA)](https://www.anderson.ucla.edu/documents/areas/fac/finance/subra_lockup.pdf): "CARs in the post expiration windows of (+2, +5), (+2,+10) and (+2,+20) are not significantly different from zero." And [Chong and Liu (2016, Springer)](https://link.springer.com/article/10.1007/s11156-015-0510-8) found non-VC lockup CARs disappear under matched benchmarking.
- Events per year, doc 117 power, and $500 to $2,000 US account fit: A $500 to $2,000 US cash account cannot short hard-to-borrow newly public stocks, and the long-only post-unlock rebound is statistically zero.
- Verdict: DROP.
- Cheapest honest next step: None.

## What This Means for Our Queue

- Do not open a new count stage or forward log from Round 56.
- Focus existing effort on the forward tracks already built for the three passes: E01 (`TLT` month-end, Queue Row 46), E04 (muni CEFs January watch), and Queue Row 49 (Upbit forward US-shortable overlap).
- The only open watch item from Round 56 is Rank 1 (`ANGL` or `FALN` fallen-angel month-end), and only as a zero-price count of nonzero monthly IG-to-HY downgrade additions before any further work.
