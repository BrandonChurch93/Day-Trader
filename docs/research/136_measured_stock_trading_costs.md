# Measured stock trading costs

MEASURED. Across 56 stocks and funds, the quoted half-spread was 1.126 bp in the middle of all sampled regular-hours observations and 2.422 bp in the first half hour. That is about $0.056 and $0.121 per side on $500 actually traded. STATED. The time machine assumes 5 bp per side ($0.25 on $500 traded), which is above both medians, but not above the opening tail.

## What it costs to cross the quote

- STATED. Crossing means buying at the ask or selling at the bid. Measured from the midpoint of those two prices, you pay half the spread each time. One basis point (bp) is 0.01%, or $0.05 per $500 traded. A buy and a later sale each pay their own half-spread; neither the quote nor the price has to be the same.
- STATED. The dollar columns scale the quote to $500 of midpoint value. A $500 cash buy gets the whole number of shares that fit at the ask (round down, before any separate fees). Multiply that share count by half the bid-to-ask gap for the actual quote cost. For example, at a $99.99 bid and $100.01 ask, $500 buys 4 shares and crossing costs $0.04, not $0.05. If one share costs more than $500, there is no whole-share order. The sale uses the actual shares held and the bid at that time.
- MEASURED. The first three rows below pool all usable observations within each time window. The group rows instead give each symbol one vote: they take the middle of the already saved symbol medians, not a pooled group median. The saved 90th percentile (p90) is the level at or below which about nine in ten pooled observations fell.

| Sample | First 30 min, bp / $ | Midday, bp / $ | Last 30 min, bp / $ | All regular hours, bp / $ | Exact close |
| --- | ---: | ---: | ---: | ---: | --- |
| All 56, pooled median | 2.422 / $0.121 | 1.086 / $0.054 | 0.843 / $0.042 | 1.126 / $0.056 | UNKNOWN |
| All 56, pooled p90 | 10.055 / $0.503 | 3.832 / $0.192 | 2.440 / $0.122 | 4.941 / $0.247 | UNKNOWN |
| Usable observations | 3,129 | 6,706 | 3,263 | 13,098 | Not a separate bucket |
| Broad equity index ETFs (5) | 0.342 / $0.017 | 0.209 / $0.010 | 0.176 / $0.009 | 0.210 / $0.011 | UNKNOWN |
| Bond ETF (TLT only) | 0.609 / $0.030 | 0.610 / $0.030 | 0.610 / $0.030 | 0.610 / $0.030 | UNKNOWN |
| Sector equity ETFs (11) | 0.888 / $0.044 | 0.587 / $0.029 | 0.587 / $0.029 | 0.587 / $0.029 | UNKNOWN |
| Gold fund (GLD) | 0.540 / $0.027 | 0.399 / $0.020 | 0.265 / $0.013 | 0.399 / $0.020 | UNKNOWN |
| Single stocks (38) | 3.787 / $0.189 | 1.591 / $0.080 | 1.074 / $0.054 | 1.668 / $0.083 | UNKNOWN |
| Closed-end funds (none in roster) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

- MEASURED. The five broad equity ETFs were DIA, IWM, QQQ, SPY and VTI. Even in the first half hour, their typical spread cost was under two cents per $500 traded.
- MEASURED. TLT is the only bond fund: about $0.030 per $500 traded at its regular-hours median. It does not stand in for corporate, high-yield, or closed-end funds. The pooled opening p90 is about $0.503, twice the time machine's $0.25 allowance.
- MEASURED. 17 of 38 single stocks had a first-half-hour median above the 5 bp allowance. The range of their opening medians was 0.747 to 9.354 bp. A broad ETF quote is a poor stand-in for a stock at the open.

## What the stock and fund tests charged

STATED. Costs below are on the amount traded, per buy or sell, unless noted. The comparison is to the quote crossing alone, not to all-in execution. A fixed allowance can exceed the median spread and still be too low at some clocks or for some stocks. The replay settings and saved verdicts come from the linked reports and [thresholds](../../config/thresholds.yaml).

