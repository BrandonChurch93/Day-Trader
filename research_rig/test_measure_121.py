"""M121 synthetic-only rule and interlock tests. No network, feed or live paths."""

from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal as D
import gzip
import io
import json
import os
from pathlib import Path
import resource
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

import measure_121 as m


DAY = '2025-09-08'
SECOND = m.NS


def fake_settings():
    c = m.settings()
    return replace(c, sample=dict(c.sample, selected_in_hash_order={'equity': ['GDO']}, walk_type_order=['equity'], sessions=[DAY]),
                   order=dict(c.order, placement_times=['10:00:00']),
                   limits=dict(c.limits, planned_fund_days=1, planned_order_slots=1), excluded_tickers=frozenset(),
                   report=dict(c.report, bootstrap_draws=100, min_primary_marked_fund_days_per_type=1,
                               min_primary_marked_funds_per_type=1, min_primary_marked_dates=1))


def times(cfg):
    start, end, close, (t,) = cfg.clocks(DAY)
    live = t + cfg.order['entry_delay_seconds'] * SECOND
    return start, end, close, t, live, live + cfg.order['rest_seconds'] * SECOND


def quote(t, b='10.00', a='10.08', bs=1, **kw):
    r = dict(bp=D(b), ap=D(a), bs=bs, bx='N', ax='N', z='A', c=['R'])
    r['as'] = 1
    r.update(kw)
    return r, t


def trade(t, ident=1, p='9.99', size=50, **kw):
    return dict(dict(i=ident, p=D(p), s=size, z='A', x='N', c=[' ', 'I']), **kw), t


