# A fair test of an AI trader: what others found, and how we would test it

Last verified: 2026-11-25.

Scope: what is publicly known about AI models trading real or pretend money on new market data, and a proposed design for our own test in a practice account. No account was opened, no key was requested and no order was placed for this research.

How it was made: one researcher wrote a report from primary pages, `docs/research/11_raw/ai_trader_test_design.md`. Two fresh checkers, on different models, re-opened the primary pages for the five key claims (A1 to A5). Their tables are in `docs/research/11_raw/check/`. Where a checker changed a figure, this file carries the checker's version.

Tags: MEASURED means read on a primary page, not that anyone audited the trades behind it. STATED means someone's claim, not confirmed on a primary page. UNKNOWN means not found, which is not the same as absent.

Status of everything recommended here: proposed by the research team. Nothing in this file is an owner decision.

## Words used here

| Word | Meaning |
|---|---|
| Forward test | The model decides before the outcome exists |
| Replay | The model is shown old prices one day at a time, as if they were new |
| Knowledge cutoff | The date after which, by the maker's own statement, the model knows little or nothing |
| Holding | Buying at the start and doing nothing. The simplest benchmark |
| Trend rule | A fixed rule with no AI, such as "hold when price is above its moving average" |
| Alpha | Return left over after removing what the market as a whole did |
| Sharpe ratio, per period | Average return per period divided by its wobble |
| Independent observation | A period whose result does not repeat another's |

## Bottom line

| # | Question | Answer |
|---|---|---|
| 1 | Have AI models beaten holding with real money? | Not shown. The one funded test scored against holding (OKX) fell short of it. Kalshi models all lost. Crypto arenas scored only against cash. The gains that circulate come mostly from pretend money |
| 2 | Can a replay of past prices settle it? | No. The model may have read those prices in training. Even after a stated cutoff, the cutoff is only the maker's statement |
| 3 | How long must a test run? | Hundreds of independent observations to detect a small edge, under kind assumptions. Real markets need more |
| 4 | What test does research propose? | A forward test in an Alpaca practice account: one frozen model setup against a fixed trend rule, pass mark written first |

Our own pilot points the same way. `docs/research/14_ai_calls_pilot_02.md` ran six model runs on 147 days of past prices. It was declared inconclusive before it ran, and every run behaved like a plain trend rule.

## What happened when AI models traded

