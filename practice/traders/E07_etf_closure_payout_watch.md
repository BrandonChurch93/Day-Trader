# E07 etf_closure_payout_watch

Status: approved forward measurement watch for queue row 95, written 2026-11-26. This is a MEASUREMENT with pretend money, not a profit claim: no orders, no broker integration, and no live capital. Historical replay of Row 95 is blocked on free primary payout data ([doc 114](../../docs/research/114_row95_etf_liquidation_payout_feasibility.md): 12 of 40 sampled closures had a recoverable dated primary payout, 30.0%). Because US ETF closures run at roughly 8 funds per month and issuers or clearinghouses publish payouts near liquidation, E07 measures the live forward spread between the last-trading-day closing SIP quote and the published cash liquidating distribution. No market prices or NAV histories were read while writing this card.

## Fund screen

Every business day, screen new SEC EDGAR Form 497, Form 497K, and Form 8-K filings (and corroborating issuer press releases) using the same screen used for the Row 95 docket (`"last day of trading" "liquidate"`, `"last day of trading" "liquidation"`, and `"closing date" "liquidation" "ETF"` on `efts.sec.gov`, serially with a real contact `User-Agent` and at least 0.4 seconds between requests).

Inclusion rules:

- Must be a US exchange-listed ETF (NYSE Arca, Nasdaq, or Cboe BZX) announcing a full cash liquidation and termination of the fund.
- Must state a scheduled last trading day strictly after the filing acceptance date (no retrospective backfilling of closures whose last trading day has already passed).
- Exclude mutual-fund-to-ETF reorganizations, ETF-to-ETF mergers without cash liquidation, and pure exchange delistings without a cash liquidating distribution.
- Exclude funds whose liquidation is later rescinded or converted into a merger before the last trading day (record the superseding filing URL and mark the event withdrawn).

Fields recorded at discovery (filings only, before any market data is read):

- `ticker`, `fund_name`, `exchange`, `cik`, `accession`, `form`, `edgar_acceptance_utc`, and `filing_url`.
- `stated_last_trading_day` and `stated_liquidation_or_payout_date` (updated if a later supplement amends either date, retaining both the original and amended filing URLs).
- `target_maturity_etf` (`true` for scheduled target-maturity bond ETFs such as iBonds, BulletShares, or State Street My2026; `false` for discretionary closures).
- `cash_before_last_trade` classification from the filing text: `pre_last_trade` (states the fund will liquidate holdings or convert to cash prior to the last trading day, or strikes final payout NAV on the last trading day itself), `post_last_trade_only` (states cash conversion occurs between the last trading day and the liquidation date), `timing_unspecified` (mentions cash conversion without stating whether it starts before the last trading day), or `not_stated` (no cash-conversion disclosure), together with the verbatim controlling sentence.

## Quote clock

On each fund's `stated_last_trading_day`, the logger reads NBBO quotes from the licensed SIP feed over `15:54:00` to `15:59:00` New York time (shifting symmetrically to `12:54:00` to `12:59:00` New York time on official [NYSE early-closing days](https://ir.theice.com/press/news/details/2024/NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx)).

Primary quote summary and cross-check:

- Primary closing bid and closing ask: duration-weighted median national best bid and duration-weighted median national best ask over `15:54:00` to `15:59:00` New York time, using a 60-second quote expiry and requiring at least 180 seconds of valid two-sided uncrossed coverage (the same SIP window and coverage rule used in E04 and Plan 36).
- Single-timestamp cross-check: exact SIP NBBO snapshot at `15:55:00` New York time (`12:55:00` New York time on early-closing days), recorded alongside the duration-weighted median to check for late-session drift.
- Missing or broken quote rule: if two-sided uncrossed coverage is below 180 seconds, or if the fund is halted or has no valid SIP ask in the window, log a quote refusal (`quote_status = missing_or_insufficient`) and exclude the fund from the numerical spread tally. Never substitute a trade print, midpoint, or prior-day close.

Why this quote clock: the `15:54:00` to `15:59:00` New York time window captures closing-day forced-exit liquidity in the final six minutes of regular trading while stopping 60 seconds before 16:00:00 New York time to avoid closing-auction imbalance freezes and quote-pulling artifacts. A marketable limit buy at the closing ask in this window is executable in a cash account at $0 commission with no exit order required.

