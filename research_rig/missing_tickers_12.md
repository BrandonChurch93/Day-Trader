# Plan 12: tickers with no prices, and a seeded look at 40 of them

Status: work note for plan 12, written 2026-11-25 by the plan 12 builder. Counts are MEASURED from `prices_12_summary.json`, `events_12_summary.json` and the missing list in `~/workspace/rig/data/congress_12/missing_tickers.json` (not in the repo). The 40 were drawn with `random.Random(12).sample(sorted(missing), 40)`. Company facts are STATED from the linked pages and were read there, not checked further.

## The whole missing list

- MEASURED. 606 of 2,996 tickers in buy and sell rows have no bars from the price source (feed sip). They carry 914 purchase events and 1,188 sale events, out of 29,380 and 30,565.
- MEASURED, by the shape of the ticker. 424 are five letters ending in Y, 78 five letters ending in F, 19 five letters ending in X, 1 five letters ending in Q, 10 have a dot or dash, 9 are other five-letter tickers and 65 are one to four letters.
- STATED. On five-letter over-the-counter tickers a final Y marks an ADR, F a foreign share, Q a company in bankruptcy, and X a mutual fund ([FINRA fifth character list](https://otce.finra.org/otce/fifth-char-identifier), [Nasdaq fifth character list](https://www.nasdaqtrader.com/content/technicalsupport/specifications/dataproducts/nasdaqfifthcharactersuffixlist.pdf)). The price source has no over-the-counter or fund prices, so most of the list is missing for that reason, not because the company failed.
- MEASURED. Renamed companies. The price source keeps a renamed company's whole history under its new ticker. Each of these new tickers returned bars from 2018-12-03 to 2026-11-24: MRSH, FISV, FBIN, WTW, SONY, TTE, BKR, J, UI, JBTM, CNH. So purchases reported under the old tickers MMC (55 purchase events), FI (28), SNE (10), FBHS (8), WLTW (8) and others have no price, though the company kept trading. STATED: Marsh McLennan moved from MMC to MRSH on 2026-01-14 ([Marsh](https://www.marsh.com/en/corp/about/news/marsh-mclennan-to-change-nyse-symbol-to-mrsh.html)); Fiserv moved from FISV to FI on 2023-06-07 and back to FISV on 2025-11-11 ([Fiserv](https://investors.fiserv.com/news-releases/news-release-details/fiserv-announces-transfer-stock-exchange-listing-nasdaq), [Nasdaq notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=DTN2025-32)).
- MEASURED. The one-to-four-letter missing tickers carry 162 purchase events. This is the group most likely to be renamed listed companies. Some are typing slips in the record (APPL).

## The seeded 40

| Ticker | Purchase events | Sale events | What it is, and what happened | Label |
|---|---|---|---|---|
| SNREY, KGFHY, TRYIY, NPSNY, DNZOY, PCRFY, AGESY, SSDOY, SMCAY, HSHCY, VOPKY, DQJCY, SFGYY, OLCLY, NDEKY, WTKWY, GASNY, TKAMY, NCMGY, QBIEY, AJINY, BDVSY, HLPPY, CCLAY, SGBLY, DLICY, UNCRY, MITSY (28) | 33 in all | 40 in all | Five letters ending in Y: ADRs of foreign companies sold over the counter. Not each checked one by one. No price because the source has no over-the-counter prices. | STATED (ticker rule), UNKNOWN (each company's fate) |
| BDRFF, RSNHF, CPXWF (3) | 4 | 2 | Five letters ending in F: foreign shares sold over the counter. Not each checked. | STATED (ticker rule), UNKNOWN (fate) |
| OTCM | 0 | 1 | OTC Markets Group, still trading over the counter ([OTC Markets](https://www.otcmarkets.com/stock/OTCM)). | STATED |
| ENBP | 0 | 1 | ENB Financial, a Pennsylvania bank, still trading over the counter ([OTC Markets](https://www.otcmarkets.com/stock/ENBP/profile)). | STATED |
| EMRZX | 0 | 1 | VanEck Emerging Markets Fund, class Z, a mutual fund, still open ([VanEck](https://www.vaneck.com/us/en/investments/emerging-markets-fund-emrzx/overview/)). | STATED |
| CAIFX | 0 | 1 | American Funds Capital Income Builder, class F-2, a mutual fund, still open ([Morningstar](https://www.morningstar.com/funds/xnas/caifx/quote)). | STATED |
| GNKOQ | 1 | 1 | Genco Shipping's ticker during its 2014 bankruptcy. Old shares were cancelled when it left bankruptcy on 2014-07-09 ([FINRA notice](https://www.finra.org/sites/default/files/26-2014%20GNKOQ_0_0_0.pdf)). Genco trades today as GNK ([SEC 10-Q](https://www.sec.gov/Archives/edgar/data/1326200/000110465926056337/gnk-20260331x10q.htm)). A filing after 2019 with this ticker is an old ticker in the record, not a failure in the window. | STATED |
| BRK | 0 | 1 | Berkshire Hathaway with no class letter. It trades as BRK.A and BRK.B. | UNKNOWN which class |
| KMI.W | 1 | 0 | Kinder Morgan warrants. They expired on 2017-05-25 ([SEC 10-Q](https://www.sec.gov/Archives/edgar/data/0001506307/000150630717000051/kmi-09302017x10q.htm)), so a purchase filed in this window under this ticker is most likely a mislabel. | STATED (expiry), UNKNOWN (what was bought) |
| TFC.F | 0 | 1 | Truist Series F preferred, redeemed at 25 dollars on 2021-03-01 ([Truist](https://media.truist.com/2021-01-20-Truist-to-Redeem-All-450-Million-of-Its-5-200-Series-F-Non-Cumulative-Perpetual-Preferred-Stock-and-All-500-Million-of-Its-5-200-Series-G-Non-Cumulative-Perpetual-Preferred-Stock-Each-Represented-by-Depositary-Shares)). | STATED |
| AAICB | 1 | 0 | Arlington Asset Series B preferred. Arlington was taken over by Ellington Financial on 2023-12-14; Ellington took on the preferred ([SEC press release](https://www.sec.gov/Archives/edgar/data/1411342/000141134223000200/ex991-efcaaicmergerclosing.htm)). | STATED |

Summary of the 40. Taken over: 1 (AAICB). Redeemed or expired: 2 (TFC.F, KMI.W). Failed inside the window: none found; the one bankruptcy ticker (GNKOQ) is from 2014. Still trading or open but outside the price source: 35 (28 ADRs, 3 foreign shares, 2 over-the-counter stocks, 2 mutual funds), with the ADR and foreign-share fates taken from the ticker rule only. No class given: 1 (BRK).

## The rename list

Added 2026-11-25 by the plan 12 builder, after the lead chose to map renames (option a). The list is `research_rig/renames_12.csv`. Each line has the old ticker, the new ticker, the date of the change, a public source and a status. Company facts are STATED from the linked source on each line.

- mapped (19): the same company under a new ticker. MMC to MRSH, FI to FISV, SNE to SONY, WLTW to WTW, TOT to TTE, BHGE to BKR, JEC to J, UBNT to UI, JBT to JBTM, CNHI to CNH, FBHS to FBIN, ROLL to RBC, BRP to BWIN, CCCS to CCC, BHLB to BBT, WGP to WES, AMGP to AM, DEAC to DKNG, BLFSD to BLFS. The feed keeps the whole history under the new ticker, so the map applies on every date. The record's own ticker stays in each event.
- Judgement calls among the mapped. JBT, WGP, AMGP, BHLB and DEAC each bought another company and took its name; the buyer is the company that went on trading, so these are renames, not takeovers. For WGP and AMGP the new ticker's price file runs smoothly across the change day (MEASURED from two closes each), so its earlier history is the buyer's. DEAC was a blank-cheque company; the record's own text names DraftKings and DKNG. FBHS spun off MasterBrand and then renamed itself; the company kept is the same one. BLFSD was a 20-day symbol after a 2014 reverse split, so a 2021 filing with it is an old label.
- left_out (55): every other one-to-four-letter ticker with no bars, and the five-letter ones looked at. Among them: takeovers and new holding companies (BHI, BRCM, JIH), a share-class change (RDSA into SHEL), NYSE delistings to over the counter (ABB, CAJ), a slip in the record (TLRN for TELL), and HTA, where the HR price file jumps on the merger day, so which company its earlier prices belong to is UNKNOWN. The rest are preferred and depositary shares, over-the-counter or foreign listings, or names not confirmed from a public source.

## Ticker reuse seen in passing, and the dated lines

Not hunted for. Found while checking the rename list, including the new tickers the list points at. The lead decided on 2026-11-25 that these must not be left joining the wrong company. Each is now a dated line in `renames_12.csv`: `mapped_before` sends rows filed before the line's date to the right ticker, `left_out_before` leaves them out and counts them as no price. The filing day chooses the line, never transaction_date. Event counts per line are MEASURED by `score_12.py --counts` and printed in the Replay 12 page.

- BBT before 2025-09-02 to TFC. BB&T became Truist and has traded as TFC since 2019-12-09. The BBT file is the bank that took BBT on 2025-09-02. The date is the day the ticker passed to that bank, not the 2019 merger day, because one BB&T row was filed in 2023 under BBT, when no listed company used it.
- CCC before 2025-10-31 to CLVT. Clarivate used CCC until 2021-02-01 and then CLVT. The CCC file is CCC Intelligent Solutions, which took CCC on 2025-10-31. Same reasoning for the date.
- AM before 2019-03-13 left out. That AM was Antero Midstream Partners LP, taken over by AMGP. The AM file before that day is AMGP's.
- HR before 2022-07-21 left out. The HR file jumps on that day; whose prices it holds before is UNKNOWN, and I could not show it is the old Healthcare Realty.
- RBC before 2021-10-05 to RRX. Regal Beloit used RBC and was renamed Regal Rexnord, trading as RRX from 2021-10-05; the RRX file runs smoothly across that day (MEASURED). The RBC file is RBC Bearings.
- WTW before 2019-04-22 left out, and WTW from 2019-04-22 to 2022-01-09 to WW. Weight Watchers used WTW until 2019-04-19 and WW from 2019-04-22. The WTW file is Willis's history throughout (MEASURED smooth on 2019-04-22 and 2022-01-10) and the WW file starts 2019-04-22, so earlier Weight Watchers rows have no price.
