# Time machine exit replay (TMX1): fixed exit templates on logged AI buys

Made by `timemachine/exit_replay.py` from `timemachine/results_tmx1.json` at 2026-11-25 16:22:25 UTC. Do not edit by hand. Pretend money only. Plan fixed before running: `timemachine/PLAN_TMX1_exit_replay.md`.

## What was tested

- Every logged filled BUY from finished `TM01` (prices only) and `TM02` (with news) sessions, plus finished random twin sessions, replayed one trade at a time on its own without re-simulating the cash book.
- Costs from `config/thresholds.yaml`: half-spread `tm_crypto_half_spread_bps` and fee `practice_crypto_fee_bps_added` (`practice_crypto_fee_in_coin` = 0), filled on 1Min bars from the recorded tape.
- Templates: A = as traded; B = 48h time only; C = 120h time only; D = 8% stop, no target, 120h; E = 8% stop, +3% trigger / 5% trail, 120h. Stops check each 1Min close and fill at the next minute's open. Trades still open at session end close at the session's last minute.
- Fixed mark: on `TM01` AI buys, a template helps only if its summed dollar gain beats A in at least 4 of the 5 months AND for at least 5 of the 6 models.

## Session coverage at run time

Run timestamp: 2026-11-25 16:22:25 UTC.

- TM01: 27 finished, 3 unfinished (TM01-B01-KIMI-2026-09, TM01-B01-KIMI-2026-11, TM01-B01-GROK-2026-11). Paired with twins: 9 sessions (162 finished twin runs).
- TM02: 16 finished, 14 unfinished (TM02-B02-OPUS-2026-11, TM02-B02-SOL-2026-11, TM02-B02-NEON-2026-08, TM02-B02-NEON-2026-09, TM02-B02-NEON-2026-11, TM02-B02-SONNET-2026-11, TM02-B02-KIMI-2026-07, TM02-B02-KIMI-2026-08, TM02-B02-KIMI-2026-09, TM02-B02-KIMI-2026-11, TM02-B02-GROK-2026-07, TM02-B02-GROK-2026-08, TM02-B02-GROK-2026-09, TM02-B02-GROK-2026-11). Paired with twins: 0 sessions (0 finished twin runs).

## TM01: summed dollar gain by model

| Model | Months | Buys | A (as traded) | B (48h) | C (120h) | D (8% stop, 120h) | E (8% / +3% trail, 120h) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Claude Opus 5.5 | 5 of 5 | 46 | -$148.89 | -$111.35 | -$150.86 | -$97.04 | -$59.84 |
| GPT-6.2 Sol | 5 of 5 | 19 | -$34.23 | $16.20 | -$63.34 | -$56.48 | -$70.54 |
| Gemini Neon | 5 of 5 | 45 | $12.96 | $9.68 | $81.53 | $80.62 | $27.95 |
| Claude Sonnet 5.5 | 5 of 5 | 20 | -$63.38 | $19.09 | $0.68 | $0.68 | -$27.08 |
| Kimi K3 | 3 of 5 | 30 | -$112.34 | -$56.38 | $24.07 | -$0.27 | $2.25 |
| Grok 4.7 | 4 of 5 | 16 | -$48.19 | -$26.09 | $29.88 | $29.88 | -$38.92 |
| **Total (AI buys)** | 27 sess | 176 | -$394.07 | -$148.85 | -$78.04 | -$42.60 | -$166.18 |
| **BTC same windows** | same | same | -$368.19 | -$10.44 | $114.26 | $120.50 | $35.94 |

## TM01: summed dollar gain by month

