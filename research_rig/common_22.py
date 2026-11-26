"""Plan 22 engine: rule A (fresh range break on volume), rule C switch,
equal-weight hold, random twins and the judged marks. Pure: no file or
network I/O. Time is counted in whole UTC hours since 1970 (epoch hours).
A bar stamped h covers [h, h+1); its close is known at h+1."""
from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timezone
import math
import random

import numpy as np

DAY = 24
FIELDS = {
    "judged_start": str, "judged_end": str, "shown_start": str, "shown_end": str,
    "wake_hour_utc": int, "range_days": int, "volume_days": int, "volume_window_hours": int,
    "min_volume_ratio": float, "max_above_level_pct": float, "max_names": int, "min_parts": int,
    "stall_days": int, "stall_volume_ratio": float, "top_rank": int, "max_page_age_days": int,
    "judged_cost_bps": int, "shown_cost_bps": list, "min_sharpe": float, "max_drawdown": float,
    "twins": int, "twin_percentile": float, "twin_seed": int, "twin_max_draws": int,
    "min_positive_years": int, "annual_days": int, "drop_best": int, "btc_line_days": int,
    "calibration_seed": int, "calibration_seeds": int, "calibration_edges_pct": list,
    "calibration_coins": int, "calibration_days": int, "calibration_sigma_hourly": float,
    "calibration_hl_spread": float, "calibration_drift_hours": int,
    "calibration_volume_boost": list, "calibration_fade_days": int,
}


def hour_of(day):
    d = datetime.fromisoformat(day)
    if d.tzinfo is not None or (d.hour, d.minute, d.second, d.microsecond) != (0, 0, 0, 0):
        raise ValueError("plan 22 bounds must be plain UTC dates")
    return int(d.replace(tzinfo=timezone.utc).timestamp()) // 3600


def policy(raw):
    """Validate the replay_22_plan value (a dict) and add hour bounds."""
    p = dict(raw)
    if set(p) != set(FIELDS):
        raise ValueError(f"plan 22 fields differ: {sorted(set(p) ^ set(FIELDS))}")
    for k, kind in FIELDS.items():
        v = p[k]
        if kind is float and type(v) is int:
            v = p[k] = float(v)
        if type(v) is not kind:
            raise ValueError(f"plan 22 field {k} has the wrong type")
    for k in ("judged_start", "judged_end", "shown_start", "shown_end"):
        p[k + "_h"] = hour_of(p[k])
    costs = (*p["shown_cost_bps"], p["judged_cost_bps"])
    if (not p["judged_start_h"] < p["judged_end_h"] <= p["shown_start_h"] < p["shown_end_h"]
            or not 0 <= p["wake_hour_utc"] < 24 or p["min_parts"] < 1 or p["max_names"] < 1
            or len(set(costs)) != len(costs) or not all(type(c) is int and 0 <= c < 10_000 for c in costs)
            or not 0 < p["max_drawdown"] < 1 or not 0 < p["twin_percentile"] < 100
            or p["volume_window_hours"] != DAY or p["twins"] < 1 or p["drop_best"] < 0):
        raise ValueError("inconsistent plan 22 policy")
    return p


def day_start(h):
    return h - h % DAY


def wakes(start, end, p):
    first = day_start(start) + p["wake_hour_utc"]
    if first < start:
        first += DAY
    return list(range(first, end, DAY))


def marks(start, end):
    """Daily marks at 00:00 UTC from start through end, both included."""
    if start % DAY or end % DAY:
        raise ValueError("marks need whole UTC days")
    return list(range(start, end + 1, DAY))


