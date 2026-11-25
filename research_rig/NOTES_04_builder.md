# Replay 04 builder notes (2026-11-25)

Status: research rig, not the product. Written by the builder agent after the run. Plan: `PREREG_04_coin_basket_trend.md`, measured per `AMENDMENT_2026-11-25_audit_fixes.md`. Output: `results_04.json`, log `run_04.log`. Nothing was tuned. The only settings run besides the base run are the two the plan names (50 bps alt slippage, 0.5 delist haircut), stored under `sensitivity`.

## Verdict in one line

No rule passes at any venue. Mark 3 (deflated Sharpe > 0.95) fails for every rule at every venue. The three wide-basket rules (K1, K2, K3) do worse than holding bitcoin in the held-back slice at every venue. They also lose money in that slice at every venue except Binance.US (where K1 and K3 make about 2.6% a year). K4 (bitcoin and ether, P1) and K5 (bitcoin, CoinDesk-style) are the only rules close to bitcoin.

## Faults found and reported to the lead before the run

- `basket.simulate_basket` trades on any move to or from zero, whatever the band. That is the old `engine.py` behaviour, and `fixtures_basket.py` check 1 tests against the old engine. Amendment A12 and `fixtures2.py` check 20 say there is no such exception. The lead agreed to this fix: `simulate_basket` is left unchanged, and a new `basket.sim_batch` (alias `simulate_basket2`) uses the literal band. The only exceptions are the two cases the plan words as "is sold": a pair that leaves its basket, and a pair whose history ends.
- A04 dust: a buy that ran short of cash did not set cash to exactly zero. Fixed in the new engine.
- Size of the band change: the old exception would have fired on 0 pair-days in every base run (`old_exception_would_fire_pair_days` = 0 for all rules and venues). The change makes no difference to these results.

## Plan points that could not be followed literally, or behaved differently from what the plan says

- File count: the plan says 760 files. 753 pairs are used. 129 files end before 2026-09-25, as stated. Corrected after the audit (finding 04-05): I first wrote that the 7 left out are all files quoted in PYUSD or RLUSD. That is wrong. 3 are (ETHPYUSD, XBTPYUSD, XRPRLUSD). MERLUSD is the real Merlin Chain/USD market, wrongly left out by the name-suffix test in `basket.OTHER_QUOTE`. CTUSD, OUSDUSD and WOJAKUSD have one row and are dropped by the length check. The auditor measured that restoring MERLUSD changes no monthly list.
- The peg test does not always remove gold tokens. PAXGUSD's 90-day volatility was above 0.20 in some months. It entered the top 20 in 12 months (2020-06, 2020-09, and 2025-12 to 2026-09) and the top 10 in 2026-04 and 2026-05. XAUTUSD was dropped as a copy of PAXGUSD. This is the plan's test applied as written. The plan's description of what it removes is not fully true.
- No position was ever closed because its history ended (forced exits = 0 for every rule, venue and sensitivity). So the 0.5 haircut sensitivity is identical to the base run, and it tested no real loss from a dead coin. Corrected after the audit (finding 04-06): I first wrote that every pair that died had already failed the activity test and left its basket at an earlier month start. That is wrong. RNDRUSD (last print 2024-06-30) was still chosen on 2024-07-01, and FTMUSD (last print 2025-03-31) on 2025-04-01. Neither had an open position at the time. Pairs that were held and later died: K1 and K2 held 3 (EOSUSD, FTMUSD, MATICUSD), K3 held 7 (adds ICXUSD, REPUSD, RNDRUSD, WAVESUSD). Corrected after the audit: I first wrote that most of these are renames or migrations. That was not measured and is withdrawn (UNKNOWN).
- K3 (top 20): in 22 of the 100 months fewer than 20 pairs qualified (the minimum was 13). K3 holds what qualifies, still one twentieth each.
- The one-hour-late fill (A13) is not part of plan 04 and was not run. Mark 1 uses the base fill only, as `run_05` does.
- "Break-even, shuffles and marks apply to single-coin trials only" (A09) conflicts with plan 04, which asks for marks on basket rules. The plan 04 wording was followed.

## Reading choices (also in `results_04.json` under `reading_choices`)

