# Insider buying: what the evidence says before any test

Last verified: 2026-11-25. Written by research. Nothing here is an owner decision, and nothing here was tested by this project. No rule was run and no price data was downloaded.

Why this page exists: decision 11 in `docs/decisions/morning_list_2026-11-25.md` proposes insider buying that is not routine as the first high-risk idea to test. `docs/research/13_high_risk_sleeve_evidence.md` gave the 2012 paper's headline. This page reads what came after it. The draft test plan, which runs nothing, is `research_rig/PREREG_08_insider_buying_DRAFT.md`.

How it was made: one researcher read the sources and wrote notes. Research then opened these sources again and checked the figures used below: the 2012 paper, the Aalto thesis, the 2026 preprint, the Equibles study, the Lee paper, the three fund filings, the Catalyst fact sheet and annual report, the SEC data page, FINRA's notice, EODHD's page on delisted stocks, and Apple's filing list at the SEC. The two closing notices were not opened again. One figure in the notes was wrong and is corrected here (the Catalyst benchmark). Everything else in the notes that is used below and was not opened again is marked "not rechecked".

Labels: MEASURED means read on an official filing, a rule text or a regulator's data page. STATED means claimed by a paper, a vendor or a promoter. Every paper result here is a backtest and is STATED. UNKNOWN means not found.

## The short version

- The 2012 paper's result is real as published, and it is old. Its sample ends in 2007 and it deducts no costs.
- Its main idea, that buys which break an insider's usual pattern do better than routine buys, does not hold up in the two later samples found. In one the gap is not different from zero. In the other it points the wrong way.
- Plain insider buying may still earn something after 2008. The sources disagree, and both sides are shown below.
- Much of the gain now arrives on the first day after the filing. In the one recent sample that measures it, a trader who misses that first day is left with a gain that cannot be told from zero.
- Three funds that used insider buying with real money have records long enough to read. Two trailed the S&P 500 over the whole period read. The third beat it over ten years to 2018 and trailed it over the last five of those. Two of the three closed.
- A test here is cheap in data and worth a plan. The honest expectation is a fail or a small result. It is a test of whether anything is left for a slow, small buyer, not a search for the paper's number.

## The rule in the 2012 paper

