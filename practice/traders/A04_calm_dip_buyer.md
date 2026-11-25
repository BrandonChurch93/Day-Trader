# A04 calm_dip_buyer

Status: builder settings, 2026-11-25. Untested. Market: US large stocks and broad ETFs. Holding time: 1 to 5 trading days.

## What it tries to do

It buys a sharp short drop in a large company's stock only when it cannot find any company news that explains the drop, betting that a drop with no reason tends to bounce. It stays out when the drop has a real reason.

## Why this might work

- MEASURED, mixed: short-term reversal (losers bounce, winners fall back) mostly fails after costs, but one study found 30 to 50 bps a week net in the largest stocks with turnover kept down ([de Groot, Huij and Zhou](https://repub.eur.nl/pub/25718/AnotherLook_2011.pdf)); another found net returns negative across size groups ([Novy-Marx and Velikov](https://www.nber.org/system/files/working_papers/w20721/w20721.pdf)). Both via `docs/research/01_stock_daytrading_evidence.md`.
- MEASURED: in a model headline study, bad news in large stocks reversed slightly (+0.06%) while bad news in small stocks kept falling (-0.70%) ([Lopez-Lira and Tang](https://arxiv.org/html/2304.07619), via `docs/research/19_information_feeds.md`).
- UNKNOWN: whether "no news found" drops bounce more than "news" drops. That is the idea under test, and the part a formula cannot do.
- Honest summary: thin. The effect, if any, is small, and costs eat small effects.

## What it looks at each time it wakes

- Its holdings and cash.
- Daily bars for the last 60 days for a fixed list of large US stocks and broad ETFs, written in the ledger row before it runs (the 100 largest companies in a large company index, plus the broad market funds).
- Top movers, filtered to that list and to drops.
- Alpaca news headlines for each candidate since 2 days ago.
- Web search for each candidate: "[company] stock down why", "[company] news", SEC filings from the last 2 days.

## How it decides to buy

Every box must be ticked, written in the reason field:

1. The stock is on the fixed list.
2. It has fallen 5% or more over the last 1 to 3 days while the broad market fund fell less than 1% over the same days.
3. After the searches, the model finds no company-specific news: no earnings, guidance cut, filing, lawsuit, downgrade by a regulator, management exit or accident. It lists what it searched.
4. The broad market fund is above its 200-day average (no buying dips in a falling market).
5. No earnings report in the next 5 trading days.

## How big

- 8% of its budget per position, at most 6 positions, at most 2 new buys a day.

## How it gets out

- Stop price: 5% below entry.
- Target price: the close of the day before the drop began, written as a price at entry.
- Exit-by time: 5 trading days after entry, at 15:45 Eastern.
- If news explaining the drop appears later, the model sells at the next wake.

## What it never does

- Buys a drop it can explain with news.
- Buys stocks outside the fixed list.
- Adds to a position that keeps falling.
- Buys inverse or leveraged funds.

## When it wakes

- 10:00 and 15:30 Eastern on market days.

## What would make us drop it

- The rules in `practice/traders/ROSTER.md`, "How we judge".
- Also: the plain code logs every drop on the list that met boxes 1, 2, 4 and 5 and was skipped for news. If the skipped drops did as well as the bought ones over the trial, the news reading adds nothing, and the method is dropped.
