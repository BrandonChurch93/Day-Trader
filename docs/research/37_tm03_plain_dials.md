# Time machine plan TM03: plain fixed dials against the AI models

Made by `timemachine/dial_rules_tm03.py --write` from `timemachine/dial_rules_tm03.json` and `timemachine/results_tm03.json`. Do not edit by hand. Pretend money.

MEASURED. Models with all 8 months in at the time this page was written: 5 of 6 (Claude Opus 5.5, GPT-6.2 Sol, Gemini Neon, Claude Sonnet 5.5, Grok 4.7). Still incomplete and left out until all 8 months finish: Kimi K3 (4 of 8).

## What was asked

- STATED. In plan TM03 (`docs/research/34_time_machine_tm03_bitcoin_dial.md`), several AI models ended ahead of holding bitcoin over the eight months from April to November 24, 2026, while none stood clear of their own answers in shuffled order (`shuffle_runs`).
- STATED. This check asks whether plain fixed rules, decided only from daily closes before each wake and run through the exact same weights book code (`timemachine/weights.py`), land in the same place.

## How the first wake of each month works

- STATED. Each month in `tm03_plan.months` starts as a fresh `tm_account_start_usd` cash account with opening target `tm03_plan.opening_weight` (fully invested in BTC/USD).
- STATED. Both the AI models and the fixed dials are asked for a target share at the first wake of each month (`tm03_plan.wake_hour_utc` on day 1), using only daily bars whose close finished at or before that wake.
- STATED. In `timemachine/weights.py` (`step_book`), the desk does not buy the opening target before the first wake's answer arrives. If a model or dial keeps the opening share of 1.0, the desk buys 1.0 at the open of the first recorded minute and pays spread (`tm_crypto_half_spread_bps`) plus fee (`practice_crypto_fee_bps_added`) on the full account.
- STATED. If a model or dial answers a lower share `w` at the first wake (for example 0.7 for Dial E or 0.0 for Dial B when bitcoin is already below its 20-day average), the desk replaces the opening target with `w` and buys only `w` directly from cash at that first minute open. It does not buy 1.0 and then sell `1 - w`. So opening below 1.0 at wake 0 costs spread and fee only on `w`, and costs $0.00 when `w` is 0.0.
- STATED. On every later wake in the month, the desk trades only when the new target differs from the standing target, skips changes smaller than `tm_weights_min_change` unless moving to 0.0, and lets the book drift between wakes.

## The dials, fixed before running

STATED. Batch 1 was fixed at the top of `timemachine/dial_rules_tm03.py` before running and was not changed after seeing results:

- Dial A: above 20d SMA -> 1.0, else 0.5.
- Dial B: above 20d SMA -> 1.0, else 0.0.
- Dial C: fraction of 10/20/50d SMAs below last close (0, 1/3, 2/3, 1).
- Dial D: 1.0, cut to 0.5 if 7d ret < -5%, back to 1.0 if 7d ret > 0%.
- Dial E: constant 0.7 (fixed lower share, no timing).
- Dial F-OPUS (hindsight): Claude Opus 5.5 month-average share held constant.
- Dial F-SOL (hindsight): GPT-6.2 Sol month-average share held constant.
- Dial F-NEON (hindsight): Gemini Neon month-average share held constant.
- Dial F-SONNET (hindsight): Claude Sonnet 5.5 month-average share held constant.
- Dial F-GROK (hindsight): Grok 4.7 month-average share held constant.

## Summed over all eight months

MEASURED, pretend money, April to November 24, 2026 (`tm03_plan.months`, November ending on `tm03_plan.last_day`). Fresh `tm_account_start_usd` account each month. Largest drop is the worst single-month drawdown across the eight months; average share is time-weighted across all eight months.

