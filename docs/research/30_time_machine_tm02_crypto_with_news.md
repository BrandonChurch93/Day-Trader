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
| Claude Opus 5.5 | 2 of 5 | -$48.70 | -$111.98 | yes |
| GPT-6.2 Sol | 2 of 5 | -$15.57 | -$35.28 | yes |
| Gemini Neon | 1 of 5 | -$95.97 | -$162.36 | yes |
| Claude Sonnet 5.5 | 3 of 5 | -$10.38 | -$63.18 | yes |
| Kimi K3 | 0 of 5 | n/a | n/a | n/a |
| Grok 4.7 | 1 of 5 | -$18.22 | -$37.59 | yes |

Verdict: not finished.

## Each session

| Month | Model | Gain | Hold | Twin 80th pct | Twins beaten | Buys | Wins | Losses | Fees | Largest drop | Wakes with no pick | Lookups | Wakes that showed stock fund movers | Wakes answered unseen |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| July | Claude Opus 5.5 | -$1.45 | $69.81 | n/a | n/a of 0 | 6 | 2 | 4 | $8.02 | -5.0% | 50 of 62 | 10 | 0 of 62 | 0 |
| July | GPT-6.2 Sol | $3.40 | $69.81 | n/a | n/a of 0 | 3 | 1 | 2 | $3.02 | -1.2% | 59 of 62 | 51 | 0 of 62 | 0 |
| July | Gemini Neon | not finished | | | | | | | | | | | | |
| July | Claude Sonnet 5.5 | -$16.55 | $69.81 | n/a | n/a of 0 | 2 | 0 | 2 | $2.97 | -2.8% | 58 of 62 | 30 | 0 of 62 | 0 |
| July | Kimi K3 | not finished | | | | | | | | | | | | |
| July | Grok 4.7 | not finished | | | | | | | | | | | | |
| August | Claude Opus 5.5 | not finished | | | | | | | | | | | | |
| August | GPT-6.2 Sol | not finished | | | | | | | | | | | | |
| August | Gemini Neon | not finished | | | | | | | | | | | | |
| August | Claude Sonnet 5.5 | $15.87 | $245.33 | n/a | n/a of 0 | 5 | 3 | 2 | $7.06 | -1.9% | 55 of 62 | 10 | 0 of 62 | 0 |
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
| October | Gemini Neon | -$95.97 | -$76.42 | n/a | n/a of 0 | 6 | 0 | 6 | $8.78 | -9.7% | 59 of 62 | 24 | 13 of 62 | 0 |
| October | Claude Sonnet 5.5 | -$9.70 | -$76.42 | n/a | n/a of 0 | 3 | 1 | 2 | $3.99 | -1.1% | 49 of 62 | 14 | 41 of 62 | 0 |
| October | Kimi K3 | not finished | | | | | | | | | | | | |
| October | Grok 4.7 | -$18.22 | -$76.42 | n/a | n/a of 0 | 1 | 0 | 1 | $1.46 | -1.9% | 61 of 62 | 15 | 8 of 62 | 0 |
| November 1 to 24 | Claude Opus 5.5 | not finished | | | | | | | | | | | | |
| November 1 to 24 | GPT-6.2 Sol | not finished | | | | | | | | | | | | |
| November 1 to 24 | Gemini Neon | not finished | | | | | | | | | | | | |
| November 1 to 24 | Claude Sonnet 5.5 | not finished | | | | | | | | | | | | |
| November 1 to 24 | Kimi K3 | not finished | | | | | | | | | | | | |
| November 1 to 24 | Grok 4.7 | not finished | | | | | | | | | | | | |

## Why each trade was made, and how it ended

One row per buy. "Looked at" is what the trader asked the desk for at that wake, beyond the packet it is always given. "Headlines it named" is the pick's own list of sources. Headlines are also in every packet, so a trader can use one without a lookup.

