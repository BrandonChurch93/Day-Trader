"""TM07 simulated order rules. No broker, model, tape fetch or clock calls."""
from copy import deepcopy
from itertools import groupby
import math

from timemachine import perp as P

MINUTE = 60


def number(value):
    return type(value) in (int, float) and abs(value) <= 1e100 and math.isfinite(value)


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
        ready = []
        for sym, order in sorted(self.active.items()):
            if sym in opens and "observed" in order and order["observed"] + self.delay <= at:
                px = opens[sym]
                gap_exit = book["qty"].get(sym) and P.exit_hit(book["qty"][sym], book["exits"].get(sym, {}), px, px, px)
                if gap_exit:
                    self.remove(sym, "cancelled", at, reason="protective_exit")
                    continue
                marks = {sym: px}
                held = P.weights_at(book, marks).get(sym, 0.0)
                ready.append((not (held * order["weight"] >= 0 and abs(order["weight"]) < abs(held)), sym))
        for _, sym in sorted(ready):
            order = self.active[sym]
            mark = opens[sym]
            weights = P.weights_at(book, {sym: mark})
            current = weights.get(sym, 0)
            other = sum(abs(v) for s, v in weights.items() if s != sym)
            value = P.value_at(book, {sym: mark})
            w = order["weight"]
            quantity = book["qty"].get(sym, 0)
            dq = w * value / mark - quantity
            target_gross = other + abs(w)
            exec_price = mark * (1 + pp["hs"][sym] if dq > 0 else 1 - pp["hs"][sym])
            costs = abs(dq) * (abs(mark - exec_price) + exec_price * pp["fee"][sym])
            reason = None
            if value <= 0 or value - costs <= 0:
                reason = "zero_equity"
            elif target_gross * value > gross * (value - costs) + 1e-8 and target_gross >= other + abs(current):
                reason = "gross_limit"
            elif abs(dq) * mark < 1e-9 or (abs(w - current) < pp["min_change"] and w != 0 and quantity*w >= 0):
                reason = "small_change"
            if reason:
                self.remove(sym, "refused", at, reason=reason, open=mark, gross_wanted=target_gross)
                continue
            trade = P.trade(book, sym, dq, mark, pp)
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

    def advance(self, book, pp, rows, start, end, gross, on_open=None):
        """At each minute: use opens, then reuse TM06 exits/maintenance, then read highs/lows."""
        at = start
        total = dict(exits=[], closeout=None, funding_usd=0.0, fallback_hours=0, held_seconds=0)

        def scan(bars, begin, stop):
            got = P.p_scan(book, bars, P.dt.datetime.fromtimestamp(begin, P.UTC), P.dt.datetime.fromtimestamp(stop, P.UTC), pp)
            total["exits"].extend(got["exits"])
            total["closeout"] = got["closeout"] or total["closeout"]
            for field in ("funding_usd", "fallback_hours", "held_seconds"):
                total[field] += got[field]
            return got

        for tick, bars in groupby(rows, key=lambda row: row[0]):
            if tick < start or tick + MINUTE > end:
                continue
            if tick > at:
                scan([], at, tick)
            bars = list(bars)
            opens = {r[1]: r[2] for r in bars}
            if on_open:
                on_open(tick, opens)
            self.execute_open(book, pp, tick, opens, gross)
            at = tick + MINUTE
            exits = scan(bars, tick, at)
            protected = {x["symbol"] for x in exits["exits"]}
            if exits["closeout"]:
                for s in sorted(self.active):
                    self.remove(s, "cancelled", at, reason="maintenance")
            for bar in bars:
                self.observe_close(bar, protected)
            self.expire(at)
        if at < end:
            scan([], at, end)
        self.expire(end)
        return total


def step(book, bundle, row, pp, minutes, at, end, last, active, gross, first=False, delay=0):
    """One shared transition for submission and replay; no broker side effects."""
    orders = Orders(active, delay)
    orders.submit(bundle, book, at)
    weights, exits = bundle.get("weights"), bundle.get("exits")
    changed = first or book.get("pending") or (weights is not None and P.norm(weights) != P.norm(book["target"]))
    book["last_px"].update(row["marks"])
    record = None

    def immediate(tick, opens):
        nonlocal record
        if record is not None:
            return
        touched = set(book["qty"]) | set(weights if weights is not None else book["target"])
        if changed and not touched <= opens.keys():
            return
        stamp = P.iso(P.dt.datetime.fromtimestamp(tick, P.UTC))
        record = P.p_step(book, weights, exits, dict(marks=dict(book["last_px"]),
                          fills={s:[stamp, opens[s]] for s in touched if changed}), pp, first)
        record["target"] = dict(record["target"])

    if not changed:
        immediate(at, {})
    symbols = set(pp["symbols"]) if changed else set(book["qty"])
    active_rows = P.scan_rows(minutes, at, end, symbols, watched=orders.active)
    if not orders.active:
        def dt(t):
            return P.dt.datetime.fromtimestamp(t, P.UTC)
        touched = set(book["qty"]) | set(weights if weights is not None else book["target"])
        match = next(((tick, opens) for tick, bars in groupby(active_rows, key=lambda r:r[0])
                      if touched <= (opens := {r[1]:r[2] for r in bars}).keys()), None) if changed and touched else (at, {})
        start, opens = match if match is not None else (end, {})
        bridge = P.p_scan(book, minutes, dt(at), dt(start), pp) if start > at else None
        if match is not None:
            immediate(start, opens)
        scan = P.p_scan(book, minutes, dt(start), dt(end), pp) if start < end else bridge
        if bridge and bridge is not scan:
            scan["exits"] = bridge["exits"]+scan["exits"]
            scan["closeout"] = scan["closeout"] or bridge["closeout"]
            for field in ("held_seconds", "funding_usd", "fallback_hours"):
                scan[field] += bridge[field]
    else:
        scan = orders.advance(book, pp, active_rows, at, end, gross, on_open=immediate)
    if record is None:
        record = dict(target=dict(book["target"]), trades=[], skipped=[{"why":"no_common_open"}], changed=False)
    record["scan"] = scan
    if last:
        orders.expire(end)
    return record, orders.active, orders.events