| Test | Who ran it | Money | Dates | What was traded | Result against holding | Main weakness |
|---|---|---|---|---|---|---|
| Prediction Arena, cohort 1 | Paper authors, [Prediction Arena paper](https://arxiv.org/html/2604.07355v1) | Real, $10,000 per model | Jan 12 to Mar 9, 2026 | Kalshi and Polymarket event contracts | All six lost 16.0% to 30.8% on Kalshi. The same models averaged 1.1% lost on Polymarket against 22.6% on Kalshi. No holding benchmark exists for event contracts. MEASURED | 57 days. Weather markets dominated. Not confirmed that all fees were deducted from the returns |
| Can AI Make Money in Crypto | Paper authors, [OKX paper](https://arxiv.org/html/2609.34510v1) | Real | Aug 24 to Sep 21, 2026 | Bitcoin and other crypto, spot and perpetuals | 0 of 4 beat holding bitcoin, which made 11.63%. Only one was a language model (Qwen), and it made 3.72%. Median of the four was minus 0.56%. MEASURED | 28 days. Three of four were older machine-learning models. Paper says five were selected but reports four |
| Beta, Not Alpha | Paper authors, [Beta, Not Alpha paper](https://arxiv.org/html/2611.19530v1) | Pretend, replayed | 2020 crash, 2022 bear market, Jan 2 to Nov 11, 2026 | 56 US stocks, long-only | 91 runs of six models. No run had significant alpha. Average alpha was minus 2.3% a year. MEASURED | Mid-size and small models only. Today's large companies, so survivors only. Models could remember 2020 and 2022 |
| Nof1 Alpha Arena, season 1 | Nof1, [Nof1 technical post](https://alphaarena.ai/blog/TechPost1) | Real, $10,000 each | Ended Nov 3, 2025 | Six crypto perpetuals | From a third-party reconstruction: two of six ended above cash, the rest lost 42% to 59%. No holding benchmark scored. STATED, [TradeRank reconstruction](https://www.traderank.ai/alpha-arena-leaderboard) | Short. Organizer itself flags luck and prompt sensitivity |
| BingX AI Arena | Crypto exchange, [BingX rankings](https://bingx.com/en/blog/article/bingx-ai-arena-ranking-the-six-llm-traders-after-a-big-week) | Real, $10,000 each | From Nov 2025 | Crypto | Nov 18, 2025 snapshot only: two of six above $10,000. No benchmark beyond cash. MEASURED as a snapshot | Exchange marketing for copy trading |
| Rallies AI Arena | Rallies, [Rallies support](https://support.rallies.ai/ai-arena/overview) | Pretend, $100,000 | Late Nov 2025 onward | US stocks and options | Organizer post of Nov 22, 2026 shows ChatGPT up 58% against the S&P 500 up 2.5%. The organizer's own figure, [Rallies results post](https://x.com/ralliesarena/status/2124551408317808942) | Pretend money. Rallies says slippage, fees and market impact are not fully modeled |
| TradeRank | Independent site, [TradeRank methods](https://www.traderank.ai/how-it-works) | Pretend, $10,000 | Since Jan 2026 | 10 crypto, 50 US stocks | Across 11 seasons, 38.9% of model seasons were profitable. MEASURED | One fill price, no slippage. Beating a falling market can just mean holding cash |

Six other research trials used pretend money or did not say. They are in the raw report and were not re-checked.

No public, funded trading test run by Anthropic, OpenAI or Google was found. UNKNOWN.

## Why a replay cannot settle it

A model may have read the prices and news of a past period in training, so in a replay it can "predict" what it already knows. In a study cited by the raw report, excess return fell by 17 to 22 points in a window the models could not have seen ([point-in-time comparison](https://arxiv.org/html/2601.13770v1)). Leaks also come from data: news joined by calendar date rather than publication time turned a loss into a gain in the Beta, Not Alpha study ([Beta, Not Alpha paper](https://arxiv.org/html/2611.19530)). Both MEASURED, not re-checked.

The makers' own stated cutoffs, all MEASURED on the makers' pages:

| Model | What the maker states | Source |
|---|---|---|
| Claude Fable 5.2 | Reliable knowledge cutoff Jun 2026. Training data cutoff Jun 2026 | [Anthropic Fable 5.2 page](https://platform.claude.com/docs/en/models/fable-5-2/overview) |
| Claude Opus 5.5 | Reliable knowledge cutoff Jun 2026. Training data cutoff Jun 2026 | [Anthropic Opus 5.5 page](https://platform.claude.com/docs/en/models/opus-5-5/overview) |
| GPT-6.2 Sol | Knowledge cutoff Jun 01, 2026 | [OpenAI GPT-6.2 Sol page](https://developers.openai.com/api/docs/models/gpt-6.2-sol) |
| GPT-6.2 Astra | Knowledge cutoff May 18, 2026. From the raw report, not in the check | [OpenAI Astra page](https://developers.openai.com/api/docs/models/gpt-6.2-astra) |
| Gemini 4 Carbon | Knowledge cutoff March 2026, "though in some domains the model's knowledge may be less up to date" | [Gemini 4 Carbon model card](https://deepmind.google/models/model-cards/gemini-4-carbon/) |

These are the makers' statements. OpenAI and Google give a knowledge cutoff only, not a separate training data cutoff (UNKNOWN). A stated cutoff does not prove a run sees only past information, especially if the model can search the web. The second checker notes that, as of now, this leaves only about 5 to 8 months of prices after the cutoffs, which is too short on its own.

So a replay can test the plumbing and the model's behaviour, not skill. A model that passes our replay marks (keys in `config/thresholds.yaml` starting `replay_` and `backtest_`) has still not shown skill.

## How many independent days a test needs

The report's arithmetic, MEASURED from [Bailey and López de Prado](https://www.davidhbailey.com/dhbpapers/sharpe-frontier.pdf) and [Lo on Sharpe ratios](https://alo.mit.edu/research-page/the-statistics-of-sharpe-ratios/):

| Situation | Edge per period (Sharpe, not yearly) | Independent observations needed |
|---|---|---|
| Confidence that an edge already seen is real, 95% | 0.10 | about 273 |
| Same | 0.05 | about 1,085 |
| Planning a test that finds a real edge 4 times in 5 | 0.10 | about 619 |
| Same | 0.05 | about 2,475 |

The assumptions, in plain words:

- Each period's result is independent of the others.
- Returns follow the bell curve, with no extreme days.
- The hurdle is zero, so any positive edge counts.
- The thing measured is the AI's net return minus the comparator's net return, on the same dates.
- An edge of 0.10 means the average daily gain over the comparator is one tenth of its daily wobble.

Real markets break the first two, so the true count is higher. Calling the model many times on the same day adds no new market periods. Every prompt and setting tried must also be counted, because the best of many tries looks good by chance ([Deflated Sharpe Ratio](https://davidhbailey.com/dhbpapers/deflated-sharpe.pdf)). These are counts of observations, not a schedule.

## The proposed fair test

The venue is an Alpaca practice account, as proposed in `docs/research/09_brokers_and_venues.md`. The minimum length of the practice period is set by `paper_min_trading_days` and `paper_min_closed_trades`. Everything below is from the raw report's proposed test.

Fixed in writing first, with a timestamp, before the first scored call:

- The question: can one frozen Claude Fable 5.2 setup add reliable value after costs over a simple trend rule, with the same information, money and risk budget.
- One main comparator and one return series.
- A positive hurdle in return units, a one-sided 95% confidence rule, a minimum sample and market coverage.
- Risk and data pass marks, a fixed rule for when the model gives no answer, and the stop rules.

What the AI is compared with:

- Main comparator: a preset moving-average trend rule.
- Also reported: fixed-weight holding, and random entries with the same holding time and size.
- Several isolated Claude copies with identical prompts, all paths reported.
- All arms use the same clock, the same quotes, fees, slippage and dividends.

Money and permissions:

- Equal pretend balances in liquid US funds, and bitcoin and ether, scored separately.
- No leverage, derivatives or transfers. Live routing off.
- A checker program, not the model, sets position size, caps exposure and rejects stale or invalid orders.
- No web, no outside memory, no direct order access. News or tools only in separate arms registered in advance.

What is logged for every decision:

- Deadline, inputs with their publication and receipt times.
- Exact model version, prompt, settings, response and a short reason.
- Retries, quotes, order and fill IDs, costs and positions.
- Holds and failures. Saved before the order is sent.

Pass, inconclusive and fail:

- Pass: the lower end of the confidence range for net outperformance over the trend rule clears the written hurdle, and the risk and data gates pass.
- Inconclusive: too few observations or too little market coverage to tell.
- Fail: the raw report does not spell this out. This file proposes that a full-length test which is not a pass counts as a fail, as does any failed risk or data gate.

What stops or splits the test:

- A change in model version, stale data or an order routing fault, each defined in advance. Failures stay in the record.
- Never stopping, or changing anything, because results look good or bad.
- The test authorizes no move to live money.

## What the check changed

| Claim | Change |
|---|---|
| A1, Kalshi funded test | Held. Narrowed: only cohort 1 (six models) traded real money. The four newer models were pretend money for 3 days. On Polymarket the same models averaged a much smaller loss. The checkers disagreed on fees: one said fees were counted in solvency checks, the other that deduction from the returns is not confirmed. This file uses the stricter reading |
| A2, OKX funded test | Held. Narrowed: three of four live methods were older machine-learning models, only Qwen was a language model. 28 days. Paper says five selected, four reported |
| A3, Beta, Not Alpha | Held. Narrowed: simulated, long-only, mid-size and small models, today's large companies |
| A4, cutoffs | Held. These are the makers' own statements. OpenAI and Google state knowledge cutoffs only |
| A5, Rallies | Held. Pretend money, costs not fully modeled |

## Not verified or unfinished

- The other research trials and competitions in the raw report were not re-checked.
- Nof1 season 1 final results come only from a third-party reconstruction.
- Separate training data cutoffs for OpenAI and Google models. UNKNOWN.
- Whether a model name can be pinned to one unchanging build. UNKNOWN.
- Whether each provider's usage rules allow this exact practice setup. No explicit approval found. UNKNOWN.
- How far Alpaca practice fills differ from real fills. UNKNOWN.
- The right hurdle, sample size under real market dependence, and whether news or tools add anything. UNKNOWN.

## What research proposes

1. Treat replay results for AI models as a plumbing and behaviour check only, because the model may have read the past.
2. Run the forward test in an Alpaca practice account, because it is free and uses the same connection as live (see `docs/research/09_brokers_and_venues.md`).
3. Compare against the preset trend rule as the one main comparator, because our pilot found every run behaved like one.
4. Fix the hurdle, sample size and stop rules in writing before the first call, because a test judged after the fact can pick its own winner.
5. Freeze one model setup and log its exact version, because a silent model update makes it a different test.
6. Report an inconclusive result as inconclusive, because the arithmetic above needs hundreds of independent observations.
7. Make no move to real money from this test alone, because no funded test found has shown a gain over holding.
