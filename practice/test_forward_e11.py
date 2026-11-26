"""Invented candles, depth and aggregate trades only. Never opens a live folder or URL."""
import json
import os
import stat
import tempfile
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import numpy as np

import forward_e11 as e
import sweep_71
from test_forward_e09 import made_up_panel, sweep_tickets

T = datetime(2027, 2, 1, tzinfo=e.UTC)


def depth(ask="101", bid="99", quantity="10"):
    return {"bids": [[bid, quantity]], "asks": [[ask, quantity]]}


class Clock:
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now

    def sleep(self, sec):
        self.now += timedelta(seconds=sec)


class Venue:
    def __init__(self):
        self.candle_calls = []
        self.depth_calls = []
        self.agg_calls = []
        self.deadline = None

    def candles(self, coin, wake):
        self.candle_calls.append(coin)
        n = int(wake.timestamp())
        prices = (("100", "100", "98") if coin == "BTC" else
                  ("100", "100", "90") if coin == "ETH" else ("100", "100", "100"))
        return [[n - (3 - j) * e.e09.HOUR, float(p), float(p), float(p), float(p), 1]
                for j, p in enumerate(prices)]

    def pairs(self):
        return {"BTC": "TRADING", "ETH": "TRADING"}

    def depth(self, coin):
        self.depth_calls.append(coin)
        return depth()

    def agg(self, coin, **kw):
        self.agg_calls.append((coin, kw))
        return []


