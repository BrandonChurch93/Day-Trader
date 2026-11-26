# Round 31: Re-Screening Cost-Dropped Crypto Ideas at Coinbase CFM Futures Costs

Date: 2026-11-26
Status: 0 queued (queue row 99 stays unused)
Scope: (1) Build a STATED round-trip cost table (fixed per-contract clearing fee plus one tick over contract notional) for all 24 crypto perpetual-style futures contracts at Coinbase Financial Markets (CFM) using Coinbase's retail fee page, contract specifications, and public futures catalog. (2) Re-screen every crypto idea previously dropped or failed on cost across `docs/QUEUE.md` (Done and skip lists), docs 41, 43, 62, 79, 85, 95, 96, 115, and 119 under the `docs/research/117_power_screen_before_data.md` power screen (`N * (net_edge / noise)^2 >= 4`), counting an idea only if its published edge was measured on a coin that has a CFM contract. (3) Identify data requirements and Plan 58 overlap for anything that clears 4.

## Summary

Zero of 14 re-screened crypto ideas clear the Doc 117 pre-data power screen of 4 at Coinbase CFM futures costs. Queue row 99 stays unused.

Two structural findings drive this outcome:

- Fixed dollar fees scale sharply upward in basis points when contract notional is small or coin prices are lower (STATED / MEASURED from the Nov 26, 2026 public catalog). At Plan 58's hypothetical $100,000 BTC and $3,000 ETH scale (`research_rig/PREREG_58_btc_hour_of_day.md`), `BIP` (0.01 BTC) fixed clearing ($0.30 round trip) plus one tick ($0.05) is 3.50 bps and `ETP` (0.10 ETH) is 11.67 bps. At the Nov 26, 2026 public catalog prices ($60,735 BTC and $1,694 ETH), `BIP` is 5.76 bps and `ETP` is 20.66 bps before variable commission, real spread, and hourly funding. Across all 24 crypto contracts, the median fixed-fee plus one-tick floor is 10.83 bps (range 1.12 bps on `PAU` PAXG to 109.59 bps on `SHP` SHIB).
- Almost every previously cost-dropped crypto idea either had a gross edge smaller than `BIP`'s 5.76 bps floor (15-minute reversal at 1.3 bps, quarter-hour boundary imbalance at 0.51 bps, CFM BTC perpetual basis at 3.2 bps, non-Plan-58 BTC time-of-day windows at 0.8 to 3.89 bps), failed directionally even at zero or low fees (Replay 03 held-back BTC, Replay 09, 1-to-3-day liquid cross-sectional reversal, CME weekend gaps, 12-hour Kraken session reversal, post-2021 stablecoin mints), or had an edge measured only on small coins absent from the 24-contract CFM roster.

## Task 1: Coinbase CFM 24-contract round-trip cost table (STATED)

Fee and specification sources opened directly (STATED):

