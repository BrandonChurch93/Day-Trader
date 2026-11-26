# E05: Forward watch for the hot-five cash switch

STATED. Proposed only. [Plan 51 closed on synthetic power](../../research_rig/CLOSE_51_on_power.md); no freeze or forward watch was started. Keep the protocol below as a record, not an instruction to begin.

STATED. Manual watch only, separate from Plan 51's historical score. Start logging from the approved strategy freeze, before seeing any later return. Pretend money, no broker connection, no automation and no price backfill scored as prospective. Use the same dated CMC list, Binance public bulk spot hourly archives, completed-close signal and 15 bp per-side traded-notional rule as [Plan 51](../../research_rig/PREREG_51_momentum_when_it_pays.md). Do not query the venue's live service.

At each 00:00 UTC decision, record the intended decision date, the roster and hourly data cutoffs actually available, what can be ranked, the proposed action or a missing-data reason, and the availability time. Keep the private append-only record off Git. If the archive has not published the bars by the decision, log the gap when it occurs; a later bulk file can verify a logged decision or fill but cannot create a timely decision. Do not use prior-price returns or look at cumulative performance between scheduled reads.

The lead agent alone reads the first result after 26 complete UTC weeks following the freeze (Monday 00:00 through Monday 00:00), then after each full year of the forward watch. Report the on-time coverage and missing decisions together with the unchanged rule, weekly Rule A, universe, BTC and spell twins. If bulk publication prevents timely decisions, say the forward watch is operationally blocked; do not label an archive reconstruction a forward result. UNKNOWN: timely coverage or any forward return.
