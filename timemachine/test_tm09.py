"""Made-up minutes, calendars, headlines, and returns only."""
from copy import deepcopy
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from io import BytesIO, StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from timemachine.score_tm09 import DEPS, run_approved, score
from timemachine import tm09_blind
from timemachine.tm09_desk import Desk, PUBLIC_SID, initialize, seal, slot, store_new
from timemachine.tm09_feed import copied_run, extract_figures
from timemachine.tm09_fixture import FILES, compile_export, compile_weeks, encode, mondays, read_private, settings, stage1_weeks, week_pairs
from timemachine.tm09_operator import benchmark_outcome, launch, review, stage1_contrasts, worker_handler
from timemachine.tm09_orders import Minutes, benchmark, fill, terminal, weights

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'config/thresholds.yaml'
KEY = 'made-up unittest-only signing material'
HEADLINE = 'SYN opens moonlit widget factory for $2 million'
NOTE = 'SYN started a facility for making widgets.'


def scout_note(source):
    return dict(symbol='SYN', source_time=source, repeat=False, paraphrase=NOTE)


def at(day, time):
    return int(datetime.fromisoformat(day + 'T' + time).replace(tzinfo=ZoneInfo('America/New_York')).timestamp())


def inputs():
    options = settings(read_private(CONFIG))
    options.update(symbols=['SYN'], notes=2, note_chars=280, looks=50, look_rows=120,
                   headline_rows=20, headline_chars=500)
    options['study']['window'].update(first_monday='2026-09-07', last_monday='2026-09-07', weeks=1)
    sessions, bars = [], []
    for day, close in [('2026-09-08', '16:00'), ('2026-09-09', '12:30')]:
        sessions.append(dict(date=day, open_utc=at(day, '09:30'), close_utc=at(day, close)))
        for hm, p in [('09:59', 10), ('10:00', 79), ('10:01', 11), ('10:02', 900),
                      ('12:29', 12), ('12:31', 17), ('15:31', 18), ('15:59', 19)]:
            if at(day, hm) < at(day, close):
                bars.append(dict(symbol='SYN', tf='1Min', t=at(day, hm), o=p, h=p, l=p, c=p, v=53))
    source = at('2026-09-08', '09:00')
    news = [dict(id='one', source='sec_edgar', stated_time=source, updated_time=source,
                 edited_later=False, headline=HEADLINE, symbols=['SYN', 'OFF'])]
    return options, sessions, bars, news


