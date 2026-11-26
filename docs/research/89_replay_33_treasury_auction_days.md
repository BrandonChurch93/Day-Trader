# Replay 33: Treasury auction days in IEF and TLT

**MEASURED: Did not pass.** The sole scored run cleared 3 of 11 frozen marks, all for placement. Buying IEF on 10-year auction dates and TLT on 30-year auction dates at the fixed afternoon clock returned −1.457 basis points (bp) net per placed auction trade (t = −0.597). The non-auction controls did slightly better at +0.791 bp; within the 257 complete pairs, auctions lagged by 2.462 bp (t = −0.868). This replay found no net intraday rise at these clocks and provides no basis to advance the rule.

## What ran and why it was refrozen

The [preregistration](../../research_rig/PREREG_33_treasury_auctions.md) fixed 260 nominal 10- and 30-year auctions from January 2016 through October 2026, one same-fund control per auction, and whole-share buys and sells using the first qualifying SIP ask and bid within 15 seconds of 13:10 and 15:59 ET, respectively. Each fund had its own settled $250 sleeve. Returns were equally weighted across placed trades, not compounded; minute trade bars were diagnostic only.

The first freeze (`359beb47fd9082857ccc5e66b01759bb458fb538`) admitted sole `R` only. Its no-return validation placed about half of the registered trades; the exact validation counts were not saved. The lead's earlier unsaved figure of 134 of 260 matches the control count in the sealed sole-`R` row but is not confirmed as a first-freeze auction count. A condition-only inventory showed that the vendor field was unknown (`?`) on most older quotes before the 2021 transition, with some `R` rows in 2018 and a mixture in 2021. No scored run took place under that freeze, and no returns had been computed or seen. On the same ledger row and the same input manifest, the independently audited second freeze (`10cc743bc4e1ad7065a852f28c21b6a04466117b`) admitted sole `?` as well as sole `R`, without changing the bid, ask, size, order, or time checks. It added a separate, non-judging sole-`R` result. The checkable figures in that sealed row are 132 of 260 auctions, 134 of 260 controls, and 132 complete pairs.

Under the second freeze, no-return validation placed 260 of 260 auctions and 257 of 260 controls, with 257 complete pairs and zero input refusals. The lead claimed and ran the sole authorized score at 2026-11-26 05:23:51 UTC, approval `8314305aa91290b26b5d479851acc89c0c388aff`. All measured returns and their aggregates below are from the sealed off-repo result, SHA-256 `e54fd1f46ee3db7f3191b16a88331a98abc3e364c48115c376ba552fb70c02dd`. The scored claim is spent.

## Frozen marks

| Mark | Fixed bar | MEASURED | Verdict |
|---|---|---|---|
| Placed count | At least 200 overall and at least 100 in each fund | 260 overall; 130 IEF and 130 TLT | Met |
| Placed share | At least 95% (247 of 260) | 260 of 260 (100%) | Met |
| Net mean | Strictly positive equal-trade-weighted auction mean | −1.457 bp | Not met |
| Net t | At least 2.0, one-sample trade t | −0.597 | Not met |
| Trim | Strictly positive auction mean without the best three trades | −2.552 bp, 257 trades, t = −1.072 | Not met |
| After-paper sample | At least 40 registered after July 31, 2024 and positive placed-trade mean | 54 registered and placed, −0.740 bp | Not met |
| Calendar-year breadth | At least 7 of 11 positive years, including partial 2026 | 6 of 11 | Not met |
| Paired comparison | Strictly positive auction-minus-control mean and paired t of at least 2.0 | −2.462 bp, paired t = −0.868 | Not met |
| Paired completeness | At least 95% (247 of 260), no rematching | 257 of 260 (98.846%) | Met |
| Maturity breadth | Positive net mean in both funds | IEF +0.743 bp; TLT −3.657 bp | Not met |
| Leave one year out | Strictly positive mean after every individual year is omitted | 0 of 11; range −2.225 to −0.256 bp | Not met |

## MEASURED: Returns and spreads

| Series | Trades or complete pairs | Mean (bp) | Median (bp) | Sample SD (bp) | t |
|---|---:|---:|---:|---:|---:|
| Auctions | 260 | −1.457 | +0.929 | 39.335 | −0.597 |
| Same-fund controls | 257 | +0.791 | −0.986 | 22.944 | +0.553 |
| Auction minus its own control | 257 | −2.462 | +0.011 | 45.457 | −0.868 |

| Series | Mean entry half-spread (bp) | Mean exit half-spread (bp) | Mean sum (bp) | Noncompounded net P&L |
|---|---:|---:|---:|---:|
| Auctions | 0.477 | 0.463 | 0.940 | −$9.59 |
| Controls | 0.464 | 0.462 | 0.926 | +$2.01 |

The spread is already paid by using the ask and bid; it is not charged a second time. Modeled commission, SEC, TAF and CAT charges were zero in the baseline under the pinned retail fee convention. Auction endpoints included 3 locked entries and 1 locked exit; controls had 1 of each. Three auction start-minute bars and five control start-minute bars were absent without preventing placement where qualifying quotes existed.

All three incomplete pairs lacked a control entry quote: TLT control 2017-04-05 (auction 2017-04-12); IEF control 2018-07-18 (auction 2018-07-11); and IEF control 2018-08-01 (auction 2018-08-08). Without a bought holding, exit size was unassessed on those controls. None was rematched, and all three remain in the completeness denominator.

## MEASURED: Funds, years and later dates

