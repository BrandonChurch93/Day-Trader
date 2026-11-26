"""Run with python3 -B research_rig/test_69_transport.py; no network or real bars."""

from contextlib import redirect_stderr, redirect_stdout
import gzip
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import call, patch
from urllib.parse import parse_qs, urlsplit

import sweep_69 as sweep


PROXY_ENV = {'HTTPS_PROXY': 'https://proxy.example.invalid:1234',
             'CURL_CA_BUNDLE': '/fake/curl-ca', 'SSL_CERT_FILE': '/fake/ssl-ca'}
FORBIDDEN_ENV = {'APCA_API_KEY_ID': 'synthetic-id-not-a-key',
                 'APCA_API_SECRET_KEY': 'synthetic-secret-not-a-key',
                 'Authorization': 'synthetic-auth-not-a-key',
                 'NO_PROXY': '*', 'HOME': '/fake/home'}


def reply(status, body=b'', rc=0):
    return subprocess.CompletedProcess([], rc, body + b'\n' + str(status).encode('ascii'), b'fake stderr')


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch.dict(os.environ, PROXY_ENV | FORBIDDEN_ENV, clear=True))
        self.runner = self.enterContext(patch.object(sweep.subprocess, 'run'))
        self.sleep = self.enterContext(patch.object(sweep.sleep_clock, 'sleep'))

    def test_collect_uses_proxy_without_headers_or_keys_and_paginates(self):
        start, end = sweep.FIRST.isoformat(), sweep.LAST.isoformat()
        stamps = ['2016-01-04T14:30:00Z', '2021-12-31T20:55:00Z']
        token = 'page+with"\n--location &'  # Must remain a query value, not a curl-config directive.
        pages = [json.dumps({'bars': {'FAKE': [{'t': stamp, 'o': 10, 'h': 10, 'l': 10, 'c': 10,
                                               'v': 1, 'vw': 10}]}, 'next_page_token': next_token}).encode()
                 for stamp, next_token in zip(stamps, (token, None))]
        self.runner.side_effect = [reply(429, b'throttled'), reply(200, pages[0]), reply(200, pages[1])]
        grid = {'universe': {'stocks': ['FAKE']}}
        identity = {'coverage_start': start, 'coverage_end': end,
                    'members': {'FAKE': {'sources': ['https://example.invalid/invented'],
                                         'aliases': [{'ticker': 'FAKE', 'start': start, 'end': end}], 'splits': []}}}
        buffers = {'identity.json': json.dumps(identity).encode(), 'calendar_65.json': b'{"sessions": []}'}
        pins = {'synthetic-fixture': 'not-an-approval'}
        with tempfile.TemporaryDirectory() as scratch, redirect_stdout(io.StringIO()) as out:
            root_fd = sweep.open_directory(Path(scratch))
            try:
                sweep.collect(grid, sweep.FIRST, sweep.LAST, root_fd, buffers, pins)
            finally:
                os.close(root_fd)
            archive = Path(scratch) / sweep.BAR_FILE
            receipt = Path(scratch) / sweep.RECEIPT
            self.assertEqual([stat.S_IMODE(p.stat().st_mode) for p in (archive, receipt)], [0o600, 0o600])
            raw = archive.read_bytes()
            rows = list(map(json.loads, gzip.decompress(raw).splitlines()))
            self.assertEqual(rows[0], sweep.collection_header(sweep.FIRST, sweep.LAST, pins))
            self.assertEqual([row[2] for row in rows[1:]], stamps)
            captured = json.loads(out.getvalue())
            self.assertEqual(captured, {'archive_records': 2, 'bars_sha256': sweep.digest(raw)})
            self.assertEqual(json.loads(receipt.read_bytes())['bars_sha256'], captured['bars_sha256'])

        self.assertEqual(self.sleep.call_args_list, [call(.25), call(2), call(.25), call(.25)])
        params = []
        for args, kwargs in self.runner.call_args_list:
            argv, = args
            self.assertEqual(argv, ['/usr/bin/curl', '--disable', '--silent', '--show-error', '--compressed',
                                    '--proto', '=https', '--connect-timeout', '20', '--max-time', '60',
                                    '--write-out', '\n%{http_code}', '--config', '-'])
            self.assertEqual(kwargs['env'], PROXY_ENV)
            rendered = repr((argv, kwargs)).lower()
            for forbidden in (*FORBIDDEN_ENV, *FORBIDDEN_ENV.values(), 'apca-api-key-id', 'apca-api-secret-key'):
                self.assertNotIn(forbidden.lower(), rendered)
            self.assertTrue(kwargs['capture_output'])
            self.assertFalse(kwargs['check'])
            config = kwargs['input'].decode('ascii')
            self.assertRegex(config, r'^url = "[^"\n]+"\n$')
            uri = urlsplit(config.split('"')[1])
            self.assertEqual((uri.scheme, uri.netloc, uri.path), ('https', 'data.alpaca.markets', '/v2/stocks/bars'))
            params.append(parse_qs(uri.query))
        planned = {'symbols': ['FAKE'], 'timeframe': ['5Min'], 'feed': ['sip'], 'adjustment': ['raw'],
                   'asof': ['-'], 'sort': ['asc'], 'limit': ['10000'],
                   'start': ['2016-01-04T14:30:00+00:00'], 'end': ['2021-12-31T20:55:00+00:00']}
        self.assertEqual(params, [planned, planned, planned | {'page_token': [token]}])

    def test_retry_statuses_and_backoff_unchanged(self):
        self.runner.side_effect = [reply(status, b'do-not-log') for status in (429, 500, 502, 503, 504)]
        with self.assertRaisesRegex(ValueError, r'^Alpaca bars HTTP 504; no response body logged$'):
            sweep.bars_transport()({})
        self.assertEqual(self.runner.call_count, 5)
        self.assertEqual(self.sleep.call_args_list,
                         [call(.25), call(2), call(.25), call(4), call(.25),
                          call(8), call(.25), call(16), call(.25)])

    def test_non_retryable_error_and_redirect(self):
        for status, rc in ((401, 0), (403, 0), (404, 18), (302, 0)):
            with self.subTest(status=status, rc=rc):
                self.runner.reset_mock()
                self.sleep.reset_mock()
                self.runner.return_value = reply(status, b'private response', rc=rc)
                with self.assertRaisesRegex(ValueError, rf'^Alpaca bars HTTP {status}; no response body logged$'):
                    sweep.bars_transport()({})
                self.runner.assert_called_once()
                self.sleep.assert_called_once_with(.25)

    def test_transport_retries_recover(self):
        failures = {'zero status': reply('000', rc=28),
                    'missing status': subprocess.CompletedProcess([], 0, b'\nno status', b''),
                    'nonzero exit with 200': reply(200, b'{"bars":{}}', rc=18),
                    'truncated JSON': reply(200, b'{"bars":'),
                    'truncated encoding': reply(200, b'{"bars":"\xc3')}
        for kind, failure in failures.items():
            with self.subTest(kind=kind):
                self.runner.reset_mock()
                self.sleep.reset_mock()
                self.runner.side_effect = [failure, reply(200, b'{"bars":{},"next_page_token":null}')]
                self.assertEqual(sweep.bars_transport()({}), {'bars': {}, 'next_page_token': None})
                self.assertEqual(self.runner.call_count, 2)
                self.assertEqual(self.sleep.call_args_list, [call(.25), call(2), call(.25)])

    def test_transport_retries_exhausted(self):
        for failure in (reply('000'), reply(200, b'{"bars":'), reply(200, b'{}', rc=18)):
            with self.subTest(failure=failure):
                self.runner.reset_mock()
                self.sleep.reset_mock()
                self.runner.side_effect = [failure] * 8
                with self.assertRaisesRegex(sweep.BarsTransportFailure, r'^Alpaca bars transport failed; no response body logged$'):
                    sweep.bars_transport()({})
                self.assertEqual(self.runner.call_count, 8)
                self.assertEqual(self.sleep.call_args_list,
                                 [call(.25)] + [event for delay in (2, 4, 8, 16, 32, 64, 128)
                                               for event in (call(delay), call(.25))])

    def test_no_proxy_never_starts_curl(self):
        del os.environ['HTTPS_PROXY']
        with self.assertRaisesRegex(ValueError, 'requires the credential HTTPS proxy'):
            sweep.bars_transport()
        self.runner.assert_not_called()


