"""Invented candles, books, clocks, authorization and filesystem only. No scorer runs."""
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from practice import forward_e13 as e

T = datetime(2030, 1, 6, tzinfo=e.UTC)
START_ID = 'invented-start'
SCORE_ID = 'invented-score'
FAKE_RELEASE = 'b' * 40
LEDGER = (b'| 231 | `E13_START=<id>` and `E13_SCORE_GO=<id>` are syntax only. '
          b'`E13_START=invented-start` and `E13_SCORE_GO=invented-score` |\n')
BOOK = {'bids': [[99., 12.], [97., 100.]], 'asks': [[101., 1.], [110., 8.]]}


def pair(ready=True, minimum='1'):
    return {'status': 'TRADING' if ready else 'HALT', 'isSpotTradingAllowed': True,
            'orderTypes': ['LIMIT', 'MARKET'], 'filters': [{'filterType': 'MIN_NOTIONAL',
                                                            'minNotional': minimum, 'applyToMarket': True}]}


class FakeClock:
    def __init__(self, day, offset=10):
        self.time = day + timedelta(seconds=offset)

    def __call__(self):
        return self.time

    def sleep(self, seconds):
        self.time += timedelta(seconds=seconds)


class Venue:
    def __init__(self, coins=('BTC',), states=None, short=(), depth=BOOK):
        self.coins, self.states, self.short, self.depth = coins, states or {}, set(short), depth
        self.candle_calls, self.book_calls, self.product_calls = [], [], 0

    def products(self, names):
        self.product_calls += 1
        return {coin: self.states.get(coin, pair()) for coin in self.coins if coin in names}

    def candles(self, coin, first, stop):
        self.candle_calls.append((coin, first, stop))
        prices = {}
        while first < stop:
            d = (first - T).days
            if coin not in self.short or d >= -4:
                prices[first.date().isoformat()] = 123.456789 + d * .19 + (d % 3) * .07
            first += timedelta(days=1)
        return prices

    def book(self, coin):
        self.book_calls.append(coin)
        return self.depth


