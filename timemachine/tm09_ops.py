"""TM09 host operator ceremony: key, rehearsal approval, sudo canary, worker probes, sudo review and signed boundaries.

Prints names and hashes only, never a key, bearer, price or headline. Commands and the account each runs as:

  keygen                                          tm09desk
  approve-rehearsal BOUNDARY_TEXT                 tm09desk
  init-canaries                                   root: private tape, notes and results canary files
  bearer-copy MODE WEEK ROLE_ARGS OUT             root: the worker's own 0600 bearer copy, owned by the worker
  slot-dir MODE WEEK ROLE_ARGS                    any: prints the desk directory the engine uses
  canary-launch SID PORT                          root: unique canary, signed proof and signed launch boundary
  probe MODE PHASE SID PORT NONCE SIBLING BEARER [EXPORT_DIR]
                                                  root: runs the isolation probe as the worker account, signs the result
  review-boundary MODE SID PORT NONCE DESK_DIR OPLOG [EXPORT_DIR]
                                                  root: sudo review from the log itself, probe checks, signed review boundary

MODE is `rehearsal` or `production`; there is no default. ROLE_ARGS is one word list without `--role`:
`price_scout`, `news_scout` or `boss MODEL ARM`. Set TM09_RELEASE to the pinned release directory.
The engine (tm09_operator) checks every capsule again.
"""
from collections import Counter
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import sys

ROOT = Path('/var/lib/tm09')
OPS = ROOT / 'ops'
KEY = ROOT / 'operator.key'
CANARY_DIR = ROOT / 'canaries'
CANARY_NAMES = ('tape', 'notes', 'results')
SUDO_LOG = Path('/var/log/tm07-sudo.log')
WORKER = 'user'
SERVICE = 'tm09desk'
SECURE_PATH = ('/usr/local/sbin', '/usr/local/bin', '/usr/sbin', '/usr/bin', '/sbin', '/bin')
MODES = ('rehearsal', 'production')
PORTS = range(8801, 8807)
FILES = ('timemachine/tm09_desk.py', 'timemachine/tm09_orders.py', 'timemachine/tm09_fixture.py', 'timemachine/tm09_feed.py',
         'timemachine/tm09_operator.py', 'timemachine/tm09_isolation_probe.py', 'timemachine/score_tm09.py',
         'timemachine/tm09_blind.py', 'timemachine/test_tm09.py', 'timemachine/TM09_WORKER_BRIEFS.md')
REHEARSAL_LIMITS = dict(notes=2, note_chars=280, looks=50, look_rows=120, headline_rows=20, headline_chars=500)
NONCE = re.compile(r'[a-f0-9]{32}')
SIDRE = re.compile(r'TM09-[a-f0-9]{32}')
LINE = re.compile(r'^\w{3} +\d+ (\d\d:\d\d:\d\d) : (\S+) : (.*?)COMMAND=(.*)$')
CANARY = re.compile(r'/usr/bin/true tm09-([a-f0-9]{32})')
ROLE_ARGS = re.compile(r'(price_scout|news_scout|boss ([a-z0-9_]+) (P1|P2|N))')


class Refused(ValueError):
    pass


def h(raw):
    return sha256(raw).hexdigest()


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()


def ops_seal(key, domain, fields):
    """Host-side authentication of operator evidence (canary proof, probe proof, sudo review)."""
    return hmac.digest(key.encode(), canon(['tm09-ops', domain, fields]), 'sha256').hex()


def sealed(key, domain, fields):
    return dict(fields, ops_seal=ops_seal(key, domain, fields))


def unseal(key, domain, raw):
    obj = json.loads(raw)
    fields = {k: v for k, v in obj.items() if k != 'ops_seal'}
    if not isinstance(obj.get('ops_seal'), str) or not hmac.compare_digest(ops_seal(key, domain, fields), obj['ops_seal']):
        raise Refused(domain + ' evidence is not host-signed')
    return fields


def parse_role(text):
    m = ROLE_ARGS.fullmatch(text.strip())
    if not m:
        raise Refused('ROLE_ARGS must be price_scout, news_scout or "boss MODEL ARM"')
    if m.group(1).startswith('boss'):
        return 'boss', m.group(2), m.group(3)
    return m.group(1), None, None


