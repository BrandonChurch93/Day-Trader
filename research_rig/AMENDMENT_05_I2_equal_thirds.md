# Amendment to replay 05: rule I2 did not hold equal thirds

Written 2026-11-25 08:22 UTC, before the corrected run. Status: research rig, not the product. Proposed by research. No owner decision is recorded here.

## What was found

An independent audit of `run_05.py` (`archive/audit/2026-11-25_replay_05_audit.md`, finding 1) found that the code for rule I2 does not do what the plan says.

- The plan (`PREREG_05_stock_trend_free_data.md`, rule I2) says: hold the three leading industry groups, one third each, else cash.
- The code splits the account into three thirds once, in 1927, and never again. Each third then grows on its own for 99 years. The first third always gets the top-ranked group when the rule comes back from cash.
- MEASURED by the auditor: by 2006-06-01 the first third was 74.0% of the account, and by 2026-06-30 it was 87.8%. In the held-back slice I2 was close to a bet on one industry group. That is not the rule in the plan.

The audit found no look-ahead and no fault in the other seven rules. Its own separate rebuild of holding the market and of rule T1 from the raw file matched the rig exactly.

## The correction, fixed before the corrected run

- When all three thirds are in cash and the rule moves back into stocks, the account is split into three equal thirds again. This costs nothing extra, because the whole account is cash at that moment.
- A third that is switched while the other two stay invested keeps its own value. The plan says a third is switched only when its group leaves the top three, so the other two are not touched.
- Nothing else changes: same data, same eight rules, same slices, same costs, same marks, same seed, same count of trials (44).
- A new check is added before the run: after a spell in cash, the three thirds are equal on the day of re-entry.

## What must be said plainly about this correction

- It was written after results were seen. The first full run, with the code as it was, is kept as `results_05.json`. The corrected run is written to `results_05b.json`. Both are reported side by side in `docs/research/22_replay_05_stock_trend.md`.
- The auditor measured the effect of this correction before this note was written, at 5 bps a side: I2's largest drop in the held-back slice goes from 73% of the market's to 49%, which moves I2 from fail to pass on mark 1. The overfitting estimate for the whole set of eight rules goes from 0.3068 to 0.1739, which moves mark 4 from fail to pass for every rule, including rules whose own trades do not change at all.
- So any pass that appears only in the corrected run is a pass after a correction whose effect was known. It is reported as that, and not as a clean pass.
- Mark 4 changing for seven rules because an eighth rule was corrected is the same weakness reported in `docs/research/16_rig_audit.md`: the overfitting estimate is a property of the set of rules, and it moves a lot. The value in `backtest_max_pbo` is not changed.

## Other audit findings, handled in the document and not in the run

- Mark 3 does not bind in this test (finding 2). The plan says the spread of Sharpe ratios is taken across these eight rules. They are all the same market and their Sharpe ratios sit close together, so the hurdle is near zero and every rule scores close to 1. The code follows the plan. The document says that mark 3 screened nothing here. The plan is not changed after the run.
- The column called trade sides counted days with a trade (finding 3). Costs were charged correctly on every side. The column is renamed.
- Sentences in the document builder that the output does not support are removed, and the missing readings are added (finding 4).
- The twelve industry sleeves in I1 and in its comparison drift over 99 years (finding 5). That is what the plan says. The document states it.
