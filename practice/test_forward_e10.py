"""E10 tests with only invented products, clocks, prices and folders."""
import io
import json
import stat
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

import numpy as np

import forward_e10 as e

BTC = "BTC"
T = datetime(2030, 1, 6, tzinfo=e.UTC)


def product(**flags):
    return {"id": "BTC-USD", "status": "online", "trading_disabled": False, "cancel_only": False,
            "post_only": False, "limit_only": False, "base_min_size": "0.001"} | flags


class Venue:
    def __init__(self, other_product=False, **flags):
        self.flags = flags
        self.other_product = other_product
        self.quote_reads = 0

    def products(self):
        records = {"BTC-USD": product(**self.flags)}
        if self.other_product:
            records["ETH-USD"] = product(id="ETH-USD")
        return records

    def candles(self, coin, start, stop):
        out = {}
        if coin != BTC:
            return out
        while start < stop:
            d = (start - T).days
            p = 200 + d + 0.15 * (d % 3)
            out[start.date().isoformat()] = [p, p + 0.1]
            start += timedelta(days=1)
        return out

    def book(self, coin):
        if coin != BTC:
            return None
        self.quote_reads += 1
        return [199.9, 200.1]


class Clock:
    def __init__(self, day, offset=10):
        self.now = day + timedelta(seconds=offset)

    def __call__(self):
        return self.now

    def sleep(self, n):
        self.now += timedelta(seconds=n)


