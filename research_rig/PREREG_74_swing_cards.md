# Plan 74: swing cards A and B, judged per signal

- STATED: Queue rows 126 and 127. Drafted 2026-11-26 12:12 MST on main 93aa70c, revised 2026-11-26 12:27 MST with main 0a2f64c merged in. Status DRAFT. This is a historical test with pretend cash. It sends no orders.
- STATED: The cards come from [doc 169](../docs/research/169_what_successful_small_account_traders_look_for.md), Card A and Card B. The owner's direction ([DECISIONS](../docs/DECISIONS.md), 2026-11-26): holds of a day to a couple of months; "quick" is a few weeks.
- STATED: No market data endpoint was called for this draft. No price, bar, return or vendor file was opened. The power table below uses made-up numbers only.
- STATED: All dates, costs and marks live in one block, `replay_74_plan`, in config/thresholds.yaml. A number in this plan names its key in that block, written as "key marks.min_t" and so on.
- STATED: Revised the same day, before any price, by the lead agent's second set of rulings (see "Rulings of the second round"). Where they change earlier text, the line says RULE CHANGE.
- STATED: The work has four gates, (a) to (d). Each is a hard gate. Nothing in a later gate starts until the lead agent signs the earlier one. This draft delivers gate (a) as a written check and gate (b) as a run on made-up data. Gates (c) and (d) are designs only.

## The lead agent's rulings, written in

- STATED, ruling 1: The judged unit is the signal, not the $500 book. Every qualifying symbol-day signal is entered at the next regular open and exited by its card's own exit rules. Its net return is compared with the same-days return of IWM (key benchmark, both cards), and the t statistic clusters by calendar month of entry (key cluster; RULE CHANGE, second round, was entry day). The four-name $500 whole-share book from doc 169 is computed and shown only. It cannot pass or fail the card.
- STATED, ruling 2: Card A primary is leader near high, tight range, breakout on volume, a dated earnings release, the market switch, the initial stop at the signal-day low, the 10-session EMA exit and the 40-session limit, with no add. The 20% revenue-growth parse is not in the primary. Shown only: without the market switch; without the earnings requirement; with the one add; and, added later by the lead agent, the 52-week-high arm below. Card B primary is Gold and Revival pooled, as written in doc 169. Shown only: Gold alone; Revival alone.
- STATED, ruling 3: Design years 2017-01-03 to 2021-12-31 (keys design_first, design_last), warm-up from 2016-01-04 (key warmup_first). Held-back years 2022-01-03 to 2025-12-31 (keys heldback_first, heldback_last), opened once per card and only if the card passes on the design years. The scorer has no held-back mode until the lead agent writes a separate go. 2026 is untouched (key untouched_year).
- STATED, ruling 4: Costs are fixed now. See "Costs" below.
- STATED, ruling 5: Pass marks are fixed now. See "Pass marks" below.
- STATED, ruling 6: Order of work (a) data feasibility, (b) power on made-up data, (c) count only, (d) one scoring run on the design years.
- STATED, ruling 7: No trader sees the future. Every input is as known at the signal close. No vendor back-adjusted price is used for the $1, $5 or other price gates. Ticker reuse is handled by a permanent ID. A delisted holding is never dropped.

## Rulings of the second round

- STATED: Made by the lead agent on 2026-11-26, before any price was read, in answer to the first draft's five questions.
- STATED, ruling 8, RULE CHANGE: the mean floor is 0.5%, not 1.0%. The test is sized to find a true edge of +2% a signal and will usually miss a true +1%.
- STATED, ruling 9, RULE CHANGE: the mark's t uses calendar-month clusters of entry dates, 60 in the design years. Day and week clustering are shown only. The power script was redone with overlapping holds and the month-clustered t.
- STATED, ruling 10: the Card A and Card B count branch in gate (c).
- STATED, ruling 11, RULE CHANGE: Card A main cost 25 bp a side, shown only at 10 and 50. Card B main 50, shown only 100. The doc 66 stop overshoot is in the main line on stop exits for both cards, as an assumption.
- STATED, ruling 12: accepted, no second signal on a symbol while an earlier one is held; the 8% stop arm drops the 3% refusal; a held name whose bars stop exits at its last close, with 0.5 times and zero shown, the count printed, and the 0.5 times line made binding if such cases exceed 1% of judged signals.
- STATED: Probes P1 to P3 now state their pacing, re-send rule, caps and user agent.

