# 66. Measurement 15: what a breakout order on stocks in play really paid

Written by `research_rig/report_15.py` from `research_rig/measure_15_summary.json` (sha256 0258d5a8515931ef). The summary was made from the off-repo per-stock-day output of 2026-11-26 02:50 UTC (sha256 40cd349f009de976). Plan: `research_rig/MEASURE_15_breakout_fills.md`, ledger row 156, queue row 23. No return was computed.

## Result

- MEASURED: mean entry slippage 0.0757 of the stop distance (n 978), mean stop-exit slippage 0.1332 (n 840), odd lots left out, all 60 days.
- MEASURED: headline sum 0.2089. The limit fixed before the run is 0.05 (`measure_15_build_max_slip_share_of_stop`). The sum is above it, so by the frozen rule the idea is dropped.
- What it means: the paper sizes each trade by the stop distance and assumes fills at the level. Measured fills gave away about 21% of that risk unit per trade, about a fifth, before any edge.

## Odd lots counted, for comparison

- MEASURED: entry 0.0585 (n 978) plus stop exit 0.2134 (n 846) = 0.2719.
- MEASURED: counting odd lots makes the entry cheaper and the stop exit dearer. Our reading, not tested: an odd lot often prints at the level first, and some odd lots print far through the stop. Both settings are above the limit.

## Counts

- MEASURED: 1,200 stock-days in play on 60 days. No direction (first bar closed at its open): 13. No breakout by 16:00: 209. Breakouts: 978.
- MEASURED, odd lots left out: entry: ok 978; exit: ok 840; exit: stop not reached by 16:00 138.
- MEASURED, odd lots counted: entry: ok 978; exit: ok 846; exit: stop not reached by 16:00 132.
- MEASURED: breakouts with no counted trade through the level within the 5-minute search ('no eligible trade'), odd lots left out: 0.

## Odd lots left out (headline): entry

MEASURED. Price groups use the entry level in dollars. Percentiles use linear interpolation. Positive is worse.

| group | n | cents median | cents mean | cents p90 | bps median | bps mean | bps p90 | share of stop, mean |
|---|---|---|---|---|---|---|---|---|
| all | 978 | 0.00 | 1.40 | 4.00 | 0.00 | 3.25 | 7.50 | 0.076 |
| price 10-20 | 151 | 0.00 | 0.49 | 1.50 | 0.00 | 3.10 | 10.85 | 0.057 |
| price 100+ | 156 | 1.00 | 3.33 | 10.25 | 0.72 | 2.12 | 6.18 | 0.082 |
| price 20-50 | 381 | 0.00 | 0.89 | 2.00 | 0.00 | 2.88 | 7.56 | 0.071 |
| price 5-10 | 62 | 0.00 | 0.91 | 1.00 | 0.00 | 11.42 | 12.49 | 0.046 |
| price 50-100 | 226 | 0.50 | 1.70 | 4.00 | 0.71 | 2.55 | 6.80 | 0.101 |
| price <5 | 2 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.000 |
| year 2016 | 94 | 0.00 | 0.49 | 2.00 | 0.00 | 1.05 | 4.08 | 0.045 |
| year 2017 | 97 | 0.00 | 0.83 | 3.00 | 0.00 | 1.60 | 5.00 | 0.070 |
| year 2018 | 101 | 0.00 | 1.28 | 4.00 | 0.00 | 2.45 | 6.41 | 0.077 |
| year 2019 | 96 | 0.00 | 1.42 | 4.25 | 0.00 | 2.20 | 6.41 | 0.082 |
| year 2020 | 95 | 0.00 | 1.68 | 5.20 | 0.00 | 3.24 | 9.90 | 0.085 |
| year 2021 | 94 | 0.00 | 1.06 | 3.00 | 0.00 | 2.67 | 8.27 | 0.043 |
| year 2022 | 109 | 0.02 | 1.71 | 4.60 | 0.12 | 3.94 | 11.02 | 0.099 |
| year 2023 | 97 | 0.50 | 2.00 | 5.00 | 0.55 | 2.71 | 7.30 | 0.081 |
| year 2024 | 92 | 0.00 | 1.45 | 3.45 | 0.00 | 3.86 | 7.39 | 0.078 |
| year 2025 | 103 | 0.01 | 2.01 | 5.00 | 0.01 | 8.37 | 9.91 | 0.092 |

