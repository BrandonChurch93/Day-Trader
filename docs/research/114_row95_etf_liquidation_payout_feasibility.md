# Row 95: ETF Cash-Liquidation Payout Feasibility (Price-Blind)

Date: 2026-11-26
Status: Feasibility audit complete (price-blind; no market prices, no NAV histories, no return calculations)
Input docket: /home/user/workspace/rig/inventories/row95_etf_liquidation_docket.csv (670 cash-liquidated US ETFs from SEC EDGAR Form 497/497K/8-K filings, 2016 to 2026; SHA-256 `7cacced5cb62f38c49a2032e5c29cee893d04dbffd0ed7dbf4fb1da5886d70a0`).

## Summary verdict

MEASURED: In a seeded, filing-year-stratified random sample of 40 docket rows (`seed = 20261126`), only 12 of 40 funds (30.0%) have a verified final cash liquidating distribution per share and payment date recoverable from a dated primary source (5 OCC Information Memos, 4 issuer closed-funds pages, 2 issuer ICI Primary Layout tax files, 1 IRS Form 8937, and 0 SEC N-CSR or N-CSRS filings).

MEASURED: Across all 670 docket filings, only 195 of 670 (29.1%) explicitly state that the fund will convert to cash or stop tracking its index before or during the run-up to the last trading day, while 209 of 670 (31.2%) state that cash conversion occurs only after the last trading day (between last trade and liquidation), 137 of 670 (20.4%) state cash conversion without specifying timing, and 129 of 670 (19.3%) make no cash-conversion statement.

STATED: From Alpaca's Market Data API documentation alone (no data call), the corporate actions endpoint has no `liquidation` event type and its documented `redemption`, `reorganization`, and `cash_dividend` schemas do not specify ETF cash liquidations; Alpaca's Mandatory Corporate Actions guide defines Final Liquidation separately for SPACs, CVRs, and escrow shares.

STATED: Neither Boehmer and Finta (SSRN 4328422) nor any peer-reviewed source found isolates the exact ask-to-payout discount on the final trading day; Boehmer and Finta report a 1-month post-announcement average discount of -3.1% (t = -2.57), while practitioner notes describe wider final-day discounts (0.1% to 0.5% on liquid funds, wider on illiquid holdings) paired with widening bid-ask spreads and potential market risk during post-delisting settlement.

Decision implication: A clean, unbiased historical backtest of buying at the ask on the last trading day and collecting the exact cash liquidation payout is blocked on free public primary data (only 30.0% primary payout coverage, heavily skewed toward optionable funds and a few issuers), and 31.2% to 70.9% of docket events do not guarantee cash-only holdings between the last trading day and payout.

## Part 1: 40-fund seeded sample payout audit

### Sampling design

MEASURED: 40 rows were drawn without replacement from the 670-row docket using Python `random.Random(20261126)` stratified proportionally by SEC EDGAR acceptance year (`2016: 2, 2017: 3, 2018: 2, 2019: 5, 2020: 4, 2021: 1, 2022: 3, 2023: 6, 2024: 3, 2025: 5, 2026: 6`; total 40). Payout amounts and payment dates were checked only against dated primary sources (issuer closed-funds pages, issuer ICI Primary Layout tax files, IRS Form 8937, SEC N-CSR and N-CSRS filings, and OCC Information Memos); no market prices or NAV histories were retrieved.

### Primary-source recovery by source type

