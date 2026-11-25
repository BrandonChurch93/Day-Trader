"""The form an AI trader's decisions must take, and the check that they do. Pure functions, no network, no model.

A pick is one JSON file, practice-picks branch, picks/<TRADER ID>/<pick id>.json. The AI decides what goes in it. The
plain program reads it, checks it against this form and against the trader's pretend budget, and places the orders. A
file that does not fit the form exactly is refused whole and nothing in it is traded.

{"trader": "A01",                        the trader's id, the same as the folder
 "made_utc": "2026-11-25T15:30:00Z",     when the decision was made
 "expires_utc": "2026-11-25T17:00:00Z",  after this, anything not yet traded is dropped
 "thesis": "one short paragraph",        why, in plain words (shown on the owner's screen)
 "sources": ["https://..."],             optional
 "actions": [                            may be empty
   {"symbol": "NVDA", "side": "buy", "usd": 250, "reason": "..."},        buy this many pretend dollars
   {"symbol": "BTC/USD", "side": "sell", "share": 1.0, "reason": "..."}], sell this share of the holding (1.0 is all)
 "exits": [                              optional. Checked by the plain program on every run until the holding is gone
   {"symbol": "NVDA", "stop": 120.5, "target": 140.0, "by_utc": "2026-11-25T20:45:00Z"}]}  any one of the three sells all
"""
import datetime as dt, math, re

PICK_ID = re.compile(r"[0-9]{8}T[0-9]{4}Z(-[a-z0-9]{1,12})?")
STOCK = re.compile(r"[A-Z]{1,5}(\.[A-Z])?")
CRYPTO = re.compile(r"[A-Z0-9]{2,10}/USD")
TOP = {"trader", "made_utc", "expires_utc", "thesis", "sources", "actions", "exits"}


def parse_t(s):
    """Any RFC 3339 time (Z or an offset, any number of decimals) as an aware UTC datetime."""
    m = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?(Z|[+-]\d\d:\d\d)", s if isinstance(s, str) else "")
    if not m:
        raise ValueError(f"not a time: {s!r}")
    frac = (m.group(2) or ".0")[:7]; off = "+00:00" if m.group(3) == "Z" else m.group(3)
    return dt.datetime.fromisoformat(m.group(1) + frac + off).astimezone(dt.timezone.utc)


def symbol_ok(s):
    return isinstance(s, str) and bool(STOCK.fullmatch(s) or CRYPTO.fullmatch(s))


def pos_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x > 0


def validate(p, trader_id, pick_id, now, max_life_hours, max_actions):
    """Returns a list of plain sentences. Empty means the pick fits the form."""
    e = []
    if not PICK_ID.fullmatch(pick_id):
        e.append("The file name is not a pick id like 20261125T1530Z or 20261125T1530Z-b.")
    if not isinstance(p, dict):
        return e + ["The file is not a JSON object."]
    if set(p) - TOP:
        e.append(f"Unknown fields: {sorted(set(p) - TOP)}.")
    if p.get("trader") != trader_id:
        e.append("The trader field does not match the folder.")
    try:
        made, exp = parse_t(p.get("made_utc")), parse_t(p.get("expires_utc"))
        if made > now + dt.timedelta(minutes=5):
            e.append("made_utc is in the future.")
        if not made < exp <= made + dt.timedelta(hours=max_life_hours):
            e.append(f"expires_utc must be after made_utc and at most {max_life_hours:g} hours after it.")
    except ValueError as x:
        e.append(f"made_utc or expires_utc: {x}.")
    if not (isinstance(p.get("thesis"), str) and 0 < len(p["thesis"]) <= 2000):
        e.append("thesis must be text, 1 to 2000 characters.")
    if not (isinstance(p.get("sources", []), list) and all(isinstance(s, str) and len(s) <= 500 for s in p.get("sources", [])) and len(p.get("sources", [])) <= 20):
        e.append("sources must be a list of at most 20 short strings.")
    acts = p.get("actions")
    if not isinstance(acts, list) or len(acts) > max_actions:
        return e + [f"actions must be a list of at most {max_actions:g}."]
    for i, a in enumerate(acts):
        if not isinstance(a, dict) or not symbol_ok(a.get("symbol")) or a.get("side") not in ("buy", "sell") or not (isinstance(a.get("reason"), str) and 0 < len(a["reason"]) <= 500):
            e.append(f"Action {i}: needs a symbol like NVDA or BTC/USD, a side of buy or sell, and a reason of 1 to 500 characters."); continue
        want = {"symbol", "side", "reason", "usd" if a["side"] == "buy" else "share"}
        if set(a) != want:
            e.append(f"Action {i}: a {a['side']} has exactly these fields: {sorted(want)}."); continue
        if a["side"] == "buy" and not pos_num(a["usd"]):
            e.append(f"Action {i}: usd must be a number above zero.")
        if a["side"] == "sell" and not (pos_num(a["share"]) and a["share"] <= 1):
            e.append(f"Action {i}: share must be above 0 and at most 1.")
    seen = [a.get("symbol") for a in acts if isinstance(a, dict)]
    if len(seen) != len(set(seen)):
        e.append("One symbol appears in more than one action.")
    ex = p.get("exits", [])
    if not isinstance(ex, list) or len(ex) > 50:
        return e + ["exits must be a list."]
    for i, x in enumerate(ex):
        if not isinstance(x, dict) or not symbol_ok(x.get("symbol")) or set(x) - {"symbol", "stop", "target", "by_utc"} or len(x) < 2:
            e.append(f"Exit {i}: needs a symbol and at least one of stop, target, by_utc, and nothing else."); continue
        if any(k in x and not pos_num(x[k]) for k in ("stop", "target")) or ("stop" in x and "target" in x and not x["stop"] < x["target"]):
            e.append(f"Exit {i}: stop and target must be numbers above zero, with stop below target.")
        if "by_utc" in x:
            try:
                parse_t(x["by_utc"])
            except ValueError:
                e.append(f"Exit {i}: by_utc is not a time.")
    return e