| Rule / Model | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Hold BTC/USD | -$64.31 | $0.00 | -$188.61 | -$190.48 | -$89.36 | -$202.66 | -$205.16 | -26.9% | 1.00 | $27.92 |
| Model OPUS (Claude Opus 5.5) | $124.30 | +$188.61 | $0.00 | -$1.87 | +$99.25 | -$14.05 | -$16.55 | -11.7% | 0.75 | $46.29 |
| Model SOL (GPT-6.2 Sol) | $126.17 | +$190.48 | +$1.87 | $0.00 | +$101.12 | -$12.18 | -$14.68 | -14.4% | 0.74 | $54.11 |
| Model NEON (Gemini Neon) | $25.05 | +$89.36 | -$99.25 | -$101.12 | $0.00 | -$113.30 | -$115.80 | -12.1% | 0.69 | $86.53 |
| Model SONNET (Claude Sonnet 5.5) | $138.35 | +$202.66 | +$14.05 | +$12.18 | +$113.30 | $0.00 | -$2.50 | -15.2% | 0.78 | $46.05 |
| Model GROK (Grok 4.7) | $140.85 | +$205.16 | +$16.55 | +$14.68 | +$115.80 | +$2.50 | $0.00 | -9.8% | 0.70 | $58.36 |
| Dial A | $33.88 | +$98.20 | -$90.42 | -$92.29 | +$8.83 | -$104.47 | -$106.97 | -16.5% | 0.73 | $59.09 |
| Dial B | $132.07 | +$196.38 | +$7.77 | +$5.90 | +$107.02 | -$6.28 | -$8.78 | -8.6% | 0.48 | $90.02 |
| Dial C | $132.51 | +$196.82 | +$8.21 | +$6.34 | +$107.46 | -$5.84 | -$8.34 | -7.4% | 0.51 | $85.90 |
| Dial D | $24.39 | +$88.70 | -$99.91 | -$101.78 | -$0.66 | -$113.96 | -$116.46 | -17.7% | 0.89 | $43.07 |
| Dial E | -$45.18 | +$19.14 | -$169.48 | -$171.35 | -$70.23 | -$183.53 | -$186.03 | -19.1% | 0.70 | $19.61 |
| Dial F-OPUS (hindsight) | $188.87 | +$253.18 | +$64.57 | +$62.70 | +$163.82 | +$50.52 | +$48.02 | -11.6% | 0.75 | $20.76 |
| Dial F-SOL (hindsight) | $205.88 | +$270.19 | +$81.58 | +$79.71 | +$180.83 | +$67.53 | +$65.03 | -9.7% | 0.74 | $20.42 |
| Dial F-NEON (hindsight) | $206.26 | +$270.57 | +$81.96 | +$80.09 | +$181.21 | +$67.91 | +$65.41 | -8.8% | 0.69 | $19.15 |
| Dial F-SONNET (hindsight) | $196.37 | +$260.68 | +$72.07 | +$70.20 | +$171.32 | +$58.02 | +$55.52 | -13.7% | 0.78 | $21.62 |
| Dial F-GROK (hindsight) | $255.58 | +$319.89 | +$131.28 | +$129.41 | +$230.53 | +$117.23 | +$114.73 | -8.6% | 0.70 | $19.28 |

## Month by month

MEASURED. Each table gives one dial's dollar gain, difference against hold and each complete model, largest drop, time-weighted average share, and costs paid.

### Dial A

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $108.12 | -$6.31 | -$6.31 | +$4.17 | +$25.11 | -$6.31 | +$12.54 | -4.2% | 0.92 | $3.49 |
| 2026-05 | -$5.15 | +$33.88 | -$5.50 | -$10.03 | +$10.15 | +$0.36 | -$3.51 | -7.4% | 0.74 | $5.30 |
| 2026-06 | -$128.69 | +$78.53 | -$20.80 | +$15.36 | -$12.96 | +$22.76 | -$30.86 | -12.9% | 0.51 | $8.28 |
| 2026-07 | $18.75 | -$51.07 | -$14.80 | -$44.09 | +$21.41 | -$38.35 | -$12.70 | -7.1% | 0.89 | $10.82 |
| 2026-08 | $208.78 | -$36.55 | -$32.83 | +$0.84 | -$11.52 | -$21.40 | -$17.81 | -3.2% | 0.79 | $10.45 |
| 2026-09 | $39.30 | -$20.60 | +$24.76 | +$15.47 | +$15.67 | -$15.25 | +$56.25 | -5.5% | 0.85 | $6.95 |
| 2026-10 | -$62.64 | +$13.78 | +$7.95 | -$1.60 | +$29.69 | -$1.75 | -$10.71 | -9.3% | 0.63 | $8.64 |
| 2026-11 | -$144.57 | +$86.53 | -$42.88 | -$72.39 | -$68.70 | -$44.51 | -$100.16 | -16.5% | 0.50 | $5.17 |

