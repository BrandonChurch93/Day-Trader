# Where each model's memory of crypto prices stops

Made by `timemachine/knowledge_line.py` from `timemachine/knowledge_lines.json`. Do not edit by hand. No money and no trading.

## Why this was measured

- The time machine replays July to November 2026. A model that remembers those months would look skilled and would not be.
- Each model was asked once, from memory and with no lookups, for the month-end price of bitcoin, ether and solana from 2025-01 to 2026-11, with null where it does not know.
- A month is a hit when at least two of the three coins are within 10% of the tape's month-end price (`tm_knowledge_hit_within`).
- "Carried forward" is how many later months would be hits if the model just repeated its answer for its stated latest month. Hits no more than that are what a guess gives.

## Result

| Model | Latest month it says it knows | Last month it got right | Replay months it answered | Replay months it got right | Later hits by carrying its last answer forward |
|---|---|---|---|---|---|
| Claude Opus 5.5 | not asked yet | | | | |
| GPT-6.2 Sol | not asked yet | | | | |
| Gemini Neon | not asked yet | | | | |
| Claude Sonnet 5.5 | not asked yet | | | | |
| Kimi K3 | not asked yet | | | | |
| Grok 4.7 | not asked yet | | | | |

## Month by month

Each cell: coins answered, then coins within the band. A dash means it answered null for all three.

| Month | Claude Opus 5.5 | GPT-6.2 Sol | Gemini Neon | Claude Sonnet 5.5 | Kimi K3 | Grok 4.7 |
|---|---|---|---|---|---|---|
| 2025-01 |  |  |  |  |  |  |
| 2025-02 |  |  |  |  |  |  |
| 2025-03 |  |  |  |  |  |  |
| 2025-04 |  |  |  |  |  |  |
| 2025-05 |  |  |  |  |  |  |
| 2025-06 |  |  |  |  |  |  |
| 2025-07 |  |  |  |  |  |  |
| 2025-08 |  |  |  |  |  |  |
| 2025-09 |  |  |  |  |  |  |
| 2025-10 |  |  |  |  |  |  |
| 2025-11 |  |  |  |  |  |  |
| 2025-12 |  |  |  |  |  |  |
| 2026-01 |  |  |  |  |  |  |
| 2026-02 |  |  |  |  |  |  |
| 2026-03 |  |  |  |  |  |  |
| 2026-04 |  |  |  |  |  |  |
| 2026-05 |  |  |  |  |  |  |
| 2026-06 |  |  |  |  |  |  |
| 2026-07 (replay) |  |  |  |  |  |  |
| 2026-08 (replay) |  |  |  |  |  |  |
| 2026-09 (replay) |  |  |  |  |  |  |
| 2026-10 (replay) |  |  |  |  |  |  |
| 2026-11 (replay) |  |  |  |  |  |  |

## What each model said about its own memory


## What this does not show

- One question, asked once. A model can know events without knowing prices, or the other way round.
- The no-lookup rule was given by instruction. The agent that answered had tools it was told not to use.
- The agent could see today's date. It could not see prices unless it broke the rule.
- A hit by luck is possible when prices move little. The carried-forward column is there to show how much luck gives.
