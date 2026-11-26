"""TM07 simulated order rules. No broker, model, tape fetch or clock calls."""
from copy import deepcopy
from itertools import groupby
from bisect import bisect_right
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


def priced_target(weights, gross):
    target = P.norm(weights)
    total = math.fsum(abs(w) for w in target.values())
    return {s:w*(gross/total) for s,w in target.items()} if total > gross else target


def cap_deltas(book,desired,opens,pp,gross):
    """Find one feasible scale for every requested position, net of delta costs."""
    current = book["qty"]
    value = math.fsum([book["cash"],*(q*opens[s] for s,q in current.items())])
    other = math.fsum(abs(q)*opens[s] for s,q in current.items() if s not in desired)
    planned = math.fsum(abs(q)*opens[s] for s,q in desired.items())

    def deltas(scale):
        return {s:scale*q-current.get(s,0) for s,q in desired.items()}

    def fits(scale):
        costs = []
        for s,dq in deltas(scale).items():
            spread = pp["hs"][s]
            fee = pp["fee"][s]*(1+spread*(1 if dq > 0 else -1))
            costs.append(abs(dq)*opens[s]*(spread+fee))
        budget = gross*(value-math.fsum(costs))
        return other+scale*planned <= budget-8*math.ulp(max(1,abs(budget)))

    if fits(1):
        return deltas(1)
    if not fits(0):
        return None
    lo,hi = 0.,1.
    for _ in range(44):
        scale = (lo+hi)/2
        if fits(scale):
            lo = scale
        else:
            hi = scale
    return deltas(lo)


def apply_basket(book, target, opens, pp, gross):
    """Fit and commit all eligible target legs at one common open, or none."""
    value = math.fsum([book["cash"],*(q*opens[s] for s,q in book["qty"].items())])
    if value <= 0:
        return [],"zero_equity"
    desired = {s:w*value/opens[s] for s,w in target.items()}
    fitted = cap_deltas(book,desired,opens,pp,gross)
    if fitted is None:
        return [],"gross_limit"
    slots = [(s,dq) for s,dq in fitted.items() if abs(dq)*opens[s] >= 1e-9]
    if not any(abs(dq)*opens[s] >= pp["min_change"]*value or not target[s]
               or book["qty"].get(s,0)*target[s] < 0 for s,dq in slots):
        return [],"small_change"

    def priority(item):
        s,dq = item
        q,p = book["qty"].get(s,0),opens[s]
        return ((abs(q+dq)-abs(q))*p, dq*p, p, pp["hs"][s], pp["fee"][s], pp["maint"][s])

    applied = deepcopy(book)
    trades = []
    for s,dq in sorted(slots,key=priority):
        trade,reason = guarded_trade(applied,s,dq,opens,pp,gross)
        if reason:
            return [],reason
        trades.append(trade)
    book.update(applied)
    return trades,None


def stamp(tick):
    return P.iso(P.dt.datetime.fromtimestamp(tick, P.UTC))


