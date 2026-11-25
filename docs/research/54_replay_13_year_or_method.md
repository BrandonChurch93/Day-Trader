# 54. Replay 13: the owner's method as a fixed rule, year by year 2020 to 2026

Status: research result, pretend trades on past prices, run once 2026-11-25 19:28 UTC against commit c6089b2. Built by `research_rig/report_13.py` from `research_rig/results_13.json`. The plan is `research_rig/PREREG_13_year_or_method.md`; its numbers are in the config key `replay_13_plan`. Ledger rows 144 and 145.

Labels: MEASURED means computed from the stored result file. Every figure below is MEASURED unless marked.

## What was asked

The owner made money in 2021 buying dips and selling peaks on the coins people were chasing. Was it the method or the year? Two fixed rules were run on every year from 2020, each year starting again from 1.00, on hourly Binance prices, with the coin list taken from each month's ranking at the time so that dead coins are in.

- Each Monday the hot five are the 5 coins with the largest 7-day gain among the first 50 by size (bitcoin, ether, dollar-tied, gold-backed, wrapped and exchange coins left out).
- Rule A: buy the hot five in equal parts and hold them for the week.
- Rule B: on the hot five, buy a coin when its hourly close is 5% or more below its highest close of the last 24 hours and still above its close 7 days ago; sell at +5%, at -5%, or after 24 hours.
- Cost 15 bps a side, judged. No leverage, judged. Fills at the next hour's open.
- Yardsticks: every rankable coin held in equal parts; the same rule on five coins drawn at random each Monday (200 paths, the 75th percentile); bitcoin held, for scale.

## The finding

- Rule B, the dip-and-peak rule (the nearer of the two to what the owner did): not paid. Above all coins in 2 of 7 years (2022, 2025); also above the random mark in 0 (none); of those, years in which all coins fell: none. The mark was at least 5 years with at least one falling year.
- Rule A, holding the hot five for the week: supported: the method, not the year. Above all coins in 5 of 7 years (2020, 2021, 2022, 2024, 2025); also above the random mark in 5 (2020, 2021, 2022, 2024, 2025); of those, years in which all coins fell: 2022, 2025. The mark was at least 5 years with at least one falling year.

A support means worth a time machine test and then the practice desk. It does not mean it makes money.

## Each year at the judged cost (15 bps a side, no leverage)

| Year | Rule A | Rule B | All coins held | Random five, rule A mark | Random five, rule B mark | Bitcoin held | Rule B trades | Rule B share stopped out |
|---|---|---|---|---|---|---|---|---|
| 2020 | +150.9% | -6.9% | +111.2% | +148.7% | +20.9% | +291.9% | 1,114 | 35% |
| 2021 | +513.0% | -78.7% | +374.1% | +505.6% | +6.5% | +39.6% | 1,783 | 41% |
| 2022 | -71.6% | -38.6% | -82.4% | -80.8% | -17.9% | -65.1% | 818 | 31% |
| 2023 | +16.7% | +30.7% | +64.1% | +88.8% | +46.6% | +153.7% | 666 | 24% |
| 2024 | +49.8% | -19.9% | +12.8% | +31.9% | +39.0% | +120.6% | 936 | 32% |
| 2025 | -66.0% | -65.3% | -72.3% | -68.1% | -35.3% | -11.2% | 711 | 33% |
| 2026 | -75.6% | -56.7% | -44.2% | -37.3% | -9.6% | -33.3% | 556 | 33% |

2026 runs to 2026-11-23. Each year starts at its first Monday.

## Other cost levels, shown and not judged

| Year | Rule A at 5 bps | Rule B at 5 bps | All coins at 5 bps | Rule A at 30 bps | Rule B at 30 bps | All coins at 30 bps | Rule B at 3x, 15 bps |
|---|---|---|---|---|---|---|---|
| 2020 | +178.4% | +46.0% | +134.1% | +114.6% | -52.4% | +81.0% | -79.8% |
| 2021 | +580.2% | -56.6% | +426.0% | +424.5% | -92.7% | +305.6% | -100.0% |
| 2022 | -68.5% | -15.0% | -80.7% | -75.7% | -62.3% | -84.6% | -88.8% |
| 2023 | +29.5% | +70.8% | +82.1% | -0.2% | -12.4% | +40.4% | +5.4% |
| 2024 | +66.5% | +16.7% | +25.1% | +27.8% | -54.4% | -3.3% | -86.0% |
| 2025 | -62.2% | -53.8% | -69.4% | -70.9% | -77.5% | -76.0% | -98.4% |
| 2026 | -73.2% | -45.9% | -38.9% | -78.7% | -68.9% | -51.3% | -95.4% |

## How rule B's trades ended

| Year | Take | Stop | Time limit | Week end | Flagged part-weeks, rule A | Flagged part-weeks, rule B |
|---|---|---|---|---|---|---|
| 2020 | 420 | 388 | 238 | 68 | 0.0% | 0.4% |
| 2021 | 713 | 738 | 254 | 78 | 0.0% | 0.4% |
| 2022 | 262 | 254 | 264 | 38 | 0.0% | 0.0% |
| 2023 | 211 | 163 | 258 | 34 | 0.0% | 0.0% |
| 2024 | 333 | 297 | 263 | 43 | 0.0% | 0.0% |
| 2025 | 203 | 235 | 241 | 32 | 0.0% | 0.0% |
| 2026 | 139 | 182 | 214 | 21 | 0.0% | 0.0% |

A year with more than 5% flagged cannot count. Years that could count: rule A 2020, 2021, 2022, 2023, 2024, 2025, 2026; rule B 2020, 2021, 2022, 2023, 2024, 2025, 2026.

## Reading the result

- Rule B lost money in 6 of 7 years (2020, 2021, 2022, 2024, 2025, 2026), 2021 among them: in the year coins rose most, selling every 5% gain gave the rise away and the trading costs took the rest. At the lowest cost shown it still ended below all coins held in every year but 2022, 2025. At 3x it was close to a total loss in most years. So the fixed dip-and-peak rule does not explain the owner's 2021. What is left are the things the rule does not have: the year itself, the choice of coins, leverage on a rising market, and judgment.
- Rule A met the marks set before the run, and that needs care. The marks compare it with the average coin, and the average coin was a poor thing to hold after 2021. Rule A still ended 3 of 7 years with a loss (2022, 2025, 2026) and ended above bitcoin held only in 2021. In 2020 and 2021 it was only a little above the random-five mark. In the latest year, 2026, it was well below every yardstick.
- What the result does show: last week's hottest coins did somewhat better than the average coin in five of seven years, two falling years among them. That is a lean, not a method. Held long by itself it rides the whole coin market up and down.
- What follows, as new plans with their own ledger rows and not as a reading of this one: the hot five against the rest of the market with the market's own move taken out, which needs short positions on futures; and the hot five only while the market as a whole is rising.

## What this does not cover

- Rule B is a fixed rule with round numbers. It is not the owner's eye for a chart. It answers whether buying 5% dips on rising coins and selling 5% up was paid by itself.
- Hot here means last week's price gain. It does not use what people were talking about.
- One venue's prices (Binance), hourly. Coins it did not list are missing from the list and counted in the result file. The cost is a flat figure, not a measured spread for each coin in each year; small coins in 2020 and 2021 may have cost more.
- Each year stands alone from 1.00; nothing is carried from year to year.
- Rule A's support comes from one run of one set of round numbers on seven years. Seven years is a small sample. It has not been tried on prices it has not seen, because every year was used here.
- The 3x column closes a position at a total loss of its part when the price falls 30% below entry. It is a simulation and not any venue's margin rules.
