# Replay 21. Cash tenders with odd-lot priority

MEASURED. The rule did not pass: **4 of 6 frozen marks**. It placed 14 trades from 106 eligible filings. The other 92 missed the 1.5% entry discount. The placements averaged +11.80% net, but 14 was below the minimum of 30 and the trade t-statistic of 1.688 was below 2.0.

## What ran

STATED. The [frozen plan](../../research_rig/PREREG_21_odd_lot_tenders.md) looked for U.S.-listed common shares in all-cash issuer tender offers from January 2016 through October 2026. The issuer had to commit in its Offer to Purchase to buying all qualifying shares held by beneficial owners of fewer than 100 shares before prorating other tenders. The filing docket used [SEC EDGAR indexes](https://www.sec.gov/Archives/edgar/full-index/), tender filings, amendments and issuer filings for corporate actions. The review was done before the market pull. Of 112 reviewed candidates, 106 were eligible and six were excluded.

The rule used the first regular U.S. open at least 30 minutes after SEC acceptance. It bought only at a discount of at least 1.5% to the fixed price or Dutch-auction minimum known at that open, using amendments accepted at least 30 minutes before it. The election cutoff was three sessions before expiry before May 28, 2024, and two sessions from then on. Each judged trade started afresh with $500, bought whole shares up to 99, and included the larger of 10 basis points or $0.05 a share on each market fill. The judged election fee was $0. The rule tendered unless a withdrawal or qualifying price cut triggered a market exit. Cash was modeled on the stated holder payment date, or the fifth regular session after expiry where no date was stated. [Alpaca SIP daily bars](https://docs.alpaca.markets/us/reference/stockbars) supplied the raw market opens; adjusted bars were used only to check the tape and historical symbol mapping.

## Frozen marks

All six had to pass. Returns are net per placed trade, equally weighted; no-trades are counted for placement but are not assigned zero returns in the trade mean.

| Mark | Fixed bar | Measured | Verdict |
|---|---|---:|---|
| Placed trades | At least 30 | 14 | Not met |
| Net mean | Above zero | +11.80% | Met |
| Net t | At least 2.0 | 1.688 | Not met |
| Net mean without the best three | Above zero | +3.50% | Met |
| Net median | Above zero | +4.32% | Met |
| Positive filing years | At least 60% of years with three or more trades | 1 of 1 (2021: 3 trades, +4.00% mean) | Met |

MEASURED. Thirteen of 14 trades were positive; all 14 were modeled as completed tenders. The median holding period was 35 calendar days. The largest net return was +101.61% (accession `0001213900-26-063179`, June 1 to July 7, 2026). It accounted for 61.5% of the sum of the 14 trade returns.

## Checks after the run, not judged

MEASURED. The independent recompute agreed with the sealed result with no mismatches. The auditor confirmed from the issuer's Offer to Purchase, final results and subsequent quarterly filing that the best trade reflected a real odd-lot payout, not a data error. The issuer's fixed tender offer was $2.50 per share; it accepted qualifying odd lots in full and prorated other tenders to about 48.6%.

MEASURED. All 92 no-trades failed the 150-basis-point discount filter, none for missing bars. The closest miss was 147.06 basis points. Removing the best trade leaves 13 trades, a +4.8952% mean, t of 4.168, a +4.2069% median and 12 of 13 positive. None of these checks changes the verdict.

## Shown only

| Comparison | Placed | Mean net or ending cash |
|---|---:|---:|
| $50 per processed election | 14 | -8.60% |
| Fixed-price offers at $0 fee | 13 | +12.62% |
| Dutch-auction offers at $0 fee | 1 | +1.23% |
| Excluding ambiguous transmittal form wording | 12 | +13.43% |
| Excluding issuer dividend-release flags | 14 | +11.80% |
| One $500 account at $0 fee, no deposits | 14 | $857.83 |

MEASURED. The simple linear annualized trade mean was +117.45% overall (+125.68% fixed and +10.46% Dutch), calculated by scaling each return by 365 divided by calendar days held. That is not a reinvestment rate. The peak was one holding open. The filing-order account placed the same 14 offers. Its 11 cash-tied skips were evaluated before the discount check in that account view; none removed a judged placement. The $357.83 shown-only increase is about $33 per year spread over the filing window, not an estimate of a typical year's profit. The report produced no trades in the no-priority comparator or the unresolved fallback; this is not evidence that similar offers without priority make nothing.

## Gaps and practical reading

MEASURED. The exclusions included one offer silent on beneficial priority, one with discretionary priority, one with an unverified ordinary-dividend date, and one with insufficient corporate-action coverage. The eligible docket had four transmittal-form wording flags, two signature-date ownership flags and two issuer dividend-release flags. It included 26 derived ordinary ex-dates across 26 offers, and one explicit final price taken from a later filing by the same issuer about the same offer. These are docket counts, not counts of placed trades. The rule also conditions on a matched terminal result by the cutoff; the replay is not a complete forward record of every unresolved filing.

The rule failed its own marks because openings at the required discount were rare: 14 placements in roughly a decade. The per-trade result was good in this sample, but one trade carries most of the mean and the yearly dollars on $500 are small. The fee sensitivity turns the mean negative. A daily opening print does not establish an executable retail fill, and the broker's election timing, acceptance and charges were not verified from live orders. The trade t-statistic is descriptive, and the yearly mark saw only one eligible year. The rule is not advanced. Queue row 85 proposes only a forward pretend-money watch, with no rule change or live order.

## Run record

STATED. At 05:38:10 UTC on November 26, 2026, the first approved acquisition stopped after a shared Alpaca rate limit (HTTP 429). No bar was kept or seen, no bundle was written and no score was attempted. A status-only diagnostic discarded bodies. The [transport-only refreeze](../../research_rig/PREREG_21_odd_lot_tenders.md) added spacing and bounded same-request retries; the filing docket, dates, fields, scoring rules and marks did not change. Before the fresh approved collection, the custodian retained the failed lock as provenance, separate from the new exclusive custody claim.

MEASURED. The saved result records the sole scoring claim at 2026-11-26 05:52:52 UTC, queue 38 and ledger 158; the lead reports no-return validation `P21_VALIDATED` before the claim. The reported score was extracted by script from the sealed off-repo result, not from a new score or a fresh market read. The scored claim is spent. The result, raw inputs and independent comparison remain off-repo.

- First freeze and approval: `aff041e4f7d57bf869663efc7daac1d43cbca572`, `2cb7348`.
- Transport refreeze and final approval: `96672f94b1f1cbd700db27139778fc1cef8951ca`, `e9e68d3e54cf0526ca635a4df3fe63a75e7b67e8`.
- Freeze package SHA-256: `bbfd516047389732d148ae138117bd395fde87739bb2c27ce7a61584a484b966`.
- Bar bundle SHA-256: `1587ffe546bdcc47831705ef80589fda13d1bd9fa80c17eff56664fbd56380d8`.
- Sealed result SHA-256: `8944573c050bdffc3198b56a424cd1283347df840739bbd91e12f9fcd60aab95`.
