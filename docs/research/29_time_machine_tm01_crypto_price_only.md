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
| Claude Opus 5.5 | 3 of 5 | -$69.01 | $238.72 | -$83.74 | 17 of 20 | not finished |
| GPT-6.2 Sol | 1 of 5 | -$32.50 | -$76.42 | -$21.92 | 0 of 20 | not finished |
| Gemini Neon | 5 of 5 | $12.96 | $67.51 | $38.86 | 12 of 20 | has shown nothing |
| Claude Sonnet 5.5 | 1 of 5 | -$88.92 | -$76.42 | -$64.07 | 0 of 20 | not finished |
| Kimi K3 | 2 of 5 | -$134.62 | -$6.61 | -$110.74 | 11 of 20 | not finished |
| Grok 4.7 | 1 of 5 | -$37.59 | -$76.42 | -$34.52 | 14 of 20 | not finished |

## Each session

| Month | Model | Gain | Hold | Twin 80th pct | Twins beaten | Buys | Wins | Losses | Fees | Largest drop | Wakes with no pick | Lookups | Wakes that showed stock fund movers | Wakes answered unseen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| July | Claude Opus 5.5 | -$50.63 | $69.81 | -$40.63 | 9 of 20 | 10 | 3 | 6 | $14.66 | -8.3% | 44 of 62 | 18 | 28 of 62 | 0 |
| July | GPT-6.2 Sol | -$2.78 | $69.81 | n/a | n/a of 0 | 5 | 2 | 3 | $6.16 | -1.9% | 57 of 62 | 92 | 10 of 62 | 0 |
| July | Gemini Neon | $57.38 | $69.81 | $32.76 | 18 of 20 | 7 | 4 | 1 | $9.37 | -6.0% | 49 of 62 | 36 | 37 of 62 | 0 |
| July | Claude Sonnet 5.5 | -$25.70 | $69.81 | n/a | n/a of 0 | 3 | 0 | 3 | $4.45 | -2.9% | 58 of 62 | 20 | 0 of 62 | 0 |
| July | Kimi K3 | -$24.12 | $69.81 | -$14.96 | 9 of 20 | 12 | 5 | 7 | $15.23 | -4.5% | 47 of 62 | 22 | 36 of 62 | 1 |
| July | Grok 4.7 | -$9.66 | $69.81 | n/a | n/a of 0 | 8 | 3 | 5 | $12.66 | -3.5% | 54 of 62 | 93 | 31 of 62 | 0 |
| August | Claude Opus 5.5 | $42.97 | $245.33 | $27.21 | 20 of 20 | 8 | 5 | 3 | $11.39 | -3.5% | 46 of 62 | 24 | 23 of 62 | 0 |
| August | GPT-6.2 Sol | $4.17 | $245.33 | n/a | n/a of 0 | 3 | 1 | 2 | $3.87 | -1.2% | 59 of 62 | 31 | 0 of 62 | 0 |
| August | Gemini Neon | $157.01 | $245.33 | $143.87 | 17 of 20 | 9 | 5 | 3 | $13.84 | -5.1% | 46 of 62 | 66 | 34 of 62 | 0 |
| August | Claude Sonnet 5.5 | $51.44 | $245.33 | n/a | n/a of 0 | 6 | 4 | 2 | $7.15 | -1.5% | 51 of 62 | 53 | 10 of 62 | 0 |
| August | Kimi K3 | $22.28 | $245.33 | n/a | n/a of 0 | 6 | 3 | 2 | $8.95 | -2.4% | 50 of 62 | 20 | 32 of 62 | 0 |
| August | Grok 4.7 | -$1.60 | $245.33 | n/a | n/a of 0 | 3 | 1 | 2 | $4.76 | -1.9% | 57 of 62 | 60 | 30 of 62 | 0 |
| September | Claude Opus 5.5 | -$34.87 | $59.89 | n/a | n/a of 2 | 11 | 4 | 7 | $15.45 | -7.0% | 47 of 60 | 25 | 44 of 60 | 0 |
| September | GPT-6.2 Sol | $6.89 | $59.89 | n/a | n/a of 0 | 5 | 3 | 2 | $5.53 | -0.5% | 55 of 60 | 90 | 60 of 60 | 0 |
| September | Gemini Neon | $45.43 | $59.89 | $87.67 | 9 of 20 | 11 | 5 | 4 | $14.23 | -7.0% | 47 of 60 | 55 | 24 of 60 | 0 |
| September | Claude Sonnet 5.5 | -$0.27 | $59.89 | n/a | n/a of 0 | 3 | 2 | 1 | $3.51 | -1.8% | 56 of 60 | 39 | 55 of 60 | 1 |
| September | Kimi K3 | -$29.77 | $59.89 | n/a | n/a of 0 | 8 | 2 | 6 | $11.86 | -3.1% | 50 of 60 | 21 | 0 of 60 | 0 |
| September | Grok 4.7 | $0.66 | $59.89 | n/a | n/a of 0 | 2 | 1 | 1 | $3.26 | -1.1% | 58 of 60 | 61 | 0 of 60 | 0 |
| October | Claude Opus 5.5 | -$61.35 | -$76.42 | -$41.50 | 11 of 20 | 6 | 0 | 6 | $7.37 | -8.0% | 55 of 62 | 250 | 0 of 62 | 0 |
| October | GPT-6.2 Sol | -$32.50 | -$76.42 | -$21.92 | 0 of 20 | 4 | 0 | 4 | $4.45 | -3.6% | 58 of 62 | 37 | 0 of 62 | 0 |
| October | Gemini Neon | -$162.36 | -$76.42 | -$131.36 | 2 of 20 | 8 | 0 | 8 | $12.53 | -17.6% | 56 of 62 | 31 | 0 of 62 | 0 |
| October | Claude Sonnet 5.5 | -$88.92 | -$76.42 | -$64.07 | 0 of 20 | 4 | 0 | 4 | $5.79 | -10.5% | 59 of 62 | 29 | 0 of 62 | 1 |
| October | Kimi K3 | -$110.50 | -$76.42 | -$94.83 | 8 of 20 | 12 | 0 | 9 | $14.50 | -13.3% | 54 of 62 | 57 | 46 of 62 | 0 |
| October | Grok 4.7 | -$37.59 | -$76.42 | -$34.52 | 14 of 20 | 3 | 0 | 3 | $5.42 | -5.7% | 59 of 62 | 116 | 0 of 62 | 0 |
| November 1 to 24 | Claude Opus 5.5 | -$45.01 | -$231.10 | n/a | n/a of 0 | 11 | 3 | 8 | $13.17 | -6.9% | 38 of 48 | 36 | 0 of 48 | 0 |
| November 1 to 24 | GPT-6.2 Sol | -$10.01 | -$231.10 | n/a | n/a of 0 | 2 | 0 | 2 | $1.98 | -1.0% | 46 of 48 | 20 | 0 of 48 | 0 |
| November 1 to 24 | Gemini Neon | -$84.50 | -$231.10 | -$12.58 | 0 of 20 | 10 | 0 | 10 | $14.07 | -10.9% | 39 of 48 | 71 | 0 of 48 | 0 |
| November 1 to 24 | Claude Sonnet 5.5 | $0.07 | -$231.10 | n/a | n/a of 0 | 4 | 2 | 2 | $5.26 | -2.5% | 43 of 48 | 37 | 43 of 48 | 1 |
| November 1 to 24 | Kimi K3 | -$36.20 | -$231.10 | n/a | n/a of 0 | 4 | 0 | 4 | $5.92 | -3.6% | 0 of 48 | 24 | 0 of 48 | 0 |
| November 1 to 24 | Grok 4.7 | -$23.09 | -$231.10 | n/a | n/a of 0 | 1 | 0 | 1 | $1.95 | -2.3% | 47 of 48 | 55 | 0 of 48 | 0 |

