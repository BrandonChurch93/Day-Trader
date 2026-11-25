# Status

Last updated: 2026-11-25 08:36 UTC

This page is the current state of the project. It is the second thing to read, after `AGENTS.md`. If another page disagrees with this one about a result or about where things stand, this page stands. The map of every file is `docs/INDEX.md`.

## Phase

- Research. Nothing is built. Building has not been approved by the owner.
- No broker account, no keys, no purchases, no real trades.
- A research rig in `research_rig/` replays rules on past prices. It is not the product.
- Owner direction that applies now, with dates, is in `docs/decisions/0002-historical-testing-and-risk-posture.md` (test on past data, a middle risk level, a small moonshot share only where there is a reason) and `docs/decisions/0003-quality-bar-adopted.md`.

## Every test so far

The Result column is written by `tools/status_table.py` from the output files. Do not edit it by hand.

<!-- results:start (written by tools/status_table.py, do not edit by hand) -->
| Test | What was asked | Result, MEASURED | Full write-up |
|---|---|---|---|
| Replay 01 with cross-check X2, rerun after the audits | Nine slow trend rules on bitcoin and on ether, daily, five venue costs, two price histories | 9 of 90 rule and venue pairs pass on Bitstamp prices and 4 of 90 on Kraken prices. Pass on both histories: P1, P2, S50, D20 on BTC, at Binance.US cost only. First run before the audit fixes: 0 on both. Knife edge: the overfitting estimate on Kraken prices is 0.2409 against a bar of 0.25 (`backtest_max_pbo`), and 0.4205 on Bitstamp prices from the same start date, which fails. | `docs/research/16_rig_audit.md` |
| Replay 03, rerun after the audits | Eight day trading rules on hourly bitcoin and ether, five venue costs | 0 of 80 rule, coin and venue combinations pass. | `docs/research/16_rig_audit.md`, rule definitions in `docs/research/15_replay_03_intraday_crypto.md` |
| Pilot 02 | Six AI model runs making one call a day on bitcoin and ether | Inconclusive, as the plan said before it ran. 6 model runs, 147 calls each. Too few days to tell skill from luck. | `docs/research/14_ai_calls_pilot_02.md` |
| Replay 04 | Trend rules on a wide basket of coins, dead coins kept | 0 of 25 rule and venue pairs pass. Highest deflated Sharpe 0.933 (K4 at Binance.US) against a bar of 0.95 (`replay_min_deflated_sharpe`). Held-back years at Binance.US cost: the top 10 coin rule K1 grew +2.7% a year, holding bitcoin grew +43.5%. An independent audit rebuilt the result and found faults that do not change it. | `docs/research/23_replay_04_coin_basket.md` |
| Replay 05, first run and corrected run | Eight slow trend rules on the US stock market index from 1927, three cost levels | First run: none at 2 bps; none at 5 bps; T1, T5, V1, I1 at 10 bps. Corrected run, after an audit found one rule did not match the plan: T1, T2, T4, T5, V1, I1, I2 at 2 bps; T1, T5, V1, I1, I2 at 5 bps; T1, T5, V1, I1, I2 at 10 bps. Pass in both runs at every cost: none. Held-back years at 5 bps: the ten-month rule T1 grew +9.1% a year with a largest drop of -21.9%, holding the market grew +11.5% with -54.6%. | `docs/research/22_replay_05_stock_trend.md` |
| Order-book samples | What it cost to trade a small size at once, sampled overnight on two venues | 18 rounds from 2026-11-25 07:28:03 to 2026-11-25 08:02:03 UTC. Bitcoin, middle cost of one order, fees not included: $1,000 cost 0.0 bps on Kraken and 0.8 bps on Binance.US; $10,000 cost 0.2 and 1.8 bps. The crypto replays assume 5 bps for this on bitcoin and ether. One night only. | `docs/research/24_order_book_costs.md` |
<!-- results:end -->

A pass means "worth running in a practice account". It does not mean "makes money". The five pass marks and their config keys are in `research_rig/README.md`.

## What is believed now

Each line says how far to trust it.

