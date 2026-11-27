# 198: What Each Owner Unlock Would Open

Date: 2026-11-26. Purpose: a plain decision page for the owner. After 45 scored tests (`docs/research/95_where_we_stand_after_32_tests.md`) and 13 idea rounds since Survey 187 (`docs/research/187_data_sources_for_an_ai_desk.md`), almost every remaining block is not a missing idea. Most ideas failed on the data itself (`lost before costs` or `too few events`), while a smaller set is parked behind gates only the owner can open: data-terms consent, repo visibility, a cheap US spot account, a derivatives or margin account, or more capital. Every figure below comes from a named repo document. Claims are labeled MEASURED (from repo runs or live public endpoint checks), STATED (from published papers, venue pages, or repo plans), INFERENCE (reading across repo records), or UNKNOWN (not established in the repo).

## Headline

- MEASURED (`docs/research/95_where_we_stand_after_32_tests.md`, `docs/research/180_round_57_cost_as_the_binding_limit.md`): Across 45 scored tests, 4 passed (Replay 25 TLT month-end, Replay 48 muni CEFs in January, Plan 75 coin trend ratchet on a proxy feed, and Replay 20 Upbit listing short offshore only). In the 44-test cost audit (`doc 180`), 23 lost before costs and only 3 were killed by costs alone (Replays 01, 03, and 07).
- INFERENCE: Most owner unlocks do not open a hidden pile of winning strategies. Paying for data feeds, opening stock margin, or opening a Kalshi account opens little or nothing with verified net edge today.
- INFERENCE: Only three owner actions have a clear payoff per unit of effort and risk right now: (1) switching the repo to private or getting written Alpaca publication clearance so the practice desk and TM09 can run cleanly, (2) asking Coinbase for written market-data consent so TM07 and the live crypto cost/dip cards can finish, and (3) opening a small ($500 to $1,000) Idaho Binance.US spot account only after Measurement 133 and the E11/E12/E13 forward logs confirm real cheap fills and the owner accepts the doc 186 venue-risk gate.
- MEASURED (`docs/research/71_replay_20_upbit_listing_short.md`, `docs/QUEUE.md` row 48): Opening a US crypto futures or margin account does **not** unlock our one short-side pass (Replay 20, Upbit listing short). Only 1 of 205 Upbit KRW notices in 2024 to 2026 had a US-reachable retail short listed at notice time (CRV on Kraken US spot margin).

## 1. Binding Reason for Every Dropped or Watched Idea

Every dropped, closed, or watched idea across `docs/QUEUE.md`, `docs/STATUS.md`, `docs/research/95_where_we_stand_after_32_tests.md`, `docs/research/180_round_57_cost_as_the_binding_limit.md`, `docs/research/194_data_source_terms_audit.md`, and Rounds 57 to 69 is classified by its single binding constraint among ten classes: `lost before costs`, `cost`, `too few events`, `direction`, `data rights`, `data does not exist with first-public times`, `venue access`, `account size`, `needs speed we do not have`, and `duplicate of something tested`.

### Scored Fails, Pre-Price Closes, and Active Watches

