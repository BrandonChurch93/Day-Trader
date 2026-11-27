"""Invented books and a simulated UTC clock. No venue transport is used."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import io
import json
import stat
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

import measure_136 as m

H = datetime(2027, 1, 1, 23, tzinfo=timezone.utc)


class FakeClock:
    def __init__(self, start=H + timedelta(minutes=19)):
        self.utc, self.elapsed, self.sleeps = start, 0, []

    def clock(self):
        return self.utc

    def mono(self):
        return self.elapsed

    def sleep(self, step):
        assert 0 < step <= 1
        self.sleeps.append(step)
        self.utc += timedelta(seconds=step)
        self.elapsed += step


def raw_book():
    return {"lastUpdateId": 123, "bids": [["99", "1"], ["98", "19"]],
            "asks": [["101", "1"], ["102", "19"]]}


def response(value, status=200):
    r = io.BytesIO(json.dumps(value).encode())
    r.status = status
    return r


class FakeOpener:
    def __init__(self, clock, answers=None):
        self.clock, self.calls = clock, []
        self.answers = answers

    def open(self, req, *, timeout):
        self.calls.append((self.clock.clock(), self.clock.mono(), req.full_url))
        assert timeout == 5 and req.get_method() == "GET"
        assert not any("key" in name.lower() for name, _ in req.header_items())
        if self.answers is None:
            return response(raw_book())
        answer = next(self.answers)
        if isinstance(answer, Exception):
            raise answer
        return answer


def client(clock, opener):
    return m.DepthClient(opener, clock.clock, clock.mono, clock.sleep)


def test_walk_buy_and_sell_use_fixed_usd_notional():
    raw = raw_book()
    gap, costs = m.book_metrics(raw)
    d = Decimal
    expected_buy = d(250) / (1 + (d(250) - 101) / 102)
    expected_sell = d(250) / (1 + (d(250) - 99) / 98)
    assert gap == d(200)
    assert costs[25] == {"buy": d(100), "sell": d(100)}
    assert costs[250]["buy"] == (expected_buy - 100) * 100
    assert costs[250]["sell"] == (100 - expected_sell) * 100
    assert m.FEE_BP == 2  # reported separately, not added


def test_thin_side_records_cannot_fill_but_keeps_other_side():
    raw = raw_book()
    raw["asks"] = [["101", "1"]]
    gap, costs = m.book_metrics(raw)
    assert costs[250]["buy"] is None and costs[250]["sell"] is not None
    assert costs[1000]["buy"] is None and costs[1000]["sell"] is not None
    assert costs[25]["buy"] == Decimal(100)
    assert m.stored_metrics(gap, costs)["sizes_usd"]["250"]["buy"] == {"status": "cannot_fill"}


@pytest.mark.parametrize(
    "start,first",
    [(H + timedelta(minutes=19), H + timedelta(minutes=20)),
     (H + timedelta(minutes=19, microseconds=1), H + timedelta(hours=1, minutes=20)),
     (H + timedelta(minutes=21), H + timedelta(hours=1, minutes=20)),
     (H + timedelta(minutes=59), H + timedelta(hours=1, minutes=20))],
)
def test_first_complete_block_has_four_slots_in_each_hour(start, first):
    actual = m.slots(start)
    assert len(actual) == 8 and actual[0] == first
    assert tuple(t.minute for t in actual) == (20, 30, 40, 50) * 2
    assert actual[4] == first + timedelta(hours=1)


def test_wait_uses_short_steps_and_rechecks_wall_clock():
    clock = FakeClock(H + timedelta(minutes=19, seconds=57.5))
    slot = H + timedelta(minutes=20)
    m.wait_for(slot, clock.clock, clock.sleep)
    assert clock.sleeps == [1, 1, 0.5]
    assert clock.clock() == slot


@pytest.mark.parametrize("minute", [17, 57])
def test_refuses_outside_request_minutes_without_opening(minute):
    clock = FakeClock(H + timedelta(minutes=minute))
    opener = FakeOpener(clock)
    with pytest.raises(m.Refuse, match="outside the UTC minute"):
        client(clock, opener).book("BTC", H + timedelta(minutes=20))
    assert not opener.calls


def test_no_late_catch_up_even_inside_the_global_window():
    clock = FakeClock(H + timedelta(minutes=23))
    opener = FakeOpener(clock)
    with pytest.raises(m.Refuse, match="scheduled snapshot slot"):
        client(clock, opener).book("BTC", H + timedelta(minutes=20))
    assert not opener.calls


def test_clock_checked_again_after_pacing_delay():
    clock = FakeClock(H + timedelta(minutes=22, seconds=59.5))
    opener = FakeOpener(clock)
    c = client(clock, opener)
    slot = H + timedelta(minutes=20)
    c.book("BTC", slot)
    with pytest.raises(m.Refuse, match="scheduled snapshot slot"):
        c.book("ETH", slot)
    assert len(opener.calls) == 1


@pytest.mark.parametrize(
    "bad,reason",
    [
        (lambda: response({}, 429), "HTTP 429"),
        (lambda: HTTPError(m.ENDPOINT, 403, "invented refusal", {}, None), "HTTP 403"),
        (lambda: TimeoutError(), "timeout"),
        (lambda: response({"bids": [["99", "1"]], "asks": [["98", "2"]]}), "malformed book"),
        (lambda: response({"bids": [["99", "1"]], "asks": []}), "malformed book"),
    ],
)
def test_bad_reply_ends_whole_attempt_and_is_not_retried(tmp_path, bad, reason):
    off = tmp_path / "measure_136"
    clock = FakeClock()
    opener = FakeOpener(clock, iter((response(raw_book()), bad(), response(raw_book()))))
    with pytest.raises(m.Refuse, match=reason):
        m.capture(off, client(clock, opener), clock.clock, clock.sleep)
    assert len(opener.calls) == 2
    summary = m.report(off)
    assert summary["status"] == "stopped" and reason in summary["stop_reason"]
    assert summary["snapshots_taken"] == 1 and summary["snapshots_complete"] == 0
    assert summary["books_taken"] == 1
    with pytest.raises(m.Refuse, match="already attempted"):
        m.capture(off, client(clock, opener), clock.clock, clock.sleep)
    assert len(opener.calls) == 2


def test_complete_invented_capture_rates_routes_custody_and_report(tmp_path):
    off = tmp_path / "measure_136"
    clock = FakeClock()
    opener = FakeOpener(clock)
    m.capture(off, client(clock, opener), clock.clock, clock.sleep)
    assert len(opener.calls) == 160
    assert all(new[1] - old[1] >= 1 for old, new in zip(opener.calls, opener.calls[1:]))
    assert {when.minute for when, _, _ in opener.calls} == {20, 30, 40, 50}
    assert {when.hour for when, _, _ in opener.calls} == {23, 0}
    for _, _, url in opener.calls:
        parsed = urlsplit(url)
        assert (parsed.scheme, parsed.netloc, parsed.path) == ("https", "api.binance.us", "/api/v3/depth")
        assert parse_qs(parsed.query)["limit"] == ["100"]
    assert {parse_qs(urlsplit(url).query)["symbol"][0] for _, _, url in opener.calls} == {
        coin + "USD" for coin in m.COINS}
    journal = off / m.RAW_NAME
    assert stat.S_IMODE(off.stat().st_mode) == 0o700 and stat.S_IMODE(journal.stat().st_mode) == 0o600
    assert "lastUpdateId" in journal.read_text()
    result = m.report(off)
    assert result["snapshots_taken"] == result["snapshots_complete"] == 8
    assert result["books_taken"] == 160 and result["status"] == "complete"
    assert result["stated_fee_bp_per_side_not_in_costs"] == 2
    assert "midnight UTC" in result["scope"] and "fast markets" in result["scope"]
    assert all(x["coins_with_both_side_medians"] == 20 and x["coins_at_or_below_25_bp"] == 0
               for x in result["by_size_usd"].values())
    assert not any(k in json.dumps(result) for k in ('"raw"', '"received"', '"bids"', '"asks"', "lastUpdateId"))


def test_headline_worse_of_two_medians_and_missing_not_zero():
    started = H + timedelta(minutes=19)
    plan = [m.iso(t) for t in m.slots(started)]
    rows = [{"kind": "header", "slots": plan, "started": m.iso(started), "symbols": list(m.COINS)}]
    rich = {"bids": [["99.98", "20"]], "asks": [["100.02", "20"]]}
    thin = rich | {"asks": [["100.02", "0.5"]]}
    for stamp, raw in zip(plan, (rich, thin)):
        rows.append({"kind": "book", "slot": stamp, "received": stamp, "symbol": "BTC", "raw": raw,
                     "measured": m.stored_metrics(*m.book_metrics(raw))})
    rows.append({"kind": "book", "slot": plan[0], "received": plan[0], "symbol": "ETH", "raw": thin,
                 "measured": m.stored_metrics(*m.book_metrics(thin))})
    summary = m.summarize(rows)
    metrics = summary["by_size_usd"][250]
    assert metrics["coins_at_or_below_25_bp"] == metrics["coins_with_both_side_medians"] == 1
    assert metrics["across_coins_median_worse_side_bp"] == 2
    assert metrics["cannot_fill"] == {"buy": 2, "sell": 0}
    assert summary["by_symbol"]["ETHUSD"]["costs_by_size_usd"][250]["median_buy_bp"] is None
    assert summary["by_symbol"]["ETHUSD"]["costs_by_size_usd"][250]["worse_side_median_bp"] is None
