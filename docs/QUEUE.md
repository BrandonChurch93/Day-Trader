# The queue: what gets tested next

The work list for the builder and its helpers. Take the top item that is not blocked, write its ledger row (`research_rig/TRIAL_LEDGER.md`), run it, put the result in `docs/STATUS.md`, then move the item to "Done" with one line saying what happened. Add new ideas at the bottom of "Ideas" with where the idea came from. Anyone may add an idea. Nothing here needs the owner's yes.

Last changed: 2026-11-25 15:05 UTC

## Running now

| # | What | Who | Started |
|---|---|---|---|
| 1 | Build the time machine: tape, pretend broker, step-through server (`timemachine/`) | builder and two helpers | 2026-11-25 |
| 2 | Second outside review of the practice desk's order code (`practice/`) | outside reviewer | 2026-11-25 |
| 3 | Record crypto minute prices for the tape, 2026-06-01 to 2026-11-24 | tape helper | 2026-11-25 |

## Next, in order

| # | What | Needs | Blocked by |
|---|---|---|---|
| 4 | First replays: the crypto traders on the roster (`practice/traders/A07_crypto_trend.md`, `practice/traders/A08_crypto_news.md`) plus a hold and a random twin for each, one month each | time machine | news for A08 needs the data key |
| 5 | Measure each model's knowledge line with dated questions, so replays only use days after it | time machine | nothing |
| 6 | Start the practice desk with the two fixed rules and the first AI traders | practice account key in the repo's secrets | the owner's key |
| 7 | Record stocks and dated news for the tape; replay the stock traders A01 to A06 and A09 | data key | the owner's key |
| 8 | Day trading rules on SPY and QQQ one-minute prices (`research_rig/PREREG_07_intraday_spy_qqq_DRAFT.md`) | one-minute stock prices | data key, or the built-in price history |
| 9 | Fund trend rules on daily prices (`research_rig/PREREG_06_fund_trend_paid_data_DRAFT.md`) | daily fund prices with dividends | data key |
| 10 | Insider buying rule (`research_rig/PREREG_08_insider_buying_DRAFT.md`) | filings with dates, prices | data key |

## Ideas, not yet shaped into a test

| Idea | From |
|---|---|
| Small cheap agents watch all the time and wake a strong agent only for the few things that matter | the owner's first request |
| Copy the stated methods of traders with verified records, one trader per method | `docs/research/17_verified_traders_and_their_methods.md` |
| Rebuild the methods of AI systems with public live records and run them in the time machine | `docs/research/18_ai_systems_with_live_records.md` |
| Earnings reports read in full by a model, traded the same day | `practice/traders/A01_earnings_reader.md` |
| A trader that only sizes and exits, on top of a fixed entry rule that already has evidence | builder, 2026-11-25 |
| Many versions of one trader with different exit rules, to learn which exits matter | builder, 2026-11-25 |
| Crypto pairs beyond bitcoin and ether, where fewer people are looking | builder, 2026-11-25 |

## Done

The results of everything already run are in the table in `docs/STATUS.md`. From 2026-11-25 on, finished queue items are listed here.

| # | What | What happened |
|---|---|---|
