# Plan 66. Third-Friday S&P 500 option settlement, two legs

Status CLOSED BEFORE PRICES.

Closed by the lead agent's ruling on 2026-11-26, before any bar was opened. Ledger 210 fixed that the row closes if synthetic power at the stated edge is under 33%. The +25 bp size is the paper's figure at the settlement print (SOQ), and a brokerage account cannot trade at that print. At a print we can trade, the largest stated size is Martone's +21.9 bp at the SPY open, which gives 29.8% power, under the line. The paper's own traded-open figures are far smaller (+5.11 bp and −2.60 bp, Jan 2024 Table II), and every post-2023 scenario gives under 15%. Using the settlement-print size to keep the row open would mean choosing the one figure that does not apply to this trade. The power table is in the Power section below. The calendar, code and tests stay as the record. `research_rig/score_66.py` was never run in `--validate-inputs` or `--go` mode, and no `PINNED_66.json` or approval file exists.

Queue 108, ledger 210. Author: plan 66 helper. Drafted 2026-11-26 (clock read 11:16 UTC). No real bar was opened and no return on real data was computed in drafting this. The settings marked PENDING RULING below were never ruled on, because the row closed first.

## Fixed in ledger 210 before any bar (copied, not changed)

- Judged series: per expiration, net return of leg 1 (S&P 500 fund, entry-session close to expiration-day open) plus net return of leg 2 (SH, expiration-day open to expiration-day close). $500 a leg, whole shares.
- Every monthly expiration, January 2016 to the last complete one.
- Costs: 2 bp a side, or one cent a share if larger. Four sides.
- All marks required:
  1. at least 120 placed;
  2. mean above zero;
  3. t at least 2;
  4. mean above zero without the best 2 expirations;
  5. at least 7 of 11 years positive;
  6. mean above zero on expirations from October 2023 on.
- If synthetic power at the stated edge is under 33%, the row closes before bars. MEASURED below: 42%, so the row stays open (see Power).

## Source effect

