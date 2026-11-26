# Reverse-split round-ups: feasibility (queue row 43, plan 30)

Status: CURRENT. Written 2026-11-26 04:24 UTC as an off-repo memo, moved here 2026-11-26 after the lead's ruling. No price was read. Counts come from two scripts kept off repo in `~/workspace/rig/plan30_draft/`.

Ruling (lead agent, 2026-11-26): no frozen test on past data. A no-money forward log is built off repo. The real one-share check is put to the owner by the lead.

Short answer: the trade is real on paper and small. What decides it is whether your broker hands you the rounded-up share, and that is not in any price file. A frozen test on past data can only repeat an assumption. So the decision is a forward log with no money, with two drop rules fixed now. A real one-share check is the owner's call.

## 1. The mechanism and who decides the outcome

STATED, the mechanism ([Trial 60 write-up](https://github.com/mtrinkner/edge-audit/blob/main/docs/REVERSE_SPLIT_ROUNDUP.md)):
- A listed company announces a 1-for-N reverse split and says fractional shares will be rounded up to a whole share instead of paid in cash.
- One share bought before the split becomes 1/N of a new share, then rounded up to one whole new share, worth about N old shares.
- It works once per account per split. It does not scale.

Three parties decide what a retail holder actually gets.

The issuer's wording comes first:
- "Rounded up at the beneficial holder level" means each end customer is rounded up. Robinhood says only this kind gives individual holders a share ([Robinhood corporate actions](https://robinhood.com/us/en/support/articles/mergers-stock-splits-and-more/)).
- "Rounded up at the DTC participant level" means only the broker's total position is rounded up. Longeveron said it would not round up at the beneficial owner level ([Longeveron release](https://www.sec.gov/Archives/edgar/data/1721484/000121390026093028/ea030309701ex99-1.htm)). Ryde Group said its round-up applies to the whole DTC position and not to each beneficial holder ([Ryde 6-K](https://www.sec.gov/Archives/edgar/data/1971115/000149315226053874/form6-k.htm)).
- Many filings add that brokers may apply their own procedures ([Beyond Meat release](https://www.sec.gov/Archives/edgar/data/1655210/000165521026000057/ex991pressreleaseannouncin.htm)).
- Some issuers add conditions. American Rebel's round-up needs each broker to answer DTC's election requests in time ([American Rebel notice](https://www.sec.gov/Archives/edgar/data/1648087/000149315225021519/ex99-18.htm)).

The transfer agent and DTC come second. DTC gathers round-up requests from brokers, and the issuer then delivers the shares. American Rebel describes about 4 business days to gather and about 10 trading days to deliver ([American Rebel 1-for-20 notice](https://www.sec.gov/Archives/edgar/data/1648087/000149315225021519/ex99-13.htm)). STATED.

The broker comes last. Its handling, from each broker's own page (all opened 2026-11-26):

| Broker | Passes a beneficial round-up through? | Source, label |
|---|---|---|
| Robinhood | Yes, "when received from the issuer", about 3 to 4 weeks after the split. Fractions across one person's individual accounts are combined first. OTC fractions are sold | [corporate actions](https://robinhood.com/us/en/support/articles/mergers-stock-splits-and-more/), STATED |
| Webull | Yes, but since 2024-12-02 only after clearing receives the shares, up to 3 to 4 weeks. Until then a placeholder fraction that "you will be unable to liquidate" | [Webull corporate actions](https://www.webull.com/help/faq/431-Corporate-Actions-Introduction), STATED |
| Interactive Brokers | No. Round-up privileges "will not be supported" | [IBKR FAQ](https://www.interactivebrokers.com/support/faq/content/will-receive-fractional-share-position-84639080), STATED |
| Moomoo | No. Reverse splits pay cash in lieu of fractions | [Moomoo policy](https://www.moomoo.com/us/support/topic4_480), STATED |
| Fidelity | Not promised. The agreement says fractions are normally distributed to three decimals, subject to the issuer's terms. A reply posted as Fidelity's says "We do not support this type of activity related to reverse splits" | [Fidelity agreement](https://www.fidelity.com/bin-public/060_www_fidelity_com/documents/brokerage-account-customer-agreement.pdf), STATED; [Reddit post](https://www.reddit.com/r/fidelityinvestments/comments/1cphx9p/seeking_official_stance_on_reverse_stock_roundup/), UNKNOWN whether genuine |
| Schwab | Not promised. Schwab "may either sell the shares on the open market or to the issuer or transfer agent" and pay the pro rata proceeds. $0 reorganization fee | [Schwab agreement](https://www.schwab.com/legal/schwab-brokerage-account-agreement), [Schwab pricing](https://www.schwab.com/legal/schwab-pricing-guide-for-individual-investors), STATED |
| E*TRADE | Charges $38 for a mandatory reverse split. That is more than any gain | [E*TRADE pricing](https://us.etrade.com/what-we-offer/pricing-and-rates), STATED |
| Public | May charge an administrative fee if you sell within 90 days of a reverse split; you are told at purchase | [Public help](https://help.public.com/en/articles/9628217-what-is-a-reverse-split-fee), STATED |
| Alpaca | The page does not say. It only says GTC orders are cancelled at a reverse split | [Alpaca corporate actions](https://docs.alpaca.markets/us/docs/mandatory-corporate-actions), UNKNOWN |

Only Robinhood and Webull document passing a beneficial round-up through. Both pay only after the issuer delivers. A trader's broker notes from November 2024 say Robinhood and tastytrade have sometimes credited fractions instead ([revRSS broker notes](https://www.revrss.com/2023/10/09/which_brokers.html)). STATED by one trader.

## 2. How many a year, 2023 to 2026

MEASURED 2026-11-26 from SEC EDGAR full-text search: one request at a time, at most 2 a second, with a declared User-Agent, counts only. Script and output are off repo: `~/workspace/rig/plan30_draft/edgar_counts.py`, and `~/workspace/rig/plan30_draft/edgar_counts.json` with sha256 150876774269ab0555a65c12d6f8dc73d27c8c4866d49822bf0e11202772d2aa. The 2026 figures run to 2026-11-25. Form 8-K only: a form list that includes "8-K/A" silently narrowed the search, so amendments are left out.

Distinct companies with at least one matching 8-K document (including exhibits):

| Phrase in one document, with "reverse stock split" | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|
| "rounded up" | 412 | 336 | 344 | 386 |
| "rounded up to the nearest whole share" | 140 | 123 | 123 | 179 |
| "rounded up" and "participant level" | 0 | 3 | 15 | 28 |
| "cash in lieu" | 302 | 274 | 308 | 303 |
| 6-K: "reverse", "split", "rounded up" (foreign issuers) | 79 | 96 | 119 | 184 |

These are upper bounds, not events. MEASURED on a fixed random sample of 20 matching 2026 filings (off repo, `~/workspace/rig/plan30_draft/precision_sample.txt`, sha256 e42bdfb20bf7fb17f2fd0ec5c4e052b77fac441ceb6c8a8a7616bdf3ea6323f3):
- Only 6 of 20 were a company describing its own reverse split with round-up wording. One of the 6 was a TSXV and OTC name.
- The other 14 were merger agreements, warrants and option plans that happen to contain both phrases.
- At about 3 in 10, the 2026 figure of 386 companies is nearer 100 to 130. A company often files twice for one split (the announcement and the completion), and some split more than once a year.
- The participant-level row is a lower bound, because the wording varies. Its rise from 0 to 28 companies is the clearest trend here.

Outside counts, STATED:
- Trial 60 classed exchange-listed CRSP splits as round-ups per holder and at participant level: 105 and 10 in 2023, 131 and 17 in 2024, 109 and 10 in 2025. Only a share of these had a usable announcement before the split. Its frozen rule traded 16, 45 and 43 events in those years ([Trial 60](https://github.com/mtrinkner/edge-audit/blob/main/docs/REVERSE_SPLIT_ROUNDUP.md)).
- Signal8 counted 376 reverse splits effective from 2026-05-01 to 2026-11-13. Of the 340 that stated a method, 218 rounded up (64.1%) and 89 paid cash. At least 40 of the 218 said participant level ([Signal8](https://signal8.ai/learn/market-structure/reverse-split-fractional-shares)).

Working figure: roughly 100 to 150 listed round-up splits a year. Only about 40 to 50 a year have a pre-split announcement, a beneficial-level promise and a usable entry day. Signal8 suggests 2026 is higher. STATED and MEASURED together; the exact tradeable count is UNKNOWN until a parser is run.

## 3. Dollars per event, capital, and how it fails

STATED from Trial 60, 121 listed events in 2019 to 2025, one share each, buy at the ask and sell at the bid:
- The mean was $4.24 an event if every round-up is delivered. At the assumed delivery rates (80% for holder-level, 40% for participant-level) it was $3.17, with a median of $2.83.
- The worst event lost $0.08, and 97.5% made money.
- At a 20% delivery rate it was $0.86. With a $5 commission every event lost: -$5.64 on average.
- Capital per event was about $0.10 to $7.
- About $55 a year per account at the 2019 to 2025 pace, and $125 at the 2024 to 2025 pace.
- Its exit is the bid on the effective date. A Robinhood or Webull holder cannot sell until the share arrives about 3 to 4 weeks later. The value at that later date is UNKNOWN; Trial 60's 5-day-later exit was $3.05.

What this means for the $500 account (derived from the figures above, not measured):
- Capital is not the limit. A few open events at a few dollars each is under $50.
- The gain is a few dollars an event and roughly $50 to $150 a year at best, before any delivery failure.

Failure cases and their rough cost for one share (STATED where linked, the dollar sizes are my reading of the cases):

| Case | What you get | Rough cost |
|---|---|---|
| Broker pays cash in lieu or credits a fraction | 1/N of a new share in cash | The spread and any fall on a share of a few dollars; cents to about $1 |
| Issuer wording is participant level | Usually cash or a fraction | Same as above |
| Split cancelled or terms changed | A sub-$1 stock to sell | Cents to about $1. Changed terms forced 7 exits in Trial 60 |
| Price falls before the split | The share is worth less | At most the purchase price, a few dollars |
| Halted or delisted, or moved to OTC | Robinhood sells OTC fractions; a whole OTC share may be hard to sell | Up to the purchase price |
| Round-up reversed after you sold the credited share | A short position you must cover | Up to one post-split share, often several dollars, plus effort. STATED: "retroactive changes in broker instructions, from rounding up to cash-in-lieu, resulted in new short positions in people's accounts" ([revRSS update](https://www.revrss.com/2025/05/04/manipulation_investigations_2.html)); SIFMA describes the same path ([SIFMA letter](https://www.sifma.org/advocacy/letters/reverse-stock-splits-and-fractional-share-round-ups)) |
| Broker fee | $38 at E*TRADE, a fee at Public | Larger than the gain |
| Account closed | You must move everything else out | Not in dollars, and the largest risk for a main account. STATED by one trader for Ally ([revRSS broker notes](https://www.revrss.com/2023/10/09/which_brokers.html)); others report it on forums, UNKNOWN how often |

## 4. Can it be tested on past data

- Past prices can show the price part. Trial 60 already did that, frozen, on 2019 to 2025: positive and small. STATED.
- The decisive part is the delivery rate p: did this broker credit a whole share to this customer, and when could it be sold? No public source records it. Trial 60 assumed it (0.8 and 0.4) and says plainly: "Not established: p itself" ([Trial 60](https://github.com/mtrinkner/edge-audit/blob/main/docs/REVERSE_SPLIT_ROUNDUP.md)). UNKNOWN.
- A replay on our own bars would rest on the same assumption. The only new thing it could add is a later exit price, about 3 to 4 weeks after the split instead of on the effective day. That is worth knowing, but it is not a test of the trade.
- A forward log with pretend positions cannot observe p either, because a pretend share is never rounded up.

A forward log can observe, with no money:
- the issuer's wording class and the time it was first public;
- whether the issuer kept, changed or cancelled the terms;
- Robinhood's own tracker entry for the event (STATED broker intent, not an account credit; [Robinhood tracker](https://robinhood.com/us/en/support/articles/corporate-actions-tracker/));
- the price path after the split, from bars, to value an exit 3 to 4 weeks later.

The only way to measure p is to hold one real share through the split and record what arrives and when. Trial 60's own forward plan says the same.

## 5. What a careful person should know

- One account, one share, no extra accounts. Robinhood combines one person's individual accounts. Upexi's complaint described wash trades and matched orders across many accounts. After its 2024 split, brokers asked for 202,183 round-up shares, more than 19% dilution ([Upexi release](https://ir.upexi.com/news-events/press-releases/detail/93/upexi-to-take-action-against-apparent-stock-manipulation-of), [Computershare case study](https://www.computershare.com/us/insights/transfer-agent-services/upexi-reverse-stock-split-case-study)). Upexi's suit named buyers before the split and was dismissed without prejudice ([revRSS update](https://www.revrss.com/2025/05/04/manipulation_investigations_2.html)). STATED.
- A credited share can be taken back. SIFMA notes that the credited share "is merely a credit that will be delivered at a later date". If the issuer refuses delivery, the broker may buy in, and a customer who sold can be left short ([SIFMA letter](https://www.sifma.org/advocacy/letters/reverse-stock-splits-and-fractional-share-round-ups)). STATED. Do not sell before the share is delivered and settled.
- The industry is pushing to end it. SIFMA asked NYSE and Nasdaq in March 2025 to make cash in lieu the standard, and repeated this in December 2025 ([SIFMA framework](https://www.sifma.org/research/white-papers/reverse-stock-splits-and-fractional-share-management-a-framework-for-market-integrity)). Computershare advises issuers to pay cash. No exchange rule set one method as of 2026-11-17 ([Signal8](https://signal8.ai/learn/market-structure/reverse-split-fractional-shares)). STATED. The rise in participant-level wording above is MEASURED.
- The notice can be short. Nasdaq requires public disclosure at least two business days before the market effective date, as cited in the SIFMA letter. Under T+1 the buy must settle before the split. A daily check is needed, not a weekly one. STATED.
- Fees, minimums and closures can erase the gain. Check the reverse-split fee (E*TRADE $38, Public's fee), any small-order minimum or commission, and that the account is a cash account with settled funds. The trader who ran revRSS stopped on 2024-11-02 and had not resumed by 2025-05-05 ([revRSS update](https://www.revrss.com/2025/05/04/manipulation_investigations_2.html)). STATED.
- Taxes: each event is a short-term gain of a few dollars plus a line on the year's tax form. Tiny, but it adds bookkeeping.

## Decision and drop rules

Forward log, no money. No frozen test on past data, and no drop yet.

- No frozen test: it would repeat Trial 60 under the same assumed p, and the decisive number is not in any price file.
- Forward log, off repo: run once a day from EDGAR. For each new 8-K with reverse-split and round-up wording, it records the filing's own sentence, its class (beneficial-holder level, participant level, cash in lieu or unclear), the accession, the effective date and the ratio. For beneficial-level events it records two values: one pre-split share at the last close before the effective day, and one post-split share at the close 20 sessions later. That is the value at full delivery only (p = 1). No position is taken.
- Drop rule 1: drop if fewer than 1 beneficial-level event a month qualifies for 3 months running.
- Drop rule 2: drop if, after 20 logged beneficial-level events, the mean of (post-split share at 20 sessions minus pre-split share) is not above zero at p = 1.
- Real-share check: holding one real share through 20 events at one named zero-fee broker that documents pass-through (Robinhood or Webull) would measure p for about $50 at risk. It is a real-money action. The lead puts it to the owner. It should not be done in his main account, given the closure risk. Until then p stays UNKNOWN, and no dollar figure here is a forecast.