def slot_name(week, role, boss=None, arm=None):
    if not re.fullmatch(r'\d{4}-\d\d-\d\d', week):
        raise Refused('week must be YYYY-MM-DD')
    return f'TM09-{week}-{boss}-{arm}' if role == 'boss' else f'TM09-{week}-{role}'


def slot_dir(mode, week, role_args):
    if mode not in MODES:
        raise Refused('MODE must be rehearsal or production')
    base = ROOT / 'invented-rehearsal' if mode == 'rehearsal' else ROOT
    return base / slot_name(week, *parse_role(role_args))


def _seconds(t):
    hh, mm, ss = map(int, t.split(':'))
    return hh * 3600 + mm * 60 + ss


def _norm(s):
    return re.sub(r'\s+', ' ', re.sub(r"[\\'\"]", '', s.replace('#012', ' '))).strip()


def parse_line(line):
    m = LINE.match(line.rstrip())
    if not m:
        return None
    fields = dict(f.strip().split('=', 1) for f in m.group(3).split(';') if '=' in f)
    return dict(time=m.group(1), invoker=m.group(2), target=fields.get('USER', '').strip(), command=m.group(4))


def record_target(argv):
    """Account a timed operator record ran as, and the remaining command argv."""
    a, target = list(argv), 'root'
    while a and a[0] in ('-u', '-n', '-g'):
        if a[0] == '-u':
            target = a[1]
        a = a[2:] if a[0] in ('-u', '-g') else a[1:]
    return target, a


def resolve(name, is_file=os.path.isfile):
    """Full executable path sudo would log for a record's first word (absolute names stay as given)."""
    if name.startswith('/'):
        return os.path.normpath(name)
    if '/' in name:
        return None
    for d in SECURE_PATH:
        if is_file(d + '/' + name):
            return d + '/' + name
    return None


def sudo_review(log, log_id, proof, records, nonce, on_file, is_file=os.path.isfile, slack=2):
    """Review the root-owned log from this launch's canary checkpoint to now. Refuses (fails closed) unless the log
    still holds the checkpointed prefix in the same file, and the checkpoint segment holds this nonce's canary once.

    Every later line must be one timed operator record (same time within slack, same target account, same full
    executable path and arguments) or a single TM09 canary whose proof is on file. Anything else is unlisted."""
    before, after = proof['size_before'], proof['size_after']
    if list(log_id) != list(proof['log_id']):
        raise Refused('sudo log was replaced or rotated since the canary')
    if len(log) < after or h(log[:after]) != proof['prefix_sha256'] or not 0 <= before < after:
        raise Refused('sudo log shrank or its checkpointed prefix changed')
    own = '/usr/bin/true tm09-' + nonce
    segment = [parse_line(l) for l in log[before:after].decode('utf-8', 'replace').splitlines() if l.strip()]
    if sum(1 for p in segment if p and p['command'] == own and p['invoker'] == WORKER and p['target'] == 'root') != 1:
        raise Refused('the checkpoint does not hold exactly one own canary')
    lines = [l for l in log[before:].decode('utf-8', 'replace').splitlines() if l.strip()]
    seen, used, listed, unlisted = Counter(), set(), [], []
    for line in lines:
        p = parse_line(line)
        if not p or p['invoker'] != WORKER:
            unlisted.append(line)
            continue
        c = CANARY.fullmatch(p['command'])
        if c:
            seen[c.group(1)] += 1
            if p['target'] == 'root' and seen[c.group(1)] == 1 and (c.group(1) == nonce or c.group(1) in on_file):
                listed.append({'time': p['time'], 'command': p['command'], 'canary': 'own' if c.group(1) == nonce else 'other'})
            else:
                unlisted.append(line)
            continue
        first, _, rest = p['command'].partition(' ')
        hit = None
        for i, r in enumerate(records):
            target, a = record_target(r['argv'])
            if (i not in used and a and abs(_seconds(p['time']) - _seconds(r['time'])) <= slack and target == p['target']
                    and resolve(a[0], is_file) == first and _norm(' '.join(a[1:])) == _norm(rest)):
                hit = i
                break
        if hit is None:
            unlisted.append(line)
        else:
            used.add(hit)
            listed.append({'time': p['time'], 'command': p['command'], 'target': p['target']})
    return {'nonce': nonce, 'entries': len(lines), 'listed': listed, 'unlisted': unlisted, 'own_canary': seen[nonce],
            'proof_sha256': proof['sha256'], 'log_id': list(log_id), 'reviewed_bytes': [before, len(log)],
            'tail_sha256': h(log[before:])}


