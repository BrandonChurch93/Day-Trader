# 149: What the two US-reachable passes are worth on $500

Written 2026-11-26 by `research_rig/build_doc149_pass_sizing.py` from repo result pages, calibration files, practice cards, `AGENTS.md` and `config/thresholds.yaml` only. No raw price file was opened, no off-repo result file was read and no scorer was run. Every figure below is historical as measured on past dates or stated in a repo rule; nothing here is a forecast or advice to trade.

## Headline

- MEASURED, Replay 25 (TLT month-end, 1x, `docs/research/69_replay_25_treasury_month_end.md`): on $500 before taxes, the judged 2 bps/side mean of +0.2562% across 130 windows equals +3.07% (+$15.37) per 12-window year. Across the 10 full years (2016 to 2025) the simple annual sum ranged from +1.92% (+$9.59, 2023) to +7.31% (+$36.56, 2019), and partial 2026 (10 windows) was -5.50% (-$27.50).
- MEASURED, Measurement 34 (TMF 3x on the same month-end windows, `docs/research/82_measurement_34_tmf_ubt_month_end.md`): failed its frozen gross tracking mark (2.5853x vs 2.7x to 3.1x). At marked cost (fixed 2 bp + closing half-spread), the net mean was +0.6483% per window (+7.78% or +$38.90 per 12-window year simple), with compounded full-year returns from +1.49% (+$7.45, 2023) to +21.73% (+$108.65, 2019), partial 2026 at -15.85% (-$79.25), worst window -8.66% (-$43.30) and max drawdown 25.44% (-$127.20).
- MEASURED, Replay 48 (worst 5 muni CEFs in January, 1x, `docs/research/103_replay_48_muni_cef_january.md`): on a $500 sleeve once a year, before taxes, the mean net return across 10 turns (2016 to 2025) was +1.39% (+$6.96/year), ranging from -5.06% (-$25.29, turn 2021) to +8.00% (+$40.02, turn 2022).
- MEASURED, idle cash and overlap: Replay 25 sits idle about 86% of trading sessions and Replay 48 sits idle about 92% of trading sessions. Both want the same $500 during the last 3 sessions of January. The exact combined annual return on one $500 account is UNKNOWN on the repo because neither Replay 25 nor Measurement 34 prints individual monthly window returns.
- STATED, forward proof before real money: neither pass has any completed forward practice records yet. Practice card E01 (`practice/traders/E01_tlt_month_end_close.md`) requires at least 12 forward months (earliest after Tue 2027-11-30). Practice card E04 (`practice/traders/E04_muni_cef_january_watch.md`) sets no numeric turn count and says one turn proves nothing on its own (first forward exit Fri 2027-01-29).

## 1. Per trade: mean net, spread of outcomes, worst case seen, trades per year

Replay 25 (TLT, 1x, last 3 sessions of each month; source `docs/research/69_replay_25_treasury_month_end.md` and `docs/research/82_measurement_34_tmf_ubt_month_end.md`):

- MEASURED: passed 9 of 9 marks over 130 monthly windows (January 2016 through October 2026).
- MEASURED: mean net per trade at the judged 2 bps/side cost was +0.2562% (t = 2.36; trimmed without best 3 windows +0.1904%; post-2020 +0.1469%; gross mean +0.2963%). On $500 that is +$1.28 per trade before taxes.
- MEASURED: at higher shown costs, the per-trade mean fell to +0.1961% (t = 1.80) at 5 bps/side and +0.0959% (t = 0.88) at 10 bps/side.
- MEASURED (`docs/research/136_measured_stock_trading_costs.md`): TLT regular-hours median half-spread was 0.610 bp ($0.030 per $500 side) and last-30-minute median half-spread was 0.610 bp ($0.030 per $500 side). Exact closing-auction fill cost for TLT is UNKNOWN on doc 136.
- MEASURED: spread of annual per-window means across the 11 scored years ran from -0.5501% (2026, 10 windows) to +0.6093% (2019, 12 windows), with 10 of 11 positive.
- UNKNOWN: single-window standard deviation, single-window median, interquartile range and single worst TLT window are not printed on `docs/research/69_replay_25_treasury_month_end.md`, and Replay 25's saved results file is kept off the repo.
- STATED: 12 round-trip trades per full year (1 window per month, 3 held sessions per window).

Replay 48 (worst 5 muni closed-end funds, 1x, last December close to last January close; source `docs/research/103_replay_48_muni_cef_january.md`):

