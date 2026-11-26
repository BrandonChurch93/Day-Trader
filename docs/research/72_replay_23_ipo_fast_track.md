# Replay 23. Early index buying after large US listings

MEASURED. Run once at 2026-11-26 04:02:32 UTC. Result: did not pass, 7 of 8 marks at 10 bps a side. 218 trades, mean net +2.64%, t 2.66. The failed mark is the recent one: -1.42% on the 42 trades priced from 2023-01-01.

STATED. The [frozen plan](../../research_rig/PREREG_23_ipo_fast_track.md) (ledger 160, queue 37) buys a large new US listing at its first day's close and sells at the fifth session's close. A listing is judged when the offer price times the prospectus's own after-offering share total is at least `judged_ratio_min` times the latest published CRSP 98% breakpoint. The idea is that index funds must buy such a listing within days. The published estimate came from a sample ending in 2022 ([Murray and Sammon, 2026](https://academic.oup.com/raps/article/16/2/163/8416725)).

## In plain words

- It worked on paper from 2017 to 2021: 172 trades with a mean of +3.76%, a positive mean in each of those 5 years. MEASURED.
- It has not worked since 2022: 46 trades with a mean of -1.52%; 2 of 5 years from 2022 had a positive mean, and those were small. MEASURED.
- The full-sample marks held only because of the busy early years; 2021 alone gave 79 of the 218 trades. MEASURED.
- The recent-years mark (mean above 0 from `recent_from`) was fixed before any price was read, because the published sample ends in 2022. It was put there to catch this case, an effect that has faded since it was written up, and it did. STATED in the plan, MEASURED here.
- The years from 2022 are thin (46 trades over 5 years), so they cannot show the effect is gone for good either. What they show is that it has not been there to collect.
- Nothing here is a reason to trade this rule.

## Eight judged marks

| Mark | Measured | Held |
| --- | ---: | --- |
| At least `min_trades` trades | 218 | yes |
| Mean net return above 0 | +2.64% | yes |
| t of the mean at least `min_t_stat` | 2.66 | yes |
| Mean above 0 without the best `drop_best` trades | +1.69% | yes |
| Median above 0 | +2.22% | yes |
| Positive mean in at least `min_year_share_pct`% of years with `min_year_trades` or more trades | 7 of 10 (70%) | yes |
| Mean minus SPY above 0 with t at least `min_t_stat` | +2.48%, t 2.51 | yes |
| Mean above 0 on events priced from `recent_from` | -1.42% on 42 | no |

## Calendar years

MEASURED. Judged trades at the judged cost. Years are the first trading day's calendar year.

| Year | Trades | Mean net | Median net |
| --- | ---: | ---: | ---: |
| 2017 | 15 | +1.61% | +2.81% |
| 2018 | 20 | +3.25% | +3.02% |
| 2019 | 25 | +6.24% | +4.37% |
| 2020 | 33 | +2.15% | +4.62% |
| 2021 | 79 | +4.18% | +2.11% |
| 2022 | 4 | -2.57% | -2.66% |
| 2023 | 5 | -8.51% | -2.61% |
| 2024 | 11 | +1.78% | +1.54% |
| 2025 | 12 | +0.84% | -5.68% |
| 2026 | 14 | -3.33% | -3.75% |

## Shown only, not judged

MEASURED. None of these was used to pick the judged result.

| Cell | Trades | Mean net | Median net | t |
| --- | ---: | ---: | ---: | ---: |
| Buy at the second day's open instead | 218 | +2.46% | +1.85% | 2.57 |
| Cost `shown_bps` a side | 218 | +2.34% | +1.91% | 2.36 |
| Cost `no_auction_bps` a side (no closing-auction order) | 218 | +1.83% | +1.41% | 1.85 |
| Without listings above `mega_usd` | 203 | +2.21% | +2.43% | 2.54 |
| First close at or above the offer price | 180 | +2.81% | +2.88% | 2.90 |
| First close below the offer price | 38 | +1.85% | -0.45% | 0.54 |
| Listings at 1.0 to 1.5 times the cut-off | 85 | +1.85% | +0.38% | 1.30 |
| Listings at 0.67 to 1.5 times the cut-off | 176 | +1.93% | +0.49% | 1.75 |

Every judged trade left at the fifth session close (218 of 218).

## Why 218 and not 228

MEASURED. 231 judged listings were on the list. 3 were left out before the run because their share count or security type could not be confirmed (2 shares unverified, 1 not common stock), which left the 228 the plan expected. The date checks fixed in the plan then left out 10 more, all before the lock:

- 8 with bars more than `prior_bar_gap_bdays` sessions before the filing date (`prior_bars`): ADT, BV, CART, LINE, MBLY, SAIL, SWI, VG. The plan reads these as a reused symbol or another security, so the first day cannot be told apart from older trading. Which of the two applies to each name was not checked. 4 of them were priced from `recent_from`, which is why the recent mark has 42 trades and not 46.
- 2 whose first bar was not a real trade (`entry_not_real_bar`): DNB, INST.

No trade dropped after the lock.

## Limits

- Calibration, STATED in the plan and MEASURED on invented paths: with no edge, 1 of 20 worlds passed all eight marks, a false pass; with a 2% edge a trade only 6 of 20 passed, and with 4% 18 of 20. So this test can miss a small real edge, and a pass would not have proved one.
- A t of 2.66 on the full sample uses the usual standard error. It does not adjust for the many ideas this project has tested or for trades that bunch in hot years.
- At `no_auction_bps` a side, the cost for a buyer who cannot use a closing-auction order, the full-sample mean falls to +1.83% with t 1.85.
- The size test is a stand-in for CRSP's own share counts and its US, PFIC and float screens. 424B1 listings and direct listings are missing.
- The daily bar close is the last consolidated trade, not the closing auction print.
- Raw bars: a split or dividend inside the five sessions is not adjusted. SPY is raw too.
- The common-shares check reads the 424B4 cover text with fixed patterns; it is not a CUSIP match.

## Run record

MEASURED. Freeze commit `4c8fe2c759f88e9c583662a1b4256c10fe43a5a1`, approval commit `a087351cbb483a95bb8beaa3ecda354f63a8e31b`, one collection and one scored run. This page was generated by `tools/report_saved_23.py` from the saved outputs only. Bars, offer prices and breakpoints stay off repo.

- Freeze record SHA-256 `57e12dfe68f9222888e6a7a416d43c954a26b3c4b81d673977d31235bb7dc5c6`
- Saved result SHA-256 `4834554deb1864e7b1a3d2f9794d4d3bb89d33e3ea8854a01cdd199e7e6dcae1`
- Frozen event list SHA-256 `a4ef7fe749d973091fdfec13e0ba1b392a9cff94e548a03298a644008e180f76`
- Calibration SHA-256 `71f9be0632a8b999a92bccc2bc6e22b3bf1bcc62baff046b7d83b1b86bb89351`
