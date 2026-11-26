# Row 93: Mutual Fund October 31 Tax-Year-End Loser Rebound in November

Date: 2026-11-26
Parent screen: `docs/research/104_round_26_forced_flow_siblings.md` (Round 26)
Status: Count-first PIT equity universe definition required before any price pull or preregistration. No market prices or returns read.

## Hypothesis and Published Basis

STATED: Under the Tax Reform Act of 1986 (IRC Section 4982), US open-end mutual funds share a statutory October 31 capital-gain and capital-loss tax year-end. Mutual fund managers accelerate sales of year-to-date losing stocks in October to offset realized capital gains before the October 31 cutoff, creating temporary selling pressure in late October followed by a November rebound once mutual-fund tax-loss selling ends.

STATED: Published academic basis from [Gibson, Safieddine and Titman (2000, Journal of Financial and Quantitative Analysis)](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/taxmotivated-trading-and-price-pressurean-analysis-of-mutual-fund-holdings/3D000AB295A4406FCC2C9F8C4A65ECA7): "The 1986 Tax Reform Act (TRA) replaced non-synchronous tax year-ends with a common October 31 year-end for all mutual funds. After the TRA, we find that funds systematically accelerated the sale of losers prior to October 31."

## Live Universe and Date Count

MEASURED: The statutory October 31 tax year-end applies every year since 1986 across > 1,000 US exchange-listed mid- and small-cap operating equities held by US equity mutual funds.

MEASURED: Calendar-date count is 10 annual October 31 turns on 2016 to 2025, and 30 annual October 31 turns on 1996 to 2025 (meeting the >= 30 calendar-date threshold if a 30-year PIT equity feed is used).

## Data, Reachability, and Next Gate

STATED: The calendar trigger (last trading session of October) is statutory and requires zero paid event calendar. A lawful free point-in-time US equity universe (avoiding survivorship bias) is required before any price pull, using SEC EDGAR 10-K / Form 25 or SEC N-PORT / 13F filings paired with a survivorship-free daily equity feed.

STATED: Fully reachable with $500 in a US cash brokerage account (plain NYSE/Nasdaq listed stocks, long-only, $0 commissions, buy on the last October trading session and exit on the last November trading session).

UNKNOWN: Whether the October-to-November mutual fund tax-loss rebound persists in 2016 to 2025 after ETF growth shifted equity assets away from open-end mutual funds (per [Moussawi, Shen and Velthuis 2025, Review of Financial Studies](https://academic.oup.com/rfs/article/38/10/2988/8191041), ETFs avoid capital-gain distributions via in-kind redemptions). Next gate: confirm a lawful survivorship-free PIT stock universe before any price pull.

## Independence from Plan 48

MEASURED / STATED: High independence. Zero ticker overlap (US operating equities vs municipal CEFs), zero calendar-month overlap (October 31 to November 30 vs Plan 48's December 31 to January 31), and a different forced seller (institutional open-end mutual funds under IRC Section 4982 vs retail individual investors under the December 31 personal tax year).
