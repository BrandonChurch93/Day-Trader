# Start here

Last verified: 2026-11-24. This page is the whole project in two pages. Each section points to the playbook file that holds the rules, and each playbook file points to the full research.

## The honest verdict

- Day trading loses money for most people who try it. Under 1% of Taiwan day traders were predictably profitable after fees ([Barber et al. 2014](https://ideas.repec.org//a/eee/finmar/v18y2014icp1-24.html)) and 97% of Brazilian day traders who persisted 300+ days lost money ([Chague et al.](https://ideas.repec.org/p/fgv/eesptd/525.html)). MEASURED.
- Giving a language model the trading decision has not fixed that. In the most careful 2026 test, 0 of 91 agent runs showed significant alpha and simple trend following beat every model ([Wang 2026](https://arxiv.org/html/2611.19530)). In the Alpha Arena real-money contest, 31 of 38 model accounts lost ([Alpha Arena audit](https://tradingagentstack.com/alpha-arena-results/), a secondary recomputation). MEASURED, short windows.
- The popular "day trading works" papers are their authors' own backtests and weaken sharply in independent checks. STATED.
- What has the best evidence is slower and plainer: multi-day trend following with volatility-based sizing on liquid ETFs and on BTC/ETH spot, held overnight, with low turnover. A realistic target is a modest edge over buy-and-hold, not doubling an account. Details: `01_stocks_what_works.md`, `02_crypto_what_works.md`.
- The tiered-agent idea is sound as a cost design, and models are useful as readers, coders and reviewers. Details: `03_role_of_ai.md`.

Default assumption for everyone working here: the system loses money until our own logged forward results say otherwise.

## What we are building

A small always-on Python service that we host. It streams market data, runs rules-based scanners, enforces risk limits and places orders. It works with every model switched off. Beside it sits an agent harness: cheap models read and tag news, filings and transcripts; a top model is called only when the escalation gate fires; both return evidence tags, watchlist candidates and pause or veto flags, never orders. Fixed rules decide what to do with those, and the risk engine can reject anything. Neither model tier holds broker keys. Details and diagram: `06_architecture_and_build.md`.

So the answer to "harness or application" is both, in one repository: the application is the product, the harness is a library plus an evaluation suite inside it, and Perplexity is the research desk and build crew around it.

## Where Perplexity fits

| Job | Piece | Notes |
|---|---|---|
| Watch public sources for catalysts | Monitor API or Search API | One-minute minimum interval, $0.001 per run ([pricing](https://docs.perplexity.ai/docs/getting-started/pricing)). Not a price feed |
| Triage and tag evidence | Decisions API or a cheap Agent API model | $0.01 per million input tokens for Decisions Flash; Haiku 5.5 or GPT-6 Luna at $0.10/$0.50 ([models](https://docs.perplexity.ai/docs/agent-api/models)) |
| Deep review on escalation | Agent API with a top model | Fable 5.2 is $8/$40 per million tokens and needs access by request on the Agent API; Opus 5.5 at $4/$20 is the fallback |
| Morning brief, weekly strategy review, trade journal review | Computer automation, later a Teammate | 15-minute public minimum, can run late; credit use is not predictable in advance |
| Writing and maintaining the code, running backtests, keeping these docs current | Computer with sub-agents on mixed models | This repository is the shared memory |
| Placing orders | None of the above | Our own service only |

Details: `05_perplexity_and_costs.md`.

## Cost picture

Illustrative list-price arithmetic, not a forecast: scanning every 15 minutes with a cheap model plus 60 top-model deep dives a month comes to about $14.80, against about $88.74 if the top model handled every scan. At one-minute scanning the gap is about $68 against about $1,177. Letting plain code do the scanning and calling models only on triggers brings the model bill to about $11. Hosting adds about $6 a month. Computer usage for briefs and build work is on top and has to be observed, not estimated.

A Claude subscription is not a clean alternative: Anthropic's consumer terms bar automated access outside its API and bar relying on the service to buy or sell securities ([consumer terms](https://www.anthropic.com/legal/consumer-terms)). MEASURED policy text.

## Provider policies shape the design

- Anthropic's usage policy, effective November 12, 2026, treats a personalized recommendation to buy, sell, hold or allocate among specific investments, digital assets included, as high risk and requires a qualified person to review it before it is acted on ([Anthropic usage policy](https://www.anthropic.com/legal/aup)). MEASURED policy text.
- Perplexity's acceptable use policy dated January 1, 2027 bars consequential automated decisions about individuals' finances without human oversight ([Perplexity AUP](https://www.perplexity.ai/hub/legal/aup)). MEASURED policy text; how it applies to trading your own account is UNKNOWN.
- This is a second reason, on top of the performance evidence, that models here produce research and tags while fixed rules make the trade decision, and that going live needs your written approval.

## Build phases and gates

| Phase | Work | Gate to pass |
|---|---|---|
| 0 | Write one strategy spec per candidate, with costs and kill criteria, before any code | Owner approves specs and risk limits |
| 1 | Data, backtests with realistic costs, trial ledger | Deflated Sharpe significant, overfitting probability under 0.25, break-even cost at least 2x modeled cost |
| 2 | Paper trading, models off | At least 60 trading days and 100 closed paper trades; slippage and errors within tolerance |
| 3 | Add the model tiers in shadow mode: their tags and flags are logged, nothing consumes them | Rules that use the model outputs beat the rules-only baseline after token cost, on forward data only |
| 4 | Tiny live capital, ring-fenced account, hard daily loss cut-off. Starts only on the owner's written go | Live results track paper within tolerance for 3 months |
| 5 | Scale slowly | Only on 6 to 12 months of live evidence |

The three reports suggested different paper-trading lengths (4 to 8 weeks, 60 to 90 trading days, 6 to 12 months). The table reconciles them: the shorter figure gates tiny live capital, the longer one gates scaling. Recorded in `docs/decisions/0001-starting-decisions.md`.

## Rules that protect you

- The $25,000 pattern day trader minimum was replaced by intraday margin standards effective June 4, 2026, with broker phase-in until October 20, 2027 ([FINRA Notice 26-10](https://www.finra.org/rules-guidance/notices/26-10)). MEASURED. It removes a barrier, not the base rate.
- You are responsible for every order a bot places on your account. Running a bot on your own money is allowed; trading for others is a registration question.
- Short-term gains are taxed as ordinary income, and a high-frequency bot produces a heavy record-keeping load. Crypto is not SIPC-protected.
- Bot keys are trade-only, withdrawals off, in a ring-fenced account.

Details: `04_brokers_data_rules.md`.

## Risk posture and historical testing

The owner wants a middle risk level: rule-based core strategies plus a small capped sleeve for moonshots that each carry a written thesis. Historical data is used for all rule-based testing, and for model comparisons only on dates after each model's training cutoff. Details: `docs/decisions/0002-historical-testing-and-risk-posture.md`.

## What the owner still has to decide

Capital and loss limits, brokers, spot-only crypto or not, hosting, Perplexity plan and API budget, and model policy. Listed in `docs/decisions/0001-starting-decisions.md`.