## Why each trade was made, and how it ended

One row per buy. "Looked at" is what the trader asked the desk for at that wake, beyond the packet it is always given. No trader in this plan had news, so none looked at news.

### July, Claude Opus 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-07-01 12:00 | SOL/USD | 1Hour bars x1 | Strongest of the eight over the past week, higher lows on hourly bars. | target reached 2026-07-02 10:35 | win $17.54 (+7.0%) |
| 2026-07-02 12:00 | BTC/USD | 1Hour bars x2 | Hourly higher lows since July 1, bounce off the 58k double bottom, about 4.5 percent room to resistance. | stop reached 2026-07-06 12:05 | win $0.74 (+0.2%) |
| 2026-07-03 12:00 | ETH/USD | 1Day bars x1, 1Hour bars x1 | Leading the rebound, broke out of a triple-bottom base, hourly trend up. | stop reached 2026-07-08 08:20 | loss -$1.80 (-0.7%) |
| 2026-07-07 00:00 | BTC/USD | 1Hour bars x1 | Dip to 61.25k was bought back within hours to a new rebound high; trend of higher daily closes since July 1. | stop reached 2026-07-08 13:50 | loss -$13.07 (-4.3%) |
| 2026-07-09 12:00 | BTC/USD | packet only | Higher lows on the daily rebound, range holding, stop placed outside the range noise. | stop reached 2026-07-17 13:45 | loss -$3.62 (-1.0%) |
| 2026-07-15 00:00 | ETH/USD | 1Hour bars x1 | Broke above the June 15 high and held the breakout on hourly bars; room to the 2000 area. | stop reached 2026-07-17 13:10 | loss -$14.39 (-4.8%) |
| 2026-07-16 00:00 | LINK/USD | 1Day bars x1 | Daily breakout to a six-week high with higher lows all month; about 7 percent room to the early-June level. | stop reached 2026-07-17 13:10 | loss -$15.37 (-6.1%) |
| 2026-07-18 00:00 | BTC/USD | 1Day bars x1, 1Hour bars x1 | Rising daily lows all month, dip to 62.45k bought straight back; stop placed outside the daily range. | stop reached 2026-07-28 01:10 | loss -$21.93 (-3.4%) |
| 2026-07-19 00:00 | ETH/USD | 1Day bars x1 | Rising daily lows, breakout retest held above 1800; wide stop under July 13 low. | time limit 2026-07-31 12:00 | win $1.28 (+0.4%) |
| 2026-07-22 00:00 | BTC/USD | packet only | Holding above the mid-June highs, a seven-week high, rising daily lows all month. | open at the end | still held at the end or not filled |

### July, GPT-6.2 Sol

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-07-02 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x2 | Buy the first post-breakout consolidation with defined risk below the 76.44 hourly low. | target reached 2026-07-02 10:40 | win $9.49 (+3.6%) |
| 2026-07-09 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x2 | Take a small rebound swing, invalidated below the late hourly base near 76.85. | time limit 2026-07-10 12:02 | win $2.36 (+1.2%) |
| 2026-07-15 00:00 | ETH/USD | 1Day bars x3, 1Hour bars x4 | Buy the relative leader for continuation, with the stop below the afternoon consolidation. | stop reached 2026-07-16 23:25 | loss -$6.92 (-2.5%) |
| 2026-07-19 00:00 | LTC/USD | 1Day bars x1, 1Hour bars x2 | Enter above the post-breakout base, with the stop below the 46.68 hourly shelf. | stop reached 2026-07-20 08:55 | loss -$4.71 (-1.9%) |
| 2026-07-21 12:00 | XRP/USD | 1Day bars x2, 1Hour bars x4 | Buy a consolidation above the breakout, with the stop below the older 1.120 pivot. | time limit 2026-07-23 12:00 | loss -$3.01 (-1.2%) |

### July, Gemini Neon

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-07-01 00:00 | SOL/USD | 1Day bars x8, 1Hour bars x2 | Strongest daily uptrend and quick recovery off 71.31 low | target reached 2026-07-02 10:50 | win $23.59 (+9.4%) |
| 2026-07-02 00:00 | BTC/USD | 1Hour bars x3 | Pullback to 60k breakout shelf after 57.7k double-bottom reversal | stop reached 2026-07-28 01:10 | win $13.82 (+4.6%) |
| 2026-07-02 12:00 | ETH/USD | 1Hour bars x3 | Range breakout above 1644 with strong hourly trend and room to 1800 | stop reached 2026-07-17 13:35 | win $31.48 (+9.0%) |
| 2026-07-03 00:00 | SOL/USD | 1Hour bars x2 | Bull flag above 80.0 support after breaking 30-day high | stop reached 2026-07-08 08:35 | loss -$13.85 (-4.9%) |
| 2026-07-10 12:00 | LINK/USD | 1Day bars x2, 1Hour bars x2 | Strong higher-low reversal from 7.52 back to 8.00 resistance alongside BTC breakout | stop reached 2026-07-28 13:40 | win $6.14 (+2.0%) |
| 2026-07-18 00:00 | ETH/USD | 1Hour bars x3 | Successful retest of 1800 breakout support and hourly SMA reclaim | open at the end | still held at the end or not filled |
| 2026-07-29 00:00 | BTC/USD | 1Hour bars x3 | Post-sweep reclaim of 63.8k and hourly SMAs with defined risk below 62,665 | open at the end | still held at the end or not filled |

