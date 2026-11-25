# A07 crypto_trend

Status: builder settings, 2026-11-25. Untested. Market: bitcoin and ether against USD on Alpaca. Holding time: days to weeks.

## What it tries to do

It follows the slow trend rule P1 on bitcoin and on ether, half its budget each. The model may only hold less than the rule says, and only when it finds clear, confirmed bad news that the price has not yet shown.

## Why this might work

- MEASURED, not credited: P1 on bitcoin cleared the five pass marks on both price histories only at the lowest venue cost and only in the rerun after the audits, and research recommends it is not credited. In the held-back years most passing bitcoin rules grew less than holding and fell much less (`docs/research/16_rig_audit.md`, `docs/STATUS.md`).
- MEASURED: no trend rule on ether passed (`docs/STATUS.md`).
- MEASURED, in-sample: a trend rule on a liquid coin index beat holding in one study, with a large drop and the lookback picked on the same data ([Le and Ruthbah](https://www.monash.edu/__data/assets/pdf_file/0011/3744821/Trend-following-Strategies-for-Crypto-Investors.pdf), via `docs/research/13_high_risk_sleeve_evidence.md`).
- MEASURED: in the funded OKX test, the model method made +3.72% while bitcoin made +11.63%. Its prompt told it to "return hold when trend, momentum, volatility, or multi-timeframe evidence is mixed" ([OKX study](https://arxiv.org/html/2609.34510v1), via `docs/research/18_ai_systems_with_live_records.md`).
- UNKNOWN: whether a news-based cut adds anything. In our pilot, models acted like the trend rule (`docs/research/14_ai_calls_pilot_02.md`).
- Honest summary: the rule has the best crypto support here, and that support is "smaller drops, less growth". This trader tests only the model's cut.

## What it looks at each time it wakes

- Its holdings and cash.
- Daily bars for BTC/USD and ETH/USD for the last 250 days, with the P1 weight worked out by plain code and shown to the model.
- Alpaca news headlines for crypto since its last wake.
- Web search: "bitcoin news today", "ether news today", "crypto exchange hack", "SEC crypto".

## How it decides to buy

1. The plain code gives P1's weight for each coin: the share of the 20, 50, 100 and 200 day averages the close is above (`research_rig/PREREG_01_daily_crypto_trend.md`, row P1).
2. The target holding is that weight times half the budget, per coin.
3. The model may lower a target to a smaller step (0, 0.25, 0.5 or 0.75 of the rule's weight) only if it names a specific, confirmed event: an exchange failure, a court or regulator action against the coin's main network, a large hack of the network itself. Two independent sources (`AGENTS.md`, "How a trader behaves", item 4).
4. It may never hold more than the rule says.
5. Changes under 5% of the budget are skipped, to save the 25 bps fee per side ([Alpaca crypto fees](https://docs.alpaca.markets/us/docs/crypto-fees)).

## How big

- At most half the budget in each coin, as the rule sets. No other coins.

## How it gets out

- The rule's weight falling is the main exit, at the daily wake.
- Stop price: 20% below the highest price since entry, as a disaster line between wakes.
- Target price: none.
- Exit-by time: none. A model cut ends when the model writes at a later wake that the event has passed, or after 10 days, when the holding goes back to the rule's weight.

## What it never does

- Holds more than P1 says, or any coin other than BTC and ETH.
- Acts on price moves alone. Price is the rule's job.
- Acts on social media sentiment, fear and greed indexes, or ETF flow headlines (`docs/research/19_information_feeds.md` lists these as no usable edge).

## When it wakes

- Once a day at 00:15 UTC, just after the daily bar closes (19:15 Eastern in winter, 20:15 in summer). Plus one news check at 08:00 Eastern that may only lower a target.

## What would make us drop it

- The rules in `practice/traders/ROSTER.md`, "How we judge", with C03 (P1 with no model) as its comparator.
- If it is not ahead of C03 at the end of its trial, the model's cut adds nothing and it is dropped. C03 keeps running.
