# 25. What the evidence supports, and what to test next

Status: research synthesis. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. This page pulls together the reading in documents 01 to 21 and our own tests. It holds no results of its own. Every result of our own tests is in the table in `docs/STATUS.md`, which is written from the output files. Where this page gives a figure, it is from a cited outside source and the link is on the same line.

## The short version

- Nothing found so far supports making money fast. That is true of our own tests (MEASURED) and of every outside record with real money that could be checked (MEASURED, sources below).
- What the evidence does support is slower and smaller: slow trend rules that cut the worst drop and give up some growth, interest on idle cash, and a short list of narrow ideas that have a reason behind them and have not been tested here yet.
- The honest use of this project's next month is to test that short list cheaply, in order, and to keep saying no when a test says no.

## What our own tests say

Read the table in `docs/STATUS.md` for the figures. In words:

| Idea | What happened | Trust |
|---|---|---|
| Slow trend rules on bitcoin | A few rules pass, only at the lowest venue cost, only after audit corrections, and within a hair of the bar on one mark. In the held-back years they grew less than holding bitcoin and fell much less | MEASURED. Not a clean pass |
| Slow trend rules on ether | No pass | MEASURED |
| Day trading rules on bitcoin and ether, hourly | No pass at any venue cost. The patterns are there before fees and the fees are larger | MEASURED |
| Trend rules on a wide basket of coins | No pass. Did worse than simply holding bitcoin | MEASURED, independently audited |
| Slow trend rules on the US stock market, free index | Same shape as bitcoin: less growth than holding, a much smaller worst drop. Whether any rule "passes" hangs on one unsteady mark | MEASURED, independently audited. The index cannot be bought, so this is a first look |
| AI models making the daily call | Inconclusive by design. Every run behaved like a simple trend rule | MEASURED, too short to mean anything |

Two things about our own method were learned the hard way and matter for everything next:

- The first rig had faults. Two outside audits found them, and verdicts changed in the rerun (`docs/research/16_rig_audit.md`). Replays 04 and 05 were audited too, and one rule in replay 05 turned out not to match its plan (`docs/research/22_replay_05_stock_trend.md`). Every test from now on gets an independent audit before its result is believed.
- Pass mark 4, the overfitting estimate, moves too much to be a yes or no by itself. How to measure it more steadily is an open question for the owner.

## What outside records with real money say

These are the checks on whether "it works for someone else".

