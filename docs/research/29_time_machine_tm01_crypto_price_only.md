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
| GPT-6.2 Sol | 1 of 5 | -$32.50 | -$76.42 | -$21.92 | 0 of 20 | not finished |
| Gemini Neon | 0 of 5 | n/a | n/a | n/a | n/a | not finished |
| Claude Sonnet 5.5 | 1 of 5 | -$88.92 | -$76.42 | -$64.07 | 0 of 20 | not finished |
| Kimi K3 | 0 of 5 | n/a | n/a | n/a | n/a | not finished |
| Grok 4.7 | 0 of 5 | n/a | n/a | n/a | n/a | not finished |

## Each session

| Month | Model | Gain | Hold | Twin 80th pct | Twins beaten | Buys | Wins | Losses | Fees | Largest drop | Wakes with no pick | Lookups |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| July | Claude Opus 5.5 | not finished | | | | | | | | | | |
| July | GPT-6.2 Sol | -$2.78 | $69.81 | n/a | n/a of 0 | 5 | 2 | 3 | $6.16 | -1.9% | 57 of 62 | 92 |
| July | Gemini Neon | not finished | | | | | | | | | | |
| July | Claude Sonnet 5.5 | -$25.70 | $69.81 | n/a | n/a of 0 | 3 | 0 | 3 | $4.45 | -2.9% | 58 of 62 | 20 |
| July | Kimi K3 | not finished | | | | | | | | | | |
| July | Grok 4.7 | not finished | | | | | | | | | | |
| August | Claude Opus 5.5 | not finished | | | | | | | | | | |
| August | GPT-6.2 Sol | $4.17 | $245.33 | n/a | n/a of 0 | 3 | 1 | 2 | $3.87 | -1.2% | 59 of 62 | 31 |
| August | Gemini Neon | not finished | | | | | | | | | | |
| August | Claude Sonnet 5.5 | $51.44 | $245.33 | n/a | n/a of 0 | 6 | 4 | 2 | $7.15 | -1.5% | 51 of 62 | 53 |
| August | Kimi K3 | not finished | | | | | | | | | | |
| August | Grok 4.7 | not finished | | | | | | | | | | |
| September | Claude Opus 5.5 | not finished | | | | | | | | | | |
| September | GPT-6.2 Sol | not finished | | | | | | | | | | |
| September | Gemini Neon | not finished | | | | | | | | | | |
| September | Claude Sonnet 5.5 | not finished | | | | | | | | | | |
| September | Kimi K3 | not finished | | | | | | | | | | |
| September | Grok 4.7 | not finished | | | | | | | | | | |
| October | Claude Opus 5.5 | -$61.35 | -$76.42 | n/a | n/a of 4 | 6 | 0 | 6 | $7.37 | -8.0% | 55 of 62 | 250 |
| October | GPT-6.2 Sol | -$32.50 | -$76.42 | -$21.92 | 0 of 20 | 4 | 0 | 4 | $4.45 | -3.6% | 58 of 62 | 37 |
| October | Gemini Neon | -$162.36 | -$76.42 | n/a | n/a of 0 | 8 | 0 | 8 | $12.53 | -17.6% | 56 of 62 | 31 |
| October | Claude Sonnet 5.5 | -$88.92 | -$76.42 | -$64.07 | 0 of 20 | 4 | 0 | 4 | $5.79 | -10.5% | 59 of 62 | 29 |
| October | Kimi K3 | not finished | | | | | | | | | | |
| October | Grok 4.7 | -$37.59 | -$76.42 | n/a | n/a of 3 | 3 | 0 | 3 | $5.42 | -5.7% | 59 of 62 | 116 |
| November 1 to 24 | Claude Opus 5.5 | not finished | | | | | | | | | | |
| November 1 to 24 | GPT-6.2 Sol | not finished | | | | | | | | | | |
| November 1 to 24 | Gemini Neon | not finished | | | | | | | | | | |
| November 1 to 24 | Claude Sonnet 5.5 | not finished | | | | | | | | | | |
| November 1 to 24 | Kimi K3 | not finished | | | | | | | | | | |
| November 1 to 24 | Grok 4.7 | not finished | | | | | | | | | | |

## Why each trade was made, and how it ended

One row per buy. "Looked at" is what the trader asked the desk for at that wake, beyond the packet it is always given. No trader in this plan had news, so none looked at news.

