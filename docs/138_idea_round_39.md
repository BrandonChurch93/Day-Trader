# Idea Round 39: Gap-to-a-known-value trades with a fixed date

Date: 2026-11-26 11:30 UTC
Queue rows queued: 0 (rows from 110 stay unused)
Scope: Every listed instrument of the shape "a listed thing trades away from a value it must reach, or be redeemable at, on a known date" reachable in a $500 US cash brokerage account (whole shares, long-only or paired with a liquid ETF, no short borrow) or on Coinbase or Kraken US spot, screened against prior skip lists and the Doc 117 pre-data power floor (`N * (net_edge / noise)^2 >= 4`). No market prices were pulled and no returns were computed.

## Bottom line

Zero new queue rows clear the Doc 117 power screen and prior skip lists. All five prompted categories were already closed on count, tested, or skipped in earlier rounds (`Plan 50 / Row 88`, `Round 27`, `Round 25`, `Round 35`, `Round 33`, and `Replay 21`), and every fresh check of the same fixed-date shape (Coinbase and Kraken fixed-ratio token migrations and wind-downs, target-maturity bond ETFs, exchange-traded baby bonds and preferred stocks after call notices, and exchange-traded notes after call notices) drops on count below 30, zero excess spread over T-bills or NAV after retail spreads, floating post-notice payout, or retail fee walls. Standard US ETF cash liquidations remain active as Queue Row 95 and live forward watch `E07` (`practice/traders/E07_etf_closure_payout_watch.md`) and are not re-queued here.

## Summary screen table

| # | Candidate | Prior skip or closure | Events per yr (2016 to 2026) | Published net size | Doc 117 screen | Verdict |
|---|---|---|---|---|---|---|
| 1 | CEF fixed-term, target-term, liquidations, open-endings, ETF conversions | Closed on count: Plan 50 / Row 88 (22 strict vs 30) | ~2.2/yr strict (MEASURED) | STATED >10 pp pre-cost in old studies; post-2016 net UNKNOWN | < 4 (count 22 < 30) | DROP (already closed on count) |
| 2 | CEF rights offerings (subscription drop and post-expiry rebound) | Skipped: Round 27 and Round 25 | ~34 transferable / ~9.7 non-transferable per yr (MEASURED Round 27) | STATED main move is downward slide (short-only); post-expiry rebound weak | 0.00 | DROP (already skipped) |
| 3 | SPAC shares below trust value ahead of redemption deadline | Skipped: Round 25 | ~43/yr DEFM14A (MEASURED Round 25); 66 IPOs in 7 qtrs to end-2023 (STATED) | STATED small spread over T-bills; -$50 to -$100 DWAC fee on $500 | 0.00 | DROP (already skipped; retail fee wall) |
| 4 | Crypto trusts and CEFs with dated conversion or redemption | Skipped: Round 35 | ~1 to 1.5/yr (MEASURED Round 35; 10 converted, 3 OTC >$20M left) | UNKNOWN net; 2.50% fee + 50 to 200+ bps/side OTCQX spread | < 4 (N < 30) | DROP (already skipped) |
| 5 | Cash merger and tender deals | Skipped: Round 33, Round 24; tested Replay 21 (`E03`) | ~150 to 215/yr all M&A; 428 usable 2016 to 2024 (STATED) | STATED median -20 bps gross 2016 to 2024 (Wang 2026) | 0.00 to 0.82 | DROP (already skipped / tested) |
| 6 | Crypto fixed-ratio token migrations, mergers, and wind-downs (Coinbase / Kraken) | New check | < 1/yr non-1:1 or fixed-USD auto-converted (STATED: 3 on Coinbase table) | UNKNOWN (zero published net-of-cost study) | 0.00 / UNKNOWN | DROP (N < 10; 80 to 180 bps RT fees; unhedged altcoin risk) |
| 7 | Target-maturity bond ETFs (`iShares iBonds`, `Invesco BulletShares`) | New check | ~2.8/yr iBonds liquidated since 2010 (STATED: 44 in 16 yrs) | STATED 0.00% gap on `IBTG`; `IBDQ` liquidated in line with final close | 0.00 | DROP (AP arb eliminates discount) |
| 8 | Baby bonds ($25 par) and preferred stocks after call notice | New check | UNKNOWN exact census (~20 to 50/yr SEC 8-K notices) | STATED "small discount for the days remaining" (~0 bps excess over T-bills) | 0.00 | DROP (T-bill carry only; 10 to 30 bps spread) |
| 9 | Exchange-traded notes (ETNs) after mandatory call or acceleration | New check | UNKNOWN exact census | UNKNOWN long-only; suspended-creation ETNs trade at premiums (short-only) | 0.00 | DROP (payout floats over 1 to 10 days after notice) |

