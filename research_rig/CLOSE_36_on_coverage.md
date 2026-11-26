# Plan 36 closed on coverage

Recorded 2026-11-26 08:05 UTC. Queue 60 and ledger 171 are closed **INCONCLUSIVE**. The [frozen preregistration](PREREG_36_form4_cluster_buys.md) sets an unresolved coverage limit of 5% overall and 10% per year. The freeze is `8fbcea52fef845ccdbac26ebdeb27aeadda11206`; neither the rule nor the frozen files changed. No single-run lock was claimed, no returns were calculated, and the custodian's market payload stayed sealed from the author and scorer. The other eight marks are UNKNOWN, not failed or passed.

## Final no-return count

MEASURED by the independent custodian on the re-sealed packet (manifest SHA-256 shown as `a7f47f8e…0e48`). **120 of 2,100 confirmed attempts were unresolved (5.71%)**. The overall limit was exceeded; no year exceeded 10%. The annual numerators and denominators sum to the overall count.

| Filing year | Unresolved | Attempts | Unresolved share |
|---|---:|---:|---:|
| 2016 | 14 | 160 | 8.75% |
| 2017 | 4 | 146 | 2.74% |
| 2018 | 7 | 184 | 3.80% |
| 2019 | 13 | 222 | 5.86% |
| 2020 | 13 | 281 | 4.63% |
| 2021 | 15 | 168 | 8.93% |
| 2022 | 20 | 267 | 7.49% |
| 2023 | 5 | 210 | 2.38% |
| 2024 | 9 | 147 | 6.12% |
| 2025 | 13 | 185 | 7.03% |
| 2026 | 7 | 130 | 5.38% |
| Overall | 120 | 2,100 | 5.71% |

- **`bar_warmup_missing`:** 76. Of these, 21 had only dropped zero-volume sessions, 9 preceded the first listed bar with an SEC listing filing, 9 preceded the first bar without a listing filing found, 35 had no vendor bars, and 2 had other vendor gaps.
- **`cap_missing`:** 26 remained unresolved after 28 of the initial 54 were resolved from eligible SEC cover pages under the frozen cap rule.
- **`identity_unknown` and `quote_missing`:** 14 and 4, respectively.

STATED. The plan exempts the fixed Alpaca history left edge, not a later security-specific first bar. Dropped zero-volume sessions alone do not establish failure of the frozen liquidity gates and do not supply valid replacement bars. Vendor gaps remain unresolved. Author and independent auditor agreed; none of the three causes was relabelled or removed from confirmed-attempt coverage.

## Pre-scoring action reconciliation

MEASURED by the custodian. The first packet omitted 60 cash dividends, the CGBD item, and one TSE amount. The vendor date filter is not the ex-date. The action packet was repaired and re-sealed before any return calculation. This did not change the preregistered coverage rule.