- A filled-in day (no row in the raw file) has a nan open, so nothing fills and the order waits. The close is carried forward for valuation and signals, and dollar volume is 0. Every raw row has volume above zero (checked on load).
- Membership for the month starting on day D uses rows before D only.
  - History: at least 200 calendar days from the first bar to D-1 inclusive.
  - Activity: at most 10 of the 90 days D-90..D-1 have no raw row. Days after the last bar count as days without trades.
  - Peg test: standard deviation (ddof 1) of the 90 close-to-close returns, times the square root of 365, below 0.20.
  - Copies: among pairs that pass the first three tests, ranked by median dollar volume over the 90 days (zero on non-traded days), a pair is dropped if its return correlation with any higher-ranked pair is above 0.98.
  - Ties go by pair name.
- Start: 2018-06-01, the first month start with 10 or more qualifying pairs (13 qualified). The calendar starts 2018-05-31 with all cash, so the first fills are at the open of 2018-06-01.
- The target at the close of day t uses the membership of the month containing t+1. A pair leaving the basket is sold at the first traded open of the new month.
- P1 = `rules.p1` (it matches the requested definition, with closes strictly above the average) on each pair's own filled calendar. nan (warm-up) counts as 0.
- K2: the top 5 of that month's top 10 by return over the 90 days known before D (close D-1 over close D-91). K4: XBTUSD and ETHUSD, half each. K5: XBTUSD with a slot of the whole account, set at the close of the bar dated Wednesday (UTC weekday 2) and held otherwise. Between Wednesdays the 1/8 band still applies against drift, as written.
- Band = slot/8, compared with the weight as a share of the whole account. Buys are sized as target times account minus holding, with costs on top. When cash is short, every buy that day is scaled down by the same share.
- Hold bitcoin is bought once at the first traded open. Hold the basket is traded with band 0 at each month start, with each order waiting for its pair to trade, and is not traded in between. Both pay the same per-pair costs. Corrected after the audit: I first wrote, here and in `reading_choices` in `results_04.json` (not rerun), that it is rebalanced exactly. It is not exactly equal parts after costs, because sizes use the account value before costs (finding 04-02; largest gap 0.00046541 of the account at Binance.US). A buy order is also cleared once its pair trades, even if it could not be funded (finding 04-03; did not happen in this run).
- Break-even uses the run_v2 convention, where c is the full per-side cost of bitcoin. XBTUSD and ETHUSD pay c, other pairs pay c + 20, and the benchmark pays the same. Mark 2 compares the break-even with the venue fee + 5 bps. Searched vs hold bitcoin (used by the marks), vs hold the basket (used by `marks_vs_basket`) and for zero growth.
- Deflated Sharpe uses 49 trials, with the spread taken as the ddof 1 standard deviation of K1..K5's per-day Sharpe at that venue. The overfitting estimate uses 16 equal blocks, dropping the earliest rows (verdict, 4 rows dropped) and also the latest. The bootstrap uses `rig2` defaults (block 30, 2,000 draws, seed 7). All of these use whole-test daily returns.
- Shuffles: a fresh seed-7 generator per rule per venue.
  - In each draw, each pair the rule can hold (in column order) has its own P1 (or the Wednesday-held K5 weight) shifted by `R.null_circular` (shift of at least 30) inside that pair's own rows in the test.
  - Membership, slots and band stay as they were.
  - No pair was too short to shift.

## Checks added to `fixtures_basket.py` (all pass; it now exits with an error on any failure)

| # | Check | Result |
|---|---|---|
| 8 | Batched engine with the old exception equals `simulate_basket` on 300 random inputs (1 to 6 coins, untradable opens, delistings, haircut, costs), and batched rows equal single runs | PASS, largest gap 2.2e-15, batch gap 0 |
| 9 | With the literal band, one coin at zero cost equals `rig2.simulate` with bars that cannot fill, on 300 inputs | PASS, gap 1.3e-15 |
| 10 | A drifted position with target zero is kept inside the band, sold when the pair leaves the basket; the old-exception counter counts it | PASS |
| 11 | No trade on the fill day: the order waits, then fills at the next traded open with the newest target; the wait is counted | PASS |
| 12 | The hold benchmark is bought once and never traded again | PASS |
| 13 | Membership is unchanged when all data from the selected month on are changed (and does change when data before it change) | PASS |
| 13b | Membership filters on a hand-made panel: copy, peg, inactive and young pairs are left out | PASS |
| 14 | K5 weights: 1 on a rising series, 0 on a falling one, equal to a hand loop on a random series, nan before 180 closes | PASS |
| 14b | K5 takes values in between and changes only on Wednesdays | PASS |
| 15 | The circular shift keeps each coin's time in market (same values inside its span) and leaves other rows alone | PASS |

