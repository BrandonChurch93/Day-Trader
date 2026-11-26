# Plan 74: swing cards A and B, judged per signal

- STATED: Queue rows 126 and 127. Drafted 2026-11-26 12:12 MST on main 93aa70c. Status DRAFT. This is a historical test with pretend cash. It sends no orders.
- STATED: The cards come from [doc 169](../docs/research/169_what_successful_small_account_traders_look_for.md), Card A and Card B. The owner's direction ([DECISIONS](../docs/DECISIONS.md), 2026-11-26): holds of a day to a couple of months; "quick" is a few weeks.
- STATED: No market data endpoint was called for this draft. No price, bar, return or vendor file was opened. The power table below uses made-up numbers only.
- STATED: All dates, costs and marks live in one block, `replay_74_plan`, in config/thresholds.yaml. A number in this plan names its key in that block, written as "key marks.min_t" and so on.
- STATED: The work has four gates, (a) to (d). Each is a hard gate. Nothing in a later gate starts until the lead agent signs the earlier one. This draft delivers gate (a) as a written check and gate (b) as a run on made-up data. Gates (c) and (d) are designs only.

## The lead agent's rulings, written in

- STATED, ruling 1: The judged unit is the signal, not the $500 book. Every qualifying symbol-day signal is entered at the next regular open and exited by its card's own exit rules. Its net return is compared with the same-days return of IWM (key benchmark, both cards), and the t statistic clusters by entry day (key cluster). The four-name $500 whole-share book from doc 169 is computed and shown only. It cannot pass or fail the card.
- STATED, ruling 2: Card A primary is leader near high, tight range, breakout on volume, a dated earnings release, the market switch, the initial stop at the signal-day low, the 10-session EMA exit and the 40-session limit, with no add. The 20% revenue-growth parse is not in the primary. Shown only: without the market switch; without the earnings requirement; with the one add; and, added later by the lead agent, the 52-week-high arm below. Card B primary is Gold and Revival pooled, as written in doc 169. Shown only: Gold alone; Revival alone.
- STATED, ruling 3: Design years 2017-01-03 to 2021-12-31 (keys design_first, design_last), warm-up from 2016-01-04 (key warmup_first). Held-back years 2022-01-03 to 2025-12-31 (keys heldback_first, heldback_last), opened once per card and only if the card passes on the design years. The scorer has no held-back mode until the lead agent writes a separate go. 2026 is untouched (key untouched_year).
- STATED, ruling 4: Costs are fixed now. See "Costs" below.
- STATED, ruling 5: Pass marks are fixed now. See "Pass marks" below.
- STATED, ruling 6: Order of work (a) data feasibility, (b) power on made-up data, (c) count only, (d) one scoring run on the design years.
- STATED, ruling 7: No trader sees the future. Every input is as known at the signal close. No vendor back-adjusted price is used for the $1, $5 or other price gates. Ticker reuse is handled by a permanent ID. A delisted holding is never dropped.

## Card A, primary

- STATED: Rules are doc 169 lines 105 to 108, with the changes in ruling 2. The only changes are listed here. Everything else is as doc 169 writes it.
- STATED: Leader screen at close t: raw close $5 to $75; 20-session mean of raw close times raw volume, ending t−1, at least $5 million; market cap $300 million to $10 billion at t−1; 63-session split-converted close return ending t−1 in the top 10% of eligible names (ceiling of 10% of the count, permanent ID breaks ties); t−1 close at least 95% of the 252-session high ending t−1; five-session range through t−1 over its mean close at most 75% of the same ratio for the five sessions before.
- STATED: Market cap uses the latest dated share count filed with the SEC on or before t−1 (see gate (a)), converted to the traded share basis with the split register, times the raw t−1 close. Issuers with more than one listed common class are left out of both cards. This is a rule fixed without prices.
- STATED: Earnings: the issuer's first 8-K with Item 2.02 for the quarter, by SEC acceptance time, accepted after the close five sessions before t and no later than the close of t. An 8-K accepted after 16:00 ET on t counts for t+1, not t. No acceptance time means no signal. The revenue parse is dropped from the primary.
- STATED: Breakout at t: t close strictly above the highest high of the prior 10 sessions, no more than 3% above it, and t volume at least 1.5 times its prior 20-session mean.
- STATED: Market switch at t: QQQ close above its 20-session EMA and IWM close above its 50-session SMA. The EMA seed is the first full 20-session simple average. If either is off, no new signal that day, and every open signal exits at the next open.
- STATED: Entry: next regular open, only if the raw open is strictly above the greater of the old pivot and the t low, and at most 1.005 times the t close. Refuse if the worst allowed open is more than 3% above the stop, as a share of entry. A refused or skipped signal is counted, not scored, and not replaced.
- STATED: Exit, whichever comes first: the fixed stop at the low of t; the market switch turning off; the first close below the stock's 10-session EMA (simple-average seed); the 40th trade-session close including the entry day. Close-based exits fill at the next regular open. A stop already in force sells at the open if the open is at or below the stop, else at the stop level if the day's low reaches it, then the stop overshoot and the cost are applied.
- STATED: No add in the primary. The one add of doc 169 line 108 is a shown-only arm.

