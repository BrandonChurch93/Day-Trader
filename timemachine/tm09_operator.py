"""Operator-only fixture custody, creation, serving and export for TM09."""
import argparse
from decimal import Decimal, localcontext
import fcntl
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import signal
import stat
from urllib.parse import parse_qs, urlsplit

from timemachine.tm09_desk import Desk, PORTS, PUBLIC_SID, SID, initialize, seal, slot, store_new, verify_seal, weekly_benchmark
from timemachine.tm09_fixture import compile_export, compile_weeks, encode, fingerprint, mondays, read_private, session_layout, settings, stage1_weeks
from timemachine.tm09_blind import exact, input_receipt, verify_stage2
from timemachine.tm09_orders import BenchmarkUnavailable

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
    key_stat = keyfile.stat(follow_symlinks=False)
    if (keyfile.parent != root or key_stat.st_uid != os.geteuid() or not stat.S_ISREG(key_stat.st_mode)
            or key_stat.st_mode & 0o077):
        raise PermissionError('key must be private within TM09 root')
    key = read_private(keyfile).decode().strip()
    capsule = json.loads(read_private(approval))
    body = capsule['body']
    scope = ('ledger-222-rehearse-tm09' if rehearsal else 'ledger-222-build-fixtures' if command == 'build' else
             'ledger-222-seal-results' if command == 'results' else
             'ledger-222-seal-stage1' if command == 'stage1-seal' else 'ledger-222-run-tm09')
    verify_seal(key, scope, body, capsule['seal'])
    release = Path(__file__).resolve().parent.parent
    if (body['root'] != str(root) or body['service_uid'] != os.geteuid() or body['release'] != str(release)
            or release.name.startswith('tm07') or not body['approved_by']):
        raise ValueError('approval is not bound to this release, root and service account')
    def release_content(name, pin):
        path = release / name
        meta = path.lstat()
        if meta.st_uid != 0 or meta.st_mode & 0o022:
            raise PermissionError('release file must be operator-owned and not service-writable')
        return content(path, pin)

    for directory in (release, release / 'timemachine', release / 'config'):
        meta = directory.lstat()
        if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != 0 or meta.st_mode & 0o022:
            raise PermissionError('release directories must be operator-owned and not service-writable')
    files = ('timemachine/tm09_desk.py', 'timemachine/tm09_orders.py', 'timemachine/tm09_fixture.py', 'timemachine/tm09_feed.py',
             'timemachine/tm09_operator.py', 'timemachine/tm09_isolation_probe.py',
             'timemachine/score_tm09.py', 'timemachine/tm09_blind.py', 'timemachine/test_tm09.py', 'timemachine/TM09_WORKER_BRIEFS.md')
    for name in files:
        release_content(name, body['release_files'][name])
    config = release_content('config/thresholds.yaml', body['config_sha256'])
    release_content('timemachine/TM09_REGISTRATION.md', body['registration_sha256'])
    opts = settings(config)
    if command != 'build':
        if (body['resolved_settings'] != opts or not body['operator_boundary_sha256']
                or not rehearsal and not body['synthetic_rehearsal_sha256']):
            raise ValueError('missing signed rehearsal, boundary or settings')
        if command == 'results' and body['window_closed'] is not True:
            raise ValueError('lead must sign scored-window closure')
        if set(body['limits']) != {'notes', 'note_chars', 'looks', 'look_rows', 'headline_rows', 'headline_chars'}:
            raise ValueError('exact signed worker limits required')
        if not body['ports'] or any(type(p) is not int or p not in PORTS for p in body['ports']):
            raise ValueError('ports outside the TM09 allowlist')
        opts.update(body['limits'])
    if 'amendment_1' in opts['study']:
        mode = 'A' if rehearsal else body['mode']
        if mode not in ('stage1', 'A', 'B'):
            raise ValueError('TM09 cannot run without its amended branch')
        if (command == 'results' and mode == 'stage1') or (command == 'stage1-seal' and mode != 'stage1'):
            raise ValueError('release scope does not match the study stage')
        if not rehearsal and mode in ('A', 'B'):
            verify_stage2(root, key, mode, body['blind_report_sha256'], body['config_sha256'],
                          body['registration_sha256'], len(stage1_weeks(opts['study'])))
        opts['mode'] = mode
    return key, body, config, opts


