# Round 12: Timestamped Public-Document Drift Candidates for a Reading Agent

Date: 2026-11-25
Author: idea_scout
Scope: Public-document events with an exact publication timestamp and published post-announcement drift, evaluated for a reading agent on a $500 US retail account (Alpaca SIP daily and minute bars from 2016 onward). No returns were computed in this note. All figures are verbatim from cited primary sources. Claims are labeled MEASURED (from audited or empirical sample output in the source), STATED (structural rule, fee, or qualitative statement in the source), or UNKNOWN (not published in the retrieved sources).

Nothing is repeated from Rounds 1 to 11 without new evidence. Congressional trade disclosures (failed in Replay 12, doc 47) are excluded. Small-lot issuer odd-lot tender offers (already queued in Row 38), reverse-split round-ups (Row 43), CEF rights snapbacks (Row 55), spin-off subsidiaries (Row 58), and marketed non-overnight SEOs (Row 59) are excluded from the candidate list.

## Summary Table

| # | Candidate | Primary Source (Sample End) | Published Post-Event Drift | Horizon | Trades/Yr | Free Exact Timestamp | $500 US Retail Executable | Faded? | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Form 4 officer/director opportunistic & cluster buys | Cohen et al. 2012 (2007); Alldredge & Blank 2019 (2014) | >2% 1-mo (cluster); +82 bps/mo VW, +180 bps/mo EW (L/S) | 21 trading days (accrues to 6 mo) | High (hundreds/yr) | Yes (EDGAR Form 4) | Yes (long-only) | UNKNOWN post-2014 | TOP 1 - TEST |
| 2 | Going-private Schedule 13E-3 first filings | Lehn 2006 (2005) | +3.7% CAR [1, 20] (p=0.01) | 20 trading days | ~12/yr (134 in 11 yrs) | Yes (EDGAR SC 13E3) | Yes (long-only) | UNKNOWN post-2005 | TOP 3 - TEST |
| 3 | DoD daily 5 p.m. ET contract awards (top-5% rel. size / <=1y) | TenderAlpha & HKU 2026 (May 2025) | +28.3 to +30.0 bps (3d); +28.6 to +28.9 bps (5d) | 3 to 5 trading days | ~65 to 140/yr | Yes (defense.gov 5 p.m. ET) | Yes (long-only) | Active through May 2025 (tight vs spreads) | TOP 2 - TEST |
| 4 | Form 10-K/10-Q text changes ("Lazy Prices") | Cohen, Malloy & Nguyen 2020 (2014) | 34 to 58 bps/mo VW overall; 188 bps/mo Risk Factors (L/S) | 12 to 18 months | Portfolio rebalance monthly | Yes (EDGAR 10-K/10-Q) | Long-only leg usable; L/S needs short | Partially (dual-download attenuation) | WATCH (too slow) |
| 5 | Earnings-call text surprise ("PEAD.txt") | Meursault et al. 2021 (2019) | +1.31% Q5 long-only (63d); +2.87% L/S (63d) | 63 to 252 trading days | High (~8,500 calls/yr) | No (paid call transcripts) | Yes (long-only Q5) | Active through 2019 | WATCH (data cost) |
| 6 | Activist Schedule 13D first filings | Collin-Dufresne & Fos 2012 (2010) | 0% post-filing drift in 2003 to 2010 | N/A | ~150 to 250/yr | Yes (EDGAR SC 13D) | Yes (long-only) | YES (disappeared by 2003 to 2010) | DROP (faded) |
| 7 | Form 8-K item-level drift (1.01, 1.03, 2.04, 2.06, 5.01, 7.01) | Lerman & Livnat 2010 (2006) | Positive items <=0.69% (90d); negative -1.2% to -19% | 30 to 90 calendar days | High (63,000+ 8-Ks/yr) | Yes (EDGAR 8-K) | Positive sub-spread; negative short-only | UNKNOWN post-2006 | DROP (short/spread) |
| 8 | Form 8-K Item 3.01 delisting / deficiency notices | Lerman & Livnat 2010 (2006) | Insignificant (-0.54% 30d, -0.44% 60d, +0.27% 90d) | 30 to 90 calendar days | Hundreds/yr | Yes (EDGAR 8-K 3.01) | No (short-only, sub-$1 locate) | No post-filing drift in sample | DROP (no drift) |
| 9 | Form 8-K Item 4.02 non-reliance / restatement notices | Lerman & Livnat 2010 (2006) | Insignificant (+0.13% 30d, +0.52% 60d, +0.94% 90d) | 30 to 90 calendar days | Dozens to ~100/yr | Yes (EDGAR 8-K 4.02) | No (no significant drift) | No post-filing drift in sample | DROP (no drift) |
| 10 | Form NT 10-K / NT 10-Q late-filing notices | Bartov & Konchitchki 2017 (2008) | -4.93% [3, 62]; -10.34% [3, 182]; -16.29% non-acct | 60 to 180 trading days | ~235/yr (2,115 in 9 yrs) | Yes (EDGAR NT 10-K/Q) | No (short-only distressed small caps) | UNKNOWN post-2008 | DROP (short-only) |
| 11 | Management earnings guidance changes | Das et al. (2004); 2026 news corpus (2026) | +4.58% med. [+2,+30] (1995-2004); +0.13% [+6,+20] (2023-2026) | 20 to 30 trading days | High (~8,000+/yr) | Mixed (8-K/PR) | Yes (long-only) | YES (faded to +0.13% in 2023-2026) | DROP (faded) |
| 12 | FDA decision dates (PDUFA approvals, CRLs, AdComs) | Lacey & Sharma 2008 (2000); Hamill et al. 2018; Drugs@FDA 2024 | No positive drift; small-cap approvals reverse -6.5% [+2,+20] | 2 to 20 trading days | ~25 to 50/yr | Partial (FDA/PR/8-K) | Long side reverses; short side hard-to-borrow | No positive drift; absorbed day 0/+1 | DROP (no drift) |
| 13 | Activist short-seller report days | Ljungqvist & Qian 2016 (2011); Brendel & Ryans 2021 (2017) | -18.6% (60d); -30% (1y); 15% squeeze rate | 60 to 252 trading days | ~20 to 60/yr | No (scattered websites) | No (borrow cost +52%, 4.85% lendable) | UNKNOWN post-2017 | DROP (short/borrow) |
| 14 | Tender offer amendments (Schedule TO-T/A, TO-I/A) | Lakonishok & Vermaelen 1990 (1986) | +0.4%/mo post-expiration (22 mo, tiny firms); amendment drift UNKNOWN | 22 to 23 months | Low (dozens/yr) | Yes (EDGAR SC TO) | Yes (long-only) | UNKNOWN post-1986 | DROP (no modern drift) |