- MEASURED: passed 7 of 7 across 10 yearly turns (turns 2016 to 2025, exiting January 2017 to January 2026).
- MEASURED: mean net per trade (yearly turn) was +1.39% (+$6.96 on $500 before taxes), versus +0.09% for MUB (+$6.49 ahead) and +0.59% for the equal-weight roster (+$3.99 ahead; loser effect +0.80% with cash, +0.79% price only).
- MEASURED: spread of outcomes across the 10 printed yearly turns had sample standard deviation 3.90%, median +1.79%, positive in 8 of 10 and ahead of MUB in 8 of 10. Without the best year (turn 2022, +8.00%), the mean fell to +0.66%.
- MEASURED: worst case seen was -5.06% (-$25.29 on $500, turn 2021); second worst was -4.48% (turn 2017); best was +8.00% (+$40.02, turn 2022).
- MEASURED: trading costs (closing half-spread + 5 bp/side, with a 50 bp proxy on 23 of 100 held sides) cut 0.51 percentage points a year (zero-cost mean +1.90% vs judged +1.39%). Closed-end funds were not sampled in `docs/research/136_measured_stock_trading_costs.md`, so live CEF fill cost outside Replay 48's quote sample is UNKNOWN.
- STATED: 1 yearly turn per year (5 funds in $100 whole-share sleeves, 10 order sides per year).
- MEASURED, failed near copy (`docs/research/122_replay_53_taxable_fund_january_rebound.md`): Replay 53 (taxable CEFs on the same 10 turns, Pearson correlation +0.802 with Replay 48) did not pass (5 of 7). Its mean was +2.74% (+$13.68 on $500, worst -3.17% or -$15.86, best +12.38% or +$61.90), but it was positive in only 6 of 10 and ahead of PCEF in only 6 of 10.

| Pass | Cost basis | Mean net per trade | Spread of outcomes | Worst case seen | Trades per year |
|---|---|---|---|---|---|
| Replay 25 (TLT, 1x) | 2 bps/side (judged) | +0.2562% (+$1.28 on $500) | Single-window SD UNKNOWN; yearly means -0.5501% to +0.6093% | UNKNOWN on repo | 12 |
| Replay 48 (Muni CEFs, 1x) | Half-spread + 5 bps/side (judged) | +1.39% (+$6.96 on $500) | 10-turn SD 3.90%, median +1.79%, 8 of 10 positive | -5.06% (-$25.29, turn 2021) | 1 |
| Replay 53 (Taxable CEFs, failed copy) | Half-spread + 5 bps/side (judged) | +2.74% (+$13.68 on $500) | 6 of 10 positive, 6 of 10 ahead of PCEF | -3.17% (-$15.86, turn 2021) | 1 |

## 2. Per year on $500 at 1x (measured historical range, not a forecast)

Replay 25 (TLT, 1x, $500 deployed fresh each month, before taxes, 0% on idle cash; source `docs/research/69_replay_25_treasury_month_end.md`):

- MEASURED: across all 130 windows, 12 times the judged window mean is +3.07% (+$15.37 per 12-window year). Across the 10 full years (2016 to 2025), the average of the simple 12-window annual sums was +3.88% (+$19.40/year).
- MEASURED: across the 10 full scored years (2016 to 2025), the simple 12-window annual sum ranged from +1.92% (+$9.59, 2023) to +7.31% (+$36.56, 2019).
- MEASURED: including partial 2026 (10 windows, Jan to Oct), the lowest year row was -5.50% (-$27.50, 2026) and the highest was +7.31% (+$36.56, 2019).
- UNKNOWN: exact compounded annual TLT returns and whole-share rounding drag on $500 are not printed on `docs/research/69_replay_25_treasury_month_end.md`.

Replay 48 (worst 5 muni CEFs, 1x, $500 sleeve in $100 whole-share slots, before taxes; source `docs/research/103_replay_48_muni_cef_january.md`):

- MEASURED: mean net annual return was +1.39% (+$6.96/year on $500).
- MEASURED: across all 10 scored turns (2016 to 2025), annual returns ranged from -5.06% (-$25.29, turn 2021) to +8.00% (+$40.02, turn 2022).

| Pass (1x on $500) | Mean per year | Lowest full year | Highest full year | Worst scored year row (incl. 2026) | Basis |
|---|---|---|---|---|---|
| Replay 25 (TLT, 1x) | +3.07% (+$15.37) | +1.92% (+$9.59, 2023) | +7.31% (+$36.56, 2019) | -5.50% (-$27.50, 2026, 10 win) | Simple sum of printed yearly window means; compounded UNKNOWN |
| Replay 48 (Muni CEFs, 1x) | +1.39% (+$6.96) | -5.06% (-$25.29, turn 2021) | +8.00% (+$40.02, turn 2022) | -5.06% (-$25.29, turn 2021) | Direct $500 whole-share sleeve, before taxes |

