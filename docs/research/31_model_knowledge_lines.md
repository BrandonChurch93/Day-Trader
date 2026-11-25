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
| Claude Opus 5.5 | 2026-01 | 2025-12 | 0 of 5 | 0 of 5 | 0 |
| GPT-6.2 Sol | 2025-12 | none | 0 of 5 | 0 of 5 | 0 |
| Gemini Neon | 2026-03 | 2026-02 | 0 of 5 | 0 of 5 | 0 |
| Claude Sonnet 5.5 | 2025-11 | 2025-11 | 0 of 5 | 0 of 5 | 1 |
| Kimi K3 | 2025-07 | 2025-06 | 0 of 5 | 0 of 5 | 0 |
| Grok 4.7 | 2025-01 | none | 0 of 5 | 0 of 5 | 0 |
| Claude Fable 5.2 | 2026-02 | 2025-12 | 0 of 5 | 0 of 5 | 0 |

## Month by month

Each cell: coins answered, then coins within the band. A dash means it answered null for all three.

| Month | Claude Opus 5.5 | GPT-6.2 Sol | Gemini Neon | Claude Sonnet 5.5 | Kimi K3 | Grok 4.7 | Claude Fable 5.2 |
|---|---|---|---|---|---|---|---|
| 2025-01 | 3 / 3 hit | 1 / 1 | 3 / 3 hit | 3 / 3 hit | 3 / 3 hit | - | 3 / 3 hit |
| 2025-02 | 3 / 3 hit | 1 / 1 | 3 / 3 hit | 3 / 3 hit | 3 / 3 hit | - | 3 / 3 hit |
| 2025-03 | 3 / 3 hit | 1 / 1 | 3 / 3 hit | 3 / 3 hit | 3 / 3 hit | - | 3 / 3 hit |
| 2025-04 | 3 / 3 hit | 1 / 1 | 3 / 3 hit | 3 / 3 hit | 3 / 3 hit | - | 3 / 3 hit |
| 2025-05 | 3 / 3 hit | 1 / 1 | 3 / 3 hit | 3 / 3 hit | 3 / 3 hit | - | 3 / 3 hit |
| 2025-06 | 3 / 3 hit | 1 / 1 | 3 / 3 hit | 3 / 3 hit | 3 / 3 hit | - | 3 / 3 hit |
| 2025-07 | 3 / 3 hit | 1 / 1 | 3 / 3 hit | 3 / 3 hit | 1 / 1 | - | 3 / 3 hit |
| 2025-08 | 3 / 3 hit | - | 3 / 3 hit | 3 / 3 hit | - | - | 3 / 3 hit |
| 2025-09 | 3 / 3 hit | - | 3 / 3 hit | 3 / 3 hit | - | - | 3 / 3 hit |
| 2025-10 | 3 / 3 hit | - | 3 / 3 hit | 3 / 3 hit | - | - | 3 / 3 hit |
| 2025-11 | 3 / 3 hit | - | 3 / 3 hit | 3 / 3 hit | - | - | 3 / 3 hit |
| 2025-12 | 3 / 3 hit | 1 / 1 | 3 / 3 hit | - | - | - | 3 / 3 hit |
| 2026-01 | - | - | 3 / 3 hit | - | - | - | 1 / 1 |
| 2026-02 | - | - | 3 / 3 hit | - | - | - | - |
| 2026-03 | - | - | - | - | - | - | - |
| 2026-04 | - | - | - | - | - | - | - |
| 2026-05 | - | - | - | - | - | - | - |
| 2026-06 | - | - | - | - | - | - | - |
| 2026-07 (replay) | - | - | - | - | - | - | - |
| 2026-08 (replay) | - | - | - | - | - | - | - |
| 2026-09 (replay) | - | - | - | - | - | - | - |
| 2026-10 (replay) | - | - | - | - | - | - | - |
| 2026-11 (replay) | - | - | - | - | - | - | - |

## What each model said about its own memory

- Claude Opus 5.5: Fairly confident in early-to-mid 2025 month-ends (within a few percent); Oct-Dec 2025 are approximate, and I only have vague impressions of a further sell-off in January 2026 with no reliable month-end figures from 2026 onward.
- GPT-6.2 Sol: The BTC values are rounded recollections rather than exact closes. I don't recall ETH or SOL month-end prices or any 2026 month-end prices with enough confidence to give a value.
- Gemini Neon: I recall approximate month-end closes from 2025-01 through 2026-02, with somewhat less precision on exact ETH and SOL month-end prints in late 2025 and early 2026. My memory ends during 2026-03, so 2026-03 month-end and all months from 2026-04 through 2026-11 are null.
- Claude Sonnet 5.5: Values for 2025-01 to 2025-06 are fairly solid to within a few percent; July to October 2025 are rougher recollections, and the 2025-11 figures are vague. I remember nothing reliable after November 2025, so everything later is null.
- Kimi K3: My memory is a rough approximation for early-to-mid 2025 (within a few thousand dollars on BTC, less certain on ETH and SOL), and it gets genuinely thin after about July 2025, so everything from 2025-08 onward is honestly unknown to me.
- Grok 4.7: I do not remember a month-end price for BTC, ETH, or SOL in any of these months, so every close is null. I only remember that bitcoin was around the $100,000 level after late 2024, and nothing reliable after early 2025.
- Claude Fable 5.2: 2025 values are recalled month-end closes, good to roughly 1-3 percent, with the last quarter of 2025 a bit looser. The 2026-01 BTC figure is a shaky recollection, I only vaguely remember a sharp BTC drop toward about 60k in early February 2026 with no month-end value, and I remember nothing after that.

## What this does not show

- One question, asked once. A model can know events without knowing prices, or the other way round.
- The no-lookup rule was given by instruction. The agent that answered had tools it was told not to use.
- The agent could see today's date. It could not see prices unless it broke the rule.
- A hit by luck is possible when prices move little. The carried-forward column is there to show how much luck gives.
