# Plan 23: early index buying after large US listings

Status FROZEN.

Frozen 2026-11-26 03:37 UTC (read from `date -u`) after audit pass 2 and its delta were CLEAR (`rig_code_auditor_b`). Drafted off repo 2026-11-26 03:06 UTC; revised 03:12 UTC (ruling on the choices), 03:28 UTC (rulings on audit pass 1: B1, B2, four should-fix items, a 50 bps line) and 03:35 UTC (pass 2 should-fix items, the power limit). Queue row 37, ledger row 160. No bar has been fetched for this plan and no return has been worked out on real prices. The design below was fixed by the lead on 2026-11-26 before any price; the lines under "Choices made in the draft" are the helper's, approved by the lead on 2026-11-26. Every number is a key in `replay_23_plan` in `config/thresholds.yaml`. Collection, freeze and scoring refuse without the lead's approval commit (see Order of work).

## The question

STATED (Murray and Sammon, Review of Asset Pricing Studies 16(2), 2026, [OUP](https://academic.oup.com/raps/article/16/2/163/8416725)): IPOs large enough for CRSP's fast-track rule are added after the close of the fifth trading day, index funds buy most of their shares in that day's closing auction, and eligibility is "highly predictable using information available before the IPO". Their sample ends in December 2022 and their 5.16% is a peer-adjusted gross estimate (`docs/research/63_round_8_outside_evidence.md`).

Does buying such a listing at its first day's close and selling at the fifth session's close make money after costs, on events chosen from the prospectus alone, and also after 2022?

The rule, its sources and the size stand-in are in `~/workspace/rig/data/ipo_fasttrack/RULE.md`. The event list comes from `ipos.csv` in that folder (method and gaps in its `README.md`). The CRSP breakpoint values stay off repo (lead's ruling, 2026-11-26); the repo gets links and the method only.

## Events (fixed by the lead)

- Rows of `ipos.csv` priced from `first_pricing` (2017-03-20) to `last_pricing` (2026-10-23), with `us_screen_guess` = yes and a stand-in value present.
- Stand-in value = offer price x shares outstanding after the offering, from the final 424B4.
- Share count (lead's ruling on audit pass 1, B1): the prospectus's own "to be outstanding after this offering" total across all classes of common stock, counted once, without the underwriters' option. Read by `src/shares_after.py` in the row 37 folder:
  - a stated total line wins, and must equal the class lines when they are also read;
  - with no total line, one class gives its own value and several classes are summed, each once;
  - units of another entity (LLC, LP or OpCo units) and preferred stock are not counted;
  - anything else is `unverified:<reason>`.
- Each event at 0.67x or more carries the quoted total, the classes it covers and a check flag (`shares_check`: `verified`, `verified_manual` or `unverified:<reason>`), in `replay_23/shares_check_23.csv` and in `ipos.csv`. 23 totals the code could not read alone were read by hand from the saved cover and "The Offering" text; each has its quote in `src/shares_manual.csv`.
- An event whose total cannot be read with confidence is listed with status `shares_unverified` and left out before the lock, with the reason.
- The kept 424B4 must offer common shares (any class, including subordinate voting shares and common shares of beneficial interest) or American depositary shares. `fetch_23.py --events` reads each selected 424B4's cover text from the row 37 parse cache (`src/snips.jsonl.gz`, first 15,000 characters of the filing) with fixed patterns (`common_23.classify_security`). A filing for preferred stock, units, notes or other depositary shares is listed with status `not_common_security` and left out before the lock. A cover the patterns cannot place refuses the selection (`P23_SECURITY_UNKNOWN`) so a person reads it. The cache file is pinned in the freeze record.
- Judged: value at least `judged_ratio_min` (1.5) times the latest 98% breakpoint published on or before the pricing date. This is known from the prospectus before the first trade; no first-day price is used to choose.
- Shown only: `band_ratio_min` to `judged_ratio_min` (1.0 to 1.5 times), and `near_ratio_min` to `near_ratio_max` (0.67 to 1.5 times).
- First trading day (lead's ruling on audit pass 1, B2; one rule for every event): the first daily bar from the `first_bar_window_bdays`-th (3rd) session before the 424B4 filing date to the 3rd session after it. The filing date counts when it is a session; when it is not, sessions are counted strictly before and after it.
- Prior bars: any bar more than `prior_bar_gap_bdays` (5) sessions before the filing date means a reused ticker or another security. Only this leaves an event out as `prior_bars`.
- No bar in the window: `late_first_bar` (bars later) or `no_bar`. Both are listed and left out before the lock.
- Where the prospectus cover gives its own date, it is recorded (`prospectus_date`), but the bar rule decides. For the 15 rows without one, `pricing_date` is the filing date; it is used only for the breakpoint lookup, the year table and the 2023-on cut.
- The event list and its SHA-256 are frozen before any return is computed.

MEASURED 2026-11-26 (run before 03:31 UTC) from the prospectus data only (`fetch_23.py --events`, `events_selected.csv` SHA-256 `94bd6fab9faf6cf0f5a0a71b8235b520ebe739c48b61b7fe75117268ad7e89aa`), by pricing year, after the B1 share fix and before the security, share-check and date checks:

| Year | Judged (1.5x or more) | 1.0x to 1.5x | 0.67x to 1.0x |
|---|---|---|---|
| 2017 (from 2017-03-20) | 15 | 9 | 10 |
| 2018 | 23 | 15 | 5 |
| 2019 | 26 | 9 | 8 |
| 2020 | 34 | 9 | 16 |
| 2021 | 82 | 25 | 29 |
| 2022 | 5 | 1 | 2 |
| 2023 | 6 | 3 | 1 |
| 2024 | 12 | 7 | 2 |
| 2025 | 14 | 6 | 8 |
| 2026 (to 2026-10-23) | 14 | 4 | 11 |
| Total | 231 | 88 | 92 |

Moves between bands from the share fix, MEASURED (pass-1 list against this one):

| From | To | Events |
|---|---|---|
| 1.0x to 1.5x | judged | 3: PVTL, GSKY, JAN (a second class was missed) |
| below 0.67x | judged | 3: ONTF, ARXS, MCG |
| below 0.67x | judged, listed, left out | 1: BROS (share total not read) |
| judged | 1.0x to 1.5x | 2: VIA, IBTA (count was doubled) |
| 1.0x to 1.5x | below 0.67x | 2: EIDX, KYTX |
| 1.0x to 1.5x | 0.67x to 1.0x | 1: VITL |
| judged | listed, left out | 2: PYCR (share total not read), Avantor preferred (not common) |
| 0.67x to 1.0x | listed, left out | 1: ZI (share total not read) |

- Other totals fixed without a band move: ATUS, APRN, DASH, VZIO, BLND, HOOD, IOT, RDDT, TTAN, CRWV, CHYM, FIG, NTSK and FLYW were halved; APP, CRCL, SDC, NMRK and TPG went up.
- Share checks, MEASURED: 384 verified by the code, 23 by hand, 4 unverified. The 8 unverified rows just below 0.67x on the old count were also read by hand; MCG and BROS moved up, the other 6 stay below on any reading. The unverified are Dutch Bros 0001628280-21-018784 (judged on its as-exchanged 163,234,263; Class B and C counts not stated in the saved text), PAYCOR 0001193125-21-221948 (judged; the saved text gives only "based on 171,302,784 shares ... outstanding as of June 30, 2021"), ZoomInfo 0001628280-20-009087 (0.67x to 1.0x; Class C named without a count) and the Avantor preferred filing (also not common).
- Security check, MEASURED: one selected filing is not common: Avantor 0001193125-19-150958, priced 2019-05-16, judged group. Its cover reads "18,000,000 Shares Avantor, Inc. 6.250% Series A Mandatory Convertible Preferred Stock". The same day's 0001193125-19-150954 reads "207,000,000 Shares Avantor, Inc. Common Stock. This is an initial public offering of shares of our common stock", and is the one kept. No selected row is an ADS row (the US screen drops those).
- So 228 judged events go to the date checks: 2017 15, 2018 23, 2019 25, 2020 34, 2021 80, 2022 5, 2023 6, 2024 12, 2025 14, 2026 14. Of these, 46 are priced from 2023-01-01 and 16 are mega listings.
- These counts fall after the date checks. The kept counts by first trading year are printed by `fetch_23.py --freeze` and go in the freeze record.

## Bars

- Alpaca daily bars, feed `sip`, adjustment `raw`, through `pplx credentials run` with the handle `custom-cred:2c245581-eef5-452d-8434-2b80a170c040@data.alpaca.markets`. The key is never loaded, printed or stored. End date no later than `bar_end` (2026-11-24).
- Bars stay in `~/workspace/rig/data/replay_23/bars/`, never in the repo.
- SPY daily bars, same feed and adjustment, from `spy_start` (2017-02-01). The SPY bar dates are the session calendar.
- Flat-run scan, as in the stock plans (`research_rig/common_14.py`, `not_trades`; plan 14's wording): a bar with zero volume, or inside a run of `flat_run` (5) or more bars in a row with identical open, high, low and close, is treated as no bar (not a real trade).
- Before the lock the fetcher reads bar dates, volume and that flat flag, and no return (lead's ruling, 2026-11-26). Prices are compared for equality only. `test_23.py` checks this by freezing on files whose open, high, low and close are words, not numbers. So the event list is fully frozen before the run.
- Reused tickers are counted once, as in the stock plans and measurement 15: one listing per CIK and per (ticker, first bar date), the earliest accession kept.

## Trade (fixed by the lead)

- Buy at the first trading day's close (session 1) and sell at the close of the fifth trading day (session `exit_session`, T+4).
- One trade per event, equal dollars. Overlapping trades are allowed and each counts once.
- Judged cost `judged_bps` (10 bps) a side; shown at `shown_bps` (25 bps) and at `no_auction_bps` (50 bps). Net return = exit/entry - 1 - cost x (1 + exit/entry).
- A missing fifth-day bar is not a dropped trade. Exit at a real close inside `exit_window_sessions` (8) sessions and count it.
- Before the lock: an event whose first bar is not a real trade is listed and left out with the reason `entry_not_real_bar`. An event with a real first bar and no real close in sessions 2 to 8 is a refusal (`P23_REFUSED_NO_EXIT_BAR`, with the accession) so the lead can look at it; it is never a silent drop.

## Pass: all eight marks

1. At least `min_trades` (30) trades.
2. Mean net return above 0.
3. t of the mean at least `min_t_stat` (2.0), with t = mean / (sample standard deviation / square root of n).
4. Mean above 0 without the best `drop_best` (3) trades.
5. Median above 0.
6. Positive mean in at least `min_year_share_pct` (60%) of calendar years with `min_year_trades` (3) or more trades.
7. Mean of (net return minus SPY's return over the same closes) above 0, with t at least `min_t_stat`.
8. Mean net above 0 on events priced from `recent_from` (2023-01-01), since the published sample ends in 2022.

Undefined never passes. That covers a zero spread, no counted year, and no trade from 2023 on.

## Shown only

- Entry at the second session's open instead.
- The 1.0x to 1.5x band, and the 0.67x to 1.5x band.
- By year.
- At 25 bps a side.
- At 50 bps a side, for a buyer who cannot use a closing-auction order.
- Without mega listings above $20B.
- First-day close below the offer price versus at or above it.

None of these changes a mark.

## Choices made in the draft (approved by the lead 2026-11-26)

1. Publication date of a breakpoint: the date on CRSP's chart file (the ranking date in `breakpoints.csv`), counted as published on that day. A pricing on that day uses it.
2. "Business days" are sessions in SPY's bar file. If SPY's file does not reach 6 sessions before or 3 after a filing date, the freeze refuses (`P23_CALENDAR_SHORT`).
3. The first trading day comes from the first bar for every event, not only those with an estimated date (now fixed by the lead's B2 rule).
4. Reused tickers:
   - each event's bars are asked for with `asof` = filing date + `asof_days` (5) calendar days, so the feed resolves the ticker to the company holding it then;
   - the file runs from `prior_listing_days` (30) calendar days before the filing date to `fetch_after_days` (40) days after;
   - prior bars are those of the B2 rule (more than 5 sessions before the filing date);
   - the kept 424B4 must be for common shares or ADS (lead's addition; see Events).
5. Exit when the fifth-session bar is missing or not a real trade: the first real close in sessions 6 to 8, else the last real close in sessions 2 to 4.
6. The lead took the second form: the fetcher reads volume and the flat flag before the lock. A first bar that is not real is a pre-lock leave-out; a real first bar with no real close in sessions 2 to 8 is a pre-lock refusal. After the lock either case would mean the files changed, and the run stops with a fixed code (`P23_ENTRY_NOT_REAL_AFTER_FREEZE`, `P23_NO_EXIT_AFTER_FREEZE`); the pins make that unreachable in practice.
7. SPY yardstick: the raw SPY close on the trade's actual entry and exit dates, with no cost charged to SPY. Mark 7 uses the net trade return minus SPY's gross return.
8. Years for mark 6 are calendar years of the first trading day. Mark 8 and the 2023 cut use the pricing date, as the lead wrote.
9. The second-day open cell uses session 2's open when session 2 is a real bar before the exit day; otherwise that event is left out of that cell only.
10. The mega cut and the bands use the stand-in value, not a market price.
11. Confirmed by the lead 2026-11-26: a bar 4 or 5 sessions before the filing date is neither in the window nor a prior bar under B2. Such an event is listed and left out before the lock as `bars_before_window`, since the window's first bar may then not be day 1. It is counted with the other gap lines in the freeze record and on the page.

## Refusals and the one shot

- Refusals before the lock:
  - `fetch_23.py --events` refuses on a 424B4 cover it cannot place (`P23_SECURITY_UNKNOWN`);
  - `fetch_23.py --freeze` refuses on any event with a real first bar and no real close in sessions 2 to 8 (`P23_REFUSED_NO_EXIT_BAR`, with the accessions) and writes no freeze record;
  - `fetch_23.py --fetch`, `fetch_23.py --freeze` and `score_23.py --run` refuse unless HEAD is the lead's approval commit (`P23_NOT_APPROVED`, `common_23.authorize`);
  - `fetch_23.py --freeze` refuses on a config other than `config/thresholds.yaml` or a draft plan (`P23_FREEZE_ON_DRAFT`) and on a short SPY calendar (`P23_CALENDAR_SHORT`);
  - `score_23.py --run` refuses on any pin that differs: freeze record, code, config, `ipos.csv`, `breakpoints.csv`, the cover cache, the selected and frozen event files, or each bar file.
- The freeze record (`freeze.json`) holds the SHA-256 of every code file, this plan, the config block, both event files, the three inputs (`ipos.csv`, `breakpoints.csv`, `snips.jsonl.gz`) and every bar file used. The lead keeps the freeze record's own SHA-256 apart and passes it to the run.
- The run checks every pin, claims `score_23.lock` with exclusive create, checks every pin again, and only then reads a price. A lock that exists means the run is used up. A second run refuses (`P23_ALREADY_USED`). The lock and the result file are written with fsync on the file and its folder. A frozen trade that drops after the lock stops the run (`P23_DROPPED_AFTER_LOCK`).
- The page is written by `report_23.py` from `results_23.json` only. It refuses if the code pins differ, and every number on it comes from the script.

## Calibration on planted paths

MEASURED 2026-11-26 03:31 UTC by `calibrate_23.py` through the same `trade()` and `judge()`:
- Inputs: invented bars, on the 228 judged events' real pricing dates, one event per CIK, so the years and the 2023-on slice have the real shape.
- Each 5-session return has a standard deviation of 15% (t noise with 4 degrees of freedom), a beta of 1.2 to an invented SPY (2% standard deviation over the four returns from session 1 to session 5, so the daily sd is 2% / square root of 4) and a shared shock per calendar year (2%).
- The planted edge is gross, spread over sessions 2 to 5, and judged at 10 bps a side.

| Planted edge a trade | All eight marks | t mark alone | SPY mark alone | 2023-on mark alone |
|---|---|---|---|---|
| 0% | 1 of 20 | 1 | 1 | 15 |
| 1% | 3 of 20 | 4 | 3 | 14 |
| 2% | 6 of 20 | 8 | 7 | 18 |
| 4% | 18 of 20 | 19 | 18 | 20 |

These are invented paths, not a pass rate for real markets. With no edge, 1 world in 20 passed all eight marks: a false pass, near the 1 in 40 a one-sided t of 2 allows. The t and SPY marks bind. An edge near the published 5% would usually be seen; one of 1% to 2% would usually be missed. Full figures are in calibration_23.json in the off-repo run folder (sha256 71f9be0632a8b999a92bccc2bc6e22b3bf1bcc62baff046b7d83b1b86bb89351).

## Limits (to print on the page)

- The size test is a stand-in for CRSP's own share counts and its US, PFIC and float screens. Actual adds are UNKNOWN.
- 424B1 listings and direct listings are missing. ADS rows without a value are missing. Foreign issuers are out through `us_screen_guess`.
- A daily bar's close is the last consolidated trade, not the closing auction print the funds trade in. The 50 bps line is for a buyer who cannot use a closing-auction order.
- Raw bars: a split or dividend inside the five sessions is not adjusted, and SPY's dividend is left out. Both are small over five sessions.
- The common-shares check reads the cover text with fixed patterns; it is not a CUSIP or listing-record match.
- First trading dates come from the feed's first bar inside the filing-date window. A feed that starts a file late would push an event out rather than shift it.
- Share totals come from fixed patterns on saved text plus 23 hand reads; a total the code read wrongly in a way that still matches its class lines would not be caught.
- Power, from the calibration on invented paths: with no edge, 1 world in 20 passed all eight marks (a false pass); at a 2% edge, 6 in 20 passed. This test can miss a small real edge.
- Overlapping trades in hot months (2020-2021) are not independent; the t-statistic is not a probability claim.

## Order of work

1. Done: audit passes 1 and 2 and the pass-2 delta, all CLEAR. No bar yet.
2. Done: this freeze commit moves `replay_23_plan` into `config/thresholds.yaml`, the plan and code into `research_rig/`, pins them in `research_rig/PINNED_23.json` (the config block as `thresholds.yaml#replay_23_plan`), and fills ledger row 160.
3. The lead's approval commit, made on top of the freeze commit, adds `research_rig/APPROVAL_23.md` with exactly this line, naming the freeze commit: "Approved by the lead: plan 23, one collection and one scored run, freeze commit <40-character sha>." It must change no pinned file and no value in `replay_23_plan`.
4. With that approval commit checked out and no tracked change, one light process at `nice -n 10`, from `research_rig/`: `fetch_23.py --events`, then `fetch_23.py --fetch --approval-commit <c>`, then `fetch_23.py --freeze --approval-commit <c>`. Dates, volume and the flat flag only. The lead keeps the freeze SHA-256.
5. One run: `score_23.py --run --approval-commit <c> --freeze-sha256 <sha>`. Then `report_23.py --freeze-sha256 <sha>`.
6. Off-repo inputs, pinned by sha256 (they hold CRSP breakpoint values or offer prices, so they stay off repo): see ledger row 160 and the freeze record.
