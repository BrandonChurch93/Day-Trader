# Morning list, 2026-11-25

Written by research at the end of the overnight run, and rewritten at 08:50 UTC after the audits and the second set of tests. Status: proposed. Nothing here is an owner decision. The record of the night is `docs/decisions/0005-overnight-research-2026-11-25.md` and `docs/decisions/0006-audit-and-second-night-2026-11-25.md`. The current state, with every result, is `docs/STATUS.md`.

## Where things stand

No rule has a clean pass. Results are in the table in `docs/STATUS.md`, which is written from the output files. In words:

| Test | What happened | Full write-up |
|---|---|---|
| Slow trend rules on bitcoin and ether | Four bitcoin rules pass, at the lowest venue cost only, only after audit fixes, and within a hair of the bar on one mark. No ether rule passes | `docs/research/16_rig_audit.md` |
| Day trading rules on bitcoin and ether | None pass at any venue cost. Fees are larger than the patterns | `docs/research/16_rig_audit.md` |
| Trend rules on a wide basket of coins | None pass. The basket did far worse than holding bitcoin | `docs/research/23_replay_04_coin_basket.md` |
| Slow trend rules on the US stock market from 1927 | Two runs, because an audit found one rule's code did not match the plan. First run: no rule passes at the two lower cost levels. Corrected run: five rules pass at every cost level. No rule passes in both runs at every cost level | `docs/research/22_replay_05_stock_trend.md` |
| AI models making the daily call | Inconclusive, as the plan said before it ran | `docs/research/14_ai_calls_pilot_02.md` |
| What it costs to trade a small size | Sampled overnight on two venues. Interim | `docs/research/24_order_book_costs.md` |

What the tests agree on, and what real funds built on the same rules also show: slow trend rules cut the worst drop and give up some growth. That is a smoother ride. It is not fast money. The reading on traders, funds and AI systems with real money says the same (`docs/research/25_what_the_evidence_supports.md`).

The one lead worth following on stocks: in the corrected run, the rule that holds the three strongest industry groups when the market is above its ten-month average grew nearly as much as holding, with a much smaller largest drop. It carries three cautions, listed in `docs/research/22_replay_05_stock_trend.md`. It has not been tested on anything that can be bought.

What has not been tested at all: funds that can be bought, and day trading SPY and QQQ. Both wait on a data purchase.

## Things only you can do

In this order. None uses real money for trading.

1. Open an Alpaca account for practice trading and create practice keys. This approves practice trading only. It does not approve funding the account. Detail is in `docs/research/09_brokers_and_venues.md`.
2. Buy one month of stock price data. Research recommends the EODHD plan with daily and one-minute prices, $29.99 for the month ([EODHD pricing](https://eodhd.com/pricing/)), because one purchase covers both waiting stock tests. Terms for keeping the files are in `docs/research/10_historical_data_and_practice.md`.
3. Say whether Kraken's published price files may be the main crypto history. Research recommends yes. Bitstamp's terms are unclear about collecting its prices.
4. Say whether the overnight order-book sampler may run again on Kraken's public price feed. Kraken's general terms bar automation on its content ([Kraken Global Terms](https://www.kraken.com/legal/global-terms)). Research reads the documented public feed as offered for this use. That is research's reading, not Kraken's word. The sampler stops by itself this morning and will not be restarted without your yes.
5. Say whether one line may be added to `AGENTS.md` so it points to `docs/STATUS.md` and `docs/INDEX.md`. That file says any change to it needs you, so it was not touched.

Not needed yet: written permission from five data sources (Cboe, FINRA, Kraken Futures, Kalshi, Polymarket) before their feeds may be collected. The collector has them switched off. Research recommends leaving them off until a test needs one (`docs/research/19_information_feeds.md`).

## Decisions waiting, one at a time

Research's recommendation is given for each. The order is the order research would take them in.

| # | Decision | Research recommends | You would be approving | You would not be approving |
|---|---|---|---|---|
| 1 | How pass mark 4 is measured | Count ties as half, and measure it over a fixed set of start dates and block counts, so one number does not decide. Detail in `docs/research/16_rig_audit.md` | A steadier way to measure. It would most likely turn the bitcoin passes back to fails. Its effect on the stock rules is UNKNOWN until rerun | Any change to the bar in `backtest_max_pbo` |
| 2 | How pass mark 3 is measured | Take the spread across every trial counted in the ledger, not only the trials in one plan. In replay 05 the mark screened nothing | A stricter mark 3 in every future plan | Any change to `replay_min_deflated_sharpe` |
| 3 | Audits | Every replay gets an independent audit by a different model before its result is believed. Tonight's audits changed results twice | A standing rule for research | |
| 4 | What to test next | Replay 06, slow trend on funds that can be bought, with the industry rule added on sector funds. Then replay 07, day trading SPY and QQQ. Each with its plan and ledger rows pushed first | Two more research replays, once the data is bought | Any building or any trade |
| 5 | Watching rules in the practice account | Run two slow rules with pretend money as observation, labelled as not passed: the bitcoin trend rule P1, and the ten-month rule on a total market fund | A forward record that starts the count toward `paper_min_trading_days` and `paper_min_closed_trades` | Calling either a strategy. Real money |
| 6 | Crypto day trading and wide coin baskets | Drop both. Every rule tested lost | Closing those two lines of work | Dropping crypto altogether |
| 7 | Interest on idle cash | Credit Treasury bill interest on cash in every replay. Trend rules sit in cash a lot and the crypto replays credit nothing | One rig change with its own plan | |
| 8 | The three pass marks proposed last night | Keep them | `replay_max_drop_ratio_vs_hold`, `replay_min_deflated_sharpe`, `replay_min_shuffle_percentile` | |
| 9 | Broker plan | Alpaca individual account for stocks and all practice. Live crypto venue left open | The plan in `docs/research/09_brokers_and_venues.md` | Funding anything |
| 10 | AI forward test | Run it in the practice account only if you want that question answered, with the rules in `docs/research/11_ai_trader_experiment_design.md` fixed first | A practice-only test | Real money on AI calls |
| 11 | High-risk share | Fund it only with ideas that pass a replay. First in line: insider buying that is not routine, in listed stocks | The order in `docs/research/25_what_the_evidence_supports.md` | Any penny stock or memecoin purchase |
| 12 | Open numbers | Yours alone: `live_starting_capital_usd`, `live_max_position_usd`, `live_max_daily_loss_usd`, `live_max_total_loss_usd`, `moonshot_sleeve_share`, `moonshot_max_position_share`, `api_model_spend_cap_usd_month` | Nothing until you set them | |
| 13 | Who the Builder is and where it runs | Decide after a rule passes in practice, not before | | |

## What research would say to a partner

- You asked for fast. Nothing tested or read supports fast, and the routes that look fast are the ones where the records show losses: borrowed money, day trading against fees, small coins, and letting a model pick trades.
- What the evidence supports is slower: rules that cut the worst drop, interest on idle cash, and a short list of narrow ideas that have a reason and have not been tested yet.
- The honest next month is cheap: one data purchase, a practice account, two stock tests, and two rules watched with pretend money. If those say no, the answer is no, and research will say so.

## One recommendation

Do items 1 and 2 of "Things only you can do" this morning, and take decision 1. That unblocks the two stock tests and the practice record, which are the things that could change this picture.