| Idea or test | Repo source | Binding class | Short factual basis |
|---|---|---|---|
| Replay 01 BTC/ETH daily trend (P1, P2, S50, D20) | `docs/research/16_rig_audit.md`, `doc 180` | cost | MEASURED: passed 5/5 at 7 bp/side (Binance.US) on Kraken feed (knife-edge PBO 0.2409 vs 0.4205 Bitstamp), failed at Alpaca (30 bp) and Kraken (43 to 85 bp). |
| Replay 03 BTC/ETH hourly intraday | `docs/research/15_replay_03_intraday_crypto.md`, `doc 180` | cost | MEASURED: 7/8 positive gross (up to +36.3 bp/RT), 0/80 pass net; break-even vs hold only 0.1 to 7.5 bp/side. |
| Replay 07 SPY/QQQ 1-minute intraday | `docs/research/27_replay_07_intraday_spy_qqq.md`, `doc 180` | cost | MEASURED: QQQ N2 Sharpe 1.21 at 0.5 bp/side vs 1.03 hold; break-even 0.90 bp/side vs hold; lost after Jul 2026 even at 0.5 bp. |
| Plan 58 BTC 21:00 to 23:00 UTC window | `docs/research/123_measure_59_bitcoin_evening_window_costs.md` | cost | MEASURED: IBIT modeled RT cost 8.13 bp vs 3.50 bp limit; STATED BIP fixed fee + 1 tick is 5.76 bp (`doc 120`). |
| Plan 70/71 overextension dip-buy (70-102, 71-013, 71-035) | `docs/research/152_plan_70_coin_sweep_search.md`, `doc 154`, `doc 157`, `doc 180` | cost | MEASURED: +56.5 to +84.1 bp net at modeled futures cost, negative at 35 to 95 bp US spot fees; half lost in first minute (+75.6 to +39.4 bp in Plan 73); forward on E09/E11/E12. |
| Replays 04, 05, 06, 09, 13A/B, 14, 16, 17, 18, 19, 22, 23, 24, 31, 33, 35, 39, 41, 52, 53, 65 | `docs/research/95_where_we_stand_after_32_tests.md`, `doc 180` | lost before costs | MEASURED: all 22 failed core return, excess, or regime marks even before full retail costs (or lost at 0 to 2 bp/side). |
| Replays 12, 46A/B, 60, 62; TM01, TM02, TM03, TM04, TM06-P/S/R | `docs/research/95_where_we_stand_after_32_tests.md`, `doc 180` | lost before costs | MEASURED: failed frozen marks against SPY, BTC, IWM, or random twins (TM06-P met min counts on Apr to Jun only and lost Jul to Nov). |
| Measurement 15 opening-range breakout fills | `docs/research/66_measure_15_breakout_fills.md` | cost | MEASURED: entry + stop-exit slippage was 0.2089 of stop distance (0.2719 with odd lots) vs 0.05 limit. |
| Measurement 121 CEF resting bids (and standalone market making) | `docs/research/170_m121_result.md`, `doc 186` | lost before costs | MEASURED: 7.56% fill rate, -26.6 bp 5-minute adverse selection; STATED Albers et al. 2025 loses -0.43 bp/trade even with -0.5 bp rebate. |
| Replay 21 odd-lot cash tenders (E03 watch) | `docs/research/97_replay_21_odd_lot_tenders.md` | too few events | MEASURED: +11.80% mean net (t 1.688) on only 14 placed trades from 106 filings, below 30-trade floor. |
| Plan 50 CEF liquidations and open-endings | `docs/QUEUE.md` row 88 | too few events | MEASURED: 22 strict documentary candidates in 10 years vs 30 required. |
| Queue 82 EDGAR altcoin treasury plans | `docs/QUEUE.md` row 82 | too few events | MEASURED: 29 eligible events vs 30 required. |
| Queue 89 going-private reverse-split cash-outs | `docs/QUEUE.md` row 89 | too few events | MEASURED: 8 verified events in 2016 to 2026 vs 30 required; 0 promised equal street-name treatment. |
| Plan 10 negative funding 1-day spot buy | `docs/QUEUE.md` Done | too few events | MEASURED: 1 to 11 triggers per rule across 4 design years. |
| Plans 51, 54, 55, 56, 66, 67, 68; Queues 11, 13, 18, 55, 67, 68, 69, 91, 92, 97, 107, 110, 118; TM08 | `docs/QUEUE.md` Done, `doc 95` | too few events | MEASURED on counts and synthetic power: all closed before prices under the 33% or 50% power line (small edge vs noise or too few independent dates). |
| Replay 20 Upbit KRW listing short (Plan 28) | `docs/research/71_replay_20_upbit_listing_short.md`, `docs/QUEUE.md` row 48 | venue access | MEASURED: +3.2088% net over 139 trades on Binance.com perps (offshore only); only 1 of 205 notices in 2024 to 2026 had a US-shortable retail contract at notice time. |
| Offshore perp venues (Binance.com, Bybit, Deribit, Hyperliquid, dYdX, Drift, Lighter, Aster) | `docs/research/40_leverage_venues_checked.md`, `doc 193`, `doc 194` | venue access | STATED: US persons explicitly barred by CFTC order or venue Terms of Service. |
| Polymarket US / global prediction markets | `docs/research/194_data_source_terms_audit.md` | venue access | STATED: US Restricted Persons barred under Terms of Service. |
| TM07 AI desk study, E06, E09, E10, E11, Measurement 132 | `docs/research/194_data_source_terms_audit.md`, `docs/STATUS.md` | data rights | STATED: Coinbase Market Data Terms (Aug 7, 2026 s3) bar AI/agent/algorithm benchmarking and Derived Works redistribution without written consent. |
| Practice desk GitHub Actions auto-run (E01, E04, E07) and TM09 hosted headlines | `docs/research/194_data_source_terms_audit.md`, `docs/STATUS.md` | data rights | STATED: Alpaca Terms bar republishing market data or order history in a public repo; TM09 real run needs written Alpaca clearance for hosted headlines. |
| Russell 2000, S&P 600, CRSP, MSCI, Nasdaq-100 index pro-forma additions/deletions | `docs/STATUS.md` line 215, `docs/QUEUE.md` line 201 | data rights | STATED: FTSE Russell, S&P DJI, CRSP, MSCI, and Nasdaq Terms prohibit storing or reproducing pro-forma lists without a paid licence. |
| Kalshi earnings-call mentions (NO under 50c) and Kalshi 5 p.m. BTC maker queues (22, 44, 53) | `docs/research/177_idea_round_54_new_market_structure.md`, `doc 194` | data rights | STATED: Kalshi Developer Agreement s3.1 bars storing API data for research or AI/ML and bars sharing without written approval; also needs an owner Kalshi account. |
| FINRA short interest, Senate eFD disclosures, CoinMarketCap, Bitnomial funding archive | `docs/research/187_data_sources_for_an_ai_desk.md`, `doc 193`, `doc 194` | data rights | STATED: publisher Terms restrict automated collection, strategy development, or AI/ML redistribution. |
| Queue 12 earnings call Q&A transcripts | `docs/QUEUE.md` Done row 12 | data rights | MEASURED: only 482 calls in 1 quarter (2025 Q4) available free; multi-year transcript sets are paid. |
| Plan 37 DoD daily contract awards | `docs/QUEUE.md` Done row 61 | data rights | MEASURED: official DoD archive index returned HTTP 403 to automated reading; 30 bp gross vs UNKNOWN spreads. |
| Plans 32, 36, 40, 42, 44, 45, 63B, 64; Queue 95 (ETF liquidation payouts), Queue 101 (earnings date advancers), Queue 102 | `docs/QUEUE.md` Done, `docs/STATUS.md`, `doc 114` | data does not exist with first-public times | MEASURED: free feeds lacked complete point-in-time rosters, verified UTC publication minutes, payout dates (only 12/40 in Row 95), or symbol continuity at both ends of windows. |
| DeFi hacks, token unlock calendars, social attention (X, Reddit, Google Trends, Wikipedia), SEC enforcement crypto shorts | `docs/QUEUE.md` line 190, `doc 45`, `doc 192`, `doc 197` | data does not exist with first-public times | MEASURED/STATED: no free dated first-word archive; AlphaGrowth has no dated unlock history; Wikipedia/Google Trends show no lead (`doc 45`, `doc 192`). |
| BTC lower-tail funding 24h rebound (Watch) | `docs/research/193_round_67_leveraged_crowd_as_a_signal.md` | data does not exist with first-public times | STATED: +50.6 bp gross in Memon et al. 2026 (Binance BTC), but no complete permitted US archive with verified first-public settlement timestamps; Perpys starts 2026-10-09 and regenerates files. |
| Reverse-side late-Jan CEF short, CEF rights-offering short, leveraged ETF reverse-split short, intraday sector/stock pairs, single-stock leveraged ETF two-sided close flow | `docs/QUEUE.md` lines 200 to 201, `doc 156`, `doc 177` | direction | STATED: main documented move is on the short or hedged side, unreachable on a $500 US cash account; stock pairs also lost in later years (`doc 156`). |
| Crypto shorting top gainers, new listings Day 0, small-cap hype pops, funding-rate upper tail | `docs/research/192_round_66_crypto_hype_and_reversal.md`, `doc 193` | direction | MEASURED/STATED: only ~35 large coins are US-shortable (0 new listings/small-cap gainers); on liquid shortable coins, Replay 17 lost 7/7 years and Plan 71 mirror shorts lost 34/38. |
| Daily long-short crypto volume-conditioned reversal (Watch: long-only add-on) and CTREND long-short | `docs/research/196_idea_round_68_thin_venue_edges.md` | direction | STATED: published spreads are long-short; Binance global low-volume reversal was -21.3 bp/day net EW and -34.1 bp/day net VW (`Bianchi et al. 2022`). |
| Two-venue US crypto inventory arbitrage (Binance.US vs Coinbase/Kraken) | `docs/research/186_round_61_thin_cheap_venue.md` | account size | STATED: dear-venue Tier 1 fees (40 to 80+ bp/side), 7-day ACH holds, $25 wire fees, and per-wallet IRS basis rules kill it at $500 to $2,000. |
| MLPs (K-1 friction), Tradovate API ($1,000 min + $25/mo), IBKR crypto ($1.75 min = 35 bp on $500), Coinbase CFM overnight ZEC/NEAR | `docs/QUEUE.md` line 200, `doc 40`, `doc 98`, `doc 180` | account size | STATED/MEASURED: fixed fees, minimums, or overnight initial margin ($748 ZEC, $860 NEAR) exceed a $300 to $500 sleeve. |
| Cross-venue stale-quote taking, quarter-hour order imbalance, 15-minute crypto reversal, sub-second market making | `docs/research/120_round_31_cfm_futures_cost_rescreen.md`, `doc 186`, `doc 188`, `doc 196` | needs speed we do not have | STATED: 500 ms to 1 s lead-lag (`arXiv:2108.09750`), 0.51 to 1.3 bp gross edges, and adverse selection require colocation and VIP rebates. |
| Round 62 operating-company liquidations, Round 62 Kalshi BTC taker blend, Round 66 6h to 24h drop rebound, Round 67 liquidation bounces, Round 69 depeg/unlock/ETF-flow repeats | `docs/research/188_round_62_career_winners_by_mechanism.md`, `doc 192`, `doc 193`, `doc 197` | duplicate of something tested | MEASURED/STATED: overlap existing Queue rows (22, 28, 36, 44, 53), prior skip lists, or tested replays (Replays 18, 24, 35, 46, Plan 50, Plan 70/71). |