## Candidate evaluations

### 1. Closed-end funds with a fixed term, target-term, announced liquidation, open-ending, or ETF conversion

Mechanism: Buy a discounted US closed-end fund after a dated board notice of liquidation, open-ending, ETF conversion, or approaching fixed termination date so the discount must close to NAV by the termination date.

Prior skip list status: MEASURED already closed on count before prices as Queue Row 88 and Plan 50 (`research_rig/CLOSE_50_on_count.md`, ledger 184).

Sources and quotes: MEASURED in `research_rig/CLOSE_50_on_count.md`: "The independent price-blind review found **22 strict documentary candidates against a floor of 30** set before the count." That total across 2016 through March 10, 2026 comprised 6 cash liquidations, 15 scheduled term maturities, and 1 open-ending. CEF-to-ETF conversions (`FGB`, `FDEU`, `FEI`, `FEN`, `FIF`, `FPL`) were already audited inside the 79-row Plan 50 discovery docket and excluded for unmapped mandates or unverified last regular trading sessions.

Published size and net status: STATED in `docs/QUEUE.md` (Row 102) and older CEF termination studies that pre-cost discount narrowing can reach mid-single to low-double digits, while post-2016 net-of-cost returns on strict board-backed US terminations remain UNKNOWN because Plan 50 closed price-blind on count.

Events per year and point-in-time free source: MEASURED ~2.2 strict events per year (22 in 10.2 years) from SEC EDGAR (`N-8F`, `8-K`, `DEF 14A`, `N-2`, and `497` filings).

Knowability before trade: MEASURED partially knowable from dated SEC filings, but `CLOSE_50_on_count.md` documented that many historical notices lacked a timely last regular exchange session or board recommendation prior to entry.

What a $500 account can do: Whole shares of $8 to $25 CEFs fit easily with no short borrow, though CEF spreads run 10 to 30+ bps per side and pairing with a liquid bond or equity ETF cuts position size in half.

Doc 117 screen: Fails the 30-event floor (`N = 22 < 30`; screen `< 4` under strict count).

Verdict: DROP. Already closed on count as Plan 50 / Row 88; December 2026 to February 2027 manual forward watch remains in place off-repo.

### 2. Closed-end fund rights offerings (subscription-period drop and post-expiry rebound)

Mechanism: Buy a closed-end fund after subscription-period dilution and price pressure fade on the fixed rights expiration date, seeking a post-expiry rebound toward pre-offer discount levels.

Prior skip list status: MEASURED already skipped in Round 27 (`docs/research/111_round_27_higher_payoff_forced_flows.md`) and Round 25 (`docs/research/100_round_25_too_small_for_big_money.md`).

Sources and quotes: STATED from [Khorana, Wahal, and Zenner (2002, Journal of Financial and Quantitative Analysis)](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/agency-conflicts-in-closedend-funds-the-case-of-rights-offerings/A9BD552704DEECFB4E2BC7E2627D42EC): "We study 120 rights offerings by closed-end funds from 1988–1998. On average, rights offerings are announced when funds trade at a premium. This premium turns into a discount over the course of the offering." Round 27 further verified that post-offering rebounds are weak and dominated by permanent price pressure, while Round 25 verified that US CEF rights offerings allocate oversubscriptions pro rata rather than by odd-lot priority.

Published size and net status: STATED the primary published move is a downward premium-to-discount decline during the offering (short-only, pre-cost); post-expiry long-only net edge is near zero or negative after spreads.

Events per year and point-in-time free source: MEASURED in Round 27 at 343 transferable and 97 non-transferable SEC EDGAR filings over 2016 to 2026 (~34 and ~9.7 per year).

Knowability before trade: STATED the subscription start and expiration dates are published in dated SEC `N-2` and `497` filings, but there is no fixed redemption value the shares must reach at expiry.

What a $500 account can do: Whole shares are affordable, but a $500 cash account cannot short the fund during the subscription period, and subscribing via rights on $500 produces trivial dollar gains after spreads and dilution.

Doc 117 screen: `0.00` (no positive net long-only post-expiry edge).

