# Replay 24: same-coin funding carry

MEASURED. Replay 24 **did not pass**, meeting **1 of 5 marks**. Only the drawdown mark was met. The $500 account ended at $500.88, or +0.036% a year after the judged Robinhood fee model. Daily Sharpe was 0.038; the largest fall was 6.75%. Only 174 of 500 random twins matched, so the twin mark was not computed and not met.

STATED. The [frozen plan](../../research_rig/PREREG_24_same_coin_carry.md) buys spot and shorts the same coin's perpetual in equal dollars at entry. It uses up to 5 sleeves, sized only once, enters at a lagged seven-day funding rate of at least 20% annualized, and exits at 5% or less or on loss of eligibility. Binance supplies the replay prices and funding; US historical funding and actual fills are UNKNOWN. All dates, from 2022-01-01 00:00 through the 2026-10-26 00:00 UTC cutoff, were already viewed in [Replay 18](65_replay_18_funding_carry.md). There is no held-back period.

## Marks and account result

| Frozen mark | MEASURED | Verdict |
|---|---:|---|
| Net gain at least 6% a year | +0.036% | not met |
| Daily Sharpe at least 1.0 | 0.038 | not met |
| Largest fall at most 10% | 6.75% | met |
| Positive in 4 of 5 UTC years | 2 of 5 | not met |
| Strictly above the 95th percentile of all 500 twins | not computed | not met |

MEASURED. Funding added +8.66 percentage points of starting money. The difference between the spot and perpetual price moves contributed -4.89 points and fees -3.60 points, leaving +0.18% net for the whole window. The book was in the market 24.07% of the time, with 30,827 coin-hours and 95 paired trade events, including 61 margin top-ups and 1 forced close. A paired entry, exit or maintenance order counts once, not once per leg.

| UTC year | Net gain | Paired trade events |
|---|---:|---:|
| 2022 | +0.000% | 0 |
| 2023 | +0.456% | 36 |
| 2024 | -0.282% | 58 |
| 2025 | +0.003% | 1 |
| 2026, partial | +0.000% | 0 |

## Gaps and the random comparison

MEASURED. The approved scope covered 78 coin identities over time and 64 dated perpetual listings, of which 58 had an approved spot link. 6 dated listings lacked an approved link: CCUSDT, ETHUSDT, FTTUSDT, KASUSDT, MANTRAUSDT, MUSDT. That includes ether; the shown bitcoin/ether row is bitcoin only. This is a limit of the reviewed inputs, not a claim that the products did not exist.

STATED. The approved older spot records did not supply the matching coin identity for CCUSDT, ETHUSDT, FTTUSDT, KASUSDT, MUSDT. For MANTRAUSDT, the approved notes give a separate reason: the old OM spot window could not be reused across the token redenomination.

MEASURED. There were 1,468 otherwise eligible fresh name-days without a complete as-of funding signal; none used a slot. Among ranked slots already assigned, 0 were blocked by missing bars or funding and 0 by a retrospective link end. There were 0 unfilled assigned entry slots in all and 0 charged missing settlements during holds. These counts do not erase the known archive gaps listed in the plan.

MEASURED. 326 of 500 random draws were refused. The plan required each draw to match the ranked book's number of holdings and additions after every daily fill, and its total coin-hours. A random book can still hold names that fall out of the available list on a day when the ranked book keeps its names. With too few available positions to keep, or too few fresh names to add, the draw cannot match.

| Saved refusal reason | Draws |
|---|---:|
| twin cannot match the ranked count and turnover as of decision | 326 |

MEASURED. The saved refusals do not split how many failed for too few continuing names versus too few fresh names, or identify the affected dates. No draw was rerolled and the valid draws were not used on their own. There is no measured percentile or claim that the book beat randomness.

## Shown only

STATED. The judged Robinhood model charges 95 bps per spot order, 0.5 bps perpetual commission with a $0.01 minimum, and a 0.5 bps venue fee. The replay applies the frozen rounding rules to each executed order. These are fee assumptions, not measured execution prices.

MEASURED. At zero fees, the same rule made +0.8% a year. The highest tested flat cost with a strictly positive gain was 40 bps per leg per side. This is a grid point, not an estimate between points or a quote for a real fill.

| Shown variant | Net gain per year |
|---|---:|
| Kraken stated fee model | +0.003% |
| Flat 5 bps per leg per side | +0.723% |
| Coinbase | UNKNOWN fee, excluded |
| Entry at 10%, Robinhood model | -4.938% |
| Entry at 30%, Robinhood model | +0.117% |
| Bitcoin only; ether unavailable, Robinhood model | +0.146% |

| Flat bps per leg per side | Net gain per year |
|---:|---:|
| 0 | +0.800% |
| 1 | +0.784% |
| 2 | +0.769% |
| 5 | +0.723% |
| 10 | +0.647% |
| 20 | +0.495% |
| 40 | +0.190% |
| 80 | -0.418% |

## Run record

MEASURED. The owner validated the inputs first with 0 hard refusals, then the one-shot claim opened at 2026-11-26 03:46 UTC and the result was written at 2026-11-26 03:49 UTC. The approval commit was `c875d58012c20b1ed2af295c25de79e529fe4d23`. The seal SHA-256 was `2970297e16baeedb70fa9c56b62f3651c3a28c66048061c83c5b35951a092fbc`.

MEASURED. An earlier start refused in authorization before a claim because the owner's shell supplied `GIT_` variables. It never opened the replay or produced a result; it was not a run.

The saved off-repo result SHA-256 is `f2f55bf58eff77760930e12cce52d3de0159becf493354d80c93303235802059`. The [report script](../../research_rig/report_24.py) generates this page from that result, the bound policy and the run records. No market tape, detailed schedule or saved result JSON is in the repo.