## Odd lots left out (headline): stop exit

MEASURED. Price groups use the entry level in dollars. Percentiles use linear interpolation. Positive is worse.

| group | n | cents median | cents mean | cents p90 | bps median | bps mean | bps p90 | share of stop, mean |
|---|---|---|---|---|---|---|---|---|
| all | 840 | 0.90 | 2.48 | 5.84 | 2.68 | 5.95 | 12.92 | 0.133 |
| price 10-20 | 129 | 0.63 | 1.16 | 2.52 | 4.29 | 7.52 | 18.33 | 0.140 |
| price 100+ | 141 | 3.21 | 6.19 | 14.72 | 1.74 | 3.45 | 9.43 | 0.123 |
| price 20-50 | 326 | 0.85 | 1.66 | 3.92 | 2.70 | 5.43 | 12.98 | 0.137 |
| price 5-10 | 52 | 0.46 | 1.25 | 1.61 | 6.78 | 16.52 | 20.57 | 0.148 |
| price 50-100 | 190 | 1.04 | 2.33 | 5.44 | 1.51 | 3.39 | 7.44 | 0.119 |
| price <5 | 2 | 6.42 | 6.42 | 8.42 | 136.13 | 136.13 | 176.79 | 0.825 |
| year 2016 | 79 | 0.92 | 2.18 | 4.76 | 2.00 | 4.95 | 10.35 | 0.142 |
| year 2017 | 81 | 0.67 | 1.68 | 4.66 | 1.59 | 4.36 | 7.98 | 0.149 |
| year 2018 | 87 | 0.88 | 1.96 | 5.13 | 2.03 | 4.05 | 9.76 | 0.109 |
| year 2019 | 83 | 0.84 | 2.21 | 5.51 | 3.27 | 5.11 | 10.35 | 0.149 |
| year 2020 | 84 | 0.90 | 2.38 | 6.13 | 3.69 | 6.31 | 12.21 | 0.104 |
| year 2021 | 78 | 0.81 | 2.68 | 5.82 | 3.58 | 11.18 | 13.84 | 0.142 |
| year 2022 | 93 | 0.91 | 2.16 | 4.39 | 2.56 | 6.50 | 12.24 | 0.112 |
| year 2023 | 84 | 1.25 | 3.64 | 9.14 | 2.80 | 6.13 | 14.87 | 0.170 |
| year 2024 | 86 | 1.14 | 3.16 | 8.92 | 2.37 | 5.72 | 13.48 | 0.135 |
| year 2025 | 85 | 0.99 | 2.76 | 6.08 | 3.59 | 5.51 | 13.55 | 0.124 |

## Odd lots counted: entry

MEASURED. Price groups use the entry level in dollars. Percentiles use linear interpolation. Positive is worse.

