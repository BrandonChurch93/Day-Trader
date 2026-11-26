# Replay 65. Stock-bond rebalancing

## The rule

- STATED, from the [frozen plan](../../research_rig/PREREG_65_stock_bond_rebalance_spread.md). The source is Harvey, Mazzoleni and Melone, [NBER working paper w33554](https://www.nber.org/system/files/working_papers/w33554/w33554.pdf). The paper claims that portfolios rebalancing back to 60% stocks push prices around, and that a rule trading against that flow had a yearly Sharpe of 1.11 before costs and stayed about 1 after costs, on stock and 10-year note futures.
- STATED. What we traded: long or short SPY against IEF, one weight a day. The weight is set at the close from a signal read on the 15-minute bar that starts 30 minutes before the close, and held to the next close. It averages a Threshold signal (26 bands from 0.0% to 2.5%, scaled by 1.5%) and a Calendar signal active in the last 5 sessions of each month and its first session. Nothing was fitted on our data.
- STATED. Costs: on each change in weight, per leg, the greater of 2 bp or $0.01 a share. Borrow on the short leg: SPY 0.50% a year, IEF 0.60% a year. Scored 2016-01-04 to 2026-11-25, judged after a burn-in of 126 sessions.
- MEASURED. The average size of the weight was 26.8% of capital.

## Did it pass?

MEASURED. Did not pass, **3 of 5 frozen marks**, in the one scored run, started 2026-11-26 11:36:49 UTC. The mean net return was +1.01 bp a session over 2,614 sessions, with a week-clustered t of 1.04 against a bar of 2. After dropping the best 27 sessions the mean was -1.76 bp. The net yearly Sharpe was 0.35. Sessions, money and year breadth were met; evidence and trim were not.

## Frozen marks

MEASURED. All five were required. Returns are net of costs and borrow, per unit of capital, in basis points a session. Before costs and borrow the mean was +1.74 bp (yearly Sharpe 0.61).

| Mark | Frozen bar | Measured | Verdict |
| --- | --- | --- | --- |
| Judged sessions | At least 2,400 | 2,614 | met |
| Money | Mean net return a session above zero | +1.01 bp | met |
| Evidence | t at least 2, clustered by calendar week of the exit session | 1.04 | not met |
| Trim | Mean above zero after dropping the best 1% of sessions, rounded up | -1.76 bp; dropped 27 | not met |
| Year breadth | At least 7 of the 11 years 2016 to 2026 with a positive mean | 7 of 11 | met |

## By year

MEASURED. Mean net return a session by calendar year of the exit session. 2026 runs to 2026-11-25. Positive in 7 of 11.

| Year | Mean net a session |
| --- | --- |
| 2016 | -0.79 bp |
| 2017 | -0.63 bp |
| 2018 | +0.42 bp |
| 2019 | -1.46 bp |
| 2020 | +8.09 bp |
| 2021 | +1.30 bp |
| 2022 | +2.24 bp |
| 2023 | +1.29 bp |
| 2024 | +0.70 bp |
| 2025 | +0.58 bp |
| 2026 (to 11-25) | -1.80 bp |

## Shown only

MEASURED. Each line below was named in the plan as shown only. None of them can count toward a mark.

- TLT in place of IEF, same weights, TLT returns, prices and borrow: +1.50 bp a session over 2,614 sessions, yearly Sharpe 0.41, t 1.26. Cannot count toward a mark.
- Threshold half only, its own costs: +0.98 bp a session over 2,614 sessions, yearly Sharpe 0.49, t 1.44. Cannot count toward a mark.
- Calendar half only, its own costs: -0.01 bp a session over 2,614 sessions, yearly Sharpe 0.00, t -0.01. Cannot count toward a mark.
- From 2023-04-01 on, outside the paper's printed sample: +0.04 bp a session over 917 sessions, yearly Sharpe 0.02, t 0.03. Cannot count toward a mark.
- Without March 2020: -0.07 bp a session over 2,592 sessions, yearly Sharpe -0.03, t -0.09. Cannot count toward a mark.
- Other reading of the Calendar first-day signal (start of the previous month's last-five window): +0.99 bp a session over 2,614 sessions, yearly Sharpe 0.35, t 1.02. Cannot count toward a mark.
- Lag-one clock: day t-1's full-close signal, held from close t to close t+1: -1.66 bp a session over 2,614 sessions, yearly Sharpe -0.55, t -1.48. Cannot count toward a mark.
- Full daily round trip: entry and exit cost on every judged session: -0.46 bp a session over 2,614 sessions, yearly Sharpe -0.16, t -0.47. Cannot count toward a mark.
- Cash account with SH (whole shares of IEF and SH, up to $500 each, only on sessions with a negative weight): -0.73 bp a session over 2,614 sessions, held on 1,989, yearly Sharpe -0.27. Cannot count toward a mark.

## Gaps

- STATED before any return. Most of the window is inside the paper's own sample, which runs 1997-09-10 to 2023-03-17, and the authors say they extended it through 2025 and found the results stronger. So only about 2026 has not been looked at by anyone, and only the months from April 2023 on lie outside the printed sample.
- STATED before any return. IEF stands in for the 10-year note future the paper uses. The future settles at 3:00 PM New York time and the ETFs close at 4:00 PM; IEF's duration differs.
- STATED before any return. The costs and borrow rates are ours. The paper gives no per-trade cost.
- UNKNOWN. Closing-auction fills, order cutoffs and the fill price. No realized spread is claimed.
- MEASURED. Coverage: 2,614 of 2,614 candidate sessions judged; 0 missing daily bars and 0 sessions without a signal bar.
- MEASURED on synthetic series before the run ([POWER_65.json](../../research_rig/POWER_65.json), 2,000 seeds a cell). Under the paper's skew of 5.23, the chance to pass all five marks was 60.9% to 65.6% at a true net Sharpe of 0.9 and 21.2% to 21.7% at 0.6.

## What it means

- STATED before the run. For a positive mean with t at least 1 but below 2, the fixed reading is **not shown, not refuted**. That is this result.
- MEASURED. The net yearly Sharpe was 0.35, against about 1 stated in the paper.
- MEASURED. Without March 2020 the mean was -0.07 bp, at or below zero. From 2023-04-01 on, the only months outside the paper's sample, it was +0.04 bp, about zero.
- MEASURED. The cash-account version a $500 account could hold lost money: -0.73 bp a session.
- STATED, ruling by the lead agent. No forward log is started, and the row closes.

## Independent recompute

- MEASURED. A second helper rebuilt the judged numbers with its own code, written from the plan text without reading the scorer. Its first numbers were fixed on disk at 2026-11-26 11:40:29 UTC, before it opened the scored result (SHA-256 `39aa8b0fccf19cece3c35d8199912510947313b757c147c103d3caacde431c08`).
- MEASURED. That first recompute did not agree in full. It gave a mean of +1.10 bp a session, t 1.20, a trimmed mean of -1.51 bp and 6 of 11 positive years, so it met 2 of 5 marks where the scored run met 3 of 5. Four marks and the verdict (did not pass) were the same; the year breadth mark differed.
- STATED by the helper, checked by the lead agent against the two scripts. The gap came from one line of the recompute's own code: it treated the last 4 sessions of each month as the Calendar window where the frozen plan says 5. The Threshold half matched in the first recompute; only the Calendar side differed.
- MEASURED. With that one line corrected, the second recompute (fixed at 2026-11-26 11:40:52 UTC, SHA-256 `455198866cfb0586438629c6039f6613a58300b4fdd27a186db1974c9dd18ac4`) agrees on all five marks, and its mean, t, trimmed mean and all 11 yearly means agree to within 1e-15.
- STATED. The correction was made after the helper had opened the scored result, so the second agreement is weaker evidence than a blind match would be. Both files are kept. The recompute did not cover the TLT, lag-one, full round trip, SH cash-account or other-reading shown lines; those rest on the scorer alone.

## Run record

- STATED by the lead agent. Scored exactly once, from 2026-11-26 11:36:49 UTC to 2026-11-26 11:36:52 UTC, exit 0. Ledger 208, queue 106.
- MEASURED. Freeze: `a6688cb7da016a182d38ceaedd773598047a4133`.
- MEASURED. Scoring approval: `baae6b533e729f1265d8cea936cf95d67f400ef8`.
- MEASURED. Inputs digest: `a95018d183acdc0b9598996a55ad564cf18bbf253f93d17d43f8f436c1cd3aae`.
- MEASURED. Saved aggregate result SHA-256: `5475bf58f123e68dc26069b2fbfe34a8074fe46a1ab6421aa6face52a5fa1d42`.