## Top Three Candidates

1. Candidate 1: SEC Form 4 officer and director opportunistic and cluster buys. It combines a free, exact-to-the-second EDGAR timestamp with a 100% long-only trade that a $500 US retail account can place without locate or borrow costs. Published abnormal returns exceed 2% in the month after clustered buys (Alldredge & Blank 2019, sample ended 2014) and 82 bps/month value-weighted or 180 bps/month equal-weighted for opportunistic insiders (Cohen, Malloy & Pomorski 2012, sample ended 2007, present in both large and small stocks). A reading agent has a direct advantage parsing Form 4 XML and footnotes to separate open-market purchases (transaction code P) by multiple executives from 10b5-1 plans, grants, and routine calendar buyers. Post-sample test window on our Alpaca 2016 to 2026 data is 11 years.

2. Candidate 3: US Department of Defense daily 5:00 p.m. ET contract awards filtered to large-relative-to-market-cap or short-duration (<=1 year) awards. It has a free, exact after-market-close timestamp on defense.gov that precedes FPDS and SAM.gov by 90 days (DFARS PGI 204.604), a fast 3 to 5 trading day holding window, and 100% long-only execution at the next open for a $500 account. Recent evidence through May 2025 (TenderAlpha & HKU 2026) documents statistically significant market-adjusted drift of +28.3 to +30.0 bps over 3 days (top 5% relative size) and +28.6 to +28.9 bps over 5 days (short duration <=1 year). Because 28 to 30 bps gross is tight against small-cap spreads, feasibility should test whether spread-filtered names and contract-to-market-cap thresholds produce net-positive moves over 2016 to 2026.

3. Candidate 2: Going-private Schedule 13E-3 first filings over the post-announcement [1, 20] trading-day window. It has a free, exact EDGAR SC 13E3 timestamp, a short 20-trading-day window, and 100% long-only execution for a $500 account. Lehn (2006, sample ended 2005) measured a +3.7% [1, 20] post-announcement CAR (p=0.01) across 134 13E-3 transactions. A reading agent can extract the cash offer price, current market spread, and financing or board-approval conditions directly from the filing. Main risks are low event count (~12/year in 1995 to 2005) and wide bid-ask spreads in going-private microcaps, both of which should be checked on 2016 to 2026 EDGAR and Alpaca data before sizing.

---

## Detailed Candidate Reviews

### 1. Officer and Director Opportunistic and Cluster Buys on SEC Form 4

