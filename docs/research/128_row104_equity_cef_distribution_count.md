# Row 104: Equity Closed-End Fund Non-Monthly and Special Distribution Count

Date: 2026-11-26 (clock read 2026-11-26 10:18 UTC, 03:18 MT)
Status: COUNT DONE, price-blind. The lead's fixed pass line is met on the count. The declaration-date lead time is UNKNOWN (see section 6), so this doc does not clear the trade's two-session rule.
Queue row 104, ledger row 204. Idea source: `docs/127_idea_round_33.md` rank 1.

No price, NAV, quote, bar or reinvestment-price field was requested, read or stored. Raw vendor records stay off the repo under `/home/user/workspace/rig/data/count_104/` (folder 0700, files 0600).

## Pass line (fixed by the lead before the count)

- Pass: at least 150 events on distinct fund-days after removing monthly managed-distribution payers.
- Close: under 100.
- Between 100 and 149: the lead rules.
- The definitions in sections 2 and 3 were written down before any event was tallied. They were not changed after the count.

## Result

- MEASURED: 472 distinct fund-days fall on 241 distinct ex-dates, 2016-01-01 to 2026-10-31.
- MEASURED: The 472 break down as 454 regular events in non-monthly fund-years, 16 rule-flagged extras and 2 vendor-flagged specials.
- MEASURED: With every extra and special removed, 454 regular quarterly fund-days remain, on 234 distinct ex-dates.
- MEASURED: 472 is at least 150, so the count passes the fixed line. The lowest reading, 454, also passes.
- MEASURED: The count is thinning. It went from 58 fund-days in 2016 (14 funds) to 24 in 2025 (6 funds) and 17 in January to October 2026.
- MEASURED: No semiannual or annual payer appears in the roster's equity funds. Every non-monthly fund-year is quarterly.
- UNKNOWN: How many days before the ex-date each amount and date became public. No permitted source gives declaration dates for the counted events (section 6).

## 1. Roster and coverage

- Roster: the plan 53 roster (PCEF holdings by year, method in `research_rig/PREREG_53_taxable_cef_tax_loss.md`). It has 1,224 fund-years and 181 CIKs over turn years 2016 to 2025.
- Stable identifier: the SEC CIK. The live ticker comes from the roster in each year. Ticker segments come from the plan 53 identity segments file (off repo), for example BIGZ to BTX on 2025-02-20 and INB's last session on 2019-12-20.
- Events in calendar year Y count only if the ticker is in the turn-Y roster. For January to October 2026, the 2025 roster tickers are used, limited by known segment end dates.

Coverage against the Investment Company Institute (ICI) year-end count of equity closed-end funds:

| Year | Roster funds | Roster equity funds (rule below) | ICI equity CEFs, year-end | Share |
|---|---:|---:|---:|---:|
| 2016 | 136 | 33 | 200 | 16.5% |
| 2017 | 139 | 34 | 197 | 17.3% |
| 2018 | 136 | 34 | 177 | 19.2% |
| 2019 | 129 | 34 | 177 | 19.2% |
| 2020 | 122 | 30 | 173 | 17.3% |
| 2021 | 120 | 28 | 166 | 16.9% |
| 2022 | 119 | 28 | 160 | 17.5% |
| 2023 | 108 | 33 | 152 | 21.7% |
| 2024 | 109 | 34 | 141 | 24.1% |
| 2025 | 106 | 33 | 137 | 24.1% |

