"""Pinned, retrospective US roster for Replay 17's shown-only cell."""
from hashlib import sha256
import json

NAME = "us_shortable_2026-11-25.json"
SHA256 = "50be7cc83aaa8fe22b401ba0531d987a63c3b37a220c9373fd8c5bd200342faf"
EXCLUDED = {"USDC", "PAXG", "BTC", "ETH"}
# Roster tickers identify these CMC assets, never an exchange ticker alone.
# Binance pairs, migration boundaries and Monday eligibility are then resolved
# by the same dated identity path as the rest of the replay.
IDS = {
    "AAVE":7278,"ADA":2010,"ALGO":4030,"AVAX":5805,"BCH":1831,"BNB":1839,
    "CRV":6538,"DOGE":74,"DOT":6636,"ENA":30171,
    "HBAR":4642,"HYPE":32196,"LINK":1975,"LTC":2,"NEAR":6535,"ONDO":21159,
    "PENGU":34466,"PEPE":24478,"RENDER":5690,"SHIB":5994,"SOL":5426,
    "SUI":20947,"TRX":1958,"UNI":7083,"VVV":35509,"WLD":13502,"XLM":512,
    "XRP":52,"ZEC":1437,
}


def rows(raw):
    if sha256(raw).hexdigest()!=SHA256:
        raise ValueError("US shortable roster differs from the pinned source")
    source = json.loads(raw)
    measured = [r["coin"] for r in source["measured_coins"]]
    if (source["measured_count"]!=len(measured) or len(set(measured))!=len(measured)
        or set(measured)!=set(IDS)|EXCLUDED or len(set(IDS.values()))!=len(IDS)):
        raise ValueError("US shortable roster has unmapped or duplicate measured coins")
    return [{"symbol":s,"id":IDS[s]} for s in sorted(IDS)]