| Scored stock or listed fund test | Cost per side (STATED) | Against this measurement |
| --- | --- | --- |
| [Time machine TM04, large-stock picker](36_time_machine_tm04_stock_basket.md) | 5 bp assumed half-spread on traded value | Above the typical stock midday and late quote; some stocks cost more at the open. |
| [05, US stock-index trend](22_replay_05_stock_trend.md) | 2, 5 and 10 bp scenarios | Above broad ETF medians, but the old index series was not a tradable fund; no pass was credited. |
| [06, ETF trend](35_replay_06_fund_trend.md) | 5 bp including modeled slippage | Above the broad ETF and sector ETF medians. |
| [07, SPY and QQQ intraday](27_replay_07_intraday_spy_qqq.md) | 2 and 5 bp judged; 0.5 bp shown only | Both judged levels exceed each fund's p90 in all three sample buckets. |
| [11, earnings reader, design score only](44_replay_11_earnings_reader.md) | 5 bp S&P 500, 10 bp MidCap 400, 20 bp SmallCap 600 | 5 bp is above the typical large-stock quote; the mid- and small-cap lists are not measured here. No held-back verdict. |
| [12, congressional purchases](47_replay_12_congress_followers.md) | 10 bp on turnover | Above the typical large-stock opening quote; actual historical names and timing differ. |
| [14, large-stock momentum](52_replay_14_large_stock_momentum.md) | 5 bp on traded value | Above the typical large-stock opening quote, but below some opening medians and tail quotes. |
| [21, odd-lot tenders](97_replay_21_odd_lot_tenders.md) | Greater of 10 bp or $0.05/share on market fills; $0 judged tender fee | Above the typical measured stock quote; tender names and the tender payout mechanism are not measured here. |
| [23, IPO fast-track](72_replay_23_ipo_fast_track.md) | 10 bp judged; 25 and 50 bp shown | Above the typical late stock quote, not a measure of IPO or auction fills. |
| [25, TLT month-end](69_replay_25_treasury_month_end.md) | 2 bp judged; 5 and 10 bp shown | Above TLT's last-half-hour median and p90. The close itself is not measured here. |
| [31, bond ETF month-end](80_replay_31_bond_fund_month_end.md) | 2 bp judged; 5 and 10 bp shown | Above TLT's median as a reference only; the traded bond funds were not sampled. |
| [33, Treasury auction days](89_replay_33_treasury_auction_days.md) | Bought at SIP ask and sold at bid; $0 modeled baseline fees. Mean quoted costs: 0.477 bp in, 0.463 bp out on auction trades | Below this sample's TLT median, but the replay used IEF as well and its own quotes and clocks. |
| [35, IBIT at CME expiry](81_replay_35_cme_bitcoin_expiry_ibit.md) | Bought at SIP ask and sold at bid; zero commission, historical SEC and FINRA sell fees | No fixed bp. IBIT and its premarket entry are outside this sample. |
| [39, IWM pre-holiday](84_replay_39_iwm_pre_holiday.md) | 2 bp judged; 5 and 10 bp shown | Above the IWM last-half-hour median and p90; not an auction measurement. |
| [41, SPY/TLT month-end switch](92_replay_41_month_end_laggard_switch.md) | 2 bp judged; 5 and 10 bp shown | Above the late quote median and p90 for both ETFs. |
| [48, muni closed-end funds](103_replay_48_muni_cef_january.md) | Own closing half-spread plus 5 bp; 55 bp total with short quote cover | Adds 5 bp beyond its own measured spread where available; closed-end funds and MUB were not sampled here. |
| [52, corporate bond quarter-end](113_replay_52_quarter_end_corporate_bond_funds.md) | 2 bp on the traded basket; Treasury proxy untraded | Above TLT's median as a reference only; the traded corporate bond funds were not sampled. |
| [53, taxable closed-end funds](122_replay_53_taxable_fund_january_rebound.md) | Own closing half-spread plus 5 bp; 55 bp total with short cover; for a missing exit use the higher of entry half-spread or 50 bp, plus 5 bp | Adds 5 bp beyond its own measured spread where available; closed-end funds and PCEF were not sampled here. |
| [60, special-dividend declarations](126_replay_60_special_dividends.md) | Greater of 5 bp or $0.01/share; 10 bp with the same floor shown | Above the large-stock median at both clocks, not necessarily an opening tail quote or distressed name. |
| [62, special-dividend ex-day](130_replay_62_special_dividend_ex_day.md) | Greater of 5 bp or $0.01/share; 10 bp with the same floor shown | Above the late large-stock and IWM medians; not an exact-close measurement for these names. |
| [65, SPY/IEF rebalancing](../STATUS.md) | [Greater of 2 bp or $0.01/share](../../research_rig/PREREG_65_stock_bond_rebalance_spread.md) on each leg's traded value, plus borrow on shorts | Above SPY's late median and p90. IEF and borrow are not measured here. |

## Were any verdicts close enough for costs to matter?

