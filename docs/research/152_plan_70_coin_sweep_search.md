<!-- Built by research_rig/build_doc152_plan70_search.py from the pinned aggregate files only. -->
# Plan 70 search: one coin rule made the cut, none carried

MEASURED: One of 188 rules met the search marks. Its carry forecast passed in 4,134 of 20,000 draws (20.67%), below the 33% bar. Nothing carried; the Plan 70 search closed and the vault stayed sealed (ledger 218, queue 112).

## What was searched

STATED: Search ran on hourly Binance global spot USDT bars for 20 coins, January 2020 through December 2023. The grid tested price fades, clock effects, shocks, ranges, BTC lead and relative moves. Trades used the next hourly open, at most one gross-1x ticket at a time, with rules fixed before the successful run. Net includes the frozen round-trip costs and 1 bp of adverse funding per gross leg per hour. The matched t compares net with the same coin, UTC hour and holding period, using that block's own-date-inclusive baseline and grouping tickets by UTC entry date.

STATED: Eligibility required at least 200 resolved trades on 100 dates, including 40 dates in each half. The marks also required positive plain net in all three slices, matched t of 3.5 overall and 1.5 in each half, positive mean after trimming the best 1%, and at least 12% simple net a year.

MEASURED: 589,801 in-range rows; 589,679 kept and 122 wrong-close rows left missing. The first authorized attempt stopped in the loader with no summary. The refrozen input check and successful search used the same loader.

| Coin | Rows kept | Wrong close |
| --- | --- | --- |
| AAVE | 26,261 | 5 |
| ADA | 35,025 | 8 |
| AVAX | 28,463 | 6 |
| BCH | 35,025 | 8 |
| BNB | 35,025 | 8 |
| BTC | 35,025 | 8 |
| DOGE | 35,025 | 8 |
| DOT | 29,183 | 6 |
| ETH | 35,025 | 8 |
| HBAR | 32,132 | 6 |
| LINK | 35,025 | 8 |
| LTC | 35,025 | 8 |
| NEAR | 26,261 | 5 |
| PEPE | 5,136 | 0 |
| SHIB | 22,647 | 2 |
| SOL | 29,183 | 6 |
| SUI | 5,136 | 0 |
| XLM | 35,026 | 7 |
| XRP | 35,026 | 7 |
| ZEC | 35,025 | 8 |

## Families and raw leaderboard

MEASURED: The family statistics use only rules meeting the sample floors. “Lost clearly” is a report label, not a preregistered gate: negative plain net and matched t at or below -2. A family with no eligible rule has no summary statistic. Net is mean basis points per resolved trade.

| Family | Rules | Eligible | Lost clearly | Best matched t | Median net bp | Best net bp |
| --- | --- | --- | --- | --- | --- | --- |
| bitcoin lead | 16 | 16 | 16 | -2.28 | -36.5 | -13.6 |
| btc overextension fade | 16 | 10 | 3 | 3.51 | +3.6 | +97.2 |
| clock after move | 64 | 64 | 60 | -1.44 | -30.9 | -14.3 |
| hedged relative | 16 | 16 | 16 | -25.77 | -28.9 | -26.2 |
| hourly shock | 12 | 12 | 7 | 1.51 | -20.2 | +38.2 |
| london brr fade | 12 | 0 | 0 | n/a | n/a | n/a |
| midnight stop run | 12 | 2 | 0 | -0.76 | -20.8 | -16.9 |
| range rejection | 16 | 16 | 16 | -11.17 | -35.5 | -32.6 |
| round rejection | 8 | 8 | 8 | -29.90 | -40.2 | -38.0 |
| volume shock | 16 | 16 | 16 | -3.26 | -29.8 | -18.1 |

MEASURED: These are the ten highest defined matched t values, before sample floors or other marks. A high t on thin data is not a pass.

