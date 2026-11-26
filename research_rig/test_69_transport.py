"""Run with python3 -B research_rig/test_69_transport.py; no network or real bars."""

from contextlib import redirect_stdout
import gzip
import io
import json
import os
from pathlib import Path
import stat
import subprocess
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

        self.assertEqual(self.sleep.call_args_list, [call(2)])
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
        self.assertEqual(self.sleep.call_args_list, [call(2), call(4), call(8), call(16)])

    def test_non_retryable_error_and_redirect(self):
        for status, body in ((401, b'private'), (302, b'https://elsewhere.invalid')):
            with self.subTest(status=status):
                self.runner.reset_mock()
                self.runner.return_value = reply(status, body)
                with self.assertRaisesRegex(ValueError, rf'^Alpaca bars HTTP {status}; no response body logged$'):
                    sweep.bars_transport()({})
                self.runner.assert_called_once()
        self.sleep.assert_not_called()

    def test_truncated_body(self):
        self.runner.return_value = reply(200, b'{"bars":')
        with self.assertRaises(json.JSONDecodeError):
            sweep.bars_transport()({})
        self.runner.return_value = reply(200, b'{"bars":{}}', rc=18)
        with self.assertRaisesRegex(ValueError, r'^Alpaca bars transport failed; no response body logged$'):
            sweep.bars_transport()({})
        self.sleep.assert_not_called()

    def test_no_proxy_never_starts_curl(self):
        del os.environ['HTTPS_PROXY']
        with self.assertRaisesRegex(ValueError, 'requires the credential HTTPS proxy'):
            sweep.bars_transport()
        self.runner.assert_not_called()


if __name__ == '__main__':
    unittest.main()
