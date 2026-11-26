# Replay 46. CFTC-certified altcoin futures

MEASURED. Neither leg passed. The pre-launch spot long lost money at the frozen cost. The post-launch short proxy was positive, but its advantage over matched BTC was too small relative to the variation across posting dates to clear the frozen t mark.

- A, before launch: did not pass, 3 of 6 marks. 43 events on 15 posting dates, -6.5393% mean net, +0.5643% paired versus BTC (t 0.174), -3.7069% paired without the best posting dates.
- B, after launch: did not pass, 5 of 6 marks. 110 events on 31 posting dates, +1.2790% mean net, +0.5574% paired versus BTC (t 0.572), +0.3032% paired without the best posting dates.

## What was tested

STATED. The [frozen plan](../../research_rig/PREREG_46_cftc_altcoin_futures.md) used the CFTC archive date plus 2 calendar days at midnight UTC as the posting proxy, not an observed release time. A bought the spot open on that day and sold at the last UTC daily close before the stated launch date; it needed at least 5 elapsed days to the launch boundary. B used the later of the first midnight after the stated launch date or the archive-date proxy, then held for 7 days. Both benchmark positions used BTC-USD in the same direction on the same price fields and dates.

## Frozen marks

MEASURED. Paired means the altcoin net return minus the matched BTC net return. Events have equal weight; the t-statistic groups events by CFTC archive date. All marks were required for each leg.

| Required mark | A result | B result |
| --- | ---: | ---: |
| At least 30 placed events | 43 (met) | 110 (met) |
| At least 12 posting dates for A and 25 for B | 15 (met) | 31 (met) |
| Mean net above zero before subtracting BTC | -6.5393% (not met) | +1.2790% (met) |
| Mean paired net above zero | +0.5643% (met) | +0.5574% (met) |
| Paired date-clustered t at least 2.0 | 0.174 (not met) | 0.572 (not met) |
| Mean paired net above zero without best 3 posting dates | -3.7069% (not met) | +0.3032% (met) |

## Net returns and counts

MEASURED. These are per-event means, not compounded portfolio returns. The trim removes every event on the best posting dates by mean paired return.

| Leg or view | Events | Posting dates | Mean net | Net t | Mean paired vs BTC | Paired t |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A, full judged sample | 43 | 15 | -6.5393% | -1.456 | +0.5643% | 0.174 |
| A, paired without best 3 posting dates | 36 | 12 | not judged | not judged | -3.7069% | -1.887 |
| B, full judged sample | 110 | 31 | +1.2790% | 1.029 | +0.5574% | 0.572 |
| B, paired without best 3 posting dates | 107 | 28 | not judged | not judged | +0.3032% | 0.304 |

## Skips

MEASURED. Calendar exclusions are counted before price checks. The planned count is the placed count plus the input-gap exclusions.

| Leg | Planned | Placed | Calendar exclusions by reason | Input gaps by reason |
| --- | ---: | ---: | --- | --- |
| A | 43 | 43 | too little notice (76); unknown trade date (3) | none |
| B | 113 | 110 | window extended past the cutoff (3); overlapping same-coin window (3); unknown trade date (3) | altcoin spot candle gap (3) |

## Shown only

MEASURED. These lines do not alter the verdicts. Earliest in the docket means the earliest roster record for a coin, not the first listing ever.

| Leg or view | Events | Posting dates | Mean net | Net t | Mean paired vs BTC | Paired t |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A, earliest in this docket (shown only) | 20 | 7 | -2.8306% | -0.305 | +7.2507% | 1.399 |
| A, 120 bp fee per side (shown only) | 43 | 15 | -7.7101% | -1.728 | +0.5581% | 0.173 |
| B, earliest in this docket (shown only) | 29 | 15 | +2.2650% | 1.236 | +2.4927% | 1.816 |
| B, without negative-notice events (shown only) | 110 | 31 | +1.2790% | 1.029 | +0.5574% | 0.572 |

## Costs and what the replay cannot show

- STATED. A charged 60 bp taker fee and 25 bp adverse half-spread per side on altcoins, and the same fee plus 2 bp half-spread for BTC. The fee is the frozen [Coinbase Exchange schedule](https://help.coinbase.com/en/exchange/trading-and-funding/exchange-fees) assumption, not an observed fee paid on an order.
- STATED. B charged 12 bp fee and 15 bp adverse half-spread per side on altcoins, plus 3 bp a day in adverse funding (21 bp total). BTC faced the same fee and funding with 2 bp half-spread. The funding assumption cancels in the paired mean, not in the outright net mean. None of these B costs is a measured venue fill.
- STATED. The prices are Coinbase Exchange USD spot daily bars. The first or last trade of a UTC bucket is a price reference, not an order fill. B is a spot-reference short proxy, not a short we could execute.
- UNKNOWN. Actual fill prices at the chosen clocks, realized funding, futures basis, venue fees, account access, and executable depth are not established. The replay does not price the listed futures contracts.
- MEASURED. TRX-USD was absent from the Coinbase Exchange product-list captures on [2026-05-21](https://web.archive.org/web/20260521161041/https://api.exchange.coinbase.com/products), [2026-08-27](https://web.archive.org/web/20260827123223/https://api.exchange.coinbase.com/products), [2026-09-14](https://web.archive.org/web/20260914031920/https://api.exchange.coinbase.com/products/). STATED. Under the lead agent's ruling, the capture evidence was used to infer absence on 24 requested dates. Those grid dates were not directly captured. A listing that opened and was removed entirely between captures is UNKNOWN. The date-level gap count is not the count of skipped trades.

## Record

- MEASURED. The lead agent claimed the one allowed run at 2026-11-26 06:51:58 UTC, queue 83, ledger 179 and 181. Approval commit `99dc23b9da20f54f1b616d791b3ed2af8e5f1071`; freeze commit `b1b2fb4f008cdc62571617b9c0f1708f1fece6d0`.
- MEASURED. Saved result SHA-256 `b941fb1a7d3f55d14fff063f8b4918e0ede4ce73d4470b9f0ceec586d9b96edb`; approved input SHA-256 `148fd664da4e1e18c1eeed193c59f50c2fc8e1e83ad7ddac7f19eec2fa8f80c2`. Only aggregates are reproduced here; the saved trade rows and input packet stay off repo.
- MEASURED. An independent recompute, written by a second agent from the frozen plan text, docket and settings without reading the scorer, matched every count, every skip, all 12 marks and all 153 events; the largest per-event difference was under 1e-15. Its comparison file stays off repo (SHA-256 `2e358264f1bc857615e5eae595d3fbae9dc148966bfba3cc3396ca0448b49556`).
- STATED. Neither rule advances; this result is not a trade recommendation.
