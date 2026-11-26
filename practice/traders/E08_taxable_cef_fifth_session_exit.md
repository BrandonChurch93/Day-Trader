# E08 taxable_cef_fifth_session_exit

Status: forward practice card for queue row 103, written 2026-11-26. Pretend money only: no orders, no broker link, no live capital. It takes the one lead from Replay 53 (plan 53) and logs it on dates nobody has seen. There is no ledger number, because forward cards do not take one.

## Why this card exists

- MEASURED (Replay 53, the lead's report): the judged rule did not pass. It met 5 of 7 marks and was positive in 6 of 10 years.
- MEASURED, shown only: the same five funds sold at the fifth January session close were positive in 10 of 10 years.
- That line was seen after the fact. It counts for nothing until it is tested on new dates. This card is that test, one January at a time.

## What one January can show

- One January is one observation. This card cannot pass or fail a rule. It only adds year 11 to the ten already seen.
- The ten seen years cannot count toward the test, because they are where the idea came from. Only forward years count.
- MEASURED from the Replay 53 shown-only fifth-session table (ten yearly results, read once from the private results file): the portfolio mean was +1.80% with a yearly standard deviation of 1.79%. Portfolio minus PCEF had a mean of +0.77% with a standard deviation of 1.24%, and was ahead in 8 of 10 years.
- STATED, doc 117 screen ([`docs/research/117_power_screen_before_data.md`](../../docs/research/117_power_screen_before_data.md)): years × (edge ÷ noise)² ≈ 4 for 50% power and ≈ 8 for 80%.
- Portfolio above zero, at the shown spread: about 4 forward years for 50% power, 8 for 80%.
- Portfolio above PCEF, at the shown spread: 11 forward years for 50% power, 21 for 80%. This is the binding count, because the house marks require beating PCEF, not only being above zero.
- The shown mean was picked after looking, so it is probably too high. If the true edge is half the shown one, the counts are four times larger: 16 and 32 years above zero, 42 and 83 years above PCEF.
- So E08 by itself can never clear the screen. At one January a year it would take a decade or more. Read its result as one more year, not as a verdict.

## Roster: universe and ranking exactly as plan 53

- Source: the PCEF holdings schedule in the SEC filings of trust CIK 0001378872, series S000027370, using the forms in `replay_53_plan` (N-Q, public fiscal quarter-end NPORT-P, N-CSR, N-CSRS and their amendments).
- Cutoff: the filing's report period and its public date must both fall strictly before 2026-12-01. Rank eligible filings by latest report period, then by latest EDGAR acceptance time. UNKNOWN until built: which filing that is.
- Membership, the municipal name screen, the Replay 48 muni anti-join (2026 ticker or CIK in `/home/user/workspace/rig/inventories/row86_muni_cef_roster.csv`), the five exclusion reasons and the file layout are exactly the plan 53 rules in [`research_rig/PREREG_53_taxable_cef_tax_loss.md`](../../research_rig/PREREG_53_taxable_cef_tax_loss.md). The identity rules come from both amendments ([`research_rig/AMENDMENT_53_CASH.md`](../../research_rig/AMENDMENT_53_CASH.md) and [`research_rig/AMENDMENT_53_JUMPS.md`](../../research_rig/AMENDMENT_53_JUMPS.md)).
- Files: `roster.csv` and `roster_exclusions.csv` for turn year 2026, off repo in `/home/user/workspace/rig/data/forward_e08_inputs/` (folder 0700, files 0600), with an independent review as in plan 53. No price is read to build or review them.
- Freeze: `freeze-list` checks structure, the cutoff, one filing, holding ID continuity, the name screen and the anti-join, then writes both SHA-256 values to the logs. It closes at the 09:30 New York open of the formation session, 2026-12-30. That is stricter than "before the last December session": the list is fixed before the ranking close exists. Nothing is added after the freeze.

## Dates

All dates come from the pinned NYSE calendar in the logger (2026 matches `research_rig/calendar_25.json`; 2027 from the [NYSE holiday calendar](https://ir.theice.com/press/news/details/2024/NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx)). None of these sessions is an early close.

| Step | Session | Clock |
|---|---|---|
| Ranking base (anchor) | Fri 2026-01-02 | close |
| Formation | Wed 2026-12-30 | close |
| Pretend entry | Thu 2026-12-31 | close |
| Claim exit: fifth January session | Fri 2027-01-08 | close |
| Reference exit: last January session | Fri 2027-01-29 | close |

## Rules, fixed now

- Eligible: a usable raw SIP daily bar on every session from the anchor through entry. A zero-volume bar counts as missing. There can be no split from the anchor through entry, whether from a vendor split record or from a step between the raw and split-adjusted closes.
- Jumps: any consecutive close ratio outside 1/1.4 to 1.4 with no split needs exactly one clearance per pair, `GENUINE_MOVE` or `IDENTITY_BREAK`, with an evidence link. An identity break on or before entry removes that fund for this turn. A PCEF jump refuses the turn.
- Rank: price return from the anchor close to the formation close, lowest first, with ties broken alphabetically by ticker.
- Buy: walk down the ranked list and buy the worst five for which one whole share fits $100 after the entry cost. Use the largest whole-share count, leave leftover cash idle and charge zero commission. If fewer than five fit, the turn refuses.
- PCEF: one $500 whole-share sleeve on the same clocks, costs and cash rule. Refuse if PCEF misses a session or splits, or if one share does not fit.
- Two exits for the same five funds and the same PCEF sleeve: the fifth January session close is the card's claim, and the last January close is the reference. The share counts set at entry do not change between them.
- Costs, as in plan 53, use the frozen engine `research_rig/common_48.py`. The engine takes SIP quotes from 15:53:00 to 15:59:00 New York time and measures the duration-weighted median relative spread from 15:54:00 to 15:59:00, with a 60-second expiry and at least 180 valid seconds.
- The side charge is half the spread plus 5 bp. Short coverage uses a 50 bp half-spread proxy. The exit side uses the larger of the entry and exit half-spreads plus 5 bp.
- Missing exit: a held fund with no usable bar on the exit day is valued at its last usable close on or before the exit. It is charged the larger of its entry half-spread and 50 bp, plus 5 bp, and it is kept and counted.
- Cash: credited per share held when the ex-date is after 2026-12-31 and on or before the exit, or the last usable close. Sources are issuer pages, issuer wire, SEC filings or exchange records only, each with its link: no aggregators, no vendor cash, no Yahoo, no Nasdaq pages and no going around a site block.
- Each held fund and PCEF gets a status of `documented`, `none`, `partial` or `unresolved`. PCEF must be `documented` or `none`. Unresolved cash gets zero credit and is counted as a gap. The month exit must repeat every cash event credited at the fifth-session exit.
- Splits after entry: every vendor split record for a held fund must be matched by a dated issuer, SEC or exchange record with its new-per-old ratio. It multiplies the share count from its ex-date, including cash on that date. Any PCEF split refuses the turn.
- Logged at each exit: the five-fund net return on $500, PCEF on $500, the difference, and the same three with all cash set to zero, each MEASURED. Counts of missing exits, proxy sides and cash gaps go with them.
- Not logged: the roster equal-weight comparison, because primary cash for about a hundred funds cannot be documented in the window.

## Commands and when they are due

Run each command from a clean worktree at the card's commit, using `pplx credentials run <data handle> -- python3 practice/forward_e08.py <command>` (the same saved data credential and host as E07). Each command refuses outside its window and refuses a second write, and a refusal writes nothing. Times are New York, then Mountain.

| Command | Opens | Closes (refuses from) |
|---|---|---|
| `freeze-list --roster ... --exclusions ...` | 2026-12-01 00:00 ET (2026-11-30 22:00 MT) | 2026-12-30 09:30 ET (07:30 MT) |
| `record-entry [--clear ...]` | 2026-12-31 16:20 ET (14:20 MT) | 2027-01-04 09:30 ET (07:30 MT) |
| `record-exit5 --status ... [--cash ...] [--split ...]` | 2027-01-08 16:20 ET (14:20 MT) | 2027-01-16 00:00 ET (2027-01-15 22:00 MT) |
| `record-exit-month --status ... [--cash ...] [--split ...]` | 2027-01-29 16:20 ET (14:20 MT) | 2027-02-13 00:00 ET (2027-02-12 22:00 MT) |

`plan` and `alive` can run at any time. `alive` prints only which records exist and which windows are open.

## Private and public logs

- Private: raw bar, split and quote pages, closes, share counts, picks, ranks and cash amounts go in `/home/user/workspace/rig/data/forward_e08` (folder 0700, files 0600) as a hash-chained `log.jsonl` with gzip packets. They are never committed.
- Public: `practice/forward/E08_log.json` holds dates, counts, private packet SHA-256 values and the chain hash, plus the return percentages at each exit. No ticker of a pick, no price and no share count appear in it. It is created at `freeze-list` and gets its INDEX row then.
- Checks: `python3 practice/test_forward_e08.py` uses a pretend data source, made-up funds and a temporary folder. It makes no requests.

## Limits

- This is one turn, one roster snapshot and one January, with the close as a fill proxy.
- A broad closed-end fund rally in early January would look the same as a tax-loss rebound.
- PCEF is linked to the roster source, so it is not an independent yardstick.
- Missing primary cash lowers the five funds' result and can only make the claim harder to meet.
