"""Forward-only public order-book cost observations for ledger 232."""

import argparse
from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal, InvalidOperation
import fcntl
import json
import os
import sys
import time
from pathlib import Path

import yaml

import venue_binance_us as bx
from venue_binance_us import (
    ROOT, COINS, HOUR, VENUE, Blocked, Failure, PublicPages, Refuse,
    anchor_state, append, atomic_json, checked_build, checked_dir, closed_klines,
    digest, enc, hour, iso, locked, need, now_utc, parse, private_open,
    read_log, require_go, ticket, write_anchor,
)

PLAN = ROOT / "docs/research/195_measurement_133_binance_us_cost.md"
DEFAULT_OFF = Path("/home/user/workspace/rig/data/measure_133")
PUBLIC = ROOT / "practice/forward/M133_log.json"
VENUES = {VENUE: bx.HOST}
SIDES = ("buy", "sell")
GROUPS = ("all", "midnight_utc", "btc_drop")


PINNED = ("practice/measure_133.py", "practice/venue_binance_us.py", "config/thresholds.yaml",
          "docs/research/195_measurement_133_binance_us_cost.md", "research_rig/GRID_70.json")


def settings():
    cfg = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
    block = cfg["measure_133"]
    plan = block["value"]
    inherited = cfg[plan["protocol_ref"]]["value"]
    fees = cfg[plan["fee_ref"]]["value"]
    path, rule_id, field, key = inherited["btc_drop_reference"].split(":")
    rules = json.loads((ROOT / path).read_text())
    signal = next(r for r in rules if r["id"] == rule_id)[field][key]
    return block, dict(days=inherited["days"], sizes_usd=inherited["sizes_usd"], decision=inherited["decision"],
                       binance_fee=fees["default_taker_bp"], binance_bnb_fee=fees["taker_overrides_bp"]["BNB"],
                       btc_drop=signal, coins=COINS, offset_s=plan["wake_offset_s"], window_s=plan["window_s"])


def frozen():
    block, st = settings()
    return dict(settings=st, sha256={"plan": digest(PLAN.read_bytes()),
                                   "logger": digest(Path(__file__).read_bytes()),
                                   "config_block": digest(enc(block).encode()),
                                   "venue_module": digest(Path(bx.__file__).read_bytes()),
                                   "gate_path": digest(str(bx.configured_gate_path()).encode())})


def candle_signal(rows, wake, threshold):
    closes = [v[3] for _, v in sorted(closed_klines(rows, wake, 2).items())]
    value = (closes[1] / closes[0]).ln()
    return {"status": "ok", "log_return": str(value), "drop": value <= -Decimal(str(threshold))}


def terminal(off, rows, exc, *, phase, now, wake=None):
    append(off, rows, kind="stop", phase=phase, at=iso(now), wake=iso(wake) if wake else None,
           host=exc.host, http_status=exc.status)
    raise Refuse(exc.reason)


def start(off, pages=None, clock=now_utc, *, gate=None):
    # Start creates a private frozen header; all observation starts at first_wake.
    commit = checked_build(PINNED)
    require_go(232, "M133_START", commit)
    bx.check_start(gate)
    with locked(off, create=True) as off:
        rows = read_log(off, recover=True, clock=clock)
        need(not rows, "log already started")
        fixed = frozen()
        now = clock()
        first = hour(now) + timedelta(seconds=fixed["settings"]["offset_s"])
        if first <= now:
            first += HOUR
        last = first + (fixed["settings"]["days"] * 24 - 1) * HOUR
        write_anchor(off, anchor_state(rows))
        append(off, rows, kind="header", **fixed, freeze=commit, made_utc=iso(now),
               first_wake=iso(first), last_wake=iso(last))
        return {"freeze": commit, "first_wake": iso(first), "last_wake": iso(last)}


def header(rows):
    need(rows and rows[0]["kind"] == "header", "log not started")
    return rows[0]


def record(off, pages, clock=now_utc):
    with locked(off) as off:
        return record_locked(off, pages, clock)


