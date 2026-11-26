# E04 muni_cef_january_watch

Status: manual forward watch for queue row 86, ready before December 10, 2026. Pretend money only: no orders, no broker link, no automation. It follows [Plan 48](../../research_rig/PREREG_48_muni_cef_tax_loss.md) exactly and runs whatever the Plan 48 back-test says. It is not one of the ten judged turns, and one turn proves nothing on its own.

## Dates

All dates are subject to the [official NYSE holiday calendar](https://ir.theice.com/press/news/details/2024/NYSE-Group-Announces-2025-2026-and-2027-Holiday-and-Early-Closings-Calendar/default.aspx); recheck it on December 10.

| Step | Session | Clock |
|---|---|---|
| Ranking base | Fri 2026-01-02 | close |
| Formation | Wed 2026-12-30 | close |
| Pretend entry | Thu 2026-12-31 | close |
| Shown-only exit | Fri 2027-01-08 (5th January session) | close |
| Judged exit | Fri 2027-01-29 (last January session) | close |

## By December 10

1. Take all 2026 rows (71, point-in-time active) of the roster (/home/user/workspace/rig/inventories/row86_muni_cef_roster.csv, from the [SEC 2026 closed-end fund file](https://www.sec.gov/files/investment/data/other/closed-end-fund-information/closed-end-investment-company-2026.csv)). Freeze that ticker list by writing its SHA-256 into the log below. No ticker is added after that.
2. Recheck the session dates above against the NYSE calendar.
3. Create /home/user/workspace/rig/data/forward_e04 (mode 0700) for private records. Prices, quotes and amounts stay there, never in the repository.

## Formation, Wed 2026-12-30, after the close

1. For each frozen ticker read raw SIP daily bars from 2026-01-02 through 2026-12-30. A fund missing any session, or with a split whose ex-date is after 2026-01-02 and on or before 2026-12-31, is not eligible. Check splits from issuer, exchange or SEC records.
2. Price return = close on 2026-12-30 over close on 2026-01-02. Rank lowest first; ties by ticker.
3. Write the ranked list privately, with its SHA-256 in the log, before the entry session opens.

## Entry, Thu 2026-12-31

1. Read SIP quotes from 15:53:00 to 15:59:00 New York time for the ranked funds and MUB. Half-spread is the plan 36 duration-weighted median over 15:54:00 to 15:59:00, 60 second expiry, 180 seconds coverage; otherwise use the 50 bp proxy. Add 5 bp a side.
2. Walk down the ranked list. A fund is held if one whole share at its 2026-12-31 close plus cost fits in $100 and it has a 2026-12-31 bar. Stop at five.
3. Pretend shares = largest whole count that fits $100 each. MUB: largest whole count that fits $500.
4. Write the five tickers, share counts and cost sides privately; log the hash.

## During January

Record every distribution with an ex-date after 2026-12-31 and on or before the exit, from a dated issuer or exchange notice, with its URL. A December 31 ex-date is not credited. A split of a held fund in January changes its share count from the ex-date.

## Exits

1. Fri 2027-01-08 close: shown-only result, priced the same way.
2. Fri 2027-01-29 close: judged result. Exit cost per side is the larger of the entry and exit half-spread plus 5 bp. A fund with no bar that day is valued at its last close, charged the larger of its entry half-spread and 50 bp plus 5 bp, and kept.
3. Report the five-fund net return on $500, MUB on $500, and the equal-weight mean of all eligible funds, each labeled MEASURED, in the log.

## Log

The public log holds only dates, ticker counts, hashes of private files and the three final returns in percent. It is created at the first record and given an INDEX row then.