class OrderTest(unittest.TestCase):
    def setUp(self):
        self.c = fake_settings()
        self.op, self.end, self.close, self.t, self.live, self.expiry = times(self.c)
        self.hit = self.live + SECOND
        self.h = {k: self.hit + s * SECOND for k, s in self.c.order['mark_seconds_after_fill'].items()}

    def day(self, qs=None, ts=None, halts=()):
        qs = [quote(self.t - SECOND)] if qs is None else qs
        ts = [trade(self.hit)] if ts is None else ts
        def ordered(items):
            return sorted(items, key=lambda item: -1 if item[1] is None else item[1])
        rows, self.stats = m.measure_day(self.c, 'equity', 'GDO', DAY, ordered(qs), ordered(ts), halts)
        return rows[0]

    def test_valid_nanosecond_and_full_size_original_limit(self):
        marks = [quote(x - 1, b='9.98', a='10.10', ax='P', bx='P', c=['R', 'R']) for x in self.h.values()]
        marks.extend([quote(self.close - 1, b='9.97', a='10.12'), quote(self.end, b='20', a='21')])
        r = self.day([quote(self.t - 1), *marks])
        self.assertEqual((r['state'], r['l'], r['size'], r['print_kind']), ('filled', '10.00', 50, 'odd_lot'))
        self.assertTrue(all(r['marks'][k] == ['9.98', '10.10'] for k in self.h))
        self.assertEqual(r['marks']['close'], ['9.97', '10.12'])
        vector, _ = m.vector(r, self.c)
        self.assertEqual(vector['short_gross_bps'], (-20, 1))
        self.assertEqual(vector['short_adverse_usd'][0], 0)
        self.assertEqual(vector['entry_ask_saved_bps'], (80, 1))
        self.assertEqual(vector['short_fraction_kept'][0] / vector['short_fraction_kept'][1], D('-.5'))

    def test_no_future_or_exact_or_conflicting_quote(self):
        cases = [([quote(self.t + 1)], 'placement_quote_absent'),
                 ([quote(self.t - 1), quote(self.t)], 'placement_quote_exact_boundary'),
                 ([quote(self.t - 1), quote(self.t - 1, b='10.01')], 'placement_quote_conflict'),
                 ([quote(self.t - 1), quote(self.live)], 'activation_quote_exact_boundary'),
                 ([quote(self.t - 1), quote(None)], 'placement_quote_bad_timestamp'),
                 ([quote(self.t - SECOND), quote(self.t - 1, c=['O'])], 'placement_quote_ineligible'),
                 ([quote(self.t - 1, c=None)], 'placement_quote_critical_field'),
                 ([quote(self.t - 1, c=[])], 'placement_quote_ineligible'),
                 ([quote(self.t - 1, b='10.001')], 'placement_quote_bid_grid_or_floor'),
                 ([quote(self.t - 1, b='.99')], 'placement_quote_bid_grid_or_floor')]
        for qs, reason in cases:
            with self.subTest(reason=reason):
                self.assertEqual(self.day(qs)['reason'], reason)
        self.assertEqual(self.day([quote(self.t - 1)] * 2)['state'], 'filled')

    def test_age_caps_and_activation_moved(self):
        age = self.c.order['quote_max_age_seconds'] * SECOND
        self.assertEqual(self.day([quote(self.t - age - 1)])['reason'], 'placement_quote_stale')
        self.assertEqual(self.day([quote(self.t - age)])['reason'], 'activation_quote_stale')
        self.assertEqual(self.day([quote(self.live - age)])['state'], 'filled')
        for q in (quote(self.t + 1, b='10.01'), quote(self.t + 1, bx='P')):
            self.assertEqual(self.day([quote(self.t - 1), q])['state'], 'not_placed')
        self.assertEqual(self.day([quote(self.t - 1, b='501', a='502')])['reason'], 'no_whole_shares')

    def test_nonqualifying_trades_never_combine(self):
        for tr in (trade(self.hit, x='D'), trade(self.hit, x='?'), trade(self.hit, x='P'),
                   trade(self.hit, z='B'), trade(self.hit, p='10.00'), trade(self.hit, p='9.991'),
                   trade(self.live), trade(self.expiry), trade(self.hit, c=[]), trade(self.hit, c=['I']),
                   trade(self.hit, c=['I', ' ']), trade(self.hit, c=[' ', 'F', 'I']), trade(self.hit, c=[' ', 'Q']),
                   trade(self.hit, c=[' ', '4']), trade(self.hit, c=[' ', 'Z']), trade(self.hit, c=[' ', 'X'])):
            with self.subTest(tr=tr):
                self.assertEqual(self.day(ts=[tr])['state'], 'unfilled')
        self.assertEqual(self.day(ts=[trade(self.hit, size=49), trade(self.hit, ident=2, size=49)])['state'], 'unfilled')
        self.assertEqual(self.day(ts=[trade(self.hit, p='9.989', c=[' '])])['print_kind'], 'regular')

    def test_unknown_trades_and_conflicts(self):
        self.assertEqual(self.day(ts=[])['reason'], 'trade_stream_empty')
        self.assertEqual(self.day(ts=[trade(self.end)])['reason'], 'trade_stream_empty')
        for bad in (trade(self.hit, c=None), trade(self.hit, i=None), trade(self.hit, x=None), trade(self.hit, s='50')):
            self.assertEqual(self.day(ts=[bad])['reason'], 'trade_critical_field')
        self.assertEqual(self.day(ts=[trade(None), trade(self.op, ident=2)])['reason'], 'trade_critical_field')
        self.assertEqual(self.day(ts=[trade(self.hit, c=None, x='P')])['state'], 'unfilled')
        self.assertEqual(self.day(ts=[trade(self.hit, c=None, size=1)])['state'], 'unfilled')
        a = trade(self.hit)
        self.assertEqual(self.day(ts=[a, a])['state'], 'filled')
        self.assertEqual(self.day(ts=[a, trade(self.hit + 1, p='10.00')])['reason'], 'trade_conflicting_id')
        self.assertEqual(self.day(ts=[a, trade(self.hit, ident=2), trade(self.hit + 1, p='10.00')])['state'], 'filled')
        self.assertEqual(self.day(ts=[a, trade(self.hit, ident=2, c=[' '])])['print_kind'], 'mixed_tie')
        self.assertEqual(self.day(ts=[a, trade(self.hit, ident=2, c=None)])['reason'], 'trade_critical_field')
        self.assertEqual(self.day(ts=[a, trade(self.hit, ident=2, c=None, size=1)])['state'], 'filled')

    def test_empty_trades_preserve_known_nonplacements_and_quote_unknowns(self):
        self.assertEqual(self.day([quote(self.t - 1), quote(self.t + 1, b='10.01')], ts=[])['state'], 'not_placed')
        self.assertEqual(self.day([quote(self.t - 1, b='501', a='502')], ts=[])['reason'], 'no_whole_shares')
        self.assertEqual(self.day(qs=[], ts=[])['reason'], 'placement_quote_absent')

    def test_marks_distinguish_unknown_and_zero(self):
        h = self.h
        qs = [quote(self.t - 1), quote(h['primary'] - 1, b='10.00'), quote(h['long'])]
        r = self.day(qs)
        self.assertEqual(r['marks'], {'short': 'quote_stale', 'primary': ['10.00', '10.08'],
                                      'long': 'quote_exact_boundary', 'close': 'quote_stale'})
        self.assertEqual(m.vector(r, self.c)[0]['primary_gross_bps'], (0, 1))
        r = self.day([quote(self.t - 1, b='2', a='2.1'), quote(h['short'] - 1, bs=2)],
                     [trade(self.hit, size=250, p='1.99', c=[' '])])
        self.assertEqual(r['marks']['short'], 'quote_bid_size')

    def test_halt_at_entry_or_during_rest_and_after_resumption(self):
        self.assertEqual(self.day(halts=[(self.t, self.t + 1)])['reason'], 'halt_order')
        self.assertEqual(self.day(halts=[(self.hit + SECOND, None)])['reason'], 'halt_order')
        r = self.day([quote(self.t - 1), quote(self.t + 1, b='10.01')], halts=[(self.hit + SECOND, None)])
        self.assertEqual(r['reason'], 'halt_order')
        r = self.day([quote(self.t - 1), quote(self.close - SECOND)], halts=[(self.expiry + 1, None)])
        self.assertEqual(r['marks']['close'], 'halt')
        r = self.day([quote(self.t - 1), quote(self.close - SECOND)], halts=[(self.expiry + 1, self.close - 1)])
        self.assertEqual(r['marks']['close'], 'quote_before_resumption')
        r = self.day([quote(self.t - 1), quote(self.close - 1)], halts=[(self.expiry + 1, self.close - SECOND)])
        self.assertIsInstance(r['marks']['close'], list)


