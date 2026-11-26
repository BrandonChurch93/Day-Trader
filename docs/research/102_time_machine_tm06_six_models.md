# Time machine TM06: six models as hot-coin picker and swing trader

MEASURED. Formal verdict by the marks fixed in `timemachine/PLAN_TM06_hot_coin_swing.md`: part P, the daily picker, is shown; part S, the hourly swing trader, is not shown. Picker: 5 of 6 models ended above the median of their random twins (needed `tm06_plan.method_min_models_above_median`, 5) and 2 cleared all three marks (needed `tm06_plan.method_min_models_above_percentile`, 2): Claude Sonnet 5.5, Gemini Neon. Both counts sit exactly at the minimum. Swing: 5 of 6 above the twin median, 0 cleared both marks. Fee 12 bps per side.

MEASURED. What the split by month shows, in plain words: where the picker made money, it made it in April to June. In July to November all six models lost money and none ended above either yardstick. In April to June 5 of 6 gained (Grok 4.7 did not) and 4 of 6 were above both yardsticks. In May all six models were at the 100th percentile of their random twins. The split is shown only and changes no mark; it was fixed in advance for the reason given below.

STATED. The plan was logged before any session (ledger rows TM06-P-a to TM06-P-f and TM06-S-a to TM06-S-f, `research_rig/TRIAL_LEDGER.md`). Part P: 48 monthly sessions, six models, eight months April to November 2026, once a day up to `tm06_plan.picker_max_names` of 20 coins in equal parts at 1x, long only. Part S: 24 one-week sessions, six models, four fixed weeks (two falling, two rising), hourly, long or short, on the week's five coins. A first start of part P was void (shared working files) and is not scored here (`docs/STATUS.md`). All 73 sessions (48 P, 24 S and the control) were scored once by `timemachine/score_tm06.py`. STATED by the operator: through the off-repo wrapper that scores sessions in parallel, as for TM06-R; its side check found the result of each of the 72 trader sessions the same as that session's own score file, with 0 differing and 1 absent.

## Part P: the picker, each model over eight months

MEASURED. Months joined by chaining each month's gain. Marks for one model: above yardstick 1 (holding all 20 coins, `equal_all_held`), above yardstick 2 (holding the coins that rose most over the last 7 days, `top_7d_rise`), and strictly above the 90th percentile (`tm_weights_pass_percentile`) of 1000 twins that swap the picks at random.

| Model | Joined gain | Above holding all 20 | Above top 7-day rise | Twin median | Twin percentile | Above 90th percentile | Above twin median | Clears all marks |
| --- | ---: | --- | --- | ---: | ---: | --- | --- | --- |
| Claude Opus 5.5 | -11.31% | no | no | -11.36% | 50.1 | no | yes | no |
| Claude Sonnet 5.5 | +78.10% | yes | yes | +11.59% | 97.4 | yes | yes | yes |
| GPT-6.2 Sol | -19.51% | no | no | -46.67% | 94.6 | yes | yes | no |
| Gemini Neon | +35.73% | yes | yes | -25.46% | 99.6 | yes | yes | yes |
| Grok 4.7 | -29.53% | no | no | -15.01% | 21.1 | no | no | no |
| Kimi K3 | -12.44% | no | no | -15.94% | 56.0 | no | yes | no |

MEASURED. Yardsticks over the same eight months: holding all 20 coins -2.57%; top 7-day rise rule +3.27%. Method count: 5 of 6 above the twin median (need 5), 2 of 6 clear all marks (need 2). Verdict: shown.

## Part P month by month

MEASURED. Each month's gain at 12 bps per side.