## 2. What Each Owner-Only Unlock Would Reopen

Each section below covers one concrete action only the owner can take, using only figures recorded in the repo.

### Unlock A: Switch the Repo to Private or Get Written Alpaca Publication Consent

What it reopens:

- The paused GitHub Actions practice desk cron (`docs/STATUS.md` line 10, `docs/research/194_data_source_terms_audit.md`) for all US-stock and ETF forward cards: E01 (Replay 25 TLT month-end, MEASURED +0.2562% net/window over 130 windows, t 2.36, 12 windows/yr, ~$15.37/yr on $500 in `doc 149`), E04 (Replay 48 muni CEFs in January, MEASURED +1.39% net/turn over 10 turns, 1 turn/yr, ~$6.96/yr on $500 in `doc 149`), E02 (IWM pre-holiday watch), E03 (odd-lot tender watch), and E07 (ETF closure payout watch).
- TM09 (stock-desk noise and hosted-headline real run), which needs written Alpaca permission if hosted headlines are used or a private non-redistribution setup (`doc 194`).

Events per year:

- STATED (`doc 149`, `doc 95`): 12 monthly windows for E01, 1 yearly turn for E04, plus infrequent E03/E07 events.

Cost and risk to the owner:

- Money: $0.
- Time and forms: 1 minute to toggle the GitHub repo to private (already done once on 2026-11-25 per `docs/STATUS.md` line 360), or one short email to Alpaca requesting written permission to publish practice-desk summary logs.
- Risk: None. `docs/DECISIONS.md` already plans to make the repo private when real money goes in.

