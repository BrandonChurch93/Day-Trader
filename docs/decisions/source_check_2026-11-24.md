# Source check, 2026-11-24

Three agents that did not write the research checked the figures in playbooks 01, 02 and 03 against their primary sources. Each used a different model. None could edit the repo. This is hand-over 11 in `docs/quality/04_research_to_build.md`. The full reports are the three `source_check_2026-11-24_*.md` files beside this one. They describe the playbooks as they stood at commit 65c881e, before the corrections below.

## Result

| Playbook | Claims checked | Verified | Overstated | Wrong | Not in source | Unreachable |
|---|---|---|---|---|---|---|
| 01 stocks | 19 | 12 | 4 | 0 | 3 | 0 |
| 02 crypto | 13 | 13 | 0 | 0 | 0 | 0 |
| 03 role of AI | 16 | 5 | 6 | 4 | 1 | 0 |

The lead read the two papers behind the worst findings (the crypto benchmark and the Wang replay) and confirmed the checker was right on both.

## What was wrong and what changed

| # | Playbook | Was | Now | Severity |
|---|---|---|---|---|
| 1 | 03 | A row said classical ML made +62.94% and +41.93% in live and paper crypto trading while every LLM agent lost | Those were 2025 backtest figures. In paper trading the order nearly reversed. With real money over four weeks one LLM method made +3.72%, the ML methods lost, and nothing beat buy and hold at +11.63%. The row is now three rows, one per stage | Severe |
| 2 | 03 | "Most news price discovery occurs within the first hour" | The first hour held under half of the move. What the study shows is that buying at the next open kept a gain that was not statistically significant | Major |
| 3 | 03 | "Factor exposures explain 78% of median-run returns" | 78% of the absolute size of the return's parts. Median R-squared 0.66. Some runs cover dates the models may remember | Major |
| 4 | 03 | "~90% hit rate" for GPT-4 on headlines | 90% of portfolio-days, not of headlines. Drift is strongest in smaller stocks and after bad news, not limited to small caps | Major |
| 5 | 03 | "12.5% on 120B vs 100% on 7B-8B models" | Three named setups. The study does not separate model size from provider | Major |
| 6 | 03 | Cascade saving "72% vs 31%-44% single-turn" | The 31% and 44% are older routers run on the same multi-step tasks. Authors' benchmark, not trading. Retagged STATED | Major |
| 7 | 03 | "0.68-year test gives 19% power" | The source computes 19% at 145 trading days. Our day and trade counts are marked as house rules | Minor |
| 8 | 03 | Sonar "ended" | Support ended. Synchronous requests still run | Minor |
| 9 | 03 | Memorization row dated 2025-04 | The figure is from the August 2026 revision | Minor |
| 10 | 03 | Drain "$150k-$200k" | $150k to $174k by the report's estimate. 80% returned, per the operator | Minor |
| 11 | 03 | Alpaca allowlist rule tagged MEASURED | The tools existing is MEASURED. The rule is our recommendation | Minor |
| 12 | 01 | Paper gate cited to research 01 | Research 01 proposed 6 to 12 months of paper trading. Decision 0001 row 9 shortened it. The playbook now says so and says the owner has not confirmed it | Major |
| 13 | 01 | Intraday trend cost bar of 2 bps round trip | The cited reproduction puts break-even below about 1 bp. `intraday_trend_max_round_trip_bps` tightened to 1 | Major (part of 12) |
| 14 | 01 | Cost model, Kelly share and drawdown band cited to research sections | Marked as house numbers. The Kelly share and drawdown band moved to config | Minor |
| 15 | 01 | Trial budget and stop-loss rules tagged MEASURED | They rest on method papers and an analytical model. Retagged STATED | Minor |
| 16 | 01 | Brazil 97% row | It is index futures, after estimated broker fees. Said so | Minor |
| 17 | 01 | Turnover "under 50%" | One-sided turnover, with cost-aware construction | Minor |
| 18 | 02 | BTC intraday break-even 10 bps beside round-trip fee rows | The paper does not say one-way or round trip, and its authors call the strategy unprofitable at a 25 bps fee. Said so | Context only |

## What this does to the recommendations

- The case for keeping models out of the order path loses one piece of evidence. "Simple ML beat LLM agents in live crypto" was false. What the paper shows is that backtest rankings did not survive and nothing beat buy and hold.
- The rest of that case stands as checked: 0 of 91 runs with significant alpha, the trend rule ahead of every model in the 2026 rally, the 51% to 62% decay past the training cutoff, the 20-year study with no significant alpha, and 31 of 38 real-money accounts losing.
- One point now cuts the other way and is stated for the owner: in the 2022 bear market the trend rule lost 5.9% and four of six models did better than it. Trend following is not ahead in every market.
- The paper gate length is a house rule, shorter than the stock research first proposed. It goes to the owner as an open number, not as a finding.

## How the errors got in

Rows 1 and 2 were added during the first cross-audit (`audit_03_role_of_ai.md`, fixes 6 and 7), by an agent reading the research report and not the papers. The research report had the same error. A check against the report could not catch it. Only a check against the primary source did. That is why hand-over 11 now requires the primary source.

## Not yet checked

Playbooks 04, 05 and 06, and the research reports beyond the lines corrected here. Broker fees and platform facts are being re-read from the firms' own pages in the broker research that started the same day.
