# TM09 power from finished repeat runs (queue 115, ledger 222)

INFERENCE: Do not launch the registered stock replay on the strength of these results. Our closest stock repeats imply a roughly 91 bp weekly gap between two runs of the same model, but the weekly books needed to measure that gap directly no longer exist. At that inferred noise level, the registered design has about a 23% chance of passing its t and positive-week marks at a true +20 bp a week, before the other gates. I would run a separate price-only rehearsal on unused weeks first, then decide whether to change the design.

## What finished

MEASURED from [the session index](../../timemachine/SESSIONS.jsonl), the saved score summaries and the reports below. Counts refer to distinct finished scores, not lines in the launch index. [The generated JSON](../../timemachine/POWER_TM09.json) names all sessions used for this inventory and counts exact-window, same-model overlaps between tasks.

| Run | What the records support | Limit |
|---|---|---|
| [TM01](29_time_machine_tm01_crypto_price_only.md) and [TM02](30_time_machine_tm02_crypto_with_news.md) | 30 sessions each. Six models each ran five matched model-months across the two tasks. | TM02 changes the information and the card. No exact within-task repeats or retained weekly marks. These comparisons include treatment and chance. |
| [TM03](34_time_machine_tm03_bitcoin_dial.md) | 48 finished sessions. Each of six models had eight months. There are 30 exact same-model windows against each of TM01 and TM02. | The earlier Opus June entry was void before any packet; only the replacement was scored. BTC-only weights are a larger task change, not repeat noise. |
| [TM04](36_time_machine_tm04_stock_basket.md) | 12 finished sessions: six exact model pairs on the same stock roster and dates. The reports identify fresh sessions for both runs. | The published summary has whole-run results, not weekly NAV. Same stocks as TM09, but an invested basket that changes weekly, with news in both runs. No Fable stock repeat. |
| [TM06](102_time_machine_tm06_six_models.md) | 56 picker scores and 28 swing scores, including the original Fable runs, plus a code control. The six-model score file has one result per ID despite duplicate launch-index lines. | The picker and swing change the task and window. Fee and leverage rows rescore the same decisions; shuffled twins and the code control are not fresh model repeats. TM06 picker dates match several TM01 to TM03 months, but the exposure, task and costs change. |
| [TM06-R](78_time_machine_tm06r_fable_repeat.md) | The [addendum](../../timemachine/TM06R_addendum.md) adds 16 sessions to the eight original Fable picker sessions, giving three repeats on the same eight months. | The saved results have monthly, not weekly, returns. Adding an isolation instruction for the new runs does not make them different trading treatments. The three pairings reuse sessions. |

MEASURED: The TM06 swing score file has direct weekly net returns, but no same-model repeat of a swing week. As a separate check, the pooled within-pair weekly SD across different models was **279.0 bp**: seven models, 21 model pairs on four shared weeks, 84 pair-weeks. The calculation subtracts each model pair's own mean before pooling. This is a different-model coin contrast on four dates, not stock noise or another independent repeat sample.

## Nearest stock and coin noise

The lead confirmed that the original per-session NAV folders were removed and there is no approved backup. MEASURED: There are no observed weekly repeat pairs in the remaining scores. The dollar gaps below are saved whole-run figures. INFERENCE: Convert the two terminal net gains to log returns, take their gap in bp, and divide by the square root of 24 elapsed weeks. TM04 has 25 weekly wakes and 24 intervening seven-day intervals, ignoring the closing stub. Under independent, equal-variance weekly gaps and no systematic run-order effect, the root mean square of those scaled gaps is a proxy for weekly repeat-gap SD. Each model contributes just one draw, not its own measured weekly SD. The smallest and largest draws are scenarios, not confidence bounds.