- No rule has a clean pass. MEASURED. Every pass in the table came after a code correction, or exists at one cost level only, or sits within a hair of a bar. Five stock rules pass at every cost in the corrected run of replay 05 and none of them passes at every cost in the first run.
- Slow trend rules cut the largest drop and give up growth. MEASURED on bitcoin and on the US stock market, and it matches the live record of funds built on the same rules (`docs/research/21_systematic_funds_and_published_rules.md`). In the held-back years these rules grew less than simply holding.
- Day trading rules on crypto lose to fees at every venue tested. MEASURED.
- A wide basket of smaller coins did worse than holding bitcoin. MEASURED.
- Nothing found so far supports fast money. MEASURED for what was tested. The reading agrees (`docs/research/25_what_the_evidence_supports.md`).
- Pass mark 4, the overfitting estimate, is not steady enough to be a yes or no on its own. MEASURED three ways: it moves with the start date, it passes on made-up data with no edge in a share of samples that document 16 gives, and in replay 05 it moved from fail to pass for seven rules when an eighth was corrected (`docs/research/16_rig_audit.md`, `docs/research/22_replay_05_stock_trend.md`). The bar in `backtest_max_pbo` has not been changed.
- AI models making the trading call: no evidence that it works, from our pilot or from live public records (`docs/research/14_ai_calls_pilot_02.md`, `docs/research/18_ai_systems_with_live_records.md`). Models stay out of the order path (`AGENTS.md` hard rule 1).
- The closest thing to a lead on stocks is rule I2 in replay 05: hold the three strongest industry groups when the market is above its ten-month average. In the corrected run it grew nearly as much as holding with a much smaller largest drop. It carries three cautions listed in `docs/research/22_replay_05_stock_trend.md`, and it has not been tested on anything that can be bought. Treat it as a reason for the next test, not as a result.
- Stocks have been tested only on a free index that cannot be bought. Funds that can be bought, and day trading SPY and QQQ, are UNKNOWN until price data is purchased.

## What has been replaced

| Do not rely on | Use instead | Why |
|---|---|---|
| Verdicts in `docs/research/12_replay_01_crypto_trend.md`, `docs/research/12b_replay_01_kraken_crosscheck.md`, `docs/research/15_replay_03_intraday_crypto.md` | `docs/research/16_rig_audit.md` | Two code audits found faults in the first rig. The rerun changed verdicts |
| Engine v1 (`research_rig/engine.py`) | Engine v2 (`research_rig/rig2.py`) | Same reason |
| `docs/decisions/0005-overnight-research-2026-11-25.md` where it reports results | `docs/decisions/0006-audit-and-second-night-2026-11-25.md` and the table above | Results changed after the audits |
| The first run of replay 05 for rule I2 | The corrected run, with both shown in `docs/research/22_replay_05_stock_trend.md` | The code for I2 did not match the plan |
| Playbook lines that read as settled findings | This page | The playbook was written from reading on 2026-11-24, before any test of our own |

## Known faults and slips

- `research_rig/basket.py` closes a position in a coin whose history ends by using knowledge of the full file. It never fired in replay 04. It must be fixed before the file is used again (`audit/2026-11-25_replay_04_audit.md`, finding 04-01, and two more in 04-02 and 04-03).
- Trial ledger rows for replays 04 and 05 were added after the runs started. The plans naming the trials were pushed before the runs. Recorded in `docs/decisions/0006-audit-and-second-night-2026-11-25.md`.
- Pass mark 3 screened nothing in replay 05, because of how its plan defined the spread of Sharpe ratios. The next plan must define it across all counted trials.
- Bitstamp's terms are unclear about collecting its prices. Kraken's published files are the proposed main crypto history. Waiting on the owner.

## Waiting on the owner

The full list, one item at a time, with what each approves and does not approve: `docs/decisions/morning_list_2026-11-25.md`. Nothing on it is decided.

Things only he can do:

1. Open an Alpaca account for practice trading and create practice keys.
2. Buy one month of stock price data, so replays 06 and 07 can run.
3. Say whether Kraken's published files may be the main crypto history.
4. Say whether the order-book sampler may run again on Kraken's public price feed.
5. Say whether one line may be added to `AGENTS.md` pointing to this page and to `docs/INDEX.md`.

Open owner numbers, with no value yet: `live_starting_capital_usd`, `live_max_position_usd`, `live_max_daily_loss_usd`, `live_max_total_loss_usd`, `moonshot_sleeve_share`, `moonshot_max_position_share`, `api_model_spend_cap_usd_month`. Nothing may assume a value for any of them.

## Next in the queue

Proposed order. The reasons are in `docs/research/25_what_the_evidence_supports.md`.

1. Decide how pass mark 4 is measured from now on (owner question in `docs/research/16_rig_audit.md`).
2. Replay 06: slow trend on funds that can be bought. Plan drafted in `research_rig/PREREG_06_fund_trend_paid_data_DRAFT.md`. Needs the data purchase. Proposed addition before it is frozen: the industry rule I2 on sector funds.
3. Replay 07: day trading SPY and QQQ on one-minute bars. Plan drafted in `research_rig/PREREG_07_intraday_spy_qqq_DRAFT.md`. Needs the data purchase.
4. Run one slow rule in the practice account as observation only, once practice keys exist.
5. Fix the three faults in `research_rig/basket.py` before any further basket test.

## Keeping this page true

- Any commit that adds or changes a result, a decision or what waits on the owner changes this page in the same commit, and moves the "Last updated" line.
- After any new output file: `python3 tools/status_table.py --write`.
- Before every commit: `python3 tools/check_repo.py`. It fails if the table above is out of date or a file named here does not exist.
- Write beliefs with their label. Do not raise a label without a new source or a new logged test.