class DeskTest(unittest.TestCase):
    def setUp(self):
        holder = TemporaryDirectory()
        self.addCleanup(holder.cleanup)
        self.path = Path(holder.name)
        self.opts, self.sessions, self.bars, self.news = inputs()
        self.f = compile_weeks(self.opts, self.sessions, self.bars, self.news)['2026-09-07']
        self.boss = self.opts['study']['boss_models'][0]

    def init(self, role, **kw):
        return initialize(self.path, self.f, self.opts, role, KEY, **kw)

    def scouts(self):
        p, tp = self.init('price_scout')
        n, tn = self.init('news_scout', news_reader=lambda: encode(self.news[0]).encode())
        for i, (wake, _) in enumerate(self.f['wakes']):
            price = p.handle(tp, 'next')
            news = n.handle(tn, 'next')
            self.assertEqual(news['wake'], wake)
            if i == 1:
                self.assertEqual(news['items'], [{'headline': HEADLINE, 'source_time': self.news[0]['stated_time'], 'symbol': 'SYN', 'repeat': False}])
                with self.assertRaises(ValueError):
                    note = scout_note(self.news[0]['stated_time']); note['paraphrase'] = HEADLINE.upper() + '!'
                    n.handle(tn, 'notes', {'wake_key': news['wake_key'], 'notes': [note]})
            else:
                self.assertEqual(news['items'], [])
            p.handle(tp, 'notes', {'wake_key': price['wake_key'], 'notes': [f'SYN price observation {i}']})
            n.handle(tn, 'notes', {'wake_key': news['wake_key'], 'notes': [scout_note(self.news[0]['stated_time'])] if i == 1 else []})
        return p.export_notes(), n.export_notes()

    def test_holiday_short_session_and_strict_news(self):
        self.assertEqual([x[0] for x in self.f['wakes']], [at('2026-09-08', t) for t in ('10:00','12:30','15:30')]
                         + [at('2026-09-09', '10:00')])
        self.assertEqual([bool(v) for v in self.f['news_index'].values()], [False, True, False, False])
        self.assertNotIn(HEADLINE, encode(self.f))

    def test_first_wake_after_holiday_and_clock_filter(self):
        early = deepcopy(self.news[0]); early.update(id='holiday', stated_time=at('2026-09-07', '15:00'))
        early['updated_time'] = early['stated_time']
        late = deepcopy(early); late.update(id='edited', updated_time=early['stated_time'] + 60, edited_later=True)
        f = compile_weeks(self.opts, self.sessions, self.bars, [early, late])['2026-09-07']
        self.assertEqual([len(v) for v in f['news_index'].values()], [1, 0, 0, 0])

    def test_visibility_sealed_arms_and_rehearsal(self):
        p, n = self.scouts()
        desks = [self.init('boss', boss=self.boss, arm=arm, price=p, news=n if arm == 'N' else None)
                 for arm in ('P1','P2','N')]
        for i, (wake, _) in enumerate(self.f['wakes']):
            packets = [d.handle(t, 'next') for d, t in desks]
            self.assertTrue(all(x['price_notes'] == packets[0]['price_notes'] for x in packets))
            self.assertNotIn('news_notes', packets[0]); self.assertNotIn('news_notes', packets[1])
            self.assertEqual(packets[2].get('news_notes'), [dict(scout_note(self.news[0]['stated_time']),
                                                                figures=['$2 million'], has_number=True)] if i == 1 else None)
            for (d, t), packet in zip(desks, packets):
                row = d.handle(t, 'look', {'wake_key': packet['wake_key'], 'symbol': 'SYN', 'rows': 20})
                self.assertTrue(all(b[0] + 60 <= wake for b in row['bars']))
                self.assertNotIn(HEADLINE, encode(packet))
                if packet.get('news_notes'):
                    self.assertEqual(d.delivery_wakes(), set())
                    d.confirm_delivery(wake)
                    d.confirm_delivery(wake)
                    self.assertEqual(d.delivery_wakes(), {wake})
                request = {'wake_key': packet['wake_key'], 'weights': {'SYN': 1} if i == 0 else None}
                ack = d.handle(t, 'pick', request)
                self.assertEqual(ack, {'accepted': True, 'done': i == len(self.f['wakes']) - 1})
                self.assertEqual(d.handle(t, 'pick', request), ack)
            if i == 1:
                self.assertEqual(packets[2]['fills'][0]['filled'], 5)
                self.assertEqual(packets[2]['book']['shares'], {'SYN': 5})
        for d, _ in desks:
            self.assertNotIn(HEADLINE.encode(), (d.path / 'desk.sqlite').read_bytes())
            self.assertTrue(d.complete())
        self.assertTrue(all(HEADLINE.encode() not in p.read_bytes() for p in self.path.rglob('*') if p.is_file()))

    def test_stage1_wont_open_news_and_preserves_shared_prices(self):
        config = settings(read_private(CONFIG))
        config['symbols'] = ['SYN']
        days = [day + timedelta(days=1) for day in stage1_weeks(config['study'])]
        sessions = [dict(date=d.isoformat(), open_utc=at(d.isoformat(), '09:30'), close_utc=at(d.isoformat(), '16:00')) for d in days]
        bars = [dict(symbol='SYN', tf='1Min', t=at(d.isoformat(), '09:59'), o=10, h=10, l=10, c=10, v=53) for d in days]
        pins = {}
        for name, records in zip(FILES[:2], (sessions, bars)):
            raw = '\n'.join(map(encode, records)).encode()
            (self.path / name).write_bytes(raw)
            pins[name] = sha256(raw).hexdigest()
        f = compile_export(config, self.path, pins, stage1=True)
        self.assertEqual(len(f), 5)
        self.assertTrue(all(not items for week in f.values() for items in week['news_index'].values()))
        stage = {**self.opts, 'mode': 'stage1'}
        stage_fixture = deepcopy(self.f)
        stage_fixture['news_index'] = {wake: [] for wake in self.f['news_index']}
        s, t = initialize(self.path, stage_fixture, stage, 'price_scout', KEY)
        for i, _ in enumerate(self.f['wakes']):
            s.handle(t, 'notes', {'wake_key': s.handle(t, 'next')['wake_key'], 'notes': [str(i)]})
        with self.assertRaises(ValueError):
            initialize(self.path, self.f, stage, 'news_scout', KEY)
        with self.assertRaises(ValueError):
            initialize(self.path, self.f, stage, 'boss', KEY, boss=self.boss, arm='N', price=s.export_notes())
        self.assertEqual(s.export_notes(), Desk(s.path, self.f, KEY, approved_options={**stage, 'mode':'B'}).export_notes())
        self.assertEqual(stage1_contrasts(list(f), config, lambda w, b, a: '.0002' if a == 'P1' else '0'), ['2'] * 5)

    def test_unfinished_news_scout_does_not_deliver(self):
        desk, token = self.init('news_scout', news_reader=lambda: encode(self.news[0]).encode())
        first = desk.handle(token, 'next')
        desk.handle(token, 'notes', {'wake_key': first['wake_key'], 'notes': []})
        second = desk.handle(token, 'next')
        desk.handle(token, 'notes', {'wake_key': second['wake_key'], 'notes': [scout_note(self.news[0]['stated_time'])]})
        with self.assertRaises(ValueError):
            desk.export_notes()
        with self.assertRaises(ValueError):
            desk.delivery_wakes()

    def test_figures_and_repeat_witness(self):
        source = self.news[0]['stated_time']
        other = [{**self.news[0], 'id': 'x0', 'headline': 'SYN opens a moonlit widget factory for $2 million'},
                 {**self.news[0], 'id': 'x1', 'headline': 'SYN opens moonlit widget factory for $3 million'}]
        fixture = compile_weeks(self.opts, self.sessions, self.bars, [*other, *self.news])['2026-09-07']
        raw = '\n'.join(map(encode, [*other, *self.news])).encode()
        feed = self.opts['study']['amendment_1']['feed']
        when = self.f['wakes'][1][0]
        items = week_pairs(fixture, feed, raw=raw)[when]
        self.assertEqual([i['repeat'] for i in items], [False, True, False])
        title = 'SYN issues −$4–6 million forecast on November 5, 2026, with a gain of 2%'
        self.assertEqual(extract_figures(title, feed), (['−$4–6 million', 'November 5, 2026', '2%'], False))
        self.assertEqual(extract_figures('SYN hires eighty people', feed), ([], True))
        self.assertEqual(extract_figures('SYN closes a quarter with new factory', feed), ([], True))
        self.assertEqual(extract_figures('SYN gives a general update', feed), ([], False))
        self.assertEqual(extract_figures('SYN rises 25zorp', feed), ([], True))
        self.assertEqual(extract_figures('SYN reports ' + '9' * 65 + ' million', feed), ([], True))

    def test_paraphrase_run_and_short_title_heuristic(self):
        feed = self.opts['study']['amendment_1']['feed']
        words = 'alpha beta gamma delta epsilon zeta eta theta'.split()
        for n in range(1, len(words) + 1):
            title = ' '.join(words[:n])
            self.assertEqual(copied_run(f'reported {title} yesterday', [title], feed), n >= 3)
            width = min(6, n) - 1
            self.assertFalse(copied_run(' '.join(words[:width]), [title], feed))
        self.assertTrue(copied_run('BETA, gamma DELTA epsilon ZETA eta', [' '.join(words)], feed))
        self.assertFalse(copied_run('alpha beta gamma delta then epsilon zeta eta theta', [' '.join(words)], feed))

    def test_news_refuses_prose_in_figures_and_consecutive_copies(self):
        title = 'SYN confirms private widget supplier as revenue rises to $20 million after review'
        raw = encode({**self.news[0], 'headline': title}).encode()
        desk, token = self.init('news_scout', news_reader=lambda: raw)
        packet = desk.handle(token, 'next')
        desk.handle(token, 'notes', {'wake_key': packet['wake_key'], 'notes': []})
        packet = desk.handle(token, 'next')
        note = scout_note(self.news[0]['stated_time'])
        for changes in ({'figures': ['private widget supplier as revenue rises to $20 million']},
                        {'has_number': False},
                        {'paraphrase': 'SYN update: private widget supplier as revenue rises this week.'}):
            with self.assertRaises(ValueError) as refused:
                desk.handle(token, 'notes', {'wake_key': packet['wake_key'], 'notes': [{**note, **changes}]})
            self.assertNotIn('private widget supplier', str(refused.exception))
        note.update(paraphrase='The company confirmed a supplier and reported higher sales.')
        self.assertTrue(desk.handle(token, 'notes', {'wake_key': packet['wake_key'], 'notes': [note]})['accepted'])
        self.assertNotIn(b'private widget supplier', (desk.path / 'desk.sqlite').read_bytes())

    def test_possible_miss_does_not_block_note(self):
        raw = encode({**self.news[0], 'headline': 'SYN ships eighty fictional widgets'}).encode()
        desk, token = self.init('news_scout', news_reader=lambda: raw)
        for i, _ in enumerate(self.f['wakes']):
            packet = desk.handle(token, 'next')
            if i == 1:
                wake = packet['wake']
            notes = [scout_note(self.news[0]['stated_time'])] if i == 1 else []
            desk.handle(token, 'notes', {'wake_key': packet['wake_key'], 'notes': notes})
        note, = desk.export_notes()['body']['wakes'][str(wake)]
        self.assertEqual((note['figures'], note['has_number']), ([], False))

    def test_attached_figures_are_literal_bytes_only_and_wrong_scales_cannot_be_submitted(self):
        forms = ('$20M', '.5%', 'USD 20 million', 'minus 2%', '10bps')
        headline = 'SYN reports ' + '; '.join(forms) + ' for its fictional program'
        feed = self.opts['study']['amendment_1']['feed']
        raw = encode({**self.news[0], 'headline': headline}).encode()
        desk, token = self.init('news_scout', news_reader=lambda: raw)
        packet = desk.handle(token, 'next')
        desk.handle(token, 'notes', {'wake_key': packet['wake_key'], 'notes': []})
        packet = desk.handle(token, 'next')
        note = scout_note(self.news[0]['stated_time'])
        with self.assertRaises(ValueError):
            desk.handle(token, 'notes', {'wake_key': packet['wake_key'], 'notes': [
                {**note, 'has_number': True, 'figures': ['$20', '5%', '20 million', '2%', '10']}]})
        desk.handle(token, 'notes', {'wake_key': packet['wake_key'], 'notes': [note]})
        for _ in self.f['wakes'][2:]:
            desk.handle(token, 'notes', {'wake_key': desk.handle(token, 'next')['wake_key'], 'notes': []})
        sealed, = desk.export_notes()['body']['wakes'][str(packet['wake'])]
        self.assertTrue(sealed['has_number'])
        self.assertEqual(sealed['figures'], list(forms))
        self.assertEqual(extract_figures(headline, feed), (list(forms), False))
        for figure in sealed['figures']:
            offset = raw.index(figure.encode())
            self.assertEqual(raw[offset:offset + len(figure.encode())], figure.encode())
        self.assertFalse(copied_run('SYN update announces a new facility today', ['SYN update'], feed))
        self.assertTrue(copied_run('SYN update today appears in the bulletin', ['SYN update today'], feed))

    def test_reject_wrong_and_tampered_stream_or_token(self):
        p, n = self.scouts()
        with self.assertRaises(ValueError):
            self.init('boss', boss=self.boss, arm='P1', price=p, news=n)
        bad = deepcopy(n); bad['body']['wakes'][str(self.f['wakes'][0][0])] = [NOTE]
        with self.assertRaises(ValueError):
            self.init('boss', boss=self.boss, arm='N', price=p, news=bad)
        p1, t1 = self.init('boss', boss=self.boss, arm='P1', price=p)
        p2, t2 = self.init('boss', boss=self.boss, arm='P2', price=p)
        with self.assertRaises(PermissionError):
            p1.handle(t2, 'next')
        with self.assertRaises(PermissionError):
            p2.handle(t2, 'pick', {'wake_key': p1.handle(t1, 'next')['wake_key'], 'weights': None})

    def test_news_scout_cannot_look_and_successor_only_once(self):
        d, t = self.init('news_scout')
        pkt = d.handle(t, 'next')
        with self.assertRaises(PermissionError):
            d.handle(t, 'look', {'wake_key': pkt['wake_key'], 'symbol': 'SYN', 'rows': 1})
        d.handle(t, 'notes', {'wake_key': pkt['wake_key'], 'notes': []})
        new, handoff = d.successor()
        self.assertEqual(handoff['body']['step'], 1)
        with self.assertRaises(PermissionError):
            d.handle(t, 'status')
        self.assertEqual(d.handle(new, 'status')['step'], 1)
        with self.assertRaises(ValueError):
            d.successor()

    def test_no_rerun_finished_slot(self):
        self.scouts()
        with self.assertRaises(FileExistsError):
            self.init('price_scout')
        d = Desk(self.path / slot(self.f['week'], 'price_scout'), self.f, KEY)
        with self.assertRaises(ValueError):
            d.successor()

    def test_volume_cancel_and_terminal(self):
        m = Minutes(self.f['bars']); wake, close = self.f['wakes'][0]
        book = {'cash':'1000', 'shares':{}}
        report, = fill(book, weights({'SYN': 1}, ['SYN']), m, wake, close, Decimal('.0005'), Decimal('.1'))
        self.assertEqual((report['requested'], report['filled'], report['canceled']), (100, 5, 95))
        self.assertEqual(report['minute'], wake + 60)
        self.assertEqual(book, {'cash':'944.9725', 'shares':{'SYN':5}})
        self.assertEqual(terminal(book, m, self.f['closes'][-1], Decimal('.0005')), Decimal('1004.9425'))
        self.assertEqual(benchmark(['SYN'], m, wake, close, self.f['closes'][-1], Decimal(0)), Decimal(12) / 11 - 1)

    def test_minute_at_cutoff_is_canceled_unfilled(self):
        m = Minutes(self.f['bars']); wake, _ = self.f['wakes'][0]
        book = {'cash':'1000', 'shares':{}}
        report, = fill(book, weights({'SYN': 1}, ['SYN']), m, wake, wake + 60, Decimal('.0005'), Decimal('.1'))
        self.assertEqual(report, {'symbol': 'SYN', 'requested': 100, 'filled': 0,
                                  'canceled': 100, 'reason': 'no eligible minute'})
        self.assertEqual(book, {'cash':'1000', 'shares':{}})

    def test_sparse_orders_counted_once_without_later_or_overnight_fill(self):
        first, second, third, fourth = (w for w, _ in self.f['wakes'])
        first_close = self.f['closes'][0]
        self.f['bars']['SYN'] = [row for row in self.f['bars']['SYN']
                                 if not (first < row[0] < second or third < row[0] < first_close)]
        price, _ = self.scouts()
        boss, token = self.init('boss', boss=self.boss, arm='P1', price=price)
        for wake in (first, second, third, fourth):
            packet = boss.handle(token, 'next')
            self.assertEqual(packet['wake'], wake)
            self.assertEqual(packet['book']['shares'], {})
            self.assertEqual(Decimal(packet['book']['cash']), Decimal(1000))
            self.assertEqual([r['reason'] for r in packet['fills']],
                             ['no eligible minute'] if wake in (second, fourth) else [])
            req = {'wake_key': packet['wake_key'], 'weights': {'SYN': 1} if wake in (first, third) else None}
            ack = boss.handle(token, 'pick', req)
            self.assertEqual(ack, {'accepted': True, 'done': wake == fourth})
            self.assertEqual(boss.handle(token, 'pick', req), ack)
        self.assertEqual(boss.sparse_counts(), {'session': boss.public_id, 'by_symbol': {'SYN': 2},
                                               'by_market_session': {'2026-09-08': {'SYN': 2}}})

    def test_export_compiler_uses_pins_and_excludes_raw_headlines(self):
        counts = {'skipped_edited_or_changed_clock': 0}
        changed = {**self.news[0], 'id': 'changed', 'updated_time': self.news[0]['updated_time'] + 1, 'edited_later': True}
        pins = {}
        for name, records in zip(FILES, (self.sessions, self.bars, [*self.news, changed])):
            blob = '\n'.join(map(encode, records)).encode()
            (self.path / name).write_bytes(blob)
            pins[name] = sha256(blob).hexdigest()
        self.assertEqual(compile_export(self.opts, self.path, pins, counts)[self.f['week']], self.f)
        self.assertEqual(counts, {'skipped_edited_or_changed_clock': 1,
                                  'by_week': {self.f['week']: {'admitted_pairs': 1, 'repeat_pairs': 0,
                                                              'items_with_extracted_figure': 1,
                                                              'items_without_extracted_figure': 0,
                                                              'possible_figure_missed': 0}}})
        pins[FILES[2]] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            compile_export(self.opts, self.path, pins)

    def test_figure_counts_per_item_not_per_symbol(self):
        self.opts['symbols'].append('XYZ')
        base = self.news[0]
        news = [{**base, 'symbols': ['SYN', 'XYZ'], 'headline': 'Fictional firm reports $20M and two deals'},
                {**base, 'id': 'two', 'headline': 'Fictional firm reports 25zorp'},
                {**base, 'id': 'three', 'headline': 'Fictional firm announces deal'}]
        counts, pins = {'skipped_edited_or_changed_clock': 0}, {}
        bars = self.bars + [dict(bar, symbol='XYZ') for bar in self.bars]
        for name, records in zip(FILES, (self.sessions, bars, news)):
            blob = '\n'.join(map(encode, records)).encode()
            (self.path / name).write_bytes(blob)
            pins[name] = sha256(blob).hexdigest()
        fixture = compile_export(self.opts, self.path, pins, counts)
        self.assertEqual(counts['by_week'][self.f['week']], {
            'admitted_pairs': 4, 'repeat_pairs': 0, 'items_with_extracted_figure': 1,
            'items_without_extracted_figure': 2, 'possible_figure_missed': 2,
        })
        self.assertNotIn('$20M', encode(fixture))
        self.assertNotIn('$20M', encode(counts))

    def test_missing_sizing_print_is_countable_cancel(self):
        wake = self.f['wakes'][0][0]
        m = Minutes({'SYN': [b for b in self.f['bars']['SYN'] if b[0] >= wake]})
        book = {'cash': '1000', 'shares': {}}
        report, = fill(book, weights({'SYN': 1}, ['SYN']), m, wake, wake + 120, Decimal(0), Decimal(1))
        self.assertEqual((report['reason'], report['filled'], report['requested']), ('no completed sizing print', 0, None))
        self.assertEqual(book, {'cash': '1000', 'shares': {}})

    def test_same_minute_buys_are_pro_rata_and_commission_applies(self):
        wake = self.f['wakes'][0][0]
        m = Minutes({s: [[wake-60, '10', '10', '10', '10', '1000'], [wake+60, '20', '20', '20', '20', '1000']]
                     for s in ('SYN', 'XYZ')})
        book = {'cash': '1000', 'shares': {}}
        report = fill(book, weights({'XYZ': '.5', 'SYN': '.5'}, ['SYN', 'XYZ']), m, wake, wake+120,
                      Decimal(0), Decimal(1), Decimal('.01'))
        self.assertEqual({r['symbol']: r['filled'] for r in report}, {'SYN': 24, 'XYZ': 24})
        self.assertEqual(Decimal(book['cash']), Decimal('30.40'))

    def test_terminal_availability_does_not_change_worker_ack(self):
        for surviving in (True, False):
            with self.subTest(surviving=surviving), TemporaryDirectory() as private:
                fixture = deepcopy(self.f)
                if not surviving:
                    fixture['bars']['SYN'] = [row for row in fixture['bars']['SYN'] if row[0] != fixture['closes'][-1] - 60]
                p, pt = initialize(Path(private), fixture, self.opts, 'price_scout', KEY)
                for _ in fixture['wakes']:
                    p.handle(pt, 'notes', {'wake_key': p.handle(pt, 'next')['wake_key'], 'notes': []})
                b, bt = initialize(Path(private), fixture, self.opts, 'boss', KEY, boss=self.boss, arm='P1', price=p.export_notes())
                for i, _ in enumerate(fixture['wakes']):
                    pkt = b.handle(bt, 'next')
                    ack = b.handle(bt, 'pick', {'wake_key': pkt['wake_key'], 'weights': {'SYN': 1} if i == 0 else None})
                    self.assertEqual(ack, {'accepted': True, 'done': i + 1 == len(fixture['wakes'])})
                self.assertEqual(b.handle(bt, 'next'), {'done': True})
                self.assertEqual(b.export_boss() is not None, surviving)
                self.assertEqual(b.access_records(0, b.access_checkpoint()), [])

    def test_worker_http_scope_and_no_store_without_binding_port(self):
        d, tok = self.init('price_scout')
        route = worker_handler(d)

        def send(path, token, method='GET'):
            wire = BytesIO()

            class Request:
                def settimeout(self, timeout):
                    pass

                def makefile(self, mode, *args):
                    message = f'{method} {path} HTTP/1.0\r\nAuthorization: Bearer {token}\r\n\r\n'
                    return BytesIO(message.encode())

                def sendall(self, blob):
                    wire.write(blob)

            route(Request(), ('127.0.0.1', 1), None)
            return wire.getvalue()

        self.assertRegex(d.public_id, PUBLIC_SID)
        self.assertNotIn(d.path.name, d.public_id)
        answer = send(f'/desk/next?session={d.public_id}', tok)
        self.assertIn(b' 200 ', answer)
        self.assertIn(b'Cache-Control: no-store', answer)
        self.assertNotIn(tok.encode(), answer)
        self.assertIn(b' 403 ', send('/desk/next?session=TM09-SIBLING', tok))
        self.assertIn(b' 403 ', send(f'/desk/export?session={d.public_id}', tok))
        self.assertIn(b' 403 ', send(f'/desk/next?session={d.public_id}', 'x' * 48))
        self.assertIn(b' 200 ', send(f'/desk/status?session={d.public_id}', tok))
        self.assertEqual(answer, send(f'/desk/next?session={d.public_id}', tok))
        refused = send(f'/desk/status?session={d.public_id}', tok, method='TRACE')
        self.assertIn(b' 501 ', refused)
        self.assertNotIn(b'Date:', refused)
        journal = d.access_records(0, d.access_checkpoint())
        self.assertEqual([x['status'] for x in journal], [200, 403, 403, 403, 200, 200, 501])
        with d.tx() as (con, _):
            self.assertEqual(con.execute("SELECT count(*) FROM journal WHERE kind='access_attempt'").fetchone()[0], 7)
        self.assertNotIn(tok, encode(journal))
        self.assertNotIn('export', encode(journal))

    def test_launch_control_and_review_use_only_signed_allowlisted_evidence(self):
        d, _ = self.init('price_scout')
        body = dict(session=d.public_id, nonce='a' * 32, port=8844, canary_observed=True,
                    sudo_size_before=1, sudo_size_after=2, sudo_checkpoint_sha256='b' * 64)
        denied, allowed, proof, receipt, canary = [self.path / item for item in ('denied', 'allowed', 'proof', 'receipt', 'canary')]
        store_new(denied, {'body': body, 'seal': seal(KEY, 'ledger-222-tm09-launch', body)})
        with patch('timemachine.tm09_operator.DeskHTTPServer') as server:
            with self.assertRaises(ValueError):
                launch(d, 8844, KEY, denied, canary)
            server.assert_not_called()
            body['port'] = 8801
            store_new(canary, dict(session=d.public_id, port=8801, nonce=body['nonce'], matched_canary=True,
                                   prefix_unchanged=True, size_before=1, size_after=2))
            body['sudo_checkpoint_sha256'] = sha256(read_private(canary)).hexdigest()
            store_new(allowed, {'body': body, 'seal': seal(KEY, 'ledger-222-tm09-launch', body)})
            listener = server.return_value.__enter__.return_value
            listener.serve_forever.side_effect = lambda: d.access('GET', '/desk/status', d.public_id, 200)
            with patch('builtins.print'):
                launch(d, 8801, KEY, allowed, canary)
            server.assert_called_once()
            self.assertEqual(server.call_args.args[0], ('127.0.0.1', 8801))
        from timemachine.tm09_fixture import fingerprint
        control = json.loads(read_private(d.path / (body['nonce'] + '-control.json')))
        store_new(proof, {'phase': 'stopped', 'session': d.public_id, 'port': 8801, 'denied_count': 4})
        end = dict(session=d.public_id, nonce=body['nonce'], port=8801, control_sha256=fingerprint(control),
                   sudo_allowlist_reviewed=True, raw_copies_denied=True, listener_stopped=True,
                   post_stop_probe_sha256=sha256(read_private(proof)).hexdigest(), sudo_review_sha256='c' * 64)
        store_new(receipt, {'body': end, 'seal': seal(KEY, 'ledger-222-tm09-review', end)})
        with patch('builtins.print'):
            review(d, KEY, receipt, proof)
        reviewed = json.loads(read_private(d.path / (body['nonce'] + '-review.json')))['body']
        self.assertEqual(reviewed['routes'], [{'method': 'GET', 'path': '/desk/status', 'session': d.public_id, 'status': 200}])


