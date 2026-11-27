"""Invented candles, books, clocks, authorization and filesystem only. No scorer runs."""
import io
import json
import stat
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

from practice import forward_e13 as e

T = datetime(2030, 1, 6, tzinfo=e.UTC)
START_ID = 'invented-start'
SCORE_ID = 'invented-score'
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
        git = patch.object(e, 'git', side_effect=self.git)
        self.addCleanup(git.stop)
        git.start()
        self.f, self.rule, self.fees = e.settings()

    def git(self, command, *args):
        self.assertIn(command, ('status', 'rev-parse', 'show'))
        return {'status': b'', 'rev-parse': b'a' * 40 + b'\n', 'show': LEDGER}[command]

    def start(self):
        return e.start(T - timedelta(days=1), START_ID, self.folder)

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
            e.start(T - timedelta(days=1), SCORE_ID, self.folder)
        self.assertFalse(self.folder.exists())
        self.assertEqual(e.clock_at(self.start()['first']), T)

    def test_no_quotes_before_scheduled_time_or_if_original_go_is_missing(self):
        self.start()
        venue = Venue()
        self.assertIsNone(self.observe(venue=venue, offset=9))
        with patch.object(e, 'git', return_value=b'| 231 | No authorization |\n'):
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
        row = self.observe(T + timedelta(days=1), offset=901)
        self.assertEqual(row['books']['main']['fills'], [])
        self.assertIn('void_buy', row['books']['main']['attempts']['BTC'])
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
        later = self.observe(T + timedelta(days=2), venue, offset=901)
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
        venue = e.BinanceUS(self.f)
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

    def test_redirects_blocked_and_429_backoff_then_refusal(self):
        venue = e.BinanceUS(self.f)
        with self.assertRaises(e.Blocked):
            e.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://elsewhere.invalid')
        replies = [HTTPError('', 429, '', {'Retry-After': '7'}, io.BytesIO()), HTTPError('', 451, '', {}, io.BytesIO())]
        with patch.object(venue.opener, 'open', side_effect=replies) as opener, patch.object(e.time, 'sleep') as sleep:
            with self.assertRaisesRegex(e.Blocked, '451'):
                venue.products(('BTC',))
        self.assertEqual(opener.call_count, 2)
        self.assertIn(unittest.mock.call(7.), sleep.call_args_list)

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