class Tests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.temp = Path(tmp.name)
        self.folder = self.temp / 'invented'
        network = patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('no live networking in tests'))
        self.addCleanup(network.stop)
        network.start()
        auth = patch.object(e, 'committed_go', side_effect=self.authority)
        self.auth = auth.start()
        self.real_authority = auth.temp_original
        self.addCleanup(auth.stop)
        self.f, self.rule, self.fees = e.settings()

    def authority(self, label, value, release=None, generation=None):
        e.ledger_go(LEDGER, label, value)
        self.assertIn(release, (None, FAKE_RELEASE))
        return 'a' * 40, FAKE_RELEASE

    def gate(self, clock=None):
        directory = self.temp / 'shared'
        gate = e.bx.Gate(cooldown_path=directory / 'cooldown.json', clock=clock or FakeClock(T))
        if not directory.exists():
            gate.check_start()
        return gate

    def start(self):
        return e.start(T - timedelta(days=1), START_ID, self.folder, gate=self.gate())

    def observe(self, day=T, venue=None, offset=10):
        c = FakeClock(day, offset)
        return e.record(c(), venue if venue is not None else Venue(), self.folder, c, c.sleep)

    def rows(self):
        with e.private(self.folder) as fd:
            return e.read_log(fd)

    def test_rule_definitions_load_without_importing_scorer(self):
        model = e.frozen(self.f['rule_source_sha256'])
        self.assertEqual(len(model.NAMES), 20)
        self.assertNotIn('score_75', sys.modules)
        self.assertNotIn('research_rig.score_75', sys.modules)
        with self.assertRaisesRegex(e.Refuse, 'frozen rule changed'):
            e.frozen('0' * 64)

    def test_ledger_gate_placeholders_wrong_row_duplicates_and_wrong_id(self):
        for bad in (LEDGER.replace(b'231', b'230'), LEDGER + LEDGER, LEDGER.replace(b'`E13_START=invented-start`', b'')):
            with self.assertRaisesRegex(e.Refuse, 'lead go missing'):
                e.ledger_go(bad, 'E13_START', START_ID)
        e.ledger_go(LEDGER, 'E13_START', START_ID)
        e.ledger_go(LEDGER, 'E13_SCORE_GO', SCORE_ID)
        with self.assertRaisesRegex(e.Refuse, 'lead go missing'):
            e.start(T - timedelta(days=1), SCORE_ID, self.folder, gate=self.gate())
        self.assertFalse(self.folder.exists())
        self.assertEqual(e.clock_at(self.start()['first']), T)

    def test_no_quotes_before_scheduled_time_or_if_original_go_is_missing(self):
        self.start()
        venue = Venue()
        self.assertIsNone(self.observe(venue=venue, offset=9))
        with patch.object(e, 'committed_go', side_effect=e.Refuse('lead go missing')):
            with self.assertRaisesRegex(e.Refuse, 'lead go missing'):
                self.observe(venue=venue)
        self.assertEqual(venue.product_calls, 0)

    def test_first_wake_roster_is_frozen_and_unwarmed_name_is_counted(self):
        self.start()
        first = Venue(coins=('BTC', 'ETH'), short=('ETH',))
        row = self.observe(venue=first)
        self.assertEqual(row['roster'], ['BTC', 'ETH'])
        self.assertEqual(row['not_ready'], ['ETH'])
        self.assertEqual(first.candle_calls[0], ('BTC', T - timedelta(days=91), T))
        second = Venue(coins=('BTC', 'ETH', 'BNB'), short=('ETH',))
        row = self.observe(T + timedelta(days=1), venue=second)
        self.assertEqual(row['roster'], ['BTC', 'ETH'])
        self.assertNotIn('BNB', second.book_calls)
        self.assertTrue(all(coin != 'BNB' for coin, _, _ in second.candle_calls))

    def test_first_wake_miss_or_pair_list_failure_cannot_pick_later_roster(self):
        self.start()
        unavailable = Venue(coins=())
        with self.assertRaisesRegex(e.Blocked, 'roster not frozen'):
            self.observe(venue=unavailable)
        self.assertEqual(unavailable.candle_calls, [])
        with self.assertRaisesRegex(e.Refuse, 'recording stopped'):
            self.observe(T + timedelta(days=1))
        self.assertEqual(e.alive(self.folder)['status'], 'STOPPED')

    def test_too_late_first_attempt_has_no_network(self):
        self.start()
        venue = Venue()
        with self.assertRaisesRegex(e.Blocked, 'first wake missed'):
            self.observe(T + timedelta(days=1), venue)
        self.assertEqual(venue.product_calls, 0)

    def test_depth_walk_then_independent_size_and_fee(self):
        self.start()
        row = self.observe()
        main, shown = (row['books'][k] for k in ('main', 'shown'))
        self.assertEqual(len(main['fills']), 1)
        fill = main['fills'][0]
        self.assertGreater(fill['quantity'], 1)
        self.assertAlmostEqual(fill['gross'], 101 + (fill['quantity'] - 1) * 110)
        self.assertAlmostEqual(fill['fee'], fill['gross'] * .0002)
        self.assertLessEqual(fill['gross'] + fill['fee'], 500.00000001)
        self.assertEqual(shown['fills'], [])
        self.assertEqual(shown['attempts']['BTC'], ['insufficient_depth'])
        self.assertEqual(e.fee_for(self.fees, 'BNB'), .0001)
        self.assertEqual(e.walk(BOOK['bids'], 13), (12 * 99 + 97, True))
        self.assertEqual(e.round_qty(1.19, [.02, .03]), 1.14)

    def test_never_retrofill_missed_day_and_followups_never_replace_depth(self):
        self.start()
        row = self.observe()
        original = row['books']
        follow = [r for r in self.rows() if r['kind'] == 'follow']
        self.assertEqual([r['offset'] for r in follow], self.f['quote_offsets_s'])
        self.assertEqual(row['books'], original)
        later = self.observe(T + timedelta(days=2))
        rows = self.rows()
        self.assertIsNone(self.observe(T + timedelta(days=1)))
        self.assertEqual([r['reason'] for r in rows if r['kind'] == 'void'], ['MISSED_WAKE'])
        self.assertIn(T.date().isoformat(), later['candles']['BTC'])

    def test_late_book_cannot_open_new_risk_and_candle_failure_is_per_coin(self):
        self.start()
        venue = Venue(depth=None)
        self.observe(venue=venue)
        later = T + timedelta(days=1)
        clock = FakeClock(later)
        venue = Venue()
        def delayed(_):
            clock.sleep(891)
            return BOOK
        with patch.object(venue, 'book', side_effect=delayed):
            row = e.record(clock(), venue, self.folder, clock, clock.sleep)
        self.assertEqual(row['books']['main']['fills'], [])
        self.assertEqual(row['depth_failures']['BTC'], 'WINDOW_ELAPSED')
        self.assertEqual(row['books']['main']['attempts']['BTC'], ['book_late'])
        venue = Venue()
        with patch.object(venue, 'candles', side_effect=TimeoutError):
            row = self.observe(T + timedelta(days=2), venue)
        self.assertEqual(row['candle_failures'], {'BTC': 'PAGE_UNAVAILABLE'})
        self.assertEqual(row['books']['main']['fills'], [])

    def test_queued_sale_waits_for_later_observable_market(self):
        self.start()
        venue = Venue(coins=('BTC', 'ETH'), short=('ETH',))
        initial = self.observe(venue=venue)
        self.assertEqual(initial['books']['main']['fills'][0]['side'], 'buy')
        blocked = Venue(coins=('BTC', 'ETH'), states={'BTC': pair(ready=False)}, short=('ETH',))
        wait = self.observe(T + timedelta(days=1), blocked)
        self.assertEqual(wait['books']['main']['fills'], [])
        self.assertIn('BTC', wait['books']['main']['queued_sells'])
        clock = FakeClock(T + timedelta(days=2))
        def at_boundary(_):
            clock.sleep(890)
            return BOOK
        with patch.object(venue, 'book', side_effect=at_boundary):
            late = e.record(clock(), venue, self.folder, clock, clock.sleep)
        self.assertEqual(late['books']['main']['fills'], [])
        self.assertEqual(late['books']['main']['attempts']['BTC'], ['book_late'])
        self.assertIn('BTC', late['books']['main']['queued_sells'])
        missed = Venue()
        self.assertEqual(self.observe(T + timedelta(days=3), missed, offset=900)['reason'], 'LATE_WAKE')
        self.assertEqual(missed.product_calls, 0)
        later = self.observe(T + timedelta(days=4), venue)
        fills = later['books']['main']['fills']
        self.assertEqual([(fill['coin'], fill['side']) for fill in fills], [('BTC', 'sell')])
        self.assertAlmostEqual(fills[0]['gross'], -fills[0]['quantity'] * 99)

    def test_accounts_no_hidden_depth_and_persistent_venue_stop(self):
        self.start()
        venue = Venue()
        with patch.object(venue, 'book', side_effect=e.Blocked('venue refused HTTP 451')):
            with self.assertRaises(e.Blocked):
                self.observe(venue=venue)
        with self.assertRaisesRegex(e.Refuse, 'recording stopped'):
            self.observe(T + timedelta(days=1))

    def test_transport_hosts_paths_and_completed_kline_validation(self):
        venue = e.BinanceUS(self.f, gate=self.gate())
        day_ms = self.f['day_s'] * 1000
        opening = int((T - timedelta(days=1)).timestamp()) * 1000
        kline = [opening, '100', '102', '99', '101', '9', opening + day_ms - 1]
        def replies(req, **_):
            parsed = urlsplit(req.full_url)
            self.assertEqual((parsed.scheme, parsed.netloc, req.method), ('https', 'api.binance.us', 'GET'))
            self.assertNotIn('Authorization', req.headers)
            body = {'/api/v3/klines': [kline], '/api/v3/depth': BOOK,
                    '/api/v3/exchangeInfo': {'symbols': [pair() | {'symbol': 'BTCUSD', 'baseAsset': 'BTC', 'quoteAsset': 'USD'},
                                                        {'symbol': 'ETHUSDT', 'baseAsset': 'ETH', 'quoteAsset': 'USDT'}]}}[parsed.path]
            if parsed.path == '/api/v3/klines':
                self.assertEqual(parse_qs(parsed.query), {'symbol': ['BTCUSD'], 'interval': ['1d'], 'limit': ['1'],
                                                          'startTime': [str(opening)], 'endTime': [str(opening + day_ms - 1)]})
            return io.BytesIO(json.dumps(body).encode())
        with patch.object(venue.opener, 'open', side_effect=replies), patch.object(e.time, 'sleep'):
            self.assertEqual(set(venue.products(('BTC', 'ETH'))), {'BTC'})
            self.assertEqual(venue.book('BTC'), BOOK)
            self.assertEqual(venue.candles('BTC', T - timedelta(days=1), T), {'2030-01-05': 101.})
            kline[0], kline[6] = opening + day_ms, opening + 2 * day_ms - 1
            with self.assertRaisesRegex(e.Refuse, 'outside completed UTC fence'):
                venue.candles('BTC', T - timedelta(days=1), T)
            with self.assertRaisesRegex(e.Refuse, 'invalid public endpoint'):
                venue.get('//elsewhere.invalid/data')

    def test_redirects_cross_endpoint_cooldown_restart_and_terminal_stop(self):
        clock = FakeClock(T)
        venue = e.BinanceUS(self.f, self.gate(clock), clock)
        self.assertIsNone(e.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://elsewhere.invalid'))
        with patch.object(venue.opener, 'open', side_effect=HTTPError('', 429, '', {'Retry-After': '60'}, io.BytesIO())) as send:
            with self.assertRaises(e.bx.Cooldown):
                venue.products(('BTC',))
        self.assertEqual(send.call_count, 1)
        restarted = e.BinanceUS(self.f, self.gate(clock), clock)
        with patch.object(restarted.opener, 'open', side_effect=AssertionError('suppressed call')) as send:
            with self.assertRaises(e.bx.Cooldown):
                restarted.book('BTC')
            with self.assertRaises(e.bx.Cooldown):
                e.start(T - timedelta(days=1), START_ID, self.folder, gate=self.gate(clock))
            send.assert_not_called()
        clock.sleep(60)
        restarted.deadline = clock()
        with self.assertRaises(e.bx.Failure):
            restarted.book('BTC')
        restarted.deadline = None
        with patch.object(restarted.opener, 'open', side_effect=HTTPError('', 418, '', {}, io.BytesIO())) as send:
            with self.assertRaises(e.bx.Blocked):
                restarted.book('BTC')
            self.assertEqual(send.call_count, 1)
        clock.sleep(900)
        self.assertTrue((self.temp / 'shared' / 'stop.json').exists())
        with self.assertRaises(e.bx.GateGeneration):
            e.BinanceUS(self.f, self.gate(clock), clock).products(('BTC',))

    def test_gate_generation_mismatch_stops_old_run_and_burned_id_survives_archive(self):
        self.assertEqual(self.start()['venue_generation'], 0)
        self.observe()
        clock = FakeClock(T + timedelta(days=1))
        gate = self.gate(clock)
        gate.write(self.temp / 'shared' / 'stop_generation.json', {'generation': 1})
        venue = e.BinanceUS(self.f, gate, clock)
        with patch.object(venue.opener, 'open', side_effect=AssertionError('old run attempted request')) as send, \
             patch.object(e, 'committed_go', side_effect=AssertionError('retired approval should not be consulted')):
            with self.assertRaises(e.Blocked):
                e.record(clock(), venue, self.folder, clock, clock.sleep)
            send.assert_not_called()
        self.assertEqual(self.rows()[-1]['reason'], 'gate_generation')
        self.folder.rename(self.temp / 'old-run')
        with self.assertRaisesRegex(e.Refuse, 'start ID was already used'):
            self.start()
        with patch.object(e, 'committed_go', return_value=('a' * 40, FAKE_RELEASE)) as auth:
            self.assertEqual(e.start(T, 'new-invented-start', self.folder, gate=gate)['venue_generation'], 1)
            self.assertIn(unittest.mock.call('E13_START', 'new-invented-start', FAKE_RELEASE, 1), auth.call_args_list)

    def test_missing_gate_generation_is_terminal_on_resume(self):
        self.start()
        (self.temp / 'shared' / 'stop_generation.json').unlink()
        with self.assertRaises(e.Blocked):
            e.resume(self.folder, self.gate())
        self.assertEqual(self.rows()[-1]['reason'], 'gate_storage')

    def test_cooldown_voids_wake_and_cannot_recapture_same_day_after_expiry(self):
        self.start()
        self.observe()
        clock = FakeClock(T + timedelta(days=1))
        venue = e.BinanceUS(self.f, self.gate(clock), clock)
        with patch.object(venue.opener, 'open', side_effect=HTTPError('', 429, '', {'Retry-After': '60'}, io.BytesIO())) as send:
            row = e.record(clock(), venue, self.folder, clock, clock.sleep)
            self.assertEqual(row['reason'], 'SHARED_COOLDOWN')
            self.assertEqual(send.call_count, 1)
        clock.sleep(60)
        restart = e.BinanceUS(self.f, self.gate(clock), clock)
        self.assertIsNone(e.record(clock(), restart, self.folder, clock, clock.sleep))
        self.assertEqual(e.alive(self.folder)['cooldown_void_wakes'], 1)

    def test_gate_persistence_failure_does_not_retry_http(self):
        clock = FakeClock(T)
        venue = e.BinanceUS(self.f, self.gate(clock), clock)
        response = HTTPError('', 429, '', {'Retry-After': '60'}, io.BytesIO())
        original = venue.gate.write
        def fault(path, body):
            if path.name == 'cooldown.json':
                raise OSError('invented disk fault')
            return original(path, body)
        with patch.object(venue.gate, 'write', side_effect=fault), \
             patch.object(venue.opener, 'open', side_effect=response) as send:
            with self.assertRaises(e.bx.GateStorage):
                venue.products(('BTC',))
            self.assertEqual(send.call_count, 1)
        self.assertTrue((self.temp / 'shared' / 'inflight.json').exists())

    def test_known_200_body_errors_are_failed_pages_not_http_policy(self):
        clock = FakeClock(T)
        venue = e.BinanceUS(self.f, self.gate(clock), clock, sleep=clock.sleep)
        class Reply(io.BytesIO):
            status = 200

        for failure in (RuntimeError('invented parser failure'), ValueError('invented read failure'),
                        HTTPError('', 429, '', {'Retry-After': '900'}, io.BytesIO()),
                        HTTPError('', 451, '', {}, io.BytesIO())):
            if isinstance(failure, HTTPError):
                self.addCleanup(failure.close)
            with self.subTest(failure=failure):
                response = Reply()
                with patch.object(response, 'read', side_effect=failure), \
                     patch.object(venue.opener, 'open', return_value=response) as send:
                    with self.assertRaisesRegex(e.Refuse, 'public response body unavailable'):
                        venue.book('BTC')
                    self.assertEqual(send.call_count, 1)
                for name in ('inflight.json', 'cooldown.json', 'stop.json'):
                    self.assertFalse((self.temp / 'shared' / name).exists(), name)
        with patch.object(venue.opener, 'open', return_value=io.BytesIO(json.dumps(BOOK).encode())):
            self.assertEqual(venue.book('BTC'), BOOK)

    def test_policy_applies_to_status_on_ordinary_response_objects(self):
        clock = FakeClock(T)
        venue = e.BinanceUS(self.f, self.gate(clock), clock, sleep=clock.sleep)
        class Reply(io.BytesIO):
            headers = {'Retry-After': '63'}

            def __init__(self, status):
                super().__init__()
                self.code = status

            def getcode(self):
                return self.code

            def read(self, size):
                raise AssertionError('policy status should not need a body')

            def close(self):
                if not self.closed:
                    super().close()
                    raise RuntimeError('invented close error')

        for status in (429, 403):
            response = Reply(status)
            with patch.object(response, 'read', wraps=response.read) as read, \
                 patch.object(venue.opener, 'open', return_value=response) as send:
                if status == 429:
                    with self.assertRaises(e.bx.Cooldown) as refused:
                        venue.book('BTC')
                    self.assertEqual(refused.exception.not_before, clock() + timedelta(seconds=63))
                else:
                    with self.assertRaises(e.bx.Blocked) as refused:
                        venue.book('BTC')
                    self.assertEqual(refused.exception.status, 403)
                self.assertEqual(send.call_count, 1)
                read.assert_not_called()
            clock.sleep(63)

    def test_no_status_failures_hold_shared_60_then_900_second_cooldowns(self):
        clock = FakeClock(T)
        for seconds in (60, 60, 900):
            venue = e.BinanceUS(self.f, self.gate(clock), clock)
            with patch.object(venue.opener, 'open', side_effect=URLError('invented disconnect')) as send:
                with self.assertRaises(e.bx.Cooldown) as refused:
                    venue.products(('BTC',))
                self.assertEqual(refused.exception.not_before, clock() + timedelta(seconds=seconds))
                self.assertEqual(send.call_count, 1)
            self.assertFalse((self.temp / 'shared' / 'inflight.json').exists())
            restarted = e.BinanceUS(self.f, self.gate(clock), clock)
            with patch.object(restarted.opener, 'open', side_effect=AssertionError('suppressed call')) as send:
                with self.assertRaises(e.bx.Cooldown):
                    restarted.book('BTC')
                with self.assertRaises(e.bx.Cooldown):
                    e.start(T - timedelta(days=1), START_ID, self.folder, gate=self.gate(clock))
                send.assert_not_called()
            clock.sleep(seconds)
        # Receiving headers is a known HTTP reply even if reading the body fails.
        class FailedBody(io.BytesIO):
            def read(self, size):
                raise TimeoutError('invented body timeout')
        with patch.object(restarted.opener, 'open', return_value=FailedBody()):
            with self.assertRaisesRegex(e.Refuse, 'response body unavailable'):
                restarted.book('BTC')
        with patch.object(restarted.opener, 'open', side_effect=TimeoutError('invented response timeout')):
            with self.assertRaises(e.bx.Cooldown) as refused:
                restarted.products(('BTC',))
        self.assertEqual(refused.exception.not_before, clock() + timedelta(seconds=60))

    def test_no_status_wait_crossing_deadline_voids_wake_without_local_stop(self):
        self.start()
        self.observe()
        tomorrow = T + timedelta(days=1)
        clock = FakeClock(tomorrow, 850)
        venue = e.BinanceUS(self.f, self.gate(clock), clock)
        with patch.object(venue.opener, 'open', side_effect=TimeoutError('invented response timeout')) as send:
            row = e.record(clock(), venue, self.folder, clock, clock.sleep)
            self.assertEqual(row['reason'], 'SHARED_COOLDOWN')
            self.assertEqual(send.call_count, 1)
        clock.sleep(60)
        self.assertIsNone(e.record(clock(), venue, self.folder, clock, clock.sleep))
        self.assertEqual(e.alive(self.folder)['status'], 'OBSERVING')
        self.assertEqual(self.observe(tomorrow + timedelta(days=1))['kind'], 'wake')

    def test_no_status_book_retry_within_window_records_delay_without_changing_intent(self):
        self.start()
        clock = FakeClock(T)
        venue = e.BinanceUS(self.f, self.gate(clock), clock, sleep=clock.sleep)
        source = Venue()
        attempts = []
        def look(req, **_):
            self.assertEqual(urlsplit(req.full_url).path, '/api/v3/depth')
            plan = next(r for r in self.rows() if r['kind'] == 'decision')
            attempts.append((clock(), plan))
            if len(attempts) == 1:
                raise URLError('invented disconnect')
            return io.BytesIO(json.dumps(BOOK).encode())
        with patch.object(venue.opener, 'open', side_effect=look), \
             patch.object(venue, 'products', side_effect=source.products), \
             patch.object(venue, 'candles', side_effect=source.candles):
            row = e.record(clock(), venue, self.folder, clock, clock.sleep)
        self.assertGreaterEqual((attempts[1][0] - attempts[0][0]).total_seconds(), 60)
        self.assertEqual(attempts[0][1], attempts[1][1])
        self.assertEqual(row['intent'], attempts[0][1]['intent'])
        fill = row['books']['main']['fills'][0]
        self.assertEqual(fill['side'], 'buy')
        self.assertEqual(fill['delay_s'], 60.)

    def test_private_journal_records_all_retry_endpoints_and_failed_second_look(self):
        endpoints = ('/api/v3/exchangeInfo', '/api/v3/klines', '/api/v3/depth')
        fixture_root = self.temp
        for failed_depth in (False, True):
            with self.subTest(failed_depth=failed_depth):
                self.temp = fixture_root / f'retries-{failed_depth}'
                self.temp.mkdir()
                self.folder = self.temp / 'run'
                clock = FakeClock(T)
                self.start()
                venue = e.BinanceUS(self.f, self.gate(clock), clock, sleep=clock.sleep)
                source = Venue()
                calls = {path: [] for path in endpoints}
                day_ms = self.f['day_s'] * 1000

                class Reply(io.BytesIO):
                    status = 200

                class FailedBody(Reply):
                    def read(self, size):
                        raise RuntimeError('invented failed retry body')

                def invented(req, **_):
                    url = urlsplit(req.full_url)
                    calls[url.path].append(clock())
                    number = len(calls[url.path])
                    if number == 1:
                        raise URLError('invented no-status disconnect')
                    if number == 2:
                        pending = [r for r in self.rows() if r['kind'] == 'retry' and r['endpoint'] == url.path]
                        self.assertEqual(len(pending), 1)
                        self.assertEqual(pending[0]['outcome'], 'PENDING')
                        self.assertEqual(pending[0]['first_attempt_at'], e.iso(calls[url.path][0]))
                    if url.path == endpoints[0]:
                        body = {'symbols': [pair() | {'symbol': 'BTCUSD', 'baseAsset': 'BTC', 'quoteAsset': 'USD'}]}
                    elif url.path == endpoints[1]:
                        query = parse_qs(url.query)
                        lo = datetime.fromtimestamp(int(query['startTime'][0]) / 1000, e.UTC)
                        hi = datetime.fromtimestamp((int(query['endTime'][0]) + 1) / 1000, e.UTC)
                        body = []
                        for day, price in source.candles('BTC', lo, hi).items():
                            opening = int(datetime.fromisoformat(day).replace(tzinfo=e.UTC).timestamp()) * 1000
                            body.append([opening, '1', '1', '1', str(price), '1', opening + day_ms - 1])
                    elif number == 2 and failed_depth:
                        return FailedBody()
                    else:
                        body = BOOK
                    return Reply(json.dumps(body).encode())

                with patch.object(venue.opener, 'open', side_effect=invented):
                    row = e.record(clock(), venue, self.folder, clock, clock.sleep)
                results = [r for r in self.rows() if r['kind'] == 'retry_outcome']
                self.assertEqual([r['endpoint'] for r in results], list(endpoints))
                self.assertEqual([r['coin'] for r in results], [None, 'BTC', 'BTC'])
                self.assertEqual([r['outcome'] for r in results], ['SUCCESS', 'SUCCESS', 'BODY_UNAVAILABLE' if failed_depth else 'SUCCESS'])
                self.assertEqual([r['http_status'] for r in results], [200, 200, 200])
                for result in results:
                    first, retry = calls[result['endpoint']][:2]
                    self.assertEqual(result['first_attempt_at'], e.iso(first))
                    self.assertEqual(result['retry_at'], e.iso(retry))
                    self.assertEqual(result['delay_s'], (retry - first).total_seconds())
                    self.assertGreaterEqual(result['delay_s'], 60.)
                    self.assertTrue(any(r['kind'] == 'retry' and r['sha256'] == result['retry_sha256'] for r in self.rows()))
                if failed_depth:
                    self.assertEqual(row['depth_failures'], {'BTC': 'PAGE_UNAVAILABLE'})
                    self.assertFalse(row['books']['main']['fills'])
                else:
                    self.assertEqual(row['books']['main']['fills'][0]['delay_s'], 60.)
                self.assertNotIn('retry_outcome', json.dumps(e.alive(self.folder)))

    def test_unknown_status_process_interruption_still_requires_resolution(self):
        clock = FakeClock(T)
        venue = e.BinanceUS(self.f, self.gate(clock), clock)
        with patch.object(venue.opener, 'open', side_effect=KeyboardInterrupt) as send:
            with self.assertRaises(KeyboardInterrupt):
                venue.products(('BTC',))
            self.assertEqual(send.call_count, 1)
        self.assertTrue((self.temp / 'shared' / 'inflight.json').exists())
        restarted = e.BinanceUS(self.f, self.gate(clock), clock)
        with patch.object(restarted.opener, 'open', side_effect=AssertionError('suppressed call')) as send:
            with self.assertRaises(e.bx.GateUncertain):
                restarted.book('BTC')
            with self.assertRaises(e.bx.GateUncertain):
                e.start(T - timedelta(days=1), START_ID, self.folder, gate=self.gate(clock))
            send.assert_not_called()

    def test_committed_closed_bar_decision_precedes_all_books_and_does_not_change(self):
        decisions = []
        for i, book in enumerate((BOOK, {'asks': [[155., 100.]], 'bids': [[150., 100.]]})):
            self.folder = self.temp / f'case-{i}'
            self.start()
            venue = Venue(coins=('BTC', 'ETH'), short=('ETH',))
            seen = []
            def verify(coin):
                rows = self.rows()
                decision = next(r for r in rows if r['kind'] == 'decision')
                self.assertEqual(decision['order_coins'], ['BTC'])
                self.assertEqual(decision['intent']['main']['BTC']['side'], 'buy')
                self.assertEqual(coin, 'BTC')
                seen.append(decision)
                return book
            with patch.object(venue, 'book', side_effect=verify):
                row = self.observe(venue=venue)
            self.assertTrue(seen)
            self.assertEqual(row['decision_sha256'], seen[0]['sha256'])
            self.assertEqual(row['intent'], seen[0]['intent'])
            self.assertEqual(row['books']['main']['fills'][0]['side'], 'buy')
            decisions.append(row['intent'])
        self.assertEqual(*decisions)

    def test_durable_claim_stops_first_on_either_side_of_inventory_or_book(self):
        for stage in ('products', 'candles', 'book', 'before_finalize'):
            with self.subTest(stage=stage):
                self.folder = self.temp / stage
                self.start()
                venue = Venue()
                def crash(*_):
                    self.assertIn('claim', [r['kind'] for r in self.rows()])
                    raise KeyboardInterrupt
                original = e.append
                def finalize(fd, rows, row):
                    if row['kind'] == 'wake':
                        crash()
                    return original(fd, rows, row)
                hook = patch.object(e, 'append', side_effect=finalize) if stage == 'before_finalize' else patch.object(venue, stage, side_effect=crash)
                with hook, self.assertRaises(KeyboardInterrupt):
                    self.observe(venue=venue)
                restart = Venue()
                with self.assertRaisesRegex(e.Blocked, 'first wake interrupted'):
                    self.observe(venue=restart)
                self.assertEqual(restart.product_calls, 0)
                self.assertEqual(self.rows()[-1]['reason'], 'FIRST_WAKE_INTERRUPTED')

    def test_later_torn_final_commit_is_void_and_not_replayed(self):
        self.start()
        self.observe()
        tomorrow = T + timedelta(days=1)
        original = e.os.replace
        def crash(src, dst, *args, **kwargs):
            if src == 'tip.tmp' and (self.folder / 'log.jsonl').read_text().splitlines()[-1].find('"kind":"wake"') >= 0:
                raise KeyboardInterrupt
            return original(src, dst, *args, **kwargs)
        with patch.object(e.os, 'replace', side_effect=crash), self.assertRaises(KeyboardInterrupt):
            self.observe(tomorrow)
        restart = Venue()
        self.assertEqual(self.observe(tomorrow, restart)['reason'], 'WAKE_INTERRUPTED')
        self.assertIsNone(self.observe(tomorrow, restart))
        self.assertEqual(restart.product_calls, 0)
        self.assertEqual(e.alive(self.folder)['interrupted_wakes'], 1)

    def test_committed_local_main_action_release_pins_and_git_overrides(self):
        target = self.temp / 'repo'
        target.mkdir()
        clean = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        def local(*args):
            return subprocess.check_output(('git', *args), cwd=target, env=clean, stderr=subprocess.DEVNULL).decode().strip()
        local('init', '-b', 'main')
        local('config', 'user.name', 'Invented')
        local('config', 'user.email', 'invented@example.invalid')
        local('config', 'commit.gpgsign', 'false')
        for path in e.PINNED + (e.LEDGER,):
            fixture = target / path
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text('invented\n')
        (target / e.CONFIG).write_text('''forward_e13: {value: {operations_ref: operations}}
operations: {value: {rule_key: rule, second_fee_key: fee}}
rule: {value: {}}
fee: {value: {}}
binance_us_gate: {value: {}}
''')
        ledger = target / e.LEDGER
        placeholder = '| 231 | `E13_START=<id>` `E13_RELEASE=<hash>` `E13_SCORE_GO=<id>` |\n'
        ledger.write_text(placeholder)
        def commit():
            local('add', '.')
            local('commit', '-m', 'invented local fixture')
            return local('rev-parse', 'HEAD')
        audited = commit()
        good = f'| 231 | `E13_RELEASE={audited}` `E13_START={START_ID}` `E13_SCORE_GO={SCORE_ID}` |\n'
        start = lambda: self.real_authority('E13_START', START_ID)
        with patch.object(e, 'ROOT', target):
            local('switch', '-c', 'wrong')
            ledger.write_text(good)
            commit()
            with patch.dict(os.environ, {'GIT_DIR': str(target / '.git'), 'GIT_NAMESPACE': 'wrong',
                                          'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.worktree',
                                          'GIT_CONFIG_VALUE_0': str(self.temp / 'elsewhere')}):
                with self.assertRaisesRegex(e.Refuse, 'lead go missing'):
                    start()
            local('switch', 'main')
            ledger.write_text(good)
            with self.assertRaisesRegex(e.Refuse, 'lead go missing'):
                start()
            for invalid in (good.replace('| 231 |', '| 230 |'), good.replace(f'`E13_START={START_ID}`',
                                                                          f'`E13_START={START_ID}` `E13_START=other`')):
                ledger.write_text(invalid)
                commit()
                with self.assertRaisesRegex(e.Refuse, 'lead go missing'):
                    start()
            ledger.write_text(good)
            approval = commit()
            self.assertEqual(start(), (approval, audited))
            with self.assertRaisesRegex(e.Refuse, 'lead go missing'):
                self.real_authority('E13_START', START_ID, audited, 1)
            ledger.write_text(good.replace(' |\n', ' `E13_START_GENERATION=1` |\n'))
            approval = commit()
            self.assertEqual(self.real_authority('E13_START', START_ID, audited, 1), (approval, audited))
            with self.assertRaisesRegex(e.Refuse, 'different venue generation'):
                self.real_authority('E13_START', START_ID, audited, 2)
            with patch.dict(os.environ, {'GIT_DIR': str(self.temp / 'wrong.git'), 'GIT_WORK_TREE': '/' }):
                self.assertEqual(start(), (approval, audited))
            self.assertEqual(self.real_authority('E13_SCORE_GO', SCORE_ID, audited), (approval, audited))
            with self.assertRaisesRegex(e.Refuse, 'lead go missing'):
                self.real_authority('E13_SCORE_GO', START_ID, audited)
            with self.assertRaisesRegex(e.Refuse, 'audited release changed'):
                self.real_authority('E13_SCORE_GO', SCORE_ID, FAKE_RELEASE)
            ledger.write_text(placeholder)
            with self.assertRaisesRegex(e.Refuse, 'freeze files differ'):
                start()
            local('restore', str(ledger.relative_to(target)))
            local('switch', '--detach', audited)
            self.assertEqual(start(), (approval, audited))
            (target / e.PINNED[0]).write_text('not audited\n')
            commit()
            with self.assertRaisesRegex(e.Refuse, 'audited release pins'):
                start()

    def test_public_summary_only_and_private_hash_chain(self):
        self.assertEqual(json.loads(e.PUBLIC.read_text()), e.summary([], self.f))
        self.start()
        self.observe()
        out = self.temp / 'aggregate.json'
        result = e.publish(self.folder, out)
        self.assertEqual(result['lines']['main']['fills'], 1)
        self.assertEqual(result['lines']['shown']['attempt_flags']['insufficient_depth'], 1)
        for secret in ('BTC', '123.456789', '"depth"', '"quantity"', '"gross"', '"received"', START_ID, '"net"'):
            self.assertNotIn(secret, out.read_text())
        journal = self.folder / 'log.jsonl'
        self.assertEqual(stat.S_IMODE(journal.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.folder.stat().st_mode), 0o700)
        before = journal.read_text()
        journal.write_text(before.replace('invented-start', 'different-start', 1))
        with self.assertRaisesRegex(e.Refuse, 'chain'):
            self.rows()
        journal.write_text(''.join(before.splitlines(keepends=True)[:-1]))
        with self.assertRaisesRegex(e.Refuse, 'tip'):
            self.rows()

    def test_locks_and_score_time_gate_only_never_run_score(self):
        self.start()
        with e.private(self.folder) as fd, e.lock(fd, 'writer.lock'):
            with self.assertRaisesRegex(e.Refuse, 'another writer'):
                self.observe()
        row = self.observe()
        days = self.f['score_days']
        closing = {'kind': 'close'}
        with self.assertRaisesRegex(e.Refuse, 'year incomplete'):
            e.score_gate([row, closing], T + timedelta(days=days), days)
        with self.assertRaisesRegex(e.Refuse, 'closing observation missing'):
            e.score_gate([row], T + timedelta(days=days, seconds=10), days)
        self.assertIs(e.score_gate([row, closing], T + timedelta(days=days, seconds=10), days), row)
        with self.assertRaisesRegex(e.Refuse, 'already read'):
            e.score_gate([row, closing, {'kind': 'score'}], T + timedelta(days=days, seconds=10), days)