### July, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-07-02 12:00 | SOL/USD | 1Day bars x2, 1Hour bars x1 | Breakout above week-long resistance near 79; hourly closes holding above it. | time limit 2026-07-06 00:00 | loss -$4.31 (-1.4%) |
| 2026-07-15 00:00 | ETH/USD | 1Day bars x2, 1Hour bars x1 | Daily close above 1848 resistance after repeated tests; hourly bars holding 1870-1890. | stop reached 2026-07-17 00:35 | loss -$8.17 (-2.7%) |
| 2026-07-21 12:00 | ETH/USD | 1Day bars x1, 1Hour bars x1 | ETH above last week's 1894 high with BTC leading through range top; hourly higher highs and higher lows. | stop reached 2026-07-24 00:40 | loss -$13.22 (-4.4%) |

### July, Kimi K3

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-07-01 12:00 | BTC/USD | 1Hour bars x1 | sweep of June lows then 8-hour hold above 58,400; higher intraday highs into 59,382 | target reached 2026-07-01 21:35 | win $7.23 (+2.9%) |
| 2026-07-02 00:00 | BTC/USD | 1Hour bars x1 | strong impulse off the sweep low, shallow pullback holding above 59,900 retest of prior intraday highs | target reached 2026-07-02 09:55 | win $3.59 (+1.4%) |
| 2026-07-02 12:00 | BTC/USD | 1Day bars x2, 1Hour bars x1 | reclaim of June 29 high 60,721; daily reversal candle; stop under the broken shelf, target under June 24 high 63,131 | stop reached 2026-07-04 06:25 | win $2.35 (+0.9%) |
| 2026-07-02 12:00 | SOL/USD | 1Day bars x2, 1Hour bars x1 | strongest alt, daily higher highs, fresh 10:00 breakout from 77-78.5 intraday base; stop back inside the base | stop reached 2026-07-08 00:00 | loss -$6.89 (-2.8%) |
| 2026-07-05 00:00 | BTC/USD | 1Day bars x1 | third green daily off the July 1 low, July 4 traded above June 24 high and closed at 63,089 on the doorstep; stop under the day's low | stop reached 2026-07-06 05:30 | loss -$2.47 (-1.0%) |
| 2026-07-06 00:00 | ETH/USD | 1Hour bars x2 | daily close confirmed above June 22 high 1,777.5, drive to 1,806, base 1,755-1,790 below | stop reached 2026-07-06 12:05 | loss -$7.92 (-3.2%) |
| 2026-07-09 00:00 | BTC/USD | 1Hour bars x1 | flush to 61,460 then eight hours of higher lows at the bottom of the range; half size for setup quality | target reached 2026-07-09 18:20 | win $2.26 (+1.1%) |
| 2026-07-15 00:00 | BTC/USD | 1Hour bars x1 | confirmed daily breakout above the five-day range with old top held as support and a second impulse into the close | stop reached 2026-07-16 07:40 | loss -$5.78 (-1.9%) |
| 2026-07-19 00:00 | BTC/USD | 1Hour bars x1 | grind of hourly higher lows holding above the 64.68-64.70k range top; breakout attempt with consolidation character, not a spike | stop reached 2026-07-20 06:35 | loss -$6.14 (-2.0%) |
| 2026-07-20 12:00 | BTC/USD | packet only | core long adapted to tape character: wide stop at the true structure failure, intent to hold through stop-hunt noise | stop reached 2026-07-25 00:00 | loss -$4.99 (-2.0%) |
| 2026-07-27 00:00 | BTC/USD | packet only | daily reclaim of 65.3k after the dip proved a bear trap; ETH new highs as breadth confirmation | stop reached 2026-07-27 22:55 | loss -$7.08 (-2.8%) |
| 2026-07-29 00:00 | BTC/USD | packet only | repeated July pattern of dip-buys back to range top; ETH strength confirms flow | sold by the trader 2026-07-30 12:00 | win $1.72 (+0.7%) |

### July, Grok 4.7

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-07-03 00:00 | SOL/USD | 1Hour bars x4 | Pullback from 82.70 held 80.00 for hours; stop under that shelf and the breakout candle, target back through the high. | target reached 2026-07-04 04:40 | win $10.29 (+3.0%) |
| 2026-07-03 00:00 | LINK/USD | 1Hour bars x4 | Cleared the late-June high near 7.85 and is holding 7.69; stop under the shelf, target under the mid-June high. | stop reached 2026-07-04 09:46 | win $3.34 (+1.2%) |
| 2026-07-04 12:00 | ETH/USD | 1Hour bars x4 | Pullback from 1773 has held 1743 for ten hours; stop under that shelf, target into the mid-June supply. | stop reached 2026-07-05 01:35 | loss -$1.47 (-0.4%) |
| 2026-07-04 12:00 | LINK/USD | 1Hour bars x4 | The 7.87 print was a wick and price is back above the 7.85 break; stop under the wick, target at the mid-June high. | target reached 2026-07-04 18:10 | win $5.96 (+2.3%) |
| 2026-07-05 12:00 | ETH/USD | 1Hour bars x3 | Retest of the 1743 shelf held at 1749; stop under the shelf, target just under the 1805 rejection. | stop reached 2026-07-06 12:05 | loss -$5.39 (-1.8%) |
| 2026-07-07 12:00 | BTC/USD | 1Hour bars x3 | Seven-hour base above 63000 after the 62736 wick; stop under the wick, target just under the June 22 high. | stop reached 2026-07-08 08:20 | loss -$7.43 (-2.2%) |
| 2026-07-12 12:00 | BTC/USD | 1Hour bars x3 | Two tests of 63615 held; stop under them, target through 64682 toward 65300. | stop reached 2026-07-13 02:00 | loss -$5.29 (-1.7%) |
| 2026-07-15 12:00 | ETH/USD | 1Hour bars x1 | Pullback to 1864 held above the 1860 breakout shelf; stop under 1848, target 1960. | stop reached 2026-07-17 02:40 | loss -$9.67 (-2.8%) |

