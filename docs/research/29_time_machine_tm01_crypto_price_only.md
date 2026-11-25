# Time machine plan TM01: six AI models trade crypto from prices alone

Made by `timemachine/score_tm01.py` from `timemachine/results_tm01.json`. Do not edit by hand. Pretend money. The plan, with its pass mark fixed before any session ran, is `timemachine/PLAN_TM01_crypto_price_only.md`.

## What was run

- Each model follows the card `practice/traders/B01_crypto_swing_price_only.md` alone in a pretend account of `tm_account_start_usd`, one session per month, a fresh agent per session.
- It wakes at the hours in `tm_crypto_wake_hours_utc`, sees prices up to that minute and nothing later, and may buy any of eight coins. It cannot sell short.
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
| Claude Sonnet 5.5 | 1 of 5 | -$88.92 | -$76.42 | -$64.07 | 0 of 20 | not finished |
| Kimi K3 | 0 of 5 | n/a | n/a | n/a | n/a | not finished |
| Grok 4.7 | 0 of 5 | n/a | n/a | n/a | n/a | not finished |

## Each session

| Month | Model | Gain | Hold | Twin 80th pct | Twins beaten | Buys | Wins | Losses | Fees | Largest drop | Wakes with no pick | Lookups |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| July | Claude Opus 5.5 | not finished | | | | | | | | | | |
| July | GPT-6.2 Sol | not finished | | | | | | | | | | |
| July | Gemini Neon | not finished | | | | | | | | | | |
| July | Claude Sonnet 5.5 | not finished | | | | | | | | | | |
| July | Kimi K3 | not finished | | | | | | | | | | |
| July | Grok 4.7 | not finished | | | | | | | | | | |
| August | Claude Opus 5.5 | not finished | | | | | | | | | | |
| August | GPT-6.2 Sol | not finished | | | | | | | | | | |
| August | Gemini Neon | not finished | | | | | | | | | | |
| August | Claude Sonnet 5.5 | not finished | | | | | | | | | | |
| August | Kimi K3 | not finished | | | | | | | | | | |
| August | Grok 4.7 | not finished | | | | | | | | | | |
| September | Claude Opus 5.5 | not finished | | | | | | | | | | |
| September | GPT-6.2 Sol | not finished | | | | | | | | | | |
| September | Gemini Neon | not finished | | | | | | | | | | |
| September | Claude Sonnet 5.5 | not finished | | | | | | | | | | |
| September | Kimi K3 | not finished | | | | | | | | | | |
| September | Grok 4.7 | not finished | | | | | | | | | | |
| October | Claude Opus 5.5 | -$61.35 | -$76.42 | n/a | n/a of 0 | 6 | 0 | 6 | $7.37 | -8.0% | 55 of 62 | 250 |
| October | GPT-6.2 Sol | -$32.50 | -$76.42 | n/a | n/a of 8 | 4 | 0 | 4 | $4.45 | -3.6% | 58 of 62 | 37 |
| October | Gemini Neon | not finished | | | | | | | | | | |
| October | Claude Sonnet 5.5 | -$88.92 | -$76.42 | -$64.07 | 0 of 20 | 4 | 0 | 4 | $5.79 | -10.5% | 59 of 62 | 29 |
| October | Kimi K3 | not finished | | | | | | | | | | |
| October | Grok 4.7 | not finished | | | | | | | | | | |
| November 1 to 24 | Claude Opus 5.5 | not finished | | | | | | | | | | |
| November 1 to 24 | GPT-6.2 Sol | not finished | | | | | | | | | | |
| November 1 to 24 | Gemini Neon | not finished | | | | | | | | | | |
| November 1 to 24 | Claude Sonnet 5.5 | not finished | | | | | | | | | | |
| November 1 to 24 | Kimi K3 | not finished | | | | | | | | | | |
| November 1 to 24 | Grok 4.7 | not finished | | | | | | | | | | |

