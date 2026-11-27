"""Made-up transport and books. Never runs the read command."""
import io
import json
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import measure_133 as m
from test_venue_binance_us import Opener

FREEZE = "1" * 40
T = datetime(2026, 11, 27, tzinfo=timezone.utc)
BOOK = {"bids": [["99.99", "100"]], "asks": [["100.01", "100"]]}


def klines(wake, closes):
    end = m.bx.epoch_ms(m.hour(wake))
    return [[stamp, p, p, p, p, "1", stamp + m.bx.HOUR_MS - 1, "0", 1, "0", "0", "0"]
            for j, value in enumerate(closes)
            for stamp, p in [(end - (len(closes) - j) * m.bx.HOUR_MS, str(value))]]


class FakePages:
    def __init__(self):
        self.calls = []
        self.pair_states = dict.fromkeys(m.COINS, "TRADING")
        self.block = False

    def pairs(self):
        self.calls.append("pairs")
        return self.pair_states

    def candles(self, wake):
        self.calls.append("BTC")
        return klines(wake, [100, 98])

    def book(self, venue, coin):
        self.calls.append((venue, coin))
        if self.block:
            raise m.Blocked(m.bx.HOST, 403)
        return BOOK


class Recorder(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(temp.cleanup)
        self.off = Path(temp.name) / "m133"
        self.pages = FakePages()
        self.gate = m.bx.Gate(Path(temp.name) / "gate" / "cooldown.json", clock=self.clock)
        self.now = T

    def clock(self):
        return self.now

    def start_mock(self):
        with patch.object(m, "checked_build", return_value=FREEZE), self.approve():
            h = m.start(self.off, self.pages, self.clock, gate=self.gate)
        self.assertEqual(self.pages.calls, [])
        self.first = m.parse(h["first_wake"])
        return h

    def approve(self):
        return patch.object(m.bx, "git", return_value=f"| 232 | M133_START=<frozen build hash> M133_START={FREEZE} |")

    def test_start_without_approval_leaves_no_private_path(self):
        with patch.object(m, "checked_build", return_value=FREEZE), patch.object(m.bx, "git", return_value=""):
            with self.assertRaises(m.Refuse):
                m.start(self.off, self.pages, self.clock)
        self.assertEqual(self.pages.calls, [])
        self.assertFalse(self.off.exists())

    def test_schedule_gate_private_permissions_and_aggregate_only(self):
        h = self.start_mock()
        self.assertEqual((self.first - T).total_seconds(), 10)
        self.assertEqual(m.parse(h["last_wake"]) - self.first, 719 * m.HOUR)
        self.assertEqual(stat.S_IMODE(self.off.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.off / "log.jsonl").stat().st_mode), 0o600)
        self.now = self.first
        with patch.object(m.bx, "git", return_value=f"| 232 | M133_READ={FREEZE} |"):
            with self.assertRaises(m.Refuse):
                m.record(self.off, self.pages, self.clock)
        self.assertEqual(self.pages.calls, [])
        self.pages.pair_states.update(AAVE="BREAK", ADA="NO_USD_PAIR")
        with self.approve():
            self.assertIsNotNone(m.record(self.off, self.pages, self.clock))
            self.assertIsNone(m.record(self.off, self.pages, self.clock))
        self.assertEqual(self.pages.calls[:2], ["pairs", "BTC"])
        self.assertEqual(len(self.pages.calls), 20)
        m.report(self.off, "publish")
        out = json.loads((self.off / "M133_log.json").read_text())
        self.assertEqual(out["book_counts"][m.VENUE], {"ok": 18, "no_usd_pair": 1, "pair_not_trading": 1})
        for detail in ("BTCUSD", "AAVE", "99.99", "fill_price", "midpoint", "observed_utc", "table", "log_return"):
            self.assertNotIn(detail, json.dumps(out))

    def test_first_missed_no_inventory_backfill(self):
        self.start_mock()
        self.now = self.first + m.HOUR
        with self.approve():
            m.record(self.off, self.pages, self.clock)
        self.assertEqual(self.pages.calls, ["BTC"])
        rows = m.read_log(self.off)
        self.assertEqual([r["kind"] for r in rows], ["header", "pairs", "void", "begin", "wake"])
        self.assertEqual(rows[-1]["books"][m.VENUE]["BTC"]["status"], "pair_inventory_unavailable")

    def test_refusal_stops_and_cannot_resume(self):
        self.start_mock()
        self.now = self.first
        self.pages.block = True
        with self.approve():
            with self.assertRaises(m.Refuse):
                m.record(self.off, self.pages, self.clock)
            calls = self.pages.calls[:]
            self.now += m.HOUR
            with self.assertRaises(m.Refuse):
                m.record(self.off, self.pages, self.clock)
        self.assertEqual(self.pages.calls, calls)
        self.assertEqual(m.read_log(self.off)[-1]["http_status"], 403)

    def test_418_after_inventory_refuses_next_book_and_restart(self):
        self.start_mock()
        self.now = self.first
        with self.approve():
            m.record(self.off, self.pages, self.clock)
        self.pages.calls.clear()
        self.now += m.HOUR

        def banned(venue, coin):
            self.pages.calls.append((venue, coin))
            with self.gate.attempt(generation=0):
                self.gate.http_error(418)

        self.pages.book = banned
        with self.approve(), self.assertRaises(m.Refuse):
            m.record(self.off, self.pages, self.clock)
        calls = self.pages.calls[:]
        self.assertEqual(calls, ["BTC", (m.VENUE, m.COINS[0])])
        self.assertEqual(m.read_log(self.off)[-1]["http_status"], 418)
        self.now += m.HOUR
        with self.approve(), self.assertRaises(m.Refuse):
            m.record(self.off, self.pages, self.clock)
        self.assertEqual(self.pages.calls, calls)
        with self.approve(), patch.object(m, "checked_build", return_value=FREEZE), self.assertRaises(m.Refuse):
            m.start(self.off.parent / "restart", clock=self.clock, gate=m.bx.Gate(self.gate.cooldown_path))
        self.assertFalse((self.off.parent / "restart").exists())

    def test_cooldown_persistence_failure_is_terminal_not_missing_page(self):
        self.start_mock()
        self.now = self.first
        opener = Opener((429, {"Retry-After": "60"}))
        pages = m.PublicPages(opener=opener, sleep=lambda _: None, gate=self.gate, clock=self.clock)
        original = m.bx.Gate.write

        def fault(path, value):
            if path == self.gate.cooldown_path:
                raise OSError("invented storage failure")
            original(path, value)

        with self.approve(), patch.object(self.gate, "write", side_effect=fault), \
                self.assertRaisesRegex(m.Refuse, "gate_storage"):
            m.record(self.off, pages, self.clock)
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual([r["kind"] for r in m.read_log(self.off)], ["header", "begin", "stop"])
        self.assertEqual(m.read_log(self.off)[-1]["reason"], "gate_storage")
        self.assertTrue((self.gate.cooldown_path.parent / m.bx.INFLIGHT).exists())

    def test_clearing_stop_never_revives_prior_sibling_and_new_go_can_start(self):
        self.start_mock()
        self.now = self.first
        directory = self.gate.cooldown_path.parent
        sibling = Opener()
        pages = m.PublicPages(opener=sibling, sleep=lambda _: None, gate=self.gate, clock=self.clock)
        issuer = m.PublicPages(opener=Opener((418, {})), sleep=lambda _: None, gate=self.gate,
                               clock=self.clock, generation=0)
        with self.assertRaises(m.Blocked):
            issuer.book(m.VENUE, "BTC")
        self.assertEqual(json.loads((directory / m.bx.GENERATION).read_text()), {"generation": 1})
        (directory / "stop.json").unlink()
        with self.approve(), self.assertRaisesRegex(m.Refuse, "gate_generation"):
            m.record(self.off, pages, self.clock)
        self.assertEqual(sibling.calls, [])
        self.assertEqual(m.read_log(self.off)[-1]["reason"], "gate_generation")
        new = self.off.parent / "new-run"
        with patch.object(m, "checked_build", return_value=FREEZE):
            with self.approve(), self.assertRaisesRegex(m.Refuse, "M133_START_GENERATION"):
                m.start(new, clock=self.clock, gate=self.gate)
            self.assertFalse(new.exists())
            new_go = f"| 232 | M133_START={FREEZE} M133_START_GENERATION=1 |"
            with patch.object(m.bx, "git", return_value=new_go):
                h = m.start(new, clock=self.clock, gate=self.gate)
        self.assertEqual(h["venue_generation"], 1)
        self.assertEqual(m.read_log(new)[0]["venue_generation"], 1)
        fresh = Opener((200, {}))
        bound = m.PublicPages(opener=fresh, sleep=lambda _: None, gate=self.gate, clock=self.clock)
        bound.bind_run(h["venue_generation"])
        self.assertEqual(bound.book(m.VENUE, "BTC"), [])
        self.assertEqual(len(fresh.calls), 1)

    def test_exact_receipt_window_plus_9_10_120_121(self):
        self.start_mock()
        for i, seconds in enumerate((9, 10, 120, 121)):
            with self.subTest(seconds=seconds), m.locked(self.off):
                rows = m.read_log(self.off)
                wake = self.first + i * m.HOUR
                self.now = wake
                pages = FakePages()

                def book(venue, coin):
                    self.now = m.hour(wake) + timedelta(seconds=seconds)
                    return BOOK

                pages.book = book
                m.collect(self.off, rows, rows[0]["settings"], {"BTC": "TRADING"}, pages, wake, self.clock)
                observed = rows[-1]["books"][m.VENUE]["BTC"]
                self.assertEqual(observed["status"], "ok" if seconds in (10, 120) else "missed_book_window")
                self.assertEqual("sizes" in observed, seconds in (10, 120))

    def test_record_does_not_fetch_before_open_or_after_cutoff(self):
        self.start_mock()
        with self.approve():
            self.now = m.hour(self.first) + timedelta(seconds=9)
            self.assertIsNone(m.record(self.off, self.pages, self.clock))
            self.now = m.hour(self.first) + timedelta(seconds=121)
            self.assertIsNone(m.record(self.off, self.pages, self.clock))
        self.assertEqual(self.pages.calls, [])
        self.assertEqual(m.read_log(self.off)[-1]["kind"], "void")

    def test_rollback_denied(self):
        self.start_mock()
        log = self.off / "log.jsonl"
        old = log.read_bytes()
        self.now = self.first
        with self.approve():
            m.record(self.off, self.pages, self.clock)
            calls = self.pages.calls[:]
            log.write_bytes(old)
            with self.assertRaises(m.Refuse):
                m.record(self.off, self.pages, self.clock)
        self.assertEqual(self.pages.calls, calls)


