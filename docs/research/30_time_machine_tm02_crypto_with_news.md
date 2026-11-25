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
| Claude Opus 5.5 | 1 of 5 | -$47.25 | -$61.35 | yes |
| GPT-6.2 Sol | 2 of 5 | -$15.57 | -$35.28 | yes |
| Gemini Neon | 0 of 5 | n/a | n/a | n/a |
| Claude Sonnet 5.5 | 2 of 5 | -$26.25 | -$114.62 | yes |
| Kimi K3 | 0 of 5 | n/a | n/a | n/a |
| Grok 4.7 | 0 of 5 | n/a | n/a | n/a |

Verdict: not finished.

## Each session

| Month | Model | Gain | Hold | Twin 80th pct | Twins beaten | Buys | Wins | Losses | Fees | Largest drop | Wakes with no pick | Lookups | Wakes that showed stock fund movers | Wakes answered unseen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| July | Claude Opus 5.5 | not finished | | | | | | | | | | | | |
| July | GPT-6.2 Sol | $3.40 | $69.81 | n/a | n/a of 0 | 3 | 1 | 2 | $3.02 | -1.2% | 59 of 62 | 51 | 0 of 62 | 0 |
| July | Gemini Neon | not finished | | | | | | | | | | | | |
| July | Claude Sonnet 5.5 | -$16.55 | $69.81 | n/a | n/a of 0 | 2 | 0 | 2 | $2.97 | -2.8% | 58 of 62 | 30 | 0 of 62 | 0 |
| July | Kimi K3 | not finished | | | | | | | | | | | | |
| July | Grok 4.7 | not finished | | | | | | | | | | | | |
| August | Claude Opus 5.5 | not finished | | | | | | | | | | | | |
| August | GPT-6.2 Sol | not finished | | | | | | | | | | | | |
| August | Gemini Neon | not finished | | | | | | | | | | | | |
| August | Claude Sonnet 5.5 | not finished | | | | | | | | | | | | |
| August | Kimi K3 | not finished | | | | | | | | | | | | |
| August | Grok 4.7 | not finished | | | | | | | | | | | | |
| September | Claude Opus 5.5 | not finished | | | | | | | | | | | | |
| September | GPT-6.2 Sol | not finished | | | | | | | | | | | | |
| September | Gemini Neon | not finished | | | | | | | | | | | | |
| September | Claude Sonnet 5.5 | not finished | | | | | | | | | | | | |
| September | Kimi K3 | not finished | | | | | | | | | | | | |
| September | Grok 4.7 | not finished | | | | | | | | | | | | |
| October | Claude Opus 5.5 | -$47.25 | -$76.42 | n/a | n/a of 0 | 6 | 1 | 5 | $8.40 | -5.7% | 53 of 62 | 17 | 21 of 62 | 0 |
| October | GPT-6.2 Sol | -$18.97 | -$76.42 | n/a | n/a of 0 | 3 | 0 | 3 | $3.24 | -2.2% | 59 of 62 | 58 | 30 of 62 | 0 |
| October | Gemini Neon | not finished | | | | | | | | | | | | |
| October | Claude Sonnet 5.5 | -$9.70 | -$76.42 | n/a | n/a of 0 | 3 | 1 | 2 | $3.99 | -1.1% | 49 of 62 | 14 | 41 of 62 | 0 |
| October | Kimi K3 | not finished | | | | | | | | | | | | |
| October | Grok 4.7 | not finished | | | | | | | | | | | | |
| November 1 to 24 | Claude Opus 5.5 | not finished | | | | | | | | | | | | |
| November 1 to 24 | GPT-6.2 Sol | not finished | | | | | | | | | | | | |
| November 1 to 24 | Gemini Neon | not finished | | | | | | | | | | | | |
| November 1 to 24 | Claude Sonnet 5.5 | not finished | | | | | | | | | | | | |
| November 1 to 24 | Kimi K3 | not finished | | | | | | | | | | | | |
| November 1 to 24 | Grok 4.7 | not finished | | | | | | | | | | | | |

## Why each trade was made, and how it ended

One row per buy. "Looked at" is what the trader asked the desk for at that wake, beyond the packet it is always given. "Headlines it named" is the pick's own list of sources. Headlines are also in every packet, so a trader can use one without a lookup.

