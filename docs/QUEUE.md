# The queue: what gets tested next

The work list for the builder and its helpers. Take the top item that is not blocked, write its ledger row (`research_rig/TRIAL_LEDGER.md`), run it, put the result in `docs/STATUS.md`, then move the item to "Done" with one line saying what happened. Add new ideas at the bottom of "Ideas" with where the idea came from. Anyone may add an idea. Nothing here needs the owner's yes.

Last changed: 2026-11-25 16:26 UTC

## Running now

| # | What | Plan | Started |
|---|---|---|---|
| 1 | Six AI models trade crypto from prices alone in the time machine, October 2026 first, then four more months | `timemachine/PLAN_TM01_crypto_price_only.md` | 2026-11-25 |
| 2 | The same six AI models trade crypto with dated headlines added, same five months | `timemachine/PLAN_TM02_crypto_with_news.md` | 2026-11-25 |
| 4b | Order-book cost samples on Kraken and Binance.US, one full day. The sampler stops by itself at about 16:30 UTC. Then: `cd research_rig && python3 books_summary.py && python3 build_doc24.py`, `python3 tools/status_table.py --write`, commit, `python3 provenance.py --record --with-books`, commit | `docs/research/24_order_book_costs.md` | 2026-11-25 |

## Next, in order

| # | What | Needs | Blocked by |
|---|---|---|---|
| 8 | Start the practice desk with the two fixed rules and the first AI traders | practice account key in the repo's secrets | the owner's key |
| 9b | An AI reads each earnings release the minute it is filed and says buy or skip for the next open; judged against random picks among the same releases and against buying every release. Plan and ledger row first | free SEC filings, daily stock prices from the built-in history | nothing |
| 9c | Plan TM03: the model sets once a day how much bitcoin to hold, starting fully invested (`timemachine/PLAN_TM03_bitcoin_dial.md`). Plan and ledger row are in | the weights tool being built; crypto headlines for April and May | the tool |
| 9d | Plan TM04: the model names eight of 38 stocks once a week (`timemachine/PLAN_TM04_stock_basket.md`). Plan and ledger row are in | the weights tool; filings and headlines on the tape | the tool |
| 9e | A new swing card where the desk, not the model, sets the exit: a stop 8% below and five days, on months not yet traded. Earned by the exit replay (`docs/research/32_exit_replay.md`). Plan and ledger row first | nothing | a free slot |
| 9f | Measured stock trading costs from past bid and ask, to replace the assumed spread | the data key (in) | being recorded |
| 10 | Company filings read in full: a trader that compares each new annual or quarterly report with last year's and buys the companies whose reports changed least | free SEC filings, daily stock prices | stock prices: data key |
| 11 | A customer's good news, then buy its supplier before the supplier reports | free SEC filings for who sells to whom, stock prices, news | nothing |
| 12 | Earnings call answers scored apart from the prepared remarks, held 15 days | filings, call text, stock prices | nothing |
| 13 | New contracts that are large against a company's sales, from 8-K filings and the federal award list | free filings and award list, stock prices | nothing |
| 14 | Fund trend rules on daily prices (`research_rig/PREREG_06_fund_trend_paid_data_DRAFT.md`) | daily fund prices with dividends | data key |
| 15 | Insider buying only when the news is bad and the price is far below its high (`research_rig/PREREG_08_insider_buying_DRAFT.md` is the plain version) | filings, prices, news | data key |

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
| - | Stock sessions in the time machine | Done 2026-11-25. Wake times, regular hours, fills and 18 new checks, with a check that a crypto session never sees a stock item |
| - | Replay the models' buys under fixed exits | Done 2026-11-25. Their own exits cost most of the loss; their entries show no skill against bitcoin bought at the same moments or against random twins (`docs/research/32_exit_replay.md`) |
| - | Measure each model's knowledge line | Done 2026-11-25. None of the six models could give a month-end price for any replay month; the latest any knows is about February 2026 (`docs/research/31_model_knowledge_lines.md`) |
| - | Tape: single stocks and company filings | Done 2026-11-25. 56 stocks and funds minute by minute from 2026-06-01 (99.99% of minutes present), 275 company filings stamped to the second, 537 headlines from one site. On the research machine only |
| - | A "why" record for every replay trade | Built 2026-11-25 into the scoring script. One row per buy: what the trader looked up, its reason, the headlines it named, how the trade ended (`docs/research/29_time_machine_tm01_crypto_price_only.md`, `docs/research/30_time_machine_tm02_crypto_with_news.md`) |