class InputsAndMath(unittest.TestCase):
    def test_exact_quoted_dollars_and_status(self):
        pages = m.PublicPages()
        sym = lambda base, quote, status: dict(baseAsset=base, quoteAsset=quote, symbol=base + quote, status=status)
        data = {"symbols": [sym("BTC", "USD", "TRADING"), sym("BNB", "USD", "BREAK"),
                            sym("ETH", "USDT", "TRADING"), sym("ETH", "USDC", "TRADING")]}
        with patch.object(pages, "get", return_value=data) as get:
            out = pages.pairs()
        get.assert_called_once_with(m.VENUE, "/api/v3/exchangeInfo")
        self.assertEqual(len(out), 20)
        self.assertEqual((out["BTC"], out["BNB"], out["ETH"]), ("TRADING", "BREAK", "NO_USD_PAIR"))

    def test_candle_clock_closed_only_and_duplicate_refusal(self):
        rows = klines(T, [100, 98])
        current = klines(T + m.HOUR, [1])[0]
        self.assertTrue(m.candle_signal([current, *rows[::-1]], T, 0.015)["drop"])
        for bad in (rows[:1], rows + rows[:1], [rows[0], [*rows[1][:6], rows[1][6] + 1, *rows[1][7:]]]):
            with self.assertRaises(m.Failure):
                m.candle_signal(bad, T, 0.015)

    def test_cost_math_and_thin_or_bad_depth(self):
        out = m.ticket(BOOK, m.VENUE, [25, 250], 2)
        for size in ("25", "250"):
            self.assertEqual(Decimal(out["sizes"][size]["buy"]["cost_bp"]), 3)
            self.assertEqual(Decimal(out["sizes"][size]["sell"]["cost_bp"]), 3)
        thin = m.ticket(BOOK | {"asks": [["100.01", "1"]]}, m.VENUE, [25, 250], 1)
        self.assertEqual(thin["sizes"]["250"]["buy"], {"status": "too thin"})
        self.assertEqual(Decimal(thin["sizes"]["250"]["sell"]["cost_bp"]), 2)
        self.assertEqual(m.ticket(BOOK | {"bids": [["101", "100"]]}, m.VENUE, [250], 1)["status"], "bad book")
        self.assertEqual(m.ticket(BOOK | {"bids": [["99.99", "100"], ["99.99", "1"]]},
                                  m.VENUE, [250], 1)["status"], "bad book")

    def test_paired_midnights_decision_both_sides_and_full_denominator(self):
        st = m.settings()[1]
        rows = [{"kind": "header", "settings": st}]
        ok = {"status": "ok", "cost_bp": "25"}
        for day in range(25):
            stamp = m.iso(T + 24 * day * m.HOUR)
            b = {c: {"status": "ok", "sizes": {"250": {"buy": ok, "sell": ok}}} for c in m.COINS}
            b = {c: b[c] for c in m.COINS[:15]}
            rows.append({"kind": "wake", "wake": stamp, "bitcoin": {"status": "ok"}, "books": {m.VENUE: b}})
        self.assertEqual(m.summarize(rows, full=True)["decision"]["main_cost_line_bp"], 25)
        rows[-1]["books"][m.VENUE][m.COINS[0]]["sizes"]["250"]["sell"] = {"status": "too thin"}
        dec = m.summarize(rows, full=True)["decision"]
        self.assertEqual((dec["main_cost_line_bp"], len(dec["paired_midnights_by_coin"])), (75, 20))

    def test_transport_routes_and_block(self):
        class Opener:
            def __init__(self):
                self.calls = []
            def open(self, req, timeout):
                self.calls.append(req.full_url)
                if len(self.calls) == 2:
                    raise HTTPError(req.full_url, 403, "", None, io.BytesIO())
                return io.BytesIO(b"[]")
        opener = Opener()
        temp = tempfile.TemporaryDirectory(dir="/tmp")
        self.addCleanup(temp.cleanup)
        gate = m.bx.Gate(Path(temp.name) / "gate" / "cooldown.json")
        pages = m.PublicPages(opener=opener, sleep=lambda _: None, gate=gate, generation=gate.check_start())
        self.assertEqual(pages.klines("BTC", T, 2), [])
        with self.assertRaises(m.Blocked):
            pages.book(m.VENUE, "BNB")
        for bad in ("https://else.invalid/api/v3/depth", "/api/v3/depth#x", "/api/v3/order"):
            with self.assertRaises(m.Refuse):
                pages.get(m.VENUE, bad)
        self.assertEqual(len(opener.calls), 2)
        candle, book = map(urlsplit, opener.calls)
        self.assertEqual((candle.hostname, book.hostname), (m.bx.HOST, m.bx.HOST))
        self.assertEqual(parse_qs(candle.query)["endTime"], [str(m.bx.epoch_ms(T) - 1)])
        self.assertEqual(parse_qs(book.query)["symbol"], ["BNBUSD"])

    def test_approval_token_exact_same_row_build_and_action(self):
        on_row = f"| 232 | M133_START=<frozen build hash> `M133_START={FREEZE}` |"
        m.require_go(232, "M133_START", FREEZE, ledger=on_row)
        for bad in (on_row.replace("232", "230"), on_row.replace("M133_START", "M133_READ"),
                    on_row.replace(FREEZE, "2" * 40), on_row + "\n" + on_row,
                    on_row + " M133_START=" + "2" * 40):
            with self.assertRaises(m.Refuse):
                m.require_go(232, "M133_START", FREEZE, ledger=bad)

    def test_read_preflight_requires_elapsed_window_separate_go_and_once(self):
        h = {"last_wake": m.iso(T), "settings": {"window_s": 120}, "freeze": FREEZE}
        with patch.object(m.bx, "git", return_value=f"| 232 | M133_READ={FREEZE} |"):
            with self.assertRaises(m.Refuse):
                m.read_gate([], h, T + timedelta(seconds=120))
            m.read_gate([], h, T + timedelta(seconds=121))
            with self.assertRaises(m.Refuse):
                m.read_gate([{"kind": "read"}], h, T + timedelta(seconds=121))
        with patch.object(m.bx, "git", return_value=f"| 232 | M133_START={FREEZE} |"):
            with self.assertRaises(m.Refuse):
                m.read_gate([], h, T + timedelta(seconds=121))


if __name__ == "__main__":
    unittest.main()