## Card A, the 52-week-high arm (shown only)

- STATED: Added 2026-11-26 by the lead agent from doc 171, docs/research/171_idea_round_50_swing_horizon.md on main 0a2f64c, family 3 and its Second check, which ranks "52-week high and relative strength with a market filter and a hard stop" second. That family is Card A without the earnings requirement, which is already the ruled shown-only arm "without the earnings requirement".
- STATED: One more shown-only arm: the same Card A entry without the earnings requirement, with two changes only. The market filter is SPY's close above its 200-session simple average at t, in place of the QQQ and IWM switch; if it is off, no new signal and every open signal exits at the next open. The stop is fixed at 8% below the actual entry open (key arm_52w.stop_share), in place of the signal-day low. Everything else, including the 10-session EMA exit, the 40-session limit, the IWM comparison, the costs and the overshoot, is unchanged.
- INFERENCE, flagged: The 3% refusal rule (worst open more than 3% above the stop) is tied to the signal-day-low stop. With a fixed 8% stop it would refuse every signal, so this arm drops that refusal and keeps the entry window. This is the drafter's reading, not a ruling.
- STATED: The outside result for this family, AlpaTrade +30.4% a year from 2022 to 2026 as doc 171 line 214 reports it, ran on today's index members, so it has survivorship bias. It is not evidence for this plan. That is why gate (a), on dead names, decides whether this plan can run at all.
- STATED: This arm is shown only. It cannot pass or fail Card A, and it has no held-back opening of its own.
- INFERENCE: The drafter's own rule, flagged for the lead: a symbol that signals again while an earlier signal on it is still held does not start a second signal. Without this, one stock in a run could count many times and the signals would not be independent.

## Card B, primary

- STATED: Rules are doc 169 lines 114 to 117, unchanged, Gold and Revival pooled. If both trigger, the signal is tagged Gold.
- STATED: Scan at raw close t: $0.50 to $10; 20-session mean split-basis share volume ending t−1 at least 200,000; 20-session mean raw dollar turnover at least $500,000. No split effective in the prior 126 sessions including t, and none announced as of t for the next open.
- STATED: Base, pivot, Gold (126 prior raw closes under $1, t close above both $1 and the pivot) and Revival (t−21 close at least 30% below t−81 close, t close above the pivot) as doc 169 line 115. Close at most 5% above the line, volume at least twice its prior 20-session mean.
- STATED: Entry next open strictly above the line and at most 1.02 times the t close. Stop 0.98 times the line. Refuse if the worst allowed open is more than 8% above the stop.
- STATED: Exit on the stop, the first close below the line or the 13-session EMA, or the 10th trade-session close, at the next open. The half sale at $2 (Gold) or at entry plus twice the initial risk (Revival) is kept. The signal's return is the share-weighted return of its two halves. No retry for ten sessions after any exit on that symbol.
- STATED: The $1 test uses raw closes only. A $1 cross caused by a reverse split is not a Gold signal, as doc 169 says.

## How one signal is scored

