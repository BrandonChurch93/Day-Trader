# Row 90: Taxable Closed-End Fund Year-End Tax-Loss Rebound

Date: 2026-11-26
Parent screen: `docs/research/104_round_26_forced_flow_siblings.md` (Round 26)
Status: Count-first PIT roster required before any price pull or preregistration. No market prices or returns read.

## Hypothesis and Published Basis

STATED: Retail investors holding taxable closed-end funds (corporate credit, high-yield, multi-sector bond, convertible, equity-income, and utility CEFs) sell prior-year losers in December to harvest tax losses, depressing share prices below net asset value before year-end and creating a January rebound once tax-loss selling ceases.

STATED: Published academic basis from [Brauer and Chang (1990, Review of Financial Studies)](https://academic.oup.com/rfs/article-abstract/3/2/255/1595700): "Closed-end fund shares display the typical size-related January seasonal while their net asset values do not." The same abstract states: "The share returns at the turn of the year are negatively related to their mean preceding year returns and positively related to the standard deviations of their preceding year returns." It concludes: "These results are consistent with tax-loss selling."

## Live Universe and Date Count

MEASURED: Intersecting official SEC annual Closed-End Fund rosters (2015 to 2026) with official SEC [SEC company_tickers_exchange.json](https://www.sec.gov/files/company_tickers_exchange.json) (NYSE, Nasdaq, NYSE American, NYSE Arca, Cboe BZX) yields 359 live exchange-listed common CEFs, consisting of 76 municipal CEFs (Plan 48's family) and 283 live exchange-listed common taxable CEFs.

MEASURED: On the 2016 to 2025 decade matching Plan 48, there are 10 annual December-to-January rebalance dates across the 283-fund cross-section (50 fund-turns at 5 funds per year). Note that the calendar-turn count is 10 (under 30), identical to Plan 48's structure.

## Data, Reachability, and Next Gate

STATED: Free lawful point-in-time roster data comes from the official SEC annual Closed-End Fund CSVs (2015 to 2026, already cached locally from Row 88) plus SEC EDGAR Form 25 / N-8F delisting records, strictly excluding all municipal and tax-exempt CEFs.

STATED: Fully reachable with $500 in a standard US cash brokerage account (plain NYSE/NYSE American listed shares, long-only, $0 commissions, no margin or shorting).

UNKNOWN: Exact point-in-time count of delisted/merged taxable CEFs between 2016 and 2025 and whether post-cost returns clear random baskets and an equal-weight taxable CEF roster. Next gate: build the price-blind PIT taxable CEF roster (2016 to 2025) excluding all Row 86 muni CEFs before any price pull.

## Independence from Plan 48

MEASURED / STATED: Partial independence. Ticker overlap with Plan 48 is 0% (283 taxable CEFs vs 76 muni CEFs), but the calendar window (last December trading session to end of January) and forced-flow mechanism (retail tax-loss selling) are identical to Plan 48. Any future test must report annual-turn correlation against Plan 48 so a second pass is not double-counted as an unrelated edge.
