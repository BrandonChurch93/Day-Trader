# Where We Stand After 32 Scored Tests

Date: 2026-11-26 UTC. Plain synthesis for the owner. Every figure below is copied from `research_rig/TRIAL_LEDGER.md`, `docs/STATUS.md`, `docs/QUEUE.md`, and the cited result documents; no return was recomputed. Claims are labeled MEASURED (from our own runs), STATED (from plans, schedules, or external sources cited in repo docs), or UNKNOWN (not yet measured).

## 1. Every Scored Test So Far

Thirty-two scored tests (trading replays, AI time-machine evaluations, and the opening-range fill gate that killed a strategy before replay) have been completed or scored on a design sample. Two counted trading replays passed their frozen marks: Replay 25 (US $500 reachable) and Replay 20 (not US-reachable). Diagnostic measurements on already-tested windows (Measurement 27 TLT closing cross in `docs/research/70_measure_27_tlt_closing_cross.md`; Measurement 34 TMF/UBT leverage check in `docs/research/82_measurement_34_tmf_ubt_month_end.md`) and non-trial descriptive looks (Alex Becker calls in `docs/research/46_becker_calls_measured.md`, attention feed in `docs/research/45_attention_feed_measured.md`, governance votes in `docs/research/49_governance_votes_look.md`, and the peak-signal look in `docs/research/61_look_after_the_peak_signal.md`) are not counted as separate strategy trials here.

