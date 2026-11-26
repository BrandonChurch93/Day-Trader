# Replay 48. Muni closed-end funds after year-end tax-loss selling

MEASURED. Passed, **7 of 7 frozen marks**, in one scored run claimed 2026-11-26 07:11:49 UTC. Over 10 yearly turns (December 2016 to January 2026) the worst 5 municipal closed-end funds by price return up to late December averaged +1.39% net from the last December close to the last January close. MUB averaged +0.09% on the same clock and the equal-weight roster of all eligible funds +0.59%. The portfolio was above zero in 8 of 10 years and ahead of MUB in 8 of 10.

STATED. A pass here is one test of a published effect on ten data points. It is a reason to watch the December 2026 turn with pretend money (`practice/traders/E04_muni_cef_january_watch.md`), not clearance to trade. The pre-run synthetic world with a muni-wide year-end rally and no loser effect passed 20.65% of the time, so this pass cannot by itself separate the two.

## The rule

STATED, from the [frozen plan](../../research_rig/PREREG_48_muni_cef_tax_loss.md). Each turn uses the muni closed-end funds on the SEC closed-end fund roster for that year. A fund is eligible if it has a raw SIP daily bar with nonzero volume on every session from the first January close through entry, no split in that span, and one whole share fits in a $100 sleeve after the entry cost. At the second-to-last December close, rank eligible funds by price return since the first January close, lowest first. Buy the worst 5, $100 each in whole shares, at the last December close. Sell at the last January close. Dated distributions are credited in cash, not reinvested. Leftover cash earns nothing.

STATED. Cost per side is half the measured closing spread plus 5 bp, from SIP quotes between 15:54:00 and 15:59:00 New York time, each quote valid 60 seconds and at least 180 seconds of cover. If cover is short, a 50 bp half-spread proxy is used for that side. MUB is one $500 whole-share sleeve on the same clock and rules. The roster equal weight is the mean of $100 sleeves over every eligible fund that turn.

## Frozen marks

MEASURED. All seven had to pass at the judged cost. Zero is not positive.

| Mark | Bar | Measured | Verdict |
| --- | --- | ---: | --- |
| Turns | all 10 turns scored | 10 of 10 | met |
| Net mean | yearly portfolio mean above zero | +1.39% | met |
| Positive years | at least 8 of 10 above zero | 8 of 10 | met |
| Against MUB, mean | mean of portfolio minus MUB above zero | +1.30% | met |
| Against MUB, years | at least 7 of 10 years ahead of MUB | 8 of 10 | met |
| Without best year | mean above zero after removing the best 1 | +0.66% | met |
| Loser effect | portfolio minus roster equal weight above zero, with documented cash and price only | +0.80% with cash, +0.79% price only | met |

## The ten turns

MEASURED. Net returns at the judged cost; the turn is the December year. Cash not documented counts held funds whose in-window distribution could not be documented and was credited zero. Proxy sides counts entry or exit sides of held funds priced at the 50 bp proxy. Fund names are kept off this page.

| Turn | Portfolio | MUB | Roster equal weight | Eligible | Held, cash not documented | Held proxy sides |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2016 | +0.62% | +0.21% | +2.26% | 132 | 5 of 5 | 0 |
| 2017 | -4.48% | -1.11% | -4.16% | 137 | 2 of 5 | 4 |
| 2018 | +4.91% | +0.23% | +4.17% | 129 | 1 of 5 | 3 |
| 2019 | +1.45% | +1.41% | +1.67% | 123 | 5 of 5 | 8 |
| 2020 | +2.12% | +0.21% | +0.34% | 123 | 0 of 5 | 3 |
| 2021 | -5.06% | -2.34% | -7.64% | 99 | 1 of 5 | 3 |
| 2022 | +8.00% | +1.99% | +5.00% | 101 | 1 of 5 | 2 |
| 2023 | +1.01% | -0.05% | +0.86% | 103 | 0 of 5 | 0 |
| 2024 | +2.56% | -0.10% | +1.83% | 103 | 1 of 5 | 0 |
| 2025 | +2.77% | +0.50% | +1.61% | 91 | 0 of 5 | 0 |
| Mean | +1.39% | +0.09% | +0.59% |  | 16 of 50 | 23 |

MEASURED. The best turn was 2022 at +8.00%; without it the mean is +0.66%. Held funds had no exit bar in 0 fund-turns; eligible funds in 2.

## Against the roster, price only

MEASURED. The loser mark compares the five losers with every eligible fund in the same turn, so a muni-wide January move cancels out. It is shown twice: with documented cash, and with cash set to zero for every fund on both sides.

| Turn | Portfolio minus roster, with cash | Portfolio minus roster, price only |
| --- | ---: | ---: |
| 2016 | -1.64% | -1.44% |
| 2017 | -0.32% | -0.39% |
| 2018 | +0.75% | +0.62% |
| 2019 | -0.22% | -0.09% |
| 2020 | +1.78% | +1.63% |
| 2021 | +2.58% | +2.64% |
| 2022 | +3.00% | +2.91% |
| 2023 | +0.15% | +0.11% |
| 2024 | +0.74% | +0.83% |
| 2025 | +1.16% | +1.06% |
| Mean | +0.80% | +0.79% |
| Years above zero | 7 of 10 | 7 of 10 |

## Shown only

MEASURED, shown only. These cannot replace or rescue a mark. The fifth-session exit sells at the close of the fifth January session instead of the last (the five-day window in Starks, Yong and Zheng). The zero-cost line uses the same share counts with no spread or fee.

