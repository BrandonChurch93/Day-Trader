"""TM07 simulated order rules. No broker, model, tape fetch or clock calls."""
from copy import deepcopy
from itertools import groupby
import math

from timemachine import perp as P

MINUTE = 60


def number(value):
    return type(value) in (int, float) and abs(value) <= 1e100 and math.isfinite(value)


def guarded_trade(book, symbol, dq, opens, pp, gross):
    """Only accept a costed fill within the cap, or a provable risk reduction."""
    price = opens[symbol]
    v, g = P.value_at(book, opens), P.gross_at(book, opens)
    q = book["qty"].get(symbol, 0)
    estimate = deepcopy(book)
    P.trade(estimate, symbol, dq, price, pp)
    v2, g2 = P.value_at(estimate, opens), P.gross_at(estimate, opens)
    if v <= 0 or v2 <= 0:
        return None, "zero_equity"
    if g2 > gross*v2 + 1e-8 and not (abs(q+dq) < abs(q) and g2*v < g*v2):
        return None, "gross_limit"
    need = sum(pp["maint"][s]*abs(qty)*opens[s] for s, qty in estimate["qty"].items())
    if v2 < need:
        return None, "maintenance"
    return P.trade(book, symbol, dq, price, pp), None


def reducing(book, symbol, dq):
    q = book["qty"].get(symbol, 0)
    return q*(q+dq) >= 0 and abs(q+dq) < abs(q)


def stamp(tick):
    return P.iso(P.dt.datetime.fromtimestamp(tick, P.UTC))


def normalize_conditions(items, marks, symbols, wake, end, max_hours, gross):
    if not isinstance(items, list):
        raise ValueError("conditions must be a list")
    out = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("bad condition")
        sym, direction = item.get("symbol"), item.get("direction")
        h, w = item.get("hours"), item.get("weight")
        levels = item.keys() & {"pct", "price"}
        if (set(item) - {"symbol", "direction", "hours", "weight", "pct", "price", "note_ids", "evidence_ids"}
                or sym not in symbols or sym in out or direction not in ("above", "below")
                or type(h) is not int or not 1 <= h <= max_hours or not number(w) or abs(w) > gross
                or len(levels) != 1 or not number(marks.get(sym)) or marks[sym] <= 0):
            raise ValueError("bad condition fields or missing reference mark")
        ref = marks[sym]
        key = next(iter(levels))
        level = item[key]
        if not number(level) or level <= 0:
            raise ValueError("condition level must be a positive number")
        if key == "pct":
            level = ref * (1 + (1 if direction == "above" else -1) * level / 100)
        if (not number(level) or level <= 0 or (direction == "above" and level <= ref)
                or (direction == "below" and level >= ref)):
            raise ValueError("condition must be beyond the current mark")
        out[sym] = dict(id=f"{wake}:{sym}", symbol=sym, direction=direction, level=level, ratio=level/ref,
                        wake=wake, hours=h, expiry=min(end, wake + 3600*h), weight=w,
                        note_ids=item.get("note_ids", []), evidence_ids=item.get("evidence_ids", []))
    return out


