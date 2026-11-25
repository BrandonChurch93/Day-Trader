# The high-risk sleeve: penny stocks, small stocks and high-risk crypto

Last verified: 2026-11-25. Asked by the owner on 2026-11-24.

Scope: the evidence on each kind of high-risk bet for a small, long-only, own-cash account in Idaho. The owner wants moonshots only "if the moonshot actually makes sense and has a reason behind it". No leverage, no shorting and no derivatives are proposed. The sleeve's size lives in `moonshot_sleeve_share` and `moonshot_max_position_share` in `config/thresholds.yaml`. Both are open owner numbers.

How it was made: two researchers wrote `docs/research/13_raw/penny_and_microcap_stocks.md` and `docs/research/13_raw/high_risk_crypto.md` from primary pages. Two fresh checkers per report, on different models, re-opened the sources for 25 key claims. Their tables are in `docs/research/13_raw/check/`. This file carries the checkers' narrower figures.

Tags: MEASURED means read on a primary page or measured from a public endpoint. STATED means a claim not confirmed. UNKNOWN means not found. Paper figures are backtests, not real money, unless marked.

Status of everything recommended here: proposed by the research team. Nothing in this file is an owner decision.

## Words used here

| Word | Meaning |
|---|---|
| Basis point (bp) | One hundredth of 1%. 100 bps = 1% |
| OTC | Stocks traded off the main exchanges |
| Gross, net | Before, after costs |
| Abnormal return, alpha | Return above what a market model predicts |
| Long-short | Buy one group and short-sell another. This account cannot short |
| Value-weighted | Big names count more |
| In-sample | Rules chosen and tested on the same data |
| Spread | Gap between best buy and sell price |
| 13D, Form 4 | Filings for an activist buying 5% or more, and for insider trades |

## Bottom line

- Penny and OTC stocks as a group have a negative expected return. No reason to buy them as a group was found.
- Opportunistic insider buying and activist 13D filings have a published reason. Both are gross, older results, and a follower gets less.
- In crypto, the idea worth testing is a slow trend rule on liquid coins, holding cash when the trend is down. Its best result is in-sample, on an index, and not replicated.
- Memecoin launches, pump groups, copy trading, buying after listing news and blind small-coin baskets show no positive return for a follower. Small-coin costs are large.
- Much measured edge is on the short side. No source showed a small retail account earning it after costs.

## Penny and OTC stocks