### July, GPT-6.2 Sol

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-07-02 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x1, news x1 | SOL closed at 77.37 above the June 29 high near 76.22; Solana USDC Liquidity Jumps As Circle Mints Another $1 Billion (2026-07-01T16:15:00Z) corroborates a liquidity tailwind but does not establish buying of SOL. | https://www.newsbtc.com/news/solana-usdc-liquidity-jumps-as-circle-mints-another-1-billion/ | target reached 2026-07-02 10:55 | win $11.93 (+4.8%) |
| 2026-07-15 00:00 | ETH/USD | 1Day bars x2, 1Hour bars x2 | ETH at 1890.82 broke June and July resistance, then closed above its intraday consolidation. Bitcoin pushes toward $65,000 on US inflation relief that may already be fading (2026-07-14T19:30:28Z) describes a broader risk rally but also cautions against larger size. | https://cryptoslate.com/bitcoin-pushes-toward-65000-on-us-inflation-relief-that-may-already-be-fading/ | stop reached 2026-07-16 23:25 | loss -$4.94 (-2.5%) |
| 2026-07-21 12:00 | LINK/USD | 1Hour bars x1, news x1 | LINK at 8.70048 held above the prior 8.635 high after Aave Picks Chainlink CCIP As Default Standard For Cross-Chain sGHO (2026-07-20T16:00:00Z), a concrete integration announcement but not evidence of direct token buying. | https://www.newsbtc.com/news/aave-chainlink-ccip-default-cross-chain-sgho/ | stop reached 2026-07-23 05:16 | loss -$3.60 (-2.4%) |

### July, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-07-03 12:00 | ETH/USD | 1Hour bars x1 | Headlines 'Crypto ETF Inflow Split: Ether and Solana Products Gain While Bitcoin Outflows Exceed $290M' (2026-07-02T18:30Z) and 'US Spot Bitcoin ETF Outflows Clash With Ethereum Fund Demand' (2026-07-03T11:17Z) show relative ETH demand; price broke above 1710 resistance, 1741 now. | Crypto ETF Inflow Split: Ether and Solana Products Gain While Bitcoin Outflows Exceed $290M (2026-07-02T18:30:00Z); US Spot Bitcoin ETF Outflows Clash With Ethereum Fund Demand (2026-07-03T11:17:00Z) | stop reached 2026-07-08 08:20 | loss -$2.16 (-0.7%) |
| 2026-07-15 00:00 | ETH/USD | 1Hour bars x2, news x1 | Price breakout above the 1805 range top at the 07-14 12:00 hour, held 1870-1890 for 11 hours, BTC also through 64K; no headline used. | none | stop reached 2026-07-17 13:10 | loss -$14.39 (-4.8%) |

### October, Claude Opus 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-10-01 00:00 | BTC/USD | 1Day bars x8 | Price-based: BTC at 83.6k sits near the bottom of a 10-day 83-87k range inside a 60-day uptrend; stop under the 29 Sep 82k low, target near range top 88k. About 5% up vs 3% down. | none | stop reached 2026-10-07 02:05 | loss -$1.18 (-0.4%) |
| 2026-10-04 12:00 | LTC/USD | packet only | Price-based: LTC at 71.2 is breaking above its 3 Oct high of about 71.1 after a week of higher lows near 67; stop at 67.4 under that base (-5%), target 76.5 just above the September high of 75 (+7.5%), well above the ~0.7% round-trip cost. | none | stop reached 2026-10-07 02:05 | loss -$15.30 (-6.1%) |
| 2026-10-10 00:00 | BTC/USD | packet only | Price-based: BTC at 82.55k has held above 82k for 24 hours after the 80.3k flush low on 8 Oct; stop 79,900 under that low (-3.2%), target 86,000 (+4.2%), more than twice the ~0.7% round-trip cost. | none | sold by the trader 2026-10-15 00:00 | loss -$5.64 (-1.9%) |
| 2026-10-16 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x1 | Headline 'Solana sets October 21 for massive Alpenglow upgrade that could make transactions 99% faster to finalize' (2026-10-15T00:00:17Z) is a dated catalyst; price held 100.5 on the 15 Oct flush and reclaimed 105. Stop 98.9 (-6%), target 114.5 (+8.7%), exit by 21 Oct; well above ~0.7% round-trip cost. | https://cryptoslate.com/solana-sets-october-21-for-massive-alpenglow-upgrade-that-could-make-transactions-99-faster-to-finalize/ | time limit 2026-10-21 12:00 | win $1.65 (+0.7%) |
| 2026-10-22 00:00 | BTC/USD | 1Hour bars x1, news x1 | BTC reclaimed 84k on 21 Oct after a higher low near 82.4k; headline 'BlackRock Bitcoin ETF Pulls In $665 Million While Rivals Lose Money' (2026-10-20T10:20:00Z) shows returning spot demand. Stop 81,600 (-2.9%), target 87,300 (+3.9%), well above the ~0.7% round-trip cost. | https://www.newsbtc.com/bitcoin-news/blackrock-bitcoin-etf-pulls-in-665-million-while-rivals-lose-money/ | stop reached 2026-10-22 13:00 | loss -$12.56 (-3.6%) |
| 2026-10-27 12:00 | XRP/USD | 1Day bars x1 | Relative strength plus news: headline 'Ripple Clears Final OCC Hurdle for National Trust Bank' (2026-10-27T07:38:41Z) and 'XRP ETFs Resume Winning Streak While SOL Funds Stay in the Red' (2026-10-26T04:03:10Z); price held the 1.255 low twice (18 and 24 Oct). Stop 1.245 (-4.3%), target 1.39 (+6.8%), above twice the ~0.7% round-trip cost. | https://cryptopotato.com/ripple-clears-final-occ-hurdle-for-national-trust-bank/; https://cryptopotato.com/xrp-etfs-resume-winning-streak-while-sol-funds-stay-in-the-red/ | stop reached 2026-10-29 20:45 | loss -$14.22 (-5.7%) |

