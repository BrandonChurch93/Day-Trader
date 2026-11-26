# Count 107: regular dividend-month coverage

MEASURED. **Closed before a plan or replay.** The dated roster supported 83 monthly turns from December 2019 through October 2026. Of those, 78 had at least 20 names on each side in the vendor-based count; the fixed requirement was 120. UNKNOWN. The independent ex-date coverage gate was not measured and did not determine the closure.

STATED before opening issuer or vendor dividend-date records. Ledger 209 fixes the gate at 120 qualifying monthly turns, each with at least 20 predicted names and 20 non-dividend-month peers, and at least 95% vendor coverage against SEC or issuer records for a random sample of 60 name-months. No prices are used.

## Frozen sampling instruction

- STATED. Seed `count-107-ledger-209-v1-66afb7af`. Draw without replacement by ordering the complete point-in-time roster frame by ascending SHA-256 of UTF-8 `seed|YYYY-MM|security_id`, breaking hash ties by the input pair, and take the first 60 unique pairs. Use the filing CUSIP as the security ID where present, or the uppercase whitespace-normalized security name and class from the original filing when CUSIP is not supplied. No date-based pruning, replacements, or redraws.
- STATED. Use the last completed month at count time; carry each holdings snapshot forward only once its report period and publication are strictly earlier than the month-start cutoff. Use lagged SEC schedules of the SPDR S&P 500 ETF Trust (SPY) as the large-cap proxy; no current constituent list as a frame or fallback.
- STATED. For each drawn pair compare exact regular cash ex-dates against issuer or SEC evidence. Do not infer absence from the vendor or from a missing filing. Report confirmed regular-event pairs, fully evidenced no-event pairs, unresolved pairs, and exact matches separately. The event recall denominator is independently confirmed regular-event pairs, not no-event pairs. Unresolved evidence cannot certify the fixed 95% gate.

MEASURED. The seed instruction was recorded before any corporate-action date was read, at 2026-11-26 11:01:25 UTC; its original file SHA-256 was `e1d405e649050c2e3a439b63782553046bcc03cf42bd11562a73a938a0440cb2`. The script drew the 60 pairs before requesting vendor data. The draw covered the usable N-PORT frame only, not the originally intended full window. The lead stopped the independent primary-source check once the roster count failed.

## Dated roster and count