class PagesTest(unittest.TestCase):
    def setUp(self):
        self.c = fake_settings()

    def test_clock_parses_exact_ns_and_timezone(self):
        a = m.timestamp('2025-09-08T14:00:01.123456789Z')
        self.assertEqual(a, m.timestamp('2025-09-08T10:00:01.123456789-04:00'))
        self.assertEqual(a - m.timestamp('2025-09-08T14:00:01.123456788Z'), 1)
        self.assertIsNone(m.timestamp('2025-09-08T14:00:01.1234567891Z'))
        self.assertIsNone(m.timestamp('2025-09-08T14:00:01'))

    def run_pages(self, pages, cap=None):
        queue = iter(pages)
        seen = []
        def send(url, args, *_):
            self.assertEqual(url, 'https://data.alpaca.markets/v2/stocks/GDO/trades')
            self.assertEqual((args['asof'], args['feed'], args['sort']), (DAY, 'sip', 'asc'))
            self.assertTrue(args['start'].endswith('-04:00'))
            seen.append(args.get('page_token'))
            raw = m.json_bytes(next(queue))
            return raw, len(raw)
        c = self.c if cap is None else replace(self.c, limits=dict(self.c.limits, **cap))
        p = m.Paged(c, send)
        self.p = p
        return list(p.records('GDO', DAY, 'trades')), p.requests, seen

    def test_pages_count_and_terminal_empty_forms(self):
        rows, count, tokens = self.run_pages([dict(trades=[], next_page_token='x'), dict(trades=None, next_page_token=None)])
        self.assertEqual((rows, count, tokens), ([], 2, [None, 'x']))

    def test_bad_paging_and_budget_stop_no_retry(self):
        for pages, cap, reason, count in (
            ([dict(trades=[])], None, 'page_shape_or_symbol', 1),
            ([dict(trades=[], next_page_token='')], None, 'bad_or_repeated_cursor', 1),
            ([dict(trades=[], next_page_token='x')] * 2, None, 'bad_or_repeated_cursor', 2),
            ([dict(trades=[], next_page_token='x')], {'pages_per_endpoint_per_day': 1}, 'nonterminal_at_cap', 1),
            ([dict(trades=[], next_page_token='x')], {'history_requests_total': 1}, 'nonterminal_at_cap', 1),
            ([dict(trades=[dict(t='2025-09-08T16:00:00Z'), dict(t='2025-09-08T15:00:00Z')], next_page_token=None)],
             None, 'page_timestamp_regression', 1)):
            with self.subTest(reason=reason), self.assertRaisesRegex(m.Stop, reason):
                try:
                    self.run_pages(pages, cap)
                finally:
                    self.assertEqual(self.p.requests, count)

    def test_compressed_and_wire_caps(self):
        class Raw(io.BytesIO):
            def read(self, n=-1, *, decode_content=False):
                self_outer.assertFalse(decode_content)
                return super().read(n)
        self_outer = self
        class Response:
            def __init__(self, wire, encoding='gzip', status=200):
                self.raw, self.status_code, self.headers = Raw(wire), status, {'Content-Encoding': encoding}
        payload = b'x' * 10_000
        wire = gzip.compress(payload)
        self.assertEqual(m.read_page(Response(wire), len(payload), len(wire)), (payload, len(wire)))
        with self.assertRaisesRegex(m.Stop, 'decoded_page_cap'):
            m.read_page(Response(wire), len(payload)-1, len(wire))
        with self.assertRaisesRegex(m.Stop, 'wire_page_cap'):
            m.read_page(Response(wire), len(payload), len(wire)-1)
        with self.assertRaisesRegex(m.Stop, 'vendor_http_status'):
            m.read_page(Response(wire, status=302), len(payload), len(wire))


