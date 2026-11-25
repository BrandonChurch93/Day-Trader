# A01 earnings_reader

Status: builder settings, 2026-11-25. Untested. Market: US stocks. Holding time: 1 to 10 trading days.

## What it tries to do

It reads earnings releases, guidance and call notes faster and more fully than a person can, and buys the few reports where the company clearly raised its outlook. It holds a few days to see whether the market keeps moving in that direction.

## Why this might work

- MEASURED, against: the old after-earnings drift is gone in large stocks since 2006 and recently in very small ones ([Martineau, Critical Finance Review](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3111607), via `docs/research/01_stock_daytrading_evidence.md`). A newer paper says it came back and the question is disputed ([UCLA Anderson Review](https://anderson-review.ucla.edu/is-post-earnings-announcement-drift-a-thing-again/)).
- MEASURED: a model scoring headlines found next-day moves, but the buy-only side was 8 bps a day before costs, and the result fell each year and turned negative at small costs when weighted by size ([Lopez-Lira and Tang](https://arxiv.org/html/2304.07619), via `docs/research/19_information_feeds.md`).
- STATED: gap-up setups on news did better than plain breakouts in one outside test with costs and dead stocks included ([TickerGuard study](https://tickerguard.com/articles/qullamaggie-backtest-study), via `docs/research/17_verified_traders_and_their_methods.md`).
- UNKNOWN: whether reading guidance text, not just the headline number, adds anything. That is the idea under test.
- Honest summary: thin. The reason to try it is that full-text reading is what a model does better than a formula.

## What it looks at each time it wakes

- Its own holdings and cash, read from the broker feed.
- Alpaca news headlines since its last wake, filtered to earnings and guidance.
- Web search: "[company] earnings guidance [quarter]", the company's own press release, the SEC 8-K item 2.02 filing.
- Daily bars for the last 60 days and minute bars for today, for each candidate.
- Most active stocks and top movers, only to find which reporting companies are moving on volume.

## How it decides to buy

Every box must be ticked, written in the reason field:

1. The report came out since the last close, before the market opened or after the previous close.
2. The company raised its full-year guidance, or beat on both sales and earnings and gave guidance above what the release says was expected. Read from the release itself, not a headline.
3. A second independent source confirms it: the 8-K or the company's own release, plus one news report (`AGENTS.md`, "How a trader behaves", item 4).
4. Today's volume so far is well above its usual level for this time of day.
5. The price is above yesterday's close at the time of the decision, and has held there since the first 15 minutes.
6. Share price above $5, average daily dollar volume large enough that the order is a tiny share of it.
7. No known event in the next 2 trading days that could undo it (a lawsuit ruling, a share sale announced in the same release).

## How big

- 10% of its budget per position, at most 6 positions, at least 30% cash at all times.

## How it gets out

- Stop price: the lower of today's low so far and 6% below entry.
- Target price: 15% above entry, or none if the model writes a reason to let it run, in which case it raises the stop to entry once the price is 8% above entry (written as a new stop at a later wake).
- Exit-by time: 10 trading days after entry, at 15:45 Eastern.
- Stops are checked by the plain code about every 30 minutes and fill as market orders, so a loss can be larger than the stop.

## What it never does

- Buys before 09:45 Eastern or after 15:30 Eastern.
- Buys on a headline alone, a social media post, or an analyst's note.
- Buys stocks under $5, OTC stocks, or the day's top percentage gainers chosen for the gain alone (`docs/research/13_high_risk_sleeve_evidence.md`).
- Adds to a losing position.
- Holds through the company's next report.

## When it wakes

- 09:45, 11:30 and 15:30 Eastern on market days.

## What would make us drop it

- The rules in `practice/traders/ROSTER.md`, "How we judge".
- Also: if fewer than 10 trades happen in 40 trading days, the method is too rare to measure and is dropped or widened as a new trial.
