# research_rig: a research tool, not the product

This folder holds the small test rig used during research to replay rules on past prices and to run a first pilot of AI models making trading calls. It exists to produce evidence for `docs/research/`.

- It is not the trading system and no part of it is meant to become the trading system. The product is built once, from an approved plan, as `docs/quality/` says.
- It places no orders, holds no keys and talks to no broker.
- It reads public price bars only. The raw bars are not stored here. `fetch.py` downloads them again into `data/`, which git ignores.

## Rules the rig keeps

| Rule | Where |
|---|---|
| Every test is written down before it runs: question, data, rules, costs, pass marks | `PREREG_*.md` |
| Every rule tried is counted, whether it worked or not | `TRIAL_LEDGER.md` |
| The engine must pass checks with known answers before a result counts | `fixtures.py` |
| A rule decides on a finished bar and fills on the next one | `engine.py` |
| Thresholds are named by their key in `config/thresholds.yaml` | `run_01b.py` |
| A fail is reported as a fail | `docs/research/12_replay_01_crypto_trend.md` |

## Files

| File | What it is |
|---|---|
| `engine.py` | The replay engine: fills, costs, the measures, and the checks for luck |
| `rules.py` | The nine textbook trend rules |
| `fixtures.py` | Engine checks with known answers |
| `fetch.py` | Downloads Bitstamp and Kraken public bars |
| `run_01.py`, `run_01b.py`, `run_01c.py`, `report_01d.py`, `tables_01.py`, `build_doc12.py` | Replay 01, its pass marks, its two method checks, and the tables in research 12 |
| `results_01*.json`, `passmarks_01.json`, `tables_01.md` | Outputs of those commands |
| `pilot/server.py` | Releases one day of prices at a time to a model and records its answer before the next day is shown |
| `pilot/decisions.jsonl` | Every answer every model gave in pilot 02, with the server's time stamp |
| `score_02.py`, `results_02.json` | Scoring of pilot 02 |

Needs Python 3 with numpy, pandas and scipy.