| TM04 model | Scored repeat pairs | Whole-run gap, run 1 minus run 2 | Implied weekly gap amplitude |
|---|---:|---:|---:|
| Claude Opus 5.5 | 1 | -$29.93 | 64.4 bp |
| GPT-6.2 Sol | 1 | -$35.13 | 70.7 bp |
| Kimi K3 | 1 | +$33.10 | 78.5 bp |
| Gemini Neon | 1 | +$41.02 | 95.9 bp |
| Grok 4.7 | 1 | +$54.64 | 112.7 bp |
| Claude Sonnet 5.5 | 1 | +$51.27 | 113.5 bp |
| Pooled, root mean square | 6 | | **91.4 bp** |

INFERENCE: The same calculation on the Fable coin months gives **484.9 bp** pooled, with three pairing values of 361.4, 430.6 and 624.0 bp. It uses 24 pair-months over eight calendar months; divide each gap by the square root of its own block length, 3.29 to 4.43 weeks. At the same monthly resolution, the TM01 to TM02 near-comparisons imply 146.2 bp pooled from 30 pairs (five monthly pairs per model; 75.2 to 205.4 bp across models, with 3.43 to 4.43 weeks per block). The latter mixes a change in method with noise. Neither coin result is used as a stock input. Shared dates, repeated sessions and carry-over positions mean these counts do not supply that many independent observations.

## TM09 mark power

INFERENCE: The fixed-seed script draws 120,000 sets of 20 weeks. It applies the registered one-sided t cutoff and the required count of positive weeks to the weekly average over both bosses of N minus the mean of P1 and P2. The central model assumes independent weeks, normal noise, no correlation between bosses' treatment contrasts, and equal within-arm and between-arm correlation from shared price notes. With equal correlations, the common part cancels: the primary SD is the single-boss repeat-gap SD times the square root of (3/8). An equal-variance Student t with five degrees of freedom and a shared-noise stress case are also shown. The stress case assumes 0.50 correlation within each arm type, 0.25 between P and N, and 0.50 between bosses' contrasts; these are assumptions, not fitted.

| Case | +20 bp | +50 bp | +100 bp | True edge for 80% |
|---|---:|---:|---:|---:|
| Baseline, low stock proxy | 45.0% | 99.9% | ~100% | 29.1 bp |
| Baseline, central stock proxy | 22.6% | 93.1% | ~100% | 41.3 bp |
| Baseline, high stock proxy | 14.8% | 77.7% | ~100% | 51.3 bp |
| Central, fat tails | 25.9% | 92.1% | 99.9% | 40.7 bp |
| Central, shared news and boss noise | 9.7% | 54.8% | 99.3% | 65.3 bp |

INFERENCE: These are two-mark probabilities, not the chance of the full **news helps** label. They assume every week finishes and do not apply the best-week removal, mean floor, placebo, delivery, or forward-label gates. In particular, with continuous symmetric noise and a true gain exactly at the registered +20 bp floor, only half of observed means reach that floor, regardless of how small nonzero noise gets. Under the central assumptions the two marks alone would need primary SD no higher than 27.1 bp for 80% power at +20. Serial dependence, common news-note errors and market regimes remain unmeasured.

## Changes without adding judged weeks

INFERENCE: All rows below use the same central stock proxy and normal weeks. For a changed outcome, the scale in the table is a stated scenario, not evidence of a variance reduction. The JSON also has low and high proxy cases for all these scenarios.

| Proposed design or outcome | +20 bp | +50 bp | +100 bp | True edge for 80% |
|---|---:|---:|---:|---:|
| Three fresh P and three fresh N per boss-week | 49.9% | ~100% | ~100% | 27.5 bp |
| Stock scores or news-only names, unchanged SD | 22.6% | 93.1% | ~100% | 41.3 bp |
| Either changed outcome, if SD is 75% of baseline | 40.1% | 99.7% | ~100% | 31.0 bp |
| Either changed outcome, if SD is half of baseline | 77.1% | ~100% | ~100% | 20.6 bp |
| Either changed outcome, if SD rises to 125% | 14.7% | 77.1% | ~100% | 51.6 bp |
| Blinded five-week stop or enlarge rule | 27.9% | 93.5% | 99.0% | 39.7 bp |