## 3. With reachable leverage measured (TMF and UBT on the month-end window)

Measurement 34 (`docs/research/82_measurement_34_tmf_ubt_month_end.md`) ran on the exact same 130 windows as Replay 25. It measures vehicle tracking and quote cost on the same effect, not a second independent test.

TMF (3x long Treasury ETF):

- MEASURED: TMF failed its frozen gross tracking mark (2.5853x vs 2.7x to 3.1x; gross mean +0.7660% vs TLT gross +0.2963%). It passed its positive-net-mean mark at fixed 2 bp + closing half-spread (+0.6483%, t = 1.996, trimmed +0.4467%).
- MEASURED extra cost: TMF's closing-minute SIP half-spread averaged 3.652 bp at entry (median 2.876, p95 8.146, max 12.092) and 4.041 bp at exit (median 3.490, p95 9.770, max 14.327), or 7.69 bp round-trip in quote half-spread alone. Combined with 2 bp/side fixed cost, total drag was 11.77 bp/window versus 4.01 bp/window on TLT at 2 bp/side — an extra 7.76 bp/window ($0.39 per $500 round-trip).
- MEASURED on $500 per year (marked cost, before taxes): 12 times the window mean is +7.78% (+$38.90/year simple). Across the 10 full years (2016 to 2025), compounded annual returns averaged +9.88% (+$49.40) and ranged from +1.49% (+$7.45, 2023) to +21.73% (+$108.65, 2019). Across all 11 year rows including partial 2026 (10 windows, -15.85% or -$79.25), the mean compounded row was +7.54% (+$37.70). Positive mean years: 10 of 11.
- MEASURED worst window and drawdown: TMF's worst single window at marked cost was -8.66% (-$43.30 on $500, 2024-06-25 to 2024-06-28; -8.63% at fixed 2 bp). Peak-to-trough max drawdown on daily closes was 25.44% (-$127.20 on $500, 2025-08-28 to 2026-10-28).

UBT (2x long Treasury ETF, shown only, no pass/fail marks):

- MEASURED: UBT's closing-minute SIP half-spread averaged 10.186 bp at entry (p95 26.861, max 78.983) and 11.369 bp at exit (p95 27.246, max 122.278), or 21.55 bp round-trip in quote half-spread alone.
- MEASURED: at fixed 2 bp + half-spread, UBT's net mean fell to +0.2671% (t = 1.225, net ratio 1.04x TLT, 8 of 11 positive), with worst window -6.32% (-$31.60, 2024-06-25 to 2024-06-28), worst compounded year -14.12% (2026) and max drawdown 22.85%.

Leverage for Replay 48 (muni CEFs):

- UNKNOWN / not tested: no external leverage or margin test was run for Replay 48 (the desk cash account does not use margin, and the underlying muni CEFs already carry internal fund leverage).

| Vehicle (month-end) | Marked net mean / trade | Round-trip half-spread (mean) | Worst single window | Worst compounded year | Max drawdown |
|---|---|---|---|---|---|
| TLT (1x, Replay 25) | +0.2562% (2 bp/side) | 1.22 bp (doc 136 last-30m med x2; close UNKNOWN) | UNKNOWN on repo | UNKNOWN on repo (2026 simple -5.50%) | UNKNOWN on repo |
| TMF (3x, Meas. 34) | +0.6483% (2 bp + spread) | 7.69 bp (closing-min SIP) | -8.66% (-$43.30) | -15.85% (2026) | 25.44% (-$127.20) |
| UBT (2x, Meas. 34, shown) | +0.2671% (2 bp + spread) | 21.55 bp (closing-min SIP) | -6.32% (-$31.60) | -14.12% (2026) | 22.85% |

## 4. Idle time and both passes together by scored year

How much of the year the money sits idle:

- MEASURED, Replay 25 (TLT or TMF): held 3 sessions per month (36 sessions in a full year). Across 2016 to 2026 in `docs/research/69_replay_25_treasury_month_end.md`, 390 daily return intervals fell inside the window and 2332 fell outside — 14.3% invested and 85.7% idle.
- STATED, Replay 48 (muni CEFs): held from the last December close to the last January close (about 20 to 21 trading sessions out of ~252 per year, roughly 8% invested and 92% idle).
- STATED, overlap on one $500 account: Replay 48 holds across the last 3 sessions of January, which is also Replay 25's January month-end window. A single $500 cash account cannot put $500 into both during those 3 sessions without splitting capital or skipping January's Treasury window. Running Replay 48 in January and Replay 25 in the other 11 months (about 53 to 54 trading sessions per year) still leaves the cash idle about 79% of trading sessions.
- UNKNOWN: any cash-sweep interest earned during idle sessions (both replays assume 0% on idle cash).