### August, Claude Opus 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-08-01 00:00 | BTC/USD | 1Day bars x5, 1Hour bars x1 | Range-low bounce near 62.4k July support, stop below it. | stop reached 2026-08-11 17:10 | win $0.35 (+0.1%) |
| 2026-08-12 00:00 | LINK/USD | 1Hour bars x2 | Relative strength into the July high while BTC dipped. | target reached 2026-08-15 02:00 | win $13.64 (+5.4%) |
| 2026-08-16 00:00 | LINK/USD | 1Hour bars x1 | Breakout above 8.90 held its first pullback at 9.22. | target reached 2026-08-19 20:25 | win $19.08 (+7.6%) |
| 2026-08-20 00:00 | BTC/USD | 1Hour bars x2, 30Min bars x1 | Range breakout above 67k that held for eight hours. | target reached 2026-08-21 08:20 | win $31.54 (+10.5%) |
| 2026-08-22 00:00 | BTC/USD | 1Hour bars x2 | Held a nine-hour shelf at 76-78k after the spike and turned up again. | stop reached 2026-08-23 05:15 | loss -$13.42 (-3.8%) |
| 2026-08-22 00:00 | ETH/USD | 1Hour bars x2 | Broke up from a 2365-2430 shelf in a strong trend. | stop reached 2026-08-23 04:50 | loss -$15.37 (-6.1%) |
| 2026-08-23 12:00 | BTC/USD | 1Hour bars x1 | Wick below 76k was bought straight back; trend range holding. | stop reached 2026-08-28 16:15 | loss $-0.00 (-0.0%) |
| 2026-08-25 00:00 | SOL/USD | 1Hour bars x1 | Steady leader breaking out of a one-day 93.3-97 base to a new high. | stop reached 2026-08-30 23:25 | win $7.16 (+2.9%) |

### August, GPT-6.2 Sol

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-08-03 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x1 | Buy the daily support reclaim while hourly lows hold above the 72.62 base. | stop reached 2026-08-03 06:45 | loss -$6.50 (-2.2%) |
| 2026-08-09 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x1 | The post-breakout pullback stayed above the pre-breakout 75.29 shelf and recovered to 75.95. | stop reached 2026-08-11 15:00 | loss -$4.29 (-1.7%) |
| 2026-08-21 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x1 | Buy the higher-post-breakout-base continuation while BTC and ETH also advance. | target reached 2026-08-21 22:45 | win $14.96 (+6.8%) |

### August, Gemini Neon

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-08-03 00:00 | ETH/USD | 1Day bars x2, 1Hour bars x4 | Bullish daily reversal (+2.25%) and clean hourly uptrend above 5/10/20/50h SMAs with healthy RSI (59.3). | stop reached 2026-08-03 08:25 | loss -$11.79 (-3.4%) |
| 2026-08-04 12:00 | AVAX/USD | 1Day bars x1, 1Hour bars x2 | High-volume breakout above daily SMAs and 6.66 resistance followed by a clean bull-flag pullback to 6.74. | stop reached 2026-08-06 10:05 | loss -$19.75 (-6.6%) |
| 2026-08-05 00:00 | BTC/USD | 1Day bars x2, 1Hour bars x2 | Daily close above 5d and 10d SMAs with clean higher-low base and hourly uptrend above 20/50h SMAs. | stop reached 2026-08-11 14:55 | loss -$4.31 (-1.2%) |
| 2026-08-06 00:00 | ETH/USD | 1Day bars x2, 1Hour bars x1 | Daily breakout (+2.00%) closing above 5/10/20-day SMAs alongside BTC clearing its 20-day SMA, entering on a minor hourly pullback from 1925.7. | target reached 2026-08-19 15:30 | win $23.90 (+8.0%) |
| 2026-08-10 12:00 | SOL/USD | 1Day bars x2, 1Hour bars x1 | Confirmed daily breakout above 5/10/20d SMAs followed by orderly consolidation above 50h SMA and fresh curl higher. | target reached 2026-08-19 20:55 | win $21.83 (+8.7%) |
| 2026-08-15 00:00 | LINK/USD | 1Day bars x1, 1Hour bars x1 | High-volume 30-day breakout above 8.90 resistance with strong 7-day relative strength (+9.47%) and clean hourly uptrend. | target reached 2026-08-19 20:55 | win $52.60 (+17.5%) |
| 2026-08-20 12:00 | ETH/USD | 1Hour bars x3 | Strongest breakout leader (+19.4% 24h) resuming higher out of a tight 2222-2265 bull flag with hourly RSI reset to 53.0. | stop reached 2026-08-30 23:40 | win $16.12 (+4.2%) |
| 2026-08-20 12:00 | BTC/USD | 1Hour bars x3 | High-volume breakout above 70k (to 72.4k/71.9k) after 10 hours of tight consolidation above 68.8k. | open at the end | still held at the end or not filled |
| 2026-08-20 12:00 | SOL/USD | 1Hour bars x3 | Clean bull-flag breakout to 88.0/87.2 after high-volume absorption and hourly RSI reset to 55.9. | stop reached 2026-08-30 23:30 | win $44.15 (+15.7%) |

### August, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-08-07 12:00 | BTC/USD | 1Day bars x4, 1Hour bars x1 | Higher lows, price at 65k, risk about 3% to stop vs about 3% to target. | time limit 2026-08-11 00:00 | loss -$7.05 (-2.3%) |
| 2026-08-12 12:00 | LINK/USD | 1Hour bars x1 | Breakout held a full day with rising hourly lows; stop under the 8.53 shelf. | target reached 2026-08-15 02:40 | win $20.85 (+8.3%) |
| 2026-08-19 12:00 | LINK/USD | 1Day bars x1, 1Hour bars x1 | Four-day base at 9.4-9.55 broken upward to 9.76; stop under base. | target reached 2026-08-19 20:45 | win $14.66 (+5.9%) |
| 2026-08-20 00:00 | BTC/USD | 1Hour bars x2 | Range top 66.5k broken and 68-70k held for 8 hours; stop under the 67.8k consolidation low. | target reached 2026-08-21 01:50 | win $16.47 (+8.2%) |
| 2026-08-20 00:00 | ETH/USD | 1Hour bars x2 | Second leg to 2.25k held; higher beta than BTC; stop under the 2.17k hold zone. | stop reached 2026-08-22 10:20 | win $8.52 (+5.7%) |
| 2026-08-27 12:00 | SOL/USD | packet only | Held a 12h base above the prior 102.9 high; stop under the base. | stop reached 2026-08-28 14:05 | loss -$2.01 (-0.8%) |