What still stands in the way afterward:

- STATED (`doc 149`): E01 needs at least 12 forward months (earliest after 2027-11-30) and E04 needs multiple turns before real money. Neither has any completed forward record yet.

### Unlock B: Written Consent from Coinbase for Market Data

What it reopens:

- TM07 (AI desk with scouts vs AI alone), currently stopped after week 8 round 1 (`docs/STATUS.md` line 349, `doc 194`). Without consent, TM07 stays stopped or restarts from zero on another venue's prices.
- Live and historical crypto cards paused by Coinbase Market Data Terms (Aug 7, 2026 s3, `doc 194`): E06 (hot-coin forward rules), E09 (overextension dip-buy 70-102, 71-013, 71-035 on Coinbase quotes; MEASURED +56.5 to +84.1 bp in search at futures cost, +39.4 bp at 1 minute in Plan 73 `doc 157`), E10 (Plan 75 coin trend ratchet; MEASURED +9.04% over 34 months at 75 bp/side on proxy feed `doc 181`), E11 (cheap-venue dip-buy paired check), and Measurement 132 (30-day Coinbase vs Binance.US cost and gap readout).
- Clean resolution of Coinbase-based figures already in the public repo (`docs/STATUS.md` line 350).

Events per year:

- STATED (`doc 95`, `doc 152`, `doc 181`): TM07 runs 20 paired weeks; E09/E11 dip-buy fires roughly 100 to 170 trades/yr across 20 coins (691 trades over 4 years in Plan 70 `doc 152`); Plan 75 holds a median of 8 days (`doc 95`).

Cost and risk to the owner:

- Money: $0 to ask; licence fee if Coinbase requires a commercial contract is UNKNOWN (`doc 187`).
- Time and forms: One short email to Coinbase asking for written personal/research consent covering automated local capture and AI/algorithm benchmarking (with repo private if needed).
- Risk: Low. Coinbase may say no or ignore the request, in which case we already have the fallback (Kraken/Binance.US via Measurement 133, E12, and E13, and restarting TM07 on Kraken).

What still stands in the way afterward:

- MEASURED (`doc 157`, `doc 180`, `doc 181`): Consent fixes data rights, not trading costs. Coinbase retail spot fees (60 bp+ taker per `doc 60` and `doc 180`) still kill E09/Plan 70/71 and push Plan 75 toward its negative 145 bp/side mark (-3.90% in `doc 95`). Live trading of crypto rules still needs a cheaper venue or verified lower fees.

### Unlock C: Binance.US Spot Account (Idaho, 0% Maker and 0.02% Taker)

What it reopens:

- Low-cost US spot execution for the only crypto rules sitting on a cost boundary (`doc 180`, `doc 185`, `doc 186`):
- Plan 75 (coin trend ratchet, E10/E13): MEASURED +9.04% over 34 months at 75 bp/side on proxy feed, negative (-3.90%) at 145 bp/side (`doc 95`, `doc 181`). Binance.US charges STATED 0.00% maker and 0.02% taker (0.01% on BNBUSD), with MEASURED $1.00 minNotional on all 20 Plan 70 USD pairs (`doc 180`, `doc 186`).
- Plan 70/71 overextension dip-buy (70-102, 71-013, 71-035; E11/E12): MEASURED +56.5 bp to +84.1 bp net at modeled futures cost, negative at 35 to 95 bp US spot fees (`doc 152`, `doc 154`, `doc 180`).
- Replay 01 BTC daily trend (P1, P2, S50, D20): MEASURED passed 5/5 at 7 bp/side (Binance.US) on Kraken prices (knife-edge PBO 0.2409 vs 0.4205 Bitstamp), failed at Alpaca 30 bp and Kraken 43 to 85 bp (`doc 16`, `doc 180`).
- Watch-only thin-venue ideas (`doc 186`, `doc 196`): 0% `LIMIT_MAKER` resting-bid execution overlay (tested forward in E11/E12) and buying a clean single-venue Binance.US USD discount when both venues are healthy.

Events per year:

- MEASURED/STATED (`doc 152`, `doc 180`, `doc 181`): roughly 100 to 170 dip-buy signals/yr (Plan 70/71), median 8-day trend holds (Plan 75), and roughly 10 to 30 switches over multi-year spans (Replay 01 `doc 120`).

Cost and risk to the owner:

- Money: $0 account fee, $0 ACH deposit/withdrawal, $25 wire withdrawal ($100 min), $500 to $1,000 test capital (`doc 186`).
- Time and forms: Standard KYC + Plaid or micro-deposit bank link (Idaho is eligible with USD per `doc 180`).
- Risk (STATED/MEASURED in `doc 186` and `doc 194`): High venue risk compared with a regulated broker. Binance.US has no cryptographic or CPA proof of reserves (only SOC 2 / ISO IT audits), does not name its USD custodial banks (FDIC pass-through UNKNOWN), enforces an unwaivable 7-day ACH hold on deposits and crypto bought with them, had an 18-month USD pair outage from June 2023 to February 2025, and its full API/data Terms of Service could not be read (`doc 194`, UNKNOWN).

What still stands in the way afterward:

- MEASURED (`doc 157`, `doc 186`, `doc 196`): Thin altcoin books can turn a 2 bp fee into a 25 to 95 bp spread (e.g., RENDER/USD 94.0 bp snapshot in `doc 60`). Plan 73 showed half of the dip-buy gain disappears in the first minute (+75.6 bp to +39.4 bp; worst-of-minute -28.1 bp). Plan 75 made all of its gain in 2024 and lost in 2025 (-4.62%) and 2026 (-3.75%). Do not fund an account until Measurement 133 and the E11/E12/E13 forward logs prove executable spreads and net gains.

### Unlock D: US Crypto Derivatives or Spot-Margin Account (Coinbase CFM, Kraken Pro `:BTNL`, Kraken Derivatives US, Robinhood Perps)

What it reopens:

- Shorting and leverage on roughly 35 large US-listed coins total: MEASURED 24 perpetual-style contracts on Coinbase CFM, 29 USD pairs (28 coins + USDC) on Kraken Pro US spot margin `:BTNL`, 32 unique symbols together, expanding to about 35 coins with Kalshi (19), Kraken US fractional perps (17), Robinhood perps (8), and Crypto.com US perps (9) (`doc 60`, `doc 98`, `doc 192`).
- Lower stated per-side fees than retail spot on BTC and a few majors: STATED $0.15/contract clearing + variable fee on Coinbase CFM (5.76 bp RT floor on BIP, 10.83 bp median across 24 contracts before variable commission, spread, and hourly funding in `doc 120`), or ~1 bp/side promo through 2026-12-31 on Robinhood perps (8 coins, no perp order API in `doc 40`, `doc 60`).

Blunt check of the outside and repo evidence:

- MEASURED (`doc 120`): Round 31 re-screened all 14 cost-dropped and cost-failed crypto ideas at Coinbase CFM costs. **Zero of 14** cleared the pre-data power screen of 4.
- MEASURED (`doc 57`, `doc 154`, `doc 192`): On US-shortable liquid coins, shorting pops lost badly. Replay 17 lost in 7 of 7 years on the US-shortable roster at 38 and 80 bp. Plan 71 mirror shorts were negative in 34 of 38 rules. 15-minute reversal peaks at 1.3 bp gross (`doc 192`).
- MEASURED (`doc 65`, `doc 68`): Both funding-carry tests failed (Replay 18 lost -44.61% net; Replay 24 made +0.036%/yr).
- MEASURED (`doc 39`): Replaying TM03 at 2x, 3x, and 5x multiplied losses; every model that made money at 1x lost money at 5x.
- MEASURED (`docs/QUEUE.md` row 48): Does **not** unlock Replay 20 (only 1 of 205 Upbit notices was on a US-shortable coin at notice time).

Events per year:

- Zero tested passing rules today; only potentially relevant as a cheaper execution rail for Plan 70/71 dip-buy longs on the 20 large coins if Binance.US spot is rejected and Coinbase CFM's real signed-in taker fee + spread proves lower than spot.

Cost and risk to the owner:

- Money: $0 application; Kraken US spot margin carries general Pro fees of 0.40% maker and 0.80% taker per side plus opening and 4-hour rollover fees (`doc 60`, `doc 98`). Coinbase CFM whole-contract overnight initial margin exceeds $300 on AAVE, BNB, HYPE, PEPE, ZEC, and NEAR, and exceeds $500 on ZEC ($748) and NEAR ($860) (`doc 98`).
- Time and forms: Identity verification, futures/margin suitability forms, and FCM onboarding.
- Risk (STATED in `doc 40`, `doc 98`): Automatic liquidation without prior notice, liquidation fees ($10 to $50 on Kraken Derivatives US; 2% index spread + 1.5% to 5% conversion on Kraken spot margin), and **liability for negative account deficits** on Coinbase CFM, Kraken, Kalshi, and Robinhood Derivatives. No verified matching retail paper API on Coinbase CFM (static mock only) or Kraken `:BTNL` (`doc 98`).

What still stands in the way afterward:

- No passing US-executable short strategy exists in the repo. Even on the long side, exact signed-in Coinbase CFM retail taker fees, real altcoin perp spreads, and historical CDE funding rates are UNKNOWN (`doc 98`, `doc 120`).

### Unlock E: More Capital ($2,000 to $25,000+)

What it reopens:

