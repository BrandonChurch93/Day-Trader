# Replay 26. Treasury month-end, earlier dates

Status FROZEN.

STATED. These dates are inside the source paper's 1990–2018 sample. A pass would replicate the paper's effect on a different instrument and price vendor, not supply fresh evidence for the paper. The fresh historical evidence is 2019–2026 in Replay 25; forward practice would supply fresh evidence under simulated fills and has not been done here. A fail would count against Replay 25 and must be reported as such. See [Hartley and Schwarz](https://kristaschwarz.com/EOM.pdf) and [Replay 25](../docs/research/69_replay_25_treasury_month_end.md).

Queue 45, ledger 163. Apply the [Replay 25 rule](PREREG_25_treasury_month_end.md) without using its results to choose any month, width, or cost. Buy unlevered TLT at the fourth-last session close and sell at the last session close. Hold cash otherwise at zero yield. Judge 2 basis points per side. Use issuer cash distributions by ex-date only while held, excluding the entry date and including the exit date. No taxes, reinvestment or leverage.

## Sessions and inputs

- **Judged months**: August 2002 through December 2015, 161 windows. July 2002 has only two available sessions and no eligible entry, so it has no judged window. The comparator does include the July 31 close-to-close interval. The partial calendar year 2002 counts as one of 14 years. There are 483 inside intervals and 2,897 outside, before fees.
- **Calendar**: Use the dates in the bars, only after they match the pinned XNYS schedule from `exchange-calendars` 4.13.3 exactly, including holiday and exceptional closures. Require 3,381 sessions for each fund from July 30, 2002 through December 31, 2015. Do not infer an extra exchange holiday from an absent bar or fill gaps.
- **Vendor**: Perplexity Finance daily market history (`finance_ohlcv_histories`). The route applies split adjustments but not dividend adjustments. The feed review found no splits for TLT or IEF, so the closes are raw for these two funds. The route caps each pull at 5,000 rows; the fixed two-pull design below includes SIP-checkable dates in each pull and repeats December 2020 on purpose. See `source_26.json` for the pinned provenance and the terms note. No Yahoo automation, alternate source, or adjusted-close field in scoring.
- **Cash**: Use the dated issuer packet SHA-256 `6f1a5cc1117cdd59e5f9a19d881fb4debe059b72eb8241720609e49525ac67b2`. It covers these dates and has 161 unique ex-dates per fund. Require session dates, positive finite amounts, and no splits. Ignore vendor-reported distributions.
- **Overlap before any score**: Compare both funds' vendor closes against the pinned Replay 25 SIP bars on the exact common session dates from January 2016 through October 2026. For each fund, at least 99.5% of the sessions must agree within one cent, inclusive, separately in pull A's overlap, pull B, and the joined series. Print only agreement counts and total sessions. Refuse on a date mismatch, a missing or duplicate bar within a pull, invalid price or volume, or a dated issuer action outside a session. Do not compute an overlap return or retune on the overlap.

## Nine marks

Require all nine, judged on TLT only.

- At least 100 monthly windows.
- Positive mean net window return.
- Window t-statistic at least 2.0.
- Positive mean net window return after dropping the best three.
- Positive mean gross daily return difference inside minus outside, with Welch t at least 2.0.
- At least 60% of years with a positive net window mean.
- Positive mean net window return from January 2009 through December 2015. This replaces Replay 25's later-period test; the statistic is unchanged.
- Positive mean net window return after omitting any single year.
- At least 60% of years with positive inside-minus-outside gross daily difference.

Show the annual and leave-one-year-out tables, 5 and 10 basis points per side, widths of 1, 2, 4 and 5 sessions at 2 basis points per side on the same eligible months, and IEF at the judged width and cost. For the next-month line buy at each eligible month-end close and sell at the third session close of the next month at 2 basis points per side, September 2002 to December 2015 exits. No December 2015 entry on that comparison, because its exit is out of period. No TMF. None of these lines sets a verdict or changes a mark.

## Gate and limits

Record ledger 163 before any real validation or score. Require the clean approved commit and a lead approval file naming the freeze, plus fixed hashes on the plan and every input. Reject any `P26_` environment variable. Validation is silent except for fixed refusal codes or the three overlap counts per fund. It never claims a lock, writes a result, or computes returns. The one-shot command repeats full validation, then claims the exclusive lock immediately before any scoring. Never retry after a claim. No bars or distribution amounts go in the repository.

The score program never calls a market-data service. The feed builder delivers owner-only JSON arrays of daily OHLCV rows in ascending order. The only accepted row fields are `date` (local exchange session `YYYY-MM-DD`), `open`, `high`, `low`, `close` and `volume`. Preserve provider decimal text with no float rounding. Do not include vendor dividends, account information, credentials, alternative closes, or derived fields. The fixed private export directory must contain only:

- `TLT_a.json` and `IEF_a.json`, July 30, 2002 through December 31, 2020 inclusive, 4,640 sessions each. These are the only pulls with any judged early dates.
- `TLT_b.json` and `IEF_b.json`, December 1, 2020 through October 30, 2026 inclusive, 1,486 sessions each. The validator requires the date and preserved decimal close text to agree byte for byte on all 22 duplicate December 2020 sessions, then uses pull A's copy in the joined series. The prescribed duplicates are only between pulls, never within either file.
- `native/` with the four untouched provider CSV exports and `normalize_plan26.py`, the fixed private normalizer. The auditor reproduces normalized byte hashes from the native pulls before the freeze, without producing a return.
- `manifest.json` naming the route and for each fund and pull the staged hash, original export hash, pull time, row count, endpoints, and mechanical normalization. Freeze the manifest and normalizer hashes before validation. The validator rechecks these hashes and both sets of input files. It does not execute the normalizer or verify the provider's internal pipeline. Use exact rational arithmetic for the inclusive cent boundary.

The dated issuer cash packet lives in its separate private directory and is pinned by its own SHA-256. The Plan 25 SIP reference is fixed by its saved input-manifest SHA-256. For each fund the required matches are 1,253 of 1,259 on pull A's overlap, 1,479 of 1,486 on pull B, and 2,710 of 2,723 on the joined overlap. The overlap rows never enter a strategy return.

## Limits

STATED by the lead agent. The route is a built-in licensed data tool of this workspace, used for the owner's private research. Files stay off repo and are not redistributed. UNKNOWN. Explicit retention terms for this route were not found.

The vendor close is a price proxy, not proof of an auction fill. Fixed costs do not establish execution at either close. The t-statistics are descriptive and do not adjust for dependence or testing many ideas. High agreement after 2015 is required but does not prove data quality before 2016.