| Line | Portfolio mean | MUB mean | Minus MUB | Minus roster, with cash | Minus roster, price only | Positive years | Years ahead of MUB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Judged: last January close | +1.39% | +0.09% | +1.30% | +0.80% | +0.79% | 8 of 10 | 8 of 10 |
| Shown only: fifth January session | +0.80% | +0.02% | +0.78% | +0.38% | +0.38% | 9 of 10 | 7 of 10 |
| Shown only: zero cost | +1.90% | +0.19% | +1.71% | +0.80% | +0.80% | 8 of 10 | 8 of 10 |

MEASURED. Costs took 0.51 percentage points a year off the portfolio mean, the gap between the zero-cost and judged lines.

## What ten turns could show

MEASURED on synthetic data before the run (`research_rig/CALIBRATION_48.json`, 10,000 trials, seed 48001). With no edge at all the seven marks pass 4.39% of the time, under the 10% ceiling. With a muni-wide year-end premium and no loser excess they pass 20.65% of the time. A true loser excess of 1%, 2% or 3% a year passes 45.14%, 66.14% or 82.01% of the time. The synthetic spreads are stated assumptions, not estimates.

## In dollars

MEASURED. On a $500 sleeve, once a year, the mean net result was +$6.96 a year, $6.49 more than MUB and $3.99 more than the equal-weight roster. The worst turn was -$25.29 and the best +$40.02. Before taxes. STATED. This is one trade a year; it is not a way to grow a small account quickly.

## Gaps

- STATED, from the custodian's off-packet coverage table as reported by the lead agent: 470 roster fund-turns had a distribution that could not be documented and were credited zero cash. MEASURED: 372 of 1,141 eligible fund-turns and 16 of 50 held fund-turns carried an empty cash list. Zero credit can only lower a fund's return, so it pushes the portfolio's mean and its lead over MUB down, not up. Against the roster it can push either way, which is why the loser mark also had to pass price only.
- STATED. Split evidence is vendor-derived: the vendor's corporate-action pages, raw against split-adjusted closes from the same vendor, and a 1.4x jump backstop, with any nonzero case resolved by the reviewer. None was found. A split the vendor missed in both series would not be caught unless it broke the backstop.
- STATED, from the lead agent: the NXC/NXN merger falls in turn 2025. MEASURED: in that turn 2 eligible funds had no bar at the exit and were valued at their last close under the plan's rule; none was held.
- MEASURED. 23 held entry or exit sides used the 50 bp proxy because quotes did not cover the window, so their cost is assumed, not measured.
- STATED, from the lead agent: before the run the distribution reviewer glimpsed 2 pages showing closing prices. The ranking and fills come only from the sealed packet.
- STATED. MUB is the yardstick. It holds investment-grade muni bonds without leverage, while the funds are leveraged and trade at moving discounts, so beating MUB is partly the funds' extra risk. The roster comparison is the cleaner test of the loser effect.
- STATED. One trade a year, so 10 data points. Years are not independent draws, and the same funds may be picked in several years.
- STATED. The funds are thin. A $100 order may not get the close, and the size this could carry is small. UNKNOWN: how much money it would take to move the price.
- STATED. This is a single test of a published effect: [Starks, Yong and Zheng, Journal of Finance 61(6), 2006](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2006.01011.x), with recent evidence from [Carrion and Zhang, Journal of Financial Research 47(4), 2024](https://onlinelibrary.wiley.com/doi/10.1111/jfir.12384). It is not a replication of their regressions.

## Independent recompute

MEASURED, from the recompute note (`/home/user/workspace/rig/plan48_review/recompute_48.md`, off repo, SHA-256 `6a699f08fb83fcefb978c5b344cc38a80a47294c8c4e0073c1cab019a0ef7492`). A helper who did not read the scoring code matched 50 of 50 picks in order, 10 of 10 portfolio returns, 10 of 10 MUB returns and 7 of 7 marks. One difference: in turn 2017 the roster equal weight differs by 0.59 bp (0.059 bp in the ten-year mean of each roster comparison), from one eligible fund that was not picked, on its entry cost. The engine treats a locked quote (bid equal to ask) as ending the valid quote before it and adding no valid time, under the plan 36 convention the plan cites. That left 139 valid seconds, under the 180-second floor, so the proxy applied; the recompute counted locked time and got 199. STATED: the plan text alone is ambiguous there; the code auditor confirmed the engine follows the cited convention. It changes no pick, return of the portfolio or MUB, or mark.

## Run record

MEASURED. The saved result records the claim at 2026-11-26 07:11:49 UTC for queue 86 and ledger 182. STATED. The lead agent reports one validation and one scored run. This page reads the saved result only; there was no rerun and the lock stays.

- Approval commit `4b0738b6a52d40e2352c9442c98101112919f9d1`
- Strategy freeze commit `b08c8e0f2abc2bac3e202b004ffee961c1f04fd1`
- Saved result SHA-256 `d303cc1b980c4bbedf92a53379e45150d3424aed44fbd97dfbbacbd4c314d1ba`
- Freeze manifest SHA-256 `254f87ee0e0d46e361b58500001f2268064cda4cb53ef8a46931bf683de743a5`
- Input manifest SHA-256 `5e160e3370baeb27f9cfb15208868bd0ffd7bc100f1dc2d9338b5c50dd96b250`
- Roster SHA-256 `8abe53b7cd1fd54b1a218e0ed0a7a0ed66319418683b958cfec7a5b20168a2f5`
- Distributions SHA-256 `12885c559698eae4fb7af0e00ad97ea916b0ba1fd97d55d9a2fde7f2db435139`