class Tape:
    """Hourly bars of one pair. Missing hours are NaN. qv is quote (USDT) volume."""

    def __init__(self, start, o, h, l, c, qv):
        self.start = int(start)
        self.o, self.h, self.l, self.c, self.qv = (np.asarray(x, dtype=float) for x in (o, h, l, c, qv))
        n = len(self.c)
        if not all(len(x) == n for x in (self.o, self.h, self.l, self.qv)):
            raise ValueError("tape columns differ in length")
        self.end = self.start + n
        self.present = ~np.isnan(self.c)
        self.traded_mask = self.present & (np.nan_to_num(self.qv) > 0)
        self.n_present = np.concatenate(([0], np.cumsum(self.present)))
        self.cum_qv = np.concatenate(([0.], np.cumsum(np.where(self.present, np.nan_to_num(self.qv), 0.))))
        self.traded_hours = np.flatnonzero(self.traded_mask) + self.start

    def _i(self, h):
        return h - self.start

    def has(self, h):
        return self.start <= h < self.end and bool(self.present[h - self.start])

    def traded(self, h):
        return self.start <= h < self.end and bool(self.traded_mask[h - self.start])

    def complete(self, a, b):
        """Every hour in [a, b) has a bar."""
        if a < self.start or b > self.end or a >= b:
            return False
        return self.n_present[b - self.start] - self.n_present[a - self.start] == b - a

    def qsum(self, a, b):
        return float(self.cum_qv[b - self.start] - self.cum_qv[a - self.start])

    def high(self, a, b):
        """Highest high in [a, b) over the bars present; None if none."""
        a, b = max(a, self.start), min(b, self.end)
        if a >= b:
            return None
        x = self.h[a - self.start:b - self.start]
        return None if np.all(np.isnan(x)) else float(np.nanmax(x))

    def low(self, a, b):
        a, b = max(a, self.start), min(b, self.end)
        if a >= b:
            return None
        x = self.l[a - self.start:b - self.start]
        return None if np.all(np.isnan(x)) else float(np.nanmin(x))

    def close(self, h):
        return float(self.c[h - self.start])

    def open(self, h):
        return float(self.o[h - self.start])

    def last_close(self, h, floor):
        """Close of the latest bar present at or before hour h, not before floor."""
        lo = max(floor, self.start)
        i = min(h, self.end - 1)
        while i >= lo:
            if self.present[i - self.start]:
                return float(self.c[i - self.start])
            i -= 1
        return None

    def next_traded(self, a, b):
        """First hour in [a, b) with a bar and volume above zero."""
        i = bisect_left(self.traded_hours, a)
        if i < len(self.traded_hours) and self.traded_hours[i] < b:
            return int(self.traded_hours[i])
        return None

    def last_traded(self, a, b):
        """Last hour in [a, b) with a bar and volume above zero."""
        i = bisect_left(self.traded_hours, b) - 1
        if i >= 0 and self.traded_hours[i] >= a:
            return int(self.traded_hours[i])
        return None


@dataclass(frozen=True, order=True)
class Asset:
    coin: int
    pair: str
    begin: int        # first usable hour of this identity segment
    end: int          # exclusive


@dataclass(frozen=True)
class Trade:
    asset: Asset
    entry: int        # wake hour of the buy
    exit: int | None  # wake hour of the sell decision, None if open at the window end
    reason: str
    level: float | None = None
    ratio: float | None = None


def volume_ratio(tp, asset, w, p):
    """Last 24 hours of quote volume over the mean 24-hour volume of the 30 days before."""
    a = w - (p["volume_days"] + 1) * DAY
    if a < asset.begin or not tp.complete(a, w):
        return None
    base = tp.qsum(a, w - DAY) / p["volume_days"]
    return tp.qsum(w - DAY, w) / base if base > 0 else None


def signal(tp, asset, w, p):
    """Rule A entry test at wake w using bars closed by w. Returns (level, ratio) or a reason."""
    d0 = day_start(w)
    lo = min(w - (p["volume_days"] + 1) * DAY, d0 - (p["range_days"] + 1) * DAY)
    if lo < asset.begin or not tp.complete(lo, w):
        return "incomplete"
    level = tp.high(d0 - p["range_days"] * DAY, d0)
    last, prev = tp.close(w - 1), tp.close(w - 1 - DAY)
    if not last > level:
        return "no_break"
    # Fresh: 24 hours earlier the close was not above this level, and at the
    # previous wake it was not above that wake's own 21-day level either.
    if prev > level or prev > tp.high(d0 - (p["range_days"] + 1) * DAY, d0 - DAY):
        return "not_fresh"
    if last > level * (1 + p["max_above_level_pct"] / 100):
        return "too_far_above"
    ratio = volume_ratio(tp, asset, w, p)
    if ratio is None:
        return "no_volume_base"
    if ratio < p["min_volume_ratio"]:
        return "low_volume"
    return level, ratio


