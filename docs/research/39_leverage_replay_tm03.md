# Leverage replay of plan TM03: the same bitcoin dials at 2x, 3x and 5x

Made by `timemachine/leverage_replay_tm03.py` from the finished TM03 sessions. Do not edit by hand. Pretend money.

Looked at after the fact. The models answered for a 1x account and did not know they were leveraged. This is not a counted trial and not part of any plan's mark.

## What was done

- Every stored daily answer of every finished TM03 session was replayed through the weights book with each weight, and the opening, times the multiple (`tm_lev_replay_multiples`). Holding (1.0 times the multiple) and dials B and C of `timemachine/dial_rules_tm03.py` were replayed the same way.
- 1x goes through the same leverage path and matches every stored session to the cent. The script stops if it does not.
- Borrowed dollars pay financing at each whole UTC hour. For BTC/USD the rate is the stored hourly perpetual funding (funding file rig/data/funding/kraken_PF_XBTUSD.json; key `tm_lev_funding_files`), paid by longs when positive and received when negative. Hours the file lacks use `tm_lev_fixed_rate_per_day`.
- On every recorded minute between wakes, if the account value at the minute's low is below `tm_lev_maintenance_crypto` of the position's value, the whole book is sold at that low, less the half spread, the fee and `tm_lev_closeout_penalty`. It stays in cash until the next wake, then the standing dial is bought again.
- Each month starts from the same account, as in TM03. A month that ends at zero does not carry into the next.
- "Gain, months summed" adds each month's gain, every month starting again from the same account, as TM03 scores it. "One account carried" takes one account through the months in order, so a month that ends near zero leaves little for the next. A real account works the second way.
- "Months below" counts months that ended below `tm_lev_replay_low_share` (0.5) of the $1,000.00 start. Largest drop: the worst month, measured on minute lows.
- Keys read: `tm_lev_closeout_penalty` from config/thresholds.yaml, `tm_lev_fixed_rate_per_day` from config/thresholds.yaml, `tm_lev_funding_files` from config/thresholds.yaml, `tm_lev_maintenance_crypto` from config/thresholds.yaml, `tm_lev_maintenance_stocks` from config/thresholds.yaml, `tm_lev_replay_low_share` from config/thresholds.yaml, `tm_lev_replay_multiples` from config/thresholds.yaml.

## Holding and the dials, every month

MEASURED, summed over 8 months.

| What | Multiple | Gain, months summed | One account carried | Worst month drop | Close-outs | Financing | Months below |
|---|---|---|---|---|---|---|---|
| hold | 1x | -$64.31 | -$148.65 | -31.9% | 0 | $0.00 | 0 of 8 |
| hold | 2x | -$155.17 | -$442.77 | -61.8% | 0 | $26.55 | 0 of 8 |
| hold | 3x | -$246.03 | -$757.61 | -89.5% | 0 | $53.10 | 2 of 8 |
| hold | 5x | -$29.45 | -$976.72 | -96.5% | 2 | $99.53 | 2 of 8 |
| dial B | 1x | $132.07 | $114.40 | -9.8% | 0 | $0.00 | 0 of 8 |
| dial B | 2x | $241.98 | $168.89 | -18.5% | 0 | $9.20 | 0 of 8 |
| dial B | 3x | $339.59 | $175.53 | -26.4% | 0 | $18.12 | 0 of 8 |
| dial B | 5x | $499.53 | $68.37 | -39.9% | 0 | $35.19 | 0 of 8 |
| dial C | 1x | $132.51 | $115.87 | -8.1% | 0 | $0.00 | 0 of 8 |
| dial C | 2x | $252.25 | $182.91 | -15.5% | 0 | $6.59 | 0 of 8 |
| dial C | 3x | $364.56 | $205.72 | -22.3% | 0 | $14.32 | 0 of 8 |
| dial C | 5x | $561.72 | $126.86 | -35.0% | 0 | $33.55 | 0 of 8 |

## Each model, over the months it has

MEASURED. Each model's rows are against holding and the dials over the same months.

### Claude Opus 5.5

8 months.

