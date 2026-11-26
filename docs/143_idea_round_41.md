# Round 41: High-Count Forced-Flow Screen (>= 300 Events Since 2016, >= 100 bp Move)

Date: 2026-11-26 12:02 UTC
Status: Reading only, no prices opened and no return calculation run by us.
Queue rows added: 0 (rows from 110 stay unused).

## Gates and scope

Every candidate in Round 41 had to clear both hard gates on a `$500` US cash brokerage account or US crypto account (Coinbase / Kraken) plus the Doc 117 power screen (`docs/research/117_power_screen_before_data.md`, `events * (net_edge / paired_noise)^2 >= 4`):

- Gate (a): at least `300` independent dated events since 2016 countable from lawful, free public filings or exchange notices without reading prices.
- Gate (b): a published or measurable move of at least `100 bp` at a tradable print (closing auction or next open) in liquid US-listed names or major crypto on Coinbase or Kraken.

Before searching, `docs/QUEUE.md` (skip lists, Next, and Done) and `docs/research/117_power_screen_before_data.md` were read in full. Six of the eight prompted areas are already closed, blocked on data licensing, or skipped in `docs/QUEUE.md`; two areas received fresh primary-source checks (convertible bond issuance days, never audited in Rounds 1 to 40, and equity-level credit-rating downgrades alongside updated lock-up evidence). None of the eight cleared both gates.

## Summary table

| Candidate area | Prior `QUEUE.md` status | Gate (a): >= 300 free dated events since 2016? | Gate (b): >= 100 bp tradable move on $500 US? | Doc 117 screen | Verdict |
|---|---|---|---|---|---|
| 1. Index adds/deletes outside S&P 500 (Russell, S&P 400/600, NDX) | `Row 42`, `Row 76`, `Row 87`, Rounds 24 and 27 | FAIL (no lawful free point-in-time lists; Russell/NDX are 10 annual dates) | S&P 600 ~6% mostly pre-open; NDX ~2% incl. pre-ann | UNKNOWN / blocked on license | DROP |
| 2. ETF create/redeem and leveraged-ETF close rebalances | Rounds 19, 33, 34, 35, 36; line 148 | FAIL (needs prices to spot large-move days, not filings) | FAIL (0 to null post-2016 US net edge) | 0.00 | DROP |
| 3. CEF tender offers and term-fund liquidations | `Row 38 / Replay 21`, `Row 88 / Plan 50`, Rounds 24 and 39 | FAIL (106 odd-lot tenders, 14 placed; 22 strict term-fund events << 300) | FAIL (pro-rated ~50 bp; odd-lot failed Replay 21) | 0.00 / closed on count | DROP |
| 4. Forced selling after credit rating downgrades (bonds + stocks) | Bond ETFs Round 32; equities FRESH | FAIL (no required SEC 8-K downgrade calendar) | FAIL (bond ETF `ANGL`/`FALN` ~5 bp; single bonds unreachable; stocks drift negative, short-only) | 0.30 (ETF) / 0.00 (long stock) | DROP |
| 5. Spin-off forced selling | `Row 58 / Plan 55` (Done, closed on power) | FAIL (MEASURED 100 dated distributions < 300) | Closest short-window gain +2.11% gross not significant | 32.86% power < 50% floor | DROP |
| 6. IPO lock-up expirations | Rounds 16 and 32; refreshed here | PASS (~300+ US IPOs via S-1/424B4 180-day dates) | FAIL (permanent -161 to -200 bp drop, no rebound; short-only) | 0.00 (long-only) | DROP |
| 7. Convertible bond issuance days (FRESH) | Never audited in Rounds 1 to 40 | PASS (~1,100 to 1,300+ US deals 2016 to 2026 via 8-K / 424B5) | FAIL (drop is overnight/short-only; peak long rebound `CAR(2,10)` only +54 bp < 100 bp, -339 bp Post-Lehman) | 2.39 (peak) / 0.00 (Post-Lehman) | DROP |
| 8. Crypto token unlocks with public schedules | `Row 36` forward logger, Rounds 15, 23, 24, 26 | FAIL (free historical dated schedules do not exist; 29 US-shortable coins) | FAIL (Albiez 2026 n=913 cliffs -14 bp net of drift, insignificant; short-only) | 0.00 | DROP |

## Candidate 1: Index additions and deletions outside the S&P 500 (Russell, S&P 400/600, Nasdaq-100)