- Dollar scale on our two verified US-reachable passes (`doc 95`, `doc 149`): Replay 25 (TLT month-end) earned MEASURED +3.07%/yr simple (+$15.37/yr on $500, or +$153.72/yr on $5,000; partial 2026 worst year -$27.51 on $500 or -$275.05 on $5,000). Replay 48 (muni CEFs in January) earned MEASURED +1.39%/yr (+$6.96/yr on $500, or +$69.60/yr on $5,000; worst turn -5.06%).
- At $2,000+: clears Alpaca's $2,000 equity floor for 2x stock margin and short selling (`doc 40` line 121), clears Tradovate's $1,000 live API floor (`doc 40` line 111), makes Coinbase CFM overnight contracts (ZEC $748, NEAR $860) fit without exhausting cash (`doc 98`), and shrinks IBKR's $1.75 minimum crypto fee from 35 bp on $500 down to 18 bp at $1,000+ (`doc 180`).
- At $25,000+: removes Pattern Day Trader limits on US equities (not currently binding on any passing rule, since Replay 25 holds 3 sessions and Replay 48 holds 1 month).

Blunt check:

- INFERENCE: More capital scales dollar payoff linearly on Replay 25 and Replay 48, but it does **not** create a new passing strategy. Neither Replay 25 nor Replay 48 has completed its forward practice test yet (`doc 149`), and both together sit idle roughly 79% of trading sessions (`doc 149`). Adding money before forward proof only raises the dollar cost of a false pass.

Cost and risk to the owner:

- Money: $1,500 to $24,500+ additional personal capital at risk.
- Risk: Scales worst-year losses linearly (e.g., Replay 25 partial 2026 was -5.50% unlevered and -15.85% on 3x TMF in `doc 149`; Replay 48 worst turn was -5.06%).

What still stands in the way afterward:

- STATED (`doc 149`, `AGENTS.md`): Forward practice proof comes first (E01 needs 12 forward months, earliest after 2027-11-30).

### Unlock F: Stock Margin and Short Locates ($2,000+ Equity + Margin Approval)

What it reopens:

- Short-only or hedged stock/CEF ideas dropped on `direction`: reverse-side late-January CEF short, early-January winner tax-gain-selling short, CEF rights-offering shorts (343 transferable / 97 non-transferable filings 2016 to 2026 in `doc 111`), leveraged/inverse ETF reverse-split shorts (297 filings in `doc 111`), intraday sector/stock pairs (`doc 156`), and regular dividend-month long-short spreads (`doc 132`).

Blunt check:

- MEASURED/STATED (`doc 111`, `doc 132`, `doc 139`, `doc 156`): None of these has a passing net-of-cost repo test. Replay 65 (stock-bond rebalancing SPY/IEF) already assumed full shorting and still failed 3 of 5 marks (+1.01 bp/session, t 1.04, -0.07 bp without March 2020 in `doc 139`). Intraday stock pairs lost money in later years (`doc 156`). Dividend-month hedged spreads failed on count (78 usable months vs 120 needed in `doc 132`). CEF rights offerings and leveraged ETF reverse splits carry hard-to-borrow fees, buy-in risk, and thin books that are not priced in the cited papers (`doc 111`).

Cost and risk to the owner:

- Money: Minimum $2,000 equity on Alpaca (`doc 40`), plus variable hard-to-borrow fees (UNKNOWN for small CEFs and reverse-split ETFs) and margin interest.
- Risk: Unlimited theoretical loss on short squeezes, forced buy-ins, and dividend-in-lieu payments. Also sits outside the owner's stated main track (crypto, `docs/DECISIONS.md`).

What still stands in the way afterward:

- No free historical borrow-rate or locate-availability archive exists in the repo, so none of these short-stock rules can be honestly backtested net of real borrow costs.

### Unlock G: Kalshi Account (Plus Written Data/Research Consent)

What it reopens:

- Event-contract watches (`doc 53`, `doc 177`, `docs/QUEUE.md` rows 22, 44, 53): Kalshi earnings-call mention contracts (STATED Barbosa 2026: +16 cents/contract on earnings NO when YES VWAP < 50% using a retrospective 2-hour-before-last-trade clock, no spread/depth/queue model, eligible count UNKNOWN), and patient maker orders on Kalshi 5 p.m. BTC threshold contracts.
- Kalshi crypto perpetuals (`doc 40`, `doc 60`): 19 crypto markets (including VVV, not on Coinbase CFM or Kraken margin) at STATED 5 bp maker / 12 bp taker exchange fee (retail broker markup UNKNOWN).

Blunt check:

- STATED (`doc 53`, `doc 177`, `doc 188`, `doc 194`): Takers lose heavily on Kalshi (-31.46% in GWU 2021 to Apr 2025; -16.0% to -30.8% across six AI models in 57 days; 0 of 527 ForecastBench entries beat market prices). The earnings-mention figure uses a retrospective clock with no fill model. An owner account alone does **not** authorize research data collection or AI/ML use because Kalshi Developer Agreement s3.1 bars storing API data except for one's own trading and bars sharing without written approval (`doc 177`, `doc 194`).

Cost and risk to the owner:

- Money: $0 to open; taker fee formula `0.07 * C * P * (1 - P)` (`doc 177`); perp retail FCM markup UNKNOWN (`doc 60`).
- Time and forms: KYC, suitability form, tutorial for perps, plus a separate written email to Kalshi for data/research permission.
- Risk: Negative balance liability on perps (`doc 40`); thin event-contract liquidity and cancellation/settlement rules.

What still stands in the way afterward:

- Even with an account and written consent, no historical order-book archive exists (`doc 53`), so every Kalshi maker rule requires months of forward book logging before any verdict.

### Unlock H: Paid Data Keys (Index Pro-Forma Lists, Funding/Liquidation Archives, Corporate Actions, Transcripts)

