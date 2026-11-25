# Time machine plan 04: the model picks which stocks to hold

Written 2026-11-25 16:22 UTC by the builder, before the tool for it was finished and before any session of this plan was made. Pretend money.

## What is asked

Can a model that reads a week of prices, company filings and headlines choose a basket of stocks that does better than baskets drawn at random from the same list?

The account is always fully invested, so the test is of choosing, not of timing or of how much to hold. The one published test found so far in which a language-model system was ahead of holding worked this way: a basket chosen once a month and held ([MarketSenseAI live validation](https://arxiv.org/html/2604.17327v1)). STATED by its authors. Its figures are signals made at the time and scored on later prices before costs, with no money traded and no outside check.

## Trader

Card `practice/traders/D02_stock_basket.md`, brief `timemachine/TRADER_BRIEF_WEIGHTS.md`. One session per model covers the whole period. Each model runs twice with fresh agents, run 1 and run 2.

| Trial | Trader id | Model |
|---|---|---|
| TM04-a | D02-OPUS | Claude Opus 5.5 |
| TM04-b | D02-SOL | GPT-6.2 Sol |
| TM04-c | D02-NEON | Gemini Neon |
| TM04-d | D02-SONNET | Claude Sonnet 5.5 |
| TM04-e | D02-KIMI | Kimi K3 |
| TM04-f | D02-GROK | Grok 4.7 |

## Dates, costs, how a session runs

- The list: the single stocks in `tm04_plan.symbols` (38 companies, no funds). It was chosen on 2026-11-25 from today's large companies, so it leans toward companies that did well. Every yardstick below is drawn from the same list and carries the same lean.
- Period: `tm04_plan.start` to `tm04_plan.end`, after every model's knowledge line.
- One wake a week: the last regular trading day of the week at `tm04_plan.wake_time_ny` New York time. The model names exactly `tm04_plan.basket_size` stocks. The desk holds them in equal shares and trades only the difference from last week, at the open of the next minute.
- Costs per side: the spread `tm_stock_half_spread_bps` on what is traded. No fee, as on the practice account.
- The account starts in cash. The first basket is bought at the first wake.
- At each wake the model sees, for every stock on the list, its price and its change over a day, a week, a month and three months, and the filings and headlines dated since the last wake. It can look up more within the lookup limit. It writes one plain line of reason for each stock it adds or drops.

## Yardsticks

1. Equal shares of all the stocks on the list, bought at the first wake and held.
2. Random baskets: `tm_weights_twin_draws` runs in which, every week, the same number of stocks is swapped as the model swapped that week, drawn at random from the list, with the same costs.
3. SPY held from the first wake, shown for scale only.

## What would count, fixed now

For one run: its final gain is above yardstick 1 and above the `tm_weights_pass_percentile`th percentile of yardstick 2.

For the method, counted on run 1 of each model: at least `tm04_plan.method_min_models_above_median` of six runs end above the middle of their random baskets, and at least `tm04_plan.method_min_models_above_percentile` end above the `tm_weights_pass_percentile`th percentile. Fewer, and it is reported as not shown.

Run 2 is not part of the mark. It shows how much one model's answer changes from run to run: the share of names the two runs hold in common each week, and the gap between their gains.

## How this can fool us

- About 25 weekly choices over one stretch of one market. One strong sector can carry a basket. A pass here earns a longer test, it is not proof.
- Models tend to like the same well-known growth names. If those led over these months, all six look good together, and that is one bet, not six.
- The list was picked with hindsight. Random baskets share that, the comparison with SPY does not, so SPY is for scale only.
- Headlines on the tape come from one site and are tagged by company name, so some are missing and some are mis-tagged. Filings come from the SEC with their time to the second.
- Fills are assumed at five hundredths of a percent a side. Not measured.
- The no-web rule is by instruction.