### Dial B

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $101.77 | -$12.66 | -$12.66 | -$2.18 | +$18.76 | -$12.66 | +$6.19 | -4.2% | 0.83 | $3.49 |
| 2026-05 | $28.72 | +$67.76 | +$28.37 | +$23.84 | +$44.02 | +$34.23 | +$30.36 | -4.2% | 0.48 | $7.10 |
| 2026-06 | -$47.43 | +$159.80 | +$60.46 | +$96.62 | +$68.30 | +$104.02 | +$50.40 | -4.7% | 0.07 | $13.68 |
| 2026-07 | -$31.32 | -$101.13 | -$64.87 | -$94.16 | -$28.66 | -$88.42 | -$62.77 | -8.6% | 0.77 | $17.63 |
| 2026-08 | $172.81 | -$72.52 | -$68.80 | -$35.13 | -$47.49 | -$57.37 | -$53.78 | -3.4% | 0.58 | $17.17 |
| 2026-09 | $18.70 | -$41.19 | +$4.16 | -$5.13 | -$4.93 | -$35.85 | +$35.65 | -4.0% | 0.70 | $10.42 |
| 2026-10 | -$49.21 | +$27.21 | +$21.38 | +$11.83 | +$43.12 | +$11.68 | +$2.72 | -7.8% | 0.26 | $13.75 |
| 2026-11 | -$61.98 | +$169.12 | +$39.71 | +$10.20 | +$13.89 | +$38.08 | -$17.57 | -6.2% | 0.04 | $6.78 |

### Dial C

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $97.54 | -$16.89 | -$16.89 | -$6.41 | +$14.53 | -$16.89 | +$1.96 | -4.2% | 0.81 | $7.27 |
| 2026-05 | -$14.18 | +$24.86 | -$14.53 | -$19.06 | +$1.12 | -$8.67 | -$12.54 | -7.4% | 0.57 | $14.05 |
| 2026-06 | -$21.79 | +$185.43 | +$86.10 | +$122.26 | +$93.94 | +$129.66 | +$76.04 | -3.4% | 0.10 | $6.90 |
| 2026-07 | -$40.73 | -$110.54 | -$74.28 | -$103.57 | -$38.07 | -$97.83 | -$72.18 | -7.1% | 0.67 | $16.16 |
| 2026-08 | $184.78 | -$60.56 | -$56.83 | -$23.16 | -$35.52 | -$45.40 | -$41.81 | -3.2% | 0.68 | $14.05 |
| 2026-09 | $12.98 | -$46.91 | -$1.56 | -$10.85 | -$10.65 | -$41.57 | +$29.93 | -5.0% | 0.74 | $11.49 |
| 2026-10 | -$44.62 | +$31.80 | +$25.97 | +$16.42 | +$47.71 | +$16.27 | +$7.31 | -6.9% | 0.41 | $11.44 |
| 2026-11 | -$41.47 | +$189.64 | +$60.22 | +$30.71 | +$34.40 | +$58.59 | +$2.94 | -4.1% | 0.03 | $4.54 |

### Dial D

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $114.43 | $0.00 | $0.00 | +$10.48 | +$31.42 | $0.00 | +$18.85 | -4.2% | 1.00 | $3.49 |
| 2026-05 | -$43.71 | -$4.67 | -$44.06 | -$48.59 | -$28.41 | -$38.20 | -$42.07 | -11.0% | 0.82 | $8.69 |
| 2026-06 | -$145.84 | +$61.38 | -$37.95 | -$1.79 | -$30.11 | +$5.61 | -$48.01 | -14.6% | 0.71 | $8.39 |
| 2026-07 | $44.21 | -$25.60 | +$10.66 | -$18.63 | +$46.87 | -$12.89 | +$12.76 | -5.6% | 0.97 | $3.49 |
| 2026-08 | $245.33 | $0.00 | +$3.72 | +$37.39 | +$25.03 | +$15.15 | +$18.74 | -3.2% | 1.00 | $3.49 |
| 2026-09 | $27.94 | -$31.96 | +$13.40 | +$4.11 | +$4.31 | -$26.61 | +$44.89 | -6.6% | 0.87 | $6.88 |
| 2026-10 | -$76.42 | $0.00 | -$5.83 | -$15.38 | +$15.91 | -$15.53 | -$24.49 | -10.8% | 1.00 | $3.49 |
| 2026-11 | -$141.55 | +$89.55 | -$39.86 | -$69.37 | -$65.68 | -$41.49 | -$97.14 | -17.7% | 0.71 | $5.15 |