class Tests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = Path(tmp.name) / "invented"
        self.f, self.rule, self.marks, self.fees = e.settings()
        e.start(T - timedelta(days=1), self.folder, "invented")

    def record(self, day=T, offset=10, venue=None):
        c = Clock(day, offset)
        return e.record(c(), venue or Venue(), self.folder, c, c.sleep)

    def rows(self):
        with e.private(self.folder) as fd:
            return e.read_log(fd)

    def test_decisions_and_no_hook_adapter_match_frozen(self):
        self.record()
        self.record(T + timedelta(days=1))
        tape, _, _ = e.make_tape(self.rows(), self.f, self.rule, "flat")
        tape.closes[-1, tape.names.index(BTC)] = 201.25
        original = e.core.indicators(tape, self.rule["lookbacks"], self.rule, self.marks["annual_days"])
        original_cal = e.core.calendar(tape, original[2])
        wrapped, cal = e.decisions(tape, self.rule, self.marks)
        for a, b in zip(original + original_cal, wrapped + cal, strict=True):
            np.testing.assert_array_equal(a, b)
        direct = e.core.play(tape, self.fees["flat"], self.rule, self.rule["cap"], original, original_cal)
        adapted = e.play_forward(tape, self.fees["flat"], self.rule, self.rule["cap"], wrapped, cal)
        for name in ("nav", "weights", "targets"):
            np.testing.assert_array_equal(getattr(direct, name), getattr(adapted, name))
        self.assertEqual(direct.fills, adapted.fills)
        self.assertTrue(direct.fills)

    def test_void_no_buy_and_no_retroactive_record(self):
        w = self.record(T + timedelta(days=1), offset=901)
        self.assertTrue(w["late"])
        self.assertEqual(w["orders"]["quote:main"]["fills"], [])
        self.assertEqual(w["orders"]["quote:main"]["void_buys"], 1)
        self.assertIsNone(self.record(T))
        public = e.alive(self.folder)
        self.assertEqual((public["wakes"], public["missed_wakes"], public["void_wakes"]), (1, 1, 2))

    def test_partial_state_waits_then_allows_sale_not_purchase(self):
        self.assertFalse(e.product_state(product(limit_only=True))["eligible"])
        self.assertTrue(e.product_state(product(limit_only=True))["sell"])
        self.assertFalse(e.product_state(product(cancel_only=True))["sell"])
        self.assertFalse(e.product_state(product(post_only=True))["sell"])
        self.assertFalse(e.product_state(product(trading_disabled=True))["sell"])
        self.assertFalse(e.product_state(None)["exists"])
        buy = self.record()
        self.assertEqual(buy["orders"]["quote:main"]["fills"], [{"coin": BTC, "side": "buy"}])
        wait = self.record(T + timedelta(days=1), venue=Venue(cancel_only=True, other_product=True))
        self.assertEqual(wait["orders"]["quote:main"]["fills"], [])
        leave = self.record(T + timedelta(days=2), 901, Venue(limit_only=True))
        self.assertEqual(leave["orders"]["quote:main"]["fills"], [{"coin": BTC, "side": "sell"}])
        self.assertEqual(leave["orders"]["quote:main"]["delayed_sells"], 1)
        self.assertTrue(leave["states"][BTC]["flags"]["limit_only"])

    def test_under_minimum_and_counts_only_public(self):
        w = self.record(venue=Venue(min_market_funds="1000"))
        self.assertEqual(w["orders"]["quote:main"]["under"], 1)
        self.assertEqual(w["orders"]["quote:shown"]["under"], 0)
        self.assertEqual(w["orders"]["quote:shown"]["fills"], [{"coin": BTC, "side": "buy"}])
        public_file = self.folder.parent / "public.json"
        public = e.publish(self.folder, public_file)
        self.assertEqual(public["placeability"]["main"]["under"], 1)
        for private in ("199.9", "200.1", '"bid"', '"ask"', '"net"', "warmup"):
            self.assertNotIn(private, public_file.read_text())

    def test_quote_offsets_follow_actual_attempts(self):
        venue = Venue()
        self.record(venue=venue)
        self.assertEqual(venue.quote_reads, 4)
        follow = [r for r in self.rows() if r["kind"] == "follow"]
        self.assertEqual([r["quotes"][BTC]["seconds"] for r in follow], self.f["quote_offsets_s"])

    def test_hash_chain_tamper_and_truncation(self):
        self.record()
        p = self.folder / "log.jsonl"
        original = p.read_text()
        self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.folder.stat().st_mode), 0o700)
        p.write_text(original.replace("200.1", "200.2", 1))
        with self.assertRaisesRegex(e.Refuse, "chain"):
            self.rows()
        p.write_text("".join(original.splitlines(keepends=True)[:-1]))
        with self.assertRaisesRegex(e.Refuse, "tip"):
            self.rows()

    def test_release_once_only_after_elapsed_horizon(self):
        short = self.f | {"score_days": 3}
        with patch.object(e, "settings", return_value=(short, self.rule, self.marks, self.fees)):
            self.record()
            with self.assertRaisesRegex(e.Refuse, "incomplete"):
                e.score(T + timedelta(days=2), self.folder)
            for d in (1, 2, 3):
                self.record(T + timedelta(days=d))
            with self.assertRaisesRegex(e.Refuse, "incomplete"):
                e.score(T + timedelta(days=3), self.folder)
            result = e.score(T + timedelta(days=3, seconds=10), self.folder)
            self.assertEqual(result["label"], "RECORD_NOT_VERDICT")
            self.assertEqual(set(result["lines"]), {"quote", "flat", "harsh"})
            self.assertIsNotNone(result["lines"]["quote"]["whole"]["matched_btc"])
            with self.assertRaisesRegex(e.Refuse, "already read"):
                e.score(T + timedelta(days=4), self.folder)

    def test_block_persists(self):
        venue = Venue()
        with patch.object(venue, "products", side_effect=e.Blocked("venue refused HTTP 451")):
            with self.assertRaises(e.Blocked):
                self.record(venue=venue)
        with self.assertRaisesRegex(e.Refuse, "venue blocked"):
            self.record()
        self.assertEqual(e.alive(self.folder)["status"], "BLOCKED")

    def test_transport_backs_off_on_429_and_stops_on_451(self):
        venue = e.Coinbase(self.f)
        replies = [HTTPError("", 429, "", {"Retry-After": "7"}, io.BytesIO()),
                   HTTPError("", 451, "", {}, io.BytesIO())]
        with patch.object(venue.opener, "open", side_effect=replies) as opener, patch.object(e.time, "sleep") as sleep:
            with self.assertRaisesRegex(e.Blocked, "451"):
                venue.get("/products")
        self.assertEqual(opener.call_count, 2)
        self.assertIn(((7.0,), {}), sleep.call_args_list)

    def test_initial_public_json_is_empty_counts(self):
        self.assertEqual(json.loads(e.PUBLIC.read_text()), e.counts([], self.f, self.fees))


if __name__ == "__main__":
    unittest.main()