def exit_reason(tp, held, w, listed, p, stall_needs_volume=True):
    """Rule A exit test at wake w for a holding (Trade-like dict). None means keep."""
    a = held["asset"]
    if listed.get(a.coin) != a:
        return "left_list"
    e = held["entry"]
    d0 = day_start(w)
    if d0 > e:
        close = tp.last_close(d0 - 1, max(e, a.begin))
        if close is not None and close < held["level"]:
            return "close_under_level"
    span = p["stall_days"] * DAY
    if w >= e + span:
        top = tp.high(e, e + span)
        if top is None or top <= held["prior_high"]:
            if not stall_needs_volume:
                return "stall"
            ratio = volume_ratio(tp, a, w, p)
            if ratio is not None and ratio < p["stall_volume_ratio"]:
                return "stall"
    return None


class BtcSwitch:
    """Rule C. Off when BTC's last hourly close is under the lowest low of the prior
    7 daily bars; back on at the first wake after a daily close above that same line."""

    def __init__(self, tp, asset, ws, p, counts=None):
        self.off_at = set()
        off, line, since = False, None, None
        n = p["btc_line_days"] * DAY
        for w in ws:
            d0 = day_start(w)
            if off:
                if d0 - 1 >= since and tp.has(d0 - 1) and tp.close(d0 - 1) > line:
                    off = False
                else:
                    if d0 - 1 >= since and not tp.has(d0 - 1) and counts is not None:
                        # no 23:00 close to test: nothing is imputed, the switch stays off
                        counts["btc_switch_recovery_unreadable"] = counts.get("btc_switch_recovery_unreadable", 0) + 1
                    self.off_at.add(w)
                    continue
            if d0 - n < asset.begin or not tp.complete(d0 - n, d0) or not tp.has(w - 1):
                if counts is not None:     # line or last close missing: nothing is imputed, the switch stays on
                    counts["btc_switch_unreadable"] = counts.get("btc_switch_unreadable", 0) + 1
                continue
            line_now = tp.low(d0 - n, d0)
            if tp.close(w - 1) < line_now:
                off, line, since = True, line_now, w
                self.off_at.add(w)

    def off(self, w):
        return w in self.off_at


def bump(counts, key, n=1):
    if counts is not None:
        counts[key] = counts.get(key, 0) + n


def rule_a(tapes, members, ws, p, switch=None, counts=None, stall_needs_volume=True):
    """Schedule of rule A trades. members(w) gives the tradable list at wake w."""
    held, trades = {}, []
    for w in ws:
        listed = {a.coin: a for a in members(w)}
        sold = set()
        for coin, s in list(held.items()):
            why = exit_reason(tapes[s["asset"].pair], s, w, listed, p, stall_needs_volume)
            if why is None and switch is not None and switch.off(w):
                why = "btc_switch"
            if why:
                trades.append(Trade(s["asset"], s["entry"], w, why, s["level"], s["ratio"]))
                del held[coin]
                sold.add(coin)
        if switch is not None and switch.off(w):
            bump(counts, "wakes_switched_off")
            continue
        slots = p["max_names"] - len(held)
        if slots <= 0:
            continue
        found = []
        for coin, a in sorted(listed.items()):
            if coin in held or coin in sold:
                continue
            tp = tapes[a.pair]
            got = signal(tp, a, w, p)
            if isinstance(got, str):
                bump(counts, "signal_" + got)
                continue
            found.append((-got[1], coin, a, got))
        found.sort(key=lambda x: (x[0], x[1]))
        bump(counts, "signals_over_slots", max(0, len(found) - slots))
        # Rank on signals first; a chosen coin with no 14:00 fill leaves its slot in cash (choice 9).
        for _, coin, a, (level, ratio) in found[:slots]:
            tp = tapes[a.pair]
            if not tp.traded(w) or w >= a.end:
                bump(counts, "signal_without_fill")
                continue
            held[coin] = {"asset": a, "entry": w, "level": level, "ratio": ratio,
                          "prior_high": tp.high(w - DAY, w)}
    for s in held.values():
        trades.append(Trade(s["asset"], s["entry"], None, "window_end", s["level"], s["ratio"]))
    return sorted(trades, key=lambda t: (t.entry, t.asset.coin))


def membership(tapes, members, ws, counts=None):
    """Hold every coin on the list: enter at the first wake with a fill, leave when it leaves."""
    held, trades = {}, []
    for w in ws:
        listed = {a.coin: a for a in members(w)}
        for coin, (a, e) in list(held.items()):
            if listed.get(coin) != a:
                trades.append(Trade(a, e, w, "left_list"))
                del held[coin]
        for coin, a in listed.items():
            if coin not in held:
                if tapes[a.pair].traded(w) and w < a.end:
                    held[coin] = (a, w)
                else:
                    bump(counts, "hold_wait_for_fill")
    for a, e in held.values():
        trades.append(Trade(a, e, None, "window_end"))
    return sorted(trades, key=lambda t: (t.entry, t.asset.coin))