| Primary source type | Verified funds (unique primary count) | Share of 40 | Notes |
|---|---:|---:|---|
| OCC Information Memos | 5 | 12.5% | `MJIN`, `KFYP`, `NVQ`, `KEM`, `OOTO` (`IWFH` also has OCC Memo 57135, counted once under Issuer closed-funds page) |
| Issuer closed-funds / closures pages | 4 | 10.0% | `IBDF` and `IWFH` (iShares); `HYRM` and `CA` (Xtrackers) |
| Issuer ICI Primary Layout tax files (1099-DIV Box 9) | 2 | 5.0% | `QPT` and `DWEQ` (AdvisorShares 2022 and 2023 Primary Layout files) |
| IRS Form 8937 (with dollar payout) | 1 | 2.5% | `HDEZ` (DWS Form 8937 attachment) |
| SEC filings (N-CSR, N-CSRS, 497, 8-K) | 0 | 0.0% | Audited across all 40 CIKs; post-liquidation N-CSR/N-CSRS notes omit per-share cash payout |
| Total verified dated primary sources | 12 | 30.0% | 28 of 40 (70.0%) lack a retrieved dated primary per-share payout |

### Structural reasons for the 70.0% primary-source gap

SEC N-CSR and N-CSRS filings do not report per-share cash liquidation payouts. MEASURED: Every one of the 40 sampled CIKs was checked on SEC EDGAR for post-liquidation `N-CSR` and `N-CSRS` filings, yielding 0 of 40 per-share payouts. For example, the BNY Mellon ETF Trust `N-CSRS` ([SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1493580/000003014625000100/output.htm)) covering `RHCB` and `BKWO` states only: "Shareholders of record of the fund on the Liquidation Date received cash equal to the net asset value of their shares as of such date." Similarly, the ETFS Trust `N-CSR` ([SEC EDGAR](https://www.sec.gov/Archives/edgar/data/1597934/000138713117001191/etfs-ncsr_123116.htm)) covering `ZSML` omits any per-share cash distribution figure.

Tax reporting rules split issuers between Form 1099-DIV Box 9 and Form 1099-B. STATED: The Investment Company Institute 2025 Primary Layout instructions ([ICI Primary Layout Guide](https://www.ici.org/system/files/2025-09/taxrpt25_primary.pdf)) state: "Note that some funds report liquidating distributions in redemption of fund shares as redemption proceeds on Form 1099-B (Proceeds from Broker and Barter Exchange Transactions) instead of liquidating distributions on Form 1099-DIV, boxes 9 and 10." MEASURED: AdvisorShares reports cash liquidation payouts in Column 28 (Box 9) of its ICI Primary Layout spreadsheets (`QPT` in [2022 AdvisorShares Primary Layout](https://advisorshares.com/wp-content/uploads/2023/01/2022-AdvisorShares__Primary_Layout_File.xlsx) and `DWEQ` in [2023 AdvisorShares Primary Layout](https://advisorshares.com/wp-content/uploads/2024/01/2023_AdvisorShares_Primary_Layout_File.xlsx)), whereas Direxion's ICI Primary Layout spreadsheets ([2020 Direxion Primary Layout](https://www.direxion.com/uploads/2020-ICI-Primary-Direxion.xlsx) and [2025 Direxion ETF Primary Layout](https://www.direxion.com/uploads/2025-ICI-Primary-Direxion-ETF.xlsx)) list closed funds `SMLL`, `RWCD`, and `OOTO` only for ordinary quarterly dividends with zero Box 9 liquidation entries.

IRS Form 8937 is generally not required for single lump-sum taxable cash redemptions. STATED: The [IRS Instructions for Form 8937](https://www.irs.gov/instructions/i8937) specify that Form 8937 is filed for organizational actions that affect the quantitative basis of a security; even when an ETF issuer files Form 8937 on liquidation, it may omit the dollar payout, as in AdvisorShares `QPT` ([QPT Form 8937](https://advisorshares.com/wp-content/uploads/2022/11/AdvisorShares-Q-Portfolio-Blended-Allocation-ETF-%E2%80%94-Form-8937.pdf)), which states only: "The above-named issuer was completely liquidated on November 4, 2022."

Issuer web archives expire and OCC memos cover only optionable ETFs. STATED: BNY Mellon's closed-funds page ([BNY Merged or Liquidated Funds](https://www.bny.com/investments/us/en/individual/products/merged-or-liquidated-funds.html)) states: "No funds have been liquidated or merged within the last 90 days," dropping `RHCB` (2024) and `BKWO` (2025). AdvisorShares's [Literature Center](https://advisorshares.com/about/literature-center/) hosts ICI Primary Layout files only back to 2021, excluding `KOR` (2018), `FNG` (2019), and `SCAP` (2020). OCC Information Memos provide exact per-share cash settlements only for ETFs with listed options; one additional optionable fund in the sample (`PFES`) has a confirmed final OCC Memo 52745 referenced in [OCC Memo 52868](https://infomemo.theocc.com/infomemos?number=52868), while `SWEB` has anticipated Memo 52681, but `infomemo.theocc.com` returned HTTP 403 to automated retrieval and Memo 52745 text was not indexed in search results, so `PFES` is counted as unverified.

Secondary broker and tax-software trackers are excluded from the primary count. MEASURED: Seven additional sample funds (`RHCB`, `BKWO`, `GHMS`, `CZAR`, `TSLO`, `NWLG`, `SCLS`, all from 2024 to 2026) appear with per-share cash payouts only on secondary retail-broker or tax-software trackers ([Robinhood Corporate Actions Tracker](https://robinhood.com/us/en/support/articles/corporate-actions-tracker/), [TradeLog 2024 Corporate Action History](https://support.tradelogsoftware.com/hc/en-us/articles/20320099321751-Corporate-Action-History-for-2024), [TradeLog 2026 Corporate Action History](https://support.tradelogsoftware.com/hc/en-us/articles/37503308556695-Corporate-Action-History-for-2026), and [FIM-TIC Corporate Actions Tracker](https://fim-tic.com/corporate-action/)). Even if broker trackers were accepted as a secondary fallback, coverage would reach 19 of 40 (47.5%) and remain heavily biased toward 2024 to 2026 closures.

### Verified primary-source quotes for the 12 recovered funds

- `IBDF` (2016): `$25.034152` as of `2016-12-21` per [iShares Closed Funds](https://www.ishares.com/us/products/closed-funds/updates) (table row for iShares iBonds Dec 2016 Term Corporate ETF, liquidation NAV `$25.034152` on 12/21/2016).
- `HDEZ` (2017): `$26.504800` payable `2018-01-02` per [DWS Form 8937 for HDEZ](https://www.dws.com/US/EN/resources/about-us/news-updates/792244_FORM_8937_HDEZ-2018-01-09.pdf) (Form 8937 liquidation distribution schedule listing `$26.504800` per share payable 1/2/2018).
- `QPT` (2022): `$19.1878` total (`$19.14579` Box 9 Cash Liquidation Distr plus `$0.04201` Box 1a Ordinary Income) payable `2022-11-04` per [2022 AdvisorShares Primary Layout](https://advisorshares.com/wp-content/uploads/2023/01/2022-AdvisorShares__Primary_Layout_File.xlsx) (row 59).
- `MJIN` (2022): `$15.36335983` on `2022-11-28` per [OCC Information Memo 51430](https://infomemo.theocc.com/infomemos?number=51430) ("Proceeds of the liquidation were distributed to shareholders in the amount of $15.36335983 per MJIN share on November 28, 2022").
- `DWEQ` (2023): `$17.387` Box 9 Cash Liquidation Distr payable `2023-04-10` per [2023 AdvisorShares Primary Layout](https://advisorshares.com/wp-content/uploads/2024/01/2023_AdvisorShares_Primary_Layout_File.xlsx) (row 71).
- `KFYP` (2023): `$22.0153` on `2023-10-31` per [OCC Information Memo 53466](https://infomemo.theocc.com/infomemos?number=53466) ("Proceeds of the liquidation were distributed to shareholders in the amount of $22.0153 per KFYP share on October 31, 2023").
- `NVQ` (2024): `$33.59537` on `2024-02-16` per [OCC Information Memo 54149](https://infomemo.theocc.com/infomemos?number=54149) ("Proceeds of the liquidation were distributed to shareholders in the amount of $33.59537 per NVQ share on February 16, 2024").
- `IWFH` (2024): `$14.411074` on `2024-08-15` per [iShares Closed Funds](https://www.ishares.com/us/products/closed-funds/updates), [iShares 2024 Distribution Summary](https://www.ishares.com/us/literature/tax-information/2024-ishares-etf-distribution-summary-stamped-extended.pdf), and [OCC Information Memo 57135](https://infomemo.theocc.com/infomemos?number=57135).
- `KEM` (2025): `$27.6196` on `2025-05-29` per [OCC Information Memo 56632](https://infomemo.theocc.com/infomemos?number=56632) ("Proceeds of the liquidation were distributed to shareholders in the amount of $27.6196 per KEM share on May 29, 2025").
- `OOTO` (2025): `$18.84849` on `2025-07-30` per [OCC Information Memo 56979](https://infomemo.theocc.com/infomemos?number=56979) ("Proceeds of the liquidation were distributed to shareholders in the amount of $18.84849 per OOTO share on July 30, 2025").
- `HYRM` (2026): `$23.27669` on `2026-05-30` per [Xtrackers Closures](https://etf.deutsche-am.com/en-us/etf-documents/closures/) (liquidation table listing `$23.27669` payable `May 30, 2026`).
- `CA` (2026): `$24.85160` on `2026-05-22` per [Xtrackers Closures](https://etf.deutsche-am.com/en-us/etf-documents/closures/) (liquidation table listing `$24.85160` payable `May 22, 2026`).

### Full 40-fund sample audit table (seed 20261126)

| # | Year | Ticker | Stated last trade | Stated liquidation | Primary payout / share | Primary pay date | Primary source type | Audit note |
|---:|---:|---|---|---|---|---|---|---|
| 1 | 2016 | ZSML | 2017-01-23 | 2017-01-30 | None | None | None | N-CSR omits per-share dollar amount |
| 2 | 2016 | IBDF | 2016-12-15 | 2016-12-21 | $25.034152 | 2016-12-21 | Issuer closed-funds page | [iShares Closed Funds](https://www.ishares.com/us/products/closed-funds/updates) |
| 3 | 2017 | PILL | 2017-03-31 | 2017-04-07 | None | None | None | Direxion ICI files omit Box 9 |
| 4 | 2017 | OEUH | 2017-11-30 | 2017-12-08 | None | None | None | No primary payout found |
| 5 | 2017 | HDEZ | 2017-12-18 | 2017-12-18 | $26.504800 | 2018-01-02 | IRS Form 8937 | [DWS Form 8937](https://www.dws.com/US/EN/resources/about-us/news-updates/792244_FORM_8937_HDEZ-2018-01-09.pdf) |
| 6 | 2018 | SQZZ | 2018-05-25 | 2018-05-30 | None | None | None | No primary payout found |
| 7 | 2018 | KOR | 2018-10-01 | 2018-10-08 | None | None | None | AdvisorShares ICI archive starts 2021 |
| 8 | 2019 | INAG | 2019-12-16 | 2019-12-17 | None | None | None | No primary payout found |
| 9 | 2019 | FNG | 2019-10-04 | 2019-10-11 | None | None | None | AdvisorShares ICI archive starts 2021 |
| 10 | 2019 | CNHX | 2020-01-06 | 2020-01-10 | None | None | None | No primary payout found |
| 11 | 2019 | XLSY | 2019-11-22 | 2019-11-27 | None | None | None | No primary payout found |
| 12 | 2019 | QXGG | 2019-05-16 | 2019-05-24 | None | None | None | No primary payout found |
| 13 | 2020 | RWCD | 2020-09-25 | 2020-10-02 | None | None | None | Direxion 2020 ICI file has 0 Box 9 |
| 14 | 2020 | PPEM | 2020-09-25 | 2020-10-02 | None | None | None | Direxion 2020 ICI file has 0 Box 9 |
| 15 | 2020 | SCAP | 2020-04-09 | 2020-04-16 | None | None | None | AdvisorShares ICI archive starts 2021 |
| 16 | 2020 | SMLL | 2020-09-25 | 2020-10-02 | None | None | None | Direxion 2020 ICI file has 0 Box 9 |
| 17 | 2021 | QMJ | 2021-09-17 | 2021-09-24 | None | None | None | Direxion ICI files omit Box 9 |
| 18 | 2022 | QPT | 2022-10-28 | 2022-11-04 | $19.1878 | 2022-11-04 | Issuer ICI Primary Layout | [2022 AdvisorShares Primary Layout](https://advisorshares.com/wp-content/uploads/2023/01/2022-AdvisorShares__Primary_Layout_File.xlsx) |
| 19 | 2022 | HDIV | 2023-01-20 | 2023-01-23 | None | None | None | No primary payout found |
| 20 | 2022 | MJIN | 2022-11-23 | 2022-11-23 | $15.36335983 | 2022-11-28 | OCC Information Memo | [OCC Memo 51430](https://infomemo.theocc.com/infomemos?number=51430) |
| 21 | 2023 | HOM | 2023-06-12 | 2023-06-16 | None | None | None | No primary payout found |
| 22 | 2023 | SWEB | 2023-06-16 | 2023-06-26 | None | None | None | OCC anticipated memo 52681 only |
| 23 | 2023 | KFYP | 2023-10-18 | 2023-10-27 | $22.0153 | 2023-10-31 | OCC Information Memo | [OCC Memo 53466](https://infomemo.theocc.com/infomemos?number=53466) |
| 24 | 2023 | PFES | 2023-06-16 | 2023-06-26 | None | None | None | OCC Memo 52745 cited in 52868 but 403/unindexed |
| 25 | 2023 | DWEQ | 2023-03-31 | 2023-04-10 | $17.387 | 2023-04-10 | Issuer ICI Primary Layout | [2023 AdvisorShares Primary Layout](https://advisorshares.com/wp-content/uploads/2024/01/2023_AdvisorShares_Primary_Layout_File.xlsx) |
| 26 | 2023 | TGN | 2023-10-24 | 2023-10-31 | None | None | None | No primary payout found |
| 27 | 2024 | RHCB | 2024-12-02 | 2024-12-09 | None | None | None | Broker/software only (TradeLog $46.5736) |
| 28 | 2024 | NVQ | 2024-02-14 | 2024-02-16 | $33.59537 | 2024-02-16 | OCC Information Memo | [OCC Memo 54149](https://infomemo.theocc.com/infomemos?number=54149) |
| 29 | 2024 | IWFH | 2024-08-13 | 2024-08-15 | $14.411074 | 2024-08-15 | Issuer closed-funds page | [iShares Closed Funds](https://www.ishares.com/us/products/closed-funds/updates); OCC Memo 57135 |
| 30 | 2025 | KEM | 2025-05-20 | 2025-05-27 | $27.6196 | 2025-05-29 | OCC Information Memo | [OCC Memo 56632](https://infomemo.theocc.com/infomemos?number=56632) |
| 31 | 2025 | UTRN | 2025-03-25 | 2025-03-28 | None | None | None | No primary payout found |
| 32 | 2025 | OOTO | 2025-07-24 | 2025-07-30 | $18.84849 | 2025-07-30 | OCC Information Memo | [OCC Memo 56979](https://infomemo.theocc.com/infomemos?number=56979) |
| 33 | 2025 | GHMS | 2025-11-25 | 2025-11-28 | None | None | None | Broker only (Robinhood $25.6359 on 2025-12-01) |
| 34 | 2025 | BKWO | 2025-09-12 | 2025-09-19 | None | None | None | Broker/tracker only (FIM-TIC $37.6808 on 2025-09-22) |
| 35 | 2026 | HYRM | 2026-05-07 | 2026-05-07 | $23.27669 | 2026-05-30 | Issuer closed-funds page | [Xtrackers Closures](https://etf.deutsche-am.com/en-us/etf-documents/closures/) |
| 36 | 2026 | CZAR | 2026-07-28 | 2026-07-31 | None | None | None | Broker only (Robinhood $32.9783 on 2026-08-03) |
| 37 | 2026 | TSLO | 2026-06-16 | 2026-06-25 | None | None | None | Broker only (Robinhood $18.2926 on 2026-06-25) |
| 38 | 2026 | CA | 2026-05-07 | 2026-05-07 | $24.85160 | 2026-05-22 | Issuer closed-funds page | [Xtrackers Closures](https://etf.deutsche-am.com/en-us/etf-documents/closures/) |
| 39 | 2026 | NWLG | 2026-04-06 | 2026-04-13 | None | None | None | Broker only (Robinhood $29.2504 on 2026-04-14) |
| 40 | 2026 | SCLS | 2026-06-16 | 2026-06-18 | None | None | None | Broker only (Robinhood $23.7774 on 2026-06-23) |

## Part 2: Alpaca Corporate Actions API (documentation only, no data call)

STATED: Per the [Alpaca Corporate Actions API Reference](https://docs.alpaca.markets/us/reference/corporateactions-1) and the [Alpaca Market Data OpenAPI Spec](https://docs.alpaca.markets/us/openapi/market-data-api.json), `GET https://data.alpaca.markets/v1/corporate-actions` exposes 16 event types: `reverse_split`, `forward_split`, `unit_split`, `cash_dividend`, `stock_dividend`, `spin_off`, `cash_merger`, `stock_merger`, `stock_and_cash_merger`, `redemption`, `name_change`, `worthless_removal`, `rights_distribution`, `partial_call`, `reorganization`, and `capital_gains_distribution`.

STATED: There is no `liquidation` event type in the OpenAPI schema. The closest schema types do not document ETF cash liquidations: `redemption` is described in the OpenAPI spec as `"Full redemption payload..."` without specifying ETF cash liquidations; `reorganization` is described as `"General-purpose corporate restructuring (e.g. Chapter 11 emergence)..."`; and `cash_dividend` restricts `sub_type` to `["interest", "return_of_capital"]`.

STATED: Alpaca's [Mandatory Corporate Actions Guide](https://docs.alpaca.markets/us/docs/mandatory-corporate-actions) lists `"Final Liquidation - This is when the shareholders of a company receive cash and the underlying shares are removed. This is usually done on SPACs or securities such as CVRs and escrow shares."` Alpaca's earlier [Corporate Actions Announcements Blog](https://alpaca.markets/blog/introducing-corporate-actions-api-announcements/) also noted: `"Additionally, bespoke reorganization announcements, such as symbol changes, redemptions, liquidations, delistings, and tender offers, are not available to view through the API at this time."`

UNKNOWN: Whether Alpaca populates `redemption` or `reorganization` records in practice for liquidated US ETFs cannot be confirmed from documentation alone without a live data call, which was excluded by instruction. From documentation alone, Alpaca does not guarantee ETF cash-liquidation payout coverage.

## Part 3: Pre-last-trading-day cash conversion across all 670 filings

MEASURED: All 670 announcement filings in the Row 95 docket were classified programmatically from their SEC EDGAR Form 497/497K/8-K text into four mutually exclusive categories based on whether and when the filing states the fund will convert holdings to cash or cease tracking its index.

| Cash-conversion timing stated in SEC 497/497K/8-K | Count | Share of 670 | Market-risk implication between last trade and payout |
|---|---:|---:|---|
| Between last trade and liquidation only | 209 | 31.2% | Holder carries market risk during post-delisting liquidation |
| Before or during run-up to last trading day | 195 | 29.1% | Fund may already be in cash or winding down before last trade |
| Stated, timing unspecified | 137 | 20.4% | Ambiguous whether portfolio is in cash by last trading day |
| Not stated in announcement filing | 129 | 19.3% | No disclosure of pre-delisting cash conversion |
| Total docket | 670 | 100.0% | Only 29.1% explicitly disclose pre-last-trade cash conversion |

Representative verbatim primary-source sentences for each bucket:

- Between last trade and liquidation only (`VLLV`, [SEC Form 497](https://www.sec.gov/Archives/edgar/data/1424958/000119312516485662/d120055d497.htm)): `"Between the Last Trading Day and the Liquidation Date, the Fund will be in the process of closing down and liquidating its portfolio. This process will result in the Fund increasing its cash holdings and, as a consequence, not tracking its underlying index."`
- Before or during run-up to last trading day (`ERW`, [SEC Form 497](https://www.sec.gov/Archives/edgar/data/1452937/000139834416009665/fp0017930_497.htm)): `"Prior to the Last Trading Day, the Fund will begin the process of liquidating its portfolio and will no longer pursue its stated investment objective or track its underlying index."`
- Stated, timing unspecified (`IBME`, [SEC Form 497K](https://www.sec.gov/Archives/edgar/data/1100663/000119312516618938/d209139d497k.htm)): `"In connection with the liquidation, the Fund will convert its assets to cash and cash equivalents and will no longer track its underlying index."`
- Not stated (`SNLN`, [SEC Form 497](https://www.sec.gov/Archives/edgar/data/1354917/000119312516529112/d132798d497.htm)): Filing announces the last trading day and liquidation date without stating when portfolio assets are converted to cash.

## Part 4: What the literature and practitioner sources say about final-day discounts

STATED: Boehmer and Finta (SSRN 4328422, [Exchange-Traded Fund Closures](https://acfr.aut.ac.nz/__data/assets/pdf_file/0004/809644/Exchange-Traded-Fund-Closures-FULL-ssrn-maf2.pdf)) do not isolate the final trading day or ask-to-payout return. Their Table 5 Panel B reports an average 1-month post-announcement Premium/Discount of `-0.031` (t = `-2.57`) compared to `-0.016` (t = `-1.81`) before announcement, and Section 3.4 states: `"following the announcement, closing ETF shares trade at a high discount."`

STATED: Practitioner notes specifically describe widening discounts and bid-ask spreads on the final trading sessions. [ETF BFF on ETF Fund Closures](https://etfbff.com/blog/etf-fund-closure/) states: `"In the final days before a fund liquidates, the premium or discount to NAV tends to widen on the negative side... typically 0.1% to 0.5% on a liquid fund and potentially more on one with illiquid holdings."` [The Weekly Investor](https://www.the-weekly-investor.com/articles/13-themes-etfs-close-july-28-exit-by-thursday-1784718225889) notes: `"Bid-ask spreads widen, and in small or illiquid funds, the discount to NAV can become material within hours."`

STATED: Broker and regulator guidance highlights execution and settlement frictions for holders who wait until liquidation. [Charles Schwab on ETF Closures](https://www.schwab.com/learn/story/what-happens-if-your-etf-closes) and the [SEC Investor Bulletin on Fund Liquidation](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/investor-bulletin-fund-liquidation) both warn that market makers may widen spreads as liquidity dries up before the last trading day and that shareholders who hold through liquidation face a multi-day settlement delay while the fund liquidates remaining positions into cash.

UNKNOWN: Whether the final-day ask-to-payout spread is positive net of bid-ask spread and post-delisting market risk across a representative US ETF liquidation sample cannot be determined from existing literature and cannot be backtested without an institutional corporate-actions payout feed (since free primary sources recover only 30.0% of payouts in our 40-fund audit).