## Rulings of the third round

- STATED: Made by the lead agent on 2026-11-26, before any price was read.
- STATED, ruling 13, RULE CHANGE: the design-year mark is month-clustered t at least 2.0, not 3.0, with the reason written under "Pass marks". The other marks stay. A design pass alone supports no claim; the result line is "advance to held-back" or "closed".
- STATED, ruling 14: the common month share is a power-model assumption, not a mark. It is calibrated from published Kenneth French data dated before 2017, not from our test data. See gate (b).
- STATED, ruling 15: Card B gets a +4% mean row, and the plan says plainly what size of edge each card's test can and cannot find.
- STATED, ruling 16: the count stage prints a raw upper bound and a lower bound per card and arm. The branch uses the lower bound.
- STATED, ruling 17: one shown-only comparison at scoring against the equal-weighted same-days return of the screen-passing names without the trigger. Not a mark.

## Rulings of the fourth round

- STATED: Written by the lead agent on 2026-11-26 1:15 PM MT, before any price, in answer to the scorer builder's list of points the text left open. Where a ruling changes earlier text it says RULE CHANGE; the rest fix a reading that was not pinned. Where this section and an earlier line disagree, this section stands.
- STATED, ruling 18, the count stage: it prints only the three branch arms. The raw count takes every qualifying signal at its close t, before any next-open check; the day count is the number of distinct signal days t. A signal is dropped from the lower bound when its signal day is N sessions or fewer after an earlier counted signal on the same symbol, so the next one kept is at least N+1 sessions later. The sentence under gate (c) saying refused signals are in neither count is wrong and is withdrawn: they are in both, which is why gate (d) applies the 150-signal and 100-day marks again.
- STATED, ruling 19, RULE CHANGE: the Card B lower-bound gap is 20 sessions, not 10 (key count_branch.lower_bound_gap_sessions.B): the 10-session hold limit plus the 10-session wait after an exit. With 10 the figure was not a true lower bound. The need of 2,000 is unchanged.
- STATED, ruling 20, Card A screen: the names ranked for the top 10% are all names that pass the price, turnover and market-cap tests at t and have the 64 closes the return needs; the near-high and range tests are applied after the rank. The 63-session return is close at t−1 over close at t−64, minus one. Every look-back window must be complete on the exchange calendar: a symbol missing a bar on any scheduled session inside a window gives no signal that day. A symbol's EMA restarts from a fresh simple-average seed after a missed scheduled session. A missing QQQ or IWM bar means no new signal that day and the run prints the count of such days.
- STATED, ruling 21, filings and clocks: of several share counts filed on or before t−1, use the one with the latest acceptance time; on a tie, the later period of report, then the larger count. On a scheduled early-close day the earnings cutoff is that day's actual close, taken from the calendar file, not 16:00 ET. A split effective on the entry day is treated as known at close t and the entry is refused for both cards, counted and not scored.
- STATED, ruling 22, one position per symbol: while a signal is open on a symbol in a card, further qualifying signals on that symbol are counted as skipped and not scored. Card A has no wait: a symbol can signal again at the close of the day it was sold. Card B's ten-session wait starts at the final exit, the day the last share is sold; the first signal day allowed is the 11th session after it.
- STATED, ruling 23, Card B levels: Revival risk is the raw entry price minus the stop level, with no cost or overshoot in it. If a split falls inside a hold, the stop, the line and the Gold $2 target are converted by the register ratio so they stay the same in entry-share units. This holds for Card A's stop too.
- STATED, ruling 24, missing bars: the last-close exit is used when a held symbol has no bar on the next scheduled session and no later bar inside the delivered design files, whether or not the register documents a delisting; documented and undocumented cases are counted separately. When bars stop and later resume, a pending entry is refused, a pending exit fills at the open of the symbol's next bar, stop checks resume there, and the hold limit counts the symbol's own sessions with bars. The market fund is measured over the same dates.
- STATED, ruling 25, RULE CHANGE, the design fence: a design signal must have its signal day early enough that the entry day plus the card's hold limit ends on or before the last design day. With the limits of 40 and 10 sessions the last signal day is the 41st session before the end for Card A and the 11th for Card B (keys to be named design_last_signal_offset). The cut is by date, fixed before prices, and applies to the count stage too. No bar after the last design day is delivered to the scorer, so no exit can read held-back data. Every design position is closed inside the fence, so the shown book has no open marks.
- STATED, ruling 26, the shown arms: in the add arm the one add is half the initial share count (doc 169 line 108) and the signal's return is the cost-weighted return of both lots. The shown $500 book follows the judged variant, so if Card A drops the earnings requirement at the count branch the book does too. The book uses this plan's costs, stop overshoot, last-close convention and no credit for distributions, not doc 169's defaults.
- STATED, ruling 27, the t statistic: G is the number of calendar months that hold at least one judged entry, as the power script counts it, not a fixed 60.
- STATED, ruling 28, the shown comparison pool: names that passed the screen at t and did not trigger that day, without the signal's own symbol. A pool name lacking either endpoint print is skipped for that signal. With fewer than five names left the comparison is blank for that signal and the count of blanks is printed.
- STATED, ruling 29, two exits in Card B: the market fund return of a Card B signal is share-weighted over its two halves, each measured to its own exit print, like the signal itself. The comparison pool is weighted the same way.
- STATED, ruling 30, same round, before any price: if missing bars push an exit past the last design day despite ruling 25, the position is sold at the close of its last bar on or before the last design day, with the card's cost, and the count of such cases is printed. Above 1% of judged signals the run prints a coverage warning beside the result line.
- STATED, ruling 31, same round: the count stage is its own one-time run, `--go-count`, which needs one committed `P74_COUNT_GO=p74c-<manifest sha256>` on ledger row 226, a clean checkout and its own lock, separate from the scoring lock and approval. The smallest comparison pool of ruling 28 is five names and goes in the config (key compare_shown.min_pool).
- STATED, ruling 32, same round, before any price: in the shown add arm the stop overshoot is taken on the share-weighted raw entry price of both lots minus the stop in force, floored at zero, and the same adjusted exit price applies to both lots. In the shown comparison an intraday stop exit uses the pool name's close that day, as for IWM, and a pool name needs its entry open and every exit print of the signal to count. A missing IWM bar at any entry or exit print of either card cannot be patched: the input check fails before the lock and prints which days are missing.
- STATED, ruling 33, same round, before any price, shown arms only: a pool name "did not trigger" when it has no price-and-volume breakout that day, whatever the earnings and market-switch filters say (for Card B, no Gold or Revival tag). In the add arm each lot is compared with IWM from its own entry open to the shared exit print, and the two are weighted by each lot's cost.

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

