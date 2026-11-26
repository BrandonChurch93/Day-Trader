# Idea Round 52: Swing Events and Post-Publication Power Screen

Written: 2026-11-26 20:34 UTC.
Scope: untested and undropped swing ideas (holds of 1 day to a couple of months, "quick" meaning within a few weeks) tradable in a $500 US retail account (stocks long-only under $2,000; coins on a US spot venue at about 75 bp a side, or 150 bp round trip), using free or already-held point-in-time data, with a rule precise enough to code without choices of ours, a stated after-cost edge of at least about 2% per trade for stocks (more for coins), and enough events to clear the Doc 117 pre-data power screen (`N_eff * (net_edge / paired_noise)^2 >= 4` for 50% power, `>= 8` for 80% power).
No price data was opened and no return calculation was run in this round.

## Leads already closed, blocked, or dropped in the repo

Every lead requested for Round 52 was checked first against `docs/STATUS.md`, `docs/QUEUE.md` (all sections including skip lists and "Looked at and dropped before testing"), `research_rig/TRIAL_LEDGER.md`, and docs 117, 169, 171, 173, and 174:
- 13D activist filings in operating companies (5 to 20 day drift): already dropped in Round 38 (`docs/QUEUE.md` skip list), `docs/QUEUE.md` ("Looked at and dropped": copying large-stake filings after the filing day), and Round 51 (`docs/research/174_idea_round_51_larger_swing_edges.md`, citing Dead Signals Lab at +0.31% net at 10 days, +0.10% at 20 days, and -0.13% at 40 days across 61,670 filings 2006 to 2024). Not repeated.
- S&P SmallCap 600 additions and Russell 2000 reconstitution run-ups: already blocked on data licensing in `docs/QUEUE.md` (`Queue 42`: no lawful free point-in-time Russell 2000 addition lists, provider lists are client-only and public PDFs require a license to store; `Queue 76`, `Queue 87`, and Round 27: S&P Dow Jones Indices Legal Disclaimers prohibit storing or reproducing archives and announcement archives return HTTP 403). Not repeated.
- Coin exchange-listing longs on US venues: already closed or dropped in `docs/QUEUE.md` (`Queue 80`, Plan 44: Coinbase listing-roadmap additions closed at feasibility with 60 additions across 40 posts and 29 prior-day spot ticker candidates; `Queue 73`: Binance spot listing announcements of US-listed coins kept on WATCH only with broad Binance listings at -0.1% 24h and -6.1% 7d; "Looked at and dropped": buying new listings and chasing coins on listing day). Not repeated.
- Open-market share buyback announcements: already dropped in `docs/QUEUE.md` ("Looked at and dropped", `docs/research/51_stock_swing_evidence_checked.md`) and Round 51 (`docs/research/174_idea_round_51_larger_swing_edges.md`, citing CBS 2025 on 14,847 US announcements 2006 to 2021 where +3 to +10 day returns attenuate to market-level and 12-month monthly alpha is 0.262%). Only non-odd-lot Dutch-auction self-tenders are evaluated below.
- 52-week-low reversal with insider buying: skipped as instructed (covered by Round 51, `docs/research/174_idea_round_51_larger_swing_edges.md`).
- Also already closed or covered in `docs/QUEUE.md` among extra families checked: marketed seasoned equity offerings (`Queue 59`, Plan 42) and US forward stock split announcements (`Queue 97`).

## Ranked evaluation of new leads and one added family

Five candidates were evaluated in full against the Round 52 criteria and Doc 117's power screen. Only Rank 1 potentially clears Doc 117 on paper, and even Rank 1 faces a direct post-2018 refutation. Ranks 2 through 5 fail the 2% net bar, the Doc 117 power screen, or both.

### Rank 1: Earnings gap-up with high volume (Episodic Pivot or Power Earnings Gap, 20 to 60 session hold)

Why this is distinct from Plan 74 Card A: Plan 74 Card A (`Ledger 226`, `Queue 126`) tests a leading stock near its 52-week high with a market switch, a tight stop, and an add to winners. The standalone Episodic Pivot rule requires the opposite pre-event setup: a neglected stock that has gained less than 30% over the prior 126 sessions, gaps up 8% to 10% or more on quarterly earnings with at least 3x average daily volume, and is held for 20 to 60 sessions (or with a day-low stop and trailing moving-average exit).

