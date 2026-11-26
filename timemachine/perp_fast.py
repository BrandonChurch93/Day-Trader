"""A faster copy of perp.run_perp for the scorer's twin draws (plan TM06). Live sessions never use this file; they keep perp.py.

Same results to the last digit as perp.run_perp: every float is made by the same operations in the same order, and every sum
is a builtin sum() over the same terms in the same order (sum() of floats is compensated in Python 3.12 and later, so the
sequence passed to it must match, not only the values). What is saved is per-minute overhead in perp.p_scan:
  - the maintenance check copied the whole price dict each minute (adv = dict(px)) and read every term through dict.get;
    here the held symbols' terms x * price and maint * abs(x) * price are kept in lists and only the minute's symbol changes;
  - the peak update copied the book dict (value_at(dict(book, last_px=px), px)); here it is cash + sum(the same terms).
The lists are rebuilt from book["qty"] (its own order) after any trade in the scan (a stop, a target or a close-out).
test_perp_fast.py compares this with perp.run_perp on made-up paths; tm06.py uses it only for twin draws.
"""
import datetime as dt

from timemachine import perp as P

UTC = dt.timezone.utc


def p_scan(book, minutes, t0, t1, pp):
    """perp.p_scan with the same results; see the module note."""
    a, b = int(t0.timestamp()), int(t1.timestamp()); ev = P.funding_times(pp, a, b); ei = 0; nev = len(ev)
    px = dict(book["last_px"]); rec = dict(funding_usd=0.0, fallback_hours=0, closeout=None, exits=[])
    held0, flat_t = bool(book["qty"]), None
    maint = pp["maint"]

    def build():
        items = list(book["qty"].items())
        idx = {y: i for i, (y, _) in enumerate(items)}
        xs = [x for _, x in items]; ma = [maint[y] * abs(x) for y, x in items]
        pv = [px.get(y, 0.0) for y, _ in items]
        return items, idx, xs, ma, [x * p for x, p in zip(xs, pv)], [m * p for m, p in zip(ma, pv)]

    items, idx, xs, ma, eqt, ndt = build()
    for t, s, o, h, l, c in P.scan_rows(minutes, a, b, book["qty"]):
        while ei < nev and ev[ei][0] <= t:
            P.fund(book, ev[ei][0], ev[ei][1], px, pp, rec); ei += 1
        q = book["qty"].get(s, 0.0); ex = book["exits"].get(s)
        if q and ex:
            hit = P.exit_hit(q, ex, o, h, l)
            if hit:
                lv, kind, gap = hit; tr = P.trade(book, s, -q, lv, pp); book["target"].pop(s, None); book["exits"].pop(s, None)
                x = dict(utc=P.iso(dt.datetime.fromtimestamp(t, UTC)), symbol=s, kind=kind, level=ex.get(kind), filled_at=lv, gap=gap, price=tr["price"], side=tr["side"], qty=tr["qty"])
                rec["exits"].append(x); book["exits_hit"].append(x)
                if not book["qty"] and flat_t is None:
                    flat_t = t
                items, idx, xs, ma, eqt, ndt = build()
        if book["qty"]:
            j = idx.get(s); q = book["qty"].get(s, 0.0)
            if j is not None and q:
                av = l if q > 0 else h
                e2 = list(eqt); e2[j] = xs[j] * av; n2 = list(ndt); n2[j] = ma[j] * av
            else:
                if q:  # s held but not in the lists: cannot happen, as the lists follow book["qty"]
                    raise AssertionError("perp_fast: held symbol missing from the lists")
                e2, n2 = eqt, ndt
            eq = book["cash"] + sum(e2); need = sum(n2)
            book["largest_drop"] = min(book["largest_drop"], max(eq, 0.0) / book["peak"] - 1 if book["peak"] > 0 else 0.0)
            if eq < need:
                adv = dict(px)
                if q:
                    adv[s] = l if q > 0 else h
                for y, x in sorted(book["qty"].items()):
                    P.trade(book, y, -x, adv[y], pp, penalty=pp["penalty"])
                book["qty"] = {}; short = max(0.0, -book["cash"])
                if short:
                    book["shortfall_usd"] += short; book["cash"] = 0.0
                rec["closeout"] = dict(utc=P.iso(dt.datetime.fromtimestamp(t, UTC)), symbol=s, value_before=eq, value_after=book["cash"], shortfall_usd=short)
                book["closeouts"].append(rec["closeout"]); book["pending"] = True; flat_t = t if flat_t is None else flat_t
                book["largest_drop"] = min(book["largest_drop"], book["cash"] / book["peak"] - 1 if book["peak"] > 0 else 0.0)
                items, idx, xs, ma, eqt, ndt = build()
        px[s] = c
        j = idx.get(s)
        if j is not None:
            eqt[j] = xs[j] * c; ndt[j] = ma[j] * c
        if book["qty"]:
            book["peak"] = max(book["peak"], book["cash"] + sum(eqt))
    while ei < nev:
        P.fund(book, ev[ei][0], ev[ei][1], px, pp, rec); ei += 1
    for s, p in px.items():
        book["last_px"][s] = p
    rec["held_seconds"] = ((flat_t if flat_t is not None else b) - a) if held0 else 0
    book["held_seconds"] = book.get("held_seconds", 0) + rec["held_seconds"]
    return rec


def run_perp(meta, table, answers, pp, minutes, cfg):
    """perp.run_perp with the faster scan. Same (book, records, final value)."""
    if meta.get("tm07_arm") == "C":
        raise ValueError("conditional desk answers require score_tm07.replay")
    book = P.new_book(cfg["tm_account_start_usd"], meta.get("opening")); wakes = [P.parse(w) for w in meta["wakes"]]; end = P.parse(meta["end_utc"])
    tf = [P.scan_from(table["rows"][k], wakes[k]) for k in range(len(answers))]; recs = []
    for k, (w, ex) in enumerate(answers):
        if k > 0:
            recs[-1]["scan"] = p_scan(book, minutes, tf[k - 1], tf[k], pp)
        recs.append(P.p_step(book, w, ex, table["rows"][k], pp, k == 0))
    if recs:
        recs[-1]["scan"] = p_scan(book, minutes, tf[-1], end, pp)
    for s, p in table["end_marks"].items():
        book["last_px"][s] = p
    return book, recs, max(0.0, P.value_at(book, table["end_marks"]))