- STATED: Added 2026-11-26 by the lead agent from [doc 171](../docs/research/171_idea_round_50_swing_horizon.md) (main 0a2f64c, merged into this draft), family 3 and its Second check, which ranks "52-week high and relative strength with a market filter and a hard stop" second. That family is Card A without the earnings requirement, which is already the ruled shown-only arm "without the earnings requirement".
- STATED: One more shown-only arm: the same Card A entry without the earnings requirement, with two changes only. The market filter is SPY's close above its 200-session simple average at t, in place of the QQQ and IWM switch; if it is off, no new signal and every open signal exits at the next open. The stop is fixed at 8% below the actual entry open (key arm_52w.stop_share), in place of the signal-day low. Everything else, including the 10-session EMA exit, the 40-session limit, the IWM comparison, the costs and the overshoot, is unchanged.
- STATED, accepted by the lead agent (ruling 12): The 3% refusal rule (worst open more than 3% above the stop) is tied to the signal-day-low stop. With a fixed 8% stop it would refuse every signal, so this arm drops that refusal and keeps the entry window. 
- STATED: The outside result for this family, AlpaTrade +30.4% a year from 2022 to 2026 as doc 171 line 214 reports it, ran on today's index members, so it has survivorship bias. It is not evidence for this plan. That is why gate (a), on dead names, decides whether this plan can run at all.
- STATED: This arm is shown only. It cannot pass or fail Card A, and it has no held-back opening of its own.
- STATED, accepted by the lead agent (ruling 12): a symbol that signals again while an earlier signal on it is still held does not start a second signal. Without this, one stock in a run could count many times and the signals would not be independent.

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
- STATED, lead agent's ruling before any price: A delisted holding is never dropped. If the bars of a held signal end, the main line exits at its last regular close (key delisted_last_close_share, primary 1.0). Shown-only lines: 0.5 times that close and zero (shown 0.5 and 0.0). The count of such cases is printed. RULE CHANGE: if they exceed 1% of judged signals (key delisted_last_close_share.share_trigger), every pass mark must also hold on the 0.5 times line (trigger_line 0.5).
- STATED: Clustered t: on design-year signals, demean the excess returns, sum them within each calendar month of entry, square and add the month totals, multiply by G/(G−1) where G is the number of entry months (60 in the design years), take the square root and divide by the signal count. t is the mean excess over that error. A zero or undefined error does not pass. RULE CHANGE, second round: was clustered by entry day. Shown only, the same t clustered by entry day and by entry week (key cluster_shown).