| Rule | Family | Trades | UTC dates | Eligible | Matched t | Plain net bp |
| --- | --- | --- | --- | --- | --- | --- |
| 70-102 | btc overextension fade | 691 | 435 | yes | 3.51 | +56.5 |
| 70-109 | btc overextension fade | 248 | 152 | yes | 3.48 | +97.2 |
| 70-110 | btc overextension fade | 194 | 149 | no | 3.39 | +140.4 |
| 70-106 | btc overextension fade | 453 | 313 | yes | 3.26 | +70.9 |
| 70-101 | btc overextension fade | 901 | 438 | yes | 2.91 | +32.1 |
| 70-114 | btc overextension fade | 101 | 79 | no | 2.90 | +202.1 |
| 70-113 | btc overextension fade | 123 | 82 | no | 2.65 | +134.9 |
| 70-105 | btc overextension fade | 552 | 317 | yes | 2.19 | +36.9 |
| 70-074 | hourly shock | 373 | 310 | yes | 1.51 | +38.2 |
| 70-073 | hourly shock | 412 | 313 | yes | 1.35 | +23.7 |

## The only finalist

MEASURED: 70-102, BTC overextension fade. The grid was 2 hours, BTC threshold 0.015 in log-price terms, 2.0 times BTC and a 2-hour hold. 3 selected tickets did not resolve; they are not included in the payoffs.

STATED: At each hourly open, compare each coin's last fully closed bar with its close two hours earlier. If BTC fell at least 0.015 in log-price terms and a non-BTC coin fell strictly more than twice as much, the rule looks for a rebound and goes long that coin with no BTC hedge. If several coins qualify, it takes the largest excess drop, breaking ties alphabetically. It enters at that hourly open and exits at the open exactly two hours later, with no stop or target. It holds at most one position at a time and skips any trade that would span the weekly maintenance hour or exit past the date fence.

| Search slice | Trades | UTC dates | Plain net bp | Matched net bp | Matched t |
| --- | --- | --- | --- | --- | --- |
| Whole | 691 | 435 | +56.5 | +54.5 | 3.51 |
| 2020 through 2021 | 466 | 272 | +62.3 | +56.2 | 2.73 |
| 2022 through 2023 | 225 | 163 | +44.4 | +44.7 | 2.08 |

MEASURED: Net after trimming the best 1% of tickets was +36.4 bp per trade. The cost-model result was +97.58% simple net per year at 1x, not a compounded or live return. Funding sensitivity for the same tickets was 0.25 bp per hour: +100.18%, 5 bp per hour: +83.76%; the 160 bp round-trip spot-fee comparison lost at -112.55% simple net per year.

MEASURED: At half the search mean, the fixed seven-day block forecast (seed 702102) cleared all vault marks jointly in 4,134 of 20,000 draws. 20.67% did not meet the 33% carry bar. This forecast does not use any vault observation.

## Limits and next steps

- **Spot proxy:** These are global spot prints, not measured fills on the named US contracts. Real funding, slippage and size feasibility are UNKNOWN.
- **Hindsight list:** The roster was selected with a later view of which coins existed and were eligible, so it is not a live 2020 roster.
- **Selection:** The finalist was best of 188 tests on the same dates; its t and net are not independent evidence. The spot-fee version lost and 3 selected tickets did not resolve.
- **Vault gap:** ZEC lacks February through June 2024 in custody. Those months stay missing, with no downloads. No Plan 70 vault price was read, so vault performance is UNKNOWN.
- **Next:** No Plan 70 practice card or vault run. Amendment 3 allows Plan 71 to search a second grid on the same dates. Rule 70-102 already used one of the sweep's three finalist places. Any new finalist must clear the same carry check before the one shared vault use and, after a vault pass, the separate US print, funding and size check.

STATED: The aggregate search and carry files are under `/home/user/workspace/rig/data/sweep_70`, with SHA-256 values `13e5375a3ed8207eb07fee034af0d7fba088bebbdce951a234bbd61373a1b607` and `6837579d1e6b805cb2c5aa679b2c7b6a75cc244c604c57c8b7c3a3f7ea4e09cf`. The builder reads only those two aggregates and the checked-in grid, settings and rule description. See the [Plan 70 design](../../research_rig/PREREG_70_coin_sweep.md) and [Amendment 3](../150_discovery_sweep_design.md).
