# Plan 50 closed on count, before prices

The lead closed queue 88 and ledger 184 on November 26, 2026, Mountain Time. The independent price-blind review found **22 strict documentary candidates against a floor of 30** set before the count. This is a generous upper bound under the strict reading: the 22 still include a missing operative term pin and several provisional mandate mappings. None are placed trades. No market prices, NAV history, bars, quotes, or returns were accessed; no market-data collection was authorized, and there was no freeze, approved input manifest, real validation, score or order. The [draft protocol](PREREG_50_cef_liquidations.md) and synthetic checks are preserved unchanged; they cannot authorize a run.

## Counts and decision

| Entry year | Cash liquidation | Scheduled term | Open-ending | Strict total |
|---|---:|---:|---:|---:|
| 2016 | 0 | 0 | 0 | 0 |
| 2017 | 0 | 0 | 0 | 0 |
| 2018 | 0 | 3 | 0 | 3 |
| 2019 | 0 | 0 | 0 | 0 |
| 2020 | 1 | 3 | 0 | 4 |
| 2021 | 1 | 2 | 0 | 3 |
| 2022 | 0 | 2 | 0 | 2 |
| 2023 | 1 | 4 | 0 | 5 |
| 2024 | 0 | 1 | 1 | 2 |
| 2025 | 3 | 0 | 0 | 3 |
| 2026 through March 10 | 0 | 0 | 0 | 0 |
| **Total** | **6** | **15** | **1** | **22** |

- **Strict, 22:** Use the draft's contemporaneous evidence standard for entry and a last regular exchange session publicly scheduled before its close, or a supported session-180 path. The strict candidates are EGIF, MIE, GER, HNW, PHT and PHD (liquidation); BJZ, BLH, BPK, JHY, BFO, BKK, NHA, JHB, JCO, EFL, NID, NIQ, IHIT, JHAA and IHTA (term); and TTP (open-ending). JHY's operative term date was not pinned. Mappings for JHB, JCO, IHIT, JHAA, IHTA and HNW still needed prospectus-level confirmation. Actual market-data coverage and whole-share affordability were never evaluated.
- **Tentative issuer dates, 32:** The alternative adds EVY, FIV, IRL, CHN, DMF, MAV, MHI, MIO, ENX and EVM by treating an “on or about” or “expected” last trading date as a firm scheduled close. It was not adopted.
- **Tentative dates plus aggregator-only copies, 36:** The broader alternative additionally accepts EFF, TKF, KTF and EHT on secondary-only wire evidence for timing or corroboration. It was not adopted. The project will not select a wider reading after seeing that doing so would clear the count floor.

## Other exclusions by reason

- **Outside the entry window:** SGL, HYF and RIT (first board notice in 2015); IAE and IHD (June 2026, after the March 10 cutoff). Board deliberation, public announcement, closing and payout are different clocks.
- **Board backing absent or not established:** PPT 2017, BKT 2018, PMM 2019 and 2024, and PCF 2023 were opposed or lacked a favorable recommendation. The other PCF charter-vote episode stays watch-only; EVF and DSM lacked verified board sponsorship. A [PMM definitive proxy](https://www.sec.gov/Archives/edgar/data/844790/000092881619000502/a_cefdef14a.htm) illustrates why voting paperwork is not itself a board-backed entry.
- **Wrong transaction:** The JMT episode and FGB's 2023 episode were CEF-to-CEF mergers. [JMT's original stated term](https://www.sec.gov/Archives/edgar/data/1479238/000119312509258162/dn2.htm) implied January 30, 2020 as the planned entry; the [retrospective N-8F](https://www.sec.gov/Archives/edgar/data/1479238/000113743920000102/nuveenjmtn8f031120.htm) documents its December 2019 event. No backdated term entry.
- **Unmapped mandate:** AABA, FGB's 2024 ETF episode, FEO, GFY, CBH, BGIO, JFC, APB, NDP, TPZ, RCG, BHL and JEMD lacked an admitted pre-entry match. JEMD was not assigned EMB on a generic emerging-debt label; the draft requires a qualifying US-dollar sovereign mandate. The BHL scheduled term and accelerated termination were distinct, as documented in its [N-8F](https://www.sec.gov/Archives/edgar/data/1412914/000134100417000527/n-8f.htm).
- **Entry not verified:** TLI had an earlier release referenced in the file, but the first public clock was unresolved.
- **Timely last regular session not verified:** KHI, PHF, KEF, LDF, TTF, MZF, AKP, FDEU, FEI, FEN, FIF, FPL, FCT, JHA and JHD. Some had a scheduled transaction effective date, an exchange removal filing, an unauthenticated last-day copy, or a contemporaneous announcement with no last-day notice. None of those resolves an uncertain scheduled sell clock or justifies backdating an exit.

## Docket corrections and audit records

The 79-row scout inventory was a discovery list. Its 31 “defensible” tags were not the tested count: all 31 lacked a populated last regular session field. The independent review found roughly twenty misidentified or unverified event clocks across the historical list, with common clocks shared by multiple funds. Corrections included the first KHI board-backed liquidation notice rather than a prior board-opposed proposal; the RIT, JFC, PHF, KEF, EGIF, EVY and IRL announcement dates; first notices for the four First Trust energy funds rather than February 2024 vote material; the NDP/TPZ/TTP announcement rather than a prior management change; the DMF board release rather than an unrelated Saba filing; the joint Pioneer initial disclosure rather than later updates; and separate corrections to ENX/EVM, KTF and FCT. Related source checks include the [October 2023 First Trust filing](https://www.sec.gov/Archives/edgar/data/0001513789/000144554623007077/fif_8k.htm), the [completed FEI conversion filing](https://www.sec.gov/Archives/edgar/data/1556336/000144554624005375/fei_n8f.htm), and the [FCT completion filing](https://www.sec.gov/Archives/edgar/data/1282850/000144554626005855/fct_8k.htm); the retrospectives do not supply entry clocks.

The detailed independent reconciliation is retained off-repo at `/home/user/workspace/rig/plan50_review/independent_count.md`. Its discovery input was `/home/user/workspace/rig/inventories/row88_cef_liquidation_docket_v2.csv` (SHA-256 `ad02ddbc76c75a8d9694ed6ddd775e8af4ff7f7924fe5af1abbd264c9d9e0a82`). The independent auditor cleared the draft code and synthetic tests. That clearance did not validate a real input packet and does not change the count disposition.

## Forward watch only

The December 2026 through February 2027 manual filings watch stays listed off-repo at `/home/user/workspace/rig/inventories/rows88_89_dec2026_feb2027_forward_watch.md`. PCF's December 18 shareholder meeting at 11:00 a.m. Mountain Time remains a watch item only: its [definitive proxy](https://www.sec.gov/Archives/edgar/data/810943/000158064226007881/pcf-def14a_annualmtg.htm) makes no board recommendation on the open-ending proposal. Watch new public notices and outcomes only. The list does not reopen Plan 50, admit PCF to a judged sample, authorize market access, or place orders.
