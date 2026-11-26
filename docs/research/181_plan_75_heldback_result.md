# Plan 75, the held-back run: a coin trend rule with a stop that only moves up

- Status: RECORD. Built by `research_rig/build_doc181_plan75_vault.py` from four aggregate files held outside the repo, each pinned by SHA-256; no price or fill row is in the repo.
- Plan and every rule change: [the plan](../../research_rig/PREREG_75_coin_trend_ratchet.md). Ledger row 225. Earlier stage on years the paper had seen: [doc 173](173_plan_75_repeat_result.md). Access dates: [doc 172](172_us_spot_access_dates_20_coins.md). Source of the idea: [doc 171](171_idea_round_50_swing_horizon.md).
- This is the judged test. The sealed stretch 2024-01-01 to 2026-10-31 was opened once, by the data custodian, from a clean checkout at commit `8a1397d`, after an independent audit of the code and a written go on the ledger. It cannot be run again.

## Short answer

- MEASURED: all four marks fixed before the run are met. Result line: `PASS`.
- MEASURED: after 75 bp a side the rule returned +9.0% over 34 months, about +3.1% a year.
- MEASURED: all of the gain came in 2024 (+18.8%). 2025 was -4.6% and 2026 to the end of October -3.8%.
- MEASURED: at the harsher cost line of 145 bp a side, shown only, the rule lost: -3.9%.
- Reading: a pass by the rules we set, and a thin one. It is not fast money. By the plan, a pass earns a forward practice card with pretend money and nothing else.

## The four marks

| Mark, fixed before any held-back price | Measured | Met |
|---|---|---|
| Net return above zero after 75 bp a side | +9.04% | true |
| Above Bitcoin held at matched volatility, after its costs | +9.04% against +6.40% (scale 0.228; Bitcoin unscaled +7.22%) | true |
| Largest fall from a high under 40% | 19.27% | true |
| From the 2025-03-19 close, after the paper's sample, at least -10% | -4.35% | true |

## The run in numbers

- MEASURED, main line: 2283 fills, 1351 holding spells, median hold 8 days, 90th percentile 22 days, longest 66 days, 2 over 60 days. Costs paid on fills came to 14.5% of starting capital. Daily Sharpe, yearly rate: 0.36.
- MEASURED, harsh line, shown only: net -3.9%; years +14.6%, -8.2%, -8.6%; largest fall 23.8%; after the paper's sample -12.1%; costs on fills 26.4% of starting capital; Bitcoin at matched volatility +6.1%.
- MEASURED, shown only, each leg alone at 75 bp a side: 10-day +3.8% (largest fall 23.5%, 1583 fills), 20-day +11.4% (largest fall 18.6%, 867 fills), 30-day +11.7% (largest fall 17.3%, 646 fills). At 145 bp: 10-day -15.5%, 20-day +0.6%, 30-day +3.9%. The slower legs trade less and lost less to costs. This is a look after the fact and counts for nothing; a slower-leg rule would be a new plan on new data.
- MEASURED, shown only, the paper's nine-leg rule as printed: +4.3% at 75 bp a side (largest fall 16.8%, 4785 fills, longest hold 179 days); -5.3% at 145 bp.
- MEASURED: the three-leg blend with the paper's 200% cap in place of our 100% gave the same book to the last digit, so the cap never bound.
- MEASURED from the access ledger: of 20700 coin-days, 2068 were admitted on a dated full-trading notice, 15553 on a dated report of the dollar order book opening plus seven days, and 3079 were not admitted. That is 85.1% admitted, 88.3% of it on the weaker level.

## Independent recompute

- A helper who had not read the scorer, its tests, its audits or its output wrote a second implementation from the plan text alone, ran it on the same sealed inputs, and reported before being told any official number.
- MEASURED, 75 bp a side, official then recompute: net +9.04% and +10.11%; largest fall 19.27% and 19.29%; fills 2283 and 2262; 2024 +18.78% and +19.97%; 2025 -4.62% and -4.62%; 2026 -3.75% and -3.77%; after the paper's sample -4.35% and -4.36%; Bitcoin at matched volatility +6.40% and +6.39%.
- MEASURED: the recompute also has all four marks true and the same result line. At 145 bp a side: -3.90% and -2.81%.
- MEASURED: the two differ by 1.08 percentage points on the net return and by 21 fills, almost all of it in 2024. That is larger than in the 2020 to 2023 stage, so the helper was then given the scorer and traced it.
- MEASURED cause: the first difference is the first day either book could invest, 2024-04-01. The plan says a leg waits for 90 valid daily returns before it carries risk. The official scorer keeps each leg's signal and stop running during that wait and only delays the money; the recompute did not let a signal begin until the wait was over. On 2024-04-01 the official book therefore bought eight coins whose signals had begun earlier, and the recompute waited for fresh signals.
- MEASURED: with that one choice switched in the recompute, its net moves from +10.11% to +8.94%; also carrying signal state through days a coin was not admitted gives +9.00%, against the official +9.04%. What is left is a difference in how a target weight is turned into a coin amount at the open. No reading changes any mark.
- Lead agent's ruling: the plan text allows both readings, so this is an ambiguity in the plan and not an error in either implementation. The official figure stands because that code was frozen and audited before the run. The honest range for the result is +9.0% to +10.1%.

## How much a pass like this proves

- MEASURED by the independent auditor on made-up price worlds with no edge, same code and same four marks: 13 of 400 worlds passed (3.25%); with a 15% yearly upward drift in coin prices, 21 of 400 (5.25%). With half of the paper's stated edge planted, 366 of 400 passed (91.50%). The edge model in those worlds is the auditor's assumption.
- INFERENCE: the four marks are hard to pass by luck in those worlds, and they do not ask how big the edge is. A pass says the rule was not harmful and beat a like-risk Bitcoin hold in this stretch. It does not say the rule earns enough to matter.
- MEASURED: one of three calendar years was positive. Two of the older diagnostics borrowed from Replay 22, a Sharpe of 1.0 and most years positive, were not met here; that set was replaced by the four marks before any price, for the reason written in the plan.

## What this does and does not show

- It shows that a published trend rule, cut down to its three fastest legs before any test and not tuned after, on holds of days to weeks, did not lose money after realistic costs on years its authors had not seen, and stayed ahead of Bitcoin at the same risk.
- It does not show a way to make money quickly. The whole gain is one year, the two years since are both losses, and a harsher cost line turns the result negative.
- Costs decide it. The rule paid about a seventh of its capital in costs. What a small US account really pays per trade is now the first thing to measure.
- STATED limits carried from the plan: the 20 coins were picked with hindsight, which flatters a long-only rule by an unknown amount; Binance USDT bars stand in for a US venue; most admitted coin-days rest on the weaker access level; the paper's liquidity filter is not carried over; an earlier daily break rule of ours failed on overlapping dates.
- Next: practice card E10, a forward log of this rule on live US venue quotes with pretend money. It records the real spread at each order and whether orders are even placeable at $500. No real money follows from this result.
