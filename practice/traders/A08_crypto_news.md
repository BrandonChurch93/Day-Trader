# A08 crypto_news

Status: builder settings, 2026-11-25. Untested. Market: liquid crypto pairs against USD on Alpaca. Holding time: hours to 5 days.

## What it tries to do

It trades crypto only after large, confirmed news that is specific to a coin or to crypto as a whole, such as a regulator's decision, a fund approval, an exchange failure or a major network upgrade. Most wakes end with no trade.

## Why this might work

- MEASURED: crypto prices moved a lot on regulatory headlines in a BIS study ([BIS regulatory news study](https://www.bis.org/publ/qtrpdf/r_qt1809f.htm), via `docs/research/02_crypto_trading_evidence.md`).
- MEASURED, against: none of the eight hourly day trading rules we tested passed at any venue cost, and at Alpaca's fee every one lost money in the held-back years (`docs/research/16_rig_audit.md`, `docs/STATUS.md`). That is why this trader does not trade chart patterns.
- MEASURED, against: on new exchange listings, most of the gain came before or on the news day, and the listing day was followed by a small fall ([Li et al.](https://www.loyola.edu/_media/sellinger-business/documents/academics/departments/finance/wealth-management-conference/speakers/J_Li.pdf), [Ante and Meyer](https://link.springer.com/content/pdf/10.1007/s10203-021-00323-0.pdf), via `docs/research/13_high_risk_sleeve_evidence.md`).
- MEASURED, against: 31 of 38 Alpha Arena accounts lost, outside reconstruction ([TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)). STATED for the figure.
- UNKNOWN: whether a model reading crypto news at its wake times gets anything after a 50 bps round trip.
- Honest summary: thin, and the costs are high. It is on the list because the owner asked for crypto day trading and this is the one form not already ruled out by our tests.

## What it looks at each time it wakes

- Its holdings and cash.
- Alpaca crypto news headlines since its last wake.
- Hourly and daily bars for the pairs in its allowed list.
- Web search: "crypto news last hour", "SEC crypto decision", "[coin] news", and the primary source for any candidate event (regulator site, court docket, project's own announcement).

## How it decides to buy

Every box must be ticked, written in the reason field:

1. The pair is in its allowed list: the 10 Alpaca USD pairs with the largest 30-day dollar volume, fixed in the ledger row before it runs.
2. There is one specific event from the last 6 hours, confirmed by a primary source or two independent outlets (`AGENTS.md`, "How a trader behaves", item 4).
3. The event is good for the coin and not yet fully in the price: the model writes why it thinks so.
4. The model writes an expected move. It must be at least 6 times the 50 bps round-trip fee ([Alpaca crypto fees](https://docs.alpaca.markets/us/docs/crypto-fees)).
5. The event is not a new listing, a celebrity post, a token unlock, or a promotion.

## How big

- 10% of its budget per position, at most 4 positions, at most 3 new buys a day.

## How it gets out

- Stop price: 5% below entry.
- Target price: the expected move written at entry, capped at 15% above entry.
- Exit-by time: 5 days after entry; or 24 hours if the model marks it as a short news trade.
- Stops are checked about every 10 minutes and crypto can move fast between checks, so losses can exceed the stop.

## What it never does

- Trades on chart patterns alone.
- Buys memecoins, new tokens, or coins outside the allowed list (`docs/research/13_high_risk_sleeve_evidence.md`, ranks 9 to 11).
- Buys on a pump call, a chat room signal, or a single post.
- Makes more than 3 buys in a day.

## When it wakes

- Every 4 hours, any day: 00:00, 04:00, 08:00, 12:00, 16:00 and 20:00 Eastern.

## What would make us drop it

- The rules in `practice/traders/ROSTER.md`, "How we judge", with C02 (hold bitcoin) as its comparator.
- Also: if its fees over a 20-day check are larger than its gains before fees, it is reviewed early.
