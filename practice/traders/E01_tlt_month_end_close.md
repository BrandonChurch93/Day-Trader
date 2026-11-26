# E01 tlt_month_end_close

Status: forward log, written 2026-11-26. Queue row 46. First month December 2026. No broker account, no order, no money of any kind. The paper-order leg is a proposal only (`practice/PROPOSAL_E01_paper_order_leg.md`).

## What it does

Each month it records Replay 25's TLT window as it happens: buy at the close of the fourth-last session of the month, sell at the close of the last. It answers one question: does the rule that passed Replay 25 keep paying on months the replay never saw?

The rule is Replay 25's, unchanged (`research_rig/PREREG_25_treasury_month_end.md`, ledger row 162). Nothing about it is tuned here.

## What it records each month

- The entry and exit sessions, and the SIP daily close of each, raw, the same source as the replay.
- The Nasdaq closing cross print at each close (largest condition-6 print on exchange Q or T), its size in shares, and the official close print (condition M).
- The cost of each side at the cross against the SIP close, in bps, signed as the rule pays it.
- TLT cash distributions with an ex-date on the three held sessions.
- The net return at 2 bps a side on the SIP closes, as the replay counts it. The same at the cross prices, shown only.

Measurement 27 found the cross equal to the SIP close on 251 of 258 past sessions, so the two returns should almost always agree ([doc 70](../../docs/research/70_measure_27_tlt_closing_cross.md)).

## Where it goes

- The full record, with prices, goes off repo, one file per month.
- One line per month goes to `practice/forward/E01_log.json`: dates, returns, bps, cross sizes, distribution and the record's sha256. No prices.
- The log file appears with the first record.

## When it runs

- `python3 practice/forward_e01.py record YYYY-MM`, through the owner's saved data credential, at least 20 minutes after the exit close.
- A month counts as forward evidence only if its record is written before the next month starts in New York. A late record is kept and marked not counted.
- One record per month. It refuses to write a month twice.

## Sessions

Pinned from the same calendar version as the replay (XNYS, exchange-calendars 4.13.3). All close at 4:00 pm New York.

| Month | Entry | Exit |
|---|---|---|
| 2026-12 | Mon 2026-12-28 | Thu 2026-12-31 |
| 2027-01 | Tue 2027-01-26 | Fri 2027-01-29 |
| 2027-02 | Tue 2027-02-23 | Fri 2027-02-26 |
| 2027-03 | Thu 2027-03-25 | Wed 2027-03-31 |
| 2027-04 | Tue 2027-04-27 | Fri 2027-04-30 |
| 2027-05 | Tue 2027-05-25 | Fri 2027-05-28 |
| 2027-06 | Fri 2027-06-25 | Wed 2027-06-30 |
| 2027-07 | Tue 2027-07-27 | Fri 2027-07-30 |
| 2027-08 | Thu 2027-08-26 | Tue 2027-08-31 |
| 2027-09 | Mon 2027-09-27 | Thu 2027-09-30 |
| 2027-10 | Tue 2027-10-26 | Fri 2027-10-29 |
| 2027-11 | Wed 2027-11-24 | Tue 2027-11-30 |
| 2027-12 | Tue 2027-12-28 | Fri 2027-12-31 |

- If the month's SIP bars do not match this table (a new holiday, a closure), it refuses and the table is fixed by a new ledger row first.
- 2026-12-24 closes at 1:00 pm and 2026-12-25 is closed, both before the December window. 2027-11-26 closes at 1:00 pm and is a held session, not an entry or exit. SIFMA recommends a 2:00 pm bond close on 2026-12-31 ([SIFMA](https://www.sifma.org/resources/guides-playbooks/holiday-schedule)); stocks trade a full day.

## How it is judged

- Not before 12 months. One month says almost nothing. A dozen months is still a small sample, so the log is a reason to keep watching or to stop, not proof.
- Each month is shown as it is. Losses are shown with a minus sign.

## When it stops

After 2027-12, unless a new ledger row extends the session table.