def worker_handler(desk):
    class Worker(BaseHTTPRequestHandler):
        timeout = 5
        def log_message(self, *args):
            pass

        def _reply(self, code, value):
            desk.access(*self.route_meta(), code)
            blob = encode(value).encode()
            self.send_response_only(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(blob)))
            self.end_headers()
            try:
                self.wfile.write(blob)
            except OSError:
                return False
            return True

        def route_meta(self):
            method = getattr(self, 'command', '')
            method = method if method in ('GET', 'POST', 'HEAD', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'TRACE', 'CONNECT') else 'unknown'
            try:
                url = urlsplit(getattr(self, 'path', ''))
                path = url.path if url.path in ('/desk/status', '/desk/next', '/desk/notes', '/desk/pick', '/desk/look') else 'unknown'
                ids = parse_qs(url.query, strict_parsing=True).get('session', [])
                session = ids[0] if len(ids) == 1 and PUBLIC_SID.fullmatch(ids[0]) else None
            except ValueError:
                path, session = 'unknown', None
            return method, path, session

        def send_error(self, code, message=None, explain=None):
            # Even HTTP parser and unsupported-method errors avoid real time and reflected values.
            if getattr(self, 'request_version', 'HTTP/0.9') == 'HTTP/0.9':
                self.request_version = 'HTTP/1.0'
            desk.access(*self.route_meta(), None)
            self._reply(code, {'error': 'request refused'})

        def _route(self, post):
            desk.access(*self.route_meta(), None)
            try:
                url = urlsplit(self.path)
                action = url.path.removeprefix('/desk/')
                if (not url.path.startswith('/desk/') or action not in (('look', 'pick', 'notes') if post else ('next', 'status'))
                        or parse_qs(url.query, strict_parsing=True) != {'session': [desk.public_id]}):
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
                sent = self._reply(200, value)
                if sent and action == 'next' and value.get('news_notes'):
                    desk.confirm_delivery(value['wake'])

        def do_GET(self):
            self._route(False)

        def do_POST(self):
            self._route(True)

    return Worker


def boundary_receipt(desk, key, path, stage):
    capsule = json.loads(read_private(path))
    body = capsule['body']
    verify_seal(key, 'ledger-222-tm09-' + stage, body, capsule['seal'])
    if (body['session'] != desk.public_id or not re.fullmatch(r'[a-f0-9]{32}', body['nonce'])
            or body['port'] not in PORTS):
        raise ValueError('wrong boundary receipt')
    return body


def signature_digest(value):
    return isinstance(value, str) and re.fullmatch(r'[a-f0-9]{64}', value) is not None


def benchmark_outcome(fixture, options, models):
    if not any(None not in arms.values() for arms in models.values()):
        return {'benchmark': None}
    try:
        return {'benchmark': weekly_benchmark(fixture, options)}
    except BenchmarkUnavailable as exc:
        return {'benchmark': None, 'benchmark_unavailable': str(exc)}


def stage1_contrasts(weeks, options, load_boss):
    if list(weeks) != [d.isoformat() for d in stage1_weeks(options['study'])]:
        raise ValueError('Stage 1 expected its original configured weeks in order')
    layout = session_layout(options['study'], 'stage1')
    values = []
    for week in weeks:
        gaps = []
        for boss in options['study']['boss_models']:
            p1, p2 = (load_boss(week, boss, arm) for arm in layout.placebo)
            if p1 is None or p2 is None:
                raise ValueError('Stage 1 requires both complete bosses at every scheduled week')
            gaps.append(exact(p1) - exact(p2))
        contrast = 10000 * sum(gaps) / len(gaps)
        with localcontext() as ctx:
            ctx.prec = 2200
            shown = str(Decimal(contrast.numerator) / Decimal(contrast.denominator))
        if exact(shown) != contrast:
            raise ValueError('cannot encode unrounded Stage 1 contrast')
        values.append(shown)
    return values


def stop_server(*_):
    raise KeyboardInterrupt


class DeskHTTPServer(ThreadingHTTPServer):
    daemon_threads = False  # Drain in-flight requests before issuing a stop receipt.


