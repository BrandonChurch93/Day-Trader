# Measurement 27. Closing cross against the consolidated close on TLT month-end entry and exit sessions

Status FROZEN 2026-11-26 04:05 UTC, before any trade was collected for this measurement.

This is a measurement, not a trial. It computes no window return and nothing in it can pass or fail as a trading rule. Queue row 47, ledger row 164.

## Why

- Replay 25 (`research_rig/PREREG_25_treasury_month_end.md`, ledger row 162) bought TLT at the SIP daily close of the fourth-last session of each month and sold at the SIP daily close of the last session, with 2 bps a side of cost.
- A real market-on-close order on TLT fills at the Nasdaq closing cross price, not at the SIP daily close. STATED by Nasdaq: the cross executes at one price, the Nasdaq Official Closing Price ([Nasdaq closing cross FAQ](https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf)).
- An Alpaca practice account cannot show this. STATED by Alpaca: practice orders are filled by simulation against the best current quote ([Alpaca](https://docs.alpaca.markets/docs/paper-trading)). Alpaca staff on its forum say a practice market-on-close order fills at the quote, not the auction ([Alpaca forum](https://forum.alpaca.markets/t/paper-moc-orders-partially-fill-remainder-expires-same-setup-on-live-works/19155)).
- So the gap between the cross price and the SIP daily close, taken from the public trade tape, is the part of the replay's cost that could be wrong.

## Sessions, fixed by rule

- The 130 entry sessions and 130 exit sessions of Replay 25: for each month January 2016 to October 2026, the fourth-last and the last session in `research_rig/calendar_25.json`, by `common_25.windows(days, 3)`. 260 sessions. The replay's results file is not read.
- Scheduled close per session: 16:00 New York time, or 13:00 on the early-close days of XNYS in exchange-calendars 4.13.3 (the version pinned in calendar_25.json). The 21 early-close days from 2016-01-04 to 2026-11-24 are written in `measure_27.py`. Five of the 260 sessions are early closes.

## Data

- Consolidated close: the `c` field of the SIP daily bar for the session in the Replay 25 input file `TLT.json`, checked against the input manifest (sha256 43f92b5249c8a2aa8778139f928cf643814e47b778d5892a903227830777aa9a). These are the closes the replay used.
- Trades: Alpaca historical stock trades, SIP feed, symbol TLT, from 1 second before the scheduled close to 300 seconds after it, through the owner's saved data credential. No live data and no date after 2026-10-30.
- Trades stay off repo, in `/home/user/workspace/rig/data/measure_27/`. The repo gets aggregates only.

## Definitions

- Cross print: among trades on exchange Q (Nasdaq) with condition 6 (Closing Prints) in the window, the one with the largest size. Ties: the earliest.
- Official close print: the first trade on exchange Q with condition M (Market Center Official Close) in the window. Used as a cross-check only.
- Found: a cross print exists for the session.
- Signed cost in bps, as the strategy would pay it, against the SIP daily close: entry (buy) (cross / close − 1) × 10,000; exit (sell) (1 − cross / close) × 10,000. Positive is a cost.
- Absolute gap: |cross / close − 1| × 10,000.
- Percentiles: linear interpolation.

## Marks, fixed by the lead before any number was seen

The replay's 2 bps a side is fair if all three hold:

1. The cross print is found on at least 95% of the 260 sessions (at least 247).
2. The mean signed cost per side is at most 1.0 bp. Read as: the entry mean and the exit mean, each over its found sessions, are both at most 1.0 bp. The pooled mean is shown too.
3. The 95th percentile of the absolute gap, over all found sessions, is at most 3 bps.

If any mark fails, the page says the 2 bps assumption is not supported by the closing cross and gives the measured figures.

## Shown, not part of the marks

- Cross size in shares: median and 5th percentile, so we know what order size the auction absorbs.
- How often the cross print equals the SIP close exactly, and how often the M print agrees with the cross price.
- By side and by year: n, mean, median and 95th percentile of the signed cost.
- The early-close sessions on their own.

## Limits, written before the run

- The cross price is what a market-on-close order receives. It says nothing of commissions or the very small SEC and FINRA sell fees.
- It is an average-size result. An order large enough to move the auction would pay more. The cross size is shown for that reason.
- If Alpaca's SIP daily close is itself the official close on most days, the gap will be near zero by construction. That is a finding, not a fault: it would mean the replay priced at the auction.
