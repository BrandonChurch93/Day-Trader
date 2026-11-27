"""Invented venue replies, clocks, and private scratch storage only."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import io
import json
import os
from pathlib import Path

import pytest

import measure_134 as m
import venue_binance_us as bx

H = datetime(2027, 1, 1, tzinfo=timezone.utc)


class Clock:
    def __init__(self, hour=0, offset=480):
        self.utc = H + timedelta(hours=hour, seconds=offset)
        self.elapsed = 0.0

    def __call__(self):
        return self.utc

    def mono(self):
        return self.elapsed

    def sleep(self, seconds):
        self.utc += timedelta(seconds=seconds)
        self.elapsed += seconds


def statuses():
    return dict.fromkeys(bx.COINS, "TRADING")


def candle_rows(wake):
    end = bx.epoch_ms(bx.hour(wake))
    return [
        [stamp, px, px, px, px, "1", stamp + bx.HOUR_MS - 1, 0, 0, 0, 0, 0]
        for stamp, px in ((end - 2 * bx.HOUR_MS, "100"), (end - bx.HOUR_MS, "98"))
    ]


def depth():
    return {"bids": [["99.98", "55"]], "asks": [["100.02", "55"]]}


class Pages:
    def __init__(self, clock, *, busy=False, book_response=None):
        self.clock = clock
        self.busy = busy
        self.book_response = book_response or (lambda _: depth())
        self.calls = []

    def pairs(self):
        self.calls.append(("pairs", self.clock()))
        if self.busy:
            raise bx.Failure("shared_gate_busy")
        return statuses()

    def candles(self, wake):
        self.calls.append(("candles", self.clock()))
        if self.busy:
            raise bx.Failure("shared_gate_busy")
        return candle_rows(wake)

    def book(self, venue, coin):
        assert venue == bx.VENUE
        self.calls.append((coin, self.clock()))
        if self.busy:
            raise bx.Failure("shared_gate_busy")
        return self.book_response(coin)


@pytest.fixture
def lab(tmp_path, monkeypatch):
    p = tmp_path / "measurement"
    p.mkdir(mode=0o700)
    monkeypatch.setattr(bx, "private_roots", lambda: (tmp_path,))
    monkeypatch.setattr(m, "require_go", lambda *_a, **_kw: None)
    monkeypatch.setattr(bx, "check_start", lambda *_a, **_kw: pytest.fail("start forbidden"))
    st = m.frozen()
    assert st["settings"]["days"] * 24 == 720
    with bx.locked(p) as path:
        rows = []
        first = H + timedelta(seconds=st["settings"]["offset_s"])
        bx.write_anchor(path, bx.anchor_state(rows))
        bx.append(path, rows, kind="header", **st, freeze="<fixture>", venue_generation=0,
                  first_wake=bx.iso(first), last_wake=bx.iso(first + 719 * bx.HOUR))
    return p


def tick(p, src, clock, sleep=None):
    # Exactly the locked iteration used by the operational scheduler.
    with bx.locked(p) as path:
        return m.record_locked(path, src, clock, sleep=sleep or clock.sleep, monotonic=clock.mono)


def current(p):
    return bx.read_log(p)[-1]


def scratch_transport(lab, clock, opener, *, pace=None, raw_clock=None):
    gate = m.TimedGate(lab.parent / "scratch_gate" / "cooldown.json", clock=clock)
    assert gate.check_start() == 0
    pages = bx.PublicPages(gate=gate, opener=opener, clock=raw_clock or clock,
                          sleep=pace or clock.sleep, monotonic=clock.mono)
    return pages, gate


def reply(data, status=200):
    response = io.BytesIO(json.dumps(data).encode())
    response.status, response.headers = status, {}
    return response


def pair_metadata():
    return {"symbols": [{"baseAsset": coin, "quoteAsset": "USD", "symbol": coin + "USD", "status": "TRADING"}
                        for coin in bx.COINS]}


def test_inherits_133_without_reading_its_log():
    _, st = m.settings()
    assert st["sizes_usd"] == [25, 250] and st["coins"] == bx.COINS and len(st["coins"]) == 20
    assert (st["binance_fee"], st["binance_bnb_fee"]) == (2, 1)
    assert st["decision"] == {"max_cost_bp": 25, "min_coins": 15, "min_midnights": 25, "fallback_cost_bp": 75}
    assert (st["offset_s"], st["window_s"], st["busy_wait_s"]) == (480, 600, 20)
    assert m.DEFAULT_OFF.name == "measure_134"


def test_first_request_busy_is_counted_and_next_wake_runs(lab):
    # Start with a frozen inventory, reproducing the second wake of 133.
    clock = Clock()
    tick(lab, Pages(clock), clock)
    clock = Clock(hour=1)
    attempted, wired = [], []

    class Gate:
        def check_start(self, **_kw):
            pytest.fail("no separate wake gate check")

        @contextmanager
        def attempt(self, deadline, *, generation):
            assert generation == 0
            assert deadline <= H + bx.HOUR + timedelta(seconds=600)
            attempted.append(clock.elapsed)
            if clock.elapsed < 20:
                raise bx.Failure("shared_gate_busy")
            yield self

        def http_error(self, status, retry_after):
            assert status == 200

    class Wire:
        def open(self, req, **_kw):
            wired.append(req.full_url)
            response = io.BytesIO(json.dumps(depth()).encode())
            response.status, response.headers = 200, {}
            return response

    src = bx.PublicPages(gate=Gate(), opener=Wire(), clock=clock, sleep=clock.sleep, monotonic=clock.mono)
    tick(lab, src, clock)
    assert attempted[0] == 0 and attempted[1] > 0
    assert current(lab)["bitcoin"]["status"] == "shared_gate_busy"
    assert len(wired) == len(bx.COINS) and all(url.startswith("https://api.binance.us/api/v3/depth?") for url in wired)
    clock = Clock(hour=2)
    tick(lab, Pages(clock), clock)
    assert current(lab)["kind"] == "wake"
    assert m.summarize(bx.read_log(lab))["wake_counts"]["wake"] == 3


def test_all_window_busy_counts_all_books_lost(lab):
    clock = Clock()
    tick(lab, Pages(clock), clock)
    clock = Clock(1)
    p = Pages(clock, busy=True)
    tick(lab, p, clock)
    assert clock.elapsed == 120
    assert all(H + bx.HOUR + timedelta(seconds=480) <= sent < H + bx.HOUR + timedelta(seconds=600)
               for _, sent in p.calls)
    result = current(lab)
    assert len(result["books"][bx.VENUE]) == len(bx.COINS)
    assert {b["status"] for b in result["books"][bx.VENUE].values()} <= {"shared_gate_busy", "wake_window_elapsed"}
    assert m.summarize(bx.read_log(lab))["wake_counts"]["partial"] == 1


def test_real_gate_late_admission_does_not_cut_off_reply(lab):
    clock = Clock()
    observed = []

    class Wire:
        def open(self, req, **_kw):
            if "exchangeInfo" in req.full_url:
                sent = clock.elapsed
                clock.sleep(0.5)
                observed.append((sent, clock.elapsed))
                return reply(pair_metadata())
            if "klines" in req.full_url:
                return reply(candle_rows(H))
            return reply(depth())

    pages, gate = scratch_transport(lab, clock, Wire())
    lock = gate.cooldown_path.parent / ".gate.lock"
    with os.fdopen(bx.private_open(lock, os.O_RDWR), "rb") as fd:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        waited = []

        def permit(seconds):
            waited.append(seconds)
            clock.sleep(19.75)
            fcntl.flock(fd, fcntl.LOCK_UN)

        tick(lab, pages, clock, permit)
    assert waited == [0.25] and observed == [(19.75, 20.25)]
    rows = bx.read_log(lab)
    inventory = next(r for r in rows if r["kind"] == "pairs")
    assert inventory["status"] == "ok" and inventory["pairs"] == statuses()
    assert m.summarize(rows)["book_counts"][bx.VENUE]["ok"] == len(bx.COINS)


def test_accepted_clock_edge_discards_actual_path_reply(lab):
    clock = Clock()
    sent = []

    def transport_sample():
        if not sent:
            # PublicPages takes its own clock sample after the guarded gate
            # yields. Shift that UTC clock before the synthetic opener runs.
            clock.utc = H + timedelta(seconds=435)
        return clock()

    class Wire:
        def open(self, req, **_kw):
            sent.append(clock())
            return reply(pair_metadata())

    pages, gate = scratch_transport(lab, clock, Wire(), raw_clock=transport_sample)
    tick(lab, pages, clock)
    assert sent == [H + timedelta(seconds=435)]
    assert not (gate.cooldown_path.parent / bx.INFLIGHT).exists()
    rows = bx.read_log(lab)
    assert rows[-2]["status"] == "untrusted_utc_clock" and rows[-2]["pairs"] == {}
    assert rows[-1]["reason"] == "pair_inventory_unavailable"


def test_first_inventory_exhausted_is_never_replaced(lab):
    clock = Clock()
    tick(lab, Pages(clock, busy=True), clock)
    assert clock.elapsed == 20
    assert current(lab)["reason"] == "pair_inventory_unavailable"
    clock = Clock(1)
    next_pages = Pages(clock)
    tick(lab, next_pages, clock)
    assert [action for action, _ in next_pages.calls] == ["candles"]
    assert {b["status"] for b in current(lab)["books"][bx.VENUE].values()} == {"pair_inventory_unavailable"}


def test_rollback_between_clock_and_claim_sends_nothing(lab, monkeypatch):
    clock = Clock()
    src = Pages(clock)

    def rollback(*_args):
        clock.utc -= timedelta(seconds=45)

    monkeypatch.setattr(m, "require_go", rollback)
    tick(lab, src, clock)
    assert not src.calls
    assert current(lab)["reason"] == "untrusted_utc_clock"


def test_rollback_during_busy_wait_is_bounded(lab):
    clock = Clock()
    tick(lab, Pages(clock), clock)
    clock = Clock(1)
    src = Pages(clock, busy=True)

    def rollback(seconds):
        clock.sleep(seconds)
        clock.utc -= timedelta(seconds=10)

    tick(lab, src, clock, rollback)
    assert len(src.calls) == 1 and clock.elapsed < 20
    assert {b["status"] for b in current(lab)["books"][bx.VENUE].values()} == {"untrusted_utc_clock"}


@pytest.mark.parametrize("delay,status", [(0, "ok"), (120, "ok"), (120.000001, "late book")])
def test_window_book_receipt_is_inclusive_but_not_late(lab, delay, status):
    clock = Clock()

    def receive(coin):
        if coin == bx.COINS[0]:
            clock.sleep(delay)
        return depth()

    src = Pages(clock, book_response=receive)
    tick(lab, src, clock)
    result = current(lab)["books"][bx.VENUE][bx.COINS[0]]
    assert result["status"] == status
    if status == "ok":
        assert bx.parse(result["observed_utc"]) == H + timedelta(seconds=480 + delay)
    else:
        assert "sizes" not in result
    if delay >= 120:
        assert [act for act, _ in src.calls] == ["pairs", "candles", bx.COINS[0]]


def test_missed_and_interrupted_wakes_are_not_retried(lab):
    clock = Clock(offset=479)
    early = Pages(clock)
    assert tick(lab, early, clock) is None and not early.calls
    clock = Clock(hour=1)
    p = Pages(clock)
    tick(lab, p, clock)
    rows = bx.read_log(lab)
    assert [r.get("reason") for r in rows if r["kind"] == "void"] == ["missed_wake"]
    assert [a for a, _ in p.calls] == ["candles"]
    with bx.locked(lab) as path:
        bx.append(path, rows, kind="begin", wake=bx.iso(H + 2 * bx.HOUR + timedelta(seconds=480)))
    clock = Clock(hour=2)
    p = Pages(clock)
    tick(lab, p, clock)
    assert not p.calls and current(lab)["reason"] == "incomplete_attempt_not_retried"
    assert m.summarize(bx.read_log(lab))["void_book_slots"] == 40


def test_timeout_bad_reply_and_http_failure_are_book_losses(lab):
    clock = Clock()

    def invented(coin):
        if coin == bx.COINS[0]:
            raise TimeoutError()
        if coin == bx.COINS[1]:
            return {"bad": 0}
        if coin == bx.COINS[2]:
            raise bx.Failure("http_404")
        return depth()

    tick(lab, Pages(clock, book_response=invented), clock)
    out = current(lab)["books"][bx.VENUE]
    assert [out[c]["status"] for c in bx.COINS[:4]] == ["transport_failure", "bad book", "no_usd_book", "ok"]


def test_every_http_500_book_is_counted_and_wake_is_partial(lab):
    clock = Clock()
    tick(lab, Pages(clock), clock)
    clock = Clock(1)

    class Wire:
        def open(self, req, **_kw):
            if "klines" in req.full_url:
                return reply(candle_rows(H + bx.HOUR))
            assert "depth" in req.full_url
            return reply({}, 500)

    pages, _ = scratch_transport(lab, clock, Wire())
    tick(lab, pages, clock)
    status = m.summarize(bx.read_log(lab))
    assert status["book_counts"][bx.VENUE]["http_500"] == len(bx.COINS)
    assert status["wake_counts"]["wake"] == 2
    assert status["wake_counts"]["partial"] == status["wake_counts"]["no_valid_books"] == 1


@pytest.mark.parametrize("fault", [bx.GateStorage, bx.GateUncertain, bx.GateGeneration])
def test_terminal_fault_records_stop_and_never_resumes(lab, fault):
    clock = Clock()

    def fail(_coin):
        raise fault()

    with pytest.raises(bx.Refuse):
        tick(lab, Pages(clock, book_response=fail), clock)
    assert current(lab)["reason"] == fault.reason
    clock = Clock(1)
    p = Pages(clock)
    with pytest.raises(bx.Refuse, match="logger already stopped"):
        tick(lab, p, clock)
    assert not p.calls


def test_no_approval_no_pages(lab, monkeypatch):
    def refuse(*_args):
        raise bx.Refuse("unapproved")

    monkeypatch.setattr(m, "require_go", refuse)
    clock = Clock()
    p = Pages(clock)
    with pytest.raises(bx.Refuse, match="unapproved"):
        tick(lab, p, clock)
    assert not p.calls


def test_crash_between_append_and_anchor_fails_closed(lab, monkeypatch):
    def fail_anchor(*_args):
        raise OSError("simulated crash")

    monkeypatch.setattr(bx, "write_anchor", fail_anchor)
    clock = Clock()
    p = Pages(clock)
    with pytest.raises(OSError):
        tick(lab, p, clock)
    assert not p.calls
    with pytest.raises(bx.Refuse, match="anchor is behind"):
        tick(lab, p, clock)


def test_alive_and_public_have_counts_only(lab):
    clock = Clock()
    tick(lab, Pages(clock), clock)
    alive = m.report(lab, "alive")
    assert alive["book_counts"][bx.VENUE]["ok"] == len(bx.COINS)
    assert alive["scheduled_wakes"] == 720
    assert m.report(lab, "publish") == alive
    published = json.loads((lab / "M134_log.json").read_text())
    raw = json.dumps(published)
    for field in ("median", "p90", "costs", "decision", "AAVE", "99.98", "observed_utc"):
        assert field not in raw
    assert json.loads(Path(m.PUBLIC).read_text())["status"] == "NOT_STARTED"


def test_unchanged_midnight_decision_uses_paired_days(lab):
    clock = Clock()
    tick(lab, Pages(clock), clock)
    rows = bx.read_log(lab)
    sample = rows[-1]
    on_schedule = [sample | {"wake": bx.iso(clock.utc + timedelta(days=i))} for i in range(25)]
    assert m.summarize([rows[0], *on_schedule[:-1]], full=True)["decision"]["main_cost_line_bp"] == 75
    result = m.summarize([rows[0], *on_schedule], full=True)["decision"]
    assert result["main_cost_line_bp"] == 25
    assert set(result["qualifying_coins"]) == set(bx.COINS)
    assert set(result["paired_midnights_by_coin"].values()) == {25}


def test_read_preflight_is_separate_once_and_after_window(lab, monkeypatch):
    rows = bx.read_log(lab)
    h = rows[0]
    seen = []
    monkeypatch.setattr(m, "require_go", lambda *a: seen.append(a))
    limit = m.deadline(bx.parse(h["last_wake"]), h["settings"])
    with pytest.raises(bx.Refuse, match="last wake"):
        m.read_gate(rows, h, limit)
    m.read_gate(rows, h, limit + timedelta(microseconds=1))
    assert seen == [(234, "M134_READ", "<fixture>")]
    with pytest.raises(bx.Refuse, match="already used"):
        m.read_gate(rows + [{"kind": "read"}], h, limit + timedelta(microseconds=1))
