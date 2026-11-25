# The first roster of AI traders for the practice desk

Status: builder settings, written 2026-11-25. Every trader below is untested. These are methods to test with pretend money, not claims that they can make money.

Labels: MEASURED means read on a primary page or measured by our own logged test. STATED means someone's claim that was not confirmed. UNKNOWN means not found. A figure on this page or on a card is copied from the file or link named next to it.

## How the desk works

On 2026-11-25 the owner decided that AI traders make the trading decisions with pretend money (`docs/DECISIONS.md`). An AI trader writes a pick and never talks to the broker. Plain code places the order, applies limits and exits, and keeps the records (`AGENTS.md`, "How a trader behaves", item 1).

The desk trades only cash-account assets it can buy. It does not place short sales (`AGENTS.md`, "How a trader behaves", item 6). Every card that uses news requires independent confirmation or a primary filing (item 4).

The builder sets the pretend-money settings before the test. Each trader below, with its card, model and settings, is one trial and gets a ledger row before it runs. A changed card, model or setting is a new trial. Dropped traders stay counted (`AGENTS.md`, "Honest testing", items 1 and 2). Real money starts when the owner funds an account (`AGENTS.md`, "What comes from the owner").

## Why the model family matters little

- MEASURED: on TradeRank, a model's rank in one season told almost nothing about its rank in the next (pooled rank correlation +0.03), per `docs/research/18_ai_systems_with_live_records.md` and [TradeRank nine-season study](https://www.traderank.ai/blog/nine-seasons-llm-paper-trading).
- MEASURED: Agent Market Arena found "agent architecture proved to be the dominant factor shaping behavior" ([AMA paper](https://arxiv.org/html/2510.11695), via document 18).
- MEASURED: in our pilot every model run behaved like a plain trend rule (`docs/research/14_ai_calls_pilot_02.md`).
- So the method card is the thing being tested. Most traders use one model family, so differences come from the method and not the model. Two use a second family as a small check. The builder records the exact model build in the ledger before a test runs.

## The traders

| ID | Short name | Market | Holding time | One-line method | Evidence it rests on | Model family |
|---|---|---|---|---|---|---|
| A01 | earnings_reader | US stocks | 1 to 10 trading days | Buy after an earnings report where the company raised its guidance and the stock confirms it with heavy volume, read from the release and the call | `docs/research/01_stock_daytrading_evidence.md` (PEAD decay, MEASURED), `docs/research/19_information_feeds.md` (LLM headline scoring, MEASURED). Thin | Claude. Long text reading is the whole job |
| A02 | stocks_in_play | US stocks | Same day to 3 days | Buy liquid stocks with unusual volume and a confirmed, specific news reason, after the first 15 minutes, with a tight stop | `docs/research/01_stock_daytrading_evidence.md` (stocks in play, STATED), `docs/research/17_verified_traders_and_their_methods.md` (high volume study, MEASURED; attention losses, MEASURED against). Thin | Claude |
| A03 | trend_leaders | US ETFs and large stocks | 2 to 12 weeks | Hold the strongest sector funds when the market is above its 10-month average; the model only skips names with event risk | `docs/research/22_replay_05_stock_trend.md` (I2, not credited), `docs/research/21_systematic_funds_and_published_rules.md` (live trend funds, MEASURED) | GPT. The second family, on a method close to a fixed rule, so model noise shows |
| A04 | calm_dip_buyer | US large stocks and ETFs | 1 to 5 trading days | Buy a sharp drop in a large stock only when the model finds no company news that explains it | `docs/research/01_stock_daytrading_evidence.md` (reversal, mixed, MEASURED), `docs/research/19_information_feeds.md` (large-stock bad news reversed, MEASURED). Thin | Claude |
| A05 | leader_breakout | US stocks | 3 days to 8 weeks | A cash-only copy of what contest winners say they do: strong stocks near highs, tight stops, less exposure in weak markets | `docs/research/17_verified_traders_and_their_methods.md` (returns MEASURED, method STATED; IBD 50 fund MEASURED against) | Claude |
| A06 | insider_filings | US stocks above $5 | 1 to 6 weeks | Buy at the first wake after a fresh, non-routine insider purchase or activist filing | `docs/research/26_insider_buying_evidence.md`, `docs/research/13_high_risk_sleeve_evidence.md` (STATED and MEASURED, weak since 2008) | Claude |
| A07 | crypto_trend | Bitcoin and ether | Days to weeks | Follow the P1 trend weight on BTC and ETH, with the model allowed only to hold less on clear bad news | `docs/research/16_rig_audit.md` (P1, not credited), `docs/research/13_high_risk_sleeve_evidence.md` (crypto trend, MEASURED, in-sample) | GPT. A second check on the other family |
| A08 | crypto_news | Liquid crypto pairs on Alpaca | Hours to 5 days | Trade only after large, confirmed, crypto-specific news (regulation, ETF decisions, exchange failures), and only when the expected move is many times the fee | `docs/research/02_crypto_trading_evidence.md` (BIS regulatory news, MEASURED), `docs/research/16_rig_audit.md` (no hourly rule passed, MEASURED against) | Claude |
| A09 | moonshot | Stocks and crypto | Days to months | Small positions only, each with a written reason from the short list of ideas that have one, a stop and an end date | `docs/research/13_high_risk_sleeve_evidence.md` (ranked list), `archive/decisions/0002-historical-testing-and-risk-posture.md` | Claude |

One card per trader: `practice/traders/A01_earnings_reader.md` and so on.

What research could not support:

- No trader on this list has evidence that it makes money after costs for a small account. The strongest evidence is for A03 and A07, and it says they grow less than holding with smaller drops (`docs/STATUS.md`).
- No crypto day trading rule passed (`docs/STATUS.md`). A08 is a news method, not a chart method, and its evidence is thin.
- A "copy a documented trader" method only partly fits: the contest winners used margin and some shorting (`docs/research/17_verified_traders_and_their_methods.md`). A05 is a cash-only version, which is not what they did.
- Public AI trading contests support no method. MEASURED or STATED: 31 of 38 Alpha Arena accounts lost ([TradingAgentStack](https://tradingagentstack.com/alpha-arena-results/)). No Season 2 results were published as of 20 November 2026 ([ai-crypto.exchange](https://ai-crypto.exchange/ai-crypto-trading-agents/alpha-arena-results/)). On TradeRank's all-time table on 2026-11-24, one of 22 models was ahead of holding SPY ([TradeRank](https://www.traderank.ai/)). STATED, organiser's own table.

## Controls

Controls exist to measure the market and luck. They use no model. Each has the same pretend budget as an AI trader, unless noted.

| ID | Control | What it measures |
|---|---|---|
| C01 | Hold a total market fund. Buy on day one, never sell | What the stock market gave. Every stock trader is compared with it |
| C02 | Hold bitcoin. Buy on day one, never sell | What crypto gave. Every crypto trader is compared with it |
| C03 | Rule P1 on bitcoin, as already built in `practice/rules.py` | A fixed slow rule. The comparator for A07 |
| C04 | Rule T1 on a total market fund, as already built in `practice/rules.py` | A fixed slow rule. The comparator for A03 |
| R01 to R09 | One random twin per AI trader | Luck. Each twin copies its trader's trade count, trade sizes, holding times and market, but picks the symbol at random from the same allowed list and the entry time at random within the same wake. It is plain code. If one twin per trader is too many, the fallback is one twin per market (stocks, crypto) that copies the totals |

C03 and C04 use the fixed-rule runs on the practice desk (`practice/PLAN_02_ai_desk.md`), not new copies.

## How we judge

These are builder settings for pretend-money tests. The builder freezes them before a test runs and never changes them based on that test's results.

The problem with many traders: if nine traders run on luck alone, one of them will look good by chance. Document 11 works out that a small real edge needs hundreds of independent days to show (`docs/research/11_ai_trader_experiment_design.md`). So early on we can only drop traders. We cannot yet keep one because it looks good.

What every trader is measured on, the same way:

- Its daily return after all costs, minus its comparator's daily return on the same dates (C01 for stock traders, C02 for crypto traders, C03 for A07, C04 for A03).
- The same figure for its random twin.
- Its largest drop from a high, next to the comparator's.

Rules for dropping:

1. Dropped at once, with no review: it does something its card says it never does; it acts on one unconfirmed headline; or more than 5% of its wakes give broken or empty output over a week. These are faults, not bad luck.
2. Dropped at once: it loses 25% of its own pretend budget. This is a safety line, not a judgment of skill.
3. Checked every 20 trading days: dropped if it is behind its comparator and also behind its own random twin, and the one-sided 90% confidence range for its daily gap to the comparator lies wholly below zero. Being behind is not by itself a reason, because chance does that often.
4. Dropped at the end of its trial if it has not shown anything: a trial lasts until it reaches the practice minimums in `paper_min_trading_days` and `paper_min_closed_trades` (both builder settings in `config/thresholds.yaml`). A trader that is not clearly ahead at that point is dropped, not run longer in the hope that it improves.

Rules for keeping:

5. A trader is called "promising" only if, at the end of its trial, the lower end of its confidence range for the gap to its comparator is above zero after correcting for every trader ever started on the desk, dropped ones included (a Bonferroni correction: the 90% level becomes stricter the more traders have been tried). It must also beat its random twin by the same test.
6. "Promising" means it gets a varied copy, logged as a new trial. It does not mean real money. Real money starts when the owner funds an account (`AGENTS.md`, "What comes from the owner").
7. Results are never cut short or extended because they look good or bad. A changed card, model or setting starts a new trial and a new count.

What research expects, said plainly: most traders will be dropped or end inconclusive. That is the honest base rate in `docs/research/25_what_the_evidence_supports.md`.
