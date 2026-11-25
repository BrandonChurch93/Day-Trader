# F01 hot_coin_swing

Status: builder settings, 2026-11-25 17:49 UTC. Untested. Market: smaller, faster coins priced on Coinbase. Holding time: a few hours. This card writes down the owner's own method so it can be tested. It is not a claim that it works.

## Where it comes from

The owner described how he traded crypto, in his words on 2026-11-25 (`docs/DECISIONS.md`). STATED by him, not checked against account records:

- He held for a few hours at a time.
- He chose the coins that people were piling into at the time (AI coins, gaming coins) and said the hype was what moved them.
- Prices "would move up and down like peaks of a mountain". He found the pattern with chart tools and bought the dips and sold the peaks, over and over.
- He followed a few callers, Alex Becker among them, and got into some coins early.
- He used leverage. He says $500 became $10,000 several times.

## What it tries to do

Two jobs, tested apart so we can tell which one carries the result:

1. The picker. Once a day it names up to five coins that attention is moving into, from what could be known at that time.
2. The swing trader. On the picked coins only, it buys a dip inside a rising stretch and sells into the next peak, several times a day.

## Why this might work, and why it might not

- MEASURED: these coins move far more in a day than the big ones, so a move can be many times the cost of a trade (`docs/research/42_small_coins_measured.md`).
- MEASURED: no published short-hold price pattern in coins was found to clear a small US account's fees (`docs/research/41_fast_lane_evidence_checked.md`). So if this works, it is the choice of coin and the timing by judgment that do it, not a simple rule.
- MEASURED on our own tests: every model so far bought what had already risen, and none beat a plain rule (`docs/STATUS.md`). A hot coin is by definition one that has already risen. This card has to show the picker is doing more than that, so it is scored against a plain rule that buys the biggest recent risers.
- UNKNOWN: whether his results came from the method or from the years he traded in. In a market where most small coins rise, buying dips with leverage wins almost whatever is picked. The test runs on both a rising stretch and a falling one for that reason.
- MEASURED: the same answers carried at 5x turned gains into losses on bitcoin in our replay (`docs/research/39_leverage_replay_tm03.md`). Leverage comes second, after the method shows something at 1x.

## What it looks at each time it wakes

- The packet: time, cash and holdings, recent bars for the coins on the fast tape, each coin's volume against its own usual volume, and dated headlines.
- Lookups of bars and headlines, within the lookup limit.
- Nothing after the packet time. No web.

## Fixed lines

Set in the plan before any session runs, not here. The plan fixes the coin list, the dates, the costs per coin, the wake times, the most it may hold, and the marks it has to beat.

## How it is judged

- Against holding the same coins in equal parts, against a plain rule that buys the biggest risers, against its own picks with the trade times shuffled, and against the same swing trader on coins drawn at random.
- At 1x first. Then the same answers carried at 2x and 3x with funding and forced close-out, at the three fees in `tm_perp_fee_levels_bps`.
- Only on dates after each model's knowledge ends.
