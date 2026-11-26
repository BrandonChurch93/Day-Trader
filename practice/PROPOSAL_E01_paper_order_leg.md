# Proposal: a practice-order leg for E01

Status: proposal only, 2026-11-26. Not built into the desk. Needs the owner's practice key and a ledger row first. The forward log (`practice/forward_e01.py`) does not need any of this.

## What it would add

A market-on-close order of whole TLT shares on the Alpaca practice account (pretend money) at each E01 entry and exit. It would show how Alpaca's practice account fills such an order, and test the order path before any real use.

## What it cannot show

- STATED by Alpaca: practice orders are filled by a simulation against the best current quote, not sent to an exchange ([Alpaca](https://docs.alpaca.markets/docs/paper-trading)).
- STATED by Alpaca staff on its forum: a practice market-on-close order is filled like a market order at the close, a buy at the ask and a sell at the bid, not at the auction price. Part of it may fill and the rest expire ([Alpaca forum](https://forum.alpaca.markets/t/paper-moc-orders-partially-fill-remainder-expires-same-setup-on-live-works/19155)).
- So a practice fill measures about half the quoted spread at 4:00 pm. The real auction price is already in the forward log.
- STATED by one Alpaca page: opg and cls orders are only for Elite Smart Router users ([Alpaca learn](https://alpaca.markets/learn/start-paper-trading)). Whether the owner's practice account takes them is UNKNOWN until one is sent.

## What the owner would add

One Alpaca practice (paper) key pair, made on the practice account page. Either:

- repo secrets named `ALPACA_PAPER_KEY_ID` and `ALPACA_PAPER_SECRET_KEY`, the names the desk already reads; or
- a saved credential for `paper-api.alpaca.markets`, if the leg runs from the research machine.

No key goes in a file. The saved data credential reaches data.alpaca.markets only and cannot place a practice order.

## The broker change it needs

`practice/broker.py` sends one market order with `day` or `gtc` only. It would also need `cls`, whole shares only:

```python
assert side in ("buy", "sell") and tif in ("day", "gtc", "cls") and (qty is None) != (notional is None)
if tif == "cls":
    assert qty is not None and float(qty) == int(qty) and qty >= 1, "market-on-close takes whole shares only"
```

Alpaca does not take fractional or notional amounts on cls orders ([Alpaca orders](https://docs.alpaca.markets/docs/orders-at-alpaca)). The broker reach tests in `practice/test_trader.py` would list the change, so the test that fails when the reach grows still means something.

## Order rules a runner would follow

1. One order per leg, `type` market, `time_in_force` cls, whole shares worth at most $1,000.00 of pretend money (`practice_amount_per_trader_usd`). The exit sells exactly the shares the entry filled.
2. Sent between 9:30 am and 3:45 pm New York time on the session day. Alpaca rejects cls after 3:50 pm ([Alpaca orders](https://docs.alpaca.markets/docs/orders-at-alpaca)). Nasdaq takes market-on-close until 3:55 pm ([Nasdaq](https://www.nasdaqtrader.com/content/productsservices/Trading/ClosingCrossfaq.pdf)).
3. Refuses unless the account number starts with PA and the broker clock and calendar show a 4:00 pm close that day.
4. No cancel, no replace, no close-all. Never sends twice; an unclear answer is checked by client order id.
5. After the close it records the fill next to the forward log's cross and SIP close, with slip in bps.

A draft of that runner with ten tests on a pretend broker was written off repo during planning. It is not in the repo and has never reached Alpaca.