def deadline(wake, st):
    return hour(wake) + timedelta(seconds=st["window_s"])


def record_locked(off, pages, clock, rows=None):
    rows = read_log(off, recover=True, clock=clock) if rows is None else rows
    h = header(rows)
    need(not any(r["kind"] == "stop" for r in rows), "logger already stopped; see alive for host/status")
    need(all(h[k] == v for k, v in frozen().items()), "plan, logger or resolved settings changed")
    require_go(232, "M133_START", h["freeze"])
    st = h["settings"]
    pairs = next((r["pairs"] for r in rows if r["kind"] == "pairs"), None)
    first, last = parse(h["first_wake"]), parse(h["last_wake"])
    finished = {r["wake"] for r in rows if r["kind"] in ("wake", "void")}
    begun = {r["wake"] for r in rows if r["kind"] == "begin"}
    wake = first
    while wake <= min(last, clock()):
        stamp = iso(wake)
        now = clock()
        limit = deadline(wake, st)
        if stamp not in finished:
            if stamp in begun or now > limit:
                reason = "incomplete_attempt_not_retried" if stamp in begun else "missed_wake"
                if wake == first and pairs is None:
                    pairs = {}
                    append(off, rows, kind="pairs", status="first_inventory_not_collected", pairs=pairs)
                append(off, rows, kind="void", wake=stamp, made_utc=iso(now), reason=reason)
            elif now >= wake:
                append(off, rows, kind="begin", wake=stamp, made_utc=iso(now))
                if pairs is None:
                    try:
                        if isinstance(pages, PublicPages):
                            pages.deadline = limit
                        pairs = pages.pairs()
                        if (not isinstance(pairs, dict) or set(pairs) != set(COINS)
                                or any(not isinstance(x, str) for x in pairs.values())
                                or not wake <= clock() <= limit):
                            raise Failure("invalid_or_late_pair_metadata")
                    except Blocked as exc:
                        terminal(off, rows, exc, phase="exchangeInfo", now=clock(), wake=wake)
                    except (Failure, OSError, KeyError, TypeError, ValueError) as exc:
                        append(off, rows, kind="pairs", status=getattr(exc, "reason", "invalid_pair_metadata"), pairs={})
                        append(off, rows, kind="void", wake=stamp, made_utc=iso(clock()), reason="pair_inventory_unavailable")
                        return stamp
                    append(off, rows, kind="pairs", status="ok", pairs=pairs)
                collect(off, rows, h["settings"], pairs, pages, wake, clock)
                return stamp
        wake += HOUR
    return None


def collect(off, rows, st, pairs, pages, wake, clock):
    limit = deadline(wake, st)
    if isinstance(pages, PublicPages):
        pages.deadline = limit
    books = {venue: {} for venue in VENUES}
    try:
        try:
            signal = candle_signal(pages.candles(wake), wake, st["btc_drop"])
            if not wake <= clock() <= limit:
                signal = {"status": "wake_window_elapsed"}
        except Blocked:
            raise
        except Failure as exc:
            signal = {"status": exc.reason}
        except (KeyError, TypeError, ValueError, InvalidOperation, IndexError):
            signal = {"status": "invalid_candle"}
        for coin in COINS:
            for venue in VENUES:
                status = pairs.get(coin)
                received = None
                if status != "TRADING":
                    out = {"status": "pair_inventory_unavailable" if status is None else
                           "no_usd_pair" if status == "NO_USD_PAIR" else "pair_not_trading"}
                elif not wake <= clock() <= limit:
                    out = {"status": "missed_book_window"}
                else:
                    fee = st["binance_bnb_fee"] if coin == "BNB" else st["binance_fee"]
                    try:
                        raw = pages.book(venue, coin)
                        received = clock()
                        out = (ticket(raw, venue, st["sizes_usd"], fee) if wake <= received <= limit
                               else {"status": "missed_book_window"})
                    except Blocked:
                        raise
                    except Failure as exc:
                        out = {"status": ("no_usd_book" if exc.reason == "http_404"
                                          else exc.reason)}
                    except (KeyError, TypeError, ValueError, ArithmeticError, IndexError):
                        out = {"status": "bad book"}
                received = clock() if received is None else received
                if status == "TRADING" and not wake <= received <= limit:
                    out = {"status": "missed_book_window"}
                books[venue][coin] = dict(out, observed_utc=bx.precise_utc(received))
    except Blocked as exc:
        terminal(off, rows, exc, phase="wake", now=clock(), wake=wake)
    finally:
        if isinstance(pages, PublicPages):
            pages.deadline = None
    append(off, rows, kind="wake", wake=iso(wake), made_utc=iso(clock()), bitcoin=signal, books=books)