| What | Multiple | Gain, months summed | One account carried | Worst month drop | Close-outs | Financing | Months below |
|---|---|---|---|---|---|---|---|
| the model's dials | 1x | $124.30 | $81.04 | -13.4% | 0 | $0.00 | 0 of 8 |
| the model's dials | 2x | $240.06 | $70.31 | -25.4% | 0 | $12.95 | 0 of 8 |
| the model's dials | 3x | $350.40 | -$13.37 | -36.1% | 0 | $32.88 | 0 of 8 |
| the model's dials | 5x | $567.89 | -$293.80 | -54.0% | 0 | $77.19 | 0 of 8 |
| hold | 1x | -$64.31 | -$148.65 | -31.9% | 0 | $0.00 | 0 of 8 |
| hold | 2x | -$155.17 | -$442.77 | -61.8% | 0 | $26.55 | 0 of 8 |
| hold | 3x | -$246.03 | -$757.61 | -89.5% | 0 | $53.10 | 2 of 8 |
| hold | 5x | -$29.45 | -$976.72 | -96.5% | 2 | $99.53 | 2 of 8 |
| dial B | 1x | $132.07 | $114.40 | -9.8% | 0 | $0.00 | 0 of 8 |
| dial B | 2x | $241.98 | $168.89 | -18.5% | 0 | $9.20 | 0 of 8 |
| dial B | 3x | $339.59 | $175.53 | -26.4% | 0 | $18.12 | 0 of 8 |
| dial B | 5x | $499.53 | $68.37 | -39.9% | 0 | $35.19 | 0 of 8 |
| dial C | 1x | $132.51 | $115.87 | -8.1% | 0 | $0.00 | 0 of 8 |
| dial C | 2x | $252.25 | $182.91 | -15.5% | 0 | $6.59 | 0 of 8 |
| dial C | 3x | $364.56 | $205.72 | -22.3% | 0 | $14.32 | 0 of 8 |
| dial C | 5x | $561.72 | $126.86 | -35.0% | 0 | $33.55 | 0 of 8 |

### GPT-6.2 Sol

8 months.

| What | Multiple | Gain, months summed | One account carried | Worst month drop | Close-outs | Financing | Months below |
|---|---|---|---|---|---|---|---|
| the model's dials | 1x | $126.17 | $87.33 | -15.0% | 0 | $0.00 | 0 of 8 |
| the model's dials | 2x | $267.07 | $107.70 | -28.3% | 0 | $14.17 | 0 of 8 |
| the model's dials | 3x | $431.55 | $70.55 | -40.1% | 0 | $33.12 | 0 of 8 |
| the model's dials | 5x | $839.31 | -$130.71 | -59.4% | 0 | $73.65 | 1 of 8 |
| hold | 1x | -$64.31 | -$148.65 | -31.9% | 0 | $0.00 | 0 of 8 |
| hold | 2x | -$155.17 | -$442.77 | -61.8% | 0 | $26.55 | 0 of 8 |
| hold | 3x | -$246.03 | -$757.61 | -89.5% | 0 | $53.10 | 2 of 8 |
| hold | 5x | -$29.45 | -$976.72 | -96.5% | 2 | $99.53 | 2 of 8 |
| dial B | 1x | $132.07 | $114.40 | -9.8% | 0 | $0.00 | 0 of 8 |
| dial B | 2x | $241.98 | $168.89 | -18.5% | 0 | $9.20 | 0 of 8 |
| dial B | 3x | $339.59 | $175.53 | -26.4% | 0 | $18.12 | 0 of 8 |
| dial B | 5x | $499.53 | $68.37 | -39.9% | 0 | $35.19 | 0 of 8 |
| dial C | 1x | $132.51 | $115.87 | -8.1% | 0 | $0.00 | 0 of 8 |
| dial C | 2x | $252.25 | $182.91 | -15.5% | 0 | $6.59 | 0 of 8 |
| dial C | 3x | $364.56 | $205.72 | -22.3% | 0 | $14.32 | 0 of 8 |
| dial C | 5x | $561.72 | $126.86 | -35.0% | 0 | $33.55 | 0 of 8 |

### Gemini Neon

8 months.

| What | Multiple | Gain, months summed | One account carried | Worst month drop | Close-outs | Financing | Months below |
|---|---|---|---|---|---|---|---|
| the model's dials | 1x | $25.05 | -$14.55 | -13.0% | 0 | $0.00 | 0 of 8 |
| the model's dials | 2x | $54.55 | -$93.32 | -24.8% | 0 | $11.38 | 0 of 8 |
| the model's dials | 3x | $97.14 | -$210.53 | -35.4% | 0 | $26.09 | 0 of 8 |
| the model's dials | 5x | $231.18 | -$484.03 | -53.3% | 0 | $56.18 | 0 of 8 |
| hold | 1x | -$64.31 | -$148.65 | -31.9% | 0 | $0.00 | 0 of 8 |
| hold | 2x | -$155.17 | -$442.77 | -61.8% | 0 | $26.55 | 0 of 8 |
| hold | 3x | -$246.03 | -$757.61 | -89.5% | 0 | $53.10 | 2 of 8 |
| hold | 5x | -$29.45 | -$976.72 | -96.5% | 2 | $99.53 | 2 of 8 |
| dial B | 1x | $132.07 | $114.40 | -9.8% | 0 | $0.00 | 0 of 8 |
| dial B | 2x | $241.98 | $168.89 | -18.5% | 0 | $9.20 | 0 of 8 |
| dial B | 3x | $339.59 | $175.53 | -26.4% | 0 | $18.12 | 0 of 8 |
| dial B | 5x | $499.53 | $68.37 | -39.9% | 0 | $35.19 | 0 of 8 |
| dial C | 1x | $132.51 | $115.87 | -8.1% | 0 | $0.00 | 0 of 8 |
| dial C | 2x | $252.25 | $182.91 | -15.5% | 0 | $6.59 | 0 of 8 |
| dial C | 3x | $364.56 | $205.72 | -22.3% | 0 | $14.32 | 0 of 8 |
| dial C | 5x | $561.72 | $126.86 | -35.0% | 0 | $33.55 | 0 of 8 |