## Costs

- STATED, RULE CHANGE, second round: Card A main line 25 bp a side (key costs_bp_per_side.A). Shown-only lines at 10 and 50 bp a side (key cost_shown_bp_per_side.A). The first draft had 10 bp main.
- STATED: For reference, [doc 136](../docs/research/136_measured_stock_trading_costs.md) line 14: pooled 90th percentile half-spread, first 30 minutes, 10.055 bp. Line 20: the 38 single stocks, first 30 minutes, median 3.787 bp. Those were large names, so 25 bp is an assumption for $5 to $75 names at the open, not a measurement.
- STATED, RULE CHANGE, second round: the stop overshoot of 0.1332 of the stop distance is in the main line on stop exits for both cards (key stop_overshoot_share_of_risk, A and B). [Doc 66](../docs/research/66_measure_15_breakout_fills.md) line 7: "mean stop-exit slippage 0.1332 (n 840), odd lots left out". Doc 66 measured it on intraday breakout fills of liquid stocks in play over 60 days, not on these cards' names or daily-bar stops, so here it is an assumption. Shown only: 0.2134 with odd lots counted, doc 66 line 13 (key stop_overshoot_shown.A_odd_lots_in).
- STATED, Card B 50 bp a side (key costs_bp_per_side.B). Doc 136 has no figure for names under $10. Its 38 single stocks are large names (line 20). So 50 bp is an assumption, not a measurement. Shown only: 100 bp a side (key cost_shown_bp_per_side.B).
- STATED: Doc 66's price group $5 to $10 had entry mean 11.42 bp (n 62) and stop-exit mean 16.52 bp (n 52). The group under $5 had n 2 (stop exit mean 136.13 bp), too thin to use. These are intraday breakout fills on stocks in play, not opening fills on sub-$10 names.
- STATED: Card B as written in doc 169 has no stop overshoot. By the second-round ruling it now carries 0.1332 in the main line, as above.

## Pass marks

- STATED, all on design-year signals, each card on its own. Every mark must hold.
- STATED: mean net excess per signal above zero (key marks.mean_above) and at least 0.5% (key marks.mean_floor). RULE CHANGE, second round: was 1.0%.
- STATED, said plainly: this test is sized to find a true edge of +2% a signal. It will usually miss a true +1%.
- STATED: month-clustered t at least 2.0 (key marks.min_t). RULE CHANGE, third round: was 3.0. RULE CHANGE, second round: was day-clustered.
- STATED, the reason written in by the lead agent: the plan is two-stage. A design pass must be confirmed once on the held-back years, same sign and month-clustered t at least 2.0. Two independent one-sided hurdles at about 2.5% each are a stricter joint bar (about 0.06%) than one hurdle at t 3.0 (about 0.13%). The single 3.0 hurdle cannot be reached at +2% with 60 month clusters whatever the count.
- STATED, new mark, third round: no claim of any kind is made on a design pass alone. The plan's result line is "advance to held-back" or "closed" (key result_line). Only the held-back check can support a claim.
- STATED: mean excess positive in at least 4 of the 5 design years by entry year (keys marks.years_positive, marks.years).
- STATED: mean excess still positive with the top 1% of signals removed, that is the highest ceil(0.01 × n) excess returns (key marks.trim_top_share).
- STATED: at least 150 signals on at least 100 entry days (keys marks.min_signals, marks.min_entry_days). Fewer is "too thin", not a fail of the idea and not a pass.
- STATED, held-back mark, used only after a separate go: same sign as the design mean and month-clustered t at least 2.0 (keys heldback_marks.same_sign, heldback_marks.min_t).
- STATED: Shown-only arms, the $500 book and the day and week t never change a verdict, except the 0.5 times delisting line when its trigger is met.

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

