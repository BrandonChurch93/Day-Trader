# Round 25. Edges too small for big money ($300 to $500 account)

Date: 2026-11-26. Author: Idea Scout.
Status: CURRENT. No prices or returns were pulled or computed. All filing counts are MEASURED from [SEC EDGAR full-text search (EFTS)](https://efts.sec.gov/LATEST/search-index) on 2026-11-26 with declared User-Agent headers, covering 2016-01-01 through 2026-11-26. All return, discount, and fee figures are STATED from the cited primary filings, broker fee schedules, and published studies.

## Summary and decisions

Six candidate event families were audited for a $300 to $500 US retail account. The bar requires at least 30 usable events from 2016 to 2026, non-trivial per-year dollars on $500 after broker corporate-action fees, no duplication of already tested rules, and a lawful free primary source.

| Candidate | 2016 to 2026 count (primary source) | Est. $500 account dollars per event and per year (STATED basis) | Main way it loses | Forward watch now? | Decision |
|---|---|---|---|---|---|
| 1. CEF and term-trust liquidations or open-endings with a set date | 181 DEF 14A open-ending unique issuer-years; 68 DEF 14A liquidation unique issuer-years; 325 N-8F unique issuer-years (mix of listed and unlisted; needs listed-CEF dedup) | $7.50 to $21.50 per event (1.5% to 4.3% post-announcement discount); $30 to $120 per year across 4 to 6 turns | Unhedged NAV drop during the 1 to 4 month hold; vote failure or term extension | Yes (SEC DEF 14A, N-2, 8-K) | QUEUE Row 88 (count-first listed-CEF dedup) |
| 2. SPACs under trust value near redemption or liquidation | 477 DEFM14A unique issuer-years; 1,069 raw extension DEF 14A filings | $1 to $6 per event; $40 to $46 per year total ($5 to $20 per year excess over T-bills); $50 to $100 broker fees wipe out small accounts | Missing early broker redemption cutoff and holding a de-SPAC drop; $50 to $100 reorg or DWAC fee | Yes, but skipped | DROP (skip list: trivial excess dollars on $500; institutional edge) |
| 3. Exchange offers and Dutch auctions with odd-lot priority | Dutch auctions already tested in Replay 21 (`docs/research/97_replay_21_odd_lot_tenders.md`); listed stock-for-stock split-offs are under 30 (42 raw S-4 and SC TO-I issuer-years including SPACs; 1 to 3 true split-offs per year) | $35 to $75 per event on 1 to 5 high-priced parent shares; under $150 per year | Unhedged parent drop (16% std dev); upper-limit cap removing discount; $50 broker fee | Yes, but skipped | DROP (skip list: Dutch auctions already tested; true split-offs under 30) |
| 4. Cash-in-lieu and fractional-share rounding events | Round-ups already covered in Queue Row 43 (`docs/research/75_reverse_split_round_up_feasibility.md`); ordinary cash-in-lieu has zero structural premium | $0 structural edge on ordinary cash-in-lieu (paid at market price); minus spread and any mandatory reorg fee | Post-split price drop during settlement; E*TRADE $38 mandatory split fee | No (Row 43 already logs round-ups) | DROP (skip list: duplicate of Row 43; ordinary cash-in-lieu pays market price) |
| 5. Rights offerings with small-holder oversubscription priority | 11 unique issuer-years in US EDGAR (424B5, 497, S-3, N-2) | $0.50 to $2.00 per event from 1-share minimum rounding in CEF rights offers | Pro-rata allocation by record-date shares gives small holders no priority; dilution and NAV drop | No | DROP (skip list: count 11 under 30; US allocates pro rata, not odd-lot priority) |
| 6. Going-private or going-dark cash-outs below a share threshold (SC 13E-3) | 61 unique SC 13E3 issuer-years with reverse-split fractional cash-outs (27 with exact phrase cashed out); mix of listed and OTC | $25 to $75 per event (5% to 15% post-announcement spread on $500); $75 to $375 per year across 3 to 5 deals | Street-name exclusion (registered holders only) leaving illiquid dark shares; board abandonment; OTC commission | Yes (SEC SC 13E3 and DEF 14A) | QUEUE Row 89 (count-first listed/OTC and street-name audit) |

## Retail broker corporate-action fee baseline

STATED. On a $500 account, flat per-event reorganization fees decide whether an edge can survive.

- Charles Schwab lists $0 for listed online equity trades and $0 for reorganizations, plus $6.95 for US OTC equity trades. Exact text from [Charles Schwab Pricing Guide for Individual Investors](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors): "Security reorganization: Voluntary, mandatory, and post-effective" at "$0". Exact text from [All Trading Fees and Commissions at Charles Schwab](https://www.schwab.com/node/29451): "US Over-The-Counter (OTC) Equities" at "$6.95".
- Interactive Brokers lists $0 for most corporate actions, though DWAC deliveries for SPAC redemptions have been reported by retail traders at $100 per event. Exact text from [Interactive Brokers Other Fees](https://www.interactivebrokers.com/en/pricing/other-fees.php): "All Other (Mandatory, Voluntary, With Options, etc)" at "Free". Exact text from [Interactive Brokers FAQ](https://www.interactivebrokers.com/support/faq/content/there-fee-corporate-actions-28217031): "The majority of corporate action processing is done free of charge to clients."
- Fidelity lists $0 online commissions for US stocks and OTC equities, with voluntary action fees varying by event. Exact text from [StockBrokers.com Online Trading Features and Fees Glossary](https://www.stockbrokers.com/guides/features-fees) for Fidelity: "$0.00" stock trades and "$0.000" penny stock (OTC) fees. Exact text from [Fidelity Voluntary Corporate Actions](https://www.fidelity.com/customer-service/corporate-actions-learn-more-voluntary): "Check to see what, if any, fees apply."
- E*TRADE charges $38 for mandatory reverse splits, which exceeds any small-account gain, as documented in `docs/research/75_reverse_split_round_up_feasibility.md`.
- Alpaca voluntary reorganization fees are not published in its public pricing table; Replay 21 (`docs/research/97_replay_21_odd_lot_tenders.md`) showed that a $50 election fee turns odd-lot tender returns from +11.80% to -8.60%.

## Candidate 1. Closed-end fund and term-trust liquidations or open-endings with a set date

Decision: QUEUE Row 88 (count-first listed-CEF deduplication before any price pull).

### Count per year from 2016 (MEASURED, SEC EDGAR EFTS)

Raw EFTS counts were deduplicated by unique CIK per filing year (capped at the first 100 hits per year, which covers every year below).

| Query and forms | Total unique issuer-years (2016 to 2026) | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DEF 14A: convert + open-end + closed-end + net asset value | 181 | 19 | 22 | 11 | 13 | 24 | 16 | 9 | 13 | 18 | 22 | 14 |
| DEF 14A: Plan of Liquidation + closed-end + net asset value | 68 | 5 | 14 | 6 | 7 | 7 | 6 | 6 | 3 | 5 | 4 | 5 |
| N-8F: closed-end + liquidation + net asset value | 325 | 9 | 34 | 9 | 57 | 53 | 33 | 18 | 25 | 9 | 33 | 45 |

MEASURED. Sampling 2024 hits shows the DEF 14A open-ending query captures listed CEFs (such as BNY Mellon Strategic Municipal Bond Fund DSM, Putnam Managed Municipal Income Trust PMM, and Tortoise Power and Energy Infrastructure Fund TPZ), whereas the DEF 14A liquidation query mixes listed CEFs with unlisted interval funds and BDCs (such as Blue Owl Credit Income Corp and Ecofin Tax-Exempt Private Credit Fund). The N-8F query also includes CEF mergers into other CEFs rather than cash-at-NAV liquidations.

STATED. As an external count benchmark, John Cole Scott at the Active Investment Company Alliance tracked 117 listed CEF open-ending or liquidation events over 12.5 years (about 9.4 per year). Exact quote from [AIC Alliance](https://aicalliance.org/how-corporate-actions-in-closed-end-funds-can-potentially-boost-portfolio-performance/): "Again, looking at the same 12.5-year time period, Scott tracked 117 open-ending or liquidation events and the status of fund discounts relative to event announcements".

### Published evidence (STATED)

- [Lee, Shleifer, and Thaler (1990, Journal of Economic Perspectives)](https://pubs.aeaweb.org/doi/pdfplus/10.1257/jep.4.4.153): "When closed-end funds are terminated, either through merger, liquidation, or conversion to an open-end fund, prices converge to reported net asset value (Brauer, 1984; Brickley and Schallheim, 1985)."
- [Lee, Shleifer, and Thaler (1991, Journal of Finance)](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.1991.tb03746.x): "The small discount that remains after the announcement of open-ending or liquidation can only be explained by the actual transactions costs of arbitrage (the inability to receive short-sale proceeds or the unobservability of the fund's portfolio) or the effect of some of the standard explanations mentioned earlier."
- [Bradley, Brav, Goldstein, and Jiang (2010, Journal of Financial Economics)](https://business.columbia.edu/sites/default/files-efs/pubfiles/4118/activist_arb.pdf): "Open-ending attempts have a substantial effect on discounts, reducing them, on average, to half of their original level."
- [AIC Alliance (John Cole Scott 12.5-year dataset, n=117)](https://aicalliance.org/how-corporate-actions-in-closed-end-funds-can-potentially-boost-portfolio-performance/): "90 days prior: -8.4% discount", "1 day prior: -5.6% discount", "1 day after: -2.08% discount", "7 days after: -1.52% discount".
- [UTSA Working Paper (2008)](https://interim.business.utsa.edu/wps/fin/0049FIN-092-2008.pdf): "The average discount of the closed-end funds in the sample reduces from 11.25% prior to the open-ending announcement to 6.22% following the announcement." And: "Accordingly the discount shrinks on average by 4.29% from the week following the reorganization announcement to the open-ending."
- [Nuveen Closed-End Funds Primer](https://documents.nuveen.com/Documents/Nuveen/Viewer.aspx?fileId=73224): "Investors who own shares when the fund terminates receive a cash payment equal to the NAV per share at that time."

### Dollars for a $500 account, main loss mode, and forward watch

- Realistic $500 dollars (STATED basis, not simulated): Buying after the announcement or set date leaves a remaining discount of roughly 1.5% to 4.3% in the published datasets above. On a $500 position, that is $7.50 to $21.50 per event before bid-ask spread and NAV movement. With capital tied up 60 to 120 days per event (about 4 to 6 turns per year), a $500 account could realistically earn $30 to $120 per year gross (6% to 24% on $500), with $0 mandatory corporate-action fee at Schwab, Fidelity, and IBKR. Note honestly that this edge is not restricted to small accounts; activist funds and institutions trade the same events.
- Main way it loses: Unhedged NAV risk during the 1 to 4 month holding period before liquidation or open-ending. Because the payout is final NAV (not announcement-day NAV), a 5% to 15% drop in the underlying bond or equity portfolio wipes out a 2% discount, and a $500 account cannot cheaply short the underlying basket. A second loss mode is shareholder vote failure or a board electing to extend a term trust into a perpetual fund via a partial tender offer.
- Forward watch now: Yes. SEC EDGAR DEF 14A, N-2, and 8-K filings are free and dated in real time.

## Candidate 2. SPACs under trust value near a redemption or liquidation date

Decision: DROP (skip list). Event count passes easily, but per-year excess dollars on $500 are trivial and broker voluntary redemption fees wipe out a $500 position.

### Count per year from 2016 (MEASURED, SEC EDGAR EFTS)

| Query and forms | Total (2016 to 2026) | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DEFM14A: trust account + redemption + business combination (unique issuer-years) | 477 | 19 | 16 | 21 | 26 | 46 | 86 | 71 | 54 | 59 | 36 | 43 |
| DEF 14A: trust account + Extension Amendment + redemption (raw filings) | 1,069 | 6 | 8 | 8 | 26 | 54 | 22 | 167 | 399 | 199 | 92 | 88 |

### Published evidence (STATED)

- [Gahng, Ritter, and Zhang (2023, Review of Financial Studies)](https://site.warrington.ufl.edu/ritter/files/SPACs.pdf): "On average, SPAC period investors earned 9.3% per year based on our optimal redemption strategy."
- [AQR (October 2024, Are SPACs Still Alive?)](https://www.aqr.com/-/media/AQR/Documents/Insights/White-Papers/Are-SPACs-Still-Alive.pdf): "Spread-to-trust is the difference between the yield-to-trust, the annualized return an investor would earn by buying SPAC equity today and redeeming for the trust value on the expiration date, and the yield on Treasury bills maturing on the SPAC's expiration date."
- [Pender Alternative Arbitrage Fund Commentary (July 2024)](https://penderfund.com/commentaries/alternative-arbitrage-fund-july-2024/): "At the end of July 2024, SPACs searching for targets were trading at a discount-to-trust value, which provided a yield-to-maturity of 8.27%."

### Dollars for a $500 account, main loss mode, and why dropped

- Realistic $500 dollars (STATED basis): An 8.3% to 9.3% annualized yield-to-trust on $500 is $41 to $46 per year total, of which roughly 4% to 5% is simply the Treasury-bill yield inside the trust. Excess profit over T-bills is roughly $5 to $20 per year, or $1 to $6 per event on a 15 to 60 day hold before redemption. This is an institutional hedge-fund trade (billions deployed), not an edge too small for big money.
- Main way it loses: Missing the broker's early redemption deadline (typically 2 to 5 business days before the vote) and getting stuck holding post-merger de-SPAC shares that can fall 20% to 70%; or paying a $50 voluntary reorg fee (reported at Alpaca and Webull) or $100 DWAC fee (reported at IBKR), which destroys 10x to 50x the per-event profit on $500.
- Forward watch now: Technically possible via SEC DEFM14A and DEF 14A, but dropped because per-year excess dollars on $500 are trivial.

## Candidate 3. Exchange offers and Dutch auctions with odd-lot priority beyond cash tenders already tested

Decision: DROP (skip list). Dutch-auction cash tenders were already tested in Replay 21 (`docs/research/97_replay_21_odd_lot_tenders.md`), and true listed stock-for-stock split-off exchange offers with odd-lot priority are under 30 events across 2016 to 2026.

### Overlap check and count per year from 2016 (MEASURED)

MEASURED from `docs/research/97_replay_21_odd_lot_tenders.md`: Replay 21 already tested all-cash issuer tender offers including modified Dutch auctions from January 2016 through October 2026 (106 eligible filings, 13 fixed-price and 1 Dutch-auction trade placed; failed 4 of 6 marks due to N = 14 under 30 and t = 1.688 under 2.0).

MEASURED from SEC EDGAR EFTS (2016 to 2026) for what remains outside Replay 21 (stock-for-stock split-off exchange offers with odd-lot priority):

| Query and forms | Total unique issuer-years (2016 to 2026) | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SC TO-I: exchange offer + odd-lot + fewer than 100 | 195 | 19 | 19 | 26 | 23 | 28 | 23 | 15 | 16 | 9 | 6 | 11 |
| S-4 and SC TO-I: split-off + odd-lot + exchange offer | 42 | 5 | 5 | 2 | 1 | 9 | 5 | 6 | 3 | 2 | 1 | 3 |
| S-4 and SC TO-I: exchange offer + odd-lot + fewer than 100 + split-off | 25 | 4 | 3 | 2 | 0 | 8 | 1 | 3 | 0 | 1 | 1 | 2 |

MEASURED. Sampling the 195 SC TO-I hits shows most are non-traded REITs (such as Highlands REIT and Lightstone Value Plus REIT II) or cash/debt offers already covered by Replay 21. Even the 42 S-4 and SC TO-I hits include SPACs (such as Anzu Special Acquisition Corp I) citing split-off language. Pure listed corporate stock-for-stock split-offs with odd-lot priority (such as Johnson & Johnson / Kenvue) occur roughly 1 to 3 times per year, well below 30 over 2016 to 2026.

### Published evidence (STATED)

- [Triple Summit Advisors (32 split-offs across 1995 to 2020, about 1.2 per year)](https://www.triplesummitadvisors.com/legal-tender-part-3-splitting-the-market/): "Generally speaking, you earn 4.7% more (15.5% versus 10.8%) on average if you participate in the exchange offer on Announcement Date unhedged, but at the expense of higher volatility (16% standard deviation versus 4.6% hedged)."
- [Special Situation Investments (16 split-offs since 2013, about 2.3 per year)](https://www.specialsituationinvestments.com/2020/06/analysis-of-different-split-off-trading-strategies/): "All in all, the most profitable strategy seems to be opening an unhedged position right after the initial announcement is made (14.9% returns on average)."

### Dollars for a $500 account, main loss mode, and why dropped

- Realistic $500 dollars (STATED basis): Large-cap split-off parents typically trade at $100 to $300 per share, so a $500 account buys only 1 to 5 shares (not 99 shares). A 7% to 15% split-off gain on $500 is $35 to $75 per event, or roughly $35 to $150 per year across 1 to 2 events.
- Main way it loses: Unhedged parent-stock drawdown during the 20-day offer window (16% standard deviation in Triple Summit's unhedged sample, since a $500 account cannot short the subsidiary to hedge), hitting the upper-limit exchange cap (which shrinks or eliminates the 7% discount), or a $50 voluntary exchange fee.
- Forward watch now: Possible via SEC S-4 and SC TO-I, but dropped because Dutch auctions were already tested in Replay 21 and true listed split-offs are under 30 events in 2016 to 2026.

## Candidate 4. Cash-in-lieu and fractional-share rounding events

Decision: DROP (skip list). Fractional-share reverse-split round-ups are already covered in Queue Row 43 (`docs/research/75_reverse_split_round_up_feasibility.md`), and ordinary cash-in-lieu has zero structural edge.

### Overlap and mechanism check (STATED)

- Reverse-split fractional round-ups were audited in `docs/research/75_reverse_split_round_up_feasibility.md` (Queue Row 43, Plan 30), where the lead ruled no frozen historical replay and a no-money forward log because broker pass-through policy (not historical price files) determines the payout.
- Ordinary cash-in-lieu (CIL) of fractional shares in standard reverse splits or stock mergers pays pro-rata market value, not a fixed premium or free whole share. Exact quote from [ZKID Network PRE 14C](https://www.sec.gov/Archives/edgar/data/1109153/000126967806000052/zkid030306pre14c.txt): "Instead, affected stockholders will receive a cash payment in an amount equal to such fractional share multiplied by the closing price of the Common Stock on the date the reverse stock split is effected." Exact quote from [Charles Schwab Brokerage Account Agreement via doc 75](https://www.schwab.com/legal/schwab-brokerage-account-agreement): Schwab "may either sell the shares on the open market or to the issuer or transfer agent" and pay the pro rata proceeds.
- The only cash-in-lieu events with an explicit above-market cash payout are going-private / going-dark reverse-split cash-outs, which are evaluated separately as Candidate 6 (Queue Row 89).

### Dollars for a $500 account, main loss mode, and why dropped

- Realistic $500 dollars: $0 structural edge on ordinary cash-in-lieu, minus bid-ask spread and any mandatory reorganization fee.
- Main way it loses: Post-split share price drop while fractional shares are aggregated and sold, plus mandatory split fees (such as E*TRADE's $38 fee).
- Forward watch now: No new watch needed; reverse-split round-ups are already tracked under Row 43.

## Candidate 5. Rights offerings where small holders get oversubscription priority

Decision: DROP (skip list). Count is 11 (under 30) in US EDGAR from 2016 to 2026, because US rights offerings allocate oversubscriptions pro rata by record-date holdings rather than giving small holders priority.

### Count per year from 2016 (MEASURED, SEC EDGAR EFTS)

| Query and forms | Total unique issuer-years (2016 to 2026) | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 424B5, 497, S-3, N-2: oversubscription privilege + odd-lot | 11 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 4 | 3 |
| N-2, 497: oversubscription privilege + closed-end (raw filings) | 83 | 1 | 3 | 12 | 6 | 5 | 9 | 1 | 4 | 14 | 17 | 11 |

### Published and primary-filing evidence (STATED)

- US CEF and corporate rights offerings allocate oversubscriptions pro rata by record-date holdings, not with odd-lot priority. Exact quote from [Western Asset High Income Fund II (HIX) Form 424B2 (2024)](https://www.sec.gov/Archives/edgar/data/1058239/000119312524018225/d715057d424b2.htm): "If the requests for primary over-subscription shares exceed the primary over-subscription shares available, the available primary oversubscription shares will be allocated pro rata among those fully exercising Record Date Stockholders who oversubscribe based on the number of Rights originally issued to them by the Fund."
- Exact quote from [Saba Capital Income and Opportunities Fund (BRW) Form 424B5 (2025)](https://www.sec.gov/Archives/edgar/data/826020/000199937125014759/brw_424b5-092325.htm): "If the requests for over-subscription shares exceed the over-subscription shares available, the available over-subscription shares will be allocated pro rata among those fully exercising Record Date Shareholders who over-subscribe based on the number of Rights originally issued to them by the Fund."
- Odd-lot priority in excess rights allotment is a Singapore Exchange (SGX) rule, not a US market rule. Exact quote from [SAC Capital Regulatory Update on SGX RegCo](https://www.saccapital.com.sg/wp-content/uploads/1970/01/SAC-Regulatory-Update-Jan-2024-What-SGX-RegCo-expects-of-listed-issuers-when-allotting-excess-rights-shares.pdf): "Rule 877(10) of the Mainboard Rules and Rule 814(3) of the Catalist Rules (Rules) require issuers to confirm that, in the allotment of excess rights shares, preference will be given to the rounding of odd lots".
- The only small-holder perk in US CEF rights offerings is 1-share minimum rounding for holders of fewer than the subscription ratio (for example, 1 or 2 shares on a 3-for-1 offer). Exact quote from [NXG NextGen Infrastructure Income Fund Exhibit 99.252zii (2024)](https://www.sec.gov/Archives/edgar/data/0001506488/000139834424005309/fp0087410-1_ex99252zii.htm): "Any Record Date Shareholder who is issued fewer than [N] Rights may subscribe for one full common share in the Offer."

### Dollars for a $500 account, main loss mode, and why dropped

- Realistic $500 dollars (STATED basis): 1-share minimum rounding at a 5% to 10% subscription discount on a $10 to $20 CEF share yields roughly $0.50 to $2.00 per event (under $15 per year).
- Main way it loses: Dilutive rights offerings typically push the CEF's share price down during the subscription period, and subscriptions are irrevocable before the formula price is finalized.
- Forward watch now: No. Dropped for count under 30 (11 US EDGAR issuer-years) and trivial per-event dollars.

## Candidate 6. Going-private or going-dark cash-outs of holders below a share threshold

Decision: QUEUE Row 89 (count-first audit of the 61 SC 13E-3 filings from 2016 to 2026 to separate exchange-listed vs OTC tickers and beneficial street-name eligibility vs registered-only before any replay).

### Count per year from 2016 (MEASURED, SEC EDGAR EFTS)

| Query and forms | Total unique issuer-years (2016 to 2026) | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SC 13E3: reverse stock split + fractional | 61 | 14 | 7 | 5 | 5 | 8 | 4 | 2 | 2 | 3 | 9 | 2 |
| SC 13E3: reverse stock split + fractional shares + cashed out | 27 | 6 | 1 | 2 | 2 | 2 | 3 | 1 | 1 | 3 | 5 | 1 |
| DEF 14A: reverse stock split + going private + cashed out | 173 | 18 | 12 | 5 | 14 | 24 | 3 | 14 | 19 | 22 | 24 | 18 |

MEASURED. Sampling 2023 to 2025 SC 13E3 hits shows small-cap and micro-cap issuers (such as Psychemedics Corp PMD, Safeguard Scientifics SFES, Superior Energy Services, and Mymetics Corp). Many trade on OTC markets rather than NYSE or Nasdaq, so a count-first roster must verify how many of the 61 unique SC 13E3 issuers were exchange-listed or broker-tradable and explicitly included beneficial street-name holders.

### Published and primary-filing evidence (STATED)

- [Leuz, Triantis, and Wang (2008, ECGI Finance Working Paper 155/2007)](https://www.ecgi.global/sites/default/files/2026-10/fin-155-2007_why_do_firms_go_dark_causes_and_economic_consequences_of_vol_0.pdf): "For instance, outside shareholders' interests are better protected if a company has more than 300 holders of record prior to going dark because the transaction that needs to be executed to bring down the number of record holders below the maximum threshold involves shareholder input: a reverse split (plus a subsequent squeeze out of fractional shareholders) requires majority shareholder approval".
- [Marosi and Massoud (2007, Journal of Financial and Quantitative Analysis 42: 421 to 442)](https://ideas.repec.org/a/cup/jfinqa/v42y2007i02p421-442_00.html): "We find that firms with fewer valuable growth opportunities, greater insider ownership, lower institutional ownership, higher leverage, and lower market momentum are more likely to go dark."
- [SEC DEF 14A (CIK 1552800, 2025)](https://www.sec.gov/Archives/edgar/data/1552800/000114036125040554/ny20055980x3_def14a.htm): "Holders of fewer than the Minimum Number immediately prior to the effective time of the Reverse Stock Split will receive a cash payment of $6.60, without interest, for each share of common stock they hold, will no longer have any ownership interest in us, and will cease to participate in any of our future earnings and growth."
- [SEC Fairness Opinion Exhibit (CIK 63814)](https://www.sec.gov/Archives/edgar/data/63814/000095012309047190/filename1.htm): "The mean premium in the three controlled group precedent transactions was 16.7%, and the mean premium in the three non-controlled group precedent transactions was 32.4%."
- [First Ipswich Bancorp SC 13E3/A Exhibit 16(c)(1)](https://www.sec.gov/Archives/edgar/data/885979/000117152007000778/presentation.pdf): "By effecting the transaction only at the registered shareholder level, shareholders holding their shares in street name are not impacted by the transaction."

### Dollars for a $500 account, main loss mode, and forward watch

- Why big money cannot take it: The cash-out applies only to accounts holding fewer than the reverse-split threshold (commonly 100 to 1,000 shares, typically $200 to $3,000 maximum per beneficial account). Larger accounts cross the threshold and are left holding illiquid deregistered shares. A $300 to $500 account is the natural taker.
- Realistic $500 dollars (STATED basis): Post-announcement discounts to the fixed cash-out price commonly run 5% to 15% (reflecting deal-break risk, illiquidity, and street-name ambiguity). On a $500 position capped below the split threshold, that is $25 to $75 per event. Across 3 to 5 qualifying deals per year, a $500 account could realistically earn $75 to $375 per year gross (15% to 75% on $500).
- Main way it loses: First, street-name exclusion, where the issuer effects the split only at the registered-holder level (or a broker aggregates street-name accounts), leaving the buyer holding illiquid dark shares instead of receiving cash. Second, board abandonment or shareholder vote failure (especially if arbitrageurs flood below the threshold and raise the issuer's cash-out cost), causing the stock to drop 20% to 50% back to pre-announcement levels. Third, OTC commissions ($6.95 per trade at Schwab, though $0 at Fidelity).
- Forward watch now: Yes. SEC EDGAR SC 13E3 and DEF 14A filings are free and real-time; a no-money forward log can record the cash-out price, threshold, announcement-day price, and whether street-name beneficial holders are included.
