# Plan 75, the 2020 to 2023 run: a coin trend rule with a stop that only moves up

- Status: RECORD. Built by `research_rig/build_doc173_plan75_repeat.py` from three aggregate files held outside the repo, each pinned by SHA-256; no price or fill row is in the repo.
- Plan and every rule change: [the plan](../../research_rig/PREREG_75_coin_trend_ratchet.md). Ledger row 225. Access dates: [doc 172](172_us_spot_access_dates_20_coins.md). Source of the idea: [doc 171](171_idea_round_50_swing_horizon.md).
- This is the repeat stage on years the published paper had already seen. It is not the judged test. The judged test is the sealed 2024-01-01 to 2026-10-31 stretch, opened once, on a separate written go.
- The run was made once by the data custodian from a clean checkout at commit `8d131f6`. The scorer's own check line read: `IMPLEMENTATION_CHECK PASS`.

## Short answer

- MEASURED: at 75 bp a side the rule returned +68.9% over the four years. First half +54.0%, second half +9.6%.
- MEASURED: by year, 2020 +28.1%, 2021 +20.2%, 2022 -9.8%, 2023 +21.5%. Largest fall from a high 13.2%.
- MEASURED: the same coins bought and held on the same calendar, with the same costs, returned +743.9%. The rule made far less than holding.
- MEASURED: 500 random copies that kept each holding spell's length and size but moved it to a random day in the same month set a 95th-percentile mark of +143.1%. The rule is below it. This run does not show that the rule's timing adds anything beyond being in coins while coins rose.
- By the line fixed before the run (net above zero after 75 bp a side overall and in at least one half): met. The plan goes on to its freeze, audit and the one held-back run.

## The run in numbers

- MEASURED, main line, 75 bp a side: 2388 fills, 1352 holding spells, median hold 9 days, 90th percentile 29.9 days, longest 103 days, 13 spells over 60 days. Costs paid came to 23.9% of starting capital. Daily Sharpe figure as the scorer prints it: 1.16. Years positive: 3 of 4.
- MEASURED, harsh line, 145 bp a side: net +43.9%; halves +44.3% and -0.3%; years +23.6%, +16.7%, -12.8%, +14.3%; largest fall 19.3%; costs 42.6% of starting capital; same-list hold +688.2%; random-copy mark +110.1%.
- MEASURED, shown only, 75 bp a side, each leg alone: 10-day +63.5% (largest fall 18.8%), 20-day +68.9% (13.6%), 30-day +72.4% (10.5%).
- MEASURED, shown only, the paper's nine-leg rule as printed: +44.1% at 75 bp a side, largest fall 14.3%, 4845 fills.
- MEASURED: random copies that could not be placed: 11590 of 676000 attempts (1.71%).
- MEASURED, the five older diagnostics, shown only at the main line: above the same-list hold false; above the random-copy mark false; largest fall within the old ceiling true; Sharpe at or above the old floor true; three of four years positive true. The five-of-seven-years line does not apply to four years.

## Independent recompute

- A helper who had not read the scorer, its tests, its audits or its output wrote a second implementation from the plan text alone and ran it on the same inputs.
- MEASURED, 75 bp a side, official then recompute: net +68.86% and +68.81%; first half +54.04% and +54.01%; second half +9.62% and +9.61%; largest fall 13.16% and 13.16%; fills 2388 and 2387; same-list hold +743.88% and +743.88%.
- MEASURED, 145 bp a side, official then recompute: net +43.88% and +43.92%; second half -0.28% and -0.24%; fills 2388 and 2386.
- MEASURED: the two differ by 0.05 percentage points on the four-year return and by 1 fill. Every sign and every year agrees. The recompute did not rebuild the random copies, so that comparison rests on the official run alone.

## Which coins were in

- MEASURED from the access ledger: of 29220 coin-days, 1112 were admitted on a dated full-trading notice, 16178 on a dated report of the dollar order book opening plus seven days, and 11930 were not admitted. That is 11.83 admitted coins a day on average; 17 of 20 coins were admitted at some point.
- STATED limit: the inferred level is weaker than a notice. It was added by a rule change before any price was read, because the venue's own notice pages do not open for us.

## What this does and does not show

- It shows the rule made money after costs in these four years with a small largest fall, on holds that fit the owner's horizon of days to weeks.
- It does not show an edge. The four years include a very large rise in coin prices, the rule lost to holding and to random timing, and the paper had already seen these years.
- STATED limits carried from the plan: the 20 coins were picked with hindsight; Binance USDT bars stand in for a US venue; the paper's liquidity filter is not carried over; an earlier daily break rule of ours failed on overlapping dates.
- Next: freeze the rule, audit the held-back entry point, then one run on the sealed stretch. Marks fixed before any price: net above zero; above Bitcoin held at matched volatility after costs; largest fall under 40%; the stretch after the paper's sample not worse than -10%. A pass earns a forward card on the practice desk, not real money.