`run_04.py` runs `fixtures2.py` and `fixtures_basket.py` first and stops unless both exit 0 and print ALL PASS.

## Runtime facts

- Full run: 367 s on 4 fork processes, while `run_05.py` was using 3 CPUs. Data load and membership took about 6 to 11 s.
- 1,000 shuffles take about 40 s per rule per venue, using the batched engine (50 draws at a time).
- The calendar runs from 2018-05-31 (cash only) to 2026-09-30, 3,045 rows. 84 pairs are in the panel, 39 were ever in a top 10, 84 ever in a top 20, over 100 months.
- Determinism: the full run was repeated with identical settings (413 s). results_04.json was identical apart from runtime_seconds; the sha256 of the output without runtime was 8e34b353aac7231d both times.

## Headline numbers, held-back slice 2023-01-01 to 2026-06-30

Growth is a year (CAGR). Drop is the largest drop. Marks are against hold bitcoin; pass marks are read from `config/thresholds.yaml`: drop ratio ≤ 0.6, break-even ≥ 2× cost, deflated Sharpe > 0.95, overfitting < 0.25, shuffle > 0.95.

### Kraken $10k tier (38 bps fee; 43 bps bitcoin and ether, 63 bps others)

Hold bitcoin: 43.5% a year, Sharpe 1.00, drop -53.1%. Hold the basket: -2.5% a year, Sharpe 0.31, drop -80.3%.

| Rule | Growth | Sharpe | Drop | Sharpe vs hold BTC | Sharpe vs hold basket | m1 | m2 | m3 | m4 | m5 | Passed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| K1 | -6.0% | 0.02 | -62.1% | -0.98 | -0.29 | no | no | no | yes | yes | no |
| K2 | -11.8% | -0.06 | -73.4% | -1.06 | -0.37 | no | no | no | yes | yes | no |
| K3 | -5.9% | 0.01 | -62.6% | -0.99 | -0.30 | no | no | no | yes | yes | no |
| K4 | 23.3% | 0.80 | -33.6% | -0.21 | +0.48 | no | yes | no | yes | yes | no |
| K5 | 33.0% | 1.04 | -34.7% | +0.03 | +0.72 | no (drop ratio 0.65 > 0.6) | yes | no | yes | no | no |

### Binance.US (2 bps fee; 7 bps bitcoin and ether, 27 bps others)

Hold bitcoin: 43.5% a year, Sharpe 1.00, drop -53.1%. Hold the basket: -1.4% a year, Sharpe 0.33, drop -79.9%.

| Rule | Growth | Sharpe | Drop | Sharpe vs hold BTC | Sharpe vs hold basket | m1 | m2 | m3 | m4 | m5 | Passed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| K1 | 2.7% | 0.26 | -56.7% | -0.74 | -0.07 | no | no | no | yes | yes | no |
| K2 | -2.6% | 0.16 | -68.3% | -0.84 | -0.17 | no | no | no | yes | yes | no |
| K3 | 2.6% | 0.25 | -57.4% | -0.75 | -0.08 | no | no | no | yes | yes | no |
| K4 | 32.9% | 1.02 | -29.7% | +0.02 | +0.69 | yes | yes | no | yes | yes | no |
| K5 | 37.1% | 1.13 | -33.3% | +0.13 | +0.80 | no (drop ratio 0.63 > 0.6) | yes | no | yes | no | no |

## Other facts worth reading

