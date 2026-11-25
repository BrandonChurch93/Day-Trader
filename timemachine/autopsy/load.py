"""Loads every answer and fill from finished TM01 to TM04 session folders. Read only. No TM06, VOID or TWIN-TM06 folder is opened."""
import json, glob, os, re
import settings
MODELS = ["OPUS", "SOL", "NEON", "SONNET", "KIMI", "GROK"]

def sessions(plan):
    out = []
    for d in sorted(glob.glob(f"{settings.RUNS}/{plan}-*")):
        b = os.path.basename(d)
        if b.startswith(("TM06", "VOID")):
            continue
        if not os.path.exists(d + "/result.json"):
            continue
        out.append(d)
    return out

def parse_sid(sid):
    p = sid.split("-")
    plan, model = p[0], p[2]
    month = "-".join(p[3:]) if len(p) > 3 else ""
    return plan, model, month

def crypto_texts():
    """Yield buy actions and written sells (TM01, TM02) with ids, plus no-pick answers count."""
    rows = []
    for plan in ("TM01", "TM02"):
        for d in sessions(plan):
            sid = os.path.basename(d); _, model, month = parse_sid(sid)
            prog = json.load(open(d + "/progress.json"))
            for s in prog["steps"]:
                pk = s.get("pick")
                if not pk:
                    continue
                pid = s.get("pick_id") or pk.get("made_utc", "").replace("-", "").replace(":", "")[:13] + "Z"
                for i, a in enumerate(pk.get("actions", [])):
                    rows.append(dict(id=f"{sid}|{pid}|{i}", sid=sid, plan=plan, model=model, month=month, utc=s["utc"],
                                     kind=a.get("side"), symbol=a.get("symbol"), reason=a.get("reason", ""), thesis=pk.get("thesis", ""),
                                     exits=[e for e in pk.get("exits", []) if e.get("symbol") == a.get("symbol")], pick_id=pid,
                                     sources=pk.get("sources", [])))
    return rows

def crypto_sell_orders():
    rows = []
    for plan in ("TM01", "TM02"):
        for d in sessions(plan):
            sid = os.path.basename(d); _, model, month = parse_sid(sid)
            res = json.load(open(d + "/result.json"))
            for o in res["summary"]["orders"]:
                if o["side"] == "sell":
                    rows.append(dict(id=f"{sid}|{o['order_id']}", sid=sid, plan=plan, model=model, month=month, utc=o.get("filled_utc") or o["utc"],
                                     symbol=o["symbol"], reason=o.get("reason") or "", status=o["status"], cid=o["client_order_id"]))
    return rows

def dial_texts():
    rows = []
    for d in sessions("TM03"):
        sid = os.path.basename(d); _, model, month = parse_sid(sid)
        prog = json.load(open(d + "/progress.json"))
        prev = 1.0
        for s in prog["steps"]:
            tgt = None if s.get("target") is None else s["target"].get("BTC/USD", 0.0)   # an empty target means all cash
            if s.get("asked") and s.get("k", 0) > 0:
                new = s["asked"].get("BTC/USD")
                rows.append(dict(id=f"{sid}|{s['k']}", sid=sid, plan="TM03", model=model, month=month, utc=s["utc"], prev=prev, new=new,
                                 direction="raise" if new > prev else ("cut" if new < prev else "same"), reason=s.get("why") or "",
                                 driver=s.get("driver"), changed=bool(s.get("changed"))))
            if tgt is not None:
                prev = tgt
    return rows

def basket_texts():
    rows = []
    for d in sessions("TM04"):
        sid = os.path.basename(d); _, model, _ = parse_sid(sid)
        run = sid.split("-")[-1]
        prog = json.load(open(d + "/progress.json"))
        held = {}
        for s in prog["steps"]:
            asked = s.get("asked")
            for sym, r in (s.get("reasons") or {}).items():
                m = re.match(r"\s*(added|dropped|kept|trimmed|raised|cut)\b", r, re.I)
                kind = m.group(1).lower() if m else None
                if kind is None and asked is not None:
                    kind = "added" if (asked.get(sym, 0) > 0 and held.get(sym, 0) == 0) else ("dropped" if asked.get(sym, 0) == 0 and held.get(sym, 0) > 0 else "kept")
                rows.append(dict(id=f"{sid}|{s['k']}|{sym}", sid=sid, plan="TM04", model=model, month=run, utc=s["utc"], symbol=sym,
                                 kind=kind, reason=r, k=s["k"]))
            if asked is not None:
                held = dict(asked)
    return rows
