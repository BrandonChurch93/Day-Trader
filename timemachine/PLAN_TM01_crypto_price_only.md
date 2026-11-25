# Time machine plan 01: six models, one card, crypto prices only

Written 2026-11-25 15:14 UTC by the builder, before any AI session was started. Pretend money. This is the first run of AI traders in the time machine.

## What is asked

Does a model trading crypto from prices alone, on card `practice/traders/B01_crypto_swing_price_only.md`, beat holding bitcoin and beat a random trader of the same size and pace? And does the time machine work with real AI traders?

## Traders

Six sessions per month, one model each, the same card and the same brief (`timemachine/TRADER_BRIEF.md`):

| Trial | Trader id | Model |
|---|---|---|
| TM01-a | B01-OPUS | Claude Opus 5.5 |
| TM01-b | B01-SOL | GPT-6.2 Sol |
| TM01-c | B01-NEON | Gemini Neon |
| TM01-d | B01-SONNET | Claude Sonnet 5.5 |
| TM01-e | B01-KIMI | Kimi K3 |
| TM01-f | B01-GROK | Grok 4.7 |

## Dates

- Months, each a separate session that starts with a fresh `tm_account_start_usd`: July, August, September, October 2026, and 2026-11-01 to 2026-11-24.
- October runs first, as the shakedown. If the machinery fails in October, it is fixed and October is run again as a new session that is also counted in `timemachine/SESSIONS.jsonl`.
- These months are after the date the repo has used as the models' knowledge line (2026-07-01). That date is not measured for these six models. UNKNOWN. Measuring it is item 5 in `docs/QUEUE.md`.

## Costs

The fee is `practice_crypto_fee_bps_added` per side. The spread is `tm_crypto_half_spread_bps` per side. Fills are at the open of the next recorded minute. No cap on order size against volume (`tm_crypto_max_share_of_minute_volume`).

## Yardsticks

- Hold: buy bitcoin at the first wake and hold to the end of the month.
- Random twins: for each finished AI session, 20 twins (`timemachine/run_code_trader.py twin`, seeds 1 to 20). A twin buys at the same wakes, the same dollars, a pair drawn at random, with the same stop and target distances and holding time.

## What would count, fixed now

For one model, over the five months added up:

1. Its gain in dollars is above the gain from holding bitcoin, and
2. its gain is above the 80th percentile of its own 20 twins' gains added up over the same months.

Both, or it has shown nothing. A model that clears both gets a longer test with the same card: more months as the tape grows, then the practice desk. It does not mean real money.

One month alone decides nothing. The October numbers are reported as they come, labelled as one month.

## Also reported

Number of trades, win rate, largest drop during a month, fees paid, how many picks were refused and why, how many wakes the model did nothing, and anything that broke.

## Known weak points

- The no-web rule is by instruction. A trader could break it. Each trader's lookups are logged by the server, and its report is read for signs of outside knowledge.
- Six models and five months is 30 sessions. With that many, one model looking good by luck is likely. That is why the twin test is per model and the bar is set before the run.
- Crypto minutes on this tape are often thin. Real fills could be worse than assumed.

## What changed after the first sessions started, and what did not

Written 2026-11-25 15:22 UTC, after three of the six October sessions had finished. The pass mark, months, card, costs and yardsticks above are unchanged.

- The October sessions were made with the benchmark shown in the packet set to AVAX/USD by mistake (the first pair on the list). The yardstick of this plan is the separate hold of bitcoin, so the scoring is not touched, but all six models saw an AVAX figure in their packets in October. Fixed in `timemachine/session.py` for the other months: a coin session is shown bitcoin.
- In October a lookup of half-hour bars for a coin came back empty, because the tape holds minutes and days. Models that asked lost a lookup. Fixed for the other months: half-hour and hour bars are built from the minutes, never including a bucket still open.
- While the October sessions ran, the tape was extended backwards (days to 2024-01-01, minutes to 2026-01-01). Nothing after a session's clock was added, but a model that looked far back late in its session could see more history than one that looked early. The other months all run on the extended tape.
- Because of these three points October stays what the plan already called it: the shakedown month. It is still counted in the five-month sum, as fixed above.
- At 15:28 UTC dated headlines were recorded onto the tape for a later plan. From 15:29 UTC a session shows headlines only if it was made with `--news`; every session of this plan was made without it. Checked at 15:30 UTC (MEASURED): of the 551 packets handed out so far in this plan, none held a headline, and no trader had asked for news.
- 2026-11-25 15:38 UTC: two traders reported buy fills stamped with their wake time and asked whether that was a look ahead. MEASURED from the code: the packet holds only minutes that had finished before the wake, and the fill is the open of the first minute that starts at or after the wake, so the trader had not seen it. One sentence saying so was added to `timemachine/TRADER_BRIEF.md`. No rule and no number changed. A real desk would be slower: the model takes time to answer, so the real fill would be a few minutes later than the replay assumes.
- 2026-11-25 15:53 UTC: after stock funds were loaded onto the tape (about 15:35 UTC), the packets of crypto sessions also listed the previous day's biggest movers and most traded among those funds. MEASURED: it showed nothing from the future (a fund's day is visible only after its close), and no trader looked up a stock. It is still outside what this plan describes, so it was switched off: a crypto session now shows nothing about stocks and refuses stock lookups. Sessions that ran across that time saw the fund movers at some wakes. The count for each session is in the results table.
