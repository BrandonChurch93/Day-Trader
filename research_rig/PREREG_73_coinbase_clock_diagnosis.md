# Plan 73: Did the search gain survive the first minute?

STATED: Ledger 221, Queue 117. This is a diagnosis on the already-searched 2020 to 2023 dates, not a test. It reprices the 382 frozen search tickets of 71-013, a rule chosen after the 300-rule sweep, on Coinbase Exchange candle prints. No reading is a pass or allows money. The [Plan 72 fresh-date runner](PREREG_72_coinbase_reachability.md) was closed before any minute price was requested, and Plan 73 neither accesses its custody nor touches the 2017 to 2019 dates. A power step must take its noise from a measured spread named in the plan.

## Fixed tickets and candle clocks

STATED: Check both fixed Plan 71 aggregates, the search summary and carry receipt, then read and hash the receipt-pinned mode-0600 `carry71_tickets.json` once per mode. Verify its shape from the same bytes and use only 71-013's exact ticket coin, UTC entry and exit, and, after claim only, its saved plain net. The count and validation do not use saved means or ticket payoff values. There is no signal calculation, retuning, fresh schedule, vault access or power calculation.

STATED: Drop tickets whose signal or scheduled hold, including entry and exit, touches any of the 12 named UTC dates from [Doc 153](../docs/research/153_overextension_lead_outside_evidence.md). Those dates are inherited by hash from `CONFIG_72.json`. A ticket just after midnight can touch a named date on the previous day. No candle is requested solely for an excluded ticket.

STATED: For every coin remaining, attempt its Coinbase Exchange USD candle pair for just the ticket's windows. Use public unauthenticated candles at `api.exchange.coinbase.com`; no current listing endpoint, book, or alternate host. Only a JSON 404 with one explicit `message` field saying "Product not found" is accepted as a product absence response. Its raw bytes are retained with their manifest hash. Bare `NotFound`, duplicate fields, any other ambiguous 404, blocks, and unexpected errors stop collection without retry, redirect, or alternate route. No print in any requested ticket window is reported separately as `no_pair_evidence_at_ticket`; an empty historical response leaves the listing status UNKNOWN, not proof of delisting or unavailability. When there is some evidence, report missing hourly open or missing minute under separate exclusive drop counters, with hourly incompleteness first if both apply. Coverage by clock after the outage filter is also shown.

STATED: Compare all lines on one common sample. If a ticket cannot be priced at every clock, none of its lines enters a mean.

- **Coinbase hourly open:** Use the entry and exit hourly open prints. This is a distinct venue and print benchmark, not an executable order.
- **Reachable proxy:** Take the midpoint of the high and low for the candle starting at :01 after each scheduled hour. If that candle is missing, use the next available minute up to five minutes later, inclusive. The proxy is not a bid or an ask.
- **Late entry:** Start at :05 or :15 with the same five-minute fallback. Exit is unchanged and uses the same reachable exit candle. :05 can tie the actual reachable entry if its fallback had already reached :05 or :06.
- **Worst of minute:** Buy at the high and sell at the low of the same minute candles the reachable proxy would use.
- **Search:** Use the frozen Plan 71 plain ticket net for exactly these same tickets. Do not price it again or apply costs twice.

STATED: Every Coinbase clock pays the inherited Plan 70 judged futures round-trip cost for that coin plus one basis point for each of the original two scheduled holding hours. The cost and nominal funding stay fixed even when a late entry shortens the hold. The prices themselves are Coinbase spot candles, not historical futures fills.

## Fixed readings and report

STATED: All means are equal-weight plain net per compared ticket and are reported as decimal returns. Compare unrounded values. State the number compared out of 382, by UTC entry year and by coin, including the unique coin count. Report the reachable mean separately by UTC entry year. For reachable minus saved search net and reachable minus Coinbase hourly open, report the same-ticket mean difference and its UTC-entry-day clustered t. A mean or t is null when it cannot be calculated, for example on no observations or no usable variation across days.

- **UNREADABLE:** Fewer than 150 complete tickets, regardless of the means.
- **ARTIFACT:** With at least 150 complete tickets, reachable mean is below half of the same-ticket search mean.
- **REACHABLE:** With at least 150 complete tickets, reachable mean is at least half of that search mean and the 5-minute-late mean is strictly positive.
- **PARTLY:** All other cases with at least 150 complete tickets.

STATED: Print the inputs to the reading, not just the label. No reading is a pass. Row 221 reserves a future pooled dated test only if this diagnosis is REACHABLE and its independently measured power clears 33%. ARTIFACT closes this family for a $500 account. This runner cannot do either a dated test or a power calculation.

## Lead procedure

STATED: Use `nice -n 10 python -E -B -X pycache_prefix=/dev/null research_rig/plan_73.py` on a clean audited commit. Real modes need `--lead-authorize`, `--freeze-commit`, `--config-sha256`, `--settings-sha256`, `--grid-sha256` and `--grid71-sha256`. The runner checks the current settings file against its pin and verifies that the earlier Plan 70 section still matches its original authenticated freeze. The sole custody is `/home/user/workspace/rig/data/plan73` with mode 0700; files are mode 0600. No selectable paths, time ranges or coins are accepted.

- **Count:** `--count` authenticates the prior tickets and prints candidate/requested USD pairs and exact hourly/minute request counts without a price or wire request. Exact private ticket timestamps and the ordered bounded request list stay only in `minute_plan.json`; the command prints its hash.
- **Approval:** The lead writes the mode-0600 `go_approval.json` with the plan's exact `binding` keys, the authenticated `plan_sha256`, and `lead_authorizes_one_use` true. Supply independent `--plan-sha256` and `--approval-sha256` pins in subsequent commands.
- **Collect:** `--collect` rederives the complete plan from the authenticated tickets in the same process and requires byte equality before any request. It collects hourly windows first, then minute windows, using the shared serialized delay. `diagnostic_manifest.json` binds the ordered jobs, exact approval and SHA-256 of each raw response. A started collection that fails produces no complete manifest. Both the planner and transport refuse any request outside 2020-01-01 through 2023-12-31; the exclusive right endpoint is converted to an in-range query timestamp. No minute controls are requested.
- **Validate and release:** First run `--validate-inputs` with the added `--windows-manifest-sha256` pin. It reauthenticates the tickets, plan and candles and returns counts only, without a return, signal, or claim. Then run `--go` with the same pins. It claims and syncs the fixed lock and its directory before opening prior vectors or candles, then reauthenticates and reports summaries only. Failure after claim spends the single use; every real mode refuses once it is claimed.
- **Synthetic:** `OPENBLAS_NUM_THREADS=1 nice -n 10 python -B research_rig/plan_73.py --synthetic` uses only temporary files and fabricated responses. It checks unreachable open prints, true drift, the two other readings, exclusive drops, date fences, prior file substitution, counts-only validation and durable release.
