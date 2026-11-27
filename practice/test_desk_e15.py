"""Card E15 on made-up candles, made-up books, a fake clock and a fake model. No venue, no model, no live gate."""
import asyncio
import json
from datetime import datetime, timedelta, timezone

import pytest

import desk_e15 as d
import forward_e14 as e14
import venue_binance_us as bx

SMALL = "gpt5_mini"
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


@pytest.fixture
def lab(tmp_path, monkeypatch):
    monkeypatch.setattr(bx, "private_roots", lambda: (tmp_path,))
    monkeypatch.setattr(e14, "require_go", lambda *a, **k: None)
    monkeypatch.setattr(bx, "check_start", lambda *a, **k: pytest.fail("live gate forbidden"))
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
        bx.append(path, rows, kind="header", first=bx.iso(T0), venue_generation=0, freeze="<test>", frozen=d.frozen(cfg()))
    return p, cfg()


def run(lab, pages, clock, scout):
    return d.record(pages, lab[0], clock, clock.sleep, clock.mono, scout)


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
    assert cfg["not_before_utc"] == "2026-11-28T01:00:00Z"
    assert d.first_wake(datetime(2026, 11, 27, 22, 0, tzinfo=timezone.utc), cfg) == datetime(2026, 11, 28, 1, tzinfo=timezone.utc)
    assert d.first_wake(datetime(2026, 11, 28, 1, 21, tzinfo=timezone.utc), cfg) == datetime(2026, 11, 28, 2, tzinfo=timezone.utc)


def test_unset_required_settings_refuse():
    cfg = d.settings()
    with pytest.raises(bx.Refuse):
        d.required(cfg)


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
    assert d.run_scouts(jobs, slow, 0.05, 10)["k"]["status"] == "call_timeout"
    assert d.run_scouts(jobs, cut, 1, 10)["k"]["status"] == "reply_incomplete"


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
        g["practice_e15_w_min_fall"] = 0.09
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
        bx.append(path, r, kind="header", first=bx.iso(T0), venue_generation=0, freeze="<test>", frozen=d.frozen(short()))
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
            g["practice_e15_w_min_fall"] = 0.09
        return g
    monkeypatch.setattr(gate, "settings", drift)
    clock = at(1)
    pages = Pages(clock)
    out = run(lab, pages, clock, Scout(pages, clock))
    assert out["kind"] == "stop" and out["reason"] == "frozen_inputs_changed"