| Question | Finding | Tag and source |
|---|---|---|
| What the OTC market returned | The value-weighted OTC market portfolio returned about -0.74% a month over Treasury bills, 1977 to 2008, before trading costs. The authors round it to -0.8%. It is an excess return, not a raw index return | MEASURED. [Ang, Shtauber and Tetlock, NBER w19309](https://www.nber.org/system/files/working_papers/w19309/w19309.pdf) |
| What happened to real buyers | 212,908 investors, 2014. The median investor's holding-period return was -13.4% and the median investor held 16 days, after commissions. The median per investor and company was -11.92%. The sample is records the SEC requested, not random. Open positions were left out, which the author says understates losses | MEASURED, real money. [SEC DERA, White, 2016](https://www.sec.gov/files/White_OutcomesOTCinvesting.pdf) |
| Lottery-like stocks | Biggest one-day jump last month: 1.03% a month less than the calmest, value-weighted, long-short, 1962 to 2005, gross | MEASURED. [Bali, Cakici and Whitelaw, NBER w14804](https://www.nber.org/system/files/working_papers/w14804/w14804.pdf) |

What Alpaca allows. Opening positions in most OTC stocks is not supported. A curated list, mostly ADRs of large foreign companies such as BYDDY, NSRGY and VWAGY, is allowed, per an Alpaca comment dated 2026-10-02 (STATED, [Alpaca issue #149](https://github.com/alpacahq/Alpaca-API/issues/149)). Positions that become OTC can still be closed, and listed stocks under $1 can be traded ([Alpaca broker API FAQ](https://docs.alpaca.markets/us/docs/broker-api-faq), [Alpaca orders](https://docs.alpaca.markets/docs/orders-at-alpaca), MEASURED). The "$2.50 a share or 100%" figure is collateral required on short positions under $5, not a fee ([Alpaca margin](https://docs.alpaca.markets/us/docs/margin-and-short-selling), MEASURED).

Nasdaq rules now in force (MEASURED):

- From January 17, 2025, a company below the $1 bid minimum that did a reverse split in the prior year gets no compliance period at all ([Federal Register, 34-102245](https://www.federalregister.gov/documents/full_text/html/2025/01/23/2025-01621.html)).
- From January 19, 2026 (approved December 5, 2025), a closing bid of $0.10 or less for ten business days in a row brings a delisting determination and trading suspension. A hearing request does not pause the suspension ([Federal Register, SR-NASDAQ-2025-065](https://www.federalregister.gov/documents/full_text/html/2025/12/10/2025-22398.html)). It is not instant delisting on the first trade under $0.10.

So a listed stock under $1 is more likely to end up on OTC, where Alpaca only lets you sell.

## Stock ideas with a reason

| Idea | Size of the effect | What a follower can still get | Not known |
|---|---|---|---|
| Opportunistic insider buying (insiders breaking their usual pattern) | 82 bps a month five-factor alpha for a long-short portfolio, opportunistic buys minus opportunistic sells, value-weighted, 1989 to 2007 (raw filings start 1986). Buys alone: 72 bps. Routine trades: -20 bps, not different from zero. No costs deducted. MEASURED, [Cohen, Malloy and Pomorski, NBER w16454](https://www.nber.org/system/files/working_papers/w16454/w16454.pdf) | The buys side, from public Form 4 filings | Results after 2007; net of costs |
| Activist 13D filings | About 7.2% abnormal return over days -20 to +20, 2001 to 2006, with no reversal over the next year. MEASURED, [Brav et al., FDIC WP 2008-06](https://www.fdic.gov/analysis/cfr/working-papers/2008/2008-06.pdf) | About 3.2 points come in the ten days before the filing and about 2.0 on the filing day and the next day. A follower gets much less | Net post-filing return; results after 2006 |
| Index inclusion | Fell from 7.6% in the 1990s to 0.8% in 2010 to 2020, the later figure not different from zero. MEASURED, [Greenwood and Sammon, NBER w30748](https://www.nber.org/system/files/working_papers/w30748/w30748.pdf) | Close to nothing | |

Post-bankruptcy stocks and spinoffs have only small, old samples.

## High-risk crypto

What an Idaho account can reach. Coinbase, Kraken, Binance.US, Gemini, Robinhood and Alpaca state they serve Idaho. Public lists on 2026-11-24 showed 404 active coins at Coinbase, 561 at Kraken with the US filter, 204 at Binance.US, 83 at Gemini, 91 at Robinhood and 36 at Alpaca, including WIF, BONK and TRUMP ([Alpaca tokens](https://alpaca.markets/support/what-cryptocurrencies-does-alpaca-currently-support)). These are public lists, not Idaho entitlements (MEASURED, sources in the raw report).

On-chain launchpads: Jupiter and Raydium say they do not serve US residents ([Jupiter terms](https://docs.jup.ag/user-docs/legal/terms-of-use), [Raydium disclaimer](https://raydium.io/docs/disclaimer/), STATED). Pump.fun's general terms do not bar the US, but bar US persons from some features ([Pump terms](https://pump.fun/docs/terms-and-conditions), STATED). Venues are compared in `docs/research/09_brokers_and_venues.md`.

| Idea | What the evidence says | Tag and source |
|---|---|---|
| Small coins, dead coins counted | Of 3,904 coins, 2014 to 2021, 1,222 were delisted. Leaving them out inflates equal-weighted returns by 62.19% a year (0.93% value-weighted). The median delisting return was -100%, mostly assigned by assumption. | MEASURED. [Ammann et al.](https://alexandria.unisg.ch/server/api/core/bitstreams/2bc8397d-47dd-4f66-8467-9004b2c9d212/content) |
| Small-coin size and momentum | Small minus large 3.4% a week, momentum 2.5% to 4.1% a week, 2014 to 2018. Gross, long-short, needs shorting small coins | MEASURED. [Liu, Tsyvinski and Wu](https://www.nber.org/system/files/working_papers/w25882/w25882.pdf) |
| Trend following, liquid basket | 67.16% a year gross and 48.76% at 0.50% cost, against 18.48% for holding, January 2019 to January 2023. 20 days was the best of four lookbacks tried, chosen on the same data. It is an index, not coins one can buy. The figure assumes cash earns interest (66.37% without). The largest drop was 60.98%. Not replicated. A 2026 abstract calls time-series momentum "strong" and cross-sectional "almost nonexistent" | MEASURED. [Le and Ruthbah, Monash](https://www.monash.edu/__data/assets/pdf_file/0011/3744821/Trend-following-Strategies-for-Crypto-Investors.pdf), [Review of Asset Pricing Studies](https://academic.oup.com/raps/advance-article-abstract/doi/10.1093/rapstu/raag011/8914819) |
| New listings | Raw run-up of +11.9% (Coinbase) and +19.5% (Binance) before listing news, +32.8% and +22.7% on the day. Listing day itself: +6.51%, then -1.51% over three days | MEASURED. [Li et al.](https://www.loyola.edu/_media/sellinger-business/documents/academics/departments/finance/wealth-management-conference/speakers/J_Li.pdf), [Ante and Meyer](https://link.springer.com/content/pdf/10.1007/s10203-021-00323-0.pdf) |
| Memecoin launches | About 1.02% of 15.25 million Pump.fun launches "graduated" to a trading pool, 2024 to 2026, which is not profit. Late buyers averaged -2.34 SOL per token in five days of September 2026 data | MEASURED, preprints. [Meme Coin Factories](https://arxiv.org/html/2609.10246), [Gafarov](https://arxiv.org/html/2610.39458) |
| Memecoin wallets | 69.92% losing in June 2025, 26.72% in April 2026. Counts only realised results and leaves out holders who never sold | MEASURED. [CoinGecko](https://www.coingecko.com/research/publications/pump-fun-traders-are-making-a-comeback) |
| Pump groups | An insider buying before the alert made up to +18.44%; a buyer in the first 10 seconds at best +6.53%; after 20 seconds, losses. Before commissions, and assumes the trader is the only seller, which the authors say overstates results. Another study's medians of 3.5% and 5.1% are the largest five-minute jump anywhere from 48 hours before to 48 hours after the signal, a peak, not a gain a follower could take | MEASURED. [Li, Shin and Wang](https://abfer.org/media/abfer-events-2019/annual-conference/investment-finance/AC19P3078_Cryptocurrency_Pump-and-Dump_Schemes.pdf), [Hamrick et al.](https://par.nsf.gov/servlets/purl/10098691) |
| Copy trading | One model test: +3% net for copiers against +14% for the chosen wallets. Not replicated | MEASURED, preprint. [Resisting Manipulative Bots](https://arxiv.org/html/2601.08641) |
| Daily reversal | Long-short, top 100 most liquid pairs. Value-weighted net 0.058% a day, not significant. The paper's cost figures disagree between text and table | MEASURED. [Riksbank WP 413](https://www.riksbank.com/globalassets/media/rapporter/working-papers/2022/no.-413-trading-volume-and-liquidity-provision-in-cryptocurreny-markets.pdf) |

What small coins cost a small order. The researcher's own single snapshot of ten hand-picked coins on Coinbase and Kraken, 2026-11-24, found median spreads of about 37 and 41 bps, with single coins up to about 390 bps and a few dollars of size at the best price. It is not a study. With entry taker fees of 60 bps at Coinbase Exchange and 80 bps at Kraken Pro, a round trip costs about 1.57% and 2.01% before price impact (MEASURED, [Coinbase Exchange fees](https://help.coinbase.com/en/exchange/trading-and-funding/exchange-fees), [Kraken Pro fees](https://www.kraken.com/pro/fees)). Pump.fun charges 1.25% per trade ([Pump fees](https://pump.fun/docs/fees), MEASURED).

Law. The Senate vote of September 15, 2026 on the CLARITY Act failed 49 to 50. It was a vote on whether to start debate, a motion to reconsider was entered the same day, and the bill is not law (MEASURED, [Senate roll call 234](https://www.senate.gov/legislative/LIS/roll_call_votes/vote1192/vote_119_2_00234.htm)).

Our own replay of slow trend rules on bitcoin and ether is in `docs/research/12_replay_01_crypto_trend.md`.

## Ranked: which ideas have a reason

| Rank | Idea | Reason? | Best evidence | Main weakness | Research would |
|---|---|---|---|---|---|
| 1 | Slow trend, liquid coins, cash when down | Yes | Monash index test; 2026 paper | In-sample, index, 60.98% drop | Test on past data |
| 2 | Opportunistic insider buys, listed stocks above $5 | Yes | 72 bps a month, buys only | Gross, ends 2007 | Test on past data |
| 3 | Activist 13D, bought after filing | Partly | 7.2%, no reversal | Most of it comes before a follower can act | Test post-filing window only |
| 4 | Cross-sectional momentum, liquid coins | Weak | Old long-short spreads | Faded with dead coins and costs | Test as a comparison only |
| 5 | Buying after crypto listing news | Weak | Large raw moves | Gains come before or at the news | Test to try to disprove |
| 6 | Post-bankruptcy stocks, spinoffs | Weak | Small, old samples | Not rechecked | Watch only |
| 7 | Index inclusion | No longer | 7.6% in the 1990s | 0.8% lately, not different from zero | Leave |
| 8 | FDA and trial catalysts | No | Run-ups before good news | Pre-decision moves do not separate approvals from rejections | Leave |
| 9 | Memecoin launches, snipers, copy trading | No | Gains go to creators and fastest buyers | Late buyers lose on average | Leave |
| 10 | Pump groups, promoted stocks, chat tips | No | Insiders profit | Followers pay them | Leave |
| 11 | Penny and OTC stocks, top gainers, de-SPACs, reverse splits, day trading | No | Many samples, all negative | Negative expected return | Leave; use as exclusion filters |

Rows 6, 8 and 11 rest on papers listed with links in the stocks raw report.

## What the check changed

Where checkers disagreed, the stricter verdict is used.

- Ang et al. (OVERSTATED, VERIFIED): an excess return, not a raw index return.
- White (WRONG, VERIFIED): investor-level medians in an SEC-requested sample.
- Cohen et al. (WRONG, OVERSTATED): 82 bps is long-short, 1989 to 2007.
- Hamrick et al. (WRONG, VERIFIED with caveat): peaks, not post-alert gains.
- Nasdaq: one checker adds that a hearings panel can still grant up to 180 days to regain compliance.
- Added: Brav et al. follower share, Alpaca's OTC list, Le and Ruthbah lookback choice.
- Spread rechecks next morning: medians about 31 and 49 bps, and 34 and 40.

## Not verified or unfinished

- UNKNOWN: whether the insider and 13D effects held up recently, after costs.
- UNKNOWN: a net, out-of-sample test of any crypto rule for this account. The 2026 momentum paper was read as an abstract only.
- UNKNOWN: the share of all memecoins that go to zero.
- STATED: the curated Alpaca OTC list rests on one Alpaca comment. No page gives a count.
- The raw report dated Alpaca's client notice 2026-01-19; a checker found it is the 2022 notice. Its wording is not relied on here.
- The SEC penny stock and Rule 15c2-11 texts were not opened.

## What research proposes

1. Fund the sleeve only with ideas that pass a replay. Recommended because every positive figure here is gross and in-sample.
2. First replay: slow trend on liquid coins at one US venue reachable from Idaho, one lookback fixed in advance, real spreads and fees, dead coins kept. Recommended because it is long-or-cash and has the broadest support.
3. Second replay: opportunistic insider buys in listed stocks above $5, 2008 to 2026, buys only, after costs. Recommended because it is the strongest stock idea and untested after 2007.
4. Third replay: activist 13D entries from the day after filing, held 1 to 12 months. Recommended because it tests only what a follower can get.
5. Cap each live position by `moonshot_max_position_share` inside `moonshot_sleeve_share`, with no refill after losses. Recommended because a hard cap keeps a losing sleeve from harming the core, and leaving it unused is a valid result ([Thorp on Kelly sizing](https://web.williams.edu/Mathematics/sjmiller/public_html/341/handouts/Thorpe_KellyCriterion2007.pdf)).
6. Rule out for real money: OTC and penny baskets, memecoin launches, pump calls, copy trading, sniping and buying after listing alerts. Recommended because no source shows a follower earning on them.
7. Check the replay engine by buying top daily gainers under $5 for 5 and 20 days, delisted tickers included. Recommended because the known result is negative.