### October, GPT-6.2 Sol

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-10-06 12:00 | AVAX/USD | 1Day bars x1, 1Hour bars x1, news x1 | Price-only entry near 11.43 after daily range expansion; stop below the hourly breakout base and target just below 11.997. Target move is about 4.6% gross. | none | stop reached 2026-10-07 02:05 | loss -$8.05 (-3.5%) |
| 2026-10-16 12:00 | SOL/USD | 1Day bars x1, 1Hour bars x3 | SOL at 106.45 is above the 104.86 hourly base, and Solana sets October 21 for massive Alpenglow upgrade that could make transactions 99% faster to finalize (2026-10-15T00:00:17Z) provides a dated mainnet catalyst. Target 111.65 is 4.9% gross versus about 1.7% to the stop; allow about 0.8% for round-trip costs. | https://cryptoslate.com/solana-sets-october-21-for-massive-alpenglow-upgrade-that-could-make-transactions-99-faster-to-finalize/ | stop reached 2026-10-16 15:10 | loss -$6.11 (-2.4%) |
| 2026-10-21 00:00 | LTC/USD | 1Day bars x1, 1Hour bars x3, news x2 | Price-only range reclaim near 61.61; stop below the 60.50 breakout base, first supply near 62.61, and target 64.4 below the older high. The gross target move is about 4.5%, with roughly 0.8% allowed for round-trip costs. | none | stop reached 2026-10-22 05:25 | loss -$4.81 (-2.7%) |

### October, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-10-02 12:00 | BTC/USD | 1Hour bars x1 | Hourly bars show a breakout above 85k holding for ~8 hours with higher lows; stop under 84.3k limits loss to ~2.3%. Price-based only, no headline used. | none | stop reached 2026-10-02 18:40 | loss -$10.19 (-3.4%) |
| 2026-10-09 00:00 | BTC/USD | 1Hour bars x1 | After the liquidation flush (headline 'Bitcoin crashes through $81,000 buy wall as $1 billion crypto liquidation bloodbath unfolds', 2026-10-08T21:00:13Z) the hourly bars show a six-hour base at 81.6-81.9k above the 80.3k low; stop under that low, target the 84k breakdown level. | https://cryptoslate.com (headline: Bitcoin crashes through $81,000 buy wall as $1 billion crypto liquidation bloodbath unfolds, 2026-10-08T21:00:13Z) | target reached 2026-10-11 17:40 | win $5.35 (+2.1%) |
| 2026-10-25 00:00 | BTC/USD | 1Hour bars x1 | After the liquidation flush (headline 'Bitcoin Price Suddenly Dumps Below $80K as Liquidations Surge to $670M', 2026-10-24T14:34:28Z) hourly bars show an 8-hour base at 80.1-80.8k above the 79.15k low; stop under the low, target 83k. | https://cryptoslate.com (headline: Bitcoin Price Suddenly Dumps Below $80K as Liquidations Surge to $670M, 2026-10-24T14:34:28Z) | time limit 2026-10-27 12:00 | loss -$4.86 (-1.9%) |

## What this does not show

- Fills are assumed, not real. Many crypto minutes on the tape are thin, so real fills could be worse.
- The rule against outside knowledge is given by instruction. Each trader's lookups are logged; its memory is not.
- Whether these months fall after each model's knowledge line is UNKNOWN. It has not been measured.
- A headline can remind a model of what it already knows about that period. That would look like skill and is not. About one headline in eight was edited after it was published; those are marked and the card says not to trade on them.
- For a time on 2026-11-25 the packets of crypto sessions also listed the previous day's movers among stock funds, after those funds were loaded onto the tape. Nothing from the future was shown, and no trader looked up a stock. The last column of the session table counts the wakes this touched. It was switched off at 15:53 UTC.
- Until 2026-11-25 16:00 UTC, a pick sent twice after a lost reply was taken twice: once for the wake it was meant for, and again for the next wake, which the trader had not seen. The last column of the session table counts those wakes. Every one found so far was a repeated "no pick"; no buy or sell was doubled. The desk now refuses a pick for a wake the trader has not asked to see.
- With six models, one looking good by luck is likely. That is why the bar is per model and was fixed before the run.