### July, GPT-6.2 Sol

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-07-02 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x2 | Buy the first post-breakout consolidation with defined risk below the 76.44 hourly low. | target reached 2026-07-02 10:40 | win $9.49 (+3.6%) |
| 2026-07-09 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x2 | Take a small rebound swing, invalidated below the late hourly base near 76.85. | time limit 2026-07-10 12:02 | win $2.36 (+1.2%) |
| 2026-07-15 00:00 | ETH/USD | 1Day bars x3, 1Hour bars x4 | Buy the relative leader for continuation, with the stop below the afternoon consolidation. | stop reached 2026-07-16 23:25 | loss -$6.92 (-2.5%) |
| 2026-07-19 00:00 | LTC/USD | 1Day bars x1, 1Hour bars x2 | Enter above the post-breakout base, with the stop below the 46.68 hourly shelf. | stop reached 2026-07-20 08:55 | loss -$4.71 (-1.9%) |
| 2026-07-21 12:00 | XRP/USD | 1Day bars x2, 1Hour bars x4 | Buy a consolidation above the breakout, with the stop below the older 1.120 pivot. | time limit 2026-07-23 12:00 | loss -$3.01 (-1.2%) |

### July, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-07-02 12:00 | SOL/USD | 1Day bars x2, 1Hour bars x1 | Breakout above week-long resistance near 79; hourly closes holding above it. | time limit 2026-07-06 00:00 | loss -$4.31 (-1.4%) |
| 2026-07-15 00:00 | ETH/USD | 1Day bars x2, 1Hour bars x1 | Daily close above 1848 resistance after repeated tests; hourly bars holding 1870-1890. | stop reached 2026-07-17 00:35 | loss -$8.17 (-2.7%) |
| 2026-07-21 12:00 | ETH/USD | 1Day bars x1, 1Hour bars x1 | ETH above last week's 1894 high with BTC leading through range top; hourly higher highs and higher lows. | stop reached 2026-07-24 00:40 | loss -$13.22 (-4.4%) |

### August, GPT-6.2 Sol

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-08-03 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x1 | Buy the daily support reclaim while hourly lows hold above the 72.62 base. | stop reached 2026-08-03 06:45 | loss -$6.50 (-2.2%) |
| 2026-08-09 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x1 | The post-breakout pullback stayed above the pre-breakout 75.29 shelf and recovered to 75.95. | stop reached 2026-08-11 15:00 | loss -$4.29 (-1.7%) |
| 2026-08-21 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x1 | Buy the higher-post-breakout-base continuation while BTC and ETH also advance. | target reached 2026-08-21 22:45 | win $14.96 (+6.8%) |

### August, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-08-07 12:00 | BTC/USD | 1Day bars x4, 1Hour bars x1 | Higher lows, price at 65k, risk about 3% to stop vs about 3% to target. | time limit 2026-08-11 00:00 | loss -$7.05 (-2.3%) |
| 2026-08-12 12:00 | LINK/USD | 1Hour bars x1 | Breakout held a full day with rising hourly lows; stop under the 8.53 shelf. | target reached 2026-08-15 02:40 | win $20.85 (+8.3%) |
| 2026-08-19 12:00 | LINK/USD | 1Day bars x1, 1Hour bars x1 | Four-day base at 9.4-9.55 broken upward to 9.76; stop under base. | target reached 2026-08-19 20:45 | win $14.66 (+5.9%) |
| 2026-08-20 00:00 | BTC/USD | 1Hour bars x2 | Range top 66.5k broken and 68-70k held for 8 hours; stop under the 67.8k consolidation low. | target reached 2026-08-21 01:50 | win $16.47 (+8.2%) |
| 2026-08-20 00:00 | ETH/USD | 1Hour bars x2 | Second leg to 2.25k held; higher beta than BTC; stop under the 2.17k hold zone. | stop reached 2026-08-22 10:20 | win $8.52 (+5.7%) |
| 2026-08-27 12:00 | SOL/USD | packet only | Held a 12h base above the prior 102.9 high; stop under the base. | stop reached 2026-08-28 14:05 | loss -$2.01 (-0.8%) |

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