## Why each trade was made, and how it ended

One row per buy. "Looked at" is what the trader asked the desk for at that wake, beyond the packet it is always given. No trader in this plan had news, so none looked at news.

### October, Claude Opus 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-10-01 00:00 | BTC/USD | 1Day bars x9 | Uptrend intact, tight week-long base near 83.5-84.5k above 20-day average | stop reached 2026-10-07 13:50 | loss -$4.48 (-1.5%) |
| 2026-10-01 00:00 | ETH/USD | 1Day bars x9 | Tight base 2676-2695 for a week after rally, above 20-day average | stop reached 2026-10-07 02:05 | loss -$8.21 (-3.3%) |
| 2026-10-02 00:00 | AVAX/USD | 1Day bars x8 | Strongest two-week trend, holding a week-long range above its 20-day average; small size for its ~10% daily range | stop reached 2026-10-08 12:45 | loss -$7.10 (-4.7%) |
| 2026-10-10 00:00 | BTC/USD | 1Day bars x8 | Held two-week support near 80.3k with an up close; strongest of the eight in the slide | stop reached 2026-10-15 13:30 | loss -$9.01 (-3.6%) |
| 2026-10-12 00:00 | AVAX/USD | 1Day bars x8 | First pair to reclaim its 7- and 20-day averages after the slide; relative strength leader | stop reached 2026-10-13 00:10 | loss -$17.20 (-8.6%) |
| 2026-10-22 00:00 | BTC/USD | 1Day bars x8 | First daily close back above the 20-day average, higher lows since the 79.7k dip | stop reached 2026-10-22 16:55 | loss -$15.34 (-4.4%) |

### October, GPT-6.2 Sol

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-10-02 12:00 | LTC/USD | packet only | Buy the reclaim of 69 with renewed market breadth and a stop below the prior wake. | stop reached 2026-10-02 18:40 | loss -$9.22 (-3.8%) |
| 2026-10-05 00:00 | LINK/USD | packet only | Buy the recovery out of the 13.80 area with broader confirmation. | stop reached 2026-10-05 14:55 | loss -$9.62 (-4.3%) |
| 2026-10-12 00:00 | AVAX/USD | 1Day bars x3 | Enter the confirmed rebound from the multiday base, with the stop back below the breakout area. | stop reached 2026-10-12 16:50 | loss -$8.77 (-3.8%) |
| 2026-10-21 12:00 | SOL/USD | 1Min bars x1 | Buy the recovered retest with a stop below the observed pullback low. | stop reached 2026-10-22 03:35 | loss -$4.88 (-2.3%) |

### October, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-10-01 00:00 | SOL/USD | 1Day bars x9 | Uptrend, +20% in 14d, consolidating around 118-122 | stop reached 2026-10-08 17:00 | loss -$28.35 (-9.4%) |
| 2026-10-01 00:00 | LINK/USD | 1Day bars x9 | Strongest 7d momentum (+16%), holding near highs | stop reached 2026-10-08 03:10 | loss -$26.48 (-8.8%) |
| 2026-10-05 00:00 | BTC/USD | packet only | Breakout attempt above the 83-85k base, lowest-vol of the group | stop reached 2026-10-08 15:25 | loss -$19.41 (-6.5%) |
| 2026-10-22 00:00 | BTC/USD | 1Day bars x3 | Range-top breakout attempt with a defined 4% risk; target retest of 86-88k | stop reached 2026-10-24 09:10 | loss -$14.67 (-4.9%) |

## What this does not show

- Fills are assumed, not real. Many crypto minutes on the tape are thin, so real fills could be worse.
- The rule against outside knowledge is given by instruction. Each trader's lookups are logged; its memory is not.
- Whether these months fall after each model's knowledge line is UNKNOWN. It has not been measured.
- October was the shakedown month. Its three known differences are listed at the end of the plan.
- With six models, one looking good by luck is likely. That is why the bar is per model and was fixed before the run.