### July, Claude Opus 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-07-02 00:00 | SOL/USD | 1Day bars x1, 1Hour bars x1 | SOL relative strength: higher daily lows since 25 June and a 5% up day to 77.4 while BTC lags; supported by the headline 'Solana USDC Liquidity Jumps As Circle Mints Another $1 Billion' (2026-07-01T16:15Z). Stop 72.0 below yesterday's low, target 84 (~+8.5%), well above round-trip costs. | https://www.newsbtc.com/news/solana-usdc-liquidity-jumps-as-circle-mints-another-1-billion/ | stop reached 2026-07-08 07:05 | win $0.72 (+0.3%) |
| 2026-07-03 00:00 | ETH/USD | 1Day bars x1 | ETH broke out of a one-week base (1510-1640) to 1698. Headlines: 'Crypto ETF Inflow Split: Ether and Solana Products Gain While Bitcoin Outflows Exceed $290M' (2026-07-02T18:30Z) and 'Ethereum Eyes Relief Rally as Double Bottom Forms Near $1.5K' (2026-07-02T13:55Z). Stop 1615 (-4.9%), target 1800 (+6%), well above ~1.25% cost hurdle. | https://www.newsbtc.com/news/crypto-etf-inflow-split-ether-and-solana-products-gain-while-bitcoin-outflows/; https://cryptopotato.com/ethereum-eyes-relief-rally-as-double-bottom-forms-near-1-5k-eth-price-analysis/ | target reached 2026-07-04 17:55 | win $15.49 (+5.1%) |
| 2026-07-04 00:00 | BTC/USD | packet only | BTC reclaimed 62k with higher lows each day since 30 June; headline 'Bitcoin ETFs see biggest inflow since May after weak US jobs report sparks BTC price rebound' (2026-07-03T16:05Z) shows flows turning after record June outflows. Stop 60400 (-3.4%), target 65600 (+4.9%) near mid-June highs; clears the ~1.25% cost hurdle. | https://cryptoslate.com/bitcoin-etfs-see-biggest-inflow-since-may-after-weak-us-jobs-report-sparks-btc-price-rebound/ | stop reached 2026-07-06 12:05 | loss -$4.40 (-1.8%) |
| 2026-07-10 12:00 | BTC/USD | 1Day bars x1, 1Hour bars x1 | Price only: higher lows since 1 July and a push to the top of the week-long 61.2k-64.6k range. Stop 61200 below the range (-5%), target 68500 (+6.4%), well above the ~1.25% cost hurdle. | none | stop reached 2026-07-24 14:25 | loss -$5.12 (-1.7%) |
| 2026-07-15 00:00 | ETH/USD | packet only | ETH broke the 1.85k level named in 'Ethereum Price Analysis: Will ETH Finally Break the $1.85K Barrier?' (2026-07-14T15:22Z) and led the market after 'Bitcoin pushes toward $65,000 on US inflation relief that may already be fading' (2026-07-14T19:30Z). Stop 1790 (-5.3%) back inside the old range, target 2000 (+5.8%); clears the ~1.25% cost hurdle. | https://cryptoslate.com/bitcoin-pushes-toward-65000-on-us-inflation-relief-that-may-already-be-fading/; https://cryptopotato.com/ethereum-price-analysis-will-eth-finally-break-the-1-85k-barrier/ | stop reached 2026-07-27 23:05 | loss -$3.07 (-1.0%) |
| 2026-07-16 00:00 | LINK/USD | 1Day bars x1, news x2 | LINK broke above the 8.31 July high to 8.53 on two strong days with relative strength; adoption headlines 'Robinhood's Chainlink CCIP Choice Adds Infrastructure Weight To Its Layer-2 Bet' (2026-07-13T12:05Z) and 'Fidelity's Chainlink-Powered FILQ Fund Shows Tokenized Finance Is Getting More Practical' (2026-07-13T11:50Z). Stop 8.00 (-6%) below the breakout, target 9.20 (+7.8%); clears the cost hurdle. (The edited 15 July Commerce-data headline is not used.) | https://www.newsbtc.com/news/robinhood-s-chainlink-ccip-choice-adds-infrastructure-weight-to-its-layer-2-bet/; https://www.newsbtc.com/news/fidelity-s-chainlink-powered-filq-fund-shows-tokenized-finance-is-getting-more/ | time limit 2026-07-26 00:00 | loss -$5.07 (-2.5%) |

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

