# 150: Discovery sweeps with a sealed vault (design ruling by the lead agent)

Written 2026-11-26 06:07 MT by the lead agent. No price was read to write this page. It fixes how plans 69 and 70 must be built. Ledger rows 217 and 218, queue rows 111 and 112.

## Why this, and why now

- MEASURED: 44 scored tests and about 37 screens closed before prices, nearly all of them rules someone else published. Three passed, and `docs/research/149_what_the_passes_are_worth.md` shows the two US-reachable ones earn about $15 and $7 a year on $500.
- STATED, the lead agent's reading: a published rule is known to everyone, so what is left of it is small. The next honest source of rules is our own data. The danger is the opposite one: search enough rules and some will look good by luck (`docs/research/140_false_pass_audit.md`).
- So the search is allowed, but only behind a vault: a block of later dates no rule, no script and no person reads until a small number of finalists has been named, and then once.

## The two sweeps

- Plan 69: US stocks and exchange-traded funds, intraday and overnight, on Alpaca SIP bars from 2016. Not closed-end funds and nothing in the scope of plans 63 or 64.
- Plan 70: coins that can be traded both ways from the US, on hourly bars already held. The judged cost is the US futures route in `docs/research/120_round_31_cfm_futures_cost_rescreen.md`; the US spot cost in `docs/research/98_kraken_and_coinbase_short_access.md` is shown beside it.

## Fixed before any bar is read

1. The list of instruments, chosen by a rule that reads no price and uses a dated public list from before the first search date, so that nothing is picked because it survived.
2. The rule grid: at most 300 fully written rules per sweep (signal, entry print, exit print, side, holding time), in one file whose checksum goes in the ledger. Every family needs a stated reason someone is forced to trade or is paid to wait, with a source. Families already scored in this repo are left out.
3. Costs per trade, from measured figures on file (`docs/research/136_measured_stock_trading_costs.md` for stocks), not from a guess.
4. The dates. Stocks: search 2016-01-04 to 2021-12-31, vault 2022-01-03 to 2026-10-30. Coins: search 2020-01-01 to 2023-12-31, vault 2024-01-01 to 2026-10-31.
5. The vault. For stocks the vault bars are not collected until the vault step. For coins the files on disk already hold those dates, so the search script must cut by date before any other work and an auditor must confirm it does.

## The bar a rule must clear in the search to become a finalist

- At least 200 trades.
- Net mean above zero at the judged cost, with a t value of 3.5 or more, clustered by day. (With 300 rules, luck alone reaches about 3.4.)
- Positive in each half of the search dates, t of 1.5 or more in each.
- Still positive without its best 1% of trades.
- Worth having: at least 12% a year on $500 at 1x, simple, net.
- At most 3 finalists per sweep, highest t first. Two rules whose trade returns move together by more than 0.7 count as one.
- No finalist: the sweep closes and its vault stays shut for a later, differently built grid.

## The vault mark, fixed now

Each finalist is run on the vault dates once.

- Net mean above zero and clustered t of 2.4 or more.
- Still positive without its best 1% of trades.
- Positive in at least 3 of the 5 vault years.
- At least 8% a year on $500 at 1x, simple, net.
- Before the vault is opened, the chance of passing is worked out from the search noise and half the search mean. Under 33%, the finalist is not carried.

A rule that passes the vault goes to a forward practice card. It does not go to real money.

## What this does not fix

- UNKNOWN: whether anything clears the search bar. A sweep that closes with no finalist is a result, and it will be written up as one.
- STATED: dates after 2022 have been read by earlier tests of single instruments (for example the long Treasury fund at month-end). The vault is clean for a rule only if that rule's family was not scored on those dates before, which is why scored families are left out of the grid.

## Amendment 1, 2026-11-26 06:09 MT, by the lead agent, before any bar was read

Raised by the plan 70 drafter. Nothing had been run.

1. Drift is taken out, both sweeps. Every t value in the finalist bar and in the vault mark is worked out on the rule's net return minus a matched baseline: the plain average return of the same instrument over the same entry and exit clock prints on all dates in the same block, with no cost charged to the baseline. The plain net mean must also be above zero and meet the yearly line. Reason: a rule that is simply in a rising market often would otherwise clear the bar without knowing anything.
2. Coin list. No dated public list of US two-way coins exists from before 2020, because the US route only opened in 2025. The plan 70 list is therefore the November 2026 list in doc 98, stated as a list chosen with hindsight. Coins on it are survivors, which flatters buying and hurts shorting. The matched baseline in point 1 removes the first-order part of that. The rest is UNKNOWN and is written next to any result.
3. Funding on coins. The US futures route charges or pays funding every hour, so no holding time avoids it. The test charges a fixed adverse amount per hour held, set in the plan from a source before any return is worked out, never zero and never taken from an offshore venue. A coin finalist that passes the vault must then pass a check on real prints and funding of the same contract before it goes to a practice card.
4. Vault years for coins. The coin vault is 2024-01-01 to 2026-10-31, which is not five years. For plan 70 the mark reads: positive in at least 4 of its 6 half-years (the last one ends 2026-10-31). The stock mark stays at 3 of 5 years.

