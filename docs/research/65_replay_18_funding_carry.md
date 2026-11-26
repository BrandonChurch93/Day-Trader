# Replay 18: funding carry

MEASURED. The three-day funding carry rule **did not pass**. At 12 bps per side on net changes in position size, it met **1 of 3 marks**, returned -44.61% net, and had a daily net Sharpe of -0.339.

STATED. The [frozen plan](../../research_rig/PREREG_18_funding_carry.md) takes three low-funding longs and three high-funding shorts from a reconstructed subset of the saved monthly top 30. It uses a full funding-interval lag, then enters at the next hourly open. Only this turnover-only book at the judged cost has marks. It is not a result for all ranked coins or for US fills.

## Judged marks

| Mark | Measured | Verdict |
|---|---:|---|
| Net Sharpe at least 1.0 | -0.339 | not met |
| Largest fall at most 25% | 57.33% | not met |
| Positive in at least three of five years | 3 of 5, 2023, 2024, 2025 | met |

MEASURED. In percentage points of starting equity, price moves contributed -29.24, funding +33.97, and fees -49.35. There were 586 qualified slots and 586 traded slots. There were 0 cash slots, 0 slots with too few names and 0 with no usable opening fill.

| Year | Net return |
|---|---:|
| 2022 | -42.10% |
| 2023 | +5.17% |
| 2024 | +3.70% |
| 2025 | +5.84% |
| 2026, partial | -17.12% |

## Forced closes

MEASURED. There were 9 forced closes. None was written to zero. The reasons below are the recorded accounting reasons, not claims about why the venue stopped printing data.

| UTC | Contract | Side | Recorded reason |
|---|---|---|---|
| 2022-05-12 09:00 UTC | LUNAUSDT | long | Funding coverage gap in an open leg |
| 2022-11-14 03:00 UTC | FTTUSDT | long | Funding coverage gap in an open leg |
| 2024-09-04 09:00 UTC | MATICUSDT | short | Dated limit on this contract's accounting |
| 2024-10-28 21:00 UTC | BNBUSDT | long | Trade gap or dated accounting limit |
| 2024-10-28 21:00 UTC | AVAXUSDT | long | Trade gap or dated accounting limit |
| 2024-10-28 21:00 UTC | BCHUSDT | long | Trade gap or dated accounting limit |
| 2024-10-28 21:00 UTC | SOLUSDT | short | Trade gap or dated accounting limit |
| 2024-10-28 21:00 UTC | DOTUSDT | short | Trade gap or dated accounting limit |
| 2024-10-28 21:00 UTC | UNIUSDT | short | Trade gap or dated accounting limit |

## FTT coverage

MEASURED. The FTT branch was `normal`. No separate stress debit applied, so there is no alternate uncharged line. The protected window was complete, although the full segment was not. The ordinary FTT forced close above is separate from that branch decision. The plan pinned 24 FTT files by published checksum.

| FTT input | Whole segment | Protected window |
|---|---:|---:|
| Trade bars | 5,112 of 5,112 | 348 of 348 |
| Mark bars | 5,088 of 5,112 | 348 of 348 |
| Funding settlements | 675 of 675 | 80 of 80 |

## What was covered

MEASURED. 59 of 79 distinct ranked IDs had dated mappings, and 59 had an archive. No scheduled saved rank page was missing. The judged book recorded 12,459 rankable name-slots out of 17,580 in scope. The saved JSON has the full funnel and coverage exclusions by decision date and ID.

UNKNOWN. How many of all dead coins the rank provider retained. The archive has settlement times and finalized funding, not the publication time or revision history of those rates. The saved rank pages do not establish original publication or revision times either. The lags are proxies, not proof of what was known then.

MEASURED. These 20 saved ranked IDs lacked a dated mapping in the registered scope. Neither class proves that a contract never traded anywhere.

### No separate underlying perpetual in the registered scope (12)

