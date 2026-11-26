# 151: Round 44 Discovery-Sweep Mechanism Families (Plans 69 and 70)

Written: 2026-11-26 13:13 UTC.
Scope: Raw mechanism families (not finished published rules) for the two sealed-vault discovery sweeps fixed in `docs/150_discovery_sweep_design.md`: Plan 69 (US stocks and ETFs, intraday and overnight on Alpaca SIP bars from 2016; search `2016-01-04` to `2021-12-31`, vault `2022-01-03` to `2026-10-30`) and Plan 70 (coins tradable both ways from the US on hourly bars already held; search `2020-01-01` to `2023-12-31`, vault `2024-01-01` to `2026-10-31`, judged at Coinbase CFM futures costs in `docs/research/120_round_31_cfm_futures_cost_rescreen.md` with US spot beside it). No price was read and no return was computed. Claims are labeled `MEASURED` (from repo records), `STATED` (from opened primary sources), or `UNKNOWN`.

## Already-Scored Families Excluded

`MEASURED` from the Done table of `docs/QUEUE.md` and `docs/research/95_where_we_stand_after_32_tests.md`, the following scored families are left out of both grids so the sealed vaults remain clean:

- Excluded from Plan 69 (US stocks and ETFs): slow daily or monthly trend and 12-month stock momentum (Replays 05, 06, 14); SPY and QQQ opening-range breakout, noise-band breakout, unconditional first-half-hour to last-half-hour sign, above-VWAP hold, unconditional overnight-only, and unconditional day-only holds (Replay 07 rules N1 through N6); stocks-in-play opening-range breakouts (Measurement 15); odd-lot tenders, IPO fast-track, and Congress disclosures (Replays 12, 21, 23); Treasury and corporate bond ETF month-end and quarter-end windows and SPY-vs-TLT laggard switch (Replays 25, 31, 41, 52); Treasury auction afternoons on IEF and TLT (Replay 33); IBIT on CME Bitcoin expiry (Replay 35); IWM pre-holiday (Replay 39); all closed-end funds and plans 63 and 64 (excluded by Plan 69 scope, including Replays 48 and 53); special-dividend declarations and ex-days (Replays 60 and 62); and daily SPY-vs-IEF stock-bond rebalancing at the close from a 15:30 signal (Replay 65).
- Excluded from Plan 70 (US two-way coins, hourly): daily trend and range-break rules on BTC, ETH, or coin baskets (Replays 01, 04, 22); hourly chart-pattern rules on BTC and ETH (Replay 03); unconditional fixed Asia hours, unconditional fixed weekend holds, Monday weekly momentum, daily cross-sectional loser reversal, BTC-lead long-only altcoin catch-up, weekly volatility-targeted BTC, and daily-bar BTC capitulation (Replay 09 rules ASIA, WKND, MOM, REV, LEAD, VOL, CAP); weekly hot-five momentum, 5% dip buys, and 5% off-peak shorts (Replays 13, 16, 17); cross-coin and same-coin perpetual funding carry (Replays 18 and 24); Monday Asia 24-hour BTC and ETH trend (Replay 19); Upbit listing shorts (Replay 20); and CFTC altcoin futures listing long and short legs (Replay 46).

## Plan 69: 12 Mechanism Families for US Stocks and ETFs (Intraday and Overnight)

All 12 families are long-only for a `$500` US cash account (no margin shorting), use bar-only signals (5-minute or 30-minute SIP bars), and carry 3 to 6 natural parameter settings. Vault dates to check for overlap: `2022-01-03` to `2026-10-30`.

### S1. Leveraged and inverse ETF end-of-day rebalancing continuation (15:30 to 15:59 ET)

- Who is forced to trade and when (`STATED`): Daily-reset 2x and 3x leveraged and inverse ETFs must rebalance swaps and underlying exposure near the 16:00 ET close in the same direction as the day's move. Per the [ProShares UltraPro QQQ Summary Prospectus on SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1174610/000119312514356432/d768699d497k.htm): "At the close of the U.S. securities markets on each trading day, the Fund will seek to position its portfolio so that its exposure to the Index is consistent with the Fund's investment objective." Per [Shum, Hejazi, Haryanto, and Rodier (2016, Review of Finance)](https://academic.oup.com/rof/article-abstract/20/6/2379/2418138): "For the period surrounding the financial crisis, 2006–11, we show that end-of-day volatility was positively and statistically significantly correlated with the ratio of potential rebalancing trades to total trading volume."
- Source sample dates and vault overlap: Prospectus (rule document, no empirical sample); Shum et al. (2016) sample is 2006 to 2011. NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: Cumulative regular-session return from 09:30 open to 15:25 or 15:30 close on leveraged-ETF-heavy index and sector ETFs (`QQQ`, `IWM`, `XLF`, `SMH`, `XLE`, `XBI`) of at least `+1.5%`, `+2.0%`, `+2.5%`, or `+3.0%` (4 thresholds), optionally requiring 15:00 to 15:30 volume at least `1.2x` trailing 20-day same-bucket median.
- Entry and exit print on `$500`: Buy at 15:30 open (or 15:35 open); sell at 15:59 close (or MOC print).
- Already scored in repo: No (Replay 07 N3 tested unconditional 09:30 to 09:59 sign on SPY and QQQ only).

