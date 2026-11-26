# Row 97: US Corporate Forward Stock Splits Count-First Audit and Closure

Date: 2026-11-26
Status: CLOSED before prices (recommended close; Plan 57 and ledger 194 stay unused)
Scope: Count-first roster without full-text search, post-2010 short-window published evidence net of the announcement-day jump, $500 execution fit without reading prices, and synthetic power at the real dated count against SPY or IWM.

## Summary decision

Recommendation: CLOSE Row 97 without pulling prices, freezing a replay, or drafting Plan 57 (ledger 194 stays unused).

Why Row 97 closes before prices:

- MEASURED: Across 2016 to 2025, 157 unique US-listed domestic common-stock forward splits (ratio at least 1.25-for-1) resolve from Alpaca corporate actions to a verified first Form 8-K split announcement with an exact SEC acceptance timestamp (113 in 2016 to 2023 and 44 in 2024 to 2025; median 21 trading sessions from announcement date to ex-date).
- MEASURED: 106 of the 157 matched Form 8-K filings (67.5%) were accepted after 16:00 ET or on a weekend, so the announcement-day jump occurs overnight before the next regular-session open and cannot be captured by a retail open-market entry.
- STATED: Published post-2010 evidence shows that drift after the announcement-day jump is effectively gone. [Pretickt (Nov 25, 2026)](https://www.pretickt.com/blog/what-happens-after-a-stock-split/) reports: "For the 115 splits since 2010 with a first announcement filed with the SEC, the stock gained a median 1.9 points more than SPY in the two or three sessions around the announcement, then +0.1 points from there to the split." [TradingStudio (Oct 2026)](https://blog.tradingstudio.finance/stock-split-performance-event-study/) reports across 1,968 US forward splits (2000 to 2025): "Post-split drift is gone in aggregate."
- MEASURED (synthetic power, zero real prices): At the real dated count (N = 157 full 2016 to 2025, N = 113 in-sample 2016 to 2023, N = 44 out-of-sample 2024 to 2025) over the real measured day-after-announcement to ex-date hold lengths (median 20 sessions, mean 27.75 sessions) paired against SPY or IWM at 1.5% to 2.0% daily idiosyncratic volatility, 80% two-sided power requires a minimum detectable effect of +1.77% to +2.36% per trade on the full sample (+2.08% to +2.77% IS; +3.36% to +4.47% OOS). At Pretickt's published +0.1% post-2010 announcement-to-ex-date drift, power is 5% (noise).
- MEASURED: 139 historical, delisted, or renamed tickers in the 2016 to 2025 Alpaca corporate-actions feed do not map through SEC's live ticker-to-CIK table, creating a survivorship gap unless a historical CUSIP-to-CIK crosswalk is added.

## 1. Roster and timing without full-text search

No SEC full-text search (EFTS) was queried and no price fields were requested or read.

Roster construction pipeline (all raw files kept off repo in `/home/user/workspace/rig/row97/`):

- Step 1 (Alpaca licensed corporate-actions endpoint, zero price fields): Queried Alpaca Market Data corporate actions with types set to forward_split for ex-dates 2016-01-01 through 2025-12-31 via the saved credential runner. Each record contains cusip, ex_date, new_rate, old_rate, payable_date, process_date, record_date, and symbol, with zero price fields. MEASURED: 830 raw forward_split records across 1 page.
- Step 2 (ratio filter): Dropped 31 records with split ratio below 1.25-for-1. MEASURED: 799 records remain (2016: 57, 2017: 83, 2018: 56, 2019: 30, 2020: 81, 2021: 129, 2022: 90, 2023: 91, 2024: 98, 2025: 84).
- Step 3 (instrument and exchange filter): Dropped 254 ETFs, ETNs, and funds flagged in Nasdaq Trader symbol directories, 121 five-letter Y or F foreign OTC ADR and ordinary tickers, 20 OTC or non-major-exchange SEC tickers, and 139 historical, delisted, or renamed tickers absent from SEC's live company ticker-to-exchange table (a real survivorship gap without a historical CUSIP-to-CIK crosswalk). MEASURED: 265 US-exchange candidates across 214 unique CIKs remain.
- Step 4 (domestic filer check via official SEC EDGAR CIK submissions JSON): Fetched official SEC EDGAR submissions JSON by 10-digit CIK for all 214 CIKs (0 errors) and dropped 52 foreign private issuer events filing Form 20-F, Form 40-F, or Form 6-K without Form 8-K. MEASURED: 213 domestic US-exchange common-stock split records across 204 unique (CIK, ex_date) company events (deduplicating dual share classes splitting on the same ex-date).
- Step 5 (first public Form 8-K announcement and acceptance timestamp): Scanned each issuer's Form 8-K filings (including archived submission JSON files for prolific filers) in the 150 calendar days prior to ex_date carrying Items 5.03, 8.01, 7.01, 2.02, or 5.07 (954 candidate 8-Ks across 200 of 204 events), and read the primary Form 8-K document in chronological order to identify the first filing mentioning the forward stock split.

| Funnel stage | Count | Notes |
|---|---:|---|
| Raw Alpaca forward_split records (2016 to 2025) | 830 | MEASURED, zero price fields |
| Ratio at least 1.25-for-1 | 799 | MEASURED (-31 below 1.25x) |
| After dropping ETFs, ETNs, funds, 5-letter Y/F, OTC, and unmapped live tickers | 265 | MEASURED (-254 ETF/fund, -121 5-letter Y/F, -20 OTC, -139 unmapped historical) |
| Domestic US-exchange 10-K and 8-K filers (split records) | 213 | MEASURED (-52 foreign 20-F/40-F/6-K filers) |
| Unique (CIK, ex_date) domestic company events | 204 | MEASURED (deduplicated dual share classes) |
| Matched first Form 8-K split announcement with SEC acceptance timestamp | 157 | MEASURED (77.0% of 204; all 157 have exact UTC acceptanceDateTime) |
| Matched events accepted after 16:00 ET or on a weekend | 106 | MEASURED (67.5% of 157; overnight jump uncapturable) |

Matched dated events by ex-date year (MEASURED, total 157, average 15.7 per year):

- 2016: 16
- 2017: 19
- 2018: 15
- 2019: 8
- 2020: 10
- 2021: 19
- 2022: 12
- 2023: 14
- 2024: 25
- 2025: 19
- Split by period: 113 events in 2016 to 2023 (IS) and 44 events in 2024 to 2025 (OOS).

Measured gap between Form 8-K announcement date (US Eastern) and split ex-date across the 157 dated events:

- Trading sessions (announcement date to ex-date): min 1, p10 12, p25 16, median 21, mean 28.73, p75 34, p90 59, max 104.
- Day-after-announcement entry to ex-date hold length (ann+1 to ex-date): median 20 sessions, mean 27.75 sessions.
- Calendar days (announcement date to ex-date): median 32 days, mean 41.89 days.
- Session-gap floors: 153 of 157 have at least 5 sessions, 148 have at least 10 sessions, and 98 have at least 20 sessions.
- Unmatched remainder (47 of 204): UNKNOWN exact share announced only in an Exhibit 99.1 press release without split text in the Form 8-K cover body, in a quarterly or annual report, in a proxy statement, or via press release without a Form 8-K.

## 2. Published post-2010 short-window evidence (net of announcement-day jump)

Plain conclusion: in post-2010 US data, drift from the day after the split announcement through the ex-date and over 20 to 60 sessions after the split is effectively gone once the uncapturable announcement-day jump is excluded.

- Announcement-to-ex-date and post-split median vs SPY since 2010 (STATED): [Pretickt (Nov 25, 2026)](https://www.pretickt.com/blog/what-happens-after-a-stock-split/) examined 156 forward splits (at least 5-for-4) by S&P 500 and Nasdaq-100 companies since January 2010, with 115 matched to SEC 8-K announcements, and found: "For the 115 splits since 2010 with a first announcement filed with the SEC, the stock gained a median 1.9 points more than SPY in the two or three sessions around the announcement, then +0.1 points from there to the split." It adds: "Then, from the announcement to the split, the gap goes back to almost zero." For post-split horizons vs SPY, Pretickt reports 1-month median -0.3 points (47% beat SPY), 3-month +0.8 points (54% beat), and 12-month +0.9 points (51% beat), noting: "Of the 53 splits since 2020 that have a full year behind them, 49% beat SPY."
- Broad US forward splits 2000 to 2025 (STATED): [TradingStudio Event Study (Oct 2026)](https://blog.tradingstudio.finance/stock-split-performance-event-study/) analyzed 1,968 US forward splits (2000 to 2025) and concluded: "Post-split drift is gone in aggregate." It further states: "After the split, there is no statistically significant drift in either direction." The only statistically significant pre-ex effect it reports across the full 2000 to 2025 pool is: "Forward stock splits show a modest pre-split run-up: +1.31% vs SPY in the 5 trading days before the effective date (t-stat 3.81, significant at p<0.01)." Pretickt's post-2010 announcement-to-ex-date median of +0.1 percentage points indicates that even this pre-split run-up has largely faded since 2010.
- CRSP announcement and ex-date panels 2000 to 2024 (STATED): [NathanArimilli24 CRSP Study (Nov 2026)](https://github.com/NathanArimilli24/stock-split-event-study) reports on 3,076 announcements and 3,121 ex-dates (2000 to 2024) that abnormal return concentrates on the announcement day (+1.26%, t = 13.2) and fades within about 6 trading days, while the ex-date panel shows an ex-date day-0 AAR of +0.63% (t = 6.7) with a "tau = 0 (clean cutoff)" rather than multi-week post-split drift.
- Post-2000 decay in academic replication (STATED): [Gharghori and Nguyen (EFMA 2018)](https://efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2018-Milan/papers/EFMA2018_0454_fullpaper.pdf) and the summary at [TradeSmrt](https://tradesmrt.com/en/strategies/stock-split-effect/) report that the historical 1975 to 2011 stock-split outperformance "is not robust across sub-periods" and had largely vanished in the 2000 to 2011 sub-period.
- Large-cap post-effective baseline comparison 2000 to 2025 (STATED): [Open-Alpha-Lab Study 142 (Oct 2026)](https://github.com/Guillain-RDCDE/Open-Alpha-Lab/tree/main/studies/142-split-drift) finds across 41 large-cap splits that post-effective returns trail each stock's own baseline at 1 month (-3.6%), 3 months (-5.3%), 6 months (-12.4%), and 12 months (-23.6%).
- Headline 12-month bank research caveat (STATED): [Wall Street Horizon (Jan 2026)](https://www.wallstreethorizon.com/blog/Sour-Stock-Split-Performances-Amid-a-Possible-Sequel-to-Last-Years-Pullback), citing Bank of America Global Research, notes: "since 2010, stocks that have split have posted a 12-month forward return five percentage points above the index" (down from +13 percentage points since 1980). That 12-month headline includes the uncapturable announcement-day jump, does not isolate a 20-to-60-session post-announcement window, and sits far too slow for a short-horizon rule.

## 3. $500 account fit (stated without reading prices)

No stock prices were read for this assessment.

- Why whole shares fail structurally: Companies declare forward stock splits specifically because their pre-split share price has risen to a high nominal level (frequently above $500 per share). A whole-shares-only rule on a $500 account would therefore be unable to purchase a large fraction of splitting stocks at announcement time, biasing any whole-share test toward lower-priced splits.
- Required execution mode: Any pre-split announcement rule on a $500 account must use fractional-share notional orders at a US retail broker that supports fractional NMS equities (such as Alpaca, Fidelity, or Charles Schwab Stock Slices).
- Execution consequence for timing: Retail fractional-share orders generally execute as market orders during regular trading hours rather than extended-hours limit orders. Combined with the measured fact that 67.5% (106 of 157) of matched Form 8-K split announcements arrive after 16:00 ET or on a weekend, a $500 fractional-share account cannot capture the announcement-day jump and can only enter on the next regular trading session.

## 4. Synthetic power at the real dated count (paired vs SPY or IWM)

All power figures below are pure Monte Carlo simulations (5,000 draws per cell, zero real prices read) for a paired single-stock minus benchmark (SPY or IWM) t-test at two-sided alpha = 0.05. Each event i uses its actual measured day-after-announcement to ex-date hold length h_i (median 20 sessions, mean 27.75 sessions) with idiosyncratic daily excess volatility sigma_daily of 1.5% (lower-vol large-cap) or 2.0% (typical mid/large-cap), plus fixed 5-session, 20-session, and 60-session reference windows at N = 157.

| Sample and window | Daily excess vol | SE of mean | 80% power MDE (2-sided) | Power at +0.1% | Power at +0.5% | Power at +1.0% | Power at +1.3% | Power at +2.0% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Full 2016 to 2025 (N = 157, ann+1 to ex) | 1.5% | 0.63% | 1.77% | 5% | 12% | 35% | 53% | 89% |
| Full 2016 to 2025 (N = 157, ann+1 to ex) | 2.0% | 0.84% | 2.36% | 5% | 9% | 23% | 33% | 66% |
| IS 2016 to 2023 (N = 113, ann+1 to ex) | 1.5% | 0.74% | 2.08% | 5% | 10% | 28% | 41% | 76% |
| IS 2016 to 2023 (N = 113, ann+1 to ex) | 2.0% | 0.99% | 2.77% | 5% | 8% | 18% | 25% | 53% |
| OOS 2024 to 2025 (N = 44, ann+1 to ex) | 1.5% | 1.20% | 3.36% | 5% | 7% | 13% | 19% | 38% |
| OOS 2024 to 2025 (N = 44, ann+1 to ex) | 2.0% | 1.60% | 4.47% | 5% | 6% | 10% | 12% | 25% |
| Full N = 157, fixed 20-session | 1.5% | 0.54% | 1.50% | 5% | 15% | 47% | 67% | 96% |
| Full N = 157, fixed 20-session | 2.0% | 0.71% | 2.00% | 5% | 10% | 29% | 44% | 81% |
| Full N = 157, fixed 60-session | 1.5% | 0.93% | 2.60% | 5% | 8% | 19% | 28% | 57% |
| Full N = 157, fixed 60-session | 2.0% | 1.24% | 3.46% | 5% | 7% | 13% | 19% | 36% |
| Full N = 157, fixed 5-session pre-ex | 1.5% | 0.27% | 0.75% | 6% | 47% | 96% | 100% | 100% |
| Full N = 157, fixed 5-session pre-ex | 2.0% | 0.36% | 1.00% | 6% | 28% | 80% | 95% | 100% |

Interpretation (MEASURED from synthetic model):

- Over the actual announcement-to-ex-date window (N = 157 full, 113 IS, 44 OOS) or a 20-to-60-session window, power is 5% to 35% for any realistic post-2010 drift (+0.1% to +1.0%). The OOS split (N = 44) would need a +3.36% to +4.47% excess return per trade just to hit 80% power.
- Only a tight 5-session pre-ex-date window reaches 80% power at +0.75% to +1.00% on the full sample (N = 157), but Pretickt's post-2010 announcement-to-split median (+0.1 percentage points across the entire window) gives no post-2010 basis to expect a +1.0% net 5-day pre-ex run-up, and the 2024 to 2025 OOS count (N = 44) remains underpowered.

## 5. Disposition

Row 97 is CLOSED before prices. Plan 57 and ledger 194 stay unused. No price pull, freeze, or replay is warranted unless future peer-reviewed post-2010 evidence isolates a tradable post-announcement sub-window with both a resolved historical CUSIP-to-CIK crosswalk and a documented excess return above +2% net of the announcement-day jump.