### August, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-08-09 00:00 | BTC/USD | packet only | Headline 'Bitcoin and Ethereum ETFs break $1B in their best week since April and BlackRock brought in 80% of the cash' (2026-08-08T18:40:18Z) plus price holding above 64k support; expect a push toward 67.5k. | Bitcoin and Ethereum ETFs break $1B in their best week since April and BlackRock brought in 80% of the cash (2026-08-08T18:40:18Z); https://cryptopotato.com/bitcoin-price-analysis-is-btc-heading-below-60k-after-the-latest-rejection/ | stop reached 2026-08-11 18:40 | loss -$9.58 (-3.2%) |
| 2026-08-14 00:00 | LINK/USD | 1Day bars x1, news x2 | Breakout above the 8.5 range top held for three days plus the headline 'LINK could be next in line after Standard Chartered's UNI and AAVE targets sparked sharp repricings' (2026-08-11T08:16:41Z) about a bank initiating coverage; target 9.6 is about 8% up vs about 5% to the stop. | LINK could be next in line after Standard Chartered's UNI and AAVE targets sparked sharp repricings (2026-08-11T08:16:41Z) https://cryptoslate.com/link-could-be-next-in-line-after-standard-chartereds-uni-and-aave-targets-sparked-sharp-repricings/ | target reached 2026-08-15 02:40 | win $20.50 (+8.2%) |
| 2026-08-21 00:00 | BTC/USD | packet only | Headline 'Bitcoin ETF Inflows Hit $517M As Institutional Demand Returns' (2026-08-20T17:15:00Z) plus a held breakout above the 65k range; target 77k about 5% up vs stop 70.5k about 3.5% down. | Bitcoin ETF Inflows Hit $517M As Institutional Demand Returns (2026-08-20T17:15:00Z) | target reached 2026-08-21 08:20 | win $14.78 (+4.9%) |
| 2026-08-23 12:00 | BTC/USD | packet only | Headline 'Institutional Demand Is Back: Bitcoin and Ethereum ETF Inflows Reached 10-Month High' (2026-08-23T11:02:27Z) plus a two-day hold at 77k; target 81k (+4.8%) vs stop 74.8k (-3.2%). | Institutional Demand Is Back: Bitcoin and Ethereum ETF Inflows Reached 10-Month High (2026-08-23T11:02:27Z) | time limit 2026-08-26 12:00 | win $2.09 (+0.8%) |
| 2026-08-28 00:00 | BTC/USD | packet only | Price holds above the 80k resistance after a retest; target 84k (+4.6%) vs stop 77.8k (-3.1%). No headline used. | none | stop reached 2026-08-28 16:20 | loss -$11.91 (-4.0%) |

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