| Month | Claude Opus 5.5 | Claude Sonnet 5.5 | GPT-6.2 Sol | Gemini Neon | Grok 4.7 | Kimi K3 | Holding all 20 | Top 7-day rise |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| April | +3.86% | +14.00% | -8.58% | +6.77% | -17.74% | +7.55% | +4.21% | +7.72% |
| May | +64.70% | +81.98% | +79.82% | +62.27% | +43.81% | +63.62% | +10.81% | +55.20% |
| June | -24.54% | +10.21% | -28.69% | -1.80% | -26.85% | -30.85% | -20.64% | -28.63% |
| July | -11.76% | -6.26% | -15.89% | -7.66% | -8.16% | -11.07% | +1.95% | -1.45% |
| August | +23.50% | +15.54% | +24.05% | +24.18% | +13.01% | +27.95% | +25.47% | +35.52% |
| September | +32.76% | +28.24% | +27.39% | +23.61% | +30.98% | +32.54% | +38.14% | +34.72% |
| October | -25.98% | -17.83% | -33.79% | -25.11% | -23.00% | -23.06% | -16.70% | -21.76% |
| November | -35.84% | -31.74% | -21.97% | -24.85% | -22.21% | -37.99% | -27.77% | -38.52% |

MEASURED. Each month's percentile among its 1000 random twins.

| Month | Claude Opus 5.5 | Claude Sonnet 5.5 | GPT-6.2 Sol | Gemini Neon | Grok 4.7 | Kimi K3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| April | 68.9 | 95.4 | 91.3 | 89.8 | 9.3 | 84.4 |
| May | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| June | 13.6 | 98.5 | 25.2 | 90.5 | 4.4 | 5.9 |
| July | 4.4 | 11.3 | 24.8 | 58.3 | 11.5 | 6.8 |
| August | 64.6 | 39.6 | 76.4 | 68.8 | 33.8 | 59.2 |
| September | 58.2 | 32.5 | 63.9 | 60.8 | 73.9 | 42.1 |
| October | 1.4 | 39.6 | 1.4 | 8.8 | 24.6 | 22.9 |
| November | 0.0 | 4.1 | 6.6 | 37.8 | 6.2 | 1.1 |

## Part P split: April to June against July to November

STATED. Why this split, fixed before any result was read: when the Claude Fable 5.2 arm was added (2026-11-25, before any g session and before any TM06 model score was read), the plan recorded that the maker states June 2026 as the reliable knowledge cutoff for Claude Fable 5.2, Claude Opus 5.5 and GPT-6.2 Sol (`docs/research/11_ai_trader_experiment_design.md`), so for those three the April to June sessions lie before the maker's stated knowledge line. Each model's picker months are therefore also shown split at that line (plan section "Added arm: Claude Fable 5.2"). For Claude Sonnet 5.5, Gemini Neon, Grok 4.7 and Kimi K3 that page gives no maker statement (UNKNOWN). The split is shown only and changes no mark. Twin percentiles are not split, because the result file holds no per-draw lists.

| Model | Span | Gain | Holding all 20 | Top 7-day rise | Above holding all 20 | Above top 7-day rise |
| --- | --- | ---: | ---: | ---: | --- | --- |
| Claude Opus 5.5 | April to June | +29.09% | -8.36% | +19.33% | yes | yes |
| Claude Opus 5.5 | July to November | -31.30% | +6.32% | -13.45% | no | no |
| Claude Sonnet 5.5 | April to June | +128.63% | -8.36% | +19.33% | yes | yes |
| Claude Sonnet 5.5 | July to November | -22.10% | +6.32% | -13.45% | no | no |
| GPT-6.2 Sol | April to June | +17.22% | -8.36% | +19.33% | yes | no |
| GPT-6.2 Sol | July to November | -31.33% | +6.32% | -13.45% | no | no |
| Gemini Neon | April to June | +70.14% | -8.36% | +19.33% | yes | yes |
| Gemini Neon | July to November | -20.23% | +6.32% | -13.45% | no | no |
| Grok 4.7 | April to June | -13.46% | -8.36% | +19.33% | no | no |
| Grok 4.7 | July to November | -18.58% | +6.32% | -13.45% | no | no |
| Kimi K3 | April to June | +21.69% | -8.36% | +19.33% | yes | yes |
| Kimi K3 | July to November | -28.05% | +6.32% | -13.45% | no | no |