| # | Test | What it tested (6 words) | Family | US $500? | Result (MEASURED) | Headline net number and source |
|---|---|---|---|---|---|---|
| 1 | Replay 01 (R1) | Daily trend rules on BTC, ETH | momentum | Yes | Failed / not credited (4/90 both feeds) | Pass on both feeds only at Binance.US; knife-edge PBO 0.2409 Kraken vs 0.4205 Bitstamp (`docs/research/16_rig_audit.md`) |
| 2 | Pilot 02 | Six AI daily BTC, ETH calls | AI discretionary | Yes | Inconclusive by design (6 runs) | 147 calls per model; too few days to tell skill from luck (`docs/research/14_ai_calls_pilot_02.md`) |
| 3 | Replay 03 (R1) | Hourly intraday rules on BTC, ETH | chart pattern | Yes | Failed (0/80 combinations pass) | 0 of 80 pass at any venue cost; all lost at Alpaca cost (`docs/research/16_rig_audit.md`) |
| 4 | Replay 04 | Trend rules on wide coin basket | momentum | No | Failed (0/25 combinations pass) | Best K1 +2.7%/yr vs BTC +43.5%/yr; highest deflated Sharpe 0.933 vs 0.95 (`docs/research/23_replay_04_coin_basket.md`) |
| 5 | Replay 05 (R2) | Slow trend on US stock index | momentum | No | Failed / not credited (0 both runs) | Untradable index; late ledger and unapproved rerun; T1 +9.1%/yr vs +11.5% hold (`docs/research/22_replay_05_stock_trend.md`) |
| 6 | Replay 06 | Slow trend on nine tradable ETFs | momentum | Yes | Failed (0/6 pass; best 1/5 marks) | Best G5 +15.4%/yr vs SPY +18.9%/yr on held-back 2023 to 2026 (`docs/research/35_replay_06_fund_trend.md`) |
| 7 | Replay 07 | Intraday one-minute rules SPY, QQQ | chart pattern | Yes | Failed (0/8 SPY, 0/8 QQQ pass) | Highest break-even cost 1.8 bps RT (N2 on QQQ) (`docs/research/27_replay_07_intraday_spy_qqq.md`) |
| 8 | Replay 09 | Seven crypto rules at Alpaca cost | momentum | Yes | Failed (0/7 pass at 35 bps/side) | Best CAP +2.1% vs BTC +1.7% on held-back Jul to Nov 2026 (`docs/research/28_replay_09_crypto_methods.md`) |
| 9 | Replay 11 (design) | AI reads quarterly earnings press releases | AI discretionary | Yes | Design only (held-back 2,146 open) | Sonnet 5.5 H5 +0.97%/trade over all releases, -0.58% vs SPY (`docs/research/44_replay_11_earnings_reader.md`) |
| 10 | Replay 12 | Copy Congress disclosed stock purchases | copy-trading | Yes | Failed (2/5 marks on held-back) | 1.99x vs SPY 2.06x (-1.0%/yr behind SPY) on 543 buys (`docs/STATUS.md`, `research_rig/TRIAL_LEDGER.md`) |
| 11 | Replay 13 Rule A | Weekly hold five hottest large coins | momentum | Yes | Relative marks met, not counted pass | Met 3/3 relative marks vs all coins, yet lost -71.6% (2022), -66.0% (2025), -75.6% (2026) (`docs/research/54_replay_13_year_or_method.md`) |
| 12 | Replay 13 Rule B | Buy 5% dip on hot coins | chart pattern | Yes | Failed (not paid, 0/7 vs random) | Lost 6 of 7 years; 2021 worst at -78.7%, 2025 -65.3%, 2026 -56.7% (`docs/research/54_replay_13_year_or_method.md`) |
| 13 | Replay 14 | S&P 500 twelve-month stock momentum | momentum | Yes | Failed (1/4 marks each) | Top 10 +203.8%, top 50 +207.8% vs SPY +264.6% (`docs/research/52_replay_14_large_stock_momentum.md`) |
| 14 | Replay 16 | Long hot five, short coin futures | momentum | No | Failed (0/4 marks) | 2 of 5 valid years positive; -60.3% in 2022, -21.7% in 2025 (`docs/research/56_replay_16_hot_five_hedged.md`) |
| 15 | Replay 17 | Short hot coins 5% off peak | chart pattern | No | Failed (0/3 marks) | Lost 5 of 7 years even at 0 cost; lost 7 of 7 years on US-shortable list (`docs/research/57_replay_17_short_the_peak.md`) |
| 16 | Replay 18 | Cross-coin perpetual funding rate carry | carry | No | Failed (1/3 marks) | -44.61% net, Sharpe -0.339, max drawdown 57.33% (`docs/research/65_replay_18_funding_carry.md`) |
| 17 | Replay 19 | Monday Asia 24-hour BTC, ETH trend | calendar | No | Failed (1/5 marks) | -53.88% net, Sharpe -0.280, ranked 95th of 168 start hours (`docs/research/64_replay_19_monday_asia.md`) |
| 18 | Replay 20 | Short after Upbit listing red day | event | No | PASSED (5/5 marks, viewed dates) | +3.2088% net/trade across 139 trades, t 2.839, worst -28.8% (`docs/research/71_replay_20_upbit_listing_short.md`) |
| 19 | Replay 23 | Buy large US IPOs before indexing | forced flow | Yes | Failed (7/8 marks) | +2.64% net overall (t 2.66, 218 trades), failed 2023+ mark at -1.42% (42 trades) (`docs/research/72_replay_23_ipo_fast_track.md`) |
| 20 | Replay 24 | Same-coin spot long, perpetual short carry | carry | Yes | Failed (1/5 marks) | $500.88 on $500 (+0.036%/yr), daily Sharpe 0.038, drawdown 6.75% (`docs/research/68_replay_24_same_coin_carry.md`) |
| 21 | Replay 25 | Long TLT last three monthly sessions | forced flow | Yes | PASSED (9/9 marks at 2 bps/side) | +0.2562% net/window across 130 windows, t 2.36 (`docs/research/69_replay_25_treasury_month_end.md`) |
| 22 | Replay 31 | Four bond ETFs month-end residual | forced flow | Yes | Failed (2/10 marks) | Plain +0.1268% (t 3.09), residual -0.0338% (t -1.69) (`docs/research/80_replay_31_bond_fund_month_end.md`) |
| 23 | Replay 33 | Long IEF, TLT on auction afternoons | forced flow | Yes | Failed (3/11 marks, placement only) | -1.457 bp net on 260 auctions (t -0.597), paired gap -2.462 bp (`docs/research/89_replay_33_treasury_auction_days.md`) |
| 24 | Replay 35 | Long IBIT on CME Bitcoin expiry | forced flow | Yes | Failed (1/6 marks) | -0.1626% net on 34 expiries (t -0.72), Friday gap -0.1398% (`docs/research/81_replay_35_cme_bitcoin_expiry_ibit.md`) |
| 25 | Replay 39 | Long IWM session before NYSE holiday | calendar | Yes | Failed (5/7 marks) | +0.1909% net on 102 events at 2 bps/side; net t 1.91 and Welch t 1.82 missed 2.0 (`docs/research/84_replay_39_iwm_pre_holiday.md`) |
| 26 | Replay 41 | Month-end SPY versus TLT laggard switch | forced flow | Yes | Failed (4/8 marks) | +0.2357% net (t 2.29), paired +0.0148% vs always-TLT (t 0.14) (`docs/research/92_replay_41_month_end_laggard_switch.md`) |
| 27 | TM01 | Six AI models trade crypto prices | AI discretionary | Yes | Failed (0/6 beat BTC or twins) | 30 sessions, 600 twins; no model beat BTC or twin mark (`docs/research/29_time_machine_tm01_crypto_price_only.md`) |
| 28 | TM02 | Six AI models trade crypto news | AI discretionary | Yes | Failed trading (0/6 beat BTC/twins) | Headlines beat price-only in 6/6 (+$3 to +$79 on $1,000), still 0/6 beat BTC or twins (`docs/research/30_time_machine_tm02_crypto_with_news.md`) |
| 29 | TM03 | Six AI models set daily BTC weight | AI discretionary | Yes | Failed (0/6 above 90th pct) | All 6 beat falling BTC by holding less; 0/6 beat 90th pct of shuffled answers (`docs/research/34_time_machine_tm03_bitcoin_dial.md`) |
| 30 | TM04 | Six AI models pick eight large stocks | AI discretionary | Yes | Failed (2/6 median, 0/6 90th pct) | 7 of 12 runs lagged equal-weight 38 stocks (`docs/research/36_time_machine_tm04_stock_basket.md`) |
| 31 | TM06-P-g / TM06-R | Fable 5.2 daily hot-coin picker repeats | AI discretionary | Yes | Mixed / did not repeat | Run 1 twin pct 98.8, run 2 96.6 (pass), run 3 84.0 (fail); all 3 negative without May (`docs/research/78_time_machine_tm06r_fable_repeat.md`) |
| 32 | Measurement 15 | Opening-range breakout fills stocks in play | chart pattern | Yes | Failed fill gate (idea dropped) | Entry 0.0757 + stop exit 0.1332 = 0.2089 of stop distance vs 0.05 limit (`docs/research/66_measure_15_breakout_fills.md`) |
| 33 | TM06-P six models | Six AI models pick hot coins daily, eight months | AI discretionary | Yes | Shown by its marks, not counted pass | 5/6 above twin median, 2/6 clear all marks; gains sit in April to June, all six lost July to November and none beat either yardstick there; memory not ruled out (`docs/research/102_time_machine_tm06_six_models.md`) |
| 34 | TM06-S six models | Six AI models trade the owner's swing card hourly, four weeks | AI discretionary | Yes | Failed (not shown, 0/6 clear both marks) | None above holding the five coins (`docs/research/102_time_machine_tm06_six_models.md`) |
| 35 | Replay 21 | Buy below the price of an odd-lot tender offer | event | Yes | Did not pass (4 of 6 marks) | 14 trades from 106 eligible filings, +11.80% mean net, t 1.688; under the floor of 30 trades (`docs/research/97_replay_21_odd_lot_tenders.md`) |
| 36 | Replay 46 Leg A | Altcoins after a CFTC futures filing, long leg | event | Yes | Did not pass (3 of 6 marks) | 43 events on 15 posting dates, -6.5393% mean net, +0.5643% paired versus BTC, t 0.174 (`docs/research/101_replay_46_cftc_altcoin_futures.md`) |
| 37 | Replay 46 Leg B | Altcoins after a CFTC futures filing, short leg | event | No | Did not pass (5 of 6 marks) | 110 events on 31 posting dates, +1.2790% mean net, +0.5574% paired versus BTC, t 0.572; spot-price proxy, not an executable short (`docs/research/101_replay_46_cftc_altcoin_futures.md`) |
| 38 | Replay 48 | Long the five worst muni closed-end funds, last December close to last January close | forced flow | Yes | Passed (7 of 7 marks) | 10 yearly turns, +1.39% mean net per turn against +0.09% for MUB and +0.59% for the roster; 8 of 10 positive (`docs/research/103_replay_48_muni_cef_january.md`) |

