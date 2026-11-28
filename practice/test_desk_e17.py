"""Card E17 on made-up candles, made-up books, a fake clock and a fake model. No venue, no model, no live gate."""
import asyncio
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack, contextmanager
from pathlib import Path
from threading import Barrier, Event, get_ident
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

import pytest

import desk_e17 as d
import forward_e14 as e14
import scout_runner_e17 as runner
import scout_spool_e17 as spool
import venue_binance_us as bx

SMALL = "gpt5_mini"
BUILD = "a" * 40
T0 = datetime(2027, 1, 4, 0, 0, tzinfo=timezone.utc)   # a Monday, 00:00 UTC: a card S scan hour


class Clock:
    def __init__(self, t):
        self.t, self.m = t, 0.0

    def __call__(self):
        return self.t

    def sleep(self, s):
        self.t += timedelta(seconds=s)
        self.m += s

    def mono(self):
        return self.m


def depth(ask="100.05", bid="99.95", size="1000"):
    return {"asks": [[ask, size], [str(float(ask) + 1), size]], "bids": [[bid, size], [str(float(bid) - 1), size]]}


class Pages:
    """Fake public pages. Each call takes 0.1 s of fake time and marks the fake gate as held while it runs."""
    def __init__(self, clock, *, last=None, prev=None, books=None, status=None, future=False, fail=None):
        self.clock, self.calls, self.held = clock, [], False
        self.last, self.prev = last or {}, prev or {}
        self.books = books or {}
        self.status = status or {c: "TRADING" for c in bx.COINS}
        self.future, self.fail = future, fail or {}

    def _hit(self, kind, coin=None):
        self.held = True
        self.calls.append((kind, coin, self.clock()))
        self.clock.sleep(0.1)
        self.held = False
        f = self.fail.get((kind, coin)) or self.fail.get((kind, None))
        if f is not None:
            raise f() if callable(f) else f

    def pairs(self):
        self._hit("pairs")
        return dict(self.status)

    def klines(self, coin, wake, hours):
        self._hit("klines", coin)
        end = bx.epoch_ms(bx.hour(wake))
        out = []
        for i in range(hours):
            stamp = end - (hours - i) * bx.HOUR_MS
            c = "100"
            if i == hours - 2 and coin in self.prev:
                c = self.prev[coin]
            if i == hours - 1:
                c = self.last.get(coin, "100")
            if i == hours - 3 and coin in self.prev:
                c = "100"
            hi = str(max(float(c), 100.0) + 1)
            lo = str(min(float(c), 100.0) - 1)
            out.append([stamp, "100", hi, lo, c, "10", stamp + bx.HOUR_MS - 1, "0", 0, "0", "0", "0"])
        if self.future:
            out.append([end, "100", "99999", "1", "99999", "10", end + bx.HOUR_MS - 1, "0", 0, "0", "0", "0"])
        return out

    def book(self, venue, coin):
        self._hit("book", coin)
        return self.books.get(coin, depth())


class Scout:
    def __init__(self, pages, clock, picks=None, error=None, seconds=5.0):
        self.pages, self.clock, self.picks, self.error, self.seconds = pages, clock, picks or {}, error, seconds
        self.seen = []

    async def __call__(self, model, card, pkt, max_tokens):
        assert not self.pages.held, "model call while a request holds the gate"
        self.seen.append((model, card, pkt))
        self.clock.sleep(self.seconds)
        if self.error:
            raise self.error
        choice = self.picks.get((card, model), pkt["qualifiers"][0])
        return {"end_turn": True, "finish": "end_turn", "text": json.dumps(
            {"choice": choice, "tags": ["broad_fall"], "facts": "The packet shows a fall."}), "usage": {}}


@pytest.fixture(autouse=True)
def private_test_spool(tmp_path, monkeypatch):
    monkeypatch.setattr(spool, "CUSTODY", tmp_path)
    monkeypatch.setattr(spool, "DEFAULT", tmp_path / "spool")


@pytest.fixture
def lab(tmp_path, monkeypatch):
    monkeypatch.setattr(bx, "private_roots", lambda: (tmp_path,))
    monkeypatch.setattr(e14, "require_go", lambda *a, **k: None)
    monkeypatch.setattr(d, "start_gate", lambda *a, **k: pytest.fail("live gate forbidden"))
    real = d.settings

    def cfg():
        c = real()
        c["ledger_row"] = 999
        c["cards"]["S"]["cost_limit_bp"] = 20
        c["not_before_utc"] = "2026-01-01T00:00:00Z"
        return c
    monkeypatch.setattr(d, "settings", cfg)
    p = tmp_path / "lab"
    p.mkdir(mode=0o700)
    with bx.locked(p) as path:
        rows = []
        bx.write_anchor(path, bx.anchor_state(rows))
        bx.append(path, rows, kind="header", first=bx.iso(T0), venue_generation=0, freeze=BUILD, frozen=d.frozen(cfg()))
    return p, cfg()


def run(lab, pages, clock, scout):
    return d.record(pages, lab[0], clock, clock.sleep, clock.mono, fake_transport(scout))


def fake_transport(scout):
    """Keep the E15 fake model tests at E17's new handoff boundary."""
    def exchange(jobs, timeout, *_args, before_call=None, **_kwargs):
        async def one(key, req):
            try:
                card = next(c for c in d.CARDS if req["system_text"] == d.COMMON + " " + d.CARD_TEXT[c])
                return key, await asyncio.wait_for(
                    scout(req["model"], card, json.loads(req["user_text"]), req["max_tokens"]), timeout)
            except TimeoutError:
                return key, {"status": "call_timeout"}
            except Exception as exc:
                return key, {"status": "call_error", "error": type(exc).__name__, "service_status": runner.rpc_status(exc)}

        async def batch():
            return dict(await asyncio.gather(*(one(k, req) for k, req in jobs.items())))

        if before_call:
            for key in jobs:
                before_call(key)
        return asyncio.run(batch()), [], 0
    return exchange


def fake_completion(text='{"choice":"pass","tags":[],"facts":"Closed candles."}'):
    return {"finish": "end_turn", "end_turn": True, "text": text, "usage": {"output_tokens": 3},
            "model_reported": SMALL}


async def advance(clock, seconds):
    clock.sleep(seconds)
    await asyncio.sleep(0)


def runner_on_poll(folder, clock, caller, build=BUILD):
    """Run an actual claim/SDK handoff with a fake model whenever the desk first waits."""
    ran = False

    def sleep(seconds):
        nonlocal ran
        if not ran:
            ran = True
            asyncio.run(runner.serve(clock() + timedelta(seconds=0.2), build=build, path=folder, clock=clock,
                                     sleep=lambda s: advance(clock, s), caller=caller))
        clock.sleep(seconds)
    return sleep


def make_request(spec, deadline, timeout=10, claim_by=None):
    return spool.request(spec, deadline, timeout, claim_by or deadline, BUILD)


def exchange_at(jobs, timeout, grace, clock, sleep, mono, **kwargs):
    deadline = clock() + timedelta(seconds=timeout)
    return spool.exchange(jobs, timeout, grace, clock, sleep, mono, deadline=deadline, build=BUILD, **kwargs)


def take(folder, req, clock, *, build=BUILD):
    return folder.claim(req, build, clock, spool.utc(req["deadline"]))


def test_spool_batch_round_trip_is_concurrent_and_hashes_exact_wire(tmp_path):
    folder, clock = tmp_path / "scout", Clock(T0)
    pkt = {"qualifiers": ["BTC"], "z": 1}
    jobs = {m: d.scout_fields(m, "S", pkt, 8000) for m in (SMALL, "claude_sonnet_5_5")}
    seen, claims = [], []

    async def call(req):
        seen.append(req)
        while len(seen) != 2:
            await asyncio.sleep(0)
        return fake_completion()

    result, ids, ignored = exchange_at(jobs, 10, 4, clock, runner_on_poll(folder, clock, call), clock.mono,
                                         path=folder, before_call=claims.append)
    assert set(claims) == set(jobs) and ignored == 0
    assert all(r["end_turn"] for r in result.values())
    assert all(r["user_text"] == json.dumps(pkt, sort_keys=True) and r["reply_schema"] == d.SCHEMA for r in seen)
    assert all(spool.valid_request(r, r["request_id"], clock()) for r in seen)
    spool.cleanup(ids, folder)
    assert {p.name for p in folder.iterdir()} == {".reply.lock", "heartbeat.json"}


