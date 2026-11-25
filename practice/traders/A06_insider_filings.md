# A06 insider_filings

Status: builder settings, 2026-11-25. Untested. Market: US stocks above $5. Holding time: 1 to 6 weeks.

## What it tries to do

It reads fresh SEC filings where company insiders bought their own stock with their own cash, or where an activist investor disclosed a large stake, and buys the few that look like real conviction rather than routine. It acts at its first wake after the filing, because the evidence says most of what is left arrives on the first day.

## Why this might work

- STATED, old: buys by insiders who broke their usual pattern did better than routine buys, 1989 to 2007, before costs ([Cohen, Malloy and Pomorski](https://www.nber.org/system/files/working_papers/w16454/w16454.pdf), via `docs/research/26_insider_buying_evidence.md`).
- STATED, against: in two later samples that "routine versus not" split does not hold up (document 26).
- STATED: in a 2018 to 2024 sample of small companies, holding from the first day after the filing gained much more than holding from the second day, which could not be told from zero ([arXiv 2602.06198](https://arxiv.org/html/2602.06198v2), via document 26). 60% of buy filings reached the SEC at or after the 4 pm close (same source).
- MEASURED, against: of three funds that used insider buying with real money, two trailed the S&P 500 over the period read and two closed (document 26).
- MEASURED, old: activist filings had about 7.2% abnormal return around the filing, but most of it came before a follower could act ([Brav et al.](https://www.fdic.gov/analysis/cfr/working-papers/2008/2008-06.pdf), via `docs/research/13_high_risk_sleeve_evidence.md`).
- Honest summary: a real reason, weak recent evidence. The model's edge would be reading each filing's footnotes and the company's situation fast.

## What it looks at each time it wakes

- Its holdings and cash.
- SEC Form 4 filings since its last wake: the EDGAR current filings feed for Form 4 and Schedule 13D, listed in `docs/research/19_information_feeds.md`. UNKNOWN: whether the desk's web tool can read that feed; if not, web search "Form 4 purchase today".
- For each candidate: the filing itself, the company's last two reports, Alpaca news, daily bars for 60 days.

## How it decides to buy

1. Transaction code P, read in the filing, and the model confirms from the footnotes that it is an open-market buy, not a private deal, an option, or a plan buy (document 19 notes code P alone does not prove this).
2. The buyer is the chief executive, the finance chief, or a director, or several insiders bought within 10 days.
3. The buy is large next to the person's stated holdings or pay, as far as the filing and the proxy show.
4. Or, for a 13D: a known activist with a stated plan in item 4 of the filing.
5. No obvious reason the buy is not conviction: required holdings, a rights offering, a company buying from itself.
6. Share price above $5, company value above $300 million.
7. The model writes what the insiders might know, and what would prove it wrong.

## How big

- 7% of its budget per position, at most 8 positions.

## How it gets out

- Stop price: 12% below entry.
- Target price: 20% above entry.
- Exit-by time: 6 weeks after entry, at 15:45 Eastern.
- Sold at the next wake if the same insiders file a sale.

## What it never does

- Buys on a filing older than 2 market days.
- Buys stocks under $5, OTC stocks, or companies under the size floor.
- Follows politicians' trades or chat room insider claims (`docs/research/19_information_feeds.md` lists Congress trades as no usable edge).

## When it wakes

- 09:45 and 15:30 Eastern on market days. The 09:45 wake catches filings made after the previous close.

## What would make us drop it

- The rules in `practice/traders/ROSTER.md`, "How we judge".
- Also: if fewer than 10 trades happen in 60 trading days, it is too rare to judge and waits for the replay in `research_rig/PREREG_08_insider_buying_DRAFT.md` instead.
