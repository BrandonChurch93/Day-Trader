# Idea Round 46: High-Payoff-Against-Cost Rules on a $500 US Account

Date: 2026-11-26 15:13 UTC
Status: COMPLETE. Zero candidates clear the Round 46 line. Zero queue rows added (rows from 120 stay unused).

## Verdict

Zero candidates clear all five Round 46 gates. Every unexplored US stock, US ETF (including leveraged ETFs), and US spot crypto rule audited from directly opened post-2018 primary sources fails at least one required gate: the 33% one-sided 5% normal power line at half the net mean from printed figures, the 150 independent post-2016 trade-date floor, the 10x round-trip cost floor, or the post-2018 evidence requirement. No queue rows are opened; all screened rules are added to the Round 46 skip list in `docs/QUEUE.md`.

## Fixed Cost Baselines and Round 46 Gates

Cost baselines used for every net-mean calculation:

- Broad US equity ETFs (`DIA`, `IWM`, `QQQ`, `SPY`, `VTI`): MEASURED in `docs/research/136_measured_stock_trading_costs.md` at 0.210 bp per side regular-hours median (0.420 bp round trip; 10x = 4.20 bp) and 0.684 bp round trip in the first 30 minutes (10x = 6.84 bp).
- Gold ETF (`GLD`): MEASURED in `docs/research/136_measured_stock_trading_costs.md` at 0.399 bp per side (0.798 bp round trip; 10x = 7.98 bp).
- Sector ETFs (11) and long Treasury ETF (`TLT`): MEASURED in `docs/research/136_measured_stock_trading_costs.md` at 1.174 bp and 1.220 bp round trip regular-hours median (10x = 11.74 to 12.20 bp).
- Single US stocks (38 liquid names): MEASURED in `docs/research/136_measured_stock_trading_costs.md` at 1.668 bp per side regular-hours median (3.336 bp round trip; 10x = 33.36 bp), 7.574 bp round trip in the first 30 minutes, 9.882 bp pooled p90 round trip, and 10.0 bp round-trip replay allowance (10x = 100.0 bp).
- Leveraged and inverse US ETFs (`TQQQ`, `UPRO`, `SOXL`, `SVXY`): UNKNOWN in `docs/research/136_measured_stock_trading_costs.md` (not in the 56-symbol sample).
- Spot crypto on Coinbase or Kraken: STATED by the lead at 80 to 120 bp round trip (10x = 800 to 1,200 bp, or +8% to +12% gross per trade).
- Account limits: STATED in repo records as a $500 US account (Alpaca 1x buying power limited margin below $2,000, no single-stock shorting; Coinbase or Kraken spot long-only).

Power formula used from printed figures only:

- Spread per trade = printed mean / printed t * sqrt(printed n).
- Net mean = printed gross mean minus our round-trip cost.
- One-sided 5% normal power at half the net mean = 1 - Phi(1.6448536 - (0.5 * net mean) / (spread per trade / sqrt(our independent dates))).
- Clearing 33% power requires t at full net mean of at least 2.41 on independent trade dates. Where a paper prints no per-trade spread, or clusters many same-day events without a date-clustered spread, power is marked UNKNOWN rather than guessed.

## Ranked Table of Screened Candidates (0 of 6 Pass)