STATED. These are from Baltussen, Terstegge and Whelan, "The Third Friday Price Spike", August 2026 version ([PDF](https://julianterstegge.com/assets/papers/third_friday_price_spike.pdf)).

- The event is the monthly AM-settled SPX option expiration. Settlement uses the Special Opening Quotation (SOQ), which is built from each stock's first trade on its primary exchange (pp. 1, 5, 48-50).
- Weekly and 0DTE options are excluded (p. 6).
- On a holiday, expiration moves to the business day before (p. 8).
- Results for 1992 to 2023, 371 expirations (Table I, p. 33):
  - Thursday close to SOQ: +9.80 bp (t 3.04).
  - SOQ to Friday close: −15.10 bp (t −3.57).
- Post-2011 (p. 34): +10.07 bp and −15.51 bp.

STATED from the January 2024 version, "The Derivative Payoff Bias" ([AFA](https://afajof.org/management/viewp.php?n=98196)):

- Table II, p. 41: SOQ legs +18.54 bp (SD 59.82) and −16.91 bp (SD 84.95).
- At the SPX traded 9:30 open instead, the legs are only +5.11 bp and −2.60 bp (t −0.43).
- Table V, p. 43: the E-mini strategy has SD 104.61 bp per expiration.

STATED from later notes:

- Martone (July 2026, [LinkedIn](https://www.linkedin.com/pulse/third-friday-price-spike-sp-500-true-distortion-anomaly-max-martone-fczac)) measured at SPY's opening trade: intraday −15.16 bp; overnight +6.7 bp in non-quarterly months.
- Quantitativo (June 2025, [post](https://www.quantitativo.com/p/the-derivative-payoff-bias)): ES after September 2023 shows +0.7 bp and −2.6 bp, with t near 0, over 20 events.

UNKNOWN. Whether the effect survives at an ETF opening auction print. The SOQ is not tradable at a single print.

## Expiration calendar

MEASURED from `research_rig/calendar_66.json`. There are 131 expirations, from 2016-01-15 to 2026-11-20; 38 of them fall from October 2023 on. The year counts are 12 for each year from 2016 to 2025, and 11 for 2026.

The rule is the third Friday, or the preceding NYSE session if that Friday is a holiday, checked against the XNYS session list in `research_rig/calendar_25.json`. Four expirations shift to Thursday:

- 2019-04-18 (Good Friday);
- 2022-04-14 (Good Friday);
- 2025-04-17 (Good Friday);
- 2026-06-18 (Juneteenth).

None of the expirations or their entry sessions is an early close.

Exchange sources:

- 2021: [Cboe 2021 calendar](https://cdn.cboe.com/resources/options/Cboe2021OPTIONSCalendar.pdf).
- 2022: [Cboe 2022 calendar](https://cdn.cboe.com/resources/options/Cboe2022OPTIONSCalendar.pdf), which shows April 14 as a Thursday.
- 2023: [Cboe 2023 calendar](https://cdn.cboe.com/resources/options/Cboe2023OPTIONSCalendar.pdf).
- 2024: [OCC memo 53701](https://infomemo.theocc.com/infomemos?number=53701).
- 2025: [OCC memo 55737](https://infomemo.theocc.com/infomemos?number=55737), which shows April 17.
- 2026: [OCC memo 57897](https://infomemo.theocc.com/infomemos?number=57897), which shows June 18.
- 2016 to 2020: UNKNOWN from an exchange document. These dates come from the rule only, because the Cboe PDFs would not load or could not be read here.

Holiday-shifted expirations run from the Wednesday close to the Thursday open, then from the Thursday open to the Thursday close.

## Settings PENDING RULING (author's recommendation first)

S1. Leg 1 fund.

- Recommended: SPY (CUSIP 78462F103) for expirations before 2020-01-24, then SPLG (CUSIP 78464A854) from that date. SPLG trades as SPYM from 2025-10-31 under the same CUSIP.
- STATED reason ([SEC 497K](https://www.sec.gov/Archives/edgar/data/1064642/000119312526034617/d53728d497k.htm)): SPLG tracked the Russell 1000, then the SSGA Large Cap Index, and only from 2020-01-24 the S&P 500.
- STATED ([SEC 497K](https://www.sec.gov/Archives/edgar/data/1064642/000119312525245691/d48050d497k.htm)): the ticker change to SPYM was effective 2025-10-31.
- Identify the fund by CUSIP. A different, earlier SPYM (CUSIP 46144X354) was cash-merged on 2025-03-04 (MEASURED, vendor record).
- Alternatives: SPLG throughout, as a large-cap proxy before 2020; or SPY throughout. SPY placement fails once one share costs more than $500, which is UNKNOWN to me because I viewed no prices.
- The engine encodes the recommendation in `leg1_cusip`.

S2. Open price.

- STATED ([Alpaca FAQ](https://docs.alpaca.markets/us/docs/market-data-faq), [Alpaca staff, May 2024](https://forum.alpaca.markets/t/open-close-daily-bar-prices-vs-open-close-auction-prices-on-primary-exchange/14227)): the daily-bar open is the first valid SIP trade on any venue, not the primary auction.
- Recommended: judge on the NYSE Arca opening print (SIP trade with exchange P and condition O) for the fund sale and the SH purchase. This is the fill a market-on-open order would get. Refuse the expiration if that print is missing.
- Use the Arca closing print (exchange P, condition 6) for both closes. Fall back to the daily-bar close only if the lead rules so.
- Show the daily-bar open and close version without a verdict.
- The engine tag is `OPEN_RULE = "arca_opening_print"`.

S3. Fund ex-dividend on an expiration day.

- MEASURED from vendor records: SPY goes ex on every quarterly expiration in 2016 to 2026. One of these is 2026-06-18, the shifted Thursday.
- The vendor has no SPY record for 2016-03 or 2018-06.
- Under S1, no SPLG ex-date falls on an expiration from 2020-02 on. Before that, SPLG ex-dates were third Fridays from 2017-12 to 2019-12.
- Rule: credit the payout per share to leg 1, because it is held at the entry close. Credit only from a vendor record that matches the issuer's dated distribution history. If the record is missing or disputed, list the date in `unverified_cash` and refuse that expiration (code CASH_UNVERIFIED). Never guess an amount.

S4. SH distributions and splits.

- MEASURED from vendor records: SH ex-dates fall Monday to Thursday, and none is an expiration day. SH paid nothing from mid-2020 to 2022-09.
- SH had reverse splits of 1:2 on 2016-06-24 and 1:4 on 2024-11-07, with the CUSIP changing from 74347B425 to 74349Y753. The 2024 split is STATED in the [ProShares Form 8937](https://www.proshares.com/globalassets/proshares/form-8937/sh_form-8937_12.4.24.pdf).
- Leg 2 is intraday, so a buyer at the open earns no payout. Raw prices on the day are used, so no adjustment is needed.
- A split ex-date on an expiration day refuses that expiration (code SPLIT_ON_EVENT).

S5. Early closes. None in scope (MEASURED, see above). If one appears, refuse the expiration.

S6. Known structural changes, shown and not judged:

- Cboe planned to end trading in expiring AM SPX options at 9:25 ET on expiration day ([notice](https://www.cboe.com/notices/content/?id=55365); [SEC approval](https://www.govinfo.gov/content/pkg/FR-2025-06-16/html/2025-10876.htm)). The effective date is UNKNOWN, and the Cboe FAQ says "TBD".
- Cboe launched AM-settled weekly SPX (SPXO) on 2026-11-09 ([notice](https://www.cboe.com/notices/content/?id=61537)). Only 2026-11-20 in scope is after it.

## Arithmetic

- For each leg: shares = floor(500 / entry price). If that is zero, refuse the expiration (code ZERO_SHARES).
- Cost of a side = max(0.0002 × shares × price, 0.01 × shares).
- Leg return = (shares × (exit − entry + cash per share) − entry side cost − exit side cost) / (shares × entry).
- Judged value = leg 1 return + leg 2 return.
- Statistics: sample variance and a conventional t. Each expiration is assigned to the year of its date. Zero or missing never counts as positive.

Shown only, with no verdict:

- each leg, net and gross;
- quarterly months against other months;
- the four holiday-shifted expirations;
- the daily-bar version (S2).

## Contamination

MEASURED by searching the repo.

- SPY bars have been used before:
  - plan 07: one-minute SPY, rules N1 to N8 on every weekday;
  - plan 06: SPY daily, trend;
  - plan 14: SPY daily, benchmark;
  - plan 31: SPY daily, factor;
  - plan 39: SPY daily, close to close, shown only;
  - plan 41: SPY daily, month end;
  - the timemachine tapes.
- No code or doc in the repo selects third Fridays, or computes Thursday-close to Friday-open or Friday open-to-close returns for SPY, SPLG or SH.
- Plan 07's intraday results pool third Fridays with all other weekdays.
- SH and SPLG bars were never opened by any scorer. SH is named only as a shown variant in ledger 208.
- The author of this draft opened no price data. Vendor corporate-action records (dividends, splits, name changes; no price fields) were read off-repo.

## Power (synthetic, no market data)

MEASURED with `python3 -B research_rig/score_66.py --synthetic` (20,000 runs, seed 66, the 131 pinned dates). It applies all six marks jointly. Every expiration is assumed placed.

Assumptions:

- Noise is normal with an SD of 104.6 bp per expiration (Jan 2024 Table V).
- The edge is gross; the cost is subtracted.

| Scenario | Gross bp | SD bp | Cost bp | Power, all marks | t ≥ 2 | Without best 2 | 7 of 11 years | From Oct 2023 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Stated, +25 gross (+10 overnight, −15 intraday) | 25.0 | 104.6 | 8 | 42.1% | 44.7% | 92.5% | 81.7% | 84.0% |
| Half the stated edge, +12.5 | 12.5 | 104.6 | 8 | 6.1% | 6.6% | 52.6% | 42.5% | 60.2% |
| ETF open (Martone), +21.9 | 21.9 | 104.6 | 8 | 29.8% | 31.9% | 86.6% | 73.7% | 79.1% |
| Post-2023 ES (Quantitativo), +3.3 | 3.3 | 104.6 | 8 | 0.6% | 0.6% | 17.0% | 15.5% | 38.9% |
| +25 before Oct 2023, +3.3 from Oct 2023 | 25.0 | 104.6 | 8 | 14.0% | 20.1% | 77.4% | 62.4% | 38.9% |
| Stated, SD 103.9 (Table II legs) | 25.0 | 103.9 | 8 | 42.6% | 45.2% | 92.7% | 82.0% | 84.2% |
| Stated, SD 125.5 (1.2x stress) | 25.0 | 125.5 | 8 | 30.8% | 32.9% | 87.3% | 74.3% | 79.5% |
| Stated, cost 12 bp (cent rule stress) | 25.0 | 104.6 | 12 | 26.5% | 28.4% | 84.4% | 71.1% | 77.6% |
| Stated, Student t 5 df tails | 25.0 | 104.6 | 8 | 43.2% | 46.1% | 91.5% | 82.9% | 84.3% |
| Zero edge | 0.0 | 104.6 | 8 | 0.2% | 0.3% | 9.4% | 9.2% | 31.5% |

Reading of the table:

- At the paper's settlement-print size (+25 bp), power is 42.1%. That size cannot be traded from a brokerage account, so it does not decide the gate (see Status).
- At Martone's ETF-open size (+21.9 bp), power is 29.8%, which is under the gate. The paper's edge is measured at the SOQ, not at an ETF print.
- Half of it, and the post-2023 size, do not.
- If the SH one-cent rule raises total cost to about 12 bp, power at the stated edge falls below 33%. Whether that happens depends on SH share prices, which I have not seen.

## Data and one-shot run

- Private inputs live in `/home/user/workspace/rig/data/plan66_inputs`. The directory is 0700 and holds exactly three files, each 0600:
  - `manifest.json`: schema 1, mode `plan66_marks`, feed `sip`, adjustment `raw`, the open rule, `collected_utc` after 2026-11-20, and SHA-256 hashes of the other two files.
  - `marks.json`: one row per expiration with the fields `expiration`, `fund_cusip`, `sh_cusip`, `fund_entry_close`, `fund_open`, `sh_open` and `sh_close`. A null field is refused.
  - `actions.json`: entries for the four CUSIPs, each with an HTTPS `source`, `cash` rows of the form `{id, ex_date, amount}`, `unverified_cash` dates and `splits` dates.
- No price or payout goes in Git.
- `--validate-inputs --input-sha256 <pin>` prints each expiration date with PLACED or a refusal code, plus the counts. It prints no price, share count or return, and needs no approval.
- `--go` needs `research_rig/APPROVAL_66.md`, added alone in a commit descended from the freeze, with exactly this line:

```text
Approved by the lead: plan 66, validation and one scored run, freeze commit <commit>, freeze SHA-256 <freeze>, input SHA-256 <input>.
```

- Before reading any input, it checks the pins in `PINNED_66.json` (written at freeze), ledger 210, queue 108, a clean environment and an empty 0700 `/home/user/workspace/rig/data/replay_66`.
- It writes `score_66.lock`, then `results_66.json`, once. An error after the lock consumes the run.

```sh
env -i PATH=/usr/bin:/bin LC_ALL=C /usr/bin/python3 -I -B research_rig/score_66.py --validate-inputs --input-sha256 <input>
env -i PATH=/usr/bin:/bin LC_ALL=C /usr/bin/python3 -I -B research_rig/score_66.py --go --approval-commit <approval> --freeze-sha256 <freeze> --input-sha256 <input>
```
