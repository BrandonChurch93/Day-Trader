"""Ledger 230: offline decisions or public observation only. No order or account API."""
import argparse
import fcntl
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from statistics import median
from urllib.parse import urlencode

import numpy as np
import yaml

import measure_133 as m133

ROOT = Path(__file__).resolve().parents[1]
CARD = "practice/traders/E12_dip_buy_binance_us.md"
OFF = Path("/home/user/workspace/rig/data/forward_e12")
PUBLIC = ROOT / "practice/forward/E12_log.json"
sys.path.insert(0, str(ROOT / "research_rig"))
import sweep_70

PINNED = (CARD, "practice/forward_e12.py", "practice/measure_133.py",
          "research_rig/sweep_70.py", "research_rig/coverage_70.py",
          "research_rig/sweep_71.py", "research_rig/GRID_70.json", "research_rig/GRID_71.json")
HOUR = m133.HOUR
UTC = timezone.utc
BINANCE = m133.VENUE
COINS = tuple(m133.COINS)
JUDGED = "70-102"
ARMS = (JUDGED, "71-013", "71-035")
AGG_LIMIT = 1000  # wire endpoint maximum
Refuse, Failure, Blocked = m133.Refuse, m133.Failure, m133.Blocked
need = m133.need
floor_hour = m133.hour


def iso(t):
    return t.astimezone(UTC).isoformat(timespec="microseconds")


def parse(s):
    return datetime.fromisoformat(s)


def settings():
    raw = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
    own = raw["forward_e12"]["value"]
    inherited = raw[own["protocol_ref"]]["value"]
    cfg = {key: inherited[key] for key in ("sizes_usd", "wake_delay_s", "first_book_limit_s",
            "resting_window_s", "resting_page_cap", "judging_count", "judging_floor", "last_wake_utc")}
    cfg.update({key: own[key] for key in ("follow_offsets_s", "t_mark", "trim_best", "maker_fee_bp")})
    cfg["wake_window_s"] = max(cfg["follow_offsets_s"])
    roots = m133.private_roots()
    return cfg, raw[own["fee_ref"]]["value"], roots, {
        key: m133.digest(m133.enc(raw[key]).encode()) for key in
        ("forward_e12", own["protocol_ref"], own["fee_ref"], "measure_133")}


def frozen(cfg, fee, block_pins):
    return {"config": cfg, "fees": fee, "rule": rules(), "config_sha256": block_pins,
            "file_sha256": {p: m133.digest((ROOT / p).read_bytes()) for p in PINNED}}


def check_storage(off, cfg_roots, create=False):
    off = Path(off)
    resolved = off.resolve()
    need(any(root in resolved.parents for root in cfg_roots), "outside private storage root")
    return m133.checked_dir(off, create=create)


def header(rows, fz):
    need(rows and rows[0]["kind"] == "header", "not started")
    h = rows[0]
    need(h["frozen"] == fz, "frozen inputs changed")
    return h


def start(now, off=OFF):
    cfg, fee, roots, pins = settings()
    commit = m133.checked_build((*PINNED, "config/thresholds.yaml"))
    m133.require_go(230, "E12_START", commit)
    path = check_storage(off, roots, create=True)
    with m133.locked(path) as path:
        rows = m133.read_log(path)
        need(not rows, "already started")
        first = floor_hour(now) + HOUR
        need(first <= parse(cfg["last_wake_utc"]), "first wake outside dates")
        m133.write_anchor(path, m133.anchor_state(rows))
        m133.append(path, rows, kind="header", freeze=commit, first=iso(first), frozen=frozen(cfg, fee, pins))
        return {"first_wake": iso(first), "freeze": commit}


class Pages(m133.PublicPages):
    """Use the pinned public REST pace, wall budget, block handling and no redirects."""
    def candles(self, coin, wake):
        return self.klines(coin, wake, 3)

    def depth(self, coin):
        return self.book(BINANCE, coin)

    def agg(self, coin, *, first_ms=None, last_ms=None, from_id=None):
        need(coin in COINS, "unapproved USD coin")
        params = {"symbol": coin + "USD", "limit": AGG_LIMIT}
        if from_id is None:
            params.update(startTime=first_ms, endTime=last_ms)
        else:
            params["fromId"] = from_id
        return self.get(BINANCE, "/api/v3/aggTrades?" + urlencode(params))


def private_error(exc):
    return exc.reason if isinstance(exc, Failure) else "invalid_or_unavailable_page"