@pytest.mark.parametrize("winner", ["claim", "withdrawn"])
def test_claim_withdraw_share_one_atomic_source_even_with_two_runners(tmp_path, winner):
    req = make_request(d.scout_fields(SMALL, None, None, 64), T0 + timedelta(seconds=10))
    rid = req["request_id"]
    with spool.private(tmp_path / "spool", create=True) as folder:
        folder.write(spool.filename("request", rid), req)
        if winner == "claim":
            assert take(folder, req, Clock(T0))
        else:
            assert folder.transfer(rid, winner)
        assert not take(folder, req, Clock(T0))
        assert not folder.transfer(rid, "withdrawn")
        assert folder.read(spool.filename("taken" if winner == "claim" else winner, rid)) == req


def test_no_runner_voids_the_pair_without_counting_a_failed_call(lab, tmp_path, monkeypatch):
    folder = tmp_path / "spool"
    monkeypatch.setattr(spool, "DEFAULT", folder)
    clock = at(1)
    wake = d.record(Pages(clock, last={"BTC": "90"}), lab[0], clock, clock.sleep, clock.mono)
    assert wake["signals"]["W"]["entries"]["scout"]["status"] == "scout_no_runner"
    assert set(x["status"] for x in wake["scout_results"].values()) == {"scout_no_runner"}
    r = rows(lab)
    ix = d.state(r, lab[1])
    assert d.paired(ix, "W", ("scout", "rule")) == []
    assert d.failed_calls(ix, 20) == (0, 0)
    assert d.counts(r, lab[1])["scout_no_runner"] == 1
    assert set(x.name for x in folder.iterdir()) == {".reply.lock"}


def test_runner_refusal_is_counted_without_message_in_rows_public_or_streams(lab, tmp_path, monkeypatch, capsys):
    marker = "invented-secret-that-must-not-appear"
    folder = tmp_path / "spool"
    monkeypatch.setattr(spool, "DEFAULT", folder)
    clock = at(1)

    class FakeRpcError(Exception):
        def code(self):
            return SimpleNamespace(name="UNAUTHENTICATED")

    async def call(_):
        try:
            raise FakeRpcError(marker)
        except FakeRpcError as exc:
            raise RuntimeError(marker) from exc

    out = d.record(Pages(clock, last={"BTC": "90"}), lab[0], clock, runner_on_poll(folder, clock, call), clock.mono)
    result, = out["scout_results"].values()
    assert {k: v for k, v in result.items() if k != "secs"} == {
        "status": "call_error", "error": "RuntimeError", "service_status": "UNAUTHENTICATED"}
    assert result["secs"] >= 0
    assert d.failed_calls(d.state(rows(lab), lab[1]), 20) == (1, 1)
    target = tmp_path / "public.json"
    assert d.publish(lab[0], target, clock())["scout_error_status"] == {"UNAUTHENTICATED": 1}
    captured = capsys.readouterr()
    assert marker not in json.dumps(rows(lab)) + target.read_text() + captured.out + captured.err
    assert runner.rpc_status(RuntimeError(marker)) == "UNKNOWN"


def test_ignores_wrong_id_or_hash_and_accepts_only_matching_claimed_reply(tmp_path):
    path, clock = tmp_path / "spool", Clock(T0)
    phases = []

    def sleep(s):
        with spool.private(path) as folder:
            if not phases:
                name, = [n for n in folder.names() if n.startswith("request-")]
                req = folder.read(name)
                assert take(folder, req, clock)
                phases.append(req)
                folder.write(spool.filename("reply", "a" * 32), {"request_id": "a" * 32})
            else:
                req = phases[0]
            rid = req["request_id"]
            phase = len(phases)
            reply = spool.reply_envelope(req, BUILD, fake_completion())
            reply["request_id"] = "f" * 32 if phase == 1 else rid
            reply["request_sha256"] = "0" * 64 if phase == 2 else req["sha256"]
            folder.write(spool.filename("reply", rid), reply)
            phases.append(phase)
        clock.sleep(s)

    got, ids, ignored = exchange_at({"s": d.scout_fields(SMALL, None, None, 64)}, 3, 1, clock, sleep,
                                       clock.mono, path=path)
    assert got["s"]["end_turn"] and ignored == 3
    spool.cleanup(ids, path)


def test_runner_ignores_deadline_and_bad_hash_and_drains_without_new_claim(tmp_path):
    path, clock = tmp_path / "spool", Clock(T0)
    spec = d.scout_fields(SMALL, None, None, 64)
    expired = make_request(spec, clock(), 3)
    invalid = make_request(spec, clock() + timedelta(seconds=10), 3) | {"sha256": "0" * 64}
    first = make_request(spec, clock() + timedelta(seconds=10), 3)
    next_ = make_request(spec, clock() + timedelta(seconds=10), 3)
    calls = []

    with spool.private(path, create=True) as folder:
        for req in (expired, invalid, first):
            folder.write(spool.filename("request", req["request_id"]), req)

    async def scenario():
        release = asyncio.Event()
        async def call(req):
            calls.append(req["request_id"])
            await release.wait()
            return fake_completion()

        async def sleep(_):
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            clock.sleep(1)
            with spool.private(path) as folder:
                folder.write(spool.filename("request", next_["request_id"]), next_)
            release.set()
            await asyncio.sleep(0)

        await runner.serve(clock() + timedelta(seconds=0.5), build=BUILD, path=path, clock=clock, sleep=sleep, caller=call)

    asyncio.run(scenario())
    assert calls == [first["request_id"]]
    with spool.private(path) as folder:
        assert all(spool.filename("request", req["request_id"]) in folder.names() for req in (expired, invalid, next_))
        assert spool.filename("reply", first["request_id"]) in folder.names()
        assert folder.read("heartbeat.json")["phase"] == "stopped"
        assert folder.read("heartbeat.json")["ignored_requests"] == 2


def test_spool_refuses_open_directory_and_nonprivate_or_symlink_files(tmp_path):
    path = tmp_path / "spool"
    path.mkdir(mode=0o755)
    with pytest.raises(spool.Refuse), spool.private(path):
        pytest.fail("public directory accepted")
    path.chmod(0o700)
    with spool.private(path) as folder:
        folder.write("x.json", {"x": 1})
        assert (path / "x.json").stat().st_mode & 0o777 == 0o600
        (path / "x.json").chmod(0o640)
        with pytest.raises(spool.Refuse):
            folder.read("x.json")
        (path / "link.json").symlink_to(path / "x.json")
        with pytest.raises(OSError):
            folder.read("link.json")
    alias = tmp_path / "alias"
    alias.symlink_to(path, target_is_directory=True)
    with pytest.raises(OSError), spool.private(alias):
        pytest.fail("symlink directory accepted")


def test_claimed_request_without_timely_reply_counts_as_timeout(tmp_path):
    path, clock = tmp_path / "spool", Clock(T0)
    observed = []
    req = None

    def sleep(s):
        nonlocal req
        clock.sleep(s)
        with spool.private(path) as folder:
            if req is None:
                name, = [n for n in folder.names() if n.startswith("request-")]
                req = folder.read(name)
                assert take(folder, req, clock)
            if clock.mono() >= 1:
                folder.write(spool.filename("reply", req["request_id"]), spool.reply_envelope(req, BUILD, fake_completion()))

    got, ids, ignored = exchange_at({"s": d.scout_fields(SMALL, None, None, 64)}, 1, 0.5, clock, sleep,
                                       clock.mono, before_call=observed.append, path=path)
    assert got == {"s": {"status": "call_timeout"}} and observed == ["s"] and ignored == 0
    spool.cleanup(ids, path)


