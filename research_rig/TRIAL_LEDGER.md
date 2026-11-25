# Trial ledger (research rig)

Every rule variant is listed here before it is run. A result with no row here does not count.

| # | Logged (UTC) | Pre-registration | Trials | Status |
|---|---|---|---|---|
| 1 to 20 | 2026-11-25 06:35 | PREREG_01_daily_crypto_trend.md | P1, P2, S50, S100, S200, D20, D55, M30, M90 on BTC and on ETH; PORT-P1, PORT-P2 | logged 06:35, first run started 06:37 UTC. Run. Results in docs/research/12 |
| 21 to 26 | 2026-11-25 06:43 | PREREG_02_ai_calls_pilot.md | r_fable_a, r_fable_b, r_fable_c, r_opus, r_sol, r_neon | logged before run. Run. All six kept. Results in docs/research/14 |
| X1 | 2026-11-25 06:54 | PREREG_01 Amendment 1 (second-source cross-check) | Same P1 and P2, Kraken daily bars 2024-12-05 to 2026-11-24, against Bitstamp over the same dates. Not a new trial | logged before run. Run. Results in docs/research/12 |
| S1 | 2026-11-25 06:54 | PREREG_01_S1_fill_delay.md | Fill-delay sensitivity on trials 1 to 18. Same rules, no new trials, no pass marks. (a) fill one hour after the daily close, (b) fill one full day late | logged before run. Run. Results in docs/research/12 |
| 27 to 42 | 2026-11-25 07:04 | PREREG_03_intraday_crypto.md | H1 to H8 on BTC and on ETH, hourly bars | logged 07:04 UTC, pushed in d91ebba before the run. First run stopped at the save step before any result was read; save step fixed, rerun. Run. 0 of 16 passed at any venue cost. Results in docs/research/15 |
| X2, S2 | 2026-11-25 07:10 | PREREG_01_X2_kraken_full_history.md | The same 9 rules on Kraken's published full daily history. BTC from 2014-05-01, ETH from 2018-03-05, and ETH from 2016-03-01 as a longer sample. Not new trials | logged 07:10 UTC, pushed in c0ef884 before the run. Run. All 8 bitcoin passes from replay 01 failed on the shorter history, 7 of them on mark 4 alone. Results in docs/research/12b |
| diagnostic | 2026-11-25 07:17 | none, written after seeing X2 | Mark 4 for bitcoin on Bitstamp prices from 2014-05-01, to tell prices from dates. Not a trial, changes no verdict | Run. Fails on Bitstamp prices too. In docs/research/12b |