| Rank | Candidate and market | Free dated signal | Gross gain vs 10x RT cost | Independent dates since 2016 and newest OOS | Printed power at half net mean (one-sided 5%) | Result and one-line failure reason |
|---|---|---|---|---|---|---|
| 1 | NYSE single-day -10% drop 3-day reversal (US single stocks, long-only) | Alpaca daily close-to-close bar on NYSE stocks | STATED +153.4 bp CAR(1,3) measured from the same event-day close that sets the -10% trigger (next-open figure UNKNOWN) | STATED n = 452 events (2020-03-11 to 2022-06-30); independent dates UNKNOWN (clustered in COVID crash) | STATED 29.85% at 10 bp RT, 31.67% at 3.336 bp RT, 32.60% at zero cost (unclustered); date-clustered power UNKNOWN, likely lower if same-day trades move together | FAIL: falls below 33% power even at zero cost if all 452 events were independent, CAR starts from the trigger close with next-open UNKNOWN, and date-clustered power is UNKNOWN |
| 2 | U-shaped implied-volatility regime switch on SPY, QQQ, DIA to IEF (US equity ETFs, long-only) | Cboe daily VIX, VXN, VXD and Alpaca ETF closes | STATED SPY Risk-On +5.63 bp/day vs Risk-Off -9.00 bp/day (diff 14.63 bp/day; per-trade gross UNKNOWN) | STATED 2000 to 2024 (no post-2018-only OOS printed); 6% to 12% is days in the risk-off state, not switches; independent date count UNKNOWN | UNKNOWN (no trade count or per-trade spread printed; full-sample SPY vs BnH t = 1.7801) | FAIL: independent switch-date count is UNKNOWN (6% to 12% is risk-off day share, not transitions), lacks a post-2018 OOS split, and prints no per-trade spread |
| 3 | Month-end payment-cycle time-series reversal on S&P 500 (US equity ETF, long-only) | Alpaca SPY fourth-Friday to month-end close return | STATED OOS annualized excess 4.600% (4.112% net vs 3.786% passive); per-trade gross UNKNOWN | STATED 1986 to 2020 OOS (414 months, active 41% of months; ~54 post-2016 dates is an extrapolation, exact post-2016 count UNKNOWN) | UNKNOWN (no per-trade mean or spread printed; predictive slope t = -3.276) | FAIL: monthly rule active ~41% of months (~54 dates since 2016 is an extrapolation, well below 150) and prints no per-trade spread |
| 4 | US equity ETF after-hours drop <= -5% next-session rebound (US ETFs, long-only) | Alpaca extended-hours and regular-session bars | STATED +141 bp measured from the same official open that defines the -5% event (not executable; next-executable-mark figure UNKNOWN) | STATED 2007 to 2014 ONLY (6,445 events across 847 ETFs; zero post-2018 evidence; independent dates UNKNOWN) | UNKNOWN (event-level t = 16.70 ignores same-morning ETF clustering; zero post-2018 data) | FAIL: sample ends December 2014 with zero post-2018 evidence, +141 bp starts at the trigger open (not executable), and date-clustered spread is UNKNOWN |
| 5 | Walk-forward cost-aware XGBoost long-only Bitcoin (US spot crypto, long-only) | Free hourly BTC OHLCV bars | STATED 65.40% ARC over 251 trades at 10 bp/side Binance futures; data provenance unverified; per-trade gross UNKNOWN | STATED 2018-01-01 to 2026-01-01 (27 quarterly OOS folds, 251 trades >= 150) | UNKNOWN (no per-trade mean or SD printed; Sharpe diff vs Buy-and-Hold +0.27, Holm p = 0.89) | FAIL: does not beat Bitcoin buy-and-hold (Holm p = 0.89), data provenance is unverified (cites Dec 2017 Binance USD-M futures before launch), uses 10 bp futures costs, and prints no per-trade spread |
| 6 | US spot crypto weekly factor spreads on Coinbase and Kraken (US spot coins) | Free public Coinbase and Kraken spot bars | STATED top weekly 5-1 long-short spreads 120 to 160 bp (fails 800 to 1,200 bp 10x coin RT) | STATED 2018 to 2022 across US spot exchanges including Coinbase and Kraken | UNKNOWN (no long-only per-trade t printed; weekly spreads require shorting unavailable on spot) | FAIL: weekly gross spreads are 5x to 10x below the 10x Coinbase/Kraken round-trip cost floor and rely on a short leg |

## Detailed Evidence, Verbatim Quotes, and Power Sums

### 1. NYSE Single-Day -10% Drop 3-Day Reversal