## 2. Count by Family

MEASURED from the 38 scored tests in Section 1 (rows 33 to 38 added 2026-11-26):

| Family | Tested | Counted passes | Notes |
|---|---:|---:|---|
| momentum | 8 | 0 | Replay 13 Rule A met relative marks vs all coins but lost ~70% in 3 years and is not a counted pass |
| AI discretionary | 9 | 0 | TM06 picker met its marks on months that may lie inside the models' memory and is not a counted pass; Replay 11 held-back (2,146 releases) is still open; TM02 met its headlines-help sub-mark only |
| forced flow | 7 | 2 | Replay 25 passed (9/9 marks) and Replay 48 passed (7 of 7 marks); both US $500 reachable |
| chart pattern | 5 | 0 | All five failed, including Measurement 15 fill gate |
| carry | 2 | 0 | Both cross-coin and same-coin funding carry failed after costs |
| calendar | 2 | 0 | Replay 39 (IWM pre-holiday) missed both t marks at 1.91 and 1.82 |
| event | 4 | 1 | Replay 20 passed (5/5 marks), but uses Binance.com perpetuals (not US-reachable); Replay 21 and both legs of Replay 46 did not pass |
| copy-trading | 1 | 0 | Replay 12 (Congress disclosures) lagged SPY by 1.0%/yr on held-back data |
| Total | 38 | 3 | 2 US $500 reachable passes (Replay 25, Replay 48); 1 offshore-only pass (Replay 20) |

