"""Operator-only fixture custody, creation, serving and export for TM09."""
import argparse
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import stat
from urllib.parse import parse_qs, urlsplit

from timemachine.tm09_desk import Desk, SID, initialize, slot, store_new, verify_seal, weekly_benchmark
from timemachine.tm09_fixture import EXPORT, compile_export, compile_weeks, encode, fingerprint, mondays, read_private, settings

READY = 'Registered desk ready; brief only this session\'s roles.'
MAX_BODY = 65536


def content(path, pin):
    raw = read_private(path)
    if sha256(raw).hexdigest() != pin:
        raise ValueError('approved input changed')
    return raw


def approved(root, keyfile, approval, command, rehearsal=False):
    if root != Path('/var/lib/tm09') or Path(os.path.realpath(root)) != root:
        raise ValueError('direct TM09 root required')
    mode = root.stat()
    if not stat.S_ISDIR(mode.st_mode) or mode.st_uid != os.geteuid() or mode.st_mode & 0o077 or not os.geteuid():
        raise PermissionError('use the private dedicated service account')
    if keyfile.parent != root or keyfile.stat(follow_symlinks=False).st_mode & 0o077:
        raise PermissionError('key must be private within TM09 root')
    key = read_private(keyfile).decode().strip()
    capsule = json.loads(read_private(approval))
    body = capsule['body']
    scope = ('ledger-222-rehearse-tm09' if rehearsal else 'ledger-222-build-fixtures' if command == 'build' else
             'ledger-222-seal-results' if command == 'results' else 'ledger-222-run-tm09')
    verify_seal(key, scope, body, capsule['seal'])
    release = Path(__file__).resolve().parent.parent
    if (body['root'] != str(root) or body['service_uid'] != os.geteuid() or body['release'] != str(release)
            or release.name.startswith('tm07') or not body['approved_by']):
        raise ValueError('approval is not bound to this release, root and service account')
    files = ('timemachine/tm09_desk.py', 'timemachine/tm09_orders.py', 'timemachine/tm09_fixture.py',
             'timemachine/tm09_operator.py', 'timemachine/tm09_isolation_probe.py',
             'timemachine/score_tm09.py', 'timemachine/test_tm09.py', 'timemachine/TM09_WORKER_BRIEFS.md')
    for name in files:
        content(release / name, body['release_files'][name])
    config = content(release / 'config/thresholds.yaml', body['config_sha256'])
    content(release / 'timemachine/TM09_REGISTRATION.md', body['registration_sha256'])
    opts = settings(config)
    if command != 'build':
        if (body['resolved_settings'] != opts or not body['operator_boundary_sha256']
                or not rehearsal and not body['synthetic_rehearsal_sha256']):
            raise ValueError('missing signed rehearsal, boundary or settings')
        if command == 'results' and body['window_closed'] is not True:
            raise ValueError('lead must sign scored-window closure')
        if set(body['limits']) != {'notes', 'note_chars', 'looks', 'look_rows', 'headline_rows', 'headline_chars'}:
            raise ValueError('exact signed worker limits required')
        opts.update(body['limits'])
    return key, body, config, opts