| Fund or period | Placed auctions | Placed controls | Complete pairs | Auction mean (bp) | Auction t | Control mean (bp) | Paired mean (bp) | Paired t |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| IEF, nominal 10-year | 130 | 128 | 128 | +0.743 | +0.543 | +1.242 | −0.533 | −0.283 |
| TLT, nominal 30-year | 130 | 129 | 129 | −3.657 | −0.780 | +0.343 | −4.376 | −0.820 |
| Strictly after July 31, 2024 | 54 | 54 | 54 | −0.740 | −0.181 | −3.907 | +3.167 | +0.697 |
| April–October 2026, descriptive only | 14 | 14 | 14 | −1.117 | −0.121 | −2.695 | +1.578 | +0.139 |

After the paper's sample, auctions fell slightly while their controls fell more. The positive matched gap in those 54 dates is not a positive auction return, and the descriptive April–October 2026 slice is not a verified post-revision subset.

| Auction year | Placed auctions | Complete pairs | All auction mean (bp) | Control mean (bp) | Paired mean (bp) | Paired t | IEF auction / paired (bp) | TLT auction / paired (bp) | Mean omitting year (bp) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2016 | 24 | 24 | +0.243 | +2.503 | −2.260 | −0.383 | +3.016 / +4.202 | −2.529 / −8.722 | −1.630 |
| 2017 | 24 | 23 | +0.388 | +1.449 | −2.995 | −0.489 | −2.730 / −2.069 | +3.506 / −4.006 | −1.644 |
| 2018 | 24 | 22 | +1.264 | −9.100 | +10.213 | +2.255 | +2.777 / +3.380 | −0.248 / +15.907 | −1.733 |
| 2019 | 24 | 24 | +6.095 | +4.660 | +1.435 | +0.214 | −2.241 / −6.775 | +14.432 / +9.646 | −2.225 |
| 2020 | 24 | 24 | −13.260 | +1.615 | −14.875 | −0.734 | −1.059 / +4.150 | −25.462 / −33.901 | −0.256 |
| 2021 | 24 | 24 | +5.120 | +0.169 | +4.951 | +0.559 | +0.760 / −2.037 | +9.480 / +11.938 | −2.125 |
| 2022 | 24 | 24 | −8.015 | −1.262 | −6.753 | −0.604 | −3.500 / +2.038 | −12.530 / −15.544 | −0.790 |
| 2023 | 24 | 24 | −6.073 | +7.958 | −14.031 | −1.815 | +11.380 / −0.514 | −23.526 / −27.548 | −0.987 |
| 2024 | 24 | 24 | +1.061 | +6.478 | −5.417 | −0.798 | +0.501 / −8.294 | +1.621 / −2.539 | −1.713 |
| 2025 | 24 | 24 | −1.315 | −5.349 | +4.034 | +0.647 | +3.769 / +4.542 | −6.399 / +3.526 | −1.471 |
| Jan–Oct 2026 | 20 | 20 | −1.546 | −1.621 | +0.074 | +0.009 | −5.544 / −4.494 | +2.451 / +4.643 | −1.449 |

## MEASURED: Shown only

| Sensitivity | Placed auctions / controls | Complete pairs | Auction mean (bp) | Auction t | Control mean (bp) | Paired mean (bp) | Paired t |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sole `R` at both endpoints, reselecting in the fixed windows | 132 / 134 | 132 | −2.124 | −0.775 | +0.550 | −2.708 | −0.763 |
| Full historical SEC and FINRA TAF fees, no exemptions or rounding | 260 / 257 | 257 | −1.634 | −0.670 | +0.615 | −2.464 | −0.869 |
| Exclude pairs with an FOMC decision date on either leg | 237 / 235 | 235 | −1.724 | −0.651 | +0.184 | −2.143 | −0.719 |
| Additional 1 bp adverse on each side, fixed size | 260 / 257 | 257 | −3.456 | −1.417 | −1.209 | −2.461 | −0.868 |
| Additional 2 bp adverse on each side, fixed size | 260 / 257 | 257 | −5.455 | −2.237 | −3.209 | −2.461 | −0.868 |

The sole-`R` row uses the same 260 registered auctions and 260 fixed control dates, but independently reselects both endpoints under the strict flag. It is not a filter on the baseline fills and it does not affect the verdict. With exemptions removed, mean auction fees were $0.003258 SEC and $0.000251 TAF per placed auction; CAT is unchanged.

| ISO-week diagnostic | Weeks | Equal-week mean (bp) | Trade-weighted cluster SE (bp) | Cluster t |
|---|---:|---:|---:|---:|
| Auctions | 130 | −1.457 | 2.574 | −0.566 |
| Controls | 143 | +0.444 | 1.519 | +0.521 |
| Paired differences, grouped by auction week | 130 | −2.237 | 2.966 | −0.830 |

## Interpretation and limits

[New York Fed Staff Report 1188, Intraday Price Pressure and Order Flow Around U.S. Treasury Auctions](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr1188.pdf) studies cash Treasury yield changes and midpoint returns for on-the-run securities, with a 180-minute measurement starting one minute after actual results were released, over June 1991 through July 2024. This replay instead bought two listed fund proxies at the fixed 13:10 ET clock, which does not establish that results had posted, and sold before the equity close. Its full January 2016–October 2026 sample is neither the paper's full sample nor wholly out of sample. The failed rule is a test of the quoted ETF trade, not a refutation of the paper's Treasury-market evidence.

The vendor's `?` flag is unknown, not verified regular. Displayed size does not establish actual routing, protected odd-lot liquidity or execution, and an absent exit quote is a retrospective coverage fact, not something knowable at entry. The fee model applies current Robinhood exemptions and rounding historically rather than using broker receipts. These are separate fixed-notional trades, not a compounded account path. ISO-week, trade and paired t statistics are descriptive and do not establish causality.
