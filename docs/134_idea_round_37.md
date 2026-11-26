# Idea Round 37: High-Count Liquid US ETF Effects After Costs and After Publication

Date: 2026-11-26
Scope: US equity and credit ETFs and large US stocks where a rule fires frequently enough to build high statistical power over a 10-to-11-year window (`2016 to 2026`), audited strictly under the Doc 117 pre-data power screen (`N x (net_edge / noise)^2 >= 4`) using only sources that measure size after transaction costs and after publication.
Data baseline: Alpaca SIP daily bars from 2016 already held off-repo; 15-minute bars pullable if needed.
Account baseline: $500 US retail cash account, whole-share long-only (`SPLG`, `QQQ`, `IWM`, `DIA`, `SH`, `IEF`, `TLT`), zero shorting, zero leverage.

## Summary Ruling

Ten candidates were audited: all seven prompted high-count liquid US ETF families plus three fresh additions (Connors `RSI(2) < 10` uptrend pullback, Internal Bar Strength `IBS < 0.20`, and Zarattini, Aziz, and Barbon 2024/2025 Noise-Area `SPY` intraday momentum).

Zero rules that fire hundreds of times a year or every session survived post-publication, after-cost measurement. All seven prompted families fail and are dropped (four were already on the Round 19 skip list or dropped in `docs/QUEUE.md`). Two of the three fresh additions (Zarattini Noise-Area and `IBS < 0.20`) also fail and are dropped.

One fresh candidate clears the strict post-publication, after-cost, and Doc 117 bar and is queued as Row 109:

- **Queue Row 109**: Connors `RSI(2) < 10` uptrend pullback (`Close > SMA(200)`, `RSI(2) < 10`, exit first close above `SMA(5)`) across the 4-ETF liquid US equity index panel (`SPLG`, `QQQ`, `IWM`, `DIA`, long-only cash, daily close-to-close). STATED across three independent 2026 post-publication replications covering 2008 to October 2026, it earns `+47.6` to `+53.2 bps` net per trade (`t = 3.6 to 3.7`) and `+33.6 bps` net excess over every-day entry (`t = 2.4`, 98th to 100th percentile of random draws, global BH `q = 0.005` across 59 holdout tests). Caveat: it fires about 8.5 times per year per ETF and about 16 independent dip-days per year across the 4-ETF panel (~180 independent dip-days over 11 years), not hundreds of times per year. On `SPLG` alone (`N = 94`), total net return clears Doc 117 (`7.96 >= 4`) while excess over every-day entry is borderline (`3.90` at 165 bps SD); the 4-ETF panel clears Doc 117 on excess over every-day entry (`180 x (33.6 / 175)^2 = 6.64 >= 4`) using SIP daily bars already held off-repo.

## Master Audit Table (All 10 Candidates)