### August, Kimi K3

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-08-02 00:00 | BTC/USD | 1Hour bars x1 | Double-defended support at 62.2-62.4k; buying the range-low defense with stop just below the lows. | stop reached 2026-08-10 15:50 | win $6.47 (+2.1%) |
| 2026-08-12 12:00 | LINK/USD | 1Day bars x1, 1Hour bars x1 | Breakout leader: base breakout plus July-high clearance, stair-step continuation under way. | stop reached 2026-08-12 22:00 | loss -$9.59 (-3.2%) |
| 2026-08-16 12:00 | LINK/USD | 1Hour bars x1 | Bull-flag continuation entry mid-flag at 9.41 with stop outside all flag lows. | target reached 2026-08-19 15:30 | win $13.07 (+5.2%) |
| 2026-08-21 00:00 | BTC/USD | 1Day bars x1 | Volume-confirmed range breakout on continuation day; trend-following entry with structural stop. | stop reached 2026-08-23 05:15 | win $12.87 (+3.2%) |
| 2026-08-23 12:00 | BTC/USD | packet only | Trend re-entry after instantly-absorbed dip, stop under the dip low. | stop reached 2026-08-28 16:20 | loss -$0.83 (-0.2%) |
| 2026-08-30 00:00 | BTC/USD | packet only | Failed breakdown back above the 78.4k floor in an intact uptrend. | open at the end | still held at the end or not filled |

### August, Grok 4.7

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-08-06 00:00 | ETH/USD | 1Hour bars x3 | Reclaimed 1895 and held above 1900 into the close, with room back toward the late-July high. | stop reached 2026-08-10 15:15 | loss -$8.64 (-2.5%) |
| 2026-08-09 00:00 | LTC/USD | 1Day bars x2, 1Hour bars x2 | Closed through the 45.50 base and the 20-day average, with a stop under the recent lows and room to 48. | sold by the trader 2026-08-10 00:00 | loss -$5.84 (-1.9%) |
| 2026-08-15 00:00 | LINK/USD | 1Hour bars x2 | Closed and held above the 60-day high, with a stop under today's low and room to 9.40. | target reached 2026-08-15 02:05 | win $12.89 (+4.3%) |

### September, Claude Opus 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-09-01 00:00 | SOL/USD | 1Day bars x9 | Strongest relative chart: higher highs after the breakout, holding 100-105; stop below Aug 30 low of 99. | stop reached 2026-09-02 09:45 | loss -$15.95 (-5.3%) |
| 2026-09-01 00:00 | BTC/USD | 1Day bars x9 | Holding near breakout highs in a tight 77-81k range; stop below the range at 76.4k. | stop reached 2026-09-02 11:25 | loss -$10.42 (-3.5%) |
| 2026-09-03 12:00 | BTC/USD | packet only | Range low held and reclaimed; buying the lower third of a 75.6k-81.4k range. | target reached 2026-09-03 15:40 | win $11.37 (+3.2%) |
| 2026-09-04 00:00 | BTC/USD | 1Hour bars x2 | Breakout to a new high above the two-week range, holding the breakout level for eight hours. | stop reached 2026-09-04 14:50 | loss -$13.59 (-3.9%) |
| 2026-09-06 00:00 | LTC/USD | 1Day bars x3 | Clear relative-strength leader, highest close since the Aug 21-22 breakout. | stop reached 2026-09-10 12:55 | loss -$14.93 (-6.0%) |
| 2026-09-07 00:00 | LINK/USD | 1Hour bars x1 | New high above the Aug 22 top, gain held for three hours after the jump. | stop reached 2026-09-08 13:35 | loss -$13.61 (-6.8%) |
| 2026-09-11 12:00 | BTC/USD | 1Hour bars x1 | Pullback to the three-week range floor that held again overnight; good reward against a stop under the whole range. | stop reached 2026-09-15 14:40 | loss -$6.75 (-2.2%) |
| 2026-09-17 12:00 | BTC/USD | packet only | Breakdown under 76.2k found support at 75.3k and price is back at the old floor. | target reached 2026-09-18 13:55 | win $12.02 (+4.0%) |
| 2026-09-19 00:00 | ETH/USD | 1Hour bars x2 | Closed above its Aug 27 high of 2566 in a market-wide breakout and held 2610-2640 for hours. | time limit 2026-09-29 12:00 | win $9.40 (+3.8%) |
| 2026-09-19 00:00 | SOL/USD | 1Hour bars x2 | New high above the Aug 27 top of 110.5, held 112-114 after the breakout. | time limit 2026-09-29 12:00 | win $11.61 (+5.8%) |
| 2026-09-21 12:00 | BTC/USD | 1Hour bars x1 | Clean break above the 82.2k range top on a day when every pair rose; trend confirmation. | time limit 2026-09-29 12:00 | loss -$4.04 (-1.3%) |

### September, GPT-6.2 Sol

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-09-05 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x2, 1Min bars x1 | Buy a small pullback-recovery swing; do not give it room to revisit the whole daily range. | target reached 2026-09-06 02:40 | win $4.81 (+1.9%) |
| 2026-09-12 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x2, 1Min bars x1 | Buy the recovery with a stop below 101.55; 103 is the first hurdle. | stop reached 2026-09-12 19:40 | loss -$4.17 (-1.7%) |
| 2026-09-17 12:00 | SOL/USD | 1Hour bars x3, 1Min bars x1 | Buy the higher-low retest, with the stop below 99.37 and target near the prior 102.54 daily close. | target reached 2026-09-18 01:50 | win $3.56 (+1.8%) |
| 2026-09-21 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x2, 1Min bars x1 | Buy the rebound toward the 114 area and exit if the latest hourly breakout fails. | target reached 2026-09-21 08:40 | win $6.02 (+2.7%) |
| 2026-09-26 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x2, 1Min bars x1 | Express a small continuation swing above 120; exit below the hourly retest low. | stop reached 2026-09-26 04:00 | loss -$3.32 (-1.8%) |