- **More sessions:** Three fresh runs per arm type cost 240 instead of 120 boss sessions over the same weeks. Hold the scouts, notes and wake clocks fixed. If N runs repeat the same news-note errors, more draws will not average that error away. In the shared-noise stress case the central power at +20 is only 13.8%, with an 80%-power edge of 53.3 bp.
- **Score every stock:** Ask for a signed score from -2 to +2 at each wake. For the fixed long-only portfolio, assign positive scores proportional weights against a fixed roster budget and keep the unused budget in cash; apply the same fills and costs. Separately, the proposed primary is the mean across stocks of signed score divided by its maximum magnitude times the next nonoverlapping wake-to-wake return, reduced to one weekly value with a fixed wake aggregation. This signal measure is not the portfolio's net return. No past session records comparable scores for every name and wake; turning picks into zeros for all other names would invent observations. The actual SD and its practical effect size need a repeated rehearsal using this output.
- **Restrict to news-bearing stocks:** Fix the stock and wake mask with the admission clock and apply the identical mask to P and N. Hold the horizon, weighting and capital rule fixed, using cash for unused capacity. P learns that a stock had an item but not what it said; the contrast now tests content beyond that eligibility signal. Fewer names can concentrate rather than reduce noise. The coverage census has no matched portfolio return on the mask, so both its variance and the change in true effect are unknown.
- **Blinded stop or enlarge:** After five weeks, a separate checker sees only the SD of the weekly boss-averaged P1 minus P2, not any N result or arm profit. Under the normal equal-correlation model, map it to each candidate design's SD. Use the baseline if its projected 80%-power edge is no more than +50 bp; otherwise switch to three per type if that design meets the same limit, or stop. If enlarged, add fresh sessions on the first five weeks too, without changing any finished session or reading N. The simulation assumes the blinded contrast is independent of the primary noise (orthogonal Gaussian contrasts) and counts stops as failures. At the central proxy it keeps 78.9%, enlarges 20.1% and stops 1.0%. This would need a new seal; the present registration reads no interim return. Correlated or heavy-tailed contrast errors can break the independence argument.

## Rehearsal before a launch decision

INFERENCE: First use made-up bars and headlines to check delivery, isolation, timing, round trips through the scorer and the frozen aggregation. That cannot measure real discretion or market noise. For the next stage, choose and seal unused full stock weeks in advance, entirely outside the scored 20 and after both makers' knowledge lines. There are no such full weeks between the later knowledge line and the scored window, so a prospective price-only sample is the cleanest option. No newsroom input is needed for that rehearsal.

INFERENCE: Run a shared price scout and independent P1/P2 sessions for both bosses each week. Reduce each week to the average of the two within-boss gaps, so the SD reflects any correlation between the bosses' gaps under the shared notes. With independent normal weekly gaps, a 90% chi-square interval from five weeks is 0.65 to 2.37 times the measured SD. **Seven weeks** (28 boss sessions) give a 90% interval within a factor of two; **14 weeks** (56 boss sessions) get within a factor of 1.5. At 95% confidence those counts are nine and 18 weeks. These precision statements do not hold unchanged under dependence or heavy tails. The rehearsal can measure P-repeat noise, but not N-specific common noise, news delivery in real conditions, or the true news effect.

INFERENCE: I would start with the seven-week price-only noise check. Use the upper interval bound, not just the point estimate, in the launch decision. If a decision about a larger, explicitly agreed edge still needs more power, prefer the three-per-type design over changing the outcome or masking stocks, since it keeps the same comparison. If the target remains +20 bp, neither the current marks nor running more copies alone establish an 80%-powered test. Do not reuse rehearsal weeks as judged weeks.

Reproduce the numbers with `nice -n 10 python3 -B research_rig/power_tm09.py`. The script reads only the indexed and already-scored material named above, plus the approved off-repo finished TM06 summaries. It never opens bars, input packets, raw headlines, a TM07 path or a held-back script. The JSON contains session IDs and aggregate results only, no per-trade rows.
