"""Forward-only public order-book cost observations for ledger 234."""

import argparse
from collections import Counter, defaultdict
from datetime import timedelta
from decimal import Decimal
import fcntl
import json
import os
import sys
import time
from pathlib import Path

import yaml

import venue_binance_us as bx
from forward_e14 import TimedGate, WakeClock, literal_git, require_go
from venue_binance_us import (
    ROOT, COINS, HOUR, VENUE, Blocked, Failure, PublicPages, Refuse,
    anchor_state, append, atomic_json, checked_dir, closed_klines,
    digest, enc, hour, iso, locked, need, now_utc, parse, private_open,
    read_log, ticket, write_anchor,
)

PLAN = ROOT / "docs/research/202_measurement_134_binance_us_cost.md"
DEFAULT_OFF = Path("/home/user/workspace/rig/data/measure_134")
PUBLIC = ROOT / "practice/forward/M134_log.json"
VENUES = {VENUE: bx.HOST}
SIDES = ("buy", "sell")
GROUPS = ("all", "midnight_utc", "btc_drop")


PINNED = ("practice/measure_134.py", "practice/forward_e14.py", "practice/venue_binance_us.py", "config/thresholds.yaml",
          "docs/research/202_measurement_134_binance_us_cost.md", "research_rig/GRID_70.json")


def request(pages, fetch, start_at, close, timing, sleep, busy_s, *, stamped=False):
    """Cap unsent admission separately from the shared HTTP receipt deadline."""
    _, began = timing.sample()
    busy = False
    gate = getattr(pages, "gate", None)

    def admission():
        now, elapsed = timing.sample()
        if now < start_at:
            raise Failure("wake_window_not_open")
        if now >= close:
            raise Failure("shared_gate_busy" if busy else "wake_window_elapsed")
        remaining = busy_s - (elapsed - began)
        if remaining <= 0:
            raise Failure("shared_gate_busy")
        return now, remaining

    try:
        while True:
            admission()
            # TimedGate checks admission during acquisition and under the
            # mutex. Once admitted, the HTTP timer retains the receipt window.
            pages.deadline = close
            if isinstance(gate, TimedGate):
                gate.before_send = admission
            try:
                data = fetch()
            except Failure as exc:
                if exc.reason != "shared_gate_busy":
                    raise
                busy = True
                now, remaining = admission()
                sleep(min(0.25, remaining, (close - now).total_seconds()))
            else:
                received, _ = timing.sample()
                if not start_at <= received <= close:
                    raise Failure("late book" if received > close else "wake_window_not_open")
                return (data, received) if stamped else data
    finally:
        if isinstance(gate, TimedGate):
            gate.before_send = None
        pages.deadline = None


def settings():
    cfg = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
    block = cfg["measure_134"]
    plan = block["value"]
    need(plan["roster_ref"] == "practice/venue_binance_us.py:COINS", "unrecognized roster reference")
    venue = cfg[plan["protocol_ref"]]["value"]
    inherited = cfg[venue["protocol_ref"]]["value"]
    fees = cfg[venue["fee_ref"]]["value"]
    path, rule_id, field, key = inherited["btc_drop_reference"].split(":")
    rules = json.loads((ROOT / path).read_text())
    signal = next(r for r in rules if r["id"] == rule_id)[field][key]
    return block, dict(days=inherited["days"], sizes_usd=inherited["sizes_usd"], decision=inherited["decision"],
                       binance_fee=fees["default_taker_bp"], binance_bnb_fee=fees["taker_overrides_bp"]["BNB"],
                       btc_drop=signal, coins=COINS, offset_s=plan["wake_offset_s"], window_s=plan["window_s"],
                       busy_wait_s=plan["busy_wait_s"])


def frozen():
    block, st = settings()
    return dict(settings=st, sha256={"plan": digest(PLAN.read_bytes()),
                                   "logger": digest(Path(__file__).read_bytes()),
                                   "helpers": digest((ROOT / "practice/forward_e14.py").read_bytes()),
                                   "config_block": digest(enc(block).encode()),
                                   "venue_module": digest(Path(bx.__file__).read_bytes()),
                                   "gate_path": digest(str(bx.configured_gate_path()).encode())})


