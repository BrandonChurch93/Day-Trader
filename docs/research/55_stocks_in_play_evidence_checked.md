# 55. Day trading stocks in play: what is published, checked

Status: reading gathered 2026-11-25 19:32 UTC by a helper; a second helper then opened every source: 29 claims confirmed, 3 wrong and corrected here, 0 not found. Nothing on this page was measured by us. Every line is STATED from the linked source unless marked.

Why it was read: the owner day trades the coins people are chasing. The stock version is "stocks in play": each morning the stocks with unusual volume in the first minutes. Replay 07 tested day trading rules on SPY and QQQ only and none passed.

## The published design

- The rule: US stocks priced above 5 dollars with average volume of at least 1,000,000 shares and a daily range above 0.50 dollars; each day take the 20 with the largest volume in the first five minutes against their own 14-day average for those minutes; buy or sell short on a break of the first five-minute bar in its own direction, stop at a tenth of the daily range, out at the close; risk 1% a trade, up to 4x leverage ([Zarattini, Barbon and Aziz, 2024](https://concretumgroup.com/wp-content/uploads/2026/02/A-Profitable-Day-Trading-Strategy-For-The-U.S.-Equity-Market.pdf)).
- The claim, 2016 to 2023, about 7,000 stocks with dead ones kept: +1,637% in total, 41.6% a year, against +198% for the S&P 500. The same rule without the volume filter: +29% in total. Costs: a broker commission of 0.0035 dollars a share and no slippage ([Zarattini, Barbon and Aziz, 2024](https://concretumgroup.com/wp-content/uploads/2026/02/A-Profitable-Day-Trading-Strategy-For-The-U.S.-Equity-Market.pdf)).

## What happened when others rebuilt it

- One independent rebuild got the paper's result with no slippage (100 grew to 851), then measured what the breakout order really paid on 549 entries: a middle of 1.0 cent, an average of 2.4 cents, a tenth of them 7.8 cents or more, about 12% of the stop distance. With 1 cent and 0.025% a fill, 100 fell to 0.91. It used 0.5% risk a trade, not 1% ([Waka Research](https://candidpnl.wakaresearch.com/lab/orb-autopsy)).
- The same rebuild found that with one-minute bars the order of the fill and the stop inside one bar cannot be known, and the two ways of settling it give between -55% and +117% a year. 44% of the unclear entries were stopped out ([Waka Research](https://candidpnl.wakaresearch.com/lab/orb-autopsy)).
- On QQQ alone the same family of rule goes from a good figure to near nothing at 2 to 4 cents of slippage, and most of its profit came from 2022 ([Nifty Edge Research](https://github.com/2005legend/nifty-edge-research/blob/main/research_notes/02_strategy_evidence_part1.md)). A rebuild on five index futures got the gross figure and nothing after costs ([MQL5 Blog](https://www.mql5.com/en/blogs/post/776235)).
- Corrected: one slippage table first reported for a 4,924-stock test belongs to a QQQ version of the rule ([Clockout Capital](https://clockoutcapital.com/learn/opening-range-breakout-tested)).

## Other day trading rules on single stocks, after costs

- Buying a 5% gap up at the open, 1,113 stocks, 2017 to 2026: a loss of 1.54 dollars per 100 dollars risked at 1 cent of slippage ([SeptInvesting](https://septinvesting.com/research/gap-and-go-5-percent)).
- Buying when the price climbs back over the day's average price, 67,126 trades: a loss of 0.34 dollars per 100 risked at 1 cent ([SeptInvesting](https://septinvesting.com/research/vwap-reclaim-long)).
- The first half hour predicting the last half hour: 4.46% a year after costs on SPY in the paper. Corrected: that figure is for July 2001 to 2013, not from 1993 ([Gao, Han, Li and Zhou, 2018](https://www.scribd.com/document/967970408/Intraday-Momentum-The-First-Half-hour-Return-Predicts-the-Last-Half-hour-Return-1)). Rebuilds after publication lost after costs ([Dead Signals Lab](https://deadsignalslab.substack.com/p/replication-intraday-momentum-eight)).
- A later rule by the same authors on SPY, 2007 to early 2024: 19.6% a year with a small slippage charge ([Zarattini, Aziz and Barbon, 2024](https://alexandria.unisg.ch/server/api/core/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/content)). On Nasdaq futures a rebuild kept part of it on later years for the buying side. Corrected: the selling side failed on the early years and made money on the later ones, which the author puts down to two falling years ([EdgeLab](https://edgelabtrading.com/blog/zarattini-intraday-momentum-nasdaq/)).
- Trading after a headline, 144,659 news items: no dependable drift in liquid stocks ([Quantisnow](https://www.quantisnow.com/research/after-the-headline/after-the-headline.pdf)).

## What real day traders made

- Taiwan, every day trader 1992 to 2006: fewer than 1 in 100 made money year after year ([Barber, Lee, Liu and Odean, 2014](https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/The%20Cross-Section%20of%20Speculator%20Skill.pdf)).
- Brazil, the 1,551 people who day traded for at least 300 days: 97% lost money ([Chague, De-Losso and Giovannetti, 2020](https://repositorio.fgv.br/server/api/core/bitstreams/0f00dd78-6909-4f91-84d5-aef8803e6436/content)).
- India: 71% of people day trading stocks lost money in the year to March 2023 ([SEBI, 2024](https://www.sebi.gov.in/sebi_data/attachdocs/jul-2024/1721818140715.pdf)).

## What this means for us

- The headline result rests on an order that nobody fills at the printed price. One rebuild with measured fills says it loses. That is one source, and we have not measured it.
- One-minute bars are not enough to test this family honestly. It needs the trades and the bid and ask around each entry.
- We can read past bids and asks from our price feed. So the cheap honest step is to measure, on a sample of mornings, what a breakout order on a stock in play would really have paid, before building anything else. If it is near the 2.4 cents others found, the idea is dropped with our own number. If it is near zero, the full test is worth building. That is queue row 23 (`docs/QUEUE.md`).
- The real-money records say the same thing as our own replays so far: day trading with plain rules is where most people lose.