### October, Gemini Neon

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-10-02 12:00 | BTC/USD | 1Hour bars x3 | Clean breakout above 85.6k resistance with constructive 85.7k retest on 1h bars, supported by 'Bitcoin’s $113,000 case strengthens as US regulators push 9 crypto actions' (2026-10-02T08:50:28Z) and 'Bitcoin ETFs Swing Back To $102.7M Inflows As BlackRock IBIT Pulls In $195.6M' (2026-10-02T08:41:26Z). | https://cryptoslate.com/bitcoins-113000-case-strengthens-as-us-regulators-push-9-crypto-actions/; https://www.newsbtc.com/markets/bitcoin-etf-inflows-blackrock-ibit-october-1/; https://cryptoslate.com/solana-enters-us-banking-with-90-north-dakota-banks-lead-it/ | stop reached 2026-10-07 02:45 | loss -$12.98 (-3.7%) |
| 2026-10-02 12:00 | SOL/USD | 1Hour bars x3 | Relative strength leader (+2.95%) breaking out from 118 to 123.5 and holding 121.85 support on 1h bars, supported by 'Solana enters US banking with 90 North Dakota banks leading it' (2026-10-02T07:20:39Z). | https://cryptoslate.com/bitcoins-113000-case-strengthens-as-us-regulators-push-9-crypto-actions/; https://www.newsbtc.com/markets/bitcoin-etf-inflows-blackrock-ibit-october-1/; https://cryptoslate.com/solana-enters-us-banking-with-90-north-dakota-banks-lead-it/ | stop reached 2026-10-07 12:30 | loss -$12.56 (-5.0%) |
| 2026-10-09 12:00 | BTC/USD | 1Hour bars x3 | Confirmed higher-low reversal on 1h bars from 80,319 -> 81,532 -> 82,318 breaking to 83,173 after the $1B liquidation flush, alongside 'Bitcoin miners escape months of distress as daily revenue surges by 78%' (2026-10-09T04:10:41Z). | https://cryptoslate.com/bitcoin-miners-escape-months-of-financial-distress-as-daily-revenue-surges-by-78/; https://cryptopotato.com/82-million-samsung-galaxy-devices-could-soon-get-native-solana-stablecoin-transfers/; https://cryptopotato.com/solana-network-growth-jumps-124-heres-why-it-could-matter-for-sol/ | stop reached 2026-10-15 13:55 | loss -$16.62 (-4.7%) |
| 2026-10-09 12:00 | SOL/USD | 1Hour bars x3 | Clean higher-low reversal on 1h bars from 105.60 -> 108.73 -> 109.31 surging to 111.25 on volume, backed by '82 Million Samsung Galaxy Devices Could Soon Get Native Solana Stablecoin Transfers' (2026-10-08T22:03:36Z) and 'Solana Network Growth Jumps 124%: Here’s Why It Could Matter for SOL' (2026-10-08T13:50:50Z). | https://cryptoslate.com/bitcoin-miners-escape-months-of-financial-distress-as-daily-revenue-surges-by-78/; https://cryptopotato.com/82-million-samsung-galaxy-devices-could-soon-get-native-solana-stablecoin-transfers/; https://cryptopotato.com/solana-network-growth-jumps-124-heres-why-it-could-matter-for-sol/ | stop reached 2026-10-13 00:10 | loss -$17.31 (-6.9%) |
| 2026-10-21 00:00 | BTC/USD | 1Hour bars x3 | Multi-day base breakout on 1h bars (81.2k -> 83.34k -> higher low 82.29k -> 82.94k), supported by 'BlackRock Bitcoin ETF Pulls In $665 Million While Rivals Lose Money' (2026-10-20T10:20:00Z), 'Switzerland Approves Its First Bitcoin ETF in Major Retail Crypto Milestone' (2026-10-20T12:31:56Z), and 'Bitcoin’s Biggest Holders Scoop Up Nearly 89,000 BTC in Just One Month' (2026-10-20T16:33:09Z). | https://www.newsbtc.com/bitcoin-news/blackrock-bitcoin-etf-pulls-in-665-million-while-rivals-lose-money/; https://cryptopotato.com/switzerland-approves-its-first-bitcoin-etf-in-major-retail-crypto-milestone/; https://cryptopotato.com/bitcoins-biggest-holders-scoop-up-nearly-89000-btc-in-just-one-month/; https://cryptopotato.com/stakerxs-ai-agent-surpasses-passes-40m-staked-assets-on-solana-within-three-months-of-launch/ | stop reached 2026-10-24 15:20 | loss -$18.23 (-5.2%) |
| 2026-10-21 00:00 | SOL/USD | 1Hour bars x3 | Clean 1h breakout from 103.75 to 108.15 with higher-low consolidation at 106.44 heading into Solana's Oct 21 Alpenglow upgrade, supported by 'StakerX’s AI Agent Surpasses Passes $40M Staked Assets on Solana Within Three Months of Launch' (2026-10-19T10:17:42Z). | https://www.newsbtc.com/bitcoin-news/blackrock-bitcoin-etf-pulls-in-665-million-while-rivals-lose-money/; https://cryptopotato.com/switzerland-approves-its-first-bitcoin-etf-in-major-retail-crypto-milestone/; https://cryptopotato.com/bitcoins-biggest-holders-scoop-up-nearly-89000-btc-in-just-one-month/; https://cryptopotato.com/stakerxs-ai-agent-surpasses-passes-40m-staked-assets-on-solana-within-three-months-of-launch/ | stop reached 2026-10-24 15:10 | loss -$18.27 (-7.3%) |

