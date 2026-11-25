# Replay 05 Code Audit (US Stock Market Slow Trend, Free Ken French Data)

Date: 2026-11-25
Auditor: Independent Auditor B
Target: `/home/user/workspace/dt-work/research_rig/` (`PREREG_05_stock_trend_free_data.md`, `AMENDMENT_2026-11-25_audit_fixes.md`, `run_05.py`, `rig2.py`, `build_doc22.py`, `data_notes_french.md`).
Probe script: `/home/user/workspace/dt-work/audit/replay_05_probes.py` (single process, read-only on rig and data).

---

## Summary of Findings (Ranked by Impact)

### 1. `I2` slot engine never pools cash back into thirds, causing 88% single-slot concentration and flipping both mark 1 and mark 4
- **Severity:** High (flips verdicts)
- **File and line:** `research_rig/run_05.py:44-56` (`sim_slots`), `research_rig/run_05.py:85-96` (`i2_assign`)
- **How known:** MEASURED (`audit/replay_05_probes.py`, Probes 4 and 8)
- **What is wrong:** `PREREG_05:50` specifies for `I2`: "At each month end, if T1 says hold the market, hold the three industry groups with the highest 12-month return, one third each, else cash. A third is switched only when its group leaves the top three." In `sim_slots`, the three slots start at `1/3` each in 1927 and are never rebalanced, not even when `T1` exits all three slots to cash and later re-enters stocks. Meanwhile, `i2_assign` sorts `top` descending by 12-month return and fills free slots with `free.pop(0)`, so whenever all three slots re-enter from cash, slot 0 always receives the #1 momentum industry, slot 1 receives #2, and slot 2 receives #3. Over 79 years of development history, slot 0 compounds to **74.03%** of `I2` by `2006-06-01` and **87.81%** by `2026-06-30` (mean **76.15%** over the held-back slice), while slot 2 shrinks to **2.33% to 7.65%** (mean **6.05%**). In the held-back slice, `I2` is effectively a single-industry concentrated portfolio rather than three equal thirds.
- **What it changes and whether it flips a verdict:** YES, flips verdicts at 5 bps a side:
  - With drifted slots (current code): `I2` held-back `CAGR = +13.27%`, `SR = 0.656`, `MDD = -39.69%`, `dd_ratio = 0.727` (**FAILS mark 1** `<= 0.60`). Across the 8 rules, 5 bps `PBO = 0.3068` (**FAILS mark 4** `< 0.25` for all 8 rules).
  - With cash pooled back into equal `1/3` slots on all-cash re-entry (zero extra trade cost, since the account is already 100% in cash): `I2` held-back `CAGR = +11.12%`, `SR = 0.650`, `MDD = -26.94%`, `dd_ratio = 0.494` (**PASSES mark 1** `<= 0.60`), whole-sample `SR` rises from `0.636` to `0.652`, and the 8-rule 5 bps `PBO` drops from `0.3068` to **`0.1739`** (**PASSES mark 4** `< 0.25` for all 8 rules, affecting `T1`, `T5`, `V1`, `I1`, and `I2`).
- **Suggested fix:** In `sim_slots`, whenever all slots are in cash (`(cur < 0).all()`) and the next assignment enters stocks, reset `val[:] = val.sum() / ns`. If the plan intends equal thirds at every replacement as well, rebalance toward `1/3` per slot when switching or on a drift band.