### Claude Sonnet 5.5

8 months.

| What | Multiple | Gain, months summed | One account carried | Worst month drop | Close-outs | Financing | Months below |
|---|---|---|---|---|---|---|---|
| the model's dials | 1x | $138.35 | $89.96 | -15.5% | 0 | $0.00 | 0 of 8 |
| the model's dials | 2x | $277.87 | $82.71 | -29.7% | 0 | $16.34 | 0 of 8 |
| the model's dials | 3x | $427.20 | -$2.39 | -42.7% | 0 | $37.33 | 0 of 8 |
| the model's dials | 5x | $756.70 | -$316.89 | -65.0% | 0 | $83.33 | 1 of 8 |
| hold | 1x | -$64.31 | -$148.65 | -31.9% | 0 | $0.00 | 0 of 8 |
| hold | 2x | -$155.17 | -$442.77 | -61.8% | 0 | $26.55 | 0 of 8 |
| hold | 3x | -$246.03 | -$757.61 | -89.5% | 0 | $53.10 | 2 of 8 |
| hold | 5x | -$29.45 | -$976.72 | -96.5% | 2 | $99.53 | 2 of 8 |
| dial B | 1x | $132.07 | $114.40 | -9.8% | 0 | $0.00 | 0 of 8 |
| dial B | 2x | $241.98 | $168.89 | -18.5% | 0 | $9.20 | 0 of 8 |
| dial B | 3x | $339.59 | $175.53 | -26.4% | 0 | $18.12 | 0 of 8 |
| dial B | 5x | $499.53 | $68.37 | -39.9% | 0 | $35.19 | 0 of 8 |
| dial C | 1x | $132.51 | $115.87 | -8.1% | 0 | $0.00 | 0 of 8 |
| dial C | 2x | $252.25 | $182.91 | -15.5% | 0 | $6.59 | 0 of 8 |
| dial C | 3x | $364.56 | $205.72 | -22.3% | 0 | $14.32 | 0 of 8 |
| dial C | 5x | $561.72 | $126.86 | -35.0% | 0 | $33.55 | 0 of 8 |

### Kimi K3

8 months.

| What | Multiple | Gain, months summed | One account carried | Worst month drop | Close-outs | Financing | Months below |
|---|---|---|---|---|---|---|---|
| the model's dials | 1x | $12.67 | -$22.54 | -14.8% | 0 | $0.00 | 0 of 8 |
| the model's dials | 2x | $38.88 | -$94.30 | -28.0% | 0 | $5.12 | 0 of 8 |
| the model's dials | 3x | $76.66 | -$202.43 | -39.7% | 0 | $16.15 | 0 of 8 |
| the model's dials | 5x | $190.59 | -$460.29 | -58.9% | 0 | $43.31 | 1 of 8 |
| hold | 1x | -$64.31 | -$148.65 | -31.9% | 0 | $0.00 | 0 of 8 |
| hold | 2x | -$155.17 | -$442.77 | -61.8% | 0 | $26.55 | 0 of 8 |
| hold | 3x | -$246.03 | -$757.61 | -89.5% | 0 | $53.10 | 2 of 8 |
| hold | 5x | -$29.45 | -$976.72 | -96.5% | 2 | $99.53 | 2 of 8 |
| dial B | 1x | $132.07 | $114.40 | -9.8% | 0 | $0.00 | 0 of 8 |
| dial B | 2x | $241.98 | $168.89 | -18.5% | 0 | $9.20 | 0 of 8 |
| dial B | 3x | $339.59 | $175.53 | -26.4% | 0 | $18.12 | 0 of 8 |
| dial B | 5x | $499.53 | $68.37 | -39.9% | 0 | $35.19 | 0 of 8 |
| dial C | 1x | $132.51 | $115.87 | -8.1% | 0 | $0.00 | 0 of 8 |
| dial C | 2x | $252.25 | $182.91 | -15.5% | 0 | $6.59 | 0 of 8 |
| dial C | 3x | $364.56 | $205.72 | -22.3% | 0 | $14.32 | 0 of 8 |
| dial C | 5x | $561.72 | $126.86 | -35.0% | 0 | $33.55 | 0 of 8 |