- Retail fee page ([Coinbase US Derivatives](https://www.coinbase.com/derivatives-trading/us-derivatives)): "This does not include a $0.15 charge per contract to cover exchange, NFA, and clearing fees." and "Enjoy volume-based fees as low as 0.005% maker."
- Contract specifications page ([Coinbase Perpetual-Style Futures Contract Specifications](https://help.coinbase.com/en/derivatives/perpetual-style-futures/contract-specifications)): lists nano BTC Perp Futures (`BIP`, 0.01 BTC, $5 tick size, $0.05 tick value), nano ETH Perp Futures (`ETP`, 0.10 ETH, $0.50 tick size, $0.05 tick value), nano Solana Perp Futures (`SLP`, 5 SOL, $0.01 tick size, $0.05 tick value), and nano XRP Perp Futures (`XPP`, 500 XRP, $0.0001 tick size, $0.05 tick value), and states: "The contracts trade continuously, 24 hours a day, 7 days a week, with the exception of a 1 hour maintenance period on Fridays from 5pm - 6pm ET."
- Public futures catalog ([Coinbase Advanced Trade public products endpoint](https://api.coinbase.com/api/v3/brokerage/market/products?product_type=FUTURE&limit=250), snapshot 2026-11-26): provides `contract_code`, `contract_root_unit`, `contract_size`, `price_increment`, and displayed `price` for all 24 non-disabled crypto `-20DEC30-CDE` perpetual-style futures contracts.

Formula matching `research_rig/PREREG_58_btc_hour_of_day.md` (STATED): round-trip fixed clearing fee is `$0.30` (`2 * $0.15`), expressed as `10000 * 0.30 / Notional`, plus one spread tick (`10000 * Tick_USD / Notional`), where `Notional = Price * Multiplier` and `Tick_USD = Tick_Size * Multiplier`. All figures below are STATED cost floors before variable commission, real bid-ask spread, and funding.

| Code | Coin | Multiplier | Tick size (pts) | Snapshot price ($) | Notional ($) | Tick ($) | Fixed fee RT (bps) | 1 tick (bps) | Fee + 1 tick RT (bps) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BIP | BTC | 0.01 | 5 | 60,735 | 607.35 | 0.05 | 4.94 | 0.82 | 5.76 |
| ETP | ETH | 0.1 | 0.5 | 1,694 | 169.40 | 0.05 | 17.71 | 2.95 | 20.66 |
| ZEC | ZEC | 1 | 0.05 | 761.4 | 761.40 | 0.05 | 3.94 | 0.66 | 4.60 |
| PAU | PAXG | 1 | 0.1 | 3,573.6 | 3,573.60 | 0.10 | 0.84 | 0.28 | 1.12 |
| SLP | SOL | 5 | 0.01 | 70.97 | 354.85 | 0.05 | 8.45 | 1.41 | 9.86 |
| AVE | AAVE | 5 | 0.01 | 94.7 | 473.50 | 0.05 | 6.34 | 1.06 | 7.39 |
| BNB | BNB | 1 | 0.05 | 559.55 | 559.55 | 0.05 | 5.36 | 0.89 | 6.26 |
| BCP | BCH | 1 | 0.05 | 207.75 | 207.75 | 0.05 | 14.44 | 2.41 | 16.85 |
| HYP | HYPE | 10 | 0.01 | 61.87 | 618.70 | 0.10 | 4.85 | 1.62 | 6.47 |
| LCP | LTC | 5 | 0.01 | 43.55 | 217.75 | 0.05 | 13.78 | 2.30 | 16.07 |
| XPP | XRP | 500 | 0.0001 | 0.9582 | 479.10 | 0.05 | 6.26 | 1.04 | 7.31 |
| NER | NEAR | 500 | 0.0001 | 3.0612 | 1,530.60 | 0.05 | 1.96 | 0.33 | 2.29 |
| LNP | LINK | 50 | 0.001 | 9.23 | 461.50 | 0.05 | 6.50 | 1.08 | 7.58 |
| AVP | AVAX | 10 | 0.01 | 6.7 | 67.00 | 0.10 | 44.78 | 14.93 | 59.70 |
| SUP | SUI | 500 | 0.0001 | 0.6732 | 336.60 | 0.05 | 8.91 | 1.49 | 10.40 |
| POP | DOT | 100 | 0.001 | 0.666 | 66.60 | 0.10 | 45.05 | 15.02 | 60.06 |
| ADP | ADA | 1,000 | 0.0001 | 0.1491 | 149.10 | 0.10 | 20.12 | 6.71 | 26.83 |
| OND | ONDO | 1,000 | 0.0001 | 0.2871 | 287.10 | 0.10 | 10.45 | 3.48 | 13.93 |
| XLP | XLM | 5,000 | 0.00001 | 0.12901 | 645.05 | 0.05 | 4.65 | 0.78 | 5.43 |
| ENA | ENA | 5,000 | 0.00001 | 0.10314 | 515.70 | 0.05 | 5.82 | 0.97 | 6.79 |
| DOP | DOGE | 5,000 | 0.00001 | 0.05666 | 283.30 | 0.05 | 10.59 | 1.76 | 12.35 |
| HEP | HBAR | 5,000 | 0.00001 | 0.05375 | 268.75 | 0.05 | 11.16 | 1.86 | 13.02 |
| PEP | PEPE | 100,000 | 0.000001 | 0.003554 | 355.40 | 0.10 | 8.44 | 2.81 | 11.25 |
| SHP | SHIB | 10,000 | 0.00001 | 0.00365 | 36.50 | 0.10 | 82.19 | 27.40 | 109.59 |

Scale sensitivity note (STATED): at Plan 58's hypothetical higher prices ($100,000 BTC and $3,000 ETH), `BIP` drops from 5.76 bps to 3.50 bps and `ETP` drops from 20.66 bps to 11.67 bps (`research_rig/PREREG_58_btc_hour_of_day.md`). Both the Nov 26, 2026 catalog floor and the hypothetical $100,000 BTC sensitivity are checked in Task 2 below.

What remains UNKNOWN on this route (consistent with `research_rig/MEASURE_59_crypto_clock_costs.md` and `docs/research/98_kraken_and_coinbase_short_access.md`):

- Real top-of-book bid-ask spread and depth across all 24 contracts (only `BIP` and `ETP` are queued for forward top-of-book sampling in Measurement 59; thin altcoin books may quote multiple ticks wide).
- Actual entry-tier retail variable commission (the retail page states "as low as 0.005% maker", whereas the Coinbase Advanced Trade futures API guide quotes 0.05% introductory per side = +10.0 bps round trip; exact signed-in entry-tier maker and taker rates are UNKNOWN).
- Hourly funding and basis carry on perpetual-style contracts (funding accrues hourly and settles twice daily, and no unauthenticated historical CDE funding series is established).
- Account-specific initial, maintenance, and intraday vs overnight margin requirements (per `docs/research/98_kraken_and_coinbase_short_access.md`, `ZEC` and `NER` already exceeded $500 overnight initial margin at snapshot, and `PAU` carries $3,574 notional per contract).

## Task 2: Re-screen of all cost-dropped and cost-failed crypto ideas

Strict coin-match rule applied: an edge measured only on small coins or broad offshore altcoin baskets does not transfer to BTC, ETH, or the 24 CFM contracts. Only ideas whose published or measured gross edge was established on a coin with a CFM contract are re-screened below. All screen values use `N * (net_edge / noise)^2` per `docs/research/117_power_screen_before_data.md` (threshold >= 4).

| # | Idea and repo source | Coin(s) with CFM contract | Events (N) | Published gross edge and source | CFM RT cost used (bps) | Net edge (bps) | Noise guess (bps) | New screen | Verdict |
|---|---|---|---:|---|---:|---:|---:|---:|---|
| 1 | 15-minute directional mean reversion (docs 41, 119) | BTC, ETH, majors | ~35,000+ | +1.3 bps peak gross ([arXiv 2608.21888v1](https://arxiv.org/html/2608.21888v1)) | 5.76 (3.50 at $100k BTC) | -4.46 (-2.20) | 40 | 0.00 | DROP |
| 2 | Quarter-hour boundary order imbalance (doc 41) | BTC, ETH, XRP, SOL, DOGE, ADA | ~100,000+ | +0.510 bps gross ([arXiv 2607.09426v2](https://arxiv.org/html/2607.09426v2)) | 5.76 to 26.83 | -5.25 to -26.32 | 25 | 0.00 | DROP |
| 3 | Spot-perpetual basis convergence (docs 41, 62, 119, Replay 24) | BTC, ETH, BNB, DOGE, ADA | ~2,000 | 3.2 bps mean abs basis on Coinbase CFM BTC ([Fracassi 2026](https://cesare-fracassi.github.io/files/pdf/Research/Fracassi_2026_CFTC_247_Perpetuals.pdf)); needs spot leg too | 5.76 perp alone (+80 to 180 spot) | <= -2.56 | 50 | 0.00 | DROP |
| 4 | BTC-to-altcoin regime lead-lag (doc 41) | BTC + 9 majors | ~100s | -34.3 bps net after costs, 52% accuracy ([Khan SSRN 7485359](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7485359)) | 7.31 to 26.83 | < 0 | 300 | 0.00 | DROP |
| 5 | Negative-funding 72h BTC rebound (doc 119, Plan 10, Rounds 21/24) | BTC (`BIP`) | 280 | +46.2 bps median 72h gross ([MyProfitFactor Oct 2026](https://myprofitfactor.com/en/crypto/negative-funding-rate-bitcoin-rebounds/)); [MarketTrace Nov 2026](https://markettrace.ai/blog/funding-rate-extremes) finds zero edge | 5.76 (3.50 at $100k BTC) | +40.44 (+42.70) | 450 | 2.26 (2.52) | DROP (< 4) |
| 6 | Cross-coin 3-day / 1-hour funding carry (doc 41, Replay 18) | Top-30 / 24 CFM | ~2,000 | Small-coin 671-perp offshore deciles ([OctopusTakopi](https://github.com/OctopusTakopi/funding-rate-alpha)); fails coin-match; Replay 18 lost -44.61% | 10.83 median | < 0 | 300 | 0.00 | DROP |
| 7 | 1-to-3-day cross-sectional reversal on liquid coins (doc 119) | BTC, ETH, SOL, XRP, ADA, DOGE, etc. | ~1,700 | -1.12 bps gross on 9 liquid coins ([WhatDoesntWork Oct 2026](https://whatdoesntwork.com/research/one-day-crypto-mean-reversion/)); -21.3 bps/d net on Binance ([Bianchi et al. 2022](http://www.cerge-ei.cz/pdf/wp/Wp730.pdf)) | 10.83 median (5.76 to 109.59) | <= -11.95 | 592 | 0.00 | DROP |
| 8 | Non-Plan-58 BTC time-of-day windows (docs 79, 119, Replay 19) | BTC (`BIP`) | ~2,465 | Best non-Plan-58 window: Europe 08:00 to 13:00 UTC +3.89 bps gross ([Janorium Nov 2026](https://janorium.com/articles/bitcoin-weekend-time-of-day-returns)); Asia short +0.8 to +2.8 bps; 23:00 UTC short +2.7 bps | 5.76 (3.50 at $100k BTC) | -1.87 (+0.39) | 100 | 0.00 (0.04) | DROP (< 4) |
| 9 | Stablecoin mint / treasury supply jump 24h BTC (docs 43, 85, 119) | BTC (`BIP`) | ~200 to 565 | Pre-2021 +63 bps weakly sig ([arXiv 2501.05232](https://arxiv.org/pdf/2501.05232)), but [Ante et al. BRL WP 15](https://www.blockchainresearchlab.org/wp-content/uploads/2020/05/BRL-Working-Paper-15-v2.pdf) and [NY Fed Apr 2025](https://libertystreeteconomics.newyorkfed.org/2025/04/stablecoins-and-crypto-shocks-an-update/) show inflows follow BTC jumps (zero forward edge) | 5.76 | <= 0 | 260 | 0.00 | DROP |
| 10 | Large liquidation-day reversal (docs 41, 119, Row 28) | BTC (`BIP`) and major alts | 72 (6-yr OOS alts) | BTC 11/20 lower in 24h ([Liqwall Oct 2026](https://liqwall.com/learn/research/btc-after-liquidation-cascades)); altcoins +98 bps BTC-hedged alpha p=0.182 ([claude-quant May 2026](https://github.com/Isk4R1oT/claude-quant/blob/main/research/2026-05-27-liquidation-cascade-and-ofi.md)) | 10.83 median | +87.2 | 600 | 1.52 | DROP (< 4) |
| 11 | 12h Kraken BTC/ETH reversal, 24h intraday reversal, CME weekend gaps, BRRNY 4pm fixing (docs 115, 119) | BTC (`BIP`), ETH (`ETP`) | 458 to 3,650 | 12h Kraken insignificant at 0 to 2 bps ([MDPI Nov 2026](https://www.mdpi.com/1911-8074/19/9/692)); CME gaps negative after 10 bps RT and CME went 24/7 May 2026 ([RipBacktest](https://ripbacktest.com/posts/bitcoin-cme-gap-fill/)); BRRNY slippage <= 1 bp ([Nasdaq](https://www.nasdaq.com/articles/suitability-analysis-cme-cf-bitcoin-reference-rate-new-york-variant-basis-regulated)) | 5.76 / 20.66 | <= 0 | 80 to 435 | 0.00 | DROP |
| 12 | Replay 03 hourly intraday rules `H1` to `H8` (docs 15, 16, 95) | BTC (`BIP`), ETH (`ETP`) | ~427 held-back (`H7`) | MEASURED in Replay 03: all 8 BTC rules lost on held-back 2023 to 2026 at 14 bps RT (`H1` -16.7%/yr, `H7` -4.2%/yr); saving 8.24 bps/trade leaves `H7` at ~+4.8 bps/trade net; `ETP` (20.66 bps) is costlier than Binance.US (14 bps) | 5.76 (BTC) / 20.66 (ETH) | +4.8 (`H7` BTC) | 180 | 0.30 | DROP (< 4) |
| 13 | Replay 09 seven crypto rules (docs 28, 95) | AVAX, BTC, DOGE, ETH, LINK, LTC, SOL, XRP | 1 to 147 | MEASURED in Replay 09: 6 of 7 rules had 0.00 bps break-even vs holding BTC; `MOM` lost -31.01% held-back with Deflated Sharpe 0.000 | 5.76 to 59.70 | <= 0 | 300 | 0.00 | DROP |
| 14 | Replay 01 daily trend on BTC `P1`, `P2`, `S50`, `D20` (docs 16, 95) | BTC (`BIP`) | ~10 to 30 switches | MEASURED in doc 16: already tested at 14 bps RT (Binance.US) and rejected on knife-edge PBO (0.2409 to 0.4205) and non-engine fixes; multi-week holds also incur UNKNOWN hourly funding carry | 5.76 + funding | n/a | n/a | n/a | DROP (PBO / low N / funding) |

Note on small-coin-only ideas excluded by the strict coin-match rule (STATED):

- Bottom-98% daily crypto reversal (`Zaremba et al. 2021`, doc 41), micro-cap `$10,000` daily volume premium (`arXiv:2610.23283v2`, doc 41), Upbit KRW listing shorts (Replay 20, where Row 48 found only 1 of 205 notices overlapped a US-shortable contract), exchange delistings and monitoring tags (0 full delistings on the 24 CFM coins in 2024 to 2026 per Round 24), Coinbase/Binance new-listing chases (docs 43, 85, 115), small-protocol DeFi hacks (median $65.63M cap in NY Fed SR 1153, doc 43), and DAO governance votes (only AAVE on CFM; doc 49 found nothing after costs) do not transfer to BTC, ETH, or the 24 CFM contracts and are excluded.

Note on Plan 58 overlap (STATED):

- The only crypto clock pattern in our entire archive whose published gross edge (+7.1 to +7.8 bps per 2-hour window on BTC) sits above `BIP`'s hypothetical $100,000 BTC cost floor (3.50 bps) is the 21:00 to 23:00 UTC Bitcoin window, which is already queued as Queue Row 98 / Plan 58 (`research_rig/PREREG_58_btc_hour_of_day.md`) and gated on live top-of-book spread collection in Measurement 59 (`research_rig/MEASURE_59_crypto_clock_costs.md`). Notably, at the Nov 26, 2026 catalog price ($60,735 BTC), `BIP`'s fixed clearing plus one tick is 5.76 bps (leaving only ~+1.34 to +2.04 bps net before variable commission and real spread, screen ~1.80 < 4), which reinforces why Measurement 59 must verify actual executable spreads and commissions before Plan 58 freezes.

## Task 3: Data requirements and Plan 58 overlap for clearing ideas

Nothing cleared the power screen of 4. No new queue row is opened (row 99 stays unused), and no new historical price pull is requested. The only existing candidate near the boundary is Plan 58 (Queue Row 98), which already has its own cost-measurement spec in `research_rig/MEASURE_59_crypto_clock_costs.md`.