- Break-even vs hold bitcoin (venue-free): K1, K2 and K3 are never ahead, even at zero cost. K4 is 88.9 bps and K5 88.2 bps, so mark 2 passes up to Kraken $10k tier (2 × 43 = 86) and fails at Kraken entry and Coinbase.
- Deflated Sharpe at Kraken $10k tier: K1 0.25, K2 0.14, K3 0.19, K4 0.80, K5 0.70. At Binance.US the best is K4 at 0.93, still below 0.95.
- Overfitting estimate (pbo, ties counted as overfit): 0.11 at Kraken $10k tier and 0.10 at Binance.US. Its range across venues is 0.07 to 0.11, with tie share 1.6% to 2.7% and the drop-latest variant within 0.005. The five trials are not many and are strongly related, so a low number here says little.
- Shuffled timing percentiles are high for K1..K4 (0.97 to 1.00) and 0.91 to 0.92 for K5. The shuffles of the P1 rules trade a little less and hold a little less than the rules do: K1 at Kraken $10k tier makes 6,535 trade sides against a shuffle mean of 6,257, with average weight 0.452 against 0.423. Corrected after the audit (finding 04-04): I first wrote that this shows the timing beats random timing within the same membership, and that the membership is what loses against bitcoin. The second part was a cause I did not measure, and the first is too strong. The shuffles are not matched on time in the market or trade count, because membership is applied after the shift, so mark 5 means less for K1 to K3. For K5 the shift also moves Wednesday signals to other weekdays. The auditor measured 0.919 with the weekday kept, against 0.914 as run at Binance.US; both fail.
- Bootstrap 5/50/95% of the Sharpe difference vs hold bitcoin at Kraken $10k tier: K1 [-0.93, -0.37, 0.15], K4 [-0.25, 0.16, 0.60], K5 [-0.32, 0.05, 0.45]. Against hold the basket, K4's whole range is above zero ([0.05, 0.49, 0.92]).
- Turnover is high for the P1 rules: about 19 to 25 times the account a year (K5 about 8). Average coins held: K1 6.8, K2 3.8, K3 12.7, K4 1.5, K5 0.74.
- Marks vs hold the basket (reported, not the verdict): K4 and K5 pass m1 at every venue, but every rule still fails m3. K5 also fails m5.
- Sensitivity, 50 bps alt slippage: K1..K3 lose about 0.11 to 0.16 more Sharpe in the held-back slice at every venue. K4 and K5 are unchanged, because they hold bitcoin and ether only. The delist haircut changes nothing (no forced exits), so it tested no real loss.
- Post-cutoff slice (2026-07-01 to 2026-09-30, at Kraken $10k tier): hold bitcoin +42.8%, hold the basket +65.8%, K1 +29.8%, K2 +45.3%, K3 +32.8%, K4 +26.3%, K5 +9.5%.
- Calendar years, Kraken $10k tier, for K1 / hold bitcoin / hold the basket:
  - 2018 (from June): -24% / -51% / -69%
  - 2019: +21% / +94% / +12%
  - 2020: +78% / +304% / +189%
  - 2021: +133% / +59% / +304%
  - 2022: -41% / -64% / -75%
  - 2023: +36% / +156% / +133%
  - 2024: +23% / +121% / +45%
  - 2025: -42% / -6% / -55%
  - 2026 (to 2026-09-30): +7% / -5% / 0%

## After the independent audit (added 2026-11-25)

The audit is `../audit/2026-11-25_replay_04_audit.md`. It has 15 findings. Its own rebuild matches K1, K4 and both benchmarks to about 1e-15. None of the changes it tested produced a pass against hold bitcoin. The lead decided not to change `basket.py` and not to rerun tonight. The result stands as run, and these faults are stated:

- 04-01: the forced-exit code uses each pair's last bar from the full archive, which is hindsight. It never fired (zero forced exits). It must be fixed before `basket.py` is used again.
- 04-02: trade sizes use the account value before costs. The auditor measured that sizing on the value after costs changes things only slightly. Hold-the-basket held Sharpe goes from 0.328049 to 0.327906 and K1's from 0.258361 to 0.262360. K4's Binance.US deflated Sharpe goes from 0.9331335 to 0.9332411, still a fail.
- 04-03: the monthly benchmark can clear an unfunded buy. It did not happen here.
- 04-04: the shuffles are not matched on exposure or trade count. See the corrected line above.
- 04-05, 04-06, 04-07: the file count, the dead pairs and PAXG. See the corrected lines above.
- 04-09: on an exactly flat window K5's two averages tie and round differently. The auditor measured weight 0.50 instead of 1.00 at a constant 100, and 0.75 at a constant 5. Check 14 leaves the flat case out on purpose (comment in `fixtures_basket.py`), but I did not report it as a fault in `basket.py`. I should have. The auditor found no effect on real bitcoin data.
- 04-13: trial ledger rows were missing when the run was made. The lead has added rows 43 to 55. The determinism line above is now filled in with a measured repeat.
- 04-15: the P1 calendar ends at the pair's last raw bar, which is known only from the full archive. That changed 18 K3 target pair-days in the auditor's probe, with no effect on equity.
- Closest miss: K4 at Binance.US fails only mark 3 (deflated Sharpe 0.933). A near miss is a fail.
- Doc 23 (`docs/research/23_replay_04_coin_basket.md`, built by `build_doc23.py`) carries these points.
