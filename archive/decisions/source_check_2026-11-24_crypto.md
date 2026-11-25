# Fact check: docs/playbook/02_crypto_what_works.md

Checker: check_c. Date: 2026-11-24. Repo was read only.

Scope note: the "Bottom line" section has no numbers and no [MEASURED] tag, so it contains no checkable claim under the brief. Its qualitative sentence ("Neither has verified durable small-account profitability") was not checked. The "Do not do" and "Must measure ourselves" sections were out of scope and are unchecked (this includes the [MEASURED] Hyperliquid terms line and the September 27, 2026 Sonar date).

Price pages for Binance.US, Kraken Pro and Robinhood were fetched fresh (cache off) on 2026-11-24 and matched the cached reads.

## Rules for the build

1. Claim: "Treat crypto-for-crypto investment swaps as generally taxable recognition events. (Research: U.S. tax and records.) [MEASURED]"
   Source: https://www.irs.gov/individuals/international-taxpayers/frequently-asked-questions-on-digital-asset-transactions ; https://www.irs.gov/pub/irs-drop/n-14-21.pdf (links from research 02, line 61)
   Verdict: VERIFIED
   Source quote: FAQ Q64: "Yes. If you exchange digital assets for other property, including for other digital assets differing materially in kind or extent ... you will recognize a capital gain or loss." Notice 2014-21 A-1: "For federal tax purposes, virtual currency is treated as property."
   Tag check: MEASURED is right (official IRS guidance).
   Omitted context: the IRS wording limits this to assets "differing materially in kind or extent", which is what "generally" covers. Nothing material is missing.

2. Claim: "Require at least 60 trading days and 100 closed paper trades with models off, then shadow before tiny live capital. Require 6-12 months of live evidence to scale beyond tiny capital. (Our recommendation; D3.) [STATED]"
   Source: archive/decisions/0001-starting-decisions.md, row 9 (D3 maps to row 9 per that file)
   Verdict: VERIFIED (matches the internal decision)
   Source quote: "Paper gate before tiny live capital: 60 trading days and 100 closed paper trades with models off, then shadow. Scaling needs 6 to 12 months of live evidence"
   Tag check: STATED is right. This is a project heuristic, not external evidence.
   Omitted context: decision 0001 has the status "proposed by the research team" and is not owner-confirmed. Research 06 (lines 213 to 215) gives a different Phase 2 duration, "4-8 weeks and >= 100 closed trades". The decision says it "Reconciles the three reports' differing durations", so the 60-day figure belongs to the project and does not come from a source.

## Key numbers

3. Claim: "Historical BTC intraday timing | ~10 bps unlevered break-even cost | Data through Dec 2020 | MEASURED"
   Source: https://centaur.reading.ac.uk/100181/3/21Sep2021Bitcoin%20Intraday%20Time-Series%20Momentum.R2.pdf
   Verdict: VERIFIED
   Source quote: "the entire-sample breakeven costs of η(rONFH), η(rSLH) and η(rONFH, rSLH) are 3, 7 and 10 bps respectively, indicating that all of these three strategies are not profitable given that the trading fee of Bitstamp is 25bps." Data runs "from the earliest date to 31st December 2020". Table 8 note: "Break-even is the trading costs that reduce performance reported in Table 5 to zero."
   Tag check: MEASURED is acceptable. This is the accepted manuscript of a peer-reviewed article (Shen, Urquhart and Wang, Financial Review 57(2), 2022, per the CentAUR record). It is still a single historical study.
   Omitted context: (a) 10 bps is the best of three variants (the others are 3 and 7 bps). (b) The paper does not say whether the break-even is one-way or round trip, and does not say spread is included. Comparing it with the "round trip, fee only" rows below (for example, Binance.US at 4 bps) is therefore not like for like, and a reader could wrongly conclude the strategy clears Binance.US costs. (c) The authors' own conclusion is that the strategies are unprofitable at a 25 bps fee. They also report break-evens of 29 to 96 bps at 10:1 leverage and call margin versions "still profitable", which the playbook leaves out, correctly given its no-leverage rule. (d) The sample covers 2013 to 2020 only.