| group | n | cents median | cents mean | cents p90 | bps median | bps mean | bps p90 | share of stop, mean |
|---|---|---|---|---|---|---|---|---|
| all | 978 | 0.00 | 1.11 | 3.00 | 0.00 | 2.61 | 6.29 | 0.058 |
| price 10-20 | 151 | 0.00 | 0.40 | 1.00 | 0.00 | 2.59 | 8.64 | 0.046 |
| price 100+ | 156 | 0.12 | 2.64 | 8.50 | 0.07 | 1.71 | 5.23 | 0.065 |
| price 20-50 | 381 | 0.00 | 0.71 | 1.99 | 0.00 | 2.23 | 4.99 | 0.055 |
| price 5-10 | 62 | 0.00 | 0.80 | 0.50 | 0.00 | 9.91 | 7.35 | 0.034 |
| price 50-100 | 226 | 0.00 | 1.31 | 4.00 | 0.00 | 1.90 | 6.18 | 0.075 |
| price <5 | 2 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.000 |
| year 2016 | 94 | 0.00 | 0.47 | 2.00 | 0.00 | 1.00 | 3.56 | 0.041 |
| year 2017 | 97 | 0.00 | 0.59 | 2.00 | 0.00 | 1.19 | 3.74 | 0.048 |
| year 2018 | 101 | 0.00 | 1.08 | 3.90 | 0.00 | 1.87 | 5.34 | 0.057 |
| year 2019 | 96 | 0.00 | 0.92 | 2.75 | 0.00 | 1.74 | 5.12 | 0.058 |
| year 2020 | 95 | 0.00 | 1.37 | 3.34 | 0.00 | 2.56 | 7.80 | 0.071 |
| year 2021 | 94 | 0.00 | 0.94 | 3.00 | 0.00 | 2.38 | 7.83 | 0.047 |
| year 2022 | 109 | 0.00 | 1.07 | 2.60 | 0.00 | 2.83 | 7.25 | 0.065 |
| year 2023 | 97 | 0.00 | 1.70 | 3.50 | 0.00 | 1.56 | 4.96 | 0.056 |
| year 2024 | 92 | 0.00 | 1.23 | 2.90 | 0.00 | 3.12 | 6.03 | 0.061 |
| year 2025 | 103 | 0.00 | 1.71 | 3.90 | 0.00 | 7.51 | 9.44 | 0.077 |

## Odd lots counted: stop exit

MEASURED. Price groups use the entry level in dollars. Percentiles use linear interpolation. Positive is worse.

| group | n | cents median | cents mean | cents p90 | bps median | bps mean | bps p90 | share of stop, mean |
|---|---|---|---|---|---|---|---|---|
| all | 846 | 0.88 | 4.56 | 6.67 | 2.54 | 8.31 | 13.76 | 0.213 |
| price 10-20 | 130 | 0.60 | 1.08 | 2.50 | 4.19 | 7.37 | 15.71 | 0.122 |
| price 100+ | 141 | 2.57 | 12.86 | 20.83 | 1.56 | 8.00 | 11.20 | 0.282 |
| price 20-50 | 328 | 0.80 | 2.21 | 4.83 | 2.59 | 7.03 | 13.99 | 0.183 |
| price 5-10 | 52 | 0.46 | 1.16 | 1.51 | 6.39 | 14.75 | 19.99 | 0.132 |
| price 50-100 | 193 | 1.09 | 5.71 | 7.38 | 1.61 | 8.29 | 11.20 | 0.292 |
| price <5 | 2 | 6.42 | 6.42 | 8.42 | 136.13 | 136.13 | 176.79 | 0.825 |
| year 2016 | 80 | 0.92 | 1.89 | 4.60 | 2.01 | 4.80 | 9.68 | 0.139 |
| year 2017 | 82 | 0.65 | 1.62 | 4.41 | 1.58 | 4.59 | 8.04 | 0.148 |
| year 2018 | 87 | 0.86 | 4.70 | 4.15 | 2.00 | 6.25 | 8.20 | 0.154 |
| year 2019 | 83 | 0.76 | 4.90 | 5.89 | 2.95 | 7.59 | 13.63 | 0.311 |
| year 2020 | 84 | 0.84 | 3.73 | 7.43 | 3.20 | 10.58 | 12.96 | 0.225 |
| year 2021 | 79 | 0.82 | 3.88 | 7.24 | 4.04 | 12.64 | 15.76 | 0.194 |
| year 2022 | 93 | 0.82 | 3.85 | 5.00 | 2.44 | 8.74 | 12.07 | 0.190 |
| year 2023 | 84 | 0.81 | 8.22 | 6.57 | 2.14 | 8.29 | 13.40 | 0.242 |
| year 2024 | 86 | 1.25 | 7.65 | 9.27 | 1.92 | 11.78 | 22.40 | 0.296 |
| year 2025 | 88 | 1.45 | 4.85 | 10.44 | 3.98 | 7.82 | 18.43 | 0.231 |