- STATED: Probe P1, delisted coverage. Take the delisted CIKs from Form 25 filings in 2016 to 2021. For each, request daily bars for its last listed month with `asof` set inside its listing interval. Print counts only: names asked, names with any bar, names with bars on every session. No prices, no volumes are returned or saved. The names used are not chosen by any price. Pacing: at least 0.4 s between requests (key probes.alpaca_spacing_s); on HTTP 429, at most 3 re-sends after 2, 4 and 8 s waits (keys probes.resend_429_max, probes.resend_wait_s), then stop. A hard cap of 2,000 requests (key probes.P1_request_cap); reaching it stops the probe. On any stop the probe records the HTTP status code and the count of requests sent.
- STATED: Probe P2, ticker mapping. For a fixed list of CIKs, the first 200 by CIK number that filed a 10-K in 2017, print counts only: CIKs with a ticker from the cover tag, from the file name, both agreeing, and none. SEC pacing: 4 requests a second or fewer, at least 0.25 s apart (key probes.sec_spacing_s), with the declared User-Agent the repo already uses, "Brandon Church research modernsoftworks@gmail.com" (key probes.sec_user_agent), the same bounded re-send on 429 and the status code recorded on any stop. Hard cap 1,000 requests (key probes.P2_request_cap). EDGAR full-text search is not used.
- STATED: Probe P3, share counts. For the same 200 CIKs, count how many have a dated cover-page share count in each design year. Same SEC pacing, User-Agent and re-send rule as P2. Hard cap 400 requests (key probes.P3_request_cap).
- STATED: All three probes return counts only.

## Gate (b): power on made-up returns

- STATED: research_rig/power_74.py reads its settings from `replay_74_plan` (key power) and the calibration file research_rig/CALIB_74.json, and opens no other file. Third version. Five design years of 252 sessions and 60 calendar months of 21 sessions (keys power.sessions_per_year, power.sessions_per_month). Signal i of n enters on session floor(i × 1260 / n). Each hold is a made-up length, uniform from 1 to the card's limit, 40 sessions for Card A and 10 for Card B (key power.hold_limit).
- STATED: An excess return is the mean plus a common part plus its own shock. The common part is a weighted sum of calendar-month shocks over the months the hold spans, weighted by the share of hold sessions in each month. Signals whose holds share a month share that shock, so overlapping holds are modeled. All shocks are Student t with 3 degrees of freedom.
- STATED: Every pass mark is applied: month-clustered t at least 2.0, the 0.5% floor, 4 of 5 years, the top-1% trim, 150 signals on 100 days. Seed 740003 (key power.seed), 2,000 worlds per cell (key power.draws). Noise SDs per signal 12%, 15% and 18% for Card A, 20%, 25% and 30% for Card B (key power.noise_sd); the middle one is what the count branch uses. Means +1% and +2%, and +4% for Card B (key power.means).
- INFERENCE: The noise SDs are guesses, not measured from any price.

### Calibration of the common month share

- STATED, ruling 14: the common month share is a power-model assumption, not a mark. research_rig/calib_74.py calibrates it from Kenneth French library files we already hold off-repo, 10_Portfolios_Prior_12_2_Daily_CSV.zip and F-F_Research_Data_Factors_daily_CSV.zip (CRSP 202609 build). Only rows dated before 2017-01-01 are read into the arithmetic. No Alpaca bar or vendor price file is opened.
- STATED: The files hold daily returns, not monthly, so the script compounds them to calendar months. The series is the top prior-return decile ("Hi PRIOR", returns from day −250 to −21) minus the market (Mkt-RF plus RF). That is the nearest held series to a long momentum book against the market.
- STATED: The main series is the equal-weighted decile over 1963-07 to 2016-12 (key power.calibration.main). Equal weight was chosen before any calculation, as nearer to small and mid names than value weight. The others are shown only.
- STATED: Share per noise row = monthly variance × average fraction of a month a hold spans / per-signal variance. The average fraction is the mean hold, (limit + 1) / 2, over 21 sessions.
- INFERENCE: Card B's holds are not a momentum book (Gold and Revival buy names that fell). The same series is used for lack of a nearer one, and Card B's share is small mainly because its holds are short.

Printed by `python3 research_rig/calib_74.py`:

