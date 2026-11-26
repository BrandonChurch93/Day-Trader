"""Made-up minutes, calendars, headlines, and returns only."""
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from timemachine.score_tm09 import run_approved, score
from timemachine.tm09_desk import Desk, initialize, slot
from timemachine.tm09_fixture import FILES, compile_export, compile_weeks, encode, mondays, read_private, settings
from timemachine.tm09_operator import worker_handler
from timemachine.tm09_orders import Minutes, benchmark, fill, terminal, weights

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'config/thresholds.yaml'
KEY = 'made-up unittest-only signing material'
HEADLINE = 'SYN opens moonlit widget factory'
NOTE = 'SYN started a facility for making widgets.'


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
                self.assertEqual(news['items'], [{'headline': HEADLINE, 'source_time': self.news[0]['stated_time'], 'symbols': ['SYN']}])
                with self.assertRaises(ValueError):
                    n.handle(tn, 'notes', {'wake_key': news['wake_key'], 'notes': [HEADLINE.upper() + '!']})
            else:
                self.assertEqual(news['items'], [])
            p.handle(tp, 'notes', {'wake_key': price['wake_key'], 'notes': [f'SYN price observation {i}']})
            n.handle(tn, 'notes', {'wake_key': news['wake_key'], 'notes': [NOTE] if i == 1 else []})
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
            self.assertEqual(packets[2]['news_notes'], [NOTE] if i == 1 else [])
            for (d, t), packet in zip(desks, packets):
                row = d.handle(t, 'look', {'wake_key': packet['wake_key'], 'symbol': 'SYN', 'rows': 20})
                self.assertTrue(all(b[0] + 60 <= wake for b in row['bars']))
                self.assertNotIn(HEADLINE, encode(packet))
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

    def test_sparse_fill_ambiguity_fails_without_mutating_book(self):
        m = Minutes(self.f['bars']); wake, _ = self.f['wakes'][0]
        book = {'cash':'1000', 'shares':{}}
        with self.assertRaisesRegex(ValueError, 'ruling needed'):
            fill(book, weights({'SYN': 1}, ['SYN']), m, wake, wake + 60, Decimal('.0005'), Decimal('.1'))
        self.assertEqual(book, {'cash':'1000', 'shares':{}})

    def test_export_compiler_uses_pins_and_excludes_raw_headlines(self):
        cfg = read_private(CONFIG).decode()
        import yaml
        cfg = yaml.safe_load(cfg)
        cfg['tm04_plan']['value']['symbols'] = ['SYN']
        cfg['tm09']['value']['window'] = self.opts['study']['window']
        pins = {}
        for name, records in zip(FILES, (self.sessions, self.bars, self.news)):
            blob = '\n'.join(map(encode, records)).encode()
            (self.path / name).write_bytes(blob)
            pins[name] = sha256(blob).hexdigest()
        cfg = yaml.safe_dump(cfg).encode()
        self.assertEqual(compile_export(cfg, self.path, pins)[self.f['week']], self.f)
        pins[FILES[2]] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            compile_export(cfg, self.path, pins)

    def test_worker_http_scope_and_no_store_without_binding_port(self):
        d, tok = self.init('price_scout')
        route = worker_handler(d)

        def send(path, token):
            wire = BytesIO()

            class Request:
                def makefile(self, mode, *args):
                    message = f'GET {path} HTTP/1.0\r\nAuthorization: Bearer {token}\r\n\r\n'
                    return BytesIO(message.encode())

                def sendall(self, blob):
                    wire.write(blob)

            route(Request(), ('127.0.0.1', 1), None)
            return wire.getvalue()

        answer = send(f'/desk/next?session={d.path.name}', tok)
        self.assertIn(b' 200 ', answer)
        self.assertIn(b'Cache-Control: no-store', answer)
        self.assertNotIn(tok.encode(), answer)
        self.assertIn(b' 403 ', send('/desk/next?session=TM09-SIBLING', tok))
        self.assertIn(b' 403 ', send(f'/desk/export?session={d.path.name}', tok))
        self.assertIn(b' 403 ', send(f'/desk/next?session={d.path.name}', 'x' * 48))


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
            pins = dict(scope='ledger-222-score-once', root=tmp, approved_by='synthetic', results_path=str(sealed),
                        config_sha256=sha256(CONFIG.read_bytes()).hexdigest(), registration_sha256=sha256(reg.read_bytes()).hexdigest(),
                        results_sha256=sha256(sealed.read_bytes()).hexdigest())
            store_new(approval, {'body': pins, 'seal': seal(KEY, 'tm09-score-approval', pins)})
            self.assertTrue(run_approved(root, approval, key, reg, CONFIG, sealed)['news_helps'])
            with self.assertRaises(FileExistsError):
                run_approved(root, approval, key, reg, CONFIG, sealed)


if __name__ == '__main__':
    unittest.main()