| Month | Models | Buys | A (as traded) | B (48h) | C (120h) | D (8% stop, 120h) | E (8% / +3% trail, 120h) | BTC same windows (A / B / C / D / E) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| July | 6 of 6 | 45 | -$55.51 | $47.43 | $61.21 | $61.21 | $22.75 | -$102.83 / $21.94 / $94.50 / $94.50 / $49.54 |
| August | 6 of 6 | 35 | $276.27 | $185.80 | $485.74 | $485.74 | $315.33 | $199.78 / $181.33 / $398.50 / $398.50 / $305.07 |
| September | 5 of 6 | 32 | $17.84 | $28.48 | $143.61 | $153.07 | $83.43 | -$1.57 / $30.88 / $125.51 / $129.76 / $85.65 |
| October | 6 of 6 | 37 | -$493.22 | -$238.18 | -$298.89 | -$322.72 | -$315.09 | -$333.52 / -$103.44 / -$109.74 / -$134.22 / -$145.51 |
| November 1 to 24 | 4 of 6 | 27 | -$139.45 | -$172.38 | -$469.71 | -$419.91 | -$272.60 | -$130.07 / -$141.15 / -$394.50 / -$368.04 / -$258.82 |

## TM02: summed dollar gain by model

| Model | Months | Buys | A (as traded) | B (48h) | C (120h) | D (8% stop, 120h) | E (8% / +3% trail, 120h) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Claude Opus 5.5 | 4 of 5 | 35 | -$21.99 | $62.38 | $92.14 | $106.55 | $105.47 |
| GPT-6.2 Sol | 4 of 5 | 19 | $2.61 | $33.51 | $57.39 | $60.37 | $14.99 |
| Gemini Neon | 2 of 5 | 12 | -$72.12 | $1.65 | $2.90 | -$7.61 | -$22.91 |
| Claude Sonnet 5.5 | 4 of 5 | 15 | -$32.40 | $0.16 | -$0.92 | $8.17 | -$8.59 |
| Kimi K3 | 1 of 5 | 11 | -$69.90 | -$51.16 | -$73.19 | -$81.29 | -$83.44 |
| Grok 4.7 | 1 of 5 | 1 | -$18.22 | -$8.28 | -$18.51 | -$18.51 | -$18.51 |
| **Total (AI buys)** | 16 sess | 93 | -$212.02 | $38.25 | $59.81 | $67.68 | -$12.98 |
| **BTC same windows** | same | same | -$208.20 | $15.24 | $110.44 | $107.22 | $22.77 |

## TM02: summed dollar gain by month

| Month | Models | Buys | A (as traded) | B (48h) | C (120h) | D (8% stop, 120h) | E (8% / +3% trail, 120h) | BTC same windows (A / B / C / D / E) |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| July | 4 of 6 | 17 | $9.25 | $49.08 | $79.37 | $79.37 | $46.71 | -$24.29 / $10.44 / $63.24 / $63.24 / $26.40 |
| August | 3 of 6 | 22 | $93.18 | $128.67 | $238.09 | $238.09 | $160.81 | $29.98 / $105.69 / $176.53 / $176.53 / $135.74 |
| September | 3 of 6 | 24 | -$54.44 | $22.40 | $13.99 | $32.54 | $63.95 | -$26.27 / $21.76 / $50.40 / $59.91 / $56.20 |
| October | 6 of 6 | 30 | -$260.01 | -$161.89 | -$271.64 | -$282.31 | -$284.45 | -$187.63 / -$122.65 / -$179.74 / -$192.46 / -$195.58 |
| November 1 to 24 | 0 of 6 | 0 | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 | $0.00 / $0.00 / $0.00 / $0.00 / $0.00 |

## AI buys minus random twin buys