| Series | Months used | Months | Monthly SD of top decile minus market |
|---|---|---:|---:|
| Hi PRIOR equal-weighted minus market | 1963-07 to 2016-12 | 642 | 3.88% |
| Hi PRIOR equal-weighted minus market | 1990-01 to 2016-12 | 324 | 4.11% |
| Hi PRIOR value-weighted minus market | 1963-07 to 2016-12 | 642 | 3.41% |
| Hi PRIOR value-weighted minus market | 1990-01 to 2016-12 | 324 | 3.65% |

Main series equal_196307_201612, monthly common SD 3.88%, variance 0.001505.

| Card | Hold limit | Average fraction of a month a hold spans | Noise SD per signal | Common month share |
|---|---:|---:|---:|---:|
| A | 40 | 0.9762 | 12% | 10.20% |
| A | 40 | 0.9762 | 15% | 6.53% |
| A | 40 | 0.9762 | 18% | 4.53% |
| B | 10 | 0.2619 | 20% | 0.99% |
| B | 10 | 0.2619 | 25% | 0.63% |
| B | 10 | 0.2619 | 30% | 0.44% |

### Main table, third version

Pasted as `python3 research_rig/power_74.py` printed it:

| Card | Hold limit, sessions | Noise SD per signal | Common month share (calibrated) | True mean excess | Smallest count, 80% power, all marks | Smallest count, 80%, without the mean floor | Power at 150 / 500 / 1,000 / 2,000 / 4,000 signals, all marks |
|---|---:|---:|---:|---:|---:|---:|---|
| A | 40 | 12% | 10.20% | +1.0% | none up to 16,000 (best 60%) | none up to 16,000 | 17% / 35% / 43% / 52% / 56% |
| A | 40 | 12% | 10.20% | +2.0% | 600 | 600 | 50% / 80% / 88% / 91% / 95% |
| A | 40 | 15% | 6.53% | +1.0% | none up to 16,000 (best 59%) | none up to 16,000 | 14% / 27% / 37% / 48% / 52% |
| A | 40 | 15% | 6.53% | +2.0% | 1,000 | 1,000 | 38% / 68% / 83% / 90% / 93% |
| A | 40 | 18% | 4.53% | +1.0% | none up to 16,000 (best 57%) | none up to 16,000 | 11% / 24% / 32% / 42% / 51% |
| A | 40 | 18% | 4.53% | +2.0% | 1,250 | 1,250 | 29% / 59% / 76% / 87% / 91% |
| B | 10 | 20% | 0.99% | +1.0% | none up to 16,000 (best 73%) | none up to 16,000 | 9% / 18% / 32% / 49% / 65% |
| B | 10 | 20% | 0.99% | +2.0% | 1,000 | 1,000 | 24% / 59% / 82% / 96% / 99% |
| B | 10 | 20% | 0.99% | +4.0% | 300 | 300 | 70% / 99% / 100% / 100% / 100% |
| B | 10 | 25% | 0.63% | +1.0% | none up to 16,000 (best 50%) | none up to 16,000 | 7% / 13% / 24% / 37% / 46% |
| B | 10 | 25% | 0.63% | +2.0% | 2,000 | 2,000 | 17% / 41% / 67% / 88% / 98% |
| B | 10 | 25% | 0.63% | +4.0% | 400 | 400 | 52% / 92% / 99% / 100% / 100% |
| B | 10 | 30% | 0.44% | +1.0% | none up to 16,000 (best 32%) | none up to 16,000 | 7% / 11% / 16% / 27% / 30% |
| B | 10 | 30% | 0.44% | +2.0% | 2,500 | 2,500 | 13% / 32% / 53% / 78% / 92% |
| B | 10 | 30% | 0.44% | +4.0% | 500 | 500 | 40% / 82% / 96% / 100% / 100% |

MEASURED on made-up data: 2000 worlds per cell, seed 740003, common month share calibrated per row from research_rig/CALIB_74.json, holds uniform 1 to the limit, t clustered by calendar month of entry (60 months), Student t with 3 degrees of freedom, mean floor 0.5%, t mark 2.0.

Shown only, fixed common month shares of 2%, 5% and 10% at the middle SD (key power.common_share_shown), pasted as `python3 research_rig/power_74.py --sensitivity` printed it:

