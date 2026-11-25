# A09 moonshot

Status: builder settings, 2026-11-25. Untested. Market: US stocks and crypto. Holding time: days to months.

## What it tries to do

It takes small positions in bets that could move a lot, only where it can write down a reason from the short list of ideas that have one, plus a stop and an end date. The owner asked for moonshots only "if the moonshot actually makes sense and has a reason behind it" (`archive/decisions/0002-historical-testing-and-risk-posture.md`).

## Why this might work

- MEASURED, against most moonshots: penny and OTC stocks, memecoin launches, pump groups, copy trading and buying after listing news show no gain for a follower in any study found (`docs/research/13_high_risk_sleeve_evidence.md`).
- The ideas with a reason, from the ranked list in document 13: unusual insider buying in listed stocks above $5, activist filings bought after the filing, and slow trend on liquid coins. Each is STATED or MEASURED in old or in-sample work only, and none has passed a test here (`docs/research/25_what_the_evidence_supports.md`).
- UNKNOWN: whether the model can find a sound reason that is not on the list. Any such reason is logged and counted.
- Honest summary: the evidence mostly says what not to buy. This trader is a fenced place for the owner's moonshot share, so that it cannot leak into the others.

## Budget

- The real sleeve size is the owner's open numbers `moonshot_sleeve_share` and `moonshot_max_position_share` in `config/thresholds.yaml`. Neither has a value, and nothing here assumes one.
- In practice, A09 gets its own pretend budget like the other traders. The shares below are of that budget.

## What it looks at each time it wakes

- Its holdings and cash.
- SEC Form 4 and 13D filings since its last wake, as in `practice/traders/A06_insider_filings.md`.
- Top movers and most active stocks, only to find candidates. Never as a reason.
- Alpaca news and web search on each candidate: the primary filing, the company's last report, the size of its cash and debt.

## How it decides to buy

Every box must be ticked, written in the reason field:

1. A thesis in three sentences: what must happen, why the market has not priced it, and by when.
2. The thesis rests on a confirmed fact from a primary source (a filing, a regulator, a court, the company itself), not on a price move or a post.
3. The idea is one of: unusual insider buying, an activist filing, a confirmed business event in a listed company, or a liquid coin in an uptrend with a confirmed event. Anything else needs a reason the model writes, labelled "off-list".
4. Not any of the "leave" rows in document 13: penny or OTC stocks, top daily gainers, reverse splits, SPACs, memecoins, new tokens, pump or chat calls, FDA run-ups.
5. Stocks above $3 on a main US exchange; crypto only on Alpaca's list.
6. The model writes how much it expects to lose if wrong. Assumed 100% for sizing.

## How big

- 5% of its budget per position, at most 8 positions. No refill after a loss: money lost stays lost for the trial, as document 13 proposes.

## How it gets out

- Stop price: 30% below entry for stocks and 35% for crypto.
- Target price: the model's thesis price, written at entry.
- Exit-by time: the thesis date written at entry, at most 90 days, at 15:45 Eastern for stocks.
- Sold at the next wake if the fact in box 2 turns out false.

## What it never does

- Buys without a written thesis and a primary source.
- Adds to a losing position.
- Uses leveraged funds, options, or margin.

## When it wakes

- 10:00 and 15:30 Eastern on market days. Once a day at 00:15 UTC for crypto (19:15 Eastern in winter, 20:15 in summer).

## What would make us drop it

- The rules in `practice/traders/ROSTER.md`, "How we judge", with C01 or C02 as comparator by market.
- Also: if more than half of its buys are "off-list", it is reviewed, because that means it is guessing.
