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
