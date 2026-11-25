# A03 trend_leaders

Status: builder settings, 2026-11-25. Untested. Market: US ETFs and large stocks. Holding time: 2 to 12 weeks.

## What it tries to do

It holds the strongest sector funds while the whole market is in an uptrend, and holds cash when it is not. The model does not pick the funds: it can only skip a pick, with a reason, when news shows a clear event risk.

## Why this might work

- MEASURED, not credited: in the corrected run of replay 05, the rule I2 (hold the three strongest of twelve industry groups when the market is above its ten-month average) grew nearly as much as holding with a much smaller largest drop. Research recommends it is not credited, it was tested on an index that cannot be bought, and it carries three cautions (`docs/research/22_replay_05_stock_trend.md`, `docs/STATUS.md`).
- MEASURED: live trend funds gave up growth for smaller drops ([PTLC prospectus](https://www.sec.gov/Archives/edgar/data/1616668/000089418925006695/pacertrendpilotuslargecape.htm), via `docs/research/25_what_the_evidence_supports.md`).
- MEASURED: winners kept winning more after rising markets than after falling ones, before costs ([Cooper, Gutierrez and Hameed](https://web2-bschool.nus.edu.sg/wp-content/uploads/media_rp/publications/96eJe1370224435.pdf), via document 17).
- UNKNOWN: whether a model skipping picks on news adds anything. Our pilot suggests a model mostly acts like the rule (`docs/research/14_ai_calls_pilot_02.md`).
- Honest summary: the best-supported idea on this list, and the support says "smaller drops, less growth", not "more money". Its main use is to show whether the AI adds anything over the fixed rule T1 (control C04).

## What it looks at each time it wakes

- Its holdings and cash.
- Daily bars for a fixed list of sector funds from one fund family and a total market fund, written into the ledger row before it runs.
- Alpaca news headlines for each held or candidate fund's largest holdings.
- Web search, only for a candidate: "[sector] news this week", and the dates of major scheduled events (central bank meetings, large company reports in that sector).

## How it decides to buy

1. Market filter: the total market fund's month-end price is above the average of its last 10 month-end prices. If not, hold cash and stop here.
2. Rank the sector funds by 12-month return, worked out by the plain feed numbers the model is shown.
3. The top three are the picks, one third each of the invested share.
4. The model may skip one pick only if it writes a specific, confirmed event in the next 10 trading days that could hit that sector hard. The skipped third stays in cash. Confirmation needs two sources (`AGENTS.md`, "How a trader behaves", item 4).
5. A held fund is switched only when it leaves the top three at a month-end check.

## How big

- Up to 90% of its budget invested, in at most 3 funds, one third each. No single stocks in the first trial.

## How it gets out

- Stop price: 12% below entry for each fund, as a disaster line only.
- Target price: none.
- Exit-by time: the next month-end check, at 15:45 Eastern on the last market day of the month, where it is kept or switched by the rules above.
- If the market filter turns off at a month-end check, all three are sold.

## What it never does

- Picks funds by its own judgment in place of the ranking.
- Trades between month-end checks, except the stop and a news skip on a new buy.
- Buys leveraged or inverse funds.

## When it wakes

- Once a day at 15:30 Eastern on market days to check news on holdings. Buys and switches only at 15:30 Eastern on the last market day of the month.

## What would make us drop it

- The rules in `practice/traders/ROSTER.md`, "How we judge", with C04 (rule T1) as its comparator.
- Also: if over its trial it is not ahead of a plain copy of the ranking with no skips (worked out by plain code from the same prices), the model is adding nothing and the method is reduced to a fixed rule for replay 06.