- ID 825: USDT is Tether's dollar token and the quote unit in the registered USDT contracts. Neither pinned inventory identifies an independent USDT underlying in this scope.
- ID 2563: TUSD is TrueUSD's pegged dollar token. A TUSD quote-pair listing does not supply standalone TUSD-asset USD-M archive evidence.
- ID 3408: USDC is Circle's dollar token; appearing as quote collateral or settlement currency does not make it an underlying USDC product in these inventories.
- ID 3717: WBTC is ERC-20 wrapped Bitcoin. The dated BTCUSDT contract uses BTC, not custodial WBTC, so no proxy substitution is made.
- ID 4687: BUSD is the Paxos-issued dollar token. The BUSD collateral or quote format is not a contract on BUSD. Paxos stopped minting in February 2023.
- ID 4943: DAI is the Maker/Sky USD soft-peg token; the registered inventory has no matched DAI-asset perpetual. Do not substitute MKR or SKY.
- ID 18579: WTRX is wrapped TRON. TRXUSDT is documented on TRX; the archive does not separately support the wrapped representation in the judged scope.
- ID 26081: FDUSD is First Digital's dollar token; FDUSD-quoted spot listings and campaigns do not provide an underlying FDUSD perpetual in this scope.
- ID 27772: PYUSD is the dollar stablecoin issued by Paxos for PayPal. It is distinct from PYPL symbols and no matching underlying is identified in either registered inventory.
- ID 29470: USDe is Ethena's synthetic dollar, not the governance token ENA. The dated ENAUSDT futures notice is not evidence for a USDe perpetual.
- ID 33793: USDG is Global Dollar, not the similarly named assets on Binance futures. No USDG underlying is identified in the registered USD-M inventory.
- ID 36148: USD1 is World Liberty Financial's dollar token. The September 2025 WLFI perpetual conversion applies to WLFI governance exposure, not USD1.

### Outside the registered scope (8)

- ID 3635: CRO is Cronos, an ecosystem asset distinct from Binance CRO lookalike codes. Neither pinned USD-M inventory identifies CROUSDT on ranked dates.
- ID 3897: OKB is the OKX ecosystem token. No OKB USD-M history occurs in the two pinned Binance inventories; an OKX contract would not be in scope.
- ID 3957: UNUS SED LEO is the Bitfinex ecosystem utility token, not LEO lookalike tickers. No supported LEO USD-M archive path identifies this underlying.
- ID 5176: XAUt's only ranked page was March 1, 2026, before the venue's March 26 XAUTUSDT launch. Neither pinned inventory lists the contract. Do not substitute generic gold exposure.
- ID 7129: The saved UST rank ID is TerraClassicUSD, the former Terra dollar-peg asset. Its depeg does not turn an existing LUNA/LUNC contract into UST archive coverage; neither pinned inventory supplies UST or USTC.
- ID 11092: BGB is Bitget's ecosystem token; a Bitget BGB contract, if any, does not establish a corresponding Binance USD-M archive. The pinned inventories contain no matched BGB underlying.
- ID 27075: Mantle MNT is not MemeCore M or MANTRA. The saved Binance USD-M inventories do not identify MNTUSDT under Mantle on the ranked dates.
- ID 35697: PI identifies Pi Network mainnet, not IOUs or similar tickers. No Pi Network USD-M archive path is present in the two registered manifests.

## Shown only: costs and full close and reopen

MEASURED. These alternatives have no marks. The saved all-false mark arrays are placeholders, not failed thresholds. For example, the 1 bp book was positive in 3 years but is not judged.

| Cost and turnover | Net return | Sharpe | Largest fall | Positive years | Traded | Forced closes |
|---|---:|---:|---:|---:|---:|---:|
| 1 bp, net changes | +8.77% | +0.199 | 50.48% | 3 | 586 | 9 |
| 24 bps, net changes | -73.52% | -0.925 | 78.22% | 0 | 586 | 9 |
| 12 bps, gross full close and reopen | -71.65% | -0.873 | 76.72% | 0 | 586 | 9 |

## Shown only: matched-pool random books

MEASURED. 200 of 200 random books completed. 200 had defined Sharpe, 0 had undefined Sharpe and 0 were refused. Of those with defined Sharpe, 6.5% (13) met or exceeded the judged Sharpe. This is a descriptive comparison, not a mark.

| Measure | 5th percentile | Median | 95th percentile |
|---|---:|---:|---:|
| Net return | -88.72% | -75.36% | -36.09% |
| Sharpe | -1.791 | -1.103 | -0.282 |
| Largest fall | 55.93% | 79.05% | 90.16% |
| Fees as a share of starting equity | 47.11% | 68.87% | 104.57% |
| Traded slots | 586 | 586 | 586 |
| Slots with too few names | 0 | 0 | 0 |
| Slots with no usable open | 0 | 0 | 0 |

