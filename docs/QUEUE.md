# The queue: what gets tested next

The work list for the builder and its helpers. Take the top item that is not blocked, write its ledger row (`research_rig/TRIAL_LEDGER.md`), run it, put the result in `docs/STATUS.md`, then move the item to "Done" with one line saying what happened. Add new ideas at the bottom of "Ideas" with where the idea came from. Anyone may add an idea. Nothing here needs the owner's yes.

Last changed: 2026-11-25 15:16 UTC

## Running now

| # | What | Plan | Started |
|---|---|---|---|
| 1 | Six AI models trade crypto from prices alone in the time machine, October 2026 first, then four more months | `timemachine/PLAN_TM01_crypto_price_only.md` | 2026-11-25 |
| 2 | Replay 07: eight day trading rules on SPY and QQQ one-minute prices | `research_rig/PREREG_07_intraday_spy_qqq.md` | 2026-11-25 |
| 3 | Replay 09: seven crypto methods not tried before, at Alpaca's fees | `research_rig/PREREG_09_crypto_methods.md` | 2026-11-25 |
| 4 | Tape: crypto prices further back, and a source of dated headlines that needs no key | none, tooling | 2026-11-25 |

## Next, in order

| # | What | Needs | Blocked by |
|---|---|---|---|
| 5 | Crypto traders that read dated headlines as well as prices (`practice/traders/A08_crypto_news.md` and a news version of card B01), against the price-only traders of item 1 | headlines on the tape | item 4 |
| 6 | Measure each model's knowledge line with dated questions, so replays only use days after it | nothing | nothing |
| 7 | Buy bitcoin or ether when the cost of holding futures has been sharply negative for a day, sell when it turns positive. A fixed rule on one year of free Kraken futures history | Kraken futures funding history | nothing |
| 8 | Start the practice desk with the two fixed rules and the first AI traders | practice account key in the repo's secrets | the owner's key |
| 9 | Record stocks and dated news for the tape; replay the stock traders A01 to A06 and A09 | data key | the owner's key |
| 10 | Company filings read in full: a trader that compares each new annual or quarterly report with last year's and buys the companies whose reports changed least | free SEC filings, daily stock prices | stock prices: data key |
| 11 | A customer's good news, then buy its supplier before the supplier reports | free SEC filings for who sells to whom, stock prices, news | data key |
| 12 | Earnings call answers scored apart from the prepared remarks, held 15 days | filings, call text, stock prices | data key |
| 13 | New contracts that are large against a company's sales, from 8-K filings and the federal award list | free filings and award list, stock prices | data key |
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