What it reopens:

- Index pro-forma lists (FTSE Russell, S&P DJI, CRSP, MSCI): small-cap index additions/deletions (`doc 111`, `doc 184`).
- Historical perp funding, OI, and liquidation archives (CoinGlass, Velo, Tardis, Tokenomist, DefiLlama Pro): BTC lower-tail funding 24h rebound (`doc 193`), cliff token unlocks (`doc 197`), and order-book microstructure (`doc 187`).
- Paid equity corporate-actions, earnings transcripts, and point-in-time delisted rosters (EODHD, ThetaData, commercial transcript vendors): Queue 12 earnings call Q&A, Queue 95 ETF liquidation payouts, Queue 101 earnings date advancers, Plan 40 point-in-time small-cap losers, and Plan 63B/64 CEF identity continuity (`docs/QUEUE.md` Done, `doc 187`).

Blunt check:

- STATED (`doc 187`): Survey 187 explicitly grouped Tokenomist, DefiLlama Pro, EODHD, CoinGlass, Velo, and Tardis under **Paid and not worth it at this size**.
- MEASURED/STATED (`doc 111`, `doc 145`, `doc 193`, `doc 197`): On a $500 to $2,000 account, even a $50 to $200/month data subscription ($600 to $2,400/yr) exceeds the entire expected annual profit of every passing rule we have. Enterprise index pro-forma licences cost far more. Worse, most paid feeds still do not solve the core edge problem: Albiez 2026 found no detectable 3-day abnormal return across 913 cliff unlocks (`docs/QUEUE.md` line 200); MarketTrace found +0.04% median 72h BTC return on lower-tail funding (`doc 193`); and Queue 12 earnings-call Q&A had only 16.29% synthetic power even if spread across years (`doc 145`).

Cost and risk to the owner:

- Money: Recurring monthly or annual fees that dwarf a $500 to $2,000 test balance.
- Risk: Sunk cost with no demonstrated net edge after costs.

What still stands in the way afterward:

- Most vendor archives still lack verified first-public receipt timestamps (`doc 187`) and many strategies still fail power or retail execution costs even with clean data.

### Unlock I: Offshore Crypto Perpetuals (Not an Owner Unlock)

- STATED (`doc 40`, `doc 71`, `doc 193`, `doc 194`): Binance.com, Bybit, Deribit, Hyperliquid, dYdX, Drift, Lighter, and Aster all exclude US residents and forbid bypassing geofencing. Under `AGENTS.md` and `doc 71`, we do not go around US legal restrictions. This is listed only for completeness because it is the binding wall on Replay 20.

## 3. Our One Pass That Needs a Short: Replay 20 (Upbit Listing Short)

MEASURED (`docs/research/71_replay_20_upbit_listing_short.md`): Replay 20 is our strongest historical pass by raw per-trade return. It met 5 of 5 frozen marks on viewed dates:

- Rule: after the first Upbit KRW listing notice for a coin, wait for the first red UTC day among the notice day and the next two days, short at 01:00 UTC the next day, cover at the prior high (capped at 25% above entry) or after 72 hours.
- Return: +3.2088% mean net per trade across 139 trades at 15 bp/side plus funding (mean funding -0.887%), median +2.522%, 64.7% win rate, per-trade t 2.839, positive (+2.537%) without the best 3 trades. At 30 bp/side it still averaged +2.915% net.
- Scale and concentration: 139 trades over ~6.8 years (~20.4 trades/yr, equal-notional ~$321/yr on $500 per trade in `doc 95`), with 99 of 139 trades in 2025 to 2026 and 69% of summed net returns from 2026 alone. Worst single trade lost -28.768% (-$143.84 on $500) unlevered.

What is missing to trade it from Idaho:

