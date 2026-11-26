# Plan 65: stock-bond rebalancing spread, the paper's own rule

Status: DRAFT. Written 2026-11-26 11:15 UTC. Not frozen. No bar has been opened and no return computed by anyone for this plan.

Queue 106, ledger 208, from [idea round 34](../docs/129_idea_round_34.md). Source: Harvey, Mazzoleni and Melone, "The Unintended Consequences of Rebalancing", NBER working paper w33554, March 2025, revised January 2026 ([PDF](https://www.nber.org/system/files/working_papers/w33554/w33554.pdf)). Page numbers are the printed page numbers of that revision. Settings live in `replay_65_plan`. Code: `research_rig/score_65.py`, tests `research_rig/test_65.py`, power `research_rig/power_65.py`.

## Weaknesses, written before any return

- Most of the window is inside the paper's own sample. The paper's sample runs 1997-09-10 to 2023-03-17 (Table 1, p.17). Footnote 32 (p.35) says the authors extended it through 2025 and found the results "even stronger". So only about 2026 has not been looked at by anyone. A pass mostly re-checks their result on ETFs after costs. A miss means more, because the effect is supposed to be there in-sample.
- The Calendar half overlaps what this project already saw about month-end. Replay 25 (long TLT over the last 3 sessions of the month, 2016 to 2026) passed. Replay 41 (month-end SPY against TLT switch) did not pass, but it showed always-TLT on that clock was positive. Replay 33 (IEF and TLT on auction afternoons) did not pass. None of them computed any rebalancing-signal return. The Threshold half is new to this project. It is not new to the paper's authors.
- IEF stands in for the 10-year note future. The paper uses Bloomberg continuous ES and TY futures (Appendix A, p.52). The 10-year future settles at 3:00 PM New York time, and the ETFs close at 4:00 PM. IEF holds 7 to 10 year cash Treasuries, so its duration differs from TY's.
- No per-trade cost is sourced from the paper. It says only that the Sharpe ratio net of costs, "following the conservative assumptions of Harvey et al. (2018)", stays close to 1 (p.39). Our costs are our own (below).
- The paper's settings were chosen by its authors on 1997 to 2023 data, which overlaps our window: the δ range (Figure 2), week4, and the 1.5% scale. We copy them as printed and fit nothing. That does not make them out of sample.
- The start state is arbitrary. Every simulated portfolio starts at 60% on 2016-01-04. Until a portfolio's first reset, its weight depends on that arbitrary start. Calendar resets at the end of January 2016. A Threshold portfolio with a wide band may not reset for months. The 126-session burn-in (`replay_65_plan` key `burn_in_sessions`) shortens this but does not remove it.

## What the paper states (STATED)

- Weight drift (p.10; Appendix B, p.53): w(t+1) = w(t)(1+R_SP) / [w(t)(1+R_SP) + (1 − w(t))(1+R_10Y)]. Target 60% (key `target`).
- Threshold portfolio (B.1, p.53): reset to 60% when the weight exceeds the target by δ. The printed condition is one-sided. The lead ruled it two-sided, |w − 60%| ≥ δ, with the reset at the breach day's close. The signal is the drifted weight minus 60%.
- Threshold Signal (eq. 2, p.12): equal average over δ from 0% to 2.5% in steps of 0.1%, 26 portfolios (keys `delta_min`, `delta_max`, `delta_step`).
- Calendar portfolio (B.2, p.53): reset on the last business day of each month. The signal is the drifted weight minus 60%.
- Trading rule (section 4, p.37 to 38): w = average of (−Threshold Signal / 1.5%) and a modified Calendar signal (key `threshold_scale`). The modified Calendar is sign(−Calendar) in the last week of the month (last 5 sessions, key `week4_sessions`; the paper's Dummy5Days, p.14). On the first business day of a new month it is sign(Calendar Signal at −4) (key `reversal_lag`). Otherwise it is 0. Return = w × (R_SP − R_10Y).
- The paper states no cap on w. A text search of the paper for cap, clip, truncate, winsorize and bounded found none in this rule, so no clip is used.
- Reported results (Table 6, p.38 to 39): Sharpe 1.11 gross, skew 5.23, 0.90 without September 2008 to March 2009 and March 2020. One-standard-deviation slopes in Table 3 (p.32 to 33) are equity +15.9 / +16.9 bp and bond −4.1 / −2.3 bp next day (Threshold / Calendar), from a multivariate regression.
- Footnote 28 (p.31): using the 3:30 PM price instead of the close gives largely the same results. That analysis is untabulated and was supplied by an asset manager.

## Reading choices (confirmed by the lead)

- The paper's words (p.38): "Furthermore, on the first business day of a new month, the modified Calendar signal is set to sign(Calendar Signal−4) to capture potential reversal effects (see Figure 4)." The subscript −4 is not defined further. Judged reading, ruled by the lead: the Calendar signal at the close four sessions before the day it is applied (key `reversal_lag`), since a subscript lag in an equation normally counts from the current day. Other reading, shown only: the Calendar signal at the first session of the previous month's last-five window (day T−4 counted from that month's last session T, which is five sessions back).
- The signal on day t uses close states through t−1, then drifts each portfolio by the return from close t−1 to the signal-bar price on day t. Reset decisions in the state history use full closes only.
- In the Threshold and Calendar shown-only lines, each half keeps its 0.5 weight, so the two halves add up to w.

## Rule, clock and return

- Sessions: XNYS from `research_rig/calendar_65.json`, scored 2016-01-04 to 2026-11-25 (keys `first_session`, `last_session`).
- Calendar file: the committed Plan 50 calendar from 2016-01-04 on. Added from the published NYSE 2026 hours: 2026-11-25, 2026-11-27 (early close), 2026-11-30 and 2026-12-01.
- Sessions after 2026-11-25 are used only to place month ends, so the sample end is not taken as a month end. November 2026's last five sessions are 23, 24, 25, 27 and 30. The scorer refuses a calendar with no session in a later month.
- Inputs: daily SIP closes and cash actions for SPY and IEF. Total return on each session i is ratio × (close i + cash i) / close (i−1) − 1, with cash per post-split share on its ex-date.
- Signal bar: the 15-minute SIP bar that starts 30 minutes before the session's close (key `signal_bar_start_before_close_min`). That is 15:30 New York time on a normal day and 12:30 on an early-close day. Its close is the price used.
- Position: set at close t to w(t), held to close t+1. Judged from the 127th session, after a burn-in of 126. Judged return = w(t) × (R_SPY(t+1) − R_IEF(t+1)) − costs − borrow, per unit of capital.
- Missing data. A missing SPY or IEF daily bar on any session refuses the run, before the lock.
- A missing signal bar for either fund on day t makes the position flat for that session, and the session is not judged. The cost of going flat and of re-entering is charged to the next judged session. If no judged session follows, it is charged to the last judged one.
- Input shape checks refuse:
- a duplicate JSON key;
- a non-numeric or Boolean price;
- a bar whose low or high does not bound its open and close;
- negative volume;
- a 15-minute stamp off the quarter-hour grid;
- a daily stamp that is not midnight New York for its session (04:00Z or 05:00Z by daylight time), or two daily bars for one session;
- a daily bar off the calendar;
- a split ratio of 1;
- two action rows for one symbol, type and ex-date (custody merges same-day cash into one row);
- an action ex-date inside the span that is not a session.
- Costs: per leg, on the change in weight at each close, the greater of 2 bp of traded notional (key `cost_bps`) or one cent a share (key `cost_cent`) at that close's price. The final position is closed at the last close.
- Borrow: charged on the short leg by calendar days held (key `borrow_annual`).
- SPY: 0.50% a year. Posted IBKR-sourced rates were 0.25% to 0.52% in 2026 ([Fintel](https://fintel.io/ss/us/spy), [ChartExchange](https://chartexchange.com/symbol/nyse-spy/borrow-fee/), [IBorrowDesk](https://www.iborrowdesk.com/report/SPY)).
- IEF: 0.60% a year. Posted rates were 0.25% to 0.53% from December 2025 to November 2026 ([Fintel](https://fintel.io/ss/us/ief), [ChartExchange](https://chartexchange.com/symbol/nasdaq-ief/borrow-fee/), [companiesmarketcap](https://companiesmarketcap.com/ishares-7-10-year-treasury-bond-etf/cost-to-borrow/)).
- TLT (shown only): 0.60% a year, ASSUMED equal to IEF and not separately sourced.
- [Alpaca](https://docs.alpaca.markets/us/docs/margin-and-short-selling) charges $0 on easy-to-borrow names. The figures above are conservative on purpose.
- Cash on the short leg is paid through the total return. No interest is earned or paid on capital.
- STATED: a live version would use market-on-close orders after a 15:45 calculation. Closing-auction fills, order cutoffs and the fill price are UNKNOWN. No realized spread is claimed.

## Five frozen marks, all required

| Mark | Bar |
| --- | --- |
| Judged sessions | At least 2,400 (key `replay_65_plan`, `marks.min_sessions`) |
| Money | Mean net daily return above zero |
| Evidence | t at least 2 on the net daily series, clustered by ISO calendar week of the exit session. Finite-group variance: G/(G−1) times the sum of squared week sums of de-meaned returns, divided by N squared. An undefined t does not meet the mark. |
| Trim | Mean above zero after dropping the best 1% of sessions, drop count rounded up |
| Year breadth | At least 7 of the 11 calendar years 2016 to 2026 with a positive mean by exit session. An empty year is not positive. |

STATED pre-return reading, in the Plan 61 style:

- A pass is evidence, not proof of future performance. Because most of the window is in the paper's sample, a pass says the paper's rule survives ETFs and our costs. It does not say the rule works out of sample.
- A miss is weak evidence against the rule at the Sharpe levels where the power block below shows a pass is unlikely.
- If the mean is positive and t is at least 1 but below 2, write **not shown, not refuted**. Only a forward pretend-money log may be considered.
- If t is below 1 or the mean is at or below zero, close the row.
- For any other miss, including an undefined t or a t of at least 2 with another mark unmet, report that it did not pass, with no automatic forward approval.

## Shown only, cannot count

- TLT in place of IEF: same weights, TLT returns, prices and borrow.
- The Threshold half and the modified Calendar half, each with its own costs.
- April 2023 onward (key `post_paper_from`), outside the paper's printed sample.
- Without March 2020 (key `stress_exclude_months`). The paper's 2008 to 2009 window is before our data.
- First-day reversal with the other reading of "Calendar Signal−4": the signal at the start of the previous month's last-five window.
- Lag-one clock: the full-close signal of day t−1, held from close t to close t+1.
- Full daily round trip: entry and exit cost on every judged session.
- Cash account with SH. On sessions with w < 0, hold whole shares of IEF and SH, each up to USD 500 (key `sh_leg_usd`). On other sessions hold nothing. Costs are on the change in shares, and any holding is sold at the last close. A split on either fund sets that session flat at no cost. P&L is shown per USD 1,000. One SPY share costs more than USD 500, so the long-stock side is not shown.

## Pre-freeze power

The script is `research_rig/power_65.py`. It uses no market data, only the calendar for week and year labels. The true net Sharpe is set and the daily sd is 1; the marks do not depend on scale.

The noise shapes:

- Normal: normal days.
- Student t: t with 4 degrees of freedom.
- Skew mix: on 1% of days the return is a positive exponential jump, and on the rest it is normal. The parameters are solved so the series has the set Sharpe and the paper's skew of 5.23.
- Skew mix in runs: the same, with jumps in runs of 5 sessions, like crisis weeks.
- Soft mix: jumps carry 30% of the mean.

<!-- power_65 start -->
MEASURED from `POWER_65.json` (synthetic, no market data). 2614 judged sessions, 543 week clusters, 2000 seeds a cell, jump share of days 0.01. Each cell is the share of runs that meet all five marks. The even-chance column is the lowest net Sharpe on a 0.05 grid from 0.30 at which at least half the runs pass.

| Noise shape | Net Sharpe 0.9 | 0.6 | 0.45 | 0.3 | Even chance needs net Sharpe |
| --- | ---: | ---: | ---: | ---: | ---: |
| Normal | 79.5% | 46.6% | 28.1% | 15.2% | 0.65 |
| Student t, 4 df | 81.0% | 45.8% | 27.0% | 13.5% | 0.65 |
| Skew mix 5.23, jumps spread out | 65.6% | 21.2% | 8.1% | 2.8% | 0.80 |
| Skew mix 5.23, jumps in 5-session runs | 60.9% | 21.7% | 9.3% | 3.6% | 0.85 |
| Soft mix, jumps carry 30% of the mean | 81.5% | 48.4% | 29.8% | 15.2% | 0.65 |

In the skew mix the jump days carry this share of the true mean: 79% at Sharpe 0.9, 118% at Sharpe 0.6, 158% at Sharpe 0.45, 236% at Sharpe 0.3. Above 100% means the other days lose on average. The soft mix has skew 0.24, 0.05, 0.01, -0.01 at the same four Sharpe levels.

In plain words: under the paper's own skew the chance to pass all five marks is about 61% to 66% at a true net Sharpe of 0.9 and about 21% to 22% at 0.6.

Close rule, fixed before bars: if an even chance needs a net Sharpe above 0.9, the row closes. Worst shape here needs 0.85, so the row stays open.
<!-- power_65 end -->

## Data request (custodian only; the author never opens it)

- Directory: `/home/user/workspace/rig/data/plan65_inputs`, mode 0700, holding exactly seven mode 0600 files.
- `SPY_15m.json`, `IEF_15m.json`: Alpaca SIP 15-minute bars, `adjustment=raw`, 2016-01-01 to 2026-11-25. Ordered arrays of objects with exactly `t`, `o`, `h`, `l`, `c`, `v`. `t` is the bar start in UTC, form `YYYY-MM-DDTHH:MM:00Z`. Regular-hours bars are enough.
- `SPY_1d.json`, `IEF_1d.json`, `TLT_1d.json`, `SH_1d.json`: Alpaca SIP daily bars, `adjustment=raw`, same fields and span. `t` is midnight New York in UTC (04:00Z or 05:00Z).
- `actions.json`: an array of objects for the four symbols. Each is `{"symbol", "type": "cash", "ex_date", "amount"}` with cash per share as of the ex-date, or `{"symbol", "type": "split", "ex_date", "ratio"}` with new shares per old share. The span is the same. Give one row per symbol, type and ex-date; merge two cash amounts on one day into one row.

## Custody and one-run protocol

- `python3 research_rig/score_65.py --synthetic` runs the whole rule on seeded fake bars. `python3 research_rig/test_65.py` runs the tests.
- `--validate-inputs` checks modes, names and formats. It prints the judged-session count, missing daily bars per fund, missing signal bars, and the inputs digest. It computes no return and no signal, and writes nothing.
- The freeze commit carries this plan marked `Status: FROZEN`, `research_rig/PINNED_65.json` (SHA-256 of the plan, scorer, tests, calendar, power script, power output and the `replay_65_plan` block) and ledger row 208.
- The lead runs `--validate-inputs` once. The lead then makes one commit whose single parent is the freeze commit and which adds only `research_rig/APPROVAL_65.md`. The whole file must be exactly this one line and its newline: `Approved by the lead: plan 65 ledger 208, one scored run, freeze commit <40 hex>, inputs SHA-256 <64 hex>.`
- `--go --approval-commit <c>` refuses unless:
- HEAD is that commit and has no tracked change.
- The pins match on disk and in git.
- The inputs match the named digest.
- `/home/user/workspace/rig/data/replay_65` exists, is empty, has mode 0700 and is owned by the user running the scorer. The inputs directory and its files must also be owned by that user.
- Every data refusal runs before the lock.
- When those checks pass, it takes the one-shot lock, scores, and writes `results_65.json`. No PLAN65_ or P65_ environment variable is allowed.
