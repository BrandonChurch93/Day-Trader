# The queue: what gets tested next

The work list for the builder and its helpers. Take the top item that is not blocked, write its ledger row (`research_rig/TRIAL_LEDGER.md`), run it, put the result in `docs/STATUS.md`, then move the item to "Done" with one line saying what happened. Add new ideas at the bottom of "Ideas" with where the idea came from. Anyone may add an idea. Nothing here needs the owner's yes.

Last changed: 2026-11-25 16:26 UTC

## Running now

As of 2026-11-25 17:52 UTC. Plans TM01 to TM04 are finished and are in Done or in `docs/STATUS.md`.

| # | What | Plan | Started |
|---|---|---|---|
| 9b | The earnings release reader: the checking code was audited by a second model, 14 faults found and fixed, a second audit pass is running before the plan is frozen | draft plan, frozen and pushed before any reader runs | 2026-11-25 |
| 9g | Fast lane, the owner's own method (`practice/traders/F01_hot_coin_swing.md`): a second price store from Coinbase minutes for smaller coins, and a futures book in the time machine that can go long or short with funding and forced close-out | plan TM06, written when both are in | 2026-11-25 |
| - | Dated calls by the crypto callers the owner followed, Alex Becker first: what was said on what date and what the coin did after | reading, no plan | 2026-11-25 |
| - | The two fixed rules on the practice desk, pretend money | `practice/README.md` | 2026-11-25 16:31 UTC |

## Next, in order

| # | What | Needs | Blocked by |
|---|---|---|---|
| 8 | Put the first AI traders on the practice desk (`practice/PLAN_02_ai_desk.md`). The two fixed rules have run there since 2026-11-25 16:31 UTC | a method that earned it in the time machine | no method has earned it yet: TM01 to TM04 did not pass |
| 9b | An AI reads each earnings release and says buy or skip for the next open; judged against random picks among the same releases and against buying every release. Large, mid and small companies. The draft plan is on the research machine until it is frozen | free SEC filings, daily stock prices from the built-in history | the plan being finished, then frozen with its ledger rows |
| 9f | Measured stock trading costs from past bid and ask. Measured for 56 symbols, June to November 2026: the middle half-spread was about 1 bps in regular hours and about 2.4 bps in the first half hour, against the 5 bps the time machine charges. Still to do: write it up in `docs/research/` from a script | the data key (in) | a free slot |
| 10 | Company filings read in full: a trader that compares each new annual or quarterly report with last year's and buys the companies whose reports changed least | free SEC filings, daily stock prices | the published design being collected with quotes |
| 11 | A customer's good news, then buy its supplier before the supplier reports | free SEC filings for who sells to whom, stock prices, news | nothing |
| 12 | Earnings call answers scored apart from the prepared remarks, held 15 days | filings, call text, stock prices | nothing |
| 13 | New contracts that are large against a company's sales, from 8-K filings and the federal award list | free filings and award list, stock prices | nothing |
| 15 | Insider buying only when the news is bad and the price is far below its high (`research_rig/PREREG_08_insider_buying_DRAFT.md` is the plain version) | filings, prices, news (data key is in; stock news only from 2026-04-29) | a free slot |
| 9e | A new swing card where the desk, not the model, sets the exit: a stop 8% below and five days, on months not yet traded. Earned by the exit replay (`docs/research/32_exit_replay.md`). Moved down by the builder 2026-11-25 16:44 UTC: the same replay showed the models' buys behind random buys under every exit, so the exit alone is unlikely to be the fix. Plan and ledger row first | a desk-exit option in the time machine | lower priority than 9b, 9c, 9d |

## Ideas, not yet shaped into a test

The idea scout's full write-up of 23 ideas, each with sources and the way it could fool us, is on the research machine and goes into `docs/research/` when its sources have been checked.

| Idea | From |
|---|---|
| Small cheap agents watch all the time and wake a strong agent only for the few things that matter | the owner's first request |
| Copy the stated methods of traders with verified records, one trader per method | `docs/research/17_verified_traders_and_their_methods.md` |
| Rebuild the methods of AI systems with public live records and run them in the time machine | `docs/research/18_ai_systems_with_live_records.md` |
| A model reads a company's numbers with the name removed and says whether profit will rise | idea scout, 2026-11-25 |
| Drug approval dates: buy weeks before, always sell before the decision | idea scout, 2026-11-25 |
| All-cash buyouts: read the agreement, buy when the gap to the offer is wide and the money is committed | idea scout, 2026-11-25 |
| Prediction markets move on confirmed news before the linked fund or coin does. Forward only | idea scout, 2026-11-25 |
| Leave heavily shorted stocks out of every stock trader's list | idea scout, 2026-11-25 |
| Avoid list: the model names stocks to leave out, the book holds the rest (`timemachine/PLAN_TM05_avoid_list_DRAFT.md`). Shelved 2026-11-25: the dropped stocks in TM04 did not fall more than random drops | builder, 2026-11-25 |
| A model that only chooses among fixed risk rules, against the best single rule | `docs/research/38_ideas_round_4_checked.md` |
| Leave-out screen from filings: a sudden chief executive or finance chief exit, or a cyber incident report | `docs/research/38_ideas_round_4_checked.md` |
| Method card from the owner's own past crypto trading, once he describes it | the owner, 2026-11-25 |
| A trader that only sizes and exits, on top of a fixed entry rule that already has evidence | builder, 2026-11-25 |
| Many versions of one trader with different exit rules, to learn which exits matter | builder, 2026-11-25 |