- MEASURED (`docs/QUEUE.md` row 48, `docs/STATUS.md` Plan 28 closure): Binance.com perpetuals are barred to US accounts. Plan 28 checked every one of the 205 first Upbit KRW notices in 2024 to 2026 (203 through Replay 20's cutoff) against every US-legal retail short venue. Only **1 of 205** coins had a US-reachable retail short contract already listed at notice time: CRV, on Kraken US spot margin (`:BTNL`, general Pro fees 40 bp maker / 80 bp taker per side plus opening and 4-hour rollover debits).
- MEASURED (`doc 71`, `doc 95`): Even using today's US-shortable list with hindsight (not point-in-time), only 15 of the 139 trades overlapped across ~6.8 years (~2.2 trades/yr, +2.003% mean on Binance prices, ~$22/yr on $500 before US spreads and higher Kraken fees).
- INFERENCE: Nothing the owner can sign today unlocks Replay 20. Opening Coinbase CFM and Kraken margin gives access to roughly 35 already-large coins, whereas Upbit's KRW listing pop happens on mid-cap and newer tokens that US CFTC venues do not list for shorting until much later, if ever. Until US regulated venues expand short listings to hundreds of mid-cap coins (tracked passively by Queue row 49), Replay 20 stays unexecutable from Idaho.

## 4. Blunt Ranking of All Unlocks

Ranked by tested or well-evidenced edge opened per unit of owner effort, cash cost, and risk.

| Rank | Owner unlock | Edge opened (repo basis) | Effort, cost, and risk | Blunt verdict |
|---|---|---|---|---|
| 1 | Switch repo to private (or get written Alpaca publication consent) | Unblocks forward practice proof for both verified US passes: Replay 25 (+$15.37/yr on $500, `doc 149`) and Replay 48 (+$6.96/yr on $500, `doc 149`), plus TM09 and E07. | 1 minute, $0, zero risk. | Do now. Highest return per minute of effort. |
| 2 | Ask Coinbase for written market-data consent | Unblocks TM07 (after week 8) and the paused crypto cards (E06, E09, E10, E11, Measurement 132) without throwing away completed work. | One email, $0 to ask, low risk (worst case: no reply, we use Kraken/Binance.US). | Do now. Already sitting in `docs/STATUS.md` waiting on owner. |
| 3 | Open a small ($500 to $1,000) Idaho Binance.US spot account (gated on Measurement 133 and E11/E12/E13) | Only US spot venue under 10 bp maker (0% maker, 0.02% taker, `doc 180`). Needed if Plan 75 (+9.04% at 75 bp proxy, `doc 181`), Plan 70/71 dip-buy (+56.5 to +84.1 bp futures proxy, `doc 152`/`154`), or Replay 01 BTC trend ever goes live. | KYC + bank link, $500 to $1,000 capital, meaningful venue risk (no audited proof of reserves, unnamed banks, 7-day ACH hold, prior 18-month USD outage, `doc 186`). | Wait for Measurement 133 and E11/E12/E13 forward readouts first, then fund small if they pass. |
| 4 | Add more capital ($5,000+) to proven rules | Scales Replay 25 (~$154/yr on $5,000) and Replay 48 (~$70/yr on $5,000) linearly (`doc 95`, `doc 149`), but adds zero new edges. | $4,500+ personal cash at risk; scales drawdowns linearly (-5.5% to -15.9% in 2026). | Wait until E01 and E04 finish forward practice proof. Premature today. |
| 5 | Open US crypto derivatives or spot-margin account (Coinbase CFM / Kraken `:BTNL`) | Opens ~35 shortable large coins, but 0 of 14 crypto ideas cleared Coinbase CFM costs (`doc 120`), US-shortable peak shorts lost 7/7 years (`doc 57`), and Replay 20 stays blocked (1 of 205 coins, `docs/QUEUE.md` row 48). | Suitability forms, margin/liquidation risk, negative-balance deficit liability (`doc 40`, `doc 98`). | Skip for now. Revisit only if a new US-executable rule passes on the 24 CFM coins and beats Binance.US spot after real fees. |
| 6 | Open Kalshi account + request written data consent | Only reopens untested watches (earnings mentions with retrospective clock, 5 p.m. BTC maker queues); takers lost -16% to -31.5% (`doc 53`, `doc 177`). | KYC + written consent email + months of forward book logging with no historical archive. | Skip unless the owner specifically wants to test prediction-market making from scratch. |
| 7 | Stock margin and short locates ($2,000+ equity) | Opens zero passing rules; Replay 65 failed even with shorting (`doc 139`), stock pairs lost in later years (`doc 156`), and borrow costs are unmeasured. | $2,000+ cash, borrow fees, short-squeeze risk, off the crypto main track. | Skip. Nothing worth having here. |
| 8 | Buy paid data keys (index pro-forma, funding/liquidation, transcripts, corporate actions) | Annual subscription cost ($600 to $2,400+) exceeds total expected profit at $500 to $2,000; most feeds still lack first-public clocks or fail power (`doc 187`). | Recurring cash burn with no verified net edge. | Skip. Do not buy data at this account size. |
| 9 | Offshore crypto perpetuals | Would open Replay 20 (+3.21%/trade, 139 trades, `doc 71`), but is legally barred to a US resident in Idaho (`doc 40`, `doc 71`). | Legally prohibited; not an option. | Off the table. |

## 5. Three Unlocks Most Worth Action and the First Test for Each

1. Switch the repo to private (or obtain written Alpaca consent to publish practice summaries).
First test the day it is granted: resume the GitHub Actions practice-desk cron so E01 (Replay 25 TLT month-end), E04 (Replay 48 muni CEFs, first forward entry at December 2026 close), and E07 (ETF closure payouts) log on-time forward pretend fills without interruption, and clear TM09's stock-desk noise run on hosted headlines (`docs/STATUS.md`, `doc 149`, `doc 194`).

2. Email Coinbase to request written market-data consent for private automated research and AI/algorithm benchmarking.
First test the day it is granted: unpause and finish TM07 from week 8 round 2 through week 20 under its frozen registration (`docs/STATUS.md` line 349, `doc 95`), and complete the 30-day Measurement 132 paired Coinbase-versus-Binance.US spread and gap readout (`doc 186`).

3. Prepare (after Measurement 133 and E11/E12/E13 readouts, not before) a capped $500 to $1,000 Idaho Binance.US spot account.
First test the day it is granted: run a small live ACH deposit-and-withdrawal round-trip check to confirm banking rails and the 7-day hold (`doc 186`), then execute tiny live $25 to $50 orders on the first E13 (Plan 75) or E12 (overextension dip-buy) signals that pass forward practice marks, comparing actual filled price against the logged paper fill before scaling to $500 (`doc 180`, `doc 186`).