def test_interrupted_wake_accounts_for_claimed_request_and_cleans_files(lab, tmp_path, monkeypatch):
    folder = tmp_path / "spool"
    monkeypatch.setattr(spool, "DEFAULT", folder)
    clock = at(0)
    # Crash after the runner's rename but before the desk's next poll.
    req = make_request(d.scout_fields(SMALL, None, None, 64), clock() + timedelta(seconds=10))
    rid = req["request_id"]
    with spool.private(create=True) as f:
        f.write(spool.filename("request", rid), req)
        assert take(f, req, clock)
    stamp = bx.iso(T0)
    with bx.locked(lab[0]) as path:
        rs = bx.read_log(path)
        bx.append(path, rs, kind="claim", wake=stamp)
        bx.append(path, rs, kind="scout_request", wake=stamp, request_id=rid, request_sha256=req["sha256"],
                  claim_by=req["claim_by"], call_id="invented", card="W", line="scout", model=SMALL,
                  prompt_sha256="p", packet_sha256="q")
    d.record(Pages(clock), lab[0], clock, clock.sleep, clock.mono)
    saved = rows(lab)
    assert [r["kind"] for r in saved[-2:]] == ["scout_call", "void"]
    assert saved[-2]["recovered"] and saved[-1]["reason"] == "interrupted_wake"
    assert d.failed_calls(d.state(saved, lab[1]), 20) == (1, 1)
    assert not list(folder.glob("*.json"))


@pytest.mark.parametrize("claimed_at", [19.999999, 20, 21])
def test_absolute_claim_edge_is_checked_even_when_desk_polls_late(tmp_path, claimed_at):
    path, clock = tmp_path / "spool", Clock(T0)
    observed = []

    def after_stall(_seconds):
        clock.sleep(claimed_at)
        with spool.private(path) as folder:
            name, = [n for n in folder.names() if n.startswith("request-")]
            req = folder.read(name)
            rid = req["request_id"]
            assert spool.utc(req["claim_by"]) == T0 + timedelta(seconds=20)
            claim = take(folder, req, clock)
            if claimed_at >= 20:
                assert claim is None
                # Simulate a stale or noncompliant runner leaving a late claim and reply.
                folder.write(spool.filename("claim", rid), spool.claim_record(req, BUILD, clock()))
                assert folder.transfer(rid, "taken")
            else:
                assert claim["claimed_utc"] == clock().isoformat()
            folder.write(spool.filename("reply", rid), spool.reply_envelope(req, BUILD, fake_completion()))
        clock.sleep(21 - claimed_at)

    spec = {"s": d.scout_fields(SMALL, None, None, 64)}
    got, ids, ignored = exchange_at(spec, 30, 20, clock, after_stall, clock.mono,
                                   before_call=observed.append, path=path)
    if claimed_at < 20:
        assert got["s"]["end_turn"] and observed == ["s"] and ignored == 0
    else:
        assert got == {"s": {"status": "scout_no_runner"}} and not observed and ignored == 2
    spool.cleanup(ids, path)


def test_rename_that_stalls_past_claim_deadline_never_calls(tmp_path, monkeypatch):
    path, clock = tmp_path / "spool", Clock(T0)
    transfer = spool.Folder.transfer

    def stalled_rename(folder, rid, dest):
        if dest == "taken":
            assert clock() == T0 + timedelta(seconds=19.9)
            clock.sleep(1.1)
        return transfer(folder, rid, dest)
    monkeypatch.setattr(spool.Folder, "transfer", stalled_rename)

    async def no_call(_):
        pytest.fail("a late rename must not start a call")

    def delayed_runner(_):
        clock.sleep(19.9)
        asyncio.run(runner.serve(T0 + timedelta(seconds=21.2), build=BUILD, path=path, clock=clock,
                                 sleep=lambda s: advance(clock, s), caller=no_call))

    jobs = {"s": d.scout_fields(SMALL, None, None, 64)}
    got, ids, ignored = exchange_at(jobs, 30, 20, clock, delayed_runner, clock.mono, path=path)
    rid, = ids
    with spool.private(path) as folder:
        claim = folder.read(spool.filename("claim", rid))
        assert claim["claimed_utc"] == (T0 + timedelta(seconds=21)).isoformat()
        assert claim["late"] is True and spool.filename("reply", rid) not in folder.names()
    assert got == {"s": {"status": "scout_no_runner"}} and ignored == 1


@pytest.mark.parametrize("pending", [False, True])
def test_held_runner_lock_cannot_delay_no_runner_decision(tmp_path, pending):
    path, clock = tmp_path / "spool", Clock(T0)
    with ExitStack() as held:
        locked = False

        def obstruct(seconds):
            nonlocal locked
            clock.sleep(seconds)
            if not locked and clock() == T0 + timedelta(seconds=20):
                folder = held.enter_context(spool.private(path))
                held.enter_context(folder.fence())
                locked = True
                if pending:
                    name, = [n for n in folder.names() if n.startswith("request-")]
                    assert folder.transfer(folder.read(name)["request_id"], "taken")

        jobs = {"s": d.scout_fields(SMALL, None, None, 64)}
        got, ids, ignored = exchange_at(jobs, 120, 20, clock, obstruct, clock.mono, path=path)
        assert locked and got == {"s": {"status": "scout_no_runner"}}
        assert clock() == T0 + timedelta(seconds=22 if pending else 20)
        assert ignored == int(pending)
        with spool.private(path) as folder:
            want = "taken" if pending else "withdrawn"
            assert spool.filename(want, ids[0]) in folder.names()
        # Cleanup must also return without waiting for the runner.
        assert spool.cleanup(ids, path) == 0


def test_claim_first_seen_after_hard_bound_is_ignored(tmp_path):
    path, clock = tmp_path / "spool", Clock(T0)

    def delayed_poll(_):
        clock.sleep(19.9)
        with spool.private(path) as folder:
            name, = [n for n in folder.names() if n.startswith("request-")]
            req = folder.read(name)
            assert take(folder, req, clock)
            clock.sleep(2.2)
            folder.write(spool.filename("reply", req["request_id"]), spool.reply_envelope(req, BUILD, fake_completion()))

    jobs = {"s": d.scout_fields(SMALL, None, None, 64)}
    got, _, ignored = exchange_at(jobs, 120, 20, clock, delayed_poll, clock.mono, path=path)
    assert got == {"s": {"status": "scout_no_runner"}} and ignored == 2


def test_late_reply_after_no_runner_is_counted_without_changing_the_wake(lab):
    clock, captured = at(1), []

    def transport(jobs, cap, grace, wall, sleep, mono, *, before_request, **kwargs):
        def register(key, req):
            captured.append(req)
            before_request(key, req)
        result = spool.exchange(jobs, cap, grace, wall, sleep, mono, before_request=register, **kwargs)
        with spool.private() as folder:
            req, = captured
            folder.write(spool.filename("reply", req["request_id"]), spool.reply_envelope(req, BUILD, fake_completion()))
        return result

    wake = d.record(Pages(clock, last={"ETH": "94"}), lab[0], clock, clock.sleep, clock.mono, transport)
    assert wake["signals"]["W"]["entries"]["scout"]["status"] == "scout_no_runner"
    saved = rows(lab)
    assert d.counts(saved, lab[1])["scout_ignored_replies"] == 1
    assert saved[-1]["kind"] == "scout_discard"
    assert not list(spool.DEFAULT.glob("reply-*.json"))


def test_two_live_runners_only_one_gets_the_request(tmp_path, monkeypatch):
    path, clock = tmp_path / "spool", spool.now_utc
    req = make_request(d.scout_fields(SMALL, None, None, 64), clock() + timedelta(seconds=10))
    rid = req["request_id"]
    timeline = []
    with spool.private(path, create=True) as folder:
        folder.write(spool.filename("request", rid), req)

    barrier = Barrier(2)
    claim = spool.Folder.claim

    def race(self, *args):
        # Both runners saw the same request before either claims it.
        barrier.wait(timeout=5)
        return claim(self, *args)

    monkeypatch.setattr(spool.Folder, "claim", race)

    async def call(_):
        timeline.append("call")
        return fake_completion()

    until = clock() + timedelta(seconds=1)
    def serve():
        asyncio.run(runner.serve(until, build=BUILD, path=path, clock=clock, caller=call))

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(serve) for _ in range(2)]
        for future in futures:
            future.result()
    assert timeline == ["call"]
    with spool.private(path) as f:
        assert f.read(spool.filename("taken", rid)) == req
        assert f.read(spool.filename("claim", rid))["build"] == BUILD
        assert f.read(spool.filename("reply", rid))["build"] == BUILD