Verdict: DROP. Already skipped in Rounds 25 and 27; no new post-2016 replication contradicts those skips.

### 3. SPAC shares below trust value ahead of a redemption deadline

Mechanism: Buy listed SPAC common shares trading below their pro-rata cash-in-trust value before a merger vote or liquidation deadline and redeem for cash plus accrued Treasury interest on the fixed redemption date.

Prior skip list status: MEASURED already skipped in Round 25 (`docs/research/100_round_25_too_small_for_big_money.md`).

Sources and quotes: STATED from [AQR (October 2024, Are SPACs Still Alive?)](https://www.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Are-SPACs-Still-Alive.pdf): "Spread-to-trust is the difference between the yield-to-trust, the annualized return an investor would earn by buying SPAC equity today and redeeming for the trust value on the expiration date, and the yield on Treasury bills maturing on the SPAC’s expiration date." AQR further states: "The spread-to-trust trade prompted our entry to the SPAC market in 2008, but similar opportunities of smaller magnitude were common prior to the SPAC boom of 2020-2021 as well as in 2022 after SPACs fell out of favor (see Figure 3 above)." On post-2022 issuance compression, AQR states: "In contrast, only $8 billion was raised by 66 vehicles over the following seven quarters between the SEC’s proposal and the end of 2023." On retail redemption fees, STATED from [Interactive Brokers FAQ](https://www.interactivebrokers.com/support/faq/content/request-special-purpose-acquisition-company-160415308): "A SPAC redemption request is subjected to 100 USD processing fee."

Published size and net status: STATED institutional spread-to-trust excess over T-bills is small in normal post-2021 markets (Round 25 estimated roughly $5 to $20 per year on $500 before fees), and negative net of retail voluntary reorganization fees.

Events per year and point-in-time free source: MEASURED in Round 25 at 477 `DEFM14A` unique issuer-years over 2016 to 2026 (~43/yr) from SEC EDGAR (`424B4`, `10-Q`, `DEFM14A`, `8-K`).

Knowability before trade: STATED trust balance per share and the redemption cutoff (typically two business days before the shareholder meeting) are stated in dated SEC `DEFM14A` and `10-Q` filings.

What a $500 account can do: Whole shares at ~$10 fit (~48 shares), with no short borrow needed, but submitting a voluntary redemption triggers a $100 processing fee at Interactive Brokers (or $50 at Alpaca per Round 25), which is -10% to -20% on a $500 position and wipes out years of spread-to-trust carry. Selling in the secondary market before the redemption cutoff avoids the DWAC fee only by selling to an arbitrageur who still discounts T-bill carry and operational friction, while missing the cutoff removes the trust floor and exposes the shares to post-merger de-SPAC losses.

Doc 117 screen: `0.00` (negative net of voluntary reorganization fees on $500).

Verdict: DROP. Already skipped in Round 25; retail reorganization fees make this an institutional-scale arbitrage only.

### 4. Crypto trusts and closed-end crypto vehicles reachable through a brokerage with a dated conversion or redemption

Mechanism: Buy a discounted US-brokerage-accessible OTC crypto trust or closed-end vehicle after a dated SEC ETF conversion filing or redemption notice so the discount collapses to spot NAV at conversion.

Prior skip list status: MEASURED already skipped in Round 35 (`docs/131_idea_round_35.md`).

Sources and quotes: MEASURED in Round 35 (`docs/131_idea_round_35.md` and `docs/QUEUE.md` skip list): 10 large Grayscale OTC trusts already converted to ETFs, leaving only 3 OTCQX trusts above $20M (`LTCN`, `BCHG`, `ETCG`) as of November 25, 2026, with 2.50% annual management fees and 50 to 200+ bps per side OTCQX spreads. Adding Osprey (`OBTC`) or Bitwise (`BITW`) and `GDLC` leaves total historical US crypto closed-end conversions well below 30 since 2016.

Published size and net status: UNKNOWN (no published post-cost replication across US crypto trust conversions).

Events per year and point-in-time free source: MEASURED ~1 to 1.5 conversions per year (< 30 total 2016 to 2026) from SEC EDGAR (`S-1`, `S-3`, `19b-4`, `8-K`).

Knowability before trade: STATED conversion applications are filed publicly on SEC EDGAR, but SEC approval dates are uncertain until final order, and OTCQX trusts frequently trade at premiums rather than discounts.

What a $500 account can do: Whole shares are affordable, but no US inverse ETF exists to hedge single-altcoin trusts (`LTCN`, `BCHG`, `ETCG`), exposing a cash account to full unhedged altcoin volatility on top of wide OTCQX spreads.

Doc 117 screen: `< 4` (event count `< 30` and unhedged altcoin noise).

Verdict: DROP. Already skipped in Round 35.

### 5. Cash merger and tender deals

Mechanism: Buy target shares trading below an announced all-cash merger or tender offer price and collect the cash consideration on deal close.

Prior skip list status: MEASURED already skipped in Round 33 (`docs/127_idea_round_33.md`, all-cash third-party tender offers and merger arbitrage) and Round 24 (pro-rated CEF cash tenders without odd-lot priority), and already tested in Replay 21 (`docs/research/97_replay_21_odd_lot_tenders.md`, odd-lot cash issuer tenders failed 4 of 6 marks; now manual watch `E03`).

Sources and quotes: STATED from [Xiya Wang (2026, NYU Shanghai honors thesis, Merger Arbitrage Returns in the U.S. Market)](https://cdn.shanghai.nyu.edu/sites/default/files/xiya_wang_thesis_nyush_honors_2026.pdf): "The analysis focuses on U.S. public company stock based M&A transactions announced and completed between January 1, 2016 and December 31, 2024. The initial Capital IQ screen yields 1,113 observations. Matching these transactions to acquiring firm information reduces the sample to 754 observations. Of these, 619 contain usable deal terms, defined by the availability of an offer price per share, an exchange ratio, or both. A total of 428 observations then provide the pricing information required to compute proposal based excess returns." Wang reports: "Mean Arbitrage Return 0.0504", "Median Arbitrage Return −0.0020", "Mean Deal Duration (days) 214.4600", and "Median Deal Duration (days) 176.0000".

Published size and net status: STATED median realized return is `-20 bps` gross over 2016 to 2024 in Wang (2026); no separate published, replicated post-2016 net-of-cost cash-only rule clears the Doc 117 screen.

Events per year and point-in-time free source: STATED ~48 usable deals per year in Wang (2026) (428 over 9 years); point-in-time free source is SEC EDGAR (`SC TO-T`, `DEFM14A`, `8-K Item 1.01`).

Knowability before trade: STATED cash offer price is known from SEC filings, but the closing date is uncertain (median 176 days) and deal-break risk is asymmetric.

What a $500 account can do: Whole shares limit a $500 cash account to 1 to 3 concurrent deals, so a single broken deal (-20% to -40%) erases 10 to 20 winning spreads, and multi-month holding periods tie up the entire account.

Doc 117 screen: `0.00` on Wang (2026) median `-20 bps`; `0.82 < 4` in Round 33.

Verdict: DROP. Already skipped in Rounds 24 and 33 and tested in Replay 21 (`E03`).

### 6. Crypto fixed-ratio token migrations, mergers, and wind-down redemptions on Coinbase and Kraken spot

Mechanism: Buy a spot token on Coinbase or Kraken ahead of a scheduled fixed-ratio conversion into another listed token (for example `VELO` to `AERO`, `MKR` to `SKY`, `AGIX` and `OCEAN` to `FET`) or a fixed-USD wind-down redemption (`GYEN` to `USDC`), capturing any pre-conversion discount to implied payout.

Prior skip list status: New check (distinct from Round 23 and 28 delistings and hard forks).

Sources and quotes: STATED from [Coinbase Help: Token delistings and migrations](https://help.coinbase.com/en/coinbase/trading-and-funding/sending-or-receiving-cryptocurrency/token-migrations), out of 33 impacted assets listed on Coinbase's official migration table, 22 require withdrawal to a self-custody wallet with trading disabled on Coinbase, 8 were 1:1 rebrands or chain migrations with no fixed USD value (`AERO`, `DAI`, `INJ`, `IP`, `LCX`, `MATIC`, `SEI`, `ZETACHAIN`), and only 3 carried a fixed-USD wind-down or non-1:1 conversion ratio auto-executed on Coinbase: for `GYEN`, "Coinbase completed the conversion of all GYEN held on Coinbase to USDC from October 26 – 29, 2026.Conversions were completed at a rate of 1 GYEN : 0.006335 USDC, with no transaction fees."; for `VELO`, "Coinbase completed the conversion of all VELO held on Coinbase to AERO from November 2 – 4, 2026. Conversions were completed at a rate of approximately 0.044 AERO per VELO, with no transaction fees."; and for `MKR`, "Coinbase completed the migration to SKY from Jan 12-14, 2026.Conversions were completed at a rate of 1 MKR : 23,520 SKY, with no transaction fees." STATED from [ChainReport Sunset and Migration Desk](https://chainreport.co/sunset-desk/), out of 16 open migrations tracked globally, only 6 carry non-1:1 ratios (`VELO` to `AERO`, `OM` to `MANTRA`, `MKR` to `SKY`, `GAL` to `G`, `AGIX` to `FET`, `OCEAN` to `FET`) and only 3 (`VELO` to `AERO`, `IP` to `DATA`, `FTM` to `S`) list Coinbase or Kraken as auto-converting.

Published size and net status: UNKNOWN (zero published academic or practitioner net-of-cost return studies).

Events per year and point-in-time free source: STATED fewer than 1 qualifying fixed-ratio or fixed-USD auto-converted event per year on Coinbase and Kraken combined (< 10 total since 2016, far below the 30-event floor); free source is official Coinbase Help and Kraken Support notices.

Knowability before trade: STATED conversion dates and ratios are published in advance by exchanges and project teams, except where trading is disabled before the exchange announces conversion terms (as with `GYEN` and `MKR` on Coinbase).

What a $500 account can do: Fractional crypto fits $500, but Coinbase Advanced Intro (50/90 bps per side) and Kraken Pro (40/80 bps per side) impose 80 to 180 bps round-trip fees before spread, and a US spot account cannot short the acquiring altcoin (`AERO`, `SKY`, `FET`), leaving any pre-conversion long fully exposed to ~5% to 10% daily altcoin volatility.

Doc 117 screen: `0.00` / UNKNOWN (count `< 10` vs 30 floor, zero published net edge, 80 to 180 bps RT fee floor).

Verdict: DROP. Too few events, zero published net edge, and unhedged altcoin risk on US spot.

### 7. Target-maturity bond ETFs (`iShares iBonds`, `Invesco BulletShares`) approaching fixed liquidation

Mechanism: Buy a defined-maturity Treasury, municipal, or corporate bond ETF ahead of its scheduled mid-December termination date if secondary market price trades below final liquidation NAV.

Prior skip list status: New check (distinct from unplanned ETF closures in Row 95 / `E07`).

Sources and quotes: STATED from [iShares iBonds Dec 2026 Term Treasury ETF (`IBTG`)](https://www.ishares.com/us/products/312457/ishares-ibonds-dec-2026-term-treasury-etf): "The last day of trading in IBTG, iShares iBonds Dec 2026 Term Treasury ETF on Nasdaq will be December 15, 2026." "Proceeds of the liquidation are currently scheduled to be sent to shareholders on December 18, 2026." "Premium/Discount 0.00 as of Nov 24, 2026". STATED from [iShares iBonds Maturity Case Study](https://www.ishares.com/us/literature/presentation/ibonds-series-case-study-en-us.pdf): "Since launching in January 2010, five treasury, five high yield, fourteen municipal, eighteen investment grade corporate, and two US TIPS iBonds ETFs have successfully liquidated." And for the 2025 corporate maturity `IBDQ`: "This culminated in a final distribution of $25.13 to shareholders on December 15th, in line with the closing price on the final day of trading."

Published size and net status: STATED ~0 bps gap to NAV in normal markets (`0.00%` on `IBTG`, final distribution in line with closing price on `IBDQ`); zero published positive excess-return study.

Events per year and point-in-time free source: STATED 44 liquidated iShares iBonds ETFs over 16 years (~2.8/yr across all five sleeves), plus a similar count for Invesco BulletShares (~5 to 8/yr combined); free point-in-time source is issuer prospectuses and SEC Form `497` filings.

Knowability before trade: STATED the termination month and last trading day are known in advance from the prospectus and issuer page, while the final cash NAV is only fixed on the last trading day (though near-cash in the final weeks).

What a $500 account can do: Whole shares at ~$23 to $25 fit easily (~20 shares) with no borrow needed, but authorized participant creation and redemption keeps market price within ~0 to 3 bps of NAV, smaller than a 4 to 10 bps retail spread.

Doc 117 screen: `0.00` (zero excess edge over T-bills after spread).

Verdict: DROP. Authorized participant arbitrage eliminates any harvestable discount before maturity.

### 8. Exchange-traded baby bonds ($25 par) and listed preferred stocks after an announced call or maturity notice

Mechanism: Buy a $25-par NYSE or Nasdaq baby bond or listed preferred stock after the issuer files an irrevocable 30-day call redemption notice at `$25.00 + accrued interest/dividend`, collecting the fixed cash payout on the redemption date.

Prior skip list status: New check.

Sources and quotes: STATED from [YieldDesk (July 20, 2026, Call provisions and call risk in preferreds)](https://yielddesk.co/learn/understanding-call-provisions-and-call-risk): "Until the redemption date the security keeps trading, at the redemption amount less a small discount for the days remaining. Selling or waiting differ by a few cents and a commission."

Published size and net status: UNKNOWN / ~0 bps excess over T-bills (no published study documents a net-of-cost excess return above T-bills after a straight preferred or baby bond call notice; academic call-notice studies cover convertible preferred and convertible bond forced-conversion calls and document negative common-stock announcement returns, not long-only par discounts).

Events per year and point-in-time free source: UNKNOWN exact 2016 to 2026 count without a dedicated census (roughly 20 to 50 full-call or maturity redemptions per year across listed US preferreds and baby bonds); free point-in-time source is SEC EDGAR Form `8-K` and press releases.

Knowability before trade: STATED the redemption date and `$25.00 + accrued` payout are fixed in the irrevocable notice of redemption (typically 30 days before redemption).

What a $500 account can do: Whole shares at ~$25 fit (~19 shares) with no borrow needed, and mandatory redemptions generally carry no voluntary reorganization fee, but a "few cents" discount over 30 days equals ~30-day T-bill carry (~35 bps gross, ~0 bps excess over T-bills) before 10 to 30 bps retail bid-ask spreads.

Doc 117 screen: `0.00` (excess net edge over T-bills ~0 bps after retail spread).

Verdict: DROP. Post-notice pricing reflects risk-free carry only, with zero published excess edge over T-bills.

### 9. Exchange-traded notes (ETNs) after an announced mandatory call or accelerated redemption

Mechanism: Buy an exchange-traded note after an issuer call or mandatory acceleration notice to capture any discount between market price and the Call Settlement Amount.

Prior skip list status: New check.

Sources and quotes: STATED from [FINRA Investor Insights (Exchange-Traded Notes)](https://www.finra.org/investors/insights/exchange-traded-notes-avoid-unpleasant-surprises): "When an ETN is trading at a premium above the indicative value, issuing more notes to the market can bring the price down. Similarly, if an ETN is trading at a discount, redemption of notes by the issuer reduces the number of notes available in the market, which tends to raise the price." FINRA adds: "For example, an ETN might trade at a premium to its indicative value if the issuer suspends issuance of new notes." On call-settlement mechanics, STATED from [Bank of Montreal Form 424B2 (filed November 20, 2026)](https://www.sec.gov/Archives/edgar/data/927971/000121465926014630/y1120261424b2.htm): "If we exercise our call right, for each note that is called, you will receive on the Call Settlement Date a cash payment equal to the arithmetic mean of the closing Indicative Note Values on each Index Business Day in the Call Measurement Period." "The Call Measurement Period will be a period of 10 consecutive Index Business Days from and including the applicable Call Calculation Date, except as provided below, and subject to adjustment as described in the product supplement under ‘Additional Terms of the Notes — Market Disruption Events.’"

Published size and net status: UNKNOWN for long-only discounts (the documented mispricing in suspended-creation ETNs is a premium that collapses on call or issuance resumption, which is short-only and unreachable on $500 cash).

Events per year and point-in-time free source: UNKNOWN exact 2016 to 2026 count (episodic clusters such as March 2020 leveraged ETN accelerations); free point-in-time source is SEC EDGAR (`424B2`, `6-K`, `8-K`) and issuer press releases.

Knowability before trade: STATED the call date is announced in advance, but the final cash payout is NOT known at notice because it averages the floating Indicative Note Value over the subsequent 1 to 10 Index Business Days.

What a $500 account can do: Whole shares fit, but a $500 cash account cannot short premium ETNs and cannot initiate direct issuer redemption (FINRA states minimums are "usually 25,000 or 50,000" notes).

Doc 117 screen: `0.00` (no fixed payout at notice; mispricing is premium/short-only).

Verdict: DROP. Fails both the fixed-value condition and the long-only cash-account constraint.