### October, Gemini Neon

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-10-01 12:00 | BTC/USD | packet only | 9-day bull flag above SMA20 (81.3k) stabilizing at 83.88k; stop at 80.5k below SMA20. | stop reached 2026-10-08 17:25 | loss -$16.72 (-4.8%) |
| 2026-10-01 12:00 | ETH/USD | packet only | Tight 7-day range above SMA20 (2610) reclaiming SMA5 and SMA10 at 2706; stop at 2580. | stop reached 2026-10-07 10:35 | loss -$18.91 (-5.4%) |
| 2026-10-02 12:00 | SOL/USD | 1Day bars x2 | Breaking out of a 4-day higher-low base at 121.85, 2.5% below 20-day high (124.96) and well above SMA20 (112.23); stop at 113.50. | stop reached 2026-10-08 11:20 | loss -$21.95 (-7.5%) |
| 2026-10-09 12:00 | BTC/USD | packet only | Rebounded +1.81% to 83,173 after testing SMA50 (80,527) with an 80,319 hammer low; stop at 79,800 below 20-day low. | stop reached 2026-10-15 13:55 | loss -$16.62 (-4.7%) |
| 2026-10-09 12:00 | SOL/USD | packet only | High-volume hammer reversal off SMA50 (107.79, low 105.60), bouncing +1.55% to 111.25; stop at 104.50 below climax low. | stop reached 2026-10-13 00:10 | loss -$20.77 (-6.9%) |
| 2026-10-12 00:00 | AVAX/USD | 1Day bars x4 | Relative-strength leader reclaiming SMA5 (10.56), SMA10 (10.86), and SMA20 (10.84) at 10.937 on expanding volume; stop at 10.05. | stop reached 2026-10-13 00:20 | loss -$25.74 (-9.2%) |
| 2026-10-16 12:00 | BTC/USD | packet only | Two consecutive 12h gains reclaiming SMA5 (82,446) off the Oct 15 hammer low (79,692); stop at 78,500 gives 1.8x ATR room. | stop reached 2026-10-29 23:40 | loss -$21.69 (-5.7%) |
| 2026-10-21 12:00 | ETH/USD | 1Day bars x1 | Reclaiming SMA5 (2,416) and SMA10 (2,441) at 2,466 on expanding volume off a 2,322-2,326 double bottom as BTC clears SMA20; stop at 2,310. | stop reached 2026-10-24 15:10 | loss -$19.96 (-7.1%) |

### October, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-10-01 00:00 | SOL/USD | 1Day bars x9 | Uptrend, +20% in 14d, consolidating around 118-122 | stop reached 2026-10-08 17:00 | loss -$28.35 (-9.4%) |
| 2026-10-01 00:00 | LINK/USD | 1Day bars x9 | Strongest 7d momentum (+16%), holding near highs | stop reached 2026-10-08 03:10 | loss -$26.48 (-8.8%) |
| 2026-10-05 00:00 | BTC/USD | packet only | Breakout attempt above the 83-85k base, lowest-vol of the group | stop reached 2026-10-08 15:25 | loss -$19.41 (-6.5%) |
| 2026-10-22 00:00 | BTC/USD | 1Day bars x3 | Range-top breakout attempt with a defined 4% risk; target retest of 86-88k | stop reached 2026-10-24 09:10 | loss -$14.67 (-4.9%) |

### October, Grok 4.7

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-10-01 00:00 | BTC/USD | 1Day bars x8 | Cleanest uptrend, holding above the late-September base, stop under the 21 September low. | sold by the trader 2026-10-08 12:00 | loss -$8.18 (-2.0%) |
| 2026-10-01 00:00 | ETH/USD | 1Day bars x8 | Same impulse-and-base structure as bitcoin, second leader, stop under the 20 September low. | stop reached 2026-10-07 13:20 | loss -$15.69 (-5.2%) |
| 2026-10-25 00:00 | BTC/USD | 1Day bars x8 | Second spring under 79700 closed back above it, stop under the 24 October wick, target above the failed breakout. | stop reached 2026-10-29 22:10 | loss -$13.72 (-3.4%) |

## What this does not show

- Fills are assumed, not real. Many crypto minutes on the tape are thin, so real fills could be worse.
- The rule against outside knowledge is given by instruction. Each trader's lookups are logged; its memory is not.
- Whether these months fall after each model's knowledge line is UNKNOWN. It has not been measured.
- October was the shakedown month. Its three known differences are listed at the end of the plan.
- With six models, one looking good by luck is likely. That is why the bar is per model and was fixed before the run.
