# Time machine plan TM02: the same six AI models trade crypto with dated headlines added

Made by `timemachine/score_tm01.py` --plan TM02 from `timemachine/results_tm02.json`. Do not edit by hand. Pretend money. The plan, with its pass mark fixed before any session ran, is `timemachine/PLAN_TM02_crypto_with_news.md`.

## What was run

- Each model follows the card `practice/traders/B02_crypto_swing_with_news.md` alone in a pretend account of `tm_account_start_usd`, one session per month, a fresh agent per session.
- It wakes at the hours in `tm_crypto_wake_hours_utc`, sees prices up to that minute and nothing later, and may buy any of eight coins. It cannot sell short. Its packet also holds crypto headlines dated up to that minute, and it may look up more.
- Costs: the fee `practice_crypto_fee_bps_added` and the spread `tm_crypto_half_spread_bps` on each side. Fills are assumed at the next recorded minute's open.
- Yardsticks: holding bitcoin for the month, and 20 random twins per session that buy at the same wakes and sizes with the same exits, a coin drawn at random.
- What counts, from the plan: over the five months added up, a model's gain is above holding bitcoin and above the 80th percentile of its twins. One month alone decides nothing.

## Where each model stands

MEASURED, pretend money, months finished so far. A month is in the sum when the AI session, the hold and all 20 twins are done.

| Model | Months counted | Gain summed | Holding bitcoin, same months | 80th percentile of twins | Twins beaten | Verdict |
|---|---|---|---|---|---|---|
| Claude Opus 5.5 | 0 of 5 | n/a | n/a | n/a | n/a | not finished |
| GPT-6.2 Sol | 0 of 5 | n/a | n/a | n/a | n/a | not finished |
| Gemini Neon | 0 of 5 | n/a | n/a | n/a | n/a | not finished |
| Claude Sonnet 5.5 | 0 of 5 | n/a | n/a | n/a | n/a | not finished |
| Kimi K3 | 0 of 5 | n/a | n/a | n/a | n/a | not finished |
| Grok 4.7 | 0 of 5 | n/a | n/a | n/a | n/a | not finished |

## Did the news help

From the plan: the news helped only if all six models gained more with it than without it over the five months added up. By luck alone that happens about 1 time in 64. MEASURED so far, on the months finished in both plans:

| Model | Months finished in both | With news | Prices alone | Better with news |
|---|---|---|---|---|
| Claude Opus 5.5 | 0 of 5 | n/a | n/a | n/a |
| GPT-6.2 Sol | 0 of 5 | n/a | n/a | n/a |
| Gemini Neon | 0 of 5 | n/a | n/a | n/a |
| Claude Sonnet 5.5 | 0 of 5 | n/a | n/a | n/a |
| Kimi K3 | 0 of 5 | n/a | n/a | n/a |
| Grok 4.7 | 0 of 5 | n/a | n/a | n/a |

Verdict: not finished.

## Each session

| Month | Model | Gain | Hold | Twin 80th pct | Twins beaten | Buys | Wins | Losses | Fees | Largest drop | Wakes with no pick | Lookups | Wakes that showed stock fund movers |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| July | Claude Opus 5.5 | not finished | | | | | | | | | | | |
| July | GPT-6.2 Sol | not finished | | | | | | | | | | | |
| July | Gemini Neon | not finished | | | | | | | | | | | |
| July | Claude Sonnet 5.5 | not finished | | | | | | | | | | | |
| July | Kimi K3 | not finished | | | | | | | | | | | |
| July | Grok 4.7 | not finished | | | | | | | | | | | |
| August | Claude Opus 5.5 | not finished | | | | | | | | | | | |
| August | GPT-6.2 Sol | not finished | | | | | | | | | | | |
| August | Gemini Neon | not finished | | | | | | | | | | | |
| August | Claude Sonnet 5.5 | not finished | | | | | | | | | | | |
| August | Kimi K3 | not finished | | | | | | | | | | | |
| August | Grok 4.7 | not finished | | | | | | | | | | | |
| September | Claude Opus 5.5 | not finished | | | | | | | | | | | |
| September | GPT-6.2 Sol | not finished | | | | | | | | | | | |
| September | Gemini Neon | not finished | | | | | | | | | | | |
| September | Claude Sonnet 5.5 | not finished | | | | | | | | | | | |
| September | Kimi K3 | not finished | | | | | | | | | | | |
| September | Grok 4.7 | not finished | | | | | | | | | | | |
| October | Claude Opus 5.5 | not finished | | | | | | | | | | | |
| October | GPT-6.2 Sol | not finished | | | | | | | | | | | |
| October | Gemini Neon | not finished | | | | | | | | | | | |
| October | Claude Sonnet 5.5 | not finished | | | | | | | | | | | |
| October | Kimi K3 | not finished | | | | | | | | | | | |
| October | Grok 4.7 | not finished | | | | | | | | | | | |
| November 1 to 24 | Claude Opus 5.5 | not finished | | | | | | | | | | | |
| November 1 to 24 | GPT-6.2 Sol | not finished | | | | | | | | | | | |
| November 1 to 24 | Gemini Neon | not finished | | | | | | | | | | | |
| November 1 to 24 | Claude Sonnet 5.5 | not finished | | | | | | | | | | | |
| November 1 to 24 | Kimi K3 | not finished | | | | | | | | | | | |
| November 1 to 24 | Grok 4.7 | not finished | | | | | | | | | | | |

## Why each trade was made, and how it ended

One row per buy. "Looked at" is what the trader asked the desk for at that wake, beyond the packet it is always given. "Headlines it named" is the pick's own list of sources. Headlines are also in every packet, so a trader can use one without a lookup.

## What this does not show

- Fills are assumed, not real. Many crypto minutes on the tape are thin, so real fills could be worse.
- The rule against outside knowledge is given by instruction. Each trader's lookups are logged; its memory is not.
- Whether these months fall after each model's knowledge line is UNKNOWN. It has not been measured.
- A headline can remind a model of what it already knows about that period. That would look like skill and is not. About one headline in eight was edited after it was published; those are marked and the card says not to trade on them.
- For a time on 2026-11-25 the packets of crypto sessions also listed the previous day's movers among stock funds, after those funds were loaded onto the tape. Nothing from the future was shown, and no trader looked up a stock. The last column of the session table counts the wakes this touched. It was switched off at 15:53 UTC.
- With six models, one looking good by luck is likely. That is why the bar is per model and was fixed before the run.