### Grok 4.7

8 months.

| What | Multiple | Gain, months summed | One account carried | Worst month drop | Close-outs | Financing | Months below |
|---|---|---|---|---|---|---|---|
| the model's dials | 1x | $140.85 | $111.86 | -10.4% | 0 | $0.00 | 0 of 8 |
| the model's dials | 2x | $274.47 | $156.05 | -20.0% | 0 | $12.35 | 0 of 8 |
| the model's dials | 3x | $409.24 | $142.67 | -28.8% | 0 | $28.57 | 0 of 8 |
| the model's dials | 5x | $691.99 | -$13.74 | -44.4% | 0 | $61.60 | 0 of 8 |
| hold | 1x | -$64.31 | -$148.65 | -31.9% | 0 | $0.00 | 0 of 8 |
| hold | 2x | -$155.17 | -$442.77 | -61.8% | 0 | $26.55 | 0 of 8 |
| hold | 3x | -$246.03 | -$757.61 | -89.5% | 0 | $53.10 | 2 of 8 |
| hold | 5x | -$29.45 | -$976.72 | -96.5% | 2 | $99.53 | 2 of 8 |
| dial B | 1x | $132.07 | $114.40 | -9.8% | 0 | $0.00 | 0 of 8 |
| dial B | 2x | $241.98 | $168.89 | -18.5% | 0 | $9.20 | 0 of 8 |
| dial B | 3x | $339.59 | $175.53 | -26.4% | 0 | $18.12 | 0 of 8 |
| dial B | 5x | $499.53 | $68.37 | -39.9% | 0 | $35.19 | 0 of 8 |
| dial C | 1x | $132.51 | $115.87 | -8.1% | 0 | $0.00 | 0 of 8 |
| dial C | 2x | $252.25 | $182.91 | -15.5% | 0 | $6.59 | 0 of 8 |
| dial C | 3x | $364.56 | $205.72 | -22.3% | 0 | $14.32 | 0 of 8 |
| dial C | 5x | $561.72 | $126.86 | -35.0% | 0 | $33.55 | 0 of 8 |

## What it shows

- 6 of 6 models were ahead of holding at 1x. In 6 of 6 the side of holding was the same at every multiple. Leverage made the gaps bigger in dollars; it did not turn a gap around.
- Holding over all 8 months, summed: -$64.31 at 1x; -$155.17 at 2x (0 close-outs, 0 months below); -$246.03 at 3x (0 close-outs, 2 months below); -$29.45 at 5x (2 close-outs, 2 months below).
- Holding, one account carried: -$148.65 at 1x; -$442.77 at 2x; -$757.61 at 3x; -$976.72 at 5x. The summed figure at high multiples looks better than the carried one because each month starts again from a full account, which a real account does not.
- The models' worst month drop: between -10% and -15% at 1x, between -44% and -65% at 5x.
- One account carried, at 1x and at 5x: Claude Opus 5.5 $81.04 and -$293.80; GPT-6.2 Sol $87.33 and -$130.71; Gemini Neon -$14.55 and -$484.03; Claude Sonnet 5.5 $89.96 and -$316.89; Kimi K3 -$22.54 and -$460.29; Grok 4.7 $111.86 and -$13.74.
- The gain at a multiple is not the 1x gain times the multiple: financing, close-outs and the month-by-month reset take from it, and a month closed out at a low does not get the rebound.
- The models chose their dials for a 1x account. A model that knew it was leveraged might have chosen otherwise. This replay cannot say how.

## What it does not show

- Eight months of one coin. A different stretch could show more or fewer close-outs.
- Funding is the stored perpetual rate applied to borrowed dollars only. A real perpetual contract charges it on the whole position, and a real broker's margin rate differs.
- Close-outs are assumed at the minute's low, less a fixed penalty. A real exchange may close out in parts, earlier or later.
- Fills are assumed from recorded minute bars.

## Files

- `timemachine/leverage_replay_tm03.py` writes this page and `timemachine/leverage_replay_tm03.json`.
- `timemachine/weights.py`: the book with `max_gross`, financing and the maintenance rule (`lev_scan`).
- `timemachine/dial_rules_tm03.py`: dials B and C.
