# Plan 63: closed-end funds after activist Schedule 13D filings

Status DRAFT.

Queue 102, ledger 206. No price, quote, action amount, placebo or target return was read to produce this draft. No vendor request, freeze, validation or score is authorized.

## What is known before prices

- MEASURED from the sealed [Count 102 census](../docs/research/124_count_102_cef_activist_13d_census.md) and its private metadata: 437 filing rows, 337 same-filer same-Eastern-date clusters, 324 distinct filing dates, 229 subject fund CIKs, and 38 filer groups. The census owner reconciled the last two against the sealed event and summary files; 163 and 36 in the original prose were transcription errors. Saba accounts for 190 of the 337 filer-days, or 56.4%. Among individual events, 14.6% arrived pre-market, 44.2% during standard market hours, and 41.2% after the standard close; these are not the actual Plan 63 eligible close counts.
- STATED. [Bradley, Brav, Goldstein and Jiang (2010), Table 3](https://business.columbia.edu/sites/default/files-efs/pubfiles/4118/activist_arb.pdf) studies 127 open-ending attempts with annual fund observations, not timestamped 13D returns. Unadjusted full-sample discounts to NAV fell from 19.82% in the year before an attempt to 14.46% in the attempt year and 8.42% in the following year, including zero discounts after open-ending. The surviving funds' corresponding values were 19.82%, 14.41%, and 14.34%. That is evidence about discounts and corporate outcomes, not a gross or net 5-, 20-, or 60-session return from this entry.
- STATED. [Souther (2016), author's summary](https://corpgov.law.harvard.edu/2016/02/22/the-effects-of-takeover-defenses-evidence-from-closed-end-funds/) and the [journal article](https://www.sciencedirect.com/science/article/pii/S0304405X15001725) report that funds with more takeover defenses had weaker market reactions to activist 13D filings. The material opened here does not establish a numerical effect after this plan's delayed entry. [ICI's later tender-offer analysis, Figure 5](https://www.ici.org/system/files/2025-09/25-cl-amendments-nyse-company-manual.pdf) finds narrower relative discounts between initial public filings and completion of 34 forced tender offers in 2015 to June 2023; that conditions on an eventual tender and uses periods rather than a fixed post-acceptance holding window. No direct, comparable replication of the after-entry edge was verified. UNKNOWN: how much price response precedes the first eligible close.
- STATED, excluded comparator. [Brav et al.'s broader activism study](https://archive.fdic.gov/view/fdic/12005/fdic_12005_DS1.pdf) reports approximately 3.2% buy-and-hold abnormal return on days -10 to -1 and roughly another 2% on filing day and the following day, but excludes closed-end funds by design. Do not transfer either figure to this CEF replay. [Souther's SSRN record](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2729874) was accessible as an abstract only; the referenced full text could not be opened. UNKNOWN: exact CEF filing-day effect and how much survives the eligible close.
- STATED. PCEF is the sole judged benchmark. [Invesco's factsheet](https://www.invesco.com/us-rest/contentdetail?contentId=9cdf66b451c41410VgnVCM100000c2f1bf0aRCRD) dates inception to February 19, 2010, before the full 2016 to 2026 census and the proposed 2015 placebo padding. PCEF is a single NYSE Arca index ETF, not a NAV-matched hedge: its index emphasizes taxable investment-grade, high-yield, and equity option-writing funds. [Amplify's YYY](https://amplifyetfs.com/yyy/) launched June 12, 2012 and also spans the period, but its yield, discount and liquidity selection and yield weights are a different tilt, not demonstrated to be a better single benchmark for this universe. YYY may be shown only if already available at no extra acquisition cost; otherwise omit it. No benchmark prices or coverage gaps have been checked yet.

## Proposed scheduling and scoring unit

- STATED by the lead. Use US-listed common shares only and the census's already-qualified initial, re-entry and Item 4 escalation events. Entry is the first official regular close at least 60 minutes after SEC acceptance, including early closes. Exit at the official close N exchange sessions later. Use the same exit and entry clocks on PCEF. No faster order, substitute session or second open position in a fund.
- STATED draft tie and overlap rule used in the count. One trade per subject fund CIK per Eastern filing date. Keep earliest acceptance and break exact timestamp ties by accession. In chronological order, a fund's first eligible scheduled trade reserves it through the exit close; veto a later filing accepted before that exit or scheduled at or before that close. No requeue. On this census, using only the scheduled-close overlap condition gives identical counts. The draft reserves by schedule even if the earlier trade later proves unfillable or exits early, to keep replacement independent of prices. Confirm this treatment before freeze.
- STATED, fixed by the lead. Trade the fund-day, then equal-weight placed paired returns within the census's normalized filer-day (average multiple fund pairs, so one filer cannot multiply the day's weight by filing across a family). Equal-weight those filer-day observations in the judged mean and trim, and cluster inference by Eastern filing date so two filers on the same date do not count as two independent dates. Non-Saba is measured on placed non-Saba filer-days. Bind all execution to the recorded share-class identity.

## Price-blind schedule

MEASURED from the pinned metadata by the [count script](count_63.py). These are scheduled candidates, not fills; they do not use prices, alias availability, tradability, actions or quote coverage. One duplicate fund-day is removed before scheduling. Cutoff means exit on or before November 25, 2026, so as not to require a future close.

| Hold, sessions | Fund trades scheduled (Saba / other) | Filer-days scheduled (Saba / other) | Distinct filing dates scheduled | Fund trades mature (Saba / other) | Filer-days mature (Saba / other) | Distinct filing dates mature | Last scheduled exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 5 | 434 (260 / 174) | 334 (190 / 144) | 322 | 431 (257 / 174) | 332 (188 / 144) | 320 | 2026-12-03 |
| 20 | 432 (260 / 172) | 332 (190 / 142) | 321 | 427 (256 / 171) | 328 (187 / 141) | 317 | 2026-12-24 |
| 60 | 394 (240 / 154) | 305 (177 / 128) | 297 | 385 (232 / 153) | 298 (171 / 127) | 290 | 2027-02-24 |

MEASURED by Eastern filing year. Each hold column shows mature filer-days as total (Saba / other), with mature fund-trade count in brackets. Through 2025 the mature and scheduled counts coincide.

| Year | N = 5 | N = 20 | N = 60 |
| --- | ---: | ---: | ---: |
| 2016 | 31 (8 / 23) [34] | 30 (8 / 22) [33] | 27 (6 / 21) [28] |
| 2017 | 23 (6 / 17) [38] | 23 (6 / 17) [38] | 21 (6 / 15) [35] |
| 2018 | 15 (3 / 12) [15] | 15 (3 / 12) [15] | 15 (3 / 12) [15] |
| 2019 | 27 (13 / 14) [31] | 27 (13 / 14) [31] | 26 (12 / 14) [30] |
| 2020 | 37 (21 / 16) [42] | 37 (21 / 16) [42] | 31 (18 / 13) [36] |
| 2021 | 14 (7 / 7) [14] | 14 (7 / 7) [14] | 11 (6 / 5) [11] |
| 2022 | 23 (13 / 10) [28] | 23 (13 / 10) [28] | 22 (12 / 10) [27] |
| 2023 | 65 (46 / 19) [87] | 64 (46 / 18) [86] | 62 (45 / 17) [83] |
| 2024 | 55 (40 / 15) [84] | 55 (40 / 15) [84] | 50 (37 / 13) [73] |
| 2025 | 26 (18 / 8) [37] | 26 (18 / 8) [37] | 22 (17 / 5) [32] |
| 2026 | 16 (13 / 3) [21] | 14 (12 / 2) [19] | 11 (9 / 2) [15] |

Each full 2026 schedule has 18 filer-days (15 Saba / 3 other) and 24 fund trades. STATED, fixed by the lead: only exits on or before the last complete session of November 25, 2026 are in the test. No later top-up. Do not label missing future outcomes as refusals. Official future holiday and early-close schedule: [NYSE hours and calendars](https://www.nyse.com/trade/hours-calendars).

MEASURED, price-free identity attrition from the [count script](count_exclusions_63.py). The lead excluded 12 unresolved fund CIKs (20 raw filing rows) and one fund with no mature window (one raw filing). The custodian's dated deny list and stricter full-horizon check showed zero collisions among known identifiers. This cannot rule out a CUSIP collision for 15 admitted segments without a verified cover-page CUSIP. Target and placebo ceilings below are total / non-Saba filer-days. Approved successor marks can further reduce placebo counts.

| Hold | Target, 15 flagged segments included | Placebo, 15 flagged segments included | Target without 15 | Placebo without 15 |
| --- | ---: | ---: | ---: | ---: |
| 5 | 314 / 129 | 279 / 109 | 298 / 115 | 263 / 95 |
| 20 | 311 / 127 | 267 / 105 | 296 / 114 | 252 / 92 |
| 60 | 281 / 113 | 240 / 91 | 268 / 100 | 228 / 79 |

STATED, fixed by the lead. Do not start Stage A if every price-free target upper bound is below 260. Stage A consists only of retained placebo bars, PCEF and corporate actions. No subject target bars or closing quotes are acquired unless a hold qualifies and the lead separately approves Stage B for that hold.

STATED, fixed by the lead. Retain the 15 specially flagged segments in the judged docket and pooled power input. Vendor requests use ticker and date, those tickers have dated primary SEC evidence, and excluded funds have no docket or acquisitions. That is not a verified CUSIP match and does not eliminate the possibility of misidentification. Show aggregate results excluding any fund pair whose target interval touches a flagged segment; rebuild filer-day averages from remaining fund pairs. This is shown only, not another rule, hold choice or verdict.

## Costs and settlement

- STATED. Independently fund each whole-share leg with $500, maximum shares affordable including entry costs, leftover cash idle. Pay benchmark side the greater of 5 bp or $0.01 per share. Compare net returns before taxes, each divided by $500; this is not a claim to execute an ETF short.
- STATED. Fund costs follow the [Plan 48 estimator and exit carry](PREREG_48_muni_cef_tax_loss.md): duration-weighted median relative spread of valid uncrossed SIP quotes in the five minutes from close minus six to close minus one, half-spread, quote lifetime 60 seconds and at least 180 seconds valid coverage; start requesting at close minus seven so an alive quote carries in. For Plan 63 use the lead's explicit 10 bp measured half-spread floor, 50 bp proxy when unavailable, and add 5 bp per side. Charge exit on the larger of entry and exit half spreads, after floor or proxy. The actual Plan 48 code had no 10 bp measured floor; the lead's Plan 63 instruction adds it. All clock offsets use the session's actual close.
- STATED. Use independently verified cash entitlements with ex-date after entry through exit, underlying share counts on the correct split basis, and cash terms for rights, mergers, liquidations and delisting when actually applicable. The census identifies true common-share delistings inside 60 sessions. Do not remove them after the fact and do not silently assume a last close equals proceeds. Proposed: verified mandatory cash-out at the legal amount, credited on entitlement with proceeds idle until the scheduled mark; verified successor shares valued to the same scheduled mark using independently mapped identity; unsupported or unverified terms stop for a lead ruling on the packet rather than dropping hard cases. Pending rules for cash in lieu, default handling and acquisition of successor data must be fixed before approval.

## Marks and miss reading

All six must hold. The lead fixed at least 230 actually placed filer-days for all candidate holds, about 77% of the smallest measured mature envelope of 298, without seeing price or outcomes.

| Mark | Draft bar |
| --- | --- |
| Placement | At least 230 placed filer-day clusters |
| Money | Raw paired mean above zero |
| Evidence | Positive winsorized paired mean with t at least 2, clustered by filing date; symmetric cap equals five times the corresponding placebo scaled MAD, fixed numerically before any target prices |
| Trim | Raw paired mean above zero after dropping the best 1% of filer-day paired outcomes, rounded up |
| Year breadth | At least 7 of 11 filing years with positive raw paired mean; empty year cannot count |
| Filer breadth | Raw paired mean across placed non-Saba filer-days above zero; empty subgroup cannot count |

Use Plan 61's miss reading: positive raw mean with winsorized t from 1 up to but not including 2 means not shown, not refuted, with only a forward pretend-money log eligible for consideration. A nonpositive raw mean or t below 1 closes the row. Other misses do not grant automatic forward approval.

STATED, fixed by lead. Validation before go is entirely price-free: identity, positive-volume endpoint existence, and independently reconciled action, split and terminal coverage only. Print an upper bound on placed filer-days, not actual affordable placements. If even the upper bound is below 230, don't spend the go. Check whole-share affordability only during the separately authorized go; it is expected to remove few or no events at a $500 budget, but that expectation is unmeasured. Exact placed count still has to meet 230 inside the go.

## Placebo and power, pending

- STATED, fixed by the lead. For each eligible fund-day and N, use one matched N-session placebo ending on the fifth completed session close strictly before SEC acceptance, without replacement. Exclude any window touching any subject fund interval from that fund's candidate entry through 60 sessions later, inclusive, across all raw census events, plus approved successor valuation endpoints. PCEF overlap is permitted only inside the custodian's isolated aggregate. No target-interval price of any subject fund is read before the go. The runner can access only positive-volume raw SIP endpoints and independently verified split and cash adjustments for the pinned placebo scopes. Report counts, sample SD, scaled MAD and its derived cap (five times scaled MAD); no mean, median, sign, per-event output or raw values. Average fund pairs within filer-day before measuring dispersion. First source audit, separate written lead approval, one locked attempt. Do not run now.
- MEASURED. The January 1, 2016 SIP history limit removes 0, 1 and 8 entire placebo filer-day clusters for 5, 20 and 60 sessions. The same-fund embargo removes another 36, 44 and 36, leaving ceilings of 296, 283 and 254 filer-days, including 123, 119 and 103 non-Saba filer-days. These are before successor marks, data coverage or other market-dependent gates. Target counts are unchanged. STATED: the lead accepted the non-Saba shortfall relative to 150 because the placebo dispersion is pooled and the non-Saba score mark tests sign only, not t. The stronger embargo still stands.
- STATED, fixed by the lead. Estimate the gross paired edge needed for a 50% and 80% chance of passing all six post-cost marks. Add 40, 70 and 120 bp pair-drag scenarios to the simulated net edge, applied equally at each hold. The controlling case is a two-scale normal mixture fitted to the aggregate SD and scaled MAD, or Gaussian with measured SD when scaled MAD is at least SD; 0.10 same-filing-date, 0.10 overlapping session and 0.02 same-filer variance shares; 90% placement; 70 bp pair drag. Also show independent and high-dependence cases and placement at 80% and 100%. These sensitivities cannot change the ruling. The fixed power budget is not an accounting change: judged return remains fund net minus PCEF net as two long legs.
- STATED selection. A hold qualifies only if the controlling even-chance gross edge is at most 150 bp. Choose the lowest qualifying gross edge per session; among holds within 10% of the best, choose the shortest. If none qualifies, close without target prices. The assumed filing jump being incorporated by entry is a planning assumption, not a sourced estimate of its size or timing in this universe. The lead alone rules the hold. No placebos, power results, N or cap exist yet.
- Draft source: [dispersion kernel](placebo_63.py), [custody and transport contract](PLACEBO_CUSTODY_63.md), [custodian-only adapter](placebo_run_63.py), [placement and scoring kernels](score_63.py), [power simulation](power_63.py), and [synthetic tests](test_63.py). No market approval or audit artifacts exist. The adapter pins exact files and scopes and can export only one aggregate report. Production preparation and identity/action evidence still require review. Local tests do not validate market inputs.

Custodian scope and request sizing: [draft sealed-data request](DATA_REQUEST_63.md). Hold choice, exact approved alias scope, cash coverage, final terminal action valuation terms, numerical winsor cap and custody approvals remain pending before target freeze.
