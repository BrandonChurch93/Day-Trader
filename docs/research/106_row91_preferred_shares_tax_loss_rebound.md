# Row 91: Exchange-Listed Preferred Shares Year-End Tax-Loss Rebound

Date: 2026-11-26
Parent screen: `docs/research/104_round_26_forced_flow_siblings.md` (Round 26)
Status: Count-first PIT roster (including called/redeemed issues) required before any price pull or preregistration. No market prices or returns read.

## Hypothesis and Published Basis

STATED: Exchange-listed $25-par preferred shares (issued mainly by banks, REITs, utilities, and insurers) are thinly traded, retail-dominated income securities with no arbitrage creation/redemption mechanism. When interest rates or credit spreads widen during the year, retail holders sell losing preferred issues in December for tax-loss harvesting, creating a potential January rebound.

STATED: Published academic basis specific to preferred shares: NONE. General turn-of-the-year tax-loss selling in retail-held securities is documented in [Brauer and Chang (1990, Review of Financial Studies)](https://academic.oup.com/rfs/article-abstract/3/2/255/1595700) ("These results are consistent with tax-loss selling.") and [Starks, Yong and Zheng (2006, Journal of Finance)](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2006.01011.x), but no peer-reviewed paper isolates exchange-listed preferred stocks.

## Live Universe and Date Count

MEASURED: Official Nasdaq Trader symbol directories (`otherlisted.txt` and `nasdaqlisted.txt`, excluding ETFs and test issues) list 775 live US exchange-listed preferred share issues (506 on NYSE, NYSE Arca, and NYSE American; 269 on Nasdaq).

MEASURED: On 2016 to 2025, there are 10 annual December-to-January rebalance dates across this ~775-issue universe (50 issue-turns at 5 names per year). Calendar-turn count is 10 (under 30), matching Plan 48's decade window.

## Data, Reachability, and Next Gate

STATED: Current listed preferreds are free from official Nasdaq Trader symbol directories, but preferred shares are frequently called at $25 par or delisted upon issuer distress. Using only live 2026 tickers would introduce severe survivorship and call bias. Point-in-time reconstruction from SEC EDGAR Form 25 (delistings) and 424B5 / 8-K (new issuances and calls) is mandatory before any price pull.

STATED: Reachable with $500 in a US cash brokerage account (plain NYSE/Nasdaq listed $25-par shares, long-only, $0 commissions). Main execution risk: wide bid-ask spreads on thinly traded preferred issues (must verify spread/volume floor before testing).

UNKNOWN: Whether a clean, free, lawful 2016 to 2025 PIT preferred-share ticker mapping (reconciling NYSE preferred symbology across vendors) is feasible without paid reference data. Next gate: verify PIT ticker mapping and Form 25 delisting coverage before any price pull.

## Independence from Plan 48

MEASURED / STATED: Partial independence. Ticker overlap with Plan 48 is 0% (corporate/REIT/bank preferred shares vs municipal CEFs), but the trade uses the exact same December-to-January calendar window, same retail tax-loss selling driver, and shares long-duration interest-rate sensitivity with municipal bonds. Any replay must report turn-level correlation with Plan 48.
