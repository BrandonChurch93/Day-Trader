# Row 94: Quarter-End Basel III Dealer Balance-Sheet Rebound in Listed Corporate Bond ETFs

Date: 2026-11-26
Parent screen: `docs/research/104_round_26_forced_flow_siblings.md` (Round 26)
Status: Ready for preregistration design (deterministic calendar, >= 30 post-rule dates, plain liquid ETFs). No market prices or returns read.

## Hypothesis and Published Basis

STATED: Since the Basel III Supplementary Leverage Ratio (SLR) took effect in January 2015, bank-affiliated bond dealers face non-risk-weighted capital charges on quarter-end regulatory reporting snapshots. Bank dealers shed corporate bond inventory during the ~10 trading days before quarter-end and rebuild balance-sheet positions in the first few trading days of the new quarter. Buying liquid US-listed corporate bond ETFs at quarter-end close (after dealer inventory shedding) and holding into the early new-quarter dealer rebuild is a plain, long-only sibling of Treasury month-end (Replay 25).

STATED: Published basis from [Rapp and Waibel (2025, AEA 2026)](https://www.aeaweb.org/conference/2026/program/paper/S2KkB95R): "In January 2015, the Basel III leverage ratio introduced a non-risk-weighted capital requirement, obliging banks to hold a minimum amount of capital against all on- and off-balance-sheet exposures irrespective of risk." The same paper reports: "Consistent with the optimization of regulatory metrics prior to reporting dates, bank dealers, but not nonbank dealers, contract their capital commitment near quarter ends." It specifies the exact timing: "The average bank starts to significantly reduce capital commitment about ten trading days before the reporting date and then rebuilds balance sheet positions a few days into the new quarter." It quantifies the flow: "Over the ten-day window, the average bank dealer sells, on net, bonds worth approximately $50 million from its balance sheet, representing a more than one standard deviation move in capital commitment outside of quarter ends."

STATED: Supporting Federal Reserve evidence from [Chabot, Cochran, Infante and Iorio (2024, Federal Reserve FEDS Notes)](https://www.federalreserve.gov/econres/notes/feds-notes/dealer-balance-sheet-constraints-evidence-from-dealer-level-data-across-repo-market-segments-20240923.html): "The series shows sharp increases on month- and quarter-end dates which is consistent with dealers' incentive to scale back their activities because of increased balance sheet costs on regulatory reporting dates, an activity known as window dressing."

## Live Universe and Date Count

MEASURED: From Q1 2015 through Q4 2025 (the entire post-Basel-III-SLR regime), there are 44 quarter-end reporting dates (4 per year x 11 years), strictly above the 30-date floor. Excluding Q4 year-ends leaves 33 non-Q4 quarter-ends (March 31, June 30, September 30), still strictly above 30.

STATED: Plain liquid US-listed corporate bond ETFs with continuous daily trading history since before 2015 include `LQD` (investment-grade corporate), `HYG` and `JNK` (high-yield corporate), and `VCIT` / `IGIB` (intermediate corporate).

## Data, Reachability, and Next Gate

STATED: Quarter-end trading dates are deterministic calendar dates requiring zero paid event feeds. Daily OHLCV and distribution-adjusted total returns for `LQD`, `HYG`, `JNK`, and `VCIT` are available on our existing free lawful US ETF daily bar stack.

STATED: Fully reachable with $500 in a standard US cash brokerage account (plain NYSE Arca / Nasdaq ETFs, tight 1 to 2 bps spreads, $0 commissions, long-only, fractional shares supported).

UNKNOWN: Whether the quarter-end corporate bond ETF rebound (entry at quarter-end close, exit at T+3 or T+5 of the new quarter) clears costs and beats matched non-quarter-end days and matched `TLT` Treasury duration moves. Next gate: draft preregistration testing both all 44 quarter-ends and the 33 non-Q4 quarter-ends, with a paired control against `TLT` to separate credit-dealer SLR effects from Treasury month-end.

## Independence from Plan 48 and Replay 25

MEASURED / STATED: High independence from Plan 48: 0% ticker overlap (corporate bond ETFs vs municipal CEFs), 75% of events (33 of 44 quarter-ends: March, June, September) occur completely outside Plan 48's December-to-January window, and the forced flow is Basel III bank-dealer regulatory window dressing rather than retail tax-loss selling.

MEASURED / STATED: Distinct sibling of Replay 25 (Treasury month-end): trades corporate credit rather than US Treasuries, runs quarterly rather than monthly (only 4 of 12 month-ends overlap), and targets bank-dealer SLR inventory rebuilding rather than Treasury index duration extension. Reporting results both raw and net of `TLT` on the same dates will prove whether it is a genuinely separate bet.
