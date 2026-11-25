# Audit of docs/playbook/02_crypto_what_works.md
Audited against: docs/research/02_crypto_trading_evidence.md
Audit date: 2026-11-24

## Spot-verification of 3 load-bearing claims (fetch_url)
- Binance.US spot taker fee (4 bps round trip on most pairs): VERIFIED. Official fee schedule lists VIP 1 (<$10k 30-day volume) Tier I ("all other pairs" outside BNB/USD) at 0.00% maker / 0.02% taker (4 bps taker round trip, fee only).
- Alpaca Crypto Spot entry fee (50 bps round trip): VERIFIED. Official docs list $0–$100k 30-day volume (Tier 1) at 0.15% maker / 0.25% taker (50 bps taker round trip, fee only).
- IRS Form 1099-DA row (`https://www.irs.gov/instructions/i1099da`): PARTIAL MISMATCH (see Finding 1 below).

## Findings

1. **FIX: Cited IRS URL does not verify 2025 gross-proceeds reporting and omits the post-2025 acquisition condition for covered basis.**
   The live `i1099da` page (updated April 30, 2026) is the 2026 edition and states only that brokers must report gross proceeds and covered-security basis for sales effected after December 31, 2025 (with covered securities defined as assets acquired after 2025 in a custodial account). It does not substantiate the "Gross proceeds from 2025" part of the row.
   Suggested replacement for Key numbers Row 10:
   `| Custodial broker 1099-DA | Gross proceeds and basis for covered assets acquired and sold after 2025 | Apr 30, 2026 | MEASURED | [IRS 2026 Form 1099-DA instructions](https://www.irs.gov/instructions/i1099da) |`

2. **BLOCKER: Dropped critical money-safety rules on exchange custody risk and stop-loss failure in thin books.**
   The research report (§5, "Risks that change the build") warns to keep idle funds off execution venues (FTX/exchange concentration risk) and not to rely on stop orders to cap losses through thin books or liquidation cascades (Oct 10, 2025 $19B liquidation / ADL event). Both rules are omitted from the playbook, leaving a build agent free to park excess capital on exchanges and assume exchange stops bound tail loss.
   Suggested addition to `## Rules for the build` (fits within the 10-bullet cap, currently 8 bullets):
   `- Keep idle capital off execution venues where practicable and never rely on exchange stop orders alone to cap tail losses through thin books [MEASURED] (research §5).`

3. **FIX: Dropped build-affecting operational rules on wash-trading/depth screening, maintenance windows, and time-varying derivatives margin.**
   The research report (§4, §5) documents >70% wash trading on unregulated venues (screen by verified depth, not printed volume), scheduled maintenance windows on 24/7 venues (Kraken U.S. perps), and overnight/weekend margin step-ups on Coinbase U.S. derivatives (e.g., 10x falling to 5x overnight; no reduced intraday margin on weekends/holidays). Dropping these risks bad pair selection and unexpected margin calls/rejects if derivatives are later enabled.
   Suggested addition to `## Rules for the build` (bringing total to 10 bullets):
   `- Screen pairs by verified order-book depth rather than printed volume, and handle venue maintenance windows and weekend/overnight derivatives margin step-ups explicitly [MEASURED] (research §§4, 5).`

4. **FIX: Dropped tax-ledger separation for derivatives/funding and taxable crypto-to-crypto swaps.**
   The research report (§6) notes that crypto-for-crypto swaps are taxable recognition events (favoring USD pairs over stablecoin/cross pairs for tax simplicity) and directs keeping futures and funding in separate ledger categories rather than assuming spot tax treatment applies. The playbook's Rule 8 logs fills and funding but omits separate derivative/spot ledger categorization.
   Suggested replacement for Rule 8:
   `- Record timestamped fills, fees, USD values, wallet/account lots, funding and transfer IDs; separate spot and futures/funding tax ledgers (treating crypto-to-crypto swaps as taxable events) and reconcile against broker reports [MEASURED] (research §6).`

5. **NOTE: Rule 5 evidence tag overstates live-signal proof relative to the report.**
   Rule 5 ("Use news, funding, on-chain activity and seasonality as risk and execution alerts, not trade triggers") is tagged `[MEASURED]`, whereas the report (§2) explicitly marks live retail capture of news/listings and attention/on-chain signals as `UNKNOWN` (with historical correlations `MEASURED`).
   Suggested replacement for Rule 5:
   `- Use news, funding, on-chain activity and seasonality as risk and execution alerts rather than directional trade triggers, as live small-account capture is unverified [UNKNOWN] (research §§2, 8).`

6. **NOTE: Section pointers (`§3`, `§5`, `§6`, `§8`) refer to unnumbered headings in the research file.**
   The research file `02_crypto_trading_evidence.md` uses unnumbered Markdown headers (`## U.S. spot pricing...`, `## Risks that change the build`, etc.), so build agents grepping for `§8` will not find a literal match.
   Suggested fix: Either reference exact heading names in parentheses (e.g., `(research: Implications for our build)`) or number the headings in `02_crypto_trading_evidence.md` if the author updates it.