| Claim people make | What the record shows | Label |
|---|---|---|
| Contest winners prove day trading works | The US Investing Championship checks account statements, and a few traders have posted strong years more than once. The winners describe using margin and concentrated positions. The contest does not check which rules made the returns ([organizer rules](https://financial-competitions.com/rules)). Detail in `docs/research/17_verified_traders_and_their_methods.md` | MEASURED for the returns, STATED for the method |
| A famous stock-picking method can be run as a rule | The fund built on the IBD 50 list returned 3.72% a year against 13.71% for the S&P 500 from April 2015 to December 2025 ([SEC prospectus](https://www.sec.gov/Archives/edgar/data/0002104659/000121390026047001/ea0286847-05_497k.htm)) | MEASURED |
| AI models trade well with real money | In the cleanest funded test, the best model made +3.72% while bitcoin made +11.63% over the same period ([OKX study](https://arxiv.org/html/2609.34510v1)). In the Alpha Arena contest an outside rebuild finds 31 of 38 accounts lost ([TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)) | MEASURED, author-reported, and STATED |
| An AI-run stock fund beats the market | The AIEQ fund has trailed the S&P 500 by about 5 points a year since 2017 ([AIEQ prospectus](https://www.sec.gov/Archives/edgar/data/1633061/000121390026008328/ea0273008-02_497k.htm)) | MEASURED |
| Trend funds beat holding | Pacer Trendpilot returned 9.35% a year against 13.35% for the S&P 500 from June 2015 to December 2024 ([PTLC prospectus](https://www.sec.gov/Archives/edgar/data/1616668/000089418925006695/pacertrendpilotuslargecape.htm)). The bitcoin trend fund BTRN returned 5.41% a year against 15.46% for bitcoin from launch to December 2025 ([BTRN prospectus](https://www.sec.gov/Archives/edgar/data/1432353/000143235326000251/a497kbitcointrendstrategy.htm)) | MEASURED |
| Penny stocks, memecoin launches, pump groups, copy trading | No gain for a follower in any study found. Detail in `docs/research/13_high_risk_sleeve_evidence.md` | MEASURED |

The pattern is the same in our tests and in the live funds: trend rules lower the ride's worst point and cost growth. That agreement between two independent kinds of evidence is the most solid thing this project knows.

## If the goal is speed, what each route really is

The owner asked for fast, and for a middle risk level with a small share for moonshots that have a reason. This is what each fast route is, said plainly.

| Route | What it is | What the evidence says |
|---|---|---|
| Borrowed money or futures on a trend rule | Makes a small edge bigger and a normal drop fatal | Barred here until a decision record says otherwise (`AGENTS.md` hard rule 10). The contest winners used it. It multiplies whatever the rule is, and our rules have no clean pass yet |
| Day trading | Many small trades | Fees ate every rule tested on crypto. SPY and QQQ at zero commission are the one untested case, and the one outside reproduction held puts the room for costs under the value in `intraday_trend_max_round_trip_bps` |
| Small coins and new tokens | Big moves | The wide basket lost to holding bitcoin in our test. Launch buying loses in the studies found |
| Letting an AI model pick trades | Hope that the model sees something | No funded record shows it. Our pilot was inconclusive |
| Concentrated buying of stocks at new highs with tight exits | What the contest winners say they do | Untested here. Needs stock data that includes companies that later died, or the test flatters itself. This is the one fast-looking idea with a real record behind it, and it is in the queue below |

A moonshot share makes sense only for an idea that has a reason and has passed a replay. Three such ideas are named in `docs/research/13_high_risk_sleeve_evidence.md`. None has been tested yet.

## What to test next, in order

Ranked by how much could be learned for how little cost and risk. Each needs a plan written and pushed before it runs, ledger rows first, and an independent audit after.

| # | Test | Why this rank | Needs |
|---|---|---|---|
| 1 | One slow bitcoin rule in a practice account, as observation only | It is the nearest thing to a pass, it costs nothing, and it starts the forward record that `paper_min_trading_days` and `paper_min_closed_trades` ask for | Practice keys from the owner |
| 2 | Replay 06: slow trend on funds that can be bought | Turns the stock index result into something that could be traded, with real opening prices | The data purchase. Plan drafted |
| 3 | Replay 07: day trading SPY and QQQ on one-minute bars | The only day trading case not yet ruled out. Research expects a fail and will measure it | The same data purchase. Plan drafted |
| 4 | Credit interest on idle cash in every replay | Trend rules sit in cash a lot. Bills paid 4.11% to 4.59% on 2026-11-24 ([Treasury daily bill rates](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_bill_rates&field_tdr_date_value_month=202611)). The crypto replays credit nothing, which understates the rules. Small, near-certain | Nothing. A rig change with its own plan |
| 5 | Insider buying that is not routine, in listed stocks | The one stock-picking screen with a mechanism and a published study, though the study is from 2012 and must be redone on recent data after costs (`docs/research/19_information_feeds.md`) | Stock price data. SEC filings are free |
| 6 | A plain statistical model against a simple tree model on bitcoin and ether, logged only | The best-supported machine learning result found is that the plain model won after costs (`docs/research/18_ai_systems_with_live_records.md`). Worth one cheap forward check | Nothing |
| 7 | Holding a small-company fund overnight only | Beat holding in 2020 to 2026 and lost in 2010 to 2019, and the funds built on it closed (`docs/research/20_small_account_edges.md`). Low rank. Fails at a few bps of cost | The data purchase |
| 8 | Buying stocks at new highs with tight exits | The contest winners' stated method. Fast if it works. Needs data with dead companies kept, which costs more | A larger data purchase. Decide after 2 and 3 |

Not on the list, with the reason:

- Limit orders in place of market orders. It could cut costs a lot, and it cannot be tested honestly on daily or hourly bars. It needs trade-by-trade data. Not feasible with what is held.
- More crypto day trading rules. Every one tested lost to fees.
- More coins. The wide basket lost to bitcoin.

## What would change this picture

- A rule that passes all five marks on two price histories, at a cost the owner can really get, and still passes when mark 4 is measured the steadier way.
- A forward record in a practice account that tracks its replay.
- An outside funded record, with rules published, that beats holding after costs. None was found. If one appears it goes to the top of the queue.

## Where each part of this comes from

- Our tests: `docs/STATUS.md`, then `docs/research/16_rig_audit.md`, `docs/research/22_replay_05_stock_trend.md`, `docs/research/23_replay_04_coin_basket.md`, `docs/research/14_ai_calls_pilot_02.md`, `docs/research/24_order_book_costs.md`.
- Traders and contests: `docs/research/17_verified_traders_and_their_methods.md`.
- AI systems with live records: `docs/research/18_ai_systems_with_live_records.md`.
- Feeds: `docs/research/19_information_feeds.md`.
- Small edges: `docs/research/20_small_account_edges.md`.
- Funds and published rules: `docs/research/21_systematic_funds_and_published_rules.md`.
- High-risk ideas: `docs/research/13_high_risk_sleeve_evidence.md`.