class ScoreTest(unittest.TestCase):
    def setUp(self):
        self.study = settings(read_private(CONFIG))['study']
        self.weeks = [w.isoformat() for w in mondays(self.study)]
        self.models = self.study['boss_models']
        self.data = {week: dict(eligible_wakes=4, note_wakes=2, benchmark='.001',
                                models={m: dict(P1='0', P2='0', N=str(Decimal(20+i)/10000)) for m in self.models})
                     for i, week in enumerate(self.weeks)}

    def test_pass_and_forward_tie(self):
        r = score(self.study, self.data)
        self.assertTrue(r['news_helps'] and r['worth_following_forward'])
        for w, row in self.data.items():
            row['benchmark'] = row['models'][self.models[0]]['N']
        self.assertFalse(score(self.study, self.data)['worth_following_forward'])

    def test_sparse_unused_roster_stock_disables_only_forward_label(self):
        options, sessions, bars, news = inputs()
        options['symbols'].append('GAP')
        for miss in ('entry', 'terminal'):
            with self.subTest(missing=miss):
                other = [{**bar, 'symbol': 'GAP'} for bar in bars
                         if not (miss == 'entry' and at('2026-09-08', '10:00') < bar['t'] < at('2026-09-08', '16:00'))
                         and not (miss == 'terminal' and bar['t'] == at('2026-09-09', '12:29'))]
                fixture = compile_weeks(options, sessions, [*bars, *other], news)['2026-09-07']
                row = self.data[self.weeks[0]]
                row.update(benchmark_outcome(fixture, options, row['models']))
                self.assertIsNone(row['benchmark'])
                self.assertIn(miss, row['benchmark_unavailable'])
                result = score(self.study, self.data)
                self.assertEqual(result['weeks_with_primary'], 20)
                self.assertTrue(result['news_helps'])
                self.assertFalse(result['worth_following_forward'])
                self.assertEqual(result['benchmark_unavailable'], {self.weeks[0]: row['benchmark_unavailable']})

    def test_missing_pairs_floor_and_model_lost_limit(self):
        for w in self.weeks[:3]:
            for m in self.models:
                self.data[w]['models'][m]['P2'] = None
        self.assertEqual(score(self.study, self.data)['weeks_with_primary'], 17)
        self.assertTrue(score(self.study, self.data)['news_helps'])
        self.data[self.weeks[3]]['models'][self.models[1]]['N'] = None
        r = score(self.study, self.data)
        self.assertEqual(r['weeks_with_primary'], 17)
        self.assertFalse(r['news_helps']); self.assertIn('inconclusive', r['labels'])
        self.assertEqual(r['weekly'][0]['models'], [self.models[0]])
        self.data[self.weeks[3]]['models'][self.models[0]]['N'] = None
        self.assertEqual(score(self.study, self.data)['weeks_with_primary'], 16)

    def test_zero_variance_control_exception_and_delivery(self):
        for row in self.data.values():
            for arms in row['models'].values():
                arms.update(P1='.001', N='.006')
        self.data[self.weeks[0]]['note_wakes'] = 0
        r = score(self.study, self.data)
        self.assertEqual(set(r['labels']), {'treatment not delivered', 'inconclusive', 'harness noise'})
        self.assertIsNone(r['primary_t']); self.assertIsNone(r['placebo_t'])

    def test_high_precision_constant_primary_is_inconclusive(self):
        for row in self.data.values():
            for arms in row['models'].values():
                arms['N'] = '0.002345678901234567890123456789'
        r = score(self.study, self.data)
        self.assertIsNone(r['primary_t'])
        self.assertEqual(r['labels'], ['inconclusive'])

    def test_sealed_tiny_net_from_one_share_is_accepted(self):
        m = Minutes({'SYN': [[0, '1', '1', '1', '1', '1000'], [120, '.9995', '1', '.9995', '1', '1000'],
                             [180, '1.0005000000000001', '1.0005000000000001', '1', '1.0005000000000001', '1000']]})
        book = {'cash':'1000', 'shares':{}}
        fill(book, {'SYN': Decimal('.001')}, m, 60, 240, Decimal('.0005'), Decimal('.1'))
        net = (terminal(book, m, 240, Decimal('.0005')) - 1000) / 1000
        self.assertEqual(net, Decimal('9.995E-20'))
        self.data[self.weeks[0]]['models'][self.models[0]]['N'] = str(net)
        self.assertEqual(score(self.study, self.data)['weeks_with_primary'], 20)

    def test_design_b_complete_six_and_placebo_uses_only_two(self):
        for row in self.data.values():
            for arms in row['models'].values():
                n = arms.pop('N')
                arms.update(P3='0', N1=n, N2=n, N3=n)
        self.assertTrue(score(self.study, self.data, 'B')['news_helps'])
        arms = self.data[self.weeks[0]]['models'][self.models[0]]
        arms['P3'] = None
        result = score(self.study, self.data, 'B')
        self.assertEqual(result['lost_weeks'][self.models[0]], [self.weeks[0]])
        self.assertTrue(result['placebo_all_exact_zero'])

    def test_exact_primary_and_placebo_boundaries(self):
        for i, row in enumerate(self.data.values()):
            for arms in row['models'].values():
                arms['N'] = '.00343' if i < 19 else '-.01657'
        r = score(self.study, self.data)
        self.assertEqual(r['primary_t'], Decimal('2.43'))
        self.assertTrue(r['marks']['primary_t'])
        for i, row in enumerate(self.data.values()):
            for arms in row['models'].values():
                arms['P1'] = '.003' if i < 19 else '-.017'
        r = score(self.study, self.data)
        self.assertEqual(r['placebo_t'], Decimal(2))
        self.assertFalse(r['marks']['placebo'])

    def test_approval_refuses_before_reading_result(self):
        with patch('timemachine.score_tm09.read_private', side_effect=FileNotFoundError) as read:
            with self.assertRaises(FileNotFoundError):
                run_approved(Path('/synthetic'), Path('/approval'), Path('/key'), Path('/reg'), CONFIG, Path('/sealed'))
        read.assert_called_once_with(Path('/approval'))

    def test_guard_score_once(self):
        from timemachine.tm09_desk import seal, store_new
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            approval, key, reg, sealed = [root / k for k in ('approval', 'key', 'reg', 'sealed')]
            key.write_text(KEY); reg.write_text('synthetic'); sealed.write_text(json.dumps(self.data))
            scorer = ROOT / 'timemachine/score_tm09.py'
            pins = dict(scope='ledger-222-score-once', root=tmp, approved_by='synthetic', results_path=str(sealed),
                        mode='A',
                        release=str(ROOT), scorer_sha256=sha256(scorer.read_bytes()).hexdigest(),
                        dependency_sha256={name: sha256((scorer.parent / name).read_bytes()).hexdigest() for name in DEPS},
                        config_sha256=sha256(CONFIG.read_bytes()).hexdigest(), registration_sha256=sha256(reg.read_bytes()).hexdigest(),
                        results_sha256=sha256(sealed.read_bytes()).hexdigest())
            store_new(approval, {'body': pins, 'seal': seal(KEY, 'tm09-score-approval', pins)})
            self.assertTrue(run_approved(root, approval, key, reg, CONFIG, sealed)['news_helps'])
            with self.assertRaises(FileExistsError):
                run_approved(root, approval, key, reg, CONFIG, sealed)


