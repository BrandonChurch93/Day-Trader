# Notes on the Kenneth French data files

> Note added 2026-11-25. These notes were written beside the downloaded files on the research machine, and "this folder", `download_log.txt`, the zips and `REPORT.md` below refer to that download. None of those files are in the repo. To get the two files replay 05 uses, run `python3 fetch_french.py` from `research_rig/`. It writes them to `research_rig/data/french/`, which git ignores. Only those two files are read by any script. Every other file listed below, including the `aqr/` and `shiller/` files, was downloaded for possible use and has not been used in a test. What follows is still the right description of where the data comes from and how each file is laid out.

All files in this folder were downloaded on 2026-11-25 (UTC) with plain HTTPS requests, no key and no login. Download times are in `download_log.txt`. Each Kenneth French file is kept three ways: the original zip, the unzipped original CSV (in `french/`), and one tidy CSV per section (in `french/clean/`, first row = header, first column `date` as YYYYMMDD, values copied as they are, missing codes left in place).

## Kenneth French Data Library files

Common layout for every French CSV (MEASURED from the files):

- A text preamble at the top, then one or more sections. Each section has a title line (for example "Average Value Weighted Returns -- Daily"), then a header line that starts with a comma, then data rows `YYYYMMDD, v1, v2, ...`. Sections are separated by blank lines. The last line is "Copyright 2026 Eugene F. Fama and Kenneth R. French".
- Units: percent per day (1.23 means +1.23 percent that day). Returns include dividends: the library home page says that since the January 2025 release "monthly returns are compounded daily returns with dividends reinvested on their ex-dates" (CRSP CIZ format).
- Missing values: -99.99 or -999 (stated in each file header). Treat both as missing.
- Built from the 202609 CRSP database, so every file ends 2026-09-30. Average Firm Size sections are in millions of dollars (STATED by the library, not checked here).
- The library rebuilds full history each update, so old values can change slightly between downloads.

Line numbers below are 1-based in the original CSV. "Skip rows" means read the section by skipping `header_line - 1` rows and reading `rows` rows, or simply use the tidy file in `french/clean/`.

### F-F_Research_Data_Factors_daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:04Z
- Units: percent per day, total return. Missing codes -99.99 / -999.
- Notes: Columns Mkt-RF, SMB, HML, RF. Market return = Mkt-RF + RF. RF is the daily simple rate that compounds to the 1-month T-bill rate (Ibbotson through 2024-05, ICE BofA US 1-Month Treasury Bill Index from 2024-06), as the file header says.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| compounds to 1-month TBill rate. The 1-month TBill rate data until 202405 are from Ibbotson Associates. Starting from 202406, the 1-month TBill rate is from ICE BofA US 1-Month Treasury Bill Index. | 5 | 6-26343 | 26338 | 19260701 | 20260930 | 4 | 0 | `french/clean/F-F_Research_Data_Factors_daily__main.csv` |

### 49_Industry_Portfolios_Daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/49_Industry_Portfolios_daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:05Z
- Units: percent per day, total return. Missing codes -99.99 / -999.
- Notes: Use section 0 (value-weighted). Several industries start late and are -99.99 before they start: Soda, FabPr, Guns, Gold from 1963-07-01; Softw from 1965-07-01; Hlth from 1969-07-01; Rubbr from 1930-07-01; Paper from 1929-07-01; PerSv from 1927-07-01. Single missing days: Toys 1930-08-22 and 1941-07-12, Books 1927-05-17, MedEq 1933-08-04, LabEq 1945-06-29. 67,250 missing cells per section in total.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 10 | 11-26348 | 26338 | 19260701 | 20260930 | 49 | 67250 | `french/clean/49_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26352 | 26353-52690 | 26338 | 19260701 | 20260930 | 49 | 67250 | `french/clean/49_Industry_Portfolios_Daily__1_Average_Equal_Weighted_Returns_Daily.csv` |

### 10_Portfolios_Prior_12_2_Daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Portfolios_Prior_12_2_Daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:05Z
- Units: percent per day, total return. Missing codes -99.99 / -999.
- Notes: Deciles sorted daily on prior return from day -250 to day -21 (columns Lo PRIOR ... Hi PRIOR). Starts 1926-11-03 because it needs a year of history.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 10 | 11-26247 | 26237 | 19261103 | 20260930 | 10 | 0 | `french/clean/10_Portfolios_Prior_12_2_Daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26251 | 26252-52488 | 26237 | 19261103 | 20260930 | 10 | 0 | `french/clean/10_Portfolios_Prior_12_2_Daily__1_Average_Equal_Weighted_Returns_Daily.csv` |