MEASURED. April to June: 5 of 6 gained, 4 of 6 above both yardsticks; for 6 of 6 the April to June gain is larger than the gain over all eight months. July to November: 6 of 6 lost, 0 of 6 above either yardstick. Of the models that cleared all picker marks (Claude Sonnet 5.5, Gemini Neon), 0 have a maker's stated June 2026 cutoff in `docs/research/11_ai_trader_experiment_design.md`.

## Part S: the swing trader, each model over four weeks

MEASURED. Weeks joined by chaining, at 1x and 12 bps per side. Marks for one model: above holding the week's five coins in equal parts, and strictly above the 90th percentile of 1000 twins that play the model's own answers in shuffled order.

| Model | Joined gain | Holding the five | Above holding the five | Twin median | Twin percentile | Above 90th percentile | Above twin median | Clears both marks | Rising weeks | Falling weeks |
| --- | ---: | ---: | --- | ---: | ---: | --- | --- | --- | ---: | ---: |
| Claude Opus 5.5 | -16.08% | -2.78% | no | -28.07% | 100.0 | yes | yes | no | -10.38% | -6.36% |
| Claude Sonnet 5.5 | -6.95% | -2.78% | no | -12.51% | 98.1 | yes | yes | no | -3.67% | -3.41% |
| GPT-6.2 Sol | -11.93% | -2.78% | no | -18.16% | 99.2 | yes | yes | no | -8.23% | -4.03% |
| Gemini Neon | -31.77% | -2.78% | no | -40.09% | 95.5 | yes | yes | no | -23.83% | -10.43% |
| Grok 4.7 | -18.27% | -2.78% | no | -11.22% | 5.7 | no | no | no | -12.94% | -6.12% |
| Kimi K3 | -16.00% | -2.78% | no | -16.07% | 51.2 | no | yes | no | -8.47% | -8.23% |

MEASURED. Method count: 5 of 6 above the twin median (need 5), 0 of 6 clear both marks (need 2). Verdict: not shown.

MEASURED, shown and not judged: trades, share of time in the market, and the answers carried at 2x and 3x at 12 bps, joined over the four weeks.

| Model | Trades | Mean time in market | Carried 2x | Carried 3x | Forced close-outs 2x / 3x |
| --- | ---: | ---: | ---: | ---: | ---: |
| Claude Opus 5.5 | 488 | 68% | -29.80% | -41.39% | 0 / 0 |
| Claude Sonnet 5.5 | 177 | 69% | -13.56% | -19.81% | 0 / 0 |
| GPT-6.2 Sol | 246 | 18% | -22.52% | -31.92% | 0 / 0 |
| Gemini Neon | 356 | 84% | -53.95% | -69.43% | 0 / 0 |
| Grok 4.7 | 145 | 23% | -33.37% | -45.84% | 0 / 0 |
| Kimi K3 | 242 | 27% | -29.54% | -40.98% | 0 / 0 |

## Fees

MEASURED. Main fee `tm06_plan` main_fee_bps, 12 bps per side; the other levels in `tm_perp_fee_levels_bps` are shown, not judged. Every level also charges each coin's half spread (3 to 31 bps, as stored with each session) and funding. Joined by chaining each session's gain at that fee.

| Model | Picker at 1 bps | Picker at 12 bps | Picker at 25 bps | Swing at 1 bps | Swing at 12 bps | Swing at 25 bps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Claude Opus 5.5 | +0.17% | -11.31% | -23.22% | -7.66% | -16.08% | -25.05% |
| Claude Sonnet 5.5 | +97.14% | +78.10% | +57.86% | -3.69% | -6.95% | -10.66% |
| GPT-6.2 Sol | -2.06% | -19.51% | -36.20% | -4.51% | -11.93% | -19.96% |
| Gemini Neon | +54.98% | +35.73% | +15.98% | -21.73% | -31.77% | -42.01% |
| Grok 4.7 | -19.61% | -29.53% | -39.72% | -13.46% | -18.27% | -23.61% |
| Kimi K3 | -0.86% | -12.44% | -24.42% | -10.12% | -16.00% | -22.47% |

## Claude Fable 5.2 against the six