@dataclass
class Result:
    marks: list       # mark hours
    equity: list      # equity at each mark; last value is after closing costs
    fills: list       # (trade, buy price, sell price or None, sell hour)
    gaps: dict


def book(trades, tapes, start, end, bps, min_parts, wake_hour):
    """Run the account from 1.0 cash at start to end. Fills at the wake bar's open.
    Equal parts of 1/max(min_parts, n) after any change in the set held. Every wake (wake_hour UTC) is an
    event: a delayed sale filled since the last wake counts as a change at the first wake at or after it."""
    fee = bps / 10_000
    by_entry, by_exit = {}, {}
    for i, t in enumerate(trades):
        by_entry.setdefault(t.entry, []).append(i)
        if t.exit is not None:
            by_exit.setdefault(t.exit, []).append(i)
    mk = marks(start, end)
    first = day_start(start) + wake_hour
    wake_set = set(range(first if first >= start else first + DAY, end, DAY))
    times = sorted(set(mk) | set(by_entry) | set(by_exit) | wake_set)
    dirty = False         # a delayed sale has filled since the last wake
    cash, units, cost = 1.0, {}, {}
    pending = []          # (hour, trade index)
    fills = {}
    gaps = {"held_hours_without_bar": 0, "sales_after_wake": 0, "closed_at_last_bar": 0,
            "stale_mark_values": 0, "buys_without_fill": 0}
    out = []

    def price_now(i, h):
        t = trades[i]
        tp = tapes[t.asset.pair]
        if tp.traded(h) and h < t.asset.end:
            return tp.open(h)
        v = tp.last_close(h - 1, t.asset.begin)
        return v if v is not None else cost[i]

    def value(h, at_open):
        total = cash
        for i, u in units.items():
            t = trades[i]
            tp = tapes[t.asset.pair]
            if at_open:
                px = price_now(i, h)
            else:
                px = tp.last_close(h - 1, t.asset.begin)
                if px is None:
                    px = cost[i]
                if not tp.has(h - 1):
                    gaps["stale_mark_values"] += 1
            total += u * px
        return total

    def sell(i, h, px):
        nonlocal cash
        cash += units[i] * px * (1 - fee)
        fills[i] = (fills[i][0], px, h)
        del units[i]

    def settle(h):
        """Sale decided at wake h: first traded bar at or after h inside the segment;
        if none is left, the last bar with volume."""
        nonlocal pending
        due = []
        for i in by_exit.get(h, []):
            if i not in units:
                continue
            t = trades[i]
            tp = tapes[t.asset.pair]
            stop = min(t.asset.end, end)
            x = tp.next_traded(h, stop)
            if x == h:
                sell(i, h, tp.open(h))
                due.append(i)
            elif x is not None:
                gaps["sales_after_wake"] += 1
                pending.append((x, i))
            else:
                y = tp.last_traded(t.asset.begin, stop)
                px = tp.close(y) if y is not None else cost[i]
                gaps["closed_at_last_bar"] += 1
                sell(i, h, px)
                due.append(i)
        return due

    pend_times = []
    k = 0
    while k < len(times) or pending:
        nxt = times[k] if k < len(times) else None
        if pending:
            pending.sort()
            if nxt is None or pending[0][0] < nxt:
                h, i = pending.pop(0)
                if i in units:
                    sell(i, h, tapes[trades[i].asset.pair].open(h))
                    dirty = True
                continue
        h = nxt
        k += 1
        if h > end:
            break
        if h in mk and h < end:
            out.append((h, value(h, False)))
        if h == end:
            break
        changed = False
        pending.sort()
        while pending and pending[0][0] == h:      # delayed sale due now: after the mark, before this wake
            _, i = pending.pop(0)
            if i in units:
                sell(i, h, tapes[trades[i].asset.pair].open(h))
                dirty = True                       # a change; the reset waits for the first wake at or after h
        if h in by_exit:
            changed = bool(settle(h)) or changed
        if h in wake_set:
            changed, dirty = changed or dirty, False
        new = []
        for i in by_entry.get(h, []):
            t = trades[i]
            tp = tapes[t.asset.pair]
            if tp.traded(h) and t.asset.begin <= h < t.asset.end:
                new.append(i)
            else:
                gaps["buys_without_fill"] += 1
        if new or changed:
            for i in new:
                units[i] = 0.0
                cost[i] = tapes[trades[i].asset.pair].open(h)
                fills[i] = (cost[i], None, None)
            live = [i for i in units if tapes[trades[i].asset.pair].traded(h)
                    and trades[i].asset.begin <= h < trades[i].asset.end]
            if not live:
                continue
            equity = value(h, True)
            parts = max(min_parts, len(units))
            target = equity / parts
            for _ in range(3):
                spend = sum(abs(target - units[i] * price_now(i, h)) for i in live) * fee
                frozen = sum(units[i] * price_now(i, h) for i in units if i not in live)
                room = equity - spend - frozen
                target = min((equity - spend) / parts, room / len(live) if live else 0.)
            vals = [units[i] * price_now(i, h) for i in live]
            if cash - sum((target - v) + abs(target - v) * fee for v in vals) < -1e-9:
                # The three-step estimate overspends (large moves since the last reset). Take the largest target
                # that is both at most (equity - fees) / parts and leaves cash at or above zero. Both conditions
                # rise monotonically in the target, so bisection keeps the last feasible point.
                def ok(t):
                    s = fee * sum(abs(t - v) for v in vals)
                    return parts * t + s <= equity and cash - sum(t - v for v in vals) - s >= 0.
                lo, hi = 0., equity / parts
                for _ in range(200):
                    mid = (lo + hi) / 2
                    lo, hi = (mid, hi) if ok(mid) else (lo, mid)
                target = lo
            for i in live:
                px = price_now(i, h)
                delta = target - units[i] * px
                cash -= delta + abs(delta) * fee
                units[i] = target / px
            for i in [i for i in new if i not in live]:
                del units[i]
            if cash < -1e-9 * max(1., equity):
                raise AssertionError("cash went below zero")
    final = value(end, False)
    final -= sum(u * (tapes[trades[i].asset.pair].last_close(end - 1, trades[i].asset.begin) or cost[i])
                 for i, u in units.items()) * fee
    for i in units:
        t = trades[i]
        fills[i] = (fills[i][0], tapes[t.asset.pair].last_close(end - 1, t.asset.begin), end)
    out.append((end, final))
    for i, (buy, sell, hs) in fills.items():
        t = trades[i]
        tp = tapes[t.asset.pair]
        a, b = max(t.entry, tp.start), min(hs if hs is not None else end, tp.end)
        if b > a:
            gaps["held_hours_without_bar"] += (b - a) - int(tp.n_present[b - tp.start] - tp.n_present[a - tp.start])
    return Result([h for h, _ in out], [v for _, v in out],
                  [(trades[i], *fills[i]) for i in sorted(fills)], gaps)