### 2. Deflated Sharpe hurdle is near zero because cross-rule Sharpe spread is computed across 8 tightly clustered stock rules
- **Severity:** Medium (makes mark 3 non-binding, though it matches the PREREG text)
- **File and line:** `research_rig/run_05.py:145, 152`
- **How known:** MEASURED (`audit/replay_05_probes.py`, Probe 5)
- **What is wrong:** `run_05.py` computes `sd = np.std([R.sharpe_pp(X[n]) for n in NAMES], ddof=1)` across the 8 US stock rules only, matching `PREREG_05:78` ("Trials counted: 44 (36 before, 8 here). The spread of Sharpe ratios used in the formula is taken across these 8 trials"). Because all 8 rules are correlated long-US-equity rules with 99-year Sharpe ratios clustered between `0.517` and `0.636`, `sd = 0.002439` per day, which is 2.5 times smaller than a single rule's theoretical Sharpe standard error `1/sqrt(26014) = 0.006200`. That produces an annualized hurdle of only `sr0 = 0.086`, so all 8 rules trivially score `DSR = 1.0000`.
- **What it changes and whether it flips a verdict:** Does not flip a verdict relative to `PREREG_05` (the code implements the PREREG as written), but mark 3 provides no real multiple-testing screen here.
- **Suggested fix:** Flag in the research note that mark 3 is non-binding under the 8-rule spread; for future plans, pool the Sharpe spread across all counted trials or floor `sd` at `1/sqrt(T)`.

### 3. "Trade sides a year" (`sides`) undercounts actual sides traded (especially for `I1` and `I2`)
- **Severity:** Low (reporting only; does not change returns, costs, or marks)
- **File and line:** `research_rig/run_05.py:54, 114`, `research_rig/rig2.py:118-121`, `research_rig/build_doc22.py:10, 15`
- **How known:** READ and MEASURED (`audit/replay_05_probes.py`, Probe 6)
- **What is wrong:** `rig2.activity` counts `int((traded > DUST * prev).sum())`, which is the number of calendar trading days with a non-zero trade. Every switch in `sim_ret` and `sim_slots` actually pays two sides (`sides = 2`), so single-asset switches are counted as 1 instead of 2 sides. For `I1` (12 sleeves summed into one `tr[t]`) and `I2` (3 slots summed into one `tr[t]`), multiple sleeves or slots switching on the same day are collapsed into 1 instead of up to 24 sides (`I1`) or 6 sides (`I2`).
- **What it changes and whether it flips a verdict:** Cannot flip any verdict; transaction costs are properly charged per sleeve/slot at `2 * cost_bps` inside `sim_ret` and `sim_slots`. Only the reported "Trade sides a year" column in `doc22` is understated.
- **Suggested fix:** Return explicit side counts from `sim_ret` and `sim_slots` (incrementing by `sides` per sleeve/slot trade), or relabel the column "Trade days a year".

### 4. `build_doc22.py` contains hardcoded prose not supported by `results_05.json` and minor PREREG reporting omissions
- **Severity:** Low (doc prose only; does not change numbers or verdicts)
- **File and line:** `research_rig/build_doc22.py:22, 32, 62, 64, 103`
- **How known:** READ
- **What is wrong:**
  1. `build_doc22.py:103` hardcodes: `"The held-back slice holds two fast falls with fast rebounds (2020 and 2022) and one slow fall (2008)."` Describing 2022 as a "fast fall with fast rebound" is not derived from `results_05.json` and is inaccurate for US stocks (the 2022 drawdown unfolded over roughly 10 months and took roughly two years to reclaim its prior peak).
  2. `build_doc22.py:22` does not emit the PREREG-mandated phrase `"passes the marks, but holding less stock did as well"` (`PREREG_05:82`) if a rule passes all five marks without beating the fixed mix (it only prints `PASS | no`).
  3. `build_doc22.py:64` prints only `pb['pbo']`, omitting the other tie readings (`pbo_strict`, `pbo_half`) and `pbo_drop_latest` required by `PREREG_05:70` and `AMENDMENT_2026-11-25_audit_fixes.md:26` (note: for `N = 8`, `tie_share = 0.0`, so `pbo == pbo_strict == pbo_half = 0.3068`, while `pbo_drop_latest = 0.3193`).
  4. `build_doc22.py:62` says `"with the same average share in stocks"` without stating that the fixed mix weight comes from the development slice (`dev` average weight differs from `held` average weight by 4 to 12 percentage points across the 8 rules).
  5. `build_doc22.py:32` omits `HOLD12` (the benchmark for `I1`) from `years_tab`.