@pytest.mark.parametrize("interrupted", [False, True])
def test_twentieth_call_is_first_dispatched_not_first_claimed(lab, interrupted):
    clock, prior = at(0), bx.iso(T0 - bx.HOUR)
    old = {f"old{i}": {"status": "call_error" if i < 5 else "ok"} for i in range(19)}
    with bx.locked(lab[0]) as path:
        rs = bx.read_log(path)
        for cid in old:
            bx.append(path, rs, kind="scout_call", wake=prior, call_id=cid)
        bx.append(path, rs, kind="wake", wake=prior, scout_results=old)
    taken = []

    def reverse_claims(seconds):
        clock.sleep(seconds)
        with spool.private() as folder:
            if len(taken) == 2:
                return
            req = next(folder.read(name) for name in folder.names() if name.startswith("request-")
                       and folder.read(name)["model"] == ("claude_sonnet_5_5" if not taken else SMALL))
            assert take(folder, req, clock)
            took_b = not taken
            taken.append(req["model"])
            reply = (fake_completion() if took_b else
                     {"status": "call_error", "error": "FakeError", "service_status": "UNKNOWN"})
            folder.write(spool.filename("reply", req["request_id"]), spool.reply_envelope(req, BUILD, reply))
            if interrupted and not took_b:
                raise KeyboardInterrupt

    if interrupted:
        with pytest.raises(KeyboardInterrupt):
            d.record(Pages(clock), lab[0], clock, reverse_claims, clock.mono)
        assert len(d.state(rows(lab), lab[1])["calls"]) == 19
        out = d.record(Pages(clock), lab[0], clock, clock.sleep, clock.mono)
    else:
        out = d.record(Pages(clock), lab[0], clock, reverse_claims, clock.mono)
    assert taken == ["claude_sonnet_5_5", SMALL]
    assert out["reason"] == "scout_repair"
    saved = rows(lab)
    assert [r["model"] for r in saved if r["kind"] == "scout_call" and r["wake"] == bx.iso(T0)] == [SMALL, taken[0]]
    assert d.failed_calls(d.state(saved, lab[1]), 20) == (6, 20)


def test_spool_refuses_symlink_ancestor_and_git_work_tree(tmp_path):
    outside = tmp_path / "real"
    outside.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(outside, target_is_directory=True)
    with pytest.raises((OSError, spool.Refuse)), spool.private(alias / "spool", create=True):
        pytest.fail("symlink ancestor accepted")
    assert not (outside / "spool").exists()
    (outside / ".git").mkdir()
    with pytest.raises(spool.Refuse, match="git work tree"), spool.private(outside / "spool", create=True):
        pytest.fail("git work tree accepted")


def seed_stale_scout_files():
    req = make_request(d.scout_fields(SMALL, None, None, 64), T0 + timedelta(seconds=10))
    rid = req["request_id"]
    with spool.private(create=True) as f:
        for kind in ("request", "claim", "reply"):
            f.write(spool.filename(kind, rid), req)
        f.write("heartbeat.json", {"phase": "stopped"})
    return rid


def test_wake_sweeps_killed_start_files_and_counts_them(lab):
    old = seed_stale_scout_files()
    clock = at(0)
    out = run(lab, Pages(clock), clock, Scout(Pages(clock), clock))
    assert out["kind"] == "wake" and d.counts(rows(lab), lab[1])["scout_ignored_replies"] == 3
    assert not list(spool.DEFAULT.glob(f"*-{old}.json"))
    assert (spool.DEFAULT / "heartbeat.json").exists()


def test_absolute_reply_deadline_does_not_rebase_after_stall(lab):
    clock = at(1, 1350)
    reserve = T0 + timedelta(hours=1, seconds=1430)
    seen = []

    def stall(jobs, cap, grace, wall, sleep, mono, *, before_request, deadline, **kwargs):
        assert deadline == reserve
        clock.sleep((deadline - clock()).total_seconds() - 1)
        def record(key, req):
            seen.append(spool.utc(req["deadline"]))
            before_request(key, req)
        res = spool.exchange(jobs, cap, grace, wall, sleep, mono, deadline=deadline, before_request=record, **kwargs)
        assert clock() == reserve
        return res

    out = d.record(Pages(clock, last={"ETH": "94"}), lab[0], clock, clock.sleep, clock.mono, stall)
    assert seen == [reserve] and out["signals"]["W"]["entries"]["scout"]["status"] == "scout_no_runner"


def test_start_checks_both_scouts_before_receipt_and_loop_drops_environment(lab, tmp_path, monkeypatch):
    folder, auth, data = tmp_path / "spool", tmp_path / "receipts", tmp_path / "new-desk"
    monkeypatch.setattr(spool, "DEFAULT", folder)
    monkeypatch.setattr(d, "checked_build", lambda: BUILD)
    monkeypatch.setattr(d, "start_gate", lambda *a: (0, None))
    clock = Clock(T0)
    env_key = "PPLX_LLM_API_KEY"

    def no_runner(jobs, cap, grace, *_args, **kwargs):
        assert env_key not in os.environ
        return spool.exchange(jobs, cap, grace, clock, clock.sleep, clock.mono, **kwargs)

    def backend(fail):
        def exchange(jobs, *_args, **_kwargs):
            assert env_key not in os.environ
            assert set(jobs) == set(d.models(lab[1]).values())
            assert all(job["system_text"] == d.CHECK_SYSTEM and job["user_text"] == d.CHECK_USER for job in jobs.values())
            result = {key: fake_completion('{"check":"OK"}') for key in jobs}
            if fail == "invalid":
                result[SMALL] = fake_completion()
            elif fail:
                result[SMALL] = {"status": "call_error", "error": "FakeRpcError", "service_status": "UNAUTHENTICATED"}
            return result, [], 0
        return exchange

    for transport in (no_runner, backend(True), backend("invalid")):
        monkeypatch.setenv(env_key, "invented-marker")
        with pytest.raises(bx.Refuse, match="scout checks refused"):
            d.start(T0, data, auth, clock=clock, check_transport=transport)
        assert env_key not in os.environ
        assert not auth.exists() and not data.exists()
    monkeypatch.setenv(env_key, "invented-marker")
    d.start(T0, data, auth, clock=clock, check_transport=backend(False))
    assert env_key not in os.environ and len(list(auth.iterdir())) == 1
    with bx.locked(data) as path:
        assert [r["kind"] for r in bx.read_log(path)] == ["header"]

    def end(*_args):
        assert env_key not in os.environ
        return {"kind": "done"}

    monkeypatch.setenv(env_key, "invented-marker")
    monkeypatch.setattr(d, "record", end)
    assert d.loop(data, clock, clock.sleep, clock.mono)["status"] == "done"
    assert env_key not in os.environ
    assert Path(d.__file__).read_text().count(f'os.environ.pop("{env_key}", None)') == 2
    assert Path(d.__file__).read_text().count(env_key) == 2
    assert env_key not in Path(runner.__file__).read_text() + Path(spool.__file__).read_text()


