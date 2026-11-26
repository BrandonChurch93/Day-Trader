# Count 55: US closed-end fund rights offerings, 2016 to 2026

Queue row 55, ledger 212. Price-blind count. This file is written by `research_rig/count_55.py` from `research_rig/count_55_events.csv`. Do not edit it by hand.

## Lines fixed before the count

- STATED (ledger 212): at least `COUNT_LINE` = 100 completed offerings with an exact expiration date, on a fund with a US listing, expiring 2016 to 2026.
- STATED (ledger 212): a post-expiration rebound size from a published source that gives at least `POWER_LINE` = 33% chance of t at `T_MARK` = 2 at that count under the doc 117 screen, with `SCREEN_SESSIONS` = 10-session dispersion from a published figure, never our bars.
- STATED: below either line the row closes.

## How the table was built

- STATED: SEC sources only. Quarterly form indexes from https://www.sec.gov/Archives/edgar/full-index/ for 2015 Q3 to 2026 Q4, then the full submission text of each candidate filing.
- STATED: candidates were every 424B filing, plus 497, 497AD and 8-K filings, by a filer that also files N-CSR, kept when the text names a rights offering. N-2, N-2/A and POS 8C filings for each event's fund were read in a second pass to find the first filing that names the event's record or expiration date.
- STATED: no SEC full-text search, no press wire site, no sponsor site, no price data of any kind. Descriptive User-Agent, at most 4 requests a second. Raw filings stay in `/home/user/workspace/rig/data/count_55/`, off the repo.
- STATED: each event row was checked by hand against the filing text. Dates were read from the filings, with a link for each. The subscription price is kept as a formula only, never as a dollar figure.
- STATED: `status` is completed when a result filing, a later prospectus or a shareholder report states the offering closed or shares were issued; withdrawn when a filing says it was terminated or withdrawn.
- STATED: `us_listed` is yes when an offering filing names the NYSE, NYSE American or Nasdaq listing of the fund's shares, with the ticker at the time.
- STATED: `count_55_events.csv` sha256 `352d66c2ccc0864b1f6010b72b82ca02f3e2352ee0de76996d5912111e4a9f43`. It holds no prices.

## Counts

- MEASURED: 127 offerings in the table expire 2016 to 2026. completed 122, pending 1, unconfirmed 2, withdrawn 2.
- MEASURED: 120 pass the count rule (completed, exact expiration, US listing), on 66 funds.
- MEASURED: 2 completed offerings were for preferred shares and are not counted.
- MEASURED: 8 of the 120 had the expiration extended. The count uses the final expiration date.
- MEASURED: of the 120, 120 have a dated announcement filing with an SEC acceptance time, 120 a record date, 84 a stated share count.

By final expiration year, all offerings and those that pass the count rule:

| Year | In table | Pass the count rule |
|---|---:|---:|
| 2016 | 3 | 2 |
| 2017 | 10 | 10 |
| 2018 | 14 | 13 |
| 2019 | 10 | 9 |
| 2020 | 5 | 4 |
| 2021 | 19 | 19 |
| 2022 | 12 | 11 |
| 2023 | 6 | 6 |
| 2024 | 11 | 11 |
| 2025 | 20 | 20 |
| 2026 | 17 | 15 |
| Total | 127 | 120 |

Transferable or not, among those that pass:

- MEASURED: non-transferable: 32.
- MEASURED: transferable: 88.

Sponsor concentration, among those that pass:

- MEASURED: RiverNorth: 17 (14.2%).
- MEASURED: Gabelli: 14 (11.7%).
- MEASURED: Cornerstone: 12 (10.0%).
- MEASURED: BlackRock: 9 (7.5%).
- MEASURED: NXG (Cushing): 8 (6.7%).
- MEASURED: Franklin Templeton: 7 (5.8%).
- MEASURED: Clough: 5 (4.2%).
- MEASURED: ALPS (Liberty All-Star): 4 (3.3%).
- MEASURED: abrdn: 4 (3.3%).
- MEASURED: Bulldog Investors: 4 (3.3%).
- MEASURED: the top five sponsors hold 60 of 120 (50.0%). Herfindahl index over sponsors 0.068.
- MEASURED: 110 clusters when offerings by one sponsor that expire within `CLUSTER_DAYS` = 14 calendar days of each other count once.

Offerings in the table not counted as completed:

- MEASURED: SPECIAL OPPORTUNITIES FUND, INC., expiration 2016-08-26, unconfirmed ([filing](https://www.sec.gov/Archives/edgar/data/897802/000089418916010409/0000894189-16-010409-index.htm)).
- MEASURED: SOURCE CAPITAL INC /DE/, expiration 2019-10-17, withdrawn ([filing](https://www.sec.gov/Archives/edgar/data/91847/000110465919049867/0001104659-19-049867-index.htm)).
- MEASURED: BANCROFT FUND LTD, expiration 2020-04-21, withdrawn ([filing](https://www.sec.gov/Archives/edgar/data/9521/000119312520074865/0001193125-20-074865-index.htm)).
- MEASURED: Nuveen Municipal Credit Opportunities Fund, expiration 2026-10-07, unconfirmed ([filing](https://www.sec.gov/Archives/edgar/data/1774342/000199937126018939/0001999371-26-018939-index.htm)).
- MEASURED: NUVEEN MUNICIPAL HIGH INCOME OPPORTUNITY FUND, expiration 2026-12-02, pending ([filing](https://www.sec.gov/Archives/edgar/data/1266585/000199937126023336/0001999371-26-023336-index.htm)).

## Published rebound figures

- STATED: Khorana, Wahal and Zenner (2002, JFQA), 120 US CEF rights offerings 1988 to 1998: the premium turns into a discount over the offering. Before 2000 and no post-expiration rebound figure. [Cambridge](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/agency-conflicts-in-closedend-funds-the-case-of-rights-offerings/A9BD552704DEECFB4E2BC7E2627D42EC)
- STATED: Brigham (LSU dissertation, 2000) reports a very weak price rebound after offers, with no figure usable here, and the sample is before 2000. [LSU](https://repository.lsu.edu/gradschool_disstheses/7143/)
- STATED: AIC article citing John Cole Scott (CEF Advisors), about 12.5 years of data to 2024, 127 rights offerings: average premium 6.7% 90 days before expiration, -4.7% on expiration day, 0.17% 90 days after; "-11% relative alpha then a bounce of +5%". No window for the bounce, no sample dates, no t and no dispersion. Not peer reviewed. [AIC](https://aicalliance.org/wp-content/uploads/2024/10/How-Corporate-Actions-in-Closed-End-Funds-Can-Potentially-Boost-Portfolio-Performance.pdf)
- STATED: Open-Alpha-Lab study 929, not peer reviewed, 39 US offerings by 20 issuers, 2013 to 2023, event dates only to the month: trading days +29 to +49 after the anchor (about 21 sessions after a modelled expiry) mean 0.21%, median 0.44%, t 0.25, 95% interval -1.51% to 1.87%. [results](https://raw.githubusercontent.com/Guillain-RDCDE/Open-Alpha-Lab/main/studies/929-rights-offering-discount/docs/results.md)
- MEASURED from those figures: the implied per-event sd of the Open-Alpha-Lab window is 5.25%, close to the published Malkiel and Xu figure scaled to 21 sessions, 5.66%.
- UNKNOWN: no published post-2000 measurement gives a rebound size for a fixed 10-session window after the exact expiration date.

## Doc 117 screen

- STATED: dispersion from Malkiel and Xu (2005), 59 US equity CEFs, 1993 to 2002: average annualized volatility from weekly returns `MX_ANNUAL_SD` = 19.6%. [paper](http://www-stat.wharton.upenn.edu/~steele/Courses/956/Resource/CEF/MalkielXu.pdf)
- MEASURED: scaled by the square root of `SCREEN_SESSIONS` / `SESSIONS_PER_YEAR` = 10/252, the 10-session sd is 3.90%. This is the fund's own return sd. The paired noise against a same-clock alternative is UNKNOWN; it is used as the paired noise here.
- STATED: power is Φ(√N × edge ÷ sd − `T_MARK`). The 33% line needs √N × edge ÷ sd of at least 1.56.
- STATED: `COST_RT_BP` = 30 bp round trip is an assumption, the top of the 10 to 30 bp spread range in doc 74.
- MEASURED: at N = 120, the 10-session edge needed is 0.56% gross, 0.86% before the cost is taken off.
- MEASURED: at the clustered count 110, it is 0.58% gross, 0.88% before the cost is taken off.

| Published figure, reading | Net edge | sd for its window | Power at N = 120 | Power at clustered 110 |
|---|---:|---:|---:|---:|
| Open-Alpha-Lab mean, its own 21-session window, net of cost | -0.09% | 5.66% | 1.5% | 1.5% |
| Open-Alpha-Lab median, its own 21-session window, net of cost | 0.14% | 5.66% | 4.2% | 4.1% |
| AIC +5% bounce read as 10 sessions (assumption), net of cost | 4.70% | 3.90% | 100.0% | 100.0% |
| AIC +5% bounce read as 90 calendar days, about 63 sessions (assumption), net of cost | 4.70% | 9.80% | 99.9% | 99.9% |

## Verdict

- MEASURED: count line: 120 against 100. Met.
- MEASURED: the one published figure with a stated window (Open-Alpha-Lab, mean) gives 1.5% at N = 120, against 33%. Not met.
- STATED: the AIC +5% passes only if its unstated window is assumed. The line asks for a stated size, so this reading is shown but not used for the verdict.
- STATED: the row closes on the fixed lines.

## Limits

- UNKNOWN: recall. Offerings named only in filings outside the forms read here (for example a press release posted only on a sponsor site) are missed. The count is a lower bound.
- STATED: completion was read by hand from later shareholder reports and prospectuses for the events where no result filing was found; the CSV `status_basis` column says which.
- STATED: 3 rows in the CSV expire before 2016; they were found by the 2015 index quarters and are kept but not counted.
- STATED: 20 candidate filings failed to download in the first pass. They were fetched again later; none was a rights offering prospectus or notice (two named rights only as a possible future offering type).
- STATED: the shareholder reports read for completion state subscription prices. Those prices were not copied into the table or the repo.
- UNKNOWN: the paired noise of a fund against its same-clock alternative; the fund's own sd stands in.
- UNKNOWN: whether the 1993 to 2002 Malkiel and Xu volatility holds for 2016 to 2026.