### Dial E

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $80.38 | -$34.05 | -$34.05 | -$23.57 | -$2.63 | -$34.05 | -$15.20 | -3.1% | 0.72 | $2.45 |
| 2026-05 | -$27.42 | +$11.61 | -$27.77 | -$32.30 | -$12.12 | -$21.91 | -$25.78 | -7.7% | 0.71 | $2.45 |
| 2026-06 | -$145.56 | +$61.66 | -$37.67 | -$1.51 | -$29.83 | +$5.89 | -$47.73 | -14.6% | 0.67 | $2.45 |
| 2026-07 | $49.04 | -$20.77 | +$15.49 | -$13.80 | +$51.70 | -$8.06 | +$17.59 | -4.0% | 0.72 | $2.45 |
| 2026-08 | $172.34 | -$73.00 | -$69.27 | -$35.60 | -$47.96 | -$57.84 | -$54.25 | -2.4% | 0.72 | $2.45 |
| 2026-09 | $42.07 | -$17.82 | +$27.53 | +$18.24 | +$18.44 | -$12.48 | +$59.02 | -5.0% | 0.71 | $2.45 |
| 2026-10 | -$53.68 | +$22.74 | +$16.91 | +$7.36 | +$38.65 | +$7.21 | -$1.75 | -7.6% | 0.70 | $2.45 |
| 2026-11 | -$162.34 | +$68.76 | -$60.65 | -$90.16 | -$86.47 | -$62.28 | -$117.93 | -19.1% | 0.68 | $2.45 |

### Dial F-OPUS (hindsight)

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $114.43 | $0.00 | $0.00 | +$10.48 | +$31.42 | $0.00 | +$18.85 | -4.2% | 1.00 | $3.49 |
| 2026-05 | -$25.51 | +$13.53 | -$25.86 | -$30.39 | -$10.21 | -$20.00 | -$23.87 | -7.2% | 0.66 | $2.28 |
| 2026-06 | -$93.91 | +$113.31 | +$13.98 | +$50.14 | +$21.82 | +$57.54 | +$3.92 | -9.4% | 0.42 | $1.58 |
| 2026-07 | $56.25 | -$13.56 | +$22.70 | -$6.59 | +$58.91 | -$0.85 | +$24.80 | -4.6% | 0.82 | $2.81 |
| 2026-08 | $241.42 | -$3.92 | -$0.19 | +$33.48 | +$21.12 | +$11.24 | +$14.83 | -3.2% | 0.99 | $3.43 |
| 2026-09 | $52.09 | -$7.81 | +$37.55 | +$28.26 | +$28.46 | -$2.46 | +$69.04 | -6.1% | 0.87 | $3.04 |
| 2026-10 | -$57.89 | +$18.53 | +$12.70 | +$3.15 | +$34.44 | +$3.00 | -$5.96 | -8.2% | 0.75 | $2.64 |
| 2026-11 | -$98.01 | +$133.10 | +$3.68 | -$25.83 | -$22.14 | +$2.05 | -$53.60 | -11.6% | 0.40 | $1.48 |