def clean(review):
    return (review['unlisted'] == [] and review['own_canary'] == 1 and review['entries'] == len(review['listed']))


def check_probe(fields, sid, port, phase, canaries):
    if (fields.get('phase') != phase or fields.get('session') != sid or fields.get('port') != port
            or fields.get('worker') != WORKER or sorted(fields.get('canaries', [])) != sorted(map(str, canaries))
            or fields.get('denied_count') != len(canaries) or not canaries):
        raise Refused(phase + ' probe does not cover the required scope')


def required_canaries(mode, export_dir=None, root=ROOT, exists=os.path.exists):
    """Existing TM09-only private files a worker must fail to read: key, tape, notes and results."""
    paths = [root / 'operator.key'] + [root / 'canaries' / n for n in CANARY_NAMES]
    if mode == 'production':
        if not export_dir:
            raise Refused('production probes need the private export directory')
        paths += sorted(Path(export_dir).glob('*.jsonl'))
        paths += sorted(root.glob('TM09-*/scout-export.json')) + sorted(root.glob('*results*.json'))
    missing = [p for p in paths if not exists(p)]
    if missing or len(paths) < 4:
        raise Refused('a required canary file is missing')
    return paths


def launch_body(sid, port, proof_fields, proof_raw):
    ev = proof_fields
    if (ev.get('session') != sid or ev.get('port') != port or not NONCE.fullmatch(ev.get('nonce', ''))
            or ev.get('matched_canary') is not True or ev.get('prefix_unchanged') is not True
            or not 0 <= ev['size_before'] < ev['size_after']):
        raise Refused('canary proof does not support a launch')
    return dict(session=sid, port=port, nonce=ev['nonce'], canary_observed=True,
                sudo_size_before=ev['size_before'], sudo_size_after=ev['size_after'], sudo_checkpoint_sha256=h(proof_raw))


def review_body(review, sid, port, nonce, control, stopped_raw, review_raw):
    """Body of the ledger-222-tm09-review capsule, from a review the signer itself derived from the log."""
    if review.get('nonce') != nonce or review.get('session') != sid or not clean(review):
        raise Refused('unlisted or unreviewed sudo entries: not signing a review boundary')
    body = control['body']
    if body.get('session') != sid or body.get('nonce') != nonce or body.get('port') != port:
        raise Refused('control receipt is for another launch')
    from timemachine.tm09_fixture import fingerprint
    return dict(session=sid, port=port, nonce=nonce, control_sha256=fingerprint(control),
                post_stop_probe_sha256=h(stopped_raw), sudo_review_sha256=h(review_raw),
                sudo_allowlist_reviewed=True, raw_copies_denied=True, listener_stopped=True)


