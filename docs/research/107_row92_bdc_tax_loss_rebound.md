# Row 92: Exchange-Listed BDC Year-End Tax-Loss Rebound

Date: 2026-11-26
Parent screen: `docs/research/104_round_26_forced_flow_siblings.md` (Round 26)
Status: Count-first PIT listed-BDC roster required before any price pull or preregistration. No market prices or returns read.

## Hypothesis and Published Basis

STATED: Exchange-listed Business Development Companies (BDCs) are closed-end Regulated Investment Companies under Subchapter M of the Internal Revenue Code, held heavily by retail income investors in taxable accounts. Unlike municipal CEFs, BDC loan portfolios are predominantly floating-rate private credit, giving them an opposite interest-rate duration profile while sharing the closed-end wrapper structure that allows year-end retail tax-loss selling to push share prices below net asset value.

STATED: Published academic basis specific to BDCs: NONE. The structural tax-loss mechanism is inferred by analogy from closed-end fund studies such as [Brauer and Chang (1990, Review of Financial Studies)](https://academic.oup.com/rfs/article-abstract/3/2/255/1595700): "Closed-end fund shares display the typical size-related January seasonal while their net asset values do not."

## Live Universe and Date Count

MEASURED: Querying SEC EDGAR EFTS for 2025 to 2026 Form 10-K filings containing `"elected to be regulated as a business development company"` returns 170 unique BDC CIKs (including non-traded and private BDCs). Intersecting those 170 CIKs with official SEC [SEC company_tickers_exchange.json](https://www.sec.gov/files/company_tickers_exchange.json) (NYSE, Nasdaq, NYSE American, NYSE Arca, Cboe BZX, common tickers) yields 47 live exchange-listed common BDCs.

MEASURED: On 2016 to 2025, there are 10 annual December-to-January rebalance dates across ~40 to 50 listed BDCs (50 fund-turns at 5 names per year). Calendar-turn count is 10 (under 30), matching Plan 48's decade structure.

## Data, Reachability, and Next Gate

STATED: Free lawful point-in-time roster data can be built cleanly from SEC EDGAR Form N-54A (BDC election), annual Form 10-K filings, and Form 25 (exchange delistings and mergers) for 2016 to 2026.

STATED: Fully reachable with $500 in a standard US cash brokerage account (plain NYSE/Nasdaq listed common shares, long-only, $0 commissions).

UNKNOWN: Exact 2016 to 2025 PIT listed BDC count (including merged/delisted BDCs) and whether loser BDCs rebound in January net of an equal-weight BDC roster and credit beta. Next gate: assemble the price-blind 2016 to 2025 PIT listed BDC roster from SEC EDGAR before any price pull.

## Independence from Plan 48

MEASURED / STATED: Partial independence. Ticker overlap with Plan 48 is 0%, and underlying asset exposure differs sharply (floating-rate senior private credit vs fixed-rate tax-exempt municipal bonds). However, it trades the exact same December-to-January calendar window and retail tax-loss selling regime, so any test must report correlation to Plan 48's annual turns.