- STATED: Gross return of a signal: exit value over entry price, both in the same share units. If a split falls between entry and exit, the exit value is converted to entry share units with the ratio from the split register. No dividend, spin-off value or cash-in-lieu is credited.
- STATED: Net return: buy at entry price times (1 + cost), sell at exit price times (1 − cost), with the card's cost per side (key costs_bp_per_side). On a stop exit filled intraday at the stop level, the exit price is first lowered by the stop overshoot (key stop_overshoot_share_of_risk) times (entry − stop). A stop that fills at a gapped open takes the open, with no extra overshoot.
- STATED: Market fund return, no cost: IWM from the same entry open to the same exit print. For an open exit that is IWM's open on the exit day. For an intraday stop exit, the exit print for IWM is its close on the stop day. This is an approximation, stated so it is not chosen later.
- STATED: Excess return = net return of the signal minus the IWM return over the same days.
- STATED: A delisted holding is never dropped. If the bars of a held signal end, it exits at its last regular close (key delisted_last_close_share, primary 1.0). Shown only: half of that close (shown 0.5). A cash merger with a stated price in the corporate actions feed, if one exists, is shown as a third line. Count such exits separately.
- STATED: Clustered t: on design-year signals, demean the excess returns, sum them within each entry day, square and add the day totals, multiply by G/(G−1) where G is the number of entry days, take the square root and divide by the signal count. t is the mean excess over that error. A zero or undefined error does not pass. Shown only, the same t clustered by entry week and by entry month (key cluster_shown).

## Costs

- STATED, Card A 10 bp a side (key costs_bp_per_side.A). [Doc 136](../docs/research/136_measured_stock_trading_costs.md) line 14: pooled 90th percentile half-spread, first 30 minutes, 10.055 bp. Line 20: the 38 single stocks, first 30 minutes, median 3.787 bp. 10 bp is about the pooled p90 for an opening fill.
- STATED, Card A stop overshoot 0.1332 of the stop distance (key stop_overshoot_share_of_risk.A). [Doc 66](../docs/research/66_measure_15_breakout_fills.md) line 7: "mean stop-exit slippage 0.1332 (n 840), odd lots left out". Shown only: 0.2134 with odd lots counted, doc 66 line 13 (key stop_overshoot_shown.A_odd_lots_in).
- STATED, Card B 50 bp a side (key costs_bp_per_side.B). Doc 136 has no figure for names under $10. Its 38 single stocks are large names (line 20). So 50 bp is an assumption, not a measurement. Shown only: 100 bp a side (key cost_shown_bp_per_side.B).
- STATED: Doc 66's price group $5 to $10 had entry mean 11.42 bp (n 62) and stop-exit mean 16.52 bp (n 52). The group under $5 had n 2 (stop exit mean 136.13 bp), too thin to use. These are intraday breakout fills on stocks in play, not opening fills on sub-$10 names.
- INFERENCE: Card B as written has no stop overshoot. A shown-only line applies doc 66's 0.1332 to Card B stop exits too (key stop_overshoot_shown.B).

## Pass marks

- STATED, all on design-year signals, each card on its own. Every mark must hold.
- STATED: mean net excess per signal above zero (key marks.mean_above) and at least 1.0% (key marks.mean_floor).
- STATED: day-clustered t at least 3.0 (key marks.min_t).
- STATED: mean excess positive in at least 4 of the 5 design years by entry year (keys marks.years_positive, marks.years).
- STATED: mean excess still positive with the top 1% of signals removed, that is the highest ceil(0.01 × n) excess returns (key marks.trim_top_share).
- STATED: at least 150 signals on at least 100 entry days (keys marks.min_signals, marks.min_entry_days). Fewer is "too thin", not a fail of the idea and not a pass.
- STATED, held-back mark, used only after a separate go: same sign as the design mean and day-clustered t at least 2.0 (keys heldback_marks.same_sign, heldback_marks.min_t).
- STATED: Shown-only arms, the $500 book and the week and month t never change a verdict.

## Gate (a): data feasibility, no prices

### Five-line verdict

