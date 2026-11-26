# Round 8: What outside evidence says about trading dated events

Status: CURRENT. Outside reading, not a test. Sources checked 2026-11-25. Where the scout and checker differ, the checker's reading of the cited source takes precedence.

STATED means a linked source reports it. UNKNOWN means the evidence does not establish it. Nothing here was MEASURED by us.

## Newly listed companies that index funds must buy early

- KEEP, buy side only. STATED: CRSP adds eligible IPOs at the close of their fifth trading session, four trading days after the first close; the rule uses size and other eligibility screens ([CRSP methodology](https://www.crsp.org/wp-content/uploads/guides/CRSP_Market_Indexes_Methodology_Guide-January_2026.pdf), [Murray and Sammon](https://academic.oup.com/raps/article/16/2/163/8416725)).
- STATED: The published 5.16% is a peer-adjusted estimate for that window from a sample ending in December 2022, before spreads and trading costs ([Murray and Sammon](https://academic.oup.com/raps/article/16/2/163/8416725)). It is not the average return a trader would have earned buying qualifying stocks at the first close ([Murray and Sammon](https://academic.oup.com/raps/article/16/2/163/8416725)).
- STATED: Contrary to the scout's account, a buyer cannot always know before placing a closing order whether a borderline listing qualifies: eligibility uses the closing price, and the exact historical dollar cutoffs and share counts are proprietary ([Murray and Sammon](https://academic.oup.com/raps/article/16/2/163/8416725), [CRSP rule change notice](https://www.crsp.org/wp-content/uploads/2023/11/crsp-indexes-technical-notice_jan_2017.pdf)). Use [SEC prospectus filings](https://www.sec.gov/edgar/search/) and stock bars, keep names clearly above the applicable size cutoff, and check whether the result survives an entry at the next open if eligibility was not known before the close.

## Small-lot issuer tender offers

- KEEP, audit only. STATED: In an issuer tender offer, a company offers to buy back shares at a stated price or range; when the offer grants small-lot priority, qualifying holders of fewer than 100 shares who tender all their shares can be bought in full before larger holders are cut back ([Rule 13e-4](https://www.law.cornell.edu/cfr/text/17/240.13e-4)). This priority is optional in issuer offers and does not apply to third-party offers under Regulation 14D ([SEC tender offer guidance](https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/tender-offer-rules-schedules), [Rule 13e-4](https://www.law.cornell.edu/cfr/text/17/240.13e-4)).
- STATED: Practitioner reports put usable offers at about 1 to 6 a year, not hundreds; filings are not the same as exchange-listed offers with both a qualifying clause and a positive price gap ([KorroAi limitations](https://github.com/KorroAi/oddly/blob/main/PAPER.md), [EDGAR filing census](https://www.crowdfundedwealth.com/articles/tender-offer-funds-explained-sc-to-census-2026)). E*TRADE lists a $38 voluntary reorganization fee, rebated for some accounts; some other brokers charge nothing for the tender itself, so check the broker and account before treating the premium as profit ([E*TRADE fees](https://us.etrade.com/what-we-offer/pricing-and-rates), [IBKR fees](https://www.interactivebrokers.com/en/pricing/other-fees.php), [broker fee comparison](https://www.brokerage-review.com/account-fee/broker-reorganization-fee.aspx)).
- UNKNOWN: No honest published after-filing return series was found ([KorroAi backtest](https://github.com/KorroAi/oddly/blob/main/PAPER.md), [Kadapakkam et al.](https://link.springer.com/article/10.1007/s11156-020-00935-4)). The scout's standout backtest assumed buying five days before the announcement, and the checker could not establish whether withdrawn offers were kept ([KorroAi backtest](https://github.com/KorroAi/oddly/blob/main/PAPER.md)). A broader academic study found no significant cost-adjusted tender profits in its more recent sample; it did not isolate the small-lot clause ([Kadapakkam et al.](https://link.springer.com/article/10.1007/s11156-020-00935-4)).
- Audit all listed-company issuer offers from 2016 to 2026 using [SEC filings and amendments](https://www.sec.gov/edgar/search/). Record the first price gap available after the filing, the exact small-lot clause or its absence, and whether the offer closed, was amended, or was withdrawn; do not count that audit as a trading trial.

## Stock splits

- HOLD forward splits only. STATED: The US thesis reports a gross abnormal gain of 1.08% on announcement day and 0.98% on the next day, but virtually no gain the day after that; a buyer acting on the announcement may miss the first jump ([Paldanius](https://digikogu.taltech.ee/en/Download/ef745499-6a21-42fb-a9f2-9370864b46e3)). Other US studies disagree about whether there is anything to buy after the announcement, and the positive later result is gross ([Longwood thesis](https://digitalcommons.longwood.edu/cgi/viewcontent.cgi?article=1022&context=senior_theses), [Li, Chung and Liu](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4949379)).
- DROP reverse-split shorts. STATED: The scout used a lab experiment as if it were recent US market evidence; its quoted reverse-split losses come from older research, and the other cited negative-return study used Brazilian stocks and excluded events without complete data ([Duffy et al.](https://www.sciencedirect.com/science/article/pii/S0167268123002858), [Brazil study](http://www.scielo.org.pe/scielo.php?script=sci_arttext&pid=S2077-18862024000200277)). US research reports that shorting restrictions and borrow and trading costs block the proposed trade despite gross losses in the shares ([Kim, Klein and Rosenfeld](https://www.seoyoungkim.com/papers/kim_klein_rosenfeld_reversesplits.pdf)).

## Overnight returns against daytime returns

- DROP. STATED: The paper sorts by the prior year's overnight returns, not the prior month's overnight-minus-daytime spread; its screen also requires a near-full current trading year, which excludes some stocks the trader could not have known would disappear ([Lachance](https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/rfe.1180)).
- STATED: The big overnight differences mostly cancel during the day: the top and bottom groups earned 11.38% and 10.33% annualized over full days ([Lachance](https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/rfe.1180)). The cost model excludes bid-ask spreads and auction slippage, and the scout's multi-day hold does not isolate the overnight effect ([Lachance](https://onlinelibrary.wiley.com/doi/pdfdirect/10.1002/rfe.1180)). A separate point-in-time study reports a weaker end-of-day reversal in its later sample and makes no after-cost strategy claim ([Vidovich and Zerjal](https://arxiv.org/pdf/2611.09286)).

## IPO lockups expiring

- DROP. STATED: The reported rebound after expiration comes from European IPOs and is before costs, not evidence for a US long trade ([Vanje and Hardeberg](http://arc.hhs.se/download.aspx?MediumId=6595)). A Nordic study excluded bankruptcies and takeovers and concluded that the costs of trading, borrowing, and holding should make its finding unusable ([Hammer and Verberk](https://research-api.cbs.dk/ws/portalfiles/portal/76440832/1345526_Abnormalities_Surrounding_Nordic_IPO_Lock_up_Expiration_Hammer_Verberk_.pdf)).
- STATED: A US study estimated a potential short-side payoff but warned that failure to find shares to borrow, recalls, and collateral calls make it hard to capture ([Patatoukas, Sloan and Wang](https://mitsloan.mit.edu/sites/default/files/inline-files/Short-sales%20Constraints%20and%20Aftermarket%20IPO%20Pricing.pdf)). The short side is outside the small cash-account setup.

## Stocks removed from S&P indexes

- DROP. STATED: The study reporting a rebound contained no S&P 500 deletions in its deletion group and excluded bankruptcies and exchange delistings, so the rebound is not for the full set of deleted names ([Choi et al.](https://www.accessecon.com/Pubs/EB/2023/Volume43/EB-23-V43-I4-P143.pdf)).
- STATED: A separate S&P 500 study finds an average deletion return of only 0.1% from 2010 to 2020; another reports a lasting decline for true S&P 500 deletions rather than a rebound ([Greenwood and Sammon](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13410), [Kumar et al.](https://ideas.repec.org/a/eee/jbfina/v154y2023ics0378426623001747.html)).

## Closed-end funds below the value of their holdings

- DROP. STATED: The reported median and mean time for a discount gap to halve were about 8 and 14 months; the paper says hedging the value of the holdings is often costly or infeasible ([Durmaz et al.](https://www.degruyterbrill.com/document/doi/10.1515/snde-2024-0123/html)).
- STATED: Contrary to the scout, the other study did charge bid-ask spreads, but it tested long-short rules and left out funds that shut down, merged, or converted to ETFs ([Tiitola](https://osuva.uwasa.fi/server/api/core/bitstreams/05c8d08a-7987-4a02-b7ee-f0cc158f9ddd/content)). UNKNOWN: A free dated daily history of fund asset values with closed funds kept, which would be needed to rule out that bias.

## Prediction-market odds against option prices

- DROP. STATED: The main study compared three mid-2023 bitcoin threshold contracts on non-US venues and had only 16 trades in the pooled backtest; its after-cost result was not statistically clear at the 5% level ([Portnaya](https://arxiv.org/html/2606.19517v1)).
- STATED: A larger study reports that longshots tended to be overpriced at long horizons but does not model fees or spreads, and does not establish that the pricing difference can be traded against options ([Le](https://arxiv.org/html/2602.19520v1)). UNKNOWN: A free historical match of US prediction-market books and option chains, or a practical small-account US hedge replicating the study.

## What this means for us

These are the builder's decisions, not owner decisions or trial results. Nothing here authorizes a real trade.

- Keep row 37 for a fixed long-only test: buy only fast-track-size listings at the first close and exit at the close four trading days later. The plan must address how to know eligibility before placing a closing order.
- Keep row 38 for an audit only: count and record listed-company small-lot tenders, including offers that changed or failed. Do not treat the existence of an offer as a fill or a return.
- Hold the forward-split idea only. Drop the reverse-split short and ranks 4 through 8.

## Gaps

- UNKNOWN: Whether the fast-track effect survived after 2022, what a trader could identify in time for the closing trade, and what was left after costs ([Murray and Sammon](https://academic.oup.com/raps/article/16/2/163/8416725)).
- UNKNOWN: The actual annual count, after-filing price gaps, and completed or failed outcomes for usable small-lot offers; those are the audit questions, not inputs to assume ([SEC filing search](https://www.sec.gov/edgar/search/), [KorroAi limitations](https://github.com/KorroAi/oddly/blob/main/PAPER.md)).