class SpanTests(unittest.TestCase):
    def setUp(self):
        self.scratch = Path(self.enterContext(tempfile.TemporaryDirectory()))
        start, end = sweep.FIRST.isoformat(), sweep.LAST.isoformat()
        self.members = ['FAKEA', 'FAKEB', 'FAKEC']
        self.grid = {'universe': {'stocks': self.members}, 'pools': {'stocks': self.members},
                     'families': {'S1': {}},
                     'rules': [{'id': 'fixture', 'family': 'S1', 'pool': 'stocks', 'side': 'long',
                                'cash_500': True, 'latest_signal_close_et': None,
                                'entry': {'clock_et': '09:30', 'print': 'open'},
                                'exit': {'clock_et': '09:35', 'print': 'open', 'session_offset': 0}}]}
        identity = {'coverage_start': start, 'coverage_end': end,
                    'members': {name: {'sources': ['https://example.invalid/invented'],
                                       'aliases': [{'ticker': name, 'start': start, 'end': end}], 'splits': []}
                                for name in self.members}}
        self.buffers = {'GRID_69.json': json.dumps(self.grid).encode(),
                        'sweep_69.py': b'synthetic script fingerprint fixture',
                        'identity.json': json.dumps(identity).encode(),
                        'calendar_65.json': b'{"sessions":[["2016-01-04","2016-01-04T14:30:00Z","2016-01-04T21:00:00Z"]]}'}
        self.code = self.scratch / 'code'
        self.code.mkdir()
        for name in ('GRID_69.json', 'sweep_69.py', 'calendar_65.json'):
            (self.code / name).write_bytes(self.buffers[name])
        self.pins = {name: sweep.digest(self.buffers[name]) for name in ('GRID_69.json', 'sweep_69.py', 'calendar_65.json', 'identity.json')}
        self.pins['thresholds.yaml'] = sweep.digest(sweep.CONFIG_RAW)

    @staticmethod
    def vendor(query):
        name = query['symbols']
        return {'bars': {name: [{'t': '2016-01-04T14:35:00Z' if 'page_token' in query else '2016-01-04T14:30:00Z',
                                'o': 10, 'h': 10, 'l': 10, 'c': 10, 'v': 1, 'vw': 10}]},
                'next_page_token': None if 'page_token' in query else 'next'}

    def run_collect(self, folder, get):
        folder.mkdir(exist_ok=True)
        root_fd = sweep.open_directory(folder)
        err = io.StringIO()
        self.err = err
        try:
            with redirect_stdout(io.StringIO()) as out, redirect_stderr(err), patch.object(sweep, 'bars_transport', return_value=get):
                sweep.collect(self.grid, sweep.FIRST, sweep.LAST, root_fd, self.buffers, self.pins)
                return json.loads(out.getvalue())
        finally:
            os.close(root_fd)

    def interrupt(self, folder):
        def fail(query):
            if query['symbols'] == 'FAKEB' and 'page_token' in query:
                raise sweep.BarsTransportFailure('Alpaca bars transport failed; no response body logged')
            return self.vendor(query)
        with self.assertRaises(SystemExit) as stop:
            self.run_collect(folder, fail)
        self.assertEqual(stop.exception.code, 75)
        self.assertEqual(self.err.getvalue().splitlines(), ['Collection span 1 of 3: 2 rows',
            'Alpaca bars transport failed; no response body logged; spans done 1, remaining 2'])
        chunks = folder / 'chunks'
        self.assertEqual(stat.S_IMODE(chunks.stat().st_mode), 0o700)
        self.assertEqual(len(list(chunks.glob('*.tmp'))), 1)
        self.assertFalse((folder / sweep.BAR_FILE).exists())
        return next(chunks.glob('*.jsonl'))

    def legacy_archive(self):
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode='wb', filename='', mtime=0) as out:
            out.write((json.dumps(sweep.collection_header(sweep.FIRST, sweep.LAST, self.pins)) + '\n').encode())
            for name in self.members:
                for row in sweep.bars_pages(name, sweep.FIRST, sweep.LAST, self.vendor):
                    out.write((json.dumps([name, name, row['t'], *(row.get(k) for k in sweep.FIELDS)],
                                          allow_nan=False, separators=(',', ':')) + '\n').encode())
        raw = buffer.getvalue()
        receipt = (json.dumps({'scope': sweep.SCOPE, 'bars_sha256': sweep.digest(raw), 'input_sha256': self.pins,
                               'archive_records': 6}, sort_keys=True) + '\n').encode()
        return raw, receipt

    def test_resume_matches_uninterrupted_and_legacy_bytes_and_validates(self):
        resumed, fresh = self.scratch / 'resumed', self.scratch / 'fresh'
        self.interrupt(resumed)
        touched = []

        def vendor(query):
            touched.append(query['symbols'])
            return self.vendor(query)

        # Discard a dangling .tmp symlink without opening its target.
        (resumed / 'chunks' / 'leftover.tmp').symlink_to('missing')
        result = self.run_collect(resumed, vendor)
        self.assertEqual(touched, ['FAKEB', 'FAKEB', 'FAKEC', 'FAKEC'])
        self.assertEqual(result, self.run_collect(fresh, self.vendor))
        for name, expected in zip((sweep.BAR_FILE, sweep.RECEIPT), self.legacy_archive()):
            self.assertEqual((resumed / name).read_bytes(), expected)
            self.assertEqual((fresh / name).read_bytes(), expected)
        self.assertFalse((resumed / 'chunks').exists())
        (resumed / 'identity.json').write_bytes(self.buffers['identity.json'])
        (resumed / 'search_approval.json').write_text(json.dumps({'scope': sweep.SCOPE, 'approved_by': 'fixture',
                                                                 'sha256': self.pins}))
        with redirect_stdout(io.StringIO()) as out, patch.object(sweep, 'STORE', resumed), patch.object(sweep, 'HERE', self.code), \
                patch.object(sys, 'argv', ['sweep_69.py', '--validate-inputs']):
            sweep.main()
        self.assertEqual(json.loads(out.getvalue())['regular_rows'], 6)

    def test_wrong_pins_in_name_or_header_refused(self):
        folder = self.scratch / 'wrong-pins'
        chunk = self.interrupt(folder)
        saved = self.pins
        self.pins = {'fixture': 'other-pin'}
        with self.assertRaisesRegex(ValueError, 'Unexpected collection chunk'):
            self.run_collect(folder, self.vendor)
        self.pins = saved
        raw = chunk.read_bytes().replace(saved['identity.json'].encode(), b'0' * 64, 1)
        chunk.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'Invalid collection chunk'):
            self.run_collect(folder, self.vendor)

    def test_corruption_refuses_until_operator_deletes_chunk(self):
        folder = self.scratch / 'corrupt'
        chunk = self.interrupt(folder)
        raw = chunk.read_bytes()
        for altered in (raw[:-1], raw.replace(b'14:30', b'14:31', 1)):
            chunk.write_bytes(altered)
            with self.assertRaisesRegex(ValueError, 'inspect and delete it before re-collecting'):
                self.run_collect(folder, self.vendor)
            self.assertTrue(chunk.exists())
        chunk.unlink()
        self.run_collect(folder, self.vendor)
        self.assertEqual((folder / sweep.BAR_FILE).read_bytes(), self.legacy_archive()[0])

    def test_consolidation_crash_before_publish(self):
        folder = self.scratch / 'crashed'
        real_publish = sweep.publish

        def fail_before_publish(*args, **kwargs):
            if kwargs.get('dest_fd') is not None:
                raise OSError('simulated consolidation crash')
            return real_publish(*args, **kwargs)

        with patch.object(sweep, 'publish', side_effect=fail_before_publish):
            with self.assertRaisesRegex(OSError, 'simulated consolidation crash'):
                self.run_collect(folder, self.vendor)
        self.assertEqual(len(list((folder / 'chunks').glob('*.jsonl'))), 3)
        self.assertFalse((folder / sweep.BAR_FILE).exists())

        def no_refetch(_):
            self.fail('a completed chunk must not be requested again')

        self.run_collect(folder, no_refetch)
        self.assertEqual((folder / sweep.BAR_FILE).read_bytes(), self.legacy_archive()[0])

    def test_legacy_partial_still_refuses(self):
        folder = self.scratch / 'legacy'
        folder.mkdir()
        partial = folder / (sweep.BAR_FILE + '.partial')
        partial.write_bytes(b'untouched')
        with self.assertRaisesRegex(ValueError, 'Existing search data, receipt or partial'):
            self.run_collect(folder, self.vendor)
        self.assertEqual(partial.read_bytes(), b'untouched')
        self.assertFalse((folder / 'chunks').exists())


if __name__ == '__main__':
    unittest.main()
