# Count 102: US-Listed Closed-End Fund Activist Schedule 13D Census (2016 to 2026)

Ledger 201, queue row 102. Written 2026-11-26 MT. Plan and pass line locked before any SEC count in `research_rig/COUNT_102_cef_13d_census.md`. Source idea: `docs/121_idea_round_32.md`; power screen: `docs/research/117_power_screen_before_data.md`.

## Verdict

MEASURED (zero price access): Between 2016-01-01 and 2026-11-25, SEC EDGAR records contain **437 qualifying common-stock activist Schedule 13D events** on US-listed closed-end funds across **337 primary independent event clusters** (same normalized filer group on the same Eastern-time filing date), spanning 163 unique listed CEF CIKs and 36 filer groups.

STATED (pass line fixed before counting): The idea advances to a pre-registration only if primary independent event clusters number at least 100, closes if fewer than 60, and defers to the lead agent between 60 and 100.

MEASURED (screen outcome): **PASSES COUNT-FIRST SCREEN (337 >= 100).** Every pre-specified sensitivity also clears 100 by more than 2.2x: 293 independent 5-calendar-day filer waves, 256 same-day clusters using initial Schedule 13D filings only (230 under 5-day waves), 327 same-day clusters excluding fund-sponsor and insider filers, and 147 same-day clusters excluding Saba Capital Management entirely.

UNKNOWN: Post-filing tradable return, discount-narrowing split before versus after acceptance, and net-of-cost Sharpe remain completely unmeasured because this census used zero market prices or returns.

## Universe Construction and SEC EDGAR Filter Funnel