def candle_signal(rows, wake, threshold):
    closes = [v[3] for _, v in sorted(closed_klines(rows, wake, 2).items())]
    value = (closes[1] / closes[0]).ln()
    return {"status": "ok", "log_return": str(value), "drop": value <= -Decimal(str(threshold))}


def terminal(off, rows, exc, *, phase, now, wake=None):
    event = {"host": bx.HOST, "reason": exc.reason}
    if isinstance(exc, Blocked):
        event["http_status"] = exc.status
    append(off, rows, kind="stop", phase=phase, at=iso(now), wake=iso(wake) if wake else None, **event)
    raise Refuse(exc.reason)


def checked_build():
    tracks = literal_git("ls-files", "-v", "-z", "--", *PINNED).split("\0")
    need({r[2:] for r in tracks if r.startswith("H ")} == set(PINNED)
         and not literal_git("status", "--porcelain", "--untracked-files=no", "--", *PINNED),
         "frozen inputs not tracked and clean")
    commit = literal_git("rev-parse", "--verify", "HEAD^{commit}").strip()
    for path in PINNED:
        need(literal_git("show", f"{commit}:{path}", binary=True) == (ROOT / path).read_bytes(),
             "frozen input differs from literal build")
    need(literal_git("rev-parse", f"{commit}:practice/venue_binance_us.py").strip()
         == "ccd1e045c705fbc4bfa2c221bed0015ac2ce8db0", "shared gate differs from audited version")
    return commit


def start(off, clock=now_utc, *, gate=None):
    # Start creates a private frozen header; all observation starts at first_wake.
    commit = checked_build()
    require_go(234, "M134_START", commit)
    generation = bx.check_start(gate)
    if generation:
        require_go(234, "M134_START", commit, generation=generation)
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
        append(off, rows, kind="header", **fixed, freeze=commit, venue_generation=generation, made_utc=iso(now),
               first_wake=iso(first), last_wake=iso(last))
        return {"freeze": commit, "first_wake": iso(first), "last_wake": iso(last), "venue_generation": generation}


def header(rows):
    need(rows and rows[0]["kind"] == "header", "log not started")
    return rows[0]


def record(off, pages, clock=now_utc, sleep=time.sleep, monotonic=time.monotonic):
    with locked(off) as off:
        return record_locked(off, pages, clock, sleep=sleep, monotonic=monotonic)


def deadline(wake, st):
    return hour(wake) + timedelta(seconds=st["window_s"])


def record_locked(off, pages, clock, rows=None, *, sleep=time.sleep, monotonic=time.monotonic):
    rows = read_log(off, recover=True, clock=clock) if rows is None else rows
    h = header(rows)
    need(not any(r["kind"] == "stop" for r in rows), "logger already stopped; see alive for host/status")
    need(not any(r["kind"] == "read" for r in rows), "schedule already read")
    need(all(h[k] == v for k, v in frozen().items()), "plan, logger or resolved settings changed")
    st = h["settings"]
    pairs = next((r["pairs"] for r in rows if r["kind"] == "pairs"), None)
    first, last = parse(h["first_wake"]), parse(h["last_wake"])
    finished = {r["wake"] for r in rows if r["kind"] in ("wake", "void")}
    begun = {r["wake"] for r in rows if r["kind"] == "begin"}
    wake = first
    timing = WakeClock(clock, monotonic)

    def void(stamp, now, reason):
        nonlocal pairs
        if wake == first and pairs is None:
            pairs = {}
            append(off, rows, kind="pairs", status="first_inventory_not_collected", pairs=pairs)
        append(off, rows, kind="void", wake=stamp, made_utc=iso(now), reason=reason)

    while wake <= last:
        stamp = iso(wake)
        if stamp in finished:
            wake += HOUR
            continue
        try:
            now, _ = timing.sample()
        except Failure as exc:
            # A broken time source cannot create a new wake. Only abandon a
            # wake already identified in this call or an anchored interrupted one.
            if stamp in begun:
                void(stamp, clock(), exc.reason)
            return None
        if now < wake:
            break
        limit = deadline(wake, st)
        if stamp in begun or now >= limit:
            void(stamp, now, "incomplete_attempt_not_retried" if stamp in begun else "missed_wake")
            wake += HOUR
            continue
        require_go(234, "M134_START", h["freeze"])
        try:
            claim_time, _ = timing.sample()
        except Failure as exc:
            void(stamp, now, exc.reason)
            return stamp
        if not wake <= claim_time < limit:
            void(stamp, now, "missed_wake")
            return stamp
        if isinstance(pages, PublicPages):
            generation = h.get("venue_generation")
            need(type(generation) is int and generation >= 0, "invalid shared gate generation")
            # The ordinary shared request verifies stop and generation with its mutex.
            pages.generation = generation
        append(off, rows, kind="begin", wake=stamp, made_utc=iso(claim_time))

        def fetch(fn, *, stamped=False):
            return request(pages, fn, wake, limit, timing, sleep, st["busy_wait_s"], stamped=stamped)

        if pairs is None:
            try:
                pairs = fetch(pages.pairs)
                if (not isinstance(pairs, dict) or set(pairs) != set(st["coins"])
                        or any(not isinstance(x, str) for x in pairs.values())):
                    raise Failure("invalid_pair_metadata")
            except (Blocked, bx.GateTerminal) as exc:
                terminal(off, rows, exc, phase="exchangeInfo", now=clock(), wake=wake)
            except (Failure, OSError, KeyError, TypeError, ValueError, ArithmeticError) as exc:
                append(off, rows, kind="pairs", status=getattr(exc, "reason", "invalid_pair_metadata"), pairs={})
                append(off, rows, kind="void", wake=stamp, made_utc=iso(clock()), reason="pair_inventory_unavailable")
                return stamp
            append(off, rows, kind="pairs", status="ok", pairs=pairs)
        collect(off, rows, st, pairs, pages, wake, clock, fetch)
        return stamp
    return None


