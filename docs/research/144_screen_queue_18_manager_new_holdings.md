# Queue 18. New positions from well-known managers

Price-blind screen for ledger 214. The initial manager and signal rules were recorded at 05:07 MT on November 26, 2026, before opening any holdings archive. No market price or replay return is an input.

## Fixed before collection

- STATED. Take all five managers in the high-recognition group of the [13F study cited in Doc 50](https://arxiv.org/html/2610.17231). Its published recognition z-score cutoff is at least 1, based on public attention rather than returns. Do not add the other 19 recognizable managers, controls, or any manager chosen by these results to the judged cohort. The study uses recognition measured as late as 2025, so the list is fixed now but was not demonstrated as a list an investor would have picked in 2016.
- STATED. Use one consolidated SEC reporting entity per manager: Warren Buffett, Berkshire Hathaway Inc. (1067983); Carl Icahn, Icahn Carl C (921669); Michael Burry, Scion Asset Management LLC (1649339); Bill Ackman, Pershing Square Capital Management LP (1336528); Nelson Peltz, Trian Fund Management LP (1345471). No family substitution for a missing filing. If a name change crosses entities, require independent evidence; do not stitch positions just to fill coverage.
- STATED. Use the first accepted original 13F-HR with an information table per manager and fiscal report quarter. Compare only to the original report for the immediately preceding quarter, available strictly before the current filing. Ignore later amendments and confidential revisions, so the signal is new to the original public tables, not verified trading by the manager. Missing prior reports are unresolved, not empty books.
- STATED. A new holding is a reported long US-listed common stock absent from the prior public table, not an increase. Merge duplicate share rows for a CUSIP, refuse options and non-common instruments, and suppress cases where the same issuer was already present under another CUSIP or a likely identifier change. Require at least 0.50% of the value of the original entire reported 13F table using reported value, not share count. This is a share of reported book, not assets under management.
- STATED. Treat the exact acceptance date in New York as day 0, even before its open, and use the open of the second regular US equity session dated strictly after day 0. Buy the admitted shares and compare the total return to gross SPY over the same open-to-open 21 or 63 sessions. Charge at least 5 bp per stock entry and exit; compare 10 bp per side as a stress. Only 63 sessions is judged; 21 sessions is shown only. No price needed for this count.
- STATED. For the screen, each horizon must have a positive full mean, filing-quarter clustered CR1 t at least 2, positive mean after removing the highest ceiling of 1% of trades, and positive filing-year mean in at least seven of 11 years. The ledger also requires at least 300 new positions and at least 33% chance of clearing all return marks in the main case. Neither count nor power authorizes a replay by itself.

## Count sources and limits

- STATED. Use the [SEC structured 13F archive](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) and [EDGAR submissions metadata](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). Keep the native archive and accession receipts off-repo. The 2015 archives supply the warm-up prior quarters; the dated count begins with January 2016 acceptance.
- STATED. For the shown-only wider line, add all other names in [Table I, printed page 8](https://arxiv.org/pdf/2610.17231), not the paper's 24 matched controls. Use one contemporaneous original public filing per manager and report quarter. Appaloosa LP is used from 2016 reporting periods and Appaloosa Management LP before then; the [SEC Form 3/A](https://www.sec.gov/Archives/edgar/data/1656456/0000905718-16-001393-index.htm) identifies both entities and David Tepper. Use [Marc Lasry's original filing CIK](https://www.sec.gov/Archives/edgar/data/1259927/0001405086-25-000079-index.html) for Avenue, not the affiliated notices. The code lists the selected CIKs. These are public-table mappings, not a claimed reconstruction of all the Thomson Reuters filer families in the paper.
- STATED. The [SEC Official List](https://www.sec.gov/rules-regulations/staff-guidance/official-list-section-13f-securities) for each report quarter supplies a date-specific CUSIP and security-class check. The [SEC 13F FAQ](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f) describes the list as mostly US exchange-traded stocks and funds, with other reportable instruments. The script excludes non-common class labels, fund and acquisition-vehicle labels, and likely prior-quarter issuer/identifier matches using normalized names and issuer CUSIP stems. The resulting count is a common-stock listing proxy, not a verified listing or opening print on each exact entry date. The liberal diagnostic keeps all new non-option share CUSIPs meeting the weight floor for the successfully joined quarters; it skips official-list, class and issuer exclusions and is not a second roster.

## Price-blind result

- MEASURED. **203 new common-stock proxy positions from 200 valid filing pairs**, below 300. Berkshire 23, Icahn 27, Scion 118, Pershing Square 21, and Trian 14. Scion is the largest source. The 203 signals span 42 nonempty quarters, 202 distinct quarter/CUSIP pairs, and 174 distinct CUSIPs. A separate manager signal on the same name still counts as its own position; the power calculation clusters by quarter, not by manager.
- MEASURED. The 45 [SEC bulk archives](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) including warm-up produced 202 judged-cohort signals through August 31, 2026. No original in the SEC metadata was absent from the corresponding bulk files. An explicitly separate original-SEC-filing supplement from September 1 to November 26 added one judged-cohort signal; all 19 supplement originals in both cohorts matched the native acceptance timestamp. The rest of 2026 was unobserved, not zero.
- MEASURED. The same five names yielded 231 liberal candidate positions in valid filing pairs before dropping 13 for prior-issuer evidence, 13 for stock-class or issuer-type reasons, and two with no Official List match. Four current originals could not be joined to a valid preceding report, and two other current reports failed a summary reconciliation. If every one of the 82 observed above-floor non-option share CUSIPs in those six current tables were credited as new common stock, the classified total would reach 285. That is an observed-table check, not a bound on corrupted or unseen rows.

Counts by acceptance quarter. Each cell lists Q1, Q2, Q3 and Q4 in order. The wider series is shown only.

| Filing year | Fixed five | Wider Table I |
|---|---:|---:|
| 2016 | 1, 5, 6, 4 | 38, 32, 19, 28 |
| 2017 | 4, 2, 1, 2 | 44, 24, 32, 10 |
| 2018 | 1, 2, 6, 3 | 15, 33, 34, 24 |
| 2019 | 4, 3, 5, 5 | 36, 23, 27, 28 |
| 2020 | 6, 6, 8, 14 | 18, 87, 52, 50 |
| 2021 | 12, 5, 3, 3 | 57, 52, 40, 25 |
| 2022 | 3, 16, 1, 6 | 30, 48, 24, 25 |
| 2023 | 5, 19, 3, 2 | 23, 55, 45, 31 |
| 2024 | 1, 3, 11, 0 | 27, 48, 38, 39 |
| 2025 | 6, 1, 7, 4 | 28, 23, 33, 30 |
| 2026 through November 26 | 1, 2, 0, 1 | 35, 26, 37, 32 |

## Published long-side evidence

- STATED. Smolinski and Saridevi, [The Buffett Effect, printed page 51, Table IA.XVIII Panel A](https://arxiv.org/pdf/2610.17231): the five high-recognition managers' long-only buy-and-hold portfolio entering at day +2 reports **+2.7 bp/day at 63 days** (p = 0.068) and +4.8 bp/day at 21 days (p = 0.075). The full sample is 2000 to 2025 (printed page 9), not a post-2010-only estimate. The paper defines new positions as first appearances in a manager's history, not necessarily quarterly re-entries as here. Its denominator is calendar-time observations, not independently matched trades; the table uses HAC standard errors with five lags, and does not publish fill-level SPY-paired dispersion.
- STATED. This is the largest nearby long-only buy-and-hold result at a practically obtainable delayed clock that I found in the checked sources for this exact group, not an estimate for our frozen print. Day +1 in that table starts at filing-day close and +2 starts one trading day later; we wait until the second subsequent regular open. The larger +3.2 bp/day at 63 is daily rebalanced, +3.8 starts at filing-day close, and +3.4 is long minus the matched controls. The +2.7 is also gross Carhart alpha, not gross excess over SPY. For a favorable proxy only, multiplying by 63 gives +170.1 bp gross and subtracting our 10 or 20 bp gives +160.1 or +150.1 bp. The analogous 21-day proxy is +100.8 bp gross and +90.8 or +80.8 bp net. A unit conversion is not a change of benchmark.
- STATED. [Barclays QIS, printed pages 17–18](https://indices.cib.barclays/file.app?action=shared&path=qis/insights/qis-insights-13f-alpha.pdf) reports +3.80 percentage points a year versus the S&P 500 Total Return Index from May 2004 to June 2019 for a top-50 consensus sleeve rebalanced 47 days after quarter-end. [Alpha Suite's November 2026 check](https://alpha-suite.org/blog/13f-copycat-strategy-backtest) shows a broad 16-manager, top-20-by-value blend at 14.0% CAGR against 14.3% for SPY over roughly 13 years, using the next close and holdings carried to the next filing. Neither checks this manager list, new holdings, 21/63 sessions, or the second regular open.
- UNKNOWN. No published result found for the exact list, weight floor, SPY benchmark and frozen print on a post-2010-only sample. No price or return was opened to fill the gap. Treat the paper's delayed long-only result as a favorable planning proxy, not a mathematical upper bound or evidence of profit.

## Power design

- STATED. [Doc 117](117_power_screen_before_data.md) requires testing the actual dated clusters and every mark together. Simulate 30,000 made-up worlds per scenario using the five-manager count by acceptance quarter. Use the count-weighted equal-position mean; compute an intercept-only CR1 t using nonempty filing quarters as clusters; apply the same trimming rule and require positive means in seven filing years. An identical 200 bp rally on both stock and SPY cancels in the paired score, and the script checks the cancellation. No empirical price, return or volatility series is read.
- STATED. With no matched event-level paired noise estimate for these names, use 1,500 bp at 63 sessions and 866 bp at 21 centrally, 20% within-quarter correlation, and adjacent shared-quarter shock correlations of 20% and 5%, respectively. Private shocks are standardized Student t with 5 degrees of freedom. Show a quieter independent case and both weaker and stronger dependence. These are assumptions, not estimates; Doc 117's 1,200 bp stock-event illustration is not a matched calibration here. For ledger 214 use only the five-name counts, including the liberal sensitivity. The 24-name exercise is separate. The docket includes recent signals irrespective of whether their holding windows have matured; also show the central case excluding the partial fourth quarter of 2026.

## Five-manager power and decision

- MEASURED. At the favorable delayed long-only proxy, the 63-session chance to clear all marks was **19.08%** with 10 bp round trip and **17.57%** with 20 bp. It was 3.98% with no planted edge. The central case needed +250 bp on the tested grid to reach the 33% line. At +160.1 bp, removing the partial fourth quarter of 2026 gives 18.86%; the liberal 231-count case gives 19.83%. The weaker-dependence scenario reached 26.76%; the quieter independent scenario reached 61.09%, but it assumes no quarter dependence and only 1,000 bp of paired noise.
- MEASURED, shown only. The 21-session case was 17.41% at +90.8 bp and 14.99% at +80.8 bp with the central noise model. Neither the 21-session case nor the 24-name comparison changes the decision.
- CLOSE BEFORE PRICES. The fixed five do not meet the 300-position gate and miss the 33% all-marks line under the central assumptions even when credited with the favorable published proxy. Matched SPY edge and noise at the frozen print remain UNKNOWN. This does not establish that the strategy loses; it shows this row does not warrant opening prices.

## Wider Table I roster, shown only

- MEASURED. The same method yielded 1,505 positions, including 1,473 from bulk and 32 from the later supplement. That clears the count line but is a different list, not extra observations for ledger 214.
- STATED. The wider set has its own delayed long-only result: [Table IA.XX Panel B, printed page 52, “Recognizable buys”](https://arxiv.org/pdf/2610.17231) gives +2.7 bp/day gross Carhart at 63 sessions (p = 0.002) for the study's 2000 to 2025 sample. This is the delayed, daily-rebalanced variant, not the five-name buy-and-hold line on page 51 that happens to have the same magnitude. [Table XV, printed page 31](https://arxiv.org/pdf/2610.17231) gives +2.8 bp/day at 63 and +1.9 bp/day at 21 for the wider set at the earlier clock; those are not the delayed figures. The wider delayed 21-session result, delayed buy-and-hold result, and exact-clock SPY edge are UNKNOWN. Convert the published wider +2.7 bp/day to +160.1 or +150.1 bp after the same costs for proxy power only.
- MEASURED. At that wider-roster proxy, all-marks power was **30.81%** at +160.1 bp and **28.13%** at +150.1 bp, using the same central noise and dependence assumptions and all 44 actual quarter counts. The effective count under that model was 131.19, not 1,505. Removing the partial fourth quarter of 2026 gives 30.30% at +160.1 bp. The first grid point to clear 33% was +175 bp net. At +160.1 bp the weaker-dependence scenario was 64.87%, while the noisy-dependent scenario was 16.21%. The wider line therefore clears on count but not on central proxy power, and neither of the wider results changes ledger 214.

## Reproduction

The count script takes an off-repo custody folder with the SEC archive index, ZIPs, quarterly Official Lists, submissions metadata and historical shards, and later original filings. It writes only aggregate results to standard output; its optional event audit stays in that folder. The power script consumes the aggregate count JSON only, not the custody folder.

```sh
nice -n 10 python3 research_rig/count_screen18.py "$SEC_CUSTODY" > /tmp/count-screen18.json
cmp /tmp/count-screen18.json research_rig/COUNT_SCREEN18.json
OPENBLAS_NUM_THREADS=1 nice -n 10 python3 research_rig/power_screen18.py /tmp/count-screen18.json > /tmp/power-screen18.json
cmp /tmp/power-screen18.json research_rig/POWER_SCREEN18.json
```