def stats(values):
    ordered = sorted(values)
    n = len(ordered)
    if not n:
        return {"n": 0, "median_bp": None, "p90_bp": None}
    median = (ordered[(n - 1) // 2] + ordered[n // 2]) / 2
    return {"n": n, "median_bp": float(median), "p90_bp": float(ordered[(9*n + 9)//10 - 1])}


def summarize(rows, *, full=False):
    st = header(rows)["settings"]
    samples, detailed, paired = defaultdict(list), defaultdict(list), Counter()
    book_counts = {v: Counter() for v in VENUES}
    side_counts = {v: Counter() for v in VENUES}
    wake_counts, btc_counts, pair_counts = Counter(), Counter(), Counter()
    stop = None
    for row in rows[1:]:
        kind = row["kind"]
        wake_counts[kind] += 1
        if kind == "stop":
            stop = {k: row[k] for k in ("host", "http_status")}
        if kind == "pairs":
            pair_counts.update(row["pairs"].values())
            if row["status"] != "ok":
                pair_counts[row["status"]] += 1
        if kind != "wake":
            continue
        signal = row["bitcoin"]
        btc_counts[signal["status"]] += 1
        missed = {"wake_window_elapsed", "missed_book_window", "shared_cooldown", "shared_gate_busy"}
        if (signal["status"] in missed
                or any(b["status"] in missed
                       for books in row["books"].values() for b in books.values())):
            wake_counts["partial"] += 1
        groups = ["all"]
        if parse(row["wake"]).hour == 0:
            groups.append("midnight_utc")
            wake_counts["midnight"] += 1
        if signal.get("drop"):
            groups.append("btc_drop")
        for venue, books in row["books"].items():
            for coin, book in books.items():
                book_counts[venue][book["status"]] += 1
                for size, sides in book.get("sizes", {}).items():
                    if ("midnight_utc" in groups and venue == "Binance.US"
                            and size == str(max(st["sizes_usd"]))
                            and all(sides[s]["status"] == "ok" for s in SIDES)):
                        paired[coin] += 1
                    for side, item in sides.items():
                        side_counts[venue][item["status"]] += 1
                        if item["status"] != "ok":
                            continue
                        value = Decimal(item["cost_bp"])
                        samples[venue, size, side].append(value)
                        if full:
                            for group in groups:
                                detailed[coin, venue, size, group, side].append(value)
    out = {"status": "BLOCKED" if stop else "STARTED",
           "wake_counts": dict(wake_counts), "scheduled_wakes": st["days"] * 24,
           "book_counts": book_counts, "side_counts": side_counts,
           "bitcoin_candle_counts": dict(btc_counts), "binance_pair_status_counts": dict(pair_counts),
           "stop": stop,
           "costs": {v: {str(n): {s: stats(samples[v, str(n), s]) for s in SIDES}
                         for n in st["sizes_usd"]} for v in VENUES}}
    if not full:
        return out
    out["table"] = [
        {"coin": c, "venue": v, "size_usd": n, "group": g,
         **{s: stats(detailed[c, v, str(n), g, s]) for s in SIDES}}
        for c in COINS for v in VENUES for n in st["sizes_usd"] for g in GROUPS]
    decision = st["decision"]
    qualifying = []
    for coin in COINS:
        side_values = [sorted(detailed[coin, "Binance.US", str(max(st["sizes_usd"])), "midnight_utc", s])
                       for s in SIDES]
        if paired[coin] >= decision["min_midnights"] and all(
                (v[(len(v)-1)//2] + v[len(v)//2])/2 <= Decimal(str(decision["max_cost_bp"])) for v in side_values):
            qualifying.append(coin)
    met = len(qualifying) >= decision["min_coins"]
    out["decision"] = {"met": met, "qualifying_coins": qualifying,
                       "paired_midnights_by_coin": {c: paired[c] for c in COINS},
                       "main_cost_line_bp": decision["max_cost_bp"] if met else decision["fallback_cost_bp"]}
    return out


def read_gate(rows, h, now):
    need(now > deadline(parse(h["last_wake"]), h["settings"]), "last wake has not passed")
    require_go(232, "M133_READ", h["freeze"])
    need(not any(r["kind"] == "read" for r in rows), "read already used")


def report(off, command, clock=now_utc):
    official = off == DEFAULT_OFF
    with locked(off, write=command == "read") as off:
        rows = read_log(off, recover=command == "read", clock=clock)
        h = header(rows)
        need(all(h[k] == v for k, v in frozen().items()), "plan, logger or resolved settings changed")
        if command == "read":
            now = clock()
            read_gate(rows, h, now)
            if not any(r["kind"] == "stop" for r in rows):
                finish_schedule(off, rows, h, now)
            append(off, rows, kind="read", made_utc=iso(now))
        out = summarize(rows, full=command == "read")
        if command == "publish":
            atomic_json(PUBLIC if official else off / "M133_log.json", out, public=official)
        return out


def finish_schedule(off, rows, h, now):
    """After the final window, project missed wakes locally without transport."""
    finished = {r["wake"] for r in rows if r["kind"] in ("wake", "void")}
    begun = {r["wake"] for r in rows if r["kind"] == "begin"}
    wake, last = parse(h["first_wake"]), parse(h["last_wake"])
    while wake <= last:
        stamp = iso(wake)
        if stamp not in finished:
            reason = "incomplete_attempt_not_retried" if stamp in begun else "missed_wake"
            append(off, rows, kind="void", wake=stamp, made_utc=iso(now), reason=reason)
        wake += HOUR


def loop(off, pages, clock=now_utc):
    # A distinct lifetime lock keeps observers available between wakes. A one-shot
    # record shares the operation lock and is idempotent under the same schedule.
    bx.check_start(pages.gate)
    off = checked_dir(off)
    with os.fdopen(private_open(off / ".loop.lock", os.O_RDWR | os.O_CREAT), "rb") as loop_lock:
        try:
            fcntl.flock(loop_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refuse("a loop is already running") from None
        while True:
            with locked(off) as off:
                rows = read_log(off, recover=True, clock=clock)
                h = header(rows)
                record_locked(off, pages, clock, rows)
            now = clock()
            last = parse(h["last_wake"])
            close = deadline(last, h["settings"])
            if now > close:
                return
            nxt = max(parse(h["first_wake"]), hour(now) + timedelta(seconds=h["settings"]["offset_s"]))
            if nxt <= now:
                nxt += HOUR
            time.sleep(max(0, (min(nxt, close + timedelta(microseconds=1)) - now).total_seconds()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "start", "record", "loop", "alive", "publish", "read"))
    command = parser.parse_args().command
    os.umask(0o077)
    off = DEFAULT_OFF
    try:
        if command == "plan":
            print(PLAN.read_text(), end="")
            return 0
        if command == "start":
            out = start(off)
        elif command in ("record", "loop"):
            out = {"record": record, "loop": loop}[command](off, PublicPages())
        else:
            out = report(off, command)
        if out is not None:
            print(json.dumps(out, indent=2, sort_keys=True))
    except (Refuse, OSError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