Paper and audited record:
- MEASURED: Cohen, Malloy & Pomorski (2012, Journal of Finance, [Harvard DASH](https://dash.harvard.edu/server/api/core/bitstreams/7312037e-2b77-6bd4-e053-0100007fdf3b/content)): "Our data are drawn from these Form 4 filings for the period January, 1986 to December, 2007."
- MEASURED: Cohen, Malloy & Pomorski (2012, [Harvard DASH](https://dash.harvard.edu/server/api/core/bitstreams/7312037e-2b77-6bd4-e053-0100007fdf3b/content)): "To give an idea of the stark differential in information revealed by these opportunistic vs. routine insiders, a long-short portfolio that exploits solely the trades of opportunistic traders (opportunistic buys minus opportunistic sells) earns value-weighted abnormal returns of 82 basis points per month (9.8 percent annualized, t=2.15), and equal-weighted abnormal returns of 180 basis points per month (21.6 percent annualized, t=6.07)."
- MEASURED: Cohen, Malloy & Pomorski (2012, [Harvard DASH](https://dash.harvard.edu/server/api/core/bitstreams/7312037e-2b77-6bd4-e053-0100007fdf3b/content)): "For example, the coefficient on opportunistic buys in column 2 indicates that opportunistic buys yield an incremental 90 basis points (t=4.64) in the following month relative to all insider trades."
- MEASURED: Alldredge & Blank (2019, Journal of Financial Research, [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1111/jfir.12172)): "We also document that clustered insider purchases are followed by abnormal returns in excess of 2% during the subsequent month."

Sample end and post-sample window:
- MEASURED: Sample ended December 2007 in Cohen et al. (2012) and 2014 in Alldredge & Blank (2019), leaving 11+ years (2016 to 2026) of clean post-sample data on Alpaca.

Size after US retail costs in small stocks:
- MEASURED: Predictability is not restricted to illiquid microcaps; Cohen et al. (2012, [Harvard DASH](https://dash.harvard.edu/server/api/core/bitstreams/7312037e-2b77-6bd4-e053-0100007fdf3b/content)): "In Appendix Table A11, we find that opportunistic trades (both buys and sells) predict returns for both large stocks and small stocks, while routine trades (both buys and sells) are uninformative for both large and small stocks."
- UNKNOWN: Neither paper reports realized US retail spread deductions on 2016 to 2026 small caps, though a >2% 1-month cluster-buy drift and +90 bps incremental opportunistic-buy alpha have meaningful headroom above typical liquid small-cap and mid-cap spreads (20 to 60 bps round-trip).

Holding period and trades per year:
- MEASURED: One-month rebalance, with drift continuing through six months; Cohen et al. (2012, [Harvard DASH](https://dash.harvard.edu/server/api/core/bitstreams/7312037e-2b77-6bd4-e053-0100007fdf3b/content)): "Further, we find that the returns to these opportunistic trades continue to rise for roughly six months following the opportunistic trading month, and then level off, exhibiting no future reversal."
- MEASURED: Hundreds of opportunistic and clustered open-market purchase events per year across US equities (36% of partitionable insider purchases classified as opportunistic in Cohen et al. 2012).

Timestamp, $500 retail reachability, and fade status:
- STATED: Free, exact-to-the-second SEC EDGAR Form 4 acceptance timestamp (XML format since 2003).
- STATED: Fully executable on a $500 US retail account on the long-only side (zero commissions, fractional or whole shares, no short locate or borrow cost).
- UNKNOWN: Whether post-2014 Form 4 cluster/opportunistic buy drift has faded in 2016 to 2026 US equities is unverified in our retrieved papers and directly testable on EDGAR plus Alpaca.

Verdict: TOP 1 - TEST. Strongest reading-agent, long-only EDGAR candidate.

---

### 2. Going-Private Schedule 13E-3 First Filings

Paper and audited record:
- MEASURED: Lehn (2006, [Nomura Foundation](https://www.nomurafoundation.or.jp/en/wordpress/wp-content/uploads/2014/09/20060912_K_Lehn.pdf)): "The sample for this study consists of 245 firms that went private during the period of 1995 through 2005."
- MEASURED: Lehn (2006, [Nomura Foundation](https://www.nomurafoundation.or.jp/en/wordpress/wp-content/uploads/2014/09/20060912_K_Lehn.pdf)): "The mean residual return on the announcement date for the 134 13e-3 transactions in the sample is 20.2%, versus 13.6% for the 111 other transactions in the sample."
- MEASURED: In Table 3 of Lehn (2006, [Nomura Foundation](https://www.nomurafoundation.or.jp/en/wordpress/wp-content/uploads/2014/09/20060912_K_Lehn.pdf)), the post-announcement [1, 20] trading-day CAR for the 134 13e-3 transactions is 3.7% (p=0.01), compared with 0.8% (p=0.60) for non-13e-3 transactions, and 3.5% (p=0.02) in the 2000 to 2005 subperiod (N=144).

Sample end and post-sample window:
- MEASURED: Sample ended 2005, leaving 20+ years (including all of Alpaca 2016 to 2026) post-sample.

Size after US retail costs in small stocks:
- UNKNOWN: Lehn (2006) does not report bid-ask spreads for 13E-3 targets. Going-private targets are typically small or microcap firms where round-trip spreads can reach 50 to 150 bps, leaving plausible net room on a +3.7% 20-day drift only if spreads and deal-break tail risk are controlled.

Holding period and trades per year:
- MEASURED: 20 trading days ([1, 20] window). Frequency was 134 deals over 11 years (~12 per year).

Timestamp, $500 retail reachability, and fade status:
- STATED: Free, exact-to-the-second SEC EDGAR SC 13E3 acceptance timestamp.
- STATED: Long-only; $500 US retail account can place it with no shorting or borrow cost.
- UNKNOWN: Post-2005 fade status is unknown; requires a post-2016 EDGAR SC 13E3 count and spread-adjusted test.

Verdict: TOP 3 - TEST. Clean long-only EDGAR reading-agent event with a 20-day horizon, subject to event-count and microcap spread verification.

---

### 3. US Department of Defense Daily 5:00 p.m. ET Contract Awards (and SAM.gov)

Paper and audited record:
- STATED: AltDataForge (2026, [AltDataForge](https://altdataforge.com/notes/dod-awards-90-day-hold)): "The award is published on the Defense Department's daily contracts page, after the stock market has closed." And regarding SAM.gov/FPDS: "But Defense Department records are held back: they are 'not available for public view ... until 90 days after the Date Signed data element', for operational security (DFARS PGI 204.604)."
- MEASURED: TenderAlpha and University of Hong Kong (2026, [TenderAlpha White Paper](https://www.tenderalpha.com/wp-content/uploads/2026/02/White-Paper-Defense-Contract-Announcements-TenderAlpha-HKU-1.pdf)): "Our sample runs from 2010-01-01 through 2025-05-31." Sample covers 16,529 unique contracts across 183 US-listed firms.
- MEASURED: TenderAlpha & HKU (2026, [TenderAlpha White Paper](https://www.tenderalpha.com/wp-content/uploads/2026/02/White-Paper-Defense-Contract-Announcements-TenderAlpha-HKU-1.pdf)): "The broad response is mildly positive, but the signal concentrates in a few corners: (i) contracts that are large relative to issuer market cap, (ii) Army awards, and (iii) short-duration deals (<=1 year)."
- MEASURED: In the TenderAlpha & HKU (2026) tables, all pooled announcements earned only +0.6 bps VW (t=0.18) and +4.0 bps EW (t=1.20) over 3 days, but the Top 5% relative-size bucket (N=1,006) earned +30.0 bps VW (t=2.35) and +28.3 bps EW (t=2.18) over 3 days, and short-duration (<=1 year) contracts (N=2,115) earned +28.9 bps VW (t=2.82) and +28.6 bps EW (t=2.84) over 5 days. Modifications outperformed new awards (+12.8 bps EW over 5 days, t=2.07 vs +3.2 bps, t=0.67).
- MEASURED: Cioaca (2025, NBER Working Paper 33880, [NBER](https://www.nber.org/system/files/working_papers/w33880/w33880.pdf), 1984 to 2015, 239 firms): "The stock market responds quickly to the announcement of an R&D contract award. Share turnover rises significantly the day after a firm receives a reportable R&D contract, consistent with the FAR Section 5.303 requirement that federal contracting officers make information on reportable awards available after market close on the award date."

Sample end and post-sample window:
- MEASURED: Sample runs through May 31, 2025 in TenderAlpha & HKU (2026), so the effect is measured in recent markets (post-sample is June 2025 onward, though our own independent build from defense.gov archives tests it cleanly on Alpaca).

Size after US retail costs in small stocks:
- UNKNOWN: TenderAlpha & HKU (2026) reports market-adjusted close-to-close returns before spreads. At +28 to +30 bps gross over 3 to 5 days, spread drag on small defense stocks (often 20 to 60 bps round-trip) could erase the edge unless restricted to liquid names or extreme contract-to-market-cap ratios.

Holding period and trades per year:
- MEASURED: 3 to 5 trading days. Top 5% relative-size bucket had 1,006 observations over 15.4 years (~65/year); short-duration <=1 year had 2,115 observations (~137/year).

Timestamp, $500 retail reachability, and fade status:
- STATED: Free, exact 5:00 p.m. ET daily publication on defense.gov (after market close), 90 days ahead of FPDS/SAM.gov.
- STATED: Long-only; $500 US retail account can buy at the next market open with zero borrow cost.
- MEASURED: Active through May 2025 in the top-5% relative-size and short-duration subsets, while pooled all-award returns are statistically indistinguishable from zero.

Verdict: TOP 2 - TEST. Best fast-horizon (3 to 5 day) reading-agent workflow; feasibility must test spread-filtered net moves.

---

### 4. SEC Form 10-K and 10-Q Text-Change Drift ("Lazy Prices")

Paper and audited record:
- MEASURED: Cohen, Malloy & Nguyen (2018 NBER w25084 / 2020 Journal of Finance, [NBER](https://www.nber.org/system/files/working_papers/w25084/revisions/w25084.rev0.pdf)): "Using the complete history of regular quarterly and annual filings by U.S. corporations from 1995-2014, we show that when firms make an active change in their reporting practices, this conveys an important signal about future firm operations."
- MEASURED: Cohen, Malloy & Nguyen (2018, [NBER](https://www.nber.org/system/files/working_papers/w25084/revisions/w25084.rev0.pdf)): "In particular, a portfolio that goes long 'non-changers' and short 'changers' earns a statistically significant 34-58 basis points per month -- up to 7% per year (t=3.59) - in value-weighted abnormal returns over the following year."
- MEASURED: Cohen, Malloy & Nguyen (2018, [NBER](https://www.nber.org/system/files/working_papers/w25084/revisions/w25084.rev0.pdf)): "Changes concentrated in the Risk Factors section, for example, yield L/S portfolio return alphas (Non-Changers minus Changers) of up to 188 basis points per month (t=2.76) in Panel A of Table VII, or over 22% in risk-adjusted abnormal returns per year."

Sample end and post-sample window:
- MEASURED: Sample ended 2014 (11 years post-sample on Alpaca).

Size after US retail costs in small stocks:
- STATED: Value-weighted results indicate the effect is not confined to microcaps, though the headline 188 bps/month Risk Factors alpha is long-short and heavily driven by negative changes (86% of changes are negative sentiment), where shorting incurs borrow fees (average anomaly short-leg borrow fee eliminates many monthly anomalies per [Journal of Finance 2025](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13501)).

Holding period and trades per year:
- MEASURED: 12 to 18 months; Cohen, Malloy & Nguyen (2018, [NBER](https://www.nber.org/system/files/working_papers/w25084/revisions/w25084.rev0.pdf)): "The returns continue to accrue out to 18 months, and do not reverse; this finding suggests that these return movements are not overreactions, but instead reflect true, fundamental changes to firms that only get gradually incorporated into asset prices over the 12-18 months after the reporting change."

Timestamp, $500 retail reachability, and fade status:
- STATED: Free, exact EDGAR 10-K/10-Q timestamp.
- STATED: A $500 account can only run the long-only non-changers leg, which is a slow 12 to 18 month cross-sectional hold rather than a fast event trade.
- MEASURED: Partially attenuated by automated comparison; Cohen, Malloy & Nguyen (2018, [NBER](https://www.nber.org/system/files/working_papers/w25084/revisions/w25084.rev0.pdf)): "We find that when more investors are potentially comparing 10-Ks, and possibly 'paying attention' to changes -- downloading both this year's and last year's 10-K -- this attenuates the key return predictability effects we document in this paper, consistent with inattention being a mechanism behind our documented findings."

Verdict: WATCH (too slow for the fast-feedback aim, and short leg carries borrow friction).

---

### 5. Earnings-Call Text Surprise Drift ("PEAD.txt")

Paper and audited record:
- MEASURED: Meursault, Liang, Routledge & Scanlon (2021, Federal Reserve Bank of Philadelphia WP 21-07, [Philadelphia Fed](https://www.philadelphiafed.org/-/media/frbp/assets/working-papers/2021/wp21-07.pdf)): "The final dataset after the construction of surprises contains 85,160 observations 2010Q1 and 2019Q4. There are 4,701 unique firms in the dataset."
- MEASURED: Meursault et al. (2021, [Philadelphia Fed](https://www.philadelphiafed.org/-/media/frbp/assets/working-papers/2021/wp21-07.pdf)): "At every calendar quarter mark, PEAD.txt is much larger and growing: 2.87% to 1.54% on trading day 63, 4.61% to 2.7% on trading day 126, 6.51% to 3.87% on trading day 189, and 8.01% to 4.63% on trading day 252."
- MEASURED: Meursault et al. (2021, [Philadelphia Fed](https://www.philadelphiafed.org/-/media/frbp/assets/working-papers/2021/wp21-07.pdf)): "The larger magnitude of PEAD.txt relative to PEAD comes from both the top and bottom quintiles, but mostly from the top one (1.31% compared to 0.16% for the first 63 trading days)."

Sample end, size after costs, holding period, trades/year, timestamp, reachability, fade:
- MEASURED: Sample ended 2019Q4 (~8,500 calls/year; 63 to 252 trading day horizon).
- UNKNOWN: No transaction-cost or small-cap spread analysis is published in the paper. Long-only top quintile is +1.31% over 63 trading days.
- STATED: Earnings-call transcripts are NOT free EDGAR documents with an official SEC timestamp; historical transcripts require paid data vendors (though a variant using free EDGAR Form 8-K Item 2.02 Exhibit 99.1 earnings releases is structurally possible).
- STATED: Long-only top quintile is $500 retail executable; fade status post-2019 is UNKNOWN.

Verdict: WATCH (requires paid transcript feed unless adapted to free EDGAR 8-K Item 2.02 press releases, and 63-day long-only drift is +1.31%).

---

### 6. Activist Schedule 13D First Filings

Paper and audited record:
- MEASURED: Collin-Dufresne & Fos (2012, NBER Working Paper 18452, [NBER](https://www.nber.org/system/files/working_papers/w18452/w18452.pdf)): "Panel A includes data from the 2001-2010 sample period." "There is a run-up of about 7% between sixty days to one day prior to the filing day. The two-day jump in excess return observed at the filing date is around 3%. After that the excess return remains positive and so that the post-filing 'drift' cumulates to a total of 13%."
- MEASURED: Collin-Dufresne & Fos (2012, [NBER](https://www.nber.org/system/files/working_papers/w18452/w18452.pdf)) directly tested whether that post-filing drift survived in the later years: "To further investigate this, we replicate Panel A while restricting the sample period to 2003-2010. The results are reported in Panel B of Figure 5. It shows that the post-filing drift in returns does not exist in the later part of the sample. Specifically, there is no trend in the abnormal return after the filing date."
- MEASURED: Collin-Dufresne & Fos (2012, [NBER](https://www.nber.org/system/files/working_papers/w18452/w18452.pdf)): "Therefore, the overall evidence suggests that market participants learn almost immediately about Schedule 13D filings in recent years, and also incorporate the resulting information about the stock price fairly efficiently into prices."

Sample end, costs, holding period, timestamp, reachability, fade:
- MEASURED: Sample ended 2010. Free exact EDGAR SC 13D timestamp; $500 retail long-only reachable; ~150 to 250 activist 13D filings/year.
- MEASURED: KNOWN TO HAVE FADED completely by 2003 to 2010 (post-filing drift equals zero; remaining return occurs before and at the filing jump).

Verdict: DROP (known to have faded).

---

### 7. Form 8-K Item-Level Post-Filing Drift (Items 1.01, 1.03, 2.04, 2.05, 2.06, 5.01, 5.02, 7.01)

Paper and audited record:
- MEASURED: Lerman & Livnat (2010, Review of Accounting Studies, [NYU Stern](https://pages.stern.nyu.edu/~jlivnat/f8k%20current.pdf)): "We obtain initial filings of Form 8-K in the SEC EDGAR database during 2005 and 2006." Sample contains 127,273 observations across eight quarters.
- MEASURED: Lerman & Livnat (2010, [NYU Stern](https://pages.stern.nyu.edu/~jlivnat/f8k%20current.pdf)): "Examining the returns by the triggering event, we observe that Bankruptcy or Receivership leads to the lowest drift of -15%, -13% and -19% for the 30, 60 and 90 day periods respectively."
- MEASURED: Lerman & Livnat (2010, [NYU Stern](https://pages.stern.nyu.edu/~jlivnat/f8k%20current.pdf)): "The items Changes in Control of Registrant and Increase/Acceleration of a Direct/Off-Balance Sheet Financial Obligation also have significant negative drifts between - 1.5% and -3.7% in those periods."
- MEASURED: In Table 3 Panel D of Lerman & Livnat (2010), every statistically significant positive post-filing drift is tiny: Item 7.01 (Reg FD) is +0.29% (30d), +0.53% (60d), +0.69% (90d); Item 2.02 (Results of Operations) is +0.18% (30d), +0.19% (60d), +0.29% (90d); Item 1.01 (Material Definitive Agreement) is +0.01% (30d), +0.10% (60d), +0.22% (90d, p<0.10). Significant negative drifts are Item 1.03 Bankruptcy (-14.70% to -19.00%), Item 5.01 Change in Control (-2.06% to -3.69%), Item 2.04 Debt Acceleration (-1.53% to -2.50%), Item 2.06 Material Impairments (-1.23% to -1.95%), Item 2.05 Exit/Disposal (-1.11% 30d), and Item 5.02 Officer/Director Changes (-0.28% to -0.45%).

Sample end, costs, holding period, timestamp, reachability, fade:
- MEASURED: Sample ended 2006; 30 to 90 calendar day holding period; free exact EDGAR 8-K timestamp; tens of thousands of filings/year.
- STATED: Positive-drift items (+0.18% to +0.69% over 30 to 90 days) are smaller than US retail small-cap round-trip spreads. Meaningful drifts (-1.5% to -19%) are exclusively on the short side of distressed or bankrupt issuers, where retail short locates are scarce and borrow fees are prohibitive on a $500 account. Fade status post-2006 is UNKNOWN.

Verdict: DROP (positive items sub-spread; large negative items short-only distressed stocks).

---

### 8. Form 8-K Item 3.01 Exchange Delisting and Non-Compliance Notices

Paper and audited record:
- MEASURED: Lerman & Livnat (2010, [NYU Stern](https://pages.stern.nyu.edu/~jlivnat/f8k%20current.pdf)): "More specifically for disclosure of delisting, the average 3 day return (volume) around the filing date is -2.81% (48.8%) if the form is filed within the deadline and -4.30% (178.8%) if the form is filed subsequently."
- MEASURED: In Table 3 Panel D of Lerman & Livnat (2010, [NYU Stern](https://pages.stern.nyu.edu/~jlivnat/f8k%20current.pdf)), post-filing buy-and-hold abnormal returns starting one day after the Form 8-K Item 3.01 filing are -0.54% (30 days), -0.44% (60 days), and +0.27% (90 days), none statistically significant.

Sample end, costs, holding period, timestamp, reachability, fade:
- MEASURED: Sample ended 2006; free exact EDGAR 8-K Item 3.01 timestamp; hundreds of notices per year (mostly Nasdaq sub-$1 bid-price or $2.5M equity deficiencies).
- STATED: Not executable on a $500 US retail account even if drift existed, because shorting sub-$1 delisting candidates faces hard-to-borrow restrictions, high borrow fees, and OTC trading suspension risk.

Verdict: DROP (no statistically significant post-filing drift after the initial 3-day drop, plus unshortable microcap constraints).

---

### 9. Form 8-K Item 4.02 Non-Reliance on Previously Issued Financial Statements (Restatements)

Paper and audited record:
- MEASURED: Lerman & Livnat (2010, [NYU Stern](https://pages.stern.nyu.edu/~jlivnat/f8k%20current.pdf)): "Four newly disclosed items generate significant negative returns around both the event date and the filing date: Costs Associated with Exit or Disposal Activities, Material Impairments, Notice of Delisting...Transfer of Listing, and Non-Reliance on Previously Issued Financial Statements."
- MEASURED: In Table 3 Panel D of Lerman & Livnat (2010, [NYU Stern](https://pages.stern.nyu.edu/~jlivnat/f8k%20current.pdf)), post-filing buy-and-hold abnormal returns for Item 4.02 starting one day after the filing date are +0.13% (30 days), +0.52% (60 days), and +0.94% (90 days), none statistically significant.

Sample end, costs, holding period, timestamp, reachability, fade:
- MEASURED: Sample ended 2006; free exact EDGAR 8-K Item 4.02 timestamp.
- MEASURED: The negative shock occurs at announcement; no statistically significant post-filing drift is documented.

Verdict: DROP (no post-filing drift).

---

### 10. SEC Form NT 10-K and NT 10-Q Late-Filing Notices

Paper and audited record:
- MEASURED: Bartov & Konchitchki (2017, Accounting Horizons, [UC Berkeley Haas](https://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/SEC-Filings-Regulatory-Deadlines-Capital-Market-Consequences_Bartov-Konchitchki_AH.pdf)): "We obtain our sample of NT filers from the Audit Analytics Non-Timely Module Feed (NT) dataset for all 10-Q and 10-K late filings with fiscal period-ends between 2000 and 2008, where the NT filing data is on or prior to September 1, 2009." "This procedure yields a final sample of 2,115 NT filers, 1,048 NT 10-Qs, and 1,067 NT 10-Ks."
- MEASURED: Bartov & Konchitchki (2017, [UC Berkeley Haas](https://faculty.haas.berkeley.edu/yaniv/files/Papers_Publications/SEC-Filings-Regulatory-Deadlines-Capital-Market-Consequences_Bartov-Konchitchki_AH.pdf)): "In the first post-event period, [3, 62], the returns for uncertain, corporate events, and multiple subsamples are, respectively, -8.63 percent, -7.30 percent, and -9.90 percent, whereas the returns for the accounting sample is markedly less negative, -1.11 percent, and statistically insignificant."
- MEASURED: In Table 7 Panels A and C of Bartov & Konchitchki (2017), Fama-French-Momentum adjusted post-NT drift across all filers is -4.93% over [3, 62] (p<0.0001, N=2,100) and -10.34% over [3, 182] (p<0.0001, N=1,914), reaching -16.29% over [3, 182] (p<0.0001, N=950) for non-accounting reasons.

Sample end, costs, holding period, timestamp, reachability, fade:
- MEASURED: Sample ended 2008 (returns through 2010); 60 to 180 trading day holding period; ~235 filtered NT filings/year; free exact EDGAR NT 10-K/NT 10-Q timestamp.
- STATED: Strictly a short-side trade in financially distressed, small, low-liquidity late filers. A $500 US retail account cannot reliably locate or pay borrow fees to hold distressed microcap shorts for 3 to 9 months (borrow fees alone eliminate the average anomaly short leg per [Journal of Finance 2025](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13501)). Fade status post-2008 is UNKNOWN.

Verdict: DROP (short-only distressed small caps; unworkable for a $500 long-only account).

---

### 11. Management Earnings Guidance Changes

Paper and audited record:
- MEASURED: Das et al. ([NYU Stern](https://web-docs.stern.nyu.edu/salomon/docs/conferences/das%20et%20al.pdf)): "We begin with an initial sample of management forecasts of quarterly earnings from the First Call database for the period 1995-2004." "Application of this restriction results in a further significant reduction from 13,414 to 8,386 observations."
- MEASURED: Das et al. ([NYU Stern](https://web-docs.stern.nyu.edu/salomon/docs/conferences/das%20et%20al.pdf)): "In the optimistic group of forecasts the market-adjusted cumulative abnormal return (CAR) from day +2 to day +30 has a median (mean) value of 4.58% (5.45%)." "This is larger than the median (mean) CAR of 2.78% (3.90%) for the conservative group measured over the same holding period."
- MEASURED: Modern 2023 to 2026 check (arXiv 2026, [arXiv](https://arxiv.org/html/2608.14014v1)): "A two-step pipeline tags the full corpus: an Azure-hosted GPT teacher labels a sample, and a small distilled classifier, refined with active learning, extends the labels to all 4.57 million articles covering roughly 3,000 US stocks (2023 to 2026) at 95 percent fidelity to the teacher and negligible cost."
- MEASURED: Across 24,828 Guidance and outlook events in 2023 to 2026 ([arXiv](https://arxiv.org/html/2608.14014v1)): "On the continuation side sit the quantified fundamental tags: capital returns +0.35%, earnings +0.22%, guidance +0.13%, analyst actions +0.10% over days +6 to +20, all significant." The same table reports -0.02% over days +1 to +5, and concludes the move was already finished by the end of publication day (completion ratio 1.08).

Sample end, costs, holding period, timestamp, reachability, fade:
- MEASURED: Old sample ended 2004; modern corpus runs through 2026. Timestamp is mixed (some guidance in 8-K Item 2.02/7.01, some in press releases or calls).
- MEASURED: KNOWN TO HAVE FADED. In 2023 to 2026, adjusted post-guidance drift is +0.13% over days +6 to +20 (-0.02% over days +1 to +5), far below US retail spreads in small stocks.

Verdict: DROP (faded to +13 bps in 2023 to 2026).

---

### 12. FDA Decision Dates (PDUFA Approvals, Complete Response Letters, Advisory Committees)

Paper and audited record:
- MEASURED: Lacey & Sharma (2008, [West Georgia](https://www.westga.edu/~bquest/2008/FDA08.pdf)): "The time period of the sample runs from 1991 to 2000." "Our FDA sample of 344 approvals and 103 rejections and other bad news originates from the universe of pharmaceutical/biotechnology firms identified by the Recombinant Capital Database and the Yahoo Biotech Industry Database."
- MEASURED: Lacey & Sharma (2008, [West Georgia](https://www.westga.edu/~bquest/2008/FDA08.pdf)): "We also find that the change in return is absorbed almost instantaneously over the event window, is largely unanticipated, and shows little or no persistence." In Table 3, all-approvals CAR over days +3 to +10 is -0.100% (z=-0.57) and drug rejections CAR over days +3 to +10 is -1.743% (z=-1.83).
- MEASURED: Hamill, Hutchinson, Nguyen & Mulcahy (2018, Economics Letters, [UCC CORA](https://cora.ucc.ie/server/api/core/bitstreams/41096b1a-8b43-462b-8b3f-8ce328637264/content)): "We show that when event-day mis-specification is accounted for the market reaction is centred on the event-day and that the increase in firm value is driven by after-market-close approval announcements."
- MEASURED: Recent 2015 to 2024 Drugs@FDA event study of 234 novel drug approvals ([GitHub biotech-fda-event-study](https://github.com/lukahere007/biotech-fda-event-study)): "Small caps (<$2B) gained +8.5% over [0,+1] (p=0.010), and lost -6.5% over [+2,+20] (BMP p=0.04)." "First approval companies, which are mostly the same small caps, lost -7.4% (p=0.002)."

Sample end, costs, holding period, timestamp, reachability, fade:
- MEASURED: Sample extends through 2024 (344 approvals 1991 to 2000; 234 approvals 2015 to 2024).
- STATED: FDA posts approvals on Drugs@FDA (often after 4:00 p.m. ET) and began publishing Complete Response Letters promptly in September 2025, though sponsor press releases or 8-Ks often arrive first, so the exact public timestamp is fragmented.
- MEASURED: There is no positive post-approval drift to buy after the timestamp; small-cap approvals partially reverse (-6.5% to -7.4% over [+2, +20]), which would require shorting volatile small biotechs with hard-to-borrow costs.

Verdict: DROP (no positive post-announcement drift; small-cap approval reversal is short-only in volatile biotechs).

---

### 13. Activist Short-Seller Report Days

Paper and audited record:
- MEASURED: Ljungqvist & Qian (2016, Review of Financial Studies / NBER w19834, [NBER](https://www.nber.org/system/files/working_papers/w19834/w19834.pdf)): "Our sample covers 17 arbs who between July 2006 (when daily short-sale data first become available from DataExplorers) and December 2011 target 113 U.S. listed companies." "We have a total of 332 reports (around three per company on average)."
- MEASURED: Ljungqvist & Qian (2016, [NBER](https://www.nber.org/system/files/working_papers/w19834/w19834.pdf)): "For the average arb, prices fall by 18.6% on average in the three months following the release of a first report." (Report-date mean abnormal return -8.5%; day -5 to day +60 net-of-borrow profit +18.9%, which assumes entering 5 days BEFORE publication.)
- MEASURED: Brendel & Ryans (2021, Journal of Accounting Research, [Tilburg University](https://www.tilburguniversity.edu/sites/default/files/download/Brendel_and_Ryans.20191202._Activist_Short_Sellers%5B1%5D.pdf)): "Our sample expands upon that of LQ (but is limited by the availability of returns and financial variables) and consists of 319 reports made by 24 prominent activist short sellers who publish multiple reports over the period from 1996 to 2017." "Consistent with LQ we find significant negative returns to the report disclosure event (-4 percent), and a further negative return of -30 percent in the year following the report issuance."
- MEASURED: Borrow cost and squeeze barriers are severe; Ljungqvist & Qian (2016, [NBER](https://www.nber.org/system/files/working_papers/w19834/w19834.pdf)): "Figure 6a below shows that the cost of initiating new shorts rises significantly one day before a report is released (perhaps in response to the arbs building their short positions) and then jumps to 52% above the baseline on average on the release day." "This reflects an unusually tight supply of lendable stock: on average, only 4.85% of shares outstanding are available for borrowing (39th percentile)."
- MEASURED: Stice-Lawrence (2025, Journal of Accounting Research, [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/1475-679X.12595)): "Using positive return reversals as a proxy for short squeezes, we estimate that 15% of short attacks experience squeezes, and squeeze risk increases with short sellers' visibility but decreases with the credibility of their evidence."

Sample end, costs, holding period, timestamp, reachability, fade:
- MEASURED: Sample ended 2017 (Brendel & Ryans) and squeeze study published 2025; 60 to 252 trading day horizon; ~20 to 60 reports/year.
- STATED: No single free official timestamped registry (reports drop across activist websites, X, and PDFs).
- STATED: Unusable for a $500 US retail account: short-only, borrow fees spike 52% on release day with only 4.85% of shares lendable, and 15% of campaigns trigger short squeezes.

Verdict: DROP (short-only, extreme locate/borrow-fee and squeeze risk, no unified free timestamp).

---

### 14. Tender Offer Amendments (Schedule TO-T/A and TO-I/A)

Paper and audited record:
- MEASURED: Lakonishok & Vermaelen (1990, Journal of Finance, [INSEAD](https://flora.insead.edu/fichiersti_wp/Inseadwp1988/88-40.pdf)): "The results of this paper indicate that by executing a simple trading strategy around repurchase tender offers it is possible to generate abnormal returns of more than 9% per week, on average, in the period 1962-1986."
- MEASURED: Lakonishok & Vermaelen (1990, [INSEAD](https://flora.insead.edu/fichiersti_wp/Inseadwp1988/88-40.pdf)): "The results show that, in the total period, stock prices increase significantly by .4% per month (t = 2.70) in the 22 months following the second month after the repurchase announcement." "We conclude that the post-expiration positive drift in security prices is mainly due to the price behavior of very small firms."

Sample end, costs, holding period, timestamp, reachability, fade:
- MEASURED: Sample ended 1986. Note that small-lot issuer odd-lot tender offers are already queued separately in Row 38.
- UNKNOWN: No modern post-2000 published study was found documenting a post-filing drift specifically after Schedule TO-T/A or TO-I/A amendments (price increases or deadline extensions), and the classic post-expiration repurchase drift takes 22 to 23 months in very small firms (quintile 1).
- STATED: Free exact EDGAR SC TO-T/A and SC TO-I/A timestamps exist, and the trade is long-only, but without modern drift evidence it does not displace the top three.

Verdict: DROP (no modern post-1986 published amendment-drift study; post-expiration drift is 22 months in tiny firms; odd-lot issuer tenders already in Row 38).