- **What it changes and whether it flips a verdict:** Cannot flip any verdict.
- **Suggested fix:** Remove the hardcoded "fast fall with fast rebound" claim about 2022, add the `PREREG_05:82` conditional note in `marks_tab`, print `pbo_drop_latest` and `tie_share` in line 64, specify "development-slice average share in stocks" in line 62, and add a `HOLD12` row to `years_tab`.

### 5. `I1` and `HOLD12` sleeve weights drift substantially over 99 years (matches plan, worth noting)
- **Severity:** Cosmetic / informational (matches `PREREG_05:49`)
- **File and line:** `research_rig/run_05.py:111-114`
- **How known:** MEASURED (`audit/replay_05_probes.py`, Probe 4)
- **What is wrong:** Because the 12 industry sleeves start at `1/12` (`8.33%`) in 1927 and are never rebalanced, by `2006-06-01` `I1` sleeve shares range from `2.81%` to `18.52%` (`2.42%` to `16.10%` by `2026-06-30`), and `HOLD12` sleeve shares range from `1.21%` to `20.25%` (`0.85%` to `19.05%` by `2026-06-30`). This matches `PREREG_05:49` ("buying the twelve groups in equal parts at the start and holding them"), so it is not a bug, but readers should know the held-back comparison is not equal-weighted across the 12 industries.
- **What it changes and whether it flips a verdict:** No code defect; does not flip a verdict against the plan.

---

## Checklist Verification

1. **Look-ahead (MEASURED, Probes 2 and 2b):**
   - Perturbed all returns (`rm`, `rf`, `ind`) strictly after five cutoffs (`2006-05-15`, `2006-05-31`, `2006-06-01`, `2020-03-16`, `2022-06-30`) and verified zero changes in any target for all 8 rules (`T1` to `T5`, `V1`, `I1`, `I2`) on or before the cutoff.
   - Verified signal-to-fill lag: `sim_ret(..., lag=1)` and `sim_slots(..., lag=1)` decide `target[t]` at close of day `t`, execute the trade at close of day `t+1`, and begin earning the new position on day `t+2`. Month-end rules (`T1`, `T3`, `I1`, `I2`) flip `target` on the month-end trading day (e.g., `1929-10-31`, `2007-12-31`) and trade at the close of the next trading day (`1929-11-04`, `2008-01-02`).
   - Bill rate `rf[t]` is earned only on cash held during day `t` before any end-of-day trade on day `t`. No look-ahead.

2. **Rule wording vs code (READ and MEASURED, Probes 2, 3, 4):**
   - `T1`, `T2`, `T3`, `T4`, `V1`, `I1`: match `PREREG_05` clause by clause.
   - `T5` (Trendpilot first version): matches all four clauses (5 closes above 200-day SMA -> `1.0`; 5 closes below after `1.0` -> `0.5`; while `< 1.0`, if 200-day SMA `<` its value 5 trading days earlier -> `0.0`; only 5 closes above returns to `1.0`). Initializing `state = 0.0` vs `1.0` at the 200th bar produces 0 differences after `1927-08-01`.
   - `0.10` band: enforced on all fractional weight changes with no exception for moves to or from zero (`abs(tw - cur) > band`), matching `PREREG_05:36` and Amendment A12.
   - `I2`: slot assignment logic (`i2_assign`) matches "switched only when its group leaves the top three", but `sim_slots` violates "one third each" (Finding 1).

3. **Costs, cash rate, Sharpe, and fixed mix (READ and MEASURED):**
   - Switches between stocks and cash pay `2 * cost_bps` (`sides = 2`) at 2, 5, and 10 bps per side; `HOLD` and `HOLD12` pay entry cost on initial buy at `t = 1`.
   - Cash earns `rf`; Sharpe uses excess returns `r - rf` with `PPY = 252` and `ddof = 1`.
   - Fixed mix weight `wbar` is taken strictly from the development slice (`dev`, `1927-08-01` to `2006-05-31`), with no held-back leakage; all 8 rules have `wbar` in `[0.660, 0.798]`, well above the `0.10` band so fixed mix always enters on `t = 1`.