class BootstrapTest(unittest.TestCase):
    def setUp(self):
        self.c = fake_settings()

    def filled(self, day=DAY, mark='10.02'):
        return dict(m.base_row('equity', 'GDO', day, '10:00:00', 'filled'), l='10.00', a='10.04', size=50,
                    print_kind='regular', marks={k: [mark, '10.08'] for k in ('short', 'primary', 'long', 'close')})

    def test_exact_lower_and_rate_survive_report(self):
        rows = [self.filled(), self.filled('2025-09-09')]
        out = m.summarize(rows, self.c)
        self.assertTrue(out['consider_later_strategy_test'])
        self.assertEqual(out['by_group']['pooled']['fill_rate_headline'], 1)
        for b in out['bootstrap'].values():
            self.assertAlmostEqual(b['pooled']['primary_gross_bps']['lower'], 20)
            self.assertEqual(b['pooled']['primary_gross_bps']['undefined_draws'], 0)
        self.assertFalse(m.summarize([self.filled(mark='10.00')], self.c)['consider_later_strategy_test'])

    def test_undefined_draws_are_counted_never_replaced(self):
        missing = dict(self.filled('2025-09-09'), marks={k: 'quote_absent' for k in ('short', 'primary', 'long', 'close')})
        rows = [self.filled(), missing]
        r = m.summarize(rows, self.c)
        self.assertEqual(r['by_group']['pooled']['fill_rate_headline'], 1)
        self.assertFalse(r['consider_later_strategy_test'])
        for b in r['bootstrap'].values():
            self.assertGreater(b['pooled']['primary_gross_bps']['undefined_draws'], 0)
            self.assertAlmostEqual(b['pooled']['primary_gross_bps']['lower'], 20)
        empty = m.summarize([dict(m.base_row('equity', 'GDO', DAY, '10:00:00', 'unfilled'), l='10.00', a='10.04', size=50)], self.c)
        self.assertEqual(empty['by_group']['pooled']['fill_rate_headline'], 0)
        for b in empty['bootstrap'].values():
            self.assertEqual(b['pooled']['primary_gross_bps']['undefined_draws'], self.c.report['bootstrap_draws'])