- UNKNOWN: Whether Alpaca SIP daily bars cover delisted symbols. The docs have no sentence on it. One repo sample says yes for 9 of 9 names. A counts-only probe (below) decides.
- INFERENCE: A free point-in-time list of US listed common shares with dead names can be built from SEC filings only (10-K/10-Q filers, 8-A12B and Form 25 dates), but it is a proxy with known gaps before EDGAR and for ticker mapping before 2019.
- STATED: Split and delisting dates can come from Alpaca corporate actions (doc 118 MEASURED 830 forward splits 2016 to 2025 there) plus SEC Form 25. Dated share counts can come from SEC XBRL cover-page share counts by filed date. Both need a probe before use.
- INFERENCE: Design years plus warm-up are about 10.6 million daily rows at most, about 1,100 to 10,600 Alpaca requests (6 to 55 minutes at 200 a minute), and about 0.4 GiB compressed. That fits the 1.5 GiB cap without shrinking the universe.
- STATED: Verdict: feasible on paper, with two named probes to run first (delisted coverage, ticker-to-CIK mapping). No collector is written until the lead agent signs this gate.

### Where the universe comes from

- STATED: [SEC Financial Statement Data Sets](https://www.sec.gov/data/financial-statement-data-sets) are quarterly files of every XBRL 10-K and 10-Q filing. Their SUB table lists each filing's CIK, form and filed date, and dead filers stay in old quarters.
- INFERENCE, the proposed rule fixed without prices: a CIK is in the universe on day t if it has filed a 10-K or 10-Q in the prior 15 months, has an 8-A12B registration on or before t, has no Form 25 or 25-NSE effective on or before t, is not a blank check company (SIC 6770), and has one listed common class. Foreign private issuers (20-F, 40-F) and funds are out because they do not file 10-K or 10-Q.
- UNKNOWN: Listings older than EDGAR have no 8-A on EDGAR. For them, the start date is the earliest 10-K/10-Q in the files. This is a gap to state, not to fill by guessing.
- INFERENCE: Ticker per CIK per interval: the cover-page tag dei:TradingSymbol (tagged from 2019) or, before 2019, the prefix of the XBRL instance file name. This needs a probe. SEC's live ticker table does not cover dead names; doc 118 found 139 historical or delisted tickers that do not map through it.
- STATED: Join to Alpaca by CUSIP where the corporate actions feed gives one, and by symbol with `asof` set per listing interval. The permanent ID is the SEC CIK plus the class, never the ticker.
- STATED: Paid point-in-time lists exist ([Norgate](https://norgatedata.com/data-content-tables.php), CRSP). They are not ours and are not proposed.

### Alpaca daily bars, what the docs say

- STATED, [stock bars reference](https://docs.alpaca.markets/us/reference/stockbars), on `asof`: "This date is used to identify the underlying entity of the provided symbol(s), so that name changes for this entity can be found. Data for past symbol(s) is returned if the query date range spans the name change." And: "The special value of "-" means symbol mapping is skipped. Data is returned based on the symbol alone without looking up previous names."
- INFERENCE: With symbol mapping skipped, a reused ticker could join two different firms. The collector must query each listing interval with its own `asof` and must store the CIK with every row.
- STATED, same page, on `limit`: "The limit applies to the total number of data points, not per symbol!" The page states no maximum, so the maximum is UNKNOWN.
- STATED, same page, on adjustment: "`raw`: no adjustments", "Default: `raw`". Raw bars are what ruling 7 needs.
- STATED, [historical stock data page](https://docs.alpaca.markets/docs/historical-stock-data-1): SIP "covers all US exchanges".
- UNKNOWN: No sentence on either page says whether delisted symbols are covered.
- MEASURED, repo, queue row 66 (docs/QUEUE.md line 99): "9 of 9 sampled common shares that later delisted had positive-volume Alpaca SIP bars on every trading session in their sampled December." That row was held for lack of a free point-in-time small-share list, which this gate proposes.

### Splits, delistings, name changes

- STATED, [corporate actions reference](https://docs.alpaca.markets/us/reference/corporateactions-1): types include reverse_split, forward_split, name_change, worthless_removal, cash_merger and stock_merger; limit "1 to 1000". It warns: "Currently Alpaca has no guarantees on the creation time of corporate actions". The page states no history depth.
- MEASURED, repo, [doc 118](../docs/research/118_row97_forward_split_count_first_close.md): 830 forward splits from 2016 to 2025 from that feed, with CUSIP, ex date and ratios.
- INFERENCE: Because creation time is not guaranteed, a split is used only from its ex date, and a split "announced as of t" (Card B) is taken from the SEC filing or exchange notice date, not from the feed. Where no dated announcement is found, the split block falls back to the ex date, and the count is shown.
- STATED: Delisting dates come from Form 25 and 25-NSE in the SEC submissions JSON per CIK. The last bar date is shown beside it as a check, not used as the date.
- UNKNOWN, [assets reference](https://docs.alpaca.markets/us/reference/get-v2-assets-1): whether the asset `id` is permanent is not stated, and there is no sentence on delisted assets. The plan does not rely on it.

### Dated share counts

- INFERENCE: SEC XBRL company concept dei EntityCommonStockSharesOutstanding per CIK, using each value's filed date as the date it was known. Needs a probe: share of universe CIKs with at least one value per year.
- INFERENCE: A value dated before a later split is converted with the split register before it meets a raw price.

### Requests, time and disk

- INFERENCE: About 7,000 ever-listed CIKs in 2016 to 2021 times 1,511 sessions is at most about 10.6 million daily rows. IWM and QQQ add two symbols.
- INFERENCE: With 10,000 rows a request, about 1,100 to 1,200 requests; with 1,000, about 10,600. At 200 a minute (key alpaca_requests_per_minute), paced, that is about 6 to 55 minutes.
- INFERENCE: About 40 bytes a row compressed gives about 424 MB at worst. The cap is 1.5 GiB compressed (key disk_cap_gib_compressed). No shrink rule is needed. If the probe shows more, the fallback rule fixed without prices is to drop CIKs with no 8-A12B.
- INFERENCE: SEC side: about 7,000 submissions requests and about 7,000 company concept requests at 4 a second or fewer (key sec_requests_per_second), about one hour. Keep only 8-K Item 2.02, 8-A12B, Form 25 and share-count rows. Stream the data set zips (about 50 to 80 MB each) one at a time and keep only SUB. Each job stays under 500 MB (key job_cap_mb).
- STATED: Held-back years are not pulled at all in this plan.

### Named probes for the custodian

- STATED: Probe P1, delisted coverage. Take the delisted CIKs from Form 25 filings in 2016 to 2021. For each, request daily bars for its last listed month with `asof` set inside its listing interval. Print counts only: names asked, names with any bar, names with bars on every session. No prices, no volumes are returned or saved. The names used are not chosen by any price.
- STATED: Probe P2, ticker mapping. For a fixed list of CIKs, the first 200 by CIK number that filed a 10-K in 2017, print counts only: CIKs with a ticker from the cover tag, from the file name, both agreeing, and none.
- STATED: Probe P3, share counts. For the same 200 CIKs, count how many have a dated cover-page share count in each design year.

## Gate (b): power on made-up returns

- STATED: research_rig/power_74.py reads its settings from `replay_74_plan` (key power) and opens no other file. Each made-up world spreads n signals over five years at 1.5 signals per entry day (key power.signals_per_day). An excess return is the mean plus a day shock carrying 10% of the variance (key power.day_share) plus its own shock; both are Student t with 3 degrees of freedom. Every pass mark above is applied. Seed 740001 (key power.seed), 2,000 worlds per cell (key power.draws).
- INFERENCE: The noise SDs per signal (key power.noise_sd) are guesses: 12% and 18% for a Card A hold of up to 40 sessions, 20% and 30% for Card B's sub-$10 names over up to 10 sessions. They are not measured from any price.
- INFERENCE: The model treats signals on different days as independent. Real 40-session holds overlap, so real power is lower than shown.

Printed table, pasted as the script printed it:

| Card | Noise SD per signal | True mean excess | Doc 117 count, 80% at t 2 | Smallest count, 80% power, all marks | Smallest count, 80%, without the 1.0% floor | Power at 150 / 500 / 1,000 / 2,000 / 4,000 signals, all marks |
|---|---:|---:|---:|---:|---:|---|
| A | 12% | +1.0% | 1,152 | none up to 16,000 (best 51%) | 3,000 | 3% / 13% / 35% / 50% / 48% |
| A | 12% | +2.0% | 288 | 750 | 750 | 20% / 75% / 97% / 100% / 100% |
| A | 18% | +1.0% | 2,592 | none up to 16,000 (best 51%) | 6,000 | 2% / 4% / 11% / 28% / 50% |
| A | 18% | +2.0% | 648 | 1,500 | 1,500 | 5% / 32% / 67% / 96% / 100% |
| B | 20% | +1.0% | 3,200 | none up to 16,000 (best 51%) | 8,000 | 1% / 3% / 7% / 23% / 48% |
| B | 20% | +2.0% | 800 | 2,000 | 2,000 | 5% / 23% / 54% / 90% / 100% |
| B | 30% | +1.0% | 7,200 | none up to 16,000 (best 28%) | none up to 16,000 | 0% / 1% / 2% / 7% / 16% |
| B | 30% | +2.0% | 1,800 | 4,000 | 4,000 | 2% / 7% / 18% / 48% / 86% |

MEASURED on made-up data: 2000 worlds per cell, seed 740001, 1.5 signals per entry day, day shock 10% of variance, Student t with 3 degrees of freedom.

### What the table says

- INFERENCE: With the 1.0% floor, a card whose true mean excess is +1.0% passes about half the time at most, at any count. The floor caps power at a true +1.0% near 50%.
- INFERENCE: At a true +2.0%, 80% power needs about 750 to 1,500 Card A signals and about 2,000 to 4,000 Card B signals.
- INFERENCE: Doc 169 guesses 3 to 25 funded starts a year for Card A and 5 to 25 for Card B in the $500 book. Raw signals will be more, but the gate (c) count decides. At the 150-signal floor, power is 20% or less in every cell.

## Gate (c): count only, design only

- STATED: A count script reads the custodied bars and filings and prints only counts: signals per design year and per gate, per card and per shown-only arm, plus refused and skipped entries, delisted-in-hold flags and entry days. Nothing else.
- STATED: The code cannot compute a return. The gate functions get a view of each symbol's bars that ends at the signal close t. The script has no exit logic, no entry-open check and no benchmark series. Its output schema is integers only, and its test fails if any float leaves the script.
- STATED: The entry-window check uses the next open, which is a price after t. So refused and skipped counts are not printed at gate (c); they wait for gate (d).
- STATED: If either card has fewer than the power need from gate (b) at +2.0%, the lead agent decides whether to stop that card before gate (d).

## Gate (d): one scoring run, design years

- STATED: One run per card, once, on design years only. It prints the marks, the shown-only arms and the $500 book. It has no held-back mode.
- STATED: The held-back years are opened once per card, only after a design pass and a separate written go.

## Identity register and custody

- STATED: Data root /home/user/workspace/rig/data/plan_74, outside the repo. No vendor data goes in the repo. Nothing is printed in bulk.
- STATED: identity.json, compiled before any bar is pulled, one row per permanent ID (CIK plus class): ticker intervals with `asof` dates, CUSIPs, 8-A12B date, Form 25 date, splits with ratio, ex date and announcement date, and share-count values with filed dates. It holds no price.
- STATED: As in Plan 69, the lead agent pins SHA-256s of the register and the code in a search approval file before collection and a score approval file before gate (d). Collection runs only under `pplx credentials run <handle>`. One heavy job at a time, nice -n 10, under 500 MB, and stop any write under 1.5 GiB free disk.

## Links opened for this draft

- [Alpaca stock bars reference](https://docs.alpaca.markets/us/reference/stockbars)
- [Alpaca historical stock data](https://docs.alpaca.markets/docs/historical-stock-data-1)
- [Alpaca corporate actions reference](https://docs.alpaca.markets/us/reference/corporateactions-1)
- [Alpaca assets reference](https://docs.alpaca.markets/us/reference/get-v2-assets-1)
- [SEC Financial Statement Data Sets](https://www.sec.gov/data/financial-statement-data-sets)
- [Norgate data content tables](https://norgatedata.com/data-content-tables.php)