STATED (zero price access, no full-text search): All counts come exclusively from SEC EDGAR quarterly `master.idx` form indexes ([SEC EDGAR full-index](https://www.sec.gov/Archives/edgar/full-index/)), SEC Division of Investment Management annual closed-end fund rosters ([SEC CEF rosters](https://www.sec.gov/files/investment/data/other/closed-end-fund-information/)), SEC submissions metadata ([SEC data API](https://data.sec.gov/submissions/)), and primary Schedule 13D / 13D amendment documents fetched below 5 request starts per second. The SEC full-text search endpoint was not used.

MEASURED (stable CIK universe): Reusing the stable CIK identity lists from Plan 48 (192 muni CEF CIKs) and Plan 53 (181 taxable CEF CIKs; 373 union) plus all CIKs in the 2016 to 2026 SEC annual CEF rosters yielded **1,581 unique CEF CIKs**. Today's ticker field was never used to rebuild historical membership.

MEASURED (filter funnel from raw SEC index hits to qualifying events):

- 3,513 unique Schedule 13D and Schedule 13D amendment accessions across 44 quarterly `master.idx` files (2016 Q1 through 2026 Q4 to 2026-11-25) touched 423 of the 1,581 CEF CIKs.
- 336 of those 423 CIKs were verified as exchange-listed US CEFs (NYSE, NYSE American, Nasdaq, or Cboe via Plan 48/53 verification, SEC submissions `exchanges`, or Form 8-A12B / 25-NSE), accounting for **2,864 accessions** (649 accessions on 87 unlisted interval, tender-offer, or private-credit funds were excluded).
- 622 of the 2,864 accessions were excluded after primary-document inspection as **preferred-share financing filings** (VMTP, VRDP, Auction Rate Preferred, MuniTerm Preferred, or Cumulative Preferred shares, led by Bank of America 331, Wells Fargo 134, GAMCO preferreds 36, Toronto Dominion 36, JPMorgan 22, Eagle Point 21, and Karpus preferreds 12).
- 47 of the 2,864 accessions were excluded because the listed CEF was the **reporting person (filer)** on an operating company rather than the subject company (45 by 180 Degree Capital Corp / Harris & Harris Group on operating companies such as Comscore and Potbelly, plus 1 each by NexPoint Strategic Opportunities Fund and High Income Securities Fund).
- 1 accession (`0001048703-17-000086`, Karpus SC 13D/A on MFS Investment Grade Municipal Trust, 2017-07-12) failed SEC fetch after retry and is omitted from the parsed count.
- **2,194 parsed common-stock filings** had a verified US-listed CEF as subject company (312 initial SC 13D or SCHEDULE 13D filings and 1,882 SC 13D/A or SCHEDULE 13D/A amendments).

MEASURED (event qualification on the 2,194 common-stock filings):

- **287 initial events**: first SC 13D or SCHEDULE 13D by a normalized filer group on a listed CEF subject CIK in the 2016 to 2026 window.
- **23 re-entry initial events**: subsequent SC 13D or SCHEDULE 13D by the same filer group on the same CEF more than 60 calendar days after a prior qualifying event (2 duplicate initials within 60 days excluded).
- **127 escalation amendment events**: SC 13D/A or SCHEDULE 13D/A filings whose Item 4 text disclosed a concrete active step (proxy contest or Rule 14a-8 / special-meeting solicitation, board or trustee slate nomination, or tender-offer / open-ending / liquidation demand) with active action language, non-duplicate Item 4 text hash, and more than 60 calendar days since the prior qualifying event for that `(filer_group, subject_cik)` pair.
- **94 standstill, settlement, or withdrawal amendments** were tagged separately and excluded from the primary escalation count (along with 1,544 routine stake-change amendments with no escalation flag, 69 escalations within 60 days of a prior event, 44 boilerplate-only mentions without concrete action verbs, and 4 exact Item 4 hash repetitions).
- **437 total qualifying events** collapse into **337 primary independent clusters** (same normalized filer group on the same Eastern-time date) and **293 five-calendar-day filer waves**.

## Events and Independent Clusters by Year

MEASURED (2016-01-01 to 2026-11-25, grouped by Eastern-time filing date):

| Year | Qualifying Events | Initial 13D | Escalation 13D/A | Primary Clusters (Same-Day) | 5-Day-Wave Clusters | External-Activist Clusters |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | 35 | 26 | 9 | 32 | 31 | 31 |
| 2017 | 38 | 32 | 6 | 23 | 23 | 23 |
| 2018 | 15 | 12 | 3 | 15 | 15 | 14 |
| 2019 | 32 | 30 | 2 | 28 | 27 | 28 |
| 2020 | 42 | 28 | 14 | 37 | 31 | 36 |
| 2021 | 14 | 10 | 4 | 14 | 13 | 14 |
| 2022 | 28 | 23 | 5 | 23 | 21 | 20 |
| 2023 | 87 | 70 | 17 | 65 | 51 | 62 |
| 2024 | 84 | 47 | 37 | 55 | 43 | 55 |
| 2025 | 38 | 17 | 21 | 27 | 24 | 26 |
| 2026 (to Nov 25) | 24 | 15 | 9 | 18 | 14 | 18 |
| Total | 437 | 310 | 127 | 337 | 293 | 327 |

MEASURED (temporal concentration): Activity is strongly cyclical rather than uniform. Years 2023 and 2024 together account for **39.1% of all events** (171 of 437) and **35.6% of all primary clusters** (120 of 337), driven by multi-fund campaigns across BlackRock, Nuveen, Eaton Vance, Franklin, and Invesco CEFs. Quiet regimes such as 2018 (15 clusters) and 2021 (14 clusters) average barely above one independent cluster per month.

## Acceptance Timestamp Split (Eastern Time)

MEASURED (converted from SEC `acceptanceDateTime` UTC to Eastern Time, handling EST and EDT):

| Session Window (ET) | Qualifying Events | Event Share | Primary Clusters (Earliest Filing) | Cluster Share |
| --- | ---: | ---: | ---: | ---: |
| Pre-market (before 09:30:00 ET) | 64 | 14.6% | 50 | 14.8% |
| Regular market hours (09:30:00 to 15:59:59 ET) | 193 | 44.2% | 148 | 43.9% |
| After close (16:00:00 ET onward) | 180 | 41.2% | 139 | 41.2% |
| Total | 437 | 100.0% | 337 | 100.0% |

MEASURED (execution-clock implication): Nearly three-fifths of clusters (198 of 337, or **58.8%**) arrive before the 16:00:00 ET closing bell (14.8% pre-market plus 43.9% during regular trading hours), while **41.2%** (139 of 337) arrive after the close. A daily-bar pre-registration cannot treat all filing dates identically: pre-market and intraday filings have already experienced partial or full announcement-day price reaction by the day-`t` close, whereas after-close filings are first tradable at the `t+1` open or `t+1` close.

## Top Filers and Same-Day Clustering

MEASURED (filer concentration across 36 normalized filer groups):

| Filer Group | Qualifying Events | Event Share | Primary Clusters | Cluster Share | 5-Day-Wave Clusters |
| --- | ---: | ---: | ---: | ---: | ---: |
| Saba Capital Management | 260 | 59.5% | 190 | 56.4% | 147 |
| Karpus Management | 40 | 9.2% | 33 | 9.8% | 33 |
| Bulldog Investors | 34 | 7.8% | 34 | 10.1% | 34 |
| City of London Investment Group | 23 | 5.3% | 11 | 3.3% | 11 |
| Sit Investment Associates | 19 | 4.3% | 11 | 3.3% | 10 |
| Western Investment | 9 | 2.1% | 9 | 2.7% | 9 |
| Ohio PERS (OPERS) | 8 | 1.8% | 5 | 1.5% | 5 |
| Ancora Advisors | 4 | 0.9% | 4 | 1.2% | 4 |
| Relative Value Partners | 3 | 0.7% | 3 | 0.9% | 3 |
| All other 27 filers combined | 37 | 8.5% | 37 | 11.0% | 37 |
| Total | 437 | 100.0% | 337 | 100.0% | 293 |

MEASURED (single-actor and multi-fund wave risk):

- **Saba Capital Management alone accounts for 59.5% of qualifying events and 56.4% of primary clusters** (50.2% of 5-day waves). The top five filers account for 86.0% of events and 82.8% of primary clusters. Any pre-registration must treat Saba-versus-non-Saba stability as a mandatory diagnostic so a strategy does not depend on a single fund manager's continued strategy or legal posture.
- Multi-fund same-day waves are common: 279 primary clusters involve 1 fund, 38 involve 2 funds, 13 involve 3 funds, 3 involve 4 funds, 2 involve 5 funds, 1 involves 9 funds (Saba Capital on 2024-10-11), and 1 involves 12 funds (City of London Investment Group across Aberdeen CEFs on 2017-03-28). Collapsing same-day waves removes 100 correlated duplicate fund rows (437 events -> 337 clusters), and collapsing 5-day waves removes another 44 (337 -> 293).
- Fund-sponsor and insider Schedule 13Ds are small in common stock once preferred shares are removed: only 10 events across 10 primary clusters (Herzfeld, Highland/Dondero, Franklin Resources, Blackstone, Carlyle, Charles Royce, Kevin Rendino, DST Systems). Excluding them leaves 427 events and 327 primary clusters.

## Sixty-Trading-Day Listing Survival (SEC Filings Only)

MEASURED (zero prices; checked against SEC Form 25-NSE, Form 25, Form N-8F, and Form N-8F ORDR filings over 60 XNYS sessions using `research_rig/calendar_25.json` extended through 2026):

- **9 late-2026 events** (filed after 2026-08-31) have fewer than 60 XNYS trading days elapsed by 2026-11-25 and are right-censored.
- Among the **428 non-censored events**, **417 (97.4%)** had zero SEC delisting or deregistration filings within 60 XNYS trading days of the event date.
- **11 events (2.6%)** had a Form 25-NSE filing within 60 XNYS trading days. Inspecting SEC submission histories shows **9 of those 11 (2.1%)** were genuine common-stock fund delistings, mergers, or liquidations (Eaton Vance Municipal Bond Fund II in 2019; Seven Hills Realty Trust in 2021; Neuberger Berman California and New York Municipal Funds in 2023; Macquarie/First Trust Global Infrastructure Fund in 2024; 180 Degree Capital Corp, Eaton Vance New York and California Municipal Bond Funds, and abrdn Japan Equity Fund in 2025), while **2 of the 11** were preferred-share or rights-class Form 25-NSE filings on funds whose common shares remained listed (Gabelli Go Anywhere Trust 2016-11-02; Eagle Point Credit Co 2018-05-24). Common-stock 60-trading-day listing survival is therefore **419 of 428 (97.9%)** (97.4% using raw unscreened Form 25-NSE hits).
- Any pre-registration holding 20 to 60 trading days must include explicit delisting/merger cash-out accounting rather than dropping non-surviving funds, because activist campaigns themselves trigger mergers, reorganizations, and liquidations.

## Source Paper Versus Tradable Rule Requirements

STATED (what the source paper actually measured): [Bradley, Brav, Goldstein, and Jiang (2008/2010, Journal of Financial Economics)](https://business.columbia.edu/sites/default/files-efs/pubfiles/4118/activist_arb.pdf) studied 142 US closed-end funds (1988 to 2002) and 127 open-ending attempts (1988 to 2003). Their headline finding is **annual/event-year discount narrowing** exceeding 10 percentage points from pre-attempt to post-attempt, including roughly 5.5 percentage points from the attempt year `t` to `t+1`.

UNKNOWN (what the source paper did NOT measure): **The tradable post-Schedule-13D-filing daily return is UNKNOWN in Bradley et al. (2008/2010).** Specifically, the paper does not establish:

- Pre-filing versus post-filing split: how much discount narrowing occurs during the activist's stealth accumulation before crossing 5% (and during the SEC filing lag: formerly 10 calendar days, shortened to 5 business days effective 2024-02-05) versus after the public 13D acceptance timestamp.
- Immediate announcement-day jump: whether a next-open or next-close retail entry captures residual post-filing drift or pays an already-compressed discount after intraday arbitrageurs react to the EDGAR feed.
- Tradable total return net of costs: CEFs trade with wider bid-ask spreads and lower daily volume than broad ETFs, pay frequent monthly or quarterly distributions (requiring cash-adjusted total return), and carry underlying NAV beta that dominates unhedged short-window returns unless paired against a fixed asset-class ETF benchmark.
- Regime transfer: whether the 2016 to 2026 Saba-dominated activist market (where fund boards routinely deploy poison pills, control-share statutes, and defensive standstills) delivers positive post-filing drift comparable to 1988 to 2003.

STATED (minimum requirements if pre-registered): A pre-registration built on this census should fix (1) equal-weighted cluster-level scoring (collapsing same-day and 5-day waves), (2) explicit entry-clock separation between after-close filings (`t+1` open or close) and pre-market/intraday filings (`t` close or `t+1` open), (3) a fixed peer-ETF benchmark (e.g., MUB for muni CEFs, SPY/AGG/HYG by pre-filing SEC fund category) to reduce noise per `docs/research/117_power_screen_before_data.md`, (4) realistic CEF round-trip spread/slippage modeling on $500 whole-share sizing, (5) full merger/delisting cash-out handling for the ~2% non-survivors, and (6) a Saba-versus-non-Saba stability check.

## Off-Repo Artifact Custody

MEASURED: Compact metadata, Item 4 excerpts (<= 600 characters per filing, zero whole submissions retained), and summary tables are stored under `/home/user/workspace/rig/data/count_102/` (`0700`, files `0600`, total footprint 5.0 MB): cef_universe_ciks.json, master_13d_cef_raw.json, cef_life_events.json, cef_submissions_meta.json, acc_acceptance_meta.json, parsed_13d_listed.jsonl, events_102.json, and census_summary.json.