class Orders:
    """Clock and book state are owned by caller; all events are deterministic."""

    def __init__(self, active=None, delay=0):
        self.active = deepcopy(active or {})
        self.events = []
        self.delay = delay

    def event(self, kind, order, at, **extra):
        self.events.append(dict(kind=kind, utc=at, order_id=order["id"], symbol=order["symbol"],
                                wake=order["wake"], decision_id=order.get("decision_id"),
                                note_ids=order["note_ids"], evidence_ids=order["evidence_ids"],
                                expiry=order["expiry"], level=order["level"], target=order["weight"],
                                observed=order.get("observed"), **extra))

    def remove(self, sym, kind, at, **extra):
        self.event(kind, self.active.pop(sym), at, **extra)

    def expire(self, at):
        for sym, order in sorted(self.active.items()):
            if at >= order["expiry"]:
                self.remove(sym, "expired", at)

    def submit(self, bundle, book, at):
        self.expire(at)
        weights = bundle.get("weights")
        target = book["target"]
        keeps = set(bundle.get("keep", ()))
        new = bundle.get("conditions", {})
        for sym, order in sorted(self.active.items()):
            changed = weights is not None and weights.get(sym, 0) != target.get(sym, 0)
            if sym in new or order["id"] not in keeps or (changed and "observed" in order):
                reason = "replaced" if sym in new else "immediate_target" if changed and "observed" in order else "not_kept"
                self.remove(sym, "cancelled", at, reason=reason)
        for sym, order in sorted(new.items()):
            self.active[sym] = deepcopy(order)
            self.event("armed", order, at)

    def execute_open(self, book, pp, at, opens, gross):
        self.expire(at)
        if not book["qty"].keys() <= opens.keys():
            return
        ready = []
        for sym, order in sorted(self.active.items()):
            if sym in opens and "observed" in order and order["observed"] + self.delay <= at:
                px = opens[sym]
                gap_exit = book["qty"].get(sym) and P.exit_hit(book["qty"][sym], book["exits"].get(sym, {}), px, px, px)
                if gap_exit:
                    self.remove(sym, "cancelled", at, reason="protective_exit")
                    continue
                held = P.weights_at(book, opens).get(sym, 0.0)
                ready.append((not (held * order["weight"] >= 0 and abs(order["weight"]) < abs(held)), sym))
        for _, sym in sorted(ready):
            order = self.active[sym]
            mark = opens[sym]
            weights = P.weights_at(book, opens)
            current = weights.get(sym, 0)
            other = sum(abs(v) for s, v in weights.items() if s != sym)
            value = P.value_at(book, opens)
            w = order["weight"]
            quantity = book["qty"].get(sym, 0)
            dq = w * value / mark - quantity
            target_gross = other + abs(w)
            saved_target_gross = abs(w) + sum(abs(v) for s,v in book["target"].items() if s != sym)
            if saved_target_gross > gross + 1e-10:
                trade, reason = None, "target_gross_limit"
            elif abs(dq)*mark < 1e-9 or (abs(w-current) < pp["min_change"] and w != 0 and quantity*w >= 0):
                trade, reason = None, "small_change"
            else:
                trade, reason = guarded_trade(book, sym, dq, opens, pp, gross)
            if reason:
                self.remove(sym, "refused", at, reason=reason, open=mark,
                            gross_wanted=target_gross,saved_target_gross=saved_target_gross)
                continue
            book["last_px"][sym] = mark
            if w:
                book["target"][sym] = w
            else:
                book["target"].pop(sym, None)
            if quantity*w <= 0:
                book["exits"].pop(sym, None)
            self.remove(sym, "filled", at, open=mark, previous_weight=current, gross_wanted=target_gross,
                        spread_usd=abs(dq) * mark * pp["hs"][sym], trade=trade)

    def observe_close(self, bar, protected=()):
        start, sym, _, high, low, _ = bar
        t = start + MINUTE
        order = self.active.get(sym)
        if not order:
            return
        if sym in protected:
            self.remove(sym, "cancelled", t, reason="protective_exit")
        elif "observed" not in order and order["wake"] <= start and t < order["expiry"]:
            if (high > order["level"] if order["direction"] == "above" else low < order["level"]):
                order["observed"] = t
                self.event("triggered", order, t, bar_start=start, high=high, low=low)

    def advance(self, book, pp, rows, start, end, gross, on_open=None, last=False):
        """Boundary funding, open maintenance, gap exits, new fills, bar-close checks."""
        at = start
        total = dict(exits=[], closeout=None, funding_usd=0.0, fallback_hours=0, held_seconds=0)
        book.setdefault("held_seconds",0)
        events = iter(P.funding_times(pp, start-1, end if last else end-1))
        upcoming = next(events, None)
        blocked = False

        def fund_until(tick, opens):
            nonlocal upcoming
            while upcoming and upcoming[0] <= tick:
                t, s = upcoming
                prices = dict(book["last_px"])
                if t == tick:
                    prices.update(opens)
                P.fund(book, t, s, prices, pp, total)
                upcoming = next(events, None)

        def block(tick):
            nonlocal blocked
            for s in sorted(self.active):
                self.remove(s, "cancelled", tick, reason="maintenance")
            book.update(target={}, exits={}, pending=False)
            blocked = True

        def hold(seconds):
            if book["qty"]:
                total["held_seconds"] += seconds
                book["held_seconds"] += seconds

        def margin(prices):
            return (P.value_at(book, prices),
                    sum(pp["maint"][s]*abs(q)*prices[s] for s,q in book["qty"].items()))

        def note_drawdown(eq):
            peak = book["peak"]
            book["largest_drop"] = min(book["largest_drop"],max(0,eq)/peak-1 if peak else 0)

        def protective(s, tick, hit, phase):
            price, kind, gap = hit
            trade = P.trade(book,s,-book["qty"][s],price,pp)
            event = dict(utc=stamp(tick),symbol=s,kind=kind,level=book["exits"].pop(s)[kind],
                         filled_at=price,gap=gap,price=trade["price"],side=trade["side"],qty=trade["qty"],phase=phase)
            book["target"].pop(s,None)
            book["exits_hit"].append(event)
            total["exits"].append(event)
            if s in self.active:
                self.remove(s,"cancelled",tick,reason="protective_exit")

        for tick, bars in groupby(rows, key=lambda row: row[0]):
            if tick < start or tick + MINUTE > end:
                continue
            hold(tick-at)
            bars = list(bars)
            opens = {r[1]: r[2] for r in bars}
            fund_until(tick, opens)
            book["last_px"].update(opens)
            protected = set()
            if book["qty"] and book["qty"].keys() <= opens.keys():
                eq, need = margin(opens)
                pending = book.pop("desk_liquidation",None)
                if pending or eq < need:
                    symbol = pending["symbol"] if pending else min(book["qty"])
                    trades = [P.trade(book,s,-q,opens[s],pp,penalty=pp["penalty"])
                              for s,q in sorted(book["qty"].items())]
                    short = max(0.0, -book["cash"])
                    book["shortfall_usd"] += short
                    book["cash"] = max(0.0, book["cash"])
                    event = dict(utc=stamp(tick),symbol=symbol,value_before=eq,value_after=book["cash"],
                                 shortfall_usd=short,at_open=True,trigger=pending,trades=trades)
                    book["closeouts"].append(event)
                    total["closeout"] = event
                    note_drawdown(book["cash"])
                    block(tick)
            for s, q in sorted(book["qty"].items()):
                if s not in opens or s not in book["exits"] or book.get("desk_liquidation"):
                    continue
                p = opens[s]
                hit = P.exit_hit(q, book["exits"][s], p, p, p)
                if hit:
                    protective(s,tick,hit,"open")
                    protected.add(s)
            prior_exits = dict(book["exits"])
            immediate_symbols = set()
            if on_open and not blocked and not book.get("desk_liquidation"):
                immediate_symbols = on_open(tick, opens, protected) or set()
                for s in sorted(immediate_symbols):
                    live = self.active.get(s)
                    if live and "observed" in live:
                        self.remove(s, "cancelled", tick, reason="immediate_fill")
            if not blocked and not book.get("desk_liquidation"):
                self.execute_open(book, pp, tick, opens, gross)
            at = tick + MINUTE
            hold(MINUTE)
            # A resting exit can fill at its level intraminute. Record the
            # observation at close, not as a second execution at the open.
            for _,s,o,h,l,_ in bars:
                ex = book["exits"].get(s)
                if (book.get("desk_liquidation") or not book["qty"].get(s) or not ex
                        or s in immediate_symbols or ex != prior_exits.get(s)):
                    continue
                hit = P.exit_hit(book["qty"][s],ex,o,h,l)
                if hit and not hit[2]:
                    protective(s,at,hit,"intrabar")
                    protected.add(s)
            if book["qty"] and book["qty"].keys() <= opens.keys():
                for _,s,_,h,l,_ in bars:
                    q = book["qty"].get(s)
                    if not q:
                        continue
                    adverse = dict(opens)
                    adverse[s] = l if q > 0 else h
                    eq,need = margin(adverse)
                    note_drawdown(eq)
                    if eq < need and not book.get("desk_liquidation"):
                        # The extreme is known only when the bar completes.
                        # It can never be a liquidation price for another coin.
                        book["desk_liquidation"] = dict(symbol=s,observed=stamp(at),bar_start=stamp(tick))
            book["last_px"].update({s:c for _,s,_,_,_,c in bars})
            if book["qty"]:
                book["peak"] = max(book["peak"],P.value_at(book,book["last_px"]))
            for bar in bars:
                self.observe_close(bar, protected)
            self.expire(at)
        hold(end-at)
        fund_until(end, {})
        self.expire(end)
        return total