### S2. Leveraged ETF end-of-day forced-selling overnight fade (15:55 to next morning)

- Who is forced to trade and when (`STATED`): Forced end-of-day selling by leveraged and inverse ETFs on large down days temporarily pushes closing prices below fair value, reverting by the next morning. Per [Barbon, Beckmeyer, Buraschi, and Moerke (2022, SFI 22-40)](https://abarbon.com/assets/Liquidity_Provision_to_Rebalancing_Flows_from_Leveraged_ETFs_and_Equity_Options.pdf): "We show that they induce significant end-of-day momentum and mean-reversion in stock returns, while the effects dissipate within the next trading day."
- Source sample dates and vault overlap: Shum et al. (2016) covers 2006 to 2011; Barbon et al. (2022) covers pre-2022 data. NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: Cumulative 09:30 open to 15:55 close return at or below `-1.5%`, `-2.0%`, `-2.5%`, or `-3.0%` (4 thresholds) on liquid ETFs and large caps, optionally requiring a negative 15:30 to 15:55 bar (`<= -0.3%`).
- Entry and exit print on `$500`: Buy at 15:55 close or 15:59 close; sell at next session 09:35 open or 10:00 open.
- Already scored in repo: No (Replay 07 N5 was an unconditional every-night hold on SPY and QQQ).

### S3. NYSE and Nasdaq 15:50 ET MOC imbalance publication shock and overnight reversal

- Who is forced to trade and when (`STATED`): NYSE Rule 7.35B publishes Significant Closing Imbalances at 15:50 ET and restricts subsequent MOC and LOC orders to the contra-side, forcing liquidity providers to absorb sudden end-of-day supply in the final 10 minutes. Per the [NYSE Q1 2026 Regulatory Memo on Rule 7.35B](https://www.nyse.com/publicdocs/nyse/markets/nyse/rule-interpretations/2026/Q1_2026_Quarterly_Expiration_RM_3.20.2026.pdf): "After 3:50 p.m., Exchange systems will accept only MOC and LOC Orders opposite to the side of the Significant Closing Imbalance."
- Source sample dates and vault overlap: Exchange rule document (no empirical sample). NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: 5-minute return from 15:50 to 15:55 at or below `-0.50%`, `-0.75%`, `-1.00%`, or `-1.50%` (4 thresholds) accompanied by 15:50 to 15:55 volume at least `2.0x` or `3.0x` trailing 20-day median for that same 5-minute bucket.
- Entry and exit print on `$500`: Buy at 15:55 close (or 15:59 close); sell at next session 09:35 open or 10:00 open.
- Already scored in repo: No.

### S4. Opening-auction retail attention and MOO gap-down reversal (09:35 to 10:30 or 11:00 ET)

- Who is forced to trade and when (`STATED`): Attention-driven retail market-on-open orders create temporary opening-price dislocations that liquidity providers correct during regular trading hours. Per [Berkman, Koch, Tuttle, and Zhang (2012, JFQA)](https://scispace.com/pdf/paying-attention-overnight-returns-and-the-hidden-cost-of-52o3bohkjq.pdf): "This result indicates that the significant overnight return patterns in Panels A and B represent a temporary mispricing at the open, which tends to be corrected during the course of the typical trading day."
- Source sample dates and vault overlap: Berkman et al. (2012) sample is 1996 to 2008. NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: Overnight gap (09:30 open versus prior 16:00 close) at or below `-1.5%`, `-2.5%`, `-3.5%`, or `-5.0%` (4 thresholds), with the 09:30 to 09:35 bar closing above its open (initial stabilization) and 09:30 to 09:35 volume at least `2.0x` trailing 20-day median.
- Entry and exit print on `$500`: Buy at 09:35 open (avoids the widest 09:30 opening spreads measured in `docs/research/136_measured_stock_trading_costs.md`); sell at 10:30 open, 11:00 open, or 15:55 close.
- Already scored in repo: No (Replay 07 N1 and Measurement 15 tested upward breakouts, not gap-down reversals).

### S5. ETF primary-market creation and redemption cut-off afternoon basis convergence (14:00 to 15:59 ET)

- Who is forced to trade and when (`STATED`): Authorized Participants must submit irrevocable Creation Unit orders generally before 16:00 ET (earlier for cash or custom baskets) to receive that day's NAV, concentrating AP arbitrage and hedging in the final two hours. Per the [iShares Trust Statement of Additional Information on SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1524513/000119312514330590/d784993d485apos.htm): "An Authorized Participant must submit an irrevocable order to purchase shares of the Fund generally before 4:00 p.m., Eastern time on any Business Day in order to receive that day's NAV."
- Source sample dates and vault overlap: SEC SAI filing (rule document, no empirical sample). NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: Intraday 09:30 to 14:00 (or 14:30) return of a liquid sector or style ETF minus SPY return at or below `-0.75%`, `-1.00%`, `-1.50%`, or `-2.00%` (4 thresholds), with ETF afternoon volume at least `1.5x` trailing 20-day median.
- Entry and exit print on `$500`: Buy at 14:00 open or 14:30 open; sell at 15:59 close.
- Already scored in repo: No.

### S6. Option dealer end-of-day delta-hedging and gamma-imbalance pressure (15:30 to 15:59 ET and overnight)

- Who is forced to trade and when (`STATED`): Option market makers re-establishing delta-neutrality before the 16:00 ET close generate temporary end-of-day price pressure that reverts at the next day's open. Per [Beckmeyer and Moerke (2021, EFMA)](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2021-Leeds/papers/EFMA%202021_stage-2049_question-Full%20Paper_id-237.pdf): "Establishing delta-neutrality around the market close causes return momentum or reversal of 18 basis points for each one percentage point move in the underlying until half an hour before trading close." and "This price pressure is temporary, as the effect reverts at the next day's open."
- Source sample dates and vault overlap: Beckmeyer and Moerke (2021) uses pre-2021 US option and TAQ data. NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: Realized intraday range from 09:30 to 15:00 at least `1.5x`, `2.0x`, or `2.5x` trailing 20-day median range (3 thresholds, bar-only proxy for active short-gamma hedging), combined with 15:30 price in the top 20% of the day's range (long continuation into 15:59) or bottom 20% of the day's range (buy 15:59 close, sell next 09:35 open).
- Entry and exit print on `$500`: Continuation leg buys 15:30 open and sells 15:59 close; reversal leg buys 15:59 close and sells next 09:35 open.
- Already scored in repo: No.

### S7. Closing selloff dealer-inventory shock and overnight reversal (15:55 to 09:35 ET)

- Who is forced to trade and when (`STATED`): Liquidity providers absorbing late-day sell order imbalances demand a discount at the US close and earn it back overnight as overseas buyers arrive. Per [Boyarchenko, Larsen, and Whelan (2020, rev. 2022, FRBNY Staff Report 917)](https://www.newyorkfed.org/research/staff_reports/sr917.html): "Consistent with models of inventory risk, we demonstrate a strong relationship with order imbalances at the close of the preceding U.S. trading day." and "market selloffs generate robust positive overnight reversals, while reversals following market rallies are much more modest."
- Source sample dates and vault overlap: Original FRBNY SR 917 sample is 1998 to 2020 (NO overlap). FLAG: the authors' July 2026 [Liberty Street Economics follow-up](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/) covers 2021 to 2026, OVERLAPPING the stock vault (`2022-01-03` to `2026-10-30`), and states: "the 2:00–3:00 window that previously generated roughly 3.7 percent per annum has averaged close to zero since 2021." Conditional close-selloff reversals on individual stocks and sector ETFs remain untested here.
- Bar-only signal and settings: Last-hour (15:00 to 15:55) return at or below `-0.50%`, `-1.00%`, `-1.50%`, or `-2.00%` (4 thresholds) on last-hour volume at least `1.5x` trailing 20-day median.
- Entry and exit print on `$500`: Buy at 15:55 close or 15:59 close; sell at next session 09:35 open.
- Already scored in repo: No (Replay 07 N5 was unconditional every-night SPY and QQQ).

### S8. Same-half-hour intraday periodicity continuation across trading days (30-minute bars)

- Who is forced to trade and when (`STATED`): Institutional execution schedules and recurring investor flows repeat at the same half-hour intervals across consecutive days, strongest in the opening and closing half-hours. Per [Heston, Korajczyk, and Sadka (2010, Journal of Finance, arXiv version)](https://ar5iv.labs.arxiv.org/html/1005.3535): "We find a striking pattern of return continuation at half-hour intervals that are exact multiples of a trading day, and this effect lasts for at least 40 trading days."
- Source sample dates and vault overlap: [Heston, Korajczyk, and Sadka (2010) Internet Appendix](https://afajof.org/wp-content/uploads/files/supplements/Internet_Appendix_to_Intrada.pdf) sample is January 2001 through December 2005. NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: Mean return of a stock in the exact same 30-minute interval (09:30 to 10:00 or 15:30 to 16:00) over the prior `L = 1`, `3`, `5`, or `10` trading days (4 lookbacks) ranks in the top cross-sectional decile or exceeds `+0.30%` per bar.
- Entry and exit print on `$500`: Buy at the open of that 30-minute bar (e.g., 15:30 open); sell at the close of that bar (15:59 close).
- Already scored in repo: No.

### S9. Cross-sectional intraday arbitrageur de-risking before close into overnight rebound

- Who is forced to trade and when (`STATED`): Higher overnight margin requirements and overnight stock-lending fees push arbitrageurs to cut positions before the 16:00 ET close, creating late-day selling pressure that rebounds overnight. Per [Bogousslavsky (2021, Journal of Financial Economics)](https://ideas.repec.org/a/eee/jfinec/v141y2021i1p172-194.html): "Margin requirements are higher overnight, and lending fees are typically charged only on positions held overnight. Such institutional constraints and overnight risk incentivize arbitrageurs who trade on mispricing to reduce their positions before the end of the day."
- Source sample dates and vault overlap: [Bogousslavsky (2021)](https://www.scribd.com/document/1047614302/The-Cross-section-of-Intraday-and-Overnight-Returns) sample is January 1, 1986 to December 31, 2015. NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: Stock's 15:55 close sits below its full-day 09:30 to 15:55 VWAP by at least `0.50%`, `1.00%`, `1.50%`, or `2.00%` (4 thresholds) while its 09:30 to 15:55 return ranks in the bottom cross-sectional quintile.
- Entry and exit print on `$500`: Buy at 15:55 close (or 15:59 close); sell at next session 09:35 open or 10:00 open.
- Already scored in repo: No.

### S10. Friday afternoon risk-reduction selloff and Monday rebound

- Who is forced to trade and when (`STATED`): Weekday shifts in institutional risk budgets and retail sentiment generate systematic Friday-versus-Monday cross-sectional return patterns. Per [Birru (2018, Journal of Financial Economics)](https://pubsonline.informs.org/servlet/linkout?suffix=B12&dbid=16&doi=10.1287/mnsc.2020.3803&key=10.1016/j.jfineco.2018.06.008): "Relative to non-speculative stocks, speculative stocks earn low returns on Mondays and high returns on Fridays."
- Source sample dates and vault overlap: Birru (2018) sample is 1963 to 2013 ([Redalyc summary](https://www.redalyc.org/journal/4237/423765204003/html/)). NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: On Friday at 15:55 ET, buy liquid low-volatility or defensive stocks and ETFs (bottom quintile of trailing 20-day realized volatility) or buy stocks with a positive 5-day return that dropped during Friday afternoon (13:00 to 15:55 return at or below `-0.50%`, `-1.00%`, or `-1.50%`, 4 settings total).
- Entry and exit print on `$500`: Buy Friday 15:55 close (or 15:59 close); sell Monday 10:00 open or Monday 15:59 close.
- Already scored in repo: No.

### S11. High-volatility intraday panic-volume flush and liquidity-provision rebound (10:00 to 14:30 ET)

- Who is forced to trade and when (`STATED`): Financially constrained market makers withdraw liquidity during volatility spikes, increasing the short-term reversal return paid to anyone willing to buy into intraday selling flushes. Per [Nagel (2012, Review of Financial Studies)](https://academic.oup.com/rfs/article-abstract/25/7/2005/1602153): "Expected returns and conditional Sharpe ratios from liquidity provision spike during periods of financial market turmoil."
- Source sample dates and vault overlap: Nagel (2012) sample is 1998 to 2010 (including the 2007 to 2009 crisis). NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: Between 10:00 and 14:30 ET, a 30-minute bar drops at or below `-1.5%`, `-2.0%`, or `-3.0%` (3 thresholds) on bar volume at least `3.0x` or `5.0x` trailing 20-day same-bucket median, gated on trailing 5-day realized volatility above its trailing 60-day median.
- Entry and exit print on `$500`: Buy next 5-minute open after the flush bar; sell after 30, 60, or 120 minutes (or 15:55 close).
- Already scored in repo: No.

### S12. Month-end and quarter-end closing-minute equity window-dressing loser fade

- Who is forced to trade and when (`STATED`): Hedge funds and mutual funds trade aggressively in the final minutes of month-end and quarter-end sessions to dress up reported holdings (buying winners and dumping losers), with reversals on the next trading day. Per [Ben-David, Franzoni, Landier, and Moussawi (2013, Journal of Finance)](https://onlinelibrary.wiley.com/doi/10.1111/jofi.12062): "Stocks in the top quartile of hedge fund holdings exhibit abnormal returns of 0.30% on the last day of the quarter and a reversal of 0.25% on the following day. A significant part of the return is earned during the last minutes of trading."
- Source sample dates and vault overlap: Ben-David et al. (2013) covers 2000 to 2010. NO overlap with stock vault (`2022-01-03` to `2026-10-30`).
- Bar-only signal and settings: On the last trading day of each month (or quarter), buy liquid stocks or equity sector ETFs sold down sharply in the final hour (15:00 to 15:55 return at or below `-0.75%`, `-1.00%`, `-1.50%`, or `-2.00%`, 4 thresholds, on volume at least `1.5x` median).
- Entry and exit print on `$500`: Buy month-end 15:55 close (or 15:59 close); sell first trading day of the new month at 10:00 open or 15:59 close.
- Already scored in repo: No (Replays 25, 31, 41, and 52 tested bond ETFs and SPY-vs-TLT, never equity single-stock or sector-ETF window-dressing fades).

## Plan 70: 12 Mechanism Families for US Two-Way Coins (Hourly Bars)

All 12 families allow both long and short trades on US-tradable coins via Coinbase CFM perpetual-style futures (judged cost in `docs/research/120_round_31_cfm_futures_cost_rescreen.md`, with US spot long leg shown beside it), use hourly OHLCV bars alone, and carry 3 to 6 natural parameter settings. Vault dates to check for overlap: `2024-01-01` to `2026-10-31`.

### C1. Global 8-hour perpetual funding-stamp micro-window snapback (00:00, 08:00, 16:00 UTC)

- Who is forced to trade and when (`STATED`): Global perpetual futures venues exchange funding every 8 hours on a fixed UTC clock, concentrating entry and exit flows immediately before and after each stamp. Per [Binance Futures Funding Rates FAQ](https://www.binance.com/en/support/faq/detail/360033525031): "The default funding interval is every 8 hours at 00:00 (UTC), 08:00 (UTC), and 16:00 (UTC)."
- Source sample dates and vault overlap: Exchange rule documentation (no empirical sample). NO overlap with coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: In the hour ending at a funding stamp (`23:00` to `00:00`, `07:00` to `08:00`, or `15:00` to `16:00` UTC), absolute 1-hour return at least `1.0%`, `1.5%`, `2.0%`, or `3.0%` (4 thresholds) on volume at least `1.5x` trailing 24-hour median -> fade the stamp-hour move (short after up-push, long after down-push).
- Entry and exit print on `$500`: Enter on Coinbase CFM futures at `00:00`, `08:00`, or `16:00` UTC hourly open; exit after 1, 2, or 4 hours.
- Already scored in repo: No (Replays 18 and 24 tested multi-day funding-rate carry, never hourly funding-stamp price snapbacks).

### C2. Hourly liquidation-cascade flush reversal (both ways)

- Who is forced to trade and when (`STATED`): Leveraged perpetual positions breaching maintenance margin are automatically liquidated by exchange engines, amplifying sharp 1-to-2-hour moves into temporary overshoots on both sides. Per [Soska, Dong, Khodaverdian, Zetlin-Jones, Routledge, and Christin (2021, WWW '21)](https://dl.acm.org/doi/fullHtml/10.1145/3442381.3450059): "When a trader's equity value fall below the maintenance margin requirement, her position is liquidated by the exchange and she receives zero."
- Source sample dates and vault overlap: Soska et al. (2021) sample is January 2017 to February 2021. NO overlap with coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: 1-hour or 2-hour absolute return at least `2.5x`, `3.5x`, or `4.5x` trailing 48-hour ATR (3 thresholds) AND bar volume at least `3.0x` or `5.0x` trailing 48-hour median hourly volume (2 volume gates); go long after a downward flush and short after an upward short-squeeze flush.
- Entry and exit print on `$500`: Enter next hourly open on CFM futures (both ways) or US spot (long leg only); exit after 2, 4, or 8 hours.
- Already scored in repo: No (Replay 09 CAP was daily-bar, long-only, BTC-only; Row 28 was never scored).

### C3. CME CF Reference Rate daily 1-hour fixing window post-fix reversal (BRR and BRRNY)

- Who is forced to trade and when (`STATED`): Institutional futures hedgers and US spot-ETF Authorized Participants execute 1-hour TWAP baskets during the daily CME CF BRR (15:00 to 16:00 London) and BRRNY (15:00 to 16:00 New York) calculation windows, creating directional fixing pressure that can revert afterward. Per the [CME CF Bitcoin Reference Rate Methodology Guide](https://www.cmegroup.com/trading/files/bitcoin-reference-rate-methodology.pdf): "Aggregation of trade executions occurring on Constituent Exchanges between 3:00 p.m. and 4:00 p.m. London time". Per the [CFTC BRRNY filing](https://www.cftc.gov/sites/default/files/filings/ptc/24/09/ptc0910245748.pdf): "It represents the aggregate executed trade flow on major cryptocurrency spot exchanges during a specific calculation window; 3:00 p.m. - 4:00 p.m. New York time."
- Source sample dates and vault overlap: Benchmark methodology and regulatory filings (no empirical sample). NO overlap with coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: During the fixing hour (`15:00` UTC or `20:00` UTC), absolute 1-hour return at least `0.75%`, `1.25%`, or `2.00%` (3 thresholds) on volume at least `1.5x` trailing 20-day same-hour median -> fade the fixing-hour imbalance (short after up-fix, long after down-fix).
- Entry and exit print on `$500`: Enter at `16:00` UTC or `21:00` UTC hourly open on CFM futures; exit after 1, 2, or 4 hours.
- Already scored in repo: No (Replay 35 tested monthly IBIT expiry only; Plan 58 was unconditional `21:00` to `23:00` UTC BTC and closed on costs before prices).

### C4. US equity cash-open (14:00 UTC) and cash-close (20:00 UTC) cross-asset hedging handover

- Who is forced to trade and when (`STATED`): Cross-asset desks and spot crypto ETF market makers concentrate hedging flows around NYSE open and close hours, driving common intraday periodicity across major coins. Per [Intraday and Daily Dynamics of Cryptocurrency (IRFA 2024)](https://www.sciencedirect.com/science/article/pii/S1059056024006506): "We show that native cryptocurrencies and tokens share common intraday periodicity determined by the operating times of the NYSE, LSE and Hang Seng stock exchange markets." Per [Kaiko (2024)](https://www.kaiko.com/resources/btc-etfs-impact-on-spot-market-structure): "During weekdays, the US market close accounts for over 6.6% of all trading volume on benchmark exchanges."
- Source sample dates and vault overlap: FLAG: Kaiko (2024) covers 2024 post-ETF data, OVERLAPPING the coin vault (`2024-01-01` to `2026-10-31`). IRFA (2024) uses pre-2024 Bitstamp hourly data.
- Bar-only signal and settings: On weekdays only, when the `13:00` to `15:00` UTC (US open) or `19:00` to `21:00` UTC (US close) 2-hour move exceeds `1.5%`, `2.5%`, or `3.5%` in magnitude (3 thresholds) on elevated volume, test continuation and reversal over 2, 4, or 6 hours.
- Entry and exit print on `$500`: Enter at `15:00` UTC or `21:00` UTC hourly open on CFM futures; exit 2, 4, or 6 hours later.
- Already scored in repo: No.

### C5. Friday Coinbase CFM maintenance halt and CME weekend close-to-reopen gap

- Who is forced to trade and when (`STATED`): Coinbase CFM perpetual-style futures halt for 1 hour every Friday from 17:00 to 18:00 ET, and CME Bitcoin futures historically closed Friday 16:00 CT through Sunday 17:00 CT, forcing institutional hedgers to square before Friday close and re-hedge Sunday evening. Per [Coinbase Perpetual-Style Futures Contract Specifications](https://help.coinbase.com/en/derivatives/perpetual-style-futures/contract-specifications): "The contracts trade continuously, 24 hours a day, 7 days a week, with the exception of a 1 hour maintenance period on Fridays from 5pm - 6pm ET." Per [CME Bitcoin Futures Contract Specifications](https://www.cmegroup.com/trading/bitcoin-futures.html%20.html): "CME Globex: Sunday - Friday 6:00 p.m. - 5:00 p.m. ET (5:00 p.m. - 4:00 p.m. CT) with a 60-minute break each day beginning at 5:00 p.m. ET (4:00 p.m. CT)".
- Source sample dates and vault overlap: Exchange contract specifications (no empirical sample). NO overlap with coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: Cumulative weekend return from Friday `21:00` UTC to Sunday `21:00` UTC at least `+2.0%` or `+4.0%` (short into Sunday `22:00` UTC reopen) or at or below `-2.0%` or `-4.0%` (long into Sunday `22:00` UTC reopen), 4 settings.
- Entry and exit print on `$500`: Enter Sunday `22:00` UTC hourly open on CFM futures (outside Friday maintenance halt); exit Monday `02:00`, `06:00`, or `14:00` UTC open.
- Already scored in repo: No (Replay 09 WKND held BTC unconditionally all weekend; Replay 19 tested Monday Asia trend).

### C6. Weekend thin-book hourly overshoot reversal (Sat 00:00 UTC to Sun 21:00 UTC)

- Who is forced to trade and when (`STATED`): Institutional market makers step back on weekends when fiat rails and ETFs are closed, shrinking weekend volume share and leaving thin order books prone to temporary overshoots. Per [Kaiko (2024)](https://marketing.kaiko.com/bitcoins-dwindling-volatility-signals-maturity): "This trend has been ongoing for six years, with the share of BTC traded on weekends dropping from 28% in 2019 to 20% in 2023."
- Source sample dates and vault overlap: The 2019 to 2023 decline is pre-vault; FLAG: the same Kaiko report also cites a 2024 figure (`16%`), OVERLAPPING the coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: Restricted to Saturday `00:00` UTC through Sunday `20:00` UTC, a 2-hour or 4-hour return magnitude at least `2.0%`, `3.0%`, or `4.5%` (3 thresholds) on volume at least `2.0x` trailing 72-hour median -> fade (short up-spike, long down-spike).
- Entry and exit print on `$500`: Enter next hourly open on CFM futures (both ways); exit after 2, 4, or 8 hours.
- Already scored in repo: No (Replay 09 WKND was unconditional long-only BTC).

### C7. Cross-sectional hourly idiosyncratic dislocation reversal (long worst laggard, short biggest outlier)

- Who is forced to trade and when (`STATED`): Common market flow drives about 80% of BTC returns, while idiosyncratic signed-volume shocks create temporary relative-price dislocations that mean-revert across venues and pairs. Per [Makarov and Schoar (2020, Journal of Financial Economics)](https://ideas.repec.org/a/eee/jfinec/v135y2020i2p293-319.html): "The common component explains 80% of bitcoin returns." and ([LSE manuscript PDF](http://eprints.lse.ac.uk/100409/1/Cryptocurrency_Markets_JFE_final_v4.pdf)): "When the price on any exchange deviates above (below) from the average price on other exchanges, subsequent returns on this exchange are predicted to be lower (higher) than the returns on other exchanges."
- Source sample dates and vault overlap: Makarov and Schoar (2020) sample is 2017 to 2018. NO overlap with coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: Every 2 hours or 4 hours, compute each US-tradable coin's trailing 2-hour or 4-hour return minus the cross-sectional median; go long coins with residual at or below `-2.0%`, `-3.0%`, or `-4.0%` and short coins with residual at least `+2.0%`, `+3.0%`, or `+4.0%` (3 thresholds) when bar volume is at least `1.5x` median.
- Entry and exit print on `$500`: Enter next hourly open on CFM futures (both ways); exit after 2, 4, or 8 hours.
- Already scored in repo: No (Replay 09 REV was daily-bar and long-only).

### C8. Medium-frequency (1h, 2h, 4h) negative autocorrelation and climax-wick blow-off reversal

- Who is forced to trade and when (`STATED`): Unlike liquid equities and FX where microstructure reversal ends in minutes, Bitcoin exhibits statistically significant negative first-order autocorrelation at 1-hour (`-0.0557`), 2-hour (`-0.0858`), and 4-hour (`-0.0564`) horizons as momentum chasers exhaust marginal liquidity. Per [Ledger (2021, On the Intraday Behavior of Bitcoin)](https://ledgerjournal.org/ojs/ledger/article/download/213/212/1232): "In particular, our most interesting finding is the unusual presence of significant negative first-order autocorrelation of returns calculated on medium-frequency timeframes, such as one, two and four hours, signaling the presence of systematic mean reversion."
- Source sample dates and vault overlap: Pre-2021 Bitcoin intraday sample. NO overlap with coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: Trailing 2-hour or 4-hour cumulative move at least `+3.0%`, `+5.0%`, or `+7.0%` (short) or at or below `-3.0%`, `-5.0%`, or `-7.0%` (long) (3 thresholds) where the final hourly bar has volume at least `2.5x` median and closes in the opposite half of its high-low range (rejection wick).
- Entry and exit print on `$500`: Enter next hourly open on CFM futures (both ways); exit after 2, 4, or 6 hours.
- Already scored in repo: No (Replay 03 tested standard chart indicators on BTC and ETH only).

### C9. Hourly volatility-compression stop-cluster breakout (both ways)

- Who is forced to trade and when (`STATED`): Crypto hourly volatility is strongly clustered and periodic across day-of-week and hour-of-day; tight range compression clusters resting stop orders just outside the channel, so a high-volume break triggers cascaded stop-fills. Per [Hansen, Kim, and Kim (2021, arXiv 2109.12142)](https://arxiv.org/html/2109.12142): "We find systematic patterns in both volatility and volume across day-of-the-week, hour-of-the-day, and within the hour."
- Source sample dates and vault overlap: Hansen et al. (2021) sample is October 1, 2020 to May 31, 2021. NO overlap with coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: Trailing 12-hour or 24-hour realized range sits in the bottom `15%` or `25%` of its trailing 168-hour (7-day) distribution, followed by an hourly close outside that 12-hour or 24-hour high-low channel on volume at least `2.0x` or `3.0x` median (4 settings); long on upside break, short on downside break.
- Entry and exit print on `$500`: Enter next hourly open on CFM futures (both ways); exit after 4, 8, or 12 hours.
- Already scored in repo: No (Replay 22 was daily-bar long-only range-break).

### C10. Rolling-24h VWAP anchor mean-reversion during non-trending hours (both ways)

- Who is forced to trade and when (`STATED`): Institutional execution algorithms slice orders on full-hour and quarter-hour clocks benchmarked to rolling VWAP, absorbing non-breakout price deviations back toward the anchor. Per [Watorek et al. (2023, Chaos, arXiv 2306.17095)](https://arxiv.org/html/2306.17095v2): "One such pattern involves the amplified market activity precisely at full hours, and a couple of more subtle patterns involve similar effects at full quarters and half-hours."
- Source sample dates and vault overlap: Watorek et al. (2023) sample is January 2020 to December 2022. NO overlap with coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: Hourly close deviates from trailing 24-hour VWAP by at least `1.5`, `2.0`, `2.5`, or `3.0` trailing 24-hour hourly return standard deviations (4 thresholds), filtered to exclude fresh 72-hour highs or lows; short above VWAP, long below VWAP.
- Entry and exit print on `$500`: Enter next hourly open on CFM futures (both ways); exit on return to 24-hour VWAP or after 4 or 8 hours.
- Already scored in repo: No.

### C11. Cross-coin BTC-beta over-extension snapback (both ways, hourly)

- Who is forced to trade and when (`STATED`): A dominant market factor drives cross-coin returns, with hourly BTC-ETH correlation between `0.802` and `0.823`; during sharp 1-to-2-hour BTC moves, thinner US-tradable altcoins frequently overshoot their beta and snap back. Per [Liu, Tsyvinski, and Wu (2022, Journal of Finance, NBER w25882)](https://www.nber.org/system/files/working_papers/w25882/w25882.pdf): "We find that three factors – cryptocurrency market, size, and momentum – capture the cross-sectional expected cryptocurrency returns." Per [Hansen et al. (2021)](https://arxiv.org/html/2109.12142): "We also observe that Bitcoin and Ether returns are very correlated, both within and across centralized exchanges, with correlations varying between 0.802 and 0.823."
- Source sample dates and vault overlap: Liu et al. (2022) covers pre-2019; Hansen et al. (2021) covers October 2020 to May 2021. NO overlap with coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: When absolute 2-hour BTC return is at least `1.5%` or `2.5%`, short US-tradable altcoins whose 2-hour return exceeds `2.0x` or `2.5x` BTC's up-move, or go long altcoins whose 2-hour drop exceeds `2.0x` or `2.5x` BTC's down-move (4 settings).
- Entry and exit print on `$500`: Enter next hourly open on CFM futures (both ways); exit after 2, 4, or 6 hours.
- Already scored in repo: No (Replay 09 LEAD bought lagging altcoins long-only; never tested fading beta over-extensions both ways).

### C12. Salient UTC-midnight (00:00 UTC) daily-candle close stop-run and reversal (both ways)

- Who is forced to trade and when (`STATED`): Algorithmic trading surges at salient clock boundaries (full hours and daily resets), generating phase-specific negative autocorrelation across boundary transitions as daily-candle close bots execute clustered market orders. Per [The Quarter-Hour Effect (arXiv 2607.09426v2)](https://arxiv.org/html/2607.09426v2): "Trading activity exhibits a nested intrahour structure, with bursts at one-minute, five-minute, quarter-hour, and hourly boundaries that become more pronounced at more salient clock times".
- Source sample dates and vault overlap: Watorek et al. (2023) covers January 2020 to December 2022 (NO overlap). FLAG: arXiv 2607.09426v2 uses 2025 to 2026 Binance perpetual trade data, OVERLAPPING the coin vault (`2024-01-01` to `2026-10-31`).
- Bar-only signal and settings: In the `23:00` to `00:00` UTC bar (daily-candle close), absolute 1-hour return at least `1.0%`, `1.5%`, or `2.5%` (3 thresholds) AND the bar prints a new 24-hour high (short) or new 24-hour low (long) on volume at least `1.5x` trailing 24-hour median -> fade the daily-close stop-run.
- Entry and exit print on `$500`: Enter at `00:00` UTC hourly open on CFM futures (both ways); exit at `02:00`, `04:00`, or `06:00` UTC open.
- Already scored in repo: No.