def launch(desk, port, key, boundary, canary_path):
    before = boundary_receipt(desk, key, boundary, 'launch')
    if (port != before['port'] or before['canary_observed'] is not True
            or before['sudo_size_after'] <= before['sudo_size_before'] or before['sudo_size_before'] < 0
            or not signature_digest(before['sudo_checkpoint_sha256'])):
        raise ValueError('operator before-launch canary required')
    evidence = json.loads(content(canary_path, before['sudo_checkpoint_sha256']))
    if (evidence.get('session') != desk.public_id or evidence.get('port') != port
            or evidence.get('nonce') != before['nonce'] or evidence.get('matched_canary') is not True
            or evidence.get('prefix_unchanged') is not True
            or evidence.get('size_before') != before['sudo_size_before'] or evidence.get('size_after') != before['sudo_size_after']):
        raise ValueError('invalid before-launch canary evidence')
    nonce = before['nonce']
    record = {'session': desk.public_id, 'nonce': nonce, 'port': port,
              'boundary_sha256': fingerprint(before), 'sudo_checkpoint_sha256': before['sudo_checkpoint_sha256'],
              'journal_start_row': desk.access_checkpoint()}
    # Binding fails if the approved port is in use. A nonce cannot be reused after a launch.
    fd = os.open(desk.path / '.listener-lock', os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if desk.complete():
            raise ValueError('completed desk cannot launch')
        with DeskHTTPServer(('127.0.0.1', port), worker_handler(desk)) as server:
            store_new(desk.path / (nonce + '-control.json'), {'body': record, 'seal': seal(key, 'tm09-control', record)})
            handler = signal.signal(signal.SIGTERM, stop_server)
            try:
                print(READY, flush=True)
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            finally:
                signal.signal(signal.SIGTERM, handler)
        stop = {**record, 'journal_stop_row': desk.access_checkpoint()}
        store_new(desk.path / (nonce + '-stop.json'), {'body': stop, 'seal': seal(key, 'tm09-stop', stop)})
    finally:
        os.close(fd)


def review(desk, key, boundary, probe_path):
    after = boundary_receipt(desk, key, boundary, 'review')
    nonce = after['nonce']
    control = json.loads(read_private(desk.path / (nonce + '-control.json')))
    stop = json.loads(read_private(desk.path / (nonce + '-stop.json')))
    verify_seal(key, 'tm09-control', control['body'], control['seal'])
    verify_seal(key, 'tm09-stop', stop['body'], stop['seal'])
    evidence = json.loads(content(probe_path, after['post_stop_probe_sha256']))
    if (after['control_sha256'] != fingerprint(control) or after['port'] != control['body']['port']
            or after['sudo_allowlist_reviewed'] is not True
            or after['raw_copies_denied'] is not True or after['listener_stopped'] is not True
            or not signature_digest(after['post_stop_probe_sha256']) or not signature_digest(after['sudo_review_sha256'])
            or evidence.get('phase') != 'stopped' or evidence.get('session') != desk.public_id
            or evidence.get('port') != after['port'] or type(evidence.get('denied_count')) is not int
            or evidence['denied_count'] < 1
            or {k: stop['body'][k] for k in control['body']} != control['body']):
        raise ValueError('incomplete post-stop operator review')
    routes = desk.access_records(control['body']['journal_start_row'], stop['body']['journal_stop_row'])
    record = {'session': desk.public_id, 'nonce': nonce, 'post_stop_receipt_sha256': fingerprint(after), 'routes': routes}
    store_new(desk.path / (nonce + '-review.json'), {'body': record, 'seal': seal(key, 'tm09-review', record)})
    print('TM09 review saved; redacted route records:', len(routes))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('build', 'create', 'launch', 'review', 'export-notes', 'successor',
                                      'sparse-counts', 'stage1-seal', 'results'))
    for name in ('root', 'key-file', 'approval'):
        p.add_argument('--' + name, required=True, type=Path)
    p.add_argument('--week')
    p.add_argument('--role', choices=('price_scout', 'news_scout', 'boss'))
    p.add_argument('--arm')
    p.add_argument('--boss')
    p.add_argument('--port', type=int)
    p.add_argument('--export-dir', type=Path)
    p.add_argument('--boundary', type=Path, help='operator-signed per-session launch or review receipt')
    p.add_argument('--canary-proof', type=Path, help='redacted operator privilege-audit canary evidence')
    p.add_argument('--probe-proof', type=Path, help='redacted post-stop worker isolation evidence')
    p.add_argument('--rehearsal', action='store_true', help='invented built-in inputs only; distinct signed scope and slots')
    a = p.parse_args()
    os.umask(0o077)
    try:
        if a.rehearsal and a.command not in ('create', 'launch', 'review', 'export-notes', 'sparse-counts'):
            raise ValueError('unsupported invented rehearsal command')
        key, approval, config, options = approved(a.root, a.key_file, a.approval, a.command, a.rehearsal)
        stage1 = options.get('mode') == 'stage1'
        week_dates = stage1_weeks(options['study']) if stage1 else mondays(options['study'])
        weeks = [m.isoformat() for m in week_dates]
        layout = session_layout(options['study'], options.get('mode'))
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
        def export_dir():
            d = a.export_dir
            if not d or d.parent != a.root or approval['export_dir'] != str(d):
                raise ValueError('signed service-owned export directory must be inside the TM09 root')
            meta = d.lstat()
            if not stat.S_ISDIR(meta.st_mode) or meta.st_uid != os.geteuid() or meta.st_mode & 0o077:
                raise PermissionError('private export directory required')
            return d

        fixture_dir = a.root / ('fixtures-stage1' if stage1 else 'fixtures')
        if a.command == 'build':
            counts = {} if stage1 else {'skipped_edited_or_changed_clock': 0}
            fixtures = compile_export(options, export_dir(), approval['export_sha256'], counts, stage1=stage1)
            fixture_dir.mkdir(mode=0o700)
            for week, fixture in fixtures.items():
                store_new(fixture_dir / (week + '.json'), fixture)
            store_new(fixture_dir / 'fixture-pins.json', {w: fingerprint(f) for w, f in fixtures.items()})
            store_new(fixture_dir / 'fixture-counts.json', counts)
            print('TM09 fixture count:', len(fixtures))
            print(encode(counts))
            return

        def get_fixture(week):
            if week not in weeks:
                raise ValueError('unregistered week')
            if a.rehearsal:
                return invented[week]
            fixture = json.loads(read_private(fixture_dir / (week + '.json')))
            if fingerprint(fixture) != approval['fixture_pins'][week]:
                raise ValueError('approved week fixture changed')
            return fixture

        if a.command == 'stage1-seal':
            def load_boss(week, boss, arm):
                path = a.root / slot(week, 'boss', boss, arm)
                d = Desk(path, get_fixture(week), key, approved_options=options) if path.exists() else None
                return d.export_boss() if d and d.complete() else None

            values = stage1_contrasts(weeks, options, load_boss)
            store_new(a.root / 'stage1-contrasts.json', values)
            input_receipt(a.root, key, approval['release'], approval['config_sha256'], approval['registration_sha256'],
                          sha256((encode(values) + '\n').encode()).hexdigest(), len(values))
            print('TM09 Stage 1 blinded handoff sealed; no values printed.')
            return
        if a.command == 'results':
            results = {}
            feed = json.loads(content(fixture_dir / 'fixture-counts.json', approval['fixture_counts_sha256']))['by_week']
            for week in weeks:
                fixture = get_fixture(week)
                models, presented = {}, set()
                for boss in options['study']['boss_models']:
                    arms = models[boss] = {}
                    for arm in layout.arms:
                        path = a.root / slot(week, 'boss', boss, arm)
                        d = Desk(path, fixture, key, approved_options=options) if path.exists() else None
                        arms[arm] = d.export_boss() if d and d.complete() else None
                        if d and arm in layout.news:
                            presented.update(d.delivery_wakes())
                results[week] = dict(models=models, eligible_wakes=sum(map(bool, fixture['news_index'].values())),
                                     note_wakes=len(presented),
                                     feed_counts=feed[week],
                                     **benchmark_outcome(fixture, options, models))
            store_new(a.root / 'sealed-results.json', results)
            print('TM09 result handoff sealed; no returns printed.')
            return
        fixture = get_fixture(a.week)
        if (a.arm is not None and a.arm not in layout.arms) or (stage1 and a.role == 'news_scout'):
            raise ValueError('unregistered arm')
        sid = slot(a.week, a.role, a.boss, a.arm)
        if not SID.fullmatch(sid):
            raise ValueError('invalid slot')
        path = a.root / sid

        def stream(role):
            return json.loads(read_private(a.root / slot(a.week, role) / 'scout-export.json'))

        def news_reader():
            if a.rehearsal:
                return '\n'.join(map(encode, news)).encode()
            return content(export_dir() / 'stock_news.jsonl', approval['export_sha256']['stock_news.jsonl'])

        if a.command == 'create':
            # Both scouts finish before any boss, but price arms don't load the news stream.
            if (a.role == 'boss' and layout.news
                    and not Desk(a.root / slot(a.week, 'news_scout'), fixture, key, approved_options=options).complete()):
                raise ValueError('both scout streams must finish first')
            desk, token = initialize(a.root, fixture, options, a.role, key, boss=a.boss, arm=a.arm,
                                     price=stream('price_scout') if a.role == 'boss' else None,
                                     news=stream('news_scout') if a.arm in layout.news else None)
            store_new(path / 'bearer.json', {'session': desk.public_id, 'token': token})
            print(desk.public_id)
            return
        desk = Desk(path, fixture, key, news_reader=news_reader if a.role == 'news_scout' else None, approved_options=options)
        if a.command == 'export-notes':
            store_new(path / 'scout-export.json', desk.export_notes())
        elif a.command == 'sparse-counts':
            print(encode(desk.sparse_counts()))
        elif a.command == 'successor':
            token, handoff = desk.successor()
            store_new(path / 'successor-handoff.json', handoff)
            store_new(path / 'successor-bearer.json', {'session': desk.public_id, 'token': token})
        elif a.command == 'launch':
            if not a.port in PORTS or a.port not in approval['ports'] or desk.complete():
                raise ValueError('unapproved launch port or completed desk')
            launch(desk, a.port, key, a.boundary, a.canary_proof)
        elif a.command == 'review':
            review(desk, key, a.boundary, a.probe_proof)
    except (ValueError, KeyError, TypeError, OSError):
        p.exit(1, 'TM09 operation refused; review the private signed ceremony, not raw inputs.\n')


if __name__ == '__main__':
    main()