4. Claim: "Binance.US, most spot pairs | 4 bps taker round trip, fee only | Nov 24, 2026 | MEASURED"
   Source: https://www.binance.us/fees
   Verdict: VERIFIED
   Source quote: "0% maker and 0.02% taker on all other pairs. The 0.02% taker rate lowers to 0.01% once your 30-day trading volume hits $500 million or more." Two times 0.02% is 4 bps.
   Tag check: MEASURED is right (published price page).
   Omitted context: a 5% discount applies when fees are paid in BNB (0.0190%). The page says "all other pairs", which is broader than the playbook's "most". A zero or low fee says nothing about book depth, which the playbook flags elsewhere.

5. Claim: "Alpaca spot entry | 50 bps taker round trip, fee only | Nov 24, 2026 | MEASURED"
   Source: https://docs.alpaca.markets/us/docs/crypto-fees
   Verdict: VERIFIED
   Source quote: Tier 1, "0 - 100,000 | 0.15% | 0.25%" (maker, taker). Two times 0.25% is 50 bps.
   Tag check: MEASURED is right.
   Omitted context: none material.

6. Claim: "Kraken Pro spot entry | 160 bps taker round trip, fee only | Nov 24, 2026 | MEASURED"
   Source: https://www.kraken.com/pro/fees
   Verdict: VERIFIED
   Source quote: "Tier 1 | $0+ | 0.40% | 0.80%". Two times 0.80% is 160 bps.
   Tag check: MEASURED is right.
   Omitted context: the tier drops to 0.60% taker at $2.5K of 30-day volume and 0.38% at $10K. Tiers can also qualify through futures volume or platform assets. The page mentions a "−0.02% off" discount on eligible spot pairs. Stablecoin and FX pairs use a separate 0.20%/0.20% schedule.

7. Claim: "Coinbase Advanced spot | Signed-in tier and preview authoritative; public entry rate unverified | Nov 24, 2026 | UNKNOWN"
   Source: https://help.coinbase.com/en/coinbase/trading-and-funding/advanced-trade/advanced-trade-fees
   Verdict: VERIFIED
   Source quote: "To see your current rates and qualification criteria, sign in to your Coinbase.com account and open the Coinbase Advanced fees page." "Advanced fees are subject to change but will always be displayed on the order preview page."
   Tag check: UNKNOWN is right. The page publishes no entry rate.
   Omitted context: none.

8. Claim: "Robinhood Exchange Routing spot entry | 190 bps taker round trip, fee only | Nov 24, 2026 | MEASURED"
   Source: https://cdn.robinhood.com/assets/robinhood/legal/rhc-fee-schedule.pdf
   Verdict: VERIFIED
   Source quote: "$0-$10K | 0.95% | 0.50%" (standard/taker, reduced/maker). Two times 0.95% is 190 bps.
   Tag check: MEASURED is right.
   Omitted context: the PDF has no effective date (identifier 20261102-6078699-19354665), so "Nov 24, 2026" is the date it was checked, not the date the fees took effect. Default routing goes to market makers with "No commissions", and its cost sits in the spread. Exchange Routing applies to all limit orders regardless of the routing setting.

9. Claim: "Gemini ActiveTrader spot entry | 240 bps taker round trip, fee only | Sep 1, 2026 | MEASURED"
   Source: https://www.gemini.com/fees/activetrader-fee-schedule
   Verdict: VERIFIED
   Source quote: "Effective date: September 1, 2026." Lowest spot tier: "Maker: 0.600%; taker: 1.200%", volume ≥ $0, balance ≥ $0. Two times 1.20% is 240 bps.
   Tag check: MEASURED is right.
   Omitted context: tier volume excludes stablecoin-pair volume. An asset balance can qualify a lower tier.