class InterlockTest(unittest.TestCase):
    def setUp(self):
        self.old = os.umask(0o077)
        self.addCleanup(os.umask, self.old)
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Path(self.tmp.name)
        self.c = fake_settings()
        r = m.json_bytes([dict(ticker='GDO', group='equity', cik=1, security_class='Common stock', rules='')])
        self.c = replace(self.c, sample=dict(self.c.sample, roster_before_draw_sha256=m.digest(r)))
        m.private_write(self.store / 'roster_before_draw.json', r)
        (self.store / 'evidence').mkdir(mode=0o700)
        check = m.digest(b'invented filing-list response')
        walk = self.keep(dict(completed=True, selected={'equity': ['GDO']}, visited=[
            dict(ticker='GDO', group='equity', cik=1, outcome='pass', forms=[], body_sha256=check)]))
        self.c = replace(self.c, sample=dict(self.c.sample, delisting_walk_sha256=walk))
        self.before = self.filing('0000000001-25-000001', '2025-09-07')
        self.after = self.filing('0000000001-25-000002', '2025-09-09')
        latest = self.keep(dict(cik='1', filings=dict(recent=dict(form=['N-CEN', 'N-CEN', '25'],
                      filingDate=['2025-09-07', '2025-09-09', '2025-09-10']))))
        self.i = dict(config_sha256=self.c.sha, fund_brackets=[dict(ticker='GDO', before=self.ref(self.before),
                      after=self.ref(self.after), filing_list=dict(sha256=walk, response_sha256=check, current_sha256=latest))],
            halt_days=[dict(session=DAY, coverage='unavailable', intervals=[])])
        self.replace_inputs()

    def keep(self, obj):
        raw = m.json_bytes(obj)
        tag = m.digest(raw)
        m.private_write(self.store / 'evidence' / tag, raw)
        return tag

    def ref(self, record):
        return dict(accession=record['accession'], sha256=self.keep(record))

    def filing(self, accession, filed):
        return dict(accession=accession, filed=filed, form='N-CEN', cik=1,
                    source_url='https://www.sec.gov/Archives/edgar/data/1/invented', source_sha256=m.digest(b'invented raw filing'),
                    listings=[dict(TICKER_SYMBOL='GDO', EXCHANGE='XNYS', DESCRIPTION='Common stock', SECURITY_CLASS_TITLE='Common stock')])

    def replace_inputs(self):
        path = self.store / 'inputs.json'
        path.unlink(missing_ok=True)
        m.private_write(path, m.json_bytes(self.i))

    def test_proof_requires_both_filings_and_the_frozen_walk(self):
        info, identities, _, _, _ = m.inputs(self.c, self.store)
        self.assertEqual(info['bracket_proved_fund_days'], 1)
        self.assertTrue(identities['GDO', DAY])
        entry = self.i['fund_brackets'][0]
        original = dict(entry)
        entry['before'] = self.ref(dict(self.before, source_url='https://www.sec.gov/files/company_tickers_exchange.json'))
        self.replace_inputs()
        with self.assertRaisesRegex(m.Stop, 'identity_filing_record'):
            m.inputs(self.c, self.store)
        entry.update(original)
        entry['filing_list'] = dict(original['filing_list'], response_sha256=m.digest(b'wrong submission receipt'))
        self.replace_inputs()
        with self.assertRaisesRegex(m.Stop, 'identity_filing_list'):
            m.inputs(self.c, self.store)
        badlist = self.keep(dict(cik='1', filings=dict(recent=dict(form=['N-CEN', '25-NSE', 'N-CEN'],
                      filingDate=['2025-09-07', DAY, '2025-09-09']))))
        entry['filing_list'] = dict(original['filing_list'], current_sha256=badlist)
        self.replace_inputs()
        with self.assertRaisesRegex(m.Stop, 'filing_list_delisting_form'):
            m.inputs(self.c, self.store)
        entry.update(original)
        entry['after'] = self.ref(dict(self.after, listings=[dict(self.after['listings'][0], DESCRIPTION='Preferred stock')]))
        self.replace_inputs()
        with self.assertRaisesRegex(m.Stop, 'identity_amendment_exclusions'):
            m.inputs(self.c, self.store)
        excluded = replace(self.c, excluded_tickers=frozenset({'GDO'}))
        entry['filing_list'] = {k: v for k, v in original['filing_list'].items() if k != 'current_sha256'}
        self.replace_inputs()
        self.assertFalse(m.inputs(excluded, self.store)[1]['GDO', DAY])
        self.i['fund_brackets'].clear()
        self.replace_inputs()
        with self.assertRaisesRegex(m.Stop, 'identity_missing_fund'):
            m.inputs(excluded, self.store)

    def test_guard_requires_exact_ledger_go_and_hashes(self):
        with self.assertRaises(FileNotFoundError):
            m.go_context(self.c, self.store)
        ledger = self.store / 'invented_ledger.md'
        ledger.write_text('| 223 | date | plan | trial | Signed; Approved for one M121 historical pull: `M121_GO=test_approval` |\n')
        info, *_ = m.inputs(self.c, self.store)
        go = dict(**info, authorization_id='test_approval', ledger_sha256=m.digest(ledger.read_bytes()))
        m.private_write(self.store / 'GO.json', m.json_bytes(go))
        with patch.object(m, 'LEDGER', ledger):
            self.assertEqual(m.go_context(self.c, self.store)[0], 'test_approval')
            self.i['fund_brackets'][0]['after'] = self.ref(dict(self.after, filed='2025-09-10'))
            self.replace_inputs()
            with self.assertRaisesRegex(m.Stop, 'go_hash_mismatch'):
                m.go_context(self.c, self.store)
            ledger.write_text('| 223 | date | plan | trial | No go; `M121_GO=test_approval` |\n')
            (self.store / 'GO.json').unlink()
            go['ledger_sha256'] = m.digest(ledger.read_bytes())
            m.private_write(self.store / 'GO.json', m.json_bytes(go))
            with self.assertRaisesRegex(m.Stop, 'go_ledger_not_authorized'):
                m.go_context(self.c, self.store)

    def test_cli_preflight_is_local_and_missing_go_creates_no_lock(self):
        out, err = io.StringIO(), io.StringIO()
        with (patch.object(m, 'STORE', self.store), patch.object(m, 'settings', return_value=self.c),
              patch.object(m, 'limit_process'), patch.object(m, 'live_transport', side_effect=AssertionError),
              redirect_stdout(out), redirect_stderr(err)):
            self.assertEqual(m.main(['--validate-inputs']), 0)
            receipt = json.loads(out.getvalue())
            self.assertEqual((receipt['bracket_proved_fund_days'], receipt['price_requests']), (1, 0))
            # Exercise the go guard directly rather than invoke historical mode.
            with self.assertRaises(FileNotFoundError):
                m.go_context(self.c, self.store)
        self.assertFalse((self.store / 'RUN.lock').exists())

    def test_execution_keeps_no_raw_and_one_lock_even_on_failure(self):
        info, verified, coverage, halts, _ = m.inputs(self.c, self.store)
        ctx = 'invented', info, verified, coverage, halts
        def stop(*_):
            raise m.Stop('synthetic_cap')
        with self.assertRaisesRegex(m.Stop, 'synthetic_cap'):
            m.execution(self.c, self.store, ctx, stop)
        self.assertFalse((self.store / '.building').exists())
        self.assertFalse((self.store / 'completed').exists())
        outcome = json.loads((self.store / 'RUN.lock').read_bytes())['stop']
        self.assertEqual((outcome['code'], outcome['attempted_requests']), ('synthetic_cap', 1))
        self.assertTrue((self.store / 'RUN.lock').is_file())
        with self.assertRaises(FileExistsError):
            m.execution(self.c, self.store, ctx, self.fail)

    def test_invented_paged_success_writes_only_reduced_outputs(self):
        info, verified, coverage, halts, _ = m.inputs(self.c, self.store)
        c = replace(self.c, sample=dict(self.c.sample, selected_in_hash_order={'equity': ['GDO', 'FICT']}),
                    limits=dict(self.c.limits, planned_fund_days=2, planned_order_slots=2), excluded_tickers=frozenset({'FICT'}))
        verified['FICT', DAY] = False
        quote_fields = dict(bp=10, ap=10.08, bs=1, bx='N', ax='N', z='A', c=['R'])
        quote_fields['as'] = 1
        def q(clock):
            return dict(quote_fields, t=DAY + 'T' + clock + '-04:00')
        responses = iter([
            ('quotes', None, 'invented-next', [q('09:59:59.999999999')]),
            ('quotes', 'invented-next', None, [q('10:01:01.999999999'), q('10:05:01.999999999'),
                                              q('10:15:01.999999999'), q('15:59:58.999999999')]),
            ('trades', None, None, [dict(t=DAY + 'T10:00:02-04:00', i=7, p=9.99, s=50, z='A', x='N', c=[' ', 'I'])]),
        ])
        def fabricated_get(url, args, decoded, wire):
            endpoint, cursor, nex, records = next(responses)
            self.assertTrue(url.endswith('/GDO/' + endpoint))
            self.assertEqual((args.get('page_token'), args['asof'], args['feed']), (cursor, DAY, 'sip'))
            raw = m.json_bytes({endpoint: records, 'symbol': 'GDO', 'next_page_token': nex})
            self.assertLessEqual(len(raw), min(decoded, wire))
            return raw, len(raw)
        m.execution(c, self.store, ('invented', info, verified, coverage, halts), fabricated_get)
        self.assertEqual(list(responses), [])
        done = self.store / 'completed'
        self.assertEqual(set(p.name for p in done.iterdir()), {'orders.jsonl', 'summary.json', 'receipt.json'})
        row = json.loads((done / 'orders.jsonl').read_bytes())
        self.assertEqual(row['state'], 'filled')
        self.assertTrue(all(isinstance(mark, list) for mark in row['marks'].values()))
        receipt = json.loads((done / 'receipt.json').read_bytes())
        self.assertEqual(receipt['attempted_requests'], 3)
        self.assertEqual(receipt['order_rows_sha256'], m.digest((done / 'orders.jsonl').read_bytes()))
        equity = json.loads((done / 'summary.json').read_bytes())['by_group']['equity']
        self.assertEqual((equity['scheduled'], equity['known_slots'], equity['identity_excluded_fund_days'],
                          equity['identity_excluded_slots']), (1, 1, 1, 1))