class BlindTest(unittest.TestCase):
    def test_gate_routes_and_is_invariant_to_all_week_signs(self):
        study = settings(read_private(CONFIG))['study']
        for vals, expect in [([0,0,0,0,0], 'A'), ([-125,-60,0,60,125], 'B'), ([-250,-120,0,120,250], 'C')]:
            result = tm09_blind.calculate(study, vals)
            self.assertEqual(result['decision'], expect)
            self.assertEqual(result, tm09_blind.calculate(study, [-x for x in vals]))

    def test_blinded_cli_never_emits_arm_payload_and_claims_once(self):
        allowed = {'placebo_sd_bps', 'primary_sd_a_bps', 'primary_sd_b_bps', 'edge_a_bps', 'edge_b_bps', 'decision'}
        marker = 'PRIVATE_PER_ARM_RETURN_+919.213333'
        with TemporaryDirectory() as test_root:
            top = Path(test_root)
            for reading in ('good', 'bad'):
                root = top / reading
                root.mkdir()
                approval, key, reg = (root / n for n in ('approval', 'key', 'reg'))
                contrasts = root / 'stage1-contrasts.json'
                (root / 'armpayload-forbidden.json').write_text(marker)
                key.write_text(KEY); reg.write_text('invented')
                store_new(contrasts, ['-100', '-60', '0', '60', '100'] if reading == 'good' else {'arm_returns': [marker]})
                module = Path(tm09_blind.__file__).resolve()
                body = dict(scope='ledger-222-check-stage1-once', root=str(root), release=str(ROOT),
                            checker_sha256=sha256(read_private(module)).hexdigest(),
                            dependency_sha256={n: sha256(read_private(module.parent / n)).hexdigest() for n in tm09_blind.DEPS},
                            config_sha256=sha256(read_private(CONFIG)).hexdigest(), registration_sha256=sha256(read_private(reg)).hexdigest(),
                            contrasts_path=str(contrasts), contrasts_sha256=sha256(read_private(contrasts)).hexdigest(), approved_by='synthetic')
                store_new(approval, {'body': body, 'seal': seal(KEY, 'tm09-stage1-check-approval', body)})
                tm09_blind.input_receipt(root, KEY, str(ROOT), body['config_sha256'], body['registration_sha256'],
                                         body['contrasts_sha256'], 5)
                before = set(root.iterdir())
                argv = ['check', '--root', str(root), '--approval', str(approval), '--key-file', str(key),
                        '--registration', str(reg), '--config', str(CONFIG), '--contrasts', str(contrasts)]
                stdout, stderr = StringIO(), StringIO()
                with patch('sys.argv', argv), patch('timemachine.tm09_blind.read_private', wraps=read_private) as read:
                    with redirect_stdout(stdout), redirect_stderr(stderr):
                        if reading == 'good':
                            tm09_blind.main()
                        else:
                            with self.assertRaises(SystemExit):
                                tm09_blind.main()
                    self.assertNotIn(root / 'armpayload-forbidden.json', [c.args[0] for c in read.call_args_list])
                new = set(root.iterdir()) - before
                self.assertNotIn(marker, stdout.getvalue() + stderr.getvalue() + ''.join(p.read_text() for p in new))
                self.assertIn(root / 'stage1-check.claim.json', new)
                if reading == 'good':
                    self.assertEqual(set(json.loads(stdout.getvalue())), allowed)
                    self.assertEqual(set(json.loads((root / 'stage1-checked.json').read_text())), allowed)
                    report_path = root / 'stage1-checked.json'
                    mode = json.loads(read_private(report_path))['decision']
                    with patch('timemachine.tm09_blind.read_private', wraps=read_private) as checked:
                        tm09_blind.verify_stage2(root, KEY, mode, sha256(read_private(report_path)).hexdigest(),
                                                 body['config_sha256'], body['registration_sha256'], 5)
                        self.assertNotIn(contrasts, [c.args[0] for c in checked.call_args_list])
                    with self.assertRaises(ValueError):
                        tm09_blind.verify_stage2(root, KEY, 'A' if mode == 'B' else 'B', sha256(read_private(report_path)).hexdigest(),
                                                 body['config_sha256'], body['registration_sha256'], 5)
                    with self.assertRaises(FileExistsError):
                        tm09_blind.run_approved(root, approval, key, reg, CONFIG, contrasts)
                    (root / 'stage1-check.claim.json').write_text('{"approval_sha256":"changed"}')
                    with self.assertRaises(ValueError):
                        tm09_blind.verify_stage2(root, KEY, mode, sha256(read_private(report_path)).hexdigest(),
                                                 body['config_sha256'], body['registration_sha256'], 5)
                else:
                    self.assertFalse(stdout.getvalue())
                    self.assertEqual(len(new), 1)

    def test_stage2_refuses_bare_decision(self):
        with TemporaryDirectory() as test_root:
            root = Path(test_root)
            report = root / 'stage1-checked.json'
            store_new(report, {'decision':'A'})
            with self.assertRaises(FileNotFoundError):
                tm09_blind.verify_stage2(root, KEY, 'A', sha256(read_private(report)).hexdigest(), '1'*64, '2'*64, 5)


if __name__ == '__main__':
    unittest.main()