## Quoted spread at 09:35 and at the close

MEASURED, cents, last quote at or before 09:35:00 and before 16:00:00 New York; price groups use the 09:30 open.

| group | n 09:35 | median 09:35 | mean 09:35 | p90 09:35 | n close | median close | mean close | p90 close |
|---|---|---|---|---|---|---|---|---|
| all | 1194 | 9.00 | 18.26 | 42.00 | 1200 | 1.00 | 2.63 | 5.00 |
| price 10-20 | 198 | 4.00 | 6.48 | 14.30 | 199 | 1.00 | 1.81 | 3.00 |
| price 100+ | 200 | 36.00 | 54.10 | 111.40 | 200 | 2.00 | 6.68 | 18.00 |
| price 20-50 | 446 | 6.50 | 9.54 | 21.00 | 449 | 1.00 | 1.65 | 3.20 |
| price 5-10 | 82 | 3.00 | 3.95 | 8.90 | 84 | 1.00 | 2.11 | 5.40 |
| price 50-100 | 268 | 14.00 | 19.12 | 40.00 | 268 | 1.00 | 2.01 | 4.00 |
| year 2016 | 120 | 7.00 | 10.18 | 23.00 | 120 | 1.00 | 1.43 | 2.00 |
| year 2017 | 120 | 7.00 | 10.56 | 22.00 | 120 | 1.00 | 1.49 | 3.00 |
| year 2018 | 120 | 9.00 | 14.08 | 31.10 | 120 | 1.00 | 1.73 | 4.00 |
| year 2019 | 119 | 7.00 | 13.13 | 30.20 | 120 | 1.00 | 1.72 | 3.00 |
| year 2020 | 119 | 7.00 | 14.61 | 34.00 | 120 | 1.00 | 3.44 | 8.10 |
| year 2021 | 120 | 7.00 | 16.13 | 36.10 | 120 | 1.00 | 3.42 | 7.00 |
| year 2022 | 120 | 6.50 | 13.65 | 32.10 | 120 | 1.00 | 2.50 | 5.00 |
| year 2023 | 119 | 14.00 | 32.77 | 88.80 | 120 | 1.00 | 3.24 | 6.10 |
| year 2024 | 120 | 12.50 | 27.62 | 79.40 | 120 | 1.00 | 3.92 | 7.00 |
| year 2025 | 117 | 15.00 | 30.21 | 70.00 | 120 | 1.00 | 3.40 | 6.00 |

- MEASURED: the median spread at 09:35 is 9.0 times the median spread at the close. The breakout order is placed soon after 09:35.

## Outlier check

- MEASURED: with the largest 1% of each part left out (entry 9 of 978, exit 8 of 840), the means are 0.0643 and 0.1211, sum 0.1854. Still above the limit.
- MEASURED: the largest single values were 1.72 (entry) and 1.97 (exit) times the stop distance. MEASURED by hand on the largest exits: they were gaps through the stop. No value was below zero (0 entry, 0 exit), as the definition requires.

## Compared with what was published

- STATED (doc 55): one rebuild measured 2.4 cents mean and 1.0 cent median on the entry, about 12% of the stop distance, and the rule then lost. Our entry mean is 1.40 cents with a median of 0.00; our stop exit costs more than our entry as a share of the stop.
- STATED (doc 55): the paper charges a commission and no slippage.

## Limits

- The ETF list is today's Nasdaq Trader list, so a dead ETF is missed and a reused ticker can be misread. Some tickers were never asked (5-letter endings other than A, B, C, K and L, and dots other than .A and .B).
- The breakout and stop minutes come from 1-minute bars, which may leave out some prints. The odd-lot version can only trigger inside minutes the bars point to.
- UNKNOWN: whether the trade time is the exchange's or the consolidated feed's. Quotes are taken as the national best bid and offer. That is likely but not proven.
- 60 days is a sample. It was fixed before any fill was seen.
- The trades, quotes and per-stock-day rows stay off the repo because they are vendor data.
