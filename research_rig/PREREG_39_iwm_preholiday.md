# Plan 39. IWM for the US pre-holiday session

Status FROZEN.

Queue 65, ledger 174. This is one strategy, not the original stock-index portfolio. No return on a real bar was computed in preparing or auditing this freeze. Only the lead may make a separate approval commit and run the scorer, once.

## Published effect and exact comparison

- **STATED:** Ko and Yang, p. 2 (physical PDF p. 3): “We follow Ariel (1990) by considering eight holidays: (1) New Year’s Day, (2) Presidents’ Days, (3) Good Friday, (4) Memorial Day, (5) July Fourth, (6) Labor Day, (7) Thanksgiving, and (8) Christmas.” P. 1 (physical PDF p. 2): “We extend Ariel’s (1990) sample to December 2019.” P. 3 (physical PDF p. 4) gives 296 pre-holidays for 1983–2019 and the last one as December 24, 2019, an early-close session according to the NYSE calendar. Ko and Yang do not specify a separate early-close exclusion or special intraday mark; the listed end date shows they did not exclude all shortened sessions. See [Ko and Yang, pp. 1–3](https://cfr.ivo-welch.info/published/papers/ko2021pre.pdf#page=3) and [NYSE's 2018–2020 calendar](https://ir.theice.com/press/news-details/2017/NYSE-Group-Announces-2018-2019-and-2020-Holiday-and-Early-Closings-Calendar/default.aspx).
- **STATED:** Ariel, Section I and pp. 1615–1617: “the close of trading on the second day prior to holidays to the close of trading on pre-holidays.” Its shortened-session note applies to the hourly DJIA series, not a deletion from the daily CRSP test: “The New York Stock Exchange observed shortened trading hours on some days in the sample so hourly DJIA index levels were converted to returns” using open-to-first-observation and last-observation-to-close endpoints. Ariel's primary sample was 1963–1982; his calendar did not distinguish holidays generating an extra closing from those that did not. Plan 39 deliberately uses actual official full closure dates only, adds MLK Day, Juneteenth from 2022 and both named mourning days, and counts their previous open session including any early closes. This is not an exact original-calendar reproduction. See [Ariel, Sections I and II.D and Table II](https://onlinelibrary.wiley.com/doi/full/10.1111/j.1540-6261.1990.tb03731.x).
- **MEASURED by authors:** The 1983–2019 average pre-holiday daily return is 0.37% for the broad CRSP equal-weight index, which gives smaller firms more weight than a cap-weighted index; it is not a stand-alone equal-weight small-cap ETF return or a 37 bps estimated net premium. The value-weight CRSP counterpart is 0.14%; VW, DJIA and S&P 500 differences are insignificant in the post-1990 evidence. IWM tracks the float-adjusted cap-weighted Russell 2000, not the CRSP equal-weight index. It could carry materially less of the effect or none. See [Ko and Yang, pp. 3–4 and Table 1](https://cfr.ivo-welch.info/published/papers/ko2021pre.pdf#page=4) and [IWM prospectus](https://www.ishares.com/us/literature/summary-prospectus/sp-ishares-russell-2000-etf-3-31.pdf).

## Official NYSE calendar and event dates

STATED. The pinned calendar transcribes the official full closures and 13:00 ET shortened cash-equity sessions, not bank holidays, ordinary weekends or futures hours. Full regular holidays and announced special closures qualify; unscheduled intraday interruptions, trading halts, or early closes alone do not. December 31, 2021 remained open because January 1, 2022 was a Saturday without an observed NYSE closure; June 2021 had no NYSE Juneteenth closure. Sources: [NYSE 2016–2017 releases](https://ir.theice.com/press/news-details/2016/NYSE-Group-Announces-2017-Holiday-and-Early-Closings-Calendar/default.aspx), [2018–2020](https://ir.theice.com/press/news-details/2017/NYSE-Group-Announces-2018-2019-and-2020-Holiday-and-Early-Closings-Calendar/default.aspx), [2021](https://ir.theice.com/press/news-details/2020/NYSE-Group-Announces-2021-2022-and-2023-Holiday-and-Early-Closings-Calendar/default.aspx), [2022–2024](https://ir.theice.com/press/news-details/2021/NYSE-Group-Announces-2022-2023-and-2024-Holiday-and-Early-Closings-Calendar/default.aspx), [2025–2026](https://ir.theice.com/press/news-details/2024/NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx), and NYSE notices for [George H. W. Bush](https://ir.theice.com/press/news-details/2018/New-York-Stock-Exchange-to-Honor-President-George-H-W-Bush/default.aspx) and [Jimmy Carter](https://ir.theice.com/press/news-details/2024/The-New-York-Stock-Exchange-Will-Close-Markets-on-January-9-to-Honor-the-Passing-of-Former-President-Jimmy-Carter-on-National-Day-of-Mourning/default.aspx). The two mourning closures were known before the December 3, 2018 and January 7, 2025 entry closes.

MEASURED from calendar metadata only. The reconstructed common grid matches all 2,723 dates in the Plan 25 XNYS snapshot for 2016-01-04 through 2026-10-30. There are 103 included-range full closure dates, of which 102 generate eligible exit dates. January 1, 2016 would exit December 31, 2015, outside scope and before the Plan 25 SIP history boundary; the first control interval ends January 5, 2016 without a December 2015 mark. July 3, 2020 and July 3, 2026 are full closures, so the exits are July 2. Early-close exits are marked “*” and use that session's close; the two mourning exits are marked “†”. Assign year and sample by exit date, so a December exit can precede a January closure. All 102 are after Ariel's sample; 37 overlap Ko and Yang's extension and 65 exit after it (January 2020 onward).

| Exit year | Pre-holiday exit sessions (MM-DD) | Count | Ko and Yang |
| --- | --- | ---: | --- |
| 2016 | 01-15, 02-12, 03-24, 05-27, 07-01, 09-02, 11-23, 12-23, 12-30 | 9 | overlap |
| 2017 | 01-13, 02-17, 04-13, 05-26, 07-03*, 09-01, 11-22, 12-22, 12-29 | 9 | overlap |
| 2018 | 01-12, 02-16, 03-29, 05-25, 07-03*, 08-31, 11-21, 12-04†, 12-24*, 12-31 | 10 | overlap |
| 2019 | 01-18, 02-15, 04-18, 05-24, 07-03*, 08-30, 11-27, 12-24*, 12-31 | 9 | overlap |
| 2020 | 01-17, 02-14, 04-09, 05-22, 07-02, 09-04, 11-25, 12-24*, 12-31 | 9 | after sample |
| 2021 | 01-15, 02-12, 04-01, 05-28, 07-02, 09-03, 11-24, 12-23 | 8 | after sample |
| 2022 | 01-14, 02-18, 04-14, 05-27, 06-17, 07-01, 09-02, 11-23, 12-23, 12-30 | 10 | after sample |
| 2023 | 01-13, 02-17, 04-06, 05-26, 06-16, 07-03*, 09-01, 11-22, 12-22, 12-29 | 10 | after sample |
| 2024 | 01-12, 02-16, 03-28, 05-24, 06-18, 07-03*, 08-30, 11-27, 12-24*, 12-31 | 10 | after sample |
| 2025 | 01-08†, 01-17, 02-14, 04-17, 05-23, 06-18, 07-03*, 08-29, 11-26, 12-24*, 12-31 | 11 | after sample |
| 2026 through October | 01-16, 02-13, 04-02, 05-22, 06-18, 07-02, 09-04 | 7 | after sample |

## Trade, payouts and all required marks

STATED. Buy one unlevered long IWM position at the raw SIP close of the second open session before a full closure and sell at the raw SIP close of the last open session before that closure. Hold one close-to-close interval, cash otherwise; no overnight position across the actual holiday, no shorting, no reinvestment or return on idle cash. Both sides use their own session's scheduled close, including 13:00 ET early closes. Use each fund's dated issuer cash payout per share on the exit ex-date only. The buyer at the prior close earns it; a payout on the entry session does not qualify. Compare raw closes without forward adjustment. Refuse an unexpected split/other noncash action until the plan is refrozen; do not silently ignore it.

STATED. At side rate f = bps/10,000, trade return = (sell close × (1 − f) + qualifying cash) / (buy close × (1 + f)) − 1. Judge at 2 bps per side. Report IWM at 5 and 10 and SPY on the identical dates at 2 bps per side, shown only. For the holiday contrast, following Plan 25, compare gross cash-inclusive IWM daily returns for the 102 pre-holiday exit intervals with the 2,620 other in-range intervals, with no cost on either side of this calendar-return comparison. It is not a claim that one would trade every comparator day. Allocation among marks or alternative controls is not selected from outcomes.

Require every mark:

1. At least 80 completed events.
2. Mean net IWM return strictly above zero.
3. One-sample t on the net series at least 2.0.
4. Net mean strictly above zero after removing the three best net events.
5. Mean net strictly above zero in the post-2019 events, by exit date.
6. Gross pre-holiday mean minus gross other-session mean strictly above zero and Welch t at least 2.0.
7. Net mean strictly above zero in at least 60% of the eleven calendar years (at least seven, including partial 2026). Zero or missing never counts as positive.

Use sample variance, conventional t statistics and equal weight per interval. A zero or undefined standard error fails the relevant t mark. Report both source-era slices and every calendar year's judged net count, mean and t. SPY and other costs get no verdict. The test is descriptive, has no serial-dependence correction and does not adjust the calendar contrast for weekday or year-end. Costs are fixed assumptions, not empirical fills. A consolidated SIP close is a proxy, not evidence of a primary closing auction fill; taxes, cash yield and other costs are not modeled. See [Alpaca historical bars](https://docs.alpaca.markets/us/reference/stockbars) and [Alpaca market-data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq).

## Data and one-shot authorization

- **Private inputs:** Fixed directory `/home/user/workspace/rig/data/plan39_inputs` (0700) with exactly four regular owner-only 0600 files: `manifest.json`, `IWM.json`, `SPY.json`, `cash_actions.json`. Bars use raw SIP daily marks from 2016-01-04 through 2026-10-30, each row exactly `{t,o,h,l,c,v}`, with positive finite ordered OHLC, positive volume, New York midnight clock, complete ordered joint grid, no missing or extra sessions, and no five consecutive identical OHLC tuples. No trade or payout values in Git.
- **Manifest:** Schema 1, `mode: raw_dated_distributions`, `feed: sip`, `adjustment: raw`, exact ISO `start` and `end`, RFC3339 UTC `collected_utc` with Z, and `files` mapping the three payload names to lowercase SHA-256. Cash packet: schema 1, exact `coverage_start` and `coverage_end`, `funds` for IWM/SPY, each with HTTPS `source`, `splits: []`, `cash` rows exactly `{id,ex_date,amount}`. Independent review of full issuer coverage, all cash categories and no splits or other relevant noncash actions is required; totals and histories come from [iShares IWM](https://www.ishares.com/us/products/239710/ishares-russell-2000-etf) and [State Street SPY](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy). A source URL or empty splits list alone does not prove coverage. Freeze the actions digest separately from the input manifest.
- **Code and approval:** `PINNED_39.json` hashes this plan, the official calendar, numerical engine, runner and synthetic tests. The lead adds only `research_rig/APPROVAL_39.md` in a separate commit descended from the freeze, with exactly the line below and a final newline. Run in that exact clean approval commit. The runner validates approval, pinned current and committed bytes, ledger 174, queue 65, clean environment and private input paths before opening any market packet. The config mirror is documentation; no environment variable alters the frozen settings or directories.

```text
Approved by the lead: plan 39, validation and one scored run, freeze commit <commit>, freeze SHA-256 <freeze>, input SHA-256 <input>, cash actions SHA-256 <actions>.
```

In the approved worktree at repository root, substitute those exact hashes. The first command performs byte and schema validation only and emits metadata counts; it neither claims a run nor computes a return. After reviewing its output, only the lead may invoke the second. It takes and syncs an exclusive lock before any return is computed, and atomically publishes the private result without overwriting. An error after locking consumes the run; do not remove the lock, retry under a different directory, or construct another approval for the same attempt.

```sh
env -i PATH=/usr/bin:/bin LC_ALL=C /usr/bin/python3 -I -B research_rig/score_39.py --validate-inputs --approval-commit <approval> --freeze-sha256 <freeze> --input-sha256 <input> --actions-sha256 <actions>
env -i PATH=/usr/bin:/bin LC_ALL=C /usr/bin/python3 -I -B research_rig/score_39.py --go --approval-commit <approval> --freeze-sha256 <freeze> --input-sha256 <input> --actions-sha256 <actions>
```

The custodian provisions the empty private 0700 run directory `/home/user/workspace/rig/data/replay_39` before scoring; validation does not use or require it. The lock is `score_39.lock` and the one private result is `results_39.json`. Both modes report the number of early-close exits; it is not a separate return arm.