Source: Cohen, Malloy and Pomorski, [NBER working paper 16454](https://www.nber.org/system/files/working_papers/w16454/w16454.pdf). The journal version is behind a paywall and was not read. All STATED.

- Trades used: open-market buys and sells on Form 4 by officers, directors and owners of more than 10%. Option exercises and private deals are left out.
- Who can be sorted: an insider with at least one trade in each of the three years before.
- Routine: "we define a routine trader as an insider who placed a trade in the same calendar month for at least three consecutive years." Everyone else who can be sorted is opportunistic. The paper counts 64% of buys as routine.
- The portfolio: "A firm is included in the opportunistic buy portfolio, for example, in month (t+1) if any of its insiders placed an opportunistic buy on the firm in month t." Held for that month, then rebuilt.
- The paper keys on the month of the trade, not the day the filing became public. It gives the middle delay between trade and report as 3 days over its sample.
- No filter on price or company size was found in the text read. UNKNOWN whether the journal version has one.

What it measured, 1989 to 2007, percent a month, before costs:

| Portfolio | Five-factor result | t-statistic |
|---|---|---|
| Opportunistic buys, every stock weighted the same | 1.58 | 7.03 |
| Opportunistic buys, weighted by company size | 0.72 | 2.27 |
| Opportunistic buys minus opportunistic sells, weighted by company size | 0.82 | 2.15 |
| Opportunistic buys, weighted by company size, four-factor model | 0.52 | 1.73 |

- The large number comes from weighting every stock the same, which leans on the smallest companies. Those are the costliest to trade.
- Weighted by size, and with the four-factor model, the buys-only result has a t-statistic under 2.

## What later work found

| Study | Years | Finding | Label |
|---|---|---|---|
| [Wu, Aalto University thesis, 2025](https://aaltodoc.aalto.fi/server/api/core/bitstreams/fbbd1ec6-d5b4-44dd-881d-144ffd0ea21c/content) | 2008 to 2024 | Opportunistic buys: 0.65 a month weighted the same (t 6.66), 0.67 weighted by size (t 2.29). Routine buys: 0.62 (t 2.79) and 0.54 (t 4.29) | STATED. A master's thesis, not peer reviewed |
| Same thesis | 2008 to 2024 | Opportunistic minus routine buys: 0.03 (t 0.31) and 0.13 (t 0.80). Not different from zero | STATED |
| [Lee, Lemmon, Li and Sequeira, 2011](https://www.business.kaist.ac.kr/faculty/inmoo/Articles/LeeLemmonLiSequeria_March_2011.pdf) | 1986 to August 2008 | Three-month return after a buy, measured from the trade date: 2.79% (t 17.29) in 1991 to 2002, 0.25% (t 1.10) after 2002. "the profitability of insider trading completely disappears in the post-2002 period" | STATED |
| [Equibles Research, August 2026](https://equibles.com/research/what-happens-after-an-insider-buys-evidence-from-47-458-open-market-purchases) | 2020 to August 2025, 47,458 buys, entry at the first close after disclosure | Middle one-year result 12.95 points behind the S&P 500 and 2.56 points ahead of the middle stock. With the paper's split, routine buys did better than opportunistic buys. None of its checks against a shifted date was different from zero | STATED. A data vendor's own study, not peer reviewed |
| [arXiv 2602.06198](https://arxiv.org/html/2602.06198v2) | 2018 to 2024, companies worth $30 million to $500 million | Holding from the first day after the filing: 2.14% a month weighted the same (t 5.54). Skipping that first day: 0.68% (t 1.78) and 0.53% weighted by size (t 1.60), "statistically indistinguishable from zero" | STATED. A preprint, not peer reviewed |
| [McLean and Pontiff, 2016](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.12365) | 97 published signals | Returns "26% lower out-of-sample and 58% lower post-publication" | STATED. Abstract only, not rechecked |

Where the sources disagree:

- The thesis table shows opportunistic buys still earning about 0.65 a month. The thesis abstract says about 0.3 to 0.4 a month and "60 to 70 percent weaker". Research could not tell which the author stands behind.
- The thesis finds buys still earn something after 2008. Lee and co-authors find nothing after 2002. The methods differ: a monthly portfolio against a factor model in one, a return measured from the trade date in the other.
- On the paper's main idea the two later samples agree with each other and not with the paper: breaking a pattern no longer marks the better buys.

## Funds that tried it with real money

Fund returns are from SEC filings and one fund fact sheet. MEASURED as published records.

| Fund | Years | Fund | S&P 500 | Cost a year | Now |
|---|---|---|---|---|---|
| Catalyst Insider Buying, class A, no sales charge | 2011-07-29 to 2026-09-30 | 8.62% a year | 14.51% a year | 1.53% after waivers | Open ([fact sheet](https://catalystmf.com/docs/factsheets/INS/factsheet.pdf)) |
| Same fund | Ten years to 2026-06-30 | 7.87% a year | 15.51% a year | | Net assets $22.2 million ([annual report](https://www.sec.gov/Archives/edgar/data/1355064/000158064226006181/catalyst-equity_ncsr.htm)) |
| Direxion All Cap Insider Sentiment (KNOW) | 2011-12-08 to 2019-12-31 | 12.62% a year | 14.74% a year | 0.66% | Closed in October 2020 ([prospectus](https://www.sec.gov/Archives/edgar/data/1424958/000119312520056220/d882073d497k.htm), [closing notice](https://www.sec.gov/Archives/edgar/data/1424958/000119312520249163/d50570d497.htm)) |
| Invesco Insider Sentiment (NFO) | Ten years to 2018-12-31 | 13.80% a year | 13.12% a year | 0.66% | Closed in February 2020 ([prospectus](https://www.sec.gov/Archives/edgar/data/1209466/000119312519231744/d742741d497k.htm), [closing notice](https://www.sec.gov/Archives/edgar/data/1209466/000119312519313283/d839044d497.htm)) |
| Same fund | Five years to 2018-12-31 | 5.37% a year | 8.49% a year | | |

- Correction to the notes: the notes set the Catalyst class A figure beside 13.70%. That is the benchmark for a different share class with a later start date. The fact sheet's benchmark for class A is the one in the table.
- None of these funds ran the paper's rule as written. Each mixed insider buying with other things. Catalyst also ran a side strategy that its report says lost money (not rechecked). So they are a loose test.
- KNOW turned its whole portfolio over about nine times a year (907%), by its own prospectus.
- Two more funds were found and not read: Direxion Large Cap Insider Sentiment (closed 2013) and Catalyst Small-Cap Insider Buying (merged away in 2021). UNKNOWN.
- A newer fund, Tweedy Browne Insider + Value (COPY), opened in December 2024. Its record is too short to read. Not rechecked.

## How fast the price moves

- In the 2018 to 2024 small-company sample, the first day supplies 0.53 of the average 30-day move, and 60.0% of buy filings reach the SEC at or after the 4pm close ([arXiv 2602.06198](https://arxiv.org/html/2602.06198v2)). STATED.
- So a buyer who waits for the next morning pays the overnight jump, and a buyer one day later has little left in that sample.
- The 2012 paper's own chart shows returns building for six months (not rechecked). That was before 2008. Whether a slow gain still exists is the thing a test here would measure.
- An older study found prices move within seconds of a filing being posted. Not rechecked.

## A trap in the dates

- The SEC stamps a filing with the day it was sent. A Form 4 sent by 10pm New York time carries that same day ([17 CFR 232.13](https://www.ecfr.gov/current/title-17/chapter-II/part-232/subpart-A/section-232.13), not rechecked).
- MEASURED on 2026-11-25: the five latest Form 4 filings in [Apple's list at the SEC](https://data.sec.gov/submissions/CIK0000320193.json) were all accepted between 22:30 and 23:58 UTC, after the market closed, and each carries that same day as its filing date.
- So a test that buys at the close on the filing date is buying before the news was public. The list gives the acceptance time to the second. A fair test buys at the next open after that time.

## Data a test would need

- Filings: the SEC's [insider transactions data sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets) cover "January 2006 - September 2026", are free, and are taken from the filings "without change". MEASURED. Their readme lists a filing date, and no acceptance time was found in it (not rechecked), so the time has to be read from the SEC's filing lists, one company at a time. The SEC allows 10 requests a second and asks for a name and an email address in each request (not rechecked). That needs the owner's yes, since it would carry a contact address.
- Prices: daily open and close for every stock an insider bought, including the ones that later went bankrupt or were bought out. Leaving the dead ones out makes any stock rule look better than it was.
- EODHD says "Delisted tickers are available in any of our packages" and that it covers "26,000+ US stock tickers (mostly from Jan 2000)" ([EODHD](https://eodhd.com/financial-academy/financial-faq/historical-stock-prices-for-delisted-companies)). STATED by the vendor. So the one-month purchase in item 2 of the morning list would also cover this test. Its help page allows keeping the files after cancelling, for private use (`docs/research/10_historical_data_and_practice.md`). How complete the dead-stock coverage is, is UNKNOWN until it is checked against the SEC's list of companies.
- Other vendors that say they carry dead stocks: Norgate, Massive and Sharadar. Tiingo says its coverage starts about 2014. Not rechecked.
- Cost of trading: small companies have wide spreads. The 2018 to 2024 sample puts the middle spread at 1.33% for its companies ([arXiv 2602.06198](https://arxiv.org/html/2602.06198v2)). STATED, and an estimate. A test has to charge something like this, and `config/thresholds.yaml` has no key for single-stock cost yet.

## Rules that touch it

- Trading on a Form 4 after it is public is not insider trading. Insider trading is trading on information that is not public, in breach of a duty ([Investor.gov](https://www.investor.gov/introduction-investing/investing-basics/glossary/insider-trading)). This is research's reading and not legal advice.
- Holding for weeks is not day trading. FINRA has in any case replaced the pattern day trader rule and its $25,000 minimum, effective June 4, 2026, with brokers allowed until October 20, 2027 to switch ([FINRA notice 26-10](https://www.finra.org/rules-guidance/notices/26-10)). MEASURED. `docs/research/09_brokers_and_venues.md` has the broker detail.

## What a fair test has to do

1. Enter at the next open after the acceptance time, never at the filing-date close.
2. Keep the stocks that died.
3. Charge a spread that fits the size of the company.
4. Test few variants, all written down first, and count every one.
5. Compare with holding the whole market, and also with the same number of random stocks of the same size, so that a small-company effect is not mistaken for an insider effect.
6. Report plain insider buying beside the paper's split, since the later evidence says the split may add nothing.

## What this changes

- Decision 11 still recommends insider buying as the first high-risk idea to test, with a weaker case than the morning list gave it. It was the idea with the longest published evidence. The newer evidence says the edge shrank, moved to the first day, and did not show up in the funds.
- It is not a fast-money idea. A hold of a month in many small positions is slow and costs a spread each time.
- Nothing here supports buying on insider filings with real money today.

## Not read

- The journal version of the 2012 paper, the full McLean and Pontiff paper, and Cline, Gokkaya and Liu 2017 (paywalls).
- The two smaller funds named above.
- Terms on keeping data after a subscription ends, for Tiingo, Massive and Sharadar.
- A recent table of spreads by company size for stocks above $5.
