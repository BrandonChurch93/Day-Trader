# Time machine TM06-R: does the Claude Fable 5.2 picker repeat

MEASURED. TM06-R mixed: of the two repeat runs of the Claude Fable 5.2 picker on the same eight months, 1 cleared both marks (above holding all 20 coins and strictly above the 90th percentile of its random twins) and 1 did not; with run 1, 2 of 3 runs cleared. All three runs were negative without May. Same months, so this measures run-to-run luck only. Fee 12 bps per side.

STATED. The rule was set before runs 2 and 3 started, in `timemachine/TM06R_addendum.md` and ledger row TM06-R (`research_rig/TRIAL_LEDGER.md`): repeats if both new runs clear above `equal_all_held` and above the twins' pass percentile (`tm_weights_pass_percentile`), did not repeat if neither does, mixed if one does. Run 1 is arm g of plan TM06 (`timemachine/PLAN_TM06_hot_coin_swing.md`), read before the rule was written. Each run is 8 fresh one-month sessions with the same card, config, briefs, server and twin settings; runs 2 and 3 were told arm g's folders were off limits. Each run was scored on its own by `timemachine/score_tm06.py`, unchanged. STATED by the operator: run 1 ran the scorer as is; runs 2 and 3 ran it through an off-repo wrapper that scores sessions in parallel, whose output was byte-identical to the serial scorer on three checks, including the committed control run.

## Each run joined over eight months

MEASURED. Main fee `tm06_plan` main_fee_bps, 12 bps per side, plus each coin's half spread (3 to 31 bps, as stored with each session) and perpetual funding, as the scorer charges. Months are joined by chaining each month's gain.

| Run | Joined gain | Holding all 20 | Above holding all 20 | Top 7-day rise rule | Twin median | Twin percentile | Above 90th percentile | Clears both marks |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- |
| Run 1 (arm g) | +52.45% | -2.57% | yes | +3.27% | -9.15% | 98.8 | yes | yes |
| Run 2 (g2) | +11.35% | -2.57% | yes | +3.27% | -26.10% | 96.6 | yes | yes |
| Run 3 (g3) | +8.48% | -2.57% | yes | +3.27% | -12.73% | 84.0 | no | no |

MEASURED. Holding all 20 coins and the top 7-day rise rule are the same in every run, because the months and coins are the same.

## Month by month

MEASURED. Each month's gain at 12 bps per side.

| Month | Run 1 | Run 2 | Run 3 | Median of three | Holding all 20 | Top 7-day rise rule |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-04 | +4.35% | +20.90% | +13.66% | +13.66% | +4.21% | +7.72% |
| 2026-05 | +73.16% | +48.44% | +55.08% | +55.08% | +10.81% | +55.20% |
| 2026-06 | -21.81% | -12.96% | -18.38% | -18.38% | -20.64% | -28.63% |
| 2026-07 | -11.96% | -11.32% | -18.96% | -11.96% | +1.95% | -1.45% |
| 2026-08 | +33.81% | +26.65% | +22.64% | +26.65% | +25.47% | +35.52% |
| 2026-09 | +16.49% | +13.50% | +20.26% | +16.49% | +38.14% | +34.72% |
| 2026-10 | -10.02% | -21.18% | -22.06% | -21.18% | -16.70% | -21.76% |
| 2026-11 | -12.61% | -29.05% | -19.06% | -19.06% | -27.77% | -38.52% |

## Without May

MEASURED. Best month of each run: Run 1 (arm g) 2026-05, Run 2 (g2) 2026-05, Run 3 (g3) 2026-05. Joined without it: Run 1 (arm g) -11.96%; Run 2 (g2) -24.99%; Run 3 (g3) -30.05%.

## May against the simple rule

MEASURED. In May the top 7-day rise rule (hold the coins that rose most over the last 7 days) made +55.20%. The model made Run 1 (arm g) +73.16%; Run 2 (g2) +48.44%; Run 3 (g3) +55.08%. The model was above the rule in 1 of 3 runs.

## Limits

STATED. Same months: this tests run-to-run luck only, not other markets.

STATED. Three runs is a small count. A model may still know this period if it falls before its knowledge line; UNKNOWN how much that helps it. The six-model comparison of plan TM06 is still being scored and is not part of this page.

## Run record

MEASURED. The figures above come from these saved files, kept off repo, checked against their fingerprints by `tools/report_saved_tm06r.py`:

- results_tm06_g.json, SHA-256 `cd49fb4c86a74f02bd24866f18c3a07b5508a79e3edf32d04aa5a130aa2fdef5`
- results_tm06_g2.json, SHA-256 `d442db3874d3d39efe056546d4ef1532a896ab97fd322dd82a12d66d4b3b482c`
- results_tm06_g3.json, SHA-256 `4dceedfa5d727734fb6e08b508be986476eb5919cefc60ff48a5ecc871c8c5b5`
- results_tm06_r_shown.json, SHA-256 `e8693ea0baedba729d0c71987f31f3bfd0fcf9d607a9f54d90696d24f5353231`

MEASURED. Each result file holds 8 of 8 picker sessions with no session missing and 1000 twin draws per session. Sessions TM06-P-g-*, TM06-P-g2-* and TM06-P-g3-* are listed in `timemachine/SESSIONS.jsonl`.