def step(book, bundle, row, pp, minutes, at, end, last, active, gross, first=False, delay=0):
    """One shared transition for submission and replay; no broker side effects."""
    orders = Orders(active, delay)
    orders.submit(bundle, book, at)
    weights, exits = bundle.get("weights"), bundle.get("exits")
    effective = P.norm(book["target"] if weights is None else weights)
    needs_open = bool(book["qty"] or effective)
    changed = needs_open and (first or book.get("pending") or effective != P.norm(book["target"]))
    update_exits = bool(book["qty"] and weights is not None and (exits or {}) != book["exits"])
    book["last_px"].update(row["marks"])
    record = None

    def immediate(tick, opens, protected):
        nonlocal record
        if record is not None:
            return
        touched = set(book["qty"]) | set(P.norm(weights if weights is not None else book["target"]))
        if (changed or update_exits) and not touched <= opens.keys():
            return
        planned = deepcopy(book)
        record = P.p_step(planned, weights, exits, dict(marks=dict(book["last_px"]),
                          fills={s:[stamp(tick), opens[s]] for s in touched if changed}), pp, first and needs_open)
        target, old_exits = dict(planned["target"]), book["exits"]
        slots = [(tr["symbol"], tr["qty"]*(1 if tr["side"] == "buy" else -1)) for tr in record["trades"]]
        record["trades"] = []
        book["pending"] = planned["pending"]
        for s, dq in sorted(slots, key=lambda item:(not reducing(book,*item), item[0])):
            tr, reason = (None, "protective_exit") if s in protected else guarded_trade(book,s,dq,opens,pp,gross)
            if reason:
                record["skipped"].append(dict(symbol=s,why=reason))
                if s in book["target"]:
                    target[s] = book["target"][s]
                else:
                    target.pop(s,None)
                if s in old_exits:
                    planned["exits"][s] = old_exits[s]
                else:
                    planned["exits"].pop(s,None)
            else:
                record["trades"].append(dict(tr,fill_utc=stamp(tick)))
        book.update(target=target, exits={s:e for s,e in planned["exits"].items() if s in target})
        record.update(target=dict(target), exits=dict(book["exits"]), value_after=P.value_at(book,opens),
                      weights_after=P.weights_at(book,opens), fill_utc=stamp(tick) if record["trades"] else None)
        return {tr["symbol"] for tr in record["trades"]}

    if not (changed or update_exits):
        immediate(at, {}, set())
    symbols = set(pp["symbols"]) if changed else set(book["qty"])
    active_rows = P.scan_rows(minutes, at, end, symbols, watched=orders.active)
    scan = orders.advance(book, pp, active_rows, at, end, gross, on_open=immediate, last=last)
    if record is None:
        record = dict(target=dict(book["target"]), trades=[],
                      skipped=[{"why":"maintenance" if scan["closeout"] else "no_common_open"}], changed=False)
    record["scan"] = scan
    if last:
        orders.expire(end)
    return record, orders.active, orders.events
