# E02 iwm_pre_holiday

Status: manual forward watch, written 2026-11-26. Queue row 71. Pretend money only: no broker, no orders, no automation. [Replay 39](../../docs/research/84_replay_39_iwm_pre_holiday.md) did not pass (5 of 7 marks); this log is a watch, not a tested edge or a reason to advance the rule.

## What it records

- One record per official NYSE full closure. Pretend buy IWM at the raw SIP daily close two trading sessions before the closure, then sell at the close of the last session before it. Include early closes at their scheduled time. The rule in [Replay 39](../../research_rig/PREREG_39_iwm_preholiday.md) is unchanged.
- Include IWM cash per share only for an ex-date on the exit session, and charge 2 bps per side. Use the issuer's dated payout history; explicitly verify zero before entering zero. If an unexpected split, another noncash action or a new closure changes the table, stop and correct the plan before using the event.
- Store the full record, including input prices, off repo in `/home/user/workspace/rig/data/forward_e02`. As with E01, the in-repo log `practice/forward/E02_log.json` contains dates, return, distribution metadata and the full record SHA-256, not close prices. Add its INDEX row when the first record is made.

## When and how to record

The lead runs `python3 practice/forward_e02.py plan` to print the pin table. At least 20 minutes after the exit, run `python3 practice/forward_e02.py record YYYY-MM-DD /private/path/iwm-event.json`, using the holiday date as the key and a mode-0600 packet outside the repo. The recorder makes no requests. Supply raw SIP entry and exit closes and the verified issuer cash per share on the exit ex-date. The packet has exactly these fields: `symbol` (IWM), `feed` (sip), `adjustment` (raw), `entry_session`, `exit_session`, `entry_close`, `exit_close`, and `exit_ex_date_cash_per_share`.

Record before midnight New York time at the start of the next open NYSE session after the holiday to count as forward evidence. Late records are still saved, marked not counted. Never record an event twice. Show losses as losses; this small watch earns no new verdict.

## Sessions

The [official NYSE holiday and early-closing calendar](https://ir.theice.com/press/news-details/2024/NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx) extends the replay's full-closure rule. Today is Thanksgiving, so its pre-holiday session has already passed and is not backfilled. The first event is Christmas Day, December 25, 2026, with entry December 23 and an early exit December 24. All entry closes are at 16:00 ET. The series stops after the December 2027 event unless the pinned table is extended.

| NYSE closure | Entry session | Exit session | Exit (ET) |
| --- | --- | --- | --- |
| 2026-12-25 | 2026-12-23 | 2026-12-24 | 13:00 |
| 2027-01-01 | 2026-12-30 | 2026-12-31 | 16:00 |
| 2027-01-18 | 2027-01-14 | 2027-01-15 | 16:00 |
| 2027-02-15 | 2027-02-11 | 2027-02-12 | 16:00 |
| 2027-03-26 | 2027-03-24 | 2027-03-25 | 16:00 |
| 2027-05-31 | 2027-05-27 | 2027-05-28 | 16:00 |
| 2027-06-18 | 2027-06-16 | 2027-06-17 | 16:00 |
| 2027-07-05 | 2027-07-01 | 2027-07-02 | 16:00 |
| 2027-09-06 | 2027-09-02 | 2027-09-03 | 16:00 |
| 2027-11-25 | 2027-11-23 | 2027-11-24 | 16:00 |
| 2027-12-24 | 2027-12-22 | 2027-12-23 | 16:00 |
