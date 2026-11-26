# Replay 26 blocked at the source check

STATED. The lead agent ran input validation on 2026-11-26 at 04:13:59 UTC from approval commit `a9d9ae5569fc427c1e7cd8e908a52f66fa6aa367`; it refused with `P26_OVERLAP_AGREEMENT`. Nothing was scored, no result was written, and the lock was unused. The [frozen plan](../../research_rig/PREREG_26_treasury_month_end_early.md) and its gate are unchanged. This is an input failure, not a strategy result.

MEASURED. The counts-only comparison found absolute gaps over one cent on 42 TLT sessions and 13 IEF sessions, all in 2016–2018. The largest gaps were 14 cents for TLT and 5 cents for IEF. From 2019 through the end of the overlap, every session for both funds agreed within one cent.

| Fund | 2016 over one cent | 2017 over one cent | 2018 over one cent | Pull A within one cent | Pull B within one cent | Joined within one cent |
|---|---:|---:|---:|---:|---:|---:|
| TLT | 16 | 23 | 3 | 1,217 / 1,259 | 1,486 / 1,486 | 2,681 / 2,723 |
| IEF | 6 | 5 | 2 | 1,246 / 1,259 | 1,486 / 1,486 | 2,710 / 2,723 |

MEASURED. TLT missed the frozen threshold on Pull A and the joined overlap; IEF missed it on Pull A. The private counts JSON had SHA-256 `279689326905338aeaf50659aa1074997244080fcef04f07f54656bfc77927a2`. The auditor reviewed the aggregate script and output; the diagnostic neither scored nor repeated input validation.

UNKNOWN. The cause of the differences and which close definition the vendor used. STATED. To revisit the plan, first obtain the vendor's close-field definition and a second independent raw source for 2002–2015. If that source is obtained, any amendment gets its own ledger row and a fresh freeze. No overlap years are dropped and the existing gate is not loosened.