| # | Candidate | Skip-List Overlap | Post-Pub Net Edge (STATED) | Obs / Yr (10 to 11 Yr N) | Doc 117 Screen | Data Needed | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | Last-half-hour momentum from first half hour | Round 19 skip list; Replay 07 `N3` and `N8` failed | `-2.30 bps/day` (`t = -5.17`) across `SPY`, `QQQ`, `IWM`, `DIA` (2014 to 2026, 2 bps RT) | ~252/yr (~2,520) | `0.00` (negative) | 15-min SIP bars | DROP |
| 2 | Overnight vs intraday return gap (unconditional and conditioned) | Dropped in `docs/QUEUE.md`; Waiting Row 67 | `-32%` net on `SPY` (1993 to 2020); `2021 to 2025` gap `-1.0 bps/day` (`SPY`), `-0.1 bps/day` (`QQQ`); conditioned `sig_c` 52nd to 63rd pctile of random nights | ~252/yr (~2,520); conditioned ~100/yr | `0.00` (negative / null) | SIP daily bars (held) | DROP |
| 3 | Scheduled macro release days (FOMC, CPI, NFP) | Pre-FOMC on Round 19 skip list | Pre-FOMC with PC fell from `+44.5 bps` to `+9.2 bps` (`SE = 6.9 bps`, insignificant) after 2015; non-PC `-5.1 bps` | ~8 FOMC/yr (~32 total macro/yr; ~320) | `0.66` (`< 4`) | SIP daily bars (held) + public calendar | DROP |
| 4 | Intraday reversal after large opening gaps | Round 19 skip list; Replay 07 tested | `-9.9 pts/yr` vs benchmark (`p = 1.000`, `q = 1.000`, 303 trades, 5 bps/side, 2005 to 2025) | ~15/yr (~165) | `0.00` (negative) | SIP daily / 15-min bars | DROP |
| 5 | Volatility-conditioned next-day rules (`VIX` term structure, `VVIX`, gamma, VRP) via `SPY` or `SH` | Gamma on Round 19 skip list; VIX SOQ on Round 20 | `VIX9D > VIX`, `VIX > VIX3M`, `VVIX`, and gamma predict next-day range, not direction (no `|t| > 1.5` after 2 bps RT, 2019 to 2026); VRP requires shorting options | ~17 to 100/yr | `0.00` (null) | SIP daily bars (held) + Cboe VIX family | DROP |
| 6 | End-of-day rebalancing / closing-auction imbalance with public data | Round 19 skip list (15:50 ET MOC and closing-auction flows) | Closing prices match pre-close bid or ask with lower impact than continuous trading; exchange imbalance feeds are paid proprietary feeds | ~252/yr (paid feed) | `0.00` (paid-data wall) | Paid NYSE/Nasdaq imbalance feeds (not in SIP) | DROP |
| 7 | Cross-ETF lead-lag (`HYG` credit leading `SPY`) | New check | Wrong sign at every horizon (4-wk `-19.6 bps`, `t = -1.70`; 1-wk `t = -1.58`); `SPY` vs `IEF` overlay net Sharpe `0.644` vs `0.645` buy-and-hold (`0.569` at 5 bps/leg) | ~252 daily / 52 weekly | `0.00` (wrong sign) | SIP daily bars (held) | DROP |
| 8 | Zarattini, Aziz, and Barbon (2024/2025) Noise-Area `SPY` intraday momentum | Fresh addition | OOS (May 2024 to Mar 2026) Sharpe fell from `1.34` to `0.39` (`p < 0.001`), returning `4.8%/yr` vs SPY buy-and-hold; requires up to 4x leverage and shorting | ~252/yr (~2,520) | `1.52` (`< 4` at 1x cash) | 15-min/30-min SIP bars; needs margin/leverage | DROP |
| 9 | Internal Bar Strength (`IBS < 0.20`) next-day mean reversion | Fresh addition | Mixed: `+16.2 bps` (`t = 2.3`, descriptive, not drift-adjusted) in KruegerAlgorithms 2019 to 2026 holdout, vs `-4.7 pts/yr` vs benchmark (`p = 1.000`, `q = 1.000`, 557 trades at 5 bps/side) in Tickfloor 2005 to 2025 | ~50/yr (~550) | `0.00` (contradicted) | SIP daily bars (held) | DROP |
| 10 | Connors `RSI(2) < 10` uptrend pullback (`SPLG`, `QQQ`, `IWM`, `DIA`) | Fresh addition | `+47.6` to `+53.2 bps` net (`t = 3.6 to 3.7`); `+33.6 bps` excess over every-day entry (`t = 2.4`, 98th to 100th pctile random, `q = 0.005`) across 3 independent 2026 replications | ~8.5/yr per ETF (~16 independent dip-days/yr across 4 ETFs; ~180 in 11 yrs) | `6.64` on excess (`13.54` on total net) | SIP daily bars from 2016 (already held off-repo) | QUEUE ROW 109 |

## Detailed Candidate Evidence

### 1. Last-Half-Hour Momentum From the First Half Hour (DROP)

Skip-list overlap: MEASURED already on the Round 19 skip list (`docs/QUEUE.md` line 11) and already failed in Replay 07 (`N3` and `N8`).

