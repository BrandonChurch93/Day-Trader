# Where We Stand After 43 Scored Tests

Last changed: 2026-11-26 UTC (Replay 22 result added after Replay 62). Plain synthesis for the owner. Figures come from `research_rig/TRIAL_LEDGER.md`, `docs/STATUS.md`, `docs/QUEUE.md`, and the named repo files, including drafts where noted; no return was recomputed. Claims are labeled MEASURED (from our own runs), STATED (from plans, schedules, or external sources cited in repo docs), or UNKNOWN (not yet measured).

## 1. Every Scored Test So Far

MEASURED: Forty-three scored tests (trading replays, AI time-machine evaluations, and the opening-range fill gate that killed a strategy before replay) have been completed or scored on a design sample, as counted below. Three counted trading replays passed their frozen marks: Replays 25 and 48 (US $500 reachable) and Replay 20 (not US-reachable). Diagnostic measurements on already-tested windows (Measurement 27 TLT closing cross in `docs/research/70_measure_27_tlt_closing_cross.md`; Measurement 34 TMF/UBT leverage check in `docs/research/82_measurement_34_tmf_ubt_month_end.md`) and non-trial descriptive looks (Alex Becker calls in `docs/research/46_becker_calls_measured.md`, attention feed in `docs/research/45_attention_feed_measured.md`, governance votes in `docs/research/49_governance_votes_look.md`, and the peak-signal look in `docs/research/61_look_after_the_peak_signal.md`) are not counted as separate strategy trials here.

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
| 38 | Replay 48 | Long the five worst muni closed-end funds, last December close to last January close | forced flow | Yes | Passed (7 of 7 marks) | 10 yearly turns, +1.39% mean net per turn against +0.09% for MUB and +0.59% for the roster; 8 of 10 positive (`docs/research/103_replay_48_muni_cef_january.md`); MEASURED identity review on 2026-11-26 found MUI under the wrong symbol for nine turns, and pre-entry prices show it would not have been picked in any turn, so the pass stands (`research_rig/REVIEW_48_identity.md`). |
| 39 | Replay 52 | Buy corporate bond funds after quarter-end | forced flow | Yes | Did not pass (0 of 6 marks) | 40 quarters, -0.0308% mean net, t -0.24; -0.0197% net of Treasury proxies, against +0.1279% net after 80 ordinary month-ends (`docs/research/113_replay_52_quarter_end_corporate_bond_funds.md`) |
| 40 | Replay 53 | Buy taxable closed-end fund losers into January | forced flow | Yes | Did not pass (5 of 7 marks) | +2.74% mean net, versus +2.00% for PCEF and +1.83% for the roster; positive in 6 of 10 turns and ahead of PCEF in 6 of 10, both below the frozen marks (`docs/research/122_replay_53_taxable_fund_january_rebound.md`) |
| 41 | Replay 60 | Buy special-dividend declarations two sessions after the filing, hold 20 sessions | event | Yes | Did not pass (6 of 7 marks) | 339 placed pairs, +1.96% mean net (clustered t 2.38); +0.96% against IWM with clustered t 1.23 against a mark of 2, the one missed mark (`docs/research/126_replay_60_special_dividends.md`) |
| 42 | Replay 62 | Buy the close before a special-dividend ex-date, sell the ex-date close, hedged against IWM | event | Yes | Did not pass (1 of 5 marks) | 316 placed pairs, -0.06% mean net against IWM, clipped clustered t -0.63 against a mark of 2, 4 of 11 years positive against a mark of 7 (`docs/research/130_replay_62_special_dividend_ex_day.md`) |
| 43 | Replay 22 | Range-break rule from Fable 5.2 picker's notes, no AI | momentum | Yes | Did not pass (1 of 5 marks) | +275.40% against +274.25% for holding the same coins, 2020 to March 2026 at 12 bp; daily Sharpe 0.67 against a mark of 1.0, largest fall 79.40% against 40%, 57% of 500 random-entry twins at or above it, 3 of 7 years positive; -11.14% without its best 3 trades (`docs/research/137_replay_22_fable_rule_a.md`) |

## 2. Count by Family

MEASURED from the 43 scored tests in Section 1:

| Family | Tested | Counted passes | Notes |
|---|---:|---:|---|
| momentum | 9 | 0 | Replay 13 Rule A met relative marks vs all coins but lost ~70% in 3 years and is not a counted pass; Replay 22 (the Fable 5.2 picker's range-break rule with no AI) ended level with holding the same coins and could not be told apart from random entries |
| AI discretionary | 9 | 0 | TM06 picker met its marks on months that may lie inside the models' memory and is not a counted pass; Replay 11 held-back (2,146 releases) is still open; TM02 met its headlines-help sub-mark only |
| forced flow | 9 | 2 | Replay 25 passed (9/9 marks) and Replay 48 passed (7 of 7 marks); both US $500 reachable. Replays 52 and 53 did not pass. |
| chart pattern | 5 | 0 | All five failed, including Measurement 15 fill gate |
| carry | 2 | 0 | Both cross-coin and same-coin funding carry failed after costs |
| calendar | 2 | 0 | Replay 39 (IWM pre-holiday) missed both t marks at 1.91 and 1.82 |
| event | 6 | 1 | Replay 20 passed (5/5 marks), but uses Binance.com perpetuals (not US-reachable); Replay 21, both legs of Replay 46, Replay 60 and Replay 62 did not pass |
| copy-trading | 1 | 0 | Replay 12 (Congress disclosures) lagged SPY by 1.0%/yr on held-back data |
| Total | 43 | 3 | 2 US $500 reachable passes (Replay 25, Replay 48); 1 offshore-only pass (Replay 20) |

## 3. What the First Two Passes Have in Common and Their Dollar Size

Both counted passes are mechanical, short-horizon rules tied to a specific forced or retail flow on a fixed clock: Replay 25 holds TLT for the last three sessions of each month during Treasury index rebalancing (`docs/research/69_replay_25_treasury_month_end.md`), and Replay 20 shorts newly Upbit-KRW-listed coins for up to 72 hours after their first red UTC day (`docs/research/71_replay_20_upbit_listing_short.md`). Neither is a chart pattern, a trend rule, a carry rule, or an AI pick. Both stay in cash outside their short window.

The later [Replay 48](103_replay_48_muni_cef_january.md) pass averaged about $7 on $500 once a year, before taxes. Its evidence is ten turns and does not separate the loser effect from a general year-end rally with confidence.

- MEASURED: [Replay 53](122_replay_53_taxable_fund_january_rebound.md) beat PCEF and the eligible roster on average, but missed both year-count marks: years above zero and years ahead of PCEF.
- MEASURED, shown only: the taxable and muni yearly results had a correlation of 0.80. STATED interpretation: the two replays are mostly the same bet, not independent evidence ([Replay 53](122_replay_53_taxable_fund_january_rebound.md)).
- STATED: the fifth-session exit was shown only, so it cannot count as a pass ([Replay 53](122_replay_53_taxable_fund_january_rebound.md)).
- MEASURED: [Replay 60](126_replay_60_special_dividends.md) made +1.96% net per 20-session hold after special-dividend declarations, but only +0.96% more than IWM over the same days, with clustered t 1.23. STATED interpretation: about half of the gain was the market, and the stock-specific half is not clear of chance on 339 events.
- MEASURED: [Replay 62](130_replay_62_special_dividend_ex_day.md) tried the one-day version on the same events: buy the close before the ex-date, sell the ex-date close, hedged against IWM. It made -0.06% per trade on 316 pairs and met 1 of 5 marks. STATED interpretation: the published ex-day gain is not there on these events after costs, so nothing in the special-dividend family is left open.

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

- Plan 60, special dividends: STATED, successor to Plan 43, draft under audit. Must place at least 300 stock/IWM pairs, show positive net and positive excess over IWM with monthly clustered t of at least 2.0 for both, stay positive without the best 1% and from 2020 on, and show gains in at least seven years (`ae00056:research_rig/PREREG_60_special_dividends.md`, `research_rig/PREREG_43_special_dividends.md`, `config/thresholds.yaml`).
- Plan 22, range-break crypto rule: STATED, near freeze. At 12 basis points per side the fixed rule must beat the equal-weight hold and the 95th percentile of random twins, with Sharpe at least 1.0, drawdown no more than 40%, and at least five positive years (queue 40 in `docs/QUEUE.md`; draft settings at `6af8761:config/thresholds.yaml`).
- TM07, AI desk with scouts versus the same AI alone: STATED, registration being finished. Over 20 paired weeks each claim needs one-sided t of at least 2.43, at least 12 winning weeks and a positive mean without its best week; no early screen decides whether the rest runs (draft `bfc9dcc:timemachine/TM07_REGISTRATION.md` and row 198 of `bfc9dcc:research_rig/TRIAL_LEDGER.md`).
- Plan 11, held-back earnings reader: STATED, score once after the last five-session exits have traded; exact date UNKNOWN. The chosen reader must make at least 100 buys and beat both buying all releases and the 95th percentile of random picks after costs (`research_rig/PREREG_11_earnings_release_reader.md`, queue 9b in `docs/QUEUE.md`).
- Plan 26, early TLT month-end check: STATED, blocked on an optional data key. Must score at least 100 windows, show positive net results across years and without the best windows or any one year, and show a statistically positive inside-versus-outside window gap (`research_rig/PREREG_26_treasury_month_end_early.md`).
- E01, TLT month-end forward log: STATED, must average above zero net after 12 on-time monthly records (`practice/traders/E01_tlt_month_end_close.md`, ledger 165).
- E02, IWM pre-holiday forward watch: STATED, record on-time pretend net results for the full-closure rule; the card gives no new pass mark (`practice/traders/E02_iwm_pre_holiday.md`).
- E03, odd-lot tender watch: STATED, show whether a filed priority offer gives an eligible opening discount and a verified outcome under the unchanged rule; no new pass mark (`practice/traders/E03_odd_lot_tender_watch.md`).
- E04, muni closed-end fund January watch: STATED, record the unchanged rule's forward net result against MUB and the eligible roster; one turn is not a verdict (`practice/traders/E04_muni_cef_january_watch.md`).
- E05, hot-five cash switch: STATED, proposed only, not started. If approved, it would report on-time coverage and compare the unchanged rule with the hold and random yardsticks after 26 complete weeks; results UNKNOWN (`practice/traders/E05_momentum_regime_watch.md`).
- E06, hot-coin forward rules: STATED, each of the two candidate rules must beat the fixed comparison in at least 16 of 20 weeks; a tie or missed week is not a win (`practice/traders/E06_forward_hot_coin_rules.md`).
- E07, ETF closure payouts: STATED, needs a mean payout over the closing ask above 0.25%, a positive median, at least 60% positive cases, and subgroup means above 0.15% where the card has enough cases, with at least 20 completed funds if stopped by date (`practice/traders/E07_etf_closure_payout_watch.md`).
- Queue 101, earnings dates moved earlier: STATED, find a lawful, free source of timestamped issuer announcements and count eligible date changes before pulling any prices. Whether the source exists is UNKNOWN (`docs/QUEUE.md`, `docs/121_idea_round_32.md`).
- Queue 102, activist filings in listed closed-end funds: STATED, count eligible SEC Schedule 13D filings and amendments with proxy or tender escalations before opening prices; the screen can clear at 150 events under its assumptions. Exact post-filing return is UNKNOWN (`docs/QUEUE.md`, `docs/121_idea_round_32.md`).

## 5. What Has Been Ruled Out Without a Run (Skip List)

These additional items closed without a scored return. Documentary checks, synthetic tests and input validation are not trading replays. See `docs/STATUS.md`, the Done section of `docs/QUEUE.md`, and the sources below.

- Plan 58, Bitcoin evening window: MEASURED by Measurement 59, IBIT quote coverage passed but modeled round-trip cost was 8.127517 basis points against a strict limit of 3.50, so the plan closed before any historical replay prices were read (`docs/research/123_measure_59_bitcoin_evening_window_costs.md`).
- Plan 50, listed fund closures: MEASURED, 22 strict documentary candidates against 30 required; closed on count (`research_rig/CLOSE_50_on_count.md`).
- Plan 51, hot-five momentum cash switch: MEASURED in synthetic tests, the original cleared 0 of 100 and uniform placement cleared 1 of 100 at the target effect, below the 50% floor (`research_rig/CLOSE_51_on_power.md`).
- Plan 36, insider buying clusters: MEASURED, unresolved coverage was 5.71% against the frozen 5% limit; stopped inconclusive without a return (`research_rig/CLOSE_36_on_coverage.md`).
- Plan 54, November small-cap loser rebound: MEASURED in synthetic tests, 7.87% power at a 2% gross edge under central noise, below the 50% floor (`research_rig/CLOSE_54_on_power.md`).
- Plan 55, spin-off rebound: MEASURED in synthetic tests, 32.86% central power at the closest published short-window edge, below the 50% floor (`research_rig/CLOSE_55_on_power.md`).
- Plan 56, fixed insider purchase clusters: MEASURED in synthetic tests, 9.20% power at the modeled published edge for the longer hold, below the 50% floor (`research_rig/CLOSE_56_on_power.md`).
- Queue 91, preferred-share January losers: MEASURED in synthetic tests, 13.69% central power at a 2% gross edge, below the 50% floor (`research_rig/CLOSE_ROWS_91_92_on_power.md`).
- Queue 92, listed BDC January losers: MEASURED in synthetic tests, 10.77% central power at a 2% gross edge, below the 50% floor (`research_rig/CLOSE_ROWS_91_92_on_power.md`).
- Queue 97, forward stock-split announcements: STATED, published drift after the announcement jump was near zero; MEASURED, 157 matched announcements could not support a useful test at that edge (`docs/research/118_row97_forward_split_count_first_close.md`).
- Plan 43, special dividends: MEASURED, three input validation stops for tape integrity, intrabar price basis, then missing or zero-volume bars and raw-to-adjusted price basis. No return was computed; STATED, Plan 60 replaces it (ledger 178, 188 and 195 in `research_rig/TRIAL_LEDGER.md`; successor draft `ae00056:research_rig/PREREG_60_special_dividends.md`).
- Idea round 30: STATED, 0 of 7 crypto idea families cleared the power screen after US retail spot fees (`docs/research/119_round_30_high_count_crypto_power_screen.md`).
- Idea round 31: STATED, 0 of 14 cost-dropped ideas cleared the power screen at the proposed futures costs (`docs/research/120_round_31_cfm_futures_cost_rescreen.md`).

STATED from `docs/QUEUE.md` (header skip lists from Rounds 17, 19, 20, and 21, plus the dropped-before-testing section): outside evidence ruled out without spending a trial all monthly cross-sectional equity factor sorts in dead or friction-eaten families (microstructure/liquidity, size `SMB`, short-term reversal, low-leverage, calendar/seasonal, long-only idiosyncratic volatility and skewness/MAX, analyst revisions, standalone accruals, intangibles); all eight intraday forced flows in broad liquid US ETFs (last-half-hour momentum, leveraged-ETF close rebalancing, option-dealer gamma/0DTE, 15:50 MOC imbalance, overnight-gap/first-30m fade, closing-auction index flows, pre-FOMC drift, turn-of-month); eight dated mechanical ETF flows (mid-month Treasury coupons, TIPS extension, Japan March fiscal repatriation, standalone target-date quarter-end, VIX SOQ settlement, currency-hedged FX rolls, ETF capital-gain distributions, IRS Sep 15 pension deadline); ten small-coin crypto events (liquidation-cascade bounces, Robinhood first-minute listing chases, Binance/Bybit-to-US-spot ms lead-lag, funding/OI extremes as spot mean-reversion, Korean volume spikes, stablecoin depegs/outages, weekend/holiday thin-book reversals, single-coin spot ETF filings/approvals, token buybacks/burns, DeFi hack bounces); plus stock S&P 500 additions, buyback announcements, breakouts in fast-growing leaders, 52-week-high proximity, copying 13D/13F/ARK/analyst upgrades/lobbying, overnight-only stocks, small-stock gap-and-go opens, MSCI additions, monthly OpEx gamma, and SEC-enforcement crypto shorts. Small-coin narrative rotations (Round 22, `docs/research/94_round_22_narrative_rotation.md`) are WATCH only; the row 81 forward logger is blocked because CoinGecko's terms do not allow scheduled logging on the keyless public service.

## 6. The Lead Agent's Read

Written by the lead agent on 2026-11-26. This section is opinion built on Sections 1 to 5. It is not a test result.

What the original 32 tests said, in plain words:

- MEASURED: nothing we tested supports fast money on a small US account. The one pass a US account can trade (Replay 25) is about $15 a year on $500, and it lost money in 2026 so far.
- MEASURED: rules that read the price chart (trend, momentum, breakouts, dips, peaks) went 0 for 13. This held on stocks and on coins, on daily bars and on minute bars.
- MEASURED: both passes share one shape. Someone is forced to trade on a known date, and the rule stands on the other side for a short window. Neither pass came from a pattern or from an AI's judgment.
- MEASURED: the same shape failed 4 more times on broad US funds (Replays 31, 33, 35 and 41), and Replay 23 on new listings missed one mark of eight. My read is that broad, liquid US funds are too well watched for a small account to find much there.

Where I still see a real chance, in the order I would spend effort:

- Trades that are too small for big money. Replay 21 (odd-lot tenders) was the cleanest case and it has now run. MEASURED: 14 trades from 106 eligible filings, +11.80% mean net, t 1.688, under the floor of 30 trades, so it did not pass. The gain per trade is large but there are too few offers a year to prove it or to live on it.
- Single-stock events with a public timestamp. This family is now mostly spent. Insider cluster buys closed twice without a score (Plan 36 on data coverage, Plan 56 on power). Special dividends were scored twice on the same events: Replay 60 (20-session hold) met 6 of 7 marks but half its gain was the market, and Replay 62 (one-session ex-day trade) met 1 of 5. I do not count the Replay 11 design sample as support: it made +0.97% a trade but trailed SPY by 0.58%. Its held-back score is still open.
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

- Single-stock event rules have now failed or closed five times (Replays 21, 60 and 62; Plans 36 and 56). A new event idea has to be a hedged spread with a forced seller, and has to clear the power screen, before it earns a trial.
- A clear TM06 or TM07 result would reopen the AI case.
- A second failure of the same kind in each would close it.