4. **Slices (MEASURED, Probe 1):**
   - `dev`: 20,899 return days (`1927-08-01` to `2006-05-31`, base `1927-07-31`).
   - `held`: 5,051 return days (`2006-06-01` to `2026-06-30`, base `2006-05-31`).
   - `post`: 64 return days (`2026-07-01` to `2026-09-30`, base `2026-06-30`).
   - Single years: `y2008` (253 days, base `2007-12-31`), `y2020` (253 days, base `2019-12-31`), `y2022` (251 days, base `2021-12-31`). All include their first trading day's return properly via `rig2.cut`.

5. **Statistics and thresholds (MEASURED, Probes 5 and 6):**
   - Thresholds are read live from `config/thresholds.yaml` (`backtest_max_pbo = 0.25`, `backtest_min_breakeven_cost_multiple = 2`, `replay_max_drop_ratio_vs_hold = 0.6`, `replay_min_deflated_sharpe = 0.95`, `replay_min_shuffle_percentile = 0.95`).
   - `N_TRIALS = 44`, `S = 16` equal blocks (`26,000` rows used, `14` earliest rows dropped, `0` zero-variance cases, `tie_share = 0.0`).
   - Shuffles (Probe 6, 20 draws at 5 bps): trade counts and average weights closely match the real rules across all 8 rules (e.g., `T1`: real 151 sides / 0.7197 wt vs shuffle 151.0 / 0.7197; `T4`: 4,730 / 0.6721 vs 4,731.5 / 0.6721; `V1`: 1,338 / 0.7818 vs 1,358.0 / 0.7825; `I1`: 702 / 0.6909 vs 703.9 / 0.6951; `I2`: 570 / 0.7197 vs 571.7 / 0.7197).

6. **Data handling (MEASURED, Probe 1):**
   - `F-F_Research_Data_Factors_daily__main.csv` and `12_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv` have 26,338 identical sorted unique trading dates (`1926-07-01` to `2026-09-30`), zero NaNs, zero `-99.99`/`-999` missing codes, and are converted from percent to decimal (`/ 100`). Market return is `(Mkt-RF + RF) / 100`. Max calendar gap is 12 days (`1933-03-15`, the March 1933 bank holiday).

---

## Independent Re-Computation of `HOLD` and `T1` (5 bps a side)

Computed directly from `/home/user/workspace/rig/stocks_free/french/clean/F-F_Research_Data_Factors_daily__main.csv` in `audit/replay_05_probes.py` (Probe 7) without calling any function from `run_05.py` or `rig2.py`.

Maximum absolute difference in daily equity across all 26,014 trading days (`1927-08-01` to `2026-09-30`):
- `HOLD`: `0.000e+00`
- `T1`: `0.000e+00`

| Slice | Rule | Independent CAGR | `run_05` CAGR | Independent Sharpe (above bills) | `run_05` Sharpe | Independent Max Drop | `run_05` Max Drop | Max Diff |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `dev` (`1927-08-01` to `2006-05-31`) | `HOLD` | +9.2546% | +9.2546% | 0.416112 | 0.416112 | -84.0740% | -84.0740% | 0.00e+00 |
| `dev` (`1927-08-01` to `2006-05-31`) | `T1` | +8.8634% | +8.8634% | 0.493129 | 0.493129 | -47.5907% | -47.5907% | 0.00e+00 |
| `held` (`2006-06-01` to `2026-06-30`) | `HOLD` | +11.4525% | +11.4525% | 0.564203 | 0.564203 | -54.5655% | -54.5655% | 0.00e+00 |
| `held` (`2006-06-01` to `2026-06-30`) | `T1` | +9.1180% | +9.1180% | 0.610801 | 0.610801 | -21.9431% | -21.9431% | 0.00e+00 |
