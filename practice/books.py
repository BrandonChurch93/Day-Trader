"""The books of every trader, worked out from the broker's own list of orders. Pure functions, no network, no model.

Nothing here is remembered between runs. Each order the program sends carries a fixed name that starts with PREFIX and
holds the trader's id, so on every run the cash, holdings, closed trades, wins and losses of each trader are counted
again from the fills the broker reports. A fill can therefore never be counted twice or lost, whatever happens to a run."""
import datetime as dt, math, re

PREFIX = "pt1"
FINAL = {"filled", "canceled", "expired", "rejected"}  # the only statuses after which an order can never fill more
DUST_USD = 0.01  # a holding worth less than one cent after a sale is counted as nothing


def cid_for(trader, tag):
    c = re.sub(r"[^a-z0-9.\-]", "-", f"{PREFIX}.{trader}.{tag}".lower())
    assert "." not in trader and len(c) <= 128, c
    return c


def parse_cid(cid):
    """(trader id in lower case, tag) for one of our orders, else None."""
    p = (cid or "").split(".", 2)
    return (p[1], p[2]) if len(p) == 3 and p[0] == PREFIX else None


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return v if math.isfinite(v) else 0.0


def key(symbol):
    return symbol.replace("/", "")


def is_crypto(o):
    return o.get("asset_class") == "crypto" or "/" in (o.get("symbol") or "")


def when(o):
    return o.get("filled_at") or o.get("updated_at") or o.get("submitted_at") or ""


def instant(o):
    """The same moment as a number, so orders sort by real time whatever time zone the text is written in."""
    s = when(o)
    try:
        m = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?(Z|[+-]\d\d:\d\d)", s)
        t = dt.datetime.fromisoformat(m.group(1) + (m.group(2) or ".0")[:7].ljust(7, "0") + ("+00:00" if m.group(3) == "Z" else m.group(3)))
        return (t.timestamp(), s)
    except (AttributeError, ValueError):
        return (0.0, s)


def new_book(start):
    return dict(cash=start, pos={}, dust={}, sym={}, trades={}, closed=[], orders=[], open=[], fees=0.0, by_day={}, bad=[])


def derive(orders, trader_ids, start_usd, fee_rate, fee_in_coin=False):
    """orders: the broker's orders. Returns ({trader id: book}, [orders that are not ours]).
    book: cash, pos {symbol key: qty}, sym {symbol key: symbol as the broker writes it}, trades {symbol key: open trade},
    closed [closed trades], orders [one row per order, oldest first], open [orders that can still fill], fees, by_day
    {UTC date: orders sent}, bad [plain sentences about things that should not happen]."""
    ids = {t.lower(): t for t in trader_ids}; books = {t: new_book(start_usd) for t in trader_ids}; others = []
    by_id = {o.get("id"): o for o in orders if o.get("id")}
    def ours(o, depth=0):
        """(trader, tag) from the order's own name, or from the order it replaced. A replacement gets a new name from the broker."""
        p = parse_cid(o.get("client_order_id"))
        if p or depth > 20 or o.get("replaces") not in by_id:
            return p
        return ours(by_id[o["replaces"]], depth + 1)
    for o in sorted(orders, key=instant):
        p = ours(o)
        if not p:
            others.append(o); continue
        tid = ids.get(p[0])
        if tid is None:  # an order of a trader that is no longer on the list: keep its books so the account still adds up
            tid = ids[p[0]] = p[0].upper(); books[tid] = new_book(start_usd)
        b = books[tid]; k = key(o["symbol"]); b["sym"][k] = o["symbol"]; side = o.get("side"); st = o.get("status")
        fq, fp = num(o.get("filled_qty")), num(o.get("filled_avg_price")); crypto = is_crypto(o)
        day = (o.get("submitted_at") or "")[:10]; b["by_day"][day] = b["by_day"].get(day, 0) + 1
        row = dict(utc=o.get("submitted_at"), filled_utc=o.get("filled_at"), trader=tid, symbol=o["symbol"], side=side, client_order_id=o["client_order_id"], order_id=o.get("id"),
                   broker_status=st, qty=fq or None, asked_qty=num(o.get("qty")) or None, asked_usd=num(o.get("notional")) or None, fill_price=fp or None,
                   notional_usd=None, fee_added_usd=None, status="open")
        b["orders"].append(row)
        moved_on = st == "replaced" and o.get("replaced_by") in by_id  # the order that took its place is in the list and is counted there
        if st not in FINAL and not moved_on:
            b["open"].append(row)
        if side not in ("buy", "sell"):
            b["bad"].append(f"Order {o.get('id')} has no clear side."); continue
        if st == "filled" and not (fq > 0 and fp > 0):
            b["bad"].append(f"Order {o.get('id')} is marked filled and has no fill size or price."); row["status"] = "unclear"; continue
        if st in FINAL or moved_on:
            row["status"] = "filled" if st == "filled" else ("part filled" if fq > 0 else st)
        if fq > 0 and not fp > 0:
            b["bad"].append(f"Order {o.get('id')} shows a fill size and no fill price."); row["status"] = "unclear"; continue
        if not (fq > 0 and fp > 0):
            continue
        notional = fq * fp; fee = notional * fee_rate if crypto else 0.0
        row.update(notional_usd=round(notional, 2), fee_added_usd=round(fee, 4)); b["fees"] += fee
        if side == "buy":
            in_coin = crypto and fee_in_coin
            if b["pos"].get(k, 0.0) == 0.0:
                b["trades"][k] = dict(symbol=o["symbol"], opened_utc=when(o), cost_usd=0.0, back_usd=0.0, first_cid=o["client_order_id"])
            b["cash"] -= notional + (0.0 if in_coin else fee); b["pos"][k] = b["pos"].get(k, 0.0) + b["dust"].pop(k, 0.0) + (fq * (1 - fee_rate) if in_coin else fq)
            b["trades"][k]["cost_usd"] += notional + (0.0 if in_coin else fee)
        else:
            have = b["pos"].get(k, 0.0); t = b["trades"].get(k)
            if t is None or fq > have * (1 + 1e-6) + 1e-9:
                b["bad"].append(f"Order {o.get('id')} sold {fq} of {o['symbol']} and the books held {have}.")
            b["cash"] += notional - fee; left = max(0.0, have - fq)
            if t is not None:
                t["back_usd"] += notional - fee
            if left * fp < DUST_USD:
                b["pos"].pop(k, None)
                if left > 0:
                    b["dust"][k] = left  # too small to sell or to count as a holding, but still in the account, so it is kept for the account check
                if t is not None:
                    g = t["back_usd"] - t["cost_usd"]
                    b["closed"].append(dict(trader=tid, symbol=o["symbol"], opened_utc=t["opened_utc"], closed_utc=when(o), cost_usd=round(t["cost_usd"], 2), gain_usd=round(g, 2),
                                            gain_pct=(g / t["cost_usd"] if t["cost_usd"] > 0 else 0.0), result="win" if g > 0 else ("loss" if g < 0 else "flat")))
                    del b["trades"][k]
            else:
                b["pos"][k] = left
    return books, others