def write_owned(path, data, owner=SERVICE, chown=True):
    """Create a new 0600 file (never overwrite) owned by the given account."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    if chown:
        import pwd
        u = pwd.getpwnam(owner)
        os.chown(path, u.pw_uid, u.pw_gid)


def port_closed(port):
    import socket
    s = socket.socket()
    s.settimeout(2)
    try:
        return s.connect_ex(('127.0.0.1', port)) != 0
    finally:
        s.close()


def main(argv):
    rel = Path(os.environ['TM09_RELEASE'])
    sys.path.insert(0, str(rel))
    from timemachine.tm09_desk import seal, store_new
    from timemachine.tm09_fixture import read_private, settings
    import subprocess

    def key():
        return read_private(KEY).decode().strip()

    def capsule(domain, body, out, owned):
        data = (json.dumps({'body': body, 'seal': seal(key(), domain, body)}, sort_keys=True) + '\n').encode()
        if owned:
            write_owned(out, data)
        else:
            store_new(out, {'body': body, 'seal': seal(key(), domain, body)})
        print(out.name, h(read_private(out)))

    def sid_port(sid, port):
        if not SIDRE.fullmatch(sid) or int(port) not in PORTS:
            raise Refused('opaque TM09 session and approved port required')
        return sid, int(port)

    cmd, args = argv[0], argv[1:]
    if cmd == 'keygen':
        fd = os.open(KEY, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.write(fd, (secrets.token_urlsafe(48) + '\n').encode())
        os.close(fd)
        print('key written')
    elif cmd == 'approve-rehearsal':
        cfg = read_private(rel / 'config/thresholds.yaml')
        files = {n: h(read_private(rel / n)) for n in FILES}
        body = dict(root=str(ROOT), service_uid=os.geteuid(), release=str(rel),
                    approved_by='lead agent, ledger 222 (rehearsal and provisioning release)',
                    release_files=files, config_sha256=h(cfg),
                    registration_sha256=h(read_private(rel / 'timemachine/TM09_REGISTRATION.md')),
                    resolved_settings=settings(cfg), limits=dict(REHEARSAL_LIMITS),
                    operator_boundary_sha256=h(read_private(Path(args[0]))), ports=list(PORTS))
        capsule('ledger-222-rehearse-tm09', body, OPS / 'rehearsal-approval.json', owned=False)
    elif cmd == 'init-canaries':
        import pwd
        u = pwd.getpwnam(SERVICE)
        CANARY_DIR.mkdir(mode=0o700)
        os.chown(CANARY_DIR, u.pw_uid, u.pw_gid)
        for n in CANARY_NAMES:
            write_owned(CANARY_DIR / n, b'TM09 canary file; a worker must not be able to open it\n')
        print('canaries', len(CANARY_NAMES))
    elif cmd == 'slot-dir':
        print(slot_dir(args[0], args[1], args[2]))
    elif cmd == 'bearer-copy':
        out = Path(args[3])
        if out.parent.stat().st_uid != __import__('pwd').getpwnam(WORKER).pw_uid or out.parent.stat().st_mode & 0o077:
            raise Refused('bearer copy must go into a private worker-owned directory')
        b = json.loads(read_private(slot_dir(args[0], args[1], args[2]) / 'bearer.json'))
        write_owned(out, json.dumps({'session': b['session'], 'token': b['token']}).encode(), owner=WORKER)
        print(out.name, b['session'])
    elif cmd == 'canary-launch':
        sid, port = sid_port(*args[:2])
        nonce = secrets.token_hex(16)
        st = os.stat(SUDO_LOG)
        before = SUDO_LOG.read_bytes()
        subprocess.run(['/usr/sbin/runuser', '-u', WORKER, '--', '/usr/bin/sudo', '-n', '/usr/bin/true', 'tm09-' + nonce], check=True)
        after = SUDO_LOG.read_bytes()
        st2 = os.stat(SUDO_LOG)
        own = '/usr/bin/true tm09-' + nonce
        segment = [parse_line(l) for l in after[len(before):].decode('utf-8', 'replace').splitlines() if l.strip()]
        matched = sum(1 for p in segment if p and p['command'] == own and p['invoker'] == WORKER and p['target'] == 'root') == 1
        fields = dict(session=sid, port=port, nonce=nonce, matched_canary=matched,
                      prefix_unchanged=after[:len(before)] == before and (st.st_dev, st.st_ino) == (st2.st_dev, st2.st_ino),
                      size_before=len(before), size_after=len(after), prefix_sha256=h(after),
                      log_id=[st2.st_dev, st2.st_ino])
        raw = canon(sealed(key(), 'canary', fields))
        out = OPS / f'{sid}-{nonce}-proof.json'
        write_owned(out, raw)
        body = launch_body(sid, port, fields, raw)
        print(out)
        capsule('ledger-222-tm09-launch', body, OPS / f'{sid}-{nonce}-launch.json', owned=True)
    elif cmd == 'probe':
        mode, phase = args[0], args[1]
        sid, port = sid_port(args[2], args[3])
        nonce, sibling, bearer = args[4], args[5], args[6]
        export_dir = args[7] if len(args) > 7 else None
        if phase not in ('live', 'stopped') or mode not in MODES or not NONCE.fullmatch(nonce) or not SIDRE.fullmatch(sibling):
            raise Refused('bad probe arguments')
        if phase == 'stopped' and not port_closed(port):
            raise Refused('listener still answers')
        canaries = required_canaries(mode, export_dir)
        cmdline = ['/usr/sbin/runuser', '-u', WORKER, '--', 'env', '-i', 'PATH=/usr/bin:/bin', '/usr/bin/python3.14', '-B',
                   '-m', 'timemachine.tm09_isolation_probe', '--port', str(port), '--session', sid, '--sibling', sibling,
                   '--bearer-file', bearer] + [x for p in canaries for x in ('--canary', str(p))] + (['--stopped'] if phase == 'stopped' else [])
        run = subprocess.run(cmdline, cwd=rel, capture_output=True, text=True)
        if run.returncode != 0:
            raise Refused(phase + ' worker probe failed')
        out = json.loads(run.stdout)
        fields = dict(out, worker=WORKER, canaries=sorted(map(str, canaries)), nonce=nonce,
                      probe_sha256=h(read_private(rel / 'timemachine/tm09_isolation_probe.py')))
        check_probe(fields, sid, port, phase, canaries)
        path = OPS / f'{sid}-{nonce}-{phase}-probe.json'
        write_owned(path, canon(sealed(key(), 'probe', fields)))
        print(path.name, phase, 'denied', fields['denied_count'])
    elif cmd == 'review-boundary':
        mode = args[0]
        sid, port = sid_port(args[1], args[2])
        nonce, desk_dir, oplog = args[3], Path(args[4]), Path(args[5])
        export_dir = args[6] if len(args) > 6 else None
        if mode not in MODES or not NONCE.fullmatch(nonce):
            raise Refused('bad review arguments')
        if not port_closed(port):
            raise Refused('listener still answers')
        k = key()
        canaries = required_canaries(mode, export_dir)
        for phase in ('live', 'stopped'):
            raw = read_private(OPS / f'{sid}-{nonce}-{phase}-probe.json')
            check_probe(unseal(k, 'probe', raw), sid, port, phase, canaries)
        stopped_raw = read_private(OPS / f'{sid}-{nonce}-stopped-probe.json')
        proof_raw = read_private(OPS / f'{sid}-{nonce}-proof.json')
        proof = unseal(k, 'canary', proof_raw)
        if proof.get('session') != sid or proof.get('nonce') != nonce or proof.get('port') != port:
            raise Refused('canary proof is for another launch')
        proof['sha256'] = h(proof_raw)
        st = os.stat(SUDO_LOG)
        log = SUDO_LOG.read_bytes()
        records = [json.loads(l) for l in oplog.read_text().splitlines() if l.strip()]
        on_file = set()
        for p in OPS.iterdir():
            m = re.fullmatch(r'TM09-[0-9a-f]{32}-([0-9a-f]{32})-proof\.json', p.name)
            if m and m.group(1) != nonce:
                unseal(k, 'canary', read_private(p))
                on_file.add(m.group(1))
        review = dict(sudo_review(log, (st.st_dev, st.st_ino), proof, records, nonce, on_file), session=sid,
                      oplog_sha256=h(oplog.read_bytes()))
        review_raw = canon(sealed(k, 'sudo-review', review))
        write_owned(OPS / f'{sid}-{nonce}-sudo.json', review_raw)
        print('sudo entries', review['entries'], 'listed', len(review['listed']), 'unlisted', len(review['unlisted']),
              'own canary', review['own_canary'])
        for line in review['unlisted']:
            print('UNLISTED', line[:200])
        control = json.loads(read_private(desk_dir / f'{nonce}-control.json'))
        from timemachine.tm09_desk import verify_seal
        verify_seal(k, 'tm09-control', control['body'], control['seal'])
        stop = json.loads(read_private(desk_dir / f'{nonce}-stop.json'))
        verify_seal(k, 'tm09-stop', stop['body'], stop['seal'])
        body = review_body(review, sid, port, nonce, control, stopped_raw, review_raw)
        capsule('ledger-222-tm09-review', body, OPS / f'{sid}-{nonce}-review.json', owned=True)
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Refused as exc:
        raise SystemExit('TM09 ops refused: ' + str(exc))