def collect(off, rows, st, pairs, pages, wake, clock, fetch):
    books = {venue: {} for venue in VENUES}
    try:
        try:
            signal = candle_signal(fetch(lambda: pages.candles(wake)), wake, st["btc_drop"])
        except Blocked:
            raise
        except Failure as exc:
            signal = {"status": exc.reason}
        except OSError:
            signal = {"status": "transport_failure"}
        except (KeyError, TypeError, ValueError, ArithmeticError, IndexError):
            signal = {"status": "invalid_candle"}
        for coin in st["coins"]:
            for venue in VENUES:
                status = pairs.get(coin)
                received = None
                if status != "TRADING":
                    out = {"status": "pair_inventory_unavailable" if status is None else
                           "no_usd_pair" if status == "NO_USD_PAIR" else "pair_not_trading"}
                else:
                    fee = st["binance_bnb_fee"] if coin == "BNB" else st["binance_fee"]
                    try:
                        raw, received = fetch(lambda: pages.book(venue, coin), stamped=True)
                        out = ticket(raw, venue, st["sizes_usd"], fee)
                    except Blocked:
                        raise
                    except Failure as exc:
                        out = {"status": ("no_usd_book" if exc.reason == "http_404"
                                          else exc.reason)}
                    except OSError:
                        out = {"status": "transport_failure"}
                    except (KeyError, TypeError, ValueError, ArithmeticError, IndexError):
                        out = {"status": "bad book"}
                books[venue][coin] = dict(out, observed_utc=bx.precise_utc(clock() if received is None else received))
    except (Blocked, bx.GateTerminal) as exc:
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
    void_reasons = Counter()
    for row in rows[1:]:
        kind = row["kind"]
        wake_counts[kind] += 1
        if kind == "void":
            void_reasons[row["reason"]] += 1
        if kind == "stop":
            stop = {k: row[k] for k in ("host", "http_status", "reason") if k in row}
        if kind == "pairs":
            pair_counts.update(row["pairs"].values())
            if row["status"] != "ok":
                pair_counts[row["status"]] += 1
        if kind != "wake":
            continue
        signal = row["bitcoin"]
        btc_counts[signal["status"]] += 1
        usable = sum(book["status"] == "ok" for books in row["books"].values() for book in books.values())
        if signal["status"] != "ok" or usable < len(st["coins"]):
            wake_counts["partial"] += 1
        if usable == 0:
            wake_counts["no_valid_books"] += 1
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
                    if (full and "midnight_utc" in groups and venue == VENUE
                            and size == str(max(st["sizes_usd"]))
                            and all(sides[s]["status"] == "ok" for s in SIDES)):
                        paired[coin] += 1
                    for side, item in sides.items():
                        side_counts[venue][item["status"]] += 1
                        if not full or item["status"] != "ok":
                            continue
                        value = Decimal(item["cost_bp"])
                        samples[venue, size, side].append(value)
                        for group in groups:
                            detailed[coin, venue, size, group, side].append(value)
    out = {"status": ("BLOCKED" if "http_status" in stop else "STOPPED") if stop else "STARTED",
           "wake_counts": dict(wake_counts), "scheduled_wakes": st["days"] * 24,
           "book_counts": book_counts, "side_counts": side_counts,
           "bitcoin_candle_counts": dict(btc_counts), "binance_pair_status_counts": dict(pair_counts),
           "stop": stop, "void_wake_reasons": dict(void_reasons),
           "void_book_slots": wake_counts["void"] * len(st["coins"])}
    if not full:
        return out
    out["costs"] = {v: {str(n): {s: stats(samples[v, str(n), s]) for s in SIDES}
                        for n in st["sizes_usd"]} for v in VENUES}
    out["table"] = [
        {"coin": c, "venue": v, "size_usd": n, "group": g,
         **{s: stats(detailed[c, v, str(n), g, s]) for s in SIDES}}
        for c in st["coins"] for v in VENUES for n in st["sizes_usd"] for g in GROUPS]
    decision = st["decision"]
    qualifying = []
    for coin in st["coins"]:
        side_values = [sorted(detailed[coin, VENUE, str(max(st["sizes_usd"])), "midnight_utc", s])
                       for s in SIDES]
        if paired[coin] >= decision["min_midnights"] and all(
                (v[(len(v)-1)//2] + v[len(v)//2])/2 <= Decimal(str(decision["max_cost_bp"])) for v in side_values):
            qualifying.append(coin)
    met = len(qualifying) >= decision["min_coins"]
    out["decision"] = {"met": met, "qualifying_coins": qualifying,
                       "paired_midnights_by_coin": {c: paired[c] for c in st["coins"]},
                       "main_cost_line_bp": decision["max_cost_bp"] if met else decision["fallback_cost_bp"]}
    return out


def read_gate(rows, h, now):
    need(now > deadline(parse(h["last_wake"]), h["settings"]), "last wake has not passed")
    require_go(234, "M134_READ", h["freeze"])
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
            finish_schedule(off, rows, h, now)
            out = summarize(rows, full=True)
            append(off, rows, kind="read", made_utc=iso(now), result_sha256=digest(enc(out).encode()))
            return out
        out = summarize(rows)
        if command == "publish":
            atomic_json(PUBLIC if official else off / "M134_log.json", out, public=official)
        return out


def finish_schedule(off, rows, h, now):
    """After the final window, project missed wakes locally without transport."""
    finished = {r["wake"] for r in rows if r["kind"] in ("wake", "void")}
    begun = {r["wake"] for r in rows if r["kind"] == "begin"}
    missing = "run_stopped" if any(r["kind"] == "stop" for r in rows) else "missed_wake"
    wake, last = parse(h["first_wake"]), parse(h["last_wake"])
    if not any(r["kind"] == "pairs" for r in rows):
        append(off, rows, kind="pairs", status="first_inventory_not_collected", pairs={})
    while wake <= last:
        stamp = iso(wake)
        if stamp not in finished:
            reason = "incomplete_attempt_not_retried" if stamp in begun else missing
            append(off, rows, kind="void", wake=stamp, made_utc=iso(now), reason=reason)
        wake += HOUR


def loop(off, pages, clock=now_utc, sleep=time.sleep, monotonic=time.monotonic):
    # A distinct lifetime lock keeps observers available between wakes. A one-shot
    # record shares the operation lock and is idempotent under the same schedule.
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
                record_locked(off, pages, clock, rows, sleep=sleep, monotonic=monotonic)
            now = clock()
            last = parse(h["last_wake"])
            close = deadline(last, h["settings"])
            if now > close:
                return
            nxt = max(parse(h["first_wake"]), hour(now) + timedelta(seconds=h["settings"]["offset_s"]))
            if nxt <= now:
                nxt += HOUR
            sleep(max(0, (min(nxt, close + timedelta(microseconds=1)) - now).total_seconds()))


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
            out = {"record": record, "loop": loop}[command](off, PublicPages(gate=TimedGate()))
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