def collect_candles(pages, wake, coins):
    bars, failed = {}, {}
    for coin in coins:
        try:
            one = m133.closed_klines(pages.candles(coin, wake), wake, 3)
            converted = {stamp // 1000: tuple(float(x) for x in values) for stamp, values in one.items()}
            if not all(math.isfinite(x) for values in converted.values() for x in values):
                raise ValueError
            bars[coin] = converted
        except Blocked:
            raise
        except (Failure, OSError, ValueError, TypeError, KeyError, ArithmeticError) as exc:
            failed[coin] = private_error(exc)
    return bars, failed


# The frozen rule loader and signal wrapper are transcribed from the predecessor.
# They run the same audited sweep code; no predecessor transport is imported.
def rules():
    g70 = {r["id"]: r for r in json.loads((ROOT / "research_rig/GRID_70.json").read_bytes())}
    g71 = {r["id"]: r for r in json.loads((ROOT / "research_rig/GRID_71.json").read_bytes())}
    out = {"70-102": g70["70-102"], "71-013": g71["71-013"], "71-035": g71["71-035"]}
    want = {"70-102": (2, 2), "71-013": (1, 2), "71-035": (1, 1)}
    for k, r in out.items():
        need(r["family"] == "btc_overextension_fade" and r["side"] == 1 and not r["btc_hedge"]
             and r.get("delay_hours", 0) == 0 and r.get("top_coins", 1) == 1
             and r["parameters"] == {"lag": want[k][0], "threshold": 0.015, "multiple": 2.0} and r["hold_hours"] == want[k][1],
             f"rule {k} is not the frozen rule")
    return out



def decide(wake, bars, rule, roster=COINS):
    """bars[coin] maps hourly open time to (o, h, l, c, v) for hours before the wake. Returns (coin, strength) or None.
    A six-hour Tape (three hours before the wake, the wake, and two hours after it) goes through sweep_70's own
    score_signal and order_times, so missing history, ranking, ties and the maintenance hour are the audited code's."""
    n = int(wake.timestamp())
    seconds = int(HOUR.total_seconds())
    hours = np.arange(n - 3 * seconds, n + 3 * seconds, seconds, dtype=np.int64)
    panel = np.full((len(roster), len(hours), 5), np.nan)
    for j, c in enumerate(roster):
        for k, t in enumerate(hours[:3]):
            if int(t) in bars.get(c, {}):
                panel[j, k] = bars[c][int(t)]
    tape = sweep_70.Tape(list(roster), panel, hours=hours, split=None)
    signal = sweep_70.score_signal(tape, rule)
    signal[:, :3] = np.nan                    # earlier hours of the short tape were decided at their own wakes
    j, i = sweep_70.order_times(tape, rule, signal)
    if not len(i):
        return None
    need(int(i[0]) == 3, "signal outside the wake hour")
    return roster[int(j[0])], float(signal[int(j[0]), 3])


def picks(wake, bars, free, rules, last, roster):
    entries = []
    for arm in free:
        due = wake + timedelta(hours=rules[arm]["hold_hours"])
        if due > last:
            continue
        selected = decide(wake, bars, rules[arm], roster)
        if selected is not None:
            coin, strength = selected
            entries.append({"arm": arm, "coin": coin, "wake": iso(wake), "due": iso(due), "strength": strength})
    return entries


def book_now(pages, pair_states, coin, wake, clock):
    state = pair_states.get(coin, "NO_USD_PAIR")
    if state != "TRADING":
        detail = {"status": state if state in ("NO_USD_PAIR", "pair page unavailable") else "pair not trading"}
    else:
        try:
            raw = pages.depth(coin)
            detail = m133.ticket(raw, BINANCE, (), 0)
            if detail["status"] == "ok":
                detail.update(bids=raw["bids"], asks=raw["asks"])
        except Blocked:
            raise
        except (Failure, OSError, ValueError, TypeError, KeyError, ArithmeticError) as exc:
            detail = {"status": "book page unavailable", "reason": private_error(exc)}
    at = clock()
    return detail | {"received": iso(at), "taken_s": (at - wake).total_seconds()}


def walk(levels, amount, *, buy):
    """Buy a quote-currency amount or sell a base amount; return (base, quote)."""
    left, base, quote = Decimal(amount), Decimal(0), Decimal(0)
    for p, q in levels:
        px, qty = Decimal(p), Decimal(q)
        available = px * qty if buy else qty
        take = min(left, available)
        base += qty if take == available else take / px if buy else take
        quote += take if buy else take * px
        left -= take
        if not left:
            return base, quote
    return None


def fee_bp(fees, coin):
    return Decimal(fees["taker_overrides_bp"].get(coin, fees["default_taker_bp"]))


def usable(book):
    return bool(book and book["status"] == "ok")


def cost(book, walked, fee, *, buy):
    base, quote = walked
    mid = Decimal(book["midpoint"])
    px = quote / base
    ratio = px / mid
    return float(((ratio - 1) if buy else (1 - ratio)) * 10000 + ratio * fee)


def leg_reason(book, limit=None):
    if not book:
        return "book missing"
    if not usable(book):
        return book["status"]
    if limit is not None and not 0 <= book["taken_s"] <= limit:
        return "late book"
    return None


def settle(entry, exit_book, dollars, fee, *, limit=None, maker_bp=None):
    reason = leg_reason(entry, limit) or leg_reason(exit_book, limit)
    if reason:
        return {"reason": reason}
    size = Decimal(dollars)
    walked = (size / Decimal(entry["bid"]), size) if maker_bp is not None else walk(entry["asks"], size, buy=True)
    if walked is None:
        return {"reason": "entry too thin"}
    sold = walk(exit_book["bids"], walked[0], buy=False)
    if sold is None:
        return {"reason": "exit too thin"}
    rate = fee / 10000
    net = (sold[1] * (1 - rate) - size * (1 + (rate if maker_bp is None else Decimal(maker_bp) / 10000))) / size
    return {"net": float(net), "sell_cost_bp": cost(exit_book, sold, fee, buy=False)}


def epoch_ms(t):
    delta = t - datetime(1970, 1, 1, tzinfo=UTC)
    return (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000


def resting(pages, coin, first_book, cfg):
    """Post-window, bounded, forward-only paging. No coverage means no no-fill claim."""
    if not usable(first_book):
        return {"status": "UNKNOWN", "reason": "limit book missing", "pages": []}
    then = parse(first_book["received"])
    start_ms = epoch_ms(then) + 1
    end_ms = epoch_ms(then + timedelta(seconds=cfg["resting_window_s"]))
    limit = Decimal(first_book["bid"])
    evidence, last_id, last_t = [], None, None
    for _ in range(cfg["resting_page_cap"]):
        index = None if last_id is None else last_id + 1
        try:
            raw = pages.agg(coin, first_ms=start_ms, last_ms=end_ms, from_id=index)
            if not isinstance(raw, list) or len(raw) > AGG_LIMIT:
                raise ValueError
            parsed = []
            for row in raw:
                a, t, p = row["a"], row["T"], row["p"]
                if type(a) is not int or a < 0 or type(t) is not int or t < start_ms or type(p) is not str:
                    raise ValueError
                if index is None and t > end_ms:
                    raise ValueError
                if last_id is not None and (a != last_id + 1 or t < last_t):
                    raise ValueError
                px = m133.price(p)
                parsed.append((a, t, px))
                last_id, last_t = a, t
        except Blocked:
            raise
        except (Failure, OSError, IndexError, KeyError, ValueError, TypeError, ArithmeticError):
            return {"status": "UNKNOWN", "reason": "trade page failed or has a gap", "pages": evidence}
        evidence.append({"count": len(parsed), "first_id": parsed[0][0] if parsed else None,
                         "last_id": last_id, "last_ms": last_t})
        for a, t, px in parsed:
            if t > end_ms:
                return {"status": "NOT_FILLED", "pages": evidence}
            if px < limit:
                fill = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=t)
                return {"status": "FILLED", "fill": iso(fill), "seconds_to_fill": (fill - then).total_seconds(),
                        "print_id": a, "print_price": str(px), "pages": evidence}
        if index is None and len(parsed) < AGG_LIMIT:
            return {"status": "NOT_FILLED", "pages": evidence}
        if index is not None and len(parsed) < AGG_LIMIT:
            break
    return {"status": "UNKNOWN", "reason": "window coverage not proved", "pages": evidence}


def index_log(rows):
    opens, claims, visits, books, rests, closed = {}, set(), {}, {}, {}, []
    for r in rows:
        kind = r["kind"]
        if kind == "claim":
            claims.add(r["wake"])
        if kind in ("wake", "void"):
            w = r["wake"]
            visits[w] = r
            for arm in r["exits"]:
                closed.append((opens.pop(arm), w, kind))
            for entry in r["entries"]:
                opens[entry["arm"]] = entry
            for side in ("entry", "exit"):
                for c, book in r.get(f"{side}_books", {}).items():
                    books[w, c, side, 0] = book
        if kind == "follow":
            books[r["wake"], r["coin"], r["side"], r["offset_s"]] = r["book"]
        if kind == "rest":
            rests[r["wake"], r["coin"]] = r["resting"]
    return opens, claims, visits, books, rests, closed


def evaluate(closed, books, cfg, fees):
    lines = []
    for entry, exit_wake, exit_kind in closed:
        w, coin = entry["wake"], entry["coin"]
        charge = fee_bp(fees, coin)
        result = {}
        for offset in (0, *cfg["follow_offsets_s"]):
            first, last = books.get((w, coin, "entry", offset)), books.get((exit_wake, coin, "exit", offset))
            for size in cfg["sizes_usd"].values():
                key = f"{size}:{offset}"
                result[key] = (settle(first, last, size, charge, limit=cfg["first_book_limit_s"] if not offset else None)
                               if exit_kind == "wake" else {"reason": "exit wake void"})
        lines.append({"entry": entry, "exit": exit_wake, "exit_kind": exit_kind, "lines": result})
    return lines


def judged_trades(lines, cfg):
    key = f"{cfg['sizes_usd']['judged']}:0"
    return sorted((r for r in lines if r["entry"]["arm"] == JUDGED and "net" in r["lines"][key]),
                  key=lambda r: r["entry"]["wake"])


def finish_void(path, rows, wake, opens, reason):
    w = iso(wake)
    due = [a for a, e in opens.items() if e["due"] == w]
    m133.append(path, rows, kind="void", wake=w, reason=reason, entries=[], exits=due)
    for a in due:
        del opens[a]


def capture_wake(path, rows, pages, wake, clock, sleep, cfg, fees, rules, idx, roster):
    opens, _, _, prior_books, _, closed = idx
    w = iso(wake)
    due = [a for a, e in opens.items() if e["due"] == w]
    free = [a for a in ARMS if a not in opens or a in due]
    live_until = wake + timedelta(seconds=cfg["wake_window_s"])
    last = parse(cfg["last_wake_utc"])
    coins_due = {opens[arm]["coin"] for arm in due}
    exit_books, entry_books = {}, {}
    pair_states = None
    pages.deadline = live_until

    def read_pairs():
        try:
            states = pages.pairs()
            if not isinstance(states, dict):
                raise ValueError
            return states
        except Blocked:
            raise
        except (Failure, OSError, ValueError, TypeError, KeyError):
            return dict.fromkeys(COINS, "pair page unavailable")

    # Exits have no candle dependency. Sample their books before a slow or
    # failing signal-panel request can consume their first-book window.
    if coins_due:
        pair_states = read_pairs()
        for coin in sorted(coins_due):
            exit_books[coin] = book_now(pages, pair_states, coin, wake, clock)
    can_enter = any(wake + timedelta(hours=rules[a]["hold_hours"]) <= last for a in free)
    bars, failed = collect_candles(pages, wake, roster) if can_enter else ({}, {})
    proposed = picks(wake, bars, free, rules, last, roster) if can_enter and not failed else []
    if any(a == JUDGED for a in due):
        judged_due = opens[JUDGED]
        coin = judged_due["coin"]
        b0, b1 = prior_books.get((judged_due["wake"], coin, "entry", 0)), exit_books[coin]
        counts_now = "net" in settle(b0, b1, cfg["sizes_usd"]["judged"], fee_bp(fees, judged_due["coin"]),
                                     limit=cfg["first_book_limit_s"])
        if counts_now and len(judged_trades(evaluate(closed, prior_books, cfg, fees), cfg)) + 1 >= cfg["judging_count"]:
            proposed = []
    if proposed and pair_states is None:
        pair_states = read_pairs()
    # An entry cannot use a book sampled before its decision, even on a coin
    # that already has an exit book from this wake.
    for coin in sorted({e["coin"] for e in proposed}):
        entry_books[coin] = book_now(pages, pair_states, coin, wake, clock)
    pair_states = pair_states or {}
    m133.append(path, rows, kind="wake", wake=w, entries=proposed, exits=due,
                entry_books=entry_books, exit_books=exit_books,
                entries_void=bool(failed), candle_failures=failed,
                busy=[a for a in ARMS if a not in free],
                pair_states={c: pair_states.get(c, "NO_USD_PAIR") for c in sorted(entry_books.keys() | exit_books.keys())},
                closed_bar_sha256=m133.digest(m133.enc(bars).encode()), signal_bars=bars if proposed else {})
    wake_row = rows[-1]
    tasks = []
    for side, first in (("entry", entry_books), ("exit", exit_books)):
        for coin, b in first.items():
            btime = parse(b["received"])
            if pair_states.get(coin) == "TRADING":
                for offset in cfg["follow_offsets_s"]:
                    tasks.append((btime + timedelta(seconds=offset), 0, coin, side, offset))
            if side == "entry":
                if usable(b):
                    tasks.append((btime + timedelta(seconds=cfg["resting_window_s"], milliseconds=1), 1, coin, side, 0))
                else:
                    m133.append(path, rows, kind="rest", wake=w, coin=coin, resting=resting(pages, coin, b, cfg))
    for when, kind, coin, side, offset in sorted(tasks):
        sleep(max(0, (when - clock()).total_seconds()))
        if clock() >= wake + HOUR:
            break
        pages.deadline = wake + HOUR
        if kind == 0:
            book = book_now(pages, pair_states, coin, wake, clock)
            m133.append(path, rows, kind="follow", wake=w, coin=coin, side=side, offset_s=offset, book=book)
        else:
            m133.append(path, rows, kind="rest", wake=w, coin=coin, resting=resting(pages, coin, entry_books[coin], cfg))
    return wake_row


def freeze_roster(path, rows, pages, wake, clock, cfg):
    pages.deadline = wake + timedelta(seconds=cfg["first_book_limit_s"])
    states = pages.pairs()
    if (not isinstance(states, dict) or set(states) != set(COINS)
            or any(not isinstance(v, str) for v in states.values())
            or clock() >= pages.deadline):
        raise Failure("invalid or late first-wake USD roster")
    roster = [c for c in COINS if states[c] != "NO_USD_PAIR"]
    if "BTC" not in roster:
        raise Failure("first-wake roster lacks BTC/USD")
    m133.append(path, rows, kind="roster", wake=iso(wake), coins=roster, states=states)
    return roster


def record(now, pages=None, off=OFF, clock=m133.now_utc, sleep=time.sleep):
    cfg, fees, roots, pins = settings()
    path = check_storage(off, roots)
    with m133.locked(path) as path:
        rows = m133.read_log(path, recover=True, clock=clock)
        start_row = header(rows, frozen(cfg, fees, pins))
        m133.require_go(230, "E12_START", start_row["freeze"])
        if any(r["kind"] == "stop" for r in rows):
            return {"kind": "stopped"}
        idx = index_log(rows)
        opens, claims, visits, books, _, closed = idx
        if len(judged_trades(evaluate(closed, books, cfg, fees), cfg)) >= cfg["judging_count"]:
            return {"kind": "judging point"}
        wake = floor_hour(now)
        last = parse(cfg["last_wake_utc"])
        current = parse(start_row["first"])
        if visits:
            current = parse(max(visits)) + HOUR
        roster = next((r["coins"] for r in rows if r["kind"] == "roster"), None)
        first_wake = parse(start_row["first"])
        while current <= min(last, wake):
            w = iso(current)
            if roster is None and (current > first_wake or w in claims or
                                   now >= first_wake + timedelta(seconds=cfg["first_book_limit_s"])):
                m133.append(path, rows, kind="stop", wake=iso(first_wake), reason="first-wake roster not frozen",
                            made_utc=iso(clock()))
                finish_void(path, rows, first_wake, opens, "first-wake roster not frozen")
                return {"kind": "stop"}
            if w in claims:
                finish_void(path, rows, current, opens, "claimed wake interrupted; not fetched again")
                if current == wake:
                    return rows[-1]
            elif now >= current + timedelta(seconds=cfg["wake_window_s"]):
                finish_void(path, rows, current, opens, "wake missed")
            elif current == wake and now >= wake + timedelta(seconds=cfg["wake_delay_s"]):
                m133.append(path, rows, kind="claim", wake=w, made_utc=iso(clock()))
                try:
                    source = pages if pages is not None else Pages()
                    if roster is None:
                        try:
                            roster = freeze_roster(path, rows, source, wake, clock, cfg)
                        except Blocked:
                            raise
                        except (Failure, OSError, ValueError, TypeError, KeyError) as exc:
                            m133.append(path, rows, kind="stop", wake=w, reason=private_error(exc), made_utc=iso(clock()))
                            finish_void(path, rows, wake, opens, "first-wake roster not frozen")
                            return {"kind": "stop"}
                    return capture_wake(path, rows, source, wake, clock, sleep,
                                        cfg, fees, start_row["frozen"]["rule"], idx, roster)
                except Blocked as exc:
                    m133.append(path, rows, kind="stop", wake=w, reason=exc.reason,
                                host=exc.host, http_status=exc.status, made_utc=iso(clock()))
                    blocked = rows[-1]
                    if not any(r.get("wake") == w and r["kind"] in ("wake", "void") for r in rows):
                        finish_void(path, rows, wake, opens, "host stopped before the wake completed")
                    return blocked
            else:
                break
            current += HOUR
        return {"kind": "nothing due"}


def stats(x):
    return {"n": len(x), "median": float(median(x)) if x else None,
            "p90": float(np.percentile(x, 90)) if x else None, "max": max(x) if x else None}


def rest_marks(entry, books, rest, cfg):
    coin, w = entry["coin"], entry["wake"]
    first = books.get((w, coin, "entry", 0))
    result = {}
    for offset in cfg["follow_offsets_s"]:
        later = books.get((w, coin, "entry", offset))
        marker = {"phase": "UNKNOWN", "move_bp": None}
        if usable(first) and usable(later):
            if rest["status"] == "FILLED":
                marker["phase"] = "BEFORE_FILL" if parse(later["received"]) < parse(rest["fill"]) else "AFTER_FILL"
            else:
                marker["phase"] = rest["status"]
            marker["move_bp"] = float((Decimal(later["midpoint"]) / Decimal(first["bid"]) - 1) * 10000)
        result[str(offset)] = marker
    return result


def rest_for(rests, entry):
    return rests.get((entry["wake"], entry["coin"]), {"status": "UNKNOWN", "reason": "trade page not recorded"})


def summary(rows, cfg, fees):
    opens, claims, visits, books, rests, closed = index_log(rows)
    finished = evaluate(closed, books, cfg, fees)
    entries = [e for w in visits.values() for e in w["entries"]]
    resting_counts = {a: {"FILLED": 0, "NOT_FILLED": 0, "UNKNOWN": 0} for a in ARMS}
    book_status = defaultdict(int)
    clock_samples = defaultdict(list)
    costs = defaultdict(lambda: {"buy": [], "sell": []})
    stop = next((r for r in rows if r["kind"] == "stop"), None)
    for (_, _, _, offset), book in books.items():
        book_status[book["status"]] += 1
        if usable(book):
            clock_samples[str(offset)].append(book["taken_s"])
    for e in entries:
        resting_counts[e["arm"]][rest_for(rests, e)["status"]] += 1
        first = books.get((e["wake"], e["coin"], "entry", 0))
        if leg_reason(first, cfg["first_book_limit_s"]):
            continue
        for size in cfg["sizes_usd"].values():
            walked = walk(first["asks"], size, buy=True)
            if walked:
                costs[str(size)]["buy"].append(cost(first, walked, fee_bp(fees, e["coin"]), buy=True))
    for r in finished:
        for size in cfg["sizes_usd"].values():
            a = r["lines"][f"{size}:0"]
            # Costs are quote measurements, not P&L. The late or thin filter
            # is applied on the judged line; late fills are not claimed here.
            if "sell_cost_bp" in a:
                costs[str(size)]["sell"].append(a["sell_cost_bp"])
    primary = f"{cfg['sizes_usd']['judged']}:0"
    voids = Counter(r["lines"][primary]["reason"] for r in finished
                    if r["entry"]["arm"] == JUDGED and "reason" in r["lines"][primary])
    status = ("BLOCKED" if "http_status" in stop else "STOPPED") if stop else "STARTED" if rows else "NOT_STARTED"
    return {"card": "E12", "status": status,
            "block": {k: stop[k] for k in ("host", "http_status", "reason") if k in stop} if stop else None,
            "frozen_usd_pairs": next((len(r["coins"]) for r in rows if r["kind"] == "roster"), None),
            "wakes": sum(r["kind"] == "wake" for r in visits.values()),
            "void_wakes": sum(r["kind"] == "void" for r in visits.values()),
            "entry_void_wakes": sum(bool(r.get("entries_void")) for r in visits.values()),
            "claimed_unresolved_wakes": len(claims - visits.keys()),
            "late_wakes": len({w for (w, _, _, offset), b in books.items() if not offset and usable(b)
                               and b["taken_s"] > cfg["first_book_limit_s"]}),
            "book_status": dict(book_status), "seconds_after_hour": {k: stats(v) for k, v in clock_samples.items()},
            "cost_per_side_bp": {n: {s: stats(v) for s, v in sides.items()} for n, sides in costs.items()},
            "signals_by_arm": {a: sum(e["arm"] == a for e in entries) for a in ARMS},
            "slots_open": len(opens), "judged_trades": len(judged_trades(finished, cfg)),
            "closed_by_arm": {a: sum(r["entry"]["arm"] == a for r in finished) for a in ARMS},
            "judged_void_reasons": dict(voids),
            "resting_counts_by_arm": resting_counts}


def alive(off=OFF):
    cfg, fee, roots, pins = settings()
    if not Path(off).exists() and not Path(off).is_symlink():
        return summary([], cfg, fee)
    with m133.locked(check_storage(off, roots), write=False) as path:
        rows = m133.read_log(path)
        header(rows, frozen(cfg, fee, pins))
        return summary(rows, cfg, fee)


def publish(off=OFF, target=PUBLIC):
    out = alive(off)
    m133.atomic_json(target, out)
    return out


def judge(valid, cfg):
    valid = valid[:cfg["judging_count"]]
    n = len(valid)
    if n < cfg["judging_floor"]:
        return {"verdict": "too few to judge", "trades": n}
    key = f"{cfg['sizes_usd']['judged']}:0"
    ret = np.array([r["lines"][key]["net"] for r in valid])
    dates = np.array([parse(r["entry"]["wake"]).date().toordinal() for r in valid], dtype=np.int64)
    t = sweep_70.t_cluster(ret, dates - dates.min())
    trimmed = np.sort(ret)[:-cfg["trim_best"]]
    mean, trim = float(ret.mean()), float(trimmed.mean()) if len(trimmed) else None
    marks = {"mean_above_zero": mean > 0, "day_t_at_least_e09_mark": t is not None and t >= cfg["t_mark"],
             "mean_above_zero_without_e09_best": trim is not None and trim > 0}
    return {"verdict": "pass" if all(marks.values()) else "did not pass", "trades": n,
            "net_mean": mean, "day_t": float(t) if t is not None else None, "entry_days": int(len(set(dates))),
            "net_mean_without_best": trim, "marks": marks}


def line_summary(values, size):
    return {"trades": len(values), "net_mean": float(np.mean(values)) if values else None,
            "pretend_usd": float(sum(values) * size)}


def shown_results(visits, finished, books, rests, cfg, fees, cut):
    by_key = {(r["entry"]["arm"], r["entry"]["wake"]): r for r in finished}
    result = {}
    main = cfg["sizes_usd"]["judged"]
    for arm in ARMS:
        values, resting_values, missed_values, fill_seconds, counts = defaultdict(list), [], [], [], Counter()
        move_groups = {str(s): defaultdict(list) for s in cfg["follow_offsets_s"]}
        for v in visits.values():
            for e in v["entries"]:
                if e["arm"] != arm or e["wake"] > cut:
                    continue
                r = by_key.get((arm, e["wake"]))
                rest = rest_for(rests, e)
                marks = rest_marks(e, books, rest, cfg)
                counts[rest["status"]] += 1
                if r:
                    for k, line in r["lines"].items():
                        if "net" in line:
                            values[k].append(line["net"])
                if rest["status"] == "FILLED":
                    fill_seconds.append(rest["seconds_to_fill"])
                    maker = {"reason": "exit wake void or unresolved"}
                    if r and r["exit_kind"] == "wake":
                        coin = e["coin"]
                        b0 = books.get((e["wake"], coin, "entry", 0))
                        b1 = books.get((r["exit"], coin, "exit", 0))
                        why = leg_reason(b1, cfg["first_book_limit_s"])
                        maker = {"reason": why} if why else settle(b0, b1, main, fee_bp(fees, e["coin"]), maker_bp=cfg["maker_fee_bp"])
                    if "net" in maker:
                        resting_values.append(maker["net"])
                elif rest["status"] == "NOT_FILLED" and r and "net" in r["lines"][f"{main}:0"]:
                    missed_values.append(r["lines"][f"{main}:0"]["net"])
                for offset, m in marks.items():
                    if m["move_bp"] is not None:
                        move_groups[offset][m["phase"]].append(m["move_bp"])
        counts = {k: counts[k] for k in ("FILLED", "NOT_FILLED", "UNKNOWN")}
        known = counts["FILLED"] + counts["NOT_FILLED"]
        result[arm] = {
            "taker_lines_usd_size_and_offset_s": {
                f"{n}:{o}": line_summary(values[f"{n}:{o}"], n)
                for n in cfg["sizes_usd"].values() for o in (0, *cfg["follow_offsets_s"])
                if arm != JUDGED or n != main or o != 0},
            "resting_line": line_summary(resting_values, main),
            "taker_line_when_not_filled": line_summary(missed_values, main),
            "resting_counts": counts,
            "resting_fill_rate_known": counts["FILLED"] / known if known else None,
            "resting_seconds_to_fill": stats(fill_seconds),
            "scheduled_midpoint_move_bp": {o: {phase: stats(v) for phase, v in g.items()}
                                           for o, g in move_groups.items()},
        }
    return result


def score_gate(rows, h, now, n, cfg):
    need(not any(r["kind"] == "score" for r in rows), "score already read")
    last = parse(cfg["last_wake_utc"])
    hit = n >= cfg["judging_count"]
    need(hit or now >= last + timedelta(seconds=cfg["wake_window_s"]), "not yet: judging point has not arrived")
    m133.require_go(230, "E12_SCORE", h["freeze"])
    return hit, last


def score(now, off=OFF):
    cfg, fees, roots, pins = settings()
    with m133.locked(check_storage(off, roots)) as path:
        rows = m133.read_log(path, recover=True, clock=lambda: now)
        h = header(rows, frozen(cfg, fees, pins))
        _, _, visits, books, rests, closed = index_log(rows)
        finished = evaluate(closed, books, cfg, fees)
        valid = judged_trades(finished, cfg)
        hit, last = score_gate(rows, h, now, len(valid), cfg)
        cut = valid[cfg["judging_count"] - 1]["entry"]["wake"] if hit else iso(last)
        out = {"card": "E12", "judged_arm": JUDGED, "cutoff": "trade count" if hit else "end date",
               "judged": judge(valid, cfg), "shown": shown_results(visits, finished, books, rests, cfg, fees, cut)}
        m133.append(path, rows, kind="score", result_sha256=m133.digest(m133.enc(out).encode()),
                    made_utc=iso(now))
        return out


def loop(off=OFF, clock=m133.now_utc, sleep=time.sleep):
    cfg, _, roots, _ = settings()
    path = check_storage(off, roots)
    fd = m133.private_open(path / ".loop.lock", os.O_RDWR | os.O_CREAT)
    with os.fdopen(fd, "rb") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refuse("a loop is already running") from None
        pages = Pages()
        delay = timedelta(seconds=cfg["wake_delay_s"])
        last = parse(cfg["last_wake_utc"])
        while True:
            out = record(clock(), pages, path, clock, sleep)
            if out["kind"] in ("stop", "stopped", "judging point") or clock() >= last + timedelta(seconds=cfg["wake_window_s"]):
                return {"status": out["kind"]}
            t = clock()
            nxt = floor_hour(t) + delay
            if nxt <= t:
                nxt += HOUR
            sleep(max(0, (min(nxt, last + timedelta(seconds=cfg["wake_window_s"])) - t).total_seconds()))


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=("plan", "start", "record", "loop", "alive", "publish", "score"))
    cmd = cli.parse_args().command
    os.umask(0o077)
    try:
        now = m133.now_utc()
        if cmd == "plan":
            cfg, fees, _, pins = settings()
            out = frozen(cfg, fees, pins)
        elif cmd == "start":
            out = start(now)
        elif cmd == "record":
            r = record(now)
            out = {k: r[k] for k in ("kind", "wake", "host", "http_status") if k in r}
        elif cmd == "loop":
            out = loop()
        elif cmd == "alive":
            out = alive()
        elif cmd == "publish":
            out = publish()
        else:
            out = score(now)
        print(json.dumps(out, sort_keys=True, allow_nan=False))
        return 0
    except (Refuse, OSError) as exc:
        print("REFUSED " + (type(exc).__name__ if isinstance(exc, OSError) else str(exc)))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