## Looked at and dropped before testing

Reported by the idea scout as dead, reversed or eaten by costs for an account that only buys. Each has its sources in the scout's write-up.

- Buying stocks added to the S&P 500 index.
- Chasing coins on the day an exchange lists them, and following stablecoin issuance.
- Holding stocks only overnight.
- Small stocks that open far higher on news, bought at the open.

## Done

The results of everything run before 2026-11-25 15:00 UTC are in the table in `docs/STATUS.md`. Finished queue items are listed here from then on.

| # | What | What happened |
|---|---|---|
| - | Build the time machine | Built and pushed 2026-11-25. Tape and recorder 65 checks, pretend broker and server 93 checks. A hold of bitcoin over October 2026 ran end to end and its books matched the pretend broker to the cent |
| - | Outside review of the practice desk's order code | Three passes by a different model. Faults found and fixed: overspending across traders, selling a shared holding twice, a stock order sent after the close, a pick edited after it was seen. Three test files pass |
| - | Replay 07: eight day trading rules on SPY and QQQ one-minute prices | Run once 2026-11-25. No rule passed on either fund (`docs/research/27_replay_07_intraday_spy_qqq.md`). Follow-up worth doing: measure the real cost of a round trip in QQQ at the practice desk, since one rule beats holding only below about 1.8 hundredths of a percent |
| - | Replay 09: seven crypto methods not tried before, at Alpaca's fees | Run once 2026-11-25 and checked by a second model. None passed (`docs/research/28_replay_09_crypto_methods.md`) |
| - | Tape: crypto prices further back, and dated headlines that need no key | Done 2026-11-25. Days from 2024, minutes from 2026-01-01, headlines from 2026-06-01 from three sites. Headline dates checked (`timemachine/news_date_check.json`). SPY, QQQ and 22 funds added from the built-in price history |
| - | Buy spot after a day of negative perpetual funding | Closed without a run, 2026-11-25. Binance funding history 2020 to 2026 is complete, but in four design years the signal fired 1 to 11 times per version. Too few to judge (`research_rig/PREREG_10_negative_funding.md`) |
| - | Replay 06: six slow trend and allocation rules on nine funds, daily prices with dividends | Run once 2026-11-25 17:06 UTC after an independent check of the runner. None passed at 5 bps per side. The strongest-three-funds rule beat its own yardstick on yearly gain but not holding SPY, and passed one mark of five (`docs/research/35_replay_06_fund_trend.md`) |
| - | Plan TM03: six AI models set once a day how much bitcoin to hold, eight months | Finished 2026-11-25 17:29 UTC, 48 sessions. Not shown: all six ended ahead of holding, none above the 90th percentile of its own answers in random order. A plain 20-day rule matched the best models (`docs/research/34_time_machine_tm03_bitcoin_dial.md`, `docs/research/37_tm03_plain_dials.md`) |
| - | Leverage in the time machine: 2x, 3x and 5x with hourly financing and forced close-out, and a replay of the stored TM03 answers | Built and tested 2026-11-25 17:39 UTC. Leverage made every gap bigger and made nothing new. With one account carried through the eight months, every model that made money at 1x lost money at 5x (`docs/research/39_leverage_replay_tm03.md`). After the fact, not a counted trial |
| - | Stock sessions in the time machine | Done 2026-11-25. Wake times, regular hours, fills and 18 new checks, with a check that a crypto session never sees a stock item |
| - | Replay the models' buys under fixed exits | Done 2026-11-25. Their own exits cost most of the loss; their entries show no skill against bitcoin bought at the same moments or against random twins (`docs/research/32_exit_replay.md`) |
| - | Measure each model's knowledge line | Done 2026-11-25. None of the six models could give a month-end price for any replay month; the latest any knows is about February 2026 (`docs/research/31_model_knowledge_lines.md`) |
| - | Tape: single stocks and company filings | Done 2026-11-25. 56 stocks and funds minute by minute from 2026-06-01 (99.99% of minutes present), 275 company filings stamped to the second, 537 headlines from one site. On the research machine only |
| - | A "why" record for every replay trade | Built 2026-11-25 into the scoring script. One row per buy: what the trader looked up, its reason, the headlines it named, how the trade ended (`docs/research/29_time_machine_tm01_crypto_price_only.md`, `docs/research/30_time_machine_tm02_crypto_with_news.md`) |
| 4b | Order-book cost samples on Kraken and Binance.US, 254 rounds over 9 hours on 2026-11-25 | Finished. Buying or selling $1,000 of bitcoin or ether cost less than the 5 bps the replays charge, in the middle case and in the worst 5% of readings. Smaller coins cost more. One calm-or-not-measured day. `docs/research/24_order_book_costs.md` |
| 9i | Where a US account in Idaho can trade crypto with leverage through an API | Read and checked 2026-11-25 17:48 UTC (`docs/research/40_leverage_venues_checked.md`): 66 claims confirmed, 3 wrong, 14 not found. No venue has small coins, an open order API and a matching practice account all at once. Fees run from about 1 to 25 basis points a side. Leveraged tests stay in the time machine, scored at three fee levels |
| 9d | Plan TM04: the model names eight of 38 stocks once a week | Finished 2026-11-25 17:51 UTC, 12 of 12 runs. Method: not shown. Seven of twelve runs ended below holding all 38 in equal parts; best was GPT-6.2 Sol run 2 at the 82nd percentile of its random baskets, under the 90 needed (`docs/research/36_time_machine_tm04_stock_basket.md`) |
