# Replay 52. Corporate bond funds after quarter-end

MEASURED. The rule did not pass: **0 of 6 frozen marks**. The basket averaged -0.0308% net per quarter-end (t -0.24) across 40 quarters and rose in 20 of them. Net of the Treasury proxy it averaged -0.0197% (t -0.17). The same basket averaged +0.1279% after ordinary month-ends (t 1.73). The rule does not advance.

## The rule

STATED, from the [frozen plan](../../research_rig/PREREG_52_quarter_end_dealer_rebound.md). Split $500 equally across LQD, HYG, JNK, VCIT using fractional shares. Buy at the last scheduled quarter close and sell at the close after 3 new-quarter sessions. Credit dated cash distributions during the hold without reinvesting. Use raw daily SIP closes and 2 basis points of assumed cost per side; no quote spread was measured. Subtract the same-window gross IEF return for LQD and VCIT and the IEI return for HYG and JNK. The proxies are comparisons, not short trades or exact duration matches.

STATED. Judged dates are quarter-ends from 2016 through 2025, with the same-window ordinary month-ends as the control. The licensed raw SIP source begins in 2016, so the earlier year in the original draft was removed before any price was read. No substitute or mixed-vendor data filled it. The 2026 quarters were set aside from every mark.

## Frozen marks

MEASURED. All marks had to pass. Zero does not meet a positive sign mark. The raw net t and positive-quarter count are context, not marks.

| Mark | Measured | Verdict |
|---|---:|---|
| Net mean above zero | -0.0308% | not met |
| Net mean after the Treasury proxy above zero | -0.0197% | not met |
| Net-of-proxy t at least 2.0 | -0.17 | not met |
| Net mean above ordinary month-ends | -0.0308% against +0.1279% | not met |
| Net mean above zero without the best 3 quarters | -0.1530% | not met |
| Net mean above zero on 30 non-December quarters | -0.0497% | not met |

## Shown only

MEASURED. Quarter-end minus ordinary month-end was -0.1587 percentage points (Welch t -1.06). The t had no pass threshold and does not adjust for shared or serial shocks. Ordinary month-ends were positive in 48 of 80 windows.

MEASURED. The 3 2026 windows averaged +0.2369% net and +0.2792% after the Treasury proxy. They are not a second trial and do not change the result.

## In dollars

MEASURED. On a fresh $500 at each entry, the mean net result was -$0.15 per quarter-end basket, or -$0.62 per year at 4 round trips without compounding, before taxes. STATED. These are sample averages at assumed fills, not expected profits or losses.

## What the result can show

STATED. [Rapp and Waibel](https://www.aeaweb.org/conference/2026/program/paper/S2KkB95R) studied dealer balance sheets; this replay tested an ETF trade, not their mechanism. Replay 31 already used parts of the post-close clock in a pooled daily comparison, as disclosed in the frozen plan.

MEASURED, synthetic only. The pre-run model passed 36.70% of worlds with a true quarter-only edge of +20 bp. With that same edge at every month-end, it passed 27.78%. STATED. This failure does not rule out a small effect, and even a pass would not establish that the rise is special to quarter-ends. UNKNOWN. Whether live fractional orders could have obtained these closes.

## Data checks and run record

- **Validation**: STATED, from the lead's counts-only check. It placed 123 windows: 40 judged, 80 controls and 3 shown. There were 30 non-December judged windows. Each of 6 symbols had 2,704 sessions (16,224 bars in total). Validation checked one split and found no holding window that crossed it.
- **JNK history**: STATED, from the lead's custody report. The first vendor query omitted 839 JNK sessions before the reverse split in 2019. The custodian recovered those sessions using the documented literal-ticker setting, and the code auditor rebuilt the packet byte for byte. No adjusted data were substituted.
- **Cash history**: STATED, from the lead's custody report. The independent checker added five cash distributions for 2016-08-01 that were missing from the vendor, using issuer pages. The off-repo checker report is pinned below.
- **First command**: STATED, from the lead. The first `--go` refused with `P52_PRIVATE` before the lock was claimed and before any return was computed. The results directory had the wrong mode and contained the validation output. The lead moved those files out, set the directory to `0700`, and the one scored run completed.
- **Claim**: MEASURED. The saved result was claimed 2026-11-26 01:03:16 MST (2026-11-26 08:03:16 UTC). This report reads the pinned saved result only. The lock stays in place.

## Independent recompute

MEASURED. Entry and exit dates matched for all 40 quarters, 80 controls and 3 shown windows. The largest absolute per-window return difference was on the order of 1e-18; summaries matched to floating-point precision and all 6 marks failed in both. STATED. The independent reviewer wrote the recompute before opening the saved result and did not open the scorer. The recompute note is off repo, SHA-256 `f76b54e7cf35bea6f651ae960da92e71efd789d526cdbd9a3eb4dbfa0391850b`.

STATED. A future plan could put these details together more explicitly. The review used the 80 non-quarter month-ends in 2016 through 2025; applied the same ex-date cash rule to Treasury proxies; used sample standard deviation with n minus one for t; treated positive as strictly above zero; trimmed the highest 3 raw net results out of 40; and applied trading cost on fund legs only. All these readings matched the scorer.

## Pins

- Approval commit `0416682d0183021ddc468d90a3c75bf6ef5b6e17`
- Freeze commit `3cc2c8c4d4868e9d9433248526c1156dea133e0a`
- Saved result SHA-256 `a4e7e74f0cca19f2b1ae22130f5816a7b6a9ff062847ef0c710fc5c185c1beca`
- Lock SHA-256 `8ec1943cb08c4d78c0cf2f8920a86813760e551ed379460aafe592058148d22f`
- Freeze manifest SHA-256 `d3f256b41fff31e10d699a87850838e6b33f7442d143254c7b355f05186cd42e`
- Input manifest SHA-256 `ce606dc16e1e3078931209ac6b696349ae54bf694078b5c1a43daf26cb4655c7`
- Cash-action packet SHA-256 `e7cdfd61a5e71321dcc3a58d547b484e190d5a7232b44ac767c2dca7ce7ffaad`
- Independent cash review SHA-256 `f6bb59a4dea09140db22485479be25eae30e703c769fc43b7f1cee096d9aa54e`
