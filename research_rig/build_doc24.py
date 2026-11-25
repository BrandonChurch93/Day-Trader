"""Builds docs/research/24_order_book_costs.md from books_summary.json. Run books_summary.py first."""
import json
o = json.load(open("books_summary.json")); P = o["pairs"]
import rig2 as R
SLIP = R.SLIP
STABLE = ("USDT", "USDC", "USDG", "EUR", "GBP", "AUD", "SOFID", "BUSD")
def nm(k):
    v, p = k.split("|"); q = p
    for a, b in (("XXBTZUSD", "BTC"), ("XETHZUSD", "ETH"), ("XXRPZUSD", "XRP"), ("XLTCZUSD", "LTC"), ("XXLMZUSD", "XLM"), ("XXMRZUSD", "XMR"), ("XZECZUSD", "ZEC"), ("XDGUSD", "DOGE"), ("USDTZUSD", "USDT"), ("ZEURZUSD", "EUR"), ("ZGBPZUSD", "GBP")):
        if p == a: q = b
    if q.endswith("USDT") and len(q) > 4: q = q[:-4] + " (vs USDT)"
    elif q.endswith("USD") and len(q) > 3: q = q[:-3]
    return v, q
rows = []
for k, r in P.items():
    v, q = nm(k)
    if q.split(" ")[0] in STABLE: continue
    rows.append((v, q, r))
f = lambda x: "book too thin" if x is None else f"{x:.1f}"
def tab(v):
    t = "| Coin | Samples | Quoted spread, middle | $100, middle | $1,000, middle | $1,000, worst 5% | $10,000, middle | $10,000, worst 5% | $10,000, worst seen |\n|---|---|---|---|---|---|---|---|---|\n"
    for vv, q, r in sorted([x for x in rows if x[0] == v], key=lambda x: x[2]["cost_10k_bps"]["median"] if x[2]["cost_10k_bps"]["median"] is not None else 1e9):
        t += f"| {q} | {r['samples']} | {r['spread_bps']['median']:.1f} | {f(r['cost_100_bps']['median'])} | {f(r['cost_1k_bps']['median'])} | {f(r['cost_1k_bps']['p95'])} | {f(r['cost_10k_bps']['median'])} | {f(r['cost_10k_bps']['p95'])} | {f(r['cost_10k_bps']['max'])} |\n"
    return t
def get(v, q): return next(r for vv, qq, r in rows if vv == v and qq == q)
kb, ke, bb, be_ = get("Kraken", "BTC"), get("Kraken", "ETH"), get("Binance.US", "BTC"), get("Binance.US", "ETH")
alts = [r for v, q, r in rows if v == "Kraken" and q not in ("BTC", "ETH")]
over5 = sum(r["cost_1k_bps"]["p95"] > SLIP for r in alts); over25 = sum(r["cost_10k_bps"]["p95"] > 25 for r in alts)
doc = f"""# 24. What it costs to cross the order book in small size

Status: research measurement. Proposed by research. No owner decision is recorded here.

Date: 2026-11-25. Every number is MEASURED from public order books and placed here by `research_rig/build_doc24.py` from `research_rig/books_summary.json`.

## Why

Every replay charges the venue's fee plus a fixed slippage of {SLIP:.0f} bps per side for bitcoin and ether, and replay 04 charges 25 bps for smaller coins. Those slippage numbers were assumptions. This checks them against live order books.

## What was done

- Once every two minutes from {o['first_sample_utc']} to {o['last_sample_utc']} UTC ({o['rounds']} rounds), the public order book was read for the 30 most traded US dollar pairs on Kraken and the 12 most traded on Binance.US.
- For each, the cost of buying or selling $100, $1,000 and $10,000 at once was worked out by walking down the book, in bps against the mid price. One side. Fees are not included.
- Only these summary costs were kept. The order books themselves were not stored.
- Rows for stablecoins and currencies are left out of the tables. {o['error_rows']} requests returned an error and are not counted.

## Bottom line

- Bitcoin on Kraken: $1,000 cost {f(kb['cost_1k_bps']['median'])} bps in the middle case and {f(kb['cost_1k_bps']['p95'])} bps in the worst 5%. $10,000 cost {f(kb['cost_10k_bps']['median'])} and {f(kb['cost_10k_bps']['p95'])} bps. Ether: {f(ke['cost_1k_bps']['median'])} and {f(ke['cost_1k_bps']['p95'])} bps for $1,000.
- Bitcoin on Binance.US: $1,000 cost {f(bb['cost_1k_bps']['median'])} bps in the middle case and {f(bb['cost_1k_bps']['p95'])} bps in the worst 5%. $10,000 cost {f(bb['cost_10k_bps']['median'])} and {f(bb['cost_10k_bps']['p95'])} bps. Ether: {f(be_['cost_1k_bps']['median'])} and {f(be_['cost_1k_bps']['p95'])} bps for $1,000.
- So on this night the {SLIP:.0f} bps assumed for bitcoin and ether was higher than what the book charged at these sizes. The replays were not flattered by it.
- Smaller coins on Kraken: of {len(alts)} coins sampled, {over5} cost more than {SLIP:.0f} bps for $1,000 in their worst 5% of samples, and {over25} cost more than 25 bps for $10,000.
- This is one night. Books are usually thinner in fast moves, which is when trend rules trade. That is STATED from general knowledge and not measured here. Treat these numbers as a floor, not an average.

## Kraken

{tab('Kraken')}
## Binance.US

{tab('Binance.US')}
## What this does not show

- A stressed market. Whether the sample window was calm or not was not measured.
- Hidden costs of a market order that arrives a moment late, or of a book that changes between the read and the trade.
- Coins outside the most traded 30. The wide basket in replay 04 reaches further down the list, where books are thinner.
- Whether a resting limit order would be filled. That needs trade-by-trade data and is not tested.

## Files

- Sampler and raw samples: outside the repo. Summary: `research_rig/books_summary.py`, `research_rig/books_summary.json`
"""
assert "—" not in doc
open("../docs/research/24_order_book_costs.md", "w").write(doc); print(len(doc.splitlines()), "lines")