## Primary payout source

When the fund completes liquidation, record the final cash liquidating distribution per share (`payout_per_share`) and actual `payment_date` (plus any final ordinary dividend or capital-gain distribution paid on or after the last trading day's close to holders of record through liquidation, with its ex-date and URL).

Allowed dated primary sources (the only sources that count toward the primary completion tally and decision rule):

- OCC Information Memo confirming final cash settlement per share (for optionable ETFs).
- Dated issuer closed-funds table, liquidation press release, or shareholder liquidation notice stating the final per-share cash payout and payment date.
- Issuer ICI Primary Layout tax file reporting Form 1099-DIV Box 9 cash liquidation distribution per share (plus any simultaneous Box 1a or Box 2a final distribution on the same payable date).
- IRS Form 8937 with an attached per-share dollar distribution schedule.

Excluded from the primary tally: retail broker trackers or tax-software logs (such as Robinhood Corporate Actions Tracker or TradeLog) may be recorded only in a separate `secondary_payout` field for operational diagnostics and never count as a completed primary fund or enter the decision rule. Unresolved payouts after 15 business days past `stated_liquidation_or_payout_date` are logged as `payout_status = primary_missing` and reported transparently in the completion rate.

## Measured quantities

For every completed fund (valid SIP NBBO on `stated_last_trading_day` plus verified dated primary payout), compute with pretend money ($0 entry commission, $0 exit cost, no margin):

- `payout_over_ask_minus_1 = (payout_per_share / closing_ask) - 1` (primary executable long-side measurement).
- `payout_over_bid_minus_1 = (payout_per_share / closing_bid) - 1` (bid-side reference to separate closing-day discount from half-spread cost).
- `closing_spread_bps = ((closing_ask - closing_bid) / ((closing_ask + closing_bid) / 2)) * 10000`.
- `days_last_trade_to_payment`: both calendar days and NYSE trading sessions from `stated_last_trading_day` to actual `payment_date`.

All aggregate summaries are reported on four slices: all completed funds, discretionary closures (`target_maturity_etf = false`), target-maturity bond ETFs (`target_maturity_etf = true`), and the `pre_last_trade` cash-converted subgroup versus `post_last_trade_only` (to separate pure settlement-discount capture from post-delisting market risk).

## Stop rule and decision rule

Stop condition: stop admitting new last-trading-day observations as soon as **40 completed primary-source funds** are recorded OR on **2027-05-31**, whichever comes first. Any fund whose `stated_last_trading_day` falls on or before `2027-05-31` gets a 15-business-day grace window (through `2027-06-21`) to publish its primary payout before final scoring.

Fixed decision rule (set before any price or payout is read): write a follow-on preregistered profit replay or live pretend-money trading rule ONLY IF ALL four conditions hold on the completed primary-source sample (minimum 20 completed primary funds if stopped by date; below 20 completed primary funds is ruled inconclusive on data availability):

1. Mean `payout_over_ask_minus_1` across all completed primary funds is strictly greater than `+0.25%` (+25 bps).
2. At least `60.0%` of completed primary funds have `payout_over_ask_minus_1 > 0`.
3. Median `payout_over_ask_minus_1` across all completed primary funds is strictly greater than `0%`.
4. Mean `payout_over_ask_minus_1` is strictly greater than `+0.15%` (+15 bps) on the discretionary closure subgroup (`target_maturity_etf = false`, if n >= 15) AND strictly greater than `+0.15%` on the `pre_last_trade` cash-converted subgroup (if n >= 10).

Justification for the decision rule: a `+0.25%` mean net of the closing ask over a typical 2 to 5 calendar-day settlement lockup clears cash-rate carry (~4 to 8 bps over 3 to 5 days at ~4% annualized) plus residual operational and tax-reporting friction, while requiring at least 60% positive hit rate and a positive median prevents a single volatile post-delisting equity move from carrying the mean. The subgroup checks ensure any measured spread is not solely target-maturity bond accrual or lucky market beta on funds that stay invested after delisting. If the decision rule fails, Row 95 closes on measured forward evidence.

## Private and public logs

Follow the E03 and E04 privacy boundary:

- Raw SIP quotes, snapshot timestamps, per-fund dollar payouts, and private packets stay outside the repository in `/home/user/workspace/rig/data/forward_e07` (directory mode 0700, file mode 0600). Never commit raw prices, quotes, or per-fund dollar amounts to the repository.
- Public log `practice/forward/E07_log.json` (created on the first recorded event and given an `docs/INDEX.md` row then) stores only filing evidence, dates, `cash_before_last_trade` and `target_maturity_etf` flags, stage statuses, SHA-256 hashes of private packets, previous-record hash, and final aggregate percentages at stop.

## Opening 45-day watch list (2026-11-26 through 2027-01-10)

Off-repo file: /home/user/workspace/rig/inventories/e07_opening_watchlist_20261126.csv
SHA-256: `7686bf3d88e3865126d9fa026e178e58b0c28bccf497cbf96d6ada769af69c09`

MEASURED: As of 2026-11-26, SEC EDGAR Form 497 and Form 497K filings contain 20 US exchange-listed ETFs with a stated last trading day in the next 45 days (14 discretionary closures and 6 scheduled target-maturity bond ETFs; no prices read).

| Ticker | Fund name | Exchange | Last trading day | Liquidation / payout | Target maturity | Cash before last trade | Filing |
|---|---|---|---|---|---|---|---|
| HFSP | TradersAI Large Cap Equity & Cash ETF | NASDAQ | 2026-11-30 | 2026-12-04 | false | post_last_trade_only | [497](https://www.sec.gov/Archives/edgar/data/1722388/000199937126025811/hfsp-497_111926.htm) |
| IBMO | iShares iBonds Dec 2026 Term Muni Bond ETF | Cboe BZX | 2026-12-01 | 2026-12-04 | true | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1100663/000119312526410673/d179727d497.htm) |
| MYCF | State Street My2026 Corporate Bond ETF | NYSE Arca | 2026-12-09 | 2026-12-16 | true | timing_unspecified | [497K](https://www.sec.gov/Archives/edgar/data/1516212/000119312526458603/d143202d497k.htm) |
| MYMF | State Street My2026 Municipal Bond ETF | NYSE Arca | 2026-12-09 | 2026-12-16 | true | timing_unspecified | [497](https://www.sec.gov/Archives/edgar/data/1516212/000119312526458575/d512394d497.htm) |
| BBYY | GraniteShares YieldBOOST BABA ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| CWY | GraniteShares YieldBOOST CRWV ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| FBYY | GraniteShares YieldBOOST META ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| FINY | GraniteShares YieldBOOST Financials ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| FIYY | GraniteShares YieldBOOST 20Y + Treasuries ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| GBHI | Gabelli High Income ETF | NYSE Arca | 2026-12-11 | 2026-12-11 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1748425/000182912626012203/gabelli_497.htm) |
| HMYY | GraniteShares YieldBOOST HIMS ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| MTYY | GraniteShares YieldBOOST MSTR ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| TECY | GraniteShares YieldBOOST Technology ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| TMYY | GraniteShares YieldBOOST TSM ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| XEY | GraniteShares YieldBOOST Ether ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| YBST | GraniteShares YieldBOOST Single Stock Universe ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| YBTY | GraniteShares YieldBOOST Top Yielders ETF | NASDAQ | 2026-12-11 | 2026-12-14 | false | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1689873/000149315226053289/form497.htm) |
| IBDR | iShares iBonds Dec 2026 Term Corporate ETF | NYSE Arca | 2026-12-15 | 2026-12-18 | true | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1100663/000119312526422932/d185272d497.htm) |
| IBHF | iShares iBonds 2026 Term High Yield and Income ETF | Cboe BZX | 2026-12-15 | 2026-12-18 | true | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1100663/000119312526422932/d185272d497.htm) |
| IBTG | iShares iBonds Dec 2026 Term Treasury ETF | NASDAQ | 2026-12-15 | 2026-12-18 | true | pre_last_trade | [497](https://www.sec.gov/Archives/edgar/data/1100663/000119312526422932/d185272d497.htm) |