### September, Gemini Neon

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-09-01 12:00 | LINK/USD | 1Day bars x6, 1Hour bars x3 | Relative strength leader bouncing off 11.00 daily support and 11.29 hourly low on rising volume. | target reached 2026-09-06 20:40 | win $23.99 (+9.6%) |
| 2026-09-03 00:00 | SOL/USD | 1Hour bars x3 | Strongest 30d leader completing a higher-low hourly reversal from 97.20 and reclaiming 100.40 above MA5/MA10/MA20. | stop reached 2026-09-09 21:50 | win $2.41 (+0.8%) |
| 2026-09-04 00:00 | BTC/USD | 1Hour bars x2 | High-volume breakout above the two-week 81.4k range high to 82,233, holding firmly above 80.6k. | stop reached 2026-09-08 06:30 | loss -$14.91 (-4.2%) |
| 2026-09-07 00:00 | ETH/USD | 1Hour bars x3 | Tight higher-low coil at 2515 just beneath 2566 August resistance as BTC holds 80.3k and alts break out. | stop reached 2026-09-10 13:00 | loss -$13.19 (-4.7%) |
| 2026-09-12 00:00 | ETH/USD | 1Hour bars x3 | High-volume breakout to a new 30-day high (2,665) followed by an orderly pullback to hourly MA20 support at 2,516. | stop reached 2026-09-15 14:55 | loss -$15.70 (-5.2%) |
| 2026-09-12 00:00 | SOL/USD | 1Hour bars x3 | Strong rebound off 98.06 sweep low with higher lows at 100.45 and 101.55, reclaiming hourly MA5/MA10/MA20. | stop reached 2026-09-15 18:50 | loss -$17.68 (-7.1%) |
| 2026-09-17 00:00 | BTC/USD | 1Hour bars x4 | Massive 19:00Z absorption volume off 74,981 sweep low with higher low and reclaim of hourly MAs; tight 2.3% stop. | open at the end | still held at the end or not filled |
| 2026-09-17 00:00 | LINK/USD | 1Hour bars x4 | Double bottom at 10.62 followed by a +1.59% reclaim of 11.00 on rising volume (V=87.5) above hourly MAs. | target reached 2026-09-21 09:25 | win $39.53 (+15.8%) |
| 2026-09-18 12:00 | SOL/USD | 1Hour bars x2 | High-volume hourly breakout (+8.35% over 48h) consolidating tightly above 105.20 with clear risk below 101.30. | stop reached 2026-09-20 03:00 | win $2.91 (+1.2%) |
| 2026-09-21 00:00 | ETH/USD | 1Hour bars x2 | Clean hourly breakout from 2,568-2,585 base flagging right under 30d high (2,665.72) with defined 3.4% risk below 2,555. | open at the end | still held at the end or not filled |
| 2026-09-21 12:00 | SOL/USD | 1Hour bars x2 | Institutional-volume breakout (V=372 at 08:00Z, V=107.5 at 11:00Z) to fresh 30-day highs (117.15) with clear support shelf at 111.20. | stop reached 2026-09-28 05:35 | win $2.32 (+0.8%) |

### September, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-09-04 00:00 | BTC/USD | 1Day bars x1, 1Hour bars x1, 1Min bars x1 | Range breakout above 80.5k held for 10 hourly bars on rising volume. | stop reached 2026-09-04 14:50 | loss -$11.64 (-3.9%) |
| 2026-09-19 00:00 | BTC/USD | 1Day bars x1, 1Hour bars x2 | Held above the 80.5k range top for 10 hourly bars after a jump. | stop reached 2026-09-23 16:00 | win $6.29 (+3.1%) |
| 2026-09-19 00:00 | ETH/USD | 1Day bars x1, 1Hour bars x2 | ETH broke out with BTC and held 2600+ for 10 hours. | stop reached 2026-09-23 14:10 | win $5.09 (+2.5%) |

### September, Kimi K3

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-09-01 00:00 | BTC/USD | 1Day bars x8, 1Hour bars x2 | Strongest coin in a choppy tape; flush-reclaim of 77k plus a full day of higher lows; swing toward the 81k range top. | stop reached 2026-09-01 18:00 | loss -$9.51 (-2.4%) |
| 2026-09-02 00:00 | LTC/USD | 1Hour bars x2 | Strongest of the eight on a day BTC made new lows; flat all-day base at 49-50; long toward 51.5 with stop under 48.75. | stop reached 2026-09-02 09:40 | loss -$7.64 (-2.5%) |
| 2026-09-03 00:00 | BTC/USD | 1Hour bars x1 | Two failed breakdowns plus 12h of higher lows; long toward 79.9k with stop under the higher-low structure. | target reached 2026-09-03 14:50 | win $11.35 (+3.2%) |
| 2026-09-04 00:00 | BTC/USD | 1Hour bars x2 | Breakout above 81446 to 82233, now retesting the old range top as support; long with tight invalidation below 80250. | stop reached 2026-09-04 12:35 | loss -$9.32 (-2.5%) |
| 2026-09-07 00:00 | LINK/USD | 1Hour bars x2 | First clean alt breakout of the month, holding above its old high; trend long with invalidation under 12.75. | stop reached 2026-09-07 18:30 | loss -$10.44 (-4.3%) |
| 2026-09-11 00:00 | BTC/USD | 1Hour bars x1 | Third defense of 76-77k range lows; buying support with stop below 75350, target range top 81k. | stop reached 2026-09-15 13:40 | loss -$2.63 (-1.1%) |
| 2026-09-21 00:00 | BTC/USD | packet only | Third press of range top with absorption (shallow dips, alt confirmation); long with stop under 79.4k, target 87.5k. | stop reached 2026-09-24 08:50 | win $4.27 (+1.9%) |
| 2026-09-25 00:00 | BTC/USD | packet only | Bull flag holding above breakout lid, turning up; long 84386 with stop under 83k, target 88k. | stop reached 2026-09-28 05:35 | loss -$5.86 (-2.4%) |

### September, Grok 4.7

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-09-18 12:00 | BTC/USD | 1Hour bars x1 | Double bottom at 74,900 broke 76,800 and the break is holding, with alts confirming. | target reached 2026-09-18 14:25 | win $10.54 (+3.0%) |
| 2026-09-22 00:00 | BTC/USD | 1Hour bars x1 | New highs held for a full session with higher lows, so the breakout is a trend and not a spike. | stop reached 2026-09-23 14:20 | loss -$9.87 (-3.3%) |

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

