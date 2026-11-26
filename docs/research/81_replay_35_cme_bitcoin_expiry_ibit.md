# Replay 35. IBIT at monthly CME Bitcoin expiry

MEASURED. **Did not pass, 1 of 6 marks.** Only placement passed. IBIT averaged -0.1626% net per expiry across 34 of 34 eligible events (t -0.72). The mean after dropping the best two was -0.3696%.

STATED. The [frozen rule](../../research_rig/PREREG_35_ibit_cme_expiry.md) bought whole shares at the first eligible SIP ask at or after 11:00 London and sold at the first eligible bid at or after 16:00, within one minute of each clock. It assumed a pre-market limit at the ask filled there and charged zero commission plus historical SEC and FINRA sell fees. The $500 return denominator includes idle cash. The author had previously held entry and exit quotes for the spread screen; the lead had not seen them when fixing the marks, and a separate custodian restaged the judged inputs.

## Frozen marks

| Fixed bar | MEASURED | Verdict |
| --- | ---: | --- |
| At least 30 placed expiry round trips | 34 of 34 | Pass |
| Net expiry mean above zero | -0.1626% | Fail |
| One-sample t at least 2.0 | -0.72 | Fail |
| Net mean above zero after dropping the best two | -0.3696% | Fail |
| Expiry-Friday gap above zero and Welch t at least 2.0 | -0.1398%; Welch t -0.51 | Fail |
| Positive net mean in at least two of three calendar years | 1 of 3 | Fail |

MEASURED. The 33 placed expiry Fridays averaged -0.1922%. The other full-session Friday controls averaged -0.0524% with 108 of 108 placed. The expiry-Friday gap was -0.1398% (Welch t -0.51); the shifted Thursday is not in that comparison.

## By year and shown-only checks

| Year | Expiry trades | MEASURED net mean |
| --- | ---: | ---: |
| 2024 | 12 | -0.2037% |
| 2025 | 12 | +0.0963% |
| 2026 | 10 | -0.4242% |

MEASURED. These checks carry no verdict. The extra friction is per round trip; the Bitstamp spot cross-check is gross, from hourly open to hourly open.

| Shown only | Expiry placed or observed | Expiry mean | Control placed or observed | Control mean |
| --- | ---: | ---: | ---: | ---: |
| IBIT, +2 bps friction | 34/34 | -0.1819% | 108/108 | -0.0714% |
| IBIT, +5 bps friction | 34/34 | -0.2107% | 108/108 | -0.1000% |
| IBIT, 14:00 to 16:00 London | 34/34 | -0.2444% | 107/108 | -0.0702% |
| Bitstamp BTC/USD spot | 34/34 | -0.1056% | 108/108 | -0.0216% |

## Coverage and reading

MEASURED. All 34 expiry windows and all 108 primary controls had placed round trips. The shorter-window control had 1 missing entry (2024-01-12); STATED. The custodian confirmed the provider window was empty. It did not affect the judged rule. STATED. IBIT history starts in January 2024 ([Nasdaq listing notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETP2024-04)), so this is not a replay of all the paper’s post-sample expiries.

The cheap route made the clock testable, but the net expiry mean and the Friday gap were both negative. The earlier Kraken and Robinhood spot routes were stopped on costs; this result does not reopen them. The Bitstamp check was negative too, but the short IBIT history and assumed SIP fills cannot rule out a smaller effect on other venues or in other periods. Futures remain forward-log only, with no build.

## Run record

MEASURED. The saved result records a claim at 2026-11-26 04:50:46 UTC, ledger 170, queue 57. STATED. The lead ran it once after no-return validation. This page reads the saved aggregate only.

- Approval commit `134a64c7fe213ba2919448dcf63fbeb8302a5ee6`
- Freeze commit `0e516956a68e5eaa4c4cebb7c3e15c3955e547e7`
- Saved result SHA-256 `083580210b0f1ba4fc623d23eefbcc24939b818b4bdc454335a8179288cfa8ac`
- Freeze manifest SHA-256 `b670b2bd6fe541ddf42decf96e9b5aa4f2b2c8a6f8c1feb67a42bfd22181b364`
- Input manifest SHA-256 `c552609c662fe01b12883a932ad55dcfff329e50dcec962a40af243462b74449`
