# A02 stocks_in_play

Status: builder settings, 2026-11-25. Untested. Market: US stocks. Holding time: same day to 3 trading days.

## What it tries to do

It looks for liquid stocks trading on much heavier volume than usual and buys only those where it can find and confirm a specific reason, such as a contract, an approval, a merger or a guidance change. It holds for hours to a few days and gets out fast if the move fails.

## Why this might work

- STATED: an opening-range method made most of its gain from picking "stocks in play" (high relative volume) rather than from the entry rule itself; the same entry on all stocks did far less ([Zarattini, Barbon and Aziz](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284), via `docs/research/01_stock_daytrading_evidence.md`). The authors run a day trading school, and no peer-reviewed repeat was found.
- MEASURED, old: stocks with unusually heavy volume did better over the next 20 sessions in a 1963 to 1996 study, long-short and before full costs ([Gervais, Kaniel and Mingelgrin](https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/9901.pdf), via document 17).
- MEASURED, against: the stocks most bought by Robinhood users had an average 20-day abnormal return of -4.7% ([Barber, Huang, Odean and Schwarz](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13183), via document 01). Buying what is popular loses. This is why a confirmed, specific reason is required.
- MEASURED, against: fast news reaction is dominated by machines faster than this desk (document 01, section 3).
- Honest summary: thin. The model's job is to separate a real business reason from noise, which a volume formula cannot do.

## What it looks at each time it wakes

- Its holdings and cash.
- Alpaca most active stocks and top movers, and minute bars for today on each.
- Alpaca news headlines for each candidate since yesterday's close.
- Web search for each candidate: "[company] news today", the company's newsroom, SEC filings from today (8-K).

## How it decides to buy

Every box must be ticked, written in the reason field:

1. Volume today is several times its usual level for this time of day.
2. There is one specific reason that changes the company's business, named in the reason field.
3. The reason is confirmed by a second independent source or a primary filing (`AGENTS.md`, "How a trader behaves", item 4).
4. The reason is not: a price target change, a social media post, a promotion, a share sale by the company, a reverse split, or a meme.
5. The price is above where it was 15 minutes after the open, and above the day's average price weighted by volume.
6. Share price above $5 and company value above $1 billion.
7. The model writes what would prove it wrong, in one sentence.

## How big

- 8% of its budget per position, at most 5 positions, at most 3 new buys a day.

## How it gets out

- Stop price: the day's low at the time of entry, but never more than 4% below entry.
- Target price: 8% above entry.
- Exit-by time: 15:45 Eastern on the day of entry, unless the model writes a reason to hold. Then the latest exit-by is 3 trading days after entry, at 15:45 Eastern.
- Stops are checked about every 10 minutes and fill at market, so losses can exceed the stop.

## What it never does

- Buys before 09:45 Eastern.
- Buys the top percentage gainer of the day for the gain alone.
- Buys on a rumour, a single headline, or a chat room post.
- Buys stocks under $5 or OTC stocks.
- Replaces a stopped-out trade in the same stock on the same day.

## When it wakes

- 09:50, 10:30, 12:00, 14:00 and 15:30 Eastern on market days. At 15:30 it only reviews holdings.

## What would make us drop it

- The rules in `practice/traders/ROSTER.md`, "How we judge".
- Also: if its average trade after costs is below its random twin's at the first 20-day check, it is reviewed early. Review is not a drop by itself.