Source opened: [Erasmus University Rotterdam Master Thesis (2023)](https://thesis.eur.nl/pub/66674/20230814-Master-Thesis.pdf).

Verbatim quotes carrying the numbers:

- Sample period (STATED): "The research period of this paper is from 11/03/2020 to 30/06/2022."
- Sample size and trigger (STATED): "Many outliers of these variables were clustered at the same event, resulting in only losing 14 observations for both samples, resulting in 452 observations for losers and 514 for winners." "N corresponds to the total number of events determined by a trigger strategy that uses -10% for losers and 10% for winners as triggers."
- Table 3 (-10% loser trigger, STATED): AR(1) = "0.835%*" with t-statistic "[1.843]"; CAR(1,3) = "1.534%**" with t-statistic "[2.388]".

Power sum from printed figures (Python verified):

- Execution mark: CAR(1,3) starts from the same event-day closing mark that sets the -10% trigger, so no practical fill is shown and a next-open figure is UNKNOWN.
- Printed n = 452 events (STATED; independent trade-date count UNKNOWN because many NYSE stocks dropped 10% on the same March 2020 crash dates).
- Printed gross mean = +153.4 bp (STATED); printed t = 2.388 (STATED).
- Implied spread per event = 153.4 / 2.388 * sqrt(452) = 1,365.72 bp (SE = 64.24 bp).
- At zero cost: half gross mean = 76.70 bp, t at half gross mean = 1.1940, one-sided 5% power = 32.60% (< 33%).
- At 10.0 bp single-stock replay allowance (MEASURED in doc 136): net mean = 143.40 bp, half net mean = 71.70 bp, t at half net mean = 1.1162, one-sided 5% power = 29.85% (< 33%).
- At 3.336 bp single-stock regular-hours median RT (MEASURED in doc 136): net mean = 150.064 bp, half net mean = 75.032 bp, t at half net mean = 1.1680, one-sided 5% power = 31.67% (< 33%).
- Date-clustered power across true independent dates: UNKNOWN, likely lower if same-day trades move together.

One-line failure reason: Fails the 33% power line even at zero cost under the unclustered event count (32.60%), CAR starts from the trigger close with next-open UNKNOWN, and date-clustered power is UNKNOWN, likely lower if same-day trades move together.

### 2. U-Shaped Implied-Volatility Regime Switch on SPY, QQQ, and DIA to IEF

Source opened: [Economics Bulletin Vol. 45, Issue 4 (2025)](http://www.accessecon.com/Pubs/EB/2025/Volume45/EB-25-V45-I4-P167.pdf).

Verbatim quotes carrying the numbers:

- Rule and asset switch (STATED): "Risk-On: Volatility is below the 'middle' threshold; the portfolio is fully invested in equities." "Risk-Off: Volatility exceeds the 'middle' but remains below the 'upper' threshold; the portfolio switches to bonds (IEF)." "Re-entry: Volatility either exceeds the 'upper' threshold or falls below the long-term average; equity exposure resumes."
- Sample and daily differential (STATED): "We use daily data from 2002 to 2024 on three ETF–volatility index pairs: SPY–VIX, QQQ– VXN, and DIA–VXD." "For example, SPY exhibits a daily return of –0.09% in Risk-Off states, compared to 0.0563% in Risk-On states." "The two-sample t-statistic for SPY equals –2.1822 and is statistically significant at the 5% level, indicating that the return differential is not due to random variation."
- Trade frequency (STATED): "The market-exit ratios of 6 to 12% imply only a few portfolio reallocations per year."

Power sum from printed figures:

- Independent trade dates since 2016: UNKNOWN. The 6% to 12% market-exit ratios measure the share of days spent in the risk-off state, not regime-switch counts; the paper states "only a few portfolio reallocations per year" without printing any switch or trade count.
- Per-trade gross mean and per-trade spread: UNKNOWN (not printed; full-sample strategy vs buy-and-hold return t-statistics are 1.7801 for SPY, 1.2145 for QQQ, and 2.2806 for DIA with no post-2018-only OOS table).
- Power at half net mean: UNKNOWN.

One-line failure reason: Independent switch-date count is UNKNOWN (the 6% to 12% figures are risk-off day shares, not transitions), no post-2018 out-of-sample split is printed, and per-trade spread is UNKNOWN.

### 3. Month-End Payment-Cycle Time-Series Reversal on S&P 500

Source opened: [American Finance Association working paper, Time Series Reversal: A Payment Cycle Friction](https://afajof.org/management/viewp.php?n=133448).

Verbatim quotes carrying the numbers:

- Rule and activity rate (STATED): "The TSR trading strategy consists of buying the S&P 500 if the last week of the month has a negative return and holding the asset for the next month." "To capture only the negative price pressure due to the payment cycle, the time series reversal portfolio invests on the risky asset only when the last week return of month t (r_t^{w=4}) is negative (around 40% of times)." "Moreover, the portfolio constructed using the time series reversal trading strategy dominates the others also in terms of Sharpe ratio, variance, and kurtosis as it sensibly reduces market exposure, being active only 41% of the time."
- OOS period (STATED): "The Out-of-Sample forecast evaluation period goes from July 1986 to December 2020 (75% of the entire sample for a total of 414 OOS point forecasts)."

Power sum from printed figures:

- Independent trade dates since 2016: exact post-2016 count is UNKNOWN (the paper's OOS window ends December 2020); ~54 dates from 2016 through 2026 is an extrapolation from a monthly rule active 41% of months (~5 dates per year), which still falls well below the 150-date floor.
- Printed OOS strategy annualized excess return is 4.600% (Sharpe 0.439, annualized SD 10.5%; net of 10 bp/month fees 4.112% vs passive 3.786%). Main predictive regression slope is -0.327 (Newey-West t = -3.276), and retail tracker covers January 2016 to January 2023.
- Per-trade mean and per-trade spread: UNKNOWN (not printed); power at half net mean: UNKNOWN.

One-line failure reason: Monthly frequency active 41% of the time (~54 dates since 2016 is an extrapolation, well below 150) and prints no per-trade spread.

### 4. US Equity ETF After-Hours Drop <= -5% Next-Session Reversal

Source opened: [Revista Contabilidade e Financas (2019)](https://www.scielo.br/j/rcf/a/dN4R3PXxcJcC7B9fvSV58kC/?format=pdf&lang=en).

Verbatim quotes carrying the numbers:

- Sample (STATED): "Our sample comprises observations of daily opening and closing prices for all the NYSE-traded equity ETFs between January 2007 and December 2014. Daily price data covering the 847 ETFs were obtained from the Bloomberg database."
- Table 2, Panel B, trigger level <= -5% (STATED): "(N = 6445)", next normal-hours return "1.41%", t-statistic "(16.70)***".

Power sum from printed figures:

- Execution mark: the +141 bp next normal-hours return is measured from the same official open that defines the after-hours -5% event, so it is not an executable rule and any next-executable-mark return is UNKNOWN.
- Newest out-of-sample date: December 2014 (zero post-2018 evidence).
- Independent trade dates since 2016: UNKNOWN (6,445 events across 847 equity ETFs over 8 years are heavily clustered on market-wide gap-down mornings).
- Date-clustered spread and power at half net mean: UNKNOWN.

One-line failure reason: Sample ends in December 2014 with zero post-2018 evidence, the +141 bp figure starts at the same official open that defines the event (not executable), and the printed t = 16.70 ignores cross-ETF same-morning clustering.

### 5. Walk-Forward Cost-Aware XGBoost Long-Only Bitcoin

Source opened: [Machine Learning-Based Bitcoin Trading Under Transaction Costs (arXiv:2606.00060, 2026)](https://arxiv.org/html/2606.00060).

Verbatim quotes carrying the numbers:

- Sample and market (STATED): "The empirical analysis uses hourly OHLCV data for the BTC/USDT USD-margined futures contract collected from Binance through its public REST API." "The raw sample runs from 1 December 2017 to 1 January 2026. The first month is used as a burn-in period for rolling feature construction, so the effective modelling window begins on 1 January 2018."
- Cost assumption (STATED): "Net strategy returns are computed as: ... where c=0.001 denotes the proportional transaction cost per unit of turnover. This corresponds to 10 basis points per position change..."
- Buy-and-hold test (STATED): "None of the reported cost-aware strategies significantly outperforms buy-and-hold in Sharpe-ratio terms after Holm correction." (LO Loss-best CA: 251 trades, ARC 65.40%, ASD 56.22%, Sharpe 1.09; Sharpe diff vs buy-and-hold +0.27, 95% CI [-0.46, 0.95], Holm-adjusted p = 0.89).

Power sum from printed figures:

- Data provenance: unverified. The paper cites hourly Binance USD-margined BTC/USDT futures starting December 1, 2017, before that contract existed (Binance launched its flagship BTC/USDT perpetual futures contract in September 2019), with no spot-to-futures stitching specified.
- Per-trade gross mean and per-trade SD: UNKNOWN (not printed).
- Cost mismatch: STATED 10 bp per side on Binance futures vs 80 to 120 bp round trip on Coinbase or Kraken spot.
- Power at half net mean: UNKNOWN.

One-line failure reason: Fails to beat Bitcoin buy-and-hold (Holm p = 0.89), data provenance is unverified (cites Binance USD-margined futures from December 2017 before that contract existed), assumes 10 bp futures costs instead of 80 to 120 bp US spot costs, and prints no per-trade spread.

### 6. US Spot Crypto Weekly Factor Spreads on Coinbase and Kraken

Source opened: [Empirical Crypto Asset Pricing (arXiv:2405.15716v1, 2024)](https://arxiv.org/html/2405.15716v1).

Verbatim quotes carrying the numbers:

- Sample and US spot venues (STATED): "We obtain hourly crypto asset prices, trading volumes, and market capitalization from Coin Metrics and CoinAPI for 2018-2022, inclusive." "Specifically, we collect these data for all assets with at least four months of trading history and a spot market to USD, USDC, or USDT on one of the following United States exchanges." "Specifically, : Binance US, Bitstamp, Coinbase, Crypto.com, FTX US, Gemini, Kraken, and Kucoin."
- Weekly spreads (STATED): "The time-series average weekly excess return spread (and annualized Sharpe ratios) for the zero-investment long-short strategies are 1.5% (0.78) for two week momentum, 1.2% (0.75) for one month industry momentum, 1.4% (0.87) for two month industry momentum, 1.6% (0.76) for one week beta, 1.2% (0.79) for one month idiosyncratic skewness, and 1.4% (0.76) for one week 5% expected shortfall."

Power sum from printed figures:

- Gross weekly spread: STATED 120 to 160 bp long-short, which is 5x to 10x below the 800 to 1,200 bp (10x) Coinbase and Kraken spot round-trip cost floor, and requires shorting unavailable on spot Coinbase and Kraken.
- Long-only per-trade mean, spread, and power: UNKNOWN.

One-line failure reason: Weekly spreads (120 to 160 bp) are far below the 800 to 1,200 bp 10x US spot coin cost floor and depend on a short leg unavailable on US spot venues.

## Additional Post-2018 Studies Screened and Rejected

- Gold trend-momentum walk-forward ([arXiv:2511.08571, August 2026](https://arxiv.org/html/2511.08571)): STATED CME Gold GC futures ("We implement the strategy on CME Gold (GC) futures, continuous front-month, rolled two business days before first notice"), not `GLD`; contradictory execution timing between Section 4.4 ("Execution timing uses either T+0 (same-day close-to-close) or stressed T+1/T+2 fills") and the later clarification ("filled at t+1 close (T+1 baseline)"); data end September 16, 2025 while the OOS backtest is extended to October 31, 2025; prints 1,282 entries on only 1,132 non-zero exposure days with expected value +2.58 bps per active day and no per-trade mean or SD (power UNKNOWN).
- EIA Weekly Natural Gas Storage Thursday puzzle ([Prokopczuk, Wese Simen, and Wichmann 2021, Energy Journal](https://centaur.reading.ac.uk/90003/1/NG_paper_final_round.pdf)): sample ends December 2018, and the authors' own subsample Table A.3 shows the effect vanished in 2014 to 2018 (-0.05% vs -0.14%, t = 0.46, p = 0.642).
- 24 US ETF calendar rules 2006 to 2026 ([arXiv:2611.03384v1, November 2026](https://arxiv.org/html/2611.03384v1)): tested turn-of-month, first/last 3 days, Monday, Friday, quarter-end, January, and 3rd Friday across `SPY`, `QQQ`, `IWM`, `TLT`, `GLD`, and sector ETFs through May 2026; promoted 0 of 24 candidates out of sample.
- Leveraged ETF timing rules (`TQQQ`, `QLD`, `UPRO`, `SOXL` 200-day MA, golden crosses, `UPRO`/`TMF` rotation, [Finlab 2026](https://finlab.finance/en/blog/leveraged-etf-timing-backtest)): 0 of 7 rules cleared buy-and-hold over 2017 to 2026; 5-minute ORB on `QQQ`/`TQQQ` is already on the Round 38 skip list and requires 49% shorting plus 4x leverage.
- Spot Bitcoin ETF daily flow predictability ([Fabus et al., SSRN 7545019](https://papers.ssrn.com/sol3/Delivery.cfm?abstractid=7545019)) and post-2020 cryptocurrency momentum ([Springer 2025](https://link.springer.com/article/10.1007/s11408-025-00474-9)): zero positive return association once ETF flows are public (already on Round 28 and Round 33 skip lists), and post-July 2020 crypto momentum turned negative and insignificant.
- USPTO patent grant post-announcement drift ([JFQA 2025](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/74B86A36A11CEAB933D828A4C59E0C05/S0022109025101658a.pdf/measuring-the-economic-value-of-an-innovation-when-some-investors-are-inattentive.pdf)): 2000 to 2014 sample only (zero post-2018 evidence), Tuesday grant clustering, and FDA drug drift insignificant.