- STATED reading. Replay 25 is the clearest cost-sensitive verdict. MEASURED in its saved rows: TLT passed at 2 bp per side (t 2.36) and the shown 5 bp case fell below the t mark of 2 (t 1.80). This sample's TLT late quote is about 0.61 bp a side, below the judged cost, not evidence that the actual closing fill was cheap.
- STATED reading. Replay 39 came close on one mark: the 2 bp allowance versus the IWM late quote median of 0.176 bp is about 3.65 bp of room over two sides. That is enough to make the net t miss at 1.91 look cost-sensitive, not enough to rescue the verdict: the other missed mark was the gross comparison (Welch t 1.82 against 2). Replay 41's saved rows also show one mark is cost-sensitive: plain t went from 2.29 at 2 bp to 1.86 at 5 bp, but the paired t was only 0.14 and 0.22, respectively.
- STATED reading. For Replay 07, even the highest saved break-even cost against holding was only 1.80 bp round trip on QQQ. The sampled SPY and QQQ quote medians can be cheaper than that scale, so a break-even comparison could change. It is not a five-mark pass: the reported judged rules missed multiple marks, and the low-cost rows were shown only.
- STATED reading. The stock spread allowance is on the scale of some small raw-return misses, not evidence of full flips. Replay 62 missed its raw paired mean by 6.07 bp; both the stock and IWM paid costs, so removing a gross 10 bp round trip from the stock alone is not the answer. The saved 10 bp-per-side stress still had a negative paired mean, and the clustered t, trimmed mean and year count also missed. In Replay 60 the sole miss was a matched t of 1.23 against 2, not an unpaired mean just short of zero. Replay 65 was positive on average but had clustered t 1.04 and a negative trimmed mean; this quote sample cannot price its two legs at the close.
- STATED reading. There is no basis here to recost the corporate bond or closed-end funds. Replay 31's residual mean (-3.38 bp) and Replay 52's plain mean (-3.08 bp) missed zero by about the size of their 4 bp nominal round-trip allowance. But Replay 31's gross inside-versus-outside comparison missed, and Replay 52's quarter-ends lagged ordinary month-ends by 15.87 bp. Replay 48's saved zero-cost line still had eight positive years, while Replay 53's saved zero-cost line still had only six positive years and six ahead of PCEF. Those lines keep judged share sizes.
- STATED reading. Replays 33 and 35 already used their own spreads, and the sampled quotes do not fix their failed comparison marks. Replay 21 was short 16 placements, and Replay 23's recent mean was -142 bp, a larger loss than the full 20 bp nominal round-trip allowance at judged cost. The remaining rows do not show an all-marks flip from this cost comparison.
- UNKNOWN. Verdicts at the actual cost of each historical order. These are readings of already published marks and shown-only checks. No score was run, and no verdict or judging cost changes.

## What was and was not measured

- MEASURED. Alpaca historical consolidated SIP bid and ask quotes, June 2026 through November 24, 2026. The collector drew 40 regular-session minutes in each of six months (seed 20261125): 10 in the first half hour, 20 in the middle and 10 in the last half hour, all relative to the exchange session. It kept the first usable returned quote within 3 seconds, or within the sampled minute if needed. Positive bids and asks were required; locked quotes could count, crossed quotes and half-spreads over 500 bp could not. There were 13,098 usable symbol-minutes of 13,440; 342 missing were not filled in.
- STATED. The all-hours row pools the sampled buckets, not all minutes of the session in their natural proportions. These were snapshots of displayed quotes, not time spent at a spread, orders sent or trades filled.
- UNKNOWN. Opening and closing auction fills, the exact close and exact opening print, odd-lot price improvement, displayed size available to a $500 order, delays, market impact, fees or taxes on real fills, and days outside the sample window. The last half hour does not measure the closing auction.
- UNKNOWN. The saved aggregate has counts, medians and p90s, not p75s, share of time at a one-cent spread, or the prices and sizes needed to reconstruct exact whole-share dollar costs. It also cannot tell how many sampled quotes were unaffordable for $500. No new quote requests were made to fill these gaps.
- STATED. [Page builder](../../tools/report_stock_trading_costs.py) reads only the saved aggregate at `/home/user/workspace/rig/stock_spreads_measured.json` (SHA-256 `793817cf246d1f0bbeaac42d5c10875b37f41d5737e17a565ce64dcf4f92ceed`). The original collector `/home/user/workspace/rig/measure_spreads.py` (SHA-256 `194ef7f0dcf59b9d70bf52a56ece1a015505581dbc4d0ee5d947feb842c06b57`) is provenance only and was not run. No raw quotes, per-quote rows, or off-repo replay inputs or results were read for this page.