Source and post-publication after-cost size: STATED from [Dead Signals Lab (Sept 30, 2026)](https://deadsignalslab.substack.com/p/replication-intraday-momentum-eight), testing `SPY`, `QQQ`, `IWM`, and `DIA` on 1-minute bars at 2 bps round-trip cost across the 2014 to 2026 common panel, the strategy lost `-2.30 bps/day` (`t = -5.17`, about `-5.8%/yr`): "Net of costs, the strategy loses in all four instruments and in every sub-window examined." On `IWM`, the only ETF with a gross pre-publication edge, the effect vanished after Gao, Han, Li, and Zhou (2018) appeared: "After 2018, the year the paper appeared, IWM's vestige falls from +1.40 to +0.08 bp per day."

Observations per year and Doc 117 screen: ~252 sessions/year (~2,520 in 10 years), net edge `-2.30 bps/day` -> screen `0.00` (negative). Data needed: 15-minute SIP bars. Verdict: DROP.

### 2. Overnight Against Intraday Return Gap in Index and Sector ETFs (DROP)

Skip-list overlap: MEASURED unconditional overnight holding is already in `docs/QUEUE.md` under "Looked at and dropped before testing," and `SPY` vs `QQQ` overnight vs intraday is Waiting Row 67.

Source and post-publication after-cost size: STATED from [Matthew Bartolini at Alpha Architect (May 20, 2022)](https://alphaarchitect.com/trading-costs-wipe-out-the-overnight-return-anomaly/), testing `SPY` across 6,800 trading days from January 1993 to January 2020 with historical bid-ask spreads and $0.01/share commissions: "For an overnight strategy that does incur trading costs, the cumulative return would be -32%, versus the no-transaction cost strategy of 717%." The author concludes: "The aspect of outperforming the market completely disappears and refutes the notion that buying at night and selling in the morning offers any premia."

For conditioned versions (including conditioning on prior-day moves and volatility), STATED from [georgeded/overnight-intraday-anomaly (Oct 22, 2026)](https://github.com/georgeded/overnight-intraday-anomaly) on CRSP 1993 to 2025 data for `SPY`, `QQQ`, and `IWM`: "In train, always-overnight breaks even with cash at only 1.23-1.65 bp per trade. In the test it breaks even at 1.3-2.7 bp, and it beats buy-and-hold only on IWM below 1.25 bp." Post-2020 unconditional gaps shrank to zero or negative on `SPY` and `QQQ`: "The overnight gap has shrunk for SPY and QQQ. In 2021-2025 it is -1.0 and -0.1 bp a day, against 3.3 and 8.8 bp in train, although the change from train is not significant at 5% (p = 0.18 for SPY, 0.06 for QQQ)." And the validation-selected conditional rule (`sig_c`) failed out of sample in 2019 to 2025: "The chosen signal has no edge in the final test (2019-2025). Before costs sig_c earns 6.36% a year on SPY, 7.20% on QQQ and 10.51% on IWM. That puts it at the 58th, 52nd and 63rd percentile of random sets of nights, below always-overnight and below or equal to buy-and-hold (17.2%, 22.7% and 10.5%)."

Observations per year and Doc 117 screen: ~252 sessions/year (~100/year conditioned), net edge <= 0 -> screen `0.00`. Data needed: SIP daily bars (held). Verdict: DROP.

### 3. Scheduled Macro Release Days: Jobs, CPI, and FOMC (DROP)

Skip-list overlap: MEASURED pre-FOMC announcement drift (Lucca and Moench 2015) is already on the Round 19 skip list (`docs/QUEUE.md` line 11).

Source and post-publication after-cost size: STATED from [Kurov, Halova Wolfe, and Gilbert (2021, Finance Research Letters, PMC7525326)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7525326/), the pre-FOMC drift on press-conference days fell from `+44.5 bps` (`SE = 13.3 bps`, April 2011 to December 2015) to `+9.2 bps` (`SE = 6.9 bps`, January 2016 to December 2019, indistinguishable from `+5.4 bps` non-announcement days), while non-press-conference FOMC days averaged `-5.1 bps` (`SE = 14.1 bps`): "We find that after first appearing before FOMC announcements accompanied by the Fed Chair press conferences, the pre-FOMC drift essentially disappeared after 2015 in both announcements accompanied by press conferences and announcements not accompanied by press conferences." The authors add: "Not only did the pre-FOMC drift disappear in announcements without press conferences as in BGM, since January 2016 the pre-FOMC drift has also substantially weakened in announcements with press conferences."

Observations per year and Doc 117 screen: FOMC (8/yr) + CPI (12/yr) + NFP (12/yr) = ~32 scheduled macro days/year (~320 in 10 years, far below "hundreds per year"). Even granting a generous `+5 bps` net excess after 4 bps round-trip cost against `110 bps` daily `SPY` noise gives `320 x (5 / 110)^2 = 0.66 < 4`. Data needed: SIP daily bars (held) + public macro calendar. Verdict: DROP.

### 4. Intraday Reversal After Large Opening Gaps in Index ETFs (DROP)

Skip-list overlap: MEASURED overnight gap continuation or fade is already on the Round 19 skip list (`docs/QUEUE.md` line 11) and was tested in Replay 07.

Source and post-publication after-cost size: STATED from [Tickfloor (Oct 14, 2026)](https://tickfloor.com/research/claims/overnight-gap-fade), testing >1.5% opening-gap fades on `QQQ` and `DIA` across 303 completed trades from January 2005 to March 2025 at 5 bps per side: "No. We tested Overnight Gap Fade on 2 ETFs, 2005 to 2025. After costs, it returned 9.9 percentage points a year less than the benchmark. None held up once we allowed for the many other rules we tested." Both `p = 1.000` and multiple-testing corrected `q = 1.000`.

Observations per year and Doc 117 screen: ~15 trades/year (~165 in 11 years), negative after costs -> screen `0.00`. Data needed: SIP daily or 15-minute bars. Verdict: DROP.

### 5. Volatility-Conditioned Next-Day Rules (`VIX` Term Structure, `VVIX`, Gamma, VRP) via `SPY` or `SH` (DROP)

Skip-list overlap: MEASURED option dealer gamma is already on the Round 19 skip list and VIX monthly SOQ settlement is on the Round 20 skip list.

Source and post-publication after-cost size: STATED from [KruegerAlgorithms (Oct 3, 2026)](https://kruegeralgorithms.com/en/research/vix-term-structure-vvix-gamma-predict-range-not-direction), testing `VIX9D > VIX`, `VIX > VIX3M`, top-third `VVIX`, and low dealer gamma in a single locked 2019 to October 2026 holdout (1,949 trading days) at 2 bps round-trip cost: "The state of the options market predicts how wide the next day will be, not where it goes." On directional next-day `SPY` or inverse trading: "A session long or short after an inverted curve earns nothing after costs. No t-value exceeds 1.5 in absolute size, and the largest result is +22.0 bps on only 132 signal days (t 1.3)." Variance risk premium (VRP) extraction requires shorting options or variance swaps, which is unreachable on a $500 cash account holding only `SPY` or `SH`.

Observations per year and Doc 117 screen: ~17 to 100 signal days/year, directional post-publication net edge statistically indistinguishable from zero -> screen `0.00`. Data needed: SIP daily bars (held) + Cboe VIX family. Verdict: DROP.

### 6. End-of-Day Rebalancing or Closing-Auction Imbalance Effects With Public Data (DROP)

Skip-list overlap: MEASURED 15:50 ET MOC imbalance publication and closing-auction index-rebalance flows are already on the Round 19 skip list (`docs/QUEUE.md` line 11).

Source and post-publication after-cost size: STATED from [Bogousslavsky and Muravyev (2023, Journal of Financial Markets, SSRN 3485840)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3485840): "Closing auctions appear to match volumes at low cost: closing prices typically match pre-close bid or ask prices, and price impact is lower than during continuous trading." While auction price deviations revert on average ("Auction price deviations revert quickly and almost completely on average"), NYSE and Nasdaq closing-auction imbalance feeds are paid proprietary exchange feeds not carried in Alpaca SIP, and no post-publication after-cost retail replication using free public imbalance data exists.

Observations per year and Doc 117 screen: ~252 sessions/year, blocked by paid-data wall and unmeasured post-publication net retail edge -> screen `0.00`. Data needed: paid proprietary NYSE/Nasdaq imbalance feeds (unavailable). Verdict: DROP.

### 7. Cross-ETF Lead-Lag at One Day: Credit ETFs (`HYG`) Leading Equity ETFs (`SPY`) (DROP)

Skip-list overlap: New check.

Source and post-publication after-cost size: STATED from [Open-Alpha-Lab Study 865 (June 11, 2026)](https://github.com/Guillain-RDCDE/Open-Alpha-Lab/blob/main/studies/865-credit-equity-lead-lag/README.md), testing `HYG`, `IEF`, `LQD`, and `SPY` across 4,822 daily closes and 1,001 weekly closes from 2007 to June 2026 at 1 bp/leg and 5 bps/leg: the trailing high-yield excess return predicted next-period `SPY` with the wrong sign at every horizon (4-week `-19.6 bps`, Newey-West `t = -1.70`; 1-week `t = -1.58`), and the `SPY` vs `IEF` overlay earned a net Sharpe of `0.644` vs `0.645` buy-and-hold at 1 bp/leg (`0.569` at 5 bps/leg), forfeiting `3.3%/yr` CAGR: "the popular 'credit leads equity' rule does not survive an honest test — the trailing HY-excess return fails to predict next-week SPY (wrong sign, t = −1.70, indistinguishable from a label shuffle, consistently wrong-signed across eras), and the SPY↔IEF overlay only trades 3.3%/yr of return for a lower drawdown, so the read is claimed lead absent, paycheck a mirage."

Observations per year and Doc 117 screen: ~252 daily / ~52 weekly observations/year, wrong sign -> screen `0.00`. Data needed: SIP daily bars (held). Verdict: DROP.

### 8. Fresh Addition: Zarattini, Aziz, and Barbon (2024/2025) Noise-Area `SPY` Intraday Momentum (DROP)

Skip-list overlap: New check.

Source and post-publication after-cost size: STATED from [PazSheimy/spy-intraday-momentum-oos (Aug 15, 2026)](https://github.com/PazSheimy/spy-intraday-momentum-oos/blob/main/README.md), replicating the Zarattini, Aziz, and Barbon (2025) 30-minute Noise-Area `SPY` breakout rule with `$0.0035/share` commission and `$0.001/share` slippage: "Headline finding: the in-sample result replicates closely (Sharpe 1.34), but out-of-sample the strategy's Sharpe falls to 0.39 and it underperforms SPY buy-and-hold." Over the May 2024 to March 2026 post-publication window, annualized return fell from `19.8%` to `4.8%` at `14.7%` volatility: "The out-of-sample decline in risk-adjusted returns is statistically significant (Sharpe test, p < 0.001)." In addition, the published rule requires shorting and up to 4x leverage ("Positions are sized to a 2% daily volatility target (capped at 4× leverage)"), which is unreachable in a $500 cash account.

Observations per year and Doc 117 screen: ~252 sessions/year, but at OOS Sharpe `0.39` over 10 years, `T x SR^2 = 10 x 0.39^2 = 1.52 < 4`. Data needed: 15-minute or 30-minute SIP bars plus margin/shorting. Verdict: DROP.

### 9. Fresh Addition: Internal Bar Strength (`IBS < 0.20`) Next-Day Mean Reversion (DROP)

Skip-list overlap: New check.

Source and post-publication after-cost size: Mixed and contradicted across independent 2026 replications. STATED from [KruegerAlgorithms (Oct 3, 2026)](https://kruegeralgorithms.com/en/research/rsi2-dip-buying-index-cfds-holdout), `IBS` (close in the lower fifth of the day's range) was reported descriptively in the 2019 to 2026 holdout without bull-market drift subtraction: "IBS (close in the lower fifth of the day's range) … [is] also positive in the holdout (+16.2 bps, t 2.3, and +55.8 bps, t 2.8, descriptive)." By contrast, STATED from [Tickfloor (Oct 14, 2026)](https://tickfloor.com/research/claims/ibs-mean-reversion), testing `IBS` across 557 completed trades from January 2005 to March 2025 at 5 bps/side on `QQQ` standing in for `SPY`: "No. None of the versions we tested passed." "After costs, it returned 4.7 percentage points a year less than the benchmark." (`p = 1.000`, corrected `q = 1.000`). Because independent after-cost replications disagree and no post-publication study confirms a positive excess over random-day entry after costs, `IBS` does not pass our strict Round 37 filter.

Observations per year and Doc 117 screen: ~50 trades/year (~550 in 11 years), net excess unconfirmed / contradicted -> screen `0.00`. Data needed: SIP daily bars (held). Verdict: DROP.

### 10. Fresh Addition: Connors `RSI(2) < 10` Uptrend Pullback in Liquid US Equity Index ETFs (QUEUE ROW 109)

Skip-list overlap: None (not in `docs/QUEUE.md` or any prior skip list).

Rule definition: Long-only daily close-to-close rule published by Larry Connors and Cesar Alvarez in November 2008 (`Short Term Trading Strategies That Work`): buy at the close when `Close > SMA(200)` and `RSI(2) < 10`; exit at the first close above `SMA(5)` (average holding period ~3.4 to 3.6 trading sessions).

Source and post-publication after-cost size (three independent 2026 replications, covering 18 post-publication years):

- STATED from [KruegerAlgorithms (Oct 3, 2026)](https://kruegeralgorithms.com/en/research/rsi2-dip-buying-index-cfds-holdout), testing the rule in a single locked 2019 to October 2026 holdout across three US equity indices (206 trades, average hold 3.4 sessions, net of CFD spread and overnight financing): "In the holdout the RSI(2) rule beats entering on every day by +33.6 bps per trade, exactly as in the search period; the higher net result comes from the bull-market drift." The net result was `+48.3 bps` (`t = 3.6`), every-day drift was `+14.7 bps`, and excess over every-day entry stayed `+33.6 bps` (`t = 2.4`): "The excess stayed at +33.6 bps (t 2.4), and the rule beat 98% of 1,000 random draws with the same holding time." It survived global multiple-testing correction: "After the global multiple-testing correction it stays confirmed (q = 0.005 across all 59 holdout tests as of 8 October 2026; q is the error probability adjusted for the number of tests)."
- STATED from [RIP Backtest (Nov 6, 2026)](https://ripbacktest.com/posts/rsi-2-strategy-spy/), testing `RSI(2) < 10` on `SPY` from 1994 to October 2026 at 4 bps round-trip cost: "before 2008 it made +0.812% a trade (107 trades), from 2008 on +0.476% (150 trades, t 3.70), still positive but weaker." Over our exact `2016 to October 2026` SIP window, `RS2-10` made `+0.532%` net per trade across 94 trades (profit factor `2.61`), landing at the 100.0th percentile of 500 random uptrend dips (`+0.316%` median). Caveat noted by the author: "on QQQ the same rule passed only 3 of 6 gates" and "invested only 10.5% of the time, it grew ×9.76, against ×29.06 for holding SPY, with a largest fall of -14.8% against -55.2% (at daily closes, open losses included)."
- STATED from [Empirica Lab (Oct 12, 2026)](https://empiricalab.substack.com/p/connors-rsi2-spy), testing `SPY` from January 2009 to October 2026 (149 post-publication trades, 74% winners, `+0.51%` net per trade, profit factor `2.4`): "It passes 6 of our 11 criteria: the effect survived publication, about a third smaller per trade." Against 2,000 random-entry placebos: "The random versions summed to +32% in the median run, the real trades to +168%. None of the 2,000 runs got there."

Observations per year and Doc 117 power screen (`2016 to 2026`, 11 years of SIP daily bars):

- Single-ETF `SPLG` (`SPY`) alone: `~8.5 trades/year` (`N = 94` in 11 years). Implied per-trade SD from RIP Backtest (`+47.6 bps`, `t = 3.70`, `N = 150`) is `158 bps`; from KruegerAlgorithms (`+48.3 bps`, `t = 3.6`, `N = 206`) is `193 bps` (central noise guess `165 to 175 bps`). On total net return (`+48 bps`, `165 bps` noise): `94 x (48 / 165)^2 = 7.96 >= 4`. On excess over every-day entry (`+33.6 bps`, `165 bps` noise): `94 x (33.6 / 165)^2 = 3.90` (borderline `< 4`).
- 4-ETF liquid US equity index panel (`SPLG`, `QQQ`, `IWM`, `DIA`, equal-weight per dip-day): KruegerAlgorithms measured cross-index overlap explicitly ("in the holdout to June 2026, 189 trades fell on only 124 days", ratio `0.656`). Scaling to 4 ETFs over 11 years yields `~350` raw trades falling on `~180` independent dip-days (`~16.4/year`).
- Doc 117 screen on 4-ETF panel excess over every-day entry (`N = 180` independent dip-days, `+33.6 bps` net excess, `175 bps` noise): `180 x (33.6 / 175)^2 = 6.64 >= 4` (and on total net `+48 bps`: `180 x (48 / 175)^2 = 13.54`).

Data needed and preregistration requirements: Alpaca SIP daily bars and corporate actions for `SPLG` (or `SPY` benchmark), `QQQ`, `IWM`, and `DIA` from 2016 to 2026 (already held off-repo; zero new data feeds needed). Preregistration must fix (1) the exact 2008 Connors rule (`Close > SMA(200)`, `RSI(2) < 10`, exit `Close > SMA(5)`) with zero threshold tuning, (2) cluster-day weighting so simultaneous dips across ETFs count as one independent event, (3) primary benchmark as excess return over matched-hold-length random-day entries (to strip out bull-market drift), and (4) explicit 4 bps and 10 bps round-trip cost tiers plus $500 whole-share cash-account sizing (`SPLG`, `IWM`, `QQQ`, `DIA`). Verdict: QUEUE ROW 109.