### October, Kimi K3

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-10-01 00:00 | LINK/USD | 1Day bars x8 | Strongest trend: +78% 60d, +14.7% 10d, higher highs; pullback to 14.36 after 15.77 high; stop under 13.5 shelf. | stop reached 2026-10-07 00:02 | loss -$11.84 (-3.4%) |
| 2026-10-01 00:00 | BTC/USD | 1Day bars x8 | Range floor 82.5k held 4 times; buying mid-range at 83.5k with tight stop under 81.8k for a run back to 87k+. | stop reached 2026-10-08 15:25 | loss -$9.49 (-3.2%) |
| 2026-10-01 00:00 | SOL/USD | 1Day bars x8 | Uptrend (+64% 60d), sitting on 116-117 support; stop under 114.3, target range high 125. | stop reached 2026-10-08 10:50 | loss -$9.86 (-3.9%) |
| 2026-10-07 00:00 | AVAX/USD | packet only | Trend leader: higher highs, +8% 10d after a 52% 20d run, breaking out; stop under 10.8 pullback low. | stop reached 2026-10-08 04:45 | loss -$15.50 (-5.2%) |
| 2026-10-07 12:00 | AVAX/USD | packet only | Topping up the under-filled leader position on a retest of the 10.8-11.0 shelf; stop 10.75 keeps risk ~2.5%. | open at the end | still held at the end or not filled |
| 2026-10-09 12:00 | BTC/USD | 1Min bars x1 | Higher-lows base after 80.3k flush, reclaiming the range floor; stop 81.3k under the base. | stop reached 2026-10-13 00:45 | loss -$8.85 (-2.9%) |
| 2026-10-09 12:00 | AVAX/USD | 1Min bars x1 | Trend leader held 10.0-10.07 through the flush, first to bounce; stop 9.95. | stop reached 2026-10-12 23:00 | loss -$14.38 (-3.6%) |
| 2026-10-12 00:00 | AVAX/USD | packet only | Adding to the leading position as it reclaims the 11.0 area; pyramid into strength. | open at the end | still held at the end or not filled |
| 2026-10-16 12:00 | AVAX/USD | packet only | False breakdown reclaimed and held 24h; leader; stop 9.90 under the reclaim zone. | stop reached 2026-10-17 12:50 | loss -$14.35 (-4.8%) |
| 2026-10-16 12:00 | BTC/USD | packet only | Back above 82k after holding the 80.3-81.5k base on the retest; stop 79.8k under the wick low. | stop reached 2026-10-22 16:50 | loss -$16.17 (-3.2%) |
| 2026-10-19 00:00 | AVAX/USD | 1Day bars x8 | Base at the 9.5-9.8 support after full washout; tight stop 9.45 gives ~3% risk for swing back to 10.7+. | stop reached 2026-10-20 01:15 | loss -$10.06 (-4.0%) |
| 2026-10-22 00:00 | BTC/USD | packet only | Higher-high attempt above 84k after three higher lows; pyramid the one working trend with stop 81.2k. | open at the end | still held at the end or not filled |

### October, Grok 4.7

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-10-01 00:00 | BTC/USD | 1Day bars x8 | Cleanest uptrend, holding above the late-September base, stop under the 21 September low. | sold by the trader 2026-10-08 12:00 | loss -$8.18 (-2.0%) |
| 2026-10-01 00:00 | ETH/USD | 1Day bars x8 | Same impulse-and-base structure as bitcoin, second leader, stop under the 20 September low. | stop reached 2026-10-07 13:20 | loss -$15.69 (-5.2%) |
| 2026-10-25 00:00 | BTC/USD | 1Day bars x8 | Second spring under 79700 closed back above it, stop under the 24 October wick, target above the failed breakout. | stop reached 2026-10-29 22:10 | loss -$13.72 (-3.4%) |

### November 1 to 24, Claude Opus 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-11-02 00:00 | BTC/USD | 1Hour bars x2 | Small bounce try after two days of base-building above 77k; risk about 2.3 percent to make about 3.3 percent. | sold by the trader 2026-11-03 00:00 | loss -$8.02 (-2.7%) |
| 2026-11-04 12:00 | ETH/USD | 1Hour bars x2 | Leader of the reversal off a swept low; risk about 3 percent to 2255, aim for 2420 near the late-Oct shelf. | target reached 2026-11-04 15:05 | win $12.20 (+4.1%) |
| 2026-11-04 12:00 | BTC/USD | 1Hour bars x2 | Failed breakdown below 75.8k and V reversal; risk about 2 percent to 76.8k, aim for 80.8k. | target reached 2026-11-04 22:45 | win $4.98 (+2.5%) |
| 2026-11-05 00:00 | BTC/USD | 1Hour bars x2 | Breakout from range holding above 80k; risk about 1.8 percent to 79k, aim 83k (+3.2 percent). | stop reached 2026-11-05 14:40 | loss -$6.25 (-2.5%) |
| 2026-11-10 00:00 | BTC/USD | 1Day bars x1, 1Hour bars x2 | Double low at 73.5k and steady climb; risk about 1.8 percent to 73.9k, aim 77.6k (+3.1 percent). | stop reached 2026-11-10 13:35 | loss -$6.27 (-2.5%) |
| 2026-11-10 00:00 | ETH/USD | 1Day bars x1, 1Hour bars x2 | Laggard after the flush; risk about 2.7 percent to 2075, aim 2220 (+4.1 percent) where it sat before the drop. | stop reached 2026-11-10 13:35 | loss -$9.66 (-3.9%) |
| 2026-11-13 12:00 | AVAX/USD | 1Hour bars x2 | Held its range and rose on a day BTC fell 3 percent; risk about 4.5 percent to 8.00, aim 9.00 (+7.4 percent). | stop reached 2026-11-14 07:20 | loss -$11.22 (-5.6%) |
| 2026-11-15 12:00 | BTC/USD | 1Hour bars x2 | Capitulation wick to 62k, higher low 63.7k, higher high 66.1k; risk about 2.8 percent to 63.5k, aim 69k (+5.6 percent). | stop reached 2026-11-17 15:55 | loss -$11.11 (-3.7%) |
| 2026-11-15 12:00 | ETH/USD | 1Hour bars x2 | Same reversal shape from 1711; risk about 3.2 percent to 1765, aim 1930 (+5.9 percent). | stop reached 2026-11-17 15:50 | loss -$6.05 (-4.0%) |
| 2026-11-18 00:00 | BTC/USD | 1Hour bars x2 | Second higher low held and recovered fast; wider stop under 62k so ordinary noise does not stop me out. Risk 4.8 percent, aim 69.5k (+7 percent). | stop reached 2026-11-19 21:20 | loss -$14.45 (-5.8%) |
| 2026-11-22 00:00 | BTC/USD | 1Hour bars x1 | V from 55.1k with ten hours holding near 60k; risk about 2.8 percent to 58.4k, aim 63.5k (+5.7 percent). | target reached 2026-11-23 14:00 | win $10.84 (+5.4%) |

### November 1 to 24, GPT-6.2 Sol

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-11-04 12:00 | SOL/USD | 1Hour bars x2 | Rebound is holding over the hourly base around 92.7 with broad confirmation. | stop reached 2026-11-04 12:55 | loss -$4.39 (-1.8%) |
| 2026-11-16 00:00 | SOL/USD | 1Hour bars x2 | The pullback held above the selloff low and the last several hours recovered constructively. | stop reached 2026-11-16 09:15 | loss -$5.62 (-3.7%) |