| Card | Noise SD | Common month share | True mean excess | Smallest count, 80% power, all marks | Power at 150 / 500 / 1,000 / 2,000 / 4,000 signals |
|---|---:|---:|---:|---:|---|
| A | 15% | 2% | +1.0% | 6,000 | 12% / 32% / 48% / 65% / 78% |
| A | 15% | 2% | +2.0% | 600 | 39% / 78% / 94% / 99% / 100% |
| A | 15% | 5% | +1.0% | none up to 16,000 (best 66%) | 13% / 27% / 40% / 50% / 60% |
| A | 15% | 5% | +2.0% | 750 | 37% / 71% / 86% / 93% / 94% |
| A | 15% | 10% | +1.0% | none up to 16,000 (best 48%) | 13% / 25% / 33% / 38% / 45% |
| A | 15% | 10% | +2.0% | 2,000 | 36% / 63% / 74% / 82% / 86% |
| B | 25% | 2% | +1.0% | none up to 16,000 (best 46%) | 7% / 13% / 19% / 32% / 38% |
| B | 25% | 2% | +2.0% | 2,500 | 15% / 38% / 63% / 77% / 90% |
| B | 25% | 2% | +4.0% | 400 | 51% / 90% / 98% / 100% / 100% |
| B | 25% | 5% | +1.0% | none up to 16,000 (best 33%) | 7% / 15% / 17% / 23% / 29% |
| B | 25% | 5% | +2.0% | 12,000 | 17% / 34% / 50% / 63% / 70% |
| B | 25% | 5% | +4.0% | 400 | 49% / 85% / 95% / 98% / 99% |
| B | 25% | 10% | +1.0% | none up to 16,000 (best 22%) | 7% / 11% / 14% / 17% / 20% |
| B | 25% | 10% | +2.0% | none up to 16,000 (best 58%) | 14% / 30% / 41% / 45% / 54% |
| B | 25% | 10% | +4.0% | 600 | 46% / 78% / 88% / 92% / 94% |

### What each card's test can and cannot find

- INFERENCE: With 60 month clusters the common month shock sets a floor on the error that more signals cannot remove, roughly the common SD over the square root of 60. A true +1% sits too close to that floor and the 0.5% mean floor, so it is found at most about 60% of the time for Card A and 73% for Card B at any count.
- INFERENCE, Card A: the test can find a true edge of +2% a signal with about 1,000 signals at the middle SD (600 to 1,250 across the SD rows). It cannot reliably find +1% at any count. At the 150-signal floor it finds +2% only about 38% of the time at the middle SD.
- INFERENCE, Card B: the test can find +4% a signal with about 400 signals at the middle SD (300 to 500), and +2% with about 2,000 (1,000 to 2,500). It cannot reliably find +1% at any count.
- INFERENCE: The shown-only table moves these needs. For Card A at +2% the need runs from 600 at a 2% share to 2,000 at 10%. For Card B at +2% it runs from 2,500 at 2% to none at 10%, while +4% stays at 400 to 600. Only at a 2% share does Card A find +1%, at 6,000 signals.
- INFERENCE: These counts need the lower-bound count from gate (c) to reach them. Doc 169 guesses a few to 25 funded starts a year per card in the $500 book, which is far below; raw symbol-day signals will be more, but the gate (c) count decides.

### Second version, t 3.0 and a 10% common share

- STATED: Kept for the record. It used the month-clustered t at least 3.0 and a 10% common share guessed for both cards, before the calibration and before ruling 13 (key power.second_version). Seed 740002.