MEASURED. Forced closes per random book: 6 in 54 books; 7 in 85 books; 8 in 47 books; 9 in 14 books. The saved result keeps the counts by seed.

## Shown only: today's four US rosters

STATED. These are current lists applied to older Binance contract data. They look ahead to which products are available today. Each venue is separate, costs are assumptions per side, and the Binance inputs cannot establish US fills, fees or funding.

### Robinhood

MEASURED. 8 of 8 products mapped; 8 had a dated segment. The results below are not judged.

| Cost per side | Net return | Sharpe | Largest fall | Positive years | Traded | Forced closes |
|---|---:|---:|---:|---:|---:|---:|
| 1 bp | +63.04% | +0.603 | 30.54% | 3 | 586 | 6 |
| 12 bps | +0.0018% | +0.102 | 41.20% | 2 | 586 | 6 |
| 24 bps | -41.39% | -0.443 | 52.40% | 1 | 586 | 6 |

### Kalshi

MEASURED. 18 of 19 products mapped; 18 had a dated segment. The results below are not judged.

- Unmatched KXKSHIBPERP: kalshi product KXKSHIBPERP states kSHIB; canonical asset or unit scale is not uniquely evidenced.

| Cost per side | Net return | Sharpe | Largest fall | Positive years | Traded | Forced closes |
|---|---:|---:|---:|---:|---:|---:|
| 1 bp | -13.04% | +0.048 | 57.42% | 2 | 586 | 6 |
| 12 bps | -54.32% | -0.408 | 69.63% | 1 | 586 | 6 |
| 24 bps | -77.41% | -0.902 | 81.88% | 0 | 586 | 6 |

### Coinbase

MEASURED. 24 of 24 products mapped; 23 had a dated segment. The results below are not judged.

- Mapped but no dated segment: PAU-20DEC30-CDE.

| Cost per side | Net return | Sharpe | Largest fall | Positive years | Traded | Forced closes |
|---|---:|---:|---:|---:|---:|---:|
| 1 bp | -38.30% | -0.195 | 68.34% | 4 | 586 | 6 |
| 12 bps | -69.18% | -0.685 | 75.76% | 0 | 586 | 6 |
| 24 bps | -85.58% | -1.217 | 88.22% | 0 | 586 | 6 |

### Kraken

MEASURED. 17 of 17 products mapped; 17 had a dated segment. The results below are not judged.

| Cost per side | Net return | Sharpe | Largest fall | Positive years | Traded | Forced closes |
|---|---:|---:|---:|---:|---:|---:|
| 1 bp | +149.87% | +0.880 | 48.07% | 5 | 586 | 6 |
| 12 bps | +25.58% | +0.312 | 51.43% | 3 | 586 | 6 |
| 24 bps | -40.83% | -0.306 | 61.71% | 1 | 586 | 6 |

## Run record

STATED. The lead reports that frozen commit `f0f855a42cd58080fe5e58729968f23b75c94a31` reached the remote main branch at 2026-11-26 02:28 UTC. The first clock preflight refused with `P18_SEAL_REFUSED` because the shell contained `GIT_CONFIG_COUNT` for GitHub proxy settings. The lead removed just that variable with `env -u GIT_CONFIG_COUNT` and repeated preflight. The refusal was before a claim, with no change to frozen files or inputs.

MEASURED in the lead's clock-only preflight. It reported 0 FTT stamp anomalies. The counts were:

| Input | Files | Rows |
|---|---:|---:|
| Funding | 3,065 | 320,353 |
| Mark | 3,128 | 2,263,673 |
| Trade | 3,177 | 2,238,542 |

MEASURED. The one-shot lock recorded consumption at 2026-11-26 02:30:04 UTC, then completion. The [saved result](../../research_rig/results_18.json) binds ledger rows 153 and 154 and has SHA-256 `3a1887332b0ba2555f84b541192cb543dffac9e052e13dc412cbc124d5cd3cbc`. The [reporter](../../research_rig/report_18.py) reads only that JSON.