STATED. Plan section "Added arm: Claude Fable 5.2": arm g was scored apart and never enters the six-model counts. Shown apart and not judged: whether its joined result ends above the best of the six on the same months and weeks, at 12 bps and 1x. Arm g itself is on page 78 (`docs/research/78_time_machine_tm06r_fable_repeat.md`).

- MEASURED. Picker, eight months: Claude Fable 5.2 +52.45%; best of the six Claude Sonnet 5.5 +78.10%. Above the best of the six: no.
- MEASURED. Swing, four weeks: Claude Fable 5.2 -13.26%; best of the six Claude Sonnet 5.5 -6.95%. Above the best of the six: no.

## Limits

STATED. Plan TM06's own list ("How this can fool us") applies in full. The points that matter most here, as written there or measured on this page:

- One stretch of one year. The picker's result rests on April to June; July to November lost for every model.
- Six models tend to like the same coins. If those led, all six look good together, and that is one bet, not six. In May all six were at the top of their twins.
- The coin list is today's survivors. Coins that died are missing, which flatters every buyer; the yardsticks share the flattery, so only the comparisons mean anything, not the gains.
- For three of the six the April to June months lie before the maker's stated knowledge line. UNKNOWN how much a model knows of that period, and UNKNOWN for the four models with no maker statement.
- The picker's verdict met both method counts at exactly the minimum.
- Four weeks is a small sample for part S.

STATED. The limits the scorer writes into the result file:

- A model may still know this period if it falls before the model's knowledge line. UNKNOWN how much that helps it.
- The no-search and no-file rule is given by instruction. It is not enforced by this program.
- News headlines and summaries are as first recorded. A story edited after it was first published is marked edited_later, and its text may hold the later edit.
- The stock list is today's list. Stocks delisted during the window are missing.
- Prices are raw, not adjusted for splits or dividends. A split inside a held position is not handled. Dividends are not paid.
- Fills are assumed: the open of the first recorded minute at or after the wake, a fixed half spread and fee per symbol. There is no cap on the share of a minute's volume. They are not real fills.
- Perpetual futures are modelled as linear USD contracts priced at the spot minute bars on the tape, not at a venue's own mark or index price.
- Funding is the stored hourly Kraken rate where tm_perp_funding_files has the symbol, else a fixed fallback paid by both sides.
- Stops, targets and the maintenance rule are checked on minute highs and lows. With several symbols the worst prices of one minute are taken together, which they need not be.
- Inside one minute the order of prices is not known: a minute that crosses both a stop and a target is counted as the stop.
- Between wakes only the minutes of symbols held are read. Funding falling on a minute where only a symbol not held traded is charged at the next minute of a held one.
- The fast tape's funding is from Kraken's non-US perps by default; a US venue's rates may differ. Before a coin's first stored rate the fixed fallback is charged.
- Open interest and attention counts are shown as they were known at the wake; the store does not always say when a value was first published, so attention uses the reader's assumed lag.

## What the plan says follows

STATED, from the plan: a pass in either part earns a longer test of that part on dates not used here, and does not earn real money. If a part does not pass, the write-up names which yardstick each model lost to: in part S each model's marks are in the table above.

## Run record

MEASURED. The figures above come from these saved files, kept off repo, checked against their fingerprints by `tools/report_saved_tm06_six.py`:

- results_tm06_six_fast.json, SHA-256 `e50d82af23f731158bee11eaebbd0ed367fb56ebeeec41cdfdec87123cb35412`
- tm06_six_p_split.json, SHA-256 `42311c02156e343a70522a1c8f7a3e9daa0bf33aca03effed5bf62255b7929e4`
- results_tm06_g.json, SHA-256 `cd49fb4c86a74f02bd24866f18c3a07b5508a79e3edf32d04aa5a130aa2fdef5`

MEASURED. The six-model file holds 73 sessions (48 picker, 24 swing, 1 control), every model with all eight months and all four weeks and none missing, and 1000 twin draws per session. The sessions are listed in `timemachine/SESSIONS.jsonl`.