### Dial F-SOL (hindsight)

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $111.97 | -$2.46 | -$2.46 | +$8.02 | +$28.96 | -$2.46 | +$16.39 | -4.1% | 0.98 | $3.42 |
| 2026-05 | -$23.44 | +$15.59 | -$23.79 | -$28.32 | -$8.14 | -$17.93 | -$21.80 | -6.6% | 0.61 | $2.10 |
| 2026-06 | -$96.74 | +$110.49 | +$11.15 | +$47.31 | +$18.99 | +$54.71 | +$1.09 | -9.7% | 0.43 | $1.63 |
| 2026-07 | $66.69 | -$3.12 | +$33.14 | +$3.85 | +$69.35 | +$9.59 | +$35.24 | -5.3% | 0.96 | $3.33 |
| 2026-08 | $224.38 | -$20.95 | -$17.23 | +$16.44 | +$4.08 | -$5.80 | -$2.21 | -3.0% | 0.92 | $3.19 |
| 2026-09 | $54.13 | -$5.76 | +$39.59 | +$30.30 | +$30.50 | -$0.42 | +$71.08 | -6.3% | 0.91 | $3.15 |
| 2026-10 | -$52.98 | +$23.44 | +$17.61 | +$8.06 | +$39.35 | +$7.91 | -$1.05 | -7.5% | 0.69 | $2.42 |
| 2026-11 | -$78.13 | +$152.97 | +$23.56 | -$5.95 | -$2.26 | +$21.93 | -$33.72 | -9.3% | 0.31 | $1.18 |

### Dial F-NEON (hindsight)

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $112.92 | -$1.51 | -$1.51 | +$8.97 | +$29.91 | -$1.51 | +$17.34 | -4.2% | 0.99 | $3.44 |
| 2026-05 | -$24.77 | +$14.26 | -$25.12 | -$29.65 | -$9.47 | -$19.26 | -$23.13 | -7.0% | 0.64 | $2.21 |
| 2026-06 | -$88.02 | +$119.20 | +$19.87 | +$56.03 | +$27.71 | +$63.43 | +$9.81 | -8.8% | 0.39 | $1.48 |
| 2026-07 | $50.16 | -$19.65 | +$16.61 | -$12.68 | +$52.82 | -$6.94 | +$18.71 | -4.1% | 0.73 | $2.51 |
| 2026-08 | $224.80 | -$20.53 | -$16.81 | +$16.86 | +$4.50 | -$5.38 | -$1.79 | -3.0% | 0.92 | $3.20 |
| 2026-09 | $51.12 | -$8.77 | +$36.58 | +$27.29 | +$27.49 | -$3.43 | +$68.07 | -6.0% | 0.86 | $2.98 |
| 2026-10 | -$49.31 | +$27.11 | +$21.28 | +$11.73 | +$43.02 | +$11.58 | +$2.62 | -7.0% | 0.64 | $2.25 |
| 2026-11 | -$70.64 | +$160.46 | +$31.05 | +$1.54 | +$5.23 | +$29.42 | -$26.23 | -8.4% | 0.28 | $1.07 |

### Dial F-SONNET (hindsight)

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $114.43 | $0.00 | $0.00 | +$10.48 | +$31.42 | $0.00 | +$18.85 | -4.2% | 1.00 | $3.49 |
| 2026-05 | -$26.84 | +$12.19 | -$27.19 | -$31.72 | -$11.54 | -$21.33 | -$25.20 | -7.5% | 0.69 | $2.40 |
| 2026-06 | -$82.33 | +$124.90 | +$25.56 | +$61.72 | +$33.40 | +$69.12 | +$15.50 | -8.2% | 0.36 | $1.39 |
| 2026-07 | $68.94 | -$0.87 | +$35.39 | +$6.10 | +$71.60 | +$11.84 | +$37.49 | -5.5% | 0.99 | $3.45 |
| 2026-08 | $231.94 | -$13.40 | -$9.67 | +$24.00 | +$11.64 | +$1.76 | +$5.35 | -3.1% | 0.95 | $3.30 |
| 2026-09 | $58.91 | -$0.99 | +$44.37 | +$35.08 | +$35.28 | +$4.36 | +$75.86 | -6.9% | 0.98 | $3.43 |
| 2026-10 | -$52.97 | +$23.44 | +$17.62 | +$8.07 | +$39.36 | +$7.92 | -$1.04 | -7.5% | 0.69 | $2.42 |
| 2026-11 | -$115.70 | +$115.40 | -$14.01 | -$43.52 | -$39.83 | -$15.64 | -$71.29 | -13.7% | 0.47 | $1.75 |

### Dial F-GROK (hindsight)

