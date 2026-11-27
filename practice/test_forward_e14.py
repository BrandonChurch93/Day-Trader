"""Invented books, fake time and private temporary files only."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json

import pytest

import forward_e14 as e
import venue_binance_us as bx

W = datetime(2027, 1, 1, tzinfo=timezone.utc)


class Clock:
    def __init__(self, wake=W, offset=195):
        self.t = wake + timedelta(seconds=offset)

    def __call__(self):
        return self.t

    def sleep(self, seconds):
        self.t += timedelta(seconds=seconds)


def depth(ask="101", bid="99", size="100"):
    return {"asks": [[ask, size]], "bids": [[bid, size]]}


def candles(wake, first, last):
    end = bx.epoch_ms(wake)
    out = []
    for i, price in enumerate((first, last), 1):
        stamp = end - (3 - i) * bx.HOUR_MS
        out.append([stamp, price, price, price, price, "1", stamp + bx.HOUR_MS - 1, None, None, None, None, None])
    return out


class Pages:
    def __init__(self, cfg, *, count=None, falls=None, books=(), missing=()):
        selected = cfg["coins"][:count]
        self.states = {c: "TRADING" if c in selected else "NO_USD_PAIR" for c in cfg["coins"]}
        self.falls = falls or {}
        self.books = iter(books)
        self.calls = []
        self.missing = missing

    def pairs(self):
        self.calls.append(("pairs",))
        return self.states

    def klines(self, coin, wake, n):
        self.calls.append(("candles", coin))
        assert n == 2
        rows = candles(wake, "100", self.falls.get(coin, "100"))
        return rows[:1] if coin in self.missing else rows

    def book(self, venue, coin):
        assert venue == bx.VENUE
        self.calls.append(("book", coin))
        item = next(self.books)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture
def lab(tmp_path, monkeypatch):
    monkeypatch.setattr(bx, "private_roots", lambda: (tmp_path,))
    monkeypatch.setattr(bx, "require_go", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(bx, "check_start", lambda *_args, **_kwargs: pytest.fail("live gate forbidden"))
    p = tmp_path / "lab"
    p.mkdir(mode=0o700)
    cfg = e.settings()
    with bx.locked(p) as path:
        rows = []
        bx.write_anchor(path, bx.anchor_state(rows))
        bx.append(path, rows, kind="header", first=bx.iso(W), venue_generation=0, freeze="<test build>",
                  frozen=e.frozen(cfg))
    return p, cfg


def wake(lab, source, hour=0, offset=195):
    clock = Clock(W + hour * bx.HOUR, offset)
    return e.record(clock(), source, lab[0], clock, clock.sleep)


def test_rules_and_exact_ties():
    cfg = e.settings()
    assert (cfg["drops"], cfg["hold_hours"], cfg["fee_bp"], cfg["sizes"]) == (
        {"primary": .05, "alternate": .035}, 24, 2, {"judged": 250, "shown": 25})
    data = {"AAA": ("20", "19"), "BBB": ("100", "95"), "CCC": ("100", "95.000000000000000000001")}
    assert e.choose(data, ["CCC", "BBB", "AAA"], .05) == "BBB"
    assert e.choose(data, ["CCC"], .05) is None
    assert e.choose({"AAA": ("100", "96.5")}, ["AAA"], .035) == "AAA"
    assert e.choose({"AAA": ("100", "95"), "BBB": ("100", "94")}, ["AAA", "BBB"], .05) == "BBB"


def test_candle_alignment_and_current_ignored():
    rows = candles(W, "100", "95")
    current = candles(W + bx.HOUR, "95", "1")[-1]
    assert len(bx.closed_klines(rows + [current], W, 2)) == 2
    for bad in ([*rows, rows[0]], [rows[0], current]):
        with pytest.raises(bx.Failure):
            bx.closed_klines(bad, W, 2)


def test_roster_failed_first_stops(lab):
    src = Pages(lab[1], count=5)
    assert wake(lab, src, offset=194)["kind"] == "nothing due"
    assert not src.calls
    assert wake(lab, src)["reason"] == "too_few_usd_pairs"
    other = Pages(lab[1])
    assert wake(lab, other, hour=1)["kind"] == "stopped"
    assert not other.calls


def test_missing_initial_wake_cannot_freeze_later(lab):
    src = Pages(lab[1])
    assert wake(lab, src, hour=1)["reason"] == "first_wake_roster_unavailable"
    assert not src.calls


def test_first_book_and_frozen_roster(lab):
    src = Pages(lab[1], count=6, falls={"AAVE": "95", "ADA": "94"}, books=[depth()])
    first = wake(lab, src)
    assert first["decisions"] == {e.PRIMARY: "ADA", e.ALT: "ADA"}
    assert src.calls == [("pairs",)] + [("candles", c) for c in lab[1]["coins"][:6]] + [("book", "ADA")]
    next_src = Pages(lab[1], count=11, falls={"XRP": "1", "AAVE": "1"}, books=[depth()])
    later = wake(lab, next_src, hour=1)
    assert later["entries"][e.LATE]["parent"] == first["wake"]
    assert later["entries"][e.LATE]["due"] == first["entries"][e.PRIMARY]["due"]
    assert not later["decisions"]
    assert next_src.calls == [("book", "ADA")]
    assert e.summary(bx.read_log(lab[0]))["frozen_pairs"] == 6


def test_exit_then_rank_and_separate_fresh_entry(lab):
    first = Pages(lab[1], falls={"BTC": "90"}, books=[depth()])
    wake(lab, first)
    delay = Pages(lab[1], books=[depth("110", "109")])
    wake(lab, delay, hour=1)
    exit_and_reenter = Pages(lab[1], falls={"BTC": "90"},
                             books=[depth("130", "120"), depth("103", "100"), depth("104", "100")])
    row = wake(lab, exit_and_reenter, hour=24)
    assert exit_and_reenter.calls[0] == ("book", "BTC")
    assert exit_and_reenter.calls[-2:] == [("book", "BTC"), ("book", "BTC")]
    assert len(row["exits"]) == len(row["entries"]) + 1 == 4
    assert row["entries"][e.PRIMARY]["book"]["ask"] == "103"
    assert row["entries"][e.ALT]["book"]["ask"] == "104"
    assert row["exits"][e.PRIMARY]["net"] == pytest.approx(120 / 101 * .9998 - 1.0002)
    assert row["exits"][e.LATE]["net"] == pytest.approx(120 / 110 * .9998 - 1.0002)


def test_missing_rank_does_not_void_exit(lab):
    wake(lab, Pages(lab[1], falls={"XRP": "20"}, books=[depth()]))
    src = Pages(lab[1], falls={"AAVE": "1"}, missing=["XRP"], books=[depth()])
    result = wake(lab, src, hour=24)
    assert result["exits"][e.PRIMARY]["status"] == "ok"
    assert result["candle_errors"] == {"XRP": "missing_adjacent_candle"}
    assert not result["entries"]
    assert src.calls.count(("book", "XRP")) == 1


def test_small_can_close_on_failed_main_walk(lab):
    src = Pages(lab[1], falls={"BTC": "90", "ETH": "94"}, books=[depth(size=".4")])
    row = wake(lab, src)
    assert row["entries"][e.PRIMARY]["status"] == "entry too thin"
    assert row["entries"][e.SMALL]["status"] == "ok"
    assert src.calls[-1] == ("book", "BTC") and ("book", "ETH") not in src.calls
    another = wake(lab, Pages(lab[1], falls={"ETH": "94"}, books=[depth()]), hour=1)
    assert another["entries"][e.PRIMARY]["coin"] == "ETH"
    assert e.LATE not in another["entries"]
    src = Pages(lab[1], books=[depth()])
    result = wake(lab, src, hour=24)
    assert list(result["exits"]) == [e.SMALL]
    assert src.calls == [("book", "BTC")]


def test_alternate_does_not_block_main(lab):
    alt = wake(lab, Pages(lab[1], falls={"ADA": "96"}, books=[depth()]))
    assert set(alt["entries"]) == {e.ALT}
    main = wake(lab, Pages(lab[1], falls={"BTC": "90"}, books=[depth()]), hour=1)
    assert set(main["entries"]) == {e.PRIMARY, e.SMALL}
    assert main["busy_arms"] == [e.ALT]


def test_shown_terminal_does_not_erase_completed_primary_entry(lab):
    wake(lab, Pages(lab[1], falls={"ADA": "96"}, books=[depth()]))
    blocked = bx.Blocked(bx.HOST, 403)
    src = Pages(lab[1], falls={"ETH": "90"}, books=[depth(), blocked])
    hit = wake(lab, src, hour=24)
    assert hit["kind"] == "stop" and hit["http_status"] == 403
    assert e.summary(bx.read_log(lab[0]))["valid_entries"][e.PRIMARY] == 1
    assert src.calls[-2:] == [("book", "ETH"), ("book", "ADA")]
    assert wake(lab, src, hour=25)["kind"] == "stopped"


def test_missed_delayed_and_void_exit_are_not_retried(lab):
    wake(lab, Pages(lab[1], falls={"BTC": "90"}, books=[depth()]))
    result = wake(lab, Pages(lab[1]), hour=2)
    assert result["kind"] == "wake"
    src = Pages(lab[1], falls={"BTC": "90"}, books=[bx.Failure("http_404"), depth(), depth()])
    row = wake(lab, src, hour=24)
    assert row["exits"][e.PRIMARY]["status"] == "http_404"
    assert row["entries"][e.PRIMARY]["status"] == "ok"
    assert src.calls.count(("book", "BTC")) == 3
    rows = bx.read_log(lab[0])
    assert e.summary(rows)["void_tickets"][e.LATE] == {"missed_wake": 1}


@pytest.mark.parametrize("offset,elapsed", [(195, 20), (283, 7)])
def test_busy_retry_is_bounded_by_first_attempt_and_cutoff(offset, elapsed):
    clock = Clock(offset=offset)
    begin = clock()
    cfg = e.settings()
    src = Pages(cfg)
    attempts = []

    def busy():
        attempts.append(clock())
        raise bx.Failure("shared_gate_busy")

    with pytest.raises(bx.Failure, match="shared_gate_busy"):
        e.request(src, busy, W + timedelta(seconds=290), clock, clock.sleep, 20)
    assert (clock() - begin).total_seconds() == elapsed
    assert len(attempts) > 1 and attempts[-1] < clock()


def test_only_busy_retries_inside_hard_window():
    clock = Clock(offset=287)
    src = Pages(e.settings())
    until = W + timedelta(seconds=290)
    attempted = []

    def fetch():
        attempted.append(clock())
        if len(attempted) == 1:
            raise bx.Failure("shared_gate_busy")
        clock.sleep(2.75)
        return depth()

    assert e.request(src, fetch, until, clock, clock.sleep, 20) == depth()
    assert clock() == until
    clock = Clock(offset=289)

    def late():
        clock.sleep(2)
        return depth()

    with pytest.raises(bx.Failure, match="late book"):
        e.request(src, late, until, clock, clock.sleep, 20)
    clock = Clock()
    attempts = []

    def cooled():
        attempts.append(1)
        raise bx.Cooldown(clock() + timedelta(seconds=2))

    with pytest.raises(bx.Cooldown):
        e.request(src, cooled, until, clock, clock.sleep, 20)
    assert attempts == [1]


def test_walks_two_levels_and_exact_base():
    base, usd = e.walk([["100", "1"], ["150", "3"]], 250, buy=True)
    assert (base, usd) == (Decimal(2), Decimal(250))
    assert e.walk([["200", "1"], ["175", "4"]], str(base), buy=False) == (Decimal(2), Decimal(375))
    assert e.walk([["150", "1"]], 250, buy=True) is None


def test_cost_sample_and_isolated_gate(monkeypatch):
    cfg = e.settings()
    samples = [{"status": "ok", "entry_cost_bp": str(i)} for i in range(1, 23)]
    samples[0] = {"status": "entry too thin"}
    assert e.costs(samples, 20) == {
        "first_books": 20, "full_walks": 19, "missing_walks": 1,
        "mean_bp": 11.0, "median_bp": 11.0, "p90_bp": 19.0,
    }
    seen = []
    monkeypatch.setattr(bx, "require_go", lambda *args: seen.append(args))
    h = {"freeze": "<test build>"}
    ix = {"books": samples[:19], "closed": {e.PRIMARY: []}}
    with pytest.raises(bx.Refuse, match="not enough"):
        e.read_gate([], h, ix, cfg, "cost", W)
    ix["books"] = samples[:20]
    e.read_gate([], h, ix, cfg, "cost", W)
    assert seen == [(233, "E14_COST", h["freeze"])]
    with pytest.raises(bx.Refuse, match="already read"):
        e.read_gate([{"kind": "cost"}], h, ix, cfg, "cost", W)
    with pytest.raises(bx.Refuse, match="has not arrived"):
        e.read_gate([{"kind": "cost"}], h, ix, cfg, "score", W)
    ix["closed"][e.PRIMARY] = [{"status": "ok"}] * 60
    e.read_gate([{"kind": "cost"}], h, ix, cfg, "score", W)
    assert seen[-1][1] == "E14_SCORE"


def test_clustered_marks():
    cfg = e.settings()
    closes = [{"status": "ok", "net": .01 + (i % 5) / 1000,
               "entry_wake": bx.iso(W + timedelta(days=i // 2, hours=i % 2))} for i in range(61)]
    assert e.judge(closes[:29], cfg)["verdict"] == "too few to judge"
    closes[-1]["net"] = -9
    passed = e.judge(closes, cfg)
    assert passed["verdict"] == "pass" and passed["trades"] == 60 and passed["entry_days"] == 30
    assert e.cluster_t([1, 3, 2, 6], [0, 0, 1, 1]) == pytest.approx(3)
    assert e.cluster_t([1, 1], [0, 1]) is None
    closes = [r | {"net": -.0001} for r in closes[:30]]
    closes[-2:] = [r | {"net": 2} for r in closes[-2:]]
    assert not e.judge(closes, cfg)["marks"]["positive_without_best"]


def test_final_date_entry_cutoff_and_scoring_boundary(lab, monkeypatch):
    cfg = lab[1] | {"last_wake_utc": bx.iso(W + 24 * bx.HOUR)}
    monkeypatch.setattr(e, "settings", lambda: cfg)
    rows = bx.read_log(lab[0])
    src = Pages(cfg, falls={"BTC": "90"}, books=[depth()])
    clock = Clock()
    first = e.capture(lab[0], rows, src, W, cfg["coins"], e.state(rows), cfg, clock, clock.sleep)
    assert first["entries"][e.PRIMARY]["due"] == cfg["last_wake_utc"]
    clock.t += 2 * bx.HOUR
    assert not e.capture(lab[0], rows, src, W + 2 * bx.HOUR, cfg["coins"],
                         e.state(rows), cfg, clock, clock.sleep)["entries"]
    stop_time = bx.parse(cfg["last_wake_utc"]) + timedelta(seconds=290)
    with pytest.raises(bx.Refuse, match="has not arrived"):
        e.read_gate(rows, {"freeze": "<test build>"}, e.state(rows), cfg, "score", stop_time)
    e.read_gate(rows, {"freeze": "<test build>"}, e.state(rows), cfg, "score",
                stop_time + timedelta(microseconds=1))


def test_target_close_does_not_start_another_ticket(lab):
    cfg = lab[1] | {"judging_count": 1}
    rows = bx.read_log(lab[0])
    clock = Clock()
    e.capture(lab[0], rows, Pages(cfg, falls={"BTC": "90"}, books=[depth()]), W,
              cfg["coins"], e.state(rows), cfg, clock, clock.sleep)
    clock.t += 24 * bx.HOUR
    src = Pages(cfg, falls={"BTC": "90"}, books=[depth()])
    row = e.capture(lab[0], rows, src, W + 24 * bx.HOUR, cfg["coins"], e.state(rows),
                    cfg, clock, clock.sleep)
    assert row["exits"][e.PRIMARY]["status"] == "ok"
    assert row["judging_point"]
    assert not row["entries"] and not row["decisions"]
    assert src.calls == [("book", "BTC")]


def test_interrupted_claim_not_fetched_again(lab):
    wake(lab, Pages(lab[1]))
    with bx.locked(lab[0]) as path:
        rows = bx.read_log(path)
        bx.append(path, rows, kind="claim", wake=bx.iso(W + bx.HOUR))
    src = Pages(lab[1], falls={"BTC": "1"})
    wake(lab, src, hour=1)
    assert not src.calls
    assert e.summary(bx.read_log(lab[0]))["wake_void_reasons"] == {"interrupted_wake": 1}


def test_bound_generation_stop_precedes_missing_approval(lab, monkeypatch):
    class FakeGate:
        def check_start(self, *, generation):
            assert generation == 0
            raise bx.GateGeneration()

    monkeypatch.setattr(bx, "require_go", lambda *_args: pytest.fail("gate stop takes precedence"))
    clock = Clock()
    pages = bx.PublicPages(opener=object(), gate=FakeGate(), clock=clock, sleep=clock.sleep)
    row = e.record(clock(), pages, lab[0], clock, clock.sleep)
    assert row["reason"] == "gate_generation"


def test_generation_approval_keys(monkeypatch):
    fake = object()
    seen = []
    monkeypatch.setattr(bx, "check_start", lambda gate: 4 if gate is fake else pytest.fail("real gate forbidden"))
    monkeypatch.setattr(bx, "require_go", lambda *a, **kw: seen.append((a, kw)))
    assert e.start_gate("<test build>", fake) == 4
    assert seen == [((233, "E14_START", "<test build>"), {}),
                    ((233, "E14_START", "<test build>"), {"generation": 4})]


def test_public_counts_only_and_anchor_refuses_rollback(lab, tmp_path):
    p, cfg = lab
    assert json.loads(e.PUBLIC.read_text()) == json.loads(json.dumps(e.summary([])))
    wake(lab, Pages(cfg, falls={"BTC": "90"}, books=[depth()]))
    pub = tmp_path / "public.json"
    e.publish(p, pub)
    raw = pub.read_text()
    doc = json.loads(raw)
    assert doc["first_primary_books"] == 1 and doc["valid_entries"][e.PRIMARY] == 1
    for item in ("BTC", "95", "101", "asks", "entry_cost_bp", "net_mean", "<test build>"):
        assert item not in raw
    ledger = p / "log.jsonl"
    lines = ledger.read_bytes().splitlines(keepends=True)
    ledger.write_bytes(b"".join(lines[:-1]))
    with pytest.raises(bx.Refuse):
        e.alive(p)
