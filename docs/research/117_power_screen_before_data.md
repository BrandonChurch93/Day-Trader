# Can the available history answer the question?

STATED. Count dated events, find a defensible edge after costs for the exact holding window, and estimate the noise of the paired difference before asking for prices. Count independent turns: 500 names moving together in one January do not make 500 Januaries. Use these estimates to decide whether building the roster and replay is worth doing.

## A quick screen

STATED. For a one-sided paired t mark of 2, the quick approximation is **events × (net edge ÷ per-event paired noise)² ≈ 4 for 50% power, and ≈ 8 for 80%**. These are large-sample planning numbers, not a release gate. Use the effective count after month/year, issuer and overlapping-window dependence; refusals and additional marks can reduce power further. Net edge means the trade minus the same-clock alternative after both legs' costs. Paired noise means the standard deviation of that difference, not the stock's volatility by itself.

| Independent observations, approximate | Net edge | Paired noise | 50% power | 80% power |
|---|---:|---:|---:|---:|
| Stock events | 1% | 12% | 576 (about 580) | 1,152 |
| Stock events | 2% | 12% | 144 (about 145) | 288 |
| Ten yearly turns, solving for edge | To find | One year's sleeve noise | 0.63× yearly noise | 0.89× yearly noise |

STATED. Ten yearly turns need an edge on the scale of the sleeve's own yearly noise, not a few basis points against several percentage points of noise. Start from the approximation, then simulate the actual dates, realistic common shocks and costs, the prechosen comparison and every proposed mark. Simulate both no edge and a shared rally. Do not reuse quiet-sleeve breadth marks for noisy stocks, or use hundreds of raw tickers to hide clustering.

## What has already closed this way

The figures below are **MEASURED on synthetic worlds**, not trading results. The planted effects are assumptions unless a closure identifies a published historical anchor. The rules and noise are not the same across rows.

| Idea | History or docket screened | MEASURED on synthetic worlds |
|---|---|---|
| [Plan 51: hot-five momentum regime](../../research_rig/CLOSE_51_on_power.md) | Six full annual panels and partial 2026, not a ten-year simulation | At ±20 bp/day in 40-day blocks, 0/100 original and 1/100 after the uniform-placement redesign |
| [Plan 54: November small-cap loser rebound](../../research_rig/CLOSE_54_on_power.md) | Ten annual turns | Central strict power 2.32% at +1% gross and 7.87% at +2%; original paired-only grid 32.27% at +2% |
| [Plan 55: post-spin-off rebound](../../research_rig/CLOSE_55_on_power.md) | 100 dated distributions, documented lower bound | Central 32.86% at +2.11% gross and 19.27% with stressed costs; hypothetical 200 events 49.86% central |
| [Plan 56: officer/director purchase clusters](../../research_rig/CLOSE_56_on_power.md) | 2,391 filing candidates, with issuer and month dependence | Central 9.20% at +53 bp net over 20 sessions; 4.60% at +12.25 bp net over ten sessions |
| [Row 91: January preferred-share losers](../../research_rig/CLOSE_ROWS_91_92_on_power.md) | Ten annual turns | Central 13.69% at +2% gross under full marks; first 50% grid point +4.00% gross |
| [Row 92: January BDC losers](../../research_rig/CLOSE_ROWS_91_92_on_power.md) | Ten annual turns | Central 10.77% at +2% gross under full marks; first 50% grid point +5.25% gross |

UNKNOWN. These closures mean “cannot be settled with the history we can lawfully get” at the supported effect, assumed noise and proposed design, not “the idea loses.” A better-matched independent study, more eligible history, or less noisy paired design can justify revisiting the screen without opening prices first.
