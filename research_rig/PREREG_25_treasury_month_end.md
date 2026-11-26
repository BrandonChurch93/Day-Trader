# Plan 25. Treasury ETF month-end window

Status FROZEN.

Queue 41, ledger 162. Before this refreeze the author inspected SIP clocks only, without decoding or retaining any price or volume field or reading any distribution amount or return. The owner must approve the new freeze and separately authorize collection and a one-shot run.

## Claim and rule

STATED. Use unlevered, long-only TLT at the close of the fourth-last US equity trading session each month. Close the position at the close of the last session. Those are the last three close-to-close returns. Hold cash otherwise, with no return or interest on cash. Count January 2016 through October 2026 inclusive. Judge TLT only, with 2 basis points of cost on each traded notional. Price and time components are not optimized.

- **Calendar**: Use XNYS sessions from the pinned `exchange-calendars` 4.13.3 schedule. Require identical, ordered coverage from both ETFs, all 2,740 sessions from January 4, 2016 through November 24, 2026 inclusive. MEASURED. The first collection refused because December 31, 2015 was unavailable for both ETFs. Exact timestamp and earlier start probes did not recover it, consistent with [Alpaca's documented equity-history boundary](https://docs.alpaca.markets/us/docs/about-market-data-api). No alternate vendor or substitute bar is used. This removes only the outside interval ending January 4, 2016. The 130 judged windows and 390 inside intervals are unchanged; there are 2,332 outside intervals. The November extension is not judged, and only its first three sessions enter the final shown cross-month window. Trade at the daily close on the scheduled session, including any early close.
- **Bar source**: Alpaca historical daily SIP. Use the owner's existing credential through `pplx credentials run`. Prices and daily volume stay in a private off-repo input directory. Nothing requests live data or a date after November 24, 2026.
- **Payouts**: Require raw bars plus a single pinned dated issuer cash-action packet for both ETFs, with the per-share USD amount, official source reference, distinct event ID and ex-date for each distribution. Record all types of cash distribution included by the source. Require independent review of both funds' action coverage and confirmation that no split needs accounting within the staged interval. The owner approves the cash-action digest separately before collection; the same digest is required when scoring. Missing data are not evidence of zero events. There is no adjusted-bar fallback in this plan. An absent or unapproved packet, adjusted data, or an unexpected split refuses.
- **Quality**: The fetcher checks session dates and volume only and prints the manifest hash and metadata counts. In the scorer's silent validation, refuse inconsistent OHLC, zero volume, or five consecutive identical OHLC tuples as in the stock replay's flat-run check, including the stale flat zero-volume case. Refuse missing, out-of-order, repeated or extra sessions rather than skipping a month, guessing a price, or treating the missing data as cash.

## Returns and pass marks

Hold one share as the normalization unit throughout a window. A payout on a session after the purchase close and through the sale session, inclusive, earns its amount once on the ex-date. A payout on the entry session or after the exit does not qualify. Do not reinvest or earn interest on these credits. Net window return is (sale close after sell cost plus earned distributions) divided by (buy close including buy cost), minus one.

To compare asset drift rather than strategy fees, compute a gross one-share daily total return as (close plus cash ex-date amount) divided by previous close minus one. Classify by the date the interval ends, also for calendar-year buckets. The comparator consists of every available close-to-close interval ending outside the judged windows from January 2016 through October 2026, including entry-day returns. Welch t is the difference of means divided by the square root of the sum of the two sample-variance-per-observation terms. Use the usual one-sample statistic for net window returns. A zero or undefined standard error fails the associated t mark.

Require all nine marks:

- **Count**: At least 100 net windows.
- **Mean**: Net mean strictly positive.
- **Window t**: At least 2.0.
- **Trim**: Mean strictly positive after dropping the three highest net returns.
- **Daily comparison**: Gross inside minus outside daily mean strictly positive and Welch t at least 2.0.
- **Net-profit breadth**: At least 60% of the eleven calendar years have strictly positive mean net windows. The January–October 2026 partial year counts as one calendar year.
- **Post-2019**: Strictly positive mean net window return on windows ending January 2020 or later.
- **Leave one year out**: The mean of all remaining net windows is strictly positive for each of the eleven single-calendar-year omissions. Weight individual windows equally within each calculation.
- **Daily edge breadth**: The inside minus outside gross daily mean is strictly positive within at least 60% of the eleven calendar years (at least seven). This is a within-year sign test by count, not an annual t requirement. Zero or an undefined difference does not count as positive.

Report the full leave-one-year-out table and each year's inside and outside means, sample counts, difference and descriptive Welch t. The positive-net-year test alone is not evidence that the calendar edge spans years.

## Shown only

Show the same three-session TLT window at 5 and 10 basis points a side. At 2 basis points a side, show IEF for the same window, TLT for the last one, two, four and five sessions, TLT by calendar year, and the first three sessions of the next month bought at the preceding month-end close and sold at that third close. The first shown next-month window is February 2016; the last is November 2026. Show calendar 2022 alone for the 2022 bond decline. The uninvested cash comparison is zero. These outputs do not get a separate pass verdict and do not change the rank, cost, or strategy choice.

## Limits and evidence

STATED. The consolidated SIP daily close is a proxy, not the auction print or a verified executable exchange close. It reflects the vendor's trade-condition rules, not a verified primary-venue closing timestamp or core-session-only volume ([Alpaca Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)). The published 0.25% per month is a modeled 10-year Treasury position net of GC repo over 1990 to 2018, not an ETF. The two durations, execution conventions and financing assumptions are not interchangeable ([Hartley and Schwarz](https://kristaschwarz.com/EOM.pdf)). The reported sample t statistics assume conventional independence for their standard errors and are descriptive; this plan does not claim serial-dependence-robust inference. There is no estimated slippage beyond the fixed costs, no taxes, and no cash yield.

STATED. [Alpaca historical bars](https://docs.alpaca.markets/us/reference/stockbars) provide the raw SIP bar route. The action packet comes from dated issuer histories for [iShares TLT](https://www.ishares.com/us/products/239454/ishares-20-year-treasury-bond-etf) and [iShares IEF](https://www.ishares.com/us/products/239456/ishares-710-year-treasury-bond-etf), after separate coverage and source review. The packet and its provenance review are off-repo.

## Authorization

The immutable draft/freeze hash binds this plan, the calendar and the four Python modules. The separate input manifest pins both raw bar files, the mandatory action file, collection metadata and source mode. Require the approved freeze, input manifest and independent action digests, a private input directory, a frozen plan marker and an absent lock/result. Every digest must be a 64-character lowercase hexadecimal string before its file is opened; then verify its bytes before parsing or use. Fully load and validate inputs silently. Refuse malformed or mismatched inputs with fixed codes, leaving the lock unclaimed. The exclusive lock is opened immediately before evaluation and remains consumed if evaluation fails. No scorer may be used to preview real returns or retry after the lock.
