# Time machine plan 02: the same six models, with the news added

Written 2026-11-25 15:33 UTC by the builder, before any session of this plan was started. Pretend money.

## What is asked

Two things, in the owner's words of 2026-11-25: "see what actually works and why it worked. Did it look at the news?"

1. Does a model that reads dated crypto headlines as well as prices, on card `practice/traders/B02_crypto_swing_with_news.md`, beat holding bitcoin and beat a random trader of the same size and pace?
2. Does the same model do better with the news than without it? The without is plan `timemachine/PLAN_TM01_crypto_price_only.md`: same models, same months, same fixed lines, same costs.

## Traders

Six sessions per month, one model each, a fresh agent per session, the same card and the same brief (`timemachine/TRADER_BRIEF.md`). Sessions are made with `--news`.

| Trial | Trader id | Model |
|---|---|---|
| TM02-a | B02-OPUS | Claude Opus 5.5 |
| TM02-b | B02-SOL | GPT-6.2 Sol |
| TM02-c | B02-NEON | Gemini Neon |
| TM02-d | B02-SONNET | Claude Sonnet 5.5 |
| TM02-e | B02-KIMI | Kimi K3 |
| TM02-f | B02-GROK | Grok 4.7 |

## Dates, costs, yardsticks

The same as plan TM01, word for word: the months July, August, September, October 2026 and 2026-11-01 to 2026-11-24, each a separate session with a fresh `tm_account_start_usd`; the fee `practice_crypto_fee_bps_added` and the spread `tm_crypto_half_spread_bps` per side; fills at the open of the next recorded minute; holding bitcoin for the month; 20 random twins per session (seeds 1 to 20).

## The news

- Headlines and summaries from three public crypto news sites, recorded on the tape with each site's own publish time to the second (`python3 timemachine/record.py crypto-news`). 5,941 items from 2026-06-01 to 2026-11-24 (MEASURED by the recorder).
- A headline is shown only at or after its publish time.
- About one in eight items was edited after it was published and the text kept is the edited one. Those are marked `edited_later`, and the card tells the trader not to trade on them.

## What would count, fixed now

For one model, over the five months added up:

1. Its gain in dollars is above the gain from holding bitcoin, and
2. its gain is above the 80th percentile of its own 20 twins' gains added up over the same months.

Both, or it has shown nothing. The same bar as plan TM01.

For the question "did the news help": the news is said to have helped only if all six models gained more over the five months on this card than they did on card B01 in plan TM01. Six of six by chance alone is 1 in 64. Anything less is reported as it is and called not shown.

## Also reported

For every buy: which headlines the trader named as its reason, what else it looked up, and how the trade ended. Number of trades, win rate, largest drop, fees, refused picks, wakes with no pick.

## Known weak points

- The same as plan TM01: assumed fills, thin crypto minutes, the no-web rule by instruction, the models' knowledge lines not measured.
- New here: a headline can cue a model's memory of the period. If these months are before a model's knowledge line, a good result here may be memory. This plan cannot tell the two apart. Measuring the knowledge lines (`docs/QUEUE.md`) can.
- The two plans were run hours apart by different fresh agents. A model's run-to-run variation is not measured, so a small difference between the two cards for one model means little. That is why the news question is asked across all six.
