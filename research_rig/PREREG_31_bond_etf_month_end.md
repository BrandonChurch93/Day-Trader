# Plan 31. Bond ETF month-end beyond Treasuries and stocks

Status FROZEN.

Ledger 166, queue 50. STATED. Buy LQD, HYG, MBB and TIP long-only in four equal dollar sleeves at the close of the fourth-last XNYS session; sell each at the last session's close. Do this in the same three close-to-close intervals as Replay 25, January 2016 through October 2026. There are 130 planned months and 126 judged months after warm-up. Hold cash at zero yield otherwise. No leverage, taxes, reinvestment, or selection among funds.

STATED. The session window is borrowed from [Replay 25](PREREG_25_treasury_month_end.md) rather than prescribed for these funds. [Hartley and Schwarz](https://www.kristaschwarz.com/EOM.pdf) studied Treasury returns, not a distinct holding window for these ETFs. The [LQD iBoxx USD Liquid Investment Grade rules](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-iboxx-usd-liquid-investment-grade-index.pdf), [HYG iBoxx USD Liquid High Yield rules](https://www.spglobal.com/spdji/en/documents/methodologies/methodology-iboxx-usd-liquid-high-yield-index.pdf), [MBB Bloomberg US MBS rules](https://assets.bwbx.io/documents/users/iqjWHBFdfxIU/rpzM2Qx4j71A/v0), and [TIP ICE inflation-linked Treasury rules](https://www.ice.com/publicdocs/data/ICE-Indices_US_Treasury_Inflation_Linked-Bond-Index_6-9-16-p.pdf) specify month-end index maintenance, not an ETF buy-to-sell window. Cutoffs, previews, and index valuation conventions are not trade instructions.

## Inputs and timing

- **Calendar**: Pin the existing XNYS schedule from Replay 25, generated with exchange-calendars 4.13.3. Use exactly its 2,723 ordered sessions from January 4, 2016 through October 30, 2026. Require all seven series on every session. There is no prior closing bar on this input clock, so January 4, 2016 has no close-to-close interval. Use the scheduled close on early-close sessions too.
- **Bars**: Raw, unadjusted daily SIP bars for LQD, HYG, MBB, TIP, IEF, IEI and SPY, with New York session dates. Vendor-neutral schema; no adjusted, stale, zero-volume, missing, duplicated, or extra rows or alternative fields. Require finite positive OHLC and volume, a valid OHLC range, and no five consecutive identical OHLC tuples. Close is the consolidated close proxy. No untimed substitution, fill interpolation or missing-month exclusion.
- **Payouts**: For all seven ETFs require independently reviewed, dated issuer USD cash payouts per share, with unique event IDs, official source reference and an ex-date on the covered clock. Distinct same-date cash events add; do not duplicate an event. Require documented full coverage and no splits over the staged period; the contract has no split adjustment or price fallback. Approve this packet's digest independently of the bar manifest. No payout amounts leave the private input area or enter result documents.

The private input directory has a manifest plus seven symbol JSON arrays and one cash-action JSON packet. Every market file requires a valid 64-character lowercase hex SHA-256 before opening and exact matching bytes before parsing. The manifest binds the raw SIP mode, the collection range and file digests; the approval binds the input manifest and issuer packet separately. Provenance and native exports, if applicable, stay in private custody outside this packet. A manifest declaration alone is not independent provenance.

## Benchmark and pooling

STATED. Proxy map fixed before any return: LQD, MBB and TIP use IEF; HYG uses IEI. These are approximate nominal-duration buckets, not per-date exact duration matches ([iShares IEF](https://www.ishares.com/us/literature/fact-sheet/ief-ishares-7-10-year-treasury-bond-etf-fund-fact-sheet-en-us.pdf), [iShares IEI](https://www.ishares.com/us/literature/fact-sheet/iei-ishares-3-7-year-treasury-bond-etf-fund-fact-sheet-en-us.pdf)). SPY is the same second, equity-market factor for all four funds. There is no proxy search or alternative judged factor model.

For each fund and month, fit two slopes with an intercept by ordinary least squares on gross one-share daily total returns. Fit on all preceding outside-window intervals, expanding, and freeze the slopes before the first session of the month. An interval is classified by its end date. The three final intervals of every planned month are inside, even in warm-up; the interval ending on the entry session is outside. No later day enters a month’s fit. Keep the slopes as fitted, including negative slopes; do not subtract the fitted intercept. Refuse a nonfinite or singular fit, including a normalized two-regressor determinant at or below 0.000000000001; do not drop the month or substitute a univariate fit.

A month is judged only with at least 60 earlier outside intervals before its first session. May 2016 is first, with 69; February through April have 15, 32 and 51 and are shown only. January has no usable earlier interval before its first session, so for its shown-only estimate use the 14 outside intervals ending strictly before its January entry session. January through April are excluded from all pass marks and the daily comparator. No warm-up return changes the eligibility rule.

Gross daily total return is (closing price plus cash on that ex-date) divided by the previous close, less one. A window earns cash on ex-dates strictly after entry and on or before exit. On each long fund the net return is (exit close less the sell fee plus those payouts) divided by (entry close plus the buy fee), less one. Each month compute the fund's net window return minus its Treasury slope times the same-window gross Treasury return, minus its equity slope times the same-window gross SPY return. The factors use the same non-reinvested cash rule and no transaction fees. Average the four residuals at equal weight for one observation per month, not four observations. Similarly average four long-fund net returns for the plain pooled series.

For the daily comparison, apply that same month's slopes to concurrent gross daily factor returns and average the four gross daily residuals, one observation per interval. There are 378 inside intervals and 2,263 outside intervals in the judged months. The outside comparison uses all eligible dates including the entry-date interval; it is not fit on the same month. A positive mean residual alone could reflect carry, which is why the separate inside-minus-outside marks are required.

## Ten marks

Use 2 basis points per side on actual long-fund traded notional. Require all ten on the pooled series, with no individual fund verdict:

- **Count**: At least 100 judged monthly observations.
- **Mean**: Strictly positive mean monthly residual.
- **Monthly t**: One-sample residual t-statistic at least 2.0.
- **Trim**: Strictly positive mean residual after dropping the three highest residual months.
- **Daily comparison**: Gross inside-minus-outside mean residual strictly positive and Welch t at least 2.0.
- **Monthly breadth**: At least seven of eleven calendar years have strictly positive mean monthly residuals.
- **Later period**: Strictly positive mean monthly residual from January 2020.
- **Leave one year out**: Strictly positive mean monthly residual after omitting each single calendar year in turn; equal weight each remaining month.
- **Daily breadth**: At least seven of eleven years have a strictly positive inside-minus-outside gross daily residual mean.
- **Plain long-only**: Strictly positive mean net pooled long-only monthly return over the same judged months.

The partial years at the two sample ends each count as one year. A zero or undefined standard error fails its associated t mark. Report the full leave-one-year-out and year-by-year daily comparisons. Show plain and residual summaries for the pool and each fund at 2, 5 and 10 basis points per side, the four warm-up months at 2 basis points, and the observed beta ranges with no extra verdicts. Do not change the window, factor selection or costs based on any of those views.

## What can be traded

STATED. The actual modeled position is the long-only fund basket, nominally 125 dollars per sleeve of a 500-dollar cash account. Treasury and SPY are calculation yardsticks, not shorts or other legs, so there are no factor fees, borrow charges, or simulated short fills. A broker that supports fractional ETF day orders can implement that cash allocation near the close; these are not verified auction fills ([Alpaca fractional order types](https://docs.alpaca.markets/us/docs/fractional-trading)). The cost assumptions are not a fill guarantee.

The residual is evidence against a simple linear explanation using these two proxies, not a standalone realizable return or proof of independence or causal index flows. TIP is a Treasury inflation-linked fund and retains real-yield and inflation exposure; MBB is agency MBS and retains optionality and prepayment exposure; LQD and HYG retain credit-spread exposure. Model residuals may therefore reflect omitted risks or beta changes. Conventional t-statistics do not adjust for serial dependence or prior idea screening. A pooled pass is not four independent discoveries.

## Validation and one scored run

The frozen manifest pins this plan, the runner, the synthetic tests, the numerical modules and the calendar. The `replay_31_plan` thresholds block mirrors the pinned rules and is not read at runtime. After the exact-commit audit, the lead agent stores the exact approval line bound to the frozen commit, freeze digest, input manifest digest and independently checked action digest. The runner requires the exact clean approval commit, ancestry, frozen bytes and a frozen ledger row. It refuses environment overrides and reads only the fixed private data directories. Invoke in an isolated, bytecode-disabled Python with a clean environment under the agreed memory and priority limits.

Validation loads and checks the full packet silently, without computing any daily or monthly returns, factor slopes or marks and without claiming a lock. It emits only a fixed refusal or the number of symbols, sessions per symbol, planned months and expected judged months from the calendar. Real validation is lead-only. The lead agent gives a separate go before any score. On go, the runner validates silently again and creates the exclusive lock immediately before any score. After a claim, any failure consumes the attempt. There is no real preview, retry, or lock removal. The result contains aggregate statistics and the run record, not bars or payouts.