Exact rule as stated:
- STATED, strict Episodic Pivot version ([TickerGuard](https://tickerguard.com/stocks/scanner/qullamaggie-ep-original)): "The open sits at least 10% above the prior day's close." "Daily volume runs at least three times the 20-day average volume." "The price gain over the last 126 trading days (roughly half a year) stayed under 30%." "The last 63 trading days had no earlier gap of 10% or more." "Entry is the open of the gap day." "The stop is that day's low; if it sits more than 1.5 times the ADR away, we throw the signal out." Note: full-day volume is not known at the open, so a causal version must either enter at the gap-day close or use an intraday opening-range volume threshold as in What Works in Trading below.
- STATED, broad Power Earnings Gap version ([StreetAlpha](https://streetalpha.app/backtests/earnings-gap-up)): "Power earnings gap: on the first session after the report, the stock opens 8% or more above the prior close, closes at or above the open, on at least 3 times its 50 day average volume."
- STATED, intraday checklist version ([What Works in Trading](https://whatworksintrading.substack.com/p/i-coded-the-six-rules-of-the-episodic)): "Enter on the gap day. Buy when price breaks above the high of the first minutes of trading, the opening range. Place the stop at the day's low, and skip the trade if that stop is more than one average daily range away." "Sell a third to a half after three to five days and hold the rest until the price closes below its 10- or 20-day average. Skip biotech."

Stated numbers, sample, years, costs, and post-publication behavior:
- STATED ([TickerGuard](https://tickerguard.com/stocks/scanner/qullamaggie-ep-original)): "We backtested these exact rules from 1976 through 2026 on a survivorship-bias-free price database: 2,843 trades, a 48.2% win rate, +3.89% average return per trade, and a −0.31% median." "Gaps on quarterly earnings were the better ones: +4.8% per trade at a 55% hit rate versus +3.7% at 43% without earnings." Transaction costs and a post-2015 split are UNKNOWN (not stated on the page).
- STATED ([Whitman Trading](https://whitmantrading.com/terms/episodic-pivot/)): on "52 US stocks, from January 2000 or their listing to 25 September 2026" using "the official open is at least 10% above the prior official close, and the session's full volume is at least 3 times the average of the prior 50 sessions", "The rule found 239 episodic pivots in 40 of the stocks, on 230 different dates." "141 of the 239, 59.0%, beat SPY over the next 20 sessions, against 51.5% for all stock-days (p = 0.023). Over 60 sessions it was 147 of 239, 61.5%, against 52.6% (p = 0.006)." "The median lead over SPY after 60 sessions was 3.07 percentage points, against 0.74 for an ordinary day." "From 2013 to 2026, 88 of 148 did, 59.5% (p = 0.10 on its own)." Mean return and costs are UNKNOWN.
- STATED post-2018 refutation ([StreetAlpha](https://streetalpha.app/backtests/earnings-gap-up)): "We tested three versions on US stocks from mid 2018 to May 2025." "Power gaps outside the S&P 500: 815 trades, 0.26% behind over 20 days and 0.08% behind over 60 days." "Judged against: the average eligible stock over the same days, after a 0.1% round trip cost, and against random stocks bought on the same day." However, "In the most recent 18 months, which we held back and checked separately, the same rules gave 306 trades and +1.85% against the average stock, with 52.6% of trades making money."
- STATED minute-bar test ([What Works in Trading](https://whatworksintrading.substack.com/p/i-coded-the-six-rules-of-the-episodic)): "The data covers liquid, fast-moving US stocks from 2015 to June 2026, including many companies that later disappeared, so the test is not flattered by looking only at survivors." "Every earnings gap that met the basic entry rule became a trade: 291 in total." "In the base version, with only rules 5 and 6, the best 5% of trades, about 15 of them, made 126.82R." Overall net percent return is UNKNOWN from the free excerpt.

Data needed, event-count estimate, and Doc 117 power statement:
- Data: free SEC EDGAR Form 8-K Item 2.02 and 10-Q filing dates plus Alpaca SIP daily and minute bars from 2016 (shared with Plan 74; dead-name coverage is MEASURED in probe P1b, still running). Tradable long-only in a $500 US account.
- Event count: STATED 815 broad Power Earnings Gaps over 7 years outside the S&P 500 (about 116 per year) in StreetAlpha, versus 291 strict intraday earnings-gap trades over 11.5 years (about 25 per year) in What Works in Trading.
- Doc 117 power statement: for the broad rule over 2016 to 2025 (about 1,000 raw trades, roughly 400 effective independent turns after quarterly earnings-season clustering), at a hypothetical +2.0% net edge and 15% paired 20-day noise, `400 * (0.02 / 0.15)^2 = 7.1`, which clears 4 for 50% power and approaches 8 for 80% power. For the strict 6-rule rule (about 250 trades, roughly 150 effective turns), at +3.5% net and 20% noise, `150 * (0.035 / 0.20)^2 = 4.6` (barely clears 4). If the true post-2018 edge is StreetAlpha's -0.26%, power is 0.

Honest reasons it may be nothing:
- StreetAlpha's mid-2018 to May 2025 after-cost test of the exact broad Power Earnings Gap rule lost to the average stock (-0.26% over 20 days).
- TickerGuard's +4.8% earnings-gap average has a negative overall median (-0.31%), omits transaction costs, does not isolate post-2015 years, and uses full-day volume with open-price entry (a look-ahead gap unless replaced by close entry or early-minute volume).
- Extreme right-skew (top 5% of trades carrying 126.82R) means a $500 account holding 1 or 2 positions faces long losing stretches and high variance.

### Rank 2 (Added family): Post-earnings small-cap crash overreaction rebound (long-only after a 10% or larger earnings-day drop, 20-session hold)

Why this is new: neither `TRIAL_LEDGER.md` nor `docs/QUEUE.md` tests buying small-cap US stocks after a large earnings-day crash for a 20-session rebound. (`Queue 17` and Plan 68 tested positive-surprise drift; Round 46 dropped non-earnings 3-day NYSE -10% reversals on power.)

Exact rule as stated (inverted to long-only from the source's short test):
- STATED ([TickerGuard](https://tickerguard.com/articles/post-earnings-drift-backtest-study)): "The core rule: if a U.S. stock with a market capitalization under $2 billion drops at least 10% on its earnings day (or the day after), it is shorted at the next market open and covered 20 trading days later at the close — no stop, because a drift is a slow move and a stop would cut off exactly that slowness." Reversed to a $500 long-only rule: buy at the next regular open after a small-cap (< $2 billion) drops at least 10% on its earnings day (or day after), and sell 20 trading days later at the close.

Stated numbers, sample, years, costs, and post-publication behavior:
- STATED ([TickerGuard](https://tickerguard.com/articles/post-earnings-drift-backtest-study)): "This preregistered backtest ran exactly that rule on 8,861 short trades across 2,615 different small-cap U.S. stocks, from 2011 through 2026."
- STATED ([TickerGuard](https://tickerguard.com/articles/post-earnings-drift-backtest-study)): "8,861 short trades across 2,615 small-cap U.S. stocks (2011-2026, excluding 2020) averaged −1.48% per trade after all costs." By sub-period (table rows): `2016 to 2019` had 2,357 trades at `-2.05%`, and `2024 to 2026` had 2,099 trades at `-2.24%`.
- STATED ([TickerGuard](https://tickerguard.com/articles/post-earnings-drift-backtest-study)): "The real problem isn't the cost load; it's the price path itself." "On average, these stocks rebound too often and too strongly for a short to outrun them." "And with every cost stripped out entirely — no spread, no commission, no borrow fee — the winsorized mean still sits at −0.48%."

Data needed, event-count estimate, and Doc 117 power statement:
- Data: free SEC EDGAR earnings filing dates plus Alpaca SIP daily bars from 2016 (shared with Plan 74). Tradable long-only in a $500 US account.
- Event count: STATED 2,357 trades in 2016 to 2019 (about 589 per year) and 2,099 trades in 2024 to early 2026 (about 900+ per year).
- Doc 117 power statement: while the short lost -1.48% after borrow and spread costs, stripping out all costs leaves a winsorized short return of -0.48%, which implies a raw long-side winsorized rebound of only +0.48% before long-side spreads (about +0.18% to +0.28% net after 20 to 30 bp small-cap round-trip spread, and UNKNOWN against IWM over the same 20 sessions). Even with 6,000 events over 10 years (roughly 2,000 effective independent turns after earnings-season clustering) and 15% paired noise, `2,000 * (0.0028 / 0.15)^2 = 0.70`, far below 4. Fails both the 2% bar and Doc 117.

Honest reasons it may be nothing:
- Most of the headline -1.48% short loss was short-side borrow and trading costs (about 1.00% per trade), not a 2%+ upward price rebound; the raw winsorized price rise is only +0.48%, which may simply be market drift (IWM rises roughly +0.7% in an average 20-session window), leaving zero or negative excess return against IWM.

### Rank 3: FDA decision-date (PDUFA) run-up in small biotech (buy before decision, sell before the date)

Why this is new: Round 43 (`docs/QUEUE.md` skip list) dropped pre-event long options around FDA PDUFA dates, not long-only equity run-ups.

Exact rule as stated:
- STATED ([pdufa.bio run-up by year](https://www.pdufa.bio/runup-by-year)): buy a biotech stock 30 trading days (or 60 to 120 trading days) before its scheduled FDA PDUFA action date and sell 1 to 7 trading days before the decision date (`T-30 -> T-1` or `T-30 -> T-7`), avoiding the binary decision day.

Stated numbers, sample, years, costs, and post-publication behavior:
- STATED ([pdufa.bio readout reaction](https://www.pdufa.bio/research/readout-reaction)): across `n = 1,661` "FDA decisions (PDUFA)", the "Median run-up (D-30 → D-1)" is `+0.43%`, and the study states: "No systematic pre-catalyst run-up."
- STATED ([pdufa.bio run-up by year](https://www.pdufa.bio/runup-by-year)): "What biotech stocks actually did into and out of an FDA decision, measured on real daily closes across 1,131 PDUFA events from 2020-01-08 to 2026-11-24." Yearly median 30-day run-ups (`T-30 -> T-1`) are: 2020 `+0.4%`, 2021 `+0.4%`, 2022 `+0.6%`, 2023 `−0.9%`, 2024 `+0.6%`, 2025 `+3.5%`, 2026 partial `+2.9%`. These are raw unhedged medians with no transaction costs subtracted and no benchmark adjustment stated.
- STATED ([pdufa.bio run-up heatmap](https://www.pdufa.bio/runup)): across "1,719 PDUFA events from 2020-2025", mean `T-30 -> T-7` returns are `+3.0%` (`57%` win, `n = 614`) in TIER_1, `+1.0%` (`57%` win, `n = 299`) in TIER_2, `+3.9%` (`53%` win, `n = 307`) in TIER_3, and `+1.2%` (`48%` win, `n = 499`) in TIER_4. However, "ODIN tiers are assigned by the Gungnir v24 model (AUC 0.988). Tier 1 represents the highest-conviction approval predictions; Tier 4 represents low confidence or likely CRL outcomes." That tiering is a proprietary model, not a public rule we can code without choices.

Data needed, event-count estimate, and Doc 117 power statement:
- Data: we do NOT hold a free point-in-time historical archive of pending PDUFA goal dates. The FDA does not publish pending PDUFA dates (Drugs@FDA records approvals post-hoc, and Complete Response Letters were only published starting in 2025). Reconstructing historical pending dates from SEC 8-K or 10-Q filings requires custom text extraction with non-trivial omission risk.
- Event count: STATED 1,131 events over 7 years (about 162 per year across all market caps; fewer in small-cap biotech).
- Doc 117 power statement: at the unconditional median of +0.43% raw (about +0.13% net after 30 bp small-cap biotech spread, UNKNOWN vs XBI), 1,000 events (roughly 500 effective turns) and 20% paired noise give `500 * (0.0013 / 0.20)^2 = 0.02`, far below 4. Even if small-cap biotech alone averaged +2.0% net over XBI across 400 small-cap events (about 250 effective turns) at 20% paired noise, `250 * (0.02 / 0.20)^2 = 2.5 < 4` (cannot reach 50% power).

Honest reasons it may be nothing:
- Across 1,661 PDUFA events, the unconditional 30-day median run-up is +0.43% ("No systematic pre-catalyst run-up").
- The +3.0% to +3.9% tier figures depend on a proprietary ML approval-probability model (ODIN Gungnir v24) and are raw returns unadjusted for biotech beta (XBI) or spreads.
- Small biotechs frequently issue dilutive secondary offerings, receive early FDA delays, or suffer advisory-committee setbacks inside the T-30 to T-1 window.

### Rank 4: Weekly cross-sectional momentum and reversal in liquid coins (Liu, Tsyvinski and Wu and post-publication follow-ups)

Repo overlap: `Queue 110` (`Ledger 216`, `docs/STATUS.md`) already closed weekly crypto dip versus breakout on power citing Grobys et al. (2025) at -0.19% (t = -0.13), and Round 46 (`docs/QUEUE.md` skip list) skipped US spot crypto weekly factor spreads. Because Round 52 specifically asked what happened after publication of Liu, Tsyvinski and Wu (2022), the 2026 replications are summarized here.

Exact rule as stated:
- STATED ([Karaptic Research / Arefev 2026](https://karaptic.com/blog/cross-sectional-momentum-net-of-costs/)): sort coins weekly by prior `J`-week return (`J = 1` or `J = 2`), go long top-quintile winners and short bottom-quintile losers (or long-only top quintile on US spot), hold `K` weeks (`K = 1` or `K = 2`), and rebalance weekly.

Stated numbers, sample, years, costs, and post-publication behavior:
- STATED post-publication reassessment ([Han Oct 2026, SSRN 7624971](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7624971)): "Liu, Tsyvinski, and Wu (2022) document size, price, momentum, volume, and volatility premia in cryptocurrency returns and explain them with a three-factor model. We replicate their study on independently collected data, extend the sample to May 2026, and mark portfolios to market daily. The volume and volatility premia flip sign in replication and vanish out of sample, the size and price premia lose significance out of sample, and no strategy performs consistently over 2014--2026."
- STATED net-of-costs replication ([Karaptic Research / Arefev Sep 2026](https://karaptic.com/blog/cross-sectional-momentum-net-of-costs/)): on "832 Binance USDⓈ-M perpetual futures symbols, using a daily-close panel from January 2020 through July 2026", "Over 338 independent weeks, the gross weekly spread came to +0.573%, positive in 52.7% of weeks." "A Binance taker fee of 0.05% per side plus an assumed 0.05% per side of slippage adds up to 0.40 percentage points round trip, roughly 70% of the gross spread. Net of that, the weekly average drops to +0.173%, and the share of profitable weeks falls to exactly 50.0%." For `J = 2 / K = 2`, "The headline phase came back net positive, +0.429% per week. The diagnostic phase came back negative, -0.076% per week."

Data needed, event-count estimate, and Doc 117 power statement:
- Data: already held (Binance archive daily bars and Coinbase USD spot access ledger from Plan 75). However, US spot is long-only and costs about 75 bp per side (150 bp round trip).
- Event count: 338 weekly turns from 2020 to mid-2026 (52 per year).
- Doc 117 power statement: at our 150 bp round-trip US spot fee, a +0.573% gross weekly spread becomes about -0.93% net per week (power = 0). Even to reach 50% power (`>= 4`) over 338 weeks at 10% weekly paired noise would require +1.09% net per week after costs, meaning at least +2.59% gross per week, more than 4x the measured 2020 to 2026 gross spread.

Honest reasons it may be nothing:
- The post-publication gross spread (+0.573% per week) is smaller than US retail spot fees (1.50% round trip) by nearly 3x.
- Rebalancing on a different day flips the `J = 2 / K = 2` net result from positive to negative, and Han (2026) finds no factor strategy performs consistently through May 2026.

### Rank 5: Non-odd-lot Dutch-auction self-tender offers (SEC Schedule TO-I)

Repo overlap: odd-lot cash issuer tenders already ran and did not pass (`Ledger 158`, `Replay 21`, `Queue 38`, only 14 placed in 10 years); open-market share buybacks are already dropped (`docs/QUEUE.md` and `docs/research/174_idea_round_51_larger_swing_edges.md`); third-party all-cash tenders (`SC TO-T`) were dropped in Rounds 33 and 39.

Exact rule as stated:
- Buy a US stock after the issuer files an SEC Schedule `SC TO-I` launching a modified Dutch-auction self-tender offer without relying on odd-lot priority, and either tender shares into the auction or hold until expiration (typically 20 business days).

Stated numbers, sample, years, costs, and post-publication behavior:
- STATED: no post-2015 empirical study reporting >= 2% net post-filing drift for non-odd-lot Dutch-auction tender participants was found (post-2015 net edge is UNKNOWN). Older pre-2015 studies attribute most gains to the announcement-day jump before a retail buyer can enter.
- STATED recent example of proration drag ([QuiverQuant](https://www.quiverquant.com/news/INVE+Technologies+Announces+Final+Results+of+Modified+Dutch+Auction+Self-Tender+Offer)): in INVE Technologies' November 2026 modified Dutch-auction self-tender, "The final proration factor for acceptance was around 70.1 percent", leaving 29.9% of tendered shares unaccepted and exposed to post-expiration market price drops.

Data needed, event-count estimate, and Doc 117 power statement:
- Data: free SEC EDGAR `SC TO-I` filings plus Alpaca SIP bars (held).
- Event count: exact 2016 to 2026 non-odd-lot Dutch-auction count is UNKNOWN without a fresh EDGAR census, but US issuer self-tenders (`SC TO-I`) total only a few dozen per year (nowhere near hundreds per year).
- Doc 117 power statement: with fewer than roughly 250 events over 10 years and UNKNOWN post-2015 net edge after proration and retail voluntary-reorganization fees (often $50 to $100 at US brokers, or 10% to 20% of a $500 account, noted in Round 39), this cannot clear Doc 117 (`< 4`).

Honest reasons it may be nothing:
- Retail voluntary corporate-action tender fees can exceed the entire dollar profit on a $500 account.
- Proration leaves an unhedged residual position exposed to post-tender price drops once the company's artificial bid ends.
- Event count is an order of magnitude too small for the Doc 117 power bar.
