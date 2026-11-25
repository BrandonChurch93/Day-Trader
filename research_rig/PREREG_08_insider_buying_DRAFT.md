# Pre-registration 08 (draft): buying after insiders buy

Status: DRAFT, written 2026-11-25. Not frozen and not in the trial ledger. It runs nothing and no data has been downloaded for it. It is frozen and logged only when every gate below is met, and before any rule is run. Proposed by research. No owner decision is recorded here.

Blocked on, each one separately:

- The owner's yes to decision 11 in `docs/decisions/morning_list_2026-11-25.md` (the order in which high-risk ideas get tested).
- His decision on pass mark 4 (decisions 1a and 1b).
- Daily prices that include stocks that later died. Item 2 of the morning list would cover it if the vendor's claim holds (`docs/research/26_insider_buying_evidence.md`, "Data a test would need").
- His yes to reading the SEC's filing lists. Each request has to carry a name and a contact email address, and research will not pick one for him.
- Keys in `config/thresholds.yaml` for the numbers this plan needs and does not have, each with a dated note in `docs/decisions/`. They are listed under "To settle before this is frozen".

## Why

The owner allows a small high-risk share for ideas with a reason behind them. Insider buying has the longest published evidence of the high-risk ideas read (`docs/research/13_high_risk_sleeve_evidence.md`). The evidence after 2007 is weaker and mixed, most of the recent gain lands on the first day, and the funds that tried it mostly trailed the market (`docs/research/26_insider_buying_evidence.md`). So the question is narrow: is anything left for a small buyer who enters the next morning and pays the spread?

The honest expectation, written before any run: a fail, or a small result. This is not a fast-money idea.

## Data needed

- Form 4 open-market buys from the SEC's insider transactions data sets, and the acceptance time of each filing from the SEC's filing lists.
- Daily open, high, low, close, volume, splits and dividends for every stock bought, dead ones included. A stock that stops trading is sold at its last price, and what happened to it after is recorded.
- Raw files stay out of the repo.

## Fill and cost rules

- The signal is the filing becoming public, read from its acceptance time. Never the trade date and never the filing date on its own.
- Entry at the open of the first regular session that starts after the acceptance time. Sensitivity, reported: entry at the open one session later.
- Exit at the close after a fixed number of sessions, about one month. One holding length only.
- Each buy is the same share of the account. A cap on how many stocks are held at once. Cash earns nothing unless decision 7 has been answered by then.
- Cost per side depends on company size, in three bands. Marks are judged at the modeled cost. Break-even cost is reported beside it.
- A stock must clear a price floor and a daily trading floor on the day before entry, so nothing is bought that the account could not have bought.
- Long only. No leverage, no shorting, no options.

## Rules (4 trials)

| Id | Rule | Why it is here |
|---|---|---|
| B1 | Buy after any open-market buy by an officer or director | The plain version. The later evidence says this may be all there is |
| B2 | Buy only after a buy by an insider who is not routine, using the 2012 paper's split: routine means a trade in the same calendar month three years running | The paper's idea |
| B3 | Buy only after a routine buy | The paper's control. It should do worse than B2 if the idea holds |
| B4 | On each B1 entry day, buy a stock drawn at random from the same size band instead (seed 7) | A yardstick. It shows what small stocks did on those days with no insider signal |

Each rule is compared with holding the total market. B1, B2 and B3 are also reported against B4.

To settle before this plan is frozen: if a rule is added or dropped, the rule list, the trial count, the fixtures and the set of rules that mark 4 is worked out over are all rewritten here first. No rule is added or dropped to change how likely a tie is in mark 4.

## Slices

| Slice | Dates | Use |
|---|---|---|
| Warm-up | 2006-01-01 to 2008-12-31 | sorting insiders into routine and not routine only. No trades |
| Development | 2009-01-01 to 2018-12-31 | look freely |
| Held back | 2019-01-01 to 2026-06-30 | each frozen rule run once |
| After the designer's knowledge cutoff | 2026-07-01 to the last day in the file | reported |

The held-back years are not blind. Research has read two published studies of insider buys that cover 2018 to 2025 (`docs/research/26_insider_buying_evidence.md`). No rule of ours has been run on them.

## Pass marks

The five marks used in the other replays, numbers read from `config/thresholds.yaml`, with the methods of `AMENDMENT_2026-11-25_audit_fixes.md` and whatever the owner decides on mark 4. Shuffle for these rules: the entry days are kept and the stock is redrawn at random from the same size band, 1,000 times, seed 7. Trials counted in the deflated Sharpe ratio: every rule trial in the ledger on the day this is frozen, reruns included, plus these four.

Reported next to the marks: results year by year; the share of the profit that came from the best 10 stocks; how many stocks died while held and what they cost; results by size band.

A pass means "worth running in the practice account". It does not mean "makes money".

## Checks that must pass first

`fixtures2.py`; a bar check that knows the stock calendar; a hand-worked filing accepted after the close, to show entry lands on the next open and not earlier; a hand-worked stock that dies while held; a check that the count of filings and buys matches the SEC's own totals for a sample quarter; the routine sort reproduced by hand for three insiders.

## To settle before this is frozen

1. The holding length in sessions, the cap on positions and the share of the account per buy. Each needs a key.
2. The three size bands and the cost per side in each. Each needs a key. The one recent estimate read puts the middle spread for small companies near 1.3% (`docs/research/26_insider_buying_evidence.md`).
3. The price floor and the daily trading floor. Each needs a key.
4. Whether owners of more than 10% count as insiders here. The paper includes them. They are often funds, not people who run the company.
5. What "total market" is in the comparison, and the dividend treatment.
6. Whether the vendor's dead-stock coverage is complete enough. A coverage check against the SEC's list of companies comes first, and a shortfall is reported as a limit of the test, not hidden.
7. How ties in entry on the same day are ordered when the cap is reached.
8. The contact address for SEC requests, from the owner.