def funding_schedule(pp,start,end):
    """An observed rate settles at its own stamp; never credit fallback."""
    events = []
    for s in pp["symbols"]:
        rates = pp["funding"].get(s,{})
        stamps = sorted(rates)
        events.extend((t,s,rates[t],0) for t in stamps[bisect_right(stamps,start-1):bisect_right(stamps,end)])
        hours = pp["hours"][s]
        interval = hours*3600
        for t in range(((start+interval-1)//interval)*interval,end+1,interval):
            if bisect_right(stamps,t) == bisect_right(stamps,t-interval):
                events.append((t,s,None,hours))
    return sorted(events)


def protective_hit(q, ex, o, h, l):
    """Evaluate only a completed bar, giving the stop priority on ambiguity."""
    for kind in ("stop","target"):
        level = ex.get(kind)
        if level is None:
            continue
        down = (q > 0) == (kind == "stop")
        crossed = l <= level if down else h >= level
        if crossed:
            gap = (o <= level) if down else (o >= level)
            return o if gap else level,kind,gap
    return None


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

    def __init__(self, active=None, delay=0, pending=None):
        self.active = deepcopy(active or {})
        self.pending = deepcopy(pending or {})
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
        for sym,change in sorted(self.pending.items()):
            order = change["order"]
            if order and at >= order["expiry"]:
                self.event("expired",order,at,reason="before_activation")
                self.pending.pop(sym)

    def submit(self, bundle, book, at):
        self.expire(at)
        keeps = set(bundle.get("keep", ()))
        new = bundle.get("conditions", {})
        for sym in set(self.active)|set(self.pending)|set(new):
            queued = self.pending.get(sym,{}).get("order")
            live = self.active.get(sym)
            if sym in new:
                self.pending[sym] = dict(after=at,order=deepcopy(new[sym]))
            elif queued and queued["id"] in keeps:
                continue
            elif live and live["id"] not in keeps:
                self.pending[sym] = dict(after=at,order=None)
            else:
                self.pending.pop(sym,None)

    def activate(self, at, opens):
        self.expire(at)
        for sym,change in sorted(self.pending.items()):
            if at <= change["after"] or sym not in opens:
                continue
            order = self.pending.pop(sym)["order"]
            if sym in self.active:
                self.remove(sym,"cancelled",at,reason="replaced" if order else "not_kept")
            if order:
                self.active[sym] = order
                self.event("armed",order,at)

    def execute_open(self, book, pp, at, opens, gross):
        self.expire(at)
        ready = sorted((order["observed"],s) for s,order in self.active.items()
                       if "observed" in order and order["observed"] + self.delay <= at)
        for _,group in groupby(ready,key=lambda item:item[0]):
            weights = {s:self.active[s]["weight"] for _,s in group}
            if not (book["qty"].keys() | weights.keys()) <= opens.keys():
                continue
            previous = P.weights_at(book, opens)
            before = dict(book["qty"])
            other_saved = math.fsum(abs(w) for s,w in book["target"].items() if s not in weights)
            saved_gross = other_saved+math.fsum(abs(w) for w in weights.values())
            target_gross = math.fsum(abs(w) for s,w in previous.items() if s not in weights)+math.fsum(map(abs,weights.values()))
            if len(weights) == 1 and saved_gross > gross+1e-10:
                trades,reason = [],"target_gross_limit"
            else:
                trades,reason = apply_basket(book,weights,opens,pp,gross)
            if reason:
                for s in weights:
                    self.remove(s,"refused",at,reason=reason,open=opens[s],
                                gross_wanted=target_gross,saved_target_gross=saved_gross)
                continue
            traded = {tr["symbol"]:tr for tr in trades}
            saved = priced_target(weights,max(0,gross-other_saved))
            for s,w in weights.items():
                mark = opens[s]
                book["last_px"][s] = mark
                if s in saved and saved[s]:
                    book["target"][s] = saved[s]
                else:
                    book["target"].pop(s,None)
                if before.get(s,0)*w <= 0:
                    book["exits"].pop(s,None)
                if s not in traded:
                    self.remove(s,"refused",at,reason="small_change",open=mark,
                                gross_wanted=target_gross,saved_target_gross=saved_gross)
                else:
                    trade = traded[s]
                    self.remove(s,"filled",at,open=mark,previous_weight=previous.get(s,0),gross_wanted=target_gross,
                                spread_usd=trade["qty"]*mark*pp["hs"][s],trade=trade)

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

    def advance(self, book, pp, rows, start, end, gross, on_open=None, last=False, end_marks=None):
        """Apply the same pessimistic one-bar maintenance proxy to every arm."""
        total = dict(exits=[], closeout=None, funding_usd=0.0, fallback_hours=0, held_seconds=0,settlements=[])
        book.setdefault("held_seconds",0)
        events = iter(funding_schedule(pp,start,end if last else end-1))
        upcoming = next(events, None)
        blocked = False

        def fund_until(tick, opens, marks, bar_start):
            nonlocal upcoming
            forced = None
            while upcoming and upcoming[0] <= tick:
                t,s,rate,fallback = upcoming
                q = book["qty"].get(s)
                if q:
                    price = opens.get(s,book["last_px"][s]) if t == tick else book["last_px"][s]
                    if fallback:
                        cost = abs(q)*price*pp["fallback_per_day"]*fallback/24
                        book["fallback_hours"] += fallback
                        total["fallback_hours"] += fallback
                    else:
                        cost = q*price*rate
                    book["cash"] -= cost
                    book["funding_usd"] += cost
                    total["funding_usd"] += cost
                    total["settlements"].append(dict(utc=stamp(t),symbol=s,qty=q,mark=price,rate=rate,cost=cost))
                    if cost > 0 and check(t,marks(),"funding_debit",bar_start):
                        forced = t
                upcoming = next(events, None)
            return forced

        def block(tick):
            nonlocal blocked
            for s in sorted(self.active):
                self.remove(s, "cancelled", tick, reason="maintenance")
            for s,change in sorted(self.pending.items()):
                if change["order"]:
                    self.event("cancelled",change["order"],tick,reason="maintenance")
            self.pending.clear()
            book.update(target={}, exits={}, pending=False)
            blocked = True

        def margin(prices):
            return (P.value_at(book, prices),
                    sum(pp["maint"][s]*abs(q)*prices[s] for s,q in book["qty"].items()))

        def note_drawdown(eq):
            peak = book["peak"]
            book["largest_drop"] = min(book["largest_drop"],max(0,eq)/peak-1 if peak else 0)

        def check(tick, prices, phase, bar_start):
            if not book["qty"]:
                return False
            eq,need = margin(prices)
            note_drawdown(eq)
            if eq >= need:
                return False
            trades = [P.trade(book,s,-q,prices[s],pp,penalty=pp["penalty"])
                      for s,q in sorted(book["qty"].items())]
            short = max(0.0, -book["cash"])
            book["shortfall_usd"] += short
            book["cash"] = max(0.0, book["cash"])
            event = dict(utc=stamp(tick),bar_start=stamp(bar_start) if bar_start is not None else None,phase=phase,
                         symbol=min(prices),value_before=eq,value_after=book["cash"],shortfall_usd=short,trades=trades)
            book["closeouts"].append(event)
            total["closeout"] = event
            note_drawdown(book["cash"])
            block(tick)
            return True

        def protective(s, tick, hit, phase, active_exit):
            price, kind, gap = hit
            trade = P.trade(book,s,-book["qty"][s],price,pp)
            book["exits"].pop(s,None)
            event = dict(utc=stamp(tick),symbol=s,kind=kind,level=active_exit[kind],
                         filled_at=price,gap=gap,price=trade["price"],side=trade["side"],qty=trade["qty"],phase=phase)
            book["target"].pop(s,None)
            book["exits_hit"].append(event)
            total["exits"].append(event)
            if s in self.active:
                self.remove(s,"cancelled",tick,reason="protective_exit")

        groups = iter((t,list(bars)) for t,bars in groupby(rows,key=lambda r:r[0]))
        group = next(groups,None)
        for tick in range(start,end,MINUTE):
            while group and group[0] < tick:
                group = next(groups,None)
            bars = group[1] if group and group[0] == tick else []
            opens = {r[1]: r[2] for r in bars}
            prior_close = dict(book["last_px"])
            extremes = {s:(l,h) for _,s,_,h,l,_ in bars}

            def adverse():
                return {s:extremes[s][q < 0] if s in extremes else prior_close[s] for s,q in book["qty"].items()}

            fund_until(tick, opens, adverse, tick)
            book["last_px"].update(opens)
            at = min(tick+MINUTE,end)
            protected = set()
            # A deliberately noncausal check on positions carried into the open.
            check(tick,adverse(),"pre_open_proxy",tick)
            if not blocked and bars:
                self.activate(tick,opens)
            bar_by_symbol = {r[1]:r for r in bars}
            for s, q in sorted(book["qty"].items()):
                if s not in opens or s not in book["exits"]:
                    continue
                _,_,o,h,l,_ = bar_by_symbol[s]
                hit = protective_hit(q,book["exits"][s],o,h,l)
                if hit and hit[2]:
                    protective(s,tick,hit,"open",book["exits"][s])
                    protected.add(s)
            prior_exits = dict(book["exits"])
            prior_qty = dict(book["qty"])
            immediate_symbols = set()
            if on_open and not blocked and bars:
                immediate_symbols = on_open(tick, opens, protected) or set()
                for s in sorted(immediate_symbols):
                    live = self.active.get(s)
                    if live and "observed" in live:
                        self.remove(s, "cancelled", tick, reason="immediate_fill")
            if not blocked and bars:
                self.execute_open(book, pp, tick, opens, gross)
            held = bool(book["qty"])
            forced = fund_until(at-1,{},adverse,tick)
            if held:
                seconds = (at if forced is None else forced)-tick
                total["held_seconds"] += seconds
                book["held_seconds"] += seconds
            # This includes exposure first opened in this minute.
            check(at,adverse(),"post_open_proxy",tick)
            # OHLC gives no touch timestamp. Account for the resting exit at
            # the bar close, after all mid-minute funding and before the next open.
            for _,s,o,h,l,_ in bars:
                ex = prior_exits.get(s)
                q = book["qty"].get(s,0)
                if not ex or q*prior_qty.get(s,0) <= 0:
                    continue
                hit = protective_hit(q,ex,o,h,l)
                if hit and not hit[2]:
                    protective(s,at,hit,"bar_close_proxy",ex)
                    protected.add(s)
            book["last_px"].update({s:c for _,s,_,_,_,c in bars})
            if book["qty"]:
                book["peak"] = max(book["peak"],P.value_at(book,book["last_px"]))
            for bar in bars:
                self.observe_close(bar, protected)
            self.expire(at)
        if last:
            book["last_px"].update(end_marks or {})
            def closing_marks():
                return {s:book["last_px"][s] for s in book["qty"]}
            fund_until(end,{},closing_marks,None)
            check(end,closing_marks(),"session_end",None)
        self.expire(end)
        return total


def step(book, bundle, row, pp, minutes, at, end, last, active, gross, first=False, delay=0, end_marks=None):
    """One shared transition for submission and replay; no broker side effects."""
    orders = Orders(active,delay,book.pop("desk_order_updates",None))
    orders.submit(bundle, book, at)
    weights, exits = bundle.get("weights"), bundle.get("exits")
    effective = priced_target(book["target"] if weights is None else weights,gross)
    needs_open = bool(book["qty"] or effective)
    changed = needs_open and (first or book.get("pending") or effective != P.norm(book["target"]))
    update_exits = bool(book["qty"] and weights is not None and (exits or {}) != book["exits"])
    book["last_px"].update(row["marks"])
    record = None

    def immediate(tick, opens, protected):
        nonlocal record
        if record is not None:
            return
        touched = set(book["qty"]) | effective.keys()
        if (changed or update_exits) and not touched <= opens.keys():
            return
        value = P.value_at(book,opens)
        record = dict(target=dict(book["target"]),exits=dict(book["exits"]),changed=changed,retry=book["pending"],
                      value_before=value,value_after=value,weights_after=P.weights_at(book,opens),
                      trades=[],skipped=[],fill_utc=None)
        target = {s:w for s,w in effective.items() if s not in protected}
        if changed and touched:
            trades,reason = apply_basket(book,{s:target.get(s,0) for s in touched-protected},opens,pp,gross)
            if reason and reason != "small_change":
                record["skipped"].append(dict(why=reason))
                return
            record["trades"] = [dict(tr,fill_utc=stamp(tick)) for tr in trades]
        new_exits = book["exits"] if weights is None else exits or {}
        book.update(target=target, exits={s:e for s,e in new_exits.items() if s in target}, pending=False)
        record.update(target=dict(target), exits=dict(book["exits"]), value_after=P.value_at(book,opens),
                      weights_after=P.weights_at(book,opens), fill_utc=stamp(tick) if record["trades"] else None)
        return {tr["symbol"] for tr in record["trades"]}

    if not (changed or update_exits):
        immediate(at, {}, set())
    symbols = set(pp["symbols"]) if changed else set(book["qty"])
    active_rows = P.scan_rows(minutes,at,end,symbols,watched=orders.active.keys()|orders.pending.keys())
    scan = orders.advance(book, pp, active_rows, at, end, gross, on_open=immediate, last=last,end_marks=end_marks)
    if record is None:
        record = dict(target=dict(book["target"]), trades=[],
                      skipped=[{"why":"maintenance" if scan["closeout"] else "no_common_open"}], changed=False)
    record["scan"] = scan
    if last:
        orders.expire(end)
        orders.pending.clear()
    if orders.pending:
        book["desk_order_updates"] = orders.pending
    return record, orders.active, orders.events
