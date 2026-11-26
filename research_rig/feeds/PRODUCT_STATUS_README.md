# Product-status forward watcher (Queue row 84)

Polls the documented public REST market-data endpoints of Coinbase Exchange and Kraken at most once every 5 minutes (`--interval-sec >= 300`, enforced in code) to build an append-only, forward-only log of USD spot product status transitions (`online`, `limit_only`, `cancel_only`, `post_only`, `trading_disabled`, `delisted`, pair additions, and pair removals).

This logger exists to supply a permitted, documented data path for TM07's deterministic defensive exit rule (Queue row 72), replacing exchange HTML notice pages that refused automated reads in Round 21.

## Documented API terms and rate limits

### Coinbase Exchange (`GET https://api.exchange.coinbase.com/products`)

- Rate limits ([Coinbase REST Rate Limits Overview](https://docs.cdp.coinbase.com/exchange/rest-api/rate-limits)): "Public endpoints are throttled by IP and private endpoints by profile ID." "Requests per second per IP: 10" and "Requests per second per IP in bursts: Up to 15". Polling once every 300 seconds uses 0.0033 requests per second (1/3000th of the documented limit).
- Terms ([Coinbase Market Data Terms of Use](https://www.coinbase.com/legal/market_data)): "Your use of Market Data is exclusively for you or your entity's personal or research purposes and may not be used to build an application intended for use by end users other than for you or your officers/employees." Restrictions: no redistribution or dissemination to third parties, no creation of indexes or benchmarks, and per Coinbase's updated Market Data Terms (referenced in [Tardis Terms Clause 23](https://docs.tardis.dev/legal/terms-of-service)), no use of Coinbase Market Data to "develop, train, fine-tune, validate, benchmark or otherwise improve any artificial intelligence or machine learning model, algorithm, agent or other automated system."
- Compliance note: all output is stored off-repo for personal/internal research and deterministic rule-based exit checks only. Do not redistribute the logged files and do not feed Coinbase product-status logs into AI/ML model training or agent context.

### Kraken (`GET https://api.kraken.com/0/public/AssetPairs`)

- Rate limits ([Kraken Support, What are the API rate limits?](https://support.kraken.com/articles/206548367-what-are-the-api-rate-limits-), updated Oct 1, 2026): "The Spot public endpoints are rate limited by IP address and currency pair for calls to Trades and OHLC, and by IP address only for calls to all other public endpoints. Calling the public endpoints at a frequency of 1 per second (or less) would remain within the rate limits, but exceeding this frequency could cause the calls to be rate limited." Polling once every 300 seconds uses 0.0033 requests per second (1/300th of the documented limit).
- Terms ([Kraken APIs Introduction](https://docs-legacy.kraken.com/api/docs/guides/global-intro/)): "You must seek our prior permission for certain uses of the Kraken API's. This includes, but is not limited to, any non-personal commercial use of data from publicly accessible endpoints, such as market data, exchange status, and any other data."
- Compliance note: personal, non-commercial research and personal account defense only; stored off-repo.

## Output files and disk budget

Default output directory (off-repo): `/home/user/workspace/rig/data/status_forward/`

- `transitions.jsonl`: append-only JSONL written only when a USD pair is added, removed, or changes a tracked status field.
- `daily_snapshots.jsonl`: append-only JSONL written at most once per UTC calendar day (roughly 45 to 60 KB per day, under 25 MB per year).
- `state.json`: atomic current-state snapshot used to detect transitions across restarts without duplicating daily snapshots.
- `heartbeat.json`: atomic JSON file updated on every poll with `ts_utc`, `pid`, `ok`, `polls_ok`, `polls_err`, `transitions_total`, `coinbase_usd_count`, `kraken_usd_count`, and `last_error`.

## Running and testing

Run synthetic unit tests (no network calls):

```bash
python3 -m unittest research_rig/feeds/test_product_status_watcher.py
```

Run a single live poll:

```bash
python3 research_rig/feeds/product_status_watcher.py --once --out-dir /home/user/workspace/rig/data/status_forward
```