| Month | Gain ($) | vs Hold | vs OPUS | vs SOL | vs NEON | vs SONNET | vs GROK | Largest drop | Avg share | Costs ($) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04 | $113.68 | -$0.75 | -$0.75 | +$9.73 | +$30.67 | -$0.75 | +$18.10 | -4.2% | 0.99 | $3.47 |
| 2026-05 | -$25.27 | +$13.76 | -$25.62 | -$30.15 | -$9.97 | -$19.76 | -$23.63 | -7.1% | 0.65 | $2.26 |
| 2026-06 | -$62.01 | +$145.21 | +$45.88 | +$82.04 | +$53.72 | +$89.44 | +$35.82 | -6.2% | 0.27 | $1.04 |
| 2026-07 | $58.13 | -$11.68 | +$24.58 | -$4.71 | +$60.79 | +$1.03 | +$26.68 | -4.7% | 0.84 | $2.91 |
| 2026-08 | $234.30 | -$11.03 | -$7.31 | +$26.36 | +$14.00 | +$4.12 | +$7.71 | -3.1% | 0.96 | $3.33 |
| 2026-09 | $53.81 | -$6.08 | +$39.27 | +$29.98 | +$30.18 | -$0.74 | +$70.76 | -6.3% | 0.90 | $3.14 |
| 2026-10 | -$44.62 | +$31.80 | +$25.97 | +$16.42 | +$47.71 | +$16.27 | +$7.31 | -6.4% | 0.58 | $2.04 |
| 2026-11 | -$72.45 | +$158.65 | +$29.24 | -$0.27 | +$3.42 | +$27.61 | -$28.04 | -8.6% | 0.29 | $1.09 |

## What this says

- MEASURED. Every fixed dial A to E beat holding BTC/USD (-$64.31) over these eight months.
- MEASURED. Plain moving-average rules that can cut all the way to 0.0 matched the best AI models without headlines or a language model: Dial B ended at $132.07 (beating 3 of 5 complete models: OPUS, SOL, NEON) and Dial C ended at $132.51 (beating 3 of 5 complete models: OPUS, SOL, NEON), compared with $25.05 (Gemini Neon) to $140.85 (Grok 4.7). Worst-month drops were -8.6% for Dial B and -7.4% for Dial C, against -15.2% to -9.8% across the complete models, with costs of $90.02 and $85.90.
- MEASURED. A constant lower share alone did not explain the models' edge over hold: Dial E (constant 0.7) ended at -$45.18 (+$19.14 vs hold). Dials A ($33.88) and D ($24.39), which never cut below 0.5, also lagged B, C and the top models during the two sharp down months (June and November).
- MEASURED. Holding each model's own month-average share constant from day 1 (Dial F, hindsight) beat every complete model by +$58.02 to +$181.21. That explains why the models failed their shuffled-stretch test in TM03: their gain over hold came from lowering exposure during falling months, but they cut after the drops had already started and paid more in trading costs than holding the same monthly share flat.
- STATED. Plain trend rules on bitcoin over many years did not pass in replay 01 (`docs/research/12_replay_01_crypto_trend.md`, corrected in `docs/research/16_rig_audit.md`), so matching them over eight months is not evidence of an edge.

## What this does not show

- STATED. Eight months only (April to November 24, 2026). That window is far too short to judge any trading rule.
- STATED. The dials were chosen on 2026-11-25 by someone who had already seen the months' hold returns.
- STATED. These dials are not counted rule trials in `research_rig/TRIAL_LEDGER.md` and prove nothing on their own.
- STATED. Long only, with no shorting and no leverage.
- STATED. Fills are assumed at the open of the first recorded minute at or after each wake, with fixed half spread (`tm_crypto_half_spread_bps`) and fixed crypto fee (`practice_crypto_fee_bps_added`), not live order-book fills.
- STATED. Dials F-* are hindsight: they read each model's finished monthly average share from `timemachine/results_tm03.json` and hold it from day 1 of that month.

## Files

- `timemachine/dial_rules_tm03.py`: runs the fixed dials through `timemachine/weights.py`, writes `timemachine/dial_rules_tm03.json` and this page (`--write`), checks freshness (`--check`), and runs synthetic-price tests (`--test`).
- `timemachine/dial_rules_tm03.json`: stored JSON output with sorted keys.
- `timemachine/results_tm03.json` and `docs/research/34_time_machine_tm03_bitcoin_dial.md`: the AI model results compared here.
- `docs/research/12_replay_01_crypto_trend.md` and `docs/research/16_rig_audit.md`: multi-year replay 01 results where plain crypto trend rules did not pass.
