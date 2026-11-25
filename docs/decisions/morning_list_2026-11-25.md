# Morning list, 2026-11-25

Written by research at the end of the overnight run. Status: proposed. Nothing here is an owner decision. The record of the night is `docs/decisions/0005-overnight-research-2026-11-25.md`.

## Where things stand

Research has not yet found a rule that passes. That is the finding of the night, and it is stated plainly so nothing is built on a result that is not there.

| Test | Result | File |
|---|---|---|
| Replay 01: slow trend rules on bitcoin and ether | Bitcoin rules passed on the first history, then failed the overfitting mark on a history that starts 16 months later. No clean pass. No ether rule passed | `docs/research/12_replay_01_crypto_trend.md`, `docs/research/12b_replay_01_kraken_crosscheck.md` |
| Replay 03: eight day trading rules on bitcoin and ether | 0 of 16 passed. At Alpaca, Kraken and Coinbase fees every rule lost money. The patterns exist before fees and the fees are larger | `docs/research/15_replay_03_intraday_crypto.md` |
| Pilot 02: six AI model runs making daily calls | Inconclusive, as declared before it ran. Every run behaved like a simple trend rule | `docs/research/14_ai_calls_pilot_02.md` |
| High-risk sleeve reading | Penny stocks, memecoin launches, pump groups and copy trading show no gain for a follower. Three ideas have a reason and are untested | `docs/research/13_high_risk_sleeve_evidence.md` |

What has not been tested at all: stocks. Two tests are waiting on price data, which is a purchase.

- Slow trend rules on large stock funds. This is the playbook's first priority for stocks (`docs/playbook/01_stocks_what_works.md`).
- Day trading SPY and QQQ. Alpaca charges no commission on stocks, so the fee problem that sank the crypto rules is smaller. Research does not expect an easy pass: the one reproduction we hold puts break-even under about 1 bp for a round trip (`intraday_trend_max_round_trip_bps`). The test is to measure it and not assume it.

## Things only you can do

In this order. Each is small and none uses real money for trading.

1. Open an Alpaca account for practice trading and create practice keys. This approves practice trading only. It does not approve funding the account. Detail is in `docs/research/09_brokers_and_venues.md`.
2. Buy one month of price data. Research recommends EODHD's daily plus one-minute plan, because one purchase then covers both stock tests. Kibot's end-of-day plan is cheaper and covers the daily test only. Prices and the terms for keeping the files are in `docs/research/10_historical_data_and_practice.md`. This changes the recommendation in that file, which was written before replay 03.
3. Say whether the rig may switch its main crypto history to Kraken's published files. Bitstamp's general terms are unclear about collecting its prices, and its US terms page was not opened. Research recommends yes.

## Decisions waiting, one at a time

Research's recommendation is given for each. The order is the order research would take them in.

| # | Decision | Research recommends | You would be approving | You would not be approving |
|---|---|---|---|---|
| 1 | What to test next | Two stock replays, each with its plan written before it runs: slow trend on large funds first, then day trading SPY and QQQ | Two more research replays | Any building or any trade |
| 2 | Crypto day trading | Drop it at Alpaca, Kraken and Coinbase taker fees | Closing that line of work | Dropping crypto altogether |
| 3 | Slow bitcoin trend | Run P1 only in the practice account, as observation, labelled as not passed | Watching one rule with pretend money | Calling it a strategy |
| 4 | The blended trend rule | Test one rule that holds the average of the nine, so nothing is picked. Needs your call on how the overfitting mark applies to a single rule | One new counted trial | Any change to `backtest_max_pbo` |
| 5 | The three new pass marks | Keep them as proposed | `replay_max_drop_ratio_vs_hold`, `replay_min_deflated_sharpe`, `replay_min_shuffle_percentile` | |
| 6 | Broker plan | Alpaca individual account for stocks and all practice. Live crypto venue left open | The plan in `docs/research/09_brokers_and_venues.md` | Funding anything |
| 7 | AI forward test | Run it in the practice account only if you want that question answered, with the rules in `docs/research/11_ai_trader_experiment_design.md` fixed first | A practice-only test | Real money on AI calls |
| 8 | High-risk sleeve | Fund it only with ideas that pass a replay. First replay: opportunistic insider buying in listed stocks | The order of three replays in `docs/research/13_high_risk_sleeve_evidence.md` | Any penny stock or memecoin purchase |
| 9 | Open numbers | Yours alone: `live_starting_capital_usd`, `live_max_position_usd`, `live_max_daily_loss_usd`, `live_max_total_loss_usd`, `moonshot_sleeve_share`, `moonshot_max_position_share`, `api_model_spend_cap_usd_month` | Nothing until you set them | |
| 10 | Who the Builder is and where it runs | Decide after a rule passes, not before | | |

## One recommendation

Start with item 2 of "Things only you can do" and decision 1 together: buy the one month of data and let research write the plans for the two stock tests. Stocks are the half of your first message that has not been tested yet.