What both passes together would have given in each scored year:

- UNKNOWN on the repo: the exact combined per-year return on one $500 account cannot be computed from repo files without opening raw data. Neither `docs/research/69_replay_25_treasury_month_end.md` nor `docs/research/82_measurement_34_tmf_ubt_month_end.md` prints individual monthly returns (so the overlapping January Treasury window cannot be removed), and `docs/research/69_replay_25_treasury_month_end.md` does not print compounded annual TLT returns. Per the repo-only rule, no combined year total is computed below.
- MEASURED, side-by-side per-year figures that are printed on the repo (aligned by exit calendar year: Replay 48 turn Y enters at the end of December Y and exits at the end of January Y+1):

| Exit year | Month-end windows | Replay 25 TLT 1x simple sum (2 bp/side) | Meas. 34 TMF 3x compounded (marked) | Replay 48 Muni CEFs 1x (exiting Jan) | Combined on $500 |
|---|---|---|---|---|---|
| 2016 | 12 | +5.31% (+$26.54) | +14.17% (+$70.85) | none (first turn entered Dec 2016) | UNKNOWN |
| 2017 | 12 | +2.54% (+$12.71) | +5.70% (+$28.50) | +0.62% (+$3.10, turn 2016) | UNKNOWN |
| 2018 | 12 | +6.09% (+$30.47) | +18.58% (+$92.90) | -4.48% (-$22.40, turn 2017) | UNKNOWN |
| 2019 | 12 | +7.31% (+$36.56) | +21.73% (+$108.65) | +4.91% (+$24.55, turn 2018) | UNKNOWN |
| 2020 | 12 | +2.21% (+$11.06) | +5.38% (+$26.90) | +1.45% (+$7.25, turn 2019) | UNKNOWN |
| 2021 | 12 | +3.34% (+$16.72) | +8.72% (+$43.60) | +2.12% (+$10.60, turn 2020) | UNKNOWN |
| 2022 | 12 | +1.98% (+$9.91) | +2.05% (+$10.25) | -5.06% (-$25.30, turn 2021) | UNKNOWN |
| 2023 | 12 | +1.92% (+$9.59) | +1.49% (+$7.45) | +8.00% (+$40.00, turn 2022) | UNKNOWN |
| 2024 | 12 | +4.56% (+$22.81) | +12.22% (+$61.10) | +1.01% (+$5.05, turn 2023) | UNKNOWN |
| 2025 | 12 | +3.53% (+$17.65) | +8.75% (+$43.75) | +2.56% (+$12.80, turn 2024) | UNKNOWN |
| 2026 | 10 | -5.50% (-$27.50) | -15.85% (-$79.25) | +2.77% (+$13.85, turn 2025) | UNKNOWN |

## 5. Forward months needed before real money, and the dates

Project rules (`AGENTS.md` and `config/thresholds.yaml`):

- STATED (`AGENTS.md`): what survives past tests trades pretend money on the practice desk, and the practice desk is the judge. Real money moves in stages set by the owner: now pretend accounts only; next a first small test amount ($300 or $500, keys such as `live_starting_capital_usd` are marked `open` in `config/thresholds.yaml`); later stricter sizing once matured. `AGENTS.md` does not set a fixed numeric forward-month count before the owner's first $300 to $500 test money.
- STATED (`config/thresholds.yaml`, builder thresholds for general practice-desk rules): see `paper_min_trading_days`, `paper_min_closed_trades`, `live_tracks_paper_months` and `scale_live_evidence_months` (per `config/thresholds.yaml`, documents name the keys rather than repeating their values).

Each card's current count and dates (as of 2026-11-26):