Paired across 9 finished TM01 sessions (162 finished twin runs; each session's twins averaged to match 1 AI session scale).

| Group | Paired | A (as traded) | B (48h) | C (120h) | D (8% stop, 120h) | E (8% / +3% trail, 120h) |
|---|---:|---:|---:|---:|---:|---:|
| AI buys (paired) | 9 | -$95.16 | -$46.29 | $91.60 | $77.30 | -$41.42 |
| Twin mean (paired) | 9 | -$197.41 | $39.55 | $149.66 | $102.06 | -$13.14 |
| **AI minus twins** | 9 | $102.24 | -$85.84 | -$58.06 | -$24.77 | -$28.28 |

By model (TM01, AI minus twins):

| Model | Paired months | A | B | C | D | E |
|---|---:|---:|---:|---:|---:|---:|
| Claude Opus 5.5 | 1 | -$4.55 | $0.73 | $15.36 | $22.09 | $26.60 |
| GPT-6.2 Sol | 1 | -$8.19 | -$3.96 | -$8.87 | $0.15 | -$2.65 |
| Gemini Neon | 3 | $133.38 | -$76.18 | -$92.66 | -$83.45 | -$113.35 |
| Claude Sonnet 5.5 | 1 | -$19.09 | -$7.75 | $3.33 | $3.35 | -$1.08 |
| Kimi K3 | 2 | -$4.06 | -$2.27 | $15.06 | $23.39 | $46.16 |
| Grok 4.7 | 1 | $4.74 | $3.59 | $9.72 | $9.70 | $16.04 |

By month (TM01, AI minus twins):

| Month | Paired models | A | B | C | D | E |
|---|---:|---:|---:|---:|---:|---:|
| July | 2 | $56.98 | $22.00 | $64.24 | $68.85 | $71.22 |
| August | 1 | $57.92 | -$50.21 | -$19.92 | -$19.92 | -$38.74 |
| September | 1 | $16.45 | -$50.82 | -$112.35 | -$103.14 | -$114.58 |
| October | 5 | -$29.11 | -$6.82 | $9.97 | $29.44 | $53.82 |
- TM02: 0 finished twin sessions at run time; AI minus twins is not available yet.

## Verdict against the fixed marks

Primary mark is `TM01` AI buys: a template helps only if it beats A in at least 4 of 5 months AND for at least 5 of 6 models. `TM02` is shown beside it for reference.

| Template | Description | TM01 total vs A | TM01 months > A | TM01 models > A | TM01 verdict | TM02 months > A | TM02 models > A |
|---|---|---:|---:|---:|---|---:|---:|
| B | time only, 48 hours after fill | $245.22 | 3 of 5 | 5 of 6 | does not help | 4 of 5 | 6 of 6 |
| C | time only, 120 hours after fill | $316.03 | 4 of 5 | 4 of 6 | does not help | 3 of 5 | 4 of 6 |
| D | stop 8% below fill, no target, 120 hours | $351.47 | 4 of 5 | 5 of 6 | HELPS (earns fresh test on new months) | 3 of 5 | 4 of 6 |
| E | stop 8%, once up 3% trail 5% below highest close, 120 hours | $227.89 | 4 of 5 | 5 of 6 | HELPS (earns fresh test on new months) | 3 of 5 | 4 of 6 |

## Trade-record checks

- TM01-B01-NEON-2026-07: 2 open position(s) at session end (acct=57.38, closed_sum=61.18)
- TM01-B01-NEON-2026-08: 1 open position(s) at session end (acct=157.01, closed_sum=122.75)
- TM01-B01-NEON-2026-09: 2 open position(s) at session end (acct=45.43, closed_sum=9.68)
- TM01-B01-KIMI-2026-08: 1 open position(s) at session end (acct=22.28, closed_sum=21.99)
- TM02-B02-OPUS-2026-09: 1 open position(s) at session end (acct=-28.24, closed_sum=-24.27)
- TM02-B02-SONNET-2026-10: problems=[{'text': 'Pick 20261027T1200Z: sell BTC/USD was not placed: there is nothing to sell.', 'trader': 'B02-SONNET', 'utc': '2026-10-27T12:05:00Z'}]
- TM02-B02-KIMI-2026-10: 1 open position(s) at session end (acct=-69.90, closed_sum=-69.67)

## What this does not show

- This is a second look at months already traded. A "helps" verdict does not prove a rule is profitable and is not a result to trade on; it only earns a fresh test on new months.
- Each buy is replayed on its own without re-simulating the cash book. Longer holds (48h or 120h) would tie up cash and block some later buys in a live cash account, so summed per-trade dollars overstate what a single cash book could deploy when buys overlap.
- A longer hold in a rising market gains from market drift alone. Compare AI buys against both BTC over the same windows and AI minus random twins before attributing any gain to entry skill.
- Fills are assumed from recorded 1Min bars with fixed spread and fee assumptions; real fills on thin crypto minutes could be worse.
- Unfinished sessions at run time are omitted; rerunning after all 30 sessions per plan and all 20 twins per session finish may change totals.