ICI sources: 2016 and 2017 are STATED in the [2018 ICI Fact Book, Table 9](https://www.ici.org/system/files/attachments/2018_factbook.pdf) as domestic plus global equity (118 + 82 and 117 + 80). 2018 to 2024 are STATED in [ICI Fact Book 2025, Chapter 5](https://www.icifactbook.org/pdf/2025-factbook-ch5.pdf). 2025 is STATED in the [ICI Q2 2026 closed-end fund release](https://www.iciglobal.org/research/stats/closedend/cef_q2_26). ICI revises these figures. For example, an ICI Q1 2024 release gave 163 for 2022, while the fact book gives 160.

- MEASURED: The roster covers 16.5% to 24.1% of the equity closed-end fund universe each year (about one fund in five).
- STATED (inference, not measured): PCEF is an income index. Its equity holdings lean toward option-income and covered-call funds, and these mostly pay monthly. Traditional equity funds outside the roster are missing, for example Adams, General American, Gabelli's quarterly funds, Tri-Continental and Central Securities. Those funds pay quarterly, annually and year-end extras more often. The universe count of non-monthly events is therefore likely larger than this roster count. It is not measured here.

## 2. Equity classification (fixed before the count)

- Source: each CIK's earliest Form NPORT-P `primary_doc.xml` on EDGAR (accession list from data.sec.gov submissions JSON). Only the `assetCat` tags were counted. No holding values were kept, and no filing was saved.
- Rule: a fund is equity if EC (common equity) lines are at least 50% of holding lines. The denominator excludes derivatives (DFE, DIR, DCR, DE, DO, DCO), short-term vehicles (STIV), repos (RA) and structured notes (SN). Preferred (EP) counts against equity.
- MEASURED: 171 of 181 CIKs had an NPORT-P. The other 10 left before N-PORT began. All 10 have bond names (Deutsche Multi-Market Income, Brookfield Total Return, three Western Asset income funds, Brookfield High Income, Deutsche High Income Opportunities, Nuveen Build America Bond, Brookfield Mortgage Opportunity, Nuveen High Income December 2018). They were treated as not equity. That treatment is STATED by name only.
- MEASURED: 41 CIKs are equity by the rule. The borderline ones are John Hancock Diversified Income (HEQ, 0.65), BlackRock Capital Allocation (0.70), Cohen & Steers Global Income Builder (INB, 0.78), GAMCO Natural Resources Gold & Income (0.88) and High Income Securities (0.90, a fund of closed-end funds).
- MEASURED: The nearest funds below the cut were NexPoint Diversified Real Estate (0.49), Barings Corporate Investors (0.41) and Barings Participation Investors (0.40). They are excluded. The two Barings funds pay quarterly, so including them would raise the count, not lower it.
- Evidence file (off repo): work file nport_class.jsonl, SHA-256 8bdb752083449c3ccca140a87938649bd250aee9816693629d5078f904fe8ecc. It holds the accession, URL, report date, the document's SHA-256 and the tag counts.

## 3. Events and cadence rules (fixed before the count)

- Source: Alpaca `/v1/corporate-actions?types=cash_dividend` for 2016-01-01 to 2026-10-31, one symbol per call, through the saved data credential.
- Pull: 185 symbols, all returned HTTP 200, all on one page. Fields kept are ex_date, record_date, payable_date, process_date, rate, special, cusip and id. Alpaca carries no declaration date.
- MEASURED: 233 of the 472 counted fund-days (all from the early years) have no record or payable date in the vendor feed. The ex-date is present for every one.
- Fund-day: one CIK on one ex-date. Several records on the same day merge into one fund-day.
- Gap: the days from one regular (non-special) ex-date to the fund's previous regular ex-date. For the fund's first record, the gap to the next one is used.
- Fund-year class, by the median gap in that calendar year: up to 45 days is monthly, 46 to 135 quarterly, 136 to 270 semiannual, over 270 annual.
- Special: any record the vendor flags as special.
- Extra: a regular record whose gap is under half the fund-year's median gap.
- Counted set: regular fund-days in non-monthly fund-years, plus specials and extras of any equity fund, including monthly payers.
- MEASURED: The 41 equity CIKs have 354 live fund-years and 3,251 live fund-days. 238 fund-years are monthly (2,779 regular fund-days removed). 116 are quarterly. None are semiannual or annual. Every roster equity fund-year had at least one live event.
- Evidence files (off repo): work file events_counted.json, SHA-256 325b192f9e5884a2d641b686d22ef7b6b363776176c119008d1ee480320228bd. work file count.py, SHA-256 8748f54ebd0543c7933a95e54d74d226ea52523d301f7d17d96bd62a53250c9a. The raw-page manifest digest is d62defbb65440862b21088fb11e25b58844d72704af6f43c637a334d37301b7a.

## 4. Counts

| Year | Quarterly regular | Specials and extras | Fund-days | Distinct ex-dates | Funds |
|---|---:|---:|---:|---:|---:|
| 2016 | 55 | 3 | 58 | 33 | 14 |
| 2017 | 56 | 7 | 63 | 26 | 19 |
| 2018 | 56 | 1 | 57 | 24 | 14 |
| 2019 | 52 | 1 | 53 | 23 | 14 |
| 2020 | 44 | 0 | 44 | 24 | 11 |
| 2021 | 40 | 1 | 41 | 24 | 10 |
| 2022 | 40 | 1 | 41 | 24 | 10 |
| 2023 | 40 | 1 | 41 | 23 | 10 |
| 2024 | 32 | 1 | 33 | 18 | 8 |
| 2025 | 24 | 0 | 24 | 12 | 6 |
| 2026 (Jan to Oct) | 15 | 2 | 17 | 10 | 8 |
| Total | 454 | 18 | 472 | 241 | 22 |

The distinct ex-date column does not add across years (241 overall).

Semiannual and annual payers: 0 fund-days (MEASURED).

Clustering:

- MEASURED: Of the 241 ex-dates, 159 have one fund, 23 have two, 4 have three, 29 have four, 18 have five, 7 have six and 1 has seven.
- MEASURED: By fund family, 208 ex-dates have one family, 26 have two and 7 have three.
- MEASURED: The four Nuveen option funds (BXMX, DIAX, QQQX, SPXX) are 164 of the 454 quarterly fund-days, and they share ex-dates almost every quarter.

Quarterly payers (fund-days per year, MEASURED):

- BXMX, DIAX, QQQX, SPXX (Nuveen): 4 a year, 2016 to 2025. Each has 1 to 3 in 2026 before Nuveen moved to monthly. Nuveen's N-CSR filed 2026-03-06 says each fund distributes "through its regular monthly distribution".
- FFA (First Trust): 4 a year, 2016 to 2025, and 3 in 2026.
- STK (Columbia Seligman): 4 a year, plus a December extra in 2017, 2018, 2021, 2022, 2023 and 2024.
- MCN (Madison, then XAI): 4 a year, 2016 to 2024. The issuer page shows monthly payments by 2026.
- HEQ (John Hancock): 4 a year, 2016 to 2024.
- IDE, IGA (Voya): 4 a year, 2016 to 2023, then monthly.
- IAE, IRR (Voya): 4 a year, 2017 to 2019 and 2016 to 2019.
- GPM (Guggenheim): 4 a year, 2016 to 2020.
- EXD (Eaton Vance): 4 a year, 2016 to 2018.
- INB (Cohen & Steers): 2016 only.

Specials and extras (18 fund-days):

- Vendor-flagged specials: BST and BSTZ on 2026-09-15, of monthly payers. MEASURED in the vendor feed. STATED by BlackRock's own distribution history (plan 53 native file): one combined row of $2.5541 for BST and $1.6172 for BSTZ, which matches the vendor's two records summed per fund.
- STK December extras: 6, on 2017-12-15, 2018-12-14, 2021-12-10, 2022-12-09, 2023-12-15 and 2024-12-16. These look like real year-end extras.
- Likely rule artifacts, kept because the rule was fixed (10):
  - Eaton Vance 2017-03-22: an extra March ex-date for EOI, EOS, ETB, ETV and ETY, which pay monthly, and EXD, which paid quarterly then.
  - EOS on 2019-12-27.
  - INB on 2016-10-18, 2016-11-16 and 2016-12-09: these follow INB's switch from quarterly to monthly.
- UNKNOWN whether the Eaton Vance March 2017 records are true extras or a date reschedule. The Eaton Vance pages are off limits.

## 5. Cross-checks

- The vendor-to-issuer match is MEASURED for the BST and BSTZ special on 2026-09-15.
- STATED: First Trust's own distribution page lists FFA's 2026 ex-dates as 3/20, 6/22 and 9/22. These match the vendor's 3 FFA fund-days in 2026.
- No other SEC or issuer corroboration of each event was done. Each event's date and amount rest on the vendor (UNKNOWN beyond the vendor).

## 6. Declaration-to-ex lead time: UNKNOWN

The trade needs the amount and date public at least two NYSE sessions before the ex-date. No permitted source gave declaration dates for the counted events:

- The Alpaca data feed has no declaration-date field.
- BlackRock's JSON history and First Trust's distribution page list ex, record and pay dates only. First Trust shows only the current year.
- XAI's MCN page has a declaration column, but only for monthly 2026 rows, which are not counted.
- The John Hancock, Guggenheim and Columbia pages refused the fetch. They were not retried by another route.
- The Section 19(a) notices that Voya files as N-CSR exhibits say only "declared in <month>", with no day.
- The N-CSR text for Nuveen (BXMX family), First Trust (FFA) and Columbia (STK) gave no dated declarations.
- The Nuveen, Eaton Vance and Business Wire pages, where most press releases live, are off limits and were not touched.

Measured lead time: none.

Two routes the lead could rule on, not used here:

- Allow one third-party distribution history that shows declared dates.
- Allow reading each fund's Section 19(a) and N-CSR exhibits per filing to bound the declaration month.

## Gaps and cautions

- The roster covers about one fund in five of the equity closed-end fund universe. The counted events come from 22 funds and are concentrated in Nuveen (164 of 454).
- 2025 to 2026 is thin: 24 and 17 fund-days, 12 and 10 ex-dates, because the Nuveen, Voya and MCN funds moved to monthly. A forward test would see few events a year unless the roster widens beyond PCEF.
- Any year-end extras of funds outside PCEF are not counted.
- The equity rule counts N-PORT lines, not values, from a single filing per fund. It is fixed, but a value-based rule could move the borderline funds.
- Nothing in this doc used prices, so it says nothing about the edge.

## Addendum: second count, year-end and special distributions in all US-listed equity closed-end funds

Clock read 2026-11-26 10:54 UTC (03:54 MT) before this section was written.
Same ledger row 204. This is a separate count with its own fixed line. It does not change the first count above.
No price, NAV, quote, bar or reinvestment-price field was requested, read or stored. Raw records stay off the repo in the count 104 folder named above, in a subfolder for this branch (folder 0700, files 0600). No whole SEC submission was saved.

### A1. Line and rules (fixed by the lead before the count)

- Pass: at least 100 fund-days on at least 50 distinct ex-dates.
- Close: under 60 fund-days.
- Between: the lead rules.
- Event: any cash distribution that is not part of the fund's regular monthly or quarterly schedule, or a regular payment at least 2 times the median of the fund's previous four regular payments. Window 2016-01-01 to 2026-10-31.
- The event rules were written to a rules file off the repo at 10:26 UTC on 2026-11-26, before the vendor pull (sha256 6311288c4107a1b487fb7f2ff1e3e2e6cf0b7192077639c20310a84bcccb13b8). They were not changed after the count. The five rule tags are:
  - a: the vendor flags the record as special.
  - b: the fund has more than one cash record on the same ex-date.
  - c: the ex-date is off the fund's own monthly or quarterly schedule for that year.
  - d: the amount is at least 2 times the median of the previous four regular payments.
  - e: the fund-year has no monthly or quarterly schedule at all (semiannual, annual or irregular payers), so every payment counts.

### A2. Universe, from SEC data alone

- Source: the SEC Form N-CEN data sets, 2018 Q3 to 2026 Q3 (33 quarterly files from the SEC markets data page).
- Filter: the registrant type is N-2, and the fund lists a common share with a US exchange code (NYSE, Nasdaq, NYSE American or NYSE Arca) and a 1 to 5 letter ticker. This gives 613 listed closed-end fund CIKs.
- Equity rule, the same as section 2: in the fund's earliest NPORT-P, equity lines (asset category EC) are at least half of the non-derivative lines. This gives 166 equity CIKs. 52 listed CIKs have no NPORT-P and stay unclassified, which leaves them out. They include Thai Fund, several Aberdeen single-country funds, Morgan Stanley Emerging Markets, Latin American Discovery and many municipal funds.
- Cleaning, disclosed and not a rule change:
  - 5-letter tickers ending in X (NAV symbols) were dropped, leaving 160 CIKs and 165 ticker spans.
  - One N-CEN data error that put BSTZ on another CIK in 2020 was dropped.
- Ticker spans come from the N-CEN years. The first span is extended back to 2015-01-01, but not before the fund's first EDGAR filing. The last span is extended to 2026-10-31, but not past 400 days after the last filing.
- MEASURED, funds with a live span per year: 2016 144, 2017 145, 2018 145, 2019 149, 2020 152, 2021 158, 2022 155, 2023 150, 2024 148, 2025 148, 2026 143.
- STATED, ICI's equity closed-end fund counts for comparison, 2016 to 2025: 200, 197, 177, 177, 173, 166, 160, 152, 141, 137 ([ICI 2018 Factbook](https://www.ici.org/system/files/attachments/2018_factbook.pdf), [ICI 2025 Factbook ch. 5](https://www.icifactbook.org/pdf/2025-factbook-ch5.pdf), [ICI Q2 2026](https://www.iciglobal.org/research/stats/closedend/cef_q2_26)).
- MEASURED gap: the early years run 50 or more funds short of ICI, because N-CEN starts in mid-2018. Funds that closed or merged before then are missing. From 2023 on, the universe is at or above ICI's count, likely because the line rule admits some mixed funds.

### A3. Events

- Vendor: Alpaca corporate actions, cash dividends only, 2015-01-01 to 2026-10-31, for the 165 tickers. Every call returned status 200 with no paging. The pull gave 10,911 records. 2015 records are used only as history for rules c and d.
- Cleaning: 6 exact duplicate records (same day, rate and flag, at CEN and TEAF) were dropped as vendor duplicates.
- MEASURED: 461 fund-days on 261 distinct ex-dates, across 89 funds. This PASSES the line (at least 100 on at least 50).
- MEASURED, reading without rule e: if every payment of a no-schedule fund-year is set aside, 281 fund-days on 173 ex-dates remain, across 85 funds. This also passes.
- MEASURED, rule tags (one event can carry several): e 262, d 155, b 113, c 70, a 23.
- MEASURED, by year, all events then events without rule e (fund-days / ex-dates):

| Year | All | Without rule e |
|---|---|---|
| 2016 | 46 / 27 | 16 / 11 |
| 2017 | 50 / 24 | 19 / 8 |
| 2018 | 46 / 27 | 17 / 12 |
| 2019 | 37 / 21 | 16 / 12 |
| 2020 | 39 / 19 | 33 / 17 |
| 2021 | 58 / 29 | 48 / 23 |
| 2022 | 46 / 26 | 32 / 21 |
| 2023 | 36 / 22 | 22 / 18 |
| 2024 | 46 / 28 | 34 / 22 |
| 2025 | 42 / 26 | 30 / 18 |
| 2026 (Jan to Oct) | 15 / 12 | 14 / 11 |

- MEASURED, the funds with the most events: ASA 21, CET 21, EEA 21, GF 20, GAM 16, ADX 14, PEO 14, IIF 13, CAF 12, TY 11. EMF, UTG, CEE, GRF, TDF and RGT have 10 each.
- The make-up differs from the first count. It is mostly year-end capital-gain and income payouts at traditional and single-country equity funds, not level covered-call payouts.

Known false positives, kept because the rules were fixed:

- Rule d fires when a fund switches from monthly to quarterly, because the first quarterly payment is about three monthly ones (for example TEAF and CEN).
- Rule c fires when a fund moves its schedule, for example UTG's late-December ex-dates and the Eaton Vance cluster on 2017-03-22.
- Rule e counts every payment of semiannual payers such as ASA, including small level payments ($0.01 to $0.03).
- Some funds pass the equity line because they hold other funds' shares, for example RFM (RiverNorth Flexible Municipal Income) and PCF (High Income Securities). They are not traditional equity funds.

### A4. Stock instead of cash

Fund-level labels come from the stock and reinvestment wording in each fund's latest N-CSR. A keyword rule did the first pass. Release text read by hand overrode it for 7 funds: CET, GAM, TY, STK, TWN, CEN and JOF. Apart from those overrides, the labels were not hand-checked.

- MEASURED, by fund (89):
  - 7 pay stock by default, with cash only if elected: ADX, PEO, CET, GAM, TY, STK and Eagle Capital Growth.
    - STATED: the CET 2024-11-05 release says the distribution is payable in shares unless the holder elects cash.
    - STATED: the GAM 2017 and 2018 notices say the same.
    - STATED: for TY (2020 and 2021 releases) and STK (2017 release), this applies to the capital-gain part, which is paid in stock unless cash is elected.
  - 46 reinvest by default under an opt-out plan, so registered holders get shares unless they elect cash. Street-name holders depend on their broker.
  - 9 pay cash by default, with reinvestment only on election. These are the Eaton Vance funds, TWN and CEN.
  - 27 are unknown.
- MEASURED, by event (461): 94 in stock-by-default funds, 197 in opt-out reinvestment funds, 22 in cash-by-default funds and 148 unknown.
- MEASURED, in the 60-event sample: 10 stock by default, 29 opt-out reinvestment, 5 cash by default and 16 unknown.
- STATED, one event-level exception: IFN's $0.80 elective payout (declared 2021-12-09) was paid in shares unless the holder asked for cash. It is not the sampled IFN event.
- The 94 stock-by-default events change the accounting. A holder who takes the default gets new shares at an issue price set after the ex-date, not cash on the pay date.

### A5. Declaration lead, sample of 60

- Draw: the sample was drawn before any date was read. The seed was 20261126. The 255 strata are fund family × year. Family comes from the N-CEN family name, and a fund with no family is its own stratum. The strata were shuffled and then drawn round-robin. Off-repo sample file sha256: f33b71f0c28916bb27740757398787ca2c4fb3857628f7f7fc5c30e9cac16391.
- Allowed sources: issuer and fund-family pages, GlobeNewswire (and its einpresswire copies), ACCESSWIRE issuer copies, SEC filings (8-K and 497AD exhibits, N-CSR text) and issuer press lists.
- Off limits: Business Wire and PR Newswire, including any republication of them. Nuveen, Eaton Vance, Nasdaq and Blackstone pages were not touched. Aggregator summaries were not used.
- One SEC page refused the automated fetch, and two N-CSR fetches failed. None of them was retried another way.
- Session rule: NYSE sessions from the rig calendar. A release marked after the close counts from the next session. The lead is the number of sessions from the announcement session to the ex-date session.
- Off-repo results file sha256: a1d2cb00ec0d2649c86b1f008ec594b17cf359f210f31c9bc0104d4b7af33da9.

Results:

- MEASURED: 36 of 60 were public at least 3 sessions before the ex-date.
  - The shortest lead was 4 sessions, if every untimed release is moved to the next session.
  - The median lead was 7 sessions.
- MEASURED: 1 of 60 was not public 3 sessions before. RENN Fund (RCG), ex 2022-12-22, was announced 2022-12-20: 2 sessions, or 1 if after the close.
- MEASURED: 23 of 60 could not be dated from allowed sources.
- The 36 dated events by fund:
  - Fund releases or notices: ASA ×3, GAM ×3, UTG ×4, KF, CET, SWZ ×2, SPE, ADX ×2, RFM, TWN ×2, BST and RCG.
  - GlobeNewswire: JOF ×5, KYN, TDF ×2 and CUBA ×2.
  - SEC exhibits: TY ×2, STK, NTG and NXG.
  - NXG note: an SEC 424B2 dated 2025-07-21 says the August distribution was already declared, with record date 4 August. The vendor ex-date is 2025-08-15. Either way, it was public more than 3 sessions before.

The 23 undatable events, by reason:

- 7 were released only through Business Wire or PR Newswire, which are off limits: SRV ×2, CAF ×2, MXF, EEA and CEE. CEE's N-CSR page also refused the automated fetch.
- 2 are BlackRock funds (BDJ and BME). No BlackRock release was found, and the N-CSR fetch failed.
- 2 are Eaton Vance funds (EVT and ETB). Eaton Vance is off limits, and the SEC Section 19 notices give only the month.
- 4 have only an aggregator summary or no allowed copy: CEN, MGU, DXR and CHN 2019.
- 7 fall outside the issuer press lists' date range: ASA 2016 and 2017, CET 2021, KF 2016 and 2020, RFM 2020 and CHN 2017.
- 1 is IFN. Its N-CSR dates a different payout.

Lead time by year:

- Undatable events cluster in 2016 to 2020: 16 of 23.
- The dated events cover every year from 2016 to 2026.

Taken at face value, 36 of the 37 datable events cleared 3 sessions. The undatable 23 are UNKNOWN. They are not counted as either clearing or failing.

### A6. Gaps and cautions for the second count

- The universe misses funds that ended before mid-2018 and the 52 listed funds with no NPORT-P.
- The equity line rule admits a few fund-of-funds and mixed funds.
- Rule e is broad. It counts level semiannual payments, so the reading without rule e (281 / 173) is the safer number.
- The stock labels for 82 of 89 funds rest on a keyword rule over one N-CSR per fund. 27 funds stay unknown.
- Each event's date and amount rest on the vendor. They were checked against issuer or SEC text only for the 37 dated sample events. Where that text gave an amount or ex-date, it matched the vendor, apart from the NXG date question. For 9 of the 37, the date comes from a dated headline in an issuer news list with no amount (GAM 2017 and 2021, UTG 2020 and 2021, ASA 2021 and 2024, SWZ 2016, RFM 2021 and TDF 2018 through a GlobeNewswire copy), so those 9 are matched on fund and month only.
- Nothing here used prices, so it says nothing about the edge.