- MEASURED, E01 (`practice/traders/E01_tlt_month_end_close.md`, Replay 25 forward log): 0 forward months completed (`docs/research/140_false_pass_audit.md` notes no E01 forward log exists yet). E01 states judgment is not before 12 forward months. First window is 2026-12 (entry Mon 2026-12-28, exit Thu 2026-12-31); the 12th forward month finishes at the exit of 2027-11 (Tue 2027-11-30), and the pinned 13-month schedule ends Fri 2027-12-31. Remaining forward months by E01's rule: 12. (Applying `paper_min_closed_trades` literally at 12 trades/year would take over 8 years.)
- MEASURED, E04 (`practice/traders/E04_muni_cef_january_watch.md`, Replay 48 forward watch): 0 forward turns completed. Next turn dates: roster freeze December 10, 2026, formation Wed 2026-12-30, pretend entry Thu 2026-12-31, shown-only fifth-session exit Fri 2027-01-08, judged exit Fri 2027-01-29. E04 states one turn proves nothing on its own and sets no numeric turn count before real money (remaining months before real money is UNKNOWN / owner decision; at 1 turn per year, even 3 to 5 forward turns would run to January 2029 to January 2031).
- MEASURED, E08 (`practice/traders/E08_taxable_cef_fifth_session_exit.md`, Replay 53 shown-only lead, not a pass): 0 forward turns completed. Next turn dates: pretend entry Thu 2026-12-31, claim exit Fri 2027-01-08, reference exit Fri 2027-01-29. E08's own power math states beating PCEF at the shown spread needs 11 forward years for 50% power and 21 forward years for 80% power (42 and 83 years if the true edge is half the shown mean), so E08 cannot clear the screen on its own.

## 6. What could make each stop working

Shared risks across both passes:

- MEASURED (`docs/research/140_false_pass_audit.md`): across 34 trading tests that could give a counted pass, a no-edge world predicts 0.36 to 2.09 passes by luck alone, giving a 0.49% to 34.92% chance of seeing 3 or more passes by luck. One or both passes could be chance.
- STATED (`docs/research/136_measured_stock_trading_costs.md`): exact closing-auction fills are UNKNOWN in our spread measurement. Live slippage or wider spreads can erase thin edges.
- STATED: both rules rest on published academic calendar effects (Hartley and Schwarz for Treasury month-end; Starks, Yong and Zheng plus Carrion and Zhang for closed-end fund tax-loss selling). Crowding or broker/fund flow shifts can shrink them.
- STATED: every return above is before taxes. Short-term gains and taxable distributions on a US taxable account cut realized dollars (exact tax drag is UNKNOWN here).

Specific risks for Replay 25 (TLT / TMF month-end):

- MEASURED: it already lost money in partial 2026 (10 windows): -0.5501% per window in TLT (-5.50% simple) and -15.85% compounded in TMF at marked cost, with a 25.44% peak-to-trough TMF drawdown.
- MEASURED: cost sensitivity is tight. TLT's t-statistic drops to 1.80 (below 2.0) at 5 bps/side, and TMF's marked t-statistic (1.996) already sits right on 2.0 while failing its 2.7x to 3.1x gross tracking mark (2.5853x).
- MEASURED (`docs/research/140_false_pass_audit.md`): Replay 25's nominal no-edge rate was 0.50% to 2.28% (NOMINAL); 5 of 6 scored month-end and bond-flow tests in the same family failed; 2016 to 2018 overlapped Hartley and Schwarz's published sample; and the 2002 to 2015 check (Replay 26) was blocked before scoring.
- STATED: changes in Treasury auction schedules, bond-index rebalancing, dealer balance-sheet capacity, or sustained high rate volatility (which increases daily-reset drag in TMF) could weaken or invert the window.

Specific risks for Replay 48 (muni CEFs in January):

- MEASURED (`research_rig/CALIBRATION_48.json` and `docs/research/140_false_pass_audit.md`): only 10 yearly turns exist, the pass sits right on the 8 of 10 positive-year bar (one more losing January would have failed), the no-edge pass rate was 4.39% point, 4.74% upper 95% (MEASURED), and a synthetic muni-wide rally with zero loser effect passed 20.65% of the time.
- MEASURED (`docs/research/122_replay_53_taxable_fund_january_rebound.md`): the closest sibling test (Replay 53, taxable CEFs, correlation +0.802) failed (5 of 7, positive in only 6 of 10).
- MEASURED (`docs/research/103_replay_48_muni_cef_january.md`): thinly traded muni CEFs have real execution and data gaps — 23 of 100 held sides lacked full closing-quote cover (50 bp proxy), 16 of 50 held fund-turns had undocumented cash, and the eligible muni CEF pool shrank over the decade (from 137 eligible in turn 2017 to 91 in turn 2025).
- STATED: January municipal bond selloffs (like turns 2017 at -4.48% and 2021 at -5.06%), fund mergers, tender offers or shifts in retail tax-loss selling timing could wipe out multiple years of average gains in one month.