def worker_handler(desk):
    class Worker(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _reply(self, code, value):
            blob = encode(value).encode()
            self.send_response_only(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(blob)))
            self.end_headers()
            try:
                self.wfile.write(blob)
            except OSError:
                pass

        def _route(self, post):
            try:
                url = urlsplit(self.path)
                action = url.path.removeprefix('/desk/')
                if (not url.path.startswith('/desk/') or action not in (('look', 'pick', 'notes') if post else ('next', 'status'))
                        or parse_qs(url.query, strict_parsing=True) != {'session': [desk.path.name]}):
                    raise PermissionError('wrong route')
                token = self.headers.get('Authorization', '').removeprefix('Bearer ')
                if self.headers.get('Authorization') != 'Bearer ' + token:
                    raise PermissionError('bearer required')
                body = None
                if post:
                    size = int(self.headers.get('Content-Length', '0'))
                    if not 1 <= size <= MAX_BODY or self.headers.get('Transfer-Encoding'):
                        raise ValueError('invalid request body')
                    body = json.loads(self.rfile.read(size))
                value = desk.handle(token, action, body)
            except PermissionError:
                self._reply(403, {'error': 'request not allowed'})
            except (ValueError, KeyError, TypeError, OSError):
                self._reply(400, {'error': 'request refused'})
            except Exception:
                self._reply(500, {'error': 'desk unavailable'})
            else:
                self._reply(200, value)

        def do_GET(self):
            self._route(False)

        def do_POST(self):
            self._route(True)

    return Worker


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('build', 'create', 'serve', 'export-notes', 'successor', 'results'))
    for name in ('root', 'key-file', 'approval'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--week')
    p.add_argument('--role', choices=('price_scout', 'news_scout', 'boss'))
    p.add_argument('--arm', choices=('P1', 'P2', 'N'))
    p.add_argument('--boss')
    p.add_argument('--port', type=int)
    p.add_argument('--rehearsal', action='store_true', help='invented built-in inputs only; distinct signed scope and slots')
    a = p.parse_args()
    os.umask(0o077)
    try:
        if a.rehearsal and a.command not in ('create', 'serve', 'export-notes'):
            raise ValueError('unsupported invented rehearsal command')
        key, approval, config, options = approved(a.root, a.key_file, a.approval, a.command, a.rehearsal)
        weeks = [m.isoformat() for m in mondays(options['study'])]
        if a.rehearsal:
            from timemachine.test_tm09 import inputs
            synth, sessions, bars, news = inputs()
            options['symbols'] = synth['symbols']
            options['study']['window'] = synth['study']['window']
            weeks = [m.isoformat() for m in mondays(options['study'])]
            invented = compile_weeks(options, sessions, bars, news)
            directory = a.root / 'invented-rehearsal'
            directory.mkdir(mode=0o700, exist_ok=True)
            if not stat.S_ISDIR(directory.lstat().st_mode) or directory.stat().st_uid != os.geteuid() or directory.stat().st_mode & 0o077:
                raise PermissionError('rehearsal directory not private')
            a.root = directory
        if a.command == 'build':
            fixtures = compile_export(config, EXPORT, approval['export_sha256'])
            directory = a.root / 'fixtures'
            directory.mkdir(mode=0o700)
            for week, fixture in fixtures.items():
                store_new(directory / (week + '.json'), fixture)
            store_new(a.root / 'fixture-pins.json', {w: fingerprint(f) for w, f in fixtures.items()})
            print('TM09 fixture count:', len(fixtures))
            return

        def get_fixture(week):
            if week not in weeks:
                raise ValueError('unregistered week')
            if a.rehearsal:
                return invented[week]
            fixture = json.loads(read_private(a.root / 'fixtures' / (week + '.json')))
            if fingerprint(fixture) != approval['fixture_pins'][week]:
                raise ValueError('approved week fixture changed')
            return fixture

        if a.command == 'results':
            results = {}
            for week in weeks:
                fixture = get_fixture(week)
                models = {}
                for boss in options['study']['boss_models']:
                    arms = models[boss] = {}
                    for arm in ('P1', 'P2', 'N'):
                        path = a.root / slot(week, 'boss', boss, arm)
                        d = Desk(path, fixture, key, approved_options=options) if path.exists() else None
                        arms[arm] = d.export_boss() if d and d.complete() else None
                path = a.root / slot(week, 'news_scout')
                results[week] = dict(models=models, eligible_wakes=sum(map(bool, fixture['news_index'].values())),
                                     note_wakes=Desk(path, fixture, key, approved_options=options).delivery_wakes() if path.exists() else 0,
                                     benchmark=weekly_benchmark(fixture, options) if any(None not in x.values() for x in models.values()) else None)
            store_new(a.root / 'sealed-results.json', results)
            print('TM09 result handoff sealed; no returns printed.')
            return
        fixture = get_fixture(a.week)
        sid = slot(a.week, a.role, a.boss, a.arm)
        if not SID.fullmatch(sid):
            raise ValueError('invalid slot')
        path = a.root / sid

        def stream(role):
            return json.loads(read_private(a.root / slot(a.week, role) / 'scout-export.json'))

        def news_reader():
            if a.rehearsal:
                return '\n'.join(map(encode, news)).encode()
            return content(EXPORT / 'stock_news.jsonl', approval['export_sha256']['stock_news.jsonl'])

        if a.command == 'create':
            # Both scouts finish before any boss, but price arms don't load the news stream.
            if a.role == 'boss' and not Desk(a.root / slot(a.week, 'news_scout'), fixture, key, approved_options=options).complete():
                raise ValueError('both scout streams must finish first')
            _, token = initialize(a.root, fixture, options, a.role, key, boss=a.boss, arm=a.arm,
                                  price=stream('price_scout') if a.role == 'boss' else None,
                                  news=stream('news_scout') if a.arm == 'N' else None)
            store_new(path / 'bearer.json', {'session': sid, 'token': token})
            print(sid)
            return
        desk = Desk(path, fixture, key, news_reader=news_reader if a.role == 'news_scout' else None, approved_options=options)
        if a.command == 'export-notes':
            store_new(path / 'scout-export.json', desk.export_notes())
        elif a.command == 'successor':
            token, handoff = desk.successor()
            store_new(path / 'successor-handoff.json', handoff)
            store_new(path / 'successor-bearer.json', {'session': sid, 'token': token})
        elif a.command == 'serve':
            if a.port not in approval['ports'] or a.port in (8766, *range(8781, 8788)) or desk.complete():
                raise ValueError('unapproved launch port or completed desk')
            with ThreadingHTTPServer(('127.0.0.1', a.port), worker_handler(desk)) as server:
                print(READY, flush=True)
                server.serve_forever()
    except (ValueError, KeyError, TypeError, OSError):
        p.exit(1, 'TM09 operation refused; review the private signed ceremony, not raw inputs.\n')


if __name__ == '__main__':
    main()