def fake_book(raw, *, taken=10):
    b = e.m132.ticket(raw, "Binance.US", (), 0)
    return b | ({"bids": raw["bids"], "asks": raw["asks"]} if b["status"] == "ok" else {}) | {
        "taken_s": taken, "received": e.iso(T + timedelta(seconds=taken))}


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.off = Path(self.tmp.name) / "e11"
        self.cfg, self.fees, self.roots, self.pins = e.settings()
        e.start(T - timedelta(minutes=30), self.off, commit="invented")
        self.v = Venue()

    def record(self, wake=T, second=5, venue=None):
        clock = Clock(wake + timedelta(seconds=second))
        return e.record(clock(), venue or self.v, self.off, clock, clock.sleep)

    def rows(self):
        return e.m132.read_log(self.off)

    def test_same_frozen_signals_and_slots_as_e09_on_invented_tape(self):
        rules = e.e09.rules()
        n = int(T.timestamp())
        hours = np.arange(n, n + 160 * e.e09.HOUR, e.e09.HOUR)
        panel = made_up_panel(422, hours)
        got, due = {a: [] for a in rules}, {}
        last = datetime.fromtimestamp(int(hours[-1]), e.UTC)
        for i, x in enumerate(hours[3:], 3):
            wake = datetime.fromtimestamp(int(x), e.UTC)
            free = [a for a in rules if a not in due or due[a] <= wake]
            bars = {coin: {int(hours[k]): tuple(panel[j, k]) for k in range(i-3, i)
                           if np.isfinite(panel[j, k]).all()} for j, coin in enumerate(e.e09.COINS)}
            for order in e.picks(wake, bars, free, rules, last):
                a = order["arm"]
                due[a] = e.parse(order["due"])
                got[a].append((order["coin"], e.e09.iso(wake)))
        for a, rule in rules.items():
            # The first three hours were pre-start history and never claimed.
            expected = sweep_tickets(hours, panel, rule)
            self.assertGreater(len(expected), 2)
            self.assertEqual(got[a], expected)
            if a != e.e09.JUDGED:
                tape = e.e09.sweep_70.Tape(list(e.e09.COINS), panel, hours=hours, split=None)
                j, i, *_ = sweep_71.ticket_legs(tape, rule, np.zeros(len(e.e09.COINS)), 1)
                priced = {(e.e09.COINS[a], e.e09.iso(datetime.fromtimestamp(int(hours[b]), e.UTC)))
                          for a, b in zip(j[0], i, strict=True)}
                self.assertTrue(priced)
                self.assertTrue(priced.issubset(set(got[a])))

    def test_arithmetic_walk_both_sides_and_fee(self):
        b = fake_book({"bids": [["90", "1"], ["80", "3"]],
                       "asks": [["100", "1"], ["120", "3"]]})
        buy = e.walk(b["asks"], 250, buy=True)
        self.assertEqual(buy, (Decimal("2.25"), Decimal("250")))
        sold = e.walk(b["bids"], buy[0], buy=False)
        self.assertEqual(sold, (Decimal("2.25"), Decimal("190")))
        net = e.settle(b, b, 250, Decimal(2))["net"]
        self.assertAlmostEqual(net, (190 * .9998 - 250 * 1.0002) / 250)
        self.assertEqual(e.fee_bp(self.fees, "BNB"), 1)

    def test_thin_bad_and_strict_clock(self):
        good = fake_book(depth(), taken=120)
        late = fake_book(depth(), taken=120.000001)
        self.assertIn("net", e.settle(good, good, 250, Decimal(2), limit=120))
        self.assertEqual(e.settle(good, late, 250, Decimal(2), limit=120)["reason"], "late book")
        self.assertEqual(e.settle(late, good, 250, Decimal(2), limit=120)["reason"], "late book")
        thin = fake_book(depth(quantity=".15"))
        self.assertEqual(e.settle(thin, good, 250, Decimal(2))["reason"], "entry too thin")
        self.assertEqual(e.settle(good, thin, 250, Decimal(2))["reason"], "exit too thin")
        for raw in (depth(ask="99"), depth(ask="NaN"), depth(quantity="0"),
                    {"asks": [["101", "1"], ["100", "1"]], "bids": [["99", "1"]]},
                    {"asks": [[101, "1"]], "bids": [["99", "1"]]},
                    {"asks": [["101", "1", "2"]], "bids": [["99", "1"]]}):
            bad = fake_book(raw)
            self.assertEqual(bad["status"], "bad book")
            self.assertFalse({"bid", "ask", "midpoint", "bids", "asks"} & bad.keys())
            self.assertEqual(e.settle(good, bad, 250, Decimal(2))["reason"], "bad book")

    def test_resting_fill_strict_price_time_and_before_fill_marks(self):
        b = fake_book(depth())
        first = e.epoch_ms(e.parse(b["received"]))
        reply = [{"a": 1, "T": first + 1, "p": "99"}, {"a": 2, "T": first + 61_000, "p": "98"}]
        with patch.object(self.v, "agg", return_value=reply):
            result = e.resting(self.v, "ETH", b, self.cfg)
        self.assertEqual((result["status"], result["seconds_to_fill"]), ("FILLED", 61))
        w = e.iso(T)
        book = {(w, "ETH", 0): b, (w, "ETH", 60): fake_book(depth(), taken=70),
                (w, "ETH", 300): fake_book(depth(), taken=310)}
        marks = e.rest_marks({"coin": "ETH", "wake": w}, book, result)
        self.assertEqual([m["phase"] for m in marks.values()], ["BEFORE_FILL", "AFTER_FILL", "UNKNOWN"])
        self.assertAlmostEqual(marks["60"]["move_bp"], (100 / 99 - 1) * 10000)
        with patch.object(self.v, "agg", return_value=[{"a": 1, "T": first, "p": "98"}]):
            self.assertEqual(e.resting(self.v, "ETH", b, self.cfg)["status"], "UNKNOWN")

    def test_resting_no_fill_coverage_and_unknown_cap_or_fetch_error(self):
        b = fake_book(depth())
        t = e.epoch_ms(e.parse(b["received"]))
        a = [{"a": 8, "T": t + 1, "p": "99"}, {"a": 9, "T": t + 2, "p": "100"}]
        b2 = [{"a": 10, "T": t + 300_001, "p": "1"}]
        with patch.object(e, "AGG_LIMIT", 2):
            with patch.object(self.v, "agg", side_effect=[a, b2]) as pages:
                self.assertEqual(e.resting(self.v, "ETH", b, self.cfg)["status"], "NOT_FILLED")
                self.assertEqual(pages.call_args_list[1].kwargs["from_id"], 10)
            with patch.object(self.v, "agg", return_value=a):
                self.assertEqual(e.resting(self.v, "ETH", b, self.cfg | {"resting_page_cap": 1})["status"], "UNKNOWN")
            with patch.object(self.v, "agg", side_effect=e.Failure("timeout")):
                self.assertEqual(e.resting(self.v, "ETH", b, self.cfg)["status"], "UNKNOWN")
            with patch.object(self.v, "agg", return_value=a[:1]):
                self.assertEqual(e.resting(self.v, "ETH", b, self.cfg)["status"], "NOT_FILLED")

    def test_candle_failure_voids_signal_wake_but_other_coins_checked(self):
        candles = self.v.candles
        def partial(coin, wake):
            if coin == "ETH":
                raise e.Failure("timeout")
            return candles(coin, wake)
        with patch.object(self.v, "candles", side_effect=partial):
            w = self.record()
        self.assertEqual(w["kind"], "void")
        self.assertEqual(w["failures"], {"ETH": "timeout"})
        self.assertIn("ZEC", self.v.candle_calls)

    def test_one_coin_depth_failure_does_not_abort_other_coin(self):
        real_depth = self.v.depth
        def partial(coin):
            if coin == "BTC":
                raise e.Failure("http_500")
            return real_depth(coin)
        proposed = [{"arm": a, "coin": c, "wake": e.iso(T), "due": e.iso(T + e.HOUR)}
                    for a, c in zip(e.e09.ARMS[:2], ("BTC", "ETH"), strict=True)]
        with patch.object(e, "picks", return_value=proposed), patch.object(self.v, "depth", side_effect=partial):
            w = self.record()
        self.assertEqual(w["kind"], "wake")
        self.assertEqual(w["books"]["BTC"]["status"], "book page unavailable")
        self.assertEqual(w["books"]["ETH"]["status"], "ok")
        self.assertEqual(len([r for r in self.rows() if r["kind"] == "follow" and r["coin"] == "ETH"]), 3)

    def test_host_stop_persists_without_next_request(self):
        with patch.object(self.v, "depth", side_effect=e.Blocked("api.binance.us", 451)):
            stop = self.record()
        self.assertEqual((stop["host"], stop["http_status"]), ("api.binance.us", 451))
        with patch.object(self.v, "candles", side_effect=AssertionError("no future venue call")):
            self.assertEqual(self.record(T + e.HOUR)["kind"], "stopped")
        self.assertEqual(e.alive(self.off)["block"], {"host": "api.binance.us", "http_status": 451})

    def test_coinbase_403_stops_before_any_binance_attempt(self):
        with patch.object(self.v, "candles", side_effect=e.Blocked("api.exchange.coinbase.com", 403)):
            stop = self.record()
        self.assertEqual(stop["http_status"], 403)
        self.assertFalse(self.v.depth_calls)

    def test_anchor_truncation_and_complete_extension_refuse(self):
        p = self.off / "log.jsonl"
        start = p.read_bytes()
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.off.stat().st_mode), 0o700)
        p.write_bytes(b"")
        with self.assertRaisesRegex(e.Refuse, "shorter"):
            self.rows()
        p.write_bytes(start)
        _, extension = e.m132.next_row(self.rows(), {"kind": "another"})
        p.write_bytes(start + extension)
        with self.assertRaisesRegex(e.Refuse, "behind"):
            self.rows()

    def test_recover_torn_tail_does_not_fetch_claimed_wake(self):
        rows = self.rows()
        e.m132.append(self.off, rows, kind="claim", wake=e.iso(T))
        with (self.off / "log.jsonl").open("ab") as out:
            out.write(b'{"kind":')
            out.flush()
            os.fsync(out.fileno())
        with self.assertRaisesRegex(e.Refuse, "torn"):
            self.rows()
        self.assertEqual(self.record()["kind"], "void")
        self.assertFalse(self.v.candle_calls)
        rows = self.rows()
        self.assertEqual([r["kind"] for r in rows], ["header", "claim", "recovery", "void"])
        self.assertEqual(self.record()["kind"], "nothing due")

    def test_storage_refuses_git_tree(self):
        other = Path(self.tmp.name) / "repo"
        other.mkdir()
        (other / ".git").touch()
        with self.assertRaisesRegex(e.Refuse, "Git"):
            e.start(T, other / "e11", commit="invented")

    def test_score_refusal_read_once_and_no_public_profit(self):
        with self.assertRaisesRegex(e.Refuse, "not yet"):
            e.score(T, self.off)
        start = self.record()
        self.assertEqual(len(start["entries"]), 3)
        for delta in (e.HOUR, 2 * e.HOUR):
            self.record(T + delta)
        public_file = Path(self.tmp.name) / "public.json"
        e.publish(self.off, public_file)
        public = public_file.read_text()
        for field in ('"bid"', '"ask"', '"net"', '"pretend_usd"', '"print_price"', '"signal_bars"'):
            self.assertNotIn(field, public)
        self.assertIn("cost_per_side_bp", public)
        final = e.parse(self.cfg["last_wake_utc"]) + timedelta(seconds=e.e09.WINDOW_S)
        out = e.score(final, self.off)
        self.assertEqual(out["judged"]["verdict"], "too few to judge")
        details = out["shown"][e.e09.JUDGED]["resting_signals"]
        self.assertEqual(details[0]["resting"], "NOT_FILLED")
        self.assertIn("net", details[0]["taker_line_if_not_filled"])
        with self.assertRaisesRegex(e.Refuse, "already read"):
            e.score(final, self.off)

    def test_default_public_file_empty_and_price_free(self):
        self.assertEqual(json.loads(e.PUBLIC.read_text()), e.summary([], self.cfg, self.fees))

    def test_reaching_judging_count_does_not_open_or_fetch_another_wake(self):
        cfg = self.cfg | {"judging_count": 1, "judging_floor": 1}
        new_off = Path(self.tmp.name) / "e11-cut"
        with patch.object(e, "settings", return_value=(cfg, self.fees, self.roots, self.pins)):
            e.start(T - timedelta(minutes=30), new_off, commit="invented")
            for d in range(3):
                clock = Clock(T + d * e.HOUR + timedelta(seconds=5))
                row = e.record(clock(), self.v, new_off, clock, clock.sleep)
            self.assertEqual(row["entries"], [])
            nxt = Clock(T + 3 * e.HOUR + timedelta(seconds=5))
            with patch.object(self.v, "candles", side_effect=AssertionError("after cutoff")):
                self.assertEqual(e.record(nxt(), self.v, new_off, nxt, nxt.sleep)["kind"], "judging point")
            out = e.score(nxt(), new_off)
            self.assertEqual((out["cutoff"], out["judged"]["trades"]), ("trade count", 1))
            self.assertEqual(out["judged"]["verdict"], "did not pass")


if __name__ == "__main__":
    unittest.main()