### 6_Portfolios_2x3_Daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/6_Portfolios_2x3_daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:06Z
- Units: percent per day, total return. Missing codes -99.99 / -999.
- Notes: Columns SMALL LoBM, ME1 BM2, SMALL HiBM, BIG LoBM, ME2 BM2, BIG HiBM. Sections 2 and 3 are number of firms and average firm size (not returns).

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 19 | 20-26357 | 26338 | 19260701 | 20260930 | 6 | 0 | `french/clean/6_Portfolios_2x3_Daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26361 | 26362-52699 | 26338 | 19260701 | 20260930 | 6 | 0 | `french/clean/6_Portfolios_2x3_Daily__1_Average_Equal_Weighted_Returns_Daily.csv` |
| Number of Firms in Portfolios | 52703 | 52704-79041 | 26338 | 19260701 | 20260930 | 6 | 0 | `french/clean/6_Portfolios_2x3_Daily__2_Number_of_Firms_in_Portfolios.csv` |
| Average Firm Size | 79045 | 79046-105383 | 26338 | 19260701 | 20260930 | 6 | 0 | `french/clean/6_Portfolios_2x3_Daily__3_Average_Firm_Size.csv` |

### F-F_Research_Data_5_Factors_2x3_daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:05Z
- Units: percent per day, total return. Missing codes -99.99 / -999.
- Notes: Columns Mkt-RF, SMB, HML, RMW, CMA, RF. Starts 1963-07-01.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| compounds to 1-month TBill rate. The 1-month TBill rate data until 202405 are from Ibbotson Associates. Starting from 202406, the 1-month TBill rate is from ICE BofA US 1-Month Treasury Bill Index. | 5 | 6-15923 | 15918 | 19630701 | 20260930 | 6 | 0 | `french/clean/F-F_Research_Data_5_Factors_2x3_daily__main.csv` |

### F-F_Momentum_Factor_daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:05Z
- Units: percent per day, total return. Missing codes -99.99 / -999.
- Notes: One column, Mom (high minus low prior-return, -250 to -21 days).

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Missing data are indicated by -99.99 or -999. | 14 | 15-26251 | 26237 | 19261103 | 20260930 | 1 | 0 | `french/clean/F-F_Momentum_Factor_daily__main.csv` |

### 5_Industry_Portfolios_Daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/5_Industry_Portfolios_daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:06Z
- Units: percent per day, total return. Missing codes -99.99 / -999.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 10 | 11-26348 | 26338 | 19260701 | 20260930 | 5 | 0 | `french/clean/5_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26352 | 26353-52690 | 26338 | 19260701 | 20260930 | 5 | 0 | `french/clean/5_Industry_Portfolios_Daily__1_Average_Equal_Weighted_Returns_Daily.csv` |

### 10_Industry_Portfolios_Daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:06Z
- Units: percent per day, total return. Missing codes -99.99 / -999.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 10 | 11-26348 | 26338 | 19260701 | 20260930 | 10 | 0 | `french/clean/10_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26352 | 26353-52690 | 26338 | 19260701 | 20260930 | 10 | 0 | `french/clean/10_Industry_Portfolios_Daily__1_Average_Equal_Weighted_Returns_Daily.csv` |

### 12_Industry_Portfolios_Daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/12_Industry_Portfolios_daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:06Z
- Units: percent per day, total return. Missing codes -99.99 / -999.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 10 | 11-26348 | 26338 | 19260701 | 20260930 | 12 | 0 | `french/clean/12_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26352 | 26353-52690 | 26338 | 19260701 | 20260930 | 12 | 0 | `french/clean/12_Industry_Portfolios_Daily__1_Average_Equal_Weighted_Returns_Daily.csv` |