| Card | Hold limit, sessions | Noise SD per signal | True mean excess | Smallest count, 80% power, all marks | Smallest count, 80%, without the mean floor | Power at 150 / 500 / 1,000 / 2,000 / 4,000 signals, all marks |
|---|---:|---:|---:|---:|---:|---|
| A | 40 | 12% | +1.0% | none up to 16,000 (best 40%) | none up to 16,000 | 4% / 12% / 21% / 28% / 34% |
| A | 40 | 12% | +2.0% | 2,000 | 2,000 | 21% / 55% / 73% / 82% / 86% |
| A | 40 | 15% | +1.0% | none up to 16,000 (best 26%) | none up to 16,000 | 2% / 8% / 15% / 18% / 26% |
| A | 40 | 15% | +2.0% | none up to 16,000 (best 76%) | none up to 16,000 | 11% / 37% / 50% / 62% / 72% |
| A | 40 | 18% | +1.0% | none up to 16,000 (best 21%) | none up to 16,000 | 2% / 7% / 9% / 13% / 17% |
| A | 40 | 18% | +2.0% | none up to 16,000 (best 61%) | none up to 16,000 | 8% / 22% / 37% / 46% / 55% |
| B | 10 | 20% | +1.0% | none up to 16,000 (best 9%) | none up to 16,000 | 1% / 3% / 4% / 6% / 8% |
| B | 10 | 20% | +2.0% | none up to 16,000 (best 47%) | none up to 16,000 | 5% / 14% / 22% / 32% / 40% |
| B | 10 | 25% | +1.0% | none up to 16,000 (best 6%) | none up to 16,000 | 1% / 2% / 2% / 3% / 4% |
| B | 10 | 25% | +2.0% | none up to 16,000 (best 29%) | none up to 16,000 | 2% / 9% / 14% / 19% / 24% |
| B | 10 | 30% | +1.0% | none up to 16,000 (best 4%) | none up to 16,000 | 0% / 1% / 2% / 2% / 4% |
| B | 10 | 30% | +2.0% | none up to 16,000 (best 18%) | none up to 16,000 | 2% / 5% / 8% / 12% / 15% |

MEASURED on made-up data: 2000 worlds per cell, seed 740002, common month shock 10% of variance, holds uniform 1 to the limit, t clustered by calendar month of entry (60 months), Student t with 3 degrees of freedom, mean floor 0.5%.

### First version, optimistic

- STATED: Kept for the record. Why it is optimistic: it treated signals on different days as independent apart from a one-day shock, and clustered by entry day, so overlapping 40-session holds were counted as separate evidence. It also used the old 1.0% floor. Seed 740001, 1.5 signals per entry day, day shock 10% of variance (key power.first_version).

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

## Gate (c): count only, design only

- STATED, lead agent's ruling before any price, the count branch (key count_branch), fixed now:
- STATED: The need is the smallest count in the main table for 80% power at +2.0% with the middle noise SD of that card (15% for Card A, 25% for Card B). With the third-version main table, the need is 1,000 lower-bound signals for Card A and 2,000 for Card B.
- STATED: Card A: if the earnings version's design-year signal count is at or above the need, the earnings version is the judged rule. Otherwise the judged rule is the arm without the earnings requirement, and the earnings version is shown only. If that arm is also under the need, Card A closes on count with no return read.
- STATED: Card B: if the pooled Gold and Revival design-year signal count is at or above the need, it is judged. Otherwise Card B closes on count with no return read.
- STATED: The count script reads the custodied bars and filings and prints only the counts this branch needs, for the Card A earnings version, the Card A arm without the earnings requirement, and Card B pooled. Nothing else.
- STATED, ruling 16: for each of those it prints two design-year signal counts with their entry-day counts. The raw upper bound counts every qualifying symbol-day signal. The lower bound drops any signal on a symbol that comes within the card's time limit after an earlier counted signal on that symbol, 40 sessions for Card A and 20 for Card B (RULE CHANGE, ruling 19; was 10) (key count_branch.lower_bound_gap_sessions). The branch uses the lower bound (key count_branch.bound).
- STATED: The code cannot compute a return. The gate functions get a view of each symbol's bars that ends at the signal close t. The script has no exit logic, no entry-open check and no benchmark series. Its output schema is integers only, and its test fails if any float leaves the script.
- INFERENCE: The count stage has no exit logic and no next-open check. The lower bound treats every earlier signal as held for the full time limit, so it can drop signals the real rule would keep, but it cannot keep one the real rule would drop for a hold. Signals refused at the next open are in both counts (ruling 18), so gate (d) still applies the 150-signal and 100-day marks.

## Gate (d): one scoring run, design years

- STATED: One run per card, once, on design years only. It prints the marks, the shown-only arms and the $500 book. It has no held-back mode. Its result line is "advance to held-back" or "closed".
- STATED, ruling 17, shown only, not a mark: each signal's return is also compared with the equal-weighted same-days return of all names that passed the screen that day without the trigger. For Card A that is the leader screen; for Card B, the price and volume scan (key compare_shown). Same entry and exit prints as the signal, no cost. This shows whether a gain comes from the trigger and the exits or only from owning leaders in a good year.
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