## 3. What the Two Passes Have in Common and Their Dollar Size

Both counted passes are mechanical, short-horizon rules tied to a specific forced or retail flow on a fixed clock: Replay 25 holds TLT for the last three sessions of each month during Treasury index rebalancing (`docs/research/69_replay_25_treasury_month_end.md`), and Replay 20 shorts newly Upbit-KRW-listed coins for up to 72 hours after their first red UTC day (`docs/research/71_replay_20_upbit_listing_short.md`). Neither is a chart pattern, a trend rule, a carry rule, or an AI pick. Both stay in cash outside their short window.

Dollar size of Replay 25 (TLT month-end, US $500 reachable, unlevered, before taxes):

- Documented per-window figure (`docs/research/69_replay_25_treasury_month_end.md`): +0.2562% net per monthly window at 2 bps per side across 130 windows (12 times the monthly mean is stated in doc 69 as about 3.1% a year unlevered, simple sum 3.0744%).
- Arithmetic on $500: `$500 x 0.002562 = $1.281` per monthly window; `12 x $1.281 = $15.37` per year (about $15.50 at the doc's 3.1% figure). At the shown 5 bps/side cost (+0.1961%/window, t 1.80), `12 x $500 x 0.001961 = $11.77` per year.
- Arithmetic on $5,000: `$5,000 x 0.002562 = $12.81` per monthly window; `12 x $12.81 = $153.72` per year (about $155 at 3.1%).
- Worst year arithmetic (`docs/research/69_replay_25_treasury_month_end.md`): partial 2026 (10 windows, Jan to Oct) averaged -0.5501% per window. On $500, `10 x ($500 x -0.005501) = -$27.51` (-$2.75 per window). On $5,000, `10 x ($5,000 x -0.005501) = -$275.05` (-$27.51 per window). Measurement 34 (`docs/research/82_measurement_34_tmf_ubt_month_end.md`) checked 3x TMF on the same windows (+0.6483% marked net mean, or ~$38.90/yr simple on $500 and ~$388.98/yr on $5,000), but TMF failed its 2.7x to 3.1x tracking mark (2.5853x) and had a worst single window of -8.7% (-$43.50 on $500; -$435 on $5,000).

Dollar size of Replay 20 (Upbit listing short, NOT US-executable, unlevered Binance.com perpetuals):

- US reachability limit (`docs/research/71_replay_20_upbit_listing_short.md`): Binance.com perpetuals exclude US accounts. The shown US-today symbol filter had only 15 trades across nearly 7 years (about 2.2 trades/year, +2.003% mean net on Binance prices, lookahead list, not US fills).
- Documented per-trade figure (`docs/research/71_replay_20_upbit_listing_short.md`): +3.2088% net per trade across 139 trades over 2020 through October 2026 (~6.8 years, ~20.4 trades/year overall; 99 of 139 trades occurred in 2025 to 2026 and 69% of summed net returns came from 2026 alone). Doc 71 notes that equal-notional sums are not compounded portfolio returns, and up to three trades overlapped.
- Illustrative equal-notional arithmetic (offshore only, not US-executable): on $500 per trade, `$500 x 0.032088 = $16.04` per trade (`~20 x $16.04 = ~$321/yr` at the 139-trade full-sample pace); on $5,000 per trade, `$160.44` per trade (`~20 x $160.44 = ~$3,209/yr`). On the sparse 15-trade US-today filter (~2.2 trades/yr at +2.003%), `$500 x 0.02003 = $10.02` per trade (~$22/yr on $500, ~$220/yr on $5,000, still on Binance prices).
- Worst year and worst trade arithmetic (`docs/research/71_replay_20_upbit_listing_short.md`): worst calendar year was 2022 (2 trades, mean -1.541%, simple sum -3.082%: -$15.41 on $500 or -$154.10 on $5,000); worst single trade was -28.768% in 2025 (-$143.84 on one $500 trade; -$1,438.40 on one $5,000 trade).

## 4. What Is Still Open and What Each Must Show

STATED from `docs/QUEUE.md`, `research_rig/TRIAL_LEDGER.md`, `research_rig/PREREG_21_odd_lot_tenders.md`, and `research_rig/PREREG_36_form4_cluster_buys.md`:

- Plan 21, odd-lot cash tender offers (queue 38, ledger 158, `research_rig/PREREG_21_odd_lot_tenders.md`): Frozen with 106 filing-eligible offers (2016 to 2026), approved for custody, no-return validation, and one scored run. Must meet all 6 frozen marks on $500 whole-share allocations at $0 voluntary election fee: >= 30 trades, net mean > 0, one-sample t >= 2.0, net mean > 0 without best 3 trades, median > 0, and positive mean in >= 60% of filing years with >= 3 trades ($50 fee sensitivity and single-$500 sequential account shown).
- Plan 22, Fable-derived 21-day range-break crypto rule (queue 40, ledger 159 reserved): Fixed spot long-only rule on monthly top-30 coins (fresh 21-day range break, volume >= 1.5x usual, within 3% of level, exit on close below level or no new high in 2 days), judged 2020 to March 2026 at 12 bps/side (April to November 2026 shown only). Being drafted off-repo against lead-fixed marks.
- Plan 36, Form 4 officer and director cluster buys (queue 60, ledger 171, `research_rig/PREREG_36_form4_cluster_buys.md`): Frozen for Jan 2016 to Sep 2026 filings, $500 whole shares, 20-session hold, measured closing half-spread + 5 bps/side. Must meet all 9 marks: unresolved coverage <= 5% overall and <= 10% per year, >= 500 paired fills across >= 100 issuers, net stock mean > 0, paired excess over size-matched ETF (IWM/IJH/IVV) >= +25 bps with strictly positive 95% block-bootstrap lower bound, positive excess trimming best 3 events and best issuer, >= 7 of 11 positive years, positive 2020+ excess, positive every leave-one-year-out, and positive excess stressing unresolved exits at 100% loss.
- Plan 43, special dividend declarations (queue 74, ledger 178 reserved): the count-first check is done. MEASURED: 546 filing-eligible declarations out of 3,218 read (2016 to September 2026), and a blind re-read of 30 agreed on 29. A consistency sweep of repeat payers is under way and the plan, marks and scorer are being written; no price has been read. Marks the lead agent has asked for: at least 300 placed, net mean above zero at 5 bps a side, t at least 2.0, positive without the best 1%, positive in at least 7 of 11 years, positive from 2020 on, and above IWM over the same window.
- Replay 11 held-back earnings reader (queue 9b, ledger 121 to 134): 2,146 held-back releases already read by Claude Sonnet 5.5 and hashed; waiting for the last 5-day exits to trade after 2026-11-24 before one final score against buying all releases and 95th percentile of random picks.
- TM06 six-model comparison (queue 9g): finished 2026-11-26, rows 33 and 34 above and `docs/research/102_time_machine_tm06_six_models.md`. What it leaves open: whether the picker's April to June gains were skill or memory. TM07 runs on weeks after the stated knowledge lines and must show it there.
- Desk test TM07 (queue 33): Cheap scout agents read coin lists and headlines (the exit rule candidates in rows 72 and 75 are queue notes and are not wired into the desk test yet) and file short notes for a big model (Fable 5.2 or Opus 5.5) with standing orders, compared against the big model working alone on the same post-cutoff weeks. First a 3-week screen to decide if a longer run is warranted.
- Forward log E01 (queue 46, ledger 165, `practice/traders/E01_tlt_month_end_close.md`): Live-clock forward log of Replay 25's TLT month-end rule from Dec 2026 to Dec 2027 at 2 bps/side on SIP closes plus ex-date payouts; fails if forward mean net return <= 0 after 12 counted months.
- Forward watch E02 (queue 71, `practice/traders/E02_iwm_pre_holiday.md`): Manual pretend-money forward watch of IWM pre-holiday sessions starting Dec 2026 (Replay 39 did not pass at 5 of 7 marks; not a tested edge).
- Reverse-split round-up forward log (queue 43, `docs/research/75_reverse_split_round_up_feasibility.md`): No-money forward log of beneficial-level reverse splits; real one-share broker delivery check waits on the owner because broker pass-through (Robinhood/Webull 3 to 4 weeks) is not in price files.
- Token unlock forward logger (queue 36, `docs/research/62_round_7_outside_evidence.md` and `docs/research/85_round_15_crypto_scheduled_events.md`): Saving upcoming unlocks every 6 hours off-repo since 2026-11-25 to accumulate honest dated history before fixing a plan separating 30d pre-unlock and 3d post-unlock windows on US-shortable coins and long-only avoids.
- Small-coin event checks (rows 79 and 80, `docs/research/93_round_21_small_coin_events.md`): both closed on 2026-11-26 without a run. A complete, timed list of exchange warning tags or Coinbase roadmap additions could not be collected, because the exchanges' notice pages refused direct reads and we do not go around that. The warning-tag idea survives only as an untested exit rule candidate inside row 72.

## 5. What Has Been Ruled Out Without a Run (Skip List)

STATED from `docs/QUEUE.md` (header skip lists from Rounds 17, 19, 20, and 21, plus the dropped-before-testing section): outside evidence ruled out without spending a trial all monthly cross-sectional equity factor sorts in dead or friction-eaten families (microstructure/liquidity, size `SMB`, short-term reversal, low-leverage, calendar/seasonal, long-only idiosyncratic volatility and skewness/MAX, analyst revisions, standalone accruals, intangibles); all eight intraday forced flows in broad liquid US ETFs (last-half-hour momentum, leveraged-ETF close rebalancing, option-dealer gamma/0DTE, 15:50 MOC imbalance, overnight-gap/first-30m fade, closing-auction index flows, pre-FOMC drift, turn-of-month); eight dated mechanical ETF flows (mid-month Treasury coupons, TIPS extension, Japan March fiscal repatriation, standalone target-date quarter-end, VIX SOQ settlement, currency-hedged FX rolls, ETF capital-gain distributions, IRS Sep 15 pension deadline); ten small-coin crypto events (liquidation-cascade bounces, Robinhood first-minute listing chases, Binance/Bybit-to-US-spot ms lead-lag, funding/OI extremes as spot mean-reversion, Korean volume spikes, stablecoin depegs/outages, weekend/holiday thin-book reversals, single-coin spot ETF filings/approvals, token buybacks/burns, DeFi hack bounces); plus stock S&P 500 additions, buyback announcements, breakouts in fast-growing leaders, 52-week-high proximity, copying 13D/13F/ARK/analyst upgrades/lobbying, overnight-only stocks, small-stock gap-and-go opens, MSCI additions, monthly OpEx gamma, and SEC-enforcement crypto shorts. Small-coin narrative rotations (Round 22, `docs/research/94_round_22_narrative_rotation.md`) are WATCH only; the row 81 forward logger is blocked because CoinGecko's terms do not allow scheduled logging on the keyless public service.

## 6. The Lead Agent's Read

Written by the lead agent on 2026-11-26. This section is opinion built on Sections 1 to 5. It is not a test result.

What the 32 tests say, in plain words:

- MEASURED: nothing we tested supports fast money on a small US account. The one pass a US account can trade (Replay 25) is about $15 a year on $500, and it lost money in 2026 so far.
- MEASURED: rules that read the price chart (trend, momentum, breakouts, dips, peaks) went 0 for 13. This held on stocks and on coins, on daily bars and on minute bars.
- MEASURED: both passes share one shape. Someone is forced to trade on a known date, and the rule stands on the other side for a short window. Neither pass came from a pattern or from an AI's judgment.
- MEASURED: the same shape failed 4 more times on broad US funds (Replays 31, 33, 35 and 41), and Replay 23 on new listings missed one mark of eight. My read is that broad, liquid US funds are too well watched for a small account to find much there.

Where I still see a real chance, in the order I would spend effort:

- Trades that are too small for big money. Plan 21 (odd-lot tenders) is the cleanest case: the priority is capped at 99 shares an account, so a fund cannot take it. UNKNOWN until its one run. Even if it passes, the number of offers a year is small, so the yearly dollars may be modest.
- Single-stock events with a public timestamp (Plan 36 insider cluster buys, Plan 43 special dividends). Both have published evidence and neither has been run. I do not count the Replay 11 design sample as support: it made +0.97% a trade but trailed SPY by 0.58%. Its held-back score is still open.
- Small coins, the owner's own ground. This is where moves are large enough to matter on $500. The honest state is mixed. The only coin rule that passed was a short (Replay 20), and a US account cannot place it. The long-only hot-coin rule lost 66% to 76% in each of 2022, 2025 and 2026 (Replay 13 Rule A). Past event lists from the exchanges could not be collected (rows 79 and 80). So the coin work now runs forward: the unlock logger, the Upbit watcher, the order-book sampler, and the desk test TM07.
- The desk design the owner described (cheap scouts, one senior model, standing orders). It has not been tested. TM07 is the test. Six finished AI tests failed, so I expect a hard fight, and I want to see it measured before saying more.

What I think is not worth more trials:

- More chart and momentum rules, on any market.
- More calendar windows on broad US funds. Replay 25 stays as a forward log (E01), not as a growth plan.
- Carry at US retail fees (Replays 18 and 24).
- A lone AI trading from prices and headlines. The remaining AI cases are TM06 (six models), Replay 11 held-back, and TM07.

The limit that matters most:

- The owner's 2021 method was mostly shorting small coins with leverage. STATED by the owner: it turned $500 into $10,000 more than once. We have not been able to test a US-legal version of it at small size, because the venues that allow it are few (`docs/research/40_leverage_venues_checked.md`). If the owner opens an account at a US-legal venue that offers small-coin shorts, Replay 20 and the peak-short idea can be retested on that venue's own prices and fees. That is his call, not mine.

What would change this read:

- A pass on Plan 21, 36 or 43 would say the event family is real and move effort there.
- A clear TM06 or TM07 result would reopen the AI case.
- A second failure of the same kind in each would close it.