def summary(res, p):
    e = np.asarray(res.equity, dtype=float)
    r = e[1:] / e[:-1] - 1
    # Fewer than two returns, or all returns exactly equal: no variance, Sharpe 0, so the Sharpe mark fails.
    flat = len(r) < 2 or bool(np.all(r == r[0]))
    sd = 0. if flat else float(np.std(r, ddof=1))
    sharpe = float(np.mean(r)) / sd * math.sqrt(p["annual_days"]) if sd > 0 else 0.
    peak = np.maximum.accumulate(e)
    dd = float(np.max(1 - e / peak))
    at = dict(zip(res.marks, res.equity))
    by_year = {}
    y0 = datetime.fromtimestamp(res.marks[0] * 3600, timezone.utc).year
    y1 = datetime.fromtimestamp((res.marks[-1] - 1) * 3600, timezone.utc).year
    for y in range(y0, y1 + 1):
        lo = max(hour_of(f"{y}-01-01"), res.marks[0])
        hi = min(hour_of(f"{y + 1}-01-01"), res.marks[-1])
        by_year[y] = at[hi] / at[lo] - 1
    return {"final": float(e[-1]), "sharpe": sharpe, "max_drawdown": dd, "by_year": by_year,
            "positive_years": sum(v > 0 for v in by_year.values()), "years": len(by_year)}


