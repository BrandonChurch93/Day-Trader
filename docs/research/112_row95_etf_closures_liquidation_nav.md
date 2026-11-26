# Row 95: US ETF Closures and Liquidations (Buy After SEC 497 Notice, Hold to Cash at NAV)

Date: 2026-11-26
Parent screen: `docs/research/111_round_27_higher_payoff_forced_flows.md` (Round 27)
Status: Count-first SEC EDGAR Form 497 docket deduplication required before any price pull or preregistration. No market prices or returns read.

## Hypothesis and Published Basis

STATED: When an ETF sponsor announces an orderly fund closure and cash liquidation (typically 2 to 6 weeks before the final trading date), retail and advisor selling immediately after the closure notice can temporarily depress shares while creation/redemption activity winds down, whereas holding to cash liquidation pays out net asset value (NAV) in cash.

STATED: Published academic basis from [Boehmer and Finta (SSRN 4328422, 633 closed ETFs from January 2012 to December 2019)](https://acfr.aut.ac.nz/__data/assets/pdf_file/0004/809644/Exchange-Traded-Fund-Closures-FULL-ssrn-maf2.pdf): "In general, closing ETFs display positive raw returns until the closure announcement, when they decrease to -0.15% and then rise to 0.66% one to two months after the announcement." The paper adds: "Interestingly, investors typically earn positive average returns while keeping calm and waiting for the liquidation date without selling their shares after the closure announcement." It concludes: "Our results also show that when the ETF issuer does not charge extra closing fees, investors may be better off doing nothing after the closure announcement, namely, chilling out and waiting to receive the value of the shares in cash at NAV."

## Live Universe and Date Count

MEASURED: SEC EDGAR EFTS (2016-01-01 to 2026-11-26) returns 185 Form 497/497K/8-K filings matching `"last day of trading" "liquidate" "exchange-traded fund"` and 183 filings matching `"cease trading" "liquidation date" "ETF"`. Because multi-series ETF trusts frequently announce 2 to 10 fund liquidations in a single Form 497 supplement, the underlying 2016 to 2026 individual ETF closure count is well above 30 (Boehmer and Finta documented 633 US ETF closures across 2012 to 2019 alone).

## Data, Reachability, and Next Gate

STATED: Free lawful dated event records come from official SEC EDGAR Form 497 prospectus supplements (exact UTC acceptance timestamp, stated last regular trading session, and stated cash liquidation date) corroborated by NYSE Arca / Nasdaq / Cboe Form 25-NSE delisting notices.

STATED: Fully reachable with $500 in a standard US cash brokerage account (plain US-listed ETFs, long-only, $0 commissions, $0 mandatory liquidation payout fee at Schwab, Fidelity, and IBKR). Pure delistings without cash liquidation (where shares move to OTC) must be excluded strictly pre-price from the Form 497 text.

UNKNOWN: Exact post-cost abnormal return net of matched style benchmark during the 2016 to 2026 period, and whether the +0.66% raw return in Boehmer and Finta reflects market/style drift during the 1 to 2 month hold rather than discount-to-NAV closure (critical test requirement: benchmark against a matched-asset-class ETF over the exact hold window, and separate last-exchange-close returns from final cash-at-NAV payout). Next gate: build a price-blind, deduplicated SEC EDGAR Form 497 ETF cash-liquidation docket (2016 to 2026) with exact UTC timestamps, scheduled last trading date, liquidation date, and pre-entry asset class before any price pull.

## Independence from Plan 48, Replay 25, and Plan 50

MEASURED / STATED: High independence from Plan 48 and Replay 25 (occurs year-round across equity, thematic, and fixed-income ETFs on idiosyncratic issuer closure dates rather than Dec/Jan muni tax-loss selling or Treasury month-end). Distinct from Plan 50 (CEF liquidations) because ETFs have open-end creation/redemption halted upon closure notice and shorter 2 to 6 week holds to cash at NAV.
