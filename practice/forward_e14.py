"""Ledger 233. Pretend-money washout observation, never orders or account data."""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import timedelta
from decimal import Decimal
import fcntl
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import yaml

import venue_binance_us as bx

ROOT = bx.ROOT
OFF = Path("/home/user/workspace/rig/data/forward_e14")
PUBLIC = ROOT / "practice/forward/E14_log.json"
CARD = "practice/traders/E14_washout_rebound_binance_us.md"
SHARED = "practice/venue_binance_us.py"
PINNED = (CARD, "practice/forward_e14.py", SHARED, "config/thresholds.yaml")
ROW = 233
PRIMARY, ALT, SMALL, LATE = "primary", "alternate", "small", "delayed"
ARMS = (PRIMARY, ALT, SMALL, LATE)
GATE_BLOB = "ccd1e045c705fbc4bfa2c221bed0015ac2ce8db0"
CLOCK_TOLERANCE_S = 0.25


def literal_git(*args, binary=False):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_NO_REPLACE_OBJECTS="1")
    try:
        return subprocess.check_output(("git", "--no-replace-objects", "-c", "core.fsmonitor=false", *args),
                                       cwd=ROOT, env=env, text=not binary, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        raise bx.Refuse("cannot read literal committed approval or build") from None


def require_go(row, key, commit, *, generation=0):
    bx.need(re.fullmatch(r"[a-f0-9]{40}", commit), "invalid frozen build")
    body = literal_git("show", f"{bx.APPROVAL_REF}:{bx.LEDGER}")
    rows = re.findall(rf"^\|[ \t]*{row}[ \t]*\|[^\r\n]*$", body, re.M)
    bx.need(len(rows) == 1, f"committed ledger row {row} missing or repeated")

    def exact(name, value):
        marker = rf"(?<![A-Za-z0-9_]){name}"
        assignments = re.findall(marker + r"[ \t]*=", rows[0])
        good = re.findall(marker + rf"={value}(?=[\s`|]|$)", rows[0])
        bx.need(len(assignments) == len(good) == 1,
                f"{name} missing, repeated or mismatched on committed ledger row {row}")

    exact(key, commit)
    if generation:
        exact(key + "_GENERATION", str(generation))


def checked_build():
    tracks = literal_git("ls-files", "-v", "-z", "--", *PINNED).split("\0")
    bx.need({r[2:] for r in tracks if r.startswith("H ")} == set(PINNED)
            and not literal_git("status", "--porcelain", "--untracked-files=no", "--", *PINNED),
            "frozen inputs not tracked and clean")
    commit = literal_git("rev-parse", "--verify", "HEAD^{commit}").strip()
    for path in PINNED:
        bx.need(literal_git("show", f"{commit}:{path}", binary=True) == (ROOT / path).read_bytes(),
                "frozen input differs from literal build")
    bx.need(literal_git("rev-parse", f"{commit}:{SHARED}").strip() == GATE_BLOB,
            "shared gate differs from audited version")
    return commit


class WakeClock:
    """Fail closed on clock steps; absolute UTC still requires a trusted host clock."""

    def __init__(self, utc, monotonic):
        self.utc, self.monotonic = utc, monotonic
        self.first = self.previous = None
        self.failed = False

    def sample(self):
        utc, elapsed = self.utc(), self.monotonic()
        if (not hasattr(utc, "utcoffset") or utc.utcoffset() != timedelta(0)
                or not math.isfinite(elapsed)):
            self.failed = True
        if not self.failed and self.first is not None:
            t0, m0 = self.first
            last_t, last_m = self.previous
            if (utc < last_t or elapsed < last_m
                    or abs((utc - t0).total_seconds() - (elapsed - m0)) > CLOCK_TOLERANCE_S):
                self.failed = True
        if self.failed:
            raise bx.Failure("untrusted_utc_clock")
        self.first = self.first or (utc, elapsed)
        self.previous = utc, elapsed
        return self.previous


class TimedGate(bx.Gate):
    """Keep the audited lock and recheck E14's clock immediately before wire I/O."""
    before_send = None

    @contextmanager
    def mutex(self, deadline=None):
        # While waiting unsent, enforce the elapsed fence even if UTC drifts.
        # Restore actual UTC before any shared cooldown or generation policy.
        venue_utc = self.clock
        if self.before_send is not None:
            self.clock = lambda: self.before_send()[0]
        try:
            with super().mutex(deadline) as directory:
                self.clock = venue_utc
                yield directory
        finally:
            self.clock = venue_utc

    @contextmanager
    def attempt(self, deadline=None, *, generation):
        with super().attempt(deadline, generation=generation):
            try:
                if self.before_send is not None:
                    self.before_send()
            except bx.Failure:
                self.cancel_unsent()
                raise
            yield self


def settings():
    raw = yaml.safe_load((ROOT / "config/thresholds.yaml").read_text())
    cfg = raw["forward_e14"]["value"].copy()
    plan = raw[cfg["rule_ref"]]["value"]
    execution = raw[cfg["size_ref"]]["value"]
    marks = raw[cfg["mark_ref"]]["value"]
    fees = raw[cfg["fee_ref"]]["value"]
    cfg.update(drops=plan["drops"], hold_hours=plan["hold_hours"]["primary"],
               sizes=execution["sizes_usd"], t_mark=marks["t_mark"], trim_best=marks["trim_best"],
               fee_bp=fees["default_taker_bp"], gate=raw["binance_us_gate"]["value"])
    return cfg


def frozen(cfg):
    return {"config": cfg, "source_sha256": {
        p: bx.digest((ROOT / p).read_bytes()) for p in PINNED if p != "config/thresholds.yaml"}}


def bound(wake, seconds):
    return wake + timedelta(seconds=seconds)


def header(rows, cfg):
    bx.need(rows and rows[0]["kind"] == "header", "not started")
    bx.need(rows[0]["frozen"] == frozen(cfg), "frozen inputs changed")
    return rows[0]


def start_gate(commit, gate):
    require_go(ROW, "E14_START", commit)
    generation = bx.check_start(gate)
    if generation:
        require_go(ROW, "E14_START", commit, generation=generation)
    return generation


def start(now, off=OFF, *, gate=None):
    cfg = settings()
    commit = checked_build()
    generation = start_gate(commit, gate)
    first = bx.hour(now)
    if now >= bound(first, cfg["wake_offset_s"]):
        first += bx.HOUR
    bx.need(first <= bx.parse(cfg["last_wake_utc"]), "first wake outside dates")
    with bx.locked(off, create=True) as path:
        rows = bx.read_log(path)
        bx.need(not rows, "already started")
        bx.write_anchor(path, bx.anchor_state(rows))
        bx.append(path, rows, kind="header", freeze=commit, venue_generation=generation,
                  first=bx.iso(first), frozen=frozen(cfg))
    return {"first_wake": bx.iso(first), "freeze": commit, "venue_generation": generation}


def request(pages, fetch, until, clock, sleep, busy_s, *, not_before=None, stamped=False,
            timing=None):
    """Only a request that the shared gate did not send may retry for gate-busy."""
    timing = timing or WakeClock(clock, time.monotonic)
    began, began_m = timing.sample()
    busy = False
    gate = getattr(pages, "gate", None)

    def limits(*, received=False):
        now, mono = timing.sample()
        if not_before is not None and now < not_before:
            raise bx.Failure("wake_window_not_open")
        if now > until or (not received and now == until):
            raise bx.Failure("late book" if received else "shared_gate_busy" if busy else "wake_window_elapsed")
        left = busy_s - (mono - began_m)
        if busy and (left < 0 or (not received and left == 0)):
            raise bx.Failure("shared_gate_busy")
        return now, min(until, began + timedelta(seconds=busy_s), bound(now, left)) if busy else until

    try:
        while True:
            attempt_at, active_until = limits()
            if attempt_at >= active_until:
                raise bx.Failure("shared_gate_busy" if busy else "wake_window_elapsed")
            pages.deadline = active_until
            if isinstance(gate, TimedGate):
                gate.before_send = limits
            try:
                data = fetch()
            except bx.Failure as exc:
                if exc.reason != "shared_gate_busy":
                    if busy and exc.reason == "wake_window_elapsed" and clock() >= active_until:
                        raise bx.Failure("shared_gate_busy") from None
                    raise
                busy = True
                now, retry_until = limits()
                left = (retry_until - now).total_seconds()
                if left > 0:
                    sleep(min(0.25, left))
            else:
                arrived, receive_until = limits(received=True)
                if arrived > min(active_until, receive_until):
                    raise bx.Failure("shared_gate_busy")
                return (data, arrived) if stamped else data
    finally:
        if isinstance(gate, TimedGate):
            gate.before_send = None
        pages.deadline = until


def private_reason(exc):
    return exc.reason if isinstance(exc, bx.Failure) else "invalid_or_unavailable_page"


def freeze_roster(fetch, pages, coins, minimum):
    states = fetch(pages.pairs)
    if not isinstance(states, dict) or any(c not in states or not isinstance(states[c], str) for c in coins):
        raise bx.Failure("invalid_first_inventory")
    roster = [c for c in coins if states[c] != "NO_USD_PAIR"]
    if len(roster) < minimum:
        raise bx.Failure("too_few_usd_pairs")
    return roster


def candles(fetch, pages, wake, roster):
    closes, errors = {}, {}
    for coin in roster:
        try:
            rows = fetch(lambda: pages.klines(coin, wake, 2))
            pair = [v[3] for _, v in sorted(bx.closed_klines(rows, wake, 2).items())]
            if any(not sane_price(p) for p in pair):
                raise bx.Failure("invalid_candle_price")
            closes[coin] = tuple(map(str, pair))
        except bx.Blocked:
            raise
        except (bx.Failure, OSError, ValueError, TypeError, KeyError, ArithmeticError) as exc:
            errors[coin] = private_reason(exc)
    return closes, errors


def sane_price(px):
    # Reject out-of-scale numerical payloads before building exact ratios.
    return -50 <= px.adjusted() <= 50 and len(px.as_tuple().digits) <= 128


def choose(closes, roster, threshold):
    """Compare plain adjacent-close declines exactly, with stable roster ties."""
    best, strength = None, None
    cut = Fraction(str(threshold))
    for coin in roster:
        previous, last = (Fraction(v) for v in closes[coin])
        drop = (previous - last) / previous
        if drop >= cut and (strength is None or drop > strength):
            best, strength = coin, drop
    return best


def book(fetch, pages, coin, clock):
    try:
        raw, arrived = fetch(lambda: pages.book(bx.VENUE, coin), stamped=True)
        received = bx.precise_utc(arrived)
        detail = bx.ticket(raw, bx.VENUE, (), 0)
        if detail["status"] == "ok":
            if not all(sane_price(Decimal(x)) for side in ("bids", "asks") for level in raw[side] for x in level):
                raise bx.Failure("invalid_book_numbers")
            detail.update(bids=raw["bids"], asks=raw["asks"])
        return detail | {"received": received}
    except bx.Blocked:
        raise
    except (bx.Failure, OSError, ValueError, TypeError, KeyError, ArithmeticError) as exc:
        return {"status": private_reason(exc), "received": bx.precise_utc(clock())}


def walk(levels, amount, *, buy):
    """E12 walking convention: quote dollars to buy, exact filled base to sell."""
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


def enter(coin, wake, due, first, dollars, *, parent=None):
    out = {"coin": coin, "wake": bx.iso(wake), "due": due, "size": dollars, "book": first}
    if parent is not None:
        out["parent"] = parent
    if first["status"] != "ok":
        return out | {"status": first["status"]}
    try:
        bought = walk(first["asks"], dollars, buy=True)
        if bought is None:
            return out | {"status": "entry too thin"}
        cost = (bought[1] / bought[0] / Decimal(first["midpoint"]) - 1) * 10_000
        if not math.isfinite(float(cost)):
            raise ArithmeticError("cost cannot be represented")
    except ArithmeticError:
        return out | {"status": "invalid_book_arithmetic"}
    return out | {"status": "ok", "base": str(bought[0]), "entry_cost_bp": str(cost)}


def leave(entry, exit_book, fee_bp):
    out = {"coin": entry["coin"], "entry_wake": entry["wake"]}
    if exit_book["status"] != "ok":
        return out | {"status": exit_book["status"]}
    try:
        sold = walk(exit_book["bids"], entry["base"], buy=False)
        if sold is None:
            return out | {"status": "exit too thin"}
        size = Decimal(entry["size"])
        fee = Decimal(fee_bp) / 10_000
        net = float((sold[1] * (1 - fee) - size * (1 + fee)) / size)
        if not math.isfinite(net):
            raise ArithmeticError("return cannot be represented")
        return out | {"status": "ok", "net": net}
    except ArithmeticError:
        return out | {"status": "invalid_book_arithmetic"}


def apply_event(idx, r):
    kind = r["kind"]
    if kind == "claim":
        idx["claims"].add(r["wake"])
    if kind not in ("wake", "void"):
        return
    stamp = r["wake"]
    idx["visits"].add(stamp)
    for arm, item in r["exits"].items():
        idx["closed"][arm].append(item)
        if arm in (PRIMARY, ALT):
            idx["open"].pop(arm)
            if arm == PRIMARY:
                idx["delayed"].pop(item["entry_wake"], None)
        elif arm == SMALL:
            idx["small"].pop(stamp)
    for arm, item in r["entries"].items():
        if arm == PRIMARY and item["book"]["status"] == "ok":
            idx["books"].append(item)
        if arm == LATE:
            idx["delayed"][item["parent"]] = item
        elif item["status"] == "ok":
            if arm == SMALL:
                idx["small"][item["due"]] = item
            else:
                idx["open"][arm] = item


def state(rows):
    idx = {"open": {}, "small": {}, "delayed": {}, "claims": set(), "visits": set(),
           "books": [], "closed": defaultdict(list)}
    for r in rows:
        apply_event(idx, r)
    return idx


def due_exits(idx, stamp):
    due = {a: e for a, e in idx["open"].items() if e["due"] == stamp}
    if stamp in idx["small"]:
        due[SMALL] = idx["small"][stamp]
    if PRIMARY in due:
        delay = idx["delayed"].get(due[PRIMARY]["wake"])
        if delay is not None and delay["status"] == "ok":
            due[LATE] = delay
    return due


def due_delayed(idx, wake):
    entry = idx["open"].get(PRIMARY)
    return entry if entry and bx.parse(entry["wake"]) + bx.HOUR == wake else None


def void_wake(path, rows, wake, reason, ix):
    stamp = bx.iso(wake)
    exits = {a: {"status": reason, "entry_wake": e["wake"]} for a, e in due_exits(ix, stamp).items()}
    entries = {}
    late = due_delayed(ix, wake)
    if late:
        entries[LATE] = enter(late["coin"], wake, late["due"], {"status": reason}, late["size"], parent=late["wake"])
    bx.append(path, rows, kind="void", wake=stamp, reason=reason, entries=entries, exits=exits)
    apply_event(ix, rows[-1])
    return rows[-1]


def capture(path, rows, pages, wake, roster, ix, cfg, clock, sleep, *, timing=None):
    stamp = bx.iso(wake)
    opens_at = bound(wake, cfg["wake_offset_s"])
    until = bound(wake, cfg["book_cutoff_s"])
    timing = timing or WakeClock(clock, time.monotonic)
    terminal = None

    def fetch(fn, *, stamped=False):
        nonlocal terminal
        if terminal is not None:
            raise bx.Failure("gate_stopped")
        try:
            return request(pages, fn, until, clock, sleep, cfg["busy_wait_s"],
                           not_before=opens_at, stamped=stamped, timing=timing)
        except (bx.Blocked, bx.GateTerminal) as exc:
            terminal = exc
            raise bx.Failure("gate_stopped") from None

    exit_books, entry_books, exits, entries = {}, {}, {}, {}

    def fresh(cache, coin):
        if coin not in cache:
            cache[coin] = book(fetch, pages, coin, clock)
        return cache[coin]

    due = due_exits(ix, stamp)
    def close(arm):
        e = due.get(arm)
        if e is not None:
            exits[arm] = leave(e, fresh(exit_books, e["coin"]), cfg["fee_bp"])

    for arm in (PRIMARY, ALT, SMALL, LATE):
        close(arm)
    hit = (sum(e["status"] == "ok" for e in ix["closed"][PRIMARY])
           + (exits.get(PRIMARY, {}).get("status") == "ok") >= cfg["judging_count"])
    last = bx.parse(cfg["last_wake_utc"])
    exit_when = wake + cfg["hold_hours"] * bx.HOUR
    free = [arm for arm in (PRIMARY, ALT) if arm not in ix["open"] or arm in exits]
    closes, errors, decisions = {}, {}, {}
    if not hit and free and exit_when <= last:
        closes, errors = candles(fetch, pages, wake, roster)
        if not errors:
            for arm in free:
                coin = choose(closes, roster, cfg["drops"][arm])
                if coin is not None:
                    decisions[arm] = coin
    # Neither a due exit snapshot nor a later quote can act as this entry book.
    if PRIMARY in decisions:
        coin = decisions[PRIMARY]
        first = fresh(entry_books, coin)
        due_stamp = bx.iso(exit_when)
        entries[PRIMARY] = enter(coin, wake, due_stamp, first, cfg["sizes"]["judged"])
        entries[SMALL] = enter(coin, wake, due_stamp, first, cfg["sizes"]["shown"])
    if ALT in decisions:
        coin = decisions[ALT]
        first = fresh(entry_books, coin)
        entries[ALT] = enter(coin, wake, bx.iso(exit_when), first, cfg["sizes"]["judged"])
    delay = due_delayed(ix, wake)
    if delay and not hit:
        first = fresh(entry_books, delay["coin"])
        entries[LATE] = enter(delay["coin"], wake, delay["due"], first, delay["size"], parent=delay["wake"])
    bx.append(path, rows, kind="wake", wake=stamp, closes=closes, candle_errors=errors, decisions=decisions,
              entries=entries, exits=exits, exit_books=exit_books, judging_point=hit,
              busy_arms=[a for a in (PRIMARY, ALT) if a not in free])
    if terminal is not None:
        return stop(path, rows, terminal.reason, clock, wake, getattr(terminal, "status", None))
    return rows[-1]


def stop(path, rows, reason, clock, wake=None, status=None):
    fields = {"reason": reason, "made_utc": bx.precise_utc(clock())}
    if status is not None:
        fields.update(host=bx.HOST, http_status=status)
    if wake is not None:
        fields["wake"] = bx.iso(wake)
    bx.append(path, rows, kind="stop", **fields)
    return rows[-1]


def record(pages=None, off=OFF, clock=bx.now_utc, sleep=time.sleep, monotonic=time.monotonic):
    cfg = settings()
    with bx.locked(off) as path:
        rows = bx.read_log(path, recover=True, clock=clock)
        h = header(rows, cfg)
        stopped = any(r["kind"] == "stop" for r in rows)
        scored = any(r["kind"] == "score" for r in rows)
        ix = state(rows)
        hit = sum(e["status"] == "ok" for e in ix["closed"][PRIMARY]) >= cfg["judging_count"]
        if hit and PRIMARY not in ix["open"]:
            return {"kind": "judging point"}
        first, last = bx.parse(h["first"]), bx.parse(cfg["last_wake_utc"])
        wake = bx.parse(max(ix["visits"])) + bx.HOUR if ix["visits"] else first
        roster = next((r["coins"] for r in rows if r["kind"] == "roster"), None)
        timing = WakeClock(clock, monotonic)
        new_stop = None
        while wake <= last:
            now, _ = timing.sample()
            hour = bx.hour(now)
            if wake > hour:
                break
            stamp = bx.iso(wake)
            opens_at = bound(wake, cfg["wake_offset_s"])
            until = bound(wake, cfg["book_cutoff_s"])
            started = stamp in ix["claims"]
            if stopped or hit or scored:
                if now < until:
                    break
                reason = "run_stopped" if stopped else "judging_point_reconciliation"
                void_wake(path, rows, wake, reason, ix)
                wake += bx.HOUR
                continue
            if roster is None and (wake != first or started or now >= until):
                new_stop = stop(path, rows, "first_wake_roster_unavailable", clock, first)
                void_wake(path, rows, first, "first_wake_roster_unavailable", ix)
                stopped = True
                wake += bx.HOUR
                continue
            if started or now >= until:
                void_wake(path, rows, wake, "interrupted_wake" if started else "missed_wake", ix)
            elif opens_at <= now < until:
                require_go(ROW, "E14_START", h["freeze"])
                claim_time, _ = timing.sample()
                if claim_time >= until:
                    void_wake(path, rows, wake, "missed_wake", ix)
                    wake += bx.HOUR
                    continue
                bx.need(claim_time >= opens_at, "wake window not open")
                pages = pages if pages is not None else bx.PublicPages(
                    clock=clock, sleep=sleep, monotonic=monotonic, gate=TimedGate(clock=clock))
                if isinstance(pages, bx.PublicPages):
                    generation = h.get("venue_generation")
                    bx.need(type(generation) is int and generation >= 0, "invalid shared gate generation")
                    # The shared per-request attempt verifies generation and stop under its own mutex.
                    pages.generation = generation
                bx.append(path, rows, kind="claim", wake=stamp, made_utc=bx.precise_utc(claim_time))
                try:
                    if roster is None:
                        try:
                            fetch = lambda fn: request(pages, fn, until, clock, sleep, cfg["busy_wait_s"],
                                                       not_before=opens_at, timing=timing)
                            roster = freeze_roster(fetch, pages, cfg["coins"], cfg["min_pairs"])
                        except bx.Blocked:
                            raise
                        except (bx.Failure, OSError, ValueError, TypeError, KeyError) as exc:
                            event = stop(path, rows, private_reason(exc), clock, wake)
                            void_wake(path, rows, wake, "first_wake_roster_unavailable", ix)
                            return event
                        bx.append(path, rows, kind="roster", wake=stamp, coins=roster)
                    return capture(path, rows, pages, wake, roster, ix, cfg, clock, sleep, timing=timing)
                except (bx.Blocked, bx.GateTerminal) as exc:
                    event = stop(path, rows, exc.reason, clock, wake, getattr(exc, "status", None))
                    void_wake(path, rows, wake, "gate_stopped", ix)
                    return event
            else:
                break
            wake += bx.HOUR
        return new_stop or {"kind": "stopped" if stopped else "nothing due"}


def summary(rows):
    ix = state(rows)
    visits = [r for r in rows if r["kind"] in ("wake", "void")]
    voids = {a: Counter() for a in ARMS}
    entries, exits = Counter(), Counter()
    for r in visits:
        for side, counts in (("entries", entries), ("exits", exits)):
            for arm, e in r[side].items():
                if e["status"] == "ok":
                    counts[arm] += 1
                else:
                    voids[arm][e["status"]] += 1
    stopped = next((r for r in rows if r["kind"] == "stop"), None)
    cfg = rows[0]["frozen"]["config"] if rows else None
    at_cut = cfg and PRIMARY not in ix["open"] and (
        exits[PRIMARY] >= cfg["judging_count"] or cfg["last_wake_utc"] in ix["visits"])
    return {"card": "E14", "status": "STOPPED" if stopped else "STARTED" if rows else "NOT_STARTED",
            "at_judging_point": bool(at_cut),
            "stop": {k: stopped[k] for k in ("reason", "host", "http_status") if k in stopped} if stopped else None,
            "frozen_pairs": next((len(r["coins"]) for r in rows if r["kind"] == "roster"), None),
            "wake_counts": dict(Counter(r["kind"] for r in visits)),
            "claimed_unresolved_wakes": len(ix["claims"] - ix["visits"]),
            "ranking_void_wakes": sum(bool(r.get("candle_errors")) for r in visits),
            "wake_void_reasons": dict(Counter(r["reason"] for r in visits if r["kind"] == "void")),
            "candle_error_counts": dict(Counter(err for r in visits for err in r.get("candle_errors", {}).values())),
            "busy_wakes_by_arm": dict(Counter(a for r in visits for a in r.get("busy_arms", ()))),
            "first_primary_books": len(ix["books"]), "valid_entries": dict(entries),
            "valid_closes": dict(exits), "void_tickets": voids}


def alive(off=OFF):
    off = Path(off)
    if not off.exists() and not off.is_symlink():
        return summary([])
    with bx.locked(off, write=False) as path:
        rows = bx.read_log(path)
        header(rows, settings())
        return summary(rows)


def publish(off=OFF, target=PUBLIC):
    out = alive(off)
    bx.atomic_json(target, out, public=target == PUBLIC)
    return out


def cluster_t(values, days):
    """E12 cluster formula, with a finite-sample correction by UTC entry day."""
    groups = Counter(days)
    scale = max(map(abs, values), default=0)
    if len(groups) < 2 or not scale or not math.isfinite(scale):
        return None
    scaled = [v / scale for v in values]
    mean = math.fsum(scaled) / len(scaled)
    residuals = defaultdict(list)
    for day, value in zip(days, scaled):
        residuals[day].append(value - mean)
    sums = [math.fsum(group) for group in residuals.values()]
    if max(map(abs, sums)) <= sys.float_info.epsilon * max(groups.values()):
        return None
    se = math.sqrt(len(groups) / (len(groups) - 1) * math.fsum(x*x for x in sums)) / len(scaled)
    return mean / se


def line(closes):
    values = [r["net"] for r in closes if r["status"] == "ok"]
    return {"trades": len(values), "net_mean": math.fsum(values) / len(values) if values else None}


def judge(closes, cfg):
    valid = [r for r in closes if r["status"] == "ok"][:cfg["judging_count"]]
    if len(valid) < cfg["judging_floor"]:
        return {"verdict": "too few to judge", "trades": len(valid)}
    x = [r["net"] for r in valid]
    trimmed = sorted(x)[:-cfg["trim_best"]]
    days = [bx.parse(r["entry_wake"]).date() for r in valid]
    mean, trim = math.fsum(x) / len(x), math.fsum(trimmed) / len(trimmed)
    t = cluster_t(x, days)
    marks = {"positive_mean": mean > 0, "positive_without_best": trim > 0,
             "cluster_t": t is not None and t >= cfg["t_mark"]}
    return {"verdict": "pass" if all(marks.values()) else "did not pass", "trades": len(x),
            "net_mean": mean, "net_mean_without_best": trim, "entry_days": len(set(days)),
            "entry_day_t": t, "marks": marks}


def costs(first_books, count):
    sample = first_books[:count]
    values = sorted(Decimal(e["entry_cost_bp"]) for e in sample if e["status"] == "ok")
    n = len(values)
    return {"first_books": len(sample), "full_walks": n, "missing_walks": len(sample) - n,
            "mean_bp": float(sum(values) / n) if n else None,
            "median_bp": float((values[(n - 1) // 2] + values[n // 2]) / 2) if n else None,
            "p90_bp": float(values[(9 * n + 9) // 10 - 1]) if n else None}


def read_gate(rows, h, ix, cfg, mode, now):
    bx.need(not any(r["kind"] == mode for r in rows), mode + " already read")
    if mode == "cost":
        bx.need(len(ix["books"]) >= cfg["cost_books"], "not enough primary first books")
        require_go(ROW, "E14_COST", h["freeze"])
    elif mode == "score":
        n = sum(r["status"] == "ok" for r in ix["closed"][PRIMARY])
        close = bound(bx.parse(cfg["last_wake_utc"]), cfg["book_cutoff_s"])
        bx.need(n >= cfg["judging_count"] or now > close, "judging point has not arrived")
        bx.need(PRIMARY not in ix["open"], "judged ticket is unresolved")
        bx.need(n >= cfg["judging_count"] or cfg["last_wake_utc"] in ix["visits"],
                "final wake is unreconciled")
        require_go(ROW, "E14_SCORE", h["freeze"])
    else:
        raise bx.Refuse("unknown read mode")


def readout(now, mode, off=OFF):
    cfg = settings()
    with bx.locked(off) as path:
        rows = bx.read_log(path)
        h = header(rows, cfg)
        ix = state(rows)
        read_gate(rows, h, ix, cfg, mode, now)
        if mode == "cost":
            out = costs(ix["books"], cfg["cost_books"])
        else:
            out = {"judged": judge(ix["closed"][PRIMARY], cfg),
                   "shown": {a: line(ix["closed"][a]) for a in (ALT, SMALL, LATE)}}
        return commit_readout(path, rows, mode, now, out)


def commit_readout(path, rows, mode, now, out):
    bx.append(path, rows, kind=mode, made_utc=bx.precise_utc(now), result_sha256=bx.digest(bx.enc(out).encode()))
    return out


def loop(off=OFF, clock=bx.now_utc, sleep=time.sleep, monotonic=time.monotonic):
    cfg = settings()
    pages = bx.PublicPages(clock=clock, sleep=sleep, monotonic=monotonic, gate=TimedGate(clock=clock))
    path = bx.checked_dir(Path(off))
    fd = bx.private_open(path / ".loop.lock", os.O_RDWR | os.O_CREAT)
    final = bound(bx.parse(cfg["last_wake_utc"]), cfg["book_cutoff_s"])
    with os.fdopen(fd, "rb") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise bx.Refuse("a loop is already running") from None
        while True:
            out = record(pages, path, clock, sleep, monotonic)
            now = clock()
            if out["kind"] in ("stop", "stopped", "judging point") or now >= final:
                return {"status": out["kind"]}
            if out.get("judging_point"):
                return {"status": "judging point"}
            nxt = bound(bx.hour(now), cfg["wake_offset_s"])
            if nxt <= now:
                nxt += bx.HOUR
            sleep(max(0, (min(nxt, final) - now).total_seconds()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "start", "record", "loop", "alive", "publish", "cost", "score"))
    cmd = parser.parse_args().command
    os.umask(0o077)
    now = bx.now_utc()
    try:
        if cmd == "plan":
            out = frozen(settings())
        elif cmd == "start":
            out = start(now)
        elif cmd == "record":
            row = record()
            out = {k: row[k] for k in ("kind", "wake", "reason", "host", "http_status") if k in row}
        elif cmd in ("score", "cost"):
            out = readout(now, cmd)
        else:
            out = {"loop": loop, "alive": alive, "publish": publish}[cmd]()
        print(json.dumps(out, sort_keys=True, allow_nan=False))
    except (bx.Refuse, bx.Failure, OSError) as exc:
        reason = exc.reason if isinstance(exc, bx.Failure) else type(exc).__name__ if isinstance(exc, OSError) else str(exc)
        print("REFUSED " + reason, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