### October, Claude Sonnet 5.5

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-10-02 12:00 | BTC/USD | 1Hour bars x1 | Hourly bars show a breakout above 85k holding for ~8 hours with higher lows; stop under 84.3k limits loss to ~2.3%. Price-based only, no headline used. | none | stop reached 2026-10-02 18:40 | loss -$10.19 (-3.4%) |
| 2026-10-09 00:00 | BTC/USD | 1Hour bars x1 | After the liquidation flush (headline 'Bitcoin crashes through $81,000 buy wall as $1 billion crypto liquidation bloodbath unfolds', 2026-10-08T21:00:13Z) the hourly bars show a six-hour base at 81.6-81.9k above the 80.3k low; stop under that low, target the 84k breakdown level. | https://cryptoslate.com (headline: Bitcoin crashes through $81,000 buy wall as $1 billion crypto liquidation bloodbath unfolds, 2026-10-08T21:00:13Z) | target reached 2026-10-11 17:40 | win $5.35 (+2.1%) |
| 2026-10-25 00:00 | BTC/USD | 1Hour bars x1 | After the liquidation flush (headline 'Bitcoin Price Suddenly Dumps Below $80K as Liquidations Surge to $670M', 2026-10-24T14:34:28Z) hourly bars show an 8-hour base at 80.1-80.8k above the 79.15k low; stop under the low, target 83k. | https://cryptoslate.com (headline: Bitcoin Price Suddenly Dumps Below $80K as Liquidations Surge to $670M, 2026-10-24T14:34:28Z) | time limit 2026-10-27 12:00 | loss -$4.86 (-1.9%) |

### October, Grok 4.7

| Wake (UTC) | Coin | Looked at | Its reason | Headlines it named | Ended | Result |
|---|---|---|---|---|---|---|
| 2026-10-02 12:00 | XRP/USD | 1Hour bars x2 | Buy the hold above 1.51 after the 2026-10-02T08:41:21Z headline 'Evernorth Clears Shareholder Vote Ahead Of XRPN Nasdaq Debut', which confirms the 2026-10-01T16:59:04Z vote story that XRP is coming to Nasdaq with a 473M treasury. Stop under the pre-break base. | https://www.newsbtc.com/business/evernorth-shareholders-approve-xrp-treasury-xrpn/; https://cryptopotato.com/xrp-is-coming-to-nasdaq-evernorth-clears-key-vote-with-473m-treasury/ | stop reached 2026-10-02 18:40 | loss -$18.22 (-6.1%) |

## What this does not show

- Fills are assumed, not real. Many crypto minutes on the tape are thin, so real fills could be worse.
- The rule against outside knowledge is given by instruction. Each trader's lookups are logged; its memory is not.
- Whether these months fall after each model's knowledge line is UNKNOWN. It has not been measured.
- A headline can remind a model of what it already knows about that period. That would look like skill and is not. About one headline in eight was edited after it was published; those are marked and the card says not to trade on them.
- For a time on 2026-11-25 the packets of crypto sessions also listed the previous day's movers among stock funds, after those funds were loaded onto the tape. Nothing from the future was shown, and no trader looked up a stock. The last column of the session table counts the wakes this touched. It was switched off at 15:53 UTC.
- Until 2026-11-25 16:00 UTC, a pick sent twice after a lost reply was taken twice: once for the wake it was meant for, and again for the next wake, which the trader had not seen. The last column of the session table counts those wakes. Every one found so far was a repeated "no pick"; no buy or sell was doubled. The desk now refuses a pick for a wake the trader has not asked to see.
- With six models, one looking good by luck is likely. That is why the bar is per model and was fixed before the run.