@pytest.fixture
def literal_start(tmp_path, monkeypatch):
    """Use real literal build, ledger parser, gate, and journal checks with no real approval."""
    checkout = tmp_path / "build"
    checkout.mkdir()
    for name in d.PINNED:
        (checkout / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(d.ROOT / name, checkout / name)
    author = {"GIT_AUTHOR_NAME": "Brandon Church", "GIT_AUTHOR_EMAIL": "modernsoftworks@gmail.com",
              "GIT_COMMITTER_NAME": "Brandon Church", "GIT_COMMITTER_EMAIL": "modernsoftworks@gmail.com"}
    env = {"PATH": os.environ.get("PATH", os.defpath), "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_CONFIG_GLOBAL": os.devnull} | author
    def git(*args):
        return subprocess.check_output(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=checkout,
                                       env=env, stderr=subprocess.DEVNULL, text=True).strip()
    git("init", "--quiet")
    git("add", ".")
    git("-c", "commit.gpgsign=false", "commit", "-qm", "Scratch audit fixture",
        "-m", "Co-authored-by: Perplexity <noreply@perplexity.ai>")
    build = git("rev-parse", "HEAD")
    monkeypatch.setattr(e14, "ROOT", checkout)
    monkeypatch.setattr(d, "ROOT", checkout)
    monkeypatch.setattr(bx, "private_roots", lambda: (tmp_path,))
    literal_git = e14.literal_git
    approval = {"build": build, "generation": None}
    def memory_ledger(*args, **kwargs):
        if args == ("show", f"{bx.APPROVAL_REF}:{bx.LEDGER}"):
            # The parser sees one synthetic approval in memory only. Do not write a go key.
            key = "E17_START"
            fields = [(key, approval["build"]), (key + "_GENERATION", approval["generation"])]
            return "| 242 | " + " ".join("=".join((k, str(v))) for k, v in fields if v is not None) + " |"
        return literal_git(*args, **kwargs)
    monkeypatch.setattr(e14, "literal_git", memory_ledger)
    clock = Clock(T0)
    gate_obj = bx.Gate(tmp_path / "gate" / "cooldown.json", clock=clock)
    return SimpleNamespace(clock=clock, build=build, checkout=checkout, approval=approval, gate=gate_obj,
                           data=tmp_path / "desk", auth=tmp_path / "receipts")


def synthetic_checks(jobs, *_args, **_kwargs):
    return {model: fake_completion('{"check":"OK"}') for model in jobs}, [], 0


def start_in(lab, transport=synthetic_checks):
    return d.start(lab.clock(), lab.data, lab.auth, gate_obj=lab.gate, clock=lab.clock, check_transport=transport)


@pytest.mark.parametrize("changed", ["pin", "generation", "approval", "cooldown"])
def test_start_rechecks_guards_after_pending_scout_checks(literal_start, changed):
    x = literal_start

    def checks(jobs, *_args, **_kwargs):
        if changed == "pin":
            path = x.checkout / d.CARD
            path.write_text(path.read_text() + "\nAn edit made while the checks are pending.\n")
        elif changed == "generation":
            x.gate.write(x.gate.cooldown_path.parent / bx.GENERATION, {"generation": 1})
        elif changed == "approval":
            x.approval["build"] = None
        else:
            x.gate.write(x.gate.cooldown_path, {"not_before_utc": bx.precise_utc(x.clock() + timedelta(seconds=30))})
        return synthetic_checks(jobs)
    with pytest.raises(bx.Refuse, match={"pin": "frozen inputs", "generation": "generation",
                                       "approval": "committed ledger", "cooldown": "gate state"}[changed]):
        start_in(x, checks)
    assert not x.data.exists() and not list(x.auth.glob("*.json"))


def test_start_generation_key_once_only_and_post_check_time(literal_start):
    x = literal_start
    assert x.gate.check_start() == 0
    x.gate.write(x.gate.cooldown_path.parent / bx.GENERATION, {"generation": 3})
    for missing_or_wrong in (None, 2):
        x.approval["generation"] = missing_or_wrong
        with pytest.raises(bx.Refuse, match="E17_START_GENERATION"):
            start_in(x, lambda *_a, **_k: pytest.fail("should refuse before scout checks"))
        assert not x.auth.exists()
    x.approval["generation"] = 3
    stale = seed_stale_scout_files()
    x.clock.sleep(1199)

    def checked(jobs, *_args, **_kwargs):
        assert not list(spool.DEFAULT.glob(f"*-{stale}.json"))
        x.clock.sleep(2)
        return synthetic_checks(jobs)

    out = start_in(x, checked)
    assert out["first_wake"] == bx.iso(T0 + bx.HOUR) and out["scout_start_ignored"] == 3
    receipt, = list(x.auth.glob("*.json"))
    assert json.loads(receipt.read_text())["made_utc"] == bx.precise_utc(x.clock())
    with bx.locked(x.data) as path:
        saved = bx.read_log(path)
    assert saved[0]["venue_generation"] == 3 and d.counts(saved, d.settings())["scout_ignored_replies"] == 3
    with pytest.raises(bx.Refuse, match="already started"):
        start_in(x, lambda *_a, **_k: pytest.fail("used approval must not dispatch checks"))
    with pytest.raises(bx.Refuse, match="already used"):
        d.start(x.clock(), x.data.with_name("missing-journal"), x.auth, gate_obj=x.gate, clock=x.clock,
                check_transport=lambda *_a, **_k: pytest.fail("used receipt must not dispatch checks"))
    assert list(x.auth.glob("*.json")) == [receipt]


def test_foreign_build_cannot_start_through_real_runner(literal_start):
    x = literal_start

    async def should_not_call(_):
        pytest.fail("foreign runner must not make a matching call")

    def exchange(jobs, cap, grace, *_args, **kwargs):
        return spool.exchange(jobs, cap, grace, x.clock,
                              runner_on_poll(spool.DEFAULT, x.clock, should_not_call, build="b" * 40),
                              x.clock.mono, **kwargs)
    with pytest.raises(bx.Refuse, match="scout_no_runner|SCOUT_NO_RUNNER"):
        start_in(x, exchange)
    assert not x.auth.exists() and not x.data.exists()


def spool_snapshot():
    return {p.name: p.read_bytes() for p in spool.DEFAULT.iterdir()}


@pytest.mark.parametrize("phase", ["before_sweep", "live_claim", "receipt_written"])
def test_interleaved_starts_cannot_change_spool(literal_start, monkeypatch, phase):
    x = literal_start
    seed_stale_scout_files()
    attempts = []

    def try_second():
        files = spool_snapshot()
        with pytest.raises(bx.Refuse, match="spool is in use"):
            # Even a different journal path cannot claim ownership of this spool.
            d.start(x.clock(), x.data.with_name("second-desk"), x.auth.with_name("second-receipt"),
                    gate_obj=x.gate, clock=x.clock, check_transport=lambda *_a, **_k: pytest.fail("second checked models"))
        assert spool_snapshot() == files
        attempts.append(phase)

    if phase == "before_sweep":
        sweep = d.sweep_requests
        def interleave(*args):
            try_second()
            return sweep(*args)
        monkeypatch.setattr(d, "sweep_requests", interleave)
    if phase == "receipt_written":
        append = bx.append
        def interleave(off, journal, **event):
            if event["kind"] == "header":
                assert list(x.auth.glob("*.json"))
                try_second()
            return append(off, journal, **event)
        monkeypatch.setattr(bx, "append", interleave)

    def checks(jobs, *_args, **_kwargs):
        if phase == "live_claim":
            until = x.clock() + timedelta(seconds=10)
            req = spool.request(next(iter(jobs.values())), until, 10, until, x.build)
            rid = req["request_id"]
            with spool.private() as folder:
                folder.write(spool.filename("request", rid), req)
                assert take(folder, req, x.clock, build=x.build)
                try_second()
            spool.cleanup([rid])
        return synthetic_checks(jobs)

    assert start_in(x, checks)["freeze"] == x.build and attempts == [phase]
    assert len(list(x.auth.glob("*.json"))) == 1


@pytest.mark.parametrize("active_wake", [True, False])
def test_start_resuming_at_open_wake_cannot_sweep_its_files(literal_start, monkeypatch, active_wake):
    x = literal_start
    start_in(x)
    x.clock.sleep(1200)
    leader = get_ident()
    paused, resume = Event(), Event()
    owner = d.scout_owner

    @contextmanager
    def stall_start():
        if get_ident() != leader:
            paused.set()
            assert resume.wait(timeout=5)
        with owner():
            yield
    monkeypatch.setattr(d, "scout_owner", stall_start)

    def late_start():
        with pytest.raises(bx.Refuse, match="spool is in use" if active_wake else "already started"):
            start_in(x, lambda *_a, **_k: pytest.fail("a late start cannot check models"))

    with ThreadPoolExecutor(max_workers=1) as pool:
        late = pool.submit(late_start)
        try:
            assert paused.wait(timeout=5)

            def sleep(seconds):
                if not resume.is_set() and active_wake:
                    files = spool_snapshot()
                    assert any(name.startswith("request-") for name in files)
                    resume.set()
                    late.result(timeout=5)
                    assert spool_snapshot() == files
                x.clock.sleep(seconds)

            wake = d.record(Pages(x.clock), x.data, x.clock, sleep, x.clock.mono)
            assert wake["kind"] == "wake"
            if not active_wake:
                seed_stale_scout_files()
                files = spool_snapshot()
                resume.set()
                late.result(timeout=5)
                assert spool_snapshot() == files
        finally:
            resume.set()


@pytest.mark.parametrize("foreign_claim", [False, True])
def test_trading_rejects_foreign_build_claim_or_reply(lab, foreign_claim):
    clock, dispatched = at(1), []

    def fake_runner(seconds):
        clock.sleep(seconds)
        if dispatched:
            return
        with spool.private() as folder:
            name, = [n for n in folder.names() if n.startswith("request-")]
            req = folder.read(name)
            rid = req["request_id"]
            foreign = "b" * 40
            if foreign_claim:
                folder.write(spool.filename("claim", rid), spool.claim_record(req, foreign, clock()))
                assert folder.transfer(rid, "taken")
            else:
                assert take(folder, req, clock)
            folder.write(spool.filename("reply", rid), spool.reply_envelope(req, foreign, fake_completion()))
            dispatched.append(rid)
    out = d.record(Pages(clock, last={"ETH": "94"}), lab[0], clock, fake_runner, clock.mono)
    result, = out["scout_results"].values()
    assert result["status"] == ("scout_no_runner" if foreign_claim else "call_timeout")
    assert out["scout_ignored_replies"] == (2 if foreign_claim else 1)
    assert d.failed_calls(d.state(rows(lab), lab[1]), 20) == ((0, 0) if foreign_claim else (1, 1))


def rows(lab):
    with bx.locked(lab[0], write=False) as path:
        return bx.read_log(path)


def at(hour, seconds=1200):
    return Clock(T0 + timedelta(hours=hour, seconds=seconds))


# ------------------------------------------------------------------ window and dates
def test_no_request_before_window_or_after_cutoff(lab):
    clock = at(1, 1199)
    pages = Pages(clock)
    assert run(lab, pages, clock, Scout(pages, clock))["kind"] == "nothing due"
    clock = at(0, 1490)                       # hour 0 is past its cutoff: void, no request
    pages = Pages(clock)
    run(lab, pages, clock, Scout(pages, clock))
    assert pages.calls == []
    assert rows(lab)[-1]["kind"] == "void" and rows(lab)[-1]["reason"] == "missed_wake"


def test_every_request_inside_window(lab):
    clock = at(0)
    pages = Pages(clock, last={"ETH": "94", "ADA": "92"})
    run(lab, pages, clock, Scout(pages, clock, seconds=30))
    assert pages.calls
    for _, _, t in pages.calls:
        assert T0 + timedelta(seconds=1200) <= t < T0 + timedelta(seconds=1490)


def test_first_wake_respects_not_before():
    cfg = d.settings.__wrapped__() if hasattr(d.settings, "__wrapped__") else d.settings()
    assert cfg["not_before_utc"] == "2026-11-28T06:00:00Z"
    assert d.first_wake(datetime(2026, 11, 27, 22, 0, tzinfo=timezone.utc), cfg) == datetime(2026, 11, 28, 6, tzinfo=timezone.utc)
    assert d.first_wake(datetime(2026, 11, 28, 6, 21, tzinfo=timezone.utc), cfg) == datetime(2026, 11, 28, 7, tzinfo=timezone.utc)


def test_unset_required_settings_refuse():
    cfg = d.settings()
    d.required(cfg)                           # the registered values (ledger row 242, S limit 25 bp) pass
    assert cfg["ledger_row"] == 242 and cfg["cards"]["S"]["cost_limit_bp"] == 25
    no_row = json.loads(json.dumps(cfg))
    no_row["ledger_row"] = None
    no_limit = json.loads(json.dumps(cfg))
    no_limit["cards"]["S"]["cost_limit_bp"] = None
    for bad in (no_row, no_limit):
        with pytest.raises(bx.Refuse):
            d.required(bad)


# ------------------------------------------------------------------ card W, pairing and the gate
def test_w_lines_share_post_decision_books_and_rule_is_largest_fall(lab):
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94", "ADA": "92"})
    scout = Scout(pages, clock, picks={("W", SMALL): "ETH"})
    out = run(lab, pages, clock, scout)
    sig = out["signals"]["W"]
    assert sig["qualifiers"] == ["ADA", "ETH"]
    assert sig["choices"]["rule"] == "ADA" and sig["choices"]["scout"] == "ETH"
    assert sig["choices"]["random"] in ("ADA", "ETH")
    for line in ("scout", "rule", "random"):
        assert sig["entries"][line]["status"] == "ok"
        assert sig["gate"][line]["outcome"] == "accepted"
    ids = {line: sig["entries"][line]["book_id"] for line in ("scout", "rule", "random")}
    coin = {line: sig["entries"][line]["coin"] for line in ids}
    for a in ids:
        for b in ids:
            assert (ids[a] == ids[b]) == (coin[a] == coin[b])
    # entry books are fetched after the scout call and once per coin
    call_t = [t for k, c, t in pages.calls if k == "book"]
    entry = [c for k, c, t in pages.calls if k == "book"][-len(set(coin.values())):]
    assert sorted(entry) == sorted(set(coin.values()))
    assert len(scout.seen) == 1


def test_w_rule_matches_e14_choice():
    panel = {c: {0: (1, 1, 1, 100, 1), 1: (1, 1, 1, 100, 1)} for c in ("ADA", "ETH", "XRP")}
    panel["ETH"][1] = (1, 1, 1, 94, 1)
    panel["ADA"][1] = (1, 1, 1, 94, 1)
    q, best = d.w_filter(panel, ["ADA", "ETH", "XRP"], 0.05)
    closes = {c: ("100", str(panel[c][1][3])) for c in panel}
    assert best == e14.choose(closes, ["ADA", "ETH", "XRP"], 0.05) == "ADA"
    assert [c for c, _ in q] == ["ADA", "ETH"]


def test_future_bar_never_reaches_scout_or_gate(lab):
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94"}, future=True)
    scout = Scout(pages, clock)
    out = run(lab, pages, clock, scout)
    pkt = scout.seen[0][2]
    assert "99999" not in json.dumps(pkt)
    eth = next(r for r in pkt["coins"] if r["coin"] == "ETH")
    assert eth["ret_1h"] == pytest.approx(-0.06)
    assert out["signals"]["W"]["entries"]["scout"]["status"] == "ok"


def test_no_model_call_while_gate_held_and_no_call_without_qualifiers(lab):
    clock = at(1)
    pages = Pages(clock)                      # nothing fell: no qualifier, no call
    scout = Scout(pages, clock)
    run(lab, pages, clock, scout)
    assert scout.seen == []


def test_scout_pass_counts_zero_in_pair(lab):
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94"})
    run(lab, pages, clock, Scout(pages, clock, picks={("W", SMALL): "pass"}))
    clock = at(25)
    pages = Pages(clock, books={"ETH": depth("101.05", "100.95")})
    run(lab, pages, clock, Scout(pages, clock))
    r = rows(lab)
    ix = d.state(r, lab[1])
    ps = d.paired(ix, "W", ("scout", "rule"))
    assert len(ps) == 1 and ps[0]["scout_net"] is None
    assert ps[0]["diff"] == pytest.approx(-ps[0]["other_net"])
    assert ps[0]["other_net"] > 0


def test_card_slot_blocks_new_w_signal_while_open(lab):
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94"})
    run(lab, pages, clock, Scout(pages, clock))
    clock = at(2)
    pages = Pages(clock, last={"ADA": "90"})
    out = run(lab, pages, clock, Scout(pages, clock))
    assert "W" not in out["active"]


# ------------------------------------------------------------------ busy, cooldown and stops
def test_busy_entry_book_is_lost_not_a_crash(lab):
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94"})
    orig = pages.book
    n = {"k": 0}

    def book(venue, coin):
        n["k"] += 1
        if n["k"] >= 2:                      # the pre-decision book works; every entry book finds the gate busy
            pages._hit("busy", coin)
            raise bx.Failure("shared_gate_busy")
        return orig(venue, coin)
    pages.book = book
    start = clock()
    out = run(lab, pages, clock, Scout(pages, clock))
    for line in ("scout", "rule", "random"):
        assert out["signals"]["W"]["entries"][line]["status"] == "shared_gate_busy"
    assert clock() - start < timedelta(seconds=60)
    assert d.state(rows(lab), lab[1])["open"].get(("W", "rule"), []) == []


def test_blocked_stops_cleanly_and_stays_stopped(lab):
    clock = at(1)
    pages = Pages(clock, fail={("pairs", None): lambda: bx.Blocked(bx.HOST, 403)})
    out = run(lab, pages, clock, Scout(pages, clock))
    assert out["kind"] == "stop" and out["http_status"] == 403
    clock = at(2)
    pages = Pages(clock)
    assert run(lab, pages, clock, Scout(pages, clock))["kind"] == "stopped"
    assert pages.calls == []


def test_gate_custody_fault_stops(lab):
    clock = at(1)
    pages = Pages(clock, fail={("pairs", None): bx.GateUncertain})
    out = run(lab, pages, clock, Scout(pages, clock))
    assert out["kind"] == "stop" and out["reason"] == "gate_inflight"


def test_lost_exit_book_retries_next_wake(lab):
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94"})
    run(lab, pages, clock, Scout(pages, clock))
    clock = at(25)
    pages = Pages(clock, fail={("book", "ETH"): bx.Failure("shared_cooldown")})
    out = run(lab, pages, clock, Scout(pages, clock))
    assert out["exits"] and all(not x["final"] for x in out["exits"])
    clock = at(26)
    pages = Pages(clock)
    out = run(lab, pages, clock, Scout(pages, clock))
    assert out["exits"] and all(x["final"] and x["status"] == "ok" for x in out["exits"])


def test_interrupted_claim_is_void_not_refetched(lab):
    with bx.locked(lab[0]) as path:
        r = bx.read_log(path)
        bx.append(path, r, kind="claim", wake=bx.iso(T0), made_utc=bx.iso(T0))
    clock = at(0)
    pages = Pages(clock)
    run(lab, pages, clock, Scout(pages, clock))
    assert rows(lab)[-1]["reason"] == "interrupted_wake" and pages.calls == []


# ------------------------------------------------------------------ card S and the repair stop
def test_s_qualifiers_cost_limit_two_scouts_random_never_passes(lab):
    clock = at(0)
    thin = {"asks": [["100.05", "0.1"], ["110", "1000"]], "bids": [["99.95", "1000"]]}
    pages = Pages(clock, books={"DOGE": thin})
    scout = Scout(pages, clock, picks={("S", SMALL): "pass"})
    out = run(lab, pages, clock, scout)
    sig = out["signals"]["S"]
    assert "DOGE" not in sig["qualifiers"] and len(sig["qualifiers"]) == 19
    assert {m for m, c, _ in scout.seen} == {SMALL, "claude_sonnet_5_5"}
    assert sig["entries"]["scout_small"]["status"] == "pass"
    assert sig["entries"]["scout_second"]["status"] == "ok"
    assert sig["entries"]["random"]["status"] == "ok"


def test_repair_stop_after_more_than_five_failed_calls(lab):
    for hour in (0, 4, 8):
        clock = at(hour)
        pages = Pages(clock)
        out = run(lab, pages, clock, Scout(pages, clock, error=RuntimeError("down")))
    assert out["kind"] == "stop" and out["reason"] == "scout_repair"


def test_reply_form():
    q = ["ETH", "ADA"]
    ok = json.dumps({"choice": "ETH", "tags": ["thin_book"], "facts": "x"})
    assert d.check_reply(ok, q)[1] == "ok"
    assert d.check_reply(json.dumps({"choice": "SOL", "tags": [], "facts": "x"}), q)[1] == "reply_choice"
    assert d.check_reply(json.dumps({"choice": "pass", "tags": ["nope"], "facts": "x"}), q)[1] == "reply_tags"
    assert d.check_reply(json.dumps({"choice": "ETH", "tags": [], "facts": "x", "size": 1}), q)[1] == "reply_fields"
    assert d.check_reply("not json", q)[1] == "reply_not_json"


def test_timeout_and_incomplete_are_failed_replies():
    async def slow(*a):
        await asyncio.sleep(5)

    async def cut(*a):
        return {"end_turn": False, "finish": "max_tokens", "text": ""}
    jobs = [("k", "m", "W", {"qualifiers": ["ETH"]}, ["ETH"])]
    clock = Clock(T0)
    args = (d.settings(), clock, clock.sleep, clock.mono)
    assert d.run_scouts(jobs, fake_transport(slow), 0.05, *args)[0]["k"]["status"] == "call_timeout"
    assert d.run_scouts(jobs, fake_transport(cut), 1, *args)[0]["k"]["status"] == "reply_incomplete"


# ------------------------------------------------------------------ card F against E12's audited rule
def test_f_rule_matches_e12_decide():
    np = pytest.importorskip("numpy")
    import forward_e12 as e12
    rule = e12.rules()["70-102"]
    wake = datetime(2027, 1, 5, 10, tzinfo=timezone.utc)
    n = int(wake.timestamp())
    panel, bars = {}, {}
    moves = {"BTC": 0.97, "ETH": 0.90, "SOL": 0.92, "ADA": 0.99}
    for coin in bx.COINS:
        f = moves.get(coin, 1.0)
        cs = [100.0, 100.0 * (1 + (f - 1) / 2), 100.0 * f]
        panel[coin] = {(n - (3 - i) * 3600) * 1000: (100, 101, 1, cs[i], 10) for i in range(3)}
        bars[coin] = {n - (3 - i) * 3600: (100, 101, 1, cs[i], 10) for i in range(3)}
    q, best, btc = d.f_filter(panel, list(bx.COINS), wake, 2, 0.015, 2.0, 2)
    assert best == e12.decide(wake, bars, rule, tuple(bx.COINS))[0] == "ETH"
    assert [c for c, _ in q] == ["ETH", "SOL"]


# ------------------------------------------------------------------ marks and published fields
def test_judge_marks():
    cfg = {"cards": {"W": {"judging_count": 60, "judging_floor": 30}, "S": {"judging_count": 240, "judging_floor": 120}},
           "trim_best": 2, "t_mark": 2.0}
    few = [{"wake": "2027-01-01T00:00:00Z", "diff": 0.01, "scout_net": 0.01}] * 10
    assert d.judge(few, cfg, "W")["verdict"] == "too few to judge"
    good = [{"wake": f"2027-01-{1 + i % 28:02d}T00:00:00Z", "diff": 0.01 + 0.001 * (i % 3), "scout_net": 0.02}
            for i in range(60)]
    out = d.judge(good, cfg, "W")
    assert out["verdict"] == "pass" and out["pairs"] == 60
    bad = [dict(p, scout_net=-0.01) for p in good]
    assert d.judge(bad, cfg, "W")["marks"]["scout_own_mean_above_zero"] is False


def test_public_counts_only_and_dashboard_label(lab, tmp_path):
    clock = at(0)
    pages = Pages(clock, last={"ETH": "94"})
    run(lab, pages, clock, Scout(pages, clock))
    target = tmp_path / "pub.json"
    out = d.publish(lab[0], target, now=clock())
    text = target.read_text()
    for word in ("ETH", "net", "price", "bid", "ask"):
        assert word not in text
    dash = json.loads((lab[0] / d.DASH_NAME).read_text())
    assert dash["S"]["label"] == "not judged yet; nothing about this card changes before its judging count"
    assert "closed" not in dash["W"] and "open" not in dash["W"]


def test_gate_stop_mid_wake_makes_no_scout_call(lab):
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94"}, fail={("klines", "ZEC"): lambda: bx.Blocked(bx.HOST, 418)})
    scout = Scout(pages, clock)
    out = run(lab, pages, clock, scout)
    assert out["kind"] == "stop" and out["http_status"] == 418
    assert scout.seen == []
    assert not any(k == "book" for k, _, _ in pages.calls)


def test_unreadable_shared_file_refusal_stops_with_record(lab):
    clock = at(1)
    pages = Pages(clock, fail={("pairs", None): lambda: bx.Refuse("cooldown file is not valid JSON")})
    out = run(lab, pages, clock, Scout(pages, clock))
    assert out["kind"] == "stop" and out["reason"] == "gate_refused"
    assert rows(lab)[-1]["kind"] == "stop"


def test_stop_during_entry_books_voids_cached_fills(lab):
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94", "ADA": "92"}, fail={("book", "ADA"): lambda: bx.Blocked(bx.HOST, 418)})
    n = {"k": 0}
    orig = pages._hit

    def hit(kind, coin=None):
        if kind == "book":
            n["k"] += 1
            if n["k"] <= 2:                   # the pre-decision books work
                pages.calls.append((kind, coin, clock()))
                return
        orig(kind, coin)
    pages._hit = hit
    out = run(lab, pages, clock, Scout(pages, clock, picks={("W", SMALL): "ETH"}))
    assert out["kind"] == "stop"
    sig = [r for r in rows(lab) if r["kind"] == "wake"][-1]["signals"]["W"]
    # processed in line order: scout (ETH, book before the stop) stays a committed entry, rule (ADA) hits the
    # stop, random is fenced even though an ETH book is already in hand
    assert sig["choices"]["scout"] == "ETH" and sig["entries"]["scout"]["status"] == "ok"
    assert sig["entries"]["rule"]["status"] != "ok"
    assert sig["entries"]["random"]["status"] == "gate_stopped"


def test_stop_during_exit_books_keeps_tickets_open(lab):
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94"})
    run(lab, pages, clock, Scout(pages, clock))
    clock = at(25)
    pages = Pages(clock, fail={("book", "ETH"): lambda: bx.Blocked(bx.HOST, 403)})
    out = run(lab, pages, clock, Scout(pages, clock))
    assert out["kind"] == "stop"
    assert not any(k == "pairs" for k, _, _ in pages.calls)
    w = [r for r in rows(lab) if r["kind"] == "wake"][-1]
    assert w["exits"] and all(x["status"] == "gate_stopped" and not x["final"] for x in w["exits"])


def test_changed_gate_setting_is_refused_after_start(lab, monkeypatch):
    import gate
    real = gate.settings

    def changed(*a, **k):
        g = real(*a, **k)
        g["practice_e17_w_min_fall"] = 0.09
        return g
    monkeypatch.setattr(gate, "settings", changed)
    clock = at(1)
    pages = Pages(clock)
    with pytest.raises(bx.Refuse):
        run(lab, pages, clock, Scout(pages, clock))
    assert pages.calls == []


def test_no_time_is_not_a_call_and_not_a_failure(lab):
    clock = at(1, 1430)                       # 60 s to the cutoff: less than entry reserve plus scout_min_s
    pages = Pages(clock, last={"ETH": "94"})
    scout = Scout(pages, clock)
    run(lab, pages, clock, scout)
    assert scout.seen == []
    r = rows(lab)
    assert not any(x["kind"] == "scout_call" for x in r)
    ix = d.state(r, lab[1])
    assert d.failed_calls(ix, 20) == (0, 0)
    assert [x for x in r if x["kind"] == "wake"][-1]["signals"]["W"]["entries"]["scout"]["status"] == "scout_no_time"


def test_exit_retry_capped_at_last_exit_wake(tmp_path, monkeypatch):
    monkeypatch.setattr(bx, "private_roots", lambda: (tmp_path,))
    monkeypatch.setattr(e14, "require_go", lambda *a, **k: None)
    real = d.settings

    def short():
        c = real()
        c["ledger_row"] = 999
        c["cards"]["S"]["cost_limit_bp"] = 20
        c["not_before_utc"] = "2026-01-01T00:00:00Z"
        c["cards"]["W"]["last_wake_utc"] = bx.iso(T0 + timedelta(hours=25))
        return c
    monkeypatch.setattr(d, "settings", short)
    p = tmp_path / "lab"
    p.mkdir(mode=0o700)
    with bx.locked(p) as path:
        r = []
        bx.write_anchor(path, bx.anchor_state(r))
        bx.append(path, r, kind="header", first=bx.iso(T0), venue_generation=0, freeze=BUILD, frozen=d.frozen(short()))
    lab = (p, short())
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94"})
    run(lab, pages, clock, Scout(pages, clock))
    clock = at(25)                                      # the last exit wake: a lost exit book is final and void
    pages = Pages(clock, fail={("book", "ETH"): bx.Failure("shared_cooldown")})
    out = run(lab, pages, clock, Scout(pages, clock))
    assert out["exits"] and all(x["final"] and x["status"] != "ok" for x in out["exits"])
    clock = at(26)
    pages = Pages(clock)
    out = run(lab, pages, clock, Scout(pages, clock))
    assert not any(k == "book" and c == "ETH" for k, c, _ in pages.calls)
    assert not d.state(rows(lab), lab[1])["open"].get(("W", "rule"))


def test_frozen_input_changed_during_wake_stops(lab, monkeypatch):
    import gate
    real = gate.settings
    n = {"k": 0}

    def drift(*a, **k):
        n["k"] += 1
        g = real(*a, **k)
        if n["k"] > 1:
            g["practice_e17_w_min_fall"] = 0.09
        return g
    monkeypatch.setattr(gate, "settings", drift)
    clock = at(1)
    pages = Pages(clock)
    out = run(lab, pages, clock, Scout(pages, clock))
    assert out["kind"] == "stop" and out["reason"] == "frozen_inputs_changed"


def test_gate_in_use_must_be_the_frozen_gate(lab):
    clock = at(1)
    pages = Pages(clock)
    pages.gate = type("G", (), {"cooldown_path": "/tmp/some/other/cooldown.json"})()
    with pytest.raises(bx.Refuse):
        run(lab, pages, clock, Scout(pages, clock))
    assert pages.calls == []
    pages = Pages(clock)
    pages.gate = type("G", (), {"cooldown_path": lab[1]["gate_custody"]["cooldown_path"]})()
    assert run(lab, pages, clock, Scout(pages, clock))["kind"] == "wake"


def test_fenced_exit_is_final_at_last_exit_wake(lab, monkeypatch):
    cfg = dict(lab[1])
    cfg["cards"] = {k: dict(v) for k, v in cfg["cards"].items()}
    cfg["cards"]["W"]["last_wake_utc"] = bx.iso(T0 + timedelta(hours=25))
    assert d.exit_final(cfg, "W", 1, T0 + timedelta(hours=25))
    clock = at(1)
    pages = Pages(clock, last={"ETH": "94", "ADA": "92"})
    run(lab, pages, clock, Scout(pages, clock))
    # a stop on the first exit book fences the rest; with the cap reached they must be final
    monkeypatch.setattr(d, "exit_final", lambda c, card, a, w: True)
    clock = at(25)
    pages = Pages(clock, fail={("book", "ADA"): lambda: bx.Blocked(bx.HOST, 418)})
    run(lab, pages, clock, Scout(pages, clock))
    w = [r for r in rows(lab) if r["kind"] == "wake"][-1]
    assert any(x["status"] == "gate_stopped" for x in w["exits"])
    assert all(x["final"] for x in w["exits"])