def full_shape_receipt():
    """Run the real execution/report path with no socket, credential or real store use."""
    c = m.settings()
    m.limit_process(c)
    t0 = time.monotonic()
    fake_ids = {(s, d): s not in c.excluded_tickers for _, s, d in c.schedule()}
    halt = {(s, d): [] for _, s, d in c.schedule()}
    n = len(c.order['placement_times'])

    def stamp(ns):
        base = datetime.fromtimestamp(ns // SECOND, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
        return f'{base}.{ns % SECOND:09d}Z'

    def fabricated_get(url, args, decoded, wire):
        symbol, endpoint = url.rsplit('/', 2)[-2:]
        date = args['asof']
        assert fake_ids[symbol, date]
        opened, _, close, slots = c.clocks(date)
        offset = sum((symbol + date).encode()) % 29
        quotes, prints = [], []

        def make_quote(ns, cents):
            return dict(t=stamp(ns), bp=cents / 100, ap=(cents + 4) / 100,
                        bs=1, bx='N', ax='N', z='A', c=['R'], **{'as': 1})

        for j, slot in enumerate(slots):
            cents = 1000 + offset + j
            hit = slot + (c.order['entry_delay_seconds'] + 1) * SECOND
            quotes.append(make_quote(slot - 1, cents))
            prints.append(dict(t=stamp(hit), i=j, p=(cents - 1) / 100, s=50, z='A', x='N', c=[' ']))
            quotes.extend(make_quote(hit + h * SECOND - 1, cents + 1) for h in c.order['mark_seconds_after_fill'].values())
        quotes.append(make_quote(close - 1, 1050))
        if symbol == c.sample['selected_in_hash_order'][c.sample['walk_type_order'][0]][0] and date == c.sample['sessions'][0]:
            quotes = [make_quote(opened + j, 1000) for j in range(c.limits['request_page_rows'] - len(quotes))] + quotes
        raw = m.json_bytes({endpoint: quotes if endpoint == 'quotes' else prints, 'symbol': symbol, 'next_page_token': None})
        assert len(raw) <= min(decoded, wire)
        return raw, len(raw)

    old = os.umask(0o077)
    try:
        with TemporaryDirectory() as path, patch('socket.socket', side_effect=AssertionError('no network in fixture')):
            tmp = Path(path)
            m.execution(c, tmp, ('invented_resource_test', {}, fake_ids, dict.fromkeys(c.sample['sessions'], 'unavailable'), halt), fabricated_get)
            report = json.loads((tmp / 'completed' / 'summary.json').read_bytes())
            receipt = json.loads((tmp / 'completed' / 'receipt.json').read_bytes())
            assert report['consider_later_strategy_test']
            assert report['by_group']['pooled']['scheduled'] == sum(fake_ids.values()) * n
            assert receipt['attempted_requests'] == 2 * sum(fake_ids.values())
    finally:
        os.umask(old)
    peaks = {k[:-1]: int(v) for s in Path('/proc/self/status').read_text().splitlines()
             if (k := s.split()[0]) in ('VmPeak:', 'VmHWM:') and (v := s.split()[1])}
    print(m.json_bytes(dict(invented=True, historical_requests=0, fund_days=sum(fake_ids.values()), slots=sum(fake_ids.values()) * n,
                            bootstrap_draws_per_method=c.report['bootstrap_draws'], nice=os.nice(0),
                            child_rlimit_as_bytes=resource.getrlimit(resource.RLIMIT_AS), child_peak_kib=peaks,
                            elapsed_seconds=round(time.monotonic() - t0, 2))).decode(), end='')


def run():
    for key in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
        os.environ[key] = '1'
    if os.environ.get('M121_FULL_INVENTED_FIXTURE') == '1':
        full_shape_receipt()
        return 0
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