Prior status in `docs/QUEUE.md`: ALREADY BLOCKED / SKIPPED (`Row 42` Russell 2000 additions, `Row 76` S&P 600 WATCH, `Row 87` S&P 400/600/NDX deletions, Round 24 NDX additions skip, Round 27 small-cap/micro-cap index drop).

Source, stated size, sample, and print: STATED in `docs/QUEUE.md` (`Row 42`, `Row 76`, `Row 87`, Round 24, Round 27), Greenwood and Sammon (2025) report roughly `+6%` (`600 bp`) for S&P SmallCap 600 additions and Dimensional (2024) documents elevated small-cap reconstitution impact around effective close, while Nasdaq-100 December additions shrank to `+2.0%` including pre-announcement days. Tradable print is announcement-plus-1 open or effective closing auction.

First count estimate (Gate a): FAIL. `Row 87` MEASURED SEC EDGAR Form 8-K hits across 2016 to 2026 at only `1` for S&P MidCap 400, `0` for S&P SmallCap 600, and `0` for Nasdaq-100 removals. Official historical pro-forma and change lists are legally blocked from free storage: FTSE Russell lists are client-only (`Row 42`), S&P DJI and Nasdaq Legal Section 11 prohibit storing or reproducing archives (`Row 87`, HTTP 403 on archives), and CRSP pro-forma lists are subscriber FTP only (Round 27). Even with paid data, Russell annual June reconstitutions and Nasdaq-100 annual December reconstitutions yield only `10` to `11` independent annual turns since 2016 (`<< 300` per Doc 117).

Why it is forced: Passive index funds and ETFs tracking the benchmark must trade additions and deletions near the effective close to minimize tracking error.

What killed or shrank it: Announcement-day overnight jumps absorb much of the addition move before next-open entry, Nasdaq-100 share prices often exceed `$250` to `$600` (limiting `$500` whole-share execution), and index providers keep historical point-in-time rosters behind commercial licenses.

Verdict: DROP. Fails Gate (a) on both lawful free public-filing count and independent turn count.

## Candidate 2: ETF creation/redemption and leveraged-ETF rebalancing flows near the close

Prior status in `docs/QUEUE.md`: ALREADY SKIPPED (Rounds 19, 33, 34, 35, and 36; `docs/QUEUE.md` line 148).

Source, stated size, sample, and print: STATED across prior rounds (`docs/QUEUE.md` lines 11, 35, 37, 39, 41, 148), Lenkey (2024 QFE survey) finds no profitable leveraged-ETF end-of-day rebalancing strategy, Woo (August 2026, arXiv:2608.22768) finds all six US leveraged crypto ETF close-rebalance cross-reversal directions null, Vidovich and Zerjal (November 2026, arXiv:2611.09286) find `-3.5 bp` (`t = -1.3`) around single-stock LETF launches, and Ashish (2026) plus Fabus et al. (SSRN 7545019) find no positive return after spot crypto ETF creation/redemption flows become public. Tradable print is 15:50 to 16:00 ET close / next open.

First count estimate (Gate a): FAIL as a filing/notice setup (identifying large-move rebalancing days requires price returns, not public filings or exchange notices).

Why it is forced: Leveraged ETFs reset daily exposure near the close in the direction of the day's move, and authorized participants create or redeem ETF shares against underlying baskets.

What killed or shrank it: Competing closing-auction liquidity providers anticipate mechanical LETF rebalancing well ahead of 16:00 ET, reducing net tradable moves to roughly zero (`< 100 bp`, Doc 117 screen `0.00`).

Verdict: DROP. Fails Gate (b) and already skipped across five prior rounds.

## Candidate 3: Closed-end fund tender offers and term-fund liquidations

Prior status in `docs/QUEUE.md`: ALREADY DONE / SKIPPED (`Row 38 / Replay 21` cash odd-lot tenders, `Row 88 / Plan 50` CEF term-fund liquidations closed on count, Round 24 pro-rated CEF tenders skip, Round 39 skip).

Source, stated size, sample, and print: MEASURED in `Replay 21` (`docs/research/97_replay_21_odd_lot_tenders.md`), cash issuer odd-lot tenders placed `14` of `106` eligible offers (`+11.80%` mean net, `t = 1.688`, failed 4 of 6 marks). STATED in Round 24, pro-rated CEF cash tenders without odd-lot priority show roughly `0.5%` (`50 bp < 100 bp`), insignificant after costs. MEASURED in `Plan 50 / Row 88`, listed CEF liquidations, term maturities, and open-endings had only `22` strict documentary candidates from 2016 to 2026.

