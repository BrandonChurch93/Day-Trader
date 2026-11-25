# Backtester fixtures: draft list

Last updated: 2026-11-24. Draft, proposed by research. It answers item 7 of `archive/quality/05_repo_review_2026-11-24.md` and hand-over 6 in `archive/quality/04_research_to_build.md`.

A gate must not be passable while the product is wrong. The engine proves itself on these before any strategy result counts. A regression test against a locked baseline stays as a second check, because it catches drift but not an engine that was wrong from the start.

No expected value is typed in this file. Each one is worked out by hand at kit time by two agents working separately, checked against each other, and stored in `kit/data/`.

| # | Fixture | What the engine must do |
|---|---|---|
| 1 | Hand-worked profit | A short price series, one buy and one sell at a fixed size. Reproduce the gross profit exactly |
| 2 | Hand-worked costs | The same trade with commission, spread and slippage. Reproduce the net profit exactly. The fee model matches a dated, published fee table |
| 3 | Buy and hold | Buy on the first bar and hold. The result equals the asset's return less one side of costs, exactly |
| 4 | Peeking at the future | A rule that uses a bar's close to trade at that same bar's open. The engine must refuse it or flag it. Shifting any signal by one bar must change the result |
| 5 | Random strategy | Random entries over many seeds on real history. The average result must be a loss about the size of the costs. An engine that shows an edge here is wrong |
| 6 | Stock split | A split in the middle of a held position. The split creates no profit and no loss |
| 7 | Dividend | A dividend on a held position is counted once, on the right date |
| 8 | Fill rule and gaps | An order decided on one bar fills on the next. A stop that the price gaps through fills at the gap price, not at the stop price |
| 9 | Position sizing | Volatility sizing on a short series with the volatility worked out by hand. Reproduce the share count exactly, including rounding. Cash never goes below zero |
| 10 | Risk engine | Each limit trips on its own fixture: daily loss, total loss, position size, order size, order rate, symbol allowlist, stale quote, market hours. After a trip no order passes. Every branch is covered |
| 11 | Clock and calendar | Bars around a daylight-saving change land in the right session. Holidays and half days are respected for stocks. Crypto runs every day |
| 12 | Point-in-time universe | A symbol that was later delisted is in the universe on dates before the delisting |
| 13 | Held-back slice lock | A second run of the same strategy version on the held-back slice is refused and logged |
| 14 | Trial ledger | A result with no trial ledger entry cannot be reported and cannot pass a gate |
| 15 | Determinism | The same inputs and seed, run twice, give identical result files. Each result file carries the command and the commit that made it |
| 16 | Duplicate order | Submitting the same order id twice creates one order. An unclear submission halts the strategy and alerts. It is not retried |
| 17 | Paper and live | Starting with a live setting and no decision record is refused |

Fixtures 5 and 6 were added by research. The rest restate `archive/quality/01_the_bar.md` under "Numbers and results" and the hard rules in `AGENTS.md`.
