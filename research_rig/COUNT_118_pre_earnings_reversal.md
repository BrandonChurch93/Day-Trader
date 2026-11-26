# Count 118: pre-earnings reversal, can the report date be known beforehand

Queue 118, doc 155 candidate 1. Count only, no price of any kind was read. Window 2016-01-01 to 2021-12-31. Nothing dated 2022 or later was used. All figures below are written by `research_rig/count_118_write_doc.py` from `research_rig/count_118_summary.json`, `research_rig/count_118_events.csv` and `research_rig/count_118_notice_sample.csv`.

## Verdict

Close before prices. MEASURED: the date is easy to know for about half the reports and the rule fires often enough, but at 1144 usable events the bottom fifth is about 229 trades in six years. With the halved paper effect and the paper's own noise, the sum gives z about 0.31, far from 2. No plausible change of universe size inside a $500 account fixes that.

## Universe

- STATED: the 100 companies in the S&P 100 on 2015-12-31, from the iShares S&P 100 ETF (OEF) schedule of investments in the [iShares Trust N-Q filed 2016-02-26](https://www.sec.gov/Archives/edgar/data/1100663/000119312516480933/d146052dnq.htm). Two share classes of one firm count once.
- Why: a dated list fixed before the window, so firms that later merged away are kept until they stop reporting (no survivor filter). Plan 69's roster (research_rig/GRID_69.json) has only 33 single stocks.
- Disney has two CIKs (old and the 2019 holding company); both are used. 18 CIKs were set by hand and checked against EDGAR names.
- MEASURED: 100 companies produced at least one report in the window.

## Step 1: actual report times

Source: data.sec.gov submissions JSON per company, declared user agent, about 4 requests a second. No full-text search. The bulk files also hold rows after 2021; those were dropped unread beyond the date field.

Rule: an original 8-K listing Item 2.02. Acceptance time is UTC, converted to New York time. Before 09:30 is before the open, 09:30 to the close is in session, after the close (16:00, or 13:00 on early-close days) is after the close. Report day t is the acceptance day for before the open and in session, the next session for after the close or a closed day.

Dedupe: Item 2.02 filings by one company within 60 calendar days of the first in a group form one group. MEASURED: 182 groups, 198 extra filings dropped. In 152 groups the kept filing is the first whose Item 2.02 text names results of a quarter or year and none of a fixed list of non-report words (preliminary, transcript, recast, historical, fact sheet, charge and so on). In 30 groups no filing passed and the first was kept; those are marked `fallback` in the events file and left out of the usable count.

| Year | Reports | Separate report days | Before open | In session | After close |
|---|---|---|---|---|---|
| 2016 | 395 | 119 | 256 | 8 | 131 |
| 2017 | 389 | 114 | 254 | 7 | 128 |
| 2018 | 384 | 123 | 243 | 5 | 136 |
| 2019 | 371 | 119 | 234 | 11 | 126 |
| 2020 | 362 | 121 | 227 | 10 | 125 |
| 2021 | 360 | 113 | 221 | 6 | 133 |
| All | 2261 | 709 | 1435 (63.5%) | 47 (2.1%) | 779 (34.5%) |

MEASURED, dedupe quality: a hand reading of 20 random kept filings from groups (before the last text-test fix) found 1 wrong pick by text (a January healthcare-conference guidance update, since added to the word list) and 2 of 3 fallbacks wrong. Single filings were not read; a gap check found the off-cycle ones (guidance, recasts) and the 60-day window was set to catch them.

## Step 2a: mechanical forecast

Rule, fixed before scoring: take the company's kept report 300 to 430 days earlier closest to 364 days; forecast the same month, same weekday, same ordinal week a year later (last such weekday if it does not exist), moved to the next session if closed. Forecast day f is that day for a base report before the open or in session, the next session if the base was after the close.

MEASURED on 2239 reports with a base (22 had none):

- Exact: 966 (43.1%).
- Off by one session: 307 (13.7%); 184 late, 123 early.
- Off by more: 966 (43.1%); 561 late, 405 early.
- Came early (before f): 528 (23.6%). Of these, 528 were public before the entry close, so no trade.

Entry under 2a: buy at the close of the session before f if no Item 2.02 has been accepted by then. Sell at the close of the session after t once the 8-K appears. If the report is late by more than one session, the trade is a wasted entry.

## Step 2b: company's own advance notice on EDGAR

Sample: 60 kept reports, random.Random(118) over the events file sorted by accession. For each, every 8-K with Item 7.01 or 8.01 accepted in the 45 days before, and the previous quarter's Item 2.02 release, were read (all .htm exhibits). A date near a call, webcast, results or earnings word was then read by hand.

- MEASURED: notice found on EDGAR for 3 of 60 (5.0%). All 3 named the exact release date. None came early or late against the named date.
- MEASURED: days ahead: 91, 16, 8 calendar days (INTC prior_2.02, UNP 7.01/8.01, IBM 7.01/8.01).
- MEASURED: 27 of 60 reports had any 7.01 or 8.01 filing in the 45 days before.
- UNKNOWN: how many firms gave notice by newswire or their own site. Those channels are outside this count; the queue 101 protocol (`research_rig/COUNT_101_earnings_date_advancers.md`) already excludes newswire syndications.

Entry under 2b: buy at the close of the session before the named date (the session before the next session if the named time is after the close). Only about one report in twenty gets a 2b entry, so 2b is not a working source here.

MEASURED, 8-K lag check on the same sample: the date in the 8-K's own Item 2.02 text equals its acceptance date in 59 of 59. So at day level the 8-K does not lag the release. A within-day lag (press release before the open, 8-K after the close) cannot be seen from EDGAR and is UNKNOWN.

## Step 3: usable events and power

MEASURED under 2a: usable means t is f or f+1, the report was not out before the entry close, and the group was not a fallback. 1144 usable events on 491 separate entry days. 567 entries would be placed with no report by f+1. 6 fallback events left out.

| Year | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 |
|---|---|---|---|---|---|---|
| Usable | 162 | 213 | 246 | 200 | 140 | 183 |

STATED from [So and Wang 2014](https://dspace.mit.edu/bitstream/handle/1721.1/119665/So_News-driven%20return.pdf):

- Table 2, actual date: Low-High 144.8 bp (`sw2014_actual_low_high_bp`), long side 81.3 bp (`sw2014_actual_q1_bp`).
- Table 7, p. 37, expected date: Low-High 65.2 bp (`sw2014_expected_low_high_bp`), long side 40.8 bp (`sw2014_expected_q1_bp`), so the long side is 62.6% of the spread.
- Table 7 by timing: on time 166.6 bp, late 68.9 bp, early -14.7 bp.
- Table 1, p. 31: SD of the three-day return over all events 877.4 bp (`sw2014_sd_ret_bp`). A per-event SD of the long leg or the spread is not printed: UNKNOWN. The all-event SD is used as the noise.

Sum (doc 117 form, z = net / SD x sqrt(n)): gross = `sw2014_expected_q1_bp` x `haircut` = 20.4 bp. Long trades n = usable x `quintile_share` = 229.

| Cost case | Net bp | z at n | n needed for z = 2 |
|---|---|---|---|
| doc 136 measured, last 30 min (`cost_half_spread_last30_bp` x 2) | 18.3 | 0.31 | 9244 |
| judged (`cost_judged_per_side_bp` x 2) | 10.4 | 0.18 | 28471 |

Days cluster: the 1144 usable events share 491 entry days, so the effective n is lower than the table uses. The exact-close cost is UNKNOWN (doc 136 measures the last 30 minutes only). The rule enters at the close before t and holds days t and t+1; the paper's three-day return also holds day t-1, so the paper figure may overstate this rule: UNKNOWN by how much.

## Ways this fools us

- Look-ahead from the actual date. Check: the usable count uses only the forecast day and the filings accepted before the entry close.
- 8-K lags the press release. Check: release date in the 8-K text vs acceptance date (done for the sample, day level). Within-day lag needs a dated newswire source.
- Non-earnings Item 2.02 filings (guidance, preliminaries, recasts). Check: the text test, the 60-day groups and the hand reading above; a price test would also need it.
- Early reports do not reverse (paper: early -14.7 bp). Check: 2a skips any report out before the entry close; the count shows how many.
- Effect gone after the paper's sample (1996 to 2011) and among the largest firms. Check: split any later test by year and firm size; the paper says the effect was larger in its first half, no number printed.
- Window mismatch (rule holds t, t+1; paper holds t-1, t, t+1). Check: price both windows; the paper's figure is for the longer one.
- Market adjustment and beta: high-beta names sit in the bottom fifth after a market drop. Check: adjust by beta and by sector, not only by the market.
- Survivorship and mergers: firms leaving mid-window. Check: fixed 2015 list, stop events at the last report; MEASURED company count above.
- Cost at the exact close is UNKNOWN. Check: measure the closing auction cost before any plan.
- COVID 2020 date shifts lower the 2a hit rate. Check: the by-year usable row (2020 is the lowest).

## Files

- `research_rig/count_118_events.csv`: one row per kept report, no price field, SHA-256 0ebc51968c76a11f43061e5372ad23dc229cb910ff2ad5b3483bc2cc8b083564.
- `research_rig/count_118_notice_sample.csv`: the 60-report notice sample, no price field, SHA-256 4ad4a14a0e71fbbf41805bcb29155027414df7055b509488af452f23d51602b5.
- `research_rig/count_118_summary.json`: counts. The text-test flags file kept off repo has SHA-256 03077041f8e465e6577a2438e13d4766906063eabd78e83e7f1b65183ee07d0b.
- `research_rig/count_118_pre_earnings.py`, `research_rig/count_118_fetch_notice.py`, `research_rig/count_118_write_doc.py`: the scripts. Raw EDGAR downloads stay off repo, packed with xz.