### 30_Industry_Portfolios_Daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/30_Industry_Portfolios_daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:07Z
- Units: percent per day, total return. Missing codes -99.99 / -999.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 10 | 11-26348 | 26338 | 19260701 | 20260930 | 30 | 0 | `french/clean/30_Industry_Portfolios_Daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26352 | 26353-52690 | 26338 | 19260701 | 20260930 | 30 | 0 | `french/clean/30_Industry_Portfolios_Daily__1_Average_Equal_Weighted_Returns_Daily.csv` |

### 6_Portfolios_ME_Prior_12_2_Daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/6_Portfolios_ME_Prior_12_2_Daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:07Z
- Units: percent per day, total return. Missing codes -99.99 / -999.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 12 | 13-26249 | 26237 | 19261103 | 20260930 | 6 | 0 | `french/clean/6_Portfolios_ME_Prior_12_2_Daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26253 | 26254-52490 | 26237 | 19261103 | 20260930 | 6 | 0 | `french/clean/6_Portfolios_ME_Prior_12_2_Daily__1_Average_Equal_Weighted_Returns_Daily.csv` |

### 25_Portfolios_5x5_Daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/25_Portfolios_5x5_Daily_CSV.zip
- Download time (UTC): 2026-11-25T07:27:07Z
- Units: percent per day, total return. Missing codes -99.99 / -999.
- Notes: One missing cell in each return section: SMALL LoBM on 1933-08-04.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 19 | 20-26357 | 26338 | 19260701 | 20260930 | 25 | 1 | `french/clean/25_Portfolios_5x5_Daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26361 | 26362-52699 | 26338 | 19260701 | 20260930 | 25 | 1 | `french/clean/25_Portfolios_5x5_Daily__1_Average_Equal_Weighted_Returns_Daily.csv` |
| Number of Firms in Portfolios | 52703 | 52704-79041 | 26338 | 19260701 | 20260930 | 25 | 0 | `french/clean/25_Portfolios_5x5_Daily__2_Number_of_Firms_in_Portfolios.csv` |
| Average Firm Size | 79045 | 79046-105383 | 26338 | 19260701 | 20260930 | 25 | 0 | `french/clean/25_Portfolios_5x5_Daily__3_Average_Firm_Size.csv` |

### Portfolios_Formed_on_ME_daily.csv

- Source URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/Portfolios_Formed_on_ME_Daily_CSV.zip
- Download time (UTC): 2026-11-25T07:32:13Z
- Units: percent per day, total return. Missing codes -99.99 / -999.
- Notes: Size groups: column "<= 0" is always -99.99 (not used); then Lo 30/Med 40/Hi 30, quintiles, deciles by NYSE market-cap breakpoints.

| Section | Header line | Data lines | Rows | First date | Last date | Columns | Missing cells | Tidy file |
|---|---|---|---|---|---|---|---|---|
| Average Value Weighted Returns -- Daily | 13 | 14-26351 | 26338 | 19260701 | 20260930 | 19 | 26338 | `french/clean/Portfolios_Formed_on_ME_daily__0_Average_Value_Weighted_Returns_Daily.csv` |
| Average Equal Weighted Returns -- Daily | 26355 | 26356-52693 | 26338 | 19260701 | 20260930 | 19 | 26338 | `french/clean/Portfolios_Formed_on_ME_daily__1_Average_Equal_Weighted_Returns_Daily.csv` |

## AQR Time Series Momentum files

### aqr/Time-Series-Momentum-Factors-Monthly.xlsx
- Source URL: https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Time-Series-Momentum-Factors-Monthly.xlsx (linked from https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Factors-Monthly)
- Download time (UTC): 2026-11-25T07:29:09Z
- Layout: sheets "TSMOM Factors", "Definitions", "Data Sources", "Disclosures". On "TSMOM Factors", rows 1 to 17 are notes, row 18 is the header (first cell blank, then TSMOM, TSMOM^CM, TSMOM^EQ, TSMOM^FI, TSMOM^FX), data from row 19. Column A is a month-end date.
- Units: decimal monthly excess return (0.043 = 4.3 percent over the T-bill rate). Long/short futures portfolios across 58 instruments, not US stocks only. TSMOM^EQ is the equity index sleeve (global, not US only).
- Rows: 497 months, 1985-01-31 to 2026-05-29. No blank cells in the data block.
- Tidy copy: `aqr/Time-Series-Momentum-Factors-Monthly.csv` (date as YYYY-MM-DD).

### aqr/Time-Series-Momentum-Original-Paper-Data.xlsx
- Source URL: https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Time-Series-Momentum-Original-Paper-Data.xlsx
- Download time (UTC): 2026-11-25T07:29:09Z
- Layout: sheet "TSMOM factors", rows 1 to 10 notes, row 11 header (DATE, TSMOM, TSMOM^EQ, TSMOM^FX, TSMOM^FI, TSMOM^CM), data from row 12. Note the column order differs from the updated file.
- Units: decimal monthly excess return. Rows: 300 months, 1985-01-31 to 2009-12-31 (frozen paper sample).
- Tidy copy: `aqr/Time-Series-Momentum-Original-Paper-Data.csv`.

## Shiller monthly US stock market data

### shiller/ie_data.xls
- Source URL: https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/downloads/249997aa-1eef-4237-93ec-2d319f7881ab/ie_data.xls?ver=1794837439406 (the "ie_data.xls" link on https://shillerdata.com/, which Shiller's Yale page http://www.econ.yale.edu/~shiller/data.htm points to)
- Download time (UTC): 2026-11-25T07:29:57Z
- Layout: sheets "Disclaimer" and "Data". On "Data", rows 1 to 8 are a multi-line header, data from row 9, last row (1880) is a footnote ("Nov price is Nov 12th close", "Oct/Nov CPI estimated", "Nov GS10 is Nov 12th value"). Date column is YYYY.MM as a number (2026.1 means October 2026). Columns N and P are empty spacers. "NA" appears in CAPE columns for the first 10 years; the last months have blank D and E (not yet reported) and blank forward-return columns.
- Units: P = S&P Composite level, monthly average of daily closes (not month-end). D and E = annualized dividends and earnings per index unit. CPI index level. GS10 percent per year. Real price, real total return price (dividends reinvested), CAPE, TR CAPE. Column R (Monthly_Total_Bond_Returns) is a gross monthly return (1.004 = +0.4 percent); column S (Real_Total_Bond_Returns) behaves like a real index level starting at 1.0. D and E being four-quarter totals is STATED on shillerdata.com.
- Rows: 1871 months, 1871-01 to 2026-11 (November 2026 is a partial month as of Nov 12).
- Tidy copy: `shiller/ie_data_Data.csv` (date as YYYY-MM, my own column names).

## Federal Reserve Board H.15 T-bill rates

### fed_h15/FRB_H15.zip
- Source URL: https://www.federalreserve.gov/datadownload/Output.aspx?rel=H15&filetype=zip (the full H.15 release from the Board's Data Download Program)
- Download time (UTC): 2026-11-25T07:30:16Z
- Layout: SDMX XML (H15_data.xml, 71 MB unzipped, deleted after extraction to save space; the zip is kept and can be unzipped again) plus schema files. Missing observations have OBS_STATUS="ND" and OBS_VALUE="-9999".

### fed_h15/H15_tbill_daily.csv (extracted from the zip)
- Columns: date (YYYY-MM-DD), TB4WK (series RIFSGFSW04_N.B), TB3M (RIFSGFSM03_N.B), TB6M (RIFSGFSM06_N.B), TB1Y (RIFSGFSY01_N.B). Secondary market rates, discount basis, percent per year. Blank = not available (ND or series not yet started).
- Rows: 19,016 business days, 1954-01-04 to 2026-11-23. Series start: TB3M 1954-01-04, TB6M 1958-12-09, TB1Y 1959-07-15, TB4WK 2001-07-31. ND days in range: TB3M 802, TB6M 756, TB1Y 2,436, TB4WK 275.

### fed_h15/H15_tbill3m_monthly.csv
- 3-month T-bill secondary market rate, monthly average (RIFSGFSM03_N.M), percent per year. 1,114 rows, 1934-01 to 2026-10.

## Not stored here

FRED copies of S&P 500 and Dow Jones (copyright S&P with a reproduction ban), the SPDR SPY NAV history from ssga.com (site says no copying without consent), Stooq files (browser check blocks plain downloads), and anything from Yahoo. See REPORT.md for why.