def twin_schedule(real, members_at, ws, p, rng, counts=None, listed_at=None, next_out=None):
    """Same number of entries per month and the same holding lengths in wakes;
    random coin and wake from the list in force in that month."""
    idx = {w: i for i, w in enumerate(ws)}
    by_month = {}
    for w in ws:
        by_month.setdefault(datetime.fromtimestamp(w * 3600, timezone.utc).strftime("%Y-%m"), []).append(w)
    out = []
    occ = np.zeros(len(ws) + 1, dtype=np.int16)
    mine = {}
    for t in real:
        i = idx[t.entry]
        month = datetime.fromtimestamp(t.entry * 3600, timezone.utc).strftime("%Y-%m")
        pool = by_month[month]
        for _ in range(p["twin_max_draws"]):
            w = pool[rng.randrange(len(pool))]
            cands = members_at(w)
            if not cands:
                continue
            a = cands[rng.randrange(len(cands))]
            j = idx[w]
            k = (idx[t.exit] - i) if t.exit is not None else len(ws) - j
            stop = None
            if next_out is not None:
                q = next_out(a, j)
                stop = q if q < min(j + k, len(ws)) else None
            else:
                for q in range(j + 1, min(j + k, len(ws))):
                    if a not in (listed_at or members_at)(ws[q]):
                        stop = q
                        break
            hi = stop if stop is not None else min(j + k, len(ws))
            hi = max(hi, j + 1)
            busy = mine.setdefault(a.coin, np.zeros(len(ws) + 1, dtype=bool))
            if busy[j:hi].any() or occ[j:hi].max() >= p["max_names"]:
                continue
            busy[j:hi] = True
            occ[j:hi] += 1
            exit_w = ws[hi] if hi < len(ws) else None
            out.append(Trade(a, w, exit_w, "left_list" if stop is not None else "twin"))
            break
        else:
            bump(counts, "twin_entries_not_placed")
    return sorted(out, key=lambda t: (t.entry, t.asset.coin))


def fillable_members(tapes, members):
    cache = {}

    def at(w):
        if w not in cache:
            cache[w] = [a for a in members(w) if tapes[a.pair].traded(w) and a.begin <= w < a.end]
        return cache[w]
    return at


def twins(real, tapes, members, ws, start, end, bps, p, seed=None):
    rng = random.Random(p["twin_seed"] if seed is None else seed)
    at = fillable_members(tapes, members)
    cache = {}

    def listed(w):
        if w not in cache:
            cache[w] = set(members(w))
        return cache[w]
    outs = {}

    def next_out(a, j):
        # First wake index after j at which asset a is off the list (len(ws) if never).
        if a not in outs:
            f = np.full(len(ws) + 2, len(ws), dtype=np.int64)
            for q in range(len(ws) - 1, -1, -1):
                f[q] = f[q + 1] if a in listed(ws[q]) else q
            outs[a] = f
        return int(outs[a][j + 1])
    finals, counts = [], {}
    for _ in range(p["twins"]):
        sched = twin_schedule(real, at, ws, p, rng, counts, listed, next_out)
        finals.append(book(sched, tapes, start, end, bps, p["min_parts"], p["wake_hour_utc"]).equity[-1])
    return finals, counts


def trade_returns(res):
    return [(t, (sell / buy - 1) if sell is not None else None) for t, buy, sell, _ in res.fills]


def without_best(trades, res, n):
    ranked = sorted((r, i) for i, (_, r) in enumerate(trade_returns(res)) if r is not None)
    drop = {res.fills[i][0] for _, i in ranked[-n:]} if n else set()
    return [t for t in trades if t not in drop]


def judge(rule, hold, twin_finals, p):
    cut = float(np.percentile(twin_finals, p["twin_percentile"]))
    tests = {
        "beats_hold": rule["final"] > hold["final"],
        "sharpe": rule["sharpe"] >= p["min_sharpe"],
        "drawdown": rule["max_drawdown"] <= p["max_drawdown"],
        "twins": rule["final"] > cut,
        "years": rule["positive_years"] >= p["min_positive_years"],
    }
    return {"tests": tests, "twin_cut": cut, "pass": all(tests.values())}


def time_in_cash(trades, ws):
    held = [0] * len(ws)
    idx = {w: i for i, w in enumerate(ws)}
    for t in trades:
        a = idx[t.entry]
        b = idx[t.exit] if t.exit is not None else len(ws)
        for i in range(a, b):
            held[i] += 1
    return sum(1 for x in held if x == 0) / len(ws) if ws else 0.