### November 1 to 24, Gemini Neon

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-11-01 12:00 | LINK/USD | 1Hour bars x4 | Strongest relative strength and volume accumulation off Oct 30 low; tight hourly consolidation below 11.93 resistance. | stop reached 2026-11-02 16:10 | loss -$13.16 (-5.2%) |
| 2026-11-04 00:00 | XRP/USD | 1Day bars x2, 1Hour bars x2 | Clean breakout from 4-day base (1.235-1.262) with strong relative strength vs BTC and alts. | stop reached 2026-11-05 15:10 | loss -$4.18 (-1.7%) |
| 2026-11-04 12:00 | ETH/USD | 1Day bars x1, 1Hour bars x2 | Leading major; swept to higher low at 2,223 and broke 5-day range high (2,312) with tight consolidation at 2,325. | stop reached 2026-11-05 15:10 | loss -$6.39 (-1.8%) |
| 2026-11-04 12:00 | BTC/USD | 1Day bars x1, 1Hour bars x2 | Wyckoff spring below Oct 30 low (75,577) followed by strong 8-hour reversal to 78,375. | stop reached 2026-11-05 15:05 | loss -$4.45 (-1.5%) |
| 2026-11-15 12:00 | ETH/USD | 1Hour bars x4 | Climax washout to 1,711, +4.9% V-reversal, higher low at 1,772, and high-volume break to 1,843. | stop reached 2026-11-18 16:40 | loss -$18.81 (-5.4%) |
| 2026-11-15 12:00 | BTC/USD | 1Hour bars x4 | Climax washout to 61,991, +3.7% V-reversal, higher low at 63,735, and break to 66,085. | stop reached 2026-11-17 15:55 | loss -$11.11 (-3.7%) |
| 2026-11-15 12:00 | LINK/USD | 1Hour bars x4 | Cleanest altcoin higher-low (8.99) and higher-high (9.29) structure off the 01:00Z washout. | stop reached 2026-11-20 02:30 | loss -$10.77 (-5.4%) |
| 2026-11-18 00:00 | SOL/USD | 1Hour bars x2 | Strongest momentum leader across all 8 pairs; 7 straight green hours off 71.05 flush to break out at 75.11 on high volume. | stop reached 2026-11-20 02:30 | loss -$12.91 (-5.1%) |
| 2026-11-22 00:00 | BTC/USD | 1Hour bars x4 | Capitulation reversal (+9.0% off 55,121 low) followed by 10-hour tight bull flag holding 60,000 support. | stop reached 2026-11-24 02:50 | loss -$1.66 (-0.5%) |
| 2026-11-22 00:00 | ETH/USD | 1Hour bars x4 | Capitulation reversal (+9.5% off 1,536 low) with two consecutive green 12h wakes and tight 10-hour flag above 1,671. | stop reached 2026-11-24 02:45 | loss -$1.06 (-0.4%) |

### November 1 to 24, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-11-03 12:00 | BTC/USD | 1Day bars x1, 1Hour bars x1 | Range-low bounce setup, stop below the Oct 30 low, target is range high about 3% up. | target reached 2026-11-04 14:45 | win $7.22 (+2.4%) |
| 2026-11-07 00:00 | BTC/USD | 1Day bars x1, 1Hour bars x1 | Third test of 75k-75.8k support, stop 1.5 percent below, target about 3 percent above. | stop reached 2026-11-08 22:00 | loss -$8.77 (-2.9%) |
| 2026-11-15 12:00 | BTC/USD | 1Hour bars x2 | Oversold bounce after a fast flush, first hourly higher low; small size, stop 3.5 percent below. | stop reached 2026-11-18 15:50 | loss -$10.65 (-4.2%) |
| 2026-11-22 00:00 | BTC/USD | 1Day bars x1, 1Hour bars x1 | Long lower wick on the daily and hourly higher lows; small size, stop 4 percent below, target 6 percent above. | target reached 2026-11-23 14:30 | win $12.27 (+6.1%) |

### November 1 to 24, Kimi K3

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-11-01 12:00 | LINK/USD | 1Hour bars x4 | Relative-strength leader in the post-crash bounce; hourly higher highs and higher lows, stop below 11.46 overnight low, target 12.40 for ~2:1 reward. | stop reached 2026-11-01 19:10 | loss -$11.76 (-3.4%) |
| 2026-11-02 12:00 | ETH/USD | 1Day bars x2, 1Hour bars x1 | Post-crash recovery leader: three green daily closes, hourly base at 2247-2280, stop 2238 below the base, target 2355 pre-crash close, ~1.6:1 reward after costs. | stop reached 2026-11-02 19:45 | loss -$9.25 (-2.6%) |
| 2026-11-04 00:00 | BTC/USD | packet only | Pilot long: four sessions of higher lows after capitulation; stop 76400 under the range floor, upside back to 80000+ if the 78600 range top gives way. | stop reached 2026-11-04 03:00 | loss -$4.76 (-2.4%) |
| 2026-11-05 00:00 | BTC/USD | packet only | Range breakout after a stop-sweep V-reversal; ETH confirms by fully reclaiming the crash. Stop 78250 back inside the range, target 84000 pre-crash congestion, ~1.6:1 reward after costs. | stop reached 2026-11-05 15:00 | loss -$10.42 (-3.5%) |

### November 1 to 24, Grok 4.7

| Wake (UTC) | Coin | Looked at | Its reason | Ended | Result |
|---|---|---|---|---|---|
| 2026-11-05 00:00 | ETH/USD | 1Day bars x4, 1Hour bars x1 | Strongest close of the reversal day, through the 20-day average, with about ten percent of room to the October shelf against a stop just under that average. | stop reached 2026-11-05 15:10 | loss -$23.09 (-5.8%) |

## What this does not show

- Fills are assumed, not real. Many crypto minutes on the tape are thin, so real fills could be worse.
- The rule against outside knowledge is given by instruction. Each trader's lookups are logged; its memory is not.
- Whether these months fall after each model's knowledge line is UNKNOWN. It has not been measured.
- October was the shakedown month. Its three known differences are listed at the end of the plan.
- For a time on 2026-11-25 the packets of crypto sessions also listed the previous day's movers among stock funds, after those funds were loaded onto the tape. Nothing from the future was shown, and no trader looked up a stock. The last column of the session table counts the wakes this touched. It was switched off at 15:53 UTC.
- Until 2026-11-25 16:00 UTC, a pick sent twice after a lost reply was taken twice: once for the wake it was meant for, and again for the next wake, which the trader had not seen. The last column of the session table counts those wakes. Every one found so far was a repeated "no pick"; no buy or sell was doubled. The desk now refuses a pick for a wake the trader has not asked to see.
- With six models, one looking good by luck is likely. That is why the bar is per model and was fixed before the run.