First count estimate (Gate a): FAIL (`106` total cash issuer odd-lot tenders with `14` qualifying at discount, and `22` strict CEF term-fund events; both far below `300`).

Why it is forced: Issuers buy back shares at or near NAV on a fixed expiration or liquidation date, forcing discount convergence.

What killed or shrank it: Low event frequency in US listed CEFs, pro-ration on non-odd-lot tenders, and pre-entry narrowing before the first tradable open after filing.

Verdict: DROP. Fails Gate (a) (`<< 300` events) and already tested or closed on count.

## Candidate 4: Forced selling by funds after credit rating downgrades

Prior status in `docs/QUEUE.md`: Bond ETF proxy (`ANGL` / `FALN` vs `HYG`) skipped in Round 32 (`docs/121_idea_round_32.md`); single-stock equity downgrade check is FRESH here.

Source, stated size, sample, and print:
- Corporate bonds: STATED from [Pictet Asset Management (June 2025)](https://am.pictet.com/us/en/investment-views/fixed-income/2025/catching-fallen-angels), fallen-angel corporate bonds downgraded from investment grade to high yield carry an "average excess credit spread premium of 120bps" and "deliver excess returns of 3.1 percentage points in the following year and 4.5 percentage points in the following two years relative to the peers in the high yield index." However, single OTC corporate bonds trade in `$1,000`+ institutional lots unreachable on `$500` cash, and Round 32 showed the US-listed ETF proxy (`ANGL`/`FALN` vs `HYG`) dilutes the month-end forced-selling move to `~5 bp` (`<< 100 bp`, Doc 117 screen `0.30 < 4`).
- Equities (FRESH check): STATED from [Avramov, Chordia, Jostova, and Philipov](https://haas.berkeley.edu/wp-content/uploads/bus.pdf) (confirming Dichev and Piotroski 2001), downgraded equities do NOT experience a buyable forced-selling rebound; instead they suffer severe continuing negative drift: "In the year before (after) the downgrade, the return for the lowest rated stocks is -50.15% (-3.78%), while the corresponding figure for the highest quality stocks is 7.68% (11.87%)." "However, our findings indicate that the cumulative stock returns of the highest credit risk stocks are negative for upto twelve months following a downgrade and lower than those of the lowest credit risk stocks for upto twenty-four months." In Table 4, lowest-rated stocks (`C10`) return `-5.64%` in the month after downgrade and `-7.91%` over months 1 to 6.

First count estimate (Gate a): FAIL. Credit-rating agency downgrades are NOT mandatory SEC Form 8-K filings unless they trigger a material debt acceleration under Item 2.04, so no free public-filing calendar of >= 300 dated rating downgrades exists back to 2016.

Why it is forced: On the bond side, [Pictet](https://am.pictet.com/us/en/investment-views/fixed-income/2025/catching-fallen-angels) explains: "investment grade investors are generally forbidden by their mandates to hold bonds with a junk rating (i.e. high yield), so they become forced sellers of fallen angels."

What killed or shrank it: For a `$500` US equity brokerage account, the bond forced-selling rebound cannot be accessed directly (and is diluted to `~5 bp` in ETFs), while downgraded common stocks drift sharply lower (short-only, unreachable on a `$500` cash account).

Verdict: DROP. Fails Gate (a) (no free SEC downgrade calendar) and Gate (b) (bond ETF ~5 bp; downgraded equities short-only).

## Candidate 5: Spin-off forced selling

Prior status in `docs/QUEUE.md`: ALREADY DONE (`Row 58 / Plan 55`, ledger 192, closed on synthetic power before prices in `research_rig/CLOSE_55_on_power.md`).

Source, stated size, sample, and print: MEASURED in `Plan 55` (`docs/QUEUE.md` line 187 and `docs/research/117_power_screen_before_data.md`), US spin-offs yield `100` dated distributions (a documented lower bound), and the closest published short-window post-selling rebound (`+2.11%` gross, not statistically significant) produced only `32.86%` central synthetic power (`19.27%` with stressed costs) against the 50% floor.

First count estimate (Gate a): FAIL (`100` dated distributions `< 300`).

Why it is forced: Parent-company index funds and mandate-constrained institutional holders automatically receive spin-off shares they are not permitted to hold and sell them after distribution.

What killed or shrank it: Low annual count of US corporate spin-offs (roughly 10 per year) and high single-stock idiosyncratic volatility relative to the post-selling rebound.

Verdict: DROP. Fails Gate (a) (`100 < 300`) and already closed on synthetic power as `Plan 55`.

## Candidate 6: IPO lock-up expirations

Prior status in `docs/QUEUE.md`: ALREADY SKIPPED in Round 16 (`docs/research/86_round_16_edgar_stock_events.md`) and Round 32 (`docs/121_idea_round_32.md`); verified against primary source here.

Source, stated size, sample, and print: STATED from [Bradley, Jordan, Yi, and Roten (2001)](https://www.uky.edu/~icrote2/venture.pdf) across `2,529` US IPOs (1988 to 1997): "Based on a sample of 2,529 IPOs for the ten-year period ending in 1997, we find that lockup expirations are associated with significant price declines." "The average abnormal return on the lockup expiration day is -.74 percent, and the cumulative abnormal return over the five-day surrounding period is -1.61 percent, both of which are significant at any conventional level." Crucially, there is NO long-side rebound after the forced insider selling: "As illustrated, there is no tendency for the prices to rebound shortly following lockup expiration. Instead, there appears to be a permanent decline of about 2 percent, virtually all of which occurs in the days surrounding the expiration of the lockup."

First count estimate (Gate a): PASS (~300+ US IPOs since 2016 with standard 180-day lock-up dates disclosed in SEC Form S-1 / 424B4).

Why it is forced: Venture-capital funds, private-equity sponsors, and early insiders are contractually barred from selling for 180 days after the IPO and liquidate shares once the lock-up lifts.

What killed or shrank it: The `-161` to `-200 bp` move is permanent and negative (short-only, unreachable on a `$500` US cash account, and concentrated in VC-backed IPOs with high stock-borrow fees). There is no >= 100 bp US long rebound (Doc 117 screen `0.00`).

Verdict: DROP. Fails Gate (b) for a `$500` US long-only cash account.

## Candidate 7: Convertible bond issuance days (FRESH)

Prior status in `docs/QUEUE.md`: FRESH. Never audited in Rounds 1 to 40.

Source, stated size, sample, and print:
- Event count (Gate a): PASSES EASILY. STATED from [Mayer Brown (February 2025)](https://www.mayerbrown.com/-/media/files/perspectives-events/events/2025/02/convertible-bond-offerings-replacing-outstanding-converts.pdf?rev=-1), US convertible debt offerings totaled `924` deals from 2016 through 2024 (`61` in 2016, `92` in 2017, `111` in 2018, `106` in 2019, `165` in 2020, `149` in 2021, `54` in 2022, `79` in 2023, `107` in 2024, plus `6` in early 2025), in liquid mid/large-cap US stocks (`$14,558 million` average market cap across `113` deals in 2024 to early 2025). Broader [Dealogic figures reported by ION Analytics (June 9, 2026)](https://ionanalytics.com/insights/mergermarket/us-convertible-issuance-races-toward-another-record-as-ai-financing-demand-grows/) count `265` US deals in 2024 (`USD 96.1bn`), record `USD 140.5bn` in 2025, and `127` deals (`USD 85.5bn`) through early June 2026 (`~1,100` to `1,300+` dated offerings since 2016, publicly filed in SEC Form 8-K Items 1.01, 3.02, 8.01 and Form 424B5).
- Announcement drop vs tradable post-issuance rebound (Gate b): FAILS. STATED from [Duca, Dutordoir, Veld, and Verwijmeren (2012, Journal of Banking and Finance, 1,436 US convertible issues 1984 to 2009)](https://eprints.gla.ac.uk/62890/1/62890.pdf), announcement-period `(-1, +1)` abnormal stock returns are large and negative: "While convertible offerings announced between 1984 and 1999 induce average abnormal stock returns of -1.69%, convertible announcement effects over the period 2000 to 2008 are more than twice as negative (-4.59%)." "Our event study results indicate that average stock returns around the announcements of convertible bonds issued between the Lehman Brothers collapse in September 2008 and December 2009 are almost twice as negative as in the Arbitrage period (-9.12%)." In 2024 to early 2025, [Mayer Brown](https://www.mayerbrown.com/-/media/files/perspectives-events/events/2025/02/convertible-bond-offerings-replacing-outstanding-converts.pdf?rev=-1) similarly reports an average stock impact of `-6.65%` across `113` deals. However, a `$500` US cash account cannot short stocks, and offerings are typically announced after the close or pre-market and priced within 24 hours, so the drop happens in the overnight gap before a retail next-open fill.
- On the **tradable long rebound after pricing (`t+2` to `t+10`)**, [Duca et al. (2012)](https://eprints.gla.ac.uk/62890/1/62890.pdf) measure only `+0.503%` (`+50.3 bp`) over `(2, 5)` and `+0.541%` (`+54.1 bp`) over `(2, 10)` even in the peak 2000 to 2008 Arbitrage period (`N = 645`): "The positive abnormal stock return of 0.54% over window (2, 10) represents approximately 12% of the absolute value of the announcement-period CAR (0.54/4.59)." Worse, the rebound vanished and flipped negative in the Post-Lehman sample (`N = 64`, `CAR (2, 5) = -1.848%`, `CAR (2, 10) = -3.391%`): "By contrast, we find no evidence of a positive stock price reversal in the Traditional Investor and Post-Lehman periods. In fact, abnormal stock returns over the window (2, 10) are significantly negative during both periods."
- Related maturity-averaging sub-check: STATED from [Gatti et al. (March 2025, European Financial Management)](https://onlinelibrary.wiley.com/doi/full/10.1111/eufm.12514), across `89` in-the-money cash-settled US convertible maturities from 2003 to 2021, the full-sample averaging-period `CAR` was `-0.44%` (market model) and `-0.52%` (Carhart); only the uncontaminated subsample without option overlays (`Subsample A`, `N = 21` bonds across 19 years, `<< 300`) was positive (`+4.67%`).

Why it is forced: Convertible arbitrage hedge funds buy the newly issued convertible bond and immediately short-sell the underlying common stock on announcement/pricing day to establish a delta-neutral hedge.

What killed or shrank it: First, roughly 88% of the announcement drop is permanent dilution/signaling rather than temporary price pressure, leaving only `+54 bp` (`< 100 bp`) even in the peak 2000 to 2008 arbitrage era and `-339 bp` Post-Lehman. Second, modern US issuers pair roughly half of all convertible offerings with **capped calls or call-spread overlays** (`55` of `113` deals = `48.7%` in [Mayer Brown 2024 to 2025 YTD](https://www.mayerbrown.com/-/media/files/perspectives-events/events/2025/02/convertible-bond-offerings-replacing-outstanding-converts.pdf?rev=-1)), where bank dealers buy common stock to hedge the option overlay and offset convertible-arbitrage short selling ([Gatti et al. 2025](https://onlinelibrary.wiley.com/doi/full/10.1111/eufm.12514): "For convertible bonds that are combined with option overlays, hedging-related buying by arbitrageurs seems to be compensated by hedging-related selling by option dealers.").

Doc 117 screen: Even taking the generous peak 2000 to 2008 `+54 bp` gross reversal minus `10 bp` round-trip cost (`+44 bp` net) across `N = 1,000` deals with `900 bp` 8-day single-stock paired SD gives `1000 * (44 / 900)^2 = 2.39 < 4`; under Post-Lehman (`-339 bp`) or modern capped-call dilution, the screen is `0.00`.

Verdict: DROP. Passes Gate (a) with `~1,100+` deals, but fails Gate (b) (`+54 bp < 100 bp` at peak, negative Post-Lehman) and fails the Doc 117 power screen.

## Candidate 8: Crypto token unlocks with public schedules

Prior status in `docs/QUEUE.md`: ALREADY TRACKED / SKIPPED (`Row 36` forward logger running off-repo since 2026-11-25; Rounds 15, 23, 24, and 26; `docs/research/62_round_7_outside_evidence.md`).

Source, stated size, sample, and print: STATED in `docs/QUEUE.md` (`Row 36` and Round 26), Albiez (2026, SSRN 7567460) measured `913` scheduled Binance cliff unlocks and found a `-0.14%` (`-14 bp`) 3-day abnormal return net of token drift (`95% CI -0.81% to +0.53%`, statistically insignificant). Keyrock (December 2024) and Kim (2026, SSRN 6632838) report larger negative drift starting 30 days pre-unlock or on large cliffs, which are short-only.

First count estimate (Gate a): FAIL. Historical point-in-time unlock schedules back to 2016 are paid-only (doc 62), and only `29` non-BTC/ETH coins are shortable on US venues (Round 24 found only `1` confirmed >5% cliff unlock in the next 60 days on those 29 coins).

Why it is forced: Early investors, founders, and team wallets receive newly unlocked tokens on fixed vesting cliffs and liquidate part of their holdings.

What killed or shrank it: Market anticipation front-runs known cliff dates (leaving `-14 bp` insignificant 3-day abnormal return in Albiez 2026), free dated historical schedules do not exist, and US retail venues cannot short most unlocking altcoins.

Verdict: DROP as a new queue row (fails both gates; `Row 36` forward logger remains active off-repo).