- MEASURED. Select the latest original public SPY NPORT-P report available before each month start; both its report date and its SEC acceptance UTC date must precede the first day. Keep US common-equity rows identified by filing CUSIP. The first usable [N-PORT filing](https://www.sec.gov/Archives/edgar/data/884394/000175272419166260/primary_doc.xml) reported September 30, 2019 and was accepted November 18, 2019 at 20:09:59 UTC ([SPY EDGAR submissions](https://data.sec.gov/submissions/CIK0000884394.json)).
- MEASURED. The January 2016 to October 2026 window contained 130 months, of which 47 lacked a usable keyed roster and 83 had one. The 83 use 28 distinct snapshots and 613 distinct CUSIPs. No later membership list was filled backward. The lagged holdings are a proxy: they do not capture membership moves or trading status between snapshots.
- MEASURED. The [SPY filings](https://data.sec.gov/submissions/CIK0000884394.json) had no N-Q. The legacy SPY [September 2018 N-30D schedule](https://www.sec.gov/Archives/edgar/data/884394/000119312518334730/d613130dn30d.htm), for example, contains names and share classes but no ticker or CUSIP column. Those schedules can show historical names, but this count did not establish the historical name-to-security joins needed to link them to the vendor. Earlier months are not usable under this roster method, not evidence that the stocks or dividends were absent.
- STATED. The count used the lead's 3-, 6-, 9- or 12-month scan on previous regular cash ex-date months. A peer had a regular ex-date within the preceding 12 calendar months but no lag match. Both legs are known from past event dates, not from actual ex-dates in the target month. This is the authors' quarterly or unknown-frequency branch, not their full frequency-specific rule.
- MEASURED. Requests used the [Alpaca corporate-action endpoint](https://docs.alpaca.markets/us/reference/corporateactions-1), filtered to cash dividends and historical CUSIPs, with the incomplete rows option and full pagination. The script kept only rows explicitly marked non-special, used the ex-date rather than the process date, and de-duplicated by CUSIP and ex-date. It found 11,102 distinct regular CUSIP/ex-date pairs for the roster IDs. The earliest returned regular ex-date month for those IDs was June 2019. That is a feature of this pull, not evidence that every name has complete coverage from then on. The vendor does not guarantee when it first ingests an event ([Alpaca](https://docs.alpaca.markets/us/reference/corporateactions-1)); these are reconstructed histories, not historical snapshots of the feed.
- MEASURED. May 2020 to October 2026 supplied the 78 consecutive qualifying count turns, 42 short of the fixed line. The roster alone caps this source at 83 turns even with perfect ex-date coverage. The 5 rostered turns that missed at least one leg are below; early action history is especially thin.

| Month | Predicted names | Peer names |
| --- | ---: | ---: |
| 2019-12 | 17 | 11 |
| 2020-01 | 4 | 24 |
| 2020-02 | 9 | 19 |
| 2020-03 | 18 | 30 |
| 2020-04 | 5 | 131 |

## Coverage sample and custody

- MEASURED. The seed selected 60 distinct pairs from the usable frame. Alpaca had at least one regular ex-date in the target month for 11 pairs. The vendor positives are not a primary-source denominator or a coverage percentage.
- UNKNOWN. None of the sampled pairs was adjudicated against primary records. The number of true events, the number with no event, and exact vendor coverage against primary records are unknown. Coverage is not marked as either passing or failing.
- MEASURED. The serial collection used 44 request starts and 15,348,779 response bytes, below caps of 1,500 starts and 150 MB. It ran at nice 10 with no sudo, and kept the raw files off-repo under `/home/user/workspace/rig/data/count_107/` (directory 0700, files 0600). No price, quotes, or TM07 paths were opened.
- MEASURED. The [count script](count_107.py) reads the saved action records and the filing identity fields. Run `nice -n 10 python3 -B research_rig/count_107.py count` to reproduce the summary without any network calls. Off-repo frame, sample, and output SHA-256 respectively: `c65be549e6434200b8693a45d5b1d2f46afdd4484df0dcdd3836a6c5b8516522`, `5acff3288e6cc185f19477b8e8cc1eb59c273109a46d1c555d97578732dff5a0`, and `6680cb344e3242d311dd7158dddca377f4d407b9baa1f3670a137c94bc353fe8`.

## Source check

- STATED. On printed page 10 of the [authors' September 2011 draft](https://doczz.net/doc/8702723/the-dividend-month-premium-samuel-m.-hartzmark--david-h), quarterly or unknown frequency uses ex-date month lags 3, 6, 9 or 12; semiannual uses 6 or 12; annual uses 12. The draft's US sample ends December 2009 (printed page 9). The [published article record](https://ideas.repec.org/a/eee/jfinec/v109y2013i3p640-660.html) is from 2013; the [Fed-hosted signal reproduction](https://www.federalreserve.gov/econres/feds/files/2021-037pap.pdf) lists its DivSeason reproduction window as 1927 to 2011, not a post-2013 sample.
- UNKNOWN. No separate post-publication US test of the original stock-level spread was found in those sources. The authors' later [AER paper](https://www.aeaweb.org/articles?id=10.1257/aer.20231725) studies aggregate US payment-day flows, not this stock-selection rule. [Kreidl and Scholz](https://link.springer.com/article/10.1057/s41260-021-00215-3) report that the premium holds up after publication in Germany, not in a US test.
- STATED. The [Open-Alpha-Lab results and method](https://raw.githubusercontent.com/Guillain-RDCDE/Open-Alpha-Lab/main/studies/516-dividend-month-premium/docs/results.md) explain both +40.31 bp/month pooled (Welch test) and +52.28 bp/month within firms (one-sample test across names). Both are over January 2000 to May 2026 for 30 large-cap stocks still trading and paying dividends in 2026; no isolated post-2013 number is shown. The method uses yfinance adjusted returns and a calendar month with at least two prior payments in that same month, not the original 3/6/9/12 rule. The published calculation is traceable, but the numbers were not rerun and are not evidence of a post-2013 edge on a point-in-time US universe.

## Closure

- STATED, lead decision. Close queue 107 on the fixed 120-turn line; no Plan or shorter test. Using the queue's own assumed 30.3 bp net edge and 140 bp noise, the script gives 3.65 at 78 turns, below the screen of 4. This is an assumption-based screen, not a new estimate of returns. The full-period survivor study does not supply a clean US post-publication replacement.
- STATED, not started. A later attempt could use an index fund that filed quarterly N-Q schedules before 2019. It would need audited historical name/class-to-security matches without CUSIPs and independent regular ex-date evidence, not a backward copy of the 2019 roster.
