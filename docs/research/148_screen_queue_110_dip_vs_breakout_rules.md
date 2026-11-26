# Queue 110: dip gate against breakout gate, screen before prices

MEASURED on made-up data, 2026-11-26 12:42 UTC. Close queue 110 and ledger 216 before prices. The only defensible outside size for the judged comparison is about zero: +0.19% a week in favour of the losers, with t = -0.13 for winners minus losers, in the 30 largest coins from August 2020 to December 2023. At that size the synthetic pass rate on all marks is 2.11%, under the 5% zero-edge rate the marks allow and far under the 33% line. Even the most generous outside size, which favours the breakout gate, reaches 33% only when the most generous entry counts and the least noise are put together (43.65%). No bars, prices, gate-open counts or held-back data were read. Published figures below are STATED, not fresh scores.

## The rule, written before any return

STATED. These are the terms a scored run would freeze. Nothing here has been run on prices.

- Universe: the 77 Binance USDT spot pairs listed in the off-repo Replay 22 manifest (rig/data/replay_22/manifest_22.json) (2,044 hourly monthly archives, 2019-11 to 2026-10, already held; MEASURED from the manifest's file names only). Each month's coin list is that month's top 30 from the Replay 13 snapshots, as in [Replay 22](137_replay_22_fable_rule_a.md), with the same identity and missing-hour exclusions. No new pull.
- Window: 2020-01-01 to 2026-04-01, end not included. This is Replay 22's judged window. It ends before the months the Fable rule was read from (2026-04-01 to 2026-10-26) and before the months the AI traders were tested on.
- Print: once a day at 00:00 UTC, on the close of the 23:00 hourly bar.
- Dip gate: the close is at least 5% below the close 168 hours earlier, and the close is no more than 3% above the lowest hourly low of the 336 hours ending at the print.
- Breakout gate: the close is above the highest hourly high of the 168 hours ending 24 hours before the print (hours t-192 to t-24).
- Entry: buy at the next hourly open. Each gate keeps its own book. A gate takes no new entry on a coin it already holds. Both gates may hold the same coin at once.
- Exit, the same for both gates: sell at the hourly open 168 hours after entry. No stop and no target. The outside evidence is all one-week holds, and a stop or target would break the link to it.
- Costs: 70 bp a side on every entry and exit. That is 60 bp taker at the [Kraken Pro](https://www.kraken.com/pro/fees) tier 2 rate (30-day spot volume of $2,500 or more), plus the repo's 10 bp crypto half spread (`tm_crypto_half_spread_bps`). Tier 1, for a new account, charges 80 bp taker ([Kraken Pro](https://www.kraken.com/pro/fees)). Binance itself is not open to a US account, so its prices stand in for a US venue's.
- Each entry's return is market-adjusted. Its net 168-hour return minus the equal-weight return of that month's eligible list over the same 168 hours. The list is a paper benchmark with no cost.

## The one judged comparison

STATED. For each calendar week (Monday start, UTC, by entry time) in which both gates open at least one entry, D = the mean market-adjusted net return of that week's dip entries minus the same for its breakout entries. Weeks in which only one gate opens are not judged.

Why dip minus breakout and not each gate against random entries:

- It is the question queue 110 asks: which gate. One comparison means one test, not two.
- The outside evidence is published as winner-minus-loser weekly spreads among large coins, so its size maps onto D directly. Nothing published measures either gate against random entries.
- Replay 22 already measured a breakout-type rule against random entries: 57% of twins did as well or better ([doc 137](137_replay_22_fable_rule_a.md)). Its twin stream could not be rebuilt from the plan text either.
- Both arms pay the same cost per entry against a cost-free benchmark, so the fee cancels in D. The fee choice cannot move the verdict.

The limit of this choice: a pass would show only that one gate beat the other. It would not show that either gate makes money after 140 bp a round trip. That would need its own row.

## Marks and measured zero-edge rate

STATED. All four marks are required. They are two-sided, and the sign of the mean names the winning gate.

- M1: at least 100 paired weeks.
- M2: Newey-West t (lag 2, over paired weeks) at least 2.21 in absolute value.
- M3: the mean keeps its sign after the 1% of weeks (rounded up) most favourable to it are dropped.
- M4: the winning sign holds in at least 4 of the 7 calendar years 2020 to 2026.

MEASURED on synthetic data. The cutoff started at 1.96 and was raised by 0.01 until the zero-edge pass rate on all marks was at most 5% in all 24 null cases: 2 count cases, 3 noise levels and 4 noise shapes (normal, t with 3 degrees of freedom, shared part doubled, and a rare 250-point week). The cutoff is 2.21. The worst zero-edge rate is 4.89% (generous counts, Fičura noise, shared part doubled). The central case at Grobys noise is 3.38%. M3 and M4 barely bind; nearly all of the pass rate comes from the t.

## Effect size from outside the traded months

STATED, published, large coins, sample after 2018:

| Source | Universe and window | Weekly winner minus loser | Where |
|---|---|---|---|
| Grobys, Kolari, Sandretto, Shahzad and Äijö, FMPM 39, 443-476 (2025) | Top 30 by market cap each year, 30-day sort, 1-week hold, Aug 2020 to Dec 2023 | -0.19%, sd 20.21, t -0.13 | Table 1 p. 450, Table 2 p. 451 ([Springer](https://link.springer.com/content/pdf/10.1007/s11408-025-00474-9.pdf)) |
| Same | Jan 2016 to Jul 2020 | +1.74%, sd 14.42, t 1.85 | Same tables |
| Same | 2016 to 2023, 416 weeks | +0.90%, sd 17.20, t 1.06 | Same tables |
| Fičura, FFA Working Paper 3/2023 | Market cap of $50M or more and prior-week volume of $5M or more, 1-week sort, 1-week hold, Jun 2017 to Dec 2022 | +1.36% (Q1 -0.20%, Q5 +1.15%), Newey-West t 2.33 | Table 3; printed page numbers not shown ([PDF](https://quantitative.cz/wp-content/uploads/2023/09/impact_of_size_and_volume_on_cryptocurrency_momentum_and_reversal.pdf)) |
| Zaremba, Bilgin, Long, Mercik and Szczygielski, IRFA 78, 101908 (2021) | Biggest 2% by market cap, last-day sort, daily, 2015 to Mar 2021 | +0.22% a day high minus low, p 0.171 (value-weighted) | Table 7 Panel B, p. 12 ([PDF](https://www.wir.ue.wroc.pl/docstore/download/UEWR135bdc5e34ad49868fe8a5e77fa021c7/Mercik_Up_or_down_Short-term_reversal.pdf)) |

STATED. None of these papers finds that the largest coins reverse over a week. Where the evidence leans at all, it leans toward momentum, which favours the breakout gate: Fičura finds weekly momentum in large liquid coins, and Zaremba finds daily momentum in the biggest 2%. On the same top-30 universe in the regime closest to our window, Grobys finds nothing (t -0.13). Fičura says plain momentum "seems to have stopped in the early months of 2021". Grobys reports that one week of -255.28% decides whether the full-sample mean is significant ([Springer](https://link.springer.com/article/10.1007/s11408-025-00474-9)). No paper tests these exact gates.

STATED, from our own scored replays (published pages only, nothing rerun):

- [Replay 22](137_replay_22_fable_rule_a.md), a 21-day breakout rule on the monthly top 30, 2020 to March 2026. It ended at +275.40% against +274.25% for holding the same list, and 57% of the random-entry twins did as well or better. Breakout entries were indistinguishable from random entries.
- [Replay 13](54_replay_13_year_or_method.md) rule B, buying 5% dips in rising hot coins with a 24-hour exit. It was under the random-five mark in all 7 years. Rule A, holding last week's hot five, beat all coins in 5 of 7 years and the random mark in 5. It was only a little above that mark in 2020 and 2021. That is a weak weekly momentum lean, not a size. Replay 13's 2026 runs to November and so overlaps the traded months; 2020 to 2025 do not.
- [Replay 17](57_replay_17_short_the_peak.md), shorting after a peak. On the held list it lost at judged costs in 5 of 7 years. Rises did not reverse enough to pay.

STATED. Taken together, the replays imply no dip-over-breakout size, and at most a small lean toward breakout. They give no number that could be planted.

The defensible size used for the line is the Grobys August 2020 to December 2023 figure: +0.19% a week for dip minus breakout (losers minus winners), on the coin universe that matches ours, in the regime that overlaps our window, from a peer-reviewed table with a page number. Fičura's -1.36% (favouring breakout) is shown as a generous sensitivity, not used for the line. It is a working paper. Half of its sample is before our window. Its size filter is far wider than the top 30. And its sign is not found on the top 30 after mid-2020.

## Power on made-up data

STATED, assumed entry counts, not counted from bars. Central case: the dip gate opens in 55% of weeks with 4 entries on average, and the breakout gate in 70% of weeks with 6 entries. That is about 114 dip and 218 breakout entries a year, and 125.5 paired weeks on average (MEASURED in the simulation). Generous case: both gates open in 80% of weeks with 10 entries each, about 416 entries a year per gate and 208.5 paired weeks.

STATED, the noise model. The weekly sd S of D is taken from a published spread: 20.21 (Grobys, Aug 2020 to Dec 2023, central), 14.42 (Grobys, 2016 to Jul 2020), or about 9.9. The 9.9 is backed out of Fičura's mean and t over about 291 weeks; it is rough, because his t is Newey-West. Half of the variance is a shared weekly part, with AR(1) 0.3 across weeks for the overlapping holds. The other half shrinks with entry counts, scaled so that 6 entries a side gives S. These are assumptions.

MEASURED on synthetic data, 20,000 worlds per case. The table shows the rate of passing all four marks with the right sign, with a normal shape (t3 in brackets).

| Planted D, % a week | Counts | S = 20.21 | S = 14.42 | S = 9.9 |
|---|---|---:|---:|---:|
| +0.19 (Grobys 2020-23, defensible) | central | 2.11% (2.16%) | 2.51% (2.25%) | 2.65% (2.55%) |
| +0.19 | generous | 2.73% (2.80%) | 3.01% (3.16%) | 3.76% (4.03%) |
| -0.90 (Grobys 2016-23) | central | 4.54% (4.87%) | 6.51% (6.77%) | 10.51% (11.81%) |
| -0.90 | generous | 7.56% (7.80%) | 11.48% (12.56%) | 21.07% (23.47%) |
| -1.36 (Fičura 2017-22) | central | 7.12% (7.50%) | 10.52% (12.10%) | 20.21% (23.52%) |
| -1.36 | generous | 12.88% (13.51%) | 21.89% (24.89%) | 43.65% (47.07%) |

MEASURED. The planted size needed for 33% power, favouring breakout, normal shape: 3.8% a week in the central case at S = 20.21, 2.6 at 14.42, and 1.8 at 9.9. In the generous case: 2.4, 1.8 and 1.2. Every one is above every published large-coin figure after 2018 except Fičura's in its most generous corner. The quick screen in [doc 117](117_power_screen_before_data.md) agrees: 125.5 × (0.19 / 20.21)² = 0.011, against about 4 needed for 50%.

## Verdict

- MEASURED: power at the defensible size is 2.11% in the central case, and 3.76% at the most generous counts and least noise. Both are under 33%. Close queue 110 and ledger 216 before prices.
- STATED: this means the held history cannot settle dip against breakout at the size outside evidence supports. It does not mean either gate loses. To revisit it, a published post-2020 large-coin weekly spread of about 2% or more would be needed, or a design with far less weekly noise.
- UNKNOWN: real gate-open counts (not taken, by rule), how well quintile sorts stand for these gates, and the true noise of D.

## Reproduction

```sh
nice -n 10 python3 -B research_rig/power_110.py | cmp - research_rig/POWER_110.json
```

MEASURED. It reads no files, seeds from 110001, and runs in about 10 minutes on one core. Script SHA-256 `98f13a1f48a2169efaccdedf23f6f0146c8f36d885b796570e3d608a4df1b7a2`. Output SHA-256 `ab0c6392514476c0853f23dba626363ee466abd6d1669515f99c818ced7162a6`.