10. Claim: "IBKR spot commission | 0.12%-0.18% per order; $1.75 minimum capped at 1% | Nov 24, 2026 | MEASURED"
    Source: https://portal.interactivebrokers.com/en/pricing/commissions-cryptocurrencies.php
    Verdict: VERIFIED
    Source quote: "≤ 100,000 | 0.18% of trade value"; "> 1,000,000 | 0.12% of trade value"; "Minimum per order: USD 1.75", "subject to a cap of 1% of trade value".
    Tag check: MEASURED is right.
    Omitted context: the rate is set by monthly trade value, so a small account pays 0.18%. "0.12%-0.18% per order" reads as if the rate varies per order. Paxos or Zero Hash charges 18 bps on every trade, and IBKR rebates the difference for higher tiers. There is also a USD 0.15 per month Paxos account fee. On small orders the 1% cap is what sets the cost (for example, 200 bps round trip on $100, per research 02).

11. Claim: "Kraken U.S. BTC perp sizing | 0.0001 BTC minimum | Nov 23, 2026 | MEASURED"
    Source: https://blog.kraken.com/product/kraken-derivatives/us-fractional-crypto-perps
    Verdict: VERIFIED
    Source quote: dated November 23, 2026. The post covers fractional sizing on "17 US crypto perps", down to 0.0001 BTC, for "eligible US clients in all states except Maine and New York."
    Tag check: borderline. The source is a vendor product announcement on a blog, not a contract specification page. It is acceptable as a vendor-published product fact, but the contract specifications page would be the stronger MEASURED source.
    Omitted context: Maine and New York are excluded. Per-contract margin, fees and funding apply.

12. Claim: "Custodial broker 1099-DA, 2025 | Gross proceeds from reportable sales; basis optional | Tax year 2025 | MEASURED"
    Source: https://www.irs.gov/pub/irs-prior/i1099da--2025.pdf
    Verdict: VERIFIED
    Source quote: "For each digital asset sale that a broker has effected for a customer in 2025, the broker must complete Form 1099-DA." Brokers "are not required to report basis information" for 2025 sales and "may voluntarily report this basis information".
    Tag check: MEASURED is right (official instructions).
    Omitted context: reported proceeds are net of digital asset transaction costs. Optional aggregate reporting applies to qualifying stablecoins and specified NFTs. The instructions state the 2025 duty for brokers that effect sales generally and do not phrase it as custodial-only, so the "Custodial broker" label is narrower than the text. That is not wrong in practice after Public Law 119-5.

13. Claim: "Custodial broker 1099-DA, 2026 onward | Gross proceeds on reportable sales; mandatory basis only for covered assets acquired after 2025 and held in the same custodial account until sale | Apr 30, 2026 | MEASURED"
    Source: https://www.irs.gov/instructions/i1099da
    Verdict: VERIFIED
    Source quote: "Page Last Reviewed or Updated: 30-Apr-2026." "For sales a broker has effected for customers after 2025 of digital assets that are covered securities, the broker is required to report basis information." "A digital asset is a covered security only if it was acquired in an account for which the broker provided custodial services and was held in that account until the broker effects the disposition".
    Tag check: MEASURED is right.
    Omitted context: basis is also not required for covered qualifying stablecoins or specified NFTs reported under the optional methods. De minimis rules apply ($600 for PDAP sales, $10,000 for qualifying stablecoin designated sales). None of this changes a BTC/ETH spot reader's decision.

## Counts

VERIFIED: 13. OVERSTATED: 0. WRONG: 0. NOT IN SOURCE: 0. UNREACHABLE: 0.
Tag concerns: 1 borderline (row 11, vendor blog post used as the MEASURED source). Unchecked: the Bottom line qualitative sentence, and the Do not do and Must measure sections (out of scope).

## Most serious problem

Row 3 sits beside a set of "round trip, fee only" rows. The University of Reading paper does not say whether its 10 bps break-even is one-way or round trip, or whether spread is included, and its authors conclude the strategy is unprofitable at a 25 bps fee. A reader could set 10 bps against Binance.US's 4 bps and wrongly infer that the edge survives. This is context only: every figure matches its source.
